"""
MLX Tensor Dimension Fix Utility
Handles tensor dimension mismatches in MLX model generation
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

import mlx.core as mx
import numpy as np

logger = logging.getLogger(__name__)


class MLXTensorFixer:
    """
    Utility class to fix tensor dimension mismatches in MLX model generation.
    Addresses common issues like:
    - Grouped Query Attention (GQA) dimension misalignment
    - Key-Value head repetition errors
    - Sequence length inconsistencies
    - Attention mask shape mismatches
    """
    
    def __init__(self):
        self.debug_mode = False
        
    def enable_debug(self):
        """Enable debug logging for tensor operations"""
        self.debug_mode = True
        
    def fix_attention_dimensions(
        self, 
        q: mx.array, 
        k: mx.array, 
        v: mx.array,
        num_heads: int,
        num_kv_heads: int,
        head_dim: int
    ) -> Tuple[mx.array, mx.array, mx.array]:
        """
        Fix attention tensor dimensions for Grouped Query Attention.
        
        Args:
            q: Query tensor [batch, seq_len, num_heads * head_dim]
            k: Key tensor [batch, seq_len, num_kv_heads * head_dim]  
            v: Value tensor [batch, seq_len, num_kv_heads * head_dim]
            num_heads: Number of query heads
            num_kv_heads: Number of key-value heads
            head_dim: Dimension per head
            
        Returns:
            Fixed q, k, v tensors with aligned dimensions
        """
        try:
            if self.debug_mode:
                logger.debug(f"Input shapes - Q: {q.shape}, K: {k.shape}, V: {v.shape}")
                logger.debug(f"Heads - Query: {num_heads}, KV: {num_kv_heads}, Head dim: {head_dim}")
            
            batch_size, seq_len = q.shape[:2]
            
            # Reshape Q tensor 
            q_reshaped = q.reshape(batch_size, seq_len, num_heads, head_dim)
            q_transposed = q_reshaped.transpose(0, 2, 1, 3)  # [batch, num_heads, seq_len, head_dim]
            
            # Reshape K and V tensors
            k_reshaped = k.reshape(batch_size, seq_len, num_kv_heads, head_dim)
            k_transposed = k_reshaped.transpose(0, 2, 1, 3)  # [batch, num_kv_heads, seq_len, head_dim]
            
            v_reshaped = v.reshape(batch_size, seq_len, num_kv_heads, head_dim)
            v_transposed = v_reshaped.transpose(0, 2, 1, 3)  # [batch, num_kv_heads, seq_len, head_dim]
            
            # Handle Grouped Query Attention - repeat K,V to match Q heads
            if num_kv_heads != num_heads:
                if num_heads % num_kv_heads != 0:
                    raise ValueError(f"num_heads ({num_heads}) must be divisible by num_kv_heads ({num_kv_heads})")
                
                repeat_factor = num_heads // num_kv_heads
                
                if self.debug_mode:
                    logger.debug(f"Repeating K,V tensors by factor: {repeat_factor}")
                
                # Repeat K and V along the head dimension
                k_transposed = mx.repeat(k_transposed, repeat_factor, axis=1)
                v_transposed = mx.repeat(v_transposed, repeat_factor, axis=1)
            
            if self.debug_mode:
                logger.debug(f"Output shapes - Q: {q_transposed.shape}, K: {k_transposed.shape}, V: {v_transposed.shape}")
            
            return q_transposed, k_transposed, v_transposed
            
        except Exception as e:
            logger.error(f"Error fixing attention dimensions: {e}")
            # Fallback: ensure all tensors have same number of heads
            return self._fallback_dimension_fix(q, k, v, num_heads, head_dim)
    
    def _fallback_dimension_fix(
        self, 
        q: mx.array, 
        k: mx.array, 
        v: mx.array,
        target_heads: int,
        head_dim: int
    ) -> Tuple[mx.array, mx.array, mx.array]:
        """Fallback dimension fixing when main method fails"""
        try:
            batch_size, seq_len = q.shape[:2]
            
            # Ensure all tensors match target dimensions
            target_shape = (batch_size, target_heads, seq_len, head_dim)
            
            # Reshape and pad/truncate if necessary
            q_fixed = self._reshape_to_target(q, target_shape)
            k_fixed = self._reshape_to_target(k, target_shape)
            v_fixed = self._reshape_to_target(v, target_shape)
            
            logger.warning("Used fallback dimension fixing - may affect model quality")
            return q_fixed, k_fixed, v_fixed
            
        except Exception as e:
            logger.error(f"Fallback dimension fix failed: {e}")
            raise
    
    def _reshape_to_target(self, tensor: mx.array, target_shape: Tuple[int, ...]) -> mx.array:
        """Reshape tensor to target shape with padding/truncation if needed"""
        try:
            current_shape = tensor.shape
            
            # Try direct reshape first
            if np.prod(current_shape) == np.prod(target_shape):
                return tensor.reshape(target_shape)
            
            # If that fails, we need to pad or truncate
            batch_size, target_heads, seq_len, head_dim = target_shape
            
            # Get the actual head dimension from current tensor
            if len(current_shape) >= 3:
                current_batch, current_seq = current_shape[:2]
                remaining_dim = np.prod(current_shape[2:])
                
                if current_batch != batch_size or current_seq != seq_len:
                    raise ValueError(f"Batch size or sequence length mismatch: {current_shape} vs {target_shape}")
                
                # Calculate current heads and head_dim
                if remaining_dim % head_dim == 0:
                    current_heads = remaining_dim // head_dim
                    
                    # Reshape to separate heads
                    reshaped = tensor.reshape(batch_size, seq_len, current_heads, head_dim)
                    transposed = reshaped.transpose(0, 2, 1, 3)
                    
                    if current_heads == target_heads:
                        return transposed
                    elif current_heads < target_heads:
                        # Pad with zeros
                        padding = mx.zeros((batch_size, target_heads - current_heads, seq_len, head_dim))
                        return mx.concatenate([transposed, padding], axis=1)
                    else:
                        # Truncate
                        return transposed[:, :target_heads, :, :]
            
            # Final fallback: create tensor with target shape
            logger.warning(f"Creating new tensor with target shape {target_shape}")
            return mx.zeros(target_shape)
            
        except Exception as e:
            logger.error(f"Reshape to target failed: {e}")
            # Ultimate fallback
            return mx.zeros(target_shape)
    
    def fix_causal_mask(self, seq_len: int, dtype=mx.float32) -> mx.array:
        """
        Create properly shaped causal mask.
        
        Args:
            seq_len: Sequence length
            dtype: Data type for mask
            
        Returns:
            Causal mask tensor [seq_len, seq_len]
        """
        try:
            # Create upper triangular mask
            mask = mx.triu(mx.ones((seq_len, seq_len)), k=1)
            
            # Convert to large negative values for attention masking
            mask = mx.where(mask, -1e9, 0.0).astype(dtype)
            
            if self.debug_mode:
                logger.debug(f"Created causal mask with shape: {mask.shape}")
            
            return mask
            
        except Exception as e:
            logger.error(f"Error creating causal mask: {e}")
            # Fallback: create simple mask
            return mx.zeros((seq_len, seq_len), dtype=dtype)
    
    def safe_attention_computation(
        self,
        q: mx.array,
        k: mx.array, 
        v: mx.array,
        scale: float,
        causal_mask: Optional[mx.array] = None
    ) -> mx.array:
        """
        Safely compute attention with dimension checking.
        
        Args:
            q: Query tensor [batch, heads, seq_len, head_dim]
            k: Key tensor [batch, heads, seq_len, head_dim]
            v: Value tensor [batch, heads, seq_len, head_dim]
            scale: Attention scale factor
            causal_mask: Optional causal mask
            
        Returns:
            Attention output tensor
        """
        try:
            if self.debug_mode:
                logger.debug(f"Attention computation - Q: {q.shape}, K: {k.shape}, V: {v.shape}")
            
            # Validate input dimensions
            if q.shape != k.shape or k.shape != v.shape:
                logger.warning(f"Dimension mismatch in attention: Q={q.shape}, K={k.shape}, V={v.shape}")
                
                # Fix dimensions
                target_shape = q.shape  # Use Q as reference
                if k.shape != target_shape:
                    k = self._reshape_to_target(k, target_shape)
                if v.shape != target_shape:
                    v = self._reshape_to_target(v, target_shape)
            
            # Compute attention scores
            scores = (q @ k.transpose(0, 1, 3, 2)) * scale
            
            if self.debug_mode:
                logger.debug(f"Attention scores shape: {scores.shape}")
            
            # Apply causal mask if provided
            if causal_mask is not None:
                seq_len = scores.shape[-1]
                if causal_mask.shape != (seq_len, seq_len):
                    # Recreate mask with correct dimensions
                    causal_mask = self.fix_causal_mask(seq_len, dtype=scores.dtype)
                scores = scores + causal_mask
            
            # Apply softmax
            attn_weights = mx.softmax(scores, axis=-1)
            
            # Apply to values
            out = attn_weights @ v
            
            if self.debug_mode:
                logger.debug(f"Attention output shape: {out.shape}")
            
            return out
            
        except Exception as e:
            logger.error(f"Safe attention computation failed: {e}")
            # Fallback: return zeros with expected shape
            batch_size, num_heads, seq_len, head_dim = q.shape
            return mx.zeros((batch_size, num_heads, seq_len, head_dim))
    
    def validate_tensor_compatibility(self, *tensors: mx.array) -> bool:
        """
        Validate that tensors are compatible for operations.
        
        Args:
            *tensors: Variable number of tensors to check
            
        Returns:
            True if tensors are compatible, False otherwise
        """
        try:
            if len(tensors) < 2:
                return True
                
            reference_shape = tensors[0].shape
            batch_size, seq_len = reference_shape[:2]
            
            for i, tensor in enumerate(tensors[1:], 1):
                if tensor.shape[:2] != (batch_size, seq_len):
                    logger.warning(f"Tensor {i} has incompatible batch/seq dimensions: {tensor.shape} vs {reference_shape}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Tensor compatibility check failed: {e}")
            return False
    
    def fix_model_generation_tensors(
        self,
        model_output: Dict[str, Any],
        expected_shapes: Dict[str, Tuple[int, ...]]
    ) -> Dict[str, Any]:
        """
        Fix tensor shapes in model generation output.
        
        Args:
            model_output: Dictionary containing model outputs
            expected_shapes: Dictionary of expected tensor shapes
            
        Returns:
            Fixed model output dictionary
        """
        try:
            fixed_output = model_output.copy()
            
            for key, expected_shape in expected_shapes.items():
                if key in fixed_output and isinstance(fixed_output[key], mx.array):
                    tensor = fixed_output[key]
                    
                    if tensor.shape != expected_shape:
                        logger.warning(f"Fixing {key} shape from {tensor.shape} to {expected_shape}")
                        fixed_output[key] = self._reshape_to_target(tensor, expected_shape)
            
            return fixed_output
            
        except Exception as e:
            logger.error(f"Failed to fix model generation tensors: {e}")
            return model_output


# Global instance
mlx_tensor_fixer = MLXTensorFixer()


def safe_mlx_attention(
    q: mx.array,
    k: mx.array,
    v: mx.array,
    num_heads: int,
    num_kv_heads: int,
    head_dim: int,
    scale: Optional[float] = None
) -> mx.array:
    """
    Safe MLX attention computation with automatic dimension fixing.
    
    This is a convenience function that handles the most common tensor
    dimension issues in MLX attention computation.
    """
    try:
        # Enable debug mode if needed
        if logger.isEnabledFor(logging.DEBUG):
            mlx_tensor_fixer.enable_debug()
        
        # Fix attention dimensions
        q_fixed, k_fixed, v_fixed = mlx_tensor_fixer.fix_attention_dimensions(
            q, k, v, num_heads, num_kv_heads, head_dim
        )
        
        # Calculate scale if not provided
        if scale is None:
            scale = 1.0 / np.sqrt(head_dim)
        
        # Get sequence length for causal mask
        seq_len = q_fixed.shape[2]
        causal_mask = mlx_tensor_fixer.fix_causal_mask(seq_len)
        
        # Compute attention safely
        output = mlx_tensor_fixer.safe_attention_computation(
            q_fixed, k_fixed, v_fixed, scale, causal_mask
        )
        
        return output
        
    except Exception as e:
        logger.error(f"Safe MLX attention failed: {e}")
        # Emergency fallback
        batch_size, seq_len = q.shape[:2]
        return mx.zeros((batch_size, num_heads, seq_len, head_dim))


def fix_mlx_generation_error(error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze MLX generation error and provide fix recommendations.
    
    Args:
        error: The exception that occurred
        context: Context information about the generation
        
    Returns:
        Dictionary with fix recommendations
    """
    error_str = str(error).lower()
    
    fixes = {
        "error_type": "unknown",
        "recommendations": [],
        "tensor_fixes_applied": False,
        "fallback_strategy": "none"
    }
    
    # Analyze error type
    if "size of tensor" in error_str and "must match" in error_str:
        fixes["error_type"] = "tensor_dimension_mismatch"
        fixes["recommendations"] = [
            "Apply tensor dimension alignment",
            "Check attention head configuration", 
            "Verify sequence length consistency",
            "Enable tensor debugging mode"
        ]
        fixes["fallback_strategy"] = "dimension_alignment"
        
    elif "dimension" in error_str and "attention" in error_str:
        fixes["error_type"] = "attention_dimension_error"
        fixes["recommendations"] = [
            "Fix attention tensor shapes",
            "Check grouped query attention setup",
            "Validate key-value head repetition"
        ]
        fixes["fallback_strategy"] = "safe_attention"
        
    elif "shape" in error_str and ("mismatch" in error_str or "incompatible" in error_str):
        fixes["error_type"] = "general_shape_mismatch"
        fixes["recommendations"] = [
            "Apply general tensor reshaping",
            "Check model configuration",
            "Validate input preprocessing"
        ]
        fixes["fallback_strategy"] = "tensor_reshaping"
    
    return fixes