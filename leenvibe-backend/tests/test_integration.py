import asyncio
import json
import os
import sys

import pytest
import websockets

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Note: These tests require the backend to be running
# They serve as integration tests for the WebSocket functionality


@pytest.mark.asyncio
async def test_websocket_connection():
    """Test basic WebSocket connection"""
    try:
        async with websockets.connect(
            "ws://localhost:8000/ws/test-client"
        ) as websocket:
            # Test connection establishment
            assert websocket is not None

            # Send test message
            test_message = {
                "type": "command",
                "content": "/status",
                "timestamp": "2025-06-26T12:00:00Z",
            }
            await websocket.send(json.dumps(test_message))

            # Receive response
            response = await websocket.recv()
            data = json.loads(response)

            # Verify response structure
            assert "status" in data
            assert "message" in data

    except ConnectionRefusedError:
        pytest.skip("Backend server not running - start with ./start.sh")


@pytest.mark.asyncio
async def test_command_processing():
    """Test various command types"""
    commands_to_test = [
        ("/status", "success"),
        ("/help", "success"),
        ("/current-dir", "success"),
        ("/list-files", "success"),
        ("/unknown-command", "error"),
    ]

    try:
        for command, expected_status in commands_to_test:
            async with websockets.connect(
                "ws://localhost:8000/ws/test-client"
            ) as websocket:
                test_message = {
                    "type": "command",
                    "content": command,
                    "timestamp": "2025-06-26T12:00:00Z",
                }
                await websocket.send(json.dumps(test_message))

                response = await websocket.recv()
                data = json.loads(response)

                assert (
                    data["status"] == expected_status
                ), f"Command {command} failed: {data}"

    except ConnectionRefusedError:
        pytest.skip("Backend server not running - start with ./start.sh")


@pytest.mark.asyncio
async def test_message_format_validation():
    """Test message format validation"""
    try:
        async with websockets.connect(
            "ws://localhost:8000/ws/test-client"
        ) as websocket:
            # Test invalid JSON
            await websocket.send("invalid json")
            response = await websocket.recv()
            data = json.loads(response)
            assert data["status"] == "error"

            # Test missing fields
            await websocket.send(json.dumps({"type": "command"}))
            response = await websocket.recv()
            data = json.loads(response)
            # Should handle gracefully

    except ConnectionRefusedError:
        pytest.skip("Backend server not running - start with ./start.sh")


@pytest.mark.asyncio
async def test_concurrent_connections():
    """Test multiple simultaneous connections"""
    try:

        async def single_connection_test(client_id):
            async with websockets.connect(
                f"ws://localhost:8000/ws/{client_id}"
            ) as websocket:
                message = {
                    "type": "command",
                    "content": "/status",
                    "timestamp": "2025-06-26T12:00:00Z",
                }
                await websocket.send(json.dumps(message))
                response = await websocket.recv()
                data = json.loads(response)
                return data["status"] == "success"

        # Test 3 concurrent connections
        tasks = [single_connection_test(f"client-{i}") for i in range(3)]
        results = await asyncio.gather(*tasks)

        # All connections should succeed
        assert all(results), "Some concurrent connections failed"

    except ConnectionRefusedError:
        pytest.skip("Backend server not running - start with ./start.sh")


def test_health_endpoint():
    """Test REST API health endpoint"""
    try:
        # This test doesn't require imports if server is running
        import requests

        response = requests.get("http://localhost:8000/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    except (ImportError, requests.exceptions.ConnectionError):
        pytest.skip("Backend server not running or requests not available")


if __name__ == "__main__":
    # Allow running tests directly
    asyncio.run(test_websocket_connection())
    print("✅ Basic WebSocket connection test passed")

    asyncio.run(test_command_processing())
    print("✅ Command processing test passed")

    asyncio.run(test_concurrent_connections())
    print("✅ Concurrent connections test passed")

    print("\n🎉 All integration tests passed!")
    print("Note: Start backend with ./start.sh before running tests")
