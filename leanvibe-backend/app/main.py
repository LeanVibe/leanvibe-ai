import asyncio
import json
import logging
from datetime import datetime

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .agent.session_manager import SessionManager
from .api.endpoints.code_completion import get_enhanced_agent
from .api.endpoints.code_completion import router as code_completion_router
from .api.endpoints.tasks import router as tasks_router
from .api.endpoints.health_mlx import router as health_mlx_router
from .api.endpoints.cli_bridge import router as cli_bridge_router
from .api.endpoints.cli_query import router as cli_query_router
from .api.endpoints.debug_cli import router as debug_cli_router
from .api.endpoints.projects import router as projects_router
from .api.endpoints.ios_bridge import router as ios_bridge_router
from .api.endpoints.config import router as config_router
from .api.models import CodeCompletionRequest
from .core.connection_manager import ConnectionManager
from .models.event_models import ClientPreferences, EventType
from .services.enhanced_ai_service import EnhancedAIService
from .services.event_streaming_service import event_streaming_service
from .services.reconnection_service import (
    client_heartbeat,
    reconnection_service,
)
from .services.task_service import task_service
from .core.error_recovery import global_error_recovery

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app with comprehensive API documentation
app = FastAPI(
    title="LeanVibe L3 Coding Agent API",
    description="""
    ## LeanVibe Backend API
    
    **Advanced AI-powered coding assistant with real-time collaboration and iOS integration.**
    
    ### Key Features
    
    * **🤖 AI-Powered Code Assistance**: Qwen2.5-Coder-32B with Apple MLX on-device processing
    * **📱 iOS App Integration**: Real-time synchronization with iOS companion app
    * **📋 Task Management**: Comprehensive Kanban-style task management with agent automation
    * **📊 Project Analytics**: Dynamic metrics calculation and health scoring
    * **🔄 Real-time Updates**: WebSocket-based live collaboration and event streaming
    * **🛠️ CLI Integration**: Powerful command-line interface with git integration
    
    ### Agent-Developed Components
    
    This API includes sophisticated features developed by 5 specialized AI agents:
    
    - **ALPHA Agent**: iOS dashboard foundation and performance optimization
    - **BETA Agent**: Backend API enhancement and push notifications  
    - **DELTA Agent**: CLI enhancement and task management APIs
    - **GAMMA Agent**: Architecture visualization and user experience
    - **KAPPA Agent**: Voice interface and integration testing
    
    ### Architecture
    
    - **Backend**: FastAPI + Python 3.11+ with MLX AI processing
    - **Real-time Communication**: WebSocket connections with automatic reconnection
    - **Data Storage**: In-memory with persistence hooks for production scaling
    - **AI Models**: Local Apple MLX deployment for complete privacy
    
    ### Getting Started
    
    1. **Health Check**: Start with `/health` to verify backend status
    2. **Project Management**: Use `/api/projects/` endpoints for project operations
    3. **Task Management**: Use `/api/tasks/` endpoints for Kanban board operations  
    4. **Real-time Events**: Connect to WebSocket at `/ws/{client_id}` for live updates
    5. **iOS Integration**: Use `/api/ios/` endpoints for mobile app synchronization
    
    ### Authentication
    
    Currently operates in development mode with no authentication required.
    Production deployment will include API key authentication.
    
    ### Rate Limiting
    
    - Standard endpoints: 100 requests/minute per client
    - AI processing: 10 requests/minute per client
    - WebSocket connections: 1 per client_id
    
    ### Support
    
    - **Repository**: [LeanVibe GitHub](https://github.com/leanvibe-ai)
    - **Documentation**: Comprehensive guides in `/docs` endpoints
    - **Issues**: Report bugs via GitHub Issues
    """,
    version="0.2.0",
    contact={
        "name": "LeanVibe Development Team",
        "url": "https://github.com/leanvibe-ai/leanvibe-backend",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_tags=[
        {
            "name": "health",
            "description": "Health check and system status endpoints. Use these to verify backend availability and AI model status.",
        },
        {
            "name": "projects", 
            "description": "Project management endpoints developed by agents. Manage projects, analyze codebases, and track metrics.",
        },
        {
            "name": "tasks",
            "description": "Task management and Kanban board endpoints. Create, update, and organize development tasks with AI assistance.",
        },
        {
            "name": "ai",
            "description": "AI-powered code assistance endpoints. Query the Qwen2.5-Coder model for code analysis and suggestions.",
        },
        {
            "name": "websocket",
            "description": "Real-time WebSocket endpoints for live collaboration and event streaming.",
        },
        {
            "name": "cli-bridge",
            "description": "CLI integration endpoints for command-line tool communication and git workflow integration.",
        },
        {
            "name": "ios",
            "description": "iOS app integration endpoints for mobile companion app synchronization and notifications.",
        },
        {
            "name": "monitoring",
            "description": "Performance monitoring and analytics endpoints for system health and usage metrics.",
        },
        {
            "name": "configuration", 
            "description": "Dynamic configuration endpoints for iOS app. Provides theme settings, feature flags, and app configuration to eliminate hardcoded values.",
        }
    ],
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS for iOS communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:*",
        "http://127.0.0.1:*", 
        "http://192.168.*",
        "http://10.*",
        "http://172.16.*",
        "http://172.17.*",
        "http://172.18.*",
        "http://172.19.*",
        "http://172.20.*",
        "http://172.21.*",
        "http://172.22.*",
        "http://172.23.*",
        "http://172.24.*",
        "http://172.25.*",
        "http://172.26.*",
        "http://172.27.*",
        "http://172.28.*",
        "http://172.29.*",
        "http://172.30.*",
        "http://172.31.*",
    ],  # Restrict to localhost and local network ranges
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(code_completion_router)
app.include_router(tasks_router)
app.include_router(health_mlx_router)
app.include_router(cli_bridge_router)
app.include_router(cli_query_router)  # New CLI query endpoint for proper routing
app.include_router(debug_cli_router)  # Debug endpoint for direct Ollama testing
app.include_router(projects_router)
app.include_router(ios_bridge_router)
app.include_router(config_router)  # Configuration API for iOS app integration


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
    await task_service.initialize()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down LeanVibe backend...")
    await session_manager.stop()
    await event_streaming_service.stop()
    await reconnection_service.stop()


@app.get("/health")
async def health_check():
    """Health check endpoint with comprehensive LLM metrics and error recovery status"""
    session_stats = session_manager.get_stats()
    streaming_stats = event_streaming_service.get_stats()
    
    # Get LLM metrics from production model service
    llm_metrics = None
    if (ai_service.is_initialized and 
        hasattr(ai_service, 'mlx_service') and 
        ai_service.mlx_service.production_service):
        try:
            production_health = ai_service.mlx_service.production_service.get_health_status()
            llm_metrics = production_health.get("llm_metrics")
        except Exception as e:
            logger.warning(f"Failed to get LLM metrics: {e}")
            llm_metrics = {
                "error": "Failed to retrieve LLM metrics",
                "message": str(e)
            }
    
    # Get error recovery system status
    error_recovery_status = global_error_recovery.get_health_status()
    user_friendly_status = global_error_recovery.get_user_friendly_status()
    
    response = {
        "status": "healthy",
        "service": "leanvibe-backend",
        "version": "0.2.0",
        "ai_ready": ai_service.is_initialized,
        "agent_framework": "pydantic.ai",
        "sessions": session_stats,
        "event_streaming": streaming_stats,
        "error_recovery": error_recovery_status,
        "system_status": user_friendly_status,
    }
    
    # Add LLM metrics if available
    if llm_metrics:
        response["llm_metrics"] = llm_metrics
    
    return response


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
    # Auto-create session if needed for iOS clients
    workspace_path = "."
    agent = await session_manager.get_or_create_session(client_id, workspace_path)
    if not agent or not hasattr(agent, "_detect_architecture_tool"):
        return {"error": "Enhanced agent not available", "client_id": client_id}

    result = await agent._detect_architecture_tool()
    return {"architecture": result, "client_id": client_id}


@app.get("/graph/circular-deps/{client_id}")
async def get_circular_dependencies(client_id: str):
    """Find circular dependencies in the project"""
    # Auto-create session if needed for iOS clients
    workspace_path = "."
    agent = await session_manager.get_or_create_session(client_id, workspace_path)
    if not agent or not hasattr(agent, "_find_circular_dependencies_tool"):
        return {"error": "Enhanced agent not available", "client_id": client_id}

    result = await agent._find_circular_dependencies_tool()
    return {"circular_dependencies": result, "client_id": client_id}


@app.get("/graph/coupling/{client_id}")
async def get_coupling_analysis(client_id: str):
    """Analyze coupling between components"""
    # Auto-create session if needed for iOS clients
    workspace_path = "."
    agent = await session_manager.get_or_create_session(client_id, workspace_path)
    if not agent or not hasattr(agent, "_analyze_coupling_tool"):
        return {"error": "Enhanced agent not available", "client_id": client_id}

    result = await agent._analyze_coupling_tool()
    return {"coupling": result, "client_id": client_id}


@app.get("/graph/hotspots/{client_id}")
async def get_code_hotspots(client_id: str):
    """Find code hotspots (critical, highly connected code)"""
    # Auto-create session if needed for iOS clients
    workspace_path = "."
    agent = await session_manager.get_or_create_session(client_id, workspace_path)
    if not agent or not hasattr(agent, "_find_hotspots_tool"):
        return {"error": "Enhanced agent not available", "client_id": client_id}

    result = await agent._find_hotspots_tool()
    return {"hotspots": result, "client_id": client_id}


@app.get("/graph/visualization/{client_id}")
async def get_graph_visualization(client_id: str):
    """Generate graph visualization data"""
    # Auto-create session if needed for iOS clients
    workspace_path = "."
    agent = await session_manager.get_or_create_session(client_id, workspace_path)
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
                
                # Handle error through recovery system
                recovery_result = await global_error_recovery.handle_error(
                    error_type="websocket_connection",
                    error=e,
                    context={"client_id": client_id, "message_type": message.get("type", "unknown")},
                    component="websocket_handler"
                )
                
                error_response = {
                    "status": "error",
                    "message": recovery_result["user_message"],
                    "confidence": 0.0,
                    "timestamp": asyncio.get_event_loop().time(),
                    "recovery_attempted": recovery_result["success"],
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
            logger.info("Usage: leanvibe query '<your question>'")
            sys.exit(1)
            
        query_text = " ".join(sys.argv[2:])
        
        # Run the CLI query handler
        result = asyncio.run(handle_cli_query(query_text))
        logger.info(f"CLI Query Result: {result}")
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
            # L3 agent returns 'message' field, not 'response'
            response = result.get("message", result.get("response", "No response generated"))
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
        except Exception as e:
            logger.warning(f"Error during session manager cleanup: {e}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
