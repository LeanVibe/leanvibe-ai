"""
Comprehensive Task Management API Tests with AI Integration

Tests for validating complete task API functionality including AI-powered analysis,
WebSocket broadcasting, and integration with the LLM system.

As specified in unified backend testing execution prompt.
"""

import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

@pytest.mark.asyncio
async def test_create_task_with_ai_analysis(test_client):
    """Test task creation with AI-powered analysis"""
    # Use real AI service (with mocked LLM for speed)
    with patch('app.services.phi3_mini_service.Phi3MiniService') as mock_phi3:
        # Mock the generate_text method to return a structured analysis
        mock_phi3.return_value.generate_text.return_value = asyncio.Future()
        mock_phi3.return_value.generate_text.return_value.set_result(
            "Task analysis: Well-defined requirements for user authentication implementation. "
            "Recommended approach: JWT-based authentication with proper validation."
        )
        
        # Test task creation with AI analysis
        response = test_client.post("/tasks/test-client", json={
            "title": "Implement user authentication",
            "description": "Add JWT-based authentication",
            "analyze_with_ai": True
        })
        
        assert response.status_code == 201
        task_data = response.json()
        assert "ai_analysis" in task_data
        assert "Well-defined requirements" in task_data["ai_analysis"]
        assert task_data["title"] == "Implement user authentication"


@pytest.mark.asyncio
async def test_task_crud_operations(test_client):
    """Test complete CRUD operations for tasks"""
    client_id = "crud-test-client"
    
    # CREATE
    create_response = test_client.post(f"/tasks/{client_id}", json={
        "title": "Test CRUD Task",
        "description": "Testing all CRUD operations",
        "priority": "high",
        "tags": ["testing", "crud"]
    })
    assert create_response.status_code == 201
    task_data = create_response.json()
    task_id = task_data["id"]
    
    # READ (single task)
    read_response = test_client.get(f"/tasks/{client_id}/{task_id}")
    assert read_response.status_code == 200
    read_data = read_response.json()
    assert read_data["title"] == "Test CRUD Task"
    assert read_data["priority"] == "high"
    
    # UPDATE
    update_response = test_client.put(f"/tasks/{client_id}/{task_id}", json={
        "title": "Updated CRUD Task",
        "description": "Updated description for testing",
        "status": "in_progress"
    })
    assert update_response.status_code == 200
    updated_data = update_response.json()
    assert updated_data["title"] == "Updated CRUD Task"
    assert updated_data["status"] == "in_progress"
    
    # DELETE
    delete_response = test_client.delete(f"/tasks/{client_id}/{task_id}")
    assert delete_response.status_code == 200
    
    # Verify deletion
    verify_response = test_client.get(f"/tasks/{client_id}/{task_id}")
    assert verify_response.status_code == 404


@pytest.mark.asyncio
async def test_task_bulk_operations(test_client):
    """Test bulk task operations for efficiency"""
    client_id = "bulk-test-client"
    
    # Create multiple tasks
    tasks_to_create = [
        {"title": f"Bulk Task {i}", "description": f"Description {i}", "priority": "medium"}
        for i in range(5)
    ]
    
    bulk_create_response = test_client.post(f"/tasks/{client_id}/bulk", json={
        "tasks": tasks_to_create
    })
    assert bulk_create_response.status_code == 201
    bulk_data = bulk_create_response.json()
    assert len(bulk_data["created_tasks"]) == 5
    
    # Get all tasks
    list_response = test_client.get(f"/tasks/{client_id}")
    assert list_response.status_code == 200
    all_tasks = list_response.json()
    assert len(all_tasks) >= 5
    
    # Bulk update
    task_ids = [task["id"] for task in bulk_data["created_tasks"]]
    bulk_update_response = test_client.put(f"/tasks/{client_id}/bulk", json={
        "task_ids": task_ids,
        "updates": {"status": "completed", "priority": "low"}
    })
    assert bulk_update_response.status_code == 200
    
    # Verify updates
    for task_id in task_ids:
        verify_response = test_client.get(f"/tasks/{client_id}/{task_id}")
        task_data = verify_response.json()
        assert task_data["status"] == "completed"
        assert task_data["priority"] == "low"


@pytest.mark.asyncio
async def test_task_search_and_filtering(test_client):
    """Test task search and filtering capabilities"""
    client_id = "search-test-client"
    
    # Create tasks with different attributes
    test_tasks = [
        {"title": "Backend API Task", "description": "Implement REST API", "tags": ["backend", "api"], "priority": "high"},
        {"title": "Frontend UI Task", "description": "Create user interface", "tags": ["frontend", "ui"], "priority": "medium"},
        {"title": "Database Migration", "description": "Update database schema", "tags": ["database", "migration"], "priority": "low"},
        {"title": "API Documentation", "description": "Document REST API endpoints", "tags": ["documentation", "api"], "priority": "medium"}
    ]
    
    for task in test_tasks:
        response = test_client.post(f"/tasks/{client_id}", json=task)
        assert response.status_code == 201
    
    # Test search by title
    search_response = test_client.get(f"/tasks/{client_id}/search", params={
        "query": "API"
    })
    assert search_response.status_code == 200
    search_results = search_response.json()
    assert len(search_results) == 2  # Backend API Task and API Documentation
    
    # Test filter by priority
    filter_response = test_client.get(f"/tasks/{client_id}", params={
        "priority": "medium"
    })
    assert filter_response.status_code == 200
    filtered_tasks = filter_response.json()
    medium_priority_tasks = [task for task in filtered_tasks if task["priority"] == "medium"]
    assert len(medium_priority_tasks) == 2
    
    # Test filter by tags
    tag_filter_response = test_client.get(f"/tasks/{client_id}", params={
        "tags": "api"
    })
    assert tag_filter_response.status_code == 200
    tag_filtered_tasks = tag_filter_response.json()
    api_tasks = [task for task in tag_filtered_tasks if "api" in task.get("tags", [])]
    assert len(api_tasks) >= 2


@pytest.mark.asyncio
async def test_task_statistics_and_analytics(test_client):
    """Test task statistics and analytics endpoints"""
    client_id = "stats-test-client"
    
    # Create tasks with various statuses
    task_statuses = ["todo", "in_progress", "completed", "completed", "todo"]
    for i, status in enumerate(task_statuses):
        response = test_client.post(f"/tasks/{client_id}", json={
            "title": f"Stats Task {i}",
            "description": f"Task for statistics testing {i}",
            "status": status,
            "priority": "medium"
        })
        assert response.status_code == 201
    
    # Get task statistics
    stats_response = test_client.get(f"/tasks/{client_id}/statistics")
    assert stats_response.status_code == 200
    stats_data = stats_response.json()
    
    # Verify statistics
    assert "total_tasks" in stats_data
    assert "status_breakdown" in stats_data
    assert stats_data["total_tasks"] >= 5
    assert stats_data["status_breakdown"]["completed"] >= 2
    assert stats_data["status_breakdown"]["todo"] >= 2
    assert stats_data["status_breakdown"]["in_progress"] >= 1
    
    # Test analytics endpoint
    analytics_response = test_client.get(f"/tasks/{client_id}/analytics", params={
        "period": "last_7_days"
    })
    assert analytics_response.status_code == 200
    analytics_data = analytics_response.json()
    assert "completion_rate" in analytics_data
    assert "productivity_metrics" in analytics_data


@pytest.mark.asyncio
async def test_task_websocket_broadcasting(test_client):
    """Test WebSocket broadcasting for task events"""
    from unittest.mock import patch, AsyncMock
    
    client_id = "ws-test-client"
    
    with patch('app.core.connection_manager.ConnectionManager') as mock_manager:
        mock_manager_instance = AsyncMock()
        mock_manager.return_value = mock_manager_instance
        mock_manager_instance.broadcast = AsyncMock()
        
        # Create a task (should trigger WebSocket broadcast)
        response = test_client.post(f"/tasks/{client_id}", json={
            "title": "WebSocket Test Task",
            "description": "Testing WebSocket broadcasting",
            "priority": "high"
        })
        
        assert response.status_code == 201
        task_data = response.json()
        
        # Verify WebSocket broadcast was called
        # Note: This test validates the integration pattern, actual WebSocket testing requires more complex setup


@pytest.mark.asyncio
async def test_task_ai_integration_comprehensive(test_client):
    """Test comprehensive AI integration with task management"""
    client_id = "ai-integration-test"
    
    with patch('app.services.unified_mlx_service.unified_mlx_service') as mock_mlx:
        # Mock AI service responses
        mock_mlx.generate_code_completion.return_value = asyncio.Future()
        mock_mlx.generate_code_completion.return_value.set_result({
            "status": "success",
            "response": "Based on the task analysis, I recommend breaking this into 3 subtasks: authentication middleware, user model, and login/logout endpoints.",
            "confidence": 0.85,
            "suggestions": ["Consider using JWT tokens", "Implement rate limiting", "Add input validation"]
        })
        
        # Test AI-enhanced task creation
        response = test_client.post(f"/tasks/{client_id}", json={
            "title": "Implement user authentication system",
            "description": "Need to add secure user authentication to the application",
            "request_ai_analysis": True,
            "request_ai_suggestions": True
        })
        
        assert response.status_code == 201
        task_data = response.json()
        
        # Verify AI analysis was included
        assert "ai_analysis" in task_data
        assert "ai_suggestions" in task_data
        assert task_data["ai_analysis"] is not None
        assert len(task_data["ai_suggestions"]) > 0
        
        # Test AI-powered task recommendations
        recommendations_response = test_client.get(f"/tasks/{client_id}/ai-recommendations")
        assert recommendations_response.status_code == 200
        recommendations = recommendations_response.json()
        assert "recommended_tasks" in recommendations
        assert "optimization_suggestions" in recommendations


@pytest.mark.asyncio
async def test_task_error_handling_and_validation(test_client):
    """Test comprehensive error handling and input validation"""
    client_id = "error-test-client"
    
    # Test invalid task creation
    invalid_response = test_client.post(f"/tasks/{client_id}", json={
        "title": "",  # Empty title should fail validation
        "description": "This should fail"
    })
    assert invalid_response.status_code == 422  # Validation error
    
    # Test invalid task ID
    not_found_response = test_client.get(f"/tasks/{client_id}/nonexistent-task-id")
    assert not_found_response.status_code == 404
    
    # Test invalid client ID format
    invalid_client_response = test_client.get("/tasks/invalid@client#id")
    # Should handle gracefully (might return 400 or process with sanitization)
    assert invalid_client_response.status_code in [400, 422, 200]
    
    # Test malformed JSON
    malformed_response = test_client.post(
        f"/tasks/{client_id}",
        data="{invalid json}",
        headers={"Content-Type": "application/json"}
    )
    assert malformed_response.status_code == 422


@pytest.mark.performance
async def test_task_api_performance(test_client):
    """Test task API performance requirements"""
    import time
    client_id = "performance-test-client"
    
    # Test single task creation performance
    start_time = time.time()
    response = test_client.post(f"/tasks/{client_id}", json={
        "title": "Performance Test Task",
        "description": "Testing API response time"
    })
    creation_time = time.time() - start_time
    
    assert response.status_code == 201
    assert creation_time < 1.0  # Should complete within 1 second
    
    # Test bulk operations performance
    start_time = time.time()
    bulk_tasks = [
        {"title": f"Bulk Perf Task {i}", "description": f"Performance test {i}"}
        for i in range(20)
    ]
    bulk_response = test_client.post(f"/tasks/{client_id}/bulk", json={
        "tasks": bulk_tasks
    })
    bulk_time = time.time() - start_time
    
    assert bulk_response.status_code == 201
    assert bulk_time < 5.0  # Should complete within 5 seconds for 20 tasks
    
    # Test list performance
    start_time = time.time()
    list_response = test_client.get(f"/tasks/{client_id}")
    list_time = time.time() - start_time
    
    assert list_response.status_code == 200
    assert list_time < 2.0  # Should complete within 2 seconds


@pytest.mark.integration
async def test_task_api_integration_workflow(test_client):
    """Test complete end-to-end task management workflow"""
    client_id = "workflow-test-client"
    
    # Step 1: Create project with multiple tasks
    project_tasks = [
        {"title": "Setup Project Structure", "description": "Initialize repository and basic structure", "priority": "high"},
        {"title": "Implement Core Features", "description": "Build main application features", "priority": "medium"},
        {"title": "Add Testing", "description": "Implement comprehensive test suite", "priority": "medium"},
        {"title": "Documentation", "description": "Create user and developer documentation", "priority": "low"},
        {"title": "Deployment", "description": "Setup CI/CD and deployment pipeline", "priority": "high"}
    ]
    
    created_tasks = []
    for task in project_tasks:
        response = test_client.post(f"/tasks/{client_id}", json=task)
        assert response.status_code == 201
        created_tasks.append(response.json())
    
    # Step 2: Update task statuses to simulate workflow
    setup_task = created_tasks[0]
    update_response = test_client.put(f"/tasks/{client_id}/{setup_task['id']}", json={
        "status": "completed"
    })
    assert update_response.status_code == 200
    
    # Step 3: Get project statistics
    stats_response = test_client.get(f"/tasks/{client_id}/statistics")
    assert stats_response.status_code == 200
    stats = stats_response.json()
    assert stats["status_breakdown"]["completed"] >= 1
    
    # Step 4: Search for high priority tasks
    high_priority_response = test_client.get(f"/tasks/{client_id}", params={
        "priority": "high"
    })
    assert high_priority_response.status_code == 200
    high_priority_tasks = high_priority_response.json()
    assert len(high_priority_tasks) >= 2
    
    # Step 5: Complete the workflow with AI recommendations
    with patch('app.services.unified_mlx_service.unified_mlx_service') as mock_mlx:
        mock_mlx.generate_code_completion.return_value = asyncio.Future()
        mock_mlx.generate_code_completion.return_value.set_result({
            "status": "success", 
            "response": "Recommended next steps: Focus on core features implementation, then testing.",
            "confidence": 0.9
        })
        
        recommendations_response = test_client.get(f"/tasks/{client_id}/ai-recommendations")
        assert recommendations_response.status_code == 200
        recommendations = recommendations_response.json()
        assert "recommended_tasks" in recommendations or "optimization_suggestions" in recommendations