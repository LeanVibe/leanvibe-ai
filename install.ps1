# LeanVibe MVP Installation Script for Windows
# PowerShell script for automated setup

param(
    [switch]$Help,
    [switch]$Check,
    [switch]$BackendOnly,
    [switch]$CliOnly
)

# Colors for output
$Red = "`e[31m"
$Green = "`e[32m"
$Yellow = "`e[33m"
$Blue = "`e[34m"
$Purple = "`e[35m"
$Cyan = "`e[36m"
$Reset = "`e[0m"

function Write-Banner {
    Write-Host "$Purple" -NoNewline
    Write-Host "  ██╗     ███████╗ █████╗ ███╗   ██╗██╗   ██╗██╗██████╗ ███████╗"
    Write-Host "  ██║     ██╔════╝██╔══██╗████╗  ██║██║   ██║██║██╔══██╗██╔════╝"
    Write-Host "  ██║     █████╗  ███████║██╔██╗ ██║██║   ██║██║██████╔╝█████╗  "
    Write-Host "  ██║     ██╔══╝  ██╔══██║██║╚██╗██║╚██╗ ██╔╝██║██╔══██╗██╔══╝  "
    Write-Host "  ███████╗███████╗██║  ██║██║ ╚████║ ╚████╔╝ ██║██████╔╝███████╗"
    Write-Host "  ╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝  ╚═══╝  ╚═╝╚═════╝ ╚══════╝$Reset"
    Write-Host "$Cyan                    AI-Powered Local-First Development$Reset"
    Write-Host "$Yellow                           MVP Installation$Reset"
    Write-Host ""
}

function Write-Info($message) {
    Write-Host "$Blue[INFO]$Reset $message"
}

function Write-Success($message) {
    Write-Host "$Green[SUCCESS]$Reset $message"
}

function Write-Warning($message) {
    Write-Host "$Yellow[WARNING]$Reset $message"
}

function Write-Error($message) {
    Write-Host "$Red[ERROR]$Reset $message"
}

function Write-Step($message) {
    Write-Host "$Purple[STEP]$Reset $message"
}

function Test-Command($command) {
    try {
        Get-Command $command -ErrorAction Stop | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

function Test-Requirements {
    Write-Step "Checking system requirements..."
    
    Write-Info "Detected OS: Windows"
    
    # Check Python
    if (Test-Command "python") {
        $pythonVersion = (python --version 2>&1).ToString().Split(" ")[1]
        Write-Success "Python found: $pythonVersion"
    }
    elseif (Test-Command "python3") {
        $pythonVersion = (python3 --version 2>&1).ToString().Split(" ")[1]
        Write-Success "Python 3 found: $pythonVersion"
    }
    else {
        Write-Error "Python 3 is required but not found"
        Write-Host "Please install Python 3.8+ from https://python.org and try again"
        exit 1
    }
    
    # Check Git
    if (Test-Command "git") {
        Write-Success "Git found"
    }
    else {
        Write-Error "Git is required but not found"
        Write-Host "Please install Git from https://git-scm.com and try again"
        exit 1
    }
    
    # Check Node.js
    if (Test-Command "node") {
        $nodeVersion = (node --version 2>&1).ToString()
        Write-Success "Node.js found: $nodeVersion"
    }
    else {
        Write-Warning "Node.js not found (optional)"
    }
    
    # Check Ollama
    if (Test-Command "ollama") {
        Write-Success "Ollama found"
    }
    else {
        Write-Warning "Ollama not found - will be installed for AI services"
    }
    
    # Check PowerShell version
    $psVersion = $PSVersionTable.PSVersion.ToString()
    Write-Info "PowerShell version: $psVersion"
    
    if ($PSVersionTable.PSVersion.Major -lt 5) {
        Write-Warning "PowerShell 5.0+ recommended"
    }
}

function Install-Ollama {
    if (Test-Command "ollama") {
        Write-Info "Ollama already installed"
        return
    }
    
    Write-Step "Installing Ollama for AI services..."
    
    try {
        # Download and install Ollama for Windows
        $ollamaUrl = "https://ollama.com/download/OllamaSetup.exe"
        $ollamaInstaller = "$env:TEMP\OllamaSetup.exe"
        
        Write-Info "Downloading Ollama installer..."
        Invoke-WebRequest -Uri $ollamaUrl -OutFile $ollamaInstaller
        
        Write-Info "Running Ollama installer..."
        Start-Process -FilePath $ollamaInstaller -Wait
        
        Write-Success "Ollama installed successfully"
    }
    catch {
        Write-Error "Failed to install Ollama: $_"
        Write-Info "Please install Ollama manually from https://ollama.com"
        exit 1
    }
}

function Setup-PythonEnv {
    Write-Step "Setting up Python environment..."
    
    Set-Location "leanvibe-backend"
    
    # Create virtual environment
    if (-not (Test-Path ".venv")) {
        Write-Info "Creating Python virtual environment..."
        python -m venv .venv
        Write-Success "Virtual environment created"
    }
    else {
        Write-Info "Virtual environment already exists"
    }
    
    # Activate virtual environment
    & ".venv\Scripts\Activate.ps1"
    
    # Upgrade pip
    python -m pip install --upgrade pip
    
    # Install dependencies
    Write-Info "Installing Python dependencies..."
    if (Test-Path "requirements.txt") {
        pip install -r requirements.txt
    }
    else {
        # Install core dependencies if requirements.txt doesn't exist
        pip install fastapi uvicorn websockets pydantic aiofiles httpx rich pyyaml psutil pytest pytest-asyncio
    }
    
    Write-Success "Python dependencies installed"
    Set-Location ".."
}

function Setup-OllamaModels {
    Write-Step "Setting up Ollama AI models..."
    
    # Start Ollama service
    if (-not (Get-Process -Name "ollama" -ErrorAction SilentlyContinue)) {
        Write-Info "Starting Ollama service..."
        Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
        Start-Sleep -Seconds 5
    }
    
    # Pull required models
    Write-Info "Downloading Mistral 7B model (this may take a few minutes)..."
    ollama pull mistral:7b-instruct
    
    Write-Success "AI models ready"
}

function Setup-CLI {
    Write-Step "Setting up LeanVibe CLI..."
    
    Set-Location "leanvibe-cli"
    
    # Install CLI in development mode
    if ((Test-Path "setup.py") -or (Test-Path "pyproject.toml")) {
        pip install -e .
        Write-Success "LeanVibe CLI installed"
    }
    else {
        Write-Warning "CLI setup files not found, skipping CLI installation"
    }
    
    Set-Location ".."
}

function New-Configs {
    Write-Step "Creating configuration files..."
    
    # Backend configuration
    if (-not (Test-Path "leanvibe-backend\.env.example")) {
        $envContent = @"
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
"@
        Set-Content -Path "leanvibe-backend\.env.example" -Value $envContent
        Write-Success "Created .env.example"
    }
    
    # CLI configuration
    $configDir = "$env:USERPROFILE\.leanvibe"
    if (-not (Test-Path $configDir)) {
        New-Item -ItemType Directory -Path $configDir -Force | Out-Null
    }
    
    if (-not (Test-Path "$configDir\config.yaml")) {
        $configContent = @"
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
  file: $env:USERPROFILE\.leanvibe\logs\cli.log
"@
        Set-Content -Path "$configDir\config.yaml" -Value $configContent
        
        $logsDir = "$configDir\logs"
        if (-not (Test-Path $logsDir)) {
            New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
        }
        
        Write-Success "Created CLI configuration"
    }
}

function Test-Health {
    Write-Step "Running health checks..."
    
    # Check Python environment
    Set-Location "leanvibe-backend"
    & ".venv\Scripts\Activate.ps1"
    
    # Test Python imports
    try {
        python -c "
import sys
try:
    import fastapi, uvicorn, pydantic
    print('✅ Core Python dependencies OK')
except ImportError as e:
    print(f'❌ Missing Python dependency: {e}')
    sys.exit(1)
"
        Write-Success "Python dependencies verified"
    }
    catch {
        Write-Error "Python dependency check failed"
        return
    }
    
    # Test Ollama connection
    if (Test-Command "ollama") {
        $models = ollama list 2>&1
        if ($models -match "mistral") {
            Write-Success "Ollama and models ready"
        }
        else {
            Write-Warning "Ollama models may not be fully downloaded"
        }
    }
    
    Set-Location ".."
    
    Write-Success "Health checks completed"
}

function Start-Services {
    Write-Step "Starting LeanVibe services..."
    
    # Start Ollama if not running
    if (-not (Get-Process -Name "ollama" -ErrorAction SilentlyContinue)) {
        Write-Info "Starting Ollama service..."
        Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
        Start-Sleep -Seconds 3
    }
    
    # Backend instructions
    Set-Location "leanvibe-backend"
    
    Write-Info "Starting LeanVibe backend..."
    Write-Host "Backend will be available at: http://localhost:8000"
    Write-Host "API documentation: http://localhost:8000/docs"
    Write-Host ""
    Write-Host "To start the backend manually:"
    Write-Host "  cd leanvibe-backend"
    Write-Host "  .venv\Scripts\Activate.ps1"
    Write-Host "  python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
    Write-Host ""
    
    Set-Location ".."
}

function Write-Usage {
    Write-Host ""
    Write-Host "$Green🎉 LeanVibe installation completed successfully!$Reset"
    Write-Host ""
    Write-Host "$Blue📋 Quick Start Guide:$Reset"
    Write-Host ""
    Write-Host "$Yellow1. Start the backend:$Reset"
    Write-Host "   cd leanvibe-backend"
    Write-Host "   .venv\Scripts\Activate.ps1"
    Write-Host "   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
    Write-Host ""
    Write-Host "$Yellow2. Test the CLI:$Reset"
    Write-Host "   leanvibe health"
    Write-Host "   leanvibe query 'Hello, LeanVibe!'"
    Write-Host ""
    Write-Host "$Blue📚 Documentation:$Reset"
    Write-Host "   • Backend API: http://localhost:8000/docs"
    Write-Host "   • Project README: .\README.md"
    Write-Host "   • User Guide: .\USER_GUIDE.md"
    Write-Host "   • Security Policy: .\SECURITY.md"
    Write-Host ""
    Write-Host "$Blue🔧 Configuration:$Reset"
    Write-Host "   • Backend: leanvibe-backend\.env.example"
    Write-Host "   • CLI: $env:USERPROFILE\.leanvibe\config.yaml"
    Write-Host ""
    Write-Host "$Blue🆘 Support:$Reset"
    Write-Host "   • GitHub: https://github.com/leanvibe-ai"
    Write-Host "   • Issues: https://github.com/leanvibe-ai/leanvibe/issues"
    Write-Host ""
}

function Show-Help {
    Write-Host "LeanVibe Installation Script for Windows"
    Write-Host ""
    Write-Host "Usage: .\install.ps1 [options]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Help          Show this help message"
    Write-Host "  -Check         Run system requirements check only"
    Write-Host "  -BackendOnly   Install backend components only"
    Write-Host "  -CliOnly       Install CLI components only"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\install.ps1                 # Full installation"
    Write-Host "  .\install.ps1 -Check          # Check requirements only"
    Write-Host "  .\install.ps1 -BackendOnly    # Backend only"
    Write-Host ""
}

function Start-Main {
    Write-Banner
    
    Write-Info "Starting LeanVibe MVP installation..."
    Write-Host ""
    
    # Run installation steps
    Test-Requirements
    Install-Ollama
    Setup-PythonEnv
    Setup-OllamaModels
    Setup-CLI
    New-Configs
    Test-Health
    Start-Services
    
    Write-Usage
    
    Write-Success "Installation completed! 🚀"
}

# Handle script parameters
if ($Help) {
    Show-Help
    exit 0
}
elseif ($Check) {
    Write-Banner
    Test-Requirements
    exit 0
}
elseif ($BackendOnly) {
    Write-Banner
    Test-Requirements
    Install-Ollama
    Setup-PythonEnv
    Setup-OllamaModels
    New-Configs
    Test-Health
    Write-Success "Backend installation completed!"
    exit 0
}
elseif ($CliOnly) {
    Write-Banner
    Test-Requirements
    Setup-CLI
    New-Configs
    Write-Success "CLI installation completed!"
    exit 0
}
else {
    Start-Main
}