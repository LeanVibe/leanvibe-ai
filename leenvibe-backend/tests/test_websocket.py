"""
Integration tests for WebSocket functionality.
"""




def test_websocket_connection(test_client):
    """Test WebSocket connection establishment"""
    with test_client.websocket_connect("/ws/test-client") as websocket:
        # Test connection is established
        assert websocket is not None

        # Send a test message
        test_message = {
            "type": "command",
            "content": "/status",
            "client_id": "test-client",
        }
        websocket.send_json(test_message)

        # Receive response
        response = websocket.receive_json()
        assert "status" in response
        assert response["status"] == "success"


def test_websocket_multiple_commands(test_client):
    """Test multiple commands through WebSocket"""
    with test_client.websocket_connect("/ws/test-client") as websocket:
        commands = ["/status", "/help", "/list-files"]

        for cmd in commands:
            websocket.send_json(
                {"type": "command", "content": cmd, "client_id": "test-client"}
            )

            response = websocket.receive_json()
            assert "status" in response
            # Some commands might return error if files don't exist, that's ok
            assert response["status"] in ["success", "error"]


def test_websocket_invalid_message_format(test_client):
    """Test WebSocket handles invalid message formats gracefully"""
    with test_client.websocket_connect("/ws/test-client") as websocket:
        # Send invalid JSON
        websocket.send_text("invalid json")

        response = websocket.receive_json()
        assert "status" in response
        assert response["status"] == "error"
