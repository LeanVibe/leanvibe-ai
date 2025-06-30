# LeenVibe iOS App - Comprehensive Testing & Validation Plan

## 📋 Overview
This document provides a systematic approach to testing all LeenVibe iOS app functionalities. Follow this plan to validate each feature incrementally and document issues for dev/QA onboarding.

---

## 🏗️ **Phase 1: Infrastructure & Launch (CRITICAL)**
**Status**: ✅ FIXED - SceneDelegate issue resolved  
**Priority**: Must pass before testing other features

### 1.1 App Launch & Basic Navigation
**Test Steps:**
1. Launch app from device home screen
2. Verify app doesn't crash immediately
3. Check if launch screen appears properly
4. Validate main app interface loads

**Expected Results:**
- ✅ App launches without SceneDelegate errors
- ✅ No immediate crashes
- ✅ Launch screen displays
- ✅ Main app interface becomes available

**How to Test:**
```bash
# Monitor device logs while testing
xcrun devicectl device log stream --device 00008120-000654961A10C01E --style compact
```

---

## 🎤 **Phase 2: Speech Recognition (PRIORITY: HIGH)**
**Status**: 🔍 NEEDS VALIDATION  
**Likely Issues**: Permission handling, audio engine initialization

### 2.1 Speech Recognition Permissions
**Test Steps:**
1. Navigate to voice/speech features
2. Trigger speech recognition
3. Grant microphone permission when prompted
4. Grant speech recognition permission when prompted

**Expected Results:**
- Permission dialogs appear correctly
- Permissions are properly granted and stored
- No crashes during permission flow

**How to Test:**
- Go to Settings → Privacy & Security → Microphone → LeenVibe (should be ON)
- Go to Settings → Privacy & Security → Speech Recognition → LeenVibe (should be ON)

### 2.2 Speech Recognition Core Functionality
**Test Steps:**
1. Find voice command button/trigger
2. Start speech recognition
3. Speak clearly: "Hello LeenVibe"
4. Verify text recognition
5. Test silence timeout (stop speaking for 3+ seconds)
6. Test maximum duration timeout (speak for 30+ seconds)

**Expected Results:**
- Audio level indicator shows when speaking
- Recognized text appears in real-time
- Recognition stops after silence timeout
- Recognition stops after max duration
- No crashes during recording

**Known Configurations:**
- Max recording: 30 seconds
- Silence timeout: 3 seconds
- Supported locale: en-US
- Partial results enabled

### 2.3 Voice Command Processing
**Test Steps:**
1. Say specific voice commands (see Voice Commands section)
2. Verify command recognition
3. Verify command execution
4. Test error handling for unrecognized commands

---

## 📱 **Phase 3: WebSocket Connectivity**
**Status**: 🔍 NEEDS VALIDATION  
**Dependencies**: QR Scanner (✅ WORKING)

### 3.1 QR Code Connection Flow
**Test Steps:**
1. Open Settings → Server Settings
2. Tap "Scan QR Code"
3. Grant camera permission if needed
4. Point camera at QR code
5. Verify connection attempt
6. Check connection status

**Expected Results:**
- ✅ Camera view displays (not placeholder)
- QR code detection works with vibration feedback
- Connection attempt initiates
- Connection status updates in UI

**QR Code Format Expected:**
```
leenvibe://server/localhost:8000?ssl=false
```

### 3.2 Manual Server Connection
**Test Steps:**
1. Open Settings → Server Settings  
2. Enter server URL manually
3. Test connection
4. Verify connection persistence

**How to Test:**
- Default URL: `http://localhost:8000`
- Test with your development server
- Check connection indicator in app

### 3.3 WebSocket Message Flow
**Test Steps:**
1. Establish connection to server
2. Send message from app
3. Verify message received by server
4. Send message from server
5. Verify message received by app
6. Test connection resilience (disconnect/reconnect)

---

## 📋 **Phase 4: Task Management**
**Status**: 🔍 NEEDS VALIDATION  
**Dependencies**: WebSocket connection

### 4.1 Task CRUD Operations
**Test Steps:**
1. Navigate to Kanban/Task view
2. Create new task
3. Edit existing task
4. Move task between columns
5. Delete task
6. Verify persistence

**Expected Task States:**
- Backlog (gray)
- In Progress (blue) 
- Testing (orange)
- Done (green)
- Blocked (red)

### 4.2 Task Priority System
**Test Priority Levels:**
- Low (🟢 green)
- Medium (🟡 blue)
- High (🟠 orange)
- Critical (🔴 red)

### 4.3 Task Confidence & AI Features
**Test Steps:**
1. Check confidence indicator on tasks
2. Verify approval workflow for low-confidence tasks
3. Test AI decision integration

---

## 🎯 **Phase 5: Voice Commands Integration**
**Status**: 🔍 NEEDS VALIDATION  
**Dependencies**: Speech Recognition + Task Management

### 5.1 Core Voice Commands to Test
**Navigation Commands:**
- "Navigate to settings"
- "Show dashboard"
- "Open task view"

**Task Commands:**
- "Create new task"
- "Move task to done"
- "Show task details"

**System Commands:**
- "Read current screen"
- "Help with this screen"

### 5.2 Voice Command Error Handling
**Test Steps:**
1. Say unrecognized command
2. Speak unclear/mumbled words
3. Test in noisy environment
4. Test with background noise

---

## 🔄 **Phase 6: Real-time Updates**
**Status**: 🔍 NEEDS VALIDATION  
**Dependencies**: WebSocket + Task Management

### 6.1 Live Data Synchronization
**Test Steps:**
1. Connect multiple clients
2. Create task on one client
3. Verify update appears on other client
4. Test task movement synchronization
5. Test task deletion synchronization

### 6.2 Connection Resilience
**Test Steps:**
1. Disconnect network
2. Verify app handles disconnection gracefully
3. Reconnect network
4. Verify automatic reconnection
5. Verify data sync after reconnection

---

## 📱 **Phase 7: UI/UX Validation**
**Status**: 🔍 NEEDS VALIDATION

### 7.1 Navigation Flow
**Test All Screens:**
- Launch Screen ✅
- QR Onboarding Screen
- Dashboard/Main View
- Settings View
- Task/Kanban View
- Voice Settings
- Accessibility Settings
- Server Settings ✅

### 7.2 Accessibility Features
**Test Steps:**
1. Enable VoiceOver
2. Test screen reader compatibility
3. Test Dynamic Type (large text)
4. Test high contrast mode
5. Test one-handed mode

---

## 🚨 **Phase 8: Error Handling & Edge Cases**

### 8.1 Permission Denial Scenarios
**Test Steps:**
1. Deny camera permission → QR scanner should show permission request
2. Deny microphone permission → Speech should show permission request
3. Deny speech recognition → Voice commands should handle gracefully

### 8.2 Network Edge Cases
**Test Steps:**
1. No internet connection
2. Server unavailable
3. Slow network connection
4. Intermittent connectivity

### 8.3 Resource Constraints
**Test Steps:**
1. Low memory conditions
2. Background app interruptions
3. Phone calls during voice recognition
4. Multiple apps using microphone

---

## 🔧 **Quick Testing Scripts**

### Check App Logs
```bash
# Stream device logs
xcrun devicectl device log stream --device 00008120-000654961A10C01E --style compact

# Filter for LeenVibe logs
xcrun devicectl device log stream --device 00008120-000654961A10C01E --style compact | grep LeenVibe
```

### Check Permissions
```bash
# Check current permissions
xcrun simctl privacy list all | grep LeenVibe
```

### Reset App State
```bash
# Uninstall and reinstall for clean state
xcrun devicectl device uninstall app --device 00008120-000654961A10C01E com.bogdan.leenvibe.LeenVibe
# Then reinstall with xcodebuild
```

---

## 📊 **Issue Documentation Template**

When you find issues, document them like this:

```markdown
### Issue #001: [Brief Description]
**Phase**: [Which testing phase]
**Severity**: [Critical/High/Medium/Low]
**Steps to Reproduce**:
1. Step 1
2. Step 2
3. Step 3

**Expected Result**: What should happen
**Actual Result**: What actually happens
**Device Info**: iPhone model, iOS version
**Logs**: Relevant error messages
**Workaround**: If any temporary fix exists
```

---

## 🎯 **Testing Priority Order**

1. **Phase 1**: Infrastructure & Launch (CRITICAL)
2. **Phase 2**: Speech Recognition (HIGH - likely crash point)
3. **Phase 3**: WebSocket Connectivity (HIGH)
4. **Phase 4**: Task Management (MEDIUM)
5. **Phase 5**: Voice Commands (MEDIUM)
6. **Phase 6**: Real-time Updates (MEDIUM)
7. **Phase 7**: UI/UX (LOW)
8. **Phase 8**: Edge Cases (LOW)

---

## 🔍 **Next Steps**

1. **Start with Phase 1** - Verify app launches properly after SceneDelegate fix
2. **Focus on Phase 2** - Speech recognition is most likely to have issues
3. **Document any crashes immediately** with device logs
4. **Test incrementally** - Don't move to next phase until current phase passes
5. **Update this document** with results and new findings

**Current Status**: Ready to begin systematic testing. SceneDelegate issue resolved. App should launch without immediate crashes.