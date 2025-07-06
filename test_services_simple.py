#!/usr/bin/env python3
"""
Simple service integration test to verify fixes
"""

import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_neo4j():
    """Test Neo4j connection with correct API"""
    try:
        import sys
        sys.path.insert(0, '/Users/bogdan/work/leanvibe-ai/leanvibe-backend')
        from app.services.graph_service import GraphService
        
        service = GraphService()
        result = await service.initialize()
        
        if result:
            logger.info("✅ Neo4j: Connection successful")
            await service.close()
            return True
        else:
            logger.warning("❌ Neo4j: Connection failed")
            return False
            
    except Exception as e:
        logger.warning(f"❌ Neo4j: Error - {e}")
        return False


async def test_chromadb():
    """Test ChromaDB HTTP connection"""
    try:
        import sys
        sys.path.insert(0, '/Users/bogdan/work/leanvibe-ai/leanvibe-backend')
        from app.services.vector_store_service import VectorStoreService
        
        service = VectorStoreService(use_http=True, host="localhost", port=8001)
        result = await service.initialize()
        
        if result:
            logger.info("✅ ChromaDB: HTTP connection successful")
            return True
        else:
            logger.warning("❌ ChromaDB: Connection failed")
            return False
            
    except Exception as e:
        logger.warning(f"❌ ChromaDB: Error - {e}")
        return False


async def test_redis():
    """Test Redis connection"""
    try:
        import redis.asyncio as redis
        
        client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        await client.set('test_key', 'test_value', ex=10)
        value = await client.get('test_key')
        await client.delete('test_key')
        await client.aclose()
        
        if value == 'test_value':
            logger.info("✅ Redis: Connection and operations successful")
            return True
        else:
            logger.warning("❌ Redis: Operations failed")
            return False
            
    except Exception as e:
        logger.warning(f"❌ Redis: Error - {e}")
        return False


async def test_ollama():
    """Test Ollama AI service"""
    try:
        import sys
        sys.path.insert(0, '/Users/bogdan/work/leanvibe-ai/leanvibe-backend')
        from app.services.ollama_ai_service import OllamaAIService
        
        service = OllamaAIService()
        result = await service.initialize()
        
        if result and service.is_ready():
            # Test with a very small prompt to avoid memory issues
            response = await service.generate("Hello", max_tokens=5)
            await service.close()
            
            if response and len(response.strip()) > 0:
                logger.info("✅ Ollama: AI generation successful")
                return True
            else:
                logger.warning("❌ Ollama: Generation failed")
                return False
        else:
            logger.warning("❌ Ollama: Service not ready")
            return False
            
    except Exception as e:
        logger.warning(f"❌ Ollama: Error - {e}")
        return False


async def main():
    """Run all service tests"""
    logger.info("🧪 Testing LeanVibe Backend Services")
    logger.info("=" * 50)
    
    # Test all services
    tests = {
        'Neo4j': test_neo4j(),
        'ChromaDB': test_chromadb(),
        'Redis': test_redis(),
        'Ollama': test_ollama()
    }
    
    results = {}
    for service_name, test_task in tests.items():
        logger.info(f"🔍 Testing {service_name}...")
        try:
            results[service_name] = await asyncio.wait_for(test_task, timeout=30.0)
        except asyncio.TimeoutError:
            logger.warning(f"❌ {service_name}: Timeout after 30s")
            results[service_name] = False
        except Exception as e:
            logger.error(f"❌ {service_name}: Exception - {e}")
            results[service_name] = False
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("📊 TEST RESULTS SUMMARY")
    
    working_count = sum(1 for result in results.values() if result)
    total_count = len(results)
    
    for service, result in results.items():
        status = "✅ WORKING" if result else "❌ FAILED"
        logger.info(f"{service:12}: {status}")
    
    logger.info(f"\n🎯 Overall: {working_count}/{total_count} services functional")
    
    if working_count >= 2:
        logger.info("🎉 Sufficient services working for basic functionality")
        return 0
    else:
        logger.warning("⚠️ Too few services working for full functionality")
        return 1


if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)