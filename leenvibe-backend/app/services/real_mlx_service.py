"""
Real MLX Service for L3 Agent Integration

Replaces mock_mlx_service.py with actual MLX inference using ProductionModelService.
Provides the same interface as MockMLXService but with real AI-powered responses.
"""

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional

import mlx.core as mx
import mlx.nn as nn

from .production_model_service import ModelConfig, ProductionModelService
from .simple_model_service import SimpleModelService
from .phi3_mini_service import Phi3MiniService
from .pragmatic_mlx_service import pragmatic_mlx_service

logger = logging.getLogger(__name__)


class RealMLXService:
    """
    Real MLX service that provides AI-powered code completion
    
    This service integrates with ProductionModelService to provide actual
    MLX inference for code completion, explanation, refactoring, debugging, 
    and optimization tasks.
    """
    
    def __init__(self):
        self.model_name = "microsoft/Phi-3-mini-128k-instruct"
        self.max_tokens = 512
        self.temperature = 0.3  # Lower temperature for code tasks
        self.is_initialized = False
        self.production_service = None
        self.simple_service = None
        self.phi3_service = None
        self.inference_mode = "auto"  # auto, production, phi3, simple, mock
        self.intent_prompts = self._load_intent_prompts()
        
    async def initialize(self) -> bool:
        """Initialize real MLX service with multiple fallback modes"""
        try:
            logger.info("Initializing Real MLX Service for L3 Agent integration...")
            
            # Try pragmatic service first (most reliable)
            if await self._try_pragmatic_service():
                self.inference_mode = "pragmatic"
                self.is_initialized = True
                logger.info("Real MLX Service initialized with pragmatic mode")
                return True
            
            # Try production service
            if await self._try_production_service():
                self.inference_mode = "production"
                self.is_initialized = True
                logger.info(f"Real MLX Service initialized with production mode: {self.production_service.deployment_mode}")
                return True
            
            # Try Phi-3-Mini service for real model inference
            if await self._try_phi3_service():
                self.inference_mode = "phi3"
                self.is_initialized = True
                logger.info("Real MLX Service initialized with Phi-3-Mini mode")
                return True
            
            # If all else fails, try simple service for basic MLX
            if await self._try_simple_service():
                self.inference_mode = "simple"
                self.is_initialized = True
                logger.info("Real MLX Service initialized with simple MLX mode")
                return True
            
            # If both fail, we still have the production service mock mode as fallback
            if self.production_service and self.production_service.deployment_mode == "mock":
                self.inference_mode = "mock"
                self.is_initialized = True
                logger.info("Real MLX Service initialized with mock mode (development fallback)")
                return True
            
            logger.error("Failed to initialize any MLX inference mode")
            return False
                
        except Exception as e:
            logger.error(f"Failed to initialize Real MLX Service: {e}")
            return False
    
    async def _try_production_service(self) -> bool:
        """Try to initialize production service with real MLX"""
        try:
            config = ModelConfig(
                model_name=self.model_name,
                deployment_mode="auto",  # Auto-detect best mode
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            self.production_service = ProductionModelService(config)
            success = await self.production_service.initialize()
            
            if success and self.production_service.deployment_mode != "mock":
                logger.info(f"Production service initialized successfully: {self.production_service.deployment_mode}")
                return True
            elif success:
                logger.info("Production service initialized but using mock mode")
                return False  # We want real inference, not mock
            else:
                logger.warning("Production service failed to initialize")
                return False
                
        except Exception as e:
            logger.warning(f"Production service initialization failed: {e}")
            return False
    
    async def _try_pragmatic_service(self) -> bool:
        """Try to initialize pragmatic MLX service (most reliable)"""
        try:
            logger.info("Attempting to initialize Pragmatic MLX Service...")
            success = await pragmatic_mlx_service.initialize()
            
            if success:
                logger.info("Pragmatic MLX Service initialized successfully")
                return True
            else:
                logger.warning("Pragmatic MLX Service failed to initialize")
                return False
                
        except Exception as e:
            logger.warning(f"Pragmatic MLX Service initialization failed: {e}")
            return False
    
    async def _try_phi3_service(self) -> bool:
        """Try to initialize Phi-3-Mini service for real model inference"""
        try:
            logger.info("Attempting to initialize Phi-3-Mini Service...")
            self.phi3_service = Phi3MiniService(self.model_name)
            success = await self.phi3_service.initialize()
            
            if success:
                logger.info("Phi-3-Mini Service initialized successfully")
                return True
            else:
                logger.warning("Phi-3-Mini Service failed to initialize")
                return False
                
        except Exception as e:
            logger.warning(f"Phi-3-Mini Service initialization failed: {e}")
            return False
    
    async def _try_simple_service(self) -> bool:
        """Try to initialize simple MLX service for real inference"""
        try:
            logger.info("Attempting to initialize Simple MLX Service...")
            self.simple_service = SimpleModelService()
            success = await self.simple_service.initialize()
            
            if success:
                logger.info("Simple MLX Service initialized successfully")
                return True
            else:
                logger.warning("Simple MLX Service failed to initialize")
                return False
                
        except Exception as e:
            logger.warning(f"Simple MLX Service initialization failed: {e}")
            return False
    
    async def generate_code_completion(
        self, 
        context: Dict[str, Any], 
        intent: str = "suggest"
    ) -> Dict[str, Any]:
        """
        Generate real AI-powered code completion based on AST context and intent
        
        Args:
            context: Rich AST context from L3 agent
            intent: Type of completion (suggest, explain, refactor, debug, optimize)
            
        Returns:
            Structured completion response with confidence scoring
        """
        try:
            if not self.is_initialized:
                # Attempt to initialize if not already
                init_success = await self.initialize()
                if not init_success:
                    return {
                        "status": "error",
                        "error": "MLX service not initialized and failed to initialize",
                        "confidence": 0.0
                    }
                
            logger.info(f"Generating real MLX {intent} completion with AST context")
            
            # Extract key context elements
            file_path = context.get("file_path", "")
            language = context.get("current_file", {}).get("language", "unknown")
            current_symbol = context.get("current_symbol")
            surrounding_context = context.get("surrounding_context", {})
            completion_hints = context.get("completion_hints", [])
            
            # Build context-aware prompt for the specific intent
            prompt = self._build_intent_prompt(
                intent, language, file_path, current_symbol, 
                surrounding_context, completion_hints
            )
            
            # Generate AI response using the appropriate service based on mode
            if self.inference_mode == "pragmatic":
                # Use pragmatic service directly - it handles its own response format
                return await pragmatic_mlx_service.generate_code_completion(context, intent)
            elif self.inference_mode == "production":
                ai_response = await self.production_service.generate_text(
                    prompt=prompt,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature
                )
            elif self.inference_mode == "phi3":
                ai_response = await self.phi3_service.generate_text(
                    prompt=prompt,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature
                )
            elif self.inference_mode == "simple":
                ai_response = await self.simple_service.generate_text(
                    prompt=prompt,
                    max_tokens=self.max_tokens
                )
            elif self.inference_mode == "mock":
                ai_response = await self.production_service.generate_text(
                    prompt=prompt,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature
                )
            else:
                raise RuntimeError(f"Unknown inference mode: {self.inference_mode}")
            
            # Parse and structure the AI response
            structured_response = self._structure_ai_response(
                ai_response, intent, language, context
            )
            
            # Calculate confidence based on context richness and response quality
            confidence = self._calculate_confidence(context, structured_response, intent)
            
            # Build final response
            completion_response = {
                "status": "success",
                "intent": intent,
                "model": self.model_name,
                "inference_mode": self.inference_mode,  # Indicate which mode was used
                "language": language,
                "confidence": confidence,
                "timestamp": time.time(),
                "response": structured_response["content"],
                "context_used": {
                    "file_path": file_path,
                    "has_symbol_context": current_symbol is not None,
                    "has_surrounding_context": bool(surrounding_context),
                    "hints_count": len(completion_hints),
                    "language_detected": language
                },
                "suggestions": structured_response["suggestions"],
                "requires_human_review": confidence < 0.8  # Real AI should have higher confidence threshold
            }
            
            # Add intent-specific fields
            if intent == "explain":
                completion_response["explanation"] = structured_response["content"]
            elif intent == "refactor":
                completion_response["refactoring_suggestions"] = structured_response["content"]
            elif intent == "debug":
                completion_response["debug_analysis"] = structured_response["content"]
            elif intent == "optimize":
                completion_response["optimization_suggestions"] = structured_response["content"]
            
            logger.info(f"Generated real MLX {intent} completion using {self.inference_mode} mode with {confidence:.2f} confidence")
            return completion_response
            
        except Exception as e:
            logger.error(f"Error generating real MLX completion: {e}")
            return {
                "status": "error",
                "error": f"MLX completion generation failed: {str(e)}",
                "confidence": 0.0
            }
    
    def _build_intent_prompt(
        self,
        intent: str,
        language: str,
        file_path: str,
        current_symbol: Optional[Dict[str, Any]],
        surrounding_context: Dict[str, Any],
        completion_hints: List[str]
    ) -> str:
        """Build context-aware prompt for specific intent"""
        
        # Base context
        context_info = f"Language: {language}\nFile: {file_path}\n"
        
        if current_symbol:
            context_info += f"Current Symbol: {current_symbol.get('name', 'unknown')} ({current_symbol.get('type', 'unknown')})\n"
        
        if surrounding_context:
            context_info += f"Context Lines: {surrounding_context.get('context_size', 0)}\n"
        
        if completion_hints:
            context_info += f"Hints: {', '.join(completion_hints[:3])}\n"
        
        # Get intent-specific prompt template
        prompt_template = self.intent_prompts.get(intent, self.intent_prompts["suggest"])
        
        # Format prompt with context
        return prompt_template.format(
            context=context_info,
            language=language,
            file_path=file_path
        )
    
    def _structure_ai_response(
        self, 
        ai_response: str, 
        intent: str, 
        language: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Structure raw AI response into consistent format"""
        
        # Extract the actual content from the AI response
        # The production service wraps responses with metadata
        content = ai_response
        if "**Response:**" in ai_response:
            # Extract just the AI-generated content
            parts = ai_response.split("**Response:**")
            if len(parts) > 1:
                content = parts[1].split("---")[0].strip()
        
        # Generate contextual suggestions based on intent
        suggestions = self._generate_contextual_suggestions(intent, language, content)
        
        return {
            "content": content,
            "suggestions": suggestions,
            "raw_response": ai_response
        }
    
    def _calculate_confidence(
        self, 
        context: Dict[str, Any], 
        structured_response: Dict[str, Any],
        intent: str
    ) -> float:
        """Calculate confidence score for real AI responses"""
        
        base_confidence = 0.5  # Start higher for real AI
        
        # Boost confidence based on available context
        if context.get("current_symbol"):
            base_confidence += 0.15
        
        if context.get("surrounding_context"):
            base_confidence += 0.15
        
        if context.get("completion_hints"):
            base_confidence += 0.1
        
        # Language-specific confidence
        language = context.get("current_file", {}).get("language", "unknown")
        if language in ["python", "javascript", "swift", "typescript"]:
            base_confidence += 0.1
        elif language != "unknown":
            base_confidence += 0.05
        
        # Response quality boost for real AI
        response_length = len(structured_response.get("content", ""))
        if response_length > 100:  # Substantial response
            base_confidence += 0.1
        if response_length > 500:  # Detailed response
            base_confidence += 0.05
        
        # Intent-specific confidence adjustments
        intent_multiplier = {
            "suggest": 1.0,
            "explain": 1.1,    # AI typically good at explanations
            "refactor": 0.95,
            "debug": 0.9,      # Debugging requires more caution
            "optimize": 0.9    # Optimization requires validation
        }
        
        final_confidence = base_confidence * intent_multiplier.get(intent, 0.9)
        return min(0.95, max(0.5, final_confidence))  # Clamp between 0.5 and 0.95
    
    def _generate_contextual_suggestions(
        self, 
        intent: str, 
        language: str, 
        content: str
    ) -> List[str]:
        """Generate contextual follow-up suggestions"""
        
        base_suggestions = {
            "suggest": [
                "Review the suggestion for your specific use case",
                "Consider testing the suggested approach",
                "Ask for explanation if anything is unclear"
            ],
            "explain": [
                "Ask for code improvement suggestions", 
                "Request performance optimization analysis",
                "Get examples of similar patterns"
            ],
            "refactor": [
                "Test the refactored code thoroughly",
                "Measure performance impact",
                "Consider additional refactoring opportunities"
            ],
            "debug": [
                "Add logging for debugging",
                "Write unit tests to isolate issues",
                "Use a debugger to step through the code"
            ],
            "optimize": [
                "Profile the optimized code",
                "Benchmark against original implementation",
                "Consider memory usage implications"
            ]
        }
        
        suggestions = base_suggestions.get(intent, base_suggestions["suggest"]).copy()
        
        # Add language-specific suggestions
        if language == "python":
            suggestions.append("Consider using type hints for better code clarity")
        elif language == "javascript":
            suggestions.append("Consider using TypeScript for better type safety")
        elif language == "swift":
            suggestions.append("Leverage Swift's strong type system")
        
        return suggestions[:3]  # Limit to 3 suggestions
    
    def _load_intent_prompts(self) -> Dict[str, str]:
        """Load prompt templates for different intents"""
        
        return {
            "suggest": """You are an expert coding assistant. Based on the following context, provide helpful code suggestions and improvements.

Context:
{context}

Please provide practical, actionable suggestions for improving this {language} code. Focus on:
- Code quality and best practices
- Performance improvements
- Readability and maintainability
- Language-specific idioms

Be specific and provide code examples where helpful.""",

            "explain": """You are an expert coding assistant. Analyze and explain the following code context in detail.

Context:
{context}

Please provide a clear, comprehensive explanation covering:
- What the code does and how it works
- Key concepts and patterns used
- Potential issues or improvements
- Best practices demonstrated or missing

Make your explanation educational and easy to understand.""",

            "refactor": """You are an expert coding assistant specializing in refactoring. Analyze the following code and suggest refactoring improvements.

Context:
{context}

Please provide specific refactoring suggestions focusing on:
- Code structure and organization
- Eliminating code smells
- Improving readability and maintainability
- Following {language} best practices

Provide concrete examples of how to refactor the code.""",

            "debug": """You are an expert debugging assistant. Analyze the following code context for potential issues and debugging strategies.

Context:
{context}

Please provide debugging analysis covering:
- Potential bugs or issues in the code
- Common error patterns for {language}
- Debugging strategies and techniques
- Preventive measures

Be specific about what to look for and how to debug effectively.""",

            "optimize": """You are an expert performance optimization assistant. Analyze the following code for optimization opportunities.

Context:
{context}

Please provide optimization suggestions focusing on:
- Performance bottlenecks
- Memory usage optimization
- Algorithm efficiency improvements
- {language}-specific optimizations

Provide specific, measurable optimization recommendations."""
        }


# Create global instance (same pattern as mock service)
    def get_model_health(self) -> Dict[str, Any]:
        """Get the health status of the underlying production model service"""
        if self.production_service:
            return self.production_service.get_health_status()
        return {"status": "uninitialized", "model_loaded": False}


# Create global instance (same pattern as mock service)
real_mlx_service = RealMLXService()
