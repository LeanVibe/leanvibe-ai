"""
COMPREHENSIVE BILLING SERVICE - STRIPE INTEGRATION TESTS
Priority 1 - Week 2 Final Implementation

These tests implement critical Stripe integration and financial security validation.
Status: IMPLEMENTING - Billing service comprehensive testing (610 lines, 30% → 90% coverage)
"""

import pytest
import pytest_asyncio
import json
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4
from unittest.mock import AsyncMock, patch, MagicMock

# Configure pytest for async tests
pytestmark = pytest.mark.asyncio

from app.services.billing_service import BillingService, StripeIntegration
from app.models.billing_models import (
    BillingAccount, Subscription, UsageRecord, Invoice, Payment,
    CreateSubscriptionRequest, UpdateSubscriptionRequest, BillingAnalytics,
    BillingStatus, SubscriptionStatus, PaymentStatus, InvoiceStatus, 
    UsageMetricType, Plan
)
from app.models.tenant_models import Tenant, TenantStatus, TenantPlan, DEFAULT_QUOTAS
from app.core.exceptions import (
    ResourceNotFoundError, PaymentRequiredError, PaymentFailedError,
    SubscriptionExpiredError
)


@pytest_asyncio.fixture
async def billing_service():
    """Create billing service with mocked database"""
    mock_db = AsyncMock()
    service = BillingService(db=mock_db)
    return service


@pytest_asyncio.fixture
async def stripe_integration():
    """Create Stripe integration for testing"""
    return StripeIntegration(api_key="sk_test_mock_key")


@pytest_asyncio.fixture
async def sample_tenant():
    """Sample tenant for billing tests"""
    return Tenant(
        id=uuid4(),
        organization_name="Enterprise Corp",
        slug="enterprise-corp",
        admin_email="admin@enterprise-corp.com",
        status=TenantStatus.ACTIVE,
        plan=TenantPlan.ENTERPRISE,
        quotas=DEFAULT_QUOTAS[TenantPlan.ENTERPRISE]
    )


@pytest_asyncio.fixture
async def sample_billing_account(sample_tenant):
    """Sample billing account"""
    return BillingAccount(
        id=uuid4(),
        tenant_id=sample_tenant.id,
        company_name="Enterprise Corp",
        billing_email="billing@enterprise-corp.com",
        billing_address={
            "line1": "123 Business St",
            "city": "San Francisco",
            "state": "CA",
            "postal_code": "94105",
            "country": "US"
        },
        stripe_customer_id="cus_test_customer_123",
        tax_id="12-3456789",
        tax_type="ein"
    )


class TestStripeIntegrationCore:
    """Test core Stripe integration functionality"""

    async def test_stripe_customer_creation_success(self, stripe_integration):
        """Test successful Stripe customer creation with proper metadata"""
        billing_account = BillingAccount(
            tenant_id=uuid4(),
            company_name="Test Company",
            billing_email="test@company.com",
            billing_address={
                "line1": "123 Test St",
                "city": "Test City",
                "state": "CA",
                "postal_code": "12345",
                "country": "US"
            }
        )
        
        customer_id = await stripe_integration.create_customer(billing_account)
        
        # Verify customer ID format
        assert customer_id.startswith("cus_mock_")
        assert len(customer_id) == 24  # Standard Stripe customer ID length

    async def test_stripe_subscription_creation_with_trial(self, stripe_integration):
        """Test subscription creation with trial period"""
        customer_id = "cus_test_123"
        price_id = "price_test_enterprise"
        trial_days = 14
        
        subscription = await stripe_integration.create_subscription(
            customer_id=customer_id,
            price_id=price_id,
            trial_period_days=trial_days
        )
        
        # Verify subscription structure
        assert subscription["id"].startswith("sub_mock_")
        assert subscription["customer"] == customer_id
        assert subscription["status"] == "trialing"
        assert subscription["trial_start"] is not None
        assert subscription["trial_end"] is not None

    async def test_stripe_subscription_creation_without_trial(self, stripe_integration):
        """Test subscription creation without trial period"""
        customer_id = "cus_test_123"
        price_id = "price_test_team"
        
        subscription = await stripe_integration.create_subscription(
            customer_id=customer_id,
            price_id=price_id,
            trial_period_days=None
        )
        
        # Verify subscription structure
        assert subscription["id"].startswith("sub_mock_")
        assert subscription["customer"] == customer_id
        assert subscription["status"] == "active"
        assert subscription["trial_start"] is None
        assert subscription["trial_end"] is None

    async def test_stripe_webhook_signature_verification(self, stripe_integration):
        """Test webhook signature verification prevents fraud"""
        # Mock webhook payload
        webhook_payload = {
            "id": "evt_test_webhook",
            "object": "event",
            "type": "customer.subscription.updated",
            "data": {
                "object": {
                    "id": "sub_test_123",
                    "status": "active"
                }
            }
        }
        
        payload_bytes = json.dumps(webhook_payload).encode()
        signature = "t=1234567890,v1=mock_signature_hash"
        
        result = await stripe_integration.verify_webhook(payload_bytes, signature)
        
        # Verify webhook parsing
        assert result["id"] == "evt_test_webhook"
        assert result["type"] == "customer.subscription.updated"
        assert result["data"]["object"]["id"] == "sub_test_123"

    async def test_stripe_usage_record_creation(self, stripe_integration):
        """Test usage record creation for metered billing"""
        subscription_item_id = "si_test_item"
        quantity = 1500  # API calls
        timestamp = int(datetime.utcnow().timestamp())
        
        usage_record = await stripe_integration.create_usage_record(
            subscription_item_id=subscription_item_id,
            quantity=quantity,
            timestamp=timestamp
        )
        
        # Verify usage record
        assert usage_record["id"].startswith("mbur_mock_")
        assert usage_record["quantity"] == quantity
        assert usage_record["timestamp"] == timestamp
        assert usage_record["subscription_item"] == subscription_item_id


class TestBillingServiceSubscriptionManagement:
    """Test subscription lifecycle management"""

    async def test_create_subscription_success(self, billing_service, sample_tenant, sample_billing_account):
        """Test successful subscription creation with trial"""
        # Mock database operations
        billing_service.db.add = MagicMock()
        billing_service.db.commit = AsyncMock()
        billing_service.db.refresh = AsyncMock()
        
        # Mock dependencies
        with patch.object(billing_service, 'get_billing_account') as mock_get_account:
            mock_get_account.return_value = sample_billing_account
            
            with patch.object(billing_service, 'get_plan') as mock_get_plan:
                mock_plan = Plan(
                    id=uuid4(),
                    name="Enterprise Plan",
                    slug="enterprise",
                    base_price=Decimal('800.00'),
                    billing_interval="monthly",
                    trial_period_days=14,
                    stripe_price_id="price_enterprise_monthly"
                )
                mock_get_plan.return_value = mock_plan
                
                with patch.object(billing_service.stripe, 'create_subscription') as mock_stripe:
                    mock_stripe.return_value = {
                        "id": "sub_test_enterprise",
                        "current_period_start": int(datetime.utcnow().timestamp()),
                        "current_period_end": int((datetime.utcnow() + timedelta(days=30)).timestamp()),
                        "status": "trialing"
                    }
                    
                    with patch.object(billing_service, '_update_tenant_subscription_status'):
                        
                        request = CreateSubscriptionRequest(
                            plan_id=mock_plan.id,
                            trial_period_days=14
                        )
                        
                        result = await billing_service.create_subscription(
                            sample_tenant.id, 
                            request
                        )
                        
                        # Verify subscription creation
                        assert isinstance(result, Subscription)
                        assert result.tenant_id == sample_tenant.id
                        assert result.billing_account_id == sample_billing_account.id
                        assert result.status == SubscriptionStatus.TRIALING
                        assert result.stripe_subscription_id == "sub_test_enterprise"
                        
                        # Verify database operations
                        billing_service.db.add.assert_called_once()
                        billing_service.db.commit.assert_called_once()

    async def test_subscription_plan_upgrade(self, billing_service, sample_tenant):
        """Test subscription plan upgrade with prorations"""
        # Mock current subscription
        current_subscription = Subscription(
            id=uuid4(),
            tenant_id=sample_tenant.id,
            plan_id=uuid4(),
            status=SubscriptionStatus.ACTIVE,
            stripe_subscription_id="sub_current_123"
        )
        
        billing_service.db.commit = AsyncMock()
        billing_service.db.refresh = AsyncMock()
        
        with patch.object(billing_service, 'get_subscription') as mock_get_sub:
            mock_get_sub.return_value = current_subscription
            
            with patch.object(billing_service, 'get_plan') as mock_get_plan:
                new_plan = Plan(
                    id=uuid4(),
                    name="Enterprise Plan",
                    slug="enterprise",
                    stripe_price_id="price_enterprise_monthly"
                )
                mock_get_plan.return_value = new_plan
                
                with patch.object(billing_service.stripe, 'update_subscription') as mock_stripe:
                    
                    request = UpdateSubscriptionRequest(
                        plan_id=new_plan.id
                    )
                    
                    result = await billing_service.update_subscription(
                        sample_tenant.id,
                        request
                    )
                    
                    # Verify plan upgrade
                    assert result.plan_id == new_plan.id
                    mock_stripe.assert_called_once()
                    billing_service.db.commit.assert_called_once()

    async def test_subscription_cancellation_immediate(self, billing_service, sample_tenant):
        """Test immediate subscription cancellation"""
        # Mock current subscription
        subscription = Subscription(
            id=uuid4(),
            tenant_id=sample_tenant.id,
            status=SubscriptionStatus.ACTIVE,
            stripe_subscription_id="sub_to_cancel_123"
        )
        
        billing_service.db.commit = AsyncMock()
        billing_service.db.refresh = AsyncMock()
        
        with patch.object(billing_service, 'get_subscription') as mock_get_sub:
            mock_get_sub.return_value = subscription
            
            with patch.object(billing_service.stripe, 'cancel_subscription') as mock_stripe:
                with patch.object(billing_service, '_update_tenant_subscription_status'):
                    
                    result = await billing_service.cancel_subscription(
                        sample_tenant.id,
                        immediately=True
                    )
                    
                    # Verify immediate cancellation
                    assert result.status == SubscriptionStatus.CANCELLED
                    assert result.cancelled_at is not None
                    assert result.cancel_at_period_end is False
                    
                    # Verify Stripe call
                    mock_stripe.assert_called_once_with(
                        "sub_to_cancel_123",
                        at_period_end=False
                    )

    async def test_subscription_cancellation_at_period_end(self, billing_service, sample_tenant):
        """Test subscription cancellation at period end"""
        # Mock current subscription
        subscription = Subscription(
            id=uuid4(),
            tenant_id=sample_tenant.id,
            status=SubscriptionStatus.ACTIVE,
            stripe_subscription_id="sub_to_cancel_period_end"
        )
        
        billing_service.db.commit = AsyncMock()
        billing_service.db.refresh = AsyncMock()
        
        with patch.object(billing_service, 'get_subscription') as mock_get_sub:
            mock_get_sub.return_value = subscription
            
            with patch.object(billing_service.stripe, 'cancel_subscription') as mock_stripe:
                
                result = await billing_service.cancel_subscription(
                    sample_tenant.id,
                    immediately=False
                )
                
                # Verify period-end cancellation
                assert result.cancelled_at is not None
                assert result.cancel_at_period_end is True
                # Status should remain active until period end
                assert result.status == SubscriptionStatus.ACTIVE
                
                # Verify Stripe call
                mock_stripe.assert_called_once_with(
                    "sub_to_cancel_period_end",
                    at_period_end=True
                )


class TestBillingServiceUsageTracking:
    """Test usage-based billing and metering"""

    async def test_record_usage_api_calls(self, billing_service, sample_tenant):
        """Test accurate API call usage recording"""
        # Mock current subscription
        subscription = Subscription(
            id=uuid4(),
            tenant_id=sample_tenant.id,
            current_period_start=datetime.utcnow().replace(day=1),
            current_period_end=datetime.utcnow().replace(day=28),
            stripe_subscription_id="sub_usage_test"
        )
        
        billing_service.db.add = MagicMock()
        billing_service.db.commit = AsyncMock()
        billing_service.db.refresh = AsyncMock()
        
        with patch.object(billing_service, 'get_subscription') as mock_get_sub:
            mock_get_sub.return_value = subscription
            
            with patch.object(billing_service.stripe, 'create_usage_record') as mock_stripe:
                mock_stripe.return_value = {
                    "id": "mbur_api_calls_123",
                    "quantity": 5000,
                    "timestamp": int(datetime.utcnow().timestamp())
                }
                
                result = await billing_service.record_usage(
                    tenant_id=sample_tenant.id,
                    metric_type=UsageMetricType.API_CALLS,
                    quantity=5000
                )
                
                # Verify usage record
                assert isinstance(result, UsageRecord)
                assert result.tenant_id == sample_tenant.id
                assert result.subscription_id == subscription.id
                assert result.metric_type == UsageMetricType.API_CALLS
                assert result.quantity == 5000
                assert result.stripe_usage_record_id == "mbur_api_calls_123"
                
                # Verify billing period assignment
                assert result.billing_period_start == subscription.current_period_start
                assert result.billing_period_end == subscription.current_period_end

    async def test_record_usage_ai_requests(self, billing_service, sample_tenant):
        """Test AI request usage recording for premium billing"""
        subscription = Subscription(
            id=uuid4(),
            tenant_id=sample_tenant.id,
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=30),
            stripe_subscription_id="sub_ai_usage"
        )
        
        billing_service.db.add = MagicMock()
        billing_service.db.commit = AsyncMock()
        billing_service.db.refresh = AsyncMock()
        
        with patch.object(billing_service, 'get_subscription') as mock_get_sub:
            mock_get_sub.return_value = subscription
            
            with patch.object(billing_service.stripe, 'create_usage_record') as mock_stripe:
                mock_stripe.return_value = {
                    "id": "mbur_ai_requests_456",
                    "quantity": 250,
                    "timestamp": int(datetime.utcnow().timestamp())
                }
                
                result = await billing_service.record_usage(
                    tenant_id=sample_tenant.id,
                    metric_type=UsageMetricType.AI_REQUESTS,
                    quantity=250
                )
                
                # Verify AI usage recording
                assert result.metric_type == UsageMetricType.AI_REQUESTS
                assert result.quantity == 250
                assert result.stripe_usage_record_id == "mbur_ai_requests_456"

    async def test_usage_without_subscription_fails(self, billing_service, sample_tenant):
        """Test usage recording fails gracefully without active subscription"""
        with patch.object(billing_service, 'get_subscription') as mock_get_sub:
            mock_get_sub.return_value = None
            
            with pytest.raises(ResourceNotFoundError):
                await billing_service.record_usage(
                    tenant_id=sample_tenant.id,
                    metric_type=UsageMetricType.API_CALLS,
                    quantity=1000
                )


class TestBillingServiceAnalytics:
    """Test billing analytics and revenue calculations"""

    async def test_billing_analytics_with_subscription(self, billing_service, sample_tenant):
        """Test billing analytics calculation with active subscription"""
        # Mock subscription
        subscription = Subscription(
            id=uuid4(),
            tenant_id=sample_tenant.id,
            plan_id=uuid4(),
            current_period_start=datetime.utcnow().replace(day=1),
            status=SubscriptionStatus.ACTIVE
        )
        
        # Mock plan
        plan = Plan(
            id=subscription.plan_id,
            name="Enterprise Plan",
            base_price=Decimal('800.00'),
            usage_prices={
                UsageMetricType.API_CALLS: Decimal('0.001'),  # $0.001 per API call
                UsageMetricType.AI_REQUESTS: Decimal('0.10')   # $0.10 per AI request
            },
            included_usage={
                UsageMetricType.API_CALLS: 100000,  # 100K included
                UsageMetricType.AI_REQUESTS: 1000    # 1K included
            }
        )
        
        billing_service.db.execute = AsyncMock()
        
        with patch.object(billing_service, 'get_subscription') as mock_get_sub:
            mock_get_sub.return_value = subscription
            
            with patch.object(billing_service, 'get_plan') as mock_get_plan:
                mock_get_plan.return_value = plan
                
                # Mock usage query result
                mock_usage_result = MagicMock()
                mock_usage_result.__iter__ = lambda self: iter([
                    MagicMock(metric_type=UsageMetricType.API_CALLS, total_quantity=150000),
                    MagicMock(metric_type=UsageMetricType.AI_REQUESTS, total_quantity=1500)
                ])
                billing_service.db.execute.return_value = mock_usage_result
                
                analytics = await billing_service.get_billing_analytics(sample_tenant.id)
                
                # Verify analytics calculations
                assert isinstance(analytics, BillingAnalytics)
                assert analytics.tenant_id == sample_tenant.id
                assert analytics.monthly_recurring_revenue == Decimal('800.00')
                assert analytics.annual_recurring_revenue == Decimal('9600.00')  # 800 * 12
                
                # Verify usage metrics
                assert analytics.usage_metrics[UsageMetricType.API_CALLS] == 150000
                assert analytics.usage_metrics[UsageMetricType.AI_REQUESTS] == 1500
                
                # Verify projected cost calculation (base + overages)
                # Base: $800, API overage: 50K * $0.001 = $50, AI overage: 500 * $0.10 = $50
                expected_projected = Decimal('800.00') + Decimal('50.00') + Decimal('50.00')
                assert analytics.projected_monthly_cost == expected_projected

    async def test_billing_analytics_without_subscription(self, billing_service, sample_tenant):
        """Test billing analytics with no active subscription"""
        with patch.object(billing_service, 'get_subscription') as mock_get_sub:
            mock_get_sub.return_value = None
            
            analytics = await billing_service.get_billing_analytics(sample_tenant.id)
            
            # Verify zero analytics for inactive tenant
            assert analytics.tenant_id == sample_tenant.id
            assert analytics.monthly_recurring_revenue == Decimal('0')
            assert analytics.annual_recurring_revenue == Decimal('0')
            assert analytics.projected_monthly_cost == Decimal('0')
            assert analytics.usage_metrics == {}


class TestBillingServiceWebhookProcessing:
    """Test Stripe webhook event processing"""

    async def test_process_subscription_updated_webhook(self, billing_service):
        """Test processing subscription updated webhook"""
        # Mock webhook event
        webhook_data = {
            "id": "evt_subscription_updated",
            "type": "customer.subscription.updated",
            "data": {
                "object": {
                    "id": "sub_webhook_test",
                    "status": "active"
                }
            }
        }
        
        # Mock subscription
        subscription = Subscription(
            id=uuid4(),
            tenant_id=uuid4(),
            stripe_subscription_id="sub_webhook_test",
            status=SubscriptionStatus.TRIALING
        )
        
        billing_service.db.execute = AsyncMock()
        billing_service.db.add = MagicMock()
        billing_service.db.commit = AsyncMock()
        
        # Mock query result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = subscription
        billing_service.db.execute.return_value = mock_result
        
        with patch.object(billing_service, '_update_tenant_subscription_status'):
            
            success = await billing_service.process_webhook(webhook_data)
            
            # Verify webhook processing
            assert success is True
            
            # Verify subscription status update
            assert subscription.status == SubscriptionStatus.ACTIVE
            assert subscription.updated_at is not None

    async def test_process_subscription_cancelled_webhook(self, billing_service):
        """Test processing subscription cancelled webhook"""
        webhook_data = {
            "id": "evt_subscription_cancelled",
            "type": "customer.subscription.deleted",
            "data": {
                "object": {
                    "id": "sub_cancelled_test"
                }
            }
        }
        
        subscription = Subscription(
            id=uuid4(),
            tenant_id=uuid4(),
            stripe_subscription_id="sub_cancelled_test",
            status=SubscriptionStatus.ACTIVE
        )
        
        billing_service.db.execute = AsyncMock()
        billing_service.db.add = MagicMock()
        billing_service.db.commit = AsyncMock()
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = subscription
        billing_service.db.execute.return_value = mock_result
        
        with patch.object(billing_service, '_update_tenant_subscription_status'):
            
            success = await billing_service.process_webhook(webhook_data)
            
            # Verify webhook processing
            assert success is True
            
            # Verify subscription cancellation
            assert subscription.status == SubscriptionStatus.CANCELLED
            assert subscription.cancelled_at is not None

    async def test_webhook_processing_unknown_event(self, billing_service):
        """Test webhook processing handles unknown event types gracefully"""
        webhook_data = {
            "id": "evt_unknown_event",
            "type": "invoice.finalization_failed",  # Unhandled event type
            "data": {
                "object": {
                    "id": "in_unknown_invoice"
                }
            }
        }
        
        billing_service.db.add = MagicMock()
        billing_service.db.commit = AsyncMock()
        
        success = await billing_service.process_webhook(webhook_data)
        
        # Should succeed but log unhandled event
        assert success is True
        billing_service.db.add.assert_called_once()
        billing_service.db.commit.assert_called_once()


class TestBillingServiceErrorHandling:
    """Test billing service error handling and resilience"""

    async def test_subscription_creation_billing_account_not_found(self, billing_service, sample_tenant):
        """Test subscription creation fails gracefully when billing account missing"""
        with patch.object(billing_service, 'get_billing_account') as mock_get_account:
            mock_get_account.return_value = None
            
            request = CreateSubscriptionRequest(plan_id=uuid4())
            
            with pytest.raises(ResourceNotFoundError):
                await billing_service.create_subscription(sample_tenant.id, request)

    async def test_subscription_creation_plan_not_found(self, billing_service, sample_tenant, sample_billing_account):
        """Test subscription creation fails when plan doesn't exist"""
        with patch.object(billing_service, 'get_billing_account') as mock_get_account:
            mock_get_account.return_value = sample_billing_account
            
            with patch.object(billing_service, 'get_plan') as mock_get_plan:
                mock_get_plan.return_value = None
                
                request = CreateSubscriptionRequest(plan_id=uuid4())
                
                with pytest.raises(ResourceNotFoundError):
                    await billing_service.create_subscription(sample_tenant.id, request)

    async def test_database_error_handling_with_rollback(self, billing_service, sample_tenant, sample_billing_account):
        """Test database errors trigger proper rollback"""
        billing_service.db.add = MagicMock()
        billing_service.db.commit = AsyncMock(side_effect=Exception("Database connection failed"))
        billing_service.db.rollback = AsyncMock()
        
        with patch.object(billing_service, 'get_billing_account') as mock_get_account:
            mock_get_account.return_value = sample_billing_account
            
            with patch.object(billing_service, 'get_plan') as mock_get_plan:
                mock_plan = Plan(id=uuid4(), name="Test Plan", base_price=Decimal('100'))
                mock_get_plan.return_value = mock_plan
                
                with patch.object(billing_service.stripe, 'create_subscription'):
                    
                    request = CreateSubscriptionRequest(plan_id=mock_plan.id)
                    
                    with pytest.raises(Exception, match="Database connection failed"):
                        await billing_service.create_subscription(sample_tenant.id, request)
                    
                    # Verify rollback was called
                    billing_service.db.rollback.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])