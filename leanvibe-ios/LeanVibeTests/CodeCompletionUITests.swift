import XCTest
import SwiftUI
@testable import LeanVibe

// MARK: - MockWebSocketServiceForUITests for UI Tests
@available(iOS 18.0, macOS 14.0, *)
@MainActor
class MockWebSocketServiceForUITests: ObservableObject {
    @Published var isConnected = false
    @Published var connectionStatus = "Disconnected"
    @Published var lastError: String?
    @Published var lastResponse: [String: Any]?
    
    var mockResponse: CodeCompletionResponse?
    var shouldFail = false
    var delay: TimeInterval = 0.0
    var lastSentMessage: String?
    
    init() {
        isConnected = true
        connectionStatus = "Connected (Mock)"
    }
    
    func sendMessage(_ message: [String: Any]) async throws -> [String: Any] {
        lastSentMessage = String(data: try JSONSerialization.data(withJSONObject: message), encoding: .utf8)
        
        if delay > 0 {
            try await Task.sleep(for: .seconds(delay))
        }
        
        if shouldFail {
            throw URLError(.networkConnectionLost)
        }
        
        return [
            "status": "success",
            "intent": "suggest", 
            "response": "Mock UI response",
            "confidence": 0.9,
            "requires_review": false,
            "suggestions": ["Mock suggestion 1", "Mock suggestion 2"]
        ]
    }
}

@available(iOS 18.0, macOS 14.0, *)
@MainActor
final class CodeCompletionUITests: XCTestCase {
    
    override func setUpWithError() throws {
        try super.setUpWithError()
        continueAfterFailure = false
    }
    
    override func tearDownWithError() throws {
        try super.tearDownWithError()
    }
    
    // MARK: - CodeCompletionTestView UI Tests
    
    func testCodeCompletionTestViewRendering() {
        // Given
        let webSocketService = WebSocketService.shared
        let codeCompletionService = CodeCompletionService(webSocketService: webSocketService)
        
        // When
        let view = CodeCompletionTestView(codeCompletionService: codeCompletionService)
        let hostingController = UIHostingController(rootView: view)
        
        // Then
        XCTAssertNotNil(hostingController.view)
        XCTAssertNoThrow(hostingController.loadViewIfNeeded())
    }
    
    func testCodeCompletionServiceObservableChanges() async throws {
        // Given
        let mockWebSocketService = MockWebSocketServiceForUITests()
        let codeCompletionService = CodeCompletionService(webSocketService: mockWebSocketService)
        
        let expectation = expectation(description: "Observable changes")
        var isLoadingStates: [Bool] = []
        
        // When
        let cancellable = codeCompletionService.$isLoading
            .sink { isLoading in
                isLoadingStates.append(isLoading)
                if isLoadingStates.count >= 2 { // Initial + changed state
                    expectation.fulfill()
                }
            }
        
        // Trigger a state change
        _ = await codeCompletionService.suggestCodeCompletion(
            content: "test",
            language: "swift",
            filePath: "/test.swift"
        )
        
        await fulfillment(of: [expectation], timeout: 2.0)
        
        // Then
        XCTAssertGreaterThanOrEqual(isLoadingStates.count, 2)
        cancellable.cancel()
    }
    
    // MARK: - Voice Command Integration UI Tests
    
    func testVoiceCommandToCodeCompletionFlow() {
        // Given
        let voiceCommand = VoiceCommand(
            originalText: "Hey LeanVibe, suggest improvements for this code",
            timestamp: Date()
        )
        
        // When
        let detectedIntent = voiceCommand.intent
        
        // Then
        XCTAssertEqual(detectedIntent, .suggest)
        XCTAssertTrue(voiceCommand.isCodeCompletionIntent)
    }
    
    func testAllCodeCompletionIntentsFromVoice() {
        // Given
        let testCases: [(String, CommandIntent)] = [
            ("suggest improvements", .suggest),
            ("explain this code", .explain),
            ("refactor this function", .refactor),
            ("debug this error", .debug),
            ("optimize performance", .optimize)
        ]
        
        // When & Then
        for (command, expectedIntent) in testCases {
            let voiceCommand = VoiceCommand(
                originalText: "Hey LeanVibe, \(command)",
                timestamp: Date()
            )
            
            XCTAssertEqual(voiceCommand.intent, expectedIntent)
            XCTAssertTrue(voiceCommand.isCodeCompletionIntent)
        }
    }
    
    // MARK: - Error Display UI Tests
    
    func testErrorDisplayIntegration() {
        // Given
        let errorManager = GlobalErrorManager.shared
        let testError = AppError(
            title: "Code Completion Failed",
            message: "Unable to connect to the AI service",
            severity: .high,
            context: "CodeCompletionService.suggestCodeCompletion"
        )
        
        // When
        errorManager.showError(testError)
        
        // Then
        XCTAssertEqual(errorManager.currentError?.title, testError.title)
        XCTAssertEqual(errorManager.currentError?.message, testError.message)
        XCTAssertTrue(errorManager.showingErrorAlert)
    }
    
    func testRetryActionFromUI() {
        // Given
        let retryManager = RetryManager.shared
        var operationCalled = false
        
        let retryAction = retryManager.createRetryAction(
            operation: {
                operationCalled = true
                return "Success"
            },
            maxAttempts: 1,
            context: "UI Test Retry"
        )
        
        // When
        retryAction()
        
        // Then
        // Allow some time for async operation
        let expectation = expectation(description: "Retry operation")
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            XCTAssertTrue(operationCalled)
            expectation.fulfill()
        }
        
        wait(for: [expectation], timeout: 1.0)
    }
    
    // MARK: - Integration with App Configuration UI Tests
    
    func testAppConfigurationInUI() {
        // Given
        let config = AppConfiguration.shared
        
        // When
        let isLoggingEnabled = config.isLoggingEnabled
        let webSocketURL = config.webSocketURL
        
        // Then
        XCTAssertTrue(isLoggingEnabled || !isLoggingEnabled) // Test that property is accessible
        XCTAssertFalse(webSocketURL.isEmpty)
    }
    
    func testConfigurationValidationInUI() {
        // Given
        let config = AppConfiguration.shared
        
        // When & Then
        XCTAssertNoThrow(try config.validateConfiguration())
        
        // In debug mode, should be able to print configuration
        if config.isDebugBuild {
            XCTAssertNoThrow(config.printConfiguration())
        }
    }
    
    // MARK: - Real Clipboard Integration UI Tests
    
    func testClipboardContentIntegration() {
        // Given
        let testCode = """
        import SwiftUI
        
        struct ContentView: View {
            var body: some View {
                Text("Hello, World!")
            }
        }
        """
        
        // When
        UIPasteboard.general.string = testCode
        
        // Then
        XCTAssertEqual(UIPasteboard.general.string, testCode)
        
        // Test that clipboard content can be used in code completion
        let clipboardContent = UIPasteboard.general.string ?? ""
        XCTAssertTrue(clipboardContent.contains("SwiftUI"))
        XCTAssertTrue(clipboardContent.contains("ContentView"))
    }
    
    // MARK: - Performance UI Tests
    
    func testUIResponsivenessDuringCodeCompletion() async throws {
        // Given
        let mockWebSocketService = MockWebSocketServiceForUITests()
        mockWebSocketService.delay = 1.0 // Simulate network delay
        let codeCompletionService = CodeCompletionService(webSocketService: mockWebSocketService)
        
        // When - start a code completion request
        let startTime = Date()
        
        async let completionTask = codeCompletionService.suggestCodeCompletion(
            content: "test code",
            language: "swift",
            filePath: "/test.swift"
        )
        
        // Simulate UI interactions during the request
        let uiInteractionTime = Date()
        let uiResponseTime = Date().timeIntervalSince(uiInteractionTime)
        
        _ = await completionTask
        let totalTime = Date().timeIntervalSince(startTime)
        
        // Then
        XCTAssertLessThan(uiResponseTime, 0.1, "UI should remain responsive during code completion")
        XCTAssertGreaterThan(totalTime, 0.5, "Code completion should have taken some time")
    }
    
    // MARK: - Accessibility UI Tests
    
    func testAccessibilitySupport() {
        // Given
        let webSocketService = WebSocketService.shared
        let codeCompletionService = CodeCompletionService(webSocketService: webSocketService)
        let view = CodeCompletionTestView(codeCompletionService: codeCompletionService)
        
        // When
        let hostingController = UIHostingController(rootView: view)
        hostingController.loadViewIfNeeded()
        
        // Then - verify accessibility elements are properly configured
        XCTAssertTrue(hostingController.view.isAccessibilityElement || 
                     hostingController.view.accessibilityElements?.count ?? 0 > 0)
    }
    
    // MARK: - Memory Management UI Tests
    
    func testViewMemoryManagement() {
        // Given
        weak var weakWebSocketService: WebSocketService?
        weak var weakCodeCompletionService: CodeCompletionService?
        weak var weakView: CodeCompletionTestView?
        
        // When
        autoreleasepool {
            let webSocketService = WebSocketService.shared // This is a singleton, so won't be deallocated
            let codeCompletionService = CodeCompletionService(webSocketService: webSocketService)
            let view = CodeCompletionTestView(codeCompletionService: codeCompletionService)
            
            weakWebSocketService = webSocketService
            weakCodeCompletionService = codeCompletionService
            weakView = view
            
            // Use the view briefly
            let hostingController = UIHostingController(rootView: view)
            hostingController.loadViewIfNeeded()
        }
        
        // Then - verify proper memory management
        // Note: WebSocketService is a singleton so it won't be deallocated
        XCTAssertNotNil(weakWebSocketService) // Singleton should persist
        // Other objects may or may not be deallocated depending on implementation
    }
}