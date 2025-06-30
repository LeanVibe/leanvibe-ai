# LeanVibe Backend

This is the backend service for the LeanVibe L3 Coding Agent. It provides WebSocket-based communication with iOS clients and integrates with local AI models for code assistance.

## Quick Start

### Prerequisites
- Python 3.11+
- macOS (for MLX support)
- 8GB+ RAM (16GB+ recommended)
- uv package manager (automatically installed by start script)

### Installation

**Option 1: Automatic Setup (Recommended)**
```bash
# One command setup - installs uv, dependencies, and starts server
./start.sh
```

**Option 2: Manual Setup**
```bash
# Install uv if not available
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies
uv sync

# Optional: Install MLX for Apple Silicon
uv sync --extra mlx

# Start server
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The server will start at `http://localhost:8000`

### Testing the API

1. Health check:
```bash
curl http://localhost:8000/health
```

2. WebSocket connection (using wscat):
```bash
# Install wscat if needed: npm install -g wscat
wscat -c ws://localhost:8000/ws/test-client
```

Then send a message:
```json
{"type": "command", "content": "/status"}
```

## Available Commands

- `/list-files [directory]` - List files in current or specified directory
- `/read-file <path>` - Read contents of a file  
- `/current-dir` - Show current working directory
- `/status` - Show agent status
- `/help` - Show help information

## Project Structure

```
app/
├── main.py              # FastAPI application entry point
├── core/
│   └── connection_manager.py  # WebSocket connection management
├── services/
│   └── ai_service.py    # AI processing and command handling
└── models/
    └── messages.py      # Pydantic data models
```

## Development

### Running Tests
```bash
# Run basic tests
uv run python run_tests.py

# Run with pytest (if installed)
uv run pytest tests/ -v

# Run integration tests (requires server running)
uv run python tests/test_integration.py
```

### Code Quality
```bash
# Install development dependencies
uv sync --extra dev

# Format code
uv run black app/ tests/

# Sort imports
uv run isort app/ tests/

# Lint code
uv run flake8 app/ tests/

# Type checking
uv run mypy app/
```

## Configuration

Currently uses default settings. Environment variables will be added in future versions:

- `LEANVIBE_HOST` - Server host (default: 0.0.0.0)
- `LEANVIBE_PORT` - Server port (default: 8000)  
- `LEANVIBE_LOG_LEVEL` - Logging level (default: INFO)

## Troubleshooting

### Common Issues

1. **Port already in use**: Change port with `--port 8001`
2. **Permission denied**: Ensure you have read permissions for directories
3. **MLX not found**: This is expected in MVP mode - full MLX integration coming soon

### Logs

Check logs for debugging:
```bash
uvicorn app.main:app --log-level debug
```

## Next Steps

- [ ] Add MLX model integration  
- [ ] Implement persistent session storage
- [ ] Add authentication
- [ ] Performance optimizations
- [ ] Docker containerization