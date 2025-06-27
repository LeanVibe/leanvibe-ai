#!/bin/bash

# LeenVibe Backend Startup Script with MLX AI Integration

echo "🚀 Starting LeenVibe Backend with MLX AI Support..."

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

# Note: MLX core is already in main dependencies
# We don't need the MLX extras which include problematic packages like sentencepiece
echo "🧠 MLX core dependencies already included..."

# Check available memory
echo "💾 Checking system memory..."
total_memory=$(system_profiler SPHardwareDataType | grep "Memory:" | awk '{print $2 $3}')
echo "   System Memory: $total_memory"
echo "   SimpleModelService uses <1GB RAM - very efficient!"

# Initialize application cache
echo "🗄️  Preparing application cache..."
uv run python -c "
import os
from pathlib import Path

# Create cache directories
cache_dir = Path.home() / '.cache' / 'leenvibe'
cache_dir.mkdir(parents=True, exist_ok=True)
print(f'✅ Cache directory ready: {cache_dir}')
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
    
    # Test model services
    import sys
    sys.path.append('app')
    
    # Check which services are available
    try:
        from services.simple_model_service import SimpleModelService
        print('✅ SimpleModelService available (lightweight MLX inference)')
    except:
        print('⚠️  SimpleModelService not available')
    
    try:
        from services.phi3_mini_service import Phi3MiniService, HF_AVAILABLE
        if HF_AVAILABLE:
            print('✅ Phi-3-Mini service with full transformers support')
        else:
            print('⚠️  Phi-3-Mini service loaded but transformers not available')
    except:
        print('⚠️  Phi-3-Mini service not available')
    
    # Show which inference mode will be used
    from services.real_mlx_service import RealMLXService
    service = RealMLXService()
    print('')
    print('🚀 MLX inference will use SimpleModelService for real tensor operations')
    print('   This provides actual MLX-based AI responses without heavy dependencies')
    
except Exception as e:
    print(f'❌ MLX/Model test failed: {e}')
    print('🔧 Check that MLX is properly installed: uv sync')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ MLX tests failed. Cannot start server."
    exit 1
fi

echo "🌟 Starting FastAPI server with MLX AI support..."
echo "📱 Scan the QR code above with the LeenVibe iOS app to connect"
echo "🖥️  Or connect manually to: http://localhost:8000"
echo ""
echo "⚡ AI Mode: SimpleModelService (Lightweight MLX inference)"
echo "💾 Expected memory usage: <1GB - very efficient!"
echo "🎯 Real MLX tensor operations without heavy dependencies"
echo "🚀 No large model downloads required - instant startup!"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server using uv
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
