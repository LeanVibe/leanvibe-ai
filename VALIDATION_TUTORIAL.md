# 🧪 LeanVibe System Validation Tutorial

A complete step-by-step guide to validate that the LeanVibe system is working correctly with a real AI model.

## Prerequisites Checklist

Before starting, ensure you have:
- [ ] macOS with Apple Silicon (M1/M2/M3/M4)
- [ ] Docker Desktop running
- [ ] Python 3.11+ installed
- [ ] Ollama installed (`brew install ollama`)
- [ ] Git repository cloned locally

## Step 1: Verify System Requirements

### Check Hardware
```bash
# Verify Apple Silicon
uname -m
# Should output: arm64

# Check available memory (recommend 32GB+ for DeepSeek R1 32B)
system_profiler SPHardwareDataType | grep "Memory:"
```

### Check Software Dependencies
```bash
# Docker status
docker --version && docker info

# Python version
python3 --version

# Ollama status
ollama --version
```

## Step 2: Install and Configure Ollama with DeepSeek R1

### Install DeepSeek R1 Model
```bash
# This downloads ~19GB model - ensure good internet connection
ollama pull deepseek-r1:32b

# Verify installation
ollama list
# Should show: deepseek-r1:32b

# Test Ollama directly
ollama run deepseek-r1:32b "What is 2+2? Explain step by step."
```

**Expected Output**: High-quality response with step-by-step reasoning showing the model works.

## Step 3: Start Backend Services

### Navigate to Backend Directory
```bash
cd leanvibe-ai/leanvibe-backend
```

### Start All Services
```bash
# Start with full service stack
./start.sh

# Alternative: Start without Docker services if they're already running
./start.sh --skip-services
```

### Verify Backend Startup
Look for these success indicators:
- [ ] ✅ Neo4j is ready
- [ ] ✅ Chroma is ready  
- [ ] ✅ Redis is ready
- [ ] ✅ MLX framework loaded successfully
- [ ] ✅ Phi-3-Mini service with full transformers support
- [ ] QR code displayed
- [ ] Server started on http://localhost:8000

### Test Backend Health
```bash
# In a new terminal window
curl http://localhost:8000/health | python -m json.tool

# Should show status: "healthy"
```

## Step 4: Install and Configure CLI

### Install CLI
```bash
cd ../leanvibe-cli

# Development installation
pip install -e .

# Verify installation
leanvibe --version
```

### Test CLI Connection
```bash
# Check backend connection
leanvibe status

# Should show:
# 🟢 Connected
# Backend: http://localhost:8000
# AI Status: Ready
```

## Step 5: Validate AI Model Integration

### Method 1: Direct Ollama Test
```bash
# Test Ollama API directly
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-r1:32b",
    "prompt": "What is 2+2? Explain your reasoning.",
    "stream": false
  }' | python -m json.tool
```

**Expected**: Detailed mathematical response with reasoning.

### Method 2: Backend AI Endpoint Test
```bash
# Test backend's AI integration
curl -X POST http://localhost:8000/api/ai/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is 2+2?",
    "session_id": "test_session"
  }' | python -m json.tool
```

### Method 3: CLI Query Test
```bash
# Test through CLI (may timeout due to model initialization)
timeout 60 leanvibe query "What is 2+2? Please be brief."

# If timeout occurs, try WebSocket test
leanvibe query --interactive
# Then type: What is 2+2?
# Type: quit to exit
```

## Step 6: Monitor System Performance

### Check Performance Metrics
```bash
# View CLI performance optimization status
leanvibe performance

# Run performance benchmark
leanvibe performance --benchmark
```

### Monitor Backend Metrics
```bash
# Check detailed backend status
leanvibe status

# Monitor in real-time
leanvibe monitor
```

## Step 7: Troubleshooting Common Issues

### Issue 1: "Query timed out"
**Cause**: DeepSeek R1 32B model is large and may take time to load initially.

**Solutions**:
```bash
# 1. Verify Ollama is responding
ollama list
ollama run deepseek-r1:32b "test"

# 2. Check if model is loaded in memory
ps aux | grep ollama

# 3. Try smaller model first
ollama pull mistral:7b-instruct
# Update backend config to use mistral temporarily
```

### Issue 2: "Backend not connected"
**Solutions**:
```bash
# 1. Check if backend is running
lsof -i :8000

# 2. Restart backend
cd leanvibe-backend
./start.sh

# 3. Check Docker services
docker ps
```

### Issue 3: "Mock mode" instead of real model
**Cause**: Backend falling back to mock responses.

**Solutions**:
```bash
# 1. Verify Ollama service
curl http://localhost:11434/api/tags

# 2. Check backend logs for errors
# Look at the terminal where backend is running

# 3. Restart with verbose logging
DEBUG=1 ./start.sh
```

## Step 8: Validate End-to-End Workflow

### Complete Validation Test
```bash
# 1. Status check
leanvibe status
echo "✓ Backend connected"

# 2. Simple query
echo "Testing simple query..."
leanvibe query "Hello, are you working?"

# 3. Mathematical reasoning
echo "Testing mathematical reasoning..."
leanvibe query "What is 15 * 23? Show your calculation."

# 4. Code analysis query
echo "Testing code analysis..."
leanvibe query "Explain what this code does: print('Hello World')"

# 5. Performance check
leanvibe performance
```

## Expected Results

### ✅ Successful Validation Indicators

1. **Backend Health**:
   - Status: "healthy"
   - AI Status: "Ready"
   - Model shows as actual model (not "Mock")
   - All services (Neo4j, Redis, ChromaDB) connected

2. **CLI Performance**:
   - Connection time: <10ms
   - Commands execute without errors
   - Performance metrics show optimization features enabled

3. **AI Responses**:
   - High-quality, detailed responses
   - Mathematical reasoning is accurate
   - Code explanations are meaningful
   - Response times: 10-60 seconds for complex queries

4. **Model Integration**:
   - Ollama shows DeepSeek R1 32B loaded
   - Backend connects to Ollama successfully
   - No timeout errors on simple queries

### ❌ Issues to Investigate

1. **Consistent Timeouts**: Model may not be properly integrated
2. **Mock Responses**: Fallback mode active, real model not connected
3. **Connection Errors**: Service configuration issues
4. **Performance Problems**: Resource constraints or configuration issues

## Advanced Testing

### Test Complex Scenarios
```bash
# 1. Interactive session
leanvibe query --interactive
# Try multiple queries in succession

# 2. Project analysis
cd /path/to/your/code/project
leanvibe analyze

# 3. Real-time monitoring
leanvibe monitor
# Make changes to files and observe
```

### Performance Optimization
```bash
# 1. Cache optimization
leanvibe performance --cleanup

# 2. Memory usage check
leanvibe performance --benchmark
```

## Configuration Fine-tuning

### Optimize for Your System
```bash
# Create custom CLI config
leanvibe config init

# Edit timeout settings for large models
nano ~/.leanvibe/cli-config.yaml
```

### Sample Optimized Config
```yaml
# ~/.leanvibe/cli-config.yaml
backend_url: "http://localhost:8000"
timeout_seconds: 120  # Increased for large models
websocket_timeout: 300
verbose: true
show_progress: true
```

## Success Criteria

The system is working correctly when:

- [ ] Backend starts without errors
- [ ] All Docker services are healthy
- [ ] Ollama DeepSeek model responds to direct queries
- [ ] CLI connects to backend successfully
- [ ] AI queries return meaningful, accurate responses
- [ ] Performance metrics show good optimization
- [ ] No persistent timeout or connection errors

## Next Steps

Once validation is complete:

1. **Explore Advanced Features**:
   - Real-time monitoring (`leanvibe monitor`)
   - Project analysis (`leanvibe analyze`)
   - iOS app integration (scan QR code)

2. **Customize Configuration**:
   - Adjust timeouts for your hardware
   - Configure notification preferences
   - Set up project-specific settings

3. **Integrate into Workflow**:
   - Use interactive query sessions
   - Set up monitoring for active projects
   - Explore voice commands (iOS app)

---

**Remember**: The DeepSeek R1 32B model is very large and powerful. Initial queries may take 30-60 seconds, but subsequent queries should be faster as the model stays loaded in memory.