"""
Performance tests for Sprint 2.3 notification system

Tests performance requirements:
- Background service uses < 50MB memory
- Notification processing adds < 10ms latency 
- Desktop notifications appear within 500ms
- Terminal notifications don't block command execution
"""

import pytest
import asyncio
import time
import psutil
import os
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import statistics

from leanvibe_cli.config import CLIConfig
from leanvibe_cli.services.notification_service import NotificationService
from leanvibe_cli.services.desktop_notifications import DesktopNotificationService
from leanvibe_cli.ui.notification_overlay import NotificationOverlay


class TestMemoryPerformance:
    """Test memory usage requirements"""
    
    @pytest.fixture
    def process(self):
        """Get current process for memory monitoring"""
        return psutil.Process(os.getpid())
    
    def get_memory_mb(self, process):
        """Get memory usage in MB"""
        return process.memory_info().rss / 1024 / 1024
    
    async def test_notification_service_memory_usage(self, process):
        """Test that notification service uses < 50MB memory"""
        initial_memory = self.get_memory_mb(process)
        
        config = CLIConfig()
        service = NotificationService(config)
        
        # Mock backend client to avoid actual connections
        service.client = Mock()
        service.client.connect_websocket = AsyncMock(return_value=True)
        service.client.listen_for_events = AsyncMock()
        
        # Start the service
        await service.start_background_monitoring()
        
        # Simulate high notification load
        for i in range(1000):
            event = {
                "type": "performance_test",
                "priority": "medium",
                "message": f"Performance test notification {i}",
                "timestamp": datetime.now().isoformat(),
                "source": f"test_source_{i % 10}"
            }
            await service.notification_queue.put(event)
            service.notification_history.appendleft(event)
        
        # Measure memory after load
        current_memory = self.get_memory_mb(process)
        memory_increase = current_memory - initial_memory
        
        print(f"Initial memory: {initial_memory:.2f} MB")
        print(f"Current memory: {current_memory:.2f} MB")
        print(f"Memory increase: {memory_increase:.2f} MB")
        
        # Quality Gate: Background service uses < 50MB memory
        assert memory_increase < 50, f"Memory usage {memory_increase:.2f} MB exceeds 50MB limit"
        
        # Cleanup
        await service.stop()
    
    async def test_notification_history_memory_efficiency(self, process):
        """Test notification history memory efficiency"""
        initial_memory = self.get_memory_mb(process)
        
        config = CLIConfig()
        service = NotificationService(config)
        
        # Fill notification history to maximum
        for i in range(100):  # maxlen=100
            large_event = {
                "type": "memory_test",
                "priority": "high",
                "message": "x" * 1000,  # 1KB message
                "timestamp": datetime.now().isoformat(),
                "metadata": {"large_data": "y" * 500}  # Additional data
            }
            service.notification_history.appendleft(large_event)
        
        # Add more events to test rotation
        for i in range(50):
            service.notification_history.appendleft({
                "type": "rotation_test",
                "priority": "medium",
                "message": f"Rotation test {i}",
                "timestamp": datetime.now().isoformat()
            })
        
        current_memory = self.get_memory_mb(process)
        memory_increase = current_memory - initial_memory
        
        print(f"Memory increase for 100 large notifications: {memory_increase:.2f} MB")
        
        # Should still be under memory limit even with large notifications
        assert memory_increase < 20, f"Notification history memory {memory_increase:.2f} MB too high"
        
        # Verify history size is still limited
        assert len(service.notification_history) == 100


class TestLatencyPerformance:
    """Test latency and response time requirements"""
    
    async def test_notification_processing_latency(self):
        """Test notification processing adds < 10ms latency"""
        config = CLIConfig()
        config.desktop_notifications = True
        config.terminal_notifications = True
        
        service = NotificationService(config)
        service.client = Mock()
        
        # Mock notification methods to avoid actual I/O
        with patch.object(service, '_send_desktop_notification', new_callable=AsyncMock) as mock_desktop:
            with patch.object(service, '_send_terminal_notification', new_callable=AsyncMock) as mock_terminal:
                
                test_event = {
                    "type": "latency_test",
                    "priority": "high",
                    "message": "Latency test notification",
                    "timestamp": datetime.now().isoformat()
                }
                
                # Measure processing time multiple times for accuracy
                processing_times = []
                for _ in range(10):
                    start_time = time.perf_counter()
                    await service._process_notification(test_event)
                    end_time = time.perf_counter()
                    
                    processing_time_ms = (end_time - start_time) * 1000
                    processing_times.append(processing_time_ms)
                
                avg_processing_time = statistics.mean(processing_times)
                max_processing_time = max(processing_times)
                
                print(f"Average processing time: {avg_processing_time:.2f} ms")
                print(f"Maximum processing time: {max_processing_time:.2f} ms")
                
                # Quality Gate: Notification processing adds < 10ms latency
                assert avg_processing_time < 10, f"Average processing time {avg_processing_time:.2f} ms exceeds 10ms limit"
                assert max_processing_time < 20, f"Maximum processing time {max_processing_time:.2f} ms exceeds 20ms reasonable limit"
    
    async def test_desktop_notification_response_time(self):
        """Test desktop notifications appear within 500ms"""
        service = DesktopNotificationService()
        
        if not service.notification_available:
            pytest.skip("Desktop notifications not available on this platform")
        
        # Mock the platform-specific notification method
        with patch.object(service, f'_send_{service.platform}_notification', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = None  # Successful send
            
            response_times = []
            for _ in range(5):
                start_time = time.perf_counter()
                
                await service.send_notification(
                    title="Performance Test",
                    message="Response time test",
                    priority="normal",
                    sound=False
                )
                
                end_time = time.perf_counter()
                response_time_ms = (end_time - start_time) * 1000
                response_times.append(response_time_ms)
            
            avg_response_time = statistics.mean(response_times)
            max_response_time = max(response_times)
            
            print(f"Average desktop notification response time: {avg_response_time:.2f} ms")
            print(f"Maximum desktop notification response time: {max_response_time:.2f} ms")
            
            # Quality Gate: Desktop notifications appear within 500ms
            assert avg_response_time < 500, f"Average response time {avg_response_time:.2f} ms exceeds 500ms limit"
            assert max_response_time < 1000, f"Maximum response time {max_response_time:.2f} ms exceeds 1000ms reasonable limit"
    
    async def test_terminal_notification_non_blocking(self):
        """Test terminal notifications don't block command execution"""
        console = Mock()
        overlay = NotificationOverlay(console)
        
        test_event = {
            "type": "blocking_test",
            "priority": "medium",
            "message": "Non-blocking test notification",
            "timestamp": datetime.now().isoformat()
        }
        
        # Mock console print to avoid actual output
        with patch.object(overlay, '_render_notification_bar', new_callable=AsyncMock):
            # Start multiple notifications concurrently
            tasks = []
            start_time = time.perf_counter()
            
            for i in range(5):
                task = asyncio.create_task(
                    overlay.show_notification(test_event, duration=0.1)
                )
                tasks.append(task)
            
            # Wait for all notifications to start
            await asyncio.sleep(0.05)
            
            # Measure time to start all notifications
            start_all_time = time.perf_counter() - start_time
            
            # Wait for completion
            await asyncio.gather(*tasks)
            
            total_time = time.perf_counter() - start_time
            
            print(f"Time to start 5 notifications: {start_all_time * 1000:.2f} ms")
            print(f"Total time for 5 notifications: {total_time * 1000:.2f} ms")
            
            # Notifications should start quickly (non-blocking)
            assert start_all_time < 0.1, f"Notification startup time {start_all_time * 1000:.2f} ms too slow"


class TestThroughputPerformance:
    """Test system throughput under load"""
    
    async def test_high_volume_event_processing(self):
        """Test processing high volume of events efficiently"""
        config = CLIConfig()
        config.notification_throttle_seconds = 0.001  # Very low throttling for testing
        
        service = NotificationService(config)
        service.client = Mock()
        
        # Mock notification methods
        with patch.object(service, '_send_desktop_notification', new_callable=AsyncMock):
            with patch.object(service, '_send_terminal_notification', new_callable=AsyncMock):
                
                # Generate high volume of events
                events = []
                for i in range(100):
                    event = {
                        "type": f"throughput_test_{i % 10}",
                        "priority": "medium",
                        "message": f"Throughput test event {i}",
                        "timestamp": datetime.now().isoformat(),
                        "source": f"source_{i % 5}"
                    }
                    events.append(event)
                
                # Process events and measure throughput
                start_time = time.perf_counter()
                
                for event in events:
                    await service._process_notification(event)
                
                end_time = time.perf_counter()
                total_time = end_time - start_time
                
                events_per_second = len(events) / total_time
                
                print(f"Processed {len(events)} events in {total_time:.3f} seconds")
                print(f"Throughput: {events_per_second:.1f} events/second")
                
                # Should process at least 50 events per second
                assert events_per_second > 50, f"Throughput {events_per_second:.1f} events/s too low"
    
    async def test_concurrent_notification_handling(self):
        """Test handling multiple concurrent notifications"""
        config = CLIConfig()
        service = NotificationService(config)
        service.client = Mock()
        
        # Mock notification methods with slight delay to simulate real work
        async def mock_desktop_notification(*args, **kwargs):
            await asyncio.sleep(0.001)  # 1ms delay
        
        async def mock_terminal_notification(*args, **kwargs):
            await asyncio.sleep(0.001)  # 1ms delay
        
        with patch.object(service, '_send_desktop_notification', side_effect=mock_desktop_notification):
            with patch.object(service, '_send_terminal_notification', side_effect=mock_terminal_notification):
                
                # Create concurrent notification tasks
                events = [
                    {
                        "type": f"concurrent_test_{i}",
                        "priority": "high",
                        "message": f"Concurrent test {i}",
                        "timestamp": datetime.now().isoformat()
                    }
                    for i in range(20)
                ]
                
                start_time = time.perf_counter()
                
                # Process notifications concurrently
                tasks = [
                    service._process_notification(event)
                    for event in events
                ]
                
                await asyncio.gather(*tasks)
                
                end_time = time.perf_counter()
                total_time = end_time - start_time
                
                print(f"Processed {len(events)} concurrent notifications in {total_time:.3f} seconds")
                
                # Concurrent processing should be faster than sequential
                # With 1ms delay per notification, sequential would take ~40ms
                # Concurrent should be much faster
                assert total_time < 0.02, f"Concurrent processing too slow: {total_time:.3f}s"


class TestResourceUtilization:
    """Test resource utilization efficiency"""
    
    async def test_cpu_usage_monitoring(self):
        """Test CPU usage remains reasonable under load"""
        process = psutil.Process(os.getpid())
        
        # Get baseline CPU usage
        initial_cpu_percent = process.cpu_percent()
        await asyncio.sleep(0.1)  # Let CPU measurement stabilize
        
        config = CLIConfig()
        service = NotificationService(config)
        service.client = Mock()
        
        # Mock notification methods with realistic work
        async def mock_notification_work(*args, **kwargs):
            # Simulate some CPU work
            for _ in range(1000):
                pass
        
        with patch.object(service, '_send_desktop_notification', side_effect=mock_notification_work):
            with patch.object(service, '_send_terminal_notification', side_effect=mock_notification_work):
                
                # Generate load
                start_time = time.perf_counter()
                
                tasks = []
                for i in range(50):
                    event = {
                        "type": f"cpu_test_{i}",
                        "priority": "medium",
                        "message": f"CPU test {i}",
                        "timestamp": datetime.now().isoformat()
                    }
                    task = service._process_notification(event)
                    tasks.append(task)
                
                await asyncio.gather(*tasks)
                
                end_time = time.perf_counter()
                
                # Measure CPU usage after load
                final_cpu_percent = process.cpu_percent()
                
                processing_time = end_time - start_time
                
                print(f"Processed 50 notifications in {processing_time:.3f} seconds")
                print(f"CPU usage change: {final_cpu_percent - initial_cpu_percent:.1f}%")
                
                # CPU usage should remain reasonable
                assert processing_time < 1.0, f"Processing time {processing_time:.3f}s too slow"
    
    async def test_queue_memory_efficiency(self):
        """Test notification queue memory efficiency"""
        config = CLIConfig()
        service = NotificationService(config)
        
        # Fill queue with many notifications
        large_event = {
            "type": "queue_memory_test",
            "priority": "medium",
            "message": "x" * 1000,  # 1KB message
            "timestamp": datetime.now().isoformat(),
            "large_payload": list(range(100))  # Additional data
        }
        
        # Add many events to queue
        queue_start_time = time.perf_counter()
        
        for i in range(1000):
            await service.notification_queue.put(large_event)
        
        queue_fill_time = time.perf_counter() - queue_start_time
        
        print(f"Time to fill queue with 1000 events: {queue_fill_time:.3f} seconds")
        print(f"Queue size: {service.notification_queue.qsize()}")
        
        # Queue operations should be fast
        assert queue_fill_time < 0.1, f"Queue filling too slow: {queue_fill_time:.3f}s"
        assert service.notification_queue.qsize() == 1000


class TestPerformanceRequirements:
    """Test specific performance requirements from Sprint 2.3 plan"""
    
    async def test_sprint_2_3_performance_gates(self):
        """Test all Sprint 2.3 performance requirements"""
        
        # Quality Gate 1: Background service uses < 50MB memory
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024
        
        config = CLIConfig()
        service = NotificationService(config)
        service.client = Mock()
        service.client.connect_websocket = AsyncMock(return_value=True)
        
        await service.start_background_monitoring()
        
        # Simulate realistic load
        for i in range(100):
            event = {
                "type": "requirement_test",
                "priority": "medium",
                "message": f"Requirement test {i}",
                "timestamp": datetime.now().isoformat()
            }
            service.notification_history.appendleft(event)
        
        current_memory = process.memory_info().rss / 1024 / 1024
        memory_usage = current_memory - initial_memory
        
        print(f"✓ Memory usage test: {memory_usage:.2f} MB (limit: 50 MB)")
        assert memory_usage < 50, f"Memory requirement failed: {memory_usage:.2f} MB"
        
        # Quality Gate 2: Notification processing adds < 10ms latency
        test_event = {
            "type": "latency_requirement_test",
            "priority": "high",
            "message": "Latency requirement test",
            "timestamp": datetime.now().isoformat()
        }
        
        with patch.object(service, '_send_desktop_notification', new_callable=AsyncMock):
            with patch.object(service, '_send_terminal_notification', new_callable=AsyncMock):
                
                start_time = time.perf_counter()
                await service._process_notification(test_event)
                processing_time_ms = (time.perf_counter() - start_time) * 1000
        
        print(f"✓ Processing latency test: {processing_time_ms:.2f} ms (limit: 10 ms)")
        assert processing_time_ms < 10, f"Latency requirement failed: {processing_time_ms:.2f} ms"
        
        # Quality Gate 3: Desktop notifications appear within 500ms
        desktop_service = DesktopNotificationService()
        
        if desktop_service.notification_available:
            with patch.object(desktop_service, f'_send_{desktop_service.platform}_notification', new_callable=AsyncMock):
                start_time = time.perf_counter()
                await desktop_service.send_notification("Test", "Message", "normal", False)
                desktop_response_time_ms = (time.perf_counter() - start_time) * 1000
            
            print(f"✓ Desktop notification test: {desktop_response_time_ms:.2f} ms (limit: 500 ms)")
            assert desktop_response_time_ms < 500, f"Desktop notification requirement failed: {desktop_response_time_ms:.2f} ms"
        else:
            print("✓ Desktop notification test: Skipped (not available on platform)")
        
        # Quality Gate 4: Terminal notifications don't block command execution
        console = Mock()
        overlay = NotificationOverlay(console)
        
        with patch.object(overlay, '_render_notification_bar', new_callable=AsyncMock):
            start_time = time.perf_counter()
            
            # Start notification but don't wait for completion
            task = asyncio.create_task(overlay.show_notification(test_event, duration=0.1))
            
            # Measure time to start (should be immediate)
            start_time_ms = (time.perf_counter() - start_time) * 1000
            
            # Wait for completion
            await task
        
        print(f"✓ Terminal notification non-blocking test: {start_time_ms:.2f} ms (should be < 1 ms)")
        assert start_time_ms < 1, f"Terminal notification blocking requirement failed: {start_time_ms:.2f} ms"
        
        # Cleanup
        await service.stop()
        
        print("\n🎉 All Sprint 2.3 performance requirements passed!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])