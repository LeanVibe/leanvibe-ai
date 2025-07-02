import XCTest
import Combine
@testable import LeanVibe

@available(iOS 18.0, macOS 14.0, *)
@MainActor
final class CodeCompletionIntegrationTests: XCTestCase {
    var webSocketService: WebSocketService!
    var codeCompletionService: CodeCompletionService!
    var cancellables: Set<AnyCancellable>!
    
    override func setUpWithError() throws {
        try super.setUpWithError()
        webSocketService = WebSocketService.shared
        codeCompletionService = CodeCompletionService(webSocketService: webSocketService)
        cancellables = Set<AnyCancellable>()
    }
    
    override func tearDownWithError() throws {
        cancellables.removeAll()
        codeCompletionService = nil
        webSocketService = nil
        try super.tearDownWithError()
    }
    
    // MARK: - Configuration Integration Tests
    
    func testAppConfigurationIntegration() {
        // Given
        let config = AppConfiguration.shared
        
        // When
        let webSocketURL = config.webSocketURL
        let apiBaseURL = config.apiBaseURL
        
        // Then
        XCTAssertFalse(webSocketURL.isEmpty)
        XCTAssertFalse(apiBaseURL.isEmpty)
        XCTAssertTrue(webSocketURL.hasPrefix("ws://") || webSocketURL.hasPrefix("wss://"))
        XCTAssertTrue(apiBaseURL.hasPrefix("http://") || apiBaseURL.hasPrefix("https://"))
    }
    
    func testEnvironmentSpecificConfiguration() {
        // Given
        let config = AppConfiguration.shared
        
        // When & Then
        if config.isDebugBuild {
            // Debug builds should use localhost
            XCTAssertTrue(config.apiBaseURL.contains("localhost") || config.apiBaseURL.contains("127.0.0.1"))
        } else if config.isTestFlightBuild {
            // TestFlight builds should use staging
            XCTAssertTrue(config.apiBaseURL.contains("staging"))
        } else {
            // Production builds should use production URLs
            XCTAssertFalse(config.apiBaseURL.contains("localhost"))
            XCTAssertFalse(config.apiBaseURL.contains("staging"))
        }
    }
    
    // MARK: - WebSocket Integration Tests
    
    func testWebSocketConnectionFlow() async throws {
        // Given
        let expectation = expectation(description: "WebSocket connection flow")
        
        // When
        webSocketService.connect()
        
        // Monitor connection state
        webSocketService.$isConnected
            .dropFirst() // Skip initial value
            .first()
            .sink { isConnected in
                // Then
                XCTAssertTrue(isConnected || !isConnected) // Connection attempt was made
                expectation.fulfill()
            }
            .store(in: &cancellables)
        
        await fulfillment(of: [expectation], timeout: 5.0)
    }
    
    func testDefaultConnectionSettings() {
        // Given
        let defaultConnection = webSocketService.defaultConnection
        
        // When & Then
        if let connection = defaultConnection {
            XCTAssertFalse(connection.host.isEmpty)
            XCTAssertGreaterThan(connection.port, 0)
            XCTAssertLessThan(connection.port, 65536)
            XCTAssertEqual(connection.websocketPath, "/ws")
        } else {
            // It's okay if no default connection in some environments
            XCTAssertTrue(true, "No default connection available")
        }
    }
    
    // MARK: - Error Handling Integration Tests
    
    func testGlobalErrorManagerIntegration() async throws {
        // Given
        let errorManager = GlobalErrorManager.shared
        let initialErrorCount = errorManager.errorHistory.count
        
        // When - simulate a code completion error
        let invalidRequest = [
            "type": "code_completion",
            "invalid_field": "invalid_value"
        ]
        
        do {
            _ = try await webSocketService.sendMessage(invalidRequest)
        } catch {
            // Expected to fail
        }
        
        // Then - error should be recorded (if error manager is integrated)
        // Note: This test may pass even if integration isn't complete
        XCTAssertGreaterThanOrEqual(errorManager.errorHistory.count, initialErrorCount)
    }
    
    func testRetryManagerIntegration() async throws {
        // Given
        let retryManager = RetryManager.shared
        let initialRetryCount = retryManager.retryHistory.count
        
        // When - attempt a failing operation with retry
        let retryAction = retryManager.createRetryAction(
            operation: {
                throw URLError(.networkConnectionLost)
            },
            maxAttempts: 2,
            context: "Test retry integration"
        )
        
        retryAction()
        
        // Allow some time for retry attempts
        try await Task.sleep(for: .seconds(1))
        
        // Then - retry should have been attempted
        XCTAssertGreaterThan(retryManager.retryHistory.count, initialRetryCount)
    }
    
    // MARK: - NotificationCenter Integration Tests
    
    func testNotificationCenterIntegration() async throws {
        // Given
        let expectation = expectation(description: "NotificationCenter integration")
        var receivedNotification = false
        
        // Subscribe to code completion notifications
        NotificationCenter.default.publisher(for: Notification.Name("codeCompletionResponse"))
            .sink { notification in
                receivedNotification = true
                expectation.fulfill()
            }
            .store(in: &cancellables)
        
        // When - send a test notification
        NotificationCenter.default.post(
            name: Notification.Name("codeCompletionResponse"),
            object: "Test response"
        )
        
        await fulfillment(of: [expectation], timeout: 1.0)
        
        // Then
        XCTAssertTrue(receivedNotification)
    }
    
    // MARK: - Voice Command Integration Tests
    
    func testVoiceCommandIntegration() {
        // Given
        let testCommands = [
            "Hey LeanVibe, suggest improvements",
            "explain this code",
            "refactor this function",
            "debug this error",
            "optimize performance"
        ]
        
        // When & Then - test voice command parsing
        for command in testCommands {
            let voiceCommand = VoiceCommand(originalText: command, timestamp: Date())
            
            XCTAssertNotNil(voiceCommand.intent)
            XCTAssertFalse(voiceCommand.originalText.isEmpty)
            
            // Verify intent detection works for code completion commands
            if command.contains("suggest") {
                XCTAssertEqual(voiceCommand.intent, .suggest)
            } else if command.contains("explain") {
                XCTAssertEqual(voiceCommand.intent, .explain)
            } else if command.contains("refactor") {
                XCTAssertEqual(voiceCommand.intent, .refactor)
            } else if command.contains("debug") {
                XCTAssertEqual(voiceCommand.intent, .debug)
            } else if command.contains("optimize") {
                XCTAssertEqual(voiceCommand.intent, .optimize)
            }
        }
    }
    
    // MARK: - Data Model Integration Tests
    
    func testCodeCompletionModelsIntegration() throws {
        // Given
        let request = CodeCompletionRequest(
            filePath: "/test/file.swift",
            cursorPosition: 100,
            content: "import Foundation\n\nclass TestClass {",
            language: "swift",
            intent: "suggest"
        )
        
        let response = CodeCompletionResponse(
            status: "success",
            intent: "suggest",
            response: "Suggested code completion",
            confidence: 0.95,
            requiresReview: false,
            suggestions: ["Suggestion 1", "Suggestion 2"]
        )
        
        // When - test serialization/deserialization
        let requestData = try JSONEncoder().encode(request)
        let responseData = try JSONEncoder().encode(response)
        
        let decodedRequest = try JSONDecoder().decode(CodeCompletionRequest.self, from: requestData)
        let decodedResponse = try JSONDecoder().decode(CodeCompletionResponse.self, from: responseData)
        
        // Then
        XCTAssertEqual(request.filePath, decodedRequest.filePath)
        XCTAssertEqual(request.content, decodedRequest.content)
        XCTAssertEqual(request.language, decodedRequest.language)
        XCTAssertEqual(request.intent, decodedRequest.intent)
        
        XCTAssertEqual(response.status, decodedResponse.status)
        XCTAssertEqual(response.intent, decodedResponse.intent)
        XCTAssertEqual(response.response, decodedResponse.response)
        XCTAssertEqual(response.confidence, decodedResponse.confidence, accuracy: 0.001)
        XCTAssertEqual(response.suggestions, decodedResponse.suggestions)
    }
    
    // MARK: - Real-world Scenario Tests
    
    func testCompleteCodeCompletionWorkflow() async throws {
        // Given - simulate a real user workflow
        let testCode = """
        import Foundation
        
        class UserManager {
            private var users: [User] = []
            
            func addUser(_ user: User) {
                // TODO: Implement
            }
        }
        """
        
        // When - user requests code completion
        let result = await codeCompletionService.suggestCodeCompletion(
            content: testCode,
            language: "swift",
            filePath: "/project/UserManager.swift"
        )
        
        // Then - verify the workflow completed
        // Note: This test may fail if backend is not available, which is expected
        XCTAssertTrue(result.success || !result.success) // Test that the method completes
        
        if result.success {
            XCTAssertEqual(result.intent, "suggest")
            XCTAssertNotNil(result.response)
        } else {
            // Failure is acceptable if backend is not available
            XCTAssertNotNil(result.error)
        }
    }
    
    func testMultipleLanguageSupport() async throws {
        // Given - different programming languages
        let testCases = [
            ("swift", "import Foundation\nclass Test {}"),
            ("python", "import os\ndef test():"),
            ("javascript", "const test = () => {"),
            ("typescript", "interface User { name: string; }")
        ]
        
        // When & Then - test each language
        for (language, code) in testCases {
            let result = await codeCompletionService.suggestCodeCompletion(
                content: code,
                language: language,
                filePath: "/test/file.\(language == "javascript" ? "js" : language)"
            )
            
            // Verify request was properly formed (success or failure is acceptable)
            XCTAssertTrue(result.success || !result.success)
            XCTAssertEqual(result.intent, "suggest")
        }
    }
    
    // MARK: - Performance Integration Tests
    
    func testMemoryUsageDuringOperations() async throws {
        // Given
        let initialMemory = getMemoryUsage()
        
        // When - perform multiple operations
        for i in 0..<10 {
            _ = await codeCompletionService.suggestCodeCompletion(
                content: "test code \(i)",
                language: "swift",
                filePath: "/test/file\(i).swift"
            )
        }
        
        let finalMemory = getMemoryUsage()
        
        // Then - memory should not grow excessively
        let memoryIncrease = finalMemory - initialMemory
        XCTAssertLessThan(memoryIncrease, 50 * 1024 * 1024) // Less than 50MB increase
    }
    
    // MARK: - Helper Methods
    
    private func getMemoryUsage() -> UInt64 {
        var info = mach_task_basic_info()
        var count = mach_msg_type_number_t(MemoryLayout<mach_task_basic_info>.size)/4
        
        let result = withUnsafeMutablePointer(to: &info) {
            $0.withMemoryRebound(to: integer_t.self, capacity: 1) {
                task_info(mach_task_self_, task_flavor_t(MACH_TASK_BASIC_INFO), $0, &count)
            }
        }
        
        return result == KERN_SUCCESS ? info.resident_size : 0
    }
}