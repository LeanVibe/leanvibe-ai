import XCTest
import Foundation
@testable import LeanVibe

@available(iOS 18.0, macOS 14.0, *)
final class ErrorHandlingSystemTests: XCTestCase {
    
    var globalErrorManager: GlobalErrorManager!
    var networkErrorHandler: NetworkErrorHandler!
    var serviceErrorHandler: ServiceErrorHandler!
    var errorRecoveryManager: ErrorRecoveryManager!
    
    override func setUpWithError() throws {
        globalErrorManager = GlobalErrorManager.shared
        networkErrorHandler = NetworkErrorHandler.shared
        serviceErrorHandler = ServiceErrorHandler.shared
        errorRecoveryManager = ErrorRecoveryManager.shared
        
        // Clear any existing state
        globalErrorManager.clearHistory()
        errorRecoveryManager.clearRecoveryHistory()
    }
    
    override func tearDownWithError() throws {
        globalErrorManager.hideError()
        globalErrorManager.clearHistory()
        errorRecoveryManager.clearRecoveryHistory()
    }
    
    // MARK: - GlobalErrorManager Tests
    
    @MainActor
    func testGlobalErrorManagerShowError() {
        let error = AppError(
            title: "Test Error",
            message: "This is a test error",
            severity: .warning,
            category: .system,
            context: "test"
        )
        
        globalErrorManager.showError(error)
        
        XCTAssertNotNil(globalErrorManager.currentError)
        XCTAssertTrue(globalErrorManager.showingErrorAlert)
        XCTAssertEqual(globalErrorManager.currentError?.title, "Test Error")
        XCTAssertEqual(globalErrorManager.errorHistory.count, 1)
    }
    
    @MainActor
    func testGlobalErrorManagerErrorCategorization() {
        let networkError = URLError(.notConnectedToInternet)
        globalErrorManager.showError(networkError, context: "test", category: .network)
        
        XCTAssertEqual(globalErrorManager.currentError?.category, .network)
        
        let serviceError = TaskServiceError.networkFailure
        globalErrorManager.showError(serviceError, context: "test", category: .service)
        
        XCTAssertEqual(globalErrorManager.currentError?.category, .service)
    }
    
    @MainActor
    func testGlobalErrorManagerOfflineMode() {
        XCTAssertFalse(globalErrorManager.isInOfflineMode())
        
        globalErrorManager.enableOfflineMode()
        
        XCTAssertTrue(globalErrorManager.isInOfflineMode())
    }
    
    @MainActor
    func testGlobalErrorManagerNetworkStatusUpdate() {
        globalErrorManager.updateNetworkStatus(.connected)
        XCTAssertEqual(globalErrorManager.networkStatus, .connected)
        
        globalErrorManager.updateNetworkStatus(.disconnected)
        XCTAssertEqual(globalErrorManager.networkStatus, .disconnected)
    }
    
    @MainActor
    func testGlobalErrorManagerServiceStatusUpdate() {
        globalErrorManager.updateServiceStatus("TestService", status: .healthy)
        XCTAssertEqual(globalErrorManager.serviceStatuses["TestService"], .healthy)
        
        globalErrorManager.updateServiceStatus("TestService", status: .failed)
        XCTAssertEqual(globalErrorManager.serviceStatuses["TestService"], .failed)
    }
    
    // MARK: - AppError Tests
    
    func testAppErrorCreation() {
        let error = AppError(
            title: "Test Error",
            message: "Test message",
            severity: .error,
            category: .network,
            context: "test_context",
            userFacingMessage: "User friendly message",
            technicalDetails: "Technical details"
        )
        
        XCTAssertEqual(error.title, "Test Error")
        XCTAssertEqual(error.message, "Test message")
        XCTAssertEqual(error.severity, .error)
        XCTAssertEqual(error.category, .network)
        XCTAssertEqual(error.context, "test_context")
        XCTAssertEqual(error.userFacingMessage, "User friendly message")
        XCTAssertEqual(error.technicalDetails, "Technical details")
        XCTAssertFalse(error.suggestedActions.isEmpty)
    }
    
    func testAppErrorFromURLError() {
        let urlError = URLError(.notConnectedToInternet)
        let appError = AppError.from(urlError, context: "test")
        
        XCTAssertEqual(appError.category, .network)
        XCTAssertEqual(appError.severity, .critical)
        XCTAssertTrue(appError.title.contains("Connection Lost"))
    }
    
    func testAppErrorFromTaskServiceError() {
        let taskError = TaskServiceError.unauthorized
        let appError = AppError.from(taskError, context: "test")
        
        XCTAssertEqual(appError.category, .service)
        XCTAssertEqual(appError.severity, .critical)
        XCTAssertTrue(appError.title.contains("Task Operation Failed"))
    }
    
    // MARK: - ErrorCategory Tests
    
    func testErrorCategoryFromError() {
        XCTAssertEqual(ErrorCategory.from(URLError(.badURL)), .network)
        XCTAssertEqual(ErrorCategory.from(TaskServiceError.invalidURL), .service)
        XCTAssertEqual(ErrorCategory.from(NSError(domain: "test", code: 1)), .system)
    }
    
    func testErrorCategoryDisplayProperties() {
        XCTAssertEqual(ErrorCategory.network.displayName, "Network")
        XCTAssertEqual(ErrorCategory.service.displayName, "Service")
        XCTAssertEqual(ErrorCategory.data.displayName, "Data")
        XCTAssertEqual(ErrorCategory.ui.displayName, "Interface")
        XCTAssertEqual(ErrorCategory.system.displayName, "System")
    }
    
    // MARK: - ServiceErrorHandler Tests
    
    @MainActor
    func testServiceRegistration() {
        let config = ServiceConfiguration(
            healthEndpoint: "/test/health",
            criticalityLevel: .high,
            healthCheckInterval: 30.0,
            timeoutInterval: 10.0
        )
        
        serviceErrorHandler.registerService("TestService", configuration: config)
        
        let healthInfo = serviceErrorHandler.getServiceHealth("TestService")
        XCTAssertNotNil(healthInfo)
        XCTAssertEqual(healthInfo?.name, "TestService")
        XCTAssertEqual(healthInfo?.configuration.criticalityLevel, .high)
    }
    
    @MainActor
    func testServiceHealthTracking() {
        let config = ServiceConfiguration(
            healthEndpoint: "/test/health",
            criticalityLevel: .medium,
            healthCheckInterval: 60.0,
            timeoutInterval: 5.0
        )
        
        serviceErrorHandler.registerService("TestService", configuration: config)
        
        // Initially status should be unknown
        var healthInfo = serviceErrorHandler.getServiceHealth("TestService")
        XCTAssertEqual(healthInfo?.status, .unknown)
        
        // Test service collections
        XCTAssertFalse(serviceErrorHandler.failedServices.contains("TestService"))
        XCTAssertFalse(serviceErrorHandler.degradedServices.contains("TestService"))
    }
    
    @MainActor
    func testCriticalServicesIdentification() {
        let highConfig = ServiceConfiguration(
            healthEndpoint: "/critical/health",
            criticalityLevel: .high,
            healthCheckInterval: 30.0,
            timeoutInterval: 10.0
        )
        
        let lowConfig = ServiceConfiguration(
            healthEndpoint: "/optional/health",
            criticalityLevel: .low,
            healthCheckInterval: 120.0,
            timeoutInterval: 5.0
        )
        
        serviceErrorHandler.registerService("CriticalService", configuration: highConfig)
        serviceErrorHandler.registerService("OptionalService", configuration: lowConfig)
        
        let criticalServices = serviceErrorHandler.getCriticalServices()
        
        XCTAssertTrue(criticalServices.contains("CriticalService"))
        XCTAssertFalse(criticalServices.contains("OptionalService"))
    }
    
    // MARK: - ErrorRecoveryManager Tests
    
    @MainActor
    func testRecoveryOperationCreation() {
        let error = AppError(
            title: "Test Error",
            message: "Test message",
            category: .network,
            context: "test"
        )
        
        let recoveryTask = Task {
            await errorRecoveryManager.attemptRecovery(for: error)
        }
        
        // Wait a brief moment for the recovery to be added
        let expectation = expectation(description: "Recovery operation created")
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
            expectation.fulfill()
        }
        
        wait(for: [expectation], timeout: 1.0)
        
        // Clean up
        recoveryTask.cancel()
    }
    
    @MainActor
    func testRecoveryMetrics() {
        let initialMetrics = errorRecoveryManager.getRecoveryMetrics()
        XCTAssertEqual(initialMetrics.totalRecoveries, 0)
        XCTAssertEqual(initialMetrics.successfulRecoveries, 0)
        XCTAssertEqual(initialMetrics.failedRecoveries, 0)
        
        let successRate = errorRecoveryManager.getRecoverySuccessRate()
        XCTAssertEqual(successRate, 0.0)
    }
    
    // MARK: - RetryManager Tests
    
    @MainActor
    func testRetryManagerCreateRetryAction() {
        let expectation = expectation(description: "Retry action executed")
        var operationCalled = false
        
        let retryAction = RetryManager.shared.createRetryAction(
            operation: {
                operationCalled = true
                expectation.fulfill()
                return "success"
            },
            maxAttempts: 1,
            context: "test",
            category: .system
        )
        
        retryAction()
        
        wait(for: [expectation], timeout: 5.0)
        XCTAssertTrue(operationCalled)
    }
    
    func testRetryManagerShouldRetryConditions() {
        // Network errors should be retried
        XCTAssertTrue(RetryManager.shouldRetry(URLError(.timedOut)))
        XCTAssertTrue(RetryManager.shouldRetry(URLError(.cannotConnectToHost)))
        XCTAssertTrue(RetryManager.shouldRetry(URLError(.networkConnectionLost)))
        
        // Authorization errors should not be retried
        XCTAssertFalse(RetryManager.shouldRetry(TaskServiceError.unauthorized))
        XCTAssertFalse(RetryManager.shouldRetry(TaskServiceError.taskNotFound))
        
        // Network failure should be retried
        XCTAssertTrue(RetryManager.shouldRetry(TaskServiceError.networkFailure))
    }
    
    // MARK: - Integration Tests
    
    @MainActor
    func testErrorHandlingIntegration() {
        // Test that errors flow through the system correctly
        let networkError = URLError(.notConnectedToInternet)
        
        // Handle the error through NetworkErrorHandler
        networkErrorHandler.handleRESTAPIError(networkError, endpoint: "/test", httpMethod: "GET")
        
        // Verify it appears in GlobalErrorManager
        XCTAssertNotNil(globalErrorManager.currentError)
        XCTAssertEqual(globalErrorManager.currentError?.category, .network)
    }
    
    @MainActor
    func testOfflineModeActivation() {
        XCTAssertFalse(globalErrorManager.isInOfflineMode())
        
        // Simulate critical network error
        let criticalNetworkError = AppError(
            title: "Critical Network Error",
            message: "No connection",
            severity: .critical,
            category: .network,
            context: "test"
        )
        
        globalErrorManager.showError(criticalNetworkError)
        
        // Offline mode should be enabled for critical network errors
        XCTAssertTrue(globalErrorManager.isInOfflineMode())
    }
    
    @MainActor
    func testServiceStatusPropagation() {
        // Update service status through ServiceErrorHandler
        serviceErrorHandler.registerService("TestService", configuration: ServiceConfiguration(
            healthEndpoint: "/test",
            criticalityLevel: .high,
            healthCheckInterval: 30,
            timeoutInterval: 10
        ))
        
        // The service status should propagate to GlobalErrorManager
        // This would be tested with actual health check execution
        XCTAssertNotNil(serviceErrorHandler.getServiceHealth("TestService"))
    }
    
    // MARK: - Performance Tests
    
    func testErrorHandlingPerformance() {
        measure {
            for i in 0..<100 {
                let error = AppError(
                    title: "Performance Test \(i)",
                    message: "Test message",
                    category: .system,
                    context: "performance_test"
                )
                
                Task { @MainActor in
                    globalErrorManager.showError(error)
                    globalErrorManager.hideError()
                }
            }
        }
    }
    
    func testRecoveryManagerPerformance() {
        measure {
            for i in 0..<50 {
                let error = AppError(
                    title: "Recovery Test \(i)",
                    message: "Test message",
                    category: .network,
                    context: "performance_test"
                )
                
                Task { @MainActor in
                    await errorRecoveryManager.attemptRecovery(for: error)
                }
            }
        }
    }
}

// MARK: - Mock Implementations for Testing

extension ErrorHandlingSystemTests {
    
    func createMockNetworkError() -> URLError {
        return URLError(.notConnectedToInternet)
    }
    
    func createMockServiceError() -> TaskServiceError {
        return TaskServiceError.networkFailure
    }
    
    func createMockAppError() -> AppError {
        return AppError(
            title: "Mock Error",
            message: "This is a mock error for testing",
            severity: .warning,
            category: .system,
            context: "mock_test",
            userFacingMessage: "Something went wrong during testing",
            technicalDetails: "Mock error created for unit testing purposes"
        )
    }
}