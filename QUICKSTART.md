# LeanVibe Quick Start Guide

**Get running in 2 minutes** 🚀

## 1. Install (30 seconds)
```bash
./install_simple.sh
```

## 2. Start Backend (10 seconds)
```bash
./start_leanvibe.sh
```

Backend is now running at: http://localhost:8000/docs

## 3. Connect iOS App
1. Open `leanvibe-ios/LeanVibe.xcodeproj` in Xcode
2. Run on simulator or device
3. App will auto-connect to `http://localhost:8000`

## What You Get

✅ **Working Backend** - REST API with WebSocket support  
✅ **iOS App** - Full-featured SwiftUI app  
✅ **CLI Tool** - Command-line interface  
✅ **AI Ready** - Mock AI service (add real models later)  

## Common Commands

### Backend
```bash
# Start backend
./start_leanvibe.sh

# View API docs
open http://localhost:8000/docs

# Check health
curl http://localhost:8000/health
```

### CLI
```bash
cd leanvibe-cli
uv run leanvibe health        # Check system
uv run leanvibe query "test"  # Test AI query
```

### iOS Development
```bash
cd leanvibe-ios
open LeanVibe.xcodeproj      # Open in Xcode
# Press Cmd+R to run
```

## Production Deployment

### 1. Configure
```bash
cp leanvibe-backend/.env.production leanvibe-backend/.env
# Edit .env and set your API key
```

### 2. Deploy
```bash
./deploy/deploy_production.sh
```

## Troubleshooting

### Backend won't start
- Check port 8000 is free: `lsof -i :8000`
- Check Python: `python3 --version` (need 3.8+)

### iOS app can't connect
- Make sure backend is running
- Check firewall allows port 8000
- Try `http://[YOUR-IP]:8000` instead of localhost

### Missing dependencies
```bash
# Reinstall
cd leanvibe-backend
uv sync
```

## Need Help?

- API Docs: http://localhost:8000/docs
- GitHub Issues: [Report problems](https://github.com/leanvibe-ai/issues)
- Logs: Check `leanvibe-backend/backend.log`

---

**That's it!** You're running LeanVibe. 🎉