# Vertical Slice Validation Setup Guide

## Overview
This guide provides step-by-step instructions for setting up a comprehensive vertical slice validation system for your L3 coding agent that validates the complete interaction flow from iOS mobile app to FastAPI backend.

## Prerequisites
- MacBook M3 Max with 48GB RAM (as specified)
- Python 3.9+ with FastAPI and pydantic.ai setup
- iOS development environment with Xcode
- Postman (latest version with WebSocket support)
- Claude Code CLI installed and configured

## Phase 1: Backend Validation Setup

### Step 1: Create Backend Test Structure
```bash
# Create testing directory structure
mkdir -p tests/unit tests/integration tests/performance
mkdir -p tests/websocket tests/agent tests/tools

# Create test configuration files
touch tests/conftest.py
touch tests/test_config.py
```

### Step 2: WebSocket Connection Testing
```python
# tests/websocket/test_connection.py
import pytest
import asyncio
from fastapi.testclient import TestClient
from websockets.exceptions import ConnectionClosed
import json

class TestWebSocketConnection:
    """Test WebSocket connection establishment and basic communication"""
    
    def test_websocket_connection_establishment(self):
        """Test basic WebSocket connection"""
        client = TestClient(app)
        with client.websocket_connect("/ws/test-client") as websocket:
            # Test connection is established
            assert websocket is not None
            
    def test_websocket_authentication(self):
        """Test WebSocket connection with authentication"""
        client = TestClient(app)
        headers = {"Authorization": "Bearer test-token"}
        with client.websocket_connect("/ws/test-client", headers=headers) as websocket:
            # Send authentication test message
            test_message = {"type": "auth", "token": "test-token"}
            websocket.send_json(test_message)
            response = websocket.receive_json()
            assert response["status"] == "authenticated"
            
    def test_websocket_message_format(self):
        """Test message format validation"""
        client = TestClient(app)
        with client.websocket_connect("/ws/test-client") as websocket:
            # Test valid message format
            valid_message = {
                "type": "message", 
                "content": "test command",
                "timestamp": "2025-06-21T11:45:00Z"
            }
            websocket.send_json(valid_message)
            response = websocket.receive_json()
            assert "response" in response
            
    def test_websocket_error_handling(self):
        """Test WebSocket error handling"""
        client = TestClient(app)
        with client.websocket_connect("/ws/test-client") as websocket:
            # Send invalid message format
            invalid_message = {"invalid": "format"}
            websocket.send_json(invalid_message)
            response = websocket.receive_json()
            assert response["status"] == "error"
            assert "error" in response
```

### Step 3: Agent Processing Validation
```python
# tests/agent/test_agent_processing.py
import pytest
from app.agent.core import process_request
from app.agent.commands import CommandRegistry

class TestAgentProcessing:
    """Test L3 agent processing capabilities"""
    
    @pytest.fixture
    def sample_session_data(self):
        return {
            "workspace_path": "/tmp/test-workspace",
            "user_preferences": {},
            "command_history": []
        }
    
    def test_basic_command_processing(self, sample_session_data):
        """Test basic command processing"""
        response = await process_request(
            client_id="test-client",
            message="list files in current directory",
            session_data=sample_session_data
        )
        assert response["status"] == "success"
        assert "response" in response
        
    def test_custom_command_execution(self, sample_session_data):
        """Test custom slash command execution"""
        response = await process_request(
            client_id="test-client", 
            message="/project:analyze-backend Focus on WebSocket implementation",
            session_data=sample_session_data
        )
        assert response["status"] == "success"
        assert len(response["actions"]) > 0
        
    def test_agent_state_persistence(self, sample_session_data):
        """Test agent state management"""
        # First request
        response1 = await process_request(
            client_id="test-client",
            message="set workspace to /tmp/test",
            session_data=sample_session_data
        )
        
        # Second request should maintain state
        response2 = await process_request(
            client_id="test-client",
            message="what is my current workspace?",
            session_data=sample_session_data
        )
        
        assert "/tmp/test" in response2["response"]
```

## Phase 2: iOS Client Validation

### Step 4: iOS WebSocket Client Testing
```swift
// Tests/AgentClientTests.swift
import XCTest
import Network
@testable import YourApp

class AgentClientTests: XCTestCase {
    var agentClient: AgentClient!
    var expectation: XCTestExpectation!
    
    override func setUp() {
        super.setUp()
        agentClient = AgentClient(serverURL: "ws://localhost:8000")
        expectation = XCTestExpectation(description: "WebSocket response")
    }
    
    func testWebSocketConnection() {
        // Test connection establishment
        agentClient.connect(
            onMessage: { data in
                XCTAssertNotNil(data)
                self.expectation.fulfill()
            },
            onError: { error in
                XCTFail("Connection failed: \(error)")
            }
        )
        
        wait(for: [expectation], timeout: 5.0)
    }
    
    func testMessageSending() {
        // Test message sending and response
        expectation = XCTestExpectation(description: "Message response")
        
        agentClient.connect(
            onMessage: { data in
                if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                   let response = json["response"] as? String {
                    XCTAssertFalse(response.isEmpty)
                    self.expectation.fulfill()
                }
            },
            onError: { error in
                XCTFail("Message sending failed: \(error)")
            }
        )
        
        // Send test message
        agentClient.sendMessage(content: "Hello agent", type: "message")
        wait(for: [expectation], timeout: 10.0)
    }
    
    func testCommandExecution() {
        // Test custom command execution
        expectation = XCTestExpectation(description: "Command response")
        
        agentClient.connect(
            onMessage: { data in
                if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                   let command = json["command"] as? String {
                    XCTAssertEqual(command, "project:quick-test")
                    self.expectation.fulfill()
                }
            },
            onError: { error in
                XCTFail("Command execution failed: \(error)")
            }
        )
        
        agentClient.sendCommand(command: "/project:quick-test")
        wait(for: [expectation], timeout: 15.0)
    }
}
```

## Phase 3: Postman Collection Setup

### Step 5: Create Postman WebSocket Collection
```json
{
  "info": {
    "name": "L3 Agent WebSocket API",
    "description": "Comprehensive WebSocket testing for L3 coding agent",
    "version": "1.0.0"
  },
  "variable": [
    {
      "key": "base_url",
      "value": "ws://localhost:8000"
    },
    {
      "key": "client_id", 
      "value": "postman-test-client"
    }
  ],
  "item": [
    {
      "name": "Connection Tests",
      "item": [
        {
          "name": "Basic Connection",
          "request": {
            "method": "WEBSOCKET",
            "url": "{{base_url}}/ws/{{client_id}}",
            "description": "Test basic WebSocket connection"
          }
        },
        {
          "name": "Authenticated Connection",
          "request": {
            "method": "WEBSOCKET", 
            "url": "{{base_url}}/ws/{{client_id}}",
            "header": [
              {
                "key": "Authorization",
                "value": "Bearer test-token"
              }
            ]
          }
        }
      ]
    },
    {
      "name": "Message Tests",
      "item": [
        {
          "name": "Send Basic Message",
          "request": {
            "method": "WEBSOCKET",
            "url": "{{base_url}}/ws/{{client_id}}",
            "body": {
              "mode": "raw",
              "raw": "{\"type\": \"message\", \"content\": \"Hello agent\"}"
            }
          }
        },
        {
          "name": "Send Custom Command",
          "request": {
            "method": "WEBSOCKET",
            "url": "{{base_url}}/ws/{{client_id}}",
            "body": {
              "mode": "raw", 
              "raw": "{\"type\": \"command\", \"content\": \"/project:quick-test\"}"
            }
          }
        }
      ]
    }
  ]
}
```

## Phase 4: End-to-End Validation

### Step 6: Create Validation Script
```python
# validation/e2e_test.py
import asyncio
import json
import websockets
from concurrent.futures import ThreadPoolExecutor
import time

class E2EValidator:
    """End-to-end validation for mobile-to-backend flow"""
    
    def __init__(self, websocket_url="ws://localhost:8000"):
        self.websocket_url = websocket_url
        self.test_results = {}
        
    async def test_connection_flow(self):
        """Test complete connection flow"""
        try:
            async with websockets.connect(f"{self.websocket_url}/ws/e2e-test") as websocket:
                # Test 1: Connection establishment
                start_time = time.time()
                await websocket.send(json.dumps({
                    "type": "message",
                    "content": "connection test"
                }))
                response = await websocket.recv()
                connection_time = time.time() - start_time
                
                self.test_results["connection"] = {
                    "success": True,
                    "response_time": connection_time,
                    "response": json.loads(response)
                }
                
                return True
        except Exception as e:
            self.test_results["connection"] = {
                "success": False,
                "error": str(e)
            }
            return False
    
    async def test_command_execution(self):
        """Test command execution flow"""
        commands_to_test = [
            "/project:quick-test",
            "/project:analyze-backend check WebSocket implementation", 
            "/user:health-check"
        ]
        
        for command in commands_to_test:
            try:
                async with websockets.connect(f"{self.websocket_url}/ws/e2e-test") as websocket:
                    start_time = time.time()
                    await websocket.send(json.dumps({
                        "type": "command",
                        "content": command
                    }))
                    response = await websocket.recv()
                    execution_time = time.time() - start_time
                    
                    self.test_results[f"command_{command}"] = {
                        "success": True,
                        "execution_time": execution_time,
                        "response": json.loads(response)
                    }
            except Exception as e:
                self.test_results[f"command_{command}"] = {
                    "success": False,
                    "error": str(e)
                }
    
    async def test_concurrent_connections(self, num_connections=5):
        """Test concurrent WebSocket connections"""
        async def single_connection_test(connection_id):
            try:
                async with websockets.connect(f"{self.websocket_url}/ws/concurrent-{connection_id}") as websocket:
                    await websocket.send(json.dumps({
                        "type": "message",
                        "content": f"concurrent test {connection_id}"
                    }))
                    response = await websocket.recv()
                    return {"success": True, "response": json.loads(response)}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        tasks = [single_connection_test(i) for i in range(num_connections)]
        results = await asyncio.gather(*tasks)
        
        successful_connections = sum(1 for r in results if r["success"])
        self.test_results["concurrent_connections"] = {
            "total_attempted": num_connections,
            "successful": successful_connections,
            "success_rate": successful_connections / num_connections,
            "details": results
        }
    
    def generate_report(self):
        """Generate comprehensive test report"""
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "summary": {
                "total_tests": len(self.test_results),
                "passed": sum(1 for r in self.test_results.values() if r.get("success", False)),
                "failed": sum(1 for r in self.test_results.values() if not r.get("success", True))
            },
            "details": self.test_results
        }
        
        return report

# Usage
async def run_validation():
    validator = E2EValidator()
    
    print("Starting E2E validation...")
    await validator.test_connection_flow()
    await validator.test_command_execution()
    await validator.test_concurrent_connections()
    
    report = validator.generate_report()
    
    print(f"Validation completed: {report['summary']['passed']}/{report['summary']['total_tests']} tests passed")
    
    with open("validation_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    return report

if __name__ == "__main__":
    asyncio.run(run_validation())
```

## Phase 5: CI/CD Integration

### Step 7: GitHub Actions Workflow
```yaml
# .github/workflows/vertical-slice-validation.yml
name: Vertical Slice Validation

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-asyncio
    - name: Run backend tests
      run: |
        pytest tests/ -v --tb=short
    - name: Start server for WebSocket tests
      run: |
        uvicorn app.main:app &
        sleep 5
    - name: Run E2E validation
      run: |
        python validation/e2e_test.py

  ios-tests:
    runs-on: macos-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Xcode
      uses: actions/setup-xcode@v1
      with:
        xcode-version: latest-stable
    - name: Run iOS tests
      run: |
        xcodebuild test -project YourApp.xcodeproj -scheme YourApp -destination 'platform=iOS Simulator,name=iPhone 14'

  postman-tests:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Install Newman
      run: npm install -g newman
    - name: Start server
      run: |
        uvicorn app.main:app &
        sleep 5
    - name: Run Postman tests
      run: |
        newman run postman/L3-Agent-WebSocket-API.postman_collection.json
```

## Usage Instructions

### 1. Setup Commands
```bash
# Create all necessary directories and files
mkdir -p .claude/commands/{code,system,project}
mkdir -p tests/{unit,integration,websocket,agent}
mkdir -p validation

# Copy the custom commands from the generated file
cp claude-commands-validation.md .claude/commands/
```

### 2. Run Individual Validations
```bash
# Backend validation using Claude Code CLI
claude "/project:analyze-backend Focus on WebSocket and agent integration"
claude "/project:test-websocket Include all error scenarios"
claude "/project:validate-agent Check state management and tools"

# Create iOS integration tests
claude "/project:ios-integration Focus on real-time communication"

# Setup Postman collection
claude "/project:postman-setup Include all command types and error cases"
```

### 3. Execute Comprehensive Validation
```bash
# Run the complete validation suite
python validation/e2e_test.py

# Run backend tests
pytest tests/ -v

# Run iOS tests (in Xcode or command line)
xcodebuild test -project YourApp.xcodeproj -scheme YourApp
```

### 4. Monitor and Debug
```bash
# Quick health check
claude "/user:health-check"

# Debug specific issues
claude "/user:debug-session Connection dropping after authentication"

# Pre-deployment validation
claude "/user:deploy-check Staging environment"
```

This comprehensive validation setup ensures your L3 coding agent works seamlessly from iOS mobile app to FastAPI backend, providing confidence in your vertical slice implementation.