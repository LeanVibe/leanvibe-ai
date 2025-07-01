#!/usr/bin/env python3
"""
Test client that exactly mimics the iOS CodeCompletionService message format.
"""

import asyncio
import json
import websockets

async def test_ios_message_format():
    uri = "ws://localhost:8001/ws"
    
    # Exact message format from iOS CodeCompletionService
    ios_message = {
        "type": "code_completion",
        "request": {
            "file_path": "current_file.py",
            "cursor_position": 10,
            "content": """def hello_world():
    # TODO: implement this function
    pass

def calculate_sum(a, b):
    return a + b""",
            "language": "python",
            "intent": "suggest"
        },
        "timestamp": "2025-01-07T16:42:00.000Z",
        "client_id": "ios-code-completion"
    }
    
    try:
        async with websockets.connect(uri) as websocket:
            print("🔗 Connected to WebSocket (iOS format test)")
            
            # Send iOS-formatted message
            message_str = json.dumps(ios_message)
            print(f"📤 Sending iOS message: {message_str}")
            await websocket.send(message_str)
            
            # Receive response
            response = await websocket.recv()
            print(f"📥 Raw response: {response}")
            
            # Parse and validate response format
            try:
                response_data = json.loads(response)
                print("✅ Response parsed successfully")
                
                # Validate response fields expected by iOS
                required_fields = ["status", "intent", "response", "confidence", "suggestions"]
                missing_fields = [field for field in required_fields if field not in response_data]
                
                if missing_fields:
                    print(f"⚠️  Missing fields: {missing_fields}")
                else:
                    print("✅ All required fields present")
                
                print(f"📊 Response summary:")
                print(f"   Status: {response_data.get('status')}")
                print(f"   Intent: {response_data.get('intent')}")
                print(f"   Confidence: {response_data.get('confidence')}")
                print(f"   Suggestions: {len(response_data.get('suggestions', []))}")
                print(f"   Response length: {len(response_data.get('response', ''))}")
                
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse response as JSON: {e}")
                
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    print("🧪 Testing iOS message format compatibility...")
    asyncio.run(test_ios_message_format())