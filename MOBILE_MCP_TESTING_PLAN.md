# LeanVibe iOS Mobile MCP Testing Plan & Analysis

## 🎯 Testing Status
- **Mobile MCP Setup**: ✅ Complete - iOS Simulator connected, LeanVibe app installed
- **WebDriverAgent Required**: ⚠️ Not configured - Manual testing guidance provided
- **App Launch Status**: ✅ LeanVibe successfully installed and launched on iPhone 16 Pro simulator

## 📱 Comprehensive Screen Testing Plan

### **Phase 1: Core Navigation & Launch Flow**

#### 1. Launch Screen Testing (`LaunchScreenView`)
**Test Objectives:**
- Verify logo and branding display
- Test loading states and transitions
- Validate navigation to onboarding

**Interactive Elements:**
- No user interaction - automatic transition based on app state
- Loading indicator animation
- App initialization progress

**Hardcoded Values Found:**
- Logo asset path: `AppIcon` in Assets.xcassets
- Loading timeout: Implicit in `AppCoordinator`
- Transition timing: Managed by SwiftUI animation defaults

**Expected Behavior:**
- App launches with LeanVibe logo
- Loading animation displays for 1-2 seconds
- Automatically navigates to `QROnboardingView` if first launch
- Navigates to `DashboardTabView` if already configured

---

#### 2. Onboarding Flow Testing (`QROnboardingView`)
**Test Objectives:**
- QR code scanner functionality
- Manual server URL input validation
- Connection testing and error handling

**Interactive Elements:**
```swift
// Key UI Components to Test:
- QR Code Scanner camera view
- Manual URL input field 
- "Connect" button
- "Skip for now" button (if available)
- Error message display
- Loading/connecting state
```

**Hardcoded Values Found:**
- Default server URL: `http://localhost:8001` (from AppConfiguration)
- Timeout values: Connection timeout settings
- Error messages: Predefined in `WebSocketService`

**Expected Behavior:**
- Camera permission request on first use
- QR scanner successfully reads server configuration QR codes
- Manual URL input accepts valid URLs
- Connection validation before proceeding
- Error handling for invalid URLs or unreachable servers

---

### **Phase 2: Main Application Features**

#### 3. Projects Tab Testing (`ProjectDashboardView`)
**Test Objectives:**
- Connection status indicators
- Project grid display and interactions
- Add project functionality
- Navigation to project details

**Interactive Elements:**
```swift
// Primary Interactive Components:
- Connection status indicator (top)
- "+ Add Project" button
- Project cards (grid layout)
- Quick action buttons (Refresh, Agent Chat, Monitor, Settings)
- Pull-to-refresh gesture
- Project card navigation
```

**Hardcoded Values Found:**
```swift
// From ProjectManager and mock data:
- Default health scores: 85%
- Sample project languages: Swift, Python, JavaScript, TypeScript
- Placeholder metrics: Lines of code, file counts
- Connection status: localhost:8001 hardcoded
- Color coding: Language-specific colors defined in PremiumDesignSystem
```

**Expected Behavior:**
- Green/Red connection indicator based on WebSocket status
- Empty state with "Add Your First Project" call-to-action
- Project cards show language icons with color coding
- Tap on project card → navigates to ProjectDetailView
- Quick action buttons navigate to respective tabs
- Pull-to-refresh updates project list

**Critical Testing Areas:**
- Test with no network connection (offline state)
- Test with invalid backend URL
- Verify language color coding matches design system
- Test grid layout on different screen orientations

---

#### 4. Agent Chat Testing (`ChatView`)
**Test Objectives:**
- Message input and sending
- Quick command functionality
- WebSocket connection status
- Message history display

**Interactive Elements:**
```swift
// Chat Interface Components:
- Text input field (multi-line support)
- Send button (airplane icon)
- Quick command buttons: /status, /list-files, /current-dir, /help
- Connection status header
- Message bubbles (user vs agent)
- Auto-scroll to latest
```

**Hardcoded Values Found:**
```swift
// From ChatView and WebSocketService:
- Quick commands: ["/status", "/list-files", "/current-dir", "/help"]
- Placeholder text: "Type a message..."
- Connection indicators: "Connected" / "Disconnected" states
- Message bubble styling: User (blue), Agent (gray)
```

**Expected Behavior:**
- Text input expands for multi-line messages
- Send button enabled only when text is entered
- Quick command buttons append text to input field
- Messages display with proper sender identification
- Auto-scroll maintains view at bottom for new messages
- Connection status updates in real-time

**Critical Testing Areas:**
- Test message sending without backend connection
- Verify quick command execution
- Test with very long messages
- Test rapid message sending (rate limiting)

---

#### 5. Monitor & Kanban Testing (`MonitoringView` + `KanbanBoardView`)
**Test Objectives:**
- Task creation and editing
- Drag-and-drop functionality
- Search and filtering
- Column management

**Interactive Elements:**
```swift
// Kanban Board Components:
- Floating Action Button (+ Create Task)
- Search bar with text input
- Sort dropdown (Priority, Due Date, Title)
- Drag-and-drop zones between columns
- Task cards with tap interaction
- Column headers: "To Do", "In Progress", "Done"
```

**Hardcoded Values Found:**
```swift
// From KanbanBoardView and Task models:
- Column names: ["To Do", "In Progress", "Done"]
- Column colors: Gray, Blue, Green
- Priority indicators: 🟢🟡🟠🔴 (Low, Medium, High, Urgent)
- Default confidence levels for AI tasks
- Sample task data in TaskService
```

**Expected Behavior:**
- Smooth drag-and-drop between columns
- Task creation modal with form validation
- Search filters tasks across all columns
- Sort options reorder tasks within columns
- Task cards show priority, confidence, and metadata
- Haptic feedback on successful drag-drop

**Critical Testing Areas:**
- Test drag-drop edge cases (dropping outside zones)
- Verify search performance with many tasks
- Test task creation form validation
- Test simultaneous task operations

---

### **Phase 3: Advanced Features**

#### 6. Settings Comprehensive Testing (`SettingsView`)
**Test Objectives:**
- All settings sections navigation
- Toggle and form controls
- Data persistence
- Settings validation

**Settings Sections to Test:**
```swift
// Main Settings Categories:
1. Voice & Speech Settings
   - Voice Commands toggle
   - Wake phrase configuration ("Hey LeanVibe")
   - Speech recognition settings
   - Voice testing interface

2. Task Management Settings
   - Kanban auto-refresh toggle
   - Task notifications
   - Productivity metrics toggle
   - Task creation defaults

3. Connection & Sync Settings
   - Server URL configuration
   - Background sync toggle
   - Offline mode settings
   - Network diagnostics

4. Appearance & Behavior Settings
   - Interface theme selection
   - Notification settings
   - Performance settings
   - Accessibility options (commented out)

5. Advanced Features Settings
   - Developer options (disabled by default)
   - Architecture viewer settings
   - System integration toggles
   - Backup & restore
   - Error history (TODO: needs fixing)
   - Retry monitor (TODO: needs fixing)

6. Support & About Settings
   - Help & documentation links
   - About LeanVibe (version display)
   - Privacy policy
```

**Hardcoded Values Found:**
```swift
// Settings default values:
- Wake phrase: "Hey LeanVibe"
- Auto-refresh interval: 30 seconds
- Connection timeout: 10 seconds
- App version: Bundle.main.infoDictionary version
- Default theme: System
```

**Expected Behavior:**
- All toggles persist state across app restarts
- Form inputs validate before saving
- Navigation to sub-settings works properly
- Settings changes take effect immediately
- Version information displays correctly

---

#### 7. Voice Interface Testing (`VoiceTabView`)
**Test Objectives:**
- Permission setup flow
- Wake phrase detection
- Voice command processing
- Audio visualization

**Interactive Elements:**
```swift
// Voice Interface Components:
- Permission setup flow
- Microphone access button
- Voice waveform visualization
- "Hey LeanVibe" wake phrase detection
- Live transcription display
- Command confirmation dialogs
- Quick command suggestions
```

**Hardcoded Values Found:**
```swift
// From VoiceCommandView and services:
- Wake phrase: "Hey LeanVibe"
- Supported commands: Status, List files, Show help
- Audio visualization settings
- Permission state management
- Low confidence threshold for confirmations
```

**Expected Behavior:**
- Microphone permission request on first use
- Real-time audio waveform visualization
- Wake phrase detection triggers command listening
- Voice transcription displays in real-time
- Low confidence commands show confirmation dialog
- Voice commands route to appropriate app sections

**Critical Testing Areas:**
- Test in noisy environments
- Verify permission denial handling
- Test wake phrase sensitivity
- Test with various accents/speech patterns

---

### **Phase 4: Error Handling & Edge Cases**

#### 8. Error Recovery Testing (`ErrorRecoveryView`)
**Test Objectives:**
- Network error handling
- App crash recovery
- Invalid input handling
- Graceful degradation

**Error Scenarios to Test:**
```swift
// Error conditions to simulate:
- Network disconnection
- Invalid server URLs
- Backend service unavailable
- Corrupted local data
- Permission denials
- Low memory conditions
- Background app refresh disabled
```

**Expected Behavior:**
- Informative error messages
- Recovery action buttons
- Automatic retry mechanisms
- Offline mode functionality
- Data consistency maintained

---

## 🔍 Comprehensive Hardcoded Values Audit

### **Configuration Values**
```swift
// AppConfiguration.swift
- Default server URL: "http://localhost:8001"
- isVoiceEnabled: true
- isDeveloperModeEnabled: false
- Wake phrase: "Hey LeanVibe"

// Performance thresholds
- Memory usage target: <200MB
- Voice response target: <500ms
- Animation frame rate: 60fps
- Battery usage target: <5% per hour
```

### **Mock Data & Placeholders**
```swift
// ProjectManager sample data
- Default health scores: 85%
- Sample languages: Swift, Python, JavaScript, TypeScript
- Placeholder file counts and metrics

// TaskService sample data
- Default task priorities and confidence levels
- Sample task descriptions and metadata

// Chat sample data
- Quick commands: /status, /list-files, /current-dir, /help
- Placeholder messages for empty states
```

### **UI Constants**
```swift
// Color coding
- Swift: Orange
- Python: Yellow  
- JavaScript: Yellow
- TypeScript: Blue
- Priority colors: Green (Low), Blue (Medium), Orange (High), Red (Urgent)

// Layout constants
- Card corner radius: 12pt
- Animation durations: 0.3s
- Haptic feedback intensities: Light, Medium, Heavy
```

### **Network & API Constants**
```swift
// WebSocket configuration
- Default port: 8001
- Reconnection timeout: <1ms target
- Connection timeout: 10 seconds
- Heartbeat interval: 30 seconds
```

---

## 🎯 Critical Production Issues Identified

### **Issues Requiring Backend Integration**
1. **Hardcoded localhost URLs** - Replace with configurable server endpoints
2. **Mock project data** - Integrate with real backend project management
3. **Sample metrics** - Connect to actual project analysis results
4. **Placeholder health scores** - Implement real health calculation

### **Incomplete Features (TODOs)**
1. **Error history view** - Currently commented out, needs implementation
2. **Retry monitor** - Placeholder implementation, needs completion
3. **Accessibility settings** - Some settings commented out
4. **Advanced features** - Several developer options disabled

### **Deprecated Code Issues**
1. **AVAudioSession.RecordPermission.denied** - Deprecated in iOS 17.0
2. **GlobalVoiceManager** - Marked deprecated, migration needed
3. **Bundle.main.appStoreReceiptURL** - Deprecated in iOS 18.0

---

## 📱 Manual Testing Workflow (Without WebDriverAgent)

### **Step-by-Step Testing Process**

1. **Launch App on Simulator**
   ```bash
   # App is already installed and launched
   # Simulator: iPhone 16 Pro (iOS 18.4)
   # Package: ai.leanvibe.LeanVibe
   ```

2. **Navigate Through Each Screen**
   - Test launch screen → onboarding flow
   - Configure server connection (use localhost:8001)
   - Navigate through all 5 tabs: Projects, Agent, Monitor, Settings, Voice
   - Test each interactive element systematically

3. **Test Key User Workflows**
   - Complete onboarding process
   - Add a new project
   - Create and move tasks in Kanban board
   - Send messages in agent chat
   - Configure settings in each section
   - Test voice commands (if permissions allow)

4. **Verify Error Handling**
   - Disconnect network and test offline behavior
   - Enter invalid URLs and test validation
   - Test with backend server down
   - Test permission denial scenarios

5. **Document Findings**
   - Screenshot each screen state
   - Note any UI issues or broken functionality
   - Identify all hardcoded values that need backend integration
   - Report any crashes or performance issues

---

## 🚀 Next Steps for Production Readiness

### **Immediate Actions Required**
1. **Replace Mock Data** - Integrate all hardcoded values with backend APIs
2. **Fix Deprecated APIs** - Update iOS 17/18 deprecated code
3. **Complete TODO Features** - Implement error history and retry monitor
4. **Backend Integration** - Replace localhost URLs with production endpoints

### **Testing Infrastructure Improvements**
1. **Set up WebDriverAgent** - Enable full Mobile MCP testing capabilities
2. **Automated UI Tests** - Create comprehensive UI test suite
3. **Performance Testing** - Validate memory, battery, and response time targets
4. **Accessibility Testing** - Implement full VoiceOver and Dynamic Type support

### **Quality Assurance Process**
1. **Manual Testing Checklist** - Complete systematic testing of all features
2. **Backend Connectivity** - Test with real backend services
3. **Error Scenario Testing** - Comprehensive error handling validation
4. **Production Environment Testing** - Validate with production configuration

---

**Testing Status**: ✅ Mobile MCP environment set up, app installed and launched  
**Next Priority**: Manual testing workflow execution and findings documentation  
**Estimated Completion**: 2-3 hours for comprehensive manual testing