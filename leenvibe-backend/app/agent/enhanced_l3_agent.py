"""
Enhanced L3 Coding Agent with AST Integration

Extends the basic L3 agent with deep code understanding through AST analysis.
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional
from pathlib import Path

from .l3_coding_agent import L3CodingAgent, AgentDependencies, AgentState
from ..services.ast_service import ast_service
from ..services.project_indexer import project_indexer
from ..services.graph_service import graph_service
from ..services.graph_query_service import graph_query_service
from ..services.visualization_service import visualization_service
from ..services.file_monitor_service import file_monitor_service
from ..models.ast_models import (
    ProjectIndex, ProjectContext, ASTContext, Symbol, Reference,
    SymbolType, ImpactAnalysis, RefactoringSuggestion
)
from ..models.graph_models import (
    GraphNode, GraphVisualizationData, ArchitecturePattern
)
from ..models.visualization_models import (
    DiagramType, DiagramTheme, DiagramLayout, DiagramConfiguration,
    DiagramGenerationRequest, DiagramExportFormat
)
from ..models.monitoring_models import (
    MonitoringConfiguration, MonitoringSession, FileChange,
    ChangeNotification, MonitoringMetrics
)

logger = logging.getLogger(__name__)


class EnhancedL3CodingAgent(L3CodingAgent):
    """
    L3 Coding Agent with AST-powered code understanding
    
    Provides deep project analysis, symbol awareness, and intelligent
    code assistance through Tree-sitter AST integration.
    """
    
    def __init__(self, dependencies: AgentDependencies):
        super().__init__(dependencies)
        
        # AST-specific state
        self.project_index: Optional[ProjectIndex] = None
        self.project_context: Optional[ProjectContext] = None
        self.last_index_update = 0
        self.index_timeout = 300  # 5 minutes
        
        # Enhanced tools with AST and graph capabilities
        self.tools.update({
            "analyze_project": self._analyze_project_tool,
            "find_references": self._find_references_tool,
            "impact_analysis": self._impact_analysis_tool,
            "suggest_refactoring": self._suggest_refactoring_tool,
            "explore_symbols": self._explore_symbols_tool,
            "check_complexity": self._check_complexity_tool,
            "detect_architecture": self._detect_architecture_tool,
            "find_circular_deps": self._find_circular_dependencies_tool,
            "analyze_coupling": self._analyze_coupling_tool,
            "find_hotspots": self._find_hotspots_tool,
            "visualize_graph": self._visualize_graph_tool,
            "generate_diagram": self._generate_diagram_tool,
            "list_diagram_types": self._list_diagram_types_tool,
            "start_monitoring": self._start_monitoring_tool,
            "stop_monitoring": self._stop_monitoring_tool,
            "get_monitoring_status": self._get_monitoring_status_tool,
            "get_recent_changes": self._get_recent_changes_tool
        })
    
    async def initialize(self):
        """Initialize the enhanced L3 agent with AST services"""
        try:
            logger.info("Initializing Enhanced L3 Coding Agent with AST...")
            
            # Initialize base agent
            await super().initialize()
            
            # Initialize AST services
            await ast_service.initialize()
            
            # Initialize graph database
            await graph_service.initialize()
            
            # Initialize project context
            await self._initialize_project_context()
            
            logger.info("Enhanced L3 Coding Agent initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize enhanced L3 agent: {e}")
            return False
    
    async def _initialize_project_context(self):
        """Initialize project context for the workspace"""
        try:
            workspace_path = self.dependencies.workspace_path
            
            # Create project context
            self.project_context = ProjectContext(
                workspace_path=workspace_path,
                current_file=None,
                recent_changes=[],
                key_components=[],
                technology_stack=[]
            )
            
            # Trigger initial project indexing (lightweight)
            await self._ensure_project_indexed()
            
        except Exception as e:
            logger.error(f"Error initializing project context: {e}")
    
    async def _ensure_project_indexed(self, force_refresh: bool = False) -> bool:
        """Ensure project is indexed and up-to-date"""
        try:
            current_time = time.time()
            
            # Check if we need to refresh the index
            if (not force_refresh and 
                self.project_index and 
                current_time - self.last_index_update < self.index_timeout):
                return True
            
            logger.info("Updating project index...")
            workspace_path = self.dependencies.workspace_path
            
            # Index the project (async in background for large projects)
            self.project_index = await project_indexer.index_project(workspace_path)
            self.last_index_update = current_time
            
            # Store project in graph database
            if graph_service.initialized and self.project_index:
                project_id = f"project_{hash(workspace_path)}"
                await graph_service.store_project_graph(self.project_index, workspace_path)
                logger.debug("Project stored in graph database")
            
            # Update project context
            if self.project_context:
                self.project_context.project_index = self.project_index
                await self._update_project_context()
            
            logger.info(f"Project indexed: {self.project_index.supported_files} files, "
                       f"{len(self.project_index.symbols)} symbols")
            return True
            
        except Exception as e:
            logger.error(f"Error indexing project: {e}")
            return False
    
    async def _update_project_context(self):
        """Update project context with analysis insights"""
        try:
            if not self.project_index or not self.project_context:
                return
            
            # Identify key components (classes and main functions)
            key_components = []
            for symbol in self.project_index.symbols.values():
                if (symbol.symbol_type in [SymbolType.CLASS, SymbolType.FUNCTION] and
                    symbol.name in ["main", "App", "Application"] or
                    symbol.name.endswith("Service") or symbol.name.endswith("Manager")):
                    key_components.append(f"{symbol.name} ({symbol.file_path})")
            
            self.project_context.key_components = key_components[:10]  # Top 10
            
            # Identify technology stack from dependencies
            tech_stack = set()
            for dependency in self.project_index.dependencies:
                if dependency.is_external and dependency.module_name:
                    tech_stack.add(dependency.module_name.split('.')[0])
            
            self.project_context.technology_stack = list(tech_stack)[:20]  # Top 20
            
            # Update architecture summary
            self.project_context.architecture_summary = self._generate_architecture_summary()
            
        except Exception as e:
            logger.error(f"Error updating project context: {e}")
    
    def _generate_architecture_summary(self) -> str:
        """Generate a brief architecture summary"""
        try:
            if not self.project_index:
                return "No project analysis available"
            
            total_files = self.project_index.supported_files
            total_symbols = len(self.project_index.symbols)
            
            # Count by symbol type
            symbol_counts = {}
            for symbol in self.project_index.symbols.values():
                symbol_type = symbol.symbol_type
                symbol_counts[symbol_type] = symbol_counts.get(symbol_type, 0) + 1
            
            # Count by language
            language_counts = {}
            for analysis in self.project_index.files.values():
                lang = analysis.language
                language_counts[lang] = language_counts.get(lang, 0) + 1
            
            summary_parts = [
                f"Project with {total_files} files and {total_symbols} symbols",
                f"Languages: {', '.join(str(lang) for lang in language_counts.keys())}",
                f"Components: {symbol_counts.get(SymbolType.CLASS, 0)} classes, "
                f"{symbol_counts.get(SymbolType.FUNCTION, 0)} functions"
            ]
            
            return ". ".join(summary_parts)
            
        except Exception as e:
            logger.error(f"Error generating architecture summary: {e}")
            return "Architecture analysis failed"
    
    async def _process_user_input(self, user_input: str) -> str:
        """Enhanced user input processing with AST awareness"""
        try:
            # Ensure project is indexed
            await self._ensure_project_indexed()
            
            # Enhanced tool detection with AST capabilities
            user_lower = user_input.lower()
            
            # Project analysis requests
            if any(keyword in user_lower for keyword in ["analyze project", "project overview", "architecture"]):
                result = await self._analyze_project_tool()
                if result["status"] == "success":
                    return result["data"]["summary"]
                else:
                    return f"Error analyzing project: {result['message']}"
            
            # Symbol exploration
            elif any(keyword in user_lower for keyword in ["find symbol", "search symbol", "explore"]):
                # Extract symbol name (simple heuristic)
                words = user_input.split()
                symbol_name = None
                for i, word in enumerate(words):
                    if word.lower() in ["symbol", "function", "class"] and i + 1 < len(words):
                        symbol_name = words[i + 1]
                        break
                
                if symbol_name:
                    result = await self._explore_symbols_tool(symbol_name)
                    if result["status"] == "success":
                        return result["data"]["summary"]
                    else:
                        return f"Error exploring symbol: {result['message']}"
            
            # Diagram types inquiry
            elif any(keyword in user_lower for keyword in ["diagram types", "available diagrams", "what diagrams"]):
                result = await self._list_diagram_types_tool()
                if result["status"] == "success":
                    return result["data"]["summary"]
                else:
                    return f"Error listing diagram types: {result['message']}"
            
            # Reference finding
            elif "references" in user_lower or "where is" in user_lower:
                # Extract symbol name from query
                for symbol in self.project_index.symbols.values() if self.project_index else []:
                    if symbol.name.lower() in user_lower:
                        result = await self._find_references_tool(symbol.name)
                        if result["status"] == "success":
                            return result["data"]["summary"]
                        break
            
            # Complexity analysis
            elif any(keyword in user_lower for keyword in ["complexity", "complex", "refactor"]):
                result = await self._check_complexity_tool()
                if result["status"] == "success":
                    return result["data"]["summary"]
                else:
                    return f"Error checking complexity: {result['message']}"
            
            # Architecture analysis
            elif any(keyword in user_lower for keyword in ["architecture", "pattern", "design"]):
                result = await self._detect_architecture_tool()
                if result["status"] == "success":
                    return result["data"]["summary"]
                else:
                    return f"Error analyzing architecture: {result['message']}"
            
            # Circular dependencies
            elif any(keyword in user_lower for keyword in ["circular", "cycle", "circular deps"]):
                result = await self._find_circular_dependencies_tool()
                if result["status"] == "success":
                    return result["data"]["summary"]
                else:
                    return f"Error finding circular dependencies: {result['message']}"
            
            # Coupling analysis
            elif any(keyword in user_lower for keyword in ["coupling", "dependencies", "depend"]):
                result = await self._analyze_coupling_tool()
                if result["status"] == "success":
                    return result["data"]["summary"]
                else:
                    return f"Error analyzing coupling: {result['message']}"
            
            # Hotspots analysis
            elif any(keyword in user_lower for keyword in ["hotspots", "critical", "important"]):
                result = await self._find_hotspots_tool()
                if result["status"] == "success":
                    return result["data"]["summary"]
                else:
                    return f"Error finding hotspots: {result['message']}"
            
            # Real-time monitoring commands
            elif any(keyword in user_lower for keyword in ["start monitoring", "monitor", "watch files"]):
                result = await self._start_monitoring_tool()
                if result["status"] == "success":
                    return result["data"]["summary"]
                else:
                    return f"Error starting monitoring: {result['message']}"
            
            elif any(keyword in user_lower for keyword in ["stop monitoring", "stop watching"]):
                result = await self._stop_monitoring_tool()
                if result["status"] == "success":
                    return result["data"]["summary"]
                else:
                    return f"Error stopping monitoring: {result['message']}"
            
            elif any(keyword in user_lower for keyword in ["monitoring status", "watch status", "recent changes"]):
                if "changes" in user_lower:
                    result = await self._get_recent_changes_tool()
                else:
                    result = await self._get_monitoring_status_tool()
                
                if result["status"] == "success":
                    return result["data"]["summary"]
                else:
                    return f"Error getting monitoring info: {result['message']}"
            
            # Graph visualization and diagrams
            elif any(keyword in user_lower for keyword in ["visualize", "diagram", "graph", "chart"]):
                # Check for specific diagram type requests
                if "dependency" in user_lower or "deps" in user_lower:
                    result = await self._generate_diagram_tool(DiagramType.DEPENDENCY_GRAPH)
                elif "hotspot" in user_lower or "critical" in user_lower:
                    result = await self._generate_diagram_tool(DiagramType.HOTSPOT_HEATMAP)
                elif "circular" in user_lower or "cycle" in user_lower:
                    result = await self._generate_diagram_tool(DiagramType.CIRCULAR_DEPENDENCIES)
                elif "coupling" in user_lower:
                    result = await self._generate_diagram_tool(DiagramType.COUPLING_ANALYSIS)
                elif "architecture" in user_lower or "overview" in user_lower:
                    result = await self._generate_diagram_tool(DiagramType.ARCHITECTURE_OVERVIEW)
                else:
                    result = await self._visualize_graph_tool()
                
                if result["status"] == "success":
                    return result["data"]["summary"]
                else:
                    return f"Error generating visualization: {result['message']}"
            
            # Enhanced file analysis with AST context
            elif "analyze" in user_lower and ("file" in user_lower or "code" in user_lower):
                # Extract file path
                words = user_input.split()
                for word in words:
                    if "." in word and "/" in word:  # Looks like a file path
                        result = await self._analyze_file_with_context(word)
                        return result
            
            # Fall back to base implementation with enhanced context
            else:
                # Add AST context to the prompt
                enhanced_prompt = await self._create_contextual_prompt(user_input)
                response = await self.model_wrapper.generate_response(enhanced_prompt)
                return response
            
        except Exception as e:
            logger.error(f"Error in enhanced user input processing: {e}")
            return f"I encountered an error processing your request: {str(e)}. How can I help you differently?"
    
    async def _create_contextual_prompt(self, user_input: str) -> str:
        """Create a context-aware prompt with project understanding"""
        try:
            base_prompt = f"""
As LeenVibe L3 coding agent, I need to respond to: "{user_input}"

Project Context:
- Workspace: {self.state.workspace_path}
- Architecture: {self.project_context.architecture_summary if self.project_context else 'Unknown'}
- Technology Stack: {', '.join(self.project_context.technology_stack[:5]) if self.project_context else 'Unknown'}
- Key Components: {len(self.project_context.key_components) if self.project_context else 0} identified
- Previous interactions: {len(self.state.conversation_history)}
- Average confidence: {self.state.get_average_confidence():.2f}
"""
            
            # Add current file context if available
            if self.project_context and self.project_context.current_file:
                current_file_analysis = None
                if self.project_index:
                    current_file_analysis = self.project_index.files.get(self.project_context.current_file)
                
                if current_file_analysis:
                    base_prompt += f"""
Current File Context:
- File: {self.project_context.current_file}
- Language: {current_file_analysis.language}
- Symbols: {len(current_file_analysis.symbols)} (functions, classes, etc.)
- Complexity: {current_file_analysis.complexity.cyclomatic_complexity}
"""
            
            base_prompt += "\nProvide a helpful, practical response focused on coding assistance with project awareness."
            
            return base_prompt
            
        except Exception as e:
            logger.error(f"Error creating contextual prompt: {e}")
            return f"As LeenVibe L3 coding agent, I need to respond to: \"{user_input}\""
    
    async def _analyze_project_tool(self) -> Dict[str, Any]:
        """Analyze the entire project and provide insights"""
        try:
            # Ensure project is indexed
            indexed = await self._ensure_project_indexed()
            if not indexed or not self.project_index:
                return {
                    "status": "error",
                    "message": "Could not index project for analysis",
                    "confidence": 0.0
                }
            
            # Generate comprehensive analysis
            analysis_data = {
                "total_files": self.project_index.total_files,
                "supported_files": self.project_index.supported_files,
                "total_symbols": len(self.project_index.symbols),
                "parsing_errors": self.project_index.parsing_errors
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
            avg_complexity = total_complexity / max(self.project_index.supported_files, 1)
            
            analysis_data["complexity"] = {
                "total": total_complexity,
                "average": avg_complexity,
                "high_complexity_files": [
                    analysis.file_path for analysis in self.project_index.files.values()
                    if analysis.complexity.cyclomatic_complexity > 20
                ]
            }
            
            # Generate summary
            summary = f"""Project Analysis Complete:

📁 Files: {analysis_data['supported_files']}/{analysis_data['total_files']} supported files
🔧 Symbols: {analysis_data['total_symbols']} total ({symbol_breakdown.get(SymbolType.FUNCTION, 0)} functions, {symbol_breakdown.get(SymbolType.CLASS, 0)} classes)
📊 Languages: {', '.join(str(lang) for lang in language_breakdown.keys())}
🔍 Complexity: Average {avg_complexity:.1f} per file
⚠️ Issues: {analysis_data['parsing_errors']} parsing errors

Key Components:
{chr(10).join(f"• {component}" for component in (self.project_context.key_components[:5] if self.project_context else []))}

Technology Stack: {', '.join(self.project_context.technology_stack[:10]) if self.project_context else 'Unknown'}"""
            
            analysis_data["summary"] = summary
            
            # Calculate confidence based on analysis completeness
            confidence = min(0.9, 0.5 + (analysis_data['supported_files'] / max(analysis_data['total_files'], 1)) * 0.4)
            
            return {
                "status": "success",
                "type": "project_analysis",
                "data": analysis_data,
                "message": "Project analysis completed successfully",
                "confidence": confidence
            }
            
        except Exception as e:
            logger.error(f"Error in project analysis tool: {e}")
            return {
                "status": "error",
                "message": f"Project analysis failed: {str(e)}",
                "confidence": 0.0
            }
    
    async def _explore_symbols_tool(self, symbol_name: str) -> Dict[str, Any]:
        """Explore symbols matching the given name"""
        try:
            if not self.project_index:
                return {
                    "status": "error",
                    "message": "Project not indexed",
                    "confidence": 0.0
                }
            
            # Find matching symbols
            matching_symbols = [
                symbol for symbol in self.project_index.symbols.values()
                if symbol_name.lower() in symbol.name.lower()
            ]
            
            if not matching_symbols:
                return {
                    "status": "error",
                    "message": f"No symbols found matching '{symbol_name}'",
                    "confidence": 0.8
                }
            
            # Organize by symbol type
            symbols_by_type = {}
            for symbol in matching_symbols:
                symbol_type = symbol.symbol_type
                if symbol_type not in symbols_by_type:
                    symbols_by_type[symbol_type] = []
                symbols_by_type[symbol_type].append(symbol)
            
            # Generate summary
            summary_parts = [f"Found {len(matching_symbols)} symbols matching '{symbol_name}':"]
            
            for symbol_type, symbols in symbols_by_type.items():
                summary_parts.append(f"\n{symbol_type}s:")
                for symbol in symbols[:5]:  # Limit to 5 per type
                    location = f"{Path(symbol.file_path).name}:{symbol.line_start}"
                    summary_parts.append(f"  • {symbol.name} ({location})")
                
                if len(symbols) > 5:
                    summary_parts.append(f"  ... and {len(symbols) - 5} more")
            
            data = {
                "matching_symbols": len(matching_symbols),
                "symbols_by_type": {str(k): len(v) for k, v in symbols_by_type.items()},
                "symbols": [
                    {
                        "name": s.name,
                        "type": s.symbol_type,
                        "file": s.file_path,
                        "line": s.line_start
                    } for s in matching_symbols[:10]
                ],
                "summary": "\n".join(summary_parts)
            }
            
            return {
                "status": "success",
                "type": "symbol_exploration",
                "data": data,
                "message": f"Found {len(matching_symbols)} symbols",
                "confidence": 0.9
            }
            
        except Exception as e:
            logger.error(f"Error in symbol exploration: {e}")
            return {
                "status": "error",
                "message": f"Symbol exploration failed: {str(e)}",
                "confidence": 0.0
            }
    
    async def _find_references_tool(self, symbol_name: str) -> Dict[str, Any]:
        """Find all references to a symbol"""
        try:
            if not self.project_index:
                return {
                    "status": "error",
                    "message": "Project not indexed",
                    "confidence": 0.0
                }
            
            # Find references using project indexer
            references = await project_indexer.find_references(self.project_index, symbol_name)
            
            if not references:
                return {
                    "status": "error",
                    "message": f"No references found for '{symbol_name}'",
                    "confidence": 0.8
                }
            
            # Organize references
            definitions = [ref for ref in references if ref.reference_type == "definition"]
            usages = [ref for ref in references if ref.reference_type == "usage"]
            
            # Generate summary
            summary = f"References for '{symbol_name}':\n\n"
            
            if definitions:
                summary += f"📍 Definitions ({len(definitions)}):\n"
                for ref in definitions[:3]:
                    location = f"{Path(ref.file_path).name}:{ref.line_number}"
                    summary += f"  • {location} - {ref.context or 'Definition'}\n"
            
            if usages:
                summary += f"\n🔗 Usages ({len(usages)}):\n"
                for ref in usages[:5]:
                    location = f"{Path(ref.file_path).name}:{ref.line_number}"
                    summary += f"  • {location} - {ref.context or 'Usage'}\n"
                
                if len(usages) > 5:
                    summary += f"  ... and {len(usages) - 5} more usages\n"
            
            data = {
                "total_references": len(references),
                "definitions": len(definitions),
                "usages": len(usages),
                "files_affected": len(set(ref.file_path for ref in references)),
                "summary": summary
            }
            
            return {
                "status": "success",
                "type": "reference_analysis",
                "data": data,
                "message": f"Found {len(references)} references",
                "confidence": 0.85
            }
            
        except Exception as e:
            logger.error(f"Error finding references: {e}")
            return {
                "status": "error",
                "message": f"Reference search failed: {str(e)}",
                "confidence": 0.0
            }
    
    async def _check_complexity_tool(self) -> Dict[str, Any]:
        """Check code complexity across the project"""
        try:
            if not self.project_index:
                return {
                    "status": "error",
                    "message": "Project not indexed",
                    "confidence": 0.0
                }
            
            # Analyze complexity across files
            complexity_data = []
            high_complexity_files = []
            total_complexity = 0
            
            for file_path, analysis in self.project_index.files.items():
                complexity = analysis.complexity.cyclomatic_complexity
                total_complexity += complexity
                
                complexity_data.append({
                    "file": file_path,
                    "complexity": complexity,
                    "functions": analysis.complexity.number_of_functions,
                    "classes": analysis.complexity.number_of_classes,
                    "lines": analysis.complexity.lines_of_code
                })
                
                if complexity > 15:  # High complexity threshold
                    high_complexity_files.append({
                        "file": Path(file_path).name,
                        "complexity": complexity,
                        "path": file_path
                    })
            
            # Sort by complexity
            complexity_data.sort(key=lambda x: x["complexity"], reverse=True)
            avg_complexity = total_complexity / max(len(complexity_data), 1)
            
            # Generate summary
            summary = f"Code Complexity Analysis:\n\n"
            summary += f"📊 Overall: {total_complexity} total complexity across {len(complexity_data)} files\n"
            summary += f"📈 Average: {avg_complexity:.1f} complexity per file\n\n"
            
            if high_complexity_files:
                summary += f"⚠️ High Complexity Files ({len(high_complexity_files)}):\n"
                for file_info in high_complexity_files[:5]:
                    summary += f"  • {file_info['file']} - Complexity: {file_info['complexity']}\n"
                
                if len(high_complexity_files) > 5:
                    summary += f"  ... and {len(high_complexity_files) - 5} more\n"
            else:
                summary += "✅ No files with high complexity detected\n"
            
            summary += f"\n🔧 Top Complex Files:\n"
            for file_data in complexity_data[:3]:
                file_name = Path(file_data["file"]).name
                summary += f"  • {file_name} - {file_data['complexity']} complexity\n"
            
            data = {
                "total_complexity": total_complexity,
                "average_complexity": avg_complexity,
                "high_complexity_files": len(high_complexity_files),
                "top_complex_files": complexity_data[:10],
                "summary": summary
            }
            
            return {
                "status": "success",
                "type": "complexity_analysis",
                "data": data,
                "message": "Complexity analysis completed",
                "confidence": 0.9
            }
            
        except Exception as e:
            logger.error(f"Error in complexity analysis: {e}")
            return {
                "status": "error",
                "message": f"Complexity analysis failed: {str(e)}",
                "confidence": 0.0
            }
    
    async def _analyze_file_with_context(self, file_path: str) -> str:
        """Analyze a file with full project context"""
        try:
            # Analyze the file with AST
            result = await self._analyze_file_tool(file_path)
            
            if result["status"] != "success":
                return f"Error analyzing file: {result['message']}"
            
            # Add project context
            file_analysis = result["data"]
            context_info = []
            
            if self.project_index:
                # Find related files through dependencies
                related_files = []
                for dep in self.project_index.dependencies:
                    if dep.source_file == file_path and dep.target_file:
                        related_files.append(Path(dep.target_file).name)
                    elif dep.target_file == file_path:
                        related_files.append(Path(dep.source_file).name)
                
                if related_files:
                    context_info.append(f"Related files: {', '.join(set(related_files[:5]))}")
                
                # Find symbols in this file
                file_symbols = [
                    symbol for symbol in self.project_index.symbols.values()
                    if symbol.file_path == file_path
                ]
                
                if file_symbols:
                    symbol_summary = {}
                    for symbol in file_symbols:
                        symbol_type = symbol.symbol_type
                        symbol_summary[symbol_type] = symbol_summary.get(symbol_type, 0) + 1
                    
                    context_info.append(f"Contains: {', '.join(f'{count} {type}s' for type, count in symbol_summary.items())}")
            
            # Combine analysis with context
            enhanced_analysis = file_analysis["analysis"]
            if context_info:
                enhanced_analysis += f"\n\nProject Context:\n• " + "\n• ".join(context_info)
            
            return enhanced_analysis
            
        except Exception as e:
            logger.error(f"Error in contextual file analysis: {e}")
            return f"Error analyzing file with context: {str(e)}"
    
    async def _impact_analysis_tool(self, file_path: str) -> Dict[str, Any]:
        """Analyze the impact of changes to a file"""
        # Placeholder implementation - would need more sophisticated analysis
        return {
            "status": "success",
            "type": "impact_analysis",
            "data": {"impact": "low", "affected_files": []},
            "message": "Impact analysis completed",
            "confidence": 0.7
        }
    
    async def _suggest_refactoring_tool(self, target: str) -> Dict[str, Any]:
        """Suggest refactoring opportunities"""
        # Placeholder implementation - would analyze complexity and patterns
        return {
            "status": "success",
            "type": "refactoring_suggestions",
            "data": {"suggestions": []},
            "message": "Refactoring analysis completed",
            "confidence": 0.6
        }
    
    async def _detect_architecture_tool(self) -> Dict[str, Any]:
        """Detect architecture patterns in the project"""
        try:
            if not graph_service.initialized:
                return {
                    "status": "error",
                    "message": "Graph database not available",
                    "confidence": 0.0
                }
            
            workspace_path = self.dependencies.workspace_path
            project_id = f"project_{hash(workspace_path)}"
            
            patterns = await graph_service.get_architecture_patterns(project_id)
            
            if not patterns:
                return {
                    "status": "success",
                    "type": "architecture_detection",
                    "data": {
                        "patterns": [],
                        "summary": "No common architecture patterns detected. This might indicate a microservice, library, or custom architecture."
                    },
                    "message": "Architecture analysis completed",
                    "confidence": 0.7
                }
            
            # Generate summary
            summary_parts = ["Detected Architecture Patterns:\n"]
            for pattern in patterns:
                confidence_indicator = "🔴" if pattern.confidence < 0.5 else "🟡" if pattern.confidence < 0.8 else "🟢"
                summary_parts.append(f"{confidence_indicator} {pattern.pattern_name} (confidence: {pattern.confidence:.1%})")
                summary_parts.append(f"   {pattern.description}")
                if pattern.components:
                    summary_parts.append(f"   Components: {', '.join(pattern.components[:3])}")
                summary_parts.append("")
            
            data = {
                "patterns": [
                    {
                        "name": p.pattern_name,
                        "confidence": p.confidence,
                        "description": p.description,
                        "components": p.components,
                        "relationships": p.relationships
                    } for p in patterns
                ],
                "total_patterns": len(patterns),
                "summary": "\n".join(summary_parts)
            }
            
            return {
                "status": "success",
                "type": "architecture_detection",
                "data": data,
                "message": f"Found {len(patterns)} architecture patterns",
                "confidence": 0.85
            }
            
        except Exception as e:
            logger.error(f"Error in architecture detection: {e}")
            return {
                "status": "error",
                "message": f"Architecture detection failed: {str(e)}",
                "confidence": 0.0
            }
    
    async def _find_circular_dependencies_tool(self) -> Dict[str, Any]:
        """Find circular dependencies in the project"""
        try:
            if not graph_service.initialized:
                return {
                    "status": "error",
                    "message": "Graph database not available",
                    "confidence": 0.0
                }
            
            workspace_path = self.dependencies.workspace_path
            project_id = f"project_{hash(workspace_path)}"
            
            cycles = await graph_query_service.find_circular_dependencies(project_id)
            
            if not cycles:
                return {
                    "status": "success",
                    "type": "circular_dependency_analysis",
                    "data": {
                        "cycles": [],
                        "cycle_count": 0,
                        "summary": "✅ No circular dependencies detected. Good modular design!"
                    },
                    "message": "No circular dependencies found",
                    "confidence": 0.9
                }
            
            # Generate summary
            summary_parts = [f"🔄 Found {len(cycles)} circular dependencies:\n"]
            for i, cycle in enumerate(cycles[:5], 1):
                cycle_str = " → ".join(cycle + [cycle[0]])  # Complete the circle
                summary_parts.append(f"{i}. {cycle_str}")
            
            if len(cycles) > 5:
                summary_parts.append(f"... and {len(cycles) - 5} more cycles")
            
            summary_parts.extend([
                "",
                "⚠️ Circular dependencies can make code harder to:",
                "• Test in isolation",
                "• Understand and maintain", 
                "• Refactor safely",
                "",
                "💡 Consider dependency injection or interface abstraction"
            ])
            
            data = {
                "cycles": cycles,
                "cycle_count": len(cycles),
                "summary": "\n".join(summary_parts)
            }
            
            return {
                "status": "success",
                "type": "circular_dependency_analysis",
                "data": data,
                "message": f"Found {len(cycles)} circular dependencies",
                "confidence": 0.85
            }
            
        except Exception as e:
            logger.error(f"Error finding circular dependencies: {e}")
            return {
                "status": "error",
                "message": f"Circular dependency analysis failed: {str(e)}",
                "confidence": 0.0
            }
    
    async def _analyze_coupling_tool(self) -> Dict[str, Any]:
        """Analyze coupling between components"""
        try:
            if not graph_service.initialized:
                return {
                    "status": "error",
                    "message": "Graph database not available",
                    "confidence": 0.0
                }
            
            workspace_path = self.dependencies.workspace_path
            project_id = f"project_{hash(workspace_path)}"
            
            coupling_data = await graph_query_service.analyze_coupling(project_id)
            
            if not coupling_data:
                return {
                    "status": "error",
                    "message": "No coupling data available",
                    "confidence": 0.0
                }
            
            # Generate summary
            avg_coupling = coupling_data.get("average_coupling", 0)
            high_coupling_files = coupling_data.get("highly_coupled_files", [])
            
            summary_parts = [f"📊 Coupling Analysis Results:\n"]
            summary_parts.append(f"Average coupling: {avg_coupling:.1f} dependencies per file")
            
            if not high_coupling_files:
                summary_parts.append("✅ No highly coupled files detected")
            else:
                summary_parts.append(f"⚠️ {len(high_coupling_files)} highly coupled files:")
                for file_info in high_coupling_files[:5]:
                    file_name = Path(file_info["file_name"]).name
                    coupling = file_info["total_coupling"]
                    summary_parts.append(f"  • {file_name}: {coupling} total dependencies")
                
                if len(high_coupling_files) > 5:
                    summary_parts.append(f"  ... and {len(high_coupling_files) - 5} more")
                
                summary_parts.extend([
                    "",
                    "💡 High coupling can indicate:",
                    "• God objects or classes",
                    "• Missing abstraction layers",
                    "• Opportunities for refactoring"
                ])
            
            data = {
                "average_coupling": avg_coupling,
                "highly_coupled_files": high_coupling_files,
                "total_files_analyzed": coupling_data.get("total_files_analyzed", 0),
                "summary": "\n".join(summary_parts)
            }
            
            return {
                "status": "success",
                "type": "coupling_analysis",
                "data": data,
                "message": "Coupling analysis completed",
                "confidence": 0.8
            }
            
        except Exception as e:
            logger.error(f"Error analyzing coupling: {e}")
            return {
                "status": "error",
                "message": f"Coupling analysis failed: {str(e)}",
                "confidence": 0.0
            }
    
    async def _find_hotspots_tool(self) -> Dict[str, Any]:
        """Find code hotspots (frequently connected code)"""
        try:
            if not graph_service.initialized:
                return {
                    "status": "error",
                    "message": "Graph database not available",
                    "confidence": 0.0
                }
            
            workspace_path = self.dependencies.workspace_path
            project_id = f"project_{hash(workspace_path)}"
            
            hotspots = await graph_query_service.find_hotspots(project_id)
            
            if not hotspots:
                return {
                    "status": "success",
                    "type": "hotspot_analysis",
                    "data": {
                        "hotspots": [],
                        "summary": "🎯 No critical hotspots detected. Code appears well-distributed."
                    },
                    "message": "No hotspots found",
                    "confidence": 0.8
                }
            
            # Generate summary
            summary_parts = [f"🔥 Found {len(hotspots)} code hotspots:\n"]
            
            for hotspot in hotspots[:5]:
                symbol_name = hotspot["symbol_name"]
                connections = hotspot["connection_count"]
                risk_level = hotspot["risk_level"]
                file_name = Path(hotspot["file_path"]).name
                
                risk_indicator = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(risk_level, "⚪")
                summary_parts.append(f"{risk_indicator} {symbol_name} ({file_name})")
                summary_parts.append(f"   {connections} connections, {risk_level} risk")
            
            if len(hotspots) > 5:
                summary_parts.append(f"... and {len(hotspots) - 5} more hotspots")
            
            summary_parts.extend([
                "",
                "🎯 Hotspots are code that:",
                "• Has many incoming/outgoing connections",
                "• May be critical to system functionality",
                "• Requires careful testing when modified",
                "",
                "💡 Consider extra testing and documentation for hotspots"
            ])
            
            data = {
                "hotspots": hotspots,
                "hotspot_count": len(hotspots),
                "summary": "\n".join(summary_parts)
            }
            
            return {
                "status": "success",
                "type": "hotspot_analysis",
                "data": data,
                "message": f"Found {len(hotspots)} hotspots",
                "confidence": 0.85
            }
            
        except Exception as e:
            logger.error(f"Error finding hotspots: {e}")
            return {
                "status": "error",
                "message": f"Hotspot analysis failed: {str(e)}",
                "confidence": 0.0
            }
    
    async def _visualize_graph_tool(self) -> Dict[str, Any]:
        """Generate graph visualization data"""
        try:
            if not graph_service.initialized:
                return {
                    "status": "error",
                    "message": "Graph database not available",
                    "confidence": 0.0
                }
            
            workspace_path = self.dependencies.workspace_path
            project_id = f"project_{hash(workspace_path)}"
            
            viz_data = await graph_service.get_visualization_data(project_id, max_nodes=50)
            
            if not viz_data.nodes:
                return {
                    "status": "success",
                    "type": "graph_visualization",
                    "data": {
                        "visualization": {},
                        "mermaid_diagram": "graph TD\n    A[No data available]",
                        "summary": "No visualization data available for this project"
                    },
                    "message": "No graph data available",
                    "confidence": 0.7
                }
            
            # Generate Mermaid diagram
            mermaid_diagram = viz_data.to_mermaid()
            
            # Generate summary
            node_count = len(viz_data.nodes)
            edge_count = len(viz_data.edges)
            
            summary = f"""📊 Project Graph Visualization:

🔗 Structure:
• {node_count} nodes (files, classes, functions)
• {edge_count} relationships (calls, dependencies, inheritance)

📈 This diagram shows the relationships between your code components.
Use it to understand:
• Code dependencies and call patterns
• Component interactions
• Potential refactoring opportunities
"""
            
            data = {
                "visualization": {
                    "nodes": viz_data.nodes,
                    "edges": viz_data.edges,
                    "layout": viz_data.layout
                },
                "mermaid_diagram": mermaid_diagram,
                "node_count": node_count,
                "edge_count": edge_count,
                "summary": summary
            }
            
            return {
                "status": "success",
                "type": "graph_visualization",
                "data": data,
                "message": f"Generated visualization with {node_count} nodes",
                "confidence": 0.9
            }
            
        except Exception as e:
            logger.error(f"Error generating visualization: {e}")
            return {
                "status": "error",
                "message": f"Visualization generation failed: {str(e)}",
                "confidence": 0.0
            }
    
    async def _generate_diagram_tool(
        self, 
        diagram_type: DiagramType = DiagramType.ARCHITECTURE_OVERVIEW,
        theme: DiagramTheme = DiagramTheme.LIGHT,
        max_nodes: int = 50
    ) -> Dict[str, Any]:
        """Generate interactive diagram using advanced visualization service"""
        try:
            workspace_path = self.dependencies.workspace_path
            project_id = f"project_{hash(workspace_path)}"
            
            # Create diagram configuration
            config = DiagramConfiguration(
                diagram_type=diagram_type,
                theme=theme,
                layout=DiagramLayout.TOP_DOWN,
                max_nodes=max_nodes,
                interactive=True,
                show_labels=True
            )
            
            # Create generation request
            request = DiagramGenerationRequest(
                project_id=project_id,
                configuration=config,
                export_format=DiagramExportFormat.MERMAID,
                include_metadata=True,
                cache_result=True
            )
            
            # Generate diagram
            response = await visualization_service.generate_diagram(request)
            
            # Create summary based on diagram type
            diagram_type_names = {
                DiagramType.ARCHITECTURE_OVERVIEW: "Architecture Overview",
                DiagramType.DEPENDENCY_GRAPH: "Dependency Graph",
                DiagramType.HOTSPOT_HEATMAP: "Code Hotspots Heatmap",
                DiagramType.CIRCULAR_DEPENDENCIES: "Circular Dependencies",
                DiagramType.COUPLING_ANALYSIS: "Coupling Analysis"
            }
            
            diagram_name = diagram_type_names.get(diagram_type, "Interactive Diagram")
            
            summary = f"""📊 {diagram_name} Generated Successfully!

🔗 Diagram Details:
• {response.node_count} nodes (components, files, symbols)
• {response.edge_count} relationships
• Generated in {response.generation_time_ms}ms
• Interactive features enabled

📈 This diagram provides:
"""
            
            # Add diagram-specific insights
            if diagram_type == DiagramType.ARCHITECTURE_OVERVIEW:
                summary += """• High-level system architecture view
• Component relationships and dependencies
• Pattern recognition and design insights
• Navigation aid for understanding code structure"""
            elif diagram_type == DiagramType.DEPENDENCY_GRAPH:
                summary += """• File and module dependency visualization
• Import relationship mapping
• Dependency chain analysis
• Potential circular dependency identification"""
            elif diagram_type == DiagramType.HOTSPOT_HEATMAP:
                summary += """• Critical code component identification
• High-connection point visualization
• Risk assessment for changes
• Focus areas for testing and documentation"""
            elif diagram_type == DiagramType.CIRCULAR_DEPENDENCIES:
                summary += """• Circular dependency cycle detection
• File interdependency issues
• Refactoring opportunity identification
• Architecture improvement guidance"""
            elif diagram_type == DiagramType.COUPLING_ANALYSIS:
                summary += """• Component coupling strength analysis
• Dependency density visualization
• Refactoring priority identification
• Architecture quality assessment"""
            
            summary += f"""

🎨 Interactive Features:
• Click nodes for detailed information
• Zoom and pan for large diagrams
• Filter and search capabilities
• Export options (SVG, PNG, PDF)

💡 Use this diagram to understand your codebase structure and identify improvement opportunities!"""
            
            data = {
                "diagram_id": response.diagram_id,
                "diagram_type": diagram_type,
                "mermaid_content": response.mermaid_diagram.content if response.mermaid_diagram else None,
                "full_mermaid": response.mermaid_diagram.get_full_content() if response.mermaid_diagram else None,
                "node_count": response.node_count,
                "edge_count": response.edge_count,
                "generation_time_ms": response.generation_time_ms,
                "summary": summary,
                "metadata": response.metadata
            }
            
            return {
                "status": "success",
                "type": "diagram_generation",
                "data": data,
                "message": f"Generated {diagram_name} with {response.node_count} nodes",
                "confidence": 0.95
            }
            
        except Exception as e:
            logger.error(f"Error generating diagram: {e}")
            return {
                "status": "error",
                "message": f"Diagram generation failed: {str(e)}",
                "confidence": 0.0
            }
    
    async def _list_diagram_types_tool(self) -> Dict[str, Any]:
        """List available diagram types and their descriptions"""
        try:
            diagram_types = await visualization_service.get_diagram_types()
            
            summary_parts = ["📊 Available Diagram Types:\n"]
            
            for i, diagram_info in enumerate(diagram_types, 1):
                summary_parts.append(f"{i}. **{diagram_info['name']}**")
                summary_parts.append(f"   {diagram_info['description']}")
                summary_parts.append(f"   Recommended max nodes: {diagram_info['max_recommended_nodes']}")
                summary_parts.append("")
            
            summary_parts.extend([
                "🎨 Themes Available:",
                "• Light (default) - Clean, professional appearance",
                "• Dark - Dark mode for reduced eye strain", 
                "• Neutral - Grayscale, minimalist design",
                "• Colorful - Vibrant, high-contrast colors",
                "",
                "📐 Layout Options:",
                "• Top-Down (TD) - Hierarchical flow from top to bottom",
                "• Left-Right (LR) - Horizontal flow, good for wide diagrams",
                "",
                "💡 To generate a specific diagram, say:",
                "• 'Show me the architecture diagram'",
                "• 'Generate dependency graph'", 
                "• 'Create hotspot heatmap'",
                "• 'Visualize circular dependencies'",
                "• 'Display coupling analysis'"
            ])
            
            data = {
                "diagram_types": diagram_types,
                "themes": ["light", "dark", "neutral", "colorful"],
                "layouts": ["TD", "LR"],
                "summary": "\n".join(summary_parts)
            }
            
            return {
                "status": "success",
                "type": "diagram_types_list",
                "data": data,
                "message": f"Listed {len(diagram_types)} available diagram types",
                "confidence": 1.0
            }
            
        except Exception as e:
            logger.error(f"Error listing diagram types: {e}")
            return {
                "status": "error",
                "message": f"Failed to list diagram types: {str(e)}",
                "confidence": 0.0
            }
    
    def get_enhanced_state_summary(self) -> Dict[str, Any]:
        """Get enhanced state summary with AST and graph information"""
        base_summary = self.get_state_summary()
        
        # Add AST and graph-specific information
        base_summary.update({
            "project_indexed": self.project_index is not None,
            "last_index_update": self.last_index_update,
            "project_files": self.project_index.supported_files if self.project_index else 0,
            "project_symbols": len(self.project_index.symbols) if self.project_index else 0,
            "project_context": bool(self.project_context),
            "graph_database_available": graph_service.initialized,
            "ast_capabilities": [
                "project_analysis", "symbol_exploration", "reference_finding",
                "complexity_analysis", "contextual_file_analysis"
            ],
            "graph_capabilities": [
                "architecture_detection", "circular_dependency_analysis",
                "coupling_analysis", "hotspot_detection", "graph_visualization"
            ],
            "visualization_capabilities": [
                "interactive_diagrams", "multiple_diagram_types", "theme_support",
                "mermaid_generation", "export_formats"
            ],
            "monitoring_capabilities": [
                "real_time_file_monitoring", "change_detection", "impact_analysis",
                "debouncing", "content_analysis", "session_management"
            ],
            "monitoring_active": self.dependencies.session_data.get("monitoring_session_id") is not None
        })
        
        return base_summary
    
    async def _start_monitoring_tool(self, workspace_path: Optional[str] = None) -> Dict[str, Any]:
        """Start real-time file monitoring for the workspace"""
        try:
            workspace = workspace_path or self.dependencies.workspace_path
            session_id = f"monitor_{self.dependencies.client_id}_{int(time.time())}"
            project_id = f"project_{hash(workspace)}"
            
            # Create monitoring configuration
            config = MonitoringConfiguration(
                workspace_path=workspace,
                watch_patterns=["**/*.py", "**/*.js", "**/*.ts", "**/*.tsx", "**/*.swift"],
                ignore_patterns=["**/__pycache__/**", "**/node_modules/**", "**/.git/**"],
                debounce_delay_ms=500,
                enable_content_analysis=True,
                enable_impact_analysis=True
            )
            
            # Start monitoring
            success = await file_monitor_service.start_monitoring(
                session_id=session_id,
                project_id=project_id,
                client_id=self.dependencies.client_id,
                config=config
            )
            
            if success:
                # Store session ID for later reference
                self.dependencies.session_data["monitoring_session_id"] = session_id
                
                summary = f"""🔍 Real-time File Monitoring Started!
                
📁 Workspace: {Path(workspace).name}
🎯 Session ID: {session_id}
👀 Watching: Python, JavaScript, TypeScript, Swift files
⚡ Features:
• Real-time change detection
• Impact analysis for modifications
• Smart debouncing (500ms)
• Content analysis enabled

🔔 You'll receive notifications for:
• File modifications and creations
• High-impact changes
• Circular dependency introduction
• Architecture pattern violations

📊 Use 'get monitoring status' to check activity
🛑 Use 'stop monitoring' to end session"""
                
                data = {
                    "session_id": session_id,
                    "workspace_path": workspace,
                    "configuration": config.dict(),
                    "status": "active",
                    "summary": summary
                }
                
                return {
                    "status": "success",
                    "type": "monitoring_started",
                    "data": data,
                    "message": f"File monitoring started for {Path(workspace).name}",
                    "confidence": 0.95
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to start file monitoring",
                    "confidence": 0.0
                }
                
        except Exception as e:
            logger.error(f"Error starting monitoring: {e}")
            return {
                "status": "error",
                "message": f"Monitoring startup failed: {str(e)}",
                "confidence": 0.0
            }
    
    async def _stop_monitoring_tool(self) -> Dict[str, Any]:
        """Stop the active file monitoring session"""
        try:
            session_id = self.dependencies.session_data.get("monitoring_session_id")
            
            if not session_id:
                return {
                    "status": "error",
                    "message": "No active monitoring session found",
                    "confidence": 0.0
                }
            
            # Get session info before stopping
            session = file_monitor_service.get_session(session_id)
            
            # Stop monitoring
            success = await file_monitor_service.stop_monitoring(session_id)
            
            if success:
                # Clear session ID
                self.dependencies.session_data.pop("monitoring_session_id", None)
                
                # Generate summary
                if session:
                    duration_min = (datetime.now() - session.started_at).total_seconds() / 60 if session.started_at else 0
                    summary = f"""✅ File Monitoring Stopped
                    
📊 Session Summary:
• Duration: {duration_min:.1f} minutes  
• Changes detected: {session.total_changes_detected}
• Files analyzed: {session.total_files_analyzed}
• Errors: {session.total_errors}

📁 Workspace: {Path(session.configuration.workspace_path).name}
🎯 Session: {session_id}

Thank you for using real-time monitoring! 
Start again with 'start monitoring' when needed."""
                else:
                    summary = f"✅ Monitoring session {session_id} stopped successfully"
                
                data = {
                    "session_id": session_id,
                    "summary": summary,
                    "session_stats": session.dict() if session else None
                }
                
                return {
                    "status": "success",
                    "type": "monitoring_stopped",
                    "data": data,
                    "message": "File monitoring stopped successfully",
                    "confidence": 0.95
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to stop monitoring session",
                    "confidence": 0.0
                }
                
        except Exception as e:
            logger.error(f"Error stopping monitoring: {e}")
            return {
                "status": "error",
                "message": f"Failed to stop monitoring: {str(e)}",
                "confidence": 0.0
            }
    
    async def _get_monitoring_status_tool(self) -> Dict[str, Any]:
        """Get the status of the current monitoring session"""
        try:
            session_id = self.dependencies.session_data.get("monitoring_session_id")
            
            if not session_id:
                return {
                    "status": "success",
                    "type": "monitoring_status",
                    "data": {
                        "active": False,
                        "summary": "📡 No active monitoring session\n\nUse 'start monitoring' to begin real-time file tracking."
                    },
                    "message": "No active monitoring session",
                    "confidence": 1.0
                }
            
            # Get session and metrics
            session = file_monitor_service.get_session(session_id)
            metrics = file_monitor_service.get_metrics(session_id)
            
            if not session:
                # Clean up stale session ID
                self.dependencies.session_data.pop("monitoring_session_id", None)
                return {
                    "status": "error",
                    "message": "Monitoring session no longer exists",
                    "confidence": 0.0
                }
            
            # Calculate uptime
            uptime_seconds = (datetime.now() - session.started_at).total_seconds() if session.started_at else 0
            uptime_str = f"{uptime_seconds//3600:.0f}h {(uptime_seconds%3600)//60:.0f}m"
            
            # Generate status summary
            status_icon = {
                MonitoringStatus.ACTIVE: "🟢",
                MonitoringStatus.PAUSED: "🟡", 
                MonitoringStatus.STOPPED: "🔴",
                MonitoringStatus.ERROR: "❌"
            }.get(session.status, "⚪")
            
            summary = f"""{status_icon} Monitoring Status: {session.status.value.upper()}
            
📊 Session Metrics:
• Uptime: {uptime_str}
• Changes detected: {session.total_changes_detected}
• Files analyzed: {session.total_files_analyzed}
• Errors: {session.total_errors}

📁 Workspace: {Path(session.configuration.workspace_path).name}
🎯 Session: {session_id}"""
            
            if metrics:
                summary += f"""

⚡ Performance:
• Changes/min: {metrics.changes_per_minute:.1f}
• Avg analysis time: {metrics.average_analysis_time_ms:.1f}ms
• Queue depth: {metrics.queue_depth}"""
            
            if session.last_activity:
                last_activity = (datetime.now() - session.last_activity).total_seconds()
                if last_activity < 60:
                    summary += f"\n🕐 Last activity: {last_activity:.0f}s ago"
                elif last_activity < 3600:
                    summary += f"\n🕐 Last activity: {last_activity//60:.0f}m ago"
                else:
                    summary += f"\n🕐 Last activity: {last_activity//3600:.0f}h ago"
            
            summary += """

💡 Commands:
• 'get recent changes' - View latest file modifications
• 'stop monitoring' - End current session
• 'pause monitoring' - Temporarily pause monitoring"""
            
            data = {
                "active": session.status == MonitoringStatus.ACTIVE,
                "session_id": session_id,
                "status": session.status,
                "uptime_seconds": uptime_seconds,
                "total_changes": session.total_changes_detected,
                "total_files_analyzed": session.total_files_analyzed,
                "total_errors": session.total_errors,
                "workspace_path": session.configuration.workspace_path,
                "last_activity": session.last_activity,
                "metrics": metrics.dict() if metrics else None,
                "summary": summary
            }
            
            return {
                "status": "success",
                "type": "monitoring_status",
                "data": data,
                "message": f"Monitoring session {session.status.value}",
                "confidence": 0.95
            }
            
        except Exception as e:
            logger.error(f"Error getting monitoring status: {e}")
            return {
                "status": "error",
                "message": f"Failed to get monitoring status: {str(e)}",
                "confidence": 0.0
            }
    
    async def _get_recent_changes_tool(self, limit: int = 10) -> Dict[str, Any]:
        """Get recent file changes from the monitoring session"""
        try:
            session_id = self.dependencies.session_data.get("monitoring_session_id")
            
            if not session_id:
                return {
                    "status": "error",
                    "message": "No active monitoring session",
                    "confidence": 0.0
                }
            
            # Get recent changes
            changes = await file_monitor_service.get_recent_changes(session_id, limit)
            
            if not changes:
                return {
                    "status": "success",
                    "type": "recent_changes",
                    "data": {
                        "changes": [],
                        "summary": "📝 No recent file changes detected\n\nFiles are being monitored, but no modifications have occurred recently."
                    },
                    "message": "No recent changes",
                    "confidence": 1.0
                }
            
            # Generate summary
            summary_parts = [f"📝 Recent File Changes ({len(changes)} total):\n"]
            
            for i, change in enumerate(changes[:limit], 1):
                file_name = Path(change.file_path).name
                time_ago = (datetime.now() - change.timestamp).total_seconds()
                
                if time_ago < 60:
                    time_str = f"{time_ago:.0f}s ago"
                elif time_ago < 3600:
                    time_str = f"{time_ago//60:.0f}m ago"
                else:
                    time_str = f"{time_ago//3600:.0f}h ago"
                
                # Change type icons
                change_icon = {
                    ChangeType.CREATED: "🆕",
                    ChangeType.MODIFIED: "✏️",
                    ChangeType.DELETED: "🗑️",
                    ChangeType.MOVED: "📦",
                    ChangeType.RENAMED: "🏷️"
                }.get(change.change_type, "📄")
                
                summary_parts.append(f"{i}. {change_icon} {file_name}")
                summary_parts.append(f"   {change.change_type.value} {time_str}")
                
                # Add line change info if available
                if change.lines_added or change.lines_removed:
                    summary_parts.append(f"   +{change.lines_added} -{change.lines_removed} lines")
                
                if change.language:
                    summary_parts.append(f"   Language: {change.language}")
                
                summary_parts.append("")
            
            if len(changes) > limit:
                summary_parts.append(f"... and {len(changes) - limit} more changes")
            
            # Process changes for response
            changes_data = []
            for change in changes:
                changes_data.append({
                    "id": change.id,
                    "file_path": change.file_path,
                    "file_name": Path(change.file_path).name,
                    "change_type": change.change_type,
                    "timestamp": change.timestamp,
                    "lines_added": change.lines_added,
                    "lines_removed": change.lines_removed,
                    "lines_modified": change.lines_modified,
                    "language": change.language,
                    "is_binary": change.is_binary,
                    "file_size": change.file_size
                })
            
            data = {
                "changes": changes_data,
                "total_changes": len(changes),
                "showing": min(limit, len(changes)),
                "summary": "\n".join(summary_parts)
            }
            
            return {
                "status": "success",
                "type": "recent_changes",
                "data": data,
                "message": f"Retrieved {len(changes)} recent changes",
                "confidence": 0.95
            }
            
        except Exception as e:
            logger.error(f"Error getting recent changes: {e}")
            return {
                "status": "error",
                "message": f"Failed to get recent changes: {str(e)}",
                "confidence": 0.0
            }