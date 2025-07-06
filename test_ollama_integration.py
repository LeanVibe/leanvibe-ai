#!/usr/bin/env python3
"""
Test Ollama Integration Script

Tests the Ollama AI service integration directly to validate it works.
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'leanvibe-backend', 'app'))

async def test_ollama_service():
    """Test Ollama service directly"""
    print("🧪 Testing Ollama AI Service Integration")
    print("=" * 50)
    
    try:
        from services.ollama_ai_service import OllamaAIService
        
        # Initialize Ollama service
        print("1. Initializing Ollama service...")
        ollama = OllamaAIService(default_model="mistral:7b-instruct")
        
        # Test initialization
        success = await ollama.initialize()
        if not success:
            print("❌ Failed to initialize Ollama service")
            return False
        
        print(f"✅ Ollama service initialized")
        print(f"   Available models: {', '.join(ollama.available_models)}")
        print(f"   Default model: {ollama.default_model}")
        
        # Test simple generation
        print("\n2. Testing simple generation...")
        response = await ollama.generate("What is 2+2? Be brief.", max_tokens=50)
        
        if response:
            print(f"✅ Generation successful:")
            print(f"   Query: 'What is 2+2? Be brief.'")
            print(f"   Response: {response}")
        else:
            print("❌ Generation failed")
            return False
        
        # Test chat interface
        print("\n3. Testing chat interface...")
        chat_response = await ollama.chat("Hello, how are you?")
        
        if chat_response:
            print(f"✅ Chat successful:")
            print(f"   Response: {chat_response}")
        else:
            print("❌ Chat failed")
            return False
        
        # Test health check
        print("\n4. Testing health check...")
        health = await ollama.health_check()
        
        if health.get("status") == "healthy":
            print(f"✅ Health check passed:")
            print(f"   Status: {health['status']}")
            print(f"   Available: {health['available']}")
            print(f"   Model: {health['default_model']}")
            print(f"   Performance: {health['performance']}")
        else:
            print(f"❌ Health check failed: {health}")
            return False
        
        # Test code analysis
        print("\n5. Testing code analysis...")
        code = "def add(a, b):\n    return a + b"
        analysis = await ollama.analyze_code(code, language="python", analysis_type="explain")
        
        if analysis:
            print(f"✅ Code analysis successful:")
            print(f"   Analysis: {analysis['analysis'][:200]}...")
        else:
            print("❌ Code analysis failed")
            return False
        
        print("\n" + "=" * 50)
        print("🎉 All Ollama tests passed!")
        print(f"📊 Performance stats: {ollama.get_performance_stats()}")
        
        await ollama.close()
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_l3_agent_integration():
    """Test L3 agent with Ollama"""
    print("\n🤖 Testing L3 Agent with Ollama Integration")
    print("=" * 50)
    
    try:
        from agent.l3_coding_agent import L3CodingAgent, AgentDependencies
        
        # Create agent dependencies
        deps = AgentDependencies(
            workspace_path=".",
            client_id="test_client",
            session_data={}
        )
        
        # Initialize agent
        print("1. Initializing L3 agent...")
        agent = L3CodingAgent(deps)
        
        # Test simple query
        print("\n2. Testing simple query...")
        response = await agent.run("What is 2+2?")
        
        print(f"✅ Agent response:")
        print(f"   Status: {response.get('status')}")
        print(f"   Message: {response.get('message')}")
        print(f"   Confidence: {response.get('confidence')}")
        print(f"   Model: {response.get('model')}")
        print(f"   Services: {response.get('services_available')}")
        
        return response.get('status') == 'success'
        
    except Exception as e:
        print(f"❌ L3 Agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    print("🚀 LeanVibe Ollama Integration Test Suite")
    print("=" * 60)
    
    # Test Ollama service directly
    ollama_success = await test_ollama_service()
    
    if ollama_success:
        # Test L3 agent integration
        agent_success = await test_l3_agent_integration()
        
        if agent_success:
            print("\n" + "=" * 60)
            print("🎉 ALL TESTS PASSED - Ollama integration is working!")
            print("🔗 The CLI should now be able to use Ollama for AI responses")
            print("=" * 60)
        else:
            print("\n❌ L3 Agent integration failed")
    else:
        print("\n❌ Ollama service test failed")

if __name__ == "__main__":
    asyncio.run(main())