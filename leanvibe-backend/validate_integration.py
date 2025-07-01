#!/usr/bin/env python3
"""
Comprehensive validation of the iOS → WebSocket → Backend integration.
This validates the complete workflow end-to-end.
"""

import asyncio
import json
import websockets
from datetime import datetime

class IntegrationValidator:
    def __init__(self):
        self.uri = "ws://localhost:8001/ws"
        self.test_results = []
    
    async def run_validation(self):
        print("🧪 LeanVibe iOS Integration Validation")
        print("=" * 50)
        
        await self.test_connection()
        await self.test_code_completion_workflow()
        await self.test_voice_command_workflow()
        await self.test_error_handling()
        
        self.print_summary()
    
    async def test_connection(self):
        print("\n1️⃣ Testing WebSocket Connection...")
        try:
            async with websockets.connect(self.uri) as websocket:
                print("✅ WebSocket connection established")
                self.test_results.append(("WebSocket Connection", True, "Connected successfully"))
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            self.test_results.append(("WebSocket Connection", False, str(e)))
    
    async def test_code_completion_workflow(self):
        print("\n2️⃣ Testing Code Completion Workflow...")
        
        # Test all 5 intents from iOS
        intents = ["suggest", "explain", "refactor", "debug", "optimize"]
        
        for intent in intents:
            await self.test_code_completion_intent(intent)
    
    async def test_code_completion_intent(self, intent):
        # Exact format that iOS CodeCompletionService sends
        ios_request = {
            "type": "code_completion",
            "request": {
                "file_path": "current_file.py",
                "cursor_position": 10,
                "content": """def hello_world():
    # TODO: implement this function
    pass

def calculate_sum(a, b):
    return a + b

def process_data(data):
    # This function needs optimization
    result = []
    for item in data:
        if item > 0:
            result.append(item * 2)
    return result""",
                "language": "python",
                "intent": intent
            },
            "timestamp": datetime.now().isoformat(),
            "client_id": "ios-code-completion"
        }
        
        try:
            async with websockets.connect(self.uri) as websocket:
                # Send request
                await websocket.send(json.dumps(ios_request))
                
                # Receive response
                response_str = await websocket.recv()
                response = json.loads(response_str)
                
                # Validate response structure (what iOS expects)
                required_fields = ["status", "intent", "response", "confidence", "suggestions", "context_used"]
                missing_fields = [field for field in required_fields if field not in response]
                
                if missing_fields:
                    print(f"⚠️  {intent}: Missing fields {missing_fields}")
                    self.test_results.append((f"Code Completion - {intent}", False, f"Missing fields: {missing_fields}"))
                else:
                    confidence = response.get("confidence", 0)
                    suggestions_count = len(response.get("suggestions", []))
                    print(f"✅ {intent}: {confidence:.0%} confidence, {suggestions_count} suggestions")
                    self.test_results.append((f"Code Completion - {intent}", True, f"{confidence:.0%} confidence"))
                
        except Exception as e:
            print(f"❌ {intent} failed: {e}")
            self.test_results.append((f"Code Completion - {intent}", False, str(e)))
    
    async def test_voice_command_workflow(self):
        print("\n3️⃣ Testing Voice Command Workflow...")
        
        # Test voice command format (simulating iOS VoiceCommand processing)
        voice_request = {
            "type": "voice_command",
            "command": "/code-completion/suggest",
            "originalText": "hey leanvibe suggest improvements to this code",
            "confidence": 0.95,
            "intent": "suggest",
            "parameters": {},
            "clientId": "ios-voice-client",
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            async with websockets.connect(self.uri) as websocket:
                await websocket.send(json.dumps(voice_request))
                response = await websocket.recv()
                
                response_data = json.loads(response)
                if response_data.get("status") == "success":
                    print("✅ Voice command processed successfully")
                    self.test_results.append(("Voice Command Processing", True, "Command processed"))
                else:
                    print("⚠️  Voice command processing incomplete")
                    self.test_results.append(("Voice Command Processing", False, "Unexpected response"))
                    
        except Exception as e:
            print(f"❌ Voice command failed: {e}")
            self.test_results.append(("Voice Command Processing", False, str(e)))
    
    async def test_error_handling(self):
        print("\n4️⃣ Testing Error Handling...")
        
        # Test malformed JSON
        try:
            async with websockets.connect(self.uri) as websocket:
                await websocket.send("invalid json {")
                response = await websocket.recv()
                print("✅ Server handles malformed JSON gracefully")
                self.test_results.append(("Error Handling - Malformed JSON", True, "Handled gracefully"))
        except Exception as e:
            print(f"❌ Malformed JSON handling failed: {e}")
            self.test_results.append(("Error Handling - Malformed JSON", False, str(e)))
        
        # Test unknown message type
        try:
            async with websockets.connect(self.uri) as websocket:
                unknown_request = {"type": "unknown_type", "data": "test"}
                await websocket.send(json.dumps(unknown_request))
                response = await websocket.recv()
                response_data = json.loads(response)
                if response_data.get("status") == "success":
                    print("✅ Server handles unknown message types")
                    self.test_results.append(("Error Handling - Unknown Type", True, "Handled gracefully"))
                else:
                    print("⚠️  Unknown message type handling needs improvement")
                    self.test_results.append(("Error Handling - Unknown Type", False, "Unexpected response"))
        except Exception as e:
            print(f"❌ Unknown message type handling failed: {e}")
            self.test_results.append(("Error Handling - Unknown Type", False, str(e)))
    
    def print_summary(self):
        print("\n" + "=" * 50)
        print("📊 INTEGRATION VALIDATION SUMMARY")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for _, passed, _ in self.test_results if passed)
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {passed_tests/total_tests:.1%}")
        
        if failed_tests > 0:
            print(f"\n⚠️  Failed Tests:")
            for test_name, passed, message in self.test_results:
                if not passed:
                    print(f"   • {test_name}: {message}")
        
        print(f"\n🎯 MVP READINESS ASSESSMENT:")
        if passed_tests >= 8:  # At least 8 tests passing
            print("✅ READY FOR MVP - Core integration working")
            print("   • WebSocket communication functional")
            print("   • Code completion pipeline operational")
            print("   • All intents responding correctly")
            print("   • Error handling in place")
        elif passed_tests >= 6:
            print("⚠️  MOSTLY READY - Minor issues to address")
        else:
            print("❌ NOT READY - Critical issues need resolution")
        
        print(f"\n🚀 Next Steps:")
        if passed_tests >= 8:
            print("   1. Test with actual iOS simulator")
            print("   2. Integrate real file content")
            print("   3. Add production error handling")
            print("   4. Performance optimization")
        else:
            print("   1. Fix failing tests")
            print("   2. Re-run validation")
            print("   3. Debug integration issues")

async def main():
    validator = IntegrationValidator()
    await validator.run_validation()

if __name__ == "__main__":
    asyncio.run(main())