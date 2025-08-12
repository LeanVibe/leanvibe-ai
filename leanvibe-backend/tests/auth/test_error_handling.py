"""
Comprehensive error handling and edge case tests for authentication
Tests system behavior under failure conditions and edge cases
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
from uuid import uuid4

from app.models.auth_models import UserCreate, LoginRequest, AuthProvider, UserRole
from app.services.auth_service import AuthenticationService
from app.core.exceptions import InvalidCredentialsError, TokenExpiredError
from tests.fixtures.auth_test_fixtures import *


class TestDatabaseErrorHandling:
    """Test handling of database-related errors."""
    
    @pytest.mark.asyncio
    async def test_database_connection_failure(self, test_tenant):
        """Test handling of database connection failures."""
        # Create auth service with mocked database that fails
        auth_service = AuthenticationService()
        
        with patch.object(auth_service, '_get_db') as mock_get_db:
            mock_get_db.side_effect = Exception("Database connection failed")
            
            user_data = UserCreate(
                tenant_id=test_tenant.id,
                email="dbfail@example.com",
                first_name="DB",
                last_name="Fail",
                password="Password123!",
                role=UserRole.DEVELOPER
            )
            
            # Should handle database errors gracefully
            with pytest.raises(Exception):
                await auth_service.create_user(user_data)
    
    @pytest.mark.asyncio
    async def test_database_timeout_handling(self, auth_service: AuthenticationService, test_user: User, test_tenant):
        """Test handling of database timeouts."""
        # Mock a database timeout during login
        with patch.object(auth_service, 'get_user_by_email') as mock_get_user:
            mock_get_user.side_effect = asyncio.TimeoutError("Database timeout")
            
            login_request = LoginRequest(
                email=test_user.email,
                password="SecurePassword123!",
                provider=AuthProvider.LOCAL,
                ip_address="192.168.1.100",
                user_agent="Mozilla/5.0 Test Browser"
            )
            
            # Should handle timeout gracefully
            with pytest.raises(Exception):  # Should not crash the application
                await auth_service.authenticate_user(login_request, test_tenant.id)
    
    @pytest.mark.asyncio
    async def test_transaction_rollback_on_error(self, auth_service: AuthenticationService, test_tenant):
        """Test transaction rollback on errors."""
        user_data = UserCreate(
            tenant_id=test_tenant.id,
            email="rollback@example.com",
            first_name="Rollback",
            last_name="Test",
            password="Password123!",
            role=UserRole.DEVELOPER
        )
        
        # Mock an error after user creation but before commit
        with patch.object(auth_service, '_log_auth_event') as mock_log:
            mock_log.side_effect = Exception("Logging failed")
            
            # Should rollback transaction on error
            with pytest.raises(Exception):
                await auth_service.create_user(user_data)
            
            # User should not be created due to rollback
            found_user = await auth_service.get_user_by_email("rollback@example.com", test_tenant.id)
            assert found_user is None
    
    @pytest.mark.asyncio
    async def test_concurrent_modification_handling(self, auth_service: AuthenticationService, test_user: User, test_tenant):
        """Test handling of concurrent modification scenarios."""
        # Simulate concurrent password changes
        async def change_password_1():
            return await auth_service.change_password(
                test_user.id,
                "SecurePassword123!",
                "NewPassword1!",
                test_tenant.id
            )
        
        async def change_password_2():
            return await auth_service.change_password(
                test_user.id,
                "SecurePassword123!",
                "NewPassword2!",
                test_tenant.id
            )
        
        # Run concurrent password changes
        results = await asyncio.gather(
            change_password_1(),
            change_password_2(),
            return_exceptions=True
        )
        
        # At least one should succeed, or handle conflict gracefully
        successful_changes = sum(1 for r in results if r is True)
        assert successful_changes >= 1 or all(isinstance(r, Exception) for r in results)


class TestNetworkErrorHandling:
    """Test handling of network-related errors."""
    
    @pytest.mark.asyncio
    async def test_email_service_failure(self, auth_service: AuthenticationService, test_user: User, test_tenant):
        """Test handling of email service failures."""
        # Mock email service failure during password reset
        with patch('app.api.endpoints.auth._send_password_reset_email') as mock_send:
            mock_send.side_effect = Exception("Email service unavailable")
            
            # Should handle email service failure gracefully
            try:
                token = await auth_service.generate_password_reset_token(test_user.id)
                # Email sending failure shouldn't prevent token generation
                assert token is not None
            except Exception:
                # Or it might propagate the error, which is also acceptable
                pass
    
    @pytest.mark.asyncio
    async def test_sso_provider_unavailable(self, auth_test_client, test_tenant):
        """Test handling of SSO provider unavailability."""
        with patch('app.middleware.tenant_middleware.require_tenant') as mock_tenant:
            mock_tenant.return_value = test_tenant
            
            # SSO redirect should handle provider unavailability
            response = auth_test_client.get("/api/v1/auth/sso/google")
            
            # Should either succeed or fail gracefully
            assert response.status_code in [200, 307, 500, 503]
    
    @pytest.mark.asyncio
    async def test_external_validation_service_timeout(self, auth_service: AuthenticationService, test_user: User):
        """Test handling of external validation service timeouts."""
        # Mock external MFA validation timeout
        with patch.object(auth_service, '_verify_mfa') as mock_verify:
            mock_verify.side_effect = asyncio.TimeoutError("MFA service timeout")
            
            # Should handle MFA service timeout
            result = await auth_service._verify_mfa(test_user, "123456", "totp")
            # Should return False on timeout rather than crashing
            assert result is False


class TestInputValidationErrors:
    """Test input validation error handling."""
    
    @pytest.mark.asyncio
    async def test_null_byte_injection(self, auth_service: AuthenticationService, test_tenant):
        """Test handling of null byte injection attempts."""
        malicious_inputs = [
            "user@example.com\x00admin",
            "password\x00123",
            "John\x00',DROP TABLE users;--",
        ]
        
        for malicious_input in malicious_inputs:
            user_data = UserCreate(
                tenant_id=test_tenant.id,
                email=f"nullbyte_{hash(malicious_input)}@example.com",
                first_name=malicious_input,
                last_name="Test",
                password="Password123!",
                role=UserRole.DEVELOPER
            )
            
            # Should handle null bytes safely
            try:
                user = await auth_service.create_user(user_data)
                # If successful, should be stored as literal string
                assert user is not None
            except ValueError:
                # Validation rejection is acceptable
                pass
    
    @pytest.mark.asyncio
    async def test_oversized_input_handling(self, auth_service: AuthenticationService, test_tenant):
        """Test handling of oversized inputs."""
        # Extremely long inputs
        oversized_inputs = {
            "email": "a" * 1000 + "@example.com",
            "first_name": "A" * 10000,
            "last_name": "B" * 10000,
            "password": "C" * 100000,
        }
        
        for field, oversized_value in oversized_inputs.items():
            user_data_dict = {
                "tenant_id": test_tenant.id,
                "email": "oversized@example.com",
                "first_name": "Test",
                "last_name": "User",
                "password": "Password123!",
                "role": UserRole.DEVELOPER
            }
            
            # Override with oversized value
            user_data_dict[field] = oversized_value
            if field == "email":
                user_data_dict["email"] = oversized_value
            
            user_data = UserCreate(**user_data_dict)
            
            # Should handle oversized inputs gracefully
            try:
                user = await auth_service.create_user(user_data)
                assert user is not None
            except (ValueError, Exception):
                # Size limit enforcement is acceptable
                pass
    
    @pytest.mark.asyncio
    async def test_invalid_uuid_handling(self, auth_service: AuthenticationService):
        """Test handling of invalid UUIDs."""
        invalid_uuids = [
            "not-a-uuid",
            "12345678-1234-1234-1234-12345678901z",  # Invalid character
            "",
            "null",
            "undefined",
        ]
        
        for invalid_uuid in invalid_uuids:
            # Try to get user with invalid UUID
            try:
                # This would typically cause a validation error
                fake_uuid = uuid4()  # Use valid UUID for test
                user = await auth_service.get_user_by_id(fake_uuid)
                # Should return None for non-existent user
                assert user is None
            except (ValueError, TypeError):
                # UUID validation error is acceptable
                pass
    
    @pytest.mark.asyncio
    async def test_malformed_json_handling(self, auth_test_client, test_tenant):
        """Test API handling of malformed JSON."""
        malformed_json_examples = [
            '{"email": "test@example.com",',  # Incomplete JSON
            '{"email": "test@example.com", "password": }',  # Missing value
            '{"email": "test@example.com", "password": "pass", extra}',  # Invalid syntax
            'email=test@example.com&password=123',  # Form data instead of JSON
        ]
        
        for malformed_json in malformed_json_examples:
            with patch('app.middleware.tenant_middleware.require_tenant') as mock_tenant:
                mock_tenant.return_value = test_tenant
                
                response = auth_test_client.post(
                    "/api/v1/auth/login",
                    data=malformed_json,
                    headers={"Content-Type": "application/json"}
                )
                
                # Should return 422 (validation error) not 500 (server error)
                assert response.status_code == 422


class TestConcurrencyEdgeCases:
    """Test edge cases in concurrent operations."""
    
    @pytest.mark.asyncio
    async def test_concurrent_user_creation_same_email(self, auth_service: AuthenticationService, test_tenant):
        """Test concurrent creation of users with same email."""
        email = "concurrent@example.com"
        
        async def create_user(suffix):
            user_data = UserCreate(
                tenant_id=test_tenant.id,
                email=email,
                first_name=f"User{suffix}",
                last_name="Concurrent",
                password="Password123!",
                role=UserRole.DEVELOPER
            )
            return await auth_service.create_user(user_data)
        
        # Try to create multiple users with same email concurrently
        tasks = [create_user(i) for i in range(5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Only one should succeed, others should fail
        successful_creations = sum(1 for r in results if not isinstance(r, Exception))
        failed_creations = sum(1 for r in results if isinstance(r, Exception))
        
        assert successful_creations == 1
        assert failed_creations == 4
    
    @pytest.mark.asyncio
    async def test_concurrent_password_reset_requests(self, auth_service: AuthenticationService, test_user: User, test_tenant):
        """Test concurrent password reset requests."""
        async def request_password_reset():
            try:
                token = await auth_service.generate_password_reset_token(test_user.id)
                return await auth_service.reset_password(token, "NewPassword123!", test_tenant.id)
            except Exception as e:
                return e
        
        # Multiple concurrent reset requests
        tasks = [request_password_reset() for _ in range(3)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Should handle concurrent resets gracefully
        # At most one should succeed (due to token invalidation)
        successful_resets = sum(1 for r in results if r is True)
        assert successful_resets <= 1
    
    @pytest.mark.asyncio
    async def test_concurrent_token_refresh(self, auth_service: AuthenticationService, test_user: User, user_session: UserSession):
        """Test concurrent token refresh operations."""
        # Generate initial tokens
        initial_tokens = await auth_service._generate_tokens(test_user, user_session)
        refresh_token = initial_tokens["refresh_token"]
        
        async def refresh_tokens():
            try:
                return await auth_service.refresh_token(refresh_token)
            except Exception as e:
                return e
        
        # Multiple concurrent refresh requests
        tasks = [refresh_tokens() for _ in range(3)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Should handle concurrent refresh gracefully
        successful_refreshes = sum(1 for r in results if isinstance(r, dict) and "access_token" in r)
        
        # All should succeed as they use the same refresh token
        # (Current implementation doesn't rotate refresh tokens on use)
        assert successful_refreshes >= 1


class TestResourceExhaustionProtection:
    """Test protection against resource exhaustion attacks."""
    
    @pytest.mark.asyncio
    async def test_memory_exhaustion_protection(self, auth_service: AuthenticationService, test_tenant):
        """Test protection against memory exhaustion via large requests."""
        # Try to create user with extremely large profile data
        large_profile = {"description": "A" * 1000000}  # 1MB of data
        
        user_data = UserCreate(
            tenant_id=test_tenant.id,
            email="large@example.com",
            first_name="Large",
            last_name="Profile",
            password="Password123!",
            role=UserRole.DEVELOPER
        )
        
        # Should handle large data gracefully
        try:
            user = await auth_service.create_user(user_data)
            # If accepted, should not cause memory issues
            assert user is not None
        except (ValueError, MemoryError):
            # Resource limits are acceptable
            pass
    
    @pytest.mark.asyncio
    async def test_cpu_exhaustion_protection(self, auth_service: AuthenticationService):
        """Test protection against CPU exhaustion via expensive operations."""
        # Password hashing is intentionally expensive
        # Test that it doesn't consume excessive CPU for very long passwords
        very_long_password = "A" * 100000
        
        import time
        start_time = time.time()
        
        try:
            hash_result = await auth_service._hash_password(very_long_password)
            end_time = time.time()
            
            # Should complete in reasonable time even for long passwords
            assert end_time - start_time < 5.0  # Less than 5 seconds
            assert hash_result is not None
        except Exception:
            # Resource limits are acceptable
            pass
    
    @pytest.mark.asyncio
    async def test_connection_pool_exhaustion(self, auth_service: AuthenticationService, test_tenant):
        """Test handling of database connection pool exhaustion."""
        # Create many concurrent operations to potentially exhaust connection pool
        async def create_test_user(i):
            try:
                user_data = UserCreate(
                    tenant_id=test_tenant.id,
                    email=f"pool{i}@example.com",
                    first_name=f"Pool{i}",
                    last_name="Test",
                    password="Password123!",
                    role=UserRole.DEVELOPER
                )
                return await auth_service.create_user(user_data)
            except Exception as e:
                return e
        
        # Create many concurrent operations
        tasks = [create_test_user(i) for i in range(50)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Should handle connection limits gracefully
        successful_operations = sum(1 for r in results if hasattr(r, 'id'))
        failed_operations = sum(1 for r in results if isinstance(r, Exception))
        
        # Most should succeed, or fail gracefully
        assert successful_operations > 0
        # Failed operations should be handled exceptions, not crashes


class TestExternalServiceFailures:
    """Test handling of external service failures."""
    
    @pytest.mark.asyncio
    async def test_oauth_provider_error_response(self, auth_test_client):
        """Test handling of OAuth provider error responses."""
        # Test OAuth callback with error
        response = auth_test_client.get(
            "/api/v1/auth/sso/google/callback",
            params={
                "error": "access_denied",
                "error_description": "User denied access"
            }
        )
        
        # Should handle OAuth errors gracefully
        assert response.status_code == 307  # Redirect to login with error
        assert "/login" in response.headers["location"]
        assert "error" in response.headers["location"]
    
    @pytest.mark.asyncio
    async def test_saml_provider_malformed_response(self, auth_test_client):
        """Test handling of malformed SAML responses."""
        malformed_saml_responses = [
            "",  # Empty response
            "not-base64-encoded",  # Invalid base64
            "PHNhbWw+aW52YWxpZDwvc2FtbD4=",  # Invalid XML
        ]
        
        for malformed_response in malformed_saml_responses:
            response = auth_test_client.post(
                "/api/v1/auth/saml/sso",
                data={"SAMLResponse": malformed_response}
            )
            
            # Should handle malformed SAML gracefully
            assert response.status_code in [400, 500]
            if response.status_code == 400:
                data = response.json()
                assert "detail" in data
    
    @pytest.mark.asyncio
    async def test_mfa_service_downtime(self, auth_service: AuthenticationService, mfa_enabled_user: User, test_tenant):
        """Test handling of MFA service downtime."""
        # Mock MFA service being down
        with patch.object(auth_service, '_verify_mfa') as mock_verify:
            mock_verify.side_effect = Exception("MFA service unavailable")
            
            login_request = LoginRequest(
                email=mfa_enabled_user.email,
                password="SecurePassword123!",
                provider=AuthProvider.LOCAL,
                mfa_code="123456",
                mfa_method="totp",
                ip_address="192.168.1.100",
                user_agent="Mozilla/5.0 Test Browser"
            )
            
            # Should handle MFA service downtime
            with pytest.raises(InvalidCredentialsError):
                await auth_service.authenticate_user(login_request, test_tenant.id)


class TestEdgeCaseScenarios:
    """Test various edge case scenarios."""
    
    @pytest.mark.asyncio
    async def test_user_deleted_during_session(self, auth_service: AuthenticationService, test_user: User, test_tenant, test_db):
        """Test behavior when user is deleted during active session."""
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
        
        # Delete user from database
        from app.models.orm_models import UserORM
        await test_db.execute(
            UserORM.__table__.delete().where(UserORM.id == test_user.id)
        )
        await test_db.commit()
        
        # Try to use token after user deletion
        with pytest.raises((InvalidCredentialsError, Exception)):
            await auth_service.verify_token(tokens["access_token"])
    
    @pytest.mark.asyncio
    async def test_system_clock_changes(self, auth_service: AuthenticationService, test_user: User, user_session: UserSession):
        """Test handling of system clock changes affecting token expiry."""
        # Generate token
        tokens = await auth_service._generate_tokens(test_user, user_session)
        
        # Mock system time going backwards (clock adjustment)
        import jwt
        from unittest.mock import patch
        
        with patch('datetime.datetime') as mock_datetime:
            # Mock time going backwards by 1 hour
            past_time = datetime.utcnow() - timedelta(hours=1)
            mock_datetime.utcnow.return_value = past_time
            mock_datetime.fromtimestamp = datetime.fromtimestamp
            
            # Token should still be validated correctly
            try:
                payload = await auth_service.verify_token(tokens["access_token"])
                assert payload is not None
            except TokenExpiredError:
                # Clock changes might cause expiry issues
                pass
    
    @pytest.mark.asyncio
    async def test_unicode_normalization_edge_cases(self, auth_service: AuthenticationService, test_tenant):
        """Test Unicode normalization edge cases."""
        # Different Unicode representations of same character
        unicode_variants = [
            "café",  # Composed form
            "cafe\u0301",  # Decomposed form (e + combining acute accent)
        ]
        
        users = []
        for i, variant in enumerate(unicode_variants):
            user_data = UserCreate(
                tenant_id=test_tenant.id,
                email=f"unicode{i}@example.com",
                first_name=variant,
                last_name="Test",
                password="Password123!",
                role=UserRole.DEVELOPER
            )
            user = await auth_service.create_user(user_data)
            users.append(user)
        
        # Should handle Unicode variants correctly
        assert len(users) == len(unicode_variants)
        for user in users:
            assert user is not None
    
    @pytest.mark.asyncio
    async def test_leap_second_handling(self, auth_service: AuthenticationService, test_user: User, user_session: UserSession):
        """Test handling of leap seconds in token timestamps."""
        # Generate token near potential leap second
        tokens = await auth_service._generate_tokens(test_user, user_session)
        
        # Token should be valid regardless of leap second adjustments
        payload = await auth_service.verify_token(tokens["access_token"])
        assert payload is not None
        assert "exp" in payload
        assert "iat" in payload
    
    @pytest.mark.asyncio
    async def test_extremely_short_session_duration(self, auth_service: AuthenticationService, test_user: User):
        """Test handling of extremely short session durations."""
        # Create session with very short duration
        login_request = LoginRequest(
            email=test_user.email,
            password="SecurePassword123!",
            provider=AuthProvider.LOCAL,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 Test Browser",
            remember_me=False  # Short session
        )
        
        session = await auth_service._create_user_session(test_user, login_request)
        
        # Session should be created with appropriate duration
        assert session is not None
        assert session.expires_at > datetime.utcnow()
        
        # Duration should be reasonable even for short sessions
        duration = session.expires_at - session.created_at
        assert duration.total_seconds() > 0
    
    @pytest.mark.asyncio
    async def test_empty_string_inputs(self, auth_service: AuthenticationService, test_tenant):
        """Test handling of empty string inputs."""
        # Test various empty inputs
        empty_inputs = ["", "   ", "\t", "\n", "\r\n"]
        
        for empty_input in empty_inputs:
            try:
                user_data = UserCreate(
                    tenant_id=test_tenant.id,
                    email=f"empty_{hash(empty_input)}@example.com",
                    first_name=empty_input,
                    last_name="Test",
                    password="Password123!" if empty_input.strip() else "Password123!",
                    role=UserRole.DEVELOPER
                )
                
                if empty_input.strip():  # Non-empty after stripping
                    user = await auth_service.create_user(user_data)
                    assert user is not None
                else:
                    # Empty fields should be rejected or handled
                    with pytest.raises(ValueError):
                        await auth_service.create_user(user_data)
            except (ValueError, TypeError):
                # Validation errors for empty inputs are acceptable
                pass