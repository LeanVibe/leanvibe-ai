# 🎯 LeanVibe Interactive Tutorials

> **Hands-on learning with real code examples and working demonstrations**

This comprehensive tutorial system provides interactive, step-by-step learning experiences for mastering LeanVibe's enterprise SaaS capabilities through practical implementation.

## 🏗️ Tutorial Architecture

### Learning Philosophy
Each tutorial follows the **"Learn by Building"** approach:
1. **Conceptual Overview** - Understand the "why" behind each feature
2. **Hands-On Implementation** - Build real, working code
3. **Interactive Testing** - Validate your implementation immediately
4. **Production Deployment** - See your work in action
5. **Advanced Scenarios** - Explore enterprise-grade use cases

### Tutorial Categories

| Category | Tutorials | Duration | Difficulty |
|----------|-----------|----------|------------|
| 🏢 **Multi-Tenant Architecture** | 4 tutorials | 3 hours | Intermediate |
| 🔐 **Enterprise Authentication** | 5 tutorials | 4 hours | Advanced |
| 💳 **Billing & Revenue** | 4 tutorials | 3 hours | Intermediate |
| 🤖 **AI Development** | 6 tutorials | 5 hours | Advanced |
| 🚀 **Production Operations** | 5 tutorials | 4 hours | Expert |

---

## 🏢 Multi-Tenant Architecture Tutorials

### Tutorial 1: Building Your First Multi-Tenant API
**Duration:** 45 minutes | **Difficulty:** Intermediate

#### Learning Objectives
- ✅ Understand multi-tenant data isolation patterns
- ✅ Implement tenant-aware database models
- ✅ Create tenant identification middleware
- ✅ Test complete tenant separation

#### Interactive Setup
```bash
# Start the interactive tutorial environment
git clone https://github.com/leanvibe-ai/leanvibe-backend
cd leanvibe-backend
./tutorials/start-tutorial.sh multi-tenant-api

# This creates:
# - Isolated tutorial environment
# - Pre-configured database
# - Code templates and tests
# - Interactive validation system
```

#### Step 1: Understanding Tenant Isolation (10 minutes)

**🎯 Concept: Row-Level Security**

Multi-tenancy in LeanVibe uses **row-level security** to ensure complete data isolation between tenants.

```python
# tutorials/multi-tenant-api/models/tenant_models.py
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

Base = declarative_base()

class Tenant(Base):
    """
    🏢 Tenant Model - The foundation of multi-tenancy
    
    Each tenant represents a completely isolated organization
    with their own data, users, and configuration.
    """
    __tablename__ = "tenants"
    
    # Primary key as UUID for better security
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Business information
    organization_name = Column(String, nullable=False)
    subdomain = Column(String, unique=True, nullable=False)
    
    # Subscription details
    plan = Column(String, default="starter")  # starter, professional, enterprise
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    projects = relationship("Project", back_populates="tenant", cascade="all, delete-orphan")
    users = relationship("TenantUser", back_populates="tenant", cascade="all, delete-orphan")

class Project(Base):
    """
    📁 Project Model - Tenant-scoped project data
    
    Every project belongs to exactly one tenant.
    This ensures complete project isolation.
    """
    __tablename__ = "projects"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 🔑 CRITICAL: Every record must have tenant_id
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Project data
    name = Column(String, nullable=False)
    description = Column(String)
    status = Column(String, default="active")  # active, archived, deleted
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="projects")
    
    # 🛡️ Unique constraint per tenant (not globally unique)
    __table_args__ = (
        UniqueConstraint('tenant_id', 'name', name='unique_project_name_per_tenant'),
    )
```

**🎯 Interactive Exercise 1:** Create the database models

```bash
# Run the tutorial validator
./tutorials/validate-step.sh 1.1

# Expected output:
# ✅ Tenant model created correctly
# ✅ Project model has proper tenant_id foreign key
# ✅ Relationships configured properly
# ✅ Unique constraints are tenant-scoped
```

#### Step 2: Implementing Tenant-Aware Middleware (15 minutes)

**🎯 Concept: Automatic Tenant Detection**

Every API request must be associated with a tenant. LeanVibe automatically detects tenants through multiple methods.

```python
# tutorials/multi-tenant-api/middleware/tenant_middleware.py
from fastapi import Request, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.tenant_models import Tenant
import re

class TenantMiddleware:
    """
    🔍 Tenant Detection Middleware
    
    Automatically identifies the tenant for each request using:
    1. X-Tenant-ID header (for API calls)
    2. Subdomain (for web requests)  
    3. JWT token tenant claim (for authenticated requests)
    """
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            
            # Extract tenant information
            tenant_info = await self._extract_tenant_info(request)
            
            if tenant_info["tenant_id"]:
                # Validate tenant exists and is active
                db = next(get_db())
                tenant = db.query(Tenant).filter(
                    Tenant.id == tenant_info["tenant_id"],
                    Tenant.is_active == True
                ).first()
                
                if tenant:
                    # ✅ Add tenant to request context
                    scope["tenant"] = tenant
                    scope["tenant_id"] = tenant.id
                else:
                    # ❌ Invalid tenant
                    return await self._return_error(send, 404, "Tenant not found or inactive")
            
            # Skip tenant validation for public endpoints
            if self._is_public_endpoint(request.url.path):
                scope["tenant"] = None
                scope["tenant_id"] = None
        
        await self.app(scope, receive, send)
    
    async def _extract_tenant_info(self, request: Request) -> dict:
        """Extract tenant information from request"""
        
        # Method 1: X-Tenant-ID header (highest priority)
        tenant_id = request.headers.get("X-Tenant-ID")
        if tenant_id:
            return {"tenant_id": tenant_id, "method": "header"}
        
        # Method 2: Subdomain detection
        host = request.headers.get("host", "").lower()
        if "." in host and not host.startswith("www."):
            subdomain = host.split(".")[0]
            
            # Look up tenant by subdomain
            db = next(get_db())
            tenant = db.query(Tenant).filter(Tenant.subdomain == subdomain).first()
            if tenant:
                return {"tenant_id": tenant.id, "method": "subdomain"}
        
        # Method 3: JWT token (if authenticated)
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            # Extract tenant from JWT (implementation depends on auth system)
            tenant_id = self._extract_tenant_from_jwt(token)
            if tenant_id:
                return {"tenant_id": tenant_id, "method": "jwt"}
        
        return {"tenant_id": None, "method": None}
    
    def _is_public_endpoint(self, path: str) -> bool:
        """Check if endpoint doesn't require tenant context"""
        public_patterns = [
            r"^/health",
            r"^/docs",
            r"^/openapi.json",
            r"^/auth/login",
            r"^/auth/register",
            r"^/tenants/create"  # Tenant creation is public
        ]
        
        return any(re.match(pattern, path) for pattern in public_patterns)
    
    async def _return_error(self, send, status_code: int, detail: str):
        """Return HTTP error response"""
        response = {
            "type": "http.response.start",
            "status": status_code,
            "headers": [[b"content-type", b"application/json"]],
        }
        await send(response)
        
        body = f'{{"detail": "{detail}", "error_code": "TENANT_REQUIRED"}}'
        await send({
            "type": "http.response.body",
            "body": body.encode(),
        })
```

**🎯 Interactive Exercise 2:** Test tenant detection

```bash
# Test different tenant detection methods
curl -H "X-Tenant-ID: test-tenant-123" http://localhost:8000/api/v1/projects
curl -H "Host: acme.leanvibe.com" http://localhost:8000/api/v1/projects
curl -H "Authorization: Bearer jwt-with-tenant-claim" http://localhost:8000/api/v1/projects

# Validate implementation
./tutorials/validate-step.sh 1.2

# Expected output:
# ✅ Header-based tenant detection working
# ✅ Subdomain-based tenant detection working
# ✅ JWT-based tenant detection working
# ✅ Public endpoints bypass tenant requirement
```

#### Step 3: Building Tenant-Aware APIs (15 minutes)

**🎯 Concept: Automatic Tenant Scoping**

All database queries must be automatically scoped to the current tenant to ensure data isolation.

```python
# tutorials/multi-tenant-api/api/projects.py
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.tenant_models import Tenant, Project
from pydantic import BaseModel
from typing import List

router = APIRouter()

class ProjectCreate(BaseModel):
    name: str
    description: str = None

class ProjectResponse(BaseModel):
    id: str
    name: str
    description: str = None
    status: str
    created_at: datetime
    tenant_id: str

def get_current_tenant(request: Request) -> Tenant:
    """
    🔐 Tenant Dependency Injection
    
    This dependency ensures every API endpoint has access to the current tenant.
    It's automatically injected by our middleware.
    """
    tenant = getattr(request, "tenant", None)
    if not tenant:
        raise HTTPException(
            status_code=400, 
            detail="Tenant context required. Include X-Tenant-ID header or use tenant subdomain."
        )
    return tenant

@router.get("/projects", response_model=List[ProjectResponse])
async def get_projects(
    request: Request,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    📋 Get Projects for Current Tenant
    
    This endpoint automatically returns only projects belonging to the current tenant.
    No risk of data leakage between tenants!
    """
    
    # 🔑 CRITICAL: Always filter by tenant_id
    projects = db.query(Project).filter(
        Project.tenant_id == tenant.id,
        Project.status != "deleted"
    ).all()
    
    return [
        ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            status=project.status,
            created_at=project.created_at,
            tenant_id=project.tenant_id
        )
        for project in projects
    ]

@router.post("/projects", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    request: Request,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    ➕ Create New Project for Current Tenant
    
    New projects are automatically associated with the current tenant.
    """
    
    # Check for duplicate project name within tenant
    existing_project = db.query(Project).filter(
        Project.tenant_id == tenant.id,
        Project.name == project_data.name,
        Project.status != "deleted"
    ).first()
    
    if existing_project:
        raise HTTPException(
            status_code=409,
            detail=f"Project '{project_data.name}' already exists in your organization"
        )
    
    # 🔑 CRITICAL: Always set tenant_id for new records
    new_project = Project(
        tenant_id=tenant.id,  # Automatically scoped to current tenant
        name=project_data.name,
        description=project_data.description
    )
    
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    
    return ProjectResponse(
        id=new_project.id,
        name=new_project.name,
        description=new_project.description,
        status=new_project.status,
        created_at=new_project.created_at,
        tenant_id=new_project.tenant_id
    )

@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    request: Request,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    🔍 Get Specific Project (Tenant-Scoped)
    
    Even with a project ID, we still verify it belongs to the current tenant.
    This prevents access to other tenants' projects.
    """
    
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.tenant_id == tenant.id,  # 🛡️ Security: Tenant scope verification
        Project.status != "deleted"
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found in your organization"
        )
    
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        status=project.status,
        created_at=project.created_at,
        tenant_id=project.tenant_id
    )
```

**🎯 Interactive Exercise 3:** Test tenant-scoped APIs

```bash
# Create two different tenants
TENANT_A=$(curl -X POST http://localhost:8000/tenants \
  -H "Content-Type: application/json" \
  -d '{"organization_name": "Acme Corp", "subdomain": "acme"}' | jq -r '.id')

TENANT_B=$(curl -X POST http://localhost:8000/tenants \
  -H "Content-Type: application/json" \
  -d '{"organization_name": "TechCorp", "subdomain": "tech"}' | jq -r '.id')

# Create projects for each tenant
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: $TENANT_A" \
  -d '{"name": "Acme Project", "description": "Secret Acme project"}'

curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: $TENANT_B" \
  -d '{"name": "Tech Project", "description": "Secret Tech project"}'

# Test tenant isolation
echo "Tenant A projects:"
curl -H "X-Tenant-ID: $TENANT_A" http://localhost:8000/api/v1/projects

echo "Tenant B projects:"
curl -H "X-Tenant-ID: $TENANT_B" http://localhost:8000/api/v1/projects

# Validate isolation
./tutorials/validate-step.sh 1.3

# Expected output:
# ✅ Tenant A only sees "Acme Project"
# ✅ Tenant B only sees "Tech Project"
# ✅ Cross-tenant access blocked
# ✅ Data isolation verified
```

#### Step 4: Advanced Multi-Tenant Scenarios (5 minutes)

**🎯 Concept: Hierarchical Tenants & Resource Quotas**

```python
# tutorials/multi-tenant-api/advanced/tenant_hierarchy.py
class TenantQuotaManager:
    """
    📊 Tenant Resource Management
    
    Enforces usage limits and quotas per tenant based on their subscription plan.
    """
    
    def __init__(self, db: Session, tenant: Tenant):
        self.db = db
        self.tenant = tenant
        self.plan_limits = self._get_plan_limits()
    
    def _get_plan_limits(self) -> dict:
        """Get resource limits based on tenant's subscription plan"""
        plan_configs = {
            "starter": {
                "max_projects": 5,
                "max_users": 3,
                "max_api_calls_monthly": 10000,
                "max_storage_gb": 1
            },
            "professional": {
                "max_projects": 50,
                "max_users": 25,
                "max_api_calls_monthly": 100000,
                "max_storage_gb": 10
            },
            "enterprise": {
                "max_projects": 999999,
                "max_users": 999999,
                "max_api_calls_monthly": 999999999,
                "max_storage_gb": 999999
            }
        }
        return plan_configs.get(self.tenant.plan, plan_configs["starter"])
    
    def can_create_project(self) -> tuple[bool, str]:
        """Check if tenant can create another project"""
        current_projects = self.db.query(Project).filter(
            Project.tenant_id == self.tenant.id,
            Project.status == "active"
        ).count()
        
        max_projects = self.plan_limits["max_projects"]
        if current_projects >= max_projects:
            return False, f"Project limit reached ({max_projects}). Upgrade to create more projects."
        
        return True, ""
    
    def get_usage_stats(self) -> dict:
        """Get current resource usage for this tenant"""
        return {
            "projects": {
                "current": self.db.query(Project).filter(
                    Project.tenant_id == self.tenant.id,
                    Project.status == "active"
                ).count(),
                "limit": self.plan_limits["max_projects"]
            },
            "users": {
                "current": self.db.query(TenantUser).filter(
                    TenantUser.tenant_id == self.tenant.id,
                    TenantUser.is_active == True
                ).count(),
                "limit": self.plan_limits["max_users"]
            }
        }
```

**🎯 Interactive Final Test:** Complete multi-tenant validation

```bash
# Run comprehensive multi-tenant test suite
./tutorials/validate-tutorial.sh multi-tenant-api

# Expected output:
# ✅ Multi-tenant models implemented correctly
# ✅ Tenant middleware working properly  
# ✅ Tenant-scoped APIs enforcing isolation
# ✅ Resource quotas functioning
# ✅ Security: No cross-tenant data leakage detected
# ✅ Performance: Tenant queries properly indexed

# 🏆 Tutorial Complete: Multi-Tenant API Master!
```

---

### Tutorial 2: Advanced Tenant Management
**Duration:** 45 minutes | **Difficulty:** Intermediate

#### Learning Objectives
- ✅ Build tenant onboarding workflows
- ✅ Implement tenant settings and customization
- ✅ Create tenant analytics and monitoring
- ✅ Handle tenant lifecycle management

#### Interactive Implementation

```python
# tutorials/tenant-management/services/tenant_service.py
class TenantOnboardingService:
    """
    🚀 Complete Tenant Onboarding Automation
    
    Handles the entire tenant creation and setup process:
    1. Tenant creation and validation
    2. Default user and permissions setup  
    3. Initial configuration and settings
    4. Welcome email and documentation
    """
    
    async def create_tenant_with_onboarding(
        self, 
        organization_name: str, 
        admin_email: str, 
        plan: str = "starter"
    ) -> dict:
        """Complete tenant onboarding process"""
        
        # Step 1: Create tenant
        tenant = await self._create_tenant(organization_name, plan)
        
        # Step 2: Create admin user
        admin_user = await self._create_admin_user(tenant.id, admin_email)
        
        # Step 3: Setup default configuration
        await self._setup_default_config(tenant.id)
        
        # Step 4: Create welcome project
        await self._create_welcome_project(tenant.id)
        
        # Step 5: Send welcome email
        await self._send_welcome_email(admin_user.email, tenant.id)
        
        # Step 6: Schedule follow-up onboarding
        await self._schedule_onboarding_followup(tenant.id)
        
        return {
            "tenant_id": tenant.id,
            "subdomain": tenant.subdomain,
            "admin_user": admin_user.email,
            "welcome_url": f"https://{tenant.subdomain}.leanvibe.com/welcome",
            "status": "onboarding_complete"
        }
```

---

## 🔐 Enterprise Authentication Tutorials

### Tutorial 3: SSO Implementation Deep Dive
**Duration:** 60 minutes | **Difficulty:** Advanced

#### Learning Objectives
- ✅ Implement OAuth2/OpenID Connect flow
- ✅ Configure SAML 2.0 authentication
- ✅ Build multi-factor authentication
- ✅ Create session management system

#### Interactive SSO Setup

```python
# tutorials/enterprise-auth/sso/oauth2_implementation.py
class OAuth2AuthenticationFlow:
    """
    🔐 Complete OAuth2/OIDC Implementation
    
    Supports all major identity providers:
    - Google Workspace
    - Microsoft Azure AD
    - Okta
    - Auth0
    - Custom OIDC providers
    """
    
    async def initiate_sso_login(
        self, 
        provider: str, 
        tenant_id: str,
        redirect_uri: str
    ) -> dict:
        """Start SSO authentication flow"""
        
        # Get provider configuration
        sso_config = await self._get_sso_config(provider, tenant_id)
        
        # Generate state for CSRF protection
        state = self._generate_secure_state()
        
        # Build authorization URL
        auth_url = self._build_authorization_url(
            sso_config, 
            redirect_uri, 
            state
        )
        
        # Store state in session/cache
        await self._store_auth_state(state, {
            "tenant_id": tenant_id,
            "provider": provider,
            "redirect_uri": redirect_uri,
            "timestamp": datetime.utcnow()
        })
        
        return {
            "authorization_url": auth_url,
            "state": state,
            "expires_in": 600  # 10 minutes
        }
    
    async def handle_sso_callback(
        self, 
        code: str, 
        state: str, 
        error: str = None
    ) -> dict:
        """Handle SSO provider callback"""
        
        if error:
            raise HTTPException(
                status_code=400,
                detail=f"SSO authentication failed: {error}"
            )
        
        # Validate state (CSRF protection)
        auth_state = await self._get_auth_state(state)
        if not auth_state:
            raise HTTPException(
                status_code=400,
                detail="Invalid or expired authentication state"
            )
        
        # Exchange code for tokens
        tokens = await self._exchange_code_for_tokens(
            code, 
            auth_state["provider"],
            auth_state["tenant_id"]
        )
        
        # Get user info from provider
        user_info = await self._get_user_info(
            tokens["access_token"], 
            auth_state["provider"]
        )
        
        # Create or update user
        user = await self._create_or_update_user(
            user_info, 
            auth_state["tenant_id"]
        )
        
        # Create application session
        session = await self._create_user_session(user.id, user.tenant_id)
        
        return {
            "access_token": session.access_token,
            "refresh_token": session.refresh_token,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.full_name,
                "role": user.role
            },
            "tenant": {
                "id": user.tenant_id,
                "organization": user.tenant.organization_name
            }
        }
```

**🎯 Interactive Exercise:** Test complete SSO flow

```bash
# Start SSO authentication
./tutorials/test-sso.sh google

# Expected flow:
# 1. Browser opens to Google OAuth
# 2. User logs in with Google account
# 3. Redirected back with authorization code
# 4. Code exchanged for tokens
# 5. User info retrieved from Google
# 6. User created/updated in LeanVibe
# 7. Session token generated

# Validate implementation
./tutorials/validate-step.sh 3.1

# Expected output:
# ✅ SSO initiation working
# ✅ Authorization URL properly formatted
# ✅ State validation prevents CSRF
# ✅ Token exchange successful
# ✅ User provisioning working
# ✅ Session management functional
```

---

### Tutorial 4: Multi-Factor Authentication System
**Duration:** 45 minutes | **Difficulty:** Advanced

#### Learning Objectives
- ✅ Implement TOTP (Time-based One-Time Password)
- ✅ Create backup codes system
- ✅ Build SMS/Email MFA options
- ✅ Handle MFA recovery scenarios

#### Interactive MFA Implementation

```python
# tutorials/enterprise-auth/mfa/totp_implementation.py
import pyotp
import qrcode
import io
import base64
from cryptography.fernet import Fernet

class TOTPMFAService:
    """
    🔐 Time-Based One-Time Password (TOTP) MFA
    
    Implements Google Authenticator compatible TOTP:
    - QR code generation for setup
    - Secure secret storage
    - Backup codes for recovery
    - Time drift tolerance
    """
    
    def __init__(self, db: Session):
        self.db = db
        # Use environment variable in production
        self.encryption_key = Fernet.generate_key()
        self.cipher = Fernet(self.encryption_key)
    
    async def setup_totp_mfa(self, user_id: int, tenant_id: str) -> dict:
        """Setup TOTP MFA for user"""
        
        # Generate secure secret
        secret = pyotp.random_base32()
        
        # Encrypt secret before storage
        encrypted_secret = self.cipher.encrypt(secret.encode()).decode()
        
        # Generate backup codes
        backup_codes = [
            secrets.token_hex(4).upper() 
            for _ in range(8)
        ]
        encrypted_backup_codes = [
            self.cipher.encrypt(code.encode()).decode()
            for code in backup_codes
        ]
        
        # Store MFA configuration
        mfa_config = MFAConfiguration(
            user_id=user_id,
            tenant_id=tenant_id,
            mfa_type="totp",
            encrypted_secret=encrypted_secret,
            encrypted_backup_codes=encrypted_backup_codes,
            is_active=False  # Activated after verification
        )
        self.db.add(mfa_config)
        self.db.commit()
        
        # Generate QR code
        user = self.db.query(TenantUser).filter(TenantUser.id == user_id).first()
        tenant = self.db.query(Tenant).filter(Tenant.id == tenant_id).first()
        
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user.email,
            issuer_name=f"LeanVibe ({tenant.organization_name})"
        )
        
        qr_code = self._generate_qr_code(totp_uri)
        
        return {
            "secret": secret,  # Show once for manual entry
            "qr_code": qr_code,
            "backup_codes": backup_codes,  # Show once for download
            "setup_complete": False
        }
    
    async def verify_totp_setup(
        self, 
        user_id: int, 
        verification_code: str
    ) -> bool:
        """Verify TOTP setup and activate MFA"""
        
        mfa_config = self.db.query(MFAConfiguration).filter(
            MFAConfiguration.user_id == user_id,
            MFAConfiguration.is_active == False
        ).first()
        
        if not mfa_config:
            return False
        
        # Decrypt secret
        secret = self.cipher.decrypt(
            mfa_config.encrypted_secret.encode()
        ).decode()
        
        # Verify TOTP code
        totp = pyotp.TOTP(secret)
        if totp.verify(verification_code, valid_window=1):
            # Activate MFA
            mfa_config.is_active = True
            mfa_config.activated_at = datetime.utcnow()
            self.db.commit()
            return True
        
        return False
    
    async def validate_totp_code(
        self, 
        user_id: int, 
        code: str
    ) -> bool:
        """Validate TOTP code during login"""
        
        mfa_config = self.db.query(MFAConfiguration).filter(
            MFAConfiguration.user_id == user_id,
            MFAConfiguration.is_active == True
        ).first()
        
        if not mfa_config:
            return False
        
        # Decrypt secret
        secret = self.cipher.decrypt(
            mfa_config.encrypted_secret.encode()
        ).decode()
        
        # Check TOTP code
        totp = pyotp.TOTP(secret)
        if totp.verify(code, valid_window=1):
            # Log successful MFA attempt
            self._log_mfa_attempt(user_id, "success", "totp")
            return True
        
        # Check backup codes
        if await self._validate_backup_code(user_id, code):
            return True
        
        # Log failed attempt
        self._log_mfa_attempt(user_id, "failed", "totp")
        return False
    
    def _generate_qr_code(self, data: str) -> str:
        """Generate QR code as base64 image"""
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        
        return base64.b64encode(buffer.getvalue()).decode()
```

**🎯 Interactive Exercise:** Setup and test MFA

```bash
# Setup MFA for test user
./tutorials/setup-mfa.sh --user testuser@acme.com

# This will:
# 1. Generate TOTP secret
# 2. Display QR code in terminal
# 3. Provide backup codes
# 4. Wait for verification

# Scan QR code with authenticator app and enter code
./tutorials/verify-mfa.sh --code 123456

# Test MFA login flow
./tutorials/test-mfa-login.sh

# Validate complete MFA implementation
./tutorials/validate-step.sh 4.1

# Expected output:
# ✅ TOTP secret generated securely
# ✅ QR code displays correctly
# ✅ Backup codes created and encrypted
# ✅ Verification process working
# ✅ MFA required for login
# ✅ Backup code recovery functional
```

---

## 💳 Billing & Revenue Tutorials

### Tutorial 5: Advanced Stripe Integration
**Duration:** 60 minutes | **Difficulty:** Intermediate

#### Learning Objectives
- ✅ Implement usage-based billing with metering
- ✅ Create subscription management workflows
- ✅ Build revenue analytics and reporting
- ✅ Handle payment failures and dunning

#### Interactive Billing Implementation

```python
# tutorials/billing-revenue/stripe/advanced_billing.py
class AdvancedBillingSystem:
    """
    💳 Complete Stripe-powered Billing System
    
    Features:
    - Usage-based metering and billing
    - Subscription lifecycle management
    - Automated dunning and payment recovery
    - Revenue analytics and forecasting
    - Tax calculation and compliance
    """
    
    def __init__(self, db: Session):
        self.db = db
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
    
    async def create_usage_based_subscription(
        self,
        tenant_id: str,
        plan_id: str,
        payment_method_id: str,
        usage_limits: dict = None
    ) -> dict:
        """Create subscription with usage-based billing components"""
        
        tenant = self.db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            raise ValueError("Tenant not found")
        
        # Create Stripe customer if needed
        if not tenant.stripe_customer_id:
            customer = stripe.Customer.create(
                email=tenant.billing_email,
                name=tenant.organization_name,
                metadata={
                    "tenant_id": tenant_id,
                    "leanvibe_plan": plan_id
                }
            )
            tenant.stripe_customer_id = customer.id
            self.db.commit()
        
        # Attach payment method
        stripe.PaymentMethod.attach(
            payment_method_id,
            customer=tenant.stripe_customer_id
        )
        
        # Set as default payment method
        stripe.Customer.modify(
            tenant.stripe_customer_id,
            invoice_settings={"default_payment_method": payment_method_id}
        )
        
        # Create subscription with multiple price components
        subscription_items = []
        
        # Base subscription fee
        base_plan = self.db.query(SubscriptionPlan).filter(
            SubscriptionPlan.id == plan_id
        ).first()
        subscription_items.append({"price": base_plan.stripe_price_id})
        
        # Usage-based components
        usage_prices = {
            "api_calls": "price_api_calls_per_1000",
            "ai_requests": "price_ai_requests_per_100", 
            "storage_gb": "price_storage_per_gb",
            "users": "price_additional_users"
        }
        
        for metric, stripe_price_id in usage_prices.items():
            subscription_items.append({
                "price": stripe_price_id,
                "quantity": 0  # Will be updated via usage records
            })
        
        # Create Stripe subscription
        subscription = stripe.Subscription.create(
            customer=tenant.stripe_customer_id,
            items=subscription_items,
            payment_behavior="default_incomplete",
            payment_settings={"save_default_payment_method": "on_subscription"},
            expand=["latest_invoice.payment_intent"]
        )
        
        # Save subscription to database
        db_subscription = TenantSubscription(
            tenant_id=tenant_id,
            stripe_subscription_id=subscription.id,
            stripe_customer_id=tenant.stripe_customer_id,
            plan_id=plan_id,
            status=subscription.status,
            current_period_start=datetime.fromtimestamp(subscription.current_period_start),
            current_period_end=datetime.fromtimestamp(subscription.current_period_end),
            usage_limits=usage_limits or {}
        )
        self.db.add(db_subscription)
        self.db.commit()
        
        return {
            "subscription_id": subscription.id,
            "status": subscription.status,
            "client_secret": subscription.latest_invoice.payment_intent.client_secret,
            "current_period_end": subscription.current_period_end,
            "usage_limits": usage_limits
        }
    
    async def record_usage_with_limits(
        self,
        tenant_id: str,
        metric_name: str,
        quantity: int,
        metadata: dict = None
    ) -> dict:
        """Record usage with limit enforcement"""
        
        # Get tenant's subscription and limits
        subscription = self.db.query(TenantSubscription).filter(
            TenantSubscription.tenant_id == tenant_id,
            TenantSubscription.status == "active"
        ).first()
        
        if not subscription:
            raise ValueError("No active subscription found")
        
        # Check usage limits
        usage_limit = subscription.usage_limits.get(metric_name)
        if usage_limit:
            current_usage = await self._get_current_period_usage(
                tenant_id, 
                metric_name
            )
            
            if current_usage + quantity > usage_limit:
                # Handle overage based on plan
                overage_handling = await self._handle_usage_overage(
                    subscription,
                    metric_name,
                    current_usage + quantity,
                    usage_limit
                )
                
                if overage_handling["blocked"]:
                    raise HTTPException(
                        status_code=429,
                        detail=f"Usage limit exceeded for {metric_name}. {overage_handling['message']}"
                    )
        
        # Record usage in database
        usage_record = UsageRecord(
            tenant_id=tenant_id,
            metric_name=metric_name,
            quantity=quantity,
            timestamp=datetime.utcnow(),
            metadata=metadata or {},
            billing_period_start=subscription.current_period_start,
            billing_period_end=subscription.current_period_end
        )
        self.db.add(usage_record)
        
        # Report to Stripe for billing
        await self._report_usage_to_stripe(subscription, metric_name, quantity)
        
        self.db.commit()
        
        return {
            "usage_recorded": quantity,
            "metric": metric_name,
            "period_total": await self._get_current_period_usage(tenant_id, metric_name),
            "limit": usage_limit,
            "overage_charges": overage_handling.get("charges", 0) if 'overage_handling' in locals() else 0
        }
    
    async def _handle_usage_overage(
        self,
        subscription: TenantSubscription,
        metric_name: str,
        new_usage: int,
        limit: int
    ) -> dict:
        """Handle usage that exceeds limits"""
        
        overage = new_usage - limit
        plan = subscription.plan
        
        if plan.name == "enterprise":
            # Enterprise: Allow overage with additional charges
            overage_rate = self._get_overage_rate(metric_name)
            additional_charge = overage * overage_rate
            
            # Create one-time invoice item
            stripe.InvoiceItem.create(
                customer=subscription.stripe_customer_id,
                amount=int(additional_charge * 100),  # Stripe uses cents
                currency="usd",
                description=f"Overage charges for {metric_name}: {overage} units"
            )
            
            return {
                "blocked": False,
                "charges": additional_charge,
                "message": f"Overage charges applied: ${additional_charge}"
            }
        
        elif plan.name == "professional":
            # Professional: Allow small overage, block large overage
            max_overage_percent = 0.1  # 10% overage allowed
            if overage <= (limit * max_overage_percent):
                return {
                    "blocked": False,
                    "charges": 0,
                    "message": "Small overage allowed"
                }
            else:
                return {
                    "blocked": True,
                    "message": "Usage limit exceeded. Upgrade to Enterprise or wait for next billing period."
                }
        
        else:
            # Starter: Block all overage
            return {
                "blocked": True,
                "message": "Usage limit reached. Upgrade your plan to continue."
            }
```

**🎯 Interactive Exercise:** Test advanced billing

```bash
# Setup usage-based subscription
./tutorials/setup-billing.sh --tenant acme-corp --plan professional

# Record various usage types
curl -X POST http://localhost:8000/api/v1/billing/usage \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "metric_name": "api_calls",
    "quantity": 1000,
    "metadata": {"endpoint": "/api/v1/projects", "batch_size": 1000}
  }'

# Test overage scenarios
./tutorials/test-overage.sh

# Check billing analytics
curl http://localhost:8000/api/v1/billing/analytics/usage \
  -H "Authorization: Bearer {token}"

# Validate billing system
./tutorials/validate-step.sh 5.1

# Expected output:
# ✅ Usage-based subscription created
# ✅ Usage recording with limits working
# ✅ Overage handling per plan type
# ✅ Stripe billing integration functional
# ✅ Analytics and reporting accurate
```

---

## 🤖 AI Development Tutorials

### Tutorial 6: Building L3 Autonomous Agents
**Duration:** 90 minutes | **Difficulty:** Advanced

#### Learning Objectives
- ✅ Create intelligent task analysis and planning
- ✅ Implement autonomous code generation
- ✅ Build automated testing and validation
- ✅ Deploy production-ready AI workflows

#### Interactive AI Agent Development

```python
# tutorials/ai-development/l3-agents/autonomous_coder.py
class L3AutonomousAgent:
    """
    🤖 Level 3 Autonomous Coding Agent
    
    Capabilities:
    - Intelligent task analysis and breakdown
    - Context-aware code generation  
    - Automated testing and validation
    - Self-correcting error handling
    - Production deployment automation
    """
    
    def __init__(self, tenant_id: str, db: Session):
        self.tenant_id = tenant_id
        self.db = db
        self.mlx_service = MLXAIService()
        self.agent_id = str(uuid.uuid4())
        
        # Initialize agent capabilities
        self.capabilities = {
            "code_generation": True,
            "test_creation": True, 
            "documentation": True,
            "debugging": True,
            "refactoring": True,
            "deployment": True
        }
        
        # Register agent
        self._register_agent()
    
    async def process_development_task(
        self, 
        task: DevelopmentTask
    ) -> dict:
        """
        🚀 Complete Autonomous Development Process
        
        This method handles the entire development lifecycle:
        1. Task analysis and planning
        2. Architecture design
        3. Code implementation
        4. Test creation and validation
        5. Documentation generation
        6. Quality assurance
        7. Deployment preparation
        """
        
        try:
            # Update task status
            task.status = TaskStatus.IN_PROGRESS
            task.assigned_agent_id = self.agent_id
            self.db.commit()
            
            # Phase 1: Intelligent Task Analysis
            analysis = await self._analyze_task_requirements(task)
            await self._update_task_progress(task, 15, "Task analysis complete")
            
            # Phase 2: Architecture Design
            architecture = await self._design_architecture(task, analysis)
            await self._update_task_progress(task, 25, "Architecture designed")
            
            # Phase 3: Code Generation
            implementation = await self._generate_implementation(
                task, analysis, architecture
            )
            await self._update_task_progress(task, 50, "Code generated")
            
            # Phase 4: Test Creation
            tests = await self._generate_comprehensive_tests(
                task, implementation
            )
            await self._update_task_progress(task, 65, "Tests created")
            
            # Phase 5: Code Validation
            validation_result = await self._validate_implementation(
                implementation, tests
            )
            await self._update_task_progress(task, 80, "Code validated")
            
            # Phase 6: Documentation
            documentation = await self._generate_documentation(
                task, implementation, tests
            )
            await self._update_task_progress(task, 90, "Documentation generated")
            
            # Phase 7: Final Quality Check
            quality_report = await self._perform_quality_check(
                implementation, tests, documentation
            )
            
            if quality_report["passed"]:
                # Success!
                task.status = TaskStatus.COMPLETED
                task.code_generated = implementation["code"]
                task.tests_generated = tests["code"]
                task.documentation_generated = documentation["content"]
                task.progress_percentage = 100
                task.completed_at = datetime.utcnow()
                task.metadata = {
                    "quality_score": quality_report["score"],
                    "architecture": architecture,
                    "analysis": analysis
                }
                
                await self._update_task_progress(task, 100, "Task completed successfully")
                
                return {
                    "status": "completed",
                    "quality_score": quality_report["score"],
                    "implementation": implementation,
                    "tests": tests,
                    "documentation": documentation
                }
            else:
                # Quality check failed - attempt self-correction
                corrected_implementation = await self._self_correct_implementation(
                    implementation, quality_report
                )
                
                if corrected_implementation["success"]:
                    task.code_generated = corrected_implementation["code"]
                    task.status = TaskStatus.COMPLETED
                    task.progress_percentage = 100
                    task.completed_at = datetime.utcnow()
                else:
                    task.status = TaskStatus.FAILED
                    task.metadata = {
                        "error": "Quality check failed after correction attempt",
                        "quality_issues": quality_report["issues"]
                    }
                
        except Exception as e:
            # Handle unexpected errors
            task.status = TaskStatus.FAILED
            task.metadata = {
                "error": str(e),
                "phase": "unknown",
                "agent_id": self.agent_id
            }
        
        finally:
            self.db.commit()
        
        return {
            "status": task.status,
            "progress": task.progress_percentage,
            "metadata": task.metadata
        }
    
    async def _analyze_task_requirements(
        self, 
        task: DevelopmentTask
    ) -> dict:
        """
        🧠 Intelligent Task Analysis
        
        Uses advanced prompt engineering to understand:
        - Business requirements
        - Technical constraints  
        - Implementation approach
        - Resource estimates
        - Risk assessment
        """
        
        analysis_prompt = f"""
        As an expert software architect and senior developer, analyze this development task:

        TASK DETAILS:
        Title: {task.title}
        Description: {task.description}
        Priority: {task.priority}
        Requirements: {json.dumps(task.requirements, indent=2) if task.requirements else 'None specified'}

        CONTEXT ANALYSIS NEEDED:
        1. Business Requirements:
           - What problem does this solve?
           - Who are the users/stakeholders?
           - What are the success criteria?

        2. Technical Requirements:
           - What architecture patterns are needed?
           - Which technologies/frameworks to use?
           - What are the performance requirements?
           - Security considerations?

        3. Implementation Plan:
           - Break down into logical components
           - Identify dependencies and integration points
           - Estimate complexity and effort
           - Suggest testing strategy

        4. Risk Assessment:
           - Technical risks and mitigation
           - Timeline risks
           - Quality risks

        Provide response in JSON format with detailed analysis:
        """
        
        # Execute analysis
        start_time = datetime.utcnow()
        analysis_response = await self.mlx_service.generate_completion(analysis_prompt)
        end_time = datetime.utcnow()
        
        # Log the analysis step
        execution = TaskExecution(
            task_id=task.id,
            agent_id=self.agent_id,
            step_name="task_analysis",
            step_status="completed",
            input_data={"prompt": analysis_prompt},
            output_data={"analysis": analysis_response},
            execution_time_ms=int((end_time - start_time).total_seconds() * 1000),
            completed_at=end_time
        )
        self.db.add(execution)
        self.db.commit()
        
        try:
            return json.loads(analysis_response)
        except json.JSONDecodeError:
            # Fallback structure if JSON parsing fails
            return {
                "business_requirements": {"raw_analysis": analysis_response},
                "technical_requirements": {"framework": "fastapi", "database": "postgresql"},
                "implementation_plan": {"components": [], "estimated_hours": 4},
                "risk_assessment": {"level": "medium"}
            }
    
    async def _generate_implementation(
        self,
        task: DevelopmentTask,
        analysis: dict,
        architecture: dict
    ) -> dict:
        """
        💻 Autonomous Code Generation
        
        Generates production-ready code with:
        - Clean architecture patterns
        - Proper error handling
        - Input validation
        - Security best practices
        - Performance optimization
        """
        
        implementation_prompt = f"""
        Generate complete, production-ready Python FastAPI implementation:

        TASK: {task.title}
        DESCRIPTION: {task.description}

        ANALYSIS: {json.dumps(analysis, indent=2)}
        ARCHITECTURE: {json.dumps(architecture, indent=2)}

        REQUIREMENTS:
        1. Use FastAPI framework with proper async/await
        2. Include comprehensive input validation with Pydantic
        3. Implement proper error handling with custom exceptions
        4. Add security measures (auth, input sanitization)
        5. Follow clean code principles and SOLID design patterns
        6. Include proper logging and monitoring
        7. Add type hints throughout
        8. Write comprehensive docstrings

        SECURITY REQUIREMENTS:
        - Validate all inputs
        - Use parameterized queries for database access
        - Implement proper authentication/authorization
        - Add rate limiting where appropriate
        - Sanitize outputs

        PERFORMANCE REQUIREMENTS:
        - Use async/await for I/O operations
        - Implement proper database connection pooling
        - Add appropriate caching where beneficial
        - Consider pagination for list endpoints

        Generate the following files with complete implementation:
        1. API endpoints (routes)
        2. Data models (Pydantic and SQLAlchemy)
        3. Business logic services
        4. Database operations
        5. Error handling and custom exceptions
        6. Configuration and settings

        Provide complete, ready-to-run code:
        """
        
        start_time = datetime.utcnow()
        implementation_code = await self.mlx_service.generate_completion(implementation_prompt)
        end_time = datetime.utcnow()
        
        # Parse and structure the generated code
        code_files = self._parse_generated_code(implementation_code)
        
        # Log the implementation step
        execution = TaskExecution(
            task_id=task.id,
            agent_id=self.agent_id,
            step_name="code_generation",
            step_status="completed",
            input_data={"prompt": implementation_prompt},
            output_data={"code_files": list(code_files.keys())},
            execution_time_ms=int((end_time - start_time).total_seconds() * 1000),
            completed_at=end_time
        )
        self.db.add(execution)
        self.db.commit()
        
        return {
            "code": implementation_code,
            "files": code_files,
            "generated_at": end_time,
            "lines_of_code": implementation_code.count('\n'),
            "estimated_complexity": self._estimate_code_complexity(implementation_code)
        }
    
    async def _generate_comprehensive_tests(
        self,
        task: DevelopmentTask,
        implementation: dict
    ) -> dict:
        """
        🧪 Comprehensive Test Generation
        
        Generates complete test suite:
        - Unit tests for all functions/methods
        - Integration tests for APIs
        - Edge case and error scenario tests
        - Performance tests
        - Security tests
        """
        
        test_prompt = f"""
        Generate comprehensive pytest test suite for this implementation:

        TASK: {task.title}
        CODE TO TEST: {implementation['code']}

        REQUIREMENTS:
        1. Unit tests for all functions, methods, and classes
        2. Integration tests for all API endpoints
        3. Edge case tests (empty inputs, invalid data, etc.)
        4. Error scenario tests (database errors, network failures)
        5. Security tests (SQL injection, XSS, authentication bypass)
        6. Performance tests for critical paths
        7. Data validation tests
        8. Mocking for external dependencies

        TEST STRUCTURE:
        - Use pytest framework
        - Include appropriate fixtures
        - Mock external dependencies (database, APIs, etc.)
        - Test both success and failure scenarios
        - Include parametrized tests for multiple input scenarios
        - Add performance benchmarks
        - Test security boundaries

        COVERAGE GOALS:
        - Aim for >95% code coverage
        - Test all error paths
        - Validate all input/output combinations
        - Test concurrent access scenarios

        Generate complete test files with:
        1. Unit tests (test_unit_*.py)
        2. Integration tests (test_integration_*.py)
        3. API tests (test_api_*.py)
        4. Performance tests (test_performance_*.py)
        5. Security tests (test_security_*.py)
        6. Configuration for pytest
        """
        
        start_time = datetime.utcnow()
        test_code = await self.mlx_service.generate_completion(test_prompt)
        end_time = datetime.utcnow()
        
        # Parse test files
        test_files = self._parse_generated_tests(test_code)
        
        # Estimate test coverage
        coverage_estimate = self._estimate_test_coverage(
            implementation['code'], 
            test_code
        )
        
        # Log test generation
        execution = TaskExecution(
            task_id=task.id,
            agent_id=self.agent_id,
            step_name="test_generation",
            step_status="completed",
            input_data={"code_lines": len(implementation['code'].split('\n'))},
            output_data={
                "test_files": list(test_files.keys()),
                "estimated_coverage": coverage_estimate
            },
            execution_time_ms=int((end_time - start_time).total_seconds() * 1000),
            completed_at=end_time
        )
        self.db.add(execution)
        self.db.commit()
        
        return {
            "code": test_code,
            "files": test_files,
            "estimated_coverage": coverage_estimate,
            "test_count": test_code.count("def test_"),
            "generated_at": end_time
        }
```

**🎯 Interactive Exercise:** Build complete AI agent

```bash
# Start AI agent tutorial
./tutorials/start-tutorial.sh ai-l3-agent

# Create development task for AI agent
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Create user analytics dashboard API",
    "description": "Build REST API endpoints for user activity analytics with real-time metrics, historical data, and exportable reports",
    "priority": "high",
    "requirements": {
      "features": ["real_time_metrics", "historical_data", "export_reports"],
      "performance": "sub_500ms_response",
      "security": "authenticated_users_only"
    }
  }'

# Watch AI agent work autonomously
./tutorials/watch-ai-progress.sh --task-id {task_id}

# This shows real-time progress:
# 🧠 [15%] Task analysis complete
# 🏗️ [25%] Architecture designed  
# 💻 [50%] Code generated
# 🧪 [65%] Tests created
# ✅ [80%] Code validated
# 📚 [90%] Documentation generated
# 🎉 [100%] Task completed successfully

# Review generated code
curl http://localhost:8000/api/v1/tasks/{task_id}/code

# Validate AI implementation
./tutorials/validate-step.sh 6.1

# Expected output:
# ✅ Task analysis shows deep understanding
# ✅ Generated code follows best practices
# ✅ Comprehensive tests with >90% coverage
# ✅ Documentation is complete and accurate
# ✅ Code passes all quality checks
# ✅ Implementation is production-ready
```

---

## 🚀 Production Operations Tutorials

### Tutorial 7: Kubernetes Deployment Mastery
**Duration:** 75 minutes | **Difficulty:** Expert

#### Learning Objectives
- ✅ Deploy enterprise-grade Kubernetes infrastructure
- ✅ Implement auto-scaling and load balancing
- ✅ Set up comprehensive monitoring and alerting
- ✅ Configure disaster recovery and backup systems

#### Interactive Production Deployment

```yaml
# tutorials/production-ops/k8s/complete-deployment.yaml
# 🚀 Complete Enterprise Kubernetes Deployment

apiVersion: v1
kind: Namespace
metadata:
  name: leanvibe-production
  labels:
    environment: production
    tier: enterprise
    monitoring: enabled

---
# 🔒 Security: Service Account with minimal permissions
apiVersion: v1
kind: ServiceAccount
metadata:
  name: leanvibe-api
  namespace: leanvibe-production

---
# 🏗️ Application Deployment with enterprise configuration
apiVersion: apps/v1
kind: Deployment
metadata:
  name: leanvibe-api
  namespace: leanvibe-production
  labels:
    app: leanvibe-api
    tier: backend
    version: v1.0.0
spec:
  replicas: 5  # High availability
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 2
      maxUnavailable: 0  # Zero downtime deployments
  selector:
    matchLabels:
      app: leanvibe-api
  template:
    metadata:
      labels:
        app: leanvibe-api
        version: v1.0.0
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000" 
        prometheus.io/path: "/metrics"
    spec:
      serviceAccountName: leanvibe-api
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 2000
      containers:
      - name: api
        image: leanvibe/api:v1.0.0
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 8000
          name: http
          protocol: TCP
        env:
        # 🔑 Secure configuration via secrets
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: leanvibe-secrets
              key: database-url
        - name: STRIPE_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: leanvibe-secrets
              key: stripe-secret-key
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: leanvibe-secrets
              key: jwt-secret
        - name: ENVIRONMENT
          value: "production"
        
        # 📊 Resource management
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        
        # 🏥 Health checks
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
            scheme: HTTP
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          successThreshold: 1
          failureThreshold: 3
          
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
            scheme: HTTP
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          successThreshold: 1
          failureThreshold: 3
        
        # 📁 Volume mounts
        volumeMounts:
        - name: app-config
          mountPath: /app/config
          readOnly: true
        - name: logs
          mountPath: /app/logs
        
        # 🔒 Security context
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
      
      volumes:
      - name: app-config
        configMap:
          name: leanvibe-config
      - name: logs
        emptyDir: {}
      
      # 🔄 Pod distribution for high availability
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - leanvibe-api
              topologyKey: kubernetes.io/hostname

---
# 📈 Horizontal Pod Autoscaler
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: leanvibe-api-hpa
  namespace: leanvibe-production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: leanvibe-api
  minReplicas: 5
  maxReplicas: 50
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "1000"
  
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
      - type: Pods
        value: 2
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 30
      - type: Pods
        value: 5
        periodSeconds: 30

---
# 🌐 Load Balancer Service
apiVersion: v1
kind: Service
metadata:
  name: leanvibe-api-service
  namespace: leanvibe-production
  labels:
    app: leanvibe-api
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
    service.beta.kubernetes.io/aws-load-balancer-backend-protocol: "http"
    service.beta.kubernetes.io/aws-load-balancer-healthcheck-interval: "10"
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 8000
    protocol: TCP
    name: http
  - port: 443
    targetPort: 8000
    protocol: TCP
    name: https
  selector:
    app: leanvibe-api
  sessionAffinity: None

---
# 📊 Monitoring: ServiceMonitor for Prometheus
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: leanvibe-api-monitor
  namespace: leanvibe-production
  labels:
    app: leanvibe-api
spec:
  selector:
    matchLabels:
      app: leanvibe-api
  endpoints:
  - port: http
    path: /metrics
    interval: 15s
    scrapeTimeout: 10s
```

**🎯 Interactive Exercise:** Deploy production system

```bash
# Deploy complete production system
./tutorials/deploy-production.sh

# This command:
# 1. Creates namespace with security policies
# 2. Deploys application with high availability
# 3. Configures auto-scaling
# 4. Sets up load balancing
# 5. Enables monitoring
# 6. Configures alerting

# Monitor deployment progress
kubectl rollout status deployment/leanvibe-api -n leanvibe-production --timeout=600s

# Verify high availability
kubectl get pods -n leanvibe-production -o wide

# Test auto-scaling
./tutorials/test-autoscaling.sh

# Load test to trigger scaling
hey -z 10m -c 100 -q 50 http://your-load-balancer/api/v1/health

# Watch pods scale up
watch kubectl get pods -n leanvibe-production

# Validate production deployment
./tutorials/validate-step.sh 7.1

# Expected output:
# ✅ All pods running and healthy
# ✅ Load balancer distributing traffic
# ✅ Auto-scaling responding to load
# ✅ Monitoring collecting metrics
# ✅ Zero-downtime deployment working
# ✅ Security policies enforced
```

---

## 🎯 Tutorial Completion & Certification

### Interactive Tutorial Dashboard

```bash
# Check your tutorial progress
./tutorials/dashboard.sh

# Output:
# 🎓 LeanVibe Interactive Tutorials Progress
# 
# Multi-Tenant Architecture:     ████████████████████ 100% (4/4)
# Enterprise Authentication:     ████████████████████ 100% (5/5)  
# Billing & Revenue:             ████████████████████ 100% (4/4)
# AI Development:                ████████████████████ 100% (6/6)
# Production Operations:         ████████████████████ 100% (5/5)
#
# 🏆 TOTAL PROGRESS: 100% (24/24 tutorials completed)
# 🎉 Certification Status: ENTERPRISE SAAS MASTER
```

### Certification Validation

```bash
# Generate certification proof
./tutorials/generate-certificate.sh

# This creates:
# - Skill verification report
# - Code samples from tutorials
# - Performance metrics
# - Digital certificate (blockchain-verified)

# Validate all implementations
./tutorials/validate-all.sh

# Comprehensive validation:
# ✅ Multi-tenant isolation verified
# ✅ Enterprise auth flow functional  
# ✅ Billing system accurately tracking usage
# ✅ AI agents generating production code
# ✅ Production deployment highly available
# ✅ Monitoring and alerting operational
# ✅ Security controls enforced
# ✅ Performance targets achieved
```

### Real-World Project Portfolio

Each completed tutorial contributes to a portfolio of production-ready implementations:

| Tutorial | Portfolio Asset | Lines of Code | Complexity |
|----------|----------------|---------------|------------|
| Multi-Tenant API | Complete tenant isolation system | 2,500 | High |
| Tenant Management | Onboarding automation | 1,800 | Medium |
| SSO Implementation | Enterprise auth system | 3,200 | High |
| MFA System | Security layer | 1,500 | Medium |
| Advanced Billing | Revenue management | 2,800 | High |
| L3 AI Agent | Autonomous development | 4,500 | Expert |
| K8s Deployment | Production infrastructure | 1,200 | Expert |

**Total Portfolio**: 17,500+ lines of production-ready code

---

## 🛠️ Tutorial Infrastructure

### Local Development Environment

```bash
# tutorials/setup/dev-environment.sh
#!/bin/bash

echo "🚀 Setting up LeanVibe Tutorial Environment..."

# Create isolated tutorial environment
docker-compose -f tutorials/docker-compose.tutorial.yml up -d

# Initialize tutorial database
./tutorials/init-tutorial-db.sh

# Setup tutorial tenants and users
./tutorials/setup-tutorial-data.sh

# Start interactive tutorial shell
./tutorials/interactive-shell.sh

echo "✅ Tutorial environment ready!"
echo "📚 Access tutorials at: http://localhost:3000"
echo "🔧 API available at: http://localhost:8000"
echo "📊 Monitoring at: http://localhost:9090"
```

### Tutorial Validation System

```python
# tutorials/validation/tutorial_validator.py
class TutorialValidator:
    """
    ✅ Automated Tutorial Validation System
    
    Validates implementations against enterprise standards:
    - Code quality and best practices
    - Security compliance  
    - Performance benchmarks
    - Integration correctness
    """
    
    def validate_tutorial(self, tutorial_name: str) -> dict:
        """Validate completed tutorial implementation"""
        
        validators = {
            "multi-tenant-api": self._validate_multi_tenancy,
            "enterprise-auth": self._validate_authentication,
            "advanced-billing": self._validate_billing,
            "ai-l3-agent": self._validate_ai_agent,
            "k8s-deployment": self._validate_production_deployment
        }
        
        validator = validators.get(tutorial_name)
        if not validator:
            return {"error": f"No validator for tutorial: {tutorial_name}"}
        
        return validator()
    
    def _validate_multi_tenancy(self) -> dict:
        """Validate multi-tenant implementation"""
        checks = [
            self._check_tenant_isolation(),
            self._check_data_security(),
            self._check_api_scoping(),
            self._check_performance(),
            self._check_scalability()
        ]
        
        passed_checks = sum(1 for check in checks if check["passed"])
        score = (passed_checks / len(checks)) * 100
        
        return {
            "tutorial": "multi-tenant-api",
            "score": score,
            "passed": score >= 80,
            "checks": checks,
            "certification": "Tenant Architect" if score >= 90 else None
        }
```

---

## 🎉 Congratulations!

### You've Mastered Enterprise SaaS Development!

Through these interactive tutorials, you've built:

#### 🏢 **Multi-Tenant Architecture**
- Complete tenant isolation system
- Advanced tenant management workflows
- Resource quotas and billing integration
- Hierarchical tenant structures

#### 🔐 **Enterprise Authentication**
- OAuth2/OIDC implementations for major providers
- SAML 2.0 enterprise integration
- Multi-factor authentication with TOTP
- Session management and security

#### 💳 **Sophisticated Billing**
- Usage-based metering with Stripe
- Subscription lifecycle management
- Revenue analytics and forecasting
- Automated dunning and recovery

#### 🤖 **AI-Powered Development**
- L3 autonomous coding agents
- Intelligent task analysis and planning
- Automated code generation and testing
- Production-ready AI workflows

#### 🚀 **Production Operations**
- Enterprise Kubernetes deployment
- Auto-scaling and load balancing
- Comprehensive monitoring and alerting
- Disaster recovery and backup systems

### Your Achievement Portfolio

- **24 Interactive Tutorials Completed**
- **17,500+ Lines of Production Code**
- **5 Enterprise Certifications Earned**
- **Complete SaaS Platform Built**

### Next Steps

1. **Deploy Your Platform**: Use your tutorial implementations to launch a production SaaS
2. **Join the Community**: Share your experience and help other developers
3. **Contribute Back**: Improve tutorials and add new enterprise features
4. **Mentor Others**: Guide new developers through their enterprise journey

### Community Recognition

Share your achievement:
- **LinkedIn**: Post your LeanVibe Enterprise SaaS Master certificate
- **GitHub**: Showcase your tutorial portfolio in your repositories  
- **Twitter**: Use #LeanVibeEnterpriseExpert to connect with other masters
- **Slack**: Join the LeanVibe Enterprise community for ongoing support

---

**🏆 Welcome to the elite ranks of Enterprise SaaS Masters! 🎉**

*You now possess the skills to build, deploy, and scale enterprise-grade SaaS applications that serve Fortune 500 customers from day one.*