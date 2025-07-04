import XCTest
import Combine
@testable import LeanVibe

/// Test suite for MetricsViewModel with 30% stability impact
/// Follows TDD methodology with Swift 6 concurrency support
@available(macOS 10.15, iOS 13.0, *)
final class MetricsViewModelTests: XCTestCase {
    
    // MARK: - Test Dependencies
    
    private var viewModel: MetricsViewModel!
    private var mockMetricsService: MockMetricsService!
    private var cancellables: Set<AnyCancellable>!
    
    // MARK: - Setup & Teardown
    
    nonisolated override func setUpWithError() throws {
        try super.setUpWithError()
        
        mockMetricsService = MockMetricsService()
        viewModel = MetricsViewModel(
            clientId: "test-client-123"
        )
        cancellables = Set<AnyCancellable>()
    }
    
    nonisolated override func tearDownWithError() throws {
        cancellables?.removeAll()
        cancellables = nil
        viewModel = nil
        mockMetricsService = nil
        
        try super.tearDownWithError()
    }
    
    // MARK: - Initialization Tests
    
    @MainActor
    func testMetricsViewModelInitialization() {
        // Test initial state is correct
        XCTAssertTrue(viewModel.metricHistory.isEmpty)
        XCTAssertTrue(viewModel.decisionLog.isEmpty)
        XCTAssertFalse(viewModel.isLoadingMetrics)
        XCTAssertFalse(viewModel.isLoadingDecisions)
        XCTAssertNil(viewModel.errorMessage)
    }
    
    // MARK: - Fetch Metrics Tests (TDD Approach)
    
    @MainActor
    func testFetchMetrics_Success() async {
        // Given: Mock service will return successful data
        let expectedMetrics = [
            createTestMetricHistory(confidenceScore: 0.85),
            createTestMetricHistory(confidenceScore: 0.92)
        ]
        mockMetricsService.mockMetricHistory = expectedMetrics
        
        // When: Fetching metrics
        await viewModel.fetchMetrics()
        
        // Then: State should be updated correctly
        XCTAssertEqual(viewModel.metricHistory.count, 2)
        XCTAssertEqual(viewModel.metricHistory[0].confidenceScore, 0.85, accuracy: 0.001)
        XCTAssertEqual(viewModel.metricHistory[1].confidenceScore, 0.92, accuracy: 0.001)
        XCTAssertFalse(viewModel.isLoadingMetrics)
        XCTAssertNil(viewModel.errorMessage)
    }
    
    @MainActor
    func testFetchMetrics_Failure() async {
        // Given: Mock service will throw an error
        mockMetricsService.shouldThrowError = true
        mockMetricsService.errorToThrow = MockMetricsService.TestError.networkError
        
        // When: Fetching metrics
        await viewModel.fetchMetrics()
        
        // Then: Error state should be set correctly
        XCTAssertTrue(viewModel.metricHistory.isEmpty)
        XCTAssertFalse(viewModel.isLoadingMetrics)
        XCTAssertNotNil(viewModel.errorMessage)
        XCTAssertTrue(viewModel.errorMessage!.contains("Failed to fetch metrics"))
    }
    
    @MainActor
    func testFetchMetrics_LoadingState() async {
        // Given: Mock service will delay response
        mockMetricsService.responseDelay = 0.1
        
        // When: Starting to fetch metrics
        let fetchTask = Task {
            await viewModel.fetchMetrics()
        }
        
        // Then: Loading state should be true initially
        await Task.yield() // Allow the task to start
        XCTAssertTrue(viewModel.isLoadingMetrics)
        XCTAssertNil(viewModel.errorMessage)
        
        // Wait for completion
        await fetchTask.value
        
        // Then: Loading state should be false after completion
        XCTAssertFalse(viewModel.isLoadingMetrics)
    }
    
    // MARK: - Fetch Decisions Tests
    
    @MainActor
    func testFetchDecisions_Success() async {
        // Given: Mock service will return successful decision data
        let expectedDecisions = [
            createTestDecisionLog(decision: "architecture", reason: "Test reasoning 1", confidenceScore: 0.88),
            createTestDecisionLog(decision: "optimization", reason: "Test reasoning 2", confidenceScore: 0.76)
        ]
        mockMetricsService.mockDecisionLog = expectedDecisions
        
        // When: Fetching decisions
        await viewModel.fetchDecisions()
        
        // Then: Decision log should be populated correctly
        XCTAssertEqual(viewModel.decisionLog.count, 2)
        XCTAssertEqual(viewModel.decisionLog[0].decision, "architecture")
        XCTAssertEqual(viewModel.decisionLog[0].confidenceScore, 0.88, accuracy: 0.001)
        XCTAssertEqual(viewModel.decisionLog[1].decision, "optimization")
        XCTAssertEqual(viewModel.decisionLog[1].confidenceScore, 0.76, accuracy: 0.001)
        XCTAssertFalse(viewModel.isLoadingDecisions)
        XCTAssertNil(viewModel.errorMessage)
    }
    
    @MainActor
    func testFetchDecisions_Failure() async {
        // Given: Mock service will throw an error
        mockMetricsService.shouldThrowError = true
        mockMetricsService.errorToThrow = MockMetricsService.TestError.authenticationError
        
        // When: Fetching decisions
        await viewModel.fetchDecisions()
        
        // Then: Error state should be set correctly
        XCTAssertTrue(viewModel.decisionLog.isEmpty)
        XCTAssertFalse(viewModel.isLoadingDecisions)
        XCTAssertNotNil(viewModel.errorMessage)
        XCTAssertTrue(viewModel.errorMessage!.contains("Failed to fetch decisions"))
    }
    
    // MARK: - Computed Properties Tests
    
    @MainActor
    func testAverageConfidence_EmptyHistory() {
        // Given: Empty metric history
        // When: Calculating average confidence
        let average = viewModel.averageConfidence
        
        // Then: Should return 0.0 for empty history
        XCTAssertEqual(average, 0.0, accuracy: 0.001)
    }
    
    @MainActor
    func testAverageConfidence_SingleItem() {
        // Given: Single metric in history
        viewModel.metricHistory = [
            createTestMetricHistory(confidenceScore: 0.75)
        ]
        
        // When: Calculating average confidence
        let average = viewModel.averageConfidence
        
        // Then: Should return the single confidence score
        XCTAssertEqual(average, 0.75, accuracy: 0.001)
    }
    
    @MainActor
    func testAverageConfidence_MultipleItems() {
        // Given: Multiple metrics in history
        viewModel.metricHistory = [
            createTestMetricHistory(confidenceScore: 0.80),
            createTestMetricHistory(confidenceScore: 0.90),
            createTestMetricHistory(confidenceScore: 0.70)
        ]
        
        // When: Calculating average confidence
        let average = viewModel.averageConfidence
        
        // Then: Should return correct average (0.80 + 0.90 + 0.70) / 3 = 0.8
        XCTAssertEqual(average, 0.8, accuracy: 0.001)
    }
    
    // MARK: - Error Handling & Edge Cases
    
    @MainActor
    func testConcurrentFetches() async {
        // Given: Mock service with delay
        mockMetricsService.responseDelay = 0.05
        let expectedMetrics = [createTestMetricHistory(confidenceScore: 0.85)]
        mockMetricsService.mockMetricHistory = expectedMetrics
        
        // When: Starting multiple concurrent fetches
        async let fetch1 = viewModel.fetchMetrics()
        async let fetch2 = viewModel.fetchMetrics()
        async let fetch3 = viewModel.fetchMetrics()
        
        // Wait for all to complete
        await fetch1
        await fetch2
        await fetch3
        
        // Then: Should handle concurrent access gracefully
        XCTAssertEqual(viewModel.metricHistory.count, 1)
        XCTAssertFalse(viewModel.isLoadingMetrics)
        XCTAssertNil(viewModel.errorMessage)
    }
    
    @MainActor
    func testErrorMessageClearing() async {
        // Given: An error state
        mockMetricsService.shouldThrowError = true
        await viewModel.fetchMetrics()
        XCTAssertNotNil(viewModel.errorMessage)
        
        // When: Making a successful request
        mockMetricsService.shouldThrowError = false
        mockMetricsService.mockMetricHistory = [createTestMetricHistory(confidenceScore: 0.85)]
        await viewModel.fetchMetrics()
        
        // Then: Error message should be cleared
        XCTAssertNil(viewModel.errorMessage)
        XCTAssertEqual(viewModel.metricHistory.count, 1)
    }
    
    // MARK: - Performance Tests
    
    @MainActor
    func testLargeDatasetPerformance() async {
        // Given: Large dataset
        let largeDataset = (1...1000).map { i in
            createTestMetricHistory(confidenceScore: Double.random(in: 0.5...1.0))
        }
        mockMetricsService.mockMetricHistory = largeDataset
        
        // When: Fetching large dataset
        let startTime = CFAbsoluteTimeGetCurrent()
        await viewModel.fetchMetrics()
        let endTime = CFAbsoluteTimeGetCurrent()
        
        // Then: Should handle large dataset efficiently
        let executionTime = endTime - startTime
        XCTAssertEqual(viewModel.metricHistory.count, 1000)
        XCTAssertLessThan(executionTime, 1.0, "Processing 1000 metrics should take less than 1 second")
        
        // Test average confidence calculation with large dataset
        let averageStartTime = CFAbsoluteTimeGetCurrent()
        let _ = viewModel.averageConfidence
        let averageEndTime = CFAbsoluteTimeGetCurrent()
        let averageCalculationTime = averageEndTime - averageStartTime
        
        XCTAssertLessThan(averageCalculationTime, 0.1, "Average confidence calculation should be fast")
    }
}

// MARK: - Mock Dependencies

/// Mock MetricsService for testing
class MockMetricsService: MetricsService {
    
    enum TestError: Error, LocalizedError {
        case networkError
        case authenticationError
        case dataCorruption
        
        var errorDescription: String? {
            switch self {
            case .networkError:
                return "Network connection failed"
            case .authenticationError:
                return "Authentication failed"
            case .dataCorruption:
                return "Data corruption detected"
            }
        }
    }
    
    // Configuration properties
    var shouldThrowError = false
    var errorToThrow: TestError = .networkError
    var responseDelay: TimeInterval = 0
    
    // Mock data
    var mockMetricHistory: [MetricHistory] = []
    var mockDecisionLog: [DecisionLog] = []
    
    // Call tracking
    var fetchMetricHistoryCallCount = 0
    var fetchDecisionLogCallCount = 0
    var lastClientId: String?
    
    override func fetchMetricHistory(clientId: String) async throws -> [MetricHistory] {
        fetchMetricHistoryCallCount += 1
        lastClientId = clientId
        
        if responseDelay > 0 {
            try await Task.sleep(nanoseconds: UInt64(responseDelay * 1_000_000_000))
        }
        
        if shouldThrowError {
            throw errorToThrow
        }
        
        return mockMetricHistory
    }
    
    override func fetchDecisionLog(clientId: String) async throws -> [DecisionLog] {
        fetchDecisionLogCallCount += 1
        lastClientId = clientId
        
        if responseDelay > 0 {
            try await Task.sleep(nanoseconds: UInt64(responseDelay * 1_000_000_000))
        }
        
        if shouldThrowError {
            throw errorToThrow
        }
        
        return mockDecisionLog
    }
}

// MARK: - Test Helper Methods

/// Helper function to create test MetricHistory using JSON decoding
func createTestMetricHistory(timestamp: Date = Date(), confidenceScore: Double) -> MetricHistory {
    let dateFormatter = ISO8601DateFormatter()
    let timestampString = dateFormatter.string(from: timestamp)
    
    let json = """
    {
        "timestamp": "\(timestampString)",
        "confidence_score": \(confidenceScore)
    }
    """.data(using: .utf8)!
    
    let decoder = JSONDecoder()
    decoder.dateDecodingStrategy = .iso8601
    
    return try! decoder.decode(MetricHistory.self, from: json)
}

/// Helper function to create test DecisionLog using JSON decoding
func createTestDecisionLog(decision: String, reason: String, confidenceScore: Double, timestamp: Date = Date()) -> DecisionLog {
    let dateFormatter = ISO8601DateFormatter()
    let timestampString = dateFormatter.string(from: timestamp)
    
    let json = """
    {
        "decision": "\(decision)",
        "reason": "\(reason)",
        "confidence_score": \(confidenceScore),
        "timestamp": "\(timestampString)"
    }
    """.data(using: .utf8)!
    
    let decoder = JSONDecoder()
    decoder.dateDecodingStrategy = .iso8601
    
    return try! decoder.decode(DecisionLog.self, from: json)
}