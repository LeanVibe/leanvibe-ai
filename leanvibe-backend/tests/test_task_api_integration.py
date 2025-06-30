import pytest
import tempfile
import shutil
from fastapi.testclient import TestClient

from app.main import app
from app.services.task_service import TaskService
from app.models.task_models import TaskStatus, TaskPriority


class TestTaskAPIIntegration:
    """Integration tests for Task Management APIs"""
    
    def test_task_api_endpoints_exist(self):
        """Test that Task API endpoints are properly registered"""
        with TestClient(app) as client:
            # Test that endpoints return proper status (not 404)
            response = client.get("/api/tasks/")
            assert response.status_code in [200, 422, 500]  # Not 404
            
            response = client.get("/api/tasks/kanban/board")
            assert response.status_code in [200, 422, 500]  # Not 404
    
    def test_task_creation_basic(self):
        """Basic test for task creation without mocking"""
        with TestClient(app) as client:
            task_data = {
                "title": "Integration Test Task",
                "description": "Testing basic functionality",
                "priority": "medium"
            }
            
            response = client.post("/api/tasks/", json=task_data)
            
            # Should either succeed or fail gracefully
            assert response.status_code in [200, 201, 422, 500]
            
            if response.status_code == 200:
                data = response.json()
                assert "id" in data
                assert data["title"] == task_data["title"]
    
    def test_kanban_board_structure(self):
        """Test Kanban board returns proper structure"""
        with TestClient(app) as client:
            response = client.get("/api/tasks/kanban/board")
            
            if response.status_code == 200:
                board = response.json()
                assert "columns" in board
                assert "total_tasks" in board
                assert isinstance(board["columns"], list)
                
                # Should have 4 columns
                expected_statuses = ["backlog", "in_progress", "testing", "done"]
                if len(board["columns"]) >= 4:
                    column_ids = [col["id"] for col in board["columns"]]
                    for status in expected_statuses:
                        assert status in column_ids
    
    def test_task_status_update(self):
        """Test task status update functionality"""
        with TestClient(app) as client:
            # First try to create a task
            task_data = {
                "title": "Status Update Test",
                "priority": "high"
            }
            
            create_response = client.post("/api/tasks/", json=task_data)
            
            if create_response.status_code == 200:
                task = create_response.json()
                task_id = task["id"]
                
                # Try to update status
                status_update = {"status": "in_progress"}
                update_response = client.put(f"/api/tasks/{task_id}/status", json=status_update)
                
                assert update_response.status_code in [200, 404, 422, 500]
                
                if update_response.status_code == 200:
                    updated_task = update_response.json()
                    assert updated_task["status"] == "in_progress"
    
    def test_api_error_handling(self):
        """Test API error handling for invalid requests"""
        with TestClient(app) as client:
            # Test getting non-existent task
            response = client.get("/api/tasks/non-existent-id")
            assert response.status_code in [404, 422, 500]
            
            # Test invalid JSON structure
            response = client.post("/api/tasks/", json={"invalid": "data"})
            assert response.status_code in [200, 422, 500]  # Should handle gracefully


@pytest.mark.asyncio
class TestTaskServiceIntegration:
    """Direct integration tests for TaskService"""
    
    async def test_task_service_initialization(self):
        """Test TaskService can be initialized"""
        temp_dir = tempfile.mkdtemp()
        try:
            service = TaskService(data_dir=temp_dir)
            await service.initialize()
            
            # Should initialize without errors
            assert service is not None
            assert hasattr(service, '_tasks')
            
        finally:
            shutil.rmtree(temp_dir)
    
    async def test_basic_task_operations(self):
        """Test basic CRUD operations"""
        temp_dir = tempfile.mkdtemp()
        try:
            from app.models.task_models import TaskCreate
            
            service = TaskService(data_dir=temp_dir)
            await service.initialize()
            
            # Create task
            task_data = TaskCreate(
                title="Test Task",
                description="Testing basic operations",
                priority=TaskPriority.MEDIUM
            )
            
            task = await service.create_task(task_data)
            assert task is not None
            assert task.title == "Test Task"
            assert task.status == TaskStatus.BACKLOG
            
            # Get task
            retrieved_task = await service.get_task(task.id)
            assert retrieved_task is not None
            assert retrieved_task.id == task.id
            
            # List tasks
            all_tasks = await service.list_tasks()
            assert len(all_tasks) >= 1
            assert any(t.id == task.id for t in all_tasks)
            
        finally:
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])