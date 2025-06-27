#!/usr/bin/env python3
"""
End-to-End MVP Testing Suite

Comprehensive testing of the LeenVibe coding assistant MVP:
- REST API functionality
- WebSocket functionality  
- Performance characteristics
- Error handling
- iOS compatibility scenarios
"""

import asyncio
import json
import time
import aiohttp
import websockets
import sys
from typing import List, Dict, Any
import statistics

class MVPTestSuite:
    """Complete MVP testing suite"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.ws_url = "ws://localhost:8000/ws"
        self.results = []
        
    async def test_health_endpoint(self) -> bool:
        """Test basic health endpoint"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        health_ok = data.get("status") == "healthy"
                        ai_ready = data.get("ai_ready", False)
                        
                        print(f"✅ Health endpoint: {response.status}")
                        print(f"   AI Ready: {ai_ready}")
                        print(f"   Service: {data.get('service')}")
                        print(f"   Version: {data.get('version')}")
                        
                        return health_ok and ai_ready
                    else:
                        print(f"❌ Health endpoint failed: {response.status}")
                        return False
        except Exception as e:
            print(f"❌ Health endpoint error: {e}")
            return False
    
    async def test_rest_api_performance(self) -> Dict[str, Any]:
        """Test REST API performance across all intents"""
        
        print("\n📊 Testing REST API Performance")
        
        test_requests = [
            {
                "intent": "suggest",
                "payload": {
                    "file_path": "/test/performance.py",
                    "cursor_position": 100,
                    "intent": "suggest",
                    "content": "def optimize_algorithm(data):\n    # TODO: implement efficient algorithm\n    pass",
                    "language": "python"
                }
            },
            {
                "intent": "explain", 
                "payload": {
                    "file_path": "/test/complex.py",
                    "cursor_position": 200,
                    "intent": "explain",
                    "content": "class DataProcessor:\n    def __init__(self, config):\n        self.config = config\n    def process(self, data):\n        return [item * 2 for item in data if item > 0]",
                    "language": "python"
                }
            },
            {
                "intent": "refactor",
                "payload": {
                    "file_path": "/test/legacy.py", 
                    "cursor_position": 150,
                    "intent": "refactor",
                    "content": "def old_function(x, y, z):\n    if x > 0:\n        if y > 0:\n            if z > 0:\n                return x + y + z\n    return 0",
                    "language": "python"
                }
            },
            {
                "intent": "debug",
                "payload": {
                    "file_path": "/test/buggy.py",
                    "cursor_position": 75,
                    "intent": "debug", 
                    "content": "def divide_numbers(a, b):\n    result = a / b\n    return result",
                    "language": "python"
                }
            },
            {
                "intent": "optimize",
                "payload": {
                    "file_path": "/test/slow.py",
                    "cursor_position": 300,
                    "intent": "optimize",
                    "content": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
                    "language": "python"
                }
            }
        ]
        
        results = {}
        
        async with aiohttp.ClientSession() as session:
            for test_case in test_requests:
                intent = test_case["intent"]
                payload = test_case["payload"]
                
                start_time = time.time()
                
                try:
                    async with session.post(
                        f"{self.base_url}/api/code-completion",
                        json=payload,
                        headers={"Content-Type": "application/json"}
                    ) as response:
                        
                        elapsed = (time.time() - start_time) * 1000
                        
                        if response.status == 200:
                            data = await response.json()
                            server_time = data.get("processing_time_ms", 0)
                            confidence = data.get("confidence", 0)
                            
                            results[intent] = {
                                "success": True,
                                "client_time_ms": elapsed,
                                "server_time_ms": server_time,
                                "confidence": confidence,
                                "response_length": len(data.get("response", ""))
                            }
                            
                            print(f"   ✅ {intent}: {elapsed:.1f}ms (server: {server_time:.1f}ms, conf: {confidence:.2f})")
                            
                        else:
                            results[intent] = {
                                "success": False,
                                "error": f"HTTP {response.status}",
                                "client_time_ms": elapsed
                            }
                            print(f"   ❌ {intent}: Failed with {response.status}")
                            
                except Exception as e:
                    results[intent] = {
                        "success": False,
                        "error": str(e),
                        "client_time_ms": (time.time() - start_time) * 1000
                    }
                    print(f"   ❌ {intent}: Exception - {e}")
        
        # Calculate performance statistics
        successful_tests = [r for r in results.values() if r.get("success")]
        if successful_tests:
            client_times = [r["client_time_ms"] for r in successful_tests]
            server_times = [r["server_time_ms"] for r in successful_tests if "server_time_ms" in r]
            confidences = [r["confidence"] for r in successful_tests if "confidence" in r]
            
            performance_stats = {
                "total_tests": len(test_requests),
                "successful_tests": len(successful_tests),
                "success_rate": len(successful_tests) / len(test_requests),
                "avg_client_time_ms": statistics.mean(client_times) if client_times else 0,
                "max_client_time_ms": max(client_times) if client_times else 0,
                "avg_server_time_ms": statistics.mean(server_times) if server_times else 0,
                "avg_confidence": statistics.mean(confidences) if confidences else 0,
                "min_confidence": min(confidences) if confidences else 0
            }
            
            print(f"\n📈 REST API Performance Summary:")
            print(f"   Success Rate: {performance_stats['success_rate']*100:.1f}%")
            print(f"   Avg Client Time: {performance_stats['avg_client_time_ms']:.1f}ms")
            print(f"   Max Client Time: {performance_stats['max_client_time_ms']:.1f}ms") 
            print(f"   Avg Server Time: {performance_stats['avg_server_time_ms']:.1f}ms")
            print(f"   Avg Confidence: {performance_stats['avg_confidence']:.2f}")
            
            return performance_stats
        else:
            return {"success_rate": 0, "total_tests": len(test_requests)}
    
    async def test_websocket_performance(self) -> Dict[str, Any]:
        """Test WebSocket performance and concurrent connections"""
        
        print("\n🔌 Testing WebSocket Performance")
        
        # Test single connection performance
        single_conn_results = await self._test_single_websocket_performance()
        
        # Test concurrent connections
        concurrent_results = await self._test_concurrent_websocket_connections()
        
        return {
            "single_connection": single_conn_results,
            "concurrent_connections": concurrent_results
        }
    
    async def _test_single_websocket_performance(self) -> Dict[str, Any]:
        """Test single WebSocket connection performance"""
        
        uri = f"{self.ws_url}/test-perf-single"
        
        try:
            async with websockets.connect(uri) as websocket:
                # Test multiple requests through same connection
                request_times = []
                
                for i in range(5):
                    test_request = {
                        "type": "code_completion",
                        "file_path": f"/test/perf_{i}.py",
                        "cursor_position": 100,
                        "intent": "suggest",
                        "content": f"def test_function_{i}():\n    # TODO: implement test {i}\n    pass",
                        "language": "python"
                    }
                    
                    start_time = time.time()
                    await websocket.send(json.dumps(test_request))
                    
                    response = await websocket.recv()
                    elapsed = (time.time() - start_time) * 1000
                    
                    response_data = json.loads(response)
                    
                    if response_data.get("status") == "success":
                        request_times.append(elapsed)
                        print(f"   ✅ Request {i+1}: {elapsed:.1f}ms")
                    else:
                        print(f"   ❌ Request {i+1}: Failed")
                
                if request_times:
                    return {
                        "success": True,
                        "total_requests": len(request_times),
                        "avg_time_ms": statistics.mean(request_times),
                        "max_time_ms": max(request_times),
                        "min_time_ms": min(request_times)
                    }
                else:
                    return {"success": False, "error": "No successful requests"}
                    
        except Exception as e:
            print(f"   ❌ Single WebSocket test failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _test_concurrent_websocket_connections(self) -> Dict[str, Any]:
        """Test concurrent WebSocket connections"""
        
        async def single_concurrent_test(client_id: int) -> Dict[str, Any]:
            uri = f"{self.ws_url}/test-concurrent-{client_id}"
            
            try:
                async with websockets.connect(uri) as websocket:
                    test_request = {
                        "type": "code_completion", 
                        "file_path": f"/test/concurrent_{client_id}.py",
                        "cursor_position": 50,
                        "intent": "suggest",
                        "content": f"# Client {client_id} test\ndef client_{client_id}_function():\n    pass",
                        "language": "python"
                    }
                    
                    start_time = time.time()
                    await websocket.send(json.dumps(test_request))
                    
                    response = await websocket.recv()
                    elapsed = (time.time() - start_time) * 1000
                    
                    response_data = json.loads(response)
                    
                    return {
                        "client_id": client_id,
                        "success": response_data.get("status") == "success",
                        "time_ms": elapsed
                    }
                    
            except Exception as e:
                return {
                    "client_id": client_id,
                    "success": False,
                    "error": str(e)
                }
        
        # Test 3 concurrent connections
        concurrent_tasks = [single_concurrent_test(i) for i in range(3)]
        concurrent_results = await asyncio.gather(*concurrent_tasks, return_exceptions=True)
        
        successful_results = [r for r in concurrent_results if isinstance(r, dict) and r.get("success")]
        
        if successful_results:
            times = [r["time_ms"] for r in successful_results]
            print(f"   ✅ Concurrent: {len(successful_results)}/3 successful")
            print(f"   Avg Time: {statistics.mean(times):.1f}ms")
            
            return {
                "success": True,
                "total_connections": 3,
                "successful_connections": len(successful_results),
                "avg_time_ms": statistics.mean(times),
                "max_time_ms": max(times)
            }
        else:
            print(f"   ❌ Concurrent: 0/3 successful")
            return {"success": False, "total_connections": 3, "successful_connections": 0}
    
    async def test_error_handling(self) -> Dict[str, Any]:
        """Test comprehensive error handling scenarios"""
        
        print("\n🚨 Testing Error Handling")
        
        error_tests = []
        
        # Test invalid REST requests
        async with aiohttp.ClientSession() as session:
            # Missing required fields
            try:
                async with session.post(
                    f"{self.base_url}/api/code-completion",
                    json={"cursor_position": 100},
                    headers={"Content-Type": "application/json"}
                ) as response:
                    error_tests.append({
                        "test": "missing_file_path",
                        "expected_status": 422,
                        "actual_status": response.status,
                        "success": response.status == 422
                    })
                    print(f"   ✅ Missing file_path: {response.status} (expected 422)")
            except Exception as e:
                error_tests.append({"test": "missing_file_path", "success": False, "error": str(e)})
            
            # Invalid intent
            try:
                async with session.post(
                    f"{self.base_url}/api/code-completion",
                    json={
                        "file_path": "/test/file.py",
                        "intent": "invalid_intent"
                    },
                    headers={"Content-Type": "application/json"}
                ) as response:
                    error_tests.append({
                        "test": "invalid_intent",
                        "expected_status": 422,
                        "actual_status": response.status,
                        "success": response.status == 422
                    })
                    print(f"   ✅ Invalid intent: {response.status} (expected 422)")
            except Exception as e:
                error_tests.append({"test": "invalid_intent", "success": False, "error": str(e)})
        
        # Test WebSocket error handling
        try:
            uri = f"{self.ws_url}/test-error-handling"
            async with websockets.connect(uri) as websocket:
                # Invalid message format
                await websocket.send("invalid json")
                response = await websocket.recv()
                response_data = json.loads(response)
                
                error_tests.append({
                    "test": "websocket_invalid_json",
                    "success": response_data.get("status") == "error",
                    "response": response_data
                })
                print(f"   ✅ WebSocket invalid JSON handled")
                
                # Missing required fields
                invalid_request = {"type": "code_completion"}  # Missing file_path
                await websocket.send(json.dumps(invalid_request))
                response = await websocket.recv()
                response_data = json.loads(response)
                
                error_tests.append({
                    "test": "websocket_missing_fields",
                    "success": response_data.get("status") == "error",
                    "response": response_data
                })
                print(f"   ✅ WebSocket missing fields handled")
                
        except Exception as e:
            error_tests.append({"test": "websocket_errors", "success": False, "error": str(e)})
        
        successful_error_tests = sum(1 for test in error_tests if test.get("success"))
        
        return {
            "total_error_tests": len(error_tests),
            "successful_error_tests": successful_error_tests,
            "error_handling_success_rate": successful_error_tests / len(error_tests) if error_tests else 0,
            "details": error_tests
        }
    
    async def test_ios_compatibility(self) -> Dict[str, Any]:
        """Test iOS app compatibility scenarios"""
        
        print("\n📱 Testing iOS Compatibility")
        
        ios_scenarios = [
            {
                "name": "Swift Code Suggestion",
                "message": {
                    "type": "code_completion",
                    "file_path": "/iOS/ViewController.swift",
                    "cursor_position": 200,
                    "intent": "suggest",
                    "content": "class ViewController: UIViewController {\n    override func viewDidLoad() {\n        super.viewDidLoad()\n        // TODO: setup UI\n    }\n}",
                    "language": "swift"
                }
            },
            {
                "name": "JavaScript Code Explanation",
                "message": {
                    "type": "code_completion",
                    "file_path": "/web/app.js",
                    "cursor_position": 150,
                    "intent": "explain",
                    "content": "const fetchData = async (url) => {\n    const response = await fetch(url);\n    return response.json();\n};",
                    "language": "javascript"
                }
            },
            {
                "name": "Large File Content",
                "message": {
                    "type": "code_completion",
                    "file_path": "/test/large_file.py",
                    "cursor_position": 1000,
                    "intent": "refactor",
                    "content": "# Large file simulation\n" + "def function_{}():\n    pass\n".replace("{}", "{}") * 50,
                    "language": "python"
                }
            }
        ]
        
        compatibility_results = []
        
        uri = f"{self.ws_url}/ios-compatibility-test"
        
        try:
            async with websockets.connect(uri) as websocket:
                for scenario in ios_scenarios:
                    start_time = time.time()
                    
                    await websocket.send(json.dumps(scenario["message"]))
                    response = await websocket.recv()
                    
                    elapsed = (time.time() - start_time) * 1000
                    response_data = json.loads(response)
                    
                    success = response_data.get("status") == "success"
                    
                    compatibility_results.append({
                        "scenario": scenario["name"],
                        "success": success,
                        "time_ms": elapsed,
                        "confidence": response_data.get("confidence", 0) if success else None,
                        "response_size": len(response_data.get("response", "")) if success else 0
                    })
                    
                    status_emoji = "✅" if success else "❌"
                    print(f"   {status_emoji} {scenario['name']}: {elapsed:.1f}ms")
                    
        except Exception as e:
            print(f"   ❌ iOS compatibility test failed: {e}")
            return {"success": False, "error": str(e)}
        
        successful_scenarios = sum(1 for result in compatibility_results if result["success"])
        
        return {
            "total_scenarios": len(ios_scenarios),
            "successful_scenarios": successful_scenarios,
            "compatibility_success_rate": successful_scenarios / len(ios_scenarios),
            "avg_response_time_ms": statistics.mean([r["time_ms"] for r in compatibility_results if r["success"]]) if successful_scenarios > 0 else 0,
            "details": compatibility_results
        }
    
    async def run_full_test_suite(self) -> Dict[str, Any]:
        """Run the complete MVP test suite"""
        
        print("🚀 LeenVibe MVP End-to-End Test Suite")
        print("=" * 60)
        
        # Test health first
        health_ok = await self.test_health_endpoint()
        if not health_ok:
            print("\n❌ Health check failed - aborting test suite")
            return {"success": False, "reason": "Health check failed"}
        
        # Run all test categories
        rest_performance = await self.test_rest_api_performance()
        ws_performance = await self.test_websocket_performance()
        error_handling = await self.test_error_handling()
        ios_compatibility = await self.test_ios_compatibility()
        
        # Calculate overall results
        overall_success = (
            rest_performance.get("success_rate", 0) > 0.8 and
            ws_performance.get("single_connection", {}).get("success", False) and
            ws_performance.get("concurrent_connections", {}).get("success", False) and
            error_handling.get("error_handling_success_rate", 0) > 0.8 and
            ios_compatibility.get("compatibility_success_rate", 0) > 0.8
        )
        
        results = {
            "overall_success": overall_success,
            "timestamp": time.time(),
            "health_check": health_ok,
            "rest_api_performance": rest_performance,
            "websocket_performance": ws_performance,
            "error_handling": error_handling,
            "ios_compatibility": ios_compatibility
        }
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 MVP Test Suite Summary")
        print(f"   Overall Success: {'✅ PASS' if overall_success else '❌ FAIL'}")
        print(f"   REST API Success Rate: {rest_performance.get('success_rate', 0)*100:.1f}%")
        print(f"   WebSocket Single Connection: {'✅' if ws_performance.get('single_connection', {}).get('success') else '❌'}")
        print(f"   WebSocket Concurrent: {'✅' if ws_performance.get('concurrent_connections', {}).get('success') else '❌'}")
        print(f"   Error Handling: {error_handling.get('error_handling_success_rate', 0)*100:.1f}%")
        print(f"   iOS Compatibility: {ios_compatibility.get('compatibility_success_rate', 0)*100:.1f}%")
        
        return results

async def main():
    """Run MVP test suite"""
    test_suite = MVPTestSuite()
    results = await test_suite.run_full_test_suite()
    
    if results.get("overall_success"):
        print("\n🎉 MVP TEST SUITE PASSED! 🎉")
        print("🚀 LeenVibe Coding Assistant MVP is ready for deployment!")
        sys.exit(0)
    else:
        print("\n❌ MVP test suite failed")
        print("📋 Review the test results above for details")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())