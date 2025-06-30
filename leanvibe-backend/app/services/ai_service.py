import asyncio
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


class AIService:
    """AI service that handles command processing and MLX integration"""

    def __init__(self):
        self.is_initialized = False
        self.session_data = {}  # Simple in-memory session storage
        self.supported_commands = {
            "/list-files": self._list_files,
            "/status": self._get_status,
            "/current-dir": self._get_current_directory,
            "/read-file": self._read_file,
            "/analyze-file": self._analyze_file,
            "/help": self._get_help,
        }
        self.mlx_available = False
        self.model_health = {
            "status": "unknown", 
            "model_loaded": False, 
            "last_check": None
        }

    async def initialize(self):
        """Initialize AI service (no MLX loading here)"""
        logger.info("Initializing AI service (command dispatcher only)...")
        self.is_initialized = True
        
        # Update model health status since this is command dispatcher only
        self.model_health = {
            "status": "mock_mode",
            "model_loaded": False,
            "last_check": time.time()
        }
        
        logger.info("AI service initialized successfully.")

    def _calculate_confidence_score(self, response: str, command_type: str) -> float:
        """Calculate confidence score for agent response"""
        # Simple heuristic-based confidence scoring
        # In production, this would use more sophisticated methods

        base_confidence = 0.7

        # Adjust based on response length and quality indicators
        if len(response) < 10:
            base_confidence -= 0.2
        elif len(response) > 100:
            base_confidence += 0.1

        # Adjust based on command type
        if command_type == "file_operation":
            base_confidence += 0.2  # File ops are usually reliable
        elif command_type == "code_analysis":
            base_confidence -= 0.1  # Code analysis needs more caution

        # Check for error indicators
        if "error" in response.lower() or "failed" in response.lower():
            base_confidence -= 0.3

        # Check for positive indicators
        if "successfully" in response.lower() or "found" in response.lower():
            base_confidence += 0.1

        return max(0.0, min(1.0, base_confidence))

    async def process_command(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process command from iOS client"""
        if not self.is_initialized:
            return {"status": "error", "message": "AI service not initialized"}

        command = data.get("content", "")
        command_type = data.get("type", "message")
        client_id = data.get("client_id", "unknown")

        try:
            start_time = time.time()

            if command_type == "command" and command.startswith("/"):
                result = await self._process_slash_command(command, client_id)
            else:
                result = await self._process_message(command, client_id)

            # Add processing time to response
            processing_time = time.time() - start_time
            result["processing_time"] = round(processing_time, 3)

            return result

        except Exception as e:
            logger.error(f"Error processing command: {e}")
            return {"status": "error", "message": str(e)}

    async def _process_slash_command(
        self, command: str, client_id: str
    ) -> Dict[str, Any]:
        """Process slash commands"""
        # Parse command and arguments
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
        """Process general messages with AI"""
        if not message.strip():
            return {"status": "error", "message": "Empty message"}

        try:
            # Create prompt for coding assistant
            prompt = self._create_coding_prompt(message)

            # Generate response using unified_mlx_service
            from .unified_mlx_service import unified_mlx_service

            if unified_mlx_service.is_initialized:
                response_obj = await unified_mlx_service.generate_code_completion(
                    context={"prompt": prompt}, intent="suggest"
                )
                if response_obj and response_obj.get("status") == "success":
                    response = response_obj.get("response", "")
                    model_info = "Unified MLX Service"
                else:
                    response = await self._generate_mock_response(message)
                    model_info = "CodeLlama-7B (Mock)"
            else:
                response = await self._generate_mock_response(message)
                model_info = "CodeLlama-7B (Mock)"

            # Calculate confidence score
            confidence = self._calculate_confidence_score(response, "ai_response")

            result = {
                "status": "success",
                "type": "ai_response",
                "message": response,
                "timestamp": time.time(),
                "model": model_info,
                "confidence": confidence,
                "health": self.model_health.copy(),
            }

            # Add human intervention suggestion if confidence is low
            if confidence < 0.5:
                result["warning"] = "Low confidence response - human review recommended"

            return result

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "status": "error",
                "message": f"Error processing message: {str(e)}",
                "confidence": 0.0,
            }

    def _create_coding_prompt(self, message: str) -> str:
        """Create a well-structured prompt for the coding assistant"""
        return f"""[INST] You are a helpful coding assistant. You provide clear, concise, and accurate responses about programming, software development, and technical questions.

User query: {message}

Please provide a helpful response focused on practical software development guidance. Keep your response concise and actionable. [/INST]"""

    async def _generate_mock_response(self, message: str) -> str:
        """Generate enhanced mock responses when MLX is not available"""
        await asyncio.sleep(0.3)  # Simulate processing time

        # More sophisticated mock responses based on message content
        message_lower = message.lower()

        if any(word in message_lower for word in ["file", "directory", "folder"]):
            return f"For file operations like '{message}', I can help you navigate and analyze your codebase. Try using /list-files to see available files or /read-file to examine specific files."
        elif any(
            word in message_lower for word in ["code", "function", "class", "method"]
        ):
            return f"Regarding '{message}': I can analyze code structure and provide insights. Use /analyze-file to get detailed code analysis, or ask me about specific programming concepts."
        elif any(word in message_lower for word in ["error", "bug", "debug", "fix"]):
            return f"For debugging '{message}': I can help identify issues in your code. Share the problematic code using /read-file, and I'll analyze it for potential problems."
        elif any(word in message_lower for word in ["help", "how", "what", "why"]):
            return f"Happy to help with '{message}'! As your L3 coding agent, I can assist with file operations, code analysis, debugging, and general programming guidance. Try /help to see all available commands."
        else:
            return f"I understand you're asking about '{message}'. As your local coding assistant, I can help with code analysis, file operations, and development tasks. Currently running in enhanced mode with confidence scoring."

    async def _list_files(self, args: str, client_id: str) -> Dict[str, Any]:
        """List files in current or specified directory"""
        try:
            target_dir = args.strip() if args.strip() else "."
            path = Path(target_dir)

            if not path.exists():
                return {
                    "status": "error",
                    "message": f"Directory not found: {target_dir}",
                }

            if not path.is_dir():
                return {"status": "error", "message": f"Not a directory: {target_dir}"}

            files = []
            dirs = []

            for item in sorted(path.iterdir()):
                if item.is_file():
                    files.append(
                        {"name": item.name, "size": item.stat().st_size, "type": "file"}
                    )
                elif item.is_dir():
                    dirs.append({"name": item.name, "type": "directory"})

            return {
                "status": "success",
                "type": "file_list",
                "data": {
                    "directories": dirs,
                    "files": files,
                    "path": str(path.absolute()),
                },
                "message": f"Found {len(dirs)} directories and {len(files)} files in {target_dir}",
            }

        except Exception as e:
            return {"status": "error", "message": f"Error listing files: {e}"}

    async def _read_file(self, args: str, client_id: str) -> Dict[str, Any]:
        """Read contents of a file"""
        if not args.strip():
            return {
                "status": "error",
                "message": "File path required. Usage: /read-file <path>",
            }

        try:
            file_path = Path(args.strip())

            if not file_path.exists():
                return {"status": "error", "message": f"File not found: {args}"}

            if not file_path.is_file():
                return {"status": "error", "message": f"Not a file: {args}"}

            # Read file with size limit for safety
            max_size = 1024 * 1024  # 1MB limit
            if file_path.stat().st_size > max_size:
                return {
                    "status": "error",
                    "message": f"File too large (max 1MB): {args}",
                }

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            return {
                "status": "success",
                "type": "file_content",
                "data": {
                    "path": str(file_path.absolute()),
                    "content": content,
                    "size": len(content),
                    "lines": len(content.splitlines()),
                },
                "message": f"Read {len(content)} characters from {args}",
            }

        except UnicodeDecodeError:
            return {"status": "error", "message": f"Cannot read binary file: {args}"}
        except Exception as e:
            return {"status": "error", "message": f"Error reading file: {e}"}

    async def _get_current_directory(self, args: str, client_id: str) -> Dict[str, Any]:
        """Get current working directory"""
        try:
            cwd = os.getcwd()
            return {
                "status": "success",
                "type": "directory_info",
                "data": {"current_directory": cwd},
                "message": f"Current directory: {cwd}",
            }
        except Exception as e:
            return {"status": "error", "message": f"Error getting directory: {e}"}

    async def _get_status(self, args: str, client_id: str) -> Dict[str, Any]:
        """Get agent status with health information"""
        model_name = "N/A (MLX handled by unified_mlx_service)"

        # Calculate confidence score for status command
        confidence = self._calculate_confidence_score(
            "Agent status retrieved", "file_operation"
        )

        status_data = {
            "model": model_name,
            "ready": self.is_initialized,
            "version": "0.2.0",
            "supported_commands": list(self.supported_commands.keys()),
            "session_active": client_id in self.session_data,
            "mlx_available": False,  # MLX availability now checked via unified_mlx_service
            "health": {
                "status": "N/A",
                "last_check": None,
                "memory_usage": 0,
            },  # MLX health now via unified_mlx_service
            "confidence_scoring": True,
        }

        return {
            "status": "success",
            "type": "agent_status",
            "data": status_data,
            "message": "Agent is ready and operational (MLX status via unified_mlx_service)",
            "confidence": confidence,
        }

    async def _analyze_file(self, args: str, client_id: str) -> Dict[str, Any]:
        """Analyze a file with AI assistance"""
        if not args.strip():
            return {
                "status": "error",
                "message": "File path required. Usage: /analyze-file <path>",
            }

        try:
            file_path = Path(args.strip())

            if not file_path.exists():
                return {"status": "error", "message": f"File not found: {args}"}

            if not file_path.is_file():
                return {"status": "error", "message": f"Not a file: {args}"}

            # Read file with size limit
            max_size = 512 * 1024  # 512KB limit for analysis
            if file_path.stat().st_size > max_size:
                return {
                    "status": "error",
                    "message": f"File too large for analysis (max 512KB): {args}",
                }

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except UnicodeDecodeError:
                return {
                    "status": "error",
                    "message": f"Cannot analyze binary file: {args}",
                }

            # Create analysis prompt
            analysis_prompt = self._create_analysis_prompt(str(file_path), content)

            # Generate analysis using unified_mlx_service or fallback
            from .unified_mlx_service import unified_mlx_service

            if unified_mlx_service.is_initialized:
                response_obj = await unified_mlx_service.generate_code_completion(
                    context={
                        "prompt": analysis_prompt,
                        "file_path": str(file_path),
                        "content": content,
                    },
                    intent="explain",  # Use explain intent for analysis
                )
                if response_obj and response_obj.get("status") == "success":
                    analysis = response_obj.get("response", "")
                    model_info = "Unified MLX Service"
                else:
                    analysis = await self._generate_mock_analysis(
                        str(file_path), content
                    )
                    model_info = "CodeLlama-7B (Mock)"
            else:
                analysis = await self._generate_mock_analysis(str(file_path), content)
                model_info = "CodeLlama-7B (Mock)"

            # Calculate confidence score
            confidence = self._calculate_confidence_score(analysis, "code_analysis")

            result = {
                "status": "success",
                "type": "file_analysis",
                "data": {
                    "path": str(file_path.absolute()),
                    "size": len(content),
                    "lines": len(content.splitlines()),
                    "analysis": analysis,
                    "model": model_info,
                },
                "message": f"Analysis complete for {args}",
                "confidence": confidence,
            }

            # Add warning for low confidence
            if confidence < 0.6:
                result["warning"] = (
                    "Analysis confidence is low - consider manual review"
                )

            return result

        except Exception as e:
            return {"status": "error", "message": f"Error analyzing file: {e}"}

    def _create_analysis_prompt(self, file_path: str, content: str) -> str:
        """Create prompt for code analysis"""
        # Truncate content if too long
        max_content_length = 2000
        if len(content) > max_content_length:
            content = content[:max_content_length] + "\n... (truncated)"

        return f"""[INST] You are a code analysis expert. Analyze the following file and provide insights about:
1. Code structure and organization
2. Potential issues or improvements
3. Code quality assessment
4. Suggestions for optimization

File: {file_path}
Content:
```
{content}
```

Provide a concise analysis focused on actionable insights. [/INST]"""

    async def _generate_mock_analysis(self, file_path: str, content: str) -> str:
        """Generate mock analysis when MLX is not available"""
        await asyncio.sleep(0.5)  # Simulate analysis time

        lines = content.splitlines()
        file_ext = Path(file_path).suffix.lower()

        # Basic analysis based on file type and content
        analysis_parts = []

        # File overview
        analysis_parts.append(f"File Analysis: {Path(file_path).name}")
        analysis_parts.append(f"Type: {file_ext} file with {len(lines)} lines")

        # Language-specific analysis
        if file_ext in [".py", ".python"]:
            analysis_parts.append("Language: Python")
            if "import" in content:
                analysis_parts.append("✓ Uses imports - good modularity")
            if "def " in content:
                analysis_parts.append("✓ Contains function definitions")
            if "class " in content:
                analysis_parts.append("✓ Object-oriented structure detected")
        elif file_ext in [".js", ".javascript"]:
            analysis_parts.append("Language: JavaScript")
            if "function" in content:
                analysis_parts.append("✓ Function-based structure")
            if "const " in content or "let " in content:
                analysis_parts.append("✓ Modern ES6+ syntax")
        elif file_ext in [".swift"]:
            analysis_parts.append("Language: Swift")
            if "func " in content:
                analysis_parts.append("✓ Contains function definitions")
            if "struct " in content or "class " in content:
                analysis_parts.append("✓ Type definitions found")
        else:
            analysis_parts.append(
                f"Language: {file_ext[1:].upper() if file_ext else 'Unknown'}"
            )

        # Code quality indicators
        if len(lines) > 200:
            analysis_parts.append(
                "⚠ Large file - consider breaking into smaller modules"
            )
        elif len(lines) < 10:
            analysis_parts.append("ℹ Small file - appropriate for simple functionality")

        # Look for common patterns
        if any("TODO" in line or "FIXME" in line for line in lines):
            analysis_parts.append("⚠ Contains TODO/FIXME comments")

        if content.count("\n\n") > 5:
            analysis_parts.append("✓ Good use of whitespace for readability")

        analysis_parts.append(
            "\nThis is a mock analysis. Enable MLX for detailed AI-powered insights."
        )

        return "\n".join(analysis_parts)

    async def _get_help(self, args: str, client_id: str) -> Dict[str, Any]:
        """Get help information"""
        help_text = """
Available Commands:
/list-files [directory] - List files in current or specified directory
/read-file <path> - Read contents of a file
/analyze-file <path> - Analyze a file with AI assistance
/current-dir - Show current working directory
/status - Show agent status and health information
/help - Show this help message

Features:
• Real-time confidence scoring for all responses
• MLX integration for Apple Silicon (when available)
• Enhanced mock responses for development
• Memory usage monitoring and health checks

You can also send natural language messages for AI assistance.
        """.strip()

        return {
            "status": "success",
            "type": "help",
            "message": help_text,
            "data": {"commands": list(self.supported_commands.keys())},
        }
