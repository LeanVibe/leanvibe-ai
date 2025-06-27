"""
Test Enhanced L3 Agent with AST Integration

Tests for the enhanced L3 agent with Tree-sitter AST capabilities.
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path

import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestEnhancedL3Agent:
    """Test enhanced L3 agent with AST capabilities"""

    @pytest.mark.asyncio
    async def test_enhanced_agent_initialization(self):
        """Test enhanced agent initialization"""
        from app.agent.enhanced_l3_agent import AgentDependencies, EnhancedL3CodingAgent

        deps = AgentDependencies(
            workspace_path=".", client_id="test-enhanced-client", session_data={}
        )

        agent = EnhancedL3CodingAgent(deps)
        success = await agent.initialize()

        assert success == True
        assert agent.model_wrapper is not None
        assert hasattr(agent, "project_context")
        assert hasattr(agent, "project_index")

    @pytest.mark.asyncio
    async def test_project_analysis_tool(self):
        """Test project analysis tool"""
        from app.agent.enhanced_l3_agent import AgentDependencies, EnhancedL3CodingAgent

        # Create a test project
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            # Create test files
            (project_path / "main.py").write_text(
                '''
def main():
    """Main function"""
    print("Hello World")
    return 0

class Calculator:
    def add(self, a, b):
        return a + b
    
    def multiply(self, a, b):
        return a * b

if __name__ == "__main__":
    main()
'''
            )

            (project_path / "utils.py").write_text(
                '''
import math

def calculate_area(radius):
    """Calculate circle area"""
    return math.pi * radius ** 2

def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)
'''
            )

            deps = AgentDependencies(
                workspace_path=str(project_path),
                client_id="test-project-client",
                session_data={},
            )

            agent = EnhancedL3CodingAgent(deps)
            await agent.initialize()

            # Test project analysis
            result = await agent._analyze_project_tool()

            assert result["status"] == "success"
            assert result["type"] == "project_analysis"
            assert "data" in result
            assert "confidence" in result

            data = result["data"]
            assert data["supported_files"] >= 2
            assert data["total_symbols"] > 0
            assert "symbol_breakdown" in data
            assert "language_breakdown" in data
            assert "complexity" in data

    @pytest.mark.asyncio
    async def test_symbol_exploration(self):
        """Test symbol exploration functionality"""
        from app.agent.enhanced_l3_agent import AgentDependencies, EnhancedL3CodingAgent

        # Create a test project with clear symbols
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            (project_path / "functions.py").write_text(
                '''
def helper_function():
    """A helper function"""
    return "helper"

def another_helper():
    """Another helper function"""
    return helper_function()

class HelperClass:
    def helper_method(self):
        return helper_function()
'''
            )

            deps = AgentDependencies(
                workspace_path=str(project_path),
                client_id="test-symbol-client",
                session_data={},
            )

            agent = EnhancedL3CodingAgent(deps)
            await agent.initialize()

            # Test symbol exploration
            result = await agent._explore_symbols_tool("helper")

            assert result["status"] == "success"
            assert result["type"] == "symbol_exploration"
            assert "data" in result

            data = result["data"]
            assert (
                data["matching_symbols"] >= 3
            )  # helper_function, another_helper, HelperClass
            assert "symbols_by_type" in data
            assert "summary" in data

    @pytest.mark.asyncio
    async def test_reference_finding(self):
        """Test reference finding functionality"""
        from app.agent.enhanced_l3_agent import AgentDependencies, EnhancedL3CodingAgent

        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            (project_path / "target.py").write_text(
                '''
def target_function():
    """Target function to find references for"""
    return "target"
'''
            )

            (project_path / "usage.py").write_text(
                """
from target import target_function

def use_target():
    result = target_function()
    return result

def another_usage():
    return target_function()
"""
            )

            deps = AgentDependencies(
                workspace_path=str(project_path),
                client_id="test-ref-client",
                session_data={},
            )

            agent = EnhancedL3CodingAgent(deps)
            await agent.initialize()

            # Test reference finding
            result = await agent._find_references_tool("target_function")

            assert result["status"] == "success"
            assert result["type"] == "reference_analysis"
            assert "data" in result

            data = result["data"]
            assert data["total_references"] > 0
            assert "definitions" in data
            assert "usages" in data
            assert "summary" in data

    @pytest.mark.asyncio
    async def test_complexity_analysis(self):
        """Test complexity analysis functionality"""
        from app.agent.enhanced_l3_agent import AgentDependencies, EnhancedL3CodingAgent

        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            # Create files with varying complexity
            (project_path / "simple.py").write_text(
                """
def simple_function(a, b):
    return a + b
"""
            )

            (project_path / "complex.py").write_text(
                """
def complex_function(x, y, z):
    if x > 0:
        if y > 0:
            if z > 0:
                for i in range(10):
                    if i % 2 == 0:
                        x += i
                    else:
                        y += i
                return x + y + z
            else:
                return x + y
        else:
            return x
    else:
        return 0

def another_complex_function(data):
    try:
        if isinstance(data, list):
            for item in data:
                if item > 0:
                    yield item * 2
                elif item < 0:
                    yield abs(item)
                else:
                    continue
        elif isinstance(data, dict):
            for key, value in data.items():
                if value:
                    yield f"{key}: {value}"
    except Exception as e:
        return str(e)
"""
            )

            deps = AgentDependencies(
                workspace_path=str(project_path),
                client_id="test-complexity-client",
                session_data={},
            )

            agent = EnhancedL3CodingAgent(deps)
            await agent.initialize()

            # Test complexity analysis
            result = await agent._check_complexity_tool()

            assert result["status"] == "success"
            assert result["type"] == "complexity_analysis"
            assert "data" in result

            data = result["data"]
            assert "total_complexity" in data
            assert "average_complexity" in data
            assert "top_complex_files" in data
            assert data["total_complexity"] > 0
            assert data["average_complexity"] > 0

    @pytest.mark.asyncio
    async def test_enhanced_user_input_processing(self):
        """Test enhanced user input processing with AST awareness"""
        from app.agent.enhanced_l3_agent import AgentDependencies, EnhancedL3CodingAgent

        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            (project_path / "example.py").write_text(
                """
class ExampleClass:
    def example_method(self):
        return "example"

def example_function():
    return ExampleClass().example_method()
"""
            )

            deps = AgentDependencies(
                workspace_path=str(project_path),
                client_id="test-input-client",
                session_data={},
            )

            agent = EnhancedL3CodingAgent(deps)
            await agent.initialize()

            # Test various types of user input
            test_cases = [
                ("analyze project", "project analysis"),
                ("find symbol example", "symbol exploration"),
                ("what's the complexity of my code", "complexity"),
                ("show me the architecture", "project analysis"),
            ]

            for user_input, expected_content in test_cases:
                response = await agent._process_user_input(user_input)

                assert isinstance(response, str)
                assert len(response) > 0
                # Response should contain relevant information based on the query
                assert any(
                    keyword in response.lower() for keyword in expected_content.split()
                )

    @pytest.mark.asyncio
    async def test_contextual_prompt_creation(self):
        """Test contextual prompt creation with project awareness"""
        from app.agent.enhanced_l3_agent import AgentDependencies, EnhancedL3CodingAgent

        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            (project_path / "test.py").write_text(
                """
def test_function():
    pass
"""
            )

            deps = AgentDependencies(
                workspace_path=str(project_path),
                client_id="test-context-client",
                session_data={},
            )

            agent = EnhancedL3CodingAgent(deps)
            await agent.initialize()

            # Test contextual prompt creation
            prompt = await agent._create_contextual_prompt("How do I optimize my code?")

            assert isinstance(prompt, str)
            assert "LeenVibe L3 coding agent" in prompt
            assert "Project Context:" in prompt
            assert "Workspace:" in prompt
            assert str(project_path) in prompt

    @pytest.mark.asyncio
    async def test_enhanced_state_summary(self):
        """Test enhanced state summary with AST information"""
        from app.agent.enhanced_l3_agent import AgentDependencies, EnhancedL3CodingAgent

        deps = AgentDependencies(
            workspace_path=".", client_id="test-state-client", session_data={}
        )

        agent = EnhancedL3CodingAgent(deps)
        await agent.initialize()

        # Get enhanced state summary
        state = agent.get_enhanced_state_summary()

        assert "project_indexed" in state
        assert "last_index_update" in state
        assert "project_files" in state
        assert "project_symbols" in state
        assert "project_context" in state
        assert "ast_capabilities" in state

        # Check AST capabilities
        capabilities = state["ast_capabilities"]
        expected_capabilities = [
            "project_analysis",
            "symbol_exploration",
            "reference_finding",
            "complexity_analysis",
            "contextual_file_analysis",
        ]

        for capability in expected_capabilities:
            assert capability in capabilities


def test_enhanced_agent_integration():
    """Test basic enhanced agent integration"""
    from app.agent.enhanced_l3_agent import AgentDependencies, EnhancedL3CodingAgent

    deps = AgentDependencies()
    agent = EnhancedL3CodingAgent(deps)

    # Check that enhanced tools are available
    expected_tools = [
        "analyze_project",
        "find_references",
        "impact_analysis",
        "suggest_refactoring",
        "explore_symbols",
        "check_complexity",
    ]

    for tool in expected_tools:
        assert tool in agent.tools


if __name__ == "__main__":
    # Run basic tests
    test_enhanced_agent_integration()
    print("✅ Enhanced agent integration test passed")

    asyncio.run(TestEnhancedL3Agent().test_enhanced_agent_initialization())
    print("✅ Enhanced agent initialization test passed")

    print("🎉 All enhanced L3 agent tests passed!")
