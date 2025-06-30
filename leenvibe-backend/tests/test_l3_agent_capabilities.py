"""
Phase 2.1: Test L3 Agent Framework Capabilities

Tests for understanding what the L3 agent framework can already do
before connecting new components.
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestL3AgentFramework:
    """Test L3 agent framework capabilities"""

    @pytest.mark.asyncio
    async def test_base_agent_initialization(self):
        """Test L3 agent can be created and configured"""
        from app.agent.l3_coding_agent import AgentDependencies, L3CodingAgent

        # Mock AI service to avoid MLX dependency
        with patch("app.agent.l3_coding_agent.AIService") as mock_ai_service:
            mock_ai_service.return_value.mlx_available = False
            mock_ai_service.return_value.model = None

            deps = AgentDependencies(
                workspace_path=".", client_id="test-client", session_data={}
            )

            agent = L3CodingAgent(deps)
            success = await agent.initialize()

            assert success is True
            assert agent.dependencies == deps
            assert hasattr(agent, "state")
            assert hasattr(agent, "tools")

    @pytest.mark.asyncio
    async def test_enhanced_agent_initialization(self):
        """Test enhanced L3 agent can be created and configured"""
        from app.agent.enhanced_l3_agent import AgentDependencies, EnhancedL3CodingAgent

        # Mock all the service dependencies
        with (
            patch("app.agent.enhanced_l3_agent.ast_service") as mock_ast_service,
            patch("app.agent.enhanced_l3_agent.graph_service") as mock_graph_service,
            patch("app.services.ai_service.AIService") as mock_ai_service,
        ):

            # Configure mocks
            mock_ast_service.initialize = AsyncMock(return_value=True)
            mock_graph_service.initialize = AsyncMock(return_value=True)
            mock_graph_service.initialized = True
            mock_ai_service.return_value.mlx_available = False
            mock_ai_service.return_value.model = None

            deps = AgentDependencies(
                workspace_path=".", client_id="test-enhanced-client", session_data={}
            )

            agent = EnhancedL3CodingAgent(deps)
            success = await agent.initialize()

            assert success is True
            assert agent.dependencies == deps
            assert hasattr(agent, "project_context")
            assert hasattr(agent, "project_index")

    @pytest.mark.asyncio
    async def test_agent_context_management(self):
        """Test agent maintains conversation context"""
        from app.agent.l3_coding_agent import (
            AgentDependencies,
            L3CodingAgent,
        )

        with patch("app.services.ai_service.AIService") as mock_ai_service:
            mock_ai_service.return_value.mlx_available = False
            mock_ai_service.return_value.model = None

            deps = AgentDependencies(
                workspace_path=".", client_id="test-client", session_data={}
            )

            agent = L3CodingAgent(deps)
            await agent.initialize()

            # Test conversation history
            agent.state.add_conversation_entry("user", "Hello", 0.9)
            agent.state.add_conversation_entry("assistant", "Hi there!", 0.8)

            assert len(agent.state.conversation_history) == 2
            assert agent.state.get_average_confidence() == 0.85

            # Test project context
            agent.state.update_project_context("language", "python")
            assert agent.state.project_context["language"] == "python"

    @pytest.mark.asyncio
    async def test_agent_tool_integration(self):
        """Test agent can use existing tools"""
        from app.agent.enhanced_l3_agent import AgentDependencies, EnhancedL3CodingAgent

        # Mock dependencies
        with (
            patch("app.agent.enhanced_l3_agent.ast_service") as mock_ast_service,
            patch("app.agent.enhanced_l3_agent.graph_service") as mock_graph_service,
            patch("app.agent.enhanced_l3_agent.project_indexer"),
            patch("app.services.ai_service.AIService") as mock_ai_service,
        ):

            mock_ast_service.initialize = AsyncMock(return_value=True)
            mock_graph_service.initialize = AsyncMock(return_value=True)
            mock_graph_service.initialized = True
            mock_ai_service.return_value.mlx_available = False
            mock_ai_service.return_value.model = None

            deps = AgentDependencies(
                workspace_path=".", client_id="test-enhanced-client", session_data={}
            )

            agent = EnhancedL3CodingAgent(deps)
            await agent.initialize()

            # Check that enhanced tools are available
            expected_tools = [
                "analyze_project",
                "find_references",
                "impact_analysis",
                "suggest_refactoring",
                "explore_symbols",
                "check_complexity",
                "detect_architecture",
                "find_circular_deps",
                "analyze_coupling",
                "find_hotspots",
                "visualize_graph",
                "generate_diagram",
            ]

            for tool in expected_tools:
                assert tool in agent.tools, f"Tool {tool} not found in agent tools"

    @pytest.mark.asyncio
    async def test_agent_mock_responses(self):
        """Test agent generates structured responses"""
        from app.agent.l3_coding_agent import (
            SimpleMLXModel,
        )
        from app.services.ai_service import AIService

        # Mock AI service to return predictable responses
        mock_ai_service = Mock(spec=AIService)
        mock_ai_service.mlx_available = False
        mock_ai_service.model = None
        mock_ai_service._generate_mock_response = AsyncMock(
            return_value="Mock response for testing"
        )

        model = SimpleMLXModel(mock_ai_service)
        response = await model.generate_response("Test prompt")

        assert response == "Mock response for testing"
        assert mock_ai_service._generate_mock_response.called

    @pytest.mark.asyncio
    async def test_enhanced_agent_project_analysis(self):
        """Test enhanced agent project analysis capability"""
        from app.agent.enhanced_l3_agent import AgentDependencies, EnhancedL3CodingAgent

        # Create a test project structure
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            # Create test files
            (project_path / "main.py").write_text(
                """
def main():
    print("Hello World")
    return 0

if __name__ == "__main__":
    main()
"""
            )

            (project_path / "utils.py").write_text(
                """
class Calculator:
    def add(self, a, b):
        return a + b
    
    def multiply(self, a, b):
        return a * b
"""
            )

            # Mock all dependencies
            with (
                patch("app.agent.enhanced_l3_agent.ast_service") as mock_ast_service,
                patch(
                    "app.agent.enhanced_l3_agent.graph_service"
                ) as mock_graph_service,
                patch(
                    "app.agent.enhanced_l3_agent.incremental_indexer"
                ) as mock_indexer,
                patch("app.services.ai_service.AIService") as mock_ai_service,
            ):

                # Create mock project index
                from app.models.ast_models import ProjectIndex

                mock_project_index = Mock(spec=ProjectIndex)
                mock_project_index.total_files = 2
                mock_project_index.supported_files = 2
                mock_project_index.symbols = {"symbol1": Mock(), "symbol2": Mock()}
                mock_project_index.parsing_errors = 0
                mock_project_index.files = {}
                mock_project_index.dependencies = []

                # Configure mocks
                mock_ast_service.initialize = AsyncMock(return_value=True)
                mock_graph_service.initialize = AsyncMock(return_value=True)
                mock_graph_service.initialized = True
                mock_indexer.get_or_create_project_index = AsyncMock(
                    return_value=mock_project_index
                )
                mock_ai_service.return_value.mlx_available = False
                mock_ai_service.return_value.model = None

                deps = AgentDependencies(
                    workspace_path=str(project_path),
                    client_id="test-enhanced-client",
                    session_data={},
                )

                agent = EnhancedL3CodingAgent(deps)
                success = await agent.initialize()
                assert success is True

                # Test project analysis tool
                result = await agent._analyze_project_tool()

                assert result["status"] == "success"
                assert result["type"] == "project_analysis"
                assert "data" in result
                assert "summary" in result["data"]
                assert result["confidence"] > 0.5

    @pytest.mark.asyncio
    async def test_enhanced_agent_symbol_exploration(self):
        """Test enhanced agent symbol exploration capability"""
        from app.agent.enhanced_l3_agent import AgentDependencies, EnhancedL3CodingAgent

        # Mock dependencies and project index with symbols
        with (
            patch("app.agent.enhanced_l3_agent.ast_service") as mock_ast_service,
            patch("app.agent.enhanced_l3_agent.graph_service") as mock_graph_service,
            patch("app.agent.enhanced_l3_agent.incremental_indexer") as mock_indexer,
            patch("app.services.ai_service.AIService") as mock_ai_service,
        ):

            # Create mock symbols
            from app.models.ast_models import Symbol, SymbolType

            mock_symbol1 = Mock(spec=Symbol)
            mock_symbol1.name = "main_function"
            mock_symbol1.symbol_type = SymbolType.FUNCTION
            mock_symbol1.file_path = "/test/main.py"
            mock_symbol1.line_start = 1

            mock_symbol2 = Mock(spec=Symbol)
            mock_symbol2.name = "helper_function"
            mock_symbol2.symbol_type = SymbolType.FUNCTION
            mock_symbol2.file_path = "/test/utils.py"
            mock_symbol2.line_start = 5

            # Create mock project index
            from app.models.ast_models import ProjectIndex

            mock_project_index = Mock(spec=ProjectIndex)
            mock_project_index.symbols = {
                "symbol1": mock_symbol1,
                "symbol2": mock_symbol2,
            }

            # Configure mocks
            mock_ast_service.initialize = AsyncMock(return_value=True)
            mock_graph_service.initialize = AsyncMock(return_value=True)
            mock_graph_service.initialized = True
            mock_indexer.get_or_create_project_index = AsyncMock(
                return_value=mock_project_index
            )
            mock_ai_service.return_value.mlx_available = False
            mock_ai_service.return_value.model = None

            deps = AgentDependencies(
                workspace_path=".", client_id="test-enhanced-client", session_data={}
            )

            agent = EnhancedL3CodingAgent(deps)
            agent.project_index = mock_project_index  # Set directly for test

            # Test symbol exploration
            result = await agent._explore_symbols_tool("function")

            assert result["status"] == "success"
            assert result["type"] == "symbol_exploration"
            assert "data" in result
            assert result["data"]["matching_symbols"] == 2
            assert "summary" in result["data"]

    def test_agent_state_summary(self):
        """Test agent state summary functionality"""
        from app.agent.enhanced_l3_agent import AgentDependencies, EnhancedL3CodingAgent

        deps = AgentDependencies(
            workspace_path=".", client_id="test-enhanced-client", session_data={}
        )

        agent = EnhancedL3CodingAgent(deps)

        # Test enhanced state summary
        summary = agent.get_enhanced_state_summary()

        assert isinstance(summary, dict)
        assert "project_indexed" in summary
        assert "ast_capabilities" in summary
        assert "graph_capabilities" in summary
        assert "visualization_capabilities" in summary
        assert "monitoring_capabilities" in summary

        # Check AST capabilities
        expected_ast_capabilities = [
            "project_analysis",
            "symbol_exploration",
            "reference_finding",
            "complexity_analysis",
            "contextual_file_analysis",
        ]
        for capability in expected_ast_capabilities:
            assert capability in summary["ast_capabilities"]

    @pytest.mark.asyncio
    async def test_agent_error_handling(self):
        """Test agent graceful error handling"""
        from app.agent.l3_coding_agent import AgentDependencies, L3CodingAgent

        # Mock failing AI service
        with patch("app.services.ai_service.AIService") as mock_ai_service:
            mock_ai_service.return_value.mlx_available = False
            mock_ai_service.return_value.model = None
            mock_ai_service.side_effect = Exception("Simulated failure")

            deps = AgentDependencies(
                workspace_path=".", client_id="test-client", session_data={}
            )

            agent = L3CodingAgent(deps)

            # Initialization should handle errors gracefully
            await agent.initialize()

            # Even if initialization has issues, agent should be in a usable state
            assert hasattr(agent, "dependencies")
            assert hasattr(agent, "state")
