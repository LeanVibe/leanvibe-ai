# LeanVibe Enterprise SSO Setup Guide

## Overview

LeanVibe's enterprise authentication system provides seamless Single Sign-On integration with major identity providers including Google Workspace, Microsoft Azure AD, Okta, Auth0, and any SAML 2.0 compliant provider. This guide provides step-by-step configuration instructions for enterprise SSO deployment.

## Supported Authentication Providers

- **Google Workspace** (OAuth2/OpenID Connect)
- **Microsoft Azure AD** (OAuth2/OpenID Connect + SAML)
- **Okta** (SAML 2.0 + OAuth2)
- **Auth0** (OAuth2/OpenID Connect)
- **Generic SAML 2.0** providers
- **LDAP/Active Directory** (via SAML bridge)

## Prerequisites

### LeanVibe Platform Requirements
- Enterprise or Team tier subscription
- Admin access to your LeanVibe tenant
- SSL certificate configured for your domain

### Identity Provider Requirements
- Administrative access to your identity provider
- Ability to create and configure applications
- Domain ownership verification (for some providers)

## Google Workspace SSO Configuration

### Step 1: Create Google OAuth Application

1. Navigate to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing project
3. Enable the Google+ API and Google People API
4. Go to **APIs & Services** → **Credentials**
5. Click **Create Credentials** → **OAuth 2.0 Client IDs**

**Configuration Settings:**
```
Application Type: Web application
Name: LeanVibe Enterprise SSO
Authorized JavaScript origins: https://your-domain.leanvibe.ai
Authorized redirect URIs: 
  - https://your-domain.leanvibe.ai/auth/google/callback
  - https://api.leanvibe.ai/v1/auth/sso/google/callback
```

6. Save the **Client ID** and **Client Secret**

### Step 2: Configure LeanVibe SSO Settings

Access your LeanVibe admin panel at `https://your-domain.leanvibe.ai/admin/sso`

```json
{
  "provider": "google",
  "provider_name": "Google Workspace",
  "enabled": true,
  "client_id": "your-google-client-id",
  "client_secret": "your-google-client-secret",
  "scopes": ["openid", "email", "profile"],
  "auto_provision_users": true,
  "default_role": "developer",
  "allowed_domains": ["yourcompany.com"],
  "attribute_mapping": {
    "email": "email",
    "first_name": "given_name", 
    "last_name": "family_name",
    "display_name": "name"
  }
}
```

### Step 3: Test Google SSO Integration

1. Navigate to `https://your-domain.leanvibe.ai/login`
2. Click **Sign in with Google**
3. Complete OAuth flow with test account
4. Verify user creation and role assignment

**API Testing:**
```bash
curl -X POST "https://api.leanvibe.ai/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@yourcompany.com",
    "provider": "google",
    "auth_code": "google-oauth-code"
  }'
```

## Microsoft Azure AD Configuration

### Step 1: Register Application in Azure

1. Sign in to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** → **App registrations**
3. Click **New registration**

**Registration Settings:**
```
Name: LeanVibe Enterprise
Supported account types: Accounts in this organizational directory only
Redirect URI: Web - https://your-domain.leanvibe.ai/auth/microsoft/callback
```

### Step 2: Configure Application Settings

After registration, configure the following:

**Authentication:**
- Add redirect URI: `https://api.leanvibe.ai/v1/auth/sso/microsoft/callback`
- Enable ID tokens and access tokens
- Set logout URL: `https://your-domain.leanvibe.ai/logout`

**Certificates & Secrets:**
- Create new client secret
- Note the secret value (visible only once)

**API Permissions:**
- Microsoft Graph: `User.Read`
- Microsoft Graph: `email`
- Microsoft Graph: `openid`
- Microsoft Graph: `profile`

### Step 3: LeanVibe Configuration

```json
{
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
  "allowed_domains": ["yourcompany.com"]
}
```

## Okta SAML Configuration

### Step 1: Create Okta Application

1. Log into Okta Admin Console
2. Navigate to **Applications** → **Create App Integration**
3. Select **SAML 2.0**

**General Settings:**
```
App name: LeanVibe Enterprise
App logo: [Upload LeanVibe logo]
```

**SAML Settings:**
```
Single sign on URL: https://api.leanvibe.ai/v1/auth/sso/saml/okta/acs
Audience URI (SP Entity ID): https://api.leanvibe.ai/v1/auth/sso/saml/metadata
Name ID format: EmailAddress
Application username: Email
```

**Attribute Statements:**
```
email: user.email
firstName: user.firstName
lastName: user.lastName
displayName: user.displayName
```

### Step 2: Extract Okta Metadata

From Okta application settings, copy:
- **Identity Provider metadata URL**
- **X.509 Certificate**
- **SSO URL**
- **Entity ID**

### Step 3: Configure LeanVibe SAML

```json
{
  "provider": "saml",
  "provider_name": "Okta SSO",
  "enabled": true,
  "saml_entity_id": "http://www.okta.com/your-okta-entity-id",
  "saml_sso_url": "https://yourcompany.okta.com/app/your-app-id/sso/saml",
  "saml_x509_cert": "-----BEGIN CERTIFICATE-----\nYOUR-X509-CERT-HERE\n-----END CERTIFICATE-----",
  "saml_metadata_url": "https://yourcompany.okta.com/app/your-app-id/sso/saml/metadata",
  "attribute_mapping": {
    "email": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress",
    "first_name": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname",
    "last_name": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname",
    "display_name": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name"
  },
  "auto_provision_users": true,
  "default_role": "developer"
}
```

## Generic SAML 2.0 Provider Setup

### Step 1: LeanVibe Service Provider Configuration

**SP Entity ID:** `https://api.leanvibe.ai/v1/auth/sso/saml/metadata`
**ACS URL:** `https://api.leanvibe.ai/v1/auth/sso/saml/acs`
**Name ID Format:** `urn:oasis:names:tc:SAML:2.0:nameid-format:emailAddress`

### Step 2: Required SAML Attributes

Your identity provider must send these attributes:
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
```

### Step 3: Upload Provider Metadata

Either provide metadata URL or upload XML file:

```bash
curl -X POST "https://api.leanvibe.ai/v1/admin/sso/saml/metadata" \
  -H "Authorization: Bearer your-admin-token" \
  -H "Content-Type: application/xml" \
  --data-binary @idp-metadata.xml
```

## Multi-Factor Authentication Setup

### Enable MFA for SSO Users

```json
{
  "mfa_required": true,
  "mfa_methods": ["totp", "sms"],
  "mfa_bypass_for_sso": false,
  "backup_codes_enabled": true
}
```

### TOTP Setup Flow

1. User completes SSO authentication
2. System generates QR code for authenticator app
3. User scans QR code and enters verification code
4. System validates and enables TOTP

**API Example:**
```bash
curl -X POST "https://api.leanvibe.ai/v1/auth/mfa/setup" \
  -H "Authorization: Bearer user-token" \
  -H "Content-Type: application/json" \
  -d '{
    "method": "totp"
  }'
```

## User Provisioning & Role Management

### Automatic User Provisioning

Configure automatic user creation and role assignment:

```json
{
  "auto_provision_users": true,
  "default_role": "developer",
  "role_mapping": {
    "admin@company.com": "owner",
    "managers": "manager", 
    "developers": "developer",
    "contractors": "viewer"
  },
  "allowed_domains": ["company.com", "subsidiary.com"],
  "required_groups": ["leanvibe-users"]
}
```

### Role-Based Access Control

Supported roles and their permissions:

| Role | Users | Projects | Admin | Billing |
|------|-------|----------|-------|---------|
| **Owner** | Full | Full | Full | Full |
| **Admin** | Full | Full | Full | Read |
| **Manager** | Team | Team | Limited | None |
| **Developer** | Self | Assigned | None | None |
| **Viewer** | None | Read | None | None |

### Group Synchronization

Configure group-based role assignment:

```json
{
  "group_role_mapping": {
    "LeanVibe-Owners": "owner",
    "LeanVibe-Admins": "admin", 
    "Engineering-Leads": "manager",
    "Developers": "developer",
    "QA-Team": "viewer"
  },
  "sync_frequency": "hourly",
  "remove_users_on_group_removal": true
}
```

## Testing & Validation

### SSO Integration Test Checklist

- [ ] **Authentication Flow**: Users can log in via SSO
- [ ] **User Provisioning**: New users created automatically
- [ ] **Role Assignment**: Correct roles applied based on configuration
- [ ] **Group Sync**: Group memberships reflected in LeanVibe
- [ ] **Session Management**: SSO logout works correctly
- [ ] **MFA Integration**: Multi-factor authentication enforced
- [ ] **Error Handling**: Invalid credentials handled gracefully

### Validation Scripts

**Test SSO Configuration:**
```bash
#!/bin/bash
# Test SSO configuration
curl -X POST "https://api.leanvibe.ai/v1/auth/sso/test" \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "google",
    "test_email": "admin@yourcompany.com"
  }'
```

**Validate User Provisioning:**
```bash
#!/bin/bash
# Check user provisioning
curl -X GET "https://api.leanvibe.ai/v1/admin/users?email=newuser@company.com" \
  -H "Authorization: Bearer admin-token"
```

## Troubleshooting Common Issues

### Google SSO Issues

**Error: `redirect_uri_mismatch`**
- **Cause**: Redirect URI not configured in Google Console
- **Solution**: Add exact URI to authorized redirect URIs

**Error: `invalid_client`**
- **Cause**: Incorrect client ID or secret
- **Solution**: Verify credentials in Google Cloud Console

### Microsoft Azure Issues

**Error: `AADSTS50011`**
- **Cause**: Reply URL mismatch
- **Solution**: Ensure redirect URI matches Azure registration

**Error: `insufficient_permissions`**
- **Cause**: Missing API permissions
- **Solution**: Add required Microsoft Graph permissions

### SAML Issues

**Error: `invalid_saml_response`**
- **Cause**: SAML response validation failed
- **Solution**: Check certificate and attribute mappings

**Error: `user_not_found`**
- **Cause**: User provisioning disabled or email mismatch
- **Solution**: Enable auto-provisioning or check email attribute

### General Debugging

**Enable Debug Logging:**
```json
{
  "debug_logging": true,
  "log_level": "DEBUG",
  "mask_sensitive_data": true
}
```

**Check Authentication Logs:**
```bash
curl -X GET "https://api.leanvibe.ai/v1/admin/audit/auth" \
  -H "Authorization: Bearer admin-token" \
  -G -d "provider=google" -d "limit=50"
```

## Enterprise Support

### Implementation Assistance
- **Technical Integration Consultation**: 4-hour implementation session
- **Configuration Review**: Security and best practices validation  
- **Performance Optimization**: SSO response time optimization
- **Compliance Verification**: SOC2 and security audit support

### Ongoing Support
- **24/7 Enterprise Helpdesk**: Priority support for SSO issues
- **Quarterly Configuration Review**: Identity provider updates
- **Security Monitoring**: Anomaly detection for authentication events
- **Training Resources**: Admin and end-user training materials

### Contact Enterprise Support
- **Email**: sso-support@leanvibe.ai
- **Phone**: +1 (555) 123-4567 ext. 2
- **Slack**: #enterprise-sso in LeanVibe Community
- **Documentation**: [Enterprise SSO Knowledge Base](https://docs.leanvibe.ai/enterprise/sso)

---

**Ready to implement enterprise SSO?** Contact our integration specialists for personalized setup assistance and ensure a seamless authentication experience for your organization.