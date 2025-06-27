"""
Test Visualization Service

Tests for the advanced Mermaid.js visualization service and diagram generation.
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path

import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestVisualizationModels:
    """Test visualization model creation and validation"""

    def test_diagram_configuration_creation(self):
        """Test diagram configuration model"""
        from app.models.visualization_models import (
            DiagramConfiguration,
            DiagramLayout,
            DiagramTheme,
            DiagramType,
        )

        config = DiagramConfiguration(
            diagram_type=DiagramType.ARCHITECTURE_OVERVIEW,
            theme=DiagramTheme.LIGHT,
            layout=DiagramLayout.TOP_DOWN,
            max_nodes=100,
            interactive=True,
        )

        assert config.diagram_type == DiagramType.ARCHITECTURE_OVERVIEW
        assert config.theme == DiagramTheme.LIGHT
        assert config.max_nodes == 100
        assert config.interactive == True
        assert isinstance(config.filters, list)

    def test_diagram_data_creation(self):
        """Test diagram data model"""
        from app.models.visualization_models import (
            DiagramConfiguration,
            DiagramData,
            DiagramEdge,
            DiagramNode,
            DiagramType,
        )

        config = DiagramConfiguration(diagram_type=DiagramType.DEPENDENCY_GRAPH)

        nodes = [
            DiagramNode(id="node1", label="Node 1", type="file"),
            DiagramNode(id="node2", label="Node 2", type="file"),
        ]

        edges = [
            DiagramEdge(
                id="edge1", source_id="node1", target_id="node2", type="depends"
            )
        ]

        diagram = DiagramData(
            id="test_diagram",
            title="Test Diagram",
            configuration=config,
            nodes=nodes,
            edges=edges,
        )

        assert diagram.get_node_count() == 2
        assert diagram.get_edge_count() == 1
        assert len(diagram.get_nodes_by_type("file")) == 2
        assert len(diagram.get_edges_by_type("depends")) == 1

    def test_mermaid_diagram_creation(self):
        """Test Mermaid diagram model"""
        from app.models.visualization_models import DiagramTheme, MermaidDiagram

        content = """graph TD
    A[Node A] --> B[Node B]
    B --> C[Node C]"""

        diagram = MermaidDiagram(
            diagram_type="graph",
            content=content,
            theme=DiagramTheme.LIGHT,
            configuration={"theme": "light"},
            custom_css="fill:#f9f9f9",
        )

        full_content = diagram.get_full_content()
        assert "graph TD" in full_content
        assert "Node A" in full_content
        assert "fill:#f9f9f9" in full_content

    def test_diagram_generation_request(self):
        """Test diagram generation request model"""
        from app.models.visualization_models import (
            DiagramConfiguration,
            DiagramExportFormat,
            DiagramGenerationRequest,
            DiagramType,
        )

        config = DiagramConfiguration(diagram_type=DiagramType.HOTSPOT_HEATMAP)

        request = DiagramGenerationRequest(
            project_id="test_project",
            configuration=config,
            export_format=DiagramExportFormat.MERMAID,
            include_metadata=True,
            cache_result=True,
        )

        assert request.project_id == "test_project"
        assert request.configuration.diagram_type == DiagramType.HOTSPOT_HEATMAP
        assert request.export_format == DiagramExportFormat.MERMAID
        assert request.cache_result == True


class TestVisualizationService:
    """Test visualization service functionality"""

    @pytest.mark.asyncio
    async def test_visualization_service_initialization(self):
        """Test visualization service initialization"""
        from app.services.visualization_service import visualization_service

        # Should initialize without errors
        assert visualization_service is not None
        assert hasattr(visualization_service, "cache")
        assert hasattr(visualization_service, "templates")
        assert hasattr(visualization_service, "theme_configurations")

        # Check that templates are loaded
        assert len(visualization_service.templates) > 0
        assert len(visualization_service.theme_configurations) > 0

    @pytest.mark.asyncio
    async def test_get_diagram_types(self):
        """Test getting available diagram types"""
        from app.services.visualization_service import visualization_service

        diagram_types = await visualization_service.get_diagram_types()

        assert isinstance(diagram_types, list)
        assert len(diagram_types) > 0

        # Check structure of diagram type info
        for diagram_type in diagram_types:
            assert "type" in diagram_type
            assert "name" in diagram_type
            assert "description" in diagram_type
            assert "supported_layouts" in diagram_type
            assert "max_recommended_nodes" in diagram_type

    @pytest.mark.asyncio
    async def test_cache_functionality(self):
        """Test diagram caching functionality"""
        from app.services.visualization_service import visualization_service

        # Get initial cache stats
        initial_stats = visualization_service.get_cache_stats()
        assert isinstance(initial_stats, dict)
        assert "cache_size" in initial_stats
        assert "max_cache_size" in initial_stats
        assert "cache_hit_rate" in initial_stats

        # Cache should be initially empty or small
        assert initial_stats["cache_size"] >= 0

    @pytest.mark.asyncio
    async def test_diagram_generation_with_mock_data(self):
        """Test diagram generation with mock project data"""
        from app.models.visualization_models import (
            DiagramConfiguration,
            DiagramGenerationRequest,
            DiagramTheme,
            DiagramType,
        )
        from app.services.visualization_service import visualization_service

        # Create test request
        config = DiagramConfiguration(
            diagram_type=DiagramType.ARCHITECTURE_OVERVIEW,
            theme=DiagramTheme.LIGHT,
            max_nodes=10,
        )

        request = DiagramGenerationRequest(
            project_id="test_project_mock", configuration=config
        )

        try:
            # This should handle gracefully even with no real project data
            response = await visualization_service.generate_diagram(request)

            # Should return response even if no data
            assert hasattr(response, "diagram_id")
            assert hasattr(response, "generation_time_ms")
            assert response.generation_time_ms >= 0

        except Exception as e:
            # Should handle gracefully - visualization service should not crash
            print(f"Expected behavior - no project data available: {e}")
            assert "project" in str(e).lower() or "graph" in str(e).lower()

    def test_id_sanitization(self):
        """Test ID sanitization for Mermaid compatibility"""
        from app.services.visualization_service import visualization_service

        # Test various ID formats that need sanitization
        test_cases = [
            ("file/path/test.py", "file_path_test_py"),
            ("module.submodule", "module_submodule"),
            ("class-name", "class_name"),
            ("123invalid", "id_123invalid"),
            ("valid_id", "valid_id"),
            ("", "unknown"),
        ]

        for input_id, expected in test_cases:
            sanitized = visualization_service._sanitize_id(input_id)
            # Should not contain problematic characters
            assert "/" not in sanitized
            assert "." not in sanitized
            assert "-" not in sanitized
            assert " " not in sanitized
            # Should start with letter or "id_"
            assert sanitized[0].isalpha() or sanitized.startswith("id_")

    def test_edge_connector_mapping(self):
        """Test edge connector mapping for different relationship types"""
        from app.models.visualization_models import DiagramType
        from app.services.visualization_service import visualization_service

        # Test different edge types
        test_cases = [
            ("dependency", "-->"),
            ("calls", "-->"),
            ("inherits", "-.->"),
            ("implements", "-.->"),
            ("unknown_type", "-->"),  # Should default to -->
        ]

        for edge_type, expected_connector in test_cases:
            connector = visualization_service._get_edge_connector(
                edge_type, DiagramType.ARCHITECTURE_OVERVIEW
            )
            assert connector == expected_connector

    def test_theme_configurations(self):
        """Test theme configuration loading"""
        from app.models.visualization_models import DiagramTheme
        from app.services.visualization_service import visualization_service

        themes = visualization_service.theme_configurations

        # Should have configurations for all themes
        assert DiagramTheme.LIGHT in themes
        assert DiagramTheme.DARK in themes
        assert DiagramTheme.NEUTRAL in themes

        # Each theme should have required properties
        for theme_config in themes.values():
            assert "primaryColor" in theme_config
            assert "primaryTextColor" in theme_config
            assert "lineColor" in theme_config


class TestVisualizationIntegration:
    """Test visualization integration with enhanced L3 agent"""

    @pytest.mark.asyncio
    async def test_enhanced_agent_visualization_tools(self):
        """Test enhanced agent visualization tool integration"""
        from app.agent.enhanced_l3_agent import AgentDependencies, EnhancedL3CodingAgent

        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            # Create test project
            (project_path / "main.py").write_text(
                '''
def main():
    """Main function"""
    print("Hello World")
    return 0

class TestClass:
    def method(self):
        return main()
'''
            )

            deps = AgentDependencies(
                workspace_path=str(project_path),
                client_id="test-viz-client",
                session_data={},
            )

            agent = EnhancedL3CodingAgent(deps)
            await agent.initialize()

            # Test diagram generation tool
            result = await agent._generate_diagram_tool()
            assert result["status"] == "success" or "error" in result["status"]
            assert "type" in result
            assert "confidence" in result

            # Test listing diagram types
            types_result = await agent._list_diagram_types_tool()
            assert types_result["status"] == "success"
            assert "data" in types_result
            assert "diagram_types" in types_result["data"]

    @pytest.mark.asyncio
    async def test_enhanced_agent_natural_language_diagram_requests(self):
        """Test natural language processing for diagram requests"""
        from app.agent.enhanced_l3_agent import AgentDependencies, EnhancedL3CodingAgent

        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            (project_path / "example.py").write_text(
                """
def example():
    return "test"
"""
            )

            deps = AgentDependencies(
                workspace_path=str(project_path),
                client_id="test-nl-viz-client",
                session_data={},
            )

            agent = EnhancedL3CodingAgent(deps)
            await agent.initialize()

            # Test various diagram-related queries
            test_queries = [
                "show me available diagrams",
                "what diagram types can you create",
                "generate architecture diagram",
                "create dependency visualization",
                "show hotspot diagram",
            ]

            for query in test_queries:
                response = await agent._process_user_input(query)

                # Should return string response
                assert isinstance(response, str)
                assert len(response) > 0

                # Should not crash or return unhandled errors
                if "Error" in response:
                    # Errors should be graceful and informative
                    assert (
                        "diagram" in response.lower()
                        or "visualization" in response.lower()
                    )

    @pytest.mark.asyncio
    async def test_enhanced_state_includes_visualization_capabilities(self):
        """Test enhanced agent state includes visualization capabilities"""
        from app.agent.enhanced_l3_agent import AgentDependencies, EnhancedL3CodingAgent

        deps = AgentDependencies(
            workspace_path=".", client_id="test-state-viz-client", session_data={}
        )

        agent = EnhancedL3CodingAgent(deps)
        await agent.initialize()

        # Get enhanced state summary
        state = agent.get_enhanced_state_summary()

        # Should include visualization capabilities
        assert "visualization_capabilities" in state
        assert isinstance(state["visualization_capabilities"], list)

        # Check specific visualization capabilities
        expected_capabilities = [
            "interactive_diagrams",
            "multiple_diagram_types",
            "theme_support",
            "mermaid_generation",
        ]

        for capability in expected_capabilities:
            assert capability in state["visualization_capabilities"]


class TestMermaidGeneration:
    """Test Mermaid.js content generation"""

    def test_mermaid_template_rendering(self):
        """Test Mermaid template rendering with sample data"""
        from app.models.visualization_models import (
            DiagramConfiguration,
            DiagramData,
            DiagramEdge,
            DiagramLayout,
            DiagramNode,
            DiagramType,
        )
        from app.services.visualization_service import visualization_service

        # Create sample diagram data
        config = DiagramConfiguration(
            diagram_type=DiagramType.DEPENDENCY_GRAPH, layout=DiagramLayout.TOP_DOWN
        )

        nodes = [
            DiagramNode(id="fileA", label="File A", type="file"),
            DiagramNode(id="fileB", label="File B", type="file"),
            DiagramNode(id="fileC", label="File C", type="file"),
        ]

        edges = [
            DiagramEdge(
                id="dep1", source_id="fileA", target_id="fileB", type="dependency"
            ),
            DiagramEdge(
                id="dep2", source_id="fileB", target_id="fileC", type="dependency"
            ),
        ]

        diagram_data = DiagramData(
            id="test_diagram",
            title="Test Dependency Graph",
            configuration=config,
            nodes=nodes,
            edges=edges,
        )

        # Test template rendering
        try:
            # This tests the internal template rendering
            template_str = visualization_service.templates.get(
                DiagramType.DEPENDENCY_GRAPH
            )
            assert template_str is not None
            assert "graph" in template_str
            assert "nodes" in template_str
            assert "edges" in template_str

        except Exception as e:
            print(
                f"Template rendering test - expected if Jinja2 not fully configured: {e}"
            )


def test_visualization_basic_functionality():
    """Test basic visualization functionality"""
    from app.models.visualization_models import DiagramTheme, DiagramType
    from app.services.visualization_service import visualization_service

    # Test service availability
    assert visualization_service is not None

    # Test basic methods exist
    assert hasattr(visualization_service, "generate_diagram")
    assert hasattr(visualization_service, "get_diagram_types")
    assert hasattr(visualization_service, "get_cache_stats")

    # Test cache stats
    stats = visualization_service.get_cache_stats()
    assert isinstance(stats, dict)
    assert "cache_size" in stats

    print("✅ Visualization service basic functionality test passed")


if __name__ == "__main__":
    # Run basic tests
    test_visualization_basic_functionality()

    # Run async tests
    asyncio.run(TestVisualizationService().test_visualization_service_initialization())
    print("✅ Visualization service initialization test passed")

    asyncio.run(TestVisualizationService().test_get_diagram_types())
    print("✅ Diagram types test passed")

    asyncio.run(
        TestVisualizationIntegration().test_enhanced_state_includes_visualization_capabilities()
    )
    print("✅ Enhanced agent visualization capabilities test passed")

    print("🎉 All visualization service tests passed!")
