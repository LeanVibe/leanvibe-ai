import XCTest
import SwiftUI
@testable import LeanVibe

@available(iOS 18.0, macOS 14.0, *)
final class ErrorDisplayViewTests: XCTestCase {
    
    func testErrorDisplayViewCreatesSuccessfully() {
        // Given
        let errorMessage = "Network timeout occurred"
        
        // When
        let view = ErrorDisplayView(error: errorMessage)
        
        // Then - View should create without crashing
        XCTAssertNotNil(view)
    }
    
    func testErrorDisplayViewWithNilError() {
        // Given/When
        let view = ErrorDisplayView(error: nil)
        
        // Then - View should create without crashing
        XCTAssertNotNil(view)
    }
    
    func testErrorDisplayViewWithRetryCallback() {
        // Given
        var retryTapped = false
        
        // When
        let view = ErrorDisplayView(
            error: "Failed to load data",
            onRetry: { retryTapped = true }
        )
        
        // Then - View should create with callback
        XCTAssertNotNil(view)
    }
}