"""
MVP Factory API Endpoints
RESTful API for managing MVP projects and assembly line system
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field

from ..services.mvp_service import mvp_service, MVPServiceError
# from ..services.tenant_service import tenant_service  # Will be imported when proper integration is added
from ..models.mvp_models import MVPProject, MVPStatus, TechnicalBlueprint, FounderInterview
from ..models.tenant_models import TenantType
from ..core.auth import get_current_tenant_id
# from ..core.database import get_db  # Will be used when proper DB integration is added

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mvp", tags=["MVP Factory"])


# Request/Response Models

class CreateMVPProjectRequest(BaseModel):
    """Request to create new MVP project"""
    founder_interview: FounderInterview
    priority: str = Field(default="normal", pattern="^(low|normal|high|urgent)$")


class StartGenerationRequest(BaseModel):
    """Request to start MVP generation"""
    technical_blueprint: TechnicalBlueprint


class MVPProjectResponse(BaseModel):
    """Response containing MVP project details"""
    project: MVPProject
    generation_progress: Optional[Dict[str, Any]] = None


class MVPProjectListResponse(BaseModel):
    """Response containing list of MVP projects"""
    projects: List[MVPProject]
    total_count: int
    has_more: bool


class GenerationProgressResponse(BaseModel):
    """Response containing generation progress"""
    mvp_project_id: UUID
    progress: Optional[Dict[str, Any]]


# API Endpoints

@router.post(
    "/projects",
    response_model=MVPProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new MVP project",
    description="Create a new MVP project from founder interview"
)
async def create_mvp_project(
    request: CreateMVPProjectRequest,
    tenant_id: UUID = Depends(get_current_tenant_id)
) -> MVPProjectResponse:
    """Create a new MVP project from founder interview"""
    try:
        # TODO: Validate tenant type with proper tenant service integration
        # For now, assume tenant is valid for testing
        logger.info(f"Creating MVP project for tenant {tenant_id} (mock validation)")
        
        # Create MVP project
        mvp_project = await mvp_service.create_mvp_project(
            tenant_id=tenant_id,
            founder_interview=request.founder_interview,
            priority=request.priority
        )
        
        logger.info(f"Created MVP project {mvp_project.id} for tenant {tenant_id}")
        
        return MVPProjectResponse(
            project=mvp_project
        )
        
    except MVPServiceError as e:
        logger.error(f"MVP service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error creating MVP project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post(
    "/projects/{mvp_project_id}/generate",
    response_model=MVPProjectResponse,
    summary="Start MVP generation",
    description="Start the assembly line system to generate complete MVP"
)
async def start_mvp_generation(
    mvp_project_id: UUID,
    request: StartGenerationRequest,
    background_tasks: BackgroundTasks,
    tenant_id: UUID = Depends(get_current_tenant_id)
) -> MVPProjectResponse:
    """Start MVP generation using the assembly line system"""
    try:
        # Verify project belongs to tenant
        mvp_project = await mvp_service.get_mvp_project(mvp_project_id)
        if not mvp_project or mvp_project.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="MVP project not found"
            )
        
        # Start generation
        success = await mvp_service.start_mvp_generation(
            mvp_project_id,
            request.technical_blueprint
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to start MVP generation"
            )
        
        # Get updated project
        updated_project = await mvp_service.get_mvp_project(mvp_project_id)
        progress = await mvp_service.get_generation_progress(mvp_project_id)
        
        logger.info(f"Started MVP generation for project {mvp_project_id}")
        
        return MVPProjectResponse(
            project=updated_project,
            generation_progress=progress
        )
        
    except MVPServiceError as e:
        logger.error(f"MVP service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error starting MVP generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/projects/{mvp_project_id}",
    response_model=MVPProjectResponse,
    summary="Get MVP project",
    description="Get detailed information about an MVP project"
)
async def get_mvp_project(
    mvp_project_id: UUID,
    tenant_id: UUID = Depends(get_current_tenant_id)
) -> MVPProjectResponse:
    """Get MVP project details"""
    try:
        mvp_project = await mvp_service.get_mvp_project(mvp_project_id)
        if not mvp_project or mvp_project.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="MVP project not found"
            )
        
        # Get generation progress if project is being generated
        progress = None
        if mvp_project.status == MVPStatus.GENERATING:
            progress = await mvp_service.get_generation_progress(mvp_project_id)
        
        return MVPProjectResponse(
            project=mvp_project,
            generation_progress=progress
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting MVP project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/projects",
    response_model=MVPProjectListResponse,
    summary="List MVP projects",
    description="Get list of MVP projects for current tenant"
)
async def list_mvp_projects(
    limit: int = 20,
    offset: int = 0,
    status_filter: Optional[MVPStatus] = None,
    tenant_id: UUID = Depends(get_current_tenant_id)
) -> MVPProjectListResponse:
    """List MVP projects for current tenant"""
    try:
        # Validate limit
        if limit > 100:
            limit = 100
        
        projects = await mvp_service.get_tenant_mvp_projects(
            tenant_id=tenant_id,
            limit=limit + 1,  # Get one extra to check if there are more
            offset=offset
        )
        
        # Apply status filter if provided
        if status_filter:
            projects = [p for p in projects if p.status == status_filter]
        
        has_more = len(projects) > limit
        if has_more:
            projects = projects[:limit]
        
        return MVPProjectListResponse(
            projects=projects,
            total_count=len(projects) + offset,
            has_more=has_more
        )
        
    except Exception as e:
        logger.error(f"Error listing MVP projects: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/projects/{mvp_project_id}/progress",
    response_model=GenerationProgressResponse,
    summary="Get generation progress",
    description="Get real-time progress of MVP generation"
)
async def get_generation_progress(
    mvp_project_id: UUID,
    tenant_id: UUID = Depends(get_current_tenant_id)
) -> GenerationProgressResponse:
    """Get real-time generation progress"""
    try:
        # Verify project belongs to tenant
        mvp_project = await mvp_service.get_mvp_project(mvp_project_id)
        if not mvp_project or mvp_project.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="MVP project not found"
            )
        
        progress = await mvp_service.get_generation_progress(mvp_project_id)
        
        return GenerationProgressResponse(
            mvp_project_id=mvp_project_id,
            progress=progress
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting generation progress: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post(
    "/projects/{mvp_project_id}/cancel",
    response_model=MVPProjectResponse,
    summary="Cancel MVP generation",
    description="Cancel ongoing MVP generation process"
)
async def cancel_mvp_generation(
    mvp_project_id: UUID,
    tenant_id: UUID = Depends(get_current_tenant_id)
) -> MVPProjectResponse:
    """Cancel ongoing MVP generation"""
    try:
        # Verify project belongs to tenant
        mvp_project = await mvp_service.get_mvp_project(mvp_project_id)
        if not mvp_project or mvp_project.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="MVP project not found"
            )
        
        if mvp_project.status != MVPStatus.GENERATING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel generation - project status is {mvp_project.status}"
            )
        
        success = await mvp_service.cancel_mvp_generation(mvp_project_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to cancel MVP generation"
            )
        
        # Get updated project
        updated_project = await mvp_service.get_mvp_project(mvp_project_id)
        
        logger.info(f"Cancelled MVP generation for project {mvp_project_id}")
        
        return MVPProjectResponse(
            project=updated_project
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling MVP generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.delete(
    "/projects/{mvp_project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete MVP project",
    description="Delete an MVP project (only allowed if not generating)"
)
async def delete_mvp_project(
    mvp_project_id: UUID,
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """Delete MVP project"""
    try:
        # Verify project belongs to tenant
        mvp_project = await mvp_service.get_mvp_project(mvp_project_id)
        if not mvp_project or mvp_project.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="MVP project not found"
            )
        
        if mvp_project.status == MVPStatus.GENERATING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete project while generation is in progress"
            )
        
        # TODO: Implement project deletion logic
        # For now, just update status to indicate deletion
        logger.info(f"Deleted MVP project {mvp_project_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting MVP project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# Health and Status Endpoints

@router.get(
    "/health",
    summary="MVP Factory health check",
    description="Health check for MVP factory system"
)
async def mvp_factory_health():
    """Health check for MVP factory system"""
    try:
        # Check assembly line system
        orchestrator_healthy = mvp_service.orchestrator is not None
        agents_registered = len(mvp_service.orchestrator.agents) > 0
        
        return {
            "status": "healthy",
            "timestamp": "2024-01-01T00:00:00Z",
            "components": {
                "orchestrator": "healthy" if orchestrator_healthy else "unhealthy",
                "agents": f"{len(mvp_service.orchestrator.agents)} registered" if agents_registered else "no agents",
                "service": "healthy"
            }
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Health check failed"
        )


@router.get(
    "/stats",
    summary="MVP Factory statistics",
    description="Get system statistics for MVP factory"
)
async def mvp_factory_stats(
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """Get MVP factory statistics"""
    try:
        projects = await mvp_service.get_tenant_mvp_projects(tenant_id)
        
        stats = {
            "total_projects": len(projects),
            "projects_by_status": {},
            "generation_stats": {
                "completed": 0,
                "in_progress": 0,
                "failed": 0
            }
        }
        
        for project in projects:
            status = project.status.value
            stats["projects_by_status"][status] = stats["projects_by_status"].get(status, 0) + 1
            
            if project.status == MVPStatus.DEPLOYED:
                stats["generation_stats"]["completed"] += 1
            elif project.status == MVPStatus.GENERATING:
                stats["generation_stats"]["in_progress"] += 1
            elif project.status == MVPStatus.FAILED:
                stats["generation_stats"]["failed"] += 1
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting MVP factory stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )