#!/usr/bin/env python3
"""
Monitoring System Integration Test

Tests the comprehensive monitoring and observability system to ensure
all components are working correctly and can be integrated into the main application.
"""

import asyncio
import json
import logging
import sys
import time
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.core.monitoring_init import initialize_all_monitoring, shutdown_all_monitoring, run_monitoring_diagnostics
from app.core.logging_config import get_logger, set_request_context
from app.core.health_monitor import health_monitor
from app.core.performance_monitor import performance_monitor, track_operation
from app.core.error_tracker import error_tracker, track_error, ErrorSeverity, ErrorCategory
from app.core.websocket_monitor import websocket_monitor, register_websocket_connection, record_websocket_message, MessageType


async def test_logging_system():
    """Test structured logging system"""
    print("🔍 Testing structured logging system...")
    
    # Set request context
    set_request_context(request_id="test_req_123", user_id="test_user", session_id="test_session")
    
    # Get logger and test different log levels
    logger = get_logger("test.monitoring")
    
    logger.debug("Debug message test")
    logger.info("Info message test", test_data={"key": "value"})
    logger.warning("Warning message test", warning_type="test")
    logger.error("Error message test", error_code="TEST_001")
    
    print("✅ Structured logging system working")
    return True


async def test_health_monitoring():
    """Test health monitoring system"""
    print("🔍 Testing health monitoring system...")
    
    try:
        # Run health checks
        health_status = await health_monitor.run_all_checks()
        
        print(f"   Overall health status: {health_status.get('status', 'unknown')}")
        print(f"   Services checked: {health_status.get('total_services', 0)}")
        print(f"   Healthy services: {health_status.get('healthy_services', 0)}")
        
        # Test individual service health
        vector_health = health_monitor.get_service_health('vector_service')
        print(f"   Vector service health: {vector_health.status if vector_health else 'Not available'}")
        
        print("✅ Health monitoring system working")
        return True
        
    except Exception as e:
        print(f"❌ Health monitoring test failed: {e}")
        return False


async def test_performance_monitoring():
    """Test performance monitoring system"""
    print("🔍 Testing performance monitoring system...")
    
    try:
        # Test operation tracking
        async with track_operation("test_operation", test_param="value"):
            await asyncio.sleep(0.1)  # Simulate work
            
        # Test endpoint tracking
        performance_monitor.track_endpoint_performance(
            endpoint="/test/endpoint",
            method="GET",
            response_time_ms=125.5,
            success=True
        )
        
        # Get performance statistics
        stats = performance_monitor.get_operation_stats("test_operation")
        print(f"   Test operation stats: {stats['total_operations']} operations tracked")
        
        endpoint_stats = performance_monitor.get_endpoint_stats()
        print(f"   Endpoint stats: {endpoint_stats['summary']['total_endpoints']} endpoints tracked")
        
        system_stats = performance_monitor.get_system_resource_stats(duration_minutes=1)
        print(f"   System resource samples: {system_stats.get('sample_count', 0)}")
        
        print("✅ Performance monitoring system working")
        return True
        
    except Exception as e:
        print(f"❌ Performance monitoring test failed: {e}")
        return False


async def test_error_tracking():
    """Test error tracking system"""
    print("🔍 Testing error tracking system...")
    
    try:
        # Track different types of errors
        test_error = ValueError("Test validation error")
        error_id_1 = track_error(
            error=test_error,
            service="test_service",
            component="validation",
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.VALIDATION,
            context={"input": "test_data"}
        )
        
        # Track a network error
        network_error = ConnectionError("Test connection error")
        error_id_2 = track_error(
            error=network_error,
            service="test_service",
            component="network",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.NETWORK
        )
        
        # Get error metrics
        error_metrics = error_tracker.get_error_metrics(time_window_hours=1)
        print(f"   Total errors tracked: {error_metrics.total_errors}")
        print(f"   Error rate: {error_metrics.error_rate_per_minute:.2f}/min")
        
        # Get active alerts
        active_alerts = error_tracker.get_active_alerts()
        print(f"   Active alerts: {len(active_alerts)}")
        
        # Get error patterns
        error_patterns = error_tracker.get_error_patterns()
        print(f"   Error patterns detected: {len(error_patterns)}")
        
        print("✅ Error tracking system working")
        return True
        
    except Exception as e:
        print(f"❌ Error tracking test failed: {e}")
        return False


async def test_websocket_monitoring():
    """Test WebSocket monitoring system"""
    print("🔍 Testing WebSocket monitoring system...")
    
    try:
        # Register a test connection
        connection_info = register_websocket_connection(
            connection_id="test_conn_123",
            client_ip="127.0.0.1",
            user_id="test_user",
            endpoint="/ws/test"
        )
        print(f"   Registered connection: {connection_info.connection_id}")
        
        # Record some messages
        message_id_1 = record_websocket_message(
            connection_id="test_conn_123",
            message_type=MessageType.TEXT,
            size_bytes=256,
            direction="inbound",
            endpoint="/ws/test",
            processing_time_ms=50.0
        )
        
        message_id_2 = record_websocket_message(
            connection_id="test_conn_123", 
            message_type=MessageType.TEXT,
            size_bytes=512,
            direction="outbound",
            endpoint="/ws/test",
            processing_time_ms=25.0
        )
        
        # Get connection statistics
        connection_stats = websocket_monitor.get_connection_stats("test_conn_123")
        print(f"   Connection messages: {connection_stats.get('messages_total', 0)}")
        print(f"   Connection bytes: {connection_stats.get('bytes_total', 0)}")
        
        # Get overall WebSocket statistics
        overall_stats = websocket_monitor.get_connection_stats()
        pool_stats = overall_stats.get('pool_stats', {})
        print(f"   Total connections: {pool_stats.get('total_connections', 0)}")
        print(f"   Active connections: {pool_stats.get('active_connections', 0)}")
        
        # Get performance metrics
        performance_metrics = websocket_monitor.get_performance_metrics(time_window_minutes=5)
        print(f"   Messages processed: {performance_metrics.get('message_count', 0)}")
        
        print("✅ WebSocket monitoring system working")
        return True
        
    except Exception as e:
        print(f"❌ WebSocket monitoring test failed: {e}")
        return False


async def test_monitoring_api_simulation():
    """Simulate monitoring API usage"""
    print("🔍 Testing monitoring API simulation...")
    
    try:
        # Simulate some API operations that would be monitored
        logger = get_logger("api.test")
        
        # Simulate successful API requests
        for i in range(5):
            set_request_context(request_id=f"api_req_{i}")
            
            async with track_operation("api_request", endpoint="/test", method="GET"):
                logger.info("API request processed", request_number=i)
                await asyncio.sleep(0.05)  # Simulate processing time
            
            performance_monitor.track_endpoint_performance(
                endpoint="/test",
                method="GET", 
                response_time_ms=50 + (i * 10),
                success=True
            )
        
        # Simulate some errors
        for i in range(2):
            try:
                raise RuntimeError(f"Test API error {i}")
            except Exception as e:
                track_error(
                    error=e,
                    service="api",
                    component="handler",
                    severity=ErrorSeverity.MEDIUM,
                    category=ErrorCategory.BUSINESS_LOGIC
                )
        
        print("✅ Monitoring API simulation completed")
        return True
        
    except Exception as e:
        print(f"❌ Monitoring API simulation failed: {e}")
        return False


async def run_comprehensive_test():
    """Run comprehensive monitoring system test"""
    print("🚀 Starting comprehensive monitoring system test\n")
    
    test_results = {
        "logging": False,
        "health_monitoring": False,
        "performance_monitoring": False,
        "error_tracking": False,
        "websocket_monitoring": False,
        "api_simulation": False
    }
    
    try:
        # Initialize monitoring system
        print("🔧 Initializing monitoring system...")
        await initialize_all_monitoring({
            'log_level': 'INFO',
            'enable_json_logging': True,
            'enable_console_logging': True,
            'enable_file_logging': False,  # Disable file logging for test
        })
        print("✅ Monitoring system initialized\n")
        
        # Run individual tests
        test_results["logging"] = await test_logging_system()
        print()
        
        test_results["health_monitoring"] = await test_health_monitoring()
        print()
        
        test_results["performance_monitoring"] = await test_performance_monitoring()
        print()
        
        test_results["error_tracking"] = await test_error_tracking()
        print()
        
        test_results["websocket_monitoring"] = await test_websocket_monitoring()
        print()
        
        test_results["api_simulation"] = await test_monitoring_api_simulation()
        print()
        
        # Run diagnostics
        print("🔧 Running monitoring diagnostics...")
        diagnostics = await run_monitoring_diagnostics()
        print(f"   Diagnostics completed: {len(diagnostics)} components checked")
        print()
        
        # Summary
        passed_tests = sum(test_results.values())
        total_tests = len(test_results)
        
        print("=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        for test_name, passed in test_results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"   {test_name:<25}: {status}")
        
        print()
        print(f"🎯 Overall Result: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 All monitoring systems are working correctly!")
            return True
        else:
            print("⚠️  Some monitoring systems have issues that need attention.")
            return False
        
    except Exception as e:
        print(f"❌ Comprehensive test failed: {e}")
        return False
    
    finally:
        # Cleanup
        print("\n🔧 Shutting down monitoring systems...")
        try:
            await shutdown_all_monitoring()
            print("✅ Monitoring systems shutdown completed")
        except Exception as e:
            print(f"⚠️  Shutdown error (non-critical): {e}")


async def main():
    """Main test function"""
    success = await run_comprehensive_test()
    
    if success:
        print("\n🎉 Monitoring system integration test completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Monitoring system integration test failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())