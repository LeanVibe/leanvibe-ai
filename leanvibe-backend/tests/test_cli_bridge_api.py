"""
Test CLI Bridge API Endpoints

Comprehensive tests for CLI-to-iOS bridge functionality including WebSocket communication,
device management, and command broadcasting.
"""

import json
import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

from app.main import app
from app.api.endpoints.cli_bridge import CLICommand, cli_bridge_connections
from app.core.connection_manager import ConnectionManager


@pytest.fixture
def test_client():
    """Create test client for API testing"""
    return TestClient(app)


@pytest.fixture
def mock_connection_manager():
    """Mock connection manager for testing"""
    mock_manager = MagicMock(spec=ConnectionManager)
    mock_manager.get_connection_info.return_value = {
        "ios_device_1": {
            "client_type": "ios",
            "user_agent": "LeanVibe/1.0 (iPhone; iOS 17.0)",
            "connected_at": datetime.now().isoformat(),
            "last_seen": datetime.now().isoformat()
        },
        "cli_client_1": {
            "client_type": "cli",
            "user_agent": "LeanVibe-CLI/1.0",
            "connected_at": datetime.now().isoformat(),
            "last_seen": datetime.now().isoformat()
        }
    }
    mock_manager.broadcast_to_ios_devices = AsyncMock(return_value=1)
    mock_manager.send_to_client = AsyncMock(return_value=True)
    return mock_manager


@pytest.fixture
def mock_session_manager():
    """Mock session manager for testing"""
    mock_manager = MagicMock()
    mock_manager.get_stats.return_value = {
        "active_sessions": 2,
        "total_requests": 150,
        "avg_response_time": 0.25,
        "error_rate": 0.02,
        "uptime_seconds": 3600,
        "memory_usage_mb": 128
    }
    return mock_manager


class TestCLIBridgeStatus:
    """Test CLI bridge status endpoints"""

    @patch('app.main.connection_manager')
    @patch('app.main.session_manager')
    def test_get_cli_status_active(self, mock_session_mgr, mock_conn_mgr, test_client, 
                                  mock_connection_manager, mock_session_manager):
        """Test CLI status with active connections"""
        mock_conn_mgr.get_connection_info.return_value = mock_connection_manager.get_connection_info()
        mock_session_mgr.get_stats.return_value = mock_session_manager.get_stats()
        
        # Add active CLI bridge connection
        cli_bridge_connections["test_cli"] = MagicMock()
        
        response = test_client.get("/cli/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"
        assert data["active_sessions"] == 2
        assert data["connected_ios_devices"] == 1
        assert "last_activity" in data
        
        # Cleanup
        cli_bridge_connections.clear()

    @patch('app.main.connection_manager')
    @patch('app.main.session_manager')
    def test_get_cli_status_idle(self, mock_session_mgr, mock_conn_mgr, test_client,
                                mock_connection_manager, mock_session_manager):
        """Test CLI status with no active CLI connections"""
        mock_conn_mgr.get_connection_info.return_value = mock_connection_manager.get_connection_info()
        mock_session_mgr.get_stats.return_value = mock_session_manager.get_stats()
        
        response = test_client.get("/cli/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "idle"
        assert data["active_sessions"] == 2
        assert data["connected_ios_devices"] == 1

    @patch('app.main.session_manager')
    @patch('app.main.connection_manager')
    def test_get_monitoring_data(self, mock_conn_mgr, mock_session_mgr, test_client,
                               mock_connection_manager, mock_session_manager):
        """Test monitoring data endpoint"""
        mock_session_mgr.get_stats.return_value = mock_session_manager.get_stats()
        mock_conn_mgr.get_connection_info.return_value = mock_connection_manager.get_connection_info()
        
        response = test_client.get("/cli/monitor")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "timestamp" in data
        assert "connections" in data
        assert "performance" in data
        assert "system" in data
        
        connections = data["connections"]
        assert connections["total"] == 2
        assert connections["ios_devices"] == 1
        assert connections["active_sessions"] == 2
        
        performance = data["performance"]
        assert performance["average_response_time"] == 0.25
        assert performance["total_requests"] == 150
        assert performance["error_rate"] == 0.02


class TestCLICommands:
    """Test CLI command execution and broadcasting"""

    @patch('app.main.connection_manager')
    @patch('app.main.event_streaming_service')
    def test_execute_cli_command_success(self, mock_event_service, mock_conn_mgr, 
                                       test_client, mock_connection_manager):
        """Test successful CLI command execution"""
        mock_conn_mgr.broadcast_to_ios_devices = mock_connection_manager.broadcast_to_ios_devices
        mock_event_service.emit_event = AsyncMock()
        
        command_data = {
            "command": "leanvibe status",
            "args": ["--verbose"],
            "workspace_path": "/path/to/project"
        }
        
        response = test_client.post("/cli/command", json=command_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["command"] == "leanvibe status"
        assert data["notified_devices"] == 1
        assert "timestamp" in data

    @patch('app.main.connection_manager')
    @patch('app.main.event_streaming_service')
    def test_execute_cli_command_failure(self, mock_event_service, mock_conn_mgr, test_client):
        """Test CLI command execution failure handling"""
        mock_conn_mgr.broadcast_to_ios_devices = AsyncMock(side_effect=Exception("Broadcast failed"))
        mock_event_service.emit_event = AsyncMock()
        
        command_data = {
            "command": "leanvibe test",
            "args": []
        }
        
        response = test_client.post("/cli/command", json=command_data)
        
        assert response.status_code == 500
        assert "Command execution failed" in response.json()["detail"]


class TestDeviceManagement:
    """Test iOS device management endpoints"""

    @patch('app.main.connection_manager')
    def test_list_connected_devices(self, mock_conn_mgr, test_client, mock_connection_manager):
        """Test listing connected iOS devices"""
        mock_conn_mgr.get_connection_info.return_value = mock_connection_manager.get_connection_info()
        
        response = test_client.get("/cli/devices")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "devices" in data
        assert "total_count" in data
        assert "timestamp" in data
        
        assert data["total_count"] == 1
        device = data["devices"][0]
        assert device["client_id"] == "ios_device_1"
        assert device["device_type"] == "ios"
        assert device["status"] == "connected"

    @patch('app.main.connection_manager')
    def test_send_message_to_device_success(self, mock_conn_mgr, test_client, mock_connection_manager):
        """Test sending message to specific device"""
        mock_conn_mgr.send_to_client = mock_connection_manager.send_to_client
        
        message_data = {
            "type": "test_message",
            "content": "Hello from CLI"
        }
        
        response = test_client.post("/cli/devices/ios_device_1/message", json=message_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["device_id"] == "ios_device_1"
        assert data["message_sent"] is True

    @patch('app.main.connection_manager')
    def test_send_message_to_device_not_found(self, mock_conn_mgr, test_client):
        """Test sending message to non-existent device"""
        mock_conn_mgr.send_to_client = AsyncMock(return_value=False)
        
        message_data = {
            "type": "test_message",
            "content": "Hello from CLI"
        }
        
        response = test_client.post("/cli/devices/nonexistent_device/message", json=message_data)
        
        assert response.status_code == 404
        assert "Device not found" in response.json()["detail"]


class TestBridgeStatus:
    """Test CLI bridge connection status"""

    def test_get_bridge_status_no_connections(self, test_client):
        """Test bridge status with no active connections"""
        cli_bridge_connections.clear()
        
        response = test_client.get("/cli/bridge/status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["active_bridges"] == 0
        assert data["bridge_ids"] == []
        assert data["status"] == "no_connections"

    def test_get_bridge_status_with_connections(self, test_client):
        """Test bridge status with active connections"""
        cli_bridge_connections["test_cli_1"] = MagicMock()
        cli_bridge_connections["test_cli_2"] = MagicMock()
        
        response = test_client.get("/cli/bridge/status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["active_bridges"] == 2
        assert "test_cli_1" in data["bridge_ids"]
        assert "test_cli_2" in data["bridge_ids"]
        assert data["status"] == "active"
        
        # Cleanup
        cli_bridge_connections.clear()


class TestCLIBridgeWebSocket:
    """Test CLI bridge WebSocket functionality"""

    def test_cli_bridge_websocket_connection(self, test_client):
        """Test WebSocket connection establishment"""
        with test_client.websocket_connect("/cli/bridge/test_cli") as websocket:
            # Should receive connection confirmation
            data = websocket.receive_json()
            
            assert data["type"] == "connection_established"
            assert data["cli_id"] == "test_cli"
            assert "timestamp" in data
            assert data["message"] == "CLI bridge connection active"

    @patch('app.api.endpoints.cli_bridge.get_monitoring_data')
    def test_cli_bridge_monitor_request(self, mock_get_monitoring, test_client):
        """Test monitoring data request via WebSocket"""
        mock_monitoring_data = {
            "timestamp": datetime.now().isoformat(),
            "connections": {"total": 1, "ios_devices": 0},
            "performance": {"average_response_time": 0.1}
        }
        mock_get_monitoring.return_value = mock_monitoring_data
        
        with test_client.websocket_connect("/cli/bridge/test_cli") as websocket:
            # Skip connection confirmation
            websocket.receive_json()
            
            # Send monitor request
            websocket.send_json({
                "type": "monitor_request"
            })
            
            # Should receive monitoring response
            response = websocket.receive_json()
            
            assert response["type"] == "monitor_response"
            assert "data" in response
            assert "timestamp" in response

    @patch('app.api.endpoints.cli_bridge.list_connected_devices')
    def test_cli_bridge_device_list_request(self, mock_list_devices, test_client):
        """Test device list request via WebSocket"""
        mock_devices_data = {
            "devices": [{"client_id": "ios_1", "status": "connected"}],
            "total_count": 1
        }
        mock_list_devices.return_value = mock_devices_data
        
        with test_client.websocket_connect("/cli/bridge/test_cli") as websocket:
            # Skip connection confirmation
            websocket.receive_json()
            
            # Send device list request
            websocket.send_json({
                "type": "device_list_request"
            })
            
            # Should receive device list response
            response = websocket.receive_json()
            
            assert response["type"] == "device_list_response"
            assert "data" in response
            assert response["data"]["total_count"] == 1

    @patch('app.main.connection_manager')
    def test_cli_bridge_command_broadcast(self, mock_conn_mgr, test_client):
        """Test command broadcast via WebSocket"""
        mock_conn_mgr.broadcast_to_ios_devices = AsyncMock(return_value=2)
        
        with test_client.websocket_connect("/cli/bridge/test_cli") as websocket:
            # Skip connection confirmation
            websocket.receive_json()
            
            # Send command broadcast
            websocket.send_json({
                "type": "command_broadcast",
                "data": {
                    "command": "leanvibe status",
                    "args": ["--json"]
                }
            })
            
            # Should receive broadcast confirmation
            response = websocket.receive_json()
            
            assert response["type"] == "broadcast_confirmation"
            assert response["devices_notified"] == 2

    def test_cli_bridge_heartbeat(self, test_client):
        """Test heartbeat via WebSocket"""
        with test_client.websocket_connect("/cli/bridge/test_cli") as websocket:
            # Skip connection confirmation
            websocket.receive_json()
            
            # Send heartbeat
            websocket.send_json({
                "type": "heartbeat"
            })
            
            # Should receive heartbeat acknowledgment
            response = websocket.receive_json()
            
            assert response["type"] == "heartbeat_ack"
            assert response["cli_id"] == "test_cli"

    def test_cli_bridge_unknown_message_type(self, test_client):
        """Test handling of unknown message types"""
        with test_client.websocket_connect("/cli/bridge/test_cli") as websocket:
            # Skip connection confirmation
            websocket.receive_json()
            
            # Send unknown message type
            websocket.send_json({
                "type": "unknown_message_type"
            })
            
            # Should receive error response
            response = websocket.receive_json()
            
            assert response["type"] == "error"
            assert "Unknown message type" in response["message"]

    def test_cli_bridge_invalid_json(self, test_client):
        """Test handling of invalid JSON"""
        with test_client.websocket_connect("/cli/bridge/test_cli") as websocket:
            # Skip connection confirmation
            websocket.receive_json()
            
            # Send invalid JSON
            websocket.send_text("invalid json")
            
            # Should receive error response
            response = websocket.receive_json()
            
            assert response["type"] == "error"
            assert "Invalid JSON format" in response["message"]


class TestCLICommandModel:
    """Test CLI command model validation"""

    def test_cli_command_valid(self):
        """Test valid CLI command creation"""
        command = CLICommand(
            command="leanvibe status",
            args=["--verbose"],
            workspace_path="/path/to/project"
        )
        
        assert command.command == "leanvibe status"
        assert command.args == ["--verbose"]
        assert command.workspace_path == "/path/to/project"

    def test_cli_command_minimal(self):
        """Test CLI command with minimal data"""
        command = CLICommand(command="leanvibe help")
        
        assert command.command == "leanvibe help"
        assert command.args == []
        assert command.workspace_path is None

    def test_cli_command_serialization(self):
        """Test CLI command JSON serialization"""
        command = CLICommand(
            command="leanvibe analyze",
            args=["--file", "main.py"],
            workspace_path="/project"
        )
        
        json_data = command.dict()
        
        assert json_data["command"] == "leanvibe analyze"
        assert json_data["args"] == ["--file", "main.py"]
        assert json_data["workspace_path"] == "/project"


@pytest.mark.integration
class TestCLIBridgeIntegration:
    """Integration tests for CLI bridge functionality"""

    @patch('app.main.event_streaming_service')
    @patch('app.main.connection_manager')
    def test_end_to_end_command_flow(self, mock_conn_mgr, mock_event_service, test_client):
        """Test complete command flow from CLI to iOS devices"""
        mock_conn_mgr.broadcast_to_ios_devices = AsyncMock(return_value=1)
        mock_event_service.emit_event = AsyncMock()
        
        # 1. Execute CLI command
        command_data = {
            "command": "leanvibe analyze",
            "args": ["--deep"],
            "workspace_path": "/test/project"
        }
        
        response = test_client.post("/cli/command", json=command_data)
        assert response.status_code == 200
        
        # 2. Verify event was emitted
        mock_event_service.emit_event.assert_called_once()
        
        # 3. Verify iOS devices were notified
        mock_conn_mgr.broadcast_to_ios_devices.assert_called_once()
        
        # 4. Check response contains expected data
        data = response.json()
        assert data["success"] is True
        assert data["command"] == "leanvibe analyze"
        assert data["notified_devices"] == 1

    def test_websocket_and_rest_consistency(self, test_client):
        """Test that WebSocket and REST endpoints provide consistent data"""
        # Test via REST
        rest_response = test_client.get("/cli/bridge/status")
        rest_data = rest_response.json()
        
        # Test via WebSocket would require more complex setup
        # For now, verify REST endpoint structure
        assert "active_bridges" in rest_data
        assert "bridge_ids" in rest_data
        assert "status" in rest_data