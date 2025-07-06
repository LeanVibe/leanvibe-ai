"""
Performance optimizations for LeanVibe CLI

This module contains various optimizations to improve CLI performance:
- Lazy imports
- Connection pooling
- Response caching
- Command batching
"""

import asyncio
import time
from typing import Dict, Any, Optional, List, Callable
from functools import wraps, lru_cache
from dataclasses import dataclass
import threading


@dataclass
class PerformanceMetrics:
    """Track performance metrics for optimization"""
    command_times: Dict[str, List[float]]
    connection_times: List[float]
    cache_hits: int
    cache_misses: int
    
    def __post_init__(self):
        if not hasattr(self, 'command_times'):
            self.command_times = {}
        if not hasattr(self, 'connection_times'):
            self.connection_times = []


# Global performance tracker
_perf_metrics = PerformanceMetrics({}, [], 0, 0)


def performance_tracker(func_name: str):
    """Decorator to track function performance"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.perf_counter() - start_time
                if func_name not in _perf_metrics.command_times:
                    _perf_metrics.command_times[func_name] = []
                _perf_metrics.command_times[func_name].append(duration * 1000)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.perf_counter() - start_time
                if func_name not in _perf_metrics.command_times:
                    _perf_metrics.command_times[func_name] = []
                _perf_metrics.command_times[func_name].append(duration * 1000)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


class LazyImporter:
    """Lazy import manager to reduce startup time"""
    
    def __init__(self):
        self._modules = {}
        self._lock = threading.Lock()
    
    def get_module(self, module_name: str, from_name: Optional[str] = None):
        """Get module with lazy loading"""
        cache_key = f"{module_name}.{from_name}" if from_name else module_name
        
        if cache_key in self._modules:
            return self._modules[cache_key]
        
        with self._lock:
            if cache_key in self._modules:
                return self._modules[cache_key]
            
            try:
                if from_name:
                    module = __import__(module_name, fromlist=[from_name])
                    self._modules[cache_key] = getattr(module, from_name)
                else:
                    self._modules[cache_key] = __import__(module_name)
                
                return self._modules[cache_key]
            except ImportError:
                return None


# Global lazy importer
lazy_import = LazyImporter()


class ResponseCache:
    """Intelligent response caching with TTL and size limits"""
    
    def __init__(self, max_size: int = 100, default_ttl: int = 30):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache = {}
        self._timestamps = {}
        self._access_times = {}
        self._lock = threading.Lock()
    
    def get(self, key: str, ttl: Optional[int] = None) -> Optional[Any]:
        """Get cached value if valid"""
        effective_ttl = ttl or self.default_ttl
        
        with self._lock:
            if key not in self._cache:
                _perf_metrics.cache_misses += 1
                return None
            
            # Check TTL
            if time.time() - self._timestamps[key] > effective_ttl:
                self._remove(key)
                _perf_metrics.cache_misses += 1
                return None
            
            # Update access time for LRU
            self._access_times[key] = time.time()
            _perf_metrics.cache_hits += 1
            return self._cache[key]
    
    def set(self, key: str, value: Any) -> None:
        """Set cached value with cleanup if needed"""
        with self._lock:
            # Clean up if at capacity
            if len(self._cache) >= self.max_size:
                self._cleanup_lru()
            
            self._cache[key] = value
            self._timestamps[key] = time.time()
            self._access_times[key] = time.time()
    
    def _remove(self, key: str) -> None:
        """Remove key from all caches"""
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)
        self._access_times.pop(key, None)
    
    def _cleanup_lru(self) -> None:
        """Remove least recently used items"""
        if not self._access_times:
            return
        
        # Remove 20% of items
        num_to_remove = max(1, len(self._cache) // 5)
        
        # Sort by access time and remove oldest
        sorted_items = sorted(self._access_times.items(), key=lambda x: x[1])
        for key, _ in sorted_items[:num_to_remove]:
            self._remove(key)
    
    def clear_expired(self) -> int:
        """Clear expired entries and return count"""
        current_time = time.time()
        expired_keys = []
        
        with self._lock:
            for key, timestamp in self._timestamps.items():
                if current_time - timestamp > self.default_ttl:
                    expired_keys.append(key)
            
            for key in expired_keys:
                self._remove(key)
        
        return len(expired_keys)


# Global response cache
response_cache = ResponseCache()


class ConnectionPool:
    """HTTP connection pool manager"""
    
    def __init__(self, max_connections: int = 5):
        self.max_connections = max_connections
        self._connections = {}
        self._lock = asyncio.Lock()
    
    async def get_client(self, base_url: str, timeout: int = 30):
        """Get or create HTTP client for base URL"""
        async with self._lock:
            if base_url not in self._connections:
                # Lazy import httpx
                httpx = lazy_import.get_module('httpx')
                if httpx:
                    # Check if HTTP/2 is available
                    try:
                        import h2
                        http2_enabled = True
                    except ImportError:
                        http2_enabled = False
                    
                    self._connections[base_url] = httpx.AsyncClient(
                        base_url=base_url,
                        timeout=httpx.Timeout(connect=5.0, read=timeout, write=10.0, pool=5.0),
                        limits=httpx.Limits(max_keepalive_connections=3, max_connections=self.max_connections),
                        http2=http2_enabled
                    )
            
            return self._connections.get(base_url)
    
    async def close_all(self):
        """Close all connections"""
        async with self._lock:
            for client in self._connections.values():
                await client.aclose()
            self._connections.clear()


# Global connection pool
connection_pool = ConnectionPool()


def batch_requests(min_batch_size: int = 2, max_wait_ms: int = 100):
    """Decorator to batch similar requests for better performance"""
    def decorator(func):
        _pending_requests = []
        _batch_timer = None
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            nonlocal _batch_timer
            
            # Add to pending batch
            future = asyncio.Future()
            _pending_requests.append((args, kwargs, future))
            
            # Start batch timer if not running
            if _batch_timer is None or _batch_timer.done():
                async def execute_batch():
                    await asyncio.sleep(max_wait_ms / 1000)
                    
                    if len(_pending_requests) >= min_batch_size:
                        # Execute batch
                        requests = _pending_requests.copy()
                        _pending_requests.clear()
                        
                        for req_args, req_kwargs, req_future in requests:
                            try:
                                result = await func(*req_args, **req_kwargs)
                                req_future.set_result(result)
                            except Exception as e:
                                req_future.set_exception(e)
                    else:
                        # Execute individually if batch too small
                        for req_args, req_kwargs, req_future in _pending_requests:
                            try:
                                result = await func(*req_args, **req_kwargs)
                                req_future.set_result(result)
                            except Exception as e:
                                req_future.set_exception(e)
                        _pending_requests.clear()
                
                _batch_timer = asyncio.create_task(execute_batch())
            
            return await future
        
        return wrapper
    return decorator


@lru_cache(maxsize=32)
def get_optimized_timeout(operation_type: str, complexity: str = "simple") -> float:
    """Get optimized timeout based on operation type and complexity"""
    timeouts = {
        "health_check": {"simple": 2.0, "complex": 5.0},
        "query": {"simple": 30.0, "complex": 60.0},  # Increased for L3 agent initialization
        "websocket": {"simple": 5.0, "complex": 15.0},
        "command": {"simple": 5.0, "complex": 15.0},
        "analysis": {"simple": 15.0, "complex": 60.0}
    }
    
    return timeouts.get(operation_type, {}).get(complexity, 30.0)


def preload_critical_modules():
    """Preload critical modules in background to reduce latency"""
    critical_modules = [
        'json',
        'asyncio',
        'httpx',
        'websockets',
        'rich.console',
        'rich.table',
        'click'
    ]
    
    for module in critical_modules:
        lazy_import.get_module(module)


class PerformanceMonitor:
    """Monitor and report performance metrics"""
    
    @staticmethod
    def get_metrics() -> Dict[str, Any]:
        """Get current performance metrics"""
        return {
            "command_times": _perf_metrics.command_times,
            "connection_times": _perf_metrics.connection_times,
            "cache_hits": _perf_metrics.cache_hits,
            "cache_misses": _perf_metrics.cache_misses,
            "cache_hit_rate": (_perf_metrics.cache_hits / 
                             max(1, _perf_metrics.cache_hits + _perf_metrics.cache_misses)),
            "avg_command_time": {
                cmd: sum(times) / len(times) 
                for cmd, times in _perf_metrics.command_times.items()
            } if _perf_metrics.command_times else {}
        }
    
    @staticmethod
    def reset_metrics():
        """Reset performance metrics"""
        global _perf_metrics
        _perf_metrics = PerformanceMetrics({}, [], 0, 0)
    
    @staticmethod
    def cleanup_resources():
        """Cleanup resources and expired cache entries"""
        expired = response_cache.clear_expired()
        return {"expired_cache_entries": expired}


# Export optimized functions
__all__ = [
    'performance_tracker',
    'lazy_import',
    'response_cache',
    'connection_pool',
    'batch_requests',
    'get_optimized_timeout',
    'preload_critical_modules',
    'PerformanceMonitor'
]