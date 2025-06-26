# LeenVibe L3 Agent - Complete Screen Design Briefs

## Table of Contents
1. [Mac Terminal Interfaces](#mac-terminal-interfaces)
2. [iOS App - Home Dashboard](#ios-app---home-dashboard)
3. [iOS App - Project Detail View](#ios-app---project-detail-view)
4. [iOS App - Kanban Board](#ios-app---kanban-board)
5. [iOS App - Architecture Viewer](#ios-app---architecture-viewer)
6. [iOS App - Voice Interface](#ios-app---voice-interface)
7. [iOS App - Decision Log](#ios-app---decision-log)
8. [iOS App - Test Results View](#ios-app---test-results-view)
9. [iOS App - Onboarding & Pairing](#ios-app---onboarding--pairing)
10. [iOS App - Settings](#ios-app---settings)

---

## Mac Terminal Interfaces

### Screen Identification
- **Screen Name**: Mac Terminal - L3 Agent Command Interface
- **Flow Context**: Active Development Flow
- **User Intent**: Execute commands and monitor agent progress in familiar CLI environment
- **Success Criteria**: Commands execute within 200ms, clear feedback, vim/tmux integration works seamlessly

### Target Persona Alignment
- **Primary Persona**: Alex Chen - Senior Engineer
- **Persona Goals**: Maintain flow state while coding, get intelligent assistance without context switching
- **Behavioral Considerations**: Prefers keyboard shortcuts, expects Unix-like command structure
- **Accessibility Needs**: High contrast for long coding sessions, clear visual hierarchy

### Brand & Visual Identity
- **Color Palette**: 
  - Background: Terminal black (#000000)
  - Primary text: Cool white (#F5F5F7)
  - Success: Green (#34C759)
  - Warning: Orange (#FF9500)
  - Error: Red (#FF3B30)
  - Agent responses: Electric blue (#007AFF)
- **Typography**: SF Mono, 14px default (user configurable)
- **Visual Style**: Clean, minimal, professional
- **ASCII Art**: Subtle LeenVibe logo on init

### Layout & Information Architecture
- **Screen Dimensions**: Terminal window (80-200 chars wide)
- **Structure**: 
  - Command prompt with project indicator
  - Agent response area with clear delineation
  - Progress indicators using Unicode blocks
  - Structured output with consistent indentation

### Content Specifications
- **Command Format**: `leenvibe [action] [target] [options]`
- **Agent Responses**: 
  ```
  🤖 L3 Agent: [Action description]
  Confidence: XX%
  Estimated time: XX minutes
  
  [Detailed plan or output]
  
  [Options]: [Y]es/[N]o/[E]xplain/[M]odify
  ```
- **Progress Indicators**: `[████████░░░░░░░░] 53% | Creating auth middleware...`
- **Error Messages**: Clear, actionable, with error codes

### Interactive Elements
- **Command Autocomplete**: Tab completion for all commands
- **Keyboard Shortcuts**: 
  - `Ctrl+C`: Cancel current operation
  - `Ctrl+L`: Clear screen
  - `Ctrl+R`: Search command history
- **Interactive Prompts**: Single-key responses for common actions

### Technical Considerations
- **Performance**: Sub-100ms response time for all commands
- **Integration**: Hooks for vim and tmux plugins
- **State Management**: Persistent session across terminal restarts
- **Output Formatting**: ANSI color codes, Unicode support

### Design Execution Guidelines
**For Implementation**:
```bash
# Visual hierarchy through spacing and symbols
🤖 L3 Agent: Analyzing task "Add user authentication"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Confidence: 87% ████████▓░
Time estimate: 25 minutes

📋 Execution Plan:
  1. Create auth/middleware.py
  2. Implement login/logout endpoints  
  3. Add JWT token support
  4. Update user model with auth fields

⚡ Ready to proceed? [Y/n/e/m]: 
```

---

## iOS App - Home Dashboard

### Screen Identification
- **Screen Name**: Projects Dashboard
- **Flow Context**: App entry point, project overview
- **User Intent**: Quickly assess project status and select active project
- **Success Criteria**: Load in <1s, show real-time status, support 10+ projects

### Target Persona Alignment
- **Primary Persona**: Alex Chen - Senior Engineer
- **Persona Goals**: Monitor multiple side projects, quickly identify what needs attention
- **Behavioral Considerations**: Checks during commute, coffee breaks, between meetings
- **Accessibility Needs**: One-handed operation, glanceable information

### Brand & Visual Identity
- **Color Palette**: 
  - Background: Pure black (#000000) for OLED
  - Card background: Dark gray (#1C1C1E) with subtle transparency
  - Primary: Electric blue (#007AFF)
  - Success: Green (#34C759)
  - Warning: Orange (#FF9500)
- **Typography**: 
  - Headers: SF Pro Display Bold, 34px
  - Project names: SF Pro Display Semibold, 20px
  - Metrics: SF Pro Text Regular, 15px
- **Visual Style**: Liquid glass design, subtle depth, smooth animations

### Layout & Information Architecture
- **Screen Dimensions**: 
  - iPhone 14 Pro: 393 × 852 pts
  - iPhone 14 Pro Max: 430 × 932 pts
- **Grid System**: 2×2 card grid with 16pt margins, 12pt gutters
- **Content Hierarchy**:
  1. Navigation bar with app title
  2. Active project cards (if any)
  3. Other project cards
  4. Tab bar

### Content Specifications
- **Project Cards Display**:
  - Project name (truncated at 2 lines)
  - Language/framework badges (max 3)
  - Status indicator (Active/Idle/Error)
  - Progress bar for active tasks
  - Last activity timestamp
  - Lines of code changed today
- **Empty State**: "No projects yet. Start one on your Mac with 'leenvibe new'"

### Interactive Elements
- **Card Interactions**:
  - Tap: Navigate to project detail
  - Long press: Quick actions menu
  - Swipe left: Archive project option
- **Pull to Refresh**: Updates all project statuses
- **Floating Action Button**: Voice command access

### Responsive Design Specifications
- **Orientation**: Portrait primary, landscape supported
- **Adaptations**: 
  - Pro Max: 2×3 grid option
  - Landscape: 3×2 grid
  - Dynamic Type: Scales from 15-24px

### Technical Considerations
- **Real-time Updates**: WebSocket connection indicator
- **Loading States**: Skeleton cards during data fetch
- **Error States**: Connection lost banner
- **Performance**: 60fps scrolling, lazy load images

### Accessibility Requirements
- **VoiceOver**: "Project [name], [status], last active [time]"
- **Dynamic Type**: All text scales appropriately
- **Contrast**: All text meets WCAG AA standards
- **Touch Targets**: Minimum 44×44pt

### Design Execution Guidelines
**For AI Tools (ChatGPT 4o, etc.)**:
"Create a modern iOS dashboard screen with a pure black background showcasing a 2×2 grid of project cards. Each card should have a dark gray (#1C1C1E) background with subtle glass morphism effect - very subtle blur and transparency. Cards display project name in SF Pro Display Semibold 20px white text, 2-3 colored language badges, a thin progress bar at bottom using electric blue (#007AFF), and status indicators. Include a tab bar at bottom with 4 icons: Projects (selected), Activity, Voice, Settings. Add subtle shadows and ensure 16pt margins around the grid with 12pt gaps between cards. The overall aesthetic should feel premium, clean, and perfectly suited for OLED displays."

---

## iOS App - Project Detail View

### Screen Identification
- **Screen Name**: Project Detail & Metrics
- **Flow Context**: Detailed project monitoring and control
- **User Intent**: Understand project progress, view metrics, access key functions
- **Success Criteria**: Complete project visibility, quick access to all features

### Target Persona Alignment
- **Primary Persona**: Alex Chen - Senior Engineer
- **Persona Goals**: Deep dive into project status, make informed decisions
- **Behavioral Considerations**: Reviews during longer breaks, makes strategic decisions
- **Accessibility Needs**: Clear data visualization, easy navigation

### Brand & Visual Identity
- **Consistent with Home Dashboard**
- **Additional Elements**: 
  - Data visualization colors: Blue gradients for positive metrics
  - Chart styles: Smooth curves, subtle gradients
  - Section dividers: 1px lines at 20% opacity

### Layout & Information Architecture
- **Screen Structure**:
  1. Navigation bar with project name
  2. Status summary card
  3. Kanban preview (horizontally scrollable)
  4. Metrics grid (2×2)
  5. Quick actions section
  6. Recent activity feed

### Content Specifications
- **Status Summary**:
  - Current task in progress
  - Overall confidence score (large, prominent)
  - Time spent today
  - Estimated completion
- **Metrics Grid**:
  - Lines changed
  - Test coverage %
  - Build status
  - Commit count
- **Quick Actions**:
  - View Kanban
  - Architecture
  - Decision Log
  - Voice Command

### Interactive Elements
- **Scrollable Sections**: Smooth scrolling with rubber-band effect
- **Metric Cards**: Tap for detailed view
- **Kanban Preview**: Horizontal scroll, tap to expand
- **Pull to Refresh**: Updates all metrics

### Design Execution Guidelines
**For AI Tools**:
"Design a comprehensive project detail screen with a black background. Start with a large status card showing current task and a circular confidence meter (87% in blue gradient). Below, create a horizontally scrollable kanban preview showing mini task cards. Add a 2×2 metrics grid with cards for: lines changed (with mini line chart), test coverage (circular progress), build status (icon + text), and commits (number + trend). Each metric card should have subtle glass morphism. Include quick action buttons with SF Symbols icons. Maintain consistent 16pt margins and ensure all elements align to an 8pt grid."

---

## iOS App - Kanban Board

### Screen Identification
- **Screen Name**: Interactive Kanban Board
- **Flow Context**: Task management and progress tracking
- **User Intent**: View and manage project tasks, understand workflow
- **Success Criteria**: Clear task visibility, smooth animations, real-time updates

### Target Persona Alignment
- **Primary Persona**: Alex Chen - Senior Engineer
- **Persona Goals**: Track task progress, identify bottlenecks
- **Behavioral Considerations**: Expects Trello-like familiarity with unique AI elements
- **Accessibility Needs**: Clear column headers, readable task cards

### Brand & Visual Identity
- **Column Colors**: 
  - Backlog: Neutral gray
  - In Progress: Electric blue
  - Testing: Orange
  - Done: Success green
- **Task Card Style**: Rounded corners, subtle shadows, glass morphism

### Layout & Information Architecture
- **Full-screen View**: Maximizes task visibility
- **Column Layout**: 4 columns, horizontally scrollable
- **Card Density**: 3-4 cards visible per column
- **Header**: Fixed position with column names

### Content Specifications
- **Task Cards**:
  - Task title (2 lines max)
  - Confidence meter (colored bar)
  - Time estimate badge
  - File count indicator
  - AI/Human indicator icon
- **Column Headers**: Name + task count

### Interactive Elements
- **Gestures**:
  - Pinch to zoom out (overview mode)
  - Tap card for detail modal
  - Long press for options
  - Swipe between columns
- **Real-time Animation**: Cards slide between columns automatically

### Design Execution Guidelines
**For AI Tools**:
"Create a kanban board interface with 4 columns on black background. Each column has a header with name and count in a colored pill (gray for Backlog, blue for In Progress, orange for Testing, green for Done). Task cards are dark gray with subtle glass effect, showing: task title in white, a colored confidence bar (0-100%), time estimate in a small badge, and file count. Add smooth shadows and ensure cards have 8px rounded corners. Include subtle column separators and maintain 12pt spacing between cards."

---

## iOS App - Architecture Viewer

### Screen Identification
- **Screen Name**: Interactive Architecture Diagram
- **Flow Context**: Code architecture visualization
- **User Intent**: Understand code structure, identify dependencies
- **Success Criteria**: Clear visualization, smooth interactions, readable at all zoom levels

### Target Persona Alignment
- **Primary Persona**: Alex Chen - Senior Engineer
- **Persona Goals**: Maintain architectural integrity, spot issues early
- **Behavioral Considerations**: Values clean architecture, enjoys visual representations
- **Accessibility Needs**: High contrast mode, zoom support

### Brand & Visual Identity
- **Node Colors**: Based on file types (Python blue, JS yellow, etc.)
- **Connection Lines**: Subtle gradients showing dependency direction
- **Background**: Pure black with subtle grid pattern
- **Highlight Colors**: Electric blue for selection

### Layout & Information Architecture
- **Full-screen Canvas**: Maximum space for diagram
- **Overlay Controls**: 
  - Zoom controls (bottom right)
  - Filter options (top right)
  - Back button (top left)
- **Node Layout**: Force-directed graph, clustered by module

### Content Specifications
- **Node Information**:
  - File/module name
  - Type icon
  - Size indicator (LOC)
  - Change frequency heat map
- **Edge Information**:
  - Dependency type
  - Strength indicator (line weight)

### Interactive Elements
- **Touch Gestures**:
  - Pinch to zoom
  - Pan to navigate
  - Tap node for details
  - Double tap to focus
- **Visual Feedback**: Nodes pulse when selected

### Design Execution Guidelines
**For AI Tools**:
"Design an architecture visualization screen with a pure black background and subtle grid. Create a network diagram with circular nodes in different colors (blue for Python files, yellow for JavaScript, green for configs). Connect nodes with curved lines that have subtle gradients. Selected nodes should have an electric blue glow. Add zoom controls in bottom right with + and - buttons in glass morphism style. Include a mini-map in top right corner for navigation. Ensure all text is legible with proper contrast."

---

## iOS App - Voice Interface

### Screen Identification
- **Screen Name**: Voice Command Interface
- **Flow Context**: Hands-free agent control
- **User Intent**: Quick commands without touching screen
- **Success Criteria**: <2s response time, accurate transcription, clear feedback

### Target Persona Alignment
- **Primary Persona**: Alex Chen - Senior Engineer
- **Persona Goals**: Control agent while multitasking
- **Behavioral Considerations**: Uses during commute, cooking, exercising
- **Accessibility Needs**: Primary accessibility feature itself

### Brand & Visual Identity
- **Animation Style**: Smooth, organic waveform
- **Color Scheme**: Blue gradient waveform on black
- **Visual Feedback**: Pulsing glow during processing

### Layout & Information Architecture
- **Full-screen Modal**: Focuses attention
- **Centered Layout**: 
  1. Animated waveform
  2. Transcription text
  3. Status indicator
  4. Cancel button

### Content Specifications
- **Status Messages**:
  - "Listening..."
  - "Processing..."
  - "Command understood"
  - Error messages
- **Transcription**: Real-time, word-by-word appearance
- **Command Examples**: Shown before activation

### Interactive Elements
- **Activation**: Tap mic button or "Hey LeenVibe"
- **Waveform**: Responds to voice amplitude
- **Cancel**: Swipe down or tap X
- **Haptic Feedback**: On recognition success/failure

### Design Execution Guidelines
**For AI Tools**:
"Create a voice interface screen with pure black background. Center a large animated waveform visualization using blue gradient colors (#007AFF to #5856D6). Below the waveform, show transcribed text appearing word by word in white SF Pro Display 24px. Add a subtle pulsing glow effect around the waveform during listening. Include a small 'Cancel' button at bottom. The waveform should have smooth, organic curves that respond to audio amplitude. Add subtle particle effects emanating from the waveform for visual interest."

---

## iOS App - Decision Log

### Screen Identification
- **Screen Name**: AI Decision History
- **Flow Context**: Transparency and audit trail
- **User Intent**: Review AI decisions, understand reasoning
- **Success Criteria**: Complete history, clear reasoning, filterable

### Target Persona Alignment
- **Primary Persona**: Alex Chen - Senior Engineer
- **Persona Goals**: Maintain control, learn from AI decisions
- **Behavioral Considerations**: Reviews during retrospectives, debugging
- **Accessibility Needs**: Searchable, scannable layout

### Brand & Visual Identity
- **Decision Type Colors**:
  - Architecture: Purple
  - Refactoring: Blue
  - Bug Fix: Orange
  - Feature: Green
- **Timeline Style**: Vertical with connecting lines

### Layout & Information Architecture
- **List Layout**: Chronological with newest first
- **Filters**: Decision type, confidence level, date range
- **Detail View**: Expandable cards with full reasoning

### Content Specifications
- **Decision Cards**:
  - Icon for decision type
  - Brief description
  - Confidence percentage
  - Timestamp
  - Outcome indicator
- **Expanded View**:
  - Full reasoning
  - Code snippets
  - Alternative considered
  - Human override option

### Interactive Elements
- **Filter Pills**: Tap to toggle
- **Cards**: Tap to expand/collapse
- **Search**: Pull down to reveal search bar
- **Actions**: Swipe for options (revert, explain more)

### Design Execution Guidelines
**For AI Tools**:
"Design a decision log screen with a black background showing a vertical timeline. Each decision is a card with dark gray background, colored left border (purple for architecture, blue for refactoring, etc.), an icon, title, confidence percentage in a small badge, and relative timestamp. Expandable cards reveal detailed reasoning with code snippets in monospace font. Add filter pills at top for decision types. Include subtle connecting lines between cards to show timeline flow. Ensure high contrast for readability."

---

## iOS App - Test Results View

### Screen Identification
- **Screen Name**: Test Suite Results
- **Flow Context**: Quality assurance monitoring
- **User Intent**: Verify code quality, identify failures
- **Success Criteria**: Clear pass/fail status, actionable failure information

### Target Persona Alignment
- **Primary Persona**: Alex Chen - Senior Engineer
- **Persona Goals**: Maintain high code quality, quickly fix issues
- **Behavioral Considerations**: Checks after notifications, during review sessions
- **Accessibility Needs**: Color-blind friendly indicators

### Brand & Visual Identity
- **Status Colors**:
  - Pass: Green (#34C759)
  - Fail: Red (#FF3B30)
  - Skipped: Gray (#8E8E93)
  - Running: Blue animated
- **Chart Style**: Clean, minimal, high contrast

### Layout & Information Architecture
- **Summary Section**: Overall stats at top
- **Test List**: Grouped by test suite
- **Detail View**: Failure output and stack traces

### Content Specifications
- **Summary Metrics**:
  - Pass rate percentage (large)
  - Total tests run
  - Duration
  - Coverage percentage
- **Test Items**:
  - Test name
  - Status icon
  - Duration
  - Error preview (if failed)

### Interactive Elements
- **Collapsible Sections**: Test suites expand/collapse
- **Re-run Button**: Prominent action button
- **Copy Error**: Long press on error message
- **Filter**: Show only failures toggle

### Design Execution Guidelines
**For AI Tools**:
"Create a test results screen with black background. Top section shows large circular progress indicator with pass rate (87% in green), surrounded by smaller metrics. Below, list test suites as collapsible sections with dark gray headers showing suite name and pass/fail count. Individual tests show as rows with status icon (green check, red X, gray dash), test name, and duration. Failed tests expand to show error message in red monospace font. Include a floating 'Re-run Tests' button with blue gradient background."

---

## iOS App - Onboarding & Pairing

### Screen Identification
- **Screen Name**: Welcome & Mac Pairing
- **Flow Context**: First-time setup
- **User Intent**: Connect iOS app to Mac backend
- **Success Criteria**: Pairing completed in <30 seconds

### Target Persona Alignment
- **Primary Persona**: Alex Chen - Senior Engineer
- **Persona Goals**: Quick setup, get to work fast
- **Behavioral Considerations**: Impatient with lengthy onboarding
- **Accessibility Needs**: Clear instructions, alternative pairing methods

### Brand & Visual Identity
- **Welcome Style**: Premium, minimal, focused
- **LeenVibe Logo**: Centered, animated entrance
- **Illustrations**: Abstract, geometric, blue gradients

### Layout & Information Architecture
1. **Welcome Screen**: Logo, tagline, get started button
2. **Pairing Screen**: QR scanner with manual option
3. **Success Screen**: Confirmation and proceed button

### Content Specifications
- **Welcome Text**: "Your L3 Coding Agent Awaits"
- **Pairing Instructions**: "Scan QR code from Mac terminal"
- **Manual Option**: "Enter code manually"
- **Success Message**: "Connected to [Mac Name]"

### Interactive Elements
- **QR Scanner**: Full-screen camera view
- **Manual Entry**: 6-digit code input
- **Skip Options**: Clear but de-emphasized
- **Animations**: Smooth transitions between steps

### Design Execution Guidelines
**For AI Tools**:
"Design an onboarding flow starting with a welcome screen: black background, centered LeenVibe logo with subtle glow effect, tagline in SF Pro Display 24px gray text, and a prominent 'Get Started' button with blue gradient. Second screen shows QR code scanner interface with camera view, scanning overlay animation, and 'Enter Code Manually' link at bottom. Success screen displays green checkmark animation, 'Successfully Connected' message, and Mac device name with a 'Continue' button."

---

## iOS App - Settings

### Screen Identification
- **Screen Name**: Settings & Preferences
- **Flow Context**: App configuration and preferences
- **User Intent**: Customize experience, manage connections
- **Success Criteria**: All options easily accessible, changes apply immediately

### Target Persona Alignment
- **Primary Persona**: Alex Chen - Senior Engineer
- **Persona Goals**: Fine-tune agent behavior, manage notifications
- **Behavioral Considerations**: Prefers granular control
- **Accessibility Needs**: Standard iOS settings patterns

### Brand & Visual Identity
- **Style**: Standard iOS settings aesthetic
- **Grouping**: Logical sections with headers
- **Icons**: SF Symbols, consistent sizing

### Layout & Information Architecture
- **Sections**:
  1. Agent Configuration
  2. Notifications
  3. Connection
  4. Appearance
  5. About

### Content Specifications
- **Agent Settings**:
  - Confidence threshold slider
  - Auto-commit toggle
  - Language preferences
- **Connection Info**:
  - Paired Mac name
  - Connection status
  - Last sync time

### Interactive Elements
- **Standard Controls**: Switches, sliders, selection lists
- **Destructive Actions**: Red text with confirmation
- **Navigation**: Disclosure indicators for sub-screens

### Design Execution Guidelines
**For AI Tools**:
"Create an iOS settings screen with black background using standard iOS design patterns. Group settings into sections with gray headers: 'Agent Configuration' (confidence threshold slider, auto-commit switch), 'Notifications' (toggle switches for different alert types), 'Connection' (shows paired Mac info with green status dot), 'Appearance' (theme options), and 'About' (version, help links). Use SF Symbols for icons, standard iOS toggle switches in blue, and ensure proper spacing between sections. Include chevron disclosure indicators for items that lead to sub-screens."

---

## Global Design System Notes

### Consistency Across All Screens
- **Spacing**: 8pt grid system throughout
- **Margins**: 16pt standard, 20pt for primary content
- **Corner Radius**: 8pt small, 12pt medium, 16pt large
- **Shadows**: Subtle, consistent elevation system
- **Animations**: 0.3s standard, spring damping 0.8

### Performance Guidelines
- **Images**: Optimize for 3x retina displays
- **Animations**: 60fps minimum, use Metal when needed
- **Loading**: Skeleton screens, progressive disclosure
- **Caching**: Aggressive caching for offline capability

### Accessibility Checklist
- [ ] All interactive elements ≥44pt touch targets
- [ ] Text contrast ratios ≥4.5:1 (WCAG AA)
- [ ] VoiceOver labels for all UI elements
- [ ] Dynamic Type support (minimum to xxxLarge)
- [ ] Reduce Motion respected for animations
- [ ] Color-blind friendly status indicators

### Brand Consistency
- [ ] LeenVibe logo placement consistent
- [ ] Color palette strictly followed
- [ ] Typography hierarchy maintained
- [ ] Glass morphism effects subtle and consistent
- [ ] Professional, premium feel throughout

---

## Implementation Priority

### Phase 1 (MVP)
1. Mac Terminal Interface
2. iOS Home Dashboard
3. iOS Project Detail View
4. iOS Pairing Flow

### Phase 2
5. iOS Kanban Board
6. iOS Voice Interface
7. iOS Test Results

### Phase 3
8. iOS Architecture Viewer
9. iOS Decision Log
10. iOS Settings

Each screen should be implemented with careful attention to the design specifications, ensuring a cohesive, premium experience that empowers senior engineers to successfully complete their side projects with the assistance of the LeenVibe L3 agent.