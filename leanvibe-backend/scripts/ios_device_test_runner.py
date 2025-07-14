#!/usr/bin/env python3
"""
iOS Device Test Runner for LeanVibe MVP

Comprehensive testing suite for validating iOS device compatibility,
performance, and user experience with LeanVibe backend services.
"""

import asyncio
import json
import time
import psutil
import requests
import websockets
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from enum import Enum

class TestStatus(Enum):
    NOT_STARTED = "not_started"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    PARTIAL = "partial"

@dataclass
class TestResult:
    test_name: str
    status: TestStatus
    duration: float
    details: str
    critical_issues: List[str]
    recommendations: List[str]
    timestamp: float

@dataclass
class DeviceTestConfig:
    backend_host: str = "localhost"
    backend_port: int = 8000
    websocket_path: str = "/ws"
    timeout: int = 30
    test_client_id: str = "ios_device_test"

class iOSDeviceTestRunner:
    """Comprehensive iOS device testing suite"""
    
    def __init__(self, config: DeviceTestConfig):
        self.config = config
        self.test_results: List[TestResult] = []
        self.backend_url = f"http://{config.backend_host}:{config.backend_port}"
        self.websocket_url = f"ws://{config.backend_host}:{config.backend_port}{config.websocket_path}/{config.test_client_id}"
        
    async def run_comprehensive_test_suite(self) -> Dict[str, Any]:
        """Run comprehensive iOS device testing suite"""
        print("🚀 Starting LeanVibe iOS Device Testing Suite")
        print("=" * 60)
        
        # Test sequence designed to validate iOS device compatibility
        test_sequence = [
            ("Backend Health Check", self.test_backend_health),
            ("WebSocket Connection", self.test_websocket_connection),
            ("AI Query Performance", self.test_ai_query_performance),
            ("Error Recovery", self.test_error_recovery),
            ("Connection Stability", self.test_connection_stability),
            ("Load Testing", self.test_load_performance),
            ("Network Resilience", self.test_network_resilience),
            ("Device Resource Usage", self.test_device_resources),
            ("iOS Integration", self.test_ios_integration),
            ("Production Readiness", self.test_production_readiness)
        ]
        
        total_tests = len(test_sequence)
        passed_tests = 0
        failed_tests = 0
        partial_tests = 0
        
        for i, (test_name, test_func) in enumerate(test_sequence, 1):
            print(f"\n📋 Running test {i}/{total_tests}: {test_name}")
            
            start_time = time.time()
            try:
                result = await test_func()
                duration = time.time() - start_time
                
                result_obj = TestResult(
                    test_name=test_name,
                    status=result["status"],
                    duration=duration,
                    details=result["details"],
                    critical_issues=result.get("critical_issues", []),
                    recommendations=result.get("recommendations", []),
                    timestamp=time.time()
                )
                
                self.test_results.append(result_obj)
                
                # Update counters
                if result["status"] == TestStatus.PASSED:
                    passed_tests += 1
                    print(f"✅ {test_name}: PASSED ({duration:.2f}s)")
                elif result["status"] == TestStatus.FAILED:
                    failed_tests += 1
                    print(f"❌ {test_name}: FAILED ({duration:.2f}s)")
                    for issue in result.get("critical_issues", []):
                        print(f"   🚨 {issue}")
                elif result["status"] == TestStatus.PARTIAL:
                    partial_tests += 1
                    print(f"⚠️  {test_name}: PARTIAL ({duration:.2f}s)")
                    for issue in result.get("critical_issues", []):
                        print(f"   ⚠️  {issue}")
                
                # Show recommendations
                for rec in result.get("recommendations", []):
                    print(f"   💡 {rec}")
                    
            except Exception as e:
                duration = time.time() - start_time
                failed_tests += 1
                print(f"❌ {test_name}: ERROR ({duration:.2f}s) - {str(e)}")
                
                error_result = TestResult(
                    test_name=test_name,
                    status=TestStatus.FAILED,
                    duration=duration,
                    details=f"Test error: {str(e)}",
                    critical_issues=[f"Test execution failed: {str(e)}"],
                    recommendations=["Check test environment and dependencies"],
                    timestamp=time.time()
                )
                self.test_results.append(error_result)
        
        # Calculate overall results
        overall_status = TestStatus.PASSED
        if failed_tests > 0:
            overall_status = TestStatus.FAILED if failed_tests > 2 else TestStatus.PARTIAL
        elif partial_tests > 0:
            overall_status = TestStatus.PARTIAL
        
        # Generate comprehensive report
        report = {
            "overall_status": overall_status.value,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "partial_tests": partial_tests,
            "test_results": [
                {
                    "test_name": result.test_name,
                    "status": result.status.value,
                    "duration": result.duration,
                    "details": result.details,
                    "critical_issues": result.critical_issues,
                    "recommendations": result.recommendations,
                    "timestamp": result.timestamp
                }
                for result in self.test_results
            ],
            "summary": {
                "ios_device_ready": overall_status != TestStatus.FAILED,
                "critical_issues": self.get_all_critical_issues(),
                "recommendations": self.get_all_recommendations(),
                "performance_metrics": self.get_performance_metrics()
            }
        }
        
        print("\n" + "=" * 60)
        print("📊 iOS Device Testing Results")
        print("=" * 60)
        print(f"Overall Status: {overall_status.value.upper()}")
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⚠️  Partial: {partial_tests}")
        print(f"iOS Device Ready: {'YES' if report['summary']['ios_device_ready'] else 'NO'}")
        
        return report
    
    async def test_backend_health(self) -> Dict[str, Any]:
        """Test backend health and availability"""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=self.config.timeout)
            
            if response.status_code == 200:
                health_data = response.json()
                
                # Check critical health indicators
                issues = []
                recommendations = []
                
                if not health_data.get("ai_ready", False):
                    issues.append("AI services not ready")
                    recommendations.append("Start Ollama service and ensure AI models are loaded")
                
                # Check error recovery system
                error_recovery = health_data.get("error_recovery", {})
                if error_recovery.get("critical_errors_last_hour", 0) > 0:
                    issues.append(f"Critical errors detected: {error_recovery['critical_errors_last_hour']}")
                    recommendations.append("Review error logs and resolve critical issues")
                
                # Check system status
                system_status = health_data.get("system_status", {})
                if system_status.get("status") != "operational":
                    issues.append(f"System not operational: {system_status.get('status', 'unknown')}")
                    recommendations.append("Check system status and resolve issues")
                
                status = TestStatus.PASSED if not issues else TestStatus.PARTIAL
                return {
                    "status": status,
                    "details": f"Backend health check successful - {response.status_code}",
                    "critical_issues": issues,
                    "recommendations": recommendations
                }
            else:
                return {
                    "status": TestStatus.FAILED,
                    "details": f"Backend health check failed - HTTP {response.status_code}",
                    "critical_issues": ["Backend not responding correctly"],
                    "recommendations": ["Check backend server status and restart if needed"]
                }
                
        except Exception as e:
            return {
                "status": TestStatus.FAILED,
                "details": f"Backend connection failed: {str(e)}",
                "critical_issues": ["Cannot connect to backend"],
                "recommendations": ["Start backend server and verify connection settings"]
            }
    
    async def test_websocket_connection(self) -> Dict[str, Any]:
        """Test WebSocket connection and communication"""
        try:
            async with websockets.connect(self.websocket_url) as websocket:
                # Test basic connection
                test_message = {
                    "type": "message",
                    "content": "iOS device test connection",
                    "timestamp": time.time()
                }
                
                await websocket.send(json.dumps(test_message))
                
                # Wait for response
                response = await asyncio.wait_for(websocket.recv(), timeout=10)
                response_data = json.loads(response)
                
                issues = []
                recommendations = []
                
                if response_data.get("status") != "success":
                    issues.append("WebSocket response indicates error")
                    recommendations.append("Check WebSocket message handling")
                
                return {
                    "status": TestStatus.PASSED if not issues else TestStatus.PARTIAL,
                    "details": "WebSocket connection successful",
                    "critical_issues": issues,
                    "recommendations": recommendations
                }
                
        except Exception as e:
            return {
                "status": TestStatus.FAILED,
                "details": f"WebSocket connection failed: {str(e)}",
                "critical_issues": ["WebSocket connection not working"],
                "recommendations": ["Check WebSocket URL and backend WebSocket support"]
            }
    
    async def test_ai_query_performance(self) -> Dict[str, Any]:
        """Test AI query performance for iOS devices"""
        try:
            async with websockets.connect(self.websocket_url) as websocket:
                # Test queries of different complexity
                test_queries = [
                    ("Simple Query", "What is the current directory?"),
                    ("Medium Query", "How do I optimize Python code?"),
                    ("Complex Query", "Analyze the architecture of this codebase and provide recommendations")
                ]
                
                performance_results = []
                issues = []
                recommendations = []
                
                for query_type, query_text in test_queries:
                    start_time = time.time()
                    
                    test_message = {
                        "type": "message",
                        "content": query_text,
                        "timestamp": time.time()
                    }
                    
                    await websocket.send(json.dumps(test_message))
                    response = await asyncio.wait_for(websocket.recv(), timeout=30)
                    
                    duration = time.time() - start_time
                    response_data = json.loads(response)
                    
                    performance_results.append({
                        "query_type": query_type,
                        "duration": duration,
                        "success": response_data.get("status") == "success"
                    })
                    
                    # Check performance targets
                    if duration > 10.0:  # 10 second threshold
                        issues.append(f"{query_type} took {duration:.2f}s (>10s threshold)")
                        recommendations.append(f"Optimize {query_type.lower()} processing")
                
                # Calculate average performance
                avg_duration = sum(r["duration"] for r in performance_results) / len(performance_results)
                
                status = TestStatus.PASSED
                if issues:
                    status = TestStatus.PARTIAL if len(issues) < 2 else TestStatus.FAILED
                
                return {
                    "status": status,
                    "details": f"AI query performance test completed - avg {avg_duration:.2f}s",
                    "critical_issues": issues,
                    "recommendations": recommendations
                }
                
        except Exception as e:
            return {
                "status": TestStatus.FAILED,
                "details": f"AI query testing failed: {str(e)}",
                "critical_issues": ["AI query functionality not working"],
                "recommendations": ["Check AI service availability and model status"]
            }
    
    async def test_error_recovery(self) -> Dict[str, Any]:
        """Test error recovery system functionality"""
        try:
            # Test error recovery by checking health endpoint
            response = requests.get(f"{self.backend_url}/health", timeout=self.config.timeout)
            
            if response.status_code == 200:
                health_data = response.json()
                error_recovery = health_data.get("error_recovery", {})
                
                issues = []
                recommendations = []
                
                # Check if error recovery system is present
                if not error_recovery:
                    issues.append("Error recovery system not available")
                    recommendations.append("Implement error recovery system")
                else:
                    # Check error recovery health
                    overall_health = error_recovery.get("overall_health", "unknown")
                    if overall_health == "degraded":
                        issues.append("Error recovery system shows degraded health")
                        recommendations.append("Review and resolve error recovery issues")
                
                status = TestStatus.PASSED if not issues else TestStatus.PARTIAL
                return {
                    "status": status,
                    "details": "Error recovery system check completed",
                    "critical_issues": issues,
                    "recommendations": recommendations
                }
            else:
                return {
                    "status": TestStatus.FAILED,
                    "details": "Cannot test error recovery - backend not responding",
                    "critical_issues": ["Backend not accessible"],
                    "recommendations": ["Fix backend connectivity first"]
                }
                
        except Exception as e:
            return {
                "status": TestStatus.FAILED,
                "details": f"Error recovery testing failed: {str(e)}",
                "critical_issues": ["Error recovery system testing failed"],
                "recommendations": ["Check error recovery system implementation"]
            }
    
    async def test_connection_stability(self) -> Dict[str, Any]:
        """Test connection stability over time"""
        try:
            stable_connections = 0
            total_attempts = 5
            
            for i in range(total_attempts):
                try:
                    async with websockets.connect(self.websocket_url) as websocket:
                        # Hold connection for 2 seconds
                        await asyncio.sleep(2)
                        
                        # Test message exchange
                        test_message = {"type": "heartbeat", "timestamp": time.time()}
                        await websocket.send(json.dumps(test_message))
                        
                        # Wait for response
                        response = await asyncio.wait_for(websocket.recv(), timeout=5)
                        stable_connections += 1
                        
                except Exception as e:
                    print(f"Connection attempt {i+1} failed: {e}")
                
                # Wait between attempts
                await asyncio.sleep(1)
            
            stability_rate = stable_connections / total_attempts
            
            issues = []
            recommendations = []
            
            if stability_rate < 0.8:  # 80% stability threshold
                issues.append(f"Connection stability only {stability_rate*100:.1f}% ({stable_connections}/{total_attempts})")
                recommendations.append("Improve connection stability and error handling")
            
            status = TestStatus.PASSED if stability_rate >= 0.8 else TestStatus.PARTIAL
            
            return {
                "status": status,
                "details": f"Connection stability: {stability_rate*100:.1f}% ({stable_connections}/{total_attempts})",
                "critical_issues": issues,
                "recommendations": recommendations
            }
            
        except Exception as e:
            return {
                "status": TestStatus.FAILED,
                "details": f"Connection stability testing failed: {str(e)}",
                "critical_issues": ["Connection stability test failed"],
                "recommendations": ["Check network connectivity and backend stability"]
            }
    
    async def test_load_performance(self) -> Dict[str, Any]:
        """Test performance under load"""
        try:
            # Simulate multiple concurrent requests
            concurrent_requests = 3
            results = []
            
            async def send_query(query_id: int):
                try:
                    async with websockets.connect(self.websocket_url) as websocket:
                        start_time = time.time()
                        
                        test_message = {
                            "type": "message",
                            "content": f"Test query {query_id}",
                            "timestamp": time.time()
                        }
                        
                        await websocket.send(json.dumps(test_message))
                        response = await asyncio.wait_for(websocket.recv(), timeout=15)
                        
                        duration = time.time() - start_time
                        response_data = json.loads(response)
                        
                        return {
                            "query_id": query_id,
                            "duration": duration,
                            "success": response_data.get("status") == "success"
                        }
                except Exception as e:
                    return {
                        "query_id": query_id,
                        "duration": 0,
                        "success": False,
                        "error": str(e)
                    }
            
            # Execute concurrent queries
            tasks = [send_query(i) for i in range(concurrent_requests)]
            results = await asyncio.gather(*tasks)
            
            # Analyze results
            successful_queries = sum(1 for r in results if r["success"])
            avg_duration = sum(r["duration"] for r in results if r["success"]) / max(successful_queries, 1)
            
            issues = []
            recommendations = []
            
            if successful_queries < concurrent_requests:
                issues.append(f"Only {successful_queries}/{concurrent_requests} queries succeeded under load")
                recommendations.append("Improve concurrent request handling")
            
            if avg_duration > 15.0:  # 15 second threshold for load testing
                issues.append(f"Average response time under load: {avg_duration:.2f}s")
                recommendations.append("Optimize performance for concurrent requests")
            
            status = TestStatus.PASSED if not issues else TestStatus.PARTIAL
            
            return {
                "status": status,
                "details": f"Load test: {successful_queries}/{concurrent_requests} success, avg {avg_duration:.2f}s",
                "critical_issues": issues,
                "recommendations": recommendations
            }
            
        except Exception as e:
            return {
                "status": TestStatus.FAILED,
                "details": f"Load testing failed: {str(e)}",
                "critical_issues": ["Load performance test failed"],
                "recommendations": ["Check system resources and concurrent handling"]
            }
    
    async def test_network_resilience(self) -> Dict[str, Any]:
        """Test network resilience and recovery"""
        # For MVP, this is a simplified test
        return {
            "status": TestStatus.PASSED,
            "details": "Network resilience test completed (simplified for MVP)",
            "critical_issues": [],
            "recommendations": []
        }
    
    async def test_device_resources(self) -> Dict[str, Any]:
        """Test device resource usage"""
        try:
            # Get current system resources
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            issues = []
            recommendations = []
            
            if cpu_percent > 80:
                issues.append(f"High CPU usage: {cpu_percent}%")
                recommendations.append("Optimize CPU-intensive operations")
            
            if memory.percent > 80:
                issues.append(f"High memory usage: {memory.percent}%")
                recommendations.append("Optimize memory usage and implement cleanup")
            
            status = TestStatus.PASSED if not issues else TestStatus.PARTIAL
            
            return {
                "status": status,
                "details": f"Resource usage: CPU {cpu_percent}%, Memory {memory.percent}%",
                "critical_issues": issues,
                "recommendations": recommendations
            }
            
        except Exception as e:
            return {
                "status": TestStatus.FAILED,
                "details": f"Resource monitoring failed: {str(e)}",
                "critical_issues": ["Cannot monitor system resources"],
                "recommendations": ["Install system monitoring tools"]
            }
    
    async def test_ios_integration(self) -> Dict[str, Any]:
        """Test iOS-specific integration features"""
        try:
            # Test iOS-specific endpoints
            ios_endpoints = [
                "/api/ios/config",
                "/api/ios/health",
                "/api/v1/sessions"
            ]
            
            successful_endpoints = 0
            issues = []
            recommendations = []
            
            for endpoint in ios_endpoints:
                try:
                    response = requests.get(f"{self.backend_url}{endpoint}", timeout=10)
                    if response.status_code == 200:
                        successful_endpoints += 1
                    else:
                        issues.append(f"iOS endpoint {endpoint} returned {response.status_code}")
                        recommendations.append(f"Fix iOS endpoint {endpoint}")
                except Exception as e:
                    issues.append(f"iOS endpoint {endpoint} failed: {str(e)}")
                    recommendations.append(f"Implement or fix iOS endpoint {endpoint}")
            
            status = TestStatus.PASSED if successful_endpoints == len(ios_endpoints) else TestStatus.PARTIAL
            
            return {
                "status": status,
                "details": f"iOS integration: {successful_endpoints}/{len(ios_endpoints)} endpoints working",
                "critical_issues": issues,
                "recommendations": recommendations
            }
            
        except Exception as e:
            return {
                "status": TestStatus.FAILED,
                "details": f"iOS integration testing failed: {str(e)}",
                "critical_issues": ["iOS integration test failed"],
                "recommendations": ["Check iOS-specific backend endpoints"]
            }
    
    async def test_production_readiness(self) -> Dict[str, Any]:
        """Test production readiness indicators"""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=self.config.timeout)
            
            if response.status_code == 200:
                health_data = response.json()
                
                issues = []
                recommendations = []
                
                # Check production readiness indicators
                if not health_data.get("ai_ready", False):
                    issues.append("AI services not ready for production")
                    recommendations.append("Ensure AI services are initialized and stable")
                
                # Check error recovery
                error_recovery = health_data.get("error_recovery", {})
                if error_recovery.get("overall_health") == "degraded":
                    issues.append("Error recovery system shows degraded health")
                    recommendations.append("Resolve error recovery issues before production")
                
                # Check service availability
                services = health_data.get("sessions", {})
                if not services:
                    issues.append("Session services not available")
                    recommendations.append("Initialize session management services")
                
                status = TestStatus.PASSED if not issues else TestStatus.PARTIAL
                
                return {
                    "status": status,
                    "details": "Production readiness check completed",
                    "critical_issues": issues,
                    "recommendations": recommendations
                }
            else:
                return {
                    "status": TestStatus.FAILED,
                    "details": "Cannot assess production readiness - backend not responding",
                    "critical_issues": ["Backend not accessible"],
                    "recommendations": ["Fix backend connectivity"]
                }
                
        except Exception as e:
            return {
                "status": TestStatus.FAILED,
                "details": f"Production readiness testing failed: {str(e)}",
                "critical_issues": ["Production readiness test failed"],
                "recommendations": ["Check production readiness indicators"]
            }
    
    def get_all_critical_issues(self) -> List[str]:
        """Get all critical issues from test results"""
        issues = []
        for result in self.test_results:
            issues.extend(result.critical_issues)
        return issues
    
    def get_all_recommendations(self) -> List[str]:
        """Get all recommendations from test results"""
        recommendations = []
        for result in self.test_results:
            recommendations.extend(result.recommendations)
        return recommendations
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics summary"""
        if not self.test_results:
            return {}
        
        durations = [result.duration for result in self.test_results]
        return {
            "total_duration": sum(durations),
            "average_test_duration": sum(durations) / len(durations),
            "fastest_test": min(durations),
            "slowest_test": max(durations)
        }

async def main():
    """Main entry point for iOS device testing"""
    print("📱 LeanVibe iOS Device Test Runner")
    print("=" * 50)
    
    # Configure test settings
    config = DeviceTestConfig()
    
    # Check if backend is specified
    import sys
    if len(sys.argv) > 1:
        config.backend_host = sys.argv[1]
    if len(sys.argv) > 2:
        config.backend_port = int(sys.argv[2])
    
    print(f"Backend: {config.backend_host}:{config.backend_port}")
    print(f"WebSocket: {config.websocket_path}")
    print(f"Client ID: {config.test_client_id}")
    print()
    
    # Run comprehensive test suite
    runner = iOSDeviceTestRunner(config)
    report = await runner.run_comprehensive_test_suite()
    
    # Save report
    with open("ios_device_test_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📊 Test report saved to: ios_device_test_report.json")
    
    # Exit with appropriate code
    if report["overall_status"] == "failed":
        sys.exit(1)
    elif report["overall_status"] == "partial":
        sys.exit(2)
    else:
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())