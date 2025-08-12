"""
Permission system for LeanVibe Enterprise SaaS Platform
Provides role-based access control and permission management
"""

import logging
from typing import Dict, List, Optional
from fastapi import HTTPException, Depends, Request
from ..middleware.tenant_middleware import get_current_tenant, get_current_user_id
from ..core.database import get_database_session
from ..models.orm_models import TenantMemberORM

logger = logging.getLogger(__name__)


class Permission:
    """Permission definitions"""
    
    # Admin permissions
    ADMIN_ALL = "admin:all"
    ADMIN_TENANTS = "admin:tenants"
    ADMIN_USERS = "admin:users"
    ADMIN_BILLING = "admin:billing"
    
    # Tenant permissions
    TENANT_READ = "tenant:read"
    TENANT_WRITE = "tenant:write"
    TENANT_ADMIN = "tenant:admin"
    
    # Project permissions
    PROJECT_CREATE = "project:create"
    PROJECT_READ = "project:read"
    PROJECT_WRITE = "project:write"
    PROJECT_DELETE = "project:delete"
    
    # Task permissions
    TASK_CREATE = "task:create"
    TASK_READ = "task:read"
    TASK_WRITE = "task:write"
    TASK_DELETE = "task:delete"


class Role:
    """Role definitions with associated permissions"""
    
    SYSTEM_ADMIN = {
        "name": "system_admin",
        "permissions": [Permission.ADMIN_ALL]
    }
    
    TENANT_ADMIN = {
        "name": "tenant_admin",
        "permissions": [
            Permission.TENANT_ADMIN,
            Permission.PROJECT_CREATE,
            Permission.PROJECT_READ,
            Permission.PROJECT_WRITE,
            Permission.PROJECT_DELETE,
            Permission.TASK_CREATE,
            Permission.TASK_READ,
            Permission.TASK_WRITE,
            Permission.TASK_DELETE,
        ]
    }
    
    TENANT_USER = {
        "name": "tenant_user",
        "permissions": [
            Permission.TENANT_READ,
            Permission.PROJECT_READ,
            Permission.PROJECT_WRITE,
            Permission.TASK_CREATE,
            Permission.TASK_READ,
            Permission.TASK_WRITE,
        ]
    }
    
    TENANT_VIEWER = {
        "name": "tenant_viewer",
        "permissions": [
            Permission.TENANT_READ,
            Permission.PROJECT_READ,
            Permission.TASK_READ,
        ]
    }


async def get_user_permissions(user_id: str, tenant_id: str = None) -> List[str]:
    """Get user permissions for the given tenant.

    Best-effort DB lookup of `TenantMemberORM` to resolve role and map to permissions.
    Falls back to read-only permissions if lookup fails.
    """
    try:
        if not user_id or not tenant_id:
            return []
        role_name: Optional[str] = None
        async for session in get_database_session():
            result = await session.execute(
                select(TenantMemberORM).where(
                    (TenantMemberORM.user_id == user_id) & (TenantMemberORM.tenant_id == tenant_id)
                )
            )
            member = result.scalar_one_or_none()
            if member:
                role_name = (member.role or '').lower()
            break
        # Map roles to permissions
        if role_name == Role.SYSTEM_ADMIN["name"]:
            return Role.SYSTEM_ADMIN["permissions"]
        if role_name == Role.TENANT_ADMIN["name"]:
            return Role.TENANT_ADMIN["permissions"]
        if role_name == Role.TENANT_USER["name"]:
            return Role.TENANT_USER["permissions"]
        if role_name == Role.TENANT_VIEWER["name"]:
            return Role.TENANT_VIEWER["permissions"]
        # Default minimal permissions
        return [Permission.TENANT_READ, Permission.PROJECT_READ, Permission.TASK_READ]
    except Exception:
        # Fail-safe: read-only
        return [Permission.TENANT_READ, Permission.PROJECT_READ, Permission.TASK_READ]


async def check_permission(permission: str, user_id: str = None, tenant_id: str = None) -> bool:
    """Check if user has specific permission"""
    if not user_id:
        return False
    
    user_permissions = await get_user_permissions(user_id, tenant_id)
    
    # Check for wildcard admin permission
    if Permission.ADMIN_ALL in user_permissions:
        return True
    
    # Check for specific permission
    return permission in user_permissions


async def require_permission(permission: str):
    """Dependency to require specific permission"""
    def permission_dependency(request: Request):
        # Get current user and tenant from middleware
        user_id = getattr(request.state, 'user_id', None)
        tenant_id = getattr(request.state, 'tenant_id', None)
        
        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Authentication required"
            )
        
        # Enforce permission
        from sqlalchemy import select  # local import to avoid global dependency early
        perms = []
        try:
            perms = await get_user_permissions(str(user_id), str(tenant_id) if tenant_id else None)
        except Exception:
            perms = []
        if Permission.ADMIN_ALL in perms or permission in perms:
            return {"user_id": user_id, "tenant_id": tenant_id, "permissions": perms}
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    return permission_dependency


async def require_admin_permissions():
    """Dependency to require admin permissions (mock implementation)"""
    # This would integrate with the actual authentication system
    # For now, return mock admin context
    return {"user_id": "admin", "role": "admin", "permissions": [Permission.ADMIN_ALL]}


async def require_tenant_admin():
    """Dependency to require tenant admin permissions"""
    return await require_permission(Permission.TENANT_ADMIN)


async def require_tenant_user():
    """Dependency to require tenant user permissions"""
    return await require_permission(Permission.TENANT_READ)