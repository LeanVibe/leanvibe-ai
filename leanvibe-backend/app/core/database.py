"""
Database configuration and session management for LeanVibe Enterprise SaaS Platform
Provides multi-tenant database support with row-level security
"""

import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool
from ..config.settings import settings

logger = logging.getLogger(__name__)

# Database base class
Base = declarative_base()

# Global engine instance
_engine: AsyncEngine = None


def get_database_url() -> str:
    """Get database URL based on environment"""
    if settings.database_url:
        return settings.database_url
    
    # Default to SQLite for development
    if settings.is_development:
        return "sqlite+aiosqlite:///./leanvibe.db"
    
    # Require explicit database URL for production
    if settings.is_production:
        raise ValueError("LEANVIBE_DATABASE_URL must be set for production")
    
    return "sqlite+aiosqlite:///./leanvibe.db"


def create_database_engine() -> AsyncEngine:
    """Create database engine with appropriate configuration"""
    database_url = get_database_url()
    
    engine_kwargs = {
        "echo": settings.is_development,
        "future": True,
    }
    
    # Special configuration for SQLite
    if database_url.startswith("sqlite"):
        engine_kwargs.update({
            "poolclass": StaticPool,
            "connect_args": {
                "check_same_thread": False,
            }
        })
    
    # PostgreSQL configuration for production
    elif database_url.startswith("postgresql"):
        engine_kwargs.update({
            "pool_size": 20,
            "max_overflow": 0,
            "pool_pre_ping": True,
            "pool_recycle": 300,
        })
    
    return create_async_engine(database_url, **engine_kwargs)


def get_database_engine() -> AsyncEngine:
    """Get global database engine instance"""
    global _engine
    
    if _engine is None:
        _engine = create_database_engine()
        logger.info(f"Created database engine for environment: {settings.environment}")
    
    return _engine


# Async session factory
AsyncSessionLocal = sessionmaker(
    bind=get_database_engine(),
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_database():
    """Initialize database tables"""
    engine = get_database_engine()
    
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Database initialized successfully")


async def close_database():
    """Close database connections"""
    global _engine
    
    if _engine:
        await _engine.dispose()
        _engine = None
        logger.info("Database connections closed")


class TenantAwareQuery:
    """Helper class for tenant-aware database queries"""
    
    @staticmethod
    def add_tenant_filter(query, model, tenant_id: str):
        """Add tenant filter to query"""
        if hasattr(model, 'tenant_id'):
            return query.where(model.tenant_id == tenant_id)
        return query
    
    @staticmethod
    def validate_tenant_access(obj, tenant_id: str):
        """Validate that object belongs to tenant"""
        if hasattr(obj, 'tenant_id') and obj.tenant_id != tenant_id:
            raise ValueError(f"Object does not belong to tenant {tenant_id}")
        return True