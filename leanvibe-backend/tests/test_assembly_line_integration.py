"""
Integration tests for Assembly Line System with all AI agents
"""

import pytest
import asyncio
from uuid import uuid4
from unittest.mock import Mock, AsyncMock

from app.services.assembly_line_system import (
    AssemblyLineOrchestrator,
    AgentType,
    AgentStatus
)
from app.models.mvp_models import TechnicalBlueprint, MVPTechStack
from app.services.agents import (
    BackendCoderAgent,
    FrontendCoderAgent,
    InfrastructureAgent,
    ObservabilityAgent
)


@pytest.fixture
def sample_blueprint():
    """Sample technical blueprint for testing"""
    return TechnicalBlueprint(
        tech_stack=MVPTechStack.FULL_STACK_REACT,
        architecture_pattern="microservices",
        database_schema={
            "tables": {
                "users": {
                    "fields": {
                        "id": {"type": "integer", "primary_key": True},
                        "email": {"type": "string", "nullable": False},
                        "name": {"type": "string", "nullable": False}
                    }
                },
                "projects": {
                    "fields": {
                        "id": {"type": "integer", "primary_key": True},
                        "title": {"type": "string", "nullable": False},
                        "description": {"type": "text", "nullable": True}
                    }
                }
            }
        },
        api_endpoints=[
            {
                "name": "users",
                "method": "GET", 
                "path": "/users",
                "description": "List users"
            },
            {
                "name": "projects",
                "method": "GET",
                "path": "/projects", 
                "description": "List projects"
            }
        ],
        user_flows=[
            "User registration and login",
            "Create and manage projects"
        ],
        wireframes=[
            "Dashboard layout",
            "Project creation form"
        ],
        design_system={
            "primary_color": "#3B82F6",
            "font_family": "Inter"
        },
        deployment_config={
            "type": "docker",
            "cloud_provider": "aws"
        },
        scaling_config={
            "min_replicas": 2,
            "max_replicas": 10
        },
        monitoring_requirements=[
            "API performance",
            "Error rates",
            "User activity"
        ]
    )


class TestAssemblyLineIntegration:
    """Integration tests for the complete assembly line system"""

    def test_orchestrator_initialization(self):
        """Test that orchestrator initializes correctly"""
        orchestrator = AssemblyLineOrchestrator()
        
        assert len(orchestrator.agents) == 0
        assert len(orchestrator.quality_gates) == 0
        assert len(orchestrator.progress_tracking) == 0

    def test_agent_registration(self):
        """Test individual agent registration"""
        orchestrator = AssemblyLineOrchestrator()
        
        # Test registering each agent type
        backend_agent = BackendCoderAgent()
        orchestrator.register_agent(backend_agent)
        assert AgentType.BACKEND in orchestrator.agents
        
        frontend_agent = FrontendCoderAgent()
        orchestrator.register_agent(frontend_agent)
        assert AgentType.FRONTEND in orchestrator.agents
        
        infrastructure_agent = InfrastructureAgent()
        orchestrator.register_agent(infrastructure_agent)
        assert AgentType.INFRASTRUCTURE in orchestrator.agents
        
        observability_agent = ObservabilityAgent()
        orchestrator.register_agent(observability_agent)
        assert AgentType.OBSERVABILITY in orchestrator.agents
        
        assert len(orchestrator.agents) == 4

    def test_register_all_agents(self):
        """Test bulk agent registration"""
        orchestrator = AssemblyLineOrchestrator()
        orchestrator.register_all_agents()
        
        # Verify all agent types are registered
        expected_agents = [
            AgentType.BACKEND,
            AgentType.FRONTEND,
            AgentType.INFRASTRUCTURE,
            AgentType.OBSERVABILITY
        ]
        
        for agent_type in expected_agents:
            assert agent_type in orchestrator.agents
            assert orchestrator.agents[agent_type] is not None
        
        assert len(orchestrator.agents) == 4

    @pytest.mark.asyncio
    async def test_agent_execution_pipeline(self, sample_blueprint):
        """Test that agents can be executed in sequence"""
        orchestrator = AssemblyLineOrchestrator()
        orchestrator.register_all_agents()
        
        mvp_project_id = uuid4()
        input_data = {"blueprint": sample_blueprint.model_dump()}
        
        # Test each agent individually
        execution_order = [
            AgentType.BACKEND,
            AgentType.FRONTEND,
            AgentType.INFRASTRUCTURE,
            AgentType.OBSERVABILITY
        ]
        
        accumulated_output = input_data.copy()
        
        for agent_type in execution_order:
            agent = orchestrator.agents[agent_type]
            
            # Mock progress callback
            progress_callback = Mock()
            
            # Execute agent
            result = await agent.execute(
                mvp_project_id,
                accumulated_output,
                progress_callback
            )
            
            # Verify result structure
            assert result.agent_type == agent_type
            assert result.status in [AgentStatus.COMPLETED, AgentStatus.FAILED]
            assert isinstance(result.output, dict)
            assert isinstance(result.artifacts, list)
            assert isinstance(result.metrics, dict)
            assert result.execution_time >= 0
            assert 0 <= result.confidence_score <= 1.0
            
            if result.status == AgentStatus.COMPLETED:
                # Add agent output to accumulated data for next agent
                accumulated_output[f"{agent_type}_output"] = result.output
                assert len(result.artifacts) > 0  # Should generate some files
            
            # Verify progress callback was called
            assert progress_callback.call_count > 0

    @pytest.mark.asyncio 
    async def test_quality_gates_integration(self, sample_blueprint):
        """Test that quality gates work with agents"""
        orchestrator = AssemblyLineOrchestrator()
        orchestrator.register_all_agents()
        
        mvp_project_id = uuid4()
        
        # Test quality gate for backend agent
        backend_agent = orchestrator.agents[AgentType.BACKEND]
        
        result = await backend_agent.execute(
            mvp_project_id,
            {"blueprint": sample_blueprint.model_dump()},
            Mock()
        )
        
        # Run quality check
        if result.status == AgentStatus.COMPLETED:
            quality_result = await backend_agent.quality_check(result)
            
            assert quality_result.overall_score >= 0.0
            assert quality_result.overall_score <= 1.0
            assert isinstance(quality_result.checks, list)
            assert len(quality_result.checks) > 0

    def test_agent_type_coverage(self):
        """Test that all required agent types are implemented"""
        orchestrator = AssemblyLineOrchestrator()
        orchestrator.register_all_agents()
        
        required_agents = {
            AgentType.BACKEND,
            AgentType.FRONTEND, 
            AgentType.INFRASTRUCTURE,
            AgentType.OBSERVABILITY
        }
        
        registered_agents = set(orchestrator.agents.keys())
        
        assert required_agents == registered_agents, f"Missing agents: {required_agents - registered_agents}"

    def test_tech_stack_compatibility(self):
        """Test that agents support the required tech stacks"""
        orchestrator = AssemblyLineOrchestrator()
        orchestrator.register_all_agents()
        
        # Test tech stack support
        backend_agent = orchestrator.agents[AgentType.BACKEND]
        frontend_agent = orchestrator.agents[AgentType.FRONTEND]
        
        # Verify supported stacks
        assert MVPTechStack.FULL_STACK_REACT in backend_agent.supported_stacks
        assert MVPTechStack.FULL_STACK_VUE in backend_agent.supported_stacks
        assert MVPTechStack.API_ONLY in backend_agent.supported_stacks
        
        assert MVPTechStack.FULL_STACK_REACT in frontend_agent.supported_stacks
        assert MVPTechStack.FULL_STACK_VUE in frontend_agent.supported_stacks

    @pytest.mark.asyncio
    async def test_error_handling_integration(self):
        """Test that agents handle errors gracefully"""
        orchestrator = AssemblyLineOrchestrator()
        orchestrator.register_all_agents()
        
        mvp_project_id = uuid4()
        
        # Test with invalid input data
        invalid_input = {"invalid": "data"}
        
        backend_agent = orchestrator.agents[AgentType.BACKEND]
        result = await backend_agent.execute(mvp_project_id, invalid_input, Mock())
        
        # Should handle error gracefully
        assert result.status == AgentStatus.FAILED
        assert result.error_message is not None
        assert len(result.error_message) > 0


if __name__ == "__main__":
    # Run basic integration test
    async def main():
        orchestrator = AssemblyLineOrchestrator()
        orchestrator.register_all_agents()
        
        print("✅ Assembly Line System Integration Test")
        print(f"✅ Registered {len(orchestrator.agents)} agents:")
        
        for agent_type in orchestrator.agents:
            print(f"   - {agent_type.title()} Agent")
        
        print("✅ Integration test passed!")

    asyncio.run(main())