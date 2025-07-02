import XCTest
@testable import LeanVibe
import Combine

@available(iOS 18.0, macOS 14.0, *)
final class VoiceMigrationTests: XCTestCase {
    
    override func setUp() async throws {
        try await super.setUp()
    }
    
    override func tearDown() async throws {
        try await super.tearDown()
    }
    
    @MainActor
    func testMigrationStatusValues() throws {
        // Test migration status enum values and properties
        let statuses = MigrationStatus.allCases
        
        XCTAssertTrue(statuses.contains(.notStarted))
        XCTAssertTrue(statuses.contains(.usingLegacy))
        XCTAssertTrue(statuses.contains(.migrating))
        XCTAssertTrue(statuses.contains(.completed))
        XCTAssertTrue(statuses.contains(.fallingBack))
        XCTAssertTrue(statuses.contains(.error))
        
        // Test display properties
        for status in statuses {
            XCTAssertFalse(status.displayText.isEmpty)
            XCTAssertNotNil(status.color)
        }
    }
    
    func testAppConfigurationVoiceFlags() {
        // Test that AppConfiguration voice flags are accessible
        let config = AppConfiguration.shared
        
        // These should not throw and should return reasonable values
        XCTAssertTrue(config.voiceConfidenceThreshold >= 0.0)
        XCTAssertTrue(config.voiceConfidenceThreshold <= 1.0)
        XCTAssertTrue(config.maxVoiceRecordingDuration > 0)
        XCTAssertTrue(config.maxVoiceRecordingDuration <= 60)
        
        // Feature flag should be accessible
        let useUnified = config.useUnifiedVoiceService
        XCTAssertTrue(useUnified == true || useUnified == false) // Just ensure it's a valid bool
    }
}