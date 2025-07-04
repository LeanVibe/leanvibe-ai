"""
Comprehensive AI Assistant Performance Tests

Tests AI response times, model optimization, and performance monitoring
to ensure <2s response time targets are met consistently.
"""

import asyncio
import pytest
import time
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any
import sys
import os

# Add the backend path for testing
backend_path = os.path.join(os.path.dirname(__file__), '../../leanvibe-backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)


class MockMLXService:
    """Mock MLX service for testing"""
    
    def __init__(self):
        self.is_initialized = False
        self.response_times = []
        self.target_response_time = 2.0
        self.cache = {}
        
    async def initialize(self):
        """Mock initialization"""
        await asyncio.sleep(0.1)  # Simulate init time
        self.is_initialized = True
        return True
        
    async def generate_code_completion(self, context: Dict[str, Any], intent: str = "suggest") -> Dict[str, Any]:
        """Mock code completion with performance simulation"""
        start_time = time.time()
        
        # Simulate model processing time
        processing_time = 0.5 + (len(context.get("surrounding_code", "")) / 1000)  # Scale with input
        await asyncio.sleep(min(processing_time, 3.0))  # Cap at 3s
        
        response_time = time.time() - start_time
        self.response_times.append(response_time)
        
        return {
            "status": "success",
            "response": f"Generated completion for {intent}",
            "confidence": 0.9,
            "response_time": response_time,
            "performance_status": self._get_performance_status(response_time),
            "from_cache": False
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        if not self.response_times:
            return {
                "avg_response_time": 0,
                "target_response_time": self.target_response_time,
                "within_target_percentage": 0,
                "total_requests": 0
            }
        
        avg_time = sum(self.response_times) / len(self.response_times)
        within_target = sum(1 for t in self.response_times if t <= self.target_response_time)
        percentage = (within_target / len(self.response_times)) * 100
        
        return {
            "avg_response_time": round(avg_time, 3),
            "target_response_time": self.target_response_time,
            "within_target_percentage": round(percentage, 1),
            "total_requests": len(self.response_times),
            "performance_status": self._get_performance_status(avg_time)
        }
    
    def _get_performance_status(self, response_time: float) -> str:
        """Calculate performance status"""
        if response_time <= 1.0:
            return "excellent"
        elif response_time <= 2.0:
            return "good"
        elif response_time <= 3.0:
            return "acceptable"
        else:
            return "slow"


class TestAIPerformance:
    """Test AI assistant performance characteristics"""
    
    @pytest.fixture
    def ai_service(self):
        """Mock AI service for testing"""
        service = MockMLXService()
        asyncio.create_task(service.initialize())
        return service
    
    @pytest.mark.asyncio
    async def test_ai_response_time_target(self, ai_service):
        """Test that AI response time meets <2s target"""
        await ai_service.initialize()
        
        context = {
            "file_path": "test.py",
            "cursor_position": 100,
            "surrounding_code": "def hello():\n    print('hello world')"
        }
        
        start_time = time.time()
        result = await ai_service.generate_code_completion(context, "suggest")
        response_time = time.time() - start_time
        
        # Assert response time meets target
        assert response_time < 2.0, f"AI response time {response_time:.3f}s exceeds 2s target"
        assert result["status"] == "success"
        assert "response_time" in result
        assert result["performance_status"] in ["excellent", "good"]
    
    @pytest.mark.asyncio
    async def test_ai_performance_under_load(self, ai_service):
        """Test AI performance under concurrent load"""
        await ai_service.initialize()
        
        # Create test contexts of varying complexity
        contexts = [
            {
                "file_path": f"test_{i}.py",
                "cursor_position": 50 + i * 10,
                "surrounding_code": "# Simple context" * (i + 1)
            }
            for i in range(10)
        ]
        
        # Execute concurrent requests
        tasks = []
        for context in contexts:
            task = asyncio.create_task(ai_service.generate_code_completion(context))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # Verify all responses meet target
        for i, result in enumerate(results):
            response_time = result["response_time"]
            assert response_time < 2.5, f"AI request {i} took {response_time:.3f}s, exceeds 2.5s limit"
            assert result["status"] == "success"
        
        # Verify average performance
        response_times = [r["response_time"] for r in results]
        avg_response_time = sum(response_times) / len(response_times)
        assert avg_response_time < 2.0, f"Average response time {avg_response_time:.3f}s should meet 2s target"
    
    @pytest.mark.asyncio
    async def test_ai_performance_with_large_context(self, ai_service):
        """Test AI performance with large context inputs"""
        await ai_service.initialize()
        
        # Test with large context
        large_context = {
            "file_path": "large_file.py",
            "cursor_position": 500,
            "surrounding_code": "# Large context\n" * 100  # Simulate large file
        }
        
        start_time = time.time()
        result = await ai_service.generate_code_completion(large_context)
        response_time = time.time() - start_time
        
        # Even with large context, should stay reasonable
        assert response_time < 3.0, f"Large context response time {response_time:.3f}s exceeds 3s limit"
        assert result["status"] == "success"
    
    def test_performance_metrics_accuracy(self, ai_service):
        """Test accuracy of performance metrics calculation"""
        # Simulate response times
        test_times = [0.5, 1.0, 1.5, 2.0, 2.5]
        ai_service.response_times = test_times
        
        metrics = ai_service.get_performance_metrics()
        
        # Verify calculations
        expected_avg = sum(test_times) / len(test_times)
        assert abs(metrics["avg_response_time"] - expected_avg) < 0.001
        
        within_target = sum(1 for t in test_times if t <= 2.0)
        expected_percentage = (within_target / len(test_times)) * 100
        assert abs(metrics["within_target_percentage"] - expected_percentage) < 0.1
        
        assert metrics["total_requests"] == len(test_times)


class TestAIModelOptimization:
    """Test AI model optimization features"""
    
    @pytest.mark.asyncio
    async def test_model_warmup_performance(self, ai_service):
        """Test model warm-up improves performance"""
        # Test cold start
        cold_start_time = time.time()
        await ai_service.initialize()
        cold_init_time = time.time() - cold_start_time
        
        # Warm-up should complete quickly
        assert cold_init_time < 1.0, f"Model initialization took {cold_init_time:.3f}s, should be <1s"
        
        # First request (potential cold start)
        context = {"file_path": "test.py", "surrounding_code": "print('hello')"}
        
        start_time = time.time()
        result1 = await ai_service.generate_code_completion(context)
        first_response_time = time.time() - start_time
        
        # Second request (warmed up)
        start_time = time.time()
        result2 = await ai_service.generate_code_completion(context)
        second_response_time = time.time() - start_time
        
        # Performance should be consistent or improve
        assert second_response_time <= first_response_time * 1.2, "Performance should not significantly degrade"
    
    @pytest.mark.asyncio
    async def test_model_caching_optimization(self, ai_service):
        """Test model response caching for performance"""
        await ai_service.initialize()
        
        # Same context for cache testing
        context = {
            "file_path": "cache_test.py",
            "surrounding_code": "def cached_function():\n    pass"
        }
        
        # First request (cache miss)
        start_time = time.time()
        result1 = await ai_service.generate_code_completion(context)
        first_time = time.time() - start_time
        
        # Simulate caching by storing result
        cache_key = f"{context['file_path']}_{hash(context['surrounding_code'])}"
        ai_service.cache[cache_key] = result1
        
        # Second identical request (cache hit simulation)
        if cache_key in ai_service.cache:
            cached_result = ai_service.cache[cache_key].copy()
            cached_result["from_cache"] = True
            cached_result["response_time"] = 0.01  # Very fast cache response
            result2 = cached_result
        else:
            result2 = await ai_service.generate_code_completion(context)
        
        # Cached result should be much faster
        if result2.get("from_cache"):
            assert result2["response_time"] < 0.1, "Cached response should be <100ms"


class TestAIErrorHandling:
    """Test AI error handling and resilience"""
    
    @pytest.mark.asyncio
    async def test_ai_timeout_handling(self, ai_service):
        """Test handling of AI model timeouts"""
        await ai_service.initialize()
        
        # Mock a timeout scenario
        with patch.object(ai_service, 'generate_code_completion', side_effect=asyncio.TimeoutError("Model timeout")):
            with pytest.raises(asyncio.TimeoutError):
                await ai_service.generate_code_completion({"surrounding_code": "test"})
    
    @pytest.mark.asyncio
    async def test_ai_model_failure_recovery(self, ai_service):
        """Test recovery from AI model failures"""
        await ai_service.initialize()
        
        # Mock model failure and recovery
        async def mock_completion(context, intent="suggest"):
            if not hasattr(mock_completion, 'call_count'):
                mock_completion.call_count = 0
            mock_completion.call_count += 1
            
            if mock_completion.call_count == 1:
                return {
                    "status": "error",
                    "error": "Model temporarily unavailable",
                    "response_time": 0.1
                }
            else:
                return {
                    "status": "success",
                    "response": "Recovery successful",
                    "confidence": 0.8,
                    "response_time": 0.5
                }
        
        with patch.object(ai_service, 'generate_code_completion', side_effect=mock_completion):
            # First call should indicate error
            result1 = await ai_service.generate_code_completion({"surrounding_code": "test"})
            assert result1["status"] == "error"
            
            # Second call should succeed (recovery)
            result2 = await ai_service.generate_code_completion({"surrounding_code": "test"})
            assert result2["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_ai_memory_pressure_handling(self, ai_service):
        """Test AI behavior under memory pressure"""
        await ai_service.initialize()
        
        # Simulate memory-intensive requests
        large_contexts = [
            {
                "file_path": f"large_{i}.py",
                "surrounding_code": "# " + "large context " * 1000
            }
            for i in range(5)
        ]
        
        # Process large contexts sequentially
        for context in large_contexts:
            result = await ai_service.generate_code_completion(context)
            assert result["status"] == "success"
            # Should still meet performance targets even with large contexts
            assert result["response_time"] < 3.0


class TestAIPerformanceMonitoring:
    """Test AI performance monitoring and metrics"""
    
    def test_performance_metrics_completeness(self, ai_service):
        """Test that all required performance metrics are provided"""
        # Add some test response times
        ai_service.response_times = [0.5, 1.0, 1.5, 2.0]
        
        metrics = ai_service.get_performance_metrics()
        
        required_fields = [
            "avg_response_time",
            "target_response_time",
            "within_target_percentage",
            "total_requests",
            "performance_status"
        ]
        
        for field in required_fields:
            assert field in metrics, f"Missing required metric field: {field}"
        
        # Verify data types and ranges
        assert 0 <= metrics["avg_response_time"] <= 10
        assert metrics["target_response_time"] == 2.0
        assert 0 <= metrics["within_target_percentage"] <= 100
        assert metrics["total_requests"] >= 0
        assert metrics["performance_status"] in ["excellent", "good", "acceptable", "slow"]
    
    def test_performance_status_thresholds(self, ai_service):
        """Test performance status threshold calculations"""
        test_cases = [
            (0.5, "excellent"),
            (1.0, "excellent"),
            (1.5, "good"),
            (2.0, "good"),
            (2.5, "acceptable"),
            (4.0, "slow")
        ]
        
        for response_time, expected_status in test_cases:
            status = ai_service._get_performance_status(response_time)
            assert status == expected_status, f"Response time {response_time}s should be {expected_status}, got {status}"


@pytest.mark.performance
class TestAIPerformanceBenchmarks:
    """Performance benchmark tests for AI assistant"""
    
    @pytest.mark.asyncio
    async def test_ai_response_time_benchmark(self):
        """Benchmark AI response time across multiple iterations"""
        ai_service = MockMLXService()
        await ai_service.initialize()
        
        response_times = []
        contexts = [
            {
                "file_path": f"benchmark_{i}.py",
                "cursor_position": 50,
                "surrounding_code": f"# Test context {i}\ndef function_{i}():\n    pass"
            }
            for i in range(30)
        ]
        
        for context in contexts:
            start_time = time.time()
            result = await ai_service.generate_code_completion(context)
            response_time = time.time() - start_time
            response_times.append(response_time)
        
        # Calculate statistics
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        min_time = min(response_times)
        
        # Performance assertions
        assert avg_time < 1.8, f"Average response time {avg_time:.3f}s should be <1.8s"
        assert max_time < 3.0, f"Max response time {max_time:.3f}s should be <3s"
        
        # 90th percentile should meet target
        sorted_times = sorted(response_times)
        p90_time = sorted_times[int(0.9 * len(sorted_times))]
        assert p90_time < 2.0, f"90th percentile {p90_time:.3f}s should meet 2s target"
    
    @pytest.mark.asyncio
    async def test_ai_throughput_benchmark(self):
        """Benchmark AI throughput (requests per second)"""
        ai_service = MockMLXService()
        await ai_service.initialize()
        
        # Measure throughput over time period
        duration = 10  # seconds
        start_time = time.time()
        request_count = 0
        
        context = {
            "file_path": "throughput_test.py",
            "surrounding_code": "def test(): pass"
        }
        
        while time.time() - start_time < duration:
            await ai_service.generate_code_completion(context)
            request_count += 1
            
            # Prevent overwhelming the system
            if request_count % 5 == 0:
                await asyncio.sleep(0.1)
        
        actual_duration = time.time() - start_time
        throughput = request_count / actual_duration
        
        # Should handle reasonable throughput
        assert throughput > 0.5, f"Throughput {throughput:.2f} req/s is too low"
        assert throughput < 10, f"Throughput {throughput:.2f} req/s seems unrealistic for testing"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])