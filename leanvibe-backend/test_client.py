#!/usr/bin/env python3
"""
Test client to validate WebSocket connection and code completion workflow.
Simulates iOS client behavior.
"""

import asyncio
import json
import websockets

async def test_code_completion():
    uri = "ws://localhost:8001/ws"
    
    # Test code completion request (simulating iOS)
    test_request = {
        "type": "code_completion",
        "request": {
            "file_path": "test_file.py",
            "cursor_position": 10,
            "content": """
def hello_world():
    # TODO: implement this function
    pass

def calculate_sum(a, b):
    return a + b
""",
            "language": "python",
            "intent": "suggest"
        },
        "timestamp": "2025-01-07T16:41:00.000Z",
        "client_id": "test-client"
    }
    
    try:
        async with websockets.connect(uri) as websocket:
            print("🔗 Connected to WebSocket server")
            
            # Send code completion request
            print("📤 Sending code completion request...")
            await websocket.send(json.dumps(test_request))
            
            # Receive response
            response = await websocket.recv()
            print("📥 Received response:")
            print(json.dumps(json.loads(response), indent=2))
            
    except Exception as e:
        print(f"❌ Error: {e}")

async def test_all_intents():
    """Test all code completion intents"""
    intents = ["suggest", "explain", "refactor", "debug", "optimize"]
    
    for intent in intents:
        print(f"\n🧪 Testing intent: {intent}")
        await test_intent(intent)

async def test_intent(intent):
    uri = "ws://localhost:8001/ws"
    
    test_request = {
        "type": "code_completion", 
        "request": {
            "file_path": "test_file.py",
            "cursor_position": 10,
            "content": "def hello_world():\n    pass",
            "language": "python",
            "intent": intent
        },
        "client_id": "test-client"
    }
    
    try:
        async with websockets.connect(uri) as websocket:
            await websocket.send(json.dumps(test_request))
            response = await websocket.recv()
            data = json.loads(response)
            print(f"✅ {intent}: {data.get('confidence', 0):.0%} confidence")
            print(f"   Response: {data.get('response', '')[:60]}...")
            
    except Exception as e:
        print(f"❌ {intent} failed: {e}")

if __name__ == "__main__":
    print("🧪 Testing WebSocket Code Completion...")
    asyncio.run(test_all_intents())