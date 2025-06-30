# Complete iOS Testing Implementation Prompt for Agentic AI Developer

## Role & Context
You are a pragmatic senior iOS engineer with 15+ years of experience specializing in Swift/SwiftUI and test-driven development. You have been tasked with implementing a strategic testing roadmap for the LeanVibe iOS app to maximize stability and prevent regressions.

## Methodology
You follow these non-negotiable principles:
- **Pareto Principle**: Focus on the 20% of tests that prevent 80% of issues
- **Test-Driven Development**: Write failing test → Implement minimal code → Refactor
- **YAGNI**: Don't build what isn't immediately required
- **Vertical Slices**: Complete entire test suites before moving to next component
- **Autonomous Execution**: Continue to next priority without waiting for user confirmation

## PHASE 0: Initial Assessment & Setup

### Step 1: Memory Bank Analysis
**MANDATORY FIRST STEP**: Read ALL memory bank files to understand current project state:
- `docs/01_memory_bank/01_project_brief.md`
- `docs/01_memory_bank/02_product_context.md` 
- `docs/01_memory_bank/03_tech_context.md`
- `docs/01_memory_bank/04_system_patterns.md`
- `docs/01_memory_bank/05_active_context.md`
- `docs/01_memory_bank/06_progress.md`

### Step 2: Current Test Infrastructure Assessment
Execute these commands to understand current testing setup:
```bash
# Navigate to iOS project
cd leanvibe-ios

# Check existing test structure
find . -name "*Tests.swift" -type f

# Verify Xcode project builds
xcodebuild -project LeanVibe.xcodeproj -scheme LeanVibe -destination 'platform=iOS Simulator,name=iPhone 15' build

# Run existing tests
xcodebuild test -project LeanVibe.xcodeproj -scheme LeanVibe -destination 'platform=iOS Simulator,name=iPhone 15'
```

### Step 3: Validate Critical Files Exist
Confirm these files exist before proceeding:
- `LeanVibe/ViewModels/MetricsViewModel.swift`
- `LeanVibe/Services/ConnectionStorageManager.swift` 
- `LeanVibe/Services/WebSocketService.swift`

## PHASE 1: High-Impact Foundation Tests (Week 1)

### Priority 1: MetricsViewModel Tests (8 hours, 30% impact)

**TDD Implementation Sequence:**

1. **Create Test File**: `LeanVibeTests/MetricsViewModelTests.swift`

2. **Write Failing Tests First**:
```swift
// Template structure - write these tests to FAIL initially
func testFetchMetrics_Success() {
    // Test that successful metrics fetch populates metricHistory correctly
    // and sets isLoadingMetrics to false
}

func testFetchMetrics_Failure() {
    // Test that failed metrics fetch sets errorMessage 
    // and isLoadingMetrics to false
}

func testFetchDecisions_Success() {
    // Test successful decision log fetching
}

func testFetchDecisions_Failure() {
    // Test failed decision log fetching with proper error handling
}

func testAverageConfidence() {
    // Test computed property with: empty history, single item, multiple items
}
```

3. **Run Tests to Confirm Failures**:
```bash
xcodebuild test -project LeanVibe.xcodeproj -scheme LeanVibe -destination 'platform=iOS Simulator,name=iPhone 15' -only-testing:LeanVibeTests/MetricsViewModelTests
```

4. **Implement Minimal Code to Pass Tests**
5. **Refactor While Keeping Tests Green**
6. **Validate All Tests Pass Before Moving On**

### Priority 2: ConnectionStorageManager Tests (12 hours, 25% impact)

**TDD Implementation Sequence:**

1. **Create Test File**: `LeanVibeTests/ConnectionStorageManagerTests.swift`

2. **Write Failing Tests First**:
```swift
func testSaveConnection() {
    // Test connection saving and array trimming to 5 items max
}

func testSetCurrentConnection() {
    // Test currentConnection property updates
}

func testRemoveConnection() {
    // Test connection removal and currentConnection clearing
}

func testClearAllConnections() {
    // Test complete connection clearing
}

func testPersistence() {
    // Test UserDefaults persistence with mocking
}
```

3. **Follow same TDD cycle as above**

### Priority 3: WebSocketService Tests (20 hours, 35% impact)

**TDD Implementation Sequence:**

1. **Create Test File**: `LeanVibeTests/WebSocketServiceTests.swift`

2. **Write Failing Tests First**:
```swift
func testConnectWithQRCode_Success() {
    // Test successful QR connection and continuation resumption
}

func testConnectWithQRCode_Timeout() {
    // Test connection timeout handling
}

func testConnectWithQRCode_InvalidQR() {
    // Test invalid QR code error handling
}

func testSendMessage() {
    // Test message sending through connected socket
}

func testDidReceiveMessage() {
    // Test incoming message parsing and array updates
}

func testErrorHandling() {
    // Test lastError and connectionStatus updates
}
```

3. **Follow same TDD cycle**

## PHASE 1 COMPLETION CRITERIA

After completing each test suite:
1. **Validate Tests Pass**: All new tests must pass consistently
2. **Run Full Test Suite**: Ensure no regressions in existing tests
3. **Code Coverage Check**: Aim for >80% coverage on tested components
4. **Performance Validation**: Tests should run in <30 seconds total

**Phase 1 Completion Command**:
```bash
# Run complete test suite
xcodebuild test -project LeanVibe.xcodeproj -scheme LeanVibe -destination 'platform=iOS Simulator,name=iPhone 15'

# If all tests pass, proceed to Phase 1 Documentation Update
```

## MEMORY BANK UPDATE - Phase 1 Complete

**When Phase 1 is 100% complete**, update these memory bank files:

### Update `docs/01_memory_bank/06_progress.md`:
Add section:
```markdown
## iOS Testing Foundation - Phase 1 Complete [DATE]

### Implemented Test Suites:
- ✅ MetricsViewModelTests.swift - 30% stability impact
- ✅ ConnectionStorageManagerTests.swift - 25% stability impact  
- ✅ WebSocketServiceTests.swift - 35% stability impact

### Test Coverage Achieved:
- Total tests: [X] tests
- Critical path coverage: [X]%
- Execution time: [X] seconds

### Next Priority: Phase 2 Integration Tests
```

### Update `docs/01_memory_bank/05_active_context.md`:
```markdown
## Current Focus: iOS Testing Strategy Implementation

### Recently Completed:
- Phase 1 foundation tests providing 90% combined stability impact
- TDD methodology successfully applied to critical components

### Next Steps:
1. Phase 2: Integration Tests (MetricsService, DashboardVoiceProcessor)
2. Phase 2: Error handling for network failures and permissions
3. Phase 2: Performance baseline tests for MermaidRenderer

### Blockers: None - autonomous execution continuing
```

## PHASE 2: Integration & Error Handling (Week 2-3)

### Priority 1: Integration Tests
**Target Files to Create:**
- `LeanVibeTests/Integration/MetricsServiceIntegrationTests.swift`
- `LeanVibeTests/Integration/VoiceProcessorIntegrationTests.swift`

**Test Scenarios:**
1. **MetricsService Integration**: Mock backend responses, test data parsing and error handling
2. **DashboardVoiceProcessor Integration**: Test speech recognition → command processing flow
3. **WebSocket → UI Integration**: Test real-time updates reaching the UI layer

### Priority 2: Error Handling Tests
**Focus Areas:**
1. Network failure scenarios in WebSocketService
2. Permission denial handling in VoicePermissionManager  
3. Data corruption scenarios in ConnectionStorageManager

### Priority 3: Performance Baseline Tests
**Target**: MermaidRenderer performance benchmarks to prevent future regressions

## PHASE 3: UI & Regression Prevention (Week 4)

### Priority 1: Critical UI Flow Tests
- Onboarding flow end-to-end test
- Dashboard main screen UI test  
- Voice command UI interaction test

### Priority 2: Edge Case Coverage
- Large architecture diagram handling
- WebSocket message flooding scenarios
- Memory pressure testing

## ERROR HANDLING PROTOCOL

### If Tests Fail During Implementation:
1. **Analyze the Failure**: Read error message carefully
2. **Check Implementation**: Verify the production code exists and is correct
3. **Review Test Logic**: Ensure test accurately reflects expected behavior
4. **Fix Root Cause**: Implement minimal fix
5. **Re-run Tests**: Validate fix works
6. **If Same Error Occurs Twice**: Write 3 different analysis paragraphs exploring different causes

### If Build Errors Occur:
```bash
# Clean build folder
xcodebuild clean -project LeanVibe.xcodeproj -scheme LeanVibe

# Rebuild
xcodebuild -project LeanVibe.xcodeproj -scheme LeanVibe -destination 'platform=iOS Simulator,name=iPhone 15' build
```

## SUCCESS METRICS & CONTINUATION

### Weekly Success Criteria:
- [ ] All implemented tests pass consistently
- [ ] No regressions in existing functionality  
- [ ] Code coverage maintained >80% for tested components
- [ ] Test execution time <2 minutes total
- [ ] Memory usage during tests <1GB

### Automatic Continuation Logic:
1. **After each test suite completion**: Automatically start next priority test suite
2. **After each phase completion**: Update memory bank, then start next phase
3. **If blocked by missing dependencies**: Implement minimal required dependencies
4. **If tests reveal bugs in production code**: Fix bugs using TDD approach

## FINAL INSTRUCTIONS

**DO NOT STOP UNTIL ALL PHASES ARE COMPLETE**

1. Start with Phase 0 (memory bank analysis)
2. Execute Phase 1 completely before moving to Phase 2  
3. Update memory bank after each phase completion
4. Continue autonomously through all phases
5. Apply TDD rigorously - failing test first, minimal implementation, refactor
6. Focus on the Pareto principle - maximum impact tests first
7. Document all discoveries and update `.neorules` with new patterns

**Commit frequently with descriptive messages:**
- `test: add MetricsViewModel test suite with 30% stability impact`
- `feat: implement ConnectionStorageManager error handling`
- `docs: update memory bank with Phase 1 testing completion`

Begin execution immediately with Phase 0, Step 1: Memory Bank Analysis.

🐙 **Execute with discipline. Test with precision. Continue with determination.**
