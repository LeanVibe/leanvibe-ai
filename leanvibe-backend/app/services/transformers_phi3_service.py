"""
Transformers-based Phi-3-Mini Service for LeanVibe
Direct Hugging Face transformers integration for real model weights
"""

import asyncio
import logging
import time
from typing import Any, Dict, Optional

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# Import compatibility utilities
try:
    from .transformers_compatibility import (
        get_safe_generation_kwargs,
        handle_generation_error,
        get_model_loading_kwargs,
        log_compatibility_info,
        patch_dynamic_cache_globally
    )
    COMPATIBILITY_AVAILABLE = True
except ImportError:
    # Fallback for direct execution
    from transformers_compatibility import (
        get_safe_generation_kwargs,
        handle_generation_error,
        get_model_loading_kwargs,
        log_compatibility_info,
        patch_dynamic_cache_globally
    )
    COMPATIBILITY_AVAILABLE = True

# Apply compatibility patches
patch_dynamic_cache_globally()

logger = logging.getLogger(__name__)


class TransformersPhi3Service:
    """Production-ready Phi-3-Mini service using Hugging Face transformers"""
    
    def __init__(self, model_name: str = "microsoft/Phi-3-mini-4k-instruct"):
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self.device = "mps" if torch.backends.mps.is_available() else "cpu"
        self.is_initialized = False
        self.load_time = None
        self.total_generations = 0
        self.total_tokens_generated = 0
        
    async def initialize(self) -> bool:
        """Initialize the model and tokenizer"""
        try:
            logger.info(f"🚀 Initializing Phi-3-Mini service with {self.model_name}")
            
            # Log compatibility information
            log_compatibility_info()
            
            start_time = time.time()
            
            # Load tokenizer
            logger.info("📚 Loading tokenizer...")
            await asyncio.to_thread(self._load_tokenizer)
            
            # Load model  
            logger.info("🧠 Loading model...")
            await asyncio.to_thread(self._load_model)
            
            self.load_time = time.time() - start_time
            self.is_initialized = True
            
            logger.info(f"✅ Phi-3-Mini service initialized in {self.load_time:.2f}s")
            logger.info(f"📊 Model parameters: ~{sum(p.numel() for p in self.model.parameters()) / 1e6:.1f}M")
            logger.info(f"🖥️  Device: {self.device}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Phi-3-Mini service: {e}")
            self.is_initialized = False
            return False
    
    def _load_tokenizer(self):
        """Load tokenizer synchronously"""
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name, 
            trust_remote_code=True
        )
        
    def _load_model(self):
        """Load model synchronously with compatibility handling"""
        torch_dtype = torch.float16 if self.device != "cpu" else torch.float32
        
        # Get compatible model loading kwargs
        model_kwargs = get_model_loading_kwargs(
            model_name=self.model_name,
            device="auto",
            torch_dtype=torch_dtype
        )
        
        # Force eager attention to avoid tensor dimension issues
        model_kwargs["attn_implementation"] = "eager"
        
        try:
            logger.info(f"Loading model {self.model_name} with compatibility settings...")
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                **model_kwargs
            )
            
            # Log model info if available
            if hasattr(self.model, 'config'):
                if hasattr(self.model.config, 'num_parameters'):
                    logger.info(f"Model loaded successfully with {self.model.config.num_parameters} parameters")
                else:
                    logger.info("Model loaded successfully")
            else:
                logger.info("Model loaded successfully")
                
        except Exception as e:
            logger.error(f"Error loading model with compatibility settings: {e}")
            # Fallback to minimal loading
            logger.info("Retrying model loading with minimal configuration...")
            try:
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    torch_dtype=torch_dtype,
                    trust_remote_code=True,
                    device_map="auto",
                    attn_implementation="eager"  # Force eager attention
                )
                logger.info("Model loaded successfully with minimal configuration")
            except Exception as fallback_error:
                logger.error(f"Failed to load model even with minimal configuration: {fallback_error}")
                raise fallback_error
        
    async def generate_text(
        self, 
        prompt: str, 
        max_new_tokens: int = 100,
        temperature: float = 0.7,
        do_sample: bool = True
    ) -> Dict[str, Any]:
        """Generate text using the Phi-3 model"""
        if not self.is_initialized:
            return {
                "status": "error",
                "error": "Service not initialized. Call initialize() first.",
                "using_pretrained": False
            }
            
        try:
            start_time = time.time()
            
            # Tokenize input with proper attention mask and padding
            inputs = self.tokenizer(
                prompt, 
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512,  # Reasonable max length to prevent issues
                add_special_tokens=True
            )
            
            # Ensure attention mask is present
            if "attention_mask" not in inputs:
                inputs["attention_mask"] = torch.ones_like(inputs["input_ids"])
            
            if self.device != "cpu":
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Get safe generation parameters using compatibility layer
            generation_kwargs = get_safe_generation_kwargs(
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                do_sample=do_sample,
                pad_token_id=self.tokenizer.eos_token_id,
                use_cache=False  # Disable cache to avoid dimension issues
            )
            
            with torch.no_grad():
                try:
                    outputs = await asyncio.to_thread(
                        self.model.generate,
                        inputs["input_ids"],
                        attention_mask=inputs["attention_mask"],
                        **generation_kwargs
                    )
                except Exception as e:
                    logger.warning(f"Generation failed with error: {e}")
                    
                    # Handle the error using compatibility layer
                    modified_kwargs = handle_generation_error(e, generation_kwargs)
                    
                    if modified_kwargs != generation_kwargs:
                        logger.info("Retrying generation with modified parameters...")
                        try:
                            outputs = await asyncio.to_thread(
                                self.model.generate,
                                inputs["input_ids"],
                                attention_mask=inputs["attention_mask"],
                                **modified_kwargs
                            )
                            logger.info("Generation succeeded with fallback parameters")
                        except Exception as fallback_error:
                            logger.error(f"Generation failed even with fallback: {fallback_error}")
                            raise fallback_error
                    else:
                        raise e
            
            # Decode response
            full_response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            generated_text = full_response[len(prompt):].strip()
            
            generation_time = time.time() - start_time
            num_tokens = len(self.tokenizer.encode(generated_text))
            
            # Update stats
            self.total_generations += 1
            self.total_tokens_generated += num_tokens
            
            return {
                "status": "success",
                "response": generated_text,
                "full_response": full_response,
                "using_pretrained": True,
                "model_name": self.model_name,
                "generation_time": generation_time,
                "tokens_generated": num_tokens,
                "tokens_per_second": num_tokens / generation_time if generation_time > 0 else 0,
                "device": self.device,
                "prompt_length": len(prompt)
            }
            
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            return {
                "status": "error",
                "error": str(e),
                "using_pretrained": True
            }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get service health and stats"""
        return {
            "service": "transformers_phi3",
            "model_name": self.model_name,
            "is_initialized": self.is_initialized,
            "device": self.device,
            "load_time": self.load_time,
            "total_generations": self.total_generations,
            "total_tokens_generated": self.total_tokens_generated,
            "using_pretrained_weights": True,
            "model_loaded": self.model is not None,
            "tokenizer_loaded": self.tokenizer is not None,
            "model_parameters": sum(p.numel() for p in self.model.parameters()) / 1e6 if self.model else 0
        }
    
    async def shutdown(self):
        """Clean shutdown of the service"""
        try:
            # Clear model and tokenizer from memory
            if self.model:
                del self.model
                self.model = None
                
            if self.tokenizer:
                del self.tokenizer
                self.tokenizer = None
                
            # Clear GPU cache if using CUDA
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                
            self.is_initialized = False
            logger.info("✅ Transformers Phi-3 service shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


# Create a singleton instance
transformers_phi3_service = TransformersPhi3Service()