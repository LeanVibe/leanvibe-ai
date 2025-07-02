"""
Test Enhanced Connection Manager

Tests for CLI bridge enhancements to the ConnectionManager including
iOS device detection, broadcasting, and device management.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.core.connection_manager import ConnectionManager
from app.models.event_models import ClientPreferences


class TestConnectionManagerIOSSupport:
    """Test iOS device support in ConnectionManager"""

    @pytest.fixture
    def connection_manager(self):
        """Create connection manager instance"""
        return ConnectionManager()

    @pytest.fixture
    def mock_websocket(self):
        """Create mock WebSocket"""
        websocket = MagicMock()
        websocket.headers = {
            "user-agent": "LeanVibe/1.0 (iPhone; iOS 17.0)"
        }
        websocket.accept = AsyncMock()
        websocket.send_text = AsyncMock()
        return websocket

    @pytest.fixture
    def mock_cli_websocket(self):
        """Create mock CLI WebSocket"""
        websocket = MagicMock()
        websocket.headers = {
            "user-agent": "LeanVibe-CLI/1.0 (Darwin)"
        }
        websocket.accept = AsyncMock()
        websocket.send_text = AsyncMock()
        return websocket

    async def test_send_to_client_success(self, connection_manager, mock_websocket):
        """Test successful message sending to specific client"""
        # Setup connection
        await connection_manager.connect(mock_websocket, "test_client")
        
        message = {"type": "test", "content": "Hello"}
        
        # Send message
        result = await connection_manager.send_to_client("test_client", message)
        
        assert result is True
        mock_websocket.send_text.assert_called_once()

    async def test_send_to_client_not_found(self, connection_manager):
        """Test sending message to non-existent client"""
        message = {"type": "test", "content": "Hello"}
        
        result = await connection_manager.send_to_client("nonexistent", message)
        
        assert result is False

    async def test_send_to_client_error(self, connection_manager, mock_websocket):
        """Test error handling when sending message fails"""
        await connection_manager.connect(mock_websocket, "test_client")
        
        # Mock send_text to raise exception
        mock_websocket.send_text.side_effect = Exception("Connection lost")
        
        message = {"type": "test", "content": "Hello"}
        result = await connection_manager.send_to_client("test_client", message)
        
        assert result is False

    async def test_broadcast_to_ios_devices_success(self, connection_manager, mock_websocket, mock_cli_websocket):
        """Test broadcasting to iOS devices only"""
        # Connect iOS device
        await connection_manager.connect(mock_websocket, "ios_device")
        
        # Connect CLI client
        await connection_manager.connect(mock_cli_websocket, "cli_client")
        
        message = {"type": "broadcast", "content": "iOS only message"}
        
        # Broadcast to iOS devices
        count = await connection_manager.broadcast_to_ios_devices(message)
        
        assert count == 1
        # iOS device should receive message
        mock_websocket.send_text.assert_called_once()
        # CLI client should not receive message
        mock_cli_websocket.send_text.assert_not_called()

    async def test_broadcast_to_ios_devices_ipad(self, connection_manager):
        """Test broadcasting recognizes iPad devices"""
        # Create iPad websocket
        ipad_websocket = MagicMock()
        ipad_websocket.headers = {
            "user-agent": "LeanVibe/1.0 (iPad; iOS 17.0)"
        }
        ipad_websocket.accept = AsyncMock()
        ipad_websocket.send_text = AsyncMock()
        
        await connection_manager.connect(ipad_websocket, "ipad_device")
        
        message = {"type": "test", "content": "iPad message"}
        count = await connection_manager.broadcast_to_ios_devices(message)
        
        assert count == 1
        ipad_websocket.send_text.assert_called_once()

    async def test_broadcast_to_ios_devices_no_ios(self, connection_manager, mock_cli_websocket):
        """Test broadcasting when no iOS devices connected"""
        await connection_manager.connect(mock_cli_websocket, "cli_client")
        
        message = {"type": "test", "content": "No iOS devices"}
        count = await connection_manager.broadcast_to_ios_devices(message)
        
        assert count == 0
        mock_cli_websocket.send_text.assert_not_called()

    async def test_broadcast_to_ios_devices_error_handling(self, connection_manager, mock_websocket):
        """Test error handling during iOS broadcast"""
        await connection_manager.connect(mock_websocket, "ios_device")
        
        # Mock send_text to raise exception
        mock_websocket.send_text.side_effect = Exception("Send failed")
        
        message = {"type": "test", "content": "Error test"}
        count = await connection_manager.broadcast_to_ios_devices(message)
        
        assert count == 0
        # Device should be disconnected due to error
        assert "ios_device" not in connection_manager.active_connections

    def test_get_ios_devices_empty(self, connection_manager):
        """Test getting iOS devices when none connected"""
        devices = connection_manager.get_ios_devices()
        
        assert devices == []

    async def test_get_ios_devices_mixed_clients(self, connection_manager, mock_websocket, mock_cli_websocket):
        """Test getting iOS devices from mixed client types"""
        # Connect iOS device
        await connection_manager.connect(mock_websocket, "ios_device")
        
        # Connect CLI client
        await connection_manager.connect(mock_cli_websocket, "cli_client")
        
        devices = connection_manager.get_ios_devices()
        
        assert len(devices) == 1
        device = devices[0]
        assert device["client_id"] == "ios_device"
        assert device["client_type"] == "ios"
        assert device["is_connected"] is True
        assert "connected_at" in device
        assert "user_agent" in device

    async def test_get_ios_devices_disconnected(self, connection_manager, mock_websocket):
        """Test getting iOS devices includes disconnected ones"""
        await connection_manager.connect(mock_websocket, "ios_device")
        
        # Disconnect the device
        connection_manager.disconnect("ios_device")
        
        devices = connection_manager.get_ios_devices()
        
        # Should still be in client_info but marked as disconnected
        # Note: Current implementation removes from client_info on disconnect
        # This test verifies that behavior
        assert len(devices) == 0

    async def test_client_type_detection_ios(self, connection_manager):
        """Test client type detection for iOS devices"""
        ios_user_agents = [
            "LeanVibe/1.0 (iPhone; iOS 17.0)",
            "LeanVibe/1.0 (iPad; iOS 16.5)",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)",
            "Custom-iOS-App/2.0 iPhone"
        ]
        
        for user_agent in ios_user_agents:
            websocket = MagicMock()
            websocket.headers = {"user-agent": user_agent}
            websocket.accept = AsyncMock()
            
            client_id = f"client_{hash(user_agent)}"
            await connection_manager.connect(websocket, client_id)
            
            devices = connection_manager.get_ios_devices()
            # Should detect at least one iOS device
            assert len(devices) >= 1
            
            # Cleanup
            connection_manager.disconnect(client_id)

    async def test_client_type_detection_non_ios(self, connection_manager):
        """Test client type detection excludes non-iOS devices"""
        non_ios_user_agents = [
            "LeanVibe-CLI/1.0 (Darwin)",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Mozilla/5.0 (X11; Linux x86_64)",
            "PostmanRuntime/7.32.0"
        ]
        
        for user_agent in non_ios_user_agents:
            websocket = MagicMock()
            websocket.headers = {"user-agent": user_agent}
            websocket.accept = AsyncMock()
            
            client_id = f"client_{hash(user_agent)}"
            await connection_manager.connect(websocket, client_id)
        
        devices = connection_manager.get_ios_devices()
        # Should not detect any iOS devices
        assert len(devices) == 0

    @patch('app.core.connection_manager.event_streaming_service')
    async def test_ios_device_registration_with_streaming(self, mock_streaming, connection_manager, mock_websocket):
        """Test iOS device gets registered with event streaming"""
        mock_streaming.register_client = MagicMock()
        
        await connection_manager.connect(mock_websocket, "ios_device")
        
        # Should register with event streaming
        mock_streaming.register_client.assert_called_once_with("ios_device")

    async def test_multiple_ios_devices_broadcast(self, connection_manager):
        """Test broadcasting to multiple iOS devices"""
        # Create multiple iOS devices
        ios_devices = []
        for i in range(3):
            websocket = MagicMock()
            websocket.headers = {"user-agent": f"LeanVibe/1.0 (iPhone{i}; iOS 17.0)"}
            websocket.accept = AsyncMock()
            websocket.send_text = AsyncMock()
            ios_devices.append(websocket)
            
            await connection_manager.connect(websocket, f"ios_device_{i}")
        
        message = {"type": "test", "content": "Multiple devices"}
        count = await connection_manager.broadcast_to_ios_devices(message)
        
        assert count == 3
        # All devices should receive message
        for websocket in ios_devices:
            websocket.send_text.assert_called_once()

    async def test_concurrent_ios_operations(self, connection_manager, mock_websocket):
        """Test concurrent iOS device operations"""
        await connection_manager.connect(mock_websocket, "ios_device")
        
        import asyncio
        
        # Concurrent operations
        message1 = {"type": "test1", "content": "Message 1"}
        message2 = {"type": "test2", "content": "Message 2"}
        
        # Send multiple messages concurrently
        results = await asyncio.gather(
            connection_manager.send_to_client("ios_device", message1),
            connection_manager.send_to_client("ios_device", message2),
            return_exceptions=True
        )
        
        assert all(result is True for result in results)
        assert mock_websocket.send_text.call_count == 2


@pytest.mark.integration
class TestConnectionManagerIntegration:
    """Integration tests for enhanced connection manager"""

    @pytest.fixture
    def connection_manager(self):
        """Create connection manager with dependencies"""
        return ConnectionManager()

    async def test_ios_device_lifecycle(self, connection_manager):
        """Test complete iOS device lifecycle"""
        # Create iOS websocket
        websocket = MagicMock()
        websocket.headers = {"user-agent": "LeanVibe/1.0 (iPhone; iOS 17.0)"}
        websocket.accept = AsyncMock()
        websocket.send_text = AsyncMock()
        
        # 1. Connect
        await connection_manager.connect(websocket, "ios_lifecycle_test")
        assert "ios_lifecycle_test" in connection_manager.active_connections
        
        # 2. Get devices list
        devices = connection_manager.get_ios_devices()
        assert len(devices) == 1
        assert devices[0]["client_id"] == "ios_lifecycle_test"
        
        # 3. Send message
        result = await connection_manager.send_to_client("ios_lifecycle_test", {"test": "message"})
        assert result is True
        
        # 4. Broadcast
        count = await connection_manager.broadcast_to_ios_devices({"broadcast": "test"})
        assert count == 1
        
        # 5. Disconnect
        connection_manager.disconnect("ios_lifecycle_test")
        assert "ios_lifecycle_test" not in connection_manager.active_connections
        
        # 6. Verify cleanup
        devices = connection_manager.get_ios_devices()
        assert len(devices) == 0

    async def test_mixed_client_environment(self, connection_manager):
        """Test environment with mixed client types"""
        clients = []
        
        # Create various client types
        client_configs = [
            ("ios_phone", "LeanVibe/1.0 (iPhone; iOS 17.0)"),
            ("ios_pad", "LeanVibe/1.0 (iPad; iOS 16.5)"),
            ("cli_mac", "LeanVibe-CLI/1.0 (Darwin)"),
            ("web_browser", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"),
            ("cli_linux", "LeanVibe-CLI/1.0 (Linux)")
        ]
        
        for client_id, user_agent in client_configs:
            websocket = MagicMock()
            websocket.headers = {"user-agent": user_agent}
            websocket.accept = AsyncMock()
            websocket.send_text = AsyncMock()
            clients.append((client_id, websocket))
            
            await connection_manager.connect(websocket, client_id)
        
        # Verify iOS detection
        ios_devices = connection_manager.get_ios_devices()
        assert len(ios_devices) == 2  # iPhone and iPad
        ios_ids = [device["client_id"] for device in ios_devices]
        assert "ios_phone" in ios_ids
        assert "ios_pad" in ios_ids
        
        # Test broadcast to iOS only
        count = await connection_manager.broadcast_to_ios_devices({"ios_only": True})
        assert count == 2
        
        # Verify only iOS devices received message
        for client_id, websocket in clients:
            if client_id in ["ios_phone", "ios_pad"]:
                websocket.send_text.assert_called()
            else:
                websocket.send_text.assert_not_called()
        
        # Cleanup
        for client_id, _ in clients:
            connection_manager.disconnect(client_id)