# LeenVibe Vertical Slice Setup Guide

This guide will help you set up and run the LeenVibe L3 Coding Agent vertical slice in under 30 minutes. Perfect for junior engineers or anyone wanting to test the system.

## 🎯 What You'll Build

By the end of this guide, you'll have:
- A local AI agent running on your Mac
- An iOS app that communicates with the agent
- Real-time command execution and responses
- A working demonstration of the core LeenVibe concept

## 📋 Prerequisites

### Hardware Requirements
- Mac with Apple Silicon (M1/M2/M3) or Intel Mac
- 8GB+ RAM (16GB+ recommended)
- iPhone or iPad with iOS 16.0+ (or iOS Simulator)

### Software Requirements
- macOS 13.0+ (Ventura)
- Python 3.11+ 
- Xcode 15+
- Terminal access

### Check Your Setup
```bash
# Verify Python version
python3 --version  # Should be 3.11+

# Verify Xcode installation
xcodebuild -version  # Should be 15.0+

# Check available RAM
system_profiler SPHardwareDataType | grep Memory
```

## 🚀 Part 1: Backend Setup (5 minutes)

### Step 1: Clone and Navigate
```bash
# Navigate to the project directory (adjust path as needed)
cd /path/to/leanvibe-ai

# Verify backend files exist
ls leenvibe-backend/
# Should see: app/ pyproject.toml start.sh README.md tests/
```

### Step 2: Quick Start Script
```bash
cd leenvibe-backend

# Make startup script executable
chmod +x start.sh

# Run the startup script (this will take 1-2 minutes)
./start.sh
```

The script will:
1. Install uv package manager (if needed)
2. Sync all dependencies using uv
3. Install MLX dependencies on Apple Silicon
4. Start the FastAPI server
5. Show you the connection URLs

### Step 3: Verify Backend is Running
Open a new terminal window and test:
```bash
# Test health endpoint
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","service":"leenvibe-backend","ai_ready":true}
```

If you see this response, your backend is ready! 🎉

### Step 4: Test WebSocket (Optional)
```bash
# Install wscat for WebSocket testing (if you have Node.js)
npm install -g wscat

# Test WebSocket connection
wscat -c ws://localhost:8000/ws/test

# Send a test command (type this after connecting):
{"type":"command","content":"/status"}

# You should see a JSON response with agent status
```

## 📱 Part 2: iOS App Setup (10 minutes)

Choose one of these options:

### Option A: Swift Package Manager (Recommended)

1. **Navigate to Swift Package**:
   ```bash
   cd LeenVibe-SwiftPM
   ```

2. **Open in Xcode**:
   ```bash
   open Package.swift
   ```

3. **Build and Run**:
   - Select iOS Simulator as target
   - Press **Cmd+R** to build and run
   - The app will launch automatically

### Option B: Traditional iOS Project

1. **Open Xcode**:
   - Launch Xcode
   - Select "Create a new Xcode project"
   - Choose **iOS** → **App**
   - Configure your project:
     - Product Name: `LeenVibe`
     - Interface: **SwiftUI**
     - Language: **Swift**
     - Minimum Deployment: **iOS 16.0**

2. **Add Package Dependency**:
   - File → Add Package Dependencies
   - Enter local path: `/path/to/LeenVibe-SwiftPM`
   - Click "Add Package"

3. **Update App Entry Point**:
   ```swift
   import SwiftUI
   import LeenVibe

   @main
   struct MyLeenVibeApp: App {
       var body: some Scene {
           WindowGroup {
               ContentView()
           }
       }
   }
   ```

### Step 3: Build and Run
1. Select your target device (iPhone Simulator or physical device)
2. Press **Cmd+R** or click the play button
3. Wait for the app to build and launch

### Step 4: Test the Connection
1. In the app, tap **"Connect"** in the top-left corner
2. The status indicator should turn green
3. Try the quick action buttons: `/status`, `/list-files`, `/help`
4. Type a custom command or message

## 🧪 Part 3: End-to-End Testing (5 minutes)

### Test Basic Commands
In the iOS app, try these commands:

1. **Agent Status**: Tap `/status` button
   - Should show agent information and model details

2. **File Operations**: Tap `/list-files` button
   - Should show files in the backend directory

3. **Help**: Tap `/help` button
   - Should show all available commands

4. **Custom Command**: Type `/current-dir` and send
   - Should show the current working directory

5. **Natural Language**: Type "Hello, can you help me?"
   - Should get an AI response (mock for now)

### Test Error Handling
1. **Invalid Command**: Type `/invalid-command`
   - Should show error message

2. **Connection Drop**: Stop the backend server (Ctrl+C)
   - App should show disconnected status

3. **Reconnection**: Restart backend and tap "Connect"
   - Should reconnect successfully

## 🔧 Troubleshooting

### Backend Issues

**Problem**: `ModuleNotFoundError: No module named 'fastapi'`
```bash
# Solution: Sync dependencies with uv
cd leenvibe-backend
uv sync
```

**Problem**: `uv: command not found`
```bash
# Solution: Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.cargo/bin:$PATH"
```

**Problem**: `Address already in use`
```bash
# Solution: Kill existing process or use different port
lsof -ti:8000 | xargs kill -9
# Or start on different port:
uv run uvicorn app.main:app --port 8001
```

**Problem**: Permission denied errors
```bash
# Solution: Fix permissions
chmod +x start.sh
chmod -R 755 app/
```

### iOS Issues

**Problem**: Build errors in Xcode
```bash
# Solution: Clean and rebuild
# In Xcode: Product → Clean Build Folder (Cmd+Shift+K)
# Then rebuild (Cmd+B)
```

**Problem**: Cannot find 'Starscream' dependency
```bash
# Solution: Update Swift package dependencies
# In Xcode: File → Packages → Update to Latest Package Versions
# Or in terminal:
cd LeenVibe-SwiftPM
swift package update
```

**Problem**: WebSocket connection fails
- Solution: Ensure backend is running on localhost:8000
- Check firewall settings
- Try iOS Simulator instead of physical device
- Verify network connectivity: `curl http://localhost:8000/health`

**Problem**: App crashes on launch
- Solution: Check Xcode console for errors
- Ensure iOS deployment target is 16.0+
- Verify Swift Package dependencies are resolved

### Network Issues

**Problem**: Cannot connect from iOS to Mac
```bash
# Check if backend is accessible
curl http://localhost:8000/health

# Check firewall (macOS)
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate

# Test WebSocket directly
wscat -c ws://localhost:8000/ws/test
```

## 🎉 Success Validation

You've successfully set up the vertical slice if:

✅ Backend health endpoint returns "healthy"  
✅ iOS app connects (green status indicator)  
✅ Commands execute and return responses  
✅ Messages appear in the chat interface  
✅ Error handling works (invalid commands show errors)  
✅ Performance is good (< 2 second response times)  

## 📈 Next Steps

Once you have the basic setup working:

1. **Explore Commands**: Try different `/` commands and natural language queries
2. **File Operations**: Use `/read-file` to examine source code
3. **Customize**: Modify the backend to add new commands
4. **Scale Testing**: Try multiple iOS connections simultaneously

## 🆘 Getting Help

If you run into issues:

1. **Check Logs**: Backend logs show detailed WebSocket activity
2. **Review Setup**: Ensure all prerequisites are met
3. **Test Components**: Verify backend health endpoint first
4. **Start Simple**: Test with curl/wscat before using iOS app

## 📚 What's Next?

This vertical slice demonstrates:
- Local AI agent architecture
- Real-time iOS-Mac communication  
- Command processing and responses
- Error handling and reconnection

The full LeenVibe system will add:
- True MLX model integration (CodeLlama-32B)
- Advanced agent autonomy with confidence scoring
- Kanban board visualization
- Voice command integration
- Multi-project support

Congratulations! You now have a working foundation for the LeenVibe L3 Coding Agent. 🎊