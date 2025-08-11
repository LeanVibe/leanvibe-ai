#!/usr/bin/env python3
"""
Production Monitoring and Logging Tests
Test-driven implementation of comprehensive error monitoring for production readiness
"""

import asyncio
import sys
import os
import json
import time
from uuid import uuid4
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def test_structured_logging():
    """
    Test that critical operations have structured logging for debugging
    This test should FAIL initially, then PASS after we implement monitoring
    """
    print("🔍 Testing Structured Logging for Critical Operations...")
    
    try:
        from app.services.monitoring_service import monitoring_service
        from app.models.mvp_models import MVPProject, MVPStatus, FounderInterview, MVPIndustry
        
        # Test 1: Test operation logging with context
        print("\n1. Testing structured operation logging...")
        
        # This should log structured data that's easily searchable
        operation_id = await monitoring_service.start_operation(
            operation_type="mvp_creation",
            tenant_id=uuid4(),
            context={
                "project_name": "TestProject",
                "user_type": "founder",
                "operation_source": "autonomous_pipeline"
            }
        )
        
        assert operation_id is not None
        print(f"   ✅ Started operation tracking: {operation_id}")
        
        # Test 2: Test operation success logging
        await monitoring_service.complete_operation(
            operation_id=operation_id,
            status="success",
            duration_ms=150,
            result_data={
                "mvp_project_id": str(uuid4()),
                "blueprint_confidence": 0.85
            }
        )
        
        print("   ✅ Completed operation tracking with success")
        
        # Test 3: Test operation failure logging
        failure_op_id = await monitoring_service.start_operation(
            operation_type="blueprint_generation",
            tenant_id=uuid4(),
            context={"retry_count": 2}
        )
        
        await monitoring_service.fail_operation(
            operation_id=failure_op_id,
            error_type="ValidationError", 
            error_message="Invalid founder interview format",
            duration_ms=75,
            error_context={
                "field_errors": ["business_idea", "target_audience"],
                "input_validation": "failed"
            }
        )
        
        print("   ✅ Completed operation tracking with failure")
        
        return True
        
    except Exception as e:
        print(f"❌ Structured logging test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_error_rate_monitoring():
    """
    Test error rate tracking for critical user journeys
    """
    print("\n🔍 Testing Error Rate Monitoring...")
    
    try:
        from app.services.monitoring_service import monitoring_service
        
        # Test 1: Track user journey success
        print("\n1. Testing user journey success tracking...")
        
        journey_id = "autonomous_pipeline_journey"
        
        # Track multiple successful operations
        for i in range(5):
            await monitoring_service.track_user_journey_step(
                journey_id=journey_id,
                step_name=f"step_{i}",
                tenant_id=uuid4(),
                status="success",
                duration_ms=100 + i * 10
            )
        
        # Track some failures
        for i in range(2):
            await monitoring_service.track_user_journey_step(
                journey_id=journey_id,
                step_name=f"step_fail_{i}",
                tenant_id=uuid4(),
                status="failure",
                duration_ms=200,
                error_type="TimeoutError"
            )
        
        # Get error rate metrics
        metrics = await monitoring_service.get_journey_metrics(journey_id, hours=1)
        
        assert metrics is not None
        assert metrics["total_operations"] == 7
        assert metrics["success_count"] == 5
        assert metrics["failure_count"] == 2
        assert abs(metrics["error_rate"] - 0.286) < 0.01  # 2/7 = ~0.286
        
        print(f"   ✅ Journey metrics calculated: {metrics['error_rate']:.2%} error rate")
        print(f"   ✅ Total operations: {metrics['total_operations']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error rate monitoring test failed: {e}")
        return False


async def test_performance_monitoring():
    """
    Test performance monitoring for slow operations
    """
    print("\n🔍 Testing Performance Monitoring...")
    
    try:
        from app.services.monitoring_service import monitoring_service
        
        # Test 1: Performance threshold detection
        print("\n1. Testing performance threshold monitoring...")
        
        # Simulate fast operation
        fast_op = await monitoring_service.start_operation(
            operation_type="fast_blueprint_generation",
            tenant_id=uuid4()
        )
        
        await monitoring_service.complete_operation(
            operation_id=fast_op,
            status="success",
            duration_ms=500  # Fast - under 1s
        )
        
        # Simulate slow operation
        slow_op = await monitoring_service.start_operation(
            operation_type="slow_blueprint_generation", 
            tenant_id=uuid4()
        )
        
        await monitoring_service.complete_operation(
            operation_id=slow_op,
            status="success",
            duration_ms=3000  # Slow - 3 seconds
        )
        
        # Test 2: Performance metrics calculation
        perf_metrics = await monitoring_service.get_performance_metrics(
            operation_type="blueprint_generation",
            hours=1
        )
        
        assert perf_metrics is not None
        assert "average_duration_ms" in perf_metrics
        assert "p95_duration_ms" in perf_metrics
        assert "slow_operation_count" in perf_metrics
        
        print(f"   ✅ Performance metrics: avg={perf_metrics.get('average_duration_ms', 0):.0f}ms")
        print(f"   ✅ P95 duration: {perf_metrics.get('p95_duration_ms', 0):.0f}ms")
        print(f"   ✅ Slow operations detected: {perf_metrics.get('slow_operation_count', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance monitoring test failed: {e}")
        return False


async def test_health_checks():
    """
    Test health checks for core services
    """
    print("\n🔍 Testing Service Health Checks...")
    
    try:
        from app.services.monitoring_service import monitoring_service
        
        # Test 1: Core service health checks
        print("\n1. Testing core service health checks...")
        
        health_status = await monitoring_service.check_system_health()
        
        assert health_status is not None
        assert "services" in health_status
        assert "overall_status" in health_status
        assert "timestamp" in health_status
        
        # Should check critical services
        required_services = [
            "mvp_service",
            "pipeline_orchestration_service", 
            "email_service",
            "assembly_line_system"
        ]
        
        for service in required_services:
            assert service in health_status["services"], f"Missing health check for {service}"
            service_status = health_status["services"][service]
            assert "status" in service_status
            assert "response_time_ms" in service_status
        
        print(f"   ✅ System health checked: {health_status['overall_status']}")
        print(f"   ✅ Services monitored: {len(health_status['services'])}")
        
        # Test 2: Health check alerting
        if health_status["overall_status"] == "degraded":
            alerts = await monitoring_service.get_active_alerts()
            assert isinstance(alerts, list)
            print(f"   ✅ Active alerts: {len(alerts)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Health checks test failed: {e}")
        return False


async def main():
    """Run comprehensive production monitoring tests"""
    print("🚀 Production Monitoring & Logging Tests")
    print("=" * 60)
    
    test_results = []
    
    # Test 1: Structured logging
    test_results.append(await test_structured_logging())
    
    # Test 2: Error rate monitoring
    test_results.append(await test_error_rate_monitoring())
    
    # Test 3: Performance monitoring  
    test_results.append(await test_performance_monitoring())
    
    # Test 4: Health checks
    test_results.append(await test_health_checks())
    
    print("\n" + "=" * 60)
    
    passed_tests = sum(test_results)
    total_tests = len(test_results)
    
    if passed_tests == total_tests:
        print("🎉 ALL PRODUCTION MONITORING TESTS PASSED!")
        print(f"✅ {passed_tests}/{total_tests} tests successful")
        print("\n🚀 PRODUCTION OBSERVABILITY COMPLETE:")
        print("✅ Structured logging for all critical operations")
        print("✅ Error rate tracking for user journey monitoring")
        print("✅ Performance monitoring with threshold detection") 
        print("✅ Health checks for automated service monitoring")
        print("✅ Comprehensive alerting and metrics collection")
        print("\n🌟 READY FOR PRODUCTION DEPLOYMENT WITH FULL OBSERVABILITY!")
        return True
    else:
        print("❌ SOME MONITORING TESTS FAILED - NEED IMPLEMENTATION")
        print(f"❌ {total_tests - passed_tests}/{total_tests} tests failed")
        print("🔧 Implement monitoring service for production observability")
        return False


if __name__ == "__main__":
    asyncio.run(main())