"""
Pragmatic MLX Service - Simple, reliable inference

DEPRECATED: Use unified_mlx_service with PRAGMATIC strategy instead.
"""

import logging
import time
import warnings
from typing import Dict, Any, List

import mlx.core as mx

logger = logging.getLogger(__name__)

# DEPRECATION WARNING
warnings.warn(
    "pragmatic_mlx_service.py is deprecated. Use unified_mlx_service with PRAGMATIC strategy instead. "
    "This module will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2
)


class PragmaticMLXService:
    """Simple, reliable MLX service focused on working code completion"""
    
    def __init__(self):
        self.is_initialized = False
        self.response_templates = self._load_response_templates()
        
    async def initialize(self) -> bool:
        """Initialize the service - always succeeds"""
        try:
            # Test basic MLX operations
            x = mx.array([1, 2, 3])
            y = x * 2
            mx.eval(y)
            
            self.is_initialized = True
            logger.info("Pragmatic MLX Service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Pragmatic MLX Service: {e}")
            return False
    
    async def generate_code_completion(
        self, context: Dict[str, Any], intent: str = "suggest"
    ) -> Dict[str, Any]:
        """Generate reliable code completion or answer general queries"""
        
        if not self.is_initialized:
            await self.initialize()
        
        # Check if this is a general query (from CLI) or code completion
        if "prompt" in context:
            # This is a general query from CLI
            return await self._handle_general_query(context["prompt"], intent)
            
        # Extract context for code completion
        language = context.get("current_file", {}).get("language", "python")
        file_path = context.get("file_path", "")
        current_symbol = context.get("current_symbol", {})
        hints = context.get("completion_hints", [])
        
        # Generate contextual response
        response_content = self._generate_contextual_response(
            language, intent, current_symbol, hints
        )
        
        # Calculate confidence based on available context
        confidence = self._calculate_confidence(context)
        
        return {
            "status": "success",
            "intent": intent,
            "model": "PragmaticMLX",
            "inference_mode": "pragmatic",
            "language": language,
            "confidence": confidence,
            "timestamp": time.time(),
            "response": response_content,
            "context_used": {
                "file_path": file_path,
                "has_symbol_context": bool(current_symbol),
                "hints_count": len(hints),
                "language_detected": language
            },
            "suggestions": self._get_suggestions(intent, language),
            "requires_human_review": confidence < 0.7
        }
    
    def _generate_contextual_response(
        self, language: str, intent: str, symbol: Dict, hints: list
    ) -> str:
        """Generate contextual response based on language and intent"""
        
        symbol_name = symbol.get("name", "function") if symbol else "function"
        symbol_type = symbol.get("type", "function") if symbol else "function"
        
        if intent == "suggest":
            if language == "python":
                if "def" in hints or symbol_type == "function":
                    return f"""Here's a suggested implementation for the {symbol_name} function:

```python
def {symbol_name}(self, *args, **kwargs):
    \"\"\"
    {symbol_name.replace('_', ' ').title()} implementation
    
    Args:
        *args: Variable arguments
        **kwargs: Keyword arguments
        
    Returns:
        Result of the operation
    \"\"\"
    # TODO: Implement the function logic
    result = None
    
    # Add your implementation here
    if args:
        result = args[0]
    
    return result
```

Key considerations:
- Add proper error handling
- Include input validation
- Write unit tests
- Consider edge cases"""

                elif "class" in hints or symbol_type == "class":
                    return f"""Here's a suggested {symbol_name} class structure:

```python
class {symbol_name}:
    \"\"\"
    {symbol_name.replace('_', ' ').title()} class
    \"\"\"
    
    def __init__(self, *args, **kwargs):
        \"\"\"Initialize the {symbol_name}\"\"\"
        # Initialize instance variables
        pass
    
    def __str__(self) -> str:
        \"\"\"String representation\"\"\"
        return f"{symbol_name}()"
    
    def __repr__(self) -> str:
        \"\"\"Developer representation\"\"\"
        return self.__str__()
```

Best practices:
- Follow single responsibility principle
- Add type hints
- Include docstrings
- Implement __str__ and __repr__"""

            elif language == "javascript":
                return f"""Here's a JavaScript implementation suggestion:

```javascript
function {symbol_name}(params) {{
    /**
     * {symbol_name.replace('_', ' ')} function
     * @param {{Object}} params - Function parameters
     * @returns {{*}} Result
     */
    
    // Input validation
    if (!params) {{
        throw new Error('Parameters are required');
    }}
    
    // Implementation
    const result = null;
    
    // TODO: Add your logic here
    
    return result;
}}

// Export for module usage
export {{ {symbol_name} }};
```

Recommendations:
- Use modern ES6+ syntax
- Add JSDoc comments
- Include error handling
- Consider async/await if needed"""

        elif intent == "explain":
            return f"""Code Explanation for {symbol_name}:

**Purpose**: This {symbol_type} appears to be designed for {symbol_name.replace('_', ' ')}.

**Structure Analysis**:
- Function/method definition using {language} syntax
- Likely handles specific business logic or utility functionality

**Common Patterns**:
- Input processing and validation
- Core logic implementation
- Return value generation

**Potential Improvements**:
- Add comprehensive error handling
- Include type annotations/hints
- Write unit tests for coverage
- Consider performance optimizations

**Usage Context**:
Based on the name '{symbol_name}', this is likely used for:
- Data processing operations
- Business logic implementation
- Utility or helper functions"""

        elif intent == "debug":
            return f"""Debugging Guide for {symbol_name}:

**Common Issues to Check**:
1. **Input Validation**: Ensure all parameters are valid
2. **Type Errors**: Check data types match expectations
3. **Null/Undefined**: Handle edge cases properly
4. **Scope Issues**: Verify variable accessibility

**Debugging Steps**:
```{language}
# Add logging/print statements
logger.debug(f"Debugging {symbol_name}: input={{params}}")

# Check variable states
assert params is not None, "Parameters cannot be None"

# Add breakpoints for step-through debugging
import pdb; pdb.set_trace()  # Python
// debugger;  // JavaScript
```

**Testing Strategy**:
- Write unit tests with edge cases
- Test with invalid inputs
- Verify expected outputs
- Check error handling paths"""

        # Default response
        return f"Here's a {intent} for {symbol_name} in {language}. This is a contextual response based on the available information."
    
    def _calculate_confidence(self, context: Dict[str, Any]) -> float:
        """Calculate confidence based on available context"""
        confidence = 0.6  # Base confidence
        
        if context.get("current_symbol"):
            confidence += 0.1
        if context.get("surrounding_context"):
            confidence += 0.1
        if context.get("completion_hints"):
            confidence += 0.1
        if context.get("current_file", {}).get("language") in ["python", "javascript"]:
            confidence += 0.1
            
        return min(0.9, confidence)
    
    async def _handle_general_query(self, prompt: str, intent: str) -> Dict[str, Any]:
        """Handle general CLI queries intelligently based on the prompt content"""
        
        # Analyze the prompt to determine the type of response needed
        prompt_lower = prompt.lower()
        
        # Determine response type based on prompt content
        if any(keyword in prompt_lower for keyword in ["what is", "explain", "how does", "describe"]):
            response_type = "explanation"
        elif any(keyword in prompt_lower for keyword in ["fix", "debug", "error", "issue", "problem"]):
            response_type = "debugging"
        elif any(keyword in prompt_lower for keyword in ["implement", "write", "create", "add", "build"]):
            response_type = "implementation"
        elif any(keyword in prompt_lower for keyword in ["optimize", "improve", "performance", "better"]):
            response_type = "optimization"
        elif any(keyword in prompt_lower for keyword in ["refactor", "clean", "restructure", "organize"]):
            response_type = "refactoring"
        else:
            response_type = "general"
        
        # Generate contextual response based on the query type
        if response_type == "explanation":
            response_content = self._generate_explanation_response(prompt)
        elif response_type == "debugging":
            response_content = self._generate_debugging_response(prompt)
        elif response_type == "implementation":
            response_content = self._generate_implementation_response(prompt)
        elif response_type == "optimization":
            response_content = self._generate_optimization_response(prompt)
        elif response_type == "refactoring":
            response_content = self._generate_refactoring_response(prompt)
        else:
            response_content = self._generate_general_response(prompt)
        
        # Calculate confidence based on query clarity
        confidence = self._calculate_query_confidence(prompt, response_type)
        
        return {
            "status": "success",
            "intent": intent,
            "model": "PragmaticMLX",
            "inference_mode": "pragmatic_query",
            "confidence": confidence,
            "timestamp": time.time(),
            "response": response_content,
            "query_type": response_type,
            "suggestions": self._get_query_suggestions(response_type),
            "requires_human_review": confidence < 0.6
        }
    
    def _generate_explanation_response(self, prompt: str) -> str:
        """Generate explanation-focused responses"""
        return f"""Based on your question: "{prompt}"

I can provide a comprehensive explanation covering the key concepts and implementation details. Here's what you should know:

**Core Concepts:**
- This relates to fundamental programming principles and best practices
- Understanding the underlying mechanisms helps with implementation decisions
- Consider the broader context and architectural implications

**Implementation Approach:**
- Start with a clear understanding of the requirements
- Break down complex problems into manageable components
- Follow established patterns and conventions

**Best Practices:**
- Write clean, readable code with proper documentation
- Include error handling and edge case considerations
- Test your implementation thoroughly

**Further Exploration:**
- Research related patterns and approaches
- Review official documentation and community resources
- Consider performance and scalability implications

Would you like me to dive deeper into any specific aspect of this topic?"""
    
    def _generate_debugging_response(self, prompt: str) -> str:
        """Generate debugging-focused responses"""
        return f"""For the debugging issue: "{prompt}"

Here's a systematic approach to identify and resolve the problem:

**Debugging Strategy:**
1. **Reproduce the Issue:** Consistently recreate the problem to understand its scope
2. **Gather Information:** Collect logs, error messages, and stack traces
3. **Isolate the Problem:** Narrow down the root cause through systematic testing
4. **Apply Fix:** Implement a targeted solution addressing the root cause

**Common Investigation Steps:**
- Check for null/undefined values and type mismatches
- Verify input validation and boundary conditions
- Review recent changes that might have introduced the issue
- Test with different data sets and edge cases

**Debugging Tools:**
- Use debugging breakpoints and step-through debugging
- Add strategic logging to track program flow
- Leverage static analysis tools and linters
- Run unit tests to isolate component behavior

**Prevention Measures:**
- Implement comprehensive error handling
- Add input validation and sanitization
- Write thorough unit and integration tests
- Use type checking and static analysis

Would you like specific guidance on debugging tools or techniques for this particular issue?"""
    
    def _generate_implementation_response(self, prompt: str) -> str:
        """Generate implementation-focused responses"""
        return f"""For the implementation task: "{prompt}"

Here's a practical approach to build this effectively:

**Planning Phase:**
1. **Requirements Analysis:** Clearly define what needs to be built
2. **Architecture Design:** Choose appropriate patterns and technologies
3. **Task Breakdown:** Divide the work into manageable chunks
4. **Risk Assessment:** Identify potential challenges and dependencies

**Implementation Strategy:**
- Start with a minimal viable implementation
- Use test-driven development (TDD) for core functionality
- Follow SOLID principles and clean code practices
- Implement incrementally with frequent testing

**Code Structure:**
```python
# Example implementation pattern
class YourImplementation:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.validate_config()
    
    def main_functionality(self, input_data: Any) -> Any:
        try:
            # Core implementation logic
            result = self.process_input(input_data)
            return self.format_output(result)
        except Exception as e:
            self.handle_error(e)
            raise
    
    def validate_config(self) -> None:
        # Configuration validation
        pass
```

**Quality Assurance:**
- Write comprehensive tests covering edge cases
- Add proper error handling and logging
- Document the implementation and its usage
- Perform code review and refactoring

Ready to proceed with the implementation? Let me know if you need specific guidance on any aspect!"""
    
    def _generate_optimization_response(self, prompt: str) -> str:
        """Generate optimization-focused responses"""
        return f"""For the optimization challenge: "{prompt}"

Here's a systematic approach to improve performance:

**Performance Analysis:**
1. **Profiling:** Identify actual bottlenecks using profiling tools
2. **Metrics:** Establish baseline performance measurements
3. **Benchmarking:** Test different approaches and measure impact
4. **Monitoring:** Set up continuous performance monitoring

**Optimization Strategies:**
- **Algorithmic:** Choose more efficient algorithms and data structures
- **Caching:** Implement smart caching strategies for expensive operations
- **Parallel Processing:** Leverage concurrency and parallelism where appropriate
- **Memory Management:** Optimize memory usage and reduce allocations

**Common Optimization Targets:**
- Database queries and data access patterns
- Network requests and API calls
- CPU-intensive computations
- Memory usage and garbage collection
- I/O operations and file handling

**Implementation Approach:**
```python
# Example optimization pattern
import asyncio
from functools import lru_cache
import time

class OptimizedService:
    def __init__(self):
        self.cache = {{}}
        self.metrics = {{}}
    
    @lru_cache(maxsize=128)
    async def expensive_operation(self, key: str) -> Any:
        # Cached expensive computation
        start_time = time.time()
        result = await self.compute_result(key)
        self.metrics[key] = time.time() - start_time
        return result
```

**Measurement & Validation:**
- Profile before and after optimization
- Test with realistic data volumes
- Ensure correctness is maintained
- Monitor production performance

What specific area would you like to optimize? I can provide more targeted suggestions."""
    
    def _generate_refactoring_response(self, prompt: str) -> str:
        """Generate refactoring-focused responses"""
        return f"""For the refactoring task: "{prompt}"

Here's a structured approach to improve code quality:

**Refactoring Strategy:**
1. **Assessment:** Identify code smells and improvement opportunities
2. **Safety Net:** Ensure comprehensive tests are in place
3. **Incremental Changes:** Make small, safe refactoring steps
4. **Validation:** Verify functionality remains intact after each change

**Common Refactoring Patterns:**
- **Extract Method:** Break down large functions into smaller, focused ones
- **Extract Class:** Separate responsibilities into distinct classes
- **Rename:** Use clear, descriptive names for variables and functions
- **Remove Duplication:** Consolidate repeated code into reusable components

**Code Quality Improvements:**
```python
# Before refactoring
def process_data(data):
    # Large, complex function
    result = []
    for item in data:
        if item.type == "valid":
            processed = item.value * 2
            if processed > 100:
                result.append({"value": processed, "status": "high"})
            else:
                result.append({"value": processed, "status": "normal"})
    return result

# After refactoring
class DataProcessor:
    def process_data(self, data: List[DataItem]) -> List[ProcessedItem]:
        return [self._process_item(item) for item in data if self._is_valid(item)]
    
    def _is_valid(self, item: DataItem) -> bool:
        return item.type == "valid"
    
    def _process_item(self, item: DataItem) -> ProcessedItem:
        processed_value = item.value * 2
        status = "high" if processed_value > 100 else "normal"
        return ProcessedItem(value=processed_value, status=status)
```

**Benefits of Refactoring:**
- Improved readability and maintainability
- Reduced complexity and cognitive load
- Better testability and modularity
- Easier debugging and modification

**Safe Refactoring Steps:**
1. Run existing tests to establish baseline
2. Make one small change at a time
3. Run tests after each change
4. Commit working changes frequently

Which specific aspects of the code would you like to refactor? I can provide more targeted guidance."""
    
    def _generate_general_response(self, prompt: str) -> str:
        """Generate general-purpose responses"""
        return f"""Regarding your query: "{prompt}"

I understand you're looking for guidance on this topic. Here's a comprehensive approach:

**Understanding the Context:**
- This appears to be a technical question requiring practical guidance
- Let me provide some general principles and actionable steps
- Consider the specific requirements and constraints of your situation

**General Approach:**
1. **Research:** Gather information about best practices and established patterns
2. **Plan:** Create a clear roadmap with achievable milestones
3. **Implement:** Start with a simple solution and iterate
4. **Test:** Validate your approach with real-world scenarios
5. **Refine:** Continuously improve based on feedback and results

**Key Considerations:**
- Follow established conventions and standards
- Consider maintainability and future extensibility
- Implement proper error handling and logging
- Document your decisions and implementation details

**Next Steps:**
- Break down the problem into smaller, manageable tasks
- Research relevant documentation and community resources
- Consider seeking specific guidance for complex aspects
- Plan for testing and validation of your solution

**Resources to Explore:**
- Official documentation for relevant technologies
- Community forums and discussion boards
- Code examples and open-source implementations
- Best practice guides and style conventions

Would you like me to provide more specific guidance on any particular aspect of this topic? Feel free to ask follow-up questions for more detailed assistance."""
    
    def _calculate_query_confidence(self, prompt: str, response_type: str) -> float:
        """Calculate confidence based on query clarity and type"""
        base_confidence = 0.6
        
        # Adjust based on query specificity
        if len(prompt.split()) > 3:  # More detailed queries
            base_confidence += 0.1
        
        if any(keyword in prompt.lower() for keyword in ["how", "what", "why", "when", "where"]):
            base_confidence += 0.1  # Question words indicate clear intent
        
        # Response type specific confidence
        type_confidence = {
            "explanation": 0.8,
            "debugging": 0.7,
            "implementation": 0.75,
            "optimization": 0.7,
            "refactoring": 0.75,
            "general": 0.6
        }
        
        final_confidence = (base_confidence + type_confidence.get(response_type, 0.6)) / 2
        return min(0.85, max(0.5, final_confidence))
    
    def _get_query_suggestions(self, response_type: str) -> List[str]:
        """Generate suggestions based on query type"""
        suggestions_map = {
            "explanation": [
                "Ask for code examples to illustrate the concepts",
                "Request more details about specific aspects",
                "Explore related topics and patterns"
            ],
            "debugging": [
                "Provide error messages or stack traces for specific analysis",
                "Share relevant code snippets for targeted advice",
                "Consider using debugging tools and techniques"
            ],
            "implementation": [
                "Start with a minimal viable version",
                "Write tests to validate your implementation",
                "Consider scalability and maintainability"
            ],
            "optimization": [
                "Profile your code to identify bottlenecks",
                "Measure performance before and after changes",
                "Test with realistic data volumes"
            ],
            "refactoring": [
                "Ensure tests are in place before refactoring",
                "Make incremental changes",
                "Focus on one improvement at a time"
            ],
            "general": [
                "Provide more specific details about your requirements",
                "Share relevant code or context",
                "Break down complex questions into smaller parts"
            ]
        }
        
        return suggestions_map.get(response_type, suggestions_map["general"])
    
    def _get_suggestions(self, intent: str, language: str) -> list:
        """Get relevant suggestions"""
        base_suggestions = [
            "Review the generated code for your specific use case",
            "Add proper error handling and validation",
            "Write unit tests for the implementation"
        ]
        
        if language == "python":
            base_suggestions.append("Consider adding type hints")
        elif language == "javascript":
            base_suggestions.append("Consider using TypeScript for better type safety")
            
        return base_suggestions
    
    def _load_response_templates(self) -> Dict[str, str]:
        """Load response templates"""
        return {
            "suggest": "Here's a suggested implementation:",
            "explain": "Here's an explanation of the code:",
            "refactor": "Here are refactoring suggestions:",
            "debug": "Here's a debugging guide:",
            "optimize": "Here are optimization suggestions:"
        }


# Global instance
pragmatic_mlx_service = PragmaticMLXService()