# LeanVibe CLI

Terminal-native interface for enterprise codebase analysis and real-time monitoring.

## Overview

LeanVibe CLI is a minimal viable command-line interface that connects to the sophisticated LeanVibe backend infrastructure. It provides real-time codebase monitoring, AST-powered analysis, and intelligent suggestions through a terminal-native experience.

## Features

- 🔍 **Real-time Monitoring**: Live file change notifications and architectural violation detection
- 🧠 **AI-Powered Analysis**: Natural language queries to the L3 agent with project context
- 📊 **Codebase Insights**: AST analysis, complexity metrics, and architecture pattern detection
- ⚡ **Terminal-Native**: Rich terminal UI with syntax highlighting and interactive displays
- 🔌 **Backend Integration**: Leverages existing sophisticated infrastructure (AST, Neo4j, WebSocket streaming)

## Installation

```bash
# Install from source (development)
cd leanvibe-cli
pip install -e .

# Or install directly
pip install leanvibe-cli
```

## Quick Start

```bash
# Check backend connection and status
leanvibe status

# Start real-time monitoring
leanvibe monitor

# Analyze your codebase
leanvibe analyze --all

# Ask the AI agent questions
leanvibe query "What are the main components of this project?"

# Interactive session with the L3 agent
leanvibe query --interactive
```

## Commands

### `leanvibe status`
Show backend health, connection status, and project information.

```bash
leanvibe status                  # Basic status
leanvibe status --detailed       # Detailed information
leanvibe status --json          # JSON output
```

### `leanvibe monitor`
Real-time file monitoring with event notifications.

```bash
leanvibe monitor                 # Start monitoring
leanvibe monitor -f high         # Filter high-priority events only
leanvibe monitor -t 60           # Monitor for 60 seconds
leanvibe monitor --json          # JSON event stream
```

### `leanvibe analyze`
Trigger AST analysis and display codebase insights.

```bash
leanvibe analyze                 # Project overview
leanvibe analyze --complexity    # Code complexity analysis
leanvibe analyze --architecture  # Architecture patterns
leanvibe analyze --dependencies  # Circular dependency detection
leanvibe analyze --all           # All analysis types
leanvibe analyze -s "MyClass"    # Analyze specific symbol
```

### `leanvibe query`
Natural language interaction with the L3 agent.

```bash
leanvibe query "Find all classes that inherit from BaseClass"
leanvibe query --interactive     # Start interactive session
leanvibe query "/status"         # Execute slash command
leanvibe query --workspace /path/to/project "Analyze this project"
```

## Configuration

LeanVibe CLI uses YAML configuration files:

- Project-specific: `.leanvibe/cli-config.yaml`
- User-wide: `~/.leanvibe/cli-config.yaml`

Example configuration:

```yaml
backend_url: http://localhost:8000
websocket_url: ws://localhost:8000/ws
timeout_seconds: 30
verbose: false
auto_detect_project: true
show_notifications: true
notification_level: medium
max_lines_output: 50
syntax_highlighting: true
show_timestamps: true
compact_mode: false
project_root: /path/to/project
exclude_patterns:
  - "*.pyc"
  - "__pycache__"
  - ".git"
  - "node_modules"
```

## Backend Requirements

LeanVibe CLI requires a running LeanVibe backend service:

```bash
# Start the backend (from leanvibe-backend directory)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The CLI will auto-detect a local backend on `localhost:8000` by default.

## Interactive Mode

Use `leanvibe query --interactive` for a persistent session with the L3 agent:

```
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

## Real-time Monitoring

The monitor command provides live updates of file changes, architectural violations, and system events:

```bash
leanvibe monitor
```

This displays:
- Real-time event stream with filtering
- Connection status and statistics  
- Event priority levels and details
- Recent activity history

## Examples

### Basic Project Analysis
```bash
# Get project overview
leanvibe analyze

# Check for issues
leanvibe analyze --complexity --dependencies

# Monitor for violations
leanvibe monitor -f high
```

### AI-Powered Exploration
```bash
# Ask about code structure
leanvibe query "What design patterns are used in this codebase?"

# Find specific code
leanvibe query "Where is the database connection handled?"

# Get refactoring suggestions
leanvibe query "What can be improved in the authentication module?"
```

### Development Workflow
```bash
# Start monitoring in background
leanvibe monitor &

# Check status periodically
leanvibe status

# Ask questions as you code
leanvibe query "Is this change following the existing patterns?"
```

## Integration

### Environment Variables
- `LEENVIBE_BACKEND_URL`: Override backend URL
- `LEENVIBE_CONFIG_PATH`: Custom config file path

### Project Detection
LeanVibe CLI automatically detects project context by looking for:
- `.leanvibe/` directory
- `.git/` repository
- `pyproject.toml`, `package.json`, etc.

## Development

```bash
# Clone and install in development mode
git clone <repository>
cd leanvibe-cli
pip install -e .

# Run tests
pytest

# Format code
black leanvibe_cli/
isort leanvibe_cli/
```

## Troubleshooting

### Connection Issues
```bash
# Check backend status
leanvibe status

# Verify backend URL
leanvibe status --detailed

# Test with explicit URL
leanvibe --backend-url http://localhost:8000 status
```

### Configuration Issues
```bash
# Check current config
leanvibe --verbose status

# Reset configuration
rm ~/.leanvibe/cli-config.yaml
leanvibe status  # Will recreate with defaults
```

### Performance Issues
```bash
# Check backend performance
leanvibe status --detailed

# Monitor with reduced frequency
leanvibe monitor -f critical
```

## Architecture

LeanVibe CLI is designed as a thin client that leverages the sophisticated backend infrastructure:

- **HTTP Client**: REST API communication for analysis requests
- **WebSocket Client**: Real-time event streaming and L3 agent interaction  
- **Rich Terminal UI**: Modern terminal interface with live updates
- **Configuration Management**: YAML-based settings with auto-detection
- **Error Handling**: Graceful degradation and meaningful error messages

The CLI focuses on user experience while the backend handles all the heavy lifting: AST parsing, graph analysis, ML inference, and real-time monitoring.

## License

MIT License - see LICENSE file for details.