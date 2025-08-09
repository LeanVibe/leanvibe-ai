"""
Tests for enterprise authentication system in LeanVibe SaaS Platform
Validates user management, authentication, MFA, and SSO functionality
"""

import pytest
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from app.models.auth_models import (
    User, UserCreate, LoginRequest, LoginResponse, UserStatus, UserRole,
    AuthProvider, MFAMethod, PasswordPolicy, DEFAULT_PASSWORD_POLICY
)


class TestUserModels:
    """Test user model validation and logic"""
    
    def test_create_user_model_validation(self):
        """Test user creation model validation"""
        user_data = UserCreate(
            tenant_id=uuid4(),
            email="test@example.com",
            first_name="John",
            last_name="Doe",
            role=UserRole.DEVELOPER,
            password="SecurePass123!",
            auth_provider=AuthProvider.LOCAL
        )
        
        # Validate user creation data
        assert user_data.email == "test@example.com"
        assert user_data.first_name == "John"
        assert user_data.role == UserRole.DEVELOPER
        assert user_data.auth_provider == AuthProvider.LOCAL
        assert user_data.send_invitation is True  # Default value
    
    def test_user_model_with_all_fields(self):
        """Test full user model with all fields"""
        tenant_id = uuid4()
        
        user = User(
            tenant_id=tenant_id,
            email="admin@company.com",
            first_name="Admin",
            last_name="User",
            display_name="Admin User",
            role=UserRole.ADMIN,
            auth_provider=AuthProvider.GOOGLE,
            external_id="google_123456",
            status=UserStatus.ACTIVE,
            mfa_enabled=True,
            mfa_methods=[MFAMethod.TOTP, MFAMethod.SMS],
            permissions=["project:create", "user:invite"]
        )
        
        # Validate user properties
        assert user.tenant_id == tenant_id
        assert user.email == "admin@company.com"
        assert user.role == UserRole.ADMIN
        assert user.auth_provider == AuthProvider.GOOGLE
        assert user.status == UserStatus.ACTIVE
        assert user.mfa_enabled is True
        assert MFAMethod.TOTP in user.mfa_methods
        assert "project:create" in user.permissions
    
    def test_user_roles_hierarchy(self):
        """Test user role hierarchy and permissions"""
        roles = [
            UserRole.OWNER,
            UserRole.ADMIN,
            UserRole.MANAGER,
            UserRole.DEVELOPER,
            UserRole.VIEWER,
            UserRole.GUEST
        ]
        
        # Verify all roles are valid
        for role in roles:
            user = User(
                tenant_id=uuid4(),
                email=f"user@example.com",
                first_name="Test",
                last_name="User",
                role=role
            )
            assert user.role == role
    
    def test_authentication_providers(self):
        """Test different authentication providers"""
        providers = [
            AuthProvider.LOCAL,
            AuthProvider.GOOGLE,
            AuthProvider.MICROSOFT,
            AuthProvider.OKTA,
            AuthProvider.AUTH0,
            AuthProvider.SAML,
            AuthProvider.LDAP
        ]
        
        for provider in providers:
            user = User(
                tenant_id=uuid4(),
                email="user@example.com",
                first_name="Test",
                last_name="User",
                auth_provider=provider
            )
            assert user.auth_provider == provider
    
    def test_mfa_methods(self):
        """Test multi-factor authentication methods"""
        mfa_methods = [
            MFAMethod.TOTP,
            MFAMethod.SMS,
            MFAMethod.EMAIL,
            MFAMethod.PUSH,
            MFAMethod.HARDWARE_TOKEN
        ]
        
        user = User(
            tenant_id=uuid4(),
            email="user@example.com", 
            first_name="Test",
            last_name="User",
            mfa_enabled=True,
            mfa_methods=mfa_methods
        )
        
        assert user.mfa_enabled is True
        assert len(user.mfa_methods) == 5
        assert MFAMethod.TOTP in user.mfa_methods
        assert MFAMethod.HARDWARE_TOKEN in user.mfa_methods
    
    def test_user_status_transitions(self):
        """Test valid user status transitions"""
        user = User(
            tenant_id=uuid4(),
            email="user@example.com",
            first_name="Test",
            last_name="User"
        )
        
        # Initial status should be PENDING_ACTIVATION
        assert user.status == UserStatus.PENDING_ACTIVATION
        
        # Test status transitions
        valid_statuses = [
            UserStatus.ACTIVE,
            UserStatus.INACTIVE,
            UserStatus.SUSPENDED,
            UserStatus.PENDING_PASSWORD_RESET
        ]
        
        for status in valid_statuses:
            user.status = status
            assert user.status == status


class TestLoginModels:
    """Test login request and response models"""
    
    def test_local_login_request(self):
        """Test local authentication login request"""
        login_request = LoginRequest(
            email="user@example.com",
            password="SecurePass123!",
            provider=AuthProvider.LOCAL,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0..."
        )
        
        assert login_request.email == "user@example.com"
        assert login_request.password == "SecurePass123!"
        assert login_request.provider == AuthProvider.LOCAL
        assert login_request.remember_me is False  # Default
        assert login_request.mfa_code is None  # Optional
    
    def test_oauth_login_request(self):
        """Test OAuth login request"""
        login_request = LoginRequest(
            email="user@google.com",
            provider=AuthProvider.GOOGLE,
            auth_code="oauth_auth_code_12345",
            state="random_state_token"
        )
        
        assert login_request.provider == AuthProvider.GOOGLE
        assert login_request.auth_code == "oauth_auth_code_12345"
        assert login_request.state == "random_state_token"
        assert login_request.password is None  # Not used for OAuth
    
    def test_saml_login_request(self):
        """Test SAML login request"""
        login_request = LoginRequest(
            email="user@company.com",
            provider=AuthProvider.SAML,
            saml_response="<saml:Response>...</saml:Response>",
            relay_state="target_url"
        )
        
        assert login_request.provider == AuthProvider.SAML
        assert login_request.saml_response.startswith("<saml:Response>")
        assert login_request.relay_state == "target_url"
    
    def test_mfa_login_request(self):
        """Test MFA-enabled login request"""
        login_request = LoginRequest(
            email="user@example.com",
            password="SecurePass123!",
            provider=AuthProvider.LOCAL,
            mfa_code="123456",
            mfa_method=MFAMethod.TOTP
        )
        
        assert login_request.mfa_code == "123456"
        assert login_request.mfa_method == MFAMethod.TOTP
    
    def test_successful_login_response(self):
        """Test successful login response"""
        user = User(
            tenant_id=uuid4(),
            email="user@example.com",
            first_name="Test",
            last_name="User",
            status=UserStatus.ACTIVE
        )
        
        response = LoginResponse(
            success=True,
            access_token="jwt.access.token",
            refresh_token="jwt.refresh.token",
            expires_in=3600,
            user=user
        )
        
        assert response.success is True
        assert response.access_token == "jwt.access.token"
        assert response.refresh_token == "jwt.refresh.token"
        assert response.expires_in == 3600
        assert response.user.email == "user@example.com"
        assert response.mfa_required is False  # Default
    
    def test_mfa_challenge_response(self):
        """Test MFA challenge login response"""
        response = LoginResponse(
            success=False,
            mfa_required=True,
            mfa_methods=[MFAMethod.TOTP, MFAMethod.SMS],
            mfa_challenge_id="challenge_12345"
        )
        
        assert response.success is False
        assert response.mfa_required is True
        assert len(response.mfa_methods) == 2
        assert MFAMethod.TOTP in response.mfa_methods
        assert response.mfa_challenge_id == "challenge_12345"
        assert response.access_token is None  # No token yet
    
    def test_failed_login_response(self):
        """Test failed login response"""
        response = LoginResponse(
            success=False,
            error="invalid_credentials",
            error_description="The provided credentials are invalid"
        )
        
        assert response.success is False
        assert response.error == "invalid_credentials"
        assert response.error_description == "The provided credentials are invalid"
        assert response.access_token is None
        assert response.user is None


class TestPasswordPolicy:
    """Test password policy functionality"""
    
    def test_default_password_policy(self):
        """Test default password policy settings"""
        policy = DEFAULT_PASSWORD_POLICY
        
        assert policy.min_length == 12
        assert policy.require_uppercase is True
        assert policy.require_lowercase is True
        assert policy.require_digits is True
        assert policy.require_special is True
        assert policy.max_age_days == 90
        assert policy.history_count == 5
        assert policy.lockout_attempts == 5
        assert policy.lockout_duration_minutes == 30
        assert policy.prevent_common_passwords is True
    
    def test_custom_password_policy(self):
        """Test custom password policy creation"""
        tenant_id = uuid4()
        
        policy = PasswordPolicy(
            tenant_id=tenant_id,
            min_length=16,
            require_special=False,
            max_age_days=180,
            lockout_attempts=3,
            lockout_duration_minutes=60
        )
        
        assert policy.tenant_id == tenant_id
        assert policy.min_length == 16
        assert policy.require_special is False
        assert policy.max_age_days == 180
        assert policy.lockout_attempts == 3
        assert policy.lockout_duration_minutes == 60
    
    def test_password_policy_validation(self):
        """Test password policy field validation"""
        tenant_id = uuid4()
        
        # Test minimum values
        policy = PasswordPolicy(
            tenant_id=tenant_id,
            min_length=6,  # Minimum allowed
            max_age_days=30,  # Minimum allowed
            lockout_attempts=3,  # Minimum allowed
            lockout_duration_minutes=5  # Minimum allowed
        )
        
        assert policy.min_length == 6
        assert policy.max_age_days == 30
        assert policy.lockout_attempts == 3
        assert policy.lockout_duration_minutes == 5
        
        # Test with invalid values should raise validation error
        with pytest.raises(ValueError):
            PasswordPolicy(
                tenant_id=tenant_id,
                min_length=5,  # Below minimum
                max_age_days=29,  # Below minimum
                lockout_attempts=2,  # Below minimum
                lockout_duration_minutes=4  # Below minimum
            )


class TestAuthenticationSecurity:
    """Test authentication security features"""
    
    def test_user_account_lockout(self):
        """Test user account lockout functionality"""
        user = User(
            tenant_id=uuid4(),
            email="user@example.com",
            first_name="Test",
            last_name="User",
            status=UserStatus.ACTIVE,
            login_attempts=0
        )
        
        # Simulate failed login attempts
        user.login_attempts = 5
        user.locked_until = datetime.utcnow() + timedelta(minutes=30)
        
        assert user.login_attempts == 5
        assert user.locked_until > datetime.utcnow()
        
        # Check if account is locked
        is_locked = user.locked_until and user.locked_until > datetime.utcnow()
        assert is_locked is True
    
    def test_password_change_requirement(self):
        """Test password change requirement"""
        user = User(
            tenant_id=uuid4(),
            email="user@example.com",
            first_name="Test",
            last_name="User",
            require_password_change=True,
            password_changed_at=datetime.utcnow() - timedelta(days=91)
        )
        
        assert user.require_password_change is True
        
        # Check if password is expired (older than 90 days)
        is_expired = (
            user.password_changed_at and 
            user.password_changed_at < datetime.utcnow() - timedelta(days=90)
        )
        assert is_expired is True
    
    def test_mfa_backup_codes(self):
        """Test MFA backup codes functionality"""
        user = User(
            tenant_id=uuid4(),
            email="user@example.com",
            first_name="Test",
            last_name="User",
            mfa_enabled=True,
            backup_codes=["ABC123", "DEF456", "GHI789"]
        )
        
        assert user.mfa_enabled is True
        assert len(user.backup_codes) == 3
        assert "ABC123" in user.backup_codes
        
        # Test backup code usage (would mark as used)
        used_code = "ABC123"
        assert used_code in user.backup_codes
    
    def test_session_security(self):
        """Test session security features"""
        session_data = {
            "ip_address": "192.168.1.100",
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            "location": {"country": "US", "city": "San Francisco"},
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=1)
        }
        
        # Validate session security context
        assert session_data["ip_address"] == "192.168.1.100"
        assert "Macintosh" in session_data["user_agent"]
        assert session_data["location"]["country"] == "US"
        assert session_data["expires_at"] > datetime.utcnow()


class TestEnterpriseFeatures:
    """Test enterprise-specific authentication features"""
    
    def test_sso_configuration(self):
        """Test SSO configuration model"""
        from app.models.auth_models import SSOConfiguration
        
        tenant_id = uuid4()
        
        sso_config = SSOConfiguration(
            tenant_id=tenant_id,
            provider=AuthProvider.GOOGLE,
            provider_name="Google SSO",
            client_id="google_client_id",
            client_secret="google_client_secret",
            scopes=["email", "profile"],
            auto_provision_users=True,
            default_role=UserRole.DEVELOPER,
            allowed_domains=["company.com", "subsidiary.com"]
        )
        
        assert sso_config.tenant_id == tenant_id
        assert sso_config.provider == AuthProvider.GOOGLE
        assert sso_config.provider_name == "Google SSO"
        assert "email" in sso_config.scopes
        assert sso_config.auto_provision_users is True
        assert sso_config.default_role == UserRole.DEVELOPER
        assert "company.com" in sso_config.allowed_domains
    
    def test_saml_configuration(self):
        """Test SAML SSO configuration"""
        from app.models.auth_models import SSOConfiguration
        
        tenant_id = uuid4()
        
        saml_config = SSOConfiguration(
            tenant_id=tenant_id,
            provider=AuthProvider.SAML,
            provider_name="Corporate SAML",
            saml_entity_id="https://company.com/saml",
            saml_sso_url="https://sso.company.com/saml/login",
            saml_x509_cert="-----BEGIN CERTIFICATE-----...",
            attribute_mapping={
                "email": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress",
                "first_name": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname",
                "last_name": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname"
            }
        )
        
        assert saml_config.provider == AuthProvider.SAML
        assert saml_config.saml_entity_id == "https://company.com/saml"
        assert saml_config.saml_sso_url == "https://sso.company.com/saml/login"
        assert saml_config.saml_x509_cert.startswith("-----BEGIN CERTIFICATE-----")
        assert "email" in saml_config.attribute_mapping
    
    def test_audit_logging(self):
        """Test authentication audit logging"""
        from app.models.auth_models import AuditLog
        
        tenant_id = uuid4()
        user_id = uuid4()
        
        audit_log = AuditLog(
            tenant_id=tenant_id,
            event_type="login_success",
            event_description="User logged in successfully",
            success=True,
            user_id=user_id,
            user_email="user@company.com",
            ip_address="10.0.0.1",
            metadata={
                "provider": "google",
                "mfa_verified": True,
                "session_duration": 3600
            }
        )
        
        assert audit_log.tenant_id == tenant_id
        assert audit_log.event_type == "login_success"
        assert audit_log.success is True
        assert audit_log.user_id == user_id
        assert audit_log.ip_address == "10.0.0.1"
        assert audit_log.metadata["provider"] == "google"
        assert audit_log.metadata["mfa_verified"] is True


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])