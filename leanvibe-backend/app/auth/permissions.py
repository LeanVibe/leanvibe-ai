"""
Permission system for LeanVibe Enterprise SaaS Platform
Provides role-based access control and permission management
"""

import logging
from typing import Dict, List, Optional
from fastapi import HTTPException, Depends, Request
from ..middleware.tenant_middleware import get_current_tenant, get_current_user_id

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
    """Get user permissions for the given tenant (mock implementation)"""
    # This would typically query the database for user roles and permissions
    # For now, return mock permissions
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
        
        # For now, allow all authenticated users (will implement properly with auth system)
        return {"user_id": user_id, "tenant_id": tenant_id, "permissions": [permission]}
    
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