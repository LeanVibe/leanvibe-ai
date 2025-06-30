"""
Comprehensive WebSocket Event Integration Tests

High-impact test suite for WebSocket event broadcasting and real-time communication.
Tests task event broadcasting, connection management, and event streaming integration.
"""

import pytest
import asyncio
import json
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi import WebSocket
from fastapi.testclient import TestClient
from datetime import datetime

from app.core.connection_manager import ConnectionManager
from app.models.task_models import Task, TaskCreate, TaskUpdate, TaskStatusUpdate
from app.models.event_models import ClientPreferences, NotificationChannel, EventPriority
from app.services.task_service import TaskService


class MockWebSocket:
    """Mock WebSocket for testing"""
    
    def __init__(self, client_id: str = "test-client"):
        self.client_id = client_id
        self.sent_messages = []
        self.closed = False
        self.headers = {"user-agent": "test-client"}
        
    async def accept(self):
        """Mock accept method"""
        pass
        
    async def send_text(self, message: str):
        """Mock send_text method"""
        if self.closed:
            raise Exception("WebSocket connection closed")
        self.sent_messages.append(message)
        
    async def close(self):
        """Mock close method"""
        self.closed = True


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket connection"""
    return MockWebSocket()


@pytest.fixture
def connection_manager():
    """Create a ConnectionManager instance for testing"""
    return ConnectionManager()


@pytest.fixture
def mock_event_streaming_service():
    """Mock the event streaming service"""
    with patch('app.core.connection_manager.event_streaming_service') as mock:
        mock.register_client = AsyncMock()
        mock.unregister_client = AsyncMock()
        mock.update_client_preferences = AsyncMock()
        mock.get_stats = MagicMock(return_value={"total_events": 0, "active_clients": 0})
        mock.get_client_info = MagicMock(return_value={})
        yield mock


@pytest.fixture
def mock_reconnection_service():
    """Mock the reconnection service"""
    with patch('app.core.connection_manager.register_client_session') as mock_register, \
         patch('app.core.connection_manager.client_disconnected') as mock_disconnect:
        mock_register.return_value = None
        mock_disconnect.return_value = None
        yield (mock_register, mock_disconnect)


class TestConnectionManager:
    """Test WebSocket connection management"""
    
    @pytest.mark.asyncio
    async def test_websocket_connection_establishment(
        self, connection_manager, mock_websocket, mock_event_streaming_service, mock_reconnection_service
    ):
        """Test establishing a new WebSocket connection"""
        client_id = "test-client-1"
        
        # Act
        await connection_manager.connect(mock_websocket, client_id)
        
        # Assert
        assert client_id in connection_manager.active_connections
        assert connection_manager.active_connections[client_id] == mock_websocket
        assert client_id in connection_manager.client_info
        
        # Verify client info structure
        client_info = connection_manager.client_info[client_id]
        assert "connected_at" in client_info
        assert "user_agent" in client_info
        assert "client_type" in client_info
        assert "streaming_enabled" in client_info
        assert "is_reconnection" in client_info
        
        # Verify event streaming registration
        mock_event_streaming_service.register_client.assert_called_once()
        
        # Verify reconnection service registration
        register_mock, _ = mock_reconnection_service
        register_mock.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_websocket_reconnection_handling(
        self, connection_manager, mock_websocket, mock_event_streaming_service, mock_reconnection_service
    ):
        """Test reconnection scenario"""
        client_id = "test-client-reconnect"
        
        # Act - simulate reconnection
        await connection_manager.connect(mock_websocket, client_id, is_reconnection=True)
        
        # Assert
        assert connection_manager.client_info[client_id]["is_reconnection"] is True
        
        # Verify event streaming handles reconnection
        mock_event_streaming_service.register_client.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_websocket_disconnection(
        self, connection_manager, mock_websocket, mock_event_streaming_service, mock_reconnection_service
    ):
        """Test WebSocket disconnection and cleanup"""
        client_id = "test-client-disconnect"
        
        # Setup - connect first
        await connection_manager.connect(mock_websocket, client_id)
        assert client_id in connection_manager.active_connections
        
        # Act - disconnect
        connection_manager.disconnect(client_id)
        
        # Assert
        assert client_id not in connection_manager.active_connections
        assert client_id not in connection_manager.client_info
        
        # Verify event streaming cleanup
        mock_event_streaming_service.unregister_client.assert_called_once_with(client_id)
        
        # Verify reconnection service cleanup
        _, disconnect_mock = mock_reconnection_service
        disconnect_mock.assert_called_once_with(client_id)
    
    @pytest.mark.asyncio
    async def test_client_type_detection(self, connection_manager):
        """Test client type detection from user agent"""
        # Test iOS client
        ios_websocket = MockWebSocket()
        ios_websocket.headers = {"user-agent": "LeanVibe iOS App/1.0 (iPhone OS)"}
        
        await connection_manager.connect(ios_websocket, "ios-client")
        assert connection_manager.client_info["ios-client"]["client_type"] == "ios"
        
        # Test CLI client
        cli_websocket = MockWebSocket()
        cli_websocket.headers = {"user-agent": "python-requests/2.28.0 CLI"}
        
        await connection_manager.connect(cli_websocket, "cli-client")
        assert connection_manager.client_info["cli-client"]["client_type"] == "cli"
        
        # Test web client
        web_websocket = MockWebSocket()
        web_websocket.headers = {"user-agent": "Mozilla/5.0 Chrome/98.0"}
        
        await connection_manager.connect(web_websocket, "web-client")
        assert connection_manager.client_info["web-client"]["client_type"] == "web"


class TestPersonalMessaging:
    """Test personal message sending to specific clients"""
    
    @pytest.mark.asyncio
    async def test_send_personal_text_message(
        self, connection_manager, mock_websocket, mock_event_streaming_service, mock_reconnection_service
    ):
        """Test sending text message to specific client"""
        client_id = "test-personal-msg"
        message = "Hello, specific client!"
        
        # Setup
        await connection_manager.connect(mock_websocket, client_id)
        
        # Act
        await connection_manager.send_personal_message(message, client_id)
        
        # Assert
        assert len(mock_websocket.sent_messages) == 1
        assert mock_websocket.sent_messages[0] == message
    
    @pytest.mark.asyncio
    async def test_send_personal_json_message(
        self, connection_manager, mock_websocket, mock_event_streaming_service, mock_reconnection_service
    ):
        """Test sending JSON message to specific client"""
        client_id = "test-json-msg"
        data = {"type": "task_update", "action": "created", "task_id": "123"}
        
        # Setup
        await connection_manager.connect(mock_websocket, client_id)
        
        # Act
        await connection_manager.send_json_message(data, client_id)
        
        # Assert
        assert len(mock_websocket.sent_messages) == 1
        sent_data = json.loads(mock_websocket.sent_messages[0])
        assert sent_data == data
    
    @pytest.mark.asyncio
    async def test_send_message_to_nonexistent_client(self, connection_manager):
        """Test sending message to non-connected client"""
        # Act - should not raise exception
        await connection_manager.send_personal_message("test", "non-existent-client")
        await connection_manager.send_json_message({"test": "data"}, "non-existent-client")
        
        # Assert - no exceptions should be raised
        assert True
    
    @pytest.mark.asyncio
    async def test_send_message_connection_error_cleanup(
        self, connection_manager, mock_event_streaming_service, mock_reconnection_service
    ):
        """Test automatic cleanup when message sending fails"""
        client_id = "failing-client"
        
        # Create a WebSocket that fails on send
        failing_websocket = MockWebSocket()
        failing_websocket.closed = True  # This will cause send_text to raise exception
        
        # Setup
        await connection_manager.connect(failing_websocket, client_id)
        assert client_id in connection_manager.active_connections
        
        # Act - try to send message (should fail and trigger cleanup)
        await connection_manager.send_personal_message("test", client_id)
        
        # Assert - client should be automatically disconnected
        assert client_id not in connection_manager.active_connections


class TestBroadcastMessaging:
    """Test broadcasting messages to all connected clients"""
    
    @pytest.mark.asyncio
    async def test_broadcast_text_message(
        self, connection_manager, mock_event_streaming_service, mock_reconnection_service
    ):
        """Test broadcasting text message to all clients"""
        # Setup multiple clients
        clients = []
        for i in range(3):
            websocket = MockWebSocket(f"client-{i}")
            clients.append((f"client-{i}", websocket))
            await connection_manager.connect(websocket, f"client-{i}")
        
        message = "Broadcast message to all"
        
        # Act
        await connection_manager.broadcast(message)
        
        # Assert
        for client_id, websocket in clients:
            assert len(websocket.sent_messages) == 1
            assert websocket.sent_messages[0] == message
    
    @pytest.mark.asyncio
    async def test_broadcast_json_message(
        self, connection_manager, mock_event_streaming_service, mock_reconnection_service
    ):
        """Test broadcasting JSON message to all clients"""
        # Setup multiple clients
        clients = []
        for i in range(2):
            websocket = MockWebSocket(f"json-client-{i}")
            clients.append((f"json-client-{i}", websocket))
            await connection_manager.connect(websocket, f"json-client-{i}")
        
        data = {"type": "system_update", "message": "System maintenance in 5 minutes"}
        
        # Act
        await connection_manager.broadcast_json(data)
        
        # Assert
        for client_id, websocket in clients:
            assert len(websocket.sent_messages) == 1
            sent_data = json.loads(websocket.sent_messages[0])
            assert sent_data == data
    
    @pytest.mark.asyncio
    async def test_broadcast_with_failing_connections(
        self, connection_manager, mock_event_streaming_service, mock_reconnection_service
    ):
        """Test broadcast handles failing connections gracefully"""
        # Setup clients - one working, one failing
        working_websocket = MockWebSocket("working-client")
        failing_websocket = MockWebSocket("failing-client")
        failing_websocket.closed = True  # Will cause send_text to fail
        
        await connection_manager.connect(working_websocket, "working-client")
        await connection_manager.connect(failing_websocket, "failing-client")
        
        message = "Test broadcast with failures"
        
        # Act
        await connection_manager.broadcast(message)
        
        # Assert
        # Working client should receive message
        assert len(working_websocket.sent_messages) == 1
        assert working_websocket.sent_messages[0] == message
        
        # Failing client should be automatically disconnected
        assert "failing-client" not in connection_manager.active_connections
        assert "working-client" in connection_manager.active_connections


class TestTaskEventBroadcasting:
    """Test task-related event broadcasting"""
    
    @pytest.mark.asyncio
    async def test_task_created_event_broadcast(
        self, connection_manager, mock_event_streaming_service, mock_reconnection_service
    ):
        """Test broadcasting task creation events"""
        # Setup clients
        websocket = MockWebSocket("task-listener")
        await connection_manager.connect(websocket, "task-listener")
        
        # Create task event data
        task = Task(
            id="test-task-123",
            title="New Task",
            priority="high",
            status="backlog"
        )
        
        event_data = {
            "type": "task_update",
            "action": "created",
            "task": task.dict(),
            "timestamp": task.updated_at.isoformat() if task.updated_at else None
        }
        
        # Act
        await connection_manager.broadcast_json(event_data)
        
        # Assert
        assert len(websocket.sent_messages) == 1
        received_data = json.loads(websocket.sent_messages[0])
        assert received_data["type"] == "task_update"
        assert received_data["action"] == "created"
        assert received_data["task"]["id"] == "test-task-123"
        assert received_data["task"]["title"] == "New Task"
    
    @pytest.mark.asyncio
    async def test_task_updated_event_broadcast(
        self, connection_manager, mock_event_streaming_service, mock_reconnection_service
    ):
        """Test broadcasting task update events"""
        # Setup clients
        websocket = MockWebSocket("update-listener")
        await connection_manager.connect(websocket, "update-listener")
        
        # Create updated task event data
        updated_task = Task(
            id="task-456",
            title="Updated Task Title",
            priority="medium",
            status="in_progress"
        )
        
        event_data = {
            "type": "task_update",
            "action": "updated",
            "task": updated_task.dict(),
            "timestamp": updated_task.updated_at.isoformat() if updated_task.updated_at else None
        }
        
        # Act
        await connection_manager.broadcast_json(event_data)
        
        # Assert
        assert len(websocket.sent_messages) == 1
        received_data = json.loads(websocket.sent_messages[0])
        assert received_data["action"] == "updated"
        assert received_data["task"]["status"] == "in_progress"
    
    @pytest.mark.asyncio
    async def test_task_status_moved_event_broadcast(
        self, connection_manager, mock_event_streaming_service, mock_reconnection_service
    ):
        """Test broadcasting task status change/move events"""
        # Setup clients
        websocket = MockWebSocket("move-listener")
        await connection_manager.connect(websocket, "move-listener")
        
        # Create moved task event data
        moved_task = Task(
            id="task-789",
            title="Moved Task",
            priority="low",
            status="testing"
        )
        
        event_data = {
            "type": "task_update",
            "action": "moved",
            "task": moved_task.dict(),
            "timestamp": moved_task.updated_at.isoformat() if moved_task.updated_at else None
        }
        
        # Act
        await connection_manager.broadcast_json(event_data)
        
        # Assert
        assert len(websocket.sent_messages) == 1
        received_data = json.loads(websocket.sent_messages[0])
        assert received_data["action"] == "moved"
        assert received_data["task"]["status"] == "testing"
    
    @pytest.mark.asyncio
    async def test_task_deleted_event_broadcast(
        self, connection_manager, mock_event_streaming_service, mock_reconnection_service
    ):
        """Test broadcasting task deletion events"""
        # Setup clients
        websocket = MockWebSocket("delete-listener")
        await connection_manager.connect(websocket, "delete-listener")
        
        # Create deleted task event data
        deleted_task = Task(
            id="task-to-delete",
            title="Task to Delete",
            priority="high",
            status="done"
        )
        
        event_data = {
            "type": "task_update",
            "action": "deleted",
            "task": deleted_task.dict(),
            "timestamp": deleted_task.updated_at.isoformat() if deleted_task.updated_at else None
        }
        
        # Act
        await connection_manager.broadcast_json(event_data)
        
        # Assert
        assert len(websocket.sent_messages) == 1
        received_data = json.loads(websocket.sent_messages[0])
        assert received_data["action"] == "deleted"
        assert received_data["task"]["id"] == "task-to-delete"


class TestClientPreferences:
    """Test client preferences management"""
    
    @pytest.mark.asyncio
    async def test_default_ios_client_preferences(
        self, connection_manager, mock_event_streaming_service, mock_reconnection_service
    ):
        """Test default preferences for iOS clients"""
        ios_websocket = MockWebSocket("ios-client")
        ios_websocket.headers = {"user-agent": "LeanVibe iOS App/1.0 (iPhone OS)"}
        
        # Act
        await connection_manager.connect(ios_websocket, "ios-client")
        
        # Assert - verify event streaming was called with iOS-appropriate preferences
        mock_event_streaming_service.register_client.assert_called_once()
        call_args = mock_event_streaming_service.register_client.call_args
        preferences = call_args[0][2]  # Third argument should be preferences
        
        assert preferences.min_priority == EventPriority.MEDIUM
        assert preferences.enable_batching is True
        assert preferences.batch_interval_ms == 1000
        assert preferences.max_events_per_second == 5
    
    @pytest.mark.asyncio
    async def test_default_cli_client_preferences(
        self, connection_manager, mock_event_streaming_service, mock_reconnection_service
    ):
        """Test default preferences for CLI clients"""
        cli_websocket = MockWebSocket("cli-client")
        cli_websocket.headers = {"user-agent": "python-requests/2.28.0 CLI"}
        
        # Act
        await connection_manager.connect(cli_websocket, "cli-client")
        
        # Assert - verify event streaming was called with CLI-appropriate preferences
        mock_event_streaming_service.register_client.assert_called_once()
        call_args = mock_event_streaming_service.register_client.call_args
        preferences = call_args[0][2]  # Third argument should be preferences
        
        assert preferences.min_priority == EventPriority.HIGH
        assert preferences.enable_batching is False
        assert preferences.max_events_per_second == 20
        assert preferences.enable_compression is True
    
    @pytest.mark.asyncio
    async def test_update_client_preferences(
        self, connection_manager, mock_websocket, mock_event_streaming_service, mock_reconnection_service
    ):
        """Test updating client preferences"""
        client_id = "pref-client"
        
        # Setup
        await connection_manager.connect(mock_websocket, client_id)
        
        # Create new preferences
        new_preferences = ClientPreferences(
            client_id=client_id,
            enabled_channels=[NotificationChannel.VIOLATIONS],
            min_priority=EventPriority.HIGH,
            max_events_per_second=15,
            enable_batching=False
        )
        
        # Act
        connection_manager.update_client_preferences(client_id, new_preferences)
        
        # Assert
        mock_event_streaming_service.update_client_preferences.assert_called_once_with(
            client_id, new_preferences
        )


class TestConnectionInfo:
    """Test connection information and statistics"""
    
    @pytest.mark.asyncio
    async def test_get_connection_info(
        self, connection_manager, mock_event_streaming_service, mock_reconnection_service
    ):
        """Test getting comprehensive connection information"""
        # Setup multiple clients
        clients = ["info-client-1", "info-client-2", "info-client-3"]
        for client_id in clients:
            websocket = MockWebSocket(client_id)
            await connection_manager.connect(websocket, client_id)
        
        # Mock streaming service stats
        mock_event_streaming_service.get_stats.return_value = {
            "total_events": 42,
            "active_clients": 3
        }
        mock_event_streaming_service.get_client_info.return_value = {
            "client_preferences": {},
            "last_event_sent": {}
        }
        
        # Act
        info = connection_manager.get_connection_info()
        
        # Assert
        assert info["total_connections"] == 3
        assert set(info["connected_clients"]) == set(clients)
        assert "client_details" in info
        assert info["streaming_enabled"] is True
        assert "streaming_stats" in info
        assert info["streaming_stats"]["total_events"] == 42
        assert "streaming_clients" in info
    
    @pytest.mark.asyncio
    async def test_streaming_enable_disable(self, connection_manager):
        """Test enabling and disabling streaming"""
        # Test disable
        connection_manager.disable_streaming()
        assert connection_manager._streaming_enabled is False
        
        info = connection_manager.get_connection_info()
        assert info["streaming_enabled"] is False
        assert "streaming_stats" not in info
        
        # Test enable
        connection_manager.enable_streaming()
        assert connection_manager._streaming_enabled is True


class TestErrorHandling:
    """Test error handling in WebSocket operations"""
    
    @pytest.mark.asyncio
    async def test_connection_error_during_broadcast(
        self, connection_manager, mock_event_streaming_service, mock_reconnection_service
    ):
        """Test handling connection errors during broadcast"""
        # Setup clients - mix of working and failing
        working_clients = []
        failing_clients = []
        
        for i in range(2):
            # Working clients
            websocket = MockWebSocket(f"working-{i}")
            working_clients.append((f"working-{i}", websocket))
            await connection_manager.connect(websocket, f"working-{i}")
            
            # Failing clients
            failing_websocket = MockWebSocket(f"failing-{i}")
            failing_websocket.closed = True
            failing_clients.append((f"failing-{i}", failing_websocket))
            await connection_manager.connect(failing_websocket, f"failing-{i}")
        
        initial_count = len(connection_manager.active_connections)
        assert initial_count == 4
        
        # Act - broadcast should handle failures gracefully
        await connection_manager.broadcast("Test message with failures")
        
        # Assert
        # Working clients should receive message
        for client_id, websocket in working_clients:
            assert len(websocket.sent_messages) == 1
            assert websocket.sent_messages[0] == "Test message with failures"
        
        # Failing clients should be automatically removed
        for client_id, _ in failing_clients:
            assert client_id not in connection_manager.active_connections
        
        # Only working clients should remain
        assert len(connection_manager.active_connections) == 2
    
    @pytest.mark.asyncio
    async def test_json_serialization_error_handling(
        self, connection_manager, mock_event_streaming_service, mock_reconnection_service
    ):
        """Test handling JSON serialization errors"""
        # Setup client
        websocket = MockWebSocket("json-error-client")
        await connection_manager.connect(websocket, "json-error-client")
        
        # Create data that might cause serialization issues
        # Using datetime objects that need special handling
        problematic_data = {
            "timestamp": datetime.now(),  # This should be handled by default=str
            "task": "test"
        }
        
        # Act - should not raise exception due to default=str in json.dumps
        await connection_manager.broadcast_json(problematic_data)
        
        # Assert - message should be sent successfully
        assert len(websocket.sent_messages) == 1
        # Should be able to parse the JSON back
        parsed_data = json.loads(websocket.sent_messages[0])
        assert "timestamp" in parsed_data
        assert parsed_data["task"] == "test"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])