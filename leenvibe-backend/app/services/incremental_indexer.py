"""
Incremental Project Indexer

Extends the basic project indexer with incremental updates, intelligent caching,
and performance optimization for real-time code analysis.
"""

import asyncio
import hashlib
import json
import logging
import pickle
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import aiofiles

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
from ..models.monitoring_models import ChangeType, FileChange
from .ast_service import ast_service
from .cache_invalidation_service import cache_invalidation_service
from .cache_warming_service import cache_warming_service
from .graph_service import graph_service
from .project_indexer import project_indexer

logger = logging.getLogger(__name__)


@dataclass
class FileIndexEntry:
    """Metadata for indexed file tracking"""

    file_path: str
    content_hash: str
    last_modified: float
    file_size: int
    analysis_timestamp: float
    symbols_count: int
    dependencies_count: int
    language: Optional[str] = None
    parsing_errors: int = 0


@dataclass
class IncrementalIndexCache:
    """Cache structure for incremental indexing"""

    project_path: str
    cache_version: str
    last_full_index: float
    file_entries: Dict[str, FileIndexEntry]
    project_metadata: Dict[str, Any]
    dependency_graph_hash: str
    symbol_registry_hash: str
    created_at: float
    updated_at: float


class IncrementalProjectIndexer:
    """
    Incremental Project Indexer

    Provides intelligent incremental indexing with change detection,
    smart caching, and performance optimization for real-time analysis.
    """

    def __init__(self, cache_dir: str = "./.leenvibe_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.executor = ThreadPoolExecutor(max_workers=6)

        # Cache configuration
        self.cache_version = "1.0.0"
        self.full_index_interval = 3600  # 1 hour - force full reindex
        self.max_cache_age = 86400  # 24 hours
        self.batch_size = 15

        # Performance tracking
        self.metrics = {
            "incremental_updates": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "files_reanalyzed": 0,
            "symbols_updated": 0,
            "total_indexing_time": 0.0,
        }

        # Register with cache invalidation service
        self._register_with_cache_service()

    def _register_with_cache_service(self):
        """Register this indexer with the cache invalidation service"""
        try:
            cache_invalidation_service.register_cache_handler(self)
        except Exception as e:
            logger.warning(f"Could not register with cache invalidation service: {e}")

    async def get_or_create_project_index(
        self,
        workspace_path: str,
        force_full_reindex: bool = False,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
    ) -> ProjectIndex:
        """Get existing project index or create/update incrementally"""
        try:
            start_time = time.time()
            workspace_path = str(Path(workspace_path).absolute())

            logger.info(f"Getting project index for: {workspace_path}")

            # Load existing cache
            cache = await self._load_cache(workspace_path)

            # Determine if full reindex is needed
            needs_full_reindex = (
                force_full_reindex or cache is None or self._needs_full_reindex(cache)
            )

            if needs_full_reindex:
                logger.info("Performing full project reindex")
                project_index = await self._full_reindex(
                    workspace_path, include_patterns, exclude_patterns
                )
                await self._save_cache(workspace_path, project_index)

                # Build dependency graph for cache invalidation service
                await cache_invalidation_service.build_dependency_graph(project_index)
            else:
                logger.info("Performing incremental project update")
                project_index = await self._incremental_update(
                    workspace_path, cache, include_patterns, exclude_patterns
                )
                await self._save_cache(workspace_path, project_index)

                # Update dependency graph for cache invalidation service
                await cache_invalidation_service.build_dependency_graph(project_index)

            # Update metrics
            indexing_time = time.time() - start_time
            self.metrics["total_indexing_time"] += indexing_time

            logger.info(
                f"Project indexing completed in {indexing_time:.2f}s "
                f"({project_index.supported_files} files, "
                f"{len(project_index.symbols)} symbols)"
            )

            # Track project access for cache warming
            cache_warming_service.track_project_access(
                workspace_path,
                "indexer",
                {
                    "files_accessed": project_index.supported_files,
                    "symbols_queried": len(project_index.symbols),
                    "analysis_requests": 1,
                },
            )

            return project_index

        except Exception as e:
            logger.error(f"Error in incremental indexing: {e}")
            # Fallback to basic indexing
            return await project_indexer.index_project(
                workspace_path, include_patterns, exclude_patterns
            )

    async def update_from_file_changes(
        self, workspace_path: str, file_changes: List[FileChange]
    ) -> Optional[ProjectIndex]:
        """Update project index based on file changes from monitoring"""
        try:
            if not file_changes:
                return None

            start_time = time.time()
            workspace_path = str(Path(workspace_path).absolute())

            logger.info(f"Updating index from {len(file_changes)} file changes")

            # Load existing cache
            cache = await self._load_cache(workspace_path)
            if not cache:
                logger.warning("No cache found, performing full reindex")
                return await self.get_or_create_project_index(workspace_path)

            # Process file changes
            updated_files = set()
            removed_files = set()

            for change in file_changes:
                if change.change_type in [ChangeType.MODIFIED, ChangeType.CREATED]:
                    if change.is_code_file():
                        updated_files.add(change.file_path)
                elif change.change_type == ChangeType.DELETED:
                    removed_files.add(change.file_path)
                elif change.change_type in [ChangeType.MOVED, ChangeType.RENAMED]:
                    if change.old_path:
                        removed_files.add(change.old_path)
                    if change.is_code_file():
                        updated_files.add(change.file_path)

            # Update cache with changes
            updated_cache = await self._apply_file_changes(
                cache, updated_files, removed_files
            )

            # Convert cache to project index
            project_index = await self._cache_to_project_index(updated_cache)

            # Save updated cache
            await self._save_cache(workspace_path, project_index)

            # Trigger cache invalidation for changed files
            if updated_files or removed_files:
                logger.debug(
                    f"Triggering cache invalidation for {len(file_changes)} file changes"
                )
                await cache_invalidation_service.invalidate_multiple_files(file_changes)

                # Update dependency graph with new project index
                await cache_invalidation_service.build_dependency_graph(project_index)

            # Update metrics
            self.metrics["incremental_updates"] += 1
            self.metrics["files_reanalyzed"] += len(updated_files)

            indexing_time = time.time() - start_time
            logger.info(
                f"Incremental update completed in {indexing_time:.2f}s "
                f"({len(updated_files)} updated, {len(removed_files)} removed)"
            )

            return project_index

        except Exception as e:
            logger.error(f"Error in incremental update from file changes: {e}")
            return None

    async def _load_cache(self, workspace_path: str) -> Optional[IncrementalIndexCache]:
        """Load incremental index cache"""
        try:
            cache_file = self._get_cache_file_path(workspace_path)

            if not cache_file.exists():
                logger.debug(f"No cache file found: {cache_file}")
                return None

            # Check cache age
            cache_age = time.time() - cache_file.stat().st_mtime
            if cache_age > self.max_cache_age:
                logger.info(f"Cache expired (age: {cache_age/3600:.1f}h), removing")
                cache_file.unlink()
                return None

            async with aiofiles.open(cache_file, "rb") as f:
                cache_data = await f.read()
                cache = pickle.loads(cache_data)

            # Validate cache version
            if cache.cache_version != self.cache_version:
                logger.info("Cache version mismatch, invalidating")
                return None

            logger.debug(f"Loaded cache with {len(cache.file_entries)} file entries")
            self.metrics["cache_hits"] += 1

            return cache

        except Exception as e:
            logger.error(f"Error loading cache: {e}")
            self.metrics["cache_misses"] += 1
            return None

    async def _save_cache(self, workspace_path: str, project_index: ProjectIndex):
        """Save project index to incremental cache"""
        try:
            cache_file = self._get_cache_file_path(workspace_path)

            # Create file entries from project index
            file_entries = {}
            for file_path, analysis in project_index.files.items():
                file_entries[file_path] = FileIndexEntry(
                    file_path=file_path,
                    content_hash=await self._calculate_file_hash(file_path),
                    last_modified=Path(file_path).stat().st_mtime,
                    file_size=Path(file_path).stat().st_size,
                    analysis_timestamp=time.time(),
                    symbols_count=len(analysis.symbols),
                    dependencies_count=len(analysis.dependencies),
                    language=analysis.language.value if analysis.language else None,
                    parsing_errors=(
                        len(analysis.parsing_errors) if analysis.parsing_errors else 0
                    ),
                )

            # Create cache object
            cache = IncrementalIndexCache(
                project_path=workspace_path,
                cache_version=self.cache_version,
                last_full_index=time.time(),
                file_entries=file_entries,
                project_metadata={
                    "total_files": project_index.total_files,
                    "supported_files": project_index.supported_files,
                    "parsing_errors": project_index.parsing_errors,
                    "total_symbols": len(project_index.symbols),
                },
                dependency_graph_hash=self._calculate_object_hash(
                    project_index.dependencies
                ),
                symbol_registry_hash=self._calculate_object_hash(project_index.symbols),
                created_at=time.time(),
                updated_at=time.time(),
            )

            # Save cache
            async with aiofiles.open(cache_file, "wb") as f:
                cache_data = pickle.dumps(cache)
                await f.write(cache_data)

            logger.debug(f"Saved cache with {len(file_entries)} file entries")

        except Exception as e:
            logger.error(f"Error saving cache: {e}")

    def _get_cache_file_path(self, workspace_path: str) -> Path:
        """Get cache file path for workspace"""
        workspace_hash = hashlib.sha256(workspace_path.encode()).hexdigest()[:16]
        return self.cache_dir / f"project_index_{workspace_hash}.cache"

    def _needs_full_reindex(self, cache: IncrementalIndexCache) -> bool:
        """Determine if full reindex is needed"""
        # Check cache age
        cache_age = time.time() - cache.last_full_index
        if cache_age > self.full_index_interval:
            logger.info(f"Cache too old ({cache_age/3600:.1f}h), needs full reindex")
            return True

        # Check if project structure has changed significantly
        try:
            current_files = set()
            workspace = Path(cache.project_path)

            for path in workspace.rglob("*"):
                if path.is_file() and path.suffix.lower() in {
                    ".py",
                    ".js",
                    ".ts",
                    ".jsx",
                    ".tsx",
                    ".swift",
                }:
                    current_files.add(str(path.absolute()))

            cached_files = set(cache.file_entries.keys())

            # Calculate file change ratio
            total_files = len(current_files | cached_files)
            if total_files == 0:
                return True

            changed_files = len(current_files.symmetric_difference(cached_files))
            change_ratio = changed_files / total_files

            if change_ratio > 0.3:  # More than 30% files changed
                logger.info(
                    f"Significant file changes ({change_ratio:.1%}), needs full reindex"
                )
                return True

        except Exception as e:
            logger.warning(f"Error checking project structure: {e}")
            return True

        return False

    async def _full_reindex(
        self,
        workspace_path: str,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
    ) -> ProjectIndex:
        """Perform full project reindex"""
        return await project_indexer.index_project(
            workspace_path, include_patterns, exclude_patterns
        )

    async def _incremental_update(
        self,
        workspace_path: str,
        cache: IncrementalIndexCache,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
    ) -> ProjectIndex:
        """Perform incremental project update"""
        try:
            # Discover current files
            current_files = await self._discover_current_files(
                workspace_path, include_patterns, exclude_patterns
            )

            # Determine files that need reanalysis
            files_to_analyze = []
            removed_files = set()

            # Check for new and modified files
            for file_path in current_files:
                if file_path not in cache.file_entries:
                    # New file
                    files_to_analyze.append(file_path)
                else:
                    # Check if file was modified
                    cache_entry = cache.file_entries[file_path]
                    current_hash = await self._calculate_file_hash(file_path)

                    if current_hash != cache_entry.content_hash:
                        files_to_analyze.append(file_path)

            # Check for removed files
            for file_path in cache.file_entries:
                if file_path not in current_files:
                    removed_files.add(file_path)

            logger.info(
                f"Incremental update: {len(files_to_analyze)} files to analyze, "
                f"{len(removed_files)} files removed"
            )

            # Convert cache to base project index
            project_index = await self._cache_to_project_index(cache)

            # Remove deleted files from index
            for file_path in removed_files:
                if file_path in project_index.files:
                    # Remove file analysis
                    analysis = project_index.files[file_path]
                    del project_index.files[file_path]

                    # Remove symbols
                    for symbol in analysis.symbols:
                        if symbol.id in project_index.symbols:
                            del project_index.symbols[symbol.id]

                    # Update counters
                    project_index.supported_files = max(
                        0, project_index.supported_files - 1
                    )
                    project_index.total_files = max(0, project_index.total_files - 1)

            # Analyze modified/new files
            if files_to_analyze:
                new_analyses = await self._analyze_files_batch(files_to_analyze)

                for file_path, analysis in new_analyses.items():
                    # Update project index
                    if file_path in project_index.files:
                        # Remove old symbols before adding new ones
                        old_analysis = project_index.files[file_path]
                        for symbol in old_analysis.symbols:
                            if symbol.id in project_index.symbols:
                                del project_index.symbols[symbol.id]
                    else:
                        # New file
                        project_index.total_files += 1
                        if not analysis.parsing_errors:
                            project_index.supported_files += 1
                        else:
                            project_index.parsing_errors += 1

                    # Add updated analysis
                    project_index.files[file_path] = analysis

                    # Add new symbols
                    for symbol in analysis.symbols:
                        project_index.symbols[symbol.id] = symbol

                    # Update dependencies
                    project_index.dependencies.extend(analysis.dependencies)

            # Update timestamp
            project_index.last_indexed = time.time()

            return project_index

        except Exception as e:
            logger.error(f"Error in incremental update: {e}")
            # Fallback to full reindex
            return await self._full_reindex(
                workspace_path, include_patterns, exclude_patterns
            )

    async def _apply_file_changes(
        self,
        cache: IncrementalIndexCache,
        updated_files: Set[str],
        removed_files: Set[str],
    ) -> IncrementalIndexCache:
        """Apply file changes to cache"""
        try:
            # Remove deleted files from cache
            for file_path in removed_files:
                if file_path in cache.file_entries:
                    del cache.file_entries[file_path]

            # Analyze updated files
            if updated_files:
                analyses = await self._analyze_files_batch(list(updated_files))

                for file_path, analysis in analyses.items():
                    # Update cache entry
                    cache.file_entries[file_path] = FileIndexEntry(
                        file_path=file_path,
                        content_hash=await self._calculate_file_hash(file_path),
                        last_modified=Path(file_path).stat().st_mtime,
                        file_size=Path(file_path).stat().st_size,
                        analysis_timestamp=time.time(),
                        symbols_count=len(analysis.symbols),
                        dependencies_count=len(analysis.dependencies),
                        language=analysis.language.value if analysis.language else None,
                        parsing_errors=(
                            len(analysis.parsing_errors)
                            if analysis.parsing_errors
                            else 0
                        ),
                    )

            # Update cache metadata
            cache.updated_at = time.time()

            return cache

        except Exception as e:
            logger.error(f"Error applying file changes to cache: {e}")
            return cache

    async def _cache_to_project_index(
        self, cache: IncrementalIndexCache
    ) -> ProjectIndex:
        """Convert cache to project index"""
        try:
            project_index = ProjectIndex(
                workspace_path=cache.project_path, last_indexed=cache.updated_at
            )

            # Set metadata
            project_index.total_files = cache.project_metadata.get("total_files", 0)
            project_index.supported_files = cache.project_metadata.get(
                "supported_files", 0
            )
            project_index.parsing_errors = cache.project_metadata.get(
                "parsing_errors", 0
            )

            # Reconstruct file analyses and symbols
            files_to_analyze = []
            for file_path, entry in cache.file_entries.items():
                if Path(file_path).exists():
                    files_to_analyze.append(file_path)

            if files_to_analyze:
                analyses = await self._analyze_files_batch(files_to_analyze)

                for file_path, analysis in analyses.items():
                    project_index.files[file_path] = analysis

                    for symbol in analysis.symbols:
                        project_index.symbols[symbol.id] = symbol

                    project_index.dependencies.extend(analysis.dependencies)

            return project_index

        except Exception as e:
            logger.error(f"Error converting cache to project index: {e}")
            return ProjectIndex(
                workspace_path=cache.project_path, last_indexed=time.time()
            )

    async def _discover_current_files(
        self,
        workspace_path: str,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
    ) -> Set[str]:
        """Discover current code files in workspace"""
        try:
            # Use the existing discovery logic from project_indexer
            code_files = await project_indexer._discover_code_files(
                workspace_path, include_patterns, exclude_patterns
            )
            return set(code_files)
        except Exception as e:
            logger.error(f"Error discovering current files: {e}")
            return set()

    async def _analyze_files_batch(
        self, file_paths: List[str]
    ) -> Dict[str, FileAnalysis]:
        """Analyze a batch of files"""
        try:
            # Use project indexer's batch analysis
            return await project_indexer._analyze_file_batch(file_paths)
        except Exception as e:
            logger.error(f"Error analyzing files batch: {e}")
            return {}

    async def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate hash of file content"""
        try:
            async with aiofiles.open(file_path, "rb") as f:
                content = await f.read()
                return hashlib.sha256(content).hexdigest()
        except Exception as e:
            logger.warning(f"Error calculating hash for {file_path}: {e}")
            return "error"

    def _calculate_object_hash(self, obj: Any) -> str:
        """Calculate hash of object for comparison"""
        try:
            # Convert to json string for consistent hashing
            obj_str = json.dumps(obj, default=str, sort_keys=True)
            return hashlib.sha256(obj_str.encode()).hexdigest()
        except Exception:
            return "error"

    def get_metrics(self) -> Dict[str, Any]:
        """Get indexer performance metrics"""
        return self.metrics.copy()

    async def clear_cache(self, workspace_path: Optional[str] = None):
        """Clear cache for specific workspace or all caches"""
        try:
            if workspace_path:
                cache_file = self._get_cache_file_path(workspace_path)
                if cache_file.exists():
                    cache_file.unlink()
                    logger.info(f"Cleared cache for {workspace_path}")
            else:
                # Clear all caches
                for cache_file in self.cache_dir.glob("project_index_*.cache"):
                    cache_file.unlink()
                logger.info("Cleared all project index caches")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")

    async def trigger_intelligent_warming(self):
        """Trigger intelligent cache warming for frequently accessed projects"""
        try:
            candidates = cache_warming_service.get_warming_candidates(limit=5)

            for candidate in candidates:
                project_path = candidate["project_path"]
                await cache_warming_service.queue_warming_task(project_path)

            logger.info(f"Triggered warming for {len(candidates)} projects")
            return len(candidates)

        except Exception as e:
            logger.error(f"Error triggering intelligent warming: {e}")
            return 0


# Global instance
incremental_indexer = IncrementalProjectIndexer()
