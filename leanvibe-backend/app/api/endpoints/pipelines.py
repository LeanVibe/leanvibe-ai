"""
Autonomous Pipeline API endpoints for LeanVibe Platform
Provides comprehensive REST API for managing autonomous MVP generation pipelines
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse

from ...models.pipeline_models import (
    PipelineCreateRequest, PipelineResponse, PipelineStatusResponse,
    PipelineUpdateRequest, PipelineExecutionRequest, PipelineLogEntry,
    PipelineStatus, PipelineStage, PipelineProgress, PipelineConfiguration
)
from ...models.mvp_models import MVPProject, MVPStatus, FounderInterview, TechnicalBlueprint
from ...services.mvp_service import mvp_service
from ...services.auth_service import auth_service
from ...middleware.tenant_middleware import get_current_tenant, require_tenant
from ...core.exceptions import InsufficientPermissionsError
from ...core.database import get_database_session
from sqlalchemy import select, func
from ...models.orm_models import PipelineExecutionLogORM as _LogORM
from ...auth.permissions import require_permission, Permission
from ...services.audit_service import audit_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/pipelines", tags=["pipelines"])
security = HTTPBearer()
@router.get("/{pipeline_id}/logs/summary")
async def get_pipeline_logs_summary(
    pipeline_id: UUID,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    tenant = Depends(require_tenant),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None)
) -> Dict[str, Any]:
    """
    Get aggregated log summary (counts by level and stage) for a pipeline.
    """
    try:
        # Verify token
        payload = await auth_service.verify_token(credentials.credentials)
        user_id = UUID(payload["user_id"]) if payload and payload.get("user_id") else None

        # Verify project access
        mvp_project = await mvp_service.get_mvp_project(pipeline_id)
        if not mvp_project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")
        if mvp_project.tenant_id != tenant.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to pipeline")

        # DB-first aggregation
        summary = {"by_level": {}, "by_stage": {}, "total": 0}
        try:
            async for session in get_database_session():
                base = select(_LogORM).where(_LogORM.mvp_project_id == pipeline_id, _LogORM.tenant_id == tenant.id)
                if start_time:
                    base = base.where(_LogORM.timestamp >= start_time)
                if end_time:
                    base = base.where(_LogORM.timestamp <= end_time)

                # Count total
                total = await session.execute(select(func.count()).select_from(base.subquery()))
                summary["total"] = int(total.scalar() or 0)

                # Counts by level
                rows = await session.execute(
                    select(_LogORM.level, func.count()).select_from(base.subquery()).group_by(_LogORM.level)
                )
                for level, count in rows.all():
                    summary["by_level"][level] = int(count)

                # Counts by stage
                rows = await session.execute(
                    select(_LogORM.stage, func.count()).select_from(base.subquery()).group_by(_LogORM.stage)
                )
                for stage, count in rows.all():
                    summary["by_stage"][stage or "unknown"] = int(count)
                break
        except Exception:
            # Fallback: in-memory
            raw_logs = await mvp_service.get_generation_logs(pipeline_id)
            for entry in raw_logs:
                ts = entry.get("timestamp")
                if start_time and ts and ts < start_time:
                    continue
                if end_time and ts and ts > end_time:
                    continue
                summary["total"] += 1
                level = str(entry.get("level", "INFO")).upper()
                stage = str(entry.get("stage", "unknown"))
                summary["by_level"][level] = summary["by_level"].get(level, 0) + 1
                summary["by_stage"][stage] = summary["by_stage"].get(stage, 0) + 1

        return summary
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to summarize pipeline logs {pipeline_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to summarize pipeline logs")


@router.post("/", response_model=PipelineResponse, status_code=status.HTTP_201_CREATED)
async def create_pipeline(
    pipeline_request: PipelineCreateRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    tenant = Depends(require_tenant)
) -> PipelineResponse:
    """
    Create new autonomous pipeline for MVP generation
    
    Creates a new pipeline that will manage the complete autonomous generation
    of an MVP from founder interview through deployment.
    
    **Requirements:**
    - Valid authentication token
    - Complete founder interview data
    - Tenant must have available pipeline quota
    
    **Process Flow:**
    1. Validate founder interview completeness
    2. Create MVP project record
    3. Initialize pipeline tracking
    4. Return pipeline details for monitoring
    """
    try:
        # Verify token and get user
        payload = await auth_service.verify_token(credentials.credentials)
        user_id = UUID(payload["user_id"])
        
        # Validate founder interview data
        if not _validate_founder_interview(pipeline_request.founder_interview):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incomplete founder interview data"
            )
        
        # Create MVP project
        mvp_project = await mvp_service.create_mvp_project(
            tenant_id=tenant.id,
            founder_interview=pipeline_request.founder_interview,
            priority=pipeline_request.configuration.priority if pipeline_request.configuration else "normal"
        )
        
        # Create pipeline response
        pipeline_response = PipelineResponse(
            id=mvp_project.id,
            project_name=mvp_project.project_name,
            status=PipelineStatus.BLUEPRINT_PENDING,
            current_stage=PipelineStage.BLUEPRINT_GENERATION,
            progress=PipelineProgress(
                overall_progress=0.0,
                stage_progress=0.0,
                estimated_completion=datetime.utcnow() + timedelta(hours=6),
                stages_completed=[],
                current_stage_details="Pipeline created, waiting for blueprint approval"
            ),
            created_at=mvp_project.created_at,
            estimated_completion=datetime.utcnow() + timedelta(hours=6),
            tenant_id=tenant.id,
            created_by=user_id
        )
        
        logger.info(f"Created pipeline {mvp_project.id} for tenant {tenant.id}")
        return pipeline_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create pipeline: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create autonomous pipeline"
        )


@router.get("/", response_model=List[PipelineResponse])
async def list_pipelines(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    tenant = Depends(require_tenant),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status_filter: Optional[PipelineStatus] = Query(None),
    stage_filter: Optional[PipelineStage] = Query(None)
) -> List[PipelineResponse]:
    """
    List user's autonomous pipelines with filtering and pagination
    
    Returns a paginated list of pipelines for the current tenant with optional filtering.
    
    **Query Parameters:**
    - **limit**: Number of results (1-100, default 50)
    - **offset**: Result offset for pagination (default 0)
    - **status_filter**: Filter by pipeline status
    - **stage_filter**: Filter by current pipeline stage
    
    **Supported Filters:**
    - Status: blueprint_pending, generating, deployed, failed, cancelled
    - Stage: blueprint_generation, backend_development, frontend_development, infrastructure_setup, deployment
    """
    try:
        # Verify token
        payload = await auth_service.verify_token(credentials.credentials)
        user_id = UUID(payload["user_id"]) if payload and payload.get("user_id") else None
        
        # Get MVP projects for tenant
        mvp_projects = await mvp_service.get_tenant_mvp_projects(
            tenant_id=tenant.id,
            limit=limit,
            offset=offset
        )
        
        # Convert to pipeline responses with filtering
        pipelines = []
        for project in mvp_projects:
            pipeline_response = await _mvp_project_to_pipeline_response(project)
            
            # Apply filters
            if status_filter and pipeline_response.status != status_filter:
                continue
            if stage_filter and pipeline_response.current_stage != stage_filter:
                continue
                
            pipelines.append(pipeline_response)
        
        logger.info(f"Listed {len(pipelines)} pipelines for tenant {tenant.id}")
        return pipelines
        
    except Exception as e:
        logger.error(f"Failed to list pipelines: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve pipelines"
        )


@router.get("/{pipeline_id}", response_model=PipelineResponse)
async def get_pipeline(
    pipeline_id: UUID,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    tenant = Depends(require_tenant)
) -> PipelineResponse:
    """
    Get detailed pipeline information by ID
    
    Returns comprehensive pipeline details including current status,
    progress metrics, and execution history.
    
    **Response includes:**
    - Current execution status and stage
    - Progress metrics and estimates
    - Configuration and blueprint details
    - Error information (if failed)
    """
    try:
        # Verify token
        await auth_service.verify_token(credentials.credentials)
        
        # Get MVP project
        mvp_project = await mvp_service.get_mvp_project(pipeline_id)
        if not mvp_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pipeline not found"
            )
        
        # Verify tenant access
        if mvp_project.tenant_id != tenant.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to pipeline"
            )
        
        # Convert to pipeline response
        pipeline_response = await _mvp_project_to_pipeline_response(mvp_project)
        
        return pipeline_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get pipeline {pipeline_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve pipeline"
        )


@router.put("/{pipeline_id}", response_model=PipelineResponse)
async def update_pipeline(
    pipeline_id: UUID,
    update_request: PipelineUpdateRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    tenant = Depends(require_tenant)
) -> PipelineResponse:
    """
    Update pipeline configuration and settings
    
    Allows updating pipeline metadata, configuration, and settings.
    Cannot modify pipeline during active generation.
    
    **Updateable Fields:**
    - Project name and description
    - Configuration settings
    - Priority level (if not currently generating)
    """
    try:
        # Verify token
        await auth_service.verify_token(credentials.credentials)
        
        # Get MVP project
        mvp_project = await mvp_service.get_mvp_project(pipeline_id)
        if not mvp_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pipeline not found"
            )
        
        # Verify tenant access
        if mvp_project.tenant_id != tenant.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to pipeline"
            )
        
        # Check if pipeline can be updated
        if mvp_project.status == MVPStatus.GENERATING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update pipeline during generation"
            )
        
        # Apply updates
        if update_request.project_name:
            mvp_project.project_name = update_request.project_name
        if update_request.description:
            mvp_project.description = update_request.description
        
        # Update project
        await mvp_service.update_mvp_project(mvp_project)
        
        # Return updated pipeline
        pipeline_response = await _mvp_project_to_pipeline_response(mvp_project)
        
        logger.info(f"Updated pipeline {pipeline_id}")
        return pipeline_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update pipeline {pipeline_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update pipeline"
        )


@router.delete("/{pipeline_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pipeline(
    pipeline_id: UUID,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    tenant = Depends(require_tenant)
):
    """
    Cancel and delete pipeline
    
    Cancels active generation (if running) and removes the pipeline.
    This action cannot be undone.
    
    **Behavior:**
    - Active generation will be cancelled
    - All pipeline data will be removed
    - Generated files will be preserved (if any)
    """
    try:
        # Verify token
        await auth_service.verify_token(credentials.credentials)
        
        # Get MVP project
        mvp_project = await mvp_service.get_mvp_project(pipeline_id)
        if not mvp_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pipeline not found"
            )
        
        # Verify tenant access
        if mvp_project.tenant_id != tenant.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to pipeline"
            )
        
        # Cancel generation if active
        if mvp_project.status == MVPStatus.GENERATING:
            await mvp_service.cancel_mvp_generation(pipeline_id)
        
        # TODO: Implement actual deletion when database persistence is added
        await audit_service.log(
            tenant_id=tenant.id,
            action="pipeline_cancel",
            resource_type="pipeline",
            resource_id=str(pipeline_id),
            user_id=user_id,
        )
        logger.info(f"Deleted pipeline {pipeline_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete pipeline {pipeline_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete pipeline"
        )


@router.post("/{pipeline_id}/start", response_model=PipelineResponse)
async def start_pipeline(
    pipeline_id: UUID,
    execution_request: PipelineExecutionRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    tenant = Depends(require_tenant)
) -> PipelineResponse:
    """
    Start autonomous pipeline execution
    
    Begins the autonomous MVP generation process using the provided
    technical blueprint and configuration.
    
    **Prerequisites:**
    - Pipeline must be in blueprint_pending status
    - Technical blueprint must be provided and valid
    - Tenant must have available generation quota
    
    **Process:**
    1. Validates technical blueprint
    2. Starts assembly line orchestration
    3. Returns updated pipeline with progress tracking
    """
    try:
        # Verify token
        await auth_service.verify_token(credentials.credentials)
        
        # Get MVP project
        mvp_project = await mvp_service.get_mvp_project(pipeline_id)
        if not mvp_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pipeline not found"
            )
        
        # Verify tenant access
        if mvp_project.tenant_id != tenant.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to pipeline"
            )
        
        # Validate pipeline can be started
        if mvp_project.status not in [MVPStatus.BLUEPRINT_PENDING, MVPStatus.FAILED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Pipeline in {mvp_project.status} status cannot be started"
            )
        
        # Start MVP generation
        success = await mvp_service.start_mvp_generation(
            pipeline_id,
            execution_request.technical_blueprint
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to start pipeline execution"
            )
        
        # Return updated pipeline
        updated_project = await mvp_service.get_mvp_project(pipeline_id)
        pipeline_response = await _mvp_project_to_pipeline_response(updated_project)
        
        # Audit
        await audit_service.log(
            tenant_id=tenant.id,
            action="pipeline_start",
            resource_type="pipeline",
            resource_id=str(pipeline_id),
            user_id=user_id,
        )
        logger.info(f"Started pipeline execution for {pipeline_id}")
        return pipeline_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start pipeline {pipeline_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start pipeline execution"
        )


@router.post("/{pipeline_id}/pause", response_model=PipelineResponse)
async def pause_pipeline(
    pipeline_id: UUID,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    tenant = Depends(require_tenant),
    _perm = Depends(require_permission(Permission.PROJECT_WRITE))
) -> PipelineResponse:
    """
    Pause pipeline execution
    
    Temporarily pauses the autonomous generation process.
    Can be resumed later without losing progress.
    
    **Note:** Currently not fully implemented in assembly line system.
    Will return appropriate status for future implementation.
    """
    try:
        # Verify token
        payload = await auth_service.verify_token(credentials.credentials)
        user_id = UUID(payload["user_id"]) if payload and payload.get("user_id") else None
        
        # Get MVP project
        mvp_project = await mvp_service.get_mvp_project(pipeline_id)
        if not mvp_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pipeline not found"
            )
        
        # Verify tenant access
        if mvp_project.tenant_id != tenant.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to pipeline"
            )
        
        # Check if pipeline can be paused
        if mvp_project.status != MVPStatus.GENERATING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Pipeline is not currently running"
            )
        
        # Pause via MVP service
        paused = await mvp_service.pause_mvp_generation(pipeline_id)
        if not paused:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to pause pipeline at this time"
            )
        # Audit
        await audit_service.log(
            tenant_id=tenant.id,
            action="pipeline_pause",
            resource_type="pipeline",
            resource_id=str(pipeline_id),
        )
        updated_project = await mvp_service.get_mvp_project(pipeline_id)
        pipeline_response = await _mvp_project_to_pipeline_response(updated_project)
        return pipeline_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to pause pipeline {pipeline_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to pause pipeline"
        )


@router.post("/{pipeline_id}/resume", response_model=PipelineResponse)
async def resume_pipeline(
    pipeline_id: UUID,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    tenant = Depends(require_tenant),
    _perm = Depends(require_permission(Permission.PROJECT_WRITE))
) -> PipelineResponse:
    """
    Resume paused pipeline execution
    
    Resumes a previously paused autonomous generation process.
    
    **Note:** Currently not fully implemented in assembly line system.
    Will return appropriate status for future implementation.
    """
    try:
        # Verify token
        await auth_service.verify_token(credentials.credentials)
        
        # Get MVP project
        mvp_project = await mvp_service.get_mvp_project(pipeline_id)
        if not mvp_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pipeline not found"
            )
        
        # Verify tenant access
        if mvp_project.tenant_id != tenant.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to pipeline"
            )
        
        # Resume via MVP service
        resumed = await mvp_service.resume_mvp_generation(pipeline_id)
        if not resumed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to resume pipeline at this time"
            )
        await audit_service.log(
            tenant_id=tenant.id,
            action="pipeline_resume",
            resource_type="pipeline",
            resource_id=str(pipeline_id),
        )
        updated_project = await mvp_service.get_mvp_project(pipeline_id)
        pipeline_response = await _mvp_project_to_pipeline_response(updated_project)
        return pipeline_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resume pipeline {pipeline_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resume pipeline"
        )


@router.post("/{pipeline_id}/restart", response_model=PipelineResponse)
async def restart_pipeline(
    pipeline_id: UUID,
    execution_request: PipelineExecutionRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    tenant = Depends(require_tenant)
) -> PipelineResponse:
    """
    Restart failed pipeline
    
    Restarts a failed pipeline with the same or updated technical blueprint.
    Clears previous error state and begins fresh execution.
    
    **Prerequisites:**
    - Pipeline must be in failed status
    - Updated technical blueprint (optional)
    - Tenant must have available generation quota
    """
    try:
        # Verify token
        await auth_service.verify_token(credentials.credentials)
        
        # Get MVP project
        mvp_project = await mvp_service.get_mvp_project(pipeline_id)
        if not mvp_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pipeline not found"
            )
        
        # Verify tenant access
        if mvp_project.tenant_id != tenant.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to pipeline"
            )
        
        # Check if pipeline can be restarted
        if mvp_project.status != MVPStatus.FAILED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only failed pipelines can be restarted"
            )
        
        # Clear error state and restart
        mvp_project.status = MVPStatus.BLUEPRINT_PENDING
        mvp_project.error_message = None
        await mvp_service.update_mvp_project(mvp_project)
        
        # Start with new blueprint
        success = await mvp_service.start_mvp_generation(
            pipeline_id,
            execution_request.technical_blueprint
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to restart pipeline execution"
            )
        
        # Return updated pipeline
        updated_project = await mvp_service.get_mvp_project(pipeline_id)
        pipeline_response = await _mvp_project_to_pipeline_response(updated_project)
        
        await audit_service.log(
            tenant_id=tenant.id,
            action="pipeline_restart",
            resource_type="pipeline",
            resource_id=str(pipeline_id),
            user_id=user_id,
        )
        logger.info(f"Restarted pipeline {pipeline_id}")
        return pipeline_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to restart pipeline {pipeline_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to restart pipeline"
        )


@router.get("/{pipeline_id}/status", response_model=PipelineStatusResponse)
async def get_pipeline_status(
    pipeline_id: UUID,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    tenant = Depends(require_tenant)
) -> PipelineStatusResponse:
    """
    Get real-time pipeline status and progress
    
    Returns detailed real-time status including current stage,
    progress metrics, logs, and error information.
    
    **Status Information:**
    - Current execution status and stage
    - Progress percentages and estimates
    - Recent execution logs
    - Error details (if applicable)
    - Stage-specific metadata
    """
    try:
        # Verify token
        await auth_service.verify_token(credentials.credentials)
        
        # Get MVP project
        mvp_project = await mvp_service.get_mvp_project(pipeline_id)
        if not mvp_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pipeline not found"
            )
        
        # Verify tenant access
        if mvp_project.tenant_id != tenant.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to pipeline"
            )
        
        # Get generation progress
        progress_data = await mvp_service.get_generation_progress(pipeline_id)
        
        # Convert MVP status to pipeline status
        status_mapping = {
            MVPStatus.BLUEPRINT_PENDING: PipelineStatus.BLUEPRINT_PENDING,
            MVPStatus.GENERATING: PipelineStatus.GENERATING,
            MVPStatus.DEPLOYED: PipelineStatus.DEPLOYED,
            MVPStatus.FAILED: PipelineStatus.FAILED,
            MVPStatus.CANCELLED: PipelineStatus.CANCELLED
        }
        
        pipeline_status = status_mapping.get(mvp_project.status, PipelineStatus.FAILED)
        
        # Create status response
        if progress_data:
            progress = PipelineProgress(
                overall_progress=progress_data.get("overall_progress", 0.0),
                stage_progress=progress_data.get("stage_progress", 0.0),
                estimated_completion=progress_data.get("estimated_completion"),
                stages_completed=progress_data.get("stages_completed", []),
                current_stage_details=progress_data.get("current_stage_details", "")
            )
            
            # Map current stage
            stage_mapping = {
                "backend": PipelineStage.BACKEND_DEVELOPMENT,
                "frontend": PipelineStage.FRONTEND_DEVELOPMENT,
                "infrastructure": PipelineStage.INFRASTRUCTURE_SETUP,
                "observability": PipelineStage.DEPLOYMENT,
                "completed": PipelineStage.DEPLOYMENT,
                "failed": PipelineStage.BLUEPRINT_GENERATION
            }
            
            current_stage = stage_mapping.get(
                progress_data.get("current_stage", ""),
                PipelineStage.BLUEPRINT_GENERATION
            )
        else:
            # Default progress for non-generating pipelines
            progress = PipelineProgress(
                overall_progress=100.0 if pipeline_status == PipelineStatus.DEPLOYED else 0.0,
                stage_progress=0.0,
                estimated_completion=mvp_project.completed_at,
                stages_completed=[],
                current_stage_details=mvp_project.error_message or "Pipeline not active"
            )
            current_stage = PipelineStage.BLUEPRINT_GENERATION
        
        # Generate mock logs for demonstration
        logs = []
        if mvp_project.status == MVPStatus.GENERATING and progress_data:
            logs.append(PipelineLogEntry(
                timestamp=datetime.utcnow(),
                level="INFO",
                message=progress_data.get("current_stage_details", "Processing..."),
                stage=current_stage
            ))
        
        status_response = PipelineStatusResponse(
            status=pipeline_status,
            current_stage=current_stage,
            progress=progress,
            stage_details=progress_data or {},
            logs=logs,
            error_message=mvp_project.error_message
        )
        
        return status_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get pipeline status {pipeline_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve pipeline status"
        )


@router.get("/{pipeline_id}/logs", response_model=List[PipelineLogEntry])
async def get_pipeline_logs(
    pipeline_id: UUID,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    tenant = Depends(require_tenant),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    level_filter: Optional[str] = Query(None, description="Filter by level (INFO, WARNING, ERROR)"),
    stage_filter: Optional[PipelineStage] = Query(None, description="Filter by stage"),
    start_time: Optional[datetime] = Query(None, description="Start time (ISO8601)"),
    end_time: Optional[datetime] = Query(None, description="End time (ISO8601)"),
    search: Optional[str] = Query(None, max_length=200, description="Search in message"),
    sort: str = Query("asc", pattern="^(asc|desc)$", description="Sort by timestamp asc|desc"),
    after_id: Optional[UUID] = Query(None, description="Seek pagination: return logs after this id (ignores offset)")
) -> List[PipelineLogEntry]:
    """
    Get pipeline execution logs with filtering
    
    Returns paginated execution logs for the pipeline with optional filtering.
    
    **Query Parameters:**
    - **limit**: Number of log entries (1-1000, default 100)
    - **offset**: Log offset for pagination (default 0)
    - **level_filter**: Filter by log level (INFO, WARNING, ERROR)
    - **stage_filter**: Filter by pipeline stage
    
    **Log Levels:**
    - INFO: General execution information
    - WARNING: Non-critical issues or warnings
    - ERROR: Error conditions and failures
    """
    try:
        # Verify token
        await auth_service.verify_token(credentials.credentials)
        
        # Get MVP project
        mvp_project = await mvp_service.get_mvp_project(pipeline_id)
        if not mvp_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pipeline not found"
            )
        
        # Verify tenant access
        if mvp_project.tenant_id != tenant.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to pipeline"
            )
        
        # Try DB-first
        db_logs: List[PipelineLogEntry] = []
        try:
            async for session in get_database_session():
                stmt = (
                    select(_LogORM)
                    .where(_LogORM.mvp_project_id == pipeline_id)
                    .where(_LogORM.tenant_id == tenant.id)
                )
                # Time window
                if start_time:
                    stmt = stmt.where(_LogORM.timestamp >= start_time)
                if end_time:
                    stmt = stmt.where(_LogORM.timestamp <= end_time)
                if level_filter:
                    stmt = stmt.where(_LogORM.level == level_filter.upper())
                if stage_filter:
                    stmt = stmt.where(_LogORM.stage == stage_filter.value)
                if search:
                    stmt = stmt.where(_LogORM.message.ilike(f"%{search}%"))
                # Seek pagination by id (based on timestamp)
                if after_id is not None:
                    anchor = await session.get(_LogORM, after_id)
                    if anchor is not None:
                        stmt = stmt.where(_LogORM.timestamp > anchor.timestamp)
                # Sort
                if sort == "desc":
                    stmt = stmt.order_by(_LogORM.timestamp.desc())
                else:
                    stmt = stmt.order_by(_LogORM.timestamp.asc())
                # Offset only when not using seek
                if after_id is None and offset:
                    stmt = stmt.offset(offset)
                stmt = stmt.limit(limit)
                result = await session.execute(stmt)
                rows = result.scalars().all()
                for row in rows:
                    # Map stage string to PipelineStage if possible
                    stage = {
                        "blueprint_generation": PipelineStage.BLUEPRINT_GENERATION,
                        "backend": PipelineStage.BACKEND_DEVELOPMENT,
                        "backend_development": PipelineStage.BACKEND_DEVELOPMENT,
                        "frontend": PipelineStage.FRONTEND_DEVELOPMENT,
                        "frontend_development": PipelineStage.FRONTEND_DEVELOPMENT,
                        "infrastructure": PipelineStage.INFRASTRUCTURE_SETUP,
                        "infrastructure_setup": PipelineStage.INFRASTRUCTURE_SETUP,
                        "deployment": PipelineStage.DEPLOYMENT,
                    }.get((row.stage or "").lower(), PipelineStage.BLUEPRINT_GENERATION)

                    db_logs.append(PipelineLogEntry(
                        timestamp=row.timestamp,
                        level=row.level,
                        message=row.message,
                        stage=stage
                    ))
                break
        except Exception:
            # Ignore DB errors and fallback to in-memory
            db_logs = []

        if db_logs:
            return db_logs

        # Fallback: Retrieve from MVP service in-memory store
        raw_logs = await mvp_service.get_generation_logs(pipeline_id)
        mem_logs: List[PipelineLogEntry] = []
        for entry in raw_logs:
            try:
                stage_str = str(entry.get("stage", "")).lower()
                stage = {
                    "blueprint_generation": PipelineStage.BLUEPRINT_GENERATION,
                    "backend": PipelineStage.BACKEND_DEVELOPMENT,
                    "backend_development": PipelineStage.BACKEND_DEVELOPMENT,
                    "frontend": PipelineStage.FRONTEND_DEVELOPMENT,
                    "frontend_development": PipelineStage.FRONTEND_DEVELOPMENT,
                    "infrastructure": PipelineStage.INFRASTRUCTURE_SETUP,
                    "infrastructure_setup": PipelineStage.INFRASTRUCTURE_SETUP,
                    "deployment": PipelineStage.DEPLOYMENT,
                }.get(stage_str, PipelineStage.BLUEPRINT_GENERATION)

                mem_logs.append(PipelineLogEntry(
                    timestamp=entry["timestamp"],
                    level=str(entry.get("level", "INFO")),
                    message=str(entry.get("message", "")),
                    stage=stage
                ))
            except Exception:
                continue

        # Apply filters to in-memory fallback
        if start_time:
            mem_logs = [log for log in mem_logs if log.timestamp >= start_time]
        if end_time:
            mem_logs = [log for log in mem_logs if log.timestamp <= end_time]
        if level_filter:
            mem_logs = [log for log in mem_logs if log.level == level_filter.upper()]
        if stage_filter:
            mem_logs = [log for log in mem_logs if log.stage == stage_filter]
        if search:
            mem_logs = [log for log in mem_logs if search.lower() in (log.message or "").lower()]
        # Sort
        reverse = (sort == "desc")
        mem_logs.sort(key=lambda l: l.timestamp or datetime.min, reverse=reverse)
        # Seek pagination on timestamp only
        if after_id is not None:
            # No ids in memory logs; approximate by skipping until after anchor timestamp from DB
            async for session in get_database_session():
                anchor = await session.get(_LogORM, after_id)
                if anchor is not None:
                    mem_logs = [l for l in mem_logs if l.timestamp and l.timestamp > anchor.timestamp]
                break
        # Offset/limit
        return mem_logs[offset:offset + limit]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get pipeline logs {pipeline_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve pipeline logs"
        )


# Helper functions

def _validate_founder_interview(interview: FounderInterview) -> bool:
    """Validate founder interview completeness"""
    required_fields = [
        interview.business_idea,
        interview.target_market,
        interview.value_proposition
    ]
    
    return all(field and field.strip() for field in required_fields)


async def _mvp_project_to_pipeline_response(mvp_project: MVPProject) -> PipelineResponse:
    """Convert MVP project to pipeline response"""
    
    # Map MVP status to pipeline status
    status_mapping = {
        MVPStatus.BLUEPRINT_PENDING: PipelineStatus.BLUEPRINT_PENDING,
        MVPStatus.GENERATING: PipelineStatus.GENERATING,
        MVPStatus.DEPLOYED: PipelineStatus.DEPLOYED,
        MVPStatus.FAILED: PipelineStatus.FAILED,
        MVPStatus.CANCELLED: PipelineStatus.CANCELLED
    }
    
    pipeline_status = status_mapping.get(mvp_project.status, PipelineStatus.FAILED)
    
    # Determine current stage
    if mvp_project.status == MVPStatus.BLUEPRINT_PENDING:
        current_stage = PipelineStage.BLUEPRINT_GENERATION
    elif mvp_project.status == MVPStatus.GENERATING:
        # Get real-time stage from progress
        progress_data = await mvp_service.get_generation_progress(mvp_project.id)
        if progress_data:
            stage_mapping = {
                "backend": PipelineStage.BACKEND_DEVELOPMENT,
                "frontend": PipelineStage.FRONTEND_DEVELOPMENT,
                "infrastructure": PipelineStage.INFRASTRUCTURE_SETUP,
                "observability": PipelineStage.DEPLOYMENT
            }
            current_stage = stage_mapping.get(
                progress_data.get("current_stage", ""),
                PipelineStage.BACKEND_DEVELOPMENT
            )
        else:
            current_stage = PipelineStage.BACKEND_DEVELOPMENT
    elif mvp_project.status == MVPStatus.DEPLOYED:
        current_stage = PipelineStage.DEPLOYMENT
    else:
        current_stage = PipelineStage.BLUEPRINT_GENERATION
    
    # Get progress information
    progress_data = await mvp_service.get_generation_progress(mvp_project.id)
    if progress_data:
        progress = PipelineProgress(
            overall_progress=progress_data.get("overall_progress", 0.0),
            stage_progress=progress_data.get("stage_progress", 0.0),
            estimated_completion=progress_data.get("estimated_completion"),
            stages_completed=progress_data.get("stages_completed", []),
            current_stage_details=progress_data.get("current_stage_details", "")
        )
    else:
        # Default progress
        if mvp_project.status == MVPStatus.DEPLOYED:
            progress = PipelineProgress(
                overall_progress=100.0,
                stage_progress=100.0,
                estimated_completion=mvp_project.completed_at,
                stages_completed=["backend", "frontend", "infrastructure", "observability"],
                current_stage_details="Pipeline completed successfully"
            )
        else:
            progress = PipelineProgress(
                overall_progress=0.0,
                stage_progress=0.0,
                estimated_completion=mvp_project.created_at + timedelta(hours=6),
                stages_completed=[],
                current_stage_details=mvp_project.error_message or "Pipeline not active"
            )
    
    return PipelineResponse(
        id=mvp_project.id,
        project_name=mvp_project.project_name,
        status=pipeline_status,
        current_stage=current_stage,
        progress=progress,
        created_at=mvp_project.created_at,
        estimated_completion=progress.estimated_completion,
        tenant_id=mvp_project.tenant_id,
        created_by=mvp_project.tenant_id  # TODO: Add proper user tracking
    )


@router.get("/{pipeline_id}/logs/tail")
async def tail_pipeline_logs(
    pipeline_id: UUID,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    tenant = Depends(require_tenant),
    level_filter: Optional[str] = Query(None, description="INFO|WARNING|ERROR"),
    stage_filter: Optional[PipelineStage] = Query(None),
    search: Optional[str] = Query(None, max_length=200),
    once: bool = Query(False, description="Emit current batch and close (for testing/polling)"),
    token: Optional[str] = Query(None, description="Alt auth for SSE when headers unavailable"),
):
    """Server-Sent Events stream for live pipeline logs with basic filters.

    For CI/tests, pass once=true to emit a single batch and close the stream.
    """
    try:
        # Support SSE without auth headers by allowing token query param
        if token:
            await auth_service.verify_token(token)
        elif credentials:
            await auth_service.verify_token(credentials.credentials)
        else:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing auth token")
        mvp_project = await mvp_service.get_mvp_project(pipeline_id)
        if not mvp_project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")
        if mvp_project.tenant_id != tenant.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to pipeline")

        async def event_generator():
            last_ts = None
            # Single pass for once mode; simple loop otherwise (limited)
            max_iterations = 1 if once else 50
            iteration = 0
            while iteration < max_iterations:
                iteration += 1
                try:
                    raw_logs = await mvp_service.get_generation_logs(pipeline_id)
                except Exception:
                    raw_logs = []
                # Filter and order by timestamp
                def _matches(entry: dict) -> bool:
                    if level_filter and str(entry.get("level", "")).upper() != level_filter.upper():
                        return False
                    if stage_filter and str(entry.get("stage", "")).lower() not in {stage_filter.value, stage_filter.name.lower()}:
                        return False
                    if search and search.lower() not in str(entry.get("message", "")).lower():
                        return False
                    if last_ts and entry.get("timestamp") and entry["timestamp"] <= last_ts:
                        return False
                    return True

                batch = [e for e in raw_logs if _matches(e)]
                # Advance cursor to latest timestamp in batch
                if batch:
                    latest_ts = max((e.get("timestamp") for e in batch if e.get("timestamp")), default=None)
                    if latest_ts:
                        last_ts = latest_ts
                # Emit SSE lines
                for e in batch:
                    # Minimal JSON to keep payload small
                    payload = {
                        "timestamp": (e.get("timestamp").isoformat() if e.get("timestamp") else None),
                        "level": e.get("level"),
                        "stage": e.get("stage"),
                        "message": e.get("message"),
                    }
                    import json as _json
                    line = f"data: {_json.dumps(payload)}\n\n"
                    yield line.encode("utf-8")
                if once:
                    break
                # Small jittered sleep to avoid busy loop
                import asyncio as _asyncio, random as _rand
                await _asyncio.sleep(0.2 + _rand.random() * 0.2)

        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to tail logs for pipeline {pipeline_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to tail logs")