# LeanVibe Enterprise API Documentation

## Overview

The LeanVibe Enterprise API provides comprehensive programmatic access to all platform features including authentication, tenant management, billing operations, and autonomous development capabilities. Built with enterprise requirements in mind, the API supports high-volume usage, complex integrations, and sophisticated workflow automation.

**Base URL:** `https://api.leanvibe.ai/v1`
**Authentication:** Bearer Token (JWT)
**Rate Limits:** Up to 10,000 requests/minute (Enterprise tier)

## Authentication System

### JWT Token Authentication

All API requests require a valid JWT token in the Authorization header:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Login and Token Generation

**Endpoint:** `POST /auth/login`

```bash
curl -X POST "https://api.leanvibe.ai/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@company.com",
    "password": "secure_password",
    "provider": "local"
  }'
```

**Response:**
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

### SSO Authentication

#### Google OAuth2 Login
```bash
curl -X POST "https://api.leanvibe.ai/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@company.com",
    "provider": "google",
    "auth_code": "google_oauth_authorization_code"
  }'
```

#### Microsoft Azure AD Login
```bash
curl -X POST "https://api.leanvibe.ai/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@company.com",
    "provider": "microsoft",
    "auth_code": "azure_oauth_authorization_code"
  }'
```

#### SAML Authentication
```bash
curl -X POST "https://api.leanvibe.ai/v1/auth/saml/acs" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d 'SAMLResponse=base64_encoded_saml_response&RelayState=optional_relay_state'
```

### Multi-Factor Authentication (MFA)

#### Setup TOTP MFA
```bash
curl -X POST "https://api.leanvibe.ai/v1/auth/mfa/setup" \
  -H "Authorization: Bearer access_token" \
  -H "Content-Type: application/json" \
  -d '{
    "method": "totp"
  }'
```

**Response:**
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

#### Verify MFA During Login
```bash
curl -X POST "https://api.leanvibe.ai/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@company.com",
    "password": "password",
    "mfa_code": "123456",
    "mfa_method": "totp"
  }'
```

### Token Management

#### Refresh Access Token
```bash
curl -X POST "https://api.leanvibe.ai/v1/auth/refresh" \
  -H "Authorization: Bearer refresh_token"
```

#### Revoke Token (Logout)
```bash
curl -X POST "https://api.leanvibe.ai/v1/auth/logout" \
  -H "Authorization: Bearer access_token"
```

## Tenant Management API

### Tenant Operations

#### Create New Tenant
```bash
curl -X POST "https://api.leanvibe.ai/v1/admin/tenants" \
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

#### Get Tenant Details
```bash
curl -X GET "https://api.leanvibe.ai/v1/tenants/{tenant_id}" \
  -H "Authorization: Bearer tenant_admin_token"
```

**Response:**
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
curl -X PATCH "https://api.leanvibe.ai/v1/tenants/{tenant_id}" \
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

### User Management

#### Create User
```bash
curl -X POST "https://api.leanvibe.ai/v1/tenants/{tenant_id}/users" \
  -H "Authorization: Bearer tenant_admin_token" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "developer@company.com",
    "first_name": "John",
    "last_name": "Developer",
    "role": "developer",
    "send_invitation": true
  }'
```

#### List Tenant Users
```bash
curl -X GET "https://api.leanvibe.ai/v1/tenants/{tenant_id}/users" \
  -H "Authorization: Bearer tenant_admin_token" \
  -G -d "page=1" -d "limit=50" -d "role=developer"
```

#### Update User Role
```bash
curl -X PATCH "https://api.leanvibe.ai/v1/tenants/{tenant_id}/users/{user_id}" \
  -H "Authorization: Bearer tenant_admin_token" \
  -H "Content-Type: application/json" \
  -d '{
    "role": "manager",
    "status": "active"
  }'
```

### Usage Monitoring

#### Get Current Usage
```bash
curl -X GET "https://api.leanvibe.ai/v1/tenants/{tenant_id}/usage" \
  -H "Authorization: Bearer tenant_admin_token"
```

#### Get Usage History
```bash
curl -X GET "https://api.leanvibe.ai/v1/tenants/{tenant_id}/usage/history" \
  -H "Authorization: Bearer tenant_admin_token" \
  -G -d "start_date=2024-01-01" -d "end_date=2024-01-31" -d "granularity=daily"
```

**Response:**
```json
{
  "tenant_id": "tenant-uuid",
  "period": {
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-01-31T23:59:59Z",
    "granularity": "daily"
  },
  "usage_data": [
    {
      "date": "2024-01-01",
      "api_calls": 2500,
      "ai_requests": 45,
      "storage_mb": 8200,
      "active_users": 12,
      "concurrent_sessions_peak": 8
    },
    {
      "date": "2024-01-02", 
      "api_calls": 3200,
      "ai_requests": 52,
      "storage_mb": 8350,
      "active_users": 15,
      "concurrent_sessions_peak": 11
    }
  ]
}
```

## Billing and Subscription API

### Plan Management

#### List Available Plans
```bash
curl -X GET "https://api.leanvibe.ai/v1/billing/plans" \
  -H "Authorization: Bearer token"
```

**Response:**
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
curl -X POST "https://api.leanvibe.ai/v1/billing/subscriptions" \
  -H "Authorization: Bearer tenant_admin_token" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "tenant-uuid",
    "plan_id": "plan-uuid-enterprise",
    "payment_method_id": "pm_stripe_payment_method_id",
    "trial_period_days": 30
  }'
```

#### Get Subscription Details
```bash
curl -X GET "https://api.leanvibe.ai/v1/billing/subscriptions/{subscription_id}" \
  -H "Authorization: Bearer tenant_admin_token"
```

#### Update Subscription
```bash
curl -X PATCH "https://api.leanvibe.ai/v1/billing/subscriptions/{subscription_id}" \
  -H "Authorization: Bearer tenant_admin_token" \
  -H "Content-Type: application/json" \
  -d '{
    "plan_id": "new-plan-uuid",
    "prorate": true
  }'
```

#### Cancel Subscription
```bash
curl -X PATCH "https://api.leanvibe.ai/v1/billing/subscriptions/{subscription_id}" \
  -H "Authorization: Bearer tenant_admin_token" \
  -H "Content-Type: application/json" \
  -d '{
    "cancel_at_period_end": true
  }'
```

### Usage-Based Billing

#### Record Usage Event
```bash
curl -X POST "https://api.leanvibe.ai/v1/billing/usage" \
  -H "Authorization: Bearer api_token" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "tenant-uuid",
    "metric_type": "api_calls",
    "quantity": 100,
    "timestamp": "2024-01-15T10:30:00Z"
  }'
```

#### Bulk Record Usage
```bash
curl -X POST "https://api.leanvibe.ai/v1/billing/usage/bulk" \
  -H "Authorization: Bearer api_token" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "tenant-uuid",
    "usage_records": [
      {
        "metric_type": "api_calls",
        "quantity": 1500,
        "date": "2024-01-15"
      },
      {
        "metric_type": "storage_gb", 
        "quantity": 25,
        "date": "2024-01-15"
      },
      {
        "metric_type": "ai_requests",
        "quantity": 300,
        "date": "2024-01-15"
      }
    ]
  }'
```

### Invoice Management

#### List Invoices
```bash
curl -X GET "https://api.leanvibe.ai/v1/billing/invoices" \
  -H "Authorization: Bearer tenant_admin_token" \
  -G -d "status=paid" -d "limit=25"
```

#### Get Invoice Details
```bash
curl -X GET "https://api.leanvibe.ai/v1/billing/invoices/{invoice_id}" \
  -H "Authorization: Bearer tenant_admin_token"
```

**Response:**
```json
{
  "id": "invoice-uuid",
  "invoice_number": "INV-2024-001",
  "status": "paid",
  "subtotal": 20000,
  "tax_amount": 1600,
  "total": 21600,
  "currency": "USD",
  "issue_date": "2024-01-01T00:00:00Z",
  "due_date": "2024-01-31T00:00:00Z",
  "paid_at": "2024-01-15T10:30:00Z",
  "line_items": [
    {
      "description": "Team Plan - January 2024",
      "quantity": 1,
      "unit_price": 20000,
      "total": 20000
    }
  ],
  "pdf_url": "https://api.leanvibe.ai/v1/billing/invoices/invoice-uuid/pdf"
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
    "stripe_payment_method_id": "pm_1234567890"
  }'
```

#### List Payment Methods
```bash
curl -X GET "https://api.leanvibe.ai/v1/billing/payment-methods" \
  -H "Authorization: Bearer tenant_admin_token"
```

#### Set Default Payment Method
```bash
curl -X PATCH "https://api.leanvibe.ai/v1/billing/payment-methods/{pm_id}/default" \
  -H "Authorization: Bearer tenant_admin_token"
```

## Autonomous Development API

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

**Response:**
```json
{
  "id": "task-uuid",
  "status": "queued",
  "project_id": "project-uuid",
  "title": "Implement user authentication API",
  "estimated_duration_minutes": 120,
  "assigned_agent": "l3-agent-001",
  "created_at": "2024-01-15T10:30:00Z",
  "tracking_url": "https://app.leanvibe.ai/tasks/task-uuid"
}
```

#### Get Task Status
```bash
curl -X GET "https://api.leanvibe.ai/v1/tasks/{task_id}" \
  -H "Authorization: Bearer developer_token"
```

**Response:**
```json
{
  "id": "task-uuid",
  "status": "in_progress",
  "progress_percentage": 65,
  "current_step": "Writing unit tests",
  "estimated_completion": "2024-01-15T12:45:00Z",
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

#### Generate Code Components
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

### Real-Time Monitoring

#### WebSocket Connection for Real-Time Updates
```javascript
// JavaScript WebSocket client example
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

## Advanced Enterprise Features

### Audit Logging

#### Get Authentication Audit Log
```bash
curl -X GET "https://api.leanvibe.ai/v1/admin/audit/auth" \
  -H "Authorization: Bearer admin_token" \
  -G -d "tenant_id=tenant-uuid" -d "start_date=2024-01-01" -d "limit=100"
```

#### Get Billing Audit Log
```bash
curl -X GET "https://api.leanvibe.ai/v1/admin/audit/billing" \
  -H "Authorization: Bearer admin_token" \
  -G -d "tenant_id=tenant-uuid" -d "event_type=subscription_updated"
```

### Analytics and Reporting

#### Revenue Analytics
```bash
curl -X GET "https://api.leanvibe.ai/v1/billing/analytics/revenue" \
  -H "Authorization: Bearer admin_token" \
  -G -d "period=monthly" -d "start_date=2024-01-01" -d "end_date=2024-12-31"
```

**Response:**
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

#### Usage Analytics  
```bash
curl -X GET "https://api.leanvibe.ai/v1/analytics/usage" \
  -H "Authorization: Bearer admin_token" \
  -G -d "tenant_id=all" -d "period=30d" -d "metrics=api_calls,ai_requests,storage"
```

### Health and Monitoring

#### Platform Health Check
```bash
curl -X GET "https://api.leanvibe.ai/v1/health" \
  -H "Authorization: Bearer token"
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
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

#### Tenant Health Check
```bash
curl -X GET "https://api.leanvibe.ai/v1/health/tenant/{tenant_id}" \
  -H "Authorization: Bearer tenant_admin_token"
```

## Rate Limiting and Quotas

### Rate Limit Headers

All API responses include rate limiting information:

```http
X-RateLimit-Limit: 10000
X-RateLimit-Remaining: 9847
X-RateLimit-Reset: 1642262400
X-RateLimit-Retry-After: 3600
```

### Plan-Based Limits

| Plan | Requests/Minute | Requests/Month | AI Requests/Day |
|------|----------------|----------------|----------------|
| **Developer** | 100 | 10,000 | 100 |
| **Team** | 1,000 | 100,000 | 1,000 |
| **Enterprise** | 10,000 | Unlimited | 10,000 |

### Quota Exceeded Response

```json
{
  "error": "quota_exceeded",
  "message": "Monthly API quota exceeded",
  "details": {
    "quota_type": "api_calls",
    "current_usage": 100000,
    "quota_limit": 100000,
    "reset_date": "2024-02-01T00:00:00Z"
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

## Error Handling

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
  "timestamp": "2024-01-15T10:30:00Z"
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

## SDKs and Client Libraries

### Official SDK Support

#### Python SDK
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

#### Node.js SDK
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

### Webhook Integration

#### Configure Webhooks
```bash
curl -X POST "https://api.leanvibe.ai/v1/admin/webhooks" \
  -H "Authorization: Bearer admin_token" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-app.com/webhooks/leanvibe",
    "events": [
      "task.completed",
      "billing.payment_succeeded",
      "user.created"
    ],
    "secret": "your_webhook_secret"
  }'
```

#### Webhook Event Types

- **Authentication Events**: `user.created`, `user.login`, `user.logout`
- **Task Events**: `task.created`, `task.in_progress`, `task.completed`, `task.failed`
- **Billing Events**: `subscription.created`, `invoice.paid`, `payment.failed`
- **System Events**: `quota.warning`, `quota.exceeded`, `maintenance.scheduled`

## Enterprise Integration Examples

### CI/CD Pipeline Integration

```yaml
# GitHub Actions workflow
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

### Slack Bot Integration

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

## Support and Resources

### Enterprise Support Channels

- **API Support**: api-support@leanvibe.ai
- **Integration Consulting**: integrations@leanvibe.ai  
- **Technical Documentation**: [docs.leanvibe.ai/api](https://docs.leanvibe.ai/api)
- **Status Page**: [status.leanvibe.ai](https://status.leanvibe.ai)
- **Developer Community**: [community.leanvibe.ai](https://community.leanvibe.ai)

### Getting Started

1. **Request Enterprise API Access**: Contact enterprise@leanvibe.ai
2. **Get API Credentials**: Access admin panel for API key generation
3. **Review Integration Guide**: Follow specific integration documentation
4. **Test in Sandbox**: Use test environment before production
5. **Production Deployment**: Enterprise onboarding with dedicated support

---

**Ready to integrate with LeanVibe Enterprise APIs?** Contact our integration specialists for personalized assistance and accelerated deployment support.