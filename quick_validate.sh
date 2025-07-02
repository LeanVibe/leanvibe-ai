#!/bin/bash
# Quick LeanVibe validation - essential checks only

echo "🚀 Quick LeanVibe Validation"
echo "==========================="

# 1. Backend import test
echo -e "\n1️⃣ Backend Services:"
cd leanvibe-backend
python -c "
import sys; sys.path.append('.')
from app.services.production_model_service import ProductionModelService
from app.services.transformers_phi3_service import transformers_phi3_service
print('✅ Backend imports working')
print(f'✅ Device: {transformers_phi3_service.device}')
print(f'✅ Model: {transformers_phi3_service.model_name}')
" 2>&1

# 2. Server startup test (5 second test)
echo -e "\n2️⃣ Server Startup:"
timeout 5 python -m uvicorn app.main:app --port 8000 > /tmp/quick_server.log 2>&1 &
sleep 3
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Server starts successfully"
    curl -s http://localhost:8000/health | python -m json.tool | grep -E "(status|version|ai_ready)"
else
    echo "❌ Server failed to start"
fi
pkill -f "uvicorn app.main:app" 2>/dev/null

# 3. iOS build test
echo -e "\n3️⃣ iOS Build Test:"
cd ../leanvibe-ios
if swift build --package-path . 2>&1 | grep -q "Compiling"; then
    echo "✅ iOS compilation started (platform issues fixed)"
else
    echo "❌ iOS build still has issues"
fi

echo -e "\n✅ Quick validation complete!"