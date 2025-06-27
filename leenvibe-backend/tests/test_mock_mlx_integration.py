"""
Phase 2.3: Test Mock MLX Service Integration

Tests for bridging L3 agent context to MLX inference responses.
"""

import asyncio
import os
import sys
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestMockMLXServiceIntegration:
    """Test Mock MLX service integration with L3 agent context"""

    @pytest.mark.asyncio
    async def test_mock_mlx_service_initialization(self):
        """Test Mock MLX service can be initialized"""
        from app.services.mock_mlx_service import MockMLXService

        service = MockMLXService()
        success = await service.initialize()

        assert success == True
        assert service.is_initialized == True
        assert service.model_name == "mlx-community/Qwen2.5-Coder-32B-Instruct"

    @pytest.mark.asyncio
    async def test_code_suggestion_generation(self):
        """Test code suggestion generation with AST context"""
        from app.services.mock_mlx_service import MockMLXService

        service = MockMLXService()
        await service.initialize()

        # Create rich AST context (simulating L3 agent output)
        ast_context = {
            "file_path": "/test/example.py",
            "cursor_position": 100,
            "current_file": {
                "name": "example.py",
                "language": "python",
                "symbol_count": 5,
                "complexity": {"cyclomatic": 3, "functions": 2, "classes": 1},
            },
            "current_symbol": {
                "id": "test_function",
                "name": "calculate_total",
                "type": "function",
                "line_start": 10,
                "line_end": 20,
                "docstring": None,
            },
            "surrounding_context": {
                "target_line": 15,
                "line_content": "def calculate_total(items):",
                "surrounding_lines": [
                    "class Calculator:",
                    "    def __init__(self):",
                    "        self.items = []",
                    "    ",
                    "    def calculate_total(items):",
                    "        # TODO: implement calculation",
                    "        pass",
                ],
                "context_size": 7,
            },
            "completion_hints": [
                "Consider type hints",
                "Follow PEP 8 style",
                "Add docstrings",
            ],
        }

        response = await service.generate_code_completion(ast_context, "suggest")

        # Verify response structure
        assert response["status"] == "success"
        assert response["intent"] == "suggest"
        assert response["language"] == "python"
        assert "confidence" in response
        assert response["confidence"] > 0.5  # Should have decent confidence
        assert "response" in response
        assert "suggestions" in response

        # Verify context usage
        context_used = response["context_used"]
        assert context_used["file_path"] == "/test/example.py"
        assert context_used["has_symbol_context"] == True
        assert context_used["has_surrounding_context"] == True
        assert context_used["hints_count"] == 3
        assert context_used["language_detected"] == "python"

        # Verify Python-specific suggestions
        response_text = response["response"]
        assert (
            "type hint" in response_text.lower()
            or "type annotation" in response_text.lower()
        )
        assert "docstring" in response_text.lower()
        assert "calculate_total" in response_text  # Should reference the function name

    @pytest.mark.asyncio
    async def test_code_explanation_generation(self):
        """Test code explanation generation"""
        from app.services.mock_mlx_service import MockMLXService

        service = MockMLXService()
        await service.initialize()

        context = {
            "file_path": "/test/example.js",
            "current_file": {"language": "javascript", "symbol_count": 3},
            "current_symbol": {
                "name": "fetchUserData",
                "type": "function",
                "line_start": 5,
                "line_end": 15,
            },
            "surrounding_context": {
                "target_line": 8,
                "line_content": "async function fetchUserData(userId) {",
            },
        }

        response = await service.generate_code_completion(context, "explain")

        assert response["status"] == "success"
        assert response["intent"] == "explain"
        assert response["language"] == "javascript"
        assert "fetchUserData" in response["response"]
        assert "function" in response["response"].lower()
        assert "javascript" in response["response"].lower()

    @pytest.mark.asyncio
    async def test_refactoring_suggestions(self):
        """Test refactoring suggestion generation"""
        from app.services.mock_mlx_service import MockMLXService

        service = MockMLXService()
        await service.initialize()

        context = {
            "file_path": "/test/example.swift",
            "current_file": {
                "language": "swift",
                "symbol_count": 8,
                "complexity": {"cyclomatic": 15, "functions": 6, "classes": 2},
            },
            "current_symbol": {
                "name": "UserService",
                "type": "class",
                "line_start": 1,
                "line_end": 50,
            },
        }

        response = await service.generate_code_completion(context, "refactor")

        assert response["status"] == "success"
        assert response["intent"] == "refactor"
        assert response["language"] == "swift"
        assert "refactor" in response["response"].lower()
        assert "swift" in response["response"].lower()

        # Should suggest Swift-specific refactoring
        assert any(
            keyword in response["response"].lower()
            for keyword in ["guard", "protocol", "extension"]
        )

    @pytest.mark.asyncio
    async def test_debug_analysis_generation(self):
        """Test debug analysis generation"""
        from app.services.mock_mlx_service import MockMLXService

        service = MockMLXService()
        await service.initialize()

        context = {
            "file_path": "/test/buggy.py",
            "current_file": {"language": "python", "symbol_count": 4},
            "current_symbol": {"name": "process_data", "type": "function"},
            "surrounding_context": {
                "line_content": "result = data[index]  # Potential IndexError"
            },
        }

        response = await service.generate_code_completion(context, "debug")

        assert response["status"] == "success"
        assert response["intent"] == "debug"
        assert "debug" in response["response"].lower()
        assert "error" in response["response"].lower()

        # Should mention Python-specific debugging tools
        assert any(
            tool in response["response"].lower() for tool in ["pdb", "logging", "print"]
        )

    @pytest.mark.asyncio
    async def test_optimization_suggestions(self):
        """Test optimization suggestion generation"""
        from app.services.mock_mlx_service import MockMLXService

        service = MockMLXService()
        await service.initialize()

        context = {
            "file_path": "/test/slow.js",
            "current_file": {
                "language": "javascript",
                "symbol_count": 10,
                "complexity": {"cyclomatic": 20},
            },
            "current_symbol": {"name": "processLargeArray", "type": "function"},
        }

        response = await service.generate_code_completion(context, "optimize")

        assert response["status"] == "success"
        assert response["intent"] == "optimize"
        assert "performance" in response["response"].lower()
        assert "optimization" in response["response"].lower()

        # Should mention profiling and benchmarking
        assert any(
            keyword in response["response"].lower()
            for keyword in ["profile", "benchmark", "performance"]
        )

    @pytest.mark.asyncio
    async def test_streaming_completion(self):
        """Test streaming completion generation"""
        from app.services.mock_mlx_service import MockMLXService

        service = MockMLXService()
        await service.initialize()

        context = {
            "file_path": "/test/stream.py",
            "current_file": {"language": "python"},
            "completion_hints": ["Add type hints"],
        }

        chunks = []
        async for chunk in service.generate_streaming_completion(context, "suggest"):
            chunks.append(chunk)

        # Should have multiple streaming chunks
        assert len(chunks) > 1

        # Check for streaming chunks
        streaming_chunks = [c for c in chunks if c.get("status") == "streaming"]
        assert len(streaming_chunks) > 0

        # Check for final completion
        final_chunks = [c for c in chunks if c.get("status") == "complete"]
        assert len(final_chunks) == 1

        final_chunk = final_chunks[0]
        assert "metadata" in final_chunk
        assert "confidence" in final_chunk["metadata"]
        assert "suggestions" in final_chunk["metadata"]

    @pytest.mark.asyncio
    async def test_confidence_scoring(self):
        """Test confidence scoring based on context richness"""
        from app.services.mock_mlx_service import MockMLXService

        service = MockMLXService()
        await service.initialize()

        # Rich context should have higher confidence
        rich_context = {
            "current_file": {"language": "python"},
            "current_symbol": {"name": "test", "type": "function"},
            "surrounding_context": {"line_content": "def test():"},
            "completion_hints": ["hint1", "hint2"],
        }

        rich_response = await service.generate_code_completion(rich_context, "suggest")

        # Minimal context should have lower confidence
        minimal_context = {"current_file": {"language": "unknown"}}

        minimal_response = await service.generate_code_completion(
            minimal_context, "suggest"
        )

        # Rich context should have higher confidence
        assert rich_response["confidence"] > minimal_response["confidence"]
        assert rich_response["confidence"] > 0.7
        assert minimal_response["confidence"] < 0.7

    @pytest.mark.asyncio
    async def test_language_specific_responses(self):
        """Test language-specific response generation"""
        from app.services.mock_mlx_service import MockMLXService

        service = MockMLXService()
        await service.initialize()

        languages = ["python", "javascript", "swift"]

        for language in languages:
            context = {
                "current_file": {"language": language},
                "current_symbol": {"name": "testFunction", "type": "function"},
            }

            response = await service.generate_code_completion(context, "suggest")

            assert response["status"] == "success"
            assert response["language"] == language
            assert language in response["response"].lower()

            # Each language should have specific suggestions
            if language == "python":
                assert any(
                    keyword in response["response"].lower()
                    for keyword in ["type hint", "pep 8", "docstring"]
                )
            elif language == "javascript":
                assert any(
                    keyword in response["response"].lower()
                    for keyword in ["const", "let", "arrow", "async"]
                )
            elif language == "swift":
                assert any(
                    keyword in response["response"].lower()
                    for keyword in ["optional", "guard", "protocol"]
                )

    @pytest.mark.asyncio
    async def test_follow_up_suggestions(self):
        """Test follow-up suggestion generation"""
        from app.services.mock_mlx_service import MockMLXService

        service = MockMLXService()
        await service.initialize()

        context = {
            "current_file": {"language": "python"},
            "current_symbol": {"name": "test", "type": "function"},
        }

        response = await service.generate_code_completion(context, "suggest")

        # Should include follow-up suggestions
        assert "suggestions" in response
        assert len(response["suggestions"]) > 0
        assert all(isinstance(s, str) for s in response["suggestions"])

        # Suggestions should be intent-specific
        for suggestion in response["suggestions"]:
            assert any(
                keyword in suggestion.lower()
                for keyword in ["ask", "request", "get", "explain", "refactor"]
            )

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in mock MLX service"""
        from app.services.mock_mlx_service import MockMLXService

        service = MockMLXService()
        await service.initialize()

        # Test with invalid context
        invalid_context = {"invalid": "context"}

        response = await service.generate_code_completion(invalid_context, "suggest")

        # Should handle gracefully with lower confidence
        assert response["status"] == "success"
        assert response["confidence"] < 0.5

        # Test streaming with invalid context
        chunks = []
        async for chunk in service.generate_streaming_completion(
            invalid_context, "suggest"
        ):
            chunks.append(chunk)

        assert len(chunks) > 0
        # Should complete without throwing errors

    def test_global_service_instance(self):
        """Test global mock MLX service instance"""
        from app.services.mock_mlx_service import mock_mlx_service

        assert mock_mlx_service is not None
        assert hasattr(mock_mlx_service, "initialize")
        assert hasattr(mock_mlx_service, "generate_code_completion")
        assert hasattr(mock_mlx_service, "generate_streaming_completion")

    @pytest.mark.asyncio
    async def test_human_review_flagging(self):
        """Test human review requirement flagging"""
        from app.services.mock_mlx_service import MockMLXService

        service = MockMLXService()
        await service.initialize()

        # Create context that should result in low confidence
        low_confidence_context = {
            "current_file": {"language": "unknown"},
            # No symbol context, no surrounding context, no hints
        }

        response = await service.generate_code_completion(
            low_confidence_context, "debug"
        )

        # Low confidence should flag for human review
        assert response["confidence"] < 0.7
        assert response["requires_human_review"] == True

        # High confidence context
        high_confidence_context = {
            "current_file": {"language": "python"},
            "current_symbol": {"name": "test", "type": "function"},
            "surrounding_context": {"line_content": "def test():"},
            "completion_hints": ["Add type hints"],
        }

        response = await service.generate_code_completion(
            high_confidence_context, "explain"
        )

        # High confidence should not require human review
        assert response["confidence"] >= 0.7
        assert response["requires_human_review"] == False
