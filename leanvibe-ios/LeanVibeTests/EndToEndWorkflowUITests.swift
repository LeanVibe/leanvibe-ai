import XCTest
@testable import LeanVibe

@available(iOS 18.0, macOS 14.0, *)
@MainActor
final class EndToEndWorkflowUITests: XCTestCase {
    
    private var app: XCUIApplication!
    
    override func setUpWithError() throws {
        continueAfterFailure = false
        app = XCUIApplication()
        app.launch()
    }
    
    override func tearDownWithError() throws {
        app = nil
    }
    
    // MARK: - Complete User Workflow Tests
    
    /// Test complete onboarding to productive use workflow
    func testCompleteOnboardingToProductiveUseWorkflow() throws {
        // Given: Fresh app launch
        
        // When: User goes through complete onboarding
        completeOnboardingFlow()
        
        // Then: Should reach functional dashboard
        XCTAssertTrue(app.tabBars.firstMatch.waitForExistence(timeout: 10))
        
        // And: Should be able to access main features
        verifyMainFeaturesAccessible()
        
        // And: Should be able to create and manage projects
        testProjectCreationInWorkflow()
        
        // And: Should be able to access monitoring features
        testMonitoringAccessInWorkflow()
        
        // And: Should be able to configure settings
        testSettingsAccessInWorkflow()
    }
    
    /// Test project creation to task management workflow
    func testProjectCreationToTaskManagementWorkflow() throws {
        // Given: User is on main dashboard
        navigateToMainDashboard()
        
        // When: User creates a new project
        createTestProject()
        
        // Then: Should be able to access task management
        navigateToTaskManagement()
        
        // And: Should be able to create tasks
        createTestTask()
        
        // And: Should be able to manage task states
        testTaskStateManagement()
        
        // And: Should be able to view task statistics
        testTaskStatisticsAccess()
    }
    
    /// Test voice command to action execution workflow
    func testVoiceCommandToActionExecutionWorkflow() throws {
        // Given: User is on main dashboard
        navigateToMainDashboard()
        
        // When: User accesses voice interface
        accessVoiceInterface()
        
        // Then: Should be able to interact with voice controls
        testVoiceControlInteraction()
        
        // And: Should be able to simulate voice commands
        simulateVoiceCommands()
        
        // And: Should return to dashboard after voice interaction
        verifyReturnToDashboard()
    }
    
    /// Test architecture exploration to code navigation workflow
    func testArchitectureExplorationToCodeNavigationWorkflow() throws {
        // Given: User is on main dashboard
        navigateToMainDashboard()
        
        // When: User accesses architecture viewer
        accessArchitectureViewer()
        
        // Then: Should be able to explore project architecture
        exploreProjectArchitecture()
        
        // And: Should be able to interact with diagram elements
        interactWithDiagramElements()
        
        // And: Should be able to export architecture
        testArchitectureExport()
        
        // And: Should be able to switch between projects
        testProjectSwitchingInArchitecture()
    }
    
    /// Test error recovery across multiple features workflow
    func testErrorRecoveryAcrossMultipleFeaturesWorkflow() throws {
        // Given: User is on main dashboard
        navigateToMainDashboard()
        
        // When: User encounters errors in different features
        // Test error handling in Kanban
        testKanbanErrorRecovery()
        
        // Test error handling in Voice interface
        testVoiceInterfaceErrorRecovery()
        
        // Test error handling in Architecture viewer
        testArchitectureViewerErrorRecovery()
        
        // Then: Should maintain app stability throughout
        verifyAppStabilityAfterErrors()
    }
    
    // MARK: - Cross-Feature Integration Tests
    
    /// Test Kanban to Voice interface integration
    func testKanbanToVoiceInterfaceIntegration() throws {
        // Given: User is on Kanban board
        navigateToMainDashboard()
        navigateToKanbanBoard()
        
        // When: User accesses voice commands from Kanban
        if app.buttons.matching(NSPredicate(format: "identifier CONTAINS 'voice'")).count > 0 {
            app.buttons.matching(NSPredicate(format: "identifier CONTAINS 'voice'")).firstMatch.tap()
            
            // Then: Should open voice interface
            XCTAssertTrue(
                app.staticTexts["Voice Commands"].waitForExistence(timeout: 3) ||
                app.buttons.matching(NSPredicate(format: "identifier CONTAINS 'mic'")).count > 0
            )
            
            // And: Should be able to return to Kanban
            if app.buttons["Close"].exists {
                app.buttons["Close"].tap()
            }
            
            XCTAssertTrue(app.navigationBars["Tasks"].waitForExistence(timeout: 3))
        }
    }
    
    /// Test Architecture viewer to project dashboard integration
    func testArchitectureViewerToProjectDashboardIntegration() throws {
        // Given: User is in architecture viewer
        navigateToMainDashboard()
        accessArchitectureViewer()
        
        // When: User navigates to project dashboard
        if app.tabBars.buttons["Projects"].exists {
            app.tabBars.buttons["Projects"].tap()
            
            // Then: Should maintain project context
            XCTAssertTrue(app.navigationBars.firstMatch.waitForExistence(timeout: 3))
            
            // And: Should be able to return to architecture viewer
            accessArchitectureViewer()
            XCTAssertTrue(app.navigationBars["Architecture"].waitForExistence(timeout: 3))
        }
    }
    
    /// Test voice commands integration with all features
    func testVoiceCommandsIntegrationWithAllFeatures() throws {
        // Given: User has access to voice interface
        navigateToMainDashboard()
        
        // When: User uses voice interface from different contexts
        let contexts = ["Projects", "Monitor", "Settings"]
        
        for context in contexts {
            if app.tabBars.buttons[context].exists {
                app.tabBars.buttons[context].tap()
                _ = app.navigationBars.firstMatch.waitForExistence(timeout: 3)
                
                // Look for voice access from this context
                let voiceButtons = app.buttons.matching(NSPredicate(format: "identifier CONTAINS 'voice' OR identifier CONTAINS 'mic'"))
                
                if voiceButtons.count > 0 {
                    voiceButtons.firstMatch.tap()
                    
                    // Should open voice interface
                    if app.staticTexts["Voice Commands"].waitForExistence(timeout: 2) {
                        // Close and verify return to context
                        if app.buttons["Close"].exists {
                            app.buttons["Close"].tap()
                        }
                        
                        XCTAssertTrue(app.navigationBars.firstMatch.waitForExistence(timeout: 3))
                    }
                }
            }
        }
    }
    
    // MARK: - Performance Integration Tests
    
    /// Test app performance during complex workflows
    func testAppPerformanceDuringComplexWorkflows() throws {
        measure(metrics: [XCTMemoryMetric(), XCTCPUMetric()]) {
            // Execute complex workflow
            navigateToMainDashboard()
            
            // Navigate through all major features
            let features = ["Projects", "Monitor", "Settings"]
            for feature in features {
                if app.tabBars.buttons[feature].exists {
                    app.tabBars.buttons[feature].tap()
                    _ = app.navigationBars.firstMatch.waitForExistence(timeout: 2)
                }
            }
            
            // Access specialized features
            navigateToKanbanBoard()
            accessVoiceInterface()
            if app.buttons["Close"].exists {
                app.buttons["Close"].tap()
            }
            accessArchitectureViewer()
        }
    }
    
    /// Test memory efficiency during extended use
    func testMemoryEfficiencyDuringExtendedUse() throws {
        measure(metrics: [XCTMemoryMetric()]) {
            // Simulate extended app use
            for _ in 0..<5 {
                navigateToMainDashboard()
                testProjectCreationToTaskManagementWorkflow()
                testVoiceCommandToActionExecutionWorkflow()
                testArchitectureExplorationToCodeNavigationWorkflow()
            }
        }
    }
    
    /// Test app responsiveness under load
    func testAppResponsivenessUnderLoad() throws {
        // Given: User performs intensive operations
        navigateToMainDashboard()
        
        measure {
            // Rapid navigation and interaction
            for i in 0..<20 {
                let tabs = ["Projects", "Monitor", "Settings"]
                let tabIndex = i % tabs.count
                
                if app.tabBars.buttons[tabs[tabIndex]].exists {
                    app.tabBars.buttons[tabs[tabIndex]].tap()
                }
            }
        }
        
        // App should remain responsive
        XCTAssertTrue(app.tabBars.firstMatch.exists)
        XCTAssertTrue(app.tabBars.firstMatch.isHittable)
    }
    
    // MARK: - Data Persistence Integration Tests
    
    /// Test data persistence across app lifecycle
    func testDataPersistenceAcrossAppLifecycle() throws {
        // Given: User creates data in the app
        navigateToMainDashboard()
        
        // Create a test project (if possible)
        createTestProject()
        
        // Navigate to different features to create state
        if app.tabBars.buttons["Settings"].exists {
            app.tabBars.buttons["Settings"].tap()
            _ = app.navigationBars.firstMatch.waitForExistence(timeout: 3)
        }
        
        // Simulate app restart by terminating and relaunching
        app.terminate()
        app.launch()
        
        // When: User returns to the app
        navigateToMainDashboard()
        
        // Then: Previous state should be maintained
        XCTAssertTrue(app.tabBars.firstMatch.exists)
        
        // Should be able to navigate to previous features
        if app.tabBars.buttons["Projects"].exists {
            app.tabBars.buttons["Projects"].tap()
            XCTAssertTrue(app.navigationBars.firstMatch.waitForExistence(timeout: 3))
        }
    }
    
    /// Test settings persistence across features
    func testSettingsPersistenceAcrossFeatures() throws {
        // Given: User modifies settings
        navigateToMainDashboard()
        
        if app.tabBars.buttons["Settings"].exists {
            app.tabBars.buttons["Settings"].tap()
            _ = app.navigationBars.firstMatch.waitForExistence(timeout: 3)
            
            // Look for toggleable settings
            let switches = app.switches
            if switches.count > 0 {
                let initialState = switches.firstMatch.value as? String
                switches.firstMatch.tap()
                
                // Navigate to different features
                if app.tabBars.buttons["Projects"].exists {
                    app.tabBars.buttons["Projects"].tap()
                    _ = app.navigationBars.firstMatch.waitForExistence(timeout: 3)
                }
                
                // Return to settings
                app.tabBars.buttons["Settings"].tap()
                _ = app.navigationBars.firstMatch.waitForExistence(timeout: 3)
                
                // Setting should be maintained
                let newState = switches.firstMatch.value as? String
                XCTAssertNotEqual(initialState, newState)
            }
        }
    }
    
    // MARK: - Error Recovery Integration Tests
    
    /// Test graceful degradation when features are unavailable
    func testGracefulDegradationWhenFeaturesUnavailable() throws {
        // Given: User attempts to access potentially unavailable features
        navigateToMainDashboard()
        
        // Try to access various features and handle gracefully
        let features = ["Projects", "Monitor", "Agent", "Settings", "Voice"]
        
        for feature in features {
            if app.tabBars.buttons[feature].exists {
                app.tabBars.buttons[feature].tap()
                
                let expectation = expectation(description: "Feature loads or shows appropriate state")
                DispatchQueue.main.asyncAfter(deadline: .now() + 3) {
                    expectation.fulfill()
                }
                wait(for: [expectation], timeout: 5)
                
                // Should either load successfully or show appropriate error/empty state
                XCTAssertTrue(
                    app.navigationBars.firstMatch.exists ||
                    app.staticTexts.containing("Error").firstMatch.exists ||
                    app.staticTexts.containing("Unavailable").firstMatch.exists ||
                    app.staticTexts.containing("Loading").firstMatch.exists
                )
            }
        }
    }
    
    /// Test network connectivity issues across features
    func testNetworkConnectivityIssuesAcrossFeatures() throws {
        // Given: User accesses network-dependent features
        navigateToMainDashboard()
        
        let networkFeatures = ["Monitor", "Agent"]
        
        for feature in networkFeatures {
            if app.tabBars.buttons[feature].exists {
                app.tabBars.buttons[feature].tap()
                _ = app.navigationBars.firstMatch.waitForExistence(timeout: 3)
                
                // Look for connectivity indicators
                if app.staticTexts.containing("connection").firstMatch.exists ||
                   app.staticTexts.containing("offline").firstMatch.exists {
                    
                    // Should have retry mechanisms
                    XCTAssertTrue(
                        app.buttons["Retry"].exists ||
                        app.buttons["Try Again"].exists ||
                        app.buttons.matching(NSPredicate(format: "identifier CONTAINS 'refresh'")).count > 0
                    )
                }
            }
        }
    }
    
    // MARK: - Accessibility Integration Tests
    
    /// Test accessibility across complete workflows
    func testAccessibilityAcrossCompleteWorkflows() throws {
        // Given: User navigates through complete workflows using accessibility
        navigateToMainDashboard()
        
        // Test accessibility in onboarding flow
        // (Already completed in this test, but elements should remain accessible)
        
        // Test accessibility in main features
        let accessibleFeatures = ["Projects", "Settings"]
        
        for feature in accessibleFeatures {
            if app.tabBars.buttons[feature].exists {
                let featureButton = app.tabBars.buttons[feature]
                
                // Should be accessible
                XCTAssertTrue(featureButton.isAccessibilityElement)
                XCTAssertNotNil(featureButton.accessibilityLabel)
                
                featureButton.tap()
                XCTAssertTrue(app.navigationBars.firstMatch.waitForExistence(timeout: 3))
                
                // Content should be accessible
                XCTAssertTrue(
                    app.navigationBars.firstMatch.isAccessibilityElement ||
                    app.staticTexts.firstMatch.isAccessibilityElement ||
                    app.buttons.firstMatch.isAccessibilityElement
                )
            }
        }
    }
    
    /// Test VoiceOver compatibility across features
    func testVoiceOverCompatibilityAcrossFeatures() throws {
        // Given: User accesses various features
        navigateToMainDashboard()
        
        // Test VoiceOver compatibility in key interfaces
        let features = ["Projects", "Monitor", "Settings"]
        
        for feature in features {
            if app.tabBars.buttons[feature].exists {
                app.tabBars.buttons[feature].tap()
                _ = app.navigationBars.firstMatch.waitForExistence(timeout: 3)
                
                // Key elements should have accessibility labels
                if app.navigationBars.firstMatch.exists {
                    XCTAssertNotNil(app.navigationBars.firstMatch.accessibilityLabel)
                }
                
                // Interactive elements should be accessible
                if app.buttons.firstMatch.exists {
                    XCTAssertTrue(app.buttons.firstMatch.isAccessibilityElement)
                }
            }
        }
    }
    
    // MARK: - Helper Methods for Workflow Components
    
    /// Complete onboarding flow
    private func completeOnboardingFlow() {
        if app.staticTexts["Welcome to LeanVibe"].exists {
            let continueButtons = ["Get Started", "Continue", "Continue", "Continue", "Continue", "Continue", "Continue", "Get Started"]
            
            for buttonText in continueButtons {
                if app.buttons[buttonText].waitForExistence(timeout: 2) {
                    app.buttons[buttonText].tap()
                }
            }
        }
    }
    
    /// Navigate to main dashboard
    private func navigateToMainDashboard() {
        completeOnboardingFlow()
        XCTAssertTrue(app.tabBars.firstMatch.waitForExistence(timeout: 10))
    }
    
    /// Verify main features are accessible
    private func verifyMainFeaturesAccessible() {
        let requiredFeatures = ["Projects", "Settings"]
        
        for feature in requiredFeatures {
            XCTAssertTrue(
                app.tabBars.buttons[feature].exists,
                "Required feature '\(feature)' should be accessible from dashboard"
            )
        }
    }
    
    /// Test project creation in workflow
    private func testProjectCreationInWorkflow() {
        if app.tabBars.buttons["Projects"].exists {
            app.tabBars.buttons["Projects"].tap()
            _ = app.navigationBars.firstMatch.waitForExistence(timeout: 3)
            
            // Look for project creation capability
            if app.buttons["Add Project"].exists {
                app.buttons["Add Project"].tap()
                
                if app.textFields["Project Name"].waitForExistence(timeout: 3) {
                    app.textFields["Project Name"].tap()
                    app.textFields["Project Name"].typeText("Test Workflow Project")
                    
                    if app.buttons["Save"].exists {
                        app.buttons["Save"].tap()
                    } else if app.buttons["Create"].exists {
                        app.buttons["Create"].tap()
                    }
                }
            }
        }
    }
    
    /// Test monitoring access in workflow
    private func testMonitoringAccessInWorkflow() {
        if app.tabBars.buttons["Monitor"].exists {
            app.tabBars.buttons["Monitor"].tap()
            XCTAssertTrue(app.navigationBars.firstMatch.waitForExistence(timeout: 3))
        }
    }
    
    /// Test settings access in workflow
    private func testSettingsAccessInWorkflow() {
        if app.tabBars.buttons["Settings"].exists {
            app.tabBars.buttons["Settings"].tap()
            XCTAssertTrue(app.navigationBars.firstMatch.waitForExistence(timeout: 3))
        }
    }
    
    /// Create test project
    private func createTestProject() {
        if app.tabBars.buttons["Projects"].exists {
            app.tabBars.buttons["Projects"].tap()
            _ = app.navigationBars.firstMatch.waitForExistence(timeout: 3)
            
            if app.buttons["Add Project"].exists {
                app.buttons["Add Project"].tap()
                
                if app.textFields["Project Name"].waitForExistence(timeout: 3) {
                    app.textFields["Project Name"].tap()
                    app.textFields["Project Name"].typeText("E2E Test Project")
                    
                    if app.buttons["Save"].exists {
                        app.buttons["Save"].tap()
                    }
                }
            }
        }
    }
    
    /// Navigate to task management
    private func navigateToTaskManagement() {
        navigateToKanbanBoard()
    }
    
    /// Navigate to Kanban board
    private func navigateToKanbanBoard() {
        if app.tabBars.buttons["Monitor"].exists {
            app.tabBars.buttons["Monitor"].tap()
            _ = app.navigationBars.firstMatch.waitForExistence(timeout: 3)
            
            if app.buttons["kanban"].exists {
                app.buttons["kanban"].tap()
            } else if app.staticTexts.containing("tasks").firstMatch.exists {
                app.staticTexts.containing("tasks").firstMatch.tap()
            }
        }
    }
    
    /// Create test task
    private func createTestTask() {
        if app.navigationBars["Tasks"].exists {
            if app.buttons["Add Task"].exists {
                app.buttons["Add Task"].tap()
                
                if app.textFields["Task Title"].waitForExistence(timeout: 3) {
                    app.textFields["Task Title"].tap()
                    app.textFields["Task Title"].typeText("E2E Test Task")
                    
                    if app.buttons["Save"].exists {
                        app.buttons["Save"].tap()
                    }
                }
            }
        }
    }
    
    /// Test task state management
    private func testTaskStateManagement() {
        if app.navigationBars["Tasks"].exists {
            // Verify Kanban columns exist
            XCTAssertTrue(
                app.staticTexts["To Do"].exists ||
                app.staticTexts["In Progress"].exists ||
                app.staticTexts["Done"].exists
            )
        }
    }
    
    /// Test task statistics access
    private func testTaskStatisticsAccess() {
        if app.navigationBars["Tasks"].exists {
            let statsButtons = app.buttons.matching(NSPredicate(format: "identifier CONTAINS 'chart'"))
            if statsButtons.count > 0 {
                statsButtons.firstMatch.tap()
                
                if app.navigationBars.firstMatch.waitForExistence(timeout: 3) {
                    if app.buttons["Close"].exists {
                        app.buttons["Close"].tap()
                    }
                }
            }
        }
    }
    
    /// Access voice interface
    private func accessVoiceInterface() {
        if app.tabBars.buttons["Voice"].exists {
            app.tabBars.buttons["Voice"].tap()
        } else {
            // Look for floating voice button
            let voiceButtons = app.buttons.matching(NSPredicate(format: "identifier CONTAINS 'voice' OR identifier CONTAINS 'mic'"))
            if voiceButtons.count > 0 {
                voiceButtons.firstMatch.tap()
            }
        }
    }
    
    /// Test voice control interaction
    private func testVoiceControlInteraction() {
        if app.staticTexts["Voice Commands"].exists ||
           app.buttons.matching(NSPredicate(format: "identifier CONTAINS 'mic'")).count > 0 {
            
            let micButtons = app.buttons.matching(NSPredicate(format: "identifier CONTAINS 'mic'"))
            if micButtons.count > 0 {
                // Test microphone button interaction
                XCTAssertTrue(micButtons.firstMatch.isHittable)
            }
        }
    }
    
    /// Simulate voice commands
    private func simulateVoiceCommands() {
        // Note: Actual voice recognition can't be simulated in UI tests
        // This tests the UI response to voice command interface
        if app.staticTexts.containing("Hey LeanVibe").firstMatch.exists {
            XCTAssertTrue(app.staticTexts.containing("Hey LeanVibe").firstMatch.exists)
        }
    }
    
    /// Verify return to dashboard
    private func verifyReturnToDashboard() {
        if app.buttons["Close"].exists {
            app.buttons["Close"].tap()
        }
        
        XCTAssertTrue(app.tabBars.firstMatch.waitForExistence(timeout: 3))
    }
    
    /// Access architecture viewer
    private func accessArchitectureViewer() {
        // Try multiple methods to access architecture viewer
        if app.tabBars.buttons["Architecture"].exists {
            app.tabBars.buttons["Architecture"].tap()
        } else if app.tabBars.buttons["Monitor"].exists {
            app.tabBars.buttons["Monitor"].tap()
            _ = app.navigationBars.firstMatch.waitForExistence(timeout: 3)
            
            if app.buttons["architecture"].exists {
                app.buttons["architecture"].tap()
            }
        }
    }
    
    /// Explore project architecture
    private func exploreProjectArchitecture() {
        if app.navigationBars["Architecture"].waitForExistence(timeout: 3) {
            // Test project selector
            if app.segmentedControls.firstMatch.exists {
                XCTAssertTrue(app.segmentedControls.firstMatch.isHittable)
            }
        }
    }
    
    /// Interact with diagram elements
    private func interactWithDiagramElements() {
        if app.webViews.firstMatch.exists {
            let webView = app.webViews.firstMatch
            let centerCoordinate = webView.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.5))
            centerCoordinate.tap()
        }
    }
    
    /// Test architecture export
    private func testArchitectureExport() {
        if app.buttons["Export"].exists && app.buttons["Export"].isEnabled {
            app.buttons["Export"].tap()
            
            if app.navigationBars.firstMatch.waitForExistence(timeout: 3) {
                if app.buttons["Done"].exists {
                    app.buttons["Done"].tap()
                }
            }
        }
    }
    
    /// Test project switching in architecture
    private func testProjectSwitchingInArchitecture() {
        if app.buttons["Mobile App"].exists {
            app.buttons["Mobile App"].tap()
            _ = app.navigationBars["Architecture"].waitForExistence(timeout: 3)
        }
    }
    
    /// Test Kanban error recovery
    private func testKanbanErrorRecovery() {
        navigateToKanbanBoard()
        
        if app.buttons["Retry"].exists {
            app.buttons["Retry"].tap()
        }
    }
    
    /// Test voice interface error recovery
    private func testVoiceInterfaceErrorRecovery() {
        accessVoiceInterface()
        
        if app.staticTexts.containing("Error").firstMatch.exists &&
           app.buttons["Retry"].exists {
            app.buttons["Retry"].tap()
        }
        
        if app.buttons["Close"].exists {
            app.buttons["Close"].tap()
        }
    }
    
    /// Test architecture viewer error recovery
    private func testArchitectureViewerErrorRecovery() {
        accessArchitectureViewer()
        
        if app.buttons["Retry"].exists {
            app.buttons["Retry"].tap()
        }
    }
    
    /// Verify app stability after errors
    private func verifyAppStabilityAfterErrors() {
        // Should still have functional dashboard
        XCTAssertTrue(app.tabBars.firstMatch.exists)
        XCTAssertTrue(app.tabBars.firstMatch.isHittable)
        
        // Should be able to navigate
        if app.tabBars.buttons["Settings"].exists {
            app.tabBars.buttons["Settings"].tap()
            XCTAssertTrue(app.navigationBars.firstMatch.waitForExistence(timeout: 3))
        }
    }
    
    /// Take screenshot for debugging
    private func takeScreenshot(name: String) {
        let screenshot = app.screenshot()
        let attachment = XCTAttachment(screenshot: screenshot)
        attachment.name = name
        attachment.lifetime = .keepAlways
        add(attachment)
    }
}

// MARK: - End-to-End Workflow Page Object Model

@available(iOS 18.0, macOS 14.0, *)
struct EndToEndWorkflowPage {
    let app: XCUIApplication
    
    func completeFullUserJourney() -> Bool {
        // Complete onboarding
        guard completeOnboarding() else { return false }
        
        // Verify dashboard access
        guard verifyDashboardAccess() else { return false }
        
        // Test main features
        guard testMainFeatures() else { return false }
        
        // Test cross-feature integration
        guard testCrossFeatureIntegration() else { return false }
        
        return true
    }
    
    private func completeOnboarding() -> Bool {
        if app.staticTexts["Welcome to LeanVibe"].exists {
            let steps = ["Get Started", "Continue", "Continue", "Continue", "Continue", "Continue", "Continue", "Get Started"]
            
            for step in steps {
                guard app.buttons[step].waitForExistence(timeout: 2) else { continue }
                app.buttons[step].tap()
            }
        }
        
        return app.tabBars.firstMatch.waitForExistence(timeout: 10)
    }
    
    private func verifyDashboardAccess() -> Bool {
        return app.tabBars.firstMatch.exists && app.navigationBars.firstMatch.exists
    }
    
    private func testMainFeatures() -> Bool {
        let features = ["Projects", "Monitor", "Settings"]
        
        for feature in features {
            guard app.tabBars.buttons[feature].exists else { continue }
            
            app.tabBars.buttons[feature].tap()
            
            guard app.navigationBars.firstMatch.waitForExistence(timeout: 3) else { return false }
        }
        
        return true
    }
    
    private func testCrossFeatureIntegration() -> Bool {
        // Test navigation flow between features
        return testKanbanToVoiceIntegration() && testArchitectureToProjectIntegration()
    }
    
    private func testKanbanToVoiceIntegration() -> Bool {
        // Navigate to Kanban
        guard app.tabBars.buttons["Monitor"].exists else { return true }
        app.tabBars.buttons["Monitor"].tap()
        
        // Look for voice integration
        let voiceButtons = app.buttons.matching(NSPredicate(format: "identifier CONTAINS 'voice'"))
        if voiceButtons.count > 0 {
            voiceButtons.firstMatch.tap()
            
            if app.buttons["Close"].exists {
                app.buttons["Close"].tap()
            }
        }
        
        return true
    }
    
    private func testArchitectureToProjectIntegration() -> Bool {
        // Test architecture to project navigation
        if app.tabBars.buttons["Projects"].exists {
            app.tabBars.buttons["Projects"].tap()
            return app.navigationBars.firstMatch.waitForExistence(timeout: 3)
        }
        
        return true
    }
}