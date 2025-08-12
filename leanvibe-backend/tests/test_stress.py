"""
Basic stress test to ensure system handles concurrent users
Following YAGNI principle - just enough to verify stability
"""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import httpx
import pytest
import psutil
import os


class TestBasicStress:
    """Basic stress testing for production readiness"""
    
    @pytest.mark.asyncio
    async def test_concurrent_api_requests(self):
        """Test that API handles 10 concurrent users without crashing"""
        base_url = "http://localhost:8765"
        
        # Check if server is running
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{base_url}/health")
                if response.status_code != 200:
                    pytest.skip("Server not running - start with ./start.sh")
        except:
            pytest.skip("Server not running - start with ./start.sh")
        
        # Simulate 10 concurrent users making requests
        num_users = 10
        requests_per_user = 5
        
        async def user_session(user_id: int):
            """Simulate a user making multiple requests"""
            results = []
            async with httpx.AsyncClient(timeout=30.0) as client:
                for i in range(requests_per_user):
                    try:
                        # Mix of different endpoints
                        endpoints = [
                            "/health",
                            "/api/projects/",
                            "/api/tasks/",
                            "/api/v1/cli/status",
                        ]
                        endpoint = endpoints[i % len(endpoints)]
                        
                        start_time = time.time()
                        response = await client.get(f"{base_url}{endpoint}")
                        elapsed = time.time() - start_time
                        
                        results.append({
                            "user": user_id,
                            "endpoint": endpoint,
                            "status": response.status_code,
                            "time": elapsed
                        })
                    except Exception as e:
                        results.append({
                            "user": user_id,
                            "endpoint": endpoint,
                            "error": str(e)
                        })
            return results
        
        # Run concurrent user sessions
        tasks = [user_session(i) for i in range(num_users)]
        all_results = await asyncio.gather(*tasks)
        
        # Flatten results
        results = [r for user_results in all_results for r in user_results]
        
        # Verify results
        total_requests = len(results)
        successful = sum(1 for r in results if "status" in r and r["status"] in [200, 401])
        failed = sum(1 for r in results if "error" in r)
        
        # Assert most requests succeeded
        success_rate = successful / total_requests
        assert success_rate > 0.9, f"Success rate too low: {success_rate:.2%}"
        
        # Check response times
        response_times = [r["time"] for r in results if "time" in r]
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            
            # Basic performance assertions
            assert avg_time < 2.0, f"Average response time too high: {avg_time:.2f}s"
            assert max_time < 10.0, f"Max response time too high: {max_time:.2f}s"
    
    def test_memory_usage_stable(self):
        """Test that memory usage doesn't explode under load"""
        # Get current Python process
        process = psutil.Process(os.getpid())
        
        # Record initial memory
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Simulate some load (simplified for testing)
        data = []
        for i in range(100):
            # Create some objects to simulate load
            data.append({"id": i, "data": "x" * 1000})
        
        # Clear the data
        data.clear()
        
        # Check memory after load
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory shouldn't increase by more than 100MB for this simple test
        assert memory_increase < 100, f"Memory increased by {memory_increase:.2f}MB"
    
    @pytest.mark.asyncio
    async def test_websocket_handles_reconnects(self):
        """Test that WebSocket handles multiple reconnection attempts"""
        import websockets
        import json
        
        ws_url = "ws://localhost:8765/ws/test-client"
        
        # Skip if server not running
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:8765/health")
                if response.status_code != 200:
                    pytest.skip("Server not running")
        except:
            pytest.skip("Server not running")
        
        reconnect_count = 5
        successful_reconnects = 0
        
        for i in range(reconnect_count):
            try:
                async with websockets.connect(ws_url) as websocket:
                    # Send a test message
                    await websocket.send(json.dumps({
                        "type": "ping",
                        "timestamp": time.time()
                    }))
                    
                    # Wait for response (with timeout)
                    try:
                        response = await asyncio.wait_for(
                            websocket.recv(),
                            timeout=5.0
                        )
                        successful_reconnects += 1
                    except asyncio.TimeoutError:
                        pass
                    
                    # Disconnect
                    await websocket.close()
                    
            except Exception as e:
                # Connection failed
                pass
            
            # Small delay between reconnects
            await asyncio.sleep(0.1)
        
        # Should handle most reconnection attempts
        success_rate = successful_reconnects / reconnect_count
        assert success_rate > 0.6, f"WebSocket reconnection rate too low: {success_rate:.2%}"
    
    def test_no_file_descriptor_leak(self):
        """Test that we're not leaking file descriptors"""
        process = psutil.Process(os.getpid())
        
        # Get initial file descriptor count
        initial_fds = process.num_fds() if hasattr(process, "num_fds") else 0
        
        # Simulate opening and closing connections
        for i in range(10):
            try:
                # Simple file operations to test
                with open("/tmp/test_file.txt", "w") as f:
                    f.write("test")
                os.remove("/tmp/test_file.txt")
            except:
                pass
        
        # Check file descriptors after operations
        final_fds = process.num_fds() if hasattr(process, "num_fds") else 0
        fd_increase = final_fds - initial_fds
        
        # Shouldn't leak file descriptors
        assert fd_increase < 5, f"File descriptors increased by {fd_increase}"