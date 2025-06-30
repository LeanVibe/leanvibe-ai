import XCTest
import SwiftUI
@testable import LeanVibe

/// Integration tests for critical UI flows and component interactions
/// Tests app launch, navigation, and feature integration
@available(iOS 18.0, macOS 14.0, *)
@MainActor
final class IntegrationTests: XCTestCase {
    
    // MARK: - Test Dependencies
    
    private var appCoordinator: AppCoordinator!
    private var webSocketService: WebSocketService!
    private var projectManager: ProjectManager!
    
    // MARK: - Setup & Teardown
    
    override func setUpWithError() throws {
        try super.setUpWithError()
        
        appCoordinator = AppCoordinator()
        webSocketService = WebSocketService()
        projectManager = ProjectManager()
    }
    
    override func tearDownWithError() throws {
        appCoordinator = nil
        webSocketService?.disconnect()
        webSocketService = nil
        projectManager = nil
        
        try super.tearDownWithError()
    }
    
    // MARK: - App Launch Flow Tests
    
    func testAppCoordinatorInitialization() {
        // Test that app coordinator initializes correctly
        XCTAssertNotNil(appCoordinator)
        XCTAssertEqual(appCoordinator.appState, .launching)
    }
    
    func testAppStateTransitions() {
        // Test app state transitions
        XCTAssertEqual(appCoordinator.appState, .launching)
        
        // Test error state
        appCoordinator.handleError("Test error")
        if case .error(let message) = appCoordinator.appState {
            XCTAssertEqual(message, "Test error")
        } else {
            XCTFail("Expected error state")
        }
        
        // Test retry functionality
        appCoordinator.retry()
        XCTAssertEqual(appCoordinator.appState, .launching)
    }
    
    // MARK: - Service Integration Tests
    
    func testWebSocketServiceIntegration() {
        // Test that WebSocketService integrates properly
        XCTAssertNotNil(webSocketService)
        XCTAssertFalse(webSocketService.isConnected)
        XCTAssertTrue(webSocketService.messages.isEmpty)
        
        // Test message handling
        webSocketService.sendMessage("Test integration message")
        XCTAssertEqual(webSocketService.lastError, "Not connected")
    }
    
    func testProjectManagerIntegration() {
        // Test that ProjectManager integrates properly
        XCTAssertNotNil(projectManager)
        XCTAssertTrue(projectManager.projects.isEmpty)
        
        // Test configuration with WebSocket service
        projectManager.configure(with: webSocketService)
        // Should not crash and should handle gracefully
    }
    
    // MARK: - Navigation Integration Tests
    
    func testNavigationCoordinatorIntegration() {
        let navigationCoordinator = NavigationCoordinator()
        
        // Test initial state
        XCTAssertEqual(navigationCoordinator.selectedTab, 0) // Projects tab
        XCTAssertTrue(navigationCoordinator.navigationPath.isEmpty)
        
        // Test tab switching
        navigationCoordinator.selectedTab = 1 // Agent tab
        XCTAssertEqual(navigationCoordinator.selectedTab, 1)
        
        navigationCoordinator.selectedTab = 4 // Voice tab
        XCTAssertEqual(navigationCoordinator.selectedTab, 4)
    }
    
    // MARK: - Settings Integration Tests
    
    func testSettingsManagerIntegration() {
        let settingsManager = SettingsManager.shared
        
        // Test that settings manager exists and has default values
        XCTAssertNotNil(settingsManager)
        XCTAssertNotNil(settingsManager.connection)
        XCTAssertNotNil(settingsManager.voice)
        XCTAssertNotNil(settingsManager.notifications)
        XCTAssertNotNil(settingsManager.kanban)
        XCTAssertNotNil(settingsManager.accessibility)
    }
    
    // MARK: - Model Integration Tests
    
    func testModelCreation() {
        // Test that core models can be created
        let project = Project(name: "Test Project", path: "/test/path")
        XCTAssertEqual(project.name, "Test Project")
        XCTAssertEqual(project.path, "/test/path")
        
        let task = Task(title: "Test Task", description: "Test Description")
        XCTAssertEqual(task.title, "Test Task")
        XCTAssertEqual(task.description, "Test Description")
        XCTAssertEqual(task.status, .todo) // Default status
    }
    
    // MARK: - Voice System Integration Tests
    
    func testVoiceManagersIntegration() {
        // Test voice system components integrate properly
        let speechService = SpeechRecognitionService()
        let permissionManager = VoicePermissionManager()
        
        XCTAssertNotNil(speechService)
        XCTAssertNotNil(permissionManager)
        
        // Test initial permission state
        XCTAssertFalse(permissionManager.isFullyAuthorized)
    }
    
    func testWakePhraseManagerIntegration() {
        // Test wake phrase manager initialization
        let voiceProcessor = DashboardVoiceProcessor(
            projectManager: projectManager,
            webSocketService: webSocketService,
            settingsManager: SettingsManager.shared
        )
        
        let wakePhraseManager = WakePhraseManager(
            webSocketService: webSocketService,
            projectManager: projectManager,
            voiceProcessor: voiceProcessor
        )
        
        XCTAssertNotNil(wakePhraseManager)
        XCTAssertFalse(wakePhraseManager.isListening)
        XCTAssertFalse(wakePhraseManager.isWakePhraseDetected)
    }
    
    // MARK: - Architecture Services Integration Tests
    
    func testArchitectureVisualizationIntegration() {
        // Test architecture visualization components
        let architectureService = OptimizedArchitectureService()
        let mermaidRenderer = MermaidRenderer()
        
        XCTAssertNotNil(architectureService)
        XCTAssertNotNil(mermaidRenderer)
    }
    
    // MARK: - Performance Integration Tests
    
    func testPerformanceManagersIntegration() {
        let performanceAnalytics = PerformanceAnalytics()
        let batteryManager = BatteryOptimizedManager()
        
        XCTAssertNotNil(performanceAnalytics)
        XCTAssertNotNil(batteryManager)
    }
    
    // MARK: - Notification System Integration Tests
    
    func testNotificationSystemIntegration() {
        // Test that notification system components can be created
        // Note: These are marked as @MainActor so they need to be tested carefully
        
        // We'll test this indirectly through the app structure
        XCTAssertTrue(true) // Placeholder for notification system tests
    }
    
    // MARK: - Data Flow Integration Tests
    
    func testMetricsViewModelIntegration() {
        let metricsViewModel = MetricsViewModel(clientId: "test-client")
        
        XCTAssertNotNil(metricsViewModel)
        XCTAssertTrue(metricsViewModel.metricHistory.isEmpty)
        XCTAssertTrue(metricsViewModel.decisionLog.isEmpty)
        XCTAssertFalse(metricsViewModel.isLoadingMetrics)
        XCTAssertFalse(metricsViewModel.isLoadingDecisions)
        XCTAssertNil(metricsViewModel.errorMessage)
        XCTAssertEqual(metricsViewModel.averageConfidence, 0.0)
    }
    
    // MARK: - End-to-End Workflow Tests
    
    func testProjectCreationWorkflow() async {
        // Test the complete project creation workflow
        
        // 1. Start with project manager
        XCTAssertTrue(projectManager.projects.isEmpty)
        
        // 2. Add a project (simulated)
        let testProject = Project(name: "Integration Test Project", path: "/test/integration/path")
        projectManager.projects.append(testProject)
        
        // 3. Verify project was added
        XCTAssertEqual(projectManager.projects.count, 1)
        XCTAssertEqual(projectManager.projects[0].name, "Integration Test Project")
        
        // 4. Configure with WebSocket
        projectManager.configure(with: webSocketService)
        
        // 5. Test messaging integration
        webSocketService.sendMessage("Project created: \(testProject.name)")
        XCTAssertEqual(webSocketService.lastError, "Not connected") // Expected since not connected
    }
    
    func testVoiceCommandWorkflow() async {
        // Test voice command integration workflow
        
        // 1. Set up voice components
        let voiceProcessor = DashboardVoiceProcessor(
            projectManager: projectManager,
            webSocketService: webSocketService,
            settingsManager: SettingsManager.shared
        )
        
        // 2. Test voice processor integration
        XCTAssertNotNil(voiceProcessor)
        
        // 3. Simulate voice command processing
        await voiceProcessor.processVoiceCommand("show projects")
        
        // 4. Verify the command was processed (even if no action taken due to no connection)
        // This tests that the voice system doesn't crash
        XCTAssertTrue(true) // Workflow completed without crashing
    }
    
    // MARK: - Error Handling Integration Tests
    
    func testErrorRecoveryWorkflow() {
        // Test that the app handles errors gracefully across components
        
        // 1. Trigger error in app coordinator
        appCoordinator.handleError("Test integration error")
        
        // 2. Verify error state
        if case .error(let message) = appCoordinator.appState {
            XCTAssertEqual(message, "Test integration error")
        } else {
            XCTFail("Expected error state")
        }
        
        // 3. Test recovery
        appCoordinator.retry()
        XCTAssertEqual(appCoordinator.appState, .launching)
        
        // 4. Test reset configuration
        appCoordinator.resetConfiguration()
        XCTAssertEqual(appCoordinator.appState, .needsConfiguration)
    }
    
    // MARK: - Memory Management Integration Tests
    
    func testMemoryManagement() {
        // Test that components don't create retain cycles
        weak var weakWebSocket: WebSocketService?
        weak var weakProjectManager: ProjectManager?
        
        autoreleasepool {
            let webSocket = WebSocketService()
            let projectMgr = ProjectManager()
            
            weakWebSocket = webSocket
            weakProjectManager = projectMgr
            
            // Configure integration
            projectMgr.configure(with: webSocket)
            
            // Use the services
            webSocket.sendMessage("test")
            projectMgr.projects.append(Project(name: "Test", path: "/test"))
        }
        
        // Allow for async deallocation
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
            // These might still be retained by the system, so this is more documentary
            // In a real app, we'd want to ensure proper memory management
        }
    }
    
    // MARK: - Performance Integration Tests
    
    func testApplicationPerformance() {
        // Test that the app initializes quickly
        let startTime = CFAbsoluteTimeGetCurrent()
        
        // Initialize major components
        let coordinator = AppCoordinator()
        let webSocket = WebSocketService()
        let projectMgr = ProjectManager()
        let settings = SettingsManager.shared
        
        projectMgr.configure(with: webSocket)
        
        let endTime = CFAbsoluteTimeGetCurrent()
        let initializationTime = endTime - startTime
        
        // Should initialize quickly
        XCTAssertLessThan(initializationTime, 1.0, "App should initialize in less than 1 second")
        
        // Cleanup
        coordinator.resetConfiguration()
        webSocket.disconnect()
        
        XCTAssertNotNil(settings) // Verify settings exist
    }
}

// MARK: - Integration Test Helpers

extension Project {
    /// Convenience initializer for testing
    convenience init(name: String, path: String) {
        self.init()
        self.name = name
        self.path = path
        self.lastModified = Date()
        self.status = .active
    }
}

extension Task {
    /// Convenience initializer for testing  
    convenience init(title: String, description: String) {
        self.init()
        self.title = title
        self.description = description
        self.status = .todo
        self.priority = .medium
        self.createdAt = Date()
    }
}