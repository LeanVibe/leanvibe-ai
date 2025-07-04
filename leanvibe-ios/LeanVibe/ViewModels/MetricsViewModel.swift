import Foundation
import Combine

@available(iOS 18.0, macOS 14.0, *)
@MainActor
class MetricsViewModel: ObservableObject {
    @Published var metricHistory: [MetricHistory] = []
    @Published var decisionLog: [DecisionLog] = []
    @Published var isLoadingMetrics = false
    @Published var isLoadingDecisions = false
    @Published var errorMessage: String? = nil

    private let metricsService: MetricsService
    private let clientId: String

    init(clientId: String) {
        self.clientId = clientId
        self.metricsService = MetricsService()
    }

    func fetchMetrics() async {
        isLoadingMetrics = true
        errorMessage = nil
        do {
            metricHistory = try await metricsService.fetchMetricHistory(clientId: clientId)
        } catch {
            errorMessage = "Failed to fetch metrics: \(error.localizedDescription)"
        }
        isLoadingMetrics = false
    }

    func fetchDecisions() async {
        isLoadingDecisions = true
        errorMessage = nil
        do {
            decisionLog = try await metricsService.fetchDecisionLog(clientId: clientId)
        } catch {
            errorMessage = "Failed to fetch decisions: \(error.localizedDescription)"
        }
        isLoadingDecisions = false
    }
    
    var averageConfidence: Double {
        guard !metricHistory.isEmpty else { return 0.0 }
        return metricHistory.map { $0.confidenceScore }.reduce(0, +) / Double(metricHistory.count)
    }
    
    var totalTasksCompleted: Int {
        // Calculate from actual task data
        return metricHistory.count > 0 ? metricHistory.count : 0
    }
    
    // Get real task completion data from metrics service
    func getTotalTasksCompleted() async -> Int {
        do {
            let taskMetrics = try await metricsService.fetchTaskMetricsFromBackend()
            return taskMetrics.byStatus.done
        } catch {
            // Fallback to local calculation if backend is unavailable
            let localMetrics = metricsService.calculateLocalTaskMetrics()
            return localMetrics.byStatus.done
        }
    }
}
