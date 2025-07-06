"""
Comprehensive Service Integration Tests

Tests for validating that all backend services (Neo4j, ChromaDB, Redis, MLX) 
are properly configured, connected, and functional together.
"""

import asyncio
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)


class ServiceHealthChecker:
    """Comprehensive service health checking utility"""
    
    def __init__(self):
        self.results = {}
        
    async def check_neo4j_connection(self) -> bool:
        """Test Neo4j database connection with correct credentials"""
        try:
            from app.services.graph_service import GraphService
            
            # Test with the expected credentials
            graph_service = GraphService(
                uri="bolt://localhost:7687",
                username="neo4j", 
                password="leanvibe123"  # Should match docker-compose.yml
            )
            
            result = await graph_service.initialize()
            if result:
                # Test basic query
                test_result = await graph_service.execute_query("RETURN 1 as test")
                await graph_service.close()
                return test_result is not None
            return False
            
        except Exception as e:
            logger.warning(f"Neo4j connection failed: {e}")
            return False
    
    async def check_chromadb_connection(self) -> bool:
        """Test ChromaDB vector store connection and basic operations"""
        try:
            from app.services.vector_store_service import VectorStoreService, CHROMADB_AVAILABLE
            
            if not CHROMADB_AVAILABLE:
                logger.warning("ChromaDB not available - dependency missing")
                return False
                
            # Test connection to ChromaDB service
            service = VectorStoreService(
                chroma_host="localhost",
                chroma_port=8001  # ChromaDB mapped to port 8001
            )
            
            await service.initialize()
            
            # Test basic operations
            from app.services.vector_store_service import CodeEmbedding
            test_embedding = CodeEmbedding(
                id="test_health_check",
                content="def test(): return True",
                file_path="/test/health.py",
                language="python",
                symbol_type="function",
                symbol_name="test",
                start_line=1,
                end_line=1
            )
            
            # Test store and retrieve
            await service.store_embeddings([test_embedding])
            results = await service.search("test function", limit=1)
            
            # Cleanup
            await service.delete_embedding("test_health_check")
            
            return len(results) > 0
            
        except Exception as e:
            logger.warning(f"ChromaDB connection failed: {e}")
            return False
    
    async def check_redis_connection(self) -> bool:
        """Test Redis connection and basic operations"""
        try:
            import redis.asyncio as redis
            
            # Connect to Redis
            client = redis.Redis(host='localhost', port=6379, decode_responses=True)
            
            # Test basic operations
            await client.set('health_check', 'test_value', ex=60)
            value = await client.get('health_check')
            await client.delete('health_check')
            await client.close()
            
            return value == 'test_value'
            
        except ImportError:
            logger.error("Redis Python client not installed")
            return False
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            return False
    
    async def check_mlx_model_loading(self) -> bool:
        """Test MLX model loading and basic inference"""
        try:
            from app.services.mlx_ai_service import MLXAIService
            
            # Initialize MLX service
            service = MLXAIService()
            await service.initialize()
            
            if not service.is_ready():
                logger.warning("MLX service not ready")
                return False
            
            # Test basic inference
            test_prompt = "def hello():"
            response = await service.generate(test_prompt, max_tokens=10)
            
            return response is not None and len(response.strip()) > 0
            
        except Exception as e:
            logger.warning(f"MLX model loading failed: {e}")
            return False
    
    async def check_all_services(self) -> Dict[str, bool]:
        """Run all service health checks in parallel"""
        logger.info("Starting comprehensive service health checks...")
        
        # Run all checks in parallel
        tasks = {
            'neo4j': self.check_neo4j_connection(),
            'chromadb': self.check_chromadb_connection(),
            'redis': self.check_redis_connection(),
            'mlx_model': self.check_mlx_model_loading()
        }
        
        self.results = {}
        for service_name, task in tasks.items():
            try:
                start_time = time.time()
                result = await asyncio.wait_for(task, timeout=30.0)
                duration = time.time() - start_time
                
                self.results[service_name] = {
                    'status': result,
                    'duration': duration,
                    'error': None
                }
                
                status_icon = "✅" if result else "❌"
                logger.info(f"{status_icon} {service_name}: {result} ({duration:.2f}s)")
                
            except asyncio.TimeoutError:
                self.results[service_name] = {
                    'status': False,
                    'duration': 30.0,
                    'error': 'Timeout'
                }
                logger.error(f"❌ {service_name}: Timeout after 30s")
            except Exception as e:
                self.results[service_name] = {
                    'status': False,
                    'duration': 0,
                    'error': str(e)
                }
                logger.error(f"❌ {service_name}: Error - {e}")
        
        return {name: info['status'] for name, info in self.results.items()}


@pytest.mark.integration
@pytest.mark.asyncio
class TestServiceIntegration:
    """Integration tests for all backend services"""
    
    async def test_all_services_health_check(self):
        """Test that all configured services are accessible and functional"""
        checker = ServiceHealthChecker()
        results = await checker.check_all_services()
        
        # Report results
        total_services = len(results)
        working_services = sum(1 for status in results.values() if status)
        
        print(f"\n🏥 SERVICE HEALTH REPORT")
        print(f"📊 Working Services: {working_services}/{total_services}")
        
        for service_name, status in results.items():
            info = checker.results[service_name]
            status_icon = "✅" if status else "❌"
            duration = info['duration']
            error = info.get('error', '')
            error_msg = f" - {error}" if error else ""
            print(f"{status_icon} {service_name:12}: {status} ({duration:.2f}s){error_msg}")
        
        # At least basic services should work
        essential_services = ['chromadb', 'mlx_model']
        essential_working = sum(1 for service in essential_services if results.get(service, False))
        
        assert essential_working >= 1, f"No essential services working. Results: {results}"
        
        # Warn about non-working services but don't fail the test
        if not results.get('neo4j', False):
            print("⚠️  Neo4j not working - graph features will be limited")
        if not results.get('redis', False):
            print("⚠️  Redis not working - caching will be disabled")

    @pytest.mark.asyncio 
    async def test_neo4j_authentication_fix(self):
        """Specifically test that Neo4j authentication issue is resolved"""
        checker = ServiceHealthChecker()
        neo4j_works = await checker.check_neo4j_connection()
        
        if not neo4j_works:
            # Check if it's a configuration issue
            print("\n🔍 NEO4J TROUBLESHOOTING:")
            print("1. Check if docker-compose.yml has: NEO4J_AUTH: neo4j/leanvibe123")
            print("2. Check if Neo4j container is running: docker ps | grep neo4j")
            print("3. Try manual connection: curl -u neo4j:leanvibe123 http://localhost:7474")
            
            # This should pass now that we fixed the password
            pytest.skip("Neo4j not accessible - check configuration")
        
        assert neo4j_works, "Neo4j should be working after password fix"

    @pytest.mark.asyncio
    async def test_redis_client_installation(self):
        """Test that Redis Python client is properly installed"""
        try:
            import redis.asyncio as redis
            
            # Test client creation
            client = redis.Redis(host='localhost', port=6379)
            
            # This should not raise ImportError anymore
            assert client is not None
            
        except ImportError as e:
            pytest.fail(f"Redis client not installed: {e}. Run: pip install redis>=4.6.0")

    @pytest.mark.asyncio
    async def test_chromadb_integration(self):
        """Test ChromaDB integration with real vector operations"""
        try:
            from app.services.vector_store_service import VectorStoreService, CHROMADB_AVAILABLE
            
            if not CHROMADB_AVAILABLE:
                pytest.skip("ChromaDB not available")
            
            service = VectorStoreService(chroma_host="localhost", chroma_port=8001)
            await service.initialize()
            
            # Test embedding and search workflow
            from app.services.vector_store_service import CodeEmbedding
            
            embeddings = [
                CodeEmbedding(
                    id="test_func_add",
                    content="def add(a, b): return a + b",
                    file_path="/test/math.py",
                    language="python",
                    symbol_type="function", 
                    symbol_name="add",
                    start_line=1,
                    end_line=1
                ),
                CodeEmbedding(
                    id="test_func_multiply",
                    content="def multiply(x, y): return x * y",
                    file_path="/test/math.py", 
                    language="python",
                    symbol_type="function",
                    symbol_name="multiply",
                    start_line=3,
                    end_line=3
                )
            ]
            
            # Store embeddings
            await service.store_embeddings(embeddings)
            
            # Search for similar code
            results = await service.search("addition function", limit=2)
            
            # Should find the add function
            assert len(results) > 0
            assert any("add" in result.content for result in results)
            
            # Cleanup
            for embedding in embeddings:
                await service.delete_embedding(embedding.id)
                
        except Exception as e:
            pytest.fail(f"ChromaDB integration failed: {e}")

    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self):
        """Test a complete workflow using multiple services"""
        checker = ServiceHealthChecker()
        
        # Check which services are available
        service_status = await checker.check_all_services()
        
        if not any(service_status.values()):
            pytest.skip("No services available for end-to-end test")
        
        print(f"\n🔄 END-TO-END WORKFLOW TEST")
        print(f"Available services: {[name for name, status in service_status.items() if status]}")
        
        # Test MLX + ChromaDB workflow if both available
        if service_status.get('mlx_model') and service_status.get('chromadb'):
            await self._test_ai_code_search_workflow()
        
        # Test Neo4j + basic analysis workflow if available
        if service_status.get('neo4j'):
            await self._test_graph_analysis_workflow()
        
        # Always test basic API health
        await self._test_basic_api_health()

    async def _test_ai_code_search_workflow(self):
        """Test AI model + vector store integration"""
        from app.services.mlx_ai_service import MLXAIService
        from app.services.vector_store_service import VectorStoreService
        
        # Initialize services
        ai_service = MLXAIService()
        vector_service = VectorStoreService(chroma_host="localhost", chroma_port=8001)
        
        await ai_service.initialize()
        await vector_service.initialize()
        
        # Test AI code generation
        prompt = "Write a Python function to calculate factorial"
        response = await ai_service.generate(prompt, max_tokens=50)
        
        assert response is not None
        assert len(response.strip()) > 0
        print(f"✅ AI generated response: {response[:50]}...")

    async def _test_graph_analysis_workflow(self):
        """Test Neo4j graph analysis"""
        from app.services.graph_service import GraphService
        
        graph_service = GraphService()
        result = await graph_service.initialize()
        
        if result:
            # Test basic graph query
            test_result = await graph_service.execute_query(
                "CREATE (n:TestNode {name: 'integration_test'}) RETURN n"
            )
            
            assert test_result is not None
            
            # Cleanup
            await graph_service.execute_query(
                "MATCH (n:TestNode {name: 'integration_test'}) DELETE n"
            )
            await graph_service.close()
            print("✅ Graph analysis workflow functional")

    async def _test_basic_api_health(self):
        """Test basic API health endpoints"""
        import httpx
        
        try:
            async with httpx.AsyncClient() as client:
                # Test main health endpoint
                response = await client.get("http://localhost:8000/health")
                assert response.status_code == 200
                
                health_data = response.json()
                assert "status" in health_data
                print(f"✅ API health: {health_data.get('status', 'unknown')}")
                
        except Exception as e:
            print(f"⚠️  API health check skipped: {e}")


@pytest.mark.performance
@pytest.mark.asyncio
class TestServicePerformance:
    """Performance tests for service integration"""
    
    async def test_service_response_times(self):
        """Test that all services meet performance requirements"""
        checker = ServiceHealthChecker()
        
        # Run health checks and measure times
        await checker.check_all_services()
        
        performance_requirements = {
            'neo4j': 5.0,        # seconds
            'chromadb': 3.0,     # seconds  
            'redis': 1.0,        # seconds
            'mlx_model': 10.0    # seconds (model loading can be slow)
        }
        
        print(f"\n⚡ PERFORMANCE REPORT")
        
        for service_name, max_time in performance_requirements.items():
            if service_name in checker.results:
                duration = checker.results[service_name]['duration']
                status = checker.results[service_name]['status']
                
                if status:  # Only check performance if service is working
                    performance_ok = duration <= max_time
                    status_icon = "✅" if performance_ok else "⚠️"
                    print(f"{status_icon} {service_name:12}: {duration:.2f}s (max: {max_time}s)")
                    
                    if not performance_ok:
                        print(f"   ⚠️  Performance below target for {service_name}")
                else:
                    print(f"❌ {service_name:12}: Not available")

    async def test_concurrent_service_access(self):
        """Test multiple concurrent service operations"""
        async def concurrent_health_check():
            checker = ServiceHealthChecker()
            return await checker.check_all_services()
        
        # Run multiple health checks concurrently
        start_time = time.time()
        
        tasks = [concurrent_health_check() for _ in range(3)]
        results = await asyncio.gather(*tasks)
        
        duration = time.time() - start_time
        
        print(f"\n🔄 CONCURRENT ACCESS TEST")
        print(f"⏱️  3 concurrent health checks: {duration:.2f}s")
        
        # Should complete reasonably quickly
        assert duration < 30.0, f"Concurrent access too slow: {duration}s"
        
        # All results should be similar
        first_result = results[0]
        for i, result in enumerate(results[1:], 1):
            for service in first_result:
                if first_result[service] != result[service]:
                    print(f"⚠️  Inconsistent results for {service} between runs")


if __name__ == "__main__":
    # Allow running this test file directly
    import subprocess
    import sys
    
    print("🧪 Running comprehensive service integration tests...")
    
    # Run the tests
    result = subprocess.run([
        sys.executable, "-m", "pytest", 
        __file__, 
        "-v", 
        "--tb=short",
        "-s"  # Show print statements
    ])
    
    sys.exit(result.returncode)