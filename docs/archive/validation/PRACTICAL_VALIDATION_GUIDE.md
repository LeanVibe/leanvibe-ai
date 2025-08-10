# 🎯 Practical LeanVibe Validation Guide

## Quick Start - Working Example

Based on my testing, here's the exact sequence to get a working LeanVibe system with real AI responses:

### 1. System Check (2 minutes)

```bash
# Check you're in the right directory
cd /Users/bogdan/work/leanvibe-ai

# Verify Ollama models
ollama list
# Should show: mistral:7b-instruct and deepseek-r1:32b
```

### 2. Start with Working Model (Mistral)

Since DeepSeek R1 32B is very large and can be unstable, start with Mistral 7B:

```bash
# Test Mistral directly (should work immediately)
ollama run mistral:7b-instruct "What is 2+2? Be brief."
# Expected: "4." (fast response)

# Exit Ollama interactive mode
# Press Ctrl+C or type /bye
```

### 3. Backend Startup (Working Configuration)

```bash
cd leanvibe-backend

# Start backend (services should already be running)
./start.sh --skip-services
```

**Look for these success indicators:**
- ✅ MLX framework loaded successfully  
- ✅ Phi-3-Mini service with full transformers support
- Server starting on http://localhost:8000

### 4. CLI Validation (Real Tests)

Open a new terminal:

```bash
cd /Users/bogdan/work/leanvibe-ai/leanvibe-cli

# Test 1: Basic connection
uv run leanvibe status
# Should show: 🟢 Connected, AI Status: Ready

# Test 2: Performance check
uv run leanvibe performance
# Should show all optimizations enabled

# Test 3: Simple query (expect timeout initially)
timeout 30 uv run leanvibe query "Hello"
# May timeout - this is expected with current configuration
```

### 5. Direct API Testing (Bypass CLI issues)

```bash
# Test backend health
curl http://localhost:8000/health | python -m json.tool

# Test what endpoints are available
curl -s http://localhost:8000/ | grep -i "api\|endpoint" | head -5
```

### 6. Monitor System in Real-Time

```bash
# Terminal 1: Backend logs (keep running)
cd leanvibe-backend
./start.sh --skip-services

# Terminal 2: CLI monitoring
cd leanvibe-cli
uv run leanvibe monitor

# Terminal 3: Test queries
uv run leanvibe query --interactive
```

## Current System Status (What I Found)

### ✅ Working Components:
1. **Backend Services**: Neo4j, ChromaDB, Redis all healthy
2. **MLX Framework**: Successfully loaded and operational  
3. **CLI Connection**: Connects to backend correctly
4. **Performance Optimizations**: All optimizations active
5. **Ollama Integration**: Mistral 7B responds perfectly
6. **Service Health**: All health checks pass

### ⚠️ Current Limitations:
1. **AI Query Timeout**: CLI queries timeout after 30s
2. **DeepSeek Model**: 32B model may be too resource-intensive
3. **Backend Integration**: AI endpoints may need configuration
4. **Mock Mode**: Backend currently uses mock responses for safety

## Immediate Working Test

**Right now, you can test this:**

```bash
# 1. Verify Ollama works directly
ollama run mistral:7b-instruct "Explain what 2+2 equals"

# 2. Check backend is responsive  
curl http://localhost:8000/health

# 3. Test CLI connection
uv run leanvibe status

# 4. View performance optimizations
uv run leanvibe performance
```

## Monitoring System Details

### Real-time Backend Status
```bash
# View detailed metrics
uv run leanvibe status

# Current output shows:
# - Active Sessions: 4
# - Connected Clients: 5  
# - AI Status: Ready
# - Model: microsoft/Phi-3.5-mini-instruct (Mode: Mock)
```

### Performance Metrics
```bash
# Check optimization status
uv run leanvibe performance

# Shows:
# - HTTP/2: ✅ Enabled
# - Connection Pooling: ✅ Enabled  
# - Response Caching: ✅ Enabled
# - All performance features active
```

### System Health
```bash
# Monitor in real-time
uv run leanvibe monitor

# Or check individual components:
docker ps  # Docker services
curl http://localhost:8000/health  # Backend
ollama list  # Available models
```

## Getting Real AI Responses

### Option 1: Configure Backend for Ollama

The backend needs to be configured to use Ollama instead of mock responses. Check:

```bash
# Look for Ollama configuration in backend
grep -r "ollama\|11434" leanvibe-backend/app/
```

### Option 2: Test Ollama Integration Directly

```bash
# Use Ollama directly while backend development continues
alias ask-ai='ollama run mistral:7b-instruct'

# Then use:
ask-ai "Analyze this code: print('hello world')"
ask-ai "What are Python best practices?"
ask-ai "Explain this error: ImportError"
```

### Option 3: Validate Individual Components

```bash
# 1. Test each service independently
curl http://localhost:7474  # Neo4j UI
curl http://localhost:8001/api/v1/heartbeat  # ChromaDB  
redis-cli ping  # Redis

# 2. Test backend endpoints
curl http://localhost:8000/health
curl http://localhost:8000/docs  # API documentation

# 3. Test CLI components
uv run leanvibe --help
uv run leanvibe config init
```

## What's Working vs What Needs Configuration

### ✅ Fully Working Now:
- Backend services (Neo4j, ChromaDB, Redis)
- CLI interface and commands
- Performance optimizations
- Health monitoring
- Ollama direct usage
- Docker orchestration

### 🔧 Needs Configuration:
- Backend → Ollama integration
- AI query routing
- WebSocket AI endpoint
- Real model responses vs mock

### 🎯 Immediate Next Steps:

1. **Use working components**: Status, monitoring, performance
2. **Test Ollama directly**: For immediate AI responses  
3. **Configure backend**: To route queries to Ollama
4. **Validate integration**: Once backend connects to Ollama

## Success Validation Checklist

Run these commands in order and check results:

```bash
# ✅ 1. Backend health
curl http://localhost:8000/health | jq .status
# Expected: "healthy"

# ✅ 2. CLI connection  
uv run leanvibe status | head -3
# Expected: 🟢 Connected

# ✅ 3. Ollama working
echo "What is 2+2?" | ollama run mistral:7b-instruct
# Expected: Mathematical answer

# ✅ 4. Performance optimized
uv run leanvibe performance | grep "✅ Enabled"
# Expected: All features enabled

# 🔧 5. AI integration (needs work)
timeout 10 uv run leanvibe query "test" || echo "Expected timeout"
# Expected: Timeout (normal for now)
```

## Troubleshooting Quick Fixes

### If Backend Won't Start:
```bash
# Kill existing processes
lsof -ti:8000 | xargs kill -9
# Restart fresh
cd leanvibe-backend && ./start.sh
```

### If Ollama Issues:
```bash
# Restart Ollama service
brew services restart ollama
# Test smallest model
ollama run mistral:7b-instruct "test"
```

### If CLI Issues:
```bash
# Reinstall CLI
cd leanvibe-cli
pip install -e . --force-reinstall
# Test basic command
uv run leanvibe --version
```

---

**Current Status**: LeanVibe infrastructure is working correctly. Backend services are healthy, CLI is optimized and connecting properly, and Ollama provides high-quality AI responses. The final integration piece (backend → Ollama routing) needs configuration to get end-to-end AI queries working through the CLI.