"""
Production Model Service for LeenVibe
Supports multiple deployment modes:
1. Direct MLX integration (when mlx-lm available)
2. HTTP client to existing MLX-LM server
3. Fallback to mock mode for development
"""
import asyncio
import logging
import time
import json
import os
import httpx
from typing import Optional, Dict, Any, List, Union
from pathlib import Path
from dataclasses import dataclass

import mlx.core as mx
import mlx.nn as nn

# Try to import MLX-LM for direct integration
try:
    from mlx_lm import load, generate
    MLX_LM_AVAILABLE = True
except ImportError:
    MLX_LM_AVAILABLE = False
    load = None
    generate = None

logger = logging.getLogger(__name__)

@dataclass
class ModelConfig:
    """Configuration for model deployment"""
    model_name: str = "Qwen/Qwen3-30B-A3B-MLX-4bit"
    deployment_mode: str = "auto"  # auto, direct, server, mock
    server_url: str = "http://127.0.0.1:8082"
    max_tokens: int = 512
    temperature: float = 0.7
    cache_dir: str = "~/.cache/leenvibe"
    
    @classmethod
    def from_env(cls) -> "ModelConfig":
        """Create config from environment variables"""
        import os
        return cls(
            model_name=os.getenv("LEENVIBE_MODEL_NAME", cls.model_name),
            deployment_mode=os.getenv("LEENVIBE_DEPLOYMENT_MODE", cls.deployment_mode),
            server_url=os.getenv("LEENVIBE_MLX_SERVER_URL", cls.server_url),
            max_tokens=int(os.getenv("LEENVIBE_MAX_TOKENS", str(cls.max_tokens))),
            temperature=float(os.getenv("LEENVIBE_TEMPERATURE", str(cls.temperature))),
            cache_dir=os.getenv("LEENVIBE_CACHE_DIR", cls.cache_dir),
        )

class ProductionModelService:
    """Production-ready model service with multiple deployment modes"""
    
    def __init__(self, config: Optional[ModelConfig] = None):
        self.config = config or ModelConfig()
        self.model = None
        self.tokenizer = None
        self.is_initialized = False
        self.deployment_mode = None
        self.http_client = None
        
        # Expand cache directory
        self.cache_dir = Path(self.config.cache_dir).expanduser()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.health_status = {
            "status": "not_initialized",
            "deployment_mode": None,
            "model_loaded": False,
            "memory_usage_mb": 0,
            "last_inference_time": None,
            "total_inferences": 0,
            "model_name": self.config.model_name,
            "mlx_lm_available": MLX_LM_AVAILABLE
        }
    
    async def initialize(self) -> bool:
        """Initialize the model service with best available mode"""
        try:
            logger.info(f"Initializing Production Model Service: {self.config.model_name}")
            
            # Determine deployment mode
            mode = await self._determine_deployment_mode()
            self.deployment_mode = mode
            self.health_status["deployment_mode"] = mode
            
            logger.info(f"Using deployment mode: {mode}")
            
            if mode == "direct":
                return await self._initialize_direct_mode()
            elif mode == "server":
                return await self._initialize_server_mode()
            elif mode == "mock":
                return await self._initialize_mock_mode()
            else:
                logger.error(f"Unknown deployment mode: {mode}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize model service: {e}")
            self.health_status["status"] = "error"
            return False
    
    async def _determine_deployment_mode(self) -> str:
        """Determine the best deployment mode based on availability"""
        
        if self.config.deployment_mode != "auto":
            return self.config.deployment_mode
        
        # Check if MLX-LM server is running
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.config.server_url}/health")
                if response.status_code == 200:
                    logger.info("Detected running MLX-LM server")
                    return "server"
        except:
            pass
        
        # Check if MLX-LM is available for direct integration
        if MLX_LM_AVAILABLE:
            logger.info("MLX-LM available for direct integration")
            return "direct"
        
        # Fallback to mock mode
        logger.warning("No MLX-LM available, using mock mode")
        return "mock"
    
    async def _initialize_direct_mode(self) -> bool:
        """Initialize direct MLX-LM integration"""
        try:
            logger.info("Loading model directly with MLX-LM...")
            
            # Load model in thread to avoid blocking
            self.model, self.tokenizer = await asyncio.to_thread(
                load, self.config.model_name, model_cache_path=str(self.cache_dir)
            )
            
            self.health_status["status"] = "ready_direct"
            self.health_status["model_loaded"] = True
            self.is_initialized = True
            
            logger.info("Direct MLX-LM model loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model directly: {e}")
            self.health_status["status"] = "direct_error"
            return False
    
    async def _initialize_server_mode(self) -> bool:
        """Initialize HTTP client to MLX-LM server"""
        try:
            self.http_client = httpx.AsyncClient(timeout=30.0)
            
            # Test connection
            response = await self.http_client.get(f"{self.config.server_url}/health")
            if response.status_code != 200:
                raise Exception(f"Server health check failed: {response.status_code}")
            
            self.health_status["status"] = "ready_server"
            self.health_status["model_loaded"] = True
            self.is_initialized = True
            
            logger.info(f"Connected to MLX-LM server at {self.config.server_url}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MLX-LM server: {e}")
            self.health_status["status"] = "server_error"
            return False
    
    async def _initialize_mock_mode(self) -> bool:
        """Initialize mock mode for development"""
        await asyncio.sleep(1)  # Simulate loading time
        
        self.health_status["status"] = "ready_mock"
        self.health_status["model_loaded"] = True
        self.is_initialized = True
        
        logger.info("Mock mode initialized")
        return True
    
    async def generate_text(self, prompt: str, max_tokens: Optional[int] = None, temperature: Optional[float] = None) -> str:
        """Generate text using the configured deployment mode"""
        if not self.is_initialized:
            raise RuntimeError("Model service not initialized")
        
        if max_tokens is None:
            max_tokens = self.config.max_tokens
        if temperature is None:
            temperature = self.config.temperature
        
        start_time = time.time()
        
        try:
            if self.deployment_mode == "direct":
                response = await self._generate_direct(prompt, max_tokens, temperature)
            elif self.deployment_mode == "server":
                response = await self._generate_server(prompt, max_tokens, temperature)
            elif self.deployment_mode == "mock":
                response = await self._generate_mock(prompt, max_tokens, temperature)
            else:
                raise RuntimeError(f"Unknown deployment mode: {self.deployment_mode}")
            
            # Update metrics
            inference_time = time.time() - start_time
            self.health_status["last_inference_time"] = inference_time
            self.health_status["total_inferences"] += 1
            
            try:
                self.health_status["memory_usage_mb"] = mx.get_active_memory() / 1024 / 1024
            except:
                pass
            
            logger.info(f"Generation completed in {inference_time:.2f}s using {self.deployment_mode} mode")
            return response
            
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise
    
    async def _generate_direct(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Generate using direct MLX-LM integration"""
        try:
            # Format as chat message
            messages = [
                {"role": "system", "content": "You are Qwen, a helpful coding assistant created by Alibaba Cloud."},
                {"role": "user", "content": prompt}
            ]
            
            # Generate response in thread to avoid blocking
            response = await asyncio.to_thread(
                generate,
                self.model,
                self.tokenizer,
                prompt=messages,
                max_tokens=max_tokens,
                temp=temperature
            )
            
            return f"""**Qwen3-30B Response** (Direct MLX-LM)

**Prompt:** {prompt}

**Response:** {response}

---
*Model: {self.config.model_name}*
*Mode: Direct MLX-LM Integration*
*Inference time: {self.health_status['last_inference_time']:.2f}s*
*Memory: {self.health_status['memory_usage_mb']:.2f}MB*
"""
            
        except Exception as e:
            logger.error(f"Direct generation failed: {e}")
            raise
    
    async def _generate_server(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Generate using HTTP client to MLX-LM server"""
        try:
            payload = {
                "model": self.config.model_name,
                "messages": [
                    {"role": "system", "content": "You are Qwen, a helpful coding assistant created by Alibaba Cloud."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": False
            }
            
            response = await self.http_client.post(
                f"{self.config.server_url}/v1/chat/completions",
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            return f"""**Qwen3-30B Response** (MLX-LM Server)

**Prompt:** {prompt}

**Response:** {content}

---
*Model: {self.config.model_name}*
*Mode: MLX-LM Server ({self.config.server_url})*
*Inference time: {self.health_status['last_inference_time']:.2f}s*
"""
            
        except Exception as e:
            logger.error(f"Server generation failed: {e}")
            raise
    
    async def _generate_mock(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Generate mock response for development"""
        await asyncio.sleep(0.5)  # Simulate processing time
        
        # Enhanced mock responses based on prompt
        if "function" in prompt.lower() or "def " in prompt:
            mock_response = f"""def hello_world():
    \"\"\"A simple hello world function\"\"\"
    return "Hello, World!"

# Usage example:
result = hello_world()
print(result)"""
        elif "class" in prompt.lower():
            mock_response = f"""class Calculator:
    \"\"\"A simple calculator class\"\"\"
    
    def add(self, a, b):
        return a + b
    
    def subtract(self, a, b):
        return a - b"""
        else:
            mock_response = f"""This is a mock response for development purposes.

Your prompt was: "{prompt}"

In production, this would be handled by Qwen3-30B model.
Current mode: {self.deployment_mode}
Mock generation successful!"""
        
        return f"""**Mock Response** (Development Mode)

**Prompt:** {prompt}

**Response:** {mock_response}

---
*Model: Mock (Development)*
*Mode: {self.deployment_mode}*
*Inference time: {inference_time:.2f}s*
*Note: This is a mock response. Enable MLX-LM for real model inference.*
"""
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status"""
        status = self.health_status.copy()
        status["is_initialized"] = self.is_initialized
        status["config"] = {
            "model_name": self.config.model_name,
            "deployment_mode": self.config.deployment_mode,
            "server_url": self.config.server_url,
            "cache_dir": str(self.cache_dir)
        }
        
        return status
    
    async def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up Production Model Service...")
        
        if self.http_client:
            await self.http_client.aclose()
            self.http_client = None
        
        self.model = None
        self.tokenizer = None
        self.is_initialized = False
        self.health_status["status"] = "shutdown"
        self.health_status["model_loaded"] = False
        
        logger.info("Production Model Service cleanup completed")