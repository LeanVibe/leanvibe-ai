"""
Monitoring and Observability API Endpoints

Provides comprehensive monitoring data through REST API endpoints:
- Health status and service monitoring
- Performance metrics and analytics
- Error tracking and alerting
- System resource monitoring
- Dashboard data aggregation
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse

from ...auth import api_key_dependency
from ...auth.permissions import require_permission, Permission
from ...core.logging_config import get_logger, set_request_context, generate_request_id
from ...core.health_monitor import health_monitor, run_health_checks, get_service_health, get_current_alerts
from ...core.performance_monitor import performance_monitor, get_performance_stats
from ...core.error_tracker import error_tracker, get_error_summary
from ...core.service_manager import service_manager
from ...core.websocket_monitor import websocket_monitor, get_websocket_stats


logger = get_logger(__name__)
router = APIRouter()


# Dependency for request context
async def setup_request_context():
    """Set up request context for logging"""
    request_id = generate_request_id()
    set_request_context(request_id=request_id)
    return request_id


@router.get("/monitoring/health")
async def get_comprehensive_health(
    request_id: str = Depends(setup_request_context),
    authenticated: bool = Depends(api_key_dependency),
    _admin = Depends(require_permission(Permission.ADMIN_ALL))
) -> Dict[str, Any]:
    """
    Get comprehensive health status for all services and components
    
    Returns detailed health information including:
    - Overall system health status
    - Individual service health metrics
    - System resource utilization
    - Active alerts and recommendations
    """
    try:
        logger.info("Fetching comprehensive health status")
        
        # Run health checks
        health_status = await run_health_checks()
        
        # Get active alerts
        alerts = get_current_alerts()
        
        # Get system resource stats
        system_stats = performance_monitor.get_system_resource_stats(duration_minutes=15)
        
        # Get service manager summary
        service_summary = service_manager.get_service_summary()
        
        response = {
            'timestamp': datetime.now().isoformat(),
            'request_id': request_id,
            'overall_health': health_status,
            'service_summary': service_summary,
            'system_resources': system_stats,
            'active_alerts': alerts,
            'alert_count': len(alerts),
            'monitoring_status': {
                'health_monitoring': True,
                'performance_monitoring': performance_monitor._monitoring_active,
                'error_tracking': error_tracker._processing_active,
                'last_health_check': health_status.get('last_check'),
            }
        }
        
        # Determine HTTP status code based on health
        status_code = 200
        overall_status = health_status.get('status', 'unknown')
        if overall_status in ['critical', 'unhealthy']:
            status_code = 503
        elif overall_status == 'degraded':
            status_code = 200  # Still operational
        
        return JSONResponse(content=response, status_code=status_code)
        
    except Exception as e:
        logger.error("Failed to fetch health status", error=str(e))
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/monitoring/health/{service_name}")
async def get_service_health_detail(
    service_name: str,
    request_id: str = Depends(setup_request_context)
) -> Dict[str, Any]:
    """Get detailed health information for a specific service"""
    try:
        logger.info("Fetching service health details", service_name=service_name)
        
        # Get service health from health monitor
        service_health = get_service_health(service_name)
        
        if not service_health:
            raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")
        
        # Get performance stats for the service
        service_performance = performance_monitor.get_operation_stats(operation_name=service_name)
        
        # Get error metrics for the service
        recent_errors = []
        for error in list(error_tracker.error_history)[-100:]:  # Last 100 errors
            if error.service == service_name:
                recent_errors.append({
                    'id': error.id,
                    'timestamp': error.timestamp.isoformat(),
                    'error_type': error.error_type,
                    'message': error.error_message,
                    'severity': error.severity.value,
                    'resolved': error.resolved
                })
        
        return {
            'service_name': service_name,
            'timestamp': datetime.now().isoformat(),
            'request_id': request_id,
            'health': service_health,
            'performance': service_performance,
            'recent_errors': recent_errors,
            'error_count_24h': len(recent_errors)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to fetch service health", service_name=service_name, error=str(e))
        raise HTTPException(status_code=500, detail=f"Service health check failed: {str(e)}")


@router.get("/monitoring/performance")
async def get_performance_overview(
    duration_hours: int = Query(default=24, ge=1, le=168),  # 1 hour to 1 week
    request_id: str = Depends(setup_request_context)
) -> Dict[str, Any]:
    """
    Get comprehensive performance overview
    
    Args:
        duration_hours: Time window for performance data (1-168 hours)
    """
    try:
        logger.info("Fetching performance overview", duration_hours=duration_hours)
        
        # Get comprehensive performance statistics
        performance_stats = get_performance_stats()
        
        # Get system resource metrics for the specified duration
        system_resources = performance_monitor.get_system_resource_stats(duration_minutes=duration_hours * 60)
        
        # Get endpoint performance statistics
        endpoint_stats = performance_monitor.get_endpoint_stats()
        
        # Get active operations
        active_operations = performance_monitor.get_active_operations()
        
        # Calculate performance trends
        trends = await _calculate_performance_trends(duration_hours)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'request_id': request_id,
            'time_window': f"{duration_hours}h",
            'summary': performance_stats['summary'],
            'operations': performance_stats['operations'],
            'endpoints': endpoint_stats,
            'system_resources': system_resources,
            'active_operations': active_operations,
            'trends': trends,
            'recommendations': _generate_performance_recommendations(performance_stats, system_resources)
        }
        
    except Exception as e:
        logger.error("Failed to fetch performance overview", error=str(e))
        raise HTTPException(status_code=500, detail=f"Performance data fetch failed: {str(e)}")


@router.get("/monitoring/errors")
async def get_error_overview(
    duration_hours: int = Query(default=24, ge=1, le=168),
    severity: Optional[str] = Query(default=None, regex="^(low|medium|high|critical)$"),
    category: Optional[str] = Query(default=None),
    request_id: str = Depends(setup_request_context),
    _admin = Depends(require_permission(Permission.ADMIN_ALL))
) -> Dict[str, Any]:
    """
    Get comprehensive error tracking overview
    
    Args:
        duration_hours: Time window for error data (1-168 hours)
        severity: Filter by error severity
        category: Filter by error category
    """
    try:
        logger.info("Fetching error overview", duration_hours=duration_hours, severity=severity, category=category)
        
        # Get error metrics
        error_metrics = error_tracker.get_error_metrics(duration_hours)
        
        # Get error summary
        error_summary = get_error_summary()
        
        # Get active alerts
        active_alerts = error_tracker.get_active_alerts()
        
        # Get error patterns
        error_patterns = error_tracker.get_error_patterns(min_occurrences=2)
        
        # Get recovery metrics
        recovery_metrics = error_tracker.get_recovery_metrics()
        
        # Filter recent errors
        cutoff_time = datetime.now() - timedelta(hours=duration_hours)
        filtered_errors = []
        
        for error in list(error_tracker.error_history):
            if error.timestamp < cutoff_time:
                continue
                
            if severity and error.severity.value != severity:
                continue
                
            if category and error.category.value != category:
                continue
            
            filtered_errors.append({
                'id': error.id,
                'timestamp': error.timestamp.isoformat(),
                'service': error.service,
                'component': error.component,
                'error_type': error.error_type,
                'message': error.error_message[:200],  # Truncate long messages
                'severity': error.severity.value,
                'category': error.category.value,
                'resolved': error.resolved,
                'resolution_time_minutes': (
                    (error.resolution_time - error.timestamp).total_seconds() / 60
                    if error.resolved and error.resolution_time else None
                )
            })
        
        # Sort by timestamp descending
        filtered_errors.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Format alerts
        formatted_alerts = []
        for alert in active_alerts:
            formatted_alerts.append({
                'id': alert.id,
                'type': alert.alert_type.value,
                'severity': alert.severity.value,
                'title': alert.title,
                'description': alert.description,
                'affected_services': alert.affected_services,
                'error_count': alert.error_count,
                'timestamp': alert.timestamp.isoformat(),
                'acknowledged': alert.acknowledged,
                'recommended_actions': alert.recommended_actions
            })
        
        # Format error patterns
        formatted_patterns = []
        for pattern in error_patterns:
            formatted_patterns.append({
                'pattern_hash': pattern.pattern_hash,
                'error_type': pattern.error_type,
                'occurrences': pattern.occurrences,
                'first_seen': pattern.first_seen.isoformat() if pattern.first_seen else None,
                'last_seen': pattern.last_seen.isoformat() if pattern.last_seen else None,
                'affected_services': list(pattern.affected_services),
                'severity': pattern.severity.value,
                'category': pattern.category.value
            })
        
        return {
            'timestamp': datetime.now().isoformat(),
            'request_id': request_id,
            'time_window': f"{duration_hours}h",
            'filters': {
                'severity': severity,
                'category': category
            },
            'metrics': {
                'total_errors': error_metrics.total_errors,
                'error_rate_per_minute': error_metrics.error_rate_per_minute,
                'resolved_errors': error_metrics.resolved_errors,
                'resolution_rate': error_metrics.resolved_errors / error_metrics.total_errors if error_metrics.total_errors > 0 else 0,
                'errors_by_severity': error_metrics.errors_by_severity,
                'errors_by_category': error_metrics.errors_by_category,
                'errors_by_service': error_metrics.errors_by_service,
                'mean_resolution_time_minutes': error_metrics.mean_resolution_time_minutes
            },
            'summary': error_summary,
            'recent_errors': filtered_errors[:100],  # Limit to 100 most recent
            'active_alerts': formatted_alerts,
            'error_patterns': formatted_patterns,
            'recovery_metrics': recovery_metrics,
            'recommendations': _generate_error_recommendations(error_metrics, active_alerts)
        }
        
    except Exception as e:
        logger.error("Failed to fetch error overview", error=str(e))
        raise HTTPException(status_code=500, detail=f"Error data fetch failed: {str(e)}")


@router.get("/monitoring/alerts")
async def get_alerts(
    include_resolved: bool = Query(default=False),
    severity: Optional[str] = Query(default=None, regex="^(low|medium|high|critical)$"),
    request_id: str = Depends(setup_request_context),
    _admin = Depends(require_permission(Permission.ADMIN_ALL))
) -> Dict[str, Any]:
    """
    Get current alerts with optional filtering
    
    Args:
        include_resolved: Include resolved alerts
        severity: Filter by alert severity
    """
    try:
        logger.info("Fetching alerts", include_resolved=include_resolved, severity=severity)
        
        # Get active alerts
        active_alerts = error_tracker.get_active_alerts()
        
        # Get health alerts
        health_alerts = get_current_alerts()
        
        # Combine and filter alerts
        all_alerts = []
        
        # Add error tracker alerts
        for alert in active_alerts:
            if not include_resolved and alert.resolved:
                continue
                
            if severity and alert.severity.value != severity:
                continue
            
            all_alerts.append({
                'id': alert.id,
                'source': 'error_tracker',
                'type': alert.alert_type.value,
                'severity': alert.severity.value,
                'title': alert.title,
                'description': alert.description,
                'affected_services': alert.affected_services,
                'error_count': alert.error_count,
                'time_window': alert.time_window,
                'timestamp': alert.timestamp.isoformat(),
                'acknowledged': alert.acknowledged,
                'acknowledged_by': alert.acknowledged_by,
                'acknowledged_at': alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                'resolved': alert.resolved,
                'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None,
                'recommended_actions': alert.recommended_actions
            })
        
        # Add health monitor alerts
        for alert in health_alerts:
            alert_data = {
                'id': f"health_{alert.get('type', 'unknown')}_{int(datetime.now().timestamp())}",
                'source': 'health_monitor',
                'type': alert.get('type', 'health_issue'),
                'severity': alert.get('level', 'medium'),
                'title': alert.get('message', 'Health Issue'),
                'description': alert.get('action', 'Check system health'),
                'affected_services': [alert.get('service', 'system')],
                'timestamp': datetime.now().isoformat(),
                'acknowledged': False,
                'resolved': False,
                'recommended_actions': [alert.get('action', 'Check system health')]
            }
            
            if not severity or alert_data['severity'] == severity:
                all_alerts.append(alert_data)
        
        # Sort by timestamp descending
        all_alerts.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Calculate alert statistics
        alert_stats = {
            'total_alerts': len(all_alerts),
            'active_alerts': len([a for a in all_alerts if not a['resolved']]),
            'acknowledged_alerts': len([a for a in all_alerts if a['acknowledged']]),
            'unacknowledged_active': len([a for a in all_alerts if not a['resolved'] and not a['acknowledged']]),
            'alerts_by_severity': {},
            'alerts_by_type': {},
            'alerts_by_service': {}
        }
        
        for alert in all_alerts:
            severity_key = alert['severity']
            alert_stats['alerts_by_severity'][severity_key] = alert_stats['alerts_by_severity'].get(severity_key, 0) + 1
            
            type_key = alert['type']
            alert_stats['alerts_by_type'][type_key] = alert_stats['alerts_by_type'].get(type_key, 0) + 1
            
            for service in alert['affected_services']:
                alert_stats['alerts_by_service'][service] = alert_stats['alerts_by_service'].get(service, 0) + 1
        
        return {
            'timestamp': datetime.now().isoformat(),
            'request_id': request_id,
            'filters': {
                'include_resolved': include_resolved,
                'severity': severity
            },
            'statistics': alert_stats,
            'alerts': all_alerts
        }
        
    except Exception as e:
        logger.error("Failed to fetch alerts", error=str(e))
        raise HTTPException(status_code=500, detail=f"Alert fetch failed: {str(e)}")


@router.post("/monitoring/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    acknowledged_by: str = Query(..., description="User acknowledging the alert"),
    request_id: str = Depends(setup_request_context),
    _admin = Depends(require_permission(Permission.ADMIN_ALL))
) -> Dict[str, Any]:
    """Acknowledge an alert"""
    try:
        logger.info("Acknowledging alert", alert_id=alert_id, acknowledged_by=acknowledged_by)
        
        # Try to acknowledge in error tracker
        error_tracker.acknowledge_alert(alert_id, acknowledged_by)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'request_id': request_id,
            'alert_id': alert_id,
            'acknowledged': True,
            'acknowledged_by': acknowledged_by,
            'message': 'Alert acknowledged successfully'
        }
        
    except Exception as e:
        logger.error("Failed to acknowledge alert", alert_id=alert_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Alert acknowledgment failed: {str(e)}")


@router.post("/monitoring/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    request_id: str = Depends(setup_request_context),
    _admin = Depends(require_permission(Permission.ADMIN_ALL))
) -> Dict[str, Any]:
    """Resolve an alert"""
    try:
        logger.info("Resolving alert", alert_id=alert_id)
        
        # Try to resolve in error tracker
        error_tracker.resolve_alert(alert_id)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'request_id': request_id,
            'alert_id': alert_id,
            'resolved': True,
            'message': 'Alert resolved successfully'
        }
        
    except Exception as e:
        logger.error("Failed to resolve alert", alert_id=alert_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Alert resolution failed: {str(e)}")


@router.get("/monitoring/dashboard")
async def get_dashboard_data(
    request_id: str = Depends(setup_request_context),
    _admin = Depends(require_permission(Permission.ADMIN_ALL))
) -> Dict[str, Any]:
    """
    Get comprehensive dashboard data combining all monitoring systems
    
    This endpoint provides a complete overview suitable for operational dashboards
    """
    try:
        logger.info("Fetching dashboard data")
        
        # Run all monitoring checks concurrently
        health_task = asyncio.create_task(run_health_checks())
        
        # Wait for health check to complete
        health_status = await health_task
        
        # Get other monitoring data
        performance_stats = get_performance_stats()
        error_summary = get_error_summary()
        active_alerts = error_tracker.get_active_alerts()
        system_resources = performance_monitor.get_system_resource_stats(duration_minutes=60)
        service_summary = service_manager.get_service_summary()
        
        # Calculate key metrics
        key_metrics = {
            'services_healthy': len([s for s in health_status.get('services', {}).values() if s.get('available')]),
            'total_services': len(health_status.get('services', {})),
            'active_alerts': len([a for a in active_alerts if not a.resolved]),
            'error_rate_24h': error_summary['metrics_24h']['error_rate_per_minute'],
            'system_cpu_usage': system_resources.get('latest_sample', {}).get('cpu_percent', 0),
            'system_memory_usage': system_resources.get('latest_sample', {}).get('memory_percent', 0),
            'uptime_hours': health_status.get('uptime_seconds', 0) / 3600,
            'requests_per_minute': performance_stats.get('endpoints', {}).get('summary', {}).get('overall_avg_response_time', 0)
        }
        
        # Determine overall system status
        overall_status = 'healthy'
        if key_metrics['active_alerts'] > 0:
            if any(a.severity.value in ['critical', 'high'] for a in active_alerts if not a.resolved):
                overall_status = 'critical'
            else:
                overall_status = 'degraded'
        
        if health_status.get('status') in ['critical', 'unhealthy']:
            overall_status = 'critical'
        elif health_status.get('status') == 'degraded':
            overall_status = 'degraded'
        
        # Recent activity
        recent_activity = []
        
        # Add recent errors
        for error in list(error_tracker.error_history)[-10:]:
            recent_activity.append({
                'timestamp': error.timestamp.isoformat(),
                'type': 'error',
                'severity': error.severity.value,
                'message': f"Error in {error.service}: {error.error_type}",
                'service': error.service
            })
        
        # Add recent alerts
        for alert in list(error_tracker.alert_history)[-5:]:
            recent_activity.append({
                'timestamp': alert.timestamp.isoformat(),
                'type': 'alert',
                'severity': alert.severity.value,
                'message': alert.title,
                'service': alert.affected_services[0] if alert.affected_services else 'system'
            })
        
        # Sort by timestamp descending
        recent_activity.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Service status breakdown
        service_status = {}
        for service_name, service_data in health_status.get('services', {}).items():
            service_status[service_name] = {
                'status': 'healthy' if service_data.get('available') else 'unhealthy',
                'response_time': service_data.get('response_time', 0),
                'last_check': service_data.get('last_health_check')
            }
        
        return {
            'timestamp': datetime.now().isoformat(),
            'request_id': request_id,
            'overall_status': overall_status,
            'key_metrics': key_metrics,
            'health_summary': {
                'status': health_status.get('status'),
                'message': health_status.get('message'),
                'services': service_status
            },
            'performance_summary': {
                'monitoring_active': performance_stats['summary']['monitoring_active'],
                'operations_tracked': performance_stats['summary']['metrics_collected'],
                'endpoints_tracked': performance_stats['summary']['endpoints_tracked'],
                'avg_response_time': performance_stats.get('endpoints', {}).get('summary', {}).get('overall_avg_response_time', 0)
            },
            'error_summary': {
                'errors_24h': error_summary['metrics_24h']['total_errors'],
                'error_rate': error_summary['metrics_24h']['error_rate_per_minute'],
                'resolution_rate': error_summary['metrics_24h']['resolution_rate'],
                'active_patterns': error_summary['error_patterns']
            },
            'alert_summary': {
                'active_alerts': len(active_alerts),
                'unacknowledged_alerts': len([a for a in active_alerts if not a.acknowledged]),
                'critical_alerts': len([a for a in active_alerts if a.severity.value == 'critical'])
            },
            'system_resources': {
                'cpu_percent': system_resources.get('latest_sample', {}).get('cpu_percent', 0),
                'memory_percent': system_resources.get('latest_sample', {}).get('memory_percent', 0),
                'active_connections': system_resources.get('latest_sample', {}).get('active_connections', 0),
                'thread_count': system_resources.get('latest_sample', {}).get('thread_count', 0)
            },
            'recent_activity': recent_activity[:20],  # Last 20 activities
            'monitoring_status': {
                'health_monitoring': True,
                'performance_monitoring': performance_monitor._monitoring_active,
                'error_tracking': error_tracker._processing_active,
                'last_update': datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error("Failed to fetch dashboard data", error=str(e))
        raise HTTPException(status_code=500, detail=f"Dashboard data fetch failed: {str(e)}")


@router.get("/monitoring/websockets")
async def get_websocket_overview(
    time_window_minutes: int = Query(default=60, ge=5, le=1440),  # 5 minutes to 24 hours
    request_id: str = Depends(setup_request_context),
    _admin = Depends(require_permission(Permission.ADMIN_ALL))
) -> Dict[str, Any]:
    """
    Get comprehensive WebSocket connection overview
    
    Args:
        time_window_minutes: Time window for WebSocket metrics (5-1440 minutes)
    """
    try:
        logger.info("Fetching WebSocket overview", time_window_minutes=time_window_minutes)
        
        # Get WebSocket statistics
        connection_stats = websocket_monitor.get_connection_stats()
        performance_metrics = websocket_monitor.get_performance_metrics(time_window_minutes)
        monitoring_summary = websocket_monitor.get_monitoring_summary()
        active_connections = websocket_monitor.get_connection_list(limit=50)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'request_id': request_id,
            'time_window_minutes': time_window_minutes,
            'monitoring_active': monitoring_summary['monitoring_active'],
            'connection_stats': connection_stats,
            'performance_metrics': performance_metrics,
            'active_connections': active_connections,
            'summary': monitoring_summary,
            'health_indicators': monitoring_summary.get('health_indicators', {}),
            'recommendations': _generate_websocket_recommendations(connection_stats, performance_metrics)
        }
        
    except Exception as e:
        logger.error("Failed to fetch WebSocket overview", error=str(e))
        raise HTTPException(status_code=500, detail=f"WebSocket data fetch failed: {str(e)}")


@router.get("/monitoring/websockets/{connection_id}")
async def get_websocket_connection_detail(
    connection_id: str,
    request_id: str = Depends(setup_request_context),
    _admin = Depends(require_permission(Permission.ADMIN_ALL))
) -> Dict[str, Any]:
    """Get detailed information for a specific WebSocket connection"""
    try:
        logger.info("Fetching WebSocket connection details", connection_id=connection_id)
        
        # Get connection-specific statistics
        connection_stats = websocket_monitor.get_connection_stats(connection_id)
        
        if 'error' in connection_stats:
            raise HTTPException(status_code=404, detail=f"WebSocket connection '{connection_id}' not found")
        
        return {
            'timestamp': datetime.now().isoformat(),
            'request_id': request_id,
            'connection': connection_stats,
            'recommendations': _generate_connection_recommendations(connection_stats)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to fetch WebSocket connection details", connection_id=connection_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"WebSocket connection detail fetch failed: {str(e)}")


def _generate_websocket_recommendations(connection_stats: Dict[str, Any], performance_metrics: Dict[str, Any]) -> List[str]:
    """Generate WebSocket performance and optimization recommendations"""
    recommendations = []
    
    try:
        pool_stats = connection_stats.get('pool_stats', {})
        
        # Check connection success rate
        success_rate = pool_stats.get('connection_success_rate', 1.0)
        if success_rate < 0.95:  # Less than 95% success rate
            recommendations.append(f"Connection success rate is low ({success_rate:.1%}) - investigate connection issues and network stability")
        
        # Check active connections
        active_connections = pool_stats.get('active_connections', 0)
        peak_connections = pool_stats.get('peak_connections', 0)
        
        if active_connections > 1000:
            recommendations.append("High number of active connections - consider connection pooling or load balancing")
        
        if peak_connections > active_connections * 2:
            recommendations.append("Large variance in connection count - implement connection limiting or queuing")
        
        # Check message performance
        error_rate = performance_metrics.get('error_rate', 0)
        if error_rate > 0.01:  # More than 1% error rate
            recommendations.append(f"High message error rate ({error_rate:.2%}) - investigate message handling and validation")
        
        avg_processing_time = performance_metrics.get('avg_processing_time_ms', 0)
        if avg_processing_time > 1000:  # More than 1 second
            recommendations.append(f"High message processing time ({avg_processing_time:.0f}ms) - optimize message handlers")
        
        # Check message size
        avg_message_size = performance_metrics.get('avg_message_size_bytes', 0)
        if avg_message_size > 50000:  # More than 50KB
            recommendations.append(f"Large average message size ({avg_message_size/1024:.1f}KB) - consider message compression or chunking")
        
        # Check message rate
        messages_per_minute = performance_metrics.get('messages_per_minute', 0)
        if messages_per_minute > 1000:
            recommendations.append(f"High message rate ({messages_per_minute:.0f}/min) - monitor system resources and consider rate limiting")
        
        if not recommendations:
            recommendations.append("WebSocket performance is within acceptable ranges")
            
    except Exception as e:
        logger.error("Failed to generate WebSocket recommendations", error=str(e))
        recommendations.append("Unable to generate recommendations due to data analysis error")
    
    return recommendations


def _generate_connection_recommendations(connection_stats: Dict[str, Any]) -> List[str]:
    """Generate recommendations for a specific WebSocket connection"""
    recommendations = []
    
    try:
        # Check connection quality
        quality = connection_stats.get('connection_quality', 1.0)
        if quality < 0.8:
            recommendations.append(f"Connection quality is degraded ({quality:.1%}) - investigate network issues or client-side problems")
        
        # Check error count
        error_count = connection_stats.get('error_count', 0)
        if error_count > 0:
            recommendations.append(f"Connection has {error_count} errors - review error patterns and implement retry logic")
        
        # Check connection duration
        duration_seconds = connection_stats.get('duration_seconds', 0)
        if duration_seconds > 24 * 3600:  # More than 24 hours
            recommendations.append(f"Long-running connection ({duration_seconds/3600:.1f} hours) - consider connection refresh or health checks")
        
        # Check message activity
        total_messages = connection_stats.get('messages_sent', 0) + connection_stats.get('messages_received', 0)
        if total_messages == 0 and duration_seconds > 300:  # No messages for 5+ minutes
            recommendations.append("Idle connection with no message activity - consider connection timeout or keep-alive mechanisms")
        
        # Check average message size
        avg_message_size = connection_stats.get('avg_message_size', 0)
        if avg_message_size > 100000:  # More than 100KB
            recommendations.append(f"Large average message size ({avg_message_size/1024:.1f}KB) - consider message optimization")
        
        if not recommendations:
            recommendations.append("Connection appears to be healthy and performing well")
            
    except Exception as e:
        logger.error("Failed to generate connection recommendations", error=str(e))
        recommendations.append("Unable to generate recommendations due to data analysis error")
    
    return recommendations


# Helper functions
async def _calculate_performance_trends(duration_hours: int) -> Dict[str, Any]:
    """Calculate performance trends over time"""
    try:
        # This would typically analyze historical data to identify trends
        # For now, return placeholder trend data
        return {
            'response_time_trend': 'stable',  # improving, degrading, stable
            'error_rate_trend': 'stable',
            'throughput_trend': 'stable',
            'resource_usage_trend': 'stable',
            'confidence': 0.8  # Confidence in trend analysis
        }
    except Exception as e:
        logger.error("Failed to calculate performance trends", error=str(e))
        return {
            'response_time_trend': 'unknown',
            'error_rate_trend': 'unknown',
            'throughput_trend': 'unknown',
            'resource_usage_trend': 'unknown',
            'confidence': 0.0
        }


def _generate_performance_recommendations(performance_stats: Dict[str, Any], system_resources: Dict[str, Any]) -> List[str]:
    """Generate performance optimization recommendations"""
    recommendations = []
    
    try:
        # Check system resource usage
        latest_sample = system_resources.get('latest_sample', {})
        cpu_percent = latest_sample.get('cpu_percent', 0)
        memory_percent = latest_sample.get('memory_percent', 0)
        
        if cpu_percent > 80:
            recommendations.append("High CPU usage detected - consider scaling or optimizing CPU-intensive operations")
        
        if memory_percent > 85:
            recommendations.append("High memory usage detected - investigate memory leaks or consider increasing memory allocation")
        
        # Check endpoint performance
        endpoint_summary = performance_stats.get('endpoints', {}).get('summary', {})
        avg_response_time = endpoint_summary.get('overall_avg_response_time', 0)
        
        if avg_response_time > 1000:  # > 1 second
            recommendations.append("High average response time detected - investigate slow endpoints and optimize database queries")
        
        # Check operation performance
        operations_summary = performance_stats.get('operations', {})
        if operations_summary.get('failed_operations', 0) > 0:
            failure_rate = operations_summary.get('failed_operations', 0) / operations_summary.get('total_operations', 1)
            if failure_rate > 0.05:  # > 5% failure rate
                recommendations.append("High operation failure rate detected - review error handling and retry mechanisms")
        
        if not recommendations:
            recommendations.append("System performance is within acceptable ranges")
            
    except Exception as e:
        logger.error("Failed to generate performance recommendations", error=str(e))
        recommendations.append("Unable to generate recommendations due to data analysis error")
    
    return recommendations


def _generate_error_recommendations(error_metrics: Any, active_alerts: List[Any]) -> List[str]:
    """Generate error management recommendations"""
    recommendations = []
    
    try:
        # Check error rate
        if error_metrics.error_rate_per_minute > 5:
            recommendations.append("High error rate detected - investigate recent deployments and system changes")
        
        # Check resolution rate
        if error_metrics.total_errors > 0:
            resolution_rate = error_metrics.resolved_errors / error_metrics.total_errors
            if resolution_rate < 0.8:  # < 80% resolution rate
                recommendations.append("Low error resolution rate - review error handling procedures and automated recovery")
        
        # Check critical alerts
        critical_alerts = [a for a in active_alerts if a.severity.value == 'critical']
        if critical_alerts:
            recommendations.append(f"Critical alerts active ({len(critical_alerts)}) - immediate attention required")
        
        # Check unacknowledged alerts
        unacknowledged = [a for a in active_alerts if not a.acknowledged]
        if len(unacknowledged) > 5:
            recommendations.append("Multiple unacknowledged alerts - ensure proper alert monitoring and response procedures")
        
        if not recommendations:
            recommendations.append("Error rates and alert levels are within acceptable ranges")
            
    except Exception as e:
        logger.error("Failed to generate error recommendations", error=str(e))
        recommendations.append("Unable to generate recommendations due to data analysis error")
    
    return recommendations