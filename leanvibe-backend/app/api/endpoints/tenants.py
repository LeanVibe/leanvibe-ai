"""
Tenant management API endpoints for LeanVibe Enterprise SaaS Platform
Provides CRUD operations for multi-tenant architecture
"""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query, Path, Request
from fastapi.responses import JSONResponse

from ...models.tenant_models import (
    Tenant, TenantCreate, TenantUpdate, TenantUsage, 
    TenantStatus, TenantPlan
)
from ...services.tenant_service import tenant_service
from ...middleware.tenant_middleware import get_current_tenant, require_tenant
from ...auth.permissions import require_permission, Permission
from ...core.exceptions import (
    TenantNotFoundError, TenantQuotaExceededError, InvalidTenantError
)
from ...core.database import get_database_session
from sqlalchemy import select
from ...models.orm_models import TenantMemberORM

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/tenants", tags=["tenants"])


# Admin-only tenant management endpoints
@router.post("/", response_model=Tenant, status_code=201)
async def create_tenant(
    tenant_data: TenantCreate,
    _admin = Depends(require_permission(Permission.ADMIN_ALL))
) -> Tenant:
    """
    Create a new tenant (Admin only)
    
    Creates a new tenant with default quotas based on the selected plan.
    Automatically sets up trial period and initial configuration.
    """
    try:
        tenant = await tenant_service.create_tenant(tenant_data)
        logger.info(f"Created tenant: {tenant.slug} by admin")
        return tenant
        
    except InvalidTenantError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create tenant: {e}")
        raise HTTPException(status_code=500, detail="Failed to create tenant")


@router.get("/", response_model=List[Tenant])
async def list_tenants(
    status: Optional[TenantStatus] = Query(None, description="Filter by tenant status"),
    plan: Optional[TenantPlan] = Query(None, description="Filter by subscription plan"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of tenants to return"),
    offset: int = Query(0, ge=0, description="Number of tenants to skip"),
    _admin = Depends(require_permission(Permission.ADMIN_ALL))
) -> List[Tenant]:
    """
    List all tenants (Admin only)
    
    Returns paginated list of tenants with optional filtering by status and plan.
    """
    try:
        tenants = await tenant_service.list_tenants(
            status=status,
            plan=plan,
            limit=limit,
            offset=offset
        )
        return tenants
        
    except Exception as e:
        logger.error(f"Failed to list tenants: {e}")
        raise HTTPException(status_code=500, detail="Failed to list tenants")


@router.get("/{tenant_id}", response_model=Tenant)
async def get_tenant(
    tenant_id: UUID = Path(..., description="Tenant ID"),
    _admin = Depends(require_permission(Permission.ADMIN_ALL))
) -> Tenant:
    """
    Get tenant by ID (Admin only)
    
    Returns detailed information about a specific tenant.
    """
    try:
        tenant = await tenant_service.get_by_id(tenant_id)
        return tenant
        
    except TenantNotFoundError:
        raise HTTPException(status_code=404, detail="Tenant not found")
    except Exception as e:
        logger.error(f"Failed to get tenant {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve tenant")


@router.put("/{tenant_id}", response_model=Tenant)
async def update_tenant(
    tenant_id: UUID = Path(..., description="Tenant ID"),
    update_data: TenantUpdate = ...,
    _admin = Depends(require_permission(Permission.ADMIN_ALL))
) -> Tenant:
    """
    Update tenant (Admin only)
    
    Updates tenant information including plan changes, status updates, and configuration.
    Plan changes automatically update quota limits.
    """
    try:
        tenant = await tenant_service.update_tenant(tenant_id, update_data)
        logger.info(f"Updated tenant: {tenant.slug} by admin")
        return tenant
        
    except TenantNotFoundError:
        raise HTTPException(status_code=404, detail="Tenant not found")
    except Exception as e:
        logger.error(f"Failed to update tenant {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update tenant")


@router.post("/{tenant_id}/suspend")
async def suspend_tenant(
    tenant_id: UUID = Path(..., description="Tenant ID"),
    reason: Optional[str] = Query(None, description="Reason for suspension"),
    _admin = Depends(require_permission(Permission.ADMIN_ALL))
) -> JSONResponse:
    """
    Suspend tenant (Admin only)
    
    Suspends tenant access while preserving data. Suspended tenants cannot
    access the platform until reactivated.
    """
    try:
        tenant = await tenant_service.suspend_tenant(tenant_id, reason)
        logger.warning(f"Suspended tenant: {tenant.slug} (reason: {reason})")
        
        return JSONResponse(
            content={
                "message": f"Tenant {tenant.slug} has been suspended",
                "tenant_id": str(tenant.id),
                "status": tenant.status.value
            },
            status_code=200
        )
        
    except TenantNotFoundError:
        raise HTTPException(status_code=404, detail="Tenant not found")
    except Exception as e:
        logger.error(f"Failed to suspend tenant {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to suspend tenant")


@router.post("/{tenant_id}/reactivate")
async def reactivate_tenant(
    tenant_id: UUID = Path(..., description="Tenant ID"),
    _admin = Depends(require_permission(Permission.ADMIN_ALL))
) -> JSONResponse:
    """
    Reactivate suspended tenant (Admin only)
    
    Reactivates a suspended tenant, restoring full platform access.
    """
    try:
        tenant = await tenant_service.reactivate_tenant(tenant_id)
        logger.info(f"Reactivated tenant: {tenant.slug}")
        
        return JSONResponse(
            content={
                "message": f"Tenant {tenant.slug} has been reactivated",
                "tenant_id": str(tenant.id),
                "status": tenant.status.value
            },
            status_code=200
        )
        
    except TenantNotFoundError:
        raise HTTPException(status_code=404, detail="Tenant not found")
    except Exception as e:
        logger.error(f"Failed to reactivate tenant {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to reactivate tenant")


@router.delete("/{tenant_id}")
async def delete_tenant(
    tenant_id: UUID = Path(..., description="Tenant ID"),
    hard_delete: bool = Query(False, description="Permanently delete tenant data"),
    _admin = Depends(require_permission(Permission.ADMIN_ALL))
) -> JSONResponse:
    """
    Delete tenant (Admin only)
    
    Soft delete (default): Marks tenant as cancelled, preserves data for recovery
    Hard delete: Permanently removes all tenant data (irreversible)
    """
    try:
        success = await tenant_service.delete_tenant(tenant_id, hard_delete=hard_delete)
        
        if success:
            delete_type = "permanently deleted" if hard_delete else "cancelled"
            logger.warning(f"Tenant {tenant_id} {delete_type}")
            
            return JSONResponse(
                content={
                    "message": f"Tenant has been {delete_type}",
                    "tenant_id": str(tenant_id),
                    "hard_delete": hard_delete
                },
                status_code=200
            )
        else:
            raise HTTPException(status_code=404, detail="Tenant not found")
            
    except Exception as e:
        logger.error(f"Failed to delete tenant {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete tenant")


# Admin: list tenant members
@router.get("/{tenant_id}/members")
async def list_tenant_members(
    tenant_id: UUID = Path(..., description="Tenant ID"),
    _admin = Depends(require_permission(Permission.ADMIN_ALL)),
) -> List[dict]:
    async for session in get_database_session():
        result = await session.execute(select(TenantMemberORM).where(TenantMemberORM.tenant_id == tenant_id))
        rows = result.scalars().all()
        return [
            {
                "id": str(r.id),
                "tenant_id": str(r.tenant_id),
                "user_id": str(r.user_id),
                "email": r.email,
                "role": r.role,
                "status": r.status,
            }
            for r in rows
        ]


# Admin: update member role
@router.put("/{tenant_id}/members/{user_id}/role")
async def update_tenant_member_role(
    tenant_id: UUID,
    user_id: UUID,
    role: str = Query(..., description="New role"),
    request: Request = None,
    _admin = Depends(require_permission(Permission.ADMIN_ALL)),
):
    async for session in get_database_session():
        result = await session.execute(
            select(TenantMemberORM).where(
                TenantMemberORM.tenant_id == tenant_id,
                TenantMemberORM.user_id == user_id,
            )
        )
        member = result.scalar_one_or_none()
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
        old_role = member.role
        member.role = role
        await session.flush()
        # Audit
        try:
            from ...services.audit_service import audit_service
            await audit_service.log(
                tenant_id=tenant_id,
                action="tenant_role_change",
                resource_type="tenant_member",
                resource_id=str(member.id),
                details={
                    "user_id": str(user_id),
                    "old_role": old_role,
                    "new_role": role,
                    "ip": request.client.host if request and request.client else None,
                    "ua": request.headers.get("user-agent") if request else None,
                },
            )
        except Exception:
            pass
        return {"status": "ok", "old_role": old_role, "new_role": role}


# Tenant self-service endpoints (require tenant context)
@router.get("/me/info", response_model=Tenant)
async def get_current_tenant_info(
    current_tenant: Tenant = Depends(require_tenant)
) -> Tenant:
    """
    Get current tenant information
    
    Returns information about the tenant making the request.
    Requires valid tenant context.
    """
    return current_tenant


@router.put("/me/info", response_model=Tenant)
async def update_current_tenant_info(
    update_data: TenantUpdate,
    current_tenant: Tenant = Depends(require_tenant)
) -> Tenant:
    """
    Update current tenant information (self-service)
    
    Allows tenants to update their own information.
    Some fields like plan and status require admin privileges.
    """
    try:
        # Remove fields that require admin privileges
        restricted_fields = {"status", "plan", "quotas"}
        update_dict = update_data.dict(exclude_unset=True)
        
        for field in restricted_fields:
            if field in update_dict:
                logger.warning(f"Tenant {current_tenant.slug} attempted to update restricted field: {field}")
                del update_dict[field]
        
        # Create filtered update object
        filtered_update = TenantUpdate(**update_dict)
        
        tenant = await tenant_service.update_tenant(current_tenant.id, filtered_update)
        logger.info(f"Tenant {tenant.slug} updated their own info")
        return tenant
        
    except Exception as e:
        logger.error(f"Failed to update tenant info for {current_tenant.slug}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update tenant information")


@router.get("/me/usage", response_model=TenantUsage)
async def get_current_tenant_usage(
    current_tenant: Tenant = Depends(require_tenant)
) -> TenantUsage:
    """
    Get current tenant resource usage
    
    Returns current resource consumption against quotas.
    """
    try:
        usage = await tenant_service.get_tenant_usage(current_tenant.id)
        return usage
        
    except Exception as e:
        logger.error(f"Failed to get usage for tenant {current_tenant.slug}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve usage information")


@router.get("/me/quota-check/{quota_type}")
async def check_quota_availability(
    quota_type: str = Path(..., description="Type of quota to check"),
    amount: int = Query(1, ge=1, description="Amount to check availability for"),
    current_tenant: Tenant = Depends(require_tenant)
) -> dict:
    """
    Check quota availability for current tenant
    
    Returns whether the tenant can consume the requested amount of a specific resource.
    """
    try:
        available = await tenant_service.check_quota(
            current_tenant.id, 
            quota_type, 
            amount
        )
        
        usage = await tenant_service.get_tenant_usage(current_tenant.id)
        
        quota_limits = {
            "users": current_tenant.quotas.max_users,
            "projects": current_tenant.quotas.max_projects,
            "api_calls": current_tenant.quotas.max_api_calls_per_month,
            "storage_mb": current_tenant.quotas.max_storage_mb,
            "ai_requests": current_tenant.quotas.max_ai_requests_per_day,
            "concurrent_sessions": current_tenant.quotas.max_concurrent_sessions,
        }
        
        quota_usage = {
            "users": usage.users_count,
            "projects": usage.projects_count,
            "api_calls": usage.api_calls_this_month,
            "storage_mb": usage.storage_used_mb,
            "ai_requests": usage.ai_requests_today,
            "concurrent_sessions": usage.concurrent_sessions,
        }
        
        return {
            "quota_type": quota_type,
            "available": available,
            "current_usage": quota_usage.get(quota_type, 0),
            "quota_limit": quota_limits.get(quota_type, 0),
            "requested_amount": amount,
            "remaining": max(0, quota_limits.get(quota_type, 0) - quota_usage.get(quota_type, 0))
        }
        
    except Exception as e:
        logger.error(f"Failed to check quota for tenant {current_tenant.slug}: {e}")
        raise HTTPException(status_code=500, detail="Failed to check quota availability")


# Utility endpoints
@router.get("/slug/{slug}/exists")
async def check_slug_availability(
    slug: str = Path(..., description="Tenant slug to check"),
    _: dict = Depends(require_admin_permissions)
) -> dict:
    """
    Check if tenant slug is available (Admin only)
    
    Returns whether the specified slug is available for use.
    """
    try:
        existing = await tenant_service.get_by_slug(slug, raise_if_not_found=False)
        
        return {
            "slug": slug,
            "available": existing is None,
            "exists": existing is not None
        }
        
    except Exception as e:
        logger.error(f"Failed to check slug availability for {slug}: {e}")
        raise HTTPException(status_code=500, detail="Failed to check slug availability")