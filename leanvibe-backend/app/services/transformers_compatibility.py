"""
Transformers Compatibility Utilities
Handles version-specific issues and compatibility patches for different transformers versions.
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Version compatibility flags
TRANSFORMERS_VERSION = None
CACHE_API_AVAILABLE = False
DYNAMIC_CACHE_PATCHED = False

try:
    import transformers
    TRANSFORMERS_VERSION = transformers.__version__
    
    # Check for cache API availability
    try:
        from transformers import DynamicCache
        from transformers.generation.utils import GenerationConfig
        CACHE_API_AVAILABLE = True
    except ImportError:
        CACHE_API_AVAILABLE = False
        
    logger.info(f"Transformers version: {TRANSFORMERS_VERSION}, Cache API: {CACHE_API_AVAILABLE}")
    
except ImportError:
    logger.warning("Transformers not available")


def patch_dynamic_cache_globally():
    """
    Global patch for DynamicCache compatibility issues.
    This should be called once at application startup.
    """
    global DYNAMIC_CACHE_PATCHED
    
    if DYNAMIC_CACHE_PATCHED:
        return True
    
    if not CACHE_API_AVAILABLE:
        logger.warning("Cache API not available, skipping patch")
        return False
    
    try:
        from transformers import DynamicCache
        
        # Check if get_max_length method exists
        if not hasattr(DynamicCache, 'get_max_length'):
            logger.info("Patching DynamicCache with missing get_max_length method")
            
            def get_max_length(self):
                """
                Compatibility implementation of get_max_length for DynamicCache.
                Returns the maximum sequence length from the cached key-value pairs.
                """
                try:
                    if hasattr(self, 'key_cache') and self.key_cache:
                        # Get max sequence length from key cache
                        max_len = 0
                        for key_tensor in self.key_cache:
                            if key_tensor is not None and key_tensor.numel() > 0:
                                # Key cache shape: [batch_size, num_heads, seq_len, head_dim]
                                seq_len = key_tensor.shape[-2]
                                max_len = max(max_len, seq_len)
                        return max_len
                    
                    # Fallback to a reasonable default
                    return getattr(self, '_max_length', 2048)
                    
                except Exception as e:
                    logger.warning(f"Error in get_max_length implementation: {e}")
                    return 2048  # Safe fallback
            
            # Add the method to DynamicCache
            DynamicCache.get_max_length = get_max_length
            DYNAMIC_CACHE_PATCHED = True
            logger.info("Successfully patched DynamicCache.get_max_length")
            return True
            
        else:
            logger.info("DynamicCache.get_max_length already exists")
            DYNAMIC_CACHE_PATCHED = True
            return True
            
    except Exception as e:
        logger.error(f"Failed to patch DynamicCache: {e}")
        return False


def get_safe_generation_kwargs(
    max_new_tokens: int = 100,
    temperature: float = 0.7,
    do_sample: bool = True,
    pad_token_id: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Get generation kwargs that are safe for the current transformers version.
    Handles compatibility issues with different versions of transformers.
    """
    base_kwargs = {
        "max_new_tokens": max_new_tokens,
        "do_sample": do_sample,
        "temperature": temperature,
        "return_dict_in_generate": False,  # Simplify output
    }
    
    if pad_token_id is not None:
        base_kwargs["pad_token_id"] = pad_token_id
    
    # Add cache handling based on version
    if CACHE_API_AVAILABLE:
        try:
            # Enable cache but let transformers handle the details
            base_kwargs["use_cache"] = True
            base_kwargs["past_key_values"] = None  # Let transformers create cache
        except Exception as e:
            logger.warning(f"Cache configuration failed: {e}")
            base_kwargs["use_cache"] = False
    else:
        # Disable cache if API not available
        base_kwargs["use_cache"] = False
    
    # Add any additional kwargs
    base_kwargs.update(kwargs)
    
    return base_kwargs


def handle_generation_error(error: Exception, generation_kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle generation errors by providing fallback configurations.
    Returns modified generation kwargs that should work.
    """
    error_str = str(error)
    modified_kwargs = generation_kwargs.copy()
    
    if "get_max_length" in error_str or "DynamicCache" in error_str:
        logger.warning("Detected DynamicCache compatibility issue, disabling cache")
        modified_kwargs["use_cache"] = False
        modified_kwargs.pop("past_key_values", None)
        
    elif "attention" in error_str.lower():
        logger.warning("Detected attention compatibility issue, using eager implementation")
        modified_kwargs["attn_implementation"] = "eager"
        
    elif "memory" in error_str.lower():
        logger.warning("Detected memory issue, reducing batch size and enabling cache")
        modified_kwargs["use_cache"] = True
        modified_kwargs["max_new_tokens"] = min(modified_kwargs.get("max_new_tokens", 100), 50)
        
    return modified_kwargs


def get_model_loading_kwargs(
    model_name: str,
    device: str = "auto",
    torch_dtype=None,
    **kwargs
) -> Dict[str, Any]:
    """
    Get model loading kwargs that are compatible with current transformers version.
    """
    base_kwargs = {
        "trust_remote_code": True,
        "device_map": device,
    }
    
    if torch_dtype is not None:
        base_kwargs["torch_dtype"] = torch_dtype
    
    # Add version-specific configurations
    if TRANSFORMERS_VERSION and TRANSFORMERS_VERSION.startswith("4.53"):
        # Specific fixes for 4.53.0
        base_kwargs.update({
            "use_cache": True,
            "attn_implementation": "eager",  # More stable than flash attention
        })
    
    # Add any additional kwargs
    base_kwargs.update(kwargs)
    
    return base_kwargs


def log_compatibility_info():
    """Log current compatibility status"""
    logger.info(f"Transformers Compatibility Status:")
    logger.info(f"  - Version: {TRANSFORMERS_VERSION}")
    logger.info(f"  - Cache API Available: {CACHE_API_AVAILABLE}")
    logger.info(f"  - DynamicCache Patched: {DYNAMIC_CACHE_PATCHED}")


# Auto-patch on import
if __name__ != "__main__":
    patch_dynamic_cache_globally()