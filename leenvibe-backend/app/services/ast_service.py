"""
AST Analysis Service

Provides comprehensive Abstract Syntax Tree analysis using Tree-sitter parsers.
Includes symbol extraction, dependency analysis, and complexity metrics.
"""

import asyncio
import hashlib
import logging
import re
import time
from pathlib import Path
from typing import Dict, List, Optional

from ..models.ast_models import (
    ComplexityMetrics,
    Dependency,
    FileAnalysis,
    LanguageType,
    Symbol,
    SymbolType,
)
from .tree_sitter_parsers import tree_sitter_manager

logger = logging.getLogger(__name__)


from concurrent.futures import ThreadPoolExecutor


class ASTAnalysisService:
    """Main service for AST analysis and code understanding"""

    def __init__(self, executor: ThreadPoolExecutor):
        self.executor = executor
        self.initialized = False
        self.file_cache: Dict[str, FileAnalysis] = {}
        self.cache_timeout = 300  # 5 minutes

    async def initialize(self):
        """Initialize the AST analysis service"""
        try:
            logger.info("Initializing AST Analysis Service...")

            # Initialize tree-sitter parsers
            await tree_sitter_manager.initialize()

            self.initialized = True
            logger.info("AST Analysis Service initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize AST service: {e}")
            self.initialized = False

    async def parse_file(self, file_path: str) -> FileAnalysis:
        """Parse a single file and extract comprehensive analysis"""
        try:
            # Skip files we shouldn't parse (pragmatic filter)
            if self._should_skip_file(file_path):
                return FileAnalysis(
                    file_path=file_path,
                    language=LanguageType.UNKNOWN,
                    parsing_errors=[f"Skipped: {file_path}"],
                )

            # Check cache first
            cache_key = self._get_cache_key(file_path)
            if cache_key in self.file_cache:
                cached = self.file_cache[cache_key]
                if time.time() - cached.last_analyzed < self.cache_timeout:
                    return cached

            # Read file content
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            content = path.read_text(encoding="utf-8", errors="ignore")
            language = tree_sitter_manager.detect_language(file_path)

            # Initialize analysis result
            analysis = FileAnalysis(
                file_path=str(path.absolute()),
                language=language,
                last_analyzed=time.time(),
            )

            if language == LanguageType.UNKNOWN:
                analysis.parsing_errors.append(f"Unsupported file type: {file_path}")
                return analysis

            # Parse with tree-sitter
            tree, parsing_errors = await tree_sitter_manager.async_parse_file(
                file_path, content
            )
            analysis.parsing_errors.extend(parsing_errors)

            if tree is None:
                return analysis

            # Convert to our AST model
            source_bytes = content.encode("utf-8")
            analysis.ast_root = tree_sitter_manager.tree_to_ast_node(
                tree.root_node, source_bytes
            )

            # Extract symbols
            analysis.symbols = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: self._extract_symbols_sync(
                    tree, source_bytes, language, file_path
                ),
            )

            # Extract dependencies
            analysis.dependencies = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: self._extract_dependencies_sync(
                    tree, source_bytes, language, file_path
                ),
            )

            # Calculate complexity metrics
            analysis.complexity = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: self._calculate_complexity_sync(tree, source_bytes, language),
            )

            # Cache the result
            self.file_cache[cache_key] = analysis

            return analysis

        except Exception as e:
            # Only log errors for files we actually care about
            if not self._should_skip_file(file_path):
                logger.error(f"Error parsing file {file_path}: {e}")
            return FileAnalysis(
                file_path=file_path,
                language=LanguageType.UNKNOWN,
                parsing_errors=[f"Analysis failed: {str(e)}"],
            )

    def _should_skip_file(self, file_path: str) -> bool:
        """Pragmatic filter to skip files we don't want to parse"""
        path_str = file_path.lower()
        
        # Skip dependency directories
        skip_patterns = [
            '/site-packages/',
            '/.venv/',
            '/venv/',
            '/env/',
            '/node_modules/',
            '/__pycache__/',
            '/.git/',
            '/build/',
            '/dist/',
            '.pyc',
            '.pyo',
            '.so',
            '.dylib',
        ]
        
        for pattern in skip_patterns:
            if pattern in path_str:
                return True
                
        return False

    def _extract_symbols_sync(
        self, tree, source_bytes: bytes, language: LanguageType, file_path: str
    ) -> List[Symbol]:
        """Extract symbols (functions, classes, variables) from the AST"""
        symbols = []

        try:
            if language == LanguageType.PYTHON:
                symbols.extend(
                    self._extract_python_symbols(
                        tree.root_node, source_bytes, file_path
                    )
                )
            elif language in [LanguageType.JAVASCRIPT, LanguageType.TYPESCRIPT]:
                symbols.extend(
                    self._extract_js_symbols(tree.root_node, source_bytes, file_path)
                )

        except Exception as e:
            logger.error(f"Error extracting symbols: {e}")

        return symbols

    def _extract_python_symbols(
        self, root, source_bytes: bytes, file_path: str
    ) -> List[Symbol]:
        """Extract Python symbols"""
        symbols = []

        # Function definitions
        function_nodes = tree_sitter_manager.find_nodes_by_type(
            root, ["function_definition"]
        )
        for node in function_nodes:
            symbol = self._create_python_function_symbol(node, source_bytes, file_path)
            if symbol:
                symbols.append(symbol)

        # Class definitions
        class_nodes = tree_sitter_manager.find_nodes_by_type(root, ["class_definition"])
        for node in class_nodes:
            symbol = self._create_python_class_symbol(node, source_bytes, file_path)
            if symbol:
                symbols.append(symbol)

        # Variable assignments (top-level only)
        assignment_nodes = tree_sitter_manager.find_nodes_by_type(root, ["assignment"])
        for node in assignment_nodes:
            # Only extract top-level assignments
            if self._is_top_level_node(node):
                symbol = self._create_python_variable_symbol(
                    node, source_bytes, file_path
                )
                if symbol:
                    symbols.append(symbol)

        return symbols

    def _create_python_function_symbol(
        self, node, source_bytes: bytes, file_path: str
    ) -> Optional[Symbol]:
        """Create symbol for Python function"""
        try:
            # Find function name
            name_node = None
            for child in node.children:
                if child.type == "identifier":
                    name_node = child
                    break

            if not name_node:
                return None

            name = tree_sitter_manager.get_node_text(name_node, source_bytes)

            # Extract parameters
            parameters = []
            param_nodes = tree_sitter_manager.find_nodes_by_type(node, ["parameter"])
            for param_node in param_nodes:
                param_name = tree_sitter_manager.get_node_text(param_node, source_bytes)
                if param_name and param_name != "self":
                    parameters.append(param_name)

            # Extract docstring
            docstring = self._extract_python_docstring(node, source_bytes)

            # Check if async
            is_async = any(child.type == "async" for child in node.children)

            # Calculate complexity
            complexity = self._calculate_cyclomatic_complexity(node)

            return Symbol(
                id=f"{file_path}:{name}:{node.start_point[0]}",
                name=name,
                symbol_type=SymbolType.FUNCTION,
                file_path=file_path,
                line_start=node.start_point[0] + 1,
                line_end=node.end_point[0] + 1,
                column_start=node.start_point[1],
                column_end=node.end_point[1],
                signature=tree_sitter_manager.get_node_text(node, source_bytes)[:200],
                docstring=docstring,
                is_async=is_async,
                parameters=parameters,
                complexity=complexity,
            )

        except Exception as e:
            logger.error(f"Error creating function symbol: {e}")
            return None

    def _create_python_class_symbol(
        self, node, source_bytes: bytes, file_path: str
    ) -> Optional[Symbol]:
        """Create symbol for Python class"""
        try:
            # Find class name
            name_node = None
            for child in node.children:
                if child.type == "identifier":
                    name_node = child
                    break

            if not name_node:
                return None

            name = tree_sitter_manager.get_node_text(name_node, source_bytes)

            # Extract docstring
            docstring = self._extract_python_docstring(node, source_bytes)

            return Symbol(
                id=f"{file_path}:{name}:{node.start_point[0]}",
                name=name,
                symbol_type=SymbolType.CLASS,
                file_path=file_path,
                line_start=node.start_point[0] + 1,
                line_end=node.end_point[0] + 1,
                column_start=node.start_point[1],
                column_end=node.end_point[1],
                signature=tree_sitter_manager.get_node_text(node, source_bytes)[:200],
                docstring=docstring,
            )

        except Exception as e:
            logger.error(f"Error creating class symbol: {e}")
            return None

    def _create_python_variable_symbol(
        self, node, source_bytes: bytes, file_path: str
    ) -> Optional[Symbol]:
        """Create symbol for Python variable"""
        try:
            # Find variable name (left side of assignment)
            for child in node.children:
                if child.type == "identifier":
                    name = tree_sitter_manager.get_node_text(child, source_bytes)

                    # Skip private variables and common patterns
                    if name.startswith("_") or name in ["__name__", "__file__"]:
                        return None

                    # Determine if it's a constant (all caps)
                    symbol_type = (
                        SymbolType.CONSTANT if name.isupper() else SymbolType.VARIABLE
                    )

                    return Symbol(
                        id=f"{file_path}:{name}:{node.start_point[0]}",
                        name=name,
                        symbol_type=symbol_type,
                        file_path=file_path,
                        line_start=node.start_point[0] + 1,
                        line_end=node.end_point[0] + 1,
                        column_start=node.start_point[1],
                        column_end=node.end_point[1],
                        signature=tree_sitter_manager.get_node_text(node, source_bytes)[
                            :100
                        ],
                    )

            return None

        except Exception as e:
            logger.error(f"Error creating variable symbol: {e}")
            return None

    def _extract_js_symbols(
        self, root, source_bytes: bytes, file_path: str
    ) -> List[Symbol]:
        """Extract JavaScript/TypeScript symbols"""
        symbols = []

        # Function declarations
        function_nodes = tree_sitter_manager.find_nodes_by_type(
            root, ["function_declaration", "arrow_function", "method_definition"]
        )
        for node in function_nodes:
            symbol = self._create_js_function_symbol(node, source_bytes, file_path)
            if symbol:
                symbols.append(symbol)

        # Class declarations
        class_nodes = tree_sitter_manager.find_nodes_by_type(
            root, ["class_declaration"]
        )
        for node in class_nodes:
            symbol = self._create_js_class_symbol(node, source_bytes, file_path)
            if symbol:
                symbols.append(symbol)

        # Variable declarations
        var_nodes = tree_sitter_manager.find_nodes_by_type(
            root, ["variable_declarator", "lexical_declaration"]
        )
        for node in var_nodes:
            if self._is_top_level_node(node):
                symbol = self._create_js_variable_symbol(node, source_bytes, file_path)
                if symbol:
                    symbols.append(symbol)

        return symbols

    def _create_js_function_symbol(
        self, node, source_bytes: bytes, file_path: str
    ) -> Optional[Symbol]:
        """Create symbol for JavaScript function"""
        try:
            # Extract function name
            name = "anonymous"
            for child in node.children:
                if child.type == "identifier":
                    name = tree_sitter_manager.get_node_text(child, source_bytes)
                    break

            # Extract parameters
            parameters = []
            param_nodes = tree_sitter_manager.find_nodes_by_type(
                node, ["formal_parameter", "identifier"]
            )
            for param_node in param_nodes:
                param_name = tree_sitter_manager.get_node_text(param_node, source_bytes)
                if param_name and param_name not in parameters:
                    parameters.append(param_name)

            # Check if async
            is_async = any(child.type == "async" for child in node.children)

            return Symbol(
                id=f"{file_path}:{name}:{node.start_point[0]}",
                name=name,
                symbol_type=SymbolType.FUNCTION,
                file_path=file_path,
                line_start=node.start_point[0] + 1,
                line_end=node.end_point[0] + 1,
                column_start=node.start_point[1],
                column_end=node.end_point[1],
                signature=tree_sitter_manager.get_node_text(node, source_bytes)[:200],
                is_async=is_async,
                parameters=parameters,
            )

        except Exception as e:
            logger.error(f"Error creating JS function symbol: {e}")
            return None

    def _create_js_class_symbol(
        self, node, source_bytes: bytes, file_path: str
    ) -> Optional[Symbol]:
        """Create symbol for JavaScript class"""
        try:
            # Find class name
            name = "anonymous"
            for child in node.children:
                if child.type == "identifier":
                    name = tree_sitter_manager.get_node_text(child, source_bytes)
                    break

            return Symbol(
                id=f"{file_path}:{name}:{node.start_point[0]}",
                name=name,
                symbol_type=SymbolType.CLASS,
                file_path=file_path,
                line_start=node.start_point[0] + 1,
                line_end=node.end_point[0] + 1,
                column_start=node.start_point[1],
                column_end=node.end_point[1],
                signature=tree_sitter_manager.get_node_text(node, source_bytes)[:200],
            )

        except Exception as e:
            logger.error(f"Error creating JS class symbol: {e}")
            return None

    def _create_js_variable_symbol(
        self, node, source_bytes: bytes, file_path: str
    ) -> Optional[Symbol]:
        """Create symbol for JavaScript variable"""
        try:
            # Find variable name
            for child in node.children:
                if child.type == "identifier":
                    name = tree_sitter_manager.get_node_text(child, source_bytes)

                    # Determine symbol type
                    symbol_type = (
                        SymbolType.CONSTANT if name.isupper() else SymbolType.VARIABLE
                    )

                    return Symbol(
                        id=f"{file_path}:{name}:{node.start_point[0]}",
                        name=name,
                        symbol_type=symbol_type,
                        file_path=file_path,
                        line_start=node.start_point[0] + 1,
                        line_end=node.end_point[0] + 1,
                        column_start=node.start_point[1],
                        column_end=node.end_point[1],
                        signature=tree_sitter_manager.get_node_text(node, source_bytes)[
                            :100
                        ],
                    )

            return None

        except Exception as e:
            logger.error(f"Error creating JS variable symbol: {e}")
            return None

    def _extract_dependencies_sync(
        self, tree, source_bytes: bytes, language: LanguageType, file_path: str
    ) -> List[Dependency]:
        """Extract file dependencies (imports, requires, etc.)"""
        dependencies = []

        try:
            # Extract imports using tree-sitter manager (synchronous version)
            imports = tree_sitter_manager.extract_imports(
                tree, source_bytes, language
            )

            for import_info in imports:
                dependency = Dependency(
                    source_file=file_path,
                    dependency_type=import_info["type"],
                    line_number=import_info["line"],
                    module_name=import_info.get("module", ""),
                    is_external=self._is_external_module(import_info.get("module", "")),
                )
                dependencies.append(dependency)

        except Exception as e:
            logger.error(f"Error extracting dependencies: {e}")

        return dependencies

    def _calculate_complexity_sync(
        self, tree, source_bytes: bytes, language: LanguageType
    ) -> ComplexityMetrics:
        """Calculate various complexity metrics for the file"""
        try:
            metrics = ComplexityMetrics()

            # Lines of code
            lines = source_bytes.decode("utf-8", errors="ignore").split("\n")
            metrics.lines_of_code = len([line for line in lines if line.strip()])

            # Count functions and classes
            functions = tree_sitter_manager.find_nodes_by_type(
                tree.root_node,
                ["function_definition", "function_declaration", "method_definition"],
            )
            classes = tree_sitter_manager.find_nodes_by_type(
                tree.root_node, ["class_definition", "class_declaration"]
            )

            metrics.number_of_functions = len(functions)
            metrics.number_of_classes = len(classes)

            # Calculate cyclomatic complexity (sum of all functions)
            total_complexity = 0
            for func_node in functions:
                complexity = self._calculate_cyclomatic_complexity(func_node)
                total_complexity += complexity

            metrics.cyclomatic_complexity = total_complexity

            # Calculate maintainability index (simplified)
            if metrics.lines_of_code > 0:
                metrics.maintainability_index = max(
                    0,
                    171
                    - 5.2
                    * (
                        metrics.cyclomatic_complexity / metrics.number_of_functions
                        if metrics.number_of_functions > 0
                        else 0
                    )
                    - 0.23 * metrics.lines_of_code / 100,
                )

            return metrics

        except Exception as e:
            logger.error(f"Error calculating complexity: {e}")
            return ComplexityMetrics()

    def _calculate_cyclomatic_complexity(self, node) -> int:
        """Calculate cyclomatic complexity for a function node"""
        complexity = 1  # Base complexity

        # Count decision points
        decision_nodes = [
            "if_statement",
            "while_statement",
            "for_statement",
            "try_statement",
            "except_clause",
            "case_clause",
            "conditional_expression",
            "and",
            "or",
        ]

        def count_decisions(n):
            count = 0
            if n.type in decision_nodes:
                count += 1
            for child in n.children:
                count += count_decisions(child)
            return count

        complexity += count_decisions(node)
        return complexity

    def _extract_python_docstring(self, node, source_bytes: bytes) -> Optional[str]:
        """Extract docstring from Python function or class"""
        try:
            # Look for string literal as first statement in the body
            for child in node.children:
                if child.type == "block":
                    for stmt in child.children:
                        if stmt.type == "expression_statement":
                            for expr in stmt.children:
                                if expr.type == "string":
                                    docstring = tree_sitter_manager.get_node_text(
                                        expr, source_bytes
                                    )
                                    # Clean up the docstring
                                    return docstring.strip('"""').strip("'''").strip()
            return None
        except Exception:
            return None

    def _is_top_level_node(self, node) -> bool:
        """Check if a node is at the top level (not nested in functions/classes)"""
        parent = node.parent
        while parent:
            if parent.type in [
                "function_definition",
                "class_definition",
                "method_definition",
            ]:
                return False
            parent = parent.parent
        return True

    def _is_external_module(self, module_name: str) -> bool:
        """Determine if a module is external (not part of current project)"""
        if not module_name:
            return False

        # Common patterns for external modules
        external_patterns = [
            # Python standard library and common packages
            r"^(os|sys|json|re|datetime|collections|itertools|functools|math|random)",
            r"^(requests|numpy|pandas|django|flask|fastapi|sqlalchemy)",
            # JavaScript/Node.js common packages
            r"^(fs|path|http|https|url|crypto|util)",
            r"^(react|vue|angular|express|lodash|axios|moment)",
            # Relative imports are internal
            r"^\.",
        ]

        # Check if it matches external patterns
        for pattern in external_patterns:
            if re.match(pattern, module_name):
                return not module_name.startswith(".")

        # If it contains a dot and doesn't start with dot, likely external
        if "." in module_name and not module_name.startswith("."):
            return True

        return False

    def _get_cache_key(self, file_path: str) -> str:
        """Generate cache key for file"""
        return hashlib.md5(file_path.encode()).hexdigest()

    async def clear_cache(self):
        """Clear the file analysis cache"""
        self.file_cache.clear()

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        return {
            "cached_files": len(self.file_cache),
            "cache_timeout": self.cache_timeout,
        }


# Global instance
ast_service = ASTAnalysisService(ThreadPoolExecutor(max_workers=2))
