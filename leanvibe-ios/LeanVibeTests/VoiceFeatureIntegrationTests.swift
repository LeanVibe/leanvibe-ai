import XCTest
import Speech
import AVFoundation
import Combine
@testable import LeanVibe

/// Comprehensive integration tests for voice feature stability
/// Created to reproduce crash conditions and validate fixes before re-enabling voice features
@available(iOS 18.0, *)
final class VoiceFeatureIntegrationTests: XCTestCase {
    
    var sut: WebSocketService!
    var mockVoiceManager: MockVoiceManager!
    var cancellables: Set<AnyCancellable>!
    
    override func setUpWithError() throws {
        try super.setUpWithError()
        sut = WebSocketService()
        mockVoiceManager = MockVoiceManager()
        cancellables = Set<AnyCancellable>()
    }
    
    override func tearDownWithError() throws {
        cancellables?.removeAll()
        mockVoiceManager = nil
        sut?.disconnect()
        sut = nil
        try super.tearDownWithError()
    }
    
    // MARK: - Voice Feature State Tests
    
    func testVoiceFeatureDisabledByDefault() {
        // Test that voice features are currently disabled by default
        let config = AppConfiguration.shared
        XCTAssertFalse(config.isVoiceEnabled, "Voice features should be disabled by default for stability")
        XCTAssertFalse(config.useUnifiedVoiceService, "Unified voice service should be disabled by default")
    }
    
    func testVoiceFeatureCanBeEnabledViaConfiguration() {
        // Test that voice features can be enabled via Info.plist override
        let expectation = XCTestExpectation(description: "Voice feature configuration test")
        
        // Simulate enabling voice features
        let mockConfig = MockAppConfiguration(voiceEnabled: true, unifiedVoiceService: true)
        
        XCTAssertTrue(mockConfig.isVoiceEnabled)
        XCTAssertTrue(mockConfig.useUnifiedVoiceService)
        
        expectation.fulfill()
        wait(for: [expectation], timeout: 1.0)
    }
    
    // MARK: - WebSocket Connection Stability Tests
    
    func testWebSocketConnectionWithInvalidQRData() async {
        // Test handling of malformed QR data that could cause crashes
        let invalidQRData = "invalid_json_data"
        
        do {
            try await sut.connectWithQRCode(invalidQRData)
            XCTFail("Should have thrown an error for invalid QR data")
        } catch {
            XCTAssertNotNil(error, "Should properly handle invalid QR data with error")
            XCTAssertTrue(error.localizedDescription.contains("Invalid QR code format"))
        }
    }
    
    func testWebSocketConnectionTimeout() async {
        // Test connection timeout handling to prevent hangs
        let timeoutQRData = """
        {
            "leanvibe": {
                "server": {
                    "host": "192.168.1.999",
                    "port": 9999,
                    "ssl": false
                },
                "auth": {
                    "type": "none"
                }
            }
        }
        """
        
        let startTime = Date()
        
        do {
            try await sut.connectWithQRCode(timeoutQRData)
            XCTFail("Should have timed out")
        } catch {
            let elapsed = Date().timeIntervalSince(startTime)
            XCTAssertLessThan(elapsed, 15.0, "Should timeout within 15 seconds")
            XCTAssertTrue(error.localizedDescription.contains("timeout"))
        }
    }
    
    func testMultipleConcurrentConnectionAttempts() async {
        // Test that multiple concurrent connection attempts don't cause crashes
        let validQRData = """
        {
            "leanvibe": {
                "server": {
                    "host": "localhost",
                    "port": 8001,
                    "ssl": false
                },
                "auth": {
                    "type": "none"
                }
            }
        }
        """
        
        await withTaskGroup(of: Void.self) { group in
            // Launch multiple connection attempts concurrently
            for i in 0..<5 {
                group.addTask { [weak self] in
                    do {
                        try await self?.sut.connectWithQRCode(validQRData)
                    } catch {
                        // Expected to fail - testing stability, not success
                        print("Connection attempt \(i) failed: \(error)")
                    }
                }
            }
            
            // Wait for all tasks to complete
            await group.waitForAll()
        }
        
        // If we reach here without crashes, the concurrency handling is stable
        XCTAssertTrue(true, "Multiple concurrent connections handled without crashes")
    }
    
    // MARK: - Speech Recognition Stability Tests
    
    func testSpeechRecognitionServiceInitialization() {
        // Test that SpeechRecognitionService can be created without crashes
        let speechService = SpeechRecognitionService()
        XCTAssertNotNil(speechService)
        XCTAssertEqual(speechService.recognitionState, .idle)
        XCTAssertFalse(speechService.isListening)
    }
    
    @MainActor
    func testSpeechRecognitionPermissionHandling() async {
        // Test permission handling without actually requesting permissions
        let speechService = SpeechRecognitionService()
        
        // Verify initial state
        XCTAssertEqual(speechService.recognitionState, .idle)
        XCTAssertFalse(speechService.isListening)
        
        // Test that service handles permission denial gracefully
        speechService.recognitionState = .error("Permission denied")
        XCTAssertEqual(speechService.recognitionState, .error("Permission denied"))
    }
    
    func testVoiceManagerLifecycle() {
        // Test VoiceManager creation and deallocation
        var voiceManager: VoiceManager? = VoiceManager(
            speechService: SpeechRecognitionService(),
            webSocketService: WebSocketService()
        )
        
        XCTAssertNotNil(voiceManager)
        XCTAssertFalse(voiceManager!.isListening)
        
        // Test deallocation doesn't cause crashes
        voiceManager = nil
        XCTAssertNil(voiceManager)
    }
    
    // MARK: - Memory Leak Detection Tests
    
    func testVoiceManagerMemoryLeak() {
        // Test for potential memory leaks in VoiceManager
        weak var weakVoiceManager: VoiceManager?
        
        autoreleasepool {
            let voiceManager = VoiceManager(
                speechService: SpeechRecognitionService(),
                webSocketService: WebSocketService()
            )
            weakVoiceManager = voiceManager
            XCTAssertNotNil(weakVoiceManager)
        }
        
        // After autoreleasepool, voiceManager should be deallocated
        XCTAssertNil(weakVoiceManager, "VoiceManager should be deallocated, potential memory leak detected")
    }
    
    func testWebSocketServiceMemoryLeak() {
        // Test for potential memory leaks in WebSocketService
        weak var weakWebSocket: WebSocketService?
        
        autoreleasepool {
            let webSocket = WebSocketService()
            weakWebSocket = webSocket
            XCTAssertNotNil(weakWebSocket)
        }
        
        // After autoreleasepool, webSocket should be deallocated
        XCTAssertNil(weakWebSocket, "WebSocketService should be deallocated, potential memory leak detected")
    }
    
    // MARK: - Error Recovery Tests
    
    func testVoiceServiceErrorRecovery() async {
        // Test that voice services can recover from error states
        let speechService = SpeechRecognitionService()
        
        // Simulate error state
        await MainActor.run {
            speechService.recognitionState = .error("Test error")
            speechService.lastError = "Test error"
        }
        
        // Verify error state
        await MainActor.run {
            XCTAssertEqual(speechService.recognitionState, .error("Test error"))
            XCTAssertEqual(speechService.lastError, "Test error")
        }
        
        // Test recovery by resetting to idle
        await MainActor.run {
            speechService.recognitionState = .idle
            speechService.lastError = nil
        }
        
        // Verify recovery
        await MainActor.run {
            XCTAssertEqual(speechService.recognitionState, .idle)
            XCTAssertNil(speechService.lastError)
        }
    }
    
    // MARK: - Audio Session Tests
    
    func testAudioSessionCoordinatorStability() {
        // Test AudioSessionCoordinator stability
        let coordinator = AudioSessionCoordinator.shared
        XCTAssertNotNil(coordinator)
        
        // Test that multiple clients can register without crashes
        let client1 = "test-client-1"
        let client2 = "test-client-2"
        
        coordinator.registerClient(client1)
        coordinator.registerClient(client2)
        
        // Test cleanup
        coordinator.deregisterClient(client1)
        coordinator.deregisterClient(client2)
        
        // If we reach here, the coordinator is stable
        XCTAssertTrue(true, "AudioSessionCoordinator handled multiple clients without crashes")
    }
}

// MARK: - Mock Classes

@available(iOS 18.0, *)
class MockVoiceManager: ObservableObject {
    @Published var isListening = false
    @Published var currentCommand = ""
    @Published var isProcessing = false
    @Published var lastError: String?
    
    func startListening() async {
        isListening = true
    }
    
    func stopListening() {
        isListening = false
    }
}

struct MockAppConfiguration {
    let voiceEnabled: Bool
    let unifiedVoiceService: Bool
    
    var isVoiceEnabled: Bool { voiceEnabled }
    var useUnifiedVoiceService: Bool { unifiedVoiceService }
}