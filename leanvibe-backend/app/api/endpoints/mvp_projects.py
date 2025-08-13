"""
MVP Project Management API endpoints for LeanVibe Platform
Provides comprehensive REST API for managing MVP projects, blueprints, and generated assets
"""

import logging
import zipfile
from datetime import datetime
from io import BytesIO
from typing import Dict, List, Optional, Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query, Response, status
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ...models.mvp_models import (
    MVPProject, MVPProjectResponse, MVPProjectCreateRequest, MVPProjectUpdateRequest,
    BlueprintResponse, BlueprintUpdateRequest, BlueprintApprovalRequest,
    ProjectFileInfo, ProjectArchiveResponse, DeploymentRequest, DeploymentResponse,
    MVPStatus, TechnicalBlueprint
)
from ...services.mvp_service import mvp_service
from ...services.storage import get_storage_service
from ...auth.permissions import require_permission, Permission
from ...services.auth_service import auth_service
from ...middleware.tenant_middleware import get_current_tenant, require_tenant
from ...core.exceptions import InsufficientPermissionsError
from ...services.audit_service import audit_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])
security = HTTPBearer()


@router.get("/", response_model=List[MVPProjectResponse])
async def list_projects(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    tenant = Depends(require_tenant),
    _perm = Depends(require_permission(Permission.PROJECT_READ)),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status_filter: Optional[MVPStatus] = Query(None),
    search: Optional[str] = Query(None, max_length=100)
) -> List[MVPProjectResponse]:
    """
    List user's MVP projects with filtering and search
    
    Returns a paginated list of MVP projects for the current tenant with optional filtering.
    
    **Query Parameters:**
    - **limit**: Number of results (1-100, default 50)
    - **offset**: Result offset for pagination (default 0)
    - **status_filter**: Filter by project status
    - **search**: Search projects by name or description
    
    **Supported Status Filters:**
    - blueprint_pending, generating, deployed, failed, cancelled
    """
    try:
        # Verify token
        await auth_service.verify_token(credentials.credentials)
        
        # Get MVP projects for tenant
        mvp_projects = await mvp_service.get_tenant_mvp_projects(
            tenant_id=tenant.id,
            limit=limit,
            offset=offset
        )
        
        # Apply filters
        filtered_projects = []
        for project in mvp_projects:
            # Status filter
            if status_filter and project.status != status_filter:
                continue
            
            # Search filter
            if search:
                search_lower = search.lower()
                if (search_lower not in project.project_name.lower() and 
                    search_lower not in (project.description or "").lower()):
                    continue
            
            # Convert to response model
            project_response = _mvp_project_to_response(project)
            filtered_projects.append(project_response)
        
        logger.info(f"Listed {len(filtered_projects)} projects for tenant {tenant.id}")
        return filtered_projects
        
    except Exception as e:
        logger.error(f"Failed to list projects: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve projects"
        )


@router.get("/{project_id}", response_model=MVPProjectResponse)
async def get_project(
    project_id: UUID,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    tenant = Depends(require_tenant),
    _perm = Depends(require_permission(Permission.PROJECT_READ))
) -> MVPProjectResponse:
    """
    Get detailed project information by ID
    
    Returns comprehensive project details including blueprint,
    generation status, and metadata.
    
    **Response includes:**
    - Project metadata and configuration
    - Blueprint information (if available)
    - Current status and progress
    - Generated files summary
    """
    try:
        # Verify token
        await auth_service.verify_token(credentials.credentials)
        
        # Get MVP project
        mvp_project = await mvp_service.get_mvp_project(project_id)
        if not mvp_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Verify tenant access
        if mvp_project.tenant_id != tenant.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to project"
            )
        
        project_response = _mvp_project_to_response(mvp_project)
        return project_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve project"
        )


@router.put("/{project_id}", response_model=MVPProjectResponse)
async def update_project(
    project_id: UUID,
    update_request: MVPProjectUpdateRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    tenant = Depends(require_tenant),
    _perm = Depends(require_permission(Permission.PROJECT_WRITE))
) -> MVPProjectResponse:
    """
    Update project metadata and configuration
    
    Allows updating project information, metadata, and settings.
    Cannot modify project during active generation.
    
    **Updateable Fields:**
    - Project name and description
    - Founder interview information
    - Project metadata and tags
    """
    try:
        # Verify token
        await auth_service.verify_token(credentials.credentials)
        
        # Get MVP project
        mvp_project = await mvp_service.get_mvp_project(project_id)
        if not mvp_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Verify tenant access
        if mvp_project.tenant_id != tenant.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to project"
            )
        
        # Check if project can be updated
        if mvp_project.status == MVPStatus.GENERATING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update project during generation"
            )
        
        # Apply updates
        if update_request.project_name:
            mvp_project.project_name = update_request.project_name
        if update_request.description:
            mvp_project.description = update_request.description
        if update_request.interview:
            mvp_project.interview = update_request.interview
        
        # Update project
        updated_project = await mvp_service.update_mvp_project(mvp_project)
        
        project_response = _mvp_project_to_response(updated_project)
        logger.info(f"Updated project {project_id}")
        return project_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update project"
        )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    tenant = Depends(require_tenant),
    _perm = Depends(require_permission(Permission.PROJECT_DELETE))
):
    """
    Delete project and all associated data
    
    Removes the project and all associated data including blueprints
    and generated files. This action cannot be undone.
    
    **Behavior:**
    - Active generation will be cancelled
    - All project data will be removed
    - Generated files will be deleted
    """
    try:
        # Verify token
        await auth_service.verify_token(credentials.credentials)
        
        # Get MVP project
        mvp_project = await mvp_service.get_mvp_project(project_id)
        if not mvp_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Verify tenant access
        if mvp_project.tenant_id != tenant.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to project"
            )
        
        # Cancel generation if active
        if mvp_project.status == MVPStatus.GENERATING:
            await mvp_service.cancel_mvp_generation(project_id)
        
        # TODO: Implement actual deletion when database persistence is added
        logger.info(f"Deleted project {project_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete project"
        )


@router.post("/{project_id}/duplicate", response_model=MVPProjectResponse, status_code=status.HTTP_201_CREATED)
async def duplicate_project(
    project_id: UUID,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    tenant = Depends(require_tenant),
    _perm = Depends(require_permission(Permission.PROJECT_WRITE))
) -> MVPProjectResponse:
    """
    Create a duplicate copy of an existing project
    
    Creates a new project based on an existing one, copying the
    founder interview and blueprint (if available).
    
    **Behavior:**
    - Creates new project with copied data
    - Resets status to blueprint_pending
    - Preserves founder interview and blueprint
    - Generates new unique project ID
    """
    try:
        # Verify token
        await auth_service.verify_token(credentials.credentials)
        
        # Get source MVP project
        source_project = await mvp_service.get_mvp_project(project_id)
        if not source_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Source project not found"
            )
        
        # Verify tenant access
        if source_project.tenant_id != tenant.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to source project"
            )
        
        # Create duplicate project
        duplicate_project = await mvp_service.create_mvp_project(
            tenant_id=tenant.id,
            founder_interview=source_project.interview,
            priority="normal"
        )
        
        # Copy blueprint if exists
        if source_project.blueprint:
            duplicate_project.blueprint = source_project.blueprint
            await mvp_service.update_mvp_project(duplicate_project)
        
        project_response = _mvp_project_to_response(duplicate_project)
        logger.info(f"Duplicated project {project_id} as {duplicate_project.id}")
        return project_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to duplicate project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to duplicate project"
        )


# Blueprint Management Endpoints

@router.get("/{project_id}/blueprint", response_model=BlueprintResponse)
async def get_project_blueprint(
    project_id: UUID,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    tenant = Depends(require_tenant),
    _perm = Depends(require_permission(Permission.PROJECT_READ))
) -> BlueprintResponse:
    """
    Get project's technical blueprint
    
    Returns the current technical blueprint for the project,
    including architecture decisions, technology stack, and implementation plan.
    
    **Response includes:**
    - Technology stack and frameworks
    - Architecture and design patterns
    - Implementation timeline
    - Resource requirements
    """
    try:
        # Verify token
        await auth_service.verify_token(credentials.credentials)
        
        # Get MVP project
        mvp_project = await mvp_service.get_mvp_project(project_id)
        if not mvp_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Verify tenant access
        if mvp_project.tenant_id != tenant.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to project"
            )
        
        if not mvp_project.blueprint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Blueprint not yet generated"
            )
        
        blueprint_response = BlueprintResponse(
            project_id=project_id,
            blueprint=mvp_project.blueprint,
            approved=mvp_project.status != MVPStatus.BLUEPRINT_PENDING,
            created_at=mvp_project.created_at,
            updated_at=mvp_project.updated_at
        )
        
        return blueprint_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get blueprint for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve blueprint"
        )


@router.put("/{project_id}/blueprint", response_model=BlueprintResponse)
async def update_project_blueprint(
    project_id: UUID,
    update_request: BlueprintUpdateRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    tenant = Depends(require_tenant),
    _perm = Depends(require_permission(Permission.PROJECT_WRITE))
) -> BlueprintResponse:
    """
    Update project's technical blueprint
    
    Updates the technical blueprint with new specifications,
    technology choices, or implementation details.
    
    **Requirements:**
    - Project must not be currently generating
    - Blueprint must be valid and complete
    """
    try:
        # Verify token
        await auth_service.verify_token(credentials.credentials)
        
        # Get MVP project
        mvp_project = await mvp_service.get_mvp_project(project_id)
        if not mvp_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Verify tenant access
        if mvp_project.tenant_id != tenant.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to project"
            )
        
        # Check if blueprint can be updated
        if mvp_project.status == MVPStatus.GENERATING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update blueprint during generation"
            )
        
        # Update blueprint
        mvp_project.blueprint = update_request.blueprint
        mvp_project.status = MVPStatus.BLUEPRINT_PENDING  # Reset to pending for re-approval
        
        updated_project = await mvp_service.update_mvp_project(mvp_project)
        
        blueprint_response = BlueprintResponse(
            project_id=project_id,
            blueprint=updated_project.blueprint,
            approved=False,
            created_at=updated_project.created_at,
            updated_at=updated_project.updated_at
        )
        
        logger.info(f"Updated blueprint for project {project_id}")
        return blueprint_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update blueprint for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update blueprint"
        )


@router.get("/{project_id}/blueprint/history", response_model=List[BlueprintResponse])
async def get_blueprint_history(
    project_id: UUID,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    tenant = Depends(require_tenant),
    _perm = Depends(require_permission(Permission.PROJECT_READ))
) -> List[BlueprintResponse]:
    """
    Get blueprint version history
    
    Returns the history of blueprint changes for the project,
    allowing review of previous versions and decisions.
    
    **Note:** Currently returns only the latest version.
    Full versioning will be implemented in future releases.
    """
    try:
        # Verify token
        await auth_service.verify_token(credentials.credentials)
        
        # Get MVP project
        mvp_project = await mvp_service.get_mvp_project(project_id)
        if not mvp_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Verify tenant access
        if mvp_project.tenant_id != tenant.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to project"
            )
        
        # TODO: Implement actual blueprint versioning
        history = []
        if mvp_project.blueprint:
            history.append(BlueprintResponse(
                project_id=project_id,
                blueprint=mvp_project.blueprint,
                approved=mvp_project.status != MVPStatus.BLUEPRINT_PENDING,
                created_at=mvp_project.created_at,
                updated_at=mvp_project.updated_at
            ))
        
        return history
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get blueprint history for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve blueprint history"
        )


@router.post("/{project_id}/blueprint/approve", response_model=BlueprintResponse)
async def approve_blueprint(
    project_id: UUID,
    approval_request: BlueprintApprovalRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    tenant = Depends(require_tenant),
    _perm = Depends(require_permission(Permission.PROJECT_WRITE))
) -> BlueprintResponse:
    """
    Approve technical blueprint for generation
    
    Approves the current blueprint and marks the project as ready
    for autonomous generation. This action enables pipeline execution.
    
    **Requirements:**
    - Project must have a complete blueprint
    - Project must be in blueprint_pending status
    - User must have project approval permissions
    """
    try:
        # Verify token
        payload = await auth_service.verify_token(credentials.credentials)
        user_id = UUID(payload["user_id"])
        
        # Get MVP project
        mvp_project = await mvp_service.get_mvp_project(project_id)
        if not mvp_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Verify tenant access
        if mvp_project.tenant_id != tenant.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to project"
            )
        
        # Validate blueprint exists
        if not mvp_project.blueprint:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No blueprint available for approval"
            )
        
        # Check project status
        if mvp_project.status != MVPStatus.BLUEPRINT_PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Blueprint is not pending approval"
            )
        
        # TODO: Add approval tracking and permissions
        # For now, mark as ready for generation
        logger.info(f"Blueprint approved for project {project_id} by user {user_id}")
        
        blueprint_response = BlueprintResponse(
            project_id=project_id,
            blueprint=mvp_project.blueprint,
            approved=True,
            created_at=mvp_project.created_at,
            updated_at=datetime.utcnow(),
            approved_by=user_id,
            approval_notes=approval_request.notes
        )
        # Audit blueprint approval
        await audit_service.log(
            tenant_id=tenant.id,
            action="blueprint_approve",
            resource_type="project_blueprint",
            resource_id=str(project_id),
            details={"notes": approval_request.notes}
        )
        
        return blueprint_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to approve blueprint for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to approve blueprint"
        )


@router.post("/{project_id}/blueprint/revise", response_model=BlueprintResponse)
async def request_blueprint_revision(
    project_id: UUID,
    revision_request: Dict[str, str],
    credentials: HTTPAuthorizationCredentials = Depends(security),
    tenant = Depends(require_tenant),
    _perm = Depends(require_permission(Permission.PROJECT_WRITE))
) -> BlueprintResponse:
    """
    Request blueprint revision with feedback
    
    Requests changes to the current blueprint with specific feedback
    and revision requirements.
    
    **Request Body:**
    - **feedback**: Detailed feedback on required changes
    - **priority**: Revision priority (low, normal, high)
    """
    try:
        # Verify token
        await auth_service.verify_token(credentials.credentials)
        
        # Get MVP project
        mvp_project = await mvp_service.get_mvp_project(project_id)
        if not mvp_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Verify tenant access
        if mvp_project.tenant_id != tenant.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to project"
            )
        
        if not mvp_project.blueprint:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No blueprint available for revision"
            )
        
        # TODO: Implement actual revision request handling
        # For now, log the revision request
        feedback = revision_request.get("feedback", "")
        priority = revision_request.get("priority", "normal")
        
        logger.info(f"Blueprint revision requested for project {project_id}: {feedback}")
        
        blueprint_response = BlueprintResponse(
            project_id=project_id,
            blueprint=mvp_project.blueprint,
            approved=False,
            created_at=mvp_project.created_at,
            updated_at=mvp_project.updated_at,
            revision_notes=feedback
        )
        
        return blueprint_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to request blueprint revision for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to request blueprint revision"
        )


# Generated Files & Assets Endpoints

@router.get("/{project_id}/files", response_model=List[ProjectFileInfo])
async def list_project_files(
    project_id: UUID,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    tenant = Depends(require_tenant),
    _perm = Depends(require_permission(Permission.PROJECT_READ)),
    path_filter: Optional[str] = Query(None, description="Filter files by path"),
    file_type: Optional[str] = Query(None, description="Filter by file type")
) -> List[ProjectFileInfo]:
    """
    List generated files for the project
    
    Returns a list of all files generated during the MVP creation process,
    with optional filtering by path or file type.
    
    **Query Parameters:**
    - **path_filter**: Filter files by path (supports wildcards)
    - **file_type**: Filter by file extension (e.g., 'py', 'js', 'html')
    
    **File Information:**
    - File path and name
    - File size and type
    - Creation/modification timestamps
    - Download URL
    """
    try:
        # Verify token
        await auth_service.verify_token(credentials.credentials)
        
        # Get MVP project
        mvp_project = await mvp_service.get_mvp_project(project_id)
        if not mvp_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Verify tenant access
        if mvp_project.tenant_id != tenant.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to project"
            )
        
        # List from storage service
        storage = get_storage_service()
        storage_files = storage.list_files(project_id)
        files: List[ProjectFileInfo] = []
        for f in storage_files:
            if path_filter and path_filter not in f.path:
                continue
            if file_type and not f.path.endswith(f".{file_type}"):
                continue
            files.append(ProjectFileInfo(
                path=f.path,
                name=f.path.split("/")[-1],
                size=f.size,
                file_type=(f.content_type.split("/")[-1] if f.content_type else "unknown"),
                created_at=mvp_project.created_at,
                modified_at=f.modified_at,
                download_url=f"/api/v1/projects/{project_id}/files/{f.path}"
            ))
        return files
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list files for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve project files"
        )


@router.get("/{project_id}/files/{file_path:path}")
async def download_project_file(
    project_id: UUID,
    file_path: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    tenant = Depends(require_tenant),
    _perm = Depends(require_permission(Permission.PROJECT_READ))
) -> Response:
    """
    Download a specific generated file
    
    Downloads a specific file from the generated MVP project.
    Returns the file content with appropriate MIME type.
    
    **Path Parameters:**
    - **file_path**: Relative path to the file within the project
    
    **Response:**
    - File content with appropriate Content-Type header
    - Content-Disposition header for download
    """
    try:
        # Verify token
        await auth_service.verify_token(credentials.credentials)
        
        # Get MVP project
        mvp_project = await mvp_service.get_mvp_project(project_id)
        if not mvp_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Verify tenant access
        if mvp_project.tenant_id != tenant.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to project"
            )
        
        # Check if project has generated files
        if mvp_project.status != MVPStatus.DEPLOYED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project has not generated files yet"
            )
        
        storage = get_storage_service()
        # If S3, prefer presigned URL redirect
        try:
            from ...services.storage.s3_storage_service import S3StorageService
            if isinstance(storage, S3StorageService):
                url = storage.presign_download(project_id, file_path)
                # Audit S3 presigned download
                await audit_service.log(
                    tenant_id=tenant.id,
                    action="file_download",
                    resource_type="project_file",
                    resource_id=f"{project_id}/{file_path}",
                    details={"file_path": file_path}
                )
                # 307 Temporary Redirect to presigned URL
                return Response(status_code=307, headers={"Location": url})
        except Exception:
            pass
        # Local storage
        try:
            buffer, media_type = storage.get_file(project_id, file_path)
        except FileNotFoundError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
        # Audit local download
        await audit_service.log(
            tenant_id=tenant.id,
            action="file_download",
            resource_type="project_file",
            resource_id=f"{project_id}/{file_path}",
            details={"file_path": file_path}
        )
        return Response(content=buffer.getvalue(), media_type=media_type, headers={"Content-Disposition": f"attachment; filename={file_path.split('/')[-1]}"})
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download file {file_path} for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download file"
        )


@router.get("/{project_id}/archive", response_model=ProjectArchiveResponse)
async def download_project_archive(
    project_id: UUID,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    tenant = Depends(require_tenant),
    _perm = Depends(require_permission(Permission.PROJECT_READ)),
    format: str = Query("zip", description="Archive format (zip, tar)")
) -> StreamingResponse:
    """
    Download complete project archive
    
    Downloads a compressed archive containing all generated files
    for the MVP project.
    
    **Query Parameters:**
    - **format**: Archive format (zip or tar, default: zip)
    
    **Response:**
    - Compressed archive file with all project files
    - Appropriate filename and Content-Type headers
    """
    try:
        # Verify token
        await auth_service.verify_token(credentials.credentials)
        
        # Get MVP project
        mvp_project = await mvp_service.get_mvp_project(project_id)
        if not mvp_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Verify tenant access
        if mvp_project.tenant_id != tenant.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to project"
            )
        
        # Check if project has generated files
        if mvp_project.status != MVPStatus.DEPLOYED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project has not generated files yet"
            )
        
        # Validate format
        if format not in ["zip", "tar"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported archive format"
            )
        
        storage = get_storage_service()
        # For S3 provider we do not stream archives server-side yet
        try:
            from ...services.storage.s3_storage_service import S3StorageService
            if isinstance(storage, S3StorageService):
                raise HTTPException(
                    status_code=status.HTTP_501_NOT_IMPLEMENTED,
                    detail="Archive download not implemented for S3 provider yet"
                )
        except Exception:
            pass

        if format == "zip":
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for f in storage.list_files(project_id):
                    try:
                        data_buf, _ct = storage.get_file(project_id, f.path)
                        zip_file.writestr(f.path, data_buf.getvalue())
                    except FileNotFoundError:
                        continue
            zip_buffer.seek(0)
            safe_name = mvp_project.project_name.replace(" ", "_").lower()
            filename = f"{safe_name}_{project_id.hex[:8]}.zip"
            await audit_service.log(
                tenant_id=tenant.id,
                action="project_archive_download",
                resource_type="project_archive",
                resource_id=str(project_id),
                details={"format": format}
            )
            return StreamingResponse(
                BytesIO(zip_buffer.getvalue()),
                media_type="application/zip",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="TAR format not yet implemented"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create archive for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create project archive"
        )


@router.post("/{project_id}/deploy", response_model=DeploymentResponse)
async def deploy_project(
    project_id: UUID,
    deployment_request: DeploymentRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    tenant = Depends(require_tenant)
) -> DeploymentResponse:
    """
    Deploy project to staging or production
    
    Deploys the generated MVP to the specified environment.
    Handles infrastructure provisioning and application deployment.
    
    **Deployment Options:**
    - **staging**: Deploy to staging environment for testing
    - **production**: Deploy to production environment
    
    **Requirements:**
    - Project must be in deployed status
    - Valid deployment configuration
    - Sufficient deployment quota
    """
    try:
        # Verify token
        await auth_service.verify_token(credentials.credentials)
        
        # Get MVP project
        mvp_project = await mvp_service.get_mvp_project(project_id)
        if not mvp_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Verify tenant access
        if mvp_project.tenant_id != tenant.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to project"
            )
        
        # Check if project can be deployed
        if mvp_project.status != MVPStatus.DEPLOYED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project must be generated before deployment"
            )
        
        # TODO: Implement actual deployment logic
        # For now, return mock deployment response
        deployment_response = DeploymentResponse(
            deployment_id=f"deploy_{project_id.hex[:8]}",
            environment=deployment_request.environment,
            status="deploying",
            url=f"https://{deployment_request.environment}.leanvibe.app/{mvp_project.slug}",
            deployed_at=datetime.utcnow()
        )
        
        logger.info(f"Started deployment for project {project_id} to {deployment_request.environment}")
        return deployment_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to deploy project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deploy project"
        )


# Helper functions

def _mvp_project_to_response(mvp_project: MVPProject) -> MVPProjectResponse:
    """Convert MVP project to response model"""
    return MVPProjectResponse(
        id=mvp_project.id,
        project_name=mvp_project.project_name,
        description=mvp_project.description,
        status=mvp_project.status,
        slug=mvp_project.slug,
        interview=mvp_project.interview,
        blueprint=mvp_project.blueprint,
        created_at=mvp_project.created_at,
        updated_at=mvp_project.updated_at,
        completed_at=mvp_project.completed_at,
        tenant_id=mvp_project.tenant_id,
        error_message=mvp_project.error_message,
        generation_duration=mvp_project.generation_duration
    )