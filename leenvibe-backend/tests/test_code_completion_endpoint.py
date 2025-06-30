"""
Phase 2.4.1: Code Completion Endpoint Tests

Comprehensive tests for the code completion REST endpoint.
Tests all 5 intents with proper validation and error handling.
"""

import asyncio
import json
import os
import sys
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestCodeCompletionEndpoint:
    """Test suite for /api/code-completion endpoint"""

    @pytest.fixture
    def test_client(self):
        """Create FastAPI test client"""
        from app.main import app

        return TestClient(app)

    @pytest.fixture
    async def async_client(self):
        """Create async test client"""

        from app.main import app

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            yield client

    @pytest.fixture
    def sample_python_request(self):
        """Sample Python code completion request"""
        return {
            "file_path": "/test/example.py",
            "cursor_position": 100,
            "intent": "suggest",
            "content": "def calculate_total(items):\n    # TODO: implement\n    pass",
            "language": "python",
        }

    @pytest.fixture
    def sample_javascript_request(self):
        """Sample JavaScript code completion request"""
        return {
            "file_path": "/test/app.js",
            "cursor_position": 50,
            "intent": "explain",
            "content": "async function fetchData() {\n    const response = await fetch('/api/data');\n    return response.json();\n}",
            "language": "javascript",
        }

    @pytest.fixture
    def mock_enhanced_agent_response(self):
        """Mock Enhanced L3 Agent response"""
        return {
            "response": "Add type hints and implement the calculation logic",
            "confidence": 0.85,
            "language": "python",
            "requires_review": False,
            "follow_up_actions": ["Add error handling", "Write unit tests"],
            "model": "mlx-community/Qwen2.5-Coder-32B-Instruct",
            "context_used": {
                "file_path": "/test/example.py",
                "has_symbol_context": True,
                "language_detected": "python",
            },
        }

    # ============================================================================
    # ENDPOINT EXISTENCE AND BASIC FUNCTIONALITY TESTS
    # ============================================================================

    def test_endpoint_exists(self, test_client):
        """Test that the code completion endpoint exists"""
        response = test_client.post("/api/code-completion", json={})
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404

    def test_endpoint_accepts_post_only(self, test_client):
        """Test endpoint only accepts POST requests"""
        # GET should not be allowed
        response = test_client.get("/api/code-completion")
        assert response.status_code == 405  # Method Not Allowed

        # PUT should not be allowed
        response = test_client.put("/api/code-completion", json={})
        assert response.status_code == 405

        # DELETE should not be allowed
        response = test_client.delete("/api/code-completion")
        assert response.status_code == 405

    # ============================================================================
    # REQUEST VALIDATION TESTS
    # ============================================================================

    def test_requires_file_path(self, test_client):
        """Test that file_path is required"""
        request = {"cursor_position": 100, "intent": "suggest"}
        response = test_client.post("/api/code-completion", json=request)
        assert response.status_code == 422  # Validation error
        assert "file_path" in response.text.lower()

    def test_requires_valid_intent(self, test_client):
        """Test that intent must be one of the valid options"""
        request = {
            "file_path": "/test/file.py",
            "cursor_position": 100,
            "intent": "invalid_intent",
        }
        response = test_client.post("/api/code-completion", json=request)
        assert response.status_code == 422

        # Valid intents should be accepted
        valid_intents = ["suggest", "explain", "refactor", "debug", "optimize"]
        for intent in valid_intents:
            request["intent"] = intent
            response = test_client.post("/api/code-completion", json=request)
            # Should not be a validation error (422)
            assert response.status_code != 422

    def test_cursor_position_defaults_to_zero(self, test_client):
        """Test that cursor_position defaults to 0 if not provided"""
        request = {"file_path": "/test/file.py", "intent": "suggest"}

        with patch("app.api.endpoints.code_completion.enhanced_agent") as mock_agent:
            mock_agent._mlx_suggest_code_tool.return_value = '{"status": "success"}'

            test_client.post("/api/code-completion", json=request)

            # Should call agent with cursor_position=0
            if mock_agent._mlx_suggest_code_tool.called:
                call_args = mock_agent._mlx_suggest_code_tool.call_args[0][0]
                request_data = json.loads(call_args)
                assert request_data.get("cursor_position") == 0

    def test_intent_defaults_to_suggest(self, test_client):
        """Test that intent defaults to 'suggest' if not provided"""
        request = {"file_path": "/test/file.py", "cursor_position": 100}

        mock_response = {
            "response": "Default suggestion response",
            "confidence": 0.8,
            "language": "python",
            "requires_review": False,
            "follow_up_actions": ["Add tests"],
            "model": "mlx-community/Qwen2.5-Coder-32B-Instruct",
            "context_used": {
                "file_path": "/test/file.py",
                "has_symbol_context": False,
                "language_detected": "python",
            },
        }

        with patch("app.api.endpoints.code_completion.enhanced_agent") as mock_agent:
            mock_agent._mlx_suggest_code_tool = AsyncMock(
                return_value=json.dumps(mock_response)
            )

            response = test_client.post("/api/code-completion", json=request)

            # Should use suggest as default intent
            assert response.status_code == 200

    # ============================================================================
    # INTENT-SPECIFIC ENDPOINT TESTS
    # ============================================================================

    @pytest.mark.asyncio
    async def test_suggest_intent_endpoint(
        self, async_client, sample_python_request, mock_enhanced_agent_response
    ):
        """Test suggest intent calls correct MLX tool"""
        sample_python_request["intent"] = "suggest"

        with patch("app.api.endpoints.code_completion.enhanced_agent") as mock_agent:
            mock_agent._mlx_suggest_code_tool = AsyncMock(
                return_value=json.dumps(mock_enhanced_agent_response)
            )

            response = await async_client.post(
                "/api/code-completion", json=sample_python_request
            )

            assert response.status_code == 200
            data = response.json()

            # Verify response structure
            assert data["status"] == "success"
            assert data["intent"] == "suggest"
            assert "response" in data
            assert "confidence" in data
            assert data["confidence"] == 0.85

            # Verify agent was called correctly
            mock_agent._mlx_suggest_code_tool.assert_called_once()

    @pytest.mark.asyncio
    async def test_explain_intent_endpoint(
        self, async_client, sample_javascript_request
    ):
        """Test explain intent calls correct MLX tool"""
        sample_javascript_request["intent"] = "explain"

        explain_response = {
            "explanation": "This async function fetches data from an API endpoint",
            "confidence": 0.9,
            "language": "javascript",
            "context_analyzed": {"has_symbol_context": True},
            "follow_up_suggestions": ["Add error handling"],
        }

        with patch("app.api.endpoints.code_completion.enhanced_agent") as mock_agent:
            mock_agent._mlx_explain_code_tool = AsyncMock(
                return_value=json.dumps(explain_response)
            )

            response = await async_client.post(
                "/api/code-completion", json=sample_javascript_request
            )

            assert response.status_code == 200
            data = response.json()

            assert data["status"] == "success"
            assert data["intent"] == "explain"
            assert "explanation" in data
            assert data["confidence"] == 0.9

            mock_agent._mlx_explain_code_tool.assert_called_once()

    @pytest.mark.asyncio
    async def test_refactor_intent_endpoint(self, async_client, sample_python_request):
        """Test refactor intent calls correct MLX tool"""
        sample_python_request["intent"] = "refactor"

        refactor_response = {
            "refactoring_suggestions": "Extract methods and add type hints",
            "confidence": 0.75,
            "language": "python",
            "requires_review": True,
            "next_steps": ["Test refactored code"],
        }

        with patch("app.api.endpoints.code_completion.enhanced_agent") as mock_agent:
            mock_agent._mlx_refactor_code_tool = AsyncMock(
                return_value=json.dumps(refactor_response)
            )

            response = await async_client.post(
                "/api/code-completion", json=sample_python_request
            )

            assert response.status_code == 200
            data = response.json()

            assert data["status"] == "success"
            assert data["intent"] == "refactor"
            assert "refactoring_suggestions" in data
            assert data["requires_review"] is True

            mock_agent._mlx_refactor_code_tool.assert_called_once()

    @pytest.mark.asyncio
    async def test_debug_intent_endpoint(self, async_client, sample_python_request):
        """Test debug intent calls correct MLX tool"""
        sample_python_request["intent"] = "debug"

        debug_response = {
            "debug_analysis": "Check for null pointer exceptions",
            "confidence": 0.65,
            "language": "python",
            "debugging_steps": ["Add logging", "Use debugger"],
        }

        with patch("app.api.endpoints.code_completion.enhanced_agent") as mock_agent:
            mock_agent._mlx_debug_code_tool = AsyncMock(
                return_value=json.dumps(debug_response)
            )

            response = await async_client.post(
                "/api/code-completion", json=sample_python_request
            )

            assert response.status_code == 200
            data = response.json()

            assert data["status"] == "success"
            assert data["intent"] == "debug"
            assert "debug_analysis" in data

            mock_agent._mlx_debug_code_tool.assert_called_once()

    @pytest.mark.asyncio
    async def test_optimize_intent_endpoint(self, async_client, sample_python_request):
        """Test optimize intent calls correct MLX tool"""
        sample_python_request["intent"] = "optimize"

        optimize_response = {
            "optimization_suggestions": "Use more efficient algorithms",
            "confidence": 0.7,
            "language": "python",
            "implementation_steps": ["Profile code", "Benchmark improvements"],
        }

        with patch("app.api.endpoints.code_completion.enhanced_agent") as mock_agent:
            mock_agent._mlx_optimize_code_tool = AsyncMock(
                return_value=json.dumps(optimize_response)
            )

            response = await async_client.post(
                "/api/code-completion", json=sample_python_request
            )

            assert response.status_code == 200
            data = response.json()

            assert data["status"] == "success"
            assert data["intent"] == "optimize"
            assert "optimization_suggestions" in data

            mock_agent._mlx_optimize_code_tool.assert_called_once()

    # ============================================================================
    # ERROR HANDLING TESTS
    # ============================================================================

    @pytest.mark.asyncio
    async def test_handles_agent_errors_gracefully(
        self, async_client, sample_python_request
    ):
        """Test endpoint handles agent errors gracefully"""
        with patch("app.api.endpoints.code_completion.enhanced_agent") as mock_agent:
            # Simulate agent error
            mock_agent._mlx_suggest_code_tool = AsyncMock(
                side_effect=Exception("Agent error")
            )

            response = await async_client.post(
                "/api/code-completion", json=sample_python_request
            )

            assert response.status_code == 500
            data = response.json()
            assert data["status"] == "error"
            assert "error" in data
            assert "Agent error" in data["error"]

    @pytest.mark.asyncio
    async def test_handles_invalid_agent_response(
        self, async_client, sample_python_request
    ):
        """Test endpoint handles invalid agent responses"""
        with patch("app.api.endpoints.code_completion.enhanced_agent") as mock_agent:
            # Return invalid JSON
            mock_agent._mlx_suggest_code_tool = AsyncMock(return_value="invalid json")

            response = await async_client.post(
                "/api/code-completion", json=sample_python_request
            )

            assert response.status_code == 500
            data = response.json()
            assert data["status"] == "error"
            assert "parse" in data["error"].lower() or "json" in data["error"].lower()

    @pytest.mark.asyncio
    async def test_handles_agent_error_responses(
        self, async_client, sample_python_request
    ):
        """Test endpoint handles agent error responses"""
        with patch("app.api.endpoints.code_completion.enhanced_agent") as mock_agent:
            # Return agent error response
            error_response = "Error: file_path required for code suggestions"
            mock_agent._mlx_suggest_code_tool = AsyncMock(return_value=error_response)

            response = await async_client.post(
                "/api/code-completion", json=sample_python_request
            )

            assert response.status_code == 400
            data = response.json()
            assert data["status"] == "error"
            assert "file_path required" in data["error"]

    # ============================================================================
    # RESPONSE FORMAT TESTS
    # ============================================================================

    @pytest.mark.asyncio
    async def test_response_includes_processing_time(
        self, async_client, sample_python_request, mock_enhanced_agent_response
    ):
        """Test response includes processing time"""
        with patch("app.api.endpoints.code_completion.enhanced_agent") as mock_agent:
            mock_agent._mlx_suggest_code_tool = AsyncMock(
                return_value=json.dumps(mock_enhanced_agent_response)
            )

            response = await async_client.post(
                "/api/code-completion", json=sample_python_request
            )

            assert response.status_code == 200
            data = response.json()

            assert "processing_time_ms" in data
            assert isinstance(data["processing_time_ms"], (int, float))
            assert data["processing_time_ms"] >= 0

    @pytest.mark.asyncio
    async def test_response_includes_all_required_fields(
        self, async_client, sample_python_request, mock_enhanced_agent_response
    ):
        """Test response includes all required fields"""
        with patch("app.api.endpoints.code_completion.enhanced_agent") as mock_agent:
            mock_agent._mlx_suggest_code_tool = AsyncMock(
                return_value=json.dumps(mock_enhanced_agent_response)
            )

            response = await async_client.post(
                "/api/code-completion", json=sample_python_request
            )

            assert response.status_code == 200
            data = response.json()

            # Required fields
            required_fields = [
                "status",
                "intent",
                "response",
                "confidence",
                "requires_review",
                "suggestions",
                "context_used",
                "processing_time_ms",
            ]

            for field in required_fields:
                assert field in data, f"Missing required field: {field}"

    @pytest.mark.asyncio
    async def test_confidence_score_in_valid_range(
        self, async_client, sample_python_request, mock_enhanced_agent_response
    ):
        """Test confidence score is in valid range (0.0-1.0)"""
        with patch("app.api.endpoints.code_completion.enhanced_agent") as mock_agent:
            mock_agent._mlx_suggest_code_tool = AsyncMock(
                return_value=json.dumps(mock_enhanced_agent_response)
            )

            response = await async_client.post(
                "/api/code-completion", json=sample_python_request
            )

            assert response.status_code == 200
            data = response.json()

            confidence = data["confidence"]
            assert isinstance(confidence, (int, float))
            assert 0.0 <= confidence <= 1.0

    # ============================================================================
    # CONTENT HANDLING TESTS
    # ============================================================================

    @pytest.mark.asyncio
    async def test_handles_file_content_in_request(
        self, async_client, sample_python_request, mock_enhanced_agent_response
    ):
        """Test endpoint handles file content in request"""
        # Add content to request
        sample_python_request["content"] = "def hello():\n    print('Hello, World!')"

        with patch("app.api.endpoints.code_completion.enhanced_agent") as mock_agent:
            mock_agent._mlx_suggest_code_tool = AsyncMock(
                return_value=json.dumps(mock_enhanced_agent_response)
            )

            response = await async_client.post(
                "/api/code-completion", json=sample_python_request
            )

            assert response.status_code == 200
            # Content should be passed to agent for context

    @pytest.mark.asyncio
    async def test_handles_language_parameter(
        self, async_client, sample_python_request, mock_enhanced_agent_response
    ):
        """Test endpoint handles language parameter"""
        sample_python_request["language"] = "python"

        with patch("app.api.endpoints.code_completion.enhanced_agent") as mock_agent:
            mock_agent._mlx_suggest_code_tool = AsyncMock(
                return_value=json.dumps(mock_enhanced_agent_response)
            )

            response = await async_client.post(
                "/api/code-completion", json=sample_python_request
            )

            assert response.status_code == 200
            data = response.json()

            # Language should be preserved in response
            assert (
                data.get("language") == "python"
                or data.get("context_used", {}).get("language") == "python"
            )

    # ============================================================================
    # PERFORMANCE TESTS
    # ============================================================================

    @pytest.mark.asyncio
    async def test_response_time_under_threshold(
        self, async_client, sample_python_request, mock_enhanced_agent_response
    ):
        """Test response time is under reasonable threshold"""
        with patch("app.api.endpoints.code_completion.enhanced_agent") as mock_agent:
            mock_agent._mlx_suggest_code_tool = AsyncMock(
                return_value=json.dumps(mock_enhanced_agent_response)
            )

            import time

            start_time = time.time()
            response = await async_client.post(
                "/api/code-completion", json=sample_python_request
            )
            end_time = time.time()

            assert response.status_code == 200

            # Should respond within 5 seconds (generous threshold for tests)
            response_time = end_time - start_time
            assert response_time < 5.0, f"Response took {response_time:.2f} seconds"

    # ============================================================================
    # EDGE CASE TESTS
    # ============================================================================

    @pytest.mark.asyncio
    async def test_handles_empty_file_path(self, async_client):
        """Test endpoint handles empty file path"""
        request = {"file_path": "", "cursor_position": 100, "intent": "suggest"}

        response = await async_client.post("/api/code-completion", json=request)

        # Should return validation error for empty file path
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_handles_negative_cursor_position(
        self, async_client, mock_enhanced_agent_response
    ):
        """Test endpoint handles negative cursor position"""
        request = {
            "file_path": "/test/file.py",
            "cursor_position": -1,
            "intent": "suggest",
        }

        with patch("app.api.endpoints.code_completion.enhanced_agent") as mock_agent:
            mock_agent._mlx_suggest_code_tool = AsyncMock(
                return_value=json.dumps(mock_enhanced_agent_response)
            )

            response = await async_client.post("/api/code-completion", json=request)

            # Should handle gracefully (negative position should be normalized to 0)
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_handles_very_large_cursor_position(
        self, async_client, mock_enhanced_agent_response
    ):
        """Test endpoint handles very large cursor position"""
        request = {
            "file_path": "/test/file.py",
            "cursor_position": 999999,
            "intent": "suggest",
        }

        with patch("app.api.endpoints.code_completion.enhanced_agent") as mock_agent:
            mock_agent._mlx_suggest_code_tool = AsyncMock(
                return_value=json.dumps(mock_enhanced_agent_response)
            )

            response = await async_client.post("/api/code-completion", json=request)

            # Should handle gracefully
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_handles_special_characters_in_file_path(
        self, async_client, mock_enhanced_agent_response
    ):
        """Test endpoint handles special characters in file path"""
        request = {
            "file_path": "/test/files with spaces/special-chars_123.py",
            "cursor_position": 100,
            "intent": "suggest",
        }

        with patch("app.api.endpoints.code_completion.enhanced_agent") as mock_agent:
            mock_agent._mlx_suggest_code_tool = AsyncMock(
                return_value=json.dumps(mock_enhanced_agent_response)
            )

            response = await async_client.post("/api/code-completion", json=request)

            assert response.status_code == 200

    # ============================================================================
    # CONCURRENT REQUEST TESTS
    # ============================================================================

    @pytest.mark.asyncio
    async def test_handles_concurrent_requests(
        self, async_client, sample_python_request, mock_enhanced_agent_response
    ):
        """Test endpoint handles multiple concurrent requests"""
        with patch("app.api.endpoints.code_completion.enhanced_agent") as mock_agent:
            mock_agent._mlx_suggest_code_tool = AsyncMock(
                return_value=json.dumps(mock_enhanced_agent_response)
            )

            # Create multiple concurrent requests
            requests = [
                async_client.post("/api/code-completion", json=sample_python_request)
                for _ in range(5)
            ]

            responses = await asyncio.gather(*requests)

            # All requests should succeed
            for response in responses:
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "success"
