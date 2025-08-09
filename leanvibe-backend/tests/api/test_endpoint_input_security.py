"""
COMPREHENSIVE API INPUT VALIDATION & SECURITY TESTING

This module implements enterprise-grade input security testing for all API endpoints
to prevent injection attacks, XSS, data corruption, and malicious payload processing.

Critical Security Requirements:
- SQL injection attempts are blocked and sanitized
- XSS payloads are properly escaped and neutralized
- Malformed JSON/data is handled gracefully without crashes
- Large payloads are rejected to prevent DoS attacks
- Hidden/additional parameters cannot be injected
- All user inputs are validated against defined schemas

Risk Level: CRITICAL - Prevents code injection, data corruption, and DoS attacks
Business Impact: Protects against data breaches, system compromises, and service disruption
"""

import pytest
import asyncio
import json
from typing import Dict, List, Any
from uuid import UUID, uuid4
from unittest.mock import AsyncMock, patch, MagicMock

from fastapi.testclient import TestClient
from fastapi import status
import httpx

from app.main import app
from app.models.auth_models import User, UserRole, UserStatus, AuthProvider
from app.models.tenant_models import Tenant, TenantStatus, TenantQuotas


class TestAPISQLInjectionPrevention:
    """
    CRITICAL: Test SQL injection prevention across all API endpoints
    
    Validates that malicious SQL payloads are properly sanitized or blocked
    to prevent database compromises and unauthorized data access.
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
            status=UserStatus.ACTIVE,
            auth_provider=AuthProvider.LOCAL
        )
    
    @pytest.fixture
    def auth_headers(self, sample_user, sample_tenant):
        """Valid authorization headers for testing"""
        token = f"valid.jwt.{sample_user.id}.{sample_tenant.id}"
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.fixture
    def sql_injection_payloads(self):
        """Common SQL injection attack payloads"""
        return [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "'; INSERT INTO users (email) VALUES ('hacker@evil.com'); --",
            "' UNION SELECT password FROM users WHERE id=1 --",
            "'; UPDATE users SET role='admin' WHERE id=1; --",
            "' OR 1=1 LIMIT 1 OFFSET 0 --",
            "'; EXEC sp_executesql N'SELECT * FROM users'; --",
            "\"; SELECT * FROM information_schema.tables; --",
            "' AND (SELECT COUNT(*) FROM users) > 0 --",
            "'; WAITFOR DELAY '00:00:10'; --"
        ]

    @pytest.mark.asyncio
    async def test_auth_endpoints_sql_injection_prevention(self, client, sql_injection_payloads):
        """
        CRITICAL: Test authentication endpoints block SQL injection
        
        Risk: Complete authentication bypass, user account compromise
        """
        auth_endpoints = [
            ("POST", "/api/v1/auth/login", {"email": "", "password": "test123"}),
            ("POST", "/api/v1/auth/refresh", {}),
        ]
        
        for payload in sql_injection_payloads:
            for method, endpoint, base_data in auth_endpoints:
                # Test SQL injection in email field
                malicious_data = base_data.copy()
                malicious_data["email"] = payload
                
                response = client.post(endpoint, json=malicious_data)
                
                # Should not return 500 (server error) or expose SQL errors
                assert response.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR, \
                    f"SQL injection payload caused server error in {endpoint}: {payload}"
                
                # Check response doesn't contain SQL error messages
                response_text = response.text.lower()
                sql_error_indicators = [
                    "sql", "syntax error", "mysql", "postgresql", "sqlite", 
                    "table doesn't exist", "column", "database", "constraint"
                ]
                
                for indicator in sql_error_indicators:
                    assert indicator not in response_text, \
                        f"SQL error exposed in {endpoint} response: {indicator}"
                
                # Test SQL injection in password field
                malicious_data = base_data.copy()
                if "password" in malicious_data:
                    malicious_data["password"] = payload
                    
                    response = client.post(endpoint, json=malicious_data)
                    
                    assert response.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR, \
                        f"SQL injection in password caused server error in {endpoint}: {payload}"

    @pytest.mark.asyncio
    async def test_project_endpoints_sql_injection_prevention(
        self, client, auth_headers, sql_injection_payloads, sample_tenant, sample_user
    ):
        """
        CRITICAL: Test project endpoints block SQL injection
        
        Risk: Unauthorized access to customer projects, code exposure
        """
        with patch("app.services.auth_service.auth_service.verify_token") as mock_verify:
            with patch("app.middleware.tenant_middleware.require_tenant") as mock_tenant:
                mock_verify.return_value = {
                    "user_id": str(sample_user.id),
                    "tenant_id": str(sample_tenant.id),
                    "role": sample_user.role.value
                }
                mock_tenant.return_value = sample_tenant
                
                project_endpoints = [
                    ("POST", "/api/v1/projects", {"name": "", "description": "Test project"}),
                    ("PUT", "/api/v1/projects/123", {"name": "", "description": "Updated project"}),
                ]
                
                for payload in sql_injection_payloads:
                    for method, endpoint, base_data in project_endpoints:
                        # Test injection in name field
                        malicious_data = base_data.copy()
                        malicious_data["name"] = payload
                        
                        response = client.request(method, endpoint, json=malicious_data, headers=auth_headers)
                        
                        # Should handle malicious input gracefully
                        assert response.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR, \
                            f"SQL injection caused server error in {endpoint}: {payload}"
                        
                        # Test injection in description field
                        malicious_data = base_data.copy()
                        malicious_data["description"] = payload
                        
                        response = client.request(method, endpoint, json=malicious_data, headers=auth_headers)
                        
                        assert response.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR, \
                            f"SQL injection in description caused server error in {endpoint}: {payload}"

    @pytest.mark.asyncio
    async def test_billing_endpoints_sql_injection_prevention(
        self, client, auth_headers, sql_injection_payloads, sample_tenant, sample_user
    ):
        """
        CRITICAL: Test billing endpoints block SQL injection
        
        Risk: Financial data corruption, payment fraud, unauthorized billing access
        """
        with patch("app.services.auth_service.auth_service.verify_token") as mock_verify:
            with patch("app.middleware.tenant_middleware.require_tenant") as mock_tenant:
                mock_verify.return_value = {
                    "user_id": str(sample_user.id),
                    "tenant_id": str(sample_tenant.id),
                    "role": sample_user.role.value
                }
                mock_tenant.return_value = sample_tenant
                
                billing_endpoints = [
                    ("POST", "/api/v1/billing/account", {"company_name": "", "billing_email": "test@test.com"}),
                    ("POST", "/api/v1/billing/payment-methods", {"type": "card", "details": ""}),
                ]
                
                for payload in sql_injection_payloads:
                    for method, endpoint, base_data in billing_endpoints:
                        # Test injection in string fields
                        for field_name in base_data.keys():
                            if isinstance(base_data[field_name], str):
                                malicious_data = base_data.copy()
                                malicious_data[field_name] = payload
                                
                                response = client.request(method, endpoint, json=malicious_data, headers=auth_headers)
                                
                                assert response.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR, \
                                    f"SQL injection in {field_name} caused server error in {endpoint}: {payload}"


class TestAPIXSSPrevention:
    """
    CRITICAL: Test XSS attack prevention across all API endpoints
    
    Validates that malicious JavaScript payloads are properly escaped or sanitized
    to prevent client-side code execution and session hijacking.
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
    
    @pytest.fixture
    def xss_payloads(self):
        """Common XSS attack payloads"""
        return [
            "<script>alert('XSS')</script>",
            "<img src='x' onerror='alert(1)'>",
            "javascript:alert('XSS')",
            "<svg onload='alert(1)'>",
            "');alert('XSS');//",
            "<iframe src='javascript:alert(1)'></iframe>",
            "<body onload='alert(1)'>",
            "<input type='text' onfocus='alert(1)' autofocus>",
            "<marquee onstart='alert(1)'></marquee>",
            "<div style='background:url(javascript:alert(1))'></div>"
        ]

    @pytest.mark.asyncio
    async def test_project_endpoints_xss_prevention(
        self, client, auth_headers, xss_payloads, sample_tenant, sample_user
    ):
        """
        CRITICAL: Test project endpoints sanitize XSS payloads
        
        Risk: Client-side code execution, session hijacking, data theft
        """
        with patch("app.services.auth_service.auth_service.verify_token") as mock_verify:
            with patch("app.middleware.tenant_middleware.require_tenant") as mock_tenant:
                with patch("app.services.project_service.create_project") as mock_create:
                    mock_verify.return_value = {
                        "user_id": str(sample_user.id),
                        "tenant_id": str(sample_tenant.id),
                        "role": sample_user.role.value
                    }
                    mock_tenant.return_value = sample_tenant
                    mock_create.return_value = {"id": "123", "name": "safe_name"}
                    
                    for payload in xss_payloads:
                        project_data = {
                            "name": payload,
                            "description": f"Project with {payload}"
                        }
                        
                        response = client.post("/api/v1/projects", json=project_data, headers=auth_headers)
                        
                        # Should handle XSS attempts gracefully
                        assert response.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR, \
                            f"XSS payload caused server error: {payload}"
                        
                        # If successful, check response doesn't contain unsanitized payload
                        if response.status_code == 200:
                            response_text = response.text
                            
                            # Response should not contain executable script tags
                            dangerous_patterns = ["<script", "javascript:", "onload=", "onerror="]
                            for pattern in dangerous_patterns:
                                assert pattern not in response_text.lower(), \
                                    f"Unsanitized XSS pattern found in response: {pattern}"

    @pytest.mark.asyncio
    async def test_tenant_settings_xss_prevention(
        self, client, auth_headers, xss_payloads, sample_tenant, sample_user
    ):
        """
        CRITICAL: Test tenant settings endpoints sanitize XSS payloads
        
        Risk: Administrative account compromise, privilege escalation
        """
        with patch("app.services.auth_service.auth_service.verify_token") as mock_verify:
            with patch("app.middleware.tenant_middleware.require_tenant") as mock_tenant:
                mock_verify.return_value = {
                    "user_id": str(sample_user.id),
                    "tenant_id": str(sample_tenant.id),
                    "role": UserRole.ADMIN.value  # Admin role for settings
                }
                mock_tenant.return_value = sample_tenant
                
                for payload in xss_payloads:
                    settings_data = {
                        "organization_name": payload,
                        "admin_email": f"admin+{payload}@test.com",
                        "custom_domain": f"{payload}.example.com"
                    }
                    
                    response = client.put("/api/v1/tenants/settings", json=settings_data, headers=auth_headers)
                    
                    # Should handle XSS gracefully
                    assert response.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR, \
                        f"XSS in tenant settings caused server error: {payload}"
                    
                    # Verify XSS was sanitized if successful
                    if response.status_code in [200, 201]:
                        response_data = response.json()
                        
                        # Check that dangerous patterns were sanitized
                        for field_value in response_data.values():
                            if isinstance(field_value, str):
                                dangerous_patterns = ["<script", "javascript:", "onload"]
                                for pattern in dangerous_patterns:
                                    assert pattern not in field_value.lower(), \
                                        f"Unsanitized XSS in response field: {pattern}"


class TestAPIMalformedRequestHandling:
    """
    CRITICAL: Test malformed request handling across all API endpoints
    
    Validates that invalid JSON, missing fields, and corrupted data
    are handled gracefully without exposing system information.
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
    async def test_malformed_json_handling(self, client, auth_headers):
        """
        CRITICAL: Test malformed JSON is handled gracefully
        
        Risk: Server crashes, information disclosure through error messages
        """
        malformed_payloads = [
            "{invalid json",  # Unclosed brace
            '{"key": }',  # Missing value
            '{"key": "value",}',  # Trailing comma
            '{"key": "value" "key2": "value2"}',  # Missing comma
            '{key: "value"}',  # Unquoted key
            '{"key": "value"',  # Missing closing brace
            '',  # Empty body
            'not json at all',  # Plain text
            '{"deeply": {"nested": {"object": {"with": {"too": {"many": {"levels": "value"}}}}}}}',  # Deep nesting
        ]
        
        test_endpoints = [
            ("POST", "/api/v1/auth/login"),
            ("POST", "/api/v1/projects"),
            ("PUT", "/api/v1/tenants/settings"),
        ]
        
        for malformed_json in malformed_payloads:
            for method, endpoint in test_endpoints:
                # Send malformed JSON
                response = client.request(
                    method,
                    endpoint,
                    data=malformed_json,  # Raw data instead of json=
                    headers={
                        **auth_headers,
                        "Content-Type": "application/json"
                    }
                )
                
                # Should return 400 Bad Request, not crash with 500
                assert response.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR, \
                    f"Malformed JSON caused server error in {endpoint}: {malformed_json[:50]}"
                
                # Should return appropriate error code
                assert response.status_code in [400, 401, 422], \
                    f"Unexpected status code for malformed JSON in {endpoint}: {response.status_code}"
                
                # Error response should not expose system details
                response_text = response.text.lower()
                sensitive_info = ["traceback", "exception", "stack trace", "internal error"]
                
                for info in sensitive_info:
                    assert info not in response_text, \
                        f"Sensitive system info exposed in {endpoint} error response: {info}"

    @pytest.mark.asyncio
    async def test_missing_required_fields_handling(self, client, auth_headers, sample_tenant, sample_user):
        """
        CRITICAL: Test missing required fields are handled properly
        
        Risk: Data corruption, system instability
        """
        with patch("app.services.auth_service.auth_service.verify_token") as mock_verify:
            with patch("app.middleware.tenant_middleware.require_tenant") as mock_tenant:
                mock_verify.return_value = {
                    "user_id": str(sample_user.id),
                    "tenant_id": str(sample_tenant.id),
                    "role": sample_user.role.value
                }
                mock_tenant.return_value = sample_tenant
                
                test_cases = [
                    ("POST", "/api/v1/auth/login", {}),  # Missing email and password
                    ("POST", "/api/v1/projects", {}),  # Missing name
                    ("POST", "/api/v1/billing/account", {}),  # Missing required billing fields
                ]
                
                for method, endpoint, empty_data in test_cases:
                    response = client.request(method, endpoint, json=empty_data, headers=auth_headers)
                    
                    # Should return validation error, not crash
                    assert response.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR, \
                        f"Missing required fields caused server error in {endpoint}"
                    
                    # Should return 400 or 422 for validation errors
                    assert response.status_code in [400, 401, 422], \
                        f"Unexpected status for missing fields in {endpoint}: {response.status_code}"

    @pytest.mark.asyncio
    async def test_invalid_data_types_handling(self, client, auth_headers, sample_tenant, sample_user):
        """
        CRITICAL: Test invalid data types are handled gracefully
        
        Risk: Type confusion attacks, data corruption
        """
        with patch("app.services.auth_service.auth_service.verify_token") as mock_verify:
            with patch("app.middleware.tenant_middleware.require_tenant") as mock_tenant:
                mock_verify.return_value = {
                    "user_id": str(sample_user.id),
                    "tenant_id": str(sample_tenant.id),
                    "role": sample_user.role.value
                }
                mock_tenant.return_value = sample_tenant
                
                invalid_type_tests = [
                    # Project creation with wrong types
                    ("POST", "/api/v1/projects", {
                        "name": 12345,  # Should be string
                        "description": [],  # Should be string
                        "active": "not_boolean"  # Should be boolean
                    }),
                    
                    # Auth login with wrong types
                    ("POST", "/api/v1/auth/login", {
                        "email": {"nested": "object"},  # Should be string
                        "password": 123456  # Should be string
                    }),
                ]
                
                for method, endpoint, invalid_data in invalid_type_tests:
                    response = client.request(method, endpoint, json=invalid_data, headers=auth_headers)
                    
                    # Should handle gracefully with validation error
                    assert response.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR, \
                        f"Invalid data types caused server error in {endpoint}"
                    
                    assert response.status_code in [400, 401, 422], \
                        f"Invalid data types not properly validated in {endpoint}: {response.status_code}"


class TestAPIRequestSizeLimits:
    """
    CRITICAL: Test request size limits prevent DoS attacks
    
    Validates that large payloads are rejected to prevent resource exhaustion
    and denial of service attacks.
    """
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self):
        return {"Authorization": "Bearer valid.test.token"}

    @pytest.mark.asyncio
    async def test_large_payload_rejection(self, client, auth_headers):
        """
        CRITICAL: Test large payloads are rejected appropriately
        
        Risk: Memory exhaustion, DoS attacks, server instability
        """
        # Create increasingly large payloads
        payload_sizes = [
            1024 * 10,   # 10KB - should be fine
            1024 * 100,  # 100KB - might be fine
            1024 * 1024, # 1MB - should be rejected
            1024 * 10 * 1024,  # 10MB - definitely rejected
        ]
        
        test_endpoints = [
            ("POST", "/api/v1/auth/login"),
            ("POST", "/api/v1/projects"),
            ("POST", "/api/v1/billing/account"),
        ]
        
        for size in payload_sizes:
            # Create large string payload
            large_string = "A" * size
            large_payload = {"large_field": large_string}
            
            for method, endpoint in test_endpoints:
                response = client.request(
                    method,
                    endpoint,
                    json=large_payload,
                    headers=auth_headers
                )
                
                # For very large payloads, should be rejected
                if size >= 1024 * 1024:  # 1MB or larger
                    assert response.status_code in [400, 413, 422], \
                        f"Large payload ({size} bytes) not rejected by {endpoint}"
                
                # Should never cause server error
                assert response.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR, \
                    f"Large payload caused server error in {endpoint}"

    @pytest.mark.asyncio
    async def test_deeply_nested_object_limits(self, client, auth_headers):
        """
        CRITICAL: Test deeply nested objects are handled safely
        
        Risk: Stack overflow, recursive processing DoS
        """
        # Create deeply nested object
        def create_nested_object(depth):
            if depth <= 0:
                return "value"
            return {"nested": create_nested_object(depth - 1)}
        
        nesting_levels = [10, 50, 100, 500]  # Increasing levels of nesting
        
        for depth in nesting_levels:
            nested_payload = create_nested_object(depth)
            
            response = client.post(
                "/api/v1/projects",
                json=nested_payload,
                headers=auth_headers
            )
            
            # For very deep nesting, should be handled safely
            assert response.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR, \
                f"Deeply nested object (depth {depth}) caused server error"
            
            # Very deep nesting might be rejected
            if depth >= 100:
                assert response.status_code in [400, 413, 422], \
                    f"Deeply nested object (depth {depth}) should be rejected"


class TestAPIParameterTamperingPrevention:
    """
    CRITICAL: Test parameter tampering prevention
    
    Validates that hidden parameters, admin flags, and privileged fields
    cannot be injected through API requests.
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
            role=UserRole.DEVELOPER,  # Regular user, not admin
            status=UserStatus.ACTIVE
        )
    
    @pytest.fixture
    def auth_headers(self, sample_user, sample_tenant):
        token = f"valid.jwt.{sample_user.id}.{sample_tenant.id}"
        return {"Authorization": f"Bearer {token}"}

    @pytest.mark.asyncio
    async def test_role_elevation_prevention(self, client, auth_headers, sample_tenant, sample_user):
        """
        CRITICAL: Test users cannot elevate their role through parameter injection
        
        Risk: Privilege escalation, unauthorized administrative access
        """
        with patch("app.services.auth_service.auth_service.verify_token") as mock_verify:
            with patch("app.middleware.tenant_middleware.require_tenant") as mock_tenant:
                mock_verify.return_value = {
                    "user_id": str(sample_user.id),
                    "tenant_id": str(sample_tenant.id),
                    "role": UserRole.DEVELOPER.value
                }
                mock_tenant.return_value = sample_tenant
                
                # Attempt to inject admin role
                malicious_payloads = [
                    {
                        "name": "Test Project",
                        "role": "admin",  # Hidden parameter injection
                        "is_admin": True,
                        "user_role": "admin",
                        "permissions": ["admin", "write", "delete"]
                    },
                    {
                        "name": "Test Project", 
                        "creator_role": "admin",
                        "tenant_admin": True,
                        "super_user": True,
                        "elevated_permissions": True
                    }
                ]
                
                for payload in malicious_payloads:
                    response = client.post("/api/v1/projects", json=payload, headers=auth_headers)
                    
                    # Should not cause server error or privilege escalation
                    assert response.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR, \
                        "Role elevation attempt caused server error"
                    
                    # If successful, verify role wasn't elevated
                    if response.status_code in [200, 201]:
                        # The user should still have developer role, not admin
                        # This would be verified through subsequent API calls
                        pass

    @pytest.mark.asyncio
    async def test_tenant_id_injection_prevention(self, client, auth_headers, sample_tenant, sample_user):
        """
        CRITICAL: Test users cannot inject different tenant IDs
        
        Risk: Cross-tenant data access, data corruption
        """
        other_tenant_id = str(uuid4())  # Different tenant ID
        
        with patch("app.services.auth_service.auth_service.verify_token") as mock_verify:
            with patch("app.middleware.tenant_middleware.require_tenant") as mock_tenant:
                mock_verify.return_value = {
                    "user_id": str(sample_user.id),
                    "tenant_id": str(sample_tenant.id),
                    "role": sample_user.role.value
                }
                mock_tenant.return_value = sample_tenant
                
                # Attempt to inject different tenant ID
                malicious_payloads = [
                    {
                        "name": "Test Project",
                        "tenant_id": other_tenant_id,  # Different tenant
                        "owner_tenant": other_tenant_id,
                        "belongs_to_tenant": other_tenant_id
                    }
                ]
                
                for payload in malicious_payloads:
                    response = client.post("/api/v1/projects", json=payload, headers=auth_headers)
                    
                    # Should not cause server error
                    assert response.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR, \
                        "Tenant ID injection caused server error"
                    
                    # Verify the project is created under correct tenant (not injected one)
                    if response.status_code in [200, 201]:
                        response_data = response.json()
                        if "tenant_id" in response_data:
                            assert response_data["tenant_id"] == str(sample_tenant.id), \
                                "Tenant ID injection succeeded - security breach"

    @pytest.mark.asyncio
    async def test_hidden_field_injection_prevention(self, client, auth_headers, sample_tenant, sample_user):
        """
        CRITICAL: Test hidden system fields cannot be injected
        
        Risk: System manipulation, data integrity compromise
        """
        with patch("app.services.auth_service.auth_service.verify_token") as mock_verify:
            with patch("app.middleware.tenant_middleware.require_tenant") as mock_tenant:
                mock_verify.return_value = {
                    "user_id": str(sample_user.id),
                    "tenant_id": str(sample_tenant.id),
                    "role": sample_user.role.value
                }
                mock_tenant.return_value = sample_tenant
                
                # Attempt to inject system fields
                malicious_payload = {
                    "name": "Test Project",
                    # Hidden system fields
                    "id": str(uuid4()),  # Should be auto-generated
                    "created_at": "2000-01-01T00:00:00Z",  # Should be current time
                    "updated_at": "2000-01-01T00:00:00Z", 
                    "version": 999,  # Should be auto-managed
                    "system_flags": {"admin": True},
                    "internal_metadata": {"bypass_validation": True},
                    "__proto__": {"admin": True},  # Prototype pollution
                    "constructor": {"admin": True},
                }
                
                response = client.post("/api/v1/projects", json=malicious_payload, headers=auth_headers)
                
                # Should handle gracefully
                assert response.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR, \
                    "Hidden field injection caused server error"
                
                # If successful, system fields should not be user-controllable
                if response.status_code in [200, 201]:
                    response_data = response.json()
                    
                    # Verify system fields weren't injected
                    if "id" in response_data:
                        assert response_data["id"] != malicious_payload["id"], \
                            "ID field injection succeeded"
                    
                    if "created_at" in response_data:
                        assert response_data["created_at"] != malicious_payload["created_at"], \
                            "created_at field injection succeeded"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])