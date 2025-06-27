#!/bin/bash

# LeenVibe Backend Startup Script with QR Code Connection

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

# Print QR code and connection info
echo "🔍 Detecting network configuration..."
uv run python -c "
import sys
sys.path.append('app')
from utils.connection_service import print_startup_qr
print_startup_qr(8000)
"

# Start the server using uv
echo "🌟 Starting FastAPI server..."
echo "Press Ctrl+C to stop the server"
echo ""

uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
