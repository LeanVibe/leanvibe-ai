# Enterprise SSO and SAML Integration Guide

## Overview

LeanVibe's enterprise authentication system provides seamless Single Sign-On integration with major identity providers including Google Workspace, Microsoft Azure AD, Okta, Auth0, and any SAML 2.0 compliant provider. This comprehensive guide provides step-by-step configuration instructions for enterprise SSO deployment with advanced security features.

## Supported Identity Providers

### OAuth2/OpenID Connect Providers
- **Google Workspace** - Complete OAuth2/OpenID Connect integration
- **Microsoft Azure AD** - OAuth2, OpenID Connect, and Graph API integration  
- **Auth0** - Universal authentication platform integration
- **Okta** - OAuth2 and OpenID Connect support

### SAML 2.0 Providers
- **Okta** - Enterprise SAML 2.0 integration
- **Microsoft Azure AD** - SAML 2.0 with advanced claim mapping
- **OneLogin** - Enterprise identity platform
- **Ping Identity** - Enterprise federation services
- **Generic SAML 2.0** - Any compliant SAML identity provider

### Directory Services
- **LDAP/Active Directory** - Via SAML bridge or direct LDAP integration
- **Google Directory** - Via Google Workspace SSO
- **Azure Active Directory** - Direct integration with Microsoft Graph

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│              LeanVibe Authentication Architecture       │
├─────────────────────────────────────────────────────────┤
│  Identity       │  Authentication  │  Authorization     │
│  Providers      │  Layer          │  & Access Control │
│                 │                 │                    │
│  • Google       │  • JWT Tokens   │  • RBAC           │
│  • Microsoft    │  • SAML         │  • Permissions    │
│  • Okta         │  • OAuth2       │  • Tenant Scope   │
│  • SAML 2.0     │  • MFA          │  • Audit Trails   │
└─────────────────────────────────────────────────────────┘
           │                    │                    │
    ┌─────────────┐    ┌─────────────────┐    ┌─────────────┐
    │  Identity   │    │  Authentication │    │   User      │
    │  Federation │    │  Middleware     │    │ Management  │
    │             │    │                 │    │             │
    └─────────────┘    └─────────────────┘    └─────────────┘
```

## Step-by-Step Setup Instructions

### Google Workspace Integration

#### Step 1: Create Google OAuth Application

1. Navigate to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing project
3. Enable the following APIs:
   - Google+ API
   - Google People API  
   - Admin SDK API (for directory sync)

4. Go to **APIs & Services** → **Credentials**
5. Click **Create Credentials** → **OAuth 2.0 Client IDs**

**OAuth Application Configuration:**
```
Application Type: Web application
Name: LeanVibe Enterprise SSO
Authorized JavaScript origins: 
  - https://your-domain.leanvibe.ai
  - https://app.leanvibe.ai
Authorized redirect URIs:
  - https://your-domain.leanvibe.ai/auth/google/callback
  - https://api.leanvibe.ai/v1/auth/sso/google/callback
```

6. Save the **Client ID** and **Client Secret**

#### Step 2: Configure LeanVibe SSO Settings

**API Configuration:**
```bash
curl -X POST "https://api.leanvibe.ai/v1/admin/sso/providers" \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "your-tenant-id",
    "provider": "google",
    "provider_name": "Google Workspace",
    "enabled": true,
    "client_id": "your-google-client-id.apps.googleusercontent.com",
    "client_secret": "your-google-client-secret",
    "scopes": ["openid", "email", "profile"],
    "auto_provision_users": true,
    "default_role": "developer",
    "allowed_domains": ["yourcompany.com", "subsidiary.com"],
    "attribute_mapping": {
      "email": "email",
      "first_name": "given_name",
      "last_name": "family_name",
      "display_name": "name"
    }
  }'
```

#### Step 3: Advanced Google Workspace Configuration

**Directory Synchronization Setup:**
```json
{
  "directory_sync": {
    "enabled": true,
    "sync_frequency": "hourly",
    "sync_groups": true,
    "group_role_mapping": {
      "Engineering": "developer",
      "Engineering Managers": "manager",
      "Administrators": "admin",
      "Executives": "owner"
    },
    "auto_deprovision": true,
    "sync_user_attributes": [
      "department",
      "title",
      "manager",
      "location"
    ]
  }
}
```

### Microsoft Azure AD Integration

#### Step 1: Register Application in Azure Portal

1. Sign in to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** → **App registrations**
3. Click **New registration**

**Application Registration Settings:**
```
Name: LeanVibe Enterprise
Supported account types: Accounts in this organizational directory only
Redirect URI: Web - https://api.leanvibe.ai/v1/auth/sso/microsoft/callback
```

#### Step 2: Configure Application Settings

**Authentication Configuration:**
- Add additional redirect URIs:
  - `https://your-domain.leanvibe.ai/auth/microsoft/callback`
  - `https://app.leanvibe.ai/auth/microsoft/callback`
- Enable ID tokens and access tokens
- Set logout URL: `https://your-domain.leanvibe.ai/logout`

**Certificates & Secrets:**
1. Create new client secret
2. Set expiration to 24 months (recommended)
3. Copy the secret value (visible only once)

**API Permissions:**
Required Microsoft Graph permissions:
- `User.Read` - Read user profile
- `User.ReadBasic.All` - Read basic profiles of all users
- `Directory.Read.All` - Read directory data
- `GroupMember.Read.All` - Read group memberships
- `email` - Access email address
- `openid` - OpenID Connect sign-in
- `profile` - Access basic profile information

#### Step 3: LeanVibe Azure AD Configuration

```bash
curl -X POST "https://api.leanvibe.ai/v1/admin/sso/providers" \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "your-tenant-id",
    "provider": "microsoft",
    "provider_name": "Microsoft Azure AD",
    "enabled": true,
    "client_id": "your-azure-application-id",
    "client_secret": "your-azure-client-secret",
    "auth_url": "https://login.microsoftonline.com/your-tenant-id/oauth2/v2.0/authorize",
    "token_url": "https://login.microsoftonline.com/your-tenant-id/oauth2/v2.0/token",
    "userinfo_url": "https://graph.microsoft.com/v1.0/me",
    "scopes": ["openid", "email", "profile", "User.Read"],
    "auto_provision_users": true,
    "default_role": "developer",
    "allowed_domains": ["yourcompany.com"],
    "attribute_mapping": {
      "email": "mail",
      "first_name": "givenName",
      "last_name": "surname",
      "display_name": "displayName",
      "department": "department",
      "job_title": "jobTitle"
    }
  }'
```

#### Step 4: Azure AD Group Synchronization

**Advanced Configuration with Group Mapping:**
```json
{
  "group_synchronization": {
    "enabled": true,
    "sync_frequency": "every_2_hours",
    "group_attribute": "groups",
    "group_role_mapping": {
      "f47ac10b-58cc-4372-a567-0e02b2c3d479": "owner",      // Executives group
      "6ba7b810-9dad-11d1-80b4-00c04fd430c8": "admin",      // IT Administrators
      "6ba7b811-9dad-11d1-80b4-00c04fd430c9": "manager",    // Team Leads
      "6ba7b812-9dad-11d1-80b4-00c04fd430c0": "developer"   // Developers
    },
    "nested_groups": true,
    "group_claims": true
  }
}
```

### Okta SAML Configuration

#### Step 1: Create Okta Application

1. Log into Okta Admin Console
2. Navigate to **Applications** → **Create App Integration**
3. Select **SAML 2.0**

**General Settings:**
```
App name: LeanVibe Enterprise
App logo: [Upload LeanVibe logo from assets]
App visibility: Display application icon to users
```

#### Step 2: SAML Configuration

**SAML Settings:**
```
Single sign on URL: https://api.leanvibe.ai/v1/auth/sso/saml/okta/acs
Use this for Recipient URL and Destination URL: ✓
Audience URI (SP Entity ID): https://api.leanvibe.ai/v1/auth/sso/saml/metadata
Default RelayState: [leave empty]
Name ID format: EmailAddress
Application username: Email
Update application username on: Create and update
```

**Attribute Statements (optional):**
```
Name: email          | Name format: Unspecified | Value: user.email
Name: firstName      | Name format: Unspecified | Value: user.firstName  
Name: lastName       | Name format: Unspecified | Value: user.lastName
Name: displayName    | Name format: Unspecified | Value: user.displayName
Name: department     | Name format: Unspecified | Value: user.department
Name: title          | Name format: Unspecified | Value: user.title
```

**Group Attribute Statements:**
```
Name: groups        | Name format: Unspecified | Value: getFilteredGroups({"group_name"}, "group.name", 100)
```

#### Step 3: Extract Okta Metadata

From the Okta application's **Sign On** tab, copy:
- **Identity Provider metadata** (XML)
- **Identity Provider Single Sign-On URL**
- **X.509 Certificate**

#### Step 4: Configure LeanVibe SAML

```bash
curl -X POST "https://api.leanvibe.ai/v1/admin/sso/providers" \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "your-tenant-id",
    "provider": "saml",
    "provider_name": "Okta Enterprise SSO",
    "enabled": true,
    "saml_entity_id": "http://www.okta.com/exk1a2b3c4d5e6f7g8h9i0j1",
    "saml_sso_url": "https://yourcompany.okta.com/app/leanvibe_enterprise_1/exk1a2b3c4d5e6f7g8h9i0j1/sso/saml",
    "saml_x509_cert": "-----BEGIN CERTIFICATE-----\nMIIDpDCCAoygAwIBAgIGAV2ka...\n-----END CERTIFICATE-----",
    "saml_metadata_url": "https://yourcompany.okta.com/app/exk1a2b3c4d5e6f7g8h9i0j1/sso/saml/metadata",
    "attribute_mapping": {
      "email": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress",
      "first_name": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname",
      "last_name": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname",
      "display_name": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name"
    },
    "auto_provision_users": true,
    "default_role": "developer",
    "group_attribute": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/groups",
    "group_role_mapping": {
      "LeanVibe-Owners": "owner",
      "LeanVibe-Admins": "admin",
      "Engineering-Leads": "manager",
      "Developers": "developer",
      "QA-Team": "viewer"
    }
  }'
```

## Generic SAML 2.0 Provider Setup

### Step 1: LeanVibe Service Provider Configuration

Provide these details to your identity provider:

**Service Provider (SP) Details:**
```
Entity ID: https://api.leanvibe.ai/v1/auth/sso/saml/metadata
ACS URL: https://api.leanvibe.ai/v1/auth/sso/saml/acs
Binding: HTTP-POST
Name ID Format: urn:oasis:names:tc:SAML:2.0:nameid-format:emailAddress
Single Logout URL: https://api.leanvibe.ai/v1/auth/sso/saml/sls
```

### Step 2: Required SAML Attributes

Your identity provider must send these attributes in the SAML assertion:

```xml
<saml2:Attribute Name="email">
  <saml2:AttributeValue>user@company.com</saml2:AttributeValue>
</saml2:Attribute>

<saml2:Attribute Name="firstName">
  <saml2:AttributeValue>John</saml2:AttributeValue>
</saml2:Attribute>

<saml2:Attribute Name="lastName">
  <saml2:AttributeValue>Doe</saml2:AttributeValue>
</saml2:Attribute>

<saml2:Attribute Name="displayName">
  <saml2:AttributeValue>John Doe</saml2:AttributeValue>
</saml2:Attribute>

<!-- Optional: Group memberships for role mapping -->
<saml2:Attribute Name="groups">
  <saml2:AttributeValue>Engineering</saml2:AttributeValue>
  <saml2:AttributeValue>Team-Leads</saml2:AttributeValue>
</saml2:Attribute>
```

### Step 3: Upload Provider Metadata

**Option 1: Metadata URL**
```bash
curl -X POST "https://api.leanvibe.ai/v1/admin/sso/saml/metadata-url" \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "your-tenant-id",
    "metadata_url": "https://your-idp.com/metadata.xml"
  }'
```

**Option 2: Upload XML Metadata File**
```bash
curl -X POST "https://api.leanvibe.ai/v1/admin/sso/saml/metadata" \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/xml" \
  --data-binary @idp-metadata.xml
```

## Multi-Factor Authentication Setup

### Enterprise MFA Configuration

```bash
curl -X POST "https://api.leanvibe.ai/v1/admin/sso/mfa-policy" \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "your-tenant-id",
    "mfa_required": true,
    "mfa_methods": ["totp", "sms", "push"],
    "mfa_bypass_for_sso": false,
    "backup_codes_enabled": true,
    "grace_period_days": 7,
    "enforce_for_roles": ["owner", "admin"],
    "risk_based_mfa": {
      "enabled": true,
      "unknown_device": true,
      "suspicious_location": true,
      "high_risk_score": 0.8
    }
  }'
```

### TOTP Setup Flow Implementation

```python
# MFA setup implementation from app/services/auth_service.py
class AuthService:
    async def setup_mfa_totp(self, user_id: UUID) -> MFASetupResponse:
        """Set up TOTP-based MFA for user"""
        
        # Generate unique secret for user
        secret = pyotp.random_base32()
        
        # Create TOTP URI for QR code
        user = await self.get_user(user_id)
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            user.email,
            issuer_name="LeanVibe Enterprise"
        )
        
        # Generate QR code
        qr_code_url = await self.generate_qr_code(totp_uri)
        
        # Generate backup codes
        backup_codes = [secrets.token_hex(4) for _ in range(10)]
        
        # Store MFA configuration (encrypted)
        await self.store_mfa_config(user_id, {
            "method": "totp",
            "secret": secret,
            "backup_codes": backup_codes,
            "setup_completed": False
        })
        
        return MFASetupResponse(
            method=MFAMethod.TOTP,
            secret=secret,
            qr_code=qr_code_url,
            backup_codes=backup_codes
        )
```

### SMS and Push Notification MFA

**SMS MFA Setup:**
```python
async def setup_mfa_sms(self, user_id: UUID, phone_number: str) -> MFASetupResponse:
    """Set up SMS-based MFA"""
    
    # Validate and format phone number
    parsed_number = phonenumbers.parse(phone_number, None)
    if not phonenumbers.is_valid_number(parsed_number):
        raise ValueError("Invalid phone number")
    
    # Send verification SMS
    verification_code = secrets.randbelow(900000) + 100000  # 6-digit code
    await self.sms_service.send_verification(phone_number, verification_code)
    
    # Store pending MFA setup
    await self.store_pending_mfa_setup(user_id, {
        "method": "sms",
        "phone_number": phone_number,
        "verification_code": verification_code,
        "expires_at": datetime.utcnow() + timedelta(minutes=10)
    })
    
    return MFASetupResponse(method=MFAMethod.SMS)
```

## User Provisioning & Role Management

### Automatic User Provisioning

**JIT (Just-In-Time) Provisioning Configuration:**
```json
{
  "auto_provision_users": true,
  "provision_strategy": "jit",
  "default_role": "developer",
  "role_mapping_strategy": "attribute_based",
  "attribute_role_mapping": {
    "department": {
      "Engineering": "developer",
      "Management": "manager", 
      "Executive": "owner",
      "IT": "admin"
    },
    "title": {
      "CTO": "owner",
      "Engineering Manager": "manager",
      "Senior Developer": "developer",
      "Developer": "developer"
    }
  },
  "group_role_mapping": {
    "Administrators": "admin",
    "Team Leads": "manager",
    "Developers": "developer",
    "Read Only": "viewer"
  }
}
```

### SCIM User Provisioning

**SCIM 2.0 Endpoint Configuration:**
```
SCIM Base URL: https://api.leanvibe.ai/v1/scim/v2
Authentication: Bearer token
Supported Operations:
  - GET /Users (list users)
  - GET /Users/{id} (get user)
  - POST /Users (create user)
  - PUT /Users/{id} (update user)
  - PATCH /Users/{id} (partial update)
  - DELETE /Users/{id} (delete user)
  - GET /Groups (list groups)
  - POST /Groups (create group)
```

### Advanced Role-Based Access Control

**Granular Permission System:**
```python
# Role and permission implementation
class TenantRole:
    """Enhanced role system with granular permissions"""
    
    ROLE_PERMISSIONS = {
        UserRole.OWNER: [
            "users:*", "projects:*", "billing:*", "settings:*", 
            "integrations:*", "audit:read", "support:create"
        ],
        UserRole.ADMIN: [
            "users:read", "users:write", "projects:*", "settings:read",
            "integrations:read", "audit:read"
        ],
        UserRole.MANAGER: [
            "users:read", "projects:read", "projects:write", 
            "team:manage", "reports:read"
        ],
        UserRole.DEVELOPER: [
            "projects:read", "projects:write", "code:*", 
            "ai:use", "files:*"
        ],
        UserRole.VIEWER: [
            "projects:read", "files:read", "reports:read"
        ]
    }
    
    @classmethod
    def has_permission(cls, role: UserRole, permission: str) -> bool:
        """Check if role has specific permission"""
        role_perms = cls.ROLE_PERMISSIONS.get(role, [])
        
        # Check exact match
        if permission in role_perms:
            return True
        
        # Check wildcard match
        for perm in role_perms:
            if perm.endswith(':*'):
                resource = perm.split(':')[0]
                if permission.startswith(f"{resource}:"):
                    return True
        
        return False
```

## Testing & Validation

### SSO Integration Test Suite

**Automated Testing Script:**
```bash
#!/bin/bash
# SSO Integration Test Suite

echo "🔍 Testing SSO Configuration..."

# Test 1: Provider Configuration
echo "Testing provider configuration..."
curl -f -X GET "https://api.leanvibe.ai/v1/admin/sso/providers" \
  -H "Authorization: Bearer $ADMIN_TOKEN" > /dev/null
echo "✅ Provider configuration accessible"

# Test 2: Google OAuth Flow
echo "Testing Google OAuth redirect..."
GOOGLE_AUTH_URL=$(curl -s -X GET "https://api.leanvibe.ai/v1/auth/sso/google/login" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.auth_url')
if [[ $GOOGLE_AUTH_URL == https://accounts.google.com* ]]; then
  echo "✅ Google OAuth redirect URL generated"
else
  echo "❌ Google OAuth configuration failed"
fi

# Test 3: SAML Metadata Validation
echo "Testing SAML metadata..."
curl -f -X GET "https://api.leanvibe.ai/v1/auth/sso/saml/metadata" \
  -H "Content-Type: application/xml" > /dev/null
echo "✅ SAML metadata endpoint accessible"

# Test 4: User Provisioning Test
echo "Testing user provisioning..."
TEST_USER_RESPONSE=$(curl -s -X POST "https://api.leanvibe.ai/v1/admin/users/test-provision" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@yourcompany.com",
    "first_name": "Test",
    "last_name": "User",
    "provider": "google"
  }')

if [[ $(echo $TEST_USER_RESPONSE | jq -r '.success') == "true" ]]; then
  echo "✅ User provisioning test passed"
else
  echo "❌ User provisioning test failed"
fi

echo "🎉 SSO Integration test suite completed"
```

### Production Validation Checklist

**Pre-Production Checklist:**
- [ ] **Identity Provider Configuration**
  - [ ] OAuth2/SAML application properly configured
  - [ ] Redirect URIs match production domains
  - [ ] Certificates valid and properly configured
  - [ ] Attribute mappings tested and validated

- [ ] **User Provisioning**
  - [ ] JIT provisioning creates users with correct roles
  - [ ] Group synchronization maps to appropriate roles
  - [ ] Deprovisioning removes access appropriately
  - [ ] Email domain restrictions enforced

- [ ] **Security Validation**
  - [ ] MFA enforcement working correctly
  - [ ] Session management and timeout configured
  - [ ] Audit logging capturing authentication events
  - [ ] Failed authentication attempts locked out

- [ ] **Integration Testing**
  - [ ] End-to-end authentication flow tested
  - [ ] Multiple users can authenticate simultaneously
  - [ ] Role-based access control validated
  - [ ] Error handling for invalid credentials tested

## Troubleshooting Common Issues

### Google SSO Issues

**Error: `redirect_uri_mismatch`**
```
Cause: Redirect URI not properly configured in Google Console
Solution: Verify exact URI match in Google OAuth configuration
Debug: Check browser developer tools for the exact redirect URI being used
```

**Error: `invalid_client`**
```
Cause: Incorrect client ID or client secret
Solution: 
1. Verify client credentials in Google Cloud Console
2. Ensure client secret hasn't expired
3. Check for whitespace/encoding issues in credentials
```

**Error: `access_denied`**
```
Cause: User doesn't have access or admin consent required
Solution:
1. Verify user is in allowed domains list
2. Check Google Workspace admin settings
3. Ensure application has been granted admin consent
```

### Microsoft Azure Issues

**Error: `AADSTS50011` - Reply URL mismatch**
```
Cause: Redirect URI doesn't match Azure AD registration
Solution:
1. Check exact redirect URI in Azure portal
2. Ensure protocol (http/https) matches
3. Verify path case sensitivity
```

**Error: `AADSTS65001` - User consent not granted**
```
Cause: Application permissions require admin consent
Solution:
1. Grant admin consent in Azure portal
2. Add permissions to app registration
3. Ensure tenant admin has approved application
```

**Error: `AADSTS70001` - Application not found**
```
Cause: Application ID incorrect or application deleted
Solution:
1. Verify application ID in Azure portal
2. Check application is enabled
3. Ensure correct tenant ID in auth URLs
```

### SAML Issues

**Error: `invalid_saml_response`**
```
Cause: SAML response validation failed
Debug Steps:
1. Check SAML response in browser developer tools
2. Verify certificate matches IdP configuration
3. Validate SAML assertion attributes
4. Check clock synchronization between IdP and SP
```

**Error: `user_not_found` after SAML authentication**
```
Cause: User provisioning disabled or attribute mapping issue
Solution:
1. Enable auto-provisioning in SSO configuration
2. Verify email attribute mapping
3. Check allowed domains configuration
4. Review audit logs for provisioning errors
```

**Error: `signature_verification_failed`**
```
Cause: SAML signature validation failed
Solution:
1. Verify X.509 certificate is correct and current
2. Check certificate format (PEM encoding)
3. Ensure IdP is signing assertions or responses
4. Verify signature algorithm compatibility
```

### General Debugging

**Enable Comprehensive Debug Logging:**
```python
# Enhanced logging configuration for SSO debugging
import logging

# Configure SSO-specific logging
sso_logger = logging.getLogger('leanvibe.sso')
sso_logger.setLevel(logging.DEBUG)

# Add detailed formatter
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - '
    '%(funcName)s:%(lineno)d - %(message)s'
)

handler = logging.StreamHandler()
handler.setFormatter(formatter)
sso_logger.addHandler(handler)

# Log all authentication attempts
@router.post("/auth/login")
async def login(request: LoginRequest):
    sso_logger.info(
        f"Authentication attempt: provider={request.provider}, "
        f"email={request.email}, ip={request.ip_address}"
    )
    # ... rest of login logic
```

**Authentication Event Monitoring:**
```bash
# Monitor authentication events in real-time
curl -X GET "https://api.leanvibe.ai/v1/admin/audit/auth/stream" \
  -H "Authorization: Bearer admin-token" \
  -H "Accept: text/event-stream"
```

## Advanced Enterprise Features

### Conditional Access Policies

**Risk-Based Authentication:**
```json
{
  "conditional_access": {
    "enabled": true,
    "policies": [
      {
        "name": "High Risk Location",
        "conditions": {
          "location_risk": "high",
          "device_trust": "unknown"
        },
        "actions": {
          "require_mfa": true,
          "session_frequency": "every_time"
        }
      },
      {
        "name": "Admin Role Protection",
        "conditions": {
          "user_role": ["owner", "admin"],
          "location": "outside_corporate_network"
        },
        "actions": {
          "require_mfa": true,
          "require_compliant_device": true,
          "session_timeout_minutes": 30
        }
      }
    ]
  }
}
```

### Identity Governance & Administration

**Automated User Lifecycle Management:**
```python
# Automated user lifecycle management
class IdentityGovernanceService:
    async def process_user_lifecycle_event(self, event: UserLifecycleEvent):
        """Handle user lifecycle events from identity provider"""
        
        if event.type == "user_created":
            await self.provision_user_access(event.user)
        elif event.type == "user_updated":
            await self.update_user_attributes(event.user)
        elif event.type == "user_disabled":
            await self.suspend_user_access(event.user)
        elif event.type == "user_deleted":
            await self.deprovision_user_access(event.user)
        elif event.type == "group_membership_changed":
            await self.update_user_roles(event.user, event.groups)
    
    async def quarterly_access_review(self):
        """Automated quarterly access review process"""
        overdue_users = await self.get_users_requiring_access_review()
        
        for user in overdue_users:
            review_request = await self.create_access_review_request(user)
            await self.notify_manager_for_review(user.manager, review_request)
            
        return len(overdue_users)
```

### Privileged Access Management

**Just-In-Time Admin Access:**
```python
# JIT access management for privileged roles
class PrivilegedAccessManager:
    async def request_elevated_access(
        self, 
        user_id: UUID, 
        requested_role: UserRole,
        duration_hours: int,
        justification: str
    ):
        """Request temporary elevated access"""
        
        # Validate request
        if requested_role in [UserRole.OWNER, UserRole.ADMIN]:
            if not justification or len(justification) < 10:
                raise ValueError("Detailed justification required for elevated access")
        
        # Create approval workflow
        approval_request = await self.create_approval_request(
            user_id=user_id,
            requested_role=requested_role,
            duration=timedelta(hours=duration_hours),
            justification=justification
        )
        
        # Notify approvers
        approvers = await self.get_role_approvers(requested_role)
        for approver in approvers:
            await self.send_approval_notification(approver, approval_request)
        
        return approval_request
```

## Enterprise Support

### Implementation Services

**Technical Integration Consultation:**
- **Duration**: 4-8 hour implementation sessions
- **Scope**: End-to-end SSO setup with best practices
- **Deliverables**: Production-ready configuration and documentation
- **Follow-up**: 30-day post-implementation support

**Security Architecture Review:**
- **Assessment**: Current authentication security posture
- **Recommendations**: Industry best practices and compliance requirements
- **Implementation**: Security hardening and monitoring setup
- **Validation**: Penetration testing and security audit support

**Enterprise Training Programs:**
- **Administrator Training**: SSO management and troubleshooting
- **End-User Training**: Authentication workflows and security practices
- **Security Training**: Identity and access management best practices
- **Custom Training**: Organization-specific authentication workflows

### Ongoing Enterprise Support

**24/7 Enterprise Helpdesk:**
- **Response Time**: <1 hour for critical authentication issues
- **Escalation**: Direct access to SSO engineering team
- **Monitoring**: Proactive authentication system monitoring
- **Reporting**: Monthly authentication and security reports

**Compliance & Security Services:**
- **SOC2 Type II**: Audit support and documentation assistance
- **GDPR Compliance**: Identity data handling and privacy controls
- **Industry Standards**: NIST, ISO 27001, and industry-specific compliance
- **Security Monitoring**: Advanced threat detection and response

### Contact Enterprise SSO Support

**Technical Support:**
- **Email**: sso-support@leanvibe.ai
- **Phone**: +1 (555) 123-4567 ext. 2
- **Emergency Hotline**: +1 (555) 123-4567 ext. 911
- **Slack**: #enterprise-sso in LeanVibe Community

**Architecture Consultation:**
- **Email**: enterprise-architects@leanvibe.ai
- **Scheduling**: [Book SSO Architecture Review](https://calendly.com/leanvibe/sso-review)
- **Documentation**: [Enterprise SSO Knowledge Base](https://docs.leanvibe.ai/enterprise/sso)

**Security & Compliance:**
- **Email**: security@leanvibe.ai
- **Phone**: +1 (555) 123-4567 ext. 5
- **Compliance Team**: compliance@leanvibe.ai

---

**Ready to implement enterprise SSO?** Contact our integration specialists for personalized setup assistance and ensure a seamless, secure authentication experience for your organization with comprehensive identity provider integration and advanced security features.

This comprehensive guide provides enterprise-grade SSO implementation with the security, scalability, and compliance features required for large-scale organizational deployments.