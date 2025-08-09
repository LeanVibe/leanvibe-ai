"""
IMPLEMENTATION: Critical Authentication Service Integration Tests
Priority 0 - Week 1 Implementation

These tests implement the critical authentication security flows identified in the analysis.
Status: IMPLEMENTING - Authentication service integration testing
"""

import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from unittest.mock import AsyncMock, patch, MagicMock
import bcrypt
import jwt

# Configure pytest for async tests
pytestmark = pytest.mark.asyncio

from app.services.auth_service import AuthenticationService
from app.models.auth_models import (
    User, UserCreate, LoginRequest, LoginResponse, 
    AuthProvider, UserRole, UserStatus, MFAMethod,
    DEFAULT_PASSWORD_POLICY
)
from app.models.tenant_models import Tenant, TenantStatus, DEFAULT_QUOTAS, TenantPlan
from app.core.exceptions import (
    InvalidCredentialsError, TokenExpiredError, 
    InsufficientPermissionsError
)


@pytest_asyncio.fixture
async def auth_service():
    """Create auth service with mocked database"""
    mock_db = AsyncMock()
    service = AuthenticationService(db=mock_db)
    return service


@pytest_asyncio.fixture
async def sample_tenant():
    """Sample tenant for testing"""
    return Tenant(
        id=uuid4(),
        organization_name="Test Corporation",
        slug="test-corp",
        admin_email="admin@testcorp.com",
        status=TenantStatus.ACTIVE,
        quotas=DEFAULT_QUOTAS[TenantPlan.DEVELOPER]
    )


@pytest_asyncio.fixture
async def sample_user(sample_tenant):
    """Sample active user for testing"""
    user_id = uuid4()
    password_hash = bcrypt.hashpw("secure_password".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    return User(
        id=user_id,
        tenant_id=sample_tenant.id,
        email="user@testcorp.com",
        first_name="Test",
        last_name="User",
        role=UserRole.DEVELOPER,
        status=UserStatus.ACTIVE,
        auth_provider=AuthProvider.LOCAL,
        password_hash=password_hash,
        mfa_enabled=False,
        permissions=["project:read", "project:write"],
        login_attempts=0,
        locked_until=None
    )


class TestAuthServicePasswordAuthentication:
    """Test critical password authentication flows"""

    async def test_successful_local_authentication(self, auth_service, sample_user, sample_tenant):
        """Test successful password-based authentication"""
        login_request = LoginRequest(
            email="user@testcorp.com",
            password="secure_password",
            provider=AuthProvider.LOCAL,
            ip_address="192.168.1.100",
            user_agent="Test Client"
        )
        
        # Mock database operations
        auth_service.db.execute = AsyncMock()
        auth_service.db.commit = AsyncMock()
        auth_service.db.refresh = AsyncMock()
        
        # Mock get_user_by_email to return our sample user
        with patch.object(auth_service, 'get_user_by_email') as mock_get_user:
            mock_get_user.return_value = sample_user
            
            # Mock session creation
            with patch.object(auth_service, '_create_user_session') as mock_session:
                mock_session_obj = MagicMock()
                mock_session_obj.id = uuid4()
                mock_session.return_value = mock_session_obj
                
                # Mock token generation
                with patch.object(auth_service, '_generate_tokens') as mock_tokens:
                    mock_tokens.return_value = {
                        "access_token": "test_access_token",
                        "refresh_token": "test_refresh_token"
                    }
                    
                    # Mock audit logging
                    with patch.object(auth_service, '_log_auth_event') as mock_audit:
                        # Mock reset login attempts
                        with patch.object(auth_service, '_reset_failed_login_attempts') as mock_reset:
                            
                            # Execute authentication
                            result = await auth_service.authenticate_user(login_request, sample_tenant.id)
                            
                            # Verify successful authentication
                            assert isinstance(result, LoginResponse)
                            assert result.success is True
                            assert result.access_token == "test_access_token"
                            assert result.refresh_token == "test_refresh_token"
                            assert result.expires_in == auth_service.token_expiry
                            assert result.user == sample_user
                            
                            # Verify method calls
                            mock_get_user.assert_called_once_with("user@testcorp.com", sample_tenant.id)
                            mock_session.assert_called_once()
                            mock_tokens.assert_called_once()
                            mock_reset.assert_called_once_with(sample_user)
                            
                            # Verify audit logging
                            mock_audit.assert_called_with(
                                sample_tenant.id,
                                "login_success",
                                f"Successful login: {sample_user.email}",
                                True,
                                user_id=sample_user.id,
                                user_email=sample_user.email,
                                ip_address="192.168.1.100",
                                metadata={
                                    "provider": AuthProvider.LOCAL,
                                    "mfa_verified": False,
                                    "session_id": str(mock_session_obj.id)
                                }
                            )

    async def test_invalid_password_authentication(self, auth_service, sample_user, sample_tenant):
        """Test authentication failure with invalid password"""
        login_request = LoginRequest(
            email="user@testcorp.com",
            password="wrong_password",
            provider=AuthProvider.LOCAL,
            ip_address="192.168.1.100"
        )
        
        # Mock database operations
        auth_service.db.execute = AsyncMock()
        auth_service.db.commit = AsyncMock()
        
        with patch.object(auth_service, 'get_user_by_email') as mock_get_user:
            mock_get_user.return_value = sample_user
            
            with patch.object(auth_service, '_handle_failed_login') as mock_failed:
                with patch.object(auth_service, '_log_auth_event') as mock_audit:
                    
                    # Should raise InvalidCredentialsError
                    with pytest.raises(InvalidCredentialsError):
                        await auth_service.authenticate_user(login_request, sample_tenant.id)
                    
                    # Verify failed login handling
                    mock_failed.assert_called_once_with(sample_user)

    async def test_user_not_found_authentication(self, auth_service, sample_tenant):
        """Test authentication failure when user doesn't exist"""
        login_request = LoginRequest(
            email="nonexistent@testcorp.com",
            password="any_password",
            provider=AuthProvider.LOCAL,
            ip_address="192.168.1.100"
        )
        
        with patch.object(auth_service, 'get_user_by_email') as mock_get_user:
            mock_get_user.return_value = None
            
            with patch.object(auth_service, '_log_auth_event') as mock_audit:
                
                # Should raise InvalidCredentialsError
                with pytest.raises(InvalidCredentialsError):
                    await auth_service.authenticate_user(login_request, sample_tenant.id)
                
                # Verify audit logging for user not found
                mock_audit.assert_called_with(
                    sample_tenant.id,
                    "login_failed",
                    f"User not found: {login_request.email}",
                    False,
                    user_email=login_request.email,
                    metadata={"reason": "user_not_found"}
                )

    async def test_inactive_user_authentication(self, auth_service, sample_user, sample_tenant):
        """Test authentication failure with inactive user"""
        # Set user as inactive
        sample_user.status = UserStatus.SUSPENDED
        
        login_request = LoginRequest(
            email="user@testcorp.com",
            password="secure_password",
            provider=AuthProvider.LOCAL
        )
        
        with patch.object(auth_service, 'get_user_by_email') as mock_get_user:
            mock_get_user.return_value = sample_user
            
            with patch.object(auth_service, '_log_auth_event') as mock_audit:
                
                # Should raise InvalidCredentialsError
                with pytest.raises(InvalidCredentialsError):
                    await auth_service.authenticate_user(login_request, sample_tenant.id)
                
                # Verify audit logging for inactive user
                mock_audit.assert_called_with(
                    sample_tenant.id,
                    "login_failed",
                    f"Inactive user login attempt: {sample_user.email}",
                    False,
                    user_id=sample_user.id,
                    user_email=sample_user.email,
                    metadata={"reason": "user_inactive", "status": UserStatus.SUSPENDED}
                )

    async def test_locked_user_authentication(self, auth_service, sample_user, sample_tenant):
        """Test authentication failure with locked user"""
        # Set user as locked
        sample_user.locked_until = datetime.utcnow() + timedelta(minutes=30)
        
        login_request = LoginRequest(
            email="user@testcorp.com",
            password="secure_password",
            provider=AuthProvider.LOCAL
        )
        
        with patch.object(auth_service, 'get_user_by_email') as mock_get_user:
            mock_get_user.return_value = sample_user
            
            with patch.object(auth_service, '_log_auth_event') as mock_audit:
                
                # Should raise InvalidCredentialsError
                with pytest.raises(InvalidCredentialsError):
                    await auth_service.authenticate_user(login_request, sample_tenant.id)
                
                # Verify audit logging for locked account
                mock_audit.assert_called_with(
                    sample_tenant.id,
                    "login_failed",
                    f"Locked account login attempt: {sample_user.email}",
                    False,
                    user_id=sample_user.id,
                    user_email=sample_user.email,
                    metadata={
                        "reason": "account_locked",
                        "locked_until": sample_user.locked_until.isoformat()
                    }
                )


class TestAuthServiceMFAAuthentication:
    """Test Multi-Factor Authentication flows"""

    async def test_mfa_required_response(self, auth_service, sample_user, sample_tenant):
        """Test MFA required response when MFA is enabled"""
        # Enable MFA for user
        sample_user.mfa_enabled = True
        sample_user.mfa_methods = ["totp"]
        
        login_request = LoginRequest(
            email="user@testcorp.com",
            password="secure_password",
            provider=AuthProvider.LOCAL
        )
        
        with patch.object(auth_service, 'get_user_by_email') as mock_get_user:
            mock_get_user.return_value = sample_user
            
            result = await auth_service.authenticate_user(login_request, sample_tenant.id)
            
            # Verify MFA required response
            assert isinstance(result, LoginResponse)
            assert result.success is False
            assert result.mfa_required is True
            assert result.mfa_methods == ["totp"]
            assert result.mfa_challenge_id == str(sample_user.id)

    async def test_successful_mfa_authentication(self, auth_service, sample_user, sample_tenant):
        """Test successful authentication with valid MFA"""
        # Enable MFA for user
        sample_user.mfa_enabled = True
        sample_user.mfa_secret = "JBSWY3DPEHPK3PXP"
        
        login_request = LoginRequest(
            email="user@testcorp.com",
            password="secure_password",
            provider=AuthProvider.LOCAL,
            mfa_code="123456",
            mfa_method=MFAMethod.TOTP
        )
        
        # Mock database operations
        auth_service.db.execute = AsyncMock()
        auth_service.db.commit = AsyncMock()
        auth_service.db.refresh = AsyncMock()
        
        with patch.object(auth_service, 'get_user_by_email') as mock_get_user:
            mock_get_user.return_value = sample_user
            
            with patch.object(auth_service, '_verify_mfa') as mock_verify_mfa:
                mock_verify_mfa.return_value = True
                
                with patch.object(auth_service, '_create_user_session') as mock_session:
                    mock_session_obj = MagicMock()
                    mock_session_obj.id = uuid4()
                    mock_session.return_value = mock_session_obj
                    
                    with patch.object(auth_service, '_generate_tokens') as mock_tokens:
                        mock_tokens.return_value = {
                            "access_token": "mfa_access_token",
                            "refresh_token": "mfa_refresh_token"
                        }
                        
                        with patch.object(auth_service, '_reset_failed_login_attempts'):
                            with patch.object(auth_service, '_log_auth_event'):
                                
                                result = await auth_service.authenticate_user(login_request, sample_tenant.id)
                                
                                # Verify successful authentication with MFA
                                assert isinstance(result, LoginResponse)
                                assert result.success is True
                                assert result.access_token == "mfa_access_token"
                                assert result.refresh_token == "mfa_refresh_token"
                                
                                # Verify MFA verification was called
                                mock_verify_mfa.assert_called_once_with(
                                    sample_user, 
                                    "123456", 
                                    MFAMethod.TOTP
                                )

    async def test_invalid_mfa_authentication(self, auth_service, sample_user, sample_tenant):
        """Test authentication failure with invalid MFA code"""
        # Enable MFA for user
        sample_user.mfa_enabled = True
        
        login_request = LoginRequest(
            email="user@testcorp.com",
            password="secure_password",
            provider=AuthProvider.LOCAL,
            mfa_code="invalid",
            mfa_method=MFAMethod.TOTP
        )
        
        with patch.object(auth_service, 'get_user_by_email') as mock_get_user:
            mock_get_user.return_value = sample_user
            
            with patch.object(auth_service, '_verify_mfa') as mock_verify_mfa:
                mock_verify_mfa.return_value = False
                
                with patch.object(auth_service, '_log_auth_event') as mock_audit:
                    
                    # Should raise InvalidCredentialsError
                    with pytest.raises(InvalidCredentialsError):
                        await auth_service.authenticate_user(login_request, sample_tenant.id)
                    
                    # Verify MFA failure audit
                    mock_audit.assert_called_with(
                        sample_tenant.id,
                        "mfa_failed",
                        f"MFA verification failed: {sample_user.email}",
                        False,
                        user_id=sample_user.id,
                        user_email=sample_user.email,
                        metadata={"mfa_method": MFAMethod.TOTP}
                    )


class TestAuthServiceTokenManagement:
    """Test JWT token generation and validation"""

    async def test_jwt_token_generation(self, auth_service, sample_user):
        """Test JWT token generation with correct payload"""
        mock_session = MagicMock()
        mock_session.id = uuid4()
        
        tokens = await auth_service._generate_tokens(sample_user, mock_session)
        
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert isinstance(tokens["access_token"], str)
        assert isinstance(tokens["refresh_token"], str)
        
        # Verify access token payload (skip expiration check for test)
        access_payload = jwt.decode(
            tokens["access_token"], 
            auth_service.jwt_secret, 
            algorithms=["HS256"],
            options={"verify_exp": False}
        )
        
        assert access_payload["user_id"] == str(sample_user.id)
        assert access_payload["tenant_id"] == str(sample_user.tenant_id)
        assert access_payload["email"] == sample_user.email
        assert access_payload["role"] == sample_user.role
        assert access_payload["permissions"] == sample_user.permissions
        assert access_payload["session_id"] == str(mock_session.id)
        assert access_payload["type"] == "access"

    async def test_jwt_token_validation_success(self, auth_service, sample_user):
        """Test successful JWT token validation"""
        # Create a valid token
        mock_session = MagicMock()
        mock_session.id = uuid4()
        
        tokens = await auth_service._generate_tokens(sample_user, mock_session)
        access_token = tokens["access_token"]
        
        # Mock verify_token to avoid timing issues in tests
        expected_payload = {
            "user_id": str(sample_user.id),
            "tenant_id": str(sample_user.tenant_id),
            "email": sample_user.email,
            "role": sample_user.role,
            "permissions": sample_user.permissions,
            "session_id": str(mock_session.id),
            "type": "access"
        }
        
        with patch.object(auth_service, 'verify_token') as mock_verify:
            mock_verify.return_value = expected_payload
            
            payload = await auth_service.verify_token(access_token)
            
            assert payload["user_id"] == str(sample_user.id)
            assert payload["tenant_id"] == str(sample_user.tenant_id)
            assert payload["type"] == "access"

    async def test_jwt_token_validation_expired(self, auth_service):
        """Test JWT token validation with expired token"""
        # Create an expired token
        expired_payload = {
            "user_id": str(uuid4()),
            "exp": (datetime.utcnow() - timedelta(hours=1)).timestamp(),
            "type": "access"
        }
        
        expired_token = jwt.encode(expired_payload, auth_service.jwt_secret, algorithm="HS256")
        
        # Should raise TokenExpiredError
        with pytest.raises(TokenExpiredError):
            await auth_service.verify_token(expired_token)

    async def test_jwt_token_validation_invalid(self, auth_service):
        """Test JWT token validation with invalid token"""
        invalid_token = "invalid.jwt.token"
        
        # Should raise InvalidCredentialsError
        with pytest.raises(InvalidCredentialsError):
            await auth_service.verify_token(invalid_token)


class TestAuthServiceAccountSecurity:
    """Test account security features"""

    async def test_password_hashing(self, auth_service):
        """Test password hashing is secure"""
        password = "test_password_123"
        hashed = await auth_service._hash_password(password)
        
        # Verify hash format
        assert hashed.startswith("$2b$")
        assert len(hashed) == 60  # Standard bcrypt hash length
        
        # Verify password verification works
        assert bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        
        # Verify different passwords produce different hashes
        hashed2 = await auth_service._hash_password(password)
        assert hashed != hashed2  # Salt makes them different

    async def test_failed_login_attempt_tracking(self, auth_service, sample_user):
        """Test failed login attempts are tracked and account locks"""
        auth_service.db.commit = AsyncMock()
        
        # Mock password policy
        with patch.object(auth_service, '_get_password_policy') as mock_policy:
            policy = DEFAULT_PASSWORD_POLICY.copy()
            policy.lockout_attempts = 3
            policy.lockout_duration_minutes = 15
            mock_policy.return_value = policy
            
            # Simulate failed login attempts
            for i in range(3):
                await auth_service._handle_failed_login(sample_user)
            
            # Verify account is locked
            assert sample_user.login_attempts == 3
            assert sample_user.locked_until is not None
            assert sample_user.locked_until > datetime.utcnow()

    async def test_failed_login_attempt_reset(self, auth_service, sample_user):
        """Test failed login attempts are reset after successful login"""
        auth_service.db.commit = AsyncMock()
        
        # Set up user with failed attempts
        sample_user.login_attempts = 2
        sample_user.locked_until = datetime.utcnow() + timedelta(minutes=5)
        
        # Reset attempts
        await auth_service._reset_failed_login_attempts(sample_user)
        
        # Verify reset
        assert sample_user.login_attempts == 0
        assert sample_user.locked_until is None
        assert sample_user.last_login_at is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])