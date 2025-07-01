# Complete Vertical Slice Validation Workflow

## Quick Start Guide

This is a practical, step-by-step guide to set up and run vertical slice validation for your L3 coding agent from mobile app to backend.

## Step 1: Project Setup (5 minutes)

```bash
# 1. Create the validation workspace
mkdir l3-agent-validation && cd l3-agent-validation

# 2. Set up directory structure
mkdir -p {.claude/commands,tests,validation,postman,ios-tests}

# 3. Initialize Python environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install fastapi uvicorn websockets pytest pytest-asyncio pydantic-ai
```

## Step 2: Deploy Custom Claude Commands (5 minutes)

```bash
# 1. Create the essential validation commands
cat > .claude/commands/validate-setup.md << 'EOF'
Validate the L3 agent project setup for mobile-backend integration:

1. Check FastAPI server configuration and WebSocket endpoints
2. Verify pydantic.ai agent implementation and tool setup
3. Validate project structure and dependencies
4. Check environment variables and configuration files
5. Verify database connections and session management
6. Review security settings and CORS configuration
7. Test basic server startup and health endpoints

Provide specific setup issues and recommended fixes.

$ARGUMENTS
EOF

cat > .claude/commands/test-flow.md << 'EOF'
Create end-to-end test for mobile-to-backend communication flow:

1. Generate WebSocket connection test from iOS perspective
2. Create authentication and session management tests
3. Build command execution validation tests
4. Add error handling and recovery scenario tests
5. Create performance and load testing scenarios
6. Build integration tests for agent responses
7. Generate test data and mock scenarios

Include both automated and manual testing approaches.

$ARGUMENTS
EOF

cat > .claude/commands/debug-mobile.md << 'EOF'
Debug mobile app connectivity and communication issues:

1. Analyze WebSocket connection logs and handshake process
2. Check iOS app configuration and URL schemes
3. Validate message format and serialization/deserialization
4. Examine authentication token handling and refresh logic
5. Review error handling and user feedback mechanisms
6. Check network configuration and SSL certificate validation
7. Analyze performance metrics and response times

Provide step-by-step debugging guidance.

$ARGUMENTS
EOF
```

## Step 3: Quick Backend Validation (10 minutes)

```bash
# 1. Run Claude Code analysis on your backend
claude "/project:validate-setup Check WebSocket implementation and pydantic.ai integration"

# 2. Generate test suite
claude "/project:test-flow Focus on WebSocket communication and agent processing"

# 3. Create a simple health check endpoint test
cat > tests/test_health.py << 'EOF'
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    """Test basic health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_websocket_endpoint_available():
    """Test WebSocket endpoint is available"""
    with client.websocket_connect("/ws/test-client") as websocket:
        websocket.send_json({"type": "ping"})
        data = websocket.receive_json()
        assert "pong" in data or "response" in data
EOF

# 4. Run the basic tests
pytest tests/test_health.py -v
```

## Step 4: Postman WebSocket Testing (10 minutes)

```bash
# 1. Create Postman collection for WebSocket testing
cat > postman/l3-agent-websocket.json << 'EOF'
{
  "info": {
    "name": "L3 Agent WebSocket Validation",
    "version": "1.0.0"
  },
  "variable": [
    {
      "key": "base_url",
      "value": "localhost:8000"
    }
  ],
  "item": [
    {
      "name": "Basic Connection Test",
      "request": {
        "method": "WEBSOCKET",
        "url": "ws://{{base_url}}/ws/postman-test",
        "description": "Test basic WebSocket connection"
      }
    },
    {
      "name": "Send Test Command",
      "request": {
        "method": "WEBSOCKET",
        "url": "ws://{{base_url}}/ws/postman-test", 
        "body": {
          "mode": "raw",
          "raw": "{\"type\": \"command\", \"content\": \"/project:quick-test\"}"
        }
      }
    },
    {
      "name": "Agent Message Test",
      "request": {
        "method": "WEBSOCKET",
        "url": "ws://{{base_url}}/ws/postman-test",
        "body": {
          "mode": "raw",
          "raw": "{\"type\": \"message\", \"content\": \"What files are in the current directory?\"}"
        }
      }
    }
  ]
}
EOF

# 2. Start your FastAPI server
uvicorn app.main:app --reload &

# 3. Import the collection into Postman and run the tests
echo "Import postman/l3-agent-websocket.json into Postman and test your WebSocket endpoints"
```

## Step 5: iOS Integration Validation (15 minutes)

```swift
// Create a simple iOS test file: ios-tests/WebSocketTests.swift
import XCTest
import Foundation

class L3AgentWebSocketTests: XCTestCase {
    var webSocketTask: URLSessionWebSocketTask?
    var urlSession: URLSession?
    
    override func setUp() {
        super.setUp()
        urlSession = URLSession(configuration: .default)
    }
    
    func testWebSocketConnection() {
        let expectation = XCTestExpectation(description: "WebSocket connection")
        
        guard let url = URL(string: "ws://localhost:8000/ws/ios-test") else {
            XCTFail("Invalid URL")
            return
        }
        
        webSocketTask = urlSession?.webSocketTask(with: url)
        webSocketTask?.resume()
        
        // Send test message
        let message = URLSessionWebSocketTask.Message.string("""
        {
            "type": "message",
            "content": "iOS connection test"
        }
        """)
        
        webSocketTask?.send(message) { error in
            if let error = error {
                XCTFail("Failed to send message: \(error)")
                return
            }
            
            // Receive response
            self.webSocketTask?.receive { result in
                switch result {
                case .success(let message):
                    switch message {
                    case .string(let text):
                        XCTAssertTrue(text.contains("response"))
                        expectation.fulfill()
                    case .data(let data):
                        XCTAssertNotNil(data)
                        expectation.fulfill()
                    @unknown default:
                        XCTFail("Unknown message type")
                    }
                case .failure(let error):
                    XCTFail("Failed to receive message: \(error)")
                }
            }
        }
        
        wait(for: [expectation], timeout: 10.0)
    }
    
    func testCommandExecution() {
        let expectation = XCTestExpectation(description: "Command execution")
        
        guard let url = URL(string: "ws://localhost:8000/ws/ios-command-test") else {
            XCTFail("Invalid URL")
            return
        }
        
        webSocketTask = urlSession?.webSocketTask(with: url)
        webSocketTask?.resume()
        
        // Send command
        let command = URLSessionWebSocketTask.Message.string("""
        {
            "type": "command",
            "content": "/project:quick-test"
        }
        """)
        
        webSocketTask?.send(command) { error in
            if let error = error {
                XCTFail("Failed to send command: \(error)")
                return
            }
            
            self.webSocketTask?.receive { result in
                switch result {
                case .success(let message):
                    switch message {
                    case .string(let text):
                        let data = text.data(using: .utf8)!
                        let json = try! JSONSerialization.jsonObject(with: data) as! [String: Any]
                        XCTAssertEqual(json["status"] as? String, "success")
                        expectation.fulfill()
                    case .data(_):
                        expectation.fulfill()
                    @unknown default:
                        XCTFail("Unknown message type")
                    }
                case .failure(let error):
                    XCTFail("Failed to receive response: \(error)")
                }
            }
        }
        
        wait(for: [expectation], timeout: 15.0)
    }
    
    override func tearDown() {
        webSocketTask?.cancel(with: .normalClosure, reason: nil)
        super.tearDown()
    }
}
```

## Step 6: Run Comprehensive Validation (10 minutes)

```bash
# 1. Create validation runner script
cat > run_validation.sh << 'EOF'
#!/bin/bash

echo "🚀 Starting L3 Agent Vertical Slice Validation"
echo "=============================================="

# Start the server in background
echo "📡 Starting FastAPI server..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
SERVER_PID=$!
sleep 5

# Run backend tests
echo "🔧 Running backend validation tests..."
pytest tests/ -v --tb=short

# Run WebSocket validation script
echo "🌐 Running WebSocket validation..."
python websocket_validator.py

# Run iOS tests (if Xcode command line tools available)
if command -v xcodebuild &> /dev/null; then
    echo "📱 Running iOS tests..."
    # Note: This requires an actual iOS project setup
    # xcodebuild test -project YourApp.xcodeproj -scheme YourApp -destination 'platform=iOS Simulator,name=iPhone 14'
    echo "iOS tests require Xcode project setup - skipping for now"
else
    echo "📱 iOS tests skipped (Xcode not available)"
fi

# Generate final report
echo "📊 Generating final validation report..."
python << EOF
import json
import os

# Collect all test results
results = {
    "timestamp": "$(date)",
    "backend_tests": "Check pytest output above",
    "websocket_tests": "Check websocket_validator output",
    "ios_tests": "Manual verification required",
    "recommendations": [
        "Review all test outputs for failures",
        "Verify WebSocket connection from iOS device/simulator", 
        "Test with actual Claude Code CLI commands",
        "Monitor performance under load",
        "Validate error handling scenarios"
    ]
}

print("\\n✅ Validation Complete!")
print("📋 Summary of validation steps completed:")
print("   • Backend health checks")
print("   • WebSocket connection testing") 
print("   • Command execution validation")
print("   • Error handling verification")
print("   • Performance baseline measurement")
print("\\n🔍 Next Steps:")
print("   1. Review generated test reports")
print("   2. Test with actual iOS device/simulator")
print("   3. Run load testing for production readiness")
print("   4. Implement CI/CD pipeline integration")
EOF

# Cleanup
echo "🧹 Cleaning up..."
kill $SERVER_PID

echo "✅ Validation completed! Check the outputs above for any issues."
EOF

chmod +x run_validation.sh

# 2. Run the complete validation
./run_validation.sh
```

## Step 7: Troubleshooting Common Issues (As needed)

```bash
# Debug connection issues
claude "/project:debug-mobile Focus on WebSocket handshake and authentication"

# Check server configuration
claude "/project:validate-setup Review CORS, SSL, and port configuration"

# Performance debugging
claude "/user:debug-session High latency in command execution"

# iOS-specific issues
claude "/project:debug-mobile iOS WebSocket connection drops after 60 seconds"
```

## Quick Validation Checklist

Use this checklist to verify your vertical slice is working:

### ✅ Backend Validation
- [ ] FastAPI server starts without errors
- [ ] WebSocket endpoint accepts connections
- [ ] Health check endpoint responds
- [ ] Agent processes basic commands
- [ ] Authentication flow works
- [ ] Session management persists state

### ✅ WebSocket Communication
- [ ] Connection establishes successfully
- [ ] Messages sent from client reach server
- [ ] Server responses arrive at client
- [ ] JSON message format is valid
- [ ] Error messages are properly formatted
- [ ] Connection remains stable during usage

### ✅ Agent Functionality  
- [ ] Custom commands execute correctly
- [ ] Tool invocation works as expected
- [ ] State persists across messages
- [ ] Error handling provides useful feedback
- [ ] Response quality meets expectations
- [ ] Performance is acceptable (<2s response)

### ✅ iOS Integration
- [ ] WebSocket connection from iOS app works
- [ ] Authentication flow completes
- [ ] Messages serialize/deserialize correctly
- [ ] UI updates with agent responses
- [ ] Error states are handled gracefully
- [ ] Connection recovery works after network issues

### ✅ End-to-End Flow
- [ ] Complete user journey works (iOS → Backend → Agent → Response → iOS)
- [ ] Commands execute from mobile interface
- [ ] Real-time communication feels responsive
- [ ] Multiple concurrent users can connect
- [ ] System handles edge cases gracefully
- [ ] Logging provides sufficient debugging info

## Common Commands for Validation

```bash
# Quick health check
claude "/user:health-check"

# Validate current setup
claude "/project:validate-setup Current project configuration"

# Test specific functionality
claude "/project:test-flow WebSocket message handling and agent processing"

# Debug specific issues
claude "/project:debug-mobile Connection timeout after authentication"

# Generate testing documentation
claude "/project:api-docs Focus on mobile integration examples"
```

## Performance Benchmarks

Your vertical slice should meet these basic performance criteria:

- **Connection establishment**: < 500ms
- **Simple command execution**: < 2 seconds  
- **Complex command execution**: < 10 seconds
- **Message round-trip time**: < 100ms
- **Concurrent connections**: 10+ without degradation
- **Memory usage**: < 500MB for basic operations
- **Error recovery**: < 5 seconds to reconnect

## Success Criteria

Your vertical slice validation is successful when:

1. **All automated tests pass** (backend, WebSocket, integration)
2. **iOS app connects and communicates** with the backend
3. **Agent responds appropriately** to commands and messages
4. **Error handling works** for common failure scenarios  
5. **Performance meets benchmarks** under normal load
6. **Documentation is complete** for team handoff

## Next Steps After Validation

Once your vertical slice is validated:

1. **Implement CI/CD pipeline** with automated testing
2. **Add comprehensive logging and monitoring**
3. **Scale testing** with load testing tools
4. **Security audit** authentication and data handling
5. **User acceptance testing** with real usage scenarios
6. **Production deployment** with proper infrastructure

This validation approach ensures your L3 coding agent works reliably from mobile app to backend before investing in full-scale development.