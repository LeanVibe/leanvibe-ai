import Foundation
import Combine
import SwiftUI

// MARK: - Task Service for Backend Integration

@available(macOS 10.15, iOS 13.0, *)
@MainActor
class TaskService: ObservableObject {
    @Published var tasks: [LeenVibeTask] = []
    @Published var taskMetrics: TaskMetrics?
    @Published var kanbanStatistics: KanbanStatistics?
    @Published var performanceMetrics: PerformanceMetrics?
    @Published var systemHealth: SystemHealthStatus?
    @Published var isLoading = false
    @Published var lastError: String?
    
    private let baseURL: String
    private var cancellables = Set<AnyCancellable>()
    private let session = URLSession.shared
    
    init(baseURL: String = "http://localhost:8002") {
        self.baseURL = baseURL
        setupPerformanceMonitoring()
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
}

// MARK: - Error Types

enum TaskServiceError: LocalizedError {
    case invalidURL
    case httpError(String)
    case decodingError(Error)
    
    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid URL configuration"
        case .httpError(let message):
            return "HTTP Error: \(message)"
        case .decodingError(let error):
            return "Failed to decode response: \(error.localizedDescription)"
        }
    }
}
