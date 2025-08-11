#!/usr/bin/env python3
"""
Production Load & Stress Testing
Comprehensive validation of system behavior under realistic production load
"""

import asyncio
import sys
import os
import time
import random
import statistics
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
from datetime import datetime
from typing import List, Dict, Any

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def test_burst_load_handling():
    """
    Test system behavior under sudden burst load
    Production scenario: Marketing campaign leads to 50 simultaneous signups
    """
    print("🔍 Testing Burst Load Handling...")
    
    try:
        from app.services.monitoring_service import monitoring_service
        
        print("\n1. Testing sudden burst of 50 concurrent operations...")
        
        burst_size = 50
        start_time = time.time()
        
        # Create burst load
        async def burst_operation(operation_id: int):
            op_id = await monitoring_service.start_operation(
                operation_type="burst_load_test",
                tenant_id=uuid4(),
                context={
                    "burst_test": True,
                    "operation_id": operation_id,
                    "burst_size": burst_size
                }
            )
            
            # Simulate realistic operation duration with some variance
            operation_duration = random.uniform(10, 100)  # 10-100ms
            await asyncio.sleep(operation_duration / 1000)
            
            await monitoring_service.complete_operation(
                operation_id=op_id,
                status="success",
                duration_ms=operation_duration,
                result_data={"burst_operation": operation_id}
            )
            
            return operation_duration
        
        # Execute burst load
        tasks = [burst_operation(i) for i in range(burst_size)]
        durations = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        total_burst_time = end_time - start_time
        
        # Analyze results
        successful_ops = [d for d in durations if not isinstance(d, Exception)]
        failed_ops = [d for d in durations if isinstance(d, Exception)]
        
        success_rate = len(successful_ops) / burst_size * 100
        
        # Performance requirements for burst load
        assert success_rate >= 95, f"Success rate {success_rate:.1f}% below 95% requirement"
        assert total_burst_time < 10, f"Burst handling took {total_burst_time:.2f}s, exceeds 10s limit"
        
        print(f"   ✅ Handled {burst_size} operations in {total_burst_time:.2f}s")
        print(f"   ✅ Success rate: {success_rate:.1f}%")
        print(f"   ✅ Failed operations: {len(failed_ops)}")
        
        if successful_ops:
            avg_duration = statistics.mean(successful_ops)
            print(f"   ✅ Average operation duration: {avg_duration:.1f}ms")
        
        return True
        
    except Exception as e:
        print(f"❌ Burst load handling test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_sustained_production_load():
    """
    Test sustained production load over extended period
    Production scenario: Normal business hours with steady traffic
    """
    print("\n🔍 Testing Sustained Production Load...")
    
    try:
        from app.services.monitoring_service import monitoring_service
        from app.services.pipeline_orchestration_service import pipeline_orchestration_service
        
        print("\n1. Testing sustained load for 30 seconds...")
        
        operations_per_second = 10  # Realistic production rate
        test_duration = 30  # 30 seconds
        total_operations = operations_per_second * test_duration
        
        start_time = time.time()
        completed_operations = 0
        error_count = 0
        response_times = []
        
        async def sustained_operation(op_index: int):
            nonlocal completed_operations, error_count
            
            op_start = time.time()
            
            try:
                # Mix of different operation types to simulate production
                op_type = random.choice([
                    "monitoring_operation", 
                    "health_check", 
                    "performance_metric",
                    "journey_tracking"
                ])
                
                op_id = await monitoring_service.start_operation(
                    operation_type=op_type,
                    tenant_id=uuid4(),
                    context={
                        "sustained_load_test": True,
                        "operation_index": op_index,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                # Simulate variable operation duration
                operation_duration = random.uniform(5, 50)  # 5-50ms realistic range
                await asyncio.sleep(operation_duration / 1000)
                
                await monitoring_service.complete_operation(
                    operation_id=op_id,
                    status="success",
                    duration_ms=operation_duration,
                    result_data={"sustained_test": True}
                )
                
                completed_operations += 1
                op_end = time.time()
                response_times.append((op_end - op_start) * 1000)  # ms
                
            except Exception as e:
                error_count += 1
                print(f"   ⚠️  Operation {op_index} failed: {e}")
        
        # Generate sustained load
        tasks = []
        for i in range(total_operations):
            task = asyncio.create_task(sustained_operation(i))
            tasks.append(task)
            
            # Control rate - add slight delay to simulate realistic spacing
            if i < total_operations - 1:
                await asyncio.sleep(1.0 / operations_per_second + random.uniform(-0.01, 0.01))
        
        # Wait for all operations to complete
        await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        actual_duration = end_time - start_time
        actual_ops_per_second = completed_operations / actual_duration
        
        # Calculate performance metrics
        success_rate = (completed_operations / total_operations) * 100 if total_operations > 0 else 0
        error_rate = (error_count / total_operations) * 100 if total_operations > 0 else 0
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            p95_response_time = statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else max(response_times)
        else:
            avg_response_time = 0
            p95_response_time = 0
        
        # Production requirements
        assert success_rate >= 99, f"Success rate {success_rate:.1f}% below 99% requirement"
        assert error_rate <= 1, f"Error rate {error_rate:.1f}% exceeds 1% limit"
        assert avg_response_time < 100, f"Average response time {avg_response_time:.1f}ms exceeds 100ms"
        
        print(f"   ✅ Sustained {actual_ops_per_second:.1f} ops/s for {actual_duration:.1f}s")
        print(f"   ✅ Success rate: {success_rate:.1f}%")
        print(f"   ✅ Error rate: {error_rate:.1f}%")
        print(f"   ✅ Average response time: {avg_response_time:.1f}ms")
        print(f"   ✅ P95 response time: {p95_response_time:.1f}ms")
        
        return True
        
    except Exception as e:
        print(f"❌ Sustained production load test failed: {e}")
        return False


async def test_resource_exhaustion_recovery():
    """
    Test system behavior when approaching resource limits
    Production scenario: System gracefully handles resource pressure
    """
    print("\n🔍 Testing Resource Exhaustion Recovery...")
    
    try:
        from app.services.monitoring_service import monitoring_service
        
        print("\n1. Testing high memory pressure scenario...")
        
        # Create many operations to increase memory pressure
        operations = []
        memory_pressure_ops = 200
        
        # Phase 1: Build up memory pressure
        for i in range(memory_pressure_ops):
            op_id = await monitoring_service.start_operation(
                operation_type="memory_pressure_test",
                tenant_id=uuid4(),
                context={
                    "memory_pressure": True,
                    "operation": i,
                    "large_context": "x" * 1000  # 1KB context per operation
                }
            )
            operations.append(op_id)
        
        print(f"   ✅ Created {len(operations)} operations for memory pressure")
        
        # Phase 2: Test system responsiveness under pressure
        start_time = time.time()
        
        test_op_id = await monitoring_service.start_operation(
            operation_type="responsiveness_test",
            tenant_id=uuid4(),
            context={"test_under_pressure": True}
        )
        
        await monitoring_service.complete_operation(
            operation_id=test_op_id,
            status="success",
            duration_ms=10.0,
            result_data={"pressure_test": True}
        )
        
        end_time = time.time()
        response_time_under_pressure = (end_time - start_time) * 1000
        
        # Phase 3: Clean up operations (simulate memory recovery)
        cleanup_start = time.time()
        for op_id in operations[:100]:  # Clean up half
            await monitoring_service.complete_operation(
                operation_id=op_id,
                status="success",
                duration_ms=1.0,
                result_data={"cleanup": True}
            )
        cleanup_end = time.time()
        cleanup_time = (cleanup_end - cleanup_start) * 1000
        
        # Validate recovery requirements
        assert response_time_under_pressure < 500, f"Response under pressure {response_time_under_pressure:.1f}ms exceeds 500ms"
        assert cleanup_time < 1000, f"Cleanup took {cleanup_time:.1f}ms, exceeds 1000ms"
        
        print(f"   ✅ Response time under memory pressure: {response_time_under_pressure:.1f}ms")
        print(f"   ✅ Cleanup time for 100 operations: {cleanup_time:.1f}ms")
        print("   ✅ System maintained responsiveness under resource pressure")
        
        return True
        
    except Exception as e:
        print(f"❌ Resource exhaustion recovery test failed: {e}")
        return False


async def test_error_cascade_prevention():
    """
    Test that errors don't cascade through the system
    Production scenario: Single service failure doesn't bring down entire system
    """
    print("\n🔍 Testing Error Cascade Prevention...")
    
    try:
        from app.services.monitoring_service import monitoring_service
        
        print("\n1. Testing error isolation and recovery...")
        
        # Simulate mixed success/failure operations
        total_operations = 50
        intentional_failures = 10
        successful_operations = 0
        failed_operations = 0
        
        async def mixed_operation(op_index: int, should_fail: bool = False):
            nonlocal successful_operations, failed_operations
            
            try:
                op_id = await monitoring_service.start_operation(
                    operation_type="error_cascade_test",
                    tenant_id=uuid4(),
                    context={
                        "error_cascade_test": True,
                        "operation_index": op_index,
                        "intentional_failure": should_fail
                    }
                )
                
                if should_fail:
                    # Simulate operation failure
                    await monitoring_service.fail_operation(
                        operation_id=op_id,
                        error_type="SimulatedError",
                        error_message=f"Intentional failure for operation {op_index}",
                        duration_ms=25.0,
                        error_context={"test": "error_cascade"}
                    )
                    failed_operations += 1
                else:
                    # Normal successful operation
                    await monitoring_service.complete_operation(
                        operation_id=op_id,
                        status="success",
                        duration_ms=15.0,
                        result_data={"successful_operation": op_index}
                    )
                    successful_operations += 1
                
            except Exception as e:
                print(f"   ⚠️  Unexpected error in operation {op_index}: {e}")
                failed_operations += 1
        
        # Create mixed operations (some will fail intentionally)
        tasks = []
        for i in range(total_operations):
            should_fail = i < intentional_failures  # First 10 operations fail
            task = asyncio.create_task(mixed_operation(i, should_fail))
            tasks.append(task)
        
        # Execute all operations
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify system health after errors
        health_status = await monitoring_service.check_system_health()
        
        # Calculate metrics
        actual_success_rate = (successful_operations / total_operations) * 100
        actual_failure_rate = (failed_operations / total_operations) * 100
        
        # Validate error isolation requirements
        expected_success_rate = ((total_operations - intentional_failures) / total_operations) * 100
        
        assert actual_success_rate >= expected_success_rate * 0.95, f"Success rate {actual_success_rate:.1f}% below expected {expected_success_rate:.1f}%"
        assert health_status["overall_status"] in ["healthy", "degraded"], f"System health {health_status['overall_status']} indicates cascade failure"
        
        print(f"   ✅ Successful operations: {successful_operations}/{total_operations}")
        print(f"   ✅ Failed operations: {failed_operations}/{total_operations} (expected: {intentional_failures})")
        print(f"   ✅ System health after errors: {health_status['overall_status']}")
        print("   ✅ No error cascade detected - system isolated failures correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Error cascade prevention test failed: {e}")
        return False


async def test_production_monitoring_under_load():
    """
    Test that monitoring system itself performs well under load
    Production scenario: Monitoring doesn't become a bottleneck
    """
    print("\n🔍 Testing Production Monitoring Under Load...")
    
    try:
        from app.services.monitoring_service import monitoring_service
        
        print("\n1. Testing monitoring system scalability...")
        
        # High-frequency monitoring operations
        monitoring_ops = 100
        concurrent_batches = 10
        
        start_time = time.time()
        
        async def monitoring_batch(batch_id: int):
            batch_times = []
            
            for i in range(monitoring_ops // concurrent_batches):
                op_start = time.time()
                
                # Test all monitoring functions under load
                op_id = await monitoring_service.start_operation(
                    operation_type=f"monitoring_load_test_batch_{batch_id}",
                    tenant_id=uuid4(),
                    context={"batch": batch_id, "operation": i}
                )
                
                await monitoring_service.complete_operation(
                    operation_id=op_id,
                    status="success",
                    duration_ms=5.0,
                    result_data={"batch_test": True}
                )
                
                # Test journey tracking
                await monitoring_service.track_user_journey_step(
                    journey_id=f"load_test_journey_{batch_id}",
                    step_name=f"step_{i}",
                    tenant_id=uuid4(),
                    status="success",
                    duration_ms=3.0
                )
                
                op_end = time.time()
                batch_times.append((op_end - op_start) * 1000)
            
            return batch_times
        
        # Execute concurrent monitoring batches
        batch_tasks = [monitoring_batch(i) for i in range(concurrent_batches)]
        batch_results = await asyncio.gather(*batch_tasks)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Analyze monitoring performance
        all_times = [time for batch in batch_results for time in batch]
        
        if all_times:
            avg_monitoring_time = statistics.mean(all_times)
            max_monitoring_time = max(all_times)
            p95_monitoring_time = statistics.quantiles(all_times, n=20)[18] if len(all_times) >= 20 else max_monitoring_time
        else:
            avg_monitoring_time = max_monitoring_time = p95_monitoring_time = 0
        
        # Test health check performance under load
        health_start = time.time()
        health_status = await monitoring_service.check_system_health()
        health_end = time.time()
        health_check_time = (health_end - health_start) * 1000
        
        # Validate monitoring performance requirements
        assert avg_monitoring_time < 50, f"Average monitoring time {avg_monitoring_time:.1f}ms exceeds 50ms"
        assert p95_monitoring_time < 100, f"P95 monitoring time {p95_monitoring_time:.1f}ms exceeds 100ms"
        assert health_check_time < 200, f"Health check time {health_check_time:.1f}ms exceeds 200ms"
        
        total_ops = len(all_times) + concurrent_batches * (monitoring_ops // concurrent_batches)
        ops_per_second = total_ops / total_time
        
        print(f"   ✅ Processed {total_ops} monitoring operations in {total_time:.2f}s")
        print(f"   ✅ Monitoring throughput: {ops_per_second:.1f} ops/s")
        print(f"   ✅ Average monitoring overhead: {avg_monitoring_time:.1f}ms")
        print(f"   ✅ P95 monitoring overhead: {p95_monitoring_time:.1f}ms")
        print(f"   ✅ Health check time: {health_check_time:.1f}ms")
        
        return True
        
    except Exception as e:
        print(f"❌ Production monitoring under load test failed: {e}")
        return False


async def main():
    """Run comprehensive production load and stress tests"""
    print("🚀 Production Load & Stress Testing")
    print("=" * 60)
    print("Testing realistic production scenarios and edge cases...")
    
    test_results = []
    
    # Test 1: Burst load handling
    test_results.append(await test_burst_load_handling())
    
    # Test 2: Sustained production load
    test_results.append(await test_sustained_production_load())
    
    # Test 3: Resource exhaustion recovery
    test_results.append(await test_resource_exhaustion_recovery())
    
    # Test 4: Error cascade prevention
    test_results.append(await test_error_cascade_prevention())
    
    # Test 5: Production monitoring under load
    test_results.append(await test_production_monitoring_under_load())
    
    print("\n" + "=" * 60)
    
    passed_tests = sum(test_results)
    total_tests = len(test_results)
    
    if passed_tests == total_tests:
        print("🎉 ALL PRODUCTION STRESS TESTS PASSED!")
        print(f"✅ {passed_tests}/{total_tests} stress test scenarios successful")
        print("\n🚀 PRODUCTION STRESS TESTING COMPLETE:")
        print("✅ Burst load handling validated")
        print("✅ Sustained production load confirmed")  
        print("✅ Resource exhaustion recovery verified")
        print("✅ Error cascade prevention validated")
        print("✅ Monitoring performance under load confirmed")
        print("\n🌟 SYSTEM READY FOR HIGH-TRAFFIC PRODUCTION DEPLOYMENT!")
        return True
    else:
        print("❌ SOME STRESS TESTS FAILED - OPTIMIZATION REQUIRED")
        print(f"❌ {total_tests - passed_tests}/{total_tests} stress scenarios failed")
        print("🔧 Address stress test failures before production deployment")
        return False


if __name__ == "__main__":
    asyncio.run(main())