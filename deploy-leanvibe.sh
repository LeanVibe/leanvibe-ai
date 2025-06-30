#!/bin/bash
# ==============================================================================
# LeanVibe Production Deployment Script
# ==============================================================================
# Single command to deploy and run LeanVibe on Mac with Qwen3-30B
# 
# Usage: ./deploy-leanvibe.sh [options]
# Options:
#   --model MODEL_NAME    Specify model (default: Qwen/Qwen3-30B-A3B-MLX-4bit)
#   --port PORT          Specify port (default: 8000)
#   --mlx-port PORT      Specify MLX-LM port (default: 8082)
#   --mode MODE          Deployment mode: auto|direct|server|mock (default: auto)
#   --setup-only         Only setup, don't start services
#   --force-reinstall    Force reinstall dependencies
#   --help               Show this help
# ==============================================================================

set -e  # Exit on any error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
BACKEND_DIR="$PROJECT_ROOT/leanvibe-backend"
CACHE_DIR="$HOME/.cache/leanvibe"
LOG_DIR="$HOME/.leanvibe/logs"
CONFIG_FILE="$HOME/.leanvibe/config.yaml"

# Default configuration
MODEL_NAME="Qwen/Qwen3-30B-A3B-MLX-4bit"
LEANVIBE_PORT=8000
MLX_PORT=8082
DEPLOYMENT_MODE="auto"
SETUP_ONLY=false
FORCE_REINSTALL=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_header() {
    echo -e "\n${BLUE}=== $1 ===${NC}"
}

# Help function
show_help() {
    cat << EOF
LeanVibe Production Deployment Script

USAGE:
    ./deploy-leanvibe.sh [OPTIONS]

OPTIONS:
    --model MODEL_NAME      Specify model (default: Qwen/Qwen3-30B-A3B-MLX-4bit)
    --port PORT            Specify LeanVibe port (default: 8000)
    --mlx-port PORT        Specify MLX-LM port (default: 8082)
    --mode MODE            Deployment mode: auto|direct|server|mock (default: auto)
    --setup-only           Only setup, don't start services
    --force-reinstall      Force reinstall dependencies
    --help                 Show this help

EXAMPLES:
    ./deploy-leanvibe.sh                    # Deploy with defaults
    ./deploy-leanvibe.sh --setup-only       # Setup only, no start
    ./deploy-leanvibe.sh --model Qwen/Qwen3-7B-A3B-MLX-4bit  # Use smaller model
    ./deploy-leanvibe.sh --mode direct      # Force direct MLX integration

DEPLOYMENT MODES:
    auto     - Auto-detect best deployment mode
    direct   - Direct MLX-LM integration in process
    server   - Connect to external MLX-LM server
    mock     - Mock mode for development/testing

EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --model)
                MODEL_NAME="$2"
                shift 2
                ;;
            --port)
                LEANVIBE_PORT="$2"
                shift 2
                ;;
            --mlx-port)
                MLX_PORT="$2"
                shift 2
                ;;
            --mode)
                DEPLOYMENT_MODE="$2"
                shift 2
                ;;
            --setup-only)
                SETUP_ONLY=true
                shift
                ;;
            --force-reinstall)
                FORCE_REINSTALL=true
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# System validation
validate_environment() {
    log_header "Environment Validation"
    
    # Check macOS
    if [[ "$(uname)" != "Darwin" ]]; then
        log_error "This script is designed for macOS only"
        exit 1
    fi
    log_success "Running on macOS"
    
    # Check Apple Silicon
    if [[ "$(uname -m)" == "arm64" ]]; then
        log_success "Apple Silicon detected (recommended for MLX)"
    else
        log_warning "Intel Mac detected - MLX performance may be limited"
    fi
    
    # Check available memory
    MEMORY_GB=$(sysctl -n hw.memsize | awk '{print int($1/1024/1024/1024)}')
    log_info "Available memory: ${MEMORY_GB}GB"
    if [[ $MEMORY_GB -lt 32 ]]; then
        log_warning "Less than 32GB RAM - large models may not fit"
    fi
    
    # Check Python
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        log_success "Python 3 found: $PYTHON_VERSION"
    else
        log_error "Python 3 not found. Please install Python 3.11+"
        exit 1
    fi
    
    # Check uv
    if command -v uv &> /dev/null; then
        UV_VERSION=$(uv --version)
        log_success "uv found: $UV_VERSION"
    else
        log_info "Installing uv package manager..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        source "$HOME/.cargo/env" 2>/dev/null || true
        if ! command -v uv &> /dev/null; then
            log_error "Failed to install uv. Please install manually."
            exit 1
        fi
        log_success "uv installed successfully"
    fi
}

# Create directory structure
setup_directories() {
    log_header "Directory Setup"
    
    mkdir -p "$CACHE_DIR/models"
    mkdir -p "$LOG_DIR"
    mkdir -p "$(dirname "$CONFIG_FILE")"
    
    log_success "Created directory structure"
}

# Install dependencies
install_dependencies() {
    log_header "Installing Dependencies"
    
    cd "$BACKEND_DIR"
    
    if [[ $FORCE_REINSTALL == true ]]; then
        log_info "Force reinstalling dependencies..."
        rm -rf .venv uv.lock 2>/dev/null || true
    fi
    
    log_info "Syncing Python dependencies with uv..."
    uv sync
    
    # Try to install MLX-LM (may fail due to sentencepiece issues)
    log_info "Attempting to install MLX-LM..."
    if uv add mlx-lm 2>/dev/null; then
        log_success "MLX-LM installed successfully"
    else
        log_warning "MLX-LM installation failed - will use server mode or mock"
    fi
    
    log_success "Dependencies installed"
}

# Generate configuration
generate_config() {
    log_header "Configuration Generation"
    
    cat > "$CONFIG_FILE" << EOF
# LeanVibe Production Configuration
# Generated: $(date)

model:
  name: "$MODEL_NAME"
  deployment_mode: "$DEPLOYMENT_MODE"
  cache_dir: "$CACHE_DIR"
  max_tokens: 512
  temperature: 0.7

server:
  leanvibe_port: $LEANVIBE_PORT
  mlx_port: $MLX_PORT
  host: "0.0.0.0"

logging:
  level: "INFO"
  log_dir: "$LOG_DIR"
  
monitoring:
  health_check_interval: 30
  restart_threshold: 3
  memory_limit_gb: 64

# Paths
paths:
  project_root: "$PROJECT_ROOT"
  backend_dir: "$BACKEND_DIR"
  cache_dir: "$CACHE_DIR"
  log_dir: "$LOG_DIR"
EOF
    
    log_success "Configuration saved to $CONFIG_FILE"
}

# Health check function
check_service_health() {
    local port=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1
    
    log_info "Checking $service_name health on port $port..."
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
            log_success "$service_name is healthy"
            return 0
        fi
        
        if [[ $attempt -eq 1 ]]; then
            echo -n "Waiting for $service_name"
        fi
        echo -n "."
        
        sleep 2
        ((attempt++))
    done
    
    echo ""
    log_error "$service_name failed to start or become healthy"
    return 1
}

# Start MLX-LM server if needed
start_mlx_server() {
    log_header "MLX-LM Server Management"
    
    # Check if server is already running
    if curl -s "http://localhost:$MLX_PORT/health" > /dev/null 2>&1; then
        log_success "MLX-LM server already running on port $MLX_PORT"
        return 0
    fi
    
    # Try to start MLX-LM server
    if command -v mlx_lm &> /dev/null; then
        log_info "Starting MLX-LM server on port $MLX_PORT..."
        
        # Start in background with logging
        nohup mlx_lm.server \
            --model "$MODEL_NAME" \
            --port "$MLX_PORT" \
            --host "127.0.0.1" \
            > "$LOG_DIR/mlx-server.log" 2>&1 &
        
        echo $! > "$HOME/.leanvibe/mlx-server.pid"
        
        # Wait for server to be ready
        if check_service_health "$MLX_PORT" "MLX-LM server"; then
            log_success "MLX-LM server started successfully"
            return 0
        else
            log_error "MLX-LM server failed to start"
            return 1
        fi
    else
        log_warning "MLX-LM not available - will use direct mode or mock"
        return 1
    fi
}

# Start LeanVibe service
start_leanvibe_service() {
    log_header "LeanVibe Service"
    
    cd "$BACKEND_DIR"
    
    log_info "Starting LeanVibe backend on port $LEANVIBE_PORT..."
    
    # Set environment variables
    export LEANVIBE_MODEL_NAME="$MODEL_NAME"
    export LEANVIBE_DEPLOYMENT_MODE="$DEPLOYMENT_MODE"
    export LEANVIBE_MLX_SERVER_URL="http://127.0.0.1:$MLX_PORT"
    export LEANVIBE_PORT="$LEANVIBE_PORT"
    export LEANVIBE_CACHE_DIR="$CACHE_DIR"
    
    # Start LeanVibe service
    nohup uv run python -m uvicorn app.main:app \
        --host 0.0.0.0 \
        --port "$LEANVIBE_PORT" \
        --reload \
        > "$LOG_DIR/leanvibe.log" 2>&1 &
    
    echo $! > "$HOME/.leanvibe/leanvibe.pid"
    
    # Wait for service to be ready
    if check_service_health "$LEANVIBE_PORT" "LeanVibe service"; then
        log_success "LeanVibe service started successfully"
        return 0
    else
        log_error "LeanVibe service failed to start"
        return 1
    fi
}

# Generate QR code for iOS connection
generate_qr_code() {
    log_header "iOS Connection Setup"
    
    # Get local IP addresses
    LOCAL_IPS=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}')
    
    echo ""
    echo "📱 iOS Connection QR Code will be displayed by LeanVibe server"
    echo "🔗 Connection URLs:"
    
    for ip in $LOCAL_IPS; do
        echo "   ws://$ip:$LEANVIBE_PORT/ws"
    done
    
    echo ""
    echo "💡 Open LeanVibe iOS app and scan the QR code displayed by the server"
}

# Create process management scripts
create_management_scripts() {
    log_header "Process Management Setup"
    
    # Create start script
    cat > "$HOME/.leanvibe/start.sh" << 'EOF'
#!/bin/bash
# Auto-generated LeanVibe start script
source ~/.leanvibe/config.yaml 2>/dev/null || true
exec "$PROJECT_ROOT/deploy-leanvibe.sh" "$@"
EOF
    chmod +x "$HOME/.leanvibe/start.sh"
    
    # Create stop script
    cat > "$HOME/.leanvibe/stop.sh" << EOF
#!/bin/bash
# Auto-generated LeanVibe stop script

echo "Stopping LeanVibe services..."

# Stop LeanVibe service
if [[ -f "$HOME/.leanvibe/leanvibe.pid" ]]; then
    PID=\$(cat "$HOME/.leanvibe/leanvibe.pid")
    if kill "\$PID" 2>/dev/null; then
        echo "✅ LeanVibe service stopped"
    fi
    rm -f "$HOME/.leanvibe/leanvibe.pid"
fi

# Stop MLX-LM server
if [[ -f "$HOME/.leanvibe/mlx-server.pid" ]]; then
    PID=\$(cat "$HOME/.leanvibe/mlx-server.pid")
    if kill "\$PID" 2>/dev/null; then
        echo "✅ MLX-LM server stopped"
    fi
    rm -f "$HOME/.leanvibe/mlx-server.pid"
fi

echo "✅ All services stopped"
EOF
    chmod +x "$HOME/.leanvibe/stop.sh"
    
    # Create status script
    cat > "$HOME/.leanvibe/status.sh" << EOF
#!/bin/bash
# Auto-generated LeanVibe status script

echo "=== LeanVibe Service Status ==="

# Check LeanVibe service
if [[ -f "$HOME/.leanvibe/leanvibe.pid" ]]; then
    PID=\$(cat "$HOME/.leanvibe/leanvibe.pid")
    if kill -0 "\$PID" 2>/dev/null; then
        echo "✅ LeanVibe service: Running (PID: \$PID)"
        curl -s "http://localhost:$LEANVIBE_PORT/health" || echo "❌ Health check failed"
    else
        echo "❌ LeanVibe service: Not running"
    fi
else
    echo "❌ LeanVibe service: Not started"
fi

# Check MLX-LM server
if [[ -f "$HOME/.leanvibe/mlx-server.pid" ]]; then
    PID=\$(cat "$HOME/.leanvibe/mlx-server.pid")
    if kill -0 "\$PID" 2>/dev/null; then
        echo "✅ MLX-LM server: Running (PID: \$PID)"
        curl -s "http://localhost:$MLX_PORT/health" || echo "❌ Health check failed"
    else
        echo "❌ MLX-LM server: Not running"
    fi
else
    echo "❌ MLX-LM server: Not started"
fi

echo ""
echo "Logs available at: $LOG_DIR"
echo "Configuration: $CONFIG_FILE"
EOF
    chmod +x "$HOME/.leanvibe/status.sh"
    
    log_success "Management scripts created in ~/.leanvibe/"
}

# Show final status and instructions
show_completion_status() {
    log_header "Deployment Complete"
    
    echo ""
    echo "🎉 LeanVibe has been deployed successfully!"
    echo ""
    echo "📊 Service Status:"
    echo "   🖥️  LeanVibe Backend: http://localhost:$LEANVIBE_PORT"
    
    if curl -s "http://localhost:$MLX_PORT/health" > /dev/null 2>&1; then
        echo "   🧠 MLX-LM Server: http://localhost:$MLX_PORT"
    fi
    
    echo ""
    echo "📱 iOS App Connection:"
    echo "   Open LeanVibe iOS app and scan the QR code displayed by the server"
    echo ""
    echo "🔧 Management Commands:"
    echo "   Status:  ~/.leanvibe/status.sh"
    echo "   Stop:    ~/.leanvibe/stop.sh"
    echo "   Restart: $0"
    echo ""
    echo "📝 Logs & Config:"
    echo "   Logs:    $LOG_DIR"
    echo "   Config:  $CONFIG_FILE"
    echo ""
    echo "🚀 LeanVibe is ready for use!"
}

# Main deployment flow
main() {
    echo ""
    echo "🚀 LeanVibe Production Deployment"
    echo "=================================="
    echo "Model: $MODEL_NAME"
    echo "Mode:  $DEPLOYMENT_MODE"
    echo "Port:  $LEANVIBE_PORT"
    echo ""
    
    # Stop any existing services
    if [[ -f "$HOME/.leanvibe/stop.sh" ]]; then
        log_info "Stopping existing services..."
        "$HOME/.leanvibe/stop.sh" || true
    fi
    
    # Core setup
    validate_environment
    setup_directories
    install_dependencies
    generate_config
    create_management_scripts
    
    if [[ $SETUP_ONLY == true ]]; then
        log_success "Setup completed. Use '$0' (without --setup-only) to start services."
        exit 0
    fi
    
    # Start services
    if [[ $DEPLOYMENT_MODE == "server" ]] || [[ $DEPLOYMENT_MODE == "auto" ]]; then
        start_mlx_server || log_warning "MLX-LM server not available, will use direct/mock mode"
    fi
    
    start_leanvibe_service
    generate_qr_code
    show_completion_status
    
    echo ""
    echo "Press Ctrl+C to stop services, or run ~/.leanvibe/stop.sh"
    
    # Keep script running to monitor services
    trap 'echo ""; log_info "Stopping services..."; ~/.leanvibe/stop.sh; exit 0' INT
    
    while true; do
        sleep 10
        # Basic health monitoring
        if ! curl -s "http://localhost:$LEANVIBE_PORT/health" > /dev/null 2>&1; then
            log_error "LeanVibe service health check failed"
            break
        fi
    done
}

# Parse arguments and run
parse_args "$@"
main