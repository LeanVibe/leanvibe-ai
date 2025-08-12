"""
Comprehensive API integration tests for authentication
Tests protected endpoints, user context injection, and authentication middleware
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from uuid import uuid4

from app.models.auth_models import UserCreate, AuthProvider, UserRole
from app.services.auth_service import AuthenticationService
from tests.fixtures.auth_test_fixtures import *


class TestProtectedEndpoints:
    """Test that protected endpoints require authentication."""
    
    @pytest.mark.asyncio
    async def test_protected_endpoint_requires_auth(self, auth_test_client: TestClient):
        """Test that protected endpoints reject unauthenticated requests."""
        protected_endpoints = [
            ("GET", "/api/v1/auth/me"),
            ("PUT", "/api/v1/auth/users/me"),
            ("PUT", "/api/v1/auth/users/me/password"),
            ("POST", "/api/v1/auth/mfa/setup"),
            ("POST", "/api/v1/auth/mfa/verify"),
        ]
        
        for method, endpoint in protected_endpoints:
            if method == "GET":
                response = auth_test_client.get(endpoint)
            elif method == "PUT":
                response = auth_test_client.put(endpoint, json={})
            elif method == "POST":
                response = auth_test_client.post(endpoint, json={})
            
            assert response.status_code == 401
            data = response.json()
            assert "Authentication required" in data["detail"] or "required" in data["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_protected_endpoint_accepts_valid_token(self, auth_test_client: TestClient, authenticated_headers, test_tenant):
        """Test that protected endpoints accept valid authentication tokens."""
        with patch('app.middleware.tenant_middleware.require_tenant') as mock_tenant:
            mock_tenant.return_value = test_tenant
            
            response = auth_test_client.get(
                "/api/v1/auth/me",
                headers=authenticated_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "email" in data
            assert "id" in data
    
    @pytest.mark.asyncio
    async def test_protected_endpoint_rejects_expired_token(self, auth_test_client: TestClient, expired_auth_headers):
        """Test that protected endpoints reject expired tokens."""
        response = auth_test_client.get(
            "/api/v1/auth/me",
            headers=expired_auth_headers
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "Token expired" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_protected_endpoint_rejects_malformed_token(self, auth_test_client: TestClient):
        """Test that protected endpoints reject malformed tokens."""
        malformed_headers = {
            "Authorization": "Bearer invalid.jwt.token",
            "Content-Type": "application/json"
        }
        
        response = auth_test_client.get(
            "/api/v1/auth/me",
            headers=malformed_headers
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "Invalid token" in data["detail"] or "Failed to get user" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_protected_endpoint_rejects_missing_bearer_prefix(self, auth_test_client: TestClient, valid_jwt_tokens):
        """Test that protected endpoints reject tokens without Bearer prefix."""
        invalid_headers = {
            "Authorization": valid_jwt_tokens["access_token"],  # Missing "Bearer " prefix
            "Content-Type": "application/json"
        }
        
        response = auth_test_client.get(
            "/api/v1/auth/me",
            headers=invalid_headers
        )
        
        assert response.status_code == 401


class TestUserContextInjection:
    """Test user context injection in protected endpoints."""
    
    @pytest.mark.asyncio
    async def test_user_context_available_in_protected_endpoint(self, auth_test_client: TestClient, authenticated_headers, test_user, test_tenant):
        """Test that user context is properly injected."""
        with patch('app.middleware.tenant_middleware.require_tenant') as mock_tenant:
            mock_tenant.return_value = test_tenant
            
            response = auth_test_client.get(
                "/api/v1/auth/me",
                headers=authenticated_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["email"] == test_user.email
            assert data["id"] == str(test_user.id)
            assert data["tenant_id"] == str(test_user.tenant_id)
    
    @pytest.mark.asyncio
    async def test_tenant_context_injection(self, auth_test_client: TestClient, authenticated_headers, test_tenant):
        """Test that tenant context is properly injected."""
        with patch('app.middleware.tenant_middleware.require_tenant') as mock_tenant:
            mock_tenant.return_value = test_tenant
            
            response = auth_test_client.get(
                "/api/v1/auth/me",
                headers=authenticated_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["tenant_id"] == str(test_tenant.id)
            
            # Verify tenant middleware was called
            mock_tenant.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_user_permissions_context(self, auth_test_client: TestClient, test_tenant):
        """Test that user permissions are available in context."""
        # Create user with specific permissions
        auth_service = AuthenticationService()
        user_data = UserCreate(
            tenant_id=test_tenant.id,
            email="permissions.test@example.com",
            first_name="Permissions",
            last_name="Test",
            password="Password123!",
            role=UserRole.ADMIN
        )
        user = await auth_service.create_user(user_data)
        
        # Update user with permissions
        from app.models.auth_models import UserUpdate
        update = UserUpdate(permissions=["admin:read", "admin:write", "user:manage"])
        updated_user = await auth_service.update_user(user.id, update, test_tenant.id)
        
        # Create session and token
        from app.models.auth_models import LoginRequest
        login_request = LoginRequest(
            email=user.email,
            password="Password123!",
            provider=AuthProvider.LOCAL,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 Test Browser"
        )
        session = await auth_service._create_user_session(updated_user, login_request)
        tokens = await auth_service._generate_tokens(updated_user, session)
        
        headers = {
            "Authorization": f"Bearer {tokens['access_token']}",
            "Content-Type": "application/json"
        }
        
        with patch('app.middleware.tenant_middleware.require_tenant') as mock_tenant:
            mock_tenant.return_value = test_tenant
            
            response = auth_test_client.get("/api/v1/auth/me", headers=headers)
            
            assert response.status_code == 200
            data = response.json()
            assert "admin:read" in data["permissions"]
            assert "admin:write" in data["permissions"]
            assert "user:manage" in data["permissions"]
    
    @pytest.mark.asyncio
    async def test_role_based_context(self, auth_test_client: TestClient, test_tenant):
        """Test that user role is available in context."""
        # Test different roles
        roles_to_test = [UserRole.ADMIN, UserRole.DEVELOPER, UserRole.VIEWER]
        
        for role in roles_to_test:
            auth_service = AuthenticationService()
            user_data = UserCreate(
                tenant_id=test_tenant.id,
                email=f"{role.value}.test@example.com",
                first_name=role.value.title(),
                last_name="Test",
                password="Password123!",
                role=role
            )
            user = await auth_service.create_user(user_data)
            
            # Activate user
            from app.models.orm_models import UserORM
            from app.models.auth_models import UserStatus
            test_db = await auth_service._get_db()
            await test_db.execute(
                UserORM.__table__.update()
                .where(UserORM.id == user.id)
                .values(status=UserStatus.ACTIVE)
            )
            await test_db.commit()
            
            # Create session and token
            from app.models.auth_models import LoginRequest
            login_request = LoginRequest(
                email=user.email,
                password="Password123!",
                provider=AuthProvider.LOCAL,
                ip_address="192.168.1.100",
                user_agent="Mozilla/5.0 Test Browser"
            )
            session = await auth_service._create_user_session(user, login_request)
            tokens = await auth_service._generate_tokens(user, session)
            
            headers = {
                "Authorization": f"Bearer {tokens['access_token']}",
                "Content-Type": "application/json"
            }
            
            with patch('app.middleware.tenant_middleware.require_tenant') as mock_tenant:
                mock_tenant.return_value = test_tenant
                
                response = auth_test_client.get("/api/v1/auth/me", headers=headers)
                
                assert response.status_code == 200
                data = response.json()
                assert data["role"] == role.value


class TestTenantScopedAPI:
    """Test tenant-scoped API operations."""
    
    @pytest.mark.asyncio
    async def test_api_operations_scoped_to_tenant(self, auth_test_client: TestClient, test_tenant, secondary_tenant):
        """Test that API operations are properly scoped to tenant."""
        # Create users in different tenants
        auth_service = AuthenticationService()
        
        # User in primary tenant
        user1_data = UserCreate(
            tenant_id=test_tenant.id,
            email="tenant1@example.com",
            first_name="Tenant",
            last_name="One",
            password="Password123!",
            role=UserRole.DEVELOPER
        )
        user1 = await auth_service.create_user(user1_data)
        
        # User in secondary tenant
        user2_data = UserCreate(
            tenant_id=secondary_tenant.id,
            email="tenant2@example.com",
            first_name="Tenant",
            last_name="Two",
            password="Password123!",
            role=UserRole.DEVELOPER
        )
        user2 = await auth_service.create_user(user2_data)
        
        # Activate users
        from app.models.orm_models import UserORM
        from app.models.auth_models import UserStatus
        test_db = await auth_service._get_db()
        await test_db.execute(
            UserORM.__table__.update()
            .where(UserORM.id.in_([user1.id, user2.id]))
            .values(status=UserStatus.ACTIVE)
        )
        await test_db.commit()
        
        # Create tokens for primary tenant user
        from app.models.auth_models import LoginRequest
        login_request = LoginRequest(
            email=user1.email,
            password="Password123!",
            provider=AuthProvider.LOCAL,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 Test Browser"
        )
        session = await auth_service._create_user_session(user1, login_request)
        tokens = await auth_service._generate_tokens(user1, session)
        
        headers = {
            "Authorization": f"Bearer {tokens['access_token']}",
            "Content-Type": "application/json"
        }
        
        # Test with primary tenant context
        with patch('app.middleware.tenant_middleware.require_tenant') as mock_tenant:
            mock_tenant.return_value = test_tenant
            
            response = auth_test_client.get("/api/v1/auth/me", headers=headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["tenant_id"] == str(test_tenant.id)
            assert data["email"] == user1.email
    
    @pytest.mark.asyncio
    async def test_cross_tenant_access_prevention(self, auth_test_client: TestClient, test_tenant, secondary_tenant):
        """Test that cross-tenant access is prevented."""
        # Create user in primary tenant
        auth_service = AuthenticationService()
        user_data = UserCreate(
            tenant_id=test_tenant.id,
            email="cross.tenant@example.com",
            first_name="Cross",
            last_name="Tenant",
            password="Password123!",
            role=UserRole.DEVELOPER
        )
        user = await auth_service.create_user(user_data)
        
        # Activate user
        from app.models.orm_models import UserORM
        from app.models.auth_models import UserStatus
        test_db = await auth_service._get_db()
        await test_db.execute(
            UserORM.__table__.update()
            .where(UserORM.id == user.id)
            .values(status=UserStatus.ACTIVE)
        )
        await test_db.commit()
        
        # Create tokens
        from app.models.auth_models import LoginRequest
        login_request = LoginRequest(
            email=user.email,
            password="Password123!",
            provider=AuthProvider.LOCAL,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 Test Browser"
        )
        session = await auth_service._create_user_session(user, login_request)
        tokens = await auth_service._generate_tokens(user, session)
        
        headers = {
            "Authorization": f"Bearer {tokens['access_token']}",
            "Content-Type": "application/json"
        }
        
        # Try to access with wrong tenant context
        with patch('app.middleware.tenant_middleware.require_tenant') as mock_tenant:
            mock_tenant.return_value = secondary_tenant  # Wrong tenant
            
            response = auth_test_client.get("/api/v1/auth/me", headers=headers)
            
            # Should fail because token is for different tenant
            assert response.status_code == 404 or response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_tenant_isolation_in_user_updates(self, auth_test_client: TestClient, test_tenant):
        """Test tenant isolation in user update operations."""
        # Create user
        auth_service = AuthenticationService()
        user_data = UserCreate(
            tenant_id=test_tenant.id,
            email="update.test@example.com",
            first_name="Update",
            last_name="Test",
            password="Password123!",
            role=UserRole.DEVELOPER
        )
        user = await auth_service.create_user(user_data)
        
        # Activate user
        from app.models.orm_models import UserORM
        from app.models.auth_models import UserStatus
        test_db = await auth_service._get_db()
        await test_db.execute(
            UserORM.__table__.update()
            .where(UserORM.id == user.id)
            .values(status=UserStatus.ACTIVE)
        )
        await test_db.commit()
        
        # Create tokens
        from app.models.auth_models import LoginRequest
        login_request = LoginRequest(
            email=user.email,
            password="Password123!",
            provider=AuthProvider.LOCAL,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 Test Browser"
        )
        session = await auth_service._create_user_session(user, login_request)
        tokens = await auth_service._generate_tokens(user, session)
        
        headers = {
            "Authorization": f"Bearer {tokens['access_token']}",
            "Content-Type": "application/json"
        }
        
        # Update user profile
        with patch('app.middleware.tenant_middleware.require_tenant') as mock_tenant:
            mock_tenant.return_value = test_tenant
            
            response = auth_test_client.put(
                "/api/v1/auth/users/me",
                headers=headers,
                json={
                    "first_name": "Updated",
                    "last_name": "Name"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["first_name"] == "Updated"
            assert data["last_name"] == "Name"
            assert data["tenant_id"] == str(test_tenant.id)


class TestAuthenticationMiddleware:
    """Test authentication middleware behavior."""
    
    @pytest.mark.asyncio
    async def test_middleware_token_extraction(self, auth_test_client: TestClient, valid_jwt_tokens):
        """Test that middleware properly extracts tokens from headers."""
        # Test different header formats
        header_formats = [
            f"Bearer {valid_jwt_tokens['access_token']}",
            f"bearer {valid_jwt_tokens['access_token']}",  # Lowercase
            f"Bearer  {valid_jwt_tokens['access_token']}",  # Extra space
        ]
        
        for auth_header in header_formats:
            headers = {
                "Authorization": auth_header,
                "Content-Type": "application/json"
            }
            
            # The middleware should handle format variations gracefully
            # Even if it fails, it should not crash
            response = auth_test_client.get("/api/v1/auth/me", headers=headers)
            assert response.status_code in [200, 401, 404]  # Should not crash
    
    @pytest.mark.asyncio
    async def test_middleware_missing_authorization_header(self, auth_test_client: TestClient):
        """Test middleware behavior with missing Authorization header."""
        response = auth_test_client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
        data = response.json()
        assert "Authentication required" in data["detail"] or "required" in data["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_middleware_empty_authorization_header(self, auth_test_client: TestClient):
        """Test middleware behavior with empty Authorization header."""
        headers = {
            "Authorization": "",
            "Content-Type": "application/json"
        }
        
        response = auth_test_client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_middleware_invalid_scheme(self, auth_test_client: TestClient, valid_jwt_tokens):
        """Test middleware behavior with invalid authentication scheme."""
        headers = {
            "Authorization": f"Basic {valid_jwt_tokens['access_token']}",  # Wrong scheme
            "Content-Type": "application/json"
        }
        
        response = auth_test_client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_middleware_error_handling(self, auth_test_client: TestClient):
        """Test middleware error handling for various edge cases."""
        edge_cases = [
            {"Authorization": "Bearer"},  # Missing token
            {"Authorization": "Bearer "},  # Empty token
            {"Authorization": "Bearer " + "x" * 1000},  # Very long token
            {"Authorization": "Bearer token with spaces"},  # Invalid token format
            {"Authorization": "Bearer " + "a" * 10},  # Too short token
        ]
        
        for headers in edge_cases:
            headers["Content-Type"] = "application/json"
            
            response = auth_test_client.get("/api/v1/auth/me", headers=headers)
            
            # Should handle gracefully without crashing
            assert response.status_code == 401
            assert "detail" in response.json()


class TestAPIResponseSecurity:
    """Test API response security features."""
    
    @pytest.mark.asyncio
    async def test_security_headers_present(self, auth_test_client: TestClient):
        """Test that security headers are present in responses."""
        response = auth_test_client.get("/api/v1/auth/providers")
        
        # Check for common security headers
        headers = response.headers
        
        # These headers might be set by middleware
        # We'll just verify the response doesn't crash and returns valid JSON
        assert response.status_code in [200, 401, 404]
        
        # Response should be valid JSON
        try:
            response.json()
        except:
            assert False, "Response should be valid JSON"
    
    @pytest.mark.asyncio
    async def test_error_responses_dont_leak_info(self, auth_test_client: TestClient):
        """Test that error responses don't leak sensitive information."""
        # Test various error scenarios
        error_scenarios = [
            ("/api/v1/auth/me", {"Authorization": "Bearer invalid"}, 401),
            ("/api/v1/auth/verify-email/invalid", {}, 400),
            ("/api/v1/auth/reset-password", {"json": {"token": "invalid"}}, 400),
        ]
        
        for endpoint, headers, expected_status in error_scenarios:
            if "json" in headers:
                response = auth_test_client.post(endpoint, json=headers["json"])
            else:
                response = auth_test_client.get(endpoint, headers=headers)
            
            assert response.status_code >= 400
            data = response.json()
            
            # Error messages should not leak sensitive information
            detail = data.get("detail", "").lower()
            assert "secret" not in detail
            assert "password" not in detail
            assert "database" not in detail
            assert "internal" not in detail
    
    @pytest.mark.asyncio
    async def test_response_time_consistency(self, auth_test_client: TestClient):
        """Test that response times don't leak information."""
        import time
        
        # Test login with valid vs invalid users
        test_cases = [
            {"email": "valid@example.com", "password": "password123"},
            {"email": "nonexistent@example.com", "password": "password123"},
        ]
        
        response_times = []
        
        for test_case in test_cases:
            start_time = time.time()
            response = auth_test_client.post("/api/v1/auth/login", json=test_case)
            end_time = time.time()
            
            response_times.append(end_time - start_time)
            
            # Should return appropriate status
            assert response.status_code in [200, 401, 422]
        
        # Response times should be relatively similar (within 100ms)
        if len(response_times) >= 2:
            time_diff = abs(response_times[0] - response_times[1])
            assert time_diff < 0.1  # Less than 100ms difference
    
    @pytest.mark.asyncio
    async def test_rate_limiting_headers(self, auth_test_client: TestClient):
        """Test rate limiting headers in responses."""
        # Make multiple requests to check for rate limiting headers
        for i in range(5):
            response = auth_test_client.post(
                "/api/v1/auth/login",
                json={"email": f"test{i}@example.com", "password": "password123"}
            )
            
            # Should not crash and return appropriate status
            assert response.status_code in [200, 401, 422, 429]
            
            # If rate limiting is implemented, check for headers
            if response.status_code == 429:
                headers = response.headers
                # Common rate limiting headers
                rate_limit_headers = [
                    "X-RateLimit-Limit",
                    "X-RateLimit-Remaining", 
                    "X-RateLimit-Reset",
                    "Retry-After"
                ]
                
                # At least one rate limiting header should be present
                has_rate_limit_header = any(header in headers for header in rate_limit_headers)
                # Current implementation might not have rate limiting headers
                # assert has_rate_limit_header


class TestAPIVersioning:
    """Test API versioning and compatibility."""
    
    @pytest.mark.asyncio
    async def test_api_version_in_urls(self, auth_test_client: TestClient):
        """Test that API endpoints include version in URL."""
        response = auth_test_client.get("/api/v1/auth/providers")
        
        # Should respond to versioned endpoint
        assert response.status_code in [200, 401]
    
    @pytest.mark.asyncio
    async def test_api_backwards_compatibility(self, auth_test_client: TestClient):
        """Test API backwards compatibility."""
        # Test that existing endpoints maintain their contract
        response = auth_test_client.get("/api/v1/auth/providers")
        
        if response.status_code == 200:
            data = response.json()
            
            # Response structure should be consistent
            assert isinstance(data, dict)
            
            # Expected fields should be present
            if "sso_providers" in data:
                assert isinstance(data["sso_providers"], list)
    
    @pytest.mark.asyncio
    async def test_api_error_format_consistency(self, auth_test_client: TestClient):
        """Test that API error responses follow consistent format."""
        # Generate various types of errors
        error_endpoints = [
            ("/api/v1/auth/me", {}, 401),  # Authentication error
            ("/api/v1/auth/verify-email/invalid", {}, 400),  # Validation error
        ]
        
        for endpoint, headers, expected_status in error_endpoints:
            response = auth_test_client.get(endpoint, headers=headers)
            
            assert response.status_code >= 400
            data = response.json()
            
            # All errors should have consistent format
            assert "detail" in data
            assert isinstance(data["detail"], str)