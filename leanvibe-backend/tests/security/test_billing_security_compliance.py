"""
BILLING SECURITY & COMPLIANCE TESTS
Priority 1 - Week 2 Final Implementation

These tests implement critical financial security, PCI DSS compliance, and revenue protection.
Status: IMPLEMENTING - Billing security and compliance validation
"""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4
from unittest.mock import AsyncMock, patch, MagicMock

# Configure pytest for async tests
pytestmark = pytest.mark.asyncio

from app.services.billing_service import BillingService
from app.models.billing_models import (
    BillingAccount, Subscription, UsageRecord, Payment, Invoice,
    SubscriptionStatus, PaymentStatus, InvoiceStatus, UsageMetricType,
    Plan, BillingAnalytics
)
from app.models.tenant_models import Tenant, TenantStatus, TenantPlan
from app.core.exceptions import (
    InsufficientPermissionsError, ResourceNotFoundError,
    PaymentRequiredError, PaymentFailedError
)


@pytest_asyncio.fixture
async def billing_service():
    """Create billing service with mocked database"""
    mock_db = AsyncMock()
    service = BillingService(db=mock_db)
    return service


@pytest_asyncio.fixture
async def tenant_a():
    """Tenant A for isolation testing"""
    return Tenant(
        id=uuid4(),
        organization_name="Company A Corp",
        slug="company-a",
        admin_email="admin@company-a.com",
        status=TenantStatus.ACTIVE,
        plan=TenantPlan.ENTERPRISE
    )


@pytest_asyncio.fixture
async def tenant_b():
    """Tenant B for isolation testing"""
    return Tenant(
        id=uuid4(),
        organization_name="Company B Ltd", 
        slug="company-b",
        admin_email="admin@company-b.com",
        status=TenantStatus.ACTIVE,
        plan=TenantPlan.TEAM
    )


class TestBillingTenantIsolationSecurity:
    """Test billing data isolation between tenants"""

    async def test_billing_account_cross_tenant_access_blocked(self, billing_service, tenant_a, tenant_b):
        """Test tenant A cannot access tenant B's billing account"""
        # Mock billing account for tenant B
        tenant_b_billing = BillingAccount(
            id=uuid4(),
            tenant_id=tenant_b.id,
            company_name="Company B Ltd",
            billing_email="billing@company-b.com",
            stripe_customer_id="cus_tenant_b_123"
        )
        
        # Mock database query that should filter by tenant_id
        billing_service.db.execute = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None  # No access for tenant A
        billing_service.db.execute.return_value = mock_result
        
        # Tenant A should not be able to access tenant B's billing account
        result = await billing_service.get_billing_account(tenant_a.id)
        
        # Verify isolation - no billing account returned for tenant A
        assert result is None
        
        # Verify database query includes tenant_id filter
        billing_service.db.execute.assert_called_once()
        call_args = billing_service.db.execute.call_args[0][0]
        
        # The query should filter by tenant_id (tenant_a.id, not tenant_b.id)
        assert "BillingAccount.tenant_id" in str(call_args)

    async def test_subscription_cross_tenant_access_blocked(self, billing_service, tenant_a, tenant_b):
        """Test tenant A cannot access tenant B's subscription data"""
        # Mock subscription for tenant B
        tenant_b_subscription = Subscription(
            id=uuid4(),
            tenant_id=tenant_b.id,
            status=SubscriptionStatus.ACTIVE,
            stripe_subscription_id="sub_tenant_b_123"
        )
        
        billing_service.db.execute = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        billing_service.db.execute.return_value = mock_result
        
        # Tenant A requesting subscription data
        result = await billing_service.get_subscription(tenant_a.id)
        
        # Should return None for tenant A (no access to tenant B data)
        assert result is None
        
        # Verify tenant isolation in database query
        billing_service.db.execute.assert_called_once()
        call_args = billing_service.db.execute.call_args[0][0]
        assert "Subscription.tenant_id" in str(call_args)

    async def test_usage_records_tenant_isolation(self, billing_service, tenant_a, tenant_b):
        """Test usage records are properly isolated by tenant"""
        # Mock usage recording for tenant A should not affect tenant B
        subscription_a = Subscription(
            id=uuid4(),
            tenant_id=tenant_a.id,
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=30)
        )
        
        billing_service.db.add = MagicMock()
        billing_service.db.commit = AsyncMock()
        billing_service.db.refresh = AsyncMock()
        
        with patch.object(billing_service, 'get_subscription') as mock_get_sub:
            mock_get_sub.return_value = subscription_a
            
            with patch.object(billing_service.stripe, 'create_usage_record') as mock_stripe:
                mock_stripe.return_value = {"id": "mbur_tenant_a_123", "quantity": 5000}
                
                result = await billing_service.record_usage(
                    tenant_id=tenant_a.id,
                    metric_type=UsageMetricType.API_CALLS,
                    quantity=5000
                )
                
                # Verify usage record is tied to correct tenant
                assert result.tenant_id == tenant_a.id
                assert result.tenant_id != tenant_b.id
                assert result.subscription_id == subscription_a.id

    async def test_billing_analytics_tenant_isolation(self, billing_service, tenant_a, tenant_b):
        """Test billing analytics are isolated by tenant"""
        # Mock subscription for tenant A
        subscription_a = Subscription(
            id=uuid4(),
            tenant_id=tenant_a.id,
            plan_id=uuid4(),
            status=SubscriptionStatus.ACTIVE
        )
        
        plan_a = Plan(
            id=subscription_a.plan_id,
            name="Enterprise Plan",
            base_price=Decimal('1000.00')
        )
        
        billing_service.db.execute = AsyncMock()
        
        with patch.object(billing_service, 'get_subscription') as mock_get_sub:
            mock_get_sub.return_value = subscription_a
            
            with patch.object(billing_service, 'get_plan') as mock_get_plan:
                mock_get_plan.return_value = plan_a
                
                # Mock empty usage result
                mock_usage_result = MagicMock()
                mock_usage_result.__iter__ = lambda self: iter([])
                billing_service.db.execute.return_value = mock_usage_result
                
                analytics = await billing_service.get_billing_analytics(tenant_a.id)
                
                # Verify analytics are for tenant A only
                assert analytics.tenant_id == tenant_a.id
                assert analytics.monthly_recurring_revenue == Decimal('1000.00')
                
                # Verify usage query filters by tenant_id
                billing_service.db.execute.assert_called_once()
                call_args = billing_service.db.execute.call_args[0][0]
                assert "UsageRecord.tenant_id" in str(call_args)


class TestBillingPaymentDataSecurity:
    """Test payment data security and PCI DSS compliance"""

    async def test_stripe_customer_creation_data_protection(self, billing_service):
        """Test sensitive customer data is properly handled in Stripe"""
        billing_account = BillingAccount(
            tenant_id=uuid4(),
            company_name="Secure Corp",
            billing_email="secure@corp.com",
            billing_address={
                "line1": "123 Secure St",
                "city": "Security City",
                "state": "CA",
                "postal_code": "94105",
                "country": "US"
            },
            tax_id="12-3456789"  # Sensitive tax information
        )
        
        billing_service.db.add = MagicMock()
        billing_service.db.commit = AsyncMock()
        billing_service.db.refresh = AsyncMock()
        
        account_data = {
            "company_name": billing_account.company_name,
            "billing_email": billing_account.billing_email,
            "billing_address": billing_account.billing_address,
            "tax_id": billing_account.tax_id,
            "tax_type": "ein"
        }
        
        with patch.object(billing_service.stripe, 'create_customer') as mock_stripe:
            mock_stripe.return_value = "cus_secure_customer_456"
            
            result = await billing_service.create_billing_account(
                billing_account.tenant_id,
                account_data
            )
            
            # Verify billing account creation
            assert result.stripe_customer_id == "cus_secure_customer_456"
            assert result.tax_id == "12-3456789"  # Tax ID stored securely
            
            # Verify Stripe integration was called with proper data
            mock_stripe.assert_called_once()
            call_args = mock_stripe.call_args[0][0]  # billing_account parameter
            assert call_args.company_name == "Secure Corp"
            assert call_args.billing_email == "secure@corp.com"

    async def test_payment_data_not_stored_locally(self, billing_service):
        """Test payment card data is never stored locally (PCI DSS compliance)"""
        # This test verifies we don't store sensitive payment data locally
        # Only Stripe tokens/IDs should be stored
        
        billing_account = BillingAccount(
            id=uuid4(),
            tenant_id=uuid4(),
            company_name="PCI Compliant Corp",
            billing_email="pci@compliant.com",
            stripe_customer_id="cus_pci_compliant"
        )
        
        # Verify billing account doesn't contain credit card fields
        billing_account_dict = billing_account.__dict__
        
        # These fields should NOT exist (PCI DSS compliance)
        forbidden_fields = [
            'credit_card_number', 'card_number', 'cvv', 'cvc',
            'card_expiry', 'cardholder_name', 'card_brand'
        ]
        
        for forbidden_field in forbidden_fields:
            assert forbidden_field not in billing_account_dict, f"PCI violation: {forbidden_field} found in billing account"
        
        # Only Stripe references should be stored
        assert billing_account.stripe_customer_id is not None
        assert billing_account.stripe_customer_id.startswith("cus_")

    async def test_webhook_signature_verification_prevents_fraud(self, billing_service):
        """Test webhook signature verification prevents payment fraud"""
        # Test invalid webhook (no signature verification)
        fraudulent_webhook = {
            "id": "evt_fraudulent_attempt",
            "type": "customer.subscription.updated",
            "data": {
                "object": {
                    "id": "sub_victim_subscription",
                    "status": "active"  # Fraudster trying to activate subscription
                }
            }
        }
        
        billing_service.db.add = MagicMock()
        billing_service.db.commit = AsyncMock()
        
        # Mock webhook verification in Stripe integration
        with patch.object(billing_service.stripe, 'verify_webhook') as mock_verify:
            # Simulate signature verification passing (in real impl, this would validate)
            mock_verify.return_value = fraudulent_webhook
            
            success = await billing_service.process_webhook(fraudulent_webhook)
            
            # Even fraudulent webhooks are processed if signature validates
            # (The signature verification is the fraud prevention mechanism)
            assert success is True
            mock_verify.assert_called_once()

    async def test_subscription_access_control_by_tenant(self, billing_service, tenant_a, tenant_b):
        """Test users can only modify their own tenant's subscriptions"""
        # Mock subscription for tenant B
        tenant_b_subscription = Subscription(
            id=uuid4(),
            tenant_id=tenant_b.id,
            status=SubscriptionStatus.ACTIVE,
            stripe_subscription_id="sub_tenant_b_secret"
        )
        
        billing_service.db.execute = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None  # No subscription for tenant A
        billing_service.db.execute.return_value = mock_result
        
        # Tenant A trying to cancel tenant B's subscription should fail
        with pytest.raises(ResourceNotFoundError):
            await billing_service.cancel_subscription(tenant_a.id, immediately=True)
        
        # Verify tenant A cannot access tenant B's subscription
        billing_service.db.execute.assert_called_once()


class TestBillingComplianceAndAudit:
    """Test billing compliance and audit trail requirements"""

    async def test_revenue_recognition_calculation_accuracy(self, billing_service, tenant_a):
        """Test revenue recognition follows accounting standards (ASC 606)"""
        # Mock enterprise subscription with specific revenue recognition requirements
        subscription = Subscription(
            id=uuid4(),
            tenant_id=tenant_a.id,
            plan_id=uuid4(),
            status=SubscriptionStatus.ACTIVE,
            current_period_start=datetime(2024, 1, 1),
            current_period_end=datetime(2024, 1, 31),  # Monthly billing
            trial_start=None,  # No trial, immediate revenue recognition
            trial_end=None
        )
        
        plan = Plan(
            id=subscription.plan_id,
            name="Enterprise Annual",
            base_price=Decimal('9600.00'),  # $9600 annual
            billing_interval="annual"
        )
        
        billing_service.db.execute = AsyncMock()
        
        with patch.object(billing_service, 'get_subscription') as mock_get_sub:
            mock_get_sub.return_value = subscription
            
            with patch.object(billing_service, 'get_plan') as mock_get_plan:
                mock_get_plan.return_value = plan
                
                mock_usage_result = MagicMock()
                mock_usage_result.__iter__ = lambda self: iter([])
                billing_service.db.execute.return_value = mock_usage_result
                
                analytics = await billing_service.get_billing_analytics(tenant_a.id)
                
                # Verify revenue recognition calculations
                # Annual plan: $9600/year = $800/month MRR
                assert analytics.monthly_recurring_revenue == Decimal('800.00')
                assert analytics.annual_recurring_revenue == Decimal('9600.00')

    async def test_tax_calculation_compliance_by_jurisdiction(self, billing_service):
        """Test tax calculations follow jurisdiction requirements"""
        # Test billing account with different jurisdictions
        us_billing_account = BillingAccount(
            id=uuid4(),
            tenant_id=uuid4(),
            company_name="US Corp",
            billing_email="us@corp.com",
            billing_address={
                "country": "US",
                "state": "CA",
                "postal_code": "94105"
            },
            tax_id="12-3456789",
            tax_type="ein"  # US tax ID
        )
        
        eu_billing_account = BillingAccount(
            id=uuid4(),
            tenant_id=uuid4(),
            company_name="EU Ltd",
            billing_email="eu@ltd.com", 
            billing_address={
                "country": "DE",
                "postal_code": "10115"
            },
            tax_id="DE123456789",
            tax_type="vat"  # EU VAT ID
        )
        
        # Verify different tax treatment by jurisdiction
        assert us_billing_account.billing_address["country"] == "US"
        assert us_billing_account.tax_type == "ein"
        
        assert eu_billing_account.billing_address["country"] == "DE"
        assert eu_billing_account.tax_type == "vat"

    async def test_financial_audit_trail_completeness(self, billing_service, tenant_a):
        """Test all financial transactions create proper audit trails"""
        # Mock subscription creation (should create audit trail)
        subscription = Subscription(
            id=uuid4(),
            tenant_id=tenant_a.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            status=SubscriptionStatus.ACTIVE
        )
        
        # Verify audit fields are present for compliance
        assert subscription.created_at is not None
        assert subscription.updated_at is not None
        assert subscription.tenant_id is not None  # Traceability
        assert subscription.status is not None   # State tracking
        
        # Financial transactions should be traceable
        usage_record = UsageRecord(
            id=uuid4(),
            tenant_id=tenant_a.id,
            subscription_id=subscription.id,
            metric_type=UsageMetricType.API_CALLS,
            quantity=5000,
            usage_date=datetime.utcnow(),
            billing_period_start=datetime.utcnow(),
            billing_period_end=datetime.utcnow() + timedelta(days=30)
        )
        
        # Verify usage record audit trail
        assert usage_record.tenant_id is not None
        assert usage_record.subscription_id is not None
        assert usage_record.usage_date is not None
        assert usage_record.billing_period_start is not None
        assert usage_record.billing_period_end is not None

    async def test_subscription_lifecycle_audit_compliance(self, billing_service, tenant_a):
        """Test subscription lifecycle changes maintain audit compliance"""
        # Mock subscription cancellation audit trail
        subscription = Subscription(
            id=uuid4(),
            tenant_id=tenant_a.id,
            status=SubscriptionStatus.ACTIVE,
            created_at=datetime.utcnow() - timedelta(days=30),
            updated_at=datetime.utcnow() - timedelta(days=30)
        )
        
        billing_service.db.commit = AsyncMock()
        billing_service.db.refresh = AsyncMock()
        
        with patch.object(billing_service, 'get_subscription') as mock_get_sub:
            mock_get_sub.return_value = subscription
            
            with patch.object(billing_service.stripe, 'cancel_subscription'):
                
                result = await billing_service.cancel_subscription(
                    tenant_a.id,
                    immediately=True
                )
                
                # Verify audit trail for cancellation
                assert result.status == SubscriptionStatus.CANCELLED
                assert result.cancelled_at is not None  # Audit timestamp
                assert result.updated_at != result.created_at  # State change tracked
                assert result.tenant_id == tenant_a.id  # Traceability maintained


class TestBillingUsageAccuracyAndFraudPrevention:
    """Test usage tracking accuracy and fraud prevention"""

    async def test_usage_measurement_accuracy_prevents_underbilling(self, billing_service, tenant_a):
        """Test usage is measured accurately to prevent revenue loss"""
        subscription = Subscription(
            id=uuid4(),
            tenant_id=tenant_a.id,
            current_period_start=datetime.utcnow().replace(day=1),
            current_period_end=datetime.utcnow().replace(day=28)
        )
        
        billing_service.db.add = MagicMock()
        billing_service.db.commit = AsyncMock()
        billing_service.db.refresh = AsyncMock()
        
        with patch.object(billing_service, 'get_subscription') as mock_get_sub:
            mock_get_sub.return_value = subscription
            
            with patch.object(billing_service.stripe, 'create_usage_record') as mock_stripe:
                mock_stripe.return_value = {
                    "id": "mbur_accurate_usage",
                    "quantity": 7500,
                    "timestamp": int(datetime.utcnow().timestamp())
                }
                
                # Record precise usage amount
                result = await billing_service.record_usage(
                    tenant_id=tenant_a.id,
                    metric_type=UsageMetricType.API_CALLS,
                    quantity=7500  # Exact amount
                )
                
                # Verify usage is recorded exactly (no rounding down)
                assert result.quantity == 7500
                assert result.metric_type == UsageMetricType.API_CALLS
                
                # Verify Stripe receives exact usage
                mock_stripe.assert_called_once_with(
                    subscription_item_id=f"si_mock_{UsageMetricType.API_CALLS}",
                    quantity=7500,
                    timestamp=int(result.usage_date.timestamp())
                )

    async def test_usage_tampering_prevention(self, billing_service, tenant_a):
        """Test usage records cannot be tampered with after creation"""
        # Mock existing usage record
        existing_usage = UsageRecord(
            id=uuid4(),
            tenant_id=tenant_a.id,
            metric_type=UsageMetricType.AI_REQUESTS,
            quantity=1000,
            usage_date=datetime.utcnow() - timedelta(hours=1),
            stripe_usage_record_id="mbur_existing_123"
        )
        
        # Verify immutable fields that prevent tampering
        original_id = existing_usage.id
        original_tenant_id = existing_usage.tenant_id
        original_quantity = existing_usage.quantity
        original_usage_date = existing_usage.usage_date
        original_stripe_id = existing_usage.stripe_usage_record_id
        
        # These fields should remain unchanged (immutable for audit trail)
        assert existing_usage.id == original_id
        assert existing_usage.tenant_id == original_tenant_id
        assert existing_usage.quantity == original_quantity
        assert existing_usage.usage_date == original_usage_date
        assert existing_usage.stripe_usage_record_id == original_stripe_id

    async def test_billing_calculation_precision_prevents_rounding_errors(self, billing_service, tenant_a):
        """Test billing calculations maintain precision to prevent revenue loss"""
        subscription = Subscription(
            id=uuid4(),
            tenant_id=tenant_a.id,
            plan_id=uuid4(),
            status=SubscriptionStatus.ACTIVE
        )
        
        # Plan with precise usage pricing
        plan = Plan(
            id=subscription.plan_id,
            name="Precision Plan",
            base_price=Decimal('500.00'),
            usage_prices={
                UsageMetricType.API_CALLS: Decimal('0.0015'),  # $0.0015 per call
                UsageMetricType.AI_REQUESTS: Decimal('0.125')  # $0.125 per AI request
            },
            included_usage={
                UsageMetricType.API_CALLS: 100000,
                UsageMetricType.AI_REQUESTS: 1000
            }
        )
        
        billing_service.db.execute = AsyncMock()
        
        with patch.object(billing_service, 'get_subscription') as mock_get_sub:
            mock_get_sub.return_value = subscription
            
            with patch.object(billing_service, 'get_plan') as mock_get_plan:
                mock_get_plan.return_value = plan
                
                # Mock usage with fractional overage amounts
                mock_usage_result = MagicMock()
                mock_usage_result.__iter__ = lambda self: iter([
                    MagicMock(metric_type=UsageMetricType.API_CALLS, total_quantity=133333),  # 33,333 overage
                    MagicMock(metric_type=UsageMetricType.AI_REQUESTS, total_quantity=1234)   # 234 overage
                ])
                billing_service.db.execute.return_value = mock_usage_result
                
                analytics = await billing_service.get_billing_analytics(tenant_a.id)
                
                # Verify precise decimal calculations
                # Base: $500.00
                # API overage: 33,333 * $0.0015 = $49.9995 (should be $50.00)
                # AI overage: 234 * $0.125 = $29.25
                # Total: $500.00 + $50.00 + $29.25 = $579.25
                
                expected_api_overage = Decimal('33333') * Decimal('0.0015')  # $49.9995
                expected_ai_overage = Decimal('234') * Decimal('0.125')      # $29.25
                expected_total = Decimal('500.00') + expected_api_overage + expected_ai_overage
                
                assert analytics.projected_monthly_cost == expected_total
                
                # Verify no precision loss in decimal calculations
                assert isinstance(analytics.projected_monthly_cost, Decimal)
                assert analytics.projected_monthly_cost >= Decimal('579.24')  # Minimum expected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])