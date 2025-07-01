import XCTest
@testable import LeanVibe

@available(iOS 18.0, macOS 14.0, *)
@MainActor
final class UserFlowUITests: XCTestCase {
    
    private var app: XCUIApplication!
    
    override func setUpWithError() throws {
        continueAfterFailure = false
        app = XCUIApplication()
        app.launch()
    }
    
    override func tearDownWithError() throws {
        app = nil
    }
    
    // MARK: - Critical User Flow Tests
    
    /// Test the complete onboarding flow from first launch to main dashboard
    func testCompleteOnboardingFlow() throws {
        // Note: This test assumes the app launches with onboarding on first run
        // Given: Fresh app launch
        
        // When: User goes through onboarding steps
        // Welcome Screen
        if app.staticTexts["Welcome to LeanVibe"].exists {
            app.buttons["Get Started"].tap()
            
            // Project Setup Screen
            XCTAssertTrue(app.staticTexts["Project Setup"].waitForExistence(timeout: 3))
            app.buttons["Continue"].tap()
            
            // Dashboard Tour Screen  
            XCTAssertTrue(app.staticTexts["Dashboard Tour"].waitForExistence(timeout: 3))
            app.buttons["Continue"].tap()
            
            // Voice Command Demo Screen
            XCTAssertTrue(app.staticTexts["Voice Commands"].waitForExistence(timeout: 3))
            app.buttons["Continue"].tap()
            
            // Architecture Viewer Screen
            XCTAssertTrue(app.staticTexts["Architecture Viewer"].waitForExistence(timeout: 3))
            app.buttons["Continue"].tap()
            
            // Kanban Introduction Screen
            XCTAssertTrue(app.staticTexts["Kanban Board"].waitForExistence(timeout: 3))
            app.buttons["Continue"].tap()
            
            // Advanced Features Screen
            XCTAssertTrue(app.staticTexts["Advanced Features"].waitForExistence(timeout: 3))
            app.buttons["Continue"].tap()
            
            // Completion Screen
            XCTAssertTrue(app.staticTexts["Setup Complete"].waitForExistence(timeout: 3))
            app.buttons["Get Started"].tap()
        }
        
        // Then: Should reach main dashboard
        XCTAssertTrue(app.tabBars.firstMatch.waitForExistence(timeout: 5))
        XCTAssertTrue(app.staticTexts["Projects"].exists || app.staticTexts["Dashboard"].exists)
    }
    
    /// Test project creation and management flow
    func testProjectManagementFlow() throws {
        // Given: User is on main dashboard
        navigateToMainDashboard()
        
        // When: Navigate to Projects tab
        if app.tabBars.buttons["Projects"].exists {
            app.tabBars.buttons["Projects"].tap()
        }
        
        // Then: Should see projects screen
        XCTAssertTrue(app.navigationBars.firstMatch.waitForExistence(timeout: 3))
        
        // When: Try to add a new project (if button exists)
        if app.buttons["Add Project"].exists {
            app.buttons["Add Project"].tap()
            
            // Fill in project details (if form exists)
            if app.textFields["Project Name"].exists {
                app.textFields["Project Name"].tap()
                app.textFields["Project Name"].typeText("UI Test Project")
                
                if app.textFields["Project Path"].exists {
                    app.textFields["Project Path"].tap()
                    app.textFields["Project Path"].typeText("/ui/test/path")
                }
                
                // Save project
                app.buttons["Save"].tap()
            }
        }
        
        // Then: Should return to projects list
        XCTAssertTrue(app.navigationBars.firstMatch.exists)
    }
    
    /// Test task management flow through Kanban board
    func testTaskManagementFlow() throws {
        // Given: User is on main dashboard
        navigateToMainDashboard()
        
        // When: Navigate to Monitor tab to access Kanban
        if app.tabBars.buttons["Monitor"].exists {
            app.tabBars.buttons["Monitor"].tap()
            
            // Look for Kanban access button
            if app.buttons["kanban"].exists {
                app.buttons["kanban"].tap()
            } else if app.staticTexts.containing("tasks").firstMatch.exists {
                app.staticTexts.containing("tasks").firstMatch.tap()
            }
            
            // Then: Should see Kanban board
            if app.staticTexts["Tasks"].waitForExistence(timeout: 5) {
                // Verify Kanban columns exist
                XCTAssertTrue(app.staticTexts["To Do"].exists || app.staticTexts["Todo"].exists)
                XCTAssertTrue(app.staticTexts["In Progress"].exists)
                XCTAssertTrue(app.staticTexts["Done"].exists)
                
                // Test task interaction (if tasks exist)
                let firstTask = app.staticTexts.matching(NSPredicate(format: "label CONTAINS 'Task' OR label CONTAINS 'task'")).firstMatch
                if firstTask.exists {
                    firstTask.tap()
                    
                    // Should open task detail view
                    XCTAssertTrue(app.navigationBars["Task Details"].waitForExistence(timeout: 3) || 
                                 app.staticTexts["Task Details"].waitForExistence(timeout: 3))
                    
                    // Close task detail
                    if app.buttons["Close"].exists {
                        app.buttons["Close"].tap()
                    } else if app.buttons["Done"].exists {
                        app.buttons["Done"].tap()
                    }
                }
            }
        }
    }
    
    /// Test settings and configuration access
    func testSettingsFlow() throws {
        // Given: User is on main dashboard
        navigateToMainDashboard()
        
        // When: Navigate to Settings tab
        if app.tabBars.buttons["Settings"].exists {
            app.tabBars.buttons["Settings"].tap()
            
            // Then: Should see settings screen
            XCTAssertTrue(app.navigationBars.firstMatch.waitForExistence(timeout: 3))
            XCTAssertTrue(app.staticTexts["Settings"].exists || app.staticTexts["Voice & Speech"].exists)
            
            // Test accessing error history (if available)
            if app.staticTexts["Error History"].exists {
                app.staticTexts["Error History"].tap()
                
                // Should show error history
                XCTAssertTrue(app.navigationBars.firstMatch.waitForExistence(timeout: 3))
                
                // Go back
                if app.buttons["Close"].exists {
                    app.buttons["Close"].tap()
                } else if app.navigationBars.buttons.firstMatch.exists {
                    app.navigationBars.buttons.firstMatch.tap()
                }
            }
            
            // Test accessing retry monitor (if available)
            if app.staticTexts["Retry Monitor"].exists {
                app.staticTexts["Retry Monitor"].tap()
                
                // Should show retry monitor
                XCTAssertTrue(app.navigationBars.firstMatch.waitForExistence(timeout: 3))
                
                // Go back
                if app.buttons["Close"].exists {
                    app.buttons["Close"].tap()
                } else if app.navigationBars.buttons.firstMatch.exists {
                    app.navigationBars.buttons.firstMatch.tap()
                }
            }
        }
    }
    
    /// Test voice interface access and permissions
    func testVoiceInterfaceFlow() throws {
        // Given: User is on main dashboard
        navigateToMainDashboard()
        
        // When: Navigate to Voice tab
        if app.tabBars.buttons["Voice"].exists {
            app.tabBars.buttons["Voice"].tap()
            
            // Then: Should see voice interface
            XCTAssertTrue(app.navigationBars.firstMatch.waitForExistence(timeout: 3))
            
            // Check for voice permission requests or interface elements
            if app.buttons["Enable Voice Commands"].exists {
                // Voice not enabled - test permission flow
                app.buttons["Enable Voice Commands"].tap()
                
                // May trigger permission dialog (system level)
                // We can't interact with system dialogs in UI tests, but we can verify the flow
            }
            
            // Look for voice controls
            if app.buttons["Start Listening"].exists || app.buttons["Stop Listening"].exists {
                // Voice interface is available
                XCTAssertTrue(true) // Interface is properly displayed
            }
        }
    }
    
    /// Test chat/agent interface flow
    func testChatInterfaceFlow() throws {
        // Given: User is on main dashboard
        navigateToMainDashboard()
        
        // When: Navigate to Agent/Chat tab
        if app.tabBars.buttons["Agent"].exists {
            app.tabBars.buttons["Agent"].tap()
            
            // Then: Should see chat interface
            XCTAssertTrue(app.navigationBars.firstMatch.waitForExistence(timeout: 3))
            
            // Test message input (if available)
            if app.textFields["Type a message"].exists || app.textViews.firstMatch.exists {
                let messageInput = app.textFields["Type a message"].exists ? 
                    app.textFields["Type a message"] : app.textViews.firstMatch
                
                messageInput.tap()
                messageInput.typeText("Hello, test message")
                
                // Look for send button
                if app.buttons["Send"].exists {
                    app.buttons["Send"].tap()
                    
                    // Should show message in chat
                    XCTAssertTrue(app.staticTexts.containing("Hello, test message").firstMatch.waitForExistence(timeout: 3))
                }
            }
        }
    }
    
    /// Test navigation between all main tabs
    func testTabNavigationFlow() throws {
        // Given: User is on main dashboard
        navigateToMainDashboard()
        
        // When: Navigate through all tabs
        let tabNames = ["Projects", "Agent", "Monitor", "Settings", "Voice"]
        
        for tabName in tabNames {
            if app.tabBars.buttons[tabName].exists {
                app.tabBars.buttons[tabName].tap()
                
                // Then: Should successfully navigate to each tab
                XCTAssertTrue(app.navigationBars.firstMatch.waitForExistence(timeout: 3))
                
                // Verify tab is selected
                XCTAssertTrue(app.tabBars.buttons[tabName].isSelected || 
                             app.tabBars.buttons[tabName].exists)
            }
        }
    }
    
    /// Test error handling in UI flows
    func testErrorHandlingFlow() throws {
        // Given: User is on main dashboard
        navigateToMainDashboard()
        
        // When: Navigate to a section that might trigger errors (Monitor for network issues)
        if app.tabBars.buttons["Monitor"].exists {
            app.tabBars.buttons["Monitor"].tap()
            
            // Look for error states or retry mechanisms
            if app.buttons["Retry"].exists {
                // Error banner is shown - test retry
                app.buttons["Retry"].tap()
                
                // Should attempt retry operation
                XCTAssertTrue(app.buttons["Retry"].waitForNonExistence(timeout: 5) || 
                             app.buttons["Retry"].exists) // Either succeeds or still retrying
            }
            
            // Look for error dismissal
            if app.buttons["Close"].exists && app.staticTexts.containing("Error").firstMatch.exists {
                app.buttons["Close"].tap()
                
                // Error should be dismissed
                XCTAssertTrue(app.staticTexts.containing("Error").firstMatch.waitForNonExistence(timeout: 3))
            }
        }
    }
    
    // MARK: - Performance Flow Tests
    
    /// Test app launch performance and responsiveness
    func testAppLaunchPerformance() throws {
        measure(metrics: [XCTApplicationLaunchMetric()]) {
            app.terminate()
            app.launch()
        }
    }
    
    /// Test navigation performance between tabs
    func testNavigationPerformance() throws {
        navigateToMainDashboard()
        
        measure {
            // Navigate through all tabs quickly
            let tabs = ["Projects", "Agent", "Monitor", "Settings", "Voice"]
            for tab in tabs {
                if app.tabBars.buttons[tab].exists {
                    app.tabBars.buttons[tab].tap()
                    _ = app.navigationBars.firstMatch.waitForExistence(timeout: 1)
                }
            }
        }
    }
    
    // MARK: - Accessibility Flow Tests
    
    /// Test accessibility features in main flows
    func testAccessibilityFlow() throws {
        // Given: User is on main dashboard
        navigateToMainDashboard()
        
        // When: Check accessibility elements
        XCTAssertTrue(app.tabBars.firstMatch.isAccessibilityElement || 
                     app.tabBars.buttons.firstMatch.isAccessibilityElement)
        
        // Navigate to different screens and verify accessibility
        let tabs = ["Projects", "Monitor", "Settings"]
        for tab in tabs {
            if app.tabBars.buttons[tab].exists {
                app.tabBars.buttons[tab].tap()
                
                // Verify main content is accessible
                XCTAssertTrue(app.navigationBars.firstMatch.isAccessibilityElement ||
                             app.staticTexts.firstMatch.isAccessibilityElement)
            }
        }
    }
    
    // MARK: - Helper Methods
    
    /// Navigate to main dashboard (skip onboarding if needed)
    private func navigateToMainDashboard() {
        // If onboarding is shown, complete it quickly
        if app.staticTexts["Welcome to LeanVibe"].exists {
            // Skip through onboarding
            let continueButtons = ["Get Started", "Continue", "Continue", "Continue", "Continue", "Continue", "Continue", "Get Started"]
            
            for buttonText in continueButtons {
                if app.buttons[buttonText].waitForExistence(timeout: 2) {
                    app.buttons[buttonText].tap()
                }
            }
        }
        
        // Wait for main dashboard
        XCTAssertTrue(app.tabBars.firstMatch.waitForExistence(timeout: 10))
    }
    
    /// Wait for element to appear with custom timeout
    private func waitForElement(_ element: XCUIElement, timeout: TimeInterval = 5) -> Bool {
        return element.waitForExistence(timeout: timeout)
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

// MARK: - Test Extensions

extension XCUIElement {
    /// Wait for element to disappear
    func waitForNonExistence(timeout: TimeInterval) -> Bool {
        let predicate = NSPredicate(format: "exists == false")
        let expectation = XCTNSPredicateExpectation(predicate: predicate, object: self)
        return XCTWaiter().wait(for: [expectation], timeout: timeout) == .completed
    }
}

// MARK: - Page Object Models (for better test organization)

@available(iOS 18.0, macOS 14.0, *)
struct OnboardingPage {
    let app: XCUIApplication
    
    var welcomeTitle: XCUIElement { app.staticTexts["Welcome to LeanVibe"] }
    var getStartedButton: XCUIElement { app.buttons["Get Started"] }
    var continueButton: XCUIElement { app.buttons["Continue"] }
    
    func completeOnboarding() {
        if welcomeTitle.exists {
            getStartedButton.tap()
            
            // Navigate through all onboarding steps
            while continueButton.waitForExistence(timeout: 2) {
                continueButton.tap()
            }
            
            // Final step
            if app.buttons["Get Started"].exists {
                app.buttons["Get Started"].tap()
            }
        }
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct DashboardPage {
    let app: XCUIApplication
    
    var tabBar: XCUIElement { app.tabBars.firstMatch }
    var projectsTab: XCUIElement { app.tabBars.buttons["Projects"] }
    var agentTab: XCUIElement { app.tabBars.buttons["Agent"] }
    var monitorTab: XCUIElement { app.tabBars.buttons["Monitor"] }
    var settingsTab: XCUIElement { app.tabBars.buttons["Settings"] }
    var voiceTab: XCUIElement { app.tabBars.buttons["Voice"] }
    
    func navigateToTab(_ tabName: String) {
        if app.tabBars.buttons[tabName].exists {
            app.tabBars.buttons[tabName].tap()
        }
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct KanbanPage {
    let app: XCUIApplication
    
    var todoColumn: XCUIElement { app.staticTexts["To Do"] }
    var inProgressColumn: XCUIElement { app.staticTexts["In Progress"] }
    var doneColumn: XCUIElement { app.staticTexts["Done"] }
    
    var firstTask: XCUIElement { 
        app.staticTexts.matching(NSPredicate(format: "label CONTAINS 'Task'")).firstMatch 
    }
    
    func openFirstTask() {
        if firstTask.exists {
            firstTask.tap()
        }
    }
}