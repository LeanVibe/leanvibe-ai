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
    TenantStatus, TenantPlan, TenantType, DEFAULT_QUOTAS, TenantMember
)
from ..models.orm_models import TenantORM, TaskORM, ProjectORM, TenantMemberORM, MVPProjectORM
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
        """Create a new tenant with default quotas (Enterprise or MVP Factory)"""
        async with self._get_db() as db:
            try:
                # Check if slug is already taken
                existing = await self.get_by_slug(tenant_data.slug, raise_if_not_found=False)
                if existing:
                    raise InvalidTenantError(f"Tenant slug '{tenant_data.slug}' is already taken")
                
                # Set default quotas based on plan
                quotas = DEFAULT_QUOTAS[tenant_data.plan]
                
                # Validate MVP Factory specific fields
                if tenant_data.tenant_type == TenantType.MVP_FACTORY:
                    if not tenant_data.founder_name:
                        raise InvalidTenantError("Founder name is required for MVP Factory tenants")
                    if tenant_data.plan not in [TenantPlan.MVP_SINGLE, TenantPlan.MVP_BUNDLE]:
                        raise InvalidTenantError(f"Plan {tenant_data.plan} is not valid for MVP Factory tenants")
                else:  # Enterprise tenant
                    if tenant_data.plan in [TenantPlan.MVP_SINGLE, TenantPlan.MVP_BUNDLE]:
                        raise InvalidTenantError(f"Plan {tenant_data.plan} is only valid for MVP Factory tenants")
                
                # Create tenant instance using ORM model
                tenant = TenantORM(
                    tenant_type=tenant_data.tenant_type,
                    organization_name=tenant_data.organization_name,
                    display_name=tenant_data.display_name or tenant_data.organization_name,
                    slug=tenant_data.slug,
                    admin_email=tenant_data.admin_email,
                    plan=tenant_data.plan,
                    data_residency=tenant_data.data_residency,
                    parent_tenant_id=tenant_data.parent_tenant_id,
                    # MVP Factory specific fields
                    founder_name=tenant_data.founder_name,
                    founder_phone=tenant_data.founder_phone,
                    business_description=tenant_data.business_description,
                    target_market=tenant_data.target_market,
                    mvp_count_used=0,
                    # Standard fields
                    quotas=quotas.model_dump(),  # Convert Pydantic to dict for JSON storage
                    current_usage={},  # Initialize empty usage
                    trial_ends_at=datetime.utcnow() + timedelta(days=14) if tenant_data.tenant_type == TenantType.ENTERPRISE else None  # No trial for MVP Factory
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
        """Get current resource usage for tenant (Enterprise + MVP Factory)"""
        async with self._get_db() as db:
            # Get tenant to check type
            tenant = await self.get_by_id(tenant_id)
            
            # Count actual usage from database
            
            # Count projects for this tenant (includes enterprise projects)
            project_result = await db.execute(
                select(func.count()).where(ProjectORM.tenant_id == tenant_id)
            )
            projects_count = project_result.scalar() or 0
            
            # Count MVP projects for this tenant
            mvp_result = await db.execute(
                select(func.count()).where(MVPProjectORM.tenant_id == tenant_id)
            )
            mvp_count = mvp_result.scalar() or 0
            
            # For MVP Factory tenants, MVP projects ARE their projects
            if tenant.tenant_type == TenantType.MVP_FACTORY:
                projects_count = mvp_count
            
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
            
            # Count active MVP generations (concurrent MVPs)
            active_mvp_result = await db.execute(
                select(func.count()).where(
                    and_(
                        MVPProjectORM.tenant_id == tenant_id,
                        MVPProjectORM.status.in_(["generating", "testing", "deploying"])
                    )
                )
            )
            concurrent_mvps = active_mvp_result.scalar() or 0
            
            # Sum resource usage for MVP projects
            resource_result = await db.execute(
                select(
                    func.coalesce(func.sum(MVPProjectORM.cpu_hours_used), 0),
                    func.coalesce(func.sum(MVPProjectORM.memory_gb_hours_used), 0),
                    func.coalesce(func.sum(MVPProjectORM.storage_mb_used), 0),
                    func.coalesce(func.sum(MVPProjectORM.ai_tokens_used), 0)
                ).where(MVPProjectORM.tenant_id == tenant_id)
            )
            resource_usage = resource_result.first() or (0, 0, 0, 0)
            
            return TenantUsage(
                tenant_id=tenant_id,
                users_count=users_count,
                projects_count=projects_count,
                api_calls_this_month=0,  # TODO: Count from API logs when implemented
                storage_used_mb=int(resource_usage[2]),  # From MVP projects
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
    
    # ===============================
    # MVP Factory Specific Methods
    # ===============================
    
    async def create_mvp_factory_tenant(
        self, 
        founder_name: str,
        founder_email: str,
        business_idea: str,
        plan: TenantPlan = TenantPlan.MVP_SINGLE
    ) -> TenantORM:
        """Simplified method to create MVP Factory tenant"""
        import re
        
        # Generate slug from founder name
        slug = re.sub(r'[^a-z0-9-]', '', founder_name.lower().replace(' ', '-'))
        slug = f"mvp-{slug}-{uuid4().hex[:6]}"  # Add unique suffix
        
        tenant_data = TenantCreate(
            tenant_type=TenantType.MVP_FACTORY,
            organization_name=f"{founder_name}'s MVP Project",
            slug=slug,
            admin_email=founder_email,
            plan=plan,
            founder_name=founder_name,
            business_description=business_idea[:2000],  # Truncate if needed
        )
        
        return await self.create_tenant(tenant_data)
    
    async def get_mvp_projects(self, tenant_id: UUID) -> List[Dict]:
        """Get all MVP projects for a tenant"""
        async with self._get_db() as db:
            result = await db.execute(
                select(MVPProjectORM).where(MVPProjectORM.tenant_id == tenant_id)
                .order_by(MVPProjectORM.created_at.desc())
            )
            mvp_projects = result.scalars().all()
            
            # Convert to dict for JSON serialization
            return [
                {
                    "id": str(project.id),
                    "project_name": project.project_name,
                    "slug": project.slug,
                    "status": project.status,
                    "description": project.description,
                    "created_at": project.created_at.isoformat(),
                    "deployed_at": project.deployed_at.isoformat() if project.deployed_at else None,
                    "deployment_url": project.deployment_url,
                    "generation_progress": project.generation_progress,
                    "total_cost": project.total_cost,
                    "founder_satisfaction_score": project.founder_satisfaction_score
                }
                for project in mvp_projects
            ]
    
    async def check_mvp_quota(self, tenant_id: UUID, quota_type: str, increment: int = 1) -> bool:
        """Check MVP-specific quotas"""
        tenant = await self.get_by_id(tenant_id)
        
        # Only check MVP quotas for MVP Factory tenants
        if tenant.tenant_type != TenantType.MVP_FACTORY:
            return True
        
        usage = await self.get_tenant_usage(tenant_id)
        from ..models.tenant_models import TenantQuotas
        quotas = TenantQuotas(**tenant.quotas)
        
        # MVP-specific quota checks
        mvp_quota_checks = {
            "concurrent_mvps": (self._get_concurrent_mvps(tenant_id), quotas.max_concurrent_mvps),
            "mvp_generations": (tenant.mvp_count_used + increment, quotas.max_mvp_generations),
            "cpu_cores": (self._get_current_cpu_usage(tenant_id) + increment, quotas.max_cpu_cores),
            "memory_gb": (self._get_current_memory_usage(tenant_id) + increment, quotas.max_memory_gb),
        }
        
        if quota_type not in mvp_quota_checks:
            # Fall back to standard quota check
            return await self.check_quota(tenant_id, quota_type, increment)
        
        current_usage, limit = mvp_quota_checks[quota_type]
        
        if current_usage > limit:
            logger.warning(
                f"MVP quota exceeded for tenant {tenant.slug}: {quota_type} "
                f"({current_usage}/{limit})"
            )
            return False
        
        return True
    
    async def increment_mvp_count(self, tenant_id: UUID) -> TenantORM:
        """Increment the MVP generation count for a tenant"""
        async with self._get_db() as db:
            try:
                await db.execute(
                    update(TenantORM)
                    .where(TenantORM.id == tenant_id)
                    .values(
                        mvp_count_used=TenantORM.mvp_count_used + 1,
                        updated_at=datetime.utcnow()
                    )
                )
                
                await db.commit()
                return await self.get_by_id(tenant_id)
                
            except Exception as e:
                await db.rollback()
                logger.error(f"Failed to increment MVP count for tenant {tenant_id}: {e}")
                raise
    
    async def get_mvp_factory_stats(self, tenant_id: UUID) -> Dict[str, Any]:
        """Get comprehensive stats for MVP Factory tenant"""
        async with self._get_db() as db:
            tenant = await self.get_by_id(tenant_id)
            
            if tenant.tenant_type != TenantType.MVP_FACTORY:
                raise InvalidTenantError("Stats are only available for MVP Factory tenants")
            
            # Get MVP project stats
            mvp_stats_result = await db.execute(
                select(
                    func.count().label("total_projects"),
                    func.count().filter(MVPProjectORM.status == "deployed").label("deployed_projects"),
                    func.count().filter(MVPProjectORM.status.in_(["generating", "testing", "deploying"])).label("active_generations"),
                    func.avg(MVPProjectORM.founder_satisfaction_score).label("avg_satisfaction"),
                    func.sum(MVPProjectORM.total_cost).label("total_cost"),
                    func.sum(MVPProjectORM.cpu_hours_used).label("total_cpu_hours"),
                    func.sum(MVPProjectORM.memory_gb_hours_used).label("total_memory_gb_hours"),
                    func.sum(MVPProjectORM.ai_tokens_used).label("total_ai_tokens")
                ).where(MVPProjectORM.tenant_id == tenant_id)
            )
            
            stats = mvp_stats_result.first()
            
            from ..models.tenant_models import TenantQuotas
            quotas = TenantQuotas(**tenant.quotas)
            
            return {
                "tenant_info": {
                    "id": str(tenant.id),
                    "founder_name": tenant.founder_name,
                    "business_description": tenant.business_description,
                    "plan": tenant.plan,
                    "created_at": tenant.created_at.isoformat()
                },
                "usage_stats": {
                    "mvp_generations_used": tenant.mvp_count_used,
                    "mvp_generations_limit": quotas.max_mvp_generations,
                    "total_projects": stats.total_projects or 0,
                    "deployed_projects": stats.deployed_projects or 0,
                    "active_generations": stats.active_generations or 0,
                    "success_rate": (stats.deployed_projects / max(stats.total_projects, 1)) * 100,
                },
                "satisfaction": {
                    "average_score": float(stats.avg_satisfaction or 0),
                    "total_responses": stats.total_projects or 0
                },
                "resource_usage": {
                    "total_cost_usd": float(stats.total_cost or 0),
                    "cpu_hours_used": float(stats.total_cpu_hours or 0),
                    "memory_gb_hours_used": float(stats.total_memory_gb_hours or 0),
                    "ai_tokens_used": int(stats.total_ai_tokens or 0)
                },
                "quotas": {
                    "max_concurrent_mvps": quotas.max_concurrent_mvps,
                    "max_cpu_cores": quotas.max_cpu_cores,
                    "max_memory_gb": quotas.max_memory_gb,
                    "max_deployment_duration_hours": quotas.max_deployment_duration_hours
                }
            }
    
    # Helper methods for MVP quota checking
    async def _get_concurrent_mvps(self, tenant_id: UUID) -> int:
        """Get current number of concurrent MVP generations"""
        async with self._get_db() as db:
            result = await db.execute(
                select(func.count()).where(
                    and_(
                        MVPProjectORM.tenant_id == tenant_id,
                        MVPProjectORM.status.in_(["generating", "testing", "deploying"])
                    )
                )
            )
            return result.scalar() or 0
    
    async def _get_current_cpu_usage(self, tenant_id: UUID) -> int:
        """Get current CPU core usage for active MVP generations"""
        # This would integrate with container orchestration (K8s, Docker)
        # For now, estimate based on concurrent MVPs
        concurrent_mvps = await self._get_concurrent_mvps(tenant_id)
        return concurrent_mvps * 2  # Assume 2 cores per active generation
    
    async def _get_current_memory_usage(self, tenant_id: UUID) -> int:
        """Get current memory usage for active MVP generations"""  
        # This would integrate with container orchestration (K8s, Docker)
        # For now, estimate based on concurrent MVPs
        concurrent_mvps = await self._get_concurrent_mvps(tenant_id)
        return concurrent_mvps * 4  # Assume 4GB per active generation


# Singleton service instance
tenant_service = TenantService()