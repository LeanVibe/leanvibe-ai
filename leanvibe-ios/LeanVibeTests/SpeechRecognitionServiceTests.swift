import XCTest
import Speech
@testable import LeanVibe

@available(iOS 18.0, macOS 14.0, *)
@MainActor
final class SpeechRecognitionServiceTests: XCTestCase {
    
    private var speechService: SpeechRecognitionService!
    
    override func setUp() async throws {
        speechService = SpeechRecognitionService()
    }
    
    override func tearDown() async throws {
        speechService.stopListening()
        speechService = nil
    }
    
    // MARK: - Basic Functionality Tests
    
    func testSpeechServiceInitialization() throws {
        // Given & When
        let service = SpeechRecognitionService()
        
        // Then
        XCTAssertFalse(service.isListening)
        XCTAssertEqual(service.recognizedText, "")
        XCTAssertEqual(service.confidenceScore, 0.0)
        XCTAssertEqual(service.recognitionState, .idle)
        XCTAssertEqual(service.audioLevel, 0.0)
        XCTAssertNil(service.lastError)
    }
    
    func testRequestPermissions() async throws {
        // Given
        let expectation = expectation(description: "Permission request completion")
        var receivedMicPermission = false
        var receivedSpeechStatus: SFSpeechRecognizerAuthorizationStatus = .notDetermined
        
        // When
        speechService.requestPermissions { micPermission, speechStatus in
            receivedMicPermission = micPermission
            receivedSpeechStatus = speechStatus
            expectation.fulfill()
        }
        
        await fulfillment(of: [expectation], timeout: 3.0)
        
        // Then - basic smoke test that completion was called
        XCTAssertFalse(speechService.isListening)
    }
    
    func testStartListeningWithoutPermissions() throws {
        // Given - no permissions setup
        
        // When
        speechService.startListening()
        
        // Then - should handle gracefully
        // Note: Without permissions, this might set an error state
        XCTAssertTrue(speechService.recognitionState == .idle || 
                     speechService.recognitionState == .error("Microphone permission denied") ||
                     speechService.recognitionState == .error("Speech recognition permission denied"))
    }
    
    func testStopListening() throws {
        // Given
        speechService.startListening()
        
        // When
        speechService.stopListening()
        
        // Then
        XCTAssertFalse(speechService.isListening)
        XCTAssertEqual(speechService.recognitionState, .idle)
    }
    
    func testResetRecognition() throws {
        // Given
        speechService.startListening()
        
        // When
        speechService.resetRecognition()
        
        // Then
        XCTAssertFalse(speechService.isListening)
        XCTAssertEqual(speechService.recognizedText, "")
        XCTAssertEqual(speechService.confidenceScore, 0.0)
        XCTAssertEqual(speechService.audioLevel, 0.0)
        XCTAssertEqual(speechService.recognitionState, .idle)
    }
    
    // MARK: - Published Properties Tests
    
    func testPublishedPropertiesAreObservable() async throws {
        // Given
        let expectation = expectation(description: "Published property changed")
        let cancellable = speechService.$recognitionState
            .sink { state in
                if state != .idle {
                    expectation.fulfill()
                }
            }
        
        // When
        speechService.startListening()
        
        // Then
        await fulfillment(of: [expectation], timeout: 2.0)
        cancellable.cancel()
    }
    
    func testRecognitionStateTransitions() throws {
        // Given
        XCTAssertEqual(speechService.recognitionState, .idle)
        
        // When
        speechService.startListening()
        
        // Then - state should transition (might be error due to permissions)
        XCTAssertNotEqual(speechService.recognitionState, .idle)
    }
    
    // MARK: - Edge Cases
    
    func testMultipleStartListeningCalls() throws {
        // Given
        speechService.startListening()
        let firstState = speechService.recognitionState
        
        // When
        speechService.startListening() // Second call
        
        // Then - should handle gracefully
        let secondState = speechService.recognitionState
        XCTAssertTrue(firstState == secondState || secondState == .error("Already listening"))
    }
    
    func testStopListeningWhenNotListening() throws {
        // Given - not listening
        XCTAssertFalse(speechService.isListening)
        
        // When
        speechService.stopListening()
        
        // Then - should handle gracefully
        XCTAssertFalse(speechService.isListening)
        XCTAssertEqual(speechService.recognitionState, .idle)
    }
}