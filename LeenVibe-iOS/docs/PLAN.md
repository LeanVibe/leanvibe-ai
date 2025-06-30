# Speech Recognition Crash Fix Plan

## 🎯 Objective
Fix critical iOS speech recognition crashes and establish regression-proof testing framework

## 🚨 Critical Issues Identified

### 1. Swift Continuation Leak (HIGH PRIORITY)
**Location**: `WebSocketService.swift:133-136`
**Issue**: `connectWithQRCode()` has unsafe continuation handling - continuation may not be resumed in all error paths
**Impact**: Memory leaks, potential crashes, system instability
**Fix**: Add proper error handling and ensure continuation is always resumed

### 2. Missing Asset Catalog Resources (HIGH PRIORITY)
**Issue**: Missing colors (green, orange, yellow) and system symbols (kanban, flowchart.box)
**Impact**: Runtime crashes when UI tries to load these missing assets
**Fix**: Add missing assets to Assets.xcassets or replace with available alternatives

### 3. Deprecated iOS APIs (MEDIUM PRIORITY)
**Location**: `VoicePermissionManager.swift:18`
**Issue**: `AVAudioSession.RecordPermission.undetermined` deprecated in iOS 17+
**Impact**: Potential future compatibility issues
**Fix**: Update to `.notDetermined`

### 4. Concurrency Violations (HIGH PRIORITY)
**Issue**: `unsafeForcedSync` calls from Swift concurrent contexts, Timer operations not properly isolated
**Impact**: Data races, undefined behavior, crashes
**Fix**: Ensure proper MainActor isolation and remove unsafe operations

### 5. NSMapTable NULL Pointer Issues (HIGH PRIORITY)
**Issue**: Unsafe memory access in speech recognition lifecycle
**Impact**: Crashes during audio engine teardown
**Fix**: Proper lifecycle management and null checking

## 📋 Detailed Implementation Plan

### PHASE 1: Critical Crash Fixes (1-2 hours)

#### Step 1.1: Fix Swift Continuation Leak
- **File**: `WebSocketService.swift`
- **Action**: Modify `connectWithQRCode()` method to ensure continuation is always resumed
- **Details**: Add comprehensive error handling, timeout mechanism, proper resource cleanup

#### Step 1.2: Add Missing Assets
- **File**: `Assets.xcassets`
- **Action**: Add missing color definitions and system symbols
- **Colors needed**: green, orange, yellow
- **Symbols needed**: kanban, flowchart.box (or suitable replacements)

#### Step 1.3: Update Deprecated APIs
- **File**: `VoicePermissionManager.swift`
- **Action**: Replace `.undetermined` with `.notDetermined`
- **Scope**: Review all AVAudioSession usage for other deprecated APIs

#### Step 1.4: Fix Concurrency Violations
- **File**: `SpeechRecognitionService.swift`
- **Action**: Audit timer operations and MainActor isolation
- **Focus**: Remove `unsafeForcedSync` calls, ensure proper actor boundaries

### PHASE 2: Testing Framework (2 hours)

#### Step 2.1: SpeechRecognitionServiceTests
- **Mock Components**: AVAudioEngine, permissions, audio input
- **Test Scenarios**:
  - Permission denial (microphone, speech recognition)
  - Audio engine start/stop lifecycle
  - Timeout scenarios (silence, max recording duration)
  - Concurrent start/stop operations
  - Error recovery and cleanup

#### Step 2.2: WebSocketServiceTests
- **Focus**: QR connection and continuation handling
- **Test Scenarios**:
  - Successful QR connection flow
  - Network failure during connection
  - Invalid QR data handling
  - Continuation timeout and cleanup
  - Multiple concurrent connection attempts

#### Step 2.3: Integration Tests
- **Scope**: End-to-end speech→WebSocket flow
- **Scenarios**:
  - Complete voice command to server transmission
  - Network interruption during speech recognition
  - Permission changes during active session
  - App backgrounding/foregrounding

### PHASE 3: Validation & Deployment (30 minutes)

#### Step 3.1: Test Suite Execution
- Run all new unit tests
- Verify test coverage meets minimum thresholds
- Validate mock effectiveness

#### Step 3.2: Build Validation
- Clean build with zero compilation errors
- SwiftLint compliance check
- Performance regression testing

#### Step 3.3: Device Testing
- Physical iPhone speech recognition validation
- Real network conditions testing
- User permission flow testing

## 🧪 Testing Strategy (Pragmatic 80/20 Approach)

### High-Value Test Coverage (80% impact)
1. **Permission States**: Most common user issues
   - Microphone denied
   - Speech recognition denied
   - Both permissions revoked during use

2. **Network Failures**: Critical for QR connection
   - Connection timeout
   - Server unreachable
   - Invalid QR data

3. **Audio Lifecycle**: Core functionality
   - Start recording success/failure
   - Stop recording cleanup
   - Engine interruption recovery

4. **Concurrency Safety**: Crash prevention
   - Multiple start/stop calls
   - Background/foreground transitions
   - Timer and continuation cleanup

### Mock Strategy
- **AVAudioEngine**: Simulate audio input, errors, interruptions
- **Network**: Control WebSocket connection states
- **Permissions**: Test all authorization combinations
- **System Events**: Background/foreground, interruptions

### Test Organization
```
Tests/
├── Unit/
│   ├── SpeechRecognitionServiceTests.swift
│   ├── WebSocketServiceTests.swift
│   └── VoicePermissionManagerTests.swift
├── Integration/
│   └── SpeechToWebSocketFlowTests.swift
└── Mocks/
    ├── MockAudioEngine.swift
    ├── MockWebSocket.swift
    └── MockPermissionManager.swift
```

## 📊 Success Metrics

### Immediate (Post-Fix)
- ✅ Zero crash reports related to speech recognition
- ✅ All tests passing (unit + integration)
- ✅ Clean build with no warnings
- ✅ Device testing successful

### Long-term (Regression Prevention)
- ✅ Test coverage >80% for critical paths
- ✅ Automated CI/CD integration
- ✅ Performance benchmarks maintained
- ✅ User experience improved (faster, more reliable)

## 🔧 Technical Implementation Details

### Continuation Fix Pattern
```swift
func connectWithQRCode(_ qrData: String) async throws {
    return try await withCheckedThrowingContinuation { continuation in
        // Ensure timeout mechanism
        let timeoutTask = Task {
            try await Task.sleep(nanoseconds: 10_000_000_000) // 10 seconds
            continuation.resume(throwing: TimeoutError())
        }
        
        // Store continuation safely
        self.qrConnectionContinuation = QRConnection(
            continuation: continuation,
            timeoutTask: timeoutTask
        )
        
        connectWithSettings(connectionSettings)
    }
}
```

### Asset Verification
- Use `Bundle.main.path(forResource:ofType:)` to verify assets exist
- Fallback to system-provided alternatives
- Runtime asset validation during app launch

### Concurrency Compliance
- All UI updates via `@MainActor` 
- Proper actor isolation for shared state
- Remove `nonisolated(unsafe)` where possible

## 🎯 Next Actions

1. **Immediate**: Start with Phase 1 critical fixes
2. **Priority Order**: Follow phases sequentially 
3. **Quality Gates**: Test after each phase before proceeding
4. **Documentation**: Update this plan based on discoveries during implementation

---

**Plan Created**: 2025-01-30  
**Last Updated**: 2025-01-30  
**Status**: Ready for Implementation