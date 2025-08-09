"""
Enterprise authentication models for LeanVibe SaaS Platform
Supports SSO, SAML, OAuth2, RBAC, and multi-factor authentication
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict


class AuthProvider(str, Enum):
    """Supported authentication providers"""
    LOCAL = "local"
    GOOGLE = "google"
    MICROSOFT = "microsoft"
    OKTA = "okta"
    AUTH0 = "auth0"
    SAML = "saml"
    LDAP = "ldap"


class UserStatus(str, Enum):
    """User account status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_ACTIVATION = "pending_activation"
    PENDING_PASSWORD_RESET = "pending_password_reset"


class UserRole(str, Enum):
    """User roles within a tenant"""
    OWNER = "owner"          # Full tenant admin rights
    ADMIN = "admin"          # Tenant administration
    MANAGER = "manager"      # Team management
    DEVELOPER = "developer"  # Full development access
    VIEWER = "viewer"        # Read-only access
    GUEST = "guest"          # Limited access


class MFAMethod(str, Enum):
    """Multi-factor authentication methods"""
    TOTP = "totp"              # Time-based One-Time Password (Google Authenticator)
    SMS = "sms"                # SMS-based verification
    EMAIL = "email"            # Email-based verification
    PUSH = "push"              # Push notification
    HARDWARE_TOKEN = "hardware" # Hardware security key


class SessionStatus(str, Enum):
    """User session status"""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    SUSPENDED = "suspended"


class User(BaseModel):
    """Core user model with enterprise features"""
    id: UUID = Field(default_factory=uuid4, description="User unique identifier")
    tenant_id: UUID = Field(description="Associated tenant identifier")
    
    # Basic user information
    email: str = Field(description="User email address (unique within tenant)")
    first_name: str = Field(description="User first name")
    last_name: str = Field(description="User last name")
    display_name: Optional[str] = Field(default=None, description="Display name")
    
    # Authentication
    password_hash: Optional[str] = Field(default=None, description="Hashed password (for local auth)")
    auth_provider: AuthProvider = Field(default=AuthProvider.LOCAL, description="Primary authentication provider")
    external_id: Optional[str] = Field(default=None, description="External provider user ID")
    
    # Status and permissions
    status: UserStatus = Field(default=UserStatus.PENDING_ACTIVATION, description="User account status")
    role: UserRole = Field(default=UserRole.DEVELOPER, description="User role within tenant")
    permissions: List[str] = Field(default_factory=list, description="Additional permissions")
    
    # Multi-factor authentication
    mfa_enabled: bool = Field(default=False, description="MFA enabled flag")
    mfa_methods: List[MFAMethod] = Field(default_factory=list, description="Enabled MFA methods")
    mfa_secret: Optional[str] = Field(default=None, description="TOTP secret key")
    backup_codes: List[str] = Field(default_factory=list, description="MFA backup codes")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Account creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    last_login_at: Optional[datetime] = Field(default=None, description="Last login timestamp")
    password_changed_at: Optional[datetime] = Field(default=None, description="Password last changed")
    
    # Security settings
    require_password_change: bool = Field(default=False, description="Force password change on next login")
    login_attempts: int = Field(default=0, description="Failed login attempts")
    locked_until: Optional[datetime] = Field(default=None, description="Account lock expiry")
    
    # Profile information
    profile: Dict[str, Any] = Field(default_factory=dict, description="Additional profile data")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="User preferences")
    
    model_config = ConfigDict(extra="ignore")


class UserCreate(BaseModel):
    """Schema for creating new users"""
    tenant_id: UUID = Field(description="Target tenant")
    email: str = Field(description="User email address")
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    role: UserRole = Field(default=UserRole.DEVELOPER)
    password: Optional[str] = Field(default=None, min_length=8, description="Password for local auth")
    auth_provider: AuthProvider = Field(default=AuthProvider.LOCAL)
    send_invitation: bool = Field(default=True, description="Send email invitation")
    
    model_config = ConfigDict(extra="ignore")


class UserUpdate(BaseModel):
    """Schema for updating user information"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    display_name: Optional[str] = Field(None, max_length=100)
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    permissions: Optional[List[str]] = None
    profile: Optional[Dict[str, Any]] = None
    preferences: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(extra="ignore")


class SSOConfiguration(BaseModel):
    """SSO provider configuration"""
    id: UUID = Field(default_factory=uuid4, description="Configuration identifier")
    tenant_id: UUID = Field(description="Associated tenant")
    
    # Provider details
    provider: AuthProvider = Field(description="SSO provider type")
    provider_name: str = Field(description="Display name for provider")
    enabled: bool = Field(default=True, description="Configuration enabled")
    
    # OAuth2/OpenID Connect settings
    client_id: Optional[str] = Field(default=None, description="OAuth client ID")
    client_secret: Optional[str] = Field(default=None, description="OAuth client secret")
    auth_url: Optional[str] = Field(default=None, description="Authorization endpoint")
    token_url: Optional[str] = Field(default=None, description="Token endpoint")
    userinfo_url: Optional[str] = Field(default=None, description="User info endpoint")
    scopes: List[str] = Field(default_factory=list, description="OAuth scopes")
    
    # SAML settings
    saml_entity_id: Optional[str] = Field(default=None, description="SAML entity ID")
    saml_sso_url: Optional[str] = Field(default=None, description="SAML SSO URL")
    saml_x509_cert: Optional[str] = Field(default=None, description="SAML X.509 certificate")
    saml_metadata_url: Optional[str] = Field(default=None, description="SAML metadata URL")
    
    # User mapping
    attribute_mapping: Dict[str, str] = Field(
        default_factory=lambda: {
            "email": "email",
            "first_name": "given_name",
            "last_name": "family_name",
            "display_name": "name"
        },
        description="Attribute mapping from provider to user fields"
    )
    
    # Auto-provisioning settings
    auto_provision_users: bool = Field(default=True, description="Automatically create users")
    default_role: UserRole = Field(default=UserRole.DEVELOPER, description="Default role for new users")
    allowed_domains: List[str] = Field(default_factory=list, description="Allowed email domains")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(extra="ignore")


class UserSession(BaseModel):
    """User session model"""
    id: UUID = Field(default_factory=uuid4, description="Session identifier")
    user_id: UUID = Field(description="Associated user")
    tenant_id: UUID = Field(description="Associated tenant")
    
    # Session details
    status: SessionStatus = Field(default=SessionStatus.ACTIVE, description="Session status")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Session creation")
    expires_at: datetime = Field(description="Session expiration")
    last_activity_at: datetime = Field(default_factory=datetime.utcnow, description="Last activity")
    
    # Security information
    ip_address: Optional[str] = Field(default=None, description="Client IP address")
    user_agent: Optional[str] = Field(default=None, description="Client user agent")
    location: Optional[Dict[str, str]] = Field(default=None, description="Geographic location")
    
    # Authentication method used for this session
    auth_method: AuthProvider = Field(description="Authentication method")
    mfa_verified: bool = Field(default=False, description="MFA verification status")
    
    # Token information
    access_token_hash: str = Field(description="Hashed access token")
    refresh_token_hash: Optional[str] = Field(default=None, description="Hashed refresh token")
    
    model_config = ConfigDict(extra="ignore")


class LoginRequest(BaseModel):
    """User login request"""
    email: str = Field(description="User email")
    password: Optional[str] = Field(default=None, description="Password for local auth")
    provider: AuthProvider = Field(default=AuthProvider.LOCAL, description="Auth provider")
    
    # SSO/OAuth fields
    auth_code: Optional[str] = Field(default=None, description="OAuth authorization code")
    state: Optional[str] = Field(default=None, description="OAuth state parameter")
    
    # SAML fields
    saml_response: Optional[str] = Field(default=None, description="SAML response")
    relay_state: Optional[str] = Field(default=None, description="SAML relay state")
    
    # MFA fields
    mfa_code: Optional[str] = Field(default=None, description="MFA verification code")
    mfa_method: Optional[MFAMethod] = Field(default=None, description="MFA method used")
    
    # Security fields
    remember_me: bool = Field(default=False, description="Extended session duration")
    ip_address: Optional[str] = Field(default=None, description="Client IP address")
    user_agent: Optional[str] = Field(default=None, description="Client user agent")
    
    model_config = ConfigDict(extra="ignore")


class LoginResponse(BaseModel):
    """Login response"""
    success: bool = Field(description="Login success status")
    
    # Success fields
    access_token: Optional[str] = Field(default=None, description="JWT access token")
    refresh_token: Optional[str] = Field(default=None, description="JWT refresh token")
    expires_in: Optional[int] = Field(default=None, description="Token expiry in seconds")
    user: Optional[User] = Field(default=None, description="User information")
    
    # MFA challenge fields
    mfa_required: bool = Field(default=False, description="MFA verification required")
    mfa_methods: List[MFAMethod] = Field(default_factory=list, description="Available MFA methods")
    mfa_challenge_id: Optional[str] = Field(default=None, description="MFA challenge identifier")
    
    # Error fields
    error: Optional[str] = Field(default=None, description="Error code")
    error_description: Optional[str] = Field(default=None, description="Error description")
    
    model_config = ConfigDict(extra="ignore")


class MFASetupRequest(BaseModel):
    """MFA setup request"""
    method: MFAMethod = Field(description="MFA method to set up")
    phone_number: Optional[str] = Field(default=None, description="Phone number for SMS")
    
    model_config = ConfigDict(extra="ignore")


class MFASetupResponse(BaseModel):
    """MFA setup response"""
    method: MFAMethod = Field(description="MFA method")
    secret: Optional[str] = Field(default=None, description="TOTP secret key")
    qr_code: Optional[str] = Field(default=None, description="QR code URL for TOTP")
    backup_codes: List[str] = Field(default_factory=list, description="Backup codes")
    
    model_config = ConfigDict(extra="ignore")


class PasswordPolicy(BaseModel):
    """Password policy configuration"""
    tenant_id: UUID = Field(description="Associated tenant")
    
    # Password requirements
    min_length: int = Field(default=8, ge=6, le=128, description="Minimum password length")
    require_uppercase: bool = Field(default=True, description="Require uppercase letters")
    require_lowercase: bool = Field(default=True, description="Require lowercase letters")
    require_digits: bool = Field(default=True, description="Require numeric digits")
    require_special: bool = Field(default=True, description="Require special characters")
    special_chars: str = Field(default="!@#$%^&*", description="Allowed special characters")
    
    # Security settings
    max_age_days: int = Field(default=90, ge=30, le=365, description="Password expiry in days")
    history_count: int = Field(default=5, ge=0, le=24, description="Password history to check")
    lockout_attempts: int = Field(default=5, ge=3, le=20, description="Failed attempts before lockout")
    lockout_duration_minutes: int = Field(default=30, ge=5, le=1440, description="Lockout duration")
    
    # Common password checks
    prevent_common_passwords: bool = Field(default=True, description="Block common passwords")
    prevent_personal_info: bool = Field(default=True, description="Block personal information in password")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(extra="ignore")


class AuditLog(BaseModel):
    """Authentication audit log entry"""
    id: UUID = Field(default_factory=uuid4, description="Log entry identifier")
    tenant_id: UUID = Field(description="Associated tenant")
    
    # Event details
    event_type: str = Field(description="Type of authentication event")
    event_description: str = Field(description="Human-readable event description")
    success: bool = Field(description="Event success status")
    
    # User context
    user_id: Optional[UUID] = Field(default=None, description="Associated user")
    user_email: Optional[str] = Field(default=None, description="User email")
    
    # Security context
    ip_address: Optional[str] = Field(default=None, description="Client IP address")
    user_agent: Optional[str] = Field(default=None, description="Client user agent")
    location: Optional[Dict[str, str]] = Field(default=None, description="Geographic location")
    
    # Additional metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Event metadata")
    
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    
    model_config = ConfigDict(extra="ignore")


# Default password policy for new tenants
DEFAULT_PASSWORD_POLICY = PasswordPolicy(
    tenant_id=UUID("00000000-0000-0000-0000-000000000000"),  # Placeholder
    min_length=12,
    require_uppercase=True,
    require_lowercase=True,
    require_digits=True,
    require_special=True,
    max_age_days=90,
    history_count=5,
    lockout_attempts=5,
    lockout_duration_minutes=30,
    prevent_common_passwords=True,
    prevent_personal_info=True
)