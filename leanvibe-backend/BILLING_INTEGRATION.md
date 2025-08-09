# LeanVibe Enterprise Billing Integration Guide

## Overview

LeanVibe's enterprise billing system provides comprehensive subscription management, usage-based metered billing, and automated payment processing through Stripe integration. This guide covers the complete setup and configuration of the billing system for enterprise deployments.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                 LeanVibe Billing System                │
├─────────────────────────────────────────────────────────┤
│  Subscription   │  Usage Tracking  │  Invoice        │
│  Management     │  & Metering     │  Generation     │
│                 │                 │                 │
│  Payment        │  Webhook        │  Analytics      │
│  Processing     │  Handlers       │  & Reporting    │
└─────────────────────────────────────────────────────────┘
           │                    │                    │
    ┌─────────────┐    ┌─────────────────┐    ┌─────────────┐
    │   Stripe    │    │   Usage APIs    │    │  Enterprise │
    │ Integration │    │   Real-time     │    │  Reporting  │
    │             │    │   Tracking      │    │             │
    └─────────────┘    └─────────────────┘    └─────────────┘
```

## Stripe Account Setup

### Step 1: Create Stripe Account

1. Sign up for [Stripe](https://stripe.com) business account
2. Complete business verification process
3. Enable international payments (if required)
4. Configure tax settings for your regions

### Step 2: Generate API Keys

Navigate to **Developers** → **API Keys** in Stripe Dashboard:

**Live Keys:**
```
Publishable Key: pk_live_...
Secret Key: sk_live_...
```

**Test Keys:**
```
Publishable Key: pk_test_...
Secret Key: sk_test_...
```

### Step 3: Create Products and Prices

Create the three main subscription products in Stripe:

#### Developer Plan ($50/month)
```bash
curl https://api.stripe.com/v1/products \
  -u sk_live_your_secret_key: \
  -d name="LeanVibe Developer" \
  -d description="Perfect for individual developers and small projects"

curl https://api.stripe.com/v1/prices \
  -u sk_live_your_secret_key: \
  -d product="prod_developer_id" \
  -d unit_amount=5000 \
  -d currency=usd \
  -d recurring[interval]=month
```

#### Team Plan ($200/month)
```bash
curl https://api.stripe.com/v1/products \
  -u sk_live_your_secret_key: \
  -d name="LeanVibe Team" \
  -d description="Ideal for growing development teams"

curl https://api.stripe.com/v1/prices \
  -u sk_live_your_secret_key: \
  -d product="prod_team_id" \
  -d unit_amount=20000 \
  -d currency=usd \
  -d recurring[interval]=month
```

#### Enterprise Plan ($800/month)
```bash
curl https://api.stripe.com/v1/products \
  -u sk_live_your_secret_key: \
  -d name="LeanVibe Enterprise" \
  -d description="Full enterprise features with unlimited scale"

curl https://api.stripe.com/v1/prices \
  -u sk_live_your_secret_key: \
  -d product="prod_enterprise_id" \
  -d unit_amount=80000 \
  -d currency=usd \
  -d recurring[interval]=month
```

## LeanVibe Billing Configuration

### Step 1: Configure Environment Variables

Add Stripe configuration to your environment:

```bash
# Production Environment
export STRIPE_SECRET_KEY="sk_live_your_secret_key"
export STRIPE_PUBLISHABLE_KEY="pk_live_your_publishable_key"
export STRIPE_WEBHOOK_SECRET="whsec_your_webhook_secret"

# Development Environment  
export STRIPE_SECRET_KEY="sk_test_your_secret_key"
export STRIPE_PUBLISHABLE_KEY="pk_test_your_publishable_key"
export STRIPE_WEBHOOK_SECRET="whsec_your_test_webhook_secret"
```

### Step 2: Initialize Billing Service

Configure the LeanVibe billing service with your Stripe settings:

```python
from app.services.billing_service import billing_service

# Initialize billing service
await billing_service.initialize_stripe_integration(
    api_key=os.getenv("STRIPE_SECRET_KEY"),
    webhook_secret=os.getenv("STRIPE_WEBHOOK_SECRET")
)
```

### Step 3: Create Default Plans

Initialize your subscription plans in LeanVibe:

```python
from app.models.billing_models import Plan, DEFAULT_PLANS

# Create plans in database
for plan_slug, plan_config in DEFAULT_PLANS.items():
    await billing_service.create_plan(plan_config)
```

## Subscription Management

### Creating Subscriptions

**API Endpoint:**
```
POST /api/v1/billing/subscriptions
```

**Request Example:**
```bash
curl -X POST "https://api.leanvibe.ai/v1/billing/subscriptions" \
  -H "Authorization: Bearer tenant-admin-token" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "tenant-uuid-here",
    "plan_id": "plan-uuid-here",
    "payment_method_id": "pm_stripe_payment_method",
    "trial_period_days": 14,
    "coupon_code": "WELCOME20"
  }'
```

**Response:**
```json
{
  "id": "sub_uuid",
  "tenant_id": "tenant_uuid",
  "plan_id": "plan_uuid", 
  "status": "trialing",
  "current_period_start": "2024-01-01T00:00:00Z",
  "current_period_end": "2024-02-01T00:00:00Z",
  "trial_end": "2024-01-15T00:00:00Z",
  "stripe_subscription_id": "sub_stripe_id"
}
```

### Subscription Lifecycle Management

#### Upgrade/Downgrade Plans
```bash
curl -X PATCH "https://api.leanvibe.ai/v1/billing/subscriptions/{sub_id}" \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{
    "plan_id": "new-plan-uuid",
    "prorate": true
  }'
```

#### Cancel Subscription
```bash
curl -X PATCH "https://api.leanvibe.ai/v1/billing/subscriptions/{sub_id}" \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{
    "cancel_at_period_end": true
  }'
```

#### Reactivate Cancelled Subscription
```bash
curl -X POST "https://api.leanvibe.ai/v1/billing/subscriptions/{sub_id}/reactivate" \
  -H "Authorization: Bearer admin-token"
```

## Usage-Based Billing Setup

### Metered Billing Configuration

LeanVibe supports usage-based billing for several metrics:

- **API Calls**: Per-request pricing beyond plan limits
- **Storage**: Additional storage beyond plan quotas  
- **AI Requests**: Premium AI model usage
- **Active Users**: Per-seat pricing for team expansion
- **Concurrent Sessions**: WebSocket connection overages

#### Create Metered Price in Stripe

```bash
curl https://api.stripe.com/v1/prices \
  -u sk_live_your_secret_key: \
  -d product="prod_your_product" \
  -d unit_amount=1 \
  -d currency=usd \
  -d recurring[interval]=month \
  -d recurring[usage_type]=metered \
  -d recurring[aggregate_usage]=sum \
  -d billing_scheme=per_unit
```

#### Track Usage in LeanVibe

**Real-time Usage Tracking:**
```python
from app.services.billing_service import billing_service

# Record usage event
await billing_service.record_usage(
    tenant_id=tenant_id,
    metric_type="api_calls",
    quantity=1,
    timestamp=datetime.utcnow()
)
```

**Batch Usage Reporting:**
```python
# Report daily usage batch
usage_records = [
    {"metric_type": "api_calls", "quantity": 1500, "date": "2024-01-01"},
    {"metric_type": "storage_gb", "quantity": 25, "date": "2024-01-01"},
    {"metric_type": "ai_requests", "quantity": 300, "date": "2024-01-01"}
]

await billing_service.bulk_record_usage(tenant_id, usage_records)
```

### Usage Analytics Dashboard

**Get Current Usage:**
```bash
curl -X GET "https://api.leanvibe.ai/v1/billing/usage/current" \
  -H "Authorization: Bearer tenant-token"
```

**Response:**
```json
{
  "tenant_id": "tenant_uuid",
  "current_period": {
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-02-01T00:00:00Z"
  },
  "usage_metrics": {
    "api_calls": {
      "current": 8500,
      "limit": 10000,
      "overages": 0,
      "unit_price_cents": 1
    },
    "storage_gb": {
      "current": 12,
      "limit": 10, 
      "overages": 2,
      "unit_price_cents": 500
    }
  },
  "projected_overage_cost": 1000
}
```

## Payment Processing

### Payment Method Management

#### Add Payment Method
```bash
curl -X POST "https://api.leanvibe.ai/v1/billing/payment-methods" \
  -H "Authorization: Bearer tenant-admin-token" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "card",
    "stripe_payment_method_id": "pm_stripe_id"
  }'
```

#### Set Default Payment Method
```bash
curl -X PATCH "https://api.leanvibe.ai/v1/billing/payment-methods/{pm_id}/default" \
  -H "Authorization: Bearer tenant-admin-token"
```

### Failed Payment Handling

LeanVibe implements sophisticated dunning management:

#### Automatic Retry Schedule
- **Day 1**: Immediate retry + email notification
- **Day 3**: Second retry + email notification  
- **Day 7**: Third retry + account suspension warning
- **Day 14**: Account suspension + service degradation
- **Day 30**: Account cancellation + data retention notice

#### Smart Retry Logic
```python
# Configure retry behavior
RETRY_CONFIG = {
    "max_attempts": 4,
    "retry_schedule": [1, 3, 7, 14],  # Days
    "grace_period_days": 3,
    "auto_suspend_after_days": 14,
    "auto_cancel_after_days": 30
}
```

### Enterprise Invoicing

#### Custom Invoice Generation
```bash
curl -X POST "https://api.leanvibe.ai/v1/billing/invoices" \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "tenant_uuid",
    "billing_period": {
      "start": "2024-01-01T00:00:00Z",
      "end": "2024-01-31T23:59:59Z"
    },
    "line_items": [
      {
        "description": "Team Plan - January 2024",
        "quantity": 1,
        "unit_price": 20000,
        "total": 20000
      },
      {
        "description": "API Overages - 5,000 calls",
        "quantity": 5000,
        "unit_price": 1,
        "total": 5000
      }
    ],
    "due_date": "2024-02-15T00:00:00Z"
  }'
```

#### Invoice Customization
```json
{
  "invoice_settings": {
    "company_logo": "https://cdn.leanvibe.ai/logo.png",
    "company_name": "LeanVibe Technologies Inc.",
    "company_address": {
      "line1": "123 Tech Street",
      "city": "San Francisco",
      "state": "CA",
      "postal_code": "94105",
      "country": "US"
    },
    "payment_terms": "Net 30",
    "custom_fields": [
      {"name": "PO Number", "value": "ENT-2024-001"}
    ]
  }
}
```

## Webhook Integration

### Configure Stripe Webhooks

1. In Stripe Dashboard, go to **Developers** → **Webhooks**
2. Add endpoint: `https://api.leanvibe.ai/v1/billing/webhooks/stripe`
3. Select events to listen for:

**Required Events:**
- `customer.subscription.created`
- `customer.subscription.updated` 
- `customer.subscription.deleted`
- `invoice.payment_succeeded`
- `invoice.payment_failed`
- `payment_intent.succeeded`
- `payment_intent.payment_failed`

### Webhook Event Handling

**Subscription Events:**
```python
@router.post("/webhooks/stripe")
async def handle_stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
        
        if event["type"] == "customer.subscription.updated":
            await handle_subscription_updated(event["data"]["object"])
        elif event["type"] == "invoice.payment_failed":
            await handle_payment_failed(event["data"]["object"])
            
    except ValueError:
        raise HTTPException(400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(400, detail="Invalid signature")
```

## Tax Management & Compliance

### Tax Configuration

#### US Sales Tax
```python
tax_config = {
    "tax_type": "sales_tax",
    "tax_rates": {
        "CA": 8.25,  # California
        "NY": 8.00,  # New York
        "TX": 6.25   # Texas
    },
    "nexus_states": ["CA", "NY", "TX", "WA"],
    "tax_exempt_customers": []
}
```

#### EU VAT
```python
vat_config = {
    "tax_type": "vat",
    "vat_rates": {
        "DE": 19.0,  # Germany
        "FR": 20.0,  # France
        "UK": 20.0,  # United Kingdom
        "IE": 23.0   # Ireland
    },
    "reverse_charge_threshold": 10000,  # €100
    "moss_reporting": True
}
```

### Automated Tax Calculation

**Tax Calculation API:**
```bash
curl -X POST "https://api.leanvibe.ai/v1/billing/tax/calculate" \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 20000,
    "currency": "USD",
    "customer_address": {
      "country": "US",
      "state": "CA",
      "postal_code": "94105"
    },
    "product_type": "saas_subscription"
  }'
```

## Analytics & Reporting

### Revenue Analytics

**Monthly Recurring Revenue (MRR):**
```bash
curl -X GET "https://api.leanvibe.ai/v1/billing/analytics/mrr" \
  -H "Authorization: Bearer admin-token" \
  -G -d "start_date=2024-01-01" -d "end_date=2024-01-31"
```

**Response:**
```json
{
  "period": {
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-01-31T23:59:59Z"
  },
  "metrics": {
    "total_mrr": 125000,
    "new_mrr": 15000,
    "expansion_mrr": 8000,
    "contraction_mrr": -2000,
    "churn_mrr": -5000,
    "net_new_mrr": 16000
  },
  "by_plan": {
    "developer": {"mrr": 25000, "subscribers": 500},
    "team": {"mrr": 60000, "subscribers": 300},
    "enterprise": {"mrr": 40000, "subscribers": 50}
  }
}
```

### Usage Analytics

**Detailed Usage Report:**
```bash
curl -X GET "https://api.leanvibe.ai/v1/billing/analytics/usage" \
  -H "Authorization: Bearer admin-token" \
  -G -d "tenant_id=all" -d "period=30d"
```

### Churn Analysis

**Churn Metrics:**
```json
{
  "churn_rate": 2.5,
  "revenue_churn_rate": 3.2,
  "cohort_analysis": {
    "jan_2024": {"retention_rate": 95.5, "revenue_retention": 108.2},
    "feb_2024": {"retention_rate": 93.2, "revenue_retention": 102.1}
  },
  "churn_reasons": {
    "price": 35,
    "features": 25,
    "support": 15,
    "other": 25
  }
}
```

## Enterprise Billing Features

### Custom Pricing & Contracts

**Enterprise Contract Setup:**
```bash
curl -X POST "https://api.leanvibe.ai/v1/billing/contracts" \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "enterprise_tenant_uuid",
    "contract_terms": {
      "annual_minimum": 100000,
      "custom_pricing": {
        "base_price": 50000,
        "user_price": 100,
        "overage_rates": {
          "api_calls": 0.5,
          "storage_gb": 300
        }
      },
      "payment_terms": "Net 60",
      "auto_renewal": true,
      "volume_discounts": [
        {"threshold": 100000, "discount": 10},
        {"threshold": 500000, "discount": 20}
      ]
    }
  }'
```

### Multi-Entity Billing

**Corporate Hierarchy Setup:**
```json
{
  "parent_entity": {
    "tenant_id": "parent_corp_uuid",
    "billing_consolidation": true,
    "payment_responsibility": true
  },
  "child_entities": [
    {
      "tenant_id": "subsidiary_1_uuid", 
      "cost_allocation": 60
    },
    {
      "tenant_id": "subsidiary_2_uuid",
      "cost_allocation": 40
    }
  ]
}
```

### Advanced Reporting

**Executive Dashboard API:**
```bash
curl -X GET "https://api.leanvibe.ai/v1/billing/executive-dashboard" \
  -H "Authorization: Bearer admin-token"
```

**Response includes:**
- Revenue growth trends
- Customer acquisition costs
- Lifetime value calculations
- Profitability by plan
- Usage forecasting
- Payment health scores

## Integration Testing

### Test Suite Setup

**Billing Integration Tests:**
```python
import pytest
from app.services.billing_service import billing_service

@pytest.mark.asyncio
async def test_subscription_creation():
    # Test subscription creation
    subscription = await billing_service.create_subscription({
        "tenant_id": test_tenant_id,
        "plan_id": test_plan_id,
        "payment_method_id": "pm_test_card"
    })
    
    assert subscription.status == "trialing"
    assert subscription.stripe_subscription_id is not None

@pytest.mark.asyncio
async def test_usage_recording():
    # Test usage tracking
    await billing_service.record_usage(
        tenant_id=test_tenant_id,
        metric_type="api_calls", 
        quantity=100
    )
    
    usage = await billing_service.get_current_usage(test_tenant_id)
    assert usage.api_calls >= 100
```

### Load Testing

**Billing API Load Test:**
```bash
# Using Apache Bench
ab -n 1000 -c 50 -H "Authorization: Bearer test-token" \
  "https://api.leanvibe.ai/v1/billing/usage/current"

# Using curl-loader
curl-loader -f billing_load_test.conf
```

## Support & Troubleshooting

### Common Issues

**Webhook Delivery Failures:**
- Check endpoint URL accessibility
- Verify SSL certificate validity
- Review signature verification logic
- Monitor webhook retry attempts

**Payment Failures:**
- Validate payment method setup
- Check account funding
- Review fraud detection rules
- Verify international payment settings

### Monitoring & Alerting

**Key Metrics to Monitor:**
- Webhook delivery success rate (>99%)
- Payment success rate (>95%)
- Invoice generation time (<30s)
- Usage tracking accuracy (100%)

**Alert Configuration:**
```json
{
  "alerts": [
    {
      "metric": "payment_failure_rate",
      "threshold": 5,
      "period": "1h",
      "action": "page_on_call_engineer"
    },
    {
      "metric": "webhook_failure_rate", 
      "threshold": 1,
      "period": "15m",
      "action": "notify_billing_team"
    }
  ]
}
```

### Enterprise Support

For enterprise billing assistance:
- **Email**: billing-support@leanvibe.ai
- **Phone**: +1 (555) 123-4567 ext. 3
- **Slack**: #enterprise-billing in LeanVibe Community
- **Escalation**: enterprise-escalation@leanvibe.ai

---

**Ready to implement enterprise billing?** Contact our billing specialists for personalized setup assistance and ensure seamless payment processing for your organization.