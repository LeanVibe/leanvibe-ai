# LeenVibe iOS App

This is the iOS companion app for the LeenVibe L3 Coding Agent. It provides real-time communication with the Mac backend and a mobile interface for monitoring and controlling the AI agent.

## Features

- Real-time WebSocket communication with Mac backend
- Command execution with quick action buttons
- Message history with different message types
- Connection status monitoring
- Error handling and reconnection
- Clean SwiftUI interface optimized for iOS

## Requirements

- iOS 16.0+
- Xcode 15+
- Mac backend running on local network

## Setup

### Option 1: Using Xcode (Recommended)

1. Open Xcode
2. Create a new iOS project:
   - Product Name: LeenVibe
   - Interface: SwiftUI
   - Language: Swift
   - Minimum Deployment: iOS 16.0

3. Replace the default files with the provided source files:
   - `LeenVibeApp.swift` - Main app entry point
   - `ContentView.swift` - Main UI
   - `Models/AgentMessage.swift` - Data models
   - `Services/WebSocketService.swift` - WebSocket communication

4. Build and run the project

### Option 2: Manual Project Creation

If you prefer to create the project manually:

```bash
# Create project structure
mkdir -p LeenVibe.xcodeproj LeenVibe/Views LeenVibe/Models LeenVibe/Services

# Copy source files to appropriate locations
cp LeenVibeApp.swift LeenVibe/
cp Views/ContentView.swift LeenVibe/Views/
cp Models/AgentMessage.swift LeenVibe/Models/
cp Services/WebSocketService.swift LeenVibe/Services/
```

## Usage

1. **Start the Mac Backend**:
   ```bash
   cd ../leenvibe-backend
   ./start.sh
   ```
   The backend should be running at `ws://localhost:8000`

2. **Connect from iOS**:
   - Open the LeenVibe app
   - Tap "Connect" in the top-left corner
   - The status indicator should turn green when connected

3. **Send Commands**:
   - Use quick action buttons: `/status`, `/list-files`, `/current-dir`, `/help`
   - Type custom commands in the text field
   - Send natural language messages for AI assistance

## Available Commands

- `/status` - Check agent status and capabilities
- `/list-files [directory]` - List files in current or specified directory
- `/read-file <path>` - Read contents of a file
- `/current-dir` - Show current working directory
- `/help` - Show all available commands

## Project Structure

```
LeenVibe/
├── LeenVibeApp.swift           # App entry point
├── Views/
│   └── ContentView.swift       # Main UI with chat interface
├── Models/
│   └── AgentMessage.swift      # Data models for messages and responses
└── Services/
    └── WebSocketService.swift  # WebSocket communication service
```

## Key Components

### WebSocketService
- Manages WebSocket connection to Mac backend
- Handles message encoding/decoding
- Provides connection status updates
- Implements automatic message formatting

### ContentView
- Main chat interface
- Quick command buttons
- Message history with different bubble styles
- Settings screen for connection management

### AgentMessage
- Data models for different message types
- JSON encoding/decoding for WebSocket communication
- Support for various response formats

## Troubleshooting

### Connection Issues

1. **Cannot Connect**: 
   - Ensure Mac backend is running on `localhost:8000`
   - Check firewall settings
   - Verify both devices are on same network

2. **Connection Drops**:
   - App automatically attempts to reconnect
   - Check network stability
   - Restart backend if needed

3. **Messages Not Sending**:
   - Check connection status (green circle)
   - Try reconnecting from Settings
   - Verify message format

### Common Solutions

1. **Restart Backend**:
   ```bash
   # In backend directory
   ./start.sh
   ```

2. **Clear App State**:
   - Use "Clear Messages" in Settings
   - Force quit and restart app

3. **Check Logs**:
   - View Xcode console for detailed error messages
   - Backend logs show WebSocket activity

## Development

### Adding New Features

1. **New Commands**:
   - Add command to backend `AIService.supported_commands`
   - Update iOS quick action buttons if needed
   - Test end-to-end functionality

2. **UI Improvements**:
   - Modify `ContentView.swift` for layout changes
   - Update `MessageBubble` for new message types
   - Test on different screen sizes

3. **WebSocket Enhancements**:
   - Extend `WebSocketService` for new message types
   - Update data models in `AgentMessage.swift`
   - Handle new response formats

### Testing

- Run on iOS Simulator for quick testing
- Test on physical device for real network conditions
- Verify with different backend states (connected/disconnected)

## Next Steps

- [ ] Add voice command support
- [ ] Implement file browsing UI
- [ ] Add code syntax highlighting
- [ ] Support multiple Mac connections
- [ ] Add push notifications for background updates

## Dependencies

Currently using only native iOS frameworks:
- SwiftUI for UI
- Foundation for networking
- Network framework for WebSocket connections

Future versions may add:
- Starscream for enhanced WebSocket support
- CodeEditor for syntax highlighting
- Lottie for animations