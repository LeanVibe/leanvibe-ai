# 🏢 LeanVibe Enterprise Integration Guide

> **Step-by-step integration with existing enterprise systems**

This comprehensive guide walks through integrating LeanVibe with your existing enterprise infrastructure, including identity providers, payment systems, development tools, and monitoring platforms.

## 🎯 Integration Overview

LeanVibe provides production-ready integrations with the most common enterprise systems, enabling seamless adoption without disrupting your existing workflows.

### Supported Integrations

| Category | Systems | Setup Time | Complexity |
|----------|---------|------------|------------|
| **Identity Providers** | Okta, Microsoft AD, Auth0, Google, SAML | 15-30 min | Easy |
| **Payment Processing** | Stripe, PayPal, Enterprise Invoicing | 20-45 min | Medium |
| **Development Tools** | GitHub, GitLab, Jira, Slack, Teams | 10-20 min | Easy |
| **Monitoring & Analytics** | DataDog, Splunk, New Relic, Grafana | 30-60 min | Medium |
| **Data & Storage** | AWS S3, Azure Blob, GCP Storage | 15-30 min | Easy |
| **Communication** | Slack, Microsoft Teams, Email Systems | 10-15 min | Easy |

---

## 🔐 Identity Provider Integrations

### Okta SSO Integration

**Prerequisites:**
- Okta Administrator access
- LeanVibe tenant with admin privileges
- Domain verification completed

#### Step 1: Configure Okta Application (10 minutes)

1. **Log into Okta Admin Console**
   ```bash
   # Access your Okta admin dashboard
   https://your-company.okta.com/admin
   ```

2. **Create New Application**
   - Navigate to Applications → Applications
   - Click "Create App Integration"
   - Select "OIDC - OpenID Connect"
   - Choose "Web Application"

3. **Configure Application Settings**
   ```json
   {
     "app_name": "LeanVibe Enterprise",
     "sign_in_redirect_uris": [
       "https://your-leanvibe-domain.com/auth/okta/callback",
       "http://localhost:8000/auth/okta/callback"
     ],
     "sign_out_redirect_uris": [
       "https://your-leanvibe-domain.com/auth/logout"
     ],
     "grant_types": [
       "authorization_code",
       "refresh_token"
     ],
     "assignments": {
       "controlled_access": true,
       "groups": ["LeanVibe Users", "LeanVibe Admins"]
     }
   }
   ```

4. **Note Configuration Details**
   - Client ID: `0oa123abc456def789gh`
   - Client Secret: `your-client-secret`
   - Okta Domain: `https://your-company.okta.com`

#### Step 2: Configure LeanVibe for Okta (5 minutes)

```bash
# Set up Okta integration
curl -X POST https://your-leanvibe.com/api/v1/auth/sso/providers \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {admin_token}" \
  -d '{
    "tenant_id": "your-tenant-id",
    "provider_type": "okta",
    "provider_name": "Company Okta",
    "client_id": "0oa123abc456def789gh",
    "client_secret": "your-client-secret",
    "discovery_url": "https://your-company.okta.com/.well-known/openid_configuration",
    "settings": {
      "auto_provision_users": true,
      "default_role": "user",
      "admin_groups": ["LeanVibe Admins"],
      "user_groups": ["LeanVibe Users"]
    }
  }'
```

#### Step 3: Test Integration (5 minutes)

```bash
# Test Okta SSO login flow
curl -X GET "https://your-leanvibe.com/auth/okta/login?tenant_id=your-tenant-id"

# This will redirect to Okta for authentication
# After successful login, user will be redirected back with session token
```

**✅ Okta Integration Complete!**
- Users can now log in with their corporate credentials
- User provisioning happens automatically
- Group-based role assignment is active

---

### Microsoft Azure AD Integration

#### Step 1: Register Application in Azure AD (10 minutes)

1. **Azure Portal Setup**
   ```bash
   # Navigate to Azure Active Directory
   https://portal.azure.com/#blade/Microsoft_AAD_IAM/ActiveDirectoryMenuBlade
   ```

2. **App Registration**
   - Go to "App registrations" → "New registration"
   - Name: "LeanVibe Enterprise"
   - Supported account types: "Single tenant"
   - Redirect URI: `https://your-leanvibe.com/auth/microsoft/callback`

3. **Configure API Permissions**
   ```json
   {
     "required_permissions": [
       "User.Read",
       "profile",
       "openid",
       "email"
     ],
     "optional_permissions": [
       "Group.Read.All",
       "Directory.Read.All"
     ]
   }
   ```

4. **Create Client Secret**
   - Go to "Certificates & secrets"
   - Create new client secret
   - Note: Secret value (only shown once)

#### Step 2: LeanVibe Configuration (5 minutes)

```bash
# Configure Microsoft integration
curl -X POST https://your-leanvibe.com/api/v1/auth/sso/providers \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {admin_token}" \
  -d '{
    "tenant_id": "your-tenant-id",
    "provider_type": "microsoft",
    "provider_name": "Company Azure AD",
    "client_id": "your-application-id",
    "client_secret": "your-client-secret",
    "settings": {
      "tenant_id": "your-azure-tenant-id",
      "authority": "https://login.microsoftonline.com/your-azure-tenant-id",
      "scopes": ["https://graph.microsoft.com/User.Read"],
      "auto_provision_users": true
    }
  }'
```

---

### SAML 2.0 Integration (Generic)

#### Step 1: Configure Identity Provider (15 minutes)

**For Any SAML 2.0 Provider (Ping Identity, ADFS, etc.):**

1. **Create New SAML Application**
   - Service Provider Entity ID: `https://your-leanvibe.com/saml/metadata`
   - Assertion Consumer Service (ACS) URL: `https://your-leanvibe.com/auth/saml/acs`
   - Single Logout URL: `https://your-leanvibe.com/auth/saml/sls`

2. **Configure Attribute Mapping**
   ```xml
   <saml:AttributeStatement>
     <saml:Attribute Name="email" Required="true">
       <saml:AttributeValue>user.email</saml:AttributeValue>
     </saml:Attribute>
     <saml:Attribute Name="first_name" Required="false">
       <saml:AttributeValue>user.firstName</saml:AttributeValue>
     </saml:Attribute>
     <saml:Attribute Name="last_name" Required="false">
       <saml:AttributeValue>user.lastName</saml:AttributeValue>
     </saml:Attribute>
     <saml:Attribute Name="groups" Required="false">
       <saml:AttributeValue>user.groups</saml:AttributeValue>
     </saml:Attribute>
   </saml:AttributeStatement>
   ```

#### Step 2: LeanVibe SAML Configuration (10 minutes)

```bash
# Download IdP metadata (if available)
curl -o idp_metadata.xml https://your-idp.com/metadata

# Configure SAML integration
curl -X POST https://your-leanvibe.com/api/v1/auth/sso/providers \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {admin_token}" \
  -d '{
    "tenant_id": "your-tenant-id",
    "provider_type": "saml",
    "provider_name": "Company SAML",
    "saml_metadata_url": "https://your-idp.com/metadata",
    "settings": {
      "entity_id": "https://your-leanvibe.com/saml/metadata",
      "acs_url": "https://your-leanvibe.com/auth/saml/acs",
      "sls_url": "https://your-leanvibe.com/auth/saml/sls",
      "attribute_mapping": {
        "email": "email",
        "first_name": "first_name",
        "last_name": "last_name",
        "groups": "groups"
      },
      "auto_provision_users": true,
      "admin_groups": ["LeanVibe Admins"]
    }
  }'
```

---

## 💳 Payment System Integrations

### Stripe Enterprise Integration

#### Step 1: Stripe Account Setup (10 minutes)

1. **Create Stripe Account**
   - Go to [stripe.com](https://stripe.com) and create account
   - Complete business verification
   - Enable live payments

2. **Get API Keys**
   ```bash
   # Test Keys (for development)
   STRIPE_PUBLISHABLE_KEY_TEST="pk_test_..."
   STRIPE_SECRET_KEY_TEST="sk_test_..."
   
   # Live Keys (for production)
   STRIPE_PUBLISHABLE_KEY_LIVE="pk_live_..."
   STRIPE_SECRET_KEY_LIVE="sk_live_..."
   ```

3. **Configure Webhooks**
   - Webhook URL: `https://your-leanvibe.com/api/v1/billing/webhooks/stripe`
   - Events to send:
     - `customer.subscription.created`
     - `customer.subscription.updated`
     - `customer.subscription.deleted`
     - `invoice.payment_succeeded`
     - `invoice.payment_failed`

#### Step 2: LeanVibe Stripe Configuration (15 minutes)

```bash
# Configure Stripe integration
curl -X POST https://your-leanvibe.com/api/v1/billing/configure/stripe \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {admin_token}" \
  -d '{
    "stripe_publishable_key": "pk_live_...",
    "stripe_secret_key": "sk_live_...",
    "webhook_secret": "whsec_...",
    "settings": {
      "currency": "usd",
      "tax_calculation": true,
      "automatic_tax": true,
      "payment_methods": ["card", "bank_account"],
      "invoice_settings": {
        "days_until_due": 30,
        "automatic_collection": true
      }
    }
  }'
```

#### Step 3: Create Subscription Plans (10 minutes)

```bash
# Create Developer plan
curl -X POST https://your-leanvibe.com/api/v1/billing/plans \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {admin_token}" \
  -d '{
    "name": "Developer",
    "description": "Perfect for individual developers",
    "base_price": 50.00,
    "billing_interval": "month",
    "currency": "usd",
    "features": {
      "users": 1,
      "projects": 5,
      "ai_requests_monthly": 10000,
      "storage_gb": 1,
      "support": "email"
    },
    "usage_limits": {
      "api_calls_monthly": 100000,
      "bandwidth_gb_monthly": 10
    }
  }'

# Create Team plan
curl -X POST https://your-leanvibe.com/api/v1/billing/plans \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {admin_token}" \
  -d '{
    "name": "Team",
    "description": "For growing development teams",
    "base_price": 200.00,
    "billing_interval": "month",
    "currency": "usd",
    "features": {
      "users": 10,
      "projects": 50,
      "ai_requests_monthly": 100000,
      "storage_gb": 10,
      "sso": true,
      "support": "priority"
    },
    "usage_limits": {
      "api_calls_monthly": 1000000,
      "bandwidth_gb_monthly": 100
    }
  }'

# Create Enterprise plan
curl -X POST https://your-leanvibe.com/api/v1/billing/plans \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {admin_token}" \
  -d '{
    "name": "Enterprise",
    "description": "For large organizations",
    "base_price": 800.00,
    "billing_interval": "month",
    "currency": "usd",
    "features": {
      "users": "unlimited",
      "projects": "unlimited",
      "ai_requests_monthly": 1000000,
      "storage_gb": 1000,
      "sso": true,
      "saml": true,
      "dedicated_support": true,
      "sla": "99.95%"
    },
    "usage_limits": {
      "api_calls_monthly": "unlimited",
      "bandwidth_gb_monthly": "unlimited"
    }
  }'
```

#### Step 4: Test Payment Flow (10 minutes)

```bash
# Test subscription creation
curl -X POST https://your-leanvibe.com/api/v1/billing/subscribe \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {tenant_admin_token}" \
  -d '{
    "plan_id": "team_plan_id",
    "payment_method_id": "pm_test_card_visa"
  }'

# Test usage tracking
curl -X POST https://your-leanvibe.com/api/v1/billing/usage \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {user_token}" \
  -d '{
    "metric_name": "api_calls",
    "quantity": 1000,
    "metadata": {
      "endpoint": "/api/v1/data",
      "user_id": "user_123"
    }
  }'
```

---

### Enterprise Invoicing Integration

For customers requiring purchase orders and manual invoicing:

#### Step 1: Configure Enterprise Billing (10 minutes)

```bash
# Set up enterprise billing
curl -X POST https://your-leanvibe.com/api/v1/billing/configure/enterprise \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {admin_token}" \
  -d '{
    "billing_settings": {
      "payment_terms": "NET30",
      "invoice_frequency": "monthly",
      "minimum_invoice_amount": 1000,
      "tax_calculation": true,
      "purchase_order_required": true
    },
    "invoice_template": {
      "company_name": "Your Company Inc",
      "address": "123 Enterprise Blvd, Suite 100",
      "city": "San Francisco",
      "state": "CA",
      "zip": "94105",
      "tax_id": "12-3456789"
    }
  }'
```

#### Step 2: Create Enterprise Customer (5 minutes)

```bash
# Create enterprise customer
curl -X POST https://your-leanvibe.com/api/v1/billing/enterprise/customers \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {admin_token}" \
  -d '{
    "tenant_id": "fortune-500-corp",
    "company_name": "Fortune 500 Corp",
    "billing_contact": {
      "name": "John Smith",
      "email": "billing@fortune500.com",
      "phone": "+1-555-0123"
    },
    "billing_address": {
      "street": "456 Corporate Way",
      "city": "New York",
      "state": "NY",
      "zip": "10001",
      "country": "US"
    },
    "contract_details": {
      "annual_contract_value": 120000,
      "contract_start": "2024-01-01",
      "contract_end": "2024-12-31",
      "payment_terms": "NET30"
    }
  }'
```

---

## 🔧 Development Tools Integration

### GitHub Integration

#### Step 1: GitHub App Setup (15 minutes)

1. **Create GitHub App**
   - Go to GitHub → Settings → Developer settings → GitHub Apps
   - Click "New GitHub App"
   - App name: "LeanVibe Enterprise"
   - Homepage URL: `https://your-leanvibe.com`
   - Webhook URL: `https://your-leanvibe.com/webhooks/github`

2. **Configure Permissions**
   ```json
   {
     "repository_permissions": {
       "contents": "read",
       "issues": "write",
       "pull_requests": "write",
       "metadata": "read",
       "actions": "read"
     },
     "organization_permissions": {
       "members": "read"
     },
     "user_permissions": {
       "email": "read"
     },
     "events": [
       "issues",
       "pull_request",
       "push",
       "repository",
       "installation"
     ]
   }
   ```

3. **Generate Private Key**
   - Download private key file
   - Store securely for API authentication

#### Step 2: LeanVibe GitHub Configuration (10 minutes)

```bash
# Configure GitHub integration
curl -X POST https://your-leanvibe.com/api/v1/integrations/github \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {admin_token}" \
  -d '{
    "app_id": "123456",
    "installation_id": "12345678",
    "private_key": "-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----",
    "webhook_secret": "your-webhook-secret",
    "settings": {
      "auto_create_issues": true,
      "link_ai_tasks": true,
      "status_updates": true,
      "pr_automation": {
        "auto_assign_reviewers": true,
        "require_tests": true,
        "auto_merge_conditions": {
          "tests_pass": true,
          "reviews_approved": 2
        }
      }
    }
  }'
```

#### Step 3: Test GitHub Integration (5 minutes)

```bash
# Create GitHub issue from AI task
curl -X POST https://your-leanvibe.com/api/v1/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {user_token}" \
  -d '{
    "title": "Create user profile endpoint",
    "description": "Implement CRUD operations for user profiles",
    "priority": "high",
    "github_integration": {
      "repository": "your-org/your-repo",
      "create_issue": true,
      "auto_assign": "developer-team"
    }
  }'
```

---

### Jira Integration

#### Step 1: Jira Configuration (15 minutes)

1. **Create API Token**
   - Go to Jira → Profile → Security → API tokens
   - Create token for LeanVibe integration

2. **Configure Project**
   - Project Key: `LEANVIBE`
   - Issue Types: Task, Bug, Story
   - Custom Fields for AI tasks

#### Step 2: LeanVibe Jira Setup (10 minutes)

```bash
# Configure Jira integration
curl -X POST https://your-leanvibe.com/api/v1/integrations/jira \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {admin_token}" \
  -d '{
    "jira_url": "https://your-company.atlassian.net",
    "username": "integration@yourcompany.com",
    "api_token": "your-jira-api-token",
    "project_key": "LEANVIBE",
    "settings": {
      "default_issue_type": "Task",
      "priority_mapping": {
        "low": "Lowest",
        "medium": "Medium",
        "high": "High",
        "urgent": "Highest"
      },
      "status_sync": true,
      "comment_sync": true
    }
  }'
```

---

### Slack Integration

#### Step 1: Slack App Setup (10 minutes)

1. **Create Slack App**
   - Go to [api.slack.com](https://api.slack.com/apps)
   - Create new app from manifest
   - Choose your workspace

2. **App Manifest**
   ```yaml
   display_information:
     name: LeanVibe Enterprise
     description: AI-powered development notifications
     background_color: "#4A90E2"
   features:
     bot_user:
       display_name: LeanVibe
       always_online: false
     shortcuts:
       - name: Create AI Task
         type: global
         callback_id: create_ai_task
         description: Create a new AI development task
   oauth_config:
     scopes:
       bot:
         - chat:write
         - channels:read
         - groups:read
         - im:read
         - mpim:read
   settings:
     event_subscriptions:
       request_url: https://your-leanvibe.com/webhooks/slack
       bot_events:
         - message.channels
     interactivity:
       is_enabled: true
       request_url: https://your-leanvibe.com/slack/interactive
   ```

#### Step 2: LeanVibe Slack Configuration (5 minutes)

```bash
# Configure Slack integration
curl -X POST https://your-leanvibe.com/api/v1/integrations/slack \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {admin_token}" \
  -d '{
    "bot_token": "xoxb-your-bot-token",
    "signing_secret": "your-signing-secret",
    "team_id": "T1234567890",
    "settings": {
      "notifications": {
        "task_completed": "#development",
        "deployment_status": "#deployments",
        "billing_alerts": "#finance",
        "security_alerts": "#security"
      },
      "commands": {
        "create_task": true,
        "check_status": true,
        "get_analytics": true
      }
    }
  }'
```

---

## 📊 Monitoring & Analytics Integrations

### DataDog Integration

#### Step 1: DataDog Setup (15 minutes)

1. **Create API Key**
   - DataDog → Integrations → APIs → Create API key

2. **Install DataDog Agent**
   ```bash
   # On Kubernetes cluster
   helm repo add datadog https://helm.datadoghq.com
   helm install datadog-agent datadog/datadog \
     --set datadog.apiKey=your-api-key \
     --set datadog.site=datadoghq.com \
     --set datadog.logs.enabled=true \
     --set datadog.apm.enabled=true
   ```

#### Step 2: LeanVibe DataDog Configuration (10 minutes)

```bash
# Configure DataDog metrics export
curl -X POST https://your-leanvibe.com/api/v1/integrations/datadog \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {admin_token}" \
  -d '{
    "api_key": "your-datadog-api-key",
    "app_key": "your-datadog-app-key",
    "site": "datadoghq.com",
    "settings": {
      "metrics": {
        "tenant_activity": true,
        "ai_performance": true,
        "billing_metrics": true,
        "error_rates": true
      },
      "logs": {
        "application_logs": true,
        "security_logs": true,
        "audit_logs": true
      },
      "dashboards": {
        "enterprise_overview": true,
        "tenant_analytics": true,
        "ai_productivity": true
      }
    }
  }'
```

#### Step 3: Custom Dashboards (15 minutes)

```python
# Create custom DataDog dashboard
import datadog
from datadog import initialize, api

# Initialize DataDog API
options = {
    'api_key': 'your-api-key',
    'app_key': 'your-app-key'
}
initialize(**options)

# Create LeanVibe Enterprise Dashboard
dashboard_config = {
    "title": "LeanVibe Enterprise Overview",
    "description": "Enterprise SaaS metrics and performance",
    "widgets": [
        {
            "definition": {
                "type": "timeseries",
                "requests": [
                    {
                        "q": "avg:leanvibe.active_tenants",
                        "display_type": "line"
                    }
                ],
                "title": "Active Tenants"
            }
        },
        {
            "definition": {
                "type": "query_value",
                "requests": [
                    {
                        "q": "sum:leanvibe.billing_revenue_total",
                        "aggregator": "last"
                    }
                ],
                "title": "Monthly Recurring Revenue"
            }
        },
        {
            "definition": {
                "type": "timeseries", 
                "requests": [
                    {
                        "q": "avg:leanvibe.ai_tasks_completed_per_hour",
                        "display_type": "bars"
                    }
                ],
                "title": "AI Productivity"
            }
        }
    ],
    "layout_type": "ordered"
}

dashboard = api.Dashboard.create(**dashboard_config)
print(f"Dashboard created: {dashboard['url']}")
```

---

### Splunk Integration

#### Step 1: Splunk Configuration (20 minutes)

1. **Install Universal Forwarder**
   ```bash
   # Download Splunk Universal Forwarder
   wget -O splunkforwarder.tgz "https://www.splunk.com/page/download_track?file=8.2.6/universalforwarder/linux/splunkforwarder-8.2.6-a6fe1ee8894b-Linux-x86_64.tgz"
   
   # Install on your servers
   tar -xzf splunkforwarder.tgz -C /opt/
   ```

2. **Configure Log Forwarding**
   ```bash
   # Add LeanVibe logs to inputs.conf
   cat >> /opt/splunkforwarder/etc/system/local/inputs.conf << EOF
   [monitor:///var/log/leanvibe/*.log]
   index = leanvibe
   sourcetype = leanvibe:application
   
   [monitor:///var/log/leanvibe/audit/*.log]
   index = leanvibe_audit
   sourcetype = leanvibe:audit
   
   [monitor:///var/log/leanvibe/security/*.log]
   index = leanvibe_security
   sourcetype = leanvibe:security
   EOF
   ```

#### Step 2: LeanVibe Splunk Integration (15 minutes)

```bash
# Configure Splunk HTTP Event Collector
curl -X POST https://your-leanvibe.com/api/v1/integrations/splunk \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {admin_token}" \
  -d '{
    "splunk_url": "https://your-splunk.com:8088",
    "hec_token": "your-hec-token",
    "index": "leanvibe",
    "settings": {
      "log_levels": ["INFO", "WARNING", "ERROR", "CRITICAL"],
      "event_types": [
        "user_login",
        "tenant_created",
        "billing_event",
        "ai_task_completed",
        "security_alert"
      ],
      "batch_size": 1000,
      "flush_interval": 60
    }
  }'
```

#### Step 3: Create Splunk Alerts (10 minutes)

```bash
# Create security alert
curl -X POST "https://your-splunk.com:8089/servicesNS/admin/search/saved/searches" \
  -u admin:password \
  -d "name=LeanVibe_Failed_Logins" \
  -d "search=index=leanvibe_security sourcetype=leanvibe:security \"failed login\" | stats count by user | where count > 5" \
  -d "cron_schedule=*/5 * * * *" \
  -d "actions=email" \
  -d "action.email.to=security@yourcompany.com"
```

---

## 💾 Data & Storage Integrations

### AWS S3 Integration

#### Step 1: AWS IAM Setup (10 minutes)

1. **Create IAM User**
   ```bash
   aws iam create-user --user-name leanvibe-s3-user
   ```

2. **Create Policy**
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "s3:GetObject",
           "s3:PutObject",
           "s3:DeleteObject",
           "s3:ListBucket"
         ],
         "Resource": [
           "arn:aws:s3:::leanvibe-tenant-data/*",
           "arn:aws:s3:::leanvibe-tenant-data"
         ]
       }
     ]
   }
   ```

3. **Attach Policy and Create Keys**
   ```bash
   aws iam attach-user-policy --user-name leanvibe-s3-user --policy-arn arn:aws:iam::account:policy/LeanVibeS3Policy
   aws iam create-access-key --user-name leanvibe-s3-user
   ```

#### Step 2: LeanVibe S3 Configuration (5 minutes)

```bash
# Configure S3 storage
curl -X POST https://your-leanvibe.com/api/v1/integrations/storage/s3 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {admin_token}" \
  -d '{
    "access_key_id": "AKIA...",
    "secret_access_key": "your-secret-key",
    "region": "us-west-2",
    "bucket_name": "leanvibe-tenant-data",
    "settings": {
      "tenant_isolation": true,
      "encryption": "AES256",
      "versioning": true,
      "lifecycle_rules": {
        "archive_after_days": 90,
        "delete_after_days": 2555
      }
    }
  }'
```

---

## 📧 Communication Integrations

### Email System Integration (SendGrid)

#### Step 1: SendGrid Setup (10 minutes)

1. **Create SendGrid Account**
   - Sign up at [sendgrid.com](https://sendgrid.com)
   - Verify domain
   - Create API key

2. **Domain Authentication**
   ```bash
   # Add DNS records for domain authentication
   # CNAME: em123.yourdomain.com → u123.wl.sendgrid.net
   # CNAME: s1.domainkey.yourdomain.com → s1.domainkey.u123.wl.sendgrid.net
   ```

#### Step 2: LeanVibe Email Configuration (5 minutes)

```bash
# Configure email service
curl -X POST https://your-leanvibe.com/api/v1/integrations/email/sendgrid \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {admin_token}" \
  -d '{
    "api_key": "SG.your-sendgrid-api-key",
    "from_email": "noreply@yourdomain.com",
    "from_name": "LeanVibe Platform",
    "settings": {
      "templates": {
        "welcome": "d-123456789",
        "invoice": "d-987654321",
        "password_reset": "d-555666777"
      },
      "tracking": {
        "click_tracking": true,
        "open_tracking": true,
        "subscription_tracking": true
      }
    }
  }'
```

---

## 🔄 Integration Testing & Validation

### Comprehensive Integration Test Suite

```bash
#!/bin/bash
# File: scripts/test-integrations.sh

echo "🧪 Starting Enterprise Integration Tests..."

# Test Identity Providers
echo "🔐 Testing SSO Integrations..."
curl -f "https://your-leanvibe.com/auth/okta/metadata" || echo "❌ Okta integration failed"
curl -f "https://your-leanvibe.com/auth/microsoft/metadata" || echo "❌ Microsoft integration failed"
curl -f "https://your-leanvibe.com/auth/saml/metadata" || echo "❌ SAML integration failed"

# Test Payment Processing
echo "💳 Testing Payment Integrations..."
curl -f "https://your-leanvibe.com/api/v1/billing/plans" || echo "❌ Billing system failed"

# Test Development Tools
echo "🔧 Testing Development Tool Integrations..."
curl -f "https://your-leanvibe.com/api/v1/integrations/github/status" || echo "❌ GitHub integration failed"
curl -f "https://your-leanvibe.com/api/v1/integrations/jira/status" || echo "❌ Jira integration failed"

# Test Monitoring
echo "📊 Testing Monitoring Integrations..."
curl -f "https://your-leanvibe.com/metrics" || echo "❌ Prometheus metrics failed"

# Test Storage
echo "💾 Testing Storage Integrations..."
curl -f "https://your-leanvibe.com/api/v1/integrations/storage/status" || echo "❌ Storage integration failed"

echo "✅ Integration tests complete!"
```

### Integration Health Dashboard

```python
# File: app/api/endpoints/integration_health.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
import httpx
import asyncio

router = APIRouter()

@router.get("/integrations/health")
async def get_integration_health(db: Session = Depends(get_db)):
    """Get health status of all integrations"""
    
    health_checks = await asyncio.gather(
        check_sso_health(),
        check_payment_health(),
        check_github_health(),
        check_monitoring_health(),
        check_storage_health(),
        return_exceptions=True
    )
    
    return {
        "timestamp": datetime.utcnow(),
        "overall_status": "healthy" if all(h.get("status") == "healthy" for h in health_checks if isinstance(h, dict)) else "degraded",
        "integrations": {
            "sso": health_checks[0] if not isinstance(health_checks[0], Exception) else {"status": "error", "error": str(health_checks[0])},
            "payment": health_checks[1] if not isinstance(health_checks[1], Exception) else {"status": "error", "error": str(health_checks[1])},
            "github": health_checks[2] if not isinstance(health_checks[2], Exception) else {"status": "error", "error": str(health_checks[2])},
            "monitoring": health_checks[3] if not isinstance(health_checks[3], Exception) else {"status": "error", "error": str(health_checks[3])},
            "storage": health_checks[4] if not isinstance(health_checks[4], Exception) else {"status": "error", "error": str(health_checks[4])}
        }
    }

async def check_sso_health():
    # Check if SSO endpoints are responding
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("https://your-leanvibe.com/auth/sso/providers", timeout=5)
            return {"status": "healthy", "response_time_ms": response.elapsed.total_seconds() * 1000}
    except Exception as e:
        return {"status": "error", "error": str(e)}
```

---

## 📋 Integration Checklist

### Pre-Integration Requirements
- [ ] **Administrative Access**: Ensure you have admin rights to all systems
- [ ] **Network Access**: Verify connectivity between systems
- [ ] **Security Approval**: Get security team approval for integrations
- [ ] **Backup Plan**: Have rollback procedures ready

### Post-Integration Validation
- [ ] **Authentication Flow**: Test complete login process
- [ ] **Data Sync**: Verify data flows correctly between systems
- [ ] **Error Handling**: Test failure scenarios and recovery
- [ ] **Performance**: Monitor integration performance impact
- [ ] **Security**: Validate encryption and access controls
- [ ] **Monitoring**: Set up alerts for integration health

### Ongoing Maintenance
- [ ] **Regular Health Checks**: Automated monitoring of all integrations
- [ ] **Credential Rotation**: Regular update of API keys and certificates
- [ ] **Version Updates**: Keep integration libraries up to date
- [ ] **Documentation**: Maintain current integration documentation
- [ ] **Team Training**: Ensure team knows how to troubleshoot integrations

---

## 🆘 Troubleshooting Guide

### Common Integration Issues

#### SSO Authentication Failures
**Symptoms:** Users can't log in via SSO
**Solutions:**
1. Check IdP certificate expiration
2. Verify redirect URLs are correct
3. Validate attribute mappings
4. Check network connectivity

```bash
# Debug SSO issues
curl -v "https://your-leanvibe.com/auth/sso/debug?provider=okta&tenant_id=your-tenant"
```

#### Payment Processing Errors
**Symptoms:** Subscription creation fails
**Solutions:**
1. Verify Stripe webhook configuration
2. Check API key validity
3. Validate customer data format
4. Review Stripe dashboard logs

```bash
# Test Stripe connectivity
curl -u sk_test_...: "https://api.stripe.com/v1/customers" -d "email=test@example.com"
```

#### GitHub Integration Issues
**Symptoms:** AI tasks not creating GitHub issues
**Solutions:**
1. Check GitHub App permissions
2. Verify installation on repositories
3. Validate webhook secret
4. Review GitHub App logs

```bash
# Test GitHub integration
curl -H "Authorization: Bearer {github_token}" "https://api.github.com/user"
```

### Emergency Contacts

| Integration | Support Contact | Response Time |
|------------|-----------------|---------------|
| **Okta** | support@okta.com | 4 hours |
| **Microsoft** | Azure Support Portal | 2 hours |
| **Stripe** | support@stripe.com | 1 hour |
| **GitHub** | support@github.com | 24 hours |
| **DataDog** | support@datadoghq.com | 2 hours |

---

## 🏆 Integration Success Metrics

### Key Performance Indicators
- **SSO Adoption Rate**: % of users using SSO vs local accounts
- **Payment Success Rate**: % of successful payment transactions  
- **GitHub Integration Usage**: Number of AI tasks linked to GitHub issues
- **Monitoring Coverage**: % of system metrics being monitored
- **Integration Uptime**: Availability of integration endpoints

### Success Targets
- SSO Adoption Rate: >80%
- Payment Success Rate: >99%
- GitHub Integration Usage: >70% of tasks
- Monitoring Coverage: >95%
- Integration Uptime: >99.9%

---

**🎉 Congratulations! Your enterprise systems are now seamlessly integrated with LeanVibe.**

Your organization can now leverage the full power of the LeanVibe enterprise platform while maintaining your existing workflows and security requirements.

For additional support with enterprise integrations, contact our enterprise team at **enterprise-integrations@leanvibe.ai**