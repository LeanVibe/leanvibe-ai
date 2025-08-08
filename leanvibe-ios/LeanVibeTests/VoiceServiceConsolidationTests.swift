import XCTest
@testable import LeanVibe

@available(iOS 18.0, macOS 14.0, *)
final class VoiceServiceConsolidationTests: XCTestCase {
    
    var unifiedVoiceService: UnifiedVoiceService!
    var voiceManagerFactory: VoiceManagerFactory!
    
    override func setUp() {
        super.setUp()
        unifiedVoiceService = UnifiedVoiceService.shared
        voiceManagerFactory = VoiceManagerFactory()
    }
    
    override func tearDown() {
        unifiedVoiceService = nil
        voiceManagerFactory = nil
        super.tearDown()
    }
    
    // MARK: - Basic Functionality Tests
    
    func testUnifiedVoiceServiceInitialization() {
        XCTAssertNotNil(unifiedVoiceService)
        XCTAssertEqual(unifiedVoiceService.state, .idle)
        XCTAssertFalse(unifiedVoiceService.isWakeListening)
        XCTAssertFalse(unifiedVoiceService.wakePhraseDetected)
    }
    
    func testVoiceManagerFactoryInitialization() {
        XCTAssertNotNil(voiceManagerFactory)
        XCTAssertNotNil(voiceManagerFactory.currentVoiceService)
        XCTAssertEqual(voiceManagerFactory.migrationStatus, .completed)
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
        // Test that wake phrase properties are available
        XCTAssertFalse(unifiedVoiceService.isWakeListening)
        XCTAssertFalse(unifiedVoiceService.wakePhraseDetected)
        XCTAssertNil(unifiedVoiceService.lastWakeDetection)
        XCTAssertEqual(unifiedVoiceService.wakeAudioLevel, 0.0)
        
        // Test toggle functionality
        unifiedVoiceService.toggleWakeListening()
        // Should not crash, but won't start without permissions in tests
    }
    
    // MARK: - Performance Optimization Tests
    
    func testIntegratedPerformanceOptimization() {
        // Test that performance properties are available
        XCTAssertNotNil(unifiedVoiceService.isOptimized)
        XCTAssertNotNil(unifiedVoiceService.currentLatency)
        XCTAssertNotNil(unifiedVoiceService.isLowLatencyMode)
        XCTAssertNotNil(unifiedVoiceService.performanceStatus)
        
        // Test performance methods
        let performanceReport = unifiedVoiceService.getPerformanceReport()
        XCTAssertNotNil(performanceReport)
        XCTAssertEqual(performanceReport.isOptimized, unifiedVoiceService.isOptimized)
        XCTAssertEqual(performanceReport.isLowLatencyMode, unifiedVoiceService.isLowLatencyMode)
    }
    
    func testPerformanceOptimization() async {
        let initialOptimizedState = unifiedVoiceService.isOptimized
        
        await unifiedVoiceService.optimizePerformance()
        
        XCTAssertTrue(unifiedVoiceService.isOptimized)
        XCTAssertGreaterThanOrEqual(unifiedVoiceService.currentLatency, 0)
    }
    
    func testLowLatencyMode() {
        // Test enabling low latency mode
        unifiedVoiceService.enableLowLatencyMode()
        XCTAssertTrue(unifiedVoiceService.isLowLatencyMode)
        
        // Test disabling low latency mode
        unifiedVoiceService.disableLowLatencyMode()
        XCTAssertFalse(unifiedVoiceService.isLowLatencyMode)
    }
    
    // MARK: - State Management Tests
    
    func testVoiceStateManagement() {
        // Test initial state
        XCTAssertEqual(unifiedVoiceService.state, .idle)
        XCTAssertTrue(unifiedVoiceService.isIdle)
        XCTAssertFalse(unifiedVoiceService.isListening)
        XCTAssertFalse(unifiedVoiceService.needsPermissions)
        
        // Test state display text
        XCTAssertEqual(unifiedVoiceService.currentStateText, "Ready")
    }
    
    func testResetFunctionality() {
        unifiedVoiceService.reset()
        
        XCTAssertEqual(unifiedVoiceService.state, .idle)
        XCTAssertEqual(unifiedVoiceService.recognizedText, "")
        XCTAssertEqual(unifiedVoiceService.audioLevel, 0.0)
        XCTAssertEqual(unifiedVoiceService.confidenceScore, 0.0)
    }
    
    // MARK: - Legacy Service Compatibility Tests
    
    func testLegacyServiceDeprecation() {
        // These should trigger deprecation warnings but still work
        #pragma clang diagnostic push
        #pragma clang diagnostic ignored "-Wdeprecated-declarations"
        
        let legacyVoiceManager = VoiceManager(
            speechService: SpeechRecognitionService(),
            webSocketService: WebSocketService()
        )
        XCTAssertNotNil(legacyVoiceManager)
        
        let legacyGlobalVoiceManager = GlobalVoiceManager(
            webSocketService: WebSocketService(),
            projectManager: ProjectManager(),
            settingsManager: SettingsManager.shared
        )
        XCTAssertNotNil(legacyGlobalVoiceManager)
        
        let legacyOptimizedVoiceManager = OptimizedVoiceManager()
        XCTAssertNotNil(legacyOptimizedVoiceManager)
        
        let legacyWakePhraseManager = WakePhraseManager(
            webSocketService: WebSocketService(),
            projectManager: ProjectManager(),
            voiceProcessor: DashboardVoiceProcessor(
                projectManager: ProjectManager(),
                webSocketService: WebSocketService(),
                settingsManager: SettingsManager.shared
            )
        )
        XCTAssertNotNil(legacyWakePhraseManager)
        
        let legacyPermissionManager = VoicePermissionManager()
        XCTAssertNotNil(legacyPermissionManager)
        
        #pragma clang diagnostic pop
    }
    
    func testVoiceManagerFactoryMigration() async {
        // Test migration to unified service
        await voiceManagerFactory.migrateToUnifiedService()
        XCTAssertTrue(voiceManagerFactory.isUsingUnifiedService)
        XCTAssertEqual(voiceManagerFactory.migrationStatus, .completed)
        XCTAssertNotNil(voiceManagerFactory.unifiedVoiceService)
        
        // Test fallback to legacy services
        await voiceManagerFactory.fallbackToLegacyServices()
        XCTAssertFalse(voiceManagerFactory.isUsingUnifiedService)
        XCTAssertEqual(voiceManagerFactory.migrationStatus, .usingLegacy)
        XCTAssertNotNil(voiceManagerFactory.legacyVoiceManager)
    }
    
    // MARK: - Performance Metrics Tests
    
    func testPerformanceMetrics() {
        let metrics = unifiedVoiceService.getPerformanceMetrics()
        
        XCTAssertNotNil(metrics)
        XCTAssertGreaterThanOrEqual(metrics.currentResponseTime, 0)
        XCTAssertGreaterThanOrEqual(metrics.averageResponseTime, 0)
        XCTAssertNotNil(metrics.performanceStatus)
        XCTAssertGreaterThanOrEqual(metrics.totalMeasurements, 0)
        XCTAssertGreaterThan(metrics.targetResponseTime, 0)
        
        // Test formatted times
        XCTAssertFalse(metrics.formattedCurrentTime.isEmpty)
        XCTAssertFalse(metrics.formattedAverageTime.isEmpty)
        
        // Test target percentage calculation
        XCTAssertGreaterThanOrEqual(metrics.targetPercentage, 0)
    }
    
    func testVoicePerformanceReport() {
        let report = unifiedVoiceService.getPerformanceReport()
        
        XCTAssertNotNil(report)
        XCTAssertGreaterThanOrEqual(report.averageResponseTime, 0)
        XCTAssertGreaterThanOrEqual(report.buffersProcessed, 0)
        XCTAssertGreaterThan(report.recognitionAccuracy, 0)
        XCTAssertGreaterThanOrEqual(report.errorRate, 0)
        
        // Test status calculation
        let status = report.status
        XCTAssertNotNil(status)
        XCTAssertFalse(status.description.isEmpty)
    }
    
    // MARK: - Error Handling Tests
    
    func testVoiceErrorTypes() {
        let permissionError = VoiceError.permissionDenied
        XCTAssertNotNil(permissionError.errorDescription)
        XCTAssertTrue(permissionError.errorDescription!.contains("permission"))
        
        let audioError = VoiceError.audioEngineError("Test error")
        XCTAssertNotNil(audioError.errorDescription)
        XCTAssertTrue(audioError.errorDescription!.contains("Test error"))
        
        let recognitionError = VoiceError.recognitionFailed("Test recognition error")
        XCTAssertNotNil(recognitionError.errorDescription)
        XCTAssertTrue(recognitionError.errorDescription!.contains("Test recognition error"))
    }
    
    // MARK: - Integration Tests
    
    func testFullVoiceWorkflow() async {
        // Test complete voice workflow without actual audio/permissions
        
        // 1. Check initial state
        XCTAssertEqual(unifiedVoiceService.state, .idle)
        
        // 2. Request permissions (will fail in test environment)
        await unifiedVoiceService.requestPermissions()
        // Should not crash
        
        // 3. Test optimization
        await unifiedVoiceService.optimizePerformance()
        XCTAssertTrue(unifiedVoiceService.isOptimized)
        
        // 4. Test reset
        unifiedVoiceService.reset()
        XCTAssertEqual(unifiedVoiceService.state, .idle)
    }
    
    func testConsolidationCompleteness() {
        // Verify that UnifiedVoiceService has all the key functionality
        // that was previously spread across multiple services
        
        // From VoiceManager
        XCTAssertTrue(unifiedVoiceService.responds(to: #selector(UnifiedVoiceService.startListening(mode:))))
        XCTAssertTrue(unifiedVoiceService.responds(to: #selector(UnifiedVoiceService.stopListening)))
        XCTAssertTrue(unifiedVoiceService.responds(to: #selector(UnifiedVoiceService.toggleListening(mode:))))
        
        // From VoicePermissionManager (now integrated)
        XCTAssertTrue(unifiedVoiceService.responds(to: #selector(UnifiedVoiceService.checkPermissions)))
        XCTAssertTrue(unifiedVoiceService.responds(to: #selector(UnifiedVoiceService.openSettings)))
        
        // From WakePhraseManager (now integrated)
        XCTAssertTrue(unifiedVoiceService.responds(to: #selector(UnifiedVoiceService.startWakeListening)))
        XCTAssertTrue(unifiedVoiceService.responds(to: #selector(UnifiedVoiceService.stopWakeListening)))
        XCTAssertTrue(unifiedVoiceService.responds(to: #selector(UnifiedVoiceService.toggleWakeListening)))
        
        // From OptimizedVoiceManager (now integrated)
        XCTAssertTrue(unifiedVoiceService.responds(to: #selector(UnifiedVoiceService.optimizePerformance)))
        XCTAssertTrue(unifiedVoiceService.responds(to: #selector(UnifiedVoiceService.enableLowLatencyMode)))
        XCTAssertTrue(unifiedVoiceService.responds(to: #selector(UnifiedVoiceService.disableLowLatencyMode)))
    }
}