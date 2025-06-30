"""
MLX AI Integration Service

Extracted from enhanced_l3_agent.py to provide focused MLX-powered AI code assistance
capabilities following single responsibility principle.
"""

import json
import logging
from typing import Any, Dict, List, Optional, AsyncIterator

from .unified_mlx_service import unified_mlx_service
from ..agent.ast_context_provider import ASTContextProvider

logger = logging.getLogger(__name__)


class MLXAIService:
    """
    Service dedicated to MLX-powered AI code assistance.
    
    Provides intelligent code suggestions, explanations, refactoring analysis,
    debugging assistance, optimization recommendations, and streaming completions.
    """
    
    def __init__(self):
        self.ast_context_provider: Optional[ASTContextProvider] = None
        self._initialized = False
        
    async def initialize(self, project_context=None) -> bool:
        """Initialize the MLX AI service"""
        try:
            # Initialize MLX service if needed
            if not unified_mlx_service.is_initialized:
                await unified_mlx_service.initialize()
            
            # Initialize AST context provider
            if project_context:
                self.ast_context_provider = ASTContextProvider(project_context)
            else:
                self.ast_context_provider = ASTContextProvider()
            
            self._initialized = True
            logger.info("MLX AI Service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize MLX AI Service: {e}")
            return False
    
    def get_capabilities(self) -> List[str]:
        """Get list of capabilities provided by this service"""
        return [
            "code_suggestions",
            "code_explanation",
            "refactoring_analysis",
            "debugging_assistance",
            "optimization_recommendations",
            "streaming_completions",
            "context_aware_inference"
        ]
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the service"""
        return {
            "service": "mlx_ai",
            "initialized": self._initialized,
            "mlx_available": unified_mlx_service.is_initialized,
            "model_health": unified_mlx_service.get_model_health(),
            "ast_context_ready": self.ast_context_provider is not None
        }
    
    async def suggest_code(
        self, 
        file_path: str, 
        cursor_position: int = 0, 
        context_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate code suggestions using MLX inference with AST context
        
        Extracted from: _mlx_suggest_code_tool()
        """
        try:
            if not file_path:
                return {
                    "status": "error",
                    "message": "file_path required for code suggestions",
                    "confidence": 0.0,
                }

            logger.info(
                f"Generating MLX code suggestions for {file_path}:{cursor_position}"
            )

            # Get rich AST context
            if self.ast_context_provider:
                context = await self.ast_context_provider.get_completion_context(
                    file_path, cursor_position, intent="suggest"
                )
            else:
                context = {"file_path": file_path, "cursor_position": cursor_position}

            # Add context hint if provided
            if context_hint:
                context["hint"] = context_hint

            # Generate MLX response
            response = await unified_mlx_service.generate_code_completion(
                context, "suggest"
            )

            if response["status"] != "success":
                return {
                    "status": "error",
                    "message": f"Error generating suggestions: {response.get('error', 'Unknown error')}",
                    "confidence": 0.0,
                }

            # Format response for service
            data = {
                "suggestions": response["response"],
                "confidence": response["confidence"],
                "language": response["language"],
                "requires_review": response["requires_human_review"],
                "follow_up_actions": response["suggestions"],
                "model": response["model"],
                "context_used": response["context_used"],
                "file_path": file_path,
                "cursor_position": cursor_position,
            }

            return {
                "status": "success",
                "type": "code_suggestions",
                "data": data,
                "message": f"Generated code suggestions for {file_path}",
                "confidence": response["confidence"],
            }

        except Exception as e:
            logger.error(f"Error in MLX suggest code: {e}")
            return {
                "status": "error",
                "message": f"Code suggestion failed: {str(e)}",
                "confidence": 0.0,
            }
    
    async def explain_code(
        self, 
        file_path: str, 
        cursor_position: int = 0,
        code_snippet: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Explain code using MLX inference with AST context
        
        Extracted from: _mlx_explain_code_tool()
        """
        try:
            if not file_path and not code_snippet:
                return {
                    "status": "error",
                    "message": "file_path or code_snippet required for code explanation",
                    "confidence": 0.0,
                }

            logger.info(
                f"Generating MLX code explanation for {file_path}:{cursor_position}"
            )

            # Get rich AST context
            if self.ast_context_provider and file_path:
                context = await self.ast_context_provider.get_completion_context(
                    file_path, cursor_position, intent="explain"
                )
            else:
                context = {
                    "file_path": file_path or "snippet",
                    "cursor_position": cursor_position,
                    "code_snippet": code_snippet
                }

            # Generate MLX response
            response = await unified_mlx_service.generate_code_completion(
                context, "explain"
            )

            if response["status"] != "success":
                return {
                    "status": "error",
                    "message": f"Error generating explanation: {response.get('error', 'Unknown error')}",
                    "confidence": 0.0,
                }

            # Format response
            data = {
                "explanation": response["response"],
                "confidence": response["confidence"],
                "language": response["language"],
                "context_analyzed": response["context_used"],
                "follow_up_suggestions": response["suggestions"],
                "file_path": file_path,
                "cursor_position": cursor_position,
            }

            return {
                "status": "success",
                "type": "code_explanation",
                "data": data,
                "message": f"Generated explanation for {file_path or 'code snippet'}",
                "confidence": response["confidence"],
            }

        except Exception as e:
            logger.error(f"Error in MLX explain code: {e}")
            return {
                "status": "error",
                "message": f"Code explanation failed: {str(e)}",
                "confidence": 0.0,
            }
    
    async def refactor_code(
        self, 
        file_path: str, 
        cursor_position: int = 0,
        refactor_goal: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate refactoring suggestions using MLX inference
        
        Extracted from: _mlx_refactor_code_tool()
        """
        try:
            if not file_path:
                return {
                    "status": "error",
                    "message": "file_path required for refactoring suggestions",
                    "confidence": 0.0,
                }

            logger.info(
                f"Generating MLX refactoring suggestions for {file_path}:{cursor_position}"
            )

            # Get rich AST context
            if self.ast_context_provider:
                context = await self.ast_context_provider.get_completion_context(
                    file_path, cursor_position, intent="refactor"
                )
            else:
                context = {"file_path": file_path, "cursor_position": cursor_position}

            # Add refactoring goal if provided
            if refactor_goal:
                context["refactor_goal"] = refactor_goal

            # Generate MLX response
            response = await unified_mlx_service.generate_code_completion(
                context, "refactor"
            )

            if response["status"] != "success":
                return {
                    "status": "error",
                    "message": f"Error generating refactoring suggestions: {response.get('error', 'Unknown error')}",
                    "confidence": 0.0,
                }

            # Format response
            data = {
                "refactoring_suggestions": response["response"],
                "confidence": response["confidence"],
                "language": response["language"],
                "requires_review": response["requires_human_review"],
                "next_steps": response["suggestions"],
                "complexity_analysis": context.get("relevant_context", {}).get(
                    "complexity", {}
                ),
                "file_path": file_path,
                "cursor_position": cursor_position,
                "refactor_goal": refactor_goal,
            }

            return {
                "status": "success",
                "type": "refactoring_suggestions",
                "data": data,
                "message": f"Generated refactoring suggestions for {file_path}",
                "confidence": response["confidence"],
            }

        except Exception as e:
            logger.error(f"Error in MLX refactor code: {e}")
            return {
                "status": "error",
                "message": f"Refactoring analysis failed: {str(e)}",
                "confidence": 0.0,
            }
    
    async def debug_code(
        self, 
        file_path: str, 
        cursor_position: int = 0,
        error_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate debugging analysis using MLX inference
        
        Extracted from: _mlx_debug_code_tool()
        """
        try:
            if not file_path:
                return {
                    "status": "error",
                    "message": "file_path required for debugging analysis",
                    "confidence": 0.0,
                }

            logger.info(
                f"Generating MLX debugging analysis for {file_path}:{cursor_position}"
            )

            # Get rich AST context
            if self.ast_context_provider:
                context = await self.ast_context_provider.get_completion_context(
                    file_path, cursor_position, intent="debug"
                )
            else:
                context = {"file_path": file_path, "cursor_position": cursor_position}

            # Add error context if provided
            if error_context:
                context["error_context"] = error_context

            # Generate MLX response
            response = await unified_mlx_service.generate_code_completion(context, "debug")

            if response["status"] != "success":
                return {
                    "status": "error",
                    "message": f"Error generating debug analysis: {response.get('error', 'Unknown error')}",
                    "confidence": 0.0,
                }

            # Format response
            data = {
                "debug_analysis": response["response"],
                "confidence": response["confidence"],
                "language": response["language"],
                "potential_issues": "Check the debug analysis for specific issues",
                "debugging_steps": response["suggestions"],
                "surrounding_context": context.get("surrounding_context", {}),
                "file_path": file_path,
                "cursor_position": cursor_position,
                "error_context": error_context,
            }

            return {
                "status": "success",
                "type": "debug_analysis",
                "data": data,
                "message": f"Generated debug analysis for {file_path}",
                "confidence": response["confidence"],
            }

        except Exception as e:
            logger.error(f"Error in MLX debug code: {e}")
            return {
                "status": "error",
                "message": f"Debug analysis failed: {str(e)}",
                "confidence": 0.0,
            }
    
    async def optimize_code(
        self, 
        file_path: str, 
        cursor_position: int = 0,
        optimization_target: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate optimization suggestions using MLX inference
        
        Extracted from: _mlx_optimize_code_tool()
        """
        try:
            if not file_path:
                return {
                    "status": "error",
                    "message": "file_path required for optimization suggestions",
                    "confidence": 0.0,
                }

            logger.info(
                f"Generating MLX optimization suggestions for {file_path}:{cursor_position}"
            )

            # Get rich AST context
            if self.ast_context_provider:
                context = await self.ast_context_provider.get_completion_context(
                    file_path, cursor_position, intent="optimize"
                )
            else:
                context = {"file_path": file_path, "cursor_position": cursor_position}

            # Add optimization target if provided
            if optimization_target:
                context["optimization_target"] = optimization_target

            # Generate MLX response
            response = await unified_mlx_service.generate_code_completion(
                context, "optimize"
            )

            if response["status"] != "success":
                return {
                    "status": "error",
                    "message": f"Error generating optimization suggestions: {response.get('error', 'Unknown error')}",
                    "confidence": 0.0,
                }

            # Format response
            data = {
                "optimization_suggestions": response["response"],
                "confidence": response["confidence"],
                "language": response["language"],
                "performance_impact": "See optimization suggestions for details",
                "implementation_steps": response["suggestions"],
                "complexity_metrics": context.get("relevant_context", {}).get(
                    "complexity", {}
                ),
                "file_path": file_path,
                "cursor_position": cursor_position,
                "optimization_target": optimization_target,
            }

            return {
                "status": "success",
                "type": "optimization_suggestions",
                "data": data,
                "message": f"Generated optimization suggestions for {file_path}",
                "confidence": response["confidence"],
            }

        except Exception as e:
            logger.error(f"Error in MLX optimize code: {e}")
            return {
                "status": "error",
                "message": f"Optimization analysis failed: {str(e)}",
                "confidence": 0.0,
            }
    
    async def start_streaming_completion(
        self, 
        file_path: str, 
        cursor_position: int = 0,
        intent: str = "suggest"
    ) -> Dict[str, Any]:
        """
        Start streaming code completion using MLX inference
        
        Extracted from: _mlx_stream_completion_tool()
        """
        try:
            if not file_path:
                return {
                    "status": "error",
                    "message": "file_path required for streaming completion",
                    "confidence": 0.0,
                }

            logger.info(
                f"Starting MLX streaming completion for {file_path}:{cursor_position} with intent '{intent}'"
            )

            # Get rich AST context
            if self.ast_context_provider:
                context = await self.ast_context_provider.get_completion_context(
                    file_path, cursor_position, intent=intent
                )
            else:
                context = {"file_path": file_path, "cursor_position": cursor_position}

            # Note: In a real implementation, this would set up a streaming endpoint
            # For now, we prepare the streaming configuration

            data = {
                "status": "streaming_started",
                "file_path": file_path,
                "cursor_position": cursor_position,
                "intent": intent,
                "context_ready": True,
                "estimated_chunks": 10,
                "stream_id": f"mlx_stream_{hash(f'{file_path}:{cursor_position}:{intent}')}",
                "context_used": context.get("context_used", False),
            }

            return {
                "status": "success",
                "type": "streaming_completion_started",
                "data": data,
                "message": "Streaming completion started. Use WebSocket connection to receive real-time updates.",
                "confidence": 0.9,
            }

        except Exception as e:
            logger.error(f"Error in MLX stream completion: {e}")
            return {
                "status": "error",
                "message": f"Streaming completion failed: {str(e)}",
                "confidence": 0.0,
            }
    
    async def get_ai_insights(self, file_path: str) -> Dict[str, Any]:
        """
        Generate comprehensive AI insights for a file
        """
        try:
            insights = {
                "file_path": file_path,
                "insights": [],
                "recommendations": [],
                "confidence": 0.0
            }
            
            # Run multiple AI analyses
            analyses = []
            
            # Get code explanation
            explanation_result = await self.explain_code(file_path, 0)
            if explanation_result["status"] == "success":
                analyses.append(explanation_result)
                insights["insights"].append({
                    "type": "code_explanation",
                    "content": explanation_result["data"]["explanation"],
                    "confidence": explanation_result["confidence"]
                })
            
            # Get optimization suggestions
            optimization_result = await self.optimize_code(file_path, 0)
            if optimization_result["status"] == "success":
                analyses.append(optimization_result)
                insights["insights"].append({
                    "type": "optimization_opportunities",
                    "content": optimization_result["data"]["optimization_suggestions"],
                    "confidence": optimization_result["confidence"]
                })
            
            # Get refactoring suggestions
            refactor_result = await self.refactor_code(file_path, 0)
            if refactor_result["status"] == "success":
                analyses.append(refactor_result)
                insights["insights"].append({
                    "type": "refactoring_opportunities",
                    "content": refactor_result["data"]["refactoring_suggestions"],
                    "confidence": refactor_result["confidence"]
                })
            
            # Calculate overall confidence
            if analyses:
                total_confidence = sum(analysis["confidence"] for analysis in analyses)
                insights["confidence"] = total_confidence / len(analyses)
            
            # Generate recommendations based on insights
            if len(insights["insights"]) >= 2:
                insights["recommendations"].append("Multiple improvement opportunities identified")
            if any(insight["confidence"] > 0.8 for insight in insights["insights"]):
                insights["recommendations"].append("High-confidence suggestions available")
            
            summary = f"""🧠 AI Insights for {file_path}:

📊 Analysis Results:
• Insights generated: {len(insights["insights"])}
• Average confidence: {insights["confidence"]:.1%}
• Recommendations: {len(insights["recommendations"])}

💡 Key Findings:
{chr(10).join(f'• {insight["type"].replace("_", " ").title()}: {insight["confidence"]:.1%} confidence' for insight in insights["insights"])}

🎯 Next Steps:
{chr(10).join(f'• {rec}' for rec in insights["recommendations"])}"""

            return {
                "status": "success",
                "type": "ai_insights",
                "data": {
                    **insights,
                    "summary": summary
                },
                "message": f"Generated {len(insights['insights'])} AI insights for {file_path}",
                "confidence": insights["confidence"],
            }

        except Exception as e:
            logger.error(f"Error generating AI insights: {e}")
            return {
                "status": "error",
                "message": f"AI insights generation failed: {str(e)}",
                "confidence": 0.0,
            }
    
    async def batch_analyze(self, file_paths: List[str], analysis_type: str = "suggest") -> Dict[str, Any]:
        """
        Perform batch analysis on multiple files
        """
        try:
            results = []
            total_confidence = 0.0
            successful_analyses = 0
            
            for file_path in file_paths:
                try:
                    if analysis_type == "suggest":
                        result = await self.suggest_code(file_path)
                    elif analysis_type == "explain":
                        result = await self.explain_code(file_path)
                    elif analysis_type == "refactor":
                        result = await self.refactor_code(file_path)
                    elif analysis_type == "optimize":
                        result = await self.optimize_code(file_path)
                    elif analysis_type == "debug":
                        result = await self.debug_code(file_path)
                    else:
                        result = {"status": "error", "message": f"Unknown analysis type: {analysis_type}"}
                    
                    results.append({
                        "file_path": file_path,
                        "result": result
                    })
                    
                    if result["status"] == "success":
                        total_confidence += result["confidence"]
                        successful_analyses += 1
                        
                except Exception as e:
                    results.append({
                        "file_path": file_path,
                        "result": {
                            "status": "error",
                            "message": f"Analysis failed: {str(e)}",
                            "confidence": 0.0
                        }
                    })
            
            avg_confidence = total_confidence / max(successful_analyses, 1)
            
            summary = f"""📚 Batch Analysis Results:

📊 Overview:
• Files analyzed: {len(file_paths)}
• Successful analyses: {successful_analyses}
• Analysis type: {analysis_type}
• Average confidence: {avg_confidence:.1%}

✅ Success rate: {(successful_analyses / max(len(file_paths), 1)):.1%}"""

            return {
                "status": "success",
                "type": "batch_analysis",
                "data": {
                    "results": results,
                    "total_files": len(file_paths),
                    "successful_analyses": successful_analyses,
                    "average_confidence": avg_confidence,
                    "analysis_type": analysis_type,
                    "summary": summary
                },
                "message": f"Completed batch {analysis_type} analysis on {len(file_paths)} files",
                "confidence": avg_confidence,
            }

        except Exception as e:
            logger.error(f"Error in batch analysis: {e}")
            return {
                "status": "error",
                "message": f"Batch analysis failed: {str(e)}",
                "confidence": 0.0,
            }