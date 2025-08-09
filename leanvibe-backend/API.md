# LeanVibe Enterprise API Documentation

## Executive Overview

The LeanVibe Enterprise API provides comprehensive programmatic access to all platform capabilities including multi-tenant management, enterprise authentication, sophisticated billing operations, and autonomous AI development features. Designed for enterprise integration with robust security, extensive functionality, and production-grade reliability.

**Base URL**: `https://api.leanvibe.ai/v1`  
**Authentication**: Bearer Token (JWT)  
**Rate Limits**: 100/1,000/10,000 requests per minute (by subscription tier)  
**SLA**: 99.95% uptime for Enterprise customers

## 🏢 Enterprise Features Overview

### Multi-Tenant Architecture
- **Complete tenant isolation** with row-level security
- **Hierarchical organizations** for enterprise customer structures
- **Resource quotas and monitoring** with real-time usage tracking
- **GDPR-compliant data residency** across 5 global regions

### Enterprise Authentication & Security
- **Single Sign-On (SSO)** with Google, Microsoft, Okta, SAML 2.0
- **Multi-Factor Authentication** (TOTP, SMS, Email, Hardware keys)
- **Role-Based Access Control** with 6 enterprise roles
- **Comprehensive audit logging** for compliance requirements

### Billing & Subscription Management
- **Stripe integration** with enterprise invoicing and tax compliance
- **Usage-based metered billing** with real-time tracking
- **Multi-tier subscriptions**: Developer ($50), Team ($200), Enterprise ($800)
- **Revenue analytics**: MRR/ARR tracking and forecasting

## 🔐 Authentication System

### JWT Token Authentication

All API requests require a valid JWT token in the Authorization header:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Multi-Provider Login

**Endpoint**: `POST /api/v1/auth/login`

```bash
# Local authentication
curl -X POST "https://api.leanvibe.ai/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@company.com",
    "password": "secure_password",
    "provider": "local"
  }'
```

**Response**:
```json
{
  "success": true,
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 3600,
  "user": {
    "id": "user-uuid",
    "email": "admin@company.com",
    "role": "owner",
    "tenant_id": "tenant-uuid"
  }
}
```

#### SSO Authentication

**Google OAuth2**:
```bash
curl -X GET "https://api.leanvibe.ai/v1/auth/sso/google" \
  -H "X-Tenant-Slug: company"
# Returns redirect URL for OAuth flow
```

**Microsoft Azure AD**:
```bash
curl -X GET "https://api.leanvibe.ai/v1/auth/sso/microsoft" \
  -H "X-Tenant-Slug: company"
```

**SAML 2.0**:
```bash
curl -X POST "https://api.leanvibe.ai/v1/auth/saml/sso" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "SAMLResponse=base64_encoded_response&RelayState=optional_state"
```

### Multi-Factor Authentication (MFA)

#### Setup TOTP MFA
```bash
curl -X POST "https://api.leanvibe.ai/v1/auth/mfa/setup" \
  -H "Authorization: Bearer access_token" \
  -H "Content-Type: application/json" \
  -d '{"method": "totp"}'
```

**Response**:
```json
{
  "method": "totp",
  "secret": "JBSWY3DPEHPK3PXP",
  "qr_code": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
  "backup_codes": [
    "12345678", "23456789", "34567890", "45678901",
    "56789012", "67890123", "78901234", "89012345"
  ]
}
```

#### Verify MFA
```bash
curl -X POST "https://api.leanvibe.ai/v1/auth/mfa/verify" \
  -H "Authorization: Bearer access_token" \
  -H "Content-Type: application/json" \
  -d '{"code": "123456", "method": "totp"}'
```

### Token Management

#### Refresh Token
```bash
curl -X POST "https://api.leanvibe.ai/v1/auth/refresh" \
  -H "Authorization: Bearer refresh_token"
```

#### Logout
```bash
curl -X POST "https://api.leanvibe.ai/v1/auth/logout" \
  -H "Authorization: Bearer access_token"
```

## 🏢 Multi-Tenant Management API

### Tenant Operations

#### Create New Tenant (Admin Only)
```bash
curl -X POST "https://api.leanvibe.ai/v1/tenants" \
  -H "Authorization: Bearer admin_token" \
  -H "Content-Type: application/json" \
  -d '{
    "organization_name": "Enterprise Corp",
    "slug": "enterprise-corp",
    "admin_email": "admin@enterprise-corp.com",
    "plan": "enterprise",
    "data_residency": "us"
  }'
```

#### Get Current Tenant Information
```bash
curl -X GET "https://api.leanvibe.ai/v1/tenants/me/info" \
  -H "Authorization: Bearer tenant_token"
```

**Response**:
```json
{
  "id": "tenant-uuid",
  "organization_name": "Enterprise Corp",
  "slug": "enterprise-corp", 
  "status": "active",
  "plan": "enterprise",
  "data_residency": "us",
  "quotas": {
    "max_users": 999999,
    "max_projects": 999999,
    "max_api_calls_per_month": 999999999,
    "max_storage_mb": 1048576,
    "max_ai_requests_per_day": 10000,
    "max_concurrent_sessions": 100
  },
  "current_usage": {
    "users_count": 45,
    "projects_count": 23,
    "api_calls_this_month": 85000,
    "storage_used_mb": 8500,
    "ai_requests_today": 750,
    "concurrent_sessions": 12
  },
  "created_at": "2024-01-01T00:00:00Z",
  "trial_ends_at": null
}
```

#### Update Tenant Configuration
```bash
curl -X PUT "https://api.leanvibe.ai/v1/tenants/me/info" \
  -H "Authorization: Bearer tenant_admin_token" \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "Enterprise Corp - Updated",
    "configuration": {
      "branding": {
        "primary_color": "#1f2937",
        "logo_url": "https://cdn.enterprise-corp.com/logo.png"
      },
      "features": {
        "advanced_ai_features": true,
        "custom_workflows": true
      }
    }
  }'
```

### Resource Usage & Quotas

#### Get Current Usage
```bash
curl -X GET "https://api.leanvibe.ai/v1/tenants/me/usage" \
  -H "Authorization: Bearer tenant_token"
```

#### Check Quota Availability
```bash
curl -X GET "https://api.leanvibe.ai/v1/tenants/me/quota-check/api_calls?amount=100" \
  -H "Authorization: Bearer tenant_token"
```

**Response**:
```json
{
  "quota_type": "api_calls",
  "available": true,
  "current_usage": 85000,
  "quota_limit": 999999999,
  "requested_amount": 100,
  "remaining": 999914999
}
```

### Tenant Administration

#### List All Tenants (Platform Admin)
```bash
curl -X GET "https://api.leanvibe.ai/v1/tenants?status=active&plan=enterprise&limit=50" \
  -H "Authorization: Bearer platform_admin_token"
```

#### Suspend Tenant (Platform Admin)
```bash
curl -X POST "https://api.leanvibe.ai/v1/tenants/{tenant_id}/suspend" \
  -H "Authorization: Bearer platform_admin_token" \
  -H "Content-Type: application/json" \
  -d '{"reason": "Payment overdue"}'
```

#### Reactivate Tenant (Platform Admin)
```bash
curl -X POST "https://api.leanvibe.ai/v1/tenants/{tenant_id}/reactivate" \
  -H "Authorization: Bearer platform_admin_token"
```

## 💰 Billing & Subscription Management API

### Subscription Plans

#### List Available Plans
```bash
curl -X GET "https://api.leanvibe.ai/v1/billing/plans" \
  -H "Authorization: Bearer token"
```

**Response**:
```json
[
  {
    "id": "plan-uuid-developer",
    "name": "Developer",
    "slug": "developer",
    "base_price": 5000,
    "currency": "USD",
    "billing_interval": "monthly",
    "features": {
      "max_users": 1,
      "max_projects": 5,
      "ai_requests_per_day": 100,
      "storage_gb": 1,
      "email_support": true,
      "api_access": true
    },
    "trial_period_days": 14
  },
  {
    "id": "plan-uuid-team",
    "name": "Team",
    "slug": "team", 
    "base_price": 20000,
    "currency": "USD",
    "billing_interval": "monthly",
    "features": {
      "max_users": 10,
      "max_projects": 50,
      "ai_requests_per_day": 1000,
      "storage_gb": 10,
      "sso_support": true,
      "chat_support": true
    },
    "trial_period_days": 14
  },
  {
    "id": "plan-uuid-enterprise",
    "name": "Enterprise",
    "slug": "enterprise",
    "base_price": 80000,
    "currency": "USD",
    "billing_interval": "monthly",
    "is_enterprise": true,
    "features": {
      "max_users": 999999,
      "max_projects": 999999,
      "ai_requests_per_day": 10000,
      "storage_gb": 1000,
      "saml_support": true,
      "dedicated_support": true,
      "sla_guarantee": true
    },
    "trial_period_days": 30
  }
]
```

### Subscription Operations

#### Create Subscription
```bash
curl -X POST "https://api.leanvibe.ai/v1/billing/subscription" \
  -H "Authorization: Bearer tenant_admin_token" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "tenant-uuid",
    "plan_id": "plan-uuid-enterprise",
    "payment_method_id": "pm_stripe_payment_method_id",
    "trial_period_days": 30
  }'
```

#### Get Current Subscription
```bash
curl -X GET "https://api.leanvibe.ai/v1/billing/subscription" \
  -H "Authorization: Bearer tenant_admin_token"
```

#### Update Subscription
```bash
curl -X PATCH "https://api.leanvibe.ai/v1/billing/subscription" \
  -H "Authorization: Bearer tenant_admin_token" \
  -H "Content-Type: application/json" \
  -d '{
    "plan_id": "new-plan-uuid",
    "cancel_at_period_end": false
  }'
```

#### Cancel Subscription
```bash
curl -X DELETE "https://api.leanvibe.ai/v1/billing/subscription?immediately=false" \
  -H "Authorization: Bearer tenant_admin_token"
```

**Response**:
```json
{
  "message": "Subscription will cancel at period end",
  "subscription_id": "subscription-uuid",
  "cancelled_at": null
}
```

### Usage-Based Billing

#### Record Usage Event
```bash
curl -X POST "https://api.leanvibe.ai/v1/billing/usage" \
  -H "Authorization: Bearer api_token" \
  -H "Content-Type: application/json" \
  -d '{
    "metric_type": "api_calls",
    "quantity": 100
  }'
```

#### Get Usage Summary
```bash
curl -X GET "https://api.leanvibe.ai/v1/billing/usage" \
  -H "Authorization: Bearer tenant_admin_token"
```

**Response**:
```json
{
  "subscription_id": "subscription-uuid",
  "billing_period": {
    "start": "2025-01-01T00:00:00Z",
    "end": "2025-01-31T23:59:59Z"
  },
  "usage_metrics": {
    "api_calls": 85000,
    "storage_gb": 8.5,
    "ai_requests": 750,
    "active_users": 12
  },
  "projected_cost": 200.00,
  "currency": "USD"
}
```

### Analytics & Reporting

#### Get Billing Analytics
```bash
curl -X GET "https://api.leanvibe.ai/v1/billing/analytics" \
  -H "Authorization: Bearer tenant_admin_token"
```

**Response**:
```json
{
  "tenant_id": "tenant-uuid",
  "monthly_recurring_revenue": 80000,
  "annual_recurring_revenue": 960000,
  "usage_metrics": {
    "api_calls": 85000,
    "storage_gb": 8,
    "ai_requests": 750,
    "active_users": 12
  },
  "usage_trends": {
    "api_calls": [75000, 82000, 85000],
    "ai_requests": [650, 700, 750]
  },
  "payment_health_score": 0.98,
  "projected_monthly_cost": 80000,
  "calculated_at": "2025-01-09T10:30:00Z"
}
```

### Payment Methods

#### Add Payment Method
```bash
curl -X POST "https://api.leanvibe.ai/v1/billing/payment-methods" \
  -H "Authorization: Bearer tenant_admin_token" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "card",
    "card_token": "stripe_card_token"
  }'
```

#### List Payment Methods
```bash
curl -X GET "https://api.leanvibe.ai/v1/billing/payment-methods" \
  -H "Authorization: Bearer tenant_admin_token"
```

### Invoice Management

#### Get Invoice Details
```bash
curl -X GET "https://api.leanvibe.ai/v1/billing/invoice/{invoice_id}" \
  -H "Authorization: Bearer tenant_admin_token"
```

**Response**:
```json
{
  "id": "invoice-uuid",
  "status": "paid",
  "total": 5000,
  "currency": "USD",
  "issue_date": "2025-01-01T00:00:00Z",
  "due_date": "2025-01-15T00:00:00Z",
  "paid_at": "2025-01-05T10:30:00Z",
  "pdf_url": "https://api.leanvibe.ai/v1/billing/invoice/{invoice_id}/pdf"
}
```

#### List Invoices
```bash
curl -X GET "https://api.leanvibe.ai/v1/billing/invoices?limit=10&offset=0" \
  -H "Authorization: Bearer tenant_admin_token"
```

### Webhook Integration

#### Stripe Webhooks
```bash
# Webhook endpoint for Stripe events
POST /api/v1/billing/webhooks/stripe

# Headers required:
Stripe-Signature: t=timestamp,v1=signature

# Supported events:
# - customer.subscription.created
# - customer.subscription.updated
# - customer.subscription.deleted
# - invoice.payment_succeeded
# - invoice.payment_failed
```

## 🤖 Autonomous AI Development API

### L3 AI Agent Operations

#### Submit Development Task
```bash
curl -X POST "https://api.leanvibe.ai/v1/tasks" \
  -H "Authorization: Bearer developer_token" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "project-uuid",
    "title": "Implement user authentication API",
    "description": "Create REST endpoints for user registration, login, and password reset with JWT token support",
    "priority": "high",
    "estimated_complexity": "medium",
    "requirements": {
      "frameworks": ["FastAPI", "SQLAlchemy"],
      "security_requirements": ["JWT", "bcrypt", "rate_limiting"],
      "testing_requirements": ["unit_tests", "integration_tests"]
    }
  }'
```

**Response**:
```json
{
  "id": "task-uuid",
  "status": "queued",
  "project_id": "project-uuid",
  "title": "Implement user authentication API",
  "estimated_duration_minutes": 120,
  "assigned_agent": "l3-agent-001",
  "created_at": "2025-01-09T10:30:00Z",
  "tracking_url": "https://app.leanvibe.ai/tasks/task-uuid"
}
```

#### Get Task Status
```bash
curl -X GET "https://api.leanvibe.ai/v1/tasks/{task_id}" \
  -H "Authorization: Bearer developer_token"
```

**Response**:
```json
{
  "id": "task-uuid",
  "status": "in_progress",
  "progress_percentage": 65,
  "current_step": "Writing unit tests",
  "estimated_completion": "2025-01-09T12:45:00Z",
  "deliverables": {
    "files_created": 8,
    "tests_written": 12,
    "api_endpoints": 4
  },
  "real_time_updates": {
    "websocket_url": "wss://api.leanvibe.ai/v1/tasks/task-uuid/updates"
  }
}
```

### Project Management

#### Create Project
```bash
curl -X POST "https://api.leanvibe.ai/v1/projects" \
  -H "Authorization: Bearer developer_token" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "E-commerce Platform",
    "description": "Modern e-commerce platform with AI recommendations",
    "tech_stack": ["Python", "FastAPI", "React", "PostgreSQL"],
    "repository_url": "https://github.com/company/ecommerce-platform",
    "ai_assistance_level": "full_autonomous"
  }'
```

#### Get Project Details
```bash
curl -X GET "https://api.leanvibe.ai/v1/projects/{project_id}" \
  -H "Authorization: Bearer developer_token"
```

#### Update Project Configuration
```bash
curl -X PATCH "https://api.leanvibe.ai/v1/projects/{project_id}" \
  -H "Authorization: Bearer developer_token" \
  -H "Content-Type: application/json" \
  -d '{
    "ai_assistance_level": "assisted",
    "auto_deployment": true,
    "quality_gates": {
      "require_tests": true,
      "min_test_coverage": 80,
      "security_scan": true
    }
  }'
```

### Code Analysis and Generation

#### Analyze Codebase
```bash
curl -X POST "https://api.leanvibe.ai/v1/projects/{project_id}/analyze" \
  -H "Authorization: Bearer developer_token" \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_type": "comprehensive",
    "include_metrics": ["complexity", "security", "performance", "maintainability"]
  }'
```

#### Direct Code Generation
```bash
curl -X POST "https://api.leanvibe.ai/v1/code/generate" \
  -H "Authorization: Bearer developer_token" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "project-uuid",
    "component_type": "api_endpoint",
    "specification": {
      "endpoint": "/api/users",
      "methods": ["GET", "POST"],
      "authentication": "jwt",
      "validation": "pydantic",
      "database": "sqlalchemy"
    }
  }'
```

**Response**:
```json
{
  "status": "success",
  "response": "from fastapi import APIRouter, Depends\nfrom sqlalchemy.orm import Session\n...",
  "confidence": 0.95,
  "requires_review": false,
  "processing_time_ms": 340
}
```

### Real-Time Monitoring

#### WebSocket Connection for Task Updates
```javascript
// JavaScript WebSocket client
const ws = new WebSocket('wss://api.leanvibe.ai/v1/tasks/task-uuid/updates');

ws.onmessage = function(event) {
    const update = JSON.parse(event.data);
    console.log('Task Update:', update);
    
    switch(update.type) {
        case 'progress':
            updateProgressBar(update.percentage);
            break;
        case 'completion':
            showCompletionNotification(update.deliverables);
            break;
        case 'error':
            handleError(update.error);
            break;
    }
};
```

## 🔍 Health Monitoring & System Status

### Platform Health Check

#### Comprehensive Health Status
```bash
curl -X GET "https://api.leanvibe.ai/v1/health" \
  -H "Authorization: Bearer token"
```

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-09T10:30:00Z",
  "services": {
    "api": {"status": "healthy", "response_time_ms": 45},
    "database": {"status": "healthy", "connection_pool": "optimal"},
    "cache": {"status": "healthy", "hit_rate": 94.5},
    "ai_services": {"status": "healthy", "queue_depth": 3},
    "billing": {"status": "healthy", "stripe_connectivity": "good"}
  },
  "metrics": {
    "requests_per_minute": 8500,
    "average_response_time": 120,
    "error_rate": 0.02,
    "uptime_percentage": 99.97
  }
}
```

#### AI Service Health
```bash
curl -X GET "https://api.leanvibe.ai/v1/health/mlx" \
  -H "Authorization: Bearer token"
```

**Response**:
```json
{
  "status": "healthy",
  "model": "phi3-mini-4k-instruct",
  "model_loaded": true,
  "inference_ready": true,
  "confidence_score": 0.95,
  "performance": {
    "last_inference_time_ms": 340,
    "average_tokens_per_second": 45.2,
    "memory_efficiency": "good"
  }
}
```

#### Tenant-Specific Health
```bash
curl -X GET "https://api.leanvibe.ai/v1/health/tenant/{tenant_id}" \
  -H "Authorization: Bearer tenant_admin_token"
```

### Billing Service Health

```bash
curl -X GET "https://api.leanvibe.ai/v1/billing/health" \
  -H "Authorization: Bearer token"
```

**Response**:
```json
{
  "status": "healthy",
  "service": "billing",
  "timestamp": "2025-01-09T10:30:00Z",
  "plans_available": 3
}
```

## 🔌 Integration & Webhooks

### Webhook Configuration

#### Configure Enterprise Webhooks
```bash
curl -X POST "https://api.leanvibe.ai/v1/admin/webhooks" \
  -H "Authorization: Bearer admin_token" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-app.com/webhooks/leanvibe",
    "events": [
      "task.completed",
      "billing.payment_succeeded",
      "user.created",
      "tenant.quota_exceeded"
    ],
    "secret": "your_webhook_secret"
  }'
```

#### Webhook Event Types

**Authentication Events**:
- `user.created` - New user registered
- `user.login` - User authentication event
- `user.logout` - User session terminated
- `mfa.enabled` - Multi-factor authentication enabled

**Task & Development Events**:
- `task.created` - New AI development task submitted
- `task.in_progress` - Task processing started
- `task.completed` - Task completed successfully
- `task.failed` - Task execution failed
- `project.created` - New project created

**Billing Events**:
- `subscription.created` - New subscription activated
- `subscription.updated` - Subscription plan changed
- `subscription.cancelled` - Subscription cancelled
- `invoice.paid` - Invoice payment succeeded
- `payment.failed` - Payment processing failed

**System Events**:
- `tenant.quota_warning` - Usage approaching quota limits (90%)
- `tenant.quota_exceeded` - Quota limit exceeded
- `tenant.suspended` - Tenant account suspended
- `maintenance.scheduled` - Scheduled maintenance notification

#### Webhook Payload Example

```json
{
  "event_type": "task.completed",
  "tenant_id": "tenant-uuid",
  "timestamp": "2025-01-09T10:30:00Z",
  "data": {
    "task_id": "task-uuid",
    "project_id": "project-uuid",
    "status": "completed",
    "deliverables": {
      "files_created": 12,
      "tests_written": 8,
      "api_endpoints": 4
    },
    "github_pr_url": "https://github.com/org/repo/pull/123"
  },
  "signature": "sha256=calculated_signature"
}
```

### Enterprise SDKs

#### Official SDK Support

**Python SDK**:
```bash
pip install leanvibe-enterprise-sdk
```

```python
from leanvibe import LeanVibeClient

client = LeanVibeClient(
    api_key="your_api_key",
    base_url="https://api.leanvibe.ai/v1"
)

# Create a development task
task = client.tasks.create(
    project_id="project-uuid",
    title="Implement payment processing",
    requirements={
        "security": ["PCI_DSS", "encryption"],
        "testing": ["unit_tests", "integration_tests"]
    }
)

print(f"Task created: {task.id}")
```

**Node.js SDK**:
```bash
npm install @leanvibe/enterprise-sdk
```

```javascript
import { LeanVibeClient } from '@leanvibe/enterprise-sdk';

const client = new LeanVibeClient({
    apiKey: 'your_api_key',
    baseURL: 'https://api.leanvibe.ai/v1'
});

// Monitor task progress
const task = await client.tasks.get('task-uuid');
console.log(`Progress: ${task.progress_percentage}%`);
```

### CI/CD Pipeline Integration

#### GitHub Actions Integration

```yaml
# .github/workflows/leanvibe-ai-development.yml
name: LeanVibe Autonomous Development
on:
  issues:
    types: [opened, labeled]

jobs:
  create_task:
    runs-on: ubuntu-latest
    if: contains(github.event.issue.labels.*.name, 'ai-task')
    steps:
      - name: Create LeanVibe Task
        run: |
          curl -X POST "https://api.leanvibe.ai/v1/tasks" \
            -H "Authorization: Bearer ${{ secrets.LEANVIBE_API_KEY }}" \
            -H "Content-Type: application/json" \
            -d '{
              "project_id": "${{ secrets.PROJECT_ID }}",
              "title": "${{ github.event.issue.title }}",
              "description": "${{ github.event.issue.body }}",
              "github_issue": ${{ github.event.issue.number }}
            }'
```

#### Slack Bot Integration

```javascript
// Slack bot command handler
app.command('/leanvibe-task', async ({ command, ack, respond }) => {
  await ack();
  
  const task = await leanvibeClient.tasks.create({
    project_id: process.env.PROJECT_ID,
    title: command.text,
    requestor: command.user_name
  });
  
  await respond({
    text: `Task created: ${task.id}`,
    blocks: [
      {
        type: "section",
        text: {
          type: "mrkdwn",
          text: `*Task:* ${task.title}\n*Status:* ${task.status}\n*Tracking:* ${task.tracking_url}`
        }
      }
    ]
  });
});
```

## ⚡ Rate Limiting & Quotas

### Plan-Based Rate Limits

All API responses include rate limiting information in headers:

```http
X-RateLimit-Limit: 10000
X-RateLimit-Remaining: 9847
X-RateLimit-Reset: 1642262400
X-RateLimit-Retry-After: 3600
```

### Subscription Tier Limits

| Plan | Requests/Minute | Requests/Month | AI Requests/Day | Concurrent Sessions |
|------|----------------|----------------|----------------|--------------------|
| **Developer** | 100 | 10,000 | 100 | 2 |
| **Team** | 1,000 | 100,000 | 1,000 | 10 |
| **Enterprise** | 10,000 | Unlimited | 10,000 | 100 |

### Quota Exceeded Response

```json
{
  "error": "quota_exceeded",
  "message": "Monthly API quota exceeded",
  "details": {
    "quota_type": "api_calls",
    "current_usage": 100000,
    "quota_limit": 100000,
    "reset_date": "2025-02-01T00:00:00Z"
  },
  "upgrade_options": [
    {
      "plan": "enterprise",
      "monthly_price": 80000,
      "benefits": ["Unlimited API calls", "Priority support"]
    }
  ]
}
```

## ⚠️ Error Handling

### Standard Error Response Format

```json
{
  "error": "error_code",
  "message": "Human-readable error message",
  "details": {
    "field": "specific_field_with_error",
    "validation_errors": ["Field is required"]
  },
  "request_id": "req_uuid_for_tracking",
  "timestamp": "2025-01-09T10:30:00Z"
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `invalid_request` | 400 | Malformed request |
| `unauthorized` | 401 | Invalid or missing authentication |
| `forbidden` | 403 | Insufficient permissions |
| `not_found` | 404 | Resource not found |
| `quota_exceeded` | 429 | Rate or usage limit exceeded |
| `server_error` | 500 | Internal server error |
| `service_unavailable` | 503 | Service temporarily unavailable |
| `tenant_suspended` | 451 | Tenant account suspended |
| `payment_required` | 402 | Subscription payment required |

## 📊 Enterprise Analytics & Reporting

### Revenue Analytics (Platform Admin)
```bash
curl -X GET "https://api.leanvibe.ai/v1/admin/analytics/revenue" \
  -H "Authorization: Bearer platform_admin_token" \
  -G -d "period=monthly" -d "start_date=2024-01-01" -d "end_date=2024-12-31"
```

**Response**:
```json
{
  "period": "monthly",
  "metrics": {
    "total_revenue": 2450000,
    "recurring_revenue": 2200000,
    "one_time_revenue": 250000,
    "revenue_growth_rate": 15.5,
    "customer_acquisition_cost": 150,
    "lifetime_value": 2400
  },
  "monthly_breakdown": [
    {
      "month": "2024-01",
      "revenue": 185000,
      "new_customers": 23,
      "churned_customers": 2,
      "expansion_revenue": 15000
    }
  ]
}
```

### Usage Analytics
```bash
curl -X GET "https://api.leanvibe.ai/v1/admin/analytics/usage" \
  -H "Authorization: Bearer platform_admin_token" \
  -G -d "tenant_id=all" -d "period=30d" -d "metrics=api_calls,ai_requests,storage"
```

### Audit Logging

#### Authentication Audit Log
```bash
curl -X GET "https://api.leanvibe.ai/v1/admin/audit/auth" \
  -H "Authorization: Bearer admin_token" \
  -G -d "tenant_id=tenant-uuid" -d "start_date=2024-01-01" -d "limit=100"
```

#### Billing Audit Log
```bash
curl -X GET "https://api.leanvibe.ai/v1/admin/audit/billing" \
  -H "Authorization: Bearer admin_token" \
  -G -d "tenant_id=tenant-uuid" -d "event_type=subscription_updated"
```

## 🏗️ Enterprise Integration Examples

### Jira Integration

```python
# Jira webhook handler
@app.route('/webhooks/jira', methods=['POST'])
def jira_webhook():
    event = request.json
    
    if event['issue_event_type_name'] == 'issue_created':
        issue = event['issue']
        
        # Create LeanVibe task from Jira issue
        task = leanvibe_client.tasks.create(
            project_id=PROJECT_ID,
            title=issue['fields']['summary'],
            description=issue['fields']['description'],
            priority=issue['fields']['priority']['name'].lower(),
            jira_key=issue['key']
        )
        
        # Update Jira with LeanVibe task link
        jira.add_comment(
            issue['key'],
            f"LeanVibe autonomous development task created: {task.tracking_url}"
        )
    
    return {'status': 'success'}
```

### Microsoft Teams Integration

```javascript
// Teams bot integration
app.message('/leanvibe', async (context) => {
    const task = await leanvibeClient.tasks.create({
        project_id: process.env.PROJECT_ID,
        title: context.activity.text,
        requestor: context.activity.from.name
    });
    
    await context.sendActivity(MessageFactory.text(
        `Task created: ${task.title}\nStatus: ${task.status}\nTracking: ${task.tracking_url}`
    ));
});
```

## 🎯 Getting Started

### Enterprise Evaluation Process

1. **Request Enterprise API Access**
   - Email: enterprise@leanvibe.ai
   - Phone: +1 (555) 123-4567
   - Schedule demo: [Enterprise Demo](https://calendly.com/leanvibe-enterprise)

2. **API Credentials Setup**
   - Access enterprise admin panel
   - Generate API keys with appropriate scopes
   - Configure SSO and multi-tenant settings

3. **Integration Testing**
   - Use sandbox environment for initial testing
   - Test authentication and authorization flows
   - Validate webhook integrations

4. **Production Deployment**
   - Enterprise onboarding with dedicated support
   - Custom integration assistance
   - Performance optimization and monitoring setup

### Support Channels

- **Enterprise API Support**: api-support@leanvibe.ai
- **Integration Consulting**: integrations@leanvibe.ai
- **Technical Documentation**: [docs.leanvibe.ai](https://docs.leanvibe.ai/api)
- **Status Page**: [status.leanvibe.ai](https://status.leanvibe.ai)
- **Developer Community**: [community.leanvibe.ai](https://community.leanvibe.ai)

### Enterprise SLA

- **99.95% Uptime Guarantee** for Enterprise tier customers
- **2-Hour Response Time** for critical issues
- **Dedicated Customer Success Manager** for strategic guidance
- **24/7 Technical Support** with escalation procedures
- **Quarterly Business Reviews** with platform optimization

---

**🚀 Ready to integrate with LeanVibe Enterprise APIs?** 

Contact our enterprise team for personalized integration assistance and accelerated deployment support.

*LeanVibe Enterprise API - Powering the future of autonomous development.*