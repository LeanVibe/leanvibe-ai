import Foundation
import Combine
import SwiftUI

// MARK: - Task Service for Backend Integration

@available(iOS 18.0, macOS 14.0, *)
@MainActor
class TaskService: ObservableObject {
    @Published var tasks: [LeanVibeTask] = []
    @Published var taskMetrics: TaskMetrics?
    @Published var kanbanStatistics: KanbanStatistics?
    @Published var performanceMetrics: PerformanceMetrics?
    @Published var systemHealth: SystemHealthStatus?
    @Published var isLoading = false
    @Published var lastError: String?
    
    private let baseURL: String
    private var cancellables = Set<AnyCancellable>()
    private let session = URLSession.shared
    private let userDefaultsKey = "leanvibe_tasks"
    private let jsonEncoder = JSONEncoder()
    private let jsonDecoder = JSONDecoder()
    
    init(baseURL: String = "http://localhost:8002") {
        self.baseURL = baseURL
        setupDateFormatting()
        loadPersistedTasks()
        setupPerformanceMonitoring()
    }
    
    private func setupDateFormatting() {
        jsonEncoder.dateEncodingStrategy = .iso8601
        jsonDecoder.dateDecodingStrategy = .iso8601
    }
    
    // MARK: - Core Task Operations
    
    func loadTasks(for projectId: UUID) async throws {
        // TODO: Fix RetryManager resolution issue
        // try await RetryManager.shared.executeWithRetry(
        //     operation: { [weak self] in
        //         await self?.loadTasksInternal(for: projectId)
        //     },
        //     maxAttempts: 3,
        //     backoffStrategy: BackoffStrategy.exponential(base: 1.0, multiplier: 2.0),
        //     retryCondition: RetryManager.shouldRetry,
        // Simplified without retry logic for now
        //     onAttempt: { attempt, error in
        //         if let error = error {
        //             print("Task loading attempt \(attempt) failed: \(error.localizedDescription)")
        //         }
        //     },
        //     context: "Loading tasks for project \(projectId)"
        // )
    }
    
    private func loadTasksInternal(for projectId: UUID) async throws {
        isLoading = true
        lastError = nil
        defer { isLoading = false }
        
        // In production, fetch from backend
        // For now, filter persisted tasks by project
        let projectTasks = tasks.filter { $0.projectId == projectId }
        
        // If no tasks exist for project, load sample data
        if projectTasks.isEmpty {
            generateSampleTasks(for: projectId)
            try await saveTasks()
        }
    }
    
    func addTask(_ task: LeanVibeTask) async throws {
        lastError = nil
        
        do {
            // Validate task data
            guard !task.title.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
                throw TaskServiceError.invalidTaskData("Task title cannot be empty")
            }
            
            tasks.append(task)
            try await saveTasks()
        } catch {
            lastError = "Failed to add task: \(error.localizedDescription)"
            throw error
        }
    }
    
    func updateTaskStatus(_ taskId: UUID, _ status: TaskStatus) async throws {
        // TODO: Fix RetryManager resolution issue
        // try await RetryManager.shared.executeWithRetry(
        //     operation: { [weak self] in
        //         try await self?.updateTaskStatusInternal(taskId, status)
        //     },
        //     maxAttempts: 2,
        //     backoffStrategy: BackoffStrategy.fixed(1.0),
        //     retryCondition: RetryManager.shouldRetry,
        //     context: "Updating task status to \(status)"
        // )
        try await updateTaskStatusInternal(taskId, status)
    }
    
    private func updateTaskStatusInternal(_ taskId: UUID, _ status: TaskStatus) async throws {
        lastError = nil
        
        guard let index = tasks.firstIndex(where: { $0.id == taskId }) else {
            throw TaskServiceError.taskNotFound
        }
        
        var updatedTask = tasks[index]
        updatedTask.status = status
        updatedTask.updatedAt = Date()
        
        tasks[index] = updatedTask
        try await saveTasks()
    }
    
    func updateTask(_ task: LeanVibeTask) async throws {
        lastError = nil
        
        do {
            guard let index = tasks.firstIndex(where: { $0.id == task.id }) else {
                throw TaskServiceError.taskNotFound
            }
            
            // Validate task data
            guard !task.title.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
                throw TaskServiceError.invalidTaskData("Task title cannot be empty")
            }
            
            var updatedTask = task
            updatedTask.updatedAt = Date()
            
            tasks[index] = updatedTask
            try await saveTasks()
        } catch {
            lastError = "Failed to update task: \(error.localizedDescription)"
            // Error handling will be managed by the global error system
            // GlobalErrorManager.shared.showError(TaskServiceError.updateFailed, context: "Updating task: \(task.title)")
            throw error
        }
    }
    
    func deleteTask(_ taskId: UUID) async throws {
        lastError = nil
        
        do {
            guard let index = tasks.firstIndex(where: { $0.id == taskId }) else {
                throw TaskServiceError.taskNotFound
            }
            
            tasks.remove(at: index)
            try await saveTasks()
        } catch {
            lastError = "Failed to delete task: \(error.localizedDescription)"
            throw error
        }
    }
    
    func moveTask(_ taskId: UUID, to newProjectId: UUID) async throws {
        lastError = nil
        
        do {
            guard let index = tasks.firstIndex(where: { $0.id == taskId }) else {
                throw TaskServiceError.taskNotFound
            }
            
            var movedTask = tasks[index]
            movedTask.projectId = newProjectId
            movedTask.updatedAt = Date()
            
            tasks[index] = movedTask
            try await saveTasks()
        } catch {
            lastError = "Failed to move task: \(error.localizedDescription)"
            throw error
        }
    }
    
    // MARK: - Task Statistics
    
    @MainActor
    func loadTaskStatistics() async {
        await MainActor.run {
            isLoading = true
            lastError = nil
        }
        
        do {
            let response = try await fetchTaskStats()
            let metrics = response.toTaskMetrics()
            
            await MainActor.run {
                self.taskMetrics = metrics
                self.isLoading = false
            }
        } catch {
            await MainActor.run {
                self.lastError = "Failed to load task statistics: \(error.localizedDescription)"
                self.isLoading = false
            }
        }
    }
    
    @MainActor
    private func fetchTaskStats() async throws -> TaskStatsAPIResponse {
        guard let url = URL(string: "\(baseURL)/api/tasks/stats") else {
            throw TaskServiceError.invalidURL
        }
        
        let (data, response) = try await session.data(from: url)
        
        guard let httpResponse = response as? HTTPURLResponse,
              200...299 ~= httpResponse.statusCode else {
            throw TaskServiceError.httpError("HTTP \((response as? HTTPURLResponse)?.statusCode ?? 0)")
        }
        
        return try JSONDecoder().decode(TaskStatsAPIResponse.self, from: data)
    }
    
    // MARK: - Kanban Statistics
    
    @MainActor
    func loadKanbanStatistics() async {
        // Generate mock statistics for now since backend doesn't provide this yet
        let utilization = ColumnUtilization(
            backlogCapacity: 0.7,
            inProgressCapacity: 0.8,
            testingCapacity: 0.6,
            doneGrowthRate: 3.2
        )
        
        let throughput = ThroughputMetrics(
            tasksCompletedToday: 5,
            tasksCompletedThisWeek: 23,
            averageTasksPerDay: 4.2,
            velocityTrend: .increasing
        )
        
        let cycleTime = CycleTimeMetrics(
            averageCycleTime: 4 * 3600, // 4 hours
            averageInProgressTime: 2 * 3600, // 2 hours
            averageTestingTime: 1 * 3600, // 1 hour
            bottleneck: .inProgress
        )
        
        let efficiency = EfficiencyMetrics(
            flowEfficiency: 0.85,
            workInProgressRatio: 0.9,
            predictability: 0.92,
            qualityScore: 0.88
        )
        
        await MainActor.run {
            self.kanbanStatistics = KanbanStatistics(
                columnUtilization: utilization,
                throughput: throughput,
                cycleTime: cycleTime,
                efficiency: efficiency
            )
        }
    }
    
    // MARK: - Performance Monitoring
    
    private func setupPerformanceMonitoring() {
        // Update performance metrics every 30 seconds
        Timer.publish(every: 30, on: .main, in: .common)
            .autoconnect()
            .sink { [weak self] _ in
                Task { @MainActor [weak self] in
                    await self?.updatePerformanceMetrics()
                }
            }
            .store(in: &cancellables)
    }
    
    @MainActor
    private func updatePerformanceMetrics() async {
        // Simulate real performance metrics
        let metrics = PerformanceMetrics(
            cpuUsage: Double.random(in: 0.1...0.7),
            memoryUsage: Int.random(in: 80...120),
            networkLatency: Double.random(in: 0.05...0.15),
            frameRate: Double.random(in: 55...60),
            apiResponseTime: Double.random(in: 0.1...0.5)
        )
        
        await MainActor.run {
            self.performanceMetrics = metrics
        }
    }
    
    // MARK: - System Health
    
    @MainActor
    func checkSystemHealth() async {
        await MainActor.run {
            isLoading = true
        }
        
        do {
            let health = try await fetchSystemHealth()
            
            await MainActor.run {
                self.systemHealth = health
                self.isLoading = false
            }
        } catch {
            await MainActor.run {
                self.lastError = "Failed to check system health: \(error.localizedDescription)"
                self.isLoading = false
            }
        }
    }
    
    @MainActor
    private func fetchSystemHealth() async throws -> SystemHealthStatus {
        // Check multiple services
        async let backendHealth = checkServiceHealth(endpoint: "/health", serviceName: "Backend")
        async let taskHealth = checkServiceHealth(endpoint: "/api/tasks/health", serviceName: "Task Management")
        
        let backend = try await backendHealth
        let tasks = try await taskHealth
        
        // Mock other services for now
        let database = ServiceHealth(
            serviceName: "Database",
            level: .healthy,
            message: "In-memory storage operational",
            responseTime: 0.001
        )
        
        let webSocket = ServiceHealth(
            serviceName: "WebSocket",
            level: .healthy,
            message: "Real-time communication active",
            responseTime: 0.050
        )
        
        return SystemHealthStatus(
            backend: backend,
            database: database,
            webSocket: webSocket,
            tasks: tasks
        )
    }
    
    private func checkServiceHealth(endpoint: String, serviceName: String) async throws -> ServiceHealth {
        guard let url = URL(string: "\(baseURL)\(endpoint)") else {
            return ServiceHealth(
                serviceName: serviceName,
                level: .error,
                message: "Invalid URL configuration"
            )
        }
        
        let startTime = Date()
        
        do {
            let (_, response) = try await session.data(from: url)
            let responseTime = Date().timeIntervalSince(startTime)
            
            if let httpResponse = response as? HTTPURLResponse {
                if 200...299 ~= httpResponse.statusCode {
                    return ServiceHealth(
                        serviceName: serviceName,
                        level: .healthy,
                        message: "Service operational",
                        responseTime: responseTime
                    )
                } else {
                    return ServiceHealth(
                        serviceName: serviceName,
                        level: .warning,
                        message: "HTTP \(httpResponse.statusCode)",
                        responseTime: responseTime
                    )
                }
            }
            
            return ServiceHealth(
                serviceName: serviceName,
                level: .warning,
                message: "Unexpected response"
            )
        } catch {
            return ServiceHealth(
                serviceName: serviceName,
                level: .error,
                message: error.localizedDescription
            )
        }
    }
    
    // MARK: - Auto Refresh
    
    @MainActor
    func startAutoRefresh() {
        Timer.publish(every: 60, on: .main, in: .common)
            .autoconnect()
            .sink { [weak self] _ in
                Task {
                    await self?.loadTaskStatistics()
                    await self?.loadKanbanStatistics()
                    await self?.checkSystemHealth()
                }
            }
            .store(in: &cancellables)
    }
    
    @MainActor
    func stopAutoRefresh() {
        cancellables.removeAll()
    }
    
    // MARK: - Persistence
    
    private func saveTasks() async throws {
        do {
            let data = try jsonEncoder.encode(tasks)
            UserDefaults.standard.set(data, forKey: userDefaultsKey)
            UserDefaults.standard.synchronize()
        } catch {
            throw TaskServiceError.persistenceError("Failed to save tasks: \(error.localizedDescription)")
        }
    }
    
    private func loadPersistedTasks() {
        guard let data = UserDefaults.standard.data(forKey: userDefaultsKey) else {
            // No persisted tasks found, start empty
            return
        }
        
        do {
            tasks = try jsonDecoder.decode([LeanVibeTask].self, from: data)
        } catch {
            // If decoding fails, log error but don't crash
            lastError = "Failed to load saved tasks: \(error.localizedDescription)"
            // Start with empty tasks
            tasks = []
        }
    }
    
    private func generateSampleTasks(for projectId: UUID) {
        let sampleTasks = [
            LeanVibeTask(
                title: "Setup project infrastructure",
                description: "Initialize development environment and CI/CD pipeline",
                status: .done,
                priority: .high,
                projectId: projectId,
                confidence: 0.95,
                clientId: "sample-client"
            ),
            LeanVibeTask(
                title: "Implement user authentication",
                description: "Add secure login and registration functionality",
                status: .inProgress,
                priority: .high,
                projectId: projectId,
                confidence: 0.85,
                clientId: "sample-client"
            ),
            LeanVibeTask(
                title: "Design dashboard UI",
                description: "Create responsive dashboard with data visualization",
                status: .todo,
                priority: .medium,
                projectId: projectId,
                confidence: 0.75,
                clientId: "sample-client"
            ),
            LeanVibeTask(
                title: "Write unit tests",
                description: "Ensure comprehensive test coverage for core functionality",
                status: .todo,
                priority: .medium,
                projectId: projectId,
                confidence: 0.80,
                clientId: "sample-client"
            ),
            LeanVibeTask(
                title: "Performance optimization",
                description: "Optimize loading times and memory usage",
                status: .todo,
                priority: .low,
                projectId: projectId,
                confidence: 0.65,
                clientId: "sample-client"
            )
        ]
        
        tasks.append(contentsOf: sampleTasks)
    }
}

// MARK: - Error Types

enum TaskServiceError: LocalizedError {
    case invalidURL
    case httpError(String)
    case decodingError(Error)
    case taskNotFound
    case invalidTaskData(String)
    case persistenceError(String)
    case updateFailed
    case networkFailure
    case invalidData
    case unauthorized
    
    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid URL configuration"
        case .httpError(let message):
            return "HTTP Error: \(message)"
        case .decodingError(let error):
            return "Failed to decode response: \(error.localizedDescription)"
        case .taskNotFound:
            return "Task not found"
        case .invalidTaskData(let message):
            return message
        case .persistenceError(let message):
            return message
        case .updateFailed:
            return "Failed to update task"
        case .networkFailure:
            return "Network connection failed"
        case .invalidData:
            return "Invalid data received"
        case .unauthorized:
            return "Unauthorized access"
        }
    }
}
