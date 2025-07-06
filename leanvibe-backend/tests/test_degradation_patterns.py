"""
Tests for graceful service degradation patterns

Validates that the degradation manager correctly handles service failures,
implements circuit breakers, retries, and fallback mechanisms.
"""

import asyncio
import logging
import sys
import os
import time
from unittest.mock import Mock, AsyncMock

import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.degradation_patterns import (
    CircuitBreaker,
    ServiceDegradationManager,
    DegradationConfig,
    FallbackHandlers,
    with_degradation,
    degradation_manager
)

logger = logging.getLogger(__name__)


class TestCircuitBreaker:
    """Test circuit breaker functionality"""
    
    def test_circuit_breaker_closed_state(self):
        """Test circuit breaker in closed state"""
        circuit_breaker = CircuitBreaker(threshold=3, timeout=1.0)
        
        # Function that always succeeds
        def success_func():
            return "success"
        
        # Should work normally in closed state
        result = circuit_breaker.call(success_func)
        assert result == "success"
        assert circuit_breaker.state == 'CLOSED'
        assert circuit_breaker.failure_count == 0
    
    def test_circuit_breaker_failure_tracking(self):
        """Test that circuit breaker tracks failures correctly"""
        circuit_breaker = CircuitBreaker(threshold=3, timeout=1.0)
        
        # Function that always fails
        def fail_func():
            raise Exception("Test failure")
        
        # Try a few failures
        for i in range(2):
            try:
                circuit_breaker.call(fail_func)
            except Exception:
                pass
        
        assert circuit_breaker.state == 'CLOSED'  # Should still be closed
        assert circuit_breaker.failure_count == 2
        
        # One more failure should open the circuit
        try:
            circuit_breaker.call(fail_func)
        except Exception:
            pass
        
        assert circuit_breaker.state == 'OPEN'
        assert circuit_breaker.failure_count == 3
    
    def test_circuit_breaker_open_state(self):
        """Test circuit breaker in open state"""
        circuit_breaker = CircuitBreaker(threshold=2, timeout=0.1)
        
        # Force circuit to open
        def fail_func():
            raise Exception("Test failure")
        
        for i in range(2):
            try:
                circuit_breaker.call(fail_func)
            except Exception:
                pass
        
        assert circuit_breaker.state == 'OPEN'
        
        # Now calls should return None without executing function
        def success_func():
            return "should not execute"
        
        result = circuit_breaker.call(success_func)
        assert result is None
    
    def test_circuit_breaker_half_open_recovery(self):
        """Test circuit breaker recovery through half-open state"""
        circuit_breaker = CircuitBreaker(threshold=2, timeout=0.1)
        
        # Force circuit to open
        def fail_func():
            raise Exception("Test failure")
        
        for i in range(2):
            try:
                circuit_breaker.call(fail_func)
            except Exception:
                pass
        
        assert circuit_breaker.state == 'OPEN'
        
        # Wait for timeout
        time.sleep(0.2)
        
        # Next call should try half-open
        def success_func():
            return "recovery"
        
        result = circuit_breaker.call(success_func)
        assert result == "recovery"
        assert circuit_breaker.state == 'CLOSED'
        assert circuit_breaker.failure_count == 0


@pytest.mark.asyncio
class TestServiceDegradationManager:
    """Test service degradation manager"""
    
    def test_service_registration(self):
        """Test service registration with degradation manager"""
        manager = ServiceDegradationManager()
        
        config = DegradationConfig(max_retries=2, retry_delay=0.1)
        fallback = lambda: "fallback_result"
        
        manager.register_service('test_service', config, fallback)
        
        assert 'test_service' in manager.degradation_configs
        assert 'test_service' in manager.circuit_breakers
        assert 'test_service' in manager.fallback_handlers
        assert 'test_service' in manager.service_metrics
        
        assert manager.degradation_configs['test_service'] == config
        assert manager.fallback_handlers['test_service'] == fallback
    
    def test_successful_operation(self):
        """Test successful service operation"""
        manager = ServiceDegradationManager()
        config = DegradationConfig(max_retries=2, retry_delay=0.1)
        
        manager.register_service('test_service', config)
        
        def success_operation():
            return "success"
        
        result = manager.call_with_degradation('test_service', success_operation)
        
        assert result == "success"
        
        # Check metrics
        metrics = manager.service_metrics['test_service']
        assert metrics['total_calls'] == 1
        assert metrics['successful_calls'] == 1
        assert metrics['failed_calls'] == 0
        assert metrics['degraded_calls'] == 0
    
    def test_operation_with_retries(self):
        """Test operation that succeeds after retries"""
        manager = ServiceDegradationManager()
        config = DegradationConfig(max_retries=2, retry_delay=0.01)  # Fast retry for testing
        
        manager.register_service('test_service', config)
        
        # Mock function that fails twice then succeeds
        call_count = 0
        def flaky_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "success_after_retries"
        
        result = manager.call_with_degradation('test_service', flaky_operation)
        
        assert result == "success_after_retries"
        assert call_count == 3  # Failed twice, succeeded on third try
        
        # Check metrics
        metrics = manager.service_metrics['test_service']
        assert metrics['total_calls'] == 1
        assert metrics['successful_calls'] == 1
    
    def test_fallback_activation(self):
        """Test fallback when primary operation fails"""
        manager = ServiceDegradationManager()
        config = DegradationConfig(max_retries=1, retry_delay=0.01, fallback_enabled=True)
        
        def fallback_func():
            return "fallback_result"
        
        manager.register_service('test_service', config, fallback_func)
        
        def failing_operation():
            raise Exception("Always fails")
        
        result = manager.call_with_degradation('test_service', failing_operation)
        
        assert result == "fallback_result"
        
        # Check metrics
        metrics = manager.service_metrics['test_service']
        assert metrics['total_calls'] == 1
        assert metrics['failed_calls'] == 2  # Original + retry
        assert metrics['degraded_calls'] == 1
    
    def test_complete_failure(self):
        """Test complete failure when no fallback available"""
        manager = ServiceDegradationManager()
        config = DegradationConfig(max_retries=1, retry_delay=0.01, fallback_enabled=False)
        
        manager.register_service('test_service', config)
        
        def failing_operation():
            raise Exception("Always fails")
        
        result = manager.call_with_degradation('test_service', failing_operation)
        
        assert result is None
        
        # Check metrics
        metrics = manager.service_metrics['test_service']
        assert metrics['total_calls'] == 1
        assert metrics['failed_calls'] == 2  # Original + retry
        assert metrics['degraded_calls'] == 0
    
    def test_service_health_metrics(self):
        """Test service health metric calculation"""
        manager = ServiceDegradationManager()
        config = DegradationConfig(max_retries=1, retry_delay=0.01)
        
        def fallback_func():
            return "fallback"
        
        manager.register_service('test_service', config, fallback_func)
        
        # Simulate some operations
        def success_op():
            return "success"
        
        def fail_op():
            raise Exception("fail")
        
        # 3 successes, 2 failures (with fallback)
        for _ in range(3):
            manager.call_with_degradation('test_service', success_op)
        
        for _ in range(2):
            manager.call_with_degradation('test_service', fail_op)
        
        health = manager.get_service_health('test_service')
        
        assert health['service_name'] == 'test_service'
        assert health['total_calls'] == 5
        assert health['successful_calls'] == 3
        assert health['degraded_calls'] == 2
        assert health['success_rate'] == 0.6  # 3/5
        assert health['degradation_rate'] == 0.4  # 2/5
        assert health['has_fallback'] is True
    
    def test_overall_health_assessment(self):
        """Test overall system health assessment"""
        manager = ServiceDegradationManager()
        
        # Register multiple services
        config = DegradationConfig(max_retries=1, retry_delay=0.01)
        
        manager.register_service('healthy_service', config)
        manager.register_service('degraded_service', config, lambda: "fallback")
        manager.register_service('failed_service', config)
        
        # Simulate different service states
        
        # Healthy service - all successes
        for _ in range(5):
            manager.call_with_degradation('healthy_service', lambda: "success")
        
        # Degraded service - some failures with fallback
        for _ in range(3):
            manager.call_with_degradation('degraded_service', lambda: "success")
        for _ in range(2):
            manager.call_with_degradation('degraded_service', lambda: (_ for _ in ()).throw(Exception("fail")))
        
        # Failed service - all failures
        for _ in range(3):
            manager.call_with_degradation('failed_service', lambda: (_ for _ in ()).throw(Exception("fail")))
        
        overall_health = manager.get_overall_health()
        
        assert overall_health['total_services'] == 3
        assert overall_health['healthy_services'] == 1
        assert overall_health['degraded_services'] == 1
        assert overall_health['failed_services'] == 1
        assert overall_health['overall_status'] == 'degraded'  # Mixed state


class TestFallbackHandlers:
    """Test built-in fallback handlers"""
    
    def test_ai_service_fallback(self):
        """Test AI service fallback handler"""
        result = FallbackHandlers.ai_service_fallback("test prompt")
        
        assert 'generated_text' in result
        assert 'fallback' in result
        assert result['fallback'] is True
        assert result['service'] == 'ai_fallback'
        assert 'unavailable' in result['generated_text']
    
    def test_vector_search_fallback(self):
        """Test vector search fallback handler"""
        result = FallbackHandlers.vector_search_fallback("test query")
        
        assert isinstance(result, list)
        assert len(result) == 1
        
        item = result[0]
        assert 'content' in item
        assert 'similarity_score' in item
        assert 'fallback' in item
        assert item['fallback'] is True
        assert item['service'] == 'vector_fallback'
        assert 'test query' in item['content']
    
    def test_graph_analysis_fallback(self):
        """Test graph analysis fallback handler"""
        result = FallbackHandlers.graph_analysis_fallback("test target")
        
        assert 'dependencies' in result
        assert 'impact_analysis' in result
        assert 'fallback' in result
        assert result['fallback'] is True
        assert result['service'] == 'graph_fallback'
        assert result['impact_analysis']['risk_level'] == 'unknown'


class TestDegradationDecorator:
    """Test the @with_degradation decorator"""
    
    def test_decorator_registration(self):
        """Test that decorator registers service automatically"""
        config = DegradationConfig(max_retries=1)
        
        @with_degradation('decorator_test', config=config)
        def test_function():
            return "decorated"
        
        assert 'decorator_test' in degradation_manager.degradation_configs
        
        result = test_function()
        assert result == "decorated"
    
    def test_decorator_with_fallback(self):
        """Test decorator with fallback function"""
        def fallback_func():
            return "fallback_from_decorator"
        
        @with_degradation('decorator_fallback_test', fallback=fallback_func)
        def failing_function():
            raise Exception("Always fails")
        
        result = failing_function()
        assert result == "fallback_from_decorator"


if __name__ == "__main__":
    # Allow running this test file directly
    import subprocess
    
    print("🧪 Running degradation patterns tests...")
    
    result = subprocess.run([
        sys.executable, "-m", "pytest",
        __file__,
        "-v",
        "--tb=short",
        "-s"  # Show print statements
    ])
    
    sys.exit(result.returncode)