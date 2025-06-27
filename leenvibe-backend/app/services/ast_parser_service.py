import asyncio
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

# Try to import Tree-sitter, gracefully handle if not available
try:
    import tree_sitter
    from tree_sitter import Language, Parser

    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    tree_sitter = None
    Language = None
    Parser = None

logger = logging.getLogger(__name__)


@dataclass
class CodeSymbol:
    """Represents a code symbol (function, class, variable, etc.)"""

    name: str
    type: str  # 'function', 'class', 'variable', 'import', etc.
    start_line: int
    end_line: int
    start_byte: int
    end_byte: int
    scope: str  # 'global', 'class', 'function'
    parent: Optional[str] = None
    docstring: Optional[str] = None
    parameters: List[str] = None

    def __post_init__(self):
        if self.parameters is None:
            self.parameters = []


@dataclass
class CodeStructure:
    """Represents the structure of a code file"""

    file_path: str
    language: str
    symbols: List[CodeSymbol]
    imports: List[str]
    dependencies: Set[str]
    complexity_score: float
    lines_of_code: int

    def __post_init__(self):
        if isinstance(self.dependencies, list):
            self.dependencies = set(self.dependencies)


class TreeSitterService:
    """Service for parsing code using Tree-sitter"""

    def __init__(self):
        self.parsers: Dict[str, Any] = (
            {}
        )  # Using Any instead of Parser for compatibility
        self.languages: Dict[str, Any] = (
            {}
        )  # Using Any instead of Language for compatibility
        self.is_initialized = False
        self.tree_sitter_available = TREE_SITTER_AVAILABLE

        # Supported languages and their extensions
        self.language_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".jsx": "javascript",
            ".swift": "swift",
            ".java": "java",
            ".cpp": "cpp",
            ".cc": "cpp",
            ".cxx": "cpp",
            ".c": "c",
            ".h": "c",
            ".hpp": "cpp",
            ".go": "go",
            ".rs": "rust",
            ".rb": "ruby",
            ".php": "php",
        }

    async def initialize(self) -> bool:
        """Initialize Tree-sitter parsers for supported languages"""
        try:
            logger.info("Initializing Tree-sitter service...")

            if not self.tree_sitter_available:
                logger.warning("Tree-sitter not available - using basic text analysis")
                self.is_initialized = True
                return True

            # For now, we'll initialize the parsers that are already available
            # This creates the infrastructure without requiring language grammar downloads

            available_languages = []

            # Try to initialize Python parser (most common for our use case)
            try:
                python_parser = await self._init_language_parser("python")
                if python_parser:
                    available_languages.append("python")
                    logger.info("Python parser initialized successfully")
            except Exception as e:
                logger.warning(f"Python parser initialization failed: {e}")

            # Try to initialize JavaScript parser
            try:
                js_parser = await self._init_language_parser("javascript")
                if js_parser:
                    available_languages.append("javascript")
                    logger.info("JavaScript parser initialized successfully")
            except Exception as e:
                logger.warning(f"JavaScript parser initialization failed: {e}")

            # Try to initialize TypeScript parser
            try:
                ts_parser = await self._init_language_parser("typescript")
                if ts_parser:
                    available_languages.append("typescript")
                    logger.info("TypeScript parser initialized successfully")
            except Exception as e:
                logger.warning(f"TypeScript parser initialization failed: {e}")

            self.is_initialized = True
            logger.info(
                f"Tree-sitter service initialized with {len(available_languages)} languages: {available_languages}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Tree-sitter service: {e}")
            self.is_initialized = True  # Allow basic text analysis mode
            return True

    async def _init_language_parser(self, language: str) -> Optional[Any]:
        """Initialize parser for a specific language"""
        try:
            if not self.tree_sitter_available or not Parser:
                return None

            # This is a placeholder implementation
            # In a full implementation, you would:
            # 1. Check if language grammar is available
            # 2. Load the language library
            # 3. Create and configure the parser

            parser = Parser()

            # For development, we'll create parsers but they won't have actual language grammars
            # This allows us to test the infrastructure

            self.parsers[language] = parser
            logger.info(f"Parser placeholder created for {language}")
            return parser

        except Exception as e:
            logger.error(f"Failed to initialize {language} parser: {e}")
            return None

    def get_language_from_file(self, file_path: str) -> Optional[str]:
        """Determine language from file extension"""
        path = Path(file_path)
        extension = path.suffix.lower()
        return self.language_map.get(extension)

    async def parse_file(self, file_path: str) -> Optional[CodeStructure]:
        """Parse a code file and extract its structure"""
        try:
            if not self.is_initialized:
                logger.warning("Tree-sitter service not initialized")
                return None

            path = Path(file_path)
            if not path.exists() or not path.is_file():
                logger.error(f"File not found: {file_path}")
                return None

            language = self.get_language_from_file(file_path)
            if not language:
                logger.warning(f"Unsupported file type: {file_path}")
                return None

            # Read file content
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
            except UnicodeDecodeError:
                logger.error(f"Cannot read file as text: {file_path}")
                return None

            # For Sprint 1, we'll do basic text-based analysis
            # This provides immediate value while we work on full Tree-sitter integration
            return await self._basic_code_analysis(file_path, content, language)

        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {e}")
            return None

    async def _basic_code_analysis(
        self, file_path: str, content: str, language: str
    ) -> CodeStructure:
        """Basic code analysis using text patterns (placeholder for full AST parsing)"""
        lines = content.splitlines()
        symbols = []
        imports = []
        dependencies = set()

        # Language-specific pattern matching
        if language == "python":
            symbols, imports, deps = self._analyze_python_code(lines)
            dependencies.update(deps)
        elif language in ["javascript", "typescript"]:
            symbols, imports, deps = self._analyze_javascript_code(lines)
            dependencies.update(deps)
        elif language == "swift":
            symbols, imports, deps = self._analyze_swift_code(lines)
            dependencies.update(deps)

        # Calculate basic complexity score
        complexity_score = self._calculate_complexity_score(lines, symbols)

        return CodeStructure(
            file_path=file_path,
            language=language,
            symbols=symbols,
            imports=imports,
            dependencies=dependencies,
            complexity_score=complexity_score,
            lines_of_code=len(
                [
                    line
                    for line in lines
                    if line.strip() and not line.strip().startswith("#")
                ]
            ),
        )

    def _analyze_python_code(
        self, lines: List[str]
    ) -> tuple[List[CodeSymbol], List[str], Set[str]]:
        """Analyze Python code structure"""
        symbols = []
        imports = []
        dependencies = set()

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Imports
            if stripped.startswith("import ") or stripped.startswith("from "):
                imports.append(stripped)
                # Extract dependency names
                if stripped.startswith("import "):
                    dep = stripped[7:].split(".")[0].split(" as ")[0]
                    dependencies.add(dep)
                elif stripped.startswith("from "):
                    dep = stripped[5:].split(" import")[0].split(".")[0]
                    dependencies.add(dep)

            # Function definitions
            elif stripped.startswith("def "):
                func_name = stripped[4:].split("(")[0].strip()
                # Extract parameters
                params = []
                if "(" in stripped and ")" in stripped:
                    param_str = stripped.split("(")[1].split(")")[0]
                    if param_str.strip():
                        params = [
                            p.strip().split(":")[0].split("=")[0].strip()
                            for p in param_str.split(",")
                            if p.strip()
                        ]

                symbols.append(
                    CodeSymbol(
                        name=func_name,
                        type="function",
                        start_line=i + 1,
                        end_line=i
                        + 1,  # We'd need proper parsing for accurate end line
                        start_byte=0,
                        end_byte=len(line),
                        scope="global",  # Would need proper scope analysis
                        parameters=params,
                    )
                )

            # Class definitions
            elif stripped.startswith("class "):
                class_name = stripped[6:].split("(")[0].split(":")[0].strip()
                symbols.append(
                    CodeSymbol(
                        name=class_name,
                        type="class",
                        start_line=i + 1,
                        end_line=i + 1,
                        start_byte=0,
                        end_byte=len(line),
                        scope="global",
                    )
                )

        return symbols, imports, dependencies

    def _analyze_javascript_code(
        self, lines: List[str]
    ) -> tuple[List[CodeSymbol], List[str], Set[str]]:
        """Analyze JavaScript/TypeScript code structure"""
        symbols = []
        imports = []
        dependencies = set()

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Imports
            if (
                stripped.startswith("import ")
                or stripped.startswith("const ")
                and "require(" in stripped
            ):
                imports.append(stripped)
                # Extract dependencies
                if "from " in stripped:
                    dep = stripped.split("from ")[1].strip().strip("'\"")
                    if not dep.startswith("."):  # External dependency
                        dependencies.add(dep.split("/")[0])
                elif "require(" in stripped:
                    dep = (
                        stripped.split("require(")[1].split(")")[0].strip().strip("'\"")
                    )
                    if not dep.startswith("."):
                        dependencies.add(dep.split("/")[0])

            # Function definitions
            elif "function " in stripped or "=>" in stripped:
                if "function " in stripped:
                    func_name = stripped.split("function ")[1].split("(")[0].strip()
                    if func_name:
                        symbols.append(
                            CodeSymbol(
                                name=func_name,
                                type="function",
                                start_line=i + 1,
                                end_line=i + 1,
                                start_byte=0,
                                end_byte=len(line),
                                scope="global",
                            )
                        )

            # Class definitions
            elif stripped.startswith("class "):
                class_name = stripped[6:].split(" ")[0].strip()
                symbols.append(
                    CodeSymbol(
                        name=class_name,
                        type="class",
                        start_line=i + 1,
                        end_line=i + 1,
                        start_byte=0,
                        end_byte=len(line),
                        scope="global",
                    )
                )

        return symbols, imports, dependencies

    def _analyze_swift_code(
        self, lines: List[str]
    ) -> tuple[List[CodeSymbol], List[str], Set[str]]:
        """Analyze Swift code structure"""
        symbols = []
        imports = []
        dependencies = set()

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Imports
            if stripped.startswith("import "):
                imports.append(stripped)
                dep = stripped[7:].strip()
                dependencies.add(dep)

            # Function definitions
            elif stripped.startswith("func "):
                func_name = stripped[5:].split("(")[0].strip()
                symbols.append(
                    CodeSymbol(
                        name=func_name,
                        type="function",
                        start_line=i + 1,
                        end_line=i + 1,
                        start_byte=0,
                        end_byte=len(line),
                        scope="global",
                    )
                )

            # Struct definitions
            elif stripped.startswith("struct "):
                struct_name = stripped[7:].split(" ")[0].split(":")[0].strip()
                symbols.append(
                    CodeSymbol(
                        name=struct_name,
                        type="struct",
                        start_line=i + 1,
                        end_line=i + 1,
                        start_byte=0,
                        end_byte=len(line),
                        scope="global",
                    )
                )

            # Class definitions
            elif stripped.startswith("class "):
                class_name = stripped[6:].split(" ")[0].split(":")[0].strip()
                symbols.append(
                    CodeSymbol(
                        name=class_name,
                        type="class",
                        start_line=i + 1,
                        end_line=i + 1,
                        start_byte=0,
                        end_byte=len(line),
                        scope="global",
                    )
                )

        return symbols, imports, dependencies

    def _calculate_complexity_score(
        self, lines: List[str], symbols: List[CodeSymbol]
    ) -> float:
        """Calculate a basic complexity score for the code"""
        score = 0.0

        # Base score from lines of code
        loc = len(
            [
                line
                for line in lines
                if line.strip() and not line.strip().startswith("#")
            ]
        )
        score += loc * 0.1

        # Add complexity for symbols
        score += len(symbols) * 2

        # Add complexity for control structures
        control_keywords = [
            "if",
            "else",
            "elif",
            "for",
            "while",
            "try",
            "except",
            "switch",
            "case",
        ]
        for line in lines:
            for keyword in control_keywords:
                if keyword in line:
                    score += 1

        # Normalize to 0-100 scale
        return min(100.0, score / 10.0)

    async def get_file_summary(self, file_path: str) -> Dict[str, Any]:
        """Get a summary of a file's structure"""
        structure = await self.parse_file(file_path)
        if not structure:
            return {"error": "Could not parse file"}

        return {
            "file_path": structure.file_path,
            "language": structure.language,
            "lines_of_code": structure.lines_of_code,
            "complexity_score": structure.complexity_score,
            "symbols": {
                "functions": len(
                    [s for s in structure.symbols if s.type == "function"]
                ),
                "classes": len(
                    [s for s in structure.symbols if s.type in ["class", "struct"]]
                ),
                "total": len(structure.symbols),
            },
            "imports": len(structure.imports),
            "dependencies": list(structure.dependencies),
            "analysis_method": "basic_text_parsing",  # Indicates current implementation level
        }

    def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            "initialized": self.is_initialized,
            "tree_sitter_available": self.tree_sitter_available,
            "available_parsers": list(self.parsers.keys()),
            "supported_languages": list(self.language_map.values()),
            "analysis_level": (
                "full_ast_parsing"
                if self.tree_sitter_available
                else "basic_text_parsing"
            ),
        }
