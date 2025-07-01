# ALPHA Agent - Task 02: Xcode Project Creation & Build System Setup

**Assignment Date**: Post Dashboard Foundation Completion  
**Worktree**: `../leanvibe-ios-dashboard`  
**Branch**: `feature/ios-dashboard-foundation`  
**Status**: 🔄 ASSIGNED  

## Mission Brief

You've successfully completed the iOS Dashboard Foundation milestone! Your Swift architecture has been integrated into the main repository. Now we need to complete the final build infrastructure to make your dashboard foundation fully testable and deployable.

## Context

- ✅ Your 10 Swift files have been merged into `LeanVibe-iOS/LeanVibe/`
- ✅ App architecture transforms 15% → 85% MVP delivery 
- ✅ DashboardTabView, ProjectManager, and all views integrated
- ❌ Missing: Xcode project file for build testing and device deployment

## Your Next Mission

Create complete Xcode project infrastructure to enable build testing and validation of your dashboard architecture.

## Working Directory

`/Users/bogdan/work/leanvibe-ai/LeanVibe-iOS/`

## Specific Tasks

1. **Create Xcode Project File**: Generate `LeanVibe.xcodeproj` with proper targets and schemes
2. **Configure Build Settings**: iOS 18+, Swift 6.0, appropriate capabilities 
3. **Add Dependencies**: Starscream WebSocket framework integration
4. **Build Validation**: Ensure clean compilation of your integrated Swift files
5. **Camera Permissions**: Add required permissions for QR scanner functionality
6. **Performance Testing**: Validate <2s launch time, <500MB memory targets

## File Structure to Support

```
LeanVibe-iOS/
├── LeanVibe.xcodeproj/          # CREATE THIS
├── LeanVibe/
│   ├── LeanVibeApp.swift ✅
│   ├── Models/
│   │   ├── AgentMessage.swift ✅  
│   │   └── Project.swift ✅       # Your creation
│   ├── Services/
│   │   ├── WebSocketService.swift ✅
│   │   ├── ConnectionStorageManager.swift ✅  # Your creation
│   │   └── ProjectManager.swift ✅            # Your creation  
│   └── Views/
│       ├── DashboardTabView.swift ✅          # Your creation
│       ├── ProjectDashboardView.swift ✅      # Your creation
│       └── [8 other view files] ✅            # Your creations
```

## Success Criteria

- [ ] `xcodebuild -project LeanVibe.xcodeproj -scheme LeanVibe build` succeeds
- [ ] App launches to your dashboard interface (not chat)
- [ ] All 4 tabs navigate correctly (Projects, Agent, Monitor, Settings)  
- [ ] QR scanner opens with camera permissions
- [ ] WebSocket connection status displays properly

## Technical Requirements

**Build Configuration**:
- **Target iOS Version**: 18.0+
- **Swift Version**: 6.0
- **Architecture**: arm64 (Apple Silicon)
- **Framework Dependencies**: Starscream (WebSocket)

**Required Permissions** (Info.plist):
```xml
<key>NSCameraUsageDescription</key>
<string>Camera access required for QR code scanning to connect to LeanVibe agent</string>
<key>NSMicrophoneUsageDescription</key>
<string>Microphone access required for voice commands</string>
```

**Capabilities**:
- App Sandbox (for App Store)
- Network connections (outgoing)

## Dependencies Integration

**Starscream WebSocket Framework**:
- Method 1: Swift Package Manager
- Method 2: CocoaPods
- Method 3: Manual framework addition

## Build Validation

After project creation, validate:
1. **Clean Build**: No compilation errors
2. **App Launch**: Launches to DashboardTabView
3. **Navigation**: All tabs functional
4. **WebSocket**: Connection status displays
5. **Performance**: Launch time <2s

## Priority

**HIGH** - This completes your dashboard foundation and enables team testing

## Handoff Deliverables

Upon completion:
1. Working `LeanVibe.xcodeproj` file
2. Build configuration documentation
3. Dependency setup instructions
4. Testing validation report

## Expected Outcome

Your architectural achievement becomes fully testable and deployable, completing the transformation from basic chat to comprehensive multi-project dashboard system.

Ready to complete your dashboard foundation with full Xcode project creation? This will make your architectural achievement fully testable and deployable! 🚀📱