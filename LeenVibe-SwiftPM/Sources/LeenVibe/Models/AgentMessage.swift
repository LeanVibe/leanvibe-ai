import Foundation

public struct AgentMessage: Identifiable, Codable, Sendable {
    public let id = UUID()
    public let content: String
    public let isFromUser: Bool
    public let timestamp: Date
    public let type: MessageType
    
    public enum MessageType: String, Codable, Sendable {
        case message = "message"
        case command = "command"
        case response = "response"
        case error = "error"
        case status = "status"
    }
    
    public init(content: String, isFromUser: Bool, type: MessageType = .message) {
        self.content = content
        self.isFromUser = isFromUser
        self.timestamp = Date()
        self.type = type
    }
}

public struct WebSocketMessage: Codable, Sendable {
    public let type: String
    public let content: String
    public let timestamp: String
    public let clientId: String?
    
    public enum CodingKeys: String, CodingKey {
        case type, content, timestamp
        case clientId = "client_id"
    }
    
    public init(type: String, content: String, timestamp: String, clientId: String? = nil) {
        self.type = type
        self.content = content
        self.timestamp = timestamp
        self.clientId = clientId
    }
}

public struct AgentResponse: Codable, Sendable {
    public let status: String
    public let type: String?
    public let message: String
    public let data: ResponseData?
    public let processingTime: Double?
    public let timestamp: Double?
    public let confidence: Double?
    public let model: String?
    public let warning: String?
    public let health: ModelHealth?
    
    public enum CodingKeys: String, CodingKey {
        case status, type, message, data, timestamp, confidence, model, warning, health
        case processingTime = "processing_time"
    }
}

public struct ModelHealth: Codable, Sendable {
    public let status: String
    public let lastCheck: Double?
    public let memoryUsage: Double?
    
    public enum CodingKeys: String, CodingKey {
        case status
        case lastCheck = "last_check"
        case memoryUsage = "memory_usage"
    }
}

public struct ResponseData: Codable, Sendable {
    public let files: [FileInfo]?
    public let directories: [FileInfo]?
    public let path: String?
    public let currentDirectory: String?
    public let agentStatus: AgentStatusInfo?
    
    public enum CodingKeys: String, CodingKey {
        case files, directories, path
        case currentDirectory = "current_directory"
        case agentStatus = "agent_status"
    }
}

public struct FileInfo: Codable, Identifiable, Sendable {
    public let id = UUID()
    public let name: String
    public let size: Int?
    public let type: String
    
    public enum CodingKeys: String, CodingKey {
        case name, size, type
    }
}

public struct AgentStatusInfo: Codable, Sendable {
    public let model: String
    public let ready: Bool
    public let version: String
    public let supportedCommands: [String]
    public let sessionActive: Bool
    
    public enum CodingKeys: String, CodingKey {
        case model, ready, version
        case supportedCommands = "supported_commands"
        case sessionActive = "session_active"
    }
}