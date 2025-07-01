# ALPHA Agent - Task 01: iOS Dashboard Foundation Specialist

**Assignment Date**: Sprint 1 Foundation  
**Worktree**: `../leanvibe-ios-dashboard`  
**Branch**: `feature/ios-dashboard-foundation`  
**Status**: ✅ COMPLETED  

## Mission Brief

You are the **iOS Dashboard Foundation Specialist** responsible for Phase 1-2 of the iOS enhancement plan. Your mission is to transform the basic chat interface into a comprehensive multi-project dashboard system.

## Context

- **Current State**: iOS app has only basic chat interface (15% of MVP features)
- **Target State**: Multi-project dashboard with navigation, project cards, and real-time metrics (85% of MVP features)
- **Working Directory**: `../leanvibe-ios-dashboard`
- **Integration Target**: Main iOS project at `LeanVibe-iOS/`

## Specific Tasks

### Phase 1: Foundation Enhancement (2 weeks)
**Critical Priority - Core UI Architecture**

**Deliverables**:
- Replace single-view chat with TabView structure (Projects, Activity, Voice, Settings)
- Implement ProjectManager for multi-project tracking
- Create project discovery via backend APIs
- Build project card data models with real-time metrics

### Phase 2: Project Dashboard (2 weeks)
**High Priority - Core User Interface**

**Deliverables**:
- Project cards grid layout (2x2 responsive)
- Project status indicators and progress bars
- Comprehensive project detail screen with metrics
- Quick actions bar for common operations

## Technical Requirements

**Files to Create**:
```
LeanVibe-iOS-App/LeanVibe/
├── Models/
│   └── Project.swift - Core project data models and enums
├── Services/
│   └── ProjectManager.swift - Multi-project tracking with WebSocket integration
└── Views/
    ├── DashboardTabView.swift - Main TabView navigation hub
    ├── ProjectDashboardView.swift - 2x2 project grid dashboard
    ├── ProjectDetailView.swift - Comprehensive project detail screens
    ├── ChatView.swift - Enhanced agent chat interface
    ├── MonitoringView.swift - Real-time metrics monitoring
    ├── AddProjectView.swift - Project creation with file picker
    └── SettingsTabView.swift - Settings tab wrapper
```

**Backend Dependencies**:
- ✅ Available: `/sessions`, `/sessions/{client_id}/state`
- ✅ Available: `/ast/project/{client_id}/analysis`

## Architecture Requirements

**Main App Entry Point Change**:
```swift
// Before:
@main
struct LeanVibeApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView() // Single chat view
        }
    }
}

// After:
@main
struct LeanVibeApp: App {
    var body: some Scene {
        WindowGroup {
            DashboardTabView() // Multi-project dashboard
        }
    }
}
```

**Expected Result After Integration**:
1. **Projects Tab** - 2x2 grid dashboard (default tab)
2. **Agent Tab** - Enhanced chat interface  
3. **Monitor Tab** - Real-time metrics view
4. **Settings Tab** - Connection management

## Performance Targets

- **Launch Time**: <2 seconds
- **Tab Navigation**: <500ms
- **Card Grid Render**: <300ms
- **Memory Usage**: <100MB

## Quality Gates

- [ ] All unit tests passing (>80% coverage)
- [ ] Integration tests with backend working
- [ ] UI/UX meets design specifications
- [ ] Performance targets achieved
- [ ] No breaking changes to existing features

## Integration Requirements

**Manual Xcode Integration Required**:
The iOS Dashboard Foundation will be implemented with 10 new Swift files that need to be added to the Xcode project build target.

**Integration Steps**:
1. Open Xcode Project: `open LeanVibe.xcodeproj`
2. Add New Files to Target: Right-click folders → "Add Files to 'LeanVibe'"
3. Ensure "LeanVibe" target is checked for each file
4. Build and Test: Clean build folder → Build project → Run on simulator

## Success Criteria

- App launches to Projects dashboard
- All 4 tabs navigate correctly
- Project cards display data from backend
- Add Project functionality works
- Real-time WebSocket integration functional
- Transforms app from 15% (chat only) to 85% (multi-project dashboard)

## Handoff Requirements

Upon completion, provide:
1. **Integration Guide**: Step-by-step Xcode integration instructions
2. **Architecture Documentation**: Component relationships and data flow
3. **Performance Validation**: Benchmarks meeting all targets
4. **Team Handoff Guide**: Instructions for Week 3-4 teams (Kanban, Voice, etc.)

## Expected Outcome

Transform the basic chat interface into a sophisticated iOS app that delivers 100% of the promised MVP features, providing users with the comprehensive monitoring and control platform originally specified.

**Next Phase**: Week 3-4 teams will build on this foundation to add Kanban board, voice interface, and architecture visualization capabilities.