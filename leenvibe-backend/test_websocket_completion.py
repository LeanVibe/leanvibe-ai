#!/usr/bin/env python3
"""
Test WebSocket Code Completion Integration

This script tests the new WebSocket code completion functionality
by sending a code completion request through the WebSocket connection.
"""

import asyncio
import json
import websockets
import sys

async def test_websocket_code_completion():
    """Test code completion through WebSocket"""
    
    uri = "ws://localhost:8000/ws/test-client-ws"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket")
            
            # Test code completion request
            test_request = {
                "type": "code_completion",
                "file_path": "/test/calculator.py",
                "cursor_position": 50,
                "intent": "suggest",
                "content": "def add(a, b):\n    # TODO: implement addition\n    pass",
                "language": "python"
            }
            
            print(f"📤 Sending code completion request: {test_request['intent']}")
            await websocket.send(json.dumps(test_request))
            
            # Wait for response
            response = await websocket.recv()
            response_data = json.loads(response)
            
            print(f"📥 Received response:")
            print(f"   Status: {response_data.get('status')}")
            print(f"   Type: {response_data.get('type')}")
            print(f"   Intent: {response_data.get('intent')}")
            print(f"   Confidence: {response_data.get('confidence')}")
            print(f"   Requires Review: {response_data.get('requires_review')}")
            print(f"   Response Length: {len(response_data.get('response', ''))}")
            print(f"   Suggestions: {len(response_data.get('suggestions', []))}")
            
            if response_data.get('status') == 'success':
                print("✅ Code completion request successful!")
                return True
            else:
                print(f"❌ Code completion failed: {response_data.get('message')}")
                return False
                
    except websockets.exceptions.ConnectionRefused:
        print("❌ Could not connect to WebSocket server. Is the server running on localhost:8000?")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def test_multiple_intents():
    """Test all code completion intents"""
    
    intents = ["suggest", "explain", "refactor", "debug", "optimize"]
    uri = "ws://localhost:8000/ws/test-client-ws-multi"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket for multi-intent test")
            
            results = {}
            
            for intent in intents:
                test_request = {
                    "type": "code_completion",
                    "file_path": "/test/sample.py",
                    "cursor_position": 100,
                    "intent": intent,
                    "content": "def calculate_fibonacci(n):\n    if n <= 1:\n        return n\n    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)",
                    "language": "python"
                }
                
                print(f"📤 Testing intent: {intent}")
                await websocket.send(json.dumps(test_request))
                
                response = await websocket.recv()
                response_data = json.loads(response)
                
                success = response_data.get('status') == 'success'
                results[intent] = success
                
                if success:
                    print(f"   ✅ {intent} - Success (confidence: {response_data.get('confidence', 0):.2f})")
                else:
                    print(f"   ❌ {intent} - Failed: {response_data.get('message')}")
            
            successful_intents = sum(results.values())
            print(f"\n📊 Results: {successful_intents}/{len(intents)} intents successful")
            
            return successful_intents == len(intents)
            
    except Exception as e:
        print(f"❌ Multi-intent test error: {e}")
        return False

async def main():
    """Run WebSocket code completion tests"""
    
    print("🚀 Testing WebSocket Code Completion Integration")
    print("=" * 50)
    
    # Test basic code completion
    print("\n1. Testing Basic Code Completion")
    basic_success = await test_websocket_code_completion()
    
    if basic_success:
        print("\n2. Testing All Intents")
        multi_success = await test_multiple_intents()
    else:
        print("\n❌ Skipping multi-intent test due to basic test failure")
        multi_success = False
    
    print("\n" + "=" * 50)
    if basic_success and multi_success:
        print("🎉 All WebSocket code completion tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())