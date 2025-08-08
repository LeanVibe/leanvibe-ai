"""
Mock Neo4j Implementation for Testing

Provides a complete mock implementation of Neo4j functionality
using in-memory data structures for testing purposes.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Set
from unittest.mock import MagicMock
from pathlib import Path

logger = logging.getLogger(__name__)


class MockRecord:
    """Mock implementation of Neo4j Record"""

    def __init__(self, data: Dict[str, Any]):
        self._data = data

    def __getitem__(self, key: str) -> Any:
        return self._data.get(key)

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def keys(self) -> List[str]:
        return list(self._data.keys())

    def values(self) -> List[Any]:
        return list(self._data.values())

    def items(self):
        return self._data.items()

    def data(self) -> Dict[str, Any]:
        return self._data.copy()


class MockResult:
    """Mock implementation of Neo4j Result"""

    def __init__(self, records: List[Dict[str, Any]]):
        self._records = [MockRecord(record) for record in records]
        self._index = 0

    def __iter__(self):
        return iter(self._records)

    def __next__(self):
        if self._index >= len(self._records):
            raise StopIteration
        record = self._records[self._index]
        self._index += 1
        return record

    def single(self) -> Optional[MockRecord]:
        """Return single record or None"""
        if len(self._records) == 1:
            return self._records[0]
        elif len(self._records) == 0:
            return None
        else:
            raise ValueError("Result contains more than one record")

    def peek(self) -> Optional[MockRecord]:
        """Peek at first record without consuming it"""
        return self._records[0] if self._records else None

    def data(self) -> List[Dict[str, Any]]:
        """Get all records as data"""
        return [record.data() for record in self._records]


class MockTransaction:
    """Mock implementation of Neo4j Transaction"""

    def __init__(self, session: "MockSession"):
        self.session = session
        self._committed = False
        self._rolled_back = False

    def run(self, query: str, **parameters) -> MockResult:
        """Execute query in transaction context"""
        if self._committed or self._rolled_back:
            raise RuntimeError("Transaction already completed")
        
        return self.session.run(query, **parameters)

    def commit(self):
        """Commit transaction"""
        if self._rolled_back:
            raise RuntimeError("Cannot commit rolled-back transaction")
        self._committed = True
        logger.debug("Mock transaction committed")

    def rollback(self):
        """Rollback transaction"""
        if self._committed:
            raise RuntimeError("Cannot rollback committed transaction")
        self._rolled_back = True
        logger.debug("Mock transaction rolled back")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.commit()
        else:
            self.rollback()


class MockSession:
    """Mock implementation of Neo4j Session"""

    def __init__(self, driver: "MockDriver", database: str = "neo4j"):
        self.driver = driver
        self.database = database
        self._closed = False

    def run(self, query: str, **parameters) -> MockResult:
        """Execute a Cypher query"""
        if self._closed:
            raise RuntimeError("Session is closed")
        
        return self.driver._execute_query(query, parameters)

    def begin_transaction(self) -> MockTransaction:
        """Begin a new transaction"""
        if self._closed:
            raise RuntimeError("Session is closed")
        return MockTransaction(self)

    def close(self):
        """Close the session"""
        self._closed = True
        logger.debug("Mock session closed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class MockDriver:
    """Mock implementation of Neo4j Driver"""

    def __init__(self, uri: str, auth: tuple, **kwargs):
        self.uri = uri
        self.auth = auth
        self.kwargs = kwargs
        self._closed = False
        
        # In-memory graph storage
        self._nodes: Dict[str, Dict[str, Any]] = {}
        self._relationships: List[Dict[str, Any]] = []
        self._node_labels: Dict[str, Set[str]] = {}  # node_id -> set of labels
        
        logger.info(f"Mock Neo4j driver created for {uri}")

    def session(self, database: str = "neo4j") -> MockSession:
        """Create a new session"""
        if self._closed:
            raise RuntimeError("Driver is closed")
        return MockSession(self, database)

    def close(self):
        """Close the driver"""
        self._closed = True
        self.clear_all_data()
        logger.info("Mock Neo4j driver closed")

    def _execute_query(self, query: str, parameters: Dict[str, Any]) -> MockResult:
        """Execute a Cypher query on the in-memory graph"""
        query = query.strip()
        query_lower = query.lower()
        
        try:
            # Handle different types of queries
            if query_lower.startswith("return "):
                return self._handle_return_query(query, parameters)
            elif query_lower.startswith("create constraint") or query_lower.startswith("create index"):
                return self._handle_schema_query(query, parameters)
            elif query_lower.startswith("merge") or query_lower.startswith("create"):
                return self._handle_create_merge_query(query, parameters)
            elif query_lower.startswith("match"):
                return self._handle_match_query(query, parameters)
            elif query_lower.startswith("detach delete"):
                return self._handle_delete_query(query, parameters)
            else:
                logger.warning(f"Unhandled mock query type: {query}")
                return MockResult([])
                
        except Exception as e:
            logger.error(f"Mock query execution error: {e}")
            return MockResult([])

    def _handle_return_query(self, query: str, parameters: Dict[str, Any]) -> MockResult:
        """Handle RETURN queries (like connection tests)"""
        if "return 1 as test" in query.lower():
            return MockResult([{"test": 1}])
        return MockResult([])

    def _handle_schema_query(self, query: str, parameters: Dict[str, Any]) -> MockResult:
        """Handle schema creation queries"""
        logger.debug(f"Mock schema query executed: {query}")
        return MockResult([])

    def _handle_create_merge_query(self, query: str, parameters: Dict[str, Any]) -> MockResult:
        """Handle CREATE/MERGE queries"""
        # Extract node creation patterns
        if "merge" in query.lower() and ":" in query:
            # Simple node creation
            node_id = parameters.get("id")
            properties = parameters.get("properties", {})
            
            if node_id:
                self._nodes[node_id] = properties
                # Extract label from query pattern like (n:Project {id: $id})
                import re
                label_match = re.search(r'\(.*?:(\w+)', query)
                if label_match:
                    label = label_match.group(1)
                    if node_id not in self._node_labels:
                        self._node_labels[node_id] = set()
                    self._node_labels[node_id].add(label)
                
                logger.debug(f"Mock node created/merged: {node_id}")
                return MockResult([{"n": properties}])
        
        # Handle relationship creation
        if "merge" in query.lower() and "-[" in query:
            source_id = parameters.get("source_id")
            target_id = parameters.get("target_id")
            rel_properties = parameters.get("properties", {})
            
            if source_id and target_id:
                relationship = {
                    "source_id": source_id,
                    "target_id": target_id,
                    "properties": rel_properties
                }
                self._relationships.append(relationship)
                logger.debug(f"Mock relationship created: {source_id} -> {target_id}")
        
        return MockResult([])

    def _handle_match_query(self, query: str, parameters: Dict[str, Any]) -> MockResult:
        """Handle MATCH queries"""
        results = []
        
        # Handle simple ID-based matches
        if "$symbol_id" in query or "$project_id" in query:
            target_id = parameters.get("symbol_id") or parameters.get("project_id")
            if target_id and target_id in self._nodes:
                node_data = self._nodes[target_id]
                labels = list(self._node_labels.get(target_id, set()))
                
                # Mock dependency/relationship queries
                if "depends_on" in query.lower() or "calls" in query.lower():
                    # Return some mock dependencies
                    mock_deps = [
                        {
                            "id": f"dep_{i}",
                            "name": f"dependency_{i}",
                            "labels": ["Function"],
                            "relationship_type": "DEPENDS_ON",
                            "distance": i + 1
                        }
                        for i in range(3)  # Return 3 mock dependencies
                    ]
                    return MockResult(mock_deps)
                
                # Regular node match
                result = {"id": target_id, "name": node_data.get("name", target_id)}
                if labels:
                    result["labels"] = labels
                results.append(result)
        
        # Handle project file queries
        elif "contains" in query.lower() and "$project_id" in query:
            project_id = parameters.get("project_id")
            # Return mock files for the project
            mock_files = [
                {"name": "main.py", "path": "/project/main.py"},
                {"name": "utils.py", "path": "/project/utils.py"},
                {"name": "service.py", "path": "/project/service.py"}
            ]
            return MockResult(mock_files)
        
        # Handle statistics queries
        elif "count(distinct n)" in query.lower():
            return MockResult([{
                "node_count": len(self._nodes),
                "relationship_count": len(self._relationships),
                "node_labels": ["Project", "File", "Function"],
                "relationship_types": "CONTAINS"
            }])
        
        return MockResult(results)

    def _handle_delete_query(self, query: str, parameters: Dict[str, Any]) -> MockResult:
        """Handle DELETE queries"""
        project_id = parameters.get("project_id")
        if project_id:
            # Remove all nodes and relationships for the project
            nodes_to_remove = []
            for node_id, node_data in self._nodes.items():
                if node_id == project_id or node_data.get("project_id") == project_id:
                    nodes_to_remove.append(node_id)
            
            for node_id in nodes_to_remove:
                del self._nodes[node_id]
                self._node_labels.pop(node_id, None)
            
            # Remove relationships
            self._relationships = [
                rel for rel in self._relationships
                if rel.get("source_id") not in nodes_to_remove
                and rel.get("target_id") not in nodes_to_remove
            ]
            
            logger.debug(f"Mock deleted project data: {project_id}")
        
        return MockResult([])

    def clear_all_data(self):
        """Clear all in-memory data"""
        self._nodes.clear()
        self._relationships.clear()
        self._node_labels.clear()
        logger.debug("Mock graph data cleared")


class MockGraphDatabase:
    """Mock implementation of Neo4j GraphDatabase"""
    
    @staticmethod
    def driver(uri: str, auth: tuple, **kwargs) -> MockDriver:
        """Create a mock driver"""
        return MockDriver(uri, auth, **kwargs)


class MockGraphService:
    """Mock implementation of GraphService for testing"""

    def __init__(self, uri: str = "bolt://localhost:7687", username: str = "neo4j", 
                 password: str = "password", database: str = "neo4j"):
        self.uri = uri
        self.username = username
        self.password = password
        self.database = database
        self.driver = MockDriver(uri, (username, password))
        self.initialized = False

    async def initialize(self) -> bool:
        """Mock initialization"""
        try:
            logger.info(f"Mock connecting to Neo4j at {self.uri}...")
            
            # Mock connection test
            await asyncio.sleep(0.1)
            
            # Mock schema initialization
            await self._mock_initialize_schema()
            
            self.initialized = True
            logger.info("Mock Neo4j graph service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Mock Neo4j initialization failed: {e}")
            self.initialized = False
            return True  # Still return True to enable mock mode

    async def close(self):
        """Mock close"""
        if self.driver:
            self.driver.close()
            logger.info("Mock Neo4j connection closed")

    async def _mock_initialize_schema(self):
        """Mock schema initialization"""
        logger.info("Mock database schema initialized")

    async def store_project_graph(self, project_index: Any, workspace_path: str) -> bool:
        """Mock store project graph"""
        try:
            if not self.initialized:
                logger.warning("Mock graph service not initialized, skipping storage")
                return False

            logger.info(f"Mock storing project graph for: {workspace_path}")
            
            # Simulate storing nodes and relationships
            await asyncio.sleep(0.1)
            
            # Create some mock data in our in-memory store
            project_id = f"project_{hash(workspace_path)}"
            self.driver._nodes[project_id] = {
                "name": Path(workspace_path).name,
                "workspace_path": workspace_path,
                "total_files": getattr(project_index, 'supported_files', 10),
                "total_symbols": len(getattr(project_index, 'symbols', {}))
            }
            self.driver._node_labels[project_id] = {"Project"}
            
            logger.info(f"Mock project graph stored successfully for {workspace_path}")
            return True
            
        except Exception as e:
            logger.error(f"Mock failed to store project graph: {e}")
            return False

    async def find_dependencies(self, symbol_id: str) -> List[Dict[str, Any]]:
        """Mock find dependencies"""
        try:
            if not self.initialized:
                return []

            # Return mock dependencies
            dependencies = [
                {
                    "id": f"dep_1_{symbol_id}",
                    "name": "mock_dependency_1",
                    "labels": ["Function"],
                    "relationship_type": "DEPENDS_ON",
                    "distance": 1,
                },
                {
                    "id": f"dep_2_{symbol_id}",
                    "name": "mock_dependency_2", 
                    "labels": ["Class"],
                    "relationship_type": "CALLS",
                    "distance": 2,
                }
            ]
            
            return dependencies
            
        except Exception as e:
            logger.error(f"Mock error finding dependencies: {e}")
            return []

    async def analyze_impact(self, symbol_id: str) -> Dict[str, Any]:
        """Mock impact analysis"""
        try:
            if not self.initialized:
                return {
                    "target_entity": symbol_id,
                    "risk_level": "unknown"
                }

            # Mock impact analysis
            directly_affected = [f"component_{i}" for i in range(3)]
            indirectly_affected = [f"indirect_{i}" for i in range(2)]
            total_affected = len(directly_affected) + len(indirectly_affected)
            
            if total_affected < 5:
                risk_level = "low"
            elif total_affected < 15:
                risk_level = "medium"
            else:
                risk_level = "high"

            return {
                "target_entity": symbol_id,
                "directly_affected": directly_affected,
                "indirectly_affected": indirectly_affected,
                "risk_level": risk_level,
                "affected_components": {
                    "direct": len(directly_affected),
                    "indirect": len(indirectly_affected),
                },
                "recommendations": [
                    f"Mock recommendation for {risk_level} impact change",
                    f"Review {total_affected} affected components"
                ]
            }
            
        except Exception as e:
            logger.error(f"Mock error analyzing impact: {e}")
            return {"target_entity": symbol_id, "risk_level": "error"}

    async def get_architecture_patterns(self, project_id: str) -> List[Dict[str, Any]]:
        """Mock get architecture patterns"""
        try:
            if not self.initialized:
                return []

            # Return mock architecture patterns
            patterns = [
                {
                    "pattern_name": "Mock Service Layer",
                    "confidence": 0.8,
                    "components": ["service.py", "api_service.py"],
                    "description": "Mock business logic encapsulated in service classes",
                    "relationships": ["Controller -> Service", "Service -> Repository"],
                }
            ]
            
            return patterns
            
        except Exception as e:
            logger.error(f"Mock error detecting architecture patterns: {e}")
            return []

    async def get_graph_statistics(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        """Mock get graph statistics"""
        try:
            if not self.initialized:
                return {}

            return {
                "total_nodes": len(self.driver._nodes),
                "total_relationships": len(self.driver._relationships),
                "node_counts": {"Project": 1, "File": 5, "Function": 10},
                "relationship_counts": {"CONTAINS": 5, "DEPENDS_ON": 8, "CALLS": 12},
                "graph_density": 0.15,
                "average_degree": 2.3,
                "connected_components": 1,
            }
            
        except Exception as e:
            logger.error(f"Mock error getting graph statistics: {e}")
            return {}

    async def get_visualization_data(self, project_id: str, max_nodes: int = 100) -> Dict[str, Any]:
        """Mock get visualization data"""
        try:
            if not self.initialized:
                return {}

            # Mock visualization data
            nodes = [
                {"id": "project_1", "name": "Mock Project", "label": "Project"},
                {"id": "file_1", "name": "main.py", "label": "File"},
                {"id": "func_1", "name": "main_function", "label": "Function"},
            ]
            
            edges = [
                {"source": "project_1", "target": "file_1", "type": "CONTAINS"},
                {"source": "file_1", "target": "func_1", "type": "DEFINES"},
            ]
            
            return {
                "nodes": nodes,
                "edges": edges,
                "layout": "force-directed",
                "metadata": {"project_id": project_id, "node_count": len(nodes)},
            }
            
        except Exception as e:
            logger.error(f"Mock error getting visualization data: {e}")
            return {}

    async def clear_project_data(self, project_id: str) -> bool:
        """Mock clear project data"""
        try:
            if not self.initialized:
                return False

            # Clear mock data for project
            self.driver._handle_delete_query(
                "MATCH (p:Project {id: $project_id})-[:CONTAINS*0..]->(n) DETACH DELETE n",
                {"project_id": project_id}
            )
            
            logger.info(f"Mock cleared project data: {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Mock error clearing project data: {e}")
            return False


# Mock module exports
GraphDatabase = MockGraphDatabase
Driver = MockDriver
Record = MockRecord
Result = MockResult

# Global mock graph service instance
mock_graph_service = MockGraphService()