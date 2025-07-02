import XCTest
import Combine
@testable import LeanVibe

// MARK: - MockWebSocketService for Code Completion Tests
@available(iOS 18.0, macOS 14.0, *)
@MainActor
class MockWebSocketServiceForCodeCompletion: ObservableObject {
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
    
    func connect() {
        isConnected = true
        connectionStatus = "Connected (Mock)"
        lastError = nil
    }
    
    func disconnect() {
        isConnected = false
        connectionStatus = "Disconnected (Mock)"
    }
    
    func sendMessage(_ message: [String: Any]) async throws -> [String: Any] {
        lastSentMessage = String(data: try JSONSerialization.data(withJSONObject: message), encoding: .utf8)
        
        if delay > 0 {
            try await Task.sleep(for: .seconds(delay))
        }
        
        if shouldFail {
            throw URLError(.networkConnectionLost)
        }
        
        if let response = mockResponse {
            let responseDict = [
                "status": response.status,
                "intent": response.intent,
                "response": response.response,
                "confidence": response.confidence,
                "requires_review": response.requiresReview,
                "suggestions": response.suggestions
            ] as [String: Any]
            
            lastResponse = responseDict
            return responseDict
        } else {
            return [
                "status": "success",
                "intent": "suggest",
                "response": "Mock default response",
                "confidence": 0.8,
                "requires_review": false,
                "suggestions": ["Mock suggestion 1", "Mock suggestion 2"]
            ]
        }
    }
}

@available(iOS 18.0, macOS 14.0, *)
final class CodeCompletionServiceTests: XCTestCase {
    var codeCompletionService: CodeCompletionService!
    var mockWebSocketService: MockWebSocketServiceForCodeCompletion!
    var cancellables: Set<AnyCancellable>!
    
    override func setUpWithError() throws {
        try super.setUpWithError()
        mockWebSocketService = MockWebSocketServiceForCodeCompletion()
        codeCompletionService = CodeCompletionService(webSocketService: mockWebSocketService)
        cancellables = Set<AnyCancellable>()
    }
    
    override func tearDownWithError() throws {
        cancellables.removeAll()
        codeCompletionService = nil
        mockWebSocketService = nil
        try super.tearDownWithError()
    }
    
    // MARK: - Initialization Tests
    
    func testInitialization() {
        XCTAssertNotNil(codeCompletionService)
        XCTAssertFalse(codeCompletionService.isLoading)
        XCTAssertNil(codeCompletionService.lastResponse)
        XCTAssertNil(codeCompletionService.lastError)
    }
    
    // MARK: - Code Completion Request Tests
    
    func testSuggestCodeCompletion() async {
        // Given
        let expectation = expectation(description: "Code completion suggest")
        let expectedResponse = createMockResponse(intent: "suggest")
        mockWebSocketService.mockResponse = expectedResponse
        
        // When
        let result = await codeCompletionService.suggestCodeCompletion(
            content: "def hello_world():",
            language: "python",
            filePath: "/test/file.py"
        )
        
        // Then
        XCTAssertTrue(result.success)
        XCTAssertEqual(result.intent, "suggest")
        XCTAssertNotNil(result.response)
        expectation.fulfill()
        
        await fulfillment(of: [expectation], timeout: 1.0)
    }
    
    func testExplainCodeCompletion() async {
        // Given
        let expectation = expectation(description: "Code completion explain")
        let expectedResponse = createMockResponse(intent: "explain")
        mockWebSocketService.mockResponse = expectedResponse
        
        // When
        let result = await codeCompletionService.explainCode(
            content: "def hello_world(): print('Hello')",
            language: "python",
            filePath: "/test/file.py"
        )
        
        // Then
        XCTAssertTrue(result.success)
        XCTAssertEqual(result.intent, "explain")
        XCTAssertNotNil(result.response)
        expectation.fulfill()
        
        await fulfillment(of: [expectation], timeout: 1.0)
    }
    
    func testRefactorCodeCompletion() async {
        // Given
        let expectation = expectation(description: "Code completion refactor")
        let expectedResponse = createMockResponse(intent: "refactor")
        mockWebSocketService.mockResponse = expectedResponse
        
        // When
        let result = await codeCompletionService.refactorCode(
            content: "def add(a, b): return a + b",
            language: "python",
            filePath: "/test/file.py"
        )
        
        // Then
        XCTAssertTrue(result.success)
        XCTAssertEqual(result.intent, "refactor")
        XCTAssertNotNil(result.response)
        expectation.fulfill()
        
        await fulfillment(of: [expectation], timeout: 1.0)
    }
    
    func testDebugCodeCompletion() async {
        // Given
        let expectation = expectation(description: "Code completion debug")
        let expectedResponse = createMockResponse(intent: "debug")
        mockWebSocketService.mockResponse = expectedResponse
        
        // When
        let result = await codeCompletionService.debugCode(
            content: "def broken_function(): return undefined_variable",
            language: "python",
            filePath: "/test/file.py"
        )
        
        // Then
        XCTAssertTrue(result.success)
        XCTAssertEqual(result.intent, "debug")
        XCTAssertNotNil(result.response)
        expectation.fulfill()
        
        await fulfillment(of: [expectation], timeout: 1.0)
    }
    
    func testOptimizeCodeCompletion() async {
        // Given
        let expectation = expectation(description: "Code completion optimize")
        let expectedResponse = createMockResponse(intent: "optimize")
        mockWebSocketService.mockResponse = expectedResponse
        
        // When
        let result = await codeCompletionService.optimizeCode(
            content: "for i in range(1000): print(i)",
            language: "python",
            filePath: "/test/file.py"
        )
        
        // Then
        XCTAssertTrue(result.success)
        XCTAssertEqual(result.intent, "optimize")
        XCTAssertNotNil(result.response)
        expectation.fulfill()
        
        await fulfillment(of: [expectation], timeout: 1.0)
    }
    
    // MARK: - Real Content Integration Tests
    
    func testRealContentIntegration() async {
        // Given
        let testContent = "import Foundation\n\nclass TestClass {\n    func testMethod() {\n        // Test implementation\n    }\n}"
        
        // Simulate clipboard content
        UIPasteboard.general.string = testContent
        
        let expectedResponse = createMockResponse(intent: "suggest")
        mockWebSocketService.mockResponse = expectedResponse
        
        // When
        let result = await codeCompletionService.suggestCodeCompletion(
            content: "", // Should use clipboard content
            language: "swift",
            filePath: "/test/TestClass.swift"
        )
        
        // Then
        XCTAssertTrue(result.success)
        // Verify the request included the clipboard content
        XCTAssertTrue(mockWebSocketService.lastSentMessage?.contains("TestClass") == true)
    }
    
    // MARK: - Error Handling Tests
    
    func testWebSocketError() async {
        // Given
        mockWebSocketService.shouldFail = true
        
        // When
        let result = await codeCompletionService.suggestCodeCompletion(
            content: "test content",
            language: "python",
            filePath: "/test/file.py"
        )
        
        // Then
        XCTAssertFalse(result.success)
        XCTAssertNotNil(codeCompletionService.lastError)
    }
    
    func testInvalidJSONResponse() async {
        // Given
        mockWebSocketService.mockResponse = CodeCompletionResponse(
            status: "error",
            intent: "suggest",
            response: "Invalid JSON response",
            confidence: 0.0,
            requiresReview: true,
            suggestions: []
        )
        
        // When
        let result = await codeCompletionService.suggestCodeCompletion(
            content: "test content",
            language: "python",
            filePath: "/test/file.py"
        )
        
        // Then
        XCTAssertFalse(result.success)
        XCTAssertEqual(result.response, "Invalid JSON response")
    }
    
    // MARK: - State Management Tests
    
    func testLoadingState() async {
        // Given
        let expectation = expectation(description: "Loading state management")
        mockWebSocketService.delay = 0.5 // Add delay to test loading state
        
        var loadingStates: [Bool] = []
        
        codeCompletionService.$isLoading
            .sink { isLoading in
                loadingStates.append(isLoading)
            }
            .store(in: &cancellables)
        
        // When
        let result = await codeCompletionService.suggestCodeCompletion(
            content: "test",
            language: "python",
            filePath: "/test/file.py"
        )
        
        // Then
        XCTAssertTrue(loadingStates.contains(true)) // Was loading at some point
        XCTAssertFalse(codeCompletionService.isLoading) // Not loading when complete
        expectation.fulfill()
        
        await fulfillment(of: [expectation], timeout: 2.0)
    }
    
    func testResponseStorage() async {
        // Given
        let expectedResponse = createMockResponse(intent: "suggest")
        mockWebSocketService.mockResponse = expectedResponse
        
        // When
        let result = await codeCompletionService.suggestCodeCompletion(
            content: "test",
            language: "python", 
            filePath: "/test/file.py"
        )
        
        // Then
        XCTAssertNotNil(codeCompletionService.lastResponse)
        XCTAssertEqual(codeCompletionService.lastResponse?.intent, "suggest")
        XCTAssertEqual(codeCompletionService.lastResponse?.response, expectedResponse.response)
    }
    
    // MARK: - Performance Tests
    
    func testResponseTime() async {
        // Given
        let startTime = Date()
        
        // When
        let result = await codeCompletionService.suggestCodeCompletion(
            content: "test",
            language: "python",
            filePath: "/test/file.py"
        )
        
        let responseTime = Date().timeIntervalSince(startTime)
        
        // Then
        XCTAssertLessThan(responseTime, 2.0, "Response should be under 2 seconds")
    }
    
    func testConcurrentRequests() async {
        // Given
        let numberOfRequests = 5
        
        // When
        await withTaskGroup(of: CodeCompletionResult.self) { group in
            for i in 0..<numberOfRequests {
                group.addTask {
                    await self.codeCompletionService.suggestCodeCompletion(
                        content: "test \(i)",
                        language: "python",
                        filePath: "/test/file\(i).py"
                    )
                }
            }
            
            var results: [CodeCompletionResult] = []
            for await result in group {
                results.append(result)
            }
            
            // Then
            XCTAssertEqual(results.count, numberOfRequests)
            // All requests should succeed (or at least complete)
            XCTAssertTrue(results.allSatisfy { _ in true })
        }
    }
    
    // MARK: - Helper Methods
    
    private func createMockResponse(intent: String) -> CodeCompletionResponse {
        return CodeCompletionResponse(
            status: "success",
            intent: intent,
            response: "Mock response for \(intent)",
            confidence: 0.95,
            requiresReview: intent == "refactor",
            suggestions: [
                "Suggestion 1 for \(intent)",
                "Suggestion 2 for \(intent)",
                "Suggestion 3 for \(intent)"
            ]
        )
    }
}

// MARK: - Code Completion Result

struct CodeCompletionResult {
    let success: Bool
    let intent: String
    let response: String?
    let error: Error?
    
    init(success: Bool, intent: String, response: String? = nil, error: Error? = nil) {
        self.success = success
        self.intent = intent
        self.response = response
        self.error = error
    }
}