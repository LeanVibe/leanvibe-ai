# LeenVibe Swift Package

This is the LeenVibe iOS app built as a Swift Package Manager executable. It provides real-time communication with the Mac backend and a mobile interface for monitoring and controlling the AI agent.

## Features

- **Swift Package Manager**: Modern Swift dependency management
- **Starscream WebSocket**: Reliable WebSocket communication
- **SwiftUI Interface**: Clean, modern iOS UI
- **Real-time Communication**: WebSocket connection with Mac backend
- **Command Execution**: Quick action buttons and text input
- **Message History**: Different message types with proper formatting
- **Connection Management**: Auto-reconnection and error handling

## Requirements

- Swift 5.9+
- iOS 16.0+
- Xcode 15+
- Mac backend running on local network

## Quick Start

### Option 1: Run as Swift Package Executable

```bash
# Clone and navigate to Swift package
cd LeenVibe-SwiftPM

# Build the package
swift build

# Run tests
swift test

# Run the package (requires iOS Simulator)
swift run LeenVibe
```

### Option 2: Create iOS App Project

1. **Create New iOS Project in Xcode**:
   - File → New → Project → iOS → App
   - Product Name: LeenVibe
   - Interface: SwiftUI
   - Language: Swift
   - Minimum Deployment: iOS 16.0

2. **Add Swift Package Dependency**:
   - File → Add Package Dependencies
   - Enter local path: `/path/to/LeenVibe-SwiftPM`
   - Or use: `https://github.com/your-org/LeenVibe-SwiftPM` (if published)

3. **Update App.swift**:
   ```swift
   import SwiftUI
   import LeenVibe

   @main
   struct MyApp: App {
       var body: some Scene {
           WindowGroup {
               ContentView()
           }
       }
   }
   ```

### Option 3: Use as Library

Add to your `Package.swift`:

```swift
dependencies: [
    .package(path: "../LeenVibe-SwiftPM"),
],
targets: [
    .target(
        name: "YourApp",
        dependencies: ["LeenVibe"]
    ),
]
```

## Usage

### Start the Backend

First, ensure the Mac backend is running:

```bash
cd ../leenvibe-backend
./start.sh
```

### Connect from iOS

1. Launch the iOS app
2. Tap "Connect" in the top-left corner
3. Status indicator should turn green when connected
4. Use quick action buttons or type commands

### Available Commands

- `/status` - Check agent status and capabilities
- `/list-files [directory]` - List files in current or specified directory
- `/read-file <path>` - Read contents of a file
- `/current-dir` - Show current working directory
- `/help` - Show all available commands

Natural language messages are also supported for AI assistance.

## Project Structure

```
LeenVibe-SwiftPM/
├── Package.swift                    # Swift Package Manager manifest
├── Sources/LeenVibe/
│   ├── LeenVibeApp.swift           # App entry point
│   ├── Models/
│   │   └── AgentMessage.swift      # Data models
│   ├── Services/
│   │   └── WebSocketService.swift  # WebSocket communication
│   └── Views/
│       └── ContentView.swift       # SwiftUI views
└── Tests/LeenVibeTests/
    └── LeenVibeTests.swift         # Unit tests
```

## Dependencies

- **Starscream 4.0+**: WebSocket communication library
- **SwiftUI**: iOS native UI framework
- **Foundation**: Core iOS frameworks

## Development

### Building

```bash
# Build for development
swift build

# Build for release
swift build -c release

# Generate Xcode project (if needed)
swift package generate-xcodeproj
```

### Testing

```bash
# Run all tests
swift test

# Run specific test
swift test --filter LeenVibeTests.testAgentMessageCreation

# Generate test coverage
swift test --enable-code-coverage
```

### Code Quality

```bash
# Format code (if swiftformat is installed)
swiftformat Sources/ Tests/

# Lint code (if swiftlint is installed)
swiftlint
```

## WebSocket Communication

### Message Format

**Outgoing (iOS → Mac)**:
```json
{
    "type": "command",
    "content": "/status",
    "timestamp": "2025-06-26T12:00:00Z",
    "client_id": "ios-client-abc123"
}
```

**Incoming (Mac → iOS)**:
```json
{
    "status": "success",
    "type": "agent_status", 
    "message": "Agent is ready",
    "processing_time": 0.123,
    "data": {
        "model": "CodeLlama-7B",
        "ready": true
    }
}
```

### Connection Management

The WebSocketService handles:
- Automatic connection setup
- Message encoding/decoding
- Reconnection logic
- Error handling
- Connection status updates

## Troubleshooting

### Build Issues

**Error: Cannot find 'Starscream' in scope**
```bash
# Update dependencies
swift package update
swift package resolve
```

**Error: Platform version not supported**
- Ensure iOS deployment target is 16.0+
- Check Swift tools version is 5.9+

### Runtime Issues

**Cannot connect to backend**:
1. Ensure backend is running: `curl http://localhost:8000/health`
2. Check network connectivity
3. Verify iOS Simulator network settings

**WebSocket connection drops**:
- Check backend logs for errors
- Verify firewall settings
- Try restarting both backend and iOS app

### Performance Issues

**Slow message processing**:
- Check backend response times
- Monitor memory usage in Xcode
- Reduce message frequency if needed

## Next Steps

- [ ] Add voice command support using Speech framework
- [ ] Implement file browsing UI with syntax highlighting
- [ ] Add push notifications for background updates
- [ ] Support multiple Mac backend connections
- [ ] Add code editor with syntax highlighting
- [ ] Implement offline mode with cached responses

## Publishing

To publish as a Swift package:

1. **Create Git Repository**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git tag 0.1.0
   ```

2. **Push to GitHub**:
   ```bash
   git remote add origin https://github.com/your-org/LeenVibe-SwiftPM
   git push -u origin main
   git push --tags
   ```

3. **Use in Other Projects**:
   ```swift
   .package(url: "https://github.com/your-org/LeenVibe-SwiftPM", from: "0.1.0")
   ```

## License

MIT License - see LICENSE file for details.