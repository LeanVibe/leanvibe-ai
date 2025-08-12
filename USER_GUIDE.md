# 📖 LeanVibe AI User Guide

**Welcome to LeanVibe AI!** This guide will help you get started with the MVP-ready local AI coding assistant.

## 🎯 What is LeanVibe?

LeanVibe is a **local-first AI coding assistant** that helps developers by:
- Answering coding questions in **<10 seconds**
- Analyzing code files and providing insights
- Managing project tasks and development workflow
- Maintaining **complete privacy** (all processing happens locally)

## 🚀 Quick Setup (5 minutes)

### Step 1: Install Ollama (AI Service)

```bash
# Install Ollama if not already installed
brew install ollama

# Start Ollama service
ollama serve &

# Download the Mistral 7B model (4.1GB, one-time download)
ollama pull mistral:7b-instruct
```

### Step 2: Start LeanVibe Backend

```bash
# Navigate to the backend directory
cd leanvibe-backend

# Install Python dependencies
pip install fastapi uvicorn pydantic aiofiles httpx

# Start the backend server
python app/main.py
```

The backend will start at `http://localhost:8765`

### Step 3: Test Your Setup

```bash
# Navigate to CLI directory
cd leanvibe-cli

# Install CLI dependencies
pip install rich click pyyaml websockets

# Run comprehensive health check
python -m leanvibe_cli health --detailed
```

You should see all services showing as "healthy" ✅

## 🎮 Using LeanVibe

### Basic Commands

**Health Check**: Verify all services are working
```bash
leanvibe health
```

**Ask Questions**: Get AI help with coding
```bash
leanvibe query "How do I optimize Python performance?"
leanvibe query "What does this function do in main.py?"
```

**Check Status**: View backend connection and performance
```bash
leanvibe status --detailed
```

### Example Workflow

1. **Start your day**: Check system health
   ```bash
   leanvibe health
   ```

2. **Ask coding questions**: Get instant AI assistance
   ```bash
   leanvibe query "How do I handle async errors in Python?"
   ```

3. **Analyze code**: Understand complex code files
   ```bash
   leanvibe query "analyze file ./src/complex_module.py"
   ```

4. **Interactive mode**: Have a conversation with the AI
   ```bash
   leanvibe query --interactive
   ```

## 📊 Performance Expectations

### Response Times (Achieved in MVP)
- **Simple questions**: ~2.7 seconds
- **Complex analysis**: ~8.6 seconds
- **Directory operations**: Instant
- **Average response**: **2.84 seconds**

### System Requirements
- **Memory**: 8GB RAM minimum, 16GB recommended
- **Storage**: 10GB free space (for AI models)
- **CPU**: Apple Silicon (M1/M2/M3/M4) or modern Intel/AMD

## 🔧 Troubleshooting

### Common Issues

**"Connection failed" error**
```bash
# Check if Ollama is running
ollama list

# Check if backend is running
curl http://localhost:8765/health

# Restart services if needed
ollama serve &
python app/main.py
```

**"AI service not ready" warning**
```bash
# Pull the AI model if missing
ollama pull mistral:7b-instruct

# Verify model is available
ollama list
```

**Slow response times**
```bash
# Check system resources
htop  # or Activity Monitor on Mac

# Verify using correct model
leanvibe health --detailed
# Should show "Model: mistral:7b-instruct"
```

### Getting Help

**Run diagnostics**:
```bash
leanvibe health --detailed --json > health_report.json
```

**Check logs**:
- Backend logs: Check terminal where you started `python app/main.py`
- Ollama logs: Check terminal where you started `ollama serve`

## 🎯 What's Possible Now (MVP Features)

### ✅ **Working Features**
- **AI Q&A**: Ask any coding question, get answers in <10s
- **Code Analysis**: Analyze Python files and get insights
- **Directory Operations**: List files, navigate projects
- **Health Monitoring**: Comprehensive system diagnostics
- **Performance Tracking**: Real-time response time monitoring

### 🔄 **Coming Soon** (Production Features)
- **Voice Interface**: "Hey LeanVibe" wake phrase
- **iOS Mobile App**: Mobile companion with real-time sync
- **Advanced Analysis**: Multi-file analysis and architecture insights
- **Team Features**: Shared knowledge base and collaboration
- **IDE Integration**: Direct integration with popular editors

## 🔒 Privacy & Security

### Data Processing
- **100% Local**: All AI processing happens on your machine
- **No Network Calls**: No data sent to external services during AI processing
- **Complete Privacy**: Your code never leaves your computer

### What Data is Stored
- **Local Only**: Session data, preferences, and AI responses stored locally
- **No Telemetry**: No usage analytics or data collection
- **Your Control**: All data remains under your complete control

## 📈 Performance Tips

### Optimize Performance
1. **Close Unnecessary Apps**: Free up RAM for AI processing
2. **Use SSD Storage**: Faster model loading and response times
3. **Monitor Temperature**: Prevent thermal throttling on intensive tasks
4. **Regular Updates**: Keep Ollama and models updated

### Best Practices
1. **Ask Specific Questions**: More focused questions get better answers
2. **Provide Context**: Include relevant file paths or code snippets
3. **Use Interactive Mode**: For complex problem-solving sessions
4. **Check Health Regularly**: Monitor system performance with `leanvibe health`

## 🆘 Support

### Self-Help Resources
- Run `leanvibe health --detailed` for comprehensive diagnostics
- Check the troubleshooting section above
- Review the performance tips for optimization

### Community & Development
- **Documentation**: See `AGENTS.md` for technical details
- **Development**: Check `NEXT_STEPS_PLAN.md` for roadmap
- **Issues**: Report bugs or request features via the project repository

---

**Congratulations!** You're now ready to use LeanVibe AI for your coding projects. Start with a simple question and experience the power of local AI assistance.