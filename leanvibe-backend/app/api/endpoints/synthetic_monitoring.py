"""
Synthetic Monitoring API Endpoints

Provides observability-as-tests endpoints for LeanVibe backend monitoring.
Integrates with synthetic probes and observability system following XP principles.
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import HTMLResponse

from ...core.logging_config import get_logger
from ...monitoring.synthetic_probes import run_synthetic_probes, get_probe_summary
from ...monitoring.observability import (
    get_system_health_summary,
    run_alert_check,
    get_error_budget_status,
    get_performance_budget_status,
    health_dashboard,
    alert_manager,
    error_budget_tracker,
    performance_budgets
)

logger = get_logger(__name__)
router = APIRouter(prefix="/monitoring", tags=["synthetic-monitoring"])

# Dashboard HTML path
DASHBOARD_HTML_PATH = Path(__file__).parent.parent.parent.parent / "monitoring" / "dashboard.html"


@router.get("/health")
async def get_monitoring_health() -> Dict[str, Any]:
    """
    Get comprehensive system health from synthetic probes and observability system
    
    This endpoint provides a unified view of system health including:
    - Synthetic probe results (response times, availability)
    - Error budget status (deployment freeze decisions)
    - Performance budget status (SLA compliance)
    - Active alerts and recommendations
    """
    try:
        logger.info("Fetching comprehensive monitoring health status")
        
        # Get system health summary (includes probe results)
        system_health = await get_system_health_summary()
        
        # Run alert checks
        await run_alert_check()
        
        # Get alert summary
        alert_summary = alert_manager.get_alert_summary()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "status": "success",
            "monitoring_type": "synthetic_probes_observability",
            "system_health": system_health,
            "alerts": alert_summary,
            "recommendations": _generate_health_recommendations(system_health, alert_summary)
        }
        
    except Exception as e:
        logger.error(f"Failed to get monitoring health: {e}")
        raise HTTPException(status_code=500, detail=f"Monitoring health check failed: {str(e)}")


@router.get("/metrics")
async def get_monitoring_metrics() -> Dict[str, Any]:
    """
    Get monitoring metrics in Prometheus-style format
    
    Returns key metrics for external monitoring systems:
    - Probe success rates and response times
    - Error budget consumption percentages
    - Performance budget utilization
    - Alert counts by severity
    """
    try:
        logger.info("Fetching monitoring metrics")
        
        # Get probe summary
        probe_summary = get_probe_summary()
        
        # Get budget statuses
        error_budget_status = get_error_budget_status()
        perf_budget_status = get_performance_budget_status()
        
        # Get alert metrics
        alert_summary = alert_manager.get_alert_summary()
        
        # Format as Prometheus-style metrics
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                # Probe metrics
                "leanvibe_probes_total": len(probe_summary.get("probes", {})),
                "leanvibe_probes_healthy_total": sum(
                    1 for probe in probe_summary.get("probes", {}).values()
                    if probe.get("status") == "healthy"
                ),
                "leanvibe_probe_success_rate": probe_summary.get("system_trends", {}).get("avg_health_percentage", 0) / 100,
                
                # Error budget metrics
                "leanvibe_error_budget_consumption_ratio": {
                    budget_name: budget_data["budget_consumption"]
                    for budget_name, budget_data in error_budget_status.get("budgets", {}).items()
                },
                "leanvibe_deployment_frozen": 1 if error_budget_status.get("deployment_frozen", False) else 0,
                
                # Performance budget metrics
                "leanvibe_performance_budget_consumption_ratio": {
                    budget_name: budget_data["budget_consumption"]
                    for budget_name, budget_data in perf_budget_status.get("budgets", {}).items()
                },
                "leanvibe_response_time_p95_ms": {
                    budget_name: budget_data["percentiles"]["p95"]
                    for budget_name, budget_data in perf_budget_status.get("budgets", {}).items()
                    if "percentiles" in budget_data
                },
                
                # Alert metrics
                "leanvibe_alerts_active_total": alert_summary.get("active_alerts_count", 0),
                "leanvibe_alerts_critical_total": alert_summary.get("critical_alerts", 0),
                "leanvibe_alerts_warning_total": alert_summary.get("warning_alerts", 0),
                "leanvibe_alerts_24h_total": alert_summary.get("total_alerts_24h", 0),
            },
            "metadata": {
                "monitoring_version": "1.0.0",
                "probe_count": len(probe_summary.get("probes", {})),
                "error_budget_count": len(error_budget_status.get("budgets", {})),
                "performance_budget_count": len(perf_budget_status.get("budgets", {}))
            }
        }
        
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to get monitoring metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Monitoring metrics fetch failed: {str(e)}")


@router.get("/dashboard", response_class=HTMLResponse)
async def get_monitoring_dashboard() -> HTMLResponse:
    """
    Get HTML monitoring dashboard
    
    Returns a real-time dashboard showing:
    - System health overview with color-coded status
    - Individual probe results and trends
    - Error budget consumption with deployment freeze warnings
    - Performance metrics and SLA compliance
    - Active alerts with recommended actions
    """
    try:
        logger.info("Serving monitoring dashboard")
        
        # Read dashboard HTML file
        if not DASHBOARD_HTML_PATH.exists():
            raise HTTPException(status_code=404, detail="Dashboard HTML file not found")
        
        dashboard_html = DASHBOARD_HTML_PATH.read_text(encoding='utf-8')
        
        return HTMLResponse(
            content=dashboard_html,
            status_code=200,
            headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
        )
        
    except Exception as e:
        logger.error(f"Failed to serve monitoring dashboard: {e}")
        raise HTTPException(status_code=500, detail=f"Dashboard unavailable: {str(e)}")


@router.get("/dashboard/data")
async def get_dashboard_data() -> Dict[str, Any]:
    """
    Get dashboard data as JSON for AJAX updates
    
    This endpoint is used by the HTML dashboard for live updates.
    Returns the same data structure expected by the dashboard JavaScript.
    """
    try:
        logger.info("Fetching dashboard data for AJAX update")
        
        # Refresh dashboard data
        await health_dashboard.refresh_data()
        
        # Get formatted dashboard data
        dashboard_data = health_dashboard.get_dashboard_html_data()
        
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Failed to get dashboard data: {e}")
        raise HTTPException(status_code=500, detail=f"Dashboard data fetch failed: {str(e)}")


@router.get("/probes")
async def run_monitoring_probes() -> Dict[str, Any]:
    """
    Run synthetic probes on demand and return results
    
    Executes all synthetic probes (Health, Metrics, WebSocket, API) and returns:
    - Individual probe results with response times
    - Overall system health assessment  
    - SLA compliance status
    - Recommended actions for any issues detected
    """
    try:
        logger.info("Running synthetic probes on demand")
        
        # Run all synthetic probes
        probe_results = await run_synthetic_probes()
        
        # Get probe summary with trends
        probe_summary = get_probe_summary()
        
        # Analyze results and generate recommendations
        recommendations = _generate_probe_recommendations(probe_results)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "status": "success",
            "execution_type": "on_demand",
            "probe_results": {
                name: {
                    "status": result.status.value,
                    "response_time_ms": result.response_time_ms,
                    "message": result.message,
                    "timestamp": result.timestamp.isoformat(),
                    "details": result.details,
                    "error": result.error
                }
                for name, result in probe_results.items()
            },
            "summary": probe_summary,
            "recommendations": recommendations,
            "sla_compliance": _evaluate_sla_compliance(probe_results)
        }
        
    except Exception as e:
        logger.error(f"Failed to run monitoring probes: {e}")
        raise HTTPException(status_code=500, detail=f"Probe execution failed: {str(e)}")


@router.get("/error-budget")
async def get_error_budget() -> Dict[str, Any]:
    """
    Get error budget status and deployment freeze decisions
    
    Returns:
    - Error budget consumption for each component
    - Deployment freeze status and reasoning
    - Budget reset times and recommendations
    - Historical trends and patterns
    """
    try:
        logger.info("Fetching error budget status")
        
        error_budget_status = get_error_budget_status()
        
        # Add additional analysis
        budget_analysis = _analyze_error_budgets(error_budget_status)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "status": "success",
            "error_budgets": error_budget_status,
            "analysis": budget_analysis,
            "deployment_recommendations": _get_deployment_recommendations(error_budget_status)
        }
        
    except Exception as e:
        logger.error(f"Failed to get error budget status: {e}")
        raise HTTPException(status_code=500, detail=f"Error budget fetch failed: {str(e)}")


@router.get("/performance-budget")
async def get_performance_budget() -> Dict[str, Any]:
    """
    Get performance budget status and SLA compliance
    
    Returns:
    - Performance percentiles (P50, P95, P99) for each component
    - SLA compliance status against targets
    - Performance trends and degradation warnings
    - Optimization recommendations
    """
    try:
        logger.info("Fetching performance budget status")
        
        perf_budget_status = get_performance_budget_status()
        
        # Add performance analysis
        perf_analysis = _analyze_performance_budgets(perf_budget_status)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "status": "success",
            "performance_budgets": perf_budget_status,
            "analysis": perf_analysis,
            "optimization_recommendations": _get_performance_recommendations(perf_budget_status)
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance budget status: {e}")
        raise HTTPException(status_code=500, detail=f"Performance budget fetch failed: {str(e)}")


@router.get("/alerts")
async def get_monitoring_alerts() -> Dict[str, Any]:
    """
    Get active alerts and alert history
    
    Returns:
    - Active alerts with severity levels
    - Recent alert history and patterns
    - Alert statistics and trends
    - Recommended actions for each alert
    """
    try:
        logger.info("Fetching monitoring alerts")
        
        # Run alert checks first
        await run_alert_check()
        
        # Get alert summary
        alert_summary = alert_manager.get_alert_summary()
        
        # Get active alerts with details
        active_alerts = alert_manager.get_active_alerts()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "status": "success",
            "alert_summary": alert_summary,
            "active_alerts": [
                {
                    "id": alert.id,
                    "level": alert.level.value,
                    "title": alert.title,
                    "message": alert.message,
                    "component": alert.component,
                    "timestamp": alert.timestamp.isoformat(),
                    "details": alert.details,
                    "actions": alert.actions,
                    "resolved": alert.resolved
                }
                for alert in active_alerts
            ],
            "alert_trends": _analyze_alert_trends(alert_summary)
        }
        
    except Exception as e:
        logger.error(f"Failed to get monitoring alerts: {e}")
        raise HTTPException(status_code=500, detail=f"Alert fetch failed: {str(e)}")


@router.post("/simulate-error")
async def simulate_error_for_testing(component: str = "test_component", error_count: int = 1, total_count: int = 10) -> Dict[str, Any]:
    """
    Simulate error for testing error budget tracking
    
    Development endpoint to test error budget functionality.
    Should be disabled in production.
    """
    try:
        logger.info(f"Simulating {error_count}/{total_count} errors for {component}")
        
        # Record simulated errors
        error_budget_tracker.record_errors(component, error_count, total_count)
        
        # Record performance data as well
        performance_budgets.record_response_time(f"{component}_response_time", 250.0)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "status": "success",
            "message": f"Simulated {error_count}/{total_count} errors for {component}",
            "component": component,
            "error_rate": error_count / total_count,
            "budget_status": error_budget_tracker.get_status_summary()
        }
        
    except Exception as e:
        logger.error(f"Failed to simulate error: {e}")
        raise HTTPException(status_code=500, detail=f"Error simulation failed: {str(e)}")


# Helper functions

def _generate_health_recommendations(system_health: Dict[str, Any], alert_summary: Dict[str, Any]) -> list[str]:
    """Generate health recommendations based on system status"""
    recommendations = []
    
    # Check overall system health
    overall_status = system_health.get("overall_status", "unknown")
    if overall_status in ["critical", "unhealthy"]:
        recommendations.append("URGENT: System in critical state - investigate failing probes and error budgets immediately")
    elif overall_status in ["warning", "degraded"]:
        recommendations.append("System degraded - review probe results and performance metrics")
    
    # Check deployment freeze
    if system_health.get("deployment_frozen", False):
        recommendations.append(f"Deployments frozen: {system_health.get('freeze_reason', 'Error budget exceeded')}")
    
    # Check active alerts
    active_alerts = alert_summary.get("active_alerts_count", 0)
    if active_alerts > 0:
        recommendations.append(f"Address {active_alerts} active alerts to improve system health")
    
    if not recommendations:
        recommendations.append("System health is good - continue monitoring")
    
    return recommendations


def _generate_probe_recommendations(probe_results: Dict[str, Any]) -> list[str]:
    """Generate recommendations based on probe results"""
    recommendations = []
    
    for probe_name, result in probe_results.items():
        if result.status.value in ["error", "timeout", "unhealthy"]:
            recommendations.append(f"{probe_name.upper()}: {result.message}")
        elif result.status.value == "degraded":
            recommendations.append(f"{probe_name.upper()}: Performance degraded ({result.response_time_ms:.0f}ms)")
    
    if not recommendations:
        recommendations.append("All probes healthy - system operating within SLA")
    
    return recommendations


def _evaluate_sla_compliance(probe_results: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate SLA compliance from probe results"""
    healthy_count = sum(1 for result in probe_results.values() if result.status.value == "healthy")
    total_count = len(probe_results)
    
    compliance_percentage = (healthy_count / total_count * 100) if total_count > 0 else 0
    
    return {
        "overall_compliance": compliance_percentage,
        "healthy_probes": healthy_count,
        "total_probes": total_count,
        "sla_target": 95.0,  # 95% availability target
        "sla_met": compliance_percentage >= 95.0
    }


def _analyze_error_budgets(error_budget_status: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze error budget consumption patterns"""
    budgets = error_budget_status.get("budgets", {})
    
    critical_budgets = [
        name for name, budget in budgets.items()
        if budget["status"] in ["critical", "exhausted"]
    ]
    
    warning_budgets = [
        name for name, budget in budgets.items()
        if budget["status"] == "warning"
    ]
    
    return {
        "critical_budget_count": len(critical_budgets),
        "warning_budget_count": len(warning_budgets),
        "critical_budgets": critical_budgets,
        "warning_budgets": warning_budgets,
        "overall_risk": "high" if critical_budgets else "medium" if warning_budgets else "low"
    }


def _get_deployment_recommendations(error_budget_status: Dict[str, Any]) -> list[str]:
    """Get deployment recommendations based on error budget status"""
    recommendations = []
    
    if error_budget_status.get("deployment_frozen", False):
        recommendations.append("DEPLOYMENT FREEZE ACTIVE - Do not deploy until error budgets recover")
        recommendations.append(f"Freeze reason: {error_budget_status.get('freeze_reason', 'Unknown')}")
    else:
        analysis = _analyze_error_budgets(error_budget_status)
        if analysis["overall_risk"] == "high":
            recommendations.append("High risk - Consider postponing non-critical deployments")
        elif analysis["overall_risk"] == "medium":
            recommendations.append("Medium risk - Deploy with caution and enhanced monitoring")
        else:
            recommendations.append("Low risk - Safe to deploy")
    
    return recommendations


def _analyze_performance_budgets(perf_budget_status: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze performance budget patterns"""
    budgets = perf_budget_status.get("budgets", {})
    
    exceeded_budgets = [
        name for name, budget in budgets.items()
        if budget["status"] in ["critical", "exhausted"]
    ]
    
    degraded_budgets = [
        name for name, budget in budgets.items()
        if budget["status"] == "warning"
    ]
    
    return {
        "exceeded_budget_count": len(exceeded_budgets),
        "degraded_budget_count": len(degraded_budgets),
        "exceeded_budgets": exceeded_budgets,
        "degraded_budgets": degraded_budgets,
        "performance_risk": "high" if exceeded_budgets else "medium" if degraded_budgets else "low"
    }


def _get_performance_recommendations(perf_budget_status: Dict[str, Any]) -> list[str]:
    """Get performance optimization recommendations"""
    recommendations = []
    
    analysis = _analyze_performance_budgets(perf_budget_status)
    
    if analysis["performance_risk"] == "high":
        recommendations.append("Performance SLA breach - Immediate optimization required")
        recommendations.extend([f"Optimize {budget}" for budget in analysis["exceeded_budgets"]])
    elif analysis["performance_risk"] == "medium":
        recommendations.append("Performance degradation detected - Monitor and optimize")
        recommendations.extend([f"Review {budget} performance" for budget in analysis["degraded_budgets"]])
    else:
        recommendations.append("Performance within SLA targets")
    
    return recommendations


def _analyze_alert_trends(alert_summary: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze alert trends and patterns"""
    return {
        "alert_rate_24h": alert_summary.get("total_alerts_24h", 0) / 24,  # alerts per hour
        "critical_alert_ratio": (
            alert_summary.get("critical_alerts", 0) / 
            max(alert_summary.get("active_alerts_count", 1), 1)
        ),
        "trend": "increasing" if alert_summary.get("total_alerts_24h", 0) > 10 else "stable"
    }