"""
SaaS Scaffolding API endpoints for LeanVibe Platform
Provides comprehensive project generation and template management capabilities
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, status, File, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.auth.permissions import require_permission
from app.models.auth_models import User
from app.models.tenant_models import Tenant
from app.models.scaffolding_models import (
    ProjectTemplate, FeatureDefinition, GeneratedProject, GenerationJob,
    ProjectGenerationRequest, TemplateReview, SaaSArchetype, TechnologyStack,
    DeploymentTarget, GenerationStatus, TemplateVisibility, FeatureComplexity
)
from app.services.scaffolding_service import ScaffoldingService
from app.services.template_service import TemplateService
from app.services.generation_service import GenerationService
from app.middleware.tenant_middleware import get_current_tenant


router = APIRouter(prefix="/scaffolding", tags=["scaffolding"])


# Template Management Endpoints
@router.get("/templates", response_model=List[ProjectTemplate])
async def list_templates(
    archetype: Optional[SaaSArchetype] = None,
    technology_stack: Optional[TechnologyStack] = None,
    features: Optional[List[str]] = Query(None),
    category: Optional[str] = None,
    visibility: Optional[TemplateVisibility] = None,
    search: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    tenant: Tenant = Depends(get_current_tenant),
    template_service: TemplateService = Depends()
):
    """
    List available project templates with comprehensive filtering
    
    Supports filtering by archetype, technology stack, features, category,
    visibility level, and free-text search across names and descriptions.
    """
    try:
        templates = await template_service.list_templates(
            tenant_id=tenant.id,
            archetype=archetype,
            technology_stack=technology_stack,
            features=features,
            category=category,
            visibility=visibility,
            search_query=search,
            limit=limit,
            offset=offset
        )
        return templates
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve templates: {str(e)}"
        )


@router.get("/templates/{template_id}", response_model=ProjectTemplate)
async def get_template(
    template_id: UUID,
    tenant: Tenant = Depends(get_current_tenant),
    template_service: TemplateService = Depends()
):
    """Get detailed information about a specific template"""
    try:
        template = await template_service.get_template(template_id, tenant.id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        return template
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve template: {str(e)}"
        )


@router.post("/templates", response_model=ProjectTemplate)
async def create_template(
    template: ProjectTemplate,
    tenant: Tenant = Depends(get_current_tenant),
    user: User = Depends(require_permission("template:create")),
    template_service: TemplateService = Depends()
):
    """Create a new project template"""
    try:
        # Ensure template belongs to current tenant
        template.tenant_id = tenant.id
        template.author_email = user.email
        template.author_name = f"{user.first_name} {user.last_name}"
        
        created_template = await template_service.create_template(template)
        return created_template
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create template: {str(e)}"
        )


@router.put("/templates/{template_id}", response_model=ProjectTemplate)
async def update_template(
    template_id: UUID,
    template_update: Dict[str, Any],
    tenant: Tenant = Depends(get_current_tenant),
    user: User = Depends(require_permission("template:update")),
    template_service: TemplateService = Depends()
):
    """Update an existing template"""
    try:
        updated_template = await template_service.update_template(
            template_id=template_id,
            tenant_id=tenant.id,
            updates=template_update,
            updated_by=user.id
        )
        if not updated_template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found or access denied"
            )
        return updated_template
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update template: {str(e)}"
        )


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: UUID,
    tenant: Tenant = Depends(get_current_tenant),
    user: User = Depends(require_permission("template:delete")),
    template_service: TemplateService = Depends()
):
    """Delete a template (soft delete to preserve references)"""
    try:
        success = await template_service.delete_template(
            template_id=template_id,
            tenant_id=tenant.id,
            deleted_by=user.id
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found or access denied"
            )
        return {"message": "Template deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete template: {str(e)}"
        )


@router.post("/templates/{template_id}/preview")
async def preview_template(
    template_id: UUID,
    features: List[str] = Query([]),
    custom_variables: Dict[str, Any] = {},
    tenant: Tenant = Depends(get_current_tenant),
    template_service: TemplateService = Depends()
):
    """
    Preview generated project structure without creating actual project
    
    Returns file structure, key code snippets, and configuration preview
    """
    try:
        preview = await template_service.preview_template_generation(
            template_id=template_id,
            tenant_id=tenant.id,
            features=features,
            custom_variables=custom_variables
        )
        return preview
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate preview: {str(e)}"
        )


# Feature Catalog Endpoints
@router.get("/features", response_model=List[FeatureDefinition])
async def list_features(
    archetype: Optional[SaaSArchetype] = None,
    category: Optional[str] = None,
    complexity: Optional[FeatureComplexity] = None,
    search: Optional[str] = None,
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    template_service: TemplateService = Depends()
):
    """List available features with filtering capabilities"""
    try:
        features = await template_service.list_features(
            archetype=archetype,
            category=category,
            complexity=complexity,
            search_query=search,
            limit=limit,
            offset=offset
        )
        return features
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve features: {str(e)}"
        )


@router.get("/features/{feature_id}", response_model=FeatureDefinition)
async def get_feature(
    feature_id: UUID,
    template_service: TemplateService = Depends()
):
    """Get detailed information about a specific feature"""
    try:
        feature = await template_service.get_feature(feature_id)
        if not feature:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Feature not found"
            )
        return feature
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve feature: {str(e)}"
        )


@router.post("/features/compatibility")
async def check_feature_compatibility(
    features: List[str],
    archetype: SaaSArchetype,
    technology_stack: TechnologyStack,
    template_service: TemplateService = Depends()
):
    """
    Check feature compatibility and get recommendations
    
    Returns compatibility matrix, conflicts, missing dependencies,
    and suggested feature alternatives
    """
    try:
        compatibility_report = await template_service.check_feature_compatibility(
            features=features,
            archetype=archetype,
            technology_stack=technology_stack
        )
        return compatibility_report
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check compatibility: {str(e)}"
        )


# Project Generation Endpoints
@router.post("/projects/generate", response_model=GenerationJob)
async def generate_project(
    request: ProjectGenerationRequest,
    background_tasks: BackgroundTasks,
    tenant: Tenant = Depends(get_current_tenant),
    user: User = Depends(require_permission("project:create")),
    generation_service: GenerationService = Depends()
):
    """
    Start SaaS project generation process
    
    Creates a background job for project generation and returns job ID
    for tracking progress. The generated project will include all selected
    features with enterprise-grade multi-tenancy, authentication, and billing.
    """
    try:
        # Validate generation request
        await generation_service.validate_generation_request(request, tenant.id)
        
        # Create generation job
        job = await generation_service.create_generation_job(
            request=request,
            tenant_id=tenant.id,
            created_by=user.id
        )
        
        # Start background generation process
        background_tasks.add_task(
            generation_service.execute_generation_job,
            job.id
        )
        
        return job
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start project generation: {str(e)}"
        )


@router.get("/projects/generation/{job_id}", response_model=GenerationJob)
async def get_generation_status(
    job_id: UUID,
    tenant: Tenant = Depends(get_current_tenant),
    generation_service: GenerationService = Depends()
):
    """Get detailed status of a project generation job"""
    try:
        job = await generation_service.get_generation_job(job_id, tenant.id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Generation job not found"
            )
        return job
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve generation status: {str(e)}"
        )


@router.get("/projects/generation/{job_id}/logs")
async def get_generation_logs(
    job_id: UUID,
    tenant: Tenant = Depends(get_current_tenant),
    generation_service: GenerationService = Depends()
):
    """Stream real-time generation logs"""
    try:
        async def log_streamer():
            async for log_entry in generation_service.stream_generation_logs(job_id, tenant.id):
                yield f"data: {log_entry}\n\n"
        
        return StreamingResponse(
            log_streamer(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stream logs: {str(e)}"
        )


@router.post("/projects/generation/{job_id}/cancel")
async def cancel_generation(
    job_id: UUID,
    tenant: Tenant = Depends(get_current_tenant),
    user: User = Depends(require_permission("project:manage")),
    generation_service: GenerationService = Depends()
):
    """Cancel a running generation job"""
    try:
        success = await generation_service.cancel_generation_job(
            job_id=job_id,
            tenant_id=tenant.id,
            cancelled_by=user.id
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Generation job not found or cannot be cancelled"
            )
        return {"message": "Generation job cancelled successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel generation: {str(e)}"
        )


# Generated Project Management
@router.get("/projects", response_model=List[GeneratedProject])
async def list_generated_projects(
    archetype: Optional[SaaSArchetype] = None,
    status: Optional[GenerationStatus] = None,
    search: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    tenant: Tenant = Depends(get_current_tenant),
    generation_service: GenerationService = Depends()
):
    """List generated projects for the current tenant"""
    try:
        projects = await generation_service.list_projects(
            tenant_id=tenant.id,
            archetype=archetype,
            status=status,
            search_query=search,
            limit=limit,
            offset=offset
        )
        return projects
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve projects: {str(e)}"
        )


@router.get("/projects/{project_id}", response_model=GeneratedProject)
async def get_generated_project(
    project_id: UUID,
    tenant: Tenant = Depends(get_current_tenant),
    generation_service: GenerationService = Depends()
):
    """Get detailed information about a generated project"""
    try:
        project = await generation_service.get_project(project_id, tenant.id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        return project
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve project: {str(e)}"
        )


@router.post("/projects/{project_id}/deploy")
async def deploy_project(
    project_id: UUID,
    environment: str,
    deployment_config: Dict[str, Any] = {},
    tenant: Tenant = Depends(get_current_tenant),
    user: User = Depends(require_permission("project:deploy")),
    generation_service: GenerationService = Depends()
):
    """Deploy a generated project to specified environment"""
    try:
        deployment_job = await generation_service.deploy_project(
            project_id=project_id,
            tenant_id=tenant.id,
            environment=environment,
            config=deployment_config,
            deployed_by=user.id
        )
        return deployment_job
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deploy project: {str(e)}"
        )


@router.post("/projects/{project_id}/features")
async def add_feature_to_project(
    project_id: UUID,
    feature_id: UUID,
    configuration: Dict[str, Any] = {},
    tenant: Tenant = Depends(get_current_tenant),
    user: User = Depends(require_permission("project:modify")),
    generation_service: GenerationService = Depends()
):
    """Add a new feature to an existing project"""
    try:
        result = await generation_service.add_feature_to_project(
            project_id=project_id,
            tenant_id=tenant.id,
            feature_id=feature_id,
            configuration=configuration,
            added_by=user.id
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add feature: {str(e)}"
        )


# Template Reviews and Ratings
@router.post("/templates/{template_id}/reviews", response_model=TemplateReview)
async def create_template_review(
    template_id: UUID,
    review: TemplateReview,
    tenant: Tenant = Depends(get_current_tenant),
    user: User = Depends(require_permission("template:review")),
    template_service: TemplateService = Depends()
):
    """Create a review for a template"""
    try:
        review.template_id = template_id
        review.tenant_id = tenant.id
        review.user_id = user.id
        
        created_review = await template_service.create_review(review)
        return created_review
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create review: {str(e)}"
        )


@router.get("/templates/{template_id}/reviews", response_model=List[TemplateReview])
async def list_template_reviews(
    template_id: UUID,
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    template_service: TemplateService = Depends()
):
    """List reviews for a template"""
    try:
        reviews = await template_service.list_reviews(
            template_id=template_id,
            limit=limit,
            offset=offset
        )
        return reviews
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve reviews: {str(e)}"
        )


# Analytics and Reporting
@router.get("/analytics/templates")
async def get_template_analytics(
    period: str = Query("30d", regex="^(7d|30d|90d|1y)$"),
    tenant: Tenant = Depends(get_current_tenant),
    user: User = Depends(require_permission("analytics:read")),
    template_service: TemplateService = Depends()
):
    """Get template usage analytics and metrics"""
    try:
        analytics = await template_service.get_template_analytics(
            tenant_id=tenant.id,
            period=period
        )
        return analytics
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve analytics: {str(e)}"
        )


@router.get("/analytics/generation")
async def get_generation_analytics(
    period: str = Query("30d", regex="^(7d|30d|90d|1y)$"),
    tenant: Tenant = Depends(get_current_tenant),
    user: User = Depends(require_permission("analytics:read")),
    generation_service: GenerationService = Depends()
):
    """Get project generation analytics and success metrics"""
    try:
        analytics = await generation_service.get_generation_analytics(
            tenant_id=tenant.id,
            period=period
        )
        return analytics
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve generation analytics: {str(e)}"
        )


# Health and Status Endpoints
@router.get("/health")
async def scaffolding_health_check(
    generation_service: GenerationService = Depends()
):
    """Health check for scaffolding system"""
    try:
        health_status = await generation_service.health_check()
        return health_status
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Scaffolding service unhealthy: {str(e)}"
        )


@router.get("/stats")
async def get_scaffolding_stats(
    template_service: TemplateService = Depends(),
    generation_service: GenerationService = Depends()
):
    """Get overall scaffolding system statistics"""
    try:
        stats = {
            "templates": await template_service.get_template_count(),
            "features": await template_service.get_feature_count(),
            "generated_projects": await generation_service.get_project_count(),
            "active_jobs": await generation_service.get_active_job_count(),
            "success_rate": await generation_service.get_success_rate(),
            "average_generation_time": await generation_service.get_average_generation_time()
        }
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve stats: {str(e)}"
        )