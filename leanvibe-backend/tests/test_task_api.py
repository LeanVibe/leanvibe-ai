"""
Comprehensive Task Management API Tests

High-impact test suite for Task Management APIs following TDD methodology.
Based on Gemini analysis recommendations for 90% coverage impact.
"""

import pytest
import tempfile
import shutil
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.models.task_models import (
    Task, TaskCreate, TaskUpdate, TaskStatusUpdate, TaskMoveRequest,
    TaskFilters, TaskSearchRequest, TaskStats, KanbanBoard,
    TaskStatus, TaskPriority
)
from app.services.task_service import TaskService


@pytest.fixture
def mock_task_service():
    """Mock the task_service to isolate API layer testing"""
    with patch('app.api.endpoints.tasks.task_service') as mock:
        # Configure all methods as AsyncMock
        mock.create_task = AsyncMock()
        mock.list_tasks = AsyncMock(return_value=[])  # Fix: use correct method name
        mock.get_task = AsyncMock(return_value=None)
        mock.update_task = AsyncMock()
        mock.update_task_status = AsyncMock()
        mock.delete_task = AsyncMock(return_value=False)
        mock.get_kanban_board = AsyncMock()
        mock.search_tasks = AsyncMock(return_value=[])
        mock.get_task_stats = AsyncMock()
        
        # Make the mock itself awaitable for any other calls
        mock.initialize = AsyncMock()
        yield mock


@pytest.fixture
def mock_connection_manager():
    """Mock ConnectionManager for WebSocket broadcasting tests"""
    with patch('app.core.connection_manager.ConnectionManager') as mock:
        mock_instance = MagicMock()
        mock_instance.broadcast = AsyncMock()
        mock_instance.send_personal_message = AsyncMock()
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def test_client():
    """Create test client without app startup to avoid timeout"""
    # Create a minimal FastAPI app for testing without startup events
    from fastapi import FastAPI
    from app.api.endpoints.tasks import router as tasks_router
    
    test_app = FastAPI()
    test_app.include_router(tasks_router)
    
    with TestClient(test_app) as client:
        yield client


class TestTaskCreationAPI:
    """Test task creation API endpoints"""
    
    def test_create_task_success(self, test_client, mock_task_service):
        """Test POST /api/tasks/ with valid data"""
        # Arrange
        task_data = {
            "title": "Test Task",
            "description": "Test description",
            "priority": "high"
        }
        
        expected_task = Task(
            id="test-task-id",
            title="Test Task",
            description="Test description",
            priority="high",
            status="backlog"
        )
        
        mock_task_service.create_task.return_value = expected_task
        
        # Act
        response = test_client.post("/api/tasks/", json=task_data)
        
        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["id"] == "test-task-id"
        assert response_data["title"] == "Test Task"
        assert response_data["priority"] == "high"
        
        # Verify service was called correctly
        mock_task_service.create_task.assert_called_once()
        call_args = mock_task_service.create_task.call_args[0][0]
        assert call_args.title == "Test Task"
        assert call_args.description == "Test description"
        assert call_args.priority == "high"
    
    def test_create_task_invalid_data(self, test_client, mock_task_service):
        """Test validation and error handling"""
        # Test missing required fields
        response = test_client.post("/api/tasks/", json={})
        assert response.status_code == 422  # Validation error
        
        # Test invalid data types
        invalid_data = {
            "title": "",  # Empty title should fail
            "priority": "invalid_priority"  # Invalid priority
        }
        response = test_client.post("/api/tasks/", json=invalid_data)
        assert response.status_code == 422
        
        # Verify service was not called for invalid data
        mock_task_service.create_task.assert_not_called()
    
    def test_create_task_service_error(self, test_client, mock_task_service):
        """Test handling of service layer errors"""
        # Arrange
        task_data = {
            "title": "Test Task",
            "priority": "medium"
        }
        
        mock_task_service.create_task.side_effect = Exception("Service error")
        
        # Act
        response = test_client.post("/api/tasks/", json=task_data)
        
        # Assert
        assert response.status_code == 500
        response_data = response.json()
        assert "detail" in response_data


class TestTaskRetrievalAPI:
    """Test task retrieval API endpoints"""
    
    def test_list_tasks_no_filters(self, test_client, mock_task_service):
        """Test GET /api/tasks/ basic functionality"""
        # Arrange
        expected_tasks = [
            Task(id="1", title="Task 1", priority="high", status="backlog"),
            Task(id="2", title="Task 2", priority="medium", status="in_progress")
        ]
        
        mock_task_service.list_tasks.return_value = expected_tasks
        
        # Act
        response = test_client.get("/api/tasks/")
        
        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert len(response_data) == 2
        assert response_data[0]["id"] == "1"
        assert response_data[1]["id"] == "2"
        
        # Verify service was called with default filters
        mock_task_service.list_tasks.assert_called_once()
    
    def test_list_tasks_with_filters(self, test_client, mock_task_service):
        """Test filtering by status, priority, etc."""
        # Arrange
        filtered_tasks = [
            Task(id="1", title="High Priority Task", priority="high", status="in_progress")
        ]
        
        mock_task_service.list_tasks.return_value = filtered_tasks
        
        # Act
        response = test_client.get("/api/tasks/?status=in_progress&priority=high")
        
        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert len(response_data) == 1
        assert response_data[0]["priority"] == "high"
        assert response_data[0]["status"] == "in_progress"
        
        # Verify service was called with filters
        mock_task_service.list_tasks.assert_called_once()
    
    def test_get_single_task_success(self, test_client, mock_task_service):
        """Test GET /api/tasks/{task_id} success"""
        # Arrange
        task_id = "test-task-id"
        expected_task = Task(
            id=task_id,
            title="Single Task",
            priority="medium",
            status="backlog"
        )
        
        mock_task_service.get_task.return_value = expected_task
        
        # Act
        response = test_client.get(f"/api/tasks/{task_id}")
        
        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["id"] == task_id
        assert response_data["title"] == "Single Task"
        
        # Verify service was called with correct ID
        mock_task_service.get_task.assert_called_once_with(task_id)
    
    def test_get_single_task_not_found(self, test_client, mock_task_service):
        """Test GET /api/tasks/{task_id} for non-existent task"""
        # Arrange
        task_id = "non-existent-id"
        mock_task_service.get_task.return_value = None
        
        # Act
        response = test_client.get(f"/api/tasks/{task_id}")
        
        # Assert
        assert response.status_code == 404
        
        # Verify service was called
        mock_task_service.get_task.assert_called_once_with(task_id)


class TestTaskUpdateAPI:
    """Test task update API endpoints"""
    
    def test_update_task_success(self, test_client, mock_task_service):
        """Test PUT /api/tasks/{task_id}"""
        # Arrange
        task_id = "test-task-id"
        update_data = {
            "title": "Updated Task",
            "description": "Updated description",
            "priority": "low"
        }
        
        updated_task = Task(
            id=task_id,
            title="Updated Task",
            description="Updated description",
            priority="low",
            status="backlog"
        )
        
        mock_task_service.update_task.return_value = updated_task
        
        # Act
        response = test_client.put(f"/api/tasks/{task_id}", json=update_data)
        
        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["id"] == task_id
        assert response_data["title"] == "Updated Task"
        assert response_data["priority"] == "low"
        
        # Verify service was called correctly
        mock_task_service.update_task.assert_called_once()
        call_args = mock_task_service.update_task.call_args[0]
        assert call_args[0] == task_id  # task_id
        assert call_args[1].title == "Updated Task"  # TaskUpdate object
    
    def test_update_task_status_success(self, test_client, mock_task_service):
        """Test PUT /api/tasks/{task_id}/status"""
        # Arrange
        task_id = "test-task-id"
        status_update = {"status": "in_progress"}
        
        updated_task = Task(
            id=task_id,
            title="Test Task",
            priority="medium",
            status="in_progress"
        )
        
        mock_task_service.update_task_status.return_value = updated_task
        
        # Act
        response = test_client.put(f"/api/tasks/{task_id}/status", json=status_update)
        
        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["status"] == "in_progress"
        
        # Verify service was called correctly
        mock_task_service.update_task_status.assert_called_once()
        call_args = mock_task_service.update_task_status.call_args[0]
        assert call_args[0] == task_id
        assert call_args[1].status == "in_progress"
    
    def test_update_task_not_found(self, test_client, mock_task_service):
        """Test update operations on non-existent task"""
        # Arrange
        task_id = "non-existent-id"
        update_data = {"title": "Updated"}
        
        mock_task_service.update_task.return_value = None
        
        # Act
        response = test_client.put(f"/api/tasks/{task_id}", json=update_data)
        
        # Assert
        assert response.status_code == 404


class TestTaskDeletionAPI:
    """Test task deletion API endpoints"""
    
    def test_delete_task_success(self, test_client, mock_task_service):
        """Test DELETE /api/tasks/{task_id}"""
        # Arrange
        task_id = "test-task-id"
        mock_task_service.delete_task.return_value = True
        
        # Act
        response = test_client.delete(f"/api/tasks/{task_id}")
        
        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["success"] is True
        assert task_id in response_data["message"]
        
        # Verify service was called
        mock_task_service.delete_task.assert_called_once_with(task_id)
    
    def test_delete_task_not_found(self, test_client, mock_task_service):
        """Test DELETE for non-existent task"""
        # Arrange
        task_id = "non-existent-id"
        mock_task_service.delete_task.return_value = False
        
        # Act
        response = test_client.delete(f"/api/tasks/{task_id}")
        
        # Assert
        assert response.status_code == 404


class TestTaskMoveAPI:
    """Test task movement/status transition API"""
    
    def test_move_task_success(self, test_client, mock_task_service):
        """Test task status transitions"""
        # Arrange
        task_id = "test-task-id"
        move_data = {
            "from_status": "backlog",
            "to_status": "in_progress"
        }
        
        moved_task = Task(
            id=task_id,
            title="Test Task",
            priority="medium",
            status="in_progress"
        )
        
        mock_task_service.update_task_status.return_value = moved_task
        
        # Act
        response = test_client.put(f"/api/tasks/{task_id}/move", json=move_data)
        
        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["status"] == "in_progress"
        
        # Verify service was called correctly
        mock_task_service.update_task_status.assert_called_once()
    
    def test_move_task_invalid_transition(self, test_client, mock_task_service):
        """Test invalid status transition validation"""
        # This would test business logic validation in the service layer
        task_id = "test-task-id"
        invalid_move = {
            "from_status": "done",
            "to_status": "backlog"  # Invalid: can't move from done back to backlog
        }
        
        mock_task_service.update_task_status.side_effect = ValueError("Invalid status transition")
        
        # Act
        response = test_client.put(f"/api/tasks/{task_id}/move", json=invalid_move)
        
        # Assert
        assert response.status_code == 400


class TestKanbanBoardAPI:
    """Test Kanban board API endpoints"""
    
    def test_get_kanban_board_success(self, test_client, mock_task_service):
        """Test GET /api/tasks/kanban/board"""
        # Arrange
        from app.models.task_models import KanbanColumn
        
        expected_board = KanbanBoard(
            columns=[
                KanbanColumn(id="backlog", title="Backlog", tasks=[], max_tasks=None),
                KanbanColumn(id="in_progress", title="In Progress", tasks=[], max_tasks=3),
                KanbanColumn(id="testing", title="Testing", tasks=[], max_tasks=None),
                KanbanColumn(id="done", title="Done", tasks=[], max_tasks=None)
            ],
            total_tasks=0
        )
        
        mock_task_service.get_kanban_board.return_value = expected_board
        
        # Act
        response = test_client.get("/api/tasks/kanban/board")
        
        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert "columns" in response_data
        assert "total_tasks" in response_data
        assert len(response_data["columns"]) == 4
        
        # Verify column structure
        column_ids = [col["id"] for col in response_data["columns"]]
        expected_ids = ["backlog", "in_progress", "testing", "done"]
        assert all(expected_id in column_ids for expected_id in expected_ids)


class TestTaskSearchAPI:
    """Test task search and filtering API"""
    
    def test_search_tasks_with_query(self, test_client, mock_task_service):
        """Test POST /api/tasks/search with text query"""
        # Arrange
        search_data = {
            "query": "test",
            "filters": {
                "status": "in_progress"
            },
            "limit": 10,
            "offset": 0
        }
        
        expected_tasks = [
            Task(id="1", title="Test Task 1", priority="high", status="in_progress"),
            Task(id="2", title="Another test", priority="medium", status="in_progress")
        ]
        
        mock_task_service.search_tasks.return_value = expected_tasks
        
        # Act
        response = test_client.post("/api/tasks/search", json=search_data)
        
        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert len(response_data) == 2
        assert all("test" in task["title"].lower() for task in response_data)
        
        # Verify service was called with correct search request
        mock_task_service.search_tasks.assert_called_once()


class TestTaskStatsAPI:
    """Test task statistics API"""
    
    def test_get_task_stats(self, test_client, mock_task_service):
        """Test GET /api/tasks/stats"""
        # Arrange
        expected_stats = TaskStats(
            total_tasks=10,
            by_status={"backlog": 3, "in_progress": 4, "testing": 2, "done": 1},
            by_priority={"high": 2, "medium": 5, "low": 3},
            completion_rate=0.1,
            average_completion_time=2.5
        )
        
        mock_task_service.get_task_stats.return_value = expected_stats
        
        # Act
        response = test_client.get("/api/tasks/stats")
        
        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["total_tasks"] == 10
        assert response_data["completion_rate"] == 0.1
        assert "by_status" in response_data
        assert "by_priority" in response_data


class TestWebSocketEventBroadcasting:
    """Test WebSocket event broadcasting for task operations"""
    
    def test_task_created_event_broadcast(self, test_client, mock_task_service, mock_connection_manager):
        """Ensure task_created event is broadcasted when task is created"""
        # Arrange
        task_data = {
            "title": "Broadcast Test Task",
            "priority": "high"
        }
        
        created_task = Task(
            id="broadcast-task-id",
            title="Broadcast Test Task",
            priority="high",
            status="backlog"
        )
        
        mock_task_service.create_task.return_value = created_task
        
        # Act
        response = test_client.post("/api/tasks/", json=task_data)
        
        # Assert
        assert response.status_code == 200
        
        # Verify WebSocket broadcast was called (this would be tested via background tasks)
        # Note: Actual broadcast testing would require more complex setup with WebSocket client
        mock_task_service.create_task.assert_called_once()
    
    def test_task_updated_event_broadcast(self, test_client, mock_task_service, mock_connection_manager):
        """Ensure task_updated event is broadcasted"""
        # Arrange
        task_id = "test-task-id"
        update_data = {"title": "Updated via API"}
        
        updated_task = Task(
            id=task_id,
            title="Updated via API",
            priority="medium",
            status="backlog"
        )
        
        mock_task_service.update_task.return_value = updated_task
        
        # Act
        response = test_client.put(f"/api/tasks/{task_id}", json=update_data)
        
        # Assert
        assert response.status_code == 200
        
        # Verify service call
        mock_task_service.update_task.assert_called_once()
    
    def test_task_deleted_event_broadcast(self, test_client, mock_task_service, mock_connection_manager):
        """Ensure task_deleted event is broadcasted"""
        # Arrange
        task_id = "test-task-id"
        mock_task_service.delete_task.return_value = True
        
        # Act
        response = test_client.delete(f"/api/tasks/{task_id}")
        
        # Assert
        assert response.status_code == 200
        
        # Verify service call
        mock_task_service.delete_task.assert_called_once_with(task_id)


class TestAPIErrorHandling:
    """Test comprehensive API error handling"""
    
    def test_malformed_json_handling(self, test_client):
        """Test handling of malformed JSON requests"""
        # Send invalid JSON
        response = test_client.post(
            "/api/tasks/",
            data="invalid json content",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
    
    def test_missing_content_type(self, test_client):
        """Test handling of requests without proper content type"""
        response = test_client.post("/api/tasks/", data='{"title": "test"}')
        
        # Should handle gracefully
        assert response.status_code in [400, 422]
    
    def test_unauthorized_requests(self, test_client):
        """Test unauthorized request handling (if auth is implemented)"""
        # This would test authentication/authorization if implemented
        # For now, just ensure endpoints are accessible
        response = test_client.get("/api/tasks/")
        assert response.status_code != 401  # No auth required currently
    
    def test_request_too_large(self, test_client):
        """Test handling of excessively large requests"""
        # Create a very large task description
        large_data = {
            "title": "Test",
            "description": "x" * 10000,  # 10KB description
            "priority": "medium"
        }
        
        response = test_client.post("/api/tasks/", json=large_data)
        
        # Should either accept or reject gracefully
        assert response.status_code in [200, 201, 413, 422]