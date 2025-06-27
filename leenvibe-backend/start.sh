#!/bin/bash

# LeenVibe Backend Startup Script with MLX Qwen3-30B-A3B-MLX-4bit Integration

echo "🚀 Starting LeenVibe Backend with Qwen3-30B-A3B-MLX-4bit..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
    echo "✅ uv installed successfully"
fi

# Check if we're on Apple Silicon (required for MLX)
if [[ $(uname -m) != "arm64" ]]; then
    echo "⚠️  Warning: MLX is optimized for Apple Silicon (M1/M2/M3/M4 Macs)"
    echo "   This may not work on Intel Macs or other architectures"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Exiting. Please run on Apple Silicon Mac for optimal performance."
        exit 1
    fi
fi

# Sync dependencies using uv
echo "📚 Syncing dependencies with uv..."
uv sync

# Install MLX dependencies on Apple Silicon
echo "🧠 Installing MLX dependencies for Qwen3-30B-A3B-MLX-4bit..."
uv sync --extra mlx

# Check available memory (30B model needs ~60GB RAM)
echo "💾 Checking system memory for Qwen3-30B model..."
total_memory=$(system_profiler SPHardwareDataType | grep "Memory:" | awk '{print $2 $3}')
echo "   System Memory: $total_memory"

# Extract numeric value for comparison
memory_gb=$(system_profiler SPHardwareDataType | grep "Memory:" | awk '{print $2}' | sed 's/[^0-9]//g')
if [[ $memory_gb -lt 64 ]]; then
    echo "⚠️  Warning: Qwen3-30B-A3B requires ~60GB+ RAM for optimal performance"
    echo "   Your system has ${memory_gb}GB. Consider using a smaller model."
    echo "   Options: Qwen3-7B-A3B-MLX-4bit or Qwen3-14B-A3B-MLX-4bit"
    read -p "Continue with 30B model anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "💡 Tip: Update model_name in qwen_coder_service.py to use a smaller model"
        exit 1
    fi
fi

# Initialize MLX model cache
echo "🗄️  Preparing MLX model cache..."
uv run python -c "
import os
from pathlib import Path

# Create model cache directory
cache_dir = Path.home() / '.cache' / 'leenvibe' / 'models'
cache_dir.mkdir(parents=True, exist_ok=True)
print(f'✅ Model cache directory: {cache_dir}')

# Check for existing model files
model_files = list(cache_dir.glob('*Qwen3*'))
if model_files:
    print(f'📁 Found {len(model_files)} existing model files')
else:
    print('📥 Model will be downloaded on first use')
"

# Print QR code and connection info
echo "🔍 Detecting network configuration..."
uv run python -c "
import sys
sys.path.append('app')
from utils.connection_service import print_startup_qr
print_startup_qr(8000)
"

# Test MLX availability before starting server
echo "🧪 Testing MLX and model service..."
uv run python -c "
try:
    import mlx.core as mx
    import mlx.nn as nn
    print('✅ MLX framework loaded successfully')
    
    # Test basic MLX operations
    x = mx.array([1, 2, 3])
    y = x * 2
    mx.eval(y)
    print('✅ MLX operations working')
    
    # Test model service initialization (without loading full weights)
    import sys
    sys.path.append('app')
    from services.qwen_coder_service import QwenCoderService
    print('✅ Qwen3 service module loaded')
    
except Exception as e:
    print(f'❌ MLX/Model test failed: {e}')
    print('🔧 Check that MLX is properly installed: pip install mlx')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ MLX tests failed. Cannot start server."
    exit 1
fi

echo "🌟 Starting FastAPI server with Qwen3-30B-A3B-MLX-4bit support..."
echo "📱 Scan the QR code above with the LeenVibe iOS app to connect"
echo "🖥️  Or connect manually to: http://localhost:8000"
echo ""
echo "⚡ Model: Qwen3-30B-A3B-MLX-4bit (MLX optimized)"
echo "💾 Expected memory usage: ~60GB during inference"
echo "🎯 First model load may take 5-10 minutes to download"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server using uv
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
