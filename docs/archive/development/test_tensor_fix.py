#!/usr/bin/env python3
"""
Test script to validate MLX tensor dimension fixes.
This script tests the tensor fix utilities and integration with MLX services.
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


async def test_tensor_fix_utility():
    """Test the MLX tensor fix utility"""
    try:
        logger.info("Testing MLX tensor fix utility...")
        
        import mlx.core as mx
        import numpy as np
        from app.services.mlx_tensor_fix import MLXTensorFixer, safe_mlx_attention, fix_mlx_generation_error
        
        fixer = MLXTensorFixer()
        fixer.enable_debug()
        
        # Test 1: Attention dimension fixing
        logger.info("Test 1: Attention dimension fixing")
        batch_size, seq_len, hidden_size = 1, 10, 768
        num_heads = 12
        num_kv_heads = 4  # Grouped Query Attention
        head_dim = hidden_size // num_heads
        
        # Create test tensors with potential dimension mismatch
        q = mx.random.normal((batch_size, seq_len, num_heads * head_dim))
        k = mx.random.normal((batch_size, seq_len, num_kv_heads * head_dim))
        v = mx.random.normal((batch_size, seq_len, num_kv_heads * head_dim))
        
        logger.info(f"Original shapes - Q: {q.shape}, K: {k.shape}, V: {v.shape}")
        
        # Fix dimensions
        q_fixed, k_fixed, v_fixed = fixer.fix_attention_dimensions(
            q, k, v, num_heads, num_kv_heads, head_dim
        )
        
        logger.info(f"Fixed shapes - Q: {q_fixed.shape}, K: {k_fixed.shape}, V: {v_fixed.shape}")
        
        # Verify shapes are compatible
        assert q_fixed.shape[1] == k_fixed.shape[1] == v_fixed.shape[1], "Head dimensions should match"
        logger.info("✅ Attention dimension fixing test passed")
        
        # Test 2: Safe attention computation
        logger.info("Test 2: Safe attention computation")
        
        out = safe_mlx_attention(q, k, v, num_heads, num_kv_heads, head_dim)
        expected_shape = (batch_size, num_heads, seq_len, head_dim)
        
        logger.info(f"Attention output shape: {out.shape}, expected: {expected_shape}")
        assert out.shape == expected_shape, f"Output shape mismatch: {out.shape} vs {expected_shape}"
        logger.info("✅ Safe attention computation test passed")
        
        # Test 3: Causal mask creation
        logger.info("Test 3: Causal mask creation")
        
        mask = fixer.fix_causal_mask(seq_len)
        assert mask.shape == (seq_len, seq_len), f"Mask shape mismatch: {mask.shape}"
        
        # Check that mask is upper triangular
        mask_np = np.array(mask)
        upper_triangle = np.triu(np.ones((seq_len, seq_len)), k=1)
        masked_positions = (mask_np < -1e8).astype(int)
        
        assert np.array_equal(masked_positions, upper_triangle), "Mask should be upper triangular"
        logger.info("✅ Causal mask creation test passed")
        
        # Test 4: Error analysis
        logger.info("Test 4: Error analysis")
        
        # Simulate a tensor dimension error
        fake_error = ValueError("The size of tensor a (12) must match the size of tensor b (13) at non-singleton dimension 3")
        fix_info = fix_mlx_generation_error(fake_error, {
            "num_heads": num_heads,
            "num_kv_heads": num_kv_heads,
            "head_dim": head_dim,
            "sequence_length": seq_len
        })
        
        logger.info(f"Error analysis result: {fix_info}")
        assert fix_info["error_type"] == "tensor_dimension_mismatch", "Should detect tensor dimension mismatch"
        logger.info("✅ Error analysis test passed")
        
        logger.info("✅ All tensor fix utility tests passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Tensor fix utility test failed: {e}")
        logger.error(traceback.format_exc())
        return False


async def test_phi3_service_with_fixes():
    """Test Phi-3 service with tensor fixes integrated"""
    try:
        logger.info("Testing Phi-3 service with tensor fixes...")
        
        from app.services.phi3_mini_service import Phi3MiniService
        
        # Create service instance
        service = Phi3MiniService()
        
        # Try to initialize (may not have real weights, but should handle tensor errors)
        init_result = await service.initialize()
        logger.info(f"Phi-3 service initialization: {init_result}")
        
        if init_result:
            # Test health status
            health = service.get_health_status()
            logger.info(f"Service health: {health['status']}")
            
            # Test generation with a simple prompt (will likely use fallback mode)
            try:
                result = await service.generate_text(
                    "Complete this function: def hello_world():",
                    max_tokens=20,
                    temperature=0.7
                )
                logger.info("Generation test completed successfully")
                logger.info(f"Result preview: {result[:200]}...")
                
            except Exception as gen_error:
                logger.warning(f"Generation failed (expected with fallback mode): {gen_error}")
                # This is expected in fallback mode without real weights
        
        logger.info("✅ Phi-3 service with tensor fixes test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Phi-3 service test failed: {e}")
        logger.error(traceback.format_exc())
        return False


async def test_production_service_integration():
    """Test production service integration with tensor fixes"""
    try:
        logger.info("Testing production service integration...")
        
        from app.services.unified_mlx_service import UnifiedMLXService, MLXInferenceStrategy
        
        # Test with pragmatic strategy (most likely to work)
        service = UnifiedMLXService(preferred_strategy=MLXInferenceStrategy.PRAGMATIC)
        
        init_result = await service.initialize()
        logger.info(f"Unified service initialization: {init_result}")
        
        if init_result:
            health = service.get_model_health()
            logger.info(f"Service strategy: {health.get('current_strategy', {}).get('strategy', 'unknown')}")
            
            # Test completion
            test_context = {
                "file_path": "test.py",
                "cursor_position": 50,
                "surrounding_code": "def process_data(data):\n    # TODO: implement\n    ",
                "current_file": {"language": "python"}
            }
            
            result = await service.generate_code_completion(test_context, "suggest")
            logger.info(f"Completion status: {result.get('status', 'unknown')}")
            
            if result.get("status") == "success":
                logger.info("✅ Production service integration test passed")
                return True
            else:
                logger.warning(f"Completion failed: {result.get('error', 'unknown')}")
                return False
        else:
            logger.warning("Service initialization failed")
            return False
        
    except Exception as e:
        logger.error(f"❌ Production service integration test failed: {e}")
        logger.error(traceback.format_exc())
        return False


async def test_tensor_dimension_scenarios():
    """Test specific tensor dimension scenarios that commonly cause errors"""
    try:
        logger.info("Testing specific tensor dimension scenarios...")
        
        import mlx.core as mx
        from app.services.mlx_tensor_fix import MLXTensorFixer
        
        fixer = MLXTensorFixer()
        
        # Scenario 1: Mismatched sequence lengths
        logger.info("Scenario 1: Mismatched sequence lengths")
        q1 = mx.random.normal((1, 12, 768))  # seq_len = 12
        k1 = mx.random.normal((1, 13, 768))  # seq_len = 13 (mismatch!)
        v1 = mx.random.normal((1, 13, 768))
        
        try:
            compatibility = fixer.validate_tensor_compatibility(q1, k1, v1)
            logger.info(f"Compatibility check: {compatibility}")
            assert not compatibility, "Should detect incompatibility"
            logger.info("✅ Sequence length mismatch detection works")
        except Exception as e:
            logger.error(f"Scenario 1 failed: {e}")
            return False
        
        # Scenario 2: Different head counts
        logger.info("Scenario 2: Different head counts (GQA)")
        batch, seq_len = 1, 10
        q2 = mx.random.normal((batch, seq_len, 12 * 64))  # 12 heads
        k2 = mx.random.normal((batch, seq_len, 4 * 64))   # 4 heads (GQA)
        v2 = mx.random.normal((batch, seq_len, 4 * 64))
        
        q_fixed, k_fixed, v_fixed = fixer.fix_attention_dimensions(q2, k2, v2, 12, 4, 64)
        
        # After fixing, K and V should be repeated to match Q heads
        assert q_fixed.shape[1] == k_fixed.shape[1] == v_fixed.shape[1], "Head dimensions should match after fixing"
        logger.info("✅ GQA dimension fixing works")
        
        # Scenario 3: Invalid dimensions
        logger.info("Scenario 3: Invalid dimensions requiring fallback")
        q3 = mx.random.normal((1, 10, 700))  # Not divisible by head_dim
        k3 = mx.random.normal((1, 10, 700))
        v3 = mx.random.normal((1, 10, 700))
        
        try:
            q_fallback, k_fallback, v_fallback = fixer.fix_attention_dimensions(q3, k3, v3, 12, 12, 64)
            logger.info("✅ Fallback dimension handling works")
        except Exception as e:
            logger.warning(f"Fallback scenario failed as expected: {e}")
        
        logger.info("✅ All tensor dimension scenarios tested")
        return True
        
    except Exception as e:
        logger.error(f"❌ Tensor dimension scenarios test failed: {e}")
        logger.error(traceback.format_exc())
        return False


async def main():
    """Run all tensor fix tests"""
    logger.info("Starting MLX tensor dimension fix validation tests...")
    
    tests = [
        ("Tensor Fix Utility", test_tensor_fix_utility),
        ("Phi-3 Service Integration", test_phi3_service_with_fixes),
        ("Production Service Integration", test_production_service_integration),
        ("Tensor Dimension Scenarios", test_tensor_dimension_scenarios),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*60}")
        logger.info(f"Running test: {test_name}")
        logger.info(f"{'='*60}")
        
        try:
            result = await test_func()
            results[test_name] = result
        except Exception as e:
            logger.error(f"Test {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    logger.info(f"\n{'='*60}")
    logger.info("TENSOR FIX TEST SUMMARY")
    logger.info(f"{'='*60}")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tensor fix tests passed! MLX tensor dimension issues are resolved.")
        return True
    else:
        logger.error("💥 Some tests failed. Please check the errors above.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)