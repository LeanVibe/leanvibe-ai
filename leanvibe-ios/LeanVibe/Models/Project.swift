import Foundation

// MARK: - Project Models

struct Project: Identifiable, Codable, Equatable {
    // Schema-required properties
    let id: UUID
    var displayName: String // NOT 'name' to avoid conflicts per schema
    var description: String?
    var status: ProjectStatus
    var tasksCount: Int // NOT 'taskCount' per schema
    var completedTasksCount: Int
    var issuesCount: Int // NOT 'issueCount' per schema
    let createdAt: Date
    var updatedAt: Date
    
    // Extended properties for implementation
    let path: String
    let language: ProjectLanguage
    let lastActivity: Date
    let metrics: ProjectMetrics
    let clientId: String?
    
    init(
        id: UUID = UUID(),
        displayName: String,
        description: String? = nil,
        status: ProjectStatus = .active,
        tasksCount: Int = 0,
        completedTasksCount: Int = 0,
        issuesCount: Int = 0,
        path: String,
        language: ProjectLanguage,
        lastActivity: Date = Date(),
        metrics: ProjectMetrics = ProjectMetrics(),
        clientId: String? = nil
    ) {
        self.id = id
        self.displayName = displayName
        self.description = description
        self.status = status
        self.tasksCount = tasksCount
        self.completedTasksCount = completedTasksCount
        self.issuesCount = issuesCount
        self.createdAt = Date()
        self.updatedAt = Date()
        self.path = path
        self.language = language
        self.lastActivity = lastActivity
        self.metrics = metrics
        self.clientId = clientId
    }
}

enum ProjectLanguage: String, CaseIterable, Codable {
    case swift = "Swift"
    case python = "Python"
    case javascript = "JavaScript"
    case typescript = "TypeScript"
    case kotlin = "Kotlin"
    case java = "Java"
    case csharp = "C#"
    case go = "Go"
    case rust = "Rust"
    case unknown = "Unknown"
    
    var icon: String {
        switch self {
        case .swift: return "swift"
        case .python: return "terminal.fill"
        case .javascript, .typescript: return "globe"
        case .kotlin, .java: return "cup.and.saucer.fill"
        case .csharp: return "square.fill"
        case .go: return "arrow.triangle.2.circlepath"
        case .rust: return "gear.badge"
        case .unknown: return "questionmark.folder"
        }
    }
    
    var color: String {
        switch self {
        case .swift: return "orange"
        case .python: return "yellow"
        case .javascript: return "yellow"
        case .typescript: return "blue"
        case .kotlin: return "purple"
        case .java: return "red"
        case .csharp: return "blue"
        case .go: return "cyan"
        case .rust: return "brown"
        case .unknown: return "gray"
        }
    }
}

enum ProjectStatus: String, CaseIterable, Codable {
    case planning = "planning"
    case active = "active"
    case inactive = "inactive"
    case completed = "completed"
    case archived = "archived"
    
    var color: String {
        switch self {
        case .planning: return "blue"
        case .active: return "green"
        case .inactive: return "orange"
        case .completed: return "purple"
        case .archived: return "gray"
        }
    }
    
    var icon: String {
        switch self {
        case .planning: return "calendar"
        case .active: return "checkmark.circle.fill"
        case .inactive: return "pause.circle.fill"
        case .completed: return "checkmark.seal.fill"
        case .archived: return "archivebox.fill"
        }
    }
    
    var displayName: String {
        switch self {
        case .planning: return "Planning"
        case .active: return "Active"
        case .inactive: return "Inactive"
        case .completed: return "Completed"
        case .archived: return "Archived"
        }
    }
}

struct ProjectMetrics: Codable, Equatable {
    let filesCount: Int
    let linesOfCode: Int
    let lastBuildTime: TimeInterval?
    let testCoverage: Double?
    let healthScore: Double
    let issuesCount: Int
    let performanceScore: Double?
    
    init(filesCount: Int = 0, linesOfCode: Int = 0, lastBuildTime: TimeInterval? = nil, testCoverage: Double? = nil, healthScore: Double = 0.85, issuesCount: Int = 0, performanceScore: Double? = nil) {
        self.filesCount = filesCount
        self.linesOfCode = linesOfCode
        self.lastBuildTime = lastBuildTime
        self.testCoverage = testCoverage
        self.healthScore = healthScore
        self.issuesCount = issuesCount
        self.performanceScore = performanceScore
    }
    
    var healthColor: String {
        switch healthScore {
        case 0.8...1.0: return "green"
        case 0.6..<0.8: return "yellow"
        case 0.4..<0.6: return "orange"
        default: return "red"
        }
    }
    
    var healthDescription: String {
        switch healthScore {
        case 0.9...1.0: return "Excellent"
        case 0.8..<0.9: return "Good"
        case 0.6..<0.8: return "Fair"
        case 0.4..<0.6: return "Poor"
        default: return "Critical"
        }
    }
}

// MARK: - Session Models

struct ProjectSession: Identifiable, Codable {
    let id: String
    let projectId: String
    let startTime: Date
    let endTime: Date?
    let duration: TimeInterval
    let activities: [SessionActivity]
    let clientId: String
    
    init(id: String = UUID().uuidString, projectId: String, startTime: Date = Date(), endTime: Date? = nil, duration: TimeInterval = 0, activities: [SessionActivity] = [], clientId: String) {
        self.id = id
        self.projectId = projectId
        self.startTime = startTime
        self.endTime = endTime
        self.duration = duration
        self.activities = activities
        self.clientId = clientId
    }
    
    var isActive: Bool {
        return endTime == nil
    }
    
    var formattedDuration: String {
        let formatter = DateComponentsFormatter()
        formatter.allowedUnits = [.hour, .minute]
        formatter.unitsStyle = .abbreviated
        return formatter.string(from: duration) ?? "0m"
    }
}

struct SessionActivity: Identifiable, Codable {
    let id: String
    let type: ActivityType
    let description: String
    let timestamp: Date
    let metadata: [String: String]?
    
    init(id: String = UUID().uuidString, type: ActivityType, description: String, timestamp: Date = Date(), metadata: [String: String]? = nil) {
        self.id = id
        self.type = type
        self.description = description
        self.timestamp = timestamp
        self.metadata = metadata
    }
}

enum ActivityType: String, CaseIterable, Codable {
    case fileEdit = "file_edit"
    case build = "build"
    case test = "test"
    case debug = "debug"
    case commit = "commit"
    case refactor = "refactor"
    
    var icon: String {
        switch self {
        case .fileEdit: return "pencil"
        case .build: return "hammer"
        case .test: return "checkmark.shield"
        case .debug: return "ladybug"
        case .commit: return "arrow.up.circle"
        case .refactor: return "arrow.triangle.2.circlepath"
        }
    }
    
    var color: String {
        switch self {
        case .fileEdit: return "blue"
        case .build: return "orange"
        case .test: return "green"
        case .debug: return "red"
        case .commit: return "purple"
        case .refactor: return "cyan"
        }
    }
}