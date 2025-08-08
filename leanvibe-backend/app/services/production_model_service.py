"""
Production Model Service for LeanVibe
Supports multiple deployment modes:
1. Direct MLX integration (when mlx-lm available)
2. HTTP client to existing MLX-LM server
3. Fallback to mock mode for development
"""

import asyncio
import logging
import os
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
import mlx.core as mx

# Import unified configuration
try:
    from ..config import UnifiedConfig, ModelConfig, DeploymentMode as ConfigDeploymentMode, get_config
except ImportError:
    # Fallback for direct execution
    from app.config import UnifiedConfig, ModelConfig, DeploymentMode as ConfigDeploymentMode, get_config

# Import LLM metrics models
try:
    from ..models.llm_metrics_models import (
        DeploymentMode,
        GenerationMetrics,
        LLMHealthStatus,
        ModelInformation,
        ModelStatus,
        SessionMetrics,
        TokenUsage,
    )
except ImportError:
    from app.models.llm_metrics_models import (
        DeploymentMode,
        GenerationMetrics,
        LLMHealthStatus,
        ModelInformation,
        ModelStatus,
        SessionMetrics,
        TokenUsage,
    )

# Try to import MLX-LM for direct integration
try:
    from mlx_lm import generate, load

    MLX_LM_AVAILABLE = True
except ImportError:
    MLX_LM_AVAILABLE = False
    load = None
    generate = None

logger = logging.getLogger(__name__)


# ModelConfig now imported from unified configuration system


class ProductionModelService:
    """Production-ready model service with multiple deployment modes"""

    def __init__(self, config: Optional[ModelConfig] = None):
        if config is None:
            # Use unified configuration system
            unified_config = get_config()
            self.config = unified_config.model
        else:
            self.config = config
            
        self.model = None
        self.tokenizer = None
        self.is_initialized = False
        self.deployment_mode = None
        self.http_client = None
        self.start_time = datetime.now()

        # Get cache directory from unified config
        unified_config = get_config()
        self.cache_dir = unified_config.directories.cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize LLM metrics
        self.model_info = ModelInformation(
            model_name=self.config.model_name,
            deployment_mode=DeploymentMode.MOCK,  # Will be updated during initialization
            status=ModelStatus.NOT_INITIALIZED,
            default_temperature=self.config.temperature,
            default_max_tokens=self.config.max_tokens,
            mlx_available=True,  # MLX core is available
            mlx_lm_available=MLX_LM_AVAILABLE,
        )
        
        # Current session metrics (tracks metrics for the lifetime of this service)
        self.current_session = SessionMetrics(
            session_id=f"prod_model_{int(time.time())}",
            start_time=self.start_time,
        )
        
        # LLM health status
        self.llm_health_status = LLMHealthStatus(
            model_info=self.model_info,
            current_session=self.current_session,
            is_ready=False,
        )

        # Legacy health status for backward compatibility
        self.health_status = {
            "status": "not_initialized",
            "deployment_mode": None,
            "model_loaded": False,
            "memory_usage_mb": 0,
            "last_inference_time": None,
            "total_inferences": 0,
            "model_name": self.config.model_name,
            "mlx_lm_available": MLX_LM_AVAILABLE,
        }

    async def initialize(self) -> bool:
        """Initialize the model service with best available mode and enhanced logging"""
        init_start_time = time.time()
        
        try:
            logger.info(
                f"Production Model Service initialization started | "
                f"model={self.config.model_name} | "
                f"config_mode={self.config.deployment_mode} | "
                f"mlx_lm_available={MLX_LM_AVAILABLE}"
            )

            # Update model status to initializing
            self.model_info.status = ModelStatus.INITIALIZING
            self.llm_health_status.model_info.status = ModelStatus.INITIALIZING

            # Determine deployment mode
            mode = await self._determine_deployment_mode()
            self.deployment_mode = mode
            self.health_status["deployment_mode"] = mode
            
            # Update LLM metrics with deployment mode
            if mode == "direct":
                self.model_info.deployment_mode = DeploymentMode.DIRECT
            elif mode == "server":
                self.model_info.deployment_mode = DeploymentMode.SERVER
            elif mode == "mock":
                self.model_info.deployment_mode = DeploymentMode.MOCK
            
            self.llm_health_status.model_info.deployment_mode = self.model_info.deployment_mode

            logger.info(f"Using deployment mode: {mode}")

            success = False
            if mode == "direct":
                success = await self._initialize_direct_mode()
            elif mode == "server":
                success = await self._initialize_server_mode()
            elif mode == "mock":
                success = await self._initialize_mock_mode()
            else:
                logger.error(f"Unknown deployment mode: {mode}")
                return False

            if success:
                self.model_info.status = ModelStatus.READY
                self.llm_health_status.model_info.status = ModelStatus.READY
                self.llm_health_status.is_ready = True
                self.is_initialized = True
                
                # Update model capabilities based on the specific model
                if "Phi-3" in self.config.model_name:
                    self.model_info.context_length = 131072  # 128k context
                    self.model_info.parameter_count = "3.8B"
                    self.model_info.estimated_memory_gb = 8.0
                elif "Qwen" in self.config.model_name:
                    self.model_info.context_length = 32768
                    self.model_info.parameter_count = "30B"
                    self.model_info.estimated_memory_gb = 20.0
                
                self.model_info.last_health_check = datetime.now()
                self.model_info.health_status = "healthy"
                
                # Update uptime
                self.llm_health_status.uptime_seconds = (datetime.now() - self.start_time).total_seconds()
                
                logger.info(f"Model service initialized successfully with {mode} mode")
                return True
            else:
                self.model_info.status = ModelStatus.ERROR
                self.llm_health_status.model_info.status = ModelStatus.ERROR
                self.llm_health_status.is_ready = False
                return False

        except Exception as e:
            logger.error(f"Failed to initialize model service: {e}")
            self.health_status["status"] = "error"
            self.model_info.status = ModelStatus.ERROR
            self.llm_health_status.model_info.status = ModelStatus.ERROR
            self.llm_health_status.is_ready = False
            return False

    async def _determine_deployment_mode(self) -> str:
        """Determine the best deployment mode based on availability with enhanced logging"""
        logger.info("Starting deployment mode determination...")

        if self.config.deployment_mode != "auto":
            logger.info(
                f"Using configured deployment mode: {self.config.deployment_mode} "
                f"(auto-detection disabled)"
            )
            return self.config.deployment_mode
        
        logger.debug("Auto-detection enabled, checking available options...")

        # Enhanced server availability checking with detailed logging
        logger.debug(f"Checking MLX-LM server availability at {self.config.server_url}...")
        server_check_start = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.config.server_url}/health")
                server_check_time = time.time() - server_check_start
                
                if response.status_code == 200:
                    logger.info(
                        f"MLX-LM server detected and healthy | "
                        f"url={self.config.server_url} | "
                        f"response_time={server_check_time:.3f}s | "
                        f"status={response.status_code}"
                    )
                    return "server"
                else:
                    logger.warning(
                        f"MLX-LM server responded with non-200 status | "
                        f"status={response.status_code} | "
                        f"response_time={server_check_time:.3f}s"
                    )
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            server_check_time = time.time() - server_check_start
            logger.debug(
                f"MLX server connection failed | "
                f"url={self.config.server_url} | "
                f"timeout_after={server_check_time:.3f}s | "
                f"error: {e}"
            )
        except httpx.HTTPStatusError as e:
            server_check_time = time.time() - server_check_start
            logger.warning(
                f"MLX server HTTP error | "
                f"status={e.response.status_code} | "
                f"response_time={server_check_time:.3f}s"
            )
        except Exception as e:
            server_check_time = time.time() - server_check_start
            logger.error(
                f"Unexpected server check error | "
                f"time={server_check_time:.3f}s | "
                f"error: {e}"
            )

        # Enhanced direct MLX availability checking
        logger.debug("Checking direct MLX-LM integration availability...")
        if MLX_LM_AVAILABLE:
            try:
                # Test MLX core functionality
                test_memory = mx.array([1.0, 2.0, 3.0])
                memory_test_success = True
                logger.debug("MLX core memory test passed")
            except Exception as e:
                memory_test_success = False
                logger.warning(f"MLX core test failed: {e}")
            
            if memory_test_success:
                logger.info(
                    f"Direct MLX-LM integration available | "
                    f"mlx_lm_version=available | "
                    f"mlx_core_functional=True"
                )
                return "direct"
            else:
                logger.warning(
                    "MLX-LM available but MLX core test failed, considering fallback"
                )
        else:
            logger.debug(
                "MLX-LM not available for direct integration | "
                f"import_available={MLX_LM_AVAILABLE}"
            )

        # Enhanced fallback decision with reasoning
        logger.warning(
            "Falling back to mock mode | "
            f"server_available=False | "
            f"direct_mlx_available={MLX_LM_AVAILABLE} | "
            f"reason=no_viable_inference_backend"
        )
        return "mock"

    async def _initialize_direct_mode(self) -> bool:
        """Initialize direct MLX-LM integration"""
        try:
            logger.info("Loading model directly with MLX-LM...")

            # Load model in thread to avoid blocking
            # Note: model_cache_path parameter removed - MLX-LM handles caching automatically
            self.model, self.tokenizer = await asyncio.to_thread(
                load, self.config.model_name
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

    async def generate_text(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """Generate text using the configured deployment mode with enhanced logging"""
        if not self.is_initialized:
            raise RuntimeError("Model service not initialized")

        if max_tokens is None:
            max_tokens = self.config.max_tokens
        if temperature is None:
            temperature = self.config.temperature

        # Create a unique request ID for correlation tracking
        request_id = f"req_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        start_time = time.time()

        # Enhanced logging: Request initiation
        logger.info(
            f"[{request_id}] LLM request initiated | "
            f"mode={self.deployment_mode} | "
            f"prompt_length={len(prompt)} | "
            f"max_tokens={max_tokens} | "
            f"temperature={temperature}"
        )
        logger.debug(f"[{request_id}] Prompt preview: {prompt[:100]}...")

        try:
            # Estimate input tokens with enhanced logging
            estimated_input_tokens = max(1, len(prompt) // 4)
            logger.debug(
                f"[{request_id}] Token estimation | "
                f"input_chars={len(prompt)} | "
                f"estimated_input_tokens={estimated_input_tokens}"
            )
            
            # Enhanced logging: Strategy selection pathway
            logger.debug(
                f"[{request_id}] Strategy execution | "
                f"selected_mode={self.deployment_mode} | "
                f"model={self.config.model_name}"
            )
            
            # Execute generation with strategy-specific logging
            if self.deployment_mode == "direct":
                logger.debug(f"[{request_id}] Executing direct MLX-LM inference")
                response = await self._generate_direct(prompt, max_tokens, temperature, request_id)
            elif self.deployment_mode == "server":
                logger.debug(f"[{request_id}] Executing server-based inference to {self.config.server_url}")
                response = await self._generate_server(prompt, max_tokens, temperature, request_id)
            elif self.deployment_mode == "mock":
                logger.debug(f"[{request_id}] Executing mock inference for development")
                response = await self._generate_mock(prompt, max_tokens, temperature, request_id)
            else:
                error_msg = f"Unknown deployment mode: {self.deployment_mode}"
                logger.error(f"[{request_id}] Strategy selection failed: {error_msg}")
                raise RuntimeError(error_msg)

            # Enhanced performance metrics calculation and logging
            generation_time = time.time() - start_time
            estimated_output_tokens = max(1, len(response) // 4)
            tokens_per_second = estimated_output_tokens / generation_time if generation_time > 0 else 0
            
            # Enhanced memory usage tracking with detailed logging
            current_memory_mb = 0.0
            memory_delta = 0.0
            try:
                current_memory_mb = mx.get_active_memory() / 1024 / 1024
                # Calculate memory impact if we have previous measurements
                if hasattr(self, '_last_memory_mb'):
                    memory_delta = current_memory_mb - self._last_memory_mb
                self._last_memory_mb = current_memory_mb
                
                logger.debug(
                    f"[{request_id}] Memory analysis | "
                    f"current={current_memory_mb:.1f}MB | "
                    f"delta={memory_delta:+.1f}MB"
                )
            except AttributeError as e:
                logger.debug(f"[{request_id}] MLX memory API not available: {e}")
            except Exception as e:
                logger.warning(f"[{request_id}] Memory tracking failed: {e}")
            
            # Enhanced performance logging
            logger.info(
                f"[{request_id}] Generation completed | "
                f"time={generation_time:.3f}s | "
                f"speed={tokens_per_second:.1f} tok/s | "
                f"tokens={estimated_input_tokens}→{estimated_output_tokens} | "
                f"memory={current_memory_mb:.1f}MB | "
                f"response_length={len(response)}"
            )

            # Create token usage metrics
            token_usage = TokenUsage(
                input_tokens=estimated_input_tokens,
                output_tokens=estimated_output_tokens
            )
            token_usage.update_total()

            # Create generation metrics
            generation_metrics = GenerationMetrics(
                request_id=request_id,
                token_usage=token_usage,
                generation_time_seconds=generation_time,
                tokens_per_second=tokens_per_second,
                memory_usage_mb=current_memory_mb,
                prompt_length=len(prompt),
                response_length=len(response),
                temperature=temperature,
                max_tokens=max_tokens,
            )

            # Update LLM health status with new metrics
            self.llm_health_status.add_generation_metrics(generation_metrics)
            self.llm_health_status.current_memory_mb = current_memory_mb
            self.llm_health_status.uptime_seconds = (datetime.now() - self.start_time).total_seconds()

            # Update session metrics
            self.current_session.update_from_generation(generation_metrics, success=True)
            self.llm_health_status.current_session = self.current_session

            # Update legacy health status for backward compatibility
            self.health_status["last_inference_time"] = generation_time
            self.health_status["total_inferences"] += 1
            self.health_status["memory_usage_mb"] = current_memory_mb

            # Enhanced completion logging with quality metrics
            context_utilization = min(100, (estimated_input_tokens / self.config.max_tokens) * 100)
            efficiency_score = min(100, (tokens_per_second / 50) * 100)  # Assume 50 tok/s as baseline
            
            logger.info(
                f"[{request_id}] Request SUCCESS | "
                f"mode={self.deployment_mode} | "
                f"context_utilization={context_utilization:.1f}% | "
                f"efficiency_score={efficiency_score:.1f}%"
            )
            
            logger.debug(
                f"[{request_id}] Response preview: {response[:150]}..."
            )
            
            return response

        except Exception as e:
            # Enhanced error tracking and recovery guidance
            generation_time = time.time() - start_time
            error_type = type(e).__name__
            error_context = {
                "deployment_mode": self.deployment_mode,
                "model_name": self.config.model_name,
                "prompt_length": len(prompt),
                "generation_time": generation_time,
                "estimated_input_tokens": estimated_input_tokens,
            }
            
            # Categorize error and provide recovery guidance
            recovery_suggestions = self._categorize_error_and_suggest_recovery(e, error_context)
            
            logger.error(
                f"[{request_id}] Request FAILED | "
                f"error_type={error_type} | "
                f"time={generation_time:.3f}s | "
                f"mode={self.deployment_mode} | "
                f"error: {str(e)}"
            )
            
            logger.warning(
                f"[{request_id}] Recovery suggestions: {'; '.join(recovery_suggestions)}"
            )
            
            # Track failed generation with enhanced metrics
            failed_metrics = GenerationMetrics(
                request_id=request_id,
                generation_time_seconds=generation_time,
                prompt_length=len(prompt),
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Update session with failed request
            self.current_session.update_from_generation(failed_metrics, success=False)
            self.llm_health_status.current_session = self.current_session
            
            raise

    def _categorize_error_and_suggest_recovery(
        self, error: Exception, context: Dict[str, Any]
    ) -> List[str]:
        """Categorize errors and provide specific recovery suggestions"""
        suggestions = []
        error_type = type(error).__name__
        error_msg = str(error).lower()
        
        if "memory" in error_msg or "out of memory" in error_msg:
            suggestions.extend([
                "Reduce max_tokens parameter",
                "Clear MLX memory cache",
                "Switch to server mode if available",
                "Consider model quantization"
            ])
        elif "timeout" in error_msg or "connection" in error_msg:
            suggestions.extend([
                "Check server connectivity",
                "Increase request timeout",
                "Fallback to direct mode",
                "Verify model server status"
            ])
        elif "model" in error_msg or "load" in error_msg:
            suggestions.extend([
                "Verify model path and availability",
                "Check disk space for model cache",
                "Try re-downloading model",
                "Fallback to mock mode for testing"
            ])
        elif "token" in error_msg or "length" in error_msg:
            suggestions.extend([
                "Reduce prompt length",
                "Implement prompt truncation",
                "Use sliding window approach",
                "Consider context compression"
            ])
        else:
            suggestions.extend([
                "Check logs for detailed error info",
                "Verify configuration settings",
                "Try different deployment mode",
                "Contact support with request ID"
            ])
        
        return suggestions

    async def _generate_direct(
        self, prompt: str, max_tokens: int, temperature: float, request_id: str
    ) -> str:
        """Generate using direct MLX-LM integration with enhanced logging"""
        try:
            logger.debug(f"[{request_id}] Direct MLX setup | model_loaded={self.model is not None}")
            
            # Format as chat message
            messages = [
                {
                    "role": "system",
                    "content": "You are Qwen, a helpful coding assistant created by Alibaba Cloud.",
                },
                {"role": "user", "content": prompt},
            ]
            
            logger.debug(
                f"[{request_id}] Direct inference | "
                f"chat_messages={len(messages)} | "
                f"system_prompt_length={len(messages[0]['content'])}"
            )

            # Generate response in thread to avoid blocking
            inference_start = time.time()
            response = await asyncio.to_thread(
                generate,
                self.model,
                self.tokenizer,
                prompt=messages,
                max_tokens=max_tokens,
                temp=temperature,
            )
            inference_time = time.time() - inference_start
            
            logger.debug(
                f"[{request_id}] Direct inference completed | "
                f"pure_inference_time={inference_time:.3f}s | "
                f"response_length={len(response)}"
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
            logger.error(
                f"[{request_id}] Direct generation FAILED | "
                f"model_state={self.model is not None} | "
                f"tokenizer_state={self.tokenizer is not None} | "
                f"error: {e}"
            )
            raise

    async def _generate_server(
        self, prompt: str, max_tokens: int, temperature: float, request_id: str
    ) -> str:
        """Generate using HTTP client to MLX-LM server with enhanced logging"""
        try:
            payload = {
                "model": self.config.model_name,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are Qwen, a helpful coding assistant created by Alibaba Cloud.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": False,
            }
            
            logger.debug(
                f"[{request_id}] Server request | "
                f"url={self.config.server_url} | "
                f"payload_size={len(str(payload))} bytes"
            )

            request_start = time.time()
            response = await self.http_client.post(
                f"{self.config.server_url}/v1/chat/completions", json=payload
            )
            request_time = time.time() - request_start
            
            response.raise_for_status()
            
            logger.debug(
                f"[{request_id}] Server response | "
                f"status={response.status_code} | "
                f"request_time={request_time:.3f}s | "
                f"response_size={len(response.text)} bytes"
            )

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
            logger.error(
                f"[{request_id}] Server generation FAILED | "
                f"server_url={self.config.server_url} | "
                f"client_state={self.http_client is not None} | "
                f"error: {e}"
            )
            raise

    async def _generate_mock(
        self, prompt: str, max_tokens: int, temperature: float, request_id: str
    ) -> str:
        """Generate mock response for development with enhanced logging"""
        logger.debug(f"[{request_id}] Mock generation | simulating processing...")
        await asyncio.sleep(0.5)  # Simulate processing time
        
        logger.debug(
            f"[{request_id}] Mock analysis | "
            f"prompt_keywords={self._extract_mock_keywords(prompt)} | "
            f"response_strategy=enhanced_contextual"
        )

        # Enhanced mock responses based on prompt
        if "function" in prompt.lower() or "def " in prompt:
            mock_response = """def hello_world():
    \"\"\"A simple hello world function\"\"\"
    return "Hello, World!"

# Usage example:
result = hello_world()
logger.info(result)"""
        elif "class" in prompt.lower():
            mock_response = """class Calculator:
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

        logger.debug(f"[{request_id}] Mock response generated | length={len(mock_response)}")
        
        return f"""**Mock Response** (Development Mode)

**Prompt:** {prompt}

**Response:** {mock_response}

---
*Model: Mock (Development)*
*Mode: {self.deployment_mode}*
*Request ID: {request_id}*
*Note: This is a mock response. Enable MLX-LM for real model inference.*
"""
    
    def _extract_mock_keywords(self, prompt: str) -> List[str]:
        """Extract keywords from prompt for mock response categorization"""
        keywords = []
        prompt_lower = prompt.lower()
        
        if "function" in prompt_lower or "def " in prompt:
            keywords.append("function")
        if "class" in prompt_lower:
            keywords.append("class")
        if "error" in prompt_lower or "debug" in prompt_lower:
            keywords.append("debug")
        if "explain" in prompt_lower:
            keywords.append("explanation")
            
        return keywords

    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status with comprehensive LLM metrics"""
        # Update uptime
        self.llm_health_status.uptime_seconds = (datetime.now() - self.start_time).total_seconds()
        
        # Legacy status for backward compatibility
        status = self.health_status.copy()
        status["is_initialized"] = self.is_initialized
        status["config"] = {
            "model_name": self.config.model_name,
            "deployment_mode": self.config.deployment_mode,
            "server_url": self.config.server_url,
            "cache_dir": str(self.cache_dir),
        }

        # Add comprehensive LLM metrics
        status["llm_metrics"] = {
            "model_info": {
                "name": self.model_info.model_name,
                "version": self.model_info.model_version,
                "deployment_mode": self.model_info.deployment_mode.value,
                "status": self.model_info.status.value,
                "context_length": self.model_info.context_length,
                "parameter_count": self.model_info.parameter_count,
                "estimated_memory_gb": self.model_info.estimated_memory_gb,
                "mlx_available": self.model_info.mlx_available,
                "mlx_lm_available": self.model_info.mlx_lm_available,
                "last_health_check": self.model_info.last_health_check.isoformat() if self.model_info.last_health_check else None,
            },
            "performance": {
                "is_ready": self.llm_health_status.is_ready,
                "uptime_seconds": self.llm_health_status.uptime_seconds,
                "recent_average_speed_tokens_per_sec": self.llm_health_status.get_recent_average_speed(),
                "recent_average_latency_seconds": self.llm_health_status.get_recent_average_latency(),
                "total_recent_requests": len(self.llm_health_status.recent_generations),
                "last_request_time": self.llm_health_status.last_request_time.isoformat() if self.llm_health_status.last_request_time else None,
            },
            "memory": {
                "current_usage_mb": self.llm_health_status.current_memory_mb,
                "available_mb": self.llm_health_status.available_memory_mb,
            },
            "session_metrics": {
                "session_id": self.current_session.session_id,
                "total_requests": self.current_session.total_requests,
                "successful_requests": self.current_session.successful_requests,
                "failed_requests": self.current_session.failed_requests,
                "error_rate": self.current_session.error_rate,
                "total_input_tokens": self.current_session.total_input_tokens,
                "total_output_tokens": self.current_session.total_output_tokens,
                "total_tokens": self.current_session.total_tokens,
                "average_generation_time": self.current_session.average_generation_time,
                "average_tokens_per_second": self.current_session.average_tokens_per_second,
                "min_generation_time": self.current_session.min_generation_time,
                "max_generation_time": self.current_session.max_generation_time,
                "average_memory_usage_mb": self.current_session.average_memory_usage_mb,
                "peak_memory_usage_mb": self.current_session.peak_memory_usage_mb,
                "session_start_time": self.current_session.start_time.isoformat(),
            },
            "recent_generations": [
                {
                    "request_id": gen.request_id,
                    "timestamp": gen.timestamp.isoformat(),
                    "input_tokens": gen.token_usage.input_tokens,
                    "output_tokens": gen.token_usage.output_tokens,
                    "total_tokens": gen.token_usage.total_tokens,
                    "generation_time_seconds": gen.generation_time_seconds,
                    "tokens_per_second": gen.tokens_per_second,
                    "memory_usage_mb": gen.memory_usage_mb,
                    "prompt_length": gen.prompt_length,
                    "response_length": gen.response_length,
                }
                for gen in self.llm_health_status.recent_generations[-5:]  # Last 5 generations
            ]
        }

        return status
    
    def get_llm_metrics_snapshot(self) -> Dict[str, Any]:
        """Get a formatted snapshot of LLM metrics for API responses"""
        from ..models.llm_metrics_models import LLMMetricsSnapshot
        
        snapshot = LLMMetricsSnapshot(health_status=self.llm_health_status)
        return snapshot.to_dict()

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
