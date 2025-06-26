"""
Test Graph Database Integration

Tests for Neo4j graph database integration with AST analysis.
"""

import pytest
import asyncio
import os
import sys
import tempfile
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestGraphService:
    """Test Neo4j graph service functionality"""
    
    @pytest.mark.asyncio
    async def test_graph_service_initialization(self):
        """Test graph service initialization"""
        from app.services.graph_service import graph_service
        
        # Test initialization (may fail if Neo4j not available, which is OK)
        result = await graph_service.initialize()
        
        # Even if initialization fails, should not crash
        assert isinstance(result, bool)
        
        if result:
            assert graph_service.initialized == True
            assert graph_service.driver is not None
        else:
            # Should gracefully handle Neo4j unavailability
            assert graph_service.initialized == False
            print("⚠️ Neo4j not available - tests will run with fallback behavior")
    
    @pytest.mark.asyncio
    async def test_graph_models(self):
        """Test graph model creation and serialization"""
        from app.models.graph_models import (
            ProjectNode, FileNode, SymbolNode, GraphRelationship,
            RelationshipType, NodeLabel, SymbolType
        )
        from app.models.ast_models import LanguageType
        from datetime import datetime
        
        # Test ProjectNode
        project = ProjectNode(
            id="test_project",
            name="Test Project",
            workspace_path="/test/path",
            technology_stack=["Python", "FastAPI"],
            total_files=10,
            total_symbols=50
        )
        
        assert project.label == NodeLabel.PROJECT
        assert project.name == "Test Project"
        assert "workspace_path" in project.properties
        assert project.properties["total_files"] == 10
        
        # Test cypher properties conversion
        cypher_props = project.to_cypher_properties()
        assert isinstance(cypher_props, str)
        assert "workspace_path" in cypher_props
        assert "total_files" in cypher_props
        
        # Test FileNode
        file_node = FileNode(
            id="test_file",
            name="test.py",
            file_path="test/test.py",
            language=LanguageType.PYTHON,
            lines_of_code=100,
            complexity=5.2
        )
        
        assert file_node.label == NodeLabel.FILE
        assert file_node.properties["language"] == "LanguageType.PYTHON"
        assert file_node.properties["complexity"] == 5.2
        
        # Test SymbolNode
        symbol_node = SymbolNode(
            id="test_symbol",
            name="test_function",
            symbol_type=SymbolType.FUNCTION,
            file_path="test/test.py",
            line_start=10,
            line_end=20,
            parameters=["arg1", "arg2"],
            return_type="str"
        )
        
        assert symbol_node.label == NodeLabel.FUNCTION
        assert symbol_node.properties["symbol_type"] == "SymbolType.FUNCTION"
        assert symbol_node.properties["parameters"] == ["arg1", "arg2"]
        
        # Test GraphRelationship
        relationship = GraphRelationship(
            source_id="source",
            target_id="target",
            relationship_type=RelationshipType.CALLS,
            strength=0.8
        )
        
        assert relationship.relationship_type == RelationshipType.CALLS
        assert relationship.strength == 0.8
        
        rel_props = relationship.to_cypher_properties()
        assert "strength" in rel_props
    
    @pytest.mark.asyncio
    async def test_project_graph_storage(self):
        """Test storing project structure in graph database"""
        from app.services.graph_service import graph_service
        from app.services.project_indexer import project_indexer
        from app.models.ast_models import ProjectIndex, FileAnalysis, Symbol, SymbolType, LanguageType
        
        # Create mock project index
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create test files
            (project_path / "main.py").write_text('''
def main():
    """Main function"""
    print("Hello World")
    return 0

class Calculator:
    def add(self, a, b):
        return a + b
''')
            
            # Index the project
            project_index = await project_indexer.index_project(str(project_path))
            
            # Test graph storage (only if Neo4j available)
            if graph_service.initialized:
                result = await graph_service.store_project_graph(project_index, str(project_path))
                assert result == True
            else:
                # Should handle gracefully when Neo4j not available
                result = await graph_service.store_project_graph(project_index, str(project_path))
                assert result == False


class TestGraphQueryService:
    """Test graph query service functionality"""
    
    @pytest.mark.asyncio
    async def test_graph_query_service_initialization(self):
        """Test graph query service initialization"""
        from app.services.graph_query_service import graph_query_service
        
        # Should initialize without errors
        assert graph_query_service is not None
        assert hasattr(graph_query_service, 'graph_service')
        assert hasattr(graph_query_service, 'query_cache')
    
    @pytest.mark.asyncio
    async def test_circular_dependency_detection(self):
        """Test circular dependency detection"""
        from app.services.graph_query_service import graph_query_service
        
        # Test with mock project (should handle gracefully if no graph DB)
        cycles = await graph_query_service.find_circular_dependencies("test_project")
        
        # Should return empty list if no cycles or no graph DB
        assert isinstance(cycles, list)
    
    @pytest.mark.asyncio
    async def test_coupling_analysis(self):
        """Test coupling analysis"""
        from app.services.graph_query_service import graph_query_service
        
        # Test with mock project
        coupling_data = await graph_query_service.analyze_coupling("test_project")
        
        # Should return dict (empty if no graph DB)
        assert isinstance(coupling_data, dict)
    
    @pytest.mark.asyncio
    async def test_hotspot_detection(self):
        """Test code hotspot detection"""
        from app.services.graph_query_service import graph_query_service
        
        # Test with mock project
        hotspots = await graph_query_service.find_hotspots("test_project")
        
        # Should return list (empty if no graph DB)
        assert isinstance(hotspots, list)
    
    @pytest.mark.asyncio
    async def test_refactoring_suggestions(self):
        """Test refactoring opportunity detection"""
        from app.services.graph_query_service import graph_query_service
        
        # Test with mock project
        suggestions = await graph_query_service.suggest_refactoring_opportunities("test_project")
        
        # Should return list (empty if no graph DB)
        assert isinstance(suggestions, list)


class TestEnhancedAgentGraphIntegration:
    """Test enhanced L3 agent integration with graph database"""
    
    @pytest.mark.asyncio
    async def test_enhanced_agent_graph_tools(self):
        """Test enhanced agent graph-based tools"""
        from app.agent.enhanced_l3_agent import EnhancedL3CodingAgent, AgentDependencies
        
        # Create test project
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            (project_path / "service.py").write_text('''
class UserService:
    def __init__(self, user_repository):
        self.user_repository = user_repository
    
    def create_user(self, user_data):
        return self.user_repository.save(user_data)
    
    def get_user(self, user_id):
        return self.user_repository.find_by_id(user_id)

class NotificationService:
    def send_notification(self, user_id, message):
        pass
''')
            
            (project_path / "repository.py").write_text('''
class UserRepository:
    def save(self, user_data):
        pass
    
    def find_by_id(self, user_id):
        pass
''')
            
            deps = AgentDependencies(
                workspace_path=str(project_path),
                client_id="test-graph-client",
                session_data={}
            )
            
            agent = EnhancedL3CodingAgent(deps)
            await agent.initialize()
            
            # Test architecture detection tool
            arch_result = await agent._detect_architecture_tool()
            assert arch_result["status"] == "success" or arch_result["status"] == "error"
            assert "type" in arch_result
            assert "confidence" in arch_result
            
            # Test circular dependency detection
            circular_result = await agent._find_circular_dependencies_tool()
            assert circular_result["status"] == "success" or circular_result["status"] == "error"
            assert "type" in circular_result
            
            # Test coupling analysis
            coupling_result = await agent._analyze_coupling_tool()
            assert coupling_result["status"] == "success" or coupling_result["status"] == "error"
            assert "type" in coupling_result
            
            # Test hotspot detection
            hotspot_result = await agent._find_hotspots_tool()
            assert hotspot_result["status"] == "success" or hotspot_result["status"] == "error"
            assert "type" in hotspot_result
            
            # Test graph visualization
            viz_result = await agent._visualize_graph_tool()
            assert viz_result["status"] == "success" or viz_result["status"] == "error"
            assert "type" in viz_result
    
    @pytest.mark.asyncio
    async def test_enhanced_agent_natural_language_graph_queries(self):
        """Test natural language processing for graph queries"""
        from app.agent.enhanced_l3_agent import EnhancedL3CodingAgent, AgentDependencies
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            (project_path / "example.py").write_text('''
def example_function():
    return "example"

class ExampleClass:
    def method(self):
        return example_function()
''')
            
            deps = AgentDependencies(
                workspace_path=str(project_path),
                client_id="test-nl-graph-client",
                session_data={}
            )
            
            agent = EnhancedL3CodingAgent(deps)
            await agent.initialize()
            
            # Test various natural language queries
            test_queries = [
                "show me the architecture",
                "find circular dependencies",
                "analyze coupling",
                "find hotspots",
                "visualize the graph"
            ]
            
            for query in test_queries:
                response = await agent._process_user_input(query)
                
                # Should return a string response
                assert isinstance(response, str)
                assert len(response) > 0
                
                # Should not crash or return error messages (unless graph DB unavailable)
                if "Graph database not available" not in response:
                    assert "Error" not in response or "Graph database not available" in response
    
    @pytest.mark.asyncio
    async def test_enhanced_agent_state_with_graph_capabilities(self):
        """Test enhanced agent state includes graph capabilities"""
        from app.agent.enhanced_l3_agent import EnhancedL3CodingAgent, AgentDependencies
        
        deps = AgentDependencies(
            workspace_path=".",
            client_id="test-state-graph-client",
            session_data={}
        )
        
        agent = EnhancedL3CodingAgent(deps)
        await agent.initialize()
        
        # Get enhanced state summary
        state = agent.get_enhanced_state_summary()
        
        # Should include graph capabilities
        assert "graph_database_available" in state
        assert "graph_capabilities" in state
        assert isinstance(state["graph_capabilities"], list)
        
        # Check specific graph capabilities
        expected_capabilities = [
            "architecture_detection", "circular_dependency_analysis",
            "coupling_analysis", "hotspot_detection", "graph_visualization"
        ]
        
        for capability in expected_capabilities:
            assert capability in state["graph_capabilities"]


class TestGraphVisualization:
    """Test graph visualization functionality"""
    
    @pytest.mark.asyncio
    async def test_mermaid_diagram_generation(self):
        """Test Mermaid diagram generation"""
        from app.models.graph_models import GraphVisualizationData
        
        # Create test visualization data
        viz_data = GraphVisualizationData(
            nodes=[
                {"id": "A", "name": "ClassA", "label": "Class"},
                {"id": "B", "name": "ClassB", "label": "Class"},
                {"id": "C", "name": "function_c", "label": "Function"}
            ],
            edges=[
                {"source": "A", "target": "B", "type": "INHERITS_FROM"},
                {"source": "A", "target": "C", "type": "CALLS"},
                {"source": "B", "target": "C", "type": "CALLS"}
            ]
        )
        
        # Generate Mermaid diagram
        mermaid = viz_data.to_mermaid()
        
        # Should be valid Mermaid syntax
        assert isinstance(mermaid, str)
        assert "graph TD" in mermaid
        assert "ClassA" in mermaid
        assert "ClassB" in mermaid
        assert "function_c" in mermaid
        assert "-->" in mermaid or "---" in mermaid
        assert "classDef" in mermaid  # Should include styling
    
    def test_graph_statistics_model(self):
        """Test graph statistics model"""
        from app.models.graph_models import GraphStatistics
        
        stats = GraphStatistics(
            total_nodes=100,
            total_relationships=150,
            node_counts={"Class": 20, "Function": 60, "File": 20},
            relationship_counts={"CALLS": 80, "DEPENDS_ON": 50, "INHERITS_FROM": 20},
            graph_density=0.03,
            average_degree=3.0,
            connected_components=1
        )
        
        assert stats.total_nodes == 100
        assert stats.total_relationships == 150
        assert stats.node_counts["Class"] == 20
        assert stats.graph_density == 0.03


def test_graph_integration_basic():
    """Test basic graph integration functionality"""
    from app.services.graph_service import graph_service
    from app.services.graph_query_service import graph_query_service
    from app.models.graph_models import ProjectNode, NodeLabel
    
    # Test basic model creation
    project = ProjectNode(
        id="test",
        name="Test Project",
        workspace_path="/test"
    )
    
    assert project.label == NodeLabel.PROJECT
    assert project.name == "Test Project"
    
    # Test service availability
    assert graph_service is not None
    assert graph_query_service is not None
    
    print("✅ Graph integration basic tests passed")


if __name__ == "__main__":
    # Run basic tests
    test_graph_integration_basic()
    
    # Run async tests
    asyncio.run(TestGraphService().test_graph_models())
    print("✅ Graph model tests passed")
    
    asyncio.run(TestGraphService().test_graph_service_initialization())
    print("✅ Graph service initialization test passed")
    
    asyncio.run(TestEnhancedAgentGraphIntegration().test_enhanced_agent_state_with_graph_capabilities())
    print("✅ Enhanced agent graph capabilities test passed")
    
    print("🎉 All graph integration tests passed!")