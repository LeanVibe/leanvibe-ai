"""
Comprehensive API Middleware Stack for LeanVibe Platform
Provides request/response processing, validation, rate limiting, and error handling
"""

import asyncio
import json
import time
import logging
from typing import Dict, Any, Optional, Callable
from uuid import uuid4

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Adds unique request ID to all requests for tracing"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate unique request ID
        request_id = str(uuid4())
        request.state.request_id = request_id
        
        # Add to headers for response
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Comprehensive request/response logging with performance metrics"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Extract request information
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        request_id = getattr(request.state, "request_id", "unknown")
        
        # Log incoming request
        logger.info(
            f"Request started: {request.method} {request.url.path} "
            f"- ID: {request_id} - IP: {client_ip}"
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log successful response
            logger.info(
                f"Request completed: {request.method} {request.url.path} "
                f"- Status: {response.status_code} - Time: {process_time:.3f}s "
                f"- ID: {request_id}"
            )
            
            # Add performance headers
            response.headers["X-Process-Time"] = f"{process_time:.3f}"
            
            return response
            
        except Exception as e:
            # Calculate processing time for errors
            process_time = time.time() - start_time
            
            # Log error
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"- Error: {str(e)} - Time: {process_time:.3f}s "
                f"- ID: {request_id}"
            )
            
            # Re-raise the exception
            raise


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Rate limiting with tenant-aware limits and sliding window"""
    
    def __init__(self, app: ASGIApp, default_rate_limit: int = 100):
        super().__init__(app)
        self.default_rate_limit = default_rate_limit
        self.request_counts: Dict[str, Dict[str, Any]] = {}
        self.window_size = 60  # 1 minute window
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Extract client identifier
        client_ip = request.client.host if request.client else "unknown"
        tenant_id = self._extract_tenant_id(request)
        client_key = f"{tenant_id}:{client_ip}" if tenant_id else client_ip
        
        # Check rate limit
        if await self._is_rate_limited(client_key, request):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "retry_after": self.window_size,
                    "limit": self._get_rate_limit(tenant_id),
                    "window": self.window_size
                },
                headers={
                    "Retry-After": str(self.window_size),
                    "X-RateLimit-Limit": str(self._get_rate_limit(tenant_id)),
                    "X-RateLimit-Window": str(self.window_size)
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        current_count = self.request_counts.get(client_key, {}).get("count", 0)
        response.headers["X-RateLimit-Limit"] = str(self._get_rate_limit(tenant_id))
        response.headers["X-RateLimit-Remaining"] = str(max(0, self._get_rate_limit(tenant_id) - current_count))
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + self.window_size))
        
        return response
    
    def _extract_tenant_id(self, request: Request) -> Optional[str]:
        """Extract tenant ID from request"""
        # Try to get from headers
        tenant_header = request.headers.get("X-Tenant-ID")
        if tenant_header:
            return tenant_header
        
        # Try to get from path
        path_parts = request.url.path.split("/")
        if len(path_parts) > 3 and path_parts[2] == "tenants":
            return path_parts[3]
        
        return None
    
    def _get_rate_limit(self, tenant_id: Optional[str]) -> int:
        """Get rate limit for tenant (can be customized per tenant)"""
        # TODO: Implement tenant-specific rate limits from database
        if tenant_id:
            # Higher limits for authenticated tenants
            return self.default_rate_limit * 2
        return self.default_rate_limit
    
    async def _is_rate_limited(self, client_key: str, request: Request) -> bool:
        """Check if client is rate limited using sliding window"""
        current_time = time.time()
        
        # Clean up old entries
        self._cleanup_old_entries(current_time)
        
        # Get current request count
        if client_key not in self.request_counts:
            self.request_counts[client_key] = {
                "count": 0,
                "window_start": current_time,
                "requests": []
            }
        
        client_data = self.request_counts[client_key]
        
        # Remove requests outside the current window
        window_start = current_time - self.window_size
        client_data["requests"] = [
            req_time for req_time in client_data["requests"] 
            if req_time > window_start
        ]
        
        # Update count
        client_data["count"] = len(client_data["requests"])
        
        # Check if limit exceeded
        rate_limit = self._get_rate_limit(self._extract_tenant_id(request))
        if client_data["count"] >= rate_limit:
            return True
        
        # Add current request
        client_data["requests"].append(current_time)
        client_data["count"] += 1
        
        return False
    
    def _cleanup_old_entries(self, current_time: float):
        """Clean up old entries to prevent memory leaks"""
        cutoff_time = current_time - (self.window_size * 2)  # Keep extra buffer
        
        keys_to_remove = []
        for client_key, data in self.request_counts.items():
            if data.get("window_start", 0) < cutoff_time:
                keys_to_remove.append(client_key)
        
        for key in keys_to_remove:
            del self.request_counts[key]


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds security headers to all responses"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add security headers
        for header, value in self.security_headers.items():
            response.headers[header] = value
        
        return response


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Validates request format, size, and content"""
    
    def __init__(self, app: ASGIApp, max_request_size: int = 10 * 1024 * 1024):  # 10MB
        super().__init__(app)
        self.max_request_size = max_request_size
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check content length
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_request_size:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={
                    "error": "Request entity too large",
                    "max_size": self.max_request_size,
                    "received_size": int(content_length)
                }
            )
        
        # Validate content type for POST/PUT requests
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if not self._is_valid_content_type(content_type):
                return JSONResponse(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    content={
                        "error": "Unsupported media type",
                        "supported_types": [
                            "application/json",
                            "application/x-www-form-urlencoded",
                            "multipart/form-data"
                        ]
                    }
                )
        
        return await call_next(request)
    
    def _is_valid_content_type(self, content_type: str) -> bool:
        """Check if content type is valid"""
        valid_types = [
            "application/json",
            "application/x-www-form-urlencoded",
            "multipart/form-data"
        ]
        
        # Handle charset parameter
        content_type = content_type.split(";")[0].strip()
        return content_type in valid_types


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Comprehensive error handling and response formatting"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        
        except HTTPException as e:
            # Handle FastAPI HTTP exceptions
            return await self._handle_http_exception(request, e)
        
        except ValueError as e:
            # Handle validation errors
            return await self._handle_validation_error(request, e)
        
        except asyncio.TimeoutError:
            # Handle timeout errors
            return await self._handle_timeout_error(request)
        
        except Exception as e:
            # Handle unexpected errors
            return await self._handle_unexpected_error(request, e)
    
    async def _handle_http_exception(self, request: Request, exc: HTTPException) -> JSONResponse:
        """Handle HTTP exceptions with proper formatting"""
        request_id = getattr(request.state, "request_id", "unknown")
        
        # Log the error
        logger.warning(
            f"HTTP Exception: {exc.status_code} - {exc.detail} "
            f"- Path: {request.url.path} - ID: {request_id}"
        )
        
        # Format error response
        error_response = {
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "type": "http_error",
                "request_id": request_id,
                "timestamp": time.time(),
                "path": str(request.url.path)
            }
        }
        
        # Add additional details for certain errors
        if exc.status_code == 422:  # Validation error
            error_response["error"]["type"] = "validation_error"
        elif exc.status_code == 401:  # Unauthorized
            error_response["error"]["type"] = "authentication_error"
        elif exc.status_code == 403:  # Forbidden
            error_response["error"]["type"] = "authorization_error"
        elif exc.status_code == 404:  # Not found
            error_response["error"]["type"] = "resource_not_found"
        elif exc.status_code == 429:  # Rate limited
            error_response["error"]["type"] = "rate_limit_exceeded"
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response,
            headers=getattr(exc, "headers", None)
        )
    
    async def _handle_validation_error(self, request: Request, exc: ValueError) -> JSONResponse:
        """Handle validation errors"""
        request_id = getattr(request.state, "request_id", "unknown")
        
        logger.warning(
            f"Validation Error: {str(exc)} "
            f"- Path: {request.url.path} - ID: {request_id}"
        )
        
        error_response = {
            "error": {
                "code": 400,
                "message": str(exc),
                "type": "validation_error",
                "request_id": request_id,
                "timestamp": time.time(),
                "path": str(request.url.path)
            }
        }
        
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response
        )
    
    async def _handle_timeout_error(self, request: Request) -> JSONResponse:
        """Handle timeout errors"""
        request_id = getattr(request.state, "request_id", "unknown")
        
        logger.error(
            f"Timeout Error: Request timeout "
            f"- Path: {request.url.path} - ID: {request_id}"
        )
        
        error_response = {
            "error": {
                "code": 504,
                "message": "Request timeout",
                "type": "timeout_error",
                "request_id": request_id,
                "timestamp": time.time(),
                "path": str(request.url.path)
            }
        }
        
        return JSONResponse(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            content=error_response
        )
    
    async def _handle_unexpected_error(self, request: Request, exc: Exception) -> JSONResponse:
        """Handle unexpected errors"""
        request_id = getattr(request.state, "request_id", "unknown")
        
        # Log the full error for debugging
        logger.error(
            f"Unexpected Error: {type(exc).__name__}: {str(exc)} "
            f"- Path: {request.url.path} - ID: {request_id}",
            exc_info=True
        )
        
        # Don't expose internal error details in production
        error_message = "Internal server error"
        error_details = None
        
        # In development, include more details
        import os
        if os.getenv("ENVIRONMENT") == "development":
            error_message = str(exc)
            error_details = {
                "exception_type": type(exc).__name__,
                "exception_message": str(exc)
            }
        
        error_response = {
            "error": {
                "code": 500,
                "message": error_message,
                "type": "internal_error",
                "request_id": request_id,
                "timestamp": time.time(),
                "path": str(request.url.path)
            }
        }
        
        if error_details:
            error_response["error"]["details"] = error_details
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response
        )


class CompressionMiddleware(BaseHTTPMiddleware):
    """Response compression for better performance"""
    
    def __init__(self, app: ASGIApp, minimum_size: int = 1024):
        super().__init__(app)
        self.minimum_size = minimum_size
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Check if client accepts compression
        accept_encoding = request.headers.get("accept-encoding", "")
        if "gzip" not in accept_encoding:
            return response
        
        # Check if response should be compressed
        content_type = response.headers.get("content-type", "")
        if not self._should_compress(content_type):
            return response
        
        # Check response size
        content_length = response.headers.get("content-length")
        if content_length and int(content_length) < self.minimum_size:
            return response
        
        # TODO: Implement actual gzip compression
        # For now, just add the header to indicate compression support
        response.headers["X-Compression-Available"] = "gzip"
        
        return response
    
    def _should_compress(self, content_type: str) -> bool:
        """Check if content type should be compressed"""
        compressible_types = [
            "application/json",
            "text/plain",
            "text/html",
            "text/css",
            "text/javascript",
            "application/javascript"
        ]
        
        for compressible_type in compressible_types:
            if content_type.startswith(compressible_type):
                return True
        
        return False


class CacheControlMiddleware(BaseHTTPMiddleware):
    """Sets appropriate cache control headers"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.cache_rules = {
            # API endpoints should not be cached by default
            "/api/": "no-cache, no-store, must-revalidate",
            # Static resources can be cached
            "/static/": "public, max-age=3600",
            # Health checks should not be cached
            "/health": "no-cache, no-store, must-revalidate"
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Set cache control based on path
        cache_control = self._get_cache_control(request.url.path)
        if cache_control:
            response.headers["Cache-Control"] = cache_control
        
        return response
    
    def _get_cache_control(self, path: str) -> Optional[str]:
        """Get cache control header for path"""
        for path_prefix, cache_control in self.cache_rules.items():
            if path.startswith(path_prefix):
                return cache_control
        
        # Default for API endpoints
        if path.startswith("/api/"):
            return "no-cache, no-store, must-revalidate"
        
        return None