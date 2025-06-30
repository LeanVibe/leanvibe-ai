import asyncio
import json
import logging
from datetime import datetime

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .agent.session_manager import SessionManager
from .api.endpoints.code_completion import get_enhanced_agent
from .api.endpoints.code_completion import router as code_completion_router
from .api.models import CodeCompletionRequest
from .core.connection_manager import ConnectionManager
from .models.event_models import ClientPreferences, EventType
from .services.enhanced_ai_service import EnhancedAIService
from .services.event_streaming_service import event_streaming_service
from .services.reconnection_service import (
    client_heartbeat,
    reconnection_service,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="LeanVibe L3 Agent", version="0.2.0")

# Configure CORS for iOS communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to local network
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(code_completion_router)


# Code completion WebSocket handler
async def handle_code_completion_websocket(message: dict, client_id: str) -> dict:
    """
    Handle code completion requests through WebSocket

    Expected message format:
    {
        "type": "code_completion",
        "file_path": "/path/to/file.py",
        "cursor_position": 100,
        "intent": "suggest",
        "content": "optional file content",
        "language": "python"
    }
    """
    try:
        # Extract request data from WebSocket message
        request_data = {
            "file_path": message.get("file_path", ""),
            "cursor_position": message.get("cursor_position", 0),
            "intent": message.get("intent", "suggest"),
            "content": message.get("content"),
            "language": message.get("language"),
        }

        # Validate request using Pydantic model
        try:
            request = CodeCompletionRequest(**request_data)
        except Exception as e:
            return {
                "status": "error",
                "message": f"Invalid request format: {str(e)}",
                "confidence": 0.0,
                "timestamp": asyncio.get_event_loop().time(),
            }

        # Get Enhanced L3 Agent
        agent = await get_enhanced_agent()

        # Prepare agent request
        agent_request = {
            "file_path": request.file_path,
            "cursor_position": request.cursor_position,
        }

        # Add optional fields
        if request.content:
            agent_request["content"] = request.content
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
            return {
                "status": "error",
                "message": f"Unsupported intent: {request.intent}",
                "confidence": 0.0,
                "timestamp": asyncio.get_event_loop().time(),
            }

        # Parse agent response
        try:
            agent_response = json.loads(response_text)
        except json.JSONDecodeError:
            # Handle plain text responses
            if response_text.startswith("Error:"):
                return {
                    "status": "error",
                    "message": response_text,
                    "confidence": 0.0,
                    "timestamp": asyncio.get_event_loop().time(),
                }

            # Wrap plain text as success response
            agent_response = {
                "response": response_text,
                "confidence": 0.7,
                "requires_review": True,
                "follow_up_actions": [],
            }

        # Build WebSocket response
        ws_response = {
            "status": "success",
            "type": "code_completion_response",
            "intent": request.intent,
            "response": agent_response.get("response", ""),
            "confidence": agent_response.get("confidence", 0.7),
            "requires_review": agent_response.get("requires_review", True),
            "suggestions": agent_response.get("follow_up_actions", []),
            "client_id": client_id,
            "timestamp": asyncio.get_event_loop().time(),
        }

        # Add intent-specific fields
        if request.intent == "explain":
            ws_response["explanation"] = agent_response.get(
                "explanation", agent_response.get("response", "")
            )
        elif request.intent == "refactor":
            ws_response["refactoring_suggestions"] = agent_response.get(
                "refactoring_suggestions", agent_response.get("response", "")
            )
        elif request.intent == "debug":
            ws_response["debug_analysis"] = agent_response.get(
                "debug_analysis", agent_response.get("response", "")
            )
        elif request.intent == "optimize":
            ws_response["optimization_suggestions"] = agent_response.get(
                "optimization_suggestions", agent_response.get("response", "")
            )

        logger.info(
            f"Code completion {request.intent} request processed for client {client_id}"
        )
        return ws_response

    except Exception as e:
        logger.error(f"Error processing code completion WebSocket message: {e}")
        return {
            "status": "error",
            "message": f"Internal error: {str(e)}",
            "confidence": 0.0,
            "timestamp": asyncio.get_event_loop().time(),
        }


# Initialize services with enhanced AI and event streaming
ai_service = EnhancedAIService()
connection_manager = ConnectionManager()
session_manager = SessionManager()

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info(
        "Starting LeanVibe backend with L3 Agent, event streaming, and reconnection handling..."
    )
    await ai_service.initialize()
    await session_manager.start()
    await event_streaming_service.start()
    await reconnection_service.start()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down LeanVibe backend...")
    await session_manager.stop()
    await event_streaming_service.stop()
    await reconnection_service.stop()


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    session_stats = session_manager.get_stats()
    streaming_stats = event_streaming_service.get_stats()
    return {
        "status": "healthy",
        "service": "leanvibe-backend",
        "version": "0.2.0",
        "ai_ready": ai_service.is_initialized,
        "agent_framework": "pydantic.ai",
        "sessions": session_stats,
        "event_streaming": streaming_stats,
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "LeanVibe L3 Coding Agent",
        "version": "0.2.0",
        "framework": "pydantic.ai",
    }


# Event Streaming Endpoints


@app.get("/streaming/stats")
async def get_streaming_stats():
    """Get event streaming service statistics"""
    return event_streaming_service.get_stats()


@app.get("/streaming/clients")
async def get_streaming_clients():
    """Get information about connected streaming clients"""
    return event_streaming_service.get_client_info()


@app.get("/streaming/clients/{client_id}/preferences")
async def get_client_preferences(client_id: str):
    """Get notification preferences for a specific client"""
    client_info = event_streaming_service.get_client_info()
    if client_id not in client_info:
        raise HTTPException(status_code=404, detail="Client not found")
    return client_info[client_id]["preferences"]


@app.put("/streaming/clients/{client_id}/preferences")
async def update_client_preferences(client_id: str, preferences: ClientPreferences):
    """Update notification preferences for a specific client"""
    try:
        event_streaming_service.update_client_preferences(client_id, preferences)
        connection_manager.update_client_preferences(client_id, preferences)
        return {
            "success": True,
            "client_id": client_id,
            "preferences": preferences.dict(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to update preferences: {str(e)}"
        )


@app.post("/streaming/test-event")
async def emit_test_event(event_data: dict):
    """Emit a test event for debugging purposes"""
    from datetime import datetime

    from .models.event_models import (
        EventData,
        EventPriority,
        NotificationChannel,
    )

    try:
        test_event = EventData(
            event_id=f"test_{int(asyncio.get_event_loop().time() * 1000)}",
            event_type=EventType(event_data.get("event_type", "system_ready")),
            priority=EventPriority(event_data.get("priority", "medium")),
            channel=NotificationChannel(event_data.get("channel", "system")),
            timestamp=datetime.now(),
            source="test_endpoint",
            data=event_data.get("data", {}),
            metadata={"test": True},
        )

        await event_streaming_service.emit_event(test_event)
        return {"success": True, "event_id": test_event.event_id}
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to emit test event: {str(e)}"
        )


@app.get("/connections")
async def get_connections():
    """Get information about all WebSocket connections"""
    return connection_manager.get_connection_info()


# Reconnection Endpoints


@app.get("/reconnection/sessions")
async def get_reconnection_sessions():
    """Get information about all client reconnection sessions"""
    return reconnection_service.get_all_sessions_info()


@app.get("/reconnection/sessions/{client_id}")
async def get_client_session_info(client_id: str):
    """Get reconnection session information for a specific client"""
    session_info = reconnection_service.get_client_session_info(client_id)
    if session_info is None:
        raise HTTPException(status_code=404, detail="Client session not found")
    return session_info


@app.post("/reconnection/heartbeat/{client_id}")
async def client_heartbeat_endpoint(client_id: str):
    """Update client heartbeat timestamp"""
    client_heartbeat(client_id)
    return {
        "success": True,
        "client_id": client_id,
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/reconnection/simulate-disconnect/{client_id}")
async def simulate_client_disconnect(client_id: str):
    """Simulate client disconnection for testing purposes"""
    from .services.reconnection_service import client_disconnected

    client_disconnected(client_id)
    return {"success": True, "client_id": client_id, "simulated": True}


@app.get("/sessions")
async def list_sessions():
    """List all active agent sessions"""
    sessions = await session_manager.list_sessions()
    return {"sessions": sessions, "count": len(sessions)}


@app.delete("/sessions/{client_id}")
async def delete_session(client_id: str):
    """Delete a specific agent session"""
    success = await session_manager.delete_session(client_id)
    return {"success": success, "client_id": client_id}


@app.get("/sessions/{client_id}/state")
async def get_session_state(client_id: str):
    """Get the state of a specific session"""
    agent = await session_manager.get_session(client_id)
    if not agent:
        return {"error": "Session not found", "client_id": client_id}

    # Use enhanced state summary if available
    if hasattr(agent, "get_enhanced_state_summary"):
        state = agent.get_enhanced_state_summary()
    else:
        state = agent.get_state_summary()

    return {"state": state, "client_id": client_id}


@app.get("/ast/project/{client_id}/analysis")
async def get_project_analysis(client_id: str):
    """Get AST-powered project analysis"""
    agent = await session_manager.get_session(client_id)
    if not agent or not hasattr(agent, "_analyze_project_tool"):
        return {"error": "Enhanced agent not available", "client_id": client_id}

    result = await agent._analyze_project_tool()
    return {"analysis": result, "client_id": client_id}


@app.get("/ast/symbols/{client_id}/{symbol_name}")
async def find_symbol_references(client_id: str, symbol_name: str):
    """Find references to a symbol"""
    agent = await session_manager.get_session(client_id)
    if not agent or not hasattr(agent, "_find_references_tool"):
        return {"error": "Enhanced agent not available", "client_id": client_id}

    result = await agent._find_references_tool(symbol_name)
    return {"references": result, "client_id": client_id}


@app.get("/ast/complexity/{client_id}")
async def get_complexity_analysis(client_id: str):
    """Get code complexity analysis"""
    agent = await session_manager.get_session(client_id)
    if not agent or not hasattr(agent, "_check_complexity_tool"):
        return {"error": "Enhanced agent not available", "client_id": client_id}

    result = await agent._check_complexity_tool()
    return {"complexity": result, "client_id": client_id}


@app.get("/graph/architecture/{client_id}")
async def get_architecture_patterns(client_id: str):
    """Detect architecture patterns in the project"""
    agent = await session_manager.get_session(client_id)
    if not agent or not hasattr(agent, "_detect_architecture_tool"):
        return {"error": "Enhanced agent not available", "client_id": client_id}

    result = await agent._detect_architecture_tool()
    return {"architecture": result, "client_id": client_id}


@app.get("/graph/circular-deps/{client_id}")
async def get_circular_dependencies(client_id: str):
    """Find circular dependencies in the project"""
    agent = await session_manager.get_session(client_id)
    if not agent or not hasattr(agent, "_find_circular_dependencies_tool"):
        return {"error": "Enhanced agent not available", "client_id": client_id}

    result = await agent._find_circular_dependencies_tool()
    return {"circular_dependencies": result, "client_id": client_id}


@app.get("/graph/coupling/{client_id}")
async def get_coupling_analysis(client_id: str):
    """Analyze coupling between components"""
    agent = await session_manager.get_session(client_id)
    if not agent or not hasattr(agent, "_analyze_coupling_tool"):
        return {"error": "Enhanced agent not available", "client_id": client_id}

    result = await agent._analyze_coupling_tool()
    return {"coupling": result, "client_id": client_id}


@app.get("/graph/hotspots/{client_id}")
async def get_code_hotspots(client_id: str):
    """Find code hotspots (critical, highly connected code)"""
    agent = await session_manager.get_session(client_id)
    if not agent or not hasattr(agent, "_find_hotspots_tool"):
        return {"error": "Enhanced agent not available", "client_id": client_id}

    result = await agent._find_hotspots_tool()
    return {"hotspots": result, "client_id": client_id}


@app.get("/graph/visualization/{client_id}")
async def get_graph_visualization(client_id: str):
    """Generate graph visualization data"""
    agent = await session_manager.get_session(client_id)
    if not agent or not hasattr(agent, "_visualize_graph_tool"):
        return {"error": "Enhanced agent not available", "client_id": client_id}

    result = await agent._visualize_graph_tool()
    return {"visualization": result, "client_id": client_id}


@app.get("/visualization/types")
async def get_diagram_types():
    """Get available diagram types"""
    from app.services.visualization_service import visualization_service

    diagram_types = await visualization_service.get_diagram_types()
    return {"diagram_types": diagram_types}


@app.post("/visualization/{client_id}/generate")
async def generate_diagram(client_id: str, request: dict):
    """Generate interactive diagram"""
    agent = await session_manager.get_session(client_id)
    if not agent or not hasattr(agent, "_generate_diagram_tool"):
        return {"error": "Enhanced agent not available", "client_id": client_id}

    from app.models.visualization_models import DiagramTheme, DiagramType

    # Extract parameters from request
    diagram_type = DiagramType(request.get("diagram_type", "architecture_overview"))
    theme = DiagramTheme(request.get("theme", "light"))
    max_nodes = min(request.get("max_nodes", 50), 200)  # Limit max nodes

    result = await agent._generate_diagram_tool(diagram_type, theme, max_nodes)
    return {"diagram": result, "client_id": client_id}


@app.get("/visualization/{client_id}/diagram/{diagram_type}")
async def get_specific_diagram(
    client_id: str, diagram_type: str, theme: str = "light", max_nodes: int = 50
):
    """Generate a specific type of diagram"""
    agent = await session_manager.get_session(client_id)
    if not agent or not hasattr(agent, "_generate_diagram_tool"):
        return {"error": "Enhanced agent not available", "client_id": client_id}

    from app.models.visualization_models import DiagramTheme, DiagramType

    try:
        dtype = DiagramType(diagram_type)
        dtheme = DiagramTheme(theme)
        max_nodes = min(max_nodes, 200)  # Safety limit

        result = await agent._generate_diagram_tool(dtype, dtheme, max_nodes)
        return {"diagram": result, "client_id": client_id}
    except ValueError as e:
        return {"error": f"Invalid diagram type or theme: {e}", "client_id": client_id}


@app.get("/visualization/cache/stats")
async def get_visualization_cache_stats():
    """Get visualization service cache statistics"""
    from app.services.visualization_service import visualization_service

    stats = visualization_service.get_cache_stats()
    return {"cache_stats": stats}


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for L3 agent communication with reconnection support"""

    # Check for reconnection scenario
    is_reconnection = client_id in reconnection_service.client_sessions
    reconnection_data = None

    if is_reconnection:
        # Handle reconnection with state synchronization
        from .models.event_models import ConnectionState

        # Create temporary connection state for reconnection
        temp_preferences = reconnection_service.client_sessions[
            client_id
        ].preferences_snapshot
        if temp_preferences:
            from .models.event_models import ClientPreferences

            preferences = ClientPreferences(**temp_preferences)
        else:
            preferences = None

        temp_connection_state = ConnectionState(
            client_id=client_id,
            connected_at=datetime.now(),
            preferences=preferences
            or connection_manager._create_default_preferences(client_id, websocket),
            sequence_number=reconnection_service.client_sessions[
                client_id
            ].sequence_number,
            last_seen=datetime.now(),
        )

        reconnection_data = await reconnection_service.client_reconnected(
            client_id, temp_connection_state
        )
        logger.info(
            f"Client {client_id} reconnecting - {reconnection_data['missed_events_count']} missed events"
        )

        await connection_manager.connect(websocket, client_id, is_reconnection=True)

        # Send reconnection info to client
        await websocket.send_text(
            json.dumps(
                {
                    "type": "reconnection_sync",
                    "data": reconnection_data,
                    "timestamp": datetime.now().isoformat(),
                }
            )
        )

    else:
        # Handle new connection
        await connection_manager.connect(websocket, client_id)
        logger.info(f"L3 Agent client {client_id} connected (new session)")

    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)

                # Handle heartbeat messages
                if message.get("type") == "heartbeat":
                    client_heartbeat(client_id)
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "heartbeat_ack",
                                "timestamp": datetime.now().isoformat(),
                            }
                        )
                    )
                    continue

                # Extract message content and workspace
                content = message.get("content", "")
                message_type = message.get("type", "message")
                workspace_path = message.get("workspace_path", ".")

                # Route to appropriate handler
                if message_type == "command" and content.startswith("/"):
                    # Handle slash commands through legacy AI service for compatibility
                    message["client_id"] = client_id
                    response = await ai_service.process_command(message)
                elif message_type == "code_completion":
                    # Handle code completion requests from iOS
                    response = await handle_code_completion_websocket(
                        message, client_id
                    )
                else:
                    # Handle natural language through L3 agent
                    response = await session_manager.process_message(
                        client_id, content, workspace_path
                    )

                # Ensure response has the expected structure
                if "timestamp" not in response:
                    response["timestamp"] = asyncio.get_event_loop().time()

                await websocket.send_text(json.dumps(response, default=str))

            except json.JSONDecodeError:
                error_response = {
                    "status": "error",
                    "message": "Invalid JSON format",
                    "confidence": 0.0,
                    "timestamp": asyncio.get_event_loop().time(),
                }
                await websocket.send_text(json.dumps(error_response))
            except Exception as e:
                logger.error(f"Error processing message for {client_id}: {e}")
                error_response = {
                    "status": "error",
                    "message": f"Processing error: {str(e)}",
                    "confidence": 0.0,
                    "timestamp": asyncio.get_event_loop().time(),
                }
                await websocket.send_text(json.dumps(error_response))

    except WebSocketDisconnect:
        connection_manager.disconnect(client_id)
        logger.info(f"L3 Agent client {client_id} disconnected")


def main():
    """Main entry point for CLI usage"""
    import sys
    import asyncio
    
    if len(sys.argv) > 1 and sys.argv[1] == "query":
        # Handle CLI query
        if len(sys.argv) < 3:
            print("Usage: leanvibe query '<your question>'")
            sys.exit(1)
            
        query_text = " ".join(sys.argv[2:])
        
        # Run the CLI query handler
        result = asyncio.run(handle_cli_query(query_text))
        print(result)
    else:
        # Start the server
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)


async def handle_cli_query(query: str) -> str:
    """Handle CLI query and return formatted response"""
    try:
        # Initialize services
        await ai_service.initialize()
        await session_manager.start()
        
        # Create a temporary session for CLI
        cli_session_id = "cli_session"
        agent = await session_manager.get_or_create_session(cli_session_id, ".")
        
        # Process the query
        result = await agent.run(query)
        
        # Format the response for CLI output
        if result.get("status") == "success":
            response = result.get("response", "No response generated")
            confidence = result.get("confidence", 0.0)
            
            # Return formatted response (without box drawing for now)
            return f"✅ Response (Confidence: {confidence*100:.1f}%)\n\n{response}"
        else:
            error = result.get("error", "Unknown error")
            return f"❌ Error: {error}"
            
    except Exception as e:
        return f"❌ CLI Error: {str(e)}"
    finally:
        # Cleanup
        try:
            await session_manager.stop()
        except:
            pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
