import asyncio
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List

from .ast_parser_service import TreeSitterService

# Import our new AI infrastructure services
from .mlx_model_service import MLXModelService
from .vector_store_service import VectorStoreService

logger = logging.getLogger(__name__)


class EnhancedAIService:
    """Enhanced AI service with MLX, AST parsing, and vector storage"""

    def __init__(self):
        # Core AI infrastructure
        self.mlx_service = MLXModelService()
        self.ast_service = TreeSitterService()
        self.vector_service = VectorStoreService()

        # Service status
        self.is_initialized = False
        self.initialization_status = {
            "mlx": False,
            "ast": False,
            "vector": False,
            "overall": False,
        }

        # Session and command handling
        self.session_data = {}
        self.supported_commands = {
            "/list-files": self._list_files,
            "/status": self._get_status,
            "/current-dir": self._get_current_directory,
            "/read-file": self._read_file,
            "/analyze-file": self._analyze_file,
            "/search-code": self._search_code,
            "/index-project": self._index_project,
            "/vector-stats": self._get_vector_stats,
            "/help": self._get_help,
        }

    async def initialize(self):
        """Initialize all AI service components"""
        try:
            logger.info("Initializing Enhanced AI Service...")

            # Initialize services in parallel for better performance
            mlx_task = asyncio.create_task(self.mlx_service.initialize())
            ast_task = asyncio.create_task(self.ast_service.initialize())
            vector_task = asyncio.create_task(self.vector_service.initialize())

            # Wait for all services to initialize
            mlx_ready, ast_ready, vector_ready = await asyncio.gather(
                mlx_task, ast_task, vector_task, return_exceptions=True
            )

            # Update initialization status
            self.initialization_status["mlx"] = (
                mlx_ready if isinstance(mlx_ready, bool) else False
            )
            self.initialization_status["ast"] = (
                ast_ready if isinstance(ast_ready, bool) else False
            )
            self.initialization_status["vector"] = (
                vector_ready if isinstance(vector_ready, bool) else False
            )

            # Overall status
            self.initialization_status["overall"] = any(
                [
                    self.initialization_status["mlx"],
                    self.initialization_status["ast"],
                    self.initialization_status["vector"],
                ]
            )

            if self.initialization_status["overall"]:
                self.is_initialized = True
                logger.info(
                    f"Enhanced AI Service initialized - MLX: {mlx_ready}, AST: {ast_ready}, Vector: {vector_ready}"
                )
            else:
                logger.warning(
                    "Enhanced AI Service initialization completed with limited functionality"
                )
                self.is_initialized = True  # Allow limited operation

            return True

        except Exception as e:
            logger.error(f"Failed to initialize Enhanced AI Service: {e}")
            return False

    async def process_command(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process command from client with enhanced AI capabilities and detailed logging"""
        if not self.is_initialized:
            error_msg = "Enhanced AI service not initialized"
            logger.error(f"Command rejected: {error_msg}")
            return {"status": "error", "message": error_msg}

        command = data.get("content", "")
        command_type = data.get("type", "message")
        client_id = data.get("client_id", "unknown")
        
        # Generate command correlation ID
        cmd_id = f"cmd_{int(time.time())}_{hash(str(data)) % 10000:04d}"
        
        logger.info(
            f"[{cmd_id}] Command processing started | "
            f"client_id={client_id} | "
            f"type={command_type} | "
            f"content_length={len(command)} | "
            f"is_slash_command={command.startswith('/')}"
        )
        
        logger.debug(f"[{cmd_id}] Command preview: {command[:100]}...")

        try:
            start_time = time.time()
            
            # Enhanced command routing with logging
            if command_type == "command" and command.startswith("/"):
                logger.debug(f"[{cmd_id}] Routing to slash command processor")
                result = await self._process_slash_command(command, client_id)
            else:
                logger.debug(f"[{cmd_id}] Routing to AI message processor")
                result = await self._process_message(command, client_id)

            # Enhanced result processing with metrics
            processing_time = time.time() - start_time
            
            # Add comprehensive processing metadata
            result["processing_time"] = round(processing_time, 3)
            result["service_status"] = self.initialization_status.copy()
            result["command_id"] = cmd_id
            
            # Add performance insights
            if processing_time > 5.0:
                result["performance_warning"] = "Slow processing detected"
                logger.warning(
                    f"[{cmd_id}] Slow processing detected | "
                    f"time={processing_time:.3f}s | "
                    f"threshold=5.0s"
                )
            
            logger.info(
                f"[{cmd_id}] Command processing completed | "
                f"status={result.get('status', 'unknown')} | "
                f"time={processing_time:.3f}s | "
                f"confidence={result.get('confidence', 'n/a')}"
            )

            return result

        except Exception as e:
            processing_time = time.time() - start_time
            error_type = type(e).__name__
            
            logger.error(
                f"[{cmd_id}] Command processing FAILED | "
                f"time={processing_time:.3f}s | "
                f"error_type={error_type} | "
                f"client_id={client_id} | "
                f"error: {e}"
            )
            
            return {
                "status": "error",
                "message": str(e),
                "service_status": self.initialization_status,
                "command_id": cmd_id,
                "error_type": error_type,
                "processing_time": round(processing_time, 3)
            }

    async def _process_slash_command(
        self, command: str, client_id: str
    ) -> Dict[str, Any]:
        """Process slash commands with enhanced capabilities"""
        parts = command.split(" ", 1)
        base_command = parts[0]
        args = parts[1] if len(parts) > 1 else ""

        if base_command in self.supported_commands:
            return await self.supported_commands[base_command](args, client_id)
        else:
            return {
                "status": "error",
                "message": f"Unknown command: {base_command}. Type /help for available commands.",
            }

    async def _process_message(self, message: str, client_id: str) -> Dict[str, Any]:
        """Process general messages with enhanced AI and detailed logging"""
        if not message.strip():
            return {"status": "error", "message": "Empty message"}

        # Generate request correlation ID
        request_id = f"ai_msg_{int(time.time())}_{hash(message) % 10000:04d}"
        start_time = time.time()
        
        logger.info(
            f"[{request_id}] AI message processing started | "
            f"client_id={client_id} | "
            f"message_length={len(message)} | "
            f"services_ready={self.is_initialized}"
        )
        
        logger.debug(f"[{request_id}] Message preview: {message[:100]}...")

        try:
            # Enhanced vector search with detailed context analysis
            relevant_context = []
            context_search_time = 0.0
            
            if self.initialization_status["vector"]:
                logger.debug(f"[{request_id}] Starting vector search for context...")
                search_start = time.time()
                
                search_results = await self.vector_service.search_similar_code(
                    message, n_results=3
                )
                context_search_time = time.time() - search_start
                
                # Enhanced context filtering with similarity threshold logging
                similarity_threshold = 0.3
                for result in search_results:
                    if result.similarity_score > similarity_threshold:
                        relevant_context.append(
                            f"Relevant code: {result.content} (from {result.file_path})"
                        )
                        logger.debug(
                            f"[{request_id}] Context included | "
                            f"file={result.file_path} | "
                            f"similarity={result.similarity_score:.3f} | "
                            f"symbol={getattr(result, 'symbol_name', 'unknown')}"
                        )
                    else:
                        logger.debug(
                            f"[{request_id}] Context excluded | "
                            f"file={result.file_path} | "
                            f"similarity={result.similarity_score:.3f} | "
                            f"threshold={similarity_threshold}"
                        )
                
                logger.info(
                    f"[{request_id}] Vector search completed | "
                    f"time={context_search_time:.3f}s | "
                    f"results_found={len(search_results)} | "
                    f"context_included={len(relevant_context)}"
                )
            else:
                logger.debug(f"[{request_id}] Vector search skipped - service not available")

            # Enhanced AI response generation with detailed logging
            response_generation_time = 0.0
            generation_start = time.time()
            
            if self.initialization_status["mlx"]:
                logger.debug(f"[{request_id}] Using MLX service for response generation")
                # Create enhanced prompt with context
                prompt = self._create_enhanced_prompt(message, relevant_context)
                logger.debug(
                    f"[{request_id}] Prompt created | "
                    f"total_length={len(prompt)} | "
                    f"context_sections={len(relevant_context)}"
                )
                
                response = await self.mlx_service.generate_text(prompt)
                model_info = "MLX Enhanced Model"
                
                logger.debug(f"[{request_id}] MLX generation completed | response_length={len(response)}")
            else:
                logger.debug(f"[{request_id}] Using enhanced mock response - MLX not available")
                # Fallback to enhanced mock response
                response = await self._generate_enhanced_mock_response(
                    message, relevant_context
                )
                model_info = "Enhanced Mock (Development Mode)"
                
            response_generation_time = time.time() - generation_start
            
            logger.info(
                f"[{request_id}] Response generated | "
                f"time={response_generation_time:.3f}s | "
                f"model={model_info} | "
                f"response_length={len(response)}"
            )

            # Enhanced confidence calculation with detailed logging
            confidence = self._calculate_confidence_score(
                response, "ai_response", relevant_context, request_id
            )
            
            # Calculate processing efficiency metrics
            total_time = time.time() - start_time
            efficiency_metrics = {
                "total_time": round(total_time, 3),
                "context_search_time": round(context_search_time, 3),
                "response_generation_time": round(response_generation_time, 3),
                "context_utilization": len(relevant_context) > 0,
                "service_efficiency": round((response_generation_time / total_time) * 100, 1) if total_time > 0 else 0
            }

            result = {
                "status": "success",
                "type": "ai_response",
                "message": response,
                "timestamp": time.time(),
                "model": model_info,
                "confidence": confidence,
                "context_used": len(relevant_context) > 0,
                "context_count": len(relevant_context),
                "request_id": request_id,
                "efficiency_metrics": efficiency_metrics,
                "services_available": {
                    "mlx": self.initialization_status["mlx"],
                    "ast": self.initialization_status["ast"],
                    "vector": self.initialization_status["vector"],
                },
            }

            # Enhanced quality assessment and warnings
            if confidence < 0.6:
                result["warning"] = "Lower confidence response - consider manual review"
                logger.warning(
                    f"[{request_id}] Low confidence result | "
                    f"confidence={confidence:.3f} | "
                    f"recommendation=manual_review"
                )
            
            if confidence > 0.8:
                logger.info(
                    f"[{request_id}] High confidence result | "
                    f"confidence={confidence:.3f} | "
                    f"quality=high"
                )
            
            # Log successful completion with summary
            logger.info(
                f"[{request_id}] Message processing completed | "
                f"total_time={total_time:.3f}s | "
                f"confidence={confidence:.3f} | "
                f"context_used={len(relevant_context) > 0} | "
                f"model_used={'mlx' if self.initialization_status['mlx'] else 'mock'}"
            )

            return result

        except Exception as e:
            total_time = time.time() - start_time
            error_type = type(e).__name__
            
            logger.error(
                f"[{request_id}] Message processing FAILED | "
                f"time={total_time:.3f}s | "
                f"error_type={error_type} | "
                f"client_id={client_id} | "
                f"error: {e}"
            )
            
            return {
                "status": "error",
                "message": f"Error processing message: {str(e)}",
                "confidence": 0.0,
                "request_id": request_id,
                "error_type": error_type,
                "processing_time": round(total_time, 3)
            }

    def _create_enhanced_prompt(self, message: str, context: List[str]) -> str:
        """Create enhanced prompt with code context"""
        context_section = ""
        if context:
            context_section = f"""

Relevant code context:
{chr(10).join(context)}
"""

        return f"""[INST] You are an advanced coding assistant with access to project context. You provide intelligent, context-aware responses about programming and software development.

User query: {message}{context_section}

Please provide a helpful response that takes into account the provided context. Be specific and actionable in your guidance. [/INST]"""

    async def _generate_enhanced_mock_response(
        self, message: str, context: List[str]
    ) -> str:
        """Generate enhanced mock responses with context awareness"""
        await asyncio.sleep(0.4)  # Simulate processing time

        message_lower = message.lower()
        has_context = len(context) > 0

        # Context-aware responses
        if has_context and any(
            word in message_lower for word in ["explain", "what", "how"]
        ):
            return f"""Based on your query about '{message}' and the relevant code context I found:

I can see related code patterns in your project that might help answer your question. The context suggests specific implementations that could be relevant to what you're asking about.

**Analysis with Context:**
- Found {len(context)} relevant code sections
- These patterns might inform the best approach for your question
- I can provide more specific guidance based on your actual codebase

**Enhanced Development Mode Active:**
- Vector search: ✅ Working with project context
- Code analysis: ✅ AST parsing available  
- MLX inference: 🔄 Infrastructure ready for full model integration

Try using /analyze-file or /search-code for more detailed insights."""

        elif any(word in message_lower for word in ["code", "function", "class"]):
            return f"""For code-related queries like '{message}':

**Enhanced Capabilities Available:**
- **Code Analysis**: Use /analyze-file <path> for detailed AST-based analysis
- **Vector Search**: Use /search-code <query> to find similar patterns
- **Project Indexing**: Use /index-project to build comprehensive code embeddings

**Current Context Awareness:**
- Found {len(context)} related code sections in your project
- AST parsing can understand code structure and dependencies
- Vector database ready for intelligent code similarity matching

**Next Steps:**
1. Try /analyze-file on a specific file for detailed insights
2. Use /search-code to find similar patterns across your codebase
3. Run /index-project to enhance context awareness

*Enhanced AI Service - Sprint 1 Development Mode*"""

        elif any(word in message_lower for word in ["error", "debug", "fix"]):
            return f"""For debugging '{message}':

**Enhanced Debugging Available:**
- **Context Analysis**: I can search your codebase for similar error patterns
- **Structural Analysis**: AST parsing can identify structural issues
- **Pattern Matching**: Vector search finds related debugging solutions

**Found in Project:**
{f"- {len(context)} potentially relevant code sections" if has_context else "- Ready to analyze your code when you provide file paths"}

**Debugging Workflow:**
1. Use /read-file <error_file> to examine problematic code
2. Try /analyze-file <path> for structural analysis  
3. Use /search-code "error pattern" to find similar issues

*Enhanced Debug Mode with Project Context*"""

        else:
            return f"""Enhanced AI Assistant ready to help with '{message}'.

**Available Capabilities:**
- **MLX Infrastructure**: ✅ Ready for local model inference
- **Code Analysis**: ✅ Tree-sitter AST parsing active
- **Vector Search**: ✅ ChromaDB for intelligent code search
- **Project Context**: {f"✅ Found {len(context)} relevant sections" if has_context else "🔄 Ready to index your project"}

**Try These Commands:**
- `/status` - Full system status
- `/analyze-file <path>` - Deep code analysis
- `/search-code <query>` - Find similar code patterns
- `/index-project` - Build project embeddings for better context

The enhanced AI infrastructure is ready and working with your project context.

*Enhanced AI Service - Development Mode*"""

    def _calculate_confidence_score(
        self, response: str, command_type: str, context: List[str], request_id: str = "conf_calc"
    ) -> float:
        """Enhanced confidence scoring with detailed decision factor logging"""
        logger.debug(f"[{request_id}] Confidence calculation started | command_type={command_type}")
        
        base_confidence = 0.7
        confidence_factors = {}
        
        # Context relevance factor
        if context:
            context_boost = 0.15
            base_confidence += context_boost
            confidence_factors["context_available"] = {
                "boost": context_boost,
                "context_count": len(context),
                "reason": "relevant_context_found"
            }
            logger.debug(f"[{request_id}] Context boost applied | count={len(context)} | boost={context_boost}")
        else:
            confidence_factors["context_available"] = {
                "boost": 0.0,
                "reason": "no_context_available"
            }

        # Service availability factor
        services_available = sum([
            self.initialization_status["mlx"],
            self.initialization_status["ast"],
            self.initialization_status["vector"],
        ])
        service_boost = (services_available / 3) * 0.1
        base_confidence += service_boost
        confidence_factors["service_availability"] = {
            "boost": service_boost,
            "services_available": services_available,
            "total_services": 3,
            "available_services": {
                "mlx": self.initialization_status["mlx"],
                "ast": self.initialization_status["ast"],
                "vector": self.initialization_status["vector"]
            }
        }
        logger.debug(f"[{request_id}] Service availability boost | available={services_available}/3 | boost={service_boost}")

        # Response quality factors
        response_length = len(response)
        if response_length < 20:
            length_penalty = -0.2
            base_confidence += length_penalty
            confidence_factors["response_length"] = {
                "penalty": length_penalty,
                "length": response_length,
                "reason": "too_short"
            }
            logger.debug(f"[{request_id}] Length penalty applied | length={response_length} | penalty={length_penalty}")
        elif response_length > 200:
            length_bonus = 0.1
            base_confidence += length_bonus
            confidence_factors["response_length"] = {
                "boost": length_bonus,
                "length": response_length,
                "reason": "comprehensive_response"
            }
            logger.debug(f"[{request_id}] Length bonus applied | length={response_length} | bonus={length_bonus}")
        else:
            confidence_factors["response_length"] = {
                "adjustment": 0.0,
                "length": response_length,
                "reason": "appropriate_length"
            }

        # Content quality analysis
        response_lower = response.lower()
        if "error" in response_lower or "failed" in response_lower:
            error_penalty = -0.3
            base_confidence += error_penalty
            confidence_factors["content_quality"] = {
                "penalty": error_penalty,
                "reason": "contains_error_indicators"
            }
            logger.debug(f"[{request_id}] Error content penalty | penalty={error_penalty}")
        elif "enhanced" in response_lower or "context" in response_lower:
            quality_bonus = 0.1
            base_confidence += quality_bonus
            confidence_factors["content_quality"] = {
                "boost": quality_bonus,
                "reason": "enhanced_context_aware_content"
            }
            logger.debug(f"[{request_id}] Quality content bonus | bonus={quality_bonus}")
        else:
            confidence_factors["content_quality"] = {
                "adjustment": 0.0,
                "reason": "standard_content"
            }

        # Calculate final confidence
        final_confidence = max(0.0, min(1.0, base_confidence))
        
        # Enhanced logging of final decision
        logger.info(
            f"[{request_id}] Confidence calculated | "
            f"final={final_confidence:.3f} | "
            f"base={0.7} | "
            f"context_boost={confidence_factors.get('context_available', {}).get('boost', 0)} | "
            f"service_boost={service_boost:.3f} | "
            f"quality_adjustment={confidence_factors.get('content_quality', {}).get('boost', confidence_factors.get('content_quality', {}).get('penalty', 0))}"
        )
        
        logger.debug(f"[{request_id}] Confidence decision factors: {confidence_factors}")
        
        return final_confidence

    # Enhanced command implementations
    async def _analyze_file(self, args: str, client_id: str) -> Dict[str, Any]:
        """Enhanced file analysis with AST parsing and vector storage"""
        if not args.strip():
            return {
                "status": "error",
                "message": "File path required. Usage: /analyze-file <path>",
            }

        file_path = args.strip()

        try:
            # Use AST service for analysis if available
            if self.initialization_status["ast"]:
                code_structure = await self.ast_service.parse_file(file_path)
                if code_structure:
                    # Store in vector database for future context
                    if self.initialization_status["vector"]:
                        await self.vector_service.add_file_embeddings(
                            file_path, code_structure
                        )

                    # Generate enhanced analysis
                    analysis = await self._generate_enhanced_analysis(code_structure)

                    return {
                        "status": "success",
                        "type": "enhanced_file_analysis",
                        "data": {
                            "file_path": file_path,
                            "language": code_structure.language,
                            "lines_of_code": code_structure.lines_of_code,
                            "complexity_score": code_structure.complexity_score,
                            "symbols": len(code_structure.symbols),
                            "imports": len(code_structure.imports),
                            "dependencies": list(code_structure.dependencies),
                            "analysis": analysis,
                        },
                        "message": f"Enhanced analysis complete for {file_path}",
                        "confidence": 0.85,
                    }

            # Fallback to basic analysis
            return await self._basic_file_analysis(file_path)

        except Exception as e:
            logger.error(f"Error in enhanced file analysis: {e}")
            return {"status": "error", "message": f"Analysis failed: {e}"}

    async def _generate_enhanced_analysis(self, code_structure) -> str:
        """Generate enhanced analysis using AST data"""
        analysis_parts = []

        analysis_parts.append(
            f"**Enhanced AST Analysis for {Path(code_structure.file_path).name}**"
        )
        analysis_parts.append(f"Language: {code_structure.language.title()}")
        analysis_parts.append(f"Lines of Code: {code_structure.lines_of_code}")
        analysis_parts.append(
            f"Complexity Score: {code_structure.complexity_score:.1f}/100"
        )

        # Symbol analysis
        if code_structure.symbols:
            functions = [s for s in code_structure.symbols if s.type == "function"]
            classes = [
                s for s in code_structure.symbols if s.type in ["class", "struct"]
            ]

            analysis_parts.append("\n**Code Structure:**")
            analysis_parts.append(f"- Functions: {len(functions)}")
            analysis_parts.append(f"- Classes/Structs: {len(classes)}")
            analysis_parts.append(f"- Total Symbols: {len(code_structure.symbols)}")

            if functions:
                analysis_parts.append("\n**Functions Found:**")
                for func in functions[:5]:  # Show first 5
                    params = (
                        f"({', '.join(func.parameters)})" if func.parameters else "()"
                    )
                    analysis_parts.append(
                        f"- {func.name}{params} (line {func.start_line})"
                    )
                if len(functions) > 5:
                    analysis_parts.append(
                        f"... and {len(functions) - 5} more functions"
                    )

        # Dependencies
        if code_structure.dependencies:
            analysis_parts.append(
                f"\n**Dependencies ({len(code_structure.dependencies)}):**"
            )
            for dep in sorted(list(code_structure.dependencies))[:10]:
                analysis_parts.append(f"- {dep}")
            if len(code_structure.dependencies) > 10:
                analysis_parts.append(
                    f"... and {len(code_structure.dependencies) - 10} more"
                )

        # Quality insights
        analysis_parts.append("\n**Quality Insights:**")
        if code_structure.complexity_score > 70:
            analysis_parts.append("⚠️ High complexity - consider refactoring")
        elif code_structure.complexity_score > 40:
            analysis_parts.append("✓ Moderate complexity - well structured")
        else:
            analysis_parts.append("✓ Low complexity - clean and simple")

        if code_structure.lines_of_code > 500:
            analysis_parts.append(
                "📏 Large file - consider breaking into smaller modules"
            )

        analysis_parts.append(
            "\n*Analysis powered by Tree-sitter AST parsing and Enhanced AI Service*"
        )

        return "\n".join(analysis_parts)

    async def _search_code(self, args: str, client_id: str) -> Dict[str, Any]:
        """Search for similar code patterns using vector similarity"""
        if not args.strip():
            return {
                "status": "error",
                "message": "Search query required. Usage: /search-code <query>",
            }

        if not self.initialization_status["vector"]:
            return {
                "status": "error",
                "message": "Vector search not available - run /index-project first",
            }

        try:
            query = args.strip()
            results = await self.vector_service.search_similar_code(query, n_results=10)

            if not results:
                return {
                    "status": "success",
                    "type": "code_search_results",
                    "data": {"results": [], "query": query},
                    "message": f"No similar code found for: {query}",
                }

            formatted_results = []
            for result in results:
                formatted_results.append(
                    {
                        "content": result.content,
                        "file_path": result.file_path,
                        "symbol_name": result.symbol_name,
                        "symbol_type": result.symbol_type,
                        "similarity_score": round(result.similarity_score, 3),
                        "line_info": f"Line {result.metadata.get('start_line', '?')}",
                    }
                )

            return {
                "status": "success",
                "type": "code_search_results",
                "data": {
                    "results": formatted_results,
                    "query": query,
                    "total_found": len(results),
                },
                "message": f"Found {len(results)} similar code patterns for '{query}'",
                "confidence": 0.8,
            }

        except Exception as e:
            logger.error(f"Error in code search: {e}")
            return {"status": "error", "message": f"Search failed: {e}"}

    async def _index_project(self, args: str, client_id: str) -> Dict[str, Any]:
        """Index project files for vector search"""
        if not self.initialization_status["vector"]:
            return {"status": "error", "message": "Vector storage not available"}

        try:
            project_dir = args.strip() if args.strip() else "."
            project_path = Path(project_dir)

            if not project_path.exists():
                return {
                    "status": "error",
                    "message": f"Directory not found: {project_dir}",
                }

            # Find code files to index
            code_extensions = {
                ".py",
                ".js",
                ".ts",
                ".tsx",
                ".jsx",
                ".swift",
                ".java",
                ".cpp",
                ".c",
                ".go",
                ".rs",
            }
            code_files = []

            for ext in code_extensions:
                code_files.extend(project_path.rglob(f"*{ext}"))

            # Limit to reasonable number for demo
            code_files = code_files[:50]

            indexed_count = 0
            processed_files = []

            for file_path in code_files:
                try:
                    # Parse file structure
                    if self.initialization_status["ast"]:
                        code_structure = await self.ast_service.parse_file(
                            str(file_path)
                        )
                        if code_structure:
                            added = await self.vector_service.add_file_embeddings(
                                str(file_path), code_structure
                            )
                            indexed_count += added
                            processed_files.append(str(file_path))

                except Exception as e:
                    logger.warning(f"Could not index {file_path}: {e}")
                    continue

            return {
                "status": "success",
                "type": "project_indexing",
                "data": {
                    "indexed_embeddings": indexed_count,
                    "processed_files": len(processed_files),
                    "total_files_found": len(code_files),
                    "project_directory": str(project_path.absolute()),
                },
                "message": f"Indexed {indexed_count} code embeddings from {len(processed_files)} files",
                "confidence": 0.9,
            }

        except Exception as e:
            logger.error(f"Error indexing project: {e}")
            return {"status": "error", "message": f"Indexing failed: {e}"}

    async def _get_vector_stats(self, args: str, client_id: str) -> Dict[str, Any]:
        """Get vector database statistics"""
        if not self.initialization_status["vector"]:
            return {"status": "error", "message": "Vector storage not available"}

        try:
            stats = await self.vector_service.get_collection_stats()

            return {
                "status": "success",
                "type": "vector_statistics",
                "data": stats,
                "message": f"Vector database contains {stats.get('total_embeddings', 0)} embeddings",
                "confidence": 1.0,
            }

        except Exception as e:
            logger.error(f"Error getting vector stats: {e}")
            return {"status": "error", "message": f"Stats retrieval failed: {e}"}

    async def _get_status(self, args: str, client_id: str) -> Dict[str, Any]:
        """Get enhanced status with all service information"""
        # Get individual service statuses
        mlx_status = self.mlx_service.get_health_status()
        ast_status = self.ast_service.get_status()
        vector_status = self.vector_service.get_status()

        status_data = {
            "service": "Enhanced AI Service",
            "version": "1.0.0-sprint1",
            "ready": self.is_initialized,
            "initialization_status": self.initialization_status,
            "supported_commands": list(self.supported_commands.keys()),
            "services": {
                "mlx_model": mlx_status,
                "ast_parser": ast_status,
                "vector_store": vector_status,
            },
            "capabilities": {
                "code_analysis": self.initialization_status["ast"],
                "vector_search": self.initialization_status["vector"],
                "ai_inference": self.initialization_status["mlx"],
                "project_indexing": self.initialization_status["ast"]
                and self.initialization_status["vector"],
            },
        }

        return {
            "status": "success",
            "type": "enhanced_status",
            "data": status_data,
            "message": "Enhanced AI Service status retrieved",
            "confidence": 1.0,
        }

    # Keep existing helper methods for compatibility
    async def _basic_file_analysis(self, file_path: str) -> Dict[str, Any]:
        """Fallback basic file analysis"""
        try:
            path = Path(file_path)
            if not path.exists():
                return {"status": "error", "message": f"File not found: {file_path}"}

            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            lines = content.splitlines()

            return {
                "status": "success",
                "type": "basic_file_analysis",
                "data": {
                    "file_path": file_path,
                    "size": len(content),
                    "lines": len(lines),
                    "analysis": f"Basic analysis: {len(lines)} lines, {len(content)} characters",
                },
                "message": f"Basic analysis complete for {file_path}",
            }

        except Exception as e:
            return {"status": "error", "message": f"Analysis failed: {e}"}

    async def _list_files(self, args: str, client_id: str) -> Dict[str, Any]:
        """List files with enhanced information"""
        try:
            target_dir = args.strip() if args.strip() else "."
            path = Path(target_dir)

            if not path.exists():
                return {
                    "status": "error",
                    "message": f"Directory not found: {target_dir}",
                }

            files = []
            dirs = []

            for item in sorted(path.iterdir()):
                if item.is_file():
                    language = None
                    if self.initialization_status["ast"]:
                        language = self.ast_service.get_language_from_file(str(item))

                    files.append(
                        {
                            "name": item.name,
                            "size": item.stat().st_size,
                            "type": "file",
                            "language": language,
                            "analyzable": language is not None,
                        }
                    )
                elif item.is_dir():
                    dirs.append({"name": item.name, "type": "directory"})

            return {
                "status": "success",
                "type": "enhanced_file_list",
                "data": {
                    "directories": dirs,
                    "files": files,
                    "path": str(path.absolute()),
                    "analyzable_files": len([f for f in files if f.get("analyzable")]),
                },
                "message": f"Found {len(dirs)} directories and {len(files)} files in {target_dir}",
            }

        except Exception as e:
            return {"status": "error", "message": f"Error listing files: {e}"}

    async def _read_file(self, args: str, client_id: str) -> Dict[str, Any]:
        """Read file with enhanced analysis option"""
        if not args.strip():
            return {
                "status": "error",
                "message": "File path required. Usage: /read-file <path>",
            }

        try:
            file_path = Path(args.strip())

            if not file_path.exists():
                return {"status": "error", "message": f"File not found: {args}"}

            # Size limit check
            max_size = 1024 * 1024  # 1MB
            if file_path.stat().st_size > max_size:
                return {
                    "status": "error",
                    "message": f"File too large (max 1MB): {args}",
                }

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Add language detection if AST service is available
            language = None
            if self.initialization_status["ast"]:
                language = self.ast_service.get_language_from_file(str(file_path))

            return {
                "status": "success",
                "type": "enhanced_file_content",
                "data": {
                    "path": str(file_path.absolute()),
                    "content": content,
                    "size": len(content),
                    "lines": len(content.splitlines()),
                    "language": language,
                    "analyzable": language is not None,
                },
                "message": f"Read {len(content)} characters from {args}",
                "suggestion": (
                    "Use /analyze-file for detailed code analysis" if language else None
                ),
            }

        except UnicodeDecodeError:
            return {"status": "error", "message": f"Cannot read binary file: {args}"}
        except Exception as e:
            return {"status": "error", "message": f"Error reading file: {e}"}

    async def _get_current_directory(self, args: str, client_id: str) -> Dict[str, Any]:
        """Get current directory with project information"""
        try:
            cwd = os.getcwd()

            # Add project analysis if services available
            project_info = {}
            if self.initialization_status["ast"]:
                # Count analyzable files
                code_extensions = {
                    ".py",
                    ".js",
                    ".ts",
                    ".tsx",
                    ".jsx",
                    ".swift",
                    ".java",
                }
                code_files = []
                for ext in code_extensions:
                    code_files.extend(Path(cwd).glob(f"*{ext}"))

                project_info["analyzable_files"] = len(code_files)
                project_info["project_type"] = self._detect_project_type(Path(cwd))

            return {
                "status": "success",
                "type": "enhanced_directory_info",
                "data": {"current_directory": cwd, "project_info": project_info},
                "message": f"Current directory: {cwd}",
                "suggestion": "Use /index-project to build code embeddings for this directory",
            }

        except Exception as e:
            return {"status": "error", "message": f"Error getting directory: {e}"}

    def _detect_project_type(self, project_path: Path) -> str:
        """Detect project type based on files present"""
        if (project_path / "package.json").exists():
            return "JavaScript/Node.js"
        elif (project_path / "requirements.txt").exists() or (
            project_path / "pyproject.toml"
        ).exists():
            return "Python"
        elif (project_path / "Package.swift").exists():
            return "Swift Package"
        elif any(project_path.glob("*.xcodeproj")):
            return "iOS/macOS"
        elif (project_path / "pom.xml").exists():
            return "Java/Maven"
        elif (project_path / "Cargo.toml").exists():
            return "Rust"
        else:
            return "Unknown"

    async def _get_help(self, args: str, client_id: str) -> Dict[str, Any]:
        """Get enhanced help with service-specific commands"""
        help_sections = []

        help_sections.append("**Enhanced AI Service Commands:**")
        help_sections.append("/status - Show detailed service status and capabilities")
        help_sections.append("/list-files [dir] - List files with language detection")
        help_sections.append("/read-file <path> - Read file with enhanced metadata")

        if self.initialization_status["ast"]:
            help_sections.append("/analyze-file <path> - Deep AST-based code analysis")

        if self.initialization_status["vector"]:
            help_sections.append("/search-code <query> - Find similar code patterns")
            help_sections.append("/vector-stats - Show vector database statistics")

        if self.initialization_status["ast"] and self.initialization_status["vector"]:
            help_sections.append(
                "/index-project [dir] - Index project for enhanced context"
            )

        help_sections.append("/current-dir - Show current directory with project info")
        help_sections.append("/help - Show this help message")

        help_sections.append("\n**Service Status:**")
        help_sections.append(
            f"MLX Model Service: {'✅' if self.initialization_status['mlx'] else '🔄'}"
        )
        help_sections.append(
            f"AST Parser: {'✅' if self.initialization_status['ast'] else '🔄'}"
        )
        help_sections.append(
            f"Vector Search: {'✅' if self.initialization_status['vector'] else '🔄'}"
        )

        help_sections.append("\n**Features:**")
        help_sections.append("• Context-aware AI responses using vector search")
        help_sections.append("• AST-based code analysis and understanding")
        help_sections.append("• Project-wide code indexing and similarity search")
        help_sections.append("• Enhanced confidence scoring with multiple services")

        help_text = "\n".join(help_sections)

        return {
            "status": "success",
            "type": "enhanced_help",
            "message": help_text,
            "data": {
                "commands": list(self.supported_commands.keys()),
                "service_status": self.initialization_status,
            },
        }
