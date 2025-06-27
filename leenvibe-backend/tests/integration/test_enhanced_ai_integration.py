import pytest
import asyncio
import json
from fastapi.testclient import TestClient

@pytest.mark.asyncio
async def test_enhanced_ai_message_processing(test_client):
    """
    Test that the EnhancedAIService processes natural language messages
    and returns a response with expected enhanced capabilities.
    """
    client_id = "enhanced-ai-test-client"
    
    with test_client.websocket_connect(f"/ws/{client_id}") as websocket:
        # Send a natural language message that should trigger AI processing
        test_message = {
            "type": "message",
            "content": "Explain the concept of dependency injection in Python.",
            "client_id": client_id,
            "workspace_path": "." # Provide a workspace path for session context
        }
        websocket.send_json(test_message)
        
        # Receive response
        response = websocket.receive_json()
        
        # Assert basic response structure
        assert "status" in response
        assert response["status"] == "success"
        assert "message" in response
        assert isinstance(response["message"], str)
        assert "confidence" in response
        assert isinstance(response["confidence"], float)
        assert "session_info" in response
        assert response["session_info"]["client_id"] == client_id
        
        # Assert enhanced AI specific fields
        assert "model" in response
        assert "services_available" in response
        assert isinstance(response["services_available"], dict)
        
        # Check if MLX or mock mode is indicated
        assert "MLX" in response["model"] or "Mock" in response["model"]
        
        # Check if core services are reported as available (even if in mock mode)
        assert response["services_available"]["mlx"] is not None
        assert response["services_available"]["ast"] is not None
        assert response["services_available"]["vector"] is not None

        # Send a command that uses AST/Vector services
        test_command = {
            "type": "command",
            "content": "/status",
            "client_id": client_id,
            "workspace_path": "."
        }
        websocket.send_json(test_command)
        response = websocket.receive_json()

        assert response["status"] == "success"
        assert response["type"] == "enhanced_status"
        assert "services" in response["data"]
        assert "mlx_model" in response["data"]["services"]
        assert "ast_parser" in response["data"]["services"]
        assert "vector_store" in response["data"]["services"]
        
    # Clean up the session after the test
    response = test_client.delete(f"/sessions/{client_id}")
    assert response.status_code == 200
    assert response.json()["success"] is True