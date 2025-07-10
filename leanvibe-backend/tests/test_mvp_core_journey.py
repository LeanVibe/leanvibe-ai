"""
MVP Core Journey End-to-End Test

Tests the essential user journey: Developer asks question → gets AI answer in <10s
This validates the core value proposition of LeanVibe MVP.
"""

import asyncio
import time
import pytest
from unittest.mock import AsyncMock, patch

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agent.l3_coding_agent import L3CodingAgent, AgentDependencies
from app.services.ollama_ai_service import OllamaAIService


class TestMVPCoreJourney:
    """Test the core MVP user journey end-to-end"""
    
    @pytest.fixture
    async def l3_agent(self):
        """Create L3 agent for testing"""
        dependencies = AgentDependencies(
            workspace_path=".",
            client_id="test_client",
            session_data={}
        )
        agent = L3CodingAgent(dependencies)
        await agent.initialize()
        return agent
    
    @pytest.fixture
    async def mock_ollama_service(self):
        """Mock Ollama service for controlled testing"""
        service = AsyncMock(spec=OllamaAIService)
        service.is_ready.return_value = True
        service.generate.return_value = "This is a test response from Mistral 7B model."
        service.initialize.return_value = True
        return service
    
    @pytest.mark.asyncio
    async def test_core_journey_simple_question(self, l3_agent):
        """Test core journey: Simple coding question gets answered in <10s"""
        # Test query: Simple code question
        test_query = "What is the purpose of the main function in Python?"
        
        # Measure response time
        start_time = time.time()
        
        # Process query through L3 agent
        response = await l3_agent._process_user_input(test_query)
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # Assertions
        assert response is not None, "Response should not be None"
        assert isinstance(response, str), "Response should be a string"
        assert len(response) > 10, "Response should be meaningful (>10 characters)"
        assert response_time < 10.0, f"Response time {response_time:.2f}s should be <10s for MVP"
        
        # Validate response quality
        assert "main" in response.lower(), "Response should mention 'main'"
        assert not response.startswith("I encountered an error"), "Response should not be an error"
        
        print(f"✅ Core journey test passed in {response_time:.2f}s")
        print(f"Response: {response[:100]}...")
    
    @pytest.mark.asyncio
    async def test_core_journey_file_analysis(self, l3_agent):
        """Test core journey: File analysis request gets meaningful response"""
        # Create a test file for analysis
        test_file_path = "/tmp/test_example.py"
        with open(test_file_path, 'w') as f:
            f.write("""
def calculate_factorial(n):
    if n <= 1:
        return 1
    return n * calculate_factorial(n - 1)

def main():
    result = calculate_factorial(5)
    print(f"5! = {result}")

if __name__ == "__main__":
    main()
""")
        
        # Test query: File analysis
        test_query = f"analyze file {test_file_path}"
        
        # Measure response time
        start_time = time.time()
        
        # Process query through L3 agent
        response = await l3_agent._process_user_input(test_query)
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # Assertions
        assert response is not None, "Response should not be None"
        assert isinstance(response, str), "Response should be a string"
        assert len(response) > 50, "Analysis response should be detailed"
        assert response_time < 15.0, f"File analysis {response_time:.2f}s should be <15s for MVP"
        
        # Validate analysis quality
        assert "factorial" in response.lower(), "Analysis should mention factorial"
        assert not response.startswith("Error analyzing"), "Analysis should not fail"
        
        print(f"✅ File analysis test passed in {response_time:.2f}s")
        print(f"Analysis: {response[:100]}...")
        
        # Cleanup
        import os
        if os.path.exists(test_file_path):
            os.remove(test_file_path)
    
    @pytest.mark.asyncio
    async def test_core_journey_directory_listing(self, l3_agent):
        """Test core journey: Directory listing works efficiently"""
        # Test query: Directory listing
        test_query = "list files in current directory"
        
        # Measure response time
        start_time = time.time()
        
        # Process query through L3 agent
        response = await l3_agent._process_user_input(test_query)
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # Assertions
        assert response is not None, "Response should not be None"
        assert isinstance(response, str), "Response should be a string"
        assert response_time < 5.0, f"Directory listing {response_time:.2f}s should be <5s for MVP"
        
        # Validate directory listing
        assert "Found" in response, "Response should mention found files/directories"
        assert "files" in response, "Response should mention files"
        assert not response.startswith("Error listing"), "Directory listing should not fail"
        
        print(f"✅ Directory listing test passed in {response_time:.2f}s")
        print(f"Listing: {response}")
    
    @pytest.mark.asyncio
    async def test_l3_agent_initialization_performance(self):
        """Test L3 agent initialization time is acceptable for MVP"""
        # Measure initialization time
        start_time = time.time()
        
        dependencies = AgentDependencies(
            workspace_path=".",
            client_id="perf_test_client",
            session_data={}
        )
        agent = L3CodingAgent(dependencies)
        success = await agent.initialize()
        
        end_time = time.time()
        init_time = end_time - start_time
        
        # Assertions
        assert success is True, "Agent initialization should succeed"
        assert init_time < 5.0, f"Agent initialization {init_time:.2f}s should be <5s for MVP"
        
        print(f"✅ Agent initialization completed in {init_time:.2f}s")
    
    @pytest.mark.asyncio
    async def test_ollama_service_availability(self):
        """Test that Ollama service is available and using Mistral 7B"""
        from app.services.ollama_ai_service import get_ollama_service
        
        # Get Ollama service
        service = await get_ollama_service()
        
        # Assertions
        assert service is not None, "Ollama service should be available"
        assert service.is_ready(), "Ollama service should be ready"
        assert service.default_model == "mistral:7b-instruct", "Should use Mistral 7B for performance"
        
        # Test simple generation
        start_time = time.time()
        response = await service.generate("Hello", max_tokens=10)
        end_time = time.time()
        
        generation_time = end_time - start_time
        
        assert response is not None, "Ollama should generate response"
        assert len(response) > 0, "Response should not be empty"
        assert generation_time < 10.0, f"Generation time {generation_time:.2f}s should be <10s"
        
        print(f"✅ Ollama service test passed in {generation_time:.2f}s")
        print(f"Model: {service.default_model}")
        print(f"Response: {response[:50]}...")
    
    @pytest.mark.asyncio
    async def test_full_mvp_user_journey(self, l3_agent):
        """Test complete MVP user journey with realistic developer workflow"""
        # Simulate realistic developer questions
        test_queries = [
            "What is the current directory?",
            "List files in the current directory",
            "What are the main Python files in this project?",
            "How do I optimize Python code for performance?",
        ]
        
        total_start_time = time.time()
        
        for i, query in enumerate(test_queries):
            print(f"\n--- Test Query {i+1}: {query} ---")
            
            start_time = time.time()
            response = await l3_agent._process_user_input(query)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            # Assertions for each query
            assert response is not None, f"Query {i+1} should have response"
            assert isinstance(response, str), f"Query {i+1} response should be string"
            assert len(response) > 5, f"Query {i+1} response should be meaningful"
            assert response_time < 15.0, f"Query {i+1} took {response_time:.2f}s, should be <15s"
            
            print(f"✅ Query {i+1} completed in {response_time:.2f}s")
            print(f"Response: {response[:80]}...")
        
        total_end_time = time.time()
        total_time = total_end_time - total_start_time
        
        print(f"\n🎉 Full MVP journey completed in {total_time:.2f}s")
        print(f"Average response time: {total_time/len(test_queries):.2f}s")
        
        # Overall journey assertions
        assert total_time < 60.0, f"Full journey {total_time:.2f}s should be <60s for MVP"
        assert total_time/len(test_queries) < 15.0, "Average response time should be <15s"


if __name__ == "__main__":
    """Run tests directly for debugging"""
    import sys
    sys.path.append("..")
    
    async def run_tests():
        print("🧪 Running MVP Core Journey Tests...")
        
        # Run individual tests
        test_instance = TestMVPCoreJourney()
        
        # Test 1: Agent initialization
        print("\n1. Testing L3 Agent Initialization...")
        await test_instance.test_l3_agent_initialization_performance()
        
        # Test 2: Ollama service availability
        print("\n2. Testing Ollama Service...")
        await test_instance.test_ollama_service_availability()
        
        # Test 3: Create agent for journey tests
        print("\n3. Creating L3 Agent for journey tests...")
        dependencies = AgentDependencies(
            workspace_path=".",
            client_id="test_client",
            session_data={}
        )
        agent = L3CodingAgent(dependencies)
        await agent.initialize()
        
        # Test 4: Simple question
        print("\n4. Testing Simple Question...")
        await test_instance.test_core_journey_simple_question(agent)
        
        # Test 5: Directory listing
        print("\n5. Testing Directory Listing...")
        await test_instance.test_core_journey_directory_listing(agent)
        
        # Test 6: Full journey
        print("\n6. Testing Full MVP Journey...")
        await test_instance.test_full_mvp_user_journey(agent)
        
        print("\n🎉 All MVP tests completed successfully!")
    
    # Run the tests
    asyncio.run(run_tests())