"""
Observability-as-Tests System for LeanVibe

Implements error budgets, performance budgets, health dashboard, and alert management
following XP principles - pragmatic monitoring that prevents issues and guides decisions.

Key Components:
- ErrorBudgetTracker: Track error rates, freeze merges when exceeded
- PerformanceBudgets: Response time SLA monitoring (p95 < 500ms)
- HealthDashboard: Simple web UI showing system health
- AlertManager: Notifications for threshold breaches
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque
import statistics

from pydantic import BaseModel

from .synthetic_probes import ProbeStatus, ProbeResult, run_synthetic_probes
from ..core.logging_config import get_logger

logger = get_logger(__name__)


class BudgetStatus(Enum):
    """Budget consumption status"""
    HEALTHY = "healthy"        # < 50% of budget consumed
    WARNING = "warning"        # 50-80% of budget consumed  
    CRITICAL = "critical"      # 80-95% of budget consumed
    EXHAUSTED = "exhausted"    # > 95% of budget consumed


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class Alert(BaseModel):
    """System alert"""
    id: str
    level: AlertLevel
    title: str
    message: str
    timestamp: datetime
    component: str
    details: Dict[str, Any] = {}
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    actions: List[str] = []


@dataclass
class ErrorBudget:
    """Error budget configuration and tracking"""
    name: str
    error_rate_threshold: float  # e.g., 0.05 for 5% error rate
    time_window_hours: int = 24  # Budget evaluation window
    budget_period_hours: int = 168  # 1 week budget reset period
    
    # Tracking data
    errors: deque = field(default_factory=deque)
    total_requests: deque = field(default_factory=deque)
    budget_reset_time: datetime = field(default_factory=datetime.now)
    
    def add_data_point(self, error_count: int, total_count: int):
        """Add error/request counts with timestamp"""
        timestamp = datetime.now()
        self.errors.append((timestamp, error_count))
        self.total_requests.append((timestamp, total_count))
        
        # Clean old data outside time window
        cutoff = timestamp - timedelta(hours=self.time_window_hours)
        while self.errors and self.errors[0][0] < cutoff:
            self.errors.popleft()
        while self.total_requests and self.total_requests[0][0] < cutoff:
            self.total_requests.popleft()
    
    def get_current_error_rate(self) -> float:
        """Calculate current error rate in time window"""
        if not self.total_requests:
            return 0.0
        
        total_errors = sum(count for _, count in self.errors)
        total_reqs = sum(count for _, count in self.total_requests)
        
        if total_reqs == 0:
            return 0.0
            
        return total_errors / total_reqs
    
    def get_budget_consumption(self) -> float:
        """Get budget consumption percentage (0.0 to 1.0)"""
        current_rate = self.get_current_error_rate()
        return min(current_rate / self.error_rate_threshold, 1.0)
    
    def get_status(self) -> BudgetStatus:
        """Get current budget status"""
        consumption = self.get_budget_consumption()
        
        if consumption >= 0.95:
            return BudgetStatus.EXHAUSTED
        elif consumption >= 0.80:
            return BudgetStatus.CRITICAL
        elif consumption >= 0.50:
            return BudgetStatus.WARNING
        else:
            return BudgetStatus.HEALTHY
    
    def should_freeze_deployments(self) -> bool:
        """Should deployments be frozen due to error budget exhaustion?"""
        return self.get_status() == BudgetStatus.EXHAUSTED
    
    def get_remaining_budget_time(self) -> timedelta:
        """Get time until budget reset"""
        reset_time = self.budget_reset_time + timedelta(hours=self.budget_period_hours)
        return max(reset_time - datetime.now(), timedelta(0))


@dataclass 
class PerformanceBudget:
    """Performance budget configuration and tracking"""
    name: str
    target_p95_ms: float = 500.0  # p95 response time target
    target_p99_ms: float = 1000.0  # p99 response time target
    time_window_minutes: int = 5  # Evaluation window
    
    # Tracking data
    response_times: deque = field(default_factory=deque)
    
    def add_response_time(self, response_time_ms: float):
        """Add response time measurement"""
        timestamp = datetime.now()
        self.response_times.append((timestamp, response_time_ms))
        
        # Clean old data outside time window
        cutoff = timestamp - timedelta(minutes=self.time_window_minutes)
        while self.response_times and self.response_times[0][0] < cutoff:
            self.response_times.popleft()
    
    def get_percentiles(self) -> Dict[str, float]:
        """Calculate performance percentiles"""
        if not self.response_times:
            return {"p50": 0, "p95": 0, "p99": 0}
        
        times = [rt for _, rt in self.response_times]
        return {
            "p50": statistics.quantiles(times, n=100)[49],  # 50th percentile
            "p95": statistics.quantiles(times, n=100)[94],  # 95th percentile
            "p99": statistics.quantiles(times, n=100)[98]   # 99th percentile
        }
    
    def get_status(self) -> BudgetStatus:
        """Get performance budget status"""
        percentiles = self.get_percentiles()
        p95 = percentiles["p95"]
        
        if p95 > self.target_p95_ms * 2:  # > 200% of target
            return BudgetStatus.EXHAUSTED
        elif p95 > self.target_p95_ms * 1.5:  # > 150% of target
            return BudgetStatus.CRITICAL
        elif p95 > self.target_p95_ms:  # > target
            return BudgetStatus.WARNING
        else:
            return BudgetStatus.HEALTHY
    
    def get_budget_consumption(self) -> float:
        """Get performance budget consumption (0.0 to 1.0)"""
        percentiles = self.get_percentiles()
        p95 = percentiles["p95"]
        return min(p95 / self.target_p95_ms, 2.0) / 2.0  # Cap at 200% = 1.0


class ErrorBudgetTracker:
    """Tracks error rates and manages deployment freeze decisions"""
    
    def __init__(self):
        self.budgets: Dict[str, ErrorBudget] = {
            "api_endpoints": ErrorBudget("API Endpoints", 0.05),  # 5% error rate budget
            "websocket_connections": ErrorBudget("WebSocket", 0.10),  # 10% error rate budget
            "ai_processing": ErrorBudget("AI Processing", 0.15),  # 15% error rate budget (more tolerant)
            "system_health": ErrorBudget("System Health", 0.02)  # 2% error rate budget (critical)
        }
        
        self.deployment_frozen = False
        self.freeze_reason = ""
        
    def record_errors(self, component: str, error_count: int, total_count: int):
        """Record error counts for a component"""
        if component in self.budgets:
            self.budgets[component].add_data_point(error_count, total_count)
            self._evaluate_deployment_freeze()
    
    def _evaluate_deployment_freeze(self):
        """Evaluate if deployments should be frozen"""
        critical_components = ["api_endpoints", "system_health"]
        
        for component_name in critical_components:
            budget = self.budgets.get(component_name)
            if budget and budget.should_freeze_deployments():
                self.deployment_frozen = True
                self.freeze_reason = f"Error budget exhausted for {component_name}"
                logger.critical(f"Deployment freeze activated: {self.freeze_reason}")
                return
        
        # Check if multiple components are in critical state
        critical_count = sum(
            1 for budget in self.budgets.values() 
            if budget.get_status() == BudgetStatus.CRITICAL
        )
        
        if critical_count >= 2:
            self.deployment_frozen = True
            self.freeze_reason = f"Multiple components ({critical_count}) in critical state"
            logger.critical(f"Deployment freeze activated: {self.freeze_reason}")
        else:
            # Check if we can unfreeze
            if self.deployment_frozen:
                can_unfreeze = all(
                    budget.get_status() not in [BudgetStatus.EXHAUSTED, BudgetStatus.CRITICAL]
                    for component_name, budget in self.budgets.items()
                    if component_name in critical_components
                )
                
                if can_unfreeze:
                    self.deployment_frozen = False
                    self.freeze_reason = ""
                    logger.info("Deployment freeze lifted - error budgets recovered")
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get comprehensive status summary"""
        budget_statuses = {}
        
        for name, budget in self.budgets.items():
            budget_statuses[name] = {
                "status": budget.get_status().value,
                "error_rate": budget.get_current_error_rate(),
                "budget_consumption": budget.get_budget_consumption(),
                "threshold": budget.error_rate_threshold,
                "remaining_budget_hours": budget.get_remaining_budget_time().total_seconds() / 3600
            }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "deployment_frozen": self.deployment_frozen,
            "freeze_reason": self.freeze_reason,
            "budgets": budget_statuses,
            "overall_health": self._get_overall_health()
        }
    
    def _get_overall_health(self) -> str:
        """Get overall error budget health"""
        if self.deployment_frozen:
            return "critical"
        
        statuses = [budget.get_status() for budget in self.budgets.values()]
        
        if any(s == BudgetStatus.CRITICAL for s in statuses):
            return "warning"
        elif any(s == BudgetStatus.WARNING for s in statuses):
            return "degraded" 
        else:
            return "healthy"


class PerformanceBudgets:
    """Manages performance SLA budgets"""
    
    def __init__(self):
        self.budgets: Dict[str, PerformanceBudget] = {
            "api_response_time": PerformanceBudget("API Response Time", 500.0, 1000.0),
            "websocket_latency": PerformanceBudget("WebSocket Latency", 200.0, 500.0),
            "ai_processing_time": PerformanceBudget("AI Processing", 5000.0, 10000.0),
            "database_query_time": PerformanceBudget("Database Queries", 100.0, 500.0)
        }
    
    def record_response_time(self, component: str, response_time_ms: float):
        """Record response time for a component"""
        if component in self.budgets:
            self.budgets[component].add_response_time(response_time_ms)
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get performance budget status summary"""
        budget_statuses = {}
        
        for name, budget in self.budgets.items():
            percentiles = budget.get_percentiles()
            status = budget.get_status()
            
            budget_statuses[name] = {
                "status": status.value,
                "percentiles": percentiles,
                "target_p95": budget.target_p95_ms,
                "target_p99": budget.target_p99_ms,
                "budget_consumption": budget.get_budget_consumption(),
                "sample_count": len(budget.response_times)
            }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "budgets": budget_statuses,
            "overall_health": self._get_overall_health()
        }
    
    def _get_overall_health(self) -> str:
        """Get overall performance health"""
        statuses = [budget.get_status() for budget in self.budgets.values()]
        
        if any(s == BudgetStatus.EXHAUSTED for s in statuses):
            return "critical"
        elif any(s == BudgetStatus.CRITICAL for s in statuses):
            return "warning"
        elif any(s == BudgetStatus.WARNING for s in statuses):
            return "degraded"
        else:
            return "healthy"


class HealthDashboard:
    """Manages health dashboard data aggregation"""
    
    def __init__(self, error_tracker: ErrorBudgetTracker, perf_budgets: PerformanceBudgets):
        self.error_tracker = error_tracker
        self.perf_budgets = perf_budgets
        self.last_probe_results: Dict[str, ProbeResult] = {}
        self.system_status_history = deque(maxlen=100)
    
    async def refresh_data(self):
        """Refresh dashboard data from all sources"""
        try:
            # Run synthetic probes
            self.last_probe_results = await run_synthetic_probes()
            
            # Update system status history
            current_status = self.get_system_status()
            self.system_status_history.append({
                "timestamp": datetime.now(),
                "status": current_status["overall_status"],
                "healthy_probes": current_status["probe_summary"]["healthy_count"],
                "total_probes": current_status["probe_summary"]["total_count"]
            })
            
        except Exception as e:
            logger.error(f"Failed to refresh dashboard data: {e}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status for dashboard"""
        # Analyze probe results
        probe_summary = self._analyze_probe_results()
        
        # Get budget statuses
        error_budget_status = self.error_tracker.get_status_summary()
        perf_budget_status = self.perf_budgets.get_status_summary()
        
        # Determine overall status
        overall_status = self._determine_overall_status(
            probe_summary["overall_health"],
            error_budget_status["overall_health"],
            perf_budget_status["overall_health"]
        )
        
        # Recent deployments (placeholder - would integrate with deployment system)
        recent_deployments = self._get_recent_deployments()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_status": overall_status,
            "probe_summary": probe_summary,
            "error_budgets": error_budget_status,
            "performance_budgets": perf_budget_status,
            "recent_deployments": recent_deployments,
            "deployment_frozen": error_budget_status["deployment_frozen"],
            "freeze_reason": error_budget_status.get("freeze_reason", ""),
            "websocket_status": self._get_websocket_status()
        }
    
    def _analyze_probe_results(self) -> Dict[str, Any]:
        """Analyze synthetic probe results"""
        if not self.last_probe_results:
            return {
                "overall_health": "unknown",
                "healthy_count": 0,
                "total_count": 0,
                "probes": {}
            }
        
        probe_analysis = {}
        healthy_count = 0
        
        for probe_name, result in self.last_probe_results.items():
            is_healthy = result.status == ProbeStatus.HEALTHY
            if is_healthy:
                healthy_count += 1
            
            probe_analysis[probe_name] = {
                "status": result.status.value,
                "response_time_ms": result.response_time_ms,
                "message": result.message,
                "timestamp": result.timestamp.isoformat(),
                "healthy": is_healthy
            }
        
        total_count = len(self.last_probe_results)
        health_percentage = (healthy_count / total_count) * 100 if total_count > 0 else 0
        
        # Determine overall probe health
        if health_percentage >= 80:
            overall_health = "healthy"
        elif health_percentage >= 60:
            overall_health = "degraded"
        else:
            overall_health = "unhealthy"
        
        return {
            "overall_health": overall_health,
            "healthy_count": healthy_count,
            "total_count": total_count,
            "health_percentage": health_percentage,
            "probes": probe_analysis
        }
    
    def _determine_overall_status(self, probe_health: str, error_health: str, perf_health: str) -> str:
        """Determine overall system status from component health"""
        health_levels = ["healthy", "degraded", "warning", "critical", "unhealthy"]
        
        # Find worst health level among components
        worst_health = "healthy"
        for health in [probe_health, error_health, perf_health]:
            if health in health_levels:
                current_index = health_levels.index(health)
                worst_index = health_levels.index(worst_health)
                if current_index > worst_index:
                    worst_health = health
        
        return worst_health
    
    def _get_recent_deployments(self) -> List[Dict[str, Any]]:
        """Get recent deployment status (placeholder)"""
        # In real implementation, this would query deployment system
        return [
            {
                "id": "deploy_001",
                "version": "v0.2.1",
                "status": "success",
                "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
                "duration_seconds": 45
            },
            {
                "id": "deploy_002", 
                "version": "v0.2.0",
                "status": "success",
                "timestamp": (datetime.now() - timedelta(hours=6)).isoformat(),
                "duration_seconds": 38
            }
        ]
    
    def _get_websocket_status(self) -> Dict[str, Any]:
        """Get WebSocket connection status from probe results"""
        websocket_probe = self.last_probe_results.get("websocket")
        
        if not websocket_probe:
            return {
                "status": "unknown",
                "message": "No WebSocket probe data available"
            }
        
        return {
            "status": websocket_probe.status.value,
            "response_time_ms": websocket_probe.response_time_ms,
            "message": websocket_probe.message,
            "last_check": websocket_probe.timestamp.isoformat()
        }
    
    def get_dashboard_html_data(self) -> Dict[str, Any]:
        """Get data formatted for HTML dashboard"""
        system_status = self.get_system_status()
        
        # Add trend data
        if len(self.system_status_history) >= 2:
            recent_statuses = list(self.system_status_history)[-10:]
            healthy_trend = [s["healthy_probes"] / s["total_probes"] for s in recent_statuses]
            trend_direction = "stable"
            
            if len(healthy_trend) >= 3:
                recent_avg = sum(healthy_trend[-3:]) / 3
                older_avg = sum(healthy_trend[-6:-3]) / 3 if len(healthy_trend) >= 6 else recent_avg
                
                if recent_avg > older_avg + 0.1:
                    trend_direction = "improving"
                elif recent_avg < older_avg - 0.1:
                    trend_direction = "degrading"
            
            system_status["trend"] = {
                "direction": trend_direction,
                "health_history": [s["healthy_probes"] / s["total_probes"] for s in recent_statuses]
            }
        
        return system_status


class AlertManager:
    """Manages system alerts and notifications"""
    
    def __init__(self):
        self.alerts: Dict[str, Alert] = {}
        self.notification_handlers: List[Callable] = []
        self.alert_history = deque(maxlen=1000)
        
        # Alert thresholds
        self.thresholds = {
            "health_probe_failures": 3,  # 3+ failures in 5min window
            "performance_budget_exceeded": 5,  # p95 > 500ms for 5min
            "error_budget_critical": 0.8,  # 80% budget consumed
            "websocket_disconnections": 10  # 10+ disconnections per minute
        }
    
    def add_notification_handler(self, handler: Callable[[Alert], None]):
        """Add notification handler (email, Slack, etc.)"""
        self.notification_handlers.append(handler)
    
    async def check_alert_conditions(self, dashboard: HealthDashboard):
        """Check all alert conditions and create/resolve alerts"""
        try:
            system_status = dashboard.get_system_status()
            
            # Check probe health alerts
            await self._check_probe_alerts(system_status["probe_summary"])
            
            # Check error budget alerts  
            await self._check_error_budget_alerts(system_status["error_budgets"])
            
            # Check performance budget alerts
            await self._check_performance_alerts(system_status["performance_budgets"])
            
            # Check WebSocket alerts
            await self._check_websocket_alerts(system_status["websocket_status"])
            
        except Exception as e:
            logger.error(f"Failed to check alert conditions: {e}")
    
    async def _check_probe_alerts(self, probe_summary: Dict[str, Any]):
        """Check synthetic probe alert conditions"""
        alert_id = "probe_health_failure"
        
        if probe_summary["health_percentage"] < 60:  # Less than 60% probes healthy
            if alert_id not in self.alerts:
                alert = Alert(
                    id=alert_id,
                    level=AlertLevel.CRITICAL,
                    title="Multiple Probe Failures Detected",
                    message=f"Only {probe_summary['healthy_count']}/{probe_summary['total_count']} probes are healthy ({probe_summary['health_percentage']:.1f}%)",
                    timestamp=datetime.now(),
                    component="synthetic_probes",
                    details=probe_summary,
                    actions=[
                        "Check system health endpoints",
                        "Investigate network connectivity", 
                        "Review recent deployments",
                        "Validate service availability"
                    ]
                )
                await self._create_alert(alert)
        else:
            # Resolve alert if it exists
            if alert_id in self.alerts and not self.alerts[alert_id].resolved:
                await self._resolve_alert(alert_id)
    
    async def _check_error_budget_alerts(self, error_budgets: Dict[str, Any]):
        """Check error budget alert conditions"""
        for budget_name, budget_data in error_budgets.get("budgets", {}).items():
            alert_id = f"error_budget_{budget_name}"
            
            if budget_data["budget_consumption"] >= 0.8:  # 80% budget consumed
                level = AlertLevel.CRITICAL if budget_data["budget_consumption"] >= 0.95 else AlertLevel.WARNING
                
                if alert_id not in self.alerts:
                    alert = Alert(
                        id=alert_id,
                        level=level,
                        title=f"Error Budget Alert: {budget_name}",
                        message=f"Error budget {budget_data['budget_consumption']*100:.1f}% consumed (rate: {budget_data['error_rate']*100:.2f}%)",
                        timestamp=datetime.now(),
                        component=budget_name,
                        details=budget_data,
                        actions=[
                            "Investigate recent error patterns",
                            "Consider deployment freeze" if level == AlertLevel.CRITICAL else "Monitor error trends",
                            "Review error handling in affected components",
                            "Check for infrastructure issues"
                        ]
                    )
                    await self._create_alert(alert)
            else:
                if alert_id in self.alerts and not self.alerts[alert_id].resolved:
                    await self._resolve_alert(alert_id)
    
    async def _check_performance_alerts(self, perf_budgets: Dict[str, Any]):
        """Check performance budget alert conditions"""
        for budget_name, budget_data in perf_budgets.get("budgets", {}).items():
            alert_id = f"performance_budget_{budget_name}"
            
            percentiles = budget_data.get("percentiles", {})
            p95 = percentiles.get("p95", 0)
            target = budget_data.get("target_p95", 500)
            
            if p95 > target * 1.5:  # 150% of target exceeded
                level = AlertLevel.CRITICAL if p95 > target * 2 else AlertLevel.WARNING
                
                if alert_id not in self.alerts:
                    alert = Alert(
                        id=alert_id,
                        level=level,
                        title=f"Performance Budget Exceeded: {budget_name}",
                        message=f"P95 response time {p95:.1f}ms exceeds target {target}ms",
                        timestamp=datetime.now(),
                        component=budget_name,
                        details=budget_data,
                        actions=[
                            "Investigate slow endpoints or queries",
                            "Check system resource utilization",
                            "Review recent code changes",
                            "Consider performance optimizations"
                        ]
                    )
                    await self._create_alert(alert)
            else:
                if alert_id in self.alerts and not self.alerts[alert_id].resolved:
                    await self._resolve_alert(alert_id)
    
    async def _check_websocket_alerts(self, websocket_status: Dict[str, Any]):
        """Check WebSocket alert conditions"""
        alert_id = "websocket_connectivity"
        
        if websocket_status["status"] in ["error", "timeout", "unhealthy"]:
            if alert_id not in self.alerts:
                alert = Alert(
                    id=alert_id,
                    level=AlertLevel.WARNING,
                    title="WebSocket Connectivity Issues",
                    message=f"WebSocket probe failed: {websocket_status['message']}",
                    timestamp=datetime.now(),
                    component="websocket",
                    details=websocket_status,
                    actions=[
                        "Check WebSocket server status",
                        "Investigate network connectivity",
                        "Review WebSocket connection logs",
                        "Validate WebSocket endpoint configuration"
                    ]
                )
                await self._create_alert(alert)
        else:
            if alert_id in self.alerts and not self.alerts[alert_id].resolved:
                await self._resolve_alert(alert_id)
    
    async def _create_alert(self, alert: Alert):
        """Create new alert and send notifications"""
        self.alerts[alert.id] = alert
        self.alert_history.append(alert)
        
        logger.warning(f"Alert created: {alert.title} - {alert.message}")
        
        # Send notifications
        for handler in self.notification_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Failed to send alert notification: {e}")
    
    async def _resolve_alert(self, alert_id: str):
        """Resolve existing alert"""
        if alert_id in self.alerts:
            alert = self.alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.now()
            
            logger.info(f"Alert resolved: {alert.title}")
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active (unresolved) alerts"""
        return [alert for alert in self.alerts.values() if not alert.resolved]
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get alert summary for monitoring"""
        active_alerts = self.get_active_alerts()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "active_alerts_count": len(active_alerts),
            "critical_alerts": len([a for a in active_alerts if a.level == AlertLevel.CRITICAL]),
            "warning_alerts": len([a for a in active_alerts if a.level == AlertLevel.WARNING]),
            "total_alerts_24h": len([a for a in self.alert_history if a.timestamp >= datetime.now() - timedelta(hours=24)]),
            "recent_alerts": [
                {
                    "id": alert.id,
                    "level": alert.level.value,
                    "title": alert.title,
                    "component": alert.component,
                    "timestamp": alert.timestamp.isoformat(),
                    "resolved": alert.resolved
                }
                for alert in list(self.alert_history)[-20:]  # Last 20 alerts
            ]
        }


# Global observability components
error_budget_tracker = ErrorBudgetTracker()
performance_budgets = PerformanceBudgets()
health_dashboard = HealthDashboard(error_budget_tracker, performance_budgets)
alert_manager = AlertManager()


# Convenience functions
async def get_system_health_summary() -> Dict[str, Any]:
    """Get comprehensive system health summary"""
    await health_dashboard.refresh_data()
    return health_dashboard.get_system_status()


async def run_alert_check():
    """Run alert condition checks"""
    await alert_manager.check_alert_conditions(health_dashboard)


def get_error_budget_status() -> Dict[str, Any]:
    """Get error budget status"""
    return error_budget_tracker.get_status_summary()


def get_performance_budget_status() -> Dict[str, Any]:
    """Get performance budget status"""
    return performance_budgets.get_status_summary()


# Example notification handler
def console_notification_handler(alert: Alert):
    """Simple console notification handler for development"""
    print(f"🚨 ALERT [{alert.level.value.upper()}] {alert.title}")
    print(f"   Component: {alert.component}")
    print(f"   Message: {alert.message}")
    print(f"   Actions: {', '.join(alert.actions)}")
    print(f"   Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")


# Register default notification handler
alert_manager.add_notification_handler(console_notification_handler)