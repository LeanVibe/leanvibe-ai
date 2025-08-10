"""
Enhanced Neo4j Graph Database Service for Code Relationships

Provides comprehensive code analysis through graph database integration,
storing and querying code relationships, dependencies, and architectural structures.
"""

import logging
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError
import os

logger = logging.getLogger(__name__)

class NodeType(Enum):
    """Graph node types for code entities"""
    FILE = "File"
    CLASS = "Class"
    FUNCTION = "Function"
    METHOD = "Method"
    VARIABLE = "Variable"
    MODULE = "Module"
    PACKAGE = "Package"
    INTERFACE = "Interface"
    ENUM = "Enum"
    CONSTANT = "Constant"

class RelationType(Enum):
    """Graph relationship types between code entities"""
    IMPORTS = "IMPORTS"
    CONTAINS = "CONTAINS"
    CALLS = "CALLS"
    INHERITS = "INHERITS"
    IMPLEMENTS = "IMPLEMENTS"
    REFERENCES = "REFERENCES"
    DEPENDS_ON = "DEPENDS_ON"
    USES = "USES"
    DEFINES = "DEFINES"
    OVERRIDES = "OVERRIDES"

@dataclass
class CodeNode:
    """Represents a code entity in the graph"""
    id: str
    name: str
    type: NodeType
    file_path: str
    start_line: int
    end_line: int
    properties: Dict[str, Any]

@dataclass
class CodeRelationship:
    """Represents a relationship between code entities"""
    from_node: str
    to_node: str
    type: RelationType
    properties: Dict[str, Any]

class CodeGraphService:
    """
    Enhanced Neo4j Graph Database Service for Code Relationships
    
    Provides high-level interface for storing and querying code relationships,
    dependencies, and architectural structures in a Neo4j graph database.
    """
    
    def __init__(self, uri: str = None, user: str = None, password: str = None):
        # Use environment variables with defaults for local development
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or os.getenv("NEO4J_USER", "neo4j") 
        self.password = password or os.getenv("NEO4J_PASSWORD", "leanvibe123")
        
        self.driver = None
        self._connected = False
        self._connection_retries = 3
        self._schema_initialized = False
        
    async def connect(self) -> bool:
        """Establish connection to Neo4j database with retry logic"""
        for attempt in range(self._connection_retries):
            try:
                logger.info(f"Attempting Neo4j connection to {self.uri} (attempt {attempt + 1})")
                
                self.driver = GraphDatabase.driver(
                    self.uri, 
                    auth=(self.user, self.password),
                    max_connection_pool_size=10,
                    connection_timeout=30,
                    max_retry_time=15
                )
                
                # Verify connection with async operation
                with self.driver.session() as session:
                    result = session.run("MATCH (n) RETURN count(n) LIMIT 1")
                    result.single()
                    
                self._connected = True
                logger.info(f"Successfully connected to Neo4j at {self.uri}")
                
                # Initialize schema
                await self._initialize_schema()
                return True
                
            except (ServiceUnavailable, AuthError) as e:
                logger.warning(f"Neo4j connection attempt {attempt + 1} failed: {e}")
                if attempt == self._connection_retries - 1:
                    logger.error("All Neo4j connection attempts failed - service will use fallback mode")
                    self._connected = False
                    return False
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                
            except Exception as e:
                logger.error(f"Unexpected error connecting to Neo4j: {e}")
                self._connected = False
                return False
        
        return False
    
    async def disconnect(self):
        """Close connection to Neo4j database"""
        if self.driver:
            self.driver.close()
            self._connected = False
            self._schema_initialized = False
            logger.info("Disconnected from Neo4j")
    
    def is_connected(self) -> bool:
        """Check if connected to Neo4j"""
        return self._connected and self.driver is not None
    
    async def _initialize_schema(self):
        """Initialize Neo4j schema with constraints and indexes"""
        if self._schema_initialized or not self.is_connected():
            return
            
        schema_queries = [
            # Node uniqueness constraints
            "CREATE CONSTRAINT unique_code_node IF NOT EXISTS FOR (n:CodeNode) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT unique_file IF NOT EXISTS FOR (f:File) REQUIRE f.path IS UNIQUE",
            "CREATE CONSTRAINT unique_class IF NOT EXISTS FOR (c:Class) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT unique_function IF NOT EXISTS FOR (f:Function) REQUIRE f.id IS UNIQUE",
            "CREATE CONSTRAINT unique_method IF NOT EXISTS FOR (m:Method) REQUIRE m.id IS UNIQUE",
            
            # Performance indexes
            "CREATE INDEX code_node_type IF NOT EXISTS FOR (n:CodeNode) ON (n.type)",
            "CREATE INDEX code_node_name IF NOT EXISTS FOR (n:CodeNode) ON (n.name)",
            "CREATE INDEX file_path_idx IF NOT EXISTS FOR (f:File) ON (f.file_path)",
            "CREATE INDEX function_name_idx IF NOT EXISTS FOR (f:Function) ON (f.name)",
            "CREATE INDEX class_name_idx IF NOT EXISTS FOR (c:Class) ON (c.name)",
            "CREATE INDEX symbol_line_idx IF NOT EXISTS FOR (n:CodeNode) ON (n.start_line)",
            
            # Relationship indexes
            "CREATE INDEX rel_calls_count IF NOT EXISTS FOR ()-[r:CALLS]-() ON (r.call_count)",
            "CREATE INDEX rel_dependency_strength IF NOT EXISTS FOR ()-[r:DEPENDS_ON]-() ON (r.strength)",
        ]
        
        try:
            with self.driver.session() as session:
                for query in schema_queries:
                    try:
                        session.run(query)
                        logger.debug(f"Schema query executed: {query[:50]}...")
                    except Exception as e:
                        # Constraints might already exist, that's okay
                        logger.debug(f"Schema query result: {e}")
                        
            self._schema_initialized = True
            logger.info("Neo4j schema initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j schema: {e}")
            raise
    
    async def add_code_node(self, node: CodeNode) -> bool:
        """Add a code node to the graph"""
        if not self.is_connected():
            logger.warning("Neo4j not connected - skipping node creation")
            return False
            
        try:
            with self.driver.session() as session:
                query = """
                MERGE (n:CodeNode:$type {id: $id})
                SET n.name = $name,
                    n.file_path = $file_path,
                    n.start_line = $start_line,
                    n.end_line = $end_line,
                    n.type = $node_type,
                    n += $properties,
                    n.last_updated = timestamp()
                RETURN n
                """
                
                result = session.run(query,
                    id=node.id,
                    name=node.name,
                    file_path=node.file_path,
                    start_line=node.start_line,
                    end_line=node.end_line,
                    node_type=node.type.value,
                    type=node.type.value,  # For dynamic label
                    properties=node.properties or {}
                )
                
                return result.single() is not None
                
        except Exception as e:
            logger.error(f"Failed to add code node {node.id}: {e}")
            return False
    
    async def add_relationship(self, relationship: CodeRelationship) -> bool:
        """Add a relationship between code nodes"""
        if not self.is_connected():
            logger.warning("Neo4j not connected - skipping relationship creation")
            return False
            
        try:
            with self.driver.session() as session:
                query = """
                MATCH (from:CodeNode {id: $from_id})
                MATCH (to:CodeNode {id: $to_id})
                MERGE (from)-[r:$rel_type]->(to)
                SET r += $properties,
                    r.created = CASE WHEN r.created IS NULL THEN timestamp() ELSE r.created END,
                    r.last_updated = timestamp()
                RETURN r
                """
                
                result = session.run(query,
                    from_id=relationship.from_node,
                    to_id=relationship.to_node,
                    rel_type=relationship.type.value,
                    properties=relationship.properties or {}
                )
                
                return result.single() is not None
                
        except Exception as e:
            logger.error(f"Failed to add relationship {relationship.from_node} -> {relationship.to_node}: {e}")
            return False
    
    async def get_dependencies(self, node_id: str, depth: int = 2) -> List[Dict[str, Any]]:
        """Get dependencies for a code node"""
        if not self.is_connected():
            logger.warning("Neo4j not connected - returning empty dependencies")
            return []
            
        try:
            with self.driver.session() as session:
                query = """
                MATCH (start:CodeNode {id: $node_id})
                MATCH path = (start)-[:DEPENDS_ON|IMPORTS|CALLS*1..$depth]->(dep)
                RETURN dep.id as id, dep.name as name, dep.type as type, 
                       dep.file_path as file_path, length(path) as distance,
                       relationships(path) as relationships
                ORDER BY distance, dep.name
                LIMIT 50
                """
                
                result = session.run(query, node_id=node_id, depth=depth)
                dependencies = []
                
                for record in result:
                    dependencies.append({
                        'id': record['id'],
                        'name': record['name'],
                        'type': record['type'],
                        'file_path': record['file_path'],
                        'distance': record['distance'],
                        'relationships': [rel.type for rel in record['relationships']]
                    })
                
                return dependencies
                
        except Exception as e:
            logger.error(f"Failed to get dependencies for {node_id}: {e}")
            return []
    
    async def get_dependents(self, node_id: str, depth: int = 2) -> List[Dict[str, Any]]:
        """Get nodes that depend on this code node"""
        if not self.is_connected():
            logger.warning("Neo4j not connected - returning empty dependents")
            return []
            
        try:
            with self.driver.session() as session:
                query = """
                MATCH (target:CodeNode {id: $node_id})
                MATCH path = (dependent)-[:DEPENDS_ON|IMPORTS|CALLS*1..$depth]->(target)
                RETURN dependent.id as id, dependent.name as name, dependent.type as type,
                       dependent.file_path as file_path, length(path) as distance,
                       relationships(path) as relationships
                ORDER BY distance, dependent.name
                LIMIT 50
                """
                
                result = session.run(query, node_id=node_id, depth=depth)
                dependents = []
                
                for record in result:
                    dependents.append({
                        'id': record['id'],
                        'name': record['name'],
                        'type': record['type'],
                        'file_path': record['file_path'],
                        'distance': record['distance'],
                        'relationships': [rel.type for rel in record['relationships']]
                    })
                
                return dependents
                
        except Exception as e:
            logger.error(f"Failed to get dependents for {node_id}: {e}")
            return []
    
    async def get_architecture_overview(self, project_id: str = None) -> Dict[str, Any]:
        """Get high-level architecture overview with detailed statistics"""
        if not self.is_connected():
            return {"error": "Neo4j not connected", "statistics": {}}
            
        try:
            with self.driver.session() as session:
                # Get node counts by type
                stats_query = """
                MATCH (n:CodeNode)
                WHERE $project_id IS NULL OR n.file_path CONTAINS $project_id
                RETURN n.type as node_type, count(n) as count
                ORDER BY count DESC
                """
                
                stats_result = session.run(stats_query, project_id=project_id)
                node_stats = {record['node_type']: record['count'] for record in stats_result}
                
                # Get relationship counts by type
                rel_query = """
                MATCH (a:CodeNode)-[r]->(b:CodeNode)
                WHERE $project_id IS NULL OR (a.file_path CONTAINS $project_id AND b.file_path CONTAINS $project_id)
                RETURN type(r) as rel_type, count(r) as count
                ORDER BY count DESC
                """
                
                rel_result = session.run(rel_query, project_id=project_id)
                rel_stats = {record['rel_type']: record['count'] for record in rel_result}
                
                # Get most connected nodes (potential hotspots)
                hotspots_query = """
                MATCH (n:CodeNode)
                WHERE $project_id IS NULL OR n.file_path CONTAINS $project_id
                OPTIONAL MATCH (n)-[r_out]->()
                WITH n, count(r_out) as out_degree
                OPTIONAL MATCH ()-[r_in]->(n)
                WITH n, out_degree, count(r_in) as in_degree
                WITH n, out_degree + in_degree as total_degree
                WHERE total_degree > 0
                RETURN n.id as id, n.name as name, n.type as type, 
                       n.file_path as file_path, total_degree,
                       out_degree, in_degree
                ORDER BY total_degree DESC
                LIMIT 10
                """
                
                hotspots_result = session.run(hotspots_query, project_id=project_id)
                hotspots = []
                for record in hotspots_result:
                    hotspots.append({
                        'id': record['id'],
                        'name': record['name'],
                        'type': record['type'],
                        'file_path': record['file_path'],
                        'total_connections': record['total_degree'],
                        'outgoing_connections': record['out_degree'],
                        'incoming_connections': record['in_degree']
                    })
                
                # Calculate graph metrics
                total_nodes = sum(node_stats.values())
                total_relationships = sum(rel_stats.values())
                
                # Graph density calculation
                max_possible_edges = total_nodes * (total_nodes - 1) if total_nodes > 1 else 0
                density = total_relationships / max_possible_edges if max_possible_edges > 0 else 0.0
                
                return {
                    'node_statistics': node_stats,
                    'relationship_statistics': rel_stats,
                    'hotspots': hotspots,
                    'metrics': {
                        'total_nodes': total_nodes,
                        'total_relationships': total_relationships,
                        'graph_density': density,
                        'average_degree': (2 * total_relationships) / total_nodes if total_nodes > 0 else 0.0
                    },
                    'project_id': project_id
                }
                
        except Exception as e:
            logger.error(f"Failed to get architecture overview: {e}")
            return {"error": str(e), "statistics": {}}
    
    async def find_circular_dependencies(self, project_id: str = None, max_depth: int = 10) -> List[List[str]]:
        """Find circular dependencies in the codebase"""
        if not self.is_connected():
            logger.warning("Neo4j not connected - returning empty circular dependencies")
            return []
            
        try:
            with self.driver.session() as session:
                query = f"""
                MATCH path = (start:CodeNode)-[:DEPENDS_ON|IMPORTS*2..{max_depth}]->(start)
                WHERE $project_id IS NULL OR start.file_path CONTAINS $project_id
                AND length(path) > 2
                WITH nodes(path) as cycle_nodes, length(path) as cycle_length
                RETURN [n IN cycle_nodes | {{id: n.id, name: n.name, type: n.type}}] as cycle,
                       cycle_length
                ORDER BY cycle_length, cycle[0].name
                LIMIT 20
                """
                
                result = session.run(query, project_id=project_id)
                cycles = []
                
                for record in result:
                    cycle_data = record['cycle']
                    cycle_length = record['cycle_length']
                    
                    if cycle_data and len(cycle_data) > 2:  # Valid cycle
                        cycles.append({
                            'cycle': cycle_data,
                            'length': cycle_length,
                            'severity': 'high' if cycle_length <= 3 else 'medium' if cycle_length <= 5 else 'low'
                        })
                
                return cycles
                
        except Exception as e:
            logger.error(f"Failed to find circular dependencies: {e}")
            return []
    
    async def analyze_code_complexity(self, project_id: str = None) -> Dict[str, Any]:
        """Analyze code complexity metrics across the project"""
        if not self.is_connected():
            return {"error": "Neo4j not connected"}
            
        try:
            with self.driver.session() as session:
                # Function complexity analysis
                complexity_query = """
                MATCH (n:CodeNode)
                WHERE n.type IN ['Function', 'Method'] 
                AND ($project_id IS NULL OR n.file_path CONTAINS $project_id)
                AND exists(n.complexity)
                RETURN n.name as name, n.type as type, n.file_path as file_path,
                       n.complexity as complexity, n.lines_of_code as loc
                ORDER BY n.complexity DESC
                LIMIT 20
                """
                
                result = session.run(complexity_query, project_id=project_id)
                complex_functions = []
                total_complexity = 0
                function_count = 0
                
                for record in result:
                    complexity = record.get('complexity', 0)
                    complex_functions.append({
                        'name': record['name'],
                        'type': record['type'], 
                        'file_path': record['file_path'],
                        'complexity': complexity,
                        'lines_of_code': record.get('loc', 0)
                    })
                    total_complexity += complexity
                    function_count += 1
                
                # File complexity analysis
                file_complexity_query = """
                MATCH (f:File)
                WHERE $project_id IS NULL OR f.file_path CONTAINS $project_id
                OPTIONAL MATCH (f)-[:CONTAINS]->(s:CodeNode)
                WHERE s.type IN ['Function', 'Method', 'Class']
                RETURN f.file_path as file_path, 
                       count(s) as symbol_count,
                       avg(s.complexity) as avg_complexity,
                       f.lines_of_code as loc
                ORDER BY avg_complexity DESC
                LIMIT 20
                """
                
                file_result = session.run(file_complexity_query, project_id=project_id)
                complex_files = [
                    {
                        'file_path': record['file_path'],
                        'symbol_count': record['symbol_count'],
                        'average_complexity': record.get('avg_complexity', 0),
                        'lines_of_code': record.get('loc', 0)
                    }
                    for record in file_result
                ]
                
                return {
                    'complex_functions': complex_functions,
                    'complex_files': complex_files,
                    'summary': {
                        'average_function_complexity': total_complexity / function_count if function_count > 0 else 0,
                        'total_functions_analyzed': function_count,
                        'high_complexity_threshold': 10,
                        'functions_above_threshold': len([f for f in complex_functions if f.get('complexity', 0) > 10])
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to analyze code complexity: {e}")
            return {"error": str(e)}
    
    async def clear_project_data(self, project_id: str) -> bool:
        """Clear all data for a specific project"""
        if not self.is_connected():
            logger.warning("Neo4j not connected - cannot clear project data")
            return False
            
        try:
            with self.driver.session() as session:
                # Count nodes to be deleted
                count_query = """
                MATCH (n:CodeNode)
                WHERE n.file_path CONTAINS $project_id
                RETURN count(n) as node_count
                """
                count_result = session.run(count_query, project_id=project_id)
                node_count = count_result.single()['node_count']
                
                # Delete relationships first to avoid constraint violations
                rel_query = """
                MATCH (a:CodeNode)-[r]-(b:CodeNode)
                WHERE a.file_path CONTAINS $project_id OR b.file_path CONTAINS $project_id
                DELETE r
                """
                
                # Delete nodes
                node_query = """
                MATCH (n:CodeNode)
                WHERE n.file_path CONTAINS $project_id
                DELETE n
                """
                
                session.run(rel_query, project_id=project_id)
                result = session.run(node_query, project_id=project_id)
                
                logger.info(f"Cleared {node_count} nodes and associated relationships for project: {project_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to clear project data for {project_id}: {e}")
            return False
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status of the graph database"""
        if not self.is_connected():
            return {
                'status': 'disconnected',
                'connected': False,
                'error': 'Not connected to Neo4j',
                'uri': self.uri,
                'schema_initialized': False
            }
        
        try:
            with self.driver.session() as session:
                # Basic connectivity and performance test
                start_time = asyncio.get_event_loop().time()
                result = session.run("MATCH (n) RETURN count(n) as total_nodes")
                total_nodes = result.single()['total_nodes']
                query_time = (asyncio.get_event_loop().time() - start_time) * 1000
                
                # Get relationship count
                rel_result = session.run("MATCH ()-[r]->() RETURN count(r) as total_relationships")
                total_relationships = rel_result.single()['total_relationships']
                
                # Test schema constraints
                schema_result = session.run("SHOW CONSTRAINTS")
                constraints = list(schema_result)
                
                # Test indexes
                index_result = session.run("SHOW INDEXES")
                indexes = list(index_result)
                
                # Calculate performance rating
                performance_rating = "excellent" if query_time < 100 else "good" if query_time < 500 else "poor"
                
                return {
                    'status': 'connected',
                    'connected': True,
                    'uri': self.uri,
                    'schema_initialized': self._schema_initialized,
                    'performance': {
                        'query_response_time_ms': round(query_time, 2),
                        'rating': performance_rating
                    },
                    'statistics': {
                        'total_nodes': total_nodes,
                        'total_relationships': total_relationships,
                        'constraints_count': len(constraints),
                        'indexes_count': len(indexes)
                    },
                    'version_info': 'Available'  # Could be enhanced to get actual version
                }
                
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'status': 'error',
                'connected': False,
                'error': str(e),
                'uri': self.uri
            }

# Factory function for easy service creation
def create_code_graph_service() -> CodeGraphService:
    """Create and initialize CodeGraphService with environment configuration"""
    try:
        from app.config.settings import settings
        return CodeGraphService(
            uri=settings.neo4j_uri,
            user=settings.neo4j_user,
            password=settings.neo4j_password
        )
    except ImportError:
        # Fallback to environment variables if settings not available
        return CodeGraphService()

# Global service instance for application use
code_graph_service = create_code_graph_service()