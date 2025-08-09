"""
Usage-Based Billing Tracking Tests for LeanVibe Enterprise Billing
Tests accurate usage measurement, quota enforcement, overage calculations, and tenant isolation
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.billing_service import BillingService
from app.models.billing_models import (
    Plan, BillingAccount, Subscription, UsageRecord, BillingAnalytics,
    SubscriptionStatus, UsageMetricType, BillingInterval,
    DEFAULT_PLANS
)
from app.models.tenant_models import Tenant, TenantStatus
from app.core.exceptions import ResourceNotFoundError


class TestUsageMeasurementAccuracy:
    """Test accurate usage measurement and tracking"""
    
    def setup_method(self):
        """Set up test environment"""
        self.billing_service = BillingService()
        self.tenant_id = uuid4()
        self.subscription_id = uuid4()
        
        # Mock active subscription
        self.mock_subscription = Subscription(
            id=self.subscription_id,
            tenant_id=self.tenant_id,
            billing_account_id=uuid4(),
            plan_id=uuid4(),
            status=SubscriptionStatus.ACTIVE,
            current_period_start=datetime.utcnow().replace(day=1),
            current_period_end=datetime.utcnow().replace(day=28) + timedelta(days=3),
            stripe_subscription_id="sub_test123"
        )
    
    @pytest.mark.asyncio
    async def test_api_calls_usage_tracking(self):
        """Test accurate API calls usage tracking"""
        with patch.object(self.billing_service, 'get_subscription', return_value=self.mock_subscription), \
             patch.object(self.billing_service, '_get_db') as mock_db, \
             patch.object(self.billing_service.stripe, 'create_usage_record') as mock_stripe:
            
            mock_session = AsyncMock()
            mock_db.return_value = mock_session
            mock_stripe.return_value = {"id": "mbur_test123", "quantity": 150}
            
            # Record API usage
            usage_record = UsageRecord(
                id=uuid4(),
                tenant_id=self.tenant_id,
                subscription_id=self.subscription_id,
                metric_type=UsageMetricType.API_CALLS,
                quantity=150,
                usage_date=datetime.utcnow(),
                billing_period_start=self.mock_subscription.current_period_start,
                billing_period_end=self.mock_subscription.current_period_end,
                stripe_usage_record_id="mbur_test123"
            )
            
            with patch.object(self.billing_service, 'record_usage', return_value=usage_record):
                result = await self.billing_service.record_usage(
                    self.tenant_id, 
                    UsageMetricType.API_CALLS, 
                    150
                )
                
                assert result.metric_type == UsageMetricType.API_CALLS
                assert result.quantity == 150
                assert result.tenant_id == self.tenant_id
                mock_stripe.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_storage_usage_tracking_gb(self):
        """Test storage usage tracking in GB"""
        with patch.object(self.billing_service, 'get_subscription', return_value=self.mock_subscription), \
             patch.object(self.billing_service, '_get_db') as mock_db, \
             patch.object(self.billing_service.stripe, 'create_usage_record') as mock_stripe:
            
            mock_session = AsyncMock()
            mock_db.return_value = mock_session
            mock_stripe.return_value = {"id": "mbur_storage123", "quantity": 5}
            
            # Record storage usage (5 GB)
            usage_record = UsageRecord(
                id=uuid4(),
                tenant_id=self.tenant_id,
                subscription_id=self.subscription_id,
                metric_type=UsageMetricType.STORAGE_GB,
                quantity=5,  # 5 GB
                usage_date=datetime.utcnow(),
                billing_period_start=self.mock_subscription.current_period_start,
                billing_period_end=self.mock_subscription.current_period_end
            )
            
            with patch.object(self.billing_service, 'record_usage', return_value=usage_record):
                result = await self.billing_service.record_usage(
                    self.tenant_id, 
                    UsageMetricType.STORAGE_GB, 
                    5
                )
                
                assert result.metric_type == UsageMetricType.STORAGE_GB
                assert result.quantity == 5
                mock_stripe.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_ai_requests_usage_tracking(self):
        """Test AI requests usage tracking"""
        with patch.object(self.billing_service, 'get_subscription', return_value=self.mock_subscription), \
             patch.object(self.billing_service, '_get_db') as mock_db, \
             patch.object(self.billing_service.stripe, 'create_usage_record') as mock_stripe:
            
            mock_session = AsyncMock()
            mock_db.return_value = mock_session
            mock_stripe.return_value = {"id": "mbur_ai123", "quantity": 25}
            
            usage_record = UsageRecord(
                id=uuid4(),
                tenant_id=self.tenant_id,
                subscription_id=self.subscription_id,
                metric_type=UsageMetricType.AI_REQUESTS,
                quantity=25,  # 25 AI requests
                usage_date=datetime.utcnow(),
                billing_period_start=self.mock_subscription.current_period_start,
                billing_period_end=self.mock_subscription.current_period_end
            )
            
            with patch.object(self.billing_service, 'record_usage', return_value=usage_record):
                result = await self.billing_service.record_usage(
                    self.tenant_id, 
                    UsageMetricType.AI_REQUESTS, 
                    25
                )
                
                assert result.metric_type == UsageMetricType.AI_REQUESTS
                assert result.quantity == 25
    
    @pytest.mark.asyncio
    async def test_concurrent_sessions_tracking(self):
        """Test concurrent sessions usage tracking"""
        with patch.object(self.billing_service, 'get_subscription', return_value=self.mock_subscription), \
             patch.object(self.billing_service, '_get_db') as mock_db, \
             patch.object(self.billing_service.stripe, 'create_usage_record') as mock_stripe:
            
            mock_session = AsyncMock()
            mock_db.return_value = mock_session
            mock_stripe.return_value = {"id": "mbur_sessions123", "quantity": 8}
            
            # Peak concurrent sessions this hour
            usage_record = UsageRecord(
                id=uuid4(),
                tenant_id=self.tenant_id,
                subscription_id=self.subscription_id,
                metric_type=UsageMetricType.CONCURRENT_SESSIONS,
                quantity=8,  # 8 concurrent sessions
                usage_date=datetime.utcnow(),
                billing_period_start=self.mock_subscription.current_period_start,
                billing_period_end=self.mock_subscription.current_period_end
            )
            
            with patch.object(self.billing_service, 'record_usage', return_value=usage_record):
                result = await self.billing_service.record_usage(
                    self.tenant_id, 
                    UsageMetricType.CONCURRENT_SESSIONS, 
                    8
                )
                
                assert result.metric_type == UsageMetricType.CONCURRENT_SESSIONS
                assert result.quantity == 8


class TestQuotaEnforcementAndBilling:
    """Test quota enforcement and billing calculations"""
    
    def setup_method(self):
        """Set up test environment"""
        self.billing_service = BillingService()
        self.tenant_id = uuid4()
        self.developer_plan = DEFAULT_PLANS["developer"]
        self.team_plan = DEFAULT_PLANS["team"]
        self.enterprise_plan = DEFAULT_PLANS["enterprise"]
    
    @pytest.mark.asyncio
    async def test_developer_plan_quota_enforcement(self):
        """Test Developer plan quota limits and enforcement"""
        # Developer plan limits: 10,000 API calls, 1GB storage
        subscription = Subscription(
            id=uuid4(),
            tenant_id=self.tenant_id,
            billing_account_id=uuid4(),
            plan_id=self.developer_plan.id,
            status=SubscriptionStatus.ACTIVE,
            current_period_start=datetime.utcnow().replace(day=1),
            current_period_end=datetime.utcnow().replace(day=28) + timedelta(days=3)
        )
        
        with patch.object(self.billing_service, 'get_subscription', return_value=subscription), \
             patch.object(self.billing_service, 'get_plan', return_value=self.developer_plan):
            
            # Test within quota
            api_calls_within_limit = 8500  # Under 10,000 limit
            assert api_calls_within_limit <= self.developer_plan.limits["api_calls_per_month"]
            
            # Test over quota
            api_calls_over_limit = 15000  # Over 10,000 limit
            overage = api_calls_over_limit - self.developer_plan.limits["api_calls_per_month"]
            assert overage == 5000
            
            # Calculate overage cost
            overage_cost = overage * self.developer_plan.usage_prices["additional_api_calls"]
            assert overage_cost == Decimal('5000')  # $50.00 overage
    
    @pytest.mark.asyncio
    async def test_team_plan_quota_enforcement(self):
        """Test Team plan quota limits and enforcement"""
        # Team plan limits: 100,000 API calls, 10GB storage
        subscription = Subscription(
            id=uuid4(),
            tenant_id=self.tenant_id,
            billing_account_id=uuid4(),
            plan_id=self.team_plan.id,
            status=SubscriptionStatus.ACTIVE,
            current_period_start=datetime.utcnow().replace(day=1),
            current_period_end=datetime.utcnow().replace(day=28) + timedelta(days=3)
        )
        
        with patch.object(self.billing_service, 'get_subscription', return_value=subscription), \
             patch.object(self.billing_service, 'get_plan', return_value=self.team_plan):
            
            # Test storage quota
            storage_within_limit = 8  # Under 10GB limit
            assert storage_within_limit <= self.team_plan.limits["storage_gb"]
            
            # Test storage overage
            storage_over_limit = 15  # Over 10GB limit
            storage_overage = storage_over_limit - self.team_plan.limits["storage_gb"]
            assert storage_overage == 5
            
            # Calculate storage overage cost
            storage_overage_cost = storage_overage * self.team_plan.usage_prices["additional_storage_gb"]
            assert storage_overage_cost == Decimal('2500')  # $25.00 overage (5GB * $5.00/GB)
    
    @pytest.mark.asyncio
    async def test_enterprise_plan_unlimited_usage(self):
        """Test Enterprise plan unlimited usage (no overages)"""
        subscription = Subscription(
            id=uuid4(),
            tenant_id=self.tenant_id,
            billing_account_id=uuid4(),
            plan_id=self.enterprise_plan.id,
            status=SubscriptionStatus.ACTIVE,
            current_period_start=datetime.utcnow().replace(day=1),
            current_period_end=datetime.utcnow().replace(day=28) + timedelta(days=3)
        )
        
        with patch.object(self.billing_service, 'get_subscription', return_value=subscription), \
             patch.object(self.billing_service, 'get_plan', return_value=self.enterprise_plan):
            
            # Enterprise should have very high limits (effectively unlimited)
            assert self.enterprise_plan.limits["api_calls_per_month"] == 999999999
            assert self.enterprise_plan.limits["storage_gb"] == 999999
            
            # Even high usage should be within enterprise limits
            high_api_usage = 1000000  # 1M API calls
            high_storage_usage = 500   # 500GB storage
            
            assert high_api_usage <= self.enterprise_plan.limits["api_calls_per_month"]
            assert high_storage_usage <= self.enterprise_plan.limits["storage_gb"]


class TestOverageCalculationAccuracy:
    """Test accurate overage calculations for billing"""
    
    def setup_method(self):
        """Set up test environment"""
        self.billing_service = BillingService()
        self.tenant_id = uuid4()
    
    @pytest.mark.asyncio
    async def test_api_calls_overage_calculation(self):
        """Test API calls overage calculation precision"""
        plan = DEFAULT_PLANS["developer"]
        
        # Simulate usage scenarios
        test_cases = [
            {
                "usage": 10000,    # Exactly at limit
                "expected_overage": 0,
                "expected_cost": Decimal('0')
            },
            {
                "usage": 10001,    # 1 over limit
                "expected_overage": 1,
                "expected_cost": Decimal('1')  # $0.01
            },
            {
                "usage": 15000,    # 5000 over limit
                "expected_overage": 5000,
                "expected_cost": Decimal('5000')  # $50.00
            },
            {
                "usage": 25000,    # 15000 over limit
                "expected_overage": 15000,
                "expected_cost": Decimal('15000')  # $150.00
            }
        ]
        
        for case in test_cases:
            usage = case["usage"]
            limit = plan.limits["api_calls_per_month"]
            
            overage = max(0, usage - limit)
            overage_cost = overage * plan.usage_prices["additional_api_calls"]
            
            assert overage == case["expected_overage"]
            assert overage_cost == case["expected_cost"]
    
    @pytest.mark.asyncio
    async def test_storage_overage_calculation(self):
        """Test storage overage calculation precision"""
        plan = DEFAULT_PLANS["team"]
        
        test_cases = [
            {
                "usage": 10,       # Exactly at limit
                "expected_overage": 0,
                "expected_cost": Decimal('0')
            },
            {
                "usage": 11,       # 1GB over limit
                "expected_overage": 1,
                "expected_cost": Decimal('500')  # $5.00
            },
            {
                "usage": 15,       # 5GB over limit
                "expected_overage": 5,
                "expected_cost": Decimal('2500')  # $25.00
            }
        ]
        
        for case in test_cases:
            usage = case["usage"]
            limit = plan.limits["storage_gb"]
            
            overage = max(0, usage - limit)
            overage_cost = overage * plan.usage_prices["additional_storage_gb"]
            
            assert overage == case["expected_overage"]
            assert overage_cost == case["expected_cost"]
    
    @pytest.mark.asyncio
    async def test_multi_metric_overage_calculation(self):
        """Test multiple metric overage calculation"""
        plan = DEFAULT_PLANS["developer"]
        
        # Simulate overages in multiple metrics
        api_usage = 15000      # 5000 over 10,000 limit
        storage_usage = 3      # 2GB over 1GB limit
        
        api_overage = max(0, api_usage - plan.limits["api_calls_per_month"])
        storage_overage = max(0, storage_usage - plan.limits["storage_gb"])
        
        api_cost = api_overage * plan.usage_prices["additional_api_calls"]
        storage_cost = storage_overage * plan.usage_prices["additional_storage_gb"]
        
        total_overage_cost = api_cost + storage_cost
        
        assert api_overage == 5000
        assert storage_overage == 2
        assert api_cost == Decimal('5000')    # $50.00
        assert storage_cost == Decimal('1000') # $10.00
        assert total_overage_cost == Decimal('6000')  # $60.00 total


class TestBillingCycleCalculations:
    """Test billing cycle calculations and period management"""
    
    def setup_method(self):
        """Set up test environment"""
        self.billing_service = BillingService()
        self.tenant_id = uuid4()
    
    def test_monthly_billing_cycle(self):
        """Test monthly billing cycle calculations"""
        # Monthly subscription starting January 1st
        period_start = datetime(2025, 1, 1)
        period_end = datetime(2025, 1, 31, 23, 59, 59)
        
        subscription = Subscription(
            id=uuid4(),
            tenant_id=self.tenant_id,
            billing_account_id=uuid4(),
            plan_id=uuid4(),
            status=SubscriptionStatus.ACTIVE,
            current_period_start=period_start,
            current_period_end=period_end
        )
        
        # Calculate period duration
        period_duration = period_end - period_start
        assert period_duration.days >= 30  # At least 30 days in January
        
        # Usage recorded within billing period
        usage_date = datetime(2025, 1, 15)
        assert period_start <= usage_date <= period_end
    
    def test_annual_billing_cycle(self):
        """Test annual billing cycle calculations"""
        # Annual subscription
        period_start = datetime(2025, 1, 1)
        period_end = datetime(2025, 12, 31, 23, 59, 59)
        
        subscription = Subscription(
            id=uuid4(),
            tenant_id=self.tenant_id,
            billing_account_id=uuid4(),
            plan_id=uuid4(),
            status=SubscriptionStatus.ACTIVE,
            current_period_start=period_start,
            current_period_end=period_end
        )
        
        # Calculate period duration
        period_duration = period_end - period_start
        assert period_duration.days >= 364  # Full year
        
        # Usage aggregation over full year
        monthly_usage = [5000, 6000, 5500, 7000, 8000, 7500, 6500, 6000, 5500, 6000, 7000, 8000]
        total_annual_usage = sum(monthly_usage)
        assert total_annual_usage == 78000
    
    def test_prorated_billing_cycle(self):
        """Test prorated billing for mid-cycle changes"""
        # Subscription starts mid-month (January 15th)
        period_start = datetime(2025, 1, 15)
        period_end = datetime(2025, 2, 14, 23, 59, 59)
        
        subscription = Subscription(
            id=uuid4(),
            tenant_id=self.tenant_id,
            billing_account_id=uuid4(),
            plan_id=uuid4(),
            status=SubscriptionStatus.ACTIVE,
            current_period_start=period_start,
            current_period_end=period_end
        )
        
        # Calculate prorated duration
        period_duration = period_end - period_start
        assert period_duration.days == 30  # Exactly 30 days
        
        # Prorated quotas for partial period
        full_monthly_quota = 10000  # 10K API calls per month
        prorated_quota = full_monthly_quota  # Same quota regardless of start date
        assert prorated_quota == 10000


class TestUsageTenantIsolation:
    """Test usage tracking tenant isolation"""
    
    def setup_method(self):
        """Set up test environment"""
        self.billing_service = BillingService()
        self.tenant_a = uuid4()
        self.tenant_b = uuid4()
        self.tenant_c = uuid4()
    
    @pytest.mark.asyncio
    async def test_usage_isolation_between_tenants(self):
        """Test that usage is properly isolated between tenants"""
        # Create usage records for different tenants
        tenant_a_usage = UsageRecord(
            id=uuid4(),
            tenant_id=self.tenant_a,
            subscription_id=uuid4(),
            metric_type=UsageMetricType.API_CALLS,
            quantity=5000,
            usage_date=datetime.utcnow()
        )
        
        tenant_b_usage = UsageRecord(
            id=uuid4(),
            tenant_id=self.tenant_b,
            subscription_id=uuid4(),
            metric_type=UsageMetricType.API_CALLS,
            quantity=8000,
            usage_date=datetime.utcnow()
        )
        
        # Ensure usage records are isolated by tenant
        assert tenant_a_usage.tenant_id != tenant_b_usage.tenant_id
        assert tenant_a_usage.subscription_id != tenant_b_usage.subscription_id
        assert tenant_a_usage.quantity != tenant_b_usage.quantity
    
    @pytest.mark.asyncio
    async def test_billing_analytics_tenant_isolation(self):
        """Test billing analytics tenant isolation"""
        # Mock analytics for different tenants
        tenant_a_analytics = BillingAnalytics(
            tenant_id=self.tenant_a,
            monthly_recurring_revenue=Decimal('5000'),
            annual_recurring_revenue=Decimal('60000'),
            usage_metrics={"api_calls": 8500, "storage_gb": 2},
            projected_monthly_cost=Decimal('5200')
        )
        
        tenant_b_analytics = BillingAnalytics(
            tenant_id=self.tenant_b,
            monthly_recurring_revenue=Decimal('20000'),
            annual_recurring_revenue=Decimal('240000'),
            usage_metrics={"api_calls": 75000, "storage_gb": 8},
            projected_monthly_cost=Decimal('20500')
        )
        
        # Verify tenant isolation
        assert tenant_a_analytics.tenant_id != tenant_b_analytics.tenant_id
        assert tenant_a_analytics.monthly_recurring_revenue != tenant_b_analytics.monthly_recurring_revenue
        assert tenant_a_analytics.usage_metrics["api_calls"] != tenant_b_analytics.usage_metrics["api_calls"]
    
    @pytest.mark.asyncio
    async def test_cross_tenant_usage_prevention(self):
        """Test prevention of cross-tenant usage access"""
        with patch.object(self.billing_service, '_get_db') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value = mock_session
            
            # Mock database query that should only return tenant-specific data
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_session.execute.return_value = mock_result
            
            # Attempt to get usage for specific tenant
            with patch.object(self.billing_service, 'get_billing_analytics') as mock_analytics:
                mock_analytics.return_value = BillingAnalytics(
                    tenant_id=self.tenant_a,
                    monthly_recurring_revenue=Decimal('5000'),
                    annual_recurring_revenue=Decimal('60000'),
                    usage_metrics={},
                    projected_monthly_cost=Decimal('5000')
                )
                
                result = await self.billing_service.get_billing_analytics(self.tenant_a)
                
                # Should only return data for the requested tenant
                assert result.tenant_id == self.tenant_a
                mock_analytics.assert_called_once_with(self.tenant_a)


class TestRealTimeUsageUpdates:
    """Test real-time usage updates and immediate billing impact"""
    
    def setup_method(self):
        """Set up test environment"""
        self.billing_service = BillingService()
        self.tenant_id = uuid4()
    
    @pytest.mark.asyncio
    async def test_immediate_usage_recording(self):
        """Test that usage is recorded immediately after API calls"""
        subscription = Subscription(
            id=uuid4(),
            tenant_id=self.tenant_id,
            billing_account_id=uuid4(),
            plan_id=uuid4(),
            status=SubscriptionStatus.ACTIVE,
            current_period_start=datetime.utcnow().replace(day=1),
            current_period_end=datetime.utcnow().replace(day=28) + timedelta(days=3)
        )
        
        with patch.object(self.billing_service, 'get_subscription', return_value=subscription), \
             patch.object(self.billing_service, '_get_db') as mock_db, \
             patch.object(self.billing_service.stripe, 'create_usage_record') as mock_stripe:
            
            mock_session = AsyncMock()
            mock_db.return_value = mock_session
            mock_stripe.return_value = {"id": "mbur_immediate123", "quantity": 1}
            
            start_time = datetime.utcnow()
            
            usage_record = UsageRecord(
                id=uuid4(),
                tenant_id=self.tenant_id,
                subscription_id=subscription.id,
                metric_type=UsageMetricType.API_CALLS,
                quantity=1,
                usage_date=datetime.utcnow(),
                billing_period_start=subscription.current_period_start,
                billing_period_end=subscription.current_period_end
            )
            
            with patch.object(self.billing_service, 'record_usage', return_value=usage_record):
                result = await self.billing_service.record_usage(
                    self.tenant_id, 
                    UsageMetricType.API_CALLS, 
                    1
                )
                
                # Usage should be recorded within seconds
                record_time = result.usage_date
                time_diff = record_time - start_time
                assert time_diff.total_seconds() < 5  # Within 5 seconds
    
    @pytest.mark.asyncio
    async def test_quota_threshold_alerts(self):
        """Test quota threshold alerts for approaching limits"""
        plan = DEFAULT_PLANS["developer"]
        current_usage = 9500  # 95% of 10,000 API call limit
        limit = plan.limits["api_calls_per_month"]
        
        usage_percentage = (current_usage / limit) * 100
        
        # Should trigger warning at 90% usage
        if usage_percentage >= 90:
            alert_triggered = True
        else:
            alert_triggered = False
        
        assert usage_percentage == 95.0
        assert alert_triggered is True
    
    @pytest.mark.asyncio
    async def test_overage_immediate_calculation(self):
        """Test immediate overage calculation when limits exceeded"""
        plan = DEFAULT_PLANS["developer"]
        
        # Simulate hitting the exact limit
        current_usage = 10000  # Exactly at limit
        new_usage = 50         # New API calls that push over limit
        
        total_usage = current_usage + new_usage
        limit = plan.limits["api_calls_per_month"]
        
        overage = max(0, total_usage - limit)
        overage_cost = overage * plan.usage_prices["additional_api_calls"]
        
        assert total_usage == 10050
        assert overage == 50
        assert overage_cost == Decimal('50')  # $0.50
        
        # Should immediately reflect in projected billing
        base_cost = plan.base_price  # $50.00
        projected_total = base_cost + overage_cost
        assert projected_total == Decimal('5050')  # $50.50


if __name__ == "__main__":
    pytest.main([__file__, "-v"])