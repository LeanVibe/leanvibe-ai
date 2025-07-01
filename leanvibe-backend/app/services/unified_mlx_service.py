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

logger = logging.getLogger(__name__)


class MLXInferenceStrategy(Enum):
    """Available MLX inference strategies"""
    AUTO = "auto"
    PRODUCTION = "production"
    PRAGMATIC = "pragmatic"
    MOCK = "mock"
    FALLBACK = "fallback"


class MLXServiceInterface(ABC):
    """Abstract interface for MLX service implementations"""
    
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


class ProductionMLXStrategy(MLXServiceInterface):
    """Production MLX implementation using real models with transformers"""
    
    def __init__(self):
        self.is_initialized = False
        self._transformers_service = None
        
    async def initialize(self) -> bool:
        """Initialize production MLX service with transformers"""
        try:
            # Import and initialize transformers service
            from .transformers_phi3_service import transformers_phi3_service
            
            self._transformers_service = transformers_phi3_service
            success = await self._transformers_service.initialize()
            
            if success:
                self.is_initialized = True
                logger.info("Production MLX strategy (transformers) initialized successfully")
                return True
            else:
                logger.error("Failed to initialize transformers service")
                return False
            
        except Exception as e:
            logger.error(f"Failed to initialize Production MLX strategy (transformers): {e}")
            return False
    
    async def generate_code_completion(
        self, context: Dict[str, Any], intent: str = "suggest"
    ) -> Dict[str, Any]:
        """Generate code completion using transformers models"""
        if not self.is_initialized or not self._transformers_service:
            return {
                "status": "error",
                "error": "Transformers service not initialized",
                "response": "",
                "confidence": 0.0
            }
        
        try:
            # Create a prompt from context and intent
            prompt = self._create_prompt_from_context(context, intent)
            
            # Use the transformers service's generate_text method
            result = await self._transformers_service.generate_text(
                prompt,
                max_new_tokens=150,
                temperature=0.7
            )
            
            if result["status"] == "success":
                return {
                    "status": "success",
                    "response": result["response"],
                    "confidence": 0.9,  # High confidence for real model
                    "language": self._detect_language(context),
                    "requires_human_review": False,
                    "suggestions": ["Generated with Phi-3 real model weights"],
                    "model": f"phi3-transformers-{result.get('model_name', 'unknown')}",
                    "context_used": True,
                    "using_pretrained": result.get("using_pretrained", True),
                    "generation_time": result.get("generation_time", 0),
                    "tokens_per_second": result.get("tokens_per_second", 0)
                }
            else:
                return {
                    "status": "error",
                    "error": result.get("error", "Unknown transformers error"),
                    "response": "",
                    "confidence": 0.0
                }
            
        except Exception as e:
            logger.error(f"Production MLX completion failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "response": "",
                "confidence": 0.0
            }
    
    def get_model_health(self) -> Dict[str, Any]:
        """Get production model health"""
        if self._transformers_service:
            service_health = self._transformers_service.get_health_status()
            return {
                "strategy": "production-transformers",
                "initialized": self.is_initialized,
                "model_loaded": service_health.get("model_loaded", False),
                "status": "healthy" if self.is_initialized else "unavailable",
                "service_details": service_health
            }
        else:
            return {
                "strategy": "production-transformers",
                "initialized": self.is_initialized,
                "model_loaded": False,
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
    Unified MLX service using Strategy Pattern to consolidate multiple implementations
    """
    
    def __init__(self, preferred_strategy: MLXInferenceStrategy = MLXInferenceStrategy.AUTO):
        self.preferred_strategy = preferred_strategy
        self.current_strategy: Optional[MLXServiceInterface] = None
        self.available_strategies: Dict[MLXInferenceStrategy, MLXServiceInterface] = {}
        self.is_initialized = False
        
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
        """Initialize the unified MLX service with best available strategy and enhanced logging"""
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
                    self.is_initialized = True
                    total_init_time = time.time() - init_start_time
                    
                    logger.info(
                        f"[{session_id}] Initialization SUCCESS | "
                        f"strategy={selected_strategy.value} | "
                        f"strategy_init_time={strategy_init_time:.3f}s | "
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
        
        # Generate request correlation ID
        request_id = f"mlx_comp_{int(time.time())}_{id(context):x}"
        start_time = time.time()
        
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
            
            # Enhanced result analysis and logging
            if "status" in result and result["status"] == "success":
                result["strategy_used"] = current_strategy_name
                result["request_id"] = request_id
                result["completion_time"] = round(completion_time, 3)
                
                confidence = result.get("confidence", 0.0)
                response_length = len(result.get("response", ""))
                
                logger.info(
                    f"[{request_id}] Completion SUCCESS | "
                    f"strategy={current_strategy_name} | "
                    f"time={completion_time:.3f}s | "
                    f"confidence={confidence:.2f} | "
                    f"response_length={response_length} | "
                    f"requires_review={result.get('requires_human_review', False)}"
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


# Global instance for backward compatibility with mock strategy for MVP
unified_mlx_service = UnifiedMLXService(preferred_strategy=MLXInferenceStrategy.MOCK)

# Aliases for backward compatibility
real_mlx_service = unified_mlx_service