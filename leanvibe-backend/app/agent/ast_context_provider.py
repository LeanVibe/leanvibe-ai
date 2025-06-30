"""
AST Context Provider for L3 Agent

Provides rich AST context to L3 agent for intelligent code suggestions.
"""

import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..models.ast_models import Symbol, SymbolType
from ..services.ast_service import ast_service
from ..services.graph_service import graph_service
from ..services.project_indexer import project_indexer

logger = logging.getLogger(__name__)


class ASTContextProvider:
    """
    Provides comprehensive AST context to L3 agent for code suggestions

    This class bridges the sophisticated AST analysis infrastructure
    to the L3 agent, enabling contextually aware code assistance.
    """

    def __init__(self):
        self.last_context_cache = {}
        self.cache_timeout = 60  # 1 minute cache for performance

    async def get_file_context(
        self, file_path: str, cursor_position: int = 0
    ) -> Dict[str, Any]:
        """
        Get comprehensive context for a file

        Args:
            file_path: Path to the file being analyzed
            cursor_position: Character position of cursor for context-specific analysis

        Returns:
            Rich context dictionary with symbols, dependencies, complexity, etc.
        """
        try:
            # Check cache first
            cache_key = f"{file_path}:{cursor_position}"
            if cache_key in self.last_context_cache:
                cached_time, cached_context = self.last_context_cache[cache_key]
                if time.time() - cached_time < self.cache_timeout:
                    logger.debug(f"Using cached context for {file_path}")
                    return cached_context

            logger.info(
                f"Generating AST context for {file_path} at position {cursor_position}"
            )

            # Get file analysis from AST service
            file_analysis = await ast_service.analyze_file(file_path)
            if not file_analysis:
                return self._create_minimal_context(file_path, "File analysis failed")

            # Get project-wide context if available
            project_context = await self._get_project_context(file_path)

            # Get symbol at cursor position
            current_symbol = await self._get_symbol_at_position(
                file_path, cursor_position
            )

            # Get related symbols and dependencies
            related_context = await self._get_related_context(file_path, current_symbol)

            # Build comprehensive context
            context = {
                "file_path": file_path,
                "file_name": Path(file_path).name,
                "cursor_position": cursor_position,
                "language": file_analysis.language,
                "timestamp": time.time(),
                # File-level analysis
                "file_analysis": {
                    "symbols": [self._symbol_to_dict(s) for s in file_analysis.symbols],
                    "imports": [
                        self._dependency_to_dict(d) for d in file_analysis.dependencies
                    ],
                    "complexity": {
                        "cyclomatic": file_analysis.complexity.cyclomatic_complexity,
                        "functions": file_analysis.complexity.number_of_functions,
                        "classes": file_analysis.complexity.number_of_classes,
                        "lines": file_analysis.complexity.lines_of_code,
                    },
                    "syntax_errors": file_analysis.syntax_errors,
                },
                # Current context
                "current_symbol": (
                    self._symbol_to_dict(current_symbol) if current_symbol else None
                ),
                "surrounding_context": await self._get_surrounding_context(
                    file_path, cursor_position
                ),
                # Project context
                "project_context": project_context,
                # Related context
                "related_symbols": related_context.get("symbols", []),
                "dependencies": related_context.get("dependencies", []),
                "references": related_context.get("references", []),
                # Architecture context
                "architecture_insights": await self._get_architecture_context(
                    file_path
                ),
                # Suggestions context
                "suggestion_context": await self._build_suggestion_context(
                    file_path, current_symbol
                ),
            }

            # Cache the result
            self.last_context_cache[cache_key] = (time.time(), context)

            # Limit cache size
            if len(self.last_context_cache) > 10:
                oldest_key = min(
                    self.last_context_cache.keys(),
                    key=lambda k: self.last_context_cache[k][0],
                )
                del self.last_context_cache[oldest_key]

            logger.info(
                f"Generated AST context with {len(context['file_analysis']['symbols'])} symbols"
            )
            return context

        except Exception as e:
            logger.error(f"Error generating file context for {file_path}: {e}")
            return self._create_minimal_context(file_path, f"Error: {str(e)}")

    async def get_symbol_context(
        self, symbol_id: str, file_path: str
    ) -> Dict[str, Any]:
        """
        Get context for specific symbol

        Args:
            symbol_id: Unique identifier of the symbol
            file_path: File containing the symbol

        Returns:
            Symbol-specific context with definitions, usages, relationships
        """
        try:
            logger.info(f"Getting symbol context for {symbol_id} in {file_path}")

            # Get symbol definition
            symbol = await ast_service.get_symbol(symbol_id)
            if not symbol:
                return {"error": f"Symbol {symbol_id} not found"}

            # Get symbol references
            references = await project_indexer.find_references_by_symbol_id(symbol_id)

            # Get related symbols from graph database
            related_symbols = []
            if graph_service.initialized:
                related_symbols = await graph_service.get_related_symbols(symbol_id)

            # Build symbol context
            context = {
                "symbol_id": symbol_id,
                "symbol": self._symbol_to_dict(symbol),
                "file_path": file_path,
                "timestamp": time.time(),
                # References and usage
                "references": [self._reference_to_dict(ref) for ref in references],
                "usage_count": len(references),
                "definition_count": len(
                    [ref for ref in references if ref.reference_type == "definition"]
                ),
                # Relationships
                "related_symbols": [self._symbol_to_dict(s) for s in related_symbols],
                # Context analysis
                "importance_score": self._calculate_symbol_importance(
                    symbol, references
                ),
                "change_impact": await self._analyze_symbol_impact(symbol_id),
                # Suggestions
                "suggestions": await self._generate_symbol_suggestions(
                    symbol, references
                ),
            }

            return context

        except Exception as e:
            logger.error(f"Error getting symbol context for {symbol_id}: {e}")
            return {"error": f"Symbol context failed: {str(e)}"}

    async def get_completion_context(
        self, file_path: str, cursor_position: int, intent: str = "suggest"
    ) -> Dict[str, Any]:
        """
        Get optimized context for code completion

        Args:
            file_path: File being edited
            cursor_position: Current cursor position
            intent: Type of completion (suggest, explain, refactor, etc.)

        Returns:
            Optimized context for code completion
        """
        try:
            logger.info(
                f"Building completion context for {intent} at {file_path}:{cursor_position}"
            )

            # Get base file context
            base_context = await self.get_file_context(file_path, cursor_position)

            # Optimize for completion based on intent
            completion_context = {
                "intent": intent,
                "file_path": file_path,
                "cursor_position": cursor_position,
                "timestamp": time.time(),
                # Essential context (always include)
                "current_file": {
                    "name": Path(file_path).name,
                    "language": base_context.get("language", "unknown"),
                    "symbol_count": len(
                        base_context.get("file_analysis", {}).get("symbols", [])
                    ),
                    "complexity": base_context.get("file_analysis", {}).get(
                        "complexity", {}
                    ),
                },
                # Current context (cursor-specific)
                "current_symbol": base_context.get("current_symbol"),
                "surrounding_context": base_context.get("surrounding_context"),
                # Intent-specific context
                "relevant_context": await self._get_intent_specific_context(
                    base_context, intent
                ),
                # Project awareness (summarized)
                "project_summary": self._summarize_project_context(
                    base_context.get("project_context", {})
                ),
                # Completion hints
                "completion_hints": await self._generate_completion_hints(
                    file_path, cursor_position, intent
                ),
            }

            logger.info(
                f"Built completion context for {intent} with {len(completion_context)} fields"
            )
            return completion_context

        except Exception as e:
            logger.error(f"Error building completion context: {e}")
            return {"error": f"Completion context failed: {str(e)}", "intent": intent}

    def _create_minimal_context(
        self, file_path: str, error_message: str
    ) -> Dict[str, Any]:
        """Create minimal context when full analysis fails"""
        return {
            "file_path": file_path,
            "file_name": Path(file_path).name,
            "language": self._detect_language_from_extension(file_path),
            "error": error_message,
            "timestamp": time.time(),
            "minimal": True,
        }

    def _detect_language_from_extension(self, file_path: str) -> str:
        """Simple language detection from file extension"""
        ext = Path(file_path).suffix.lower()
        return {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".swift": "swift",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
        }.get(ext, "unknown")

    def _symbol_to_dict(self, symbol: Symbol) -> Dict[str, Any]:
        """Convert Symbol object to dictionary"""
        if not symbol:
            return None
        return {
            "id": symbol.id,
            "name": symbol.name,
            "type": symbol.symbol_type.value if symbol.symbol_type else "unknown",
            "file_path": symbol.file_path,
            "line_start": symbol.line_start,
            "line_end": symbol.line_end,
            "docstring": symbol.docstring,
        }

    def _dependency_to_dict(self, dependency) -> Dict[str, Any]:
        """Convert dependency to dictionary"""
        return {
            "module_name": dependency.module_name,
            "is_external": dependency.is_external,
            "source_file": dependency.source_file,
            "target_file": dependency.target_file,
        }

    def _reference_to_dict(self, reference) -> Dict[str, Any]:
        """Convert reference to dictionary"""
        return {
            "file_path": reference.file_path,
            "line_number": reference.line_number,
            "reference_type": reference.reference_type,
            "context": reference.context,
        }

    async def _get_project_context(self, file_path: str) -> Dict[str, Any]:
        """Get project-wide context"""
        try:
            # This would use the existing project indexer
            # For now, return basic structure
            return {
                "workspace_path": str(Path(file_path).parent),
                "total_files": 0,
                "supported_languages": [],
                "key_components": [],
            }
        except FileNotFoundError as e:
            logger.error(f"File not found for project context: {file_path}")
            return {"error": "file_not_found", "file_path": file_path}
        except PermissionError as e:
            logger.error(f"Permission denied accessing {file_path}: {e}")
            return {"error": "permission_denied", "file_path": file_path}
        except Exception as e:
            logger.error(f"Unexpected error getting project context for {file_path}: {e}")
            return {"error": "analysis_failed", "file_path": file_path}

    async def _get_symbol_at_position(
        self, file_path: str, cursor_position: int
    ) -> Optional[Symbol]:
        """Get symbol at specific cursor position"""
        try:
            # This would analyze the file to find symbol at cursor
            # For now, return None - implement with real cursor analysis
            return None
        except FileNotFoundError as e:
            logger.error(f"File not found for symbol analysis: {file_path}")
            return None
        except Exception as e:
            logger.error(f"Error analyzing symbol at position {cursor_position} in {file_path}: {e}")
            return None

    async def _get_related_context(
        self, file_path: str, current_symbol: Optional[Symbol]
    ) -> Dict[str, Any]:
        """Get related symbols and dependencies"""
        return {"symbols": [], "dependencies": [], "references": []}

    async def _get_surrounding_context(
        self, file_path: str, cursor_position: int
    ) -> Dict[str, Any]:
        """Get surrounding code context"""
        try:
            # Read file content around cursor position
            with open(file_path, "r") as f:
                content = f.read()

            # Simple implementation - get surrounding lines
            lines = content.split("\n")
            char_pos = 0
            target_line = 0

            for i, line in enumerate(lines):
                if char_pos + len(line) >= cursor_position:
                    target_line = i
                    break
                char_pos += len(line) + 1  # +1 for newline

            # Get context around target line
            start_line = max(0, target_line - 5)
            end_line = min(len(lines), target_line + 6)

            return {
                "target_line": target_line,
                "line_content": lines[target_line] if target_line < len(lines) else "",
                "surrounding_lines": lines[start_line:end_line],
                "context_size": end_line - start_line,
            }
        except FileNotFoundError as e:
            logger.error(f"File not found for surrounding context: {file_path}")
            return {"error": "file_not_found", "file_path": file_path}
        except PermissionError as e:
            logger.error(f"Permission denied reading {file_path}: {e}")
            return {"error": "permission_denied", "file_path": file_path}
        except UnicodeDecodeError as e:
            logger.error(f"Encoding error reading {file_path}: {e}")
            return {"error": "encoding_error", "file_path": file_path}
        except Exception as e:
            logger.error(f"Error reading surrounding context from {file_path}: {e}")
            return {"error": "read_failed", "file_path": file_path}

    async def _get_architecture_context(self, file_path: str) -> Dict[str, Any]:
        """Get architecture insights for the file"""
        return {"patterns": [], "design_principles": [], "suggestions": []}

    async def _build_suggestion_context(
        self, file_path: str, current_symbol: Optional[Symbol]
    ) -> Dict[str, Any]:
        """Build context optimized for generating suggestions"""
        return {
            "completion_type": "general",
            "confidence_factors": [],
            "context_strength": 0.5,
        }

    def _calculate_symbol_importance(self, symbol: Symbol, references: List) -> float:
        """Calculate importance score for symbol"""
        base_score = 0.5

        # More references = higher importance
        if references:
            base_score += min(0.3, len(references) * 0.02)

        # Function/class symbols more important than variables
        if symbol.symbol_type in [SymbolType.FUNCTION, SymbolType.CLASS]:
            base_score += 0.1

        return min(1.0, base_score)

    async def _analyze_symbol_impact(self, symbol_id: str) -> Dict[str, Any]:
        """Analyze potential impact of changing symbol"""
        return {"risk_level": "low", "affected_files": [], "affected_symbols": []}

    async def _generate_symbol_suggestions(
        self, symbol: Symbol, references: List
    ) -> List[str]:
        """Generate suggestions for symbol improvement"""
        suggestions = []

        if len(references) > 10:
            suggestions.append("High usage symbol - consider documentation")

        if symbol.symbol_type == SymbolType.FUNCTION and not symbol.docstring:
            suggestions.append("Consider adding docstring for better maintainability")

        return suggestions

    async def _get_intent_specific_context(
        self, base_context: Dict[str, Any], intent: str
    ) -> Dict[str, Any]:
        """Get context optimized for specific intent"""
        if intent == "suggest":
            return {
                "focus": "code_completion",
                "relevant_symbols": base_context.get("file_analysis", {}).get(
                    "symbols", []
                )[:5],
                "patterns": [],
            }
        elif intent == "explain":
            return {
                "focus": "code_understanding",
                "complexity": base_context.get("file_analysis", {}).get(
                    "complexity", {}
                ),
                "architecture": base_context.get("architecture_insights", {}),
            }
        elif intent == "refactor":
            return {
                "focus": "code_improvement",
                "complexity": base_context.get("file_analysis", {}).get(
                    "complexity", {}
                ),
                "suggestions": base_context.get("suggestion_context", {}),
            }
        else:
            return {"focus": "general"}

    def _summarize_project_context(
        self, project_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Summarize project context for completion"""
        return {
            "workspace": project_context.get("workspace_path", "unknown"),
            "file_count": project_context.get("total_files", 0),
            "languages": project_context.get("supported_languages", []),
        }

    async def _generate_completion_hints(
        self, file_path: str, cursor_position: int, intent: str
    ) -> List[str]:
        """Generate hints for code completion"""
        hints = []

        language = self._detect_language_from_extension(file_path)

        if intent == "suggest":
            if language == "python":
                hints.extend(
                    ["Consider type hints", "Follow PEP 8 style", "Add docstrings"]
                )
            elif language == "javascript":
                hints.extend(
                    ["Use const/let", "Consider async/await", "Add JSDoc comments"]
                )

        return hints
