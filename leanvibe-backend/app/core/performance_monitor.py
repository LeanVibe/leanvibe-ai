"""
Performance Monitoring System

Provides comprehensive performance monitoring with:
- Request timing and throughput metrics
- Memory usage tracking
- Database query performance
- WebSocket connection metrics
- API endpoint performance analysis
- Resource utilization monitoring
"""

import asyncio
import time
import tracemalloc
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from contextlib import asynccontextmanager
import psutil
import threading
from statistics import mean, median

from .logging_config import get_logger


logger = get_logger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for an operation"""
    operation: str
    start_time: float
    end_time: float
    duration_ms: float
    memory_used_mb: float
    cpu_percent: float
    success: bool
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EndpointStats:
    """Statistics for an API endpoint"""
    endpoint: str
    method: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0
    min_response_time: float = float('inf')
    max_response_time: float = 0.0
    median_response_time: float = 0.0
    p95_response_time: float = 0.0
    p99_response_time: float = 0.0
    requests_per_minute: float = 0.0
    last_request: Optional[datetime] = None
    response_times: deque = field(default_factory=lambda: deque(maxlen=1000))


@dataclass
class SystemResourceMetrics:
    """System resource utilization metrics"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_bytes_sent: int
    network_bytes_received: int
    active_connections: int
    thread_count: int
    process_count: int


class PerformanceMonitor:
    """
    Comprehensive performance monitoring system
    
    Tracks performance metrics across all application components,
    provides real-time performance analysis, and identifies bottlenecks.
    """
    
    def __init__(self, max_metrics_history: int = 10000):
        self.max_metrics_history = max_metrics_history
        self.metrics_history: deque = deque(maxlen=max_metrics_history)
        self.endpoint_stats: Dict[str, EndpointStats] = {}
        self.resource_metrics: deque = deque(maxlen=1000)  # Last 1000 resource snapshots
        self.active_operations: Dict[str, Dict[str, Any]] = {}
        
        # Performance thresholds
        self.thresholds = {
            'response_time_warning': 1000,  # 1 second
            'response_time_critical': 5000,  # 5 seconds
            'memory_warning': 500,  # 500MB
            'memory_critical': 1000,  # 1GB
            'cpu_warning': 70,  # 70%
            'cpu_critical': 90,  # 90%
            'error_rate_warning': 0.05,  # 5%
            'error_rate_critical': 0.15  # 15%
        }
        
        # Background monitoring
        self._monitoring_active = False
        self._monitoring_task = None
        self._resource_collection_interval = 30  # seconds
        
        # Memory tracking
        self._memory_tracking_enabled = False
        
        # Lock for thread safety
        self._lock = threading.RLock()
    
    def start_monitoring(self):
        """Start background performance monitoring"""
        if self._monitoring_active:
            logger.warning("Performance monitoring already active")
            return
        
        self._monitoring_active = True
        self._monitoring_task = asyncio.create_task(self._background_monitoring())
        
        # Start memory tracking if available
        try:
            tracemalloc.start()
            self._memory_tracking_enabled = True
            logger.info("Memory tracking enabled")
        except Exception as e:
            logger.warning("Could not start memory tracking", error=str(e))
        
        logger.info("Performance monitoring started")
    
    async def stop_monitoring(self):
        """Stop background performance monitoring"""
        if not self._monitoring_active:
            return
        
        self._monitoring_active = False
        
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        if self._memory_tracking_enabled:
            tracemalloc.stop()
        
        logger.info("Performance monitoring stopped")
    
    async def _background_monitoring(self):
        """Background task for collecting system resource metrics"""
        try:
            while self._monitoring_active:
                await self._collect_system_resources()
                await asyncio.sleep(self._resource_collection_interval)
        except asyncio.CancelledError:
            logger.info("Background monitoring cancelled")
        except Exception as e:
            logger.error("Background monitoring error", error=str(e))
    
    async def _collect_system_resources(self):
        """Collect current system resource metrics"""
        try:
            # CPU and memory
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            # Disk I/O
            disk_io = psutil.disk_io_counters()
            disk_read_mb = disk_io.read_bytes / 1024 / 1024 if disk_io else 0
            disk_write_mb = disk_io.write_bytes / 1024 / 1024 if disk_io else 0
            
            # Network I/O
            network_io = psutil.net_io_counters()
            network_sent = network_io.bytes_sent if network_io else 0
            network_received = network_io.bytes_recv if network_io else 0
            
            # Connections and processes
            try:
                active_connections = len(psutil.net_connections())
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                active_connections = 0
            
            thread_count = threading.active_count()
            process_count = len(psutil.pids())
            
            metrics = SystemResourceMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory.used / 1024 / 1024,
                memory_available_mb=memory.available / 1024 / 1024,
                disk_io_read_mb=disk_read_mb,
                disk_io_write_mb=disk_write_mb,
                network_bytes_sent=network_sent,
                network_bytes_received=network_received,
                active_connections=active_connections,
                thread_count=thread_count,
                process_count=process_count
            )
            
            with self._lock:
                self.resource_metrics.append(metrics)
                
        except Exception as e:
            logger.error("Failed to collect system resources", error=str(e))
    
    @asynccontextmanager
    async def track_operation(self, operation_name: str, **metadata):
        """Context manager to track operation performance"""
        operation_id = f"{operation_name}_{int(time.time() * 1000000)}"
        start_time = time.time()
        start_memory = self._get_current_memory_usage()
        start_cpu = psutil.cpu_percent()
        
        # Record operation start
        with self._lock:
            self.active_operations[operation_id] = {
                'operation': operation_name,
                'start_time': start_time,
                'start_memory': start_memory,
                'metadata': metadata
            }
        
        try:
            logger.debug("Operation started", operation=operation_name, operation_id=operation_id)
            yield operation_id
            
            # Record successful completion
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            end_memory = self._get_current_memory_usage()
            memory_used = max(0, end_memory - start_memory)
            
            metrics = PerformanceMetrics(
                operation=operation_name,
                start_time=start_time,
                end_time=end_time,
                duration_ms=duration_ms,
                memory_used_mb=memory_used,
                cpu_percent=psutil.cpu_percent() - start_cpu,
                success=True,
                metadata=metadata
            )
            
            self._record_metrics(metrics)
            logger.info(
                "Operation completed",
                operation=operation_name,
                duration_ms=round(duration_ms, 2),
                memory_used_mb=round(memory_used, 2)
            )
            
        except Exception as e:
            # Record failed completion
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            end_memory = self._get_current_memory_usage()
            memory_used = max(0, end_memory - start_memory)
            
            metrics = PerformanceMetrics(
                operation=operation_name,
                start_time=start_time,
                end_time=end_time,
                duration_ms=duration_ms,
                memory_used_mb=memory_used,
                cpu_percent=psutil.cpu_percent() - start_cpu,
                success=False,
                error=str(e),
                metadata=metadata
            )
            
            self._record_metrics(metrics)
            logger.error(
                "Operation failed",
                operation=operation_name,
                duration_ms=round(duration_ms, 2),
                error=str(e)
            )
            raise
        finally:
            # Clean up active operation
            with self._lock:
                self.active_operations.pop(operation_id, None)
    
    def track_endpoint_performance(
        self,
        endpoint: str,
        method: str,
        response_time_ms: float,
        success: bool,
        **metadata
    ):
        """Track performance metrics for an API endpoint"""
        with self._lock:
            stats_key = f"{method}:{endpoint}"
            
            if stats_key not in self.endpoint_stats:
                self.endpoint_stats[stats_key] = EndpointStats(
                    endpoint=endpoint,
                    method=method
                )
            
            stats = self.endpoint_stats[stats_key]
            stats.total_requests += 1
            stats.last_request = datetime.now()
            stats.response_times.append(response_time_ms)
            
            if success:
                stats.successful_requests += 1
            else:
                stats.failed_requests += 1
            
            # Update response time statistics
            response_times_list = list(stats.response_times)
            if response_times_list:
                stats.avg_response_time = mean(response_times_list)
                stats.median_response_time = median(response_times_list)
                stats.min_response_time = min(response_times_list)
                stats.max_response_time = max(response_times_list)
                
                # Calculate percentiles
                sorted_times = sorted(response_times_list)
                stats.p95_response_time = self._percentile(sorted_times, 95)
                stats.p99_response_time = self._percentile(sorted_times, 99)
            
            # Calculate requests per minute (based on last 100 requests)
            recent_requests = list(stats.response_times)[-100:]
            if len(recent_requests) > 1:
                time_span_minutes = len(recent_requests) / 60.0  # Approximate
                stats.requests_per_minute = len(recent_requests) / time_span_minutes
    
    def _record_metrics(self, metrics: PerformanceMetrics):
        """Record performance metrics"""
        with self._lock:
            self.metrics_history.append(metrics)
        
        # Check for performance alerts
        self._check_performance_alerts(metrics)
    
    def _check_performance_alerts(self, metrics: PerformanceMetrics):
        """Check if performance metrics trigger any alerts"""
        alerts = []
        
        # Response time alerts
        if metrics.duration_ms > self.thresholds['response_time_critical']:
            alerts.append({
                'type': 'response_time_critical',
                'message': f"Critical response time: {metrics.duration_ms:.0f}ms",
                'operation': metrics.operation,
                'severity': 'critical'
            })
        elif metrics.duration_ms > self.thresholds['response_time_warning']:
            alerts.append({
                'type': 'response_time_warning',
                'message': f"Slow response time: {metrics.duration_ms:.0f}ms",
                'operation': metrics.operation,
                'severity': 'warning'
            })
        
        # Memory alerts
        if metrics.memory_used_mb > self.thresholds['memory_critical']:
            alerts.append({
                'type': 'memory_critical',
                'message': f"Critical memory usage: {metrics.memory_used_mb:.1f}MB",
                'operation': metrics.operation,
                'severity': 'critical'
            })
        elif metrics.memory_used_mb > self.thresholds['memory_warning']:
            alerts.append({
                'type': 'memory_warning',
                'message': f"High memory usage: {metrics.memory_used_mb:.1f}MB",
                'operation': metrics.operation,
                'severity': 'warning'
            })
        
        # Log alerts
        for alert in alerts:
            if alert['severity'] == 'critical':
                logger.error("Performance alert", **alert)
            else:
                logger.warning("Performance alert", **alert)
    
    def _get_current_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            if self._memory_tracking_enabled:
                current, peak = tracemalloc.get_traced_memory()
                return current / 1024 / 1024
            else:
                # Fallback to process memory
                process = psutil.Process()
                return process.memory_info().rss / 1024 / 1024
        except Exception:
            return 0.0
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of data"""
        if not data:
            return 0.0
        
        k = (len(data) - 1) * percentile / 100
        f = int(k)
        c = k - f
        
        if f >= len(data) - 1:
            return data[-1]
        return data[f] + c * (data[f + 1] - data[f])
    
    def get_operation_stats(self, operation_name: Optional[str] = None) -> Dict[str, Any]:
        """Get performance statistics for operations"""
        with self._lock:
            metrics = list(self.metrics_history)
        
        if operation_name:
            metrics = [m for m in metrics if m.operation == operation_name]
        
        if not metrics:
            return {
                'operation': operation_name or 'all',
                'total_operations': 0,
                'message': 'No metrics available'
            }
        
        # Calculate statistics
        successful_ops = [m for m in metrics if m.success]
        failed_ops = [m for m in metrics if not m.success]
        
        durations = [m.duration_ms for m in metrics]
        memory_usage = [m.memory_used_mb for m in metrics]
        
        # Time-based analysis (last hour)
        one_hour_ago = time.time() - 3600
        recent_metrics = [m for m in metrics if m.end_time > one_hour_ago]
        
        return {
            'operation': operation_name or 'all',
            'total_operations': len(metrics),
            'successful_operations': len(successful_ops),
            'failed_operations': len(failed_ops),
            'success_rate': len(successful_ops) / len(metrics) if metrics else 0,
            'response_times': {
                'avg_ms': mean(durations) if durations else 0,
                'median_ms': median(durations) if durations else 0,
                'min_ms': min(durations) if durations else 0,
                'max_ms': max(durations) if durations else 0,
                'p95_ms': self._percentile(sorted(durations), 95) if durations else 0,
                'p99_ms': self._percentile(sorted(durations), 99) if durations else 0
            },
            'memory_usage': {
                'avg_mb': mean(memory_usage) if memory_usage else 0,
                'median_mb': median(memory_usage) if memory_usage else 0,
                'max_mb': max(memory_usage) if memory_usage else 0,
                'total_mb': sum(memory_usage) if memory_usage else 0
            },
            'recent_activity': {
                'operations_last_hour': len(recent_metrics),
                'operations_per_minute': len(recent_metrics) / 60 if recent_metrics else 0,
                'avg_response_time_last_hour': mean([m.duration_ms for m in recent_metrics]) if recent_metrics else 0
            }
        }
    
    def get_endpoint_stats(self, endpoint: Optional[str] = None) -> Dict[str, Any]:
        """Get performance statistics for API endpoints"""
        with self._lock:
            stats = dict(self.endpoint_stats)
        
        if endpoint:
            # Filter by endpoint
            stats = {k: v for k, v in stats.items() if endpoint in k}
        
        if not stats:
            return {
                'endpoints': {},
                'summary': {
                    'total_endpoints': 0,
                    'total_requests': 0,
                    'message': 'No endpoint statistics available'
                }
            }
        
        # Calculate summary statistics
        total_requests = sum(s.total_requests for s in stats.values())
        total_successful = sum(s.successful_requests for s in stats.values())
        total_failed = sum(s.failed_requests for s in stats.values())
        
        avg_response_times = [s.avg_response_time for s in stats.values() if s.avg_response_time > 0]
        overall_avg_response = mean(avg_response_times) if avg_response_times else 0
        
        # Convert stats to serializable format
        endpoint_data = {}
        for key, stat in stats.items():
            endpoint_data[key] = {
                'endpoint': stat.endpoint,
                'method': stat.method,
                'total_requests': stat.total_requests,
                'successful_requests': stat.successful_requests,
                'failed_requests': stat.failed_requests,
                'success_rate': stat.successful_requests / stat.total_requests if stat.total_requests > 0 else 0,
                'avg_response_time': round(stat.avg_response_time, 2),
                'min_response_time': round(stat.min_response_time, 2) if stat.min_response_time != float('inf') else 0,
                'max_response_time': round(stat.max_response_time, 2),
                'median_response_time': round(stat.median_response_time, 2),
                'p95_response_time': round(stat.p95_response_time, 2),
                'p99_response_time': round(stat.p99_response_time, 2),
                'requests_per_minute': round(stat.requests_per_minute, 2),
                'last_request': stat.last_request.isoformat() if stat.last_request else None
            }
        
        return {
            'endpoints': endpoint_data,
            'summary': {
                'total_endpoints': len(stats),
                'total_requests': total_requests,
                'successful_requests': total_successful,
                'failed_requests': total_failed,
                'overall_success_rate': total_successful / total_requests if total_requests > 0 else 0,
                'overall_avg_response_time': round(overall_avg_response, 2)
            }
        }
    
    def get_system_resource_stats(self, duration_minutes: int = 60) -> Dict[str, Any]:
        """Get system resource statistics for the specified duration"""
        with self._lock:
            metrics = list(self.resource_metrics)
        
        if not metrics:
            return {
                'message': 'No system resource metrics available',
                'duration_minutes': duration_minutes
            }
        
        # Filter by time
        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
        recent_metrics = [m for m in metrics if m.timestamp > cutoff_time]
        
        if not recent_metrics:
            recent_metrics = metrics[-100:]  # Use last 100 if no recent data
        
        # Calculate statistics
        cpu_values = [m.cpu_percent for m in recent_metrics]
        memory_values = [m.memory_percent for m in recent_metrics]
        memory_used_values = [m.memory_used_mb for m in recent_metrics]
        connection_values = [m.active_connections for m in recent_metrics]
        thread_values = [m.thread_count for m in recent_metrics]
        
        return {
            'duration_minutes': duration_minutes,
            'sample_count': len(recent_metrics),
            'cpu': {
                'avg_percent': round(mean(cpu_values), 2) if cpu_values else 0,
                'max_percent': round(max(cpu_values), 2) if cpu_values else 0,
                'min_percent': round(min(cpu_values), 2) if cpu_values else 0
            },
            'memory': {
                'avg_percent': round(mean(memory_values), 2) if memory_values else 0,
                'max_percent': round(max(memory_values), 2) if memory_values else 0,
                'avg_used_mb': round(mean(memory_used_values), 2) if memory_used_values else 0,
                'max_used_mb': round(max(memory_used_values), 2) if memory_used_values else 0
            },
            'network': {
                'avg_connections': round(mean(connection_values), 2) if connection_values else 0,
                'max_connections': max(connection_values) if connection_values else 0
            },
            'threads': {
                'avg_count': round(mean(thread_values), 2) if thread_values else 0,
                'max_count': max(thread_values) if thread_values else 0
            },
            'latest_sample': {
                'timestamp': recent_metrics[-1].timestamp.isoformat(),
                'cpu_percent': recent_metrics[-1].cpu_percent,
                'memory_percent': recent_metrics[-1].memory_percent,
                'memory_used_mb': round(recent_metrics[-1].memory_used_mb, 2),
                'active_connections': recent_metrics[-1].active_connections,
                'thread_count': recent_metrics[-1].thread_count
            } if recent_metrics else None
        }
    
    def get_active_operations(self) -> Dict[str, Any]:
        """Get currently active operations"""
        with self._lock:
            active_ops = dict(self.active_operations)
        
        current_time = time.time()
        
        operations_data = {}
        for op_id, op_data in active_ops.items():
            duration_seconds = current_time - op_data['start_time']
            operations_data[op_id] = {
                'operation': op_data['operation'],
                'duration_seconds': round(duration_seconds, 2),
                'start_time': datetime.fromtimestamp(op_data['start_time']).isoformat(),
                'metadata': op_data['metadata']
            }
        
        return {
            'active_operations_count': len(operations_data),
            'operations': operations_data
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        return {
            'monitoring_active': self._monitoring_active,
            'memory_tracking_enabled': self._memory_tracking_enabled,
            'metrics_collected': len(self.metrics_history),
            'endpoints_tracked': len(self.endpoint_stats),
            'resource_samples': len(self.resource_metrics),
            'active_operations': len(self.active_operations),
            'thresholds': self.thresholds,
            'last_collection': self.resource_metrics[-1].timestamp.isoformat() if self.resource_metrics else None
        }


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


# Convenience functions
async def start_performance_monitoring():
    """Start performance monitoring"""
    performance_monitor.start_monitoring()


async def stop_performance_monitoring():
    """Stop performance monitoring"""
    await performance_monitor.stop_monitoring()


def track_operation(operation_name: str, **metadata):
    """Context manager to track operation performance"""
    return performance_monitor.track_operation(operation_name, **metadata)


def track_endpoint(endpoint: str, method: str, response_time_ms: float, success: bool, **metadata):
    """Track endpoint performance"""
    performance_monitor.track_endpoint_performance(endpoint, method, response_time_ms, success, **metadata)


def get_performance_stats() -> Dict[str, Any]:
    """Get comprehensive performance statistics"""
    return {
        'summary': performance_monitor.get_performance_summary(),
        'operations': performance_monitor.get_operation_stats(),
        'endpoints': performance_monitor.get_endpoint_stats(),
        'system_resources': performance_monitor.get_system_resource_stats(),
        'active_operations': performance_monitor.get_active_operations()
    }