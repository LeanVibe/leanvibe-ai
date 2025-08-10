"""
Comprehensive tests for CodeGraphService

Tests the enhanced Neo4j graph database service for code relationships,
including connection management, node/relationship operations, and analysis features.
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from app.services.code_graph_service import (
    CodeGraphService, 
    CodeNode, 
    CodeRelationship, 
    NodeType, 
    RelationType,
    create_code_graph_service
)

class TestCodeGraphServiceCore:
    """Test core functionality of CodeGraphService"""

    @pytest.fixture
    def mock_neo4j_driver(self):
        """Mock Neo4j driver with realistic session behavior"""
        with patch('app.services.code_graph_service.GraphDatabase.driver') as mock_driver:
            # Create mock session and transaction
            mock_session = Mock()
            mock_transaction = Mock()
            mock_result = Mock()
            
            # Configure return values
            mock_result.single.return_value = {'count': 0}
            mock_transaction.run.return_value = mock_result
            mock_session.run.return_value = mock_result
            mock_session.begin_transaction.return_value.__enter__ = Mock(return_value=mock_transaction)
            mock_session.begin_transaction.return_value.__exit__ = Mock(return_value=None)
            mock_driver.return_value.session.return_value.__enter__ = Mock(return_value=mock_session)
            mock_driver.return_value.session.return_value.__exit__ = Mock(return_value=None)
            
            yield mock_driver

    @pytest.fixture
    def graph_service(self, mock_neo4j_driver):
        """Create CodeGraphService with mocked Neo4j"""
        service = CodeGraphService("bolt://localhost:7687", "neo4j", "test")
        return service

    @pytest.mark.asyncio
    async def test_connection_success(self, graph_service, mock_neo4j_driver):
        """Test successful Neo4j connection"""
        # Arrange
        mock_neo4j_driver.return_value.session.return_value.__enter__.return_value.run.return_value.single.return_value = {'count': 0}
        
        # Act
        result = await graph_service.connect()
        
        # Assert
        assert result == True
        assert graph_service.is_connected() == True
        assert graph_service._schema_initialized == True

    @pytest.mark.asyncio 
    async def test_connection_failure_with_retry(self, graph_service):
        """Test connection failure with retry logic"""
        # Mock connection failure
        with patch('app.services.code_graph_service.GraphDatabase.driver') as mock_driver:
            mock_driver.side_effect = Exception("Connection failed")
            
            # Act
            result = await graph_service.connect()
            
            # Assert
            assert result == False
            assert graph_service.is_connected() == False

    @pytest.mark.asyncio
    async def test_add_code_node_success(self, graph_service, mock_neo4j_driver):
        """Test successful code node creation"""
        # Arrange
        await graph_service.connect()
        
        node = CodeNode(
            id="test_node_123",
            name="TestClass",
            type=NodeType.CLASS,
            file_path="/test/file.py",
            start_line=1,
            end_line=10,
            properties={"test": "value", "complexity": 5}
        )
        
        # Mock successful insertion
        mock_session = mock_neo4j_driver.return_value.session.return_value.__enter__.return_value
        mock_session.run.return_value.single.return_value = {"n": {"id": "test_node_123"}}
        
        # Act
        result = await graph_service.add_code_node(node)
        
        # Assert
        assert result == True
        mock_session.run.assert_called()

    @pytest.mark.asyncio
    async def test_add_code_node_disconnected(self, graph_service):
        """Test node creation when disconnected from Neo4j"""
        # Ensure service is not connected
        assert not graph_service.is_connected()
        
        node = CodeNode(
            id="test_node",
            name="TestClass", 
            type=NodeType.CLASS,
            file_path="/test/file.py",
            start_line=1,
            end_line=10,
            properties={}
        )
        
        # Act
        result = await graph_service.add_code_node(node)
        
        # Assert
        assert result == False

    @pytest.mark.asyncio
    async def test_add_relationship_success(self, graph_service, mock_neo4j_driver):
        """Test successful relationship creation"""
        # Arrange
        await graph_service.connect()
        
        relationship = CodeRelationship(
            from_node="node1_id",
            to_node="node2_id", 
            type=RelationType.CALLS,
            properties={"call_count": 5, "context": "test"}
        )
        
        # Mock successful relationship creation
        mock_session = mock_neo4j_driver.return_value.session.return_value.__enter__.return_value
        mock_session.run.return_value.single.return_value = {"r": {"type": "CALLS"}}
        
        # Act
        result = await graph_service.add_relationship(relationship)
        
        # Assert
        assert result == True
        mock_session.run.assert_called()

    @pytest.mark.asyncio
    async def test_get_dependencies(self, graph_service, mock_neo4j_driver):
        """Test dependency retrieval"""
        # Arrange
        await graph_service.connect()
        
        # Mock dependency query results
        mock_session = mock_neo4j_driver.return_value.session.return_value.__enter__.return_value
        mock_session.run.return_value = [
            {
                'id': 'dep1',
                'name': 'Dependency1',
                'type': 'Function',
                'file_path': '/test/dep.py',
                'distance': 1,
                'relationships': ['CALLS']
            },
            {
                'id': 'dep2', 
                'name': 'Dependency2',
                'type': 'Class',
                'file_path': '/test/dep2.py',
                'distance': 2,
                'relationships': ['DEPENDS_ON', 'CALLS']
            }
        ]
        
        # Act
        deps = await graph_service.get_dependencies("test_node", depth=2)
        
        # Assert
        assert len(deps) == 2
        assert deps[0]['id'] == 'dep1'
        assert deps[0]['name'] == 'Dependency1'
        assert deps[1]['distance'] == 2

    @pytest.mark.asyncio
    async def test_get_dependents(self, graph_service, mock_neo4j_driver):
        """Test dependent retrieval"""
        # Arrange
        await graph_service.connect()
        
        # Mock dependents query results
        mock_session = mock_neo4j_driver.return_value.session.return_value.__enter__.return_value
        mock_session.run.return_value = [
            {
                'id': 'dependent1',
                'name': 'DependentClass',
                'type': 'Class',
                'file_path': '/test/dependent.py',
                'distance': 1,
                'relationships': ['IMPORTS']
            }
        ]
        
        # Act
        dependents = await graph_service.get_dependents("test_node", depth=2)
        
        # Assert
        assert len(dependents) == 1
        assert dependents[0]['id'] == 'dependent1'
        assert dependents[0]['type'] == 'Class'

class TestCodeGraphServiceAnalysis:
    """Test analysis features of CodeGraphService"""

    @pytest.fixture
    def connected_graph_service(self, mock_neo4j_driver):
        """Create connected graph service for analysis tests"""
        service = CodeGraphService()
        # Mock successful connection
        service._connected = True
        service.driver = mock_neo4j_driver.return_value
        return service

    @pytest.mark.asyncio
    async def test_architecture_overview(self, connected_graph_service, mock_neo4j_driver):
        """Test architecture overview generation"""
        # Mock multiple query results
        mock_session = mock_neo4j_driver.return_value.session.return_value.__enter__.return_value
        
        # Mock node statistics query
        node_stats_result = [
            {'node_type': 'Function', 'count': 45},
            {'node_type': 'Class', 'count': 12},
            {'node_type': 'File', 'count': 8}
        ]
        
        # Mock relationship statistics query  
        rel_stats_result = [
            {'rel_type': 'CALLS', 'count': 123},
            {'rel_type': 'IMPORTS', 'count': 34},
            {'rel_type': 'CONTAINS', 'count': 67}
        ]
        
        # Mock hotspots query
        hotspots_result = [
            {
                'id': 'class:main.py:DatabaseService:10',
                'name': 'DatabaseService',
                'type': 'Class', 
                'file_path': 'main.py',
                'total_degree': 15,
                'out_degree': 8,
                'in_degree': 7
            },
            {
                'id': 'function:utils.py:helper_func:5',
                'name': 'helper_func',
                'type': 'Function',
                'file_path': 'utils.py', 
                'total_degree': 12,
                'out_degree': 3,
                'in_degree': 9
            }
        ]
        
        # Configure mock to return different results for different queries
        mock_session.run.side_effect = [
            node_stats_result,
            rel_stats_result,
            hotspots_result
        ]
        
        # Act
        overview = await connected_graph_service.get_architecture_overview("test_project")
        
        # Assert
        assert 'node_statistics' in overview
        assert 'relationship_statistics' in overview
        assert 'hotspots' in overview
        assert 'metrics' in overview
        
        assert overview['node_statistics']['Function'] == 45
        assert overview['relationship_statistics']['CALLS'] == 123
        assert len(overview['hotspots']) == 2
        assert overview['metrics']['total_nodes'] == 65  # 45 + 12 + 8

    @pytest.mark.asyncio
    async def test_find_circular_dependencies(self, connected_graph_service, mock_neo4j_driver):
        """Test circular dependency detection"""
        # Mock circular dependency query results
        mock_session = mock_neo4j_driver.return_value.session.return_value.__enter__.return_value
        mock_session.run.return_value = [
            {
                'cycle': [
                    {'id': 'file:a.py', 'name': 'a.py', 'type': 'File'},
                    {'id': 'file:b.py', 'name': 'b.py', 'type': 'File'},
                    {'id': 'file:c.py', 'name': 'c.py', 'type': 'File'},
                    {'id': 'file:a.py', 'name': 'a.py', 'type': 'File'}
                ],
                'cycle_length': 3
            }
        ]
        
        # Act
        cycles = await connected_graph_service.find_circular_dependencies("test_project")
        
        # Assert
        assert len(cycles) == 1
        assert cycles[0]['length'] == 3
        assert cycles[0]['severity'] == 'high'
        assert len(cycles[0]['cycle']) == 4

    @pytest.mark.asyncio
    async def test_analyze_code_complexity(self, connected_graph_service, mock_neo4j_driver):
        """Test code complexity analysis"""
        # Mock complexity query results
        mock_session = mock_neo4j_driver.return_value.session.return_value.__enter__.return_value
        
        # Mock function complexity results
        function_complexity_result = [
            {
                'name': 'complex_function',
                'type': 'Function',
                'file_path': 'main.py',
                'complexity': 15,
                'loc': 45
            },
            {
                'name': 'simple_function',
                'type': 'Method', 
                'file_path': 'utils.py',
                'complexity': 3,
                'loc': 12
            }
        ]
        
        # Mock file complexity results
        file_complexity_result = [
            {
                'file_path': 'main.py',
                'symbol_count': 8,
                'avg_complexity': 9.5,
                'loc': 200
            }
        ]
        
        # Configure mock to return different results
        mock_session.run.side_effect = [
            function_complexity_result,
            file_complexity_result
        ]
        
        # Act
        analysis = await connected_graph_service.analyze_code_complexity("test_project")
        
        # Assert
        assert 'complex_functions' in analysis
        assert 'complex_files' in analysis
        assert 'summary' in analysis
        
        assert len(analysis['complex_functions']) == 2
        assert analysis['complex_functions'][0]['complexity'] == 15
        assert analysis['summary']['total_functions_analyzed'] == 2
        assert analysis['summary']['functions_above_threshold'] == 1

    @pytest.mark.asyncio
    async def test_clear_project_data(self, connected_graph_service, mock_neo4j_driver):
        """Test project data clearing"""
        # Mock count and delete queries
        mock_session = mock_neo4j_driver.return_value.session.return_value.__enter__.return_value
        
        # Mock count query
        count_result = Mock()
        count_result.single.return_value = {'node_count': 25}
        
        # Configure mock responses
        mock_session.run.side_effect = [count_result, None, None]
        
        # Act  
        result = await connected_graph_service.clear_project_data("test_project")
        
        # Assert
        assert result == True
        assert mock_session.run.call_count == 3  # Count + relationships + nodes

class TestCodeGraphServiceHealth:
    """Test health monitoring and connection management"""

    @pytest.mark.asyncio
    async def test_health_status_connected(self, mock_neo4j_driver):
        """Test health status when connected"""
        # Arrange
        service = CodeGraphService()
        service._connected = True
        service.driver = mock_neo4j_driver.return_value
        
        mock_session = mock_neo4j_driver.return_value.session.return_value.__enter__.return_value
        
        # Mock health queries
        node_result = Mock()
        node_result.single.return_value = {'total_nodes': 150}
        
        rel_result = Mock()  
        rel_result.single.return_value = {'total_relationships': 300}
        
        constraints_result = [{'constraint': 'unique_node'}, {'constraint': 'unique_file'}]
        indexes_result = [{'index': 'node_name'}, {'index': 'file_path'}]
        
        mock_session.run.side_effect = [
            node_result,
            rel_result, 
            constraints_result,
            indexes_result
        ]
        
        # Act
        status = await service.get_health_status()
        
        # Assert
        assert status['status'] == 'connected'
        assert status['connected'] == True
        assert status['statistics']['total_nodes'] == 150
        assert status['statistics']['total_relationships'] == 300
        assert 'performance' in status
        assert status['performance']['rating'] in ['excellent', 'good', 'poor']

    @pytest.mark.asyncio
    async def test_health_status_disconnected(self):
        """Test health status when disconnected"""
        # Arrange
        service = CodeGraphService()
        
        # Act - service not connected
        status = await service.get_health_status()
        
        # Assert
        assert status['status'] == 'disconnected'
        assert status['connected'] == False
        assert 'error' in status

    @pytest.mark.asyncio
    async def test_health_status_error(self, mock_neo4j_driver):
        """Test health status when query fails"""
        # Arrange
        service = CodeGraphService()
        service._connected = True
        service.driver = mock_neo4j_driver.return_value
        
        mock_session = mock_neo4j_driver.return_value.session.return_value.__enter__.return_value
        mock_session.run.side_effect = Exception("Query failed")
        
        # Act
        status = await service.get_health_status()
        
        # Assert
        assert status['status'] == 'error'
        assert status['connected'] == False
        assert 'Query failed' in status['error']

class TestFactoryFunction:
    """Test factory function and service creation"""

    def test_create_code_graph_service(self):
        """Test factory function creates service correctly"""
        service = create_code_graph_service()
        
        assert isinstance(service, CodeGraphService)
        assert service.uri == "bolt://localhost:7687"  # Default
        assert service.user == "neo4j"  # Default
        
    @patch.dict('os.environ', {
        'NEO4J_URI': 'bolt://custom:7687',
        'NEO4J_USER': 'custom_user', 
        'NEO4J_PASSWORD': 'custom_pass'
    })
    def test_create_code_graph_service_with_env(self):
        """Test factory function uses environment variables"""
        service = create_code_graph_service()
        
        assert service.uri == 'bolt://custom:7687'
        assert service.user == 'custom_user'
        assert service.password == 'custom_pass'

class TestEdgeCases:
    """Test edge cases and error conditions"""

    @pytest.mark.asyncio
    async def test_add_node_with_none_properties(self, mock_neo4j_driver):
        """Test adding node with None properties"""
        service = CodeGraphService()
        service._connected = True
        service.driver = mock_neo4j_driver.return_value
        
        node = CodeNode(
            id="test",
            name="Test",
            type=NodeType.FUNCTION,
            file_path="test.py",
            start_line=1,
            end_line=5,
            properties=None  # Test None properties
        )
        
        mock_session = mock_neo4j_driver.return_value.session.return_value.__enter__.return_value
        mock_session.run.return_value.single.return_value = {"n": {"id": "test"}}
        
        result = await service.add_node(node)
        assert result == True

    @pytest.mark.asyncio 
    async def test_get_dependencies_empty_result(self, mock_neo4j_driver):
        """Test dependency query with empty results"""
        service = CodeGraphService()
        service._connected = True
        service.driver = mock_neo4j_driver.return_value
        
        mock_session = mock_neo4j_driver.return_value.session.return_value.__enter__.return_value
        mock_session.run.return_value = []  # Empty result
        
        deps = await service.get_dependencies("nonexistent_node")
        assert deps == []

    @pytest.mark.asyncio
    async def test_architecture_overview_with_none_project_id(self, mock_neo4j_driver):
        """Test architecture overview with None project_id"""
        service = CodeGraphService()  
        service._connected = True
        service.driver = mock_neo4j_driver.return_value
        
        mock_session = mock_neo4j_driver.return_value.session.return_value.__enter__.return_value
        mock_session.run.side_effect = [[], [], []]  # Empty results
        
        overview = await service.get_architecture_overview(None)
        
        assert overview['project_id'] is None
        assert overview['metrics']['total_nodes'] == 0

if __name__ == "__main__":
    # Run a quick smoke test
    pytest.main([__file__, "-v"])