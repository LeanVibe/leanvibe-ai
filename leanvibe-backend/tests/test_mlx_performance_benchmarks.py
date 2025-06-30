"""
MLX Performance Benchmarking Tests

Comprehensive performance tests to validate MLX inference times (<5s) and
API response times (<1s) as specified in the execution prompt requirements.

Tests real pre-trained weight loading performance and API endpoint responsiveness.
"""

import pytest
import time
import asyncio
import statistics
from unittest.mock import patch, AsyncMock
from typing import List, Dict, Any


class PerformanceMetrics:
    """Helper class to collect and analyze performance metrics"""
    
    def __init__(self):
        self.measurements: List[float] = []
        self.start_time: float = 0
        
    def start_timer(self):
        """Start timing measurement"""
        self.start_time = time.perf_counter()
    
    def end_timer(self) -> float:
        """End timing measurement and record result"""
        elapsed = time.perf_counter() - self.start_time
        self.measurements.append(elapsed)
        return elapsed
    
    def get_stats(self) -> Dict[str, float]:
        """Get performance statistics"""
        if not self.measurements:
            return {}
        
        return {
            "count": len(self.measurements),
            "mean": statistics.mean(self.measurements),
            "median": statistics.median(self.measurements),
            "min": min(self.measurements),
            "max": max(self.measurements),
            "p95": self._percentile(self.measurements, 95),
            "p99": self._percentile(self.measurements, 99)
        }
    
    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile of measurements"""
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        lower = int(index)
        upper = min(lower + 1, len(sorted_data) - 1)
        weight = index - lower
        return sorted_data[lower] * (1 - weight) + sorted_data[upper] * weight


@pytest.mark.performance
@pytest.mark.mlx_real_inference
async def test_mlx_inference_performance_requirements():
    """Test MLX inference performance meets <5s requirement"""
    from app.services.phi3_mini_service import Phi3MiniService
    
    # Initialize service with real weights
    service = Phi3MiniService()
    await service.initialize()
    
    # Performance tracking
    inference_metrics = PerformanceMetrics()
    
    # Test prompts of varying complexity
    test_prompts = [
        "Write a simple Python function",
        "Explain the concept of machine learning in 2 sentences",
        "Create a REST API endpoint for user authentication with proper error handling and validation",
        "Analyze this code and suggest optimizations:\ndef slow_function():\n    result = []\n    for i in range(1000):\n        for j in range(1000):\n            result.append(i * j)\n    return result",
        "Design a scalable microservices architecture for an e-commerce platform including database considerations, caching strategies, and deployment patterns"
    ]
    
    for prompt in test_prompts:
        inference_metrics.start_timer()
        
        # Test real inference
        result = await service.generate_text(prompt, max_tokens=200)
        
        elapsed = inference_metrics.end_timer()
        
        # Verify inference completed successfully
        assert result is not None
        assert len(result) > 0
        
        # Verify performance requirement: <5s per inference
        assert elapsed < 5.0, f"Inference took {elapsed:.2f}s, exceeds 5s limit"
        
        print(f"Inference time for prompt length {len(prompt)}: {elapsed:.3f}s")
    
    # Analyze overall performance statistics
    stats = inference_metrics.get_stats()
    print(f"\nMLX Inference Performance Stats:")
    print(f"Mean: {stats['mean']:.3f}s")
    print(f"P95: {stats['p95']:.3f}s")
    print(f"P99: {stats['p99']:.3f}s")
    print(f"Max: {stats['max']:.3f}s")
    
    # Verify performance requirements
    assert stats['mean'] < 3.0, f"Mean inference time {stats['mean']:.3f}s exceeds 3s target"
    assert stats['p95'] < 5.0, f"P95 inference time {stats['p95']:.3f}s exceeds 5s limit"
    assert stats['max'] < 5.0, f"Max inference time {stats['max']:.3f}s exceeds 5s limit"


@pytest.mark.performance
async def test_api_response_time_requirements(test_client):
    """Test API response times meet <1s requirement"""
    
    api_metrics = PerformanceMetrics()
    
    # Test various API endpoints
    api_endpoints = [
        ("GET", "/health"),
        ("GET", "/health-mlx"),
        ("GET", "/sessions"),
        ("POST", "/tasks/perf-test-client", {"title": "Performance Test", "description": "API performance testing"}),
        ("GET", "/tasks/perf-test-client"),
        ("GET", "/streaming/stats"),
        ("GET", "/connections")
    ]
    
    for method, endpoint, *data in api_endpoints:
        api_metrics.start_timer()
        
        if method == "GET":
            response = test_client.get(endpoint)
        elif method == "POST":
            response = test_client.post(endpoint, json=data[0] if data else {})
        
        elapsed = api_metrics.end_timer()
        
        # Verify API responded successfully
        assert response.status_code in [200, 201], f"API {endpoint} failed with status {response.status_code}"
        
        # Verify performance requirement: <1s per API call
        assert elapsed < 1.0, f"API {endpoint} took {elapsed:.3f}s, exceeds 1s limit"
        
        print(f"API {method} {endpoint}: {elapsed:.3f}s")
    
    # Analyze API performance statistics
    stats = api_metrics.get_stats()
    print(f"\nAPI Response Performance Stats:")
    print(f"Mean: {stats['mean']:.3f}s")
    print(f"P95: {stats['p95']:.3f}s")
    print(f"Max: {stats['max']:.3f}s")
    
    # Verify performance requirements
    assert stats['mean'] < 0.5, f"Mean API response time {stats['mean']:.3f}s exceeds 500ms target"
    assert stats['p95'] < 1.0, f"P95 API response time {stats['p95']:.3f}s exceeds 1s limit"
    assert stats['max'] < 1.0, f"Max API response time {stats['max']:.3f}s exceeds 1s limit"


@pytest.mark.performance
@pytest.mark.mlx_real_inference
async def test_mlx_concurrent_inference_performance():
    """Test MLX performance under concurrent load"""
    from app.services.phi3_mini_service import Phi3MiniService
    
    service = Phi3MiniService()
    await service.initialize()
    
    concurrent_metrics = PerformanceMetrics()
    num_concurrent_requests = 5
    
    async def single_inference(prompt_id: int):
        """Single inference task for concurrent testing"""
        start_time = time.perf_counter()
        
        prompt = f"Generate a Python function for task {prompt_id} that processes data efficiently"
        result = await service.generate_text(prompt, max_tokens=150)
        
        elapsed = time.perf_counter() - start_time
        return elapsed, len(result) if result else 0
    
    # Run concurrent inferences
    concurrent_metrics.start_timer()
    
    tasks = [single_inference(i) for i in range(num_concurrent_requests)]
    results = await asyncio.gather(*tasks)
    
    total_concurrent_time = concurrent_metrics.end_timer()
    
    # Analyze concurrent performance
    individual_times = [result[0] for result in results]
    response_lengths = [result[1] for result in results]
    
    print(f"\nConcurrent Inference Performance:")
    print(f"Total time for {num_concurrent_requests} concurrent inferences: {total_concurrent_time:.3f}s")
    print(f"Average individual inference time: {statistics.mean(individual_times):.3f}s")
    print(f"Max individual inference time: {max(individual_times):.3f}s")
    print(f"Average response length: {statistics.mean(response_lengths)} chars")
    
    # Verify concurrent performance requirements
    assert total_concurrent_time < 10.0, f"Concurrent inferences took {total_concurrent_time:.3f}s, too slow"
    assert max(individual_times) < 5.0, f"Slowest concurrent inference took {max(individual_times):.3f}s"
    assert all(length > 0 for length in response_lengths), "Some inferences produced no output"


@pytest.mark.performance
async def test_mlx_memory_usage_during_inference():
    """Test MLX memory usage stays within acceptable limits during inference"""
    import psutil
    import os
    from app.services.phi3_mini_service import Phi3MiniService
    
    # Get initial memory usage
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    service = Phi3MiniService()
    await service.initialize()
    
    post_init_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    # Run inference and monitor memory
    memory_measurements = []
    
    for i in range(10):
        pre_inference_memory = process.memory_info().rss / 1024 / 1024
        
        prompt = f"Create a detailed code example {i} with comprehensive documentation and error handling"
        await service.generate_text(prompt, max_tokens=300)
        
        post_inference_memory = process.memory_info().rss / 1024 / 1024
        memory_measurements.append(post_inference_memory)
        
        # Small delay to allow garbage collection
        await asyncio.sleep(0.1)
    
    max_memory = max(memory_measurements)
    memory_growth = max_memory - post_init_memory
    
    print(f"\nMemory Usage Analysis:")
    print(f"Initial memory: {initial_memory:.1f} MB")
    print(f"Post-initialization memory: {post_init_memory:.1f} MB")
    print(f"Max memory during inference: {max_memory:.1f} MB")
    print(f"Memory growth during inference: {memory_growth:.1f} MB")
    
    # Verify memory usage requirements
    assert max_memory < 2000, f"Memory usage {max_memory:.1f} MB exceeds 2GB limit"
    assert memory_growth < 500, f"Memory growth {memory_growth:.1f} MB during inference too high"


@pytest.mark.performance
async def test_api_concurrent_load_performance(test_client):
    """Test API performance under concurrent load"""
    import threading
    import concurrent.futures
    
    load_metrics = PerformanceMetrics()
    num_concurrent_clients = 10
    requests_per_client = 5
    
    def make_api_requests(client_id: int) -> List[float]:
        """Make multiple API requests from a single client"""
        client_times = []
        
        for request_id in range(requests_per_client):
            start_time = time.perf_counter()
            
            # Mix of different API calls
            if request_id % 3 == 0:
                response = test_client.get("/health")
            elif request_id % 3 == 1:
                response = test_client.post(f"/tasks/load-client-{client_id}", json={
                    "title": f"Load test task {request_id}",
                    "description": f"Client {client_id} request {request_id}"
                })
            else:
                response = test_client.get(f"/tasks/load-client-{client_id}")
            
            elapsed = time.perf_counter() - start_time
            client_times.append(elapsed)
            
            # Verify response
            assert response.status_code in [200, 201], f"Request failed: {response.status_code}"
        
        return client_times
    
    # Run concurrent load test
    load_metrics.start_timer()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_concurrent_clients) as executor:
        futures = [executor.submit(make_api_requests, i) for i in range(num_concurrent_clients)]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    total_load_time = load_metrics.end_timer()
    
    # Analyze load test results
    all_request_times = [time for client_times in results for time in client_times]
    total_requests = len(all_request_times)
    
    print(f"\nConcurrent Load Test Results:")
    print(f"Total requests: {total_requests}")
    print(f"Total time: {total_load_time:.3f}s")
    print(f"Requests per second: {total_requests / total_load_time:.1f}")
    print(f"Average request time: {statistics.mean(all_request_times):.3f}s")
    print(f"Max request time: {max(all_request_times):.3f}s")
    print(f"P95 request time: {PerformanceMetrics._percentile(None, all_request_times, 95):.3f}s")
    
    # Verify load performance requirements
    assert statistics.mean(all_request_times) < 1.0, "Average request time under load exceeds 1s"
    assert max(all_request_times) < 2.0, "Max request time under load exceeds 2s"
    assert total_requests / total_load_time > 10, "Throughput too low under concurrent load"


@pytest.mark.performance
@pytest.mark.mlx_real_inference
async def test_mlx_model_initialization_performance():
    """Test MLX model initialization time"""
    from app.services.phi3_mini_service import Phi3MiniService
    
    init_metrics = PerformanceMetrics()
    
    # Test initialization multiple times
    for iteration in range(3):
        service = Phi3MiniService()
        
        init_metrics.start_timer()
        await service.initialize()
        init_time = init_metrics.end_timer()
        
        # Verify service is properly initialized
        assert service.is_initialized, f"Service not initialized after {init_time:.3f}s"
        
        # Test quick inference to verify model is loaded
        test_result = await service.generate_text("Test", max_tokens=10)
        assert test_result is not None, "Model not properly loaded"
        
        print(f"Initialization {iteration + 1}: {init_time:.3f}s")
    
    # Analyze initialization performance
    stats = init_metrics.get_stats()
    print(f"\nMLX Initialization Performance:")
    print(f"Mean initialization time: {stats['mean']:.3f}s")
    print(f"Max initialization time: {stats['max']:.3f}s")
    
    # Verify initialization performance requirements
    assert stats['mean'] < 30.0, f"Mean initialization time {stats['mean']:.3f}s too slow"
    assert stats['max'] < 45.0, f"Max initialization time {stats['max']:.3f}s too slow"


@pytest.mark.performance
async def test_end_to_end_ai_workflow_performance(test_client):
    """Test complete end-to-end AI workflow performance"""
    
    workflow_metrics = PerformanceMetrics()
    
    # Test complete workflow: Task creation -> AI analysis -> Response
    workflows = [
        {
            "title": "Simple function implementation",
            "description": "Create a function to calculate fibonacci numbers",
            "analyze_with_ai": True
        },
        {
            "title": "Database optimization task", 
            "description": "Optimize database queries for user authentication",
            "analyze_with_ai": True
        },
        {
            "title": "API security enhancement",
            "description": "Add rate limiting and input validation to REST API",
            "analyze_with_ai": True
        }
    ]
    
    for i, workflow_data in enumerate(workflows):
        workflow_metrics.start_timer()
        
        # Step 1: Create task with AI analysis
        response = test_client.post(f"/tasks/e2e-perf-client-{i}", json=workflow_data)
        
        workflow_time = workflow_metrics.end_timer()
        
        # Verify workflow completed successfully
        assert response.status_code == 201, f"Workflow {i} failed: {response.status_code}"
        
        task_data = response.json()
        assert "ai_analysis" in task_data, f"Workflow {i} missing AI analysis"
        assert len(task_data["ai_analysis"]) > 0, f"Workflow {i} empty AI analysis"
        
        print(f"E2E workflow {i + 1}: {workflow_time:.3f}s")
        
        # Verify individual workflow performance
        assert workflow_time < 6.0, f"Workflow {i} took {workflow_time:.3f}s, exceeds 6s limit"
    
    # Analyze overall workflow performance
    stats = workflow_metrics.get_stats()
    print(f"\nEnd-to-End Workflow Performance:")
    print(f"Mean workflow time: {stats['mean']:.3f}s")
    print(f"Max workflow time: {stats['max']:.3f}s")
    
    # Verify end-to-end performance requirements
    assert stats['mean'] < 5.0, f"Mean workflow time {stats['mean']:.3f}s exceeds 5s target"
    assert stats['max'] < 6.0, f"Max workflow time {stats['max']:.3f}s exceeds 6s limit"


@pytest.mark.performance
@pytest.mark.stress
async def test_mlx_service_stress_test():
    """Stress test MLX service with high load"""
    from app.services.phi3_mini_service import Phi3MiniService
    
    service = Phi3MiniService()
    await service.initialize()
    
    stress_metrics = PerformanceMetrics()
    num_stress_requests = 20
    
    async def stress_inference(request_id: int):
        """Single stress test inference"""
        prompt = f"Stress test {request_id}: Write a comprehensive Python class with methods, error handling, and documentation"
        
        start_time = time.perf_counter()
        result = await service.generate_text(prompt, max_tokens=400)
        elapsed = time.perf_counter() - start_time
        
        return {
            "request_id": request_id,
            "elapsed": elapsed,
            "success": result is not None,
            "response_length": len(result) if result else 0
        }
    
    # Run stress test
    print(f"\nRunning stress test with {num_stress_requests} requests...")
    
    stress_metrics.start_timer()
    
    # Create all tasks and run them
    tasks = [stress_inference(i) for i in range(num_stress_requests)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    total_stress_time = stress_metrics.end_timer()
    
    # Analyze stress test results
    successful_results = [r for r in results if isinstance(r, dict) and r["success"]]
    failed_results = [r for r in results if not (isinstance(r, dict) and r.get("success", False))]
    
    success_rate = len(successful_results) / num_stress_requests
    avg_response_time = statistics.mean([r["elapsed"] for r in successful_results]) if successful_results else 0
    
    print(f"Stress Test Results:")
    print(f"Total time: {total_stress_time:.3f}s")
    print(f"Success rate: {success_rate:.1%}")
    print(f"Successful requests: {len(successful_results)}/{num_stress_requests}")
    print(f"Failed requests: {len(failed_results)}")
    print(f"Average response time: {avg_response_time:.3f}s")
    
    if successful_results:
        response_times = [r["elapsed"] for r in successful_results]
        print(f"Min response time: {min(response_times):.3f}s")
        print(f"Max response time: {max(response_times):.3f}s")
    
    # Verify stress test requirements
    assert success_rate >= 0.95, f"Success rate {success_rate:.1%} below 95% threshold"
    assert avg_response_time < 5.0, f"Average response time {avg_response_time:.3f}s exceeds 5s under stress"
    assert len(failed_results) == 0, f"Had {len(failed_results)} failed requests during stress test"