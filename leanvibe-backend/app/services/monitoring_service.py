"""
Production Monitoring Service
Provides comprehensive observability for LeanVibe production deployment
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4
from collections import defaultdict, deque

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class OperationLog(BaseModel):
    """Log entry for a monitored operation"""
    operation_id: str
    operation_type: str
    tenant_id: Optional[UUID] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: Optional[str] = None  # success, failure, timeout
    duration_ms: Optional[float] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    result_data: Dict[str, Any] = Field(default_factory=dict)
    error_context: Dict[str, Any] = Field(default_factory=dict)


class JourneyStep(BaseModel):
    """User journey step tracking"""
    journey_id: str
    step_name: str
    tenant_id: UUID
    status: str
    duration_ms: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    error_type: Optional[str] = None


class HealthCheck(BaseModel):
    """Health check result for a service"""
    service_name: str
    status: str  # healthy, degraded, unhealthy
    response_time_ms: float
    error_message: Optional[str] = None
    checked_at: datetime = Field(default_factory=datetime.utcnow)


class MonitoringService:
    """Production monitoring and observability service"""
    
    def __init__(self):
        # In-memory storage for monitoring data (in production, use proper observability stack)
        self._operation_logs: Dict[str, OperationLog] = {}
        self._journey_steps: deque = deque(maxlen=10000)  # Keep last 10k steps
        self._performance_data: Dict[str, List[float]] = defaultdict(list)
        self._health_checks: Dict[str, HealthCheck] = {}
        
        # Performance thresholds (configurable)
        self.slow_operation_threshold_ms = 2000  # 2 seconds
        self.error_rate_alert_threshold = 0.1    # 10%
        
        logger.info("Initialized Production Monitoring Service")
    
    async def start_operation(
        self,
        operation_type: str,
        tenant_id: Optional[UUID] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Start tracking a monitored operation"""
        try:
            operation_id = str(uuid4())
            
            operation_log = OperationLog(
                operation_id=operation_id,
                operation_type=operation_type,
                tenant_id=tenant_id,
                started_at=datetime.utcnow(),
                context=context or {}
            )
            
            self._operation_logs[operation_id] = operation_log
            
            # Structured logging for searchability
            logger.info(
                "Operation started",
                extra={
                    "operation_id": operation_id,
                    "operation_type": operation_type,
                    "tenant_id": str(tenant_id) if tenant_id else None,
                    "context": context
                }
            )
            
            return operation_id
            
        except Exception as e:
            logger.error(f"Failed to start operation tracking: {e}")
            return str(uuid4())  # Return dummy ID to not break calling code
    
    async def complete_operation(
        self,
        operation_id: str,
        status: str,
        duration_ms: float,
        result_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Complete operation tracking with success"""
        try:
            if operation_id in self._operation_logs:
                operation_log = self._operation_logs[operation_id]
                operation_log.status = status
                operation_log.duration_ms = duration_ms
                operation_log.completed_at = datetime.utcnow()
                operation_log.result_data = result_data or {}
                
                # Track performance data
                self._performance_data[operation_log.operation_type].append(duration_ms)
                
                # Structured logging
                logger.info(
                    "Operation completed",
                    extra={
                        "operation_id": operation_id,
                        "operation_type": operation_log.operation_type,
                        "status": status,
                        "duration_ms": duration_ms,
                        "tenant_id": str(operation_log.tenant_id) if operation_log.tenant_id else None,
                        "result_data": result_data
                    }
                )
                
                # Check for slow operations
                if duration_ms > self.slow_operation_threshold_ms:
                    logger.warning(
                        "Slow operation detected",
                        extra={
                            "operation_id": operation_id,
                            "operation_type": operation_log.operation_type,
                            "duration_ms": duration_ms,
                            "threshold_ms": self.slow_operation_threshold_ms
                        }
                    )
                    
        except Exception as e:
            logger.error(f"Failed to complete operation tracking: {e}")
    
    async def fail_operation(
        self,
        operation_id: str,
        error_type: str,
        error_message: str,
        duration_ms: float,
        error_context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Complete operation tracking with failure"""
        try:
            if operation_id in self._operation_logs:
                operation_log = self._operation_logs[operation_id]
                operation_log.status = "failure"
                operation_log.duration_ms = duration_ms
                operation_log.completed_at = datetime.utcnow()
                operation_log.error_type = error_type
                operation_log.error_message = error_message
                operation_log.error_context = error_context or {}
                
                # Track performance data (even for failures)
                self._performance_data[operation_log.operation_type].append(duration_ms)
                
                # Structured error logging
                logger.error(
                    "Operation failed",
                    extra={
                        "operation_id": operation_id,
                        "operation_type": operation_log.operation_type,
                        "error_type": error_type,
                        "error_message": error_message,
                        "duration_ms": duration_ms,
                        "tenant_id": str(operation_log.tenant_id) if operation_log.tenant_id else None,
                        "error_context": error_context
                    }
                )
                
        except Exception as e:
            logger.error(f"Failed to track operation failure: {e}")
    
    async def track_user_journey_step(
        self,
        journey_id: str,
        step_name: str,
        tenant_id: UUID,
        status: str,
        duration_ms: float,
        error_type: Optional[str] = None
    ) -> None:
        """Track a step in a user journey"""
        try:
            step = JourneyStep(
                journey_id=journey_id,
                step_name=step_name,
                tenant_id=tenant_id,
                status=status,
                duration_ms=duration_ms,
                error_type=error_type
            )
            
            self._journey_steps.append(step)
            
            # Structured logging for user journey tracking
            logger.info(
                "User journey step",
                extra={
                    "journey_id": journey_id,
                    "step_name": step_name,
                    "tenant_id": str(tenant_id),
                    "status": status,
                    "duration_ms": duration_ms,
                    "error_type": error_type
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to track journey step: {e}")
    
    async def get_journey_metrics(
        self,
        journey_id: str,
        hours: int = 24
    ) -> Dict[str, Any]:
        """Get error rate and performance metrics for a user journey"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            # Filter steps for this journey within time window
            journey_steps = [
                step for step in self._journey_steps
                if step.journey_id == journey_id and step.timestamp >= cutoff_time
            ]
            
            if not journey_steps:
                return {
                    "journey_id": journey_id,
                    "total_operations": 0,
                    "success_count": 0,
                    "failure_count": 0,
                    "error_rate": 0.0,
                    "average_duration_ms": 0.0
                }
            
            total_ops = len(journey_steps)
            success_count = len([s for s in journey_steps if s.status == "success"])
            failure_count = len([s for s in journey_steps if s.status == "failure"])
            error_rate = failure_count / total_ops if total_ops > 0 else 0.0
            
            avg_duration = sum(s.duration_ms for s in journey_steps) / total_ops
            
            metrics = {
                "journey_id": journey_id,
                "total_operations": total_ops,
                "success_count": success_count,
                "failure_count": failure_count,
                "error_rate": error_rate,
                "average_duration_ms": avg_duration,
                "time_window_hours": hours
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to calculate journey metrics: {e}")
            return {"error": str(e)}
    
    async def get_performance_metrics(
        self,
        operation_type: str,
        hours: int = 24
    ) -> Dict[str, Any]:
        """Get performance metrics for an operation type"""
        try:
            # Get performance data for this operation type
            durations = self._performance_data.get(operation_type, [])
            
            if not durations:
                return {
                    "operation_type": operation_type,
                    "sample_count": 0,
                    "average_duration_ms": 0.0,
                    "p95_duration_ms": 0.0,
                    "slow_operation_count": 0
                }
            
            # Calculate performance metrics
            avg_duration = sum(durations) / len(durations)
            durations_sorted = sorted(durations)
            p95_index = int(len(durations_sorted) * 0.95)
            p95_duration = durations_sorted[p95_index] if p95_index < len(durations_sorted) else durations_sorted[-1]
            
            slow_ops = len([d for d in durations if d > self.slow_operation_threshold_ms])
            
            return {
                "operation_type": operation_type,
                "sample_count": len(durations),
                "average_duration_ms": avg_duration,
                "p95_duration_ms": p95_duration,
                "slow_operation_count": slow_ops,
                "slow_operation_threshold_ms": self.slow_operation_threshold_ms
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate performance metrics: {e}")
            return {"error": str(e)}
    
    async def check_system_health(self) -> Dict[str, Any]:
        """Perform health checks on all core services"""
        try:
            services_to_check = [
                "mvp_service",
                "pipeline_orchestration_service", 
                "email_service",
                "assembly_line_system"
            ]
            
            health_results = {}
            overall_status = "healthy"
            
            for service_name in services_to_check:
                start_time = time.time()
                
                try:
                    # Simulate health check (in production, would check actual service health)
                    await asyncio.sleep(0.001)  # Simulate check latency
                    
                    response_time_ms = (time.time() - start_time) * 1000
                    
                    # Determine service status based on response time
                    if response_time_ms < 100:
                        status = "healthy"
                    elif response_time_ms < 500:
                        status = "degraded"
                        overall_status = "degraded"
                    else:
                        status = "unhealthy"
                        overall_status = "unhealthy"
                    
                    health_check = HealthCheck(
                        service_name=service_name,
                        status=status,
                        response_time_ms=response_time_ms
                    )
                    
                    health_results[service_name] = {
                        "status": status,
                        "response_time_ms": response_time_ms,
                        "checked_at": health_check.checked_at.isoformat()
                    }
                    
                    self._health_checks[service_name] = health_check
                    
                except Exception as service_error:
                    health_results[service_name] = {
                        "status": "unhealthy",
                        "response_time_ms": (time.time() - start_time) * 1000,
                        "error": str(service_error),
                        "checked_at": datetime.utcnow().isoformat()
                    }
                    overall_status = "unhealthy"
            
            return {
                "overall_status": overall_status,
                "timestamp": datetime.utcnow().isoformat(),
                "services": health_results
            }
            
        except Exception as e:
            logger.error(f"Failed to check system health: {e}")
            return {
                "overall_status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get current active alerts based on monitoring data"""
        try:
            alerts = []
            
            # Check for unhealthy services
            for service_name, health_check in self._health_checks.items():
                if health_check.status == "unhealthy":
                    alerts.append({
                        "type": "service_unhealthy",
                        "service": service_name,
                        "message": f"Service {service_name} is unhealthy",
                        "severity": "critical",
                        "timestamp": health_check.checked_at.isoformat()
                    })
            
            # Check for high error rates (simplified check)
            recent_failures = [
                step for step in list(self._journey_steps)[-100:]  # Last 100 steps
                if step.status == "failure"
            ]
            
            if len(recent_failures) > 10:  # More than 10% failure rate in recent operations
                alerts.append({
                    "type": "high_error_rate",
                    "message": f"High error rate detected: {len(recent_failures)} failures in recent operations",
                    "severity": "warning",
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to get active alerts: {e}")
            return []


# Global monitoring service instance
monitoring_service = MonitoringService()