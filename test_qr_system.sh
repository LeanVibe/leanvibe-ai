#!/bin/bash
# LeenVibe QR Connection End-to-End Test Script

echo "🧪 LeenVibe QR Connection System - End-to-End Test"
echo "=================================================="

# Test 1: Backend QR Generation
echo ""
echo "📱 Test 1: Backend QR Code Generation"
echo "-------------------------------------"
cd /Users/bogdan/work/leanvibe-ai/leenvibe-backend

echo "Testing QR code generation..."
QR_OUTPUT=$(uv run python -c "
import sys
sys.path.append('app')
from utils.connection_service import get_connection_qr_data
print(get_connection_qr_data(8000))
" 2>/dev/null)

if [[ $QR_OUTPUT == *"leenvibe"* ]]; then
    echo "✅ QR code generation: PASSED"
    echo "   Generated JSON with leenvibe config"
else
    echo "❌ QR code generation: FAILED"
    echo "   Output: $QR_OUTPUT"
    exit 1
fi

# Test 2: QR JSON Validation
echo ""
echo "🔍 Test 2: QR JSON Format Validation"
echo "-----------------------------------"
VALIDATION_RESULT=$(echo "$QR_OUTPUT" | python3 -c "
import json
import sys
try:
    data = json.load(sys.stdin)
    leenvibe = data['leenvibe']
    server = leenvibe['server']
    required_fields = ['host', 'port', 'websocket_path']
    for field in required_fields:
        if field not in server:
            raise KeyError(f'Missing {field}')
    print('VALID')
except Exception as e:
    print(f'INVALID: {e}')
")

if [[ $VALIDATION_RESULT == "VALID" ]]; then
    echo "✅ QR JSON validation: PASSED"
    echo "   All required fields present"
else
    echo "❌ QR JSON validation: FAILED"
    echo "   Validation result: $VALIDATION_RESULT"
    exit 1
fi

# Test 3: Backend Health Check
echo ""
echo "🏥 Test 3: Backend Health Check"
echo "------------------------------"
echo "Starting backend server for health test..."

# Start backend in background
timeout 10s uv run uvicorn app.main:app --host 0.0.0.0 --port 8002 > /dev/null 2>&1 &
BACKEND_PID=$!
sleep 3

# Test health endpoint
HEALTH_RESPONSE=$(curl -s http://localhost:8002/health 2>/dev/null)

if [[ $HEALTH_RESPONSE == *"healthy"* ]]; then
    echo "✅ Backend health check: PASSED"
    echo "   Health endpoint responding correctly"
else
    echo "❌ Backend health check: FAILED"
    echo "   Health response: $HEALTH_RESPONSE"
fi

# Cleanup backend
kill $BACKEND_PID 2>/dev/null
wait $BACKEND_PID 2>/dev/null

# Test 4: iOS App Build
echo ""
echo "📱 Test 4: iOS App Build Verification"
echo "------------------------------------"
cd /Users/bogdan/work/leanvibe-ai/LeenVibe-iOS-App

echo "Building iOS app..."
BUILD_RESULT=$(xcodebuild -project LeenVibe.xcodeproj -scheme LeenVibe -destination 'platform=iOS Simulator,name=iPhone 15' build -quiet 2>&1)
BUILD_EXIT_CODE=$?

if [[ $BUILD_EXIT_CODE -eq 0 ]]; then
    echo "✅ iOS app build: PASSED"
    echo "   App builds successfully for iOS Simulator"
else
    echo "❌ iOS app build: FAILED"
    echo "   Build errors detected"
    echo "$BUILD_RESULT" | grep -i error | head -5
fi

# Test 5: QR Parsing Logic Test
echo ""
echo "🔍 Test 5: iOS QR Parsing Logic"
echo "------------------------------"
cd /Users/bogdan/work/leanvibe-ai/LeenVibe-iOS-App

PARSING_RESULT=$(swift test_qr_parsing.swift 2>/dev/null)

if [[ $PARSING_RESULT == *"QR Parsing Success"* ]]; then
    echo "✅ QR parsing logic: PASSED"
    echo "   iOS can correctly parse QR code JSON"
else
    echo "❌ QR parsing logic: FAILED"
    echo "   Parsing result: $PARSING_RESULT"
fi

# Summary
echo ""
echo "📊 Test Summary"
echo "==============="

TOTAL_TESTS=5
PASSED_TESTS=0

[[ $QR_OUTPUT == *"leenvibe"* ]] && ((PASSED_TESTS++))
[[ $VALIDATION_RESULT == "VALID" ]] && ((PASSED_TESTS++))
[[ $HEALTH_RESPONSE == *"healthy"* ]] && ((PASSED_TESTS++))
[[ $BUILD_EXIT_CODE -eq 0 ]] && ((PASSED_TESTS++))
[[ $PARSING_RESULT == *"QR Parsing Success"* ]] && ((PASSED_TESTS++))

echo "Tests passed: $PASSED_TESTS/$TOTAL_TESTS"

if [[ $PASSED_TESTS -eq $TOTAL_TESTS ]]; then
    echo "🎉 ALL TESTS PASSED - QR Connection System Ready!"
    echo ""
    echo "🚀 Ready for End-to-End Testing:"
    echo "1. Start backend: cd leenvibe-backend && ./start.sh"
    echo "2. Deploy iOS app to device"
    echo "3. Scan QR code in iOS app"
    echo "4. Enjoy seamless connection!"
else
    echo "⚠️  Some tests failed. Check output above for details."
    exit 1
fi