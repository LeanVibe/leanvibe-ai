"""
Enterprise billing and subscription models for LeanVibe SaaS Platform
Supports Stripe integration, usage-based billing, and enterprise invoicing
"""

from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict


class BillingStatus(str, Enum):
    """Billing account status"""
    ACTIVE = "active"
    PAST_DUE = "past_due" 
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"
    TRIAL = "trial"


class SubscriptionStatus(str, Enum):
    """Subscription status matching Stripe statuses"""
    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELLED = "cancelled"
    UNPAID = "unpaid"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"


class PaymentStatus(str, Enum):
    """Payment status"""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class InvoiceStatus(str, Enum):
    """Invoice status"""
    DRAFT = "draft"
    OPEN = "open"
    PAID = "paid"
    VOID = "void"
    UNCOLLECTIBLE = "uncollectible"


class PaymentMethod(str, Enum):
    """Payment method types"""
    CARD = "card"
    BANK_ACCOUNT = "bank_account"
    PAYPAL = "paypal"
    WIRE_TRANSFER = "wire_transfer"


class BillingInterval(str, Enum):
    """Billing intervals"""
    MONTHLY = "monthly"
    YEARLY = "yearly"
    QUARTERLY = "quarterly"


class UsageMetricType(str, Enum):
    """Usage metric types for metered billing"""
    API_CALLS = "api_calls"
    STORAGE_GB = "storage_gb"
    AI_REQUESTS = "ai_requests"
    ACTIVE_USERS = "active_users"
    PROJECTS = "projects"
    CONCURRENT_SESSIONS = "concurrent_sessions"


class TaxType(str, Enum):
    """Tax types for compliance"""
    VAT = "vat"        # European VAT
    GST = "gst"        # Goods and Services Tax
    SALES_TAX = "sales_tax"  # US Sales Tax
    NONE = "none"


class Plan(BaseModel):
    """Subscription plan definition"""
    id: UUID = Field(default_factory=uuid4, description="Plan unique identifier")
    name: str = Field(description="Plan display name")
    slug: str = Field(description="URL-safe plan identifier")
    
    # Pricing
    base_price: Decimal = Field(description="Base monthly price in cents")
    currency: str = Field(default="USD", description="Currency code")
    billing_interval: BillingInterval = Field(description="Billing frequency")
    
    # Features and limits
    features: Dict[str, Any] = Field(default_factory=dict, description="Included features")
    limits: Dict[str, int] = Field(default_factory=dict, description="Usage limits")
    
    # Trial settings
    trial_period_days: int = Field(default=14, description="Trial period in days")
    
    # Metered usage pricing
    usage_prices: Dict[str, Decimal] = Field(default_factory=dict, description="Per-unit pricing for metered usage")
    included_usage: Dict[str, int] = Field(default_factory=dict, description="Included usage quotas")
    
    # Plan metadata
    description: Optional[str] = Field(default=None, description="Plan description")
    is_active: bool = Field(default=True, description="Plan availability")
    is_enterprise: bool = Field(default=False, description="Enterprise plan flag")
    
    # Stripe integration
    stripe_price_id: Optional[str] = Field(default=None, description="Stripe price ID")
    stripe_product_id: Optional[str] = Field(default=None, description="Stripe product ID")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(extra="ignore")


class BillingAccount(BaseModel):
    """Billing account associated with tenant"""
    id: UUID = Field(default_factory=uuid4, description="Billing account identifier")
    tenant_id: UUID = Field(description="Associated tenant")
    
    # Account details
    company_name: str = Field(description="Company name for billing")
    billing_email: str = Field(description="Billing contact email")
    
    # Address information
    billing_address: Dict[str, str] = Field(description="Billing address")
    tax_id: Optional[str] = Field(default=None, description="Tax identification number")
    tax_type: TaxType = Field(default=TaxType.NONE, description="Tax type")
    
    # Account status
    status: BillingStatus = Field(default=BillingStatus.TRIAL, description="Billing status")
    
    # Payment methods
    default_payment_method_id: Optional[str] = Field(default=None, description="Default payment method")
    
    # Stripe integration
    stripe_customer_id: Optional[str] = Field(default=None, description="Stripe customer ID")
    
    # Balance and credits
    account_balance: Decimal = Field(default=Decimal('0'), description="Account balance in cents")
    available_credits: Decimal = Field(default=Decimal('0'), description="Available credits in cents")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(extra="ignore")


class Subscription(BaseModel):
    """Subscription to a plan"""
    id: UUID = Field(default_factory=uuid4, description="Subscription identifier")
    tenant_id: UUID = Field(description="Associated tenant")
    billing_account_id: UUID = Field(description="Associated billing account")
    plan_id: UUID = Field(description="Subscribed plan")
    
    # Subscription details
    status: SubscriptionStatus = Field(description="Subscription status")
    
    # Pricing override (for custom pricing)
    custom_price: Optional[Decimal] = Field(default=None, description="Custom price override")
    discount_percentage: Decimal = Field(default=Decimal('0'), description="Discount percentage")
    
    # Subscription period
    current_period_start: datetime = Field(description="Current billing period start")
    current_period_end: datetime = Field(description="Current billing period end")
    
    # Trial information
    trial_start: Optional[datetime] = Field(default=None, description="Trial start date")
    trial_end: Optional[datetime] = Field(default=None, description="Trial end date")
    
    # Cancellation
    cancelled_at: Optional[datetime] = Field(default=None, description="Cancellation timestamp")
    cancel_at_period_end: bool = Field(default=False, description="Cancel at period end flag")
    
    # Stripe integration
    stripe_subscription_id: Optional[str] = Field(default=None, description="Stripe subscription ID")
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(extra="ignore")


class UsageRecord(BaseModel):
    """Usage record for metered billing"""
    id: UUID = Field(default_factory=uuid4, description="Usage record identifier")
    tenant_id: UUID = Field(description="Associated tenant")
    subscription_id: UUID = Field(description="Associated subscription")
    
    # Usage details
    metric_type: UsageMetricType = Field(description="Type of usage metric")
    quantity: int = Field(description="Usage quantity")
    unit_price: Optional[Decimal] = Field(default=None, description="Price per unit")
    
    # Time period
    usage_date: datetime = Field(description="Date of usage")
    billing_period_start: datetime = Field(description="Billing period start")
    billing_period_end: datetime = Field(description="Billing period end")
    
    # Aggregation metadata
    aggregation_key: Optional[str] = Field(default=None, description="Aggregation grouping key")
    
    # Stripe integration
    stripe_usage_record_id: Optional[str] = Field(default=None, description="Stripe usage record ID")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(extra="ignore")


class Invoice(BaseModel):
    """Invoice for billing"""
    id: UUID = Field(default_factory=uuid4, description="Invoice identifier")
    tenant_id: UUID = Field(description="Associated tenant")
    billing_account_id: UUID = Field(description="Associated billing account")
    subscription_id: Optional[UUID] = Field(default=None, description="Associated subscription")
    
    # Invoice details
    invoice_number: str = Field(description="Human-readable invoice number")
    status: InvoiceStatus = Field(description="Invoice status")
    
    # Amounts (in cents)
    subtotal: Decimal = Field(description="Subtotal before tax")
    tax_amount: Decimal = Field(default=Decimal('0'), description="Tax amount")
    discount_amount: Decimal = Field(default=Decimal('0'), description="Total discount amount")
    total: Decimal = Field(description="Total amount")
    amount_paid: Decimal = Field(default=Decimal('0'), description="Amount paid")
    amount_due: Decimal = Field(description="Amount due")
    
    # Currency
    currency: str = Field(default="USD", description="Invoice currency")
    
    # Dates
    issue_date: datetime = Field(description="Invoice issue date")
    due_date: datetime = Field(description="Payment due date")
    period_start: datetime = Field(description="Billing period start")
    period_end: datetime = Field(description="Billing period end")
    
    # Payment
    paid_at: Optional[datetime] = Field(default=None, description="Payment timestamp")
    
    # Line items
    line_items: List[Dict[str, Any]] = Field(default_factory=list, description="Invoice line items")
    
    # Stripe integration
    stripe_invoice_id: Optional[str] = Field(default=None, description="Stripe invoice ID")
    
    # File attachments
    pdf_url: Optional[str] = Field(default=None, description="PDF download URL")
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(extra="ignore")


class Payment(BaseModel):
    """Payment record"""
    id: UUID = Field(default_factory=uuid4, description="Payment identifier")
    tenant_id: UUID = Field(description="Associated tenant")
    billing_account_id: UUID = Field(description="Associated billing account")
    invoice_id: Optional[UUID] = Field(default=None, description="Associated invoice")
    
    # Payment details
    amount: Decimal = Field(description="Payment amount in cents")
    currency: str = Field(default="USD", description="Payment currency")
    status: PaymentStatus = Field(description="Payment status")
    payment_method: PaymentMethod = Field(description="Payment method used")
    
    # Payment method details
    payment_method_details: Dict[str, Any] = Field(default_factory=dict, description="Payment method details")
    
    # Stripe integration
    stripe_payment_intent_id: Optional[str] = Field(default=None, description="Stripe PaymentIntent ID")
    stripe_charge_id: Optional[str] = Field(default=None, description="Stripe Charge ID")
    
    # Processing details
    processed_at: Optional[datetime] = Field(default=None, description="Processing timestamp")
    failure_reason: Optional[str] = Field(default=None, description="Failure reason if failed")
    
    # Refund information
    refunded_amount: Decimal = Field(default=Decimal('0'), description="Refunded amount")
    refund_reason: Optional[str] = Field(default=None, description="Refund reason")
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(extra="ignore")


class BillingEvent(BaseModel):
    """Billing event for audit and webhook processing"""
    id: UUID = Field(default_factory=uuid4, description="Event identifier")
    tenant_id: UUID = Field(description="Associated tenant")
    
    # Event details
    event_type: str = Field(description="Type of billing event")
    event_data: Dict[str, Any] = Field(description="Event payload")
    
    # Source information
    source: str = Field(description="Event source (stripe, internal, etc.)")
    source_id: Optional[str] = Field(default=None, description="Source event ID")
    
    # Processing status
    processed: bool = Field(default=False, description="Processing status")
    processed_at: Optional[datetime] = Field(default=None, description="Processing timestamp")
    processing_error: Optional[str] = Field(default=None, description="Processing error message")
    
    # Retry information
    retry_count: int = Field(default=0, description="Retry attempts")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(extra="ignore")


# Request/Response models
class CreateSubscriptionRequest(BaseModel):
    """Request to create a new subscription"""
    tenant_id: UUID = Field(description="Target tenant")
    plan_id: UUID = Field(description="Selected plan")
    payment_method_id: Optional[str] = Field(default=None, description="Payment method for subscription")
    trial_period_days: Optional[int] = Field(default=None, description="Custom trial period")
    coupon_code: Optional[str] = Field(default=None, description="Coupon code for discount")
    
    model_config = ConfigDict(extra="ignore")


class UpdateSubscriptionRequest(BaseModel):
    """Request to update subscription"""
    plan_id: Optional[UUID] = Field(default=None, description="New plan ID")
    cancel_at_period_end: Optional[bool] = Field(default=None, description="Cancel at period end")
    
    model_config = ConfigDict(extra="ignore")


class CreatePaymentMethodRequest(BaseModel):
    """Request to create payment method"""
    type: PaymentMethod = Field(description="Payment method type")
    card_token: Optional[str] = Field(default=None, description="Card token from Stripe")
    bank_account_token: Optional[str] = Field(default=None, description="Bank account token")
    
    model_config = ConfigDict(extra="ignore")


class BillingAnalytics(BaseModel):
    """Billing analytics and metrics"""
    tenant_id: UUID = Field(description="Associated tenant")
    
    # Revenue metrics
    monthly_recurring_revenue: Decimal = Field(description="MRR in cents")
    annual_recurring_revenue: Decimal = Field(description="ARR in cents")
    
    # Usage metrics
    usage_metrics: Dict[str, int] = Field(description="Current usage by metric type")
    usage_trends: Dict[str, List[int]] = Field(description="Usage trends over time")
    
    # Billing health
    overdue_amount: Decimal = Field(default=Decimal('0'), description="Overdue amount")
    next_invoice_amount: Decimal = Field(default=Decimal('0'), description="Next invoice amount")
    payment_health_score: float = Field(description="Payment health score (0-1)")
    
    # Forecasting
    projected_monthly_cost: Decimal = Field(description="Projected monthly cost based on usage")
    
    calculated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(extra="ignore")


# Default plan configurations
DEFAULT_PLANS = {
    "developer": Plan(
        name="Developer",
        slug="developer",
        base_price=Decimal('5000'),  # $50.00
        billing_interval=BillingInterval.MONTHLY,
        features={
            "max_users": 1,
            "max_projects": 5,
            "ai_requests_per_day": 100,
            "storage_gb": 1,
            "email_support": True,
            "api_access": True
        },
        limits={
            "api_calls_per_month": 10000,
            "storage_gb": 1,
            "concurrent_sessions": 2
        },
        usage_prices={
            "additional_api_calls": Decimal('1'),  # $0.01 per call over limit
            "additional_storage_gb": Decimal('500'),  # $5.00 per GB over limit
        },
        trial_period_days=14
    ),
    
    "team": Plan(
        name="Team",
        slug="team",
        base_price=Decimal('20000'),  # $200.00
        billing_interval=BillingInterval.MONTHLY,
        features={
            "max_users": 10,
            "max_projects": 50,
            "ai_requests_per_day": 1000,
            "storage_gb": 10,
            "email_support": True,
            "chat_support": True,
            "api_access": True,
            "sso_support": True
        },
        limits={
            "api_calls_per_month": 100000,
            "storage_gb": 10,
            "concurrent_sessions": 10
        },
        usage_prices={
            "additional_api_calls": Decimal('1'),  # $0.01 per call over limit
            "additional_storage_gb": Decimal('400'),  # $4.00 per GB over limit
        },
        trial_period_days=14
    ),
    
    "enterprise": Plan(
        name="Enterprise",
        slug="enterprise",
        base_price=Decimal('80000'),  # $800.00
        billing_interval=BillingInterval.MONTHLY,
        is_enterprise=True,
        features={
            "max_users": 999999,  # Unlimited
            "max_projects": 999999,  # Unlimited
            "ai_requests_per_day": 10000,
            "storage_gb": 1000,  # 1TB
            "email_support": True,
            "chat_support": True,
            "phone_support": True,
            "api_access": True,
            "sso_support": True,
            "saml_support": True,
            "custom_integrations": True,
            "dedicated_support": True,
            "sla_guarantee": True
        },
        limits={
            "api_calls_per_month": 999999999,  # Unlimited
            "storage_gb": 1000,
            "concurrent_sessions": 100
        },
        usage_prices={
            "additional_storage_gb": Decimal('300'),  # $3.00 per GB over 1TB
        },
        trial_period_days=30
    )
}