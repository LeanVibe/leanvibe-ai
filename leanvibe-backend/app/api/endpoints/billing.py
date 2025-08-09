"""
Billing API endpoints for LeanVibe Enterprise SaaS Platform
Provides subscription management, payment processing, and usage tracking
"""

import logging
from typing import Dict, List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ...models.billing_models import (
    Plan, BillingAccount, Subscription, UsageRecord, BillingAnalytics,
    CreateSubscriptionRequest, UpdateSubscriptionRequest, CreatePaymentMethodRequest,
    UsageMetricType, DEFAULT_PLANS
)
from ...services.billing_service import billing_service, StripeIntegration
from ...services.auth_service import auth_service
from ...middleware.tenant_middleware import get_current_tenant, require_tenant
from ...core.exceptions import (
    ResourceNotFoundError, PaymentRequiredError, PaymentFailedError,
    SubscriptionExpiredError
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/billing", tags=["billing"])
security = HTTPBearer(auto_error=False)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    payload = await auth_service.verify_token(credentials.credentials)
    return payload


@router.get("/plans", response_model=List[Plan])
async def list_plans(include_inactive: bool = False) -> List[Plan]:
    """
    List available subscription plans
    
    Returns all available plans with pricing and features.
    """
    try:
        plans = await billing_service.list_plans(include_inactive=include_inactive)
        
        # If no plans in database, return default plans
        if not plans:
            return list(DEFAULT_PLANS.values())
        
        return plans
        
    except Exception as e:
        logger.error(f"Failed to list plans: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve plans"
        )


@router.get("/plans/{plan_id}", response_model=Plan)
async def get_plan(plan_id: UUID) -> Plan:
    """
    Get specific plan details
    
    Returns detailed information about a specific plan.
    """
    try:
        plan = await billing_service.get_plan(plan_id)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan not found"
            )
        
        return plan
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get plan {plan_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve plan"
        )


@router.post("/account", response_model=BillingAccount)
async def create_billing_account(
    account_data: Dict,
    tenant=Depends(require_tenant),
    current_user=Depends(get_current_user)
) -> BillingAccount:
    """
    Create billing account for tenant
    
    Sets up billing and payment infrastructure for the tenant.
    """
    try:
        # Validate required fields
        required_fields = ["company_name", "billing_email"]
        for field in required_fields:
            if field not in account_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        billing_account = await billing_service.create_billing_account(
            tenant.id, account_data
        )
        
        logger.info(f"Created billing account for tenant {tenant.id}")
        return billing_account
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create billing account: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create billing account"
        )


@router.get("/account", response_model=BillingAccount)
async def get_billing_account(
    tenant=Depends(require_tenant),
    current_user=Depends(get_current_user)
) -> BillingAccount:
    """
    Get billing account for tenant
    
    Returns current billing account information.
    """
    try:
        billing_account = await billing_service.get_billing_account(tenant.id)
        if not billing_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Billing account not found"
            )
        
        return billing_account
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get billing account: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve billing account"
        )


@router.post("/subscription", response_model=Subscription)
async def create_subscription(
    request: CreateSubscriptionRequest,
    tenant=Depends(require_tenant),
    current_user=Depends(get_current_user)
) -> Subscription:
    """
    Create new subscription
    
    Subscribes tenant to a plan with optional trial period.
    """
    try:
        # Validate tenant matches request
        if request.tenant_id != tenant.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot create subscription for different tenant"
            )
        
        # Check if billing account exists
        billing_account = await billing_service.get_billing_account(tenant.id)
        if not billing_account:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Billing account required before creating subscription"
            )
        
        subscription = await billing_service.create_subscription(tenant.id, request)
        
        logger.info(f"Created subscription {subscription.id} for tenant {tenant.id}")
        return subscription
        
    except HTTPException:
        raise
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create subscription"
        )


@router.get("/subscription", response_model=Subscription)
async def get_subscription(
    tenant=Depends(require_tenant),
    current_user=Depends(get_current_user)
) -> Subscription:
    """
    Get current subscription
    
    Returns active subscription for the tenant.
    """
    try:
        subscription = await billing_service.get_subscription(tenant.id)
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active subscription found"
            )
        
        return subscription
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve subscription"
        )


@router.patch("/subscription", response_model=Subscription)
async def update_subscription(
    request: UpdateSubscriptionRequest,
    tenant=Depends(require_tenant),
    current_user=Depends(get_current_user)
) -> Subscription:
    """
    Update existing subscription
    
    Modify plan, billing settings, or cancellation status.
    """
    try:
        subscription = await billing_service.update_subscription(tenant.id, request)
        
        logger.info(f"Updated subscription {subscription.id}")
        return subscription
        
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to update subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update subscription"
        )


@router.delete("/subscription")
async def cancel_subscription(
    immediately: bool = False,
    tenant=Depends(require_tenant),
    current_user=Depends(get_current_user)
) -> JSONResponse:
    """
    Cancel subscription
    
    Cancel subscription immediately or at period end.
    """
    try:
        subscription = await billing_service.cancel_subscription(
            tenant.id, 
            immediately=immediately
        )
        
        message = "Subscription cancelled immediately" if immediately else "Subscription will cancel at period end"
        
        logger.info(f"Cancelled subscription {subscription.id}")
        return JSONResponse(
            {
                "message": message,
                "subscription_id": str(subscription.id),
                "cancelled_at": subscription.cancelled_at.isoformat() if subscription.cancelled_at else None
            },
            status_code=200
        )
        
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to cancel subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel subscription"
        )


@router.post("/usage", response_model=UsageRecord)
async def record_usage(
    metric_type: UsageMetricType,
    quantity: int,
    tenant=Depends(require_tenant),
    current_user=Depends(get_current_user)
) -> UsageRecord:
    """
    Record usage for metered billing
    
    Track usage metrics for billing calculation.
    """
    try:
        if quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quantity must be positive"
            )
        
        usage_record = await billing_service.record_usage(
            tenant.id, metric_type, quantity
        )
        
        logger.info(f"Recorded usage: {metric_type}={quantity} for tenant {tenant.id}")
        return usage_record
        
    except HTTPException:
        raise
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to record usage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record usage"
        )


@router.get("/usage")
async def get_usage(
    tenant=Depends(require_tenant),
    current_user=Depends(get_current_user)
) -> Dict:
    """
    Get usage summary for current billing period
    
    Returns usage metrics and billing information.
    """
    try:
        # Get current subscription
        subscription = await billing_service.get_subscription(tenant.id)
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active subscription found"
            )
        
        # Get billing analytics
        analytics = await billing_service.get_billing_analytics(tenant.id)
        
        return {
            "subscription_id": str(subscription.id),
            "billing_period": {
                "start": subscription.current_period_start.isoformat(),
                "end": subscription.current_period_end.isoformat()
            },
            "usage_metrics": analytics.usage_metrics,
            "projected_cost": float(analytics.projected_monthly_cost) / 100,  # Convert cents to dollars
            "currency": "USD"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get usage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve usage"
        )


@router.get("/analytics", response_model=BillingAnalytics)
async def get_billing_analytics(
    tenant=Depends(require_tenant),
    current_user=Depends(get_current_user)
) -> BillingAnalytics:
    """
    Get billing analytics and metrics
    
    Returns comprehensive billing and usage analytics.
    """
    try:
        analytics = await billing_service.get_billing_analytics(tenant.id)
        return analytics
        
    except Exception as e:
        logger.error(f"Failed to get billing analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve billing analytics"
        )


@router.post("/payment-methods", response_model=Dict)
async def create_payment_method(
    request: CreatePaymentMethodRequest,
    tenant=Depends(require_tenant),
    current_user=Depends(get_current_user)
) -> Dict:
    """
    Create payment method
    
    Add new payment method for subscription billing.
    """
    try:
        # Get billing account
        billing_account = await billing_service.get_billing_account(tenant.id)
        if not billing_account:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Billing account required"
            )
        
        # Mock payment method creation
        payment_method_id = f"pm_mock_{request.type}_{tenant.slug}"
        
        return {
            "payment_method_id": payment_method_id,
            "type": request.type,
            "status": "active",
            "created_at": "2025-01-01T00:00:00Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create payment method: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create payment method"
        )


@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request) -> JSONResponse:
    """
    Handle Stripe webhook events
    
    Process subscription and payment events from Stripe.
    """
    try:
        # Get webhook payload
        payload = await request.body()
        signature = request.headers.get("stripe-signature")
        
        if not signature:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing Stripe signature"
            )
        
        # Verify webhook signature
        stripe = StripeIntegration()
        event_data = await stripe.verify_webhook(payload, signature)
        
        # Process webhook
        success = await billing_service.process_webhook(event_data)
        
        if success:
            return JSONResponse({"received": True}, status_code=200)
        else:
            return JSONResponse({"error": "Processing failed"}, status_code=500)
        
    except Exception as e:
        logger.error(f"Stripe webhook error: {e}")
        return JSONResponse({"error": "Webhook processing failed"}, status_code=500)


@router.get("/invoice/{invoice_id}")
async def get_invoice(
    invoice_id: UUID,
    tenant=Depends(require_tenant),
    current_user=Depends(get_current_user)
) -> Dict:
    """
    Get invoice details
    
    Returns invoice information and download links.
    """
    try:
        # Mock invoice data
        invoice_data = {
            "id": str(invoice_id),
            "tenant_id": str(tenant.id),
            "status": "paid",
            "total": 5000,  # $50.00
            "currency": "USD",
            "issue_date": "2025-01-01T00:00:00Z",
            "due_date": "2025-01-15T00:00:00Z",
            "paid_at": "2025-01-05T00:00:00Z",
            "pdf_url": f"/api/v1/billing/invoice/{invoice_id}/pdf"
        }
        
        return invoice_data
        
    except Exception as e:
        logger.error(f"Failed to get invoice: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve invoice"
        )


@router.get("/invoices")
async def list_invoices(
    limit: int = 10,
    offset: int = 0,
    tenant=Depends(require_tenant),
    current_user=Depends(get_current_user)
) -> Dict:
    """
    List invoices for tenant
    
    Returns paginated list of invoices.
    """
    try:
        # Mock invoice list
        invoices = [
            {
                "id": f"inv_mock_{i}",
                "status": "paid" if i % 2 == 0 else "open",
                "total": 5000 + (i * 100),
                "issue_date": f"2025-0{min(i+1, 9)}-01T00:00:00Z"
            }
            for i in range(limit)
        ]
        
        return {
            "invoices": invoices,
            "total_count": 20,  # Mock total
            "has_more": offset + limit < 20
        }
        
    except Exception as e:
        logger.error(f"Failed to list invoices: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve invoices"
        )


@router.get("/health")
async def billing_health_check() -> JSONResponse:
    """
    Billing service health check
    
    Returns service status and connectivity.
    """
    try:
        # Check database connectivity
        plans = await billing_service.list_plans(include_inactive=False)
        
        return JSONResponse({
            "status": "healthy",
            "service": "billing",
            "timestamp": "2025-01-01T00:00:00Z",
            "plans_available": len(plans) if plans else len(DEFAULT_PLANS)
        })
        
    except Exception as e:
        logger.error(f"Billing health check failed: {e}")
        return JSONResponse({
            "status": "unhealthy",
            "service": "billing", 
            "error": str(e)
        }, status_code=503)