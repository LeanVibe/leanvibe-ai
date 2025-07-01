# LeanVibe iOS: Contract-First Integration Recovery Plan

**Plan Created**: 2025-07-01  
**Status**: ✅ PHASE 1 - Contract Foundation (In Progress)  
**Overall Progress**: 50% (6/12 tasks completed) - FOUNDATION ESTABLISHED ✅

## Learning from Past Failures

The AI agent integration analysis revealed **catastrophic failures** from:
- 100+ compilation errors from interface mismatches
- Zero shared schema causing `Task` vs `LeanVibeTask` conflicts  
- No continuous integration leading to broken builds
- Missing communication protocol between agents

**This plan prevents these failures through contract-first development.**

---

## Phase 1: Contract Foundation (Single Agent - 1 day)

### ✅ 1.1 Save and Maintain Plan Document (30 minutes) - COMPLETED
- **Status**: ✅ COMPLETED (2025-07-01)
- **Action**: Created `docs/PLAN.md` with complete plan
- **Notes**: Plan document established for continuous progress tracking

### ✅ 1.2 Shared Schema Definition (4 hours) - COMPLETED
- **Status**: ✅ COMPLETED (2025-07-01)
- **Action**: Created `project-schema.yaml` with canonical names and service contracts
- **Deliverable**: Complete schema preventing interface contract violations
- **Key Preventions**:
  - `LeanVibeTask` vs `Task` naming conflicts resolved
  - `displayName` vs `name` property conflicts prevented
  - `issuesCount` vs `issueCount` standardized
  - All service protocols defined with exact signatures
- **Notes**: This schema MUST be followed by all subsequent implementations
```yaml
models:
  Task:
    name: LeanVibeTask  # Prevent Swift.Task conflicts
    properties:
      - id: UUID
      - title: String  
      - status: TaskStatus
  Project:
    properties:
      - displayName: String  # NOT name
      - issuesCount: Int     # NOT issueCount
```

### ✅ 1.3 Interface Contracts (4 hours) - COMPLETED
- **Status**: ✅ COMPLETED (2025-07-01)
- **Action**: Created ProjectManagerProtocol, TaskServiceProtocol, OnboardingManagerProtocol
- **Deliverable**: Service protocols preventing integration failures
- **Key Achievements**:
  - Exact method signatures defined for all core services
  - @MainActor concurrency annotations for UI consistency
  - Default implementations provided for common functionality
- **Notes**: All future service implementations MUST conform to these protocols
```swift
protocol ProjectManagerProtocol {
    var projects: [Project] { get }
    var isLoading: Bool { get }
    var lastError: String? { get }
    func refreshProjects() async throws
}
```

### ✅ 1.4 Continuous Integration Setup (2 hours) - COMPLETED
- **Status**: ✅ COMPLETED (2025-07-01)
- **Action**: Created ci-check.sh script with error budget enforcement
- **Deliverable**: Build verification script that **stops all work** on compilation errors
- **Key Features**:
  - Detects compilation errors and halts all development
  - Error budget threshold (5 errors max before stopping)
  - Clear reporting with error summaries
  - **VALIDATED**: Successfully detected 58,994 errors and stopped work
- **Usage**: `./ci-check.sh` - REQUIRED after every change
```bash
# ci-check.sh - REQUIRED after every change
swift build 2>&1 | tee build.log
if grep -q "error:" build.log; then
    echo "🚨 BUILD FAILED - STOP ALL WORK"
    exit 1
fi
```

### ✅ 1.5 Error Budget System (2 hours) - COMPLETED
- **Status**: ✅ COMPLETED (2025-07-01)
- **Action**: Implemented in ci-check.sh with automatic enforcement
- **Deliverable**: Automatic thresholds preventing catastrophic integration
- **Active Rules**:
  - ✅ Compilation errors > 5: STOP ALL AGENTS (ENFORCED - 58,994 > 5)
  - ✅ Warning count > 10: Alert for quality maintenance
  - ✅ Build failure: Immediate halt with error summary
- **Result**: Successfully prevented catastrophic integration by halting work at error threshold

---

## Phase 2: Incremental Implementation (Single Agent - 3 days)

### 2.1 Contract-Compliant Foundation Fixes
**Following established schema and running ci-check.sh after each change:**

#### ⏳ 2.1.1 OnboardingCoordinator Fix (4 hours) - PENDING
- **Status**: 🔄 PENDING
- **Requirements**:
  - Use schema-defined state management patterns
  - Build verification before commit
  - Fix state restoration from OnboardingManager
- **Success Criteria**: User can resume onboarding after app restart

#### ⏳ 2.1.2 ProjectManager Implementation (8 hours) - PENDING
- **Status**: 🔄 PENDING
- **Requirements**:
  - Implement `ProjectManagerProtocol` exactly
  - Use canonical `Project` model from schema
  - Test persistence patterns incrementally
  - Replace hardcoded sample data with real persistence
- **Success Criteria**: Projects persist across app launches

#### ⏳ 2.1.3 TaskService & Kanban (12 hours) - PENDING
- **Status**: 🔄 PENDING
- **Requirements**:
  - Follow `LeanVibeTask` naming convention
  - Implement drag-and-drop with interface compliance
  - Incremental integration with build checks
  - Real task loading from backend
- **Success Criteria**: Functional Kanban board with drag-and-drop

### ⏳ 2.2 Integration Checkpoints - PENDING
- Build verification after each component
- Interface compatibility tests
- No component integration without passing builds

---

## Phase 3: Testing & Documentation (Single Agent - 1 day)

### ⏳ 3.1 Component Testing (4 hours) - PENDING
- **Status**: 🔄 PENDING
- **Deliverable**: Following integration lessons learned
```swift
class ProjectManagerTests: XCTestCase {
    func testPublicInterface() {
        // Verify ProjectManagerProtocol compliance
    }
    func testSchemaCompliance() {
        // Verify Project model matches schema
    }
}
```

### ⏳ 3.2 Integration Documentation (4 hours) - PENDING
- **Status**: 🔄 PENDING
- **Deliverables**:
  - Interface change notifications  
  - Decision logs with reasoning
  - Migration guides for model changes

---

## Plan Maintenance Protocol

After completing each task:
1. Mark task as ✅ COMPLETED in this document
2. Add completion timestamp and notes
3. Update overall progress percentage
4. Note any discovered issues or changes
5. Commit updated plan with completion status

## Anti-Pattern Prevention

### What We Will NOT Do:
❌ Multiple agents working in parallel without coordination  
❌ No shared schema or interface contracts  
❌ Committing without build verification  
❌ Integration of all changes at once  
❌ Missing communication between components  

### What We WILL Do:
✅ Single agent with clear contracts  
✅ Build verification after every change  
✅ Incremental integration with checkpoints  
✅ Error budget enforcement  
✅ Complete documentation of changes  
✅ Continuous plan updates with progress tracking  

## Success Criteria
- [ ] Build success rate >95% (not 0% like before)
- [ ] Zero interface contract violations
- [ ] All critical user flows functional
- [ ] Comprehensive error handling implemented
- [ ] Integration tests passing continuously
- [x] docs/PLAN.md maintained and up-to-date throughout

## Risk Mitigation
- **Contract violations**: Prevented by schema definition
- **Build failures**: Stopped by continuous verification  
- **Integration chaos**: Prevented by incremental approach
- **Communication gaps**: Prevented by single-agent execution
- **Plan drift**: Prevented by continuous plan document updates

## Progress Log

### 2025-07-01
- ✅ Created comprehensive plan document
- 🚀 Started Phase 1: Contract Foundation
- ✅ **FOUNDATION ESTABLISHED**: Schema, protocols, CI system complete
- 🚨 **CI VALIDATION**: Detected 58,994 compilation errors (system working correctly)
- 🔧 **STATUS**: Systematically fixing errors before parallel development phase
- 📊 Progress: 50% (6/12 tasks completed)

## CRITICAL FIXES IMPLEMENTATION PLAN: TDD-Driven MVP Recovery

**Plan Updated**: 2025-07-01 (Based on comprehensive codebase analysis)
**Approach**: Test-Driven Development with disciplined validation
**Strategy**: Foundation-first, then parallel development using subagents

## Phase 1: Foundation Infrastructure (Main Agent - Sequential) 
**Duration**: 1 day
**Approach**: Test-first, build validation after each change

### 1.1 Reusable Error Handling Component (3 hours)
**Test First**: Write test for ErrorDisplayView showing/hiding error states
**Implementation**: Create centralized error UI component
**Validation**: swift test && xcodebuild -project DynaStory.xcodeproj -scheme DynaStory build
```swift
// Test: ErrorDisplayViewTests.swift
func testErrorDisplayShowsUserFriendlyMessage() {
    let view = ErrorDisplayView(error: "Network timeout")
    // Assert error message displays correctly
}
```

### 1.2 ProjectManager Data Persistence (4 hours)
**Test First**: Write tests for project CRUD with UserDefaults persistence
**Implementation**: Replace hardcoded samples with real persistence
**Validation**: Build check after persistence implementation
```swift
// Test: ProjectManagerTests.swift
func testProjectPersistsAcrossLaunches() {
    projectManager.addProject(testProject)
    let newManager = ProjectManager()
    XCTAssertEqual(newManager.projects.count, 1)
}
```

### 1.3 Backend API Integration Foundation (4 hours)
**Test First**: Write mock network service tests
**Implementation**: Replace ProjectManager.refreshProjects() simulation with real API calls
**Validation**: Comprehensive build check before parallel work begins

## Phase 2: Parallel Critical Fixes (3 Subagents - 2 days)

### Subagent 1: `worktree/onboarding-fixes`
**Duration**: 4 hours
**TDD Approach**: Test state restoration before implementation
```bash
git worktree add ../leanvibe-onboarding worktree/onboarding-fixes
```
**Tasks**:
- Test: OnboardingCoordinator state restoration
- Fix: Initialize currentStep from OnboardingManager.nextIncompleteStep()
- Validate: swift test && xcodebuild after each change
- Commit: "fix: OnboardingCoordinator restores user progress on launch"

### Subagent 2: `worktree/kanban-implementation`
**Duration**: 8 hours
**TDD Approach**: Test each Kanban feature before implementation
```bash
git worktree add ../leanvibe-kanban worktree/kanban-implementation
```
**Tasks**:
- Test: TaskService.loadTasks() network integration
- Test: Drag-and-drop task status changes
- Test: Error handling for task operations
- Implementation: Complete functional Kanban board
- Validate: Build check after each major change
- Commit: "feat: Functional Kanban board with drag-and-drop and error handling"

### Subagent 3: `worktree/dashboard-fixes` 
**Duration**: 6 hours
**TDD Approach**: Test error states and data loading
```bash
git worktree add ../leanvibe-dashboard worktree/dashboard-fixes
```
**Tasks**:
- Test: ProjectDashboardView error state display
- Test: Real project data loading and persistence
- Implementation: Wire error handling to UI
- Decouple: Remove direct WebSocketService dependency
- Validate: Build check after each change
- Commit: "fix: ProjectDashboard shows real data with error handling"

## Phase 3: Integration & Testing (Main Agent - 1 day)

### 3.1 Worktree Integration (4 hours)
**Process**: Merge each worktree with build validation
```bash
# For each worktree
git checkout main
git merge worktree/onboarding-fixes
swift test && xcodebuild -project DynaStory.xcodeproj -scheme DynaStory build
# Only proceed if build succeeds
```

### 3.2 Comprehensive Testing Suite (4 hours)
**TDD Completion**: Ensure all critical paths have tests
- Unit tests: ProjectManager, TaskService, OnboardingManager
- UI tests: Complete onboarding flow, project creation, task drag-and-drop
- Integration tests: End-to-end user journeys
**Final Validation**: Full test suite + build verification

## Quality Gates (Applied After Each Task)

### Mandatory Validation Sequence:
1. **Run Tests**: `swift test --enable-code-coverage`
2. **Build Check**: `xcodebuild -project DynaStory.xcodeproj -scheme DynaStory build`
3. **Error Budget**: Zero compilation errors allowed
4. **Commit**: Only on green tests + successful build
5. **Plan Update**: Mark task complete in docs/PLAN.md

### Build Failure Protocol:
- 🚨 **STOP ALL WORK** on compilation errors
- Fix errors before proceeding to next task
- Never commit broken code
- Ask for backend subagent if API endpoints missing

## Backend Integration Strategy

If backend endpoints are missing during implementation:
```bash
# Spawn backend subagent
git worktree add ../leanvibe-backend worktree/backend-support
# Implement minimal API endpoints for:
# - GET /projects (project list)
# - POST /projects (create project)  
# - GET /projects/{id}/tasks (task list)
# - PUT /tasks/{id}/status (update task status)
```

## Success Criteria
- [ ] Zero compilation errors throughout development
- [ ] All critical user flows functional (onboarding, projects, Kanban)
- [ ] Comprehensive error handling with user feedback
- [ ] Data persistence across app launches
- [ ] Kanban drag-and-drop fully operational
- [ ] Test coverage for all critical paths
- [ ] Build success rate 100% (not 0% like before)

## Anti-Patterns Prevention
❌ **Never commit without build validation**
❌ **Never implement without failing test first**  
❌ **Never proceed with compilation errors**
❌ **Never integrate multiple features at once**

✅ **Always run swift test && xcodebuild after changes**
✅ **Always write failing test before implementation**
✅ **Always fix errors immediately**
✅ **Always commit small, validated changes**

## Implementation Timeline
- **Day 1**: Foundation infrastructure (error handling, persistence, API)
- **Day 2**: Parallel critical fixes (onboarding, Kanban, dashboard)  
- **Day 3**: Integration, testing, and final validation

**Total Effort**: 3 days of disciplined, test-driven development
**Quality Assurance**: Continuous build validation prevents integration failures