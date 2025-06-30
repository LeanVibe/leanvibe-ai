#!/usr/bin/env python3
"""
Simple test runner that works without pytest installation
Useful for quick validation during setup
"""

import asyncio
import time
import sys
import os

# Add leanvibe-backend to path for module discovery
sys.path.insert(0, os.path.dirname(__file__))

async def test_ai_service():
    """Test AI service initialization and basic commands"""
    print("🧠 Testing AI Service...")
    
    try:
        from app.services.ai_service import AIService
        
        # Test initialization
        ai_service = AIService()
        await ai_service.initialize()
        
        if not ai_service.is_initialized:
            print("❌ AI service failed to initialize")
            return False
        
        print("✅ AI service initialized successfully")
        
        # Test basic commands
        test_commands = [
            {"type": "command", "content": "/status"},
            {"type": "command", "content": "/help"},
            {"type": "command", "content": "/current-dir"},
            {"type": "message", "content": "Hello agent"}
        ]
        
        for cmd in test_commands:
            start_time = time.time()
            response = await ai_service.process_command(cmd)
            response_time = time.time() - start_time
            
            if response["status"] != "success" and cmd["content"] != "Hello agent":
                print(f"❌ Command failed: {cmd['content']} - {response.get('message', 'Unknown error')}")
                return False
            
            if response_time > 2.0:
                print(f"⚠️  Slow response for {cmd['content']}: {response_time:.2f}s")
            else:
                print(f"✅ {cmd['content']} responded in {response_time:.3f}s")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure you're in the backend directory and dependencies are installed")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_connection_manager():
    """Test connection manager"""
    print("\n🔌 Testing Connection Manager...")
    
    try:
        from app.core.connection_manager import ConnectionManager
        
        manager = ConnectionManager()
        
        # Test basic functionality
        info = manager.get_connection_info()
        if info["total_connections"] != 0:
            print("❌ Connection manager should start with 0 connections")
            return False
        
        print("✅ Connection manager initialized correctly")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_models():
    """Test data models"""
    print("\n📊 Testing Data Models...")
    
    try:
        from app.models.messages import WebSocketMessage, AgentResponse
        
        # Test WebSocketMessage
        msg = WebSocketMessage(type="command", content="/status")
        if msg.type != "command" or msg.content != "/status":
            print("❌ WebSocketMessage validation failed")
            return False
        
        # Test AgentResponse
        response = AgentResponse(status="success", message="Test message")
        if response.status != "success" or response.message != "Test message":
            print("❌ AgentResponse validation failed")
            return False
        
        print("✅ Data models work correctly")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

async def test_full_flow():
    """Test complete request-response flow"""
    print("\n🔄 Testing Full Request-Response Flow...")
    
    try:
        from app.services.ai_service import AIService
        
        ai_service = AIService()
        await ai_service.initialize()
        
        # Simulate iOS app requests
        ios_requests = [
            {"type": "command", "content": "/status", "client_id": "ios-test"},
            {"type": "command", "content": "/list-files", "client_id": "ios-test"},
            {"type": "message", "content": "What files are in this directory?", "client_id": "ios-test"}
        ]
        
        for request in ios_requests:
            start_time = time.time()
            response = await ai_service.process_command(request)
            response_time = time.time() - start_time
            
            # Validate response structure
            required_fields = ["status", "message"]
            for field in required_fields:
                if field not in response:
                    print(f"❌ Missing field '{field}' in response")
                    return False
            
            # Check performance
            if response_time > 2.0:
                print(f"⚠️  Performance warning: {request['content']} took {response_time:.2f}s")
            
            print(f"✅ {request['content']} -> {response['status']} ({response_time:.3f}s)")
        
        return True
        
    except Exception as e:
        print(f"❌ Full flow test failed: {e}")
        return False

def print_environment_info():
    """Print environment information"""
    print("🔍 Environment Information:")
    print(f"   Python: {sys.version}")
    print(f"   Platform: {sys.platform}")
    print(f"   Working Directory: {os.getcwd()}")
    print(f"   Python Path: {sys.path[0]}")
    
    # Check for uv
    import subprocess
    try:
        result = subprocess.run(['uv', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   UV: {result.stdout.strip()}")
        else:
            print("   UV: Not installed")
    except FileNotFoundError:
        print("   UV: Not installed")
    
    # Check for key dependencies
    try:
        import fastapi
        print(f"   FastAPI: {fastapi.__version__}")
    except ImportError:
        print("   FastAPI: Not installed (run 'uv sync')")
    
    try:
        import uvicorn
        print(f"   Uvicorn: {uvicorn.__version__}")
    except ImportError:
        print("   Uvicorn: Not installed (run 'uv sync')")
    
    try:
        import websockets
        print(f"   WebSockets: {websockets.__version__}")
    except ImportError:
        print("   WebSockets: Not installed (run 'uv sync')")

async def main():
    """Run all tests"""
    print("🧪 LeanVibe Backend Test Suite")
    print("=" * 40)
    
    print_environment_info()
    print()
    
    tests = [
        test_models(),
        test_connection_manager(),
        await test_ai_service(),
        await test_full_flow()
    ]
    
    passed = sum(tests)
    total = len(tests)
    
    print(f"\n📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! Your backend is ready.")
        print("\nNext steps:")
        print("1. Start the server: ./start.sh")
        print("2. Test with iOS app")
        print("3. Run integration tests: python tests/test_integration.py")
    else:
        print("❌ Some tests failed. Check the output above for details.")
        print("\nTroubleshooting:")
        print("1. Ensure you're in the backend directory")
        print("2. Install dependencies: uv sync")
        print("3. Check Python version: python --version (should be 3.11+)")
        print("4. Install uv if missing: curl -LsSf https://astral.sh/uv/install.sh | sh")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)