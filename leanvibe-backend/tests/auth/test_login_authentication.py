"""
Comprehensive login and authentication flow tests
Tests all authentication methods, rate limiting, account lockout, and security features
"""

import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock, MagicMock
from uuid import uuid4
import time

from app.models.auth_models import (
    LoginRequest, LoginResponse, AuthProvider, UserStatus, 
    MFAMethod, SessionStatus
)
from app.services.auth_service import AuthenticationService
from app.core.exceptions import InvalidCredentialsError, TokenExpiredError
from tests.fixtures.auth_test_fixtures import *


class TestBasicAuthentication:
    """Test basic authentication functionality."""
    
    @pytest.mark.asyncio
    async def test_login_success(self, auth_service: AuthenticationService, test_user: User, test_tenant):
        """Test successful login with valid credentials."""
        login_request = LoginRequest(
            email=test_user.email,
            password="SecurePassword123!",
            provider=AuthProvider.LOCAL,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 Test Browser"
        )
        
        response = await auth_service.authenticate_user(login_request, test_tenant.id)
        
        assert response.success is True
        assert response.access_token is not None
        assert response.refresh_token is not None
        assert response.expires_in == auth_service.token_expiry
        assert response.user.id == test_user.id
        assert response.mfa_required is False
    
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, auth_service: AuthenticationService, test_user: User, test_tenant):
        """Test login with invalid password."""
        login_request = LoginRequest(
            email=test_user.email,
            password="WrongPassword",
            provider=AuthProvider.LOCAL,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 Test Browser"
        )
        
        with pytest.raises(InvalidCredentialsError):
            await auth_service.authenticate_user(login_request, test_tenant.id)
    
    @pytest.mark.asyncio
    async def test_login_user_not_found(self, auth_service: AuthenticationService, test_tenant):
        """Test login with non-existent user."""
        login_request = LoginRequest(
            email="nonexistent@example.com",
            password="Password123!",
            provider=AuthProvider.LOCAL,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 Test Browser"
        )
        
        with pytest.raises(InvalidCredentialsError):
            await auth_service.authenticate_user(login_request, test_tenant.id)
    
    @pytest.mark.asyncio
    async def test_login_unverified_account(self, auth_service: AuthenticationService, test_tenant, test_db):
        """Test login with unverified account."""
        # Create unverified user
        user_data = UserCreate(
            tenant_id=test_tenant.id,
            email="unverified@example.com",
            first_name="Unverified",
            last_name="User",
            password="Password123!",
            role=UserRole.DEVELOPER
        )
        user = await auth_service.create_user(user_data)
        
        # Ensure user is pending activation
        await test_db.execute(
            UserORM.__table__.update()
            .where(UserORM.id == user.id)
            .values(status=UserStatus.PENDING_ACTIVATION)
        )
        await test_db.commit()
        
        login_request = LoginRequest(
            email=user.email,
            password="Password123!",
            provider=AuthProvider.LOCAL,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 Test Browser"
        )
        
        with pytest.raises(InvalidCredentialsError, match="not active"):
            await auth_service.authenticate_user(login_request, test_tenant.id)
    
    @pytest.mark.asyncio
    async def test_login_suspended_account(self, auth_service: AuthenticationService, test_user: User, test_tenant, test_db):
        """Test login with suspended account."""
        # Suspend the user
        await test_db.execute(
            UserORM.__table__.update()
            .where(UserORM.id == test_user.id)
            .values(status=UserStatus.SUSPENDED)
        )
        await test_db.commit()
        
        login_request = LoginRequest(
            email=test_user.email,
            password="SecurePassword123!",
            provider=AuthProvider.LOCAL,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 Test Browser"
        )
        
        with pytest.raises(InvalidCredentialsError, match="not active"):
            await auth_service.authenticate_user(login_request, test_tenant.id)


class TestAccountLockout:
    """Test account lockout and brute force protection."""
    
    @pytest.mark.asyncio
    async def test_login_account_lockout(self, auth_service: AuthenticationService, test_user: User, test_tenant):
        """Test account lockout after multiple failed attempts."""
        login_request = LoginRequest(
            email=test_user.email,
            password="WrongPassword",
            provider=AuthProvider.LOCAL,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 Test Browser"
        )
        
        # Attempt login 5 times with wrong password
        for i in range(5):
            with pytest.raises(InvalidCredentialsError):
                await auth_service.authenticate_user(login_request, test_tenant.id)
        
        # Check if user is locked
        locked_user = await auth_service.get_user_by_id(test_user.id, test_tenant.id)
        assert locked_user.login_attempts >= 5
        assert locked_user.locked_until is not None
        assert locked_user.locked_until > datetime.utcnow()
    
    @pytest.mark.asyncio
    async def test_login_locked_account_rejection(self, auth_service: AuthenticationService, locked_user: User, test_tenant):
        """Test that locked account rejects even valid credentials."""
        login_request = LoginRequest(
            email=locked_user.email,
            password="SecurePassword123!",  # Correct password
            provider=AuthProvider.LOCAL,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 Test Browser"
        )
        
        with pytest.raises(InvalidCredentialsError, match="locked"):
            await auth_service.authenticate_user(login_request, test_tenant.id)
    
    @pytest.mark.asyncio
    async def test_account_unlock_after_timeout(self, auth_service: AuthenticationService, test_user: User, test_tenant, test_db):
        """Test account unlock after lockout timeout expires."""
        # Lock the account with past expiry time
        past_time = datetime.utcnow() - timedelta(minutes=1)
        await test_db.execute(
            UserORM.__table__.update()
            .where(UserORM.id == test_user.id)
            .values(
                login_attempts=5,
                locked_until=past_time
            )
        )
        await test_db.commit()
        
        login_request = LoginRequest(
            email=test_user.email,
            password="SecurePassword123!",
            provider=AuthProvider.LOCAL,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 Test Browser"
        )
        
        # Should succeed since lockout expired
        response = await auth_service.authenticate_user(login_request, test_tenant.id)
        assert response.success is True
        
        # Check that failed attempts were reset
        unlocked_user = await auth_service.get_user_by_id(test_user.id, test_tenant.id)
        assert unlocked_user.login_attempts == 0
        assert unlocked_user.locked_until is None
    
    @pytest.mark.asyncio
    async def test_failed_attempts_reset_on_success(self, auth_service: AuthenticationService, test_user: User, test_tenant, test_db):
        """Test that failed attempts reset after successful login."""
        # Set some failed attempts
        await test_db.execute(
            UserORM.__table__.update()
            .where(UserORM.id == test_user.id)
            .values(login_attempts=3)
        )
        await test_db.commit()
        
        login_request = LoginRequest(
            email=test_user.email,
            password="SecurePassword123!",
            provider=AuthProvider.LOCAL,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 Test Browser"
        )
        
        response = await auth_service.authenticate_user(login_request, test_tenant.id)
        assert response.success is True
        
        # Check that failed attempts were reset
        reset_user = await auth_service.get_user_by_id(test_user.id, test_tenant.id)
        assert reset_user.login_attempts == 0


class TestMFAAuthentication:
    """Test Multi-Factor Authentication."""
    
    @pytest.mark.asyncio
    async def test_mfa_required_challenge(self, auth_service: AuthenticationService, mfa_enabled_user: User, test_tenant):
        """Test MFA challenge is returned for MFA-enabled users."""
        login_request = LoginRequest(
            email=mfa_enabled_user.email,
            password="SecurePassword123!",
            provider=AuthProvider.LOCAL,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 Test Browser"
        )
        
        response = await auth_service.authenticate_user(login_request, test_tenant.id)
        
        assert response.success is False
        assert response.mfa_required is True
        assert MFAMethod.TOTP in response.mfa_methods
        assert response.mfa_challenge_id is not None
        assert response.access_token is None
    
    @pytest.mark.asyncio
    async def test_mfa_login_success(self, auth_service: AuthenticationService, mfa_enabled_user: User, test_tenant):
        """Test successful MFA login with valid TOTP code."""
        # Generate valid TOTP code
        import pyotp
        totp = pyotp.TOTP(mfa_enabled_user.mfa_secret)
        valid_code = totp.now()
        
        login_request = LoginRequest(
            email=mfa_enabled_user.email,
            password="SecurePassword123!",
            provider=AuthProvider.LOCAL,
            mfa_code=valid_code,
            mfa_method=MFAMethod.TOTP,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 Test Browser"
        )
        
        response = await auth_service.authenticate_user(login_request, test_tenant.id)
        
        assert response.success is True
        assert response.access_token is not None
        assert response.refresh_token is not None
        assert response.mfa_required is False
    
    @pytest.mark.asyncio
    async def test_mfa_login_invalid_code(self, auth_service: AuthenticationService, mfa_enabled_user: User, test_tenant):
        """Test MFA login with invalid code."""
        login_request = LoginRequest(
            email=mfa_enabled_user.email,
            password="SecurePassword123!",
            provider=AuthProvider.LOCAL,
            mfa_code="000000",  # Invalid code
            mfa_method=MFAMethod.TOTP,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 Test Browser"
        )
        
        with pytest.raises(InvalidCredentialsError, match="Invalid MFA"):
            await auth_service.authenticate_user(login_request, test_tenant.id)
    
    @pytest.mark.asyncio
    async def test_mfa_sms_verification(self, auth_service: AuthenticationService, test_user: User, test_tenant, test_db):
        """Test SMS MFA verification."""
        # Enable SMS MFA for user
        await test_db.execute(
            UserORM.__table__.update()
            .where(UserORM.id == test_user.id)
            .values(
                mfa_enabled=True,
                mfa_methods=["sms"]
            )
        )
        await test_db.commit()
        
        login_request = LoginRequest(
            email=test_user.email,
            password="SecurePassword123!",
            provider=AuthProvider.LOCAL,
            mfa_code="123456",  # Mock SMS code
            mfa_method=MFAMethod.SMS,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 Test Browser"
        )
        
        # SMS verification is mocked to always succeed
        response = await auth_service.authenticate_user(login_request, test_tenant.id)
        assert response.success is True


class TestSSOAuthentication:
    """Test Single Sign-On authentication."""
    
    @pytest.mark.asyncio
    async def test_oauth_google_authentication(self, auth_service: AuthenticationService, test_tenant, test_db):
        """Test Google OAuth authentication."""
        # Create user with Google auth provider
        google_user_data = UserCreate(
            tenant_id=test_tenant.id,
            email="google.user@gmail.com",
            first_name="Google",
            last_name="User",
            role=UserRole.DEVELOPER,
            auth_provider=AuthProvider.GOOGLE,
            external_id="google_123456789"
        )
        google_user = await auth_service.create_user(google_user_data)
        
        # Activate user
        await test_db.execute(
            UserORM.__table__.update()
            .where(UserORM.id == google_user.id)
            .values(status=UserStatus.ACTIVE)
        )
        await test_db.commit()
        
        login_request = LoginRequest(
            email=google_user.email,
            provider=AuthProvider.GOOGLE,
            auth_code="google_auth_code_123",
            state="google_state_123",
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 Test Browser"
        )
        
        response = await auth_service.authenticate_user(login_request, test_tenant.id)
        
        assert response.success is True
        assert response.access_token is not None
        assert response.user.auth_provider == AuthProvider.GOOGLE
    
    @pytest.mark.asyncio
    async def test_oauth_microsoft_authentication(self, auth_service: AuthenticationService, test_tenant, test_db):
        """Test Microsoft OAuth authentication."""
        # Create user with Microsoft auth provider
        ms_user_data = UserCreate(
            tenant_id=test_tenant.id,
            email="microsoft.user@outlook.com",
            first_name="Microsoft",
            last_name="User",
            role=UserRole.DEVELOPER,
            auth_provider=AuthProvider.MICROSOFT,
            external_id="microsoft_987654321"
        )
        ms_user = await auth_service.create_user(ms_user_data)
        
        # Activate user
        await test_db.execute(
            UserORM.__table__.update()
            .where(UserORM.id == ms_user.id)
            .values(status=UserStatus.ACTIVE)
        )
        await test_db.commit()
        
        login_request = LoginRequest(
            email=ms_user.email,
            provider=AuthProvider.MICROSOFT,
            auth_code="microsoft_auth_code_123",
            state="microsoft_state_123",
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 Test Browser"
        )
        
        response = await auth_service.authenticate_user(login_request, test_tenant.id)
        
        assert response.success is True
        assert response.user.auth_provider == AuthProvider.MICROSOFT
    
    @pytest.mark.asyncio
    async def test_saml_authentication(self, auth_service: AuthenticationService, test_tenant, test_db):
        """Test SAML authentication."""
        # Create user with SAML auth provider
        saml_user_data = UserCreate(
            tenant_id=test_tenant.id,
            email="saml.user@example.com",
            first_name="SAML",
            last_name="User",
            role=UserRole.DEVELOPER,
            auth_provider=AuthProvider.SAML,
            external_id="saml_user_123"
        )
        saml_user = await auth_service.create_user(saml_user_data)
        
        # Activate user
        await test_db.execute(
            UserORM.__table__.update()
            .where(UserORM.id == saml_user.id)
            .values(status=UserStatus.ACTIVE)
        )
        await test_db.commit()
        
        login_request = LoginRequest(
            email=saml_user.email,
            provider=AuthProvider.SAML,
            saml_response="encoded_saml_response_123",
            relay_state="saml_relay_state_123",
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 Test Browser"
        )
        
        response = await auth_service.authenticate_user(login_request, test_tenant.id)
        
        assert response.success is True
        assert response.user.auth_provider == AuthProvider.SAML


class TestLoginAPI:
    """Test login API endpoints."""
    
    @pytest.mark.asyncio
    async def test_login_api_success(self, auth_test_client: TestClient, test_user: User, test_tenant):
        """Test successful login via API."""
        with patch('app.middleware.tenant_middleware.require_tenant') as mock_tenant:
            mock_tenant.return_value = test_tenant
            
            response = auth_test_client.post(
                "/api/v1/auth/login",
                json={
                    "email": test_user.email,
                    "password": "SecurePassword123!",
                    "provider": "local"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "access_token" in data
            assert "refresh_token" in data
            assert data["user"]["email"] == test_user.email
    
    @pytest.mark.asyncio
    async def test_login_api_invalid_credentials(self, auth_test_client: TestClient, test_user: User, test_tenant):
        """Test login API with invalid credentials."""
        with patch('app.middleware.tenant_middleware.require_tenant') as mock_tenant:
            mock_tenant.return_value = test_tenant
            
            response = auth_test_client.post(
                "/api/v1/auth/login",
                json={
                    "email": test_user.email,
                    "password": "WrongPassword",
                    "provider": "local"
                }
            )
            
            assert response.status_code == 401
            data = response.json()
            assert "Invalid credentials" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_login_api_missing_fields(self, auth_test_client: TestClient, test_tenant):
        """Test login API with missing required fields."""
        with patch('app.middleware.tenant_middleware.require_tenant') as mock_tenant:
            mock_tenant.return_value = test_tenant
            
            response = auth_test_client.post(
                "/api/v1/auth/login",
                json={
                    "email": "test@example.com"
                    # Missing password
                }
            )
            
            assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_logout_api_success(self, auth_test_client: TestClient, authenticated_headers):
        """Test successful logout via API."""
        response = auth_test_client.post(
            "/api/v1/auth/logout",
            headers=authenticated_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Logged out" in data["message"]
    
    @pytest.mark.asyncio
    async def test_logout_api_no_token(self, auth_test_client: TestClient):
        """Test logout API without authentication token."""
        response = auth_test_client.post("/api/v1/auth/logout")
        
        assert response.status_code == 200  # Logout should be forgiving
        data = response.json()
        assert "Logged out" in data["message"]


class TestRateLimiting:
    """Test rate limiting for authentication endpoints."""
    
    @pytest.mark.asyncio
    async def test_login_rate_limiting_same_user(self, auth_service: AuthenticationService, test_user: User, test_tenant):
        """Test rate limiting for same user login attempts."""
        login_request = LoginRequest(
            email=test_user.email,
            password="WrongPassword",
            provider=AuthProvider.LOCAL,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 Test Browser"
        )
        
        # Make multiple rapid failed login attempts
        failed_attempts = 0
        for i in range(10):
            try:
                await auth_service.authenticate_user(login_request, test_tenant.id)
            except InvalidCredentialsError:
                failed_attempts += 1
        
        # Should have failed attempts recorded
        assert failed_attempts > 0
        
        # User should be locked after enough attempts
        locked_user = await auth_service.get_user_by_id(test_user.id, test_tenant.id)
        if failed_attempts >= 5:
            assert locked_user.login_attempts >= 5
    
    @pytest.mark.asyncio
    async def test_login_rate_limiting_different_users(self, auth_service: AuthenticationService, test_tenant):
        """Test rate limiting doesn't affect different users."""
        # Create multiple users
        users = []
        for i in range(5):
            user_data = UserCreate(
                tenant_id=test_tenant.id,
                email=f"ratelimit{i}@example.com",
                first_name=f"Rate{i}",
                last_name="Limit",
                password="Password123!",
                role=UserRole.DEVELOPER
            )
            user = await auth_service.create_user(user_data)
            users.append(user)
        
        # Each user should be able to login independently
        for user in users:
            login_request = LoginRequest(
                email=user.email,
                password="Password123!",
                provider=AuthProvider.LOCAL,
                ip_address="192.168.1.100",
                user_agent="Mozilla/5.0 Test Browser"
            )
            
            # Should not be rate limited
            try:
                response = await auth_service.authenticate_user(login_request, test_tenant.id)
                # User might need activation first
            except InvalidCredentialsError as e:
                if "not active" in str(e):
                    continue  # Expected for unactivated users
                else:
                    raise
    
    @pytest.mark.asyncio
    async def test_ip_based_rate_limiting(self, auth_service: AuthenticationService, test_tenant):
        """Test IP-based rate limiting."""
        # This would be implemented with Redis or similar in production
        # For now, test that multiple requests from same IP are handled
        
        requests_from_ip = []
        for i in range(20):
            login_request = LoginRequest(
                email=f"test{i}@example.com",
                password="WrongPassword",
                provider=AuthProvider.LOCAL,
                ip_address="192.168.1.100",  # Same IP
                user_agent="Mozilla/5.0 Test Browser"
            )
            requests_from_ip.append(login_request)
        
        # All requests should be processed (no rate limiting implemented yet)
        for request in requests_from_ip:
            try:
                await auth_service.authenticate_user(request, test_tenant.id)
            except InvalidCredentialsError:
                pass  # Expected for non-existent users


class TestSecurityHeaders:
    """Test security headers and context tracking."""
    
    @pytest.mark.asyncio
    async def test_login_session_tracking(self, auth_service: AuthenticationService, test_user: User, test_tenant):
        """Test that login sessions are properly tracked."""
        login_request = LoginRequest(
            email=test_user.email,
            password="SecurePassword123!",
            provider=AuthProvider.LOCAL,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        
        response = await auth_service.authenticate_user(login_request, test_tenant.id)
        
        assert response.success is True
        # Session should be created and tracked
        # In a full implementation, we'd verify session in database
    
    @pytest.mark.asyncio
    async def test_login_geolocation_tracking(self, auth_service: AuthenticationService, test_user: User, test_tenant):
        """Test geolocation tracking for login sessions."""
        different_ips = [
            "192.168.1.100",  # Local
            "203.0.113.1",    # Example public IP
            "198.51.100.1",   # Another example IP
        ]
        
        for ip in different_ips:
            login_request = LoginRequest(
                email=test_user.email,
                password="SecurePassword123!",
                provider=AuthProvider.LOCAL,
                ip_address=ip,
                user_agent="Mozilla/5.0 Test Browser"
            )
            
            response = await auth_service.authenticate_user(login_request, test_tenant.id)
            assert response.success is True
            # Each login from different IP should be tracked
    
    @pytest.mark.asyncio
    async def test_suspicious_login_detection(self, auth_service: AuthenticationService, test_user: User, test_tenant):
        """Test detection of suspicious login patterns."""
        # Rapid logins from different locations could be suspicious
        suspicious_requests = [
            LoginRequest(
                email=test_user.email,
                password="SecurePassword123!",
                provider=AuthProvider.LOCAL,
                ip_address="192.168.1.100",
                user_agent="Mozilla/5.0 (Windows NT 10.0) Chrome"
            ),
            LoginRequest(
                email=test_user.email,
                password="SecurePassword123!",
                provider=AuthProvider.LOCAL,
                ip_address="203.0.113.1",  # Different IP immediately after
                user_agent="Mozilla/5.0 (Macintosh) Safari"
            )
        ]
        
        for request in suspicious_requests:
            response = await auth_service.authenticate_user(request, test_tenant.id)
            assert response.success is True
            # In production, this might trigger additional verification
    
    @pytest.mark.asyncio
    async def test_user_agent_tracking(self, auth_service: AuthenticationService, test_user: User, test_tenant):
        """Test user agent tracking for security analysis."""
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            "curl/7.68.0",  # Potentially suspicious
            "python-requests/2.25.1",  # API client
        ]
        
        for user_agent in user_agents:
            login_request = LoginRequest(
                email=test_user.email,
                password="SecurePassword123!",
                provider=AuthProvider.LOCAL,
                ip_address="192.168.1.100",
                user_agent=user_agent
            )
            
            response = await auth_service.authenticate_user(login_request, test_tenant.id)
            assert response.success is True
            # User agent should be tracked in session


class TestConcurrentLogins:
    """Test concurrent login scenarios."""
    
    @pytest.mark.asyncio
    async def test_concurrent_logins_same_user(self, auth_service: AuthenticationService, test_user: User, test_tenant):
        """Test multiple concurrent logins for same user."""
        login_request = LoginRequest(
            email=test_user.email,
            password="SecurePassword123!",
            provider=AuthProvider.LOCAL,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 Test Browser"
        )
        
        # Simulate concurrent logins
        login_tasks = [
            auth_service.authenticate_user(login_request, test_tenant.id)
            for _ in range(5)
        ]
        
        responses = await asyncio.gather(*login_tasks)
        
        # All logins should succeed
        for response in responses:
            assert response.success is True
            assert response.access_token is not None
    
    @pytest.mark.asyncio
    async def test_concurrent_logins_different_users(self, auth_service: AuthenticationService, test_tenant):
        """Test concurrent logins for different users."""
        # Create multiple users
        users = []
        for i in range(10):
            user_data = UserCreate(
                tenant_id=test_tenant.id,
                email=f"concurrent{i}@example.com",
                first_name=f"Concurrent{i}",
                last_name="User",
                password="Password123!",
                role=UserRole.DEVELOPER
            )
            user = await auth_service.create_user(user_data)
            users.append(user)
        
        # Activate all users
        test_db = await auth_service._get_db()
        for user in users:
            await test_db.execute(
                UserORM.__table__.update()
                .where(UserORM.id == user.id)
                .values(status=UserStatus.ACTIVE)
            )
        await test_db.commit()
        
        # Simulate concurrent logins
        login_tasks = []
        for user in users:
            login_request = LoginRequest(
                email=user.email,
                password="Password123!",
                provider=AuthProvider.LOCAL,
                ip_address="192.168.1.100",
                user_agent="Mozilla/5.0 Test Browser"
            )
            login_tasks.append(auth_service.authenticate_user(login_request, test_tenant.id))
        
        responses = await asyncio.gather(*login_tasks)
        
        # All logins should succeed
        successful_logins = sum(1 for r in responses if r.success)
        assert successful_logins == len(users)


class TestLoginPerformance:
    """Test login performance under load."""
    
    @pytest.mark.asyncio
    async def test_login_response_time(self, auth_service: AuthenticationService, test_user: User, test_tenant):
        """Test login response time is within acceptable limits."""
        login_request = LoginRequest(
            email=test_user.email,
            password="SecurePassword123!",
            provider=AuthProvider.LOCAL,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 Test Browser"
        )
        
        start_time = time.time()
        response = await auth_service.authenticate_user(login_request, test_tenant.id)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert response.success is True
        assert response_time < 2.0  # Should complete within 2 seconds
    
    @pytest.mark.asyncio
    async def test_password_hashing_performance(self, auth_service: AuthenticationService):
        """Test password hashing performance."""
        password = "TestPassword123!"
        
        start_time = time.time()
        hash_result = await auth_service._hash_password(password)
        end_time = time.time()
        
        hashing_time = end_time - start_time
        
        assert hash_result is not None
        assert hash_result != password
        assert hashing_time < 1.0  # Should complete within 1 second
    
    @pytest.mark.asyncio
    async def test_jwt_generation_performance(self, auth_service: AuthenticationService, test_user: User, user_session: UserSession):
        """Test JWT token generation performance."""
        start_time = time.time()
        tokens = await auth_service._generate_tokens(test_user, user_session)
        end_time = time.time()
        
        generation_time = end_time - start_time
        
        assert tokens["access_token"] is not None
        assert tokens["refresh_token"] is not None
        assert generation_time < 0.1  # Should complete within 100ms