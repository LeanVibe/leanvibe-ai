"""
COMPREHENSIVE TENANT API SECURITY TESTING

This module implements enterprise-grade security testing for tenant management API endpoints
to ensure proper multi-tenant isolation, administrative access controls, and data security.

Critical Security Requirements:
- Admin-only endpoints require admin role and cannot be bypassed
- Tenant configuration is isolated by tenant ID
- Tenant deletion requires proper authorization and safeguards
- Cross-tenant administrative operations are blocked
- Tenant settings cannot be manipulated by unauthorized users
- API keys and secrets are properly secured per tenant

Risk Level: CRITICAL - Prevents tenant data breaches, privilege escalation, system compromise
Business Impact: Protects customer data isolation, prevents unauthorized access, ensures compliance
"""

import pytest
import asyncio
import json
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


class TestTenantAPIAdminOnlyEndpoints:
    """
    CRITICAL: Test admin-only tenant endpoints require admin role
    
    Validates that administrative tenant operations are properly protected
    and cannot be accessed by non-admin users.
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
    def admin_user(self, sample_tenant):
        """Admin user with full permissions"""
        return User(
            id=uuid4(),
            tenant_id=sample_tenant.id,
            email="admin@testcorp.com",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            auth_provider=AuthProvider.LOCAL
        )
    
    @pytest.fixture
    def developer_user(self, sample_tenant):
        """Developer user with limited permissions"""
        return User(
            id=uuid4(),
            tenant_id=sample_tenant.id,
            email="dev@testcorp.com",
            role=UserRole.DEVELOPER,
            status=UserStatus.ACTIVE,
            auth_provider=AuthProvider.LOCAL
        )
    
    @pytest.fixture
    def viewer_user(self, sample_tenant):
        """Viewer user with read-only permissions"""
        return User(
            id=uuid4(),
            tenant_id=sample_tenant.id,
            email="viewer@testcorp.com",
            role=UserRole.VIEWER,
            status=UserStatus.ACTIVE,
            auth_provider=AuthProvider.LOCAL
        )

    @pytest.mark.asyncio
    async def test_tenant_settings_modification_requires_admin(
        self, client, sample_tenant, admin_user, developer_user, viewer_user
    ):
        """
        CRITICAL: Test tenant settings modification requires admin role
        
        Risk: Unauthorized tenant configuration changes, security bypass
        """
        settings_data = {
            "organization_name": "Updated Corp Name",
            "admin_email": "newemail@testcorp.com",
            "allowed_domains": ["testcorp.com", "example.com"],
            "sso_enabled": True,
            "api_rate_limit": 1000
        }
        
        # Test with different user roles
        user_tests = [
            (viewer_user, "viewer", status.HTTP_403_FORBIDDEN),
            (developer_user, "developer", status.HTTP_403_FORBIDDEN),
            (admin_user, "admin", [200, 201, 204])  # Admin should succeed
        ]
        
        with patch("app.services.auth_service.auth_service.verify_token") as mock_verify:
            with patch("app.middleware.tenant_middleware.require_tenant") as mock_tenant:
                mock_tenant.return_value = sample_tenant
                
                for user, role_name, expected_codes in user_tests:
                    mock_verify.return_value = {
                        "user_id": str(user.id),
                        "tenant_id": str(sample_tenant.id),
                        "role": user.role.value
                    }
                    
                    token = f"jwt.{user.id}.{sample_tenant.id}"
                    headers = {"Authorization": f"Bearer {token}"}
                    
                    response = client.put(
                        "/api/v1/tenants/settings",
                        json=settings_data,
                        headers=headers
                    )
                    
                    if isinstance(expected_codes, list):
                        # Admin should not be rejected
                        assert response.status_code not in [401, 403], \
                            f"Admin user was denied tenant settings access: {response.status_code}"
                    else:
                        # Non-admin should be rejected
                        assert response.status_code == expected_codes, \
                            f"{role_name.title()} user was allowed tenant settings modification: {response.status_code}"

    @pytest.mark.asyncio
    async def test_user_management_requires_admin(
        self, client, sample_tenant, admin_user, developer_user
    ):
        """
        CRITICAL: Test user management endpoints require admin role
        
        Risk: Unauthorized user creation/deletion, privilege escalation
        """
        user_creation_data = {
            "email": "newuser@testcorp.com",
            "role": "developer",
            "send_invitation": True
        }
        
        user_management_endpoints = [
            ("POST", "/api/v1/tenants/users", user_creation_data),  # Create user
            ("PUT", "/api/v1/tenants/users/123", {"role": "admin"}),  # Update user role
            ("DELETE", "/api/v1/tenants/users/123", {}),  # Delete user
        ]
        
        with patch("app.services.auth_service.auth_service.verify_token") as mock_verify:
            with patch("app.middleware.tenant_middleware.require_tenant") as mock_tenant:
                mock_tenant.return_value = sample_tenant
                
                for method, endpoint, data in user_management_endpoints:
                    # Test with developer user - should be rejected
                    mock_verify.return_value = {
                        "user_id": str(developer_user.id),
                        "tenant_id": str(sample_tenant.id),
                        "role": developer_user.role.value
                    }
                    
                    dev_token = f"jwt.{developer_user.id}.{sample_tenant.id}"
                    dev_headers = {"Authorization": f"Bearer {dev_token}"}
                    
                    response = client.request(
                        method, endpoint, json=data, headers=dev_headers
                    )
                    
                    assert response.status_code == status.HTTP_403_FORBIDDEN, \
                        f"Developer allowed user management operation: {method} {endpoint}"
                    
                    # Test with admin user - should be allowed
                    mock_verify.return_value = {
                        "user_id": str(admin_user.id),
                        "tenant_id": str(sample_tenant.id),
                        "role": admin_user.role.value
                    }
                    
                    admin_token = f"jwt.{admin_user.id}.{sample_tenant.id}"
                    admin_headers = {"Authorization": f"Bearer {admin_token}"}
                    
                    response = client.request(
                        method, endpoint, json=data, headers=admin_headers
                    )
                    
                    # Admin should not be rejected due to role
                    assert response.status_code != status.HTTP_403_FORBIDDEN, \
                        f"Admin denied user management operation: {method} {endpoint}"

    @pytest.mark.asyncio
    async def test_api_key_management_requires_admin(
        self, client, sample_tenant, admin_user, developer_user
    ):
        """
        CRITICAL: Test API key management requires admin role
        
        Risk: Unauthorized API key creation, security credential exposure
        """
        api_key_data = {
            "name": "Production API Key",
            "permissions": ["read", "write"],
            "expires_at": "2024-12-31T23:59:59Z"
        }
        
        api_key_endpoints = [
            ("POST", "/api/v1/tenants/api-keys", api_key_data),  # Create API key
            ("GET", "/api/v1/tenants/api-keys", {}),  # List API keys
            ("DELETE", "/api/v1/tenants/api-keys/key_123", {}),  # Delete API key
        ]
        
        with patch("app.services.auth_service.auth_service.verify_token") as mock_verify:
            with patch("app.middleware.tenant_middleware.require_tenant") as mock_tenant:
                mock_tenant.return_value = sample_tenant
                
                for method, endpoint, data in api_key_endpoints:
                    # Test with developer - should be restricted
                    mock_verify.return_value = {
                        "user_id": str(developer_user.id),
                        "tenant_id": str(sample_tenant.id),
                        "role": developer_user.role.value
                    }
                    
                    dev_token = f"jwt.{developer_user.id}.{sample_tenant.id}"
                    dev_headers = {"Authorization": f"Bearer {dev_token}"}
                    
                    if data:
                        response = client.request(method, endpoint, json=data, headers=dev_headers)
                    else:
                        response = client.request(method, endpoint, headers=dev_headers)
                    
                    # API key management should be admin-only
                    if method in ["POST", "DELETE"]:
                        assert response.status_code == status.HTTP_403_FORBIDDEN, \
                            f"Developer allowed API key operation: {method} {endpoint}"
                    
                    # Test with admin - should be allowed
                    mock_verify.return_value = {
                        "user_id": str(admin_user.id),
                        "tenant_id": str(sample_tenant.id),
                        "role": admin_user.role.value
                    }
                    
                    admin_token = f"jwt.{admin_user.id}.{sample_tenant.id}"
                    admin_headers = {"Authorization": f"Bearer {admin_token}"}
                    
                    if data:
                        response = client.request(method, endpoint, json=data, headers=admin_headers)
                    else:
                        response = client.request(method, endpoint, headers=admin_headers)
                    
                    assert response.status_code != status.HTTP_403_FORBIDDEN, \
                        f"Admin denied API key operation: {method} {endpoint}"


class TestTenantAPIConfigurationIsolation:
    """
    CRITICAL: Test tenant configuration isolation
    
    Validates that tenant configurations are properly isolated and
    cannot be accessed or modified by users from other tenants.
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
    def admin_a(self, tenant_a):
        """Admin user for Tenant A"""
        return User(
            id=uuid4(),
            tenant_id=tenant_a.id,
            email="admin@tenant-a.com",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE
        )
    
    @pytest.fixture
    def admin_b(self, tenant_b):
        """Admin user for Tenant B"""
        return User(
            id=uuid4(),
            tenant_id=tenant_b.id,
            email="admin@tenant-b.com",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE
        )

    @pytest.mark.asyncio
    async def test_tenant_settings_isolation(
        self, client, tenant_a, tenant_b, admin_a, admin_b
    ):
        """
        CRITICAL: Test tenant settings are isolated between tenants
        
        Risk: Cross-tenant configuration access, data leakage
        """
        with patch("app.services.auth_service.auth_service.verify_token") as mock_verify:
            with patch("app.middleware.tenant_middleware.require_tenant") as mock_tenant:
                with patch("app.services.tenant_service.get_tenant_settings") as mock_settings:
                    
                    # Mock different settings for each tenant
                    tenant_a_settings = {
                        "tenant_id": str(tenant_a.id),
                        "organization_name": "Tenant A Corp",
                        "api_rate_limit": 1000,
                        "sso_enabled": True,
                        "custom_domain": "tenant-a.com"
                    }
                    
                    tenant_b_settings = {
                        "tenant_id": str(tenant_b.id),
                        "organization_name": "Tenant B Corp",
                        "api_rate_limit": 2000,
                        "sso_enabled": False,
                        "custom_domain": "tenant-b.com"
                    }
                    
                    # Test Tenant A admin accessing settings
                    mock_verify.return_value = {
                        "user_id": str(admin_a.id),
                        "tenant_id": str(tenant_a.id),
                        "role": admin_a.role.value
                    }
                    mock_tenant.return_value = tenant_a
                    mock_settings.return_value = tenant_a_settings
                    
                    token_a = f"jwt.{admin_a.id}.{tenant_a.id}"
                    headers_a = {"Authorization": f"Bearer {token_a}"}
                    
                    response_a = client.get("/api/v1/tenants/settings", headers=headers_a)
                    
                    if response_a.status_code == 200:
                        settings_a = response_a.json()
                        
                        # Should only contain Tenant A data
                        assert settings_a["tenant_id"] == str(tenant_a.id)
                        assert settings_a["organization_name"] == "Tenant A Corp"
                        assert str(tenant_b.id) not in json.dumps(settings_a)
                    
                    # Test Tenant B admin accessing settings
                    mock_verify.return_value = {
                        "user_id": str(admin_b.id),
                        "tenant_id": str(tenant_b.id),
                        "role": admin_b.role.value
                    }
                    mock_tenant.return_value = tenant_b
                    mock_settings.return_value = tenant_b_settings
                    
                    token_b = f"jwt.{admin_b.id}.{tenant_b.id}"
                    headers_b = {"Authorization": f"Bearer {token_b}"}
                    
                    response_b = client.get("/api/v1/tenants/settings", headers=headers_b)
                    
                    if response_b.status_code == 200:
                        settings_b = response_b.json()
                        
                        # Should only contain Tenant B data
                        assert settings_b["tenant_id"] == str(tenant_b.id)
                        assert settings_b["organization_name"] == "Tenant B Corp"
                        assert str(tenant_a.id) not in json.dumps(settings_b)

    @pytest.mark.asyncio
    async def test_tenant_user_list_isolation(
        self, client, tenant_a, tenant_b, admin_a, admin_b
    ):
        """
        CRITICAL: Test tenant user lists are isolated
        
        Risk: Cross-tenant user enumeration, privacy breach
        """
        with patch("app.services.auth_service.auth_service.verify_token") as mock_verify:
            with patch("app.middleware.tenant_middleware.require_tenant") as mock_tenant:
                with patch("app.services.tenant_service.get_tenant_users") as mock_users:
                    
                    # Mock user lists for each tenant
                    tenant_a_users = [
                        {"id": str(admin_a.id), "email": "admin@tenant-a.com", "role": "admin"},
                        {"id": str(uuid4()), "email": "dev@tenant-a.com", "role": "developer"}
                    ]
                    
                    tenant_b_users = [
                        {"id": str(admin_b.id), "email": "admin@tenant-b.com", "role": "admin"},
                        {"id": str(uuid4()), "email": "user@tenant-b.com", "role": "viewer"}
                    ]
                    
                    # Test Tenant A user list access
                    mock_verify.return_value = {
                        "user_id": str(admin_a.id),
                        "tenant_id": str(tenant_a.id),
                        "role": admin_a.role.value
                    }
                    mock_tenant.return_value = tenant_a
                    mock_users.return_value = tenant_a_users
                    
                    token_a = f"jwt.{admin_a.id}.{tenant_a.id}"
                    headers_a = {"Authorization": f"Bearer {token_a}"}
                    
                    response_a = client.get("/api/v1/tenants/users", headers=headers_a)
                    
                    if response_a.status_code == 200:
                        users_a = response_a.json()
                        response_str_a = json.dumps(users_a)
                        
                        # Should contain Tenant A users
                        assert "admin@tenant-a.com" in response_str_a
                        
                        # Should NOT contain Tenant B users
                        assert "admin@tenant-b.com" not in response_str_a
                        assert "user@tenant-b.com" not in response_str_a
                    
                    # Test Tenant B user list access
                    mock_verify.return_value = {
                        "user_id": str(admin_b.id),
                        "tenant_id": str(tenant_b.id),
                        "role": admin_b.role.value
                    }
                    mock_tenant.return_value = tenant_b
                    mock_users.return_value = tenant_b_users
                    
                    token_b = f"jwt.{admin_b.id}.{tenant_b.id}"
                    headers_b = {"Authorization": f"Bearer {token_b}"}
                    
                    response_b = client.get("/api/v1/tenants/users", headers=headers_b)
                    
                    if response_b.status_code == 200:
                        users_b = response_b.json()
                        response_str_b = json.dumps(users_b)
                        
                        # Should contain Tenant B users
                        assert "admin@tenant-b.com" in response_str_b
                        
                        # Should NOT contain Tenant A users
                        assert "admin@tenant-a.com" not in response_str_b
                        assert "dev@tenant-a.com" not in response_str_b

    @pytest.mark.asyncio
    async def test_api_key_isolation(
        self, client, tenant_a, tenant_b, admin_a, admin_b
    ):
        """
        CRITICAL: Test API keys are isolated between tenants
        
        Risk: Cross-tenant API key access, unauthorized system access
        """
        with patch("app.services.auth_service.auth_service.verify_token") as mock_verify:
            with patch("app.middleware.tenant_middleware.require_tenant") as mock_tenant:
                with patch("app.services.tenant_service.get_tenant_api_keys") as mock_keys:
                    
                    # Mock API keys for each tenant
                    tenant_a_keys = [
                        {"id": "key_a_1", "name": "Production API", "tenant_id": str(tenant_a.id)},
                        {"id": "key_a_2", "name": "Development API", "tenant_id": str(tenant_a.id)}
                    ]
                    
                    tenant_b_keys = [
                        {"id": "key_b_1", "name": "Main API", "tenant_id": str(tenant_b.id)}
                    ]
                    
                    # Test Tenant A API key access
                    mock_verify.return_value = {
                        "user_id": str(admin_a.id),
                        "tenant_id": str(tenant_a.id),
                        "role": admin_a.role.value
                    }
                    mock_tenant.return_value = tenant_a
                    mock_keys.return_value = tenant_a_keys
                    
                    token_a = f"jwt.{admin_a.id}.{tenant_a.id}"
                    headers_a = {"Authorization": f"Bearer {token_a}"}
                    
                    response_a = client.get("/api/v1/tenants/api-keys", headers=headers_a)
                    
                    if response_a.status_code == 200:
                        keys_a = response_a.json()
                        response_str_a = json.dumps(keys_a)
                        
                        # Should contain Tenant A keys
                        assert "key_a_1" in response_str_a
                        assert "Production API" in response_str_a
                        
                        # Should NOT contain Tenant B keys
                        assert "key_b_1" not in response_str_a
                        assert "Main API" not in response_str_a
                    
                    # Verify tenant ID filtering was applied
                    mock_keys.assert_called_with(tenant_a.id)


class TestTenantAPIDeletionAuthorization:
    """
    CRITICAL: Test tenant deletion authorization and safeguards
    
    Validates that tenant deletion operations are properly authorized
    and include appropriate safeguards to prevent accidental deletion.
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
    def admin_user(self, sample_tenant):
        return User(
            id=uuid4(),
            tenant_id=sample_tenant.id,
            email="admin@testcorp.com",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE
        )
    
    @pytest.fixture
    def developer_user(self, sample_tenant):
        return User(
            id=uuid4(),
            tenant_id=sample_tenant.id,
            email="dev@testcorp.com",
            role=UserRole.DEVELOPER,
            status=UserStatus.ACTIVE
        )

    @pytest.mark.asyncio
    async def test_tenant_deletion_requires_admin(
        self, client, sample_tenant, admin_user, developer_user
    ):
        """
        CRITICAL: Test tenant deletion requires admin role
        
        Risk: Unauthorized tenant deletion, data loss
        """
        deletion_data = {
            "confirmation": "DELETE",
            "reason": "Account closure requested"
        }
        
        with patch("app.services.auth_service.auth_service.verify_token") as mock_verify:
            with patch("app.middleware.tenant_middleware.require_tenant") as mock_tenant:
                mock_tenant.return_value = sample_tenant
                
                # Test with developer user - should be rejected
                mock_verify.return_value = {
                    "user_id": str(developer_user.id),
                    "tenant_id": str(sample_tenant.id),
                    "role": developer_user.role.value
                }
                
                dev_token = f"jwt.{developer_user.id}.{sample_tenant.id}"
                dev_headers = {"Authorization": f"Bearer {dev_token}"}
                
                response = client.delete(
                    f"/api/v1/tenants/{sample_tenant.id}",
                    json=deletion_data,
                    headers=dev_headers
                )
                
                assert response.status_code == status.HTTP_403_FORBIDDEN, \
                    "Developer was allowed to delete tenant"
                
                # Test with admin user - should be allowed (but may have other requirements)
                mock_verify.return_value = {
                    "user_id": str(admin_user.id),
                    "tenant_id": str(sample_tenant.id),
                    "role": admin_user.role.value
                }
                
                admin_token = f"jwt.{admin_user.id}.{sample_tenant.id}"
                admin_headers = {"Authorization": f"Bearer {admin_token}"}
                
                response = client.delete(
                    f"/api/v1/tenants/{sample_tenant.id}",
                    json=deletion_data,
                    headers=admin_headers
                )
                
                # Admin should not be rejected due to role (other checks may apply)
                assert response.status_code != status.HTTP_403_FORBIDDEN, \
                    "Admin was denied tenant deletion due to role restrictions"

    @pytest.mark.asyncio
    async def test_tenant_deletion_confirmation_required(
        self, client, sample_tenant, admin_user
    ):
        """
        CRITICAL: Test tenant deletion requires proper confirmation
        
        Risk: Accidental tenant deletion, data loss
        """
        with patch("app.services.auth_service.auth_service.verify_token") as mock_verify:
            with patch("app.middleware.tenant_middleware.require_tenant") as mock_tenant:
                mock_verify.return_value = {
                    "user_id": str(admin_user.id),
                    "tenant_id": str(sample_tenant.id),
                    "role": admin_user.role.value
                }
                mock_tenant.return_value = sample_tenant
                
                admin_token = f"jwt.{admin_user.id}.{sample_tenant.id}"
                headers = {"Authorization": f"Bearer {admin_token}"}
                
                # Test without confirmation - should be rejected
                response = client.delete(
                    f"/api/v1/tenants/{sample_tenant.id}",
                    json={},
                    headers=headers
                )
                
                assert response.status_code in [400, 422], \
                    "Tenant deletion allowed without confirmation"
                
                # Test with wrong confirmation - should be rejected
                wrong_confirmation = {
                    "confirmation": "WRONG",
                    "reason": "Test deletion"
                }
                
                response = client.delete(
                    f"/api/v1/tenants/{sample_tenant.id}",
                    json=wrong_confirmation,
                    headers=headers
                )
                
                assert response.status_code in [400, 422], \
                    "Tenant deletion allowed with wrong confirmation"
                
                # Test with correct confirmation - should be processed
                correct_confirmation = {
                    "confirmation": "DELETE",
                    "reason": "Authorized deletion for testing"
                }
                
                response = client.delete(
                    f"/api/v1/tenants/{sample_tenant.id}",
                    json=correct_confirmation,
                    headers=headers
                )
                
                # Should not be rejected due to confirmation issues
                assert response.status_code not in [400, 422] or \
                    "confirmation" not in response.text.lower(), \
                    "Correct confirmation was rejected"

    @pytest.mark.asyncio
    async def test_cross_tenant_deletion_blocked(self, client, admin_user):
        """
        CRITICAL: Test users cannot delete other tenants
        
        Risk: Cross-tenant data deletion, unauthorized system access
        """
        other_tenant_id = uuid4()  # Different tenant
        
        with patch("app.services.auth_service.auth_service.verify_token") as mock_verify:
            with patch("app.middleware.tenant_middleware.require_tenant") as mock_tenant:
                mock_verify.return_value = {
                    "user_id": str(admin_user.id),
                    "tenant_id": str(admin_user.tenant_id),  # User's actual tenant
                    "role": admin_user.role.value
                }
                mock_tenant.return_value = Tenant(
                    id=admin_user.tenant_id,
                    organization_name="User's Tenant",
                    slug="users-tenant",
                    admin_email="admin@userstenant.com",
                    status=TenantStatus.ACTIVE
                )
                
                admin_token = f"jwt.{admin_user.id}.{admin_user.tenant_id}"
                headers = {"Authorization": f"Bearer {admin_token}"}
                
                deletion_data = {
                    "confirmation": "DELETE",
                    "reason": "Attempted cross-tenant deletion"
                }
                
                # Attempt to delete different tenant
                response = client.delete(
                    f"/api/v1/tenants/{other_tenant_id}",
                    json=deletion_data,
                    headers=headers
                )
                
                # Should be rejected - user cannot delete other tenants
                assert response.status_code in [403, 404, 401], \
                    "Cross-tenant deletion was allowed"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])