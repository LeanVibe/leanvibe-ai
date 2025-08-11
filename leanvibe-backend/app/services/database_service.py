"""
Production Database Service
Provides database connectivity and management for production deployment
"""

import asyncio
import logging
import os
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager
from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, DateTime, Boolean, Text, Float, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID as PGUUID
import asyncpg

from app.config.settings import settings

logger = logging.getLogger(__name__)

# SQLAlchemy Base
Base = declarative_base()


class User(Base):
    """User model for authentication"""
    __tablename__ = "users"
    __table_args__ = {"schema": "auth"}
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default="uuid_generate_v4()")
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    company_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    tenant_id = Column(PGUUID(as_uuid=True), server_default="uuid_generate_v4()")
    created_at = Column(DateTime(timezone=True), server_default="NOW()")
    updated_at = Column(DateTime(timezone=True), server_default="NOW()")
    last_login = Column(DateTime(timezone=True))


class MVPProject(Base):
    """MVP Project model"""
    __tablename__ = "mvp_projects"
    __table_args__ = {"schema": "public"}
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default="uuid_generate_v4()")
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False)
    user_id = Column(PGUUID(as_uuid=True))
    project_name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False)
    description = Column(Text)
    status = Column(String(50), default="blueprint_pending")
    interview_data = Column(JSON)
    blueprint_data = Column(JSON)
    generated_files = Column(JSON)
    deployment_url = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default="NOW()")
    updated_at = Column(DateTime(timezone=True), server_default="NOW()")
    completed_at = Column(DateTime(timezone=True))


class PipelineExecution(Base):
    """Pipeline execution tracking"""
    __tablename__ = "pipeline_executions"
    __table_args__ = {"schema": "public"}
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default="uuid_generate_v4()")
    mvp_project_id = Column(PGUUID(as_uuid=True), nullable=False)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False)
    current_stage = Column(String(50), default="interview_received")
    status = Column(String(50), default="initializing")
    started_at = Column(DateTime(timezone=True), server_default="NOW()")
    completed_at = Column(DateTime(timezone=True))
    current_stage_started_at = Column(DateTime(timezone=True), server_default="NOW()")
    stages_completed = Column(JSON, default=list)
    stage_durations = Column(JSON, default=dict)
    workflow_id = Column(PGUUID(as_uuid=True))
    blueprint_versions = Column(JSON, default=list)
    overall_progress = Column(Float, default=0.0)
    current_stage_progress = Column(Float, default=0.0)
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)


class OperationLog(Base):
    """Operation monitoring logs"""
    __tablename__ = "operation_logs"
    __table_args__ = {"schema": "monitoring"}
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default="uuid_generate_v4()")
    operation_id = Column(String(255), nullable=False)
    operation_type = Column(String(100), nullable=False)
    tenant_id = Column(PGUUID(as_uuid=True))
    started_at = Column(DateTime(timezone=True), server_default="NOW()")
    completed_at = Column(DateTime(timezone=True))
    status = Column(String(50))
    duration_ms = Column(Float)
    error_type = Column(String(100))
    error_message = Column(Text)
    context_data = Column(JSON, default=dict)
    result_data = Column(JSON, default=dict)
    error_context = Column(JSON, default=dict)


class DatabaseService:
    """Production database service with connection pooling and management"""
    
    def __init__(self):
        self.engine = None
        self.async_session_maker = None
        self._initialized = False
        
    async def initialize(self):
        """Initialize database connection and session factory"""
        try:
            # Get database URL from settings
            database_url = getattr(settings, 'database_url', None) or os.getenv(
                'DATABASE_URL', 
                'postgresql+asyncpg://postgres:leanvibe123@localhost:5432/leanvibe_production'
            )
            
            # Ensure asyncpg driver for PostgreSQL
            if database_url.startswith('postgresql://'):
                database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
            
            # Create async engine with connection pooling
            self.engine = create_async_engine(
                database_url,
                echo=False,  # Set to True for SQL debugging
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600,  # 1 hour
                connect_args={
                    "server_settings": {
                        "application_name": "leanvibe-backend",
                    }
                }
            )
            
            # Create session factory
            self.async_session_maker = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            self._initialized = True
            logger.info("Database service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database service: {e}")
            raise
    
    @asynccontextmanager
    async def get_session(self):
        """Get database session with automatic cleanup"""
        if not self._initialized:
            await self.initialize()
        
        async with self.async_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Check database connectivity and performance"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            if not self._initialized:
                await self.initialize()
                
            async with self.get_session() as session:
                # Simple connectivity test
                result = await session.execute("SELECT 1")
                row = result.scalar()
                
                response_time = (asyncio.get_event_loop().time() - start_time) * 1000
                
                return {
                    "status": "healthy" if row == 1 else "unhealthy",
                    "response_time_ms": response_time,
                    "connection_pool_size": self.engine.pool.size(),
                    "connection_pool_checked_out": self.engine.pool.checkedout(),
                    "database_url": self.engine.url.render_as_string(hide_password=True)
                }
                
        except Exception as e:
            response_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            return {
                "status": "unhealthy",
                "response_time_ms": response_time,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def create_user(self, email: str, password_hash: str, **kwargs) -> Optional[UUID]:
        """Create a new user"""
        try:
            async with self.get_session() as session:
                user = User(
                    email=email,
                    password_hash=password_hash,
                    **kwargs
                )
                session.add(user)
                await session.flush()
                return user.id
                
        except Exception as e:
            logger.error(f"Failed to create user {email}: {e}")
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email address"""
        try:
            async with self.get_session() as session:
                from sqlalchemy import select
                
                stmt = select(User).where(User.email == email)
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()
                
                if user:
                    return {
                        "id": user.id,
                        "email": user.email,
                        "password_hash": user.password_hash,
                        "full_name": user.full_name,
                        "company_name": user.company_name,
                        "is_active": user.is_active,
                        "is_verified": user.is_verified,
                        "tenant_id": user.tenant_id,
                        "created_at": user.created_at,
                        "last_login": user.last_login
                    }
                    
                return None
                
        except Exception as e:
            logger.error(f"Failed to get user by email {email}: {e}")
            return None
    
    async def save_mvp_project(self, project_data: Dict[str, Any]) -> Optional[UUID]:
        """Save MVP project to database"""
        try:
            async with self.get_session() as session:
                project = MVPProject(**project_data)
                session.add(project)
                await session.flush()
                return project.id
                
        except Exception as e:
            logger.error(f"Failed to save MVP project: {e}")
            return None
    
    async def save_operation_log(self, operation_data: Dict[str, Any]) -> bool:
        """Save operation monitoring log"""
        try:
            async with self.get_session() as session:
                log_entry = OperationLog(**operation_data)
                session.add(log_entry)
                return True
                
        except Exception as e:
            logger.error(f"Failed to save operation log: {e}")
            return False
    
    async def close(self):
        """Close database connections"""
        if self.engine:
            await self.engine.dispose()
            self._initialized = False
            logger.info("Database service closed")


# Global database service instance
database_service = DatabaseService()


async def get_database_service() -> DatabaseService:
    """Get the global database service instance"""
    if not database_service._initialized:
        await database_service.initialize()
    return database_service