"""
Event Streaming Service for Real-time Notifications

Handles real-time event streaming to WebSocket clients with smart filtering,
batching, compression, and client preference management.
"""

import asyncio
import gzip
import json
import logging
import time
from collections import defaultdict, deque
from dataclasses import asdict
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from ..models.event_models import (
    ClientPreferences,
    ConnectionState,
    EventData,
    EventPriority,
    EventStats,
    EventType,
    NotificationChannel,
    StreamingMessage,
)

logger = logging.getLogger(__name__)


class EventFilter:
    """Filters events based on client preferences and rules"""

    def __init__(self):
        self.rate_limiters: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))

    def should_deliver(self, event: EventData, preferences: ClientPreferences) -> bool:
        """Determine if an event should be delivered to a client"""

        # Check channel subscription
        if (
            NotificationChannel.ALL not in preferences.enabled_channels
            and event.channel not in preferences.enabled_channels
        ):
            return False

        # Check priority threshold
        priority_levels = {
            EventPriority.DEBUG: 0,
            EventPriority.LOW: 1,
            EventPriority.MEDIUM: 2,
            EventPriority.HIGH: 3,
            EventPriority.CRITICAL: 4,
        }

        if priority_levels[event.priority] < priority_levels[preferences.min_priority]:
            return False

        # Check rate limiting
        if not self._check_rate_limit(
            preferences.client_id, preferences.max_events_per_second
        ):
            return False

        # Apply custom filters
        if not self._apply_custom_filters(event, preferences.custom_filters):
            return False

        return True

    def _check_rate_limit(self, client_id: str, max_events_per_second: int) -> bool:
        """Check if client is within rate limits"""
        now = time.time()
        rate_limiter = self.rate_limiters[client_id]

        # Remove old entries (older than 1 second)
        while rate_limiter and rate_limiter[0] < now - 1.0:
            rate_limiter.popleft()

        # Check if we're at the limit
        if len(rate_limiter) >= max_events_per_second:
            return False

        # Add current timestamp
        rate_limiter.append(now)
        return True

    def _apply_custom_filters(
        self, event: EventData, custom_filters: Dict[str, Any]
    ) -> bool:
        """Apply custom client-specific filters"""
        for filter_name, filter_config in custom_filters.items():
            if filter_name == "exclude_file_patterns":
                patterns = filter_config.get("patterns", [])
                if hasattr(event, "file_path") and event.file_path:
                    for pattern in patterns:
                        if pattern in event.file_path:
                            return False

            elif filter_name == "min_confidence":
                min_confidence = filter_config.get("threshold", 0.0)
                if hasattr(event, "confidence_score"):
                    if event.confidence_score < min_confidence:
                        return False

        return True


class EventBatcher:
    """Batches events for efficient delivery"""

    def __init__(self):
        self.pending_batches: Dict[str, List[EventData]] = defaultdict(list)
        self.batch_timers: Dict[str, asyncio.Task] = {}

    async def add_event(
        self, client_id: str, event: EventData, preferences: ClientPreferences
    ):
        """Add an event to a client's batch"""
        if not preferences.enable_batching:
            # Send immediately
            return [event]

        self.pending_batches[client_id].append(event)

        # Start timer if not already running
        if client_id not in self.batch_timers:
            self.batch_timers[client_id] = asyncio.create_task(
                self._flush_after_delay(
                    client_id, preferences.batch_interval_ms / 1000.0
                )
            )

        # Flush if batch is getting large
        if len(self.pending_batches[client_id]) >= 20:
            return await self._flush_batch(client_id)

        return None  # Will be flushed later

    async def _flush_after_delay(self, client_id: str, delay: float):
        """Flush batch after delay"""
        await asyncio.sleep(delay)
        await self._flush_batch(client_id)

    async def _flush_batch(self, client_id: str) -> Optional[List[EventData]]:
        """Flush pending events for a client"""
        if client_id not in self.pending_batches:
            return None

        events = self.pending_batches[client_id]
        if not events:
            return None

        # Clear batch and timer
        self.pending_batches[client_id] = []
        if client_id in self.batch_timers:
            self.batch_timers[client_id].cancel()
            del self.batch_timers[client_id]

        return events


class CompressionManager:
    """Handles message compression for large payloads"""

    MIN_COMPRESSION_SIZE = 1024  # Only compress messages larger than 1KB

    def compress_message(self, message: str) -> tuple[bytes, bool]:
        """Compress a message if beneficial"""
        message_bytes = message.encode("utf-8")

        if len(message_bytes) < self.MIN_COMPRESSION_SIZE:
            return message_bytes, False

        compressed = gzip.compress(message_bytes)

        # Only use compression if it saves at least 20%
        if len(compressed) < len(message_bytes) * 0.8:
            return compressed, True

        return message_bytes, False


class EventStreamingService:
    """Main event streaming service"""

    def __init__(self):
        self.clients: Dict[str, ConnectionState] = {}
        self.event_filter = EventFilter()
        self.event_batcher = EventBatcher()
        self.compression_manager = CompressionManager()
        self.stats = EventStats()
        self.event_listeners: List[Callable] = []
        self.websocket_connections: Dict[str, Any] = {}  # WebSocket connections

        # Event queue for processing
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.processing_task: Optional[asyncio.Task] = None

        logger.info("Event streaming service initialized")

    async def start(self):
        """Start the event processing task"""
        if self.processing_task is None:
            self.processing_task = asyncio.create_task(self._process_events())
            logger.info("Event streaming service started")

    async def stop(self):
        """Stop the event processing task"""
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
            self.processing_task = None
            logger.info("Event streaming service stopped")

    def register_client(
        self, client_id: str, websocket, preferences: Optional[ClientPreferences] = None
    ):
        """Register a new WebSocket client"""
        if preferences is None:
            preferences = ClientPreferences(client_id=client_id)

        self.clients[client_id] = ConnectionState(
            client_id=client_id,
            connected_at=datetime.now(),
            last_seen=datetime.now(),
            preferences=preferences,
        )

        self.websocket_connections[client_id] = websocket
        self.stats.connected_clients = len(self.clients)

        logger.info(f"Client {client_id} registered for event streaming")

    def unregister_client(self, client_id: str):
        """Unregister a WebSocket client"""
        if client_id in self.clients:
            del self.clients[client_id]

        if client_id in self.websocket_connections:
            del self.websocket_connections[client_id]

        self.stats.connected_clients = len(self.clients)
        logger.info(f"Client {client_id} unregistered from event streaming")

    def update_client_preferences(self, client_id: str, preferences: ClientPreferences):
        """Update client notification preferences"""
        if client_id in self.clients:
            self.clients[client_id].preferences = preferences
            logger.info(f"Updated preferences for client {client_id}")

    async def emit_event(self, event: EventData):
        """Emit an event to the streaming system"""
        await self.event_queue.put(event)
        self.stats.total_events_sent += 1

        # Update stats
        event_type_str = event.event_type.value
        priority_str = event.priority.value

        self.stats.events_by_type[event_type_str] = (
            self.stats.events_by_type.get(event_type_str, 0) + 1
        )
        self.stats.events_by_priority[priority_str] = (
            self.stats.events_by_priority.get(priority_str, 0) + 1
        )

    async def _process_events(self):
        """Process events from the queue"""
        while True:
            try:
                event = await self.event_queue.get()
                await self._deliver_event(event)
                self.event_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing event: {e}")

    async def _deliver_event(self, event: EventData):
        """Deliver an event to all eligible clients"""
        delivery_tasks = []
        disconnected_clients = []

        for client_id, client_state in self.clients.items():
            # Check if client is currently connected
            if not client_state.active or client_id not in self.websocket_connections:
                # Track missed event for disconnected clients
                disconnected_clients.append(client_id)
                continue

            # Check if event should be delivered to this client
            if not self.event_filter.should_deliver(event, client_state.preferences):
                continue

            # Add to batch or deliver immediately
            delivery_tasks.append(
                self._deliver_to_client(client_id, event, client_state)
            )

        # Track missed events for disconnected clients that should receive this event
        if disconnected_clients:
            self._track_missed_events(event, disconnected_clients)

        if delivery_tasks:
            await asyncio.gather(*delivery_tasks, return_exceptions=True)

    def _track_missed_events(self, event: EventData, disconnected_clients: List[str]):
        """Track missed events for disconnected clients"""
        try:
            # Import here to avoid circular imports
            from .reconnection_service import track_missed_event_for_client

            for client_id in disconnected_clients:
                # Only track if the client has preferences that would want this event
                if client_id in self.clients:
                    client_state = self.clients[client_id]
                    if self.event_filter.should_deliver(
                        event, client_state.preferences
                    ):
                        track_missed_event_for_client(client_id, event)
                        logger.debug(
                            f"Tracked missed event {event.event_type.value} for disconnected client {client_id}"
                        )
        except Exception as e:
            logger.error(f"Error tracking missed events: {e}")

    async def _deliver_to_client(
        self, client_id: str, event: EventData, client_state: ConnectionState
    ):
        """Deliver an event to a specific client"""
        try:
            # Check if we should batch this event
            events_to_send = await self.event_batcher.add_event(
                client_id, event, client_state.preferences
            )

            if events_to_send is None:
                return  # Event was batched, will be sent later

            # Create streaming message(s)
            if len(events_to_send) == 1:
                message = self._create_streaming_message(
                    events_to_send[0], client_state
                )
            else:
                message = self._create_batch_message(events_to_send, client_state)

            # Send to WebSocket
            await self._send_to_websocket(client_id, message, client_state)

        except Exception as e:
            logger.error(f"Error delivering event to client {client_id}: {e}")
            self.stats.failed_deliveries += 1

    def _create_streaming_message(
        self, event: EventData, client_state: ConnectionState
    ) -> StreamingMessage:
        """Create a streaming message from an event"""
        client_state.sequence_number += 1

        return StreamingMessage(
            message_type="notification",
            event_type=event.event_type,
            priority=event.priority,
            channel=event.channel,
            timestamp=event.timestamp,
            data=asdict(event),
            sequence_number=client_state.sequence_number,
        )

    def _create_batch_message(
        self, events: List[EventData], client_state: ConnectionState
    ) -> StreamingMessage:
        """Create a batch streaming message"""
        client_state.sequence_number += 1

        # Use the highest priority event for the batch
        max_priority = max(
            events, key=lambda e: self._priority_value(e.priority)
        ).priority

        return StreamingMessage(
            message_type="batch_notification",
            event_type=EventType.SYSTEM_READY,  # Generic for batches
            priority=max_priority,
            channel=NotificationChannel.ALL,
            timestamp=datetime.now(),
            data={
                "events": [asdict(event) for event in events],
                "batch_size": len(events),
            },
            batch_info={
                "event_count": len(events),
                "compressed": False,  # Will be updated if compressed
            },
            sequence_number=client_state.sequence_number,
        )

    def _priority_value(self, priority: EventPriority) -> int:
        """Convert priority to numeric value for comparison"""
        return {
            EventPriority.DEBUG: 0,
            EventPriority.LOW: 1,
            EventPriority.MEDIUM: 2,
            EventPriority.HIGH: 3,
            EventPriority.CRITICAL: 4,
        }[priority]

    async def _send_to_websocket(
        self, client_id: str, message: StreamingMessage, client_state: ConnectionState
    ):
        """Send message to WebSocket connection"""
        if client_id not in self.websocket_connections:
            return

        websocket = self.websocket_connections[client_id]

        try:
            # Serialize message
            message_data = message.dict()
            message_json = json.dumps(message_data, default=str)

            # Compress if enabled and beneficial
            if client_state.preferences.enable_compression:
                message_bytes, compressed = self.compression_manager.compress_message(
                    message_json
                )

                if compressed:
                    # Send compressed data with compression flag
                    message_data["_compressed"] = True
                    await websocket.send_bytes(message_bytes)
                else:
                    await websocket.send_text(message_json)
            else:
                await websocket.send_text(message_json)

            # Update client state
            client_state.last_seen = datetime.now()

        except Exception as e:
            logger.error(f"Failed to send message to client {client_id}: {e}")
            # Mark client as inactive
            client_state.active = False
            self.stats.failed_deliveries += 1

    def get_stats(self) -> Dict[str, Any]:
        """Get streaming service statistics"""
        return {
            "connected_clients": self.stats.connected_clients,
            "total_events_sent": self.stats.total_events_sent,
            "events_by_type": self.stats.events_by_type,
            "events_by_priority": self.stats.events_by_priority,
            "failed_deliveries": self.stats.failed_deliveries,
            "avg_latency_ms": self.stats.avg_latency_ms,
            "events_per_second": self.stats.events_per_second,
        }

    def get_client_info(self) -> Dict[str, Any]:
        """Get information about connected clients"""
        return {
            client_id: {
                "connected_at": state.connected_at.isoformat(),
                "last_seen": state.last_seen.isoformat(),
                "sequence_number": state.sequence_number,
                "active": state.active,
                "preferences": state.preferences.dict(),
            }
            for client_id, state in self.clients.items()
        }


# Global service instance
event_streaming_service = EventStreamingService()


# Convenience functions for emitting common events


async def emit_file_change(
    file_path: str, change_type: str, old_path: Optional[str] = None
):
    """Emit a file change event"""
    from ..models.event_models import create_file_change_event

    event = create_file_change_event(file_path, change_type, old_path)
    await event_streaming_service.emit_event(event)


async def emit_analysis_completed(
    analysis_type: str, file_path: str, processing_time: float
):
    """Emit an analysis completion event"""
    from ..models.event_models import create_analysis_event

    event = create_analysis_event(analysis_type, file_path, True, processing_time)
    await event_streaming_service.emit_event(event)


async def emit_violation_detected(
    violation_id: str,
    violation_type: str,
    severity: str,
    file_path: str,
    description: str,
):
    """Emit a violation detection event"""
    from ..models.event_models import create_violation_event

    event = create_violation_event(
        violation_id, violation_type, severity, file_path, description
    )
    await event_streaming_service.emit_event(event)


async def emit_agent_event(
    session_id: str, event_type: EventType, query: Optional[str] = None
):
    """Emit an agent processing event"""
    from ..models.event_models import create_agent_event

    event = create_agent_event(session_id, event_type, query)
    await event_streaming_service.emit_event(event)
