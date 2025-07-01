import Foundation

// MARK: - Code Completion Request

struct CodeCompletionRequest: Codable {
    let filePath: String
    let cursorPosition: Int
    let content: String
    let language: String
    let intent: String
    
    enum CodingKeys: String, CodingKey {
        case filePath = "file_path"
        case cursorPosition = "cursor_position"
        case content
        case language
        case intent
    }
}

// MARK: - Code Completion Response

struct CodeCompletionResponse: Codable, Identifiable {
    let id = UUID()
    let status: String
    let intent: String
    let response: String
    let confidence: Double
    let requiresReview: Bool
    let suggestions: [String]
    let contextUsed: ContextUsed
    let processingTimeMs: Double
    
    enum CodingKeys: String, CodingKey {
        case status, intent, response, confidence
        case requiresReview = "requires_review"
        case suggestions
        case contextUsed = "context_used"
        case processingTimeMs = "processing_time_ms"
    }
}

// MARK: - Context Used

struct ContextUsed: Codable {
    let language: String
    let symbolsFound: Int
    let hasContext: Bool
    let filePath: String
    let hasSymbolContext: Bool
    let languageDetected: String
    
    enum CodingKeys: String, CodingKey {
        case language
        case symbolsFound = "symbols_found"
        case hasContext = "has_context"
        case filePath = "file_path"
        case hasSymbolContext = "has_symbol_context"
        case languageDetected = "language_detected"
    }
}

// MARK: - Code Completion Message

struct CodeCompletionMessage: Codable {
    let type: String
    let request: CodeCompletionRequest
    let timestamp: Date
    let clientId: String = "ios-code-completion"
    
    enum CodingKeys: String, CodingKey {
        case type, request, timestamp
        case clientId = "client_id"
    }
}