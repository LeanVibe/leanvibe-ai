"""
Multi-tenant middleware for LeanVibe Enterprise SaaS Platform
Provides tenant context injection and isolation validation
"""

import logging
from typing import Callable, Optional
from uuid import UUID

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..models.tenant_models import Tenant, TenantStatus
from ..services.tenant_service import TenantService
from ..core.security import verify_api_key

logger = logging.getLogger(__name__)


class TenantContext:
    """Thread-local tenant context for request isolation"""
    
    def __init__(self):
        self._tenant: Optional[Tenant] = None
        self._user_id: Optional[UUID] = None
    
    @property
    def tenant(self) -> Optional[Tenant]:
        return self._tenant
    
    @tenant.setter
    def tenant(self, tenant: Optional[Tenant]):
        self._tenant = tenant
    
    @property
    def user_id(self) -> Optional[UUID]:
        return self._user_id
    
    @user_id.setter
    def user_id(self, user_id: Optional[UUID]):
        self._user_id = user_id
    
    @property
    def tenant_id(self) -> Optional[UUID]:
        return self._tenant.id if self._tenant else None
    
    def clear(self):
        """Clear the current context"""
        self._tenant = None
        self._user_id = None
    
    def is_valid(self) -> bool:
        """Check if context has valid tenant"""
        return self._tenant is not None and self._tenant.status == TenantStatus.ACTIVE


# Global tenant context instance
tenant_context = TenantContext()


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract tenant context from request and inject into thread-local storage
    
    Supports multiple tenant identification strategies:
    1. Subdomain-based: tenant-slug.leanvibe.ai
    2. Header-based: X-Tenant-ID or X-Tenant-Slug
    3. API key-based: API key includes tenant context
    4. JWT-based: JWT token contains tenant claims
    """
    
    def __init__(self, app, tenant_service: TenantService):
        super().__init__(app)
        self.tenant_service = tenant_service
        
        # Routes that don't require tenant context
        self.exempt_paths = {
            "/health",
            "/docs",
            "/openapi.json",
            "/admin/tenants",  # Admin endpoints
            "/auth/login",
            "/auth/register"
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with tenant context injection"""
        
        # Clear any existing context
        tenant_context.clear()
        
        # Skip tenant resolution for exempt paths
        if any(request.url.path.startswith(path) for path in self.exempt_paths):
            return await call_next(request)
        
        try:
            # Extract tenant from request
            tenant = await self._extract_tenant(request)
            
            if tenant:
                # Validate tenant status
                if tenant.status != TenantStatus.ACTIVE:
                    return JSONResponse(
                        status_code=403,
                        content={
                            "error": "tenant_suspended",
                            "message": f"Tenant is {tenant.status.value}",
                            "tenant_id": str(tenant.id)
                        }
                    )
                
                # Set tenant context
                tenant_context.tenant = tenant
                
                # Extract user context if available
                user_id = await self._extract_user_id(request, tenant)
                tenant_context.user_id = user_id
                
                # Add tenant info to request state for easy access
                request.state.tenant = tenant
                request.state.tenant_id = tenant.id
                request.state.user_id = user_id
                
                logger.info(f"Request processed for tenant: {tenant.slug} (user: {user_id})")
                
            else:
                # No tenant found - return error for API endpoints
                if request.url.path.startswith("/api/"):
                    return JSONResponse(
                        status_code=400,
                        content={
                            "error": "tenant_required",
                            "message": "Valid tenant context is required for API endpoints"
                        }
                    )
            
            # Process request
            response = await call_next(request)
            
            # Add tenant info to response headers (for debugging)
            if tenant:
                response.headers["X-Tenant-ID"] = str(tenant.id)
                response.headers["X-Tenant-Slug"] = tenant.slug
            
            return response
            
        except HTTPException as e:
            return JSONResponse(
                status_code=e.status_code,
                content={"error": "tenant_error", "message": str(e.detail)}
            )
        
        except Exception as e:
            logger.error(f"Tenant middleware error: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "error": "tenant_middleware_error",
                    "message": "Internal server error in tenant processing"
                }
            )
        
        finally:
            # Always clear context after request
            tenant_context.clear()
    
    async def _extract_tenant(self, request: Request) -> Optional[Tenant]:
        """Extract tenant from request using multiple strategies"""
        
        # Strategy 1: Subdomain extraction (tenant-slug.leanvibe.ai)
        tenant = await self._extract_from_subdomain(request)
        if tenant:
            return tenant
        
        # Strategy 2: Header-based extraction
        tenant = await self._extract_from_headers(request)
        if tenant:
            return tenant
        
        # Strategy 3: API key-based extraction
        tenant = await self._extract_from_api_key(request)
        if tenant:
            return tenant
        
        # Strategy 4: JWT-based extraction (future implementation)
        # tenant = await self._extract_from_jwt(request)
        # if tenant:
        #     return tenant
        
        return None
    
    async def _extract_from_subdomain(self, request: Request) -> Optional[Tenant]:
        """Extract tenant from subdomain (e.g., acme.leanvibe.ai)"""
        host = request.headers.get("host", "")
        
        # Parse subdomain
        if "." in host:
            subdomain = host.split(".")[0]
            
            # Skip common non-tenant subdomains
            if subdomain not in ["www", "api", "admin", "app", "staging", "localhost"]:
                try:
                    return await self.tenant_service.get_by_slug(subdomain)
                except Exception as e:
                    logger.warning(f"Failed to resolve tenant from subdomain {subdomain}: {e}")
        
        return None
    
    async def _extract_from_headers(self, request: Request) -> Optional[Tenant]:
        """Extract tenant from request headers"""
        
        # Try X-Tenant-ID header (UUID)
        tenant_id = request.headers.get("X-Tenant-ID")
        if tenant_id:
            try:
                tenant_uuid = UUID(tenant_id)
                return await self.tenant_service.get_by_id(tenant_uuid)
            except (ValueError, Exception) as e:
                logger.warning(f"Invalid tenant ID in header {tenant_id}: {e}")
        
        # Try X-Tenant-Slug header
        tenant_slug = request.headers.get("X-Tenant-Slug")
        if tenant_slug:
            try:
                return await self.tenant_service.get_by_slug(tenant_slug)
            except Exception as e:
                logger.warning(f"Failed to resolve tenant from slug {tenant_slug}: {e}")
        
        return None
    
    async def _extract_from_api_key(self, request: Request) -> Optional[Tenant]:
        """Extract tenant from API key"""
        
        # Get API key from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        
        api_key = auth_header.replace("Bearer ", "")
        
        try:
            # Verify API key and extract tenant context
            # This would integrate with your existing API key auth system
            tenant_id = await self._verify_api_key_and_get_tenant(api_key)
            if tenant_id:
                return await self.tenant_service.get_by_id(tenant_id)
        except Exception as e:
            logger.warning(f"Failed to resolve tenant from API key: {e}")
        
        return None
    
    async def _extract_user_id(self, request: Request, tenant: Tenant) -> Optional[UUID]:
        """Extract user ID from request context"""
        
        # Try to extract from JWT token if available
        # This would integrate with your authentication system
        
        # For now, return None - will be implemented with auth system
        return None
    
    async def _verify_api_key_and_get_tenant(self, api_key: str) -> Optional[UUID]:
        """Verify API key and return associated tenant ID"""
        
        # This would integrate with your existing API key verification
        # For now, return None - needs integration with auth system
        
        # Example implementation:
        # api_key_info = await verify_api_key(api_key)
        # return api_key_info.tenant_id if api_key_info else None
        
        return None


def get_current_tenant() -> Optional[Tenant]:
    """Get current tenant from thread-local context"""
    return tenant_context.tenant


def get_current_tenant_id() -> Optional[UUID]:
    """Get current tenant ID from thread-local context"""
    return tenant_context.tenant_id


def get_current_user_id() -> Optional[UUID]:
    """Get current user ID from thread-local context"""
    return tenant_context.user_id


def require_tenant() -> Tenant:
    """Require valid tenant context, raise exception if not available"""
    tenant = tenant_context.tenant
    if not tenant:
        raise HTTPException(
            status_code=400,
            detail="Tenant context is required for this operation"
        )
    
    if tenant.status != TenantStatus.ACTIVE:
        raise HTTPException(
            status_code=403,
            detail=f"Tenant is {tenant.status.value}"
        )
    
    return tenant


def require_user() -> UUID:
    """Require valid user context, raise exception if not available"""
    user_id = tenant_context.user_id
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="User authentication is required for this operation"
        )
    
    return user_id