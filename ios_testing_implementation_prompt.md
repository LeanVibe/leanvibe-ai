# iOS Testing Implementation - Autonomous Execution Prompt

## Objective
You are an elite iOS engineer implementing a comprehensive testing strategy for the LeanVibe iOS app based on Gemini CLI analysis results. Focus on preventing MVP launch blockers and ensuring production stability through pragmatic testing implementation.

## Prerequisites
- Gemini analysis completed with `gemini_ios_comprehensive_testing_analysis.md`
- iOS development environment ready (Xcode, iOS Simulator)
- Understanding of SwiftUI, XCTest, and iOS testing frameworks

## Phase 0: Memory Bank Analysis & iOS Assessment

### Step 0.1: Read Memory Bank Files
```bash
# Read all memory bank files to understand current project state
find docs/01_memory_bank/ -name "*.md" -exec cat {} \;
```

### Step 0.2: iOS Codebase Health Check
```bash
cd leanvibe-ios

# Check current build status
xcodebuild -project LeanVibe.xcodeproj -scheme LeanVibe -destination 'platform=iOS Simulator,name=iPhone 15' build

# Run existing tests to establish baseline
xcodebuild test -project LeanVibe.xcodeproj -scheme LeanVibe -destination 'platform=iOS Simulator,name=iPhone 15'

# Check for compile warnings and errors
xcodebuild -project LeanVibe.xcodeproj -scheme LeanVibe -destination 'platform=iOS Simulator,name=iPhone 15' build 2>&1 | grep -E "(warning|error):"
```

### Step 0.3: Critical Assessment Based on Gemini Analysis
```bash
# Document current state in active-context.md
echo "## iOS Testing Implementation Status - $(date)" >> docs/01_memory_bank/05_active_context.md
echo "### Baseline Assessment:" >> docs/01_memory_bank/05_active_context.md
```

**Key Questions to Address:**
1. Which critical issues from Gemini analysis block MVP launch?
2. What is the current test coverage baseline?
3. Which user journeys are completely untested?
4. What integration points with backend are most fragile?
5. Which performance bottlenecks could cause App Store rejection?

## Phase 1: Critical Stability Tests (High Impact - Week 1)

### Phase 1A: Foundation Tests for Core Components

Based on typical iOS architecture, prioritize testing:

#### 1.1: Core ViewModel Testing
```swift
// Create: LeanVibeTests/ViewModels/MetricsViewModelTests.swift
@testable import LeanVibe
import XCTest
import Combine

class MetricsViewModelTests: XCTestCase {
    var viewModel: MetricsViewModel!
    var cancellables: Set<AnyCancellable>!
    
    override func setUp() {
        super.setUp()
        viewModel = MetricsViewModel()
        cancellables = Set<AnyCancellable>()
    }
    
    func testInitialState() {
        // Test initial state is correct
        XCTAssertFalse(viewModel.isLoading)
        XCTAssertTrue(viewModel.metrics.isEmpty)
    }
    
    func testMetricsLoading() {
        // Test loading state management
        let expectation = XCTestExpectation(description: "Metrics loaded")
        
        viewModel.$isLoading
            .dropFirst()
            .sink { isLoading in
                if !isLoading {
                    expectation.fulfill()
                }
            }
            .store(in: &cancellables)
        
        viewModel.loadMetrics()
        wait(for: [expectation], timeout: 5.0)
    }
    
    func testErrorHandling() {
        // Test error state handling
        // Implementation based on actual error handling patterns
    }
}
```

#### 1.2: Backend Communication Testing
```swift
// Create: LeanVibeTests/Services/BackendServiceTests.swift
@testable import LeanVibe
import XCTest

class BackendServiceTests: XCTestCase {
    var service: BackendService!
    
    override func setUp() {
        super.setUp()
        service = BackendService()
    }
    
    func testWebSocketConnection() {
        let expectation = XCTestExpectation(description: "WebSocket connected")
        
        service.connect { result in
            switch result {
            case .success:
                expectation.fulfill()
            case .failure(let error):
                XCTFail("Connection failed: \(error)")
            }
        }
        
        wait(for: [expectation], timeout: 10.0)
    }
    
    func testReconnectionLogic() {
        // Test automatic reconnection after disconnection
    }
    
    func testMessageSerialization() {
        // Test proper encoding/decoding of messages
    }
}
```

#### 1.3: Data Persistence Testing
```swift
// Create: LeanVibeTests/Storage/DataStorageTests.swift
@testable import LeanVibe
import XCTest

class DataStorageTests: XCTestCase {
    var storage: DataStorage!
    
    override func setUp() {
        super.setUp()
        storage = DataStorage(testing: true)  // Use test database
    }
    
    override func tearDown() {
        storage.clearAllData()
        super.tearDown()
    }
    
    func testProjectPersistence() {
        // Test project data saving and retrieval
        let project = Project(id: "test", name: "Test Project")
        
        storage.save(project: project)
        let retrieved = storage.loadProject(id: "test")
        
        XCTAssertEqual(retrieved?.name, "Test Project")
    }
    
    func testSettingsPersistence() {
        // Test settings persistence across app restarts
    }
}
```

### Phase 1B: Critical User Journey Testing

#### 1.4: Onboarding Flow Testing
```swift
// Create: LeanVibeTests/Features/OnboardingTests.swift
@testable import LeanVibe
import XCTest

class OnboardingTests: XCTestCase {
    func testOnboardingCompletion() {
        // Test complete onboarding flow
        let onboardingManager = OnboardingManager()
        
        XCTAssertFalse(onboardingManager.isComplete)
        
        onboardingManager.completeStep(.welcome)
        onboardingManager.completeStep(.permissions)
        onboardingManager.completeStep(.backendConnection)
        
        XCTAssertTrue(onboardingManager.isComplete)
    }
    
    func testOnboardingInterruption() {
        // Test recovery from interrupted onboarding
    }
    
    func testPermissionHandling() {
        // Test proper permission request handling
    }
}
```

#### 1.5: Navigation Testing
```swift
// Create: LeanVibeTests/Navigation/NavigationTests.swift
@testable import LeanVibe
import XCTest
import SwiftUI

class NavigationTests: XCTestCase {
    func testTabNavigation() {
        // Test main tab navigation works correctly
    }
    
    func testDeepLinking() {
        // Test deep link handling
    }
    
    func testBackButtonBehavior() {
        // Test navigation stack management
    }
}
```

## Phase 2: Integration & Error Handling Tests (Week 2)

### Phase 2A: Backend Integration Testing

#### 2.1: API Integration Tests
```swift
// Create: LeanVibeTests/Integration/APIIntegrationTests.swift
@testable import LeanVibe
import XCTest

class APIIntegrationTests: XCTestCase {
    var apiClient: APIClient!
    
    override func setUp() {
        super.setUp()
        apiClient = APIClient(baseURL: TestConfig.backendURL)
    }
    
    func testTaskCreation() {
        let expectation = XCTestExpectation(description: "Task created")
        
        let task = Task(title: "Test Task", description: "Test Description")
        
        apiClient.createTask(task) { result in
            switch result {
            case .success(let createdTask):
                XCTAssertNotNil(createdTask.id)
                expectation.fulfill()
            case .failure(let error):
                XCTFail("Task creation failed: \(error)")
            }
        }
        
        wait(for: [expectation], timeout: 10.0)
    }
    
    func testErrorHandling() {
        // Test proper error handling for API failures
    }
    
    func testOfflineMode() {
        // Test app behavior when backend is unreachable
    }
}
```

#### 2.2: WebSocket Event Testing
```swift
// Create: LeanVibeTests/Integration/WebSocketEventTests.swift
@testable import LeanVibe
import XCTest

class WebSocketEventTests: XCTestCase {
    func testRealTimeUpdates() {
        // Test real-time event handling
    }
    
    func testEventSerialization() {
        // Test proper event encoding/decoding
    }
    
    func testConnectionRecovery() {
        // Test recovery from connection drops
    }
}
```

### Phase 2B: Feature Integration Testing

#### 2.3: Kanban Integration Tests
```swift
// Create: LeanVibeTests/Features/KanbanIntegrationTests.swift
@testable import LeanVibe
import XCTest

class KanbanIntegrationTests: XCTestCase {
    func testTaskDragAndDrop() {
        // Test task movement between columns
    }
    
    func testRealTimeSync() {
        // Test task updates sync with backend
    }
    
    func testConflictResolution() {
        // Test handling of concurrent task modifications
    }
}
```

#### 2.4: Voice Interface Tests
```swift
// Create: LeanVibeTests/Features/VoiceInterfaceTests.swift
@testable import LeanVibe
import XCTest

class VoiceInterfaceTests: XCTestCase {
    func testVoiceCommandRecognition() {
        // Test speech recognition accuracy
    }
    
    func testPermissionHandling() {
        // Test microphone permission management
    }
    
    func testOfflineVoiceCommands() {
        // Test fallback for network issues
    }
}
```

## Phase 3: UI & Performance Tests (Week 3-4)

### Phase 3A: SwiftUI View Testing

#### 3.1: View Rendering Tests
```swift
// Create: LeanVibeTests/Views/ViewRenderingTests.swift
import ViewInspector
@testable import LeanVibe
import XCTest
import SwiftUI

class ViewRenderingTests: XCTestCase {
    func testDashboardViewRendering() throws {
        let view = DashboardView()
        let body = try view.inspect().body
        
        // Test view structure
        XCTAssertNoThrow(try body.find(ViewType.NavigationView.self))
    }
    
    func testErrorStateRendering() throws {
        let viewModel = MetricsViewModel()
        viewModel.error = NetworkError.connectionFailed
        
        let view = MetricsView(viewModel: viewModel)
        let errorMessage = try view.inspect().find(text: "Connection Failed")
        
        XCTAssertNotNil(errorMessage)
    }
    
    func testLoadingStateRendering() throws {
        // Test loading state UI
    }
}
```

#### 3.2: Performance Tests
```swift
// Create: LeanVibeTests/Performance/PerformanceTests.swift
@testable import LeanVibe
import XCTest

class PerformanceTests: XCTestCase {
    func testAppLaunchTime() {
        measure {
            // Test app launch performance
            let app = XCUIApplication()
            app.launch()
        }
    }
    
    func testMemoryUsage() {
        // Test memory usage patterns
        let viewController = UIHostingController(rootView: ContentView())
        
        measure(metrics: [XCTMemoryMetric()]) {
            // Perform memory-intensive operations
            viewController.loadView()
        }
    }
    
    func testLargeDatasetRendering() {
        // Test performance with large datasets
    }
}
```

### Phase 3B: Edge Case & Regression Tests

#### 3.3: Edge Case Testing
```swift
// Create: LeanVibeTests/EdgeCases/EdgeCaseTests.swift
@testable import LeanVibe
import XCTest

class EdgeCaseTests: XCTestCase {
    func testEmptyDataStates() {
        // Test UI with no data
    }
    
    func testLargeDataSets() {
        // Test with large amounts of data
    }
    
    func testNetworkTimeouts() {
        // Test long network request handling
    }
    
    func testLowMemoryConditions() {
        // Test app behavior under memory pressure
    }
}
```

#### 3.4: Accessibility Tests
```swift
// Create: LeanVibeTests/Accessibility/AccessibilityTests.swift
@testable import LeanVibe
import XCTest

class AccessibilityTests: XCTestCase {
    func testVoiceOverSupport() {
        // Test VoiceOver compatibility
    }
    
    func testDynamicTypeSupport() {
        // Test text scaling support
    }
    
    func testHighContrastSupport() {
        // Test high contrast mode
    }
}
```

## Testing Infrastructure Setup

### Test Configuration
```swift
// Create: LeanVibeTests/TestConfig.swift
import Foundation

struct TestConfig {
    static let backendURL = "http://localhost:8000"
    static let testTimeout: TimeInterval = 30.0
    static let simulatorDevice = "iPhone 15"
    
    static var isRunningTests: Bool {
        return ProcessInfo.processInfo.environment["XCTestConfigurationFilePath"] != nil
    }
}
```

### Mock Services
```swift
// Create: LeanVibeTests/Mocks/MockBackendService.swift
@testable import LeanVibe
import Foundation
import Combine

class MockBackendService: BackendServiceProtocol {
    var shouldFailConnection = false
    var mockTasks: [Task] = []
    
    func connect(completion: @escaping (Result<Void, Error>) -> Void) {
        if shouldFailConnection {
            completion(.failure(NetworkError.connectionFailed))
        } else {
            completion(.success(()))
        }
    }
    
    func createTask(_ task: Task, completion: @escaping (Result<Task, Error>) -> Void) {
        var newTask = task
        newTask.id = UUID().uuidString
        mockTasks.append(newTask)
        completion(.success(newTask))
    }
    
    // Implement other protocol methods
}
```

## Quality Gates & Validation

### After Phase 1 (Critical Tests):
```bash
# Run critical test suite
xcodebuild test -project LeanVibe.xcodeproj -scheme LeanVibe -destination 'platform=iOS Simulator,name=iPhone 15' -only-testing:LeanVibeTests/ViewModels
xcodebuild test -project LeanVibe.xcodeproj -scheme LeanVibe -destination 'platform=iOS Simulator,name=iPhone 15' -only-testing:LeanVibeTests/Services
xcodebuild test -project LeanVibe.xcodeproj -scheme LeanVibe -destination 'platform=iOS Simulator,name=iPhone 15' -only-testing:LeanVibeTests/Features/OnboardingTests

# Verify no critical failures
echo "✅ Phase 1 Critical Tests Complete"
```

### After Phase 2 (Integration Tests):
```bash
# Run integration test suite
xcodebuild test -project LeanVibe.xcodeproj -scheme LeanVibe -destination 'platform=iOS Simulator,name=iPhone 15' -only-testing:LeanVibeTests/Integration

# Test with real backend if available
if curl -f http://localhost:8000/health; then
    echo "✅ Backend available - running full integration tests"
    # Run tests that require backend
else
    echo "⚠️  Backend not available - running mock-only tests"
fi
```

### After Phase 3 (Complete Test Suite):
```bash
# Run full test suite with coverage
xcodebuild test -project LeanVibe.xcodeproj -scheme LeanVibe -destination 'platform=iOS Simulator,name=iPhone 15' -enableCodeCoverage YES

# Performance benchmarking
xcodebuild test -project LeanVibe.xcodeproj -scheme LeanVibe -destination 'platform=iOS Simulator,name=iPhone 15' -only-testing:LeanVibeTests/Performance

# Accessibility validation
xcodebuild test -project LeanVibe.xcodeproj -scheme LeanVibe -destination 'platform=iOS Simulator,name=iPhone 15' -only-testing:LeanVibeTests/Accessibility
```

## Final Success Criteria

### MVP Launch Readiness:
- [ ] **Core user journey tests pass** (onboarding → dashboard → key features)
- [ ] **Backend integration tests pass** (API calls, WebSocket events)
- [ ] **Error handling validated** (network failures, permission denials)
- [ ] **Performance benchmarks met** (launch time, memory usage, rendering)
- [ ] **Accessibility standards met** (VoiceOver, Dynamic Type)
- [ ] **No critical crashes** in test scenarios

### Test Coverage Targets:
- [ ] **ViewModels**: >90% test coverage
- [ ] **Services**: >85% test coverage  
- [ ] **Critical user flows**: 100% test coverage
- [ ] **Error handling**: >80% test coverage
- [ ] **Integration points**: 100% test coverage

## Memory Bank Updates

### After Phase 1:
Update `docs/01_memory_bank/06_progress.md`:
```markdown
## iOS Testing Implementation - Phase 1 Complete
- ✅ Critical ViewModels tested (MetricsViewModel, etc.)
- ✅ Backend service integration tested
- ✅ Core data persistence validated
- ✅ Onboarding flow tested
- ✅ Basic navigation tested
- 🔄 Integration tests in progress (Phase 2)
```

### After Phase 2:
```markdown
## iOS Testing Implementation - Phase 2 Complete
- ✅ API integration tests implemented
- ✅ WebSocket event handling tested
- ✅ Kanban board integration validated
- ✅ Voice interface core functionality tested
- 🔄 UI and performance tests in progress (Phase 3)
```

### After Phase 3:
```markdown
## iOS Testing Implementation - Complete ✅
- ✅ Comprehensive test suite implemented
- ✅ Performance benchmarks established
- ✅ Accessibility standards validated
- ✅ Edge cases and error handling covered
- ✅ MVP launch readiness achieved

### Test Metrics:
- Total Tests: [X]
- Coverage: [X]%
- Performance: Launch <3s, Memory <200MB
- Accessibility: VoiceOver compatible
```

## Error Handling & Recovery Protocol

### If Critical Tests Fail:
1. **Identify root cause** - is it a test issue or implementation issue?
2. **Fix implementation first** - make the test pass correctly
3. **Refactor test if needed** - ensure test accurately reflects requirements
4. **Document any architectural changes** needed
5. **Re-run full test suite** to ensure no regressions

### If Performance Tests Fail:
1. **Profile the specific performance issue** using Instruments
2. **Identify bottlenecks** in rendering, memory, or computation
3. **Implement targeted optimizations** 
4. **Re-validate performance benchmarks**
5. **Update performance documentation**

### If Integration Tests Fail:
1. **Check backend connectivity** and API compatibility
2. **Verify data serialization** between iOS and backend
3. **Test with mock services** to isolate iOS-specific issues
4. **Update integration protocols** if needed

## Autonomous Execution Protocol

### Start Immediately:
```bash
cd leanvibe-ios
# Begin Phase 0 - Memory bank analysis and iOS assessment
```

### Execution Sequence:
1. **Phase 0**: Memory bank analysis + iOS health check
2. **Phase 1**: Critical stability tests (ViewModels, Services, Core flows)
3. **Phase 2**: Integration tests (Backend, Features, WebSocket)
4. **Phase 3**: UI, Performance, and Edge case tests
5. **Memory Bank Updates**: After each phase completion
6. **Quality Gates**: Validate success criteria at each phase

### Commit Strategy:
```bash
# After each test suite completion
git add LeanVibeTests/
git commit -m "feat(ios-tests): implement [Phase X] testing suite

- Add comprehensive tests for [component/feature]
- Establish [performance/quality] benchmarks  
- Validate [user journey/integration] scenarios
- Coverage: [X]% for [component]

Resolves: MVP testing requirements for [area]"
```

This autonomous execution protocol ensures systematic implementation of comprehensive iOS testing that prevents MVP launch blockers and establishes long-term stability.
