"""
CLI Query API Endpoints

Provides REST endpoints specifically for CLI query processing using the L3CodingAgent.
This fixes the routing issue where CLI queries were timing out.
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from ...auth import api_key_dependency

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/cli", tags=["CLI Query"])

# CLI Query Models
class CLIQueryRequest(BaseModel):
    """CLI query request model"""
    query: str
    session_id: Optional[str] = "cli_default"
    workspace_path: Optional[str] = "."
    timeout: Optional[float] = 30.0

class CLIQueryResponse(BaseModel):
    """CLI query response model"""
    status: str
    message: str
    confidence: Optional[float] = None
    model: Optional[str] = None
    processing_time: Optional[float] = None
    timestamp: str
    session_info: Optional[dict] = None

@router.post("/query", response_model=CLIQueryResponse)
async def process_cli_query(request: CLIQueryRequest, authenticated: bool = Depends(api_key_dependency)) -> CLIQueryResponse:
    """
    Process a CLI query using the L3CodingAgent.
    
    This endpoint fixes the routing issue identified by Gemini CLI analysis.
    CLI queries now properly route to the L3CodingAgent instead of timing out.
    """
    start_time = datetime.now()
    
    try:
        logger.info(f"🔍 Processing CLI query: {request.query[:100]}...")
        
        # Import global session manager from main app
        from ...main import session_manager
        
        # Get or create agent session (session manager already initialized in main.py)
        agent = await session_manager.get_or_create_session(
            request.session_id, 
            request.workspace_path
        )
        
        # Process the query using L3CodingAgent
        result = await agent.run(request.query)
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        if result.get("status") == "success":
            # L3 agent returns 'message' field, not 'response'
            response_text = result.get("message", result.get("response", "No response generated"))
            confidence = result.get("confidence", 0.0)
            model_info = result.get("model", "L3-Agent")
            
            logger.info(f"✅ CLI query processed successfully in {processing_time:.3f}s")
            
            return CLIQueryResponse(
                status="success",
                message=response_text,
                confidence=confidence,
                model=model_info,
                processing_time=processing_time,
                timestamp=datetime.now().isoformat(),
                session_info=result.get("session_info", {})
            )
        else:
            error_message = result.get("message", "Unknown error")
            logger.warning(f"⚠️ CLI query failed: {error_message}")
            
            return CLIQueryResponse(
                status="error",
                message=error_message,
                processing_time=processing_time,
                timestamp=datetime.now().isoformat()
            )
            
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds()
        error_message = f"CLI query processing failed: {str(e)}"
        logger.error(f"❌ {error_message}")
        
        return CLIQueryResponse(
            status="error",
            message=error_message,
            processing_time=processing_time,
            timestamp=datetime.now().isoformat()
        )

@router.get("/status")
async def get_cli_query_status(authenticated: bool = Depends(api_key_dependency)):
    """Get CLI query service status"""
    try:
        # Import global session manager from main app
        from ...main import session_manager
            
        sessions = await session_manager.list_sessions()
        active_sessions = len([s for s in sessions if s.get("active", False)])
        
        return {
            "status": "healthy",
            "service": "cli-query",
            "active_sessions": active_sessions,
            "total_sessions": len(sessions),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ CLI status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))