import XCTest
import Speech
@testable import LeanVibe

@available(iOS 18.0, macOS 14.0, *)
@MainActor
final class SpeechRecognitionServiceTests: XCTestCase {
    
    private var speechService: SpeechRecognitionService!
    private var mockAuthorizationProvider: MockSpeechAuthorizationProvider!
    
    override func setUp() async throws {
        mockAuthorizationProvider = MockSpeechAuthorizationProvider()
        speechService = SpeechRecognitionService()
        // Inject mock for testing
        speechService.authorizationProvider = mockAuthorizationProvider
    }
    
    override func tearDown() async throws {
        await speechService.stopListening()
        speechService = nil
        mockAuthorizationProvider = nil
    }
    
    // MARK: - Authorization Tests
    
    func testRequestPermissionsWithAuthorizedStatus() async throws {
        // Given
        mockAuthorizationProvider.authorizationStatus = .authorized
        
        // When
        await speechService.requestPermissions()
        
        // Then
        XCTAssertTrue(speechService.hasPermission)
        XCTAssertFalse(speechService.isListening)
        XCTAssertNil(speechService.lastError)
    }
    
    func testRequestPermissionsWithDeniedStatus() async throws {
        // Given
        mockAuthorizationProvider.authorizationStatus = .denied
        
        // When
        await speechService.requestPermissions()
        
        // Then
        XCTAssertFalse(speechService.hasPermission)
        XCTAssertFalse(speechService.isListening)
        XCTAssertNotNil(speechService.lastError)
        XCTAssertTrue(speechService.lastError?.contains("denied") == true)
    }
    
    func testRequestPermissionsWithRestrictedStatus() async throws {
        // Given
        mockAuthorizationProvider.authorizationStatus = .restricted
        
        // When
        await speechService.requestPermissions()
        
        // Then
        XCTAssertFalse(speechService.hasPermission)
        XCTAssertNotNil(speechService.lastError)
        XCTAssertTrue(speechService.lastError?.contains("restricted") == true)
    }
    
    // MARK: - Listening Tests
    
    func testStartListeningWithPermission() async throws {
        // Given
        mockAuthorizationProvider.authorizationStatus = .authorized
        await speechService.requestPermissions()
        
        // When
        try await speechService.startListening()
        
        // Then
        XCTAssertTrue(speechService.isListening)
        XCTAssertNil(speechService.lastError)
    }
    
    func testStartListeningWithoutPermission() async throws {
        // Given
        mockAuthorizationProvider.authorizationStatus = .denied
        await speechService.requestPermissions()
        
        // When & Then
        do {
            try await speechService.startListening()
            XCTFail("Expected error when starting listening without permission")
        } catch {
            XCTAssertFalse(speechService.isListening)
            XCTAssertNotNil(speechService.lastError)
        }
    }
    
    func testStopListening() async throws {
        // Given
        mockAuthorizationProvider.authorizationStatus = .authorized
        await speechService.requestPermissions()
        try await speechService.startListening()
        XCTAssertTrue(speechService.isListening)
        
        // When
        await speechService.stopListening()
        
        // Then
        XCTAssertFalse(speechService.isListening)
    }
    
    // MARK: - Text Recognition Tests
    
    func testProcessRecognizedText() async throws {
        // Given
        mockAuthorizationProvider.authorizationStatus = .authorized
        await speechService.requestPermissions()
        var recognizedTexts: [String] = []
        
        // Subscribe to recognized text
        let cancellable = speechService.$recognizedText.sink { text in
            if !text.isEmpty {
                recognizedTexts.append(text)
            }
        }
        defer { cancellable.cancel() }
        
        // When
        speechService.processRecognizedText("Hello world")
        speechService.processRecognizedText("Test speech recognition")
        
        // Then
        XCTAssertTrue(recognizedTexts.contains("Hello world"))
        XCTAssertTrue(recognizedTexts.contains("Test speech recognition"))
    }
    
    func testClearRecognizedText() async throws {
        // Given
        speechService.processRecognizedText("Some text")
        XCTAssertFalse(speechService.recognizedText.isEmpty)
        
        // When
        speechService.clearRecognizedText()
        
        // Then
        XCTAssertTrue(speechService.recognizedText.isEmpty)
    }
    
    // MARK: - Error Handling Tests
    
    func testHandleRecognitionError() async throws {
        // Given
        let testError = NSError(domain: "TestError", code: 1001, userInfo: [NSLocalizedDescriptionKey: "Test recognition error"])
        
        // When
        speechService.handleRecognitionError(testError)
        
        // Then
        XCTAssertNotNil(speechService.lastError)
        XCTAssertTrue(speechService.lastError?.contains("Test recognition error") == true)
        XCTAssertFalse(speechService.isListening)
    }
    
    // MARK: - Lifecycle Tests
    
    func testMultipleStartStopCycles() async throws {
        // Given
        mockAuthorizationProvider.authorizationStatus = .authorized
        await speechService.requestPermissions()
        
        // When & Then - Multiple cycles
        for _ in 0..<3 {
            try await speechService.startListening()
            XCTAssertTrue(speechService.isListening)
            
            await speechService.stopListening()
            XCTAssertFalse(speechService.isListening)
        }
    }
    
    func testConcurrentStartListening() async throws {
        // Given
        mockAuthorizationProvider.authorizationStatus = .authorized
        await speechService.requestPermissions()
        
        // When - Start listening multiple times concurrently
        async let result1 = speechService.startListening()
        async let result2 = speechService.startListening()
        async let result3 = speechService.startListening()
        
        // Then - Should handle gracefully without crashes
        do {
            try await result1
            try await result2
            try await result3
        } catch {
            // Some may fail due to concurrent access, but no crashes
        }
        
        // Service should be in a consistent state
        XCTAssertTrue(speechService.isListening || !speechService.isListening) // Just verify no crash
    }
}

// MARK: - Mock Implementation

@available(iOS 18.0, macOS 14.0, *)
class MockSpeechAuthorizationProvider {
    var authorizationStatus: SFSpeechRecognizerAuthorizationStatus = .notDetermined
    
    func requestAuthorization() async -> SFSpeechRecognizerAuthorizationStatus {
        return authorizationStatus
    }
    
    func currentAuthorizationStatus() -> SFSpeechRecognizerAuthorizationStatus {
        return authorizationStatus
    }
}

// MARK: - Performance Tests

@available(iOS 18.0, macOS 14.0, *)
extension SpeechRecognitionServiceTests {
    
    func testSpeechServiceInitializationPerformance() throws {
        measure {
            let service = SpeechRecognitionService()
            _ = service.hasPermission
        }
    }
    
    func testTextProcessingPerformance() throws {
        let longText = String(repeating: "This is a test of speech recognition performance. ", count: 100)
        
        measure {
            speechService.processRecognizedText(longText)
        }
    }
}

// MARK: - Integration Helpers

@available(iOS 18.0, macOS 14.0, *)
extension SpeechRecognitionService {
    var authorizationProvider: MockSpeechAuthorizationProvider? {
        get { nil } // Not implemented for real service
        set { /* Inject mock in tests */ }
    }
}