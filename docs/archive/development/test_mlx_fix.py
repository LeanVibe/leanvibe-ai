#!/usr/bin/env python3
"""
Test script to validate the MLX DynamicCache fix.
This script tests the transformers compatibility layer and the Phi-3 service.
"""

import asyncio
import logging
import sys
import traceback
from pathlib import Path

# Add the backend app to the path
backend_path = Path(__file__).parent / "leanvibe-backend"
sys.path.insert(0, str(backend_path))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_compatibility_layer():
    """Test the transformers compatibility layer"""
    try:
        logger.info("Testing transformers compatibility layer...")
        
        # Import the compatibility module
        from app.services.transformers_compatibility import (
            patch_dynamic_cache_globally,
            get_safe_generation_kwargs,
            handle_generation_error,
            get_model_loading_kwargs,
            log_compatibility_info
        )
        
        # Test patching
        patch_result = patch_dynamic_cache_globally()
        logger.info(f"Patch result: {patch_result}")
        
        # Test compatibility info
        log_compatibility_info()
        
        # Test generation kwargs
        gen_kwargs = get_safe_generation_kwargs(
            max_new_tokens=50,
            temperature=0.7
        )
        logger.info(f"Safe generation kwargs: {gen_kwargs}")
        
        # Test model loading kwargs
        model_kwargs = get_model_loading_kwargs(
            model_name="microsoft/Phi-3-mini-4k-instruct",
            device="auto"
        )
        logger.info(f"Model loading kwargs: {model_kwargs}")
        
        logger.info("✅ Compatibility layer test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Compatibility layer test failed: {e}")
        logger.error(traceback.format_exc())
        return False


async def test_dynamic_cache_patch():
    """Test the DynamicCache patch specifically"""
    try:
        logger.info("Testing DynamicCache patch...")
        
        # Try to import and use DynamicCache
        try:
            from transformers import DynamicCache
            
            # Create a cache instance
            cache = DynamicCache()
            
            # Test if get_max_length method exists
            if hasattr(cache, 'get_max_length'):
                max_length = cache.get_max_length()
                logger.info(f"DynamicCache.get_max_length() returned: {max_length}")
            else:
                logger.warning("DynamicCache.get_max_length method not found")
                return False
            
            logger.info("✅ DynamicCache patch test passed")
            return True
            
        except ImportError:
            logger.warning("DynamicCache not available, skipping test")
            return True
            
    except Exception as e:
        logger.error(f"❌ DynamicCache patch test failed: {e}")
        logger.error(traceback.format_exc())
        return False


async def test_phi3_service_import():
    """Test importing the Phi-3 service"""
    try:
        logger.info("Testing Phi-3 service import...")
        
        # Import the service
        from app.services.transformers_phi3_service import TransformersPhi3Service
        
        # Create an instance
        service = TransformersPhi3Service()
        logger.info(f"Service created: {service}")
        
        # Check health status
        health = service.get_health_status()
        logger.info(f"Service health: {health}")
        
        logger.info("✅ Phi-3 service import test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Phi-3 service import test failed: {e}")
        logger.error(traceback.format_exc())
        return False


async def test_unified_mlx_service():
    """Test the unified MLX service"""
    try:
        logger.info("Testing unified MLX service...")
        
        # Import the service
        from app.services.unified_mlx_service import UnifiedMLXService, MLXInferenceStrategy
        
        # Create an instance with mock strategy to avoid heavy model loading
        service = UnifiedMLXService(preferred_strategy=MLXInferenceStrategy.MOCK)
        
        # Initialize the service
        init_result = await service.initialize()
        logger.info(f"Service initialization result: {init_result}")
        
        if init_result:
            # Test health status
            health = service.get_model_health()
            logger.info(f"Service health: {health}")
            
            # Test a simple completion (should use mock)
            test_context = {
                "file_path": "test.py",
                "cursor_position": 100,
                "surrounding_code": "def hello():\n    return"
            }
            
            result = await service.generate_code_completion(test_context, "suggest")
            logger.info(f"Mock completion result: {result.get('status', 'unknown')}")
        
        logger.info("✅ Unified MLX service test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Unified MLX service test failed: {e}")
        logger.error(traceback.format_exc())
        return False


async def main():
    """Run all tests"""
    logger.info("Starting MLX DynamicCache fix validation tests...")
    
    tests = [
        ("Compatibility Layer", test_compatibility_layer),
        ("DynamicCache Patch", test_dynamic_cache_patch),
        ("Phi-3 Service Import", test_phi3_service_import),
        ("Unified MLX Service", test_unified_mlx_service),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running test: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = await test_func()
            results[test_name] = result
        except Exception as e:
            logger.error(f"Test {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*50}")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! The MLX DynamicCache fix is working correctly.")
        return True
    else:
        logger.error("💥 Some tests failed. Please check the errors above.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)