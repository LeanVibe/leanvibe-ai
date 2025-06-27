#!/bin/bash

# LeenVibe Backend Startup Script with MLX Phi-3-Mini-128K-Instruct Integration

echo "🚀 Starting LeenVibe Backend with Phi-3-Mini-128K-Instruct..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
    echo "✅ uv installed successfully"
fi

# Check if we're on Apple Silicon (required for optimal MLX performance)
if [[ $(uname -m) != "arm64" ]]; then
    echo "⚠️  Notice: MLX is optimized for Apple Silicon (M1/M2/M3/M4 Macs)"
    echo "   Intel Macs and other architectures will use CPU fallback"
    echo "   Performance may be reduced but functionality remains intact"
fi

# Sync dependencies using uv
echo "📚 Syncing dependencies with uv..."
uv sync

# Install MLX dependencies
echo "🧠 Installing MLX dependencies for Phi-3-Mini..."
uv sync --extra mlx

# Check available memory (Phi-3-Mini needs ~8GB RAM)
echo "💾 Checking system memory for Phi-3-Mini model..."
total_memory=$(system_profiler SPHardwareDataType | grep "Memory:" | awk '{print $2 $3}')
echo "   System Memory: $total_memory"

# Extract numeric value for comparison
memory_gb=$(system_profiler SPHardwareDataType | grep "Memory:" | awk '{print $2}' | sed 's/[^0-9]//g')
if [[ $memory_gb -lt 16 ]]; then
    echo "⚠️  Warning: Phi-3-Mini works best with 16GB+ RAM for optimal performance"
    echo "   Your system has ${memory_gb}GB. Model will still work but may be slower."
    echo "   Consider closing other applications for better performance."
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
model_files = list(cache_dir.glob('*Phi-3*'))
if model_files:
    print(f'📁 Found {len(model_files)} existing model files')
else:
    print('📥 Model will be downloaded on first use (~7GB download)')
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
    from services.phi3_mini_service import Phi3MiniService
    print('✅ Phi-3-Mini service module loaded')
    
except Exception as e:
    print(f'❌ MLX/Model test failed: {e}')
    print('🔧 Check that MLX is properly installed: pip install mlx')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ MLX tests failed. Cannot start server."
    exit 1
fi

echo "🌟 Starting FastAPI server with Phi-3-Mini-128K-Instruct support..."
echo "📱 Scan the QR code above with the LeenVibe iOS app to connect"
echo "🖥️  Or connect manually to: http://localhost:8000"
echo ""
echo "⚡ Model: Phi-3-Mini-128K-Instruct (Microsoft, MLX optimized)"
echo "💾 Expected memory usage: ~8GB during inference"
echo "🎯 First model load may take 2-5 minutes to download (~7GB)"
echo "🚀 Much faster and lighter than 30B models - perfect for MVP!"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server using uv
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
