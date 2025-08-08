"""
Example endpoint demonstrating contract-first validation integration
"""

from fastapi import APIRouter, Depends
from app.contracts.models import HealthResponse
from app.contracts.decorators import validate_response
from app.auth.api_key_auth import api_key_dependency

router = APIRouter(prefix="/api/example", tags=["example"])


@router.get("/validated-health")
@validate_response(HealthResponse)
async def validated_health_check(authenticated: bool = Depends(api_key_dependency)):
    """
    Example endpoint showing contract validation in action.
    
    This endpoint demonstrates:
    1. Response validation against generated Pydantic models
    2. Automatic error handling for contract violations
    3. Type safety through contract-first development
    """
    return {
        "status": "healthy",
        "service": "leanvibe-backend",
        "version": "0.2.0",
        "ai_ready": True,
        "agent_framework": "pydantic.ai",
        "sessions": {"active": 0, "total": 0},
        "event_streaming": {"connected_clients": 0},
        "error_recovery": {"active": False},
        "system_status": {"uptime": "1h 30m"},
        "llm_metrics": {"inference_time": 150.5}
    }