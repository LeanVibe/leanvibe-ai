"""
Phase 2.2: Test AST Agent Integration

Tests for AST context provision to L3 agent.
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestASTAgentIntegration:
    """Test AST context integration with L3 agent"""

    @pytest.mark.asyncio
    async def test_ast_context_provider_creation(self):
        """Test AST context provider can be created"""
        from app.agent.ast_context_provider import ASTContextProvider

        provider = ASTContextProvider()
        assert provider is not None
        assert hasattr(provider, "get_file_context")
        assert hasattr(provider, "get_symbol_context")
        assert hasattr(provider, "get_completion_context")

    @pytest.mark.asyncio
    async def test_file_context_provision(self):
        """Test AST context provided to agent"""
        from app.agent.ast_context_provider import ASTContextProvider

        # Create a test file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """
def hello_world():
    '''A simple hello world function'''
    print("Hello, World!")
    return True

class Calculator:
    def add(self, a, b):
        return a + b
"""
            )
            test_file = f.name

        try:
            # Mock AST service
            with patch(
                "app.agent.ast_context_provider.ast_service"
            ) as mock_ast_service:
                # Create mock file analysis
                mock_analysis = Mock()
                mock_analysis.language = "python"
                mock_analysis.symbols = []
                mock_analysis.dependencies = []
                mock_analysis.complexity = Mock()
                mock_analysis.complexity.cyclomatic_complexity = 2
                mock_analysis.complexity.number_of_functions = 2
                mock_analysis.complexity.number_of_classes = 1
                mock_analysis.complexity.lines_of_code = 8
                mock_analysis.syntax_errors = []

                mock_ast_service.analyze_file = AsyncMock(return_value=mock_analysis)

                provider = ASTContextProvider()
                context = await provider.get_file_context(test_file, cursor_position=50)

                # Verify context structure
                assert context is not None
                assert "file_path" in context
                assert "language" in context
                assert "file_analysis" in context
                assert "current_symbol" in context
                assert "project_context" in context

                # Verify file analysis
                file_analysis = context["file_analysis"]
                assert "symbols" in file_analysis
                assert "complexity" in file_analysis
                assert file_analysis["complexity"]["cyclomatic"] == 2

                # Verify it was called
                mock_ast_service.analyze_file.assert_called_once_with(test_file)

        finally:
            # Clean up
            os.unlink(test_file)

    @pytest.mark.asyncio
    async def test_symbol_context_provision(self):
        """Test symbol-specific context"""
        from app.agent.ast_context_provider import ASTContextProvider

        with (
            patch("app.agent.ast_context_provider.ast_service") as mock_ast_service,
            patch("app.agent.ast_context_provider.project_indexer") as mock_indexer,
        ):

            # Mock symbol
            mock_symbol = Mock()
            mock_symbol.id = "test_symbol"
            mock_symbol.name = "test_function"
            mock_symbol.symbol_type = Mock()
            mock_symbol.symbol_type.value = "function"
            mock_symbol.file_path = "/test/file.py"
            mock_symbol.line_start = 1
            mock_symbol.line_end = 5
            mock_symbol.docstring = "Test function"

            # Mock references
            mock_references = [Mock()]
            mock_references[0].file_path = "/test/another.py"
            mock_references[0].line_number = 10
            mock_references[0].reference_type = "usage"
            mock_references[0].context = "function call"

            mock_ast_service.get_symbol = AsyncMock(return_value=mock_symbol)
            mock_indexer.find_references_by_symbol_id = AsyncMock(
                return_value=mock_references
            )

            provider = ASTContextProvider()
            context = await provider.get_symbol_context("test_symbol", "/test/file.py")

            # Verify context
            assert context is not None
            assert "symbol_id" in context
            assert "symbol" in context
            assert "references" in context
            assert "usage_count" in context
            assert context["usage_count"] == 1
            assert context["symbol"]["name"] == "test_function"

    @pytest.mark.asyncio
    async def test_completion_context_provision(self):
        """Test completion-optimized context"""
        from app.agent.ast_context_provider import ASTContextProvider

        # Create test file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def test(): pass")
            test_file = f.name

        try:
            # Mock dependencies
            with patch(
                "app.agent.ast_context_provider.ast_service"
            ) as mock_ast_service:
                mock_analysis = Mock()
                mock_analysis.language = "python"
                mock_analysis.symbols = []
                mock_analysis.dependencies = []
                mock_analysis.complexity = Mock()
                mock_analysis.complexity.cyclomatic_complexity = 1
                mock_analysis.complexity.number_of_functions = 1
                mock_analysis.complexity.number_of_classes = 0
                mock_analysis.complexity.lines_of_code = 1
                mock_analysis.syntax_errors = []

                mock_ast_service.analyze_file = AsyncMock(return_value=mock_analysis)

                provider = ASTContextProvider()
                context = await provider.get_completion_context(
                    test_file, 10, "suggest"
                )

                # Verify completion context structure
                assert context is not None
                assert "intent" in context
                assert "current_file" in context
                assert "relevant_context" in context
                assert "completion_hints" in context
                assert context["intent"] == "suggest"
                assert context["current_file"]["language"] == "python"

        finally:
            os.unlink(test_file)

    @pytest.mark.asyncio
    async def test_agent_context_understanding(self):
        """Test agent can use AST context in responses"""
        from app.agent.ast_context_provider import ASTContextProvider
        from app.agent.enhanced_l3_agent import AgentDependencies, EnhancedL3CodingAgent

        # Mock all dependencies
        with (
            patch("app.agent.enhanced_l3_agent.ast_service") as mock_ast_service,
            patch("app.agent.enhanced_l3_agent.graph_service") as mock_graph_service,
            patch("app.agent.enhanced_l3_agent.incremental_indexer") as mock_indexer,
            patch("app.services.ai_service.AIService") as mock_ai_service,
        ):

            # Configure mocks
            mock_ast_service.initialize = AsyncMock(return_value=True)
            mock_graph_service.initialize = AsyncMock(return_value=True)
            mock_graph_service.initialized = True
            mock_ai_service.return_value.mlx_available = False
            mock_ai_service.return_value.model = None

            # Create mock project index
            mock_project_index = Mock()
            mock_project_index.total_files = 1
            mock_project_index.supported_files = 1
            mock_project_index.symbols = {}
            mock_project_index.parsing_errors = 0
            mock_project_index.files = {}
            mock_project_index.dependencies = []

            mock_indexer.get_or_create_project_index = AsyncMock(
                return_value=mock_project_index
            )

            deps = AgentDependencies(
                workspace_path=".", client_id="test-ast-integration", session_data={}
            )

            agent = EnhancedL3CodingAgent(deps)
            agent.project_index = mock_project_index  # Set directly for test

            # Test that agent can handle AST context
            provider = ASTContextProvider()

            # Test file context integration
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write("print('hello')")
                test_file = f.name

            try:
                # Mock file analysis for context provider
                with patch.object(provider, "get_file_context") as mock_get_context:
                    mock_context = {
                        "file_path": test_file,
                        "language": "python",
                        "file_analysis": {
                            "symbols": [],
                            "complexity": {"cyclomatic": 1},
                            "imports": [],
                        },
                        "current_symbol": None,
                        "project_context": {},
                    }
                    mock_get_context.return_value = mock_context

                    # Get context
                    context = await provider.get_file_context(test_file)

                    # Verify agent can process the context
                    assert context is not None
                    assert "file_analysis" in context
                    assert "language" in context

                    # The agent tools should be able to process this context
                    # (Testing the tool interface, not full execution)
                    assert hasattr(agent, "_analyze_project_tool")
                    assert hasattr(agent, "_explore_symbols_tool")

            finally:
                os.unlink(test_file)

    def test_context_provider_error_handling(self):
        """Test context provider handles errors gracefully"""
        from app.agent.ast_context_provider import ASTContextProvider

        provider = ASTContextProvider()

        # Test minimal context creation
        minimal_context = provider._create_minimal_context(
            "/fake/file.py", "Test error"
        )

        assert minimal_context is not None
        assert "error" in minimal_context
        assert "file_path" in minimal_context
        assert "language" in minimal_context
        assert minimal_context["minimal"] == True

    def test_language_detection(self):
        """Test language detection from file extensions"""
        from app.agent.ast_context_provider import ASTContextProvider

        provider = ASTContextProvider()

        assert provider._detect_language_from_extension("test.py") == "python"
        assert provider._detect_language_from_extension("test.js") == "javascript"
        assert provider._detect_language_from_extension("test.ts") == "typescript"
        assert provider._detect_language_from_extension("test.swift") == "swift"
        assert provider._detect_language_from_extension("test.unknown") == "unknown"

    def test_symbol_conversion(self):
        """Test symbol to dictionary conversion"""
        from app.agent.ast_context_provider import ASTContextProvider

        provider = ASTContextProvider()

        # Test with None symbol
        assert provider._symbol_to_dict(None) is None

        # Test with mock symbol
        mock_symbol = Mock()
        mock_symbol.id = "test_id"
        mock_symbol.name = "test_name"
        mock_symbol.symbol_type = Mock()
        mock_symbol.symbol_type.value = "function"
        mock_symbol.file_path = "/test/file.py"
        mock_symbol.line_start = 1
        mock_symbol.line_end = 5
        mock_symbol.docstring = "Test docstring"

        result = provider._symbol_to_dict(mock_symbol)

        assert result is not None
        assert result["id"] == "test_id"
        assert result["name"] == "test_name"
        assert result["type"] == "function"
        assert result["file_path"] == "/test/file.py"

    @pytest.mark.asyncio
    async def test_surrounding_context_extraction(self):
        """Test extraction of surrounding code context"""
        from app.agent.ast_context_provider import ASTContextProvider

        # Create test file with content
        test_content = """line 1
line 2
line 3
line 4 - target
line 5
line 6
line 7"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_content)
            test_file = f.name

        try:
            provider = ASTContextProvider()

            # Test getting context around line 4 (target line)
            cursor_position = test_content.find("line 4")
            context = await provider._get_surrounding_context(
                test_file, cursor_position
            )

            assert context is not None
            assert "target_line" in context
            assert "line_content" in context
            assert "surrounding_lines" in context
            assert "line 4 - target" in context["line_content"]

        finally:
            os.unlink(test_file)
