# LeanVibe AI - Development Workflow Guide

## 🚀 Development Environment Setup

### Prerequisites

**Hardware Requirements**
- Apple Silicon Mac (M1/M2/M3) - Required for Apple MLX framework
- 16GB+ RAM recommended (32GB+ for optimal performance)
- 50GB+ available storage for models and development tools

**Software Requirements**
```bash
# Core dependencies
Python 3.11+
Xcode 15.0+ (iOS 18.0+ support)
Git 2.40+
Node.js 18+ (for documentation tools)

# Install Python dependencies
pip install mlx-lm fastapi uvicorn pydantic-ai
pip install neo4j chromadb python-multipart
pip install websockets click rich

# Install iOS development tools
xcode-select --install
```

### Project Setup

**Repository Structure**
```
leanvibe-ai/
├── leanvibe-backend/          # Python FastAPI backend
├── leanvibe-ios/             # SwiftUI iOS application  
├── leanvibe-cli/             # Python CLI tool
├── docs/                     # Documentation and guides
├── scripts/                  # Automation and utility scripts
└── .github/                  # CI/CD and templates
```

**Initial Setup Commands**
```bash
# Clone and setup main repository
git clone https://github.com/bogdan/leanvibe-ai.git
cd leanvibe-ai

# Setup Python virtual environment
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
pip install -r leanvibe-backend/requirements.txt

# iOS setup
cd leanvibe-ios
xcodebuild -project LeanVibe.xcodeproj -list
xcodebuild -project LeanVibe.xcodeproj -scheme LeanVibe build

# CLI setup  
cd ../leanvibe-cli
pip install -e .
```

---

## 🔄 Git Worktree Development Strategy

### Worktree Structure

**Primary Branches**
```bash
# Main development branches
main/                    # Production-ready code
integration/            # Integration testing branch
production/             # Production release branch

# Agent-specific worktrees (parallel development)
agent-alpha/            # iOS foundation and performance
agent-beta/             # Backend API and infrastructure  
agent-delta/            # CLI enhancement and developer experience

# Archived worktrees (completed work)
archives/agent-gamma/   # Architecture visualization (completed)
archives/agent-kappa/   # Voice interface and testing (completed)
```

**Worktree Commands**
```bash
# Create new agent worktree
git worktree add -b agent-feature ../agent-feature origin/main

# List all worktrees
git worktree list

# Switch between worktrees
cd ../agent-alpha  # Move to different worktree

# Remove completed worktree
git worktree remove ../agent-gamma
git branch -D agent-gamma  # Clean up branch
```

### Branch Management

**Naming Conventions**
```bash
# Feature branches
feature/DS-XXX-description    # New feature implementation
fix/DS-XXX-description       # Bug fix
docs/DS-XXX-description      # Documentation updates
perf/DS-XXX-description      # Performance optimization

# Agent branches
agent-alpha/feature-name     # Agent-specific feature work
agent-beta/api-enhancement   # Backend-specific development
```

**Branch Protection Rules**
- `main` branch requires pull request review
- All tests must pass before merge
- SwiftLint and code quality checks required
- Performance regression tests must pass

---

## 📝 Code Quality Standards

### Swift Development (iOS)

**SwiftLint Configuration**
```yaml
# .swiftlint.yml
disabled_rules:
  - trailing_whitespace
  - line_length

opt_in_rules:
  - empty_count
  - missing_docs
  - private_outlet

included:
  - leanvibe-ios/LeanVibe
  
excluded:
  - Pods
  - leanvibe-ios/LeanVibe/Generated
```

**Swift Style Guidelines**
```swift
// Naming conventions
class StoryCardView: View { }           // Views: UpperCamelCase + View suffix
class StoryViewModel: ObservableObject { } // ViewModels: UpperCamelCase + ViewModel
struct Story: Codable { }              // Models: UpperCamelCase, descriptive

// Async patterns
@MainActor
class VoiceInterface: ObservableObject {
    func processCommand(_ command: String) async throws -> AIResponse {
        // Use Swift Concurrency with proper @MainActor marking
    }
}

// Memory management
class WebSocketManager {
    func connect() {
        webSocket.onReceive = { [weak self] message in
            // Always use [weak self] to prevent retain cycles
        }
    }
}
```

### Python Development (Backend/CLI)

**Code Formatting**
```bash
# Install formatting tools
pip install black isort flake8 mypy

# Format code
black leanvibe-backend/
isort leanvibe-backend/
flake8 leanvibe-backend/
mypy leanvibe-backend/
```

**Python Style Guidelines**
```python
# FastAPI service structure
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List

class CodeRequest(BaseModel):
    """Request model for code analysis."""
    code: str
    language: str
    confidence_threshold: float = 0.8

@app.post("/api/v1/ai/analyze")
async def analyze_code(request: CodeRequest) -> CodeResponse:
    """Analyze code with AI model and return suggestions."""
    try:
        result = await ai_service.analyze(request.code)
        return CodeResponse(suggestions=result.suggestions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**Type Safety Requirements**
- All function signatures must include type hints
- Use Pydantic models for API request/response
- Enable strict mypy checking for critical components
- Document complex types with examples

---

## 🧪 Testing Framework

### iOS Testing (Swift)

**Unit Testing Structure**
```swift
// LeanVibeTests/VoiceInterfaceTests.swift
import XCTest
@testable import LeanVibe

final class VoiceInterfaceTests: XCTestCase {
    var voiceInterface: VoiceInterface!
    
    override func setUp() {
        super.setUp()
        voiceInterface = VoiceInterface()
    }
    
    func testWakePhraseDetection() async throws {
        // Given
        let testPhrase = "Hey LeanVibe, analyze this code"
        
        // When
        let command = try await voiceInterface.processCommand(testPhrase)
        
        // Then
        XCTAssertEqual(command.action, .analyzeCode)
        XCTAssertTrue(command.confidence > 0.8)
    }
    
    func testPerformanceResponseTime() {
        // Performance test for <500ms requirement
        self.measure {
            _ = voiceInterface.detectWakePhrase("Hey LeanVibe")
        }
    }
}
```

**Testing Commands**
```bash
# Run all iOS tests with coverage
swift test --enable-code-coverage

# Run specific test suite
swift test --filter VoiceInterfaceTests

# Performance testing
swift test --filter PerformanceTests
```

### Backend Testing (Python)

**API Testing Structure**
```python
# tests/test_ai_service.py
import pytest
from fastapi.testclient import TestClient
from leanvibe_backend.main import app

client = TestClient(app)

class TestAIService:
    @pytest.mark.asyncio
    async def test_code_analysis_endpoint(self):
        """Test AI code analysis with valid input."""
        response = client.post(
            "/api/v1/ai/analyze",
            json={
                "code": "def hello(): print('world')",
                "language": "python",
                "confidence_threshold": 0.8
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data
        assert len(data["suggestions"]) > 0

    def test_websocket_connection(self):
        """Test WebSocket connection and message handling."""
        with client.websocket_connect("/ws") as websocket:
            websocket.send_json({"type": "ping"})
            data = websocket.receive_json()
            assert data["type"] == "pong"
```

**Testing Commands**
```bash
# Run backend tests with coverage
pytest --cov=leanvibe_backend tests/

# Run specific test categories
pytest -m integration tests/
pytest -m performance tests/

# Load testing
locust -f tests/load_test.py --host=http://localhost:8000
```

---

## 🚀 Build and Deployment

### Development Build Process

**iOS Development Build**
```bash
# Quick syntax check
swiftc -parse leanvibe-ios/LeanVibe/**/*.swift

# Full development build
xcodebuild -project leanvibe-ios/LeanVibe.xcodeproj \
           -scheme LeanVibe \
           -configuration Debug \
           build

# Build with tests
xcodebuild -project leanvibe-ios/LeanVibe.xcodeproj \
           -scheme LeanVibe \
           -configuration Debug \
           build test
```

**Backend Development**
```bash
# Start development server
cd leanvibe-backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Background development with auto-restart
honcho start  # Uses Procfile for multi-process development

# Production-like testing
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Production Build Process

**iOS Production Build**
```bash
# Archive for App Store
xcodebuild -project leanvibe-ios/LeanVibe.xcodeproj \
           -scheme LeanVibe \
           -configuration Release \
           -archivePath LeanVibe.xcarchive \
           archive

# Export for App Store submission
xcodebuild -exportArchive \
           -archivePath LeanVibe.xcarchive \
           -exportPath ./build \
           -exportOptionsPlist ExportOptions.plist
```

**Backend Production Package**
```bash
# Create distribution package
python setup.py bdist_wheel

# Docker production image
docker build -t leanvibe-backend:latest .
docker run -p 8000:8000 leanvibe-backend:latest

# Production configuration validation
python -m leanvibe_backend.config.validate_production
```

---

## 🔍 Quality Gates and Validation

### Pre-Commit Validation

**Automated Quality Checks**
```bash
#!/bin/bash
# scripts/pre-commit-check.sh

echo "🔍 Running quality gates..."

# Swift quality checks
echo "📱 iOS: Running SwiftLint..."
swiftlint lint --config .swiftlint.yml --quiet
if [ $? -ne 0 ]; then exit 1; fi

echo "📱 iOS: Running tests..."
swift test --enable-code-coverage > /dev/null
if [ $? -ne 0 ]; then exit 1; fi

# Python quality checks  
echo "🐍 Backend: Running Python linting..."
black --check leanvibe-backend/
isort --check leanvibe-backend/
flake8 leanvibe-backend/

echo "🐍 Backend: Running tests..."
pytest leanvibe-backend/tests/ -v
if [ $? -ne 0 ]; then exit 1; fi

echo "✅ All quality gates passed!"
```

**Integration Health Check**
```bash
#!/bin/bash
# scripts/integration-health-check.sh

echo "🔄 Running 5-minute integration health check..."

# Start backend
uvicorn leanvibe_backend.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
sleep 5

# Test backend health
curl -f http://localhost:8000/health || exit 1

# Test WebSocket connection
python scripts/test_websocket.py || exit 1

# Test iOS build
xcodebuild -project leanvibe-ios/LeanVibe.xcodeproj -scheme LeanVibe build > /dev/null
if [ $? -ne 0 ]; then 
    kill $BACKEND_PID
    exit 1
fi

# Cleanup
kill $BACKEND_PID
echo "✅ Integration health check passed!"
```

### Performance Validation

**Performance Benchmarks**
```bash
# iOS performance validation
swift test --filter PerformanceTests

# Backend load testing
ab -n 1000 -c 10 http://localhost:8000/api/v1/health

# Memory usage monitoring
instruments -t "Time Profiler" LeanVibe.app

# WebSocket performance testing
python scripts/websocket_load_test.py --connections 100 --duration 60
```

---

## 📚 Documentation Standards

### Code Documentation

**Swift Documentation**
```swift
/// Manages voice interface interactions with natural language processing.
/// 
/// The VoiceInterface provides wake phrase detection and command processing
/// with sub-500ms response times for optimal user experience.
///
/// - Important: Requires microphone permissions and Speech Recognition setup.
/// - Version: 1.0
/// - Since: iOS 18.0
class VoiceInterface: ObservableObject {
    
    /// Processes voice commands and returns structured AI requests.
    ///
    /// - Parameter command: Natural language voice command from user
    /// - Returns: Structured AIRequest with action and parameters
    /// - Throws: VoiceProcessingError if command cannot be parsed
    func processCommand(_ command: String) async throws -> AIRequest {
        // Implementation
    }
}
```

**Python Documentation**
```python
class AIService:
    """
    AI service for code analysis and generation using Qwen2.5-Coder-32B.
    
    This service provides local AI processing with confidence-driven decision
    making and maintains privacy by processing all requests on-device.
    
    Attributes:
        model: The loaded Qwen2.5-Coder model instance
        confidence_threshold: Minimum confidence for autonomous actions (0.8)
        
    Example:
        >>> ai_service = AIService()
        >>> result = await ai_service.analyze_code("def hello(): pass")
        >>> print(result.suggestions)
    """
    
    async def analyze_code(self, code: str, language: str) -> CodeAnalysisResult:
        """
        Analyze code and provide improvement suggestions.
        
        Args:
            code: Source code to analyze
            language: Programming language (python, swift, etc.)
            
        Returns:
            CodeAnalysisResult with suggestions and confidence scores
            
        Raises:
            AIProcessingError: If model processing fails
            ValueError: If language is not supported
        """
```

### Commit Message Standards

**Conventional Commits Format**
```bash
# Format: type(scope): description
feat(ios): add voice interface with wake phrase detection
fix(backend): resolve WebSocket connection memory leaks  
docs(api): update authentication endpoint documentation
perf(ios): optimize voice response time to <500ms
test(backend): add comprehensive WebSocket integration tests

# Breaking changes
feat(api)!: restructure authentication endpoints for security

# With ticket reference
fix(ios): resolve crash in voice processing (DS-123)
```

---

## 🤖 AI Agent Integration Workflow

### Agent Development Process

**Agent Onboarding**
1. **Context Setup**: Create agent-specific CLAUDE.md with domain expertise
2. **Worktree Creation**: Dedicated development environment assignment  
3. **Task Assignment**: Clear deliverables with success criteria
4. **Integration Planning**: Defined handoff points and quality gates

**Agent Coordination Protocol**
```markdown
# Agent Status Update Template
## Current Sprint: [Sprint Number]
## Agent: [ALPHA/BETA/DELTA] 
## Progress: [Percentage]% Complete

### Completed This Week:
- [ ] Task 1: Description and validation
- [ ] Task 2: Description and validation

### In Progress:
- [ ] Task 3: Current status and expected completion

### Blockers:
- Dependency on [Other Agent] for [Specific Requirement]
- Technical challenge: [Description and proposed solution]

### Next Week Plan:
- [ ] Priority 1: Critical path item
- [ ] Priority 2: Enhancement or optimization
```

**Integration Checkpoints**
- **Daily**: Progress updates in STATUS.md
- **Weekly**: Cross-agent integration testing
- **Sprint End**: Comprehensive integration and quality validation

### Quality Assurance for AI Development

**Agent Code Review Process**
1. **Automated Validation**: All quality gates must pass
2. **Integration Testing**: Cross-component compatibility verification
3. **Performance Validation**: Response time and resource usage benchmarks
4. **Documentation Review**: Code comments and API documentation completeness

**Human Review Gates**
- **Architecture Changes**: Significant structural modifications require human review
- **Security Implications**: Authentication, privacy, or security-related changes
- **Performance Regressions**: Any degradation in critical performance metrics
- **External Integrations**: New third-party dependencies or API integrations

---

This comprehensive development workflow ensures high-quality, consistent development practices across all team members and AI agents working on the LeanVibe AI project.