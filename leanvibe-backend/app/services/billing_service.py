"""
Enterprise billing service for LeanVibe SaaS Platform
Handles Stripe integration, subscription management, and usage-based billing
"""

import logging
import secrets
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, func

from ..models.billing_models import (
    Plan, BillingAccount, Subscription, UsageRecord, Invoice, Payment, BillingEvent,
    CreateSubscriptionRequest, UpdateSubscriptionRequest, BillingAnalytics,
    BillingStatus, SubscriptionStatus, PaymentStatus, InvoiceStatus, UsageMetricType,
    DEFAULT_PLANS
)
from ..models.tenant_models import Tenant, TenantStatus
from ..core.database import get_database_session
from ..core.exceptions import (
    ResourceNotFoundError, InvalidCredentialsError, PaymentRequiredError,
    PaymentFailedError, SubscriptionExpiredError
)
from ..config.settings import settings

logger = logging.getLogger(__name__)


class StripeIntegration:
    """Stripe API integration wrapper"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.stripe_secret_key
        self.webhook_secret = settings.stripe_webhook_secret
    
    async def create_customer(self, billing_account: BillingAccount) -> str:
        """Create Stripe customer"""
        # Mock implementation - in production, use Stripe Python library
        customer_data = {
            "email": billing_account.billing_email,
            "name": billing_account.company_name,
            "address": billing_account.billing_address,
            "metadata": {
                "tenant_id": str(billing_account.tenant_id),
                "billing_account_id": str(billing_account.id)
            }
        }
        
        # Mock Stripe customer ID
        stripe_customer_id = f"cus_mock_{secrets.token_hex(8)}"
        logger.info(f"Mock Stripe customer created: {stripe_customer_id}")
        
        return stripe_customer_id
    
    async def create_subscription(
        self, 
        customer_id: str, 
        price_id: str, 
        trial_period_days: int = None
    ) -> Dict:
        """Create Stripe subscription"""
        # Mock implementation
        subscription_data = {
            "id": f"sub_mock_{secrets.token_hex(8)}",
            "customer": customer_id,
            "status": "trialing" if trial_period_days else "active",
            "current_period_start": int(datetime.utcnow().timestamp()),
            "current_period_end": int((datetime.utcnow() + timedelta(days=30)).timestamp()),
            "trial_start": int(datetime.utcnow().timestamp()) if trial_period_days else None,
            "trial_end": int((datetime.utcnow() + timedelta(days=trial_period_days)).timestamp()) if trial_period_days else None,
        }
        
        logger.info(f"Mock Stripe subscription created: {subscription_data['id']}")
        return subscription_data
    
    async def update_subscription(self, subscription_id: str, **kwargs) -> Dict:
        """Update Stripe subscription"""
        # Mock implementation
        logger.info(f"Mock Stripe subscription updated: {subscription_id}")
        return {"id": subscription_id, "status": "active"}
    
    async def cancel_subscription(self, subscription_id: str, at_period_end: bool = True) -> Dict:
        """Cancel Stripe subscription"""
        # Mock implementation
        status = "active" if at_period_end else "canceled"
        logger.info(f"Mock Stripe subscription cancelled: {subscription_id}, at_period_end: {at_period_end}")
        return {"id": subscription_id, "status": status, "cancel_at_period_end": at_period_end}
    
    async def create_usage_record(self, subscription_item_id: str, quantity: int, timestamp: int = None) -> Dict:
        """Create usage record in Stripe"""
        # Mock implementation
        usage_record = {
            "id": f"mbur_mock_{secrets.token_hex(8)}",
            "quantity": quantity,
            "timestamp": timestamp or int(datetime.utcnow().timestamp()),
            "subscription_item": subscription_item_id
        }
        
        logger.info(f"Mock Stripe usage record created: {usage_record['id']}")
        return usage_record
    
    async def verify_webhook(self, payload: bytes, signature: str) -> Dict:
        """Verify Stripe webhook signature"""
        # Mock implementation - in production, use Stripe's webhook verification
        import json
        logger.info(f"Mock webhook verification successful")
        return json.loads(payload.decode())


class BillingService:
    """Enterprise billing service"""
    
    def __init__(self, db: AsyncSession = None):
        self.db = db
        self.stripe = StripeIntegration()
    
    async def _get_db(self) -> AsyncSession:
        """Get database session"""
        if self.db:
            return self.db
        return await get_database_session()
    
    async def create_billing_account(self, tenant_id: UUID, account_data: Dict) -> BillingAccount:
        """Create billing account for tenant"""
        db = await self._get_db()
        
        try:
            # Create billing account
            billing_account = BillingAccount(
                tenant_id=tenant_id,
                company_name=account_data["company_name"],
                billing_email=account_data["billing_email"],
                billing_address=account_data.get("billing_address", {}),
                tax_id=account_data.get("tax_id"),
                tax_type=account_data.get("tax_type", "none")
            )
            
            # Create Stripe customer
            stripe_customer_id = await self.stripe.create_customer(billing_account)
            billing_account.stripe_customer_id = stripe_customer_id
            
            # Save to database
            db.add(billing_account)
            await db.commit()
            await db.refresh(billing_account)
            
            logger.info(f"Created billing account for tenant {tenant_id}")
            return billing_account
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to create billing account: {e}")
            raise
    
    async def get_billing_account(self, tenant_id: UUID) -> Optional[BillingAccount]:
        """Get billing account by tenant ID"""
        db = await self._get_db()
        
        result = await db.execute(
            select(BillingAccount).where(BillingAccount.tenant_id == tenant_id)
        )
        return result.scalar_one_or_none()
    
    async def create_subscription(
        self, 
        tenant_id: UUID, 
        request: CreateSubscriptionRequest
    ) -> Subscription:
        """Create new subscription"""
        db = await self._get_db()
        
        try:
            # Get billing account
            billing_account = await self.get_billing_account(tenant_id)
            if not billing_account:
                raise ResourceNotFoundError("Billing account not found")
            
            # Get plan
            plan = await self.get_plan(request.plan_id)
            if not plan:
                raise ResourceNotFoundError("Plan not found")
            
            # Calculate trial period
            trial_days = request.trial_period_days or plan.trial_period_days
            trial_start = datetime.utcnow() if trial_days > 0 else None
            trial_end = trial_start + timedelta(days=trial_days) if trial_start else None
            
            # Create Stripe subscription
            stripe_subscription = await self.stripe.create_subscription(
                customer_id=billing_account.stripe_customer_id,
                price_id=plan.stripe_price_id or f"price_mock_{plan.slug}",
                trial_period_days=trial_days if trial_days > 0 else None
            )
            
            # Create local subscription
            subscription = Subscription(
                tenant_id=tenant_id,
                billing_account_id=billing_account.id,
                plan_id=request.plan_id,
                status=SubscriptionStatus.TRIALING if trial_days > 0 else SubscriptionStatus.ACTIVE,
                current_period_start=datetime.fromtimestamp(stripe_subscription["current_period_start"]),
                current_period_end=datetime.fromtimestamp(stripe_subscription["current_period_end"]),
                trial_start=trial_start,
                trial_end=trial_end,
                stripe_subscription_id=stripe_subscription["id"]
            )
            
            # Save to database
            db.add(subscription)
            await db.commit()
            await db.refresh(subscription)
            
            # Update tenant status
            await self._update_tenant_subscription_status(tenant_id, subscription.status)
            
            logger.info(f"Created subscription {subscription.id} for tenant {tenant_id}")
            return subscription
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to create subscription: {e}")
            raise
    
    async def get_subscription(self, tenant_id: UUID) -> Optional[Subscription]:
        """Get active subscription for tenant"""
        db = await self._get_db()
        
        result = await db.execute(
            select(Subscription)
            .where(
                and_(
                    Subscription.tenant_id == tenant_id,
                    Subscription.status.in_([
                        SubscriptionStatus.ACTIVE,
                        SubscriptionStatus.TRIALING,
                        SubscriptionStatus.PAST_DUE
                    ])
                )
            )
            .order_by(Subscription.created_at.desc())
        )
        return result.scalar_one_or_none()
    
    async def update_subscription(
        self, 
        tenant_id: UUID, 
        request: UpdateSubscriptionRequest
    ) -> Subscription:
        """Update existing subscription"""
        db = await self._get_db()
        
        try:
            # Get current subscription
            subscription = await self.get_subscription(tenant_id)
            if not subscription:
                raise ResourceNotFoundError("Active subscription not found")
            
            # Update in Stripe
            stripe_updates = {}
            if request.plan_id and request.plan_id != subscription.plan_id:
                new_plan = await self.get_plan(request.plan_id)
                stripe_updates["items"] = [{
                    "price": new_plan.stripe_price_id or f"price_mock_{new_plan.slug}"
                }]
            
            if request.cancel_at_period_end is not None:
                stripe_updates["cancel_at_period_end"] = request.cancel_at_period_end
            
            if stripe_updates:
                await self.stripe.update_subscription(
                    subscription.stripe_subscription_id,
                    **stripe_updates
                )
            
            # Update local subscription
            if request.plan_id:
                subscription.plan_id = request.plan_id
            
            if request.cancel_at_period_end is not None:
                subscription.cancel_at_period_end = request.cancel_at_period_end
                if request.cancel_at_period_end:
                    subscription.cancelled_at = datetime.utcnow()
            
            subscription.updated_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(subscription)
            
            logger.info(f"Updated subscription {subscription.id}")
            return subscription
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to update subscription: {e}")
            raise
    
    async def cancel_subscription(self, tenant_id: UUID, immediately: bool = False) -> Subscription:
        """Cancel subscription"""
        db = await self._get_db()
        
        try:
            subscription = await self.get_subscription(tenant_id)
            if not subscription:
                raise ResourceNotFoundError("Active subscription not found")
            
            # Cancel in Stripe
            await self.stripe.cancel_subscription(
                subscription.stripe_subscription_id,
                at_period_end=not immediately
            )
            
            # Update local subscription
            subscription.cancelled_at = datetime.utcnow()
            subscription.cancel_at_period_end = not immediately
            
            if immediately:
                subscription.status = SubscriptionStatus.CANCELLED
                await self._update_tenant_subscription_status(tenant_id, subscription.status)
            
            subscription.updated_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(subscription)
            
            logger.info(f"Cancelled subscription {subscription.id}")
            return subscription
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to cancel subscription: {e}")
            raise
    
    async def record_usage(
        self, 
        tenant_id: UUID, 
        metric_type: UsageMetricType, 
        quantity: int,
        usage_date: datetime = None
    ) -> UsageRecord:
        """Record usage for metered billing"""
        db = await self._get_db()
        
        try:
            subscription = await self.get_subscription(tenant_id)
            if not subscription:
                raise ResourceNotFoundError("Active subscription not found")
            
            usage_date = usage_date or datetime.utcnow()
            
            # Determine billing period
            billing_period_start = subscription.current_period_start
            billing_period_end = subscription.current_period_end
            
            # Create usage record
            usage_record = UsageRecord(
                tenant_id=tenant_id,
                subscription_id=subscription.id,
                metric_type=metric_type,
                quantity=quantity,
                usage_date=usage_date,
                billing_period_start=billing_period_start,
                billing_period_end=billing_period_end
            )
            
            # Report to Stripe (for metered billing)
            if subscription.stripe_subscription_id:
                stripe_usage = await self.stripe.create_usage_record(
                    subscription_item_id=f"si_mock_{metric_type}",
                    quantity=quantity,
                    timestamp=int(usage_date.timestamp())
                )
                usage_record.stripe_usage_record_id = stripe_usage["id"]
            
            # Save to database
            db.add(usage_record)
            await db.commit()
            await db.refresh(usage_record)
            
            logger.info(f"Recorded usage: {metric_type}={quantity} for tenant {tenant_id}")
            return usage_record
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to record usage: {e}")
            raise
    
    async def get_plan(self, plan_id: UUID) -> Optional[Plan]:
        """Get plan by ID"""
        db = await self._get_db()
        
        result = await db.execute(
            select(Plan).where(Plan.id == plan_id)
        )
        return result.scalar_one_or_none()
    
    async def list_plans(self, include_inactive: bool = False) -> List[Plan]:
        """List available plans"""
        db = await self._get_db()
        
        query = select(Plan)
        if not include_inactive:
            query = query.where(Plan.is_active == True)
        
        result = await db.execute(query.order_by(Plan.base_price))
        return result.scalars().all()
    
    async def get_billing_analytics(self, tenant_id: UUID) -> BillingAnalytics:
        """Get billing analytics for tenant"""
        db = await self._get_db()
        
        # Get current subscription
        subscription = await self.get_subscription(tenant_id)
        if not subscription:
            return BillingAnalytics(
                tenant_id=tenant_id,
                monthly_recurring_revenue=Decimal('0'),
                annual_recurring_revenue=Decimal('0'),
                usage_metrics={},
                usage_trends={},
                payment_health_score=1.0,
                projected_monthly_cost=Decimal('0')
            )
        
        # Calculate MRR/ARR
        plan = await self.get_plan(subscription.plan_id)
        mrr = plan.base_price if plan else Decimal('0')
        arr = mrr * 12
        
        # Get usage metrics for current period
        usage_result = await db.execute(
            select(
                UsageRecord.metric_type,
                func.sum(UsageRecord.quantity).label("total_quantity")
            )
            .where(
                and_(
                    UsageRecord.tenant_id == tenant_id,
                    UsageRecord.billing_period_start == subscription.current_period_start
                )
            )
            .group_by(UsageRecord.metric_type)
        )
        
        usage_metrics = {row.metric_type: row.total_quantity for row in usage_result}
        
        # Calculate projected monthly cost
        projected_cost = mrr
        if plan and plan.usage_prices:
            for metric_type, usage in usage_metrics.items():
                if metric_type in plan.usage_prices:
                    included = plan.included_usage.get(metric_type, 0)
                    overage = max(0, usage - included)
                    projected_cost += overage * plan.usage_prices[metric_type]
        
        return BillingAnalytics(
            tenant_id=tenant_id,
            monthly_recurring_revenue=mrr,
            annual_recurring_revenue=arr,
            usage_metrics=usage_metrics,
            usage_trends={},  # Would implement trend analysis
            payment_health_score=1.0,  # Would calculate based on payment history
            projected_monthly_cost=projected_cost
        )
    
    async def process_webhook(self, event_data: Dict) -> bool:
        """Process Stripe webhook event"""
        try:
            event_type = event_data.get("type")
            data_object = event_data.get("data", {}).get("object", {})
            
            # Create billing event record
            event_record = BillingEvent(
                tenant_id=UUID("00000000-0000-0000-0000-000000000000"),  # Will be updated
                event_type=event_type,
                event_data=event_data,
                source="stripe",
                source_id=event_data.get("id")
            )
            
            # Process different event types
            if event_type == "customer.subscription.updated":
                await self._handle_subscription_updated(data_object)
            elif event_type == "customer.subscription.deleted":
                await self._handle_subscription_cancelled(data_object)
            elif event_type == "invoice.payment_succeeded":
                await self._handle_payment_succeeded(data_object)
            elif event_type == "invoice.payment_failed":
                await self._handle_payment_failed(data_object)
            else:
                logger.info(f"Unhandled webhook event type: {event_type}")
            
            # Mark event as processed
            event_record.processed = True
            event_record.processed_at = datetime.utcnow()
            
            db = await self._get_db()
            db.add(event_record)
            await db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to process webhook: {e}")
            return False
    
    async def _handle_subscription_updated(self, subscription_data: Dict):
        """Handle subscription updated webhook"""
        stripe_subscription_id = subscription_data.get("id")
        status = subscription_data.get("status")
        
        db = await self._get_db()
        
        # Find local subscription
        result = await db.execute(
            select(Subscription).where(
                Subscription.stripe_subscription_id == stripe_subscription_id
            )
        )
        subscription = result.scalar_one_or_none()
        
        if subscription:
            subscription.status = SubscriptionStatus(status)
            subscription.updated_at = datetime.utcnow()
            
            await db.commit()
            
            # Update tenant status
            await self._update_tenant_subscription_status(
                subscription.tenant_id, 
                subscription.status
            )
            
            logger.info(f"Updated subscription {subscription.id} status to {status}")
    
    async def _handle_subscription_cancelled(self, subscription_data: Dict):
        """Handle subscription cancelled webhook"""
        stripe_subscription_id = subscription_data.get("id")
        
        db = await self._get_db()
        
        result = await db.execute(
            select(Subscription).where(
                Subscription.stripe_subscription_id == stripe_subscription_id
            )
        )
        subscription = result.scalar_one_or_none()
        
        if subscription:
            subscription.status = SubscriptionStatus.CANCELLED
            subscription.cancelled_at = datetime.utcnow()
            subscription.updated_at = datetime.utcnow()
            
            await db.commit()
            
            # Update tenant status
            await self._update_tenant_subscription_status(
                subscription.tenant_id, 
                SubscriptionStatus.CANCELLED
            )
            
            logger.info(f"Cancelled subscription {subscription.id}")
    
    async def _handle_payment_succeeded(self, invoice_data: Dict):
        """Handle successful payment webhook"""
        # Implementation for payment success handling
        logger.info(f"Payment succeeded for invoice {invoice_data.get('id')}")
    
    async def _handle_payment_failed(self, invoice_data: Dict):
        """Handle failed payment webhook"""
        # Implementation for payment failure handling
        logger.info(f"Payment failed for invoice {invoice_data.get('id')}")
    
    async def _update_tenant_subscription_status(
        self, 
        tenant_id: UUID, 
        subscription_status: SubscriptionStatus
    ):
        """Update tenant status based on subscription status"""
        db = await self._get_db()
        
        # Map subscription status to tenant status
        tenant_status_mapping = {
            SubscriptionStatus.TRIALING: TenantStatus.TRIAL,
            SubscriptionStatus.ACTIVE: TenantStatus.ACTIVE,
            SubscriptionStatus.PAST_DUE: TenantStatus.SUSPENDED,
            SubscriptionStatus.CANCELLED: TenantStatus.CANCELLED,
            SubscriptionStatus.UNPAID: TenantStatus.SUSPENDED
        }
        
        new_tenant_status = tenant_status_mapping.get(subscription_status)
        if new_tenant_status:
            await db.execute(
                update(Tenant)
                .where(Tenant.id == tenant_id)
                .values(
                    status=new_tenant_status,
                    updated_at=datetime.utcnow()
                )
            )
            await db.commit()
            
            logger.info(f"Updated tenant {tenant_id} status to {new_tenant_status}")


# Singleton service instance
billing_service = BillingService()