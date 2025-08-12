"""
API Performance Optimization Service for LeanVibe Platform
Provides caching, pagination, response optimization, and performance monitoring
"""

import asyncio
import hashlib
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable
from uuid import UUID

from fastapi import Query, Request
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class CacheEntry(BaseModel):
    """Cache entry with metadata"""
    data: Any
    expires_at: datetime
    created_at: datetime
    access_count: int = 0
    last_accessed: datetime
    cache_key: str
    size_bytes: int = 0


class PaginationParams(BaseModel):
    """Standardized pagination parameters"""
    limit: int = Query(50, ge=1, le=100, description="Number of items per page")
    offset: int = Query(0, ge=0, description="Number of items to skip")
    sort_by: Optional[str] = Query(None, description="Field to sort by")
    sort_order: str = Query("asc", regex="^(asc|desc)$", description="Sort order")
    
    @property
    def page(self) -> int:
        """Calculate page number from offset and limit"""
        return (self.offset // self.limit) + 1


class PaginatedResponse(BaseModel):
    """Standardized paginated response"""
    data: List[Any]
    pagination: Dict[str, Any]
    
    @classmethod
    def create(cls, data: List[Any], params: PaginationParams, total_count: int):
        """Create paginated response with metadata"""
        total_pages = (total_count + params.limit - 1) // params.limit
        has_next = params.offset + params.limit < total_count
        has_prev = params.offset > 0
        
        pagination = {
            "total_count": total_count,
            "total_pages": total_pages,
            "current_page": params.page,
            "page_size": params.limit,
            "has_next": has_next,
            "has_previous": has_prev,
            "next_offset": params.offset + params.limit if has_next else None,
            "previous_offset": max(0, params.offset - params.limit) if has_prev else None
        }
        
        return cls(data=data, pagination=pagination)


class APIPerformanceService:
    """Service for API performance optimization"""
    
    def __init__(self):
        self.cache: Dict[str, CacheEntry] = {}
        self.performance_metrics: Dict[str, List[float]] = {}
        self.cache_hit_count = 0
        self.cache_miss_count = 0
        self.total_requests = 0
        
        # Start background cleanup task
        asyncio.create_task(self._cleanup_expired_cache())
    
    # Caching Methods
    
    def generate_cache_key(self, endpoint: str, params: Dict[str, Any], user_context: Optional[Dict] = None) -> str:
        """Generate unique cache key for request"""
        # Create deterministic key from parameters
        cache_data = {
            "endpoint": endpoint,
            "params": params
        }
        
        # Add user context if provided (for user-specific caching)
        if user_context:
            cache_data["user_id"] = user_context.get("user_id")
            cache_data["tenant_id"] = user_context.get("tenant_id")
        
        # Create hash of the data
        cache_str = json.dumps(cache_data, sort_keys=True, default=str)
        return hashlib.sha256(cache_str.encode()).hexdigest()
    
    async def get_cached_response(self, cache_key: str) -> Optional[Any]:
        """Get response from cache if available and not expired"""
        if cache_key not in self.cache:
            self.cache_miss_count += 1
            return None
        
        entry = self.cache[cache_key]
        
        # Check if expired
        if datetime.utcnow() > entry.expires_at:
            del self.cache[cache_key]
            self.cache_miss_count += 1
            return None
        
        # Update access metadata
        entry.access_count += 1
        entry.last_accessed = datetime.utcnow()
        
        self.cache_hit_count += 1
        logger.debug(f"Cache hit for key: {cache_key[:12]}...")
        
        return entry.data
    
    async def cache_response(
        self,
        cache_key: str,
        data: Any,
        ttl_seconds: int = 300,
        max_size_mb: float = 10.0
    ) -> bool:
        """Cache response data with TTL"""
        try:
            # Calculate data size
            data_str = json.dumps(data, default=str)
            size_bytes = len(data_str.encode('utf-8'))
            size_mb = size_bytes / (1024 * 1024)
            
            # Check size limit
            if size_mb > max_size_mb:
                logger.warning(f"Response too large to cache: {size_mb:.2f}MB > {max_size_mb}MB")
                return False
            
            # Create cache entry
            entry = CacheEntry(
                data=data,
                expires_at=datetime.utcnow() + timedelta(seconds=ttl_seconds),
                created_at=datetime.utcnow(),
                last_accessed=datetime.utcnow(),
                cache_key=cache_key,
                size_bytes=size_bytes
            )
            
            self.cache[cache_key] = entry
            logger.debug(f"Cached response: {cache_key[:12]}... (TTL: {ttl_seconds}s, Size: {size_mb:.2f}MB)")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache response: {e}")
            return False
    
    def invalidate_cache(self, pattern: Optional[str] = None, keys: Optional[List[str]] = None):
        """Invalidate cache entries by pattern or specific keys"""
        if keys:
            # Invalidate specific keys
            for key in keys:
                if key in self.cache:
                    del self.cache[key]
                    logger.debug(f"Invalidated cache key: {key[:12]}...")
        
        elif pattern:
            # Invalidate by pattern
            keys_to_remove = []
            for key in self.cache.keys():
                if pattern in key:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self.cache[key]
                logger.debug(f"Invalidated cache key by pattern '{pattern}': {key[:12]}...")
        
        else:
            # Clear all cache
            self.cache.clear()
            logger.info("Cleared all cache entries")
    
    async def _cleanup_expired_cache(self):
        """Background task to clean up expired cache entries"""
        while True:
            try:
                current_time = datetime.utcnow()
                expired_keys = []
                
                for key, entry in self.cache.items():
                    if current_time > entry.expires_at:
                        expired_keys.append(key)
                
                for key in expired_keys:
                    del self.cache[key]
                
                if expired_keys:
                    logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
                
                # Run cleanup every 5 minutes
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"Error in cache cleanup: {e}")
                await asyncio.sleep(60)  # Retry after 1 minute on error
    
    # Pagination Methods
    
    def paginate_list(self, data: List[Any], params: PaginationParams) -> PaginatedResponse:
        """Paginate a list of data"""
        total_count = len(data)
        
        # Apply sorting if specified
        if params.sort_by:
            data = self._sort_data(data, params.sort_by, params.sort_order)
        
        # Apply pagination
        start_idx = params.offset
        end_idx = start_idx + params.limit
        paginated_data = data[start_idx:end_idx]
        
        return PaginatedResponse.create(paginated_data, params, total_count)
    
    async def paginate_query(
        self,
        query_func: Callable,
        params: PaginationParams,
        **query_kwargs
    ) -> PaginatedResponse:
        """Paginate a database query or async function"""
        # Get total count (if query_func supports it)
        if hasattr(query_func, 'count'):
            total_count = await query_func.count(**query_kwargs)
        else:
            # Fallback: execute query without pagination to get count
            all_data = await query_func(**query_kwargs)
            total_count = len(all_data) if isinstance(all_data, list) else 0
        
        # Execute paginated query
        query_kwargs.update({
            'limit': params.limit,
            'offset': params.offset,
            'sort_by': params.sort_by,
            'sort_order': params.sort_order
        })
        
        data = await query_func(**query_kwargs)
        
        return PaginatedResponse.create(data, params, total_count)
    
    def _sort_data(self, data: List[Any], sort_by: str, sort_order: str) -> List[Any]:
        """Sort data by specified field"""
        try:
            reverse = sort_order.lower() == "desc"
            
            # Handle different data types
            if isinstance(data[0], dict):
                # Sort dictionaries
                return sorted(data, key=lambda x: x.get(sort_by, ""), reverse=reverse)
            elif hasattr(data[0], sort_by):
                # Sort objects with attributes
                return sorted(data, key=lambda x: getattr(x, sort_by, ""), reverse=reverse)
            else:
                logger.warning(f"Cannot sort by field '{sort_by}' - field not found")
                return data
                
        except Exception as e:
            logger.error(f"Error sorting data: {e}")
            return data
    
    # Response Optimization Methods
    
    def optimize_response(self, data: Any, include_fields: Optional[List[str]] = None, exclude_fields: Optional[List[str]] = None) -> Any:
        """Optimize response by including/excluding specific fields"""
        if not isinstance(data, (dict, list)):
            return data
        
        if isinstance(data, list):
            return [self.optimize_response(item, include_fields, exclude_fields) for item in data]
        
        if isinstance(data, dict):
            result = {}
            
            # Include specific fields
            if include_fields:
                for field in include_fields:
                    if field in data:
                        result[field] = data[field]
            else:
                result = data.copy()
            
            # Exclude specific fields
            if exclude_fields:
                for field in exclude_fields:
                    result.pop(field, None)
            
            return result
        
        return data
    
    def compress_response(self, data: Any, compression_level: str = "medium") -> Any:
        """Compress response data by removing verbose fields"""
        compression_configs = {
            "light": {
                "remove_null_fields": True,
                "truncate_long_strings": False,
                "remove_metadata": False
            },
            "medium": {
                "remove_null_fields": True,
                "truncate_long_strings": True,
                "remove_metadata": True,
                "max_string_length": 500
            },
            "aggressive": {
                "remove_null_fields": True,
                "truncate_long_strings": True,
                "remove_metadata": True,
                "max_string_length": 200,
                "remove_timestamps": True,
                "remove_ids": False
            }
        }
        
        config = compression_configs.get(compression_level, compression_configs["medium"])
        return self._apply_compression(data, config)
    
    def _apply_compression(self, data: Any, config: Dict[str, Any]) -> Any:
        """Apply compression configuration to data"""
        if isinstance(data, list):
            return [self._apply_compression(item, config) for item in data]
        
        if isinstance(data, dict):
            result = {}
            
            for key, value in data.items():
                # Remove null fields
                if config.get("remove_null_fields") and value is None:
                    continue
                
                # Remove metadata fields
                if config.get("remove_metadata") and key in ["created_at", "updated_at", "metadata", "_meta"]:
                    continue
                
                # Remove timestamp fields
                if config.get("remove_timestamps") and key.endswith("_at"):
                    continue
                
                # Remove ID fields (except primary)
                if config.get("remove_ids") and key.endswith("_id") and key != "id":
                    continue
                
                # Truncate long strings
                if config.get("truncate_long_strings") and isinstance(value, str):
                    max_length = config.get("max_string_length", 500)
                    if len(value) > max_length:
                        value = value[:max_length] + "..."
                
                # Recursively apply to nested objects
                if isinstance(value, (dict, list)):
                    value = self._apply_compression(value, config)
                
                result[key] = value
            
            return result
        
        return data
    
    # Performance Monitoring Methods
    
    def track_request_performance(self, endpoint: str, duration_ms: float):
        """Track request performance metrics"""
        if endpoint not in self.performance_metrics:
            self.performance_metrics[endpoint] = []
        
        self.performance_metrics[endpoint].append(duration_ms)
        
        # Keep only last 1000 measurements
        if len(self.performance_metrics[endpoint]) > 1000:
            self.performance_metrics[endpoint] = self.performance_metrics[endpoint][-1000:]
        
        self.total_requests += 1
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        cache_total = self.cache_hit_count + self.cache_miss_count
        cache_hit_rate = (self.cache_hit_count / cache_total * 100) if cache_total > 0 else 0
        
        endpoint_stats = {}
        for endpoint, durations in self.performance_metrics.items():
            if durations:
                endpoint_stats[endpoint] = {
                    "count": len(durations),
                    "avg_duration_ms": sum(durations) / len(durations),
                    "min_duration_ms": min(durations),
                    "max_duration_ms": max(durations),
                    "p95_duration_ms": self._percentile(durations, 95),
                    "p99_duration_ms": self._percentile(durations, 99)
                }
        
        return {
            "cache_stats": {
                "hit_count": self.cache_hit_count,
                "miss_count": self.cache_miss_count,
                "hit_rate_percent": cache_hit_rate,
                "total_entries": len(self.cache),
                "total_size_mb": sum(entry.size_bytes for entry in self.cache.values()) / (1024 * 1024)
            },
            "request_stats": {
                "total_requests": self.total_requests,
                "endpoints": endpoint_stats
            }
        }
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of data"""
        if not data:
            return 0.0
        
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        if index >= len(sorted_data):
            index = len(sorted_data) - 1
        
        return sorted_data[index]
    
    # Cache Warming Methods
    
    async def warm_cache(self, warmup_requests: List[Dict[str, Any]]):
        """Pre-warm cache with common requests"""
        logger.info(f"Starting cache warmup with {len(warmup_requests)} requests")
        
        for request in warmup_requests:
            try:
                cache_key = self.generate_cache_key(
                    request["endpoint"],
                    request.get("params", {}),
                    request.get("user_context")
                )
                
                # Skip if already cached
                if cache_key in self.cache:
                    continue
                
                # TODO: Execute actual request to warm cache
                # For now, just log the warmup attempt
                logger.debug(f"Would warm cache for: {request['endpoint']}")
                
            except Exception as e:
                logger.error(f"Error warming cache for request {request}: {e}")
        
        logger.info("Cache warmup completed")


# Global performance service instance
api_performance_service = APIPerformanceService()


# Decorator for caching API responses
def cached_response(ttl_seconds: int = 300, cache_key_func: Optional[Callable] = None):
    """Decorator for caching API endpoint responses"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract request from arguments
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                # No request found, execute without caching
                return await func(*args, **kwargs)
            
            # Generate cache key
            if cache_key_func:
                cache_key = cache_key_func(request, *args, **kwargs)
            else:
                cache_key = api_performance_service.generate_cache_key(
                    request.url.path,
                    dict(request.query_params)
                )
            
            # Try to get from cache
            cached_result = await api_performance_service.get_cached_response(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            await api_performance_service.cache_response(cache_key, result, ttl_seconds)
            
            return result
        
        return wrapper
    return decorator


# Decorator for performance tracking
def track_performance(endpoint_name: Optional[str] = None):
    """Decorator for tracking endpoint performance"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration_ms = (time.time() - start_time) * 1000
                endpoint = endpoint_name or func.__name__
                api_performance_service.track_request_performance(endpoint, duration_ms)
        
        return wrapper
    return decorator