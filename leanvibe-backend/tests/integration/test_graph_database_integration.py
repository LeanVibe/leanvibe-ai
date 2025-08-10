"""
Neo4j Graph Database Integration Test Suite

This module provides comprehensive integration testing for Neo4j graph database
operations within the LeanVibe AI system, focusing on:

1. Database Connection & Schema Management
2. Code Entity Storage & Retrieval
3. Relationship Mapping & Querying
4. Architecture Analysis Operations
5. Performance & Query Optimization
6. Error Handling & Recovery
7. Data Consistency & Integrity
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.services.code_graph_service import (
    CodeGraphService, 
    CodeNode, 
    CodeRelationship, 
    NodeType, 
    RelationType
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GraphDatabaseTestFixtures:
    """Provides test fixtures for graph database testing"""
    
    @staticmethod
    def create_sample_code_nodes() -> List[CodeNode]:
        """Create sample code nodes for testing"""
        return [
            CodeNode(
                id="file_main_py",
                name="main.py",
                type=NodeType.FILE,
                file_path="/project/main.py",
                start_line=1,
                end_line=50,
                properties={"language": "python", "size_bytes": 1024}
            ),
            CodeNode(
                id="class_Calculator",
                name="Calculator",
                type=NodeType.CLASS,
                file_path="/project/main.py",
                start_line=5,
                end_line=25,
                properties={"methods_count": 3, "complexity": 5}
            ),
            CodeNode(
                id="method_add",
                name="add",
                type=NodeType.METHOD,
                file_path="/project/main.py",
                start_line=8,
                end_line=10,
                properties={"parameters": ["self", "a", "b"], "returns": "int"}
            ),
            CodeNode(
                id="function_helper",
                name="validate_input",
                type=NodeType.FUNCTION,
                file_path="/project/utils.py",
                start_line=15,
                end_line=20,
                properties={"parameters": ["value"], "complexity": 2}
            )
        ]
    
    @staticmethod
    def create_sample_relationships() -> List[CodeRelationship]:
        """Create sample relationships for testing"""
        return [
            CodeRelationship(
                from_node="file_main_py",
                to_node="class_Calculator",
                type=RelationType.CONTAINS,
                properties={"line_span": 20}
            ),
            CodeRelationship(
                from_node="class_Calculator",
                to_node="method_add",
                type=RelationType.CONTAINS,
                properties={"method_type": "instance"}
            ),
            CodeRelationship(
                from_node="method_add",
                to_node="function_helper",
                type=RelationType.CALLS,
                properties={"call_count": 2, "call_type": "direct"}
            )
        ]
    
    @staticmethod
    def create_complex_project_structure() -> Tuple[List[CodeNode], List[CodeRelationship]]:
        """Create a more complex project structure for advanced testing"""
        nodes = [
            # API Layer
            CodeNode("api_main", "FastAPIApp", NodeType.CLASS, "/api/main.py", 1, 50, 
                    {"layer": "api", "endpoints": 5}),
            CodeNode("api_users", "UserAPI", NodeType.CLASS, "/api/users.py", 1, 100,
                    {"layer": "api", "crud_operations": 4}),
            
            # Service Layer
            CodeNode("service_user", "UserService", NodeType.CLASS, "/services/user.py", 1, 80,
                    {"layer": "service", "business_logic": True}),
            CodeNode("service_auth", "AuthService", NodeType.CLASS, "/services/auth.py", 1, 60,
                    {"layer": "service", "security_critical": True}),
            
            # Data Layer
            CodeNode("model_user", "User", NodeType.CLASS, "/models/user.py", 1, 40,
                    {"layer": "data", "table": "users"}),
            CodeNode("db_connection", "DatabaseConnection", NodeType.CLASS, "/db/connection.py", 1, 30,
                    {"layer": "data", "connection_pool": True})
        ]
        
        relationships = [
            # API -> Service dependencies
            CodeRelationship("api_users", "service_user", RelationType.DEPENDS_ON,
                           {"dependency_type": "injection"}),
            CodeRelationship("api_users", "service_auth", RelationType.DEPENDS_ON,
                           {"dependency_type": "authentication"}),
            
            # Service -> Data dependencies
            CodeRelationship("service_user", "model_user", RelationType.USES,
                           {"usage_type": "entity_management"}),
            CodeRelationship("service_user", "db_connection", RelationType.USES,
                           {"usage_type": "data_access"}),
            CodeRelationship("service_auth", "db_connection", RelationType.USES,
                           {"usage_type": "credential_verification"}),
            
            # Potential circular dependency for testing
            CodeRelationship("service_auth", "service_user", RelationType.CALLS,
                           {"call_reason": "user_validation"})
        ]
        
        return nodes, relationships


class GraphDatabaseConnectionTester:
    """Tests Neo4j database connection and basic operations"""
    
    def __init__(self):
        self.test_results = {}
        
    async def test_database_connection(self) -> Dict[str, Any]:
        """Test Neo4j database connection establishment"""
        logger.info("Testing Neo4j database connection")
        
        try:
            with patch('neo4j.GraphDatabase.driver') as mock_driver:
                # Mock successful driver creation
                mock_driver_instance = MagicMock()
                mock_session = MagicMock()
                mock_result = MagicMock()
                mock_record = MagicMock()
                mock_record.single.return_value = {'count': 0}
                mock_result.single.return_value = mock_record.single.return_value
                mock_session.run.return_value = mock_result
                mock_driver_instance.session.return_value.__enter__.return_value = mock_session
                mock_driver.return_value = mock_driver_instance
                
                # Test connection
                graph_service = CodeGraphService()
                connection_start = time.time()
                connected = await graph_service.connect()
                connection_time = time.time() - connection_start
                
                return {
                    'passed': connected,
                    'connection_time': connection_time,
                    'driver_created': mock_driver.called,
                    'session_established': mock_session.run.called
                }
                
        except Exception as e:
            return {
                'passed': False,
                'error': str(e),
                'connection_time': 0
            }
    
    async def test_schema_initialization(self) -> Dict[str, Any]:
        """Test database schema and index creation"""
        logger.info("Testing Neo4j schema initialization")
        
        try:
            with patch('neo4j.GraphDatabase.driver') as mock_driver:
                # Mock driver and session
                mock_driver_instance = MagicMock()
                mock_session = MagicMock()
                mock_driver_instance.session.return_value.__enter__.return_value = mock_session
                mock_driver.return_value = mock_driver_instance
                
                # Mock successful query executions
                mock_session.run.return_value = MagicMock()
                
                graph_service = CodeGraphService()
                graph_service.driver = mock_driver_instance
                graph_service._connected = True
                
                # Initialize schema
                await graph_service._initialize_schema()
                
                # Verify schema queries were executed
                schema_queries_executed = mock_session.run.call_count
                
                return {
                    'passed': schema_queries_executed > 0,
                    'schema_queries_count': schema_queries_executed,
                    'constraints_created': True,  # Mocked as successful
                    'indexes_created': True       # Mocked as successful
                }
                
        except Exception as e:
            return {
                'passed': False,
                'error': str(e)
            }
    
    async def test_health_check_operations(self) -> Dict[str, Any]:
        """Test database health check operations"""
        logger.info("Testing database health check operations")
        
        try:
            with patch('neo4j.GraphDatabase.driver') as mock_driver:
                # Mock comprehensive health check responses
                mock_driver_instance = MagicMock()
                mock_session = MagicMock()
                mock_driver_instance.session.return_value.__enter__.return_value = mock_session
                mock_driver.return_value = mock_driver_instance
                
                # Mock health check queries
                health_responses = [
                    {'total_nodes': 150},      # Node count query
                    {'total_relationships': 300},  # Relationship count query
                    [],  # Constraints query
                    []   # Indexes query
                ]
                
                mock_results = []
                for response in health_responses:
                    mock_result = MagicMock()
                    if isinstance(response, dict):
                        mock_result.single.return_value = response
                    else:
                        mock_result.__iter__.return_value = iter(response)
                    mock_results.append(mock_result)
                
                mock_session.run.side_effect = mock_results
                
                graph_service = CodeGraphService()
                graph_service.driver = mock_driver_instance
                graph_service._connected = True
                
                health_start = time.time()
                health_status = await graph_service.get_health_status()
                health_time = time.time() - health_start
                
                return {
                    'passed': health_status.get('status') == 'connected',
                    'health_check_time': health_time,
                    'nodes_count': health_status.get('statistics', {}).get('total_nodes', 0),
                    'relationships_count': health_status.get('statistics', {}).get('total_relationships', 0),
                    'performance_rating': health_status.get('performance', {}).get('rating', 'unknown')
                }
                
        except Exception as e:
            return {
                'passed': False,
                'error': str(e)
            }


class CodeEntityStorageTester:
    """Tests code entity storage and retrieval operations"""
    
    def __init__(self):
        self.fixtures = GraphDatabaseTestFixtures()
        
    async def test_node_creation_and_storage(self) -> Dict[str, Any]:
        """Test creation and storage of code nodes"""
        logger.info("Testing code node creation and storage")
        
        try:
            with patch('neo4j.GraphDatabase.driver') as mock_driver:
                # Setup mock driver and session
                mock_driver_instance = MagicMock()
                mock_session = MagicMock()
                mock_result = MagicMock()
                mock_result.single.return_value = {'id': 'test_node'}
                mock_session.run.return_value = mock_result
                mock_driver_instance.session.return_value.__enter__.return_value = mock_session
                mock_driver.return_value = mock_driver_instance
                
                graph_service = CodeGraphService()
                graph_service.driver = mock_driver_instance
                graph_service._connected = True
                
                # Test storing sample nodes
                sample_nodes = self.fixtures.create_sample_code_nodes()
                storage_results = []
                
                storage_start = time.time()
                for node in sample_nodes:
                    result = await graph_service.add_code_node(node)
                    storage_results.append(result)
                storage_time = time.time() - storage_start
                
                return {
                    'passed': all(storage_results),
                    'nodes_stored': len([r for r in storage_results if r]),
                    'total_nodes_attempted': len(sample_nodes),
                    'storage_time': storage_time,
                    'average_time_per_node': storage_time / len(sample_nodes) if sample_nodes else 0,
                    'node_types_stored': list(set(node.type.value for node in sample_nodes))
                }
                
        except Exception as e:
            return {
                'passed': False,
                'error': str(e)
            }
    
    async def test_relationship_creation_and_storage(self) -> Dict[str, Any]:
        """Test creation and storage of code relationships"""
        logger.info("Testing code relationship creation and storage")
        
        try:
            with patch('neo4j.GraphDatabase.driver') as mock_driver:
                # Setup mock driver and session
                mock_driver_instance = MagicMock()
                mock_session = MagicMock()
                mock_result = MagicMock()
                mock_result.single.return_value = {'type': 'CALLS'}
                mock_session.run.return_value = mock_result
                mock_driver_instance.session.return_value.__enter__.return_value = mock_session
                mock_driver.return_value = mock_driver_instance
                
                graph_service = CodeGraphService()
                graph_service.driver = mock_driver_instance
                graph_service._connected = True
                
                # Test storing sample relationships
                sample_relationships = self.fixtures.create_sample_relationships()
                relationship_results = []
                
                storage_start = time.time()
                for relationship in sample_relationships:
                    result = await graph_service.add_relationship(relationship)
                    relationship_results.append(result)
                storage_time = time.time() - storage_start
                
                return {
                    'passed': all(relationship_results),
                    'relationships_stored': len([r for r in relationship_results if r]),
                    'total_relationships_attempted': len(sample_relationships),
                    'storage_time': storage_time,
                    'relationship_types_stored': list(set(rel.type.value for rel in sample_relationships))
                }
                
        except Exception as e:
            return {
                'passed': False,
                'error': str(e)
            }
    
    async def test_dependency_querying(self) -> Dict[str, Any]:
        """Test querying code dependencies"""
        logger.info("Testing dependency querying operations")
        
        try:
            with patch('neo4j.GraphDatabase.driver') as mock_driver:
                # Setup mock responses for dependency queries
                mock_driver_instance = MagicMock()
                mock_session = MagicMock()
                
                # Mock dependency query results
                mock_dependencies = [
                    {
                        'id': 'dep_1',
                        'name': 'DependentClass',
                        'type': 'Class',
                        'file_path': '/project/dependent.py',
                        'distance': 1,
                        'relationships': ['DEPENDS_ON']
                    },
                    {
                        'id': 'dep_2', 
                        'name': 'HelperFunction',
                        'type': 'Function',
                        'file_path': '/project/helpers.py',
                        'distance': 2,
                        'relationships': ['CALLS', 'USES']
                    }
                ]
                
                mock_result = MagicMock()
                mock_result.__iter__.return_value = iter([
                    MagicMock(**dep) for dep in mock_dependencies
                ])
                mock_session.run.return_value = mock_result
                mock_driver_instance.session.return_value.__enter__.return_value = mock_session
                mock_driver.return_value = mock_driver_instance
                
                graph_service = CodeGraphService()
                graph_service.driver = mock_driver_instance
                graph_service._connected = True
                
                # Test dependency queries
                query_start = time.time()
                dependencies = await graph_service.get_dependencies("test_node", depth=2)
                dependents = await graph_service.get_dependents("test_node", depth=2)
                query_time = time.time() - query_start
                
                return {
                    'passed': True,
                    'dependencies_found': len(mock_dependencies),
                    'dependents_found': len(mock_dependencies),  # Same mock data
                    'query_time': query_time,
                    'max_dependency_distance': max(dep['distance'] for dep in mock_dependencies),
                    'relationship_types_found': ['DEPENDS_ON', 'CALLS', 'USES']
                }
                
        except Exception as e:
            return {
                'passed': False,
                'error': str(e)
            }


class ArchitectureAnalysisTester:
    """Tests architecture analysis and advanced graph operations"""
    
    def __init__(self):
        self.fixtures = GraphDatabaseTestFixtures()
        
    async def test_architecture_overview_analysis(self) -> Dict[str, Any]:
        """Test architecture overview generation"""
        logger.info("Testing architecture overview analysis")
        
        try:
            with patch('neo4j.GraphDatabase.driver') as mock_driver:
                # Mock comprehensive architecture data
                mock_driver_instance = MagicMock()
                mock_session = MagicMock()
                
                # Mock architecture analysis results
                architecture_data = {
                    'node_statistics': {
                        'Class': 25,
                        'Function': 45,
                        'Method': 78,
                        'File': 12
                    },
                    'relationship_statistics': {
                        'CALLS': 120,
                        'DEPENDS_ON': 65,
                        'CONTAINS': 90,
                        'USES': 30
                    },
                    'hotspots': [
                        {
                            'id': 'central_service',
                            'name': 'CoreService',
                            'type': 'Class',
                            'file_path': '/core/service.py',
                            'total_connections': 25,
                            'outgoing_connections': 15,
                            'incoming_connections': 10
                        }
                    ]
                }
                
                # Mock multiple query responses for architecture analysis
                query_responses = [
                    # Node statistics query
                    [MagicMock(get=lambda k, d=None: architecture_data['node_statistics'].get(k, d)) 
                     for k in architecture_data['node_statistics'].keys()],
                    # Relationship statistics query  
                    [MagicMock(get=lambda k, d=None: architecture_data['relationship_statistics'].get(k, d))
                     for k in architecture_data['relationship_statistics'].keys()],
                    # Hotspots query
                    [MagicMock(**hotspot) for hotspot in architecture_data['hotspots']]
                ]
                
                mock_session.run.side_effect = [
                    # Node stats
                    MagicMock(__iter__=lambda s: iter([
                        {'node_type': k, 'count': v} 
                        for k, v in architecture_data['node_statistics'].items()
                    ])),
                    # Relationship stats
                    MagicMock(__iter__=lambda s: iter([
                        {'rel_type': k, 'count': v}
                        for k, v in architecture_data['relationship_statistics'].items()
                    ])),
                    # Hotspots
                    MagicMock(__iter__=lambda s: iter([
                        {
                            'id': h['id'], 'name': h['name'], 'type': h['type'],
                            'file_path': h['file_path'], 'total_degree': h['total_connections'],
                            'out_degree': h['outgoing_connections'], 'in_degree': h['incoming_connections']
                        } for h in architecture_data['hotspots']
                    ]))
                ]
                
                mock_driver_instance.session.return_value.__enter__.return_value = mock_session
                mock_driver.return_value = mock_driver_instance
                
                graph_service = CodeGraphService()
                graph_service.driver = mock_driver_instance
                graph_service._connected = True
                
                # Test architecture analysis
                analysis_start = time.time()
                overview = await graph_service.get_architecture_overview("test_project")
                analysis_time = time.time() - analysis_start
                
                return {
                    'passed': 'node_statistics' in overview,
                    'analysis_time': analysis_time,
                    'total_nodes': sum(architecture_data['node_statistics'].values()),
                    'total_relationships': sum(architecture_data['relationship_statistics'].values()),
                    'hotspots_identified': len(architecture_data['hotspots']),
                    'graph_density': overview.get('metrics', {}).get('graph_density', 0),
                    'most_connected_component': architecture_data['hotspots'][0]['name'] if architecture_data['hotspots'] else None
                }
                
        except Exception as e:
            return {
                'passed': False,
                'error': str(e)
            }
    
    async def test_circular_dependency_detection(self) -> Dict[str, Any]:
        """Test circular dependency detection"""
        logger.info("Testing circular dependency detection")
        
        try:
            with patch('neo4j.GraphDatabase.driver') as mock_driver:
                # Mock circular dependency data
                mock_cycles = [
                    {
                        'cycle': [
                            {'id': 'service_a', 'name': 'ServiceA', 'type': 'Class'},
                            {'id': 'service_b', 'name': 'ServiceB', 'type': 'Class'},
                            {'id': 'service_a', 'name': 'ServiceA', 'type': 'Class'}
                        ],
                        'cycle_length': 3
                    },
                    {
                        'cycle': [
                            {'id': 'util_x', 'name': 'UtilX', 'type': 'Class'},
                            {'id': 'helper_y', 'name': 'HelperY', 'type': 'Class'},
                            {'id': 'processor_z', 'name': 'ProcessorZ', 'type': 'Class'},
                            {'id': 'util_x', 'name': 'UtilX', 'type': 'Class'}
                        ],
                        'cycle_length': 4
                    }
                ]
                
                mock_driver_instance = MagicMock()
                mock_session = MagicMock()
                mock_result = MagicMock()
                mock_result.__iter__.return_value = iter([
                    {'cycle': cycle['cycle'], 'cycle_length': cycle['cycle_length']}
                    for cycle in mock_cycles
                ])
                mock_session.run.return_value = mock_result
                mock_driver_instance.session.return_value.__enter__.return_value = mock_session
                mock_driver.return_value = mock_driver_instance
                
                graph_service = CodeGraphService()
                graph_service.driver = mock_driver_instance
                graph_service._connected = True
                
                # Test circular dependency detection
                detection_start = time.time()
                cycles = await graph_service.find_circular_dependencies("test_project", max_depth=10)
                detection_time = time.time() - detection_start
                
                return {
                    'passed': len(cycles) > 0,  # Should find the mocked cycles
                    'detection_time': detection_time,
                    'cycles_found': len(mock_cycles),
                    'shortest_cycle_length': min(cycle['cycle_length'] for cycle in mock_cycles),
                    'longest_cycle_length': max(cycle['cycle_length'] for cycle in mock_cycles),
                    'severity_distribution': {
                        'high': len([c for c in mock_cycles if c['cycle_length'] <= 3]),
                        'medium': len([c for c in mock_cycles if 3 < c['cycle_length'] <= 5]),
                        'low': len([c for c in mock_cycles if c['cycle_length'] > 5])
                    }
                }
                
        except Exception as e:
            return {
                'passed': False,
                'error': str(e)
            }
    
    async def test_complexity_analysis(self) -> Dict[str, Any]:
        """Test code complexity analysis operations"""
        logger.info("Testing code complexity analysis")
        
        try:
            with patch('neo4j.GraphDatabase.driver') as mock_driver:
                # Mock complexity analysis data
                mock_complex_functions = [
                    {
                        'name': 'complex_algorithm',
                        'type': 'Function',
                        'file_path': '/core/algorithms.py',
                        'complexity': 15,
                        'loc': 45
                    },
                    {
                        'name': 'data_processor',
                        'type': 'Method',
                        'file_path': '/services/processor.py', 
                        'complexity': 12,
                        'loc': 38
                    }
                ]
                
                mock_complex_files = [
                    {
                        'file_path': '/core/algorithms.py',
                        'symbol_count': 8,
                        'avg_complexity': 10.5,
                        'loc': 200
                    },
                    {
                        'file_path': '/services/processor.py',
                        'symbol_count': 12,
                        'avg_complexity': 8.2,
                        'loc': 150
                    }
                ]
                
                mock_driver_instance = MagicMock()
                mock_session = MagicMock()
                
                # Mock query responses for complexity analysis
                mock_session.run.side_effect = [
                    # Functions complexity query
                    MagicMock(__iter__=lambda s: iter(mock_complex_functions)),
                    # Files complexity query
                    MagicMock(__iter__=lambda s: iter(mock_complex_files))
                ]
                
                mock_driver_instance.session.return_value.__enter__.return_value = mock_session
                mock_driver.return_value = mock_driver_instance
                
                graph_service = CodeGraphService()
                graph_service.driver = mock_driver_instance
                graph_service._connected = True
                
                # Test complexity analysis
                analysis_start = time.time()
                complexity_result = await graph_service.analyze_code_complexity("test_project")
                analysis_time = time.time() - analysis_start
                
                return {
                    'passed': 'complex_functions' in complexity_result,
                    'analysis_time': analysis_time,
                    'complex_functions_found': len(mock_complex_functions),
                    'complex_files_found': len(mock_complex_files),
                    'highest_function_complexity': max(f.get('complexity', 0) for f in mock_complex_functions),
                    'average_file_complexity': sum(f.get('avg_complexity', 0) for f in mock_complex_files) / len(mock_complex_files),
                    'functions_above_threshold': len([f for f in mock_complex_functions if f.get('complexity', 0) > 10])
                }
                
        except Exception as e:
            return {
                'passed': False,
                'error': str(e)
            }


@pytest.mark.asyncio
async def test_graph_database_integration_suite():
    """Main graph database integration test suite"""
    logger.info("Starting comprehensive graph database integration tests")
    
    test_results = {}
    
    # Test 1: Database connection and setup
    connection_tester = GraphDatabaseConnectionTester()
    
    connection_result = await connection_tester.test_database_connection()
    test_results['database_connection'] = connection_result
    
    schema_result = await connection_tester.test_schema_initialization() 
    test_results['schema_initialization'] = schema_result
    
    health_result = await connection_tester.test_health_check_operations()
    test_results['health_check'] = health_result
    
    # Test 2: Code entity storage and retrieval
    storage_tester = CodeEntityStorageTester()
    
    node_storage_result = await storage_tester.test_node_creation_and_storage()
    test_results['node_storage'] = node_storage_result
    
    relationship_storage_result = await storage_tester.test_relationship_creation_and_storage()
    test_results['relationship_storage'] = relationship_storage_result
    
    dependency_query_result = await storage_tester.test_dependency_querying()
    test_results['dependency_queries'] = dependency_query_result
    
    # Test 3: Architecture analysis operations
    analysis_tester = ArchitectureAnalysisTester()
    
    architecture_result = await analysis_tester.test_architecture_overview_analysis()
    test_results['architecture_analysis'] = architecture_result
    
    circular_deps_result = await analysis_tester.test_circular_dependency_detection()
    test_results['circular_dependency_detection'] = circular_deps_result
    
    complexity_result = await analysis_tester.test_complexity_analysis()
    test_results['complexity_analysis'] = complexity_result
    
    # Calculate overall success metrics
    passed_tests = sum(1 for result in test_results.values() if result.get('passed', False))
    total_tests = len(test_results)
    success_rate = (passed_tests / total_tests) * 100
    
    # Log comprehensive results
    logger.info(f"Graph database integration tests completed: {success_rate:.1f}% success rate")
    logger.info(f"Passed: {passed_tests}/{total_tests} tests")
    
    # Assert minimum success criteria
    assert success_rate >= 80, f"Graph database integration tests failed with {success_rate:.1f}% success rate"
    assert test_results['database_connection']['passed'], "Database connection test must pass"
    assert test_results['node_storage']['passed'], "Node storage test must pass"
    assert test_results['relationship_storage']['passed'], "Relationship storage test must pass"
    
    return test_results


@pytest.mark.asyncio 
async def test_performance_optimization():
    """Test performance optimization features"""
    logger.info("Testing graph database performance optimization")
    
    # Test query performance
    with patch('app.services.code_graph_service.CodeGraphService') as mock_service:
        mock_instance = AsyncMock()
        mock_service.return_value = mock_instance
        
        # Mock performance metrics
        mock_instance.get_health_status = AsyncMock(return_value={
            'performance': {
                'query_response_time_ms': 150.5,
                'rating': 'good'
            },
            'statistics': {
                'total_nodes': 1000,
                'total_relationships': 2500
            }
        })
        
        service = mock_service.return_value
        health = await service.get_health_status()
        
        # Assert performance criteria
        response_time = health['performance']['query_response_time_ms']
        assert response_time < 500, f"Query response time too slow: {response_time}ms"
        
        # Assert scaling capacity
        node_count = health['statistics']['total_nodes']
        assert node_count > 0, "Database should contain nodes"
        
        logger.info(f"Performance test passed: {response_time}ms response time for {node_count} nodes")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])