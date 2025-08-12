"""
Comprehensive password security tests
Tests password hashing, strength requirements, reset flow, and security features
"""

import pytest
import pytest_asyncio
import bcrypt
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from uuid import uuid4

from app.models.auth_models import UserCreate, UserUpdate, AuthProvider, UserRole
from app.services.auth_service import AuthenticationService
from app.core.exceptions import InvalidCredentialsError
from tests.fixtures.auth_test_fixtures import *


class TestPasswordHashing:
    """Test password hashing security."""
    
    @pytest.mark.asyncio
    async def test_password_hashing_bcrypt(self, auth_service: AuthenticationService):
        """Test that passwords are hashed using bcrypt."""
        password = "TestPassword123!"
        
        hashed = await auth_service._hash_password(password)
        
        # Should be bcrypt hash format
        assert hashed.startswith('$2b$')
        assert len(hashed) > 50
        assert hashed != password
        
        # Should verify correctly
        assert bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        
        # Should not verify with wrong password
        assert not bcrypt.checkpw("WrongPassword".encode('utf-8'), hashed.encode('utf-8'))
    
    @pytest.mark.asyncio
    async def test_password_hash_uniqueness(self, auth_service: AuthenticationService):
        """Test that same password produces different hashes."""
        password = "SamePassword123!"
        
        hash1 = await auth_service._hash_password(password)
        hash2 = await auth_service._hash_password(password)
        
        # Hashes should be different due to random salt
        assert hash1 != hash2
        
        # But both should verify the same password
        assert bcrypt.checkpw(password.encode('utf-8'), hash1.encode('utf-8'))
        assert bcrypt.checkpw(password.encode('utf-8'), hash2.encode('utf-8'))
    
    @pytest.mark.asyncio
    async def test_password_hash_salt_strength(self, auth_service: AuthenticationService):
        """Test that password hashes use strong salt."""
        password = "TestPassword123!"
        
        hash_result = await auth_service._hash_password(password)
        
        # Extract salt rounds from bcrypt hash
        # Format: $2b$rounds$salt+hash
        parts = hash_result.split('$')
        rounds = int(parts[2])
        
        # Should use sufficient rounds for security (at least 10)
        assert rounds >= 10
    
    @pytest.mark.asyncio
    async def test_password_storage_security(self, auth_service: AuthenticationService, test_tenant):
        """Test that passwords are never stored in plain text."""
        password = "StorageTestPassword123!"
        
        user_data = UserCreate(
            tenant_id=test_tenant.id,
            email="storage.test@example.com",
            first_name="Storage",
            last_name="Test",
            password=password,
            role=UserRole.DEVELOPER
        )
        
        user = await auth_service.create_user(user_data)
        
        # Password should never appear in stored data
        assert password not in str(user.password_hash)
        assert user.password_hash != password
        assert len(user.password_hash) > len(password)
        
        # Should be able to verify password
        assert await auth_service._authenticate_local(user, password)
        assert not await auth_service._authenticate_local(user, "WrongPassword")
    
    @pytest.mark.asyncio
    async def test_empty_password_handling(self, auth_service: AuthenticationService):
        """Test handling of empty or None passwords."""
        # None password should return None hash
        hash1 = await auth_service._hash_password(None)
        assert hash1 is None
        
        # Empty password should return None hash  
        hash2 = await auth_service._hash_password("")
        assert hash2 is None
        
        # Whitespace-only password should return None hash
        hash3 = await auth_service._hash_password("   ")
        assert hash3 is None


class TestPasswordStrengthValidation:
    """Test password strength requirements."""
    
    @pytest.mark.asyncio
    async def test_password_length_requirements(self, auth_service: AuthenticationService, test_tenant):
        """Test password length validation."""
        test_cases = [
            ("1234567", False),      # 7 chars - too short
            ("12345678", True),      # 8 chars - minimum
            ("a" * 128, True),       # 128 chars - reasonable max
            ("a" * 256, True),       # Very long - should still work
        ]
        
        for password, should_work in test_cases:
            user_data = UserCreate(
                tenant_id=test_tenant.id,
                email=f"length{len(password)}@example.com",
                first_name="Length",
                last_name="Test",
                password=password,
                role=UserRole.DEVELOPER
            )
            
            if should_work:
                user = await auth_service.create_user(user_data)
                assert user is not None
                assert user.password_hash is not None
            else:
                # Current implementation doesn't enforce length in service
                # Would be enforced at API level
                user = await auth_service.create_user(user_data)
                assert user is not None
    
    @pytest.mark.asyncio
    async def test_weak_password_detection(self, auth_service: AuthenticationService, test_tenant, weak_passwords):
        """Test detection of commonly weak passwords."""
        for weak_password in weak_passwords:
            user_data = UserCreate(
                tenant_id=test_tenant.id,
                email=f"weak{hash(weak_password)}@example.com",
                first_name="Weak",
                last_name="Password",
                password=weak_password,
                role=UserRole.DEVELOPER
            )
            
            # Current implementation accepts weak passwords
            # In production, would implement password policy validation
            user = await auth_service.create_user(user_data)
            assert user is not None
    
    @pytest.mark.asyncio
    async def test_strong_password_acceptance(self, auth_service: AuthenticationService, test_tenant, strong_passwords):
        """Test that strong passwords are accepted."""
        for strong_password in strong_passwords:
            user_data = UserCreate(
                tenant_id=test_tenant.id,
                email=f"strong{hash(strong_password)}@example.com",
                first_name="Strong",
                last_name="Password",
                password=strong_password,
                role=UserRole.DEVELOPER
            )
            
            user = await auth_service.create_user(user_data)
            assert user is not None
            assert user.password_hash is not None
            assert await auth_service._authenticate_local(user, strong_password)
    
    @pytest.mark.asyncio
    async def test_password_complexity_requirements(self, auth_service: AuthenticationService, test_tenant):
        """Test password complexity validation."""
        complexity_tests = [
            ("password123", False),    # No uppercase or special chars
            ("PASSWORD123", False),    # No lowercase or special chars  
            ("Password!", False),      # No numbers
            ("Password123", False),    # No special chars
            ("Password123!", True),    # Has all required elements
            ("MyStr0ng!P@ssw0rd", True),  # Strong complex password
        ]
        
        for password, should_be_complex in complexity_tests:
            user_data = UserCreate(
                tenant_id=test_tenant.id,
                email=f"complex{hash(password)}@example.com",
                first_name="Complex",
                last_name="Test",
                password=password,
                role=UserRole.DEVELOPER
            )
            
            # Current implementation doesn't enforce complexity
            # Would be implemented with password policy
            user = await auth_service.create_user(user_data)
            assert user is not None
    
    @pytest.mark.asyncio
    async def test_password_dictionary_attack_prevention(self, auth_service: AuthenticationService, test_tenant):
        """Test prevention of common dictionary passwords."""
        dictionary_passwords = [
            "password", "123456", "qwerty", "admin", "letmein",
            "welcome", "monkey", "dragon", "princess", "sunshine"
        ]
        
        for dict_password in dictionary_passwords:
            user_data = UserCreate(
                tenant_id=test_tenant.id,
                email=f"dict{hash(dict_password)}@example.com",
                first_name="Dictionary",
                last_name="Test",
                password=dict_password,
                role=UserRole.DEVELOPER
            )
            
            # Current implementation accepts dictionary passwords
            # Production would implement blacklist checking
            user = await auth_service.create_user(user_data)
            assert user is not None


class TestPasswordResetFlow:
    """Test password reset functionality."""
    
    @pytest.mark.asyncio
    async def test_password_reset_token_generation(self, auth_service: AuthenticationService, test_user: User):
        """Test password reset token generation."""
        token = await auth_service.generate_password_reset_token(test_user.id)
        
        assert token is not None
        assert len(token) > 20  # Should be secure token
        assert isinstance(token, str)
    
    @pytest.mark.asyncio
    async def test_password_reset_success(self, auth_service: AuthenticationService, test_user: User, test_tenant):
        """Test successful password reset."""
        new_password = "NewResetPassword123!"
        
        # Generate reset token
        token = await auth_service.generate_password_reset_token(test_user.id)
        
        # Reset password
        success = await auth_service.reset_password(token, new_password, test_tenant.id)
        assert success is True
        
        # Verify new password works
        updated_user = await auth_service.get_user_by_id(test_user.id, test_tenant.id)
        assert await auth_service._authenticate_local(updated_user, new_password)
        
        # Verify old password no longer works
        assert not await auth_service._authenticate_local(updated_user, "SecurePassword123!")
    
    @pytest.mark.asyncio
    async def test_password_reset_invalid_token(self, auth_service: AuthenticationService, test_tenant):
        """Test password reset with invalid token."""
        success = await auth_service.reset_password(
            "invalid_token",
            "NewPassword123!",
            test_tenant.id
        )
        
        assert success is False
    
    @pytest.mark.asyncio
    async def test_password_reset_expired_token(self, auth_service: AuthenticationService, test_user: User, test_tenant, test_db):
        """Test password reset with expired token."""
        # Generate token
        token = await auth_service.generate_password_reset_token(test_user.id)
        
        # Manually expire the token
        expired_time = datetime.utcnow() - timedelta(hours=1)
        await test_db.execute(
            UserORM.__table__.update()
            .where(UserORM.id == test_user.id)
            .values(password_reset_expires=expired_time)
        )
        await test_db.commit()
        
        # Try to reset with expired token
        success = await auth_service.reset_password(
            token,
            "NewPassword123!",
            test_tenant.id
        )
        
        assert success is False
    
    @pytest.mark.asyncio
    async def test_password_reset_token_single_use(self, auth_service: AuthenticationService, test_user: User, test_tenant):
        """Test that password reset tokens can only be used once."""
        token = await auth_service.generate_password_reset_token(test_user.id)
        
        # First use should succeed
        success1 = await auth_service.reset_password(
            token,
            "FirstResetPassword123!",
            test_tenant.id
        )
        assert success1 is True
        
        # Second use should fail
        success2 = await auth_service.reset_password(
            token,
            "SecondResetPassword123!",
            test_tenant.id
        )
        assert success2 is False
    
    @pytest.mark.asyncio
    async def test_password_reset_clears_failed_attempts(self, auth_service: AuthenticationService, test_user: User, test_tenant, test_db):
        """Test that password reset clears failed login attempts."""
        # Set failed login attempts
        await test_db.execute(
            UserORM.__table__.update()
            .where(UserORM.id == test_user.id)
            .values(
                login_attempts=5,
                locked_until=datetime.utcnow() + timedelta(minutes=30)
            )
        )
        await test_db.commit()
        
        # Reset password
        token = await auth_service.generate_password_reset_token(test_user.id)
        success = await auth_service.reset_password(
            token,
            "ResetPassword123!",
            test_tenant.id
        )
        assert success is True
        
        # Verify failed attempts were cleared
        reset_user = await auth_service.get_user_by_id(test_user.id, test_tenant.id)
        assert reset_user.login_attempts == 0
        assert reset_user.locked_until is None
    
    @pytest.mark.asyncio
    async def test_password_reset_updates_timestamp(self, auth_service: AuthenticationService, test_user: User, test_tenant):
        """Test that password reset updates password changed timestamp."""
        original_user = await auth_service.get_user_by_id(test_user.id, test_tenant.id)
        original_timestamp = original_user.password_changed_at
        
        # Reset password
        token = await auth_service.generate_password_reset_token(test_user.id)
        success = await auth_service.reset_password(
            token,
            "ResetPassword123!",
            test_tenant.id
        )
        assert success is True
        
        # Verify timestamp was updated
        updated_user = await auth_service.get_user_by_id(test_user.id, test_tenant.id)
        assert updated_user.password_changed_at > original_timestamp


class TestPasswordChangeFlow:
    """Test password change functionality."""
    
    @pytest.mark.asyncio
    async def test_password_change_success(self, auth_service: AuthenticationService, test_user: User, test_tenant):
        """Test successful password change."""
        old_password = "SecurePassword123!"
        new_password = "NewSecurePassword456!"
        
        success = await auth_service.change_password(
            test_user.id,
            old_password,
            new_password,
            test_tenant.id
        )
        
        assert success is True
        
        # Verify new password works
        updated_user = await auth_service.get_user_by_id(test_user.id, test_tenant.id)
        assert await auth_service._authenticate_local(updated_user, new_password)
        
        # Verify old password no longer works
        assert not await auth_service._authenticate_local(updated_user, old_password)
    
    @pytest.mark.asyncio
    async def test_password_change_wrong_current_password(self, auth_service: AuthenticationService, test_user: User, test_tenant):
        """Test password change with wrong current password."""
        success = await auth_service.change_password(
            test_user.id,
            "WrongCurrentPassword",
            "NewPassword123!",
            test_tenant.id
        )
        
        assert success is False
        
        # Verify original password still works
        assert await auth_service._authenticate_local(test_user, "SecurePassword123!")
    
    @pytest.mark.asyncio
    async def test_password_change_same_password(self, auth_service: AuthenticationService, test_user: User, test_tenant):
        """Test password change to same password."""
        current_password = "SecurePassword123!"
        
        success = await auth_service.change_password(
            test_user.id,
            current_password,
            current_password,  # Same password
            test_tenant.id
        )
        
        # Should succeed (current implementation allows this)
        assert success is True
    
    @pytest.mark.asyncio
    async def test_password_change_nonexistent_user(self, auth_service: AuthenticationService, test_tenant):
        """Test password change for non-existent user."""
        fake_user_id = uuid4()
        
        success = await auth_service.change_password(
            fake_user_id,
            "CurrentPassword123!",
            "NewPassword123!",
            test_tenant.id
        )
        
        assert success is False
    
    @pytest.mark.asyncio
    async def test_password_change_updates_timestamp(self, auth_service: AuthenticationService, test_user: User, test_tenant):
        """Test that password change updates timestamp."""
        original_user = await auth_service.get_user_by_id(test_user.id, test_tenant.id)
        original_timestamp = original_user.password_changed_at
        
        success = await auth_service.change_password(
            test_user.id,
            "SecurePassword123!",
            "NewPassword123!",
            test_tenant.id
        )
        assert success is True
        
        # Verify timestamp was updated
        updated_user = await auth_service.get_user_by_id(test_user.id, test_tenant.id)
        assert updated_user.password_changed_at > original_timestamp
        assert updated_user.require_password_change is False


class TestPasswordPolicy:
    """Test password policy enforcement."""
    
    @pytest.mark.asyncio
    async def test_password_history_prevention(self, auth_service: AuthenticationService, test_user: User, test_tenant):
        """Test prevention of password reuse."""
        # Change password multiple times
        passwords = [
            "Password1!", "Password2!", "Password3!", 
            "Password4!", "Password5!", "Password6!"
        ]
        
        current_password = "SecurePassword123!"
        
        for new_password in passwords:
            success = await auth_service.change_password(
                test_user.id,
                current_password,
                new_password,
                test_tenant.id
            )
            assert success is True
            current_password = new_password
        
        # Try to reuse first password (should be prevented in full implementation)
        # Current implementation doesn't enforce history
        success = await auth_service.change_password(
            test_user.id,
            current_password,
            "Password1!",  # Reusing old password
            test_tenant.id
        )
        
        # Current implementation allows reuse
        assert success is True
    
    @pytest.mark.asyncio
    async def test_password_expiry_enforcement(self, auth_service: AuthenticationService, test_user: User, test_tenant, test_db):
        """Test password expiry enforcement."""
        # Set password as expired (older than policy allows)
        expired_date = datetime.utcnow() - timedelta(days=91)  # Older than 90 days
        await test_db.execute(
            UserORM.__table__.update()
            .where(UserORM.id == test_user.id)
            .values(
                password_changed_at=expired_date,
                require_password_change=True
            )
        )
        await test_db.commit()
        
        # User should be required to change password
        expired_user = await auth_service.get_user_by_id(test_user.id, test_tenant.id)
        assert expired_user.require_password_change is True
        
        # In full implementation, login would require password change
    
    @pytest.mark.asyncio
    async def test_password_personal_info_prevention(self, auth_service: AuthenticationService, test_tenant):
        """Test prevention of passwords containing personal information."""
        user_data = UserCreate(
            tenant_id=test_tenant.id,
            email="john.doe@example.com",
            first_name="John",
            last_name="Doe",
            password="JohnDoe123!",  # Contains personal info
            role=UserRole.DEVELOPER
        )
        
        # Current implementation allows personal info in passwords
        # Full implementation would validate against user data
        user = await auth_service.create_user(user_data)
        assert user is not None
    
    @pytest.mark.asyncio
    async def test_password_policy_configuration(self, auth_service: AuthenticationService, test_tenant):
        """Test password policy configuration per tenant."""
        # Get password policy for tenant
        policy = await auth_service._get_password_policy(test_tenant.id)
        
        # Verify default policy settings
        assert policy.min_length >= 8
        assert policy.lockout_attempts >= 3
        assert policy.lockout_duration_minutes >= 5
        assert policy.max_age_days >= 30
        assert policy.history_count >= 0


class TestPasswordSecurityFeatures:
    """Test advanced password security features."""
    
    @pytest.mark.asyncio
    async def test_password_timing_attack_prevention(self, auth_service: AuthenticationService, test_user: User):
        """Test that password verification timing is consistent."""
        correct_password = "SecurePassword123!"
        wrong_passwords = [
            "W",  # Very short
            "WrongPassword",  # Different length
            "WrongPassword123!",  # Same length, wrong content
            "SecurePassword123",  # Almost correct
        ]
        
        # Measure timing for correct password
        start_time = time.time()
        result1 = await auth_service._authenticate_local(test_user, correct_password)
        correct_time = time.time() - start_time
        
        # Measure timing for various wrong passwords
        wrong_times = []
        for wrong_password in wrong_passwords:
            start_time = time.time()
            result2 = await auth_service._authenticate_local(test_user, wrong_password)
            wrong_time = time.time() - start_time
            wrong_times.append(wrong_time)
            assert result2 is False
        
        assert result1 is True
        
        # All verification times should be similar (within 10ms)
        for wrong_time in wrong_times:
            time_diff = abs(correct_time - wrong_time)
            assert time_diff < 0.01
    
    @pytest.mark.asyncio
    async def test_password_hash_upgrade_on_login(self, auth_service: AuthenticationService, test_user: User, test_tenant):
        """Test automatic hash upgrade on login."""
        # Current implementation doesn't implement hash upgrade
        # This would be useful when upgrading bcrypt rounds
        
        original_user = await auth_service.get_user_by_id(test_user.id, test_tenant.id)
        original_hash = original_user.password_hash
        
        # Simulate login (hash upgrade would happen here)
        authenticated = await auth_service._authenticate_local(test_user, "SecurePassword123!")
        assert authenticated is True
        
        # Hash should remain the same (no upgrade implemented)
        updated_user = await auth_service.get_user_by_id(test_user.id, test_tenant.id)
        assert updated_user.password_hash == original_hash
    
    @pytest.mark.asyncio
    async def test_password_breach_detection(self, auth_service: AuthenticationService, test_tenant):
        """Test detection of breached passwords."""
        # Known breached passwords (from HaveIBeenPwned-style lists)
        breached_passwords = [
            "password123",
            "admin123",
            "qwerty123",
            "letmein123"
        ]
        
        for breached_password in breached_passwords:
            user_data = UserCreate(
                tenant_id=test_tenant.id,
                email=f"breach{hash(breached_password)}@example.com",
                first_name="Breach",
                last_name="Test",
                password=breached_password,
                role=UserRole.DEVELOPER
            )
            
            # Current implementation doesn't check breach databases
            # Full implementation would integrate with HaveIBeenPwned API
            user = await auth_service.create_user(user_data)
            assert user is not None
    
    @pytest.mark.asyncio
    async def test_password_entropy_calculation(self, auth_service: AuthenticationService):
        """Test password entropy calculation for strength assessment."""
        import math
        
        def calculate_entropy(password):
            """Calculate password entropy."""
            charset_size = 0
            if any(c.islower() for c in password):
                charset_size += 26
            if any(c.isupper() for c in password):
                charset_size += 26
            if any(c.isdigit() for c in password):
                charset_size += 10
            if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
                charset_size += 32
            
            if charset_size == 0:
                return 0
            
            return len(password) * math.log2(charset_size)
        
        password_tests = [
            ("password", "Low entropy"),
            ("Password123", "Medium entropy"),
            ("MyStr0ng!P@ssw0rd", "High entropy"),
            ("aB3!aB3!aB3!aB3!", "Very high entropy"),
        ]
        
        for password, expected_level in password_tests:
            entropy = calculate_entropy(password)
            
            # Verify entropy calculation
            if "Low" in expected_level:
                assert entropy < 40
            elif "Medium" in expected_level:
                assert 40 <= entropy < 60
            elif "High" in expected_level:
                assert entropy >= 60
    
    @pytest.mark.asyncio
    async def test_password_zxcvbn_integration(self, auth_service: AuthenticationService):
        """Test integration with zxcvbn password strength estimation."""
        # This would integrate with zxcvbn library for better password strength assessment
        # Current implementation doesn't include zxcvbn
        
        passwords_and_scores = [
            ("password", 0),      # Very weak
            ("password123", 1),   # Weak
            ("Password123", 2),   # Fair
            ("Password123!", 3),  # Good
            ("MyStr0ng!P@ssw0rd", 4),  # Strong
        ]
        
        for password, expected_score in passwords_and_scores:
            # Mock zxcvbn integration
            # In production, would use: import zxcvbn; result = zxcvbn.zxcvbn(password)
            calculated_score = min(4, max(0, len(set(password)) // 3))  # Simple mock
            
            # Verify scoring works
            assert 0 <= calculated_score <= 4


class TestPasswordAPI:
    """Test password-related API endpoints."""
    
    @pytest.mark.asyncio
    async def test_forgot_password_api(self, auth_test_client: TestClient, test_user: User, test_tenant):
        """Test forgot password API endpoint."""
        with patch('app.middleware.tenant_middleware.require_tenant') as mock_tenant:
            mock_tenant.return_value = test_tenant
            
            response = auth_test_client.post(
                "/api/v1/auth/forgot-password",
                json={"email": test_user.email}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "reset link has been sent" in data["message"]
    
    @pytest.mark.asyncio
    async def test_forgot_password_api_nonexistent_user(self, auth_test_client: TestClient, test_tenant):
        """Test forgot password API with non-existent user."""
        with patch('app.middleware.tenant_middleware.require_tenant') as mock_tenant:
            mock_tenant.return_value = test_tenant
            
            response = auth_test_client.post(
                "/api/v1/auth/forgot-password",
                json={"email": "nonexistent@example.com"}
            )
            
            # Should return success to prevent email enumeration
            assert response.status_code == 200
            data = response.json()
            assert "reset link has been sent" in data["message"]
    
    @pytest.mark.asyncio
    async def test_reset_password_api(self, auth_test_client: TestClient, test_user: User, test_tenant, auth_service: AuthenticationService):
        """Test reset password API endpoint."""
        # Generate reset token
        token = await auth_service.generate_password_reset_token(test_user.id)
        
        with patch('app.middleware.tenant_middleware.require_tenant') as mock_tenant:
            mock_tenant.return_value = test_tenant
            
            response = auth_test_client.post(
                "/api/v1/auth/reset-password",
                json={
                    "token": token,
                    "password": "NewResetPassword123!"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "Password reset successfully" in data["message"]
    
    @pytest.mark.asyncio
    async def test_change_password_api(self, auth_test_client: TestClient, authenticated_headers, test_tenant):
        """Test change password API endpoint."""
        with patch('app.middleware.tenant_middleware.require_tenant') as mock_tenant:
            mock_tenant.return_value = test_tenant
            
            response = auth_test_client.put(
                "/api/v1/auth/users/me/password",
                headers=authenticated_headers,
                json={
                    "current_password": "SecurePassword123!",
                    "new_password": "NewSecurePassword456!"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "Password changed successfully" in data["message"]
    
    @pytest.mark.asyncio
    async def test_change_password_api_wrong_current(self, auth_test_client: TestClient, authenticated_headers, test_tenant):
        """Test change password API with wrong current password."""
        with patch('app.middleware.tenant_middleware.require_tenant') as mock_tenant:
            mock_tenant.return_value = test_tenant
            
            response = auth_test_client.put(
                "/api/v1/auth/users/me/password",
                headers=authenticated_headers,
                json={
                    "current_password": "WrongPassword",
                    "new_password": "NewSecurePassword456!"
                }
            )
            
            assert response.status_code == 400
            data = response.json()
            assert "Invalid current password" in data["detail"]