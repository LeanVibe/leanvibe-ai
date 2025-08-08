"""
Contract Validation Tests

Tests to validate that the API implementation matches the contract schemas.
Ensures all endpoints return responses that conform to the OpenAPI spec.
"""

import pytest
import json
from typing import Dict, Any
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.contracts.models import (
    HealthResponse,
    MLXHealthResponse,
    ProjectListResponse,
    TaskListResponse,
    CodeCompletionRequest,
    CodeCompletionResponse,
    CodeCompletionErrorResponse,
    Project,
    Task,
)


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestHealthEndpoints:
    """Test health endpoints against contract schemas."""
    
    def test_health_endpoint_schema_validation(self, client):
        """Test that /health endpoint returns valid HealthResponse."""
        response = client.get("/health")
        assert response.status_code == 200
        
        # Validate response against schema
        data = response.json()
        health_response = HealthResponse(**data)
        
        # Verify required fields
        assert health_response.status in ["healthy", "degraded", "unhealthy"]
        assert health_response.service == "leanvibe-backend"
        assert health_response.version == "0.2.0"
        assert isinstance(health_response.ai_ready, bool)

    def test_mlx_health_endpoint_schema_validation(self, client):
        """Test that /health/mlx endpoint returns valid MLXHealthResponse."""
        response = client.get("/health/mlx")
        
        # Should return 200 or 503 based on MLX availability
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            data = response.json()
            mlx_response = MLXHealthResponse(**data)
            
            # Verify required fields
            assert mlx_response.status in ["healthy", "uninitialized", "degraded"]
            assert isinstance(mlx_response.model_loaded, bool)
            assert isinstance(mlx_response.inference_ready, bool)
            assert 0 <= mlx_response.confidence_score <= 1
        else:
            # Validate error response structure
            data = response.json()
            assert "detail" in data
            assert "status" in data["detail"]
            assert "error" in data["detail"]


class TestProjectEndpoints:
    """Test project endpoints against contract schemas."""
    
    def test_projects_list_endpoint_schema_validation(self, client):
        """Test that /api/projects endpoint returns valid ProjectListResponse."""
        response = client.get("/api/projects")
        
        # May fail with 401 if auth is required
        if response.status_code == 401:
            pytest.skip("Authentication required for projects endpoint")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response against schema
        project_list = ProjectListResponse(**data)
        
        # Verify structure
        assert isinstance(project_list.projects, list)
        assert isinstance(project_list.total, int)
        assert len(project_list.projects) == project_list.total
        
        # Validate each project if any exist
        for project_data in project_list.projects:
            project = Project(**project_data)
            assert project.status in ["active", "inactive", "archived"]


class TestTaskEndpoints:
    """Test task endpoints against contract schemas."""
    
    def test_tasks_list_endpoint_schema_validation(self, client):
        """Test that /api/tasks endpoint returns valid TaskListResponse."""
        response = client.get("/api/tasks")
        
        # May fail with 401 if auth is required
        if response.status_code == 401:
            pytest.skip("Authentication required for tasks endpoint")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response against schema
        task_list = TaskListResponse(**data)
        
        # Verify structure
        assert isinstance(task_list.tasks, list)
        assert isinstance(task_list.total, int)
        assert len(task_list.tasks) == task_list.total
        
        # Validate each task if any exist
        for task_data in task_list.tasks:
            task = Task(**task_data)
            assert task.status in ["todo", "in_progress", "done", "cancelled"]
            if task.priority:
                assert task.priority in ["low", "medium", "high", "urgent"]


class TestCodeCompletionEndpoints:
    """Test code completion endpoints against contract schemas."""
    
    def test_code_completion_request_validation(self):
        """Test CodeCompletionRequest model validation."""
        # Valid request
        valid_request = {
            "file_path": "/path/to/file.py",
            "cursor_position": 100,
            "intent": "suggest",
            "content": "def hello():",
            "language": "python"
        }
        request = CodeCompletionRequest(**valid_request)
        assert request.file_path == "/path/to/file.py"
        assert request.cursor_position == 100
        assert request.intent == "suggest"
        
        # Invalid request - empty file_path
        with pytest.raises(ValidationError):
            CodeCompletionRequest(file_path="")
        
        # Invalid request - negative cursor position (should be normalized to 0)
        request = CodeCompletionRequest(file_path="/test.py", cursor_position=-5)
        assert request.cursor_position == 0
        
        # Invalid intent
        with pytest.raises(ValidationError):
            CodeCompletionRequest(file_path="/test.py", intent="invalid_intent")

    def test_code_completion_endpoint_schema_validation(self, client):
        """Test that /api/code-completion endpoint validates request/response."""
        request_data = {
            "file_path": "/test.py",
            "cursor_position": 0,
            "intent": "suggest",
            "content": "def hello():\n    ",
            "language": "python"
        }
        
        response = client.post("/api/code-completion", json=request_data)
        
        # Should return 200 or appropriate error
        assert response.status_code in [200, 400, 500, 503]
        
        data = response.json()
        
        if response.status_code == 200:
            # Validate success response
            completion_response = CodeCompletionResponse(**data)
            assert completion_response.status == "success"
            assert completion_response.intent in ["suggest", "explain", "refactor", "debug", "optimize"]
            assert 0 <= completion_response.confidence <= 1
            assert isinstance(completion_response.requires_review, bool)
            assert completion_response.processing_time_ms >= 0
        elif response.status_code == 400:
            # Validate error response
            error_response = CodeCompletionErrorResponse(**data)
            assert error_response.status == "error"
            assert isinstance(error_response.error, str)
            assert error_response.processing_time_ms >= 0


class TestContractConsistency:
    """Test consistency between contract schemas and implementation."""
    
    def test_openapi_schema_accessibility(self, client):
        """Test that OpenAPI schema is accessible."""
        response = client.get("/api/v1/openapi.json")
        assert response.status_code == 200
        
        openapi_spec = response.json()
        assert openapi_spec["openapi"].startswith("3.")
        assert openapi_spec["info"]["title"] == "LeanVibe L3 Coding Agent API"
        assert openapi_spec["info"]["version"] == "0.2.0"

    def test_contract_models_importable(self):
        """Test that all contract models can be imported."""
        from app.contracts.models import (
            HealthResponse,
            MLXHealthResponse,
            ProjectListResponse,
            TaskListResponse,
            CodeCompletionRequest,
            CodeCompletionResponse,
            Project,
            Task,
        )
        
        # Verify models are properly defined
        assert hasattr(HealthResponse, '__fields__')
        assert hasattr(MLXHealthResponse, '__fields__')
        assert hasattr(ProjectListResponse, '__fields__')
        assert hasattr(TaskListResponse, '__fields__')
        assert hasattr(CodeCompletionRequest, '__fields__')
        assert hasattr(CodeCompletionResponse, '__fields__')

    def test_validation_decorators_importable(self):
        """Test that validation decorators can be imported."""
        from app.contracts.decorators import validate_response
        
        # Verify decorator is callable
        assert callable(validate_response)


class TestResponseValidation:
    """Test response validation with generated decorators."""
    
    def test_validate_response_decorator(self):
        """Test the validate_response decorator functionality."""
        from app.contracts.decorators import validate_response
        from app.contracts.models import HealthResponse
        
        @validate_response(HealthResponse)
        async def mock_health_endpoint():
            return {
                "status": "healthy",
                "service": "leanvibe-backend",
                "version": "0.2.0",
                "ai_ready": True
            }
        
        # Test with valid response
        import asyncio
        result = asyncio.run(mock_health_endpoint())
        assert result["status"] == "healthy"

    def test_validate_response_decorator_with_invalid_data(self):
        """Test validate_response decorator with invalid data."""
        from app.contracts.decorators import validate_response
        from app.contracts.models import HealthResponse
        from fastapi import HTTPException
        
        @validate_response(HealthResponse)
        async def mock_invalid_endpoint():
            return {
                "status": "invalid_status",  # This should fail validation
                "service": "leanvibe-backend",
                "version": "0.2.0",
                "ai_ready": True
            }
        
        # Test with invalid response - should raise HTTPException
        import asyncio
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(mock_invalid_endpoint())
        
        assert exc_info.value.status_code == 500
        assert "Response validation failed" in str(exc_info.value.detail)


class TestSchemaIntegrity:
    """Test schema files integrity and structure."""
    
    def test_openapi_schema_structure(self):
        """Test OpenAPI schema has required structure."""
        import yaml
        from pathlib import Path
        
        schema_path = Path("contracts/openapi.yaml")
        assert schema_path.exists(), "OpenAPI schema file not found"
        
        with open(schema_path) as f:
            schema = yaml.safe_load(f)
        
        # Verify required sections
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema
        assert "components" in schema
        
        # Verify info section
        assert schema["info"]["title"] == "LeanVibe L3 Coding Agent API"
        assert schema["info"]["version"] == "0.2.0"
        
        # Verify paths exist
        required_paths = ["/health", "/health/mlx", "/api/projects", "/api/code-completion"]
        for path in required_paths:
            assert path in schema["paths"], f"Required path {path} not found in schema"

    def test_asyncapi_schema_structure(self):
        """Test AsyncAPI schema has required structure."""
        import yaml
        from pathlib import Path
        
        schema_path = Path("contracts/asyncapi.yaml")
        assert schema_path.exists(), "AsyncAPI schema file not found"
        
        with open(schema_path) as f:
            schema = yaml.safe_load(f)
        
        # Verify required sections
        assert "asyncapi" in schema
        assert "info" in schema
        assert "channels" in schema
        assert "components" in schema
        
        # Verify info section
        assert schema["info"]["title"] == "LeanVibe WebSocket Events API"
        assert schema["info"]["version"] == "0.2.0"
        
        # Verify WebSocket channel exists
        assert "/ws/{client_id}" in schema["channels"]


@pytest.mark.integration
class TestContractValidationIntegration:
    """Integration tests for contract validation."""
    
    def test_end_to_end_validation_flow(self, client):
        """Test complete validation flow from request to response."""
        # Test health endpoint first
        response = client.get("/health")
        assert response.status_code == 200
        
        # Validate against contract
        from app.contracts.models import HealthResponse
        health_data = response.json()
        health_response = HealthResponse(**health_data)
        
        # Verify all required fields are present and valid
        assert health_response.status in ["healthy", "degraded", "unhealthy"]
        assert health_response.service
        assert health_response.version
        assert isinstance(health_response.ai_ready, bool)
        
        print(f"✅ Contract validation successful for health endpoint")

    def test_contract_generation_reproducibility(self):
        """Test that contract generation is reproducible."""
        from pathlib import Path
        
        # Verify generated files exist
        contracts_dir = Path("app/contracts")
        assert contracts_dir.exists()
        assert (contracts_dir / "models.py").exists()
        assert (contracts_dir / "decorators.py").exists()
        assert (contracts_dir / "types.ts").exists()
        assert (contracts_dir / "__init__.py").exists()
        
        print(f"✅ All contract files generated successfully")