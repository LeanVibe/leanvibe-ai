"""
Phase 2.3: Test L3 Agent MLX Integration

Tests for complete workflow from L3 agent to MLX inference via AST context.
"""

import pytest
import asyncio
import os
import sys
import tempfile
from unittest.mock import Mock, AsyncMock, patch

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestL3AgentMLXIntegration:
    """Test complete L3 agent to MLX integration workflow"""
    
    @pytest.mark.asyncio
    async def test_enhanced_l3_agent_has_mlx_tools(self):
        """Test Enhanced L3 Agent has MLX-powered tools"""
        from app.agent.enhanced_l3_agent import EnhancedL3CodingAgent, AgentDependencies
        
        deps = AgentDependencies(
            workspace_path=".",
            client_id="test-mlx-tools",
            session_data={}
        )
        
        agent = EnhancedL3CodingAgent(deps)
        
        # Verify MLX tools are available
        mlx_tools = [
            "mlx_suggest_code",
            "mlx_explain_code", 
            "mlx_refactor_code",
            "mlx_debug_code",
            "mlx_optimize_code",
            "mlx_stream_completion"
        ]
        
        for tool in mlx_tools:
            assert tool in agent.tools, f"MLX tool {tool} not found in agent tools"
            assert hasattr(agent, f"_{tool}_tool"), f"MLX tool method _{tool}_tool not found"
    
    @pytest.mark.asyncio
    async def test_mlx_suggest_code_tool_integration(self):
        """Test MLX code suggestion tool with AST context"""
        from app.agent.enhanced_l3_agent import EnhancedL3CodingAgent, AgentDependencies
        
        # Create test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
def calculate_total(items):
    # TODO: implement calculation
    pass

class Calculator:
    def __init__(self):
        self.items = []
""")
            test_file = f.name
        
        try:
            # Mock dependencies
            with patch('app.agent.enhanced_l3_agent.ast_service') as mock_ast_service, \
                 patch('app.agent.enhanced_l3_agent.graph_service') as mock_graph_service, \
                 patch('app.agent.enhanced_l3_agent.incremental_indexer') as mock_indexer, \
                 patch('app.agent.enhanced_l3_agent.mock_mlx_service') as mock_mlx_service:
                
                # Configure mocks
                mock_ast_service.initialize = AsyncMock(return_value=True)
                mock_graph_service.initialize = AsyncMock(return_value=True)
                mock_graph_service.initialized = True
                mock_mlx_service.initialize = AsyncMock(return_value=True)
                
                # Mock project index
                mock_project_index = Mock()
                mock_project_index.total_files = 1
                mock_project_index.supported_files = 1
                mock_project_index.symbols = {}
                mock_project_index.parsing_errors = 0
                mock_project_index.files = {}
                mock_project_index.dependencies = []
                
                mock_indexer.get_or_create_project_index = AsyncMock(return_value=mock_project_index)
                
                # Mock MLX response
                mock_mlx_response = {
                    "status": "success",
                    "response": "Add type hints and implement the calculation logic",
                    "confidence": 0.85,
                    "language": "python",
                    "requires_human_review": False,
                    "suggestions": ["Add error handling", "Write unit tests"],
                    "model": "mlx-community/Qwen2.5-Coder-32B-Instruct",
                    "context_used": {
                        "file_path": test_file,
                        "has_symbol_context": True,
                        "language_detected": "python"
                    }
                }
                mock_mlx_service.generate_code_completion = AsyncMock(return_value=mock_mlx_response)
                
                deps = AgentDependencies(
                    workspace_path=".",
                    client_id="test-mlx-integration",
                    session_data={}
                )
                
                agent = EnhancedL3CodingAgent(deps)
                
                # Test MLX suggest code tool
                import json
                request = json.dumps({
                    "file_path": test_file,
                    "cursor_position": 50
                })
                
                response = await agent._mlx_suggest_code_tool(request)
                
                # Parse response
                result = json.loads(response)
                
                # Verify response structure
                assert "suggestions" in result
                assert "confidence" in result
                assert "language" in result
                assert result["confidence"] == 0.85
                assert result["language"] == "python"
                assert "type hints" in result["suggestions"].lower()
                
                # Verify MLX service was called with proper context
                mock_mlx_service.generate_code_completion.assert_called_once()
                call_args = mock_mlx_service.generate_code_completion.call_args
                context_arg, intent_arg = call_args[0]
                assert intent_arg == "suggest"
                assert "file_path" in context_arg
        
        finally:
            os.unlink(test_file)
    
    @pytest.mark.asyncio
    async def test_mlx_explain_code_tool_integration(self):
        """Test MLX code explanation tool"""
        from app.agent.enhanced_l3_agent import EnhancedL3CodingAgent, AgentDependencies
        
        # Create test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write("""
async function fetchUserData(userId) {
    const response = await fetch('/api/users/' + userId);
    return response.json();
}
""")
            test_file = f.name
        
        try:
            # Mock dependencies for explanation
            with patch('app.agent.enhanced_l3_agent.mock_mlx_service') as mock_mlx_service:
                
                mock_mlx_service.initialize = AsyncMock(return_value=True)
                
                # Mock MLX explanation response
                mock_explanation_response = {
                    "status": "success",
                    "response": "This is an async function that fetches user data from an API endpoint",
                    "confidence": 0.9,
                    "language": "javascript",
                    "requires_human_review": False,
                    "suggestions": ["Add error handling", "Use TypeScript"],
                    "model": "mlx-community/Qwen2.5-Coder-32B-Instruct",
                    "context_used": {
                        "file_path": test_file,
                        "has_symbol_context": True,
                        "language_detected": "javascript"
                    }
                }
                mock_mlx_service.generate_code_completion = AsyncMock(return_value=mock_explanation_response)
                
                deps = AgentDependencies(
                    workspace_path=".",
                    client_id="test-explain",
                    session_data={}
                )
                
                agent = EnhancedL3CodingAgent(deps)
                
                # Test explain tool
                import json
                request = json.dumps({
                    "file_path": test_file,
                    "cursor_position": 30
                })
                
                response = await agent._mlx_explain_code_tool(request)
                
                # Parse and verify response
                result = json.loads(response)
                assert "explanation" in result
                assert "confidence" in result
                assert result["confidence"] == 0.9
                assert "async function" in result["explanation"].lower()
                
                # Verify MLX service called with explain intent
                mock_mlx_service.generate_code_completion.assert_called_once()
                call_args = mock_mlx_service.generate_code_completion.call_args
                _, intent_arg = call_args[0]
                assert intent_arg == "explain"
        
        finally:
            os.unlink(test_file)
    
    @pytest.mark.asyncio
    async def test_mlx_refactor_code_tool_integration(self):
        """Test MLX refactoring tool"""
        from app.agent.enhanced_l3_agent import EnhancedL3CodingAgent, AgentDependencies
        
        with patch('app.agent.enhanced_l3_agent.mock_mlx_service') as mock_mlx_service:
            
            mock_mlx_service.initialize = AsyncMock(return_value=True)
            
            # Mock refactoring response
            mock_refactor_response = {
                "status": "success",
                "response": "Consider extracting methods and adding type hints",
                "confidence": 0.75,
                "language": "python", 
                "requires_human_review": True,
                "suggestions": ["Test refactored code", "Profile performance"],
                "model": "mlx-community/Qwen2.5-Coder-32B-Instruct",
                "context_used": {
                    "file_path": "/test/file.py",
                    "has_symbol_context": False,
                    "language_detected": "python"
                }
            }
            mock_mlx_service.generate_code_completion = AsyncMock(return_value=mock_refactor_response)
            
            deps = AgentDependencies(
                workspace_path=".",
                client_id="test-refactor",
                session_data={}
            )
            
            agent = EnhancedL3CodingAgent(deps)
            
            # Test refactor tool
            import json
            request = json.dumps({
                "file_path": "/test/file.py",
                "cursor_position": 100
            })
            
            response = await agent._mlx_refactor_code_tool(request)
            
            # Verify refactoring response
            result = json.loads(response)
            assert "refactoring_suggestions" in result
            assert "requires_review" in result
            assert result["requires_review"] == True
            assert "extract" in result["refactoring_suggestions"].lower()
            
            # Verify correct intent
            call_args = mock_mlx_service.generate_code_completion.call_args
            _, intent_arg = call_args[0]
            assert intent_arg == "refactor"
    
    @pytest.mark.asyncio
    async def test_mlx_debug_and_optimize_tools(self):
        """Test MLX debug and optimize tools"""
        from app.agent.enhanced_l3_agent import EnhancedL3CodingAgent, AgentDependencies
        
        with patch('app.agent.enhanced_l3_agent.mock_mlx_service') as mock_mlx_service:
            
            mock_mlx_service.initialize = AsyncMock(return_value=True)
            
            deps = AgentDependencies(
                workspace_path=".",
                client_id="test-debug-optimize",
                session_data={}
            )
            
            agent = EnhancedL3CodingAgent(deps)
            
            # Test debug tool
            debug_response = {
                "status": "success",
                "response": "Check for null pointer exceptions and boundary conditions",
                "confidence": 0.65,
                "language": "swift",
                "requires_human_review": True,
                "suggestions": ["Add logging", "Use debugger"],
                "model": "mlx-community/Qwen2.5-Coder-32B-Instruct",
                "context_used": {"language_detected": "swift"}
            }
            mock_mlx_service.generate_code_completion = AsyncMock(return_value=debug_response)
            
            import json
            debug_request = json.dumps({"file_path": "/test/file.swift", "cursor_position": 50})
            
            debug_result = await agent._mlx_debug_code_tool(debug_request)
            debug_parsed = json.loads(debug_result)
            
            assert "debug_analysis" in debug_parsed
            assert "null pointer" in debug_parsed["debug_analysis"].lower()
            
            # Test optimize tool  
            optimize_response = {
                "status": "success",
                "response": "Use more efficient algorithms and data structures",
                "confidence": 0.7,
                "language": "swift",
                "requires_human_review": False,
                "suggestions": ["Profile code", "Benchmark improvements"],
                "model": "mlx-community/Qwen2.5-Coder-32B-Instruct",
                "context_used": {"language_detected": "swift"}
            }
            mock_mlx_service.generate_code_completion = AsyncMock(return_value=optimize_response)
            
            optimize_request = json.dumps({"file_path": "/test/file.swift", "cursor_position": 75})
            
            optimize_result = await agent._mlx_optimize_code_tool(optimize_request)
            optimize_parsed = json.loads(optimize_result)
            
            assert "optimization_suggestions" in optimize_parsed
            assert "efficient" in optimize_parsed["optimization_suggestions"].lower()
    
    @pytest.mark.asyncio
    async def test_mlx_streaming_tool(self):
        """Test MLX streaming completion tool"""
        from app.agent.enhanced_l3_agent import EnhancedL3CodingAgent, AgentDependencies
        
        deps = AgentDependencies(
            workspace_path=".",
            client_id="test-streaming",
            session_data={}
        )
        
        agent = EnhancedL3CodingAgent(deps)
        
        # Test streaming tool
        import json
        stream_request = json.dumps({
            "file_path": "/test/file.py",
            "cursor_position": 100,
            "intent": "suggest"
        })
        
        response = await agent._mlx_stream_completion_tool(stream_request)
        result = json.loads(response)
        
        assert "status" in result
        assert result["status"] == "streaming_started"
        assert result["intent"] == "suggest"
        assert result["context_ready"] == True
        assert "WebSocket" in result["message"]
    
    @pytest.mark.asyncio
    async def test_error_handling_in_mlx_tools(self):
        """Test error handling in MLX tools"""
        from app.agent.enhanced_l3_agent import EnhancedL3CodingAgent, AgentDependencies
        
        deps = AgentDependencies(
            workspace_path=".",
            client_id="test-errors",
            session_data={}
        )
        
        agent = EnhancedL3CodingAgent(deps)
        
        # Test with missing file_path
        response = await agent._mlx_suggest_code_tool("{}")
        assert "Error: file_path required" in response
        
        # Test with invalid JSON
        response = await agent._mlx_explain_code_tool("invalid json")
        assert "Error" in response  # Should handle error gracefully
        
        # Test streaming with invalid JSON
        response = await agent._mlx_stream_completion_tool("invalid")
        assert "Error: Invalid JSON request" in response
    
    def test_enhanced_agent_tool_count(self):
        """Test Enhanced L3 Agent has all expected tools"""
        from app.agent.enhanced_l3_agent import EnhancedL3CodingAgent, AgentDependencies
        
        deps = AgentDependencies(
            workspace_path=".",
            client_id="test-tool-count",
            session_data={}
        )
        
        agent = EnhancedL3CodingAgent(deps)
        
        # Should have original tools + AST tools + MLX tools
        # Base L3 agent: ~3 tools
        # Enhanced L3 agent: ~26 tools  
        # AST tools: 3 tools  
        # MLX tools: 6 tools
        # Total should be around 32 tools
        assert len(agent.tools) >= 30, f"Expected at least 30 tools, got {len(agent.tools)}"
        
        # Verify we have all key tool categories
        tool_names = list(agent.tools.keys())
        
        # Base L3 tools
        assert "analyze_file" in tool_names
        assert "file_operations" in tool_names
        assert "assess_confidence" in tool_names
        
        # AST tools
        assert "get_file_context" in tool_names
        assert "get_completion_context" in tool_names
        assert "suggest_code_completion" in tool_names
        
        # MLX tools
        assert "mlx_suggest_code" in tool_names
        assert "mlx_explain_code" in tool_names
        assert "mlx_refactor_code" in tool_names
        assert "mlx_debug_code" in tool_names
        assert "mlx_optimize_code" in tool_names
        assert "mlx_stream_completion" in tool_names