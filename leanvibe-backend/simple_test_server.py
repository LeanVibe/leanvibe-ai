#!/usr/bin/env python3
"""
Simple test server for iOS integration testing
"""

import asyncio
import sys
import os
sys.path.insert(0, os.getcwd())

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from app.agent.l3_coding_agent import L3CodingAgent, AgentDependencies
from app.core.error_recovery import global_error_recovery

app = FastAPI(title="LeanVibe Test Server", version="1.0.0")

# Enable CORS for iOS app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global agent instance
global_agent = None

class QueryRequest(BaseModel):
    message: str
    session_id: str = "default"

class QueryResponse(BaseModel):
    status: str
    message: str
    response_time: float
    confidence: float = 0.8

@app.on_event("startup")
async def startup_event():
    """Initialize the L3 agent on startup"""
    global global_agent
    print("🚀 Starting LeanVibe Test Server...")
    print("🤖 Initializing L3 Coding Agent...")
    
    dependencies = AgentDependencies(
        workspace_path=".",
        client_id="test_server",
        session_data={}
    )
    
    global_agent = L3CodingAgent(dependencies)
    success = await global_agent.initialize()
    
    if success:
        print("✅ L3 Coding Agent initialized successfully")
    else:
        print("❌ Failed to initialize L3 Coding Agent")
        raise RuntimeError("Agent initialization failed")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "leanvibe-test-server",
        "version": "1.0.0",
        "ai_ready": global_agent is not None,
        "agent_framework": "L3CodingAgent"
    }

@app.post("/api/v1/ai/chat", response_model=QueryResponse)
async def chat_with_agent(request: QueryRequest):
    """Process chat request with L3 agent"""
    if global_agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    import time
    start_time = time.time()
    
    try:
        # Process query with L3 agent
        response = await global_agent._process_user_input(request.message)
        end_time = time.time()
        
        if response and len(response) > 0:
            return QueryResponse(
                status="success",
                message=response,
                response_time=end_time - start_time,
                confidence=0.8
            )
        else:
            return QueryResponse(
                status="error",
                message="No response generated",
                response_time=end_time - start_time,
                confidence=0.0
            )
    
    except Exception as e:
        end_time = time.time()
        
        # Handle error through recovery system
        recovery_result = await global_error_recovery.handle_error(
            error_type="query_timeout",
            error=e,
            context={"message": request.message[:100], "session_id": request.session_id},
            component="test_server"
        )
        
        return QueryResponse(
            status="error",
            message=recovery_result["user_message"],
            response_time=end_time - start_time,
            confidence=0.0
        )

@app.get("/api/v1/sessions")
async def get_sessions():
    """Get active sessions"""
    return {
        "sessions": [
            {
                "session_id": "test_server",
                "status": "active",
                "total_requests": 0,
                "last_activity": "2025-07-10T10:00:00Z"
            }
        ]
    }

if __name__ == "__main__":
    print("🌟 LeanVibe Test Server for iOS Integration")
    print("🔗 Starting server at http://localhost:8000")
    print("📱 iOS app can connect to this server for testing")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000, 
        log_level="info",
        access_log=True
    )