"""
Simple circuit breaker for production stability.
Following YAGNI - just enough to prevent cascade failures.
"""

import asyncio
import time
from typing import Any, Callable, Optional
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """
    Simple circuit breaker to prevent cascade failures.
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, requests fail fast
    - HALF_OPEN: Testing if service recovered
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        timeout: float = 30.0,
        recovery_timeout: float = 60.0
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.recovery_timeout = recovery_timeout
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        # Check if circuit should be reset
        if self.state == "OPEN":
            if self.last_failure_time and \
               time.time() - self.last_failure_time > self.recovery_timeout:
                logger.info(f"Circuit breaker {self.name}: attempting recovery")
                self.state = "HALF_OPEN"
                self.failure_count = 0
        
        # If circuit is open, fail fast
        if self.state == "OPEN":
            logger.warning(f"Circuit breaker {self.name}: failing fast (circuit open)")
            raise Exception(f"Circuit breaker {self.name} is OPEN - service unavailable")
        
        try:
            # Execute with timeout
            result = func(*args, **kwargs)
            
            # Success - reset failure count
            if self.state == "HALF_OPEN":
                logger.info(f"Circuit breaker {self.name}: recovered successfully")
                self.state = "CLOSED"
            self.failure_count = 0
            
            return result
            
        except Exception as e:
            # Record failure
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            # Check if we should open the circuit
            if self.failure_count >= self.failure_threshold:
                logger.error(f"Circuit breaker {self.name}: opening circuit after {self.failure_count} failures")
                self.state = "OPEN"
            
            raise e
    
    async def async_call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute async function with circuit breaker protection"""
        # Check if circuit should be reset
        if self.state == "OPEN":
            if self.last_failure_time and \
               time.time() - self.last_failure_time > self.recovery_timeout:
                logger.info(f"Circuit breaker {self.name}: attempting recovery")
                self.state = "HALF_OPEN"
                self.failure_count = 0
        
        # If circuit is open, fail fast
        if self.state == "OPEN":
            logger.warning(f"Circuit breaker {self.name}: failing fast (circuit open)")
            raise Exception(f"Circuit breaker {self.name} is OPEN - service unavailable")
        
        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=self.timeout
            )
            
            # Success - reset failure count
            if self.state == "HALF_OPEN":
                logger.info(f"Circuit breaker {self.name}: recovered successfully")
                self.state = "CLOSED"
            self.failure_count = 0
            
            return result
            
        except asyncio.TimeoutError:
            # Convert to regular exception for consistency
            logger.warning(f"Circuit breaker {self.name}: timeout after {self.timeout}s")
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                logger.error(f"Circuit breaker {self.name}: opening circuit after {self.failure_count} failures")
                self.state = "OPEN"
            
            raise Exception(f"Operation timed out after {self.timeout} seconds")
            
        except Exception as e:
            # Record failure
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            # Check if we should open the circuit
            if self.failure_count >= self.failure_threshold:
                logger.error(f"Circuit breaker {self.name}: opening circuit after {self.failure_count} failures")
                self.state = "OPEN"
            
            raise e


# Global circuit breakers for critical services
ai_circuit_breaker = CircuitBreaker(
    name="AI_Service",
    failure_threshold=3,
    timeout=30.0,
    recovery_timeout=60.0
)

database_circuit_breaker = CircuitBreaker(
    name="Database",
    failure_threshold=5,
    timeout=10.0,
    recovery_timeout=30.0
)

external_api_circuit_breaker = CircuitBreaker(
    name="External_API",
    failure_threshold=3,
    timeout=15.0,
    recovery_timeout=60.0
)


def with_circuit_breaker(breaker: CircuitBreaker):
    """Decorator to apply circuit breaker to a function"""
    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await breaker.async_call(func, *args, **kwargs)
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                return breaker.call(func, *args, **kwargs)
            return sync_wrapper
    return decorator


# Fallback responses for when circuit is open
class FallbackResponses:
    """Simple fallback responses for when services are down"""
    
    @staticmethod
    def ai_fallback():
        """Fallback response for AI service"""
        return {
            "response": "AI service is temporarily unavailable. Please try again later.",
            "confidence": 0.0,
            "fallback": True
        }
    
    @staticmethod
    def database_fallback():
        """Fallback response for database"""
        return {
            "data": [],
            "error": "Database temporarily unavailable",
            "fallback": True
        }
    
    @staticmethod
    def generic_fallback(service_name: str):
        """Generic fallback response"""
        return {
            "error": f"{service_name} is temporarily unavailable",
            "fallback": True,
            "retry_after": 60
        }