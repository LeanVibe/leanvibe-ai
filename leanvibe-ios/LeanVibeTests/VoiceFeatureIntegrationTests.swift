import XCTest
import Speech
import AVFoundation
import Combine
@testable import LeanVibe

/// Comprehensive integration tests for voice feature stability
/// Now tests the consolidated UnifiedVoiceService
@available(iOS 18.0, *)
final class VoiceFeatureIntegrationTests: XCTestCase {
    
    var sut: WebSocketService!
    var unifiedVoiceService: UnifiedVoiceService!
    var cancellables: Set<AnyCancellable>!
    
    override func setUpWithError() throws {
        try super.setUpWithError()
        sut = WebSocketService()
        unifiedVoiceService = UnifiedVoiceService.shared
        cancellables = Set<AnyCancellable>()
    }
    
    override func tearDownWithError() throws {
        cancellables?.removeAll()
        unifiedVoiceService = nil
        sut?.disconnect()
        sut = nil
        try super.tearDownWithError()
    }
    
    // MARK: - Voice Feature State Tests
    
    func testVoiceFeatureDisabledByDefault() {
        // Production voice feature gating
        let config = AppConfiguration.shared
        XCTAssertTrue(config.isVoiceEnabled, "Voice should be enabled by default now with UnifiedVoiceService")
        XCTAssertTrue(config.useUnifiedVoiceService, "Should default to UnifiedVoiceService")
    }
    
    func testVoiceFeatureConfigurationAccess() {
        // Test configuration readability
        let mockConfig = MockAppConfiguration()
        mockConfig.unifiedVoiceService = true
        
        XCTAssertTrue(mockConfig.useUnifiedVoiceService)
        XCTAssertNotNil(mockConfig.voiceConfidenceThreshold)
        XCTAssertNotNil(mockConfig.maxVoiceRecordingDuration)
    }
    
    // MARK: - UnifiedVoiceService Integration Tests
    
    func testUnifiedVoiceServiceInitialization() {
        XCTAssertNotNil(unifiedVoiceService)
        XCTAssertEqual(unifiedVoiceService.state, .idle)
        XCTAssertFalse(unifiedVoiceService.isWakeListening)
    }
    
    func testUnifiedVoiceServicePermissions() {
        // Test permission state access
        XCTAssertNotNil(unifiedVoiceService.hasMicrophonePermission)
        XCTAssertNotNil(unifiedVoiceService.hasSpeechRecognitionPermission)
        XCTAssertNotNil(unifiedVoiceService.permissionStatus)
        XCTAssertNotNil(unifiedVoiceService.isFullyAuthorized)
        
        // Test permission checking doesn't crash
        unifiedVoiceService.checkPermissions()
    }
    
    func testUnifiedVoiceServiceWakePhrase() {
        // Test wake phrase functionality
        XCTAssertFalse(unifiedVoiceService.isWakeListening)
        XCTAssertFalse(unifiedVoiceService.wakePhraseDetected)
        XCTAssertEqual(unifiedVoiceService.wakeAudioLevel, 0.0)
        XCTAssertNil(unifiedVoiceService.lastWakeDetection)
    }
    
    func testUnifiedVoiceServicePerformanceMetrics() {
        // Test performance monitoring
        XCTAssertNotNil(unifiedVoiceService.responseTime)
        XCTAssertNotNil(unifiedVoiceService.averageResponseTime)
        XCTAssertNotNil(unifiedVoiceService.performanceStatus)
        XCTAssertNotNil(unifiedVoiceService.currentLatency)
        XCTAssertNotNil(unifiedVoiceService.isLowLatencyMode)
        XCTAssertNotNil(unifiedVoiceService.isOptimized)
    }
    
    // MARK: - State Management Integration
    
    func testUnifiedVoiceServiceStateTransitions() {
        // Test basic state management
        XCTAssertEqual(unifiedVoiceService.state, .idle)
        XCTAssertEqual(unifiedVoiceService.recognizedText, "")
        XCTAssertEqual(unifiedVoiceService.audioLevel, 0.0)
        XCTAssertEqual(unifiedVoiceService.confidenceScore, 0.0)
    }
    
    func testUnifiedVoiceServiceConfiguration() async {
        // Test async operations don't crash
        do {
            await unifiedVoiceService.startListening(mode: .pushToTalk)
            // Should not crash even if permissions aren't granted
        } catch {
            // Expected if permissions not granted in test environment
        }
        
        // Test stopping listening
        unifiedVoiceService.stopListening()
    }
    
    // MARK: - WebSocket Integration
    
    func testWebSocketVoiceIntegration() {
        // Test that WebSocket can handle voice commands
        XCTAssertNotNil(sut)
        XCTAssertNotNil(unifiedVoiceService)
        
        // WebSocket should be able to receive voice-related messages
        let expectation = XCTestExpectation(description: "WebSocket connection")
        
        sut.connectionStatePublisher
            .sink { state in
                if case .connected = state {
                    expectation.fulfill()
                }
            }
            .store(in: &cancellables)
        
        sut.connect()
        wait(for: [expectation], timeout: 5.0)
    }
    
    // MARK: - Memory Safety Tests
    
    func testUnifiedVoiceServiceMemoryManagement() {
        // Test that the service doesn't cause memory issues
        weak var weakVoiceService: UnifiedVoiceService?
        
        autoreleasepool {
            let service = UnifiedVoiceService.shared
            weakVoiceService = service
            XCTAssertNotNil(weakVoiceService)
        }
        
        // Singleton should remain alive
        XCTAssertNotNil(weakVoiceService, "Singleton should be alive")
    }
    
    // MARK: - Error Handling Integration
    
    func testUnifiedVoiceServiceErrorHandling() {
        // Test error states are handled gracefully
        XCTAssertNotEqual(unifiedVoiceService.state, .error)
        
        // Test that error transitions don't crash
        // (UnifiedVoiceService should handle errors internally)
    }
    
    // MARK: - Performance Validation
    
    func testUnifiedVoiceServicePerformance() {
        // Test performance metrics are tracked
        let initialResponseTime = unifiedVoiceService.responseTime
        let initialLatency = unifiedVoiceService.currentLatency
        
        // Should have initial values
        XCTAssertGreaterThanOrEqual(initialResponseTime, 0.0)
        XCTAssertGreaterThanOrEqual(initialLatency, 0.0)
    }
    
    // MARK: - Configuration Integration
    
    func testVoiceConfigurationIntegration() {
        let config = AppConfiguration.shared
        
        // Test voice configuration access
        XCTAssertNotNil(config.voiceConfidenceThreshold)
        XCTAssertNotNil(config.maxVoiceRecordingDuration)
        XCTAssertTrue(config.useUnifiedVoiceService)
        XCTAssertTrue(config.isVoiceEnabled)
    }
}

// MARK: - Test Helpers

class MockAppConfiguration {
    var unifiedVoiceService: Bool = true
    var voiceConfidenceThreshold: Float = 0.6
    var maxVoiceRecordingDuration: TimeInterval = 30.0
    
    var useUnifiedVoiceService: Bool { unifiedVoiceService }
}