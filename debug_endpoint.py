#!/usr/bin/env python3
"""
Debug the code completion endpoint error
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add the backend directory to path
sys.path.insert(0, str(Path(__file__).parent / "leanvibe-backend"))

from app.agent.enhanced_l3_agent import EnhancedL3CodingAgent, AgentDependencies
from app.services.unified_mlx_service import unified_mlx_service, MLXInferenceStrategy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def debug_endpoint_error():
    """Debug the exact error in the endpoint"""
    
    print("🔍 Debugging Code Completion Endpoint Error")
    print("=" * 50)
    
    # 1. Set up agent with mock strategy (we know this works)
    unified_mlx_service.preferred_strategy = MLXInferenceStrategy.MOCK
    await unified_mlx_service.initialize()
    
    deps = AgentDependencies(
        workspace_path=".",
        client_id="debug-test",
        session_data={}
    )
    
    agent = EnhancedL3CodingAgent(deps)
    agent_init_success = await agent.initialize()
    
    print(f"Agent initialized: {'✅' if agent_init_success else '❌'}")
    
    if not agent_init_success:
        print("❌ Cannot debug - agent failed to initialize")
        return
    
    # 2. Test the exact request that failed
    test_request = json.dumps({
        "file_path": "test.py",
        "cursor_position": 10,
        "content": "def hello_world():\n    # TODO: implement",
        "language": "python"
    })
    
    print(f"\n🧪 Testing agent._mlx_suggest_code_tool with request:")
    print(f"   {test_request}")
    
    try:
        # This is what the endpoint calls
        response_text = await agent._mlx_suggest_code_tool(test_request)
        
        print(f"\n✅ Agent returned response:")
        print(f"   Type: {type(response_text)}")
        print(f"   Content: {response_text}")
        
        # Test if it can be parsed as JSON
        try:
            if isinstance(response_text, str):
                response_json = json.loads(response_text)
                print(f"   ✅ JSON parseable: {list(response_json.keys())}")
                
                # Check for .get() calls on non-dict objects
                for key, value in response_json.items():
                    print(f"   {key}: {type(value)} = {value}")
                    
            else:
                print(f"   ❌ Not a string - this is the problem!")
                print(f"   Actual type: {type(response_text)}")
                print(f"   Has .get method: {hasattr(response_text, 'get')}")
                
        except json.JSONDecodeError as e:
            print(f"   ❌ JSON decode failed: {e}")
            
    except Exception as e:
        print(f"❌ Agent tool failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_endpoint_error())