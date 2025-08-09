"""
COMPREHENSIVE API ENDPOINT AUTHENTICATION & AUTHORIZATION TESTING

This module implements enterprise-grade security testing for all API endpoints
to ensure proper JWT validation, tenant isolation, and RBAC enforcement.

Critical Security Requirements:
- All customer-facing endpoints require valid JWT authentication
- API responses are filtered by tenant context (multi-tenant isolation)
- Role-based access control is enforced on all sensitive operations
- Invalid/expired tokens are properly rejected
- Cross-tenant resource access is blocked

Risk Level: CRITICAL - Prevents unauthorized access and data breaches
Business Impact: Protects customer data, ensures compliance, prevents financial losses
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from unittest.mock import AsyncMock, patch, MagicMock

from fastapi.testclient import TestClient
from fastapi import status
import httpx

from app.main import app
from app.models.auth_models import User, UserRole, UserStatus, AuthProvider
from app.models.tenant_models import Tenant, TenantStatus, TenantQuotas
from app.core.exceptions import InvalidCredentialsError, TokenExpiredError


class TestAPIEndpointAuthentication:
    """
    CRITICAL: Test authentication requirements for all API endpoints
    
    Validates that every customer-facing endpoint properly validates JWT tokens
    and rejects unauthorized access attempts.
    """
    
    @pytest.fixture
    def client(self):
        """HTTP test client"""
        return TestClient(app)
    
    @pytest.fixture
    def sample_tenant(self):
        """Sample active tenant for testing"""
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
        """Sample authenticated user"""
        return User(
            id=uuid4(),
            tenant_id=sample_tenant.id,
            email="user@testcorp.com",
            role=UserRole.DEVELOPER,
            status=UserStatus.ACTIVE,
            auth_provider=AuthProvider.LOCAL
        )
    
    @pytest.fixture
    def admin_user(self, sample_tenant):
        """Sample admin user for RBAC testing"""
        return User(
            id=uuid4(),
            tenant_id=sample_tenant.id,
            email="admin@testcorp.com",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            auth_provider=AuthProvider.LOCAL
        )
    
    @pytest.fixture
    def valid_jwt_token(self, sample_user, sample_tenant):
        """Mock valid JWT token for testing"""
        return f"valid.jwt.{sample_user.id}.{sample_tenant.id}"
    
    @pytest.fixture
    def expired_jwt_token(self):
        """Mock expired JWT token for testing"""
        return "expired.jwt.token"
    
    @pytest.fixture
    def malformed_jwt_token(self):
        """Mock malformed JWT token for testing"""
        return "malformed.invalid.token"

    # Core Authentication Endpoint Tests
    @pytest.mark.asyncio
    async def test_all_auth_endpoints_require_valid_jwt(self, client, valid_jwt_token, sample_tenant, sample_user):
        """
        CRITICAL: Test all authentication endpoints require valid JWT tokens
        
        Risk: Authentication bypass, unauthorized access to user accounts
        """
        auth_endpoints = [
            ("GET", "/api/v1/auth/me"),
            ("POST", "/api/v1/auth/mfa/setup"),
            ("POST", "/api/v1/auth/mfa/verify"),
            ("POST", "/api/v1/auth/logout"),
        ]
        
        with patch("app.services.auth_service.auth_service.verify_token") as mock_verify:
            # Setup valid token verification
            mock_verify.return_value = {
                "user_id": str(sample_user.id),
                "tenant_id": str(sample_tenant.id),
                "role": sample_user.role.value,
                "exp": (datetime.utcnow() + timedelta(hours=1)).timestamp()
            }
            
            with patch("app.services.auth_service.auth_service.get_user_by_id") as mock_get_user:
                mock_get_user.return_value = sample_user
                
                for method, endpoint in auth_endpoints:
                    # Test with valid token - should succeed
                    headers = {"Authorization": f"Bearer {valid_jwt_token}"}
                    
                    if method == "GET":
                        response = client.get(endpoint, headers=headers)
                    else:
                        response = client.post(endpoint, json={}, headers=headers)
                    
                    # Should not return 401 Unauthorized for valid tokens
                    assert response.status_code != status.HTTP_401_UNAUTHORIZED, \
                        f"Endpoint {method} {endpoint} rejected valid JWT token"
                    
                    # Test without token - should fail
                    if method == "GET":
                        response = client.get(endpoint)
                    else:
                        response = client.post(endpoint, json={})
                    
                    assert response.status_code == status.HTTP_401_UNAUTHORIZED, \
                        f"Endpoint {method} {endpoint} allowed access without JWT token"

    @pytest.mark.asyncio 
    async def test_billing_endpoints_require_valid_jwt(self, client, valid_jwt_token, sample_tenant, sample_user):
        """
        CRITICAL: Test billing endpoints require valid JWT authentication
        
        Risk: Unauthorized access to payment information and financial data
        """
        billing_endpoints = [
            ("GET", "/api/v1/billing/account"),
            ("POST", "/api/v1/billing/account"),
            ("GET", "/api/v1/billing/subscriptions"),
            ("POST", "/api/v1/billing/subscriptions"),
            ("GET", "/api/v1/billing/usage"),
            ("POST", "/api/v1/billing/payment-methods"),
            ("GET", "/api/v1/billing/invoices"),
        ]
        
        with patch("app.services.auth_service.auth_service.verify_token") as mock_verify:
            mock_verify.return_value = {
                "user_id": str(sample_user.id),
                "tenant_id": str(sample_tenant.id),
                "role": sample_user.role.value
            }
            
            with patch("app.middleware.tenant_middleware.require_tenant") as mock_tenant:
                mock_tenant.return_value = sample_tenant
                
                for method, endpoint in billing_endpoints:
                    # Test without authentication - should fail
                    if method == "GET":
                        response = client.get(endpoint)
                    else:
                        response = client.post(endpoint, json={})
                    
                    assert response.status_code == status.HTTP_401_UNAUTHORIZED, \
                        f"Billing endpoint {method} {endpoint} allowed access without authentication"
                    
                    # Test with valid token - should at least not return 401
                    headers = {"Authorization": f"Bearer {valid_jwt_token}"}
                    if method == "GET":
                        response = client.get(endpoint, headers=headers)
                    else:
                        response = client.post(endpoint, json={}, headers=headers)
                    
                    assert response.status_code != status.HTTP_401_UNAUTHORIZED, \
                        f"Billing endpoint {method} {endpoint} rejected valid JWT token"

    @pytest.mark.asyncio
    async def test_tenant_endpoints_require_valid_jwt(self, client, valid_jwt_token, sample_tenant, sample_user):
        """
        CRITICAL: Test tenant management endpoints require valid JWT authentication
        
        Risk: Unauthorized tenant modifications, privilege escalation
        """
        tenant_endpoints = [
            ("GET", "/api/v1/tenants/settings"),
            ("PUT", "/api/v1/tenants/settings"),
            ("GET", "/api/v1/tenants/users"),
            ("POST", "/api/v1/tenants/users"),
            ("GET", "/api/v1/tenants/api-keys"),
            ("POST", "/api/v1/tenants/api-keys"),
        ]
        
        with patch("app.services.auth_service.auth_service.verify_token") as mock_verify:
            mock_verify.return_value = {
                "user_id": str(sample_user.id),
                "tenant_id": str(sample_tenant.id),
                "role": sample_user.role.value
            }
            
            with patch("app.middleware.tenant_middleware.require_tenant") as mock_tenant:
                mock_tenant.return_value = sample_tenant
                
                for method, endpoint in tenant_endpoints:
                    # Test without authentication - should fail
                    if method == "GET":
                        response = client.get(endpoint)
                    else:
                        response = client.request(method, endpoint, json={})
                    
                    assert response.status_code == status.HTTP_401_UNAUTHORIZED, \
                        f"Tenant endpoint {method} {endpoint} allowed access without authentication"

    @pytest.mark.asyncio
    async def test_project_endpoints_require_valid_jwt(self, client, valid_jwt_token, sample_tenant, sample_user):
        """
        CRITICAL: Test project management endpoints require valid JWT authentication
        
        Risk: Unauthorized access to customer projects and code
        """
        project_endpoints = [
            ("GET", "/api/v1/projects"),
            ("POST", "/api/v1/projects"),
            ("GET", "/api/v1/projects/123"),
            ("PUT", "/api/v1/projects/123"),
            ("DELETE", "/api/v1/projects/123"),
        ]
        
        with patch("app.services.auth_service.auth_service.verify_token") as mock_verify:
            mock_verify.return_value = {
                "user_id": str(sample_user.id),
                "tenant_id": str(sample_tenant.id),
                "role": sample_user.role.value
            }
            
            with patch("app.middleware.tenant_middleware.require_tenant") as mock_tenant:
                mock_tenant.return_value = sample_tenant
                
                for method, endpoint in project_endpoints:
                    # Test without authentication - should fail
                    response = client.request(method, endpoint, json={} if method != "GET" else None)
                    
                    assert response.status_code == status.HTTP_401_UNAUTHORIZED, \
                        f"Project endpoint {method} {endpoint} allowed access without authentication"

    @pytest.mark.asyncio
    async def test_invalid_token_rejection(self, client, expired_jwt_token, malformed_jwt_token):
        """
        CRITICAL: Test invalid/expired/malformed tokens are properly rejected
        
        Risk: Authentication bypass through token manipulation
        """
        test_endpoint = "/api/v1/auth/me"
        
        # Test expired token
        with patch("app.services.auth_service.auth_service.verify_token") as mock_verify:
            mock_verify.side_effect = TokenExpiredError("Token expired")
            
            headers = {"Authorization": f"Bearer {expired_jwt_token}"}
            response = client.get(test_endpoint, headers=headers)
            
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert "expired" in response.json().get("detail", "").lower()
        
        # Test malformed token
        with patch("app.services.auth_service.auth_service.verify_token") as mock_verify:
            mock_verify.side_effect = InvalidCredentialsError("Invalid token")
            
            headers = {"Authorization": f"Bearer {malformed_jwt_token}"}
            response = client.get(test_endpoint, headers=headers)
            
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Test missing Bearer prefix
        headers = {"Authorization": malformed_jwt_token}  # Missing "Bearer "
        response = client.get(test_endpoint, headers=headers)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Test empty token
        headers = {"Authorization": "Bearer "}
        response = client.get(test_endpoint, headers=headers)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestAPITenantIsolation:
    """
    CRITICAL: Test API responses are filtered by tenant context
    
    Validates that users can only access resources within their tenant
    and cross-tenant data access is blocked.
    """
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def tenant_a(self):
        """First tenant for isolation testing"""
        return Tenant(
            id=uuid4(),
            organization_name="Tenant A Corp",
            slug="tenant-a",
            admin_email="admin@tenant-a.com",
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
    def tenant_b(self):
        """Second tenant for isolation testing"""
        return Tenant(
            id=uuid4(),
            organization_name="Tenant B Corp", 
            slug="tenant-b",
            admin_email="admin@tenant-b.com",
            status=TenantStatus.ACTIVE,
            quotas=TenantQuotas(
                max_users=20,
                max_projects=100,
                max_api_calls_per_month=20000,
                max_storage_mb=2000,
                max_ai_requests_per_day=200,
                max_concurrent_sessions=10
            )
        )
    
    @pytest.fixture
    def user_tenant_a(self, tenant_a):
        """User belonging to Tenant A"""
        return User(
            id=uuid4(),
            tenant_id=tenant_a.id,
            email="user@tenant-a.com",
            role=UserRole.DEVELOPER,
            status=UserStatus.ACTIVE
        )
    
    @pytest.fixture
    def user_tenant_b(self, tenant_b):
        """User belonging to Tenant B"""
        return User(
            id=uuid4(),
            tenant_id=tenant_b.id,
            email="user@tenant-b.com",
            role=UserRole.DEVELOPER,
            status=UserStatus.ACTIVE
        )

    @pytest.mark.asyncio
    async def test_tenant_isolation_in_project_api(self, client, user_tenant_a, user_tenant_b, tenant_a, tenant_b):
        """
        CRITICAL: Test project API responses are filtered by tenant
        
        Risk: Cross-tenant data access, exposure of customer projects
        """
        token_a = f"valid.jwt.{user_tenant_a.id}.{tenant_a.id}"
        token_b = f"valid.jwt.{user_tenant_b.id}.{tenant_b.id}"
        
        with patch("app.services.auth_service.auth_service.verify_token") as mock_verify:
            with patch("app.middleware.tenant_middleware.require_tenant") as mock_tenant:
                with patch("app.services.project_service.get_tenant_projects") as mock_projects:
                    
                    # Setup mock responses
                    tenant_a_projects = [{"id": "proj-a-1", "name": "Project A1"}]
                    tenant_b_projects = [{"id": "proj-b-1", "name": "Project B1"}]
                    
                    # Test Tenant A user can only see Tenant A projects
                    mock_verify.return_value = {
                        "user_id": str(user_tenant_a.id),
                        "tenant_id": str(tenant_a.id),
                        "role": "developer"
                    }
                    mock_tenant.return_value = tenant_a
                    mock_projects.return_value = tenant_a_projects
                    
                    headers_a = {"Authorization": f"Bearer {token_a}"}
                    response = client.get("/api/v1/projects", headers=headers_a)
                    
                    # Should return only Tenant A projects
                    assert response.status_code == 200
                    projects = response.json()
                    assert len(projects) == 1
                    assert projects[0]["name"] == "Project A1"
                    
                    # Verify tenant isolation was enforced
                    mock_projects.assert_called_with(tenant_a.id)
                    
                    # Test Tenant B user can only see Tenant B projects
                    mock_verify.return_value = {
                        "user_id": str(user_tenant_b.id),
                        "tenant_id": str(tenant_b.id),
                        "role": "developer"
                    }
                    mock_tenant.return_value = tenant_b
                    mock_projects.return_value = tenant_b_projects
                    
                    headers_b = {"Authorization": f"Bearer {token_b}"}
                    response = client.get("/api/v1/projects", headers=headers_b)
                    
                    # Should return only Tenant B projects
                    assert response.status_code == 200
                    projects = response.json()
                    assert len(projects) == 1
                    assert projects[0]["name"] == "Project B1"
                    
                    # Verify tenant isolation was enforced
                    mock_projects.assert_called_with(tenant_b.id)

    @pytest.mark.asyncio
    async def test_tenant_isolation_in_billing_api(self, client, user_tenant_a, user_tenant_b, tenant_a, tenant_b):
        """
        CRITICAL: Test billing API responses are filtered by tenant
        
        Risk: Cross-tenant billing data access, financial data exposure
        """
        token_a = f"valid.jwt.{user_tenant_a.id}.{tenant_a.id}"
        token_b = f"valid.jwt.{user_tenant_b.id}.{tenant_b.id}"
        
        with patch("app.services.auth_service.auth_service.verify_token") as mock_verify:
            with patch("app.middleware.tenant_middleware.require_tenant") as mock_tenant:
                with patch("app.services.billing_service.get_tenant_billing_account") as mock_billing:
                    
                    # Setup mock billing accounts
                    billing_a = {"tenant_id": str(tenant_a.id), "balance": 100.0}
                    billing_b = {"tenant_id": str(tenant_b.id), "balance": 200.0}
                    
                    # Test Tenant A user can only see Tenant A billing
                    mock_verify.return_value = {
                        "user_id": str(user_tenant_a.id),
                        "tenant_id": str(tenant_a.id),
                        "role": "admin"
                    }
                    mock_tenant.return_value = tenant_a
                    mock_billing.return_value = billing_a
                    
                    headers_a = {"Authorization": f"Bearer {token_a}"}
                    response = client.get("/api/v1/billing/account", headers=headers_a)
                    
                    # Should return only Tenant A billing data
                    if response.status_code == 200:
                        billing_data = response.json()
                        assert billing_data["tenant_id"] == str(tenant_a.id)
                        assert billing_data["balance"] == 100.0
                        
                        # Verify tenant isolation was enforced
                        mock_billing.assert_called_with(tenant_a.id)

    @pytest.mark.asyncio
    async def test_cross_tenant_resource_access_blocked(self, client, user_tenant_a, tenant_b):
        """
        CRITICAL: Test cross-tenant resource access is blocked
        
        Risk: Unauthorized access to other tenant's resources
        """
        token_a = f"valid.jwt.{user_tenant_a.id}.{tenant_b.id}"  # User A trying to access Tenant B
        
        with patch("app.services.auth_service.auth_service.verify_token") as mock_verify:
            # Setup user from Tenant A trying to access Tenant B resources
            mock_verify.return_value = {
                "user_id": str(user_tenant_a.id),
                "tenant_id": str(tenant_b.id),  # Different tenant
                "role": "admin"
            }
            
            headers = {"Authorization": f"Bearer {token_a}"}
            
            # Should be blocked by tenant middleware or authorization logic
            response = client.get("/api/v1/projects", headers=headers)
            
            # Should either return 403 Forbidden or filter out unauthorized data
            assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED], \
                "Cross-tenant access was not blocked"


class TestAPIRBACEnforcement:
    """
    CRITICAL: Test Role-Based Access Control enforcement on API endpoints
    
    Validates that role restrictions are properly enforced across all sensitive operations.
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
    def developer_user(self, sample_tenant):
        """Developer role user - limited permissions"""
        return User(
            id=uuid4(),
            tenant_id=sample_tenant.id,
            email="developer@testcorp.com",
            role=UserRole.DEVELOPER,
            status=UserStatus.ACTIVE
        )
    
    @pytest.fixture
    def admin_user(self, sample_tenant):
        """Admin role user - full permissions"""
        return User(
            id=uuid4(),
            tenant_id=sample_tenant.id,
            email="admin@testcorp.com",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE
        )

    @pytest.mark.asyncio
    async def test_admin_only_endpoints_require_admin_role(self, client, developer_user, admin_user, sample_tenant):
        """
        CRITICAL: Test admin-only endpoints require admin role
        
        Risk: Privilege escalation, unauthorized administrative operations
        """
        admin_only_endpoints = [
            ("POST", "/api/v1/tenants/users"),  # User creation
            ("DELETE", "/api/v1/tenants/users/123"),  # User deletion
            ("PUT", "/api/v1/tenants/settings"),  # Tenant settings
            ("POST", "/api/v1/tenants/api-keys"),  # API key creation
        ]
        
        with patch("app.services.auth_service.auth_service.verify_token") as mock_verify:
            with patch("app.middleware.tenant_middleware.require_tenant") as mock_tenant:
                mock_tenant.return_value = sample_tenant
                
                for method, endpoint in admin_only_endpoints:
                    # Test with developer role - should be denied
                    mock_verify.return_value = {
                        "user_id": str(developer_user.id),
                        "tenant_id": str(sample_tenant.id),
                        "role": developer_user.role.value
                    }
                    
                    dev_token = f"dev.jwt.{developer_user.id}"
                    headers = {"Authorization": f"Bearer {dev_token}"}
                    
                    response = client.request(method, endpoint, json={}, headers=headers)
                    
                    assert response.status_code == status.HTTP_403_FORBIDDEN, \
                        f"Endpoint {method} {endpoint} allowed developer access - should require admin"
                    
                    # Test with admin role - should be allowed (or at least not 403)
                    mock_verify.return_value = {
                        "user_id": str(admin_user.id),
                        "tenant_id": str(sample_tenant.id),
                        "role": admin_user.role.value
                    }
                    
                    admin_token = f"admin.jwt.{admin_user.id}"
                    headers = {"Authorization": f"Bearer {admin_token}"}
                    
                    response = client.request(method, endpoint, json={}, headers=headers)
                    
                    assert response.status_code != status.HTTP_403_FORBIDDEN, \
                        f"Endpoint {method} {endpoint} denied admin access"

    @pytest.mark.asyncio
    async def test_billing_endpoints_require_appropriate_roles(self, client, developer_user, admin_user, sample_tenant):
        """
        CRITICAL: Test billing endpoints enforce role-based access
        
        Risk: Unauthorized billing modifications, financial data access
        """
        # Billing read operations - developers can view
        read_endpoints = [
            ("GET", "/api/v1/billing/account"),
            ("GET", "/api/v1/billing/usage"),
            ("GET", "/api/v1/billing/invoices"),
        ]
        
        # Billing write operations - admin only
        admin_billing_endpoints = [
            ("POST", "/api/v1/billing/subscriptions"),
            ("PUT", "/api/v1/billing/subscriptions/123"),
            ("POST", "/api/v1/billing/payment-methods"),
        ]
        
        with patch("app.services.auth_service.auth_service.verify_token") as mock_verify:
            with patch("app.middleware.tenant_middleware.require_tenant") as mock_tenant:
                mock_tenant.return_value = sample_tenant
                
                # Test read operations - developers should have access
                for method, endpoint in read_endpoints:
                    mock_verify.return_value = {
                        "user_id": str(developer_user.id),
                        "tenant_id": str(sample_tenant.id),
                        "role": developer_user.role.value
                    }
                    
                    dev_token = f"dev.jwt.{developer_user.id}"
                    headers = {"Authorization": f"Bearer {dev_token}"}
                    
                    response = client.request(method, endpoint, headers=headers)
                    
                    # Should not be 403 Forbidden for read operations
                    assert response.status_code != status.HTTP_403_FORBIDDEN, \
                        f"Billing read endpoint {method} {endpoint} denied developer access"
                
                # Test write operations - admin only
                for method, endpoint in admin_billing_endpoints:
                    # Developer should be denied
                    mock_verify.return_value = {
                        "user_id": str(developer_user.id),
                        "tenant_id": str(sample_tenant.id),
                        "role": developer_user.role.value
                    }
                    
                    dev_token = f"dev.jwt.{developer_user.id}"
                    headers = {"Authorization": f"Bearer {dev_token}"}
                    
                    response = client.request(method, endpoint, json={}, headers=headers)
                    
                    assert response.status_code == status.HTTP_403_FORBIDDEN, \
                        f"Billing write endpoint {method} {endpoint} allowed developer access"
                    
                    # Admin should be allowed
                    mock_verify.return_value = {
                        "user_id": str(admin_user.id),
                        "tenant_id": str(sample_tenant.id),
                        "role": admin_user.role.value
                    }
                    
                    admin_token = f"admin.jwt.{admin_user.id}"
                    headers = {"Authorization": f"Bearer {admin_token}"}
                    
                    response = client.request(method, endpoint, json={}, headers=headers)
                    
                    assert response.status_code != status.HTTP_403_FORBIDDEN, \
                        f"Billing write endpoint {method} {endpoint} denied admin access"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])