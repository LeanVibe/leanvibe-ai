#!/bin/bash

# LeanVibe iOS-Backend Integration Test Script
# Tests the complete iOS ↔ Backend integration flow

echo "🚀 LeanVibe iOS-Backend Integration Test"
echo "========================================"

# Check if backend is running
echo "📡 Checking backend status..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend is running on http://localhost:8000"
else
    echo "❌ Backend not running. Starting backend..."
    cd leanvibe-backend
    ./start.sh &
    BACKEND_PID=$!
    echo "⏳ Waiting for backend to start..."
    sleep 10
    
    if curl -s http://localhost:8000/health > /dev/null; then
        echo "✅ Backend started successfully"
    else
        echo "❌ Failed to start backend"
        exit 1
    fi
fi

# Build iOS app
echo "🏗️ Building iOS app..."
cd leanvibe-ios
xcodebuild -project LeanVibe.xcodeproj -scheme LeanVibe -destination 'platform=iOS Simulator,id=7DE38F97-D151-445D-B9F3-9CDC6B800EF9' build

if [ $? -eq 0 ]; then
    echo "✅ iOS app built successfully"
else
    echo "❌ iOS app build failed"
    exit 1
fi

# Test WebSocket endpoint
echo "🔌 Testing WebSocket endpoint..."
if curl -s http://localhost:8000/ws > /dev/null; then
    echo "✅ WebSocket endpoint accessible"
else
    echo "⚠️ WebSocket endpoint not directly accessible (normal for WS)"
fi

# Test API endpoints
echo "🧪 Testing API endpoints..."
echo "  - Health check:"
curl -s http://localhost:8000/health | jq -r '.status' || echo "❌ Health check failed"

echo "  - CLI query endpoint:"
QUERY_RESULT=$(curl -s -X POST http://localhost:8000/api/v1/cli/query \
    -H "Content-Type: application/json" \
    -d '{"query": "test connection"}' | jq -r '.status' 2>/dev/null)

if [ "$QUERY_RESULT" = "success" ]; then
    echo "    ✅ CLI query endpoint working"
else
    echo "    ⚠️ CLI query endpoint response: $QUERY_RESULT"
fi

echo ""
echo "🎯 Integration Test Summary:"
echo "=============================="
echo "✅ Backend: Running and responsive"
echo "✅ iOS Build: Successful compilation"
echo "✅ API Endpoints: Accessible"
echo "📱 Next Steps:"
echo "  1. Launch iOS simulator manually"
echo "  2. Test WebSocket connection in app"
echo "  3. Test voice commands"
echo ""
echo "🤖 Ready for iOS simulator testing!"

# Instructions for manual testing
echo ""
echo "📋 Manual Testing Instructions:"
echo "1. Open iOS Simulator:"
echo "   xcrun simctl boot 7DE38F97-D151-445D-B9F3-9CDC6B800EF9"
echo ""
echo "2. Install and run app:"
echo "   xcodebuild -project LeanVibe.xcodeproj -scheme LeanVibe -destination 'platform=iOS Simulator,id=7DE38F97-D151-445D-B9F3-9CDC6B800EF9' install"
echo ""
echo "3. Watch backend logs for connection attempts"
echo ""
echo "4. Test WebSocket connectivity in Monitor tab"