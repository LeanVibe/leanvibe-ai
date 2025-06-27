"""
Event Models for Real-time Notification System

Defines event types, notification models, and streaming message formats
for the LeenVibe real-time communication system.
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from pydantic import BaseModel


class EventType(str, Enum):
    """Types of events that can be streamed to clients"""
    # File system events
    FILE_CHANGED = "file_changed"
    FILE_CREATED = "file_created"
    FILE_DELETED = "file_deleted"
    FILE_RENAMED = "file_renamed"
    
    # AST analysis events
    AST_ANALYSIS_STARTED = "ast_analysis_started"
    AST_ANALYSIS_COMPLETED = "ast_analysis_completed"
    AST_ANALYSIS_FAILED = "ast_analysis_failed"
    SYMBOL_ADDED = "symbol_added"
    SYMBOL_UPDATED = "symbol_updated"
    SYMBOL_REMOVED = "symbol_removed"
    
    # Graph database events
    GRAPH_UPDATED = "graph_updated"
    RELATIONSHIP_ADDED = "relationship_added"
    RELATIONSHIP_REMOVED = "relationship_removed"
    CIRCULAR_DEPENDENCY_DETECTED = "circular_dependency_detected"
    
    # Architectural violation events
    VIOLATION_DETECTED = "violation_detected"
    VIOLATION_RESOLVED = "violation_resolved"
    QUALITY_SCORE_CHANGED = "quality_score_changed"
    
    # Cache events
    CACHE_INVALIDATED = "cache_invalidated"
    CACHE_WARMED = "cache_warmed"
    INDEX_UPDATED = "index_updated"
    
    # Agent events
    AGENT_STARTED = "agent_started"
    AGENT_PROCESSING = "agent_processing"
    AGENT_COMPLETED = "agent_completed"
    AGENT_ERROR = "agent_error"
    
    # System events
    SYSTEM_READY = "system_ready"
    SYSTEM_ERROR = "system_error"
    CONNECTION_STATUS = "connection_status"


class EventPriority(str, Enum):
    """Priority levels for events"""
    CRITICAL = "critical"    # System errors, critical violations
    HIGH = "high"           # Important changes, agent completions
    MEDIUM = "medium"       # File changes, cache updates
    LOW = "low"             # Status updates, minor cache events
    DEBUG = "debug"         # Debug information, verbose logging


class NotificationChannel(str, Enum):
    """Channels for different types of notifications"""
    ALL = "all"                      # All events
    FILE_SYSTEM = "file_system"      # File change events
    ANALYSIS = "analysis"            # AST and graph analysis
    VIOLATIONS = "violations"        # Code quality and violations
    AGENT = "agent"                  # Agent processing events
    SYSTEM = "system"                # System status events


@dataclass
class EventData:
    """Base event data structure"""
    event_id: str
    event_type: EventType
    priority: EventPriority
    channel: NotificationChannel
    timestamp: datetime
    source: str  # Component that generated the event
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FileChangeEvent(EventData):
    """File system change event"""
    file_path: str
    change_type: str  # created, modified, deleted, renamed
    old_path: Optional[str] = None  # For rename operations
    file_size: Optional[int] = None
    modified_time: Optional[datetime] = None


@dataclass
class AnalysisEvent(EventData):
    """AST or graph analysis event"""
    analysis_type: str  # ast, graph, complexity, violations
    file_path: Optional[str] = None
    symbols_count: Optional[int] = None
    processing_time: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None


@dataclass
class ViolationEvent(EventData):
    """Code quality violation event"""
    violation_id: str
    violation_type: str
    severity: str
    file_path: str
    symbol_name: Optional[str] = None
    line_number: Optional[int] = None
    description: str
    suggestion: Optional[str] = None
    confidence_score: float = 0.0


@dataclass
class AgentEvent(EventData):
    """L3 Agent processing event"""
    session_id: str
    query: Optional[str] = None
    response: Optional[str] = None
    processing_time: Optional[float] = None
    confidence_score: Optional[float] = None
    tools_used: List[str] = field(default_factory=list)


class ClientPreferences(BaseModel):
    """Client-specific notification preferences"""
    client_id: str
    enabled_channels: List[NotificationChannel] = [NotificationChannel.ALL]
    min_priority: EventPriority = EventPriority.MEDIUM
    max_events_per_second: int = 10
    enable_batching: bool = True
    batch_interval_ms: int = 500
    enable_compression: bool = False
    custom_filters: Dict[str, Any] = {}
    
    class Config:
        use_enum_values = True


class NotificationBatch(BaseModel):
    """Batch of notifications for efficient delivery"""
    batch_id: str
    client_id: str
    events: List[EventData]
    created_at: datetime
    compressed: bool = False
    total_size: int = 0
    
    class Config:
        arbitrary_types_allowed = True


class StreamingMessage(BaseModel):
    """WebSocket streaming message format"""
    message_type: str = "notification"
    event_type: EventType
    priority: EventPriority
    channel: NotificationChannel
    timestamp: datetime
    data: Dict[str, Any]
    batch_info: Optional[Dict[str, Any]] = None
    sequence_number: Optional[int] = None
    
    class Config:
        use_enum_values = True
        arbitrary_types_allowed = True


class ConnectionState(BaseModel):
    """Client connection state"""
    client_id: str
    connected_at: datetime
    last_seen: datetime
    preferences: ClientPreferences
    missed_events: List[str] = []  # Event IDs missed during disconnection
    sequence_number: int = 0
    active: bool = True
    
    class Config:
        arbitrary_types_allowed = True


class EventStats(BaseModel):
    """Event streaming statistics"""
    total_events_sent: int = 0
    events_by_type: Dict[str, int] = {}
    events_by_priority: Dict[str, int] = {}
    avg_latency_ms: float = 0.0
    failed_deliveries: int = 0
    connected_clients: int = 0
    events_per_second: float = 0.0
    last_reset: datetime = datetime.now()


# Utility functions for event creation

def create_file_change_event(
    file_path: str,
    change_type: str,
    old_path: Optional[str] = None
) -> FileChangeEvent:
    """Create a file change event"""
    return FileChangeEvent(
        event_id=f"file_{int(time.time() * 1000)}_{hash(file_path) % 10000}",
        event_type=EventType.FILE_CHANGED,
        priority=EventPriority.MEDIUM,
        channel=NotificationChannel.FILE_SYSTEM,
        timestamp=datetime.now(),
        source="file_monitor",
        file_path=file_path,
        change_type=change_type,
        old_path=old_path
    )


def create_analysis_event(
    analysis_type: str,
    file_path: Optional[str] = None,
    success: bool = True,
    processing_time: Optional[float] = None
) -> AnalysisEvent:
    """Create an analysis event"""
    event_type = EventType.AST_ANALYSIS_COMPLETED if success else EventType.AST_ANALYSIS_FAILED
    priority = EventPriority.HIGH if not success else EventPriority.MEDIUM
    
    return AnalysisEvent(
        event_id=f"analysis_{int(time.time() * 1000)}_{hash(str(file_path)) % 10000}",
        event_type=event_type,
        priority=priority,
        channel=NotificationChannel.ANALYSIS,
        timestamp=datetime.now(),
        source="analysis_service",
        analysis_type=analysis_type,
        file_path=file_path,
        success=success,
        processing_time=processing_time
    )


def create_violation_event(
    violation_id: str,
    violation_type: str,
    severity: str,
    file_path: str,
    description: str
) -> ViolationEvent:
    """Create a violation event"""
    priority_map = {
        "critical": EventPriority.CRITICAL,
        "error": EventPriority.HIGH,
        "warning": EventPriority.MEDIUM,
        "info": EventPriority.LOW
    }
    
    return ViolationEvent(
        event_id=violation_id,
        event_type=EventType.VIOLATION_DETECTED,
        priority=priority_map.get(severity.lower(), EventPriority.MEDIUM),
        channel=NotificationChannel.VIOLATIONS,
        timestamp=datetime.now(),
        source="violation_detector",
        violation_id=violation_id,
        violation_type=violation_type,
        severity=severity,
        file_path=file_path,
        description=description
    )


def create_agent_event(
    session_id: str,
    event_type: EventType,
    query: Optional[str] = None,
    response: Optional[str] = None
) -> AgentEvent:
    """Create an agent processing event"""
    return AgentEvent(
        event_id=f"agent_{session_id}_{int(time.time() * 1000)}",
        event_type=event_type,
        priority=EventPriority.HIGH,
        channel=NotificationChannel.AGENT,
        timestamp=datetime.now(),
        source="l3_agent",
        session_id=session_id,
        query=query,
        response=response
    )