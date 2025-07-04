import Foundation

struct AgentMessage: Identifiable, Codable, Sendable {
    var id = UUID()
    let content: String
    let isFromUser: Bool
    let timestamp: Date
    let type: MessageType
    
    enum MessageType: String, Codable, Sendable {
        case message = "message"
        case command = "command"
        case response = "response"
        case error = "error"
        case status = "status"
    }
    
    init(content: String, isFromUser: Bool, type: MessageType = .message) {
        self.content = content
        self.isFromUser = isFromUser
        self.timestamp = Date()
        self.type = type
    }
}

struct WebSocketMessage: Codable, Sendable {
    let type: String
    let content: String
    let timestamp: String
    let clientId: String
    let priority: MessagePriority
    let messageId: String?
    let sessionId: String?
    let version: Int?
    
    enum CodingKeys: String, CodingKey {
        case type, content, timestamp, priority
        case clientId = "client_id"
        case messageId = "message_id"
        case sessionId = "session_id"
        case version
    }
    
    init(type: String, content: String, timestamp: String, clientId: String, priority: MessagePriority, messageId: String? = nil, sessionId: String? = nil, version: Int? = nil) {
        self.type = type
        self.content = content
        self.timestamp = timestamp
        self.clientId = clientId
        self.priority = priority
        self.messageId = messageId ?? UUID().uuidString
        self.sessionId = sessionId
        self.version = version ?? 1
    }
}

enum MessagePriority: Int, Codable, Sendable {
    case low = 1
    case normal = 2
    case high = 3
    case critical = 4
}

struct AgentResponse: Codable, Sendable {
    let status: String
    let type: String?
    let message: String
    let data: ResponseData?
    let processingTime: Double?
    let timestamp: Double?
    let confidence: Double?
    let model: String?
    let warning: String?
    let health: ModelHealth?
    
    enum CodingKeys: String, CodingKey {
        case status, type, message, data, timestamp, confidence, model, warning, health
        case processingTime = "processing_time"
    }
}

struct ModelHealth: Codable, Sendable {
    let status: String
    let lastCheck: Double?
    let memoryUsage: Double?
    
    enum CodingKeys: String, CodingKey {
        case status
        case lastCheck = "last_check"
        case memoryUsage = "memory_usage"
    }
}

struct ResponseData: Codable, Sendable {
    let files: [FileInfo]?
    let directories: [FileInfo]?
    let path: String?
    let currentDirectory: String?
    let agentStatus: AgentStatusInfo?
    
    enum CodingKeys: String, CodingKey {
        case files, directories, path
        case currentDirectory = "current_directory"
        case agentStatus = "agent_status"
    }
}

struct FileInfo: Codable, Identifiable, Sendable {
    var id = UUID()
    let name: String
    let size: Int?
    let type: String
    
    enum CodingKeys: String, CodingKey {
        case name, size, type
    }
}

struct AgentStatusInfo: Codable, Sendable {
    let model: String
    let ready: Bool
    let version: String
    let supportedCommands: [String]
    let sessionActive: Bool
    
    enum CodingKeys: String, CodingKey {
        case model, ready, version
        case supportedCommands = "supported_commands"
        case sessionActive = "session_active"
    }
}

// MARK: - Conflict Resolution Models

struct ConflictResolutionMessage: Codable, Sendable {
    let type: String = "conflict_resolution"
    let conflictId: String
    let strategy: ConflictStrategy
    let originalMessage: WebSocketMessage
    let conflictingMessage: WebSocketMessage
    let resolvedMessage: WebSocketMessage
    let timestamp: String
    let clientId: String
    
    enum CodingKeys: String, CodingKey {
        case type
        case conflictId = "conflict_id"
        case strategy
        case originalMessage = "original_message"
        case conflictingMessage = "conflicting_message"
        case resolvedMessage = "resolved_message"
        case timestamp
        case clientId = "client_id"
    }
}

enum ConflictStrategy: String, Codable, Sendable {
    case lastWriteWins = "last_write_wins"
    case firstWriteWins = "first_write_wins"
    case merge = "merge"
    case userChoice = "user_choice"
}

struct ConflictNotification: Codable, Sendable {
    let type: String = "conflict_detected"
    let conflictId: String
    let description: String
    let affectedMessages: [String] // message IDs
    let suggestedResolution: ConflictStrategy
    let userActionRequired: Bool
    let timestamp: String
    
    enum CodingKeys: String, CodingKey {
        case type
        case conflictId = "conflict_id"
        case description
        case affectedMessages = "affected_messages"
        case suggestedResolution = "suggested_resolution"
        case userActionRequired = "user_action_required"
        case timestamp
    }
}