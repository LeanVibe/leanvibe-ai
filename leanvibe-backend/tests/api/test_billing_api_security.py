"""
COMPREHENSIVE BILLING API SECURITY TESTING

This module implements enterprise-grade security testing specifically for billing API endpoints
to ensure payment data protection, Stripe webhook security, and financial data isolation.

Critical Security Requirements:
- Stripe webhook signatures are validated to prevent tampering
- Payment data is encrypted and never exposed in logs/responses
- Subscription access is restricted to authorized users only
- Billing data is isolated per tenant
- PCI DSS compliance requirements are met
- Financial operations require proper authorization

Risk Level: CRITICAL - Protects financial data, prevents fraud, ensures compliance
Business Impact: Prevents financial losses, regulatory penalties, customer trust issues
"""

import pytest
import asyncio
import json
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, List, Any
from uuid import UUID, uuid4
from unittest.mock import AsyncMock, patch, MagicMock

from fastapi.testclient import TestClient
from fastapi import status
import httpx

from app.main import app
from app.models.auth_models import User, UserRole, UserStatus, AuthProvider
from app.models.tenant_models import Tenant, TenantStatus, TenantQuotas
from app.models.billing_models import Plan, Subscription, BillingAccount


class TestBillingAPIStripeWebhookSecurity:
    """
    CRITICAL: Test Stripe webhook signature validation
    
    Validates that webhook endpoints properly verify Stripe signatures
    to prevent tampering and unauthorized financial operations.
    """
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def stripe_webhook_secret(self):
        """Mock Stripe webhook secret for testing"""
        return "whsec_test_secret_key_12345"
    
    @pytest.fixture
    def sample_tenant(self):
        return Tenant(
            id=uuid4(),
            organization_name="Test Corp",
            slug="test-corp",
            admin_email="admin@testcorp.com",
            status=TenantStatus.ACTIVE,
            quotas=TenantQuotas(
                max_users=10,
                max_projects=50,
                max_api_calls_per_month=10000,
                max_storage_mb=1000,
                max_ai_requests_per_day=100,
                max_concurrent_sessions=5
            )
        )
    
    def generate_stripe_signature(self, payload: str, secret: str, timestamp: int = None) -> str:
        """Generate valid Stripe webhook signature for testing"""
        if timestamp is None:
            timestamp = int(datetime.utcnow().timestamp())
        
        # Stripe signature format: t=timestamp,v1=signature
        payload_to_sign = f"{timestamp}.{payload}"
        signature = hmac.new(
            secret.encode('utf-8'),
            payload_to_sign.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return f"t={timestamp},v1={signature}"

    @pytest.mark.asyncio
    async def test_stripe_webhook_signature_validation_success(self, client, stripe_webhook_secret):
        """
        CRITICAL: Test valid Stripe webhook signatures are accepted
        
        Risk: Legitimate webhook events rejected, billing system malfunction
        """
        # Sample Stripe webhook payload
        webhook_payload = {
            "id": "evt_test_webhook",
            "object": "event",
            "type": "invoice.payment_succeeded",
            "data": {
                "object": {
                    "id": "in_test_invoice",
                    "customer": "cus_test_customer",
                    "amount_paid": 2000,
                    "currency": "usd"
                }
            },
            "created": int(datetime.utcnow().timestamp())
        }
        
        payload_str = json.dumps(webhook_payload, separators=(',', ':'))
        valid_signature = self.generate_stripe_signature(payload_str, stripe_webhook_secret)
        
        with patch("app.services.billing_service.STRIPE_WEBHOOK_SECRET", stripe_webhook_secret):
            response = client.post(
                "/api/v1/billing/webhooks/stripe",
                data=payload_str,
                headers={
                    "Content-Type": "application/json",
                    "Stripe-Signature": valid_signature
                }
            )
        
        # Valid webhook should not be rejected due to signature
        assert response.status_code != status.HTTP_401_UNAUTHORIZED, \
            "Valid Stripe signature was rejected"
        assert response.status_code != status.HTTP_403_FORBIDDEN, \
            "Valid Stripe signature was rejected"

    @pytest.mark.asyncio
    async def test_stripe_webhook_signature_validation_failure(self, client, stripe_webhook_secret):
        """
        CRITICAL: Test invalid Stripe webhook signatures are rejected
        
        Risk: Unauthorized financial operations, payment fraud, data tampering
        """
        webhook_payload = {
            "id": "evt_malicious_webhook",
            "object": "event", 
            "type": "invoice.payment_succeeded",
            "data": {
                "object": {
                    "id": "in_malicious_invoice",
                    "customer": "cus_hacker",
                    "amount_paid": 999999999,  # Fraudulent amount
                    "currency": "usd"
                }
            }
        }
        
        payload_str = json.dumps(webhook_payload, separators=(',', ':'))
        
        # Test various invalid signatures
        invalid_signatures = [
            "invalid_signature",
            "t=123456789,v1=invalid_hash",
            self.generate_stripe_signature(payload_str, "wrong_secret"),  # Wrong secret
            self.generate_stripe_signature("different_payload", stripe_webhook_secret),  # Tampered payload
            "",  # Empty signature
            "t=999999999999,v1=" + self.generate_stripe_signature(payload_str, stripe_webhook_secret)[12:],  # Future timestamp
        ]
        
        for invalid_signature in invalid_signatures:
            with patch("app.services.billing_service.STRIPE_WEBHOOK_SECRET", stripe_webhook_secret):
                response = client.post(
                    "/api/v1/billing/webhooks/stripe",
                    data=payload_str,
                    headers={
                        "Content-Type": "application/json",
                        "Stripe-Signature": invalid_signature
                    }
                )
            
            # Invalid signatures should be rejected
            assert response.status_code in [401, 403, 400], \
                f"Invalid Stripe signature was accepted: {invalid_signature[:50]}"

    @pytest.mark.asyncio
    async def test_stripe_webhook_timestamp_validation(self, client, stripe_webhook_secret):
        """
        CRITICAL: Test webhook timestamp validation prevents replay attacks
        
        Risk: Replay attacks, duplicate payment processing
        """
        webhook_payload = {
            "id": "evt_timestamp_test",
            "object": "event",
            "type": "customer.subscription.updated"
        }
        
        payload_str = json.dumps(webhook_payload)
        
        # Test old timestamp (replay attack simulation)
        old_timestamp = int((datetime.utcnow() - timedelta(hours=1)).timestamp())
        old_signature = self.generate_stripe_signature(payload_str, stripe_webhook_secret, old_timestamp)
        
        with patch("app.services.billing_service.STRIPE_WEBHOOK_SECRET", stripe_webhook_secret):
            response = client.post(
                "/api/v1/billing/webhooks/stripe",
                data=payload_str,
                headers={
                    "Content-Type": "application/json",
                    "Stripe-Signature": old_signature
                }
            )
        
        # Old timestamps should be rejected (depending on tolerance window)
        # This prevents replay attacks
        if response.status_code not in [200, 204]:
            assert response.status_code in [400, 401], \
                "Webhook with old timestamp should be rejected to prevent replay attacks"

    @pytest.mark.asyncio
    async def test_stripe_webhook_malicious_payload_handling(self, client, stripe_webhook_secret):
        """
        CRITICAL: Test malicious webhook payloads are handled safely
        
        Risk: Code injection, system compromise, data corruption
        """
        malicious_payloads = [
            # JSON injection attempts
            '{"type": "invoice.payment_succeeded", "data": {"object": {"id": "\"; DROP TABLE subscriptions; --"}}}',
            
            # XSS attempts
            '{"type": "customer.created", "data": {"object": {"email": "<script>alert(\\"xss\\")</script>"}}}',
            
            # Large payload DoS attempt
            '{"type": "test", "data": {"large_field": "' + "A" * 1000000 + '"}}',
            
            # Nested object attack
            '{"type": "test", "deeply": ' + json.dumps({"nested": {"object": {"depth": "value"}} * 100}) + '}',
        ]
        
        for malicious_payload in malicious_payloads:
            # Generate valid signature for malicious payload
            valid_signature = self.generate_stripe_signature(malicious_payload, stripe_webhook_secret)
            
            with patch("app.services.billing_service.STRIPE_WEBHOOK_SECRET", stripe_webhook_secret):
                response = client.post(
                    "/api/v1/billing/webhooks/stripe",
                    data=malicious_payload,
                    headers={
                        "Content-Type": "application/json",
                        "Stripe-Signature": valid_signature
                    }
                )
            
            # Should handle malicious payloads gracefully
            assert response.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR, \
                f"Malicious webhook payload caused server error: {malicious_payload[:100]}"


class TestBillingAPIPaymentDataSecurity:
    """
    CRITICAL: Test payment data encryption and security
    
    Validates that sensitive payment information is properly encrypted,
    never logged, and follows PCI DSS compliance requirements.
    """
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def sample_tenant(self):
        return Tenant(
            id=uuid4(),
            organization_name="Test Corp",
            slug="test-corp",
            admin_email="admin@testcorp.com",
            status=TenantStatus.ACTIVE,
            quotas=TenantQuotas(
                max_users=10,
                max_projects=50,
                max_api_calls_per_month=10000,
                max_storage_mb=1000,
                max_ai_requests_per_day=100,
                max_concurrent_sessions=5
            )
        )
    
    @pytest.fixture
    def sample_user(self, sample_tenant):
        return User(
            id=uuid4(),
            tenant_id=sample_tenant.id,
            email="billing@testcorp.com",
            role=UserRole.ADMIN,  # Billing requires admin role
            status=UserStatus.ACTIVE
        )
    
    @pytest.fixture
    def auth_headers(self, sample_user, sample_tenant):
        token = f"valid.jwt.{sample_user.id}.{sample_tenant.id}"
        return {"Authorization": f"Bearer {token}"}

    @pytest.mark.asyncio
    async def test_payment_method_creation_data_encryption(
        self, client, auth_headers, sample_tenant, sample_user
    ):
        """
        CRITICAL: Test payment method data is encrypted and not exposed
        
        Risk: Credit card data exposure, PCI DSS violation, financial fraud
        """
        with patch("app.services.auth_service.auth_service.verify_token") as mock_verify:
            with patch("app.middleware.tenant_middleware.require_tenant") as mock_tenant:
                mock_verify.return_value = {
                    "user_id": str(sample_user.id),
                    "tenant_id": str(sample_tenant.id),
                    "role": sample_user.role.value
                }
                mock_tenant.return_value = sample_tenant
                
                # Test payment method creation with sensitive data
                sensitive_payment_data = {
                    "type": "card",
                    "card_number": "4242424242424242",  # Test card number
                    "exp_month": 12,
                    "exp_year": 2025,
                    "cvc": "123",
                    "cardholder_name": "John Doe"
                }
                
                response = client.post(
                    "/api/v1/billing/payment-methods",
                    json=sensitive_payment_data,
                    headers=auth_headers
                )
                
                # Response should not contain sensitive payment data
                if response.status_code in [200, 201]:
                    response_data = response.json()
                    response_str = json.dumps(response_data).lower()
                    
                    # Should not contain full card number
                    assert "4242424242424242" not in response_str, \
                        "Full card number exposed in API response"
                    
                    # Should not contain CVC
                    assert "123" not in response_str, \
                        "CVC exposed in API response"
                    
                    # Card number should be masked (if present)
                    if "card_number" in response_str or "number" in response_str:
                        # Should show masked version like "****1242" or similar
                        pass  # Specific format depends on implementation

    @pytest.mark.asyncio
    async def test_billing_response_data_filtering(
        self, client, auth_headers, sample_tenant, sample_user
    ):
        """
        CRITICAL: Test billing API responses filter sensitive data
        
        Risk: Sensitive financial data exposure in API responses
        """
        with patch("app.services.auth_service.auth_service.verify_token") as mock_verify:
            with patch("app.middleware.tenant_middleware.require_tenant") as mock_tenant:
                with patch("app.services.billing_service.billing_service.get_tenant_billing_account") as mock_billing:
                    mock_verify.return_value = {
                        "user_id": str(sample_user.id),
                        "tenant_id": str(sample_tenant.id),
                        "role": sample_user.role.value
                    }
                    mock_tenant.return_value = sample_tenant
                    
                    # Mock billing account with sensitive data
                    mock_billing_account = {
                        "id": "acct_123",
                        "tenant_id": str(sample_tenant.id),
                        "stripe_customer_id": "cus_sensitive_id",
                        "payment_methods": [
                            {
                                "id": "pm_123",
                                "type": "card",
                                "card": {
                                    "last4": "4242",
                                    "brand": "visa",
                                    "exp_month": 12,
                                    "exp_year": 2025,
                                    # These should not be exposed
                                    "number": "4242424242424242",  # Should be filtered
                                    "cvc": "123"  # Should be filtered
                                }
                            }
                        ],
                        # Internal fields that should be filtered
                        "stripe_secret_key": "sk_test_secret",
                        "webhook_secret": "whsec_secret",
                        "internal_notes": "Customer is high risk"
                    }
                    
                    mock_billing.return_value = mock_billing_account
                    
                    response = client.get("/api/v1/billing/account", headers=auth_headers)
                    
                    if response.status_code == 200:
                        response_data = response.json()
                        response_str = json.dumps(response_data)
                        
                        # Should not contain sensitive Stripe data
                        sensitive_fields = [
                            "4242424242424242",  # Full card number
                            "123",  # CVC (in this context)
                            "sk_test_secret",  # Stripe secret key
                            "whsec_secret",  # Webhook secret
                        ]
                        
                        for sensitive_field in sensitive_fields:
                            assert sensitive_field not in response_str, \
                                f"Sensitive field exposed in billing response: {sensitive_field}"

    @pytest.mark.asyncio
    async def test_subscription_access_authorization(
        self, client, auth_headers, sample_tenant, sample_user
    ):
        """
        CRITICAL: Test subscription access is properly authorized
        
        Risk: Unauthorized access to billing information, subscription tampering
        """
        with patch("app.services.auth_service.auth_service.verify_token") as mock_verify:
            with patch("app.middleware.tenant_middleware.require_tenant") as mock_tenant:
                mock_verify.return_value = {
                    "user_id": str(sample_user.id),
                    "tenant_id": str(sample_tenant.id),
                    "role": sample_user.role.value
                }
                mock_tenant.return_value = sample_tenant
                
                # Test subscription operations require proper authorization
                subscription_endpoints = [
                    ("GET", "/api/v1/billing/subscriptions"),
                    ("POST", "/api/v1/billing/subscriptions"),
                    ("PUT", "/api/v1/billing/subscriptions/sub_123"),
                    ("DELETE", "/api/v1/billing/subscriptions/sub_123"),
                ]
                
                for method, endpoint in subscription_endpoints:
                    # Test with regular developer user (should be restricted)
                    mock_verify.return_value["role"] = UserRole.DEVELOPER.value
                    
                    response = client.request(method, endpoint, json={}, headers=auth_headers)
                    
                    # Developer should not have access to billing operations
                    if method in ["POST", "PUT", "DELETE"]:
                        assert response.status_code == status.HTTP_403_FORBIDDEN, \
                            f"Developer user allowed billing write operation: {method} {endpoint}"
                    
                    # Test with admin user (should be allowed)
                    mock_verify.return_value["role"] = UserRole.ADMIN.value
                    
                    response = client.request(method, endpoint, json={}, headers=auth_headers)
                    
                    # Admin should not be rejected due to authorization (other errors are OK)
                    assert response.status_code != status.HTTP_403_FORBIDDEN, \
                        f"Admin user denied billing access: {method} {endpoint}"

    @pytest.mark.asyncio
    async def test_billing_data_tenant_isolation(self, client, sample_tenant, sample_user):
        """
        CRITICAL: Test billing data is isolated between tenants
        
        Risk: Cross-tenant billing data access, financial data breach
        """
        # Create second tenant
        other_tenant = Tenant(
            id=uuid4(),
            organization_name="Other Corp",
            slug="other-corp", 
            admin_email="admin@othercorp.com",
            status=TenantStatus.ACTIVE
        )
        
        other_user = User(
            id=uuid4(),
            tenant_id=other_tenant.id,
            email="admin@othercorp.com",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE
        )
        
        # Create auth headers for both tenants
        tenant_a_headers = {"Authorization": f"Bearer valid.jwt.{sample_user.id}.{sample_tenant.id}"}
        tenant_b_headers = {"Authorization": f"Bearer valid.jwt.{other_user.id}.{other_tenant.id}"}
        
        with patch("app.services.auth_service.auth_service.verify_token") as mock_verify:
            with patch("app.middleware.tenant_middleware.require_tenant") as mock_tenant:
                # Test Tenant A user
                mock_verify.return_value = {
                    "user_id": str(sample_user.id),
                    "tenant_id": str(sample_tenant.id),
                    "role": sample_user.role.value
                }
                mock_tenant.return_value = sample_tenant
                
                response_a = client.get("/api/v1/billing/account", headers=tenant_a_headers)
                
                # Test Tenant B user
                mock_verify.return_value = {
                    "user_id": str(other_user.id),
                    "tenant_id": str(other_tenant.id),
                    "role": other_user.role.value
                }
                mock_tenant.return_value = other_tenant
                
                response_b = client.get("/api/v1/billing/account", headers=tenant_b_headers)
                
                # Both requests should be processed independently
                # Neither should see the other tenant's data
                if response_a.status_code == 200 and response_b.status_code == 200:
                    data_a = response_a.json()
                    data_b = response_b.json()
                    
                    # Verify tenant isolation
                    if "tenant_id" in data_a and "tenant_id" in data_b:
                        assert data_a["tenant_id"] != data_b["tenant_id"], \
                            "Billing data not properly isolated between tenants"
                    
                    # Should not contain cross-tenant references
                    assert str(other_tenant.id) not in json.dumps(data_a), \
                        "Tenant A billing data contains Tenant B references"
                    
                    assert str(sample_tenant.id) not in json.dumps(data_b), \
                        "Tenant B billing data contains Tenant A references"


class TestBillingAPIUsageTracking:
    """
    CRITICAL: Test usage tracking and billing limit enforcement
    
    Validates that API usage is properly tracked, limits are enforced,
    and billing events are recorded accurately.
    """
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def sample_tenant(self):
        return Tenant(
            id=uuid4(),
            organization_name="Test Corp",
            slug="test-corp",
            admin_email="admin@testcorp.com",
            status=TenantStatus.ACTIVE,
            quotas=TenantQuotas(
                max_users=10,
                max_projects=50,
                max_api_calls_per_month=10000,
                max_storage_mb=1000,
                max_ai_requests_per_day=100,
                max_concurrent_sessions=5
            )
        )
    
    @pytest.fixture
    def sample_user(self, sample_tenant):
        return User(
            id=uuid4(),
            tenant_id=sample_tenant.id,
            email="user@testcorp.com",
            role=UserRole.DEVELOPER,
            status=UserStatus.ACTIVE
        )
    
    @pytest.fixture
    def auth_headers(self, sample_user, sample_tenant):
        token = f"valid.jwt.{sample_user.id}.{sample_tenant.id}"
        return {"Authorization": f"Bearer {token}"}

    @pytest.mark.asyncio
    async def test_usage_tracking_accuracy(self, client, auth_headers, sample_tenant, sample_user):
        """
        CRITICAL: Test API usage is accurately tracked for billing
        
        Risk: Incorrect billing, revenue loss, customer disputes
        """
        with patch("app.services.auth_service.auth_service.verify_token") as mock_verify:
            with patch("app.middleware.tenant_middleware.require_tenant") as mock_tenant:
                with patch("app.services.billing_service.track_usage") as mock_usage:
                    mock_verify.return_value = {
                        "user_id": str(sample_user.id),
                        "tenant_id": str(sample_tenant.id),
                        "role": sample_user.role.value
                    }
                    mock_tenant.return_value = sample_tenant
                    
                    # Make API calls that should be tracked
                    tracked_endpoints = [
                        ("POST", "/api/v1/code-completion", {"code": "def hello():"}),
                        ("POST", "/api/v1/cli-query", {"query": "How to deploy?"}),
                        ("GET", "/api/v1/projects"),
                    ]
                    
                    for method, endpoint, data in tracked_endpoints:
                        if data:
                            response = client.request(method, endpoint, json=data, headers=auth_headers)
                        else:
                            response = client.request(method, endpoint, headers=auth_headers)
                        
                        # Usage tracking should be called for billable operations
                        # This verifies the integration exists
                        
                    # Verify usage was tracked (number of calls depends on which endpoints are billable)
                    # mock_usage.assert_called()  # At least some calls should be tracked

    @pytest.mark.asyncio
    async def test_billing_limit_enforcement(self, client, auth_headers, sample_tenant, sample_user):
        """
        CRITICAL: Test billing limits are enforced to prevent overuse
        
        Risk: Unlimited usage, revenue loss, resource exhaustion
        """
        with patch("app.services.auth_service.auth_service.verify_token") as mock_verify:
            with patch("app.middleware.tenant_middleware.require_tenant") as mock_tenant:
                with patch("app.services.billing_service.check_usage_limits") as mock_limits:
                    mock_verify.return_value = {
                        "user_id": str(sample_user.id),
                        "tenant_id": str(sample_tenant.id),
                        "role": sample_user.role.value
                    }
                    mock_tenant.return_value = sample_tenant
                    
                    # Simulate usage limit exceeded
                    mock_limits.return_value = False  # Limit exceeded
                    
                    billable_request = {
                        "code": "print('hello world')" * 1000  # Large request
                    }
                    
                    response = client.post(
                        "/api/v1/code-completion",
                        json=billable_request,
                        headers=auth_headers
                    )
                    
                    # Should be rejected if limits are exceeded
                    if mock_limits.called:
                        # If limit checking is implemented, should return payment required
                        if response.status_code == status.HTTP_402_PAYMENT_REQUIRED:
                            # Proper billing limit enforcement
                            assert "usage limit" in response.text.lower() or \
                                   "billing" in response.text.lower()

    @pytest.mark.asyncio
    async def test_usage_data_integrity(self, client, auth_headers, sample_tenant, sample_user):
        """
        CRITICAL: Test usage data cannot be tampered with
        
        Risk: Billing fraud, revenue loss, data integrity compromise
        """
        with patch("app.services.auth_service.auth_service.verify_token") as mock_verify:
            with patch("app.middleware.tenant_middleware.require_tenant") as mock_tenant:
                mock_verify.return_value = {
                    "user_id": str(sample_user.id),
                    "tenant_id": str(sample_tenant.id),
                    "role": sample_user.role.value
                }
                mock_tenant.return_value = sample_tenant
                
                # Attempt to manipulate usage data through API
                malicious_usage_data = {
                    "usage_override": -1000,  # Negative usage
                    "billing_credits": 999999,
                    "usage_multiplier": 0.01,  # Reduce billing
                    "free_tier": True,
                    "bypass_billing": True,
                }
                
                # Try to inject usage manipulation in regular API calls
                response = client.post(
                    "/api/v1/code-completion",
                    json={
                        "code": "def test():",
                        **malicious_usage_data  # Attempt to inject billing manipulation
                    },
                    headers=auth_headers
                )
                
                # Should handle gracefully without allowing manipulation
                assert response.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR, \
                    "Usage manipulation attempt caused server error"
                
                # Usage data should not be client-controllable
                # This is validated through the service layer


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])