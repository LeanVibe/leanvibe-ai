"""
Multi-tenant models for LeanVibe Enterprise SaaS Platform
Provides tenant isolation, resource quotas, and organization hierarchy
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict


class TenantType(str, Enum):
    """Tenant types for hybrid enterprise + MVP factory model"""
    ENTERPRISE = "enterprise"  # Traditional enterprise organization  
    MVP_FACTORY = "mvp_factory"  # Individual MVP generation project


class TenantStatus(str, Enum):
    """Tenant status values for lifecycle management"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    INACTIVE = "inactive"
    CANCELLED = "cancelled"


class TenantPlan(str, Enum):
    """Tenant subscription plans"""
    # Enterprise plans
    DEVELOPER = "developer"  # $50/month - 1 user, 5 projects
    TEAM = "team"           # $200/month - 10 users, 50 projects
    ENTERPRISE = "enterprise"  # $800/month - unlimited users/projects
    
    # MVP Factory plans
    MVP_SINGLE = "mvp_single"  # $5,000 one-time - single MVP generation
    MVP_BUNDLE = "mvp_bundle"  # $15,000 one-time - 5 MVP generations with priority support


class TenantDataResidency(str, Enum):
    """Data residency requirements for compliance"""
    US = "us"
    EU = "eu"
    UK = "uk"
    CANADA = "canada"
    AUSTRALIA = "australia"


class TenantQuotas(BaseModel):
    """Resource quotas per tenant based on subscription plan"""
    # Enterprise quotas
    max_users: int = Field(description="Maximum number of users")
    max_projects: int = Field(description="Maximum number of projects") 
    max_api_calls_per_month: int = Field(description="API call quota")
    max_storage_mb: int = Field(description="Storage quota in MB")
    max_ai_requests_per_day: int = Field(description="AI processing quota")
    max_concurrent_sessions: int = Field(description="Concurrent WebSocket sessions")
    
    # MVP Factory quotas  
    max_concurrent_mvps: int = Field(default=0, description="Maximum concurrent MVPs being generated")
    max_mvp_generations: int = Field(default=0, description="Maximum MVP generations allowed")
    max_cpu_cores: int = Field(default=0, description="Maximum CPU cores for MVP generation")
    max_memory_gb: int = Field(default=0, description="Maximum memory in GB for MVP generation")
    max_deployment_duration_hours: int = Field(default=0, description="Maximum deployment duration per MVP")
    max_custom_domains: int = Field(default=0, description="Maximum custom domains per MVP")
    
    model_config = ConfigDict(extra="ignore")


class TenantConfiguration(BaseModel):
    """Tenant-specific configuration settings"""
    branding: Dict[str, str] = Field(default_factory=dict, description="Custom branding settings")
    features: Dict[str, bool] = Field(default_factory=dict, description="Feature flag overrides")
    integrations: Dict[str, Any] = Field(default_factory=dict, description="Third-party integrations")
    security_settings: Dict[str, Any] = Field(default_factory=dict, description="Security configuration")
    
    model_config = ConfigDict(extra="ignore")


class Tenant(BaseModel):
    """Core tenant model for hybrid multi-tenant architecture (Enterprise + MVP Factory)"""
    id: UUID = Field(default_factory=uuid4, description="Tenant unique identifier")
    
    # Tenant type and identification
    tenant_type: TenantType = Field(description="Type of tenant (enterprise or MVP factory)")
    organization_name: str = Field(description="Organization/company name or MVP project name")
    display_name: Optional[str] = Field(default=None, description="Friendly display name")
    slug: str = Field(description="URL-safe tenant identifier")
    
    # Status and lifecycle
    status: TenantStatus = Field(default=TenantStatus.TRIAL, description="Current tenant status")
    plan: TenantPlan = Field(default=TenantPlan.DEVELOPER, description="Subscription plan")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Tenant creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    trial_ends_at: Optional[datetime] = Field(default=None, description="Trial expiration date")
    subscription_ends_at: Optional[datetime] = Field(default=None, description="Subscription end date")
    last_activity_at: datetime = Field(default_factory=datetime.utcnow, description="Last activity timestamp")
    
    # Contact and billing
    admin_email: str = Field(description="Primary admin email")
    billing_email: Optional[str] = Field(default=None, description="Billing contact email")
    
    # MVP Factory specific fields
    founder_name: Optional[str] = Field(default=None, description="Founder name (MVP Factory only)")
    founder_phone: Optional[str] = Field(default=None, description="Founder phone (MVP Factory only)")
    business_description: Optional[str] = Field(default=None, description="Business description (MVP Factory only)")
    target_market: Optional[str] = Field(default=None, description="Target market (MVP Factory only)")
    mvp_count_used: int = Field(default=0, description="Number of MVPs generated (MVP Factory only)")
    
    # Compliance and security
    data_residency: TenantDataResidency = Field(default=TenantDataResidency.US, description="Data residency requirement")
    encryption_key_id: Optional[str] = Field(default=None, description="Tenant-specific encryption key")
    
    # Resource management
    quotas: TenantQuotas = Field(description="Resource quotas")
    current_usage: Dict[str, int] = Field(default_factory=dict, description="Current resource usage")
    
    # Configuration
    configuration: TenantConfiguration = Field(default_factory=TenantConfiguration, description="Tenant configuration")
    
    # Hierarchy support (for enterprise organizations)
    parent_tenant_id: Optional[UUID] = Field(default=None, description="Parent tenant for hierarchical organizations")
    
    model_config = ConfigDict(extra="ignore")


class TenantCreate(BaseModel):
    """Schema for creating new tenants (Enterprise + MVP Factory)"""
    tenant_type: TenantType = Field(description="Type of tenant to create")
    organization_name: str = Field(..., min_length=2, max_length=255)
    display_name: Optional[str] = Field(None, max_length=255)
    slug: str = Field(..., min_length=2, max_length=50, pattern=r"^[a-z0-9-]+$")
    admin_email: str = Field(..., pattern=r"^[^@]+@[^@]+\.[^@]+$")
    plan: TenantPlan = Field(default=TenantPlan.DEVELOPER)
    data_residency: TenantDataResidency = Field(default=TenantDataResidency.US)
    parent_tenant_id: Optional[UUID] = Field(default=None)
    
    # MVP Factory specific fields (required only for MVP Factory tenants)
    founder_name: Optional[str] = Field(None, max_length=255, description="Founder name (MVP Factory only)")
    founder_phone: Optional[str] = Field(None, max_length=50, description="Founder phone (MVP Factory only)")
    business_description: Optional[str] = Field(None, max_length=2000, description="Business description (MVP Factory only)")
    target_market: Optional[str] = Field(None, max_length=500, description="Target market (MVP Factory only)")
    
    model_config = ConfigDict(extra="ignore")


class TenantUpdate(BaseModel):
    """Schema for updating tenant information"""
    organization_name: Optional[str] = Field(None, min_length=2, max_length=255)
    display_name: Optional[str] = Field(None, max_length=255)
    status: Optional[TenantStatus] = None
    plan: Optional[TenantPlan] = None
    admin_email: Optional[str] = Field(None, pattern=r"^[^@]+@[^@]+\.[^@]+$")
    billing_email: Optional[str] = Field(None, pattern=r"^[^@]+@[^@]+\.[^@]+$")
    data_residency: Optional[TenantDataResidency] = None
    configuration: Optional[TenantConfiguration] = None
    
    # MVP Factory specific fields
    founder_name: Optional[str] = Field(None, max_length=255)
    founder_phone: Optional[str] = Field(None, max_length=50)
    business_description: Optional[str] = Field(None, max_length=2000)
    target_market: Optional[str] = Field(None, max_length=500)
    mvp_count_used: Optional[int] = Field(None, ge=0)
    
    model_config = ConfigDict(extra="ignore")


class TenantUsage(BaseModel):
    """Current tenant resource usage"""
    tenant_id: UUID = Field(description="Tenant identifier")
    users_count: int = Field(default=0, description="Current number of users")
    projects_count: int = Field(default=0, description="Current number of projects")
    api_calls_this_month: int = Field(default=0, description="API calls in current month")
    storage_used_mb: int = Field(default=0, description="Storage used in MB")
    ai_requests_today: int = Field(default=0, description="AI requests today")
    concurrent_sessions: int = Field(default=0, description="Current concurrent sessions")
    last_calculated_at: datetime = Field(default_factory=datetime.utcnow, description="Last calculation timestamp")
    
    model_config = ConfigDict(extra="ignore")


class TenantQuotaExceeded(BaseModel):
    """Model for quota exceeded notifications"""
    tenant_id: UUID
    quota_type: str
    current_usage: int
    quota_limit: int
    exceeded_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(extra="ignore")


class TenantMember(BaseModel):
    """Tenant membership model"""
    id: UUID = Field(default_factory=uuid4, description="Membership unique identifier")
    tenant_id: UUID = Field(description="Tenant identifier")
    user_id: UUID = Field(description="User identifier")
    email: str = Field(description="User email")
    role: str = Field(description="User role within tenant")
    status: str = Field(default="active", description="Membership status")
    invited_at: datetime = Field(default_factory=datetime.utcnow, description="Invitation timestamp")
    joined_at: Optional[datetime] = Field(default=None, description="Join timestamp")
    last_activity_at: Optional[datetime] = Field(default=None, description="Last activity timestamp")
    
    model_config = ConfigDict(extra="ignore")


# Default quota configurations based on plan
DEFAULT_QUOTAS = {
    # Enterprise Plans
    TenantPlan.DEVELOPER: TenantQuotas(
        max_users=1,
        max_projects=5,
        max_api_calls_per_month=10000,
        max_storage_mb=1024,  # 1GB
        max_ai_requests_per_day=100,
        max_concurrent_sessions=2,
        max_concurrent_mvps=0,  # No MVP generation for enterprise plans
        max_mvp_generations=0,
        max_cpu_cores=0,
        max_memory_gb=0,
        max_deployment_duration_hours=0,
        max_custom_domains=0
    ),
    TenantPlan.TEAM: TenantQuotas(
        max_users=10,
        max_projects=50,
        max_api_calls_per_month=100000,
        max_storage_mb=10240,  # 10GB
        max_ai_requests_per_day=1000,
        max_concurrent_sessions=10,
        max_concurrent_mvps=0,  # No MVP generation for enterprise plans
        max_mvp_generations=0,
        max_cpu_cores=0,
        max_memory_gb=0,
        max_deployment_duration_hours=0,
        max_custom_domains=0
    ),
    TenantPlan.ENTERPRISE: TenantQuotas(
        max_users=999999,  # Unlimited
        max_projects=999999,  # Unlimited
        max_api_calls_per_month=999999999,  # Unlimited
        max_storage_mb=1048576,  # 1TB
        max_ai_requests_per_day=10000,
        max_concurrent_sessions=100,
        max_concurrent_mvps=0,  # No MVP generation for enterprise plans
        max_mvp_generations=0,
        max_cpu_cores=0,
        max_memory_gb=0,
        max_deployment_duration_hours=0,
        max_custom_domains=0
    ),
    
    # MVP Factory Plans
    TenantPlan.MVP_SINGLE: TenantQuotas(
        max_users=1,  # Just the founder
        max_projects=1,  # The MVP project
        max_api_calls_per_month=50000,  # High API limit for MVP generation
        max_storage_mb=5120,  # 5GB for MVP assets
        max_ai_requests_per_day=500,  # High AI quota for generation
        max_concurrent_sessions=5,  # Multiple sessions during generation
        max_concurrent_mvps=1,  # Single concurrent MVP generation
        max_mvp_generations=1,  # Single MVP generation
        max_cpu_cores=4,  # 4 CPU cores for generation
        max_memory_gb=16,  # 16GB memory for generation
        max_deployment_duration_hours=168,  # 7 days deployment included
        max_custom_domains=1  # Custom domain included
    ),
    TenantPlan.MVP_BUNDLE: TenantQuotas(
        max_users=1,  # Just the founder
        max_projects=5,  # Up to 5 MVP projects
        max_api_calls_per_month=250000,  # Very high API limit
        max_storage_mb=25600,  # 25GB for multiple MVPs
        max_ai_requests_per_day=2500,  # Very high AI quota
        max_concurrent_sessions=10,  # Multiple concurrent sessions
        max_concurrent_mvps=2,  # Up to 2 concurrent MVP generations
        max_mvp_generations=5,  # 5 MVP generations
        max_cpu_cores=8,  # 8 CPU cores for faster generation
        max_memory_gb=32,  # 32GB memory for generation
        max_deployment_duration_hours=720,  # 30 days deployment per MVP
        max_custom_domains=5  # 5 custom domains
    )
}