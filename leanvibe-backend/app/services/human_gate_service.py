"""
Human Gate Service - Founder Approval Workflows
Manages secure token-based approval workflows with email notifications
"""

import asyncio
import logging
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

import jwt
from sqlalchemy import and_
from sqlalchemy.orm import Session

from ..models.human_gate_models import (
    HumanApprovalWorkflow, FounderFeedback, WorkflowType, WorkflowStatus,
    FeedbackType, ApprovalPriority, CreateWorkflowRequest, WorkflowResponse,
    EmailDeliveryLog, WorkflowMetrics
)
from ..models.mvp_models import MVPProject
# from ..core.database import get_db  # Will be imported when needed
# from ..core.config import settings  # Will be imported when needed

logger = logging.getLogger(__name__)


class HumanGateServiceError(Exception):
    """Custom exception for human gate service errors"""
    pass


class SecureTokenService:
    """Secure token generation and validation for approval workflows"""
    
    def __init__(self):
        # In production, this should come from environment variables
        self.secret_key = "your-secret-key-here-replace-in-production"
        self.algorithm = "HS256"
        self.issuer = "leanvibe-startup-factory"
    
    def generate_approval_token(
        self, 
        workflow_id: UUID,
        founder_email: str,
        expires_at: datetime
    ) -> str:
        """Generate secure JWT token for workflow approval"""
        
        payload = {
            "workflow_id": str(workflow_id),
            "founder_email": founder_email,
            "exp": expires_at,
            "iat": datetime.utcnow(),
            "iss": self.issuer,
            "purpose": "workflow_approval",
            "nonce": secrets.token_hex(16)  # Prevent token reuse
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        logger.info(f"Generated approval token for workflow {workflow_id}")
        return token
    
    def validate_approval_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate approval token and return payload if valid"""
        
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm],
                issuer=self.issuer
            )
            
            # Verify token purpose
            if payload.get("purpose") != "workflow_approval":
                logger.warning("Invalid token purpose")
                return None
            
            # Check expiration (JWT already validates exp claim)
            workflow_id = payload.get("workflow_id")
            founder_email = payload.get("founder_email")
            
            if not workflow_id or not founder_email:
                logger.warning("Missing required claims in token")
                return None
                
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Approval token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid approval token: {e}")
            return None
    
    def create_approval_url(
        self, 
        token: str,
        frontend_base_url: str = "https://startup-factory.leanvibe.ai"
    ) -> str:
        """Generate secure approval URL for founder"""
        
        return f"{frontend_base_url}/approve/{token}"


class HumanGateService:
    """Service for managing human approval workflows"""
    
    def __init__(self):
        self.token_service = SecureTokenService()
        # In-memory storage for development/testing
        self._workflows_storage: Dict[UUID, HumanApprovalWorkflow] = {}
        self._workflows_by_token: Dict[str, UUID] = {}
        self._workflows_by_tenant: Dict[UUID, List[UUID]] = {}
        self._email_logs: Dict[UUID, List[EmailDeliveryLog]] = {}
    
    async def create_approval_workflow(
        self,
        request: CreateWorkflowRequest,
        tenant_id: UUID
    ) -> HumanApprovalWorkflow:
        """Create new approval workflow for founder review"""
        
        try:
            workflow_id = uuid4()
            
            # Create workflow record
            workflow = HumanApprovalWorkflow(
                id=workflow_id,
                mvp_project_id=request.mvp_project_id,
                workflow_type=request.workflow_type,
                priority=request.priority,
                founder_email=request.founder_email,
                workflow_title=request.workflow_title,
                workflow_description=request.workflow_description,
                context_data=request.context_data,
                tenant_id=tenant_id,
                approval_token="",  # Will be set below
                approval_url=""     # Will be set below
            )
            
            # Generate secure token
            approval_token = self.token_service.generate_approval_token(
                workflow_id=workflow.id,
                founder_email=workflow.founder_email,
                expires_at=workflow.expires_at
            )
            
            # Generate approval URL
            approval_url = self.token_service.create_approval_url(approval_token)
            
            # Update workflow with token and URL
            workflow.approval_token = approval_token
            workflow.approval_url = approval_url
            
            # Save to storage
            await self._save_workflow(workflow)
            
            logger.info(f"Created approval workflow {workflow_id} for project {request.mvp_project_id}")
            return workflow
            
        except Exception as e:
            logger.error(f"Failed to create approval workflow: {e}")
            raise HumanGateServiceError(f"Workflow creation failed: {str(e)}")
    
    async def get_workflow_by_token(self, approval_token: str) -> Optional[HumanApprovalWorkflow]:
        """Get workflow by approval token (for founder access)"""
        
        # Validate token first
        token_payload = self.token_service.validate_approval_token(approval_token)
        if not token_payload:
            return None
        
        workflow_id = UUID(token_payload["workflow_id"])
        return await self._get_workflow(workflow_id)
    
    async def submit_founder_feedback(
        self,
        approval_token: str,
        feedback: FounderFeedback
    ) -> bool:
        """Process founder feedback for approval workflow"""
        
        try:
            # Validate token and get workflow
            workflow = await self.get_workflow_by_token(approval_token)
            if not workflow:
                raise HumanGateServiceError("Invalid or expired approval token")
            
            # Check if workflow can still receive feedback
            if workflow.status != WorkflowStatus.PENDING:
                raise HumanGateServiceError(f"Workflow is in {workflow.status} state, cannot accept feedback")
            
            if workflow.is_expired():
                workflow.status = WorkflowStatus.EXPIRED
                await self._update_workflow(workflow)
                raise HumanGateServiceError("Workflow has expired")
            
            # Process feedback based on type
            response_time = (datetime.utcnow() - workflow.created_at).total_seconds() / 3600
            
            if feedback.feedback_type == FeedbackType.APPROVE:
                workflow.status = WorkflowStatus.APPROVED
                workflow.approved_at = datetime.utcnow()
                
            elif feedback.feedback_type == FeedbackType.REJECT:
                workflow.status = WorkflowStatus.REJECTED
                
            elif feedback.feedback_type == FeedbackType.REQUEST_REVISION:
                workflow.status = WorkflowStatus.REVISION_REQUESTED
                workflow.revision_requests = feedback.add_features + feedback.remove_features + list(feedback.modify_features.values())
                workflow.priority_adjustments = feedback.priority_changes
                
            # Update workflow with feedback
            workflow.founder_feedback = feedback.overall_comments
            workflow.responded_at = datetime.utcnow()
            workflow.response_time_hours = response_time
            
            await self._update_workflow(workflow)
            
            logger.info(f"Processed {feedback.feedback_type} feedback for workflow {workflow.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to process founder feedback: {e}")
            raise HumanGateServiceError(f"Feedback processing failed: {str(e)}")
    
    async def get_tenant_workflows(
        self,
        tenant_id: UUID,
        status_filter: Optional[WorkflowStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[HumanApprovalWorkflow]:
        """Get approval workflows for a tenant"""
        
        try:
            workflow_ids = self._workflows_by_tenant.get(tenant_id, [])
            
            # Filter by status if requested
            workflows = []
            for workflow_id in workflow_ids[offset:offset + limit]:
                workflow = self._workflows_storage.get(workflow_id)
                if workflow:
                    if status_filter is None or workflow.status == status_filter:
                        workflows.append(workflow)
            
            return workflows
            
        except Exception as e:
            logger.error(f"Failed to get tenant workflows: {e}")
            raise HumanGateServiceError(f"Failed to retrieve workflows: {str(e)}")
    
    async def send_reminder(self, workflow_id: UUID) -> bool:
        """Send reminder email for pending workflow"""
        
        try:
            workflow = await self._get_workflow(workflow_id)
            if not workflow:
                return False
            
            if workflow.status != WorkflowStatus.PENDING or workflow.is_expired():
                return False
            
            # Update reminder count
            workflow.reminder_count += 1
            workflow.last_reminder_at = datetime.utcnow()
            await self._update_workflow(workflow)
            
            # Log email delivery (mock implementation)
            email_log = EmailDeliveryLog(
                workflow_id=workflow_id,
                recipient_email=workflow.founder_email,
                email_type="reminder",
                subject=f"Reminder: {workflow.workflow_title}",
                tenant_id=workflow.tenant_id
            )
            
            await self._log_email_delivery(email_log)
            
            logger.info(f"Sent reminder #{workflow.reminder_count} for workflow {workflow_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send reminder: {e}")
            return False
    
    async def cancel_workflow(self, workflow_id: UUID, tenant_id: UUID) -> bool:
        """Cancel an active workflow"""
        
        try:
            workflow = await self._get_workflow(workflow_id)
            if not workflow or workflow.tenant_id != tenant_id:
                return False
            
            if workflow.status not in [WorkflowStatus.PENDING]:
                return False
            
            workflow.status = WorkflowStatus.CANCELLED
            await self._update_workflow(workflow)
            
            logger.info(f"Cancelled workflow {workflow_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel workflow: {e}")
            return False
    
    async def get_workflow_metrics(
        self,
        tenant_id: UUID,
        days: int = 30
    ) -> WorkflowMetrics:
        """Get workflow analytics and metrics"""
        
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Get workflows for date range
            workflow_ids = self._workflows_by_tenant.get(tenant_id, [])
            workflows = [
                self._workflows_storage[wid] for wid in workflow_ids 
                if wid in self._workflows_storage and 
                self._workflows_storage[wid].created_at >= start_date
            ]
            
            # Calculate metrics
            total_workflows = len(workflows)
            approved_count = len([w for w in workflows if w.status == WorkflowStatus.APPROVED])
            rejected_count = len([w for w in workflows if w.status == WorkflowStatus.REJECTED])
            expired_count = len([w for w in workflows if w.status == WorkflowStatus.EXPIRED])
            
            responded_workflows = [w for w in workflows if w.responded_at is not None]
            response_times = [w.response_time_hours for w in responded_workflows if w.response_time_hours is not None]
            
            metrics = WorkflowMetrics(
                tenant_id=tenant_id,
                date_range_start=start_date,
                date_range_end=end_date,
                total_workflows=total_workflows,
                approved_workflows=approved_count,
                rejected_workflows=rejected_count,
                expired_workflows=expired_count,
                response_rate=len(responded_workflows) / max(1, total_workflows) * 100,
                approval_rate=approved_count / max(1, len(responded_workflows)) * 100,
                average_response_time_hours=sum(response_times) / max(1, len(response_times)),
                median_response_time_hours=sorted(response_times)[len(response_times)//2] if response_times else 0,
                fastest_response_time_hours=min(response_times) if response_times else 0,
                slowest_response_time_hours=max(response_times) if response_times else 0
            )
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to calculate workflow metrics: {e}")
            raise HumanGateServiceError(f"Metrics calculation failed: {str(e)}")
    
    async def cleanup_expired_workflows(self) -> int:
        """Cleanup expired workflows (background task)"""
        
        try:
            cleanup_count = 0
            current_time = datetime.utcnow()
            
            for workflow in self._workflows_storage.values():
                # Check both pending workflows and workflows that should be expired
                if (workflow.status == WorkflowStatus.PENDING and workflow.expires_at < current_time) or \
                   (workflow.expires_at < current_time and workflow.status != WorkflowStatus.EXPIRED):
                    workflow.status = WorkflowStatus.EXPIRED
                    await self._update_workflow(workflow)
                    cleanup_count += 1
            
            if cleanup_count > 0:
                logger.info(f"Cleaned up {cleanup_count} expired workflows")
                
            return cleanup_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired workflows: {e}")
            return 0
    
    # Private helper methods
    
    async def _save_workflow(self, workflow: HumanApprovalWorkflow):
        """Save workflow to storage"""
        self._workflows_storage[workflow.id] = workflow
        self._workflows_by_token[workflow.approval_token] = workflow.id
        
        # Add to tenant index
        if workflow.tenant_id not in self._workflows_by_tenant:
            self._workflows_by_tenant[workflow.tenant_id] = []
        
        if workflow.id not in self._workflows_by_tenant[workflow.tenant_id]:
            self._workflows_by_tenant[workflow.tenant_id].append(workflow.id)
        
        logger.debug(f"Saved workflow {workflow.id} to storage")
    
    async def _update_workflow(self, workflow: HumanApprovalWorkflow):
        """Update workflow in storage"""
        if workflow.id in self._workflows_storage:
            self._workflows_storage[workflow.id] = workflow
            logger.debug(f"Updated workflow {workflow.id}")
        else:
            logger.warning(f"Attempted to update non-existent workflow {workflow.id}")
    
    async def _get_workflow(self, workflow_id: UUID) -> Optional[HumanApprovalWorkflow]:
        """Get workflow from storage"""
        return self._workflows_storage.get(workflow_id)
    
    async def _log_email_delivery(self, email_log: EmailDeliveryLog):
        """Log email delivery for tracking"""
        if email_log.workflow_id not in self._email_logs:
            self._email_logs[email_log.workflow_id] = []
        
        self._email_logs[email_log.workflow_id].append(email_log)
        logger.debug(f"Logged email delivery for workflow {email_log.workflow_id}")


# Global service instance
human_gate_service = HumanGateService()