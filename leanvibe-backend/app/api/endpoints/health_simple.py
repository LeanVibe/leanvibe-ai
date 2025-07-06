"""
Simplified Health Check Endpoint

Provides comprehensive health information using the new service manager.
Replaces complex health checking with simple, reliable status reporting.
"""

import time
from typing import Dict, Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from ...core.service_manager import service_manager, is_service_available

router = APIRouter()


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Comprehensive health check for all LeanVibe services.
    
    Returns:
        - Overall system status
        - Individual service health
        - Performance metrics
        - Degraded mode information
    """
    try:
        # Get comprehensive health status
        health_status = await service_manager.health_check_all()
        
        # Add system-level information
        system_info = {
            'timestamp': time.time(),
            'service_manager_initialized': service_manager.initialized,
            'degraded_mode': health_status['overall_status'] != 'healthy'
        }
        
        # Determine HTTP status code
        overall_status = health_status['overall_status']
        
        if overall_status == 'healthy':
            status_code = 200
        elif overall_status == 'degraded':
            status_code = 200  # Still functional, just degraded
        else:
            status_code = 503  # Service unavailable
        
        # Build response
        response_data = {
            'status': overall_status,
            'system': system_info,
            'services': health_status['services'],
            'summary': health_status['summary'],
            'capabilities': _get_current_capabilities(),
            'recommendations': _get_health_recommendations(health_status)
        }
        
        return JSONResponse(
            content=response_data,
            status_code=status_code
        )
        
    except Exception as e:
        # Fallback health check if service manager fails
        return JSONResponse(
            content={
                'status': 'error',
                'error': str(e),
                'timestamp': time.time(),
                'fallback': True
            },
            status_code=500
        )


@router.get("/health/simple")
async def simple_health_check() -> Dict[str, Any]:
    """
    Simple health check for load balancers and monitoring.
    
    Returns basic status without detailed service information.
    """
    try:
        if not service_manager.initialized:
            return JSONResponse(
                content={'status': 'starting', 'ready': False},
                status_code=503
            )
        
        # Check core services only
        vector_available = is_service_available('vector')
        ai_available = is_service_available('ai')
        
        # Determine overall health
        if vector_available and ai_available:
            status = 'healthy'
            ready = True
            status_code = 200
        elif vector_available or ai_available:
            status = 'degraded'
            ready = True
            status_code = 200
        else:
            status = 'unhealthy'
            ready = False
            status_code = 503
        
        return JSONResponse(
            content={
                'status': status,
                'ready': ready,
                'timestamp': time.time()
            },
            status_code=status_code
        )
        
    except Exception as e:
        return JSONResponse(
            content={
                'status': 'error',
                'ready': False,
                'error': str(e)
            },
            status_code=500
        )


@router.get("/health/services")
async def services_health() -> Dict[str, Any]:
    """
    Detailed service-by-service health information.
    
    Useful for debugging and service monitoring.
    """
    try:
        summary = service_manager.get_service_summary()
        
        # Add detailed service information
        service_details = {}
        
        for service_name in ['graph', 'vector', 'ai', 'project', 'monitor']:
            is_available = is_service_available(service_name)
            service = service_manager.get_service(service_name)
            
            details = {
                'available': is_available,
                'instance': service is not None,
                'type': 'core' if service_name in ['vector', 'ai'] else 'optional'
            }
            
            # Add service-specific health information
            if service and is_available:
                if service_name == 'ai' and hasattr(service, 'get_performance_stats'):
                    details['performance'] = service.get_performance_stats()
                elif service_name == 'vector' and hasattr(service, 'get_status'):
                    details['status'] = service.get_status()
                elif service_name == 'graph':
                    details['initialized'] = getattr(service, 'initialized', False)
            
            service_details[service_name] = details
        
        return {
            'summary': summary,
            'services': service_details,
            'timestamp': time.time()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/capabilities")
async def current_capabilities() -> Dict[str, Any]:
    """
    Return current system capabilities based on available services.
    
    Helps clients understand what functionality is available.
    """
    capabilities = _get_current_capabilities()
    
    return {
        'capabilities': capabilities,
        'degraded_mode': not all(capabilities.values()),
        'core_functionality': capabilities.get('code_search', False) and capabilities.get('ai_assistance', False),
        'timestamp': time.time()
    }


def _get_current_capabilities() -> Dict[str, bool]:
    """Determine current system capabilities based on service availability"""
    return {
        'code_search': is_service_available('vector'),
        'ai_assistance': is_service_available('ai'),
        'graph_analysis': is_service_available('graph'),
        'project_management': is_service_available('project'),
        'file_monitoring': is_service_available('monitor')
    }


def _get_health_recommendations(health_status: Dict[str, Any]) -> list:
    """Generate health recommendations based on current status"""
    recommendations = []
    
    overall_status = health_status.get('overall_status', 'unknown')
    services = health_status.get('services', {})
    
    if overall_status == 'unhealthy':
        recommendations.append({
            'level': 'critical',
            'message': 'Core services unavailable - check service configuration',
            'action': 'Restart services or check logs for errors'
        })
    
    elif overall_status == 'degraded':
        recommendations.append({
            'level': 'warning',
            'message': 'System operating in degraded mode - some features unavailable',
            'action': 'Check individual service status and resolve issues'
        })
    
    # Service-specific recommendations
    if not services.get('vector', {}).get('available', False):
        recommendations.append({
            'level': 'error',
            'message': 'Vector store unavailable - code search disabled',
            'action': 'Check ChromaDB connection and configuration'
        })
    
    if not services.get('ai', {}).get('available', False):
        recommendations.append({
            'level': 'error',
            'message': 'AI service unavailable - code assistance disabled',
            'action': 'Check Ollama service and model availability'
        })
    
    if not services.get('graph', {}).get('available', False):
        recommendations.append({
            'level': 'warning',
            'message': 'Graph database unavailable - relationship analysis disabled',
            'action': 'Check Neo4j connection and authentication'
        })
    
    # Performance recommendations
    ai_service = services.get('ai', {})
    if ai_service.get('available') and ai_service.get('response_time', 0) > 10:
        recommendations.append({
            'level': 'info',
            'message': 'AI response times slower than optimal',
            'action': 'Consider model optimization or hardware upgrades'
        })
    
    if not recommendations:
        recommendations.append({
            'level': 'success',
            'message': 'All systems operational',
            'action': 'No action required'
        })
    
    return recommendations