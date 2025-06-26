#!/bin/bash

# LeenVibe Backend Startup Script

echo "🚀 Starting LeenVibe Backend..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
    echo "✅ uv installed successfully"
fi

# Sync dependencies using uv
echo "📚 Syncing dependencies with uv..."
uv sync

# Install optional MLX dependencies on Apple Silicon
if [[ $(uname -m) == "arm64" ]]; then
    echo "🧠 Installing MLX dependencies for Apple Silicon..."
    uv sync --extra mlx
fi

# Start the server using uv
echo "🌟 Starting FastAPI server..."
echo "Backend will be available at: http://localhost:8000"
echo "WebSocket endpoint: ws://localhost:8000/ws/{client_id}"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload