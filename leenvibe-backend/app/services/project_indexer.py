"""
Project Indexing Service

Handles project-wide code indexing, symbol cross-referencing, and dependency analysis.
"""

import asyncio
import fnmatch
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from ..models.ast_models import (
    CallGraph,
    Dependency,
    DependencyGraph,
    FileAnalysis,
    LanguageType,
    ProjectIndex,
    Reference,
    Symbol,
)
from .ast_service import ASTAnalysisService
from .tree_sitter_parsers import TreeSitterManager

logger = logging.getLogger(__name__)


class ProjectIndexer:
    """Indexes and analyzes entire projects for code understanding"""

    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.default_excludes = [
            "*.pyc",
            "__pycache__",
            ".git",
            ".svn",
            ".hg",
            "node_modules",
            ".venv",
            "venv",
            "env",
            ".build",
            "build",
            "dist",
            "target",
            "*.min.js",
            "*.bundle.js",
            "*.map",
        ]
        self.supported_extensions = {
            ".py",
            ".js",
            ".ts",
            ".jsx",
            ".tsx",
            ".swift",
            ".go",
            ".rs",
        }

    async def index_project(
        self,
        workspace_path: str,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
    ) -> ProjectIndex:
        """Index an entire project"""
        try:
            start_time = time.time()
            logger.info(f"Starting project indexing: {workspace_path}")

            # Initialize project index
            project_index = ProjectIndex(
                workspace_path=workspace_path, last_indexed=time.time()
            )

            # Discover code files
            code_files = await self._discover_code_files(
                workspace_path, include_patterns, exclude_patterns
            )
            project_index.total_files = len(code_files)

            logger.info(f"Found {len(code_files)} code files to analyze")

            # Analyze files in batches for performance
            batch_size = 10
            for i in range(0, len(code_files), batch_size):
                batch = code_files[i : i + batch_size]
                batch_results = await self._analyze_file_batch(batch)

                for file_path, analysis in batch_results.items():
                    if analysis.parsing_errors:
                        project_index.parsing_errors += 1
                    else:
                        project_index.supported_files += 1

                    # Store file analysis
                    project_index.files[file_path] = analysis

                    # Index symbols
                    for symbol in analysis.symbols:
                        project_index.symbols[symbol.id] = symbol

                    # Store dependencies
                    project_index.dependencies.extend(analysis.dependencies)

                # Progress logging
                analyzed = min(i + batch_size, len(code_files))
                logger.info(f"Analyzed {analyzed}/{len(code_files)} files")

            # Build cross-references
            await self._build_cross_references(project_index)

            # Calculate project metrics
            await self._calculate_project_metrics(project_index)

            duration = time.time() - start_time
            logger.info(f"Project indexing completed in {duration:.2f}s")

            return project_index

        except Exception as e:
            logger.error(f"Error indexing project {workspace_path}: {e}")
            return ProjectIndex(workspace_path=workspace_path, last_indexed=time.time())

    async def _discover_code_files(
        self,
        workspace_path: str,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
    ) -> List[str]:
        """Discover all code files in the project"""
        try:
            workspace = Path(workspace_path)
            if not workspace.exists():
                logger.error(f"Workspace path does not exist: {workspace_path}")
                return []

            # Combine default and custom exclude patterns
            all_excludes = self.default_excludes.copy()
            if exclude_patterns:
                all_excludes.extend(exclude_patterns)

            code_files = []

            def should_exclude(path: Path) -> bool:
                """Check if path should be excluded"""
                path_str = str(path)
                relative_path = str(path.relative_to(workspace))

                for pattern in all_excludes:
                    if fnmatch.fnmatch(path.name, pattern) or fnmatch.fnmatch(
                        relative_path, pattern
                    ):
                        return True
                return False

            def should_include(path: Path) -> bool:
                """Check if file should be included based on extension"""
                return path.suffix.lower() in self.supported_extensions

            # Walk directory tree
            for path in workspace.rglob("*"):
                if path.is_file() and should_include(path) and not should_exclude(path):
                    code_files.append(str(path.absolute()))

            return sorted(code_files)

        except Exception as e:
            logger.error(f"Error discovering code files: {e}")
            return []

    async def _analyze_file_batch(
        self, file_paths: List[str]
    ) -> Dict[str, FileAnalysis]:
        """Analyze a batch of files concurrently"""
        try:
            # Create analysis tasks
            tasks = []
            for file_path in file_paths:
                task = asyncio.create_task(ast_service.parse_file(file_path))
                tasks.append((file_path, task))

            # Wait for all analyses to complete
            results = {}
            for file_path, task in tasks:
                try:
                    analysis = await task
                    results[file_path] = analysis
                except Exception as e:
                    logger.error(f"Error analyzing {file_path}: {e}")
                    # Create minimal analysis for failed files
                    results[file_path] = FileAnalysis(
                        file_path=file_path,
                        language=LanguageType.UNKNOWN,
                        parsing_errors=[f"Analysis failed: {str(e)}"],
                    )

            return results

        except Exception as e:
            logger.error(f"Error in batch analysis: {e}")
            return {}

    async def _build_cross_references(self, project_index: ProjectIndex):
        """Build cross-references between symbols and dependencies"""
        try:
            logger.info("Building cross-references...")

            # Create symbol lookup by name for quick reference resolution
            symbol_by_name: Dict[str, List[Symbol]] = {}
            for symbol in project_index.symbols.values():
                if symbol.name not in symbol_by_name:
                    symbol_by_name[symbol.name] = []
                symbol_by_name[symbol.name].append(symbol)

            # Resolve dependency targets
            for dependency in project_index.dependencies:
                if dependency.module_name and not dependency.is_external:
                    # Try to resolve internal module dependencies
                    target_file = self._resolve_module_path(
                        dependency.module_name,
                        dependency.source_file,
                        project_index.workspace_path,
                    )
                    if target_file:
                        dependency.target_file = target_file

            logger.info("Cross-references built successfully")

        except Exception as e:
            logger.error(f"Error building cross-references: {e}")

    def _resolve_module_path(
        self, module_name: str, source_file: str, workspace_path: str
    ) -> Optional[str]:
        """Resolve a module name to a file path"""
        try:
            source_dir = Path(source_file).parent
            workspace = Path(workspace_path)

            # Handle relative imports
            if module_name.startswith("."):
                # Relative import
                relative_parts = module_name.lstrip(".").split(".")
                target_dir = source_dir

                # Go up directories for each leading dot
                dots = len(module_name) - len(module_name.lstrip("."))
                for _ in range(dots - 1):
                    target_dir = target_dir.parent

                # Navigate to target module
                for part in relative_parts:
                    if part:
                        target_dir = target_dir / part

                # Check for file variations
                candidates = [
                    target_dir.with_suffix(".py"),
                    target_dir / "__init__.py",
                    target_dir.with_suffix(".js"),
                    target_dir.with_suffix(".ts"),
                ]

                for candidate in candidates:
                    if candidate.exists() and candidate.is_relative_to(workspace):
                        return str(candidate.absolute())

            else:
                # Absolute import - search in workspace
                module_parts = module_name.split(".")

                # Start from workspace root
                target_path = workspace
                for part in module_parts:
                    target_path = target_path / part

                # Check for file variations
                candidates = [
                    target_path.with_suffix(".py"),
                    target_path / "__init__.py",
                    target_path.with_suffix(".js"),
                    target_path.with_suffix(".ts"),
                ]

                for candidate in candidates:
                    if candidate.exists():
                        return str(candidate.absolute())

            return None

        except Exception as e:
            logger.debug(f"Could not resolve module {module_name}: {e}")
            return None

    async def _calculate_project_metrics(self, project_index: ProjectIndex):
        """Calculate project-wide metrics and statistics"""
        try:
            logger.info("Calculating project metrics...")

            # Count symbols by type
            symbol_counts = {}
            for symbol in project_index.symbols.values():
                symbol_type = symbol.symbol_type
                symbol_counts[symbol_type] = symbol_counts.get(symbol_type, 0) + 1

            # Count languages
            language_counts = {}
            for analysis in project_index.files.values():
                lang = analysis.language
                language_counts[lang] = language_counts.get(lang, 0) + 1

            # Calculate total complexity
            total_complexity = sum(
                analysis.complexity.cyclomatic_complexity
                for analysis in project_index.files.values()
            )

            # Store metrics in project index (could extend model for this)
            logger.info(f"Project metrics: {symbol_counts}")
            logger.info(f"Languages: {language_counts}")
            logger.info(f"Total complexity: {total_complexity}")

        except Exception as e:
            logger.error(f"Error calculating project metrics: {e}")

    async def update_file_index(
        self, project_index: ProjectIndex, file_path: str
    ) -> bool:
        """Update the index for a single file"""
        try:
            logger.info(f"Updating index for file: {file_path}")

            # Remove old analysis if it exists
            old_analysis = project_index.files.get(file_path)
            if old_analysis:
                # Remove old symbols
                for symbol in old_analysis.symbols:
                    project_index.symbols.pop(symbol.id, None)

                # Remove old dependencies
                project_index.dependencies = [
                    dep
                    for dep in project_index.dependencies
                    if dep.source_file != file_path
                ]

            # Analyze the file
            new_analysis = await ast_service.parse_file(file_path)

            # Update project index
            project_index.files[file_path] = new_analysis

            # Add new symbols
            for symbol in new_analysis.symbols:
                project_index.symbols[symbol.id] = symbol

            # Add new dependencies
            project_index.dependencies.extend(new_analysis.dependencies)

            # Update timestamp
            project_index.last_indexed = time.time()

            logger.info(f"Successfully updated index for {file_path}")
            return True

        except Exception as e:
            logger.error(f"Error updating file index for {file_path}: {e}")
            return False

    async def find_references(
        self, project_index: ProjectIndex, symbol_name: str
    ) -> List[Reference]:
        """Find all references to a symbol across the project"""
        try:
            references = []

            # Find symbol definitions
            matching_symbols = [
                symbol
                for symbol in project_index.symbols.values()
                if symbol.name == symbol_name
            ]

            for symbol in matching_symbols:
                # Add definition reference
                references.append(
                    Reference(
                        symbol_id=symbol.id,
                        file_path=symbol.file_path,
                        line_number=symbol.line_start,
                        column_number=symbol.column_start,
                        reference_type="definition",
                        context=f"Definition of {symbol.symbol_type} {symbol.name}",
                    )
                )

            # Search for usages in all files (simplified - would need better AST analysis)
            for file_path, analysis in project_index.files.items():
                if analysis.ast_root:
                    # This is a simplified search - in practice, we'd need more sophisticated analysis
                    try:
                        content = Path(file_path).read_text(
                            encoding="utf-8", errors="ignore"
                        )
                        lines = content.split("\n")

                        for line_num, line in enumerate(lines, 1):
                            if symbol_name in line and not line.strip().startswith("#"):
                                references.append(
                                    Reference(
                                        symbol_id=f"usage_{file_path}_{line_num}",
                                        file_path=file_path,
                                        line_number=line_num,
                                        column_number=line.find(symbol_name),
                                        reference_type="usage",
                                        context=line.strip(),
                                    )
                                )
                    except Exception:
                        continue

            return references

        except Exception as e:
            logger.error(f"Error finding references for {symbol_name}: {e}")
            return []

    async def get_call_graph(self, project_index: ProjectIndex) -> CallGraph:
        """Generate a call graph from the project index"""
        try:
            call_graph = CallGraph()

            # Add all function symbols as nodes
            for symbol in project_index.symbols.values():
                if symbol.symbol_type in [symbol.FUNCTION, symbol.METHOD]:
                    call_graph.nodes[symbol.id] = symbol

            # Analyze function calls (simplified implementation)
            # In practice, this would require more sophisticated AST analysis
            for file_path, analysis in project_index.files.items():
                # This is a placeholder - would need proper call analysis
                pass

            return call_graph

        except Exception as e:
            logger.error(f"Error generating call graph: {e}")
            return CallGraph()

    async def get_dependency_graph(
        self, project_index: ProjectIndex
    ) -> DependencyGraph:
        """Generate a dependency graph from the project index"""
        try:
            dependency_graph = DependencyGraph()

            # Add all files as nodes
            for file_path in project_index.files.keys():
                dependency_graph.nodes.append(file_path)

            # Add dependency edges
            for dependency in project_index.dependencies:
                if dependency.target_file and not dependency.is_external:
                    edge = (dependency.source_file, dependency.target_file)
                    if edge not in dependency_graph.edges:
                        dependency_graph.edges.append(edge)

            # Detect cycles (simplified)
            dependency_graph.cycles = await self._detect_dependency_cycles(
                dependency_graph
            )

            return dependency_graph

        except Exception as e:
            logger.error(f"Error generating dependency graph: {e}")
            return DependencyGraph()

    async def _detect_dependency_cycles(
        self, graph: DependencyGraph
    ) -> List[List[str]]:
        """Detect circular dependencies in the graph"""
        try:
            cycles = []
            visited = set()
            rec_stack = set()

            def dfs(node: str, path: List[str]) -> bool:
                visited.add(node)
                rec_stack.add(node)
                path.append(node)

                # Get neighbors
                neighbors = [target for source, target in graph.edges if source == node]

                for neighbor in neighbors:
                    if neighbor not in visited:
                        if dfs(neighbor, path.copy()):
                            return True
                    elif neighbor in rec_stack:
                        # Found a cycle
                        cycle_start = path.index(neighbor)
                        cycle = path[cycle_start:] + [neighbor]
                        cycles.append(cycle)

                rec_stack.remove(node)
                return False

            for node in graph.nodes:
                if node not in visited:
                    dfs(node, [])

            return cycles

        except Exception as e:
            logger.error(f"Error detecting cycles: {e}")
            return []

    def get_supported_extensions(self) -> Set[str]:
        """Get set of supported file extensions"""
        return self.supported_extensions.copy()

    def add_supported_extension(self, extension: str):
        """Add a supported file extension"""
        self.supported_extensions.add(extension.lower())

    def set_exclude_patterns(self, patterns: List[str]):
        """Set custom exclude patterns"""
        self.default_excludes = patterns.copy()


# Global instance
project_indexer = ProjectIndexer()
ast_service = ASTAnalysisService(project_indexer.executor)
tree_sitter_manager = TreeSitterManager(project_indexer.executor)
