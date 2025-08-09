#!/bin/bash
# LeanVibe Production Deployment Script
# Simple, pragmatic deployment following XP principles

set -e

# Detect OS
OS="unknown"
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
fi

echo "🚀 LeanVibe Production Deployment"
echo "   OS: $OS"
echo ""

# 1. Check for production config
if [ ! -f "leanvibe-backend/.env" ]; then
    echo "❌ Missing .env file!"
    echo "   Copy .env.production to .env and update values:"
    echo "   cp leanvibe-backend/.env.production leanvibe-backend/.env"
    echo "   vim leanvibe-backend/.env"
    exit 1
fi

# 2. Verify API key is set
if grep -q "change-this" leanvibe-backend/.env; then
    echo "❌ Default API key detected!"
    echo "   Edit .env and set secure LEANVIBE_API_KEY"
    exit 1
fi

# 3. Install dependencies
echo "📦 Installing production dependencies..."
cd leanvibe-backend
if command -v uv &> /dev/null; then
    uv sync --no-dev
else
    pip install -r requirements.txt
fi
cd ..

# 4. Run production checks
echo "🔍 Running production validation..."
cd leanvibe-backend
python -c "
import os
import sys
os.environ['ENVIRONMENT'] = 'production'

# Check API key
api_key = os.environ.get('LEANVIBE_API_KEY', '')
if not api_key or 'change-this' in api_key:
    print('❌ Invalid API key')
    sys.exit(1)

# Check imports
try:
    from app.main import app
    from app.auth.api_key_auth import verify_api_key
    print('✅ Core modules loaded')
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)

print('✅ Production checks passed')
"
cd ..

# 5. Install service based on OS
if [ "$OS" == "linux" ]; then
    echo "🐧 Installing systemd service..."
    sudo cp deploy/leanvibe.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable leanvibe
    echo "✅ Service installed"
    echo ""
    echo "To start:"
    echo "  sudo systemctl start leanvibe"
    echo "To check status:"
    echo "  sudo systemctl status leanvibe"
    echo "To view logs:"
    echo "  sudo journalctl -u leanvibe -f"
    
elif [ "$OS" == "macos" ]; then
    echo "🍎 Installing launchd service..."
    cp deploy/com.leanvibe.backend.plist ~/Library/LaunchAgents/
    launchctl load ~/Library/LaunchAgents/com.leanvibe.backend.plist
    echo "✅ Service installed"
    echo ""
    echo "To start:"
    echo "  launchctl start com.leanvibe.backend"
    echo "To check status:"
    echo "  launchctl list | grep leanvibe"
    echo "To view logs:"
    echo "  tail -f /var/log/leanvibe/backend.log"
    
else
    echo "⚠️ Unknown OS - manual setup required"
    echo ""
    echo "Run directly with:"
    echo "  cd leanvibe-backend"
    echo "  uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4"
fi

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🔒 Security checklist:"
echo "   [ ] API key is unique and secure"
echo "   [ ] CORS origins are restricted"
echo "   [ ] Firewall configured for port 8000"
echo "   [ ] SSL/TLS configured (use nginx/caddy)"
echo "   [ ] Log rotation configured"
echo ""
echo "📊 Monitor at: http://localhost:8000/health"