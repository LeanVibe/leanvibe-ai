"""
Graph Analysis API Endpoints

Provides REST API endpoints for Neo4j graph database operations,
code relationship analysis, and architectural insights.
"""

import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, Query, Path
from pydantic import BaseModel, Field

from app.services.code_graph_service import CodeGraphService, create_code_graph_service
from app.services.ast_graph_service import ASTGraphService, create_ast_graph_service
from app.agent.session_manager import SessionManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/graph", tags=["graph-analysis"])

# Response models
class GraphHealthResponse(BaseModel):
    """Graph database health status response"""
    status: str = Field(..., description="Connection status")
    connected: bool = Field(..., description="Whether Neo4j is connected")
    uri: str = Field(..., description="Neo4j connection URI")
    schema_initialized: bool = Field(default=False, description="Whether schema is initialized")
    performance: Optional[Dict[str, Any]] = Field(default=None, description="Performance metrics")
    statistics: Optional[Dict[str, Any]] = Field(default=None, description="Database statistics")
    error: Optional[str] = Field(default=None, description="Error message if any")

class ArchitectureOverviewResponse(BaseModel):
    """Architecture overview analysis response"""
    client_id: str = Field(..., description="Client session ID")
    project_id: Optional[str] = Field(default=None, description="Project identifier")
    node_statistics: Dict[str, int] = Field(default_factory=dict, description="Node counts by type")
    relationship_statistics: Dict[str, int] = Field(default_factory=dict, description="Relationship counts")
    hotspots: List[Dict[str, Any]] = Field(default_factory=list, description="Most connected code entities")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Graph metrics")
    error: Optional[str] = Field(default=None, description="Error message if any")

class DependencyAnalysisResponse(BaseModel):
    """Dependency analysis response"""
    client_id: str = Field(..., description="Client session ID")
    node_id: str = Field(..., description="Target node ID")
    dependencies: List[Dict[str, Any]] = Field(default_factory=list, description="Dependencies")
    dependents: List[Dict[str, Any]] = Field(default_factory=list, description="Dependents")
    error: Optional[str] = Field(default=None, description="Error message if any")

class CircularDependencyResponse(BaseModel):
    """Circular dependency detection response"""
    client_id: str = Field(..., description="Client session ID")
    project_id: Optional[str] = Field(default=None, description="Project identifier")
    circular_dependencies: List[Dict[str, Any]] = Field(default_factory=list, description="Detected cycles")
    summary: Dict[str, Any] = Field(default_factory=dict, description="Analysis summary")
    error: Optional[str] = Field(default=None, description="Error message if any")

class ComplexityAnalysisResponse(BaseModel):
    """Code complexity analysis response"""
    client_id: str = Field(..., description="Client session ID") 
    project_id: Optional[str] = Field(default=None, description="Project identifier")
    complex_functions: List[Dict[str, Any]] = Field(default_factory=list, description="Most complex functions")
    complex_files: List[Dict[str, Any]] = Field(default_factory=list, description="Most complex files")
    summary: Dict[str, Any] = Field(default_factory=dict, description="Complexity summary")
    error: Optional[str] = Field(default=None, description="Error message if any")

class ProjectAnalysisResponse(BaseModel):
    """Project analysis response"""
    client_id: str = Field(..., description="Client session ID")
    project_path: str = Field(..., description="Analyzed project path")
    analysis_stats: Dict[str, Any] = Field(default_factory=dict, description="Analysis statistics")
    success: bool = Field(..., description="Whether analysis succeeded")
    error: Optional[str] = Field(default=None, description="Error message if any")

# Request models
class ProjectAnalysisRequest(BaseModel):
    """Request to analyze a project"""
    project_path: str = Field(..., description="Path to the project to analyze")
    project_id: Optional[str] = Field(default=None, description="Optional project identifier")

# Dependency injection
def get_graph_service() -> CodeGraphService:
    """Get CodeGraphService instance"""
    return create_code_graph_service()

def get_ast_graph_service(graph_service: CodeGraphService = Depends(get_graph_service)) -> ASTGraphService:
    """Get ASTGraphService instance"""
    return create_ast_graph_service(graph_service)

def get_session_manager() -> SessionManager:
    """Get SessionManager instance"""
    # This should be injected from the application context in a real app
    return SessionManager()

# Health and Status Endpoints
@router.get("/health", response_model=GraphHealthResponse)
async def get_graph_health(
    graph_service: CodeGraphService = Depends(get_graph_service)
) -> GraphHealthResponse:
    """Get Neo4j graph database health status"""
    try:
        # Attempt connection if not connected
        if not graph_service.is_connected():
            await graph_service.connect()
        
        # Get detailed health status
        status_data = await graph_service.get_health_status()
        
        return GraphHealthResponse(**status_data)
        
    except Exception as e:
        logger.error(f"Failed to get graph health status: {e}")
        return GraphHealthResponse(
            status="error",
            connected=False,
            uri=graph_service.uri,
            error=str(e)
        )

@router.post("/connect")
async def connect_graph_database(
    graph_service: CodeGraphService = Depends(get_graph_service)
) -> Dict[str, Any]:
    """Manually trigger graph database connection"""
    try:
        success = await graph_service.connect()
        
        if success:
            return {
                "success": True,
                "message": "Successfully connected to Neo4j",
                "uri": graph_service.uri
            }
        else:
            return {
                "success": False,
                "message": "Failed to connect to Neo4j",
                "uri": graph_service.uri
            }
            
    except Exception as e:
        logger.error(f"Error connecting to graph database: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Analysis Endpoints
@router.get("/architecture/{client_id}", response_model=ArchitectureOverviewResponse)
async def get_architecture_overview(
    client_id: str = Path(..., description="Client session ID"),
    project_id: Optional[str] = Query(default=None, description="Optional project filter"),
    graph_service: CodeGraphService = Depends(get_graph_service)
) -> ArchitectureOverviewResponse:
    """Get architectural overview of the codebase"""
    try:
        # Ensure connection
        if not graph_service.is_connected():
            await graph_service.connect()
        
        # Get architecture overview
        overview = await graph_service.get_architecture_overview(project_id)
        
        return ArchitectureOverviewResponse(
            client_id=client_id,
            project_id=project_id,
            **overview
        )
        
    except Exception as e:
        logger.error(f"Failed to get architecture overview for {client_id}: {e}")
        return ArchitectureOverviewResponse(
            client_id=client_id,
            project_id=project_id,
            error=str(e)
        )

@router.get("/dependencies/{client_id}/{node_id}", response_model=DependencyAnalysisResponse)
async def get_dependency_analysis(
    client_id: str = Path(..., description="Client session ID"),
    node_id: str = Path(..., description="Node ID to analyze"),
    depth: int = Query(default=2, ge=1, le=5, description="Analysis depth"),
    graph_service: CodeGraphService = Depends(get_graph_service)
) -> DependencyAnalysisResponse:
    """Get dependency analysis for a specific code entity"""
    try:
        # Ensure connection
        if not graph_service.is_connected():
            await graph_service.connect()
        
        # Get dependencies and dependents
        dependencies = await graph_service.get_dependencies(node_id, depth)
        dependents = await graph_service.get_dependents(node_id, depth)
        
        return DependencyAnalysisResponse(
            client_id=client_id,
            node_id=node_id,
            dependencies=dependencies,
            dependents=dependents
        )
        
    except Exception as e:
        logger.error(f"Failed to get dependency analysis for {node_id}: {e}")
        return DependencyAnalysisResponse(
            client_id=client_id,
            node_id=node_id,
            error=str(e)
        )

@router.get("/circular-deps/{client_id}", response_model=CircularDependencyResponse)
async def get_circular_dependencies(
    client_id: str = Path(..., description="Client session ID"),
    project_id: Optional[str] = Query(default=None, description="Optional project filter"),
    max_depth: int = Query(default=10, ge=3, le=20, description="Maximum cycle depth"),
    graph_service: CodeGraphService = Depends(get_graph_service)
) -> CircularDependencyResponse:
    """Detect circular dependencies in the codebase"""
    try:
        # Ensure connection
        if not graph_service.is_connected():
            await graph_service.connect()
        
        # Find circular dependencies
        cycles = await graph_service.find_circular_dependencies(project_id, max_depth)
        
        # Calculate summary statistics
        summary = {
            "total_cycles": len(cycles),
            "high_severity_cycles": len([c for c in cycles if c.get('severity') == 'high']),
            "medium_severity_cycles": len([c for c in cycles if c.get('severity') == 'medium']),
            "low_severity_cycles": len([c for c in cycles if c.get('severity') == 'low']),
            "max_cycle_length": max((c.get('length', 0) for c in cycles), default=0)
        }
        
        return CircularDependencyResponse(
            client_id=client_id,
            project_id=project_id,
            circular_dependencies=cycles,
            summary=summary
        )
        
    except Exception as e:
        logger.error(f"Failed to detect circular dependencies for {client_id}: {e}")
        return CircularDependencyResponse(
            client_id=client_id,
            project_id=project_id,
            error=str(e)
        )

@router.get("/complexity/{client_id}", response_model=ComplexityAnalysisResponse)
async def get_complexity_analysis(
    client_id: str = Path(..., description="Client session ID"),
    project_id: Optional[str] = Query(default=None, description="Optional project filter"),
    graph_service: CodeGraphService = Depends(get_graph_service)
) -> ComplexityAnalysisResponse:
    """Analyze code complexity across the project"""
    try:
        # Ensure connection
        if not graph_service.is_connected():
            await graph_service.connect()
        
        # Get complexity analysis
        analysis = await graph_service.analyze_code_complexity(project_id)
        
        return ComplexityAnalysisResponse(
            client_id=client_id,
            project_id=project_id,
            **analysis
        )
        
    except Exception as e:
        logger.error(f"Failed to get complexity analysis for {client_id}: {e}")
        return ComplexityAnalysisResponse(
            client_id=client_id,
            project_id=project_id,
            error=str(e)
        )

@router.post("/analyze-project/{client_id}", response_model=ProjectAnalysisResponse)
async def analyze_project(
    request: ProjectAnalysisRequest,
    client_id: str = Path(..., description="Client session ID"),
    ast_service: ASTGraphService = Depends(get_ast_graph_service)
) -> ProjectAnalysisResponse:
    """Analyze a project and populate the graph database"""
    try:
        logger.info(f"Starting project analysis for {client_id}: {request.project_path}")
        
        # Run project analysis
        stats = await ast_service.analyze_project(
            request.project_path, 
            request.project_id or client_id
        )
        
        success = len(stats.get('errors', [])) == 0 or stats.get('files_processed', 0) > 0
        
        return ProjectAnalysisResponse(
            client_id=client_id,
            project_path=request.project_path,
            analysis_stats=stats,
            success=success,
            error=None if success else f"Analysis completed with {len(stats.get('errors', []))} errors"
        )
        
    except Exception as e:
        logger.error(f"Failed to analyze project for {client_id}: {e}")
        return ProjectAnalysisResponse(
            client_id=client_id,
            project_path=request.project_path,
            analysis_stats={},
            success=False,
            error=str(e)
        )

@router.delete("/project/{client_id}")
async def clear_project_data(
    client_id: str = Path(..., description="Client session ID"),
    project_id: Optional[str] = Query(default=None, description="Project ID to clear"),
    graph_service: CodeGraphService = Depends(get_graph_service)
) -> Dict[str, Any]:
    """Clear project data from the graph database"""
    try:
        # Use client_id as project_id if not specified
        target_project_id = project_id or client_id
        
        # Ensure connection
        if not graph_service.is_connected():
            await graph_service.connect()
        
        # Clear project data
        success = await graph_service.clear_project_data(target_project_id)
        
        return {
            "success": success,
            "client_id": client_id,
            "project_id": target_project_id,
            "message": f"Project data cleared successfully" if success else "Failed to clear project data"
        }
        
    except Exception as e:
        logger.error(f"Failed to clear project data for {client_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Utility Endpoints
@router.get("/statistics")
async def get_graph_statistics(
    project_id: Optional[str] = Query(default=None, description="Optional project filter"),
    graph_service: CodeGraphService = Depends(get_graph_service)
) -> Dict[str, Any]:
    """Get general graph database statistics"""
    try:
        # Ensure connection
        if not graph_service.is_connected():
            await graph_service.connect()
        
        # Get architecture overview for statistics
        overview = await graph_service.get_architecture_overview(project_id)
        
        return {
            "project_id": project_id,
            "statistics": overview.get('metrics', {}),
            "node_counts": overview.get('node_statistics', {}),
            "relationship_counts": overview.get('relationship_statistics', {}),
            "connected": graph_service.is_connected()
        }
        
    except Exception as e:
        logger.error(f"Failed to get graph statistics: {e}")
        return {
            "error": str(e),
            "connected": False
        }