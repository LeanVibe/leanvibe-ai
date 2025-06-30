
import Foundation

struct MetricHistory: Identifiable, Decodable {
    let id = UUID()
    let timestamp: Date
    let confidenceScore: Double
    
    enum CodingKeys: String, CodingKey {
        case timestamp, confidenceScore = "confidence_score"
    }
}

struct TaskCompletionData: Identifiable, Decodable {
    let id = UUID()
    let status: String
    let count: Int
}
