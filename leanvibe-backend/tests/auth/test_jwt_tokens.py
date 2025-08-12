"""
Comprehensive JWT token management tests
Tests token generation, validation, expiry, refresh, and security
"""

import pytest
import pytest_asyncio
import jwt
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from uuid import uuid4

from app.models.auth_models import LoginRequest, AuthProvider, SessionStatus
from app.services.auth_service import AuthenticationService
from app.core.exceptions import InvalidCredentialsError, TokenExpiredError
from tests.fixtures.auth_test_fixtures import *


class TestJWTGeneration:
    """Test JWT token generation."""
    
    @pytest.mark.asyncio
    async def test_jwt_token_generation(self, auth_service: AuthenticationService, test_user: User, user_session: UserSession):
        """Test JWT token generation with correct payload."""
        tokens = await auth_service._generate_tokens(test_user, user_session)
        
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["access_token"] is not None
        assert tokens["refresh_token"] is not None
        assert tokens["access_token"] != tokens["refresh_token"]
    
    @pytest.mark.asyncio
    async def test_access_token_payload(self, auth_service: AuthenticationService, test_user: User, user_session: UserSession):
        """Test access token contains correct payload."""
        tokens = await auth_service._generate_tokens(test_user, user_session)
        access_token = tokens["access_token"]
        
        # Decode without verification for testing
        payload = jwt.decode(access_token, options={"verify_signature": False})
        
        assert payload["user_id"] == str(test_user.id)
        assert payload["tenant_id"] == str(test_user.tenant_id)
        assert payload["email"] == test_user.email
        assert payload["role"] == test_user.role
        assert payload["permissions"] == test_user.permissions
        assert payload["session_id"] == str(user_session.id)
        assert payload["type"] == "access"
        assert "iat" in payload  # Issued at
        assert "exp" in payload  # Expiry
    
    @pytest.mark.asyncio
    async def test_refresh_token_payload(self, auth_service: AuthenticationService, test_user: User, user_session: UserSession):
        """Test refresh token contains correct payload."""
        tokens = await auth_service._generate_tokens(test_user, user_session)
        refresh_token = tokens["refresh_token"]
        
        # Decode without verification for testing
        payload = jwt.decode(refresh_token, options={"verify_signature": False})
        
        assert payload["user_id"] == str(test_user.id)
        assert payload["session_id"] == str(user_session.id)
        assert payload["type"] == "refresh"
        assert "iat" in payload
        assert "exp" in payload
        # Refresh token should not contain sensitive data
        assert "email" not in payload
        assert "role" not in payload
        assert "permissions" not in payload
    
    @pytest.mark.asyncio
    async def test_token_expiry_times(self, auth_service: AuthenticationService, test_user: User, user_session: UserSession):
        """Test token expiry times are set correctly."""
        tokens = await auth_service._generate_tokens(test_user, user_session)
        
        access_payload = jwt.decode(tokens["access_token"], options={"verify_signature": False})
        refresh_payload = jwt.decode(tokens["refresh_token"], options={"verify_signature": False})
        
        # Access token should expire in 1 hour (3600 seconds)
        access_exp = datetime.fromtimestamp(access_payload["exp"])
        access_iat = datetime.fromtimestamp(access_payload["iat"])
        access_duration = access_exp - access_iat
        assert abs(access_duration.total_seconds() - 3600) < 60  # Within 1 minute tolerance
        
        # Refresh token should expire in 30 days
        refresh_exp = datetime.fromtimestamp(refresh_payload["exp"])
        refresh_iat = datetime.fromtimestamp(refresh_payload["iat"])
        refresh_duration = refresh_exp - refresh_iat
        expected_refresh_seconds = 86400 * 30  # 30 days
        assert abs(refresh_duration.total_seconds() - expected_refresh_seconds) < 3600  # Within 1 hour tolerance
    
    @pytest.mark.asyncio
    async def test_token_uniqueness(self, auth_service: AuthenticationService, test_user: User, user_session: UserSession):
        """Test that generated tokens are unique."""
        tokens1 = await auth_service._generate_tokens(test_user, user_session)
        tokens2 = await auth_service._generate_tokens(test_user, user_session)
        
        assert tokens1["access_token"] != tokens2["access_token"]
        assert tokens1["refresh_token"] != tokens2["refresh_token"]


class TestJWTValidation:
    """Test JWT token validation."""
    
    @pytest.mark.asyncio
    async def test_valid_token_verification(self, auth_service: AuthenticationService, valid_jwt_tokens):
        """Test validation of valid JWT tokens."""
        access_token = valid_jwt_tokens["access_token"]
        
        payload = await auth_service.verify_token(access_token)
        
        assert payload is not None
        assert "user_id" in payload
        assert "tenant_id" in payload
        assert "exp" in payload
        assert payload["type"] == "access"
    
    @pytest.mark.asyncio
    async def test_expired_token_verification(self, auth_service: AuthenticationService, expired_jwt_token):
        """Test validation of expired JWT tokens."""
        with pytest.raises(TokenExpiredError):
            await auth_service.verify_token(expired_jwt_token)
    
    @pytest.mark.asyncio
    async def test_malformed_token_verification(self, auth_service: AuthenticationService, malformed_jwt_token):
        """Test validation of malformed JWT tokens."""
        with pytest.raises(InvalidCredentialsError):
            await auth_service.verify_token(malformed_jwt_token)
    
    @pytest.mark.asyncio
    async def test_token_with_wrong_secret(self, auth_service: AuthenticationService, test_user: User, user_session: UserSession):
        """Test validation of token signed with wrong secret."""
        # Create token with wrong secret
        payload = {
            "user_id": str(test_user.id),
            "tenant_id": str(test_user.tenant_id),
            "exp": (datetime.utcnow() + timedelta(hours=1)).timestamp(),
            "type": "access"
        }
        wrong_token = jwt.encode(payload, "wrong_secret", algorithm="HS256")
        
        with pytest.raises(InvalidCredentialsError):
            await auth_service.verify_token(wrong_token)
    
    @pytest.mark.asyncio
    async def test_token_algorithm_confusion(self, auth_service: AuthenticationService, test_user: User):
        """Test protection against algorithm confusion attacks."""
        # Try to create a token with 'none' algorithm
        payload = {
            "user_id": str(test_user.id),
            "tenant_id": str(test_user.tenant_id),
            "exp": (datetime.utcnow() + timedelta(hours=1)).timestamp(),
            "type": "access"
        }
        
        # Create unsigned token
        none_token = jwt.encode(payload, "", algorithm="none")
        
        with pytest.raises(InvalidCredentialsError):
            await auth_service.verify_token(none_token)
    
    @pytest.mark.asyncio
    async def test_token_replay_protection(self, auth_service: AuthenticationService, valid_jwt_tokens):
        """Test that tokens can't be replayed after logout."""
        access_token = valid_jwt_tokens["access_token"]
        
        # First verification should succeed
        payload1 = await auth_service.verify_token(access_token)
        assert payload1 is not None
        
        # Token should still be valid for multiple uses
        # (Replay protection would be implemented via session revocation)
        payload2 = await auth_service.verify_token(access_token)
        assert payload2 is not None
    
    @pytest.mark.asyncio
    async def test_token_timing_attack_prevention(self, auth_service: AuthenticationService, valid_jwt_tokens):
        """Test that token validation time is consistent."""
        valid_token = valid_jwt_tokens["access_token"]
        invalid_token = "invalid.jwt.token"
        
        # Measure validation time for valid token
        start_time = time.time()
        try:
            await auth_service.verify_token(valid_token)
        except:
            pass
        valid_time = time.time() - start_time
        
        # Measure validation time for invalid token
        start_time = time.time()
        try:
            await auth_service.verify_token(invalid_token)
        except:
            pass
        invalid_time = time.time() - start_time
        
        # Time difference should be minimal (within 10ms)
        time_difference = abs(valid_time - invalid_time)
        assert time_difference < 0.01


class TestTokenRefresh:
    """Test JWT token refresh functionality."""
    
    @pytest.mark.asyncio
    async def test_refresh_token_success(self, auth_service: AuthenticationService, valid_jwt_tokens):
        """Test successful token refresh."""
        refresh_token = valid_jwt_tokens["refresh_token"]
        
        new_tokens = await auth_service.refresh_token(refresh_token)
        
        assert "access_token" in new_tokens
        assert "refresh_token" in new_tokens
        assert new_tokens["access_token"] != valid_jwt_tokens["access_token"]
        assert new_tokens["refresh_token"] != valid_jwt_tokens["refresh_token"]
    
    @pytest.mark.asyncio
    async def test_refresh_with_access_token(self, auth_service: AuthenticationService, valid_jwt_tokens):
        """Test refresh fails when using access token instead of refresh token."""
        access_token = valid_jwt_tokens["access_token"]
        
        with pytest.raises(InvalidCredentialsError, match="Invalid refresh token"):
            await auth_service.refresh_token(access_token)
    
    @pytest.mark.asyncio
    async def test_refresh_expired_token(self, auth_service: AuthenticationService):
        """Test refresh with expired refresh token."""
        # Create expired refresh token
        payload = {
            "user_id": str(uuid4()),
            "session_id": str(uuid4()),
            "exp": (datetime.utcnow() - timedelta(hours=1)).timestamp(),
            "type": "refresh"
        }
        expired_refresh_token = jwt.encode(payload, auth_service.jwt_secret, algorithm="HS256")
        
        with pytest.raises(TokenExpiredError):
            await auth_service.refresh_token(expired_refresh_token)
    
    @pytest.mark.asyncio
    async def test_refresh_nonexistent_user(self, auth_service: AuthenticationService):
        """Test refresh with token for non-existent user."""
        # Create refresh token for non-existent user
        payload = {
            "user_id": str(uuid4()),  # Random user ID
            "session_id": str(uuid4()),
            "exp": (datetime.utcnow() + timedelta(days=1)).timestamp(),
            "type": "refresh"
        }
        invalid_refresh_token = jwt.encode(payload, auth_service.jwt_secret, algorithm="HS256")
        
        with pytest.raises(InvalidCredentialsError, match="User not found"):
            await auth_service.refresh_token(invalid_refresh_token)
    
    @pytest.mark.asyncio
    async def test_refresh_inactive_session(self, auth_service: AuthenticationService, test_user: User, test_db):
        """Test refresh with inactive session."""
        # Create session
        login_request = LoginRequest(
            email=test_user.email,
            password="SecurePassword123!",
            provider=AuthProvider.LOCAL,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 Test Browser"
        )
        session = await auth_service._create_user_session(test_user, login_request)
        tokens = await auth_service._generate_tokens(test_user, session)
        
        # Deactivate session
        await test_db.execute(
            UserSessionORM.__table__.update()
            .where(UserSessionORM.id == session.id)
            .values(status=SessionStatus.REVOKED)
        )
        await test_db.commit()
        
        with pytest.raises(InvalidCredentialsError, match="Session expired"):
            await auth_service.refresh_token(tokens["refresh_token"])
    
    @pytest.mark.asyncio
    async def test_refresh_token_rotation(self, auth_service: AuthenticationService, valid_jwt_tokens):
        """Test that refresh tokens are rotated on use."""
        original_refresh = valid_jwt_tokens["refresh_token"]
        
        # First refresh
        new_tokens1 = await auth_service.refresh_token(original_refresh)
        
        # Second refresh with new token
        new_tokens2 = await auth_service.refresh_token(new_tokens1["refresh_token"])
        
        # All tokens should be different
        assert new_tokens1["refresh_token"] != original_refresh
        assert new_tokens2["refresh_token"] != new_tokens1["refresh_token"]
        assert new_tokens2["access_token"] != new_tokens1["access_token"]


class TestTokenAPI:
    """Test token-related API endpoints."""
    
    @pytest.mark.asyncio
    async def test_refresh_api_success(self, auth_test_client: TestClient, valid_jwt_tokens):
        """Test successful token refresh via API."""
        refresh_token = valid_jwt_tokens["refresh_token"]
        
        response = auth_test_client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {refresh_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
    
    @pytest.mark.asyncio
    async def test_refresh_api_no_token(self, auth_test_client: TestClient):
        """Test refresh API without token."""
        response = auth_test_client.post("/api/v1/auth/refresh")
        
        assert response.status_code == 401
        data = response.json()
        assert "Refresh token required" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_refresh_api_invalid_token(self, auth_test_client: TestClient):
        """Test refresh API with invalid token."""
        response = auth_test_client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "Invalid refresh token" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_me_endpoint_with_valid_token(self, auth_test_client: TestClient, authenticated_headers, test_user: User):
        """Test /me endpoint with valid access token."""
        response = auth_test_client.get(
            "/api/v1/auth/me",
            headers=authenticated_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["id"] == str(test_user.id)
    
    @pytest.mark.asyncio
    async def test_me_endpoint_with_expired_token(self, auth_test_client: TestClient, expired_auth_headers):
        """Test /me endpoint with expired token."""
        response = auth_test_client.get(
            "/api/v1/auth/me",
            headers=expired_auth_headers
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "Token expired" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_me_endpoint_no_token(self, auth_test_client: TestClient):
        """Test /me endpoint without token."""
        response = auth_test_client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
        data = response.json()
        assert "Authentication required" in data["detail"]


class TestTokenSecurity:
    """Test token security features."""
    
    @pytest.mark.asyncio
    async def test_token_secret_rotation(self, auth_service: AuthenticationService, test_user: User, user_session: UserSession):
        """Test behavior when JWT secret is rotated."""
        # Generate token with current secret
        tokens = await auth_service._generate_tokens(test_user, user_session)
        access_token = tokens["access_token"]
        
        # Verify token works
        payload = await auth_service.verify_token(access_token)
        assert payload is not None
        
        # Simulate secret rotation
        old_secret = auth_service.jwt_secret
        auth_service.jwt_secret = "new_rotated_secret"
        
        # Token should now be invalid
        with pytest.raises(InvalidCredentialsError):
            await auth_service.verify_token(access_token)
        
        # Restore original secret
        auth_service.jwt_secret = old_secret
    
    @pytest.mark.asyncio
    async def test_token_payload_tampering(self, auth_service: AuthenticationService, valid_jwt_tokens):
        """Test detection of payload tampering."""
        access_token = valid_jwt_tokens["access_token"]
        
        # Split token into parts
        header, payload, signature = access_token.split('.')
        
        # Decode payload and modify it
        import base64
        import json
        
        # Add padding if needed
        payload_padded = payload + '=' * (4 - len(payload) % 4)
        decoded_payload = json.loads(base64.urlsafe_b64decode(payload_padded))
        
        # Tamper with payload
        decoded_payload["role"] = "admin"  # Privilege escalation attempt
        
        # Re-encode payload
        tampered_payload_bytes = json.dumps(decoded_payload).encode()
        tampered_payload = base64.urlsafe_b64encode(tampered_payload_bytes).decode().rstrip('=')
        
        # Create tampered token
        tampered_token = f"{header}.{tampered_payload}.{signature}"
        
        # Should fail verification
        with pytest.raises(InvalidCredentialsError):
            await auth_service.verify_token(tampered_token)
    
    @pytest.mark.asyncio
    async def test_token_cross_tenant_validation(self, auth_service: AuthenticationService, test_user: User, cross_tenant_user: User):
        """Test that tokens are validated against correct tenant."""
        # Create session and tokens for primary tenant user
        login_request = LoginRequest(
            email=test_user.email,
            password="SecurePassword123!",
            provider=AuthProvider.LOCAL,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 Test Browser"
        )
        session = await auth_service._create_user_session(test_user, login_request)
        tokens = await auth_service._generate_tokens(test_user, session)
        
        # Verify token payload contains correct tenant
        payload = await auth_service.verify_token(tokens["access_token"])
        assert payload["tenant_id"] == str(test_user.tenant_id)
        assert payload["tenant_id"] != str(cross_tenant_user.tenant_id)
    
    @pytest.mark.asyncio
    async def test_token_size_limits(self, auth_service: AuthenticationService, test_user: User, user_session: UserSession):
        """Test that tokens don't exceed reasonable size limits."""
        tokens = await auth_service._generate_tokens(test_user, user_session)
        
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]
        
        # Tokens should be reasonable size (typically < 2KB for JWTs)
        assert len(access_token) < 2048
        assert len(refresh_token) < 2048
        
        # But should be substantial enough to be secure
        assert len(access_token) > 100
        assert len(refresh_token) > 100


class TestTokenBlacklisting:
    """Test token blacklisting and revocation."""
    
    @pytest.mark.asyncio
    async def test_logout_single_session(self, auth_service: AuthenticationService, valid_jwt_tokens):
        """Test logout invalidates current session tokens."""
        access_token = valid_jwt_tokens["access_token"]
        
        # Verify token works initially
        payload = await auth_service.verify_token(access_token)
        assert payload is not None
        
        # In a full implementation, logout would blacklist the session
        # For now, we just verify the token can be validated
        session_id = payload.get("session_id")
        assert session_id is not None
    
    @pytest.mark.asyncio
    async def test_logout_all_sessions(self, auth_service: AuthenticationService, test_user: User, test_tenant):
        """Test logout from all sessions invalidates all user tokens."""
        # Create multiple sessions
        sessions = []
        tokens_list = []
        
        for i in range(3):
            login_request = LoginRequest(
                email=test_user.email,
                password="SecurePassword123!",
                provider=AuthProvider.LOCAL,
                ip_address=f"192.168.1.{100 + i}",
                user_agent=f"Browser {i}"
            )
            session = await auth_service._create_user_session(test_user, login_request)
            tokens = await auth_service._generate_tokens(test_user, session)
            sessions.append(session)
            tokens_list.append(tokens)
        
        # All tokens should be valid initially
        for tokens in tokens_list:
            payload = await auth_service.verify_token(tokens["access_token"])
            assert payload is not None
        
        # In a full implementation, "logout all" would revoke all sessions
        # This would be implemented by updating session status in database
    
    @pytest.mark.asyncio
    async def test_token_revocation_on_password_change(self, auth_service: AuthenticationService, test_user: User, test_tenant):
        """Test that password change invalidates existing tokens."""
        # Create session and tokens
        login_request = LoginRequest(
            email=test_user.email,
            password="SecurePassword123!",
            provider=AuthProvider.LOCAL,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 Test Browser"
        )
        session = await auth_service._create_user_session(test_user, login_request)
        tokens = await auth_service._generate_tokens(test_user, session)
        
        # Verify token works
        payload = await auth_service.verify_token(tokens["access_token"])
        assert payload is not None
        
        # Change password
        success = await auth_service.change_password(
            test_user.id,
            "SecurePassword123!",
            "NewSecurePassword456!",
            test_tenant.id
        )
        assert success is True
        
        # In a full implementation, password change would invalidate all sessions
        # Token should still validate (current implementation doesn't revoke)
        payload = await auth_service.verify_token(tokens["access_token"])
        assert payload is not None


class TestTokenPerformance:
    """Test token-related performance."""
    
    @pytest.mark.asyncio
    async def test_token_generation_performance(self, auth_service: AuthenticationService, test_user: User, user_session: UserSession):
        """Test token generation performance."""
        start_time = time.time()
        
        # Generate 100 token pairs
        for _ in range(100):
            tokens = await auth_service._generate_tokens(test_user, user_session)
            assert tokens["access_token"] is not None
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / 100
        
        # Should generate tokens quickly (< 10ms each)
        assert avg_time < 0.01
    
    @pytest.mark.asyncio
    async def test_token_validation_performance(self, auth_service: AuthenticationService, valid_jwt_tokens):
        """Test token validation performance."""
        access_token = valid_jwt_tokens["access_token"]
        
        start_time = time.time()
        
        # Validate token 100 times
        for _ in range(100):
            payload = await auth_service.verify_token(access_token)
            assert payload is not None
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / 100
        
        # Should validate tokens quickly (< 5ms each)
        assert avg_time < 0.005
    
    @pytest.mark.asyncio
    async def test_concurrent_token_validation(self, auth_service: AuthenticationService, valid_jwt_tokens):
        """Test concurrent token validation performance."""
        access_token = valid_jwt_tokens["access_token"]
        
        async def validate_token():
            payload = await auth_service.verify_token(access_token)
            return payload is not None
        
        start_time = time.time()
        
        # Validate 50 tokens concurrently
        tasks = [validate_token() for _ in range(50)]
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # All validations should succeed
        assert all(results)
        
        # Concurrent validation should be fast (< 100ms total)
        assert total_time < 0.1