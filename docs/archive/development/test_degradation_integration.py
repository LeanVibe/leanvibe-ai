#!/usr/bin/env python3
"""
Test integration of service manager with degradation patterns

Validates that the complete system handles service failures gracefully
and continues to provide functionality through fallback mechanisms.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "leanvibe-backend"))

from app.core.service_manager import initialize_backend, shutdown_backend
from app.core.service_manager import get_ai_service, get_vector_service, get_graph_service
from app.core.degradation_patterns import (
    degradation_manager, 
    get_degradation_summary,
    is_service_healthy,
    is_service_degraded,
    is_service_failed
)


async def test_degradation_integration():
    """Test complete degradation integration"""
    print("🛡️ TESTING DEGRADATION PATTERNS INTEGRATION")
    print("=" * 70)
    
    try:
        # Test 1: Initialize backend with degradation patterns
        print("\n🚀 Test 1: Backend Initialization with Degradation")
        results = await initialize_backend()
        
        print("   Service initialization results:")
        for service, status in results.items():
            icon = "✅" if status else "❌"
            print(f"      {icon} {service}: {status}")
        
        # Test 2: Check degradation manager registration
        print("\n📋 Test 2: Degradation Manager Registration")
        
        # Check that services are registered with degradation manager
        degradation_summary = get_degradation_summary()
        
        print(f"   Degradation manager tracking {degradation_summary.get('total_services', 0)} services")
        print(f"   Overall degradation status: {degradation_summary.get('overall_status', 'unknown')}")
        
        if 'services' in degradation_summary:
            for service_name, health in degradation_summary['services'].items():
                has_fallback = health.get('has_fallback', False)
                fallback_icon = "🔄" if has_fallback else "❌"
                print(f"      {service_name}: {fallback_icon} fallback available")
        
        # Test 3: Service Health Assessment
        print("\n🩺 Test 3: Service Health Assessment")
        
        core_services = ['vector', 'ai', 'graph']
        
        for service_name in core_services:
            healthy = is_service_healthy(service_name)
            degraded = is_service_degraded(service_name)
            failed = is_service_failed(service_name)
            
            if healthy:
                status = "✅ HEALTHY"
            elif degraded:
                status = "⚠️ DEGRADED"
            elif failed:
                status = "❌ FAILED"
            else:
                status = "❓ UNKNOWN"
            
            print(f"   {service_name}: {status}")
        
        # Test 4: Simulate Service Operations with Degradation
        print("\n🔄 Test 4: Service Operations with Degradation Protection")
        
        # Test AI service with degradation
        ai_service = get_ai_service()
        if ai_service:
            print("   Testing AI service with degradation protection...")
            
            # Use degradation manager to call AI service
            def ai_operation():
                # This might fail due to resource limits
                return ai_service.generate("Hello", max_tokens=5)
            
            try:
                result = degradation_manager.call_with_degradation('ai', ai_operation)
                
                if result and 'fallback' not in str(result):
                    print("      ✅ AI service working normally")
                elif result:
                    print("      🔄 AI service using fallback")
                else:
                    print("      ❌ AI service failed completely")
                
            except Exception as e:
                print(f"      ❌ AI service error: {e}")
        
        # Test Vector service with degradation
        vector_service = get_vector_service()
        if vector_service:
            print("   Testing Vector service with degradation protection...")
            
            def vector_operation():
                return vector_service.search_similar_code("test query", n_results=1)
            
            try:
                result = degradation_manager.call_with_degradation('vector', vector_operation)
                
                if result and not any(item.get('fallback', False) for item in result if isinstance(item, dict)):
                    print("      ✅ Vector service working normally")
                elif result:
                    print("      🔄 Vector service using fallback")
                else:
                    print("      ❌ Vector service failed completely")
                
            except Exception as e:
                print(f"      ❌ Vector service error: {e}")
        
        # Test 5: Degradation Metrics Analysis
        print("\n📊 Test 5: Degradation Metrics Analysis")
        
        final_summary = get_degradation_summary()
        
        print(f"   Overall system status: {final_summary.get('overall_status', 'unknown')}")
        print(f"   Average success rate: {final_summary.get('average_success_rate', 0):.2%}")
        print(f"   Average degradation rate: {final_summary.get('average_degradation_rate', 0):.2%}")
        
        services_breakdown = final_summary.get('services', {})
        
        print("   Service-specific metrics:")
        for service_name, metrics in services_breakdown.items():
            success_rate = metrics.get('success_rate', 0)
            degradation_rate = metrics.get('degradation_rate', 0)
            circuit_state = metrics.get('circuit_breaker_state', 'unknown')
            
            print(f"      {service_name}:")
            print(f"         Success rate: {success_rate:.2%}")
            print(f"         Degradation rate: {degradation_rate:.2%}")
            print(f"         Circuit breaker: {circuit_state}")
        
        # Test 6: Resilience Validation
        print("\n🛡️ Test 6: System Resilience Validation")
        
        healthy_services = final_summary.get('healthy_services', 0)
        degraded_services = final_summary.get('degraded_services', 0)
        failed_services = final_summary.get('failed_services', 0)
        total_services = final_summary.get('total_services', 0)
        
        print(f"   Service status distribution:")
        print(f"      Healthy: {healthy_services}/{total_services}")
        print(f"      Degraded: {degraded_services}/{total_services}")
        print(f"      Failed: {failed_services}/{total_services}")
        
        # Determine system resilience
        if healthy_services >= total_services * 0.8:
            resilience = "🟢 EXCELLENT"
        elif healthy_services + degraded_services >= total_services * 0.6:
            resilience = "🟡 GOOD (with degradation)"
        elif healthy_services + degraded_services > 0:
            resilience = "🟠 LIMITED"
        else:
            resilience = "🔴 POOR"
        
        print(f"   System resilience: {resilience}")
        
        # Summary
        print("\n📋 DEGRADATION INTEGRATION TEST SUMMARY")
        print("=" * 70)
        
        core_working = sum(1 for service in ['vector', 'ai'] if results.get(service))
        degradation_enabled = final_summary.get('total_services', 0) > 0
        has_fallbacks = any(
            metrics.get('has_fallback', False) 
            for metrics in services_breakdown.values()
        )
        
        print(f"Core services working: {core_working}/2")
        print(f"Degradation patterns enabled: {'✅' if degradation_enabled else '❌'}")
        print(f"Fallback mechanisms available: {'✅' if has_fallbacks else '❌'}")
        print(f"System resilience: {resilience}")
        
        if core_working >= 1 and degradation_enabled:
            print("🎉 DEGRADATION INTEGRATION: SUCCESSFUL")
            print("   System demonstrates graceful degradation capabilities")
            return True
        else:
            print("⚠️ DEGRADATION INTEGRATION: NEEDS IMPROVEMENT")
            return False
            
    except Exception as e:
        print(f"❌ Degradation integration test failed: {e}")
        return False
        
    finally:
        print("\n🧹 Cleaning up...")
        await shutdown_backend()
        print("✅ Backend shutdown complete")


async def main():
    """Main test entry point"""
    success = await test_degradation_integration()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)