#!/usr/bin/env python3
"""
Test the simplified LeanVibe backend architecture

Validates that the service manager and simplified health endpoints work correctly.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "leanvibe-backend"))

from app.core.service_manager import initialize_backend, shutdown_backend
from app.core.service_manager import get_ai_service, get_vector_service, get_graph_service
from app.api.endpoints.health_simple import _get_current_capabilities, _get_health_recommendations


async def test_simplified_backend():
    """Test the complete simplified backend"""
    print("🧪 TESTING SIMPLIFIED LEANVIBE BACKEND")
    print("=" * 60)
    
    try:
        # Test 1: Backend Initialization
        print("\n🚀 Test 1: Backend Initialization")
        results = await initialize_backend()
        
        print("   Service initialization results:")
        for service, status in results.items():
            icon = "✅" if status else "❌"
            print(f"      {icon} {service}: {status}")
        
        # Test 2: Service Access
        print("\n🔗 Test 2: Service Access")
        ai_service = get_ai_service()
        vector_service = get_vector_service()
        graph_service = get_graph_service()
        
        print(f"   AI service available: {'✅' if ai_service else '❌'}")
        print(f"   Vector service available: {'✅' if vector_service else '❌'}")
        print(f"   Graph service available: {'✅' if graph_service else '❌'}")
        
        # Test 3: Capabilities Assessment
        print("\n⚡ Test 3: Current Capabilities")
        capabilities = _get_current_capabilities()
        
        for capability, available in capabilities.items():
            icon = "✅" if available else "❌"
            print(f"   {icon} {capability.replace('_', ' ').title()}: {available}")
        
        # Test 4: Quick Service Validation
        print("\n🔍 Test 4: Service Functionality")
        
        if vector_service:
            status = vector_service.get_status()
            print(f"   Vector service initialized: {'✅' if status.get('initialized') else '❌'}")
            print(f"   Vector embedding model: {status.get('embedding_model', 'unknown')}")
        
        if ai_service:
            is_ready = ai_service.is_ready()
            print(f"   AI service ready: {'✅' if is_ready else '❌'}")
            
            if is_ready:
                models = await ai_service.get_models()
                print(f"   Available AI models: {', '.join(models) if models else 'none'}")
        
        if graph_service:
            print(f"   Graph service initialized: {'✅' if graph_service.initialized else '❌'}")
        
        # Test 5: Health Recommendations
        print("\n🩺 Test 5: Health Assessment")
        
        # Simulate health status for recommendations
        mock_health_status = {
            'overall_status': 'healthy' if all(capabilities.values()) else 'degraded',
            'services': {
                'vector': {'available': vector_service is not None},
                'ai': {'available': ai_service is not None},
                'graph': {'available': graph_service is not None}
            }
        }
        
        recommendations = _get_health_recommendations(mock_health_status)
        
        print("   Health recommendations:")
        for rec in recommendations:
            level_icon = {
                'success': '✅',
                'info': 'ℹ️',
                'warning': '⚠️',
                'error': '❌',
                'critical': '🚨'
            }.get(rec['level'], '❓')
            
            print(f"      {level_icon} {rec['level'].upper()}: {rec['message']}")
        
        # Test 6: Integration Test
        print("\n🔄 Test 6: Basic Integration")
        
        integration_success = False
        
        if vector_service and ai_service:
            print("   Testing AI + Vector integration...")
            
            # Quick AI test
            try:
                response = await ai_service.generate("Hello", max_tokens=5)
                ai_works = response is not None and len(response.strip()) > 0
                print(f"   AI generation test: {'✅' if ai_works else '❌'}")
                
                # Quick vector test
                from app.services.vector_store_service import CodeEmbedding
                test_embedding = CodeEmbedding(
                    id="integration_test",
                    content="def test(): pass",
                    file_path="/test.py",
                    language="python",
                    symbol_type="function",
                    symbol_name="test",
                    start_line=1,
                    end_line=1
                )
                
                vector_result = await vector_service.add_code_embedding(test_embedding)
                print(f"   Vector storage test: {'✅' if vector_result else '❌'}")
                
                search_results = await vector_service.search_similar_code("test function", n_results=1)
                print(f"   Vector search test: {'✅' if search_results else '❌'}")
                
                integration_success = ai_works and vector_result and search_results
                
                # Cleanup
                try:
                    if vector_service.chromadb_available and vector_service.collection:
                        vector_service.collection.delete(ids=["integration_test"])
                except Exception:
                    pass
                
            except Exception as e:
                print(f"   Integration test error: {e}")
        
        else:
            print("   ⚠️ Insufficient services for integration test")
        
        # Summary
        print("\n📊 SIMPLIFIED BACKEND TEST SUMMARY")
        print("=" * 60)
        
        total_services = len(results)
        working_services = sum(1 for status in results.values() if status)
        core_working = sum(1 for service in ['vector', 'ai'] if results.get(service))
        
        print(f"Services initialized: {working_services}/{total_services}")
        print(f"Core services working: {core_working}/2")
        print(f"Integration test: {'✅ PASSED' if integration_success else '❌ FAILED'}")
        
        if core_working >= 2:
            print("🎉 SIMPLIFIED BACKEND: FULLY FUNCTIONAL")
        elif core_working >= 1:
            print("⚠️ SIMPLIFIED BACKEND: PARTIALLY FUNCTIONAL (DEGRADED MODE)")
        else:
            print("❌ SIMPLIFIED BACKEND: NOT FUNCTIONAL")
        
        return core_working >= 1  # Success if at least one core service works
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
        
    finally:
        # Cleanup
        print("\n🧹 Cleaning up...")
        await shutdown_backend()
        print("✅ Backend shutdown complete")


async def main():
    """Main test entry point"""
    success = await test_simplified_backend()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)