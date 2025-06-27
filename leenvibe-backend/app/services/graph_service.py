"""
Neo4j Graph Database Service

Manages connections and operations with Neo4j graph database for storing
and querying code relationships and architecture patterns.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import networkx as nx
from neo4j import AsyncDriver, Driver, GraphDatabase
from neo4j.exceptions import AuthError, ServiceUnavailable

from ..models.ast_models import Dependency, ProjectIndex, Symbol
from ..models.graph_models import (
    ArchitecturePattern,
    FileNode,
    GraphNode,
    GraphQuery,
    GraphRelationship,
    GraphStatistics,
    GraphVisualizationData,
    ImpactAnalysisResult,
    NodeLabel,
    ProjectNode,
    RelationshipType,
    SymbolNode,
)

logger = logging.getLogger(__name__)


class GraphService:
    """
    Neo4j Graph Database Service

    Provides high-level interface for storing and querying code relationships
    in a Neo4j graph database.
    """

    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        username: str = "neo4j",
        password: str = "leenvibe123",
        database: str = "neo4j",
    ):
        self.uri = uri
        self.username = username
        self.password = password
        self.database = database
        self.driver: Optional[Driver] = None
        self.initialized = False

        # Connection pool settings
        self.max_connection_lifetime = 3600  # 1 hour
        self.max_connection_pool_size = 50
        self.connection_acquisition_timeout = 60

    async def initialize(self) -> bool:
        """Initialize connection to Neo4j database"""
        try:
            logger.info(f"Connecting to Neo4j at {self.uri}...")

            # Create driver with configuration
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password),
                max_connection_lifetime=self.max_connection_lifetime,
                max_connection_pool_size=self.max_connection_pool_size,
                connection_acquisition_timeout=self.connection_acquisition_timeout,
            )

            # Test connection
            await self._test_connection()

            # Initialize schema and constraints
            await self._initialize_schema()

            self.initialized = True
            logger.info("Neo4j graph service initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Neo4j: {e}")
            logger.info("Graph service will continue with in-memory graph fallback")
            self.initialized = False
            return False

    async def close(self):
        """Close database connection"""
        if self.driver:
            await asyncio.get_event_loop().run_in_executor(None, self.driver.close)
            logger.info("Neo4j connection closed")

    async def _test_connection(self):
        """Test database connection"""
        try:
            with self.driver.session(database=self.database) as session:
                result = session.run("RETURN 1 as test")
                record = result.single()
                if not record or record["test"] != 1:
                    raise Exception("Connection test failed")
                logger.debug("Neo4j connection test successful")
        except Exception as e:
            raise Exception(f"Neo4j connection failed: {e}")

    async def _initialize_schema(self):
        """Initialize database schema and constraints"""
        try:
            constraints_and_indexes = [
                # Node uniqueness constraints
                "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Project) REQUIRE p.id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (f:File) REQUIRE f.id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Class) REQUIRE c.id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (fn:Function) REQUIRE fn.id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (m:Method) REQUIRE m.id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (v:Variable) REQUIRE v.id IS UNIQUE",
                # Indexes for performance
                "CREATE INDEX IF NOT EXISTS FOR (p:Project) ON (p.name)",
                "CREATE INDEX IF NOT EXISTS FOR (f:File) ON (f.file_path)",
                "CREATE INDEX IF NOT EXISTS FOR (c:Class) ON (c.name)",
                "CREATE INDEX IF NOT EXISTS FOR (fn:Function) ON (fn.name)",
                "CREATE INDEX IF NOT EXISTS FOR (m:Method) ON (m.name)",
                "CREATE INDEX IF NOT EXISTS FOR (v:Variable) ON (v.name)",
                # Composite indexes
                "CREATE INDEX IF NOT EXISTS FOR (f:File) ON (f.language, f.complexity)",
                "CREATE INDEX IF NOT EXISTS FOR ()-[r:CALLS]-() ON (r.call_count)",
                "CREATE INDEX IF NOT EXISTS FOR ()-[r:DEPENDS_ON]-() ON (r.strength)",
            ]

            with self.driver.session(database=self.database) as session:
                for query in constraints_and_indexes:
                    try:
                        session.run(query)
                        logger.debug(f"Executed: {query}")
                    except Exception as e:
                        logger.warning(f"Schema query failed: {query}, Error: {e}")

            logger.info("Database schema initialized")

        except Exception as e:
            logger.error(f"Failed to initialize schema: {e}")
            raise

    async def store_project_graph(
        self, project_index: ProjectIndex, workspace_path: str
    ) -> bool:
        """Store project structure as graph in Neo4j"""
        try:
            if not self.initialized:
                logger.warning("Graph service not initialized, skipping storage")
                return False

            logger.info(f"Storing project graph for: {workspace_path}")

            with self.driver.session(database=self.database) as session:
                # Start transaction
                with session.begin_transaction() as tx:

                    # Create project node
                    project_node = ProjectNode(
                        id=f"project_{hash(workspace_path)}",
                        name=Path(workspace_path).name,
                        workspace_path=workspace_path,
                        total_files=project_index.supported_files,
                        total_symbols=len(project_index.symbols),
                    )

                    # Store project
                    await self._create_node(tx, project_node)

                    # Store files
                    file_nodes = []
                    for file_path, file_analysis in project_index.files.items():
                        file_node = FileNode(
                            id=f"file_{hash(file_path)}",
                            name=Path(file_path).name,
                            file_path=file_path,
                            language=file_analysis.language,
                            lines_of_code=file_analysis.complexity.lines_of_code,
                            complexity=file_analysis.complexity.cyclomatic_complexity,
                        )
                        file_nodes.append(file_node)
                        await self._create_node(tx, file_node)

                        # Connect file to project
                        file_rel = GraphRelationship(
                            source_id=project_node.id,
                            target_id=file_node.id,
                            relationship_type=RelationshipType.CONTAINS,
                        )
                        await self._create_relationship(tx, file_rel)

                    # Store symbols
                    symbol_nodes = []
                    for symbol_id, symbol in project_index.symbols.items():
                        symbol_node = SymbolNode(
                            id=symbol_id,
                            name=symbol.name,
                            symbol_type=symbol.symbol_type,
                            file_path=symbol.file_path,
                            line_start=symbol.line_start,
                            line_end=symbol.line_end,
                            visibility=symbol.visibility,
                            parameters=symbol.parameters,
                            return_type=symbol.return_type,
                        )
                        symbol_nodes.append(symbol_node)
                        await self._create_node(tx, symbol_node)

                        # Connect symbol to file
                        file_id = f"file_{hash(symbol.file_path)}"
                        symbol_rel = GraphRelationship(
                            source_id=file_id,
                            target_id=symbol_id,
                            relationship_type=RelationshipType.DEFINES,
                        )
                        await self._create_relationship(tx, symbol_rel)

                    # Store dependencies
                    for dependency in project_index.dependencies:
                        if dependency.source_file and dependency.target_file:
                            source_id = f"file_{hash(dependency.source_file)}"
                            target_id = f"file_{hash(dependency.target_file)}"

                            dep_rel = GraphRelationship(
                                source_id=source_id,
                                target_id=target_id,
                                relationship_type=RelationshipType.DEPENDS_ON,
                                properties={"import_type": dependency.dependency_type},
                            )
                            await self._create_relationship(tx, dep_rel)

                    # Commit transaction
                    tx.commit()

            logger.info(
                f"Project graph stored successfully: {len(file_nodes)} files, {len(symbol_nodes)} symbols"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to store project graph: {e}")
            return False

    async def _create_node(self, tx, node: GraphNode):
        """Create a node in the database"""
        query = f"""
        MERGE (n:{node.label} {{id: $id}})
        SET n = $properties
        RETURN n
        """

        result = tx.run(query, id=node.id, properties=node.properties)
        return result.single()

    async def _create_relationship(self, tx, rel: GraphRelationship):
        """Create a relationship in the database"""
        props_str = rel.to_cypher_properties()

        query = f"""
        MATCH (a {{id: $source_id}})
        MATCH (b {{id: $target_id}})
        MERGE (a)-[r:{rel.relationship_type}]->(b)
        """

        if props_str and props_str != "{}":
            query += f" SET r = $properties"
            tx.run(
                query,
                source_id=rel.source_id,
                target_id=rel.target_id,
                properties=rel.properties,
            )
        else:
            tx.run(query, source_id=rel.source_id, target_id=rel.target_id)

    async def find_dependencies(self, symbol_id: str) -> List[Dict[str, Any]]:
        """Find all dependencies for a symbol"""
        try:
            if not self.initialized:
                return []

            query = """
            MATCH (s {id: $symbol_id})-[r:DEPENDS_ON|CALLS|USES*1..3]->(target)
            RETURN target.id as id, target.name as name, 
                   labels(target) as labels, type(r) as relationship_type,
                   length(r) as distance
            ORDER BY distance, target.name
            LIMIT 50
            """

            with self.driver.session(database=self.database) as session:
                result = session.run(query, symbol_id=symbol_id)
                dependencies = []

                for record in result:
                    dependencies.append(
                        {
                            "id": record["id"],
                            "name": record["name"],
                            "labels": record["labels"],
                            "relationship_type": record["relationship_type"],
                            "distance": record["distance"],
                        }
                    )

                return dependencies

        except Exception as e:
            logger.error(f"Error finding dependencies: {e}")
            return []

    async def analyze_impact(self, symbol_id: str) -> ImpactAnalysisResult:
        """Analyze impact of changing a symbol"""
        try:
            if not self.initialized:
                return ImpactAnalysisResult(
                    target_entity=symbol_id, risk_level="unknown"
                )

            # Find direct dependents
            direct_query = """
            MATCH (target {id: $symbol_id})<-[r:CALLS|USES|DEPENDS_ON]-(dependent)
            RETURN dependent.id as id, dependent.name as name, 
                   labels(dependent) as labels, type(r) as relationship_type
            """

            # Find indirect dependents (2-3 hops)
            indirect_query = """
            MATCH (target {id: $symbol_id})<-[r:CALLS|USES|DEPENDS_ON*2..3]-(dependent)
            WHERE NOT (target)<-[:CALLS|USES|DEPENDS_ON]-(dependent)
            RETURN dependent.id as id, dependent.name as name,
                   labels(dependent) as labels, length(r) as distance
            ORDER BY distance
            LIMIT 20
            """

            with self.driver.session(database=self.database) as session:
                # Get direct dependencies
                direct_result = session.run(direct_query, symbol_id=symbol_id)
                directly_affected = [record["name"] for record in direct_result]

                # Get indirect dependencies
                indirect_result = session.run(indirect_query, symbol_id=symbol_id)
                indirectly_affected = [record["name"] for record in indirect_result]

                # Calculate risk level
                total_affected = len(directly_affected) + len(indirectly_affected)
                if total_affected == 0:
                    risk_level = "low"
                elif total_affected < 5:
                    risk_level = "low"
                elif total_affected < 15:
                    risk_level = "medium"
                else:
                    risk_level = "high"

                return ImpactAnalysisResult(
                    target_entity=symbol_id,
                    directly_affected=directly_affected,
                    indirectly_affected=indirectly_affected,
                    risk_level=risk_level,
                    affected_components={
                        "direct": len(directly_affected),
                        "indirect": len(indirectly_affected),
                    },
                    recommendations=self._generate_impact_recommendations(
                        risk_level, total_affected
                    ),
                )

        except Exception as e:
            logger.error(f"Error analyzing impact: {e}")
            return ImpactAnalysisResult(target_entity=symbol_id, risk_level="error")

    def _generate_impact_recommendations(
        self, risk_level: str, affected_count: int
    ) -> List[str]:
        """Generate recommendations based on impact analysis"""
        recommendations = []

        if risk_level == "high":
            recommendations.extend(
                [
                    "⚠️ High impact change - proceed with caution",
                    "Consider creating comprehensive unit tests before modification",
                    "Plan for extensive regression testing",
                    "Consider refactoring to reduce coupling before changes",
                ]
            )
        elif risk_level == "medium":
            recommendations.extend(
                [
                    "⚡ Medium impact change - test thoroughly",
                    "Review dependent components for compatibility",
                    "Update related documentation",
                ]
            )
        else:
            recommendations.append(
                "✅ Low impact change - standard testing should suffice"
            )

        if affected_count > 0:
            recommendations.append(f"📊 Review {affected_count} affected components")

        return recommendations

    async def get_architecture_patterns(
        self, project_id: str
    ) -> List[ArchitecturePattern]:
        """Detect common architecture patterns in the project"""
        try:
            if not self.initialized:
                return []

            patterns = []

            # Detect MVC pattern
            mvc_pattern = await self._detect_mvc_pattern(project_id)
            if mvc_pattern:
                patterns.append(mvc_pattern)

            # Detect service layer pattern
            service_pattern = await self._detect_service_layer_pattern(project_id)
            if service_pattern:
                patterns.append(service_pattern)

            # Detect repository pattern
            repo_pattern = await self._detect_repository_pattern(project_id)
            if repo_pattern:
                patterns.append(repo_pattern)

            return patterns

        except Exception as e:
            logger.error(f"Error detecting architecture patterns: {e}")
            return []

    async def _detect_mvc_pattern(
        self, project_id: str
    ) -> Optional[ArchitecturePattern]:
        """Detect MVC (Model-View-Controller) pattern"""
        try:
            query = """
            MATCH (p:Project {id: $project_id})-[:CONTAINS]->(f:File)
            WHERE f.name =~ '.*[Cc]ontroller.*' OR f.name =~ '.*[Mm]odel.*' OR f.name =~ '.*[Vv]iew.*'
            RETURN f.name as name, f.file_path as path
            """

            with self.driver.session(database=self.database) as session:
                result = session.run(query, project_id=project_id)
                mvc_files = list(result)

                if len(mvc_files) >= 2:  # At least 2 components
                    controllers = [
                        f for f in mvc_files if "controller" in f["name"].lower()
                    ]
                    models = [f for f in mvc_files if "model" in f["name"].lower()]
                    views = [f for f in mvc_files if "view" in f["name"].lower()]

                    component_count = len(
                        [c for c in [controllers, models, views] if c]
                    )
                    confidence = min(0.9, component_count / 3.0 * 0.7 + 0.2)

                    return ArchitecturePattern(
                        pattern_name="MVC (Model-View-Controller)",
                        confidence=confidence,
                        components=[f["name"] for f in mvc_files],
                        description="Separation of concerns with Model, View, and Controller components",
                        relationships=[
                            "Controller -> Model",
                            "Controller -> View",
                            "View -> Model",
                        ],
                    )

            return None

        except Exception as e:
            logger.error(f"Error detecting MVC pattern: {e}")
            return None

    async def _detect_service_layer_pattern(
        self, project_id: str
    ) -> Optional[ArchitecturePattern]:
        """Detect Service Layer pattern"""
        try:
            query = """
            MATCH (p:Project {id: $project_id})-[:CONTAINS]->(f:File)
            WHERE f.name =~ '.*[Ss]ervice.*'
            RETURN f.name as name, f.file_path as path
            """

            with self.driver.session(database=self.database) as session:
                result = session.run(query, project_id=project_id)
                service_files = list(result)

                if len(service_files) >= 1:
                    confidence = min(0.8, len(service_files) / 3.0 * 0.6 + 0.2)

                    return ArchitecturePattern(
                        pattern_name="Service Layer",
                        confidence=confidence,
                        components=[f["name"] for f in service_files],
                        description="Business logic encapsulated in service classes",
                        relationships=[
                            "Controller -> Service",
                            "Service -> Repository/DAO",
                        ],
                    )

            return None

        except Exception as e:
            logger.error(f"Error detecting service pattern: {e}")
            return None

    async def _detect_repository_pattern(
        self, project_id: str
    ) -> Optional[ArchitecturePattern]:
        """Detect Repository pattern"""
        try:
            query = """
            MATCH (p:Project {id: $project_id})-[:CONTAINS]->(f:File)
            WHERE f.name =~ '.*[Rr]epository.*' OR f.name =~ '.*[Dd][Aa][Oo].*'
            RETURN f.name as name, f.file_path as path
            """

            with self.driver.session(database=self.database) as session:
                result = session.run(query, project_id=project_id)
                repo_files = list(result)

                if len(repo_files) >= 1:
                    confidence = min(0.7, len(repo_files) / 2.0 * 0.5 + 0.2)

                    return ArchitecturePattern(
                        pattern_name="Repository/DAO Pattern",
                        confidence=confidence,
                        components=[f["name"] for f in repo_files],
                        description="Data access abstraction layer",
                        relationships=[
                            "Service -> Repository",
                            "Repository -> Database",
                        ],
                    )

            return None

        except Exception as e:
            logger.error(f"Error detecting repository pattern: {e}")
            return None

    async def get_graph_statistics(
        self, project_id: Optional[str] = None
    ) -> GraphStatistics:
        """Get comprehensive graph statistics"""
        try:
            if not self.initialized:
                return GraphStatistics()

            # Base query - limit scope to project if specified
            where_clause = f"WHERE p.id = '{project_id}'" if project_id else ""

            stats_query = f"""
            MATCH (n)
            {where_clause}
            OPTIONAL MATCH (n)-[r]->()
            RETURN 
                count(DISTINCT n) as node_count,
                count(DISTINCT r) as relationship_count,
                labels(n) as node_labels,
                type(r) as relationship_types
            """

            with self.driver.session(database=self.database) as session:
                result = session.run(stats_query)

                total_nodes = 0
                total_relationships = 0
                node_counts = {}
                relationship_counts = {}

                for record in result:
                    total_nodes += record["node_count"] or 0
                    total_relationships += record["relationship_count"] or 0

                    # Count node types
                    if record["node_labels"]:
                        for label in record["node_labels"]:
                            node_counts[label] = node_counts.get(label, 0) + 1

                    # Count relationship types
                    if record["relationship_types"]:
                        rel_type = record["relationship_types"]
                        relationship_counts[rel_type] = (
                            relationship_counts.get(rel_type, 0) + 1
                        )

                # Calculate density
                graph_density = 0.0
                if total_nodes > 1:
                    max_edges = total_nodes * (total_nodes - 1)
                    graph_density = (
                        total_relationships / max_edges if max_edges > 0 else 0.0
                    )

                # Calculate average degree
                average_degree = (
                    (2 * total_relationships) / total_nodes if total_nodes > 0 else 0.0
                )

                return GraphStatistics(
                    total_nodes=total_nodes,
                    total_relationships=total_relationships,
                    node_counts=node_counts,
                    relationship_counts=relationship_counts,
                    graph_density=graph_density,
                    average_degree=average_degree,
                    connected_components=1,  # Simplified for now
                )

        except Exception as e:
            logger.error(f"Error getting graph statistics: {e}")
            return GraphStatistics()

    async def get_visualization_data(
        self, project_id: str, max_nodes: int = 100
    ) -> GraphVisualizationData:
        """Get data formatted for graph visualization"""
        try:
            if not self.initialized:
                return GraphVisualizationData()

            query = f"""
            MATCH (p:Project {{id: $project_id}})-[:CONTAINS*0..2]->(n)
            OPTIONAL MATCH (n)-[r]->(m)
            WHERE p.id = $project_id
            RETURN n.id as node_id, n.name as node_name, labels(n) as node_labels,
                   m.id as target_id, m.name as target_name, type(r) as relationship_type
            LIMIT {max_nodes}
            """

            with self.driver.session(database=self.database) as session:
                result = session.run(query, project_id=project_id)

                nodes = {}
                edges = []

                for record in result:
                    # Add source node
                    node_id = record["node_id"]
                    if node_id not in nodes:
                        nodes[node_id] = {
                            "id": node_id,
                            "name": record["node_name"],
                            "label": (
                                record["node_labels"][0]
                                if record["node_labels"]
                                else "Unknown"
                            ),
                        }

                    # Add target node and edge if they exist
                    if record["target_id"]:
                        target_id = record["target_id"]
                        if target_id not in nodes:
                            nodes[target_id] = {
                                "id": target_id,
                                "name": record["target_name"],
                                "label": "Unknown",
                            }

                        edges.append(
                            {
                                "source": node_id,
                                "target": target_id,
                                "type": record["relationship_type"],
                            }
                        )

                return GraphVisualizationData(
                    nodes=list(nodes.values()),
                    edges=edges,
                    layout="force-directed",
                    metadata={"project_id": project_id, "node_count": len(nodes)},
                )

        except Exception as e:
            logger.error(f"Error getting visualization data: {e}")
            return GraphVisualizationData()

    async def clear_project_data(self, project_id: str) -> bool:
        """Clear all data for a specific project"""
        try:
            if not self.initialized:
                return False

            query = """
            MATCH (p:Project {id: $project_id})-[:CONTAINS*0..]->(n)
            DETACH DELETE n
            """

            with self.driver.session(database=self.database) as session:
                session.run(query, project_id=project_id)

            logger.info(f"Cleared project data: {project_id}")
            return True

        except Exception as e:
            logger.error(f"Error clearing project data: {e}")
            return False


# Global instance
graph_service = GraphService()
