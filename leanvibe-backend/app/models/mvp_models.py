"""
MVP Factory models for LeanVibe Startup Factory
Provides MVP project management, blueprint storage, and generation tracking
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict


class MVPStatus(str, Enum):
    """MVP project lifecycle statuses"""
    BLUEPRINT_PENDING = "blueprint_pending"  # Waiting for founder interview completion
    BLUEPRINT_REVIEW = "blueprint_review"    # Blueprint generated, awaiting founder approval
    BLUEPRINT_APPROVED = "blueprint_approved"  # Blueprint approved, ready for generation
    GENERATING = "generating"                # AI agents are generating the MVP
    TESTING = "testing"                     # Generated MVP is being tested
    DEPLOYMENT_REVIEW = "deployment_review"  # MVP ready for deployment approval
    DEPLOYING = "deploying"                 # MVP is being deployed
    DEPLOYED = "deployed"                   # MVP is live and operational
    PAUSED = "paused"                       # MVP generation/deployment paused
    FAILED = "failed"                       # MVP generation failed
    ARCHIVED = "archived"                   # MVP archived by founder


class MVPTechStack(str, Enum):
    """Technology stack options for MVP generation"""
    FULL_STACK_REACT = "fullstack_react"     # React + FastAPI + PostgreSQL
    FULL_STACK_VUE = "fullstack_vue"         # Vue + FastAPI + PostgreSQL  
    MOBILE_FIRST = "mobile_first"            # React Native + FastAPI + PostgreSQL
    API_ONLY = "api_only"                    # FastAPI + PostgreSQL only
    STATIC_SITE = "static_site"              # Static site + serverless functions
    E_COMMERCE = "ecommerce"                 # Shopify/WooCommerce integration
    SAAS_PLATFORM = "saas_platform"          # Multi-tenant SaaS architecture


class MVPIndustry(str, Enum):
    """Industry categories for MVP optimization"""
    FINTECH = "fintech"
    HEALTHTECH = "healthtech"
    EDTECH = "edtech"
    ECOMMERCE = "ecommerce"
    PRODUCTIVITY = "productivity"
    SOCIAL = "social"
    GAMING = "gaming"
    IOT = "iot"
    AI_ML = "ai_ml"
    BLOCKCHAIN = "blockchain"
    OTHER = "other"


class BusinessRequirement(BaseModel):
    """Individual business requirement extracted from founder interview"""
    id: UUID = Field(default_factory=uuid4)
    requirement: str = Field(description="Business requirement description")
    priority: str = Field(description="Priority level: high, medium, low")
    category: str = Field(description="Category: functional, performance, business")
    acceptance_criteria: List[str] = Field(default_factory=list, description="Acceptance criteria")
    
    model_config = ConfigDict(extra="ignore")


class TechnicalBlueprint(BaseModel):
    """Technical blueprint generated from business requirements"""
    id: UUID = Field(default_factory=uuid4)
    
    # Architecture decisions
    tech_stack: MVPTechStack = Field(description="Selected technology stack")
    architecture_pattern: str = Field(description="Architecture pattern (MVC, microservices, etc.)")
    database_schema: Dict[str, Any] = Field(description="Database schema definition")
    api_endpoints: List[Dict[str, Any]] = Field(description="API endpoint definitions")
    
    # UI/UX specifications
    user_flows: List[Dict[str, Any]] = Field(description="User flow definitions")
    wireframes: List[Dict[str, Any]] = Field(description="UI wireframe specifications")
    design_system: Dict[str, Any] = Field(description="Design system configuration")
    
    # Infrastructure requirements
    deployment_config: Dict[str, Any] = Field(description="Deployment configuration")
    monitoring_config: Dict[str, Any] = Field(description="Monitoring and observability setup")
    scaling_config: Dict[str, Any] = Field(description="Auto-scaling configuration")
    
    # Quality and testing
    test_strategy: Dict[str, Any] = Field(description="Testing strategy and coverage")
    performance_targets: Dict[str, Any] = Field(description="Performance benchmarks")
    security_requirements: List[str] = Field(description="Security requirements")
    
    # Generation metadata
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    confidence_score: float = Field(description="AI confidence in blueprint (0-1)")
    estimated_generation_time: int = Field(description="Estimated generation time in minutes")
    
    model_config = ConfigDict(extra="ignore")


class FounderInterview(BaseModel):
    """Founder interview data and extracted requirements"""
    id: UUID = Field(default_factory=uuid4)
    
    # Interview metadata
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)
    duration_minutes: int = Field(default=0, description="Interview duration in minutes")
    
    # Business context
    business_idea: str = Field(description="Core business idea description")
    problem_statement: str = Field(description="Problem being solved")
    target_audience: str = Field(description="Target customer description")
    value_proposition: str = Field(description="Unique value proposition")
    market_size: Optional[str] = Field(default=None, description="Estimated market size")
    competition: Optional[str] = Field(default=None, description="Competitive landscape")
    
    # Product requirements
    core_features: List[str] = Field(description="Core MVP features")
    nice_to_have_features: List[str] = Field(default_factory=list, description="Future features")
    user_personas: List[Dict[str, str]] = Field(default_factory=list, description="User personas")
    success_metrics: List[str] = Field(default_factory=list, description="Success metrics")
    
    # Technical preferences
    preferred_tech_stack: Optional[MVPTechStack] = Field(default=None)
    technical_constraints: List[str] = Field(default_factory=list)
    integration_requirements: List[str] = Field(default_factory=list)
    
    # Business model
    revenue_model: Optional[str] = Field(default=None, description="Revenue model")
    pricing_strategy: Optional[str] = Field(default=None, description="Pricing strategy")
    go_to_market: Optional[str] = Field(default=None, description="Go-to-market strategy")
    
    # Extracted requirements
    requirements: List[BusinessRequirement] = Field(default_factory=list)
    industry: MVPIndustry = Field(default=MVPIndustry.OTHER)
    complexity_score: float = Field(default=0.5, description="Project complexity (0-1)")
    
    model_config = ConfigDict(extra="ignore")


class GenerationProgress(BaseModel):
    """Real-time progress tracking for MVP generation"""
    id: UUID = Field(default_factory=uuid4)
    
    # Generation stages
    blueprint_generation: Dict[str, Any] = Field(default_factory=dict, description="Blueprint generation progress")
    backend_generation: Dict[str, Any] = Field(default_factory=dict, description="Backend code generation progress")
    frontend_generation: Dict[str, Any] = Field(default_factory=dict, description="Frontend code generation progress")
    infrastructure_setup: Dict[str, Any] = Field(default_factory=dict, description="Infrastructure setup progress")
    testing_validation: Dict[str, Any] = Field(default_factory=dict, description="Testing and validation progress")
    deployment_process: Dict[str, Any] = Field(default_factory=dict, description="Deployment process progress")
    
    # Overall progress
    overall_progress_percent: int = Field(default=0, ge=0, le=100, description="Overall progress percentage")
    current_stage: str = Field(default="blueprint", description="Current generation stage")
    estimated_completion_at: Optional[datetime] = Field(default=None)
    
    # Real-time updates
    last_update_at: datetime = Field(default_factory=datetime.utcnow)
    status_message: str = Field(default="Starting generation...", description="Current status message")
    
    model_config = ConfigDict(extra="ignore")


class HumanApprovalWorkflow(BaseModel):
    """Human gate approval workflow for blueprints and deployments"""
    id: UUID = Field(default_factory=uuid4)
    
    # Workflow metadata
    workflow_type: str = Field(description="Type: blueprint_approval, deployment_approval")
    status: str = Field(default="pending", description="Status: pending, approved, rejected")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    responded_at: Optional[datetime] = Field(default=None)
    
    # Approval data
    approval_url: str = Field(description="URL for founder to review and approve")
    feedback: Optional[str] = Field(default=None, description="Founder feedback")
    revision_requests: List[str] = Field(default_factory=list, description="Requested revisions")
    
    # Notifications
    email_sent_at: Optional[datetime] = Field(default=None)
    reminder_count: int = Field(default=0, description="Number of reminder emails sent")
    
    model_config = ConfigDict(extra="ignore")


class MVPProject(BaseModel):
    """Core MVP project model for startup factory"""
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID = Field(description="Associated tenant (founder)")
    
    # Project identification
    project_name: str = Field(description="MVP project name")
    slug: str = Field(description="URL-safe project identifier")
    description: str = Field(description="Project description")
    
    # Project status and lifecycle
    status: MVPStatus = Field(default=MVPStatus.BLUEPRINT_PENDING)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)
    deployed_at: Optional[datetime] = Field(default=None)
    
    # Core components
    interview: Optional[FounderInterview] = Field(default=None, description="Founder interview data")
    blueprint: Optional[TechnicalBlueprint] = Field(default=None, description="Technical blueprint")
    generation_progress: GenerationProgress = Field(default_factory=GenerationProgress)
    
    # Human approval workflows
    blueprint_approval: Optional[HumanApprovalWorkflow] = Field(default=None)
    deployment_approval: Optional[HumanApprovalWorkflow] = Field(default=None)
    
    # Deployment information
    deployment_url: Optional[str] = Field(default=None, description="Live MVP URL")
    repository_url: Optional[str] = Field(default=None, description="Private repository URL")
    monitoring_dashboard_url: Optional[str] = Field(default=None, description="Monitoring dashboard URL")
    admin_panel_url: Optional[str] = Field(default=None, description="Admin panel URL")
    
    # Error handling
    error_message: Optional[str] = Field(default=None, description="Error message if generation failed")
    
    # Resource usage
    cpu_hours_used: float = Field(default=0.0, description="CPU hours consumed for generation")
    memory_gb_hours_used: float = Field(default=0.0, description="Memory GB-hours consumed")
    storage_mb_used: int = Field(default=0, description="Storage used in MB")
    ai_tokens_used: int = Field(default=0, description="AI tokens consumed")
    
    # Success metrics
    generation_success_rate: float = Field(default=0.0, description="Generation success rate (0-1)")
    deployment_uptime: float = Field(default=0.0, description="Deployment uptime percentage")
    founder_satisfaction_score: Optional[int] = Field(default=None, ge=1, le=10, description="Founder satisfaction (1-10)")
    
    # Billing and payment
    total_cost: float = Field(default=0.0, description="Total cost for MVP generation")
    payment_status: str = Field(default="pending", description="Payment status")
    payment_method: Optional[str] = Field(default=None, description="Payment method used")
    
    model_config = ConfigDict(extra="ignore")


class MVPProjectCreate(BaseModel):
    """Schema for creating new MVP projects"""
    project_name: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., min_length=2, max_length=50, pattern=r"^[a-z0-9-]+$")
    description: str = Field(..., min_length=10, max_length=1000)
    
    # Optional initial data
    business_idea: Optional[str] = Field(None, max_length=2000)
    target_audience: Optional[str] = Field(None, max_length=500)
    preferred_tech_stack: Optional[MVPTechStack] = None
    
    model_config = ConfigDict(extra="ignore")


class MVPProjectUpdate(BaseModel):
    """Schema for updating MVP projects"""
    project_name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = Field(None, min_length=10, max_length=1000)
    status: Optional[MVPStatus] = None
    
    # Deployment information updates
    deployment_url: Optional[str] = None
    repository_url: Optional[str] = None
    monitoring_dashboard_url: Optional[str] = None
    admin_panel_url: Optional[str] = None
    
    # Resource usage updates
    cpu_hours_used: Optional[float] = Field(None, ge=0)
    memory_gb_hours_used: Optional[float] = Field(None, ge=0)
    storage_mb_used: Optional[int] = Field(None, ge=0)
    ai_tokens_used: Optional[int] = Field(None, ge=0)
    
    # Success metrics
    founder_satisfaction_score: Optional[int] = Field(None, ge=1, le=10)
    
    # Billing updates
    total_cost: Optional[float] = Field(None, ge=0)
    payment_status: Optional[str] = None
    payment_method: Optional[str] = None
    
    model_config = ConfigDict(extra="ignore")


class MVPGenerationRequest(BaseModel):
    """Request to start MVP generation"""
    mvp_project_id: UUID = Field(description="MVP project to generate")
    priority: str = Field(default="normal", description="Generation priority: low, normal, high")
    custom_instructions: Optional[str] = Field(None, max_length=1000, description="Custom generation instructions")
    
    # Generation options
    skip_tests: bool = Field(default=False, description="Skip automated testing")
    include_sample_data: bool = Field(default=True, description="Include sample data in MVP")
    enable_analytics: bool = Field(default=True, description="Enable analytics tracking")
    
    model_config = ConfigDict(extra="ignore")


class MVPMetrics(BaseModel):
    """MVP success and performance metrics"""
    mvp_project_id: UUID = Field(description="Associated MVP project")
    
    # Performance metrics
    response_time_ms: float = Field(description="Average response time")
    uptime_percentage: float = Field(description="Uptime percentage")
    error_rate: float = Field(description="Error rate percentage")
    
    # Business metrics
    page_views: int = Field(default=0, description="Total page views")
    unique_visitors: int = Field(default=0, description="Unique visitors")
    conversion_rate: float = Field(default=0.0, description="Conversion rate percentage")
    user_signups: int = Field(default=0, description="User signups")
    
    # Technical metrics
    code_quality_score: float = Field(description="Code quality score (0-100)")
    test_coverage: float = Field(description="Test coverage percentage")
    security_score: float = Field(description="Security score (0-100)")
    
    # Collection timestamp
    collected_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(extra="ignore")