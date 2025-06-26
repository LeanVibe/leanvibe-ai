import Foundation

struct AgentMessage: Identifiable, Codable {
    let id = UUID()
    let content: String
    let isFromUser: Bool
    let timestamp: Date
    let type: MessageType
    
    enum MessageType: String, Codable {
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

struct WebSocketMessage: Codable {
    let type: String
    let content: String
    let timestamp: String
    let clientId: String?
    
    enum CodingKeys: String, CodingKey {
        case type, content, timestamp
        case clientId = "client_id"
    }
}

struct AgentResponse: Codable {
    let status: String
    let type: String?
    let message: String
    let data: ResponseData?
    let processingTime: Double?
    let timestamp: Double?
    
    enum CodingKeys: String, CodingKey {
        case status, type, message, data, timestamp
        case processingTime = "processing_time"
    }
}

struct ResponseData: Codable {
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

struct FileInfo: Codable, Identifiable {
    let id = UUID()
    let name: String
    let size: Int?
    let type: String
    
    enum CodingKeys: String, CodingKey {
        case name, size, type
    }
}

struct AgentStatusInfo: Codable {
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