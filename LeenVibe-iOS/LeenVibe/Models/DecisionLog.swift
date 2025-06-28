
import Foundation

struct DecisionLog: Identifiable, Decodable {
    let id = UUID()
    let decision: String
    let reason: String
    let confidenceScore: Double
    let timestamp: Date
    
    enum CodingKeys: String, CodingKey {
        case decision, reason, confidenceScore = "confidence_score", timestamp
    }
}
