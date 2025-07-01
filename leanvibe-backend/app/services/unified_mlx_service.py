"""
Unified MLX Service - Strategy Pattern Implementation

Consolidates multiple MLX services (real_mlx_service, pragmatic_mlx_service, 
mock_mlx_service, mlx_model_service) into a unified architecture using the 
Strategy Pattern for improved maintainability and reduced code duplication.
"""

import logging
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
        """Initialize the unified MLX service with best available strategy"""
        try:
            logger.info(f"Initializing Unified MLX Service with preferred strategy: {self.preferred_strategy.value}")
            
            # Determine strategy to use
            if self.preferred_strategy == MLXInferenceStrategy.AUTO:
                selected_strategy = await self._select_best_strategy()
            else:
                selected_strategy = self.preferred_strategy
            
            # Initialize selected strategy
            strategy_impl = self.available_strategies.get(selected_strategy)
            if strategy_impl and strategy_impl.is_available():
                success = await strategy_impl.initialize()
                if success:
                    self.current_strategy = strategy_impl
                    self.is_initialized = True
                    logger.info(f"Unified MLX Service initialized with {selected_strategy.value} strategy")
                    return True
            
            # Fallback to fallback strategy if preferred fails
            if selected_strategy != MLXInferenceStrategy.FALLBACK:
                logger.warning(f"Preferred strategy {selected_strategy.value} failed, using fallback")
                fallback_strategy = self.available_strategies[MLXInferenceStrategy.FALLBACK]
                await fallback_strategy.initialize()
                self.current_strategy = fallback_strategy
                self.is_initialized = True
                return True
            
            logger.error("Failed to initialize any MLX strategy")
            return False
            
        except Exception as e:
            logger.error(f"Failed to initialize Unified MLX Service: {e}")
            return False
    
    async def _select_best_strategy(self) -> MLXInferenceStrategy:
        """Automatically select the best available strategy"""
        # Priority order: Production > Pragmatic > Mock > Fallback
        priority_order = [
            MLXInferenceStrategy.PRODUCTION,
            MLXInferenceStrategy.PRAGMATIC,
            MLXInferenceStrategy.MOCK,
            MLXInferenceStrategy.FALLBACK
        ]
        
        for strategy in priority_order:
            strategy_impl = self.available_strategies.get(strategy)
            if strategy_impl and strategy_impl.is_available():
                logger.info(f"Auto-selected {strategy.value} strategy")
                return strategy
        
        # Ultimate fallback
        return MLXInferenceStrategy.FALLBACK
    
    async def generate_code_completion(
        self, context: Dict[str, Any], intent: str = "suggest"
    ) -> Dict[str, Any]:
        """Generate code completion using current strategy"""
        if not self.is_initialized or not self.current_strategy:
            return {
                "status": "error",
                "error": "Unified MLX service not initialized",
                "response": "",
                "confidence": 0.0
            }
        
        try:
            result = await self.current_strategy.generate_code_completion(context, intent)
            
            # Add strategy information to result
            if "status" in result and result["status"] == "success":
                result["strategy_used"] = self._get_current_strategy_name()
            
            return result
            
        except Exception as e:
            logger.error(f"Unified MLX completion failed: {e}")
            
            # Try fallback if current strategy fails
            if self.current_strategy != self.available_strategies[MLXInferenceStrategy.FALLBACK]:
                logger.warning("Current strategy failed, falling back to fallback strategy")
                fallback = self.available_strategies[MLXInferenceStrategy.FALLBACK]
                return await fallback.generate_code_completion(context, intent)
            
            return {
                "status": "error",
                "error": str(e),
                "response": "",
                "confidence": 0.0
            }
    
    def get_model_health(self) -> Dict[str, Any]:
        """Get comprehensive health status of MLX service"""
        if not self.current_strategy:
            return {
                "status": "uninitialized",
                "current_strategy": None,
                "available_strategies": []
            }
        
        # Get health from current strategy
        current_health = self.current_strategy.get_model_health()
        
        # Check availability of all strategies
        available_strategies = []
        for strategy, impl in self.available_strategies.items():
            if impl.is_available():
                available_strategies.append(strategy.value)
        
        return {
            "status": "healthy" if self.is_initialized else "unhealthy",
            "current_strategy": current_health,
            "available_strategies": available_strategies,
            "preferred_strategy": self.preferred_strategy.value,
            "fallback_available": True  # Fallback is always available
        }
    
    def _get_current_strategy_name(self) -> str:
        """Get name of current strategy"""
        if not self.current_strategy:
            return "none"
        
        for strategy, impl in self.available_strategies.items():
            if impl == self.current_strategy:
                return strategy.value
        
        return "unknown"
    
    async def switch_strategy(self, new_strategy: MLXInferenceStrategy) -> bool:
        """Switch to a different strategy"""
        try:
            if new_strategy not in self.available_strategies:
                logger.error(f"Strategy {new_strategy.value} not available")
                return False
            
            strategy_impl = self.available_strategies[new_strategy]
            if not strategy_impl.is_available():
                logger.error(f"Strategy {new_strategy.value} is not available")
                return False
            
            # Initialize new strategy
            success = await strategy_impl.initialize()
            if success:
                self.current_strategy = strategy_impl
                logger.info(f"Successfully switched to {new_strategy.value} strategy")
                return True
            else:
                logger.error(f"Failed to initialize {new_strategy.value} strategy")
                return False
                
        except Exception as e:
            logger.error(f"Error switching to {new_strategy.value} strategy: {e}")
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