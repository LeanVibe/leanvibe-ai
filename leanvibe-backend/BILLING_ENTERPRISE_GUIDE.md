# Enterprise Billing and Subscription Management Guide

## Overview & Business Value

LeanVibe's enterprise billing system provides comprehensive subscription management, sophisticated usage-based metered billing, automated payment processing, and enterprise-grade invoicing through deep Stripe integration. This system enables scalable SaaS revenue operations with advanced analytics, compliance features, and multi-entity billing capabilities.

**Key Enterprise Features:**
- **Usage-Based Metered Billing**: Real-time tracking and billing for API calls, storage, AI requests, and user seats
- **Enterprise Invoicing**: Automated invoice generation with custom branding, PO support, and multi-entity billing
- **Revenue Analytics**: Advanced MRR/ARR tracking, cohort analysis, and revenue forecasting
- **Compliance & Tax Management**: Automated US Sales Tax, EU VAT, and global tax compliance
- **Subscription Lifecycle**: Complete automation from trial to renewal with intelligent dunning management
- **Enterprise Contracts**: Custom pricing, volume discounts, and multi-year agreements

## Subscription Tier Overview

### Developer Tier ($50/month)
**Target**: Individual developers and small projects
```json
{
  "base_price": 5000,  // $50.00 in cents
  "billing_interval": "monthly",
  "features": {
    "max_users": 1,
    "max_projects": 5,
    "max_api_calls_per_month": 10000,
    "storage_gb": 1,
    "ai_requests_per_day": 100,
    "concurrent_sessions": 2,
    "email_support": true,
    "api_access": true
  },
  "overage_pricing": {
    "api_calls": 0.01,     // $0.01 per additional call
    "storage_gb": 5.00      // $5.00 per additional GB
  },
  "trial_period_days": 14
}
```

### Team Tier ($200/month)
**Target**: Growing development teams
```json
{
  "base_price": 20000,  // $200.00 in cents
  "billing_interval": "monthly", 
  "features": {
    "max_users": 10,
    "max_projects": 50,
    "max_api_calls_per_month": 100000,
    "storage_gb": 10,
    "ai_requests_per_day": 1000,
    "concurrent_sessions": 10,
    "email_support": true,
    "chat_support": true,
    "sso_support": true,
    "api_access": true
  },
  "overage_pricing": {
    "api_calls": 0.01,     // $0.01 per additional call
    "storage_gb": 4.00      // $4.00 per additional GB  
  },
  "trial_period_days": 14
}
```

### Enterprise Tier ($800/month)
**Target**: Large enterprises with unlimited scale
```json
{
  "base_price": 80000,  // $800.00 in cents
  "billing_interval": "monthly",
  "is_enterprise": true,
  "features": {
    "max_users": 999999,        // Unlimited
    "max_projects": 999999,     // Unlimited
    "max_api_calls_per_month": 999999999,  // Unlimited
    "storage_gb": 1000,         // 1TB included
    "ai_requests_per_day": 10000,
    "concurrent_sessions": 100,
    "email_support": true,
    "chat_support": true,
    "phone_support": true,
    "sso_support": true,
    "saml_support": true,
    "custom_integrations": true,
    "dedicated_support": true,
    "sla_guarantee": true
  },
  "overage_pricing": {
    "storage_gb": 3.00          // $3.00 per GB over 1TB
  },
  "trial_period_days": 30
}
```

## Billing System Architecture

```
┌─────────────────────────────────────────────────────────┐
│              LeanVibe Enterprise Billing System        │
├─────────────────────────────────────────────────────────┤
│  Subscription    │  Usage Tracking  │  Payment         │
│  Management      │  & Metering      │  Processing      │
│                  │                  │                  │
│  • Plan Tiers    │  • Real-time     │  • Stripe        │
│  • Upgrades      │    Tracking      │    Integration   │
│  • Cancellations │  • Overage       │  • Multiple      │
│  • Renewals      │    Billing       │    Currencies    │
└─────────────────────────────────────────────────────────┘
           │                    │                    │
    ┌─────────────┐    ┌─────────────────┐    ┌─────────────┐
    │  Analytics  │    │  Invoice        │    │  Enterprise │
    │  & Reporting│    │  Generation     │    │  Features   │
    │             │    │                 │    │             │
    └─────────────┘    └─────────────────┘    └─────────────┘
```

## Implementation Guide

### Stripe Integration Setup

#### Step 1: Stripe Account Configuration

**Production Account Setup:**
1. Create Stripe business account at [stripe.com](https://stripe.com)
2. Complete business verification process
3. Configure tax settings for operating jurisdictions
4. Enable international payments if required
5. Set up webhook endpoints for real-time event processing

**API Key Configuration:**
```bash
# Production Environment Variables
export STRIPE_SECRET_KEY="sk_live_your_secret_key"
export STRIPE_PUBLISHABLE_KEY="pk_live_your_publishable_key"  
export STRIPE_WEBHOOK_SECRET="whsec_your_webhook_secret"

# Development Environment Variables
export STRIPE_SECRET_KEY="sk_test_your_test_key"
export STRIPE_PUBLISHABLE_KEY="pk_test_your_test_key"
export STRIPE_WEBHOOK_SECRET="whsec_your_test_webhook_secret"
```

#### Step 2: Create Products and Pricing

**Developer Plan Setup:**
```bash
# Create Developer Product
curl https://api.stripe.com/v1/products \
  -u sk_live_your_secret_key: \
  -d name="LeanVibe Developer" \
  -d description="Perfect for individual developers and small projects" \
  -d metadata[plan_slug]="developer"

# Create Developer Price  
curl https://api.stripe.com/v1/prices \
  -u sk_live_your_secret_key: \
  -d product="prod_developer_id" \
  -d unit_amount=5000 \
  -d currency=usd \
  -d recurring[interval]=month \
  -d metadata[plan_tier]="developer"
```

**Team Plan Setup:**
```bash
# Create Team Product
curl https://api.stripe.com/v1/products \
  -u sk_live_your_secret_key: \
  -d name="LeanVibe Team" \
  -d description="Ideal for growing development teams" \
  -d metadata[plan_slug]="team"

# Create Team Price
curl https://api.stripe.com/v1/prices \
  -u sk_live_your_secret_key: \
  -d product="prod_team_id" \
  -d unit_amount=20000 \
  -d currency=usd \
  -d recurring[interval]=month \
  -d metadata[plan_tier]="team"
```

**Enterprise Plan Setup:**
```bash
# Create Enterprise Product  
curl https://api.stripe.com/v1/products \
  -u sk_live_your_secret_key: \
  -d name="LeanVibe Enterprise" \
  -d description="Full enterprise features with unlimited scale" \
  -d metadata[plan_slug]="enterprise"

# Create Enterprise Price
curl https://api.stripe.com/v1/prices \
  -u sk_live_your_secret_key: \
  -d product="prod_enterprise_id" \
  -d unit_amount=80000 \
  -d currency=usd \
  -d recurring[interval]=month \
  -d metadata[plan_tier]="enterprise"
```

#### Step 3: Usage-Based Billing Configuration

**API Calls Metered Pricing:**
```bash
# Create API calls metered price
curl https://api.stripe.com/v1/prices \
  -u sk_live_your_secret_key: \
  -d product="prod_api_calls_id" \
  -d unit_amount=1 \
  -d currency=usd \
  -d recurring[interval]=month \
  -d recurring[usage_type]=metered \
  -d recurring[aggregate_usage]=sum \
  -d billing_scheme=per_unit \
  -d metadata[metric_type]="api_calls"
```

**Storage Overage Pricing:**
```bash
# Create storage overage price
curl https://api.stripe.com/v1/prices \
  -u sk_live_your_secret_key: \
  -d product="prod_storage_id" \
  -d unit_amount=300 \
  -d currency=usd \
  -d recurring[interval]=month \
  -d recurring[usage_type]=metered \
  -d recurring[aggregate_usage]=last_during_period \
  -d billing_scheme=per_unit \
  -d metadata[metric_type]="storage_gb"
```

### Subscription Management

#### Creating Enterprise Subscriptions

**API Endpoint:**
```
POST /api/v1/billing/subscriptions
```

**Enterprise Subscription Creation:**
```bash
curl -X POST "https://api.leanvibe.ai/v1/billing/subscriptions" \
  -H "Authorization: Bearer tenant-admin-token" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
    "plan_id": "enterprise-plan-uuid",
    "payment_method_id": "pm_stripe_payment_method_id",
    "trial_period_days": 30,
    "coupon_code": "ENTERPRISE20",
    "billing_address": {
      "company_name": "Acme Corporation",
      "line1": "123 Enterprise Blvd",
      "line2": "Suite 500",
      "city": "San Francisco",
      "state": "CA",
      "postal_code": "94105",
      "country": "US"
    },
    "tax_id": "12-3456789",
    "custom_pricing": {
      "base_price": 75000,  // $750 custom price
      "discount_percentage": 6.25
    }
  }'
```

**Response:**
```json
{
  "id": "sub-uuid-here",
  "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
  "plan_id": "enterprise-plan-uuid",
  "status": "trialing",
  "custom_price": 75000,
  "discount_percentage": 6.25,
  "current_period_start": "2024-01-01T00:00:00Z",
  "current_period_end": "2024-02-01T00:00:00Z",
  "trial_start": "2024-01-01T00:00:00Z",
  "trial_end": "2024-01-31T00:00:00Z",
  "stripe_subscription_id": "sub_stripe_id_here",
  "billing_account": {
    "id": "billing-account-uuid",
    "company_name": "Acme Corporation",
    "billing_email": "billing@acme-corp.com",
    "stripe_customer_id": "cus_stripe_id_here"
  }
}
```

#### Subscription Lifecycle Management

**Plan Upgrades with Proration:**
```bash
curl -X PATCH "https://api.leanvibe.ai/v1/billing/subscriptions/{subscription_id}" \
  -H "Authorization: Bearer tenant-admin-token" \
  -H "Content-Type: application/json" \
  -d '{
    "plan_id": "enterprise-plan-uuid",
    "prorate": true,
    "upgrade_date": "immediate"
  }'
```

**Scheduled Cancellation:**
```bash
curl -X PATCH "https://api.leanvibe.ai/v1/billing/subscriptions/{subscription_id}" \
  -H "Authorization: Bearer tenant-admin-token" \
  -H "Content-Type: application/json" \
  -d '{
    "cancel_at_period_end": true,
    "cancellation_reason": "cost_optimization",
    "feedback": "Great product, but need to reduce costs"
  }'
```

**Subscription Reactivation:**
```bash
curl -X POST "https://api.leanvibe.ai/v1/billing/subscriptions/{subscription_id}/reactivate" \
  -H "Authorization: Bearer tenant-admin-token" \
  -H "Content-Type: application/json" \
  -d '{
    "reactivate_immediately": true,
    "new_payment_method_id": "pm_new_payment_method"
  }'
```

### Usage-Based Billing Implementation

#### Real-Time Usage Tracking

**Usage Recording Service Implementation:**
```python
# Implementation from app/services/billing_service.py
class BillingService:
    async def record_usage(
        self,
        tenant_id: UUID,
        metric_type: UsageMetricType,
        quantity: int,
        timestamp: datetime = None
    ) -> UsageRecord:
        """Record usage event for metered billing"""
        
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        # Get active subscription
        subscription = await self.get_active_subscription(tenant_id)
        if not subscription:
            raise ValueError("No active subscription for tenant")
        
        # Create usage record
        usage_record = UsageRecord(
            tenant_id=tenant_id,
            subscription_id=subscription.id,
            metric_type=metric_type,
            quantity=quantity,
            usage_date=timestamp,
            billing_period_start=subscription.current_period_start,
            billing_period_end=subscription.current_period_end
        )
        
        # Store in database
        await self.usage_repository.create(usage_record)
        
        # Update real-time usage cache
        cache_key = f"usage:{tenant_id}:{metric_type}:{timestamp.strftime('%Y-%m')}"
        await self.redis_client.incr(cache_key, quantity)
        await self.redis_client.expire(cache_key, 86400 * 32)  # 32-day expiry
        
        # Report to Stripe for billing
        if subscription.stripe_subscription_id:
            await self.report_usage_to_stripe(subscription, metric_type, quantity, timestamp)
        
        return usage_record
```

**API Usage Tracking Middleware:**
```python
# Automatic API call tracking
async def api_usage_tracking_middleware(request: Request, call_next):
    """Track API usage for billing"""
    
    tenant_id = request.state.tenant.id
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Record API call usage
    if response.status_code < 500:  # Only count successful calls
        await billing_service.record_usage(
            tenant_id=tenant_id,
            metric_type=UsageMetricType.API_CALLS,
            quantity=1
        )
    
    # Track response time for analytics
    response_time = time.time() - start_time
    await analytics_service.record_response_time(tenant_id, response_time)
    
    return response
```

#### Batch Usage Reporting

**Daily Usage Aggregation:**
```python
# Daily batch reporting to Stripe
async def aggregate_daily_usage():
    """Aggregate and report daily usage to Stripe"""
    
    yesterday = datetime.utcnow().date() - timedelta(days=1)
    
    # Get all active subscriptions
    active_subscriptions = await subscription_repository.get_active_subscriptions()
    
    for subscription in active_subscriptions:
        # Aggregate usage by metric type
        usage_aggregates = await usage_repository.get_daily_aggregates(
            subscription.id, yesterday
        )
        
        # Report to Stripe
        for metric_type, quantity in usage_aggregates.items():
            if quantity > 0:
                await stripe_service.create_usage_record(
                    subscription.stripe_subscription_id,
                    metric_type,
                    quantity,
                    yesterday
                )
```

### Enterprise Invoicing

#### Custom Invoice Generation

**Enterprise Invoice Creation:**
```bash
curl -X POST "https://api.leanvibe.ai/v1/billing/invoices" \
  -H "Authorization: Bearer tenant-admin-token" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "enterprise-tenant-uuid",
    "subscription_id": "sub-uuid-here",
    "billing_period": {
      "start": "2024-01-01T00:00:00Z", 
      "end": "2024-01-31T23:59:59Z"
    },
    "line_items": [
      {
        "description": "Enterprise Plan - January 2024",
        "quantity": 1,
        "unit_price": 80000,
        "total": 80000,
        "type": "subscription"
      },
      {
        "description": "Storage Overage - 250 GB",
        "quantity": 250,
        "unit_price": 300,
        "total": 75000,
        "type": "usage_overage",
        "metadata": {
          "metric_type": "storage_gb",
          "included_amount": 1000,
          "total_usage": 1250
        }
      },
      {
        "description": "Professional Services - Implementation",
        "quantity": 40,
        "unit_price": 15000,
        "total": 600000,
        "type": "professional_services"
      }
    ],
    "subtotal": 755000,
    "tax_amount": 60400,  // 8% sales tax
    "total": 815400,
    "due_date": "2024-02-15T00:00:00Z",
    "payment_terms": "Net 15",
    "purchase_order_number": "ENT-2024-001"
  }'
```

#### Invoice Customization & Branding

**Enterprise Invoice Branding:**
```json
{
  "invoice_branding": {
    "company_logo": "https://cdn.leanvibe.ai/branding/acme-corp-logo.png",
    "primary_color": "#007ACC",
    "company_name": "LeanVibe Technologies Inc.",
    "company_address": {
      "line1": "123 Technology Drive",
      "line2": "Suite 100",
      "city": "San Francisco",
      "state": "CA",
      "postal_code": "94105",
      "country": "US"
    },
    "contact_info": {
      "phone": "+1 (555) 123-4567",
      "email": "billing@leanvibe.ai",
      "website": "https://leanvibe.ai"
    },
    "payment_instructions": [
      "Payment due within 15 days of invoice date",
      "Wire transfer information available upon request",
      "ACH payments accepted for US customers"
    ]
  }
}
```

### Payment Processing

#### Enterprise Payment Method Management

**Add Corporate Credit Card:**
```bash
curl -X POST "https://api.leanvibe.ai/v1/billing/payment-methods" \
  -H "Authorization: Bearer tenant-admin-token" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "card",
    "stripe_payment_method_id": "pm_enterprise_card_id",
    "metadata": {
      "card_type": "corporate",
      "cardholder_name": "Acme Corporation",
      "billing_address": {
        "line1": "123 Enterprise Blvd",
        "city": "San Francisco", 
        "state": "CA",
        "postal_code": "94105",
        "country": "US"
      }
    },
    "set_as_default": true
  }'
```

**Configure ACH/Bank Transfer:**
```bash
curl -X POST "https://api.leanvibe.ai/v1/billing/payment-methods" \
  -H "Authorization: Bearer tenant-admin-token" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "bank_account",
    "stripe_payment_method_id": "pm_bank_account_id",
    "metadata": {
      "account_type": "checking",
      "bank_name": "First National Bank",
      "account_holder_type": "company"
    }
  }'
```

#### Sophisticated Dunning Management

**Enterprise Dunning Configuration:**
```python
# Advanced dunning management for enterprise customers
class EnterpriseDunningManager:
    def __init__(self):
        self.dunning_schedules = {
            "enterprise": {
                "grace_period_days": 7,
                "retry_schedule": [1, 7, 14, 21],  # Days after failure
                "notification_schedule": [0, 3, 7, 14, 21],  # Notification days
                "escalation_contacts": ["billing", "admin", "account_manager"],
                "service_degradation_after_days": 30,
                "suspension_after_days": 45
            },
            "team": {
                "grace_period_days": 3,
                "retry_schedule": [1, 3, 7, 14],
                "notification_schedule": [0, 3, 7, 14],
                "escalation_contacts": ["billing", "admin"],
                "service_degradation_after_days": 14,
                "suspension_after_days": 30
            }
        }
    
    async def handle_payment_failure(self, payment_failure_event):
        """Handle failed payment with enterprise-specific logic"""
        
        subscription = await self.get_subscription(payment_failure_event.subscription_id)
        tenant = await self.get_tenant(subscription.tenant_id)
        
        dunning_config = self.dunning_schedules.get(
            tenant.plan.value, 
            self.dunning_schedules["team"]
        )
        
        # Send immediate notification
        await self.send_payment_failure_notification(
            subscription, 
            dunning_config["escalation_contacts"]
        )
        
        # Schedule retry attempts
        for retry_day in dunning_config["retry_schedule"]:
            await self.schedule_payment_retry(
                subscription.id,
                retry_date=datetime.utcnow() + timedelta(days=retry_day)
            )
        
        # Schedule service actions if enterprise
        if tenant.plan == TenantPlan.ENTERPRISE:
            await self.schedule_account_manager_outreach(
                tenant.id, 
                outreach_date=datetime.utcnow() + timedelta(days=1)
            )
```

## Tax Management & Compliance

### Automated Tax Calculation

#### US Sales Tax Configuration

**Sales Tax Setup:**
```python
# US Sales Tax configuration
US_SALES_TAX_CONFIG = {
    "tax_type": "sales_tax",
    "nexus_states": ["CA", "NY", "TX", "WA", "FL"],
    "tax_rates": {
        "CA": 8.25,   # California state + average local
        "NY": 8.00,   # New York state + average local  
        "TX": 6.25,   # Texas state + average local
        "WA": 6.50,   # Washington state + average local
        "FL": 6.00    # Florida state + average local
    },
    "tax_exempt_customers": [
        "non_profit_organizations",
        "government_entities",
        "resellers_with_valid_certificate"
    ],
    "threshold_amounts": {
        "CA": 50000,   # $500 annual threshold
        "NY": 30000,   # $300 annual threshold
        "TX": 50000    # $500 annual threshold
    }
}
```

#### EU VAT Configuration

**VAT Setup:**
```python
# European VAT configuration
EU_VAT_CONFIG = {
    "tax_type": "vat",
    "vat_rates": {
        "DE": 19.0,   # Germany
        "FR": 20.0,   # France
        "GB": 20.0,   # United Kingdom
        "IE": 23.0,   # Ireland
        "NL": 21.0,   # Netherlands
        "ES": 21.0,   # Spain
        "IT": 22.0    # Italy
    },
    "reverse_charge_threshold": 10000,  # €100.00
    "moss_reporting": True,
    "digital_services_place_of_supply": "customer_location"
}
```

#### Real-Time Tax Calculation API

**Tax Calculation Service:**
```bash
curl -X POST "https://api.leanvibe.ai/v1/billing/tax/calculate" \
  -H "Authorization: Bearer tenant-admin-token" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 80000,  // $800.00 in cents
    "currency": "USD",
    "customer_address": {
      "line1": "123 Enterprise Blvd",
      "city": "San Francisco",
      "state": "CA", 
      "postal_code": "94105",
      "country": "US"
    },
    "product_type": "saas_subscription",
    "tax_exempt": false
  }'
```

**Response:**
```json
{
  "subtotal": 80000,
  "tax_amount": 6600,    // 8.25% CA sales tax
  "tax_rate": 8.25,
  "total": 86600,
  "tax_breakdown": [
    {
      "type": "state_sales_tax",
      "rate": 7.25,
      "amount": 5800,
      "jurisdiction": "California State"
    },
    {
      "type": "local_sales_tax", 
      "rate": 1.00,
      "amount": 800,
      "jurisdiction": "San Francisco County"
    }
  ],
  "compliance_note": "California sales tax applies to SaaS subscriptions"
}
```

## Analytics & Reporting

### Revenue Analytics Dashboard

#### Monthly Recurring Revenue (MRR) Tracking

**MRR Analytics API:**
```bash
curl -X GET "https://api.leanvibe.ai/v1/billing/analytics/mrr" \
  -H "Authorization: Bearer admin-token" \
  -G -d "start_date=2024-01-01" -d "end_date=2024-12-31"
```

**Comprehensive MRR Response:**
```json
{
  "period": {
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-12-31T23:59:59Z"
  },
  "mrr_metrics": {
    "current_mrr": 485000,      // $4,850 current MRR
    "new_mrr": 68000,           // $680 from new customers
    "expansion_mrr": 24000,     // $240 from upgrades
    "contraction_mrr": -8000,   // -$80 from downgrades
    "churn_mrr": -15000,        // -$150 from cancellations
    "net_new_mrr": 69000,       // $690 net growth
    "mrr_growth_rate": 16.6     // 16.6% growth rate
  },
  "arr_projection": 5820000,    // $58,200 ARR
  "by_plan_tier": {
    "developer": {
      "mrr": 125000,           // $1,250 MRR
      "subscriber_count": 250,
      "average_revenue_per_user": 500,  // $5.00 ARPU
      "churn_rate": 3.2
    },
    "team": {
      "mrr": 240000,           // $2,400 MRR  
      "subscriber_count": 120,
      "average_revenue_per_user": 2000, // $20.00 ARPU
      "churn_rate": 1.8
    },
    "enterprise": {
      "mrr": 120000,           // $1,200 MRR
      "subscriber_count": 15,
      "average_revenue_per_user": 8000, // $80.00 ARPU
      "churn_rate": 0.5
    }
  },
  "cohort_analysis": {
    "jan_2024": {
      "initial_customers": 45,
      "retained_customers": 43,
      "retention_rate": 95.6,
      "revenue_retention": 108.2  // Revenue expansion
    },
    "feb_2024": {
      "initial_customers": 52,
      "retained_customers": 49,
      "retention_rate": 94.2,
      "revenue_retention": 103.8
    }
  }
}
```

#### Customer Lifetime Value Analysis

**CLV Analytics API:**
```bash
curl -X GET "https://api.leanvibe.ai/v1/billing/analytics/clv" \
  -H "Authorization: Bearer admin-token" \
  -G -d "segment=by_plan" -d "period=12months"
```

**CLV Response:**
```json
{
  "customer_lifetime_value": {
    "overall": {
      "average_clv": 2850,        // $28.50 average CLV
      "median_clv": 1920,         // $19.20 median CLV
      "clv_to_cac_ratio": 3.8     // 3.8:1 CLV to CAC ratio
    },
    "by_plan": {
      "developer": {
        "average_clv": 1200,      // $12.00 average CLV
        "average_lifespan_months": 24,
        "monthly_churn_rate": 3.2,
        "customer_acquisition_cost": 180  // $1.80 CAC
      },
      "team": {
        "average_clv": 3600,      // $36.00 average CLV
        "average_lifespan_months": 18,
        "monthly_churn_rate": 1.8,
        "customer_acquisition_cost": 420  // $4.20 CAC
      },
      "enterprise": {
        "average_clv": 19200,     // $192.00 average CLV
        "average_lifespan_months": 24,
        "monthly_churn_rate": 0.5,
        "customer_acquisition_cost": 2400  // $24.00 CAC
      }
    },
    "predictive_metrics": {
      "projected_3_month_churn": 2.1,
      "high_risk_customers": 28,
      "expansion_opportunities": 45
    }
  }
}
```

### Usage Analytics

#### Comprehensive Usage Reporting

**Usage Analytics API:**
```bash
curl -X GET "https://api.leanvibe.ai/v1/billing/analytics/usage" \
  -H "Authorization: Bearer admin-token" \
  -G -d "tenant_id=all" -d "period=30d" -d "breakdown=daily"
```

**Usage Analytics Response:**
```json
{
  "usage_summary": {
    "total_api_calls": 2450000,      // 2.45M API calls
    "total_storage_gb": 18500,       // 18.5TB storage
    "total_ai_requests": 145000,     // 145K AI requests
    "active_users": 890,             // 890 active users
    "average_concurrent_sessions": 156
  },
  "usage_trends": {
    "api_calls_growth": 18.5,        // 18.5% month-over-month
    "storage_growth": 12.3,          // 12.3% month-over-month
    "user_growth": 8.7               // 8.7% month-over-month
  },
  "by_tenant_tier": {
    "developer": {
      "total_tenants": 250,
      "average_api_calls_per_tenant": 8500,
      "quota_utilization": 85.0,     // 85% of quota used
      "overage_customers": 42        // 42 customers over quota
    },
    "team": {
      "total_tenants": 120,
      "average_api_calls_per_tenant": 75000,
      "quota_utilization": 75.0,     // 75% of quota used
      "overage_customers": 18        // 18 customers over quota
    },
    "enterprise": {
      "total_tenants": 15,
      "average_api_calls_per_tenant": 450000,
      "quota_utilization": 45.0,     // 45% of quota used (unlimited)
      "overage_customers": 0         // No quota limits
    }
  },
  "overage_revenue": {
    "total_overage_revenue": 28500,  // $285 in overages
    "api_call_overages": 18200,     // $182 from API overages
    "storage_overages": 10300       // $103 from storage overages
  }
}
```

## Enterprise Billing Features

### Custom Pricing & Contracts

#### Enterprise Contract Management

**Create Custom Enterprise Contract:**
```bash
curl -X POST "https://api.leanvibe.ai/v1/billing/contracts" \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "enterprise-customer-uuid",
    "contract_type": "enterprise_annual",
    "contract_terms": {
      "contract_value": 960000,       // $9,600 annual contract
      "payment_schedule": "annual",
      "payment_terms": "Net 30",
      "auto_renewal": true,
      "renewal_terms": "annual",
      "custom_pricing": {
        "base_monthly_price": 60000,  // $600/month ($7,200/year)
        "included_users": 200,
        "additional_user_price": 2000,  // $20 per additional user
        "included_storage_gb": 2000,   // 2TB included
        "additional_storage_gb_price": 200,  // $2 per GB over 2TB
        "included_api_calls": 5000000, // 5M API calls included
        "additional_api_call_price": 0.5    // $0.005 per additional call
      },
      "volume_discounts": [
        {
          "threshold": 500000,   // $5,000 annual
          "discount_percentage": 5
        },
        {
          "threshold": 1000000,  // $10,000 annual
          "discount_percentage": 10
        },
        {
          "threshold": 2000000,  // $20,000 annual
          "discount_percentage": 15
        }
      ],
      "service_level_agreement": {
        "uptime_guarantee": 99.95,
        "response_time_guarantee": 200,  // ms
        "support_response_time": 1,      // hours
        "dedicated_support": true,
        "monthly_business_review": true
      }
    },
    "effective_date": "2024-01-01T00:00:00Z",
    "expiration_date": "2024-12-31T23:59:59Z",
    "signed_by": {
      "customer": {
        "name": "John Smith",
        "title": "CTO",
        "email": "john.smith@enterprise-customer.com",
        "signed_date": "2023-12-15T00:00:00Z"
      },
      "leanvibe": {
        "name": "Sarah Johnson",
        "title": "VP Sales",
        "email": "sarah.johnson@leanvibe.ai",
        "signed_date": "2023-12-20T00:00:00Z"
      }
    }
  }'
```

### Multi-Entity Billing

#### Corporate Hierarchy Billing

**Multi-Entity Setup:**
```json
{
  "corporate_billing_structure": {
    "parent_entity": {
      "tenant_id": "parent-corp-uuid",
      "legal_name": "Global Corp Holdings Inc.",
      "billing_responsibility": true,
      "consolidated_invoicing": true,
      "payment_terms": "Net 60"
    },
    "child_entities": [
      {
        "tenant_id": "subsidiary-us-uuid",
        "legal_name": "Global Corp USA LLC",
        "cost_center": "US-Operations",
        "cost_allocation_percentage": 45,
        "budget_cap": 500000,  // $5,000 monthly cap
        "billing_contact": "finance-us@globalcorp.com"
      },
      {
        "tenant_id": "subsidiary-eu-uuid",
        "legal_name": "Global Corp Europe GmbH",
        "cost_center": "EU-Operations", 
        "cost_allocation_percentage": 35,
        "budget_cap": 400000,  // $4,000 monthly cap
        "billing_contact": "finance-eu@globalcorp.com"
      },
      {
        "tenant_id": "subsidiary-apac-uuid",
        "legal_name": "Global Corp Asia Pte Ltd",
        "cost_center": "APAC-Operations",
        "cost_allocation_percentage": 20,
        "budget_cap": 300000,  // $3,000 monthly cap
        "billing_contact": "finance-apac@globalcorp.com"
      }
    ],
    "consolidated_reporting": {
      "monthly_consolidated_invoice": true,
      "cost_center_breakdown": true,
      "department_allocation": true,
      "budget_tracking": true,
      "variance_reporting": true
    }
  }
}
```

#### Department Cost Allocation

**Cost Center Management:**
```python
# Cost allocation service implementation  
class CostAllocationService:
    async def allocate_monthly_costs(self, parent_tenant_id: UUID, billing_month: date):
        """Allocate costs across departments and cost centers"""
        
        # Get consolidated billing data
        monthly_costs = await self.get_consolidated_costs(parent_tenant_id, billing_month)
        
        # Get allocation rules
        allocation_rules = await self.get_allocation_rules(parent_tenant_id)
        
        cost_allocations = []
        
        for child_entity in allocation_rules.child_entities:
            # Calculate allocated costs
            allocated_amount = monthly_costs.total * (
                child_entity.cost_allocation_percentage / 100
            )
            
            # Apply budget caps
            if allocated_amount > child_entity.budget_cap:
                excess_amount = allocated_amount - child_entity.budget_cap
                allocated_amount = child_entity.budget_cap
                
                # Notify of budget overrun
                await self.notify_budget_overrun(
                    child_entity, excess_amount, billing_month
                )
            
            # Create cost allocation record
            cost_allocation = CostAllocation(
                parent_tenant_id=parent_tenant_id,
                child_tenant_id=child_entity.tenant_id,
                billing_month=billing_month,
                allocated_amount=allocated_amount,
                cost_center=child_entity.cost_center,
                allocation_percentage=child_entity.cost_allocation_percentage
            )
            
            cost_allocations.append(cost_allocation)
        
        # Store allocations
        await self.cost_allocation_repository.bulk_create(cost_allocations)
        
        # Generate department reports
        await self.generate_department_reports(parent_tenant_id, cost_allocations)
        
        return cost_allocations
```

## Enterprise Support

### Implementation Services

**Enterprise Billing Setup (8-12 hours):**
- Complete Stripe integration configuration
- Custom pricing and contract setup
- Usage tracking implementation and validation
- Tax compliance configuration for all operating jurisdictions
- Multi-entity billing structure implementation
- Invoice branding and customization

**Revenue Operations Consultation (4-6 hours):**
- Revenue recognition automation setup
- Subscription lifecycle optimization
- Dunning management configuration
- Analytics dashboard customization
- KPI tracking and alerting setup

### Ongoing Enterprise Support

**Billing Operations Support:**
- **Response Time**: <2 hours for billing system issues
- **Escalation**: Direct access to billing engineering team
- **Monitoring**: 24/7 billing system monitoring and alerting
- **Monthly Reviews**: Revenue metrics and optimization recommendations

**Compliance & Reporting:**
- **Tax Compliance**: Automated tax calculation and reporting
- **Revenue Recognition**: GAAP/IFRS compliant revenue tracking
- **Audit Support**: Complete audit trails and documentation
- **Custom Reporting**: Enterprise-specific reporting and dashboards

### Contact Enterprise Billing Support

**Billing Technical Support:**
- **Email**: billing-support@leanvibe.ai
- **Phone**: +1 (555) 123-4567 ext. 3
- **Emergency**: +1 (555) 123-4567 ext. 911
- **Slack**: #enterprise-billing in LeanVibe Community

**Revenue Operations:**
- **Email**: revenue-ops@leanvibe.ai
- **Scheduling**: [Book Revenue Review](https://calendly.com/leanvibe/revenue-review)
- **Documentation**: [Enterprise Billing Knowledge Base](https://docs.leanvibe.ai/enterprise/billing)

**Compliance & Finance:**
- **Email**: finance@leanvibe.ai  
- **Tax Questions**: tax-compliance@leanvibe.ai
- **Audit Support**: audit-support@leanvibe.ai

---

**Ready to implement enterprise billing?** Contact our billing specialists for personalized setup assistance and ensure seamless payment processing, compliance, and revenue optimization for your organization.

This comprehensive guide provides enterprise-grade billing implementation with the sophistication, accuracy, and compliance features required for large-scale SaaS revenue operations.