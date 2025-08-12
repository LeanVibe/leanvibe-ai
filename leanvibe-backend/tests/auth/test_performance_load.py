"""
Comprehensive performance and load tests for authentication
Tests response times, throughput, concurrent users, and scalability
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from app.models.auth_models import UserCreate, LoginRequest, AuthProvider, UserRole
from app.services.auth_service import AuthenticationService
from tests.fixtures.auth_test_fixtures import *


class TestAuthenticationPerformance:
    """Test authentication performance benchmarks."""
    
    @pytest.mark.asyncio
    async def test_login_response_time(self, auth_service: AuthenticationService, test_user: User, test_tenant):
        """Test login response time meets performance requirements."""
        login_request = LoginRequest(
            email=test_user.email,
            password="SecurePassword123!",
            provider=AuthProvider.LOCAL,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 Test Browser"
        )
        
        # Measure login time
        start_time = time.time()
        response = await auth_service.authenticate_user(login_request, test_tenant.id)
        end_time = time.time()
        
        login_time = end_time - start_time
        
        assert response.success is True
        assert login_time < 0.2  # Should complete within 200ms
        print(f"Login response time: {login_time:.3f}s")
    
    @pytest.mark.asyncio
    async def test_token_generation_performance(self, auth_service: AuthenticationService, test_user: User, user_session: UserSession):
        """Test JWT token generation performance."""
        # Measure token generation time for multiple tokens
        generation_times = []
        
        for _ in range(100):
            start_time = time.time()
            tokens = await auth_service._generate_tokens(test_user, user_session)
            end_time = time.time()
            
            generation_times.append(end_time - start_time)
            
            assert tokens["access_token"] is not None
            assert tokens["refresh_token"] is not None
        
        avg_time = sum(generation_times) / len(generation_times)
        max_time = max(generation_times)
        
        assert avg_time < 0.01  # Average should be < 10ms
        assert max_time < 0.05  # Max should be < 50ms
        print(f"Token generation - Avg: {avg_time:.4f}s, Max: {max_time:.4f}s")
    
    @pytest.mark.asyncio
    async def test_token_validation_performance(self, auth_service: AuthenticationService, valid_jwt_tokens):
        """Test JWT token validation performance."""
        access_token = valid_jwt_tokens["access_token"]
        
        # Measure token validation time for multiple validations
        validation_times = []
        
        for _ in range(100):
            start_time = time.time()
            payload = await auth_service.verify_token(access_token)
            end_time = time.time()
            
            validation_times.append(end_time - start_time)
            
            assert payload is not None
            assert "user_id" in payload
        
        avg_time = sum(validation_times) / len(validation_times)
        max_time = max(validation_times)
        
        assert avg_time < 0.005  # Average should be < 5ms
        assert max_time < 0.02   # Max should be < 20ms
        print(f"Token validation - Avg: {avg_time:.4f}s, Max: {max_time:.4f}s")
    
    @pytest.mark.asyncio
    async def test_password_hashing_performance(self, auth_service: AuthenticationService):
        """Test password hashing performance."""
        password = "TestPassword123!"
        
        # Measure password hashing time
        hashing_times = []
        
        for _ in range(10):  # Fewer iterations as hashing is intentionally slow
            start_time = time.time()
            hash_result = await auth_service._hash_password(password)
            end_time = time.time()
            
            hashing_times.append(end_time - start_time)
            
            assert hash_result is not None
            assert hash_result != password
        
        avg_time = sum(hashing_times) / len(hashing_times)
        max_time = max(hashing_times)
        
        # Password hashing should be slow for security but not too slow for UX
        assert avg_time < 1.0   # Average should be < 1 second
        assert max_time < 2.0   # Max should be < 2 seconds
        print(f"Password hashing - Avg: {avg_time:.3f}s, Max: {max_time:.3f}s")
    
    @pytest.mark.asyncio
    async def test_user_lookup_performance(self, auth_service: AuthenticationService, test_user: User, test_tenant):
        """Test user lookup performance."""
        # Measure user lookup by email
        lookup_times = []
        
        for _ in range(100):
            start_time = time.time()
            found_user = await auth_service.get_user_by_email(test_user.email, test_tenant.id)
            end_time = time.time()
            
            lookup_times.append(end_time - start_time)
            
            assert found_user is not None
            assert found_user.id == test_user.id
        
        avg_time = sum(lookup_times) / len(lookup_times)
        max_time = max(lookup_times)
        
        assert avg_time < 0.01  # Average should be < 10ms
        assert max_time < 0.05  # Max should be < 50ms
        print(f"User lookup - Avg: {avg_time:.4f}s, Max: {max_time:.4f}s")
    
    @pytest.mark.asyncio
    async def test_session_creation_performance(self, auth_service: AuthenticationService, test_user: User):
        """Test session creation performance."""
        login_request = LoginRequest(
            email=test_user.email,
            password="SecurePassword123!",
            provider=AuthProvider.LOCAL,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 Test Browser"
        )
        
        # Measure session creation time
        creation_times = []
        
        for i in range(50):
            start_time = time.time()
            session = await auth_service._create_user_session(test_user, login_request)
            end_time = time.time()
            
            creation_times.append(end_time - start_time)
            
            assert session is not None
            assert session.user_id == test_user.id
        
        avg_time = sum(creation_times) / len(creation_times)
        max_time = max(creation_times)
        
        assert avg_time < 0.05  # Average should be < 50ms
        assert max_time < 0.1   # Max should be < 100ms
        print(f"Session creation - Avg: {avg_time:.4f}s, Max: {max_time:.4f}s")


class TestConcurrentAuthentication:
    """Test concurrent authentication scenarios."""
    
    @pytest.mark.asyncio
    async def test_concurrent_logins_same_user(self, auth_service: AuthenticationService, test_user: User, test_tenant):
        """Test concurrent logins for the same user."""
        login_request = LoginRequest(
            email=test_user.email,
            password="SecurePassword123!",
            provider=AuthProvider.LOCAL,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 Test Browser"
        )
        
        # Create multiple concurrent login tasks
        num_concurrent = 10
        start_time = time.time()
        
        tasks = [
            auth_service.authenticate_user(login_request, test_tenant.id)
            for _ in range(num_concurrent)
        ]
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        total_time = end_time - start_time
        
        # All logins should succeed
        successful_logins = sum(1 for r in responses if hasattr(r, 'success') and r.success)
        assert successful_logins == num_concurrent
        
        # Should complete in reasonable time
        assert total_time < 2.0  # All logins within 2 seconds
        print(f"Concurrent logins ({num_concurrent}): {total_time:.3f}s")
    
    @pytest.mark.asyncio
    async def test_concurrent_logins_different_users(self, auth_service: AuthenticationService, test_tenant):
        """Test concurrent logins for different users."""
        # Create multiple test users
        users = []
        for i in range(20):
            user_data = UserCreate(
                tenant_id=test_tenant.id,
                email=f"concurrent{i}@example.com",
                first_name=f"User{i}",
                last_name="Concurrent",
                password="Password123!",
                role=UserRole.DEVELOPER
            )
            user = await auth_service.create_user(user_data)
            users.append(user)
        
        # Activate all users
        from app.models.orm_models import UserORM
        from app.models.auth_models import UserStatus
        test_db = await auth_service._get_db()
        user_ids = [user.id for user in users]
        await test_db.execute(
            UserORM.__table__.update()
            .where(UserORM.id.in_(user_ids))
            .values(status=UserStatus.ACTIVE)
        )
        await test_db.commit()
        
        # Create concurrent login requests
        login_tasks = []
        for user in users:
            login_request = LoginRequest(
                email=user.email,
                password="Password123!",
                provider=AuthProvider.LOCAL,
                ip_address="192.168.1.100",
                user_agent="Mozilla/5.0 Test Browser"
            )
            task = auth_service.authenticate_user(login_request, test_tenant.id)
            login_tasks.append(task)
        
        start_time = time.time()
        responses = await asyncio.gather(*login_tasks, return_exceptions=True)
        end_time = time.time()
        
        total_time = end_time - start_time
        
        # Count successful logins
        successful_logins = sum(1 for r in responses if hasattr(r, 'success') and r.success)
        assert successful_logins == len(users)
        
        # Should handle concurrent users efficiently
        assert total_time < 5.0  # All logins within 5 seconds
        avg_time_per_login = total_time / len(users)
        assert avg_time_per_login < 0.5  # Average < 500ms per login
        print(f"Concurrent users ({len(users)}): {total_time:.3f}s, Avg: {avg_time_per_login:.3f}s")
    
    @pytest.mark.asyncio
    async def test_concurrent_token_validation(self, auth_service: AuthenticationService, valid_jwt_tokens):
        """Test concurrent token validation."""
        access_token = valid_jwt_tokens["access_token"]
        
        # Create multiple concurrent validation tasks
        num_concurrent = 50
        
        async def validate_token():
            return await auth_service.verify_token(access_token)
        
        start_time = time.time()
        tasks = [validate_token() for _ in range(num_concurrent)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        total_time = end_time - start_time
        
        # All validations should succeed
        successful_validations = sum(1 for r in results if isinstance(r, dict) and "user_id" in r)
        assert successful_validations == num_concurrent
        
        # Should be very fast
        assert total_time < 0.5  # All validations within 500ms
        avg_time = total_time / num_concurrent
        assert avg_time < 0.01  # Average < 10ms per validation
        print(f"Concurrent token validations ({num_concurrent}): {total_time:.3f}s, Avg: {avg_time:.4f}s")
    
    @pytest.mark.asyncio
    async def test_concurrent_password_hashing(self, auth_service: AuthenticationService):
        """Test concurrent password hashing performance."""
        passwords = [f"Password{i}123!" for i in range(10)]
        
        async def hash_password(password):
            return await auth_service._hash_password(password)
        
        start_time = time.time()
        tasks = [hash_password(pwd) for pwd in passwords]
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        total_time = end_time - start_time
        
        # All hashes should be generated
        assert len(results) == len(passwords)
        assert all(result is not None for result in results)
        assert all(result != pwd for result, pwd in zip(results, passwords))
        
        # Should complete in reasonable time
        assert total_time < 10.0  # All hashing within 10 seconds
        avg_time = total_time / len(passwords)
        assert avg_time < 2.0  # Average < 2 seconds per hash
        print(f"Concurrent password hashing ({len(passwords)}): {total_time:.3f}s, Avg: {avg_time:.3f}s")


class TestLoadTesting:
    """Test system behavior under load."""
    
    @pytest.mark.asyncio
    async def test_high_frequency_requests(self, auth_service: AuthenticationService, test_user: User, test_tenant):
        """Test high-frequency authentication requests."""
        login_request = LoginRequest(
            email=test_user.email,
            password="SecurePassword123!",
            provider=AuthProvider.LOCAL,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 Test Browser"
        )
        
        # Send many requests in rapid succession
        num_requests = 100
        start_time = time.time()
        
        successful_requests = 0
        failed_requests = 0
        
        for _ in range(num_requests):
            try:
                response = await auth_service.authenticate_user(login_request, test_tenant.id)
                if response.success:
                    successful_requests += 1
                else:
                    failed_requests += 1
            except Exception:
                failed_requests += 1
        
        end_time = time.time()
        total_time = end_time - start_time
        requests_per_second = num_requests / total_time
        
        # Should handle high frequency requests
        assert successful_requests >= num_requests * 0.95  # At least 95% success rate
        assert requests_per_second > 50  # At least 50 requests per second
        print(f"High frequency test: {requests_per_second:.1f} req/s, Success: {successful_requests}/{num_requests}")
    
    @pytest.mark.asyncio
    async def test_burst_traffic_handling(self, auth_service: AuthenticationService, test_tenant):
        """Test handling of burst traffic patterns."""
        # Create multiple users for burst test
        users = []
        for i in range(50):
            user_data = UserCreate(
                tenant_id=test_tenant.id,
                email=f"burst{i}@example.com",
                first_name=f"Burst{i}",
                last_name="User",
                password="Password123!",
                role=UserRole.DEVELOPER
            )
            user = await auth_service.create_user(user_data)
            users.append(user)
        
        # Activate users
        from app.models.orm_models import UserORM
        from app.models.auth_models import UserStatus
        test_db = await auth_service._get_db()
        user_ids = [user.id for user in users]
        await test_db.execute(
            UserORM.__table__.update()
            .where(UserORM.id.in_(user_ids))
            .values(status=UserStatus.ACTIVE)
        )
        await test_db.commit()
        
        # Simulate burst traffic (all requests at once)
        burst_tasks = []
        for user in users:
            login_request = LoginRequest(
                email=user.email,
                password="Password123!",
                provider=AuthProvider.LOCAL,
                ip_address="192.168.1.100",
                user_agent="Mozilla/5.0 Test Browser"
            )
            task = auth_service.authenticate_user(login_request, test_tenant.id)
            burst_tasks.append(task)
        
        start_time = time.time()
        responses = await asyncio.gather(*burst_tasks, return_exceptions=True)
        end_time = time.time()
        
        burst_time = end_time - start_time
        
        # Count successful responses
        successful_responses = sum(1 for r in responses if hasattr(r, 'success') and r.success)
        success_rate = successful_responses / len(users)
        
        # Should handle burst traffic reasonably well
        assert success_rate >= 0.9  # At least 90% success rate
        assert burst_time < 10.0    # Complete within 10 seconds
        
        requests_per_second = len(users) / burst_time
        print(f"Burst traffic: {requests_per_second:.1f} req/s, Success rate: {success_rate:.2%}")
    
    @pytest.mark.asyncio
    async def test_sustained_load(self, auth_service: AuthenticationService, test_user: User, test_tenant):
        """Test sustained load over time."""
        login_request = LoginRequest(
            email=test_user.email,
            password="SecurePassword123!",
            provider=AuthProvider.LOCAL,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 Test Browser"
        )
        
        # Sustained load test for 30 seconds
        test_duration = 30  # seconds
        requests_per_second = 10
        
        start_time = time.time()
        successful_requests = 0
        failed_requests = 0
        response_times = []
        
        while time.time() - start_time < test_duration:
            request_start = time.time()
            
            try:
                response = await auth_service.authenticate_user(login_request, test_tenant.id)
                request_end = time.time()
                response_times.append(request_end - request_start)
                
                if response.success:
                    successful_requests += 1
                else:
                    failed_requests += 1
            except Exception:
                failed_requests += 1
            
            # Wait to maintain desired request rate
            sleep_time = 1.0 / requests_per_second
            await asyncio.sleep(sleep_time)
        
        total_requests = successful_requests + failed_requests
        success_rate = successful_requests / total_requests if total_requests > 0 else 0
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Performance should remain stable under sustained load
        assert success_rate >= 0.95  # At least 95% success rate
        assert avg_response_time < 1.0  # Average response time < 1 second
        
        print(f"Sustained load: {total_requests} requests, Success: {success_rate:.2%}, "
              f"Avg response: {avg_response_time:.3f}s")
    
    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self, auth_service: AuthenticationService, test_tenant):
        """Test memory usage under load."""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create many users and sessions
        users = []
        sessions = []
        
        for i in range(100):
            user_data = UserCreate(
                tenant_id=test_tenant.id,
                email=f"memory{i}@example.com",
                first_name=f"Memory{i}",
                last_name="Test",
                password="Password123!",
                role=UserRole.DEVELOPER
            )
            user = await auth_service.create_user(user_data)
            users.append(user)
            
            # Create session for each user
            login_request = LoginRequest(
                email=user.email,
                password="Password123!",
                provider=AuthProvider.LOCAL,
                ip_address="192.168.1.100",
                user_agent="Mozilla/5.0 Test Browser"
            )
            session = await auth_service._create_user_session(user, login_request)
            sessions.append(session)
        
        # Get memory usage after load
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory usage should be reasonable
        assert memory_increase < 100  # Should not increase by more than 100MB
        
        memory_per_user = memory_increase / len(users) if len(users) > 0 else 0
        assert memory_per_user < 1.0  # Should not use more than 1MB per user
        
        print(f"Memory usage: {memory_increase:.1f}MB increase for {len(users)} users "
              f"({memory_per_user:.3f}MB per user)")


class TestPerformanceAPI:
    """Test API endpoint performance."""
    
    @pytest.mark.asyncio
    async def test_login_api_performance(self, auth_test_client, test_user: User, test_tenant):
        """Test login API endpoint performance."""
        login_data = {
            "email": test_user.email,
            "password": "SecurePassword123!",
            "provider": "local"
        }
        
        response_times = []
        
        for _ in range(50):
            with patch('app.middleware.tenant_middleware.require_tenant') as mock_tenant:
                mock_tenant.return_value = test_tenant
                
                start_time = time.time()
                response = auth_test_client.post("/api/v1/auth/login", json=login_data)
                end_time = time.time()
                
                response_times.append(end_time - start_time)
                
                # Should return successful response
                assert response.status_code in [200, 401]  # 401 if user not active
        
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        
        # API should be fast
        assert avg_time < 0.5  # Average < 500ms
        assert max_time < 1.0  # Max < 1 second
        print(f"Login API - Avg: {avg_time:.3f}s, Max: {max_time:.3f}s")
    
    @pytest.mark.asyncio
    async def test_token_refresh_api_performance(self, auth_test_client, valid_jwt_tokens):
        """Test token refresh API performance."""
        refresh_token = valid_jwt_tokens["refresh_token"]
        
        response_times = []
        
        for _ in range(30):
            headers = {"Authorization": f"Bearer {refresh_token}"}
            
            start_time = time.time()
            response = auth_test_client.post("/api/v1/auth/refresh", headers=headers)
            end_time = time.time()
            
            response_times.append(end_time - start_time)
            
            # Should return new tokens or error
            assert response.status_code in [200, 401]
            
            # Use new refresh token for next iteration if available
            if response.status_code == 200:
                data = response.json()
                if "refresh_token" in data:
                    refresh_token = data["refresh_token"]
        
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        
        # Token refresh should be very fast
        assert avg_time < 0.2  # Average < 200ms
        assert max_time < 0.5  # Max < 500ms
        print(f"Token refresh API - Avg: {avg_time:.3f}s, Max: {max_time:.3f}s")
    
    @pytest.mark.asyncio
    async def test_user_profile_api_performance(self, auth_test_client, authenticated_headers, test_tenant):
        """Test user profile API performance."""
        response_times = []
        
        for _ in range(50):
            with patch('app.middleware.tenant_middleware.require_tenant') as mock_tenant:
                mock_tenant.return_value = test_tenant
                
                start_time = time.time()
                response = auth_test_client.get("/api/v1/auth/me", headers=authenticated_headers)
                end_time = time.time()
                
                response_times.append(end_time - start_time)
                
                # Should return user profile or error
                assert response.status_code in [200, 401, 404]
        
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        
        # Profile lookup should be fast
        assert avg_time < 0.1  # Average < 100ms
        assert max_time < 0.3  # Max < 300ms
        print(f"User profile API - Avg: {avg_time:.3f}s, Max: {max_time:.3f}s")


class TestScalabilityLimits:
    """Test system scalability limits."""
    
    @pytest.mark.asyncio
    async def test_maximum_concurrent_sessions(self, auth_service: AuthenticationService, test_user: User):
        """Test maximum number of concurrent sessions."""
        login_request = LoginRequest(
            email=test_user.email,
            password="SecurePassword123!",
            provider=AuthProvider.LOCAL,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 Test Browser"
        )
        
        # Create many concurrent sessions
        sessions = []
        max_sessions = 100
        
        for i in range(max_sessions):
            try:
                session = await auth_service._create_user_session(test_user, login_request)
                sessions.append(session)
            except Exception as e:
                print(f"Failed to create session {i}: {e}")
                break
        
        # Should be able to create reasonable number of sessions
        assert len(sessions) >= 50  # At least 50 concurrent sessions
        print(f"Created {len(sessions)} concurrent sessions")
        
        # All sessions should be valid
        for session in sessions[:10]:  # Check first 10
            assert session.user_id == test_user.id
            assert session.status.value == "active"
    
    @pytest.mark.asyncio
    async def test_token_payload_size_limits(self, auth_service: AuthenticationService, test_user: User, user_session: UserSession):
        """Test JWT token size doesn't exceed limits."""
        # Test with user having many permissions
        from app.models.auth_models import UserUpdate
        large_permissions = [f"permission_{i}" for i in range(100)]
        
        # Update user with many permissions
        update = UserUpdate(permissions=large_permissions)
        test_db = await auth_service._get_db()
        from app.models.orm_models import UserORM
        await test_db.execute(
            UserORM.__table__.update()
            .where(UserORM.id == test_user.id)
            .values(permissions=large_permissions)
        )
        await test_db.commit()
        
        # Update test_user object
        test_user.permissions = large_permissions
        
        # Generate tokens
        tokens = await auth_service._generate_tokens(test_user, user_session)
        
        # Check token sizes
        access_token_size = len(tokens["access_token"])
        refresh_token_size = len(tokens["refresh_token"])
        
        # Tokens should not be excessively large
        assert access_token_size < 4096  # Less than 4KB
        assert refresh_token_size < 2048  # Less than 2KB
        
        print(f"Token sizes - Access: {access_token_size} bytes, Refresh: {refresh_token_size} bytes")
        
        # Tokens should still be valid
        payload = await auth_service.verify_token(tokens["access_token"])
        assert payload is not None
        assert len(payload["permissions"]) == 100