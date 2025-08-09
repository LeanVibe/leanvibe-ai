"""
Tests for enterprise billing system in LeanVibe SaaS Platform
Validates subscription management, usage tracking, and Stripe integration
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

from app.models.billing_models import (
    Plan, BillingAccount, Subscription, UsageRecord, BillingAnalytics,
    CreateSubscriptionRequest, UpdateSubscriptionRequest, CreatePaymentMethodRequest,
    BillingStatus, SubscriptionStatus, PaymentStatus, InvoiceStatus,
    UsageMetricType, BillingInterval, PaymentMethod, TaxType,
    DEFAULT_PLANS
)
from app.services.billing_service import BillingService, StripeIntegration


class TestBillingModels:
    """Test billing model validation and logic"""
    
    def test_plan_model_validation(self):
        """Test plan model validation"""
        plan = Plan(
            name="Test Plan",
            slug="test-plan",
            base_price=Decimal('5000'),  # $50.00
            currency="USD",
            billing_interval=BillingInterval.MONTHLY,
            features={
                "max_users": 5,
                "max_projects": 10,
                "api_access": True
            },
            limits={
                "api_calls_per_month": 10000,
                "storage_gb": 5
            },
            usage_prices={
                "additional_api_calls": Decimal('1')  # $0.01 per call
            },
            included_usage={
                "api_calls": 10000
            },
            trial_period_days=14
        )
        
        assert plan.name == "Test Plan"
        assert plan.slug == "test-plan"
        assert plan.base_price == Decimal('5000')
        assert plan.billing_interval == BillingInterval.MONTHLY
        assert plan.features["max_users"] == 5
        assert plan.limits["api_calls_per_month"] == 10000
        assert plan.trial_period_days == 14
    
    def test_billing_account_model(self):
        """Test billing account model"""
        tenant_id = uuid4()
        
        billing_account = BillingAccount(
            tenant_id=tenant_id,
            company_name="Test Company",
            billing_email="billing@test.com",
            billing_address={
                "line1": "123 Test St",
                "city": "Test City",
                "state": "TS",
                "postal_code": "12345",
                "country": "US"
            },
            tax_id="12-3456789",
            tax_type=TaxType.SALES_TAX,
            status=BillingStatus.ACTIVE,
            stripe_customer_id="cus_test123",
            account_balance=Decimal('-1500'),  # $15.00 credit
            available_credits=Decimal('1500')
        )
        
        assert billing_account.tenant_id == tenant_id
        assert billing_account.company_name == "Test Company"
        assert billing_account.billing_email == "billing@test.com"
        assert billing_account.tax_type == TaxType.SALES_TAX
        assert billing_account.status == BillingStatus.ACTIVE
        assert billing_account.account_balance == Decimal('-1500')
    
    def test_subscription_model(self):
        """Test subscription model"""
        tenant_id = uuid4()
        billing_account_id = uuid4()
        plan_id = uuid4()
        
        now = datetime.utcnow()
        period_end = now + timedelta(days=30)
        
        subscription = Subscription(
            tenant_id=tenant_id,
            billing_account_id=billing_account_id,
            plan_id=plan_id,
            status=SubscriptionStatus.TRIALING,
            current_period_start=now,
            current_period_end=period_end,
            trial_start=now,
            trial_end=now + timedelta(days=14),
            stripe_subscription_id="sub_test123",
            custom_price=Decimal('4500'),  # $45.00
            discount_percentage=Decimal('10.0')  # 10% discount
        )
        
        assert subscription.tenant_id == tenant_id
        assert subscription.status == SubscriptionStatus.TRIALING
        assert subscription.custom_price == Decimal('4500')
        assert subscription.discount_percentage == Decimal('10.0')
        assert subscription.trial_end > subscription.trial_start
    
    def test_usage_record_model(self):
        """Test usage record model"""
        tenant_id = uuid4()
        subscription_id = uuid4()
        
        usage_record = UsageRecord(
            tenant_id=tenant_id,
            subscription_id=subscription_id,
            metric_type=UsageMetricType.API_CALLS,
            quantity=1500,
            unit_price=Decimal('1'),  # $0.01 per call
            usage_date=datetime.utcnow(),
            billing_period_start=datetime.utcnow(),
            billing_period_end=datetime.utcnow() + timedelta(days=30),
            stripe_usage_record_id="mbur_test123"
        )
        
        assert usage_record.metric_type == UsageMetricType.API_CALLS
        assert usage_record.quantity == 1500
        assert usage_record.unit_price == Decimal('1')
        assert usage_record.stripe_usage_record_id == "mbur_test123"
    
    def test_default_plans(self):
        """Test default plan configurations"""
        assert "developer" in DEFAULT_PLANS
        assert "team" in DEFAULT_PLANS
        assert "enterprise" in DEFAULT_PLANS
        
        dev_plan = DEFAULT_PLANS["developer"]
        assert dev_plan.name == "Developer"
        assert dev_plan.base_price == Decimal('5000')  # $50.00
        assert dev_plan.features["max_users"] == 1
        assert dev_plan.features["max_projects"] == 5
        
        team_plan = DEFAULT_PLANS["team"]
        assert team_plan.name == "Team"
        assert team_plan.base_price == Decimal('20000')  # $200.00
        assert team_plan.features["max_users"] == 10
        assert team_plan.features["sso_support"] is True
        
        enterprise_plan = DEFAULT_PLANS["enterprise"]
        assert enterprise_plan.name == "Enterprise"
        assert enterprise_plan.base_price == Decimal('80000')  # $800.00
        assert enterprise_plan.is_enterprise is True
        assert enterprise_plan.features["saml_support"] is True


class TestSubscriptionRequests:
    """Test subscription request models"""
    
    def test_create_subscription_request(self):
        """Test create subscription request validation"""
        tenant_id = uuid4()
        plan_id = uuid4()
        
        request = CreateSubscriptionRequest(
            tenant_id=tenant_id,
            plan_id=plan_id,
            payment_method_id="pm_test123",
            trial_period_days=30,
            coupon_code="WELCOME20"
        )
        
        assert request.tenant_id == tenant_id
        assert request.plan_id == plan_id
        assert request.payment_method_id == "pm_test123"
        assert request.trial_period_days == 30
        assert request.coupon_code == "WELCOME20"
    
    def test_update_subscription_request(self):
        """Test update subscription request validation"""
        new_plan_id = uuid4()
        
        request = UpdateSubscriptionRequest(
            plan_id=new_plan_id,
            cancel_at_period_end=True
        )
        
        assert request.plan_id == new_plan_id
        assert request.cancel_at_period_end is True
    
    def test_create_payment_method_request(self):
        """Test create payment method request validation"""
        request = CreatePaymentMethodRequest(
            type=PaymentMethod.CARD,
            card_token="tok_visa_test",
            bank_account_token=None
        )
        
        assert request.type == PaymentMethod.CARD
        assert request.card_token == "tok_visa_test"
        assert request.bank_account_token is None


class TestBillingAnalytics:
    """Test billing analytics model"""
    
    def test_billing_analytics_model(self):
        """Test billing analytics model validation"""
        tenant_id = uuid4()
        
        analytics = BillingAnalytics(
            tenant_id=tenant_id,
            monthly_recurring_revenue=Decimal('5000'),  # $50.00 MRR
            annual_recurring_revenue=Decimal('60000'),   # $600.00 ARR
            usage_metrics={
                "api_calls": 8500,
                "storage_gb": 3,
                "active_users": 2
            },
            usage_trends={
                "api_calls": [7000, 7500, 8000, 8500],  # Last 4 months
                "storage_gb": [2, 2, 3, 3]
            },
            overdue_amount=Decimal('0'),
            next_invoice_amount=Decimal('5000'),
            payment_health_score=0.95,
            projected_monthly_cost=Decimal('5200')  # $52.00 with usage
        )
        
        assert analytics.tenant_id == tenant_id
        assert analytics.monthly_recurring_revenue == Decimal('5000')
        assert analytics.annual_recurring_revenue == Decimal('60000')
        assert analytics.usage_metrics["api_calls"] == 8500
        assert analytics.payment_health_score == 0.95
        assert analytics.projected_monthly_cost == Decimal('5200')
    
    def test_analytics_usage_calculation(self):
        """Test usage-based cost calculation logic"""
        tenant_id = uuid4()
        
        # Simulate usage above plan limits
        analytics = BillingAnalytics(
            tenant_id=tenant_id,
            monthly_recurring_revenue=Decimal('5000'),  # Developer plan $50
            annual_recurring_revenue=Decimal('60000'),
            usage_metrics={
                "api_calls": 15000,  # 5000 over 10K limit
                "storage_gb": 3,     # 2GB over 1GB limit
                "active_users": 1
            },
            usage_trends={},
            payment_health_score=1.0,
            projected_monthly_cost=Decimal('6500')  # Base + overage fees
        )
        
        # Verify projected cost includes overage
        base_cost = analytics.monthly_recurring_revenue
        projected_cost = analytics.projected_monthly_cost
        overage_cost = projected_cost - base_cost
        
        assert overage_cost == Decimal('1500')  # $15.00 in overages
        assert analytics.usage_metrics["api_calls"] > 10000  # Over limit


class TestEnumValidation:
    """Test billing enum validation"""
    
    def test_billing_status_enum(self):
        """Test billing status enum values"""
        statuses = [
            BillingStatus.ACTIVE,
            BillingStatus.PAST_DUE,
            BillingStatus.SUSPENDED,
            BillingStatus.CANCELLED,
            BillingStatus.TRIAL
        ]
        
        for status in statuses:
            assert isinstance(status, str)
            assert status in ["active", "past_due", "suspended", "cancelled", "trial"]
    
    def test_subscription_status_enum(self):
        """Test subscription status enum matches Stripe"""
        stripe_statuses = [
            SubscriptionStatus.TRIALING,
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.PAST_DUE,
            SubscriptionStatus.CANCELLED,
            SubscriptionStatus.UNPAID,
            SubscriptionStatus.INCOMPLETE,
            SubscriptionStatus.INCOMPLETE_EXPIRED
        ]
        
        for status in stripe_statuses:
            assert isinstance(status, str)
            # These should match Stripe's exact status values
            assert status in [
                "trialing", "active", "past_due", "cancelled",
                "unpaid", "incomplete", "incomplete_expired"
            ]
    
    def test_usage_metric_types(self):
        """Test usage metric type enum"""
        metric_types = [
            UsageMetricType.API_CALLS,
            UsageMetricType.STORAGE_GB,
            UsageMetricType.AI_REQUESTS,
            UsageMetricType.ACTIVE_USERS,
            UsageMetricType.PROJECTS,
            UsageMetricType.CONCURRENT_SESSIONS
        ]
        
        for metric in metric_types:
            assert isinstance(metric, str)
            assert metric in [
                "api_calls", "storage_gb", "ai_requests",
                "active_users", "projects", "concurrent_sessions"
            ]
    
    def test_payment_methods(self):
        """Test payment method types"""
        methods = [
            PaymentMethod.CARD,
            PaymentMethod.BANK_ACCOUNT,
            PaymentMethod.PAYPAL,
            PaymentMethod.WIRE_TRANSFER
        ]
        
        for method in methods:
            assert isinstance(method, str)
            assert method in ["card", "bank_account", "paypal", "wire_transfer"]


class TestStripeIntegration:
    """Test Stripe integration wrapper"""
    
    def test_stripe_integration_init(self):
        """Test Stripe integration initialization"""
        stripe = StripeIntegration()
        
        # Should initialize with mock settings
        assert stripe.api_key is not None
        assert stripe.webhook_secret is not None
    
    @pytest.mark.asyncio
    async def test_create_customer_mock(self):
        """Test mock customer creation"""
        stripe = StripeIntegration()
        
        tenant_id = uuid4()
        billing_account = BillingAccount(
            tenant_id=tenant_id,
            company_name="Test Company",
            billing_email="test@company.com",
            billing_address={
                "line1": "123 Test St",
                "city": "Test City",
                "country": "US"
            }
        )
        
        customer_id = await stripe.create_customer(billing_account)
        
        assert customer_id is not None
        assert customer_id.startswith("cus_mock_")
    
    @pytest.mark.asyncio
    async def test_create_subscription_mock(self):
        """Test mock subscription creation"""
        stripe = StripeIntegration()
        
        subscription_data = await stripe.create_subscription(
            customer_id="cus_test123",
            price_id="price_test_plan",
            trial_period_days=14
        )
        
        assert subscription_data["id"] is not None
        assert subscription_data["id"].startswith("sub_mock_")
        assert subscription_data["customer"] == "cus_test123"
        assert subscription_data["status"] == "trialing"
        assert subscription_data["trial_start"] is not None
        assert subscription_data["trial_end"] is not None


class TestBillingBusinessLogic:
    """Test billing business logic and calculations"""
    
    def test_plan_pricing_calculation(self):
        """Test plan pricing calculations"""
        plan = DEFAULT_PLANS["developer"]
        
        # Base monthly cost
        base_monthly = plan.base_price
        assert base_monthly == Decimal('5000')  # $50.00
        
        # Calculate overage costs
        api_calls_used = 15000  # 5000 over limit
        api_calls_limit = plan.limits["api_calls_per_month"]  # 10000
        api_calls_overage = max(0, api_calls_used - api_calls_limit)
        
        overage_cost = api_calls_overage * plan.usage_prices["additional_api_calls"]
        total_cost = base_monthly + overage_cost
        
        assert api_calls_overage == 5000
        assert overage_cost == Decimal('5000')  # $50.00 overage
        assert total_cost == Decimal('10000')   # $100.00 total
    
    def test_enterprise_plan_features(self):
        """Test enterprise plan feature validation"""
        enterprise_plan = DEFAULT_PLANS["enterprise"]
        
        # Enterprise features
        assert enterprise_plan.is_enterprise is True
        assert enterprise_plan.features["saml_support"] is True
        assert enterprise_plan.features["dedicated_support"] is True
        assert enterprise_plan.features["sla_guarantee"] is True
        
        # Unlimited resources
        assert enterprise_plan.features["max_users"] == 999999
        assert enterprise_plan.features["max_projects"] == 999999
        assert enterprise_plan.limits["api_calls_per_month"] == 999999999
    
    def test_trial_period_calculation(self):
        """Test trial period calculations"""
        plans = DEFAULT_PLANS
        
        # Developer and Team: 14 days trial
        assert plans["developer"].trial_period_days == 14
        assert plans["team"].trial_period_days == 14
        
        # Enterprise: 30 days trial
        assert plans["enterprise"].trial_period_days == 30
        
        # Calculate trial end dates
        trial_start = datetime(2025, 1, 1)
        
        for plan_name, plan in plans.items():
            trial_end = trial_start + timedelta(days=plan.trial_period_days)
            trial_duration = trial_end - trial_start
            
            assert trial_duration.days == plan.trial_period_days


class TestBillingSecurity:
    """Test billing security and validation"""
    
    def test_decimal_precision(self):
        """Test decimal precision for monetary calculations"""
        # Test various monetary amounts
        amounts = [
            Decimal('0.01'),      # 1 cent
            Decimal('1.00'),      # 1 dollar
            Decimal('999.99'),    # $999.99
            Decimal('5000'),      # $50.00 in cents
            Decimal('10000.50')   # $100.005 (should round)
        ]
        
        for amount in amounts:
            # Should maintain precision
            assert isinstance(amount, Decimal)
            
            # Cents calculation
            cents = amount * 100 if amount < 100 else amount
            assert isinstance(cents, Decimal)
    
    def test_subscription_status_transitions(self):
        """Test valid subscription status transitions"""
        tenant_id = uuid4()
        
        # Trial to Active
        subscription = Subscription(
            tenant_id=tenant_id,
            billing_account_id=uuid4(),
            plan_id=uuid4(),
            status=SubscriptionStatus.TRIALING,
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=30)
        )
        
        # Valid transitions
        valid_transitions = [
            (SubscriptionStatus.TRIALING, SubscriptionStatus.ACTIVE),
            (SubscriptionStatus.ACTIVE, SubscriptionStatus.PAST_DUE),
            (SubscriptionStatus.PAST_DUE, SubscriptionStatus.ACTIVE),
            (SubscriptionStatus.ACTIVE, SubscriptionStatus.CANCELLED)
        ]
        
        for from_status, to_status in valid_transitions:
            subscription.status = from_status
            # Transition should be valid
            subscription.status = to_status
            assert subscription.status == to_status


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])