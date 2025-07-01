#!/usr/bin/env python3
"""
Simple test script for MLX tensor dimension fixes (no model downloads required).
"""

import sys
import logging
from pathlib import Path

# Add the backend app to the path
backend_path = Path(__file__).parent / "leanvibe-backend"
sys.path.insert(0, str(backend_path))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_basic_tensor_operations():
    """Test basic MLX tensor operations"""
    try:
        import mlx.core as mx
        import numpy as np
        
        logger.info("Testing basic MLX tensor operations...")
        
        # Test 1: Basic tensor creation
        x = mx.array([1, 2, 3])
        y = x * 2
        mx.eval(y)
        logger.info("✅ Basic tensor operations work")
        
        # Test 2: Attention-like tensor operations
        batch_size, seq_len, hidden_size = 1, 5, 64
        
        # Create query, key, value tensors
        q = mx.random.normal((batch_size, seq_len, hidden_size))
        k = mx.random.normal((batch_size, seq_len, hidden_size))  
        v = mx.random.normal((batch_size, seq_len, hidden_size))
        
        # Simple attention computation
        scores = q @ k.transpose(0, 2, 1)  # [batch, seq_len, seq_len]
        attn_weights = mx.softmax(scores, axis=-1)
        out = attn_weights @ v  # [batch, seq_len, hidden_size]
        
        mx.eval(out)
        logger.info(f"✅ Attention-like computation successful: {out.shape}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Basic tensor operations failed: {e}")
        return False


def test_tensor_fix_utility():
    """Test the tensor fix utility without model dependencies"""
    try:
        from app.services.mlx_tensor_fix import MLXTensorFixer, fix_mlx_generation_error
        import mlx.core as mx
        
        logger.info("Testing tensor fix utility...")
        
        fixer = MLXTensorFixer()
        
        # Test error analysis
        fake_error = ValueError("The size of tensor a (12) must match the size of tensor b (13) at non-singleton dimension 3")
        fix_info = fix_mlx_generation_error(fake_error, {"test": "context"})
        
        logger.info(f"Error analysis: {fix_info['error_type']}")
        assert fix_info["error_type"] == "tensor_dimension_mismatch"
        
        # Test causal mask creation
        seq_len = 8
        mask = fixer.fix_causal_mask(seq_len)
        assert mask.shape == (seq_len, seq_len)
        logger.info(f"✅ Causal mask created: {mask.shape}")
        
        # Test tensor compatibility
        t1 = mx.random.normal((1, 10, 64))
        t2 = mx.random.normal((1, 10, 64))
        t3 = mx.random.normal((1, 12, 64))  # Different seq_len
        
        compatible = fixer.validate_tensor_compatibility(t1, t2)
        assert compatible, "Compatible tensors should pass validation"
        
        incompatible = fixer.validate_tensor_compatibility(t1, t3)
        assert not incompatible, "Incompatible tensors should fail validation"
        
        logger.info("✅ Tensor fix utility tests passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Tensor fix utility test failed: {e}")
        return False


def test_dimension_fixing():
    """Test specific dimension fixing scenarios"""
    try:
        from app.services.mlx_tensor_fix import MLXTensorFixer
        import mlx.core as mx
        
        logger.info("Testing dimension fixing scenarios...")
        
        fixer = MLXTensorFixer()
        
        # Scenario: Grouped Query Attention (GQA) dimension mismatch
        batch_size, seq_len = 1, 8
        num_heads = 12
        num_kv_heads = 4  # Fewer KV heads (typical in GQA)
        head_dim = 64
        
        q = mx.random.normal((batch_size, seq_len, num_heads * head_dim))
        k = mx.random.normal((batch_size, seq_len, num_kv_heads * head_dim))
        v = mx.random.normal((batch_size, seq_len, num_kv_heads * head_dim))
        
        logger.info(f"Before fixing - Q: {q.shape}, K: {k.shape}, V: {v.shape}")
        
        # Fix dimensions
        q_fixed, k_fixed, v_fixed = fixer.fix_attention_dimensions(
            q, k, v, num_heads, num_kv_heads, head_dim
        )
        
        logger.info(f"After fixing - Q: {q_fixed.shape}, K: {k_fixed.shape}, V: {v_fixed.shape}")
        
        # Verify: all tensors should now have the same number of heads
        assert q_fixed.shape[1] == k_fixed.shape[1] == v_fixed.shape[1], "Head counts should match"
        assert q_fixed.shape[1] == num_heads, "Should have correct number of heads"
        
        logger.info("✅ GQA dimension fixing successful")
        return True
        
    except Exception as e:
        logger.error(f"❌ Dimension fixing test failed: {e}")
        return False


def test_safe_computation():
    """Test safe computation without full model"""
    try:
        from app.services.mlx_tensor_fix import safe_mlx_attention
        import mlx.core as mx
        
        logger.info("Testing safe computation...")
        
        # Test parameters
        batch_size, seq_len, head_dim = 1, 6, 64
        num_heads = 8
        num_kv_heads = 2
        
        # Create test tensors
        q = mx.random.normal((batch_size, seq_len, num_heads * head_dim))
        k = mx.random.normal((batch_size, seq_len, num_kv_heads * head_dim))
        v = mx.random.normal((batch_size, seq_len, num_kv_heads * head_dim))
        
        # Use safe attention
        output = safe_mlx_attention(q, k, v, num_heads, num_kv_heads, head_dim)
        
        expected_shape = (batch_size, num_heads, seq_len, head_dim)
        assert output.shape == expected_shape, f"Output shape mismatch: {output.shape} vs {expected_shape}"
        
        logger.info(f"✅ Safe attention computation successful: {output.shape}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Safe computation test failed: {e}")
        return False


def main():
    """Run all simple tests"""
    logger.info("Running MLX tensor fix simple validation tests...")
    
    tests = [
        ("Basic Tensor Operations", test_basic_tensor_operations),
        ("Tensor Fix Utility", test_tensor_fix_utility),
        ("Dimension Fixing", test_dimension_fixing),
        ("Safe Computation", test_safe_computation),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} ---")
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            logger.error(f"Test {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*50}")
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("\n🎉 All tensor fix tests passed!")
        logger.info("The MLX tensor dimension mismatch issue should now be resolved.")
        return True
    else:
        logger.error("\n💥 Some tests failed.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)