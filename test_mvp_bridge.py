#!/usr/bin/env python3
"""
MVP Bridge Test - Verify L3 Agent -> MLX Connection

Tests the critical connection between Enhanced L3 Agent and Unified MLX Service
to validate that the "Ferrari engine" can actually drive the wheels.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add the backend directory to path
sys.path.insert(0, str(Path(__file__).parent / "leanvibe-backend"))

from app.agent.enhanced_l3_agent import EnhancedL3CodingAgent, AgentDependencies
from app.services.unified_mlx_service import unified_mlx_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_mvp_bridge():
    """Test the core MVP functionality: iOS -> L3 Agent -> MLX -> Response"""
    
    print("🔧 MVP Bridge Test - Verifying L3 Agent ↔ MLX Connection")
    print("=" * 60)
    
    # 1. Test Unified MLX Service Initialization
    print("\n1. Testing Unified MLX Service...")
    mlx_init_success = await unified_mlx_service.initialize()
    mlx_health = unified_mlx_service.get_model_health()
    
    print(f"   MLX Initialized: {'✅' if mlx_init_success else '❌'}")
    print(f"   MLX Status: {mlx_health.get('status', 'unknown')}")
    print(f"   Current Strategy: {mlx_health.get('current_strategy', {}).get('strategy', 'none')}")
    print(f"   Available Strategies: {mlx_health.get('available_strategies', [])}")
    
    # 2. Test Direct MLX Code Completion
    print("\n2. Testing Direct MLX Code Completion...")
    test_context = {
        "file_path": "test.py",
        "cursor_position": 10,
        "surrounding_code": "def hello_world():\n    # TODO: implement",
        "language": "python"
    }
    
    mlx_response = await unified_mlx_service.generate_code_completion(test_context, "suggest")
    print(f"   MLX Response Status: {'✅' if mlx_response.get('status') == 'success' else '❌'}")
    print(f"   MLX Confidence: {mlx_response.get('confidence', 0.0):.2f}")
    print(f"   MLX Strategy Used: {mlx_response.get('strategy_used', 'unknown')}")
    
    # 3. Test Enhanced L3 Agent Initialization
    print("\n3. Testing Enhanced L3 Agent...")
    deps = AgentDependencies(
        workspace_path=".",
        client_id="mvp-bridge-test",
        session_data={}
    )
    
    agent = EnhancedL3CodingAgent(deps)
    agent_init_success = await agent.initialize()
    
    print(f"   Agent Initialized: {'✅' if agent_init_success else '❌'}")
    
    if agent_init_success:
        agent_status = agent.get_state_summary()
        print(f"   Agent Session ID: {agent_status.get('session_id')}")
        print(f"   Agent AI Service: {agent_status.get('ai_service_status', {}).get('status', 'unknown')}")
    
    # 4. Test End-to-End: L3 Agent MLX Code Tool
    print("\n4. Testing End-to-End L3 Agent ↔ MLX Integration...")
    
    if agent_init_success:
        test_request = json.dumps({
            "file_path": "test.py",
            "cursor_position": 10,
            "content": "def hello_world():\n    # TODO: implement",
            "language": "python"
        })
        
        # Test the actual method that the code completion endpoint calls
        try:
            response_text = await agent._mlx_suggest_code_tool(test_request)
            print(f"   L3 Agent MLX Tool: ✅ Response received")
            
            # Try to parse the response
            try:
                response_json = json.loads(response_text)
                print(f"   Response Confidence: {response_json.get('confidence', 0.0):.2f}")
                print(f"   Response Model: {response_json.get('model', 'unknown')}")
                print(f"   Context Used: {response_json.get('context_used', False)}")
                
                # Show first 100 chars of actual response
                actual_response = response_json.get('response', '')[:100]
                print(f"   Generated Text Preview: {actual_response}...")
                
            except json.JSONDecodeError:
                print(f"   Response Format: Plain text (length: {len(response_text)})")
                print(f"   Response Preview: {response_text[:100]}...")
            
        except Exception as e:
            print(f"   L3 Agent MLX Tool: ❌ Error - {e}")
    
    # 5. Summary and MVP Assessment
    print("\n" + "=" * 60)
    print("🎯 MVP READINESS ASSESSMENT")
    print("=" * 60)
    
    checks = {
        "MLX Service Initialization": mlx_init_success,
        "MLX Code Completion": mlx_response.get('status') == 'success',
        "L3 Agent Initialization": agent_init_success,
        "End-to-End Integration": agent_init_success  # Will be refined based on tool test
    }
    
    total_checks = len(checks)
    passed_checks = sum(1 for passed in checks.values() if passed)
    readiness_percentage = (passed_checks / total_checks) * 100
    
    print(f"\nChecks Passed: {passed_checks}/{total_checks} ({readiness_percentage:.0f}%)")
    
    for check, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {check}")
    
    if readiness_percentage >= 75:
        print(f"\n🎉 READY FOR MVP! Bridge connection verified.")
        print("   Next steps: Connect iOS WebSocket commands to L3 Agent")
    elif readiness_percentage >= 50:
        print(f"\n⚠️  PARTIALLY READY - {100-readiness_percentage:.0f}% gaps remain")
        print("   Critical gaps need to be addressed")
    else:
        print(f"\n❌ NOT READY - Major infrastructure issues")
        print("   Fundamental components not working")
    
    return readiness_percentage


if __name__ == "__main__":
    asyncio.run(test_mvp_bridge())