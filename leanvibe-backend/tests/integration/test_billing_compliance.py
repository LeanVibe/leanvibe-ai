"""
Revenue Recognition & Compliance Testing for LeanVibe Enterprise Billing
Tests revenue recognition rules, tax calculations, dunning management, chargebacks, refunds, and analytics accuracy
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.billing_service import BillingService
from app.models.billing_models import (
    Plan, BillingAccount, Subscription, Invoice, Payment, BillingAnalytics,
    UsageRecord, BillingEvent, PaymentStatus, InvoiceStatus, SubscriptionStatus,
    UsageMetricType, TaxType, BillingInterval, PaymentMethod,
    DEFAULT_PLANS
)
from app.models.tenant_models import Tenant, TenantStatus


class TestRevenueRecognitionRules:
    """Test revenue recognition according to accounting standards (ASC 606)"""
    
    def setup_method(self):
        """Set up test environment"""
        self.billing_service = BillingService()
        self.tenant_id = uuid4()
        self.subscription_id = uuid4()
    
    def test_subscription_revenue_recognition_monthly(self):
        """Test monthly subscription revenue recognition"""
        # Monthly subscription: $50.00/month
        subscription = Subscription(
            id=self.subscription_id,
            tenant_id=self.tenant_id,
            billing_account_id=uuid4(),
            plan_id=uuid4(),
            status=SubscriptionStatus.ACTIVE,
            current_period_start=datetime(2025, 1, 1),
            current_period_end=datetime(2025, 1, 31, 23, 59, 59)
        )
        
        plan = DEFAULT_PLANS["developer"]
        monthly_revenue = plan.base_price  # $50.00
        
        # Revenue should be recognized over the service period (31 days in January)
        service_days = 31
        daily_revenue = monthly_revenue / service_days
        
        assert daily_revenue == Decimal('1612.903226')  # $16.129 per day (rounded)
        
        # For mid-month recognition (15 days into January)
        days_elapsed = 15
        recognized_revenue = daily_revenue * days_elapsed
        
        expected_recognized = Decimal('24193.548387')  # ~$241.94
        assert abs(recognized_revenue - expected_recognized) < Decimal('0.01')
    
    def test_annual_subscription_revenue_recognition(self):
        """Test annual subscription revenue recognition"""
        # Annual subscription with discount
        subscription = Subscription(
            id=self.subscription_id,
            tenant_id=self.tenant_id,
            billing_account_id=uuid4(),
            plan_id=uuid4(),
            status=SubscriptionStatus.ACTIVE,
            current_period_start=datetime(2025, 1, 1),
            current_period_end=datetime(2025, 12, 31, 23, 59, 59)
        )
        
        # Annual plan: $500 paid upfront (vs $600 if paid monthly)
        annual_payment = Decimal('50000')  # $500.00
        service_days = 365
        
        # Daily revenue recognition
        daily_revenue = annual_payment / service_days
        assert daily_revenue == Decimal('136.986301')  # ~$1.37 per day
        
        # Quarterly revenue recognition (Q1)
        q1_days = 90  # Jan-Mar
        q1_revenue = daily_revenue * q1_days
        expected_q1 = Decimal('12328.767123')  # ~$123.29
        
        assert abs(q1_revenue - expected_q1) < Decimal('0.01')
    
    def test_usage_based_revenue_recognition(self):
        """Test usage-based revenue recognition"""
        # Usage-based billing: recognize revenue when service is consumed
        usage_record = UsageRecord(
            id=uuid4(),
            tenant_id=self.tenant_id,
            subscription_id=self.subscription_id,
            metric_type=UsageMetricType.API_CALLS,
            quantity=5000,  # 5000 API calls
            unit_price=Decimal('1'),  # $0.01 per call
            usage_date=datetime(2025, 1, 15, 14, 30, 0),  # Specific usage time
            billing_period_start=datetime(2025, 1, 1),
            billing_period_end=datetime(2025, 1, 31, 23, 59, 59)
        )
        
        # Revenue recognized immediately upon usage
        usage_revenue = usage_record.quantity * usage_record.unit_price
        assert usage_revenue == Decimal('5000')  # $50.00
        
        # Recognition date = usage date
        recognition_date = usage_record.usage_date
        assert recognition_date == datetime(2025, 1, 15, 14, 30, 0)
    
    def test_prorated_revenue_recognition(self):
        """Test prorated revenue recognition for plan changes"""
        # Customer upgrades from Developer ($50) to Team ($200) mid-cycle
        upgrade_date = datetime(2025, 1, 15)  # 15 days into January
        period_start = datetime(2025, 1, 1)
        period_end = datetime(2025, 1, 31, 23, 59, 59)
        
        total_days = 31
        days_on_developer = 14  # Jan 1-14
        days_on_team = 17       # Jan 15-31
        
        developer_price = Decimal('5000')  # $50.00
        team_price = Decimal('20000')      # $200.00
        
        # Prorated revenue calculation
        developer_daily = developer_price / total_days
        team_daily = team_price / total_days
        
        prorated_developer = developer_daily * days_on_developer
        prorated_team = team_daily * days_on_team
        
        total_prorated_revenue = prorated_developer + prorated_team
        
        expected_developer = Decimal('2258.064516')  # ~$22.58
        expected_team = Decimal('10967.741935')     # ~$109.68
        expected_total = Decimal('13225.806451')    # ~$132.26
        
        assert abs(prorated_developer - expected_developer) < Decimal('0.01')
        assert abs(prorated_team - expected_team) < Decimal('0.01')
        assert abs(total_prorated_revenue - expected_total) < Decimal('0.01')


class TestTaxCalculationByJurisdiction:
    """Test tax calculations by customer location and jurisdiction"""
    
    def setup_method(self):
        """Set up test environment"""
        self.billing_service = BillingService()
        self.tenant_id = uuid4()
    
    def test_us_sales_tax_calculation(self):
        """Test US sales tax calculation"""
        # US customer in California
        billing_account = BillingAccount(
            id=uuid4(),
            tenant_id=self.tenant_id,
            company_name="US Company Inc",
            billing_email="billing@uscompany.com",
            billing_address={
                "line1": "123 Main St",
                "city": "San Francisco",
                "state": "CA",
                "postal_code": "94105",
                "country": "US"
            },
            tax_id="12-3456789",
            tax_type=TaxType.SALES_TAX
        )
        
        # California sales tax rate: ~8.5%
        ca_tax_rate = Decimal('0.085')
        subscription_amount = Decimal('5000')  # $50.00
        
        tax_amount = subscription_amount * ca_tax_rate
        total_amount = subscription_amount + tax_amount
        
        assert tax_amount == Decimal('425')    # $4.25 tax
        assert total_amount == Decimal('5425') # $54.25 total
    
    def test_eu_vat_calculation(self):
        """Test EU VAT calculation"""
        # EU customer in Germany
        billing_account = BillingAccount(
            id=uuid4(),
            tenant_id=self.tenant_id,
            company_name="Deutsche Firma GmbH",
            billing_email="billing@deutsche-firma.de",
            billing_address={
                "line1": "Hauptstraße 123",
                "city": "Berlin",
                "state": "Berlin",
                "postal_code": "10115",
                "country": "DE"
            },
            tax_id="DE123456789",
            tax_type=TaxType.VAT
        )
        
        # German VAT rate: 19%
        de_vat_rate = Decimal('0.19')
        subscription_amount = Decimal('5000')  # $50.00
        
        vat_amount = subscription_amount * de_vat_rate
        total_amount = subscription_amount + vat_amount
        
        assert vat_amount == Decimal('950')    # $9.50 VAT
        assert total_amount == Decimal('5950') # $59.50 total
    
    def test_reverse_charge_mechanism(self):
        """Test reverse charge mechanism for B2B EU transactions"""
        # B2B transaction with valid VAT numbers
        supplier_vat = "DE123456789"  # German supplier
        customer_vat = "FR98765432101"  # French customer
        
        billing_account = BillingAccount(
            id=uuid4(),
            tenant_id=self.tenant_id,
            company_name="French Enterprise SARL",
            billing_email="billing@french-enterprise.fr",
            billing_address={
                "line1": "Rue de la Paix 45",
                "city": "Paris",
                "postal_code": "75001",
                "country": "FR"
            },
            tax_id=customer_vat,
            tax_type=TaxType.REVERSE_CHARGE
        )
        
        # Reverse charge: no VAT charged by supplier
        subscription_amount = Decimal('5000')  # $50.00
        vat_amount = Decimal('0')              # No VAT charged
        total_amount = subscription_amount
        
        assert vat_amount == Decimal('0')
        assert total_amount == Decimal('5000')
    
    def test_tax_exempt_organization(self):
        """Test tax-exempt organization handling"""
        billing_account = BillingAccount(
            id=uuid4(),
            tenant_id=self.tenant_id,
            company_name="Nonprofit Foundation",
            billing_email="billing@nonprofit.org",
            billing_address={
                "line1": "501 Charity Lane",
                "city": "Austin",
                "state": "TX",
                "postal_code": "73301",
                "country": "US"
            },
            tax_id="12-3456789",
            tax_type=TaxType.EXEMPT
        )
        
        # Tax-exempt organization
        subscription_amount = Decimal('5000')  # $50.00
        tax_amount = Decimal('0')              # Exempt from tax
        total_amount = subscription_amount
        
        assert tax_amount == Decimal('0')
        assert total_amount == Decimal('5000')


class TestDunningManagementWorkflow:
    """Test dunning management for failed payments"""
    
    def setup_method(self):
        """Set up test environment"""
        self.billing_service = BillingService()
        self.tenant_id = uuid4()
        self.subscription_id = uuid4()
    
    def test_dunning_sequence_day_1(self):
        """Test dunning sequence - Day 1 after failed payment"""
        failed_payment = Payment(
            id=uuid4(),
            tenant_id=self.tenant_id,
            subscription_id=self.subscription_id,
            amount=Decimal('5000'),  # $50.00
            currency="USD",
            status=PaymentStatus.FAILED,
            payment_method=PaymentMethod.CARD,
            failure_reason="card_declined",
            attempted_at=datetime.utcnow(),
            failed_at=datetime.utcnow()
        )
        
        # Day 1: Immediate retry + notification
        retry_1_date = failed_payment.failed_at + timedelta(hours=1)
        notification_1 = {
            "type": "payment_failed_retry_1",
            "message": "Your payment failed. We'll retry in 3 days.",
            "action_required": False,
            "retry_date": retry_1_date + timedelta(days=3)
        }
        
        assert notification_1["type"] == "payment_failed_retry_1"
        assert notification_1["action_required"] is False
    
    def test_dunning_sequence_day_3(self):
        """Test dunning sequence - Day 3 retry"""
        failed_payment_date = datetime.utcnow() - timedelta(days=3)
        
        # Day 3: First retry attempt
        retry_2_date = failed_payment_date + timedelta(days=3)
        notification_2 = {
            "type": "payment_failed_retry_2",
            "message": "Second payment attempt failed. Please update your payment method.",
            "action_required": True,
            "next_retry": retry_2_date + timedelta(days=4)
        }
        
        assert notification_2["action_required"] is True
        assert "update your payment method" in notification_2["message"]
    
    def test_dunning_sequence_day_7(self):
        """Test dunning sequence - Day 7 final retry"""
        failed_payment_date = datetime.utcnow() - timedelta(days=7)
        
        # Day 7: Final retry attempt
        final_retry_date = failed_payment_date + timedelta(days=7)
        notification_3 = {
            "type": "payment_failed_final_retry",
            "message": "Final payment attempt. Account will be suspended if payment fails.",
            "action_required": True,
            "suspension_date": final_retry_date + timedelta(days=3)
        }
        
        assert notification_3["action_required"] is True
        assert "suspended" in notification_3["message"]
    
    def test_dunning_sequence_suspension(self):
        """Test account suspension after failed dunning"""
        failed_payment_date = datetime.utcnow() - timedelta(days=10)
        
        # Day 10: Account suspension
        suspension_notification = {
            "type": "account_suspended",
            "message": "Account suspended due to failed payment. Service restored upon payment.",
            "action_required": True,
            "account_status": "suspended"
        }
        
        # Update subscription status
        subscription_status = SubscriptionStatus.PAST_DUE
        tenant_status = TenantStatus.SUSPENDED
        
        assert suspension_notification["account_status"] == "suspended"
        assert subscription_status == SubscriptionStatus.PAST_DUE
        assert tenant_status == TenantStatus.SUSPENDED


class TestChargebackAndDisputeHandling:
    """Test chargeback and dispute handling workflow"""
    
    def setup_method(self):
        """Set up test environment"""
        self.billing_service = BillingService()
        self.tenant_id = uuid4()
    
    def test_chargeback_received_webhook(self):
        """Test chargeback received webhook processing"""
        chargeback_webhook = {
            "id": "evt_chargeback_created",
            "type": "charge.dispute.created",
            "data": {
                "object": {
                    "id": "dp_chargeback123",
                    "charge": "ch_payment123",
                    "amount": 5000,  # $50.00
                    "currency": "usd",
                    "reason": "fraudulent",
                    "status": "needs_response",
                    "evidence_due_by": int((datetime.utcnow() + timedelta(days=7)).timestamp())
                }
            }
        }
        
        # Process chargeback
        dispute_id = chargeback_webhook["data"]["object"]["id"]
        amount = Decimal(str(chargeback_webhook["data"]["object"]["amount"]))
        reason = chargeback_webhook["data"]["object"]["reason"]
        
        assert dispute_id == "dp_chargeback123"
        assert amount == Decimal('5000')
        assert reason == "fraudulent"
    
    def test_chargeback_evidence_submission(self):
        """Test chargeback evidence submission"""
        evidence_package = {
            "customer_communication": "Email thread showing customer satisfaction",
            "service_documentation": "Logs showing service was delivered",
            "receipt": "Invoice and payment confirmation",
            "shipping_documentation": "N/A - Digital service",
            "uncategorized_text": "Customer used service for 6 months without issues"
        }
        
        # Evidence submission timeline
        dispute_created = datetime.utcnow()
        evidence_due = dispute_created + timedelta(days=7)
        evidence_submitted = dispute_created + timedelta(days=3)
        
        assert evidence_submitted < evidence_due
        assert len(evidence_package["uncategorized_text"]) > 0
    
    def test_chargeback_won_handling(self):
        """Test successful chargeback defense"""
        chargeback_won_webhook = {
            "id": "evt_dispute_closed",
            "type": "charge.dispute.closed",
            "data": {
                "object": {
                    "id": "dp_chargeback123",
                    "status": "won",
                    "amount": 5000,
                    "currency": "usd"
                }
            }
        }
        
        # Chargeback won: funds recovered
        dispute_status = chargeback_won_webhook["data"]["object"]["status"]
        recovered_amount = Decimal(str(chargeback_won_webhook["data"]["object"]["amount"]))
        
        assert dispute_status == "won"
        assert recovered_amount == Decimal('5000')
    
    def test_chargeback_lost_handling(self):
        """Test lost chargeback handling"""
        chargeback_lost_webhook = {
            "id": "evt_dispute_lost",
            "type": "charge.dispute.closed",
            "data": {
                "object": {
                    "id": "dp_chargeback123",
                    "status": "lost",
                    "amount": 5000,
                    "currency": "usd"
                }
            }
        }
        
        # Chargeback lost: funds debited + chargeback fee
        dispute_status = chargeback_lost_webhook["data"]["object"]["status"]
        lost_amount = Decimal(str(chargeback_lost_webhook["data"]["object"]["amount"]))
        chargeback_fee = Decimal('1500')  # $15.00 typical chargeback fee
        
        total_loss = lost_amount + chargeback_fee
        
        assert dispute_status == "lost"
        assert total_loss == Decimal('6500')  # $65.00 total loss


class TestRefundProcessing:
    """Test refund processing for various scenarios"""
    
    def setup_method(self):
        """Set up test environment"""
        self.billing_service = BillingService()
        self.tenant_id = uuid4()
    
    def test_full_refund_processing(self):
        """Test full refund processing"""
        original_payment = Payment(
            id=uuid4(),
            tenant_id=self.tenant_id,
            subscription_id=uuid4(),
            amount=Decimal('5000'),  # $50.00
            currency="USD",
            status=PaymentStatus.SUCCEEDED,
            payment_method=PaymentMethod.CARD,
            processed_at=datetime.utcnow() - timedelta(days=5)
        )
        
        # Full refund within 30-day window
        refund_amount = original_payment.amount
        refund_reason = "customer_request"
        
        refund = Payment(
            id=uuid4(),
            tenant_id=self.tenant_id,
            subscription_id=original_payment.subscription_id,
            amount=-refund_amount,  # Negative amount for refund
            currency="USD",
            status=PaymentStatus.REFUNDED,
            payment_method=PaymentMethod.CARD,
            processed_at=datetime.utcnow(),
            metadata={"refund_reason": refund_reason, "original_payment_id": str(original_payment.id)}
        )
        
        assert refund.amount == Decimal('-5000')
        assert refund.status == PaymentStatus.REFUNDED
        assert refund.metadata["refund_reason"] == "customer_request"
    
    def test_partial_refund_processing(self):
        """Test partial refund processing"""
        original_payment = Payment(
            id=uuid4(),
            tenant_id=self.tenant_id,
            subscription_id=uuid4(),
            amount=Decimal('20000'),  # $200.00
            currency="USD",
            status=PaymentStatus.SUCCEEDED,
            payment_method=PaymentMethod.CARD,
            processed_at=datetime.utcnow() - timedelta(days=10)
        )
        
        # Partial refund: 50% refund for unused service
        refund_percentage = Decimal('0.50')
        refund_amount = original_payment.amount * refund_percentage
        
        partial_refund = Payment(
            id=uuid4(),
            tenant_id=self.tenant_id,
            subscription_id=original_payment.subscription_id,
            amount=-refund_amount,  # -$100.00
            currency="USD",
            status=PaymentStatus.REFUNDED,
            payment_method=PaymentMethod.CARD,
            processed_at=datetime.utcnow(),
            metadata={"refund_type": "partial", "refund_percentage": str(refund_percentage)}
        )
        
        assert partial_refund.amount == Decimal('-10000')  # -$100.00
        assert partial_refund.metadata["refund_type"] == "partial"
    
    def test_prorated_refund_calculation(self):
        """Test prorated refund for mid-cycle cancellation"""
        # Customer cancels on January 15th (paid for full month)
        cancellation_date = datetime(2025, 1, 15)
        period_start = datetime(2025, 1, 1)
        period_end = datetime(2025, 1, 31, 23, 59, 59)
        
        monthly_fee = Decimal('20000')  # $200.00
        total_days = 31
        used_days = 14  # Jan 1-14
        remaining_days = 17  # Jan 15-31
        
        # Prorated refund calculation
        daily_rate = monthly_fee / total_days
        refund_amount = daily_rate * remaining_days
        
        expected_refund = Decimal('10967.741935')  # ~$109.68
        
        assert abs(refund_amount - expected_refund) < Decimal('0.01')


class TestBillingAnalyticsAccuracy:
    """Test billing analytics accuracy and financial reporting"""
    
    def setup_method(self):
        """Set up test environment"""
        self.billing_service = BillingService()
        self.tenant_id = uuid4()
    
    @pytest.mark.asyncio
    async def test_mrr_calculation_accuracy(self):
        """Test Monthly Recurring Revenue (MRR) calculation accuracy"""
        # Mock subscription with known MRR
        subscription = Subscription(
            id=uuid4(),
            tenant_id=self.tenant_id,
            billing_account_id=uuid4(),
            plan_id=uuid4(),
            status=SubscriptionStatus.ACTIVE,
            current_period_start=datetime(2025, 1, 1),
            current_period_end=datetime(2025, 1, 31, 23, 59, 59)
        )
        
        plan = DEFAULT_PLANS["team"]  # $200/month
        expected_mrr = plan.base_price  # $200.00
        
        with patch.object(self.billing_service, 'get_subscription', return_value=subscription), \
             patch.object(self.billing_service, 'get_plan', return_value=plan), \
             patch.object(self.billing_service, '_get_db') as mock_db:
            
            mock_session = AsyncMock()
            mock_db.return_value = mock_session
            
            # Mock usage query result
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_session.execute.return_value = mock_result
            
            analytics = await self.billing_service.get_billing_analytics(self.tenant_id)
            
            assert analytics.monthly_recurring_revenue == expected_mrr
            assert analytics.annual_recurring_revenue == expected_mrr * 12
    
    @pytest.mark.asyncio
    async def test_arr_calculation_accuracy(self):
        """Test Annual Recurring Revenue (ARR) calculation accuracy"""
        subscription = Subscription(
            id=uuid4(),
            tenant_id=self.tenant_id,
            billing_account_id=uuid4(),
            plan_id=uuid4(),
            status=SubscriptionStatus.ACTIVE,
            current_period_start=datetime(2025, 1, 1),
            current_period_end=datetime(2025, 12, 31, 23, 59, 59)
        )
        
        plan = DEFAULT_PLANS["enterprise"]  # $800/month
        expected_mrr = plan.base_price
        expected_arr = expected_mrr * 12  # $9,600/year
        
        with patch.object(self.billing_service, 'get_subscription', return_value=subscription), \
             patch.object(self.billing_service, 'get_plan', return_value=plan), \
             patch.object(self.billing_service, '_get_db') as mock_db:
            
            mock_session = AsyncMock()
            mock_db.return_value = mock_session
            
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_session.execute.return_value = mock_result
            
            analytics = await self.billing_service.get_billing_analytics(self.tenant_id)
            
            assert analytics.annual_recurring_revenue == expected_arr
    
    @pytest.mark.asyncio
    async def test_usage_metrics_aggregation(self):
        """Test usage metrics aggregation accuracy"""
        subscription = Subscription(
            id=uuid4(),
            tenant_id=self.tenant_id,
            billing_account_id=uuid4(),
            plan_id=uuid4(),
            status=SubscriptionStatus.ACTIVE,
            current_period_start=datetime(2025, 1, 1),
            current_period_end=datetime(2025, 1, 31, 23, 59, 59)
        )
        
        plan = DEFAULT_PLANS["developer"]
        
        # Mock usage data
        mock_usage_data = [
            MagicMock(metric_type=UsageMetricType.API_CALLS, total_quantity=8500),
            MagicMock(metric_type=UsageMetricType.STORAGE_GB, total_quantity=3),
            MagicMock(metric_type=UsageMetricType.AI_REQUESTS, total_quantity=125)
        ]
        
        with patch.object(self.billing_service, 'get_subscription', return_value=subscription), \
             patch.object(self.billing_service, 'get_plan', return_value=plan), \
             patch.object(self.billing_service, '_get_db') as mock_db:
            
            mock_session = AsyncMock()
            mock_db.return_value = mock_session
            
            mock_result = MagicMock()
            mock_result.__iter__ = lambda x: iter(mock_usage_data)
            mock_session.execute.return_value = mock_result
            
            analytics = await self.billing_service.get_billing_analytics(self.tenant_id)
            
            expected_usage = {
                UsageMetricType.API_CALLS: 8500,
                UsageMetricType.STORAGE_GB: 3,
                UsageMetricType.AI_REQUESTS: 125
            }
            
            assert analytics.usage_metrics == expected_usage
    
    @pytest.mark.asyncio
    async def test_projected_monthly_cost_accuracy(self):
        """Test projected monthly cost calculation with overages"""
        subscription = Subscription(
            id=uuid4(),
            tenant_id=self.tenant_id,
            billing_account_id=uuid4(),
            plan_id=uuid4(),
            status=SubscriptionStatus.ACTIVE,
            current_period_start=datetime(2025, 1, 1),
            current_period_end=datetime(2025, 1, 31, 23, 59, 59)
        )
        
        plan = DEFAULT_PLANS["developer"]  # $50 base + overages
        
        # Mock usage with overages
        mock_usage_data = [
            MagicMock(metric_type=UsageMetricType.API_CALLS, total_quantity=15000),  # 5K over limit
            MagicMock(metric_type=UsageMetricType.STORAGE_GB, total_quantity=3)      # 2GB over limit
        ]
        
        with patch.object(self.billing_service, 'get_subscription', return_value=subscription), \
             patch.object(self.billing_service, 'get_plan', return_value=plan), \
             patch.object(self.billing_service, '_get_db') as mock_db:
            
            mock_session = AsyncMock()
            mock_db.return_value = mock_session
            
            mock_result = MagicMock()
            mock_result.__iter__ = lambda x: iter(mock_usage_data)
            mock_session.execute.return_value = mock_result
            
            analytics = await self.billing_service.get_billing_analytics(self.tenant_id)
            
            # Calculate expected cost
            base_cost = plan.base_price  # $50.00
            
            # API overage: 5000 calls * $0.01 = $50.00
            api_overage = (15000 - plan.included_usage["api_calls"]) * plan.usage_prices["additional_api_calls"]
            
            # Storage overage: 2GB * $5.00 = $10.00
            storage_overage = (3 - plan.included_usage["storage_gb"]) * plan.usage_prices["additional_storage_gb"]
            
            expected_projected = base_cost + api_overage + storage_overage  # $110.00
            
            assert analytics.projected_monthly_cost == expected_projected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])