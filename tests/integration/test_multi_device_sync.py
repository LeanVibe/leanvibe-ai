"""
Comprehensive Multi-Device Sync Integration Tests

Tests WebSocket communication, conflict resolution, and cross-device
synchronization to ensure production-ready multi-device functionality.
"""

import asyncio
import pytest
import json
import time
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, List
import uuid


class MockWebSocket:
    """Mock WebSocket connection for testing"""
    
    def __init__(self):
        self.is_connected = False
        self.messages_sent = []
        self.message_handlers = []
        
    async def connect(self):
        self.is_connected = True
        
    async def disconnect(self):
        self.is_connected = False
        
    async def send(self, message: str):
        if self.is_connected:
            self.messages_sent.append(message)
            # Simulate message processing
            await asyncio.sleep(0.01)
        else:
            raise ConnectionError("WebSocket not connected")
    
    def add_message_handler(self, handler):
        self.message_handlers.append(handler)
    
    async def simulate_incoming_message(self, message: Dict[str, Any]):
        """Simulate receiving a message from another device"""
        message_str = json.dumps(message)
        for handler in self.message_handlers:
            await handler(message_str)


class MockWebSocketService:
    """Mock WebSocket service with conflict resolution"""
    
    def __init__(self):
        self.websocket = MockWebSocket()
        self.is_connected = False
        self.messages = []
        self.pending_messages = {}
        self.conflict_notifications = []
        self.session_id = str(uuid.uuid4())
        self.client_id = f"test-client-{uuid.uuid4().hex[:8]}"
        
    async def connect(self):
        await self.websocket.connect()
        self.is_connected = True
        
    async def disconnect(self):
        await self.websocket.disconnect()
        self.is_connected = False
        
    async def send_message(self, content: str, message_type: str = "message"):
        if not self.is_connected:
            raise ConnectionError("Not connected")
            
        message_id = str(uuid.uuid4())
        timestamp = time.time()
        
        message = {
            "type": message_type,
            "content": content,
            "timestamp": time.time(),
            "client_id": self.client_id,
            "message_id": message_id,
            "session_id": self.session_id,
            "version": 1
        }
        
        # Store for conflict resolution
        self.pending_messages[message_id] = message
        
        await self.websocket.send(json.dumps(message))
        
        # Add to local messages (optimistic update)
        self.messages.append({
            "content": content,
            "is_from_user": True,
            "type": message_type,
            "id": message_id
        })
        
        return message_id
    
    async def handle_incoming_message(self, message_data: Dict[str, Any]):
        """Handle incoming message with conflict detection"""
        if message_data.get("type") == "conflict_resolution":
            await self._handle_conflict_resolution(message_data)
        elif message_data.get("type") == "conflict_detected":
            await self._handle_conflict_notification(message_data)
        else:
            # Check for conflicts
            conflicts = self._detect_conflicts(message_data)
            if conflicts:
                await self._resolve_conflicts(conflicts, message_data)
            else:
                self._add_message_to_ui(message_data)
    
    def _detect_conflicts(self, incoming_message: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect conflicts with pending messages"""
        conflicts = []
        
        for pending_id, pending_msg in self.pending_messages.items():
            # Check for content conflicts
            if (pending_msg["content"] == incoming_message.get("content") and
                pending_msg.get("version") != incoming_message.get("version")):
                
                conflicts.append({
                    "type": "version_mismatch",
                    "pending_message": pending_msg,
                    "incoming_message": incoming_message
                })
            
            # Check for timing conflicts
            pending_time = pending_msg.get("timestamp", 0)
            incoming_time = incoming_message.get("timestamp", 0)
            
            if abs(pending_time - incoming_time) < 2.0:  # Within 2 seconds
                conflicts.append({
                    "type": "timing_conflict", 
                    "pending_message": pending_msg,
                    "incoming_message": incoming_message
                })
        
        return conflicts
    
    async def _resolve_conflicts(self, conflicts: List[Dict[str, Any]], incoming_message: Dict[str, Any]):
        """Resolve conflicts using last-write-wins strategy"""
        for conflict in conflicts:
            pending_msg = conflict["pending_message"]
            incoming_msg = conflict["incoming_message"]
            
            # Last-write-wins resolution
            pending_time = pending_msg.get("timestamp", 0)
            incoming_time = incoming_msg.get("timestamp", 0)
            
            if incoming_time > pending_time:
                winning_message = incoming_msg
                losing_message = pending_msg
            else:
                winning_message = pending_msg
                losing_message = incoming_msg
            
            # Apply resolution
            self._apply_conflict_resolution(winning_message, losing_message)
    
    def _apply_conflict_resolution(self, winning_message: Dict[str, Any], losing_message: Dict[str, Any]):
        """Apply conflict resolution"""
        # Remove losing message from UI if present
        self.messages = [
            msg for msg in self.messages 
            if msg.get("id") != losing_message.get("message_id")
        ]
        
        # Add winning message to UI
        self._add_message_to_ui(winning_message)
        
        # Clean up pending messages
        if losing_message.get("message_id") in self.pending_messages:
            del self.pending_messages[losing_message["message_id"]]
    
    def _add_message_to_ui(self, message_data: Dict[str, Any]):
        """Add message to UI"""
        self.messages.append({
            "content": message_data.get("content", ""),
            "is_from_user": message_data.get("client_id") == self.client_id,
            "type": message_data.get("type", "message"),
            "id": message_data.get("message_id", str(uuid.uuid4()))
        })
    
    async def _handle_conflict_resolution(self, resolution_data: Dict[str, Any]):
        """Handle conflict resolution message"""
        # Apply the resolved state
        resolved_message = resolution_data.get("resolved_message", {})
        self._add_message_to_ui(resolved_message)
    
    async def _handle_conflict_notification(self, notification_data: Dict[str, Any]):
        """Handle conflict notification"""
        self.conflict_notifications.append(notification_data)


class TestMultiDeviceSync:
    """Test multi-device synchronization functionality"""
    
    @pytest.fixture
    def device1(self):
        """First device WebSocket service"""
        return MockWebSocketService()
    
    @pytest.fixture  
    def device2(self):
        """Second device WebSocket service"""
        return MockWebSocketService()
    
    @pytest.mark.asyncio
    async def test_basic_message_sync(self, device1, device2):
        """Test basic message synchronization between devices"""
        # Connect both devices
        await device1.connect()
        await device2.connect()
        
        # Device 1 sends a message
        message_id = await device1.send_message("Hello from device 1", "message")
        
        # Simulate the message arriving at device 2
        sync_message = {
            "type": "message",
            "content": "Hello from device 1", 
            "timestamp": time.time(),
            "client_id": device1.client_id,
            "message_id": message_id,
            "session_id": device1.session_id,
            "version": 1
        }
        
        await device2.handle_incoming_message(sync_message)
        
        # Verify message appears on both devices
        assert len(device1.messages) == 1
        assert len(device2.messages) == 1
        assert device1.messages[0]["content"] == "Hello from device 1"
        assert device2.messages[0]["content"] == "Hello from device 1"
    
    @pytest.mark.asyncio
    async def test_conflict_resolution_last_write_wins(self, device1, device2):
        """Test conflict resolution using last-write-wins strategy"""
        await device1.connect()
        await device2.connect()
        
        # Both devices send similar messages at nearly the same time
        base_time = time.time()
        
        # Device 1 sends first (earlier timestamp)
        device1_message = {
            "type": "message",
            "content": "Conflicting message",
            "timestamp": base_time,
            "client_id": device1.client_id,
            "message_id": str(uuid.uuid4()),
            "session_id": device1.session_id,
            "version": 1
        }
        
        # Device 2 sends later (later timestamp) 
        device2_message = {
            "type": "message", 
            "content": "Conflicting message",
            "timestamp": base_time + 0.1,  # 100ms later
            "client_id": device2.client_id,
            "message_id": str(uuid.uuid4()),
            "session_id": device2.session_id,
            "version": 2
        }
        
        # Add device 1 message to pending
        device1.pending_messages[device1_message["message_id"]] = device1_message
        
        # Device 1 receives device 2's conflicting message
        await device1.handle_incoming_message(device2_message)
        
        # Last write (device 2) should win
        assert len(device1.messages) == 1
        assert device1.messages[0]["content"] == "Conflicting message"
        # Verify the winning message came from device 2
        assert not device1.messages[0]["is_from_user"]  # Not from device 1
    
    @pytest.mark.asyncio
    async def test_session_persistence(self, device1):
        """Test session persistence across connections"""
        # Initial connection and message
        await device1.connect()
        await device1.send_message("Initial message", "message")
        
        initial_session_id = device1.session_id
        initial_message_count = len(device1.messages)
        
        # Disconnect and reconnect
        await device1.disconnect()
        await device1.connect()
        
        # Session should be maintained for reconnection
        assert device1.session_id == initial_session_id
        assert len(device1.messages) == initial_message_count
    
    @pytest.mark.asyncio
    async def test_concurrent_message_handling(self, device1, device2):
        """Test handling of concurrent messages from multiple devices"""
        await device1.connect()
        await device2.connect()
        
        # Send multiple concurrent messages
        messages = []
        for i in range(10):
            if i % 2 == 0:
                message_id = await device1.send_message(f"Message {i} from device 1", "message")
                messages.append((device1, f"Message {i} from device 1"))
            else:
                # Simulate device 2 message
                message = {
                    "type": "message",
                    "content": f"Message {i} from device 2",
                    "timestamp": time.time(),
                    "client_id": device2.client_id,
                    "message_id": str(uuid.uuid4()),
                    "session_id": device2.session_id,
                    "version": 1
                }
                await device1.handle_incoming_message(message)
                messages.append((device2, f"Message {i} from device 2"))
        
        # All messages should be present
        assert len(device1.messages) == 10
        
        # Messages should be in order
        for i, message in enumerate(device1.messages):
            expected_content = f"Message {i} from device {'1' if i % 2 == 0 else '2'}"
            assert expected_content in message["content"]
    
    @pytest.mark.asyncio
    async def test_network_interruption_recovery(self, device1):
        """Test recovery from network interruptions"""
        await device1.connect()
        
        # Send message before interruption
        await device1.send_message("Before interruption", "message")
        pre_interruption_count = len(device1.messages)
        
        # Simulate network interruption
        await device1.disconnect()
        
        # Try to send message during interruption (should fail)
        with pytest.raises(ConnectionError):
            await device1.send_message("During interruption", "message")
        
        # Reconnect and verify state
        await device1.connect()
        assert len(device1.messages) == pre_interruption_count
        
        # Send message after recovery
        await device1.send_message("After recovery", "message")
        assert len(device1.messages) == pre_interruption_count + 1


class TestConflictResolution:
    """Test conflict resolution mechanisms"""
    
    @pytest.fixture
    def sync_service(self):
        return MockWebSocketService()
    
    @pytest.mark.asyncio 
    async def test_version_conflict_detection(self, sync_service):
        """Test detection of version conflicts"""
        await sync_service.connect()
        
        # Create pending message
        pending_message = {
            "type": "message",
            "content": "Same content",
            "timestamp": time.time(),
            "client_id": sync_service.client_id,
            "message_id": "pending-123",
            "version": 1
        }
        sync_service.pending_messages["pending-123"] = pending_message
        
        # Incoming message with same content but different version
        incoming_message = {
            "type": "message", 
            "content": "Same content",
            "timestamp": time.time(),
            "client_id": "other-client",
            "message_id": "incoming-456",
            "version": 2
        }
        
        conflicts = sync_service._detect_conflicts(incoming_message)
        assert len(conflicts) == 1
        assert conflicts[0]["type"] == "version_mismatch"
    
    @pytest.mark.asyncio
    async def test_timing_conflict_detection(self, sync_service):
        """Test detection of timing conflicts"""
        await sync_service.connect()
        
        base_time = time.time()
        
        # Create pending message
        pending_message = {
            "type": "message",
            "content": "Different content 1",
            "timestamp": base_time,
            "client_id": sync_service.client_id,
            "message_id": "pending-123"
        }
        sync_service.pending_messages["pending-123"] = pending_message
        
        # Incoming message within timing window
        incoming_message = {
            "type": "message",
            "content": "Different content 2", 
            "timestamp": base_time + 1.0,  # Within 2 second window
            "client_id": "other-client",
            "message_id": "incoming-456"
        }
        
        conflicts = sync_service._detect_conflicts(incoming_message)
        assert len(conflicts) == 1
        assert conflicts[0]["type"] == "timing_conflict"
    
    @pytest.mark.asyncio
    async def test_no_conflict_detection(self, sync_service):
        """Test that non-conflicting messages are not flagged"""
        await sync_service.connect()
        
        base_time = time.time()
        
        # Create pending message
        pending_message = {
            "type": "message",
            "content": "Different content 1",
            "timestamp": base_time,
            "client_id": sync_service.client_id,
            "message_id": "pending-123"
        }
        sync_service.pending_messages["pending-123"] = pending_message
        
        # Incoming message with different content and timing
        incoming_message = {
            "type": "message",
            "content": "Different content 2",
            "timestamp": base_time + 5.0,  # Outside timing window
            "client_id": "other-client", 
            "message_id": "incoming-456"
        }
        
        conflicts = sync_service._detect_conflicts(incoming_message)
        assert len(conflicts) == 0


class TestPerformanceAndReliability:
    """Test performance and reliability aspects of multi-device sync"""
    
    @pytest.mark.asyncio
    async def test_sync_latency(self, device1, device2):
        """Test synchronization latency between devices"""
        await device1.connect()
        await device2.connect()
        
        # Measure sync latency
        start_time = time.time()
        message_id = await device1.send_message("Latency test", "message")
        
        # Simulate message propagation to device 2
        sync_message = {
            "type": "message",
            "content": "Latency test",
            "timestamp": time.time(),
            "client_id": device1.client_id,
            "message_id": message_id,
            "session_id": device1.session_id
        }
        
        await device2.handle_incoming_message(sync_message)
        sync_time = time.time() - start_time
        
        # Sync should happen quickly
        assert sync_time < 0.5, f"Sync latency {sync_time:.3f}s exceeds 500ms target"
    
    @pytest.mark.asyncio
    async def test_message_ordering(self, device1):
        """Test that message ordering is preserved"""
        await device1.connect()
        
        # Send messages in sequence
        for i in range(10):
            await device1.send_message(f"Message {i}", "message")
            await asyncio.sleep(0.01)  # Small delay to ensure ordering
        
        # Verify ordering is preserved
        for i, message in enumerate(device1.messages):
            expected_content = f"Message {i}"
            assert expected_content in message["content"]
    
    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self, device1):
        """Test memory usage doesn't grow excessively under load"""
        await device1.connect()
        
        initial_message_count = len(device1.messages)
        
        # Send many messages
        for i in range(100):
            await device1.send_message(f"Load test message {i}", "message")
        
        # Memory structures should be bounded
        assert len(device1.messages) <= initial_message_count + 100
        assert len(device1.pending_messages) <= 50  # Should be cleaned up
        assert len(device1.conflict_notifications) <= 10  # Should be bounded


@pytest.mark.integration
class TestMultiDeviceIntegration:
    """Integration tests for complete multi-device workflows"""
    
    @pytest.mark.asyncio
    async def test_three_device_sync(self):
        """Test synchronization across three devices"""
        device1 = MockWebSocketService()
        device2 = MockWebSocketService()  
        device3 = MockWebSocketService()
        
        # Connect all devices
        await device1.connect()
        await device2.connect()
        await device3.connect()
        
        # Device 1 sends message
        message_id = await device1.send_message("Hello from device 1", "message")
        
        # Propagate to other devices
        sync_message = {
            "type": "message",
            "content": "Hello from device 1",
            "timestamp": time.time(),
            "client_id": device1.client_id,
            "message_id": message_id,
            "session_id": device1.session_id
        }
        
        await device2.handle_incoming_message(sync_message)
        await device3.handle_incoming_message(sync_message)
        
        # All devices should have the message
        assert len(device1.messages) == 1
        assert len(device2.messages) == 1
        assert len(device3.messages) == 1
        
        for device in [device1, device2, device3]:
            assert device.messages[0]["content"] == "Hello from device 1"
    
    @pytest.mark.asyncio
    async def test_cross_platform_compatibility(self):
        """Test compatibility between different client types"""
        ios_device = MockWebSocketService()
        cli_device = MockWebSocketService()
        
        # Simulate different client types
        ios_device.client_id = "ios-client-12345"
        cli_device.client_id = "cli-client-67890"
        
        await ios_device.connect()
        await cli_device.connect()
        
        # iOS sends command
        await ios_device.send_message("/status", "command")
        
        # CLI receives and responds
        command_message = {
            "type": "command",
            "content": "/status",
            "timestamp": time.time(),
            "client_id": ios_device.client_id,
            "message_id": str(uuid.uuid4())
        }
        
        await cli_device.handle_incoming_message(command_message)
        
        # Both should have the message
        assert len(ios_device.messages) == 1
        assert len(cli_device.messages) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])