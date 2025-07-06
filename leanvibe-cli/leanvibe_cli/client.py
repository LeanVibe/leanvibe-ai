"""
Backend client for LeanVibe CLI

Handles HTTP and WebSocket communication with the sophisticated
LeanVibe backend services.
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
    """Client for communicating with LeanVibe backend services"""
    
    def __init__(self, config: CLIConfig):
        self.config = config
        self.client_id = f"cli_{int(time.time())}"
        self.websocket = None
        # Optimized HTTP client with connection pooling and shorter timeouts for CLI operations
        # HTTP/2 is enabled only if h2 package is available
        try:
            import h2
            http2_enabled = True
        except ImportError:
            http2_enabled = False
        
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=5.0, read=config.timeout_seconds, write=10.0, pool=5.0),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            http2=http2_enabled
        )
        self.connected = False
        # Response cache for frequently accessed data
        self._cache = {}
        self._cache_ttl = {}
        
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
        """Check backend health status with caching"""
        cache_key = "health_check"
        
        # Check cache first (cache for 5 seconds)
        if self._is_cached(cache_key, ttl_seconds=5):
            return self._cache[cache_key]
        
        try:
            response = await self.http_client.get(f"{self.config.backend_url}/health")
            response.raise_for_status()
            result = response.json()
            self._set_cache(cache_key, result)
            return result
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
        """Get complexity analysis"""
        session_id = client_id or self.client_id
        try:
            response = await self.http_client.get(f"{self.config.backend_url}/ast/complexity/{session_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise ConnectionError(f"Failed to get complexity analysis: {e}")
    
    # iOS Integration Methods
    
    async def get_ios_status(self) -> Dict[str, Any]:
        """Get iOS app connection status"""
        try:
            response = await self.http_client.get(f"{self.config.backend_url}/api/ios/status")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"connected": False, "error": str(e)}
    
    async def get_ios_details(self) -> Dict[str, Any]:
        """Get detailed iOS connection information"""
        try:
            response = await self.http_client.get(f"{self.config.backend_url}/api/ios/details")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise ConnectionError(f"Failed to get iOS details: {e}")
    
    async def send_ios_notification(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send notification to iOS app"""
        try:
            response = await self.http_client.post(
                f"{self.config.backend_url}/api/ios/notify",
                json=notification_data
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_projects(self) -> list:
        """Get all projects"""
        try:
            response = await self.http_client.get(f"{self.config.backend_url}/api/projects/")
            response.raise_for_status()
            return response.json().get("projects", [])
        except Exception as e:
            raise ConnectionError(f"Failed to get projects: {e}")
    
    async def get_ios_projects(self) -> list:
        """Get projects from iOS app"""
        try:
            response = await self.http_client.get(f"{self.config.backend_url}/api/ios/projects")
            response.raise_for_status()
            return response.json().get("projects", [])
        except Exception as e:
            return []
    
    async def sync_ios_projects(self, force: bool = False) -> Dict[str, Any]:
        """Sync projects with iOS app"""
        try:
            payload = {"force": force}
            response = await self.http_client.post(
                f"{self.config.backend_url}/api/ios/sync/projects",
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def sync_ios_tasks(self, force: bool = False) -> Dict[str, Any]:
        """Sync tasks with iOS app"""
        try:
            payload = {"force": force}
            response = await self.http_client.post(
                f"{self.config.backend_url}/api/ios/sync/tasks",
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def sync_ios_metrics(self, force: bool = False) -> Dict[str, Any]:
        """Sync metrics with iOS app"""
        try:
            payload = {"force": force}
            response = await self.http_client.post(
                f"{self.config.backend_url}/api/ios/sync/metrics",
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def push_projects_to_ios(self, projects: list) -> Dict[str, Any]:
        """Push projects to iOS app"""
        try:
            payload = {"projects": projects}
            response = await self.http_client.post(
                f"{self.config.backend_url}/api/ios/projects/push",
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def pull_projects_from_ios(self) -> Dict[str, Any]:
        """Pull projects from iOS app"""
        try:
            response = await self.http_client.post(f"{self.config.backend_url}/api/ios/projects/pull")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def create_ios_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create task on iOS app"""
        try:
            response = await self.http_client.post(
                f"{self.config.backend_url}/api/ios/tasks",
                json=task_data
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def update_ios_task(self, task_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update task on iOS app"""
        try:
            response = await self.http_client.put(
                f"{self.config.backend_url}/api/ios/tasks/{task_id}",
                json=update_data
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_ios_tasks(self, status_filter: Optional[str] = None) -> list:
        """Get tasks from iOS app"""
        try:
            params = {}
            if status_filter:
                params["status"] = status_filter
            
            response = await self.http_client.get(
                f"{self.config.backend_url}/api/ios/tasks",
                params=params
            )
            response.raise_for_status()
            return response.json().get("tasks", [])
        except Exception as e:
            return []
    
    async def launch_ios_app(self, launch_data: Dict[str, Any]) -> Dict[str, Any]:
        """Launch iOS app with specific screen or content"""
        try:
            response = await self.http_client.post(
                f"{self.config.backend_url}/api/ios/launch",
                json=launch_data
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def monitor_ios_events(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Monitor iOS app events via WebSocket"""
        if not self.websocket:
            await self.connect_websocket()
        
        try:
            while True:
                message = await self.websocket.recv()
                event = json.loads(message)
                
                # Filter for iOS events
                if event.get("source") == "ios" or event.get("type", "").startswith("ios_"):
                    yield event
                    
        except websockets.exceptions.ConnectionClosed:
            self.connected = False
            raise ConnectionError("WebSocket connection closed")
    
    async def query_agent(self, query: str) -> Dict[str, Any]:
        """Query the AI agent"""
        try:
            payload = {
                "message": query,
                "session_id": self.client_id,
                "timestamp": datetime.now().isoformat()
            }
            response = await self.http_client.post(
                f"{self.config.backend_url}/api/ai/chat",
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    async def notify_command_execution(self, command_name: str, command_args: list, working_dir: str):
        """Notify backend of command execution"""
        try:
            payload = {
                "command": command_name,
                "args": command_args,
                "working_dir": working_dir,
                "client_id": self.client_id,
                "timestamp": datetime.now().isoformat()
            }
            response = await self.http_client.post(
                f"{self.config.backend_url}/api/cli/command/start",
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except Exception:
            # Don't fail CLI operations if notification fails
            pass
    
    async def notify_command_completion(self, command_name: str, exit_code: int):
        """Notify backend of command completion"""
        try:
            payload = {
                "command": command_name,
                "exit_code": exit_code,
                "client_id": self.client_id,
                "timestamp": datetime.now().isoformat()
            }
            response = await self.http_client.post(
                f"{self.config.backend_url}/api/cli/command/complete",
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except Exception:
            # Don't fail CLI operations if notification fails
            pass
    
    async def notify_command_error(self, command_name: str, error_message: str):
        """Notify backend of command error"""
        try:
            payload = {
                "command": command_name,
                "error": error_message,
                "client_id": self.client_id,
                "timestamp": datetime.now().isoformat()
            }
            response = await self.http_client.post(
                f"{self.config.backend_url}/api/cli/command/error",
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except Exception:
            # Don't fail CLI operations if notification fails
            pass
    
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
    
    # CLI Bridge Integration Methods
    
    async def notify_command_execution(self, command_name: str, command_args: list, working_dir: str):
        """Notify backend of command execution start"""
        try:
            await self.post("/cli/command", {
                "command": command_name,
                "args": command_args[1:] if len(command_args) > 1 else [],
                "workspace_path": working_dir,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            if self.config.verbose:
                console.print(f"[yellow]Could not notify backend of command execution: {e}[/yellow]")
    
    async def notify_command_completion(self, command_name: str, exit_code: int):
        """Notify backend of command completion"""
        try:
            if self.websocket:
                await self.websocket.send(json.dumps({
                    "type": "cli_command_completed",
                    "command": command_name,
                    "exit_code": exit_code,
                    "timestamp": datetime.now().isoformat()
                }))
        except Exception as e:
            if self.config.verbose:
                console.print(f"[yellow]Could not notify backend of command completion: {e}[/yellow]")
    
    async def notify_command_error(self, command_name: str, error_message: str):
        """Notify backend of command error"""
        try:
            if self.websocket:
                await self.websocket.send(json.dumps({
                    "type": "cli_command_error",
                    "command": command_name,
                    "error": error_message,
                    "timestamp": datetime.now().isoformat()
                }))
        except Exception as e:
            if self.config.verbose:
                console.print(f"[yellow]Could not notify backend of command error: {e}[/yellow]")
    
    async def get_cli_bridge_status(self) -> Dict[str, Any]:
        """Get CLI bridge status from backend"""
        return await self.get("/cli/status")
    
    async def get_monitoring_data(self) -> Dict[str, Any]:
        """Get monitoring data from backend"""
        return await self.get("/cli/monitor")
    
    async def list_connected_devices(self) -> Dict[str, Any]:
        """List connected iOS devices"""
        return await self.get("/cli/devices")
    
    async def query_agent(self, query: str, workspace_path: str = ".") -> Dict[str, Any]:
        """Send a natural language query to the L3 agent with optimizations"""
        # Use HTTP for simple queries to avoid WebSocket overhead
        if len(query) < 100 and not any(keyword in query.lower() for keyword in ['interactive', 'session', 'real-time']):
            try:
                payload = {
                    "query": query,
                    "session_id": self.client_id,
                    "workspace_path": workspace_path
                }
                response = await self.http_client.post(
                    f"{self.config.backend_url}/api/v1/cli/query",
                    json=payload,
                    timeout=15.0  # Shorter timeout for simple queries
                )
                response.raise_for_status()
                return response.json()
            except Exception:
                # Fall back to WebSocket if HTTP fails
                pass
        
        # Use WebSocket for complex queries or if HTTP fails
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
    
    # HTTP Utility Methods
    
    async def get(self, endpoint: str) -> Dict[str, Any]:
        """Make GET request to backend endpoint"""
        try:
            response = await self.http_client.get(f"{self.config.backend_url}{endpoint}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise ConnectionError(f"GET request failed: {e}")
    
    async def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make POST request to backend endpoint"""
        try:
            response = await self.http_client.post(f"{self.config.backend_url}{endpoint}", json=data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise ConnectionError(f"POST request failed: {e}")
    
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
    
    def _is_cached(self, key: str, ttl_seconds: int = 30) -> bool:
        """Check if data is cached and still valid"""
        if key not in self._cache or key not in self._cache_ttl:
            return False
        return time.time() - self._cache_ttl[key] < ttl_seconds
    
    def _set_cache(self, key: str, value: Any) -> None:
        """Set cache with timestamp"""
        self._cache[key] = value
        self._cache_ttl[key] = time.time()
    
    def _clear_cache(self) -> None:
        """Clear expired cache entries"""
        current_time = time.time()
        expired_keys = [k for k, timestamp in self._cache_ttl.items() if current_time - timestamp > 60]
        for key in expired_keys:
            self._cache.pop(key, None)
            self._cache_ttl.pop(key, None)