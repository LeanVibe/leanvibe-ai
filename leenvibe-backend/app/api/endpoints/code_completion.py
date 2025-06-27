"""
Phase 2.4.2: Code Completion Endpoint

REST endpoint that connects iOS app to Enhanced L3 Agent MLX tools.
Provides AI-powered code suggestions, explanations, refactoring, debugging, and optimization.
"""

import asyncio
import json
import logging
import time
from typing import Union

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from ...agent.enhanced_l3_agent import EnhancedL3CodingAgent, AgentDependencies
from ..models import (
    CodeCompletionRequest, 
    CodeCompletionResponse, 
    CodeCompletionErrorResponse,
    ContextUsed
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api", tags=["code-completion"])

# Global Enhanced L3 Agent instance
enhanced_agent: EnhancedL3CodingAgent = None


async def get_enhanced_agent() -> EnhancedL3CodingAgent:
    """Get or create Enhanced L3 Agent instance"""
    global enhanced_agent
    
    if enhanced_agent is None:
        logger.info("Initializing Enhanced L3 Agent for code completion endpoint")
        
        # Create agent dependencies
        deps = AgentDependencies(
            workspace_path=".",  # Current working directory
            client_id="code-completion-endpoint",
            session_data={}
        )
        
        # Create and initialize agent
        enhanced_agent = EnhancedL3CodingAgent(deps)
        success = await enhanced_agent.initialize()
        
        if not success:
            logger.error("Failed to initialize Enhanced L3 Agent")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to initialize AI agent"
            )
        
        logger.info("Enhanced L3 Agent initialized successfully")
    
    return enhanced_agent


def parse_agent_response(response_text: str, intent: str) -> dict:
    """Parse agent response text to structured format"""
    try:
        # Try to parse as JSON first
        return json.loads(response_text)
    except json.JSONDecodeError:
        # If not JSON, check if it's an error message
        if response_text.startswith("Error:"):
            raise ValueError(response_text)
        
        # For production agents, invalid JSON indicates a critical failure
        # Only allow non-JSON responses in development/testing scenarios
        if response_text.strip() and not response_text.startswith("{"):
            # If it looks like plain text, treat as parsing error for robustness
            raise ValueError(f"Agent returned invalid JSON: {response_text[:100]}")
        
        # Otherwise, wrap plain text response (fallback for edge cases)
        return {
            "status": "success",
            "response": response_text,
            "confidence": 0.7,  # Default confidence for plain text responses
            "requires_review": True,
            "suggestions": [],
            "context_used": {}
        }


def create_context_used(agent_response: dict, request: CodeCompletionRequest) -> ContextUsed:
    """Create ContextUsed object from agent response"""
    context_data = agent_response.get("context_used", {})
    
    return ContextUsed(
        language=context_data.get("language_detected", request.language or "unknown"),
        symbols_found=context_data.get("symbols_found", 0),
        has_context=context_data.get("has_symbol_context", False),
        file_path=context_data.get("file_path", request.file_path),
        has_symbol_context=context_data.get("has_symbol_context", False),
        language_detected=context_data.get("language_detected", request.language or "unknown")
    )


@router.post(
    "/code-completion",
    response_model=Union[CodeCompletionResponse, CodeCompletionErrorResponse],
    summary="Generate AI-powered code completion",
    description="Generate code suggestions, explanations, refactoring advice, debugging help, or optimization recommendations using AI"
)
async def code_completion(
    request: CodeCompletionRequest
) -> Union[CodeCompletionResponse, CodeCompletionErrorResponse]:
    """
    Generate AI-powered code completion based on file context and intent.
    
    Supports 5 types of completion:
    - suggest: Code suggestions and improvements
    - explain: Code explanation and analysis
    - refactor: Refactoring recommendations
    - debug: Debugging analysis and tips
    - optimize: Performance optimization suggestions
    """
    start_time = time.time()
    
    try:
        logger.info(f"Processing {request.intent} request for {request.file_path}:{request.cursor_position}")
        
        # Get Enhanced L3 Agent
        agent = await get_enhanced_agent()
        
        # Prepare agent request
        agent_request = {
            "file_path": request.file_path,
            "cursor_position": request.cursor_position
        }
        
        # Add content to agent request if provided
        if request.content:
            agent_request["content"] = request.content
        
        # Add language if provided
        if request.language:
            agent_request["language"] = request.language
        
        agent_request_json = json.dumps(agent_request)
        
        # Call appropriate MLX tool based on intent
        if request.intent == "suggest":
            response_text = await agent._mlx_suggest_code_tool(agent_request_json)
        elif request.intent == "explain":
            response_text = await agent._mlx_explain_code_tool(agent_request_json)
        elif request.intent == "refactor":
            response_text = await agent._mlx_refactor_code_tool(agent_request_json)
        elif request.intent == "debug":
            response_text = await agent._mlx_debug_code_tool(agent_request_json)
        elif request.intent == "optimize":
            response_text = await agent._mlx_optimize_code_tool(agent_request_json)
        else:
            # This should not happen due to Pydantic validation, but just in case
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported intent: {request.intent}"
            )
        
        # Parse agent response
        try:
            agent_response = parse_agent_response(response_text, request.intent)
        except ValueError as e:
            # Agent returned an error
            processing_time = (time.time() - start_time) * 1000
            error_msg = str(e)
            
            # Distinguish between agent logic errors (400) and parsing errors (500)
            if "invalid JSON" in error_msg or "parse" in error_msg.lower():
                # Agent malfunction - internal server error
                logger.error(f"Agent JSON parsing error for {request.intent} request: {e}")
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={
                        "status": "error",
                        "error": error_msg,
                        "error_code": "AGENT_PARSE_ERROR",
                        "processing_time_ms": processing_time
                    }
                )
            else:
                # Agent logic error - bad request
                logger.error(f"Agent logic error for {request.intent} request: {e}")
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "status": "error",
                        "error": error_msg,
                        "error_code": "AGENT_ERROR", 
                        "processing_time_ms": processing_time
                    }
                )
        
        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000
        
        # Create response based on intent
        context_used = create_context_used(agent_response, request)
        
        # Build response with intent-specific fields
        response_data = {
            "status": "success",
            "intent": request.intent,
            "response": agent_response.get("response", ""),
            "confidence": agent_response.get("confidence", 0.7),
            "requires_review": agent_response.get("requires_review", True),
            "suggestions": agent_response.get("suggestions", agent_response.get("follow_up_actions", [])),
            "context_used": context_used,
            "processing_time_ms": processing_time
        }
        
        # Add intent-specific fields
        if request.intent == "explain":
            response_data["explanation"] = agent_response.get("explanation", agent_response.get("response", ""))
        elif request.intent == "refactor":
            response_data["refactoring_suggestions"] = agent_response.get("refactoring_suggestions", agent_response.get("response", ""))
        elif request.intent == "debug":
            response_data["debug_analysis"] = agent_response.get("debug_analysis", agent_response.get("response", ""))
        elif request.intent == "optimize":
            response_data["optimization_suggestions"] = agent_response.get("optimization_suggestions", agent_response.get("response", ""))
        
        logger.info(f"Completed {request.intent} request in {processing_time:.1f}ms with confidence {response_data['confidence']:.2f}")
        
        return CodeCompletionResponse(**response_data)
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Handle unexpected errors
        processing_time = (time.time() - start_time) * 1000
        logger.error(f"Unexpected error in code completion endpoint: {e}", exc_info=True)
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "error": f"Internal server error: {str(e)}",
                "error_code": "INTERNAL_ERROR",
                "processing_time_ms": processing_time
            }
        )