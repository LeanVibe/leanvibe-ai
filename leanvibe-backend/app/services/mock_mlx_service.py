"""
Phase 2.3: Mock MLX Service for L3 Agent Integration

Sophisticated mock service that simulates MLX responses with contextually
appropriate suggestions based on AST context from L3 agent.

DEPRECATED: Use unified_mlx_service with MOCK strategy instead.
"""

import asyncio
import logging
import time
import warnings
from typing import Any, AsyncGenerator, Dict, List, Optional

logger = logging.getLogger(__name__)

# DEPRECATION WARNING
warnings.warn(
    "mock_mlx_service.py is deprecated. Use unified_mlx_service with MOCK strategy instead. "
    "This module will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2
)


class MockMLXService:
    """
    Mock MLX service that provides contextually appropriate responses

    This service simulates real MLX inference while validating the entire
    workflow from L3 agent context to code completion responses.
    """

    def __init__(self):
        self.model_name = "mlx-community/Qwen2.5-Coder-32B-Instruct"
        self.max_tokens = 1024
        self.temperature = 0.2
        self.is_initialized = False
        self.response_templates = self._load_response_templates()
        self.context_patterns = self._load_context_patterns()

    async def initialize(self) -> bool:
        """Initialize mock MLX service"""
        try:
            logger.info("Initializing Mock MLX Service for L3 Agent integration...")
            await asyncio.sleep(0.1)  # Simulate initialization
            self.is_initialized = True
            logger.info("Mock MLX Service initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Mock MLX Service: {e}")
            return False

    async def generate_code_completion(
        self, context: Dict[str, Any], intent: str = "suggest"
    ) -> Dict[str, Any]:
        """
        Generate code completion based on AST context and intent

        Args:
            context: Rich AST context from L3 agent
            intent: Type of completion (suggest, explain, refactor, debug, optimize)

        Returns:
            Structured completion response with confidence scoring
        """
        try:
            logger.info(f"Generating {intent} completion with AST context")

            # Simulate processing time
            await asyncio.sleep(0.2)

            # Extract key context elements
            file_path = context.get("file_path", "")
            language = context.get("current_file", {}).get("language", "unknown")
            current_symbol = context.get("current_symbol")
            surrounding_context = context.get("surrounding_context", {})
            completion_hints = context.get("completion_hints", [])

            # Generate intent-specific response
            if intent == "suggest":
                response = await self._generate_code_suggestion(
                    language, current_symbol, surrounding_context, completion_hints
                )
            elif intent == "explain":
                response = await self._generate_code_explanation(
                    language, current_symbol, surrounding_context
                )
            elif intent == "refactor":
                response = await self._generate_refactoring_suggestion(
                    language, current_symbol, surrounding_context
                )
            elif intent == "debug":
                response = await self._generate_debug_analysis(
                    language, current_symbol, surrounding_context
                )
            elif intent == "optimize":
                response = await self._generate_optimization_suggestion(
                    language, current_symbol, surrounding_context
                )
            else:
                response = await self._generate_general_assistance(
                    language, current_symbol, surrounding_context
                )

            # Calculate confidence based on context richness
            confidence = self._calculate_completion_confidence(context, intent)

            # Build structured response
            completion_response = {
                "status": "success",
                "intent": intent,
                "model": self.model_name,
                "language": language,
                "confidence": confidence,
                "timestamp": time.time(),
                "response": response,
                "context_used": {
                    "file_path": file_path,
                    "has_symbol_context": current_symbol is not None,
                    "has_surrounding_context": bool(surrounding_context),
                    "hints_count": len(completion_hints),
                    "language_detected": language,
                },
                "suggestions": self._generate_follow_up_suggestions(intent, language),
                "requires_human_review": confidence < 0.7,
            }

            logger.info(
                f"Generated {intent} completion with {confidence:.2f} confidence"
            )
            return completion_response

        except Exception as e:
            logger.error(f"Error generating completion: {e}")
            return {
                "status": "error",
                "error": f"Completion generation failed: {str(e)}",
                "confidence": 0.0,
            }

    async def generate_streaming_completion(
        self, context: Dict[str, Any], intent: str = "suggest"
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generate streaming code completion for real-time feedback

        Args:
            context: Rich AST context from L3 agent
            intent: Type of completion

        Yields:
            Streaming completion chunks
        """
        try:
            logger.info(f"Starting streaming {intent} completion")

            # Get full completion
            full_response = await self.generate_code_completion(context, intent)

            if full_response["status"] != "success":
                yield full_response
                return

            response_text = full_response["response"]

            # Stream response in chunks
            chunk_size = 20
            words = response_text.split()

            for i in range(0, len(words), chunk_size):
                chunk_words = words[i : i + chunk_size]
                chunk_text = " ".join(chunk_words)

                yield {
                    "status": "streaming",
                    "chunk": chunk_text,
                    "progress": min(1.0, (i + chunk_size) / len(words)),
                    "is_final": i + chunk_size >= len(words),
                }

                await asyncio.sleep(0.1)  # Simulate streaming delay

            # Send final metadata
            yield {
                "status": "complete",
                "metadata": {
                    "confidence": full_response["confidence"],
                    "suggestions": full_response["suggestions"],
                    "requires_human_review": full_response["requires_human_review"],
                },
            }

        except Exception as e:
            logger.error(f"Error in streaming completion: {e}")
            yield {"status": "error", "error": f"Streaming failed: {str(e)}"}

    async def _generate_code_suggestion(
        self,
        language: str,
        current_symbol: Optional[Dict[str, Any]],
        surrounding_context: Dict[str, Any],
        hints: List[str],
    ) -> str:
        """Generate code suggestions based on context"""

        if language == "python":
            if current_symbol and current_symbol.get("type") == "function":
                return f"""Based on the function '{current_symbol.get("name", "unknown")}', here are some suggestions:

1. **Type Hints**: Add type annotations for better code clarity:
   ```python
   def {current_symbol.get("name", "function_name")}(param: str) -> str:
       # Your implementation
   ```

2. **Docstring**: Consider adding a docstring:
   ```python
   def {current_symbol.get("name", "function_name")}():
       \"\"\"
       Brief description of what this function does.
       
       Returns:
           Description of return value
       \"\"\"
   ```

3. **Error Handling**: Add appropriate error handling if needed.

Context hints: {', '.join(hints) if hints else 'Consider following PEP 8 guidelines'}"""

            else:
                return """Python code suggestions:

1. **Import Organization**: Group imports (standard library, third-party, local)
2. **Variable Naming**: Use descriptive snake_case names
3. **List Comprehensions**: Consider using them for simple transformations
4. **Context Managers**: Use 'with' statements for resource management
5. **Type Hints**: Add type annotations for better code documentation

Example:
```python
from typing import List, Optional

def process_items(items: List[str]) -> Optional[str]:
    \"\"\"Process a list of items and return the first valid one.\"\"\"
    return next((item for item in items if item.strip()), None)
```"""

        elif language == "javascript":
            return """JavaScript/TypeScript suggestions:

1. **Modern Syntax**: Use const/let instead of var
2. **Arrow Functions**: Consider arrow functions for concise code
3. **Async/Await**: Use async/await for better promise handling
4. **Destructuring**: Use object/array destructuring where appropriate
5. **Template Literals**: Use template literals for string interpolation

Example:
```javascript
const processData = async (data) => {
    const { items, meta } = data;
    return items.map(item => ({
        ...item,
        processed: true
    }));
};
```"""

        elif language == "swift":
            return """Swift code suggestions:

1. **Type Safety**: Leverage Swift's strong type system
2. **Optionals**: Use optionals properly with nil-coalescing
3. **Extensions**: Use extensions to organize code
4. **Protocols**: Define protocols for better abstraction
5. **Guards**: Use guard statements for early returns

Example:
```swift
func processUser(_ user: User?) -> String {
    guard let user = user else { return "No user" }
    return "Hello, \\(user.name)"
}
```"""

        else:
            return f"""General {language} suggestions:

1. **Code Organization**: Keep functions small and focused
2. **Naming**: Use descriptive and consistent naming
3. **Comments**: Add comments for complex logic
4. **Error Handling**: Handle edge cases appropriately
5. **Testing**: Consider writing unit tests

The code appears to be well-structured. Consider refactoring if functions become too large."""

    async def _generate_code_explanation(
        self,
        language: str,
        current_symbol: Optional[Dict[str, Any]],
        surrounding_context: Dict[str, Any],
    ) -> str:
        """Generate code explanations"""

        if current_symbol:
            symbol_name = current_symbol.get("name", "unknown")
            symbol_type = current_symbol.get("type", "unknown")

            return f"""Code Explanation for {symbol_type} '{symbol_name}':

**Purpose**: This {symbol_type} appears to be part of a {language} codebase.

**Context Analysis**:
- Symbol Type: {symbol_type.title()}
- Location: Lines {current_symbol.get("line_start", "?")} - {current_symbol.get("line_end", "?")}
- Language: {language.title()}

**Functionality**:
{self._get_functionality_description(symbol_type, language)}

**Best Practices**:
{self._get_best_practices(symbol_type, language)}

**Potential Improvements**:
- Consider adding documentation if not present
- Ensure proper error handling
- Follow language-specific conventions"""

        else:
            return f"""Code Section Explanation:

This appears to be a {language} code section. Based on the surrounding context:

**Structure Analysis**:
- Language: {language.title()}
- Context: {surrounding_context.get("context_size", 0)} lines of surrounding code

**Common Patterns**:
{self._get_language_patterns(language)}

**Recommendations**:
- Maintain consistent code style
- Add appropriate comments for complex logic
- Consider refactoring if the section becomes too complex"""

    async def _generate_refactoring_suggestion(
        self,
        language: str,
        current_symbol: Optional[Dict[str, Any]],
        surrounding_context: Dict[str, Any],
    ) -> str:
        """Generate refactoring suggestions"""

        suggestions = [
            "**Extract Method**: Break down large functions into smaller, focused methods",
            "**Rename Variables**: Use more descriptive names for better readability",
            "**Remove Duplication**: Look for repeated code patterns that can be abstracted",
            "**Simplify Conditionals**: Consider using early returns or guard clauses",
            "**Add Constants**: Replace magic numbers with named constants",
        ]

        if language == "python":
            suggestions.extend(
                [
                    "**Use List Comprehensions**: Replace simple loops with comprehensions",
                    "**Add Type Hints**: Improve code documentation with type annotations",
                    "**Use Context Managers**: Replace try/finally with 'with' statements",
                ]
            )
        elif language == "javascript":
            suggestions.extend(
                [
                    "**Use Arrow Functions**: Simplify function definitions where appropriate",
                    "**Destructuring**: Simplify object/array access",
                    "**Template Literals**: Replace string concatenation",
                ]
            )
        elif language == "swift":
            suggestions.extend(
                [
                    "**Use Guards**: Replace nested if-let with guard statements",
                    "**Protocol Extensions**: Add default implementations",
                    "**Computed Properties**: Replace getter methods with computed properties",
                ]
            )

        return f"""Refactoring Suggestions for {language.title()} Code:

{chr(10).join(f"{i+1}. {suggestion}" for i, suggestion in enumerate(suggestions[:5]))}

**Priority**: Focus on readability and maintainability first, then performance optimizations.

**Testing**: Ensure you have tests in place before refactoring to maintain functionality."""

    async def _generate_debug_analysis(
        self,
        language: str,
        current_symbol: Optional[Dict[str, Any]],
        surrounding_context: Dict[str, Any],
    ) -> str:
        """Generate debug analysis"""

        return f"""Debug Analysis for {language.title()} Code:

**Common Issues to Check**:

1. **Null/Undefined Values**: Check for null pointer exceptions or undefined variables
2. **Type Mismatches**: Verify variable types match expected usage
3. **Boundary Conditions**: Test edge cases (empty arrays, zero values, etc.)
4. **Resource Management**: Ensure proper cleanup of resources
5. **Logic Errors**: Verify conditional statements and loop termination

**Language-Specific Debugging**:
{self._get_debug_tips(language)}

**Debugging Strategy**:
1. Add logging/print statements at key points
2. Use a debugger to step through execution
3. Write unit tests to isolate the issue
4. Check error logs and stack traces
5. Verify input data and assumptions

**Next Steps**:
- Identify the specific error or unexpected behavior
- Create a minimal reproduction case
- Use appropriate debugging tools for {language}"""

    async def _generate_optimization_suggestion(
        self,
        language: str,
        current_symbol: Optional[Dict[str, Any]],
        surrounding_context: Dict[str, Any],
    ) -> str:
        """Generate optimization suggestions"""

        return f"""Performance Optimization for {language.title()} Code:

**General Optimizations**:

1. **Algorithm Complexity**: Review time/space complexity of algorithms
2. **Data Structures**: Choose appropriate data structures for the use case
3. **Caching**: Cache expensive computations or frequently accessed data
4. **Lazy Loading**: Load data only when needed
5. **Memory Management**: Minimize object creation and manage memory efficiently

**Language-Specific Optimizations**:
{self._get_optimization_tips(language)}

**Profiling Strategy**:
1. Measure current performance to establish baseline
2. Identify bottlenecks using profiling tools
3. Optimize the most impactful areas first
4. Verify improvements with benchmarks
5. Monitor production performance

**Trade-offs**:
- Balance performance with code readability
- Consider maintenance costs of optimizations
- Profile in production-like environments"""

    async def _generate_general_assistance(
        self,
        language: str,
        current_symbol: Optional[Dict[str, Any]],
        surrounding_context: Dict[str, Any],
    ) -> str:
        """Generate general assistance"""

        return f"""General Code Assistance for {language.title()}:

**Code Quality Checklist**:
✓ Readable and well-structured code
✓ Appropriate naming conventions
✓ Proper error handling
✓ Adequate documentation
✓ Consistent formatting

**Best Practices**:
- Follow language-specific style guides
- Write self-documenting code
- Add tests for critical functionality
- Use version control effectively
- Regular code reviews

**Resources**:
- Language documentation and style guides
- Static analysis tools and linters
- Testing frameworks
- Code review tools
- Performance profiling tools

**Need Help With**:
- Ask specific questions about implementation
- Request code reviews for critical sections
- Discuss architectural decisions
- Explore alternative approaches"""

    def _calculate_completion_confidence(
        self, context: Dict[str, Any], intent: str
    ) -> float:
        """Calculate confidence score based on context richness"""
        base_confidence = 0.3  # Start lower for unknown contexts

        # Boost confidence based on available context
        if context.get("current_symbol"):
            base_confidence += 0.15

        if context.get("surrounding_context"):
            base_confidence += 0.15

        if context.get("completion_hints"):
            base_confidence += 0.1

        # Language-specific confidence
        language = context.get("current_file", {}).get("language", "unknown")
        if language in ["python", "javascript", "swift"]:
            base_confidence += 0.2
        elif language != "unknown":
            base_confidence += 0.1

        # Intent-specific confidence adjustments
        intent_multiplier = {
            "suggest": 1.0,
            "explain": 1.1,  # Explanations are generally more reliable
            "refactor": 0.9,
            "debug": 0.8,  # Debugging requires more caution
            "optimize": 0.8,  # Optimization requires more caution
        }

        final_confidence = base_confidence * intent_multiplier.get(intent, 0.8)
        return min(0.95, max(0.3, final_confidence))  # Clamp between 0.3 and 0.95

    def _generate_follow_up_suggestions(self, intent: str, language: str) -> List[str]:
        """Generate follow-up action suggestions"""
        suggestions = []

        if intent == "suggest":
            suggestions = [
                "Ask for explanation of suggested patterns",
                "Request refactoring recommendations",
                "Get debugging tips for this code section",
            ]
        elif intent == "explain":
            suggestions = [
                "Request code improvement suggestions",
                "Ask about performance optimization",
                "Get examples of similar patterns",
            ]
        elif intent == "refactor":
            suggestions = [
                "Test the refactored code",
                "Get performance impact analysis",
                "Request additional refactoring opportunities",
            ]
        elif intent == "debug":
            suggestions = [
                "Set up debugging environment",
                "Write unit tests to isolate issues",
                "Profile code for performance bottlenecks",
            ]
        elif intent == "optimize":
            suggestions = [
                "Benchmark current performance",
                "Profile memory usage",
                "Consider alternative algorithms",
            ]

        return suggestions

    def _get_functionality_description(self, symbol_type: str, language: str) -> str:
        """Get functionality description for symbol type"""
        descriptions = {
            "function": f"A {language} function that encapsulates specific functionality and can be called with parameters.",
            "class": f"A {language} class that defines an object template with properties and methods.",
            "method": f"A {language} method that belongs to a class and operates on object instances.",
            "variable": f"A {language} variable that stores data for use within its scope.",
        }
        return descriptions.get(
            symbol_type,
            f"A {language} {symbol_type} that serves a specific purpose in the codebase.",
        )

    def _get_best_practices(self, symbol_type: str, language: str) -> str:
        """Get best practices for symbol type"""
        if symbol_type == "function":
            return "Keep functions small and focused, use descriptive names, add proper documentation"
        elif symbol_type == "class":
            return "Follow single responsibility principle, use composition over inheritance when appropriate"
        elif symbol_type == "method":
            return "Ensure methods operate on instance state, consider static methods for utilities"
        else:
            return "Use descriptive names, maintain appropriate scope, document complex logic"

    def _get_language_patterns(self, language: str) -> str:
        """Get common patterns for language"""
        patterns = {
            "python": "List comprehensions, context managers, decorators, generators",
            "javascript": "Callbacks, promises, async/await, closures, modules",
            "swift": "Optionals, protocols, extensions, computed properties, guards",
        }
        return patterns.get(language, "Language-specific idioms and patterns")

    def _get_debug_tips(self, language: str) -> str:
        """Get debugging tips for language"""
        tips = {
            "python": "Use pdb debugger, print statements, logging module, pytest for testing",
            "javascript": "Use browser dev tools, console.log, debugger statement, Jest for testing",
            "swift": "Use Xcode debugger, print statements, XCTest framework, breakpoints",
        }
        return tips.get(
            language, "Use language-appropriate debugging tools and techniques"
        )

    def _get_optimization_tips(self, language: str) -> str:
        """Get optimization tips for language"""
        tips = {
            "python": "Use list comprehensions, numpy for numerical operations, cProfile for profiling",
            "javascript": "Minimize DOM manipulation, use requestAnimationFrame, avoid memory leaks",
            "swift": "Use value types when appropriate, lazy properties, Instruments for profiling",
        }
        return tips.get(
            language, "Profile first, optimize bottlenecks, measure improvements"
        )

    def _load_response_templates(self) -> Dict[str, str]:
        """Load response templates for different scenarios"""
        return {
            "code_suggestion": "Based on the code context, here are some suggestions...",
            "explanation": "This code section appears to...",
            "refactoring": "Consider the following refactoring opportunities...",
            "debugging": "To debug this issue, check the following...",
            "optimization": "For better performance, consider...",
        }

    def _load_context_patterns(self) -> Dict[str, Any]:
        """Load patterns for context recognition"""
        return {
            "python": {
                "function_patterns": ["def ", "lambda "],
                "class_patterns": ["class "],
                "import_patterns": ["import ", "from "],
            },
            "javascript": {
                "function_patterns": ["function ", "=> ", "const "],
                "class_patterns": ["class "],
                "import_patterns": ["import ", "require("],
            },
            "swift": {
                "function_patterns": ["func "],
                "class_patterns": ["class ", "struct "],
                "import_patterns": ["import "],
            },
        }


# Global mock MLX service instance
mock_mlx_service = MockMLXService()
