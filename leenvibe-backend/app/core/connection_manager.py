from fastapi import WebSocket
from typing import Dict, Set, Optional
import logging
import json
from datetime import datetime

from ..models.event_models import ClientPreferences, NotificationChannel, EventPriority, ConnectionState
from ..services.event_streaming_service import event_streaming_service
from ..services.reconnection_service import reconnection_service, register_client_session, client_disconnected

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Enhanced WebSocket connection manager with event streaming integration"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.client_info: Dict[str, Dict] = {}
        self._streaming_enabled = True
    
    async def connect(self, websocket: WebSocket, client_id: str, preferences: Optional[ClientPreferences] = None, is_reconnection: bool = False):
        """Accept a new WebSocket connection with event streaming and reconnection handling"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        
        # Store connection info
        self.client_info[client_id] = {
            "connected_at": datetime.now().isoformat(),
            "user_agent": websocket.headers.get("user-agent", "unknown"),
            "client_type": self._detect_client_type(websocket.headers.get("user-agent", "")),
            "streaming_enabled": True,
            "is_reconnection": is_reconnection
        }
        
        # Set up default preferences if not provided
        if preferences is None:
            preferences = self._create_default_preferences(client_id, websocket)
        
        # Create connection state for reconnection tracking
        connection_state = ConnectionState(
            client_id=client_id,
            connected_at=datetime.now(),
            last_seen=datetime.now(),
            preferences=preferences,
            sequence_number=0,  # Will be updated during reconnection
            last_activity=datetime.now()
        )
        
        # Register with event streaming service
        if self._streaming_enabled:
            event_streaming_service.register_client(client_id, websocket, preferences)
        
        # Register session for reconnection tracking
        register_client_session(client_id, connection_state)
        
        connection_type = "reconnected" if is_reconnection else "new"
        logger.info(f"Client {client_id} {connection_type} connection with streaming. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, client_id: str):
        """Remove a WebSocket connection and clean up streaming"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.client_info:
            del self.client_info[client_id]
        
        # Unregister from event streaming
        if self._streaming_enabled:
            event_streaming_service.unregister_client(client_id)
        
        # Mark client as disconnected for reconnection service
        client_disconnected(client_id)
        
        logger.info(f"Client {client_id} disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, client_id: str):
        """Send a message to a specific client"""
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Error sending personal message to {client_id}: {e}")
                self.disconnect(client_id)
    
    async def send_json_message(self, data: Dict, client_id: str):
        """Send a JSON message to a specific client"""
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                await websocket.send_text(json.dumps(data, default=str))
            except Exception as e:
                logger.error(f"Error sending JSON message to {client_id}: {e}")
                self.disconnect(client_id)
    
    async def broadcast(self, message: str):
        """Send a message to all connected clients"""
        disconnected_clients = []
        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to {client_id}: {e}")
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            self.disconnect(client_id)
    
    async def broadcast_json(self, data: Dict):
        """Broadcast a JSON message to all connected clients"""
        message = json.dumps(data, default=str)
        await self.broadcast(message)
    
    def update_client_preferences(self, client_id: str, preferences: ClientPreferences):
        """Update client notification preferences"""
        if self._streaming_enabled and client_id in self.active_connections:
            event_streaming_service.update_client_preferences(client_id, preferences)
            logger.info(f"Updated streaming preferences for client {client_id}")
    
    def _detect_client_type(self, user_agent: str) -> str:
        """Detect client type from user agent"""
        user_agent_lower = user_agent.lower()
        if "ios" in user_agent_lower or "iphone" in user_agent_lower or "ipad" in user_agent_lower:
            return "ios"
        elif "cli" in user_agent_lower or "curl" in user_agent_lower or "python" in user_agent_lower:
            return "cli"
        elif "browser" in user_agent_lower or "mozilla" in user_agent_lower or "chrome" in user_agent_lower:
            return "web"
        else:
            return "unknown"
    
    def _create_default_preferences(self, client_id: str, websocket: WebSocket) -> ClientPreferences:
        """Create default preferences based on client type"""
        client_type = self._detect_client_type(websocket.headers.get("user-agent", ""))
        
        if client_type == "ios":
            # iOS clients want important events with batching
            return ClientPreferences(
                client_id=client_id,
                enabled_channels=[NotificationChannel.ALL],
                min_priority=EventPriority.MEDIUM,
                max_events_per_second=5,
                enable_batching=True,
                batch_interval_ms=1000,
                enable_compression=False  # iOS handles decompression
            )
        elif client_type == "cli":
            # CLI clients want immediate, high-priority events
            return ClientPreferences(
                client_id=client_id,
                enabled_channels=[NotificationChannel.ANALYSIS, NotificationChannel.VIOLATIONS, NotificationChannel.AGENT],
                min_priority=EventPriority.HIGH,
                max_events_per_second=20,
                enable_batching=False,
                batch_interval_ms=100,
                enable_compression=True  # CLI can handle compression
            )
        else:
            # Default preferences for other clients
            return ClientPreferences(
                client_id=client_id,
                enabled_channels=[NotificationChannel.ALL],
                min_priority=EventPriority.MEDIUM,
                max_events_per_second=10,
                enable_batching=True,
                batch_interval_ms=500,
                enable_compression=False
            )
    
    def get_connection_info(self) -> Dict:
        """Get comprehensive information about current connections"""
        base_info = {
            "total_connections": len(self.active_connections),
            "connected_clients": list(self.active_connections.keys()),
            "client_details": self.client_info,
            "streaming_enabled": self._streaming_enabled
        }
        
        # Add streaming service info if enabled
        if self._streaming_enabled:
            base_info["streaming_stats"] = event_streaming_service.get_stats()
            base_info["streaming_clients"] = event_streaming_service.get_client_info()
        
        return base_info
    
    def enable_streaming(self):
        """Enable event streaming for all connections"""
        self._streaming_enabled = True
        logger.info("Event streaming enabled for connection manager")
    
    def disable_streaming(self):
        """Disable event streaming for all connections"""
        self._streaming_enabled = False
        logger.info("Event streaming disabled for connection manager")