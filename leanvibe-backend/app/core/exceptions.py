"""
Custom exceptions for LeanVibe Enterprise SaaS Platform
Provides tenant-specific and enterprise-grade error handling
"""

from typing import Optional, Dict, Any


class LeanVibeException(Exception):
    """Base exception for all LeanVibe errors"""
    
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)


# Tenant-related exceptions
class TenantException(LeanVibeException):
    """Base exception for tenant-related errors"""
    pass


class TenantNotFoundError(TenantException):
    """Raised when a tenant cannot be found"""
    
    def __init__(self, message: str, tenant_id: str = None):
        super().__init__(message, "tenant_not_found", {"tenant_id": tenant_id})
        self.tenant_id = tenant_id


class TenantSuspendedError(TenantException):
    """Raised when attempting to access suspended tenant"""
    
    def __init__(self, message: str, tenant_id: str = None, suspension_reason: str = None):
        details = {"tenant_id": tenant_id}
        if suspension_reason:
            details["suspension_reason"] = suspension_reason
        
        super().__init__(message, "tenant_suspended", details)
        self.tenant_id = tenant_id
        self.suspension_reason = suspension_reason


class TenantQuotaExceededError(TenantException):
    """Raised when tenant exceeds resource quotas"""
    
    def __init__(
        self, 
        message: str, 
        quota_type: str = None, 
        current_usage: int = None,
        quota_limit: int = None,
        tenant_id: str = None
    ):
        details = {
            "quota_type": quota_type,
            "current_usage": current_usage,
            "quota_limit": quota_limit,
            "tenant_id": tenant_id
        }
        
        super().__init__(message, "quota_exceeded", details)
        self.quota_type = quota_type
        self.current_usage = current_usage
        self.quota_limit = quota_limit
        self.tenant_id = tenant_id


class InvalidTenantError(TenantException):
    """Raised when tenant data is invalid"""
    
    def __init__(self, message: str, validation_errors: Dict[str, str] = None):
        super().__init__(message, "invalid_tenant", {"validation_errors": validation_errors})
        self.validation_errors = validation_errors or {}


class TenantAccessDeniedError(TenantException):
    """Raised when access to tenant resources is denied"""
    
    def __init__(self, message: str, tenant_id: str = None, user_id: str = None):
        super().__init__(
            message, 
            "tenant_access_denied", 
            {"tenant_id": tenant_id, "user_id": user_id}
        )
        self.tenant_id = tenant_id
        self.user_id = user_id


# Authentication and Authorization exceptions
class AuthException(LeanVibeException):
    """Base exception for authentication/authorization errors"""
    pass


class InvalidCredentialsError(AuthException):
    """Raised when credentials are invalid"""
    
    def __init__(self, message: str = "Invalid credentials"):
        super().__init__(message, "invalid_credentials")


class TokenExpiredError(AuthException):
    """Raised when authentication token has expired"""
    
    def __init__(self, message: str = "Authentication token has expired"):
        super().__init__(message, "token_expired")


class InsufficientPermissionsError(AuthException):
    """Raised when user lacks required permissions"""
    
    def __init__(self, message: str, required_permission: str = None, user_id: str = None):
        details = {"required_permission": required_permission, "user_id": user_id}
        super().__init__(message, "insufficient_permissions", details)
        self.required_permission = required_permission
        self.user_id = user_id


class SSOConfigurationError(AuthException):
    """Raised when SSO configuration is invalid"""
    
    def __init__(self, message: str, provider: str = None):
        super().__init__(message, "sso_configuration_error", {"provider": provider})
        self.provider = provider


# Billing and Subscription exceptions
class BillingException(LeanVibeException):
    """Base exception for billing-related errors"""
    pass


class PaymentRequiredError(BillingException):
    """Raised when payment is required to continue"""
    
    def __init__(self, message: str, amount: float = None, currency: str = "USD"):
        super().__init__(
            message, 
            "payment_required", 
            {"amount": amount, "currency": currency}
        )
        self.amount = amount
        self.currency = currency


class SubscriptionExpiredError(BillingException):
    """Raised when subscription has expired"""
    
    def __init__(self, message: str, expired_at: str = None, tenant_id: str = None):
        super().__init__(
            message,
            "subscription_expired",
            {"expired_at": expired_at, "tenant_id": tenant_id}
        )
        self.expired_at = expired_at
        self.tenant_id = tenant_id


class PaymentFailedError(BillingException):
    """Raised when payment processing fails"""
    
    def __init__(self, message: str, payment_id: str = None, error_code: str = None):
        super().__init__(
            message,
            "payment_failed",
            {"payment_id": payment_id, "payment_error_code": error_code}
        )
        self.payment_id = payment_id
        self.payment_error_code = error_code


# Resource and API exceptions
class ResourceException(LeanVibeException):
    """Base exception for resource-related errors"""
    pass


class ResourceNotFoundError(ResourceException):
    """Raised when a resource cannot be found"""
    
    def __init__(self, message: str, resource_type: str = None, resource_id: str = None):
        super().__init__(
            message,
            "resource_not_found",
            {"resource_type": resource_type, "resource_id": resource_id}
        )
        self.resource_type = resource_type
        self.resource_id = resource_id


class ResourceConflictError(ResourceException):
    """Raised when resource conflicts with existing data"""
    
    def __init__(self, message: str, conflict_field: str = None, conflict_value: str = None):
        super().__init__(
            message,
            "resource_conflict",
            {"conflict_field": conflict_field, "conflict_value": conflict_value}
        )
        self.conflict_field = conflict_field
        self.conflict_value = conflict_value


class RateLimitExceededError(ResourceException):
    """Raised when API rate limit is exceeded"""
    
    def __init__(
        self, 
        message: str, 
        retry_after: int = None,
        rate_limit: int = None,
        window_seconds: int = None
    ):
        details = {
            "retry_after": retry_after,
            "rate_limit": rate_limit,
            "window_seconds": window_seconds
        }
        super().__init__(message, "rate_limit_exceeded", details)
        self.retry_after = retry_after
        self.rate_limit = rate_limit
        self.window_seconds = window_seconds


# External service exceptions
class ExternalServiceException(LeanVibeException):
    """Base exception for external service errors"""
    pass


class AIServiceError(ExternalServiceException):
    """Raised when AI service encounters an error"""
    
    def __init__(self, message: str, model_name: str = None, error_type: str = None):
        super().__init__(
            message,
            "ai_service_error", 
            {"model_name": model_name, "error_type": error_type}
        )
        self.model_name = model_name
        self.error_type = error_type


class DatabaseConnectionError(ExternalServiceException):
    """Raised when database connection fails"""
    
    def __init__(self, message: str, database_name: str = None):
        super().__init__(
            message,
            "database_connection_error",
            {"database_name": database_name}
        )
        self.database_name = database_name


class CacheServiceError(ExternalServiceException):
    """Raised when cache service encounters an error"""
    
    def __init__(self, message: str, cache_type: str = None):
        super().__init__(
            message,
            "cache_service_error",
            {"cache_type": cache_type}
        )
        self.cache_type = cache_type


# Configuration and validation exceptions
class ConfigurationException(LeanVibeException):
    """Base exception for configuration errors"""
    pass


class InvalidConfigurationError(ConfigurationException):
    """Raised when configuration is invalid"""
    
    def __init__(self, message: str, config_key: str = None, config_value: str = None):
        super().__init__(
            message,
            "invalid_configuration",
            {"config_key": config_key, "config_value": config_value}
        )
        self.config_key = config_key
        self.config_value = config_value


class ValidationException(LeanVibeException):
    """Base exception for validation errors"""
    pass


class SchemaValidationError(ValidationException):
    """Raised when data doesn't match expected schema"""
    
    def __init__(self, message: str, schema_name: str = None, validation_errors: list = None):
        super().__init__(
            message,
            "schema_validation_error",
            {"schema_name": schema_name, "validation_errors": validation_errors}
        )
        self.schema_name = schema_name
        self.validation_errors = validation_errors or []


# Webhook and integration exceptions
class WebhookException(LeanVibeException):
    """Base exception for webhook-related errors"""
    pass


class WebhookDeliveryError(WebhookException):
    """Raised when webhook delivery fails"""
    
    def __init__(
        self, 
        message: str, 
        webhook_url: str = None,
        status_code: int = None,
        response_body: str = None
    ):
        details = {
            "webhook_url": webhook_url,
            "status_code": status_code,
            "response_body": response_body
        }
        super().__init__(message, "webhook_delivery_error", details)
        self.webhook_url = webhook_url
        self.status_code = status_code
        self.response_body = response_body


class IntegrationException(LeanVibeException):
    """Base exception for third-party integration errors"""
    pass


class ThirdPartyServiceError(IntegrationException):
    """Raised when third-party service encounters an error"""
    
    def __init__(
        self, 
        message: str, 
        service_name: str = None,
        service_error_code: str = None,
        service_error_message: str = None
    ):
        details = {
            "service_name": service_name,
            "service_error_code": service_error_code,
            "service_error_message": service_error_message
        }
        super().__init__(message, "third_party_service_error", details)
        self.service_name = service_name
        self.service_error_code = service_error_code
        self.service_error_message = service_error_message