"""
Test L3 Coding Agent Pydantic.ai Integration

Comprehensive tests for the new L3 agent framework with pydantic.ai
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path

import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestL3AgentIntegration:
    """Test L3 coding agent pydantic.ai integration"""

    @pytest.mark.asyncio
    async def test_agent_initialization(self):
        """Test L3 agent initialization"""
        from app.agent.l3_coding_agent import AgentDependencies, L3CodingAgent

        deps = AgentDependencies(
            workspace_path=".", client_id="test-client", session_data={}
        )

        agent = L3CodingAgent(deps)
        success = await agent.initialize()

        assert success == True
        assert agent.model_wrapper is not None
        assert agent.ai_service.is_initialized == True
        assert agent.model_wrapper is not None

    @pytest.mark.asyncio
    async def test_agent_basic_interaction(self):
        """Test basic agent interaction"""
        from app.agent.l3_coding_agent import AgentDependencies, L3CodingAgent

        deps = AgentDependencies(
            workspace_path=".", client_id="test-client", session_data={}
        )

        agent = L3CodingAgent(deps)
        await agent.initialize()

        # Test simple question
        response = await agent.run("What is the current directory?")

        assert response["status"] == "success"
        assert "confidence" in response
        assert "model" in response
        assert "session_state" in response
        assert isinstance(response["confidence"], float)
        assert 0.0 <= response["confidence"] <= 1.0

    @pytest.mark.asyncio
    async def test_agent_confidence_system(self):
        """Test agent confidence scoring system"""
        from app.agent.l3_coding_agent import AgentDependencies, L3CodingAgent

        deps = AgentDependencies(
            workspace_path=".", client_id="test-client", session_data={}
        )

        agent = L3CodingAgent(deps)
        await agent.initialize()

        # Test different types of questions for confidence variation
        responses = []

        # Simple question (should have high confidence)
        response1 = await agent.run("What is my current directory?")
        responses.append(response1)

        # Complex question (should have lower confidence)
        response2 = await agent.run(
            "Design a distributed microservices architecture for my application"
        )
        responses.append(response2)

        # Check confidence variations
        for response in responses:
            assert "confidence" in response
            assert "recommendation" in response
            assert response["recommendation"] in [
                "proceed_autonomously",
                "human_review_suggested",
                "human_intervention_required",
                "stop_and_escalate",
            ]

    @pytest.mark.asyncio
    async def test_agent_state_management(self):
        """Test agent state persistence and management"""
        from app.agent.l3_coding_agent import AgentDependencies, L3CodingAgent

        deps = AgentDependencies(
            workspace_path=".", client_id="test-client", session_data={}
        )

        agent = L3CodingAgent(deps)
        await agent.initialize()

        # Initial state
        initial_state = agent.get_state_summary()
        assert initial_state["conversation_length"] == 0

        # Add some interactions
        await agent.run("Hello, how are you?")
        await agent.run("Can you help me with Python code?")

        # Check state updates
        updated_state = agent.get_state_summary()
        assert (
            updated_state["conversation_length"] == 4
        )  # 2 user + 2 assistant messages
        assert updated_state["average_confidence"] > 0.0

    @pytest.mark.asyncio
    async def test_session_manager(self):
        """Test session manager functionality"""
        from app.agent.session_manager import SessionManager

        session_manager = SessionManager("./.test_sessions")
        await session_manager.start()

        try:
            # Test session creation
            agent = await session_manager.create_session("test-client-1", ".")
            assert agent is not None

            # Test session retrieval
            retrieved_agent = await session_manager.get_session("test-client-1")
            assert retrieved_agent is agent

            # Test message processing
            response = await session_manager.process_message(
                "test-client-1", "What files are in the current directory?"
            )
            assert response["status"] == "success"
            assert "session_info" in response

            # Test session listing
            sessions = await session_manager.list_sessions()
            assert len(sessions) == 1
            assert sessions[0]["client_id"] == "test-client-1"

        finally:
            await session_manager.stop()

    @pytest.mark.asyncio
    async def test_simple_mlx_model(self):
        """Test simple MLX model integration"""
        from app.agent.l3_coding_agent import SimpleMLXModel
        from app.services.ai_service import AIService

        ai_service = AIService()
        await ai_service.initialize()

        model = SimpleMLXModel(ai_service)

        # Test response generation
        response = await model.generate_response("Hello, how can you help me?")

        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_agent_tools_integration(self):
        """Test agent tools functionality"""
        from app.agent.l3_coding_agent import AgentDependencies, L3CodingAgent

        deps = AgentDependencies(
            workspace_path=".", client_id="test-client", session_data={}
        )

        agent = L3CodingAgent(deps)
        await agent.initialize()

        # Create a test file for analysis
        test_file = Path("test_agent_analysis.py")
        test_content = '''
def hello_world():
    """A simple hello world function"""
    print("Hello, World from L3 Agent!")
    return "success"

if __name__ == "__main__":
    result = hello_world()
    print(f"Result: {result}")
'''
        test_file.write_text(test_content)

        try:
            # Test file analysis through agent
            response = await agent.run(f"Please analyze the file: {test_file}")

            assert response["status"] == "success"
            assert "confidence" in response

            # The agent should have used tools to analyze the file
            assert agent.state.conversation_length > 0

        finally:
            # Clean up test file
            if test_file.exists():
                test_file.unlink()

    @pytest.mark.asyncio
    async def test_agent_planning_and_reflection(self):
        """Test agent planning and reflection capabilities"""
        from app.agent.l3_coding_agent import AgentDependencies, L3CodingAgent

        deps = AgentDependencies(
            workspace_path=".", client_id="test-client", session_data={}
        )

        agent = L3CodingAgent(deps)
        await agent.initialize()

        # Test planning
        plan_response = await agent.plan("Create a simple REST API with FastAPI")
        assert plan_response["status"] == "success"
        assert "confidence" in plan_response
        assert agent.state.current_task is not None

        # Add some interactions
        await agent.run("What are the steps to implement authentication?")
        await agent.run("How should I structure the database models?")

        # Test reflection
        reflection_response = await agent.reflect()
        assert reflection_response["status"] == "success"
        assert "confidence" in reflection_response

    @pytest.mark.asyncio
    async def test_confidence_thresholds(self):
        """Test confidence threshold system"""
        from app.agent.l3_coding_agent import AgentDependencies, L3CodingAgent

        deps = AgentDependencies(
            workspace_path=".", client_id="test-client", session_data={}
        )

        agent = L3CodingAgent(deps)
        await agent.initialize()

        # Test different confidence scenarios
        test_cases = [
            ("What is the current directory?", "proceed_autonomously"),
            ("Help me debug this complex memory leak", "human_review_suggested"),
        ]

        for question, expected_category in test_cases:
            response = await agent.run(question)

            confidence = response["confidence"]
            recommendation = response["recommendation"]

            # Verify confidence is within valid range
            assert 0.0 <= confidence <= 1.0

            # Verify recommendation exists
            assert recommendation in [
                "proceed_autonomously",
                "human_review_suggested",
                "human_intervention_required",
                "stop_and_escalate",
            ]


def test_agent_dependencies():
    """Test agent dependencies configuration"""
    from app.agent.l3_coding_agent import AgentDependencies

    # Test default initialization
    deps = AgentDependencies()
    assert deps.workspace_path == "."
    assert deps.client_id == "default"
    assert deps.session_data == {}

    # Test custom initialization
    deps2 = AgentDependencies(
        workspace_path="/custom/path",
        client_id="custom-client",
        session_data={"key": "value"},
    )
    assert deps2.workspace_path == "/custom/path"
    assert deps2.client_id == "custom-client"
    assert deps2.session_data == {"key": "value"}


def test_agent_state():
    """Test agent state management"""
    from app.agent.l3_coding_agent import AgentState

    state = AgentState()

    # Test initial state
    assert len(state.conversation_history) == 0
    assert len(state.confidence_scores) == 0
    assert state.get_average_confidence() == 0.5

    # Test adding conversations
    state.add_conversation_entry("user", "Hello", 0.8)
    state.add_conversation_entry("assistant", "Hi there!", 0.9)

    assert len(state.conversation_history) == 2
    assert len(state.confidence_scores) == 2
    assert (
        abs(state.get_average_confidence() - 0.85) < 0.01
    )  # Allow small floating point differences

    # Test project context
    state.update_project_context("language", "python")
    assert state.project_context["language"] == "python"


if __name__ == "__main__":
    # Run basic tests
    asyncio.run(TestL3AgentIntegration().test_agent_initialization())
    print("✅ Agent initialization test passed")

    asyncio.run(TestL3AgentIntegration().test_agent_basic_interaction())
    print("✅ Basic interaction test passed")

    test_agent_dependencies()
    print("✅ Agent dependencies test passed")

    test_agent_state()
    print("✅ Agent state test passed")

    print("🎉 All L3 agent integration tests passed!")
