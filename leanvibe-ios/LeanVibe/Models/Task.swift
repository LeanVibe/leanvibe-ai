import Foundation
import UniformTypeIdentifiers

// MARK: - Task Management Models

struct LeanVibeTask: Identifiable, Codable, Sendable, Transferable {
    let id: UUID
    var title: String
    var description: String? // Optional per schema
    var status: TaskStatus
    var priority: TaskPriority
    var projectId: UUID // Required per schema
    var createdAt: Date
    var updatedAt: Date
    
    // Extended properties (not in core schema but useful for implementation)
    var confidence: Double // 0.0 to 1.0 for AI confidence
    var agentDecision: AgentDecision?
    var clientId: String
    var assignedTo: String? // Agent or user identifier
    var estimatedEffort: TimeInterval? // In seconds
    var actualEffort: TimeInterval? // In seconds
    var tags: [String]
    var dependencies: [UUID] // Task IDs this task depends on
    var attachments: [TaskAttachment]
    
    // MARK: - Backend Compatibility
    enum CodingKeys: String, CodingKey {
        case id
        case title
        case description
        case status
        case priority
        case projectId = "project_id"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
        case confidence
        case agentDecision = "agent_decision"
        case clientId = "client_id"
        case assignedTo = "assigned_to"
        case estimatedEffort = "estimated_effort"
        case actualEffort = "actual_effort"
        case tags
        case dependencies
        case attachments
    }
    
    init(
        id: UUID = UUID(),
        title: String,
        description: String? = nil, // Optional per schema
        status: TaskStatus = .todo, // Updated to match schema
        priority: TaskPriority = .medium,
        projectId: UUID, // Required per schema
        confidence: Double = 1.0,
        clientId: String,
        assignedTo: String? = nil,
        estimatedEffort: TimeInterval? = nil,
        tags: [String] = [],
        dependencies: [UUID] = [],
        attachments: [TaskAttachment] = []
    ) {
        self.id = id
        self.title = title
        self.description = description
        self.status = status
        self.priority = priority
        self.projectId = projectId
        self.createdAt = Date()
        self.updatedAt = Date()
        self.confidence = confidence
        self.agentDecision = nil
        self.clientId = clientId
        self.assignedTo = assignedTo
        self.estimatedEffort = estimatedEffort
        self.actualEffort = nil
        self.tags = tags
        self.dependencies = dependencies
        self.attachments = attachments
    }
    
    // MARK: - Computed Properties
    
    var confidenceLevel: ConfidenceLevel {
        switch confidence {
        case 0.8...1.0:
            return .high
        case 0.5..<0.8:
            return .medium
        case 0.0..<0.5:
            return .low
        default:
            return .medium
        }
    }
    
    var requiresApproval: Bool {
        return confidence < 0.8 || agentDecision?.requiresHumanApproval == true
    }
    
    var isBlocked: Bool {
        return dependencies.count > 0 // Simplified - in real app would check if dependencies are complete
    }
    
    var statusColor: String {
        switch status {
        case .backlog:
            return "orange"
        case .todo:
            return "gray"
        case .inProgress:
            return "blue"
        case .testing:
            return "purple"
        case .done:
            return "green"
        }
    }
    
    var priorityEmoji: String {
        switch priority {
        case .low:
            return "🟢"
        case .medium:
            return "🟡"
        case .high:
            return "🟠"
        case .urgent:
            return "🔴"
        }
    }
    
    // MARK: - Transferable Implementation
    
    @available(macOS 13.0, iOS 16.0, *)
    static var transferRepresentation: some TransferRepresentation {
        CodableRepresentation(contentType: .kanbanTask)
    }
}

@available(macOS 11.0, iOS 14.0, *)
extension UTType {
    static let kanbanTask = UTType(exportedAs: "ai.leanvibe.task")
}

enum TaskStatus: String, CaseIterable, Codable, Sendable {
    case backlog = "backlog"
    case todo = "todo"
    case inProgress = "in_progress"  // Backend compatibility
    case testing = "testing"
    case done = "done"
    
    var displayName: String {
        switch self {
        case .backlog:
            return "Backlog"
        case .todo:
            return "To Do"
        case .inProgress:
            return "In Progress"
        case .testing:
            return "Testing"
        case .done:
            return "Done"
        }
    }
    
    var systemIcon: String {
        switch self {
        case .backlog:
            return "archivebox"
        case .todo:
            return "tray"
        case .inProgress:
            return "gear"
        case .testing:
            return "testtube.2"
        case .done:
            return "checkmark.circle.fill"
        }
    }
}

enum TaskPriority: String, CaseIterable, Codable, Sendable {
    case low = "low"
    case medium = "medium"
    case high = "high"
    case urgent = "urgent"
    
    var weight: Int {
        switch self {
        case .low:
            return 1
        case .medium:
            return 2
        case .high:
            return 3
        case .urgent:
            return 4
        }
    }
}

import SwiftUI

@available(macOS 10.15, iOS 13.0, *)
extension TaskPriority {
    var swiftUIColor: Color {
        switch self {
        case .low:
            return .green
        case .medium:
            return .blue
        case .high:
            return .orange
        case .urgent:
            return .red
        }
    }
    
    var color: String {
        switch self {
        case .low:
            return "green"
        case .medium:
            return "blue"
        case .high:
            return "orange"
        case .urgent:
            return "red"
        }
    }
}

enum ConfidenceLevel: String, CaseIterable, Sendable {
    case high = "high"
    case medium = "medium"
    case low = "low"
    
    var color: String {
        switch self {
        case .high:
            return "green"
        case .medium:
            return "yellow"
        case .low:
            return "red"
        }
    }
    
    var emoji: String {
        switch self {
        case .high:
            return "🟢"
        case .medium:
            return "🟡"
        case .low:
            return "🔴"
        }
    }
}

// MARK: - Agent Decision Models

struct AgentDecision: Codable, Sendable {
    let id: UUID
    let taskId: UUID
    let recommendation: String
    let reasoning: String
    let confidence: Double
    let requiresHumanApproval: Bool
    let suggestedActions: [SuggestedAction]
    let createdAt: Date
    var approvalStatus: ApprovalStatus
    var humanFeedback: String?
    
    init(
        id: UUID = UUID(),
        taskId: UUID,
        recommendation: String,
        reasoning: String,
        confidence: Double,
        requiresHumanApproval: Bool = false,
        suggestedActions: [SuggestedAction] = []
    ) {
        self.id = id
        self.taskId = taskId
        self.recommendation = recommendation
        self.reasoning = reasoning
        self.confidence = confidence
        self.requiresHumanApproval = requiresHumanApproval
        self.suggestedActions = suggestedActions
        self.createdAt = Date()
        self.approvalStatus = .pending
        self.humanFeedback = nil
    }
}

struct SuggestedAction: Codable, Sendable {
    let id: UUID
    let title: String
    let description: String
    let type: ActionType
    let confidence: Double
    
    init(
        id: UUID = UUID(),
        title: String,
        description: String,
        type: ActionType,
        confidence: Double
    ) {
        self.id = id
        self.title = title
        self.description = description
        self.type = type
        self.confidence = confidence
    }
}

enum ActionType: String, Codable, Sendable {
    case codeGeneration = "code_generation"
    case codeReview = "code_review"
    case testing = "testing"
    case documentation = "documentation"
    case refactoring = "refactoring"
    case debugging = "debugging"
}

enum ApprovalStatus: String, Codable, Sendable {
    case pending = "pending"
    case approved = "approved"
    case rejected = "rejected"
    case modified = "modified"
    
    var displayName: String {
        switch self {
        case .pending:
            return "Pending Review"
        case .approved:
            return "Approved"
        case .rejected:
            return "Rejected"
        case .modified:
            return "Modified"
        }
    }
    
    var color: String {
        switch self {
        case .pending:
            return "orange"
        case .approved:
            return "green"
        case .rejected:
            return "red"
        case .modified:
            return "blue"
        }
    }
}

// MARK: - Task Attachment Models

struct TaskAttachment: Identifiable, Codable, Sendable {
    let id: UUID
    let fileName: String
    let fileType: AttachmentType
    let url: String? // For remote files
    let data: Data? // For local files
    let createdAt: Date
    
    init(
        id: UUID = UUID(),
        fileName: String,
        fileType: AttachmentType,
        url: String? = nil,
        data: Data? = nil
    ) {
        self.id = id
        self.fileName = fileName
        self.fileType = fileType
        self.url = url
        self.data = data
        self.createdAt = Date()
    }
}

enum AttachmentType: String, Codable, Sendable {
    case image = "image"
    case document = "document"
    case code = "code"
    case log = "log"
    case other = "other"
    
    var systemIcon: String {
        switch self {
        case .image:
            return "photo"
        case .document:
            return "doc.text"
        case .code:
            return "chevron.left.forwardslash.chevron.right"
        case .log:
            return "list.bullet.rectangle"
        case .other:
            return "paperclip"
        }
    }
}

// MARK: - WebSocket Task Messages

struct TaskUpdateMessage: Codable, Sendable {
    let type: String
    let task: LeanVibeTask
    let clientId: String
    let timestamp: String
    
    init(task: LeanVibeTask, clientId: String) {
        self.type = "task_update"
        self.task = task
        self.clientId = clientId
        self.timestamp = ISO8601DateFormatter().string(from: Date())
    }
}

struct TaskCreationMessage: Codable, Sendable {
    let type: String
    let title: String
    let description: String
    let priority: TaskPriority
    let assignedTo: String?
    let tags: [String]
    let clientId: String
    let timestamp: String
    
    init(
        title: String,
        description: String,
        priority: TaskPriority = .medium,
        assignedTo: String? = nil,
        tags: [String] = [],
        clientId: String
    ) {
        self.type = "create_task"
        self.title = title
        self.description = description
        self.priority = priority
        self.assignedTo = assignedTo
        self.tags = tags
        self.clientId = clientId
        self.timestamp = ISO8601DateFormatter().string(from: Date())
    }
}

struct AgentDecisionMessage: Codable, Sendable {
    let type: String
    let decision: AgentDecision
    let clientId: String
    let timestamp: String
    
    init(decision: AgentDecision, clientId: String) {
        self.type = "agent_decision"
        self.decision = decision
        self.clientId = clientId
        self.timestamp = ISO8601DateFormatter().string(from: Date())
    }
}

// MARK: - Task Response Models

struct TaskResponse: Codable, Sendable {
    let status: String
    let message: String
    let task: LeanVibeTask?
    let tasks: [LeanVibeTask]?
    let error: String?
    
    var isSuccess: Bool {
        return status == "success"
    }
}

struct TaskListResponse: Codable, Sendable {
    let status: String
    let message: String
    let tasks: [LeanVibeTask]
    let totalCount: Int
    let hasMore: Bool
    
    var isSuccess: Bool {
        return status == "success"
    }
}