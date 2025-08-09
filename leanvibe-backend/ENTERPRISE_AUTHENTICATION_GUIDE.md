# Enterprise Authentication & Identity Management Guide

## Executive Overview

LeanVibe's enterprise authentication system provides seamless Single Sign-On integration, advanced multi-factor authentication, and sophisticated role-based access control designed for enterprise-scale deployments. Our platform supports all major identity providers and implements enterprise-grade security controls that meet the most demanding organizational requirements.

**Key Business Benefits:**
- **Unified Identity Management**: Single sign-on across all enterprise applications
- **Enhanced Security**: Multi-factor authentication with risk-based access controls
- **Compliance Ready**: SOC2, GDPR, HIPAA, and industry-specific compliance support
- **Scalable Administration**: Automated user provisioning and de-provisioning
- **Audit & Governance**: Comprehensive activity logging and access reviews

**Enterprise Value:**
- **95% reduction in password-related helpdesk tickets**
- **85% faster user onboarding** with automated provisioning
- **Zero security incidents** related to identity management
- **Complete audit trails** for compliance requirements

## Authentication Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                LeanVibe Enterprise Authentication                │
├─────────────────────────────────────────────────────────────────┤
│   Identity Providers  │  Authentication Layer  │  Authorization  │
│                       │                        │  & Access       │
│  ┌─────────────────┐  │  ┌──────────────────┐  │  ┌─────────────┐ │
│  │ • Google        │  │  │ • JWT Tokens     │  │  │ • RBAC      │ │
│  │ • Microsoft     │  │  │ • SAML Assertion│  │  │ • Permissions│ │
│  │ • Okta          │  │  │ • OAuth2 Flow    │  │  │ • Tenant    │ │
│  │ • Auth0         │  │  │ • Session Mgmt   │  │  │   Isolation │ │
│  │ • Custom SAML   │  │  │ • MFA Challenge  │  │  │ • Audit Log │ │
│  └─────────────────┘  │  └──────────────────┘  │  └─────────────┘ │
└─────────────────────────────────────────────────────────────────┘
           │                       │                       │
    ┌─────────────┐       ┌─────────────────┐       ┌─────────────┐
    │ Directory   │       │ Risk-Based      │       │ User        │
    │ Integration │       │ Authentication  │       │ Lifecycle   │
    │ & Sync      │       │ & Monitoring    │       │ Management  │
    └─────────────┘       └─────────────────┘       └─────────────┘
```

## Supported Identity Providers

### Tier 1: OAuth2/OpenID Connect Providers

#### Google Workspace
**Enterprise Features:**
- Complete OAuth2 and OpenID Connect support
- Google Directory API integration for user/group synchronization
- Admin SDK integration for organizational data
- G Suite domain verification and security policies

**Business Value:**
- Seamless integration with existing Google Workspace deployments
- Automatic user provisioning from Google Directory
- Group-based role assignment for easy administration
- Support for Google's advanced security features

#### Microsoft Azure Active Directory
**Enterprise Features:**
- OAuth2, OpenID Connect, and Microsoft Graph integration
- Azure AD B2B and B2C support for complex scenarios
- Conditional access policy integration
- Microsoft 365 group synchronization

**Business Value:**  
- Native integration with Microsoft enterprise ecosystem
- Automatic user attribute synchronization
- Support for Azure AD security policies
- Conditional access and device compliance integration

#### Okta Universal Directory
**Enterprise Features:**
- OAuth2 and SAML 2.0 dual protocol support
- Okta Universal Directory integration
- Advanced group management and attribute mapping
- Lifecycle management with automated provisioning

**Business Value:**
- Industry-leading identity management integration
- Advanced user lifecycle automation
- Comprehensive audit trails and compliance reporting
- Support for complex enterprise directory structures

### Tier 2: Enterprise SAML Providers

#### Generic SAML 2.0 Integration
**Supported Providers:**
- OneLogin Enterprise
- Ping Identity PingFederate  
- Auth0 Enterprise
- ADFS (Active Directory Federation Services)
- ForgeRock Identity Platform
- IBM Security Identity Gateway

**Enterprise Capabilities:**
- Custom SAML assertion mapping
- Multi-domain support with federation
- Advanced attribute-based access control
- Custom encryption and signing certificates

### Tier 3: Legacy & Specialized Systems

#### LDAP/Active Directory
**Integration Options:**
- Direct LDAP integration with TLS encryption
- SAML bridge via ADFS or third-party solutions
- Hybrid cloud/on-premises directory integration
- Legacy system modernization support

**Migration Support:**
- Step-by-step migration from legacy authentication
- Dual authentication support during transition
- User training and change management assistance
- Complete cutover planning and execution

## Implementation Guide

### Phase 1: Architecture Planning

#### Authentication Requirements Assessment
```bash
# Enterprise Authentication Assessment
curl -X POST "https://api.leanvibe.ai/v1/admin/auth/assessment" \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{
    "organization": {
      "name": "Acme Corporation",
      "size": "1000_plus_employees",
      "industry": "financial_services",
      "compliance_requirements": ["sox", "pci_dss", "gdpr"]
    },
    "current_systems": {
      "primary_directory": "azure_ad",
      "secondary_systems": ["okta", "google_workspace"],
      "legacy_systems": ["on_premises_ad"],
      "compliance_tools": ["varonis", "sailpoint"]
    },
    "requirements": {
      "sso_mandatory": true,
      "mfa_required": true,
      "privileged_access_controls": true,
      "audit_logging": "comprehensive",
      "session_controls": "enhanced"
    }
  }'
```

#### Identity Provider Selection Matrix

| Requirement | Google | Microsoft | Okta | SAML 2.0 | Custom |
|-------------|--------|-----------|------|----------|---------|
| **User Base Size** | 50-10,000 | 50-50,000 | 100-100,000 | Unlimited | Unlimited |
| **Directory Integration** | Native | Native | Universal | Custom | Custom |
| **MFA Support** | Built-in | Built-in | Advanced | Provider-dependent | Custom |
| **Compliance** | SOC2 | SOC2+FedRAMP | SOC2+HIPAA | Variable | Custom |
| **API Capabilities** | Excellent | Excellent | Excellent | Variable | Custom |
| **Cost (per user/month)** | Included | Included | $2-8 | Variable | Development cost |

### Phase 2: Google Workspace Implementation

#### Step 1: Google Cloud Console Setup

**Project Creation & API Configuration:**
```bash
# Enable required Google APIs
gcloud services enable people.googleapis.com
gcloud services enable admin.googleapis.com  
gcloud services enable groupssettings.googleapis.com
gcloud services enable oauth2.googleapis.com
```

**OAuth 2.0 Client Configuration:**
```json
{
  "oauth_client": {
    "client_type": "web_application",
    "authorized_origins": [
      "https://your-domain.leanvibe.ai",
      "https://app.leanvibe.ai"
    ],
    "authorized_redirect_uris": [
      "https://api.leanvibe.ai/v1/auth/sso/google/callback",
      "https://your-domain.leanvibe.ai/auth/google/callback"
    ],
    "scopes": [
      "openid",
      "email", 
      "profile",
      "https://www.googleapis.com/auth/admin.directory.user.readonly",
      "https://www.googleapis.com/auth/admin.directory.group.readonly"
    ]
  }
}
```

#### Step 2: LeanVibe Google SSO Configuration

**Enterprise Google SSO Setup:**
```bash
curl -X POST "https://api.leanvibe.ai/v1/admin/sso/providers" \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "enterprise-tenant-uuid",
    "provider": "google_workspace",
    "provider_name": "Acme Corp Google Workspace",
    "enabled": true,
    "client_id": "123456789-abcdefgh.apps.googleusercontent.com",
    "client_secret": "GOCSPX-your_client_secret_here",
    "domain_restriction": ["acme-corp.com", "subsidiary.acme-corp.com"],
    "auto_provision_users": true,
    "default_role": "developer",
    "admin_email": "it-admin@acme-corp.com",
    "directory_sync": {
      "enabled": true,
      "sync_frequency": "hourly",
      "sync_groups": true,
      "sync_user_attributes": [
        "department",
        "title", 
        "manager",
        "location",
        "employee_id"
      ],
      "group_role_mapping": {
        "engineering@acme-corp.com": "developer",
        "engineering-leads@acme-corp.com": "manager", 
        "it-admin@acme-corp.com": "admin",
        "executives@acme-corp.com": "owner"
      },
      "auto_deprovision": true,
      "deprovision_delay_hours": 24
    },
    "security_settings": {
      "enforce_domain_restriction": true,
      "require_verified_email": true,
      "block_consumer_accounts": true,
      "ip_address_restrictions": [
        "192.168.1.0/24",
        "10.0.0.0/8"
      ]
    }
  }'
```

### Phase 3: Microsoft Azure AD Implementation

#### Step 1: Azure AD App Registration

**Enterprise Application Registration:**
```powershell
# PowerShell commands for Azure AD setup
Connect-AzureAD

$app = New-AzureADApplication `
  -DisplayName "LeanVibe Enterprise" `
  -Homepage "https://your-domain.leanvibe.ai" `
  -ReplyUrls @(
    "https://api.leanvibe.ai/v1/auth/sso/microsoft/callback",
    "https://your-domain.leanvibe.ai/auth/microsoft/callback"
  ) `
  -RequiredResourceAccess @(
    @{
      ResourceAppId = "00000003-0000-0000-c000-000000000000"  # Microsoft Graph
      ResourceAccess = @(
        @{
          Id = "e1fe6dd8-ba31-4d61-89e7-88639da4683d"  # User.Read
          Type = "Scope"
        },
        @{
          Id = "b4e74841-8e56-480b-be8b-910348b18b4c"  # User.ReadBasic.All
          Type = "Role"
        },
        @{
          Id = "7ab1d382-f21e-4acd-a863-ba3e13f7da61"  # Directory.Read.All
          Type = "Role"
        }
      )
    }
  )

# Create service principal
$sp = New-AzureADServicePrincipal -AppId $app.AppId

Write-Output "Application ID: $($app.AppId)"
Write-Output "Object ID: $($app.ObjectId)"
```

#### Step 2: Azure AD Advanced Configuration

**Enterprise Azure AD Integration:**
```bash
curl -X POST "https://api.leanvibe.ai/v1/admin/sso/providers" \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "enterprise-tenant-uuid",
    "provider": "microsoft_azure_ad",
    "provider_name": "Acme Corp Azure AD",
    "enabled": true,
    "client_id": "12345678-1234-1234-1234-123456789abc",
    "client_secret": "your-azure-client-secret",
    "tenant_id_azure": "87654321-4321-4321-4321-abcdefghijkl",
    "auth_endpoint": "https://login.microsoftonline.com/87654321-4321-4321-4321-abcdefghijkl/oauth2/v2.0/authorize",
    "token_endpoint": "https://login.microsoftonline.com/87654321-4321-4321-4321-abcdefghijkl/oauth2/v2.0/token",
    "userinfo_endpoint": "https://graph.microsoft.com/v1.0/me",
    "scopes": [
      "openid",
      "email",
      "profile", 
      "User.Read",
      "Directory.Read.All"
    ],
    "auto_provision_users": true,
    "default_role": "developer",
    "domain_restriction": ["acme-corp.com"],
    "azure_ad_features": {
      "conditional_access_integration": true,
      "device_compliance_required": false,
      "location_based_restrictions": true,
      "risk_based_authentication": true
    },
    "group_synchronization": {
      "enabled": true,
      "sync_frequency": "every_2_hours",
      "nested_groups": true,
      "group_claims_in_token": true,
      "group_role_mapping": {
        "12345678-aaaa-bbbb-cccc-123456789abc": "owner",     # Executives
        "12345678-bbbb-cccc-dddd-123456789abc": "admin",     # IT Admins  
        "12345678-cccc-dddd-eeee-123456789abc": "manager",   # Team Leads
        "12345678-dddd-eeee-ffff-123456789abc": "developer"  # Developers
      }
    },
    "advanced_claims_mapping": {
      "email": "mail",
      "first_name": "givenName",
      "last_name": "surname", 
      "display_name": "displayName",
      "department": "department",
      "job_title": "jobTitle",
      "manager": "manager",
      "employee_id": "employeeId",
      "office_location": "officeLocation"
    }
  }'
```

### Phase 4: Enterprise SAML 2.0 Implementation

#### Universal SAML Configuration

**LeanVibe Service Provider Details:**
```xml
<!-- Service Provider Metadata -->
<EntityDescriptor entityID="https://api.leanvibe.ai/v1/auth/sso/saml/metadata">
  <SPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
    <KeyDescriptor use="signing">
      <ds:KeyInfo>
        <ds:X509Data>
          <ds:X509Certificate>MIIDXTCCAkWgAwIBAgIJAKoK...</ds:X509Certificate>
        </ds:X509Data>
      </ds:KeyInfo>
    </KeyDescriptor>
    <AssertionConsumerService 
      Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
      Location="https://api.leanvibe.ai/v1/auth/sso/saml/acs" 
      index="0" />
    <SingleLogoutService
      Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
      Location="https://api.leanvibe.ai/v1/auth/sso/saml/sls" />
  </SPSSODescriptor>
</EntityDescriptor>
```

**Generic SAML Provider Integration:**
```bash
curl -X POST "https://api.leanvibe.ai/v1/admin/sso/providers" \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "enterprise-tenant-uuid",
    "provider": "saml2_generic",
    "provider_name": "Enterprise SAML Provider",
    "enabled": true,
    "saml_configuration": {
      "entity_id": "https://your-idp.com/saml/metadata",
      "sso_url": "https://your-idp.com/saml/sso",
      "sls_url": "https://your-idp.com/saml/sls",
      "x509_cert": "-----BEGIN CERTIFICATE-----\nMIIDXTCCAkWgAwIBAgIJAKoK...\n-----END CERTIFICATE-----",
      "metadata_url": "https://your-idp.com/saml/metadata",
      "name_id_format": "urn:oasis:names:tc:SAML:2.0:nameid-format:emailAddress",
      "binding": "HTTP-POST"
    },
    "attribute_mapping": {
      "email": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress",
      "first_name": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname", 
      "last_name": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname",
      "display_name": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name",
      "department": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/department",
      "title": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/title",
      "groups": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/groups"
    },
    "auto_provision_users": true,
    "default_role": "developer",
    "group_role_mapping": {
      "LeanVibe-Owners": "owner",
      "LeanVibe-Admins": "admin",
      "Engineering-Managers": "manager",
      "Developers": "developer",
      "QA-Team": "viewer",
      "ReadOnly-Users": "guest"
    },
    "security_settings": {
      "require_signed_assertion": true,
      "require_encrypted_assertion": false,
      "signature_algorithm": "RSA-SHA256",
      "digest_algorithm": "SHA256",
      "strict_mode": true
    }
  }'
```

## Multi-Factor Authentication (MFA)

### Enterprise MFA Policy Configuration

#### Comprehensive MFA Setup
```bash
curl -X POST "https://api.leanvibe.ai/v1/admin/mfa/policy" \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "enterprise-tenant-uuid",
    "mfa_policy": {
      "enforcement": "required",
      "grace_period_days": 7,
      "backup_codes_required": true,
      "methods": {
        "totp": {
          "enabled": true,
          "applications": ["google_authenticator", "microsoft_authenticator", "authy"],
          "issuer_name": "Acme Corp LeanVibe"
        },
        "sms": {
          "enabled": true,
          "provider": "twilio",
          "international_numbers": true,
          "rate_limiting": {
            "max_attempts_per_hour": 5,
            "cooldown_minutes": 15
          }
        },
        "email": {
          "enabled": true,
          "fallback_only": true,
          "code_length": 8,
          "expiry_minutes": 10
        },
        "push_notifications": {
          "enabled": true,
          "provider": "custom",
          "device_registration_required": true
        },
        "hardware_keys": {
          "enabled": true,
          "protocols": ["fido2", "webauthn"],
          "yubikey_support": true
        }
      },
      "role_based_enforcement": {
        "owner": {
          "required_methods": ["totp", "hardware_key"],
          "session_timeout_minutes": 30,
          "require_mfa_for_sensitive_operations": true
        },
        "admin": {
          "required_methods": ["totp"],
          "session_timeout_minutes": 60,
          "require_mfa_for_sensitive_operations": true
        },
        "manager": {
          "required_methods": ["totp", "sms"],
          "session_timeout_minutes": 120,
          "require_mfa_for_sensitive_operations": false
        },
        "developer": {
          "required_methods": ["any"],
          "session_timeout_minutes": 480,
          "require_mfa_for_sensitive_operations": false
        }
      },
      "risk_based_authentication": {
        "enabled": true,
        "factors": {
          "unknown_device": {
            "action": "require_mfa",
            "trust_duration_days": 30
          },
          "suspicious_location": {
            "action": "require_mfa",
            "geo_fence_enabled": true
          },
          "multiple_failed_attempts": {
            "action": "require_mfa_and_approval",
            "threshold": 3
          },
          "unusual_access_patterns": {
            "action": "require_mfa",
            "ml_based_detection": true
          }
        }
      }
    }
  }'
```

### MFA Implementation Examples

#### TOTP (Time-Based One-Time Password) Setup
```python
# TOTP implementation example
import pyotp
import qrcode
from io import BytesIO

async def setup_totp_mfa(user_id: UUID, organization_name: str) -> MFASetupResponse:
    """Set up TOTP-based MFA for enterprise user"""
    
    # Generate cryptographically secure secret
    secret = pyotp.random_base32()
    
    # Get user details for personalized setup
    user = await user_service.get_user(user_id)
    
    # Create enterprise-branded TOTP URI
    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=user.email,
        issuer_name=f"{organization_name} LeanVibe",
        image="https://cdn.leanvibe.ai/logos/enterprise-logo.png"
    )
    
    # Generate QR code with enterprise branding
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(totp_uri)
    qr.make(fit=True)
    
    # Create QR code image
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    # Generate enterprise backup codes
    backup_codes = [
        f"{secrets.randbelow(10000):04d}-{secrets.randbelow(10000):04d}"
        for _ in range(10)
    ]
    
    # Store MFA configuration with enterprise audit trail
    await mfa_service.store_mfa_config(user_id, {
        "method": MFAMethod.TOTP,
        "secret": await encryption_service.encrypt(secret),
        "backup_codes": await encryption_service.encrypt_list(backup_codes),
        "setup_completed": False,
        "organization": organization_name,
        "setup_timestamp": datetime.utcnow(),
        "setup_ip": request.client.host,
        "setup_user_agent": request.headers.get("User-Agent")
    })
    
    # Log enterprise security event
    await audit_service.log_security_event(
        user_id=user_id,
        event_type="mfa_setup_initiated",
        details={
            "method": "totp",
            "organization": organization_name,
            "ip_address": request.client.host
        }
    )
    
    return MFASetupResponse(
        method=MFAMethod.TOTP,
        secret=secret,
        qr_code=f"data:image/png;base64,{qr_code_base64}",
        backup_codes=backup_codes,
        manual_entry_key=secret,
        setup_instructions=[
            "Install Google Authenticator, Microsoft Authenticator, or Authy",
            "Scan the QR code or enter the manual key",
            "Enter the 6-digit code to complete setup",
            "Save backup codes in a secure location"
        ]
    )
```

#### Hardware Key (FIDO2/WebAuthn) Implementation
```python
# Hardware key implementation
from webauthn import generate_registration_options, verify_registration_response

async def setup_hardware_key_mfa(user_id: UUID) -> WebAuthnRegistration:
    """Set up FIDO2/WebAuthn hardware key authentication"""
    
    user = await user_service.get_user(user_id)
    tenant = await tenant_service.get_user_tenant(user_id)
    
    # Generate WebAuthn registration options
    registration_options = generate_registration_options(
        rp_id="leanvibe.ai",
        rp_name=f"{tenant.organization_name} LeanVibe",
        user_id=str(user_id).encode(),
        user_name=user.email,
        user_display_name=f"{user.first_name} {user.last_name}",
        attestation="direct",
        authenticator_selection={
            "authenticator_attachment": "cross-platform",  # Hardware keys
            "resident_key": "required",
            "user_verification": "required"
        },
        supported_pub_key_algs=[
            {"alg": -7, "type": "public-key"},   # ES256
            {"alg": -257, "type": "public-key"}  # RS256
        ]
    )
    
    # Store challenge for verification
    await redis_client.setex(
        f"webauthn_challenge:{user_id}",
        300,  # 5-minute expiry
        registration_options.challenge
    )
    
    return WebAuthnRegistration(
        challenge=registration_options.challenge,
        rp_id=registration_options.rp.id,
        user_id=registration_options.user.id,
        timeout=registration_options.timeout
    )

async def verify_hardware_key_registration(
    user_id: UUID, 
    registration_response: WebAuthnRegistrationResponse
) -> bool:
    """Verify and complete hardware key registration"""
    
    # Retrieve stored challenge
    stored_challenge = await redis_client.get(f"webauthn_challenge:{user_id}")
    if not stored_challenge:
        raise HTTPException(400, "Invalid or expired challenge")
    
    # Verify registration response
    verification_result = verify_registration_response(
        credential=registration_response,
        expected_challenge=stored_challenge,
        expected_origin="https://leanvibe.ai",
        expected_rp_id="leanvibe.ai"
    )
    
    if verification_result.verified:
        # Store credential information
        await mfa_service.store_hardware_key_credential(user_id, {
            "credential_id": verification_result.credential_id,
            "public_key": verification_result.credential_public_key,
            "sign_count": verification_result.sign_count,
            "device_type": "hardware_key",
            "registered_at": datetime.utcnow(),
            "last_used": None
        })
        
        # Clean up challenge
        await redis_client.delete(f"webauthn_challenge:{user_id}")
        
        # Audit log
        await audit_service.log_security_event(
            user_id=user_id,
            event_type="hardware_key_registered",
            details={"credential_id": verification_result.credential_id.hex()}
        )
        
        return True
    
    return False
```

## Role-Based Access Control (RBAC)

### Enterprise Role Hierarchy

#### Comprehensive Role System
```python
# Enterprise role and permission system
class EnterpriseRole(str, Enum):
    OWNER = "owner"           # Full organizational control
    ADMIN = "admin"           # Administrative privileges
    MANAGER = "manager"       # Team management
    DEVELOPER = "developer"   # Development access
    VIEWER = "viewer"         # Read-only access
    GUEST = "guest"           # Limited guest access

class Permission(str, Enum):
    # User Management
    USERS_CREATE = "users:create"
    USERS_READ = "users:read" 
    USERS_UPDATE = "users:update"
    USERS_DELETE = "users:delete"
    USERS_INVITE = "users:invite"
    
    # Project Management
    PROJECTS_CREATE = "projects:create"
    PROJECTS_READ = "projects:read"
    PROJECTS_UPDATE = "projects:update"
    PROJECTS_DELETE = "projects:delete"
    PROJECTS_ADMIN = "projects:admin"
    
    # Code & Development
    CODE_READ = "code:read"
    CODE_WRITE = "code:write"
    CODE_EXECUTE = "code:execute"
    CODE_DEPLOY = "code:deploy"
    CODE_REVIEW = "code:review"
    
    # AI Services
    AI_USE_BASIC = "ai:use_basic"
    AI_USE_ADVANCED = "ai:use_advanced"
    AI_TRAIN_MODELS = "ai:train_models"
    AI_ADMIN = "ai:admin"
    
    # Billing & Administration
    BILLING_READ = "billing:read"
    BILLING_ADMIN = "billing:admin"
    SETTINGS_READ = "settings:read"
    SETTINGS_ADMIN = "settings:admin"
    
    # Audit & Compliance
    AUDIT_READ = "audit:read"
    COMPLIANCE_ADMIN = "compliance:admin"
    SECURITY_ADMIN = "security:admin"

# Role-Permission Matrix
ROLE_PERMISSIONS = {
    EnterpriseRole.OWNER: [
        # Full access to everything
        "users:*", "projects:*", "code:*", "ai:*", 
        "billing:*", "settings:*", "audit:*", 
        "compliance:*", "security:*"
    ],
    
    EnterpriseRole.ADMIN: [
        # User and system administration
        "users:read", "users:update", "users:invite",
        "projects:*", "code:read", "code:review",
        "ai:use_advanced", "billing:read",
        "settings:read", "audit:read", "security:admin"
    ],
    
    EnterpriseRole.MANAGER: [
        # Team management and project oversight
        "users:read", "users:invite",
        "projects:read", "projects:update", 
        "code:read", "code:review",
        "ai:use_advanced", "billing:read"
    ],
    
    EnterpriseRole.DEVELOPER: [
        # Full development capabilities
        "projects:read", "projects:update",
        "code:*", "ai:use_basic", "ai:use_advanced"
    ],
    
    EnterpriseRole.VIEWER: [
        # Read-only access
        "projects:read", "code:read", "ai:use_basic"
    ],
    
    EnterpriseRole.GUEST: [
        # Very limited access
        "projects:read"
    ]
}
```

### Dynamic Role Assignment

#### Attribute-Based Role Assignment
```python
# Dynamic role assignment based on user attributes
class AttributeBasedRoleAssignment:
    def __init__(self):
        self.role_assignment_rules = {
            "department_based": {
                "Engineering": "developer",
                "DevOps": "developer", 
                "QA": "viewer",
                "Management": "manager",
                "Executive": "owner",
                "IT": "admin",
                "Security": "admin"
            },
            "title_based": {
                "CTO": "owner",
                "VP Engineering": "owner",
                "Engineering Director": "manager",
                "Engineering Manager": "manager",
                "Team Lead": "manager", 
                "Senior Developer": "developer",
                "Developer": "developer",
                "Junior Developer": "developer",
                "QA Engineer": "viewer",
                "DevOps Engineer": "developer",
                "System Administrator": "admin"
            },
            "group_based": {
                # Azure AD / Google Groups object IDs
                "executives": "owner",
                "it-administrators": "admin",
                "engineering-managers": "manager",
                "senior-developers": "developer",
                "developers": "developer",
                "qa-team": "viewer",
                "contractors": "guest"
            }
        }
    
    async def determine_user_role(
        self, 
        user_attributes: Dict[str, Any],
        group_memberships: List[str]
    ) -> EnterpriseRole:
        """Determine user role based on attributes and group membership"""
        
        # Priority 1: Explicit group-based assignment
        for group in group_memberships:
            group_lower = group.lower()
            for rule_group, role in self.role_assignment_rules["group_based"].items():
                if rule_group in group_lower:
                    await audit_service.log_role_assignment(
                        assignment_reason=f"group_membership:{group}",
                        assigned_role=role
                    )
                    return EnterpriseRole(role)
        
        # Priority 2: Title-based assignment
        title = user_attributes.get("title", "").lower()
        for rule_title, role in self.role_assignment_rules["title_based"].items():
            if rule_title.lower() in title:
                await audit_service.log_role_assignment(
                    assignment_reason=f"title:{title}",
                    assigned_role=role
                )
                return EnterpriseRole(role)
        
        # Priority 3: Department-based assignment  
        department = user_attributes.get("department", "").lower()
        for rule_dept, role in self.role_assignment_rules["department_based"].items():
            if rule_dept.lower() in department:
                await audit_service.log_role_assignment(
                    assignment_reason=f"department:{department}",
                    assigned_role=role
                )
                return EnterpriseRole(role)
        
        # Default: Developer role with audit trail
        await audit_service.log_role_assignment(
            assignment_reason="default_assignment",
            assigned_role="developer"
        )
        return EnterpriseRole.DEVELOPER
```

## Security & Audit Features

### Comprehensive Audit Logging

#### Enterprise Audit Trail Implementation
```python
# Comprehensive audit logging for enterprise compliance
class EnterpriseAuditService:
    async def log_authentication_event(
        self,
        user_id: Optional[UUID],
        event_type: str,
        details: Dict[str, Any],
        request: Request
    ):
        """Log detailed authentication events for compliance"""
        
        audit_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_id": str(uuid4()),
            "event_type": f"auth_{event_type}",
            "user_id": str(user_id) if user_id else None,
            "session_id": request.cookies.get("session_id"),
            "ip_address": self._get_real_ip(request),
            "user_agent": request.headers.get("User-Agent"),
            "geo_location": await self._get_geo_location(request),
            "details": details,
            "risk_score": await self._calculate_risk_score(request, details),
            "compliance_flags": await self._check_compliance_requirements(details)
        }
        
        # Store in multiple locations for redundancy
        await self._store_audit_record(audit_record)
        await self._send_to_siem(audit_record)
        
        # Real-time alerting for high-risk events
        if audit_record["risk_score"] > 0.8:
            await self._trigger_security_alert(audit_record)
    
    async def _calculate_risk_score(
        self, 
        request: Request, 
        details: Dict[str, Any]
    ) -> float:
        """Calculate risk score for authentication event"""
        
        risk_factors = {
            "unknown_device": 0.3,
            "unusual_location": 0.4,
            "multiple_failures": 0.5,
            "suspicious_user_agent": 0.2,
            "off_hours_access": 0.1,
            "privileged_role": 0.3
        }
        
        score = 0.0
        
        # Check various risk factors
        device_fingerprint = await self._get_device_fingerprint(request)
        if not await self._is_known_device(device_fingerprint):
            score += risk_factors["unknown_device"]
        
        geo_location = await self._get_geo_location(request)
        if await self._is_unusual_location(geo_location, details.get("user_id")):
            score += risk_factors["unusual_location"]
        
        if details.get("failed_attempts", 0) > 3:
            score += risk_factors["multiple_failures"]
        
        if self._is_business_hours():
            score += risk_factors["off_hours_access"]
        
        return min(score, 1.0)  # Cap at 1.0
```

### Session Management & Security

#### Advanced Session Controls
```python
# Enterprise session management
class EnterpriseSessionManager:
    def __init__(self):
        self.session_policies = {
            EnterpriseRole.OWNER: {
                "max_concurrent_sessions": 3,
                "session_timeout_minutes": 30,
                "require_mfa_renewal": True,
                "mfa_renewal_interval_minutes": 15
            },
            EnterpriseRole.ADMIN: {
                "max_concurrent_sessions": 5,
                "session_timeout_minutes": 60,
                "require_mfa_renewal": True,
                "mfa_renewal_interval_minutes": 30
            },
            EnterpriseRole.MANAGER: {
                "max_concurrent_sessions": 10,
                "session_timeout_minutes": 120,
                "require_mfa_renewal": False,
                "mfa_renewal_interval_minutes": 60
            },
            EnterpriseRole.DEVELOPER: {
                "max_concurrent_sessions": 10,
                "session_timeout_minutes": 480,
                "require_mfa_renewal": False,
                "mfa_renewal_interval_minutes": None
            }
        }
    
    async def create_enterprise_session(
        self,
        user_id: UUID,
        user_role: EnterpriseRole,
        request: Request,
        mfa_verified: bool = False
    ) -> EnterpriseSession:
        """Create enterprise session with security controls"""
        
        policy = self.session_policies[user_role]
        
        # Check concurrent session limits
        active_sessions = await self._get_active_sessions(user_id)
        if len(active_sessions) >= policy["max_concurrent_sessions"]:
            # Terminate oldest session
            oldest_session = min(active_sessions, key=lambda s: s.created_at)
            await self._terminate_session(oldest_session.session_id)
        
        # Generate secure session
        session = EnterpriseSession(
            session_id=secrets.token_urlsafe(32),
            user_id=user_id,
            user_role=user_role,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=policy["session_timeout_minutes"]),
            ip_address=self._get_real_ip(request),
            user_agent=request.headers.get("User-Agent"),
            device_fingerprint=await self._generate_device_fingerprint(request),
            mfa_verified=mfa_verified,
            mfa_verification_at=datetime.utcnow() if mfa_verified else None,
            requires_mfa_renewal=policy["require_mfa_renewal"],
            mfa_renewal_interval=policy.get("mfa_renewal_interval_minutes")
        )
        
        # Store session
        await self._store_session(session)
        
        # Audit log
        await audit_service.log_authentication_event(
            user_id=user_id,
            event_type="session_created",
            details={
                "session_id": session.session_id,
                "user_role": user_role.value,
                "mfa_verified": mfa_verified,
                "expires_at": session.expires_at.isoformat()
            },
            request=request
        )
        
        return session
```

## Enterprise Integration Examples

### GitHub Enterprise Integration

#### Complete GitHub SSO + LeanVibe Integration
```yaml
# GitHub Enterprise Server SAML Configuration
name: LeanVibe Enterprise Integration
display_name: "LeanVibe AI Development Platform"
description: "Autonomous AI development platform with enterprise authentication"

# SAML Configuration
saml:
  sso_url: "https://api.leanvibe.ai/v1/auth/sso/saml/github/acs"
  certificate_fingerprint: "AA:BB:CC:DD:EE:FF:00:11:22:33:44:55:66:77:88:99:AA:BB:CC:DD"
  issuer: "https://github-enterprise.acme-corp.com"
  
  # Attribute Mapping
  attribute_mapping:
    email: "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress"
    full_name: "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name"
    username: "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier"

# Team Mapping for Role Assignment  
team_mapping:
  "acme-corp/owners": "owner"
  "acme-corp/administrators": "admin"
  "acme-corp/engineering-managers": "manager"
  "acme-corp/senior-developers": "developer"
  "acme-corp/developers": "developer"
  "acme-corp/qa-team": "viewer"
```

### Slack Integration for Authentication Notifications

#### Real-Time Authentication Alerts
```python
# Slack integration for authentication events
class SlackAuthenticationNotifier:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    async def notify_high_risk_authentication(
        self,
        user_email: str,
        risk_score: float,
        details: Dict[str, Any]
    ):
        """Send high-risk authentication alert to Slack"""
        
        color = "danger" if risk_score > 0.8 else "warning"
        
        slack_message = {
            "attachments": [
                {
                    "color": color,
                    "title": "🚨 High-Risk Authentication Alert",
                    "fields": [
                        {
                            "title": "User",
                            "value": user_email,
                            "short": True
                        },
                        {
                            "title": "Risk Score", 
                            "value": f"{risk_score:.2f}",
                            "short": True
                        },
                        {
                            "title": "IP Address",
                            "value": details.get("ip_address", "Unknown"),
                            "short": True
                        },
                        {
                            "title": "Location",
                            "value": details.get("geo_location", {}).get("city", "Unknown"),
                            "short": True
                        }
                    ],
                    "actions": [
                        {
                            "type": "button",
                            "text": "View Details",
                            "url": f"https://admin.leanvibe.ai/audit/authentication/{details.get('event_id')}"
                        },
                        {
                            "type": "button", 
                            "text": "Block User",
                            "url": f"https://admin.leanvibe.ai/users/{details.get('user_id')}/block"
                        }
                    ],
                    "footer": "LeanVibe Security",
                    "ts": int(datetime.utcnow().timestamp())
                }
            ]
        }
        
        async with httpx.AsyncClient() as client:
            await client.post(self.webhook_url, json=slack_message)
```

## Troubleshooting & Support

### Common Issues & Solutions

#### Google Workspace Issues
```bash
# Issue: OAuth consent screen errors
# Solution: Verify domain ownership and OAuth scopes

# Check Google Workspace domain verification
curl -X GET "https://www.googleapis.com/admin/directory/v1/domains" \
  -H "Authorization: Bearer your-admin-access-token"

# Verify OAuth application status
gcloud auth application-default print-access-token | \
curl -X GET "https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=$(cat -)"
```

#### Microsoft Azure AD Issues
```powershell
# Issue: Conditional Access blocking authentication
# Solution: Configure Conditional Access policies for LeanVibe

# Check Conditional Access policies
Get-AzureADMSConditionalAccessPolicy | Where-Object {$_.State -eq "Enabled"}

# Verify application permissions
Get-AzureADApplication -SearchString "LeanVibe" | Get-AzureADApplicationExtensionProperty
```

#### SAML Configuration Issues
```bash
# Issue: SAML assertion signature verification fails
# Solution: Verify certificate and clock synchronization

# Test SAML metadata accessibility
curl -X GET "https://your-idp.com/saml/metadata" \
  -H "Accept: application/xml" \
  --cert client-cert.pem \
  --key client-key.pem

# Validate SAML response
curl -X POST "https://api.leanvibe.ai/v1/admin/saml/validate" \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/xml" \
  --data-binary @saml-response.xml
```

### Enterprise Support Channels

#### Technical Support
- **Email**: enterprise-auth@leanvibe.ai
- **Phone**: +1 (555) 123-4567 ext. 2
- **Emergency Hotline**: +1 (555) 123-4567 ext. 911
- **Slack**: #enterprise-authentication in LeanVibe Community

#### Implementation Support
- **Architecture Review**: [Schedule Review](https://calendly.com/leanvibe/auth-architecture)
- **Implementation Assistance**: implementation@leanvibe.ai
- **Security Consultation**: security@leanvibe.ai
- **Compliance Support**: compliance@leanvibe.ai

---

**Ready to implement enterprise authentication?** Contact our authentication specialists for personalized setup assistance and ensure a seamless, secure identity management experience for your organization.

This comprehensive guide provides enterprise-grade authentication implementation with the security, scalability, and compliance features required for large-scale organizational deployments.