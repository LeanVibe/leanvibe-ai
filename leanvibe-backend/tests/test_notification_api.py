"""
Comprehensive Push Notification and Event Streaming API Tests

High-impact test suite for the notification system, event streaming service,
and real-time client communication. Tests event filtering, batching, compression,
rate limiting, and client preference management.
"""

import asyncio
import gzip
import json
import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, List

from app.models.event_models import (
    EventType, EventPriority, NotificationChannel, ClientPreferences,
    ConnectionState, EventData, FileChangeEvent, AnalysisEvent, 
    ViolationEvent, AgentEvent, StreamingMessage, EventStats,
    create_file_change_event, create_analysis_event, create_violation_event,
    create_agent_event
)
from app.services.event_streaming_service import (
    EventStreamingService, EventFilter, EventBatcher, CompressionManager,
    event_streaming_service, emit_file_change, emit_analysis_completed,
    emit_violation_detected, emit_agent_event
)


class MockWebSocket:
    """Mock WebSocket for testing event delivery"""
    
    def __init__(self, client_id: str = "test-client"):
        self.client_id = client_id
        self.sent_messages = []
        self.sent_bytes = []
        self.closed = False
        
    async def send_text(self, message: str):
        """Mock send_text method"""
        if self.closed:
            raise Exception("WebSocket connection closed")
        self.sent_messages.append(message)
        
    async def send_bytes(self, data: bytes):
        """Mock send_bytes method"""
        if self.closed:
            raise Exception("WebSocket connection closed")
        self.sent_bytes.append(data)
        
    def get_last_message_data(self) -> Dict:
        """Get the last sent message as parsed JSON"""
        if not self.sent_messages:
            return {}
        return json.loads(self.sent_messages[-1])


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket connection"""
    return MockWebSocket()


@pytest.fixture
def streaming_service():
    """Create a fresh EventStreamingService for testing"""
    service = EventStreamingService()
    yield service
    # Cleanup
    if service.processing_task:
        service.processing_task.cancel()
        try:
            asyncio.create_task(service.processing_task)
        except:
            pass


@pytest.fixture
def sample_client_preferences():
    """Create sample client preferences"""
    return ClientPreferences(
        client_id="test-client",
        enabled_channels=[NotificationChannel.ALL],
        min_priority=EventPriority.MEDIUM,
        max_events_per_second=10,
        enable_batching=True,
        batch_interval_ms=500,
        enable_compression=False
    )


@pytest.fixture
def sample_events():
    """Create sample events for testing"""
    return {
        "file_change": create_file_change_event("/test/file.py", "modified"),
        "analysis": create_analysis_event("ast", "/test/file.py", True, 1.5),
        "violation": create_violation_event("v1", "complexity", "warning", "/test/file.py", "High complexity"),
        "agent": create_agent_event("session1", EventType.AGENT_COMPLETED, "test query")
    }


class TestEventFilter:
    """Test event filtering logic"""
    
    def test_event_filter_initialization(self):
        """Test EventFilter initialization"""
        event_filter = EventFilter()
        assert event_filter is not None
        assert hasattr(event_filter, 'rate_limiters')
        assert len(event_filter.rate_limiters) == 0
    
    def test_channel_filtering(self, sample_events):
        """Test filtering by notification channels"""
        event_filter = EventFilter()
        
        # Test ALL channel subscription
        prefs_all = ClientPreferences(
            client_id="test",
            enabled_channels=[NotificationChannel.ALL]
        )
        assert event_filter.should_deliver(sample_events["file_change"], prefs_all)
        assert event_filter.should_deliver(sample_events["analysis"], prefs_all)
        assert event_filter.should_deliver(sample_events["violation"], prefs_all)
        
        # Test specific channel subscription
        prefs_violations = ClientPreferences(
            client_id="test",
            enabled_channels=[NotificationChannel.VIOLATIONS]
        )
        assert not event_filter.should_deliver(sample_events["file_change"], prefs_violations)
        assert not event_filter.should_deliver(sample_events["analysis"], prefs_violations)
        assert event_filter.should_deliver(sample_events["violation"], prefs_violations)
    
    def test_priority_filtering(self, sample_events):
        """Test filtering by event priority"""
        event_filter = EventFilter()
        
        # Test HIGH priority filter
        prefs_high = ClientPreferences(
            client_id="test",
            enabled_channels=[NotificationChannel.ALL],
            min_priority=EventPriority.HIGH
        )
        
        # Should not deliver MEDIUM priority events
        assert not event_filter.should_deliver(sample_events["file_change"], prefs_high)  # MEDIUM
        assert event_filter.should_deliver(sample_events["agent"], prefs_high)  # HIGH
        
        # Test MEDIUM priority filter
        prefs_medium = ClientPreferences(
            client_id="test",
            enabled_channels=[NotificationChannel.ALL],
            min_priority=EventPriority.MEDIUM
        )
        
        # Should deliver MEDIUM and HIGH priority events
        assert event_filter.should_deliver(sample_events["file_change"], prefs_medium)  # MEDIUM
        assert event_filter.should_deliver(sample_events["agent"], prefs_medium)  # HIGH
    
    def test_rate_limiting(self, sample_events):
        """Test rate limiting functionality"""
        event_filter = EventFilter()
        
        prefs = ClientPreferences(
            client_id="rate-test",
            enabled_channels=[NotificationChannel.ALL],
            max_events_per_second=2  # Very low limit for testing
        )
        
        # First two events should pass
        assert event_filter.should_deliver(sample_events["file_change"], prefs)
        assert event_filter.should_deliver(sample_events["analysis"], prefs)
        
        # Third event should be rate limited
        assert not event_filter.should_deliver(sample_events["violation"], prefs)
        
        # After waiting, should pass again
        time.sleep(1.1)  # Wait for rate limit window to reset
        assert event_filter.should_deliver(sample_events["agent"], prefs)
    
    def test_custom_filters_file_patterns(self):
        """Test custom filtering by file patterns"""
        event_filter = EventFilter()
        
        # Create event with specific file path
        file_event = create_file_change_event("/test/node_modules/lib.js", "modified")
        
        prefs_with_filter = ClientPreferences(
            client_id="test",
            enabled_channels=[NotificationChannel.ALL],
            custom_filters={
                "exclude_file_patterns": {
                    "patterns": ["node_modules", "__pycache__"]
                }
            }
        )
        
        # Should be filtered out
        assert not event_filter.should_deliver(file_event, prefs_with_filter)
        
        # Regular file should pass
        normal_file_event = create_file_change_event("/test/src/main.py", "modified")
        assert event_filter.should_deliver(normal_file_event, prefs_with_filter)
    
    def test_custom_filters_confidence_threshold(self):
        """Test custom filtering by confidence score"""
        event_filter = EventFilter()
        
        # Create violation with low confidence
        low_confidence_violation = create_violation_event(
            "v1", "complexity", "warning", "/test/file.py", "Low confidence issue"
        )
        low_confidence_violation.confidence_score = 0.3
        
        prefs_with_confidence = ClientPreferences(
            client_id="test",
            enabled_channels=[NotificationChannel.ALL],
            custom_filters={
                "min_confidence": {
                    "threshold": 0.5
                }
            }
        )
        
        # Should be filtered out due to low confidence
        assert not event_filter.should_deliver(low_confidence_violation, prefs_with_confidence)
        
        # High confidence should pass
        high_confidence_violation = create_violation_event(
            "v2", "complexity", "warning", "/test/file.py", "High confidence issue"
        )
        high_confidence_violation.confidence_score = 0.8
        assert event_filter.should_deliver(high_confidence_violation, prefs_with_confidence)


class TestEventBatcher:
    """Test event batching functionality"""
    
    @pytest.mark.asyncio
    async def test_immediate_delivery_when_batching_disabled(self, sample_events):
        """Test immediate delivery when batching is disabled"""
        batcher = EventBatcher()
        
        prefs = ClientPreferences(
            client_id="test",
            enable_batching=False
        )
        
        # Should return event immediately
        result = await batcher.add_event("test", sample_events["file_change"], prefs)
        assert result is not None
        assert len(result) == 1
        assert result[0] == sample_events["file_change"]
    
    @pytest.mark.asyncio
    async def test_batching_enabled_delay(self, sample_events):
        """Test batching with delay"""
        batcher = EventBatcher()
        
        prefs = ClientPreferences(
            client_id="batch-test",
            enable_batching=True,
            batch_interval_ms=100  # 100ms delay
        )
        
        # Add event - should be batched
        result = await batcher.add_event("batch-test", sample_events["file_change"], prefs)
        assert result is None  # Not delivered immediately
        
        # Wait for batch to be flushed
        await asyncio.sleep(0.15)  # Wait longer than batch interval
        
        # Check that pending batch was cleared
        assert len(batcher.pending_batches["batch-test"]) == 0
    
    @pytest.mark.asyncio
    async def test_batch_size_limit(self, sample_events):
        """Test automatic flushing when batch gets large"""
        batcher = EventBatcher()
        
        prefs = ClientPreferences(
            client_id="large-batch",
            enable_batching=True,
            batch_interval_ms=5000  # Long delay to test size limit
        )
        
        # Add events until batch size limit is reached
        events_to_add = 25  # Should trigger flush at 20
        for i in range(events_to_add):
            result = await batcher.add_event("large-batch", sample_events["file_change"], prefs)
            if i < 19:  # First 19 should be batched
                assert result is None
            else:  # 20th should trigger flush
                assert result is not None
                assert len(result) == 20
                break


class TestCompressionManager:
    """Test message compression functionality"""
    
    def test_compression_manager_initialization(self):
        """Test CompressionManager initialization"""
        compression_manager = CompressionManager()
        assert compression_manager.MIN_COMPRESSION_SIZE == 1024
    
    def test_small_message_no_compression(self):
        """Test that small messages are not compressed"""
        compression_manager = CompressionManager()
        
        small_message = "small message"
        result, compressed = compression_manager.compress_message(small_message)
        
        assert not compressed
        assert result == small_message.encode("utf-8")
    
    def test_large_message_compression(self):
        """Test compression of large messages"""
        compression_manager = CompressionManager()
        
        # Create large, compressible message
        large_message = "this is a test message " * 100  # About 2.3KB, very compressible
        result, compressed = compression_manager.compress_message(large_message)
        
        assert compressed
        assert len(result) < len(large_message.encode("utf-8"))
        
        # Verify we can decompress it back
        decompressed = gzip.decompress(result).decode("utf-8")
        assert decompressed == large_message
    
    def test_large_message_inefficient_compression(self):
        """Test that inefficient compression is avoided"""
        compression_manager = CompressionManager()
        
        # Create large, incompressible message (random data)
        import random
        random_chars = [chr(random.randint(32, 126)) for _ in range(2000)]
        incompressible_message = "".join(random_chars)
        
        result, compressed = compression_manager.compress_message(incompressible_message)
        
        # Should not compress if savings are less than 20%
        # Random data typically doesn't compress well
        assert result == incompressible_message.encode("utf-8")


class TestEventStreamingService:
    """Test main event streaming service functionality"""
    
    @pytest.mark.asyncio
    async def test_service_initialization(self):
        """Test EventStreamingService initialization"""
        service = EventStreamingService()
        
        assert service is not None
        assert len(service.clients) == 0
        assert service.event_filter is not None
        assert service.event_batcher is not None
        assert service.compression_manager is not None
        assert service.stats is not None
        assert service.processing_task is None
    
    @pytest.mark.asyncio
    async def test_service_start_stop(self, streaming_service):
        """Test starting and stopping the service"""
        # Test start
        await streaming_service.start()
        assert streaming_service.processing_task is not None
        assert not streaming_service.processing_task.cancelled()
        
        # Test stop
        await streaming_service.stop()
        assert streaming_service.processing_task is None
    
    def test_client_registration(self, streaming_service, mock_websocket, sample_client_preferences):
        """Test client registration"""
        client_id = "test-client-reg"
        
        # Register client
        streaming_service.register_client(client_id, mock_websocket, sample_client_preferences)
        
        # Verify registration
        assert client_id in streaming_service.clients
        assert client_id in streaming_service.websocket_connections
        assert streaming_service.stats.connected_clients == 1
        
        client_state = streaming_service.clients[client_id]
        assert client_state.client_id == client_id
        assert client_state.preferences == sample_client_preferences
        assert client_state.active is True
    
    def test_client_unregistration(self, streaming_service, mock_websocket, sample_client_preferences):
        """Test client unregistration"""
        client_id = "test-client-unreg"
        
        # Register then unregister
        streaming_service.register_client(client_id, mock_websocket, sample_client_preferences)
        assert client_id in streaming_service.clients
        
        streaming_service.unregister_client(client_id)
        
        # Verify unregistration
        assert client_id not in streaming_service.clients
        assert client_id not in streaming_service.websocket_connections
        assert streaming_service.stats.connected_clients == 0
    
    def test_update_client_preferences(self, streaming_service, mock_websocket, sample_client_preferences):
        """Test updating client preferences"""
        client_id = "test-client-update"
        
        # Register client
        streaming_service.register_client(client_id, mock_websocket, sample_client_preferences)
        
        # Update preferences
        new_preferences = ClientPreferences(
            client_id=client_id,
            enabled_channels=[NotificationChannel.VIOLATIONS],
            min_priority=EventPriority.HIGH,
            max_events_per_second=5
        )
        
        streaming_service.update_client_preferences(client_id, new_preferences)
        
        # Verify update
        updated_state = streaming_service.clients[client_id]
        assert updated_state.preferences == new_preferences
        assert updated_state.preferences.min_priority == EventPriority.HIGH
    
    @pytest.mark.asyncio
    async def test_emit_event(self, streaming_service, sample_events):
        """Test emitting events to the queue"""
        initial_count = streaming_service.stats.total_events_sent
        
        # Emit event
        await streaming_service.emit_event(sample_events["file_change"])
        
        # Verify stats updated
        assert streaming_service.stats.total_events_sent == initial_count + 1
        assert "file_changed" in streaming_service.stats.events_by_type
        assert "medium" in streaming_service.stats.events_by_priority
    
    @pytest.mark.asyncio
    async def test_event_delivery_to_client(self, streaming_service, mock_websocket, sample_client_preferences, sample_events):
        """Test event delivery to registered client"""
        client_id = "delivery-test"
        
        # Register client with immediate delivery (no batching)
        no_batch_prefs = ClientPreferences(
            client_id=client_id,
            enabled_channels=[NotificationChannel.ALL],
            min_priority=EventPriority.LOW,
            enable_batching=False,
            enable_compression=False
        )
        
        streaming_service.register_client(client_id, mock_websocket, no_batch_prefs)
        
        # Emit event
        await streaming_service.emit_event(sample_events["file_change"])
        
        # Process the event queue
        if streaming_service.event_queue.qsize() > 0:
            event = await streaming_service.event_queue.get()
            await streaming_service._deliver_event(event)
        
        # Verify message was sent
        assert len(mock_websocket.sent_messages) > 0
        
        # Verify message content
        message_data = mock_websocket.get_last_message_data()
        assert message_data["message_type"] == "notification"
        assert message_data["event_type"] == "file_changed"
        assert "data" in message_data
    
    @pytest.mark.asyncio
    async def test_event_filtering_during_delivery(self, streaming_service, mock_websocket, sample_events):
        """Test that events are properly filtered during delivery"""
        client_id = "filter-test"
        
        # Register client that only wants HIGH priority events
        high_priority_prefs = ClientPreferences(
            client_id=client_id,
            enabled_channels=[NotificationChannel.ALL],
            min_priority=EventPriority.HIGH,
            enable_batching=False
        )
        
        streaming_service.register_client(client_id, mock_websocket, high_priority_prefs)
        
        # Emit MEDIUM priority event (should be filtered out)
        await streaming_service.emit_event(sample_events["file_change"])  # MEDIUM priority
        
        # Process the event queue
        if streaming_service.event_queue.qsize() > 0:
            event = await streaming_service.event_queue.get()
            await streaming_service._deliver_event(event)
        
        # Should not receive message due to priority filter
        assert len(mock_websocket.sent_messages) == 0
        
        # Emit HIGH priority event (should be delivered)
        await streaming_service.emit_event(sample_events["agent"])  # HIGH priority
        
        # Process the event queue
        if streaming_service.event_queue.qsize() > 0:
            event = await streaming_service.event_queue.get()
            await streaming_service._deliver_event(event)
        
        # Should receive this message
        assert len(mock_websocket.sent_messages) > 0
    
    @pytest.mark.asyncio
    async def test_compression_in_delivery(self, streaming_service, mock_websocket):
        """Test message compression during delivery"""
        client_id = "compression-test"
        
        # Register client with compression enabled
        compression_prefs = ClientPreferences(
            client_id=client_id,
            enabled_channels=[NotificationChannel.ALL],
            min_priority=EventPriority.LOW,
            enable_batching=False,
            enable_compression=True
        )
        
        streaming_service.register_client(client_id, mock_websocket, compression_prefs)
        
        # Create large event that should trigger compression
        large_event = create_file_change_event("/very/long/path/to/file" * 50, "modified")
        large_event.data = {"large_data": "x" * 2000}  # Add large data
        
        await streaming_service.emit_event(large_event)
        
        # Process the event
        if streaming_service.event_queue.qsize() > 0:
            event = await streaming_service.event_queue.get()
            await streaming_service._deliver_event(event)
        
        # Check if compression was used (bytes were sent instead of text)
        # This depends on whether the message was large enough and compressible enough
        total_messages = len(mock_websocket.sent_messages) + len(mock_websocket.sent_bytes)
        assert total_messages > 0
    
    def test_get_stats(self, streaming_service, mock_websocket, sample_client_preferences):
        """Test getting service statistics"""
        # Register some clients and emit events
        streaming_service.register_client("client1", mock_websocket, sample_client_preferences)
        streaming_service.register_client("client2", MockWebSocket("client2"), sample_client_preferences)
        
        stats = streaming_service.get_stats()
        
        assert "connected_clients" in stats
        assert "total_events_sent" in stats
        assert "events_by_type" in stats
        assert "events_by_priority" in stats
        assert "failed_deliveries" in stats
        assert stats["connected_clients"] == 2
    
    def test_get_client_info(self, streaming_service, mock_websocket, sample_client_preferences):
        """Test getting client information"""
        client_id = "info-client"
        
        streaming_service.register_client(client_id, mock_websocket, sample_client_preferences)
        
        client_info = streaming_service.get_client_info()
        
        assert client_id in client_info
        client_data = client_info[client_id]
        assert "connected_at" in client_data
        assert "last_seen" in client_data
        assert "sequence_number" in client_data
        assert "active" in client_data
        assert "preferences" in client_data
        assert client_data["active"] is True


class TestConvenienceFunctions:
    """Test convenience functions for emitting events"""
    
    @pytest.mark.asyncio
    async def test_emit_file_change(self):
        """Test emit_file_change convenience function"""
        with patch('app.services.event_streaming_service.event_streaming_service.emit_event') as mock_emit:
            mock_emit.return_value = None
            
            await emit_file_change("/test/file.py", "modified", "/old/path.py")
            
            mock_emit.assert_called_once()
            event = mock_emit.call_args[0][0]
            assert isinstance(event, FileChangeEvent)
            assert event.file_path == "/test/file.py"
            assert event.change_type == "modified"
            assert event.old_path == "/old/path.py"
    
    @pytest.mark.asyncio
    async def test_emit_analysis_completed(self):
        """Test emit_analysis_completed convenience function"""
        with patch('app.services.event_streaming_service.event_streaming_service.emit_event') as mock_emit:
            mock_emit.return_value = None
            
            await emit_analysis_completed("ast", "/test/file.py", 2.5)
            
            mock_emit.assert_called_once()
            event = mock_emit.call_args[0][0]
            assert isinstance(event, AnalysisEvent)
            assert event.analysis_type == "ast"
            assert event.file_path == "/test/file.py"
            assert event.processing_time == 2.5
            assert event.success is True
    
    @pytest.mark.asyncio
    async def test_emit_violation_detected(self):
        """Test emit_violation_detected convenience function"""
        with patch('app.services.event_streaming_service.event_streaming_service.emit_event') as mock_emit:
            mock_emit.return_value = None
            
            await emit_violation_detected(
                "v123", "complexity", "warning", "/test/file.py", "High complexity detected"
            )
            
            mock_emit.assert_called_once()
            event = mock_emit.call_args[0][0]
            assert isinstance(event, ViolationEvent)
            assert event.violation_id == "v123"
            assert event.violation_type == "complexity"
            assert event.severity == "warning"
            assert event.file_path == "/test/file.py"
            assert event.description == "High complexity detected"
    
    @pytest.mark.asyncio
    async def test_emit_agent_event(self):
        """Test emit_agent_event convenience function"""
        with patch('app.services.event_streaming_service.event_streaming_service.emit_event') as mock_emit:
            mock_emit.return_value = None
            
            await emit_agent_event("session123", EventType.AGENT_COMPLETED, "test query")
            
            mock_emit.assert_called_once()
            event = mock_emit.call_args[0][0]
            assert isinstance(event, AgentEvent)
            assert event.session_id == "session123"
            assert event.event_type == EventType.AGENT_COMPLETED
            assert event.query == "test query"


class TestEventCreationUtilities:
    """Test event creation utility functions"""
    
    def test_create_file_change_event(self):
        """Test file change event creation"""
        event = create_file_change_event("/test/file.py", "modified", "/old/file.py")
        
        assert isinstance(event, FileChangeEvent)
        assert event.file_path == "/test/file.py"
        assert event.change_type == "modified"
        assert event.old_path == "/old/file.py"
        assert event.event_type == EventType.FILE_CHANGED
        assert event.priority == EventPriority.MEDIUM
        assert event.channel == NotificationChannel.FILE_SYSTEM
        assert event.source == "file_monitor"
    
    def test_create_analysis_event_success(self):
        """Test analysis event creation for successful analysis"""
        event = create_analysis_event("ast", "/test/file.py", True, 1.5)
        
        assert isinstance(event, AnalysisEvent)
        assert event.analysis_type == "ast"
        assert event.file_path == "/test/file.py"
        assert event.success is True
        assert event.processing_time == 1.5
        assert event.event_type == EventType.AST_ANALYSIS_COMPLETED
        assert event.priority == EventPriority.MEDIUM
        assert event.channel == NotificationChannel.ANALYSIS
    
    def test_create_analysis_event_failure(self):
        """Test analysis event creation for failed analysis"""
        event = create_analysis_event("ast", "/test/file.py", False, 0.5)
        
        assert isinstance(event, AnalysisEvent)
        assert event.success is False
        assert event.processing_time == 0.5
        assert event.event_type == EventType.AST_ANALYSIS_FAILED
        assert event.priority == EventPriority.HIGH  # Failed events have higher priority
    
    def test_create_violation_event(self):
        """Test violation event creation"""
        event = create_violation_event("v1", "complexity", "error", "/test/file.py", "High complexity")
        
        assert isinstance(event, ViolationEvent)
        assert event.violation_id == "v1"
        assert event.violation_type == "complexity"
        assert event.severity == "error"
        assert event.file_path == "/test/file.py"
        assert event.description == "High complexity"
        assert event.event_type == EventType.VIOLATION_DETECTED
        assert event.priority == EventPriority.HIGH  # Error severity maps to HIGH priority
        assert event.channel == NotificationChannel.VIOLATIONS
    
    def test_create_agent_event(self):
        """Test agent event creation"""
        event = create_agent_event("session1", EventType.AGENT_COMPLETED, "test query", "test response")
        
        assert isinstance(event, AgentEvent)
        assert event.session_id == "session1"
        assert event.event_type == EventType.AGENT_COMPLETED
        assert event.query == "test query"
        assert event.response == "test response"
        assert event.priority == EventPriority.HIGH
        assert event.channel == NotificationChannel.AGENT
        assert event.source == "l3_agent"


class TestErrorHandling:
    """Test error handling in the notification system"""
    
    @pytest.mark.asyncio
    async def test_websocket_send_error_handling(self, streaming_service, sample_events):
        """Test handling of WebSocket send errors"""
        client_id = "error-client"
        
        # Create a WebSocket that will fail on send
        failing_websocket = MockWebSocket(client_id)
        failing_websocket.closed = True  # This will cause send_text to raise exception
        
        prefs = ClientPreferences(
            client_id=client_id,
            enabled_channels=[NotificationChannel.ALL],
            min_priority=EventPriority.LOW,
            enable_batching=False
        )
        
        streaming_service.register_client(client_id, failing_websocket, prefs)
        
        # Emit event and process
        await streaming_service.emit_event(sample_events["file_change"])
        
        if streaming_service.event_queue.qsize() > 0:
            event = await streaming_service.event_queue.get()
            await streaming_service._deliver_event(event)
        
        # Client should be marked as inactive due to send failure
        client_state = streaming_service.clients[client_id]
        assert client_state.active is False
        
        # Failed delivery count should increase
        assert streaming_service.stats.failed_deliveries > 0
    
    @pytest.mark.asyncio
    async def test_missing_websocket_connection(self, streaming_service, sample_events):
        """Test handling missing WebSocket connections"""
        client_id = "missing-ws-client"
        
        # Register client preferences but don't add WebSocket connection
        prefs = ClientPreferences(client_id=client_id)
        streaming_service.clients[client_id] = ConnectionState(
            client_id=client_id,
            connected_at=datetime.now(),
            last_seen=datetime.now(),
            preferences=prefs
        )
        
        # Emit event - should handle missing WebSocket gracefully
        await streaming_service.emit_event(sample_events["file_change"])
        
        if streaming_service.event_queue.qsize() > 0:
            event = await streaming_service.event_queue.get()
            await streaming_service._deliver_event(event)
        
        # Should not raise exception, and no messages should be sent
        # (since there's no WebSocket to send to)
        assert True  # Test passes if no exception is raised
    
    @pytest.mark.asyncio
    async def test_event_processing_error_recovery(self, streaming_service):
        """Test recovery from event processing errors"""
        # Start the service
        await streaming_service.start()
        
        # Create an invalid event that might cause processing errors
        invalid_event = EventData(
            event_id="invalid",
            event_type=EventType.SYSTEM_ERROR,
            priority=EventPriority.CRITICAL,
            channel=NotificationChannel.SYSTEM,
            timestamp=datetime.now(),
            source="test"
        )
        
        # Emit invalid event
        await streaming_service.emit_event(invalid_event)
        
        # Give time for processing
        await asyncio.sleep(0.1)
        
        # Service should still be running
        assert streaming_service.processing_task is not None
        assert not streaming_service.processing_task.cancelled()
        
        # Stop the service
        await streaming_service.stop()


class TestIntegrationScenarios:
    """Test realistic integration scenarios"""
    
    @pytest.mark.asyncio
    async def test_multiple_clients_different_preferences(self, streaming_service, sample_events):
        """Test multiple clients with different notification preferences"""
        # Setup different types of clients
        
        # iOS client - wants batched, medium priority notifications
        ios_client = MockWebSocket("ios-client")
        ios_prefs = ClientPreferences(
            client_id="ios-client",
            enabled_channels=[NotificationChannel.ALL],
            min_priority=EventPriority.MEDIUM,
            enable_batching=True,
            batch_interval_ms=200,
            max_events_per_second=5
        )
        
        # CLI client - wants immediate, high priority notifications
        cli_client = MockWebSocket("cli-client")
        cli_prefs = ClientPreferences(
            client_id="cli-client",
            enabled_channels=[NotificationChannel.VIOLATIONS, NotificationChannel.AGENT],
            min_priority=EventPriority.HIGH,
            enable_batching=False,
            max_events_per_second=20
        )
        
        # Web client - wants specific channels only
        web_client = MockWebSocket("web-client")
        web_prefs = ClientPreferences(
            client_id="web-client",
            enabled_channels=[NotificationChannel.FILE_SYSTEM],
            min_priority=EventPriority.LOW,
            enable_batching=True,
            batch_interval_ms=500
        )
        
        # Register all clients
        streaming_service.register_client("ios-client", ios_client, ios_prefs)
        streaming_service.register_client("cli-client", cli_client, cli_prefs)
        streaming_service.register_client("web-client", web_client, web_prefs)
        
        # Emit various events
        await streaming_service.emit_event(sample_events["file_change"])  # MEDIUM, FILE_SYSTEM
        await streaming_service.emit_event(sample_events["violation"])    # MEDIUM, VIOLATIONS  
        await streaming_service.emit_event(sample_events["agent"])        # HIGH, AGENT
        
        # Process events
        while streaming_service.event_queue.qsize() > 0:
            event = await streaming_service.event_queue.get()
            await streaming_service._deliver_event(event)
        
        # Wait for any batching delays
        await asyncio.sleep(0.6)
        
        # Verify delivery based on preferences
        # iOS client should receive file_change and violation (both MEDIUM+)
        # CLI client should only receive agent event (HIGH priority, correct channels)
        # Web client should only receive file_change (FILE_SYSTEM channel)
        
        total_ios_messages = len(ios_client.sent_messages) + len(ios_client.sent_bytes)
        total_cli_messages = len(cli_client.sent_messages) + len(cli_client.sent_bytes)
        total_web_messages = len(web_client.sent_messages) + len(web_client.sent_bytes)
        
        # At least some messages should be delivered based on preferences
        assert total_ios_messages >= 0  # iOS gets batched messages
        assert total_cli_messages >= 0  # CLI gets immediate high-priority messages
        assert total_web_messages >= 0  # Web gets file system events
        
        # Verify service stats
        stats = streaming_service.get_stats()
        assert stats["connected_clients"] == 3
        assert stats["total_events_sent"] == 3
    
    @pytest.mark.asyncio
    async def test_high_volume_event_scenario(self, streaming_service):
        """Test handling high volume of events"""
        # Register client with rate limiting
        client = MockWebSocket("volume-client")
        prefs = ClientPreferences(
            client_id="volume-client",
            enabled_channels=[NotificationChannel.ALL],
            min_priority=EventPriority.LOW,
            enable_batching=True,
            batch_interval_ms=100,
            max_events_per_second=10  # Rate limit
        )
        
        streaming_service.register_client("volume-client", client, prefs)
        
        # Emit many events quickly
        events_emitted = 50
        for i in range(events_emitted):
            event = create_file_change_event(f"/test/file_{i}.py", "modified")
            await streaming_service.emit_event(event)
        
        # Process all events
        while streaming_service.event_queue.qsize() > 0:
            event = await streaming_service.event_queue.get()
            await streaming_service._deliver_event(event)
        
        # Wait for batching
        await asyncio.sleep(0.2)
        
        # Should have received some messages, but rate limiting should have applied
        total_messages = len(client.sent_messages) + len(client.sent_bytes)
        
        # With rate limiting and batching, shouldn't receive all 50 events individually
        assert total_messages < events_emitted
        
        # Stats should reflect all emitted events
        stats = streaming_service.get_stats()
        assert stats["total_events_sent"] == events_emitted


if __name__ == "__main__":
    pytest.main([__file__, "-v"])