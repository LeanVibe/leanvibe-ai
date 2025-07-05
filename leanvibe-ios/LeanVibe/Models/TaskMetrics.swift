import Foundation

// MARK: - Task Metrics Models for Dashboard Integration

struct TaskMetrics: Codable, Identifiable {
    let id = UUID()
    let totalTasks: Int
    let completionRate: Double
    let averageCompletionTime: TimeInterval?
    let byStatus: TaskStatusCount
    let byPriority: TaskPriorityCount
    let lastUpdated: Date
    
    init(totalTasks: Int, completionRate: Double, averageCompletionTime: TimeInterval? = nil, byStatus: TaskStatusCount, byPriority: TaskPriorityCount) {
        self.totalTasks = totalTasks
        self.completionRate = completionRate
        self.averageCompletionTime = averageCompletionTime
        self.byStatus = byStatus
        self.byPriority = byPriority
        self.lastUpdated = Date()
    }
    
    var completionPercentage: Int {
        return Int(completionRate * 100)
    }
    
    var averageCompletionTimeFormatted: String {
        guard let time = averageCompletionTime else { return "N/A" }
        let hours = Int(time / 3600)
        let minutes = Int((time.truncatingRemainder(dividingBy: 3600)) / 60)
        
        if hours > 0 {
            return "\(hours)h \(minutes)m"
        } else {
            return "\(minutes)m"
        }
    }
}

struct TaskStatusCount: Codable {
    let backlog: Int
    let inProgress: Int
    let testing: Int
    let done: Int
    
    var total: Int {
        return backlog + inProgress + testing + done
    }
    
    var activeCount: Int {
        return inProgress + testing
    }
}

struct TaskPriorityCount: Codable {
    let low: Int
    let medium: Int
    let high: Int
    let urgent: Int // Changed from 'critical' to 'urgent' to match TaskPriority enum
    
    var total: Int {
        return low + medium + high + urgent
    }
    
    var urgentCount: Int {
        return high + urgent // Now correctly references 'urgent' instead of 'critical'
    }
    
    // Backward compatibility for API responses that still use 'critical'
    enum CodingKeys: String, CodingKey {
        case low
        case medium
        case high
        case urgent = "urgent" // Maps to 'urgent' in API
    }
    
    // Custom initializer to handle both 'urgent' and 'critical' from API
    init(low: Int, medium: Int, high: Int, urgent: Int) {
        self.low = low
        self.medium = medium
        self.high = high
        self.urgent = urgent
    }
    
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        low = try container.decode(Int.self, forKey: .low)
        medium = try container.decode(Int.self, forKey: .medium)
        high = try container.decode(Int.self, forKey: .high)
        
        // Try 'urgent' first, then fallback to 'critical' for backward compatibility
        if let urgentValue = try? container.decode(Int.self, forKey: .urgent) {
            urgent = urgentValue
        } else {
            // Fallback to check for 'critical' key in API response
            let criticalContainer = try decoder.container(keyedBy: FallbackCodingKeys.self)
            urgent = try criticalContainer.decodeIfPresent(Int.self, forKey: .critical) ?? 0
        }
    }
    
    private enum FallbackCodingKeys: String, CodingKey {
        case critical
    }
}

// MARK: - Kanban Statistics

struct KanbanStatistics: Codable, Identifiable {
    let id = UUID()
    let columnUtilization: ColumnUtilization
    let throughput: ThroughputMetrics
    let cycleTime: CycleTimeMetrics
    let efficiency: EfficiencyMetrics
    let lastUpdated: Date
    
    init(columnUtilization: ColumnUtilization, throughput: ThroughputMetrics, cycleTime: CycleTimeMetrics, efficiency: EfficiencyMetrics) {
        self.columnUtilization = columnUtilization
        self.throughput = throughput
        self.cycleTime = cycleTime
        self.efficiency = efficiency
        self.lastUpdated = Date()
    }
}

struct ColumnUtilization: Codable {
    let backlogCapacity: Double // 0.0 - 1.0
    let inProgressCapacity: Double // 0.0 - 1.0 (3 max)
    let testingCapacity: Double // 0.0 - 1.0 (2 max)
    let doneGrowthRate: Double // Tasks completed per day
    
    var inProgressUtilizationPercentage: Int {
        return Int(inProgressCapacity * 100)
    }
    
    var testingUtilizationPercentage: Int {
        return Int(testingCapacity * 100)
    }
    
    var isInProgressAtCapacity: Bool {
        return inProgressCapacity >= 1.0
    }
    
    var isTestingAtCapacity: Bool {
        return testingCapacity >= 1.0
    }
}

struct ThroughputMetrics: Codable {
    let tasksCompletedToday: Int
    let tasksCompletedThisWeek: Int
    let averageTasksPerDay: Double
    let velocityTrend: VelocityTrend
    
    enum VelocityTrend: String, Codable, CaseIterable {
        case increasing = "increasing"
        case stable = "stable"
        case decreasing = "decreasing"
        
        var displayName: String {
            switch self {
            case .increasing: return "↗️ Increasing"
            case .stable: return "→ Stable"
            case .decreasing: return "↘️ Decreasing"
            }
        }
        
        var color: String {
            switch self {
            case .increasing: return "green"
            case .stable: return "blue"
            case .decreasing: return "orange"
            }
        }
    }
}

struct CycleTimeMetrics: Codable {
    let averageCycleTime: TimeInterval // Backlog to Done
    let averageInProgressTime: TimeInterval
    let averageTestingTime: TimeInterval
    let bottleneck: BottleneckStage?
    
    enum BottleneckStage: String, Codable, CaseIterable {
        case inProgress = "in_progress"
        case testing = "testing"
        case none = "none"
        
        var displayName: String {
            switch self {
            case .inProgress: return "In Progress"
            case .testing: return "Testing"
            case .none: return "No Bottleneck"
            }
        }
    }
    
    var averageCycleTimeFormatted: String {
        let hours = Int(averageCycleTime / 3600)
        let minutes = Int((averageCycleTime.truncatingRemainder(dividingBy: 3600)) / 60)
        
        if hours > 24 {
            let days = hours / 24
            let remainingHours = hours % 24
            return "\(days)d \(remainingHours)h"
        } else if hours > 0 {
            return "\(hours)h \(minutes)m"
        } else {
            return "\(minutes)m"
        }
    }
}

struct EfficiencyMetrics: Codable {
    let flowEfficiency: Double // 0.0 - 1.0
    let workInProgressRatio: Double // Current WIP vs optimal
    let predictability: Double // 0.0 - 1.0
    let qualityScore: Double // 0.0 - 1.0 (based on rework/bugs)
    
    var flowEfficiencyPercentage: Int {
        return Int(flowEfficiency * 100)
    }
    
    var predictabilityPercentage: Int {
        return Int(predictability * 100)
    }
    
    var qualityScorePercentage: Int {
        return Int(qualityScore * 100)
    }
    
    var overallHealthScore: Double {
        return (flowEfficiency + predictability + qualityScore) / 3.0
    }
    
    var healthScorePercentage: Int {
        return Int(overallHealthScore * 100)
    }
    
    var healthScoreColor: String {
        let score = overallHealthScore
        if score >= 0.8 {
            return "green"
        } else if score >= 0.6 {
            return "orange"
        } else {
            return "red"
        }
    }
}

// MARK: - API Response Models

struct TaskStatsAPIResponse: Codable {
    let totalTasks: Int
    let byStatus: [String: Int]
    let byPriority: [String: Int]
    let completedToday: Int?  // Optional since backend doesn't provide this field yet
    let averageCompletionTime: Double?
    
    func toTaskMetrics() -> TaskMetrics {
        let completionRate = totalTasks > 0 ? Double(byStatus["done"] ?? 0) / Double(totalTasks) : 0.0
        
        let statusCount = TaskStatusCount(
            backlog: byStatus["backlog"] ?? 0,
            inProgress: byStatus["in_progress"] ?? 0,
            testing: byStatus["testing"] ?? 0,
            done: byStatus["done"] ?? 0
        )
        
        let priorityCount = TaskPriorityCount(
            low: byPriority["low"] ?? 0,
            medium: byPriority["medium"] ?? 0,
            high: byPriority["high"] ?? 0,
            urgent: byPriority["urgent"] ?? byPriority["critical"] ?? 0 // Handle both 'urgent' and 'critical' for backward compatibility
        )
        
        return TaskMetrics(
            totalTasks: totalTasks,
            completionRate: completionRate,
            averageCompletionTime: averageCompletionTime,
            byStatus: statusCount,
            byPriority: priorityCount
        )
    }
}

// MARK: - Performance Metrics

struct PerformanceMetrics: Codable, Identifiable {
    let id = UUID()
    let cpuUsage: Double // 0.0 - 1.0
    let memoryUsage: Int // MB
    let networkLatency: TimeInterval // seconds
    let frameRate: Double // FPS
    let apiResponseTime: TimeInterval // seconds
    let lastUpdated: Date
    
    init(cpuUsage: Double, memoryUsage: Int, networkLatency: TimeInterval, frameRate: Double, apiResponseTime: TimeInterval) {
        self.cpuUsage = cpuUsage
        self.memoryUsage = memoryUsage
        self.networkLatency = networkLatency
        self.frameRate = frameRate
        self.apiResponseTime = apiResponseTime
        self.lastUpdated = Date()
    }
    
    var cpuPercentage: Int {
        return Int(cpuUsage * 100)
    }
    
    var isPerformanceGood: Bool {
        return cpuUsage < 0.8 && memoryUsage < 150 && networkLatency < 0.1 && frameRate >= 55
    }
    
    var performanceGrade: String {
        let score = calculatePerformanceScore()
        if score >= 0.9 {
            return "A"
        } else if score >= 0.8 {
            return "B"
        } else if score >= 0.7 {
            return "C"
        } else if score >= 0.6 {
            return "D"
        } else {
            return "F"
        }
    }
    
    private func calculatePerformanceScore() -> Double {
        let cpuScore = max(0, 1.0 - cpuUsage)
        let memoryScore = max(0, 1.0 - Double(memoryUsage) / 200.0) // 200MB threshold
        let latencyScore = max(0, 1.0 - networkLatency / 0.2) // 200ms threshold
        let fpsScore = min(1.0, frameRate / 60.0) // 60 FPS ideal
        
        return (cpuScore + memoryScore + latencyScore + fpsScore) / 4.0
    }
}

// MARK: - System Health Status

struct SystemHealthStatus: Codable, Identifiable {
    let id = UUID()
    let backend: ServiceHealth
    let database: ServiceHealth
    let webSocket: ServiceHealth
    let tasks: ServiceHealth
    let overall: HealthLevel
    let lastChecked: Date
    
    init(backend: ServiceHealth, database: ServiceHealth, webSocket: ServiceHealth, tasks: ServiceHealth) {
        self.backend = backend
        self.database = database
        self.webSocket = webSocket
        self.tasks = tasks
        self.lastChecked = Date()
        
        // Calculate overall health
        let services = [backend, database, webSocket, tasks]
        let healthyCount = services.filter { $0.level == .healthy }.count
        let warningCount = services.filter { $0.level == .warning }.count
        let errorCount = services.filter { $0.level == .error }.count
        
        if errorCount > 0 {
            self.overall = .error
        } else if warningCount > 0 {
            self.overall = .warning
        } else {
            self.overall = .healthy
        }
    }
}

struct ServiceHealth: Codable {
    let serviceName: String
    let level: HealthLevel
    let message: String
    let responseTime: TimeInterval?
    let lastUpdated: Date
    
    init(serviceName: String, level: HealthLevel, message: String, responseTime: TimeInterval? = nil) {
        self.serviceName = serviceName
        self.level = level
        self.message = message
        self.responseTime = responseTime
        self.lastUpdated = Date()
    }
}

enum HealthLevel: String, Codable, CaseIterable {
    case healthy = "healthy"
    case warning = "warning"
    case error = "error"
    
    var displayName: String {
        switch self {
        case .healthy: return "Healthy"
        case .warning: return "Warning"
        case .error: return "Error"
        }
    }
    
    var color: String {
        switch self {
        case .healthy: return "green"
        case .warning: return "orange"
        case .error: return "red"
        }
    }
    
    var iconName: String {
        switch self {
        case .healthy: return "checkmark.circle.fill"
        case .warning: return "exclamationmark.triangle.fill"
        case .error: return "xmark.circle.fill"
        }
    }
}