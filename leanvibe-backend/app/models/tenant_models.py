"""
Multi-tenant models for LeanVibe Enterprise SaaS Platform
Provides tenant isolation, resource quotas, and organization hierarchy
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict


class TenantStatus(str, Enum):
    """Tenant status values for lifecycle management"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    INACTIVE = "inactive"
    CANCELLED = "cancelled"


class TenantPlan(str, Enum):
    """Tenant subscription plans"""
    DEVELOPER = "developer"  # $50/month - 1 user, 5 projects
    TEAM = "team"           # $200/month - 10 users, 50 projects
    ENTERPRISE = "enterprise"  # $800/month - unlimited users/projects


class TenantDataResidency(str, Enum):
    """Data residency requirements for compliance"""
    US = "us"
    EU = "eu"
    UK = "uk"
    CANADA = "canada"
    AUSTRALIA = "australia"


class TenantQuotas(BaseModel):
    """Resource quotas per tenant based on subscription plan"""
    max_users: int = Field(description="Maximum number of users")
    max_projects: int = Field(description="Maximum number of projects")
    max_api_calls_per_month: int = Field(description="API call quota")
    max_storage_mb: int = Field(description="Storage quota in MB")
    max_ai_requests_per_day: int = Field(description="AI processing quota")
    max_concurrent_sessions: int = Field(description="Concurrent WebSocket sessions")
    
    model_config = ConfigDict(extra="ignore")


class TenantConfiguration(BaseModel):
    """Tenant-specific configuration settings"""
    branding: Dict[str, str] = Field(default_factory=dict, description="Custom branding settings")
    features: Dict[str, bool] = Field(default_factory=dict, description="Feature flag overrides")
    integrations: Dict[str, Any] = Field(default_factory=dict, description="Third-party integrations")
    security_settings: Dict[str, Any] = Field(default_factory=dict, description="Security configuration")
    
    model_config = ConfigDict(extra="ignore")


class Tenant(BaseModel):
    """Core tenant model for multi-tenant architecture"""
    id: UUID = Field(default_factory=uuid4, description="Tenant unique identifier")
    organization_name: str = Field(description="Organization/company name")
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
    """Schema for creating new tenants"""
    organization_name: str = Field(..., min_length=2, max_length=255)
    display_name: Optional[str] = Field(None, max_length=255)
    slug: str = Field(..., min_length=2, max_length=50, pattern=r"^[a-z0-9-]+$")
    admin_email: str = Field(..., pattern=r"^[^@]+@[^@]+\.[^@]+$")
    plan: TenantPlan = Field(default=TenantPlan.DEVELOPER)
    data_residency: TenantDataResidency = Field(default=TenantDataResidency.US)
    parent_tenant_id: Optional[UUID] = Field(default=None)
    
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
    TenantPlan.DEVELOPER: TenantQuotas(
        max_users=1,
        max_projects=5,
        max_api_calls_per_month=10000,
        max_storage_mb=1024,  # 1GB
        max_ai_requests_per_day=100,
        max_concurrent_sessions=2
    ),
    TenantPlan.TEAM: TenantQuotas(
        max_users=10,
        max_projects=50,
        max_api_calls_per_month=100000,
        max_storage_mb=10240,  # 10GB
        max_ai_requests_per_day=1000,
        max_concurrent_sessions=10
    ),
    TenantPlan.ENTERPRISE: TenantQuotas(
        max_users=999999,  # Unlimited
        max_projects=999999,  # Unlimited
        max_api_calls_per_month=999999999,  # Unlimited
        max_storage_mb=1048576,  # 1TB
        max_ai_requests_per_day=10000,
        max_concurrent_sessions=100
    )
}