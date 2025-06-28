import Foundation

// MARK: - Project Models

struct Project: Identifiable, Codable, Equatable {
    let id: String
    let name: String
    let path: String
    let language: ProjectLanguage
    let status: ProjectStatus
    let lastActivity: Date
    let metrics: ProjectMetrics
    let clientId: String?
    
    var displayName: String {
        return name.isEmpty ? URL(fileURLWithPath: path).lastPathComponent : name
    }
    
    var isActive: Bool {
        return status == .active && clientId != nil
    }
    
    init(
        id: String = UUID().uuidString,
        name: String,
        path: String,
        language: ProjectLanguage = .unknown,
        status: ProjectStatus = .inactive,
        lastActivity: Date = Date(),
        metrics: ProjectMetrics = ProjectMetrics(),
        clientId: String? = nil
    ) {
        self.id = id
        self.name = name
        self.path = path
        self.language = language
        self.status = status
        self.lastActivity = lastActivity
        self.metrics = metrics
        self.clientId = clientId
    }
}

enum ProjectLanguage: String, Codable, CaseIterable {
    case swift = "swift"
    case python = "python"
    case javascript = "javascript"
    case typescript = "typescript"
    case rust = "rust"
    case go = "go"
    case java = "java"
    case csharp = "csharp"
    case cpp = "cpp"
    case unknown = "unknown"
    
    var displayName: String {
        switch self {
        case .swift: return "Swift"
        case .python: return "Python"
        case .javascript: return "JavaScript"
        case .typescript: return "TypeScript"
        case .rust: return "Rust"
        case .go: return "Go"
        case .java: return "Java"
        case .csharp: return "C#"
        case .cpp: return "C++"
        case .unknown: return "Unknown"
        }
    }
    
    var iconName: String {
        switch self {
        case .swift: return "swift"
        case .python: return "snake.fill"
        case .javascript, .typescript: return "curlybraces"
        case .rust: return "gear.badge"
        case .go: return "go.forward"
        case .java: return "cup.and.saucer.fill"
        case .csharp: return "number.square"
        case .cpp: return "plus.plus"
        case .unknown: return "questionmark.folder"
        }
    }
    
    var color: String {
        switch self {
        case .swift: return "orange"
        case .python: return "blue"
        case .javascript: return "yellow"
        case .typescript: return "blue"
        case .rust: return "brown"
        case .go: return "cyan"
        case .java: return "red"
        case .csharp: return "purple"
        case .cpp: return "gray"
        case .unknown: return "gray"
        }
    }
}

enum ProjectStatus: String, Codable, CaseIterable {
    case active = "active"
    case inactive = "inactive"
    case analyzing = "analyzing"
    case error = "error"
    case building = "building"
    case testing = "testing"
    
    var displayName: String {
        switch self {
        case .active: return "Active"
        case .inactive: return "Inactive"
        case .analyzing: return "Analyzing"
        case .error: return "Error"
        case .building: return "Building"
        case .testing: return "Testing"
        }
    }
    
    var color: String {
        switch self {
        case .active: return "green"
        case .inactive: return "gray"
        case .analyzing: return "blue"
        case .error: return "red"
        case .building: return "orange"
        case .testing: return "purple"
        }
    }
    
    var iconName: String {
        switch self {
        case .active: return "checkmark.circle.fill"
        case .inactive: return "circle"
        case .analyzing: return "magnifyingglass.circle.fill"
        case .error: return "exclamationmark.triangle.fill"
        case .building: return "hammer.circle.fill"
        case .testing: return "testtube.2"
        }
    }
}

// MARK: - Project Metrics

struct ProjectMetrics: Codable, Equatable {
    let fileCount: Int
    let lineCount: Int
    let complexity: Double
    let testCoverage: Double?
    let buildTime: Double?
    let memoryUsage: Double?
    let cpuUsage: Double?
    let issueCount: Int
    let performanceScore: Double?
    let lastAnalyzed: Date?
    
    init(
        fileCount: Int = 0,
        lineCount: Int = 0,
        complexity: Double = 0.0,
        testCoverage: Double? = nil,
        buildTime: Double? = nil,
        memoryUsage: Double? = nil,
        cpuUsage: Double? = nil,
        issueCount: Int = 0,
        performanceScore: Double? = nil,
        lastAnalyzed: Date? = nil
    ) {
        self.fileCount = fileCount
        self.lineCount = lineCount
        self.complexity = complexity
        self.testCoverage = testCoverage
        self.buildTime = buildTime
        self.memoryUsage = memoryUsage
        self.cpuUsage = cpuUsage
        self.issueCount = issueCount
        self.performanceScore = performanceScore
        self.lastAnalyzed = lastAnalyzed
    }
    
    var healthScore: Double {
        var score = 1.0
        
        // Complexity penalty
        if complexity > 10 {
            score -= 0.2
        }
        
        // Issue penalty
        if issueCount > 0 {
            score -= min(0.3, Double(issueCount) * 0.05)
        }
        
        // Test coverage bonus
        if let coverage = testCoverage {
            score += (coverage - 0.5) * 0.2
        }
        
        // Performance score factor
        if let performance = performanceScore {
            score = score * performance
        }
        
        return max(0.0, min(1.0, score))
    }
    
    var healthColor: String {
        let health = healthScore
        if health >= 0.8 { return "green" }
        if health >= 0.6 { return "yellow" }
        if health >= 0.4 { return "orange" }
        return "red"
    }
}

// MARK: - Session Integration

struct ProjectSession: Identifiable, Codable {
    let id: String
    let projectId: String
    let clientId: String
    let startTime: Date
    let lastActivity: Date
    let isActive: Bool
    let metrics: SessionMetrics?
    
    init(
        id: String = UUID().uuidString,
        projectId: String,
        clientId: String,
        startTime: Date = Date(),
        lastActivity: Date = Date(),
        isActive: Bool = true,
        metrics: SessionMetrics? = nil
    ) {
        self.id = id
        self.projectId = projectId
        self.clientId = clientId
        self.startTime = startTime
        self.lastActivity = lastActivity
        self.isActive = isActive
        self.metrics = metrics
    }
}

struct SessionMetrics: Codable {
    let commandCount: Int
    let analysisCount: Int
    let errorCount: Int
    let avgResponseTime: Double
    let totalActiveTime: Double
    
    init(
        commandCount: Int = 0,
        analysisCount: Int = 0,
        errorCount: Int = 0,
        avgResponseTime: Double = 0.0,
        totalActiveTime: Double = 0.0
    ) {
        self.commandCount = commandCount
        self.analysisCount = analysisCount
        self.errorCount = errorCount
        self.avgResponseTime = avgResponseTime
        self.totalActiveTime = totalActiveTime
    }
}