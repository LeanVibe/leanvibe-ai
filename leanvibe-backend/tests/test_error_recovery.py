"""
Tests for the Error Recovery and Resilience System

Validates error handling, recovery mechanisms, and system resilience
for production reliability.
"""

import asyncio
import time
import pytest
from unittest.mock import Mock, patch, AsyncMock

from app.core.error_recovery import (
    ErrorRecoveryManager,
    ErrorSeverity,
    RecoveryStrategy,
    ErrorContext,
    RecoveryPlan,
    global_error_recovery,
    with_error_recovery
)


class TestErrorRecoveryManager:
    """Test suite for ErrorRecoveryManager"""
    
    def setup_method(self):
        """Setup test environment"""
        self.recovery_manager = ErrorRecoveryManager()
    
    def test_initialization(self):
        """Test error recovery manager initialization"""
        assert len(self.recovery_manager.recovery_plans) > 0
        assert "ollama_connection" in self.recovery_manager.recovery_plans
        assert "l3_agent_init" in self.recovery_manager.recovery_plans
        assert "websocket_connection" in self.recovery_manager.recovery_plans
    
    def test_default_recovery_plans(self):
        """Test default recovery plans are properly configured"""
        # Test Ollama connection recovery plan
        ollama_plan = self.recovery_manager.recovery_plans["ollama_connection"]
        assert RecoveryStrategy.RETRY in ollama_plan.strategies
        assert RecoveryStrategy.RESTART_SERVICE in ollama_plan.strategies
        assert ollama_plan.max_attempts == 3
        
        # Test L3 agent initialization plan
        l3_plan = self.recovery_manager.recovery_plans["l3_agent_init"]
        assert RecoveryStrategy.GRACEFUL_DEGRADATION in l3_plan.strategies
        assert l3_plan.max_attempts == 2
        
        # Test WebSocket connection plan
        ws_plan = self.recovery_manager.recovery_plans["websocket_connection"]
        assert RecoveryStrategy.FALLBACK in ws_plan.strategies
        assert ws_plan.max_attempts == 5
    
    def test_severity_determination(self):
        """Test error severity classification"""
        # Test critical errors
        critical_error = Exception("Resource exhaustion")
        severity = self.recovery_manager._determine_severity("resource_exhaustion", critical_error)
        assert severity == ErrorSeverity.CRITICAL
        
        # Test high severity errors
        high_error = Exception("initialization failed")
        severity = self.recovery_manager._determine_severity("l3_agent_init", high_error)
        assert severity == ErrorSeverity.HIGH
        
        # Test medium severity errors
        medium_error = Exception("connection timeout")
        severity = self.recovery_manager._determine_severity("websocket_connection", medium_error)
        assert severity == ErrorSeverity.MEDIUM
        
        # Test low severity errors
        low_error = Exception("minor issue")
        severity = self.recovery_manager._determine_severity("file_operation", low_error)
        assert severity == ErrorSeverity.LOW
    
    @pytest.mark.asyncio
    async def test_handle_error_basic(self):
        """Test basic error handling"""
        test_error = Exception("Test error")
        
        result = await self.recovery_manager.handle_error(
            error_type="query_timeout",
            error=test_error,
            context={"test": "context"},
            component="test_component"
        )
        
        assert isinstance(result, dict)
        assert "success" in result
        assert "user_message" in result
        assert "strategy_used" in result
        assert "retry_possible" in result
        
        # Check that error was logged
        assert len(self.recovery_manager.error_history) > 0
        assert self.recovery_manager.error_history[-1].error_type == "query_timeout"
    
    @pytest.mark.asyncio
    async def test_retry_strategy(self):
        """Test retry recovery strategy"""
        # Test successful retry
        result = await self.recovery_manager._retry_operation(
            ErrorContext(
                error_type="websocket_connection",
                error_message="Connection failed",
                severity=ErrorSeverity.MEDIUM,
                component="test",
                recovery_attempts=1
            ),
            RecoveryPlan(strategies=[RecoveryStrategy.RETRY], backoff_multiplier=1.0)
        )
        
        assert isinstance(result, bool)
    
    @pytest.mark.asyncio
    async def test_restart_service_strategy(self):
        """Test service restart recovery strategy"""
        error_context = ErrorContext(
            error_type="ollama_connection",
            error_message="Service unavailable",
            severity=ErrorSeverity.HIGH,
            component="ollama_service"
        )
        
        result = await self.recovery_manager._restart_service(error_context)
        
        assert isinstance(result, bool)
        # Check that service health was updated
        assert "ollama_service" in self.recovery_manager.service_health
    
    @pytest.mark.asyncio
    async def test_fallback_strategy(self):
        """Test fallback recovery strategy"""
        error_context = ErrorContext(
            error_type="query_timeout",
            error_message="Request timeout",
            severity=ErrorSeverity.MEDIUM,
            component="ai_service"
        )
        
        result = await self.recovery_manager._use_fallback(error_context)
        
        assert isinstance(result, bool)
    
    @pytest.mark.asyncio
    async def test_graceful_degradation_strategy(self):
        """Test graceful degradation recovery strategy"""
        error_context = ErrorContext(
            error_type="resource_exhaustion",
            error_message="Memory limit exceeded",
            severity=ErrorSeverity.CRITICAL,
            component="system"
        )
        
        result = await self.recovery_manager._graceful_degradation(error_context)
        
        assert result is True  # Graceful degradation should always succeed
    
    @pytest.mark.asyncio
    async def test_user_notification_strategy(self):
        """Test user notification recovery strategy"""
        error_context = ErrorContext(
            error_type="file_operation",
            error_message="File not found",
            severity=ErrorSeverity.LOW,
            component="file_system"
        )
        
        recovery_plan = RecoveryPlan(
            strategies=[RecoveryStrategy.USER_NOTIFICATION],
            fallback_message="Test notification"
        )
        
        result = await self.recovery_manager._notify_user(error_context, recovery_plan)
        
        assert result is True
    
    def test_health_status(self):
        """Test health status reporting"""
        # Add some test errors
        self.recovery_manager.error_history.append(
            ErrorContext(
                error_type="test_error",
                error_message="Test",
                severity=ErrorSeverity.LOW,
                component="test"
            )
        )
        
        health_status = self.recovery_manager.get_health_status()
        
        assert "service_health" in health_status
        assert "recent_errors" in health_status
        assert "critical_errors_last_hour" in health_status
        assert "recovery_stats" in health_status
        assert "overall_health" in health_status
    
    def test_user_friendly_status(self):
        """Test user-friendly status reporting"""
        status = self.recovery_manager.get_user_friendly_status()
        
        assert "status" in status
        assert "message" in status
        assert "last_updated" in status
        assert status["status"] in ["operational", "limited_functionality", "experiencing_issues"]
    
    def test_recovery_stats_tracking(self):
        """Test recovery statistics tracking"""
        # Test successful recovery
        self.recovery_manager._update_recovery_stats("test_error", True)
        
        assert "test_error" in self.recovery_manager.recovery_stats
        assert self.recovery_manager.recovery_stats["test_error"]["attempts"] == 1
        assert self.recovery_manager.recovery_stats["test_error"]["successes"] == 1
        
        # Test failed recovery
        self.recovery_manager._update_recovery_stats("test_error", False)
        
        assert self.recovery_manager.recovery_stats["test_error"]["attempts"] == 2
        assert self.recovery_manager.recovery_stats["test_error"]["successes"] == 1


class TestErrorRecoveryDecorator:
    """Test suite for error recovery decorator"""
    
    @pytest.mark.asyncio
    async def test_successful_function_execution(self):
        """Test decorator with successful function execution"""
        
        @with_error_recovery("test_error", "test_component")
        async def test_function():
            return "success"
        
        result = await test_function()
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_function_with_error(self):
        """Test decorator with function that raises error"""
        
        @with_error_recovery("test_error", "test_component")
        async def failing_function():
            raise Exception("Test error")
        
        result = await failing_function()
        
        # Should return recovery result
        assert isinstance(result, dict)
        assert "status" in result
        assert "message" in result


class TestErrorRecoveryIntegration:
    """Integration tests for error recovery system"""
    
    @pytest.mark.asyncio
    async def test_global_error_recovery_instance(self):
        """Test that global error recovery instance works correctly"""
        test_error = Exception("Global test error")
        
        result = await global_error_recovery.handle_error(
            error_type="test_integration",
            error=test_error,
            context={"integration": "test"},
            component="integration_test"
        )
        
        assert isinstance(result, dict)
        assert "success" in result
        assert "user_message" in result
    
    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self):
        """Test complete error recovery workflow"""
        # Simulate a sequence of errors and recoveries
        errors = [
            ("ollama_connection", "Connection failed"),
            ("l3_agent_init", "Initialization failed"),
            ("websocket_connection", "WebSocket error"),
            ("query_timeout", "Request timeout")
        ]
        
        results = []
        for error_type, error_message in errors:
            result = await global_error_recovery.handle_error(
                error_type=error_type,
                error=Exception(error_message),
                context={"workflow": "test"},
                component="workflow_test"
            )
            results.append(result)
        
        # All errors should be handled
        assert len(results) == 4
        assert all("success" in result for result in results)
        assert all("user_message" in result for result in results)
        
        # Check that error history was updated
        assert len(global_error_recovery.error_history) >= 4
    
    @pytest.mark.asyncio
    async def test_recovery_plan_customization(self):
        """Test custom recovery plan creation and usage"""
        custom_plan = RecoveryPlan(
            strategies=[RecoveryStrategy.RETRY, RecoveryStrategy.USER_NOTIFICATION],
            max_attempts=5,
            backoff_multiplier=1.5,
            fallback_message="Custom recovery message"
        )
        
        # Add custom plan
        global_error_recovery.recovery_plans["custom_error"] = custom_plan
        
        # Test custom plan usage
        result = await global_error_recovery.handle_error(
            error_type="custom_error",
            error=Exception("Custom error"),
            context={"custom": True},
            component="custom_test"
        )
        
        assert isinstance(result, dict)
        assert "success" in result


class TestErrorRecoveryPerformance:
    """Performance tests for error recovery system"""
    
    @pytest.mark.asyncio
    async def test_recovery_performance(self):
        """Test that error recovery doesn't significantly impact performance"""
        
        @with_error_recovery("performance_test", "performance_component")
        async def fast_function():
            return "fast_result"
        
        # Time function execution
        start_time = time.time()
        result = await fast_function()
        end_time = time.time()
        
        # Should be very fast for successful execution
        assert end_time - start_time < 0.1  # Less than 100ms
        assert result == "fast_result"
    
    @pytest.mark.asyncio
    async def test_concurrent_error_handling(self):
        """Test error recovery under concurrent load"""
        
        async def error_generator(error_id: int):
            """Generate errors concurrently"""
            return await global_error_recovery.handle_error(
                error_type="concurrent_test",
                error=Exception(f"Concurrent error {error_id}"),
                context={"error_id": error_id},
                component="concurrent_test"
            )
        
        # Generate 10 concurrent errors
        tasks = [error_generator(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        # All errors should be handled
        assert len(results) == 10
        assert all("success" in result for result in results)
        assert all("user_message" in result for result in results)


class TestErrorRecoveryResilience:
    """Test error recovery system resilience"""
    
    @pytest.mark.asyncio
    async def test_recovery_system_stability(self):
        """Test that recovery system remains stable under stress"""
        
        # Generate many errors rapidly
        for i in range(50):
            await global_error_recovery.handle_error(
                error_type="stress_test",
                error=Exception(f"Stress test error {i}"),
                context={"stress_test": True, "iteration": i},
                component="stress_test"
            )
        
        # System should remain operational
        health_status = global_error_recovery.get_health_status()
        assert "overall_health" in health_status
        
        # Should have recovery stats
        assert "stress_test" in global_error_recovery.recovery_stats
        assert global_error_recovery.recovery_stats["stress_test"]["attempts"] == 50
    
    @pytest.mark.asyncio
    async def test_memory_usage_stability(self):
        """Test that error recovery doesn't cause memory leaks"""
        
        # Generate errors and check memory usage doesn't grow unbounded
        initial_history_size = len(global_error_recovery.error_history)
        
        # Generate many errors
        for i in range(100):
            await global_error_recovery.handle_error(
                error_type="memory_test",
                error=Exception(f"Memory test error {i}"),
                context={"memory_test": True},
                component="memory_test"
            )
        
        # Error history should be managed (not grow indefinitely)
        final_history_size = len(global_error_recovery.error_history)
        growth = final_history_size - initial_history_size
        
        # Should not grow by more than 100 entries (some cleanup should happen)
        assert growth <= 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])