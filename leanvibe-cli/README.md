# 🖥️ LeanVibe CLI

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Click](https://img.shields.io/badge/Click-CLI_Framework-green.svg)](https://click.palletsprojects.com/)
[![Rich](https://img.shields.io/badge/Rich-Terminal_UI-orange.svg)](https://rich.readthedocs.io/)

> **A powerful command-line interface for developers to interact with the LeanVibe AI backend, providing real-time monitoring, codebase analysis, and intelligent assistance.**

The LeanVibe CLI is a terminal-native interface that connects to the LeanVibe backend for real-time code analysis, architectural insights, and intelligent suggestions powered by local AI processing.

## ✨ Features

- **🔍 Real-Time Monitoring**: Live file watching and change detection
- **🧠 AI-Powered Analysis**: Intelligent code insights and suggestions
- **📊 Rich Dashboards**: Beautiful terminal interfaces with live updates
- **🎯 Task Management**: Integrated task tracking and project management
- **🗣️ Voice Integration**: Voice command support for hands-free operation
- **⚡ High Performance**: Optimized with caching, connection pooling, and smart timeouts
- **📈 Performance Monitoring**: Built-in benchmarking and performance metrics

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **LeanVibe Backend**: Must be running (see [Backend README](../leanvibe-backend/README.md))

### Installation

**Option 1: Development Install (Recommended)**
```bash
# Clone repository
git clone https://github.com/LeanVibe/leanvibe-ai.git
cd leanvibe-ai/leanvibe-cli

# Install in development mode
pip install -e .

# Verify installation
leanvibe --version
```

**Option 2: Production Install**
```bash
pip install leanvibe-cli
```

### First Run

```bash
# Check connection to backend
leanvibe status

# Start interactive monitoring
leanvibe monitor

# Analyze current project
leanvibe analyze

# Get help
leanvibe --help
```

## 🛠️ Commands

### Core Commands

| Command | Description | Example |
|---------|-------------|---------|
| `status` | Check backend connection and health | `leanvibe status` |
| `analyze` | Analyze codebase or specific files | `leanvibe analyze src/` |
| `monitor` | Start real-time monitoring dashboard | `leanvibe monitor` |
| `query` | Ask questions about your codebase | `leanvibe query "How does auth work?"` |
| `config` | Manage CLI configuration | `leanvibe config --backend-url ws://localhost:8000` |
| `qr` | Generate QR code for mobile connection | `leanvibe qr` |

### Command Examples

**Status Check**
```bash
# Basic status
leanvibe status

# Verbose status with details
leanvibe status --detailed
```

**Code Analysis**
```bash
# Analyze current directory
leanvibe analyze

# Analyze specific file
leanvibe analyze src/main.py

# Complex analysis with options
leanvibe analyze --complexity --architecture --dependencies
```

**Real-Time Monitoring**
```bash
# Start monitoring current project
leanvibe monitor

# Monitor with filters
leanvibe monitor -f high

# Monitor for specific time
leanvibe monitor -t 60
```

**Interactive Queries**
```bash
# Ask about code patterns
leanvibe query "What are the main classes in this project?"

# Interactive session with L3 agent
leanvibe query --interactive

# Execute slash commands
leanvibe query "/status"
```

## ⚙️ Configuration

### Configuration File

The CLI uses YAML configuration files:

- **Project-specific**: `.leanvibe/cli-config.yaml`
- **User-wide**: `~/.leanvibe/cli-config.yaml`

```yaml
# Backend connection
backend_url: http://localhost:8000
websocket_url: ws://localhost:8000/ws
timeout_seconds: 30

# Display preferences
verbose: false
syntax_highlighting: true
show_timestamps: true
compact_mode: false
max_lines_output: 50

# Monitoring settings
auto_detect_project: true
show_notifications: true
notification_level: medium

# Project settings
project_root: /path/to/project
exclude_patterns:
  - "*.pyc"
  - "__pycache__"
  - ".git"
  - "node_modules"
```

### Command-Line Options

```bash
# Override backend URL
leanvibe --backend-url http://192.168.1.100:8000 status

# Use custom config file
leanvibe --config /path/to/config.yml monitor

# Enable verbose output
leanvibe --verbose analyze
```

### Environment Variables

```bash
export LEANVIBE_BACKEND_URL="http://localhost:8000"
export LEANVIBE_CONFIG_PATH="~/.leanvibe/cli-config.yaml"
export LEANVIBE_LOG_LEVEL="INFO"
```

## 🎨 Terminal UI Features

### Live Dashboard

The monitoring command provides a rich, live-updating dashboard:

```
┌─ LeanVibe Monitor ─────────────────────────────────────────────┐
│                                                                │
│ 📊 Project: my-awesome-app                Status: ● Connected  │
│ 📁 Files: 1,247                          Changes: 3 pending   │
│ 🧠 AI: Ready                             Backend: Healthy     │
│                                                                │
├─ Recent Changes ───────────────────────────────────────────────┤
│ • src/main.py:42        [Modified]     2s ago                 │
│ • tests/test_api.py     [Created]      5s ago                 │
│ • README.md             [Modified]     1m ago                 │
│                                                                │
├─ AI Insights ──────────────────────────────────────────────────┤
│ 💡 Consider adding type hints to main.py                      │
│ 🔍 New test file detected - coverage improved                 │
│ ⚠️  Potential circular import in auth module                   │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### Interactive Session Example

```bash
❯ leanvibe query --interactive

❯ What files have high complexity?
✅ Response (Confidence: 85.2%)
Based on the analysis, here are the files with high complexity:

• src/core/analyzer.py - Complexity: 24.5
• src/utils/parser.py - Complexity: 18.3  
• src/services/processor.py - Complexity: 16.8

❯ Show me the architecture patterns
✅ Response (Confidence: 92.1%)
Architecture Patterns Detected:
• Service Layer Pattern - Well-structured service separation
• Repository Pattern - Data access abstraction
• Factory Pattern - Object creation abstraction

❯ quit
Goodbye!
```

## 🔧 Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/LeanVibe/leanvibe-ai.git
cd leanvibe-ai/leanvibe-cli

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Project Structure

```
leanvibe-cli/
├── leanvibe_cli/
│   ├── __init__.py
│   ├── main.py              # CLI entry point
│   ├── client.py            # Backend communication
│   ├── config/              # Configuration management
│   │   ├── __init__.py
│   │   ├── manager.py       # Config file handling
│   │   ├── schema.py        # Configuration schema
│   │   └── wizard.py        # Interactive setup
│   ├── commands/            # CLI commands
│   │   ├── __init__.py
│   │   ├── analyze.py       # Code analysis commands
│   │   ├── monitor.py       # Real-time monitoring
│   │   ├── query.py         # AI query interface
│   │   ├── status.py        # Status checking
│   │   └── config.py        # Configuration commands
│   ├── ui/                  # Terminal UI components
│   │   ├── __init__.py
│   │   ├── live_dashboard.py # Live dashboard
│   │   └── notification_overlay.py # Desktop notifications
│   ├── services/            # Core services
│   │   ├── __init__.py
│   │   ├── desktop_notifications.py
│   │   └── notification_service.py
│   └── utils/               # Utility functions
│       ├── __init__.py
│       └── yaml_helpers.py
├── tests/                   # Test suite
├── pyproject.toml          # Project configuration
└── README.md               # This file
```

### Testing

```bash
# Run all tests
python run_tests.py

# Run with pytest
pytest

# Run with coverage
pytest --cov=leanvibe_cli tests/

# Run integration tests (requires backend)
pytest tests/test_integration.py
```

### Code Quality

```bash
# Format code
black leanvibe_cli/ tests/

# Sort imports
isort leanvibe_cli/ tests/

# Lint code
flake8 leanvibe_cli/ tests/

# Type checking
mypy leanvibe_cli/
```

## ⚡ Performance Optimization

The LeanVibe CLI is optimized for speed and efficiency with multiple performance enhancements:

### Performance Features

- **🗄️ Intelligent Caching**: Response caching with configurable TTL
- **🔗 Connection Pooling**: HTTP connection reuse for better performance  
- **⏱️ Smart Timeouts**: Adaptive timeouts based on operation complexity
- **🚀 HTTP/2 Support**: Modern protocol support when available
- **📊 Performance Monitoring**: Built-in metrics and benchmarking

### Performance Commands

```bash
# View performance metrics and optimization status
leanvibe performance

# Run performance benchmark
leanvibe performance --benchmark

# Clean up expired cache entries  
leanvibe performance --cleanup

# Reset performance counters
leanvibe performance --reset
```

### Performance Metrics

The CLI tracks and displays:
- Command execution times
- Cache hit/miss ratios  
- Connection establishment times
- Memory usage patterns
- Query success rates

### Typical Performance

- **Connection Speed**: 1-5ms (excellent)
- **Simple Queries**: 10s timeout with optimization
- **Cache Hit Rate**: Up to 80%+ for repeated operations
- **Memory Usage**: <10MB for optimal performance
- **Startup Time**: <500ms with lazy loading

See [PERFORMANCE_OPTIMIZATIONS.md](PERFORMANCE_OPTIMIZATIONS.md) for detailed technical information.

## 🔌 Backend Integration

### WebSocket Communication

The CLI communicates with the backend via WebSocket for real-time updates:

```python
from leanvibe_cli.client import BackendClient

client = BackendClient("ws://localhost:8000")

# Connect and send command
await client.connect()
response = await client.send_command("analyze", {"path": "src/"})
```

### Message Protocol

```json
{
  "type": "command",
  "id": "unique-request-id",
  "command": "analyze",
  "payload": {
    "path": "src/main.py",
    "options": ["syntax", "security"]
  }
}
```

## 📱 Mobile Integration

### QR Code Connection

Generate QR codes for easy mobile app connection:

```bash
# Generate QR code for current backend
leanvibe qr

# QR code with custom backend URL
leanvibe qr --backend-url ws://192.168.1.100:8000

# Save QR code to file
leanvibe qr --output connection.png
```

## 🐛 Troubleshooting

### Common Issues

**CLI command not found?**
```bash
# Ensure CLI is installed
pip list | grep leanvibe

# Reinstall if needed
pip install -e .
```

**Backend connection failed?**
```bash
# Check backend status
curl http://localhost:8000/health

# Try different backend URL
leanvibe --backend-url http://127.0.0.1:8000 status

# Check network connectivity
ping localhost
```

**Configuration issues?**
```bash
# Check current config
leanvibe --verbose status

# Reset configuration
rm ~/.leanvibe/cli-config.yaml
leanvibe status  # Will recreate with defaults
```

### Debug Mode

```bash
# Enable debug logging
export LEANVIBE_LOG_LEVEL=DEBUG
leanvibe --verbose monitor

# Save debug logs
leanvibe monitor 2>&1 | tee debug.log
```

## 🚀 Advanced Usage

### Scripting and Automation

```bash
# Batch analysis with JSON output
leanvibe analyze --json src/ > analysis.json

# Monitor with custom filtering
leanvibe monitor -f critical --json

# Automated code review
leanvibe query "Review this change" --workspace /path/to/project
```

### Integration Examples

```bash
# Development workflow
leanvibe monitor &          # Start monitoring
leanvibe status            # Check status
leanvibe query "Is this change following patterns?"

# CI/CD integration
leanvibe analyze --all --json > analysis.json
if [ $? -ne 0 ]; then exit 1; fi
```

## 🤝 Contributing

### Development Guidelines

1. **Fork and clone the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
4. **Add tests for new functionality**
5. **Ensure code quality**
   ```bash
   black leanvibe_cli/ tests/
   flake8 leanvibe_cli/ tests/
   pytest
   ```

6. **Commit with conventional format**
   ```bash
   git commit -m "feat: add new monitoring feature"
   ```

7. **Submit a pull request**

### Code Standards

- Follow PEP 8 style guidelines
- Use type hints for all functions
- Write docstrings for public APIs
- Add tests for new features
- Maintain backward compatibility

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

## 🔗 Related Projects

- [LeanVibe Backend](../leanvibe-backend/README.md) - Core AI backend service
- [LeanVibe iOS](../leanvibe-ios/README.md) - iOS companion app
- [Main Project](../README.md) - Overall project documentation

---

**Built with ❤️ for developers who value efficiency and powerful terminal tools**