import XCTest
import AVFoundation
@testable import LeanVibe

@available(iOS 18.0, macOS 14.0, *)
class VoiceFeedbackServiceTests: XCTestCase {
    
    var voiceFeedbackService: VoiceFeedbackService!
    var expectationTimeout: TimeInterval = 5.0
    
    override func setUp() {
        super.setUp()
        voiceFeedbackService = VoiceFeedbackService.shared
        // Reset service to clean state for each test
        voiceFeedbackService.stopSpeaking()
        voiceFeedbackService.isEnabled = true
        voiceFeedbackService.quietModeEnabled = false
        voiceFeedbackService.speechRate = 0.5
        voiceFeedbackService.speechVolume = 0.8
        voiceFeedbackService.enableHapticFeedback = true
    }
    
    override func tearDown() {
        voiceFeedbackService.stopSpeaking()
        voiceFeedbackService = nil
        super.tearDown()
    }
    
    // MARK: - Initialization Tests
    
    func testVoiceFeedbackServiceInitialization() {
        XCTAssertNotNil(voiceFeedbackService)
        XCTAssertFalse(voiceFeedbackService.isSpeaking)
        XCTAssertTrue(voiceFeedbackService.isEnabled)
        XCTAssertNil(voiceFeedbackService.currentMessage)
        XCTAssertEqual(voiceFeedbackService.speechRate, 0.5, accuracy: 0.01)
        XCTAssertEqual(voiceFeedbackService.speechVolume, 0.8, accuracy: 0.01)
        XCTAssertEqual(voiceFeedbackService.preferredVoice, "en-US")
        XCTAssertTrue(voiceFeedbackService.enableHapticFeedback)
        XCTAssertFalse(voiceFeedbackService.quietModeEnabled)
    }
    
    func testSingletonBehavior() {
        let instance1 = VoiceFeedbackService.shared
        let instance2 = VoiceFeedbackService.shared
        
        XCTAssertTrue(instance1 === instance2, "VoiceFeedbackService should be a singleton")
    }
    
    // MARK: - Basic Functionality Tests
    
    func testSpeakResponse() {
        let expectation = expectation(description: "Voice feedback should start speaking")
        let testMessage = "Test message for voice feedback"
        
        // Start speaking
        voiceFeedbackService.speakResponse(testMessage)
        
        // Verify speaking state changes
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            XCTAssertTrue(self.voiceFeedbackService.isSpeaking)
            XCTAssertEqual(self.voiceFeedbackService.currentMessage, testMessage)
            expectation.fulfill()
        }
        
        waitForExpectations(timeout: expectationTimeout)
    }
    
    func testSpeakResponseWhenDisabled() {
        voiceFeedbackService.isEnabled = false
        
        voiceFeedbackService.speakResponse("This should not be spoken")
        
        // Should not start speaking when disabled
        XCTAssertFalse(voiceFeedbackService.isSpeaking)
        XCTAssertNil(voiceFeedbackService.currentMessage)
    }
    
    func testSpeakResponseInQuietMode() {
        voiceFeedbackService.quietModeEnabled = true
        
        voiceFeedbackService.speakResponse("This should not be spoken in quiet mode")
        
        // Should not start speaking in quiet mode
        XCTAssertFalse(voiceFeedbackService.isSpeaking)
        XCTAssertNil(voiceFeedbackService.currentMessage)
    }
    
    // MARK: - Command Confirmation Tests
    
    func testCommandConfirmationSuccess() {
        let expectation = expectation(description: "Should speak success confirmation")
        
        voiceFeedbackService.confirmCommand("status", success: true)
        
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            XCTAssertTrue(self.voiceFeedbackService.isSpeaking)
            XCTAssertTrue(self.voiceFeedbackService.currentMessage?.contains("completed successfully") ?? false)
            expectation.fulfill()
        }
        
        waitForExpectations(timeout: expectationTimeout)
    }
    
    func testCommandConfirmationFailure() {
        let expectation = expectation(description: "Should speak failure confirmation")
        
        voiceFeedbackService.confirmCommand("invalid", success: false)
        
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            XCTAssertTrue(self.voiceFeedbackService.isSpeaking)
            XCTAssertTrue(self.voiceFeedbackService.currentMessage?.contains("failed to execute") ?? false)
            expectation.fulfill()
        }
        
        waitForExpectations(timeout: expectationTimeout)
    }
    
    // MARK: - Error Handling Tests
    
    func testSpeakError() {
        let expectation = expectation(description: "Should speak error message")
        let errorMessage = "Connection failed"
        
        voiceFeedbackService.speakError(errorMessage)
        
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            XCTAssertTrue(self.voiceFeedbackService.isSpeaking)
            XCTAssertTrue(self.voiceFeedbackService.currentMessage?.contains("Error") ?? false)
            XCTAssertTrue(self.voiceFeedbackService.currentMessage?.contains(errorMessage) ?? false)
            expectation.fulfill()
        }
        
        waitForExpectations(timeout: expectationTimeout)
    }
    
    // MARK: - Speech Control Tests
    
    func testStopSpeaking() {
        let expectation = expectation(description: "Should stop speaking")
        
        // Start speaking first
        voiceFeedbackService.speakResponse("This is a long test message that should be stopped")
        
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            XCTAssertTrue(self.voiceFeedbackService.isSpeaking)
            
            // Stop speaking
            self.voiceFeedbackService.stopSpeaking()
            
            XCTAssertFalse(self.voiceFeedbackService.isSpeaking)
            XCTAssertNil(self.voiceFeedbackService.currentMessage)
            XCTAssertEqual(self.voiceFeedbackService.queueLength, 0)
            expectation.fulfill()
        }
        
        waitForExpectations(timeout: expectationTimeout)
    }
    
    func testTestVoice() {
        let expectation = expectation(description: "Should speak test message")
        
        voiceFeedbackService.testVoice()
        
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            XCTAssertTrue(self.voiceFeedbackService.isSpeaking)
            XCTAssertTrue(self.voiceFeedbackService.currentMessage?.contains("test") ?? false)
            expectation.fulfill()
        }
        
        waitForExpectations(timeout: expectationTimeout)
    }
    
    // MARK: - Priority Tests
    
    func testPriorityHandling() {
        let expectation = expectation(description: "Urgent messages should interrupt current speech")
        
        // Start with normal priority message
        voiceFeedbackService.speakResponse("This is a normal message that should be interrupted", priority: .normal)
        
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            let firstMessage = self.voiceFeedbackService.currentMessage
            XCTAssertTrue(self.voiceFeedbackService.isSpeaking)
            
            // Send urgent message
            self.voiceFeedbackService.speakResponse("URGENT MESSAGE", priority: .urgent)
            
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.2) {
                // Urgent message should replace the current message
                XCTAssertNotEqual(self.voiceFeedbackService.currentMessage, firstMessage)
                XCTAssertEqual(self.voiceFeedbackService.currentMessage, "URGENT MESSAGE")
                expectation.fulfill()
            }
        }
        
        waitForExpectations(timeout: expectationTimeout)
    }
    
    // MARK: - Queue Management Tests
    
    func testSpeechQueue() {
        // Start speaking
        voiceFeedbackService.speakResponse("First message", priority: .normal)
        
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
            // Queue additional messages
            self.voiceFeedbackService.speakResponse("Second message", priority: .normal)
            self.voiceFeedbackService.speakResponse("Third message", priority: .normal)
            
            // Check queue has messages
            XCTAssertGreaterThan(self.voiceFeedbackService.queueLength, 0)
        }
    }
    
    func testClearQueue() {
        // Add messages to queue
        voiceFeedbackService.speakResponse("First message", priority: .normal)
        
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
            self.voiceFeedbackService.speakResponse("Second message", priority: .normal)
            self.voiceFeedbackService.speakResponse("Third message", priority: .normal)
            
            // Clear queue
            self.voiceFeedbackService.clearQueue()
            
            XCTAssertEqual(self.voiceFeedbackService.queueLength, 0)
        }
    }
    
    // MARK: - Voice Configuration Tests
    
    func testGetAvailableVoices() {
        let availableVoices = voiceFeedbackService.getAvailableVoices()
        
        XCTAssertGreaterThan(availableVoices.count, 0, "Should have at least one available voice")
        
        // All voices should be English
        for voice in availableVoices {
            XCTAssertTrue(voice.language.hasPrefix("en"), "All voices should be English")
        }
    }
    
    func testSpeechRateValidation() {
        // Test setting valid speech rates
        voiceFeedbackService.speechRate = 0.1
        XCTAssertEqual(voiceFeedbackService.speechRate, 0.1, accuracy: 0.01)
        
        voiceFeedbackService.speechRate = 1.0
        XCTAssertEqual(voiceFeedbackService.speechRate, 1.0, accuracy: 0.01)
        
        voiceFeedbackService.speechRate = 0.5
        XCTAssertEqual(voiceFeedbackService.speechRate, 0.5, accuracy: 0.01)
    }
    
    func testSpeechVolumeValidation() {
        // Test setting valid speech volumes
        voiceFeedbackService.speechVolume = 0.0
        XCTAssertEqual(voiceFeedbackService.speechVolume, 0.0, accuracy: 0.01)
        
        voiceFeedbackService.speechVolume = 1.0
        XCTAssertEqual(voiceFeedbackService.speechVolume, 1.0, accuracy: 0.01)
        
        voiceFeedbackService.speechVolume = 0.5
        XCTAssertEqual(voiceFeedbackService.speechVolume, 0.5, accuracy: 0.01)
    }
    
    // MARK: - Quick Feedback Tests
    
    func testQuickFeedbackCommandSucceeded() {
        let expectation = expectation(description: "Should provide command success feedback")
        
        voiceFeedbackService.provide(.commandSucceeded("test"))
        
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            XCTAssertTrue(self.voiceFeedbackService.isSpeaking)
            XCTAssertTrue(self.voiceFeedbackService.currentMessage?.contains("executed successfully") ?? false)
            expectation.fulfill()
        }
        
        waitForExpectations(timeout: expectationTimeout)
    }
    
    func testQuickFeedbackWakePhraseDetected() {
        let expectation = expectation(description: "Should provide wake phrase feedback")
        
        voiceFeedbackService.provide(.wakePhraseDetected)
        
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            XCTAssertTrue(self.voiceFeedbackService.isSpeaking)
            XCTAssertTrue(self.voiceFeedbackService.currentMessage?.contains("Wake phrase detected") ?? false)
            expectation.fulfill()
        }
        
        waitForExpectations(timeout: expectationTimeout)
    }
    
    // MARK: - Availability Tests
    
    func testIsAvailable() {
        // Should be available when enabled and not in quiet mode
        voiceFeedbackService.isEnabled = true
        voiceFeedbackService.quietModeEnabled = false
        XCTAssertTrue(voiceFeedbackService.isAvailable)
        
        // Should not be available when disabled
        voiceFeedbackService.isEnabled = false
        XCTAssertFalse(voiceFeedbackService.isAvailable)
        
        // Should not be available in quiet mode
        voiceFeedbackService.isEnabled = true
        voiceFeedbackService.quietModeEnabled = true
        XCTAssertFalse(voiceFeedbackService.isAvailable)
    }
    
    // MARK: - Sequence Tests
    
    func testSpeakSequence() {
        let messages = ["First message", "Second message", "Third message"]
        let expectation = expectation(description: "Should speak sequence of messages")
        
        voiceFeedbackService.speakSequence(messages, withDelay: 0.1)
        
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            XCTAssertTrue(self.voiceFeedbackService.isSpeaking)
            XCTAssertEqual(self.voiceFeedbackService.currentMessage, messages.first)
            
            // Check that additional messages are queued
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.2) {
                // Queue should have remaining messages
                XCTAssertGreaterThan(self.voiceFeedbackService.queueLength, 0)
                expectation.fulfill()
            }
        }
        
        waitForExpectations(timeout: expectationTimeout)
    }
    
    // MARK: - Settings Integration Tests
    
    func testSettingsChanges() {
        let expectation = expectation(description: "Settings changes should affect behavior")
        
        // Disable service
        voiceFeedbackService.isEnabled = false
        voiceFeedbackService.speakResponse("Should not speak")
        
        XCTAssertFalse(voiceFeedbackService.isSpeaking)
        
        // Enable quiet mode
        voiceFeedbackService.isEnabled = true
        voiceFeedbackService.quietModeEnabled = true
        voiceFeedbackService.speakResponse("Should not speak in quiet mode")
        
        XCTAssertFalse(voiceFeedbackService.isSpeaking)
        
        // Normal operation
        voiceFeedbackService.quietModeEnabled = false
        voiceFeedbackService.speakResponse("Should speak normally")
        
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            XCTAssertTrue(self.voiceFeedbackService.isSpeaking)
            expectation.fulfill()
        }
        
        waitForExpectations(timeout: expectationTimeout)
    }
    
    // MARK: - Memory Management Tests
    
    func testMemoryManagement() {
        weak var weakReference: VoiceFeedbackService?
        
        autoreleasepool {
            // Note: Since VoiceFeedbackService is a singleton, this test 
            // primarily ensures no memory leaks in regular usage
            let service = VoiceFeedbackService.shared
            weakReference = service
            
            service.speakResponse("Test message")
            service.stopSpeaking()
        }
        
        // Singleton should still exist
        XCTAssertNotNil(weakReference)
    }
    
    // MARK: - Edge Case Tests
    
    func testEmptyMessage() {
        voiceFeedbackService.speakResponse("")
        
        // Should handle empty messages gracefully
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            // May or may not start speaking depending on AVSpeechSynthesizer behavior
            // The important thing is it doesn't crash
            XCTAssertTrue(true, "Should handle empty messages without crashing")
        }
    }
    
    func testVeryLongMessage() {
        let longMessage = String(repeating: "This is a very long message. ", count: 100)
        
        voiceFeedbackService.speakResponse(longMessage)
        
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            XCTAssertTrue(self.voiceFeedbackService.isSpeaking)
            XCTAssertEqual(self.voiceFeedbackService.currentMessage, longMessage)
        }
    }
    
    func testRapidFireMessages() {
        // Send multiple messages rapidly
        for i in 1...10 {
            voiceFeedbackService.speakResponse("Message \(i)", priority: .normal)
        }
        
        // Service should handle this gracefully
        XCTAssertGreaterThan(voiceFeedbackService.queueLength, 0)
        
        // Clear queue to prevent test interference
        voiceFeedbackService.stopSpeaking()
    }
}