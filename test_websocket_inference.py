#!/usr/bin/env python3
"""
Test WebSocket connection to verify Phi-3 model inference
"""

import asyncio
import json
import websockets

async def test_websocket_inference():
    """Test WebSocket connection and inference"""
    print("🔌 Testing WebSocket Phi-3 Inference")
    print("=" * 50)
    
    try:
        # Connect to WebSocket
        uri = "ws://localhost:8000/ws/test_client"
        
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket")
            
            # Test code completion request
            request = {
                "type": "code_completion",
                "file_path": "test.py",
                "cursor_position": 0,
                "intent": "suggest",
                "content": "def fibonacci(n):",
                "language": "python"
            }
            
            print(f"📤 Sending request: {request['intent']} for {request['file_path']}")
            await websocket.send(json.dumps(request))
            
            # Wait for response
            print("⏳ Waiting for response...")
            response = await websocket.recv()
            response_data = json.loads(response)
            
            print(f"📥 Response received:")
            print(f"   Status: {response_data.get('status', 'unknown')}")
            print(f"   Type: {response_data.get('type', 'unknown')}")
            
            if response_data.get('status') == 'success':
                print(f"   Response: {response_data.get('response', '')[:200]}...")
                print(f"   Confidence: {response_data.get('confidence', 0)}")
                print(f"   Model: {response_data.get('model', 'unknown')}")
                print(f"   Using pretrained: {response_data.get('using_pretrained', False)}")
                
                if response_data.get('using_pretrained'):
                    print("🎉 SUCCESS: Real Phi-3 model weights are working!")
                    return True
                else:
                    print("⚠️  Using fallback weights, not real model")
                    return False
            else:
                print(f"❌ Error: {response_data.get('message', 'Unknown error')}")
                return False
                
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_websocket_inference())
    if success:
        print(f"\n✅ WEBSOCKET TEST PASSED - Real Phi-3 model inference working!")
    else:
        print(f"\n❌ WEBSOCKET TEST FAILED")