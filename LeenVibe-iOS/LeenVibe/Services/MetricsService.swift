import Foundation

@available(macOS 10.15, iOS 13.0, *)
@MainActor
class MetricsService: ObservableObject {
    private let baseURL = URL(string: "http://localhost:8000")!

    func fetchMetricHistory(clientId: String) async throws -> [MetricHistory] {
        let url = baseURL.appendingPathComponent("metrics/\(clientId)/history")
        let (data, _) = try await URLSession.shared.data(from: url)
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        return try decoder.decode([MetricHistory].self, from: data)
    }

    func fetchDecisionLog(clientId: String) async throws -> [DecisionLog] {
        let url = baseURL.appendingPathComponent("decisions/\(clientId)")
        let (data, _) = try await URLSession.shared.data(from: url)
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        return try decoder.decode([DecisionLog].self, from: data)
    }
}
