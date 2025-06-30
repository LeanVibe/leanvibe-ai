"""
Comprehensive Integration and Performance Testing Suite

High-impact test suite for validating service integration, performance benchmarks,
load testing, memory usage, and end-to-end workflows. Tests the complete LeanVibe
backend system under realistic conditions.
"""

import asyncio
import gc
import json
import psutil
import pytest
import time
import tempfile
import shutil
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from unittest.mock import AsyncMock, MagicMock, patch
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.services.enhanced_ai_service import EnhancedAIService
from app.services.event_streaming_service import EventStreamingService, event_streaming_service
from app.services.task_service import TaskService
from app.core.connection_manager import ConnectionManager
from app.models.task_models import TaskCreate, TaskUpdate
from app.models.event_models import (
    EventType, EventPriority, NotificationChannel, ClientPreferences,
    create_file_change_event, create_analysis_event, create_agent_event
)


class PerformanceMetrics:
    """Track performance metrics during testing"""
    
    def __init__(self):
        self.response_times: List[float] = []
        self.memory_usage: List[float] = []
        self.cpu_usage: List[float] = []
        self.throughput_counts: List[int] = []
        self.error_counts: List[int] = []
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
    
    def start_monitoring(self):
        """Start performance monitoring"""
        self.start_time = time.time()
        self._record_system_metrics()
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.end_time = time.time()
        self._record_system_metrics()
    
    def record_response_time(self, response_time: float):
        """Record a response time measurement"""
        self.response_times.append(response_time)
    
    def record_throughput(self, count: int):
        """Record throughput count"""
        self.throughput_counts.append(count)
    
    def record_error(self):
        """Record an error occurrence"""
        self.error_counts.append(1)
    
    def _record_system_metrics(self):
        """Record current system metrics"""
        process = psutil.Process()
        self.memory_usage.append(process.memory_info().rss / 1024 / 1024)  # MB
        self.cpu_usage.append(process.cpu_percent())
    
    def get_summary(self) -> Dict:
        """Get performance metrics summary"""
        duration = (self.end_time - self.start_time) if self.start_time and self.end_time else 0
        
        return {
            "duration_seconds": duration,
            "response_times": {
                "avg": statistics.mean(self.response_times) if self.response_times else 0,
                "min": min(self.response_times) if self.response_times else 0,
                "max": max(self.response_times) if self.response_times else 0,
                "p95": statistics.quantiles(self.response_times, n=20)[18] if len(self.response_times) >= 20 else 0,
                "p99": statistics.quantiles(self.response_times, n=100)[98] if len(self.response_times) >= 100 else 0,
                "count": len(self.response_times)
            },
            "memory_usage_mb": {
                "avg": statistics.mean(self.memory_usage) if self.memory_usage else 0,
                "max": max(self.memory_usage) if self.memory_usage else 0,
                "min": min(self.memory_usage) if self.memory_usage else 0
            },
            "cpu_usage_percent": {
                "avg": statistics.mean(self.cpu_usage) if self.cpu_usage else 0,
                "max": max(self.cpu_usage) if self.cpu_usage else 0
            },
            "throughput": {
                "total_operations": sum(self.throughput_counts),
                "operations_per_second": sum(self.throughput_counts) / duration if duration > 0 else 0
            },
            "errors": {
                "total": sum(self.error_counts),
                "error_rate": sum(self.error_counts) / len(self.response_times) if self.response_times else 0
            }
        }
    
    def assert_performance_requirements(self, requirements: Dict):
        """Assert that performance meets requirements"""
        summary = self.get_summary()
        
        if "max_response_time" in requirements:
            max_response = summary["response_times"]["max"]
            assert max_response <= requirements["max_response_time"], \
                f"Max response time {max_response}s exceeds requirement {requirements['max_response_time']}s"
        
        if "avg_response_time" in requirements:
            avg_response = summary["response_times"]["avg"]
            assert avg_response <= requirements["avg_response_time"], \
                f"Avg response time {avg_response}s exceeds requirement {requirements['avg_response_time']}s"
        
        if "max_memory_mb" in requirements:
            max_memory = summary["memory_usage_mb"]["max"]
            assert max_memory <= requirements["max_memory_mb"], \
                f"Max memory usage {max_memory}MB exceeds requirement {requirements['max_memory_mb']}MB"
        
        if "min_throughput" in requirements:
            throughput = summary["throughput"]["operations_per_second"]
            assert throughput >= requirements["min_throughput"], \
                f"Throughput {throughput} ops/sec below requirement {requirements['min_throughput']} ops/sec"
        
        if "max_error_rate" in requirements:
            error_rate = summary["errors"]["error_rate"]
            assert error_rate <= requirements["max_error_rate"], \
                f"Error rate {error_rate} exceeds requirement {requirements['max_error_rate']}"


class MockWebSocket:
    """Enhanced mock WebSocket for integration testing"""
    
    def __init__(self, client_id: str = "test-client"):
        self.client_id = client_id
        self.sent_messages = []
        self.sent_bytes = []
        self.closed = False
        self.response_times = []
        
    async def send_text(self, message: str):
        start_time = time.time()
        if self.closed:
            raise Exception("WebSocket connection closed")
        self.sent_messages.append(message)
        response_time = time.time() - start_time
        self.response_times.append(response_time)
        
    async def send_bytes(self, data: bytes):
        start_time = time.time()
        if self.closed:
            raise Exception("WebSocket connection closed")
        self.sent_bytes.append(data)
        response_time = time.time() - start_time
        self.response_times.append(response_time)
    
    def get_avg_response_time(self) -> float:
        return statistics.mean(self.response_times) if self.response_times else 0


@pytest.fixture
def performance_metrics():
    """Create performance metrics tracker"""
    return PerformanceMetrics()


@pytest.fixture
def temp_workspace():
    """Create temporary workspace for testing"""
    temp_dir = tempfile.mkdtemp(prefix="leanvibe_test_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def enhanced_ai_service():
    """Create enhanced AI service for testing"""
    with patch('app.services.enhanced_ai_service.EnhancedAIService.initialize') as mock_init:
        mock_init.return_value = None
        service = EnhancedAIService()
        service.is_initialized = True
        yield service


@pytest.fixture  
def task_service(temp_workspace):
    """Create task service for testing"""
    service = TaskService(data_dir=temp_workspace)
    asyncio.run(service.initialize())
    return service


@pytest.fixture
def streaming_service():
    """Create event streaming service for testing"""
    service = EventStreamingService()
    yield service
    # Cleanup
    if service.processing_task:
        service.processing_task.cancel()


@pytest.fixture
def connection_manager():
    """Create connection manager for testing"""
    return ConnectionManager()


class TestServiceIntegration:
    """Test integration between major services"""
    
    @pytest.mark.asyncio
    async def test_ai_service_task_service_integration(self, enhanced_ai_service, task_service, performance_metrics):
        """Test integration between AI service and task service"""
        performance_metrics.start_monitoring()
        
        # Create task through task service
        start_time = time.time()
        task_data = TaskCreate(
            title="AI Integration Test Task",
            description="Test task for AI integration",
            priority="high"
        )
        
        task = await task_service.create_task(task_data)
        performance_metrics.record_response_time(time.time() - start_time)
        
        assert task is not None
        assert task.title == "AI Integration Test Task"
        
        # Test AI service processing (mocked)
        with patch.object(enhanced_ai_service, 'process_code_request', return_value="AI response"):
            start_time = time.time()
            response = enhanced_ai_service.process_code_request("Analyze the task")
            performance_metrics.record_response_time(time.time() - start_time)
            
            assert response == "AI response"
        
        # Update task based on AI analysis
        start_time = time.time()
        update_data = TaskUpdate(
            description="Updated based on AI analysis",
            metadata={"ai_processed": True}
        )
        updated_task = await task_service.update_task(task.id, update_data)
        performance_metrics.record_response_time(time.time() - start_time)
        
        assert updated_task is not None
        assert updated_task.description == "Updated based on AI analysis"
        assert updated_task.metadata.get("ai_processed") is True
        
        performance_metrics.stop_monitoring()
        
        # Verify performance requirements
        performance_metrics.assert_performance_requirements({
            "max_response_time": 1.0,  # Max 1 second per operation
            "avg_response_time": 0.5,  # Avg 500ms per operation
            "max_memory_mb": 1000      # Max 1GB memory usage
        })
    
    @pytest.mark.asyncio
    async def test_event_streaming_task_integration(self, streaming_service, task_service, connection_manager, performance_metrics):
        """Test integration between event streaming and task management"""
        performance_metrics.start_monitoring()
        
        # Setup WebSocket client
        mock_websocket = MockWebSocket("integration-client")
        client_prefs = ClientPreferences(
            client_id="integration-client",
            enabled_channels=[NotificationChannel.ALL],
            min_priority=EventPriority.LOW,
            enable_batching=False
        )
        
        # Register client with both services
        streaming_service.register_client("integration-client", mock_websocket, client_prefs)
        await connection_manager.connect(mock_websocket, "integration-client", client_prefs)
        
        # Start event streaming
        await streaming_service.start()
        
        # Create task and emit events
        start_time = time.time()
        task_data = TaskCreate(
            title="Event Integration Task",
            priority="medium"
        )
        
        task = await task_service.create_task(task_data)
        performance_metrics.record_response_time(time.time() - start_time)
        
        # Emit task creation event
        start_time = time.time()
        task_event = create_analysis_event("task_created", None, True, 0.1)
        await streaming_service.emit_event(task_event)
        
        # Process events
        await asyncio.sleep(0.1)  # Allow event processing
        performance_metrics.record_response_time(time.time() - start_time)
        
        # Verify event was delivered
        assert len(mock_websocket.sent_messages) > 0
        
        # Update task and emit more events  
        for i in range(5):
            start_time = time.time()
            
            update_data = TaskUpdate(description=f"Update {i}")
            await task_service.update_task(task.id, update_data)
            
            event = create_file_change_event(f"/test/file_{i}.py", "modified")
            await streaming_service.emit_event(event)
            
            performance_metrics.record_response_time(time.time() - start_time)
            performance_metrics.record_throughput(1)
        
        # Allow event processing
        await asyncio.sleep(0.2)
        
        await streaming_service.stop()
        performance_metrics.stop_monitoring()
        
        # Verify performance requirements for integrated workflow
        performance_metrics.assert_performance_requirements({
            "max_response_time": 2.0,  # Max 2 seconds for integrated operations
            "avg_response_time": 0.3,  # Avg 300ms
            "min_throughput": 2.0,     # Min 2 operations per second
            "max_error_rate": 0.1      # Max 10% error rate
        })


class TestLoadTesting:
    """Test system behavior under load"""
    
    @pytest.mark.asyncio
    async def test_high_concurrent_websocket_connections(self, streaming_service, connection_manager, performance_metrics):
        """Test system with many concurrent WebSocket connections"""
        performance_metrics.start_monitoring()
        
        # Create many concurrent connections
        num_clients = 50
        clients = []
        
        # Register many clients
        for i in range(num_clients):
            start_time = time.time()
            
            client_id = f"load-client-{i}"
            mock_websocket = MockWebSocket(client_id)
            client_prefs = ClientPreferences(
                client_id=client_id,
                enabled_channels=[NotificationChannel.ALL],
                min_priority=EventPriority.MEDIUM,
                enable_batching=True,
                batch_interval_ms=100
            )
            
            streaming_service.register_client(client_id, mock_websocket, client_prefs)
            await connection_manager.connect(mock_websocket, client_id, client_prefs)
            clients.append((client_id, mock_websocket))
            
            performance_metrics.record_response_time(time.time() - start_time)
        
        await streaming_service.start()
        
        # Emit many events concurrently
        num_events = 200
        events_per_batch = 10
        
        for batch in range(0, num_events, events_per_batch):
            start_time = time.time()
            
            # Emit batch of events
            for i in range(events_per_batch):
                event = create_file_change_event(f"/load/test/file_{batch + i}.py", "modified")
                await streaming_service.emit_event(event)
            
            performance_metrics.record_response_time(time.time() - start_time)
            performance_metrics.record_throughput(events_per_batch)
            
            # Small delay between batches
            await asyncio.sleep(0.01)
        
        # Allow event processing
        await asyncio.sleep(1.0)
        
        # Verify all clients received some events
        total_messages_received = sum(len(ws.sent_messages) + len(ws.sent_bytes) for _, ws in clients)
        assert total_messages_received > 0, "No messages were delivered to clients"
        
        # Clean up connections
        for client_id, _ in clients:
            streaming_service.unregister_client(client_id)
            connection_manager.disconnect(client_id)
        
        await streaming_service.stop()
        performance_metrics.stop_monitoring()
        
        # Verify load testing requirements
        performance_metrics.assert_performance_requirements({
            "max_response_time": 5.0,    # Max 5 seconds under load
            "avg_response_time": 1.0,    # Avg 1 second under load
            "min_throughput": 10.0,      # Min 10 operations per second
            "max_memory_mb": 2000,       # Max 2GB under load
            "max_error_rate": 0.2        # Max 20% error rate under load
        })
    
    @pytest.mark.asyncio
    async def test_high_volume_task_operations(self, task_service, performance_metrics):
        """Test task service with high volume of operations"""
        performance_metrics.start_monitoring()
        
        # Create many tasks rapidly
        num_tasks = 100
        task_ids = []
        
        # Batch create tasks
        for i in range(num_tasks):
            start_time = time.time()
            
            task_data = TaskCreate(
                title=f"Load Test Task {i}",
                description=f"High volume test task number {i}",
                priority="medium" if i % 2 == 0 else "high"
            )
            
            task = await task_service.create_task(task_data)
            task_ids.append(task.id)
            
            performance_metrics.record_response_time(time.time() - start_time)
            performance_metrics.record_throughput(1)
        
        # Batch update tasks
        for i, task_id in enumerate(task_ids):
            start_time = time.time()
            
            update_data = TaskUpdate(
                description=f"Updated load test task {i}",
                metadata={"load_test": True, "iteration": i}
            )
            
            updated_task = await task_service.update_task(task_id, update_data)
            assert updated_task is not None
            
            performance_metrics.record_response_time(time.time() - start_time)
            performance_metrics.record_throughput(1)
        
        # Test task retrieval performance
        start_time = time.time()
        all_tasks = await task_service.list_tasks()
        performance_metrics.record_response_time(time.time() - start_time)
        
        assert len(all_tasks) >= num_tasks
        
        # Test kanban board generation under load
        start_time = time.time()
        kanban_board = await task_service.get_kanban_board()
        performance_metrics.record_response_time(time.time() - start_time)
        
        assert kanban_board is not None
        assert kanban_board.total_tasks >= num_tasks
        
        # Test search performance
        start_time = time.time()
        from app.models.task_models import TaskSearchRequest
        search_request = TaskSearchRequest(query="Load Test", limit=50)
        search_results = await task_service.search_tasks(search_request)
        performance_metrics.record_response_time(time.time() - start_time)
        
        assert len(search_results) > 0
        
        performance_metrics.stop_monitoring()
        
        # Verify task service performance under load
        performance_metrics.assert_performance_requirements({
            "max_response_time": 3.0,    # Max 3 seconds for task operations
            "avg_response_time": 0.5,    # Avg 500ms for task operations
            "min_throughput": 20.0,      # Min 20 tasks per second
            "max_memory_mb": 1500        # Max 1.5GB for task operations
        })


class TestMemoryAndResourceUsage:
    """Test memory usage and resource management"""
    
    @pytest.mark.asyncio
    async def test_memory_usage_during_event_streaming(self, streaming_service, performance_metrics):
        """Test memory usage patterns during event streaming"""
        performance_metrics.start_monitoring()
        
        # Force garbage collection before test
        gc.collect()
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        # Register multiple clients
        num_clients = 20
        clients = []
        
        for i in range(num_clients):
            client_id = f"memory-client-{i}"
            mock_websocket = MockWebSocket(client_id)
            client_prefs = ClientPreferences(client_id=client_id)
            
            streaming_service.register_client(client_id, mock_websocket, client_prefs)
            clients.append((client_id, mock_websocket))
        
        await streaming_service.start()
        
        # Generate events and monitor memory
        num_events = 500
        memory_samples = []
        
        for i in range(num_events):
            # Create event
            event = create_agent_event(f"session-{i}", EventType.AGENT_PROCESSING, f"Query {i}")
            await streaming_service.emit_event(event)
            
            # Sample memory every 50 events
            if i % 50 == 0:
                current_memory = psutil.Process().memory_info().rss / 1024 / 1024
                memory_samples.append(current_memory)
                performance_metrics.memory_usage.append(current_memory)
            
            # Small delay to prevent overwhelming
            if i % 10 == 0:
                await asyncio.sleep(0.01)
        
        # Allow event processing
        await asyncio.sleep(0.5)
        
        # Check for memory leaks
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_growth = final_memory - initial_memory
        
        # Cleanup
        for client_id, _ in clients:
            streaming_service.unregister_client(client_id)
        
        await streaming_service.stop()
        
        # Force garbage collection and check memory after cleanup
        gc.collect()
        await asyncio.sleep(0.1)
        cleanup_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        performance_metrics.stop_monitoring()
        
        # Memory usage assertions
        assert memory_growth < 500, f"Excessive memory growth: {memory_growth}MB"
        
        # Memory should decrease after cleanup (allowing for some variance)
        memory_cleanup_ratio = (final_memory - cleanup_memory) / memory_growth if memory_growth > 0 else 0
        assert memory_cleanup_ratio > 0.3, f"Poor memory cleanup: {memory_cleanup_ratio}"
        
        print(f"Memory usage: Initial: {initial_memory:.1f}MB, Peak: {final_memory:.1f}MB, " +
              f"After cleanup: {cleanup_memory:.1f}MB, Growth: {memory_growth:.1f}MB")
    
    @pytest.mark.asyncio
    async def test_resource_cleanup_on_service_shutdown(self, streaming_service, task_service, performance_metrics):
        """Test proper resource cleanup when services shut down"""
        performance_metrics.start_monitoring()
        
        # Setup services with resources
        num_clients = 10
        num_tasks = 20
        
        # Create clients and tasks
        for i in range(num_clients):
            client_id = f"cleanup-client-{i}"
            mock_websocket = MockWebSocket(client_id)
            client_prefs = ClientPreferences(client_id=client_id)
            streaming_service.register_client(client_id, mock_websocket, client_prefs)
        
        for i in range(num_tasks):
            task_data = TaskCreate(title=f"Cleanup Task {i}")
            await task_service.create_task(task_data)
        
        await streaming_service.start()
        
        # Generate some activity
        for i in range(50):
            event = create_file_change_event(f"/cleanup/file_{i}.py", "modified")
            await streaming_service.emit_event(event)
        
        # Record resource usage before shutdown
        before_shutdown_memory = psutil.Process().memory_info().rss / 1024 / 1024
        before_shutdown_threads = len(psutil.Process().threads())
        
        # Shutdown services
        await streaming_service.stop()
        
        # Force cleanup
        gc.collect()
        await asyncio.sleep(0.2)
        
        # Record resource usage after shutdown
        after_shutdown_memory = psutil.Process().memory_info().rss / 1024 / 1024
        after_shutdown_threads = len(psutil.Process().threads())
        
        performance_metrics.stop_monitoring()
        
        # Verify resource cleanup
        memory_freed = before_shutdown_memory - after_shutdown_memory
        threads_cleaned = before_shutdown_threads - after_shutdown_threads
        
        # Allow for some memory variance, but should see some cleanup
        assert memory_freed > -50, f"Memory not properly freed: {memory_freed}MB change"
        
        # Threads should not increase significantly
        assert threads_cleaned >= -2, f"Thread cleanup issue: {threads_cleaned} threads difference"
        
        print(f"Resource cleanup: Memory freed: {memory_freed:.1f}MB, " +
              f"Thread change: {threads_cleaned}")


class TestEndToEndWorkflows:
    """Test complete end-to-end workflows"""
    
    @pytest.mark.asyncio
    async def test_complete_development_workflow(self, enhanced_ai_service, task_service, streaming_service, connection_manager, performance_metrics):
        """Test a complete development workflow from task creation to completion"""
        performance_metrics.start_monitoring()
        
        # Setup WebSocket client for real-time updates
        mock_websocket = MockWebSocket("dev-workflow-client")
        client_prefs = ClientPreferences(
            client_id="dev-workflow-client",
            enabled_channels=[NotificationChannel.ALL],
            min_priority=EventPriority.LOW,
            enable_batching=False
        )
        
        streaming_service.register_client("dev-workflow-client", mock_websocket, client_prefs)
        await connection_manager.connect(mock_websocket, "dev-workflow-client", client_prefs)
        await streaming_service.start()
        
        # Step 1: Create development task
        start_time = time.time()
        task_data = TaskCreate(
            title="Implement new feature",
            description="Add real-time notifications to dashboard",
            priority="high",
            estimated_hours=8.0,
            tags=["feature", "frontend", "real-time"]
        )
        
        task = await task_service.create_task(task_data)
        performance_metrics.record_response_time(time.time() - start_time)
        assert task is not None
        
        # Step 2: Start development - file changes
        file_changes = [
            "/src/components/Dashboard.tsx",
            "/src/services/NotificationService.ts", 
            "/src/types/Notification.ts",
            "/tests/NotificationService.test.ts"
        ]
        
        for file_path in file_changes:
            start_time = time.time()
            
            # Simulate file change event
            event = create_file_change_event(file_path, "modified")
            await streaming_service.emit_event(event)
            
            # Simulate AST analysis
            analysis_event = create_analysis_event("ast", file_path, True, 0.5)
            await streaming_service.emit_event(analysis_event)
            
            performance_metrics.record_response_time(time.time() - start_time)
            performance_metrics.record_throughput(1)
        
        # Step 3: Move task through workflow states
        workflow_states = ["in_progress", "testing", "done"]
        
        for state in workflow_states:
            start_time = time.time()
            
            from app.models.task_models import TaskStatusUpdate
            status_update = TaskStatusUpdate(status=state)
            updated_task = await task_service.update_task_status(task.id, status_update)
            
            assert updated_task.status == state
            
            # Emit task state change event
            state_event = create_agent_event(
                f"workflow-{task.id}", 
                EventType.AGENT_COMPLETED,
                f"Task moved to {state}"
            )
            await streaming_service.emit_event(state_event)
            
            performance_metrics.record_response_time(time.time() - start_time)
            performance_metrics.record_throughput(1)
        
        # Step 4: AI code analysis (mocked)
        with patch.object(enhanced_ai_service, 'process_code_request') as mock_ai:
            mock_ai.return_value = {
                "analysis": "Code quality is good",
                "suggestions": ["Add error handling", "Improve test coverage"],
                "complexity_score": 7.2
            }
            
            start_time = time.time()
            ai_analysis = enhanced_ai_service.process_code_request(
                "Analyze the notification service implementation"
            )
            performance_metrics.record_response_time(time.time() - start_time)
            
            assert ai_analysis is not None
            assert "analysis" in ai_analysis
        
        # Step 5: Generate project statistics
        start_time = time.time()
        task_stats = await task_service.get_task_stats()
        kanban_board = await task_service.get_kanban_board()
        performance_metrics.record_response_time(time.time() - start_time)
        
        assert task_stats.total_tasks >= 1
        assert kanban_board.total_tasks >= 1
        
        # Allow all events to process
        await asyncio.sleep(0.5)
        
        # Verify real-time notifications were sent
        total_notifications = len(mock_websocket.sent_messages) + len(mock_websocket.sent_bytes)
        assert total_notifications > 0, "No real-time notifications were sent"
        
        # Cleanup
        await streaming_service.stop()
        performance_metrics.stop_monitoring()
        
        # Verify end-to-end performance
        performance_metrics.assert_performance_requirements({
            "max_response_time": 3.0,    # Max 3 seconds for any single operation
            "avg_response_time": 1.0,    # Avg 1 second per operation
            "min_throughput": 5.0,       # Min 5 operations per second
            "max_memory_mb": 1000,       # Max 1GB for complete workflow
            "max_error_rate": 0.05       # Max 5% error rate
        })
        
        # Verify workflow completion
        final_task = await task_service.get_task(task.id)
        assert final_task.status == "done"
        assert len(final_task.tags) == 3
        
        print(f"Complete workflow executed successfully in {performance_metrics.get_summary()['duration_seconds']:.2f}s")
    
    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self, streaming_service, task_service, performance_metrics):
        """Test system behavior and recovery under error conditions"""
        performance_metrics.start_monitoring()
        
        # Setup system
        await streaming_service.start()
        
        # Test 1: Network failure simulation
        failing_websocket = MockWebSocket("failing-client")
        failing_websocket.closed = True  # Simulate network failure
        
        client_prefs = ClientPreferences(client_id="failing-client")
        streaming_service.register_client("failing-client", failing_websocket, client_prefs)
        
        # Emit events to failing client
        for i in range(10):
            start_time = time.time()
            try:
                event = create_file_change_event(f"/error/test_{i}.py", "modified")
                await streaming_service.emit_event(event)
                performance_metrics.record_response_time(time.time() - start_time)
            except Exception:
                performance_metrics.record_error()
        
        # Allow error handling
        await asyncio.sleep(0.2)
        
        # Test 2: Invalid task operations
        invalid_operations = [
            ("nonexistent-task-id", TaskUpdate(title="Updated")),
            ("", TaskUpdate(description="Empty ID")),
            ("invalid-id", TaskUpdate(title="")),  # Empty title
        ]
        
        for task_id, update_data in invalid_operations:
            start_time = time.time()
            try:
                result = await task_service.update_task(task_id, update_data)
                if result is None:
                    performance_metrics.record_error()
                performance_metrics.record_response_time(time.time() - start_time)
            except Exception:
                performance_metrics.record_error()
                performance_metrics.record_response_time(time.time() - start_time)
        
        # Test 3: System recovery - create working client
        working_websocket = MockWebSocket("working-client")
        working_prefs = ClientPreferences(client_id="working-client")
        streaming_service.register_client("working-client", working_websocket, working_prefs)
        
        # Verify system still works after errors
        start_time = time.time()
        recovery_task = await task_service.create_task(TaskCreate(
            title="Recovery Test Task",
            description="Testing system recovery after errors"
        ))
        performance_metrics.record_response_time(time.time() - start_time)
        
        assert recovery_task is not None
        
        # Emit recovery event
        start_time = time.time()
        recovery_event = create_agent_event("recovery", EventType.SYSTEM_READY, "System recovered")
        await streaming_service.emit_event(recovery_event)
        performance_metrics.record_response_time(time.time() - start_time)
        
        await asyncio.sleep(0.1)
        
        # Verify working client received events
        assert len(working_websocket.sent_messages) > 0
        
        await streaming_service.stop()
        performance_metrics.stop_monitoring()
        
        # Verify error recovery performance
        summary = performance_metrics.get_summary()
        
        # Should handle errors gracefully without crashing
        assert summary["errors"]["total"] > 0, "No errors were recorded during error testing"
        assert summary["errors"]["error_rate"] < 0.8, "Error rate too high - system not recovering"
        
        # System should still be responsive despite errors
        assert summary["response_times"]["avg"] < 5.0, "System too slow during error conditions"
        
        print(f"Error recovery test: {summary['errors']['total']} errors handled, " +
              f"{summary['errors']['error_rate']:.2%} error rate, " +
              f"avg response time: {summary['response_times']['avg']:.3f}s")


class TestConcurrencyAndRaceConditions:
    """Test concurrent operations and race condition handling"""
    
    @pytest.mark.asyncio
    async def test_concurrent_task_operations(self, task_service, performance_metrics):
        """Test concurrent task creation and updates"""
        performance_metrics.start_monitoring()
        
        # Test concurrent task creation
        async def create_task_worker(worker_id: int, num_tasks: int):
            tasks_created = []
            for i in range(num_tasks):
                start_time = time.time()
                try:
                    task_data = TaskCreate(
                        title=f"Concurrent Task {worker_id}-{i}",
                        description=f"Created by worker {worker_id}",
                        priority="medium"
                    )
                    task = await task_service.create_task(task_data)
                    tasks_created.append(task.id)
                    performance_metrics.record_response_time(time.time() - start_time)
                    performance_metrics.record_throughput(1)
                except Exception:
                    performance_metrics.record_error()
            return tasks_created
        
        # Run 5 workers creating 10 tasks each concurrently
        num_workers = 5
        tasks_per_worker = 10
        
        tasks = await asyncio.gather(*[
            create_task_worker(worker_id, tasks_per_worker) 
            for worker_id in range(num_workers)
        ])
        
        all_task_ids = [task_id for worker_tasks in tasks for task_id in worker_tasks]
        expected_total = num_workers * tasks_per_worker
        
        assert len(all_task_ids) == expected_total, f"Expected {expected_total} tasks, got {len(all_task_ids)}"
        assert len(set(all_task_ids)) == expected_total, "Duplicate task IDs detected - race condition!"
        
        # Test concurrent updates to same tasks
        async def update_task_worker(task_ids: List[str], worker_id: int):
            for task_id in task_ids[:5]:  # Update first 5 tasks from each worker
                start_time = time.time()
                try:
                    update_data = TaskUpdate(
                        description=f"Updated by worker {worker_id} at {datetime.now().isoformat()}",
                        metadata={f"worker_{worker_id}_update": True}
                    )
                    updated_task = await task_service.update_task(task_id, update_data)
                    if updated_task:
                        performance_metrics.record_response_time(time.time() - start_time)
                        performance_metrics.record_throughput(1)
                    else:
                        performance_metrics.record_error()
                except Exception:
                    performance_metrics.record_error()
                    performance_metrics.record_response_time(time.time() - start_time)
        
        # Run concurrent updates
        await asyncio.gather(*[
            update_task_worker(worker_tasks, worker_id)
            for worker_id, worker_tasks in enumerate(tasks)
        ])
        
        performance_metrics.stop_monitoring()
        
        # Verify data consistency after concurrent operations
        all_tasks_after_update = await task_service.list_tasks()
        assert len(all_tasks_after_update) >= expected_total
        
        # Verify performance under concurrency
        performance_metrics.assert_performance_requirements({
            "max_response_time": 2.0,    # Max 2 seconds per operation under concurrency
            "avg_response_time": 0.5,    # Avg 500ms per operation
            "min_throughput": 20.0,      # Min 20 operations per second
            "max_error_rate": 0.1        # Max 10% error rate under concurrency
        })
    
    @pytest.mark.asyncio
    async def test_event_streaming_concurrency(self, streaming_service, performance_metrics):
        """Test concurrent event emission and processing"""
        performance_metrics.start_monitoring()
        
        # Setup multiple clients
        num_clients = 10
        clients = []
        
        for i in range(num_clients):
            client_id = f"concurrent-client-{i}"
            mock_websocket = MockWebSocket(client_id)
            client_prefs = ClientPreferences(
                client_id=client_id,
                enable_batching=False  # Immediate delivery for testing
            )
            streaming_service.register_client(client_id, mock_websocket, client_prefs)
            clients.append((client_id, mock_websocket))
        
        await streaming_service.start()
        
        # Concurrent event emission from multiple sources
        async def event_emitter(emitter_id: int, num_events: int):
            for i in range(num_events):
                start_time = time.time()
                try:
                    event = create_file_change_event(
                        f"/concurrent/emitter_{emitter_id}/file_{i}.py", 
                        "modified"
                    )
                    await streaming_service.emit_event(event)
                    performance_metrics.record_response_time(time.time() - start_time)
                    performance_metrics.record_throughput(1)
                except Exception:
                    performance_metrics.record_error()
                
                # Small random delay to create realistic timing
                await asyncio.sleep(0.001)
        
        # Run 10 concurrent event emitters
        num_emitters = 10
        events_per_emitter = 20
        
        await asyncio.gather(*[
            event_emitter(emitter_id, events_per_emitter)
            for emitter_id in range(num_emitters)
        ])
        
        # Allow event processing
        await asyncio.sleep(0.5)
        
        # Verify events were delivered
        total_messages_delivered = sum(
            len(ws.sent_messages) + len(ws.sent_bytes)
            for _, ws in clients
        )
        
        expected_events = num_emitters * events_per_emitter
        assert total_messages_delivered > 0, "No events were delivered"
        
        # With 10 clients and proper filtering, should see significant delivery
        min_expected_deliveries = expected_events * num_clients * 0.1  # At least 10%
        assert total_messages_delivered >= min_expected_deliveries, \
            f"Too few deliveries: {total_messages_delivered} < {min_expected_deliveries}"
        
        await streaming_service.stop()
        performance_metrics.stop_monitoring()
        
        # Verify concurrent event processing performance
        performance_metrics.assert_performance_requirements({
            "max_response_time": 1.0,    # Max 1 second per event emission
            "avg_response_time": 0.1,    # Avg 100ms per event
            "min_throughput": 50.0,      # Min 50 events per second
            "max_error_rate": 0.05       # Max 5% error rate
        })


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])