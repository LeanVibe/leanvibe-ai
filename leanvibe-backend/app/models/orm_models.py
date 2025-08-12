"""
SQLAlchemy ORM Models for LeanVibe Enterprise Platform
Multi-tenant database architecture with row-level security
"""

from datetime import datetime
from typing import Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Column, String, DateTime, Boolean, Integer, Float, Text, JSON,
    ForeignKey, Enum as SQLEnum, Index, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property

from ..core.database import Base
from .tenant_models import TenantStatus, TenantPlan, TenantDataResidency, TenantType
from .task_models import TaskStatus, TaskPriority
from .auth_models import UserStatus, UserRole, AuthProvider, SessionStatus, MFAMethod


class TenantORM(Base):
    """SQLAlchemy ORM model for hybrid tenants (Enterprise + MVP Factory)"""
    __tablename__ = "tenants"
    
    # Primary key and identification
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    
    # Tenant type and identification
    tenant_type = Column(SQLEnum(TenantType), nullable=False, index=True)
    organization_name = Column(String(255), nullable=False, index=True)
    display_name = Column(String(255), nullable=True)
    slug = Column(String(50), nullable=False, unique=True, index=True)
    
    # Status and lifecycle
    status = Column(SQLEnum(TenantStatus), default=TenantStatus.TRIAL, nullable=False, index=True)
    plan = Column(SQLEnum(TenantPlan), default=TenantPlan.DEVELOPER, nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    trial_ends_at = Column(DateTime, nullable=True)
    subscription_ends_at = Column(DateTime, nullable=True)
    last_activity_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Contact and billing
    admin_email = Column(String(255), nullable=False, index=True)
    billing_email = Column(String(255), nullable=True)
    
    # MVP Factory specific fields
    founder_name = Column(String(255), nullable=True)
    founder_phone = Column(String(50), nullable=True)
    business_description = Column(Text, nullable=True)
    target_market = Column(String(500), nullable=True)
    mvp_count_used = Column(Integer, default=0, nullable=False)
    
    # Compliance and security
    data_residency = Column(SQLEnum(TenantDataResidency), default=TenantDataResidency.US, nullable=False)
    encryption_key_id = Column(String(255), nullable=True)
    
    # Resource management (stored as JSON for flexibility)
    quotas = Column(JSON, nullable=False, default=dict)
    current_usage = Column(JSON, nullable=False, default=dict)
    
    # Configuration
    configuration = Column(JSON, nullable=False, default=dict)
    
    # Hierarchy support
    parent_tenant_id = Column(PG_UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=True)
    
    # Relationships
    parent_tenant = relationship("TenantORM", remote_side=[id])
    tenant_members = relationship("TenantMemberORM", back_populates="tenant", cascade="all, delete-orphan")
    tasks = relationship("TaskORM", back_populates="tenant", cascade="all, delete-orphan")
    projects = relationship("ProjectORM", back_populates="tenant", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_tenant_status_plan', 'status', 'plan'),
        Index('idx_tenant_activity', 'last_activity_at'),
        Index('idx_tenant_org_name', 'organization_name'),
        CheckConstraint('created_at <= updated_at', name='chk_tenant_timestamps'),
        CheckConstraint("admin_email LIKE '%@%'", name='chk_admin_email_format'),
    )
    
    @validates('slug')
    def validate_slug(self, key, slug):
        """Validate slug format"""
        import re
        if not re.match(r'^[a-z0-9-]+$', slug):
            raise ValueError('Slug must contain only lowercase letters, numbers, and hyphens')
        return slug
    
    @hybrid_property
    def is_active(self):
        """Check if tenant is active"""
        return self.status == TenantStatus.ACTIVE
    
    @hybrid_property
    def is_trial(self):
        """Check if tenant is in trial"""
        return self.status == TenantStatus.TRIAL
    
    def __repr__(self):
        return f"<TenantORM(id={self.id}, org={self.organization_name}, status={self.status})>"


class TenantMemberORM(Base):
    """SQLAlchemy ORM model for tenant membership"""
    __tablename__ = "tenant_members"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    tenant_id = Column(PG_UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False, index=True)
    user_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)  # References external user system
    email = Column(String(255), nullable=False, index=True)
    role = Column(String(50), nullable=False, default='member')
    status = Column(String(20), nullable=False, default='active')
    
    # Timestamps
    invited_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    joined_at = Column(DateTime, nullable=True)
    last_activity_at = Column(DateTime, nullable=True)
    
    # Relationships
    tenant = relationship("TenantORM", back_populates="tenant_members")
    
    # Indexes and constraints
    __table_args__ = (
        Index('idx_member_tenant_user', 'tenant_id', 'user_id', unique=True),
        Index('idx_member_email', 'email'),
        Index('idx_member_role', 'role'),
        CheckConstraint("email LIKE '%@%'", name='chk_member_email_format'),
    )
    
    def __repr__(self):
        return f"<TenantMemberORM(tenant_id={self.tenant_id}, email={self.email}, role={self.role})>"


class TaskORM(Base):
    """SQLAlchemy ORM model for tasks with multi-tenant support"""
    __tablename__ = "tasks"
    
    # Primary identification
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Status and organization
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.TODO, nullable=False, index=True)
    priority = Column(SQLEnum(TaskPriority), default=TaskPriority.MEDIUM, nullable=False, index=True)
    
    # Multi-tenant isolation (CRITICAL for enterprise)
    tenant_id = Column(PG_UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False, index=True)
    project_id = Column(PG_UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # AI and assignment fields
    confidence = Column(Float, default=1.0, nullable=False)
    agent_decision = Column(JSON, nullable=True)
    
    # Assignment and tracking
    client_id = Column(String(255), nullable=False, index=True)  # Legacy compatibility
    created_by = Column(PG_UUID(as_uuid=True), nullable=True, index=True)
    assigned_to = Column(String(255), nullable=True, index=True)
    
    # Effort tracking
    estimated_effort = Column(Float, nullable=True)  # hours
    actual_effort = Column(Float, nullable=True)     # hours
    
    # Organization and metadata
    tags = Column(JSON, nullable=False, default=list)  # List of strings
    dependencies = Column(JSON, nullable=False, default=list)  # List of task IDs
    attachments = Column(JSON, nullable=False, default=list)   # List of attachment objects
    task_metadata = Column(JSON, nullable=False, default=dict)     # Additional task metadata (renamed from metadata)
    
    # Relationships
    tenant = relationship("TenantORM", back_populates="tasks")
    project = relationship("ProjectORM", back_populates="tasks")
    
    # Indexes for performance and tenant isolation
    __table_args__ = (
        # Critical: All queries must filter by tenant_id first
        Index('idx_task_tenant_status', 'tenant_id', 'status'),
        Index('idx_task_tenant_project', 'tenant_id', 'project_id'),
        Index('idx_task_tenant_priority', 'tenant_id', 'priority'),
        Index('idx_task_tenant_created', 'tenant_id', 'created_at'),
        Index('idx_task_tenant_assigned', 'tenant_id', 'assigned_to'),
        # Ensure all timestamps are logical
        CheckConstraint('created_at <= updated_at', name='chk_task_timestamps'),
        CheckConstraint('confidence >= 0.0 AND confidence <= 1.0', name='chk_task_confidence'),
        CheckConstraint('estimated_effort IS NULL OR estimated_effort >= 0', name='chk_estimated_effort'),
        CheckConstraint('actual_effort IS NULL OR actual_effort >= 0', name='chk_actual_effort'),
    )
    
    @hybrid_property
    def is_completed(self):
        """Check if task is completed"""
        return self.status == TaskStatus.DONE
    
    @hybrid_property  
    def is_overdue(self):
        """Check if task is overdue (placeholder for due date functionality)"""
        # TODO: Implement when due_date field is added
        return False
    
    def __repr__(self):
        return f"<TaskORM(id={self.id}, tenant_id={self.tenant_id}, title='{self.title[:30]}...', status={self.status})>"


class ProjectORM(Base):
    """SQLAlchemy ORM model for projects with multi-tenant support"""
    __tablename__ = "projects"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Multi-tenant isolation
    tenant_id = Column(PG_UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False, index=True)
    
    # Project metadata
    status = Column(String(50), default='active', nullable=False, index=True)
    repository_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Project configuration
    settings = Column(JSON, nullable=False, default=dict)
    
    # Relationships
    tenant = relationship("TenantORM", back_populates="projects")
    tasks = relationship("TaskORM", back_populates="project", cascade="all, delete-orphan")
    
    # Indexes for tenant isolation and performance
    __table_args__ = (
        Index('idx_project_tenant_name', 'tenant_id', 'name'),
        Index('idx_project_tenant_status', 'tenant_id', 'status'),
        Index('idx_project_tenant_created', 'tenant_id', 'created_at'),
        CheckConstraint('created_at <= updated_at', name='chk_project_timestamps'),
    )
    
    def __repr__(self):
        return f"<ProjectORM(id={self.id}, tenant_id={self.tenant_id}, name='{self.name}')>"


class AuditLogORM(Base):
    """Audit log for compliance and security tracking"""
    __tablename__ = "audit_logs"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    
    # Multi-tenant isolation
    tenant_id = Column(PG_UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False, index=True)
    
    # Audit information
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False, index=True)
    resource_id = Column(String(255), nullable=True, index=True)
    user_id = Column(PG_UUID(as_uuid=True), nullable=True, index=True)
    user_email = Column(String(255), nullable=True, index=True)
    
    # Audit details
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    details = Column(JSON, nullable=False, default=dict)
    ip_address = Column(String(45), nullable=True)  # IPv6 support
    user_agent = Column(Text, nullable=True)
    
    # Relationships
    tenant = relationship("TenantORM")
    
    # Indexes for compliance queries
    __table_args__ = (
        Index('idx_audit_tenant_action', 'tenant_id', 'action'),
        Index('idx_audit_tenant_resource', 'tenant_id', 'resource_type', 'resource_id'),
        Index('idx_audit_tenant_user', 'tenant_id', 'user_id'),
        Index('idx_audit_timestamp', 'timestamp'),  # For time-based compliance queries
    )
    
    def __repr__(self):
        return f"<AuditLogORM(tenant_id={self.tenant_id}, action={self.action}, timestamp={self.timestamp})>"


class MVPProjectORM(Base):
    """SQLAlchemy ORM model for MVP Factory projects"""
    __tablename__ = "mvp_projects"
    
    # Primary key and identification
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    
    # Multi-tenant isolation
    tenant_id = Column(PG_UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False, index=True)
    
    # Project identification
    project_name = Column(String(255), nullable=False, index=True)
    slug = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=False)
    
    # Project status and lifecycle
    status = Column(String(50), nullable=False, index=True, default="blueprint_pending")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    deployed_at = Column(DateTime, nullable=True)
    
    # Core components (stored as JSON for flexibility)
    interview_data = Column(JSON, nullable=True)
    blueprint_data = Column(JSON, nullable=True)  
    generation_progress = Column(JSON, nullable=False, default=dict)
    
    # Human approval workflows (stored as JSON)
    blueprint_approval = Column(JSON, nullable=True)
    deployment_approval = Column(JSON, nullable=True)
    
    # Deployment information
    deployment_url = Column(String(500), nullable=True)
    repository_url = Column(String(500), nullable=True) 
    monitoring_dashboard_url = Column(String(500), nullable=True)
    admin_panel_url = Column(String(500), nullable=True)
    
    # Resource usage tracking
    cpu_hours_used = Column(Float, default=0.0, nullable=False)
    memory_gb_hours_used = Column(Float, default=0.0, nullable=False)
    storage_mb_used = Column(Integer, default=0, nullable=False)
    ai_tokens_used = Column(Integer, default=0, nullable=False)
    
    # Success metrics
    generation_success_rate = Column(Float, default=0.0, nullable=False)
    deployment_uptime = Column(Float, default=0.0, nullable=False)
    founder_satisfaction_score = Column(Integer, nullable=True)
    
    # Billing and payment
    total_cost = Column(Float, default=0.0, nullable=False)
    payment_status = Column(String(50), default="pending", nullable=False)
    payment_method = Column(String(50), nullable=True)
    
    # Relationships
    tenant = relationship("TenantORM")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_mvp_tenant_status', 'tenant_id', 'status'),
        Index('idx_mvp_tenant_created', 'tenant_id', 'created_at'),
        Index('idx_mvp_slug_tenant', 'slug', 'tenant_id'),
        Index('idx_mvp_deployment_status', 'status', 'deployed_at'),
        CheckConstraint('created_at <= updated_at', name='chk_mvp_timestamps'),
        CheckConstraint('cpu_hours_used >= 0', name='chk_cpu_hours_positive'),
        CheckConstraint('memory_gb_hours_used >= 0', name='chk_memory_hours_positive'),
        CheckConstraint('storage_mb_used >= 0', name='chk_storage_positive'),
        CheckConstraint('founder_satisfaction_score >= 1 AND founder_satisfaction_score <= 10', 
                       name='chk_satisfaction_range'),
    )
    
    @hybrid_property
    def is_deployed(self):
        """Check if MVP is deployed"""
        return self.status == "deployed"
    
    @hybrid_property
    def is_generating(self):
        """Check if MVP is currently being generated"""
        return self.status in ["generating", "testing", "deploying"]
    
    def __repr__(self):
        return f"<MVPProjectORM(id={self.id}, name={self.project_name}, status={self.status})>"


class MVPMetricsORM(Base):
    """SQLAlchemy ORM model for MVP performance and business metrics"""
    __tablename__ = "mvp_metrics"
    
    # Primary key
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    
    # Multi-tenant isolation via MVP project
    mvp_project_id = Column(PG_UUID(as_uuid=True), ForeignKey('mvp_projects.id'), nullable=False, index=True)
    
    # Performance metrics
    response_time_ms = Column(Float, nullable=False)
    uptime_percentage = Column(Float, nullable=False)
    error_rate = Column(Float, nullable=False)
    
    # Business metrics
    page_views = Column(Integer, default=0, nullable=False)
    unique_visitors = Column(Integer, default=0, nullable=False)
    conversion_rate = Column(Float, default=0.0, nullable=False)
    user_signups = Column(Integer, default=0, nullable=False)
    
    # Technical metrics
    code_quality_score = Column(Float, nullable=False)
    test_coverage = Column(Float, nullable=False) 
    security_score = Column(Float, nullable=False)
    
    # Collection timestamp
    collected_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    mvp_project = relationship("MVPProjectORM")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_metrics_project_time', 'mvp_project_id', 'collected_at'),
        Index('idx_metrics_collection_time', 'collected_at'),
        CheckConstraint('response_time_ms >= 0', name='chk_response_time_positive'),
        CheckConstraint('uptime_percentage >= 0 AND uptime_percentage <= 100', name='chk_uptime_range'),
        CheckConstraint('error_rate >= 0 AND error_rate <= 100', name='chk_error_rate_range'),
        CheckConstraint('code_quality_score >= 0 AND code_quality_score <= 100', name='chk_code_quality_range'),
        CheckConstraint('test_coverage >= 0 AND test_coverage <= 100', name='chk_test_coverage_range'),
        CheckConstraint('security_score >= 0 AND security_score <= 100', name='chk_security_score_range'),
    )
    
    def __repr__(self):
        return f"<MVPMetricsORM(mvp_id={self.mvp_project_id}, collected_at={self.collected_at})>"


# ------------------------
# Pipeline Execution Models
# ------------------------


class PipelineExecutionORM(Base):
    """Pipeline execution tracking ORM model"""
    __tablename__ = "pipeline_executions"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    mvp_project_id = Column(PG_UUID(as_uuid=True), ForeignKey('mvp_projects.id'), nullable=False, index=True)
    tenant_id = Column(PG_UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False, index=True)
    
    current_stage = Column(String(64), nullable=False, default="interview_received", index=True)
    status = Column(String(64), nullable=False, default="initializing", index=True)
    
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)
    current_stage_started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    stages_completed = Column(JSON, nullable=False, default=list)
    stage_durations = Column(JSON, nullable=False, default=dict)
    
    overall_progress = Column(Float, default=0.0, nullable=False)
    current_stage_progress = Column(Float, default=0.0, nullable=False)
    
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    
    __table_args__ = (
        Index('idx_exec_project_time', 'mvp_project_id', 'started_at'),
        Index('idx_exec_tenant_status', 'tenant_id', 'status'),
    )
    
    def __repr__(self):
        return f"<PipelineExecutionORM(id={self.id}, project={self.mvp_project_id}, status={self.status})>"


class PipelineExecutionLogORM(Base):
    """Pipeline execution log entries"""
    __tablename__ = "pipeline_execution_logs"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    execution_id = Column(PG_UUID(as_uuid=True), ForeignKey('pipeline_executions.id'), nullable=False, index=True)
    tenant_id = Column(PG_UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False, index=True)
    mvp_project_id = Column(PG_UUID(as_uuid=True), ForeignKey('mvp_projects.id'), nullable=False, index=True)
    
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    level = Column(String(16), nullable=False, index=True)
    message = Column(Text, nullable=False)
    stage = Column(String(64), nullable=True)
    # 'metadata' is reserved by SQLAlchemy declarative; map column name to different attribute
    log_metadata = Column('metadata', JSON, nullable=True)
    
    __table_args__ = (
        Index('idx_exec_logs_exec_time', 'execution_id', 'timestamp'),
        Index('idx_exec_logs_tenant_time', 'tenant_id', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<PipelineExecutionLogORM(exec={self.execution_id}, level={self.level})>"

# Row-Level Security Policies (Applied via migrations)
"""
These policies will be implemented in Alembic migrations:

-- Enable row-level security on all tenant-isolated tables
ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_members ENABLE ROW LEVEL SECURITY;  
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- Create policies for tenant isolation
CREATE POLICY tenant_isolation_policy ON tasks
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

CREATE POLICY project_isolation_policy ON projects  
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

CREATE POLICY audit_isolation_policy ON audit_logs
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- Tenant members can only see their own tenant's data
CREATE POLICY member_isolation_policy ON tenant_members
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- Super admin bypass (for system operations)
CREATE POLICY admin_bypass_policy ON tasks
    USING (current_setting('app.user_role', true) = 'superadmin');
"""


class UserORM(Base):
    """SQLAlchemy ORM model for users with enterprise authentication"""
    __tablename__ = "users"
    
    # Primary key and identification
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    tenant_id = Column(PG_UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False, index=True)
    
    # Basic user information
    email = Column(String(255), nullable=False, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    display_name = Column(String(100), nullable=True)
    
    # Authentication
    password_hash = Column(String(255), nullable=True)  # For local auth
    auth_provider = Column(SQLEnum(AuthProvider), default=AuthProvider.LOCAL, nullable=False, index=True)
    external_id = Column(String(255), nullable=True, index=True)  # External provider user ID
    
    # Status and permissions
    status = Column(SQLEnum(UserStatus), default=UserStatus.PENDING_ACTIVATION, nullable=False, index=True)
    role = Column(SQLEnum(UserRole), default=UserRole.DEVELOPER, nullable=False, index=True)
    permissions = Column(JSON, nullable=False, default=list)
    
    # Multi-factor authentication
    mfa_enabled = Column(Boolean, default=False, nullable=False)
    mfa_methods = Column(JSON, nullable=False, default=list)  # List of MFAMethod values
    mfa_secret = Column(String(255), nullable=True)  # TOTP secret key
    backup_codes = Column(JSON, nullable=False, default=list)  # MFA backup codes
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login_at = Column(DateTime, nullable=True, index=True)
    password_changed_at = Column(DateTime, nullable=True)
    
    # Security settings
    require_password_change = Column(Boolean, default=False, nullable=False)
    login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)
    
    # Profile information
    profile = Column(JSON, nullable=False, default=dict)
    preferences = Column(JSON, nullable=False, default=dict)
    
    # Email verification
    email_verified = Column(Boolean, default=False, nullable=False)
    email_verification_token = Column(String(255), nullable=True)
    email_verification_expires = Column(DateTime, nullable=True)
    
    # Password reset
    password_reset_token = Column(String(255), nullable=True)
    password_reset_expires = Column(DateTime, nullable=True)
    
    # Relationships
    tenant = relationship("TenantORM")
    user_sessions = relationship("UserSessionORM", back_populates="user", cascade="all, delete-orphan")
    
    # Indexes for performance and tenant isolation
    __table_args__ = (
        # Unique email within tenant
        Index('idx_user_tenant_email', 'tenant_id', 'email', unique=True),
        Index('idx_user_tenant_status', 'tenant_id', 'status'),
        Index('idx_user_tenant_role', 'tenant_id', 'role'),
        Index('idx_user_provider_external', 'auth_provider', 'external_id'),
        Index('idx_user_verification_token', 'email_verification_token'),
        Index('idx_user_reset_token', 'password_reset_token'),
        CheckConstraint('created_at <= updated_at', name='chk_user_timestamps'),
        CheckConstraint("email LIKE '%@%'", name='chk_user_email_format'),
        CheckConstraint('login_attempts >= 0', name='chk_login_attempts_positive'),
    )
    
    @validates('email')
    def validate_email(self, key, email):
        """Validate email format"""
        if not email or '@' not in email:
            raise ValueError('Invalid email address')
        return email.lower()
    
    @hybrid_property
    def is_active(self):
        """Check if user is active"""
        return self.status == UserStatus.ACTIVE
    
    @hybrid_property
    def is_locked(self):
        """Check if user account is locked"""
        return self.locked_until and self.locked_until > datetime.utcnow()
    
    @hybrid_property
    def full_name(self):
        """Get user's full name"""
        return f"{self.first_name} {self.last_name}"
    
    def __repr__(self):
        return f"<UserORM(id={self.id}, tenant_id={self.tenant_id}, email={self.email}, status={self.status})>"


class UserSessionORM(Base):
    """SQLAlchemy ORM model for user sessions"""
    __tablename__ = "user_sessions"
    
    # Primary identification
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    tenant_id = Column(PG_UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False, index=True)
    
    # Session details
    status = Column(SQLEnum(SessionStatus), default=SessionStatus.ACTIVE, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    last_activity_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Security information
    ip_address = Column(String(45), nullable=True)  # IPv6 support
    user_agent = Column(Text, nullable=True)
    location = Column(JSON, nullable=True)  # Geographic location data
    
    # Authentication method used for this session
    auth_method = Column(SQLEnum(AuthProvider), nullable=False, index=True)
    mfa_verified = Column(Boolean, default=False, nullable=False)
    
    # Token information (hashed for security)
    access_token_hash = Column(String(64), nullable=False, index=True)  # SHA-256 hash
    refresh_token_hash = Column(String(64), nullable=True, index=True)  # SHA-256 hash
    
    # Relationships
    user = relationship("UserORM", back_populates="user_sessions")
    tenant = relationship("TenantORM")
    
    # Indexes for performance and security
    __table_args__ = (
        Index('idx_session_tenant_user', 'tenant_id', 'user_id'),
        Index('idx_session_tenant_status', 'tenant_id', 'status'),
        Index('idx_session_expires', 'expires_at'),
        Index('idx_session_activity', 'last_activity_at'),
        Index('idx_session_access_token', 'access_token_hash'),
        Index('idx_session_refresh_token', 'refresh_token_hash'),
        CheckConstraint('created_at <= expires_at', name='chk_session_timestamps'),
        CheckConstraint('created_at <= last_activity_at', name='chk_session_activity'),
    )
    
    @hybrid_property
    def is_active(self):
        """Check if session is active and not expired"""
        return (
            self.status == SessionStatus.ACTIVE and 
            self.expires_at > datetime.utcnow()
        )
    
    @hybrid_property
    def is_expired(self):
        """Check if session has expired"""
        return self.expires_at <= datetime.utcnow()
    
    def __repr__(self):
        return f"<UserSessionORM(id={self.id}, user_id={self.user_id}, status={self.status}, expires={self.expires_at})>"


class PasswordPolicyORM(Base):
    """SQLAlchemy ORM model for tenant password policies"""
    __tablename__ = "password_policies"
    
    # Primary identification
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    tenant_id = Column(PG_UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False, unique=True, index=True)
    
    # Password requirements
    min_length = Column(Integer, default=12, nullable=False)
    require_uppercase = Column(Boolean, default=True, nullable=False)
    require_lowercase = Column(Boolean, default=True, nullable=False)
    require_digits = Column(Boolean, default=True, nullable=False)
    require_special = Column(Boolean, default=True, nullable=False)
    special_chars = Column(String(50), default="!@#$%^&*", nullable=False)
    
    # Security settings
    max_age_days = Column(Integer, default=90, nullable=False)
    history_count = Column(Integer, default=5, nullable=False)
    lockout_attempts = Column(Integer, default=5, nullable=False)
    lockout_duration_minutes = Column(Integer, default=30, nullable=False)
    
    # Common password checks
    prevent_common_passwords = Column(Boolean, default=True, nullable=False)
    prevent_personal_info = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    tenant = relationship("TenantORM")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('min_length >= 6 AND min_length <= 128', name='chk_min_length_range'),
        CheckConstraint('max_age_days >= 30 AND max_age_days <= 365', name='chk_max_age_range'),
        CheckConstraint('history_count >= 0 AND history_count <= 24', name='chk_history_range'),
        CheckConstraint('lockout_attempts >= 3 AND lockout_attempts <= 20', name='chk_lockout_attempts_range'),
        CheckConstraint('lockout_duration_minutes >= 5 AND lockout_duration_minutes <= 1440', name='chk_lockout_duration_range'),
        CheckConstraint('created_at <= updated_at', name='chk_policy_timestamps'),
    )
    
    def __repr__(self):
        return f"<PasswordPolicyORM(tenant_id={self.tenant_id}, min_length={self.min_length})>"


class SSOConfigurationORM(Base):
    """SQLAlchemy ORM model for SSO provider configurations"""
    __tablename__ = "sso_configurations"
    
    # Primary identification
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    tenant_id = Column(PG_UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False, index=True)
    
    # Provider details
    provider = Column(SQLEnum(AuthProvider), nullable=False, index=True)
    provider_name = Column(String(100), nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    
    # OAuth2/OpenID Connect settings
    client_id = Column(String(255), nullable=True)
    client_secret = Column(String(500), nullable=True)  # Encrypted in production
    auth_url = Column(String(500), nullable=True)
    token_url = Column(String(500), nullable=True)
    userinfo_url = Column(String(500), nullable=True)
    scopes = Column(JSON, nullable=False, default=list)
    
    # SAML settings
    saml_entity_id = Column(String(255), nullable=True)
    saml_sso_url = Column(String(500), nullable=True)
    saml_x509_cert = Column(Text, nullable=True)
    saml_metadata_url = Column(String(500), nullable=True)
    
    # User mapping
    attribute_mapping = Column(JSON, nullable=False, default=dict)
    
    # Auto-provisioning settings
    auto_provision_users = Column(Boolean, default=True, nullable=False)
    default_role = Column(SQLEnum(UserRole), default=UserRole.DEVELOPER, nullable=False)
    allowed_domains = Column(JSON, nullable=False, default=list)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    tenant = relationship("TenantORM")
    
    # Indexes and constraints
    __table_args__ = (
        Index('idx_sso_tenant_provider', 'tenant_id', 'provider', unique=True),
        Index('idx_sso_enabled', 'enabled'),
        CheckConstraint('created_at <= updated_at', name='chk_sso_timestamps'),
    )
    
    def __repr__(self):
        return f"<SSOConfigurationORM(tenant_id={self.tenant_id}, provider={self.provider}, enabled={self.enabled})>"


class AuthAuditLogORM(Base):
    """SQLAlchemy ORM model for authentication audit logs"""
    __tablename__ = "auth_audit_logs"
    
    # Primary identification
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    tenant_id = Column(PG_UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False, index=True)
    
    # Event details
    event_type = Column(String(50), nullable=False, index=True)
    event_description = Column(String(500), nullable=False)
    success = Column(Boolean, nullable=False, index=True)
    
    # User context
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey('users.id'), nullable=True, index=True)
    user_email = Column(String(255), nullable=True, index=True)
    
    # Security context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    location = Column(JSON, nullable=True)
    
    # Additional metadata
    event_metadata = Column(JSON, nullable=False, default=dict)
    
    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    tenant = relationship("TenantORM")
    user = relationship("UserORM")
    
    # Indexes for audit queries
    __table_args__ = (
        Index('idx_auth_audit_tenant_event', 'tenant_id', 'event_type'),
        Index('idx_auth_audit_tenant_user', 'tenant_id', 'user_id'),
        Index('idx_auth_audit_tenant_success', 'tenant_id', 'success'),
        Index('idx_auth_audit_timestamp', 'timestamp'),
        Index('idx_auth_audit_user_event', 'user_id', 'event_type'),
    )
    
    def __repr__(self):
        return f"<AuthAuditLogORM(tenant_id={self.tenant_id}, event={self.event_type}, timestamp={self.timestamp})>"