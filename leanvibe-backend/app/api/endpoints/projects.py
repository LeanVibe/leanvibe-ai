"""
Project API endpoints
"""

import logging
from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Path

from ...models.project_models import (
    Project,
    ProjectListResponse,
    ProjectMetrics,
    ProjectMetricsResponse,
    ProjectTask,
    ProjectTasksResponse,
    ProjectLanguage,
    ProjectStatus,
)
from ...services.project_service import ProjectService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["projects"])
project_service = ProjectService()


@router.get("/", response_model=ProjectListResponse)
async def list_projects():
    """Get list of all projects"""
    try:
        projects = await project_service.get_all_projects()
        return ProjectListResponse(
            projects=projects,
            total=len(projects)
        )
    except Exception as e:
        logger.error(f"Error listing projects: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve projects: {str(e)}")


@router.get("/{project_id}", response_model=Project)
async def get_project(
    project_id: UUID = Path(..., description="Project UUID")
):
    """Get specific project by ID"""
    try:
        project = await project_service.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve project: {str(e)}")


@router.get("/{project_id}/tasks", response_model=ProjectTasksResponse)
async def get_project_tasks(
    project_id: UUID = Path(..., description="Project UUID")
):
    """Get tasks for a specific project"""
    try:
        # Verify project exists
        project = await project_service.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        tasks = await project_service.get_project_tasks(project_id)
        return ProjectTasksResponse(
            tasks=tasks,
            total=len(tasks),
            project_id=project_id
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tasks for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve project tasks: {str(e)}")


@router.get("/{project_id}/metrics", response_model=ProjectMetricsResponse)
async def get_project_metrics(
    project_id: UUID = Path(..., description="Project UUID")
):
    """Get metrics for a specific project"""
    try:
        # Verify project exists
        project = await project_service.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        metrics = await project_service.get_project_metrics(project_id)
        return ProjectMetricsResponse(
            metrics=metrics,
            project_id=project_id,
            updated_at=datetime.now()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting metrics for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve project metrics: {str(e)}")


@router.post("/{project_id}/analyze")
async def analyze_project(
    project_id: UUID = Path(..., description="Project UUID")
):
    """Analyze project and update metrics"""
    try:
        # Verify project exists
        project = await project_service.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        analysis_result = await project_service.analyze_project(project_id)
        return {
            "status": "success",
            "project_id": project_id,
            "analysis": analysis_result,
            "timestamp": datetime.now()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze project: {str(e)}")


@router.delete("/{project_id}")
async def delete_project(
    project_id: UUID = Path(..., description="Project UUID")
):
    """Delete a project"""
    try:
        # Verify project exists
        project = await project_service.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        success = await project_service.delete_project(project_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete project")
        
        return {
            "status": "success",
            "message": "Project deleted successfully",
            "project_id": project_id,
            "timestamp": datetime.now()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete project: {str(e)}")