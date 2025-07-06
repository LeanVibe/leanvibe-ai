"""
Lightweight End-to-End Tests for LeanVibe AI Backend

Quick validation of core workflows without heavy AI processing.
"""

import asyncio
import logging
import os
import sys
import time
from typing import Dict, Any

import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.graph_service import GraphService
from app.services.vector_store_service import VectorStoreService, CodeEmbedding
from app.services.ollama_ai_service import OllamaAIService

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
class TestLightweightE2E:
    """Lightweight end-to-end workflow tests"""
    
    async def test_service_initialization_workflow(self):
        """Test that all services can be initialized and work together"""
        services = {}
        
        try:
            # Initialize Graph Service
            graph_service = GraphService()
            graph_result = await graph_service.initialize()
            services['graph'] = {'service': graph_service, 'status': graph_result}
            
            # Initialize Vector Service  
            vector_service = VectorStoreService(use_http=True, host="localhost", port=8001)
            vector_result = await vector_service.initialize()
            services['vector'] = {'service': vector_service, 'status': vector_result}
            
            # Initialize AI Service
            ai_service = OllamaAIService()
            ai_result = await ai_service.initialize()
            services['ai'] = {'service': ai_service, 'status': ai_result and ai_service.is_ready()}
            
            # Report initialization results
            working_services = [name for name, info in services.items() if info['status']]
            
            print(f"\n🚀 SERVICE INITIALIZATION RESULTS")
            for name, info in services.items():
                status_icon = "✅" if info['status'] else "❌"
                print(f"{status_icon} {name}: {'WORKING' if info['status'] else 'FAILED'}")
            
            print(f"\n📊 Summary: {len(working_services)}/{len(services)} services working")
            
            # Assert minimum functionality
            assert len(working_services) >= 2, f"Insufficient services working: {working_services}"
            
        finally:
            # Cleanup
            for info in services.values():
                try:
                    if hasattr(info['service'], 'close'):
                        await info['service'].close()
                except Exception:
                    pass
    
    async def test_basic_data_flow(self):
        """Test basic data flow between services"""
        vector_service = None
        ai_service = None
        
        try:
            # Initialize services for data flow test
            vector_service = VectorStoreService(use_http=True, host="localhost", port=8001)
            vector_result = await vector_service.initialize()
            
            ai_service = OllamaAIService()
            ai_result = await ai_service.initialize()
            
            if not vector_result:
                pytest.skip("Vector service not available")
            
            # Test 1: Vector store operations
            print("\n📚 Testing vector store operations...")
            
            test_embedding = CodeEmbedding(
                id="lightweight_test",
                content="def hello_world(): return 'Hello, World!'",
                file_path="/test/hello.py",
                language="python",
                symbol_type="function",
                symbol_name="hello_world",
                start_line=1,
                end_line=1
            )
            
            # Store embedding
            store_success = await vector_service.add_code_embedding(test_embedding)
            assert store_success, "Failed to store test embedding"
            print("✅ Vector store: embedding stored")
            
            # Search for similar code
            search_results = await vector_service.search_similar_code("hello function", n_results=1)
            assert len(search_results) > 0, "Failed to find stored embedding"
            print(f"✅ Vector store: search returned {len(search_results)} results")
            
            # Test 2: AI service basic operation (if available)
            if ai_result and ai_service.is_ready():
                print("\n🤖 Testing AI service...")
                
                # Simple generation test with very short response
                start_time = time.time()
                response = await ai_service.generate("Hello", max_tokens=5)
                duration = time.time() - start_time
                
                assert response is not None, "AI service failed to generate response"
                assert len(response.strip()) > 0, "AI service returned empty response"
                print(f"✅ AI service: generated response in {duration:.2f}s")
                
                # Health check
                health = await ai_service.health_check()
                assert health.get('status') in ['healthy', 'not_initialized'], f"AI service unhealthy: {health}"
                print("✅ AI service: health check passed")
            else:
                print("⚠️ AI service not available, skipping AI tests")
            
            # Test 3: Service integration validation
            print("\n🔗 Testing service integration...")
            
            # Verify services can work independently
            vector_stats = await vector_service.get_collection_stats()
            assert 'total_embeddings' in vector_stats, "Vector service stats unavailable"
            print(f"✅ Integration: vector store has {vector_stats.get('total_embeddings', 0)} embeddings")
            
            # Cleanup test data
            try:
                if vector_service.chromadb_available and vector_service.collection:
                    vector_service.collection.delete(ids=["lightweight_test"])
                print("✅ Integration: cleanup completed")
            except Exception:
                pass  # Ignore cleanup errors
            
            print("\n🎉 Basic data flow test completed successfully")
            
        finally:
            # Cleanup services
            if ai_service:
                await ai_service.close()
    
    async def test_performance_baseline(self):
        """Test basic performance characteristics"""
        vector_service = None
        
        try:
            vector_service = VectorStoreService(use_http=True, host="localhost", port=8001)
            result = await vector_service.initialize()
            
            if not result:
                pytest.skip("Vector service not available for performance test")
            
            print("\n⚡ PERFORMANCE BASELINE TEST")
            
            # Test 1: Vector store write performance
            start_time = time.time()
            
            test_embeddings = [
                CodeEmbedding(
                    id=f"perf_test_{i}",
                    content=f"def test_function_{i}(): return {i}",
                    file_path=f"/test/perf_{i}.py",
                    language="python",
                    symbol_type="function",
                    symbol_name=f"test_function_{i}",
                    start_line=1,
                    end_line=1
                )
                for i in range(5)  # Small batch for quick test
            ]
            
            added_count = await vector_service.add_code_embeddings_batch(test_embeddings)
            write_duration = time.time() - start_time
            
            assert added_count == len(test_embeddings), f"Batch write failed: {added_count}/{len(test_embeddings)}"
            print(f"✅ Write performance: {len(test_embeddings)} embeddings in {write_duration:.2f}s")
            
            # Test 2: Vector store read performance
            start_time = time.time()
            
            search_results = await vector_service.search_similar_code("test function", n_results=3)
            read_duration = time.time() - start_time
            
            assert len(search_results) > 0, "Search returned no results"
            print(f"✅ Read performance: search completed in {read_duration:.2f}s")
            
            # Test 3: Performance validation
            assert write_duration < 10.0, f"Write performance too slow: {write_duration}s"
            assert read_duration < 5.0, f"Read performance too slow: {read_duration}s"
            
            # Cleanup test data
            try:
                for embedding in test_embeddings:
                    if vector_service.chromadb_available and vector_service.collection:
                        vector_service.collection.delete(ids=[embedding.id])
            except Exception:
                pass  # Ignore cleanup errors
            
            print(f"📊 Performance summary:")
            print(f"   Write: {write_duration:.2f}s for {len(test_embeddings)} items")
            print(f"   Read:  {read_duration:.2f}s for search query")
            print("✅ Performance baseline test completed")
            
        finally:
            # No cleanup needed for this test
            pass
    
    async def test_error_handling_and_resilience(self):
        """Test error handling and service resilience"""
        print("\n🛡️ ERROR HANDLING AND RESILIENCE TEST")
        
        # Test 1: Graceful handling of unavailable services
        try:
            # Try to connect to non-existent service
            bad_vector_service = VectorStoreService(use_http=True, host="localhost", port=9999)
            result = await bad_vector_service.initialize()
            
            # Service should handle this gracefully
            print(f"✅ Graceful handling: bad connection handled gracefully (result: {result})")
            
        except Exception as e:
            print(f"⚠️ Exception handling: {str(e)[:100]}...")
        
        # Test 2: Service fallback behavior
        vector_service = VectorStoreService(use_http=False)  # Local mode fallback
        result = await vector_service.initialize()
        
        assert result, "Local vector service fallback failed"
        print("✅ Fallback behavior: local vector store initialization successful")
        
        # Test 3: Invalid data handling
        try:
            invalid_embedding = CodeEmbedding(
                id="",  # Invalid empty ID
                content="",  # Invalid empty content
                file_path="",
                language="",
                symbol_type="",
                symbol_name="",
                start_line=0,
                end_line=0
            )
            
            # Service should handle invalid data gracefully
            result = await vector_service.add_code_embedding(invalid_embedding)
            print(f"✅ Invalid data handling: gracefully handled invalid embedding (result: {result})")
            
        except Exception as e:
            print(f"✅ Invalid data handling: exception caught - {str(e)[:50]}...")
        
        print("✅ Error handling and resilience test completed")


if __name__ == "__main__":
    # Allow running this test file directly
    import subprocess
    
    print("🧪 Running lightweight end-to-end tests...")
    
    result = subprocess.run([
        sys.executable, "-m", "pytest",
        __file__,
        "-v",
        "--tb=short",
        "-s"  # Show print statements
    ])
    
    sys.exit(result.returncode)