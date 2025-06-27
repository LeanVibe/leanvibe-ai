"""
Incremental Graph Update Service

Provides real-time graph database updates with relationship propagation,
maintaining graph consistency without full rebuilds.
"""

import asyncio
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from neo4j.exceptions import Neo4jError

from ..models.ast_models import (
    Dependency,
    FileAnalysis,
    ProjectIndex,
    Reference,
    Symbol,
    SymbolType,
)
from ..models.monitoring_models import ChangeType, FileChange
from .graph_service import graph_service

logger = logging.getLogger(__name__)


class GraphUpdateType(str, Enum):
    """Types of graph updates"""

    NODE_ADDED = "node_added"
    NODE_UPDATED = "node_updated"
    NODE_DELETED = "node_deleted"
    RELATIONSHIP_ADDED = "relationship_added"
    RELATIONSHIP_UPDATED = "relationship_updated"
    RELATIONSHIP_DELETED = "relationship_deleted"


@dataclass
class GraphChange:
    """Represents a change to the graph"""

    change_id: str
    update_type: GraphUpdateType
    entity_type: str  # 'file', 'symbol', 'dependency'
    entity_id: str
    old_data: Optional[Dict[str, Any]] = None
    new_data: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)
    related_changes: List[str] = field(default_factory=list)


@dataclass
class GraphUpdateBatch:
    """Batch of graph updates to apply together"""

    batch_id: str
    changes: List[GraphChange]
    project_id: str
    created_at: datetime = field(default_factory=datetime.now)
    applied_at: Optional[datetime] = None
    success: bool = False
    error_message: Optional[str] = None
    rollback_data: Optional[Dict[str, Any]] = None


@dataclass
class PropagationResult:
    """Result of relationship propagation"""

    nodes_affected: int
    relationships_updated: int
    propagation_depth: int
    execution_time_ms: float
    warnings: List[str] = field(default_factory=list)


class IncrementalGraphUpdateService:
    """
    Incremental Graph Update Service

    Updates Neo4j graph incrementally as files change, propagating
    relationship changes and maintaining consistency.
    """

    def __init__(self):
        # Update tracking
        self.pending_changes: Dict[str, List[GraphChange]] = defaultdict(list)
        self.update_history: List[GraphUpdateBatch] = []
        self.max_history_size = 100

        # Propagation configuration
        self.max_propagation_depth = 10
        self.batch_size = 50
        self.propagation_timeout_seconds = 30

        # Performance tracking
        self.metrics = {
            "total_updates": 0,
            "successful_updates": 0,
            "failed_updates": 0,
            "nodes_added": 0,
            "nodes_updated": 0,
            "nodes_deleted": 0,
            "relationships_added": 0,
            "relationships_updated": 0,
            "relationships_deleted": 0,
            "average_propagation_time_ms": 0.0,
            "max_propagation_depth_reached": 0,
        }

        # Relationship type mappings
        self.relationship_types = {
            "import": "IMPORTS",
            "call": "CALLS",
            "inheritance": "INHERITS",
            "contains": "CONTAINS",
            "defines": "DEFINES",
            "references": "REFERENCES",
            "depends_on": "DEPENDS_ON",
        }

    async def process_file_changes(
        self,
        project_path: str,
        file_changes: List[FileChange],
        updated_index: Optional[Any] = None,
    ) -> Optional[GraphUpdateBatch]:
        """Process file changes and update graph incrementally"""
        try:
            if not graph_service.initialized:
                logger.warning(
                    "Graph service not initialized, skipping incremental update"
                )
                return None

            start_time = time.time()

            # Extract project ID from path
            project_id = Path(project_path).name

            # Build change list
            changes = []

            # Get file analyses from updated index if available
            file_analyses = {}
            if updated_index and hasattr(updated_index, "file_analyses"):
                file_analyses = updated_index.file_analyses

            for change in file_changes:
                file_path = change.file_path

                if change.change_type == ChangeType.DELETED:
                    # Handle file deletion
                    changes.extend(
                        await self._build_deletion_changes(project_id, file_path)
                    )

                elif change.change_type in [ChangeType.CREATED, ChangeType.MODIFIED]:
                    # Handle file creation/modification
                    if file_path in file_analyses:
                        analysis = file_analyses[file_path]
                        changes.extend(
                            await self._build_update_changes(
                                project_id,
                                file_path,
                                analysis,
                                is_new=(change.change_type == ChangeType.CREATED),
                            )
                        )
                    else:
                        # Basic file node update without detailed analysis
                        changes.extend(
                            await self._build_basic_file_update(
                                project_id,
                                file_path,
                                change.change_type == ChangeType.CREATED,
                            )
                        )

                elif change.change_type in [ChangeType.MOVED, ChangeType.RENAMED]:
                    # Handle file move/rename
                    old_path = change.old_path or file_path
                    changes.extend(
                        await self._build_move_changes(
                            project_id,
                            old_path,
                            file_path,
                            file_analyses.get(file_path),
                        )
                    )

            if not changes:
                logger.debug("No graph changes to apply")
                return None

            # Create update batch
            batch_id = f"batch_{project_id}_{int(time.time() * 1000)}"
            batch = GraphUpdateBatch(
                batch_id=batch_id, changes=changes, project_id=project_id
            )

            # Apply changes to graph
            success = await self._apply_update_batch(batch)

            if success:
                # Propagate relationship changes
                propagation_result = await self._propagate_relationship_changes(batch)

                execution_time_ms = (time.time() - start_time) * 1000
                logger.info(
                    f"Graph update completed in {execution_time_ms:.1f}ms: "
                    f"{len(changes)} changes, {propagation_result.nodes_affected} nodes affected"
                )

                # Update metrics
                self._update_metrics(batch, propagation_result)

            # Store in history
            self.update_history.append(batch)
            if len(self.update_history) > self.max_history_size:
                self.update_history = self.update_history[-self.max_history_size :]

            return batch

        except Exception as e:
            logger.error(f"Error processing file changes for graph update: {e}")
            return None

    async def _build_deletion_changes(
        self, project_id: str, file_path: str
    ) -> List[GraphChange]:
        """Build changes for file deletion"""
        changes = []

        try:
            # Get existing node data for rollback
            old_data = await self._get_node_data(project_id, file_path, "File")

            # Delete file node
            changes.append(
                GraphChange(
                    change_id=f"delete_file_{hash(file_path)}_{int(time.time() * 1000)}",
                    update_type=GraphUpdateType.NODE_DELETED,
                    entity_type="file",
                    entity_id=file_path,
                    old_data=old_data,
                )
            )

            # Get symbols in file for deletion
            symbols = await self._get_file_symbols(project_id, file_path)
            for symbol_data in symbols:
                changes.append(
                    GraphChange(
                        change_id=f"delete_symbol_{symbol_data['id']}_{int(time.time() * 1000)}",
                        update_type=GraphUpdateType.NODE_DELETED,
                        entity_type="symbol",
                        entity_id=symbol_data["id"],
                        old_data=symbol_data,
                    )
                )

        except Exception as e:
            logger.error(f"Error building deletion changes: {e}")

        return changes

    async def _build_update_changes(
        self, project_id: str, file_path: str, analysis: FileAnalysis, is_new: bool
    ) -> List[GraphChange]:
        """Build changes for file creation/update"""
        changes = []

        try:
            # File node change
            file_data = {
                "path": file_path,
                "language": analysis.language.value if analysis.language else "unknown",
                "size": analysis.file_size,
                "complexity": analysis.complexity.cyclomatic_complexity,
                "last_analyzed": time.time(),
            }

            if is_new:
                changes.append(
                    GraphChange(
                        change_id=f"add_file_{hash(file_path)}_{int(time.time() * 1000)}",
                        update_type=GraphUpdateType.NODE_ADDED,
                        entity_type="file",
                        entity_id=file_path,
                        new_data=file_data,
                    )
                )
            else:
                old_data = await self._get_node_data(project_id, file_path, "File")
                changes.append(
                    GraphChange(
                        change_id=f"update_file_{hash(file_path)}_{int(time.time() * 1000)}",
                        update_type=GraphUpdateType.NODE_UPDATED,
                        entity_type="file",
                        entity_id=file_path,
                        old_data=old_data,
                        new_data=file_data,
                    )
                )

            # Symbol changes
            existing_symbols = await self._get_file_symbols(project_id, file_path)
            existing_symbol_ids = {s["id"] for s in existing_symbols}
            new_symbol_ids = {s.id for s in analysis.symbols}

            # Deleted symbols
            for symbol_data in existing_symbols:
                if symbol_data["id"] not in new_symbol_ids:
                    changes.append(
                        GraphChange(
                            change_id=f"delete_symbol_{symbol_data['id']}_{int(time.time() * 1000)}",
                            update_type=GraphUpdateType.NODE_DELETED,
                            entity_type="symbol",
                            entity_id=symbol_data["id"],
                            old_data=symbol_data,
                        )
                    )

            # New or updated symbols
            for symbol in analysis.symbols:
                symbol_data = {
                    "id": symbol.id,
                    "name": symbol.name,
                    "type": symbol.symbol_type.value,
                    "line_start": symbol.line_start,
                    "line_end": symbol.line_end,
                    "signature": symbol.signature,
                    "complexity": symbol.complexity or 0,
                }

                if symbol.id not in existing_symbol_ids:
                    changes.append(
                        GraphChange(
                            change_id=f"add_symbol_{symbol.id}_{int(time.time() * 1000)}",
                            update_type=GraphUpdateType.NODE_ADDED,
                            entity_type="symbol",
                            entity_id=symbol.id,
                            new_data=symbol_data,
                        )
                    )
                else:
                    # Check if symbol actually changed
                    old_symbol_data = next(
                        (s for s in existing_symbols if s["id"] == symbol.id), None
                    )
                    if old_symbol_data and self._has_symbol_changed(
                        old_symbol_data, symbol_data
                    ):
                        changes.append(
                            GraphChange(
                                change_id=f"update_symbol_{symbol.id}_{int(time.time() * 1000)}",
                                update_type=GraphUpdateType.NODE_UPDATED,
                                entity_type="symbol",
                                entity_id=symbol.id,
                                old_data=old_symbol_data,
                                new_data=symbol_data,
                            )
                        )

            # Dependency relationship changes
            changes.extend(
                await self._build_dependency_changes(
                    project_id, file_path, analysis.dependencies
                )
            )

        except Exception as e:
            logger.error(f"Error building update changes: {e}")

        return changes

    async def _build_basic_file_update(
        self, project_id: str, file_path: str, is_new: bool
    ) -> List[GraphChange]:
        """Build basic file update without detailed analysis"""
        changes = []

        try:
            # Basic file data
            file_data = {
                "path": file_path,
                "language": "unknown",
                "size": 0,
                "complexity": 0,
                "last_analyzed": time.time(),
            }

            if is_new:
                changes.append(
                    GraphChange(
                        change_id=f"add_file_{hash(file_path)}_{int(time.time() * 1000)}",
                        update_type=GraphUpdateType.NODE_ADDED,
                        entity_type="file",
                        entity_id=file_path,
                        new_data=file_data,
                    )
                )
            else:
                old_data = await self._get_node_data(project_id, file_path, "File")
                changes.append(
                    GraphChange(
                        change_id=f"update_file_{hash(file_path)}_{int(time.time() * 1000)}",
                        update_type=GraphUpdateType.NODE_UPDATED,
                        entity_type="file",
                        entity_id=file_path,
                        old_data=old_data,
                        new_data=file_data,
                    )
                )

        except Exception as e:
            logger.error(f"Error building basic file update: {e}")

        return changes

    async def _build_move_changes(
        self,
        project_id: str,
        old_path: str,
        new_path: str,
        analysis: Optional[FileAnalysis],
    ) -> List[GraphChange]:
        """Build changes for file move/rename"""
        changes = []

        try:
            # Update file node path
            old_data = await self._get_node_data(project_id, old_path, "File")
            if old_data:
                new_data = old_data.copy()
                new_data["path"] = new_path

                changes.append(
                    GraphChange(
                        change_id=f"move_file_{hash(old_path)}_{int(time.time() * 1000)}",
                        update_type=GraphUpdateType.NODE_UPDATED,
                        entity_type="file",
                        entity_id=old_path,
                        old_data=old_data,
                        new_data=new_data,
                    )
                )

            # Update symbol file references
            symbols = await self._get_file_symbols(project_id, old_path)
            for symbol_data in symbols:
                # Update symbol's file reference
                changes.append(
                    GraphChange(
                        change_id=f"update_symbol_file_{symbol_data['id']}_{int(time.time() * 1000)}",
                        update_type=GraphUpdateType.RELATIONSHIP_UPDATED,
                        entity_type="symbol_file_ref",
                        entity_id=f"{symbol_data['id']}_file",
                        old_data={"file_path": old_path},
                        new_data={"file_path": new_path},
                    )
                )

        except Exception as e:
            logger.error(f"Error building move changes: {e}")

        return changes

    async def _build_dependency_changes(
        self, project_id: str, file_path: str, dependencies: List[Dependency]
    ) -> List[GraphChange]:
        """Build dependency relationship changes"""
        changes = []

        try:
            # Get existing dependencies
            existing_deps = await self._get_file_dependencies(project_id, file_path)
            existing_dep_keys = {self._get_dependency_key(d) for d in existing_deps}

            # Build new dependency keys
            new_deps = []
            for dep in dependencies:
                dep_key = f"{file_path}_{dep.dependency_type}_{dep.target_file or dep.target_symbol}"
                new_deps.append(
                    {
                        "key": dep_key,
                        "source": file_path,
                        "target": dep.target_file or dep.target_symbol,
                        "type": dep.dependency_type,
                        "line": dep.line_number,
                    }
                )

            new_dep_keys = {d["key"] for d in new_deps}

            # Deleted dependencies
            for dep in existing_deps:
                dep_key = self._get_dependency_key(dep)
                if dep_key not in new_dep_keys:
                    changes.append(
                        GraphChange(
                            change_id=f"delete_dep_{hash(dep_key)}_{int(time.time() * 1000)}",
                            update_type=GraphUpdateType.RELATIONSHIP_DELETED,
                            entity_type="dependency",
                            entity_id=dep_key,
                            old_data=dep,
                        )
                    )

            # New dependencies
            for dep in new_deps:
                if dep["key"] not in existing_dep_keys:
                    changes.append(
                        GraphChange(
                            change_id=f"add_dep_{hash(dep['key'])}_{int(time.time() * 1000)}",
                            update_type=GraphUpdateType.RELATIONSHIP_ADDED,
                            entity_type="dependency",
                            entity_id=dep["key"],
                            new_data=dep,
                        )
                    )

        except Exception as e:
            logger.error(f"Error building dependency changes: {e}")

        return changes

    async def _apply_update_batch(self, batch: GraphUpdateBatch) -> bool:
        """Apply a batch of updates to the graph"""
        try:
            if not graph_service.initialized:
                batch.error_message = "Graph service not initialized"
                return False

            start_time = time.time()

            # Group changes by type for efficient processing
            node_additions = []
            node_updates = []
            node_deletions = []
            rel_additions = []
            rel_updates = []
            rel_deletions = []

            for change in batch.changes:
                if change.update_type == GraphUpdateType.NODE_ADDED:
                    node_additions.append(change)
                elif change.update_type == GraphUpdateType.NODE_UPDATED:
                    node_updates.append(change)
                elif change.update_type == GraphUpdateType.NODE_DELETED:
                    node_deletions.append(change)
                elif change.update_type == GraphUpdateType.RELATIONSHIP_ADDED:
                    rel_additions.append(change)
                elif change.update_type == GraphUpdateType.RELATIONSHIP_UPDATED:
                    rel_updates.append(change)
                elif change.update_type == GraphUpdateType.RELATIONSHIP_DELETED:
                    rel_deletions.append(change)

            # Apply changes in order: deletions, updates, additions
            # This ensures consistency

            # Process relationship deletions first
            if rel_deletions:
                await self._apply_relationship_deletions(
                    batch.project_id, rel_deletions
                )

            # Process node deletions
            if node_deletions:
                await self._apply_node_deletions(batch.project_id, node_deletions)

            # Process node updates
            if node_updates:
                await self._apply_node_updates(batch.project_id, node_updates)

            # Process node additions
            if node_additions:
                await self._apply_node_additions(batch.project_id, node_additions)

            # Process relationship updates
            if rel_updates:
                await self._apply_relationship_updates(batch.project_id, rel_updates)

            # Process relationship additions
            if rel_additions:
                await self._apply_relationship_additions(
                    batch.project_id, rel_additions
                )

            batch.applied_at = datetime.now()
            batch.success = True

            execution_time = time.time() - start_time
            logger.debug(f"Applied batch {batch.batch_id} in {execution_time:.3f}s")

            return True

        except Exception as e:
            logger.error(f"Error applying update batch: {e}")
            batch.error_message = str(e)
            batch.success = False
            return False

    async def _propagate_relationship_changes(
        self, batch: GraphUpdateBatch
    ) -> PropagationResult:
        """Propagate relationship changes through the graph"""
        try:
            start_time = time.time()

            # Identify nodes that need propagation
            affected_nodes = set()

            for change in batch.changes:
                if change.entity_type in ["file", "symbol"]:
                    affected_nodes.add(change.entity_id)
                elif change.entity_type == "dependency":
                    # Extract source and target from dependency
                    if change.new_data:
                        affected_nodes.add(change.new_data.get("source"))
                        affected_nodes.add(change.new_data.get("target"))
                    if change.old_data:
                        affected_nodes.add(change.old_data.get("source"))
                        affected_nodes.add(change.old_data.get("target"))

            # Remove None values
            affected_nodes.discard(None)

            if not affected_nodes:
                return PropagationResult(
                    nodes_affected=0,
                    relationships_updated=0,
                    propagation_depth=0,
                    execution_time_ms=0,
                )

            # Perform BFS propagation
            visited = set()
            queue = deque([(node, 0) for node in affected_nodes])
            max_depth = 0
            relationships_updated = 0

            while queue and len(visited) < 1000:  # Safety limit
                node_id, depth = queue.popleft()

                if node_id in visited or depth > self.max_propagation_depth:
                    continue

                visited.add(node_id)
                max_depth = max(max_depth, depth)

                # Get connected nodes
                connected = await self._get_connected_nodes(batch.project_id, node_id)

                for connected_node in connected:
                    if connected_node not in visited:
                        queue.append((connected_node, depth + 1))
                        relationships_updated += 1

            execution_time_ms = (time.time() - start_time) * 1000

            return PropagationResult(
                nodes_affected=len(visited),
                relationships_updated=relationships_updated,
                propagation_depth=max_depth,
                execution_time_ms=execution_time_ms,
            )

        except Exception as e:
            logger.error(f"Error propagating relationship changes: {e}")
            return PropagationResult(
                nodes_affected=0,
                relationships_updated=0,
                propagation_depth=0,
                execution_time_ms=0,
                warnings=[str(e)],
            )

    async def _apply_node_additions(self, project_id: str, changes: List[GraphChange]):
        """Apply node addition changes"""
        if not changes:
            return

        for batch_changes in self._batch_changes(changes, self.batch_size):
            query = """
            UNWIND $changes AS change
            CREATE (n)
            SET n = change.data
            SET n.project_id = $project_id
            SET n:"""

            # Group by entity type
            by_type = defaultdict(list)
            for change in batch_changes:
                by_type[change.entity_type].append({"data": change.new_data})

            for entity_type, typed_changes in by_type.items():
                label = "File" if entity_type == "file" else "Symbol"
                typed_query = query + label

                await graph_service.driver.execute_query(
                    typed_query, project_id=project_id, changes=typed_changes
                )

    async def _apply_node_updates(self, project_id: str, changes: List[GraphChange]):
        """Apply node update changes"""
        if not changes:
            return

        for batch_changes in self._batch_changes(changes, self.batch_size):
            # Update file nodes
            file_updates = [c for c in batch_changes if c.entity_type == "file"]
            if file_updates:
                query = """
                UNWIND $updates AS update
                MATCH (f:File {path: update.old_path, project_id: $project_id})
                SET f += update.new_data
                """

                updates = [
                    {"old_path": c.entity_id, "new_data": c.new_data}
                    for c in file_updates
                ]

                await graph_service.driver.execute_query(
                    query, project_id=project_id, updates=updates
                )

            # Update symbol nodes
            symbol_updates = [c for c in batch_changes if c.entity_type == "symbol"]
            if symbol_updates:
                query = """
                UNWIND $updates AS update
                MATCH (s:Symbol {id: update.id, project_id: $project_id})
                SET s += update.new_data
                """

                updates = [
                    {"id": c.entity_id, "new_data": c.new_data} for c in symbol_updates
                ]

                await graph_service.driver.execute_query(
                    query, project_id=project_id, updates=updates
                )

    async def _apply_node_deletions(self, project_id: str, changes: List[GraphChange]):
        """Apply node deletion changes"""
        if not changes:
            return

        for batch_changes in self._batch_changes(changes, self.batch_size):
            # Delete file nodes
            file_deletions = [c for c in batch_changes if c.entity_type == "file"]
            if file_deletions:
                paths = [c.entity_id for c in file_deletions]

                query = """
                MATCH (f:File {project_id: $project_id})
                WHERE f.path IN $paths
                DETACH DELETE f
                """

                await graph_service.driver.execute_query(
                    query, project_id=project_id, paths=paths
                )

            # Delete symbol nodes
            symbol_deletions = [c for c in batch_changes if c.entity_type == "symbol"]
            if symbol_deletions:
                ids = [c.entity_id for c in symbol_deletions]

                query = """
                MATCH (s:Symbol {project_id: $project_id})
                WHERE s.id IN $ids
                DETACH DELETE s
                """

                await graph_service.driver.execute_query(
                    query, project_id=project_id, ids=ids
                )

    async def _apply_relationship_additions(
        self, project_id: str, changes: List[GraphChange]
    ):
        """Apply relationship addition changes"""
        if not changes:
            return

        for batch_changes in self._batch_changes(changes, self.batch_size):
            dependencies = []

            for change in batch_changes:
                if change.entity_type == "dependency" and change.new_data:
                    dep = change.new_data
                    rel_type = self.relationship_types.get(
                        dep.get("type", "depends_on"), "DEPENDS_ON"
                    )

                    dependencies.append(
                        {
                            "source": dep["source"],
                            "target": dep["target"],
                            "type": rel_type,
                            "line": dep.get("line", 0),
                        }
                    )

            if dependencies:
                query = """
                UNWIND $deps AS dep
                MATCH (source {project_id: $project_id})
                WHERE source.path = dep.source OR source.id = dep.source
                MATCH (target {project_id: $project_id})
                WHERE target.path = dep.target OR target.id = dep.target
                CREATE (source)-[r:DEPENDS_ON {type: dep.type, line: dep.line}]->(target)
                """

                await graph_service.driver.execute_query(
                    query, project_id=project_id, deps=dependencies
                )

    async def _apply_relationship_updates(
        self, project_id: str, changes: List[GraphChange]
    ):
        """Apply relationship update changes"""
        # For now, treat updates as delete + add
        # In future, could optimize this
        deletions = []
        additions = []

        for change in changes:
            if change.old_data:
                del_change = GraphChange(
                    change_id=f"{change.change_id}_del",
                    update_type=GraphUpdateType.RELATIONSHIP_DELETED,
                    entity_type=change.entity_type,
                    entity_id=change.entity_id,
                    old_data=change.old_data,
                )
                deletions.append(del_change)

            if change.new_data:
                add_change = GraphChange(
                    change_id=f"{change.change_id}_add",
                    update_type=GraphUpdateType.RELATIONSHIP_ADDED,
                    entity_type=change.entity_type,
                    entity_id=change.entity_id,
                    new_data=change.new_data,
                )
                additions.append(add_change)

        if deletions:
            await self._apply_relationship_deletions(project_id, deletions)
        if additions:
            await self._apply_relationship_additions(project_id, additions)

    async def _apply_relationship_deletions(
        self, project_id: str, changes: List[GraphChange]
    ):
        """Apply relationship deletion changes"""
        if not changes:
            return

        for batch_changes in self._batch_changes(changes, self.batch_size):
            dependencies = []

            for change in batch_changes:
                if change.entity_type == "dependency" and change.old_data:
                    dep = change.old_data
                    dependencies.append(
                        {"source": dep["source"], "target": dep["target"]}
                    )

            if dependencies:
                query = """
                UNWIND $deps AS dep
                MATCH (source {project_id: $project_id})-[r:DEPENDS_ON]->(target {project_id: $project_id})
                WHERE (source.path = dep.source OR source.id = dep.source) 
                  AND (target.path = dep.target OR target.id = dep.target)
                DELETE r
                """

                await graph_service.driver.execute_query(
                    query, project_id=project_id, deps=dependencies
                )

    def _batch_changes(self, changes: List[GraphChange], batch_size: int):
        """Yield batches of changes"""
        for i in range(0, len(changes), batch_size):
            yield changes[i : i + batch_size]

    def _has_symbol_changed(self, old_data: Dict, new_data: Dict) -> bool:
        """Check if symbol data has materially changed"""
        # Compare relevant fields
        fields_to_check = ["name", "type", "signature", "line_start", "line_end"]

        for field in fields_to_check:
            if old_data.get(field) != new_data.get(field):
                return True

        return False

    def _get_dependency_key(self, dep: Dict) -> str:
        """Generate unique key for dependency"""
        return f"{dep.get('source')}_{dep.get('type')}_{dep.get('target')}"

    async def _get_node_data(
        self, project_id: str, node_id: str, node_type: str
    ) -> Optional[Dict]:
        """Get existing node data from graph"""
        try:
            query = f"""
            MATCH (n:{node_type} {{project_id: $project_id}})
            WHERE n.path = $node_id OR n.id = $node_id
            RETURN n
            LIMIT 1
            """

            records, _, _ = await graph_service.driver.execute_query(
                query, project_id=project_id, node_id=node_id
            )

            if records:
                return dict(records[0]["n"])

            return None

        except Exception as e:
            logger.error(f"Error getting node data: {e}")
            return None

    async def _get_file_symbols(self, project_id: str, file_path: str) -> List[Dict]:
        """Get symbols in a file"""
        try:
            query = """
            MATCH (f:File {path: $file_path, project_id: $project_id})-[:CONTAINS]->(s:Symbol)
            RETURN s
            """

            records, _, _ = await graph_service.driver.execute_query(
                query, project_id=project_id, file_path=file_path
            )

            return [dict(record["s"]) for record in records]

        except Exception as e:
            logger.error(f"Error getting file symbols: {e}")
            return []

    async def _get_file_dependencies(
        self, project_id: str, file_path: str
    ) -> List[Dict]:
        """Get dependencies from a file"""
        try:
            query = """
            MATCH (f:File {path: $file_path, project_id: $project_id})-[r:DEPENDS_ON]->(target)
            RETURN f.path as source, 
                   type(r) as type, 
                   target.path as target, 
                   r.line as line
            """

            records, _, _ = await graph_service.driver.execute_query(
                query, project_id=project_id, file_path=file_path
            )

            return [dict(record) for record in records]

        except Exception as e:
            logger.error(f"Error getting file dependencies: {e}")
            return []

    async def _get_connected_nodes(self, project_id: str, node_id: str) -> List[str]:
        """Get nodes connected to a given node"""
        try:
            query = """
            MATCH (n {project_id: $project_id})-[r]-(connected)
            WHERE n.path = $node_id OR n.id = $node_id
            RETURN DISTINCT connected.path as path, connected.id as id
            LIMIT 100
            """

            records, _, _ = await graph_service.driver.execute_query(
                query, project_id=project_id, node_id=node_id
            )

            connected = []
            for record in records:
                if record.get("path"):
                    connected.append(record["path"])
                elif record.get("id"):
                    connected.append(record["id"])

            return connected

        except Exception as e:
            logger.error(f"Error getting connected nodes: {e}")
            return []

    def _update_metrics(self, batch: GraphUpdateBatch, propagation: PropagationResult):
        """Update service metrics"""
        self.metrics["total_updates"] += 1

        if batch.success:
            self.metrics["successful_updates"] += 1
        else:
            self.metrics["failed_updates"] += 1

        # Count change types
        for change in batch.changes:
            if change.update_type == GraphUpdateType.NODE_ADDED:
                self.metrics["nodes_added"] += 1
            elif change.update_type == GraphUpdateType.NODE_UPDATED:
                self.metrics["nodes_updated"] += 1
            elif change.update_type == GraphUpdateType.NODE_DELETED:
                self.metrics["nodes_deleted"] += 1
            elif change.update_type == GraphUpdateType.RELATIONSHIP_ADDED:
                self.metrics["relationships_added"] += 1
            elif change.update_type == GraphUpdateType.RELATIONSHIP_UPDATED:
                self.metrics["relationships_updated"] += 1
            elif change.update_type == GraphUpdateType.RELATIONSHIP_DELETED:
                self.metrics["relationships_deleted"] += 1

        # Update propagation metrics
        if propagation.execution_time_ms > 0:
            current_avg = self.metrics["average_propagation_time_ms"]
            new_avg = (current_avg + propagation.execution_time_ms) / 2
            self.metrics["average_propagation_time_ms"] = new_avg

        if (
            propagation.propagation_depth
            > self.metrics["max_propagation_depth_reached"]
        ):
            self.metrics["max_propagation_depth_reached"] = (
                propagation.propagation_depth
            )

    async def rollback_batch(self, batch_id: str) -> bool:
        """Rollback a previously applied batch"""
        try:
            # Find batch in history
            batch = next(
                (b for b in self.update_history if b.batch_id == batch_id), None
            )

            if not batch or not batch.success:
                logger.warning(
                    f"Cannot rollback batch {batch_id}: not found or not successful"
                )
                return False

            # Build reverse changes
            reverse_changes = []

            for change in reversed(batch.changes):  # Reverse order
                if change.update_type == GraphUpdateType.NODE_ADDED:
                    # Delete the added node
                    reverse_changes.append(
                        GraphChange(
                            change_id=f"rollback_{change.change_id}",
                            update_type=GraphUpdateType.NODE_DELETED,
                            entity_type=change.entity_type,
                            entity_id=change.entity_id,
                            old_data=change.new_data,
                        )
                    )
                elif change.update_type == GraphUpdateType.NODE_DELETED:
                    # Re-add the deleted node
                    reverse_changes.append(
                        GraphChange(
                            change_id=f"rollback_{change.change_id}",
                            update_type=GraphUpdateType.NODE_ADDED,
                            entity_type=change.entity_type,
                            entity_id=change.entity_id,
                            new_data=change.old_data,
                        )
                    )
                elif change.update_type == GraphUpdateType.NODE_UPDATED:
                    # Restore old data
                    reverse_changes.append(
                        GraphChange(
                            change_id=f"rollback_{change.change_id}",
                            update_type=GraphUpdateType.NODE_UPDATED,
                            entity_type=change.entity_type,
                            entity_id=change.entity_id,
                            old_data=change.new_data,
                            new_data=change.old_data,
                        )
                    )

            # Apply rollback
            rollback_batch = GraphUpdateBatch(
                batch_id=f"rollback_{batch_id}",
                changes=reverse_changes,
                project_id=batch.project_id,
            )

            success = await self._apply_update_batch(rollback_batch)

            if success:
                logger.info(f"Successfully rolled back batch {batch_id}")

            return success

        except Exception as e:
            logger.error(f"Error rolling back batch {batch_id}: {e}")
            return False

    def get_metrics(self) -> Dict[str, Any]:
        """Get service metrics"""
        return self.metrics.copy()

    def get_update_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent update history"""
        history = []

        for batch in self.update_history[-limit:]:
            history.append(
                {
                    "batch_id": batch.batch_id,
                    "project_id": batch.project_id,
                    "created_at": batch.created_at.isoformat(),
                    "applied_at": (
                        batch.applied_at.isoformat() if batch.applied_at else None
                    ),
                    "success": batch.success,
                    "change_count": len(batch.changes),
                    "error_message": batch.error_message,
                }
            )

        return history


# Global instance
incremental_graph_service = IncrementalGraphUpdateService()
