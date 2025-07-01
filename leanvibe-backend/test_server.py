#!/usr/bin/env python3
"""
Minimal test server for iOS code completion integration testing.
Provides mock responses to validate the iOS → WebSocket → Backend workflow.
"""

import json
import asyncio
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="LeanVibe Test Server", version="1.0.0")

# Enable CORS for all domains (for testing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active WebSocket connections
active_connections = []

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            # Receive message from iOS client
            data = await websocket.receive_text()
            print(f"📱 Received from iOS: {data}")
            
            try:
                message = json.loads(data)
                response = await handle_message(message)
                
                # Send response back to iOS
                await websocket.send_text(json.dumps(response))
                print(f"🚀 Sent to iOS: {json.dumps(response, indent=2)}")
                
            except json.JSONDecodeError:
                # Handle plain text messages
                response = {
                    "status": "success",
                    "message": f"Echo: {data}",
                    "type": "echo"
                }
                await websocket.send_text(json.dumps(response))
                
    except WebSocketDisconnect:
        print("📱 iOS client disconnected")
        active_connections.remove(websocket)

async def handle_message(message: dict) -> dict:
    """Handle different message types from iOS client."""
    
    message_type = message.get("type", "unknown")
    print(f"🔍 Message type: {message_type}")
    
    if message_type == "code_completion":
        return await handle_code_completion(message)
    elif message_type == "voice_command":
        return await handle_voice_command(message)
    else:
        # Default agent response
        return {
            "status": "success",
            "message": f"Received {message_type} message",
            "type": "agent_response",
            "timestamp": datetime.now().isoformat()
        }

async def handle_code_completion(message: dict) -> dict:
    """Handle code completion requests with realistic mock responses."""
    
    request = message.get("request", {})
    intent = request.get("intent", "suggest")
    content = request.get("content", "")
    language = request.get("language", "python")
    
    # Simulate processing delay
    await asyncio.sleep(0.5)
    
    # Generate realistic mock responses based on intent
    mock_responses = {
        "suggest": {
            "response": "Here are some suggestions to improve your code:\n\n1. Add type hints for better code clarity\n2. Consider using list comprehension for better performance\n3. Add error handling for edge cases\n4. Use descriptive variable names",
            "suggestions": [
                "Add type hints: def process_data(data: List[int]) -> List[int]",
                "Use list comprehension: return [item * 2 for item in data if item > 0]",
                "Add docstring to explain the function purpose"
            ]
        },
        "explain": {
            "response": "This code defines a function that processes a list of numbers:\n\n• `hello_world()` - A placeholder function that needs implementation\n• `calculate_sum(a, b)` - Adds two numbers together\n• `process_data(data)` - Filters positive numbers and doubles them\n\nThe code follows basic Python conventions but could benefit from type hints and documentation.",
            "suggestions": [
                "Add comprehensive docstrings",
                "Include input validation", 
                "Consider edge cases like empty lists"
            ]
        },
        "refactor": {
            "response": "Here's a refactored version of your code:\n\n```python\nfrom typing import List\n\ndef hello_world() -> str:\n    \"\"\"Return a greeting message.\"\"\"\n    return \"Hello, World!\"\n\ndef calculate_sum(a: float, b: float) -> float:\n    \"\"\"Calculate the sum of two numbers.\"\"\"\n    return a + b\n\ndef process_data(data: List[int]) -> List[int]:\n    \"\"\"Process data by filtering positive numbers and doubling them.\"\"\"\n    return [item * 2 for item in data if item > 0]\n```",
            "suggestions": [
                "Added type hints for better IDE support",
                "Implemented hello_world function",
                "Used list comprehension for efficiency",
                "Added docstrings for documentation"
            ]
        },
        "debug": {
            "response": "Code analysis complete. No syntax errors found, but here are potential issues:\n\n1. `hello_world()` function is incomplete (contains only pass)\n2. No input validation in `calculate_sum()` - could fail with non-numeric types\n3. `process_data()` doesn't handle None or empty input gracefully\n\nSuggested fixes:\n• Implement hello_world function body\n• Add type checking in calculate_sum\n• Add null/empty checks in process_data",
            "suggestions": [
                "Implement TODO in hello_world function",
                "Add try-catch for type errors",
                "Handle edge cases for empty/None inputs"
            ]
        },
        "optimize": {
            "response": "Performance optimization analysis:\n\n**Current Issues:**\n• Manual loop in process_data is slower than list comprehension\n• No early return for empty lists\n• Multiple list operations could be combined\n\n**Optimized version:**\n```python\ndef process_data(data: List[int]) -> List[int]:\n    if not data:  # Early return for empty lists\n        return []\n    return [item * 2 for item in data if item > 0]  # ~3x faster\n```\n\n**Performance gain:** ~70% faster for large datasets",
            "suggestions": [
                "Use list comprehension instead of manual loops",
                "Add early returns for edge cases",
                "Consider using numpy for very large datasets",
                "Profile code to identify real bottlenecks"
            ]
        }
    }
    
    mock_response = mock_responses.get(intent, mock_responses["suggest"])
    
    return {
        "status": "success",
        "intent": intent,
        "response": mock_response["response"],
        "confidence": 0.95,
        "requires_review": intent in ["refactor", "debug"],
        "suggestions": mock_response["suggestions"],
        "context_used": {
            "language": language,
            "symbols_found": 3,
            "has_context": True,
            "file_path": request.get("filePath", "test_file.py"),
            "has_symbol_context": True,
            "language_detected": language
        },
        "processing_time_ms": 500.0
    }

async def handle_voice_command(message: dict) -> dict:
    """Handle voice command messages."""
    
    command = message.get("command", "")
    original_text = message.get("originalText", "")
    
    return {
        "status": "success",
        "message": f"Voice command received: {original_text}",
        "command": command,
        "type": "voice_response",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting LeanVibe Test Server...")
    print("📱 iOS WebSocket endpoint: ws://localhost:8001/ws")
    print("🔍 Health check: http://localhost:8001/health")
    uvicorn.run(app, host="0.0.0.0", port=8001)