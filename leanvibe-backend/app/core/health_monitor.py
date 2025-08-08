"""
Comprehensive Health Monitoring System

Provides advanced health checking capabilities with:
- Service dependency validation
- Performance metrics collection
- Real-time health status tracking
- Alert generation and recovery recommendations
- System resource monitoring
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import psutil
import socket

from .logging_config import get_logger
from .service_manager import service_manager


logger = get_logger(__name__)


class HealthStatus(str, Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded" 
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class ServiceType(str, Enum):
    """Service type categories"""
    CORE = "core"
    OPTIONAL = "optional"
    EXTERNAL = "external"


@dataclass
class HealthCheck:
    """Individual health check definition"""
    name: str
    check_func: Callable
    timeout: float = 5.0
    critical: bool = False
    service_type: ServiceType = ServiceType.OPTIONAL
    dependencies: List[str] = field(default_factory=list)
    enabled: bool = True


@dataclass  
class HealthMetrics:
    """Health metrics for a service or component"""
    status: HealthStatus
    response_time_ms: float
    last_check: datetime
    error_count: int = 0
    uptime_seconds: float = 0.0
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemMetrics:
    """System-level performance metrics"""
    cpu_percent: float
    memory_percent: float  
    memory_mb: float
    disk_percent: float
    network_connections: int
    process_count: int
    load_average: Optional[float] = None


class HealthMonitor:
    """
    Comprehensive health monitoring system
    
    Manages health checks for all services and system components,
    tracks metrics, generates alerts, and provides recovery recommendations.
    """
    
    def __init__(self):
        self.health_checks: Dict[str, HealthCheck] = {}
        self.health_metrics: Dict[str, HealthMetrics] = {}
        self.system_metrics: Optional[SystemMetrics] = None
        self.start_time = time.time()
        self.last_full_check: Optional[datetime] = None
        
        # Monitoring configuration
        self.check_interval = 30  # seconds
        self.alert_thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'disk_percent': 90.0,
            'error_rate_threshold': 0.1,  # 10%
            'response_time_threshold': 5000.0  # 5 seconds
        }
        
        self._initialize_default_checks()
    
    def _initialize_default_checks(self):
        """Initialize default health checks for core services"""
        
        # Core service health checks
        self.register_check(
            "vector_service",
            self._check_vector_service,
            timeout=3.0,
            critical=True,
            service_type=ServiceType.CORE
        )
        
        self.register_check(
            "ai_service", 
            self._check_ai_service,
            timeout=5.0,
            critical=True,
            service_type=ServiceType.CORE
        )
        
        self.register_check(
            "graph_service",
            self._check_graph_service,
            timeout=3.0,
            critical=False,
            service_type=ServiceType.OPTIONAL,
            dependencies=["vector_service"]
        )
        
        # System resource checks
        self.register_check(
            "system_resources",
            self._check_system_resources,
            timeout=2.0,
            critical=True,
            service_type=ServiceType.CORE
        )
        
        # Network connectivity checks
        self.register_check(
            "network_connectivity",
            self._check_network_connectivity,
            timeout=5.0,
            critical=False,
            service_type=ServiceType.EXTERNAL
        )
        
        # Database connectivity (if applicable)
        self.register_check(
            "database_connections",
            self._check_database_connections,
            timeout=3.0,
            critical=False,
            service_type=ServiceType.OPTIONAL
        )
    
    def register_check(
        self,
        name: str,
        check_func: Callable,
        timeout: float = 5.0,
        critical: bool = False,
        service_type: ServiceType = ServiceType.OPTIONAL,
        dependencies: Optional[List[str]] = None
    ):
        """Register a new health check"""
        self.health_checks[name] = HealthCheck(
            name=name,
            check_func=check_func,
            timeout=timeout,
            critical=critical,
            service_type=service_type,
            dependencies=dependencies or []
        )
        
        logger.debug("Health check registered", check_name=name, critical=critical)
    
    async def run_single_check(self, check_name: str) -> HealthMetrics:
        """Run a single health check"""
        if check_name not in self.health_checks:
            return HealthMetrics(
                status=HealthStatus.UNKNOWN,
                response_time_ms=0,
                last_check=datetime.now(),
                message=f"Check '{check_name}' not found"
            )
        
        check = self.health_checks[check_name]
        start_time = time.time()
        
        try:
            # Check dependencies first
            for dep in check.dependencies:
                dep_metrics = self.health_metrics.get(dep)
                if not dep_metrics or dep_metrics.status in [HealthStatus.UNHEALTHY, HealthStatus.CRITICAL]:
                    return HealthMetrics(
                        status=HealthStatus.DEGRADED,
                        response_time_ms=0,
                        last_check=datetime.now(),
                        message=f"Dependency '{dep}' is unhealthy"
                    )
            
            # Run the actual check with timeout
            result = await asyncio.wait_for(
                check.check_func(),
                timeout=check.timeout
            )
            
            response_time = (time.time() - start_time) * 1000
            
            if isinstance(result, dict):
                status = HealthStatus(result.get('status', HealthStatus.HEALTHY))
                message = result.get('message', 'Check completed successfully')
                details = result.get('details', {})
            else:
                status = HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY
                message = 'Check completed successfully' if result else 'Check failed'
                details = {}
            
            metrics = HealthMetrics(
                status=status,
                response_time_ms=response_time,
                last_check=datetime.now(),
                message=message,
                details=details
            )
            
            # Update error count
            if check_name in self.health_metrics:
                prev_metrics = self.health_metrics[check_name]
                if status in [HealthStatus.UNHEALTHY, HealthStatus.CRITICAL]:
                    metrics.error_count = prev_metrics.error_count + 1
                else:
                    metrics.error_count = max(0, prev_metrics.error_count - 1)
                    
                # Calculate uptime
                if prev_metrics.last_check:
                    time_diff = (metrics.last_check - prev_metrics.last_check).total_seconds()
                    if status == HealthStatus.HEALTHY:
                        metrics.uptime_seconds = prev_metrics.uptime_seconds + time_diff
                    else:
                        metrics.uptime_seconds = prev_metrics.uptime_seconds
            
            return metrics
            
        except asyncio.TimeoutError:
            response_time = check.timeout * 1000
            return HealthMetrics(
                status=HealthStatus.CRITICAL,
                response_time_ms=response_time,
                last_check=datetime.now(),
                error_count=self.health_metrics.get(check_name, HealthMetrics(HealthStatus.UNKNOWN, 0, datetime.now())).error_count + 1,
                message=f"Health check timed out after {check.timeout}s"
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error("Health check failed", check_name=check_name, error=str(e))
            
            return HealthMetrics(
                status=HealthStatus.CRITICAL,
                response_time_ms=response_time,
                last_check=datetime.now(),
                error_count=self.health_metrics.get(check_name, HealthMetrics(HealthStatus.UNKNOWN, 0, datetime.now())).error_count + 1,
                message=f"Health check error: {str(e)}"
            )
    
    async def run_all_checks(self) -> Dict[str, HealthMetrics]:
        """Run all registered health checks"""
        logger.info("Running comprehensive health checks")
        start_time = time.time()
        
        # Update system metrics first
        self.system_metrics = await self._collect_system_metrics()
        
        # Run all health checks concurrently
        check_tasks = []
        for check_name in self.health_checks.keys():
            if self.health_checks[check_name].enabled:
                task = asyncio.create_task(self.run_single_check(check_name))
                check_tasks.append((check_name, task))
        
        # Collect results
        for check_name, task in check_tasks:
            try:
                self.health_metrics[check_name] = await task
            except Exception as e:
                logger.error("Failed to complete health check", check_name=check_name, error=str(e))
                self.health_metrics[check_name] = HealthMetrics(
                    status=HealthStatus.CRITICAL,
                    response_time_ms=0,
                    last_check=datetime.now(),
                    message=f"Check execution failed: {str(e)}"
                )
        
        self.last_full_check = datetime.now()
        total_time = (time.time() - start_time) * 1000
        
        logger.info(
            "Health checks completed",
            total_checks=len(self.health_metrics),
            total_time_ms=round(total_time, 2),
            healthy_checks=len([m for m in self.health_metrics.values() if m.status == HealthStatus.HEALTHY])
        )
        
        return self.health_metrics
    
    def get_overall_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        if not self.health_metrics:
            return {
                'status': HealthStatus.UNKNOWN,
                'message': 'No health checks have been run',
                'last_check': None
            }
        
        # Analyze health status
        statuses = [metrics.status for metrics in self.health_metrics.values()]
        critical_checks = [name for name, check in self.health_checks.items() 
                          if check.critical and self.health_metrics.get(name, {}).status in [HealthStatus.UNHEALTHY, HealthStatus.CRITICAL]]
        
        # Determine overall status
        if any(status == HealthStatus.CRITICAL for status in statuses):
            overall_status = HealthStatus.CRITICAL
        elif critical_checks:
            overall_status = HealthStatus.UNHEALTHY
        elif any(status == HealthStatus.UNHEALTHY for status in statuses):
            overall_status = HealthStatus.DEGRADED
        elif any(status == HealthStatus.DEGRADED for status in statuses):
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY
        
        # Generate status message
        healthy_count = len([s for s in statuses if s == HealthStatus.HEALTHY])
        total_count = len(statuses)
        
        if overall_status == HealthStatus.HEALTHY:
            message = f"All {total_count} services are healthy"
        elif overall_status == HealthStatus.DEGRADED:
            message = f"{healthy_count}/{total_count} services healthy - degraded performance"
        elif overall_status == HealthStatus.UNHEALTHY:
            message = f"Critical services unavailable ({len(critical_checks)} critical failures)"
        else:
            message = f"System in critical state - immediate attention required"
        
        return {
            'status': overall_status,
            'message': message,
            'last_check': self.last_full_check,
            'uptime_seconds': time.time() - self.start_time,
            'healthy_services': healthy_count,
            'total_services': total_count,
            'critical_failures': critical_checks,
            'system_metrics': self.system_metrics
        }
    
    def get_service_health(self, service_name: str) -> Optional[HealthMetrics]:
        """Get health metrics for a specific service"""
        return self.health_metrics.get(service_name)
    
    def get_alerts(self) -> List[Dict[str, Any]]:
        """Get current alerts based on health status and thresholds"""
        alerts = []
        
        # Check service-level alerts
        for name, metrics in self.health_metrics.items():
            check = self.health_checks.get(name)
            if not check:
                continue
            
            # Critical service down
            if check.critical and metrics.status in [HealthStatus.UNHEALTHY, HealthStatus.CRITICAL]:
                alerts.append({
                    'type': 'service_critical',
                    'severity': 'critical',
                    'service': name,
                    'message': f"Critical service '{name}' is {metrics.status.value}",
                    'details': metrics.message,
                    'timestamp': metrics.last_check
                })
            
            # High response time
            if metrics.response_time_ms > self.alert_thresholds['response_time_threshold']:
                alerts.append({
                    'type': 'high_response_time',
                    'severity': 'warning',
                    'service': name,
                    'message': f"High response time for '{name}': {metrics.response_time_ms:.0f}ms",
                    'details': f"Threshold: {self.alert_thresholds['response_time_threshold']}ms",
                    'timestamp': metrics.last_check
                })
            
            # High error rate
            if metrics.error_count > 5:  # More than 5 consecutive errors
                alerts.append({
                    'type': 'high_error_rate',
                    'severity': 'error',
                    'service': name,
                    'message': f"High error rate for '{name}': {metrics.error_count} errors",
                    'details': metrics.message,
                    'timestamp': metrics.last_check
                })
        
        # Check system-level alerts
        if self.system_metrics:
            if self.system_metrics.cpu_percent > self.alert_thresholds['cpu_percent']:
                alerts.append({
                    'type': 'high_cpu_usage',
                    'severity': 'warning',
                    'service': 'system',
                    'message': f"High CPU usage: {self.system_metrics.cpu_percent:.1f}%",
                    'details': f"Threshold: {self.alert_thresholds['cpu_percent']}%",
                    'timestamp': datetime.now()
                })
            
            if self.system_metrics.memory_percent > self.alert_thresholds['memory_percent']:
                alerts.append({
                    'type': 'high_memory_usage',
                    'severity': 'warning',
                    'service': 'system',
                    'message': f"High memory usage: {self.system_metrics.memory_percent:.1f}%",
                    'details': f"Threshold: {self.alert_thresholds['memory_percent']}%",
                    'timestamp': datetime.now()
                })
            
            if self.system_metrics.disk_percent > self.alert_thresholds['disk_percent']:
                alerts.append({
                    'type': 'high_disk_usage',
                    'severity': 'error',
                    'service': 'system',
                    'message': f"High disk usage: {self.system_metrics.disk_percent:.1f}%",
                    'details': f"Threshold: {self.alert_thresholds['disk_percent']}%",
                    'timestamp': datetime.now()
                })
        
        return alerts
    
    async def _collect_system_metrics(self) -> SystemMetrics:
        """Collect system performance metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # Network connections
            try:
                connections = len(psutil.net_connections())
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                connections = 0
            
            # Process count
            process_count = len(psutil.pids())
            
            # Load average (Unix systems only)
            load_avg = None
            try:
                load_avg = psutil.getloadavg()[0]  # 1-minute load average
            except (AttributeError, OSError):
                pass  # Not available on Windows
            
            return SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_mb=memory.used / 1024 / 1024,
                disk_percent=disk.percent,
                network_connections=connections,
                process_count=process_count,
                load_average=load_avg
            )
            
        except Exception as e:
            logger.error("Failed to collect system metrics", error=str(e))
            return SystemMetrics(
                cpu_percent=0,
                memory_percent=0,
                memory_mb=0,
                disk_percent=0,
                network_connections=0,
                process_count=0
            )
    
    # Health check implementations
    async def _check_vector_service(self) -> Dict[str, Any]:
        """Check vector store service health"""
        try:
            vector_service = service_manager.get_service('vector')
            if not vector_service:
                return {
                    'status': HealthStatus.UNHEALTHY,
                    'message': 'Vector service not available'
                }
            
            # Check if service is responding
            if hasattr(vector_service, 'get_status'):
                status = vector_service.get_status()
                if status and status.get('initialized'):
                    return {
                        'status': HealthStatus.HEALTHY,
                        'message': 'Vector service is operational',
                        'details': status
                    }
            
            return {
                'status': HealthStatus.DEGRADED,
                'message': 'Vector service available but not fully initialized'
            }
            
        except Exception as e:
            return {
                'status': HealthStatus.CRITICAL,
                'message': f'Vector service check failed: {str(e)}'
            }
    
    async def _check_ai_service(self) -> Dict[str, Any]:
        """Check AI service health"""
        try:
            ai_service = service_manager.get_service('ai')
            if not ai_service:
                return {
                    'status': HealthStatus.UNHEALTHY,
                    'message': 'AI service not available'
                }
            
            # Check if service is responding
            if hasattr(ai_service, 'health_check'):
                health_result = await ai_service.health_check()
                if health_result.get('status') == 'healthy':
                    return {
                        'status': HealthStatus.HEALTHY,
                        'message': 'AI service is operational',
                        'details': health_result
                    }
                else:
                    return {
                        'status': HealthStatus.DEGRADED,
                        'message': 'AI service responding but degraded',
                        'details': health_result
                    }
            
            return {
                'status': HealthStatus.HEALTHY,
                'message': 'AI service is available'
            }
            
        except Exception as e:
            return {
                'status': HealthStatus.CRITICAL,
                'message': f'AI service check failed: {str(e)}'
            }
    
    async def _check_graph_service(self) -> Dict[str, Any]:
        """Check graph service health"""
        try:
            graph_service = service_manager.get_service('graph')
            if not graph_service:
                return {
                    'status': HealthStatus.UNHEALTHY,
                    'message': 'Graph service not available'
                }
            
            # Check if service is initialized
            if hasattr(graph_service, 'initialized') and graph_service.initialized:
                return {
                    'status': HealthStatus.HEALTHY,
                    'message': 'Graph service is operational'
                }
            else:
                return {
                    'status': HealthStatus.DEGRADED,
                    'message': 'Graph service available but not initialized'
                }
                
        except Exception as e:
            return {
                'status': HealthStatus.CRITICAL,
                'message': f'Graph service check failed: {str(e)}'
            }
    
    async def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resource availability"""
        try:
            metrics = await self._collect_system_metrics()
            
            # Determine status based on resource usage
            critical_threshold = 95.0
            warning_threshold = 80.0
            
            issues = []
            status = HealthStatus.HEALTHY
            
            if metrics.cpu_percent > critical_threshold:
                issues.append(f"CPU usage critical: {metrics.cpu_percent:.1f}%")
                status = HealthStatus.CRITICAL
            elif metrics.cpu_percent > warning_threshold:
                issues.append(f"CPU usage high: {metrics.cpu_percent:.1f}%")
                status = HealthStatus.DEGRADED
            
            if metrics.memory_percent > critical_threshold:
                issues.append(f"Memory usage critical: {metrics.memory_percent:.1f}%")
                status = HealthStatus.CRITICAL
            elif metrics.memory_percent > warning_threshold:
                issues.append(f"Memory usage high: {metrics.memory_percent:.1f}%")
                if status == HealthStatus.HEALTHY:
                    status = HealthStatus.DEGRADED
            
            if metrics.disk_percent > critical_threshold:
                issues.append(f"Disk usage critical: {metrics.disk_percent:.1f}%")
                status = HealthStatus.CRITICAL
            elif metrics.disk_percent > warning_threshold:
                issues.append(f"Disk usage high: {metrics.disk_percent:.1f}%")
                if status == HealthStatus.HEALTHY:
                    status = HealthStatus.DEGRADED
            
            message = "System resources are healthy"
            if issues:
                message = f"System resource issues: {'; '.join(issues)}"
            
            return {
                'status': status,
                'message': message,
                'details': {
                    'cpu_percent': metrics.cpu_percent,
                    'memory_percent': metrics.memory_percent,
                    'memory_mb': metrics.memory_mb,
                    'disk_percent': metrics.disk_percent,
                    'load_average': metrics.load_average
                }
            }
            
        except Exception as e:
            return {
                'status': HealthStatus.CRITICAL,
                'message': f'System resource check failed: {str(e)}'
            }
    
    async def _check_network_connectivity(self) -> Dict[str, Any]:
        """Check network connectivity"""
        try:
            # Test basic connectivity by creating a socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2.0)
            
            # Test connection to localhost (should always work if network stack is healthy)
            try:
                result = sock.connect_ex(('localhost', 80))
                # Connection refused is expected, we just want to test network stack
                if result in [0, 111]:  # 111 is connection refused
                    return {
                        'status': HealthStatus.HEALTHY,
                        'message': 'Network connectivity is healthy'
                    }
                else:
                    return {
                        'status': HealthStatus.DEGRADED,
                        'message': 'Network connectivity may be degraded'
                    }
            finally:
                sock.close()
                
        except Exception as e:
            return {
                'status': HealthStatus.UNHEALTHY,
                'message': f'Network connectivity check failed: {str(e)}'
            }
    
    async def _check_database_connections(self) -> Dict[str, Any]:
        """Check database connection health"""
        try:
            # Check graph service database connection
            graph_service = service_manager.get_service('graph')
            if graph_service and hasattr(graph_service, 'driver'):
                # Neo4j is available
                return {
                    'status': HealthStatus.HEALTHY,
                    'message': 'Database connections are healthy',
                    'details': {'neo4j': 'connected'}
                }
            
            return {
                'status': HealthStatus.DEGRADED,
                'message': 'Database connections not available - operating without graph storage'
            }
            
        except Exception as e:
            return {
                'status': HealthStatus.DEGRADED,
                'message': f'Database connection check failed: {str(e)}'
            }


# Global health monitor instance
health_monitor = HealthMonitor()


# Export functions
async def run_health_checks() -> Dict[str, Any]:
    """Run all health checks and return comprehensive status"""
    await health_monitor.run_all_checks()
    return health_monitor.get_overall_health()


def get_service_health(service_name: str) -> Optional[Dict[str, Any]]:
    """Get health status for a specific service"""
    metrics = health_monitor.get_service_health(service_name)
    if not metrics:
        return None
    
    return {
        'status': metrics.status,
        'response_time_ms': metrics.response_time_ms,
        'last_check': metrics.last_check.isoformat(),
        'error_count': metrics.error_count,
        'uptime_seconds': metrics.uptime_seconds,
        'message': metrics.message,
        'details': metrics.details
    }


def get_current_alerts() -> List[Dict[str, Any]]:
    """Get current system alerts"""
    return health_monitor.get_alerts()