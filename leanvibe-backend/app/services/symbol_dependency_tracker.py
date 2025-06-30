"""
Real-time Symbol Dependency Tracking Service

Tracks symbol dependencies across the codebase in real-time, providing
impact analysis and change propagation for symbol modifications.
"""

import asyncio
import hashlib
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from ..models.ast_models import (
    Symbol,
    SymbolType,
)
from ..models.monitoring_models import ChangeType, FileChange

logger = logging.getLogger(__name__)


class DependencyType(str, Enum):
    """Types of symbol dependencies"""

    IMPORT = "import"
    INHERITANCE = "inheritance"
    FUNCTION_CALL = "function_call"
    METHOD_CALL = "method_call"
    VARIABLE_ACCESS = "variable_access"
    TYPE_REFERENCE = "type_reference"
    ANNOTATION = "annotation"
    INSTANTIATION = "instantiation"
    COMPOSITION = "composition"
    AGGREGATION = "aggregation"
    UNKNOWN = "unknown"


class ImpactLevel(str, Enum):
    """Impact levels for symbol changes"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SymbolNode:
    """Represents a symbol in the dependency graph"""

    symbol_id: str
    symbol_name: str
    symbol_type: SymbolType
    file_path: str
    line_number: int
    column_number: int
    scope: str
    namespace: Optional[str] = None
    signature: Optional[str] = None
    is_public: bool = True
    is_exported: bool = False
    last_modified: datetime = field(default_factory=datetime.now)
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)


@dataclass
class DependencyEdge:
    """Represents a dependency relationship between symbols"""

    source_symbol_id: str
    target_symbol_id: str
    dependency_type: DependencyType
    file_path: str
    line_number: int
    column_number: int
    strength: float = 1.0  # Dependency strength (0.0 - 1.0)
    is_direct: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)


@dataclass
class SymbolChange:
    """Represents a change to a symbol"""

    change_id: str
    symbol_id: str
    change_type: str  # 'added', 'modified', 'deleted', 'moved'
    old_data: Optional[Dict[str, Any]] = None
    new_data: Optional[Dict[str, Any]] = None
    file_path: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    impact_level: ImpactLevel = ImpactLevel.LOW
    affected_symbols: Set[str] = field(default_factory=set)


@dataclass
class ImpactAnalysis:
    """Result of impact analysis for symbol changes"""

    symbol_id: str
    change_type: str
    directly_affected: List[str]
    indirectly_affected: List[str]
    breaking_changes: List[str]
    impact_score: float
    analysis_depth: int
    suggestions: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class DependencyPath:
    """Represents a path between two symbols through dependencies"""

    source_symbol_id: str
    target_symbol_id: str
    path: List[str]
    path_types: List[DependencyType]
    total_strength: float
    path_length: int
    is_cyclic: bool = False


class SymbolDependencyTracker:
    """
    Real-time Symbol Dependency Tracking Service

    Tracks symbol dependencies, analyzes impact of changes,
    and provides real-time dependency monitoring.
    """

    def __init__(self):
        # Symbol and dependency storage
        self.symbols: Dict[str, SymbolNode] = {}
        self.dependencies: Dict[str, DependencyEdge] = {}
        self.file_symbols: Dict[str, Set[str]] = defaultdict(set)

        # Dependency graph structures
        self.dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        self.reverse_dependency_graph: Dict[str, Set[str]] = defaultdict(set)

        # Change tracking
        self.symbol_changes: List[SymbolChange] = []
        self.pending_analysis: deque[str] = deque()
        self.max_change_history = 1000

        # Real-time monitoring
        self.active_watchers: Dict[str, Set[str]] = defaultdict(
            set
        )  # file_path -> client_ids
        self.symbol_subscribers: Dict[str, Set[str]] = defaultdict(
            set
        )  # symbol_id -> client_ids

        # Configuration
        self.max_analysis_depth = 10
        self.impact_threshold = 0.1
        self.batch_processing_size = 50
        self.real_time_enabled = True

        # Performance metrics
        self.metrics = {
            "total_symbols": 0,
            "total_dependencies": 0,
            "dependency_updates": 0,
            "impact_analyses": 0,
            "average_analysis_time_ms": 0.0,
            "cyclic_dependencies_detected": 0,
            "real_time_updates_sent": 0,
        }

        # Background tasks
        self.analysis_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None

    async def initialize(self) -> bool:
        """Initialize the symbol dependency tracker"""
        try:
            logger.info("Initializing Symbol Dependency Tracker...")

            # Start background tasks
            self.analysis_task = asyncio.create_task(
                self._background_analysis_processor()
            )
            self.cleanup_task = asyncio.create_task(self._periodic_cleanup())

            logger.info("Symbol dependency tracker initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Error initializing symbol dependency tracker: {e}")
            return False

    async def shutdown(self):
        """Shutdown the symbol dependency tracker"""
        try:
            logger.info("Shutting down symbol dependency tracker...")

            # Cancel background tasks
            if self.analysis_task:
                self.analysis_task.cancel()
                try:
                    await self.analysis_task
                except asyncio.CancelledError:
                    pass

            if self.cleanup_task:
                self.cleanup_task.cancel()
                try:
                    await self.cleanup_task
                except asyncio.CancelledError:
                    pass

            logger.info("Symbol dependency tracker shutdown complete")

        except Exception as e:
            logger.error(f"Error during symbol dependency tracker shutdown: {e}")

    async def add_symbol(self, symbol: Symbol, file_path: str) -> bool:
        """Add or update a symbol in the dependency tracker"""
        try:
            symbol_id = self._generate_symbol_id(symbol, file_path)

            # Check if symbol already exists
            existing_symbol = self.symbols.get(symbol_id)
            change_type = "modified" if existing_symbol else "added"

            # Create symbol node
            symbol_node = SymbolNode(
                symbol_id=symbol_id,
                symbol_name=symbol.name,
                symbol_type=symbol.symbol_type,
                file_path=file_path,
                line_number=symbol.line_start,
                column_number=symbol.column_start,
                scope="global",  # Default scope since Symbol model doesn't have this field
                signature=getattr(symbol, "signature", None),
                is_public=getattr(symbol, "visibility", "public") == "public",
                is_exported=True,  # Default to exported for now
            )

            # Update symbol storage
            old_data = self.symbols.get(symbol_id)
            self.symbols[symbol_id] = symbol_node
            self.file_symbols[file_path].add(symbol_id)

            # Track change
            change = SymbolChange(
                change_id=self._generate_change_id(),
                symbol_id=symbol_id,
                change_type=change_type,
                old_data=old_data.__dict__ if old_data else None,
                new_data=symbol_node.__dict__,
                file_path=file_path,
            )

            await self._record_symbol_change(change)

            # Update metrics
            if change_type == "added":
                self.metrics["total_symbols"] += 1

            logger.debug(f"Added/updated symbol {symbol.name} in {file_path}")
            return True

        except Exception as e:
            logger.error(f"Error adding symbol {symbol.name}: {e}")
            return False

    async def add_dependency(
        self,
        source_symbol: Symbol,
        target_symbol: Symbol,
        dependency_type: DependencyType,
        file_path: str,
        line_number: int = 0,
        column_number: int = 0,
    ) -> bool:
        """Add a dependency relationship between symbols"""
        try:
            source_id = self._generate_symbol_id(source_symbol, file_path)
            target_id = self._generate_symbol_id(target_symbol, file_path)

            # Create dependency edge
            edge_id = f"{source_id}->{target_id}:{dependency_type}"
            dependency_edge = DependencyEdge(
                source_symbol_id=source_id,
                target_symbol_id=target_id,
                dependency_type=dependency_type,
                file_path=file_path,
                line_number=line_number,
                column_number=column_number,
                strength=self._calculate_dependency_strength(dependency_type),
            )

            # Update dependency storage
            self.dependencies[edge_id] = dependency_edge
            self.dependency_graph[source_id].add(target_id)
            self.reverse_dependency_graph[target_id].add(source_id)

            # Update symbol nodes
            if source_id in self.symbols:
                self.symbols[source_id].dependencies.add(target_id)
            if target_id in self.symbols:
                self.symbols[target_id].dependents.add(source_id)

            # Check for cyclic dependencies
            if self._creates_cycle(source_id, target_id):
                self.metrics["cyclic_dependencies_detected"] += 1
                logger.warning(
                    f"Cyclic dependency detected: {source_id} -> {target_id}"
                )

            self.metrics["total_dependencies"] += 1
            self.metrics["dependency_updates"] += 1

            logger.debug(
                f"Added dependency: {source_symbol.name} -> {target_symbol.name} ({dependency_type})"
            )
            return True

        except Exception as e:
            logger.error(f"Error adding dependency: {e}")
            return False

    async def remove_symbol(self, symbol_id: str) -> bool:
        """Remove a symbol and its dependencies"""
        try:
            if symbol_id not in self.symbols:
                return False

            symbol_node = self.symbols[symbol_id]

            # Remove from file mapping
            self.file_symbols[symbol_node.file_path].discard(symbol_id)

            # Remove all dependencies involving this symbol
            edges_to_remove = []
            for edge_id, edge in self.dependencies.items():
                if (
                    edge.source_symbol_id == symbol_id
                    or edge.target_symbol_id == symbol_id
                ):
                    edges_to_remove.append(edge_id)

            for edge_id in edges_to_remove:
                del self.dependencies[edge_id]

            # Remove from dependency graphs
            for target_id in self.dependency_graph[symbol_id]:
                self.reverse_dependency_graph[target_id].discard(symbol_id)
            del self.dependency_graph[symbol_id]

            for source_id in self.reverse_dependency_graph[symbol_id]:
                self.dependency_graph[source_id].discard(symbol_id)
            del self.reverse_dependency_graph[symbol_id]

            # Remove symbol
            del self.symbols[symbol_id]

            # Track change
            change = SymbolChange(
                change_id=self._generate_change_id(),
                symbol_id=symbol_id,
                change_type="deleted",
                old_data=symbol_node.__dict__,
                file_path=symbol_node.file_path,
            )

            await self._record_symbol_change(change)

            self.metrics["total_symbols"] -= 1

            logger.debug(f"Removed symbol {symbol_id}")
            return True

        except Exception as e:
            logger.error(f"Error removing symbol {symbol_id}: {e}")
            return False

    async def analyze_symbol_impact(
        self, symbol_id: str, change_type: str = "modified"
    ) -> ImpactAnalysis:
        """Analyze the impact of changes to a symbol"""
        try:
            start_time = time.time()

            if symbol_id not in self.symbols:
                return ImpactAnalysis(
                    symbol_id=symbol_id,
                    change_type=change_type,
                    directly_affected=[],
                    indirectly_affected=[],
                    breaking_changes=[],
                    impact_score=0.0,
                    analysis_depth=0,
                )

            symbol = self.symbols[symbol_id]
            directly_affected = []
            indirectly_affected = []
            breaking_changes = []

            # Analyze direct dependencies (symbols that depend on this one)
            direct_dependents = self.reverse_dependency_graph.get(symbol_id, set())
            directly_affected = list(direct_dependents)

            # Analyze indirect dependencies (breadth-first search)
            visited = set([symbol_id])
            queue = deque(direct_dependents)
            depth = 0

            while queue and depth < self.max_analysis_depth:
                level_size = len(queue)
                depth += 1

                for _ in range(level_size):
                    current_symbol = queue.popleft()
                    if current_symbol in visited:
                        continue

                    visited.add(current_symbol)
                    indirectly_affected.append(current_symbol)

                    # Add next level dependencies
                    next_dependents = self.reverse_dependency_graph.get(
                        current_symbol, set()
                    )
                    for dependent in next_dependents:
                        if dependent not in visited:
                            queue.append(dependent)

            # Analyze breaking changes
            if change_type in ["deleted", "signature_changed"]:
                breaking_changes = directly_affected.copy()
            elif change_type == "moved":
                # Import dependencies might break
                breaking_changes = [
                    dep
                    for dep in directly_affected
                    if self._is_import_dependency(dep, symbol_id)
                ]

            # Calculate impact score
            impact_score = self._calculate_impact_score(
                len(directly_affected),
                len(indirectly_affected),
                len(breaking_changes),
                symbol.symbol_type,
                symbol.is_public,
            )

            # Generate suggestions
            suggestions = self._generate_impact_suggestions(
                symbol, change_type, directly_affected, breaking_changes
            )

            analysis = ImpactAnalysis(
                symbol_id=symbol_id,
                change_type=change_type,
                directly_affected=directly_affected,
                indirectly_affected=indirectly_affected,
                breaking_changes=breaking_changes,
                impact_score=impact_score,
                analysis_depth=depth,
                suggestions=suggestions,
            )

            # Update metrics
            analysis_time = (time.time() - start_time) * 1000
            self._update_analysis_metrics(analysis_time)

            logger.debug(
                f"Impact analysis for {symbol_id}: {len(directly_affected)} direct, "
                f"{len(indirectly_affected)} indirect dependencies"
            )

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing symbol impact for {symbol_id}: {e}")
            return ImpactAnalysis(
                symbol_id=symbol_id,
                change_type=change_type,
                directly_affected=[],
                indirectly_affected=[],
                breaking_changes=[],
                impact_score=0.0,
                analysis_depth=0,
            )

    async def find_dependency_path(
        self, source_symbol_id: str, target_symbol_id: str
    ) -> Optional[DependencyPath]:
        """Find dependency path between two symbols"""
        try:
            if (
                source_symbol_id not in self.symbols
                or target_symbol_id not in self.symbols
            ):
                return None

            # Use breadth-first search to find shortest path
            queue = deque([(source_symbol_id, [source_symbol_id], [])])
            visited = set([source_symbol_id])

            while queue:
                current_symbol, path, path_types = queue.popleft()

                if current_symbol == target_symbol_id:
                    # Found path
                    total_strength = self._calculate_path_strength(path, path_types)
                    is_cyclic = self._path_is_cyclic(path)

                    return DependencyPath(
                        source_symbol_id=source_symbol_id,
                        target_symbol_id=target_symbol_id,
                        path=path,
                        path_types=path_types,
                        total_strength=total_strength,
                        path_length=len(path) - 1,
                        is_cyclic=is_cyclic,
                    )

                # Explore dependencies
                for dependency_id in self.dependency_graph.get(current_symbol, set()):
                    if (
                        dependency_id not in visited
                        and len(path) < self.max_analysis_depth
                    ):
                        visited.add(dependency_id)

                        # Find dependency type
                        dep_type = self._get_dependency_type(
                            current_symbol, dependency_id
                        )

                        queue.append(
                            (
                                dependency_id,
                                path + [dependency_id],
                                path_types + [dep_type],
                            )
                        )

            return None

        except Exception as e:
            logger.error(f"Error finding dependency path: {e}")
            return None

    async def get_symbol_dependencies(
        self, symbol_id: str, depth: int = 1
    ) -> Dict[str, Any]:
        """Get dependencies for a symbol up to specified depth"""
        try:
            if symbol_id not in self.symbols:
                return {}

            result = {
                "symbol": self.symbols[symbol_id].__dict__,
                "direct_dependencies": [],
                "direct_dependents": [],
                "dependency_tree": {},
            }

            # Get direct dependencies (symbols this one depends on)
            direct_deps = self.dependency_graph.get(symbol_id, set())
            result["direct_dependencies"] = [
                {
                    "symbol_id": dep_id,
                    "symbol": (
                        self.symbols[dep_id].__dict__
                        if dep_id in self.symbols
                        else None
                    ),
                    "dependency_type": self._get_dependency_type(symbol_id, dep_id),
                }
                for dep_id in direct_deps
            ]

            # Get direct dependents (symbols that depend on this one)
            direct_dependents = self.reverse_dependency_graph.get(symbol_id, set())
            result["direct_dependents"] = [
                {
                    "symbol_id": dep_id,
                    "symbol": (
                        self.symbols[dep_id].__dict__
                        if dep_id in self.symbols
                        else None
                    ),
                    "dependency_type": self._get_dependency_type(dep_id, symbol_id),
                }
                for dep_id in direct_dependents
            ]

            # Build dependency tree if depth > 1
            if depth > 1:
                result["dependency_tree"] = await self._build_dependency_tree(
                    symbol_id, depth - 1, set([symbol_id])
                )

            return result

        except Exception as e:
            logger.error(f"Error getting symbol dependencies for {symbol_id}: {e}")
            return {}

    async def process_file_changes(
        self, file_changes: List[FileChange]
    ) -> List[ImpactAnalysis]:
        """Process file changes and analyze symbol impact"""
        try:
            analyses = []

            for file_change in file_changes:
                if not file_change.is_code_file():
                    continue

                file_path = file_change.file_path

                if file_change.change_type == ChangeType.DELETED:
                    # Analyze impact of all symbols in deleted file
                    symbols_in_file = self.file_symbols.get(file_path, set()).copy()
                    for symbol_id in symbols_in_file:
                        analysis = await self.analyze_symbol_impact(
                            symbol_id, "deleted"
                        )
                        analyses.append(analysis)
                        await self.remove_symbol(symbol_id)

                elif file_change.change_type in [
                    ChangeType.MODIFIED,
                    ChangeType.CREATED,
                ]:
                    # Re-analyze symbols in modified/created file
                    # This would typically be called after re-parsing the file
                    symbols_in_file = self.file_symbols.get(file_path, set())
                    for symbol_id in symbols_in_file:
                        analysis = await self.analyze_symbol_impact(
                            symbol_id, "modified"
                        )
                        if analysis.impact_score > self.impact_threshold:
                            analyses.append(analysis)

            return analyses

        except Exception as e:
            logger.error(f"Error processing file changes: {e}")
            return []

    def subscribe_to_symbol(self, symbol_id: str, client_id: str):
        """Subscribe to changes for a specific symbol"""
        self.symbol_subscribers[symbol_id].add(client_id)
        logger.debug(f"Client {client_id} subscribed to symbol {symbol_id}")

    def unsubscribe_from_symbol(self, symbol_id: str, client_id: str):
        """Unsubscribe from changes for a specific symbol"""
        self.symbol_subscribers[symbol_id].discard(client_id)
        if not self.symbol_subscribers[symbol_id]:
            del self.symbol_subscribers[symbol_id]
        logger.debug(f"Client {client_id} unsubscribed from symbol {symbol_id}")

    def get_metrics(self) -> Dict[str, Any]:
        """Get dependency tracking metrics"""
        return {
            **self.metrics,
            "active_watchers": len(self.active_watchers),
            "symbol_subscribers": len(self.symbol_subscribers),
            "pending_analysis": len(self.pending_analysis),
            "recent_changes": len(self.symbol_changes),
        }

    def _generate_symbol_id(self, symbol: Symbol, file_path: str) -> str:
        """Generate unique ID for a symbol"""
        path_hash = hashlib.md5(file_path.encode()).hexdigest()[:8]
        symbol_info = f"{symbol.name}:{symbol.symbol_type}:{symbol.line_start}"
        return f"{path_hash}:{symbol_info}"

    def _generate_change_id(self) -> str:
        """Generate unique ID for a change"""
        timestamp = int(time.time() * 1000)
        return (
            f"change_{timestamp}_{hashlib.md5(str(timestamp).encode()).hexdigest()[:8]}"
        )

    def _calculate_dependency_strength(self, dependency_type: DependencyType) -> float:
        """Calculate strength of dependency based on type"""
        strength_map = {
            DependencyType.INHERITANCE: 1.0,
            DependencyType.COMPOSITION: 0.9,
            DependencyType.IMPORT: 0.8,
            DependencyType.TYPE_REFERENCE: 0.7,
            DependencyType.METHOD_CALL: 0.6,
            DependencyType.FUNCTION_CALL: 0.5,
            DependencyType.VARIABLE_ACCESS: 0.4,
            DependencyType.ANNOTATION: 0.3,
            DependencyType.INSTANTIATION: 0.8,
            DependencyType.AGGREGATION: 0.7,
        }
        return strength_map.get(dependency_type, 0.5)

    def _creates_cycle(self, source_id: str, target_id: str) -> bool:
        """Check if adding dependency creates a cycle"""
        # Simple cycle detection: check if target can reach source
        visited = set()
        queue = deque([target_id])

        while queue:
            current = queue.popleft()
            if current == source_id:
                return True

            if current in visited:
                continue
            visited.add(current)

            # Add dependencies of current symbol
            for dep_id in self.dependency_graph.get(current, set()):
                if dep_id not in visited:
                    queue.append(dep_id)

        return False

    def _calculate_impact_score(
        self,
        direct_count: int,
        indirect_count: int,
        breaking_count: int,
        symbol_type: SymbolType,
        is_public: bool,
    ) -> float:
        """Calculate impact score for symbol changes"""
        base_score = direct_count * 0.5 + indirect_count * 0.1 + breaking_count * 1.0

        # Type multipliers
        type_multipliers = {
            SymbolType.CLASS: 1.5,
            SymbolType.FUNCTION: 1.2,
            SymbolType.METHOD: 1.0,
            SymbolType.VARIABLE: 0.8,
            SymbolType.CONSTANT: 0.6,
            SymbolType.MODULE: 1.4,
            SymbolType.IMPORT: 0.7,
            SymbolType.PROPERTY: 0.9,
            SymbolType.PARAMETER: 0.5,
        }

        multiplier = type_multipliers.get(symbol_type, 1.0)
        if is_public:
            multiplier *= 1.3

        return min(base_score * multiplier, 10.0)  # Cap at 10.0

    def _generate_impact_suggestions(
        self,
        symbol: SymbolNode,
        change_type: str,
        affected_symbols: List[str],
        breaking_changes: List[str],
    ) -> List[str]:
        """Generate suggestions for handling symbol impact"""
        suggestions = []

        if breaking_changes:
            suggestions.append(
                f"Consider gradual migration for {len(breaking_changes)} breaking changes"
            )
            suggestions.append("Add deprecation warnings before removing symbols")

        if len(affected_symbols) > 10:
            suggestions.append(
                "Consider batch refactoring tools for large-scale changes"
            )

        if symbol.symbol_type == SymbolType.CLASS and change_type == "modified":
            suggestions.append("Review inheritance hierarchy for consistency")

        if symbol.is_public and symbol.is_exported:
            suggestions.append("Update API documentation and version changelog")

        return suggestions

    async def _record_symbol_change(self, change: SymbolChange):
        """Record a symbol change for analysis"""
        self.symbol_changes.append(change)

        # Trim history if too long
        if len(self.symbol_changes) > self.max_change_history:
            self.symbol_changes = self.symbol_changes[-self.max_change_history :]

        # Queue for background analysis
        if self.real_time_enabled:
            self.pending_analysis.append(change.symbol_id)

    async def _background_analysis_processor(self):
        """Background task to process pending analysis"""
        try:
            while True:
                if self.pending_analysis:
                    # Process batch of symbols
                    batch = []
                    for _ in range(
                        min(self.batch_processing_size, len(self.pending_analysis))
                    ):
                        if self.pending_analysis:
                            batch.append(self.pending_analysis.popleft())

                    # Analyze each symbol in batch
                    for symbol_id in batch:
                        if symbol_id in self.symbols:
                            analysis = await self.analyze_symbol_impact(symbol_id)

                            # Notify subscribers if significant impact
                            if analysis.impact_score > self.impact_threshold:
                                await self._notify_symbol_subscribers(
                                    symbol_id, analysis
                                )

                # Wait before next batch
                await asyncio.sleep(1.0)

        except asyncio.CancelledError:
            logger.info("Background analysis processor cancelled")
        except Exception as e:
            logger.error(f"Error in background analysis processor: {e}")

    async def _periodic_cleanup(self):
        """Periodic cleanup of old data"""
        try:
            while True:
                await asyncio.sleep(3600)  # Run every hour

                # Clean up old changes
                cutoff_time = datetime.now() - timedelta(days=7)
                self.symbol_changes = [
                    change
                    for change in self.symbol_changes
                    if change.timestamp > cutoff_time
                ]

                logger.debug("Completed periodic cleanup of symbol dependency tracker")

        except asyncio.CancelledError:
            logger.info("Periodic cleanup cancelled")
        except Exception as e:
            logger.error(f"Error in periodic cleanup: {e}")

    async def _notify_symbol_subscribers(
        self, symbol_id: str, analysis: ImpactAnalysis
    ):
        """Notify subscribers about symbol changes"""
        try:
            subscribers = self.symbol_subscribers.get(symbol_id, set())
            if subscribers:
                # Here you would send real-time notifications to subscribers
                # This would typically use WebSocket connections
                self.metrics["real_time_updates_sent"] += len(subscribers)
                logger.debug(
                    f"Notified {len(subscribers)} subscribers about changes to {symbol_id}"
                )

        except Exception as e:
            logger.error(f"Error notifying symbol subscribers: {e}")

    def _is_import_dependency(self, dependent_id: str, symbol_id: str) -> bool:
        """Check if dependency is an import relationship"""
        edge_id = f"{dependent_id}->{symbol_id}:{DependencyType.IMPORT}"
        return edge_id in self.dependencies

    def _get_dependency_type(
        self, source_id: str, target_id: str
    ) -> Optional[DependencyType]:
        """Get dependency type between two symbols"""
        for edge_id, edge in self.dependencies.items():
            if (
                edge.source_symbol_id == source_id
                and edge.target_symbol_id == target_id
            ):
                return edge.dependency_type
        return None

    def _calculate_path_strength(
        self, path: List[str], path_types: List[DependencyType]
    ) -> float:
        """Calculate total strength of dependency path"""
        if not path_types:
            return 0.0

        total_strength = 1.0
        for dep_type in path_types:
            total_strength *= self._calculate_dependency_strength(dep_type)

        return total_strength

    def _path_is_cyclic(self, path: List[str]) -> bool:
        """Check if path contains cycles"""
        return len(path) != len(set(path))

    async def _build_dependency_tree(
        self, symbol_id: str, remaining_depth: int, visited: Set[str]
    ) -> Dict[str, Any]:
        """Build dependency tree recursively"""
        if remaining_depth <= 0 or symbol_id in visited:
            return {}

        visited.add(symbol_id)
        tree = {}

        dependencies = self.dependency_graph.get(symbol_id, set())
        for dep_id in dependencies:
            if dep_id not in visited:
                subtree = await self._build_dependency_tree(
                    dep_id, remaining_depth - 1, visited.copy()
                )
                tree[dep_id] = {
                    "symbol": (
                        self.symbols[dep_id].__dict__
                        if dep_id in self.symbols
                        else None
                    ),
                    "dependency_type": self._get_dependency_type(symbol_id, dep_id),
                    "dependencies": subtree,
                }

        return tree

    def _update_analysis_metrics(self, analysis_time_ms: float):
        """Update analysis performance metrics"""
        self.metrics["impact_analyses"] += 1

        if self.metrics["average_analysis_time_ms"] == 0:
            self.metrics["average_analysis_time_ms"] = analysis_time_ms
        else:
            current_avg = self.metrics["average_analysis_time_ms"]
            new_avg = (current_avg + analysis_time_ms) / 2
            self.metrics["average_analysis_time_ms"] = new_avg


# Global instance
symbol_dependency_tracker = SymbolDependencyTracker()
