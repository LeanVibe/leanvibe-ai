"""
Mock Tree-sitter Implementation for Testing

Provides a complete mock implementation of tree-sitter functionality
that allows tests to run without the actual tree-sitter dependency.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import MagicMock

logger = logging.getLogger(__name__)


class MockNode:
    """Mock implementation of tree-sitter Node"""

    def __init__(
        self,
        node_type: str = "program",
        start_byte: int = 0,
        end_byte: int = 100,
        start_point: Tuple[int, int] = (0, 0),
        end_point: Tuple[int, int] = (5, 0),
        children: Optional[List["MockNode"]] = None,
        has_error: bool = False,
    ):
        self.type = node_type
        self.start_byte = start_byte
        self.end_byte = end_byte
        self.start_point = start_point
        self.end_point = end_point
        self.children = children or []
        self.has_error = has_error

    def __str__(self):
        return f"MockNode(type={self.type}, children={len(self.children)})"

    def __repr__(self):
        return self.__str__()


class MockTree:
    """Mock implementation of tree-sitter Tree"""

    def __init__(self, root_node: Optional[MockNode] = None):
        self.root_node = root_node or MockNode()

    def __str__(self):
        return f"MockTree(root={self.root_node})"


class MockLanguage:
    """Mock implementation of tree-sitter Language"""

    def __init__(self, name: str = "python"):
        self.name = name

    def __str__(self):
        return f"MockLanguage({self.name})"


class MockParser:
    """Mock implementation of tree-sitter Parser"""

    def __init__(self, language: Optional[MockLanguage] = None):
        self.language = language or MockLanguage()

    def parse(self, source_code: bytes) -> MockTree:
        """Parse source code and return a mock syntax tree"""
        try:
            content = source_code.decode("utf-8")
            return self._create_mock_tree(content)
        except Exception as e:
            logger.warning(f"Mock parser failed: {e}")
            return MockTree(MockNode(has_error=True))

    def _create_mock_tree(self, content: str) -> MockTree:
        """Create a realistic mock tree based on content"""
        lines = content.split("\n")
        total_length = len(content)

        # Create mock nodes based on content patterns
        children = []
        current_byte = 0

        for i, line in enumerate(lines):
            line_start = current_byte
            line_end = current_byte + len(line)

            # Mock different node types based on content
            if line.strip().startswith("def "):
                node = MockNode(
                    node_type="function_definition",
                    start_byte=line_start,
                    end_byte=line_end,
                    start_point=(i, 0),
                    end_point=(i, len(line)),
                )
            elif line.strip().startswith("class "):
                node = MockNode(
                    node_type="class_definition",
                    start_byte=line_start,
                    end_byte=line_end,
                    start_point=(i, 0),
                    end_point=(i, len(line)),
                )
            elif line.strip().startswith("import ") or line.strip().startswith("from "):
                node = MockNode(
                    node_type="import_statement",
                    start_byte=line_start,
                    end_byte=line_end,
                    start_point=(i, 0),
                    end_point=(i, len(line)),
                )
            elif line.strip() and not line.strip().startswith("#"):
                node = MockNode(
                    node_type="expression_statement",
                    start_byte=line_start,
                    end_byte=line_end,
                    start_point=(i, 0),
                    end_point=(i, len(line)),
                )
            else:
                # Skip empty lines or comments
                current_byte = line_end + 1  # +1 for newline
                continue

            children.append(node)
            current_byte = line_end + 1  # +1 for newline

        root = MockNode(
            node_type="module",
            start_byte=0,
            end_byte=total_length,
            start_point=(0, 0),
            end_point=(len(lines), 0),
            children=children,
        )

        return MockTree(root)


class MockTreeSitterManager:
    """Mock implementation of TreeSitterManager"""

    def __init__(self, executor=None):
        self.executor = executor
        self.languages = {}
        self.parsers = {}
        self.initialized = False
        logger.info("MockTreeSitterManager initialized")

    async def initialize(self):
        """Mock initialization"""
        try:
            logger.info("Initializing Mock Tree-sitter parsers...")

            # Mock initialization for all languages
            await self._mock_init_python()
            await self._mock_init_javascript()
            await self._mock_init_typescript()

            self.initialized = True
            logger.info(f"Mock initialized {len(self.languages)} Tree-sitter parsers")

        except Exception as e:
            logger.error(f"Mock Tree-sitter initialization failed: {e}")
            self.initialized = False

    async def _mock_init_python(self):
        """Mock Python parser initialization"""
        language = MockLanguage("python")
        parser = MockParser(language)

        self.languages["PYTHON"] = language
        self.parsers["PYTHON"] = parser
        logger.debug("Mock Python parser initialized")

    async def _mock_init_javascript(self):
        """Mock JavaScript parser initialization"""
        language = MockLanguage("javascript")
        parser = MockParser(language)

        self.languages["JAVASCRIPT"] = language
        self.parsers["JAVASCRIPT"] = parser
        logger.debug("Mock JavaScript parser initialized")

    async def _mock_init_typescript(self):
        """Mock TypeScript parser initialization"""
        language = MockLanguage("typescript")
        parser = MockParser(language)

        self.languages["TYPESCRIPT"] = language
        self.parsers["TYPESCRIPT"] = parser
        logger.debug("Mock TypeScript parser initialized")

    def detect_language(self, file_path: str) -> str:
        """Mock language detection"""
        path = Path(file_path)
        extension = path.suffix.lower()

        language_map = {
            ".py": "PYTHON",
            ".js": "JAVASCRIPT",
            ".mjs": "JAVASCRIPT",
            ".jsx": "JAVASCRIPT",
            ".ts": "TYPESCRIPT",
            ".tsx": "TYPESCRIPT",
            ".swift": "SWIFT",
            ".go": "GO",
            ".rs": "RUST",
        }

        return language_map.get(extension, "UNKNOWN")

    def parse_file(self, file_path: str, content: str) -> Tuple[Optional[MockTree], List[str]]:
        """Mock file parsing"""
        errors = []

        try:
            if not self.initialized:
                errors.append("Mock Tree-sitter parsers not initialized")
                return None, errors

            language = self.detect_language(file_path)
            if language == "UNKNOWN":
                errors.append(f"Unsupported file type: {file_path}")
                return None, errors

            if language not in self.parsers:
                errors.append(f"Mock parser not available for {language}")
                return None, errors

            parser = self.parsers[language]
            tree = parser.parse(content.encode("utf-8"))

            # Simulate parsing errors occasionally for testing
            if "syntax_error" in content.lower():
                tree.root_node.has_error = True
                errors.append(f"Mock syntax errors detected in {file_path}")

            return tree, errors

        except Exception as e:
            logger.error(f"Mock parsing error {file_path}: {e}")
            errors.append(f"Mock parsing failed: {str(e)}")
            return None, errors

    async def async_parse_file(self, file_path: str, content: str) -> Tuple[Optional[MockTree], List[str]]:
        """Mock async file parsing"""
        return self.parse_file(file_path, content)

    def tree_to_ast_node(self, node: MockNode, source_code: bytes) -> Dict[str, Any]:
        """Mock conversion to AST node"""
        try:
            node_text = source_code[node.start_byte : node.end_byte].decode("utf-8", errors="ignore")

            # Convert children recursively
            children = []
            for child in node.children:
                children.append(self.tree_to_ast_node(child, source_code))

            return {
                "node_type": node.type,
                "start_byte": node.start_byte,
                "end_byte": node.end_byte,
                "start_point": node.start_point,
                "end_point": node.end_point,
                "text": node_text[:1000] if len(node_text) > 1000 else node_text,
                "children": children,
            }

        except Exception as e:
            logger.error(f"Mock node conversion error: {e}")
            return {
                "node_type": node.type or "error",
                "start_byte": node.start_byte or 0,
                "end_byte": node.end_byte or 0,
                "start_point": node.start_point or (0, 0),
                "end_point": node.end_point or (0, 0),
                "text": "<mock_error>",
                "children": [],
            }

    def find_nodes_by_type(self, root: MockNode, node_types: List[str]) -> List[MockNode]:
        """Mock node finding by type"""
        found_nodes = []

        def traverse(node: MockNode):
            if node.type in node_types:
                found_nodes.append(node)

            for child in node.children:
                traverse(child)

        traverse(root)
        return found_nodes

    def get_node_text(self, node: MockNode, source_code: bytes) -> str:
        """Mock node text extraction"""
        try:
            return source_code[node.start_byte : node.end_byte].decode("utf-8", errors="ignore")
        except Exception:
            return f"<mock_text_{node.type}>"

    def extract_imports(self, tree: MockTree, source_code: bytes, language: str) -> List[Dict]:
        """Mock import extraction"""
        imports = []

        try:
            if language == "PYTHON":
                imports.extend(self._mock_extract_python_imports(tree.root_node, source_code))
            elif language in ["JAVASCRIPT", "TYPESCRIPT"]:
                imports.extend(self._mock_extract_js_imports(tree.root_node, source_code))

        except Exception as e:
            logger.error(f"Mock import extraction error: {e}")

        return imports

    async def async_extract_imports(self, tree: MockTree, source_code: bytes, language: str) -> List[Dict]:
        """Mock async import extraction"""
        return self.extract_imports(tree, source_code, language)

    def _mock_extract_python_imports(self, root: MockNode, source_code: bytes) -> List[Dict]:
        """Mock Python import extraction"""
        imports = []
        import_nodes = self.find_nodes_by_type(root, ["import_statement", "import_from_statement"])

        for node in import_nodes:
            try:
                import_text = self.get_node_text(node, source_code)

                if "import " in import_text and " from " not in import_text:
                    imports.append({
                        "type": "import",
                        "module": import_text.replace("import ", "").strip(),
                        "line": node.start_point[0] + 1,
                        "raw": import_text,
                    })
                elif "from " in import_text and " import " in import_text:
                    imports.append({
                        "type": "from_import",
                        "module": import_text,
                        "line": node.start_point[0] + 1,
                        "raw": import_text,
                    })

            except Exception as e:
                logger.error(f"Mock Python import parsing error: {e}")

        return imports

    def _mock_extract_js_imports(self, root: MockNode, source_code: bytes) -> List[Dict]:
        """Mock JavaScript/TypeScript import extraction"""
        imports = []
        import_nodes = self.find_nodes_by_type(root, ["import_statement", "call_expression"])

        for node in import_nodes:
            try:
                import_text = self.get_node_text(node, source_code)

                if import_text.strip().startswith("import"):
                    imports.append({
                        "type": "import",
                        "module": import_text,
                        "line": node.start_point[0] + 1,
                        "raw": import_text,
                    })
                elif "require(" in import_text:
                    imports.append({
                        "type": "require",
                        "module": import_text,
                        "line": node.start_point[0] + 1,
                        "raw": import_text,
                    })

            except Exception as e:
                logger.error(f"Mock JS import parsing error: {e}")

        return imports

    def get_supported_languages(self) -> List[str]:
        """Mock supported languages"""
        return list(self.languages.keys())

    def is_language_supported(self, language: str) -> bool:
        """Mock language support check"""
        return language in self.parsers and self.initialized


# Mock modules that can be imported
class MockTreeSitterModule:
    """Mock tree_sitter module"""
    
    Language = MockLanguage
    Node = MockNode
    Parser = MockParser
    Tree = MockTree
    
    def language(self):
        return MockLanguage()


class MockTreeSitterPython:
    """Mock tree_sitter_python module"""
    
    @staticmethod
    def language():
        return MockLanguage("python")


class MockTreeSitterJavaScript:
    """Mock tree_sitter_javascript module"""
    
    @staticmethod
    def language():
        return MockLanguage("javascript")


class MockTreeSitterTypeScript:
    """Mock tree_sitter_typescript module"""
    
    @staticmethod
    def language_typescript():
        return MockLanguage("typescript")
    
    @staticmethod
    def language_tsx():
        return MockLanguage("tsx")


# Global mock manager instance
mock_tree_sitter_manager = MockTreeSitterManager()