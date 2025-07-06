"""
Graceful Service Degradation Patterns for LeanVibe AI Backend

Implements patterns for handling service failures gracefully,
ensuring the system continues to provide value even when
some services are unavailable.
"""

import logging
import time
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union
from dataclasses import dataclass

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class DegradationConfig:
    """Configuration for service degradation behavior"""
    max_retries: int = 3
    retry_delay: float = 1.0
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: float = 60.0
    fallback_enabled: bool = True
    log_degradation: bool = True


class CircuitBreaker:
    """Circuit breaker pattern to prevent cascading failures"""
    
    def __init__(self, threshold: int = 5, timeout: float = 60.0):
        self.threshold = threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func: Callable[..., T], *args, **kwargs) -> Optional[T]:
        """Execute function with circuit breaker protection"""
        if self.state == 'OPEN':
            if self._should_attempt_reset():
                self.state = 'HALF_OPEN'
            else:
                logger.debug(f"Circuit breaker OPEN for {func.__name__}")
                return None
        
        try:
            result = func(*args, **kwargs)
            
            if self.state == 'HALF_OPEN':
                self._reset()
            
            return result
            
        except Exception as e:
            self._record_failure()
            logger.debug(f"Circuit breaker recorded failure for {func.__name__}: {e}")
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset"""
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time > self.timeout
    
    def _record_failure(self):
        """Record a failure and potentially open circuit"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.threshold:
            self.state = 'OPEN'
            logger.warning(f"Circuit breaker OPENED after {self.failure_count} failures")
    
    def _reset(self):
        """Reset circuit breaker to closed state"""
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'
        logger.info("Circuit breaker RESET to CLOSED state")


class ServiceDegradationManager:
    """Manages graceful degradation patterns across services"""
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.fallback_handlers: Dict[str, Callable] = {}
        self.degradation_configs: Dict[str, DegradationConfig] = {}
        self.service_metrics: Dict[str, Dict[str, Any]] = {}
    
    def register_service(self, 
                        service_name: str, 
                        config: Optional[DegradationConfig] = None,
                        fallback_handler: Optional[Callable] = None):
        """Register a service for degradation management"""
        self.degradation_configs[service_name] = config or DegradationConfig()
        self.circuit_breakers[service_name] = CircuitBreaker(
            threshold=config.circuit_breaker_threshold if config else 5,
            timeout=config.circuit_breaker_timeout if config else 60.0
        )
        
        if fallback_handler:
            self.fallback_handlers[service_name] = fallback_handler
        
        self.service_metrics[service_name] = {
            'total_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'degraded_calls': 0,
            'last_success': None,
            'last_failure': None
        }
        
        logger.info(f"Registered service '{service_name}' for degradation management")
    
    def call_with_degradation(self, 
                             service_name: str, 
                             operation: Callable[..., T],
                             *args,
                             **kwargs) -> Optional[T]:
        """
        Call service operation with full degradation protection.
        
        Implements retry logic, circuit breaker, and fallback handling.
        """
        if service_name not in self.degradation_configs:
            # Service not registered - call directly
            return operation(*args, **kwargs)
        
        config = self.degradation_configs[service_name]
        circuit_breaker = self.circuit_breakers[service_name]
        metrics = self.service_metrics[service_name]
        
        metrics['total_calls'] += 1
        
        # Try primary operation with circuit breaker
        for attempt in range(config.max_retries + 1):
            try:
                result = circuit_breaker.call(operation, *args, **kwargs)
                
                if result is not None:
                    metrics['successful_calls'] += 1
                    metrics['last_success'] = time.time()
                    
                    if config.log_degradation and attempt > 0:
                        logger.info(f"Service '{service_name}' recovered after {attempt} retries")
                    
                    return result
                
                # Circuit breaker is open
                break
                
            except Exception as e:
                metrics['failed_calls'] += 1
                metrics['last_failure'] = time.time()
                
                if attempt < config.max_retries:
                    logger.debug(f"Retry {attempt + 1}/{config.max_retries} for {service_name}: {e}")
                    time.sleep(config.retry_delay * (attempt + 1))  # Exponential backoff
                else:
                    logger.warning(f"Service '{service_name}' failed after {config.max_retries} retries: {e}")
        
        # Primary operation failed - try fallback
        if config.fallback_enabled and service_name in self.fallback_handlers:
            try:
                fallback_result = self.fallback_handlers[service_name](*args, **kwargs)
                metrics['degraded_calls'] += 1
                
                if config.log_degradation:
                    logger.info(f"Using fallback for service '{service_name}'")
                
                return fallback_result
                
            except Exception as e:
                logger.error(f"Fallback failed for service '{service_name}': {e}")
        
        # All options exhausted
        if config.log_degradation:
            logger.warning(f"Service '{service_name}' completely unavailable")
        
        return None
    
    def get_service_health(self, service_name: str) -> Dict[str, Any]:
        """Get health metrics for a specific service"""
        if service_name not in self.service_metrics:
            return {'error': 'Service not registered'}
        
        metrics = self.service_metrics[service_name]
        circuit_breaker = self.circuit_breakers[service_name]
        
        total_calls = metrics['total_calls']
        success_rate = (metrics['successful_calls'] / total_calls) if total_calls > 0 else 0
        degradation_rate = (metrics['degraded_calls'] / total_calls) if total_calls > 0 else 0
        
        return {
            'service_name': service_name,
            'circuit_breaker_state': circuit_breaker.state,
            'success_rate': success_rate,
            'degradation_rate': degradation_rate,
            'total_calls': total_calls,
            'successful_calls': metrics['successful_calls'],
            'failed_calls': metrics['failed_calls'],
            'degraded_calls': metrics['degraded_calls'],
            'last_success': metrics['last_success'],
            'last_failure': metrics['last_failure'],
            'has_fallback': service_name in self.fallback_handlers
        }
    
    def get_overall_health(self) -> Dict[str, Any]:
        """Get overall system health considering degradation"""
        services_health = {}
        total_success_rate = 0
        total_degradation_rate = 0
        healthy_services = 0
        degraded_services = 0
        failed_services = 0
        
        for service_name in self.service_metrics:
            health = self.get_service_health(service_name)
            services_health[service_name] = health
            
            success_rate = health['success_rate']
            degradation_rate = health['degradation_rate']
            
            total_success_rate += success_rate
            total_degradation_rate += degradation_rate
            
            if success_rate > 0.9:
                healthy_services += 1
            elif success_rate > 0.5 or degradation_rate > 0:
                degraded_services += 1
            else:
                failed_services += 1
        
        total_services = len(self.service_metrics)
        
        if total_services > 0:
            avg_success_rate = total_success_rate / total_services
            avg_degradation_rate = total_degradation_rate / total_services
        else:
            avg_success_rate = 0
            avg_degradation_rate = 0
        
        # Determine overall status
        if failed_services == 0 and degraded_services == 0:
            overall_status = 'healthy'
        elif failed_services < total_services / 2:
            overall_status = 'degraded'
        else:
            overall_status = 'unhealthy'
        
        return {
            'overall_status': overall_status,
            'average_success_rate': avg_success_rate,
            'average_degradation_rate': avg_degradation_rate,
            'healthy_services': healthy_services,
            'degraded_services': degraded_services,
            'failed_services': failed_services,
            'total_services': total_services,
            'services': services_health,
            'timestamp': time.time()
        }


# Global degradation manager instance
degradation_manager = ServiceDegradationManager()


def with_degradation(service_name: str, 
                    config: Optional[DegradationConfig] = None,
                    fallback: Optional[Callable] = None):
    """
    Decorator for adding degradation protection to service methods.
    
    Usage:
        @with_degradation('ai_service', fallback=ai_fallback)
        async def generate_code(prompt: str):
            # Service implementation
            pass
    """
    def decorator(func: Callable[..., T]) -> Callable[..., Optional[T]]:
        # Register service if not already registered
        if service_name not in degradation_manager.degradation_configs:
            degradation_manager.register_service(service_name, config, fallback)
        
        @wraps(func)
        def wrapper(*args, **kwargs) -> Optional[T]:
            return degradation_manager.call_with_degradation(
                service_name, func, *args, **kwargs
            )
        
        return wrapper
    return decorator


# Common fallback implementations
class FallbackHandlers:
    """Common fallback handlers for different service types"""
    
    @staticmethod
    def ai_service_fallback(*args, **kwargs) -> Dict[str, Any]:
        """Fallback for AI service failures"""
        return {
            'generated_text': "// AI service temporarily unavailable - please try again later",
            'fallback': True,
            'service': 'ai_fallback'
        }
    
    @staticmethod
    def vector_search_fallback(query: str, *args, **kwargs) -> List[Dict[str, Any]]:
        """Fallback for vector search failures"""
        return [{
            'content': f"// Vector search unavailable for query: {query}",
            'similarity_score': 0.0,
            'fallback': True,
            'service': 'vector_fallback'
        }]
    
    @staticmethod
    def graph_analysis_fallback(*args, **kwargs) -> Dict[str, Any]:
        """Fallback for graph analysis failures"""
        return {
            'dependencies': [],
            'impact_analysis': {
                'risk_level': 'unknown',
                'message': 'Graph analysis unavailable'
            },
            'fallback': True,
            'service': 'graph_fallback'
        }
    
    @staticmethod
    def project_indexing_fallback(*args, **kwargs) -> Dict[str, Any]:
        """Fallback for project indexing failures"""
        return {
            'indexed_files': 0,
            'symbols': [],
            'status': 'degraded - indexing unavailable',
            'fallback': True,
            'service': 'project_fallback'
        }


# Utility functions for checking degradation status
def is_service_healthy(service_name: str) -> bool:
    """Check if a service is operating normally (not degraded)"""
    health = degradation_manager.get_service_health(service_name)
    return health.get('success_rate', 0) > 0.9 and health.get('degradation_rate', 0) < 0.1


def is_service_degraded(service_name: str) -> bool:
    """Check if a service is operating in degraded mode"""
    health = degradation_manager.get_service_health(service_name)
    return health.get('degradation_rate', 0) > 0 or (0.5 < health.get('success_rate', 0) <= 0.9)


def is_service_failed(service_name: str) -> bool:
    """Check if a service has completely failed"""
    health = degradation_manager.get_service_health(service_name)
    return health.get('success_rate', 0) <= 0.5 and health.get('degradation_rate', 0) == 0


def get_degradation_summary() -> Dict[str, Any]:
    """Get a summary of current degradation status across all services"""
    return degradation_manager.get_overall_health()