"""
Cache Invalidation Service

Provides intelligent cache invalidation based on dependency relationships,
ensuring cache coherency when files and their dependencies change.
"""

import asyncio
import logging
import time
from typing import Dict, List, Set, Optional, Tuple, Any
from pathlib import Path
from dataclasses import dataclass
from collections import defaultdict, deque
from datetime import datetime, timedelta

from ..models.ast_models import (
    ProjectIndex, FileAnalysis, Symbol, Dependency, 
    LanguageType
)
from ..models.monitoring_models import FileChange, ChangeType

logger = logging.getLogger(__name__)


@dataclass
class InvalidationEvent:
    """Represents a cache invalidation event"""
    file_path: str
    invalidation_type: str  # 'direct', 'dependency', 'cascade'
    triggered_by: str  # The original file that caused the invalidation
    timestamp: datetime
    propagation_depth: int = 0
    affected_symbols: List[str] = None
    
    def __post_init__(self):
        if self.affected_symbols is None:
            self.affected_symbols = []


@dataclass
class DependencyNode:
    """Represents a node in the dependency graph"""
    file_path: str
    dependencies: Set[str]  # Files this node depends on
    dependents: Set[str]    # Files that depend on this node
    last_modified: float
    symbols: Set[str]       # Symbols defined in this file
    external_imports: Set[str]  # External module imports
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = set()
        if self.dependents is None:
            self.dependents = set()
        if self.symbols is None:
            self.symbols = set()
        if self.external_imports is None:
            self.external_imports = set()


class CacheInvalidationService:
    """
    Cache Invalidation Service
    
    Provides intelligent cache invalidation based on dependency relationships,
    symbol usage, and file modification patterns.
    """
    
    def __init__(self):
        # Dependency graph: file_path -> DependencyNode
        self.dependency_graph: Dict[str, DependencyNode] = {}
        
        # Symbol to files mapping for quick lookup
        self.symbol_to_files: Dict[str, Set[str]] = defaultdict(set)
        
        # External import to files mapping
        self.import_to_files: Dict[str, Set[str]] = defaultdict(set)
        
        # Cache handlers for actual cache invalidation
        self._cache_handlers: List[Any] = []
        
        # Invalidation tracking
        self.invalidation_events: List[InvalidationEvent] = []
        self.max_events_history = 1000
        
        # Configuration
        self.max_propagation_depth = 10
        self.cascade_threshold = 5  # Max files to cascade before stopping
        self.symbol_invalidation_enabled = True
        self.external_dependency_tracking = True
        
        # Performance metrics
        self.metrics = {
            "total_invalidations": 0,
            "cascade_invalidations": 0,
            "symbol_based_invalidations": 0,
            "external_dependency_invalidations": 0,
            "average_propagation_depth": 0.0,
            "cache_coherency_events": 0
        }
    
    def register_cache_handler(self, handler: Any):
        """Register a cache handler for invalidation"""
        if handler not in self._cache_handlers:
            self._cache_handlers.append(handler)
            logger.debug(f"Registered cache handler: {type(handler).__name__}")
    
    def unregister_cache_handler(self, handler: Any):
        """Unregister a cache handler"""
        if handler in self._cache_handlers:
            self._cache_handlers.remove(handler)
            logger.debug(f"Unregistered cache handler: {type(handler).__name__}")
    
    async def build_dependency_graph(self, project_index: ProjectIndex):
        """Build the dependency graph from project index"""
        try:
            start_time = time.time()
            logger.info("Building dependency graph for cache invalidation")
            
            # Clear existing graph
            self.dependency_graph.clear()
            self.symbol_to_files.clear()
            self.import_to_files.clear()
            
            # Build nodes from project files
            for file_path, analysis in project_index.files.items():
                await self._create_dependency_node(file_path, analysis)
            
            # Build dependency relationships
            for file_path, analysis in project_index.files.items():
                await self._build_file_dependencies(file_path, analysis)
            
            # Build reverse dependencies (dependents)
            self._build_reverse_dependencies()
            
            build_time = time.time() - start_time
            logger.info(f"Dependency graph built: {len(self.dependency_graph)} nodes, "
                       f"{sum(len(node.dependencies) for node in self.dependency_graph.values())} edges, "
                       f"in {build_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Error building dependency graph: {e}")
    
    async def _create_dependency_node(self, file_path: str, analysis: FileAnalysis):
        """Create a dependency node for a file"""
        try:
            file_stat = Path(file_path).stat()
            
            # Extract symbols
            symbols = set()
            for symbol in analysis.symbols:
                symbols.add(symbol.name)
                # Map symbol to file
                self.symbol_to_files[symbol.name].add(file_path)
            
            # Extract external imports
            external_imports = set()
            for dependency in analysis.dependencies:
                if dependency.is_external and dependency.module_name:
                    external_imports.add(dependency.module_name)
                    # Map import to file
                    self.import_to_files[dependency.module_name].add(file_path)
            
            # Create node
            node = DependencyNode(
                file_path=file_path,
                dependencies=set(),
                dependents=set(),
                last_modified=file_stat.st_mtime,
                symbols=symbols,
                external_imports=external_imports
            )
            
            self.dependency_graph[file_path] = node
            
        except Exception as e:
            logger.debug(f"Error creating dependency node for {file_path}: {e}")
    
    async def _build_file_dependencies(self, file_path: str, analysis: FileAnalysis):
        """Build dependencies for a specific file"""
        try:
            node = self.dependency_graph.get(file_path)
            if not node:
                return
            
            for dependency in analysis.dependencies:
                if not dependency.is_external and dependency.target_file:
                    # Internal dependency
                    dep_path = str(Path(dependency.target_file).absolute())
                    if dep_path in self.dependency_graph:
                        node.dependencies.add(dep_path)
                    
        except Exception as e:
            logger.debug(f"Error building dependencies for {file_path}: {e}")
    
    def _build_reverse_dependencies(self):
        """Build reverse dependency relationships (who depends on whom)"""
        try:
            for file_path, node in self.dependency_graph.items():
                for dep_path in node.dependencies:
                    if dep_path in self.dependency_graph:
                        self.dependency_graph[dep_path].dependents.add(file_path)
                        
        except Exception as e:
            logger.error(f"Error building reverse dependencies: {e}")
    
    async def invalidate_file_cache(
        self, 
        file_path: str, 
        change_type: ChangeType,
        propagate: bool = True
    ) -> List[InvalidationEvent]:
        """Invalidate cache for a file and its dependencies"""
        try:
            start_time = time.time()
            file_path = str(Path(file_path).absolute())
            
            logger.debug(f"Starting cache invalidation for {file_path}")
            
            invalidation_events = []
            
            # Direct invalidation
            direct_event = InvalidationEvent(
                file_path=file_path,
                invalidation_type='direct',
                triggered_by=file_path,
                timestamp=datetime.now(),
                propagation_depth=0
            )
            
            invalidation_events.append(direct_event)
            await self._execute_invalidation(direct_event)
            
            if propagate and file_path in self.dependency_graph:
                # Propagate invalidation to dependents
                cascade_events = await self._propagate_invalidation(
                    file_path, change_type, triggered_by=file_path
                )
                invalidation_events.extend(cascade_events)
                
                # Symbol-based invalidation if enabled
                if self.symbol_invalidation_enabled:
                    symbol_events = await self._invalidate_by_symbols(
                        file_path, change_type, triggered_by=file_path
                    )
                    invalidation_events.extend(symbol_events)
            
            # Update metrics
            self._update_metrics(invalidation_events)
            
            # Store events in history
            self.invalidation_events.extend(invalidation_events)
            if len(self.invalidation_events) > self.max_events_history:
                self.invalidation_events = self.invalidation_events[-self.max_events_history:]
            
            invalidation_time = time.time() - start_time
            logger.debug(f"Cache invalidation completed: {len(invalidation_events)} files, "
                        f"{invalidation_time:.3f}s")
            
            return invalidation_events
            
        except Exception as e:
            logger.error(f"Error invalidating cache for {file_path}: {e}")
            return []
    
    async def _propagate_invalidation(
        self, 
        file_path: str, 
        change_type: ChangeType,
        triggered_by: str,
        current_depth: int = 0
    ) -> List[InvalidationEvent]:
        """Propagate invalidation through dependency graph"""
        try:
            if current_depth >= self.max_propagation_depth:
                logger.debug(f"Max propagation depth reached for {file_path}")
                return []
            
            node = self.dependency_graph.get(file_path)
            if not node:
                return []
            
            events = []
            processed = set()
            
            # BFS propagation to dependents
            queue = deque([(dep_file, current_depth + 1) for dep_file in node.dependents])
            
            while queue:
                dependent_file, depth = queue.popleft()
                
                if dependent_file in processed or depth > self.max_propagation_depth:
                    continue
                
                processed.add(dependent_file)
                
                # Create invalidation event
                event = InvalidationEvent(
                    file_path=dependent_file,
                    invalidation_type='dependency',
                    triggered_by=triggered_by,
                    timestamp=datetime.now(),
                    propagation_depth=depth
                )
                
                events.append(event)
                await self._execute_invalidation(event)
                
                # Continue propagation for cascading changes
                if len(events) < self.cascade_threshold:
                    dependent_node = self.dependency_graph.get(dependent_file)
                    if dependent_node:
                        for next_dependent in dependent_node.dependents:
                            if next_dependent not in processed:
                                queue.append((next_dependent, depth + 1))
            
            return events
            
        except Exception as e:
            logger.error(f"Error propagating invalidation from {file_path}: {e}")
            return []
    
    async def _invalidate_by_symbols(
        self, 
        file_path: str, 
        change_type: ChangeType,
        triggered_by: str
    ) -> List[InvalidationEvent]:
        """Invalidate caches based on symbol usage"""
        try:
            if change_type == ChangeType.DELETED:
                return []  # No symbols to check for deleted files
            
            node = self.dependency_graph.get(file_path)
            if not node:
                return []
            
            events = []
            
            # Find files that might use symbols from this file
            for symbol in node.symbols:
                for using_file in self.symbol_to_files.get(symbol, set()):
                    if using_file != file_path and using_file not in [e.file_path for e in events]:
                        event = InvalidationEvent(
                            file_path=using_file,
                            invalidation_type='symbol',
                            triggered_by=triggered_by,
                            timestamp=datetime.now(),
                            affected_symbols=[symbol]
                        )
                        
                        events.append(event)
                        await self._execute_invalidation(event)
            
            return events
            
        except Exception as e:
            logger.error(f"Error invalidating by symbols for {file_path}: {e}")
            return []
    
    async def _execute_invalidation(self, event: InvalidationEvent):
        """Execute the actual cache invalidation"""
        try:
            # Clear from any registered cache handlers
            if hasattr(self, '_cache_handlers'):
                for handler in self._cache_handlers:
                    try:
                        if hasattr(handler, 'clear_cache'):
                            await handler.clear_cache(event.file_path)
                    except Exception as e:
                        logger.warning(f"Cache handler failed for {event.file_path}: {e}")
            
            # Update metrics
            self.metrics["total_invalidations"] += 1
            if event.invalidation_type == 'dependency':
                self.metrics["cascade_invalidations"] += 1
            elif event.invalidation_type == 'symbol':
                self.metrics["symbol_based_invalidations"] += 1
            
            logger.debug(f"Executed {event.invalidation_type} invalidation for {event.file_path}")
            
        except Exception as e:
            logger.error(f"Error executing invalidation for {event.file_path}: {e}")
    
    async def invalidate_multiple_files(
        self, 
        file_changes: List[FileChange]
    ) -> List[InvalidationEvent]:
        """Invalidate cache for multiple files efficiently"""
        try:
            all_events = []
            processed_files = set()
            
            # Group changes by type for optimized processing
            changes_by_type = defaultdict(list)
            for change in file_changes:
                changes_by_type[change.change_type].append(change.file_path)
            
            # Process deletions first (no propagation needed)
            for file_path in changes_by_type.get(ChangeType.DELETED, []):
                if file_path not in processed_files:
                    events = await self.invalidate_file_cache(file_path, ChangeType.DELETED, propagate=False)
                    all_events.extend(events)
                    processed_files.add(file_path)
            
            # Process modifications and creations with propagation
            for change_type in [ChangeType.MODIFIED, ChangeType.CREATED, ChangeType.MOVED]:
                for file_path in changes_by_type.get(change_type, []):
                    if file_path not in processed_files:
                        events = await self.invalidate_file_cache(file_path, change_type, propagate=True)
                        all_events.extend(events)
                        processed_files.add(file_path)
                        
                        # Add all affected files to processed to avoid duplicate invalidation
                        processed_files.update(event.file_path for event in events)
            
            logger.info(f"Batch invalidation: {len(file_changes)} changes -> {len(all_events)} invalidations")
            return all_events
            
        except Exception as e:
            logger.error(f"Error invalidating multiple files: {e}")
            return []
    
    def _update_metrics(self, events: List[InvalidationEvent]):
        """Update performance metrics"""
        try:
            if not events:
                return
            
            # Update average propagation depth
            depths = [e.propagation_depth for e in events if e.propagation_depth > 0]
            if depths:
                current_avg = self.metrics["average_propagation_depth"]
                new_avg = sum(depths) / len(depths)
                self.metrics["average_propagation_depth"] = (current_avg + new_avg) / 2
            
            # Count event types
            for event in events:
                if event.invalidation_type == 'dependency':
                    self.metrics["cascade_invalidations"] += 1
                elif event.invalidation_type == 'symbol':
                    self.metrics["symbol_based_invalidations"] += 1
            
        except Exception as e:
            logger.debug(f"Error updating metrics: {e}")
    
    def get_dependency_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get dependency information for a file"""
        try:
            file_path = str(Path(file_path).absolute())
            node = self.dependency_graph.get(file_path)
            
            if not node:
                return None
            
            return {
                "file_path": file_path,
                "dependencies": list(node.dependencies),
                "dependents": list(node.dependents),
                "symbols": list(node.symbols),
                "external_imports": list(node.external_imports),
                "last_modified": node.last_modified,
                "dependency_count": len(node.dependencies),
                "dependent_count": len(node.dependents)
            }
            
        except Exception as e:
            logger.error(f"Error getting dependency info for {file_path}: {e}")
            return None
    
    def get_invalidation_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent invalidation events"""
        try:
            recent_events = self.invalidation_events[-limit:]
            
            return [
                {
                    "file_path": event.file_path,
                    "invalidation_type": event.invalidation_type,
                    "triggered_by": event.triggered_by,
                    "timestamp": event.timestamp.isoformat(),
                    "propagation_depth": event.propagation_depth,
                    "affected_symbols": event.affected_symbols
                }
                for event in recent_events
            ]
            
        except Exception as e:
            logger.error(f"Error getting invalidation history: {e}")
            return []
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get cache invalidation metrics"""
        return {
            **self.metrics,
            "dependency_graph_size": len(self.dependency_graph),
            "symbol_mappings": len(self.symbol_to_files),
            "import_mappings": len(self.import_to_files),
            "recent_events": len(self.invalidation_events),
            "max_propagation_depth": self.max_propagation_depth,
            "cascade_threshold": self.cascade_threshold
        }
    
    async def optimize_graph(self):
        """Optimize the dependency graph by removing stale entries"""
        try:
            start_time = time.time()
            removed_count = 0
            
            # Remove nodes for files that no longer exist
            stale_files = []
            for file_path in self.dependency_graph:
                if not Path(file_path).exists():
                    stale_files.append(file_path)
            
            for file_path in stale_files:
                await self._remove_node(file_path)
                removed_count += 1
            
            # Rebuild reverse dependencies to ensure consistency
            if removed_count > 0:
                self._build_reverse_dependencies()
            
            optimization_time = time.time() - start_time
            if removed_count > 0:
                logger.info(f"Dependency graph optimized: removed {removed_count} stale nodes "
                           f"in {optimization_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Error optimizing dependency graph: {e}")
    
    async def _remove_node(self, file_path: str):
        """Remove a node from the dependency graph"""
        try:
            node = self.dependency_graph.get(file_path)
            if not node:
                return
            
            # Remove from symbol mappings
            for symbol in node.symbols:
                self.symbol_to_files[symbol].discard(file_path)
                if not self.symbol_to_files[symbol]:
                    del self.symbol_to_files[symbol]
            
            # Remove from import mappings
            for import_name in node.external_imports:
                self.import_to_files[import_name].discard(file_path)
                if not self.import_to_files[import_name]:
                    del self.import_to_files[import_name]
            
            # Remove dependencies pointing to this node
            for dep_file in node.dependencies:
                if dep_file in self.dependency_graph:
                    self.dependency_graph[dep_file].dependents.discard(file_path)
            
            # Remove dependents pointing from this node
            for dep_file in node.dependents:
                if dep_file in self.dependency_graph:
                    self.dependency_graph[dep_file].dependencies.discard(file_path)
            
            # Remove the node itself
            del self.dependency_graph[file_path]
            
        except Exception as e:
            logger.error(f"Error removing node {file_path}: {e}")


# Global instance
cache_invalidation_service = CacheInvalidationService()