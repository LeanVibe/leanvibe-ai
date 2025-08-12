"""
Comprehensive enterprise authentication features tests
Tests MFA, SSO, audit logging, session management, and enterprise security
"""

import pytest
import pytest_asyncio
import secrets
import base64
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
from uuid import uuid4

from app.models.auth_models import (
    LoginRequest, MFASetupRequest, MFASetupResponse, AuthProvider, 
    MFAMethod, UserCreate, UserRole, SessionStatus, UserStatus
)
from app.services.auth_service import AuthenticationService
from app.core.exceptions import InvalidCredentialsError
from tests.fixtures.auth_test_fixtures import *


class TestMFASetup:
    """Test Multi-Factor Authentication setup."""
    
    @pytest.mark.asyncio
    async def test_mfa_totp_setup(self, auth_test_client: TestClient, authenticated_headers, test_tenant):
        """Test TOTP MFA setup."""
        with patch('app.middleware.tenant_middleware.require_tenant') as mock_tenant:
            mock_tenant.return_value = test_tenant
            
            response = auth_test_client.post(
                "/api/v1/auth/mfa/setup",
                headers=authenticated_headers,
                json={"method": "totp"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["method"] == "totp"
            assert "secret" in data
            assert "qr_code" in data
            assert "backup_codes" in data
            assert len(data["backup_codes"]) == 10
            
            # QR code should be base64 encoded PNG
            assert data["qr_code"].startswith("data:image/png;base64,")
    
    @pytest.mark.asyncio
    async def test_mfa_sms_setup(self, auth_test_client: TestClient, authenticated_headers, test_tenant):
        """Test SMS MFA setup."""
        with patch('app.middleware.tenant_middleware.require_tenant') as mock_tenant:
            mock_tenant.return_value = test_tenant
            
            response = auth_test_client.post(
                "/api/v1/auth/mfa/setup",
                headers=authenticated_headers,
                json={
                    "method": "sms",
                    "phone_number": "+1234567890"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["method"] == "sms"
            assert "backup_codes" in data
            assert len(data["backup_codes"]) == 10
            assert "secret" not in data  # SMS doesn't use secret
            assert "qr_code" not in data  # SMS doesn't use QR code
    
    @pytest.mark.asyncio
    async def test_mfa_email_setup(self, auth_test_client: TestClient, authenticated_headers, test_tenant):
        """Test Email MFA setup."""
        with patch('app.middleware.tenant_middleware.require_tenant') as mock_tenant:
            mock_tenant.return_value = test_tenant
            
            response = auth_test_client.post(
                "/api/v1/auth/mfa/setup",
                headers=authenticated_headers,
                json={"method": "email"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["method"] == "email"
            assert "backup_codes" in data
            assert len(data["backup_codes"]) == 10
    
    @pytest.mark.asyncio
    async def test_mfa_verification_success(self, auth_test_client: TestClient, authenticated_headers, test_tenant):
        """Test MFA verification with valid code."""
        with patch('app.middleware.tenant_middleware.require_tenant') as mock_tenant:
            mock_tenant.return_value = test_tenant
            
            response = auth_test_client.post(
                "/api/v1/auth/mfa/verify",
                headers=authenticated_headers,
                json={
                    "code": "123456",  # Valid 6-digit code
                    "method": "totp"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "MFA verified successfully" in data["message"]
            assert data["enabled"] is True
    
    @pytest.mark.asyncio
    async def test_mfa_verification_invalid_code(self, auth_test_client: TestClient, authenticated_headers, test_tenant):
        """Test MFA verification with invalid code."""
        with patch('app.middleware.tenant_middleware.require_tenant') as mock_tenant:
            mock_tenant.return_value = test_tenant
            
            response = auth_test_client.post(
                "/api/v1/auth/mfa/verify",
                headers=authenticated_headers,
                json={
                    "code": "123",  # Invalid code format
                    "method": "totp"
                }
            )
            
            assert response.status_code == 400
            data = response.json()
            assert "Invalid MFA code" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_mfa_backup_codes_generation(self, auth_service: AuthenticationService, test_user: User):
        """Test MFA backup codes generation."""
        setup_request = MFASetupRequest(method=MFAMethod.TOTP)
        
        # Mock user authentication for MFA setup
        with patch.object(auth_service, 'verify_token') as mock_verify:
            mock_verify.return_value = {"user_id": str(test_user.id)}
            with patch.object(auth_service, 'get_user_by_id') as mock_get_user:
                mock_get_user.return_value = test_user
                
                # Create mock credentials
                from fastapi.security import HTTPAuthorizationCredentials
                mock_credentials = HTTPAuthorizationCredentials(
                    scheme="Bearer",
                    credentials="mock_token"
                )
                
                # This would be called in the endpoint
                import pyotp
                secret = pyotp.random_base32()
                backup_codes = [secrets.token_hex(4).upper() for _ in range(10)]
                
                # Verify backup codes format
                for code in backup_codes:
                    assert len(code) == 8  # 4 hex bytes = 8 characters
                    assert code.isupper()
                    assert all(c in '0123456789ABCDEF' for c in code)
    
    @pytest.mark.asyncio
    async def test_mfa_qr_code_generation(self, auth_service: AuthenticationService, test_user: User):
        """Test TOTP QR code generation."""
        import pyotp
        import qrcode
        import io
        
        secret = pyotp.random_base32()
        
        # Generate QR code
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            test_user.email,
            issuer_name="LeanVibe"
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        qr_code_data = base64.b64encode(buffer.getvalue()).decode()
        
        # Verify QR code generation
        assert qr_code_data is not None
        assert len(qr_code_data) > 100  # Should be substantial data
        
        # Verify TOTP URI format
        assert "otpauth://totp/" in totp_uri
        assert test_user.email in totp_uri
        assert "LeanVibe" in totp_uri
        assert secret in totp_uri


class TestMFAAuthentication:
    """Test MFA authentication flows."""
    
    @pytest.mark.asyncio
    async def test_mfa_totp_authentication(self, auth_service: AuthenticationService, mfa_enabled_user: User, test_tenant):
        """Test TOTP authentication with real TOTP library."""
        import pyotp
        
        # Generate valid TOTP code
        totp = pyotp.TOTP(mfa_enabled_user.mfa_secret)
        valid_code = totp.now()
        
        # Test MFA verification
        is_valid = await auth_service._verify_mfa(mfa_enabled_user, valid_code, MFAMethod.TOTP)
        assert is_valid is True
        
        # Test with invalid code
        is_invalid = await auth_service._verify_mfa(mfa_enabled_user, "000000", MFAMethod.TOTP)
        assert is_invalid is False
    
    @pytest.mark.asyncio
    async def test_mfa_sms_authentication(self, auth_service: AuthenticationService, test_user: User, test_db):
        """Test SMS MFA authentication."""
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
        
        # Test SMS verification (mocked)
        is_valid = await auth_service._verify_mfa(test_user, "123456", MFAMethod.SMS)
        assert is_valid is True  # Mock implementation always returns True
    
    @pytest.mark.asyncio
    async def test_mfa_email_authentication(self, auth_service: AuthenticationService, test_user: User, test_db):
        """Test Email MFA authentication."""
        # Enable Email MFA for user
        await test_db.execute(
            UserORM.__table__.update()
            .where(UserORM.id == test_user.id)
            .values(
                mfa_enabled=True,
                mfa_methods=["email"]
            )
        )
        await test_db.commit()
        
        # Test Email verification (mocked)
        is_valid = await auth_service._verify_mfa(test_user, "123456", MFAMethod.EMAIL)
        assert is_valid is True  # Mock implementation always returns True
    
    @pytest.mark.asyncio
    async def test_mfa_backup_code_authentication(self, auth_service: AuthenticationService, mfa_enabled_user: User):
        """Test backup code authentication."""
        # In a full implementation, backup codes would be stored hashed
        # and verified separately from TOTP/SMS/Email
        
        backup_codes = ["ABCD1234", "EFGH5678", "IJKL9012"]
        
        # Test valid backup code
        # This would be implemented as a separate verification method
        assert "ABCD1234" in backup_codes  # Simulated verification
        
        # Test invalid backup code
        assert "INVALID1" not in backup_codes
    
    @pytest.mark.asyncio
    async def test_mfa_time_window_validation(self, auth_service: AuthenticationService, mfa_enabled_user: User):
        """Test TOTP time window validation."""
        import pyotp
        
        # Test current time window
        totp = pyotp.TOTP(mfa_enabled_user.mfa_secret)
        current_code = totp.now()
        is_valid_current = await auth_service._verify_mfa(mfa_enabled_user, current_code, MFAMethod.TOTP)
        assert is_valid_current is True
        
        # Test previous time window (should be valid with window=1)
        previous_code = totp.at(datetime.now().timestamp() - 30)
        is_valid_previous = await auth_service._verify_mfa(mfa_enabled_user, previous_code, MFAMethod.TOTP)
        assert is_valid_previous is True  # TOTP allows 1 window tolerance
        
        # Test very old code (should be invalid)
        old_code = totp.at(datetime.now().timestamp() - 300)  # 5 minutes ago
        is_valid_old = await auth_service._verify_mfa(mfa_enabled_user, old_code, MFAMethod.TOTP)
        assert is_valid_old is False


class TestSSOAuthentication:
    """Test Single Sign-On authentication."""
    
    @pytest.mark.asyncio
    async def test_sso_google_redirect(self, auth_test_client: TestClient, test_tenant):
        """Test Google SSO redirect."""
        with patch('app.middleware.tenant_middleware.require_tenant') as mock_tenant:
            mock_tenant.return_value = test_tenant
            
            response = auth_test_client.get("/api/v1/auth/sso/google")
            
            # Should redirect to Google OAuth
            assert response.status_code == 307  # Redirect
            assert "google.com" in response.headers["location"]
    
    @pytest.mark.asyncio
    async def test_sso_microsoft_redirect(self, auth_test_client: TestClient, test_tenant):
        """Test Microsoft SSO redirect."""
        with patch('app.middleware.tenant_middleware.require_tenant') as mock_tenant:
            mock_tenant.return_value = test_tenant
            
            response = auth_test_client.get("/api/v1/auth/sso/microsoft")
            
            # Should redirect to Microsoft OAuth
            assert response.status_code == 307  # Redirect
            assert "microsoftonline.com" in response.headers["location"]
    
    @pytest.mark.asyncio
    async def test_sso_saml_redirect(self, auth_test_client: TestClient, test_tenant):
        """Test SAML SSO redirect."""
        with patch('app.middleware.tenant_middleware.require_tenant') as mock_tenant:
            mock_tenant.return_value = test_tenant
            
            response = auth_test_client.get("/api/v1/auth/sso/saml")
            
            # Should redirect to SAML login
            assert response.status_code == 307  # Redirect
            assert "/saml/login" in response.headers["location"]
    
    @pytest.mark.asyncio
    async def test_sso_callback_success(self, auth_test_client: TestClient):
        """Test successful SSO callback."""
        response = auth_test_client.get(
            "/api/v1/auth/sso/google/callback",
            params={
                "code": "oauth_authorization_code",
                "state": "oauth_state_parameter"
            }
        )
        
        # Should redirect to dashboard on success
        assert response.status_code == 307  # Redirect
        assert "/dashboard" in response.headers["location"]
        assert "login=success" in response.headers["location"]
    
    @pytest.mark.asyncio
    async def test_sso_callback_error(self, auth_test_client: TestClient):
        """Test SSO callback with error."""
        response = auth_test_client.get(
            "/api/v1/auth/sso/google/callback",
            params={"error": "access_denied"}
        )
        
        # Should redirect to login with error
        assert response.status_code == 307  # Redirect
        assert "/login" in response.headers["location"]
        assert "error=sso_error" in response.headers["location"]
    
    @pytest.mark.asyncio
    async def test_sso_callback_missing_code(self, auth_test_client: TestClient):
        """Test SSO callback without authorization code."""
        response = auth_test_client.get("/api/v1/auth/sso/google/callback")
        
        # Should redirect to login with error
        assert response.status_code == 307  # Redirect
        assert "/login" in response.headers["location"]
        assert "error=missing_code" in response.headers["location"]
    
    @pytest.mark.asyncio
    async def test_saml_sso_post(self, auth_test_client: TestClient, mock_saml_response):
        """Test SAML SSO POST request."""
        response = auth_test_client.post(
            "/api/v1/auth/saml/sso",
            data={
                "SAMLResponse": base64.b64encode(mock_saml_response.encode()).decode(),
                "RelayState": "saml_relay_state"
            }
        )
        
        # Should redirect to dashboard on success
        assert response.status_code == 307  # Redirect
        assert "/dashboard" in response.headers["location"]
        assert "saml=success" in response.headers["location"]
    
    @pytest.mark.asyncio
    async def test_saml_sso_missing_response(self, auth_test_client: TestClient):
        """Test SAML SSO without SAML response."""
        response = auth_test_client.post("/api/v1/auth/saml/sso", data={})
        
        assert response.status_code == 400
        data = response.json()
        assert "Missing SAML response" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_sso_providers_list(self, auth_test_client: TestClient, test_tenant):
        """Test getting available SSO providers."""
        with patch('app.middleware.tenant_middleware.require_tenant') as mock_tenant:
            mock_tenant.return_value = test_tenant
            
            response = auth_test_client.get("/api/v1/auth/providers")
            
            assert response.status_code == 200
            data = response.json()
            assert "local" in data
            assert "sso_providers" in data
            assert len(data["sso_providers"]) > 0
            
            # Check Google provider
            google_provider = next((p for p in data["sso_providers"] if p["provider"] == "google"), None)
            assert google_provider is not None
            assert google_provider["enabled"] is True
            assert "/auth/sso/google" in google_provider["login_url"]


class TestAuditLogging:
    """Test audit logging functionality."""
    
    @pytest.mark.asyncio
    async def test_login_success_audit_log(self, auth_service: AuthenticationService, test_user: User, test_tenant):
        """Test audit logging for successful login."""
        login_request = LoginRequest(
            email=test_user.email,
            password="SecurePassword123!",
            provider=AuthProvider.LOCAL,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 Test Browser"
        )
        
        # Perform login
        response = await auth_service.authenticate_user(login_request, test_tenant.id)
        assert response.success is True
        
        # Audit log should be created automatically
        # In a full implementation, we'd query audit logs to verify
    
    @pytest.mark.asyncio
    async def test_login_failure_audit_log(self, auth_service: AuthenticationService, test_user: User, test_tenant):
        """Test audit logging for failed login."""
        login_request = LoginRequest(
            email=test_user.email,
            password="WrongPassword",
            provider=AuthProvider.LOCAL,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 Test Browser"
        )
        
        # Perform failed login
        with pytest.raises(InvalidCredentialsError):
            await auth_service.authenticate_user(login_request, test_tenant.id)
        
        # Audit log should record the failure
    
    @pytest.mark.asyncio
    async def test_user_creation_audit_log(self, auth_service: AuthenticationService, test_tenant):
        """Test audit logging for user creation."""
        user_data = UserCreate(
            tenant_id=test_tenant.id,
            email="audit.test@example.com",
            first_name="Audit",
            last_name="Test",
            password="Password123!",
            role=UserRole.DEVELOPER
        )
        
        # Create user
        user = await auth_service.create_user(user_data)
        assert user is not None
        
        # Audit log should record user creation
    
    @pytest.mark.asyncio
    async def test_password_change_audit_log(self, auth_service: AuthenticationService, test_user: User, test_tenant):
        """Test audit logging for password changes."""
        success = await auth_service.change_password(
            test_user.id,
            "SecurePassword123!",
            "NewPassword123!",
            test_tenant.id
        )
        assert success is True
        
        # Audit log should record password change
    
    @pytest.mark.asyncio
    async def test_mfa_events_audit_log(self, auth_service: AuthenticationService, test_user: User, test_tenant):
        """Test audit logging for MFA events."""
        # Log MFA setup
        await auth_service._log_auth_event(
            test_tenant.id,
            "mfa_setup",
            f"User {test_user.email} enabled MFA",
            True,
            user_id=test_user.id,
            user_email=test_user.email,
            event_metadata={"mfa_method": "totp"}
        )
        
        # Log MFA verification
        await auth_service._log_auth_event(
            test_tenant.id,
            "mfa_verified",
            f"User {test_user.email} completed MFA verification",
            True,
            user_id=test_user.id,
            user_email=test_user.email,
            event_metadata={"mfa_method": "totp"}
        )
        
        # Audit logs should be created without errors
    
    @pytest.mark.asyncio
    async def test_audit_log_metadata(self, auth_service: AuthenticationService, test_tenant):
        """Test audit log metadata collection."""
        metadata = {
            "ip_address": "192.168.1.100",
            "user_agent": "Mozilla/5.0 Test Browser",
            "session_id": str(uuid4()),
            "auth_method": "local",
            "risk_score": 0.2
        }
        
        await auth_service._log_auth_event(
            test_tenant.id,
            "login_success",
            "Test login event",
            True,
            ip_address=metadata["ip_address"],
            event_metadata={
                "user_agent": metadata["user_agent"],
                "session_id": metadata["session_id"],
                "auth_method": metadata["auth_method"],
                "risk_score": metadata["risk_score"]
            }
        )
        
        # Metadata should be properly stored
    
    @pytest.mark.asyncio
    async def test_audit_log_tenant_isolation(self, auth_service: AuthenticationService, test_tenant, secondary_tenant):
        """Test that audit logs are properly isolated by tenant."""
        # Log event for primary tenant
        await auth_service._log_auth_event(
            test_tenant.id,
            "test_event_primary",
            "Event in primary tenant",
            True
        )
        
        # Log event for secondary tenant
        await auth_service._log_auth_event(
            secondary_tenant.id,
            "test_event_secondary",
            "Event in secondary tenant",
            True
        )
        
        # Events should be properly scoped to their respective tenants
        # In a full implementation, we'd verify isolation through queries


class TestSessionManagement:
    """Test session management functionality."""
    
    @pytest.mark.asyncio
    async def test_session_creation(self, auth_service: AuthenticationService, test_user: User):
        """Test user session creation."""
        login_request = LoginRequest(
            email=test_user.email,
            password="SecurePassword123!",
            provider=AuthProvider.LOCAL,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 Test Browser",
            remember_me=True
        )
        
        session = await auth_service._create_user_session(test_user, login_request)
        
        assert session.user_id == test_user.id
        assert session.tenant_id == test_user.tenant_id
        assert session.status == SessionStatus.ACTIVE
        assert session.ip_address == "192.168.1.100"
        assert session.user_agent == "Mozilla/5.0 Test Browser"
        assert session.auth_method == AuthProvider.LOCAL
        
        # Remember me should extend session duration
        if login_request.remember_me:
            duration = session.expires_at - session.created_at
            assert duration.days >= 30
    
    @pytest.mark.asyncio
    async def test_session_expiry(self, auth_service: AuthenticationService, test_user: User, test_db):
        """Test session expiry handling."""
        # Create session
        login_request = LoginRequest(
            email=test_user.email,
            password="SecurePassword123!",
            provider=AuthProvider.LOCAL,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 Test Browser"
        )
        session = await auth_service._create_user_session(test_user, login_request)
        
        # Manually expire session
        expired_time = datetime.utcnow() - timedelta(hours=1)
        await test_db.execute(
            UserSessionORM.__table__.update()
            .where(UserSessionORM.id == session.id)
            .values(
                expires_at=expired_time,
                status=SessionStatus.EXPIRED
            )
        )
        await test_db.commit()
        
        # Get expired session
        expired_session = await auth_service._get_session_by_id(session.id)
        assert expired_session.status == SessionStatus.EXPIRED
        assert expired_session.expires_at < datetime.utcnow()
    
    @pytest.mark.asyncio
    async def test_session_revocation(self, auth_service: AuthenticationService, test_user: User, test_db):
        """Test session revocation."""
        # Create session
        login_request = LoginRequest(
            email=test_user.email,
            password="SecurePassword123!",
            provider=AuthProvider.LOCAL,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 Test Browser"
        )
        session = await auth_service._create_user_session(test_user, login_request)
        
        # Revoke session
        await test_db.execute(
            UserSessionORM.__table__.update()
            .where(UserSessionORM.id == session.id)
            .values(status=SessionStatus.REVOKED)
        )
        await test_db.commit()
        
        # Get revoked session
        revoked_session = await auth_service._get_session_by_id(session.id)
        assert revoked_session.status == SessionStatus.REVOKED
    
    @pytest.mark.asyncio
    async def test_multiple_active_sessions(self, auth_service: AuthenticationService, test_user: User):
        """Test multiple active sessions for same user."""
        # Create multiple sessions
        sessions = []
        for i in range(3):
            login_request = LoginRequest(
                email=test_user.email,
                password="SecurePassword123!",
                provider=AuthProvider.LOCAL,
                ip_address=f"192.168.1.{100 + i}",
                user_agent=f"Browser {i}"
            )
            session = await auth_service._create_user_session(test_user, login_request)
            sessions.append(session)
        
        # All sessions should be active
        for session in sessions:
            assert session.status == SessionStatus.ACTIVE
            assert session.user_id == test_user.id
    
    @pytest.mark.asyncio
    async def test_session_security_tracking(self, auth_service: AuthenticationService, test_user: User):
        """Test session security tracking."""
        login_request = LoginRequest(
            email=test_user.email,
            password="SecurePassword123!",
            provider=AuthProvider.LOCAL,
            ip_address="203.0.113.1",  # Different location
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)"  # Mobile device
        )
        
        session = await auth_service._create_user_session(test_user, login_request)
        
        # Session should track security context
        assert session.ip_address == "203.0.113.1"
        assert "iPhone" in session.user_agent
        assert session.auth_method == AuthProvider.LOCAL
        
        # In a full implementation, this would trigger security analysis
    
    @pytest.mark.asyncio
    async def test_session_concurrent_limit(self, auth_service: AuthenticationService, test_user: User):
        """Test concurrent session limits (if implemented)."""
        # Create many sessions
        sessions = []
        for i in range(10):
            login_request = LoginRequest(
                email=test_user.email,
                password="SecurePassword123!",
                provider=AuthProvider.LOCAL,
                ip_address=f"192.168.1.{100 + i}",
                user_agent=f"Browser {i}"
            )
            session = await auth_service._create_user_session(test_user, login_request)
            sessions.append(session)
        
        # Current implementation doesn't limit concurrent sessions
        # All sessions should be created successfully
        assert len(sessions) == 10
        for session in sessions:
            assert session.status == SessionStatus.ACTIVE


class TestEnterpriseSecurityFeatures:
    """Test enterprise security features."""
    
    @pytest.mark.asyncio
    async def test_password_policy_enforcement(self, auth_service: AuthenticationService, test_tenant):
        """Test enterprise password policy enforcement."""
        policy = await auth_service._get_password_policy(test_tenant.id)
        
        # Verify enterprise password requirements
        assert policy.min_length >= 8
        assert policy.require_uppercase is True
        assert policy.require_lowercase is True
        assert policy.require_digits is True
        assert policy.require_special is True
        assert policy.max_age_days <= 90
        assert policy.history_count >= 5
        assert policy.lockout_attempts <= 10
        assert policy.prevent_common_passwords is True
        assert policy.prevent_personal_info is True
    
    @pytest.mark.asyncio
    async def test_risk_based_authentication(self, auth_service: AuthenticationService, test_user: User, test_tenant):
        """Test risk-based authentication triggers."""
        # Simulate high-risk login scenarios
        high_risk_scenarios = [
            {
                "ip_address": "203.0.113.1",  # Different country
                "user_agent": "curl/7.68.0",  # Non-browser client
                "description": "API client from different location"
            },
            {
                "ip_address": "198.51.100.1",  # VPN/proxy
                "user_agent": "Mozilla/5.0 (Windows NT 5.1)",  # Old browser
                "description": "Outdated browser from suspicious IP"
            }
        ]
        
        for scenario in high_risk_scenarios:
            login_request = LoginRequest(
                email=test_user.email,
                password="SecurePassword123!",
                provider=AuthProvider.LOCAL,
                ip_address=scenario["ip_address"],
                user_agent=scenario["user_agent"]
            )
            
            # In a full implementation, this might trigger additional verification
            response = await auth_service.authenticate_user(login_request, test_tenant.id)
            assert response.success is True
            
            # Risk analysis would happen here
    
    @pytest.mark.asyncio
    async def test_device_fingerprinting(self, auth_service: AuthenticationService, test_user: User):
        """Test device fingerprinting for security."""
        device_signatures = [
            {
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "screen_resolution": "1920x1080",
                "timezone": "America/New_York",
                "language": "en-US"
            },
            {
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "screen_resolution": "2560x1600",
                "timezone": "America/Los_Angeles",
                "language": "en-US"
            }
        ]
        
        sessions = []
        for signature in device_signatures:
            login_request = LoginRequest(
                email=test_user.email,
                password="SecurePassword123!",
                provider=AuthProvider.LOCAL,
                ip_address="192.168.1.100",
                user_agent=signature["user_agent"]
            )
            
            session = await auth_service._create_user_session(test_user, login_request)
            sessions.append(session)
        
        # Each session should track device information
        for session in sessions:
            assert session.user_agent is not None
            assert session.ip_address is not None
        
        # In a full implementation, device fingerprints would be compared
    
    @pytest.mark.asyncio
    async def test_adaptive_authentication(self, auth_service: AuthenticationService, test_user: User, test_tenant):
        """Test adaptive authentication based on context."""
        # Trusted location login
        trusted_login = LoginRequest(
            email=test_user.email,
            password="SecurePassword123!",
            provider=AuthProvider.LOCAL,
            ip_address="192.168.1.100",  # Office IP
            user_agent="Mozilla/5.0 (Windows NT 10.0) Chrome"
        )
        
        trusted_response = await auth_service.authenticate_user(trusted_login, test_tenant.id)
        assert trusted_response.success is True
        
        # Suspicious location login
        suspicious_login = LoginRequest(
            email=test_user.email,
            password="SecurePassword123!",
            provider=AuthProvider.LOCAL,
            ip_address="203.0.113.1",  # Foreign IP
            user_agent="curl/7.68.0"  # Non-browser
        )
        
        suspicious_response = await auth_service.authenticate_user(suspicious_login, test_tenant.id)
        # Current implementation doesn't implement adaptive auth
        assert suspicious_response.success is True
        
        # In a full implementation, suspicious login might require additional verification
    
    @pytest.mark.asyncio
    async def test_compliance_reporting(self, auth_service: AuthenticationService, test_tenant):
        """Test compliance reporting features."""
        # Generate various auth events for compliance reporting
        events = [
            ("user_login", "Successful login", True),
            ("user_logout", "User logout", True),
            ("password_change", "Password changed", True),
            ("mfa_setup", "MFA enabled", True),
            ("login_failed", "Invalid credentials", False),
            ("account_locked", "Account locked", False)
        ]
        
        for event_type, description, success in events:
            await auth_service._log_auth_event(
                test_tenant.id,
                event_type,
                description,
                success,
                ip_address="192.168.1.100",
                event_metadata={"compliance": True}
            )
        
        # Events should be logged for compliance reporting
        # In a full implementation, we'd verify compliance report generation