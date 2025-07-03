"""
Comprehensive test suite for Project API endpoints

Tests the agent-developed project management APIs that are critical
for iOS app functionality and represent the largest coverage gap.
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import UUID

import httpx
from fastapi.testclient import TestClient

from app.main import app
from app.models.project_models import (
    Project,
    ProjectListResponse,
    ProjectMetrics,
    ProjectMetricsResponse,
    ProjectTask,
    ProjectTasksResponse,
    ProjectLanguage,
    ProjectStatus,
)


# Test client setup
client = TestClient(app)


class TestProjectAPIEndpoints:
    """Test suite for project API endpoints developed by agents"""

    @pytest.fixture
    def sample_project_id(self):
        """Sample project UUID for testing"""
        return uuid.uuid4()

    @pytest.fixture
    def sample_project(self, sample_project_id):
        """Sample project data for testing"""
        now = datetime.now()
        return Project(
            id=sample_project_id,
            display_name="Test Project",
            description="A test project for API validation",
            path="/path/to/test/project",
            language=ProjectLanguage.PYTHON,
            status=ProjectStatus.ACTIVE,
            tasks_count=5,
            completed_tasks_count=3,
            issues_count=2,
            created_at=now,
            updated_at=now,
            last_activity=now,
            metrics=ProjectMetrics(
                files_count=50,
                lines_of_code=1500,
                health_score=0.85,
                issues_count=2,
                test_coverage=0.78
            ),
            client_id="test-client"
        )

    @pytest.fixture
    def sample_projects_list(self, sample_project):
        """Sample list of projects for testing"""
        now = datetime.now()
        project2 = Project(
            id=uuid.uuid4(),
            display_name="Another Project",
            description="Second test project",
            path="/path/to/another/project",
            language=ProjectLanguage.JAVASCRIPT,
            status=ProjectStatus.ACTIVE,
            tasks_count=8,
            completed_tasks_count=6,
            issues_count=1,
            created_at=now,
            updated_at=now,
            last_activity=now,
            metrics=ProjectMetrics(
                files_count=80,
                lines_of_code=2300,
                health_score=0.92,
                issues_count=1,
                test_coverage=0.85
            ),
            client_id="test-client-2"
        )
        return [sample_project, project2]

    @pytest.fixture
    def sample_metrics(self, sample_project_id):
        """Sample project metrics for testing"""
        return ProjectMetrics(
            files_count=50,
            lines_of_code=1500,
            test_coverage=0.78,
            health_score=0.85,
            issues_count=2,
            last_build_time=45.2,
            performance_score=0.92
        )

    @pytest.fixture
    def sample_tasks(self, sample_project_id):
        """Sample project tasks for testing"""
        now = datetime.now()
        return [
            ProjectTask(
                id=uuid.uuid4(),
                project_id=sample_project_id,
                title="Fix critical bug",
                description="Fix authentication issue",
                status="in_progress",
                priority="high",
                created_at=now,
                updated_at=now
            ),
            ProjectTask(
                id=uuid.uuid4(),
                project_id=sample_project_id,
                title="Add feature",
                description="Implement new dashboard",
                status="todo",
                priority="medium",
                created_at=now,
                updated_at=now
            )
        ]

    # Test GET /api/projects/ - List all projects
    @patch('app.services.project_service.ProjectService.get_all_projects')
    def test_list_projects_success(self, mock_get_all, sample_projects_list):
        """Test successful project listing"""
        # Arrange
        mock_get_all.return_value = sample_projects_list

        # Act
        response = client.get("/api/projects/")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "projects" in data
        assert "total" in data
        assert data["total"] == 2
        assert len(data["projects"]) == 2
        assert data["projects"][0]["display_name"] == "Test Project"
        assert data["projects"][1]["language"] == "JavaScript"

    @patch('app.services.project_service.ProjectService.get_all_projects')
    def test_list_projects_empty(self, mock_get_all):
        """Test project listing when no projects exist"""
        # Arrange
        mock_get_all.return_value = []

        # Act
        response = client.get("/api/projects/")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["projects"] == []

    @patch('app.services.project_service.ProjectService.get_all_projects')
    def test_list_projects_service_error(self, mock_get_all):
        """Test project listing when service raises exception"""
        # Arrange
        mock_get_all.side_effect = Exception("Database connection failed")

        # Act
        response = client.get("/api/projects/")

        # Assert
        assert response.status_code == 500
        assert "Failed to retrieve projects" in response.json()["detail"]

    # Test GET /api/projects/{project_id} - Get specific project
    @patch('app.services.project_service.ProjectService.get_project')
    def test_get_project_success(self, mock_get_project, sample_project, sample_project_id):
        """Test successful project retrieval by ID"""
        # Arrange
        mock_get_project.return_value = sample_project

        # Act
        response = client.get(f"/api/projects/{sample_project_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sample_project_id)
        assert data["name"] == "Test Project"
        assert data["language"] == "python"
        assert data["health_score"] == 0.85

    @patch('app.services.project_service.ProjectService.get_project')
    def test_get_project_not_found(self, mock_get_project):
        """Test project retrieval when project doesn't exist"""
        # Arrange
        project_id = uuid.uuid4()
        mock_get_project.return_value = None

        # Act
        response = client.get(f"/api/projects/{project_id}")

        # Assert
        assert response.status_code == 404
        assert "Project not found" in response.json()["detail"]

    def test_get_project_invalid_uuid(self):
        """Test project retrieval with invalid UUID format"""
        # Act
        response = client.get("/api/projects/invalid-uuid")

        # Assert
        assert response.status_code == 422  # Pydantic validation error

    @patch('app.services.project_service.ProjectService.get_project')
    def test_get_project_service_error(self, mock_get_project):
        """Test project retrieval when service raises exception"""
        # Arrange
        project_id = uuid.uuid4()
        mock_get_project.side_effect = Exception("Service unavailable")

        # Act
        response = client.get(f"/api/projects/{project_id}")

        # Assert
        assert response.status_code == 500
        assert "Failed to retrieve project" in response.json()["detail"]

    # Test GET /api/projects/{project_id}/tasks - Get project tasks
    @patch('app.services.project_service.ProjectService.get_project')
    @patch('app.services.project_service.ProjectService.get_project_tasks')
    def test_get_project_tasks_success(self, mock_get_tasks, mock_get_project, 
                                     sample_project, sample_tasks, sample_project_id):
        """Test successful project tasks retrieval"""
        # Arrange
        mock_get_project.return_value = sample_project
        mock_get_tasks.return_value = sample_tasks

        # Act
        response = client.get(f"/api/projects/{sample_project_id}/tasks")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data
        assert "total" in data
        assert "project_id" in data
        assert data["total"] == 2
        assert data["project_id"] == str(sample_project_id)
        assert len(data["tasks"]) == 2
        assert data["tasks"][0]["priority"] == "high"
        assert data["tasks"][1]["status"] == "todo"

    @patch('app.services.project_service.ProjectService.get_project')
    def test_get_project_tasks_project_not_found(self, mock_get_project):
        """Test project tasks retrieval when project doesn't exist"""
        # Arrange
        project_id = uuid.uuid4()
        mock_get_project.return_value = None

        # Act
        response = client.get(f"/api/projects/{project_id}/tasks")

        # Assert
        assert response.status_code == 404
        assert "Project not found" in response.json()["detail"]

    @patch('app.services.project_service.ProjectService.get_project')
    @patch('app.services.project_service.ProjectService.get_project_tasks')
    def test_get_project_tasks_empty(self, mock_get_tasks, mock_get_project, 
                                   sample_project, sample_project_id):
        """Test project tasks retrieval when no tasks exist"""
        # Arrange
        mock_get_project.return_value = sample_project
        mock_get_tasks.return_value = []

        # Act
        response = client.get(f"/api/projects/{sample_project_id}/tasks")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["tasks"] == []

    # Test GET /api/projects/{project_id}/metrics - Get project metrics
    @patch('app.services.project_service.ProjectService.get_project')
    @patch('app.services.project_service.ProjectService.get_project_metrics')
    def test_get_project_metrics_success(self, mock_get_metrics, mock_get_project,
                                       sample_project, sample_metrics, sample_project_id):
        """Test successful project metrics retrieval"""
        # Arrange
        mock_get_project.return_value = sample_project
        mock_get_metrics.return_value = sample_metrics

        # Act
        response = client.get(f"/api/projects/{sample_project_id}/metrics")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data
        assert "project_id" in data
        assert "updated_at" in data
        assert data["project_id"] == str(sample_project_id)
        assert data["metrics"]["lines_of_code"] == 1500
        assert data["metrics"]["test_coverage"] == 0.78
        assert data["metrics"]["code_quality_score"] == 0.85

    @patch('app.services.project_service.ProjectService.get_project')
    def test_get_project_metrics_project_not_found(self, mock_get_project):
        """Test project metrics retrieval when project doesn't exist"""
        # Arrange
        project_id = uuid.uuid4()
        mock_get_project.return_value = None

        # Act
        response = client.get(f"/api/projects/{project_id}/metrics")

        # Assert
        assert response.status_code == 404
        assert "Project not found" in response.json()["detail"]

    # Test POST /api/projects/{project_id}/analyze - Analyze project
    @patch('app.services.project_service.ProjectService.get_project')
    @patch('app.services.project_service.ProjectService.analyze_project')
    def test_analyze_project_success(self, mock_analyze, mock_get_project,
                                   sample_project, sample_project_id):
        """Test successful project analysis"""
        # Arrange
        mock_get_project.return_value = sample_project
        mock_analyze.return_value = {
            "status": "completed",
            "findings": {
                "issues_found": 3,
                "improvements_suggested": 5,
                "overall_health": 0.87
            }
        }

        # Act
        response = client.post(f"/api/projects/{sample_project_id}/analyze")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["project_id"] == str(sample_project_id)
        assert "analysis" in data
        assert "timestamp" in data
        assert data["analysis"]["findings"]["issues_found"] == 3

    @patch('app.services.project_service.ProjectService.get_project')
    def test_analyze_project_not_found(self, mock_get_project):
        """Test project analysis when project doesn't exist"""
        # Arrange
        project_id = uuid.uuid4()
        mock_get_project.return_value = None

        # Act
        response = client.post(f"/api/projects/{project_id}/analyze")

        # Assert
        assert response.status_code == 404
        assert "Project not found" in response.json()["detail"]

    @patch('app.services.project_service.ProjectService.get_project')
    @patch('app.services.project_service.ProjectService.analyze_project')
    def test_analyze_project_analysis_error(self, mock_analyze, mock_get_project,
                                          sample_project, sample_project_id):
        """Test project analysis when analysis service fails"""
        # Arrange
        mock_get_project.return_value = sample_project
        mock_analyze.side_effect = Exception("Analysis service unavailable")

        # Act
        response = client.post(f"/api/projects/{sample_project_id}/analyze")

        # Assert
        assert response.status_code == 500
        assert "Failed to analyze project" in response.json()["detail"]

    # Test DELETE /api/projects/{project_id} - Delete project
    @patch('app.services.project_service.ProjectService.get_project')
    @patch('app.services.project_service.ProjectService.delete_project')
    def test_delete_project_success(self, mock_delete, mock_get_project,
                                  sample_project, sample_project_id):
        """Test successful project deletion"""
        # Arrange
        mock_get_project.return_value = sample_project
        mock_delete.return_value = True

        # Act
        response = client.delete(f"/api/projects/{sample_project_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["message"] == "Project deleted successfully"
        assert data["project_id"] == str(sample_project_id)

    @patch('app.services.project_service.ProjectService.get_project')
    def test_delete_project_not_found(self, mock_get_project):
        """Test project deletion when project doesn't exist"""
        # Arrange
        project_id = uuid.uuid4()
        mock_get_project.return_value = None

        # Act
        response = client.delete(f"/api/projects/{project_id}")

        # Assert
        assert response.status_code == 404
        assert "Project not found" in response.json()["detail"]

    @patch('app.services.project_service.ProjectService.get_project')
    @patch('app.services.project_service.ProjectService.delete_project')
    def test_delete_project_deletion_failed(self, mock_delete, mock_get_project,
                                          sample_project, sample_project_id):
        """Test project deletion when deletion service fails"""
        # Arrange
        mock_get_project.return_value = sample_project
        mock_delete.return_value = False

        # Act
        response = client.delete(f"/api/projects/{sample_project_id}")

        # Assert
        assert response.status_code == 500
        assert "Failed to delete project" in response.json()["detail"]

    # Edge Cases and Error Handling Tests
    def test_all_endpoints_invalid_uuid_format(self):
        """Test all endpoints with invalid UUID format"""
        invalid_uuid = "not-a-uuid"
        
        endpoints = [
            ("GET", f"/api/projects/{invalid_uuid}"),
            ("GET", f"/api/projects/{invalid_uuid}/tasks"),
            ("GET", f"/api/projects/{invalid_uuid}/metrics"),
            ("POST", f"/api/projects/{invalid_uuid}/analyze"),
            ("DELETE", f"/api/projects/{invalid_uuid}")
        ]
        
        for method, endpoint in endpoints:
            if method == "GET":
                response = client.get(endpoint)
            elif method == "POST":
                response = client.post(endpoint)
            elif method == "DELETE":
                response = client.delete(endpoint)
            
            assert response.status_code == 422, f"Failed for {method} {endpoint}"

    @patch('app.services.project_service.ProjectService.get_all_projects')
    def test_concurrent_access_simulation(self, mock_get_all, sample_projects_list):
        """Test API behavior under concurrent access (simulation)"""
        # Arrange
        mock_get_all.return_value = sample_projects_list

        # Act - Simulate concurrent requests
        responses = []
        for _ in range(5):
            response = client.get("/api/projects/")
            responses.append(response)

        # Assert - All should succeed
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 2

    def test_api_response_format_consistency(self, sample_project_id):
        """Test that all API responses follow consistent format"""
        # This test ensures consistent error response format
        endpoints = [
            f"/api/projects/{sample_project_id}",
            f"/api/projects/{sample_project_id}/tasks",
            f"/api/projects/{sample_project_id}/metrics"
        ]
        
        for endpoint in endpoints:
            with patch('app.services.project_service.ProjectService.get_project', return_value=None):
                response = client.get(endpoint)
                assert response.status_code == 404
                data = response.json()
                assert "detail" in data
                assert isinstance(data["detail"], str)


# Performance and Integration Tests
class TestProjectAPIPerformance:
    """Performance tests for project API endpoints"""

    @patch('app.services.project_service.ProjectService.get_all_projects')
    def test_large_project_list_performance(self, mock_get_all):
        """Test API performance with large number of projects"""
        # Arrange - Create 100 mock projects
        large_project_list = []
        for i in range(100):
            project = Project(
                id=uuid.uuid4(),
                name=f"Project {i}",
                description=f"Test project {i}",
                path=f"/path/to/project{i}",
                language=ProjectLanguage.PYTHON,
                status=ProjectStatus.ACTIVE,
                health_score=0.8 + (i % 20) * 0.01,
                lines_of_code=1000 + i * 10,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            large_project_list.append(project)
        
        mock_get_all.return_value = large_project_list

        # Act
        import time
        start_time = time.time()
        response = client.get("/api/projects/")
        end_time = time.time()

        # Assert
        assert response.status_code == 200
        assert len(response.json()["projects"]) == 100
        # Performance assertion - should complete within 1 second
        assert (end_time - start_time) < 1.0

    @patch('app.services.project_service.ProjectService.get_project')
    @patch('app.services.project_service.ProjectService.get_project_tasks')
    def test_large_task_list_performance(self, mock_get_tasks, mock_get_project):
        """Test API performance with large number of tasks"""
        # Arrange
        project_id = uuid.uuid4()
        sample_project = Project(
            id=project_id,
            name="Test Project",
            description="Test",
            path="/test",
            language=ProjectLanguage.PYTHON,
            status=ProjectStatus.ACTIVE,
            health_score=0.85,
            lines_of_code=1500,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Create 50 mock tasks
        large_task_list = []
        for i in range(50):
            task = ProjectTask(
                id=uuid.uuid4(),
                project_id=project_id,
                title=f"Task {i}",
                description=f"Description for task {i}",
                status="todo" if i % 2 == 0 else "in_progress",
                priority="high" if i % 3 == 0 else "medium",
                created_at=datetime.now()
            )
            large_task_list.append(task)
        
        mock_get_project.return_value = sample_project
        mock_get_tasks.return_value = large_task_list

        # Act
        import time
        start_time = time.time()
        response = client.get(f"/api/projects/{project_id}/tasks")
        end_time = time.time()

        # Assert
        assert response.status_code == 200
        assert len(response.json()["tasks"]) == 50
        # Performance assertion
        assert (end_time - start_time) < 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])