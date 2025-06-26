from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import logging
import asyncio
import json
from .services.ai_service import AIService
from .core.connection_manager import ConnectionManager
from .agent.session_manager import SessionManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="LeenVibe L3 Agent", version="0.1.0")

# Configure CORS for iOS communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to local network
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
ai_service = AIService()
connection_manager = ConnectionManager()
session_manager = SessionManager()

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting LeenVibe backend with L3 Agent...")
    await ai_service.initialize()
    await session_manager.start()

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down LeenVibe backend...")
    await session_manager.stop()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    session_stats = session_manager.get_stats()
    return {
        "status": "healthy", 
        "service": "leenvibe-backend", 
        "version": "0.2.0",
        "ai_ready": ai_service.is_initialized,
        "agent_framework": "pydantic.ai",
        "sessions": session_stats
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "LeenVibe L3 Coding Agent", "version": "0.2.0", "framework": "pydantic.ai"}

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
    if hasattr(agent, 'get_enhanced_state_summary'):
        state = agent.get_enhanced_state_summary()
    else:
        state = agent.get_state_summary()
    
    return {"state": state, "client_id": client_id}

@app.get("/ast/project/{client_id}/analysis")
async def get_project_analysis(client_id: str):
    """Get AST-powered project analysis"""
    agent = await session_manager.get_session(client_id)
    if not agent or not hasattr(agent, '_analyze_project_tool'):
        return {"error": "Enhanced agent not available", "client_id": client_id}
    
    result = await agent._analyze_project_tool()
    return {"analysis": result, "client_id": client_id}

@app.get("/ast/symbols/{client_id}/{symbol_name}")
async def find_symbol_references(client_id: str, symbol_name: str):
    """Find references to a symbol"""
    agent = await session_manager.get_session(client_id)
    if not agent or not hasattr(agent, '_find_references_tool'):
        return {"error": "Enhanced agent not available", "client_id": client_id}
    
    result = await agent._find_references_tool(symbol_name)
    return {"references": result, "client_id": client_id}

@app.get("/ast/complexity/{client_id}")
async def get_complexity_analysis(client_id: str):
    """Get code complexity analysis"""
    agent = await session_manager.get_session(client_id)
    if not agent or not hasattr(agent, '_check_complexity_tool'):
        return {"error": "Enhanced agent not available", "client_id": client_id}
    
    result = await agent._check_complexity_tool()
    return {"complexity": result, "client_id": client_id}

@app.get("/graph/architecture/{client_id}")
async def get_architecture_patterns(client_id: str):
    """Detect architecture patterns in the project"""
    agent = await session_manager.get_session(client_id)
    if not agent or not hasattr(agent, '_detect_architecture_tool'):
        return {"error": "Enhanced agent not available", "client_id": client_id}
    
    result = await agent._detect_architecture_tool()
    return {"architecture": result, "client_id": client_id}

@app.get("/graph/circular-deps/{client_id}")
async def get_circular_dependencies(client_id: str):
    """Find circular dependencies in the project"""
    agent = await session_manager.get_session(client_id)
    if not agent or not hasattr(agent, '_find_circular_dependencies_tool'):
        return {"error": "Enhanced agent not available", "client_id": client_id}
    
    result = await agent._find_circular_dependencies_tool()
    return {"circular_dependencies": result, "client_id": client_id}

@app.get("/graph/coupling/{client_id}")
async def get_coupling_analysis(client_id: str):
    """Analyze coupling between components"""
    agent = await session_manager.get_session(client_id)
    if not agent or not hasattr(agent, '_analyze_coupling_tool'):
        return {"error": "Enhanced agent not available", "client_id": client_id}
    
    result = await agent._analyze_coupling_tool()
    return {"coupling": result, "client_id": client_id}

@app.get("/graph/hotspots/{client_id}")
async def get_code_hotspots(client_id: str):
    """Find code hotspots (critical, highly connected code)"""
    agent = await session_manager.get_session(client_id)
    if not agent or not hasattr(agent, '_find_hotspots_tool'):
        return {"error": "Enhanced agent not available", "client_id": client_id}
    
    result = await agent._find_hotspots_tool()
    return {"hotspots": result, "client_id": client_id}

@app.get("/graph/visualization/{client_id}")
async def get_graph_visualization(client_id: str):
    """Generate graph visualization data"""
    agent = await session_manager.get_session(client_id)
    if not agent or not hasattr(agent, '_visualize_graph_tool'):
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
    if not agent or not hasattr(agent, '_generate_diagram_tool'):
        return {"error": "Enhanced agent not available", "client_id": client_id}
    
    from app.models.visualization_models import DiagramType, DiagramTheme
    
    # Extract parameters from request
    diagram_type = DiagramType(request.get("diagram_type", "architecture_overview"))
    theme = DiagramTheme(request.get("theme", "light"))
    max_nodes = min(request.get("max_nodes", 50), 200)  # Limit max nodes
    
    result = await agent._generate_diagram_tool(diagram_type, theme, max_nodes)
    return {"diagram": result, "client_id": client_id}

@app.get("/visualization/{client_id}/diagram/{diagram_type}")
async def get_specific_diagram(client_id: str, diagram_type: str, theme: str = "light", max_nodes: int = 50):
    """Generate a specific type of diagram"""
    agent = await session_manager.get_session(client_id)
    if not agent or not hasattr(agent, '_generate_diagram_tool'):
        return {"error": "Enhanced agent not available", "client_id": client_id}
    
    from app.models.visualization_models import DiagramType, DiagramTheme
    
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
    """WebSocket endpoint for L3 agent communication"""
    await connection_manager.connect(websocket, client_id)
    logger.info(f"L3 Agent client {client_id} connected")
    
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                
                # Extract message content and workspace
                content = message.get("content", "")
                message_type = message.get("type", "message")
                workspace_path = message.get("workspace_path", ".")
                
                # Route to appropriate handler
                if message_type == "command" and content.startswith("/"):
                    # Handle slash commands through legacy AI service for compatibility
                    message["client_id"] = client_id
                    response = await ai_service.process_command(message)
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
                    "timestamp": asyncio.get_event_loop().time()
                }
                await websocket.send_text(json.dumps(error_response))
            except Exception as e:
                logger.error(f"Error processing message for {client_id}: {e}")
                error_response = {
                    "status": "error", 
                    "message": f"Processing error: {str(e)}",
                    "confidence": 0.0,
                    "timestamp": asyncio.get_event_loop().time()
                }
                await websocket.send_text(json.dumps(error_response))
                
    except WebSocketDisconnect:
        connection_manager.disconnect(client_id)
        logger.info(f"L3 Agent client {client_id} disconnected")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)