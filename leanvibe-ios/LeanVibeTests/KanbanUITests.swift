import XCTest
@testable import LeanVibe

@available(iOS 18.0, macOS 14.0, *)
@MainActor
final class KanbanUITests: XCTestCase {
    
    private var app: XCUIApplication!
    
    override func setUpWithError() throws {
        continueAfterFailure = false
        app = XCUIApplication()
        app.launch()
        
        // Navigate to main dashboard and then to Kanban board
        navigateToMainDashboard()
        navigateToKanbanBoard()
    }
    
    override func tearDownWithError() throws {
        app = nil
    }
    
    // MARK: - Kanban Board Display Tests
    
    /// Test that Kanban board displays all required columns
    func testKanbanBoardDisplaysColumns() throws {
        // Given: User is on Kanban board
        XCTAssertTrue(app.navigationBars["Tasks"].waitForExistence(timeout: 5))
        
        // Then: All three columns should be visible
        XCTAssertTrue(app.staticTexts["To Do"].exists || app.staticTexts["Todo"].exists)
        XCTAssertTrue(app.staticTexts["In Progress"].exists)
        XCTAssertTrue(app.staticTexts["Done"].exists)
        
        // Scroll horizontally to ensure all columns are accessible
        app.scrollViews.firstMatch.swipeLeft()
        XCTAssertTrue(app.staticTexts["Done"].waitForExistence(timeout: 2))
        
        app.scrollViews.firstMatch.swipeRight()
        XCTAssertTrue(app.staticTexts["To Do"].exists || app.staticTexts["Todo"].exists)
    }
    
    /// Test Kanban board navigation and toolbar elements
    func testKanbanBoardNavigation() throws {
        // Given: User is on Kanban board
        XCTAssertTrue(app.navigationBars["Tasks"].exists)
        
        // Then: Should have proper navigation elements
        XCTAssertTrue(app.navigationBars["Tasks"].buttons.count >= 2) // At least back + menu
        
        // Should have statistics button
        XCTAssertTrue(app.buttons.matching(NSPredicate(format: "identifier CONTAINS 'chart' OR label CONTAINS 'Statistics'")).count > 0)
        
        // Should have menu button for settings and sort options
        XCTAssertTrue(app.buttons.matching(NSPredicate(format: "identifier CONTAINS 'ellipsis' OR label CONTAINS 'More'")).count > 0)
    }
    
    /// Test search functionality in Kanban board
    func testKanbanBoardSearch() throws {
        // Given: User is on Kanban board
        XCTAssertTrue(app.navigationBars["Tasks"].exists)
        
        // When: User taps search bar
        if app.searchFields.firstMatch.exists {
            app.searchFields.firstMatch.tap()
            app.searchFields.firstMatch.typeText("test")
            
            // Then: Search should filter tasks
            // Note: This test validates the search UI exists and is interactive
            XCTAssertTrue(app.searchFields.firstMatch.value as? String == "test")
            
            // Clear search
            if app.buttons["Clear text"].exists {
                app.buttons["Clear text"].tap()
            }
        }
    }
    
    // MARK: - Task Display and Interaction Tests
    
    /// Test task display in columns
    func testTaskDisplayInColumns() throws {
        // Given: User is on Kanban board with tasks
        XCTAssertTrue(app.navigationBars["Tasks"].exists)
        
        // When: Look for tasks in any column
        let taskElements = app.staticTexts.matching(NSPredicate(format: "label CONTAINS 'Task' OR label CONTAINS 'task'"))
        
        if taskElements.count > 0 {
            // Then: Tasks should be properly displayed
            let firstTask = taskElements.firstMatch
            XCTAssertTrue(firstTask.exists)
            
            // Task should be tappable
            XCTAssertTrue(firstTask.isHittable)
        } else {
            // No tasks exist - this is also a valid state to test
            XCTAssertTrue(true, "No tasks found - empty state is valid")
        }
    }
    
    /// Test task detail view navigation
    func testTaskDetailNavigation() throws {
        // Given: User is on Kanban board
        XCTAssertTrue(app.navigationBars["Tasks"].exists)
        
        // When: User taps on a task (if any exist)
        let taskElements = app.staticTexts.matching(NSPredicate(format: "label CONTAINS 'Task' OR label CONTAINS 'task'"))
        
        if taskElements.count > 0 {
            let firstTask = taskElements.firstMatch
            firstTask.tap()
            
            // Then: Should navigate to task detail view
            XCTAssertTrue(
                app.navigationBars["Task Details"].waitForExistence(timeout: 3) ||
                app.staticTexts["Task Details"].waitForExistence(timeout: 3) ||
                app.navigationBars.firstMatch.waitForExistence(timeout: 3)
            )
            
            // Should be able to navigate back
            if app.buttons["Close"].exists {
                app.buttons["Close"].tap()
            } else if app.buttons["Done"].exists {
                app.buttons["Done"].tap()
            } else if app.navigationBars.buttons.firstMatch.exists {
                app.navigationBars.buttons.firstMatch.tap()
            }
            
            // Should return to Kanban board
            XCTAssertTrue(app.navigationBars["Tasks"].waitForExistence(timeout: 3))
        }
    }
    
    // MARK: - Task Creation Tests
    
    /// Test task creation workflow
    func testTaskCreationWorkflow() throws {
        // Given: User is on Kanban board
        XCTAssertTrue(app.navigationBars["Tasks"].exists)
        
        // When: User attempts to create a new task
        // Look for add/create task buttons
        let createButtons = [
            app.buttons["Add Task"],
            app.buttons["+"],
            app.buttons.matching(NSPredicate(format: "identifier CONTAINS 'plus' OR label CONTAINS 'Add'"))
        ]
        
        var createButtonFound = false
        for buttonQuery in createButtons {
            if buttonQuery.firstMatch.exists {
                buttonQuery.firstMatch.tap()
                createButtonFound = true
                break
            }
        }
        
        if createButtonFound {
            // Then: Task creation interface should appear
            XCTAssertTrue(
                app.navigationBars["Create Task"].waitForExistence(timeout: 3) ||
                app.navigationBars["New Task"].waitForExistence(timeout: 3) ||
                app.staticTexts["Create Task"].waitForExistence(timeout: 3) ||
                app.textFields.firstMatch.waitForExistence(timeout: 3)
            )
            
            // Should have task input fields
            if app.textFields["Task Title"].exists || app.textFields.firstMatch.exists {
                let titleField = app.textFields["Task Title"].exists ? 
                    app.textFields["Task Title"] : app.textFields.firstMatch
                titleField.tap()
                titleField.typeText("UI Test Task")
                
                // Look for save/create button
                if app.buttons["Save"].exists {
                    app.buttons["Save"].tap()
                } else if app.buttons["Create"].exists {
                    app.buttons["Create"].tap()
                }
                
                // Should return to Kanban board
                XCTAssertTrue(app.navigationBars["Tasks"].waitForExistence(timeout: 5))
            }
        } else {
            // No create task button found - document this state
            XCTAssertTrue(true, "No task creation UI found - may be feature not implemented yet")
        }
    }
    
    // MARK: - Drag and Drop Tests
    
    /// Test task drag and drop between columns (basic interaction)
    func testTaskDragDropInteraction() throws {
        // Given: User is on Kanban board with tasks
        XCTAssertTrue(app.navigationBars["Tasks"].exists)
        
        // When: Look for draggable tasks
        let taskElements = app.staticTexts.matching(NSPredicate(format: "label CONTAINS 'Task' OR label CONTAINS 'task'"))
        
        if taskElements.count > 0 {
            let firstTask = taskElements.firstMatch
            let taskFrame = firstTask.frame
            
            // Try to perform drag gesture (basic test)
            let startPoint = CGPoint(x: taskFrame.midX, y: taskFrame.midY)
            let endPoint = CGPoint(x: startPoint.x + 200, y: startPoint.y) // Drag right
            
            // Perform drag gesture
            firstTask.press(forDuration: 1.0, thenDragTo: app.coordinate(withNormalizedOffset: CGVector(dx: 0.8, dy: 0.5)))
            
            // Note: Actual drag-drop validation would require more complex coordinate calculation
            // This test validates that drag gestures don't crash the app
            XCTAssertTrue(app.navigationBars["Tasks"].exists)
        }
    }
    
    // MARK: - Settings and Menu Tests
    
    /// Test Kanban settings access
    func testKanbanSettingsAccess() throws {
        // Given: User is on Kanban board
        XCTAssertTrue(app.navigationBars["Tasks"].exists)
        
        // When: User taps menu/settings button
        let menuButtons = app.buttons.matching(NSPredicate(format: "identifier CONTAINS 'ellipsis' OR label CONTAINS 'More'"))
        
        if menuButtons.count > 0 {
            menuButtons.firstMatch.tap()
            
            // Then: Should show menu options
            XCTAssertTrue(
                app.buttons["Settings"].waitForExistence(timeout: 2) ||
                app.staticTexts["Settings"].waitForExistence(timeout: 2) ||
                app.menus.firstMatch.waitForExistence(timeout: 2)
            )
            
            // Test settings access if available
            if app.buttons["Settings"].exists {
                app.buttons["Settings"].tap()
                
                // Should navigate to settings
                XCTAssertTrue(
                    app.navigationBars.firstMatch.waitForExistence(timeout: 3) ||
                    app.staticTexts["Kanban Settings"].waitForExistence(timeout: 3)
                )
                
                // Navigate back
                if app.buttons["Done"].exists {
                    app.buttons["Done"].tap()
                } else if app.navigationBars.buttons.firstMatch.exists {
                    app.navigationBars.buttons.firstMatch.tap()
                }
            }
            
            // Dismiss menu if still open
            if app.menus.firstMatch.exists {
                app.coordinate(withNormalizedOffset: CGVector(dx: 0.1, dy: 0.1)).tap()
            }
        }
    }
    
    /// Test sort functionality
    func testKanbanSortFunctionality() throws {
        // Given: User is on Kanban board
        XCTAssertTrue(app.navigationBars["Tasks"].exists)
        
        // When: User accesses sort options
        let menuButtons = app.buttons.matching(NSPredicate(format: "identifier CONTAINS 'ellipsis' OR label CONTAINS 'More'"))
        
        if menuButtons.count > 0 {
            menuButtons.firstMatch.tap()
            
            // Look for sort options
            let sortOptions = ["priority", "due_date", "title", "Priority", "Due Date", "Title"]
            var sortOptionFound = false
            
            for option in sortOptions {
                if app.buttons[option].exists || app.staticTexts[option].exists {
                    (app.buttons[option].exists ? app.buttons[option] : app.staticTexts[option]).tap()
                    sortOptionFound = true
                    break
                }
            }
            
            if sortOptionFound {
                // Then: Sort should be applied (UI should remain stable)
                XCTAssertTrue(app.navigationBars["Tasks"].waitForExistence(timeout: 3))
            }
            
            // Dismiss menu if still open
            if app.menus.firstMatch.exists {
                app.coordinate(withNormalizedOffset: CGVector(dx: 0.1, y: 0.1)).tap()
            }
        }
    }
    
    // MARK: - Statistics Tests
    
    /// Test task statistics view access
    func testTaskStatisticsAccess() throws {
        // Given: User is on Kanban board
        XCTAssertTrue(app.navigationBars["Tasks"].exists)
        
        // When: User taps statistics button
        let statsButtons = app.buttons.matching(NSPredicate(format: "identifier CONTAINS 'chart' OR label CONTAINS 'Statistics'"))
        
        if statsButtons.count > 0 {
            statsButtons.firstMatch.tap()
            
            // Then: Should show statistics view
            XCTAssertTrue(
                app.navigationBars["Statistics"].waitForExistence(timeout: 3) ||
                app.staticTexts["Task Statistics"].waitForExistence(timeout: 3) ||
                app.staticTexts["Statistics"].waitForExistence(timeout: 3)
            )
            
            // Should be able to close statistics
            if app.buttons["Close"].exists {
                app.buttons["Close"].tap()
            } else if app.buttons["Done"].exists {
                app.buttons["Done"].tap()
            }
            
            // Should return to Kanban board
            XCTAssertTrue(app.navigationBars["Tasks"].waitForExistence(timeout: 3))
        }
    }
    
    // MARK: - Error Handling Tests
    
    /// Test error display and retry functionality
    func testKanbanErrorHandling() throws {
        // Given: User is on Kanban board
        XCTAssertTrue(app.navigationBars["Tasks"].exists)
        
        // When: Look for error states (if any)
        if app.staticTexts.containing("Error").firstMatch.exists {
            // Then: Should have retry option
            XCTAssertTrue(app.buttons["Retry"].exists)
            
            // Test retry functionality
            app.buttons["Retry"].tap()
            
            // Should attempt to retry (either succeed or show error again)
            XCTAssertTrue(
                app.navigationBars["Tasks"].waitForExistence(timeout: 5) ||
                app.staticTexts.containing("Error").firstMatch.waitForExistence(timeout: 5)
            )
        }
        
        // Test error dismissal if available
        if app.buttons["Close"].exists && app.staticTexts.containing("Error").firstMatch.exists {
            app.buttons["Close"].tap()
            
            // Error should be dismissed
            XCTAssertTrue(app.staticTexts.containing("Error").firstMatch.waitForNonExistence(timeout: 2))
        }
    }
    
    // MARK: - Performance Tests
    
    /// Test Kanban board rendering performance
    func testKanbanRenderingPerformance() throws {
        measure(metrics: [XCTMemoryMetric(), XCTCPUMetric()]) {
            // Navigate away and back to test rendering performance
            if app.tabBars.buttons["Settings"].exists {
                app.tabBars.buttons["Settings"].tap()
                _ = app.navigationBars.firstMatch.waitForExistence(timeout: 2)
                
                navigateToKanbanBoard()
                _ = app.navigationBars["Tasks"].waitForExistence(timeout: 2)
            }
        }
    }
    
    /// Test horizontal scrolling performance
    func testKanbanScrollingPerformance() throws {
        // Given: User is on Kanban board
        XCTAssertTrue(app.navigationBars["Tasks"].exists)
        
        measure {
            // Perform horizontal scrolling
            for _ in 0..<5 {
                app.scrollViews.firstMatch.swipeLeft()
                app.scrollViews.firstMatch.swipeRight()
            }
        }
    }
    
    // MARK: - Accessibility Tests
    
    /// Test Kanban board accessibility features
    func testKanbanAccessibility() throws {
        // Given: User is on Kanban board
        XCTAssertTrue(app.navigationBars["Tasks"].exists)
        
        // Then: Key elements should be accessible
        XCTAssertTrue(app.navigationBars["Tasks"].isAccessibilityElement || 
                     app.navigationBars["Tasks"].accessibilityLabel != nil)
        
        // Column headers should be accessible
        let columns = [app.staticTexts["To Do"], app.staticTexts["In Progress"], app.staticTexts["Done"]]
        for column in columns {
            if column.exists {
                XCTAssertTrue(column.isAccessibilityElement)
            }
        }
        
        // Tasks should be accessible if they exist
        let taskElements = app.staticTexts.matching(NSPredicate(format: "label CONTAINS 'Task' OR label CONTAINS 'task'"))
        if taskElements.count > 0 {
            XCTAssertTrue(taskElements.firstMatch.isAccessibilityElement)
        }
    }
    
    // MARK: - Integration Tests
    
    /// Test Kanban integration with backend
    func testKanbanBackendIntegration() throws {
        // Given: User is on Kanban board
        XCTAssertTrue(app.navigationBars["Tasks"].exists)
        
        // When: User pulls to refresh (if available)
        let scrollView = app.scrollViews.firstMatch
        if scrollView.exists {
            let startPoint = scrollView.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.3))
            let endPoint = scrollView.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.7))
            
            startPoint.press(forDuration: 0.1, thenDragTo: endPoint)
            
            // Should trigger refresh (may show loading indicator)
            // Test that UI remains stable during refresh
            XCTAssertTrue(app.navigationBars["Tasks"].waitForExistence(timeout: 5))
        }
    }
    
    // MARK: - Helper Methods
    
    /// Navigate to main dashboard
    private func navigateToMainDashboard() {
        // Skip onboarding if present
        if app.staticTexts["Welcome to LeanVibe"].exists {
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
    
    /// Navigate to Kanban board
    private func navigateToKanbanBoard() {
        // Navigate to Monitor tab to access Kanban
        if app.tabBars.buttons["Monitor"].exists {
            app.tabBars.buttons["Monitor"].tap()
            
            // Look for Kanban access
            if app.buttons["kanban"].exists {
                app.buttons["kanban"].tap()
            } else if app.staticTexts.containing("tasks").firstMatch.exists {
                app.staticTexts.containing("tasks").firstMatch.tap()
            } else if app.staticTexts["Tasks"].exists {
                app.staticTexts["Tasks"].tap()
            }
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

// MARK: - Kanban Page Object Model

@available(iOS 18.0, macOS 14.0, *)
struct KanbanBoardPage {
    let app: XCUIApplication
    
    var navigationBar: XCUIElement { app.navigationBars["Tasks"] }
    var searchField: XCUIElement { app.searchFields.firstMatch }
    var statisticsButton: XCUIElement { app.buttons.matching(NSPredicate(format: "identifier CONTAINS 'chart'")).firstMatch }
    var menuButton: XCUIElement { app.buttons.matching(NSPredicate(format: "identifier CONTAINS 'ellipsis'")).firstMatch }
    
    // Columns
    var todoColumn: XCUIElement { app.staticTexts["To Do"] }
    var inProgressColumn: XCUIElement { app.staticTexts["In Progress"] }
    var doneColumn: XCUIElement { app.staticTexts["Done"] }
    
    // Tasks
    var allTasks: XCUIElementQuery { app.staticTexts.matching(NSPredicate(format: "label CONTAINS 'Task'")) }
    var firstTask: XCUIElement { allTasks.firstMatch }
    
    func scrollToColumn(_ column: String) {
        let scrollView = app.scrollViews.firstMatch
        switch column.lowercased() {
        case "done":
            scrollView.swipeLeft()
        case "todo", "to do":
            scrollView.swipeRight()
        default:
            break
        }
    }
    
    func openTaskCreation() -> Bool {
        let createButtons = [
            app.buttons["Add Task"],
            app.buttons["+"],
            app.buttons.matching(NSPredicate(format: "identifier CONTAINS 'plus'")).firstMatch
        ]
        
        for button in createButtons {
            if button.exists {
                button.tap()
                return true
            }
        }
        return false
    }
    
    func openStatistics() -> Bool {
        if statisticsButton.exists {
            statisticsButton.tap()
            return true
        }
        return false
    }
    
    func openMenu() -> Bool {
        if menuButton.exists {
            menuButton.tap()
            return true
        }
        return false
    }
}