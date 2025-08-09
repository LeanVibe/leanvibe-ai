#!/bin/bash
# LeanVibe Simple Installation - XP Approach
# Goal: Get developers running in < 2 minutes

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "🚀 LeanVibe Quick Install (< 2 minutes)"
echo ""

# 1. Check Python (most important)
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 required. Install from python.org${NC}"
    exit 1
fi
echo "✅ Python found"

# 2. Install uv if needed (modern Python package manager)
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi
echo "✅ Package manager ready"

# 3. Install backend dependencies
echo "📚 Installing backend (30 seconds)..."
cd leanvibe-backend
uv sync --quiet
cd ..

# 4. Install CLI
echo "🔧 Installing CLI tool..."
cd leanvibe-cli
uv sync --quiet
cd ..

# 5. Create minimal config
echo "⚙️ Creating config..."
mkdir -p ~/.leanvibe
if [ ! -f ~/.leanvibe/config.yaml ]; then
    cat > ~/.leanvibe/config.yaml << EOF
backend:
  host: localhost
  port: 8000
EOF
fi

# 6. Create start script
cat > start_leanvibe.sh << 'EOF'
#!/bin/bash
cd leanvibe-backend
echo "🚀 Starting LeanVibe..."
echo "📱 Connect iOS app to: http://localhost:8000"
echo "📚 API docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
EOF
chmod +x start_leanvibe.sh

# 7. Done!
echo ""
echo -e "${GREEN}✅ Installation complete!${NC}"
echo ""
echo "To start LeanVibe:"
echo "  ./start_leanvibe.sh"
echo ""
echo "To use CLI:"
echo "  cd leanvibe-cli && uv run leanvibe --help"
echo ""
echo "API will be at: http://localhost:8000/docs"