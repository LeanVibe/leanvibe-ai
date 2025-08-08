"""
Mock MLX Services Implementation for Testing

Provides comprehensive mock implementations of all MLX-based AI services
that allows tests to run without actual MLX dependencies.
"""

import asyncio
import logging
import time
from typing import Any, AsyncGenerator, Dict, List, Optional, Union
from unittest.mock import MagicMock

logger = logging.getLogger(__name__)


class MockMLXArray:
    """Mock implementation of MLX array"""
    
    def __init__(self, data: Any, shape: tuple = (1,), dtype: str = "float32"):
        self.data = data
        self.shape = shape
        self.dtype = dtype
    
    def item(self):
        """Return scalar value"""
        return self.data if isinstance(self.data, (int, float)) else 0.5
    
    def tolist(self):
        """Convert to Python list"""
        return self.data if isinstance(self.data, list) else [self.data]
    
    def __str__(self):
        return f"MockMLXArray(shape={self.shape}, dtype={self.dtype})"


class MockMLXModule:
    """Mock MLX module"""
    
    array = MockMLXArray
    
    @staticmethod
    def random_uniform(shape: tuple = (1,)) -> MockMLXArray:
        return MockMLXArray(0.5, shape)
    
    @staticmethod
    def zeros(shape: tuple) -> MockMLXArray:
        return MockMLXArray(0.0, shape)
    
    @staticmethod
    def ones(shape: tuple) -> MockMLXArray:
        return MockMLXArray(1.0, shape)


class MockTokenizer:
    """Mock implementation of a tokenizer"""
    
    def __init__(self, model_name: str = "mock-tokenizer"):
        self.model_name = model_name
        self.vocab_size = 50000
        self.pad_token_id = 0
        self.eos_token_id = 2
        self.bos_token_id = 1
    
    def encode(self, text: str) -> List[int]:
        """Mock text encoding"""
        # Simple mock: return token IDs based on text length
        return list(range(1, min(len(text.split()), 20) + 1))
    
    def decode(self, token_ids: List[int]) -> str:
        """Mock text decoding"""
        # Simple mock: return placeholder text
        return f"mock_decoded_text_tokens_{len(token_ids)}"
    
    def __call__(self, text: Union[str, List[str]], **kwargs) -> Dict[str, Any]:
        """Mock tokenizer call"""
        if isinstance(text, str):
            text = [text]
        
        encoded = [self.encode(t) for t in text]
        max_len = max(len(e) for e in encoded) if encoded else 0
        
        # Pad sequences
        input_ids = []
        attention_mask = []
        
        for seq in encoded:
            padded = seq + [self.pad_token_id] * (max_len - len(seq))
            mask = [1] * len(seq) + [0] * (max_len - len(seq))
            input_ids.append(padded)
            attention_mask.append(mask)
        
        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
        }


class MockMLXModel:
    """Mock implementation of an MLX model"""
    
    def __init__(self, model_name: str = "mock-model"):
        self.model_name = model_name
        self.config = {
            "vocab_size": 50000,
            "hidden_size": 4096,
            "num_layers": 32,
            "max_position_embeddings": 2048,
        }
        self.loaded = False
    
    def load_weights(self, path: str):
        """Mock weight loading"""
        logger.info(f"Mock loading weights from {path}")
        self.loaded = True
    
    def generate(self, input_ids: List[int], max_tokens: int = 100, 
                temperature: float = 0.7, **kwargs) -> List[int]:
        """Mock text generation"""
        # Generate mock token sequence
        generated = input_ids.copy()
        for i in range(max_tokens):
            # Mock next token prediction
            next_token = (len(generated) % 1000) + 100
            generated.append(next_token)
            
            # Stop at mock EOS token
            if next_token == 2:
                break
        
        return generated
    
    async def agenerate(self, input_ids: List[int], max_tokens: int = 100, 
                       temperature: float = 0.7, **kwargs) -> AsyncGenerator[int, None]:
        """Mock async text generation"""
        for i in range(max_tokens):
            await asyncio.sleep(0.01)  # Simulate processing time
            next_token = (len(input_ids) + i) % 1000 + 100
            yield next_token
            
            # Stop at mock EOS token
            if next_token == 2:
                break
    
    def __call__(self, input_ids: Any, **kwargs) -> Dict[str, MockMLXArray]:
        """Mock model forward pass"""
        batch_size = 1
        seq_len = len(input_ids[0]) if isinstance(input_ids[0], list) else len(input_ids)
        vocab_size = self.config["vocab_size"]
        
        # Mock logits
        logits_data = [0.1] * vocab_size
        logits_data[100] = 0.9  # Mock high probability for token 100
        
        return {
            "logits": MockMLXArray(logits_data, (batch_size, seq_len, vocab_size))
        }


class MockMLXService:
    """Enhanced mock MLX service with more realistic behaviors"""
    
    def __init__(self, model_name: str = "mlx-community/Qwen2.5-Coder-32B-Instruct"):
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self.is_initialized = False
        self.generation_count = 0
        
        # Mock model capabilities
        self.max_tokens = 4096
        self.temperature = 0.7
        self.top_p = 0.9
        
        logger.info(f"MockMLXService created with model: {model_name}")
    
    async def initialize(self) -> bool:
        """Mock service initialization"""
        try:
            logger.info(f"Mock initializing MLX service with {self.model_name}")
            
            # Simulate loading time
            await asyncio.sleep(0.2)
            
            # Create mock model and tokenizer
            self.model = MockMLXModel(self.model_name)
            self.tokenizer = MockTokenizer("mock-tokenizer")
            
            # Mock weight loading
            self.model.load_weights("mock/path/to/weights")
            
            self.is_initialized = True
            logger.info("Mock MLX service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Mock MLX initialization failed: {e}")
            return False
    
    async def generate_response(self, prompt: str, max_tokens: int = 1024, 
                              temperature: float = 0.7, **kwargs) -> Dict[str, Any]:
        """Mock response generation"""
        try:
            if not self.is_initialized:
                return {
                    "status": "error",
                    "error": "Mock MLX service not initialized"
                }
            
            logger.info(f"Mock generating response for prompt: {prompt[:50]}...")
            
            # Simulate processing time
            await asyncio.sleep(0.3)
            self.generation_count += 1
            
            # Generate mock response based on prompt content
            response_text = self._generate_mock_response(prompt)
            
            # Mock token usage
            input_tokens = len(self.tokenizer.encode(prompt))
            output_tokens = len(self.tokenizer.encode(response_text))
            
            return {
                "status": "success",
                "response": response_text,
                "model": self.model_name,
                "usage": {
                    "prompt_tokens": input_tokens,
                    "completion_tokens": output_tokens,
                    "total_tokens": input_tokens + output_tokens
                },
                "generation_time": 0.3,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "generation_id": f"mock_gen_{self.generation_count}"
            }
            
        except Exception as e:
            logger.error(f"Mock generation error: {e}")
            return {
                "status": "error",
                "error": f"Mock generation failed: {str(e)}"
            }
    
    async def generate_streaming_response(self, prompt: str, max_tokens: int = 1024,
                                        temperature: float = 0.7, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """Mock streaming response generation"""
        try:
            if not self.is_initialized:
                yield {
                    "status": "error",
                    "error": "Mock MLX service not initialized"
                }
                return
            
            logger.info(f"Mock streaming generation for prompt: {prompt[:50]}...")
            
            # Generate full response
            response_text = self._generate_mock_response(prompt)
            words = response_text.split()
            
            # Stream response word by word
            current_text = ""
            for i, word in enumerate(words):
                current_text += f"{word} "
                progress = (i + 1) / len(words)
                
                yield {
                    "status": "streaming",
                    "delta": f"{word} ",
                    "text": current_text.strip(),
                    "progress": progress,
                    "is_final": i == len(words) - 1
                }
                
                await asyncio.sleep(0.05)  # Simulate streaming delay
            
            # Final metadata
            yield {
                "status": "complete",
                "model": self.model_name,
                "usage": {
                    "prompt_tokens": len(self.tokenizer.encode(prompt)),
                    "completion_tokens": len(words),
                    "total_tokens": len(self.tokenizer.encode(prompt)) + len(words)
                },
                "generation_time": len(words) * 0.05
            }
            
        except Exception as e:
            logger.error(f"Mock streaming error: {e}")
            yield {
                "status": "error",
                "error": f"Mock streaming failed: {str(e)}"
            }
    
    async def generate_code_completion(self, context: Dict[str, Any], 
                                     intent: str = "suggest") -> Dict[str, Any]:
        """Mock code completion generation"""
        try:
            if not self.is_initialized:
                return {
                    "status": "error",
                    "error": "Mock MLX service not initialized"
                }
            
            file_path = context.get("file_path", "")
            language = context.get("current_file", {}).get("language", "unknown")
            current_symbol = context.get("current_symbol")
            
            logger.info(f"Mock code completion: {intent} for {language}")
            
            # Generate contextual response
            response = self._generate_code_response(language, intent, current_symbol)
            confidence = self._calculate_confidence(context, intent)
            
            await asyncio.sleep(0.2)  # Simulate processing
            
            return {
                "status": "success",
                "intent": intent,
                "language": language,
                "response": response,
                "confidence": confidence,
                "model": self.model_name,
                "timestamp": time.time(),
                "context_used": {
                    "file_path": file_path,
                    "language": language,
                    "has_symbol": current_symbol is not None
                },
                "suggestions": self._get_follow_up_suggestions(intent),
                "requires_review": confidence < 0.7
            }
            
        except Exception as e:
            logger.error(f"Mock code completion error: {e}")
            return {
                "status": "error",
                "error": f"Mock code completion failed: {str(e)}"
            }
    
    async def analyze_code(self, code: str, analysis_type: str = "quality") -> Dict[str, Any]:
        """Mock code analysis"""
        try:
            if not self.is_initialized:
                return {"status": "error", "error": "Service not initialized"}
            
            logger.info(f"Mock code analysis: {analysis_type}")
            await asyncio.sleep(0.1)
            
            # Mock analysis results
            if analysis_type == "quality":
                issues = [
                    {"type": "style", "message": "Mock: Consider adding docstring", "line": 1},
                    {"type": "complexity", "message": "Mock: Function is too complex", "line": 5}
                ]
                score = 0.8
            elif analysis_type == "security":
                issues = [
                    {"type": "security", "message": "Mock: Potential SQL injection", "line": 10}
                ]
                score = 0.6
            else:
                issues = []
                score = 0.9
            
            return {
                "status": "success",
                "analysis_type": analysis_type,
                "score": score,
                "issues": issues,
                "suggestions": ["Mock suggestion: Add error handling"],
                "model": self.model_name
            }
            
        except Exception as e:
            logger.error(f"Mock code analysis error: {e}")
            return {"status": "error", "error": str(e)}
    
    def _generate_mock_response(self, prompt: str) -> str:
        """Generate contextually appropriate mock responses"""
        prompt_lower = prompt.lower()
        
        if "function" in prompt_lower and "python" in prompt_lower:
            return """Here's a Python function suggestion:

```python
def process_data(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    \"\"\"
    Process the input data and return results.
    
    Args:
        data: List of data dictionaries to process
        
    Returns:
        Dictionary containing processed results
    \"\"\"
    processed_items = []
    for item in data:
        if item.get('valid', True):
            processed_items.append(item)
    
    return {
        'processed_count': len(processed_items),
        'items': processed_items
    }
```

This function includes type hints, proper documentation, and error handling."""
        
        elif "error" in prompt_lower or "debug" in prompt_lower:
            return """Here are some debugging suggestions:

1. **Check Variable Types**: Ensure all variables are the expected types
2. **Add Logging**: Insert logging statements to trace execution flow  
3. **Validate Inputs**: Add input validation to catch edge cases
4. **Test Edge Cases**: Consider empty inputs, null values, boundary conditions
5. **Review Stack Trace**: Examine the full error stack trace for clues

Common debugging techniques:
- Print intermediate values
- Use a debugger with breakpoints
- Write unit tests to isolate the issue
- Check for off-by-one errors in loops"""
        
        elif "refactor" in prompt_lower:
            return """Refactoring suggestions:

1. **Extract Method**: Break large functions into smaller, focused methods
2. **Rename Variables**: Use descriptive names that explain purpose
3. **Remove Duplication**: Consolidate repeated code into reusable functions
4. **Simplify Conditionals**: Use early returns to reduce nesting
5. **Add Constants**: Replace magic numbers with named constants

Example refactoring:
```python
# Before
def calc(x, y, t):
    if t == 1:
        return x + y
    elif t == 2:
        return x * y
    return 0

# After  
OPERATION_ADD = 1
OPERATION_MULTIPLY = 2

def calculate(first_value, second_value, operation_type):
    if operation_type == OPERATION_ADD:
        return first_value + second_value
    if operation_type == OPERATION_MULTIPLY:
        return first_value * second_value
    return 0
```"""
        
        else:
            return f"""Mock response for your query about: {prompt[:100]}...

This is a simulated response from the MLX model. In a real implementation, this would be generated by the actual language model based on the context and prompt provided.

Key points:
- This demonstrates the response format
- Actual responses would be more contextually relevant
- The mock maintains consistent structure for testing
- Response quality depends on the actual model capabilities

For testing purposes, this mock response includes realistic formatting and structure while providing predictable output for test assertions."""
    
    def _generate_code_response(self, language: str, intent: str, current_symbol: Optional[Dict]) -> str:
        """Generate language and intent-specific code responses"""
        
        if intent == "suggest" and language == "python":
            if current_symbol and current_symbol.get("type") == "function":
                return f"""Suggestions for Python function '{current_symbol.get("name", "function")}':

1. **Type Annotations**: Add type hints for clarity
2. **Documentation**: Include docstring with parameters and return value
3. **Error Handling**: Add try-except blocks for robust error handling
4. **Testing**: Consider writing unit tests

Example:
```python
def {current_symbol.get("name", "function_name")}(param: str) -> Optional[str]:
    \"\"\"
    Description of function purpose.
    
    Args:
        param: Description of parameter
        
    Returns:
        Description of return value
    \"\"\"
    try:
        # Implementation here
        return processed_result
    except Exception as e:
        logger.error(f"Error in {current_symbol.get("name", "function")}: {{e}}")
        return None
```"""
            else:
                return """Python code suggestions:

1. **PEP 8 Compliance**: Follow Python style guidelines
2. **List Comprehensions**: Use for concise data transformations  
3. **Context Managers**: Use 'with' statements for resource management
4. **Type Hints**: Add annotations for better documentation
5. **Exception Handling**: Use specific exception types"""
        
        elif intent == "explain":
            return f"""Code Explanation for {language}:

This code section demonstrates common patterns in {language} development. The structure follows standard conventions for the language.

**Key Components:**
- Function/method definitions with appropriate parameters
- Variable assignments and data manipulation
- Control flow structures (if/else, loops)
- Error handling mechanisms specific to {language}

**Best Practices Observed:**
- Clear naming conventions
- Proper code organization
- Appropriate use of language features

**Potential Improvements:**
- Consider adding more comprehensive documentation
- Evaluate error handling completeness
- Review performance implications"""
        
        else:
            return f"""Mock {intent} response for {language}:

This is a contextual response based on the intent '{intent}' and language '{language}'. 
The actual implementation would provide specific guidance based on the code context 
and the type of assistance requested."""
    
    def _calculate_confidence(self, context: Dict[str, Any], intent: str) -> float:
        """Calculate mock confidence score"""
        base_confidence = 0.5
        
        # Boost for available context
        if context.get("current_symbol"):
            base_confidence += 0.2
        if context.get("surrounding_context"):
            base_confidence += 0.1
        if context.get("completion_hints"):
            base_confidence += 0.1
        
        # Language-specific confidence
        language = context.get("current_file", {}).get("language", "unknown")
        if language in ["python", "javascript", "typescript"]:
            base_confidence += 0.1
        
        # Intent-specific adjustments
        intent_multipliers = {
            "suggest": 1.0,
            "explain": 1.1,
            "refactor": 0.9,
            "debug": 0.8,
            "optimize": 0.8
        }
        
        return min(0.95, base_confidence * intent_multipliers.get(intent, 0.8))
    
    def _get_follow_up_suggestions(self, intent: str) -> List[str]:
        """Generate follow-up suggestions"""
        suggestions_map = {
            "suggest": [
                "Request code explanation",
                "Get refactoring recommendations", 
                "Ask for debugging help"
            ],
            "explain": [
                "Request improvement suggestions",
                "Get performance analysis",
                "Ask about best practices"
            ],
            "refactor": [
                "Test refactored code",
                "Get performance impact analysis",
                "Request additional improvements"
            ],
            "debug": [
                "Set up debugging environment",
                "Write unit tests",
                "Profile performance"
            ],
            "optimize": [
                "Benchmark performance",
                "Analyze memory usage",  
                "Consider algorithms alternatives"
            ]
        }
        
        return suggestions_map.get(intent, ["Ask follow-up questions"])
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get mock model information"""
        return {
            "model_name": self.model_name,
            "is_initialized": self.is_initialized,
            "capabilities": [
                "text_generation",
                "code_completion", 
                "code_analysis",
                "streaming_generation"
            ],
            "parameters": {
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "top_p": self.top_p
            },
            "generation_count": self.generation_count
        }


class MockTransformersService:
    """Mock Transformers-based AI service"""
    
    def __init__(self, model_name: str = "microsoft/phi-3-mini"):
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self.is_initialized = False
    
    async def initialize(self) -> bool:
        """Mock initialization"""
        try:
            logger.info(f"Mock initializing Transformers service with {self.model_name}")
            await asyncio.sleep(0.1)
            
            self.model = MockMLXModel(self.model_name)
            self.tokenizer = MockTokenizer()
            self.is_initialized = True
            
            logger.info("Mock Transformers service initialized")
            return True
            
        except Exception as e:
            logger.error(f"Mock Transformers initialization failed: {e}")
            return False
    
    async def generate_response(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Mock response generation using transformers"""
        if not self.is_initialized:
            return {"status": "error", "error": "Service not initialized"}
        
        # Use similar mock generation logic
        response = f"Mock Transformers response for: {prompt[:50]}..."
        
        return {
            "status": "success", 
            "response": response,
            "model": self.model_name,
            "backend": "transformers"
        }


# Mock module components for importing
class MockMLX:
    """Mock MLX module"""
    core = MockMLXModule()
    
    @staticmethod
    def array(data, dtype=None):
        return MockMLXArray(data, dtype=dtype or "float32")


# Global service instances
mock_mlx_service = MockMLXService()
mock_transformers_service = MockTransformersService()

# Mock mlx module for imports
mlx = MockMLX()
mlx_core = MockMLXModule()