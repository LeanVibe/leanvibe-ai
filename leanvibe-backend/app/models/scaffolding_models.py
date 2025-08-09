"""
SaaS Scaffolding System models for LeanVibe Platform
Enables rapid generation of production-ready SaaS applications with enterprise features
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict, validator


class SaaSArchetype(str, Enum):
    """Core SaaS application archetypes"""
    B2B_PRODUCTIVITY = "b2b_productivity"           # Slack-like collaboration tools
    VERTICAL_MARKETPLACE = "vertical_marketplace"   # Industry-specific marketplaces
    DATA_ANALYTICS = "data_analytics"              # BI and analytics platforms  
    AI_POWERED_SAAS = "ai_powered_saas"            # AI/ML enabled applications
    CONTENT_MANAGEMENT = "content_management"       # CMS and publishing platforms
    E_COMMERCE = "e_commerce"                      # Online commerce platforms
    FINTECH_SAAS = "fintech_saas"                  # Financial services applications
    HEALTHCARE_SAAS = "healthcare_saas"            # HIPAA-compliant health applications
    IOT_PLATFORM = "iot_platform"                 # IoT device management platforms


class TechnologyStack(str, Enum):
    """Supported technology stacks"""
    PYTHON_FASTAPI = "python_fastapi"             # Python + FastAPI + SQLAlchemy
    PYTHON_DJANGO = "python_django"               # Python + Django + DRF
    TYPESCRIPT_NEXTJS = "typescript_nextjs"       # TypeScript + Next.js + Prisma
    TYPESCRIPT_NESTJS = "typescript_nestjs"       # TypeScript + NestJS + TypeORM
    GO_GIN = "go_gin"                             # Go + Gin + GORM
    RUST_AXUM = "rust_axum"                       # Rust + Axum + SeaORM


class DeploymentTarget(str, Enum):
    """Deployment platform options"""
    KUBERNETES_BASIC = "kubernetes_basic"          # Basic K8s deployment
    KUBERNETES_ENTERPRISE = "kubernetes_enterprise" # Enterprise K8s with compliance
    SERVERLESS_AWS = "serverless_aws"              # AWS Lambda + API Gateway
    SERVERLESS_GCP = "serverless_gcp"              # Google Cloud Run
    DOCKER_COMPOSE = "docker_compose"              # Docker Compose for development
    BARE_METAL = "bare_metal"                      # Traditional server deployment


class GenerationStatus(str, Enum):
    """Project generation status"""
    PENDING = "pending"                            # Generation queued
    ANALYZING = "analyzing"                        # Analyzing requirements
    GENERATING_SCHEMA = "generating_schema"        # Creating database models
    GENERATING_API = "generating_api"              # Creating API endpoints
    GENERATING_FRONTEND = "generating_frontend"    # Creating frontend components
    GENERATING_TESTS = "generating_tests"          # Creating test suites
    CONFIGURING_DEPLOYMENT = "configuring_deployment"  # Setting up deployment
    FINALIZING = "finalizing"                      # Final touches and cleanup
    COMPLETED = "completed"                        # Generation successful
    FAILED = "failed"                              # Generation failed
    CANCELLED = "cancelled"                        # Generation cancelled


class FeatureComplexity(str, Enum):
    """Feature implementation complexity levels"""
    TRIVIAL = "trivial"                           # <2 hours implementation
    LOW = "low"                                   # 2-8 hours implementation
    MEDIUM = "medium"                             # 1-3 days implementation
    HIGH = "high"                                 # 3-7 days implementation
    COMPLEX = "complex"                           # 1-2 weeks implementation


class ComplianceFramework(str, Enum):
    """Compliance frameworks for regulated industries"""
    SOC2_TYPE2 = "soc2_type2"                    # SOC 2 Type II compliance
    HIPAA = "hipaa"                               # Healthcare compliance
    GDPR = "gdpr"                                 # European data protection
    PCI_DSS = "pci_dss"                          # Payment card industry
    ISO27001 = "iso27001"                        # Information security management
    FFIEC = "ffiec"                              # Financial institution compliance


class TemplateVisibility(str, Enum):
    """Template visibility and access control"""
    PRIVATE = "private"                           # Only accessible to creator tenant
    TEAM = "team"                                 # Accessible to team members
    ORGANIZATION = "organization"                 # Accessible to entire organization
    PUBLIC = "public"                             # Publicly available
    MARKETPLACE = "marketplace"                   # Available in LeanVibe marketplace


class ProjectTemplate(BaseModel):
    """Project template definition for SaaS generation"""
    id: UUID = Field(default_factory=uuid4, description="Template unique identifier")
    tenant_id: UUID = Field(description="Template owner tenant")
    
    # Template metadata
    name: str = Field(..., min_length=2, max_length=100, description="Template display name")
    slug: str = Field(..., min_length=2, max_length=50, pattern=r"^[a-z0-9-]+$", description="URL-safe identifier")
    description: str = Field(..., min_length=10, max_length=500, description="Template description")
    version: str = Field(default="1.0.0", description="Template version (semantic versioning)")
    
    # Classification
    archetype: SaaSArchetype = Field(description="Base SaaS archetype")
    category: str = Field(description="Template category for organization")
    tags: List[str] = Field(default_factory=list, description="Search and filtering tags")
    
    # Technical configuration
    technology_stack: TechnologyStack = Field(description="Primary technology stack")
    supported_stacks: List[TechnologyStack] = Field(default_factory=list, description="Alternative tech stacks")
    deployment_targets: List[DeploymentTarget] = Field(description="Supported deployment platforms")
    
    # Feature configuration
    supported_features: List[str] = Field(description="All supported features")
    required_features: List[str] = Field(description="Mandatory features that cannot be disabled")
    default_features: List[str] = Field(description="Features enabled by default")
    feature_dependencies: Dict[str, List[str]] = Field(default_factory=dict, description="Feature dependency map")
    
    # Compliance and security
    compliance_frameworks: List[ComplianceFramework] = Field(default_factory=list, description="Supported compliance")
    security_features: Dict[str, bool] = Field(default_factory=dict, description="Security feature flags")
    data_residency_support: List[str] = Field(default_factory=list, description="Supported data residency regions")
    
    # Generation configuration
    generation_config: Dict[str, Any] = Field(default_factory=dict, description="Template-specific generation settings")
    customization_points: List[str] = Field(default_factory=list, description="Aspects users can customize")
    variable_definitions: Dict[str, Dict] = Field(default_factory=dict, description="Template variable schema")
    
    # Quality metrics and targets
    test_coverage_target: float = Field(default=0.85, ge=0.0, le=1.0, description="Target test coverage")
    performance_targets: Dict[str, str] = Field(default_factory=dict, description="Performance SLA targets")
    estimated_generation_time: int = Field(description="Estimated generation time in seconds")
    
    # Template status and metrics
    visibility: TemplateVisibility = Field(default=TemplateVisibility.PRIVATE, description="Template visibility")
    is_active: bool = Field(default=True, description="Template availability")
    is_featured: bool = Field(default=False, description="Featured template flag")
    
    # Usage analytics
    usage_count: int = Field(default=0, description="Number of times used")
    success_rate: float = Field(default=1.0, ge=0.0, le=1.0, description="Generation success rate")
    average_rating: float = Field(default=0.0, ge=0.0, le=5.0, description="User rating average")
    review_count: int = Field(default=0, description="Number of reviews")
    
    # Template authoring
    author_name: str = Field(description="Template author name")
    author_email: str = Field(description="Template author email")
    license: str = Field(default="MIT", description="Template license")
    documentation_url: Optional[str] = Field(default=None, description="Template documentation URL")
    repository_url: Optional[str] = Field(default=None, description="Template source repository")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Template creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    last_used_at: Optional[datetime] = Field(default=None, description="Last usage timestamp")
    
    model_config = ConfigDict(extra="ignore")

    @validator('slug')
    def validate_slug(cls, v):
        """Ensure slug is URL-safe and unique"""
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Slug must contain only letters, numbers, hyphens, and underscores')
        return v.lower()


class FeatureDefinition(BaseModel):
    """Reusable feature definition for SaaS projects"""
    id: UUID = Field(default_factory=uuid4, description="Feature unique identifier")
    
    # Feature metadata
    name: str = Field(..., min_length=2, max_length=100, description="Feature display name")
    slug: str = Field(..., min_length=2, max_length=50, pattern=r"^[a-z0-9-_]+$", description="Feature identifier")
    description: str = Field(..., min_length=10, max_length=500, description="Feature description")
    category: str = Field(description="Feature category for organization")
    
    # Implementation details
    complexity: FeatureComplexity = Field(description="Implementation complexity level")
    estimated_hours: int = Field(ge=1, le=336, description="Estimated implementation hours")  # Max 2 weeks
    
    # Compatibility matrix
    supported_archetypes: List[SaaSArchetype] = Field(description="Compatible SaaS archetypes")
    supported_stacks: List[TechnologyStack] = Field(description="Compatible technology stacks")
    
    # Dependencies and conflicts
    dependencies: List[str] = Field(default_factory=list, description="Required feature dependencies")
    conflicts: List[str] = Field(default_factory=list, description="Conflicting features")
    optional_dependencies: List[str] = Field(default_factory=list, description="Optional related features")
    
    # Implementation artifacts
    code_templates: Dict[str, str] = Field(default_factory=dict, description="Code generation templates")
    configuration_schema: Dict[str, Any] = Field(default_factory=dict, description="Feature configuration schema")
    test_templates: Dict[str, str] = Field(default_factory=dict, description="Test generation templates")
    migration_templates: List[str] = Field(default_factory=list, description="Database migration templates")
    
    # API impact
    api_endpoints: List[Dict[str, str]] = Field(default_factory=list, description="API endpoints added")
    database_changes: List[Dict[str, Any]] = Field(default_factory=list, description="Database schema changes")
    
    # Documentation and examples
    documentation: str = Field(default="", description="Feature documentation markdown")
    usage_examples: List[str] = Field(default_factory=list, description="Code usage examples")
    integration_examples: List[str] = Field(default_factory=list, description="Integration examples")
    
    # Quality assurance
    test_coverage_impact: float = Field(default=0.0, description="Impact on overall test coverage")
    performance_impact: str = Field(default="minimal", description="Performance impact assessment")
    security_considerations: List[str] = Field(default_factory=list, description="Security considerations")
    
    # Feature metrics
    usage_count: int = Field(default=0, description="Number of times used in projects")
    success_rate: float = Field(default=1.0, ge=0.0, le=1.0, description="Implementation success rate")
    
    # Feature status
    is_active: bool = Field(default=True, description="Feature availability")
    is_beta: bool = Field(default=False, description="Beta feature flag")
    deprecation_date: Optional[datetime] = Field(default=None, description="Feature deprecation date")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(extra="ignore")


class GeneratedProject(BaseModel):
    """Generated SaaS project record"""
    id: UUID = Field(default_factory=uuid4, description="Project unique identifier")
    tenant_id: UUID = Field(description="Project owner tenant")
    
    # Project metadata
    name: str = Field(..., min_length=2, max_length=100, description="Project name")
    slug: str = Field(..., min_length=2, max_length=50, pattern=r"^[a-z0-9-]+$", description="URL-safe project identifier")
    description: str = Field(description="Project description")
    
    # Generation source
    template_id: UUID = Field(description="Source template used for generation")
    template_version: str = Field(description="Template version used")
    archetype: SaaSArchetype = Field(description="SaaS archetype")
    
    # Project configuration
    business_domain: str = Field(description="Business domain/industry")
    target_audience: str = Field(description="Target user demographic")
    selected_features: List[str] = Field(description="Features enabled in this project")
    feature_configuration: Dict[str, Any] = Field(default_factory=dict, description="Feature-specific configuration")
    
    # Technical configuration
    technology_stack: TechnologyStack = Field(description="Selected technology stack")
    deployment_target: DeploymentTarget = Field(description="Selected deployment platform")
    deployment_regions: List[str] = Field(description="Deployment regions")
    
    # Compliance and security
    compliance_requirements: List[ComplianceFramework] = Field(default_factory=list, description="Required compliance")
    security_level: str = Field(default="standard", description="Security configuration level")
    data_residency: str = Field(description="Data residency requirement")
    
    # Project structure
    repository_url: Optional[str] = Field(default=None, description="Generated project repository URL")
    project_structure: Dict[str, Any] = Field(default_factory=dict, description="Generated file structure")
    
    # Generation metadata
    generation_status: GenerationStatus = Field(default=GenerationStatus.PENDING, description="Current generation status")
    generation_progress: float = Field(default=0.0, ge=0.0, le=1.0, description="Generation progress percentage")
    generation_log: List[str] = Field(default_factory=list, description="Generation log messages")
    generation_errors: List[str] = Field(default_factory=list, description="Generation error messages")
    
    # Timing metrics
    generation_started_at: Optional[datetime] = Field(default=None, description="Generation start time")
    generation_completed_at: Optional[datetime] = Field(default=None, description="Generation completion time")
    generation_duration_seconds: Optional[int] = Field(default=None, description="Total generation time")
    
    # Deployment status
    deployment_status: str = Field(default="not_deployed", description="Current deployment status")
    deployment_environments: Dict[str, Dict] = Field(default_factory=dict, description="Environment deployment info")
    last_deployed_at: Optional[datetime] = Field(default=None, description="Last deployment timestamp")
    
    # Quality metrics
    generated_test_coverage: float = Field(default=0.0, description="Generated test coverage percentage")
    quality_score: float = Field(default=0.0, description="Overall quality score")
    security_scan_results: Dict[str, Any] = Field(default_factory=dict, description="Security scan results")
    performance_benchmarks: Dict[str, Any] = Field(default_factory=dict, description="Performance test results")
    
    # Project health
    health_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Project health score")
    build_status: str = Field(default="unknown", description="Latest build status")
    test_status: str = Field(default="unknown", description="Latest test status")
    
    # User customizations
    customizations_applied: List[str] = Field(default_factory=list, description="User customizations")
    custom_code_percentage: float = Field(default=0.0, description="Percentage of custom vs generated code")
    
    # Analytics
    daily_active_users: int = Field(default=0, description="Current DAU")
    monthly_active_users: int = Field(default=0, description="Current MAU")
    api_usage_monthly: int = Field(default=0, description="Monthly API calls")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(extra="ignore")


class GenerationJob(BaseModel):
    """Background job for project generation"""
    id: UUID = Field(default_factory=uuid4, description="Job unique identifier")
    tenant_id: UUID = Field(description="Job owner tenant")
    project_id: UUID = Field(description="Target project being generated")
    
    # Job configuration
    job_type: str = Field(default="full_generation", description="Type of generation job")
    priority: int = Field(default=0, description="Job priority (higher = more important)")
    
    # Job status
    status: GenerationStatus = Field(default=GenerationStatus.PENDING, description="Current job status")
    progress: float = Field(default=0.0, ge=0.0, le=1.0, description="Job progress percentage")
    current_step: str = Field(default="", description="Current generation step")
    
    # Job execution
    worker_id: Optional[str] = Field(default=None, description="Worker processing this job")
    started_at: Optional[datetime] = Field(default=None, description="Job start time")
    completed_at: Optional[datetime] = Field(default=None, description="Job completion time")
    
    # Job results
    result_data: Dict[str, Any] = Field(default_factory=dict, description="Job execution results")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    retry_count: int = Field(default=0, description="Number of retry attempts")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    
    # Job metadata
    estimated_duration: Optional[int] = Field(default=None, description="Estimated job duration in seconds")
    resource_requirements: Dict[str, Any] = Field(default_factory=dict, description="Required compute resources")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(extra="ignore")


class ProjectGenerationRequest(BaseModel):
    """Request model for project generation"""
    # Project basics
    name: str = Field(..., min_length=2, max_length=100, description="Project name")
    description: str = Field(..., min_length=10, max_length=500, description="Project description")
    business_domain: str = Field(description="Business domain/industry")
    
    # Template selection
    template_id: Optional[UUID] = Field(default=None, description="Specific template to use")
    archetype: Optional[SaaSArchetype] = Field(default=None, description="SaaS archetype if no template")
    
    # Feature selection
    features: List[str] = Field(description="List of features to include")
    feature_config: Dict[str, Any] = Field(default_factory=dict, description="Feature-specific configuration")
    
    # Technical choices
    technology_stack: TechnologyStack = Field(description="Preferred technology stack")
    deployment_target: DeploymentTarget = Field(description="Target deployment platform")
    deployment_regions: List[str] = Field(description="Deployment regions")
    
    # Compliance and security
    compliance_requirements: List[ComplianceFramework] = Field(default_factory=list, description="Required compliance")
    security_level: str = Field(default="standard", description="Security configuration level")
    data_residency: str = Field(description="Data residency requirement")
    
    # Customization
    custom_variables: Dict[str, Any] = Field(default_factory=dict, description="Template variable overrides")
    additional_requirements: List[str] = Field(default_factory=list, description="Additional custom requirements")
    
    # Generation options
    include_sample_data: bool = Field(default=True, description="Include sample/demo data")
    include_documentation: bool = Field(default=True, description="Generate project documentation")
    setup_ci_cd: bool = Field(default=True, description="Set up CI/CD pipeline")
    
    model_config = ConfigDict(extra="ignore")


class TemplateReview(BaseModel):
    """User review of a project template"""
    id: UUID = Field(default_factory=uuid4, description="Review unique identifier")
    template_id: UUID = Field(description="Reviewed template")
    tenant_id: UUID = Field(description="Reviewer tenant")
    user_id: UUID = Field(description="Reviewer user")
    
    # Review content
    rating: int = Field(ge=1, le=5, description="Rating from 1-5 stars")
    title: str = Field(..., min_length=5, max_length=100, description="Review title")
    content: str = Field(..., min_length=20, max_length=2000, description="Review content")
    
    # Review metadata
    is_verified: bool = Field(default=False, description="Verified purchase/usage")
    is_featured: bool = Field(default=False, description="Featured review")
    helpful_votes: int = Field(default=0, description="Number of helpful votes")
    
    # Generated project reference
    generated_project_id: Optional[UUID] = Field(default=None, description="Associated generated project")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(extra="ignore")


# Default feature catalog for common SaaS features
DEFAULT_FEATURES = {
    # Authentication & Authorization
    "user_authentication": FeatureDefinition(
        name="User Authentication",
        slug="user_authentication",
        description="Complete user authentication system with login, registration, password reset",
        category="authentication",
        complexity=FeatureComplexity.LOW,
        estimated_hours=4,
        supported_archetypes=list(SaaSArchetype),
        supported_stacks=list(TechnologyStack),
    ),
    
    "sso_integration": FeatureDefinition(
        name="Single Sign-On (SSO)",
        slug="sso_integration", 
        description="Enterprise SSO integration with Google, Microsoft, Okta, and SAML providers",
        category="authentication",
        complexity=FeatureComplexity.MEDIUM,
        estimated_hours=16,
        supported_archetypes=[SaaSArchetype.B2B_PRODUCTIVITY, SaaSArchetype.VERTICAL_MARKETPLACE],
        dependencies=["user_authentication"],
    ),
    
    # Collaboration
    "real_time_collaboration": FeatureDefinition(
        name="Real-time Collaboration",
        slug="real_time_collaboration",
        description="WebSocket-based real-time collaboration with operational transforms",
        category="collaboration",
        complexity=FeatureComplexity.HIGH,
        estimated_hours=40,
        supported_archetypes=[SaaSArchetype.B2B_PRODUCTIVITY, SaaSArchetype.CONTENT_MANAGEMENT],
    ),
    
    # Commerce
    "payment_processing": FeatureDefinition(
        name="Payment Processing",
        slug="payment_processing",
        description="Integrated payment processing with Stripe, PayPal, and bank transfers",
        category="commerce",
        complexity=FeatureComplexity.MEDIUM,
        estimated_hours=24,
        supported_archetypes=[SaaSArchetype.VERTICAL_MARKETPLACE, SaaSArchetype.E_COMMERCE],
    ),
    
    # AI/ML
    "ai_content_generation": FeatureDefinition(
        name="AI Content Generation",
        slug="ai_content_generation",
        description="AI-powered content generation using LLMs with custom prompts and templates",
        category="artificial_intelligence",
        complexity=FeatureComplexity.HIGH,
        estimated_hours=32,
        supported_archetypes=[SaaSArchetype.AI_POWERED_SAAS, SaaSArchetype.CONTENT_MANAGEMENT],
    ),
    
    # Analytics
    "business_analytics": FeatureDefinition(
        name="Business Analytics Dashboard",
        slug="business_analytics",
        description="Comprehensive analytics dashboard with charts, metrics, and reporting",
        category="analytics",
        complexity=FeatureComplexity.MEDIUM,
        estimated_hours=20,
        supported_archetypes=[SaaSArchetype.DATA_ANALYTICS, SaaSArchetype.B2B_PRODUCTIVITY],
    )
}


# Default template configurations for each archetype
DEFAULT_TEMPLATES = {
    SaaSArchetype.B2B_PRODUCTIVITY: ProjectTemplate(
        tenant_id=UUID("00000000-0000-0000-0000-000000000000"),  # System template
        name="B2B Productivity Suite",
        slug="b2b-productivity-suite",
        description="Complete B2B productivity platform with team collaboration, project management, and enterprise features",
        archetype=SaaSArchetype.B2B_PRODUCTIVITY,
        category="productivity",
        technology_stack=TechnologyStack.PYTHON_FASTAPI,
        deployment_targets=[DeploymentTarget.KUBERNETES_ENTERPRISE],
        supported_features=["user_authentication", "sso_integration", "real_time_collaboration", "business_analytics"],
        required_features=["user_authentication"],
        default_features=["user_authentication", "business_analytics"],
        author_name="LeanVibe Team",
        author_email="templates@leanvibe.ai",
        estimated_generation_time=240,  # 4 minutes
    ),
    
    SaaSArchetype.VERTICAL_MARKETPLACE: ProjectTemplate(
        tenant_id=UUID("00000000-0000-0000-0000-000000000000"),  # System template
        name="Vertical Marketplace Platform",
        slug="vertical-marketplace-platform",
        description="Industry-specific marketplace with vendor management, payments, and commission tracking",
        archetype=SaaSArchetype.VERTICAL_MARKETPLACE,
        category="marketplace",
        technology_stack=TechnologyStack.PYTHON_FASTAPI,
        deployment_targets=[DeploymentTarget.KUBERNETES_ENTERPRISE],
        supported_features=["user_authentication", "payment_processing", "business_analytics"],
        required_features=["user_authentication", "payment_processing"],
        default_features=["user_authentication", "payment_processing", "business_analytics"],
        author_name="LeanVibe Team", 
        author_email="templates@leanvibe.ai",
        estimated_generation_time=300,  # 5 minutes
    )
}