# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# LeanVibe L3 Coding Assistant Project

## Project Overview
LeanVibe is an L3 autonomous coding assistant designed for senior engineers. It provides AI-powered development acceleration while maintaining human control, running entirely on local hardware with privacy-first architecture.

**Current Status**: Foundation phase - iOS companion app and backend WebSocket communication working. **✅ Real MLX model inference implemented and tested successfully!**

## Tech Stack

### Backend (Mac Agent) - Current State
- **Language:** Python 3.11+
- **Framework:** FastAPI with WebSocket support ✅ (Implemented)
- **Testing:** pytest with comprehensive test suite ✅ (44+ tests passing)
- **Package Manager:** uv for dependency management ✅
- **Development:** Hot reload with uvicorn ✅

### Backend (Mac Agent) - Planned
- **LLM:** MLX with Phi-3-Mini-128K-Instruct (Microsoft, MVP-optimized) ✅ (Architecture Ready - MVP Perfect)
- **Vector Store:** ChromaDB for code embeddings ⚠️ (Planned)  
- **Agent Framework:** Pydantic.ai for L3 implementation ⚠️ (Planned)
- **Code Analysis:** Tree-sitter for AST parsing ⚠️ (Planned)

### iOS Companion App - Current State
- **Framework:** SwiftUI (iOS 17.0+) ✅ (Implemented)
- **Communication:** WebSocket client ✅ (Working)
- **Discovery:** QR code pairing system ✅ (Implemented)
- **Persistence:** Auto-reconnect with UserDefaults ✅ (Working)

### CLI Integration - Planned
- **Framework:** Python Click ⚠️ (Not Started)
- **Integration:** Unix socket for vim plugin ⚠️ (Not Started) 
- **Target:** Terminal-first workflow (vim+tmux) ⚠️ (Not Started)

## Common Commands

```bash
# Development Setup (Current)
cd leanvibe-backend && uv sync
./start.sh  # Starts server with QR code

# Testing (Current)
cd leanvibe-backend
python run_tests.py  # or uv run pytest
pytest tests/ -v
pytest --cov=app --cov-report=html

# Code Quality (Current)
black app/ tests/
isort app/ tests/
flake8 app/ tests/
mypy app/

# iOS Development (Current)
open LeanVibe-iOS-App/LeanVibe.xcodeproj  # Current working iOS project
# SwiftUI app with QR scanner and WebSocket connection

# iOS Development - Testing
# Use Xcode Test Navigator or iOS Simulator

# Performance Testing (When Available)
# pytest tests/performance/ -v --benchmark-only
```

## Architecture Overview

### Core Components - Current Implementation
- **FastAPI Backend**: WebSocket server with QR pairing ✅
- **iOS Bridge**: SwiftUI app with real-time WebSocket communication ✅
- **Connection Management**: QR-based pairing with auto-reconnect ✅
- **Testing Infrastructure**: Comprehensive test suite with pytest ✅

### Core Components - In Development  
- **L3 Agent**: Semi-autonomous with confidence scoring and human gates ⚠️
- **Code Context**: Project understanding and dependency mapping ⚠️
- **CLI Interface**: Unix socket communication for vim integration ⚠️
- **Vector Database**: ChromaDB for code embeddings ⚠️

### Key Design Patterns - Implemented
- **Privacy-First**: All processing local, no cloud dependencies ✅
- **Event-Driven**: WebSocket for real-time updates ✅
- **Connection Resilience**: Auto-reconnect and connection persistence ✅

### Key Design Patterns - Planned
- **Human-in-the-Loop**: Approval required for low-confidence actions ⚠️
- **Plugin Architecture**: Extensible integration system ⚠️

## Development Workflow

### Branch Strategy
- `main`: Production-ready code
- `develop`: Integration branch
- `feature/*`: New features
- `fix/*`: Bug fixes

### Commit Convention
- Use conventional commits: `feat:`, `fix:`, `docs:`, `test:`
- Include ticket/issue numbers when applicable

### Testing Requirements - Current
- Unit test coverage: 80%+ for implemented features ✅
- Integration tests for WebSocket endpoints ✅  
- iOS app functionality testing ✅
- Backend API testing with 44+ tests ✅

### Testing Requirements - Target
- Unit test coverage: 90% minimum for critical paths
- Performance benchmarks for key operations:
  - Code suggestion: < 500ms ⚠️ (Not yet implemented)
  - Architecture visualization: < 2s ⚠️ (Not yet implemented)
  - iOS UI responsiveness: < 100ms ✅ (Meeting target)

## Performance Targets - Current vs Target

### Current Performance
- **WebSocket Response:** < 50ms for connection/messaging ✅
- **iOS App Launch:** < 2s ✅  
- **QR Code Generation:** < 100ms ✅
- **Connection Persistence:** Auto-reconnect working ✅

### Target Performance (When AI Implemented)
- **Agent Response:** < 500ms for code suggestions ⚠️
- **Context Loading:** < 1s for large projects ⚠️  
- **Memory Usage:** < 16GB RAM during normal operation ⚠️ (MVP-friendly with Phi-3-Mini)
- **Model Loading:** < 30s initial load ⚠️ (Optimized for smaller model)

## Security Considerations - Current Status
- All processing local - no external API calls ✅
- WebSocket communication over local network only ✅
- No telemetry or usage tracking ✅
- Connection tokens stored securely in iOS app ✅

## Security Considerations - Planned
- End-to-end encryption for iOS-Mac communication ⚠️
- Sandboxed code execution environment ⚠️
- Code analysis safety mechanisms ⚠️

## Current Limitations & Known Issues
1. **Model Weights**: Phi-3-Mini-128K-Instruct architecture ready, need to download weights ✅ (MVP-Perfect Choice)
2. **No CLI Tool**: Terminal workflow not yet implemented ⚠️ (Planned)
3. **No Session Persistence**: Beyond WebSocket connection state ⚠️ (Planned)
4. **Limited Error Handling**: Basic error cases covered ⚠️ (Improving)

## Memory Management - Planned
- Session state persisted to `.leanvibe/sessions/` ⚠️
- Context pruning at 80% capacity ⚠️
- Automatic consolidation of long-running sessions ⚠️

## Quality Gates
Before any PR:
1. All tests passing (pytest)
2. Code coverage maintained
3. No security vulnerabilities (bandit)
4. Performance benchmarks met
5. Documentation updated

## Common Development Tasks

### Adding a New Agent Capability
1. Define capability in `app/agents/capabilities/`
2. Add confidence scoring logic
3. Implement human gate if confidence < 85%
4. Add unit tests with mocked LLM responses
5. Update capability registry

### Extending CLI Commands
1. Add command to `app/cli/commands/`
2. Update Unix socket protocol if needed
3. Add integration tests
4. Update vim plugin mappings

### iOS Feature Development
1. SwiftUI views in standard MVVM pattern
2. WebSocket messages follow defined protocol
3. Maintain offline-first capability
4. Test on both iPhone and iPad

## Troubleshooting

### Common Issues
- **Model loading fails**: Ensure 16GB+ RAM available (MVP-friendly requirements)
- **WebSocket disconnects**: Check firewall/network settings
- **Performance degradation**: Monitor context size, trigger pruning
- **iOS pairing fails**: Verify both devices on same network

### Debug Commands
```bash
# Check agent status
leanvibe status --verbose

# Analyze context usage
leanvibe context --analyze

# Performance profiling
python -m cProfile -o profile.out app/main.py
```