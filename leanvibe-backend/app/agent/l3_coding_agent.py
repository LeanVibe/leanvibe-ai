"""
LeanVibe L3 Coding Agent - Pydantic.ai Framework Integration

This module implements the core L3 agent using pydantic.ai for structured 
autonomous coding assistance with MLX backend integration.
"""

import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ..services.ai_service import AIService
from ..services.unified_mlx_service import unified_mlx_service

logger = logging.getLogger(__name__)


@dataclass
class AgentDependencies:
    """Dependencies for the L3 coding agent"""

    workspace_path: str = "."
    client_id: str = "default"
    session_data: Dict[str, Any] = None

    def __post_init__(self):
        if self.session_data is None:
            self.session_data = {}


class AgentState(BaseModel):
    """State management for the L3 coding agent"""

    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    project_context: Dict[str, Any] = Field(default_factory=dict)
    confidence_scores: List[float] = Field(default_factory=list)
    current_task: Optional[str] = None
    workspace_path: str = "."
    session_id: str = "default"

    def add_conversation_entry(self, role: str, content: str, confidence: float = 1.0):
        """Add an entry to conversation history"""
        entry = {
            "role": role,
            "content": content,
            "timestamp": time.time(),
            "confidence": confidence,
        }
        self.conversation_history.append(entry)
        self.confidence_scores.append(confidence)

    def get_average_confidence(self) -> float:
        """Get average confidence score across recent interactions"""
        if not self.confidence_scores:
            return 0.5
        # Consider only recent scores (last 10)
        recent_scores = self.confidence_scores[-10:]
        return sum(recent_scores) / len(recent_scores)

    def update_project_context(self, key: str, value: Any):
        """Update project context information"""
        self.project_context[key] = value


class SimpleOllamaModel:
    """Simple Ollama model for pydantic.ai integration"""

    def __init__(self, ollama_service: "OllamaAIService" = None):
        self.ollama_service = ollama_service
        self.fallback_service = None
        
    async def initialize(self):
        """Initialize Ollama service"""
        if self.ollama_service is None:
            from ..services.ollama_ai_service import get_ollama_service
            try:
                self.ollama_service = await get_ollama_service()
                logger.info("✅ Ollama service initialized for L3 agent")
            except Exception as e:
                logger.warning(f"Failed to initialize Ollama service: {e}")
                
    async def generate_response(self, prompt: str) -> str:
        """Generate response using Ollama backend"""
        try:
            # Ensure Ollama service is initialized
            if self.ollama_service is None or not self.ollama_service.is_ready():
                await self.initialize()
                
            if self.ollama_service and self.ollama_service.is_ready():
                # Use Ollama for generation
                response = await self.ollama_service.generate(
                    prompt=prompt,
                    max_tokens=1000,
                    temperature=0.1
                )
                
                if response:
                    logger.info(f"✅ Ollama generated response ({len(response)} chars)")
                    return response
                else:
                    logger.warning("Ollama returned empty response")
                    return "I apologize, but I couldn't generate a response at the moment. Please try again."
            else:
                # Fallback to simple response
                logger.warning("Ollama service not available, using fallback")
                return f"I received your message: '{prompt[:100]}...' but I'm currently unable to process it fully. The AI service is not available."

        except Exception as e:
            logger.error(f"Ollama model generation failed: {e}")
            return f"I encountered an error: {str(e)}. How can I help you differently?"


class L3CodingAgent:
    """
    L3 Autonomous Coding Agent using pydantic.ai framework

    Provides structured, confidence-scored autonomous coding assistance
    with tool integration and human intervention triggers.
    """

    def __init__(self, dependencies: AgentDependencies):
        self.dependencies = dependencies
        self.ai_service = AIService()
        self.model_wrapper = SimpleOllamaModel()
        # Initialize Ollama service asynchronously
        self._model_initialized = False
        self.state = AgentState(
            workspace_path=dependencies.workspace_path,
            session_id=dependencies.client_id,
        )

        # Confidence thresholds for different actions
        self.confidence_thresholds = {
            "autonomous_execution": 0.8,
            "human_review_suggested": 0.6,
            "human_intervention_required": 0.4,
        }

        # Tools available to the agent
        self.tools = {
            "analyze_file": self._analyze_file_tool,
            "file_operations": self._file_operations_tool,
            "assess_confidence": self._assess_confidence_tool,
        }

    async def initialize(self):
        """Initialize the L3 coding agent"""
        try:
            logger.info("Initializing L3 Coding Agent...")

            # Initialize underlying AI service (for file ops, etc.)
            await self.ai_service.initialize()

            # Initialize real MLX service
            await unified_mlx_service.initialize()

            logger.info("L3 Coding Agent initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize L3 agent: {e}")
            return False

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the L3 coding agent"""
        return """You are LeanVibe, an L3 autonomous coding agent designed to help senior engineers with their side projects.

Your capabilities:
- Analyze code files and provide detailed insights
- Perform file operations and directory navigation
- Generate confidence scores for all recommendations
- Trigger human intervention when confidence is low
- Maintain project context across sessions

Core principles:
1. Always provide confidence scores (0.0-1.0) for your responses
2. Suggest human review for complex or critical decisions
3. Focus on practical, actionable coding assistance
4. Maintain awareness of the project's overall architecture
5. Be transparent about your limitations and uncertainty

When confidence < 0.8: Recommend human review
When confidence < 0.4: Require human intervention before proceeding

You have access to file analysis, file operations, and confidence assessment tools."""

    async def _analyze_file_tool(self, file_path: str) -> Dict[str, Any]:
        """Analyze a code file and provide detailed insights"""
        try:
            result = await self.ai_service._analyze_file(
                file_path, self.dependencies.client_id
            )

            # Update agent state with analysis
            if result["status"] == "success":
                confidence = result.get("confidence", 0.5)
                self.state.add_conversation_entry(
                    "system", f"Analyzed file: {file_path}", confidence
                )
                self.state.update_project_context(
                    f"analysis_{file_path}", result["data"]
                )

            return result

        except Exception as e:
            logger.error(f"File analysis tool error: {e}")
            return {"status": "error", "message": str(e), "confidence": 0.0}

    async def _file_operations_tool(
        self, operation: str, path: str = "", content: str = ""
    ) -> Dict[str, Any]:
        """Perform file operations like read, list, or directory navigation"""
        try:
            if operation == "list":
                result = await self.ai_service._list_files(
                    path, self.dependencies.client_id
                )
            elif operation == "read":
                result = await self.ai_service._read_file(
                    path, self.dependencies.client_id
                )
            elif operation == "current_dir":
                result = await self.ai_service._get_current_directory(
                    "", self.dependencies.client_id
                )
            else:
                result = {
                    "status": "error",
                    "message": f"Unknown operation: {operation}",
                }

            # Update agent state
            if result["status"] == "success":
                confidence = self.ai_service._calculate_confidence_score(
                    result.get("message", ""), "file_operation"
                )
                self.state.add_conversation_entry(
                    "system", f"File operation: {operation} on {path}", confidence
                )

            return result

        except Exception as e:
            logger.error(f"File operations tool error: {e}")
            return {"status": "error", "message": str(e), "confidence": 0.0}

    async def _assess_confidence_tool(
        self, action: str, complexity: str = "medium"
    ) -> Dict[str, Any]:
        """Assess confidence level for a proposed action"""
        try:
            # Calculate confidence based on various factors
            base_confidence = 0.7

            # Adjust based on action complexity
            complexity_adjustments = {
                "low": 0.2,
                "medium": 0.0,
                "high": -0.2,
                "critical": -0.4,
            }

            adjustment = complexity_adjustments.get(complexity.lower(), 0.0)
            confidence = max(0.0, min(1.0, base_confidence + adjustment))

            # Consider historical performance
            avg_confidence = self.state.get_average_confidence()
            confidence = (confidence + avg_confidence) / 2

            # Determine recommendation
            recommendation = self._get_confidence_recommendation(confidence)

            result = {
                "status": "success",
                "confidence": confidence,
                "recommendation": recommendation,
                "action": action,
                "complexity": complexity,
            }

            # Update state
            self.state.add_conversation_entry(
                "system", f"Confidence assessment for: {action}", confidence
            )

            return result

        except Exception as e:
            logger.error(f"Confidence assessment tool error: {e}")
            return {"status": "error", "message": str(e), "confidence": 0.0}

    def _get_confidence_recommendation(self, confidence: float) -> str:
        """Get recommendation based on confidence score"""
        if confidence >= self.confidence_thresholds["autonomous_execution"]:
            return "proceed_autonomously"
        elif confidence >= self.confidence_thresholds["human_review_suggested"]:
            return "human_review_suggested"
        elif confidence >= self.confidence_thresholds["human_intervention_required"]:
            return "human_intervention_required"
        else:
            return "stop_and_escalate"

    async def run(self, user_input: str) -> Dict[str, Any]:
        """Main entry point for agent interaction"""
        try:
            # Ensure model wrapper is initialized
            if not self._model_initialized:
                await self.model_wrapper.initialize()
                self._model_initialized = True

            # Record user input
            self.state.add_conversation_entry("user", user_input)

            # Process the input and determine if tools are needed
            response_content = await self._process_user_input(user_input)

            # Calculate overall confidence for this interaction
            # Use Ollama service confidence if available, otherwise fallback
            if (self.model_wrapper.ollama_service and 
                self.model_wrapper.ollama_service.is_ready()):
                confidence = 0.85  # High confidence for Ollama responses
            else:
                confidence = self.ai_service._calculate_confidence_score(
                    response_content, "ai_response"
                )

            # Record agent response
            self.state.add_conversation_entry("assistant", response_content, confidence)

            # Create structured response
            agent_response = {
                "status": "success",
                "message": response_content,
                "confidence": confidence,
                "recommendation": self._get_confidence_recommendation(confidence),
                "model": (
                    f"Ollama ({self.model_wrapper.ollama_service.default_model})"
                    if self.model_wrapper.ollama_service and self.model_wrapper.ollama_service.is_ready()
                    else "L3-Agent-Fallback"
                ),
                "services_available": {
                    "ollama": self.model_wrapper.ollama_service and self.model_wrapper.ollama_service.is_ready(),
                    "mlx": unified_mlx_service.is_initialized,
                    "ast": self.ai_service.is_initialized,
                    "vector": self.ai_service.is_initialized,
                },
                "session_state": {
                    "conversation_length": len(self.state.conversation_history),
                    "average_confidence": self.state.get_average_confidence(),
                    "current_task": self.state.current_task,
                },
                "timestamp": time.time(),
            }

            # Add warning if confidence is low
            if confidence < self.confidence_thresholds["human_review_suggested"]:
                agent_response["warning"] = "Low confidence - human review recommended"

            return agent_response

        except Exception as e:
            logger.error(f"Agent run error: {e}")
            return {
                "status": "error",
                "message": f"Agent execution failed: {str(e)}",
                "confidence": 0.0,
                "timestamp": time.time(),
            }

    async def _process_user_input(self, user_input: str) -> str:
        """Process user input and determine appropriate response"""
        try:
            # Simple tool detection based on keywords
            user_lower = user_input.lower()

            # Check if user wants file analysis
            if "analyze" in user_lower and (
                "file" in user_lower or "code" in user_lower
            ):
                # Extract file path (simple heuristic)
                words = user_input.split()
                for word in words:
                    if "." in word and "/" in word:  # Looks like a file path
                        result = await self._analyze_file_tool(word)
                        if result["status"] == "success":
                            return f"File analysis complete for {word}:\n{result['data']['analysis']}"
                        else:
                            return f"Error analyzing file: {result['message']}"

            # Check if user wants file operations
            elif "list" in user_lower and (
                "file" in user_lower or "directory" in user_lower
            ):
                result = await self._file_operations_tool("list", ".")
                if result["status"] == "success":
                    files = result["data"]["files"]
                    dirs = result["data"]["directories"]
                    return f"Found {len(dirs)} directories and {len(files)} files in current directory."
                else:
                    return f"Error listing files: {result['message']}"

            # Check if user wants current directory
            elif "current" in user_lower and "directory" in user_lower:
                result = await self._file_operations_tool("current_dir")
                if result["status"] == "success":
                    return f"Current directory: {result['data']['current_directory']}"
                else:
                    return f"Error getting directory: {result['message']}"

            # For general questions, use the MLX model
            else:
                enhanced_prompt = f"""
As LeanVibe L3 coding agent, I need to respond to: "{user_input}"

Context:
- Workspace: {self.state.workspace_path}
- Previous interactions: {len(self.state.conversation_history)}
- Average confidence: {self.state.get_average_confidence():.2f}

Provide a helpful, practical response focused on coding assistance.
"""
                response = await self.model_wrapper.generate_response(enhanced_prompt)
                return response

        except Exception as e:
            logger.error(f"Error processing user input: {e}")
            return f"I encountered an error processing your request: {str(e)}. How can I help you differently?"

    def _calculate_interaction_confidence(
        self, user_input: str, response: str
    ) -> float:
        """Calculate confidence for this specific interaction"""
        # This method will be replaced by direct call to unified_mlx_service._calculate_confidence
        # in the run method. Keeping it for now to avoid breaking other parts.
        base_confidence = 0.5  # Default if Ollama service is not initialized
        if (self.model_wrapper.ollama_service and 
            self.model_wrapper.ollama_service.is_ready()):
            base_confidence = 0.85  # Default confidence for Ollama service
        else:
            base_confidence = self.ai_service._calculate_confidence_score(
                response, "ai_response"
            )

        # Adjust based on input complexity
        input_complexity_factors = {
            "simple_question": 0.1,  # Questions about status, help, etc.
            "file_operation": 0.0,  # Standard file operations
            "code_analysis": -0.1,  # More complex analysis
            "architecture": -0.2,  # High-level architecture questions
        }

        # Determine input type
        input_lower = user_input.lower()
        if any(word in input_lower for word in ["status", "help", "list"]):
            adjustment = input_complexity_factors["simple_question"]
        elif any(word in input_lower for word in ["read", "file", "directory"]):
            adjustment = input_complexity_factors["file_operation"]
        elif any(word in input_lower for word in ["analyze", "review", "code"]):
            adjustment = input_complexity_factors["code_analysis"]
        elif any(
            word in input_lower for word in ["architecture", "design", "structure"]
        ):
            adjustment = input_complexity_factors["architecture"]
        else:
            adjustment = 0.0

        # Consider historical performance
        historical_confidence = self.state.get_average_confidence()
        if historical_confidence > 0.5:  # Have some history
            base_confidence = (base_confidence + historical_confidence) / 2

        return max(0.0, min(1.0, base_confidence + adjustment))

    async def plan(self, task_description: str) -> Dict[str, Any]:
        """Plan a complex task with confidence assessment"""
        try:
            planning_prompt = f"""
            As an L3 coding agent, break down this task into manageable steps:
            
            Task: {task_description}
            
            Provide:
            1. Step-by-step breakdown
            2. Confidence assessment for each step
            3. Risk factors and mitigation strategies
            4. Human intervention points
            
            Format your response as a structured plan.
            """

            result = await self.run(planning_prompt)

            # Update current task
            self.state.current_task = task_description

            return result

        except Exception as e:
            logger.error(f"Task planning error: {e}")
            return {
                "status": "error",
                "message": f"Failed to plan task: {str(e)}",
                "confidence": 0.0,
            }

    async def reflect(self) -> Dict[str, Any]:
        """Reflect on recent performance and provide insights"""
        try:
            conversation_summary = (
                f"Recent conversation length: {len(self.state.conversation_history)}"
            )
            avg_confidence = self.state.get_average_confidence()

            reflection_prompt = f"""
            Reflect on our recent interactions:
            
            {conversation_summary}
            Average confidence: {avg_confidence:.2f}
            Current task: {self.state.current_task or 'None'}
            
            Provide insights on:
            1. Performance trends
            2. Areas for improvement
            3. Successful patterns
            4. Recommendations for better collaboration
            """

            result = await self.run(reflection_prompt)

            return result

        except Exception as e:
            logger.error(f"Reflection error: {e}")
            return {
                "status": "error",
                "message": f"Failed to reflect: {str(e)}",
                "confidence": 0.0,
            }

    def get_state_summary(self) -> Dict[str, Any]:
        """Get current agent state summary"""
        return {
            "session_id": self.state.session_id,
            "workspace_path": self.state.workspace_path,
            "conversation_length": len(self.state.conversation_history),
            "average_confidence": self.state.get_average_confidence(),
            "current_task": self.state.current_task,
            "project_context_keys": list(self.state.project_context.keys()),
            "ai_service_status": unified_mlx_service.get_model_health(),
            "confidence_thresholds": self.confidence_thresholds,
        }
