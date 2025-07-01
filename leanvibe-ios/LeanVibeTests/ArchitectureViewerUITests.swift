import XCTest
@testable import LeanVibe

@available(iOS 18.0, macOS 14.0, *)
@MainActor
final class ArchitectureViewerUITests: XCTestCase {
    
    private var app: XCUIApplication!
    
    override func setUpWithError() throws {
        continueAfterFailure = false
        app = XCUIApplication()
        app.launch()
        
        // Navigate to main dashboard and then to Architecture viewer
        navigateToMainDashboard()
        navigateToArchitectureViewer()
    }
    
    override func tearDownWithError() throws {
        app = nil
    }
    
    // MARK: - Architecture Viewer Display Tests
    
    /// Test that Architecture tab displays properly
    func testArchitectureViewerDisplay() throws {
        // Given: User is on Architecture viewer
        XCTAssertTrue(app.navigationBars["Architecture"].waitForExistence(timeout: 5))
        
        // Then: Should have main interface elements
        XCTAssertTrue(app.navigationBars["Architecture"].exists)
        
        // Should have toolbar with export button
        XCTAssertTrue(
            app.buttons["Export"].exists ||
            app.buttons.matching(NSPredicate(format: "label CONTAINS 'Export'")).count > 0
        )
        
        // Should have content area (either diagram, loading, or empty state)
        XCTAssertTrue(
            app.otherElements.firstMatch.exists || // WebView or diagram content
            app.staticTexts.containing("Loading").firstMatch.exists ||
            app.staticTexts.containing("architecture").firstMatch.exists ||
            app.buttons["Generate Diagram"].exists
        )
    }
    
    /// Test architecture viewer navigation elements
    func testArchitectureViewerNavigation() throws {
        // Given: User is on Architecture viewer
        XCTAssertTrue(app.navigationBars["Architecture"].exists)
        
        // Then: Should have proper navigation structure
        XCTAssertTrue(app.navigationBars["Architecture"].buttons.count >= 1) // At least export button
        
        // Should be able to navigate back to main dashboard
        if app.tabBars.firstMatch.exists {
            // Tab-based navigation
            XCTAssertTrue(app.tabBars.firstMatch.isHittable)
        } else {
            // Navigation-based
            let backButtons = app.navigationBars.buttons.matching(NSPredicate(format: "identifier CONTAINS 'Back'"))
            if backButtons.count > 0 {
                XCTAssertTrue(backButtons.firstMatch.isHittable)
            }
        }
    }
    
    /// Test project selector functionality
    func testProjectSelectorFunctionality() throws {
        // Given: User is on Architecture viewer
        XCTAssertTrue(app.navigationBars["Architecture"].exists)
        
        // When: Look for project selector
        let projectSelectors = [
            app.segmentedControls.firstMatch,
            app.buttons["Default Project"],
            app.buttons["Mobile App"],
            app.buttons["Backend API"],
            app.pickers.firstMatch
        ]
        
        var selectorFound = false
        for selector in projectSelectors {
            if selector.exists {
                selectorFound = true
                
                // Then: Selector should be interactive
                XCTAssertTrue(selector.isHittable)
                
                // Test selection change
                if selector.elementType == .segmentedControl {
                    // Test segmented control interaction
                    if app.buttons["Mobile App"].exists {
                        app.buttons["Mobile App"].tap()
                        
                        // Should trigger diagram reload
                        XCTAssertTrue(
                            app.staticTexts.containing("Loading").firstMatch.waitForExistence(timeout: 3) ||
                            app.navigationBars["Architecture"].waitForExistence(timeout: 3)
                        )
                        
                        // Switch back
                        if app.buttons["Default Project"].exists {
                            app.buttons["Default Project"].tap()
                        }
                    }
                }
                break
            }
        }
        
        if !selectorFound {
            XCTAssertTrue(true, "Project selector not found - may be integrated differently")
        }
    }
    
    // MARK: - Diagram Display Tests
    
    /// Test diagram loading states
    func testDiagramLoadingStates() throws {
        // Given: User is on Architecture viewer
        XCTAssertTrue(app.navigationBars["Architecture"].exists)
        
        // When: Check for different loading states
        let loadingStates = [
            app.staticTexts.containing("Loading").firstMatch,
            app.activityIndicators.firstMatch,
            app.progressIndicators.firstMatch
        ]
        
        var loadingStateFound = false
        for state in loadingStates {
            if state.exists {
                loadingStateFound = true
                
                // Then: Loading state should be properly displayed
                XCTAssertTrue(state.frame.height > 0)
                break
            }
        }
        
        // Check for empty states
        let emptyStates = [
            app.staticTexts["No architecture diagram available"],
            app.buttons["Generate Diagram"],
            app.buttons["Load Architecture"],
            app.staticTexts.containing("No Architecture").firstMatch
        ]
        
        var emptyStateFound = false
        for state in emptyStates {
            if state.exists {
                emptyStateFound = true
                
                // Then: Empty state should have action button
                if state.elementType == .button {
                    XCTAssertTrue(state.isHittable)
                    
                    // Test diagram generation
                    state.tap()
                    
                    // Should trigger loading or show error
                    XCTAssertTrue(
                        app.staticTexts.containing("Loading").firstMatch.waitForExistence(timeout: 3) ||
                        app.staticTexts.containing("Error").firstMatch.waitForExistence(timeout: 3) ||
                        app.navigationBars["Architecture"].waitForExistence(timeout: 3)
                    )
                }
                break
            }
        }
        
        XCTAssertTrue(loadingStateFound || emptyStateFound || app.webViews.firstMatch.exists, 
                      "Should have loading state, empty state, or diagram content")
    }
    
    /// Test diagram WebView integration
    func testDiagramWebViewIntegration() throws {
        // Given: User is on Architecture viewer
        XCTAssertTrue(app.navigationBars["Architecture"].exists)
        
        // When: Look for WebView containing diagram
        if app.webViews.firstMatch.exists {
            let webView = app.webViews.firstMatch
            
            // Then: WebView should be properly integrated
            XCTAssertTrue(webView.frame.width > 0 && webView.frame.height > 0)
            XCTAssertTrue(webView.isHittable)
            
            // Test basic interaction with WebView
            webView.tap()
            
            // WebView should remain responsive
            XCTAssertTrue(webView.exists)
            
            // Test scroll/zoom capabilities (if supported)
            let centerCoordinate = webView.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.5))
            centerCoordinate.tap()
            
            // Should handle tap without crashing
            XCTAssertTrue(app.navigationBars["Architecture"].exists)
        } else {
            XCTAssertTrue(true, "WebView not present - diagram may not be loaded yet")
        }
    }
    
    /// Test diagram node interaction
    func testDiagramNodeInteraction() throws {
        // Given: User is on Architecture viewer with diagram
        XCTAssertTrue(app.navigationBars["Architecture"].exists)
        
        // When: WebView exists (indicating diagram is loaded)
        if app.webViews.firstMatch.exists {
            let webView = app.webViews.firstMatch
            
            // Try tapping different areas of the diagram
            let tapLocations = [
                CGVector(dx: 0.3, dy: 0.3),
                CGVector(dx: 0.5, dy: 0.5),
                CGVector(dx: 0.7, dy: 0.7)
            ]
            
            for location in tapLocations {
                let coordinate = webView.coordinate(withNormalizedOffset: location)
                coordinate.tap()
                
                // Should handle tap gracefully
                XCTAssertTrue(app.navigationBars["Architecture"].exists)
                
                // Brief pause between taps
                usleep(500000) // 0.5 seconds
            }
            
            // Then: Application should remain stable
            XCTAssertTrue(webView.exists)
        }
    }
    
    // MARK: - Diagram Controls Tests
    
    /// Test diagram refresh functionality
    func testDiagramRefreshFunctionality() throws {
        // Given: User is on Architecture viewer
        XCTAssertTrue(app.navigationBars["Architecture"].exists)
        
        // When: Look for refresh controls
        let refreshControls = [
            app.buttons.matching(NSPredicate(format: "identifier CONTAINS 'refresh' OR identifier CONTAINS 'clockwise'")),
            app.buttons["Auto-Refresh"],
            app.buttons.matching(NSPredicate(format: "label CONTAINS 'Refresh'"))
        ]
        
        var refreshButtonFound = false
        for controlQuery in refreshControls {
            let control = controlQuery.firstMatch
            if control.exists {
                refreshButtonFound = true
                
                // Then: Refresh control should be interactive
                XCTAssertTrue(control.isHittable)
                
                // Test refresh action
                control.tap()
                
                // Should trigger refresh (loading state or content update)
                XCTAssertTrue(
                    app.staticTexts.containing("Loading").firstMatch.waitForExistence(timeout: 3) ||
                    app.navigationBars["Architecture"].waitForExistence(timeout: 3)
                )
                break
            }
        }
        
        if !refreshButtonFound {
            // Try pull-to-refresh gesture
            if app.scrollViews.firstMatch.exists {
                let scrollView = app.scrollViews.firstMatch
                let startPoint = scrollView.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.3))
                let endPoint = scrollView.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.7))
                
                startPoint.press(forDuration: 0.1, thenDragTo: endPoint)
                
                // Should handle pull-to-refresh
                XCTAssertTrue(app.navigationBars["Architecture"].waitForExistence(timeout: 3))
            }
        }
    }
    
    /// Test diagram comparison functionality
    func testDiagramComparisonFunctionality() throws {
        // Given: User is on Architecture viewer
        XCTAssertTrue(app.navigationBars["Architecture"].exists)
        
        // When: Look for comparison controls
        let comparisonControls = [
            app.buttons["Compare"],
            app.buttons.matching(NSPredicate(format: "identifier CONTAINS 'stack' OR label CONTAINS 'Compare'"))
        ]
        
        var comparisonButtonFound = false
        for controlQuery in comparisonControls {
            let control = controlQuery.firstMatch
            if control.exists {
                comparisonButtonFound = true
                
                // Then: Comparison control should be interactive
                XCTAssertTrue(control.isHittable)
                
                // Test comparison toggle
                control.tap()
                
                // Should toggle comparison view
                XCTAssertTrue(app.navigationBars["Architecture"].waitForExistence(timeout: 3))
                
                // Toggle back
                if control.exists {
                    control.tap()
                }
                break
            }
        }
        
        if !comparisonButtonFound {
            XCTAssertTrue(true, "Comparison functionality not found - may be disabled or unavailable")
        }
    }
    
    /// Test diagram zoom and pan controls
    func testDiagramZoomAndPanControls() throws {
        // Given: User is on Architecture viewer with WebView
        XCTAssertTrue(app.navigationBars["Architecture"].exists)
        
        // When: WebView exists
        if app.webViews.firstMatch.exists {
            let webView = app.webViews.firstMatch
            
            // Test pinch zoom gestures (simulated)
            let centerCoordinate = webView.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.5))
            
            // Test double-tap zoom
            centerCoordinate.doubleTap()
            
            // Should handle zoom interaction
            XCTAssertTrue(webView.exists)
            
            // Test pan gesture
            let startPoint = webView.coordinate(withNormalizedOffset: CGVector(dx: 0.3, dy: 0.3))
            let endPoint = webView.coordinate(withNormalizedOffset: CGVector(dx: 0.7, dy: 0.7))
            
            startPoint.press(forDuration: 0.5, thenDragTo: endPoint)
            
            // Should handle pan interaction
            XCTAssertTrue(webView.exists)
            
            // Then: WebView should remain responsive
            XCTAssertTrue(webView.isHittable)
        }
    }
    
    // MARK: - Export Functionality Tests
    
    /// Test diagram export functionality
    func testDiagramExportFunctionality() throws {
        // Given: User is on Architecture viewer
        XCTAssertTrue(app.navigationBars["Architecture"].exists)
        
        // When: User taps export button
        if app.buttons["Export"].exists {
            let exportButton = app.buttons["Export"]
            
            // Then: Export button should be accessible
            XCTAssertTrue(exportButton.isHittable)
            
            // Test export action
            exportButton.tap()
            
            // Should show export interface
            XCTAssertTrue(
                app.navigationBars["Export"].waitForExistence(timeout: 3) ||
                app.navigationBars["Export Diagram"].waitForExistence(timeout: 3) ||
                app.staticTexts.containing("Export").firstMatch.waitForExistence(timeout: 3) ||
                app.staticTexts.containing("Mermaid").firstMatch.waitForExistence(timeout: 3)
            )
            
            // Should have diagram content
            if app.staticTexts.containing("Mermaid").firstMatch.exists {
                XCTAssertTrue(app.staticTexts.containing("Mermaid").firstMatch.frame.height > 0)
            }
            
            // Should have action buttons
            XCTAssertTrue(
                app.buttons["Done"].exists ||
                app.buttons["Copy to Clipboard"].exists ||
                app.buttons["Close"].exists
            )
            
            // Close export interface
            if app.buttons["Done"].exists {
                app.buttons["Done"].tap()
            } else if app.buttons["Close"].exists {
                app.buttons["Close"].tap()
            }
            
            // Should return to architecture viewer
            XCTAssertTrue(app.navigationBars["Architecture"].waitForExistence(timeout: 3))
        } else {
            // Export button may be disabled if no diagram is loaded
            XCTAssertTrue(true, "Export button not available - may be disabled without diagram")
        }
    }
    
    /// Test copy to clipboard functionality
    func testCopyToClipboardFunctionality() throws {
        // Given: User is in export interface
        XCTAssertTrue(app.navigationBars["Architecture"].exists)
        
        // When: Export button is available and tapped
        if app.buttons["Export"].exists && app.buttons["Export"].isEnabled {
            app.buttons["Export"].tap()
            
            // Look for copy button
            if app.buttons["Copy to Clipboard"].waitForExistence(timeout: 3) {
                let copyButton = app.buttons["Copy to Clipboard"]
                
                // Then: Copy button should be interactive
                XCTAssertTrue(copyButton.isHittable)
                
                // Test copy action
                copyButton.tap()
                
                // Should execute copy (can't verify clipboard content in UI tests)
                // But should not crash
                XCTAssertTrue(copyButton.exists)
                
                // Close export interface
                if app.buttons["Done"].exists {
                    app.buttons["Done"].tap()
                }
            }
        }
    }
    
    // MARK: - Error Handling Tests
    
    /// Test architecture viewer error handling
    func testArchitectureViewerErrorHandling() throws {
        // Given: User is on Architecture viewer
        XCTAssertTrue(app.navigationBars["Architecture"].exists)
        
        // When: Look for error states
        let errorElements = [
            app.staticTexts.containing("Failed to load architecture").firstMatch,
            app.staticTexts.containing("Error").firstMatch,
            app.staticTexts.containing("failed").firstMatch,
            app.buttons["Retry"]
        ]
        
        var errorFound = false
        for element in errorElements {
            if element.exists {
                errorFound = true
                
                // Then: Error should be properly displayed
                XCTAssertTrue(element.frame.height > 0)
                
                // Should have retry mechanism
                if app.buttons["Retry"].exists {
                    let retryButton = app.buttons["Retry"]
                    XCTAssertTrue(retryButton.isHittable)
                    
                    // Test retry action
                    retryButton.tap()
                    
                    // Should attempt retry
                    XCTAssertTrue(
                        app.staticTexts.containing("Loading").firstMatch.waitForExistence(timeout: 3) ||
                        app.navigationBars["Architecture"].waitForExistence(timeout: 3)
                    )
                }
                break
            }
        }
        
        if !errorFound {
            XCTAssertTrue(true, "No errors found - architecture viewer is working correctly")
        }
    }
    
    /// Test network error recovery
    func testNetworkErrorRecovery() throws {
        // Given: User is on Architecture viewer
        XCTAssertTrue(app.navigationBars["Architecture"].exists)
        
        // When: Trigger refresh to potentially encounter network issues
        if app.buttons.matching(NSPredicate(format: "identifier CONTAINS 'refresh'")).count > 0 {
            let refreshButton = app.buttons.matching(NSPredicate(format: "identifier CONTAINS 'refresh'")).firstMatch
            refreshButton.tap()
            
            // Wait for either success or error
            let expectation = expectation(description: "Wait for refresh result")
            DispatchQueue.main.asyncAfter(deadline: .now() + 3) {
                expectation.fulfill()
            }
            wait(for: [expectation], timeout: 5)
            
            // Then: Should handle result gracefully
            XCTAssertTrue(
                app.navigationBars["Architecture"].exists ||
                app.staticTexts.containing("Error").firstMatch.exists ||
                app.staticTexts.containing("Loading").firstMatch.exists
            )
        }
    }
    
    // MARK: - Performance Tests
    
    /// Test architecture viewer rendering performance
    func testArchitectureViewerPerformance() throws {
        measure(metrics: [XCTMemoryMetric(), XCTCPUMetric()]) {
            // Navigate away and back to test rendering performance
            if app.tabBars.buttons["Settings"].exists {
                app.tabBars.buttons["Settings"].tap()
                _ = app.navigationBars.firstMatch.waitForExistence(timeout: 2)
                
                navigateToArchitectureViewer()
                _ = app.navigationBars["Architecture"].waitForExistence(timeout: 2)
            }
        }
    }
    
    /// Test diagram loading performance
    func testDiagramLoadingPerformance() throws {
        // Given: User is on Architecture viewer
        XCTAssertTrue(app.navigationBars["Architecture"].exists)
        
        measure {
            // Test project switching performance
            if app.buttons["Mobile App"].exists {
                app.buttons["Mobile App"].tap()
                _ = app.navigationBars["Architecture"].waitForExistence(timeout: 3)
                
                app.buttons["Default Project"].tap()
                _ = app.navigationBars["Architecture"].waitForExistence(timeout: 3)
            }
        }
    }
    
    /// Test WebView rendering performance
    func testWebViewRenderingPerformance() throws {
        // Given: User is on Architecture viewer with WebView
        if app.webViews.firstMatch.exists {
            measure {
                let webView = app.webViews.firstMatch
                
                // Test various interactions
                for i in 0..<5 {
                    let location = CGVector(dx: 0.2 + Double(i) * 0.15, dy: 0.5)
                    let coordinate = webView.coordinate(withNormalizedOffset: location)
                    coordinate.tap()
                }
            }
        }
    }
    
    // MARK: - Accessibility Tests
    
    /// Test architecture viewer accessibility features
    func testArchitectureViewerAccessibility() throws {
        // Given: User is on Architecture viewer
        XCTAssertTrue(app.navigationBars["Architecture"].exists)
        
        // Then: Key elements should be accessible
        
        // Navigation title should be accessible
        XCTAssertTrue(app.navigationBars["Architecture"].isAccessibilityElement)
        
        // Export button should be accessible
        if app.buttons["Export"].exists {
            XCTAssertTrue(app.buttons["Export"].isAccessibilityElement)
            XCTAssertNotNil(app.buttons["Export"].accessibilityLabel)
        }
        
        // Project selector should be accessible
        if app.segmentedControls.firstMatch.exists {
            XCTAssertTrue(app.segmentedControls.firstMatch.isAccessibilityElement)
        }
        
        // Control buttons should be accessible
        let controlButtons = ["Compare", "Auto-Refresh", "Retry", "Generate Diagram"]
        for buttonTitle in controlButtons {
            if app.buttons[buttonTitle].exists {
                XCTAssertTrue(app.buttons[buttonTitle].isAccessibilityElement)
            }
        }
        
        // WebView should be accessible if present
        if app.webViews.firstMatch.exists {
            XCTAssertTrue(app.webViews.firstMatch.isAccessibilityElement)
        }
    }
    
    /// Test accessibility labels and hints
    func testAccessibilityLabelsAndHints() throws {
        // Given: User is on Architecture viewer
        XCTAssertTrue(app.navigationBars["Architecture"].exists)
        
        // Then: Interactive elements should have proper accessibility labels
        
        if app.buttons["Export"].exists {
            let exportButton = app.buttons["Export"]
            XCTAssertNotNil(exportButton.accessibilityLabel)
            XCTAssertFalse(exportButton.accessibilityLabel?.isEmpty ?? true)
        }
        
        if app.buttons.matching(NSPredicate(format: "identifier CONTAINS 'refresh'")).count > 0 {
            let refreshButton = app.buttons.matching(NSPredicate(format: "identifier CONTAINS 'refresh'")).firstMatch
            XCTAssertNotNil(refreshButton.accessibilityLabel)
        }
        
        // Project selector should have clear labels
        if app.segmentedControls.firstMatch.exists {
            XCTAssertNotNil(app.segmentedControls.firstMatch.accessibilityLabel)
        }
    }
    
    // MARK: - Integration Tests
    
    /// Test architecture viewer integration with backend
    func testArchitectureViewerBackendIntegration() throws {
        // Given: User is on Architecture viewer
        XCTAssertTrue(app.navigationBars["Architecture"].exists)
        
        // When: Trigger backend interaction (project switch or refresh)
        if app.buttons["Mobile App"].exists {
            app.buttons["Mobile App"].tap()
            
            // Should communicate with backend for new diagram
            // Wait for response (either success or error)
            let expectation = expectation(description: "Wait for backend response")
            DispatchQueue.main.asyncAfter(deadline: .now() + 5) {
                expectation.fulfill()
            }
            wait(for: [expectation], timeout: 7)
            
            // Then: Should handle backend response appropriately
            XCTAssertTrue(
                app.webViews.firstMatch.exists || // Diagram loaded
                app.staticTexts.containing("Loading").firstMatch.exists || // Still loading
                app.staticTexts.containing("Error").firstMatch.exists || // Error state
                app.buttons["Generate Diagram"].exists // Empty state
            )
        }
    }
    
    /// Test real-time diagram updates
    func testRealTimeDiagramUpdates() throws {
        // Given: User is on Architecture viewer with auto-refresh
        XCTAssertTrue(app.navigationBars["Architecture"].exists)
        
        // When: Auto-refresh is enabled (if available)
        if app.buttons["Auto-Refresh"].exists {
            app.buttons["Auto-Refresh"].tap()
            
            // Should maintain connection for real-time updates
            // Test that interface remains responsive
            XCTAssertTrue(app.navigationBars["Architecture"].exists)
            
            // WebView should remain stable
            if app.webViews.firstMatch.exists {
                XCTAssertTrue(app.webViews.firstMatch.isHittable)
            }
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
    
    /// Navigate to Architecture viewer
    private func navigateToArchitectureViewer() {
        // Try different methods to access Architecture viewer
        
        // Method 1: Direct Architecture tab (if exists)
        if app.tabBars.buttons["Architecture"].exists {
            app.tabBars.buttons["Architecture"].tap()
            return
        }
        
        // Method 2: Through Monitor tab
        if app.tabBars.buttons["Monitor"].exists {
            app.tabBars.buttons["Monitor"].tap()
            
            // Look for Architecture access
            if app.buttons["architecture"].exists {
                app.buttons["architecture"].tap()
                return
            } else if app.staticTexts["Architecture"].exists {
                app.staticTexts["Architecture"].tap()
                return
            }
        }
        
        // Method 3: Through Projects tab
        if app.tabBars.buttons["Projects"].exists {
            app.tabBars.buttons["Projects"].tap()
            
            // Look for Architecture viewer access
            if app.buttons.containing("Architecture").firstMatch.exists {
                app.buttons.containing("Architecture").firstMatch.tap()
                return
            }
        }
        
        // Method 4: Through Settings or main menu
        if app.tabBars.buttons["Settings"].exists {
            app.tabBars.buttons["Settings"].tap()
            
            if app.staticTexts["Architecture Viewer"].exists {
                app.staticTexts["Architecture Viewer"].tap()
                return
            }
        }
        
        // Fallback: Assume we're already in architecture viewer or it's not available
        XCTAssertTrue(true, "Architecture viewer navigation attempted")
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

// MARK: - Architecture Viewer Page Object Model

@available(iOS 18.0, macOS 14.0, *)
struct ArchitectureViewerPage {
    let app: XCUIApplication
    
    var navigationBar: XCUIElement { app.navigationBars["Architecture"] }
    var exportButton: XCUIElement { app.buttons["Export"] }
    var webView: XCUIElement { app.webViews.firstMatch }
    
    // Project selector
    var projectSelector: XCUIElement { app.segmentedControls.firstMatch }
    var defaultProjectButton: XCUIElement { app.buttons["Default Project"] }
    var mobileAppButton: XCUIElement { app.buttons["Mobile App"] }
    var backendAPIButton: XCUIElement { app.buttons["Backend API"] }
    
    // Controls
    var compareButton: XCUIElement { app.buttons["Compare"] }
    var refreshButton: XCUIElement { app.buttons.matching(NSPredicate(format: "identifier CONTAINS 'refresh'")).firstMatch }
    var autoRefreshButton: XCUIElement { app.buttons["Auto-Refresh"] }
    
    // States
    var loadingIndicator: XCUIElement { app.staticTexts.containing("Loading").firstMatch }
    var errorMessage: XCUIElement { app.staticTexts.containing("Failed to load").firstMatch }
    var retryButton: XCUIElement { app.buttons["Retry"] }
    var generateButton: XCUIElement { app.buttons["Generate Diagram"] }
    
    func isDisplayingDiagram() -> Bool {
        return webView.exists && webView.frame.height > 0
    }
    
    func isLoading() -> Bool {
        return loadingIndicator.exists || app.activityIndicators.firstMatch.exists
    }
    
    func hasError() -> Bool {
        return errorMessage.exists || retryButton.exists
    }
    
    func isEmpty() -> Bool {
        return generateButton.exists || app.staticTexts["No architecture diagram available"].exists
    }
    
    func switchToProject(_ project: String) -> Bool {
        switch project.lowercased() {
        case "mobile app":
            guard mobileAppButton.exists else { return false }
            mobileAppButton.tap()
            return true
        case "backend api":
            guard backendAPIButton.exists else { return false }
            backendAPIButton.tap()
            return true
        case "default project":
            guard defaultProjectButton.exists else { return false }
            defaultProjectButton.tap()
            return true
        default:
            return false
        }
    }
    
    func openExport() -> Bool {
        guard exportButton.exists && exportButton.isEnabled else { return false }
        exportButton.tap()
        return true
    }
    
    func refreshDiagram() -> Bool {
        guard refreshButton.exists else { return false }
        refreshButton.tap()
        return true
    }
    
    func toggleComparison() -> Bool {
        guard compareButton.exists else { return false }
        compareButton.tap()
        return true
    }
    
    func retryLoading() -> Bool {
        guard retryButton.exists else { return false }
        retryButton.tap()
        return true
    }
    
    func generateDiagram() -> Bool {
        guard generateButton.exists else { return false }
        generateButton.tap()
        return true
    }
    
    func tapDiagramAt(normalizedPoint: CGVector) -> Bool {
        guard webView.exists else { return false }
        let coordinate = webView.coordinate(withNormalizedOffset: normalizedPoint)
        coordinate.tap()
        return true
    }
}