import Foundation

// MARK: - Task Management Models

struct LeanVibeTask: Identifiable, Codable, Sendable {
    let id: UUID
    var title: String
    var description: String
    var status: TaskStatus
    var priority: TaskPriority
    var confidence: Double // 0.0 to 1.0 for AI confidence
    var agentDecision: AgentDecision?
    var clientId: String
    var createdAt: Date
    var updatedAt: Date
    var assignedTo: String? // Agent or user identifier
    var estimatedEffort: TimeInterval? // In seconds
    var actualEffort: TimeInterval? // In seconds
    var tags: [String]
    var dependencies: [UUID] // Task IDs this task depends on
    var attachments: [TaskAttachment]
    
    init(
        id: UUID = UUID(),
        title: String,
        description: String,
        status: TaskStatus = .backlog,
        priority: TaskPriority = .medium,
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
        self.confidence = confidence
        self.agentDecision = nil
        self.clientId = clientId
        self.createdAt = Date()
        self.updatedAt = Date()
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
            return "gray"
        case .inProgress:
            return "blue"
        case .testing:
            return "orange"
        case .done:
            return "green"
        case .blocked:
            return "red"
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
        case .critical:
            return "🔴"
        }
    }
}

enum TaskStatus: String, CaseIterable, Codable, Sendable {
    case backlog = "backlog"
    case inProgress = "in_progress"
    case testing = "testing"
    case done = "done"
    case blocked = "blocked"
    
    var displayName: String {
        switch self {
        case .backlog:
            return "Backlog"
        case .inProgress:
            return "In Progress"
        case .testing:
            return "Testing"
        case .done:
            return "Done"
        case .blocked:
            return "Blocked"
        }
    }
    
    var systemIcon: String {
        switch self {
        case .backlog:
            return "tray"
        case .inProgress:
            return "gear"
        case .testing:
            return "checkmark.circle"
        case .done:
            return "checkmark.circle.fill"
        case .blocked:
            return "exclamationmark.triangle.fill"
        }
    }
}

enum TaskPriority: String, CaseIterable, Codable, Sendable {
    case low = "low"
    case medium = "medium"
    case high = "high"
    case critical = "critical"
    
    var weight: Int {
        switch self {
        case .low:
            return 1
        case .medium:
            return 2
        case .high:
            return 3
        case .critical:
            return 4
        }
    }
}

import SwiftUI

extension TaskPriority {
    var color: Color {
        switch self {
        case .low:
            return .green
        case .medium:
            return .blue
        case .high:
            return .orange
        case .critical:
            return .red
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
    let type: String = "task_update"
    let task: LeanVibeTask
    let clientId: String
    let timestamp: String
    
    init(task: LeanVibeTask, clientId: String) {
        self.task = task
        self.clientId = clientId
        self.timestamp = ISO8601DateFormatter().string(from: Date())
    }
}

struct TaskCreationMessage: Codable, Sendable {
    let type: String = "create_task"
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
    let type: String = "agent_decision"
    let decision: AgentDecision
    let clientId: String
    let timestamp: String
    
    init(decision: AgentDecision, clientId: String) {
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