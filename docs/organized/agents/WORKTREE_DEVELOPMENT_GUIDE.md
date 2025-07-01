# LeanVibe Worktree Development Guide

## Overview

This guide explains how to use the git worktrees set up for parallel development of LeanVibe iOS app enhancement features. Each worktree enables independent development of specific features while maintaining integration with the main codebase.

## Worktree Structure

### Created Worktrees

| Worktree Directory | Branch | Purpose | Phase |
|-------------------|--------|---------|-------|
| `../leanvibe-ios-dashboard` | `feature/ios-dashboard-foundation` | Project dashboard and navigation architecture | 1-2 |
| `../leanvibe-ios-kanban` | `feature/ios-kanban-board` | Interactive Kanban board system | 3 |
| `../leanvibe-ios-voice` | `feature/ios-voice-interface` | Voice command system | 5 |
| `../leanvibe-ios-visualization` | `feature/ios-architecture-viewer` | Architecture visualization | 4 |
| `../leanvibe-backend-apis` | `feature/ios-support-apis` | Backend API enhancements | All |
| `../leanvibe-testing` | `feature/ios-integration-testing` | End-to-end testing and validation | 8 |
| `../leanvibe-ai` | `sprint-1-foundation` | Main integration and coordination | All |

## Development Workflow

### 1. Starting Work on a Feature

```bash
# Navigate to the appropriate worktree
cd ../leanvibe-ios-dashboard

# Verify you're on the correct branch
git branch
# Should show: * feature/ios-dashboard-foundation

# Pull latest changes from main
git pull origin sprint-1-foundation

# Start development
open LeanVibe-iOS/LeanVibe.xcodeproj
```

### 2. iOS Development Setup

Each iOS worktree contains the complete iOS app structure:

```bash
# Verify iOS app builds in worktree
cd ../leanvibe-ios-dashboard/LeanVibe-iOS
xcodebuild -project LeanVibe.xcodeproj -scheme LeanVibe build

# Open in Xcode for development
open LeanVibe.xcodeproj
```

### 3. Backend Development Setup

The backend APIs worktree is for enhancing backend endpoints:

```bash
# Navigate to backend worktree
cd ../leanvibe-backend-apis/leanvibe-backend

# Install dependencies
uv sync

# Start development server
./start.sh

# Run tests
python run_tests.py
```

### 4. Feature Integration Process

#### Daily Sync Process
```bash
# In each worktree, sync with latest main changes
git fetch origin
git merge origin/sprint-1-foundation

# Resolve any conflicts
# Commit your feature work
git add .
git commit -m "feat: implement [feature description]"
```

#### Weekly Integration
```bash
# Push feature branch
git push origin feature/ios-dashboard-foundation

# In main worktree, create integration branch
cd ../leanvibe-ai
git checkout -b integration/week-X-features

# Merge completed features
git merge feature/ios-dashboard-foundation
git merge feature/ios-kanban-board

# Test integration
cd leanvibe-backend && ./start.sh
cd ../LeanVibe-iOS && xcodebuild -project LeanVibe.xcodeproj -scheme LeanVibe build

# If tests pass, merge to main
git checkout sprint-1-foundation
git merge integration/week-X-features
```

## Feature Development Guidelines

### iOS Dashboard Worktree (`../leanvibe-ios-dashboard`)
**Focus**: Project cards, navigation, project detail views

```swift
// Expected file structure additions:
LeanVibe-iOS/LeanVibe/
├── Views/
│   ├── Dashboard/
│   │   ├── ProjectDashboardView.swift
│   │   ├── ProjectCardView.swift
│   │   └── ProjectDetailView.swift
│   └── Navigation/
│       └── MainTabView.swift
├── ViewModels/
│   ├── ProjectManager.swift
│   └── DashboardViewModel.swift
└── Models/
    ├── Project.swift
    └── ProjectMetrics.swift
```

### iOS Kanban Worktree (`../leanvibe-ios-kanban`)
**Focus**: Task management, drag-and-drop, real-time updates

```swift
// Expected file structure additions:
LeanVibe-iOS/LeanVibe/
├── Views/
│   ├── Kanban/
│   │   ├── KanbanBoardView.swift
│   │   ├── KanbanColumnView.swift
│   │   ├── TaskCardView.swift
│   │   └── TaskDetailView.swift
├── ViewModels/
│   ├── KanbanViewModel.swift
│   └── TaskManager.swift
└── Models/
    ├── Task.swift
    ├── KanbanColumn.swift
    └── TaskStatus.swift
```

### iOS Voice Worktree (`../leanvibe-ios-voice`)
**Focus**: Speech recognition, voice commands, wake phrase

```swift
// Expected file structure additions:
LeanVibe-iOS/LeanVibe/
├── Views/
│   ├── Voice/
│   │   ├── VoiceCommandView.swift
│   │   ├── VoiceWaveformView.swift
│   │   └── VoiceSettingsView.swift
├── Services/
│   ├── SpeechRecognitionService.swift
│   ├── VoiceCommandProcessor.swift
│   └── WakePhraseDetector.swift
└── Models/
    ├── VoiceCommand.swift
    └── SpeechRecognitionResult.swift
```

### Backend APIs Worktree (`../leanvibe-backend-apis`)
**Focus**: New endpoints for iOS features

```python
# Expected file structure additions:
leanvibe-backend/app/
├── api/endpoints/
│   ├── tasks.py          # Task management endpoints
│   ├── projects.py       # Project management endpoints
│   ├── voice_commands.py # Voice command processing
│   └── notifications.py # Push notification endpoints
├── models/
│   ├── task_models.py
│   ├── project_models.py
│   └── notification_models.py
└── services/
    ├── task_service.py
    ├── project_service.py
    └── notification_service.py
```

## Testing Strategy

### Unit Testing in Each Worktree
```bash
# iOS Testing
cd ../leanvibe-ios-dashboard/LeanVibe-iOS
xcodebuild test -project LeanVibe.xcodeproj -scheme LeanVibe

# Backend Testing
cd ../leanvibe-backend-apis/leanvibe-backend
python run_tests.py
```

### Integration Testing
```bash
# In testing worktree
cd ../leanvibe-testing

# Create end-to-end test scenarios
mkdir -p tests/ios-integration/
# Add tests for complete iOS → Backend workflows
```

## Conflict Resolution

### Common Conflict Scenarios
1. **Xcode Project File Conflicts** (`.pbxproj`)
2. **Shared Model Changes**
3. **Backend API Changes**

### Resolution Process
```bash
# For Xcode project conflicts
git checkout --theirs LeanVibe-iOS/LeanVibe.xcodeproj/project.pbxproj
# Then manually re-add your changes in Xcode

# For model conflicts
# Manually merge changes ensuring backward compatibility

# For API conflicts
# Coordinate with backend team to ensure all features work
```

## Shared Configuration

### Environment Variables
Create `.env.shared` in main worktree and symlink to others:
```bash
# In main worktree
echo "BACKEND_URL=http://localhost:8000" > .env.shared

# In other worktrees
ln -s ../../leanvibe-ai/.env.shared .env.shared
```

### Xcode Build Settings
Use shared xcconfig files for consistent build settings across worktrees.

## Maintenance Commands

### List All Worktrees
```bash
git worktree list
```

### Remove Completed Worktree
```bash
# After feature is merged and no longer needed
git worktree remove ../leanvibe-ios-dashboard
git branch -d feature/ios-dashboard-foundation
```

### Sync All Worktrees
```bash
# Script to sync all worktrees with latest main
#!/bin/bash
WORKTREES=(
    "../leanvibe-ios-dashboard"
    "../leanvibe-ios-kanban" 
    "../leanvibe-ios-voice"
    "../leanvibe-ios-visualization"
    "../leanvibe-backend-apis"
    "../leanvibe-testing"
)

for worktree in "${WORKTREES[@]}"; do
    echo "Syncing $worktree"
    cd "$worktree"
    git fetch origin
    git merge origin/sprint-1-foundation
    cd - > /dev/null
done
```

## IDE Configuration

### Xcode Workspace Setup
Each iOS worktree can be opened independently in Xcode, or create a master workspace:

```xml
<!-- LeanVibeWorkspace.xcworkspace/contents.xcworkspacedata -->
<?xml version="1.0" encoding="UTF-8"?>
<Workspace version = "1.0">
   <FileRef location = "group:../leanvibe-ios-dashboard/LeanVibe-iOS/LeanVibe.xcodeproj">
   </FileRef>
   <FileRef location = "group:../leanvibe-ios-kanban/LeanVibe-iOS/LeanVibe.xcodeproj">
   </FileRef>
   <!-- Add other worktrees as needed -->
</Workspace>
```

### VS Code Workspace
```json
{
    "folders": [
        {"path": "../leanvibe-ios-dashboard"},
        {"path": "../leanvibe-ios-kanban"},
        {"path": "../leanvibe-backend-apis"},
        {"path": "."}
    ],
    "settings": {
        "git.ignoredRepositories": [
            "../leanvibe-ios-dashboard",
            "../leanvibe-ios-kanban",
            "../leanvibe-backend-apis"
        ]
    }
}
```

## Best Practices

### 1. Feature Branch Naming
- Use descriptive, hierarchical names
- Follow pattern: `feature/ios-[component]-[description]`
- Example: `feature/ios-dashboard-project-cards`

### 2. Commit Messages
- Use conventional commits format
- Include component prefix
- Example: `feat(ios-dashboard): add project card grid layout`

### 3. Code Sharing
- Keep shared models in main worktree
- Use protocols for cross-component interfaces
- Document breaking changes clearly

### 4. Testing Requirements
- All iOS features must have unit tests
- Backend changes must have integration tests
- End-to-end tests in testing worktree

### 5. Performance Considerations
- Monitor memory usage across worktrees
- Use git worktree for active development only
- Clean up unused worktrees regularly

## Troubleshooting

### Common Issues

1. **"Worktree already exists"**
   ```bash
   git worktree list
   git worktree remove [path]
   ```

2. **Xcode project won't open**
   ```bash
   # Ensure only one instance of project open
   # Check file permissions
   chmod -R 755 LeanVibe-iOS/
   ```

3. **Backend port conflicts**
   ```bash
   # Kill existing backend processes
   lsof -ti:8000 | xargs kill -9
   ```

4. **Git submodule issues**
   ```bash
   git submodule update --init --recursive
   ```

## Success Metrics

### Weekly Integration Goals
- [ ] All iOS worktrees build successfully
- [ ] Backend tests pass in APIs worktree
- [ ] Integration tests pass in testing worktree
- [ ] No merge conflicts during integration
- [ ] Feature demos work end-to-end

### Quality Gates
- [ ] Code coverage maintained >80%
- [ ] No Xcode warnings in release builds
- [ ] Backend API response times <200ms
- [ ] iOS app launch time <2s
- [ ] Memory usage <500MB total

This worktree setup enables efficient parallel development while maintaining code quality and integration stability.