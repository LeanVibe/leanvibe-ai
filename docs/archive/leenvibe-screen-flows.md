# LeenVibe L3 Agent - Screen Flow Documentation

## 1. Flow Overview & Objectives

### Primary User Flows
1. **Initial Setup Flow** - First-time configuration of Mac backend and iOS pairing
2. **Project Initialization Flow** - Starting a new project with the L3 agent
3. **Active Development Flow** - Day-to-day coding with agent assistance
4. **Mobile Monitoring Flow** - iOS app usage for project oversight
5. **Voice Command Flow** - Hands-free agent control via iOS

### Success Criteria
- Setup completed in under 5 minutes
- Zero friction for daily usage
- Instant sync between Mac and iOS
- Clear visibility into agent actions

## 2. Initial Setup Flow

### Entry Points
- Mac: Terminal command `leenvibe init`
- iOS: App Store download → First launch

### User Journey Map

```
[Mac Terminal] → [Installation] → [Model Download] → [Configuration] → [iOS Pairing] → [Ready]
```

### Detailed Screen Progression

#### S1.1: Mac Terminal - Installation
- **Entry**: User runs `brew install leenvibe` or downloads installer
- **Actions**: 
  - System compatibility check (M3 Max, 48GB RAM)
  - Installation progress display
  - Dependency verification
- **Success**: "LeenVibe CLI installed successfully"
- **Error States**: 
  - Insufficient hardware → Show requirements
  - Missing dependencies → Auto-install prompt

#### S1.2: Mac Terminal - Model Setup
- **Entry**: Automatic after installation
- **Display**: 
  ```
  LeenVibe L3 Agent Setup
  ======================
  Downloading Qwen2.5-Coder-32B model...
  [████████████████████████] 100% | 19.2GB/19.2GB
  
  Optimizing for Apple Silicon...
  Model ready for inference ✓
  ```
- **Actions**: Download progress, optimization status
- **Success**: Model ready confirmation
- **Error States**: Insufficient storage, network issues

#### S1.3: Mac Terminal - Configuration
- **Entry**: After model setup
- **Display**: Interactive configuration prompts
  ```
  Configure LeenVibe Settings
  
  1. Default project directory: ~/Projects
  2. Vim integration: [Y/n]
  3. Tmux integration: [Y/n]
  4. Confidence threshold: [0.7]
  5. Auto-commit enabled: [Y/n]
  ```
- **Actions**: User inputs preferences
- **Success**: Configuration saved

#### S1.4: iOS App - First Launch
- **Entry**: App opens after download
- **Display**: Welcome screen with LeenVibe branding
- **Actions**: 
  - "Get Started" button
  - Privacy policy acknowledgment
- **Navigation**: → Pairing screen

#### S1.5: iOS App - Mac Pairing
- **Entry**: From welcome or settings
- **Display**: 
  - QR code scanner view
  - Manual pairing code option
- **Mac Side**: Terminal shows QR code and 6-digit code
- **Actions**: Scan QR or enter code
- **Success**: "Successfully paired with Mac"
- **Error States**: Invalid code, network issues

## 3. Project Initialization Flow

### Entry Point
Mac: `leenvibe new [project-name]` or `leenvibe init` in existing directory

### Screen Progression

#### S2.1: Mac Terminal - Project Setup
- **Display**:
  ```
  Initializing LeenVibe for project: my-side-project
  
  Detected: Python 3.11, Node.js 18.2
  Analyzing existing codebase...
  Found 47 files, 3,421 lines of code
  
  Creating project knowledge graph...
  Setting up monitoring...
  ```
- **Actions**: Automatic analysis and setup
- **Success**: Project ready message

#### S2.2: iOS App - Project Card Creation
- **Entry**: Automatic sync from Mac
- **Display**: New project card appears on home screen
- **Content**:
  - Project name and icon
  - Language badges (Python, JS, etc.)
  - Initial stats (files, LOC)
  - "No active tasks" status

## 4. Active Development Flow

### Primary Interface: Mac Terminal (CLI)

#### S3.1: Mac Terminal - Agent Commands
- **Entry**: During active development
- **Common Commands**:
  ```
  leenvibe task "Add user authentication"
  leenvibe analyze [file]
  leenvibe refactor [function]
  leenvibe test
  leenvibe commit
  ```
- **Display Format**:
  ```
  🤖 L3 Agent: Analyzing task...
  Confidence: 87%
  Estimated time: 25 minutes
  
  Plan:
  1. Create auth middleware
  2. Add login/logout endpoints  
  3. Implement JWT tokens
  4. Update user model
  
  Proceed? [Y/n/explain]
  ```

#### S3.2: Mac Terminal - Real-time Feedback
- **During Execution**:
  ```
  ▶ Creating auth/middleware.py... ✓
  ▶ Implementing login endpoint... ✓
  ▶ Adding JWT support... 
    ⚠️ Confidence dropped to 65%
    Reason: Uncertain about token expiry strategy
    
  [P]ause for review / [C]ontinue / [A]bort?
  ```

### Secondary Interface: iOS Monitoring

#### S3.3: iOS App - Home Dashboard
- **Entry**: App launch or notification tap
- **Layout**: 
  - Project cards grid (2x2 on Pro Max)
  - Each card shows:
    - Project name
    - Active task indicator
    - Progress bar
    - Last activity timestamp
- **Actions**: Tap card → Project details

#### S3.4: iOS App - Project Detail View
- **Entry**: From home dashboard
- **Layout Sections**:
  1. **Header**: Project name, status badge
  2. **Kanban Board**: 
     - Backlog | In Progress | Testing | Done
     - Task cards with confidence indicators
  3. **Metrics Summary**:
     - Lines changed today
     - Test coverage
     - Build status
  4. **Quick Actions Bar**:
     - Voice command button
     - View architecture
     - See decision log

#### S3.5: iOS App - Kanban Board Interaction
- **Display**: Full-screen kanban view
- **Task Card Elements**:
  - Task title
  - Confidence meter (colored bar)
  - Time estimate
  - File count badge
- **Gestures**:
  - Swipe between columns
  - Tap card for details
  - Long press for options
- **Real-time Updates**: Cards move automatically as agent progresses

## 5. Architecture Visualization Flow

#### S4.1: iOS App - Architecture Viewer
- **Entry**: "View Architecture" button
- **Display**: 
  - Full-screen Mermaid diagram
  - Interactive nodes and edges
  - Zoom/pan controls
- **Interactions**:
  - Pinch to zoom
  - Tap node → Show file details
  - Double tap → Navigate to file view
  - Swipe down → Dismiss

#### S4.2: Architecture Change Detection
- **Trigger**: Significant structural changes
- **iOS Notification**: "Architecture changed in [project]"
- **Display**: 
  - Before/after comparison view
  - Changed nodes highlighted
  - Impact summary

## 6. Voice Command Flow

#### S5.1: iOS App - Voice Interface
- **Entry**: 
  - Tap microphone button
  - "Hey LeenVibe" wake phrase
- **Display**: 
  - Full-screen voice UI
  - Animated waveform
  - Transcription in real-time
- **Example Commands**:
  - "Start the authentication task"
  - "Show me the test results"
  - "What's the current confidence level?"
  - "Pause the agent"

#### S5.2: Voice Command Processing
- **Visual Feedback**:
  - Processing spinner
  - Command interpretation
  - Action confirmation
- **Response Format**:
  - Visual confirmation
  - Optional voice response
  - Status update

## 7. Decision & Confidence Management

#### S6.1: iOS App - Decision Log
- **Entry**: "Decision Log" from project menu
- **Display**: 
  - Chronological list of decisions
  - Each entry shows:
    - Timestamp
    - Decision type icon
    - Brief description
    - Confidence level
    - Outcome (if available)
- **Interactions**: Tap for full details

#### S6.2: Confidence Threshold Breach
- **Trigger**: Agent confidence < threshold
- **iOS Alert**: Push notification
- **Display Options**:
  - Quick review (notification actions)
  - Full review in app
- **Actions**:
  - Approve and continue
  - Modify approach
  - Take manual control

## 8. Test & Build Monitoring

#### S7.1: iOS App - Test Results View
- **Entry**: From metrics or notification
- **Display**:
  - Test suite summary
  - Pass/fail indicators
  - Coverage visualization
  - Failed test details
- **Actions**: 
  - Tap test → See output
  - "Re-run tests" button

#### S7.2: Build Status Display
- **Location**: Project header badge
- **States**:
  - Building (animated)
  - Success (green check)
  - Failed (red X)
  - Not run (gray dash)
- **Tap Action**: Show build log

## 9. Error Handling & Recovery

#### S8.1: Connection Lost
- **Trigger**: Mac-iOS connection interrupted
- **iOS Display**: 
  - Banner: "Connection lost. Attempting to reconnect..."
  - Cached data remains visible
  - Actions disabled
- **Recovery**: Auto-reconnect with status updates

#### S8.2: Agent Error State
- **Trigger**: Agent encounters unrecoverable error
- **Notification**: High-priority push
- **Display**: 
  - Error summary
  - Stack trace (expandable)
  - Suggested actions
  - "Get Help" button → Documentation

#### S8.3: Sync Conflicts
- **Trigger**: Conflicting changes detected
- **Display**: 
  - Conflict explanation
  - Side-by-side comparison
  - Resolution options
- **Actions**: Choose version or merge

## 10. Settings & Preferences

#### S9.1: iOS App - Settings Screen
- **Sections**:
  1. **Agent Configuration**
     - Confidence threshold slider
     - Auto-commit toggle
     - Language preferences
  2. **Notifications**
     - Push notification types
     - Do not disturb schedule
  3. **Connection**
     - Paired Mac info
     - Re-pair option
     - Connection diagnostics
  4. **About**
     - Version info
     - Documentation links
     - Support contact

## Navigation Flow Summary

### Mac Terminal Navigation
- Linear command-based flow
- Context maintained in terminal session
- Clear command feedback and prompts

### iOS App Navigation Structure
```
Tab Bar:
├── Projects (Home)
│   ├── Project Cards → Project Detail
│   │   ├── Kanban Board
│   │   ├── Architecture View
│   │   ├── Metrics Dashboard
│   │   └── Decision Log
├── Activity (Global feed)
├── Voice (Quick access)
└── Settings
```

### Cross-Platform State Synchronization
- All state changes reflect in <2 seconds
- Optimistic UI updates with rollback
- Offline queue for commands
- Conflict resolution UI when needed

## Accessibility Considerations

### Voice Control
- Primary accessibility feature
- All actions available via voice
- Clear audio feedback

### Visual Accessibility
- High contrast mode support
- Dynamic type support
- Reduced motion option
- Screen reader optimized labels

### Navigation
- Logical tab order
- Keyboard shortcuts (Mac)
- Gesture alternatives
- Clear focus indicators