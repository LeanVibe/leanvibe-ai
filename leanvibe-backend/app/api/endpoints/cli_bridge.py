"""
CLI Bridge API Endpoints

Provides WebSocket and REST endpoints specifically for CLI-to-iOS bridge functionality.
These endpoints enable the CLI to communicate with iOS devices through the backend.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from ...core.connection_manager import ConnectionManager
from ...models.event_models import EventData, EventType, EventPriority, NotificationChannel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cli", tags=["CLI Bridge"])

# CLI Bridge Models
class CLICommand(BaseModel):
    """CLI command model for bridge communication"""
    command: str
    args: Optional[List[str]] = []
    workspace_path: Optional[str] = None
    timestamp: Optional[str] = None

class CLIStatus(BaseModel):
    """CLI status response model"""
    status: str
    message: str
    active_sessions: int
    connected_ios_devices: int
    last_activity: Optional[str] = None

class CLIMonitoringData(BaseModel):
    """CLI monitoring data model"""
    memory_usage: float
    cpu_usage: float
    active_commands: int
    response_time_avg: float
    error_count: int

# Global CLI bridge state
cli_bridge_connections: Dict[str, WebSocket] = {}
ios_device_connections: Dict[str, Dict] = {}

@router.get("/status", response_model=CLIStatus)
async def get_cli_status():
    """Get CLI bridge status and connection information"""
    
    # Get connection statistics from the global objects
    try:
        from ...main import connection_manager, session_manager
        connection_info = connection_manager.get_connection_info()
        session_stats = session_manager.get_stats()
    except Exception:
        # Fallback to basic status if managers not available
        connection_info = {}
        session_stats = {"active_sessions": 0}
    
    # Count iOS devices (clients with 'ios' in their user agent or client type)
    ios_devices = 0
    for client_id, info in connection_info.items():
        if 'ios' in info.get('client_type', '').lower() or 'iphone' in info.get('user_agent', '').lower():
            ios_devices += 1
    
    return CLIStatus(
        status="active" if len(cli_bridge_connections) > 0 else "idle",
        message=f"CLI bridge operational with {len(cli_bridge_connections)} CLI connections",
        active_sessions=session_stats.get('active_sessions', 0),
        connected_ios_devices=ios_devices,
        last_activity=datetime.now().isoformat()
    )

@router.get("/monitor")
async def get_monitoring_data():
    """Get CLI monitoring and performance data"""
    
    try:
        from ...main import connection_manager, session_manager
        session_stats = session_manager.get_stats()
        connection_info = connection_manager.get_connection_info()
    except Exception:
        # Fallback to basic data if managers not available
        session_stats = {"active_sessions": 0}
        connection_info = {}
    
    # Calculate basic metrics
    total_connections = len(connection_info)
    active_sessions = session_stats.get('active_sessions', 0)
    
    monitoring_data = {
        "timestamp": datetime.now().isoformat(),
        "connections": {
            "total": total_connections,
            "cli_bridges": len(cli_bridge_connections),
            "ios_devices": len([c for c in connection_info.values() 
                             if 'ios' in c.get('client_type', '').lower()]),
            "active_sessions": active_sessions
        },
        "performance": {
            "average_response_time": session_stats.get('avg_response_time', 0.0),
            "total_requests": session_stats.get('total_requests', 0),
            "error_rate": session_stats.get('error_rate', 0.0)
        },
        "system": {
            "uptime_seconds": session_stats.get('uptime_seconds', 0),
            "memory_usage_mb": session_stats.get('memory_usage_mb', 0)
        }
    }
    
    return monitoring_data

@router.post("/command")
async def execute_cli_command(command: CLICommand):
    """Execute a CLI command and broadcast to connected iOS devices"""
    logger.info(f"Executing CLI command: {command.command}")
    
    try:
        # Create event for command execution
        command_event = EventData(
            event_id=f"cli_cmd_{int(asyncio.get_event_loop().time() * 1000)}",
            event_type=EventType.task_created,
            priority=EventPriority.medium,
            channel=NotificationChannel.tasks,
            timestamp=datetime.now(),
            source="cli_bridge",
            data={
                "command": command.command,
                "args": command.args,
                "workspace_path": command.workspace_path,
                "execution_time": datetime.now().isoformat()
            },
            metadata={"cli_bridge": True, "command_type": "cli"}
        )
        
        # Emit event to all connected devices
        try:
            from ...main import event_streaming_service, connection_manager
            await event_streaming_service.emit_event(command_event)
            
            # Broadcast to iOS devices via WebSocket
            command_message = {
                "type": "cli_command",
                "command": command.command,
                "args": command.args,
                "workspace_path": command.workspace_path,
                "timestamp": datetime.now().isoformat()
            }
            
            ios_notification_count = await connection_manager.broadcast_to_ios_devices(command_message)
        except Exception as import_error:
            logger.warning(f"Could not access streaming/connection services: {import_error}")
            ios_notification_count = 0
        
        return {
            "success": True,
            "command": command.command,
            "notified_devices": ios_notification_count,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error executing CLI command: {e}")
        raise HTTPException(status_code=500, detail=f"Command execution failed: {str(e)}")

@router.get("/devices")
async def list_connected_devices():
    """List all connected iOS devices and their status"""
    
    try:
        from ...main import connection_manager
        connection_info = connection_manager.get_connection_info()
    except Exception:
        # Fallback if connection manager not available
        connection_info = {}
    
    devices = []
    for client_id, info in connection_info.items():
        if 'ios' in info.get('client_type', '').lower() or 'iphone' in info.get('user_agent', '').lower():
            device_info = {
                "client_id": client_id,
                "connected_at": info.get('connected_at'),
                "last_seen": info.get('last_seen'),
                "device_type": info.get('client_type', 'ios'),
                "user_agent": info.get('user_agent', ''),
                "status": "connected"
            }
            devices.append(device_info)
    
    return {
        "devices": devices,
        "total_count": len(devices),
        "timestamp": datetime.now().isoformat()
    }

@router.post("/devices/{device_id}/message")
async def send_message_to_device(device_id: str, message: dict):
    """Send a direct message to a specific iOS device"""
    
    try:
        from ...main import connection_manager
        success = await connection_manager.send_to_client(device_id, message)
        
        if success:
            return {
                "success": True,
                "device_id": device_id,
                "message_sent": True,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=404, detail="Device not found or disconnected")
            
    except Exception as e:
        logger.error(f"Error sending message to device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Message delivery failed: {str(e)}")

@router.websocket("/bridge/{cli_id}")
async def cli_bridge_websocket(websocket: WebSocket, cli_id: str):
    """WebSocket endpoint specifically for CLI bridge connections"""
    await websocket.accept()
    cli_bridge_connections[cli_id] = websocket
    
    logger.info(f"CLI bridge connection established: {cli_id}")
    
    # Send initial connection confirmation
    await websocket.send_text(json.dumps({
        "type": "connection_established",
        "cli_id": cli_id,
        "timestamp": datetime.now().isoformat(),
        "message": "CLI bridge connection active"
    }))
    
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                message_type = message.get("type", "unknown")
                
                logger.info(f"CLI bridge message from {cli_id}: {message_type}")
                
                if message_type == "monitor_request":
                    # Handle monitoring data request
                    monitoring_data = await get_monitoring_data()
                    await websocket.send_text(json.dumps({
                        "type": "monitor_response",
                        "data": monitoring_data,
                        "timestamp": datetime.now().isoformat()
                    }))
                    
                elif message_type == "device_list_request":
                    # Handle device list request
                    devices_data = await list_connected_devices()
                    await websocket.send_text(json.dumps({
                        "type": "device_list_response",
                        "data": devices_data,
                        "timestamp": datetime.now().isoformat()
                    }))
                    
                elif message_type == "command_broadcast":
                    # Handle command broadcast to iOS devices
                    command_data = message.get("data", {})
                    
                    try:
                        from ...main import connection_manager
                        ios_count = await connection_manager.broadcast_to_ios_devices(command_data)
                    except Exception:
                        ios_count = 0
                    
                    await websocket.send_text(json.dumps({
                        "type": "broadcast_confirmation",
                        "devices_notified": ios_count,
                        "timestamp": datetime.now().isoformat()
                    }))
                
                elif message_type == "heartbeat":
                    # Handle CLI heartbeat
                    await websocket.send_text(json.dumps({
                        "type": "heartbeat_ack",
                        "cli_id": cli_id,
                        "timestamp": datetime.now().isoformat()
                    }))
                
                else:
                    logger.warning(f"Unknown message type from CLI {cli_id}: {message_type}")
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": f"Unknown message type: {message_type}",
                        "timestamp": datetime.now().isoformat()
                    }))
                    
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format",
                    "timestamp": datetime.now().isoformat()
                }))
            except Exception as e:
                logger.error(f"Error processing CLI bridge message: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"Processing error: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                }))
                
    except WebSocketDisconnect:
        if cli_id in cli_bridge_connections:
            del cli_bridge_connections[cli_id]
        logger.info(f"CLI bridge disconnected: {cli_id}")

@router.get("/bridge/status")
async def get_bridge_status():
    """Get CLI bridge connection status"""
    return {
        "active_bridges": len(cli_bridge_connections),
        "bridge_ids": list(cli_bridge_connections.keys()),
        "status": "active" if cli_bridge_connections else "no_connections",
        "timestamp": datetime.now().isoformat()
    }