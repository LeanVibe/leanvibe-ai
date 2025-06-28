"""
Tests for data models and validation.
"""

from datetime import datetime

import pytest


def test_websocket_message_model():
    """Test WebSocketMessage model validation"""
    from app.models.messages import WebSocketMessage

    # Valid message
    msg = WebSocketMessage(type="command", content="/status")
    assert msg.type == "command"
    assert msg.content == "/status"
    assert msg.client_id is None

    # Message with all fields
    msg = WebSocketMessage(
        type="message", content="Hello", client_id="test", timestamp=datetime.now()
    )
    assert msg.client_id == "test"
    assert msg.timestamp is not None


def test_agent_response_model():
    """Test AgentResponse model validation"""
    from app.models.messages import AgentResponse

    # Basic response
    response = AgentResponse(status="success", message="Test message")
    assert response.status == "success"
    assert response.message == "Test message"
    assert response.data is None

    # Response with data
    response = AgentResponse(
        status="success", message="Test", data={"key": "value"}, processing_time=0.5
    )
    assert response.data["key"] == "value"
    assert response.processing_time == 0.5


def test_connection_info_model():
    """Test ConnectionInfo model validation"""
    from app.models.messages import ConnectionInfo

    now = datetime.now()
    info = ConnectionInfo(
        client_id="test-client", connected_at=now, user_agent="TestAgent/1.0"
    )
    assert info.client_id == "test-client"
    assert info.connected_at == now
    assert info.user_agent == "TestAgent/1.0"
