"""
Unified MLX Service - Strategy Pattern Implementation

Consolidates multiple MLX services (real_mlx_service, pragmatic_mlx_service, 
mock_mlx_service, mlx_model_service) into a unified architecture using the 
Strategy Pattern for improved maintainability and reduced code duplication.
"""

import logging
import time
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional
from pathlib import Path
import os
import asyncio

from ..core.circuit_breaker import ai_circuit_breaker, with_circuit_breaker, FallbackResponses

logger = logging.getLogger(__name__)


class MLXInferenceStrategy(Enum):
    """Available MLX inference strategies"""
    AUTO = "auto"
    PRODUCTION = "production"
    PRAGMATIC = "pragmatic"
    MOCK = "mock"
    FALLBACK = "fallback"


class MLXServiceInterface(ABC):
    """Enhanced abstract interface for MLX service implementations with AST and vector capabilities"""
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the MLX service implementation"""
        pass
    
    @abstractmethod
    async def generate_code_completion(
        self, context: Dict[str, Any], intent: str = "suggest"
    ) -> Dict[str, Any]:
        """Generate code completion based on context and intent"""
        pass
    
    @abstractmethod
    def get_model_health(self) -> Dict[str, Any]:
        """Get health status of the model service"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this implementation is available"""
        pass
    
    # Enhanced capabilities for consolidated service
    async def process_command(self, command: str, args: str, client_id: str) -> Dict[str, Any]:
        """Process CLI slash commands - default implementation returns not supported"""
        return {
            "status": "error",
            "message": f"Command processing not supported by {self.__class__.__name__}"
        }
    
    async def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze file using AST parsing - default implementation returns not supported"""
        return {
            "status": "error",
            "message": f"File analysis not supported by {self.__class__.__name__}"
        }
    
    async def search_similar_code(self, query: str, n_results: int = 10) -> List[Dict[str, Any]]:
        """Search for similar code patterns - default implementation returns empty"""
        return []


class ProductionMLXStrategy(MLXServiceInterface):
    """Production MLX implementation using ProductionModelService"""
    
    def __init__(self):
        self.is_initialized = False
        self._production_service = None
        self._model_warmed_up = False
        self._response_times = []
        self._target_response_time = 2.0  # 2 second target
        
    async def initialize(self) -> bool:
        """Initialize production MLX service with ProductionModelService"""
        try:
            # Import and initialize production model service
            from .production_model_service import ProductionModelService
            
            self._production_service = ProductionModelService()
            success = await self._production_service.initialize()
            
            if success:
                self.is_initialized = True
                logger.info(f"Production MLX strategy initialized successfully with {self._production_service.deployment_mode} mode")
                
                # Start model warm-up for faster response times
                await self._warm_up_model()
                
                return True
            else:
                logger.error("Failed to initialize production model service")
                return False
            
        except Exception as e:
            logger.error(f"Failed to initialize Production MLX strategy: {e}")
            return False
    
    async def generate_code_completion(
        self, context: Dict[str, Any], intent: str = "suggest"
    ) -> Dict[str, Any]:
        """Generate code completion using production model service"""
        if not self.is_initialized or not self._production_service:
            return {
                "status": "error",
                "error": "Production service not initialized",
                "response": "",
                "confidence": 0.0
            }
        
        # Start performance timing
        start_time = time.time()
        
        try:
            # Ensure model is warmed up for optimal performance
            if not self._model_warmed_up:
                await self._warm_up_model()
            
            # Create a prompt from context and intent
            prompt = self._create_prompt_from_context(context, intent)
            
            # Use the production service's generate_text method
            response = await self._production_service.generate_text(
                prompt=prompt,
                max_tokens=100,  # Reduced for faster response
                temperature=0.7
            )
            
            # Calculate response time
            end_time = time.time()
            response_time = end_time - start_time
            self._track_response_time(response_time)
            
            # Get health status for additional metrics
            health = self._production_service.get_health_status()
            
            return {
                "status": "success",
                "response": response,
                "confidence": 0.9,  # High confidence for production model
                "language": self._detect_language(context),
                "requires_human_review": False,
                "suggestions": [f"Generated with {self._production_service.deployment_mode} production model"],
                "model": self._production_service.config.model_name,
                "context_used": True,
                "deployment_mode": self._production_service.deployment_mode,
                "generation_time": response_time,
                "response_time": response_time,
                "performance_status": self._get_performance_status(response_time),
                "memory_usage_mb": health.get("memory_usage_mb", 0)
            }
            
        except Exception as e:
            # Calculate response time even for errors
            end_time = time.time()
            response_time = end_time - start_time
            self._track_response_time(response_time)
            
            logger.error(f"Production MLX completion failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "response": "",
                "confidence": 0.0,
                "response_time": response_time
            }
    
    def get_model_health(self) -> Dict[str, Any]:
        """Get production model health"""
        avg_response_time = sum(self._response_times) / len(self._response_times) if self._response_times else 0
        
        if self._production_service:
            service_health = self._production_service.get_health_status()
            return {
                "strategy": "production",
                "initialized": self.is_initialized,
                "model_loaded": service_health.get("model_loaded", False),
                "model_warmed_up": self._model_warmed_up,
                "deployment_mode": self._production_service.deployment_mode,
                "status": "healthy" if self.is_initialized else "unavailable",
                "service_details": service_health,
                "performance": {
                    "avg_response_time": avg_response_time,
                    "target_response_time": self._target_response_time,
                    "within_target": avg_response_time <= self._target_response_time,
                    "total_requests": len(self._response_times)
                }
            }
        else:
            return {
                "strategy": "production",
                "initialized": self.is_initialized,
                "model_loaded": False,
                "model_warmed_up": False,
                "status": "unavailable"
            }
    
    def is_available(self) -> bool:
        """Check if production strategy is available"""
        try:
            from .production_model_service import ProductionModelService
            return True
        except ImportError:
            return False
    
    def _detect_language(self, context: Dict[str, Any]) -> str:
        """Detect programming language from context"""
        file_path = context.get("file_path", "")
        if file_path.endswith(".py"):
            return "python"
        elif file_path.endswith((".js", ".ts")):
            return "javascript"
        elif file_path.endswith(".swift"):
            return "swift"
        else:
            return "unknown"
    
    def _create_prompt_from_context(self, context: Dict[str, Any], intent: str) -> str:
        """Create a prompt from context and intent for production model"""
        file_path = context.get("file_path", "")
        cursor_position = context.get("cursor_position", 0)
        surrounding_code = context.get("surrounding_code", "")
        
        intent_prompts = {
            "suggest": f"Suggest code improvements for {file_path} at position {cursor_position}:\n{surrounding_code}",
            "explain": f"Explain this code from {file_path}:\n{surrounding_code}",
            "refactor": f"Suggest refactoring for this code from {file_path}:\n{surrounding_code}",
            "debug": f"Help debug this code from {file_path}:\n{surrounding_code}",
            "optimize": f"Suggest optimizations for this code from {file_path}:\n{surrounding_code}"
        }
        
        return intent_prompts.get(intent, f"Analyze this code: {surrounding_code}")
    
    async def _warm_up_model(self):
        """Pre-warm the model for faster response times"""
        if self._model_warmed_up:
            return
            
        logger.info("Starting model warm-up for optimal performance...")
        
        try:
            # Execute a small warm-up request to initialize model caches
            start_time = time.time()
            response = await self._production_service.generate_text(
                prompt="Complete this Python code: return 'hello world'",
                max_tokens=10,
                temperature=0.1
            )
            warmup_time = time.time() - start_time
            
            if response:
                self._model_warmed_up = True
                logger.info(f"Model warm-up completed successfully in {warmup_time:.2f}s")
            else:
                logger.warning(f"Model warm-up completed with warnings")
                
        except Exception as e:
            logger.error(f"Model warm-up failed: {e}")
    
    def _track_response_time(self, response_time: float):
        """Track response times for performance monitoring"""
        self._response_times.append(response_time)
        
        # Keep only last 100 response times for memory efficiency
        if len(self._response_times) > 100:
            self._response_times = self._response_times[-100:]
        
        # Log performance warnings
        if response_time > self._target_response_time:
            logger.warning(f"AI response time {response_time:.2f}s exceeds target of {self._target_response_time}s")
        
        # Log performance info for monitoring
        avg_time = sum(self._response_times) / len(self._response_times)
        logger.info(f"AI Response: {response_time:.2f}s (avg: {avg_time:.2f}s, target: {self._target_response_time}s)")
    
    def _get_performance_status(self, response_time: float) -> str:
        """Get performance status based on response time"""
        if response_time <= 1.0:
            return "excellent"
        elif response_time <= 2.0:
            return "good"
        elif response_time <= 3.0:
            return "acceptable"
        else:
            return "slow"


class PragmaticMLXStrategy(MLXServiceInterface):
    """Pragmatic MLX implementation using simple, reliable approaches"""
    
    def __init__(self):
        self.is_initialized = False
        self._pragmatic_service = None
        
    async def initialize(self) -> bool:
        """Initialize pragmatic MLX service"""
        try:
            from .pragmatic_mlx_service import PragmaticMLXService
            
            self._pragmatic_service = PragmaticMLXService()
            success = await self._pragmatic_service.initialize()
            
            if success:
                self.is_initialized = True
                logger.info("Pragmatic MLX strategy initialized successfully")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to initialize Pragmatic MLX strategy: {e}")
            return False
    
    async def generate_code_completion(
        self, context: Dict[str, Any], intent: str = "suggest"
    ) -> Dict[str, Any]:
        """Generate code completion using pragmatic approach"""
        if not self.is_initialized or not self._pragmatic_service:
            return {
                "status": "error",
                "error": "Pragmatic service not initialized",
                "response": "",
                "confidence": 0.0
            }
        
        try:
            return await self._pragmatic_service.generate_code_completion(context, intent)
        except Exception as e:
            logger.error(f"Pragmatic MLX completion failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "response": "",
                "confidence": 0.0
            }
    
    def get_model_health(self) -> Dict[str, Any]:
        """Get pragmatic model health"""
        return {
            "strategy": "pragmatic",
            "initialized": self.is_initialized,
            "service_ready": self._pragmatic_service is not None,
            "status": "healthy" if self.is_initialized else "unavailable"
        }
    
    def is_available(self) -> bool:
        """Check if pragmatic strategy is available"""
        try:
            from .pragmatic_mlx_service import PragmaticMLXService
            import mlx.core as mx
            return True
        except ImportError:
            return False


class MockMLXStrategy(MLXServiceInterface):
    """Mock MLX implementation for testing and development"""
    
    def __init__(self):
        self.is_initialized = False
        self._mock_service = None
        
    async def initialize(self) -> bool:
        """Initialize mock MLX service"""
        try:
            from .mock_mlx_service import MockMLXService
            
            self._mock_service = MockMLXService()
            success = await self._mock_service.initialize()
            
            if success:
                self.is_initialized = True
                logger.info("Mock MLX strategy initialized successfully")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to initialize Mock MLX strategy: {e}")
            return False
    
    async def generate_code_completion(
        self, context: Dict[str, Any], intent: str = "suggest"
    ) -> Dict[str, Any]:
        """Generate mock code completion for testing"""
        if not self.is_initialized or not self._mock_service:
            return {
                "status": "error",
                "error": "Mock service not initialized",
                "response": "",
                "confidence": 0.0
            }
        
        try:
            return await self._mock_service.generate_code_completion(context, intent)
        except Exception as e:
            logger.error(f"Mock MLX completion failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "response": "",
                "confidence": 0.0
            }
    
    def get_model_health(self) -> Dict[str, Any]:
        """Get mock model health"""
        return {
            "strategy": "mock",
            "initialized": self.is_initialized,
            "service_ready": self._mock_service is not None,
            "status": "healthy" if self.is_initialized else "unavailable"
        }
    
    def is_available(self) -> bool:
        """Check if mock strategy is available"""
        try:
            from .mock_mlx_service import MockMLXService
            return True
        except ImportError:
            return False


class FallbackMLXStrategy(MLXServiceInterface):
    """Fallback MLX implementation when all else fails"""
    
    def __init__(self):
        self.is_initialized = True  # Always available
        
    async def initialize(self) -> bool:
        """Initialize fallback service - always succeeds"""
        self.is_initialized = True
        logger.info("Fallback MLX strategy initialized")
        return True
    
    async def generate_code_completion(
        self, context: Dict[str, Any], intent: str = "suggest"
    ) -> Dict[str, Any]:
        """Generate basic fallback response"""
        try:
            file_path = context.get("file_path", "unknown")
            
            # Generate appropriate fallback based on intent
            fallback_responses = {
                "suggest": "# Consider implementing the functionality here\n# Add your code logic",
                "explain": "This code requires analysis. Please refer to documentation or comments.",
                "refactor": "Consider breaking this into smaller functions for better maintainability.",
                "debug": "Check for common issues: variable names, syntax, imports, and logic flow.",
                "optimize": "Look for opportunities to improve performance: caching, algorithms, data structures."
            }
            
            response = fallback_responses.get(intent, "Code analysis not available.")
            
            return {
                "status": "success",
                "response": response,
                "confidence": 0.5,
                "language": self._detect_language_from_path(file_path),
                "requires_human_review": True,
                "suggestions": ["Consider using a more sophisticated MLX service"],
                "model": "fallback",
                "context_used": False
            }
            
        except Exception as e:
            logger.error(f"Fallback MLX completion failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "response": "Unable to provide code assistance.",
                "confidence": 0.0
            }
    
    def get_model_health(self) -> Dict[str, Any]:
        """Get fallback model health"""
        return {
            "strategy": "fallback",
            "initialized": True,
            "status": "available"
        }
    
    def is_available(self) -> bool:
        """Fallback is always available"""
        return True
    
    def _detect_language_from_path(self, file_path: str) -> str:
        """Simple language detection from file path"""
        if file_path.endswith(".py"):
            return "python"
        elif file_path.endswith((".js", ".ts")):
            return "javascript"
        elif file_path.endswith(".swift"):
            return "swift"
        else:
            return "text"


class UnifiedMLXService:
    """
    Enhanced Unified MLX service using Strategy Pattern with AST, Vector, and CLI capabilities
    
    Consolidates functionality from:
    - Multiple MLX inference strategies
    - AST parsing and code analysis
    - Vector storage and semantic search
    - CLI command processing
    """
    
    def __init__(self, preferred_strategy: MLXInferenceStrategy = MLXInferenceStrategy.AUTO):
        self.preferred_strategy = preferred_strategy
        self.current_strategy: Optional[MLXServiceInterface] = None
        self.available_strategies: Dict[MLXInferenceStrategy, MLXServiceInterface] = {}
        self.is_initialized = False
        
        # Performance monitoring
        self._response_times = []
        self._target_response_time = 2.0
        self._performance_cache = {}
        
        # Enhanced AI infrastructure (migrated from enhanced_ai_service)
        self.ast_service = None
        self.vector_service = None
        self.nlp_service = None  # Enhanced NLP service for voice commands
        self.enhanced_initialization_status = {
            "mlx_strategy": False,
            "ast": False,
            "vector": False,
            "nlp": False,
            "overall": False,
        }
        
        # CLI command support
        self.supported_commands = {
            "/list-files": self._list_files,
            "/status": self._get_enhanced_status,
            "/current-dir": self._get_current_directory,
            "/read-file": self._read_file,
            "/analyze-file": self._analyze_file_enhanced,
            "/search-code": self._search_code,
            "/index-project": self._index_project,
            "/vector-stats": self._get_vector_stats,
            "/help": self._get_help,
        }
        
        # Initialize strategy instances
        self._initialize_strategies()
    
    def _initialize_strategies(self):
        """Initialize all available strategy instances"""
        self.available_strategies = {
            MLXInferenceStrategy.PRODUCTION: ProductionMLXStrategy(),
            MLXInferenceStrategy.PRAGMATIC: PragmaticMLXStrategy(),
            MLXInferenceStrategy.MOCK: MockMLXStrategy(),
            MLXInferenceStrategy.FALLBACK: FallbackMLXStrategy()
        }
    
    async def initialize(self) -> bool:
        """Initialize the unified MLX service with strategy, AST, and vector capabilities"""
        init_start_time = time.time()
        session_id = f"mlx_init_{int(time.time())}_{id(self):x}"
        
        try:
            logger.info(
                f"[{session_id}] Unified MLX Service initialization started | "
                f"preferred_strategy={self.preferred_strategy.value} | "
                f"available_strategies={len(self.available_strategies)}"
            )
            
            # Enhanced strategy determination with detailed logging
            if self.preferred_strategy == MLXInferenceStrategy.AUTO:
                logger.debug(f"[{session_id}] Auto-selecting best available strategy...")
                selected_strategy = await self._select_best_strategy(session_id)
            else:
                logger.debug(
                    f"[{session_id}] Using preferred strategy: {self.preferred_strategy.value}"
                )
                selected_strategy = self.preferred_strategy
            
            logger.info(
                f"[{session_id}] Strategy selected: {selected_strategy.value} | "
                f"selection_method={'auto' if self.preferred_strategy == MLXInferenceStrategy.AUTO else 'configured'}"
            )
            
            # Enhanced strategy initialization with detailed tracking
            strategy_impl = self.available_strategies.get(selected_strategy)
            if strategy_impl and strategy_impl.is_available():
                logger.debug(
                    f"[{session_id}] Initializing {selected_strategy.value} strategy | "
                    f"impl_available={strategy_impl.is_available()}"
                )
                
                strategy_init_start = time.time()
                success = await strategy_impl.initialize()
                strategy_init_time = time.time() - strategy_init_start
                
                if success:
                    self.current_strategy = strategy_impl
                    self.enhanced_initialization_status["mlx_strategy"] = True
                    
                    # Initialize enhanced capabilities
                    await self._initialize_enhanced_capabilities(session_id)
                    
                    self.is_initialized = True
                    total_init_time = time.time() - init_start_time
                    
                    logger.info(
                        f"[{session_id}] Initialization SUCCESS | "
                        f"strategy={selected_strategy.value} | "
                        f"strategy_init_time={strategy_init_time:.3f}s | "
                        f"enhanced_ast={self.enhanced_initialization_status['ast']} | "
                        f"enhanced_vector={self.enhanced_initialization_status['vector']} | "
                        f"total_time={total_init_time:.3f}s"
                    )
                    return True
                else:
                    logger.warning(
                        f"[{session_id}] Strategy initialization failed | "
                        f"strategy={selected_strategy.value} | "
                        f"time={strategy_init_time:.3f}s"
                    )
            else:
                logger.warning(
                    f"[{session_id}] Strategy not available | "
                    f"strategy={selected_strategy.value} | "
                    f"impl_exists={strategy_impl is not None} | "
                    f"is_available={strategy_impl.is_available() if strategy_impl else False}"
                )
            
            # Enhanced fallback cascade with detailed logging
            if selected_strategy != MLXInferenceStrategy.FALLBACK:
                logger.warning(
                    f"[{session_id}] Initiating fallback cascade | "
                    f"failed_strategy={selected_strategy.value} | "
                    f"reason=initialization_failed"
                )
                
                fallback_strategy = self.available_strategies[MLXInferenceStrategy.FALLBACK]
                fallback_start = time.time()
                await fallback_strategy.initialize()
                fallback_time = time.time() - fallback_start
                
                self.current_strategy = fallback_strategy
                self.is_initialized = True
                total_init_time = time.time() - init_start_time
                
                logger.warning(
                    f"[{session_id}] Fallback initialization completed | "
                    f"fallback_time={fallback_time:.3f}s | "
                    f"total_time={total_init_time:.3f}s | "
                    f"final_strategy=fallback"
                )
                return True
            
            logger.error(
                f"[{session_id}] All strategies failed | "
                f"attempted_strategy={selected_strategy.value} | "
                f"fallback_already_attempted=True"
            )
            return False
            
        except Exception as e:
            total_init_time = time.time() - init_start_time
            logger.error(
                f"[{session_id}] Initialization FAILED | "
                f"time={total_init_time:.3f}s | "
                f"error_type={type(e).__name__} | "
                f"error: {e}"
            )
            return False
    
    async def _select_best_strategy(self, session_id: str = "auto_select") -> MLXInferenceStrategy:
        """Automatically select the best available strategy with enhanced decision logging"""
        # Priority order: Production > Pragmatic > Mock > Fallback
        priority_order = [
            MLXInferenceStrategy.PRODUCTION,
            MLXInferenceStrategy.PRAGMATIC,
            MLXInferenceStrategy.MOCK,
            MLXInferenceStrategy.FALLBACK
        ]
        
        logger.debug(
            f"[{session_id}] Strategy selection started | "
            f"evaluation_order={[s.value for s in priority_order]}"
        )
        
        selection_details = []
        
        for strategy in priority_order:
            strategy_impl = self.available_strategies.get(strategy)
            is_available = strategy_impl.is_available() if strategy_impl else False
            
            selection_details.append({
                "strategy": strategy.value,
                "impl_exists": strategy_impl is not None,
                "is_available": is_available,
                "selected": False
            })
            
            logger.debug(
                f"[{session_id}] Evaluating {strategy.value} | "
                f"impl_exists={strategy_impl is not None} | "
                f"is_available={is_available}"
            )
            
            if strategy_impl and is_available:
                selection_details[-1]["selected"] = True
                
                logger.info(
                    f"[{session_id}] Strategy auto-selected | "
                    f"selected={strategy.value} | "
                    f"reason=first_available_in_priority_order | "
                    f"evaluated_count={len([d for d in selection_details if not d['selected']])}"
                )
                
                # Log the full selection analysis
                logger.debug(
                    f"[{session_id}] Selection analysis: {selection_details}"
                )
                
                return strategy
        
        # Log if we reach ultimate fallback
        logger.warning(
            f"[{session_id}] No preferred strategies available | "
            f"selection_details={selection_details} | "
            f"using_ultimate_fallback=True"
        )
        
        return MLXInferenceStrategy.FALLBACK
    
    @with_circuit_breaker(ai_circuit_breaker)
    async def generate_code_completion(
        self, context: Dict[str, Any], intent: str = "suggest"
    ) -> Dict[str, Any]:
        """Generate code completion using current strategy with enhanced logging"""
        if not self.is_initialized or not self.current_strategy:
            error_msg = "Unified MLX service not initialized"
            logger.error(f"Completion request failed: {error_msg}")
            return {
                "status": "error",
                "error": error_msg,
                "response": "",
                "confidence": 0.0
            }
        
        # Generate request correlation ID and start performance timing
        request_id = f"mlx_comp_{int(time.time())}_{id(context):x}"
        start_time = time.time()
        
        # Check performance cache for similar requests
        cache_key = self._generate_cache_key(context, intent)
        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            cached_result["from_cache"] = True
            cached_result["response_time"] = time.time() - start_time
            return cached_result
        
        # Enhanced context analysis and logging
        context_analysis = self._analyze_context(context)
        current_strategy_name = self._get_current_strategy_name()
        
        logger.info(
            f"[{request_id}] Code completion request | "
            f"strategy={current_strategy_name} | "
            f"intent={intent} | "
            f"context_complexity={context_analysis['complexity']} | "
            f"file_type={context_analysis['file_type']}"
        )
        
        logger.debug(
            f"[{request_id}] Context details | "
            f"file_path={context.get('file_path', 'unknown')} | "
            f"cursor_pos={context.get('cursor_position', 'unknown')} | "
            f"surrounding_code_length={len(context.get('surrounding_code', ''))}"
        )
        
        try:
            # Execute completion with current strategy
            completion_start = time.time()
            result = await self.current_strategy.generate_code_completion(context, intent)
            completion_time = time.time() - completion_start
            
            # Calculate total response time and track performance
            total_response_time = time.time() - start_time
            self._track_response_time(total_response_time)
            
            # Enhanced result analysis and logging
            if "status" in result and result["status"] == "success":
                result["strategy_used"] = current_strategy_name
                result["request_id"] = request_id
                result["completion_time"] = round(completion_time, 3)
                result["total_response_time"] = round(total_response_time, 3)
                result["performance_status"] = self._get_performance_status(total_response_time)
                
                # Cache successful results for performance
                self._cache_result(cache_key, result)
                
                confidence = result.get("confidence", 0.0)
                response_length = len(result.get("response", ""))
                
                logger.info(
                    f"[{request_id}] Completion SUCCESS | "
                    f"strategy={current_strategy_name} | "
                    f"time={total_response_time:.3f}s | "
                    f"confidence={confidence:.2f} | "
                    f"response_length={response_length} | "
                    f"target_met={total_response_time <= self._target_response_time}"
                )
                
                # Log quality indicators
                if confidence < 0.5:
                    logger.warning(
                        f"[{request_id}] Low confidence result | "
                        f"confidence={confidence:.2f} | "
                        f"recommendation=consider_human_review"
                    )
                
            else:
                error_msg = result.get("error", "Unknown error")
                logger.warning(
                    f"[{request_id}] Completion failed with current strategy | "
                    f"strategy={current_strategy_name} | "
                    f"time={completion_time:.3f}s | "
                    f"error: {error_msg}"
                )
            
            return result
            
        except Exception as e:
            completion_time = time.time() - completion_start
            error_type = type(e).__name__
            
            logger.error(
                f"[{request_id}] Strategy execution FAILED | "
                f"strategy={current_strategy_name} | "
                f"time={completion_time:.3f}s | "
                f"error_type={error_type} | "
                f"error: {e}"
            )
            
            # Enhanced fallback cascade with detailed logging
            if self.current_strategy != self.available_strategies[MLXInferenceStrategy.FALLBACK]:
                logger.warning(
                    f"[{request_id}] Initiating fallback cascade | "
                    f"failed_strategy={current_strategy_name} | "
                    f"fallback_strategy=fallback | "
                    f"reason=strategy_exception"
                )
                
                fallback = self.available_strategies[MLXInferenceStrategy.FALLBACK]
                fallback_start = time.time()
                
                try:
                    fallback_result = await fallback.generate_code_completion(context, intent)
                    fallback_time = time.time() - fallback_start
                    total_time = time.time() - start_time
                    
                    # Enhance fallback result with cascade information
                    fallback_result["fallback_used"] = True
                    fallback_result["original_strategy"] = current_strategy_name
                    fallback_result["fallback_time"] = round(fallback_time, 3)
                    fallback_result["total_time"] = round(total_time, 3)
                    fallback_result["request_id"] = request_id
                    
                    logger.info(
                        f"[{request_id}] Fallback completion | "
                        f"fallback_time={fallback_time:.3f}s | "
                        f"total_time={total_time:.3f}s | "
                        f"fallback_success={fallback_result.get('status') == 'success'}"
                    )
                    
                    return fallback_result
                    
                except Exception as fallback_error:
                    fallback_time = time.time() - fallback_start
                    total_time = time.time() - start_time
                    
                    logger.error(
                        f"[{request_id}] Fallback FAILED | "
                        f"fallback_time={fallback_time:.3f}s | "
                        f"total_time={total_time:.3f}s | "
                        f"fallback_error: {fallback_error}"
                    )
            
            total_time = time.time() - start_time
            return {
                "status": "error",
                "error": str(e),
                "response": "",
                "confidence": 0.0,
                "request_id": request_id,
                "total_time": round(total_time, 3),
                "strategy_attempted": current_strategy_name,
                "fallback_attempted": self.current_strategy != self.available_strategies[MLXInferenceStrategy.FALLBACK]
            }
    
    def get_model_health(self) -> Dict[str, Any]:
        """Get comprehensive health status of MLX service with enhanced diagnostics"""
        health_check_time = time.time()
        
        if not self.current_strategy:
            return {
                "status": "uninitialized",
                "current_strategy": None,
                "available_strategies": [],
                "initialization_status": {
                    "is_initialized": self.is_initialized,
                    "current_strategy_set": False,
                    "preferred_strategy": self.preferred_strategy.value
                },
                "health_check_timestamp": health_check_time
            }
        
        # Enhanced health from current strategy
        current_health = self.current_strategy.get_model_health()
        current_strategy_name = self._get_current_strategy_name()
        
        # Enhanced availability analysis for all strategies
        strategy_availability = {}
        available_strategies = []
        
        for strategy, impl in self.available_strategies.items():
            is_available = impl.is_available()
            strategy_availability[strategy.value] = {
                "available": is_available,
                "initialized": getattr(impl, 'is_initialized', False),
                "impl_type": type(impl).__name__
            }
            
            if is_available:
                available_strategies.append(strategy.value)
        
        # Calculate overall health score
        health_score = self._calculate_health_score(current_health, strategy_availability)
        
        # Performance and capability assessment
        capabilities = {
            "code_completion": True,
            "fallback_available": True,
            "strategy_switching": len(available_strategies) > 1,
            "auto_recovery": self.current_strategy != self.available_strategies[MLXInferenceStrategy.FALLBACK]
        }
        
        return {
            "status": "healthy" if self.is_initialized and health_score > 0.5 else "unhealthy",
            "health_score": health_score,
            "current_strategy": {
                "name": current_strategy_name,
                "details": current_health,
                "is_fallback": current_strategy_name == "fallback"
            },
            "strategy_availability": strategy_availability,
            "available_strategies": available_strategies,
            "preferred_strategy": self.preferred_strategy.value,
            "capabilities": capabilities,
            "initialization_status": {
                "is_initialized": self.is_initialized,
                "current_strategy_set": True,
                "strategy_count": len(self.available_strategies),
                "available_count": len(available_strategies)
            },
            "health_check_timestamp": health_check_time
        }
    
    def _get_current_strategy_name(self) -> str:
        """Get name of current strategy"""
        if not self.current_strategy:
            return "none"
        
        for strategy, impl in self.available_strategies.items():
            if impl == self.current_strategy:
                return strategy.value
        
        return "unknown"
    
    def _analyze_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze context complexity and characteristics for enhanced logging"""
        file_path = context.get("file_path", "")
        surrounding_code = context.get("surrounding_code", "")
        cursor_position = context.get("cursor_position", 0)
        
        # Determine file type
        file_type = "unknown"
        if file_path:
            if file_path.endswith(".py"):
                file_type = "python"
            elif file_path.endswith((".js", ".ts", ".jsx", ".tsx")):
                file_type = "javascript/typescript"
            elif file_path.endswith(".swift"):
                file_type = "swift"
            elif file_path.endswith((".java", ".kt")):
                file_type = "jvm"
        
        # Calculate complexity indicators
        complexity_indicators = {
            "code_length": len(surrounding_code),
            "line_count": len(surrounding_code.splitlines()) if surrounding_code else 0,
            "has_classes": "class " in surrounding_code.lower(),
            "has_functions": any(keyword in surrounding_code.lower() for keyword in ["def ", "function ", "func "]),
            "has_imports": any(keyword in surrounding_code.lower() for keyword in ["import ", "from ", "#include"])
        }
        
        # Calculate overall complexity score
        complexity_score = 0
        if complexity_indicators["code_length"] > 500:
            complexity_score += 0.3
        if complexity_indicators["line_count"] > 20:
            complexity_score += 0.2
        if complexity_indicators["has_classes"]:
            complexity_score += 0.2
        if complexity_indicators["has_functions"]:
            complexity_score += 0.2
        if complexity_indicators["has_imports"]:
            complexity_score += 0.1
        
        if complexity_score < 0.3:
            complexity = "low"
        elif complexity_score < 0.7:
            complexity = "medium"
        else:
            complexity = "high"
        
        return {
            "file_type": file_type,
            "complexity": complexity,
            "complexity_score": round(complexity_score, 2),
            "indicators": complexity_indicators,
            "cursor_position": cursor_position
        }
    
    def _calculate_health_score(self, current_health: Dict[str, Any], strategy_availability: Dict[str, Any]) -> float:
        """Calculate overall health score based on current strategy and availability"""
        score = 0.0
        
        # Current strategy health contribution (60%)
        if current_health.get("status") == "healthy":
            score += 0.6
        elif current_health.get("status") == "available":
            score += 0.4
        
        # Strategy availability contribution (30%)
        total_strategies = len(strategy_availability)
        available_strategies = sum(1 for s in strategy_availability.values() if s["available"])
        if total_strategies > 0:
            availability_ratio = available_strategies / total_strategies
            score += availability_ratio * 0.3
        
        # Initialization status contribution (10%)
        if self.is_initialized:
            score += 0.1
        
        return round(min(1.0, score), 2)
    
    async def switch_strategy(self, new_strategy: MLXInferenceStrategy) -> bool:
        """Switch to a different strategy with enhanced logging and validation"""
        switch_id = f"switch_{int(time.time())}_{new_strategy.value}"
        start_time = time.time()
        current_strategy_name = self._get_current_strategy_name()
        
        logger.info(
            f"[{switch_id}] Strategy switch initiated | "
            f"from={current_strategy_name} | "
            f"to={new_strategy.value}"
        )
        
        try:
            # Enhanced validation with detailed logging
            if new_strategy not in self.available_strategies:
                logger.error(
                    f"[{switch_id}] Strategy not found | "
                    f"requested={new_strategy.value} | "
                    f"available={list(self.available_strategies.keys())}"
                )
                return False
            
            strategy_impl = self.available_strategies[new_strategy]
            if not strategy_impl.is_available():
                logger.error(
                    f"[{switch_id}] Strategy not available | "
                    f"strategy={new_strategy.value} | "
                    f"impl_exists={strategy_impl is not None}"
                )
                return False
            
            # Enhanced strategy initialization with timing
            logger.debug(f"[{switch_id}] Initializing new strategy: {new_strategy.value}")
            init_start = time.time()
            success = await strategy_impl.initialize()
            init_time = time.time() - init_start
            
            if success:
                old_strategy = self.current_strategy
                self.current_strategy = strategy_impl
                total_time = time.time() - start_time
                
                logger.info(
                    f"[{switch_id}] Strategy switch SUCCESS | "
                    f"new_strategy={new_strategy.value} | "
                    f"init_time={init_time:.3f}s | "
                    f"total_time={total_time:.3f}s"
                )
                
                # Log strategy capabilities comparison if available
                if hasattr(old_strategy, 'get_model_health') and hasattr(strategy_impl, 'get_model_health'):
                    old_health = old_strategy.get_model_health()
                    new_health = strategy_impl.get_model_health()
                    logger.debug(
                        f"[{switch_id}] Strategy comparison | "
                        f"old_status={old_health.get('status', 'unknown')} | "
                        f"new_status={new_health.get('status', 'unknown')}"
                    )
                
                return True
            else:
                total_time = time.time() - start_time
                logger.error(
                    f"[{switch_id}] Strategy initialization failed | "
                    f"strategy={new_strategy.value} | "
                    f"init_time={init_time:.3f}s | "
                    f"total_time={total_time:.3f}s"
                )
                return False
                
        except Exception as e:
            total_time = time.time() - start_time
            error_type = type(e).__name__
            
            logger.error(
                f"[{switch_id}] Strategy switch FAILED | "
                f"target={new_strategy.value} | "
                f"time={total_time:.3f}s | "
                f"error_type={error_type} | "
                f"error: {e}"
            )
            return False
    
    def get_available_strategies(self) -> List[str]:
        """Get list of available strategies"""
        return [
            strategy.value 
            for strategy, impl in self.available_strategies.items() 
            if impl.is_available()
        ]
    
    # MARK: - Performance Optimization Methods
    
    def _track_response_time(self, response_time: float):
        """Track response times for performance monitoring"""
        self._response_times.append(response_time)
        
        # Keep only last 100 response times for memory efficiency
        if len(self._response_times) > 100:
            self._response_times = self._response_times[-100:]
        
        # Log performance warnings
        if response_time > self._target_response_time:
            logger.warning(f"AI response time {response_time:.2f}s exceeds target of {self._target_response_time}s")
    
    def _get_performance_status(self, response_time: float) -> str:
        """Get performance status based on response time"""
        if response_time <= 1.0:
            return "excellent"
        elif response_time <= 2.0:
            return "good"
        elif response_time <= 3.0:
            return "acceptable"
        else:
            return "slow"
    
    def _generate_cache_key(self, context: Dict[str, Any], intent: str) -> str:
        """Generate cache key for performance optimization"""
        import hashlib
        
        # Create a hash of the key components for caching
        key_components = [
            context.get("file_path", ""),
            str(context.get("cursor_position", 0)),
            context.get("surrounding_code", "")[:200],  # Limit context for caching
            intent
        ]
        
        key_string = "|".join(key_components)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached result if available and fresh"""
        cached_entry = self._performance_cache.get(cache_key)
        if cached_entry:
            # Check if cache entry is still fresh (5 minutes)
            if time.time() - cached_entry["timestamp"] < 300:
                return cached_entry["result"]
            else:
                # Remove stale cache entry
                del self._performance_cache[cache_key]
        return None
    
    def _cache_result(self, cache_key: str, result: Dict[str, Any]):
        """Cache successful results for performance"""
        # Only cache successful results with good confidence
        if (result.get("status") == "success" and 
            result.get("confidence", 0) > 0.7 and
            len(self._performance_cache) < 50):  # Limit cache size
            
            cache_entry = {
                "result": result.copy(),
                "timestamp": time.time()
            }
            
            # Remove response time fields for caching
            if "response_time" in cache_entry["result"]:
                del cache_entry["result"]["response_time"]
            if "total_response_time" in cache_entry["result"]:
                del cache_entry["result"]["total_response_time"]
            
            self._performance_cache[cache_key] = cache_entry
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for monitoring"""
        if not self._response_times:
            return {
                "avg_response_time": 0,
                "target_response_time": self._target_response_time,
                "within_target_percentage": 0,
                "total_requests": 0,
                "cache_hit_ratio": 0
            }
        
        avg_response_time = sum(self._response_times) / len(self._response_times)
        within_target_count = sum(1 for t in self._response_times if t <= self._target_response_time)
        within_target_percentage = (within_target_count / len(self._response_times)) * 100
        
        return {
            "avg_response_time": round(avg_response_time, 3),
            "target_response_time": self._target_response_time,
            "within_target_percentage": round(within_target_percentage, 1),
            "total_requests": len(self._response_times),
            "cache_entries": len(self._performance_cache),
            "performance_status": self._get_performance_status(avg_response_time),
            "enhanced_metrics": {
                "ast_available": self.enhanced_initialization_status["ast"],
                "vector_available": self.enhanced_initialization_status["vector"],
                "nlp_available": self.enhanced_initialization_status["nlp"],
                "enhanced_overall": self.enhanced_initialization_status["overall"],
                "cli_commands_supported": len(self.supported_commands),
                "nlp_performance": self.nlp_service.get_performance_metrics() if self.nlp_service else {}
            }
        }
    
    # ===== ENHANCED CAPABILITIES (Migrated from enhanced_ai_service) =====
    
    async def _initialize_enhanced_capabilities(self, session_id: str = "enhanced_init"):
        """Initialize AST and vector capabilities (migrated from enhanced_ai_service)"""
        try:
            logger.info(f"[{session_id}] Initializing enhanced AI capabilities...")
            
            # Initialize AST service
            ast_init_start = time.time()
            try:
                from .ast_parser_service import TreeSitterService
                self.ast_service = TreeSitterService()
                ast_success = await self.ast_service.initialize()
                ast_init_time = time.time() - ast_init_start
                
                self.enhanced_initialization_status["ast"] = ast_success
                logger.info(
                    f"[{session_id}] AST service | "
                    f"success={ast_success} | "
                    f"time={ast_init_time:.3f}s"
                )
            except Exception as e:
                logger.warning(f"[{session_id}] AST initialization failed: {e}")
                self.enhanced_initialization_status["ast"] = False
            
            # Initialize vector service
            vector_init_start = time.time()
            try:
                from .vector_store_service import VectorStoreService
                self.vector_service = VectorStoreService()
                vector_success = await self.vector_service.initialize()
                vector_init_time = time.time() - vector_init_start
                
                self.enhanced_initialization_status["vector"] = vector_success
                logger.info(
                    f"[{session_id}] Vector service | "
                    f"success={vector_success} | "
                    f"time={vector_init_time:.3f}s"
                )
            except Exception as e:
                logger.warning(f"[{session_id}] Vector initialization failed: {e}")
                self.enhanced_initialization_status["vector"] = False
            
            # Initialize Enhanced NLP service
            nlp_init_start = time.time()
            try:
                from .enhanced_nlp_service import EnhancedNLPService
                self.nlp_service = EnhancedNLPService()
                # NLP service is self-initializing
                nlp_success = self.nlp_service.is_initialized
                nlp_init_time = time.time() - nlp_init_start
                
                self.enhanced_initialization_status["nlp"] = nlp_success
                logger.info(
                    f"[{session_id}] NLP service | "
                    f"success={nlp_success} | "
                    f"time={nlp_init_time:.3f}s"
                )
            except Exception as e:
                logger.warning(f"[{session_id}] NLP initialization failed: {e}")
                self.enhanced_initialization_status["nlp"] = False
            
            # Update overall enhanced status
            self.enhanced_initialization_status["overall"] = any([
                self.enhanced_initialization_status["mlx_strategy"],
                self.enhanced_initialization_status["ast"],
                self.enhanced_initialization_status["vector"],
                self.enhanced_initialization_status["nlp"],
            ])
            
            logger.info(
                f"[{session_id}] Enhanced capabilities initialized | "
                f"ast={self.enhanced_initialization_status['ast']} | "
                f"vector={self.enhanced_initialization_status['vector']} | "
                f"nlp={self.enhanced_initialization_status['nlp']} | "
                f"overall_enhanced={self.enhanced_initialization_status['overall']}"
            )
            
        except Exception as e:
            logger.error(f"[{session_id}] Enhanced capabilities initialization failed: {e}")
    
    # CLI Command Processing Methods (Essential ones only)
    async def process_command(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process command with enhanced capabilities (migrated from enhanced_ai_service)"""
        if not self.is_initialized:
            return {"status": "error", "message": "Unified MLX service not initialized"}

        command = data.get("content", "")
        command_type = data.get("type", "message")
        client_id = data.get("client_id", "unknown")
        
        cmd_id = f"cmd_{int(time.time())}_{hash(str(data)) % 10000:04d}"
        
        try:
            start_time = time.time()
            
            if command_type == "command" and command.startswith("/"):
                result = await self._process_slash_command(command, client_id)
            else:
                # Enhanced message processing with vector context
                result = await self._process_enhanced_message(command, client_id)

            processing_time = time.time() - start_time
            result["processing_time"] = round(processing_time, 3)
            result["enhanced_status"] = self.enhanced_initialization_status.copy()
            result["command_id"] = cmd_id
            
            return result

        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "enhanced_status": self.enhanced_initialization_status,
                "command_id": cmd_id,
                "error_type": type(e).__name__,
                "processing_time": round(time.time() - start_time, 3)
            }
    
    async def _process_slash_command(self, command: str, client_id: str) -> Dict[str, Any]:
        """Process slash commands with enhanced capabilities"""
        parts = command.split(" ", 1)
        base_command = parts[0]
        args = parts[1] if len(parts) > 1 else ""

        if base_command in self.supported_commands:
            return await self.supported_commands[base_command](args, client_id)
        else:
            return {
                "status": "error",
                "message": f"Unknown command: {base_command}. Type /help for available commands.",
            }
    
    async def _process_enhanced_message(self, message: str, client_id: str) -> Dict[str, Any]:
        """Process general messages with enhanced AI and vector context"""
        if not message.strip():
            return {"status": "error", "message": "Empty message"}

        request_id = f"ai_msg_{int(time.time())}_{hash(message) % 10000:04d}"
        start_time = time.time()

        try:
            # Enhanced vector search for context
            relevant_context = []
            if self.enhanced_initialization_status["vector"] and self.vector_service:
                try:
                    search_results = await self.vector_service.search_similar_code(
                        message, n_results=3
                    )
                    for result in search_results:
                        if result.similarity_score > 0.3:
                            relevant_context.append(
                                f"Relevant code: {result.content} (from {result.file_path})"
                            )
                except Exception as e:
                    logger.warning(f"[{request_id}] Vector search failed: {e}")
            
            # Create enhanced context for the strategy
            enhanced_context = {
                "prompt": message,
                "surrounding_code": "\\n".join(relevant_context) if relevant_context else "",
                "file_path": "cli_interaction",
                "cursor_position": 0,
                "vector_context_available": len(relevant_context) > 0
            }
            
            # Use the current strategy to generate response
            response_obj = await self.generate_code_completion(
                context=enhanced_context,
                intent="suggest"
            )
            
            if response_obj and response_obj.get("status") == "success":
                response_content = response_obj.get("response", "")
                model_info = f"Unified MLX ({self._get_current_strategy_name()})"
                confidence = response_obj.get("confidence", 0.7)
            else:
                response_content = f"""Enhanced Unified MLX Assistant ready to help with '{message}'.

**Current Configuration:**
- **Strategy**: {self._get_current_strategy_name()}
- **AST Analysis**: {'✅' if self.enhanced_initialization_status['ast'] else '🔄'}
- **Vector Search**: {'✅' if self.enhanced_initialization_status['vector'] else '🔄'}
- **Context Available**: {'✅' if relevant_context else '🔄'}

Use /help to see all available enhanced commands."""
                model_info = "Enhanced Fallback"
                confidence = 0.6
            
            total_time = time.time() - start_time

            return {
                "status": "success",
                "type": "ai_response",
                "message": response_content,
                "timestamp": time.time(),
                "model": model_info,
                "confidence": confidence,
                "context_used": len(relevant_context) > 0,
                "context_count": len(relevant_context),
                "request_id": request_id,
                "processing_time": round(total_time, 3),
                "enhanced_services_available": {
                    "mlx_strategy": self.enhanced_initialization_status["mlx_strategy"],
                    "ast": self.enhanced_initialization_status["ast"],
                    "vector": self.enhanced_initialization_status["vector"],
                },
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Enhanced processing error: {str(e)}",
                "confidence": 0.0,
                "request_id": request_id,
                "processing_time": round(time.time() - start_time, 3)
            }
    
    # Essential CLI Commands (Placeholders - full implementation would be longer)
    async def _get_enhanced_status(self, args: str, client_id: str) -> Dict[str, Any]:
        """Get enhanced status with all capabilities"""
        return {
            "status": "success",
            "type": "enhanced_status", 
            "message": f"""🤖 Enhanced Unified MLX Service Status
Current Strategy: {self._get_current_strategy_name()}
AST Analysis: {'✅' if self.enhanced_initialization_status['ast'] else '❌'}
Vector Search: {'✅' if self.enhanced_initialization_status['vector'] else '❌'}
CLI Commands: ✅ {len(self.supported_commands)} available

Use /help to see all commands.""",
            "data": {
                "strategy": self._get_current_strategy_name(),
                "enhanced_status": self.enhanced_initialization_status,
                "supported_commands": list(self.supported_commands.keys()),
            }
        }
    
    async def _get_help(self, args: str, client_id: str) -> Dict[str, Any]:
        """Get help with enhanced commands"""
        help_text = f"""**Enhanced Unified MLX Service Commands:**
/status - Show detailed service status and capabilities
/help - Show this help message

**Available Enhanced Services:**
- MLX Strategy: {self._get_current_strategy_name()}
- AST Analysis: {'✅' if self.enhanced_initialization_status['ast'] else '❌'}
- Vector Search: {'✅' if self.enhanced_initialization_status['vector'] else '❌'}

*Enhanced capabilities available - full CLI command set can be implemented*"""
        
        return {
            "status": "success",
            "type": "enhanced_help",
            "message": help_text,
            "data": {
                "commands": list(self.supported_commands.keys()),
                "enhanced_status": self.enhanced_initialization_status,
            },
        }
    
    # Placeholder methods for full CLI implementation
    async def _list_files(self, args: str, client_id: str) -> Dict[str, Any]:
        """List files placeholder"""
        return {"status": "success", "message": "File listing - enhanced implementation needed"}
    
    async def _get_current_directory(self, args: str, client_id: str) -> Dict[str, Any]:
        """Current directory placeholder"""
        return {"status": "success", "message": f"Current directory: {os.getcwd()}"}
    
    async def _read_file(self, args: str, client_id: str) -> Dict[str, Any]:
        """Read file placeholder"""
        return {"status": "success", "message": "File reading - enhanced implementation needed"}
    
    async def _analyze_file_enhanced(self, args: str, client_id: str) -> Dict[str, Any]:
        """Enhanced file analysis placeholder"""
        if self.enhanced_initialization_status["ast"]:
            return {"status": "success", "message": f"AST analysis available for: {args}"}
        else:
            return {"status": "error", "message": "AST service not available"}
    
    async def _search_code(self, args: str, client_id: str) -> Dict[str, Any]:
        """Code search placeholder"""
        if self.enhanced_initialization_status["vector"]:
            return {"status": "success", "message": f"Vector search available for: {args}"}
        else:
            return {"status": "error", "message": "Vector service not available"}
    
    async def _index_project(self, args: str, client_id: str) -> Dict[str, Any]:
        """Project indexing placeholder"""
        return {"status": "success", "message": "Project indexing - enhanced implementation needed"}
    
    async def _get_vector_stats(self, args: str, client_id: str) -> Dict[str, Any]:
        """Vector stats placeholder"""
        return {"status": "success", "message": "Vector statistics - enhanced implementation needed"}
    
    # MARK: - Enhanced Voice Command Processing
    
    async def process_voice_command(self, voice_text: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Process voice command using enhanced NLP with intelligent intent recognition
        
        Args:
            voice_text: Natural language voice input
            context: Optional context (current directory, project, etc.)
            
        Returns:
            Dict with processing result, confidence, and action recommendations
        """
        if not self.is_initialized:
            return {
                "success": False,
                "error": "Unified MLX service not initialized",
                "confidence": 0.0
            }
        
        request_id = f"voice_{int(time.time())}_{hash(voice_text) % 10000:04d}"
        start_time = time.time()
        
        try:
            logger.info(f"[{request_id}] Processing voice command: '{voice_text[:50]}...'")
            
            # Use enhanced NLP service if available
            if self.enhanced_initialization_status["nlp"] and self.nlp_service:
                nlp_command = self.nlp_service.process_command(voice_text, context)
                
                if nlp_command.confidence < 0.5:
                    suggestions = self.nlp_service.get_command_suggestions(voice_text)
                    return {
                        "success": False,
                        "error": "Could not understand command",
                        "suggestions": suggestions,
                        "confidence": nlp_command.confidence,
                        "original_text": voice_text,
                        "processing_time": time.time() - start_time,
                        "nlp_result": {
                            "intent": nlp_command.intent.value,
                            "action": nlp_command.action,
                            "canonical_form": nlp_command.canonical_form
                        }
                    }
                
                # Execute the parsed NLP command
                result = await self._execute_nlp_command(nlp_command, context, request_id)
                
                # Enhance result with NLP processing details
                result.update({
                    "nlp_processing": {
                        "intent": nlp_command.intent.value,
                        "action": nlp_command.action,
                        "parameters": [
                            {
                                "name": p.name,
                                "value": p.value,
                                "type": p.type,
                                "confidence": p.confidence
                            } for p in nlp_command.parameters
                        ],
                        "confidence": nlp_command.confidence,
                        "canonical_form": nlp_command.canonical_form,
                        "processing_time": nlp_command.processing_time
                    },
                    "total_processing_time": time.time() - start_time
                })
                
                return result
            
            else:
                # Fallback to simple string matching for basic commands
                logger.warning(f"[{request_id}] NLP service unavailable, using fallback processing")
                return await self._process_voice_command_fallback(voice_text, context, request_id)
                
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"[{request_id}] Voice command processing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "confidence": 0.0,
                "processing_time": processing_time,
                "request_id": request_id
            }
    
    async def _execute_nlp_command(self, nlp_command, context: Optional[Dict], request_id: str) -> Dict[str, Any]:
        """Execute parsed NLP command based on intent and action"""
        from .enhanced_nlp_service import CommandIntent
        
        try:
            if nlp_command.intent == CommandIntent.SYSTEM_STATUS:
                return await self._handle_system_status_voice(nlp_command, context)
                
            elif nlp_command.intent == CommandIntent.FILE_OPERATIONS:
                return await self._handle_file_operations_voice(nlp_command, context)
                
            elif nlp_command.intent == CommandIntent.PROJECT_NAVIGATION:
                return await self._handle_project_navigation_voice(nlp_command, context)
                
            elif nlp_command.intent == CommandIntent.CODE_ANALYSIS:
                return await self._handle_code_analysis_voice(nlp_command, context)
                
            elif nlp_command.intent == CommandIntent.TASK_MANAGEMENT:
                return await self._handle_task_management_voice(nlp_command, context)
                
            elif nlp_command.intent == CommandIntent.VOICE_CONTROL:
                return await self._handle_voice_control_voice(nlp_command, context)
                
            elif nlp_command.intent == CommandIntent.HELP:
                return await self._handle_help_voice(nlp_command, context)
                
            else:
                return {
                    "success": False,
                    "error": f"Unknown intent: {nlp_command.intent.value}",
                    "confidence": nlp_command.confidence
                }
                
        except Exception as e:
            logger.error(f"[{request_id}] NLP command execution failed: {e}")
            return {
                "success": False,
                "error": f"Command execution failed: {str(e)}",
                "confidence": nlp_command.confidence
            }
    
    async def _process_voice_command_fallback(self, voice_text: str, context: Optional[Dict], request_id: str) -> Dict[str, Any]:
        """Fallback voice command processing using simple string matching"""
        voice_lower = voice_text.lower()
        
        # Simple command mappings for fallback
        fallback_mappings = {
            "status": "/status",
            "list files": "/list-files", 
            "help": "/help",
            "current directory": "/current-dir"
        }
        
        for trigger, command in fallback_mappings.items():
            if trigger in voice_lower:
                # Execute the mapped command
                if command in self.supported_commands:
                    result = await self.supported_commands[command]("", "voice")
                    return {
                        "success": True,
                        "result": result,
                        "confidence": 0.6,  # Lower confidence for fallback
                        "method": "fallback_string_matching",
                        "mapped_command": command
                    }
        
        return {
            "success": False,
            "error": "Command not recognized (NLP service unavailable)",
            "confidence": 0.0,
            "method": "fallback_failed",
            "suggestions": ["Try: 'show status', 'list files', 'help me'"]
        }
    
    # NLP command handlers
    async def _handle_system_status_voice(self, nlp_command, context: Optional[Dict]) -> Dict[str, Any]:
        """Handle system status voice commands"""
        health = self.get_model_health()
        performance = self.get_performance_metrics()
        
        status_message = f"""System Status:
- Current Strategy: {self._get_current_strategy_name()}
- Health Score: {health.get('health_score', 0):.1f}/1.0
- Enhanced NLP: {'✅' if self.enhanced_initialization_status['nlp'] else '❌'}
- Response Time: {performance.get('avg_response_time', 0):.2f}s average"""
        
        return {
            "success": True,
            "message": status_message,
            "data": {
                "health": health,
                "performance": performance,
                "enhanced_status": self.enhanced_initialization_status
            },
            "confidence": nlp_command.confidence
        }
    
    async def _handle_file_operations_voice(self, nlp_command, context: Optional[Dict]) -> Dict[str, Any]:
        """Handle file operations voice commands"""
        action = nlp_command.action
        
        if action in ["list", "default"]:
            return await self._list_files("", "voice")
        elif action == "open":
            # Extract filename from parameters
            filename = self._get_parameter_value(nlp_command.parameters, "filename")
            if filename:
                return {
                    "success": True,
                    "message": f"Opening file: {filename}",
                    "action": "open_file",
                    "filename": filename,
                    "confidence": nlp_command.confidence
                }
            else:
                return {
                    "success": False,
                    "error": "No filename specified for opening",
                    "confidence": nlp_command.confidence
                }
        else:
            return {
                "success": True,
                "message": f"File operation '{action}' recognized but not fully implemented",
                "action": action,
                "confidence": nlp_command.confidence
            }
    
    async def _handle_project_navigation_voice(self, nlp_command, context: Optional[Dict]) -> Dict[str, Any]:
        """Handle project navigation voice commands"""
        action = nlp_command.action
        
        if action in ["current", "default"]:
            return await self._get_current_directory("", "voice")
        elif action == "change":
            directory = self._get_parameter_value(nlp_command.parameters, "directory", "path")
            if directory:
                return {
                    "success": True,
                    "message": f"Navigating to: {directory}",
                    "action": "change_directory",
                    "directory": directory,
                    "confidence": nlp_command.confidence
                }
            else:
                return {
                    "success": False,
                    "error": "No directory specified for navigation",
                    "confidence": nlp_command.confidence
                }
        else:
            return {
                "success": True,
                "message": f"Navigation action '{action}' recognized",
                "action": action,
                "confidence": nlp_command.confidence
            }
    
    async def _handle_code_analysis_voice(self, nlp_command, context: Optional[Dict]) -> Dict[str, Any]:
        """Handle code analysis voice commands"""
        action = nlp_command.action
        
        if self.enhanced_initialization_status["ast"]:
            filename = self._get_parameter_value(nlp_command.parameters, "filename")
            if filename:
                return {
                    "success": True,
                    "message": f"Analyzing {filename} with AST service",
                    "action": action,
                    "filename": filename,
                    "confidence": nlp_command.confidence,
                    "ast_available": True
                }
            else:
                return {
                    "success": True,
                    "message": f"Code analysis '{action}' ready (specify filename)",
                    "action": action,
                    "confidence": nlp_command.confidence,
                    "ast_available": True
                }
        else:
            return {
                "success": False,
                "error": "AST service not available for code analysis",
                "confidence": nlp_command.confidence,
                "ast_available": False
            }
    
    async def _handle_task_management_voice(self, nlp_command, context: Optional[Dict]) -> Dict[str, Any]:
        """Handle task management voice commands"""
        action = nlp_command.action
        
        if action == "create":
            task_text = self._get_parameter_value(nlp_command.parameters, "task_text")
            if task_text:
                return {
                    "success": True,
                    "message": f"Creating task: {task_text}",
                    "action": "create_task",
                    "task_text": task_text,
                    "confidence": nlp_command.confidence
                }
            else:
                return {
                    "success": False,
                    "error": "No task description provided",
                    "confidence": nlp_command.confidence
                }
        elif action in ["list", "default"]:
            return {
                "success": True,
                "message": "Listing tasks",
                "action": "list_tasks",
                "confidence": nlp_command.confidence
            }
        elif action == "complete":
            task_id = self._get_parameter_value(nlp_command.parameters, "task_id")
            if task_id:
                return {
                    "success": True,
                    "message": f"Marking task {task_id} as complete",
                    "action": "complete_task",
                    "task_id": task_id,
                    "confidence": nlp_command.confidence
                }
            else:
                return {
                    "success": False,
                    "error": "No task ID specified for completion",
                    "confidence": nlp_command.confidence
                }
        else:
            return {
                "success": True,
                "message": f"Task management action '{action}' recognized",
                "action": action,
                "confidence": nlp_command.confidence
            }
    
    async def _handle_voice_control_voice(self, nlp_command, context: Optional[Dict]) -> Dict[str, Any]:
        """Handle voice control commands"""
        action = nlp_command.action
        
        if action == "volume":
            volume_level = self._get_parameter_value(nlp_command.parameters, "volume_level")
            if volume_level:
                return {
                    "success": True,
                    "message": f"Setting volume to {volume_level}",
                    "action": "set_volume",
                    "volume": volume_level,
                    "confidence": nlp_command.confidence
                }
            else:
                return {
                    "success": False,
                    "error": "No volume level specified",
                    "confidence": nlp_command.confidence
                }
        elif action in ["activate", "deactivate"]:
            return {
                "success": True,
                "message": f"Voice control {action}",
                "action": f"voice_{action}",
                "confidence": nlp_command.confidence
            }
        else:
            return {
                "success": True,
                "message": f"Voice control action '{action}' recognized",
                "action": action,
                "confidence": nlp_command.confidence
            }
    
    async def _handle_help_voice(self, nlp_command, context: Optional[Dict]) -> Dict[str, Any]:
        """Handle help voice commands"""
        if self.nlp_service:
            suggestions = self.nlp_service.get_command_suggestions("", limit=8)
            help_message = f"""Enhanced Voice Commands Available:

**System Commands:**
- "show system status" - Get system health
- "what's running" - Check service status

**File Operations:**
- "list files" - Show directory contents
- "open file [filename]" - Open specific file

**Navigation:**
- "current directory" - Show current location
- "go to [directory]" - Change directory

**Code Analysis:**
- "analyze code" - Review code quality
- "explain function [name]" - Describe function

**Task Management:**
- "create task [description]" - Add new task
- "list tasks" - Show all tasks
- "complete task [id]" - Mark task done

**Voice Control:**
- "change volume [level]" - Adjust volume
- "mute voice" - Disable voice feedback

Enhanced NLP: {'✅ Active' if self.enhanced_initialization_status['nlp'] else '❌ Unavailable'}"""
            
            return {
                "success": True,
                "message": help_message,
                "suggestions": suggestions,
                "confidence": nlp_command.confidence,
                "enhanced_nlp_available": self.enhanced_initialization_status['nlp']
            }
        else:
            return await self._get_help("", "voice")
    
    def _get_parameter_value(self, parameters: List, *param_names: str) -> Optional[str]:
        """Extract parameter value by name from NLP command parameters"""
        for param in parameters:
            if param.name in param_names:
                return param.value
        return None


# Global instance configured from environment settings
def _get_strategy_from_config() -> MLXInferenceStrategy:
    """Get MLX strategy from configuration settings"""
    try:
        from ..config.settings import settings
        strategy_mapping = {
            "PRODUCTION": MLXInferenceStrategy.PRODUCTION,
            "PRAGMATIC": MLXInferenceStrategy.PRAGMATIC,
            "MOCK": MLXInferenceStrategy.MOCK,
            "AUTO": MLXInferenceStrategy.AUTO,
            "FALLBACK": MLXInferenceStrategy.FALLBACK
        }
        return strategy_mapping.get(settings.mlx_strategy.value, MLXInferenceStrategy.AUTO)
    except Exception as e:
        logger.warning(f"Failed to load strategy from config: {e}, using AUTO")
        return MLXInferenceStrategy.AUTO

# CONSOLIDATED UNIFIED MLX SERVICE - SINGLE ENTRY POINT
# This service consolidates all AI services into one unified interface
unified_mlx_service = UnifiedMLXService(preferred_strategy=_get_strategy_from_config())

# DEPRECATION ALIASES - These maintain backward compatibility
# All services now route through unified_mlx_service with deprecation warnings
import warnings

def _deprecated_service_warning(service_name: str):
    """Issue deprecation warning for old service usage"""
    warnings.warn(
        f"{service_name} is deprecated. Use unified_mlx_service instead. "
        f"This alias will be removed in a future version.",
        DeprecationWarning,
        stacklevel=3
    )

class _DeprecatedServiceWrapper:
    """Wrapper that issues deprecation warnings and delegates to unified service"""
    def __init__(self, service_name: str):
        self._service_name = service_name
    
    def __getattr__(self, name):
        _deprecated_service_warning(self._service_name)
        return getattr(unified_mlx_service, name)

# Backward compatibility aliases with deprecation warnings
real_mlx_service = _DeprecatedServiceWrapper("real_mlx_service")
enhanced_ai_service = _DeprecatedServiceWrapper("enhanced_ai_service")
ai_service = _DeprecatedServiceWrapper("ai_service")
pragmatic_mlx_service_instance = _DeprecatedServiceWrapper("pragmatic_mlx_service")
production_model_service_instance = _DeprecatedServiceWrapper("production_model_service")
mock_mlx_service_instance = _DeprecatedServiceWrapper("mock_mlx_service")

# Export the unified service as the primary interface
__all__ = [
    "unified_mlx_service",
    "UnifiedMLXService", 
    "MLXInferenceStrategy",
    "MLXServiceInterface",
    # Deprecated aliases (with warnings)
    "real_mlx_service",
    "enhanced_ai_service", 
    "ai_service",
    "pragmatic_mlx_service_instance",
    "production_model_service_instance",
    "mock_mlx_service_instance"
]