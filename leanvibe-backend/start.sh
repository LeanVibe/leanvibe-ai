#!/bin/bash

# LeanVibe Backend Startup Script with MLX AI Integration and Docker Services

echo "🚀 Starting LeanVibe Backend with MLX AI Support..."

# Function to check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        echo "❌ Docker is not running. Please start Docker first."
        exit 1
    fi
}

# Function to start external services
start_services() {
    echo "🐳 Starting external services with Docker Compose..."
    
    # Save current directory and navigate to project root where docker-compose.yml is located
    BACKEND_DIR="$(cd "$(dirname "$0")" && pwd)"
    cd "$(dirname "$0")/.."
    
    # Check if Docker Compose file exists
    if [ ! -f "docker-compose.yml" ]; then
        echo "❌ docker-compose.yml not found in project root"
        exit 1
    fi
    
    # Start services in background
    docker-compose up -d neo4j chroma redis
    
    # Wait for services to be ready
    echo "⏳ Waiting for services to be ready..."
    
    # Wait for Neo4j
    echo "   Checking Neo4j..."
    timeout=60
    while [ $timeout -gt 0 ]; do
        if curl -f http://localhost:7474 >/dev/null 2>&1; then
            echo "   ✅ Neo4j is ready"
            break
        fi
        sleep 2
        timeout=$((timeout-2))
    done
    
    # Wait for Chroma
    echo "   Checking Chroma..."
    timeout=30
    while [ $timeout -gt 0 ]; do
        # Check if Chroma responds (even with deprecation message means it's running)
        if curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/api/v1/collections | grep -E "(200|410)" >/dev/null 2>&1; then
            echo "   ✅ Chroma is ready"
            break
        fi
        sleep 2
        timeout=$((timeout-2))
    done
    
    # Wait for Redis
    echo "   Checking Redis..."
    timeout=60
    while [ $timeout -gt 0 ]; do
        if redis-cli -p 6379 ping >/dev/null 2>&1 || docker exec leanvibe-redis redis-cli ping >/dev/null 2>&1; then
            echo "   ✅ Redis is ready"
            break
        fi
        sleep 2
        timeout=$((timeout-2))
    done
    
    echo "🎉 All services are ready!"
    
    # Return to backend directory
    cd "$BACKEND_DIR"
}

# Check if --skip-services flag is provided
SKIP_SERVICES=false
for arg in "$@"; do
    if [ "$arg" = "--skip-services" ]; then
        SKIP_SERVICES=true
        break
    fi
done

# Start Docker services unless skipped
if [ "$SKIP_SERVICES" = false ]; then
    check_docker
    start_services
fi

# Ensure we're in the backend directory for dependency management
BACKEND_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$BACKEND_DIR"

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
cache_dir = Path.home() / '.cache' / 'leanvibe'
cache_dir.mkdir(parents=True, exist_ok=True)
print(f'✅ Cache directory ready: {cache_dir}')
"

# Print QR code and connection info
echo "🔍 Detecting network configuration..."
uv run python -c "
import sys
import os
sys.path.insert(0, os.path.join(os.getcwd(), 'app'))
try:
    from utils.connection_service import print_startup_qr
    print_startup_qr(8000)
except ImportError as e:
    print(f'⚠️  QR code service not available: {e}')
    print('📱 Backend will start on: http://localhost:8000')
"

# Test MLX availability before starting server
echo "🧪 Testing MLX and model service..."
uv run python -c "
import sys
import os
sys.path.insert(0, os.path.join(os.getcwd(), 'app'))

try:
    import mlx.core as mx
    import mlx.nn as nn
    print('✅ MLX framework loaded successfully')
    
    # Test basic MLX operations
    x = mx.array([1, 2, 3])
    y = x * 2
    mx.eval(y)
    print('✅ MLX operations working')
    
    # Check which services are available
    try:
        from services.simple_model_service import SimpleModelService
        print('✅ SimpleModelService available (lightweight MLX inference)')
    except Exception as e:
        print(f'⚠️  SimpleModelService not available: {e}')
    
    try:
        from services.phi3_mini_service import Phi3MiniService, HF_AVAILABLE
        if HF_AVAILABLE:
            print('✅ Phi-3-Mini service with full transformers support')
        else:
            print('⚠️  Phi-3-Mini service loaded but transformers not available')
    except Exception as e:
        print(f'⚠️  Phi-3-Mini service not available: {e}')
    
    try:
        # Show which inference mode will be used
        from services.real_mlx_service import RealMLXService
        service = RealMLXService()
        print('')
        print('🚀 MLX inference priority: Phi-3-Mini -> SimpleModelService -> Mock')
        print('   Phi-3-Mini provides high-quality AI responses with MLX optimization')
    except Exception as e:
        print(f'⚠️  RealMLXService not available: {e}')
        print('✅ MLX core functionality working, services will initialize during startup')
    
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
echo "📱 Scan the QR code above with the LeanVibe iOS app to connect"
echo "🖥️  Or connect manually to: http://localhost:8000"
echo ""
echo "🐳 External Services:"
echo "   Neo4j:  http://localhost:7474 (neo4j/password123)"
echo "   Chroma: http://localhost:8001"
echo "   Redis:  localhost:6379"
echo ""
echo "⚡ AI Mode: Phi-3-Mini with MLX acceleration (fallback chain available)"
echo "💾 Expected memory usage: ~8GB for Phi-3-Mini, <1GB for fallback"
echo "🎯 High-quality AI responses with real MLX optimization"
echo "🚀 Model downloads on first use - then cached locally"
echo ""
echo "💡 Use --skip-services flag to start without Docker services"
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server using uv
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
