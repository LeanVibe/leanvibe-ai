#!/bin/bash
cd leanvibe-backend
echo "🚀 Starting LeanVibe..."
echo "📱 Connect iOS app to: http://localhost:8765"
echo "📚 API docs: http://localhost:8765/docs"
echo ""
echo "Press Ctrl+C to stop"
uv run uvicorn app.main:app --host 0.0.0.0 --port 8765 --reload
