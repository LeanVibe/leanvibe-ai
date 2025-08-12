"""
Pipeline API Models for LeanVibe Autonomous MVP Generation
Comprehensive data models for pipeline management and tracking
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field, validator


class PipelineStatus(str, Enum):
    """Pipeline execution status"""
    BLUEPRINT_PENDING = "blueprint_pending"
    GENERATING = "generating"
    DEPLOYED = "deployed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PipelineStage(str, Enum):
    """Pipeline execution stages"""
    BLUEPRINT_GENERATION = "blueprint_generation"
    BACKEND_DEVELOPMENT = "backend_development"
    FRONTEND_DEVELOPMENT = "frontend_development"
    INFRASTRUCTURE_SETUP = "infrastructure_setup"
    DEPLOYMENT = "deployment"


class PipelinePriority(str, Enum):
    """Pipeline execution priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class PipelineConfiguration(BaseModel):
    """Pipeline configuration settings"""
    priority: PipelinePriority = Field(default=PipelinePriority.NORMAL)
    auto_deploy: bool = Field(default=True, description="Automatically deploy upon completion")
    enable_monitoring: bool = Field(default=True, description="Enable monitoring and observability")
    backup_enabled: bool = Field(default=True, description="Enable automatic backups")
    notification_settings: Optional[Dict[str, Any]] = Field(default=None)
    resource_limits: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Resource limits for generation (CPU, memory, time)"
    )
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PipelineProgress(BaseModel):
    """Pipeline progress tracking"""
    overall_progress: float = Field(ge=0.0, le=100.0, description="Overall completion percentage")
    stage_progress: float = Field(ge=0.0, le=100.0, description="Current stage completion percentage")
    estimated_completion: Optional[datetime] = Field(default=None)
    stages_completed: List[str] = Field(default_factory=list)
    current_stage_details: str = Field(default="", description="Detailed status of current stage")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PipelineLogEntry(BaseModel):
    """Pipeline execution log entry"""
    timestamp: datetime
    level: str = Field(description="Log level (INFO, WARNING, ERROR)")
    message: str = Field(description="Log message")
    stage: PipelineStage = Field(description="Pipeline stage when log was generated")
    metadata: Optional[Dict[str, Any]] = Field(default=None)
    
    @validator('level')
    def validate_level(cls, v):
        allowed_levels = {'INFO', 'WARNING', 'ERROR', 'DEBUG'}
        if v.upper() not in allowed_levels:
            raise ValueError(f"Log level must be one of {allowed_levels}")
        return v.upper()
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PipelineCreateRequest(BaseModel):
    """Request model for creating a new pipeline"""
    project_name: str = Field(min_length=1, max_length=100, description="Name for the MVP project")
    founder_interview: 'FounderInterview' = Field(description="Complete founder interview data")
    configuration: Optional[PipelineConfiguration] = Field(default=None)
    
    @validator('project_name')
    def validate_project_name(cls, v):
        # Remove any potentially problematic characters
        import re
        if not re.match(r'^[a-zA-Z0-9\s\-_\.]+$', v):
            raise ValueError("Project name contains invalid characters")
        return v.strip()


class PipelineUpdateRequest(BaseModel):
    """Request model for updating pipeline configuration"""
    project_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    configuration: Optional[PipelineConfiguration] = Field(default=None)
    
    @validator('project_name')
    def validate_project_name(cls, v):
        if v is not None:
            import re
            if not re.match(r'^[a-zA-Z0-9\s\-_\.]+$', v):
                raise ValueError("Project name contains invalid characters")
            return v.strip()
        return v


class PipelineExecutionRequest(BaseModel):
    """Request model for starting pipeline execution"""
    technical_blueprint: 'TechnicalBlueprint' = Field(description="Technical blueprint for MVP generation")
    configuration_overrides: Optional[PipelineConfiguration] = Field(default=None)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PipelineResponse(BaseModel):
    """Response model for pipeline information"""
    id: UUID = Field(description="Unique pipeline identifier")
    project_name: str = Field(description="Name of the MVP project")
    status: PipelineStatus = Field(description="Current pipeline status")
    current_stage: PipelineStage = Field(description="Current execution stage")
    progress: PipelineProgress = Field(description="Progress information")
    created_at: datetime = Field(description="Pipeline creation timestamp")
    estimated_completion: Optional[datetime] = Field(default=None)
    tenant_id: UUID = Field(description="Tenant identifier")
    created_by: UUID = Field(description="User who created the pipeline")
    configuration: Optional[PipelineConfiguration] = Field(default=None)
    blueprint_approved: bool = Field(default=False, description="Whether blueprint has been approved")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PipelineStatusResponse(BaseModel):
    """Detailed status response for real-time monitoring"""
    status: PipelineStatus = Field(description="Current pipeline status")
    current_stage: PipelineStage = Field(description="Current execution stage")
    progress: PipelineProgress = Field(description="Detailed progress information")
    stage_details: Dict[str, Any] = Field(default_factory=dict, description="Stage-specific details")
    logs: List[PipelineLogEntry] = Field(default_factory=list, description="Recent log entries")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    performance_metrics: Optional[Dict[str, Any]] = Field(default=None)
    resource_usage: Optional[Dict[str, Any]] = Field(default=None)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PipelineMetrics(BaseModel):
    """Pipeline performance and usage metrics"""
    total_pipelines: int = Field(ge=0)
    active_pipelines: int = Field(ge=0)
    completed_pipelines: int = Field(ge=0)
    failed_pipelines: int = Field(ge=0)
    average_completion_time: Optional[float] = Field(default=None, description="Average completion time in hours")
    success_rate: float = Field(ge=0.0, le=100.0, description="Success rate percentage")
    resource_utilization: Optional[Dict[str, float]] = Field(default=None)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PipelineTemplate(BaseModel):
    """Pipeline template for common configurations"""
    id: UUID
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(max_length=500)
    configuration: PipelineConfiguration
    default_blueprint: Optional['TechnicalBlueprint'] = Field(default=None)
    created_at: datetime
    is_public: bool = Field(default=False)
    tenant_id: Optional[UUID] = Field(default=None)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PipelineWebhook(BaseModel):
    """Webhook configuration for pipeline events"""
    id: UUID
    pipeline_id: UUID
    url: str = Field(description="Webhook URL to call")
    events: List[str] = Field(description="List of events to trigger webhook")
    secret: Optional[str] = Field(default=None, description="Secret for webhook validation")
    enabled: bool = Field(default=True)
    retry_count: int = Field(default=3, ge=0, le=10)
    timeout_seconds: int = Field(default=30, ge=1, le=300)
    
    @validator('url')
    def validate_url(cls, v):
        import re
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        if not url_pattern.match(v):
            raise ValueError("Invalid webhook URL format")
        return v
    
    @validator('events')
    def validate_events(cls, v):
        allowed_events = {
            'pipeline.created',
            'pipeline.started',
            'pipeline.stage_completed',
            'pipeline.completed',
            'pipeline.failed',
            'pipeline.cancelled'
        }
        for event in v:
            if event not in allowed_events:
                raise ValueError(f"Invalid event type: {event}")
        return v


class PipelineAnalytics(BaseModel):
    """Analytics data for pipeline performance"""
    pipeline_id: UUID
    execution_time: float = Field(description="Total execution time in hours")
    stages_breakdown: Dict[PipelineStage, float] = Field(description="Time spent per stage")
    resource_usage: Dict[str, float] = Field(description="Resource utilization metrics")
    error_count: int = Field(ge=0)
    retry_count: int = Field(ge=0)
    quality_score: float = Field(ge=0.0, le=100.0, description="Generated code quality score")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Import dependencies (circular import resolution)
from ..models.mvp_models import FounderInterview, TechnicalBlueprint

# Update forward references
PipelineCreateRequest.model_rebuild()
PipelineExecutionRequest.model_rebuild()
PipelineTemplate.model_rebuild()