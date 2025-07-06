"""
Debug CLI endpoint for testing Ollama integration directly
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/debug", tags=["Debug"])

class DebugQueryRequest(BaseModel):
    query: str
    model: Optional[str] = "mistral:7b-instruct"

class DebugQueryResponse(BaseModel):
    status: str
    message: str
    processing_time: float
    timestamp: str

@router.post("/ollama", response_model=DebugQueryResponse)
async def debug_ollama_query(request: DebugQueryRequest) -> DebugQueryResponse:
    """
    Direct Ollama test endpoint bypassing all other services
    """
    start_time = datetime.now()
    
    try:
        logger.info(f"🔧 Debug Ollama query: {request.query}")
        
        # Direct Ollama service import and test
        from ...services.ollama_ai_service import OllamaAIService
        
        # Create fresh service instance
        ollama = OllamaAIService(default_model=request.model)
        
        # Initialize with timeout
        init_success = await ollama.initialize()
        if not init_success:
            raise Exception("Ollama initialization failed")
        
        logger.info(f"✅ Ollama initialized with model: {ollama.default_model}")
        
        # Generate response with timeout
        response = await ollama.generate(
            prompt=request.query,
            max_tokens=100,  # Short response for testing
            temperature=0.1
        )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        if response:
            logger.info(f"✅ Debug query completed in {processing_time:.3f}s")
            return DebugQueryResponse(
                status="success",
                message=response,
                processing_time=processing_time,
                timestamp=datetime.now().isoformat()
            )
        else:
            raise Exception("Empty response from Ollama")
            
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds()
        error_message = f"Debug query failed: {str(e)}"
        logger.error(f"❌ {error_message}")
        
        return DebugQueryResponse(
            status="error", 
            message=error_message,
            processing_time=processing_time,
            timestamp=datetime.now().isoformat()
        )

@router.get("/status")
async def debug_status():
    """Simple debug status endpoint"""
    return {
        "status": "healthy",
        "service": "debug-cli",
        "timestamp": datetime.now().isoformat()
    }