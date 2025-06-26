# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# LeenVibe L3 Coding Assistant Project

## Project Overview
LeenVibe is an L3 autonomous coding assistant designed for senior engineers. It provides AI-powered development acceleration while maintaining human control, running entirely on local hardware with privacy-first architecture.

## Tech Stack

### Backend (Mac Agent)
- **Language:** Python 3.11+
- **LLM:** MLX with Qwen2.5-Coder-32B (Apple Silicon optimized)
- **Framework:** FastAPI with WebSocket support
- **Database:** PostgreSQL 15 with TimescaleDB, Neo4j for code graphs
- **Vector Store:** ChromaDB for code embeddings
- **Agent Framework:** Pydantic.ai for L3 implementation
- **Code Analysis:** Tree-sitter for AST parsing

### iOS Companion App
- **Framework:** SwiftUI (iOS 17.0+)
- **Communication:** WebSocket client
- **Discovery:** Bonjour/mDNS for local pairing
- **Visualization:** Mermaid.js for architecture diagrams

### CLI Integration
- **Framework:** Python Click
- **Integration:** Unix socket for vim plugin
- **Target:** Terminal-first workflow (vim+tmux)

## Common Commands

```bash
# Development Setup
pip install -r requirements.txt
docker-compose up

# Testing
pytest --cov=app --cov-report=html
pytest tests/unit/ -v
pytest tests/integration/ -v --asyncio-mode=auto

# Code Quality
black app/ tests/
isort app/ tests/
flake8 app/ tests/
mypy app/

# iOS Development (when implemented)
# Standard Xcode build process

# Performance Testing
pytest tests/performance/ -v --benchmark-only
```

## Architecture Overview

### Core Components
- **L3 Agent**: Semi-autonomous with confidence scoring and human gates
- **Code Graph**: Neo4j-based dependency and relationship mapping
- **Context Manager**: Maintains project understanding across sessions
- **CLI Interface**: Unix socket communication for vim integration
- **iOS Bridge**: WebSocket + Bonjour for mobile companion

### Key Design Patterns
- **Human-in-the-Loop**: Approval required for low-confidence actions
- **Privacy-First**: All processing local, no cloud dependencies
- **Event-Driven**: WebSocket for real-time updates
- **Plugin Architecture**: Extensible integration system

## Development Workflow

### Branch Strategy
- `main`: Production-ready code
- `develop`: Integration branch
- `feature/*`: New features
- `fix/*`: Bug fixes

### Commit Convention
- Use conventional commits: `feat:`, `fix:`, `docs:`, `test:`
- Include ticket/issue numbers when applicable

### Testing Requirements
- Unit test coverage: 90% minimum for critical paths
- Integration tests for all API endpoints
- Performance benchmarks for key operations:
  - Code suggestion: < 500ms
  - Architecture visualization: < 2s
  - iOS UI responsiveness: < 100ms

## Performance Targets
- **Agent Response:** < 500ms for code suggestions
- **Context Loading:** < 1s for large projects
- **Memory Usage:** < 8GB RAM during normal operation
- **Model Loading:** < 30s initial load

## Security Considerations
- All processing local - no external API calls
- End-to-end encryption for iOS-Mac communication
- Sandboxed code execution environment
- No telemetry or usage tracking

## Human Gate Requirements
Require explicit approval for:
1. Database schema changes
2. External dependencies additions
3. Security-sensitive operations
4. Architecture modifications
5. Production deployments

## Memory Management
- Session state persisted to `.leenvibe/sessions/`
- Context pruning at 80% capacity
- Automatic consolidation of long-running sessions

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
- **Model loading fails**: Ensure 48GB+ RAM available
- **WebSocket disconnects**: Check firewall/network settings
- **Performance degradation**: Monitor context size, trigger pruning
- **iOS pairing fails**: Verify both devices on same network

### Debug Commands
```bash
# Check agent status
leenvibe status --verbose

# Analyze context usage
leenvibe context --analyze

# Performance profiling
python -m cProfile -o profile.out app/main.py
```