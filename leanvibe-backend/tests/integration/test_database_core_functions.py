"""
IMPLEMENTATION: Core Database Functions Integration Tests
Priority 0 - Week 1 Implementation

These tests implement comprehensive testing of core database functions
to achieve 95%+ coverage on database security operations.
Status: IMPLEMENTING - Database core functions testing
"""

import pytest
import pytest_asyncio
import asyncio
from datetime import datetime
from uuid import UUID, uuid4
from unittest.mock import AsyncMock, patch, MagicMock
from typing import List, Dict, Any
import os
import tempfile

# Configure pytest for async tests
pytestmark = pytest.mark.asyncio

from app.core.database import (
    get_database_url, create_database_engine, get_database_engine,
    get_database_session, init_database, close_database, TenantAwareQuery
)
from app.config.settings import settings


class TestDatabaseConfiguration:
    """Test database configuration and URL generation"""
    
    def test_get_database_url_with_env_variable(self):
        """Test database URL retrieval from environment variable"""
        test_url = "postgresql://test:test@localhost/testdb"
        
        with patch.object(settings, 'database_url', test_url):
            url = get_database_url()
            assert url == test_url
    
    def test_get_database_url_development_default(self):
        """Test default SQLite URL for development environment"""
        with patch.object(settings, 'database_url', None):
            with patch.object(settings, 'is_development', True):
                url = get_database_url()
                assert url == "sqlite+aiosqlite:///./leanvibe.db"
    
    def test_get_database_url_production_requires_explicit(self):
        """Test that production environment requires explicit database URL"""
        with patch.object(settings, 'database_url', None):
            with patch.object(settings, 'is_production', True):
                with pytest.raises(ValueError, match="LEANVIBE_DATABASE_URL must be set for production"):
                    get_database_url()


class TestDatabaseEngineCreation:
    """Test database engine creation with different configurations"""
    
    @patch('app.core.database.create_async_engine')
    def test_create_database_engine_sqlite(self, mock_create_engine):
        """Test SQLite engine configuration"""
        with patch('app.core.database.get_database_url', return_value="sqlite+aiosqlite:///./test.db"):
            with patch.object(settings, 'is_development', True):
                create_database_engine()
                
                # Verify engine creation was called with SQLite-specific config
                mock_create_engine.assert_called_once()
                args, kwargs = mock_create_engine.call_args
                
                assert args[0] == "sqlite+aiosqlite:///./test.db"
                assert kwargs['echo'] is True  # Development mode
                assert 'poolclass' in kwargs
                assert 'connect_args' in kwargs
                assert kwargs['connect_args']['check_same_thread'] is False
    
    @patch('app.core.database.create_async_engine')
    def test_create_database_engine_postgresql(self, mock_create_engine):
        """Test PostgreSQL engine configuration"""
        with patch('app.core.database.get_database_url', return_value="postgresql+asyncpg://user:pass@localhost/db"):
            with patch.object(settings, 'is_development', False):
                create_database_engine()
                
                # Verify engine creation was called with PostgreSQL-specific config
                mock_create_engine.assert_called_once()
                args, kwargs = mock_create_engine.call_args
                
                assert args[0] == "postgresql+asyncpg://user:pass@localhost/db"
                assert kwargs['echo'] is False  # Production mode
                assert kwargs['pool_size'] == 20
                assert kwargs['max_overflow'] == 0
                assert kwargs['pool_pre_ping'] is True
                assert kwargs['pool_recycle'] == 300


class TestDatabaseEngineManagement:
    """Test global database engine management"""
    
    def test_get_database_engine_singleton(self):
        """Test that get_database_engine returns singleton instance"""
        # Reset global engine
        import app.core.database
        app.core.database._engine = None
        
        with patch('app.core.database.create_database_engine') as mock_create:
            mock_engine = MagicMock()
            mock_create.return_value = mock_engine
            
            # First call should create engine
            engine1 = get_database_engine()
            assert engine1 == mock_engine
            mock_create.assert_called_once()
            
            # Second call should return same instance
            engine2 = get_database_engine()
            assert engine2 == mock_engine
            assert engine1 is engine2
            # create_database_engine should still only be called once
            assert mock_create.call_count == 1


class TestDatabaseSession:
    """Test database session management"""
    
    async def test_get_database_session_lifecycle(self):
        """Test database session creation and cleanup"""
        mock_session = AsyncMock()
        mock_session.close = AsyncMock()
        mock_session.rollback = AsyncMock()
        
        with patch('app.core.database.AsyncSessionLocal') as mock_session_factory:
            mock_session_factory.return_value.__aenter__.return_value = mock_session
            mock_session_factory.return_value.__aexit__.return_value = None
            
            # Test normal session usage
            async with get_database_session() as session:
                assert session == mock_session
                # Simulate some database work
                await session.execute("SELECT 1")
            
            # Verify session lifecycle
            mock_session.execute.assert_called_with("SELECT 1")
            mock_session.close.assert_called_once()
    
    async def test_get_database_session_exception_handling(self):
        """Test database session rollback on exception"""
        mock_session = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.close = AsyncMock()
        
        with patch('app.core.database.AsyncSessionLocal') as mock_session_factory:
            mock_session_factory.return_value.__aenter__.return_value = mock_session
            mock_session_factory.return_value.__aexit__.return_value = None
            
            # Test session with exception
            with pytest.raises(Exception, match="Test exception"):
                async with get_database_session() as session:
                    # Simulate database error
                    session.execute.side_effect = Exception("Test exception")
                    await session.execute("SELECT 1")
            
            # Verify rollback was called
            mock_session.rollback.assert_called_once()
            mock_session.close.assert_called_once()


class TestDatabaseInitialization:
    """Test database initialization and cleanup"""
    
    async def test_init_database_creates_tables(self):
        """Test database initialization creates all tables"""
        mock_engine = AsyncMock()
        mock_conn = AsyncMock()
        mock_engine.begin.return_value.__aenter__.return_value = mock_conn
        
        with patch('app.core.database.get_database_engine', return_value=mock_engine):
            with patch('app.core.database.Base') as mock_base:
                mock_metadata = MagicMock()
                mock_base.metadata = mock_metadata
                
                await init_database()
                
                # Verify connection and table creation
                mock_engine.begin.assert_called_once()
                mock_conn.run_sync.assert_called_once()
                # Verify metadata.create_all would be called
                assert mock_conn.run_sync.called
    
    async def test_close_database_disposes_engine(self):
        """Test database cleanup disposes engine"""
        mock_engine = AsyncMock()
        mock_engine.dispose = AsyncMock()
        
        # Set global engine
        import app.core.database
        app.core.database._engine = mock_engine
        
        await close_database()
        
        # Verify engine disposal
        mock_engine.dispose.assert_called_once()
        
        # Verify global engine is reset
        assert app.core.database._engine is None
    
    async def test_close_database_with_no_engine(self):
        """Test database cleanup with no active engine"""
        # Reset global engine
        import app.core.database
        app.core.database._engine = None
        
        # Should not raise exception
        await close_database()
        
        # Engine should still be None
        assert app.core.database._engine is None


class TestTenantAwareQueryExtended:
    """Extended tests for TenantAwareQuery functionality"""
    
    def test_add_tenant_filter_with_tenant_model(self):
        """Test tenant filter application with tenant-aware model"""
        class TenantModel:
            tenant_id = "test_field"
        
        mock_query = MagicMock()
        mock_query.where = MagicMock(return_value="filtered_query")
        
        result = TenantAwareQuery.add_tenant_filter(mock_query, TenantModel, "test_tenant_id")
        
        # Verify where clause was applied
        mock_query.where.assert_called_once()
        assert result == "filtered_query"
    
    def test_add_tenant_filter_with_non_tenant_model(self):
        """Test tenant filter with non-tenant-aware model"""
        class NonTenantModel:
            other_field = "value"
        
        mock_query = MagicMock()
        
        result = TenantAwareQuery.add_tenant_filter(mock_query, NonTenantModel, "test_tenant_id")
        
        # Query should be unchanged
        assert result == mock_query
        # where should not be called
        assert not mock_query.where.called
    
    def test_validate_tenant_access_success(self):
        """Test successful tenant access validation"""
        class TenantObject:
            def __init__(self, tenant_id):
                self.tenant_id = tenant_id
        
        obj = TenantObject("tenant_123")
        result = TenantAwareQuery.validate_tenant_access(obj, "tenant_123")
        assert result is True
    
    def test_validate_tenant_access_failure(self):
        """Test failed tenant access validation"""
        class TenantObject:
            def __init__(self, tenant_id):
                self.tenant_id = tenant_id
        
        obj = TenantObject("tenant_123")
        with pytest.raises(ValueError, match="Object does not belong to tenant"):
            TenantAwareQuery.validate_tenant_access(obj, "tenant_456")
    
    def test_validate_tenant_access_non_tenant_object(self):
        """Test validation with object that has no tenant_id"""
        class NonTenantObject:
            def __init__(self):
                self.other_field = "value"
        
        obj = NonTenantObject()
        result = TenantAwareQuery.validate_tenant_access(obj, "any_tenant_id")
        assert result is True


class TestDatabaseEnvironmentConfiguration:
    """Test database configuration across environments"""
    
    def test_development_environment_config(self):
        """Test development environment database configuration"""
        with patch.object(settings, 'is_development', True):
            with patch.object(settings, 'database_url', None):
                url = get_database_url()
                assert "sqlite" in url
                assert "leanvibe.db" in url
    
    def test_production_environment_requires_url(self):
        """Test production environment requires explicit URL"""
        with patch.object(settings, 'is_production', True):
            with patch.object(settings, 'database_url', None):
                with pytest.raises(ValueError):
                    get_database_url()
    
    def test_explicit_database_url_overrides_environment(self):
        """Test explicit database URL overrides environment defaults"""
        explicit_url = "postgresql://explicit:url@localhost/db"
        
        with patch.object(settings, 'database_url', explicit_url):
            with patch.object(settings, 'is_development', True):
                url = get_database_url()
                assert url == explicit_url


class TestDatabaseSecurityCoverage:
    """Additional tests to improve database security coverage"""
    
    async def test_session_context_manager_error_paths(self):
        """Test error handling paths in session context manager"""
        mock_session = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.close = AsyncMock()
        
        # Test exception in session usage
        with patch('app.core.database.AsyncSessionLocal') as mock_session_factory:
            mock_session_factory.return_value.__aenter__.return_value = mock_session
            mock_session_factory.return_value.__aexit__.return_value = None
            
            with pytest.raises(RuntimeError, match="Database error"):
                async with get_database_session() as session:
                    raise RuntimeError("Database error")
            
            # Verify cleanup was called despite error
            mock_session.rollback.assert_called_once()
            mock_session.close.assert_called_once()
    
    def test_tenant_query_edge_cases(self):
        """Test edge cases in tenant query handling"""
        # Test with None tenant_id
        class TenantModel:
            tenant_id = "field"
        
        mock_query = MagicMock()
        result = TenantAwareQuery.add_tenant_filter(mock_query, TenantModel, None)
        # Should still apply filter even with None
        mock_query.where.assert_called_once()
        
        # Test validation with None values
        class TenantObject:
            tenant_id = None
        
        obj = TenantObject()
        with pytest.raises(ValueError):
            TenantAwareQuery.validate_tenant_access(obj, "some_tenant")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])