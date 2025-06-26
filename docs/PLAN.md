# LeenVibe Vertical Slice Implementation Plan

## Executive Summary

This document provides a detailed step-by-step implementation plan for creating a working vertical slice of the LeenVibe L3 Coding Agent. The vertical slice will demonstrate the core value proposition: a local AI assistant running on Mac that can be monitored and controlled via an iOS companion app.

## Current State Analysis

### Documentation Assessment
✅ **Strengths**:
- Comprehensive product vision and strategy documentation
- Detailed architecture specifications for full system
- Clear market analysis and user personas
- Well-defined technical stack and requirements
- Extensive UI/UX design documentation

❌ **Critical Gaps**:
- **No implementation code exists** - project is documentation-only
- Missing step-by-step setup instructions for developers
- No dependency management (requirements.txt, pyproject.toml)
- Missing development environment configuration
- No working examples or code templates

### Technical Debt Identified
1. **Over-specified initial scope**: Full system too complex for first iteration
2. **Missing implementation guidance**: Docs assume expert-level knowledge
3. **Conflicting model requirements**: 32B vs 7B model specifications
4. **Unclear deployment strategy**: Local-only vs cloud-optional confusion

## Vertical Slice Definition

### Core Value Proposition
**"Demonstrate that an L3 coding agent can run locally on Mac and be controlled via iOS with sub-2-second response times"**

### Minimal Feature Set (MVP)
1. **Mac Backend**: FastAPI server with basic AI agent that can list files and analyze simple code
2. **iOS App**: Single screen showing agent status and allowing command input
3. **Communication**: WebSocket connection between Mac and iOS
4. **AI Integration**: Local MLX with CodeLlama-7B (smaller than full 32B for MVP)

### Explicitly Deferred Features
- Advanced architecture visualization
- Voice commands
- Kanban board interface
- Multi-project support
- Complex agent autonomy levels
- Database persistence beyond simple file storage

## Implementation Roadmap

### Phase 1: Foundation (Week 1)

#### Week 1.1: Backend Foundation (Days 1-2)
**Objective**: Create working FastAPI server with basic AI integration

**Tasks for Junior Engineer**:

1. **Project Structure Setup**
   ```bash
   mkdir -p leenvibe-backend/{app,tests,docs}
   mkdir -p leenvibe-backend/app/{api,core,services,models}
   mkdir -p leenvibe-backend/tests/{unit,integration}
   ```

2. **Python Environment Setup**
   ```bash
   cd leenvibe-backend
   python3.11 -m venv venv
   source venv/bin/activate
   ```

3. **Create requirements.txt**
   ```txt
   fastapi==0.104.1
   uvicorn[standard]==0.24.0
   websockets==12.0
   pydantic==2.5.0
   mlx-lm==0.8.0
   python-multipart==0.0.6
   python-jose[cryptography]==3.3.0
   python-dotenv==1.0.0
   pytest==7.4.3
   pytest-asyncio==0.21.1
   httpx==0.25.2
   ```

4. **Basic FastAPI Application**
   - Create `app/main.py` with FastAPI instance
   - Add health check endpoint
   - Configure CORS for iOS communication
   - Add basic logging configuration

5. **MLX Integration Setup**
   - Create `app/services/ai_service.py`
   - Implement basic MLX model loading (CodeLlama-7B)
   - Add simple text completion endpoint
   - Include error handling for model loading failures

**Detailed Implementation Files**:

*app/main.py*:
```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import logging
import asyncio
from .services.ai_service import AIService
from .core.connection_manager import ConnectionManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="LeenVibe L3 Agent", version="0.1.0")

# Configure CORS for iOS communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to local network
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
ai_service = AIService()
connection_manager = ConnectionManager()

@app.on_event("startup")
async def startup_event():
    """Initialize AI service on startup"""
    logger.info("Starting LeenVibe backend...")
    await ai_service.initialize()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "leenvibe-backend"}

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for iOS communication"""
    await connection_manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_json()
            response = await ai_service.process_command(data)
            await websocket.send_json(response)
    except WebSocketDisconnect:
        connection_manager.disconnect(client_id)
        logger.info(f"Client {client_id} disconnected")
```

*app/services/ai_service.py*:
```python
import asyncio
import logging
from typing import Dict, Any, Optional
import mlx.core as mx
from mlx_lm import load, generate

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.is_initialized = False
    
    async def initialize(self):
        """Initialize MLX model"""
        try:
            logger.info("Loading CodeLlama-7B model...")
            # Use smaller model for MVP - can upgrade to 32B later
            self.model, self.tokenizer = load("codellama/CodeLlama-7b-Instruct-hf")
            self.is_initialized = True
            logger.info("AI service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AI service: {e}")
            self.is_initialized = False
    
    async def process_command(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process command from iOS client"""
        if not self.is_initialized:
            return {"status": "error", "message": "AI service not initialized"}
        
        command = data.get("content", "")
        command_type = data.get("type", "message")
        
        try:
            if command_type == "command" and command.startswith("/"):
                return await self._process_slash_command(command)
            else:
                return await self._process_message(command)
        except Exception as e:
            logger.error(f"Error processing command: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _process_slash_command(self, command: str) -> Dict[str, Any]:
        """Process slash commands like /list-files"""
        if command == "/list-files":
            import os
            files = os.listdir(".")
            return {
                "status": "success",
                "type": "file_list",
                "data": files,
                "message": f"Found {len(files)} files in current directory"
            }
        elif command == "/status":
            return {
                "status": "success",
                "type": "agent_status",
                "data": {"model": "CodeLlama-7B", "ready": True},
                "message": "Agent is ready and operational"
            }
        else:
            return {
                "status": "error",
                "message": f"Unknown command: {command}"
            }
    
    async def _process_message(self, message: str) -> Dict[str, Any]:
        """Process general messages with AI"""
        if not message.strip():
            return {"status": "error", "message": "Empty message"}
        
        try:
            # Simple prompt for code assistance
            prompt = f"[INST] You are a coding assistant. Help with this request: {message} [/INST]"
            
            # Generate response (simplified for MVP)
            response = generate(
                self.model,
                self.tokenizer,
                prompt=prompt,
                max_tokens=150,
                temp=0.7
            )
            
            return {
                "status": "success",
                "type": "ai_response",
                "message": response,
                "timestamp": asyncio.get_event_loop().time()
            }
        except Exception as e:
            return {"status": "error", "message": f"AI processing failed: {e}"}
```

#### Week 1.2: iOS Foundation (Days 3-4)
**Objective**: Create basic iOS app with WebSocket communication

**Tasks for Junior Engineer**:

1. **Create iOS Project**
   ```bash
   # In Xcode
   File > New > Project > iOS > App
   Product Name: LeenVibe
   Interface: SwiftUI
   Language: Swift
   Minimum Deployment: iOS 16.0
   ```

2. **Add WebSocket Dependencies**
   - Add Starscream WebSocket library via Swift Package Manager
   - URL: `https://github.com/daltoniam/Starscream.git`

3. **Core iOS Implementation**

*WebSocketService.swift*:
```swift
import Foundation
import Starscream

class WebSocketService: ObservableObject, WebSocketDelegate {
    @Published var isConnected = false
    @Published var messages: [AgentMessage] = []
    @Published var connectionStatus = "Disconnected"
    
    private var socket: WebSocket?
    private let serverURL = "ws://localhost:8000/ws/ios-client"
    
    func connect() {
        guard let url = URL(string: serverURL) else { return }
        
        var request = URLRequest(url: url)
        request.timeoutInterval = 5
        
        socket = WebSocket(request: request)
        socket?.delegate = self
        socket?.connect()
        
        connectionStatus = "Connecting..."
    }
    
    func disconnect() {
        socket?.disconnect()
        isConnected = false
        connectionStatus = "Disconnected"
    }
    
    func sendCommand(_ command: String, type: String = "message") {
        let message = [
            "type": type,
            "content": command,
            "timestamp": ISO8601DateFormatter().string(from: Date())
        ]
        
        guard let data = try? JSONSerialization.data(withJSONObject: message),
              let jsonString = String(data: data, encoding: .utf8) else { return }
        
        socket?.write(string: jsonString)
    }
    
    // MARK: - WebSocketDelegate
    
    func didReceive(event: Starscream.WebSocketEvent, client: Starscream.WebSocketClient) {
        switch event {
        case .connected(let headers):
            DispatchQueue.main.async {
                self.isConnected = true
                self.connectionStatus = "Connected"
            }
            
        case .disconnected(let reason, let code):
            DispatchQueue.main.async {
                self.isConnected = false
                self.connectionStatus = "Disconnected"
            }
            
        case .text(let string):
            if let data = string.data(using: .utf8),
               let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
                DispatchQueue.main.async {
                    let message = AgentMessage(
                        content: json["message"] as? String ?? "No response",
                        isFromUser: false,
                        timestamp: Date()
                    )
                    self.messages.append(message)
                }
            }
            
        case .error(let error):
            print("WebSocket error: \(error?.localizedDescription ?? "Unknown")")
            
        default:
            break
        }
    }
}

struct AgentMessage: Identifiable {
    let id = UUID()
    let content: String
    let isFromUser: Bool
    let timestamp: Date
}
```

*ContentView.swift*:
```swift
import SwiftUI

struct ContentView: View {
    @StateObject private var webSocketService = WebSocketService()
    @State private var inputText = ""
    
    var body: some View {
        NavigationView {
            VStack {
                // Connection Status
                HStack {
                    Circle()
                        .fill(webSocketService.isConnected ? .green : .red)
                        .frame(width: 12, height: 12)
                    Text(webSocketService.connectionStatus)
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                    Spacer()
                }
                .padding()
                
                // Messages List
                ScrollView {
                    LazyVStack(alignment: .leading, spacing: 12) {
                        ForEach(webSocketService.messages) { message in
                            MessageBubble(message: message)
                        }
                    }
                    .padding()
                }
                
                // Input Area
                HStack {
                    TextField("Enter command or message", text: $inputText)
                        .textFieldStyle(RoundedBorderTextFieldStyle())
                    
                    Button("Send") {
                        sendMessage()
                    }
                    .disabled(inputText.isEmpty || !webSocketService.isConnected)
                }
                .padding()
            }
            .navigationTitle("LeenVibe Agent")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(webSocketService.isConnected ? "Disconnect" : "Connect") {
                        if webSocketService.isConnected {
                            webSocketService.disconnect()
                        } else {
                            webSocketService.connect()
                        }
                    }
                }
            }
        }
    }
    
    private func sendMessage() {
        guard !inputText.isEmpty else { return }
        
        let message = AgentMessage(
            content: inputText,
            isFromUser: true,
            timestamp: Date()
        )
        webSocketService.messages.append(message)
        
        let commandType = inputText.hasPrefix("/") ? "command" : "message"
        webSocketService.sendCommand(inputText, type: commandType)
        
        inputText = ""
    }
}

struct MessageBubble: View {
    let message: AgentMessage
    
    var body: some View {
        HStack {
            if message.isFromUser { Spacer() }
            
            VStack(alignment: message.isFromUser ? .trailing : .leading) {
                Text(message.content)
                    .padding()
                    .background(message.isFromUser ? .blue : .gray.opacity(0.2))
                    .foregroundColor(message.isFromUser ? .white : .primary)
                    .cornerRadius(12)
                
                Text(DateFormatter.shortTime.string(from: message.timestamp))
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            if !message.isFromUser { Spacer() }
        }
    }
}

extension DateFormatter {
    static let shortTime: DateFormatter = {
        let formatter = DateFormatter()
        formatter.timeStyle = .short
        return formatter
    }()
}
```

#### Week 1.3: Integration Testing (Days 5-7)
**Objective**: Ensure Mac-iOS communication works reliably

**Tasks**:
1. Test WebSocket connection establishment
2. Verify command processing flow
3. Add error handling for connection drops
4. Create basic performance benchmarks
5. Document setup process

### Phase 2: Core Features (Week 2)

#### Enhanced Agent Capabilities
- Extend AI service with file reading and basic code analysis
- Add confidence scoring for responses
- Implement simple state persistence
- Create more sophisticated command processing

#### iOS User Experience
- Add command history and favorites
- Implement agent status visualization
- Create settings screen for server configuration
- Add haptic feedback for interactions

### Phase 3: Documentation & Polish (Week 3)

#### Setup Documentation
- Create step-by-step installation guide
- Document environment requirements
- Add troubleshooting section
- Create video demonstration

#### Code Quality
- Add comprehensive unit tests
- Implement integration test suite
- Add performance monitoring
- Create code documentation

## Success Criteria & Validation

### Technical Requirements
1. **Response Time**: < 2 seconds for basic commands
2. **Reliability**: Handle connection drops gracefully
3. **Usability**: Junior engineer setup in < 30 minutes
4. **Performance**: Handle 5+ concurrent iOS connections

### Functional Requirements
1. **Basic Commands**: `/list-files`, `/status`, `/analyze-file`
2. **AI Integration**: Natural language code questions
3. **Real-time Communication**: WebSocket bidirectional messaging
4. **Error Handling**: Graceful failure modes

### Quality Gates
- [ ] All unit tests pass
- [ ] Integration tests cover WebSocket flow
- [ ] Performance benchmarks meet targets
- [ ] Setup documentation verified with new developer
- [ ] Demo video shows complete flow

## Risk Mitigation

### Technical Risks
1. **MLX Model Size**: Use CodeLlama-7B instead of 32B for MVP
2. **iOS-Mac Discovery**: Hardcode localhost for initial version
3. **Memory Usage**: Monitor and optimize model loading
4. **WebSocket Stability**: Implement reconnection logic

### Implementation Risks
1. **Scope Creep**: Strictly maintain minimal feature set
2. **Over-engineering**: Focus on working solution first
3. **Documentation Debt**: Document as you build
4. **Testing Gaps**: Write tests for core functionality only

## Next Steps After Vertical Slice

### Phase 4: Enhanced Features
- Voice command integration
- Architecture visualization
- Multi-project support
- Advanced agent autonomy

### Phase 5: Production Ready
- Cloud sync capabilities
- Advanced security
- Performance optimization
- User analytics

## Appendix: Environment Setup Guide

### macOS Requirements
- macOS 13.0+ (Ventura)
- Apple Silicon (M1/M2/M3)
- 16GB+ RAM (32GB+ recommended)
- Python 3.11+
- Xcode 15+

### Installation Commands
```bash
# Backend setup
git clone <repo>
cd leenvibe-backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# iOS setup (in Xcode)
# Open LeenVibe.xcodeproj
# Build and run on device or simulator
```

This plan provides the detailed roadmap needed to create a working vertical slice while maintaining focus on core value delivery and avoiding scope creep.