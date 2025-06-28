"""
Backend client for LeenVibe CLI

Handles HTTP and WebSocket communication with the sophisticated
LeenVibe backend services.
"""

import asyncio
import json
import time
from typing import Dict, Any, Optional, AsyncGenerator, Callable
from datetime import datetime

import httpx
import websockets
from rich.console import Console

from .config import CLIConfig

console = Console()


class BackendClient:
    """Client for communicating with LeenVibe backend services"""
    
    def __init__(self, config: CLIConfig):
        self.config = config
        self.client_id = f"cli_{int(time.time())}"
        self.websocket = None
        self.http_client = httpx.AsyncClient(timeout=config.timeout_seconds)
        self.connected = False
        
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def close(self):
        """Close connections and cleanup"""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        
        await self.http_client.aclose()
        self.connected = False
    
    # HTTP API Methods
    
    async def health_check(self) -> Dict[str, Any]:
        """Check backend health status"""
        try:
            response = await self.http_client.get(f"{self.config.backend_url}/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise ConnectionError(f"Backend health check failed: {e}")
    
    async def get_sessions(self) -> Dict[str, Any]:
        """Get list of active agent sessions"""
        try:
            response = await self.http_client.get(f"{self.config.backend_url}/sessions")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise ConnectionError(f"Failed to get sessions: {e}")
    
    async def get_session_state(self, client_id: str = None) -> Dict[str, Any]:
        """Get state of a specific session"""
        session_id = client_id or self.client_id
        try:
            response = await self.http_client.get(f"{self.config.backend_url}/sessions/{session_id}/state")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise ConnectionError(f"Failed to get session state: {e}")
    
    async def get_project_analysis(self, client_id: str = None) -> Dict[str, Any]:
        """Get AST-powered project analysis"""
        session_id = client_id or self.client_id
        try:
            response = await self.http_client.get(f"{self.config.backend_url}/ast/project/{session_id}/analysis")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise ConnectionError(f"Failed to get project analysis: {e}")
    
    async def find_symbol_references(self, symbol_name: str, client_id: str = None) -> Dict[str, Any]:
        """Find references to a symbol"""
        session_id = client_id or self.client_id
        try:
            response = await self.http_client.get(f"{self.config.backend_url}/ast/symbols/{session_id}/{symbol_name}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise ConnectionError(f"Failed to find symbol references: {e}")
    
    async def get_complexity_analysis(self, client_id: str = None) -> Dict[str, Any]:
        """Get code complexity analysis"""
        session_id = client_id or self.client_id
        try:
            response = await self.http_client.get(f"{self.config.backend_url}/ast/complexity/{session_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise ConnectionError(f"Failed to get complexity analysis: {e}")
    
    async def get_architecture_patterns(self, client_id: str = None) -> Dict[str, Any]:
        """Detect architecture patterns in the project"""
        session_id = client_id or self.client_id
        try:
            response = await self.http_client.get(f"{self.config.backend_url}/graph/architecture/{session_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise ConnectionError(f"Failed to get architecture patterns: {e}")
    
    async def get_circular_dependencies(self, client_id: str = None) -> Dict[str, Any]:
        """Find circular dependencies in the project"""
        session_id = client_id or self.client_id
        try:
            response = await self.http_client.get(f"{self.config.backend_url}/graph/circular-deps/{session_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise ConnectionError(f"Failed to get circular dependencies: {e}")
    
    async def get_streaming_stats(self) -> Dict[str, Any]:
        """Get event streaming service statistics"""
        try:
            response = await self.http_client.get(f"{self.config.backend_url}/streaming/stats")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise ConnectionError(f"Failed to get streaming stats: {e}")
    
    async def emit_test_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Emit a test event for debugging purposes"""
        try:
            response = await self.http_client.post(
                f"{self.config.backend_url}/streaming/test-event",
                json=event_data
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise ConnectionError(f"Failed to emit test event: {e}")
    
    # WebSocket Methods
    
    async def connect_websocket(self) -> bool:
        """Connect to WebSocket for real-time communication"""
        try:
            websocket_url = f"{self.config.websocket_url}/{self.client_id}"
            
            # Use longer timeout for initial connection (agent session creation)
            connect_timeout = self.config.timeout_seconds * 2
            
            if self.config.verbose:
                console.print(f"[dim]Connecting to WebSocket (timeout: {connect_timeout}s): {websocket_url}[/dim]")
            
            self.websocket = await asyncio.wait_for(
                websockets.connect(websocket_url),
                timeout=connect_timeout
            )
            self.connected = True
            
            if self.config.verbose:
                console.print(f"[green]Connected to WebSocket: {websocket_url}[/green]")
            
            return True
        except asyncio.TimeoutError:
            console.print(f"[yellow]WebSocket connection timed out (backend may be initializing L3 agent)[/yellow]")
            return False
        except Exception as e:
            console.print(f"[red]WebSocket connection failed: {e}[/red]")
            return False
    
    async def send_message(self, content: str, message_type: str = "message", workspace_path: str = ".") -> Dict[str, Any]:
        """Send a message through WebSocket"""
        if not self.websocket:
            raise ConnectionError("WebSocket not connected")
        
        message = {
            "type": message_type,
            "content": content,
            "workspace_path": workspace_path,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.websocket.send(json.dumps(message))
        
        # Wait for response
        response_text = await self.websocket.recv()
        return json.loads(response_text)
    
    async def send_heartbeat(self) -> bool:
        """Send heartbeat to maintain connection"""
        if not self.websocket:
            return False
        
        try:
            heartbeat = {
                "type": "heartbeat",
                "timestamp": datetime.now().isoformat()
            }
            await self.websocket.send(json.dumps(heartbeat))
            
            # Wait for acknowledgment
            response_text = await self.websocket.recv()
            response = json.loads(response_text)
            return response.get("type") == "heartbeat_ack"
        except Exception:
            return False
    
    async def listen_for_events(self, event_handler: Callable[[Dict[str, Any]], None] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """Listen for real-time events from the backend"""
        if not self.websocket:
            raise ConnectionError("WebSocket not connected")
        
        try:
            while True:
                message_text = await self.websocket.recv()
                message = json.loads(message_text)
                
                # Handle different message types
                if message.get("type") == "reconnection_sync":
                    if self.config.verbose:
                        console.print("[blue]Received reconnection sync data[/blue]")
                
                # Call event handler if provided
                if event_handler:
                    event_handler(message)
                
                yield message
                
        except websockets.exceptions.ConnectionClosed:
            self.connected = False
            console.print("[yellow]WebSocket connection closed[/yellow]")
        except Exception as e:
            self.connected = False
            console.print(f"[red]WebSocket error: {e}[/red]")
    
    async def query_agent(self, query: str, workspace_path: str = ".") -> Dict[str, Any]:
        """Send a natural language query to the L3 agent"""
        if not self.websocket:
            if not await self.connect_websocket():
                raise ConnectionError("Could not establish WebSocket connection")
        
        return await self.send_message(query, "message", workspace_path)
    
    async def execute_command(self, command: str, workspace_path: str = ".") -> Dict[str, Any]:
        """Execute a slash command through the agent"""
        if not self.websocket:
            if not await self.connect_websocket():
                raise ConnectionError("Could not establish WebSocket connection")
        
        return await self.send_message(command, "command", workspace_path)
    
    # Utility Methods
    
    async def test_connection(self) -> bool:
        """Test connection to backend services"""
        try:
            # Test HTTP connection
            health = await self.health_check()
            if health.get("status") != "healthy":
                return False
            
            # Test WebSocket connection
            if not await self.connect_websocket():
                return False
            
            # Test heartbeat
            if not await self.send_heartbeat():
                return False
            
            return True
        except Exception:
            return False
    
    def is_connected(self) -> bool:
        """Check if client is connected to backend"""
        return self.connected and self.websocket and not self.websocket.closed