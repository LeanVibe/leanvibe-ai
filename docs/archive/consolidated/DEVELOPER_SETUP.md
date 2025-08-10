# LeanVibe Developer Setup Guide

**Fast Track Setup**: Get up and running in under 10 minutes

## Quick Start (Recommended)

### 1. Prerequisites Check
```bash
# Verify Python 3.11+
python3 --version

# Verify Node.js (for CLI dependencies)
node --version

# Verify Git
git --version
```

### 2. Backend Setup (2-3 minutes)
```bash
# Clone and setup backend
cd leanvibe-backend

# Install dependencies
pip install -r requirements.txt

# Start backend services
python -m app.main
```

**Backend should start on**: `http://localhost:8000`

### 3. CLI Setup (1-2 minutes)
```bash
# Install LeanVibe CLI
cd leanvibe-cli
pip install -e .

# Initialize your project
leanvibe init

# Verify setup
leanvibe status --detailed
```

### 4. Validation (1 minute)
Run the comprehensive health check:
```bash
leanvibe status --detailed
```

**Expected Output**: All services should show ✅ status

---

## Detailed Setup Instructions

### Backend Services Architecture

The LeanVibe backend consists of several integrated services:

#### Core Services
- **FastAPI Application**: Main API server (`app.main`)
- **AI Processing Service**: Apple MLX integration for on-device AI
- **WebSocket Manager**: Real-time communication hub
- **Project Service**: Codebase analysis and metrics
- **Task Service**: Kanban-style task management

#### Optional Services (Enhanced Features)
- **Neo4j**: Dependency graph analysis (Docker)
- **Chroma**: Vector embeddings for code search (Docker) 
- **Redis**: Caching and session management (Docker)

### Backend Configuration

#### Environment Variables
```bash
# Required
export LEANVIBE_ENV=development
export API_HOST=0.0.0.0
export API_PORT=8000

# Optional (Advanced Features)
export NEO4J_URI=bolt://localhost:7687
export CHROMA_HOST=localhost
export REDIS_URL=redis://localhost:6379
```

#### Development Mode
```bash
# Start with hot reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start with verbose logging
python -m app.main --log-level debug
```

### CLI Configuration

#### Global Configuration
The CLI uses a hierarchical configuration system:
1. Command-line arguments (highest priority)
2. Project-specific config (`.leanvibe/config.yaml`)
3. User config (`~/.config/leanvibe/config.yaml`)
4. System defaults (lowest priority)

#### Project Configuration Structure
```yaml
# .leanvibe/config.yaml
project:
  name: "my-project"
  type: "python"
  version: "1.0.0"

leanvibe:
  backend_url: "http://localhost:8000"
  features:
    ai_assistance: true
    code_analysis: true
    auto_commits: true
    live_monitoring: true

development:
  monitoring:
    file_patterns: ["*.py", "*.js", "*.ts"]
    ignore_patterns: ["__pycache__/*", "node_modules/*"]
    auto_analysis: true
  
  ai_assistance:
    auto_suggest_commits: true
    code_review_hints: true
    refactoring_suggestions: true
```

### Service Health Validation

The enhanced `leanvibe init` command performs comprehensive backend validation:

#### Validation Checks
- ✅ **Health Check**: Backend responds and reports healthy status
- ✅ **AI Service**: Apple MLX models loaded and ready for inference
- ✅ **WebSocket**: Real-time communication channel working
- ✅ **iOS Bridge**: Mobile app integration endpoints available  
- ✅ **Projects API**: Core project management functionality working

#### Troubleshooting Common Issues

**Backend Connection Failed**
```bash
# Check if backend is running
curl http://localhost:8000/health

# Restart backend with verbose logging
python -m app.main --log-level debug
```

**AI Service Not Ready**
```bash
# Check MLX installation (macOS only)
python -c "import mlx; print('MLX available')"

# Restart backend to reload AI models
pkill -f "python -m app.main" && python -m app.main
```

**WebSocket Connection Issues**
```bash
# Test WebSocket manually
wscat -c ws://localhost:8000/ws/test_client

# Check firewall settings
sudo lsof -i :8000
```

**iOS Bridge Not Responding**
```bash
# Test iOS endpoints
curl http://localhost:8000/api/ios/status

# Check iOS bridge is loaded
curl http://localhost:8000/docs | grep ios
```

## Advanced Setup Options

### Docker Development Environment

For consistent development environments across teams:

```bash
# Start all services with Docker Compose
docker-compose up -d

# Verify all services are healthy
docker-compose ps
leanvibe status --detailed
```

### Production-Like Setup

```bash
# Install production dependencies
pip install -r requirements-prod.txt

# Setup production database (PostgreSQL)
createdb leanvibe_prod

# Run with production settings
LEANVIBE_ENV=production python -m app.main
```

### Team Development Setup

```bash
# Shared team configuration
cp .leanvibe/config.yaml.template .leanvibe/config.yaml

# Configure team backend URL
sed -i 's/localhost:8000/team-backend.example.com/' .leanvibe/config.yaml

# Validate team setup
leanvibe status --detailed
```

## Performance Optimization

### Backend Performance
- **Memory Usage**: Target <200MB for backend services
- **Response Time**: API calls <100ms, AI inference <2s
- **Concurrent Users**: Supports 50+ concurrent WebSocket connections

### CLI Performance
- **Startup Time**: <500ms for most commands
- **Project Analysis**: <5s for projects up to 100K lines of code
- **Real-time Monitoring**: <50ms latency for file change detection

## Development Workflow Integration

### IDE Integration
```bash
# VS Code integration
leanvibe init --vscode-config

# Vim integration  
leanvibe init --vim-config

# Generic editor integration
leanvibe init --generic-editor
```

### Git Workflow Integration
```bash
# Setup git hooks
leanvibe init --git-hooks

# Configure AI-powered commits
git config leanvibe.auto-commit-ai true

# Test git integration
leanvibe git commit --ai-message
```

### CI/CD Integration
```bash
# GitHub Actions integration
leanvibe init --github-actions

# Pre-commit hooks
leanvibe analyze --pre-commit

# Build validation
leanvibe project run test && leanvibe analyze --full
```

## Support and Troubleshooting

### Self-Diagnosis
```bash
# Comprehensive system check
leanvibe status --detailed --json > health_report.json

# Performance benchmarking
leanvibe benchmark --full

# Connection diagnostics
leanvibe diagnose --network
```

### Common Commands
```bash
# Reset configuration
leanvibe config reset

# Clear cache and restart
leanvibe cache clear && leanvibe restart

# Export logs for debugging
leanvibe logs export --last 1h
```

### Getting Help
- **Documentation**: Run `leanvibe --help` for comprehensive command reference
- **Issues**: Report problems with `leanvibe diagnose --report`
- **Community**: Use `leanvibe community --discord` for real-time support

---

## Success Criteria

After completing setup, you should be able to:
- ✅ Run `leanvibe status --detailed` and see all services healthy
- ✅ Execute `leanvibe query "analyze this codebase"` and get AI responses
- ✅ Use `leanvibe monitor` for real-time project monitoring
- ✅ Access `http://localhost:8000/docs` for API documentation
- ✅ Connect iOS app (if available) via `leanvibe ios status`

**Setup Time**: ~10 minutes for standard configuration, ~20 minutes for full feature setup

This setup guide ensures developers can quickly onboard to the LeanVibe development environment while providing comprehensive troubleshooting and advanced configuration options.