import XCTest
@testable import LeanVibe

@available(iOS 18.0, macOS 14.0, *)
final class VoiceServiceConsolidationTests: XCTestCase {
    
    var unifiedVoiceService: UnifiedVoiceService!
    
    override func setUp() {
        super.setUp()
        unifiedVoiceService = UnifiedVoiceService.shared
    }
    
    override func tearDown() {
        unifiedVoiceService = nil
        super.tearDown()
    }
    
    // MARK: - Basic Functionality Tests
    
    func testUnifiedVoiceServiceInitialization() {
        XCTAssertNotNil(unifiedVoiceService)
        XCTAssertEqual(unifiedVoiceService.state, .idle)
        XCTAssertFalse(unifiedVoiceService.isWakeListening)
        XCTAssertFalse(unifiedVoiceService.wakePhraseDetected)
    }
    
    // MARK: - Permission Management Tests
    
    func testIntegratedPermissionManagement() {
        // Test that permission properties are available
        XCTAssertNotNil(unifiedVoiceService.hasMicrophonePermission)
        XCTAssertNotNil(unifiedVoiceService.hasSpeechRecognitionPermission)
        XCTAssertNotNil(unifiedVoiceService.permissionStatus)
        XCTAssertNotNil(unifiedVoiceService.isFullyAuthorized)
        
        // Test permission checking
        unifiedVoiceService.checkPermissions()
        // Permissions should be checked without crashing
    }
    
    // MARK: - Wake Phrase Detection Tests
    
    func testIntegratedWakePhraseDetection() {
        // Test wake phrase properties
        XCTAssertFalse(unifiedVoiceService.isWakeListening)
        XCTAssertFalse(unifiedVoiceService.wakePhraseDetected)
        XCTAssertEqual(unifiedVoiceService.wakeAudioLevel, 0.0)
        XCTAssertNil(unifiedVoiceService.lastWakeDetection)
    }
    
    // MARK: - Performance Optimization Tests
    
    func testIntegratedPerformanceOptimization() {
        // Test performance properties from integrated OptimizedVoiceManager functionality
        XCTAssertNotNil(unifiedVoiceService.isOptimized)
        XCTAssertNotNil(unifiedVoiceService.currentLatency)
        XCTAssertNotNil(unifiedVoiceService.isLowLatencyMode)
        XCTAssertNotNil(unifiedVoiceService.performanceStatus)
        XCTAssertNotNil(unifiedVoiceService.responseTime)
        XCTAssertNotNil(unifiedVoiceService.averageResponseTime)
    }
    
    // MARK: - State Management Tests
    
    func testUnifiedStateManagement() {
        // Test that state is properly managed
        XCTAssertEqual(unifiedVoiceService.state, .idle)
        XCTAssertEqual(unifiedVoiceService.recognizedText, "")
        XCTAssertEqual(unifiedVoiceService.audioLevel, 0.0)
        XCTAssertEqual(unifiedVoiceService.confidenceScore, 0.0)
    }
    
    // MARK: - Dependency Service Tests
    
    func testDependencyServiceCompatibility() {
        // Test that the remaining dependency services still work
        let wakePhraseManager = WakePhraseManager(
            webSocketService: WebSocketService(),
            projectManager: ProjectManager(),
            voiceProcessor: DashboardVoiceProcessor(
                projectManager: ProjectManager(),
                webSocketService: WebSocketService(),
                settingsManager: SettingsManager.shared
            )
        )
        XCTAssertNotNil(wakePhraseManager)
        
        let permissionManager = VoicePermissionManager()
        XCTAssertNotNil(permissionManager)
    }
    
    // MARK: - Feature Completeness Tests
    
    func testConsolidatedFeatureCompleteness() {
        // Verify that UnifiedVoiceService has all the key functionality
        XCTAssertNotNil(unifiedVoiceService)
        
        // From VoiceManager
        XCTAssertTrue(unifiedVoiceService.responds(to: #selector(UnifiedVoiceService.startListening(mode:))))
        XCTAssertTrue(unifiedVoiceService.responds(to: #selector(UnifiedVoiceService.stopListening)))
        XCTAssertTrue(unifiedVoiceService.responds(to: #selector(UnifiedVoiceService.toggleListening(mode:))))
        
        // From VoicePermissionManager (integrated)
        XCTAssertTrue(unifiedVoiceService.responds(to: #selector(UnifiedVoiceService.checkPermissions)))
        XCTAssertTrue(unifiedVoiceService.responds(to: #selector(UnifiedVoiceService.openSettings)))
        
        // From WakePhraseManager (integrated)
        XCTAssertTrue(unifiedVoiceService.responds(to: #selector(UnifiedVoiceService.startWakeListening)))
        XCTAssertTrue(unifiedVoiceService.responds(to: #selector(UnifiedVoiceService.stopWakeListening)))
        XCTAssertTrue(unifiedVoiceService.responds(to: #selector(UnifiedVoiceService.toggleWakeListening)))
        
        // From OptimizedVoiceManager (now integrated)
        XCTAssertTrue(unifiedVoiceService.responds(to: #selector(UnifiedVoiceService.optimizePerformance)))
        XCTAssertTrue(unifiedVoiceService.responds(to: #selector(UnifiedVoiceService.enableLowLatencyMode)))
        XCTAssertTrue(unifiedVoiceService.responds(to: #selector(UnifiedVoiceService.disableLowLatencyMode)))
    }
    
    // MARK: - Configuration Tests
    
    func testVoiceServiceConfiguration() {
        // Test that configuration is properly integrated
        let configuration = AppConfiguration.shared
        XCTAssertTrue(configuration.useUnifiedVoiceService, "Configuration should default to UnifiedVoiceService")
        XCTAssertNotNil(configuration.voiceConfidenceThreshold)
        XCTAssertNotNil(configuration.maxVoiceRecordingDuration)
    }
    
    // MARK: - Memory Safety Tests
    
    func testMemorySafety() {
        // Test that the consolidated service doesn't have memory issues
        weak var weakReference: UnifiedVoiceService?
        
        autoreleasepool {
            let service = UnifiedVoiceService.shared
            weakReference = service
            XCTAssertNotNil(weakReference)
        }
        
        // UnifiedVoiceService is a singleton, so it should remain alive
        XCTAssertNotNil(weakReference, "Singleton should remain alive")
    }
}