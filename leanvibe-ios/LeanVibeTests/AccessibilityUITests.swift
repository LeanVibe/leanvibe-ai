import XCTest
@testable import LeanVibe

/// Comprehensive UI tests using accessibility identifiers
/// Tests critical user flows for production readiness validation
@available(iOS 18.0, *)
final class AccessibilityUITests: XCTestCase {
    
    var app: XCUIApplication!
    
    override func setUpWithError() throws {
        try super.setUpWithError()
        
        continueAfterFailure = false
        app = XCUIApplication()
        
        // Configure app for testing
        app.launchEnvironment["LEANVIBE_ENV"] = "test"
        app.launchEnvironment["LEANVIBE_USE_MOCK_DATA"] = "true"
        app.launchEnvironment["LEANVIBE_SKIP_ONBOARDING"] = "true"
        
        app.launch()
    }
    
    override func tearDownWithError() throws {
        app = nil
        try super.tearDownWithError()
    }
    
    // MARK: - Main Navigation Tests
    
    func testMainTabNavigation() throws {
        let tabView = app.tabBars[AccessibilityIdentifiers.MainNavigation.tabView]
        XCTAssertTrue(tabView.exists, "Main tab view should exist")
        
        // Test Projects tab
        let projectsTab = tabView.buttons[AccessibilityIdentifiers.MainNavigation.projectsTab]
        XCTAssertTrue(projectsTab.exists, "Projects tab should exist")
        projectsTab.tap()
        
        let projectsContainer = app.scrollViews[AccessibilityIdentifiers.Projects.container]
        XCTAssertTrue(projectsContainer.waitForExistence(timeout: 2), "Projects view should load")
        
        // Test Dashboard tab
        let dashboardTab = tabView.buttons[AccessibilityIdentifiers.MainNavigation.dashboardTab]
        XCTAssertTrue(dashboardTab.exists, "Dashboard tab should exist")
        dashboardTab.tap()
        
        let dashboardContainer = app.scrollViews[AccessibilityIdentifiers.Dashboard.container]
        XCTAssertTrue(dashboardContainer.waitForExistence(timeout: 2), "Dashboard view should load")
        
        // Test Settings tab
        let settingsTab = tabView.buttons[AccessibilityIdentifiers.MainNavigation.settingsTab]
        XCTAssertTrue(settingsTab.exists, "Settings tab should exist")
        settingsTab.tap()
        
        let settingsContainer = app.scrollViews[AccessibilityIdentifiers.Settings.container]
        XCTAssertTrue(settingsContainer.waitForExistence(timeout: 2), "Settings view should load")
    }
    
    // MARK: - Dashboard Tests
    
    func testDashboardBasicFunctionality() throws {
        // Navigate to dashboard
        app.tabBars.buttons[AccessibilityIdentifiers.MainNavigation.dashboardTab].tap()
        
        let dashboardContainer = app.scrollViews[AccessibilityIdentifiers.Dashboard.container]
        XCTAssertTrue(dashboardContainer.waitForExistence(timeout: 3), "Dashboard should load")
        
        // Check connection status
        let connectionStatus = app.staticTexts[AccessibilityIdentifiers.Dashboard.connectionStatus]
        XCTAssertTrue(connectionStatus.exists, "Connection status should be visible")
        
        // Test message input
        let messageInput = app.textFields[AccessibilityIdentifiers.Dashboard.messageInput]
        if messageInput.exists {
            messageInput.tap()
            messageInput.typeText("Test message")
            
            let sendButton = app.buttons[AccessibilityIdentifiers.Dashboard.sendButton]
            if sendButton.exists && sendButton.isEnabled {
                sendButton.tap()
            }
        }
        
        // Check messages list
        let messagesList = app.tables[AccessibilityIdentifiers.Dashboard.messagesList]
        XCTAssertTrue(messagesList.exists, "Messages list should exist")
    }
    
    func testVoiceInterfaceAccessibility() throws {
        // Only test if voice features are enabled
        guard AppConfiguration.shared.isVoiceEnabled else {
            throw XCTSkip("Voice features are disabled")
        }
        
        // Navigate to voice interface
        if app.tabBars.buttons[AccessibilityIdentifiers.MainNavigation.voiceTab].exists {
            app.tabBars.buttons[AccessibilityIdentifiers.MainNavigation.voiceTab].tap()
            
            let voiceContainer = app.scrollViews[AccessibilityIdentifiers.Voice.container]
            XCTAssertTrue(voiceContainer.waitForExistence(timeout: 3), "Voice interface should load")
            
            // Check permission view if needed
            let permissionView = app.otherElements[AccessibilityIdentifiers.Voice.permissionView]
            if permissionView.exists {
                let permissionButton = app.buttons[AccessibilityIdentifiers.Voice.permissionButton]
                XCTAssertTrue(permissionButton.exists, "Permission button should exist")
                // Note: Don't actually request permissions in tests
            }
            
            // Check microphone button accessibility
            let micButton = app.buttons[AccessibilityIdentifiers.Voice.microphoneButton]
            if micButton.exists {
                XCTAssertTrue(micButton.isEnabled, "Microphone button should be enabled")
                // Note: Don't actually start recording in tests
            }
        }
    }
    
    // MARK: - Project Management Tests
    
    func testProjectManagement() throws {
        // Navigate to projects
        app.tabBars.buttons[AccessibilityIdentifiers.MainNavigation.projectsTab].tap()
        
        let projectsContainer = app.scrollViews[AccessibilityIdentifiers.Projects.container]
        XCTAssertTrue(projectsContainer.waitForExistence(timeout: 3), "Projects view should load")
        
        // Test add project button
        let addButton = app.buttons[AccessibilityIdentifiers.Projects.addProjectButton]
        if addButton.exists {
            addButton.tap()
            
            // Check if project creation UI appears
            let projectDetail = app.otherElements[AccessibilityIdentifiers.Projects.projectDetail]
            XCTAssertTrue(projectDetail.waitForExistence(timeout: 2), "Project detail view should appear")
            
            // Cancel creation
            if app.navigationBars.buttons["Cancel"].exists {
                app.navigationBars.buttons["Cancel"].tap()
            }
        }
        
        // Check projects list
        let projectsList = app.tables[AccessibilityIdentifiers.Projects.projectsList]
        XCTAssertTrue(projectsList.exists, "Projects list should exist")
    }
    
    // MARK: - Kanban Board Tests
    
    func testKanbanBoardNavigation() throws {
        // This test assumes we can navigate to a kanban board from projects
        app.tabBars.buttons[AccessibilityIdentifiers.MainNavigation.projectsTab].tap()
        
        let projectsList = app.tables[AccessibilityIdentifiers.Projects.projectsList]
        if projectsList.exists && projectsList.cells.count > 0 {
            // Tap first project
            projectsList.cells.firstMatch.tap()
            
            // Check if kanban board loads
            let kanbanContainer = app.scrollViews[AccessibilityIdentifiers.Kanban.container]
            if kanbanContainer.waitForExistence(timeout: 3) {
                
                // Check columns exist
                let todoColumn = app.otherElements[AccessibilityIdentifiers.Kanban.todoColumn]
                let inProgressColumn = app.otherElements[AccessibilityIdentifiers.Kanban.inProgressColumn]
                let doneColumn = app.otherElements[AccessibilityIdentifiers.Kanban.doneColumn]
                
                XCTAssertTrue(todoColumn.exists, "Todo column should exist")
                XCTAssertTrue(inProgressColumn.exists, "In Progress column should exist")
                XCTAssertTrue(doneColumn.exists, "Done column should exist")
                
                // Test add task functionality
                let addTaskButton = app.buttons[AccessibilityIdentifiers.Kanban.addTaskButton]
                if addTaskButton.exists {
                    addTaskButton.tap()
                    
                    // Check if task creation UI appears
                    let taskDetailView = app.otherElements[AccessibilityIdentifiers.Kanban.taskDetailView]
                    XCTAssertTrue(taskDetailView.waitForExistence(timeout: 2), "Task detail view should appear")
                    
                    // Cancel task creation
                    if app.navigationBars.buttons["Cancel"].exists {
                        app.navigationBars.buttons["Cancel"].tap()
                    }
                }
            }
        }
    }
    
    // MARK: - Settings Tests
    
    func testSettingsAccessibility() throws {
        app.tabBars.buttons[AccessibilityIdentifiers.MainNavigation.settingsTab].tap()
        
        let settingsContainer = app.scrollViews[AccessibilityIdentifiers.Settings.container]
        XCTAssertTrue(settingsContainer.waitForExistence(timeout: 3), "Settings should load")
        
        // Test server settings section
        let serverSection = app.otherElements[AccessibilityIdentifiers.Settings.serverSection]
        if serverSection.exists {
            serverSection.tap()
            
            let hostField = app.textFields[AccessibilityIdentifiers.Settings.serverHostField]
            let portField = app.textFields[AccessibilityIdentifiers.Settings.serverPortField]
            
            XCTAssertTrue(hostField.exists, "Server host field should exist")
            XCTAssertTrue(portField.exists, "Server port field should exist")
        }
        
        // Test voice settings section (if voice is enabled)
        if AppConfiguration.shared.isVoiceEnabled {
            let voiceSection = app.otherElements[AccessibilityIdentifiers.Settings.voiceSection]
            if voiceSection.exists {
                voiceSection.tap()
                
                let voiceToggle = app.switches[AccessibilityIdentifiers.Settings.voiceEnabledToggle]
                XCTAssertTrue(voiceToggle.exists, "Voice enabled toggle should exist")
            }
        }
    }
    
    // MARK: - Error Handling Tests
    
    func testErrorHandlingAccessibility() throws {
        // This test would require triggering an error condition
        // For now, we'll just check that error UI elements can be identified
        
        // Simulate network error by attempting invalid connection
        app.tabBars.buttons[AccessibilityIdentifiers.MainNavigation.settingsTab].tap()
        
        // If connection test button exists and triggers error
        let connectionTestButton = app.buttons[AccessibilityIdentifiers.Settings.connectionTestButton]
        if connectionTestButton.exists {
            connectionTestButton.tap()
            
            // Check if error view appears
            let errorView = app.alerts[AccessibilityIdentifiers.Error.errorView]
            if errorView.waitForExistence(timeout: 5) {
                let errorMessage = errorView.staticTexts[AccessibilityIdentifiers.Error.errorMessage]
                XCTAssertTrue(errorMessage.exists, "Error message should be accessible")
                
                let okButton = errorView.buttons[AccessibilityIdentifiers.Alerts.okButton]
                if okButton.exists {
                    okButton.tap()
                }
            }
        }
    }
    
    // MARK: - Performance Tests
    
    func testUIPerformance() throws {
        measure {
            // Test tab switching performance
            app.tabBars.buttons[AccessibilityIdentifiers.MainNavigation.projectsTab].tap()
            _ = app.scrollViews[AccessibilityIdentifiers.Projects.container].waitForExistence(timeout: 2)
            
            app.tabBars.buttons[AccessibilityIdentifiers.MainNavigation.dashboardTab].tap()
            _ = app.scrollViews[AccessibilityIdentifiers.Dashboard.container].waitForExistence(timeout: 2)
            
            app.tabBars.buttons[AccessibilityIdentifiers.MainNavigation.settingsTab].tap()
            _ = app.scrollViews[AccessibilityIdentifiers.Settings.container].waitForExistence(timeout: 2)
        }
    }
    
    func testLaunchPerformance() throws {
        if #available(macOS 10.15, iOS 13.0, tvOS 13.0, watchOS 7.0, *) {
            measure(metrics: [XCTApplicationLaunchMetric()]) {
                XCUIApplication().launch()
            }
        }
    }
    
    // MARK: - Accessibility Compliance Tests
    
    func testVoiceOverSupport() throws {
        // Enable VoiceOver simulation
        app.accessibilityActivate()
        
        // Navigate through main tabs using accessibility
        let tabView = app.tabBars[AccessibilityIdentifiers.MainNavigation.tabView]
        XCTAssertTrue(tabView.exists, "Tab view should be accessible")
        
        // Test each tab for accessibility labels
        let projectsTab = tabView.buttons[AccessibilityIdentifiers.MainNavigation.projectsTab]
        XCTAssertFalse(projectsTab.label.isEmpty, "Projects tab should have accessibility label")
        
        let dashboardTab = tabView.buttons[AccessibilityIdentifiers.MainNavigation.dashboardTab]
        XCTAssertFalse(dashboardTab.label.isEmpty, "Dashboard tab should have accessibility label")
        
        let settingsTab = tabView.buttons[AccessibilityIdentifiers.MainNavigation.settingsTab]
        XCTAssertFalse(settingsTab.label.isEmpty, "Settings tab should have accessibility label")
    }
    
    func testDynamicTypeSupport() throws {
        // Test with larger text sizes
        app.launchArguments.append("-UIPreferredContentSizeCategoryName")
        app.launchArguments.append("UICTContentSizeCategoryExtraExtraExtraLarge")
        
        app.launch()
        
        // Verify UI still functions with large text
        app.tabBars.buttons[AccessibilityIdentifiers.MainNavigation.dashboardTab].tap()
        
        let dashboardContainer = app.scrollViews[AccessibilityIdentifiers.Dashboard.container]
        XCTAssertTrue(dashboardContainer.waitForExistence(timeout: 3), "Dashboard should load with large text")
        
        // Verify text is still readable and buttons are still tappable
        let messageInput = app.textFields[AccessibilityIdentifiers.Dashboard.messageInput]
        if messageInput.exists {
            XCTAssertTrue(messageInput.isHittable, "Message input should remain tappable with large text")
        }
    }
}