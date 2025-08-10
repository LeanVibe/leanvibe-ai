# LeanVibe Installation Guide

Complete installation instructions for LeanVibe MVP - AI-powered local-first development assistant.

## Quick Start

### Automated Installation (Recommended)

**macOS/Linux:**
```bash
curl -fsSL https://raw.githubusercontent.com/leanvibe-ai/leanvibe/main/install.sh | bash
```

**Windows (PowerShell):**
```powershell
iwr -useb https://raw.githubusercontent.com/leanvibe-ai/leanvibe/main/install.ps1 | iex
```

**Local Installation:**
```bash
# Clone the repository
git clone https://github.com/leanvibe-ai/leanvibe.git
cd leanvibe

# Run installation script
./install.sh
```

### Docker Installation

```bash
# Clone and start with Docker
git clone https://github.com/leanvibe-ai/leanvibe.git
cd leanvibe

# Start services
docker-compose up -d

# Wait for models to download (first run only)
docker-compose logs -f model-init
```

## Manual Installation

### Prerequisites

#### System Requirements
- **OS:** macOS 10.15+, Ubuntu 18.04+, Windows 10+
- **Python:** 3.8 or higher
- **Memory:** 8GB RAM minimum (16GB recommended)
- **Storage:** 10GB free space (for AI models)
- **Network:** Internet connection for initial setup

#### Required Software
- **Python 3.8+** with pip
- **Git** for version control
- **Ollama** for AI model serving
- **Node.js 16+** (optional, for iOS development)

#### Optional Software
- **Xcode** (macOS only, for iOS development)
- **Docker** (for containerized deployment)
- **Visual Studio Code** (recommended IDE)

### Step 1: Install Dependencies

#### macOS
```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python git ollama node

# Install Xcode command line tools (for iOS development)
xcode-select --install
```

#### Linux (Ubuntu/Debian)
```bash
# Update package list
sudo apt update

# Install Python and Git
sudo apt install python3 python3-pip python3-venv git curl

# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Install Node.js (optional)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

#### Windows
```powershell
# Install Python from python.org
# Install Git from git-scm.com
# Install Ollama from ollama.com

# Or use Chocolatey
choco install python git nodejs
```

### Step 2: Clone Repository

```bash
git clone https://github.com/leanvibe-ai/leanvibe.git
cd leanvibe
```

### Step 3: Backend Setup

```bash
# Navigate to backend directory
cd leanvibe-backend

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
# macOS/Linux:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create environment configuration
cp .env.example .env
# Edit .env with your settings

# Test backend
python -c "import fastapi; print('✅ Backend dependencies OK')"
```

### Step 4: AI Models Setup

```bash
# Start Ollama service
ollama serve &

# Download required models (this may take several minutes)
ollama pull mistral:7b-instruct

# Verify models
ollama list
```

### Step 5: CLI Setup (Optional)

```bash
# Navigate to CLI directory
cd ../leanvibe-cli

# Install CLI in development mode
pip install -e .

# Test CLI
leanvibe --help
```

### Step 6: iOS Setup (macOS Only)

```bash
# Navigate to iOS directory
cd ../leanvibe-ios

# Open in Xcode
open LeanVibe.xcodeproj

# Or use Xcode command line
xcodebuild -list
```

## Verification

### Health Check

```bash
# Check system requirements
./install.sh --check

# Start backend
cd leanvibe-backend
source .venv/bin/activate
python -m uvicorn app.main:app --reload

# Test health endpoint
curl http://localhost:8000/health

# Test CLI
leanvibe health
```

### Test Installation

```bash
# Test backend API
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello LeanVibe!"}'

# Test CLI query
leanvibe query "What is LeanVibe?"

# Test WebSocket connection
# (Use web browser dev tools or WebSocket client)
```

## Configuration

### Backend Configuration

Edit `leanvibe-backend/.env`:

```bash
# Server Configuration
BACKEND_HOST=localhost
BACKEND_PORT=8000
LOG_LEVEL=INFO
ENVIRONMENT=development

# AI Configuration
OLLAMA_HOST=localhost
OLLAMA_PORT=11434
DEFAULT_MODEL=mistral:7b-instruct
MAX_TOKENS=1000
TEMPERATURE=0.1

# Security (change in production)
SECRET_KEY=your-secret-key-here
API_KEY=your-api-key-here
```

### CLI Configuration

Edit `~/.leanvibe/config.yaml`:

```yaml
backend:
  host: localhost
  port: 8000
  timeout: 30

ai:
  model: mistral:7b-instruct
  temperature: 0.1
  max_tokens: 1000

logging:
  level: INFO
  file: ~/.leanvibe/logs/cli.log
```

### iOS Configuration

Update `leanvibe-ios/LeanVibe/Config.swift`:

```swift
struct Config {
    static let backendHost = "localhost"
    static let backendPort = 8000
    static let websocketPath = "/ws"
}
```

## Advanced Setup

### Production Deployment

#### Environment Variables
```bash
# Production environment
export ENVIRONMENT=production
export LOG_LEVEL=WARNING
export SECRET_KEY="your-secure-secret-key"
export API_KEY="your-secure-api-key"

# Database (if using)
export DATABASE_URL="postgresql://user:pass@localhost/leanvibe"

# Redis (if using)
export REDIS_URL="redis://localhost:6379"
```

#### Security Hardening
```bash
# Generate secure keys
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Set file permissions
chmod 600 .env
chmod 755 install.sh

# Review security settings
./scripts/security_audit.py
```

#### Load Balancing
```bash
# Start multiple backend instances
python -m uvicorn app.main:app --port 8000 &
python -m uvicorn app.main:app --port 8001 &
python -m uvicorn app.main:app --port 8002 &

# Use nginx for load balancing
```

### Docker Deployment

#### Basic Setup
```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Scale backend
docker-compose up -d --scale backend=3
```

#### Production Setup
```bash
# Use production profile
docker-compose --profile production up -d

# With monitoring
docker-compose --profile monitoring up -d

# Custom configuration
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Development Setup

#### Hot Reload
```bash
# Backend with hot reload
cd leanvibe-backend
python -m uvicorn app.main:app --reload --host 0.0.0.0

# iOS with Xcode hot reload
# Enable "Hot Reload" in Xcode
```

#### Testing
```bash
# Run backend tests
cd leanvibe-backend
pytest tests/ -v

# Run security tests
python scripts/security_audit.py

# Run iOS tests
cd leanvibe-ios
xcodebuild test -scheme LeanVibe
```

## Troubleshooting

### Common Issues

#### Ollama Connection Failed
```bash
# Check Ollama status
ollama list
ps aux | grep ollama

# Restart Ollama
pkill ollama
ollama serve &

# Check port availability
lsof -i :11434
```

#### Python Environment Issues
```bash
# Recreate virtual environment
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### iOS Build Errors
```bash
# Clean build folder
rm -rf ~/Library/Developer/Xcode/DerivedData

# Reset simulators
xcrun simctl erase all

# Update provisioning profiles
```

#### Port Conflicts
```bash
# Find processes using ports
lsof -i :8000
lsof -i :11434

# Kill processes
kill -9 <PID>

# Use different ports
export BACKEND_PORT=8080
export OLLAMA_PORT=11435
```

### Logs and Debugging

#### Backend Logs
```bash
# View backend logs
tail -f leanvibe-backend/logs/app.log

# Adjust log level
export LOG_LEVEL=DEBUG
```

#### Ollama Logs
```bash
# View Ollama logs
ollama logs

# Ollama debug mode
OLLAMA_DEBUG=1 ollama serve
```

#### System Resources
```bash
# Monitor resource usage
htop
nvidia-smi  # For GPU usage

# Check disk space
df -h

# Check memory usage
free -h
```

## Performance Optimization

### Memory Usage
```bash
# Optimize Python memory
export PYTHONOPTIMIZE=1

# Limit Ollama memory
export OLLAMA_MAX_MEMORY=8GB
```

### Model Optimization
```bash
# Use quantized models
ollama pull mistral:7b-instruct-q4_0

# Cache models
export OLLAMA_MODELS=/path/to/fast/storage
```

### Network Optimization
```bash
# Enable compression
export ENABLE_GZIP=true

# Connection pooling
export MAX_CONNECTIONS=100
```

## Support

### Getting Help
- 📖 **Documentation**: Check `README.md` and `USER_GUIDE.md`
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/leanvibe-ai/leanvibe/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/leanvibe-ai/leanvibe/discussions)
- 📧 **Security**: security@leanvibe.ai

### Useful Commands
```bash
# System information
./install.sh --check

# Health diagnostics
leanvibe health --detailed

# Reset installation
rm -rf .venv ~/.leanvibe
./install.sh

# Update LeanVibe
git pull origin main
./install.sh
```

---

**Installation successful?** 🎉 Continue with the [User Guide](USER_GUIDE.md) to start using LeanVibe!