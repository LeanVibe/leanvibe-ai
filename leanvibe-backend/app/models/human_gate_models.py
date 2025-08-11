"""
Human Gate Workflow Models
Secure founder approval system with token-based authentication and feedback loops
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict, validator


class WorkflowType(str, Enum):
    """Types of human approval workflows"""
    BLUEPRINT_APPROVAL = "blueprint_approval"
    DEPLOYMENT_APPROVAL = "deployment_approval"
    REVISION_REVIEW = "revision_review"
    EMERGENCY_STOP = "emergency_stop"


class WorkflowStatus(str, Enum):
    """Human approval workflow status"""
    PENDING = "pending"                    # Awaiting founder response
    APPROVED = "approved"                  # Founder approved the request
    REJECTED = "rejected"                  # Founder rejected the request  
    REVISION_REQUESTED = "revision_requested"  # Founder requested changes
    EXPIRED = "expired"                    # Approval window expired
    CANCELLED = "cancelled"                # Workflow cancelled


class FeedbackType(str, Enum):
    """Types of founder feedback"""
    APPROVE = "approve"                    # Approve as-is
    REJECT = "reject"                      # Reject completely
    REQUEST_REVISION = "request_revision"  # Request specific changes
    REQUEST_CLARIFICATION = "request_clarification"  # Need more information


class ApprovalPriority(str, Enum):
    """Priority levels for approval workflows"""
    LOW = "low"           # 7 day expiration
    NORMAL = "normal"     # 3 day expiration  
    HIGH = "high"         # 1 day expiration
    URGENT = "urgent"     # 12 hour expiration


class HumanApprovalWorkflow(BaseModel):
    """Core human approval workflow model"""
    id: UUID = Field(default_factory=uuid4)
    mvp_project_id: UUID = Field(description="Associated MVP project")
    workflow_type: WorkflowType
    status: WorkflowStatus = WorkflowStatus.PENDING
    priority: ApprovalPriority = ApprovalPriority.NORMAL
    
    # Security and access control
    approval_token: str = Field(description="Secure JWT token for founder access")
    approval_url: str = Field(description="Frontend URL for review interface")
    founder_email: str = Field(description="Founder's email address")
    
    # Workflow timing
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(description="Approval window expiration")
    responded_at: Optional[datetime] = Field(default=None)
    approved_at: Optional[datetime] = Field(default=None)
    
    # Content and context
    workflow_title: str = Field(description="Human-readable workflow title")
    workflow_description: str = Field(description="Detailed description of what needs approval")
    context_data: Dict[str, Any] = Field(default_factory=dict, description="Workflow-specific context")
    
    # Feedback and revisions
    founder_feedback: Optional[str] = Field(default=None, description="Founder's feedback text")
    revision_requests: List[str] = Field(default_factory=list, description="Specific revision requests")
    priority_adjustments: Dict[str, str] = Field(default_factory=dict, description="Feature priority changes")
    
    # Email and notification tracking
    email_sent_at: Optional[datetime] = Field(default=None)
    reminder_count: int = Field(default=0, ge=0, description="Number of reminder emails sent")
    last_reminder_at: Optional[datetime] = Field(default=None)
    
    # Analytics and metrics
    email_opened_at: Optional[datetime] = Field(default=None)
    approval_page_viewed_at: Optional[datetime] = Field(default=None)
    response_time_hours: Optional[float] = Field(default=None, description="Time from creation to response")
    
    # Multi-tenancy
    tenant_id: UUID = Field(description="Tenant ID for RLS")
    
    model_config = ConfigDict(extra="ignore")
    
    def __init__(self, **data):
        # Set expiration time if not provided
        if 'expires_at' not in data or data['expires_at'] is None:
            created_at = data.get('created_at', datetime.utcnow())
            priority = data.get('priority', ApprovalPriority.NORMAL)
            
            expiration_hours = {
                ApprovalPriority.LOW: 168,    # 7 days
                ApprovalPriority.NORMAL: 72,  # 3 days
                ApprovalPriority.HIGH: 24,    # 1 day
                ApprovalPriority.URGENT: 12   # 12 hours
            }
            
            hours = expiration_hours.get(priority, 72)
            data['expires_at'] = created_at + timedelta(hours=hours)
        
        super().__init__(**data)
    
    def is_expired(self) -> bool:
        """Check if workflow has expired"""
        return datetime.utcnow() > self.expires_at
    
    def time_until_expiration(self) -> timedelta:
        """Get time remaining until expiration"""
        return self.expires_at - datetime.utcnow()


class FounderFeedback(BaseModel):
    """Structured founder feedback for workflow responses"""
    workflow_id: UUID
    feedback_type: FeedbackType
    
    # Overall feedback
    overall_comments: Optional[str] = Field(default=None, max_length=2000)
    satisfaction_score: Optional[int] = Field(default=None, ge=1, le=10, description="Satisfaction rating 1-10")
    
    # Feature-specific feedback
    feature_feedback: Dict[str, str] = Field(default_factory=dict, description="Per-feature feedback")
    feature_ratings: Dict[str, int] = Field(default_factory=dict, description="Per-feature ratings 1-5")
    
    # Technical concerns
    tech_stack_concerns: List[str] = Field(default_factory=list, description="Technology-related concerns")
    performance_concerns: List[str] = Field(default_factory=list, description="Performance-related concerns")
    security_concerns: List[str] = Field(default_factory=list, description="Security-related concerns")
    
    # Timeline and expectations
    timeline_expectations: Optional[str] = Field(default=None, description="Expected timeline feedback")
    budget_concerns: Optional[str] = Field(default=None, description="Budget-related concerns")
    
    # Specific change requests
    add_features: List[str] = Field(default_factory=list, description="Features to add")
    remove_features: List[str] = Field(default_factory=list, description="Features to remove")
    modify_features: Dict[str, str] = Field(default_factory=dict, description="Features to modify")
    
    # Priority adjustments
    priority_changes: Dict[str, str] = Field(default_factory=dict, description="Priority adjustments (feature_id: new_priority)")
    
    # Contact preferences
    preferred_contact_method: Optional[str] = Field(default="email", description="Preferred communication method")
    follow_up_requested: bool = Field(default=False, description="Whether founder wants follow-up call")
    
    # Metadata
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = Field(default=None, description="Submitter IP for security")
    user_agent: Optional[str] = Field(default=None, description="Browser user agent")
    
    model_config = ConfigDict(extra="ignore")


class BlueprintApprovalWorkflow(BaseModel):
    """Specialized workflow for blueprint approvals"""
    base_workflow: HumanApprovalWorkflow
    
    # Blueprint-specific data
    blueprint_summary: Dict[str, Any] = Field(description="Executive summary of blueprint")
    tech_stack_details: Dict[str, Any] = Field(description="Technology stack breakdown")
    feature_breakdown: List[Dict[str, Any]] = Field(description="Feature list with priorities")
    timeline_estimate: Dict[str, Any] = Field(description="Development timeline estimate")
    cost_estimate: Dict[str, Any] = Field(description="Development cost estimate")
    risk_assessment: Dict[str, Any] = Field(description="Technical risks and mitigation")
    
    # Interactive elements
    feature_toggles: Dict[str, bool] = Field(default_factory=dict, description="Features that can be toggled")
    customization_options: List[Dict[str, Any]] = Field(default_factory=list, description="Customizable aspects")
    
    model_config = ConfigDict(extra="ignore")


class DeploymentApprovalWorkflow(BaseModel):
    """Specialized workflow for deployment approvals"""
    base_workflow: HumanApprovalWorkflow
    
    # Deployment-specific data
    deployment_summary: Dict[str, Any] = Field(description="Deployment configuration summary")
    infrastructure_details: Dict[str, Any] = Field(description="Infrastructure specifications")
    security_measures: List[str] = Field(description="Security measures implemented")
    performance_metrics: Dict[str, Any] = Field(description="Expected performance metrics")
    monitoring_setup: Dict[str, Any] = Field(description="Monitoring and alerting configuration")
    
    # Deployment options
    environment_options: List[str] = Field(description="Available deployment environments")
    rollback_plan: Dict[str, Any] = Field(description="Rollback strategy")
    
    model_config = ConfigDict(extra="ignore")


class WorkflowTemplate(BaseModel):
    """Template for creating standardized approval workflows"""
    template_id: str = Field(description="Unique template identifier")
    template_name: str = Field(description="Human-readable template name")
    workflow_type: WorkflowType
    
    # Template configuration
    default_priority: ApprovalPriority = ApprovalPriority.NORMAL
    required_fields: List[str] = Field(description="Fields that must be provided")
    optional_fields: List[str] = Field(description="Optional fields")
    
    # Email template
    email_subject_template: str = Field(description="Email subject with variables")
    email_body_template: str = Field(description="Email body with variables")
    reminder_email_template: str = Field(description="Reminder email template")
    
    # Approval page template
    approval_page_title: str = Field(description="Title for approval page")
    approval_page_sections: List[Dict[str, Any]] = Field(description="Page sections configuration")
    
    # Workflow behavior
    allow_revisions: bool = Field(default=True, description="Allow revision requests")
    max_revisions: int = Field(default=3, description="Maximum revision cycles")
    auto_approve_conditions: List[Dict[str, Any]] = Field(default_factory=list, description="Auto-approval rules")
    
    model_config = ConfigDict(extra="ignore")


class EmailDeliveryLog(BaseModel):
    """Email delivery tracking for approval workflows"""
    id: UUID = Field(default_factory=uuid4)
    workflow_id: UUID = Field(description="Associated approval workflow")
    
    # Email details
    recipient_email: str = Field(description="Email recipient")
    email_type: str = Field(description="Email type (approval, reminder, etc.)")
    subject: str = Field(description="Email subject line")
    
    # Delivery tracking
    sent_at: datetime = Field(default_factory=datetime.utcnow)
    delivered_at: Optional[datetime] = Field(default=None)
    opened_at: Optional[datetime] = Field(default=None)
    clicked_at: Optional[datetime] = Field(default=None)
    bounced_at: Optional[datetime] = Field(default=None)
    
    # Status and metrics
    delivery_status: str = Field(default="sent", description="sent, delivered, bounced, failed")
    bounce_reason: Optional[str] = Field(default=None, description="Bounce reason if applicable")
    open_count: int = Field(default=0, description="Number of times email was opened")
    click_count: int = Field(default=0, description="Number of link clicks")
    
    # Email service metadata
    email_service_id: Optional[str] = Field(default=None, description="External service tracking ID")
    email_service_provider: str = Field(default="sendgrid", description="Email service provider")
    
    # Multi-tenancy
    tenant_id: UUID = Field(description="Tenant ID for RLS")
    
    model_config = ConfigDict(extra="ignore")


class WorkflowMetrics(BaseModel):
    """Analytics and metrics for approval workflows"""
    tenant_id: UUID
    date_range_start: datetime
    date_range_end: datetime
    
    # Workflow counts
    total_workflows: int = 0
    approved_workflows: int = 0
    rejected_workflows: int = 0
    expired_workflows: int = 0
    
    # Response rates
    response_rate: float = 0.0  # Percentage of workflows that received response
    approval_rate: float = 0.0  # Percentage of responded workflows that were approved
    
    # Timing metrics
    average_response_time_hours: float = 0.0
    median_response_time_hours: float = 0.0
    fastest_response_time_hours: float = 0.0
    slowest_response_time_hours: float = 0.0
    
    # Email metrics
    email_delivery_rate: float = 0.0
    email_open_rate: float = 0.0
    email_click_rate: float = 0.0
    
    # Satisfaction metrics
    average_satisfaction_score: Optional[float] = None
    satisfaction_scores: List[int] = Field(default_factory=list)
    
    model_config = ConfigDict(extra="ignore")


# Request/Response Models for API

class CreateWorkflowRequest(BaseModel):
    """Request to create new approval workflow"""
    mvp_project_id: UUID
    workflow_type: WorkflowType
    founder_email: str
    priority: ApprovalPriority = ApprovalPriority.NORMAL
    workflow_title: str
    workflow_description: str
    context_data: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(extra="ignore")


class WorkflowResponse(BaseModel):
    """Response containing workflow details"""
    workflow: HumanApprovalWorkflow
    time_until_expiration: Optional[str] = None
    can_respond: bool = True
    
    model_config = ConfigDict(extra="ignore")


class SubmitFeedbackRequest(BaseModel):
    """Request to submit founder feedback"""
    approval_token: str
    feedback: FounderFeedback
    
    model_config = ConfigDict(extra="ignore")


class WorkflowListResponse(BaseModel):
    """Response containing list of workflows"""
    workflows: List[HumanApprovalWorkflow]
    total_count: int
    pending_count: int
    expired_count: int
    has_more: bool
    
    model_config = ConfigDict(extra="ignore")


class WorkflowMetricsResponse(BaseModel):
    """Response containing workflow metrics"""
    metrics: WorkflowMetrics
    trends: Dict[str, List[float]] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list)
    
    model_config = ConfigDict(extra="ignore")