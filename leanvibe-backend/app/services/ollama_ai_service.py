"""
Ollama AI Service for LeanVibe Backend

Provides high-quality AI inference using Ollama with DeepSeek R1 and other models.
This replaces the inadequate Phi-3-Mini with much better coding-focused models.
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional, List
import httpx

logger = logging.getLogger(__name__)


class OllamaAIService:
    """AI service using Ollama for high-quality local inference"""
    
    def __init__(self, 
                 host: str = "localhost",
                 port: int = 11434,
                 default_model: str = "deepseek-r1:32b",
                 timeout: int = 300):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.default_model = default_model
        self.timeout = timeout
        self.client = None
        self.available_models = []
        self.initialized = False
        
        # Performance tracking
        self.request_count = 0
        self.total_response_time = 0
        self.last_response_time = 0
        
    async def initialize(self) -> bool:
        """Initialize Ollama connection and check available models"""
        try:
            logger.info(f"Initializing Ollama AI service at {self.base_url}")
            
            # Create HTTP client
            self.client = httpx.AsyncClient(timeout=self.timeout)
            
            # Test connection
            response = await self.client.get(f"{self.base_url}/api/tags")
            
            if response.status_code == 200:
                models_data = response.json()
                self.available_models = [model["name"] for model in models_data.get("models", [])]
                
                logger.info(f"✅ Connected to Ollama successfully")
                logger.info(f"📋 Available models: {', '.join(self.available_models)}")
                
                # Check if default model is available
                if self.default_model in self.available_models:
                    logger.info(f"🎯 Default model '{self.default_model}' is available")
                else:
                    logger.warning(f"⚠️ Default model '{self.default_model}' not found")
                    if self.available_models:
                        self.default_model = self.available_models[0]
                        logger.info(f"🔄 Switched to '{self.default_model}' as default")
                    else:
                        logger.error("❌ No models available in Ollama")
                        return False
                
                self.initialized = True
                return True
            else:
                logger.error(f"❌ Failed to connect to Ollama: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ollama initialization failed: {e}")
            return False
    
    async def generate(self, 
                      prompt: str, 
                      model: Optional[str] = None,
                      max_tokens: int = 1000,
                      temperature: float = 0.1,
                      stream: bool = False) -> Optional[str]:
        """Generate response using Ollama"""
        if not self.initialized:
            logger.error("Ollama service not initialized")
            return None
            
        model = model or self.default_model
        
        try:
            start_time = time.time()
            
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": stream,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }
            
            logger.debug(f"🤖 Generating response with {model}")
            
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json=payload
            )
            
            if response.status_code == 200:
                response_data = response.json()
                generated_text = response_data.get("response", "")
                
                # Update performance metrics
                response_time = time.time() - start_time
                self.last_response_time = response_time
                self.request_count += 1
                self.total_response_time += response_time
                
                logger.info(f"✅ Generated response in {response_time:.2f}s ({len(generated_text)} chars)")
                
                return generated_text
            else:
                logger.error(f"❌ Generation failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Generation error: {e}")
            return None
    
    async def analyze_code(self, 
                          code: str, 
                          language: str = "python",
                          analysis_type: str = "review") -> Optional[Dict[str, Any]]:
        """Analyze code with specific prompts for different analysis types"""
        
        prompts = {
            "review": f"""Please review this {language} code and provide feedback:

```{language}
{code}
```

Analyze:
1. Code quality and best practices
2. Potential bugs or issues
3. Performance considerations
4. Suggestions for improvement
5. Security concerns

Provide your analysis in a structured format.""",

            "explain": f"""Please explain this {language} code in detail:

```{language}
{code}
```

Explain:
1. What the code does (purpose)
2. How it works (step by step)
3. Key concepts used
4. Potential use cases
5. Any notable patterns or techniques""",

            "optimize": f"""Please suggest optimizations for this {language} code:

```{language}
{code}
```

Focus on:
1. Performance improvements
2. Memory efficiency
3. Readability enhancements
4. Best practice implementations
5. Provide the optimized version"""
        }
        
        prompt = prompts.get(analysis_type, prompts["review"])
        
        try:
            result = await self.generate(prompt, max_tokens=2000, temperature=0.1)
            
            if result:
                return {
                    "analysis_type": analysis_type,
                    "language": language,
                    "original_code": code,
                    "analysis": result,
                    "timestamp": time.time(),
                    "model": self.default_model
                }
            else:
                return None
                
        except Exception as e:
            logger.error(f"Code analysis failed: {e}")
            return None
    
    async def chat(self, 
                   message: str, 
                   context: Optional[List[Dict[str, str]]] = None,
                   model: Optional[str] = None) -> Optional[str]:
        """Chat interface with optional conversation context"""
        
        # Build conversation context
        if context:
            conversation = []
            for msg in context:
                conversation.append(f"User: {msg.get('user', '')}")
                conversation.append(f"Assistant: {msg.get('assistant', '')}")
            
            full_prompt = "\n".join(conversation) + f"\nUser: {message}\nAssistant:"
        else:
            full_prompt = f"User: {message}\nAssistant:"
        
        try:
            response = await self.generate(
                full_prompt, 
                model=model,
                max_tokens=1500,
                temperature=0.3
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Chat error: {e}")
            return None
    
    async def get_models(self) -> List[str]:
        """Get list of available models"""
        if not self.initialized:
            await self.initialize()
        return self.available_models
    
    async def health_check(self) -> Dict[str, Any]:
        """Check service health and performance metrics"""
        try:
            if not self.initialized:
                return {
                    "status": "not_initialized",
                    "available": False,
                    "error": "Service not initialized"
                }
            
            # Test with a simple prompt
            start_time = time.time()
            test_response = await self.generate("Hello", max_tokens=10)
            test_time = time.time() - start_time
            
            avg_response_time = (self.total_response_time / self.request_count 
                               if self.request_count > 0 else 0)
            
            return {
                "status": "healthy" if test_response else "unhealthy",
                "available": test_response is not None,
                "default_model": self.default_model,
                "available_models": self.available_models,
                "performance": {
                    "last_response_time": self.last_response_time,
                    "average_response_time": avg_response_time,
                    "total_requests": self.request_count,
                    "test_response_time": test_time
                },
                "timestamp": time.time()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "available": False,
                "error": str(e),
                "timestamp": time.time()
            }
    
    async def close(self):
        """Close the HTTP client"""
        if self.client:
            await self.client.aclose()
            logger.info("🔌 Ollama AI service connection closed")
    
    def is_ready(self) -> bool:
        """Check if service is ready for use"""
        return self.initialized and bool(self.available_models)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        avg_response_time = (self.total_response_time / self.request_count 
                           if self.request_count > 0 else 0)
        
        return {
            "total_requests": self.request_count,
            "average_response_time": avg_response_time,
            "last_response_time": self.last_response_time,
            "current_model": self.default_model,
            "available_models": len(self.available_models)
        }


# Global service instance
ollama_service = OllamaAIService()


async def get_ollama_service() -> OllamaAIService:
    """Get the global Ollama service instance"""
    if not ollama_service.initialized:
        await ollama_service.initialize()
    return ollama_service