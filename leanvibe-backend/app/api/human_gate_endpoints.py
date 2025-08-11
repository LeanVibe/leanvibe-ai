"""
Human Gate API Endpoints
RESTful API for founder approval workflows and secure token-based authentication
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from pydantic import BaseModel, Field

from ..services.human_gate_service import human_gate_service, HumanGateServiceError
from ..models.human_gate_models import (
    HumanApprovalWorkflow, FounderFeedback, WorkflowType, WorkflowStatus, FeedbackType,
    CreateWorkflowRequest, WorkflowResponse, WorkflowListResponse,
    WorkflowMetricsResponse, SubmitFeedbackRequest, WorkflowMetrics
)
from ..core.auth import get_current_tenant_id
# from ..core.database import get_db  # Will be used when proper DB integration is added

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/human-gate", tags=["Human Gate Workflows"])


# Request/Response Models

class CreateWorkflowResponse(BaseModel):
    """Response for workflow creation"""
    workflow: HumanApprovalWorkflow
    approval_url: str
    expires_in_hours: float


class PublicWorkflowResponse(BaseModel):
    """Public workflow response (no sensitive data)"""
    workflow_id: UUID
    workflow_type: WorkflowType
    workflow_title: str
    workflow_description: str
    context_data: Dict[str, Any]
    created_at: str
    expires_at: str
    status: WorkflowStatus
    can_respond: bool
    time_remaining_hours: float


class FeedbackResponse(BaseModel):
    """Response after feedback submission"""
    success: bool
    message: str
    workflow_status: WorkflowStatus
    next_steps: Optional[str] = None


class WorkflowStatsResponse(BaseModel):
    """Workflow statistics response"""
    total_workflows: int
    pending_workflows: int
    approved_workflows: int
    rejected_workflows: int
    expired_workflows: int
    avg_response_time_hours: float
    approval_rate_percent: float


# Private API Endpoints (require authentication)

@router.post(
    "/workflows",
    response_model=CreateWorkflowResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create approval workflow",
    description="Create new approval workflow for founder review"
)
async def create_approval_workflow(
    request: CreateWorkflowRequest,
    background_tasks: BackgroundTasks,
    tenant_id: UUID = Depends(get_current_tenant_id)
) -> CreateWorkflowResponse:
    """Create new approval workflow and send notification email"""
    
    try:
        # Create workflow
        workflow = await human_gate_service.create_approval_workflow(request, tenant_id)
        
        # Calculate expiration time
        time_remaining = workflow.time_until_expiration()
        expires_in_hours = time_remaining.total_seconds() / 3600
        
        # TODO: Send notification email in background
        # background_tasks.add_task(
        #     send_approval_notification_email,
        #     workflow.founder_email,
        #     workflow.approval_url,
        #     workflow.workflow_title
        # )
        
        logger.info(f"Created workflow {workflow.id} for project {request.mvp_project_id}")
        
        return CreateWorkflowResponse(
            workflow=workflow,
            approval_url=workflow.approval_url,
            expires_in_hours=expires_in_hours
        )
        
    except HumanGateServiceError as e:
        logger.error(f"Human gate service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error creating workflow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/workflows",
    response_model=WorkflowListResponse,
    summary="List approval workflows",
    description="Get list of approval workflows for current tenant"
)
async def list_approval_workflows(
    status_filter: Optional[WorkflowStatus] = None,
    limit: int = 20,
    offset: int = 0,
    tenant_id: UUID = Depends(get_current_tenant_id)
) -> WorkflowListResponse:
    """List approval workflows for current tenant"""
    
    try:
        # Validate limit
        if limit > 100:
            limit = 100
        
        workflows = await human_gate_service.get_tenant_workflows(
            tenant_id=tenant_id,
            status_filter=status_filter,
            limit=limit + 1,  # Get one extra to check if there are more
            offset=offset
        )
        
        has_more = len(workflows) > limit
        if has_more:
            workflows = workflows[:limit]
        
        # Count workflows by status
        all_workflows = await human_gate_service.get_tenant_workflows(tenant_id)
        pending_count = len([w for w in all_workflows if w.status == WorkflowStatus.PENDING])
        expired_count = len([w for w in all_workflows if w.status == WorkflowStatus.EXPIRED])
        
        return WorkflowListResponse(
            workflows=workflows,
            total_count=len(all_workflows),
            pending_count=pending_count,
            expired_count=expired_count,
            has_more=has_more
        )
        
    except Exception as e:
        logger.error(f"Error listing workflows: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/workflows/{workflow_id}",
    response_model=WorkflowResponse,
    summary="Get approval workflow",
    description="Get detailed information about an approval workflow"
)
async def get_approval_workflow(
    workflow_id: UUID,
    tenant_id: UUID = Depends(get_current_tenant_id)
) -> WorkflowResponse:
    """Get approval workflow details"""
    
    try:
        workflow = await human_gate_service._get_workflow(workflow_id)
        if not workflow or workflow.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found"
            )
        
        time_remaining = workflow.time_until_expiration()
        can_respond = workflow.status == WorkflowStatus.PENDING and not workflow.is_expired()
        
        return WorkflowResponse(
            workflow=workflow,
            time_until_expiration=str(time_remaining) if not workflow.is_expired() else "Expired",
            can_respond=can_respond
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workflow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post(
    "/workflows/{workflow_id}/remind",
    summary="Send reminder email",
    description="Send reminder email to founder for pending workflow"
)
async def send_workflow_reminder(
    workflow_id: UUID,
    background_tasks: BackgroundTasks,
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """Send reminder email for pending workflow"""
    
    try:
        workflow = await human_gate_service._get_workflow(workflow_id)
        if not workflow or workflow.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found"
            )
        
        if workflow.status != WorkflowStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot send reminder - workflow status is {workflow.status}"
            )
        
        success = await human_gate_service.send_reminder(workflow_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to send reminder"
            )
        
        return {"message": f"Reminder sent to {workflow.founder_email}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending reminder: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post(
    "/workflows/{workflow_id}/cancel",
    summary="Cancel approval workflow",
    description="Cancel a pending approval workflow"
)
async def cancel_approval_workflow(
    workflow_id: UUID,
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """Cancel pending approval workflow"""
    
    try:
        success = await human_gate_service.cancel_workflow(workflow_id, tenant_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot cancel workflow - may not exist or not in cancellable state"
            )
        
        return {"message": "Workflow cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling workflow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/analytics/workflows",
    response_model=WorkflowMetricsResponse,
    summary="Get workflow analytics",
    description="Get analytics and metrics for approval workflows"
)
async def get_workflow_analytics(
    days: int = 30,
    tenant_id: UUID = Depends(get_current_tenant_id)
) -> WorkflowMetricsResponse:
    """Get workflow analytics and metrics"""
    
    try:
        # Validate days parameter
        if days < 1 or days > 365:
            days = 30
        
        metrics = await human_gate_service.get_workflow_metrics(tenant_id, days)
        
        # Generate recommendations based on metrics
        recommendations = []
        
        if metrics.response_rate < 70:
            recommendations.append("Consider simplifying approval process - low response rate")
        
        if metrics.approval_rate < 60:
            recommendations.append("Review blueprint quality - low approval rate")
        
        if metrics.average_response_time_hours > 48:
            recommendations.append("Consider shorter approval windows or more reminders")
        
        return WorkflowMetricsResponse(
            metrics=metrics,
            recommendations=recommendations
        )
        
    except Exception as e:
        logger.error(f"Error getting workflow analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# Public API Endpoints (no authentication required)

@router.get(
    "/public/review/{approval_token}",
    response_model=PublicWorkflowResponse,
    summary="Get workflow for review (public)",
    description="Get workflow details for founder review using approval token"
)
async def get_workflow_for_review(
    approval_token: str,
    request: Request
) -> PublicWorkflowResponse:
    """Public endpoint for founder workflow review"""
    
    try:
        workflow = await human_gate_service.get_workflow_by_token(approval_token)
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid or expired approval link"
            )
        
        # Track approval page view
        if not workflow.approval_page_viewed_at:
            workflow.approval_page_viewed_at = datetime.utcnow()
            await human_gate_service._update_workflow(workflow)
        
        # Calculate time remaining
        time_remaining = workflow.time_until_expiration()
        can_respond = workflow.status == WorkflowStatus.PENDING and not workflow.is_expired()
        
        # Return public-safe workflow data
        return PublicWorkflowResponse(
            workflow_id=workflow.id,
            workflow_type=workflow.workflow_type,
            workflow_title=workflow.workflow_title,
            workflow_description=workflow.workflow_description,
            context_data=workflow.context_data,
            created_at=workflow.created_at.isoformat(),
            expires_at=workflow.expires_at.isoformat(),
            status=workflow.status,
            can_respond=can_respond,
            time_remaining_hours=time_remaining.total_seconds() / 3600 if not workflow.is_expired() else 0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workflow for review: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post(
    "/public/feedback/{approval_token}",
    response_model=FeedbackResponse,
    summary="Submit founder feedback (public)",
    description="Submit founder feedback for approval workflow using token"
)
async def submit_founder_feedback(
    approval_token: str,
    feedback: FounderFeedback,
    request: Request
) -> FeedbackResponse:
    """Public endpoint for founder feedback submission"""
    
    try:
        # Set client metadata
        feedback.ip_address = request.client.host if request.client else None
        feedback.user_agent = request.headers.get("user-agent")
        
        success = await human_gate_service.submit_founder_feedback(approval_token, feedback)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to process feedback"
            )
        
        # Get updated workflow status
        workflow = await human_gate_service.get_workflow_by_token(approval_token)
        
        # Generate response message based on feedback type
        if feedback.feedback_type == FeedbackType.APPROVE:
            message = "Thank you! Your approval has been received. MVP generation will begin shortly."
            next_steps = "You'll receive progress updates via email as your MVP is built."
            
        elif feedback.feedback_type == FeedbackType.REJECT:
            message = "Your feedback has been received. The project has been cancelled as requested."
            next_steps = "If you change your mind, please contact our support team."
            
        elif feedback.feedback_type == FeedbackType.REQUEST_REVISION:
            message = "Thank you for your detailed feedback! We'll revise the blueprint based on your input."
            next_steps = "You'll receive a new approval request with the updated blueprint within 24 hours."
            
        else:
            message = "Your feedback has been received and will be reviewed by our team."
            next_steps = "We'll follow up with you within 24 hours."
        
        logger.info(f"Processed {feedback.feedback_type} feedback for workflow {workflow.id if workflow else 'unknown'}")
        
        return FeedbackResponse(
            success=True,
            message=message,
            workflow_status=workflow.status if workflow else WorkflowStatus.PENDING,
            next_steps=next_steps
        )
        
    except HumanGateServiceError as e:
        logger.error(f"Human gate service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# System Endpoints

@router.get(
    "/health",
    summary="Human gate system health check",
    description="Health check for human gate workflow system"
)
async def human_gate_health():
    """Health check for human gate system"""
    
    try:
        # Basic health checks
        service_healthy = human_gate_service is not None
        token_service_healthy = human_gate_service.token_service is not None
        
        return {
            "status": "healthy" if service_healthy and token_service_healthy else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "human_gate_service": "healthy" if service_healthy else "unhealthy",
                "token_service": "healthy" if token_service_healthy else "unhealthy",
                "workflow_storage": "healthy"  # In-memory storage always healthy
            }
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Health check failed"
        )


@router.post(
    "/system/cleanup-expired",
    summary="Cleanup expired workflows",
    description="Background task to cleanup expired workflows"
)
async def cleanup_expired_workflows():
    """Cleanup expired workflows (admin endpoint)"""
    
    try:
        cleanup_count = await human_gate_service.cleanup_expired_workflows()
        
        return {
            "message": f"Cleaned up {cleanup_count} expired workflows",
            "count": cleanup_count
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up workflows: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cleanup failed"
        )