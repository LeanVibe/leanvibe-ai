"""
Tenant service for LeanVibe Enterprise SaaS Platform
Provides tenant management, quota tracking, and usage monitoring
Updated to use SQLAlchemy ORM models
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func
from sqlalchemy.orm import selectinload

from ..models.tenant_models import (
    TenantCreate, TenantUpdate, TenantUsage, TenantQuotaExceeded,
    TenantStatus, TenantPlan, DEFAULT_QUOTAS, TenantMember
)
from ..models.orm_models import TenantORM, TaskORM, ProjectORM, TenantMemberORM
from ..core.database import get_database_session
from ..core.exceptions import (
    TenantNotFoundError, TenantQuotaExceededError, TenantSuspendedError,
    InvalidTenantError
)

logger = logging.getLogger(__name__)


class TenantService:
    """Service for tenant management operations using SQLAlchemy ORM"""
    
    def __init__(self, db: AsyncSession = None):
        self.db = db
    
    async def _get_db(self) -> AsyncSession:
        """Get database session"""
        if self.db:
            return self.db
        async for db in get_database_session():
            return db
    
    async def create_tenant(self, tenant_data: TenantCreate) -> TenantORM:
        """Create a new tenant with default quotas"""
        async with self._get_db() as db:
            try:
                # Check if slug is already taken
                existing = await self.get_by_slug(tenant_data.slug, raise_if_not_found=False)
                if existing:
                    raise InvalidTenantError(f"Tenant slug '{tenant_data.slug}' is already taken")
                
                # Set default quotas based on plan
                quotas = DEFAULT_QUOTAS[tenant_data.plan]
                
                # Create tenant instance using ORM model
                tenant = TenantORM(
                    organization_name=tenant_data.organization_name,
                    display_name=tenant_data.display_name or tenant_data.organization_name,
                    slug=tenant_data.slug,
                    admin_email=tenant_data.admin_email,
                    plan=tenant_data.plan,
                    data_residency=tenant_data.data_residency,
                    parent_tenant_id=tenant_data.parent_tenant_id,
                    quotas=quotas.model_dump(),  # Convert Pydantic to dict for JSON storage
                    current_usage={},  # Initialize empty usage
                    trial_ends_at=datetime.utcnow() + timedelta(days=14)  # 14-day trial
                )
                
                # Save to database
                db.add(tenant)
                await db.commit()
                await db.refresh(tenant)
                
                logger.info(f"Created tenant: {tenant.slug} ({tenant.id})")
                
                return tenant
                
            except Exception as e:
                await db.rollback()
                logger.error(f"Failed to create tenant: {e}")
                raise
    
    async def get_by_id(self, tenant_id: UUID, raise_if_not_found: bool = True) -> Optional[TenantORM]:
        """Get tenant by ID"""
        async with self._get_db() as db:
            result = await db.execute(
                select(TenantORM).where(TenantORM.id == tenant_id)
            )
            tenant = result.scalar_one_or_none()
            
            if not tenant and raise_if_not_found:
                raise TenantNotFoundError(f"Tenant not found: {tenant_id}")
            
            return tenant
    
    async def get_by_slug(self, slug: str, raise_if_not_found: bool = True) -> Optional[TenantORM]:
        """Get tenant by slug"""
        async with self._get_db() as db:
            result = await db.execute(
                select(TenantORM).where(TenantORM.slug == slug)
            )
            tenant = result.scalar_one_or_none()
            
            if not tenant and raise_if_not_found:
                raise TenantNotFoundError(f"Tenant not found: {slug}")
            
            return tenant
    
    async def update_tenant(self, tenant_id: UUID, update_data: TenantUpdate) -> TenantORM:
        """Update tenant information"""
        async with self._get_db() as db:
            try:
                tenant = await self.get_by_id(tenant_id)
                
                # Update fields
                update_dict = update_data.model_dump(exclude_unset=True)
                
                # Handle plan changes - update quotas
                if "plan" in update_dict and update_dict["plan"] != tenant.plan:
                    new_plan = update_dict["plan"]
                    update_dict["quotas"] = DEFAULT_QUOTAS[new_plan].model_dump()
                    logger.info(f"Updated tenant {tenant.slug} plan from {tenant.plan} to {new_plan}")
                
                # Always update the timestamp
                update_dict["updated_at"] = datetime.utcnow()
                
                await db.execute(
                    update(TenantORM)
                    .where(TenantORM.id == tenant_id)
                    .values(**update_dict)
                )
                
                await db.commit()
                
                # Return updated tenant
                return await self.get_by_id(tenant_id)
                
            except Exception as e:
                await db.rollback()
                logger.error(f"Failed to update tenant {tenant_id}: {e}")
                raise
    
    async def suspend_tenant(self, tenant_id: UUID, reason: str = None) -> TenantORM:
        """Suspend a tenant"""
        return await self.update_tenant(
            tenant_id,
            TenantUpdate(status=TenantStatus.SUSPENDED)
        )
    
    async def reactivate_tenant(self, tenant_id: UUID) -> TenantORM:
        """Reactivate a suspended tenant"""
        return await self.update_tenant(
            tenant_id,
            TenantUpdate(status=TenantStatus.ACTIVE)
        )
    
    async def delete_tenant(self, tenant_id: UUID, hard_delete: bool = False) -> bool:
        """Delete tenant (soft delete by default)"""
        async with self._get_db() as db:
            try:
                if hard_delete:
                    # Hard delete - completely remove from database
                    result = await db.execute(
                        delete(TenantORM).where(TenantORM.id == tenant_id)
                    )
                    deleted = result.rowcount > 0
                else:
                    # Soft delete - mark as cancelled
                    result = await db.execute(
                        update(TenantORM)
                        .where(TenantORM.id == tenant_id)
                        .values(
                            status=TenantStatus.CANCELLED,
                            updated_at=datetime.utcnow()
                        )
                    )
                    deleted = result.rowcount > 0
                
                await db.commit()
                
                if deleted:
                    logger.info(f"{'Hard' if hard_delete else 'Soft'} deleted tenant: {tenant_id}")
                
                return deleted
                
            except Exception as e:
                await db.rollback()
                logger.error(f"Failed to delete tenant {tenant_id}: {e}")
                raise
    
    async def list_tenants(
        self,
        status: Optional[TenantStatus] = None,
        plan: Optional[TenantPlan] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[TenantORM]:
        """List tenants with optional filters"""
        async with self._get_db() as db:
            query = select(TenantORM)
            
            # Apply filters
            if status:
                query = query.where(TenantORM.status == status)
            if plan:
                query = query.where(TenantORM.plan == plan)
            
            # Apply pagination
            query = query.offset(offset).limit(limit)
            
            result = await db.execute(query)
            return result.scalars().all()
    
    async def get_tenant_usage(self, tenant_id: UUID) -> TenantUsage:
        """Get current resource usage for tenant"""
        async with self._get_db() as db:
            # Count actual usage from database
            
            # Count projects for this tenant
            project_result = await db.execute(
                select(func.count()).where(ProjectORM.tenant_id == tenant_id)
            )
            projects_count = project_result.scalar() or 0
            
            # Count tasks for this tenant
            task_result = await db.execute(
                select(func.count()).where(TaskORM.tenant_id == tenant_id)
            )
            tasks_count = task_result.scalar() or 0
            
            # Count tenant members
            member_result = await db.execute(
                select(func.count()).where(TenantMemberORM.tenant_id == tenant_id)
            )
            users_count = member_result.scalar() or 0
            
            return TenantUsage(
                tenant_id=tenant_id,
                users_count=users_count,
                projects_count=projects_count,
                api_calls_this_month=0,  # TODO: Count from API logs when implemented
                storage_used_mb=0,  # TODO: Calculate from file storage when implemented
                ai_requests_today=0,  # TODO: Count from AI request logs when implemented
                concurrent_sessions=0,  # TODO: Count from active WebSocket connections
            )
    
    async def check_quota(self, tenant_id: UUID, quota_type: str, increment: int = 1) -> bool:
        """Check if tenant can consume resource within quota"""
        tenant = await self.get_by_id(tenant_id)
        usage = await self.get_tenant_usage(tenant_id)
        
        # Convert JSON quotas back to object for easier access
        from ..models.tenant_models import TenantQuotas
        quotas = TenantQuotas(**tenant.quotas)
        
        quota_checks = {
            "users": (usage.users_count + increment, quotas.max_users),
            "projects": (usage.projects_count + increment, quotas.max_projects),
            "api_calls": (usage.api_calls_this_month + increment, quotas.max_api_calls_per_month),
            "storage_mb": (usage.storage_used_mb + increment, quotas.max_storage_mb),
            "ai_requests": (usage.ai_requests_today + increment, quotas.max_ai_requests_per_day),
            "concurrent_sessions": (usage.concurrent_sessions + increment, quotas.max_concurrent_sessions),
        }
        
        if quota_type not in quota_checks:
            logger.warning(f"Unknown quota type: {quota_type}")
            return True  # Allow unknown quota types
        
        current_usage, limit = quota_checks[quota_type]
        
        if current_usage > limit:
            logger.warning(
                f"Quota exceeded for tenant {tenant.slug}: {quota_type} "
                f"({current_usage}/{limit})"
            )
            return False
        
        return True
    
    async def enforce_quota(self, tenant_id: UUID, quota_type: str, increment: int = 1):
        """Enforce quota limits, raise exception if exceeded"""
        if not await self.check_quota(tenant_id, quota_type, increment):
            tenant = await self.get_by_id(tenant_id)
            usage = await self.get_tenant_usage(tenant_id)
            
            raise TenantQuotaExceededError(
                f"Quota exceeded for {quota_type}. "
                f"Consider upgrading to a higher plan.",
                quota_type=quota_type,
                current_usage=getattr(usage, f"{quota_type}_count", 0),
                quota_limit=getattr(tenant.quotas, f"max_{quota_type}", 0)
            )
    
    async def record_quota_usage(
        self,
        tenant_id: UUID,
        quota_type: str,
        amount: int = 1,
        metadata: Dict = None
    ):
        """Record quota usage (for tracking and billing)"""
        # This would typically insert into a usage_logs table
        # For now, just log the usage
        logger.info(
            f"Quota usage recorded for tenant {tenant_id}: "
            f"{quota_type}={amount}, metadata={metadata}"
        )
    
    async def get_tenant_hierarchy(self, tenant_id: UUID) -> List[TenantORM]:
        """Get tenant hierarchy (parent and children)"""
        async with self._get_db() as db:
            # Get all related tenants in hierarchy
            result = await db.execute(
                select(TenantORM).where(
                    or_(
                        TenantORM.id == tenant_id,
                        TenantORM.parent_tenant_id == tenant_id,
                        TenantORM.id.in_(
                            select(TenantORM.parent_tenant_id).where(TenantORM.id == tenant_id)
                        )
                    )
                )
            )
            
            return result.scalars().all()
    
    async def update_last_activity(self, tenant_id: UUID):
        """Update tenant's last activity timestamp"""
        async with self._get_db() as db:
            await db.execute(
                update(TenantORM)
                .where(TenantORM.id == tenant_id)
                .values(last_activity_at=datetime.utcnow())
            )
            
            await db.commit()
    
    async def get_trial_expiring_soon(self, days_ahead: int = 7) -> List[TenantORM]:
        """Get tenants whose trials are expiring soon"""
        async with self._get_db() as db:
            expiry_cutoff = datetime.utcnow() + timedelta(days=days_ahead)
            
            result = await db.execute(
                select(TenantORM).where(
                    and_(
                        TenantORM.status == TenantStatus.TRIAL,
                        TenantORM.trial_ends_at <= expiry_cutoff,
                        TenantORM.trial_ends_at > datetime.utcnow()
                    )
                )
            )
            
            return result.scalars().all()


# Singleton service instance
tenant_service = TenantService()