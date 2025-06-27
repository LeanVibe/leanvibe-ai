from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel


class WebSocketMessage(BaseModel):
    """Schema for WebSocket messages"""

    type: str  # "command", "message", "response"
    content: str
    client_id: Optional[str] = None
    timestamp: Optional[datetime] = None


class AgentResponse(BaseModel):
    """Schema for agent responses"""

    status: str  # "success", "error"
    type: Optional[str] = None
    message: str
    data: Optional[Dict[str, Any]] = None
    processing_time: Optional[float] = None
    timestamp: Optional[datetime] = None


class ConnectionInfo(BaseModel):
    """Schema for connection information"""

    client_id: str
    connected_at: datetime
    user_agent: Optional[str] = None
    last_activity: Optional[datetime] = None
