"""
AST Intelligence Service

Extracted from enhanced_l3_agent.py to provide focused AST analysis
and code intelligence capabilities following single responsibility principle.
"""

import logging
from typing import Any, Dict, List, Optional
from pathlib import Path

from ..models.ast_models import ProjectContext, ProjectIndex, SymbolType
from .ast_service import ast_service
from .project_indexer import project_indexer
from ..agent.ast_context_provider import ASTContextProvider

logger = logging.getLogger(__name__)


class ASTIntelligenceService:
    """
    Service dedicated to AST-based code analysis and intelligence.
    
    Provides deep code understanding through AST parsing, symbol exploration,
    complexity analysis, and intelligent code completion context.
    """
    
    def __init__(self):
        self.project_index: Optional[ProjectIndex] = None
        self.project_context: Optional[ProjectContext] = None
        self.ast_context_provider: Optional[ASTContextProvider] = None
        self._initialized = False
        
    async def initialize(self, project_root: str) -> bool:
        """Initialize the AST intelligence service for a project"""
        try:
            self.project_context = ProjectContext(project_root=project_root)
            self.ast_context_provider = ASTContextProvider(self.project_context)
            self._initialized = True
            
            # Ensure project is indexed
            await self._ensure_project_indexed()
            
            logger.info(f"AST Intelligence Service initialized for project: {project_root}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize AST Intelligence Service: {e}")
            return False
    
    def get_capabilities(self) -> List[str]:
        """Get list of capabilities provided by this service"""
        return [
            "project_analysis",
            "symbol_exploration", 
            "reference_finding",
            "complexity_analysis",
            "file_context_analysis",
            "completion_context",
            "code_completion_suggestions"
        ]
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the service"""
        return {
            "service": "ast_intelligence",
            "initialized": self._initialized,
            "project_indexed": self.project_index is not None,
            "total_symbols": len(self.project_index.symbols) if self.project_index else 0,
            "total_files": self.project_index.total_files if self.project_index else 0
        }
    
    async def _ensure_project_indexed(self) -> bool:
        """Ensure the project is properly indexed"""
        if not self.project_context:
            return False
            
        try:
            result = await project_indexer.index_project(self.project_context.project_root)
            if result.get("status") == "success":
                self.project_index = result.get("project_index")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to index project: {e}")
            return False
    
    async def analyze_project(self) -> Dict[str, Any]:
        """
        Analyze the entire project and provide comprehensive insights
        
        Extracted from: _analyze_project_tool()
        """
        try:
            # Ensure project is indexed
            indexed = await self._ensure_project_indexed()
            if not indexed or not self.project_index:
                return {
                    "status": "error",
                    "message": "Could not index project for analysis",
                    "confidence": 0.0,
                }

            # Generate comprehensive analysis
            analysis_data = {
                "total_files": self.project_index.total_files,
                "supported_files": self.project_index.supported_files,
                "total_symbols": len(self.project_index.symbols),
                "parsing_errors": self.project_index.parsing_errors,
            }

            # Symbol breakdown
            symbol_breakdown = {}
            for symbol in self.project_index.symbols.values():
                symbol_type = symbol.symbol_type
                symbol_breakdown[symbol_type] = symbol_breakdown.get(symbol_type, 0) + 1

            analysis_data["symbol_breakdown"] = symbol_breakdown

            # Language breakdown
            language_breakdown = {}
            for analysis in self.project_index.files.values():
                lang = analysis.language
                language_breakdown[lang] = language_breakdown.get(lang, 0) + 1

            analysis_data["language_breakdown"] = language_breakdown

            # Complexity analysis
            total_complexity = sum(
                analysis.complexity.cyclomatic_complexity
                for analysis in self.project_index.files.values()
            )
            avg_complexity = total_complexity / max(
                self.project_index.supported_files, 1
            )

            analysis_data["complexity"] = {
                "total": total_complexity,
                "average": avg_complexity,
                "high_complexity_files": [
                    analysis.file_path
                    for analysis in self.project_index.files.values()
                    if analysis.complexity.cyclomatic_complexity > 10
                ][:10]  # Top 10 most complex files
            }

            # Quality metrics
            quality_score = self._calculate_quality_score(analysis_data)
            analysis_data["quality_score"] = quality_score

            # Generate summary
            summary = self._generate_analysis_summary(analysis_data)

            return {
                "status": "success",
                "data": {
                    "analysis": analysis_data,
                    "summary": summary
                },
                "confidence": 0.9,
            }

        except Exception as e:
            logger.error(f"Error in project analysis: {e}")
            return {
                "status": "error",
                "message": f"Analysis failed: {str(e)}",
                "confidence": 0.0,
            }
    
    async def explore_symbols(self, symbol_name: str) -> Dict[str, Any]:
        """
        Explore symbols in the codebase
        
        Extracted from: _explore_symbols_tool()
        """
        try:
            if not self.project_index:
                await self._ensure_project_indexed()
                
            if not self.project_index:
                return {
                    "status": "error",
                    "message": "Project not indexed",
                    "confidence": 0.0,
                }

            # Find matching symbols
            matching_symbols = []
            for symbol in self.project_index.symbols.values():
                if symbol_name.lower() in symbol.name.lower():
                    matching_symbols.append({
                        "name": symbol.name,
                        "type": symbol.symbol_type,
                        "file": symbol.file_path,
                        "line": symbol.line_number,
                        "scope": symbol.parent_scope,
                        "docstring": symbol.docstring
                    })

            if not matching_symbols:
                return {
                    "status": "success",
                    "data": {
                        "symbols": [],
                        "summary": f"No symbols found matching '{symbol_name}'"
                    },
                    "confidence": 0.8,
                }

            # Sort by relevance (exact matches first, then partial)
            matching_symbols.sort(key=lambda s: (
                s["name"].lower() != symbol_name.lower(),  # Exact matches first
                len(s["name"]),  # Shorter names first
                s["name"].lower()  # Alphabetical
            ))

            summary = self._generate_symbol_summary(symbol_name, matching_symbols)

            return {
                "status": "success",
                "data": {
                    "symbols": matching_symbols[:20],  # Limit to top 20
                    "total_found": len(matching_symbols),
                    "summary": summary
                },
                "confidence": 0.9,
            }

        except Exception as e:
            logger.error(f"Error exploring symbols: {e}")
            return {
                "status": "error",
                "message": f"Symbol exploration failed: {str(e)}",
                "confidence": 0.0,
            }
    
    async def find_references(self, symbol_name: str) -> Dict[str, Any]:
        """
        Find references to a symbol across the codebase
        
        Extracted from: _find_references_tool()
        """
        try:
            if not self.project_index:
                await self._ensure_project_indexed()
                
            if not self.project_index:
                return {
                    "status": "error",
                    "message": "Project not indexed",
                    "confidence": 0.0,
                }

            # Find symbol definition
            target_symbol = None
            for symbol in self.project_index.symbols.values():
                if symbol.name == symbol_name:
                    target_symbol = symbol
                    break

            if not target_symbol:
                return {
                    "status": "success",
                    "data": {
                        "references": [],
                        "summary": f"Symbol '{symbol_name}' not found in project"
                    },
                    "confidence": 0.8,
                }

            # Find references in the graph
            references = []
            for file_analysis in self.project_index.files.values():
                for ref in file_analysis.references:
                    if ref.target_symbol == symbol_name:
                        references.append({
                            "file": file_analysis.file_path,
                            "line": ref.line_number,
                            "context": ref.context,
                            "reference_type": ref.reference_type
                        })

            summary = self._generate_reference_summary(symbol_name, target_symbol, references)

            return {
                "status": "success",
                "data": {
                    "symbol": {
                        "name": target_symbol.name,
                        "type": target_symbol.symbol_type,
                        "file": target_symbol.file_path,
                        "line": target_symbol.line_number
                    },
                    "references": references,
                    "total_references": len(references),
                    "summary": summary
                },
                "confidence": 0.9,
            }

        except Exception as e:
            logger.error(f"Error finding references: {e}")
            return {
                "status": "error",
                "message": f"Reference search failed: {str(e)}",
                "confidence": 0.0,
            }
    
    async def check_complexity(self, file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze code complexity across the project or specific file
        
        Extracted from: _check_complexity_tool()
        """
        try:
            if not self.project_index:
                await self._ensure_project_indexed()
                
            if not self.project_index:
                return {
                    "status": "error",
                    "message": "Project not indexed",
                    "confidence": 0.0,
                }

            if file_path:
                # Analyze specific file
                file_analysis = self.project_index.files.get(file_path)
                if not file_analysis:
                    return {
                        "status": "error",
                        "message": f"File not found: {file_path}",
                        "confidence": 0.0,
                    }
                
                complexity_data = {
                    "file": file_path,
                    "cyclomatic_complexity": file_analysis.complexity.cyclomatic_complexity,
                    "cognitive_complexity": file_analysis.complexity.cognitive_complexity,
                    "maintainability_index": file_analysis.complexity.maintainability_index,
                    "functions": []
                }
                
                # Add function-level complexity
                for symbol in self.project_index.symbols.values():
                    if (symbol.file_path == file_path and 
                        symbol.symbol_type == SymbolType.FUNCTION):
                        complexity_data["functions"].append({
                            "name": symbol.name,
                            "line": symbol.line_number,
                            "complexity": getattr(symbol, 'complexity', 0)
                        })
                
            else:
                # Analyze entire project
                total_complexity = sum(
                    analysis.complexity.cyclomatic_complexity
                    for analysis in self.project_index.files.values()
                )
                
                high_complexity_files = [
                    {
                        "file": analysis.file_path,
                        "complexity": analysis.complexity.cyclomatic_complexity
                    }
                    for analysis in self.project_index.files.values()
                    if analysis.complexity.cyclomatic_complexity > 10
                ]
                
                high_complexity_files.sort(key=lambda x: x["complexity"], reverse=True)
                
                complexity_data = {
                    "total_complexity": total_complexity,
                    "average_complexity": total_complexity / max(self.project_index.supported_files, 1),
                    "high_complexity_files": high_complexity_files[:10],
                    "recommendations": self._generate_complexity_recommendations(high_complexity_files)
                }

            summary = self._generate_complexity_summary(complexity_data, file_path)

            return {
                "status": "success",
                "data": {
                    "complexity": complexity_data,
                    "summary": summary
                },
                "confidence": 0.9,
            }

        except Exception as e:
            logger.error(f"Error checking complexity: {e}")
            return {
                "status": "error",
                "message": f"Complexity analysis failed: {str(e)}",
                "confidence": 0.0,
            }
    
    async def get_file_context(self, file_path: str) -> Dict[str, Any]:
        """
        Get comprehensive context for a specific file
        
        Extracted from: _get_file_context_tool()
        """
        try:
            if not self.ast_context_provider:
                return {
                    "status": "error",
                    "message": "AST context provider not initialized",
                    "confidence": 0.0,
                }

            context = await self.ast_context_provider.get_file_context(file_path)
            
            if not context:
                return {
                    "status": "error",
                    "message": f"Could not analyze file: {file_path}",
                    "confidence": 0.0,
                }

            # Enhance context with additional analysis
            enhanced_context = {
                "file_path": file_path,
                "symbols": [
                    {
                        "name": symbol.name,
                        "type": symbol.symbol_type,
                        "line": symbol.line_number,
                        "docstring": symbol.docstring
                    }
                    for symbol in context.symbols
                ],
                "imports": [
                    {
                        "module": imp.module_name,
                        "alias": imp.alias,
                        "line": imp.line_number
                    }
                    for imp in context.imports
                ],
                "complexity": {
                    "cyclomatic": context.complexity.cyclomatic_complexity,
                    "cognitive": context.complexity.cognitive_complexity,
                    "maintainability": context.complexity.maintainability_index
                }
            }

            summary = self._generate_file_context_summary(enhanced_context)

            return {
                "status": "success",
                "data": {
                    "context": enhanced_context,
                    "summary": summary
                },
                "confidence": 0.9,
            }

        except Exception as e:
            logger.error(f"Error getting file context: {e}")
            return {
                "status": "error",
                "message": f"File context analysis failed: {str(e)}",
                "confidence": 0.0,
            }
    
    async def get_completion_context(self, file_path: str, line_number: int, column: int) -> Dict[str, Any]:
        """
        Get intelligent completion context for a specific position
        
        Extracted from: _get_completion_context_tool()
        """
        try:
            if not self.ast_context_provider:
                return {
                    "status": "error",
                    "message": "AST context provider not initialized",
                    "confidence": 0.0,
                }

            context = await self.ast_context_provider.get_completion_context(
                file_path, line_number, column
            )
            
            if not context:
                return {
                    "status": "success",
                    "data": {
                        "suggestions": [],
                        "summary": "No completion context available"
                    },
                    "confidence": 0.5,
                }

            # Transform context into completion suggestions
            suggestions = []
            
            # Add symbols from current scope
            for symbol in context.available_symbols:
                suggestions.append({
                    "name": symbol.name,
                    "type": symbol.symbol_type,
                    "description": symbol.docstring or f"{symbol.symbol_type} in {symbol.parent_scope}",
                    "insert_text": symbol.name,
                    "priority": self._calculate_symbol_priority(symbol, context.current_scope)
                })

            # Add import suggestions
            for module in context.available_imports:
                suggestions.append({
                    "name": module,
                    "type": "module",
                    "description": f"Import {module}",
                    "insert_text": f"import {module}",
                    "priority": 0.5
                })

            # Sort by priority
            suggestions.sort(key=lambda x: x["priority"], reverse=True)

            summary = f"Found {len(suggestions)} completion suggestions at {file_path}:{line_number}:{column}"

            return {
                "status": "success",
                "data": {
                    "suggestions": suggestions[:20],  # Top 20 suggestions
                    "context": {
                        "file": file_path,
                        "line": line_number,
                        "column": column,
                        "scope": context.current_scope
                    },
                    "summary": summary
                },
                "confidence": 0.8,
            }

        except Exception as e:
            logger.error(f"Error getting completion context: {e}")
            return {
                "status": "error",
                "message": f"Completion context failed: {str(e)}",
                "confidence": 0.0,
            }
    
    def _calculate_quality_score(self, analysis_data: Dict[str, Any]) -> float:
        """Calculate a quality score based on analysis data"""
        score = 100.0
        
        # Penalize high average complexity
        avg_complexity = analysis_data.get("complexity", {}).get("average", 0)
        if avg_complexity > 10:
            score -= min(30, (avg_complexity - 10) * 2)
        
        # Penalize parsing errors
        parsing_errors = analysis_data.get("parsing_errors", 0)
        if parsing_errors > 0:
            error_rate = parsing_errors / max(analysis_data.get("total_files", 1), 1)
            score -= min(20, error_rate * 100)
        
        # Bonus for good symbol distribution
        symbol_breakdown = analysis_data.get("symbol_breakdown", {})
        if symbol_breakdown.get("class", 0) > 0 and symbol_breakdown.get("function", 0) > 0:
            score += 5
        
        return max(0.0, min(100.0, score))
    
    def _generate_analysis_summary(self, analysis_data: Dict[str, Any]) -> str:
        """Generate a human-readable summary of the analysis"""
        total_files = analysis_data.get("total_files", 0)
        total_symbols = analysis_data.get("total_symbols", 0)
        avg_complexity = analysis_data.get("complexity", {}).get("average", 0)
        quality_score = analysis_data.get("quality_score", 0)
        
        summary = f"Project analysis complete: {total_files} files, {total_symbols} symbols. "
        summary += f"Average complexity: {avg_complexity:.1f}, Quality score: {quality_score:.1f}/100."
        
        # Add recommendations
        if avg_complexity > 10:
            summary += " Consider refactoring complex functions."
        if quality_score < 70:
            summary += " Project could benefit from code quality improvements."
        
        return summary
    
    def _generate_symbol_summary(self, symbol_name: str, symbols: List[Dict]) -> str:
        """Generate summary for symbol exploration results"""
        if not symbols:
            return f"No symbols found matching '{symbol_name}'"
        
        types = set(s["type"] for s in symbols)
        files = set(s["file"] for s in symbols)
        
        summary = f"Found {len(symbols)} symbols matching '{symbol_name}' "
        summary += f"({', '.join(types)}) across {len(files)} files."
        
        return summary
    
    def _generate_reference_summary(self, symbol_name: str, symbol: Any, references: List[Dict]) -> str:
        """Generate summary for reference search results"""
        ref_count = len(references)
        files = set(ref["file"] for ref in references)
        
        summary = f"Symbol '{symbol_name}' ({symbol.symbol_type}) "
        summary += f"defined in {symbol.file_path}:{symbol.line_number} "
        summary += f"has {ref_count} references across {len(files)} files."
        
        return summary
    
    def _generate_complexity_summary(self, complexity_data: Dict[str, Any], file_path: Optional[str]) -> str:
        """Generate summary for complexity analysis"""
        if file_path:
            complexity = complexity_data.get("cyclomatic_complexity", 0)
            return f"File {file_path} has cyclomatic complexity of {complexity}"
        else:
            avg_complexity = complexity_data.get("average_complexity", 0)
            high_files = len(complexity_data.get("high_complexity_files", []))
            return f"Project average complexity: {avg_complexity:.1f}, {high_files} files need refactoring"
    
    def _generate_file_context_summary(self, context: Dict[str, Any]) -> str:
        """Generate summary for file context"""
        symbol_count = len(context.get("symbols", []))
        import_count = len(context.get("imports", []))
        complexity = context.get("complexity", {}).get("cyclomatic", 0)
        
        return f"File has {symbol_count} symbols, {import_count} imports, complexity: {complexity}"
    
    def _generate_complexity_recommendations(self, high_complexity_files: List[Dict]) -> List[str]:
        """Generate recommendations for reducing complexity"""
        recommendations = []
        
        if len(high_complexity_files) > 5:
            recommendations.append("Consider creating a refactoring plan for high-complexity files")
        
        if any(f["complexity"] > 20 for f in high_complexity_files):
            recommendations.append("Files with complexity >20 should be prioritized for refactoring")
        
        recommendations.append("Break down large functions into smaller, focused functions")
        recommendations.append("Consider using design patterns to reduce conditional complexity")
        
        return recommendations
    
    def _calculate_symbol_priority(self, symbol: Any, current_scope: str) -> float:
        """Calculate priority for symbol completion suggestions"""
        priority = 0.5
        
        # Higher priority for symbols in current scope
        if symbol.parent_scope == current_scope:
            priority += 0.3
        
        # Higher priority for public symbols
        if not symbol.name.startswith('_'):
            priority += 0.1
        
        # Higher priority for functions and classes
        if symbol.symbol_type in [SymbolType.FUNCTION, SymbolType.CLASS]:
            priority += 0.1
        
        return priority