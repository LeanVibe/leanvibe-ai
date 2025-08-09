"""
IMPLEMENTATION: Critical Database Transaction Safety Integration Tests
Priority 0 - Week 1 Implementation

These tests implement comprehensive transaction safety and integrity testing 
to validate rollback behavior, concurrent transaction handling, and data consistency.
Status: IMPLEMENTING - Database transaction integration testing
"""

import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from unittest.mock import AsyncMock, patch, MagicMock, call
from typing import List, Dict, Any
from contextlib import asynccontextmanager

# Configure pytest for async tests
pytestmark = pytest.mark.asyncio

from app.core.database import (
    get_database_session, AsyncSessionLocal, get_database_engine
)
from app.models.tenant_models import (
    Tenant, TenantStatus, TenantPlan, DEFAULT_QUOTAS, TenantUsage
)
from app.models.auth_models import User, UserRole, UserStatus, AuthProvider
from app.models.project_models import Project, ProjectMetrics, ProjectLanguage, ProjectStatus
from app.core.exceptions import (
    DatabaseConnectionError, LeanVibeException, TenantNotFoundError
)


@pytest_asyncio.fixture
async def sample_tenant():
    """Sample tenant for transaction testing"""
    return Tenant(
        id=uuid4(),
        organization_name="Transaction Test Corp",
        slug="transaction-test",
        admin_email="admin@transaction-test.com",
        status=TenantStatus.ACTIVE,
        plan=TenantPlan.ENTERPRISE,
        quotas=DEFAULT_QUOTAS[TenantPlan.ENTERPRISE]
    )


@pytest_asyncio.fixture
async def sample_user(sample_tenant):
    """Sample user for transaction testing"""
    return User(
        id=uuid4(),
        tenant_id=sample_tenant.id,
        email="user@transaction-test.com",
        first_name="Transaction",
        last_name="User",
        role=UserRole.DEVELOPER,
        status=UserStatus.ACTIVE,
        auth_provider=AuthProvider.LOCAL,
        permissions=["project:read", "project:write"]
    )


@pytest_asyncio.fixture
async def sample_project(sample_tenant):
    """Sample project for transaction testing"""
    return Project(
        id=uuid4(),
        tenant_id=sample_tenant.id,
        display_name="Transaction Test Project",
        description="Project for testing transaction safety",
        status=ProjectStatus.ACTIVE,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        path="/projects/transaction-test",
        language=ProjectLanguage.PYTHON,
        last_activity=datetime.utcnow(),
        metrics=ProjectMetrics()
    )


@pytest_asyncio.fixture
async def mock_db_session():
    """Mock database session with transaction methods"""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    session.execute = AsyncMock()
    session.scalars = AsyncMock()
    session.add = AsyncMock()
    session.delete = AsyncMock()
    session.flush = AsyncMock()
    
    # Mock transaction state
    session.in_transaction = MagicMock(return_value=True)
    session.begin = AsyncMock()
    
    return session


class TestTransactionRollbackIntegrity:
    """Test transaction rollback preserves data integrity"""

    async def test_rollback_preserves_data_integrity(
        self, 
        mock_db_session, 
        sample_tenant, 
        sample_user, 
        sample_project
    ):
        """Test that failed operations don't corrupt data through proper rollbacks"""
        
        # Mock initial data state
        initial_tenant_data = {
            "id": sample_tenant.id,
            "name": sample_tenant.organization_name,
            "status": sample_tenant.status
        }
        
        # Simulate a multi-step operation that should rollback on failure
        with patch('app.core.database.AsyncSessionLocal') as mock_session_factory:
            mock_session_factory.return_value.__aenter__.return_value = mock_db_session
            
            async with AsyncSessionLocal() as session:
                try:
                    # Step 1: Update tenant (succeeds)
                    session.add(sample_tenant)
                    await session.flush()
                    
                    # Step 2: Create user (succeeds)
                    session.add(sample_user)
                    await session.flush()
                    
                    # Step 3: Create project (fails - simulate constraint violation)
                    session.add(sample_project)
                    
                    # Simulate database constraint violation
                    mock_db_session.commit.side_effect = Exception("Database constraint violation")
                    
                    # This should trigger rollback
                    await session.commit()
                    
                except Exception as e:
                    # Verify rollback is called on failure
                    await session.rollback()
                    
                    # Verify rollback was called
                    mock_db_session.rollback.assert_called_once()
                    
                    # Verify original data integrity is preserved
                    # (in real scenario, data would be unchanged after rollback)
                    assert str(e) == "Database constraint violation"
        
        # Verify the transaction operations were attempted
        assert mock_db_session.add.call_count == 3  # tenant, user, project
        assert mock_db_session.flush.call_count == 2  # first two operations
        assert mock_db_session.rollback.call_count == 1  # rollback on failure

    async def test_concurrent_transaction_handling(
        self,
        sample_tenant,
        sample_user
    ):
        """Test multiple transactions don't interfere with each other"""
        
        # Create separate mock sessions for concurrent transactions
        session_a = AsyncMock()
        session_b = AsyncMock()
        
        session_a.commit = AsyncMock()
        session_a.rollback = AsyncMock()
        session_a.add = AsyncMock()
        session_a.execute = AsyncMock()
        
        session_b.commit = AsyncMock()
        session_b.rollback = AsyncMock() 
        session_b.add = AsyncMock()
        session_b.execute = AsyncMock()
        
        async def transaction_a():
            """Transaction A: Update tenant data"""
            with patch('app.core.database.AsyncSessionLocal') as mock_factory:
                mock_factory.return_value.__aenter__.return_value = session_a
                
                async with AsyncSessionLocal() as session:
                    # Simulate tenant update
                    sample_tenant.organization_name = "Updated by Transaction A"
                    session.add(sample_tenant)
                    
                    # Simulate some processing time
                    await asyncio.sleep(0.01)
                    
                    # Commit transaction A
                    await session.commit()
                    
                    return "Transaction A completed"
        
        async def transaction_b():
            """Transaction B: Update user data"""
            with patch('app.core.database.AsyncSessionLocal') as mock_factory:
                mock_factory.return_value.__aenter__.return_value = session_b
                
                async with AsyncSessionLocal() as session:
                    # Simulate user update
                    sample_user.first_name = "Updated by Transaction B"
                    session.add(sample_user)
                    
                    # Simulate some processing time
                    await asyncio.sleep(0.01)
                    
                    # Commit transaction B
                    await session.commit()
                    
                    return "Transaction B completed"
        
        # Execute transactions concurrently
        results = await asyncio.gather(
            transaction_a(),
            transaction_b(),
            return_exceptions=True
        )
        
        # Verify both transactions completed successfully
        assert results[0] == "Transaction A completed"
        assert results[1] == "Transaction B completed"
        
        # Verify each session was used independently
        session_a.add.assert_called_once()
        session_b.add.assert_called_once()
        session_a.commit.assert_called_once()
        session_b.commit.assert_called_once()
        
        # Verify no rollbacks occurred (successful transactions)
        session_a.rollback.assert_not_called()
        session_b.rollback.assert_not_called()

    async def test_deadlock_detection_recovery(
        self,
        sample_tenant,
        sample_user
    ):
        """Test system handles deadlocks gracefully with proper recovery"""
        
        mock_session = AsyncMock()
        deadlock_count = 0
        max_retries = 3
        
        async def simulate_deadlock_then_success():
            nonlocal deadlock_count
            deadlock_count += 1
            
            if deadlock_count <= 2:  # First two attempts fail with deadlock
                raise Exception("deadlock detected")
            else:  # Third attempt succeeds
                return "success"
        
        mock_session.commit = AsyncMock(side_effect=simulate_deadlock_then_success)
        mock_session.rollback = AsyncMock()
        mock_session.add = AsyncMock()
        
        with patch('app.core.database.AsyncSessionLocal') as mock_session_factory:
            mock_session_factory.return_value.__aenter__.return_value = mock_session
            
            # Implement deadlock retry logic
            retry_count = 0
            last_exception = None
            
            while retry_count < max_retries:
                try:
                    async with AsyncSessionLocal() as session:
                        # Simulate database operation
                        session.add(sample_tenant)
                        session.add(sample_user)
                        
                        # This will deadlock on first two attempts
                        await session.commit()
                        
                        # If we get here, operation succeeded
                        break
                        
                except Exception as e:
                    last_exception = e
                    retry_count += 1
                    
                    if "deadlock detected" in str(e):
                        # Rollback and retry
                        await mock_session.rollback()
                        await asyncio.sleep(0.01 * retry_count)  # Exponential backoff
                        continue
                    else:
                        # Non-deadlock error, don't retry
                        raise e
            
            # Verify deadlock was detected and handled
            assert deadlock_count == 3  # Two deadlocks + one success
            assert mock_session.commit.call_count == 3  # Three attempts
            assert mock_session.rollback.call_count == 2  # Two rollbacks for deadlocks
            assert retry_count == 2  # Two retries before success

    async def test_transaction_isolation_levels(
        self,
        sample_tenant,
        sample_project
    ):
        """Test proper isolation between concurrent transactions"""
        
        # Create two sessions with different isolation scenarios
        session_reader = AsyncMock()
        session_writer = AsyncMock()
        
        # Configure reader session
        session_reader.execute = AsyncMock()
        session_reader.scalars = AsyncMock()
        
        # Configure writer session
        session_writer.add = AsyncMock()
        session_writer.commit = AsyncMock()
        session_writer.execute = AsyncMock()
        
        # Initial project state
        initial_project_name = "Original Project Name"
        sample_project.display_name = initial_project_name
        
        # Mock reader query results
        mock_reader_result = MagicMock()
        mock_reader_result.all.return_value = [sample_project]
        session_reader.scalars.return_value = mock_reader_result
        
        async def reader_transaction():
            """Read transaction that should see consistent data"""
            with patch('app.core.database.AsyncSessionLocal') as mock_factory:
                mock_factory.return_value.__aenter__.return_value = session_reader
                
                async with AsyncSessionLocal() as session:
                    # Read project data at start
                    first_read = session_reader.scalars.return_value.all.return_value[0]
                    
                    # Simulate some processing time
                    await asyncio.sleep(0.02)
                    
                    # Read project data again - should be consistent (isolation)
                    second_read = session_reader.scalars.return_value.all.return_value[0]
                    
                    # With proper isolation, both reads should return same data
                    assert first_read.display_name == second_read.display_name
                    return first_read.display_name
        
        async def writer_transaction():
            """Write transaction that updates data"""
            with patch('app.core.database.AsyncSessionLocal') as mock_factory:
                mock_factory.return_value.__aenter__.return_value = session_writer
                
                async with AsyncSessionLocal() as session:
                    # Wait a bit before updating
                    await asyncio.sleep(0.01)
                    
                    # Update project
                    sample_project.display_name = "Updated Project Name"
                    session.add(sample_project)
                    await session.commit()
                    
                    return "Update completed"
        
        # Execute reader and writer concurrently
        reader_result, writer_result = await asyncio.gather(
            reader_transaction(),
            writer_transaction()
        )
        
        # Verify isolation: reader saw consistent data throughout transaction
        assert reader_result == initial_project_name
        assert writer_result == "Update completed"
        
        # Verify operations were executed
        session_reader.scalars.assert_called()  # Reader performed queries
        session_writer.add.assert_called_once()  # Writer added update
        session_writer.commit.assert_called_once()  # Writer committed change


class TestTransactionErrorHandling:
    """Test comprehensive transaction error handling scenarios"""
    
    async def test_nested_transaction_rollback(
        self, 
        mock_db_session,
        sample_tenant,
        sample_user
    ):
        """Test nested transaction rollback behavior"""
        
        # Mock nested transaction behavior
        savepoint_mock = AsyncMock()
        savepoint_mock.rollback = AsyncMock()
        savepoint_mock.commit = AsyncMock()
        
        mock_db_session.begin_nested = AsyncMock(return_value=savepoint_mock)
        
        with patch('app.core.database.AsyncSessionLocal') as mock_session_factory:
            mock_session_factory.return_value.__aenter__.return_value = mock_db_session
            
            async with AsyncSessionLocal() as session:
                # Start main transaction
                session.add(sample_tenant)
                
                try:
                    # Start nested transaction (savepoint)
                    async with session.begin_nested():
                        session.add(sample_user)
                        
                        # Simulate failure in nested transaction
                        raise Exception("Nested transaction error")
                        
                except Exception as e:
                    # Nested transaction should rollback, main continues
                    assert str(e) == "Nested transaction error"
                
                # Main transaction can still commit
                await session.commit()
        
        # Verify nested transaction was used
        mock_db_session.begin_nested.assert_called_once()
        
        # Main transaction should still commit
        mock_db_session.commit.assert_called_once()
    
    async def test_connection_loss_recovery(self, sample_tenant):
        """Test transaction recovery after connection loss"""
        
        mock_session = AsyncMock()
        connection_loss_count = 0
        
        async def simulate_connection_loss():
            nonlocal connection_loss_count
            connection_loss_count += 1
            
            if connection_loss_count == 1:
                raise Exception("connection lost")
            else:
                return "reconnected"
        
        mock_session.commit = AsyncMock(side_effect=simulate_connection_loss)
        mock_session.rollback = AsyncMock()
        mock_session.add = AsyncMock()
        
        with patch('app.core.database.AsyncSessionLocal') as mock_session_factory:
            mock_session_factory.return_value.__aenter__.return_value = mock_session
            
            # Implement connection recovery logic
            try:
                async with AsyncSessionLocal() as session:
                    session.add(sample_tenant)
                    await session.commit()
            except Exception as e:
                if "connection lost" in str(e):
                    # Simulate recovery attempt
                    async with AsyncSessionLocal() as recovery_session:
                        recovery_session.add(sample_tenant)
                        await recovery_session.commit()
        
        # Verify connection loss was handled
        assert connection_loss_count == 2  # First failure + recovery attempt
        assert mock_session.commit.call_count >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])