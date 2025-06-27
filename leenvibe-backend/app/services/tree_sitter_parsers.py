"""
Tree-sitter Parsers Service

Handles initialization and management of tree-sitter parsers for different languages.
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor

import tree_sitter
from tree_sitter import Language, Node, Parser

from ..models.ast_models import ASTNode, LanguageType

logger = logging.getLogger(__name__)


class TreeSitterManager:
    """Manages tree-sitter parsers for multiple languages"""

    def __init__(self, executor: ThreadPoolExecutor):
        self.executor = executor
        self.languages: Dict[LanguageType, Language] = {}
        self.parsers: Dict[LanguageType, Parser] = {}
        self.initialized = False

    async def initialize(self):
        """Initialize all supported language parsers"""
        try:
            logger.info("Initializing Tree-sitter parsers...")

            # Initialize languages
            await self._init_python()
            await self._init_javascript()
            await self._init_typescript()

            self.initialized = True
            logger.info(f"Initialized {len(self.languages)} Tree-sitter parsers")

        except Exception as e:
            logger.error(f"Failed to initialize Tree-sitter parsers: {e}")
            # Initialize with reduced functionality
            self.initialized = False

    async def _init_python(self):
        """Initialize Python parser"""
        try:
            import tree_sitter_python

            language = Language(tree_sitter_python.language())
            parser = Parser(language)

            self.languages[LanguageType.PYTHON] = language
            self.parsers[LanguageType.PYTHON] = parser
            logger.debug("Python parser initialized")

        except Exception as e:
            logger.error(f"Failed to initialize Python parser: {e}")

    async def _init_javascript(self):
        """Initialize JavaScript parser"""
        try:
            import tree_sitter_javascript

            language = Language(tree_sitter_javascript.language())
            parser = Parser(language)

            self.languages[LanguageType.JAVASCRIPT] = language
            self.parsers[LanguageType.JAVASCRIPT] = parser
            logger.debug("JavaScript parser initialized")

        except Exception as e:
            logger.error(f"Failed to initialize JavaScript parser: {e}")

    async def _init_typescript(self):
        """Initialize TypeScript parser"""
        try:
            import tree_sitter_typescript

            # TypeScript has separate grammars for TS and TSX
            ts_language = Language(tree_sitter_typescript.language_typescript())
            tsx_language = Language(tree_sitter_typescript.language_tsx())

            ts_parser = Parser(ts_language)
            tsx_parser = Parser(tsx_language)

            self.languages[LanguageType.TYPESCRIPT] = ts_language
            self.parsers[LanguageType.TYPESCRIPT] = ts_parser

            # Store TSX separately for future use
            self.languages["tsx"] = tsx_language
            self.parsers["tsx"] = tsx_parser

            logger.debug("TypeScript parser initialized")

        except Exception as e:
            logger.error(f"Failed to initialize TypeScript parser: {e}")

    def detect_language(self, file_path: str) -> LanguageType:
        """Detect programming language from file extension"""
        path = Path(file_path)
        extension = path.suffix.lower()

        language_map = {
            ".py": LanguageType.PYTHON,
            ".js": LanguageType.JAVASCRIPT,
            ".mjs": LanguageType.JAVASCRIPT,
            ".jsx": LanguageType.JAVASCRIPT,
            ".ts": LanguageType.TYPESCRIPT,
            ".tsx": LanguageType.TYPESCRIPT,
            ".swift": LanguageType.SWIFT,
            ".go": LanguageType.GO,
            ".rs": LanguageType.RUST,
        }

        return language_map.get(extension, LanguageType.UNKNOWN)

    def parse_file(
        self, file_path: str, content: str
    ) -> Tuple[Optional[tree_sitter.Tree], List[str]]:
        """Parse a file and return the syntax tree (synchronous)"""
        errors = []

        try:
            if not self.initialized:
                errors.append("Tree-sitter parsers not initialized")
                return None, errors

            language = self.detect_language(file_path)
            if language == LanguageType.UNKNOWN:
                errors.append(f"Unsupported file type: {file_path}")
                return None, errors

            if language not in self.parsers:
                errors.append(f"Parser not available for {language}")
                return None, errors

            parser = self.parsers[language]
            tree = parser.parse(content.encode("utf-8"))

            # Check for parsing errors
            if tree.root_node.has_error:
                errors.append(f"Syntax errors detected in {file_path}")

            return tree, errors

        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {e}")
            errors.append(f"Parsing failed: {str(e)}")
            return None, errors

    async def async_parse_file(
        self, file_path: str, content: str
    ) -> Tuple[Optional[tree_sitter.Tree], List[str]]:
        """Parse a file asynchronously using the executor"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self.parse_file,  # Call the synchronous parse_file
            file_path,
            content,
        )

    def tree_to_ast_node(self, node: Node, source_code: bytes) -> ASTNode:
        """Convert tree-sitter Node to our ASTNode model"""
        try:
            # Extract node text
            node_text = source_code[node.start_byte : node.end_byte].decode(
                "utf-8", errors="ignore"
            )

            # Convert children recursively
            children = []
            for child in node.children:
                children.append(self.tree_to_ast_node(child, source_code))

            return ASTNode(
                node_type=node.type,
                start_byte=node.start_byte,
                end_byte=node.end_byte,
                start_point=node.start_point,
                end_point=node.end_point,
                text=(
                    node_text[:1000] if len(node_text) > 1000 else node_text
                ),  # Limit text length
                children=children,
            )

        except Exception as e:
            logger.error(f"Error converting node to AST: {e}")
            # Return minimal node on error
            return ASTNode(
                node_type=node.type or "error",
                start_byte=node.start_byte or 0,
                end_byte=node.end_byte or 0,
                start_point=node.start_point or (0, 0),
                end_point=node.end_point or (0, 0),
                text="<error>",
                children=[],
            )

    def find_nodes_by_type(self, root: Node, node_types: List[str]) -> List[Node]:
        """Find all nodes of specific types in the tree"""
        found_nodes = []

        def traverse(node: Node):
            if node.type in node_types:
                found_nodes.append(node)

            for child in node.children:
                traverse(child)

        traverse(root)
        return found_nodes

    def get_node_text(self, node: Node, source_code: bytes) -> str:
        """Get the text content of a node"""
        try:
            return source_code[node.start_byte : node.end_byte].decode(
                "utf-8", errors="ignore"
            )
        except Exception:
            return ""

    def extract_imports(
        self, tree: tree_sitter.Tree, source_code: bytes, language: LanguageType
    ) -> List[Dict]:
        """Extract import statements from the syntax tree (synchronous)"""
        imports = []

        try:
            if language == LanguageType.PYTHON:
                imports.extend(
                    self._extract_python_imports(tree.root_node, source_code)
                )
            elif language in [LanguageType.JAVASCRIPT, LanguageType.TYPESCRIPT]:
                imports.extend(self._extract_js_imports(tree.root_node, source_code))

        except Exception as e:
            logger.error(f"Error extracting imports: {e}")

        return imports

    async def async_extract_imports(
        self, tree: tree_sitter.Tree, source_code: bytes, language: LanguageType
    ) -> List[Dict]:
        """Extract import statements from the syntax tree (asynchronous)"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, self.extract_imports, tree, source_code, language
        )

    def _extract_python_imports(self, root: Node, source_code: bytes) -> List[Dict]:
        """Extract Python import statements"""
        imports = []

        # Find import and from_import nodes
        import_nodes = self.find_nodes_by_type(
            root, ["import_statement", "import_from_statement"]
        )

        for node in import_nodes:
            try:
                import_text = self.get_node_text(node, source_code)

                if node.type == "import_statement":
                    # Handle: import module1, module2
                    imports.append(
                        {
                            "type": "import",
                            "module": import_text.replace("import ", "").strip(),
                            "line": node.start_point[0] + 1,
                            "raw": import_text,
                        }
                    )
                elif node.type == "import_from_statement":
                    # Handle: from module import item1, item2
                    imports.append(
                        {
                            "type": "from_import",
                            "module": import_text,
                            "line": node.start_point[0] + 1,
                            "raw": import_text,
                        }
                    )

            except Exception as e:
                logger.error(f"Error parsing Python import: {e}")

        return imports

    def _extract_js_imports(self, root: Node, source_code: bytes) -> List[Dict]:
        """Extract JavaScript/TypeScript import statements"""
        imports = []

        # Find import and require nodes
        import_nodes = self.find_nodes_by_type(
            root, ["import_statement", "call_expression"]
        )

        for node in import_nodes:
            try:
                import_text = self.get_node_text(node, source_code)

                if node.type == "import_statement":
                    imports.append(
                        {
                            "type": "import",
                            "module": import_text,
                            "line": node.start_point[0] + 1,
                            "raw": import_text,
                        }
                    )
                elif "require(" in import_text:
                    imports.append(
                        {
                            "type": "require",
                            "module": import_text,
                            "line": node.start_point[0] + 1,
                            "raw": import_text,
                        }
                    )

            except Exception as e:
                logger.error(f"Error parsing JS import: {e}")

        return imports

    def get_supported_languages(self) -> List[LanguageType]:
        """Get list of supported languages"""
        return list(self.languages.keys())

    def is_language_supported(self, language: LanguageType) -> bool:
        """Check if a language is supported"""
        return language in self.parsers and self.initialized


# Global instance
tree_sitter_manager = TreeSitterManager(ThreadPoolExecutor(max_workers=2))
