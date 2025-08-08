"""
WebSocket Connection Monitoring System

Provides comprehensive WebSocket monitoring with:
- Connection lifecycle tracking
- Message throughput monitoring
- Connection health and quality metrics
- Real-time connection analytics
- WebSocket-specific error tracking
- Performance optimization recommendations
"""

import asyncio
import time
import json
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Set
import threading
from statistics import mean, median

from .logging_config import get_logger
from .performance_monitor import performance_monitor
from .error_tracker import error_tracker, ErrorSeverity, ErrorCategory


logger = get_logger(__name__)


class ConnectionState(str, Enum):
    """WebSocket connection states"""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class MessageType(str, Enum):
    """WebSocket message types"""
    TEXT = "text"
    BINARY = "binary"
    PING = "ping"
    PONG = "pong"
    CLOSE = "close"


@dataclass
class ConnectionInfo:
    """Information about a WebSocket connection"""
    connection_id: str
    client_ip: str
    user_agent: Optional[str]
    user_id: Optional[str]
    session_id: Optional[str]
    connected_at: datetime
    disconnected_at: Optional[datetime] = None
    state: ConnectionState = ConnectionState.CONNECTING
    
    # Connection metrics
    bytes_sent: int = 0
    bytes_received: int = 0
    messages_sent: int = 0
    messages_received: int = 0
    ping_count: int = 0
    pong_count: int = 0
    
    # Performance metrics
    last_activity: Optional[datetime] = None
    avg_message_size: float = 0.0
    peak_message_rate: float = 0.0
    connection_quality: float = 1.0  # 0.0 to 1.0
    
    # Error tracking
    error_count: int = 0
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None


@dataclass
class MessageMetrics:
    """Metrics for a WebSocket message"""
    message_id: str
    connection_id: str
    timestamp: datetime
    message_type: MessageType
    size_bytes: int
    processing_time_ms: float = 0.0
    direction: str = "inbound"  # inbound or outbound
    endpoint: Optional[str] = None
    error: Optional[str] = None


@dataclass
class ConnectionPoolStats:
    """Statistics for the connection pool"""
    total_connections: int = 0
    active_connections: int = 0
    peak_connections: int = 0
    total_messages_processed: int = 0
    total_bytes_transferred: int = 0
    avg_connection_duration: float = 0.0
    avg_messages_per_connection: float = 0.0
    connection_success_rate: float = 1.0


class WebSocketMonitor:
    """
    Comprehensive WebSocket connection monitoring system
    
    Tracks all WebSocket connections, monitors their performance,
    and provides analytics and alerting for connection issues.
    """
    
    def __init__(self, max_history_size: int = 10000):
        self.max_history_size = max_history_size
        self.active_connections: Dict[str, ConnectionInfo] = {}
        self.connection_history: deque = deque(maxlen=max_history_size)
        self.message_history: deque = deque(maxlen=max_history_size)
        
        # Performance tracking
        self.message_rate_buckets: deque = deque(maxlen=300)  # 5 minutes at 1-second intervals
        self.connection_rate_buckets: deque = deque(maxlen=300)
        
        # Statistics
        self.pool_stats = ConnectionPoolStats()
        self.endpoint_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'total_connections': 0,
            'active_connections': 0,
            'total_messages': 0,
            'avg_message_size': 0.0,
            'error_count': 0,
            'response_times': deque(maxlen=1000)
        })
        
        # Monitoring configuration
        self.monitoring_config = {
            'max_idle_time_minutes': 30,
            'max_connection_duration_hours': 24,
            'message_rate_alert_threshold': 1000,  # messages per minute
            'connection_count_alert_threshold': 1000,
            'large_message_threshold_kb': 100,
            'slow_message_threshold_ms': 5000,
            'quality_degradation_threshold': 0.7
        }
        
        # Background monitoring
        self._monitoring_active = False
        self._monitoring_task: Optional[asyncio.Task] = None
        
        # Thread safety
        self._lock = threading.RLock()
    
    def start_monitoring(self):
        """Start background WebSocket monitoring"""
        if self._monitoring_active:
            logger.warning("WebSocket monitoring already active")
            return
        
        self._monitoring_active = True
        self._monitoring_task = asyncio.create_task(self._background_monitoring())
        logger.info("WebSocket monitoring started")
    
    async def stop_monitoring(self):
        """Stop background WebSocket monitoring"""
        if not self._monitoring_active:
            return
        
        self._monitoring_active = False
        
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("WebSocket monitoring stopped")
    
    async def _background_monitoring(self):
        """Background task for WebSocket monitoring and cleanup"""
        try:
            while self._monitoring_active:
                await self._update_statistics()
                await self._check_connection_health()
                await self._cleanup_stale_connections()
                await self._check_alerts()
                await asyncio.sleep(10)  # Run every 10 seconds
        except asyncio.CancelledError:
            logger.info("WebSocket monitoring background task cancelled")
        except Exception as e:
            logger.error("WebSocket monitoring background task error", error=str(e))
    
    def register_connection(
        self,
        connection_id: str,
        client_ip: str,
        user_agent: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        endpoint: Optional[str] = None
    ) -> ConnectionInfo:
        """Register a new WebSocket connection"""
        
        connection_info = ConnectionInfo(
            connection_id=connection_id,
            client_ip=client_ip,
            user_agent=user_agent,
            user_id=user_id,
            session_id=session_id,
            connected_at=datetime.now(),
            state=ConnectionState.CONNECTING,
            last_activity=datetime.now()
        )
        
        with self._lock:
            self.active_connections[connection_id] = connection_info
            
            # Update statistics
            self.pool_stats.total_connections += 1
            self.pool_stats.active_connections = len(self.active_connections)
            self.pool_stats.peak_connections = max(
                self.pool_stats.peak_connections,
                self.pool_stats.active_connections
            )
            
            # Update endpoint statistics
            if endpoint:
                self.endpoint_stats[endpoint]['total_connections'] += 1
                self.endpoint_stats[endpoint]['active_connections'] = len([
                    c for c in self.active_connections.values()
                    if c.connection_id.startswith(endpoint)
                ])
        
        logger.info(
            "WebSocket connection registered",
            connection_id=connection_id,
            client_ip=client_ip,
            user_id=user_id,
            endpoint=endpoint
        )
        
        return connection_info
    
    def update_connection_state(self, connection_id: str, state: ConnectionState):
        """Update connection state"""
        with self._lock:
            if connection_id in self.active_connections:
                self.active_connections[connection_id].state = state
                self.active_connections[connection_id].last_activity = datetime.now()
                
                logger.debug(
                    "Connection state updated",
                    connection_id=connection_id,
                    state=state.value
                )
    
    def record_message(
        self,
        connection_id: str,
        message_type: MessageType,
        size_bytes: int,
        direction: str = "inbound",
        endpoint: Optional[str] = None,
        processing_time_ms: float = 0.0,
        error: Optional[str] = None
    ) -> str:
        """Record a WebSocket message"""
        
        message_id = f"msg_{connection_id}_{int(time.time() * 1000000)}"
        
        message_metrics = MessageMetrics(
            message_id=message_id,
            connection_id=connection_id,
            timestamp=datetime.now(),
            message_type=message_type,
            size_bytes=size_bytes,
            direction=direction,
            endpoint=endpoint,
            processing_time_ms=processing_time_ms,
            error=error
        )
        
        with self._lock:
            self.message_history.append(message_metrics)
            
            # Update connection statistics
            if connection_id in self.active_connections:
                conn = self.active_connections[connection_id]
                conn.last_activity = datetime.now()
                
                if direction == "outbound":
                    conn.bytes_sent += size_bytes
                    conn.messages_sent += 1
                else:
                    conn.bytes_received += size_bytes
                    conn.messages_received += 1
                
                # Update message type counters
                if message_type == MessageType.PING:
                    conn.ping_count += 1
                elif message_type == MessageType.PONG:
                    conn.pong_count += 1
                
                # Update average message size
                total_messages = conn.messages_sent + conn.messages_received
                total_bytes = conn.bytes_sent + conn.bytes_received
                conn.avg_message_size = total_bytes / total_messages if total_messages > 0 else 0.0
                
                # Handle errors
                if error:
                    conn.error_count += 1
                    conn.last_error = error
                    conn.last_error_time = datetime.now()
                    
                    # Track error in error tracker
                    try:
                        error_tracker.track_error(
                            error=Exception(error),
                            service="websocket",
                            component="connection",
                            severity=ErrorSeverity.MEDIUM,
                            category=ErrorCategory.NETWORK,
                            context={
                                'connection_id': connection_id,
                                'message_type': message_type.value,
                                'message_size': size_bytes,
                                'endpoint': endpoint
                            }
                        )
                    except Exception as e:
                        logger.error("Failed to track WebSocket error", error=str(e))
            
            # Update endpoint statistics
            if endpoint:
                endpoint_stat = self.endpoint_stats[endpoint]
                endpoint_stat['total_messages'] += 1
                
                # Update average message size
                current_avg = endpoint_stat.get('avg_message_size', 0.0)
                total_messages = endpoint_stat['total_messages']
                endpoint_stat['avg_message_size'] = (
                    (current_avg * (total_messages - 1) + size_bytes) / total_messages
                )
                
                # Track response times
                if processing_time_ms > 0:
                    endpoint_stat['response_times'].append(processing_time_ms)
                
                # Track errors
                if error:
                    endpoint_stat['error_count'] += 1
            
            # Update pool statistics
            self.pool_stats.total_messages_processed += 1
            self.pool_stats.total_bytes_transferred += size_bytes
        
        # Check for performance alerts
        if processing_time_ms > self.monitoring_config['slow_message_threshold_ms']:
            logger.warning(
                "Slow WebSocket message processing",
                connection_id=connection_id,
                processing_time_ms=processing_time_ms,
                message_size=size_bytes
            )
        
        if size_bytes > self.monitoring_config['large_message_threshold_kb'] * 1024:
            logger.info(
                "Large WebSocket message",
                connection_id=connection_id,
                message_size_kb=size_bytes / 1024
            )
        
        return message_id
    
    def disconnect_connection(
        self,
        connection_id: str,
        reason: Optional[str] = None,
        error: Optional[str] = None
    ):
        """Mark a connection as disconnected"""
        
        with self._lock:
            if connection_id in self.active_connections:
                conn = self.active_connections[connection_id]
                conn.state = ConnectionState.DISCONNECTED
                conn.disconnected_at = datetime.now()
                
                if error:
                    conn.error_count += 1
                    conn.last_error = error
                    conn.last_error_time = datetime.now()
                
                # Move to history
                self.connection_history.append(conn)
                del self.active_connections[connection_id]
                
                # Update statistics
                self.pool_stats.active_connections = len(self.active_connections)
                
                # Calculate connection duration
                if conn.connected_at and conn.disconnected_at:
                    duration_seconds = (conn.disconnected_at - conn.connected_at).total_seconds()
                    
                    # Update average connection duration
                    total_connections = self.pool_stats.total_connections
                    current_avg = self.pool_stats.avg_connection_duration
                    self.pool_stats.avg_connection_duration = (
                        (current_avg * (total_connections - 1) + duration_seconds) / total_connections
                    )
                
                logger.info(
                    "WebSocket connection disconnected",
                    connection_id=connection_id,
                    reason=reason,
                    duration_seconds=duration_seconds if 'duration_seconds' in locals() else None,
                    messages_sent=conn.messages_sent,
                    messages_received=conn.messages_received
                )
            else:
                logger.warning("Attempted to disconnect unknown connection", connection_id=connection_id)
    
    async def _update_statistics(self):
        """Update real-time statistics"""
        current_time = time.time()
        
        # Count messages in the last minute
        one_minute_ago = datetime.now() - timedelta(minutes=1)
        recent_messages = [
            msg for msg in list(self.message_history)[-1000:]  # Check last 1000 messages
            if msg.timestamp >= one_minute_ago
        ]
        
        # Update message rate buckets
        with self._lock:
            self.message_rate_buckets.append({
                'timestamp': current_time,
                'message_count': len(recent_messages),
                'active_connections': len(self.active_connections)
            })
            
            # Update connection rate
            self.connection_rate_buckets.append({
                'timestamp': current_time,
                'active_connections': len(self.active_connections)
            })
            
            # Update pool statistics
            if len(self.active_connections) > 0:
                total_messages = sum(
                    conn.messages_sent + conn.messages_received
                    for conn in self.active_connections.values()
                )
                self.pool_stats.avg_messages_per_connection = total_messages / len(self.active_connections)
            
            # Calculate connection success rate
            total_connections = self.pool_stats.total_connections
            successful_connections = total_connections - len([
                conn for conn in self.connection_history
                if conn.error_count > 0 or conn.state == ConnectionState.ERROR
            ])
            self.pool_stats.connection_success_rate = (
                successful_connections / total_connections if total_connections > 0 else 1.0
            )
    
    async def _check_connection_health(self):
        """Check health of active connections"""
        current_time = datetime.now()
        idle_threshold = timedelta(minutes=self.monitoring_config['max_idle_time_minutes'])
        duration_threshold = timedelta(hours=self.monitoring_config['max_connection_duration_hours'])
        
        connections_to_check = []
        
        with self._lock:
            connections_to_check = list(self.active_connections.values())
        
        for conn in connections_to_check:
            # Check for idle connections
            if conn.last_activity and current_time - conn.last_activity > idle_threshold:
                logger.warning(
                    "Idle WebSocket connection detected",
                    connection_id=conn.connection_id,
                    idle_minutes=(current_time - conn.last_activity).total_seconds() / 60
                )
                
                # Update connection quality
                conn.connection_quality = max(0.5, conn.connection_quality - 0.1)
            
            # Check for long-running connections
            if current_time - conn.connected_at > duration_threshold:
                logger.info(
                    "Long-running WebSocket connection",
                    connection_id=conn.connection_id,
                    duration_hours=(current_time - conn.connected_at).total_seconds() / 3600
                )
            
            # Check connection quality based on errors
            if conn.error_count > 0:
                total_messages = conn.messages_sent + conn.messages_received
                if total_messages > 0:
                    error_rate = conn.error_count / total_messages
                    conn.connection_quality = max(0.0, 1.0 - error_rate)
                    
                    if conn.connection_quality < self.monitoring_config['quality_degradation_threshold']:
                        logger.warning(
                            "WebSocket connection quality degraded",
                            connection_id=conn.connection_id,
                            quality=conn.connection_quality,
                            error_count=conn.error_count,
                            total_messages=total_messages
                        )
    
    async def _cleanup_stale_connections(self):
        """Clean up stale or abandoned connections"""
        current_time = datetime.now()
        stale_threshold = timedelta(hours=1)  # Connections idle for more than 1 hour
        
        stale_connections = []
        
        with self._lock:
            for conn_id, conn in self.active_connections.items():
                if (conn.last_activity and
                    current_time - conn.last_activity > stale_threshold and
                    conn.state not in [ConnectionState.DISCONNECTING, ConnectionState.DISCONNECTED]):
                    
                    stale_connections.append(conn_id)
        
        # Mark stale connections for cleanup
        for conn_id in stale_connections:
            logger.info("Cleaning up stale WebSocket connection", connection_id=conn_id)
            self.disconnect_connection(conn_id, reason="stale_connection_cleanup")
    
    async def _check_alerts(self):
        """Check for conditions that should trigger alerts"""
        
        # Check message rate
        if len(self.message_rate_buckets) >= 5:  # At least 5 data points
            recent_rates = [bucket['message_count'] for bucket in list(self.message_rate_buckets)[-5:]]
            avg_rate = sum(recent_rates) / len(recent_rates)
            
            if avg_rate > self.monitoring_config['message_rate_alert_threshold']:
                logger.warning(
                    "High WebSocket message rate detected",
                    avg_messages_per_minute=avg_rate,
                    threshold=self.monitoring_config['message_rate_alert_threshold']
                )
        
        # Check connection count
        active_count = len(self.active_connections)
        if active_count > self.monitoring_config['connection_count_alert_threshold']:
            logger.warning(
                "High WebSocket connection count",
                active_connections=active_count,
                threshold=self.monitoring_config['connection_count_alert_threshold']
            )
        
        # Check for degraded connections
        degraded_connections = [
            conn for conn in self.active_connections.values()
            if conn.connection_quality < self.monitoring_config['quality_degradation_threshold']
        ]
        
        if len(degraded_connections) > len(self.active_connections) * 0.1:  # > 10% degraded
            logger.warning(
                "Multiple degraded WebSocket connections",
                degraded_count=len(degraded_connections),
                total_active=len(self.active_connections),
                degradation_percentage=len(degraded_connections) / len(self.active_connections) * 100
            )
    
    def get_connection_stats(self, connection_id: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics for a specific connection or all connections"""
        
        if connection_id:
            with self._lock:
                if connection_id in self.active_connections:
                    conn = self.active_connections[connection_id]
                    return {
                        'connection_id': conn.connection_id,
                        'state': conn.state.value,
                        'connected_at': conn.connected_at.isoformat(),
                        'last_activity': conn.last_activity.isoformat() if conn.last_activity else None,
                        'duration_seconds': (datetime.now() - conn.connected_at).total_seconds(),
                        'bytes_sent': conn.bytes_sent,
                        'bytes_received': conn.bytes_received,
                        'messages_sent': conn.messages_sent,
                        'messages_received': conn.messages_received,
                        'error_count': conn.error_count,
                        'connection_quality': conn.connection_quality,
                        'avg_message_size': conn.avg_message_size,
                        'client_ip': conn.client_ip,
                        'user_id': conn.user_id
                    }
                else:
                    return {'error': 'Connection not found'}
        
        # Return overall statistics
        with self._lock:
            active_connections = list(self.active_connections.values())
            
        return {
            'pool_stats': {
                'total_connections': self.pool_stats.total_connections,
                'active_connections': self.pool_stats.active_connections,
                'peak_connections': self.pool_stats.peak_connections,
                'total_messages_processed': self.pool_stats.total_messages_processed,
                'total_bytes_transferred': self.pool_stats.total_bytes_transferred,
                'avg_connection_duration': self.pool_stats.avg_connection_duration,
                'avg_messages_per_connection': self.pool_stats.avg_messages_per_connection,
                'connection_success_rate': self.pool_stats.connection_success_rate
            },
            'current_connections': len(active_connections),
            'connections_by_state': {
                state.value: len([c for c in active_connections if c.state == state])
                for state in ConnectionState
            },
            'message_rate_last_minute': (
                self.message_rate_buckets[-1]['message_count'] if self.message_rate_buckets else 0
            ),
            'endpoint_stats': dict(self.endpoint_stats) if self.endpoint_stats else {}
        }
    
    def get_performance_metrics(self, time_window_minutes: int = 60) -> Dict[str, Any]:
        """Get WebSocket performance metrics for a time window"""
        
        cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)
        
        # Filter recent messages
        recent_messages = [
            msg for msg in list(self.message_history)
            if msg.timestamp >= cutoff_time
        ]
        
        if not recent_messages:
            return {
                'time_window_minutes': time_window_minutes,
                'message_count': 0,
                'message': 'No messages in time window'
            }
        
        # Calculate metrics
        total_messages = len(recent_messages)
        total_bytes = sum(msg.size_bytes for msg in recent_messages)
        avg_message_size = total_bytes / total_messages if total_messages > 0 else 0
        
        processing_times = [msg.processing_time_ms for msg in recent_messages if msg.processing_time_ms > 0]
        avg_processing_time = mean(processing_times) if processing_times else 0
        
        error_messages = [msg for msg in recent_messages if msg.error]
        error_rate = len(error_messages) / total_messages if total_messages > 0 else 0
        
        # Message types distribution
        message_type_dist = defaultdict(int)
        for msg in recent_messages:
            message_type_dist[msg.message_type.value] += 1
        
        # Direction distribution
        direction_dist = defaultdict(int)
        for msg in recent_messages:
            direction_dist[msg.direction] += 1
        
        return {
            'time_window_minutes': time_window_minutes,
            'message_count': total_messages,
            'total_bytes': total_bytes,
            'avg_message_size_bytes': round(avg_message_size, 2),
            'messages_per_minute': round(total_messages / time_window_minutes, 2),
            'bytes_per_minute': round(total_bytes / time_window_minutes, 2),
            'avg_processing_time_ms': round(avg_processing_time, 2),
            'max_processing_time_ms': max(processing_times) if processing_times else 0,
            'error_rate': round(error_rate, 4),
            'error_count': len(error_messages),
            'message_types': dict(message_type_dist),
            'directions': dict(direction_dist)
        }
    
    def get_connection_list(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get list of active connections with basic info"""
        
        with self._lock:
            connections = list(self.active_connections.values())
        
        # Sort by connection time (newest first)
        connections.sort(key=lambda c: c.connected_at, reverse=True)
        
        connection_list = []
        for conn in connections[:limit]:
            connection_list.append({
                'connection_id': conn.connection_id,
                'client_ip': conn.client_ip,
                'user_id': conn.user_id,
                'state': conn.state.value,
                'connected_at': conn.connected_at.isoformat(),
                'duration_minutes': (datetime.now() - conn.connected_at).total_seconds() / 60,
                'messages_total': conn.messages_sent + conn.messages_received,
                'bytes_total': conn.bytes_sent + conn.bytes_received,
                'error_count': conn.error_count,
                'connection_quality': conn.connection_quality
            })
        
        return connection_list
    
    def get_monitoring_summary(self) -> Dict[str, Any]:
        """Get comprehensive monitoring summary"""
        
        stats = self.get_connection_stats()
        performance = self.get_performance_metrics()
        
        return {
            'monitoring_active': self._monitoring_active,
            'timestamp': datetime.now().isoformat(),
            'connection_summary': {
                'active_connections': stats['pool_stats']['active_connections'],
                'total_connections': stats['pool_stats']['total_connections'],
                'peak_connections': stats['pool_stats']['peak_connections'],
                'connection_success_rate': stats['pool_stats']['connection_success_rate']
            },
            'performance_summary': {
                'messages_per_minute': performance.get('messages_per_minute', 0),
                'avg_message_size': performance.get('avg_message_size_bytes', 0),
                'avg_processing_time': performance.get('avg_processing_time_ms', 0),
                'error_rate': performance.get('error_rate', 0)
            },
            'health_indicators': {
                'degraded_connections': len([
                    c for c in self.active_connections.values()
                    if c.connection_quality < 0.8
                ]),
                'idle_connections': len([
                    c for c in self.active_connections.values()
                    if c.last_activity and
                    (datetime.now() - c.last_activity).total_seconds() > 300  # 5 minutes
                ]),
                'error_connections': len([
                    c for c in self.active_connections.values()
                    if c.error_count > 0
                ])
            }
        }


# Global WebSocket monitor instance
websocket_monitor = WebSocketMonitor()


# Convenience functions
async def start_websocket_monitoring():
    """Start WebSocket monitoring"""
    websocket_monitor.start_monitoring()


async def stop_websocket_monitoring():
    """Stop WebSocket monitoring"""
    await websocket_monitor.stop_monitoring()


def register_websocket_connection(connection_id: str, client_ip: str, **kwargs) -> ConnectionInfo:
    """Register a new WebSocket connection"""
    return websocket_monitor.register_connection(connection_id, client_ip, **kwargs)


def record_websocket_message(connection_id: str, message_type: MessageType, size_bytes: int, **kwargs) -> str:
    """Record a WebSocket message"""
    return websocket_monitor.record_message(connection_id, message_type, size_bytes, **kwargs)


def disconnect_websocket(connection_id: str, **kwargs):
    """Disconnect a WebSocket connection"""
    websocket_monitor.disconnect_connection(connection_id, **kwargs)


def get_websocket_stats() -> Dict[str, Any]:
    """Get WebSocket statistics"""
    return websocket_monitor.get_monitoring_summary()