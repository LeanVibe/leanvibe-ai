"""
Simple Service Manager for LeanVibe AI Backend

Manages core services with proper initialization order and graceful degradation.
Replaces over-engineered dependency injection with simple service locator pattern.
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List, Type

from .degradation_patterns import (
    degradation_manager, 
    DegradationConfig, 
    FallbackHandlers,
    get_degradation_summary
)

logger = logging.getLogger(__name__)


class ServiceManager:
    """
    Simple service manager that handles initialization, lifecycle, and access
    to core LeanVibe services with graceful degradation.
    """
    
    def __init__(self):
        self.services: Dict[str, Any] = {}
        self.service_status: Dict[str, Dict[str, Any]] = {}
        self.initialization_order = [
            'graph',    # Neo4j (optional but preferred)
            'vector',   # ChromaDB (core requirement)
            'ai',       # Ollama (core requirement)
            'project',  # Project management (optional)
            'monitor'   # File monitoring (optional)
        ]
        self.initialized = False
        
    async def initialize_all_services(self) -> Dict[str, bool]:
        """
        Initialize all services in proper order with graceful degradation.
        Returns status dict with service availability.
        """
        logger.info("🚀 Initializing LeanVibe AI Backend Services...")
        
        # Register services with degradation manager
        self._register_degradation_patterns()
        
        results = {}
        
        for service_name in self.initialization_order:
            try:
                start_time = time.time()
                success = await self._initialize_service(service_name)
                duration = time.time() - start_time
                
                results[service_name] = success
                self.service_status[service_name] = {
                    'available': success,
                    'initialization_time': duration,
                    'last_health_check': time.time() if success else None,
                    'error_count': 0
                }
                
                status_icon = "✅" if success else "❌"
                logger.info(f"   {service_name.title()} Service: {status_icon} ({duration:.2f}s)")
                
            except Exception as e:
                logger.error(f"   {service_name.title()} Service: ❌ ERROR - {e}")
                results[service_name] = False
                self.service_status[service_name] = {
                    'available': False,
                    'error': str(e),
                    'error_count': 1
                }
        
        # Validate minimum requirements
        core_services = ['vector', 'ai']
        available_core = sum(1 for service in core_services if results.get(service))
        
        if available_core < len(core_services):
            logger.warning(f"⚠️ Only {available_core}/{len(core_services)} core services available")
            logger.info("   System will operate in degraded mode")
        else:
            logger.info("✅ All core services available - full functionality enabled")
        
        self.initialized = True
        return results
    
    def _register_degradation_patterns(self):
        """Register all services with the degradation manager"""
        # AI Service - critical with fallback
        degradation_manager.register_service(
            'ai',
            DegradationConfig(
                max_retries=2,
                retry_delay=1.0,
                circuit_breaker_threshold=3,
                circuit_breaker_timeout=30.0,
                fallback_enabled=True
            ),
            FallbackHandlers.ai_service_fallback
        )
        
        # Vector Service - critical with fallback
        degradation_manager.register_service(
            'vector',
            DegradationConfig(
                max_retries=3,
                retry_delay=0.5,
                circuit_breaker_threshold=5,
                circuit_breaker_timeout=60.0,
                fallback_enabled=True
            ),
            FallbackHandlers.vector_search_fallback
        )
        
        # Graph Service - optional with fallback
        degradation_manager.register_service(
            'graph',
            DegradationConfig(
                max_retries=2,
                retry_delay=1.0,
                circuit_breaker_threshold=3,
                circuit_breaker_timeout=45.0,
                fallback_enabled=True
            ),
            FallbackHandlers.graph_analysis_fallback
        )
        
        # Project Service - optional with fallback
        degradation_manager.register_service(
            'project',
            DegradationConfig(
                max_retries=1,
                retry_delay=0.5,
                circuit_breaker_threshold=2,
                circuit_breaker_timeout=30.0,
                fallback_enabled=True
            ),
            FallbackHandlers.project_indexing_fallback
        )
        
        # Monitor Service - optional, no fallback needed
        degradation_manager.register_service(
            'monitor',
            DegradationConfig(
                max_retries=1,
                retry_delay=0.5,
                circuit_breaker_threshold=2,
                circuit_breaker_timeout=30.0,
                fallback_enabled=False
            )
        )
    
    async def _initialize_service(self, service_name: str) -> bool:
        """Initialize a specific service"""
        try:
            if service_name == 'graph':
                from ..services.graph_service import GraphService
                service = GraphService()
                result = await service.initialize()
                if result:
                    self.services['graph'] = service
                return result
                
            elif service_name == 'vector':
                from ..services.vector_store_service import VectorStoreService
                service = VectorStoreService(use_http=True, host="localhost", port=8000)
                result = await service.initialize()
                if result:
                    self.services['vector'] = service
                return result
                
            elif service_name == 'ai':
                from ..services.ollama_ai_service import OllamaAIService
                service = OllamaAIService()
                result = await service.initialize()
                if result and service.is_ready():
                    self.services['ai'] = service
                    return True
                return False
                
            elif service_name == 'project':
                # Simplified project service - will be implemented later
                logger.info("   Project service: Not implemented yet - skipping")
                return False
                
            elif service_name == 'monitor':
                # Simplified monitor service - will be implemented later
                logger.info("   Monitor service: Not implemented yet - skipping")
                return False
                
            else:
                logger.warning(f"Unknown service: {service_name}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize {service_name}: {e}")
            return False
    
    def get_service(self, service_name: str) -> Optional[Any]:
        """
        Get a service instance with automatic fallback handling.
        Returns None if service is not available.
        """
        if not self.initialized:
            logger.warning("Service manager not initialized")
            return None
            
        service = self.services.get(service_name)
        
        if service is None:
            # Log degraded mode operation
            status = self.service_status.get(service_name, {})
            if status.get('available') is False:
                logger.debug(f"Service '{service_name}' not available - operating in degraded mode")
        
        return service
    
    def is_service_available(self, service_name: str) -> bool:
        """Check if a service is available and healthy"""
        status = self.service_status.get(service_name, {})
        return status.get('available', False)
    
    def get_available_services(self) -> List[str]:
        """Get list of available service names"""
        return [
            name for name, status in self.service_status.items()
            if status.get('available', False)
        ]
    
    async def health_check_all(self) -> Dict[str, Any]:
        """
        Perform health checks on all services.
        Returns comprehensive health status including degradation patterns.
        """
        health_status = {
            'timestamp': time.time(),
            'overall_status': 'unknown',
            'services': {},
            'summary': {
                'total_services': len(self.service_status),
                'available_services': 0,
                'core_services_available': 0
            },
            'degradation': get_degradation_summary()
        }
        
        core_services = ['vector', 'ai']
        available_count = 0
        core_available = 0
        
        for service_name, status in self.service_status.items():
            service_health = {
                'available': status.get('available', False),
                'initialization_time': status.get('initialization_time'),
                'error_count': status.get('error_count', 0)
            }
            
            # Perform active health check if service is available
            if status.get('available') and service_name in self.services:
                try:
                    service = self.services[service_name]
                    
                    if service_name == 'ai' and hasattr(service, 'health_check'):
                        ai_health = await service.health_check()
                        service_health['ai_status'] = ai_health.get('status')
                        service_health['response_time'] = ai_health.get('performance', {}).get('test_response_time')
                    
                    elif service_name == 'vector' and hasattr(service, 'get_status'):
                        vector_status = service.get_status()
                        service_health['vector_status'] = 'healthy' if vector_status.get('initialized') else 'unhealthy'
                    
                    service_health['last_health_check'] = time.time()
                    
                except Exception as e:
                    service_health['health_check_error'] = str(e)
                    service_health['available'] = False
            
            health_status['services'][service_name] = service_health
            
            if service_health['available']:
                available_count += 1
                if service_name in core_services:
                    core_available += 1
        
        # Determine overall status
        if core_available == len(core_services):
            health_status['overall_status'] = 'healthy'
        elif core_available > 0:
            health_status['overall_status'] = 'degraded'
        else:
            health_status['overall_status'] = 'unhealthy'
        
        health_status['summary']['available_services'] = available_count
        health_status['summary']['core_services_available'] = core_available
        
        return health_status
    
    async def graceful_shutdown(self):
        """Gracefully shutdown all services"""
        logger.info("🔌 Shutting down services...")
        
        shutdown_order = list(reversed(self.initialization_order))
        
        for service_name in shutdown_order:
            if service_name in self.services:
                try:
                    service = self.services[service_name]
                    if hasattr(service, 'close'):
                        await service.close()
                    logger.info(f"   ✅ {service_name.title()} service closed")
                except Exception as e:
                    logger.error(f"   ❌ Error closing {service_name}: {e}")
        
        self.services.clear()
        self.service_status.clear()
        self.initialized = False
        
        logger.info("✅ All services shut down")
    
    def get_service_summary(self) -> Dict[str, Any]:
        """Get a summary of service status for monitoring/debugging"""
        if not self.initialized:
            return {'status': 'not_initialized'}
        
        available_services = self.get_available_services()
        
        return {
            'initialized': self.initialized,
            'total_services': len(self.service_status),
            'available_services': len(available_services),
            'available_service_names': available_services,
            'core_services_status': {
                'vector': self.is_service_available('vector'),
                'ai': self.is_service_available('ai')
            },
            'optional_services_status': {
                'graph': self.is_service_available('graph'),
                'project': self.is_service_available('project'),
                'monitor': self.is_service_available('monitor')
            }
        }


# Global service manager instance
service_manager = ServiceManager()


# Convenience functions for easy service access
def get_ai_service():
    """Get AI service with fallback handling"""
    return service_manager.get_service('ai')


def get_vector_service():
    """Get vector store service with fallback handling"""
    return service_manager.get_service('vector')


def get_graph_service():
    """Get graph service with fallback handling"""
    return service_manager.get_service('graph')


def get_project_service():
    """Get project service with fallback handling"""
    return service_manager.get_service('project')


def is_service_available(service_name: str) -> bool:
    """Check if a specific service is available"""
    return service_manager.is_service_available(service_name)


async def initialize_backend():
    """Initialize the complete LeanVibe backend"""
    return await service_manager.initialize_all_services()


async def shutdown_backend():
    """Shutdown the complete LeanVibe backend"""
    await service_manager.graceful_shutdown()