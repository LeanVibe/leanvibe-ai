#!/bin/bash

# LeanVibe MVP Installation Script
# Automated setup for LeanVibe backend, CLI, and iOS development environment

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ASCII Art Banner
print_banner() {
    echo -e "${PURPLE}"
    echo "  ██╗     ███████╗ █████╗ ███╗   ██╗██╗   ██╗██╗██████╗ ███████╗"
    echo "  ██║     ██╔════╝██╔══██╗████╗  ██║██║   ██║██║██╔══██╗██╔════╝"
    echo "  ██║     █████╗  ███████║██╔██╗ ██║██║   ██║██║██████╔╝█████╗  "
    echo "  ██║     ██╔══╝  ██╔══██║██║╚██╗██║╚██╗ ██╔╝██║██╔══██╗██╔══╝  "
    echo "  ███████╗███████╗██║  ██║██║ ╚████║ ╚████╔╝ ██║██████╔╝███████╗"
    echo "  ╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝  ╚═══╝  ╚═╝╚═════╝ ╚══════╝"
    echo -e "${NC}"
    echo -e "${CYAN}                    AI-Powered Local-First Development${NC}"
    echo -e "${YELLOW}                           MVP Installation${NC}"
    echo ""
}

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

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Get OS information
get_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    else
        echo "unknown"
    fi
}

# Check system requirements
check_requirements() {
    log_step "Checking system requirements..."
    
    local os=$(get_os)
    log_info "Detected OS: $os"
    
    # Check Python
    if command_exists python3; then
        local python_version=$(python3 --version | cut -d' ' -f2)
        log_success "Python 3 found: $python_version"
    else
        log_error "Python 3 is required but not found"
        echo "Please install Python 3.8+ and try again"
        exit 1
    fi
    
    # Check Node.js (for iOS development)
    if command_exists node; then
        local node_version=$(node --version)
        log_success "Node.js found: $node_version"
    else
        log_warning "Node.js not found (optional for iOS development)"
    fi
    
    # Check git
    if command_exists git; then
        log_success "Git found"
    else
        log_error "Git is required but not found"
        exit 1
    fi
    
    # Check Ollama for AI services
    if command_exists ollama; then
        log_success "Ollama found"
    else
        log_warning "Ollama not found - will be installed for AI services"
    fi
    
    # macOS specific checks
    if [[ "$os" == "macos" ]]; then
        if command_exists xcode-select; then
            log_success "Xcode command line tools found"
        else
            log_warning "Xcode command line tools not found (required for iOS development)"
        fi
        
        if command_exists brew; then
            log_success "Homebrew found"
        else
            log_warning "Homebrew not found (recommended for macOS)"
        fi
    fi
}

# Install Ollama if not present
install_ollama() {
    if command_exists ollama; then
        log_info "Ollama already installed"
        return
    fi
    
    log_step "Installing Ollama for AI services..."
    
    local os=$(get_os)
    if [[ "$os" == "macos" ]]; then
        if command_exists brew; then
            brew install ollama
        else
            curl -fsSL https://ollama.com/install.sh | sh
        fi
    elif [[ "$os" == "linux" ]]; then
        curl -fsSL https://ollama.com/install.sh | sh
    else
        log_error "Unsupported OS for automatic Ollama installation"
        echo "Please install Ollama manually from https://ollama.com"
        exit 1
    fi
    
    log_success "Ollama installed successfully"
}

# Setup Python virtual environment
setup_python_env() {
    log_step "Setting up Python environment..."
    
    cd leanvibe-backend
    
    # Create virtual environment
    if [[ ! -d ".venv" ]]; then
        log_info "Creating Python virtual environment..."
        python3 -m venv .venv
        log_success "Virtual environment created"
    else
        log_info "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source .venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install dependencies
    log_info "Installing Python dependencies..."
    if [[ -f "requirements.txt" ]]; then
        pip install -r requirements.txt
    else
        # Install core dependencies if requirements.txt doesn't exist
        pip install fastapi uvicorn websockets pydantic aiofiles httpx rich pyyaml psutil pytest pytest-asyncio
    fi
    
    log_success "Python dependencies installed"
    cd ..
}

# Setup Ollama models
setup_ollama_models() {
    log_step "Setting up Ollama AI models..."
    
    # Start Ollama service
    if ! pgrep -f ollama >/dev/null; then
        log_info "Starting Ollama service..."
        ollama serve &
        sleep 5
    fi
    
    # Pull required models
    log_info "Downloading Mistral 7B model (this may take a few minutes)..."
    ollama pull mistral:7b-instruct
    
    log_success "AI models ready"
}

# Setup CLI
setup_cli() {
    log_step "Setting up LeanVibe CLI..."
    
    cd leanvibe-cli
    
    # Install CLI in development mode
    if [[ -f "setup.py" ]] || [[ -f "pyproject.toml" ]]; then
        pip install -e .
        log_success "LeanVibe CLI installed"
    else
        log_warning "CLI setup files not found, skipping CLI installation"
    fi
    
    cd ..
}

# Setup iOS development (macOS only)
setup_ios() {
    local os=$(get_os)
    if [[ "$os" != "macos" ]]; then
        log_info "iOS setup skipped (macOS required)"
        return
    fi
    
    log_step "Setting up iOS development environment..."
    
    # Check Xcode
    if ! command_exists xcode-select; then
        log_warning "Xcode command line tools not found"
        echo "Please install Xcode from the App Store and run:"
        echo "  xcode-select --install"
        return
    fi
    
    cd leanvibe-ios
    
    # Check if this is an Xcode project
    if [[ -f "LeanVibe.xcodeproj/project.pbxproj" ]] || [[ -f "*.xcworkspace" ]]; then
        log_success "iOS project structure detected"
        log_info "To open in Xcode: open LeanVibe.xcodeproj"
    else
        log_warning "iOS project files not found"
    fi
    
    cd ..
}

# Create configuration files
create_configs() {
    log_step "Creating configuration files..."
    
    # Backend configuration
    if [[ ! -f "leanvibe-backend/.env.example" ]]; then
        cat > leanvibe-backend/.env.example << EOF
# LeanVibe Backend Configuration
OLLAMA_HOST=localhost
OLLAMA_PORT=11434
BACKEND_HOST=localhost
BACKEND_PORT=8000
LOG_LEVEL=INFO
ENVIRONMENT=development

# AI Model Settings
DEFAULT_MODEL=mistral:7b-instruct
MAX_TOKENS=1000
TEMPERATURE=0.1

# Security Settings (change in production)
SECRET_KEY=your-secret-key-here
API_KEY=your-api-key-here
EOF
        log_success "Created .env.example"
    fi
    
    # CLI configuration
    mkdir -p ~/.leanvibe
    if [[ ! -f ~/.leanvibe/config.yaml ]]; then
        cat > ~/.leanvibe/config.yaml << EOF
# LeanVibe CLI Configuration
backend:
  host: localhost
  port: 8000
  timeout: 30

ai:
  model: mistral:7b-instruct
  temperature: 0.1
  max_tokens: 1000

logging:
  level: INFO
  file: ~/.leanvibe/logs/cli.log
EOF
        mkdir -p ~/.leanvibe/logs
        log_success "Created CLI configuration"
    fi
}

# Run health checks
run_health_checks() {
    log_step "Running health checks..."
    
    # Check Python environment
    cd leanvibe-backend
    source .venv/bin/activate
    
    # Test Python imports
    python -c "
import sys
try:
    import fastapi, uvicorn, pydantic
    print('✅ Core Python dependencies OK')
except ImportError as e:
    print(f'❌ Missing Python dependency: {e}')
    sys.exit(1)
" || return 1
    
    # Test Ollama connection
    if command_exists ollama; then
        if ollama list | grep -q mistral; then
            log_success "Ollama and models ready"
        else
            log_warning "Ollama models may not be fully downloaded"
        fi
    fi
    
    cd ..
    
    log_success "Health checks completed"
}

# Start services
start_services() {
    log_step "Starting LeanVibe services..."
    
    # Start Ollama if not running
    if ! pgrep -f ollama >/dev/null; then
        log_info "Starting Ollama service..."
        ollama serve &
        sleep 3
    fi
    
    # Start backend
    cd leanvibe-backend
    source .venv/bin/activate
    
    log_info "Starting LeanVibe backend..."
    echo "Backend will be available at: http://localhost:8000"
    echo "API documentation: http://localhost:8000/docs"
    echo ""
    echo "To start the backend manually:"
    echo "  cd leanvibe-backend"
    echo "  source .venv/bin/activate"
    echo "  python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
    echo ""
    
    # Don't actually start here to avoid blocking the install script
    cd ..
}

# Print usage instructions
print_usage() {
    echo ""
    echo -e "${GREEN}🎉 LeanVibe installation completed successfully!${NC}"
    echo ""
    echo -e "${BLUE}📋 Quick Start Guide:${NC}"
    echo ""
    echo -e "${YELLOW}1. Start the backend:${NC}"
    echo "   cd leanvibe-backend"
    echo "   source .venv/bin/activate"
    echo "   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
    echo ""
    echo -e "${YELLOW}2. Test the CLI:${NC}"
    echo "   leanvibe health"
    echo "   leanvibe query 'Hello, LeanVibe!'"
    echo ""
    echo -e "${YELLOW}3. Open iOS project (macOS):${NC}"
    echo "   cd leanvibe-ios"
    echo "   open LeanVibe.xcodeproj"
    echo ""
    echo -e "${BLUE}📚 Documentation:${NC}"
    echo "   • Backend API: http://localhost:8000/docs"
    echo "   • Project README: ./README.md"
    echo "   • User Guide: ./USER_GUIDE.md"
    echo "   • Security Policy: ./SECURITY.md"
    echo ""
    echo -e "${BLUE}🔧 Configuration:${NC}"
    echo "   • Backend: leanvibe-backend/.env.example"
    echo "   • CLI: ~/.leanvibe/config.yaml"
    echo ""
    echo -e "${BLUE}🆘 Support:${NC}"
    echo "   • GitHub: https://github.com/leanvibe-ai"
    echo "   • Issues: https://github.com/leanvibe-ai/leanvibe/issues"
    echo ""
}

# Main installation process
main() {
    print_banner
    
    log_info "Starting LeanVibe MVP installation..."
    echo ""
    
    # Run installation steps
    check_requirements
    install_ollama
    setup_python_env
    setup_ollama_models
    setup_cli
    setup_ios
    create_configs
    run_health_checks
    start_services
    
    print_usage
    
    log_success "Installation completed! 🚀"
}

# Handle script arguments
case "${1:-}" in
    --help|-h)
        echo "LeanVibe Installation Script"
        echo ""
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --check        Run system requirements check only"
        echo "  --backend-only Install backend components only"
        echo "  --cli-only     Install CLI components only"
        echo ""
        exit 0
        ;;
    --check)
        print_banner
        check_requirements
        exit 0
        ;;
    --backend-only)
        print_banner
        check_requirements
        install_ollama
        setup_python_env
        setup_ollama_models
        create_configs
        run_health_checks
        log_success "Backend installation completed!"
        exit 0
        ;;
    --cli-only)
        print_banner
        check_requirements
        setup_cli
        create_configs
        log_success "CLI installation completed!"
        exit 0
        ;;
    *)
        main
        ;;
esac