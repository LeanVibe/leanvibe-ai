"""
Reconnection Service for WebSocket State Synchronization

Handles WebSocket reconnection scenarios with state preservation,
missed notification replay, and seamless client experience.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from ..models.event_models import ConnectionState, EventData

logger = logging.getLogger(__name__)


class ReconnectionStrategy(str, Enum):
    """Strategies for handling reconnection scenarios"""

    IMMEDIATE = "immediate"  # Reconnect immediately
    EXPONENTIAL_BACKOFF = "exponential_backoff"  # Exponential backoff retry
    LINEAR_BACKOFF = "linear_backoff"  # Linear backoff retry
    MANUAL = "manual"  # Manual reconnection only


@dataclass
class ReconnectionConfig:
    """Configuration for reconnection behavior"""

    strategy: ReconnectionStrategy = ReconnectionStrategy.EXPONENTIAL_BACKOFF
    max_retry_attempts: int = 10
    initial_delay_ms: int = 1000
    max_delay_ms: int = 30000
    backoff_multiplier: float = 2.0
    missed_event_retention_hours: int = 24
    state_sync_timeout_ms: int = 5000
    enable_heartbeat: bool = True
    heartbeat_interval_ms: int = 30000


@dataclass
class MissedEvent:
    """Represents an event that was missed during disconnection"""

    event: EventData
    missed_at: datetime
    retry_count: int = 0
    delivered: bool = False


@dataclass
class ClientSession:
    """Stores client session state for reconnection"""

    client_id: str
    last_seen: datetime
    sequence_number: int
    missed_events: List[MissedEvent] = field(default_factory=list)
    connection_attempts: int = 0
    last_heartbeat: Optional[datetime] = None
    session_state: Dict[str, Any] = field(default_factory=dict)
    preferences_snapshot: Optional[Dict[str, Any]] = None


class ReconnectionService:
    """Manages WebSocket reconnection and state synchronization"""

    def __init__(self, config: Optional[ReconnectionConfig] = None):
        self.config = config or ReconnectionConfig()
        self.client_sessions: Dict[str, ClientSession] = {}
        self.active_reconnections: Set[str] = set()
        self.heartbeat_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None

        logger.info("Reconnection service initialized")

    async def start(self):
        """Start the reconnection service background tasks"""
        if self.config.enable_heartbeat:
            self.heartbeat_task = asyncio.create_task(self._heartbeat_monitor())

        self.cleanup_task = asyncio.create_task(self._cleanup_expired_sessions())
        logger.info("Reconnection service started")

    async def stop(self):
        """Stop the reconnection service background tasks"""
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass

        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass

        logger.info("Reconnection service stopped")

    def register_client_session(
        self, client_id: str, connection_state: ConnectionState
    ):
        """Register a new client session"""
        session = ClientSession(
            client_id=client_id,
            last_seen=datetime.now(),
            sequence_number=connection_state.sequence_number,
            preferences_snapshot=connection_state.preferences.dict(),
        )

        self.client_sessions[client_id] = session
        logger.info(f"Registered session for client {client_id}")

    def update_client_heartbeat(self, client_id: str):
        """Update client heartbeat timestamp"""
        if client_id in self.client_sessions:
            session = self.client_sessions[client_id]
            session.last_heartbeat = datetime.now()
            session.last_seen = datetime.now()

    def client_disconnected(self, client_id: str):
        """Handle client disconnection"""
        if client_id in self.client_sessions:
            session = self.client_sessions[client_id]
            session.last_seen = datetime.now()
            logger.info(f"Client {client_id} disconnected, session preserved")

    async def client_reconnected(
        self, client_id: str, connection_state: ConnectionState
    ) -> Dict[str, Any]:
        """Handle client reconnection and return synchronization data"""
        if client_id not in self.client_sessions:
            logger.warning(f"No session found for reconnecting client {client_id}")
            return {"status": "new_session", "missed_events": []}

        session = self.client_sessions[client_id]
        reconnection_info = {
            "status": "reconnected",
            "session_restored": True,
            "missed_events_count": len(session.missed_events),
            "last_sequence_number": session.sequence_number,
            "disconnection_duration_ms": int(
                (datetime.now() - session.last_seen).total_seconds() * 1000
            ),
        }

        # Prepare missed events for replay
        missed_events_data = []
        for missed_event in session.missed_events:
            if not missed_event.delivered:
                missed_events_data.append(
                    {
                        "event": missed_event.event.__dict__,
                        "missed_at": missed_event.missed_at.isoformat(),
                        "sequence_number": session.sequence_number + 1,
                    }
                )
                session.sequence_number += 1
                missed_event.delivered = True

        reconnection_info["missed_events"] = missed_events_data

        # Update session state
        session.last_seen = datetime.now()
        session.last_heartbeat = datetime.now()
        session.connection_attempts += 1

        # Remove client from active reconnections
        self.active_reconnections.discard(client_id)

        logger.info(
            f"Client {client_id} reconnected, replaying {len(missed_events_data)} missed events"
        )
        return reconnection_info

    def add_missed_event(self, client_id: str, event: EventData):
        """Add a missed event for a disconnected client"""
        if client_id not in self.client_sessions:
            return

        session = self.client_sessions[client_id]
        missed_event = MissedEvent(event=event, missed_at=datetime.now())

        session.missed_events.append(missed_event)

        # Limit missed events to prevent memory bloat
        max_missed_events = 1000  # Configurable limit
        if len(session.missed_events) > max_missed_events:
            # Remove oldest events, keep newest
            session.missed_events = session.missed_events[-max_missed_events:]
            logger.warning(
                f"Trimmed missed events for client {client_id} to {max_missed_events}"
            )

    def get_reconnection_delay(self, client_id: str) -> int:
        """Calculate reconnection delay based on strategy and attempt count"""
        if client_id not in self.client_sessions:
            return self.config.initial_delay_ms

        session = self.client_sessions[client_id]
        attempt = session.connection_attempts

        if self.config.strategy == ReconnectionStrategy.IMMEDIATE:
            return 0
        elif self.config.strategy == ReconnectionStrategy.LINEAR_BACKOFF:
            delay = self.config.initial_delay_ms * (attempt + 1)
        elif self.config.strategy == ReconnectionStrategy.EXPONENTIAL_BACKOFF:
            delay = min(
                self.config.initial_delay_ms
                * (self.config.backoff_multiplier**attempt),
                self.config.max_delay_ms,
            )
        else:  # MANUAL
            return -1  # No automatic reconnection

        return int(min(delay, self.config.max_delay_ms))

    def should_attempt_reconnection(self, client_id: str) -> bool:
        """Determine if reconnection should be attempted"""
        if client_id not in self.client_sessions:
            return False

        session = self.client_sessions[client_id]

        # Check if we've exceeded max attempts
        if session.connection_attempts >= self.config.max_retry_attempts:
            return False

        # Check if manual reconnection only
        if self.config.strategy == ReconnectionStrategy.MANUAL:
            return False

        return True

    def get_client_session_info(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Get session information for a client"""
        if client_id not in self.client_sessions:
            return None

        session = self.client_sessions[client_id]
        return {
            "client_id": session.client_id,
            "last_seen": session.last_seen.isoformat(),
            "sequence_number": session.sequence_number,
            "missed_events_count": len(session.missed_events),
            "connection_attempts": session.connection_attempts,
            "last_heartbeat": (
                session.last_heartbeat.isoformat() if session.last_heartbeat else None
            ),
            "reconnection_eligible": self.should_attempt_reconnection(client_id),
            "next_reconnection_delay_ms": self.get_reconnection_delay(client_id),
        }

    def get_all_sessions_info(self) -> Dict[str, Any]:
        """Get information about all client sessions"""
        return {
            "total_sessions": len(self.client_sessions),
            "active_reconnections": len(self.active_reconnections),
            "config": {
                "strategy": self.config.strategy.value,
                "max_retry_attempts": self.config.max_retry_attempts,
                "heartbeat_enabled": self.config.enable_heartbeat,
                "heartbeat_interval_ms": self.config.heartbeat_interval_ms,
            },
            "sessions": {
                client_id: self.get_client_session_info(client_id)
                for client_id in self.client_sessions.keys()
            },
        }

    async def _heartbeat_monitor(self):
        """Monitor client heartbeats and detect disconnections"""
        while True:
            try:
                await asyncio.sleep(self.config.heartbeat_interval_ms / 1000.0)

                current_time = datetime.now()
                heartbeat_timeout = timedelta(
                    milliseconds=self.config.heartbeat_interval_ms * 2
                )

                disconnected_clients = []
                for client_id, session in self.client_sessions.items():
                    if session.last_heartbeat:
                        if current_time - session.last_heartbeat > heartbeat_timeout:
                            disconnected_clients.append(client_id)

                for client_id in disconnected_clients:
                    logger.warning(f"Client {client_id} heartbeat timeout detected")
                    # Could trigger reconnection attempt here

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat monitor: {e}")

    async def _cleanup_expired_sessions(self):
        """Clean up expired client sessions"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run cleanup every hour

                current_time = datetime.now()
                retention_period = timedelta(
                    hours=self.config.missed_event_retention_hours
                )

                expired_clients = []
                for client_id, session in self.client_sessions.items():
                    if current_time - session.last_seen > retention_period:
                        expired_clients.append(client_id)

                for client_id in expired_clients:
                    del self.client_sessions[client_id]
                    logger.info(f"Cleaned up expired session for client {client_id}")

                # Clean up old missed events
                for session in self.client_sessions.values():
                    original_count = len(session.missed_events)
                    session.missed_events = [
                        event
                        for event in session.missed_events
                        if current_time - event.missed_at < retention_period
                    ]

                    if len(session.missed_events) < original_count:
                        logger.info(
                            f"Cleaned up {original_count - len(session.missed_events)} old missed events for {session.client_id}"
                        )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in session cleanup: {e}")


# Global service instance
reconnection_service = ReconnectionService()


# Utility functions for integration


async def handle_client_reconnection(
    client_id: str, connection_state: ConnectionState
) -> Dict[str, Any]:
    """Handle client reconnection and return sync data"""
    return await reconnection_service.client_reconnected(client_id, connection_state)


def track_missed_event_for_client(client_id: str, event: EventData):
    """Track missed event for a disconnected client"""
    reconnection_service.add_missed_event(client_id, event)


def register_client_session(client_id: str, connection_state: ConnectionState):
    """Register a new client session for reconnection tracking"""
    reconnection_service.register_client_session(client_id, connection_state)


def client_heartbeat(client_id: str):
    """Update client heartbeat"""
    reconnection_service.update_client_heartbeat(client_id)


def client_disconnected(client_id: str):
    """Mark client as disconnected"""
    reconnection_service.client_disconnected(client_id)
