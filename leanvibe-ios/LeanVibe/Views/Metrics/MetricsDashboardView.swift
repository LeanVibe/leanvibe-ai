
import SwiftUI

/// Enhanced Metrics Dashboard with real-time analytics and comprehensive insights
/// NO HARDCODED VALUES - All data comes from MetricsService
@available(iOS 18.0, macOS 14.0, *)
struct MetricsDashboardView: View {
    @StateObject private var metricsService = MetricsService()
    @StateObject private var taskService = TaskService()
    
    let projectId: UUID?
    
    init(projectId: UUID? = nil) {
        self.projectId = projectId
    }

    var body: some View {
        NavigationView {
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    // Header
                    headerSection
                    
                    if metricsService.isLoading {
                        loadingSection
                    } else if let error = metricsService.lastError {
                        errorSection(error)
                    } else {
                        // Main Content
                        VStack(spacing: 20) {
                            // Task Metrics Section
                            if let taskMetrics = metricsService.taskMetrics {
                                taskMetricsSection(taskMetrics)
                            }
                            
                            // Kanban Statistics Section
                            if let kanbanStats = metricsService.kanbanStatistics {
                                kanbanStatisticsSection(kanbanStats)
                            }
                            
                            // Performance Section
                            if let performanceMetrics = metricsService.performanceMetrics {
                                performanceSection(performanceMetrics)
                            }
                            
                            // System Health Section
                            if let systemHealth = metricsService.systemHealth {
                                systemHealthSection(systemHealth)
                            }
                        }
                    }
                }
                .padding()
            }
            .navigationTitle("Analytics")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: {
                        Task {
                            await metricsService.refreshAllMetrics()
                        }
                    }) {
                        Image(systemName: "arrow.clockwise")
                    }
                    .disabled(metricsService.isLoading)
                }
            }
            .task {
                await metricsService.refreshAllMetrics()
                if let projectId = projectId {
                    try? await taskService.loadTasks(for: projectId)
                }
            }
        }
    }
    
    // MARK: - View Sections
    
    private var headerSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Analytics Dashboard")
                .font(.largeTitle)
                .fontWeight(.bold)
            
            Text("Real-time insights and performance metrics")
                .font(.subheadline)
                .foregroundColor(.secondary)
        }
    }
    
    private var loadingSection: some View {
        VStack(spacing: 16) {
            ProgressView()
                .scaleEffect(1.2)
            Text("Loading analytics...")
                .font(.headline)
                .foregroundColor(.secondary)
        }
        .frame(maxWidth: .infinity, minHeight: 200)
    }
    
    private func errorSection(_ error: String) -> some View {
        VStack(spacing: 16) {
            Image(systemName: "exclamationmark.triangle.fill")
                .font(.largeTitle)
                .foregroundColor(.orange)
            
            Text("Failed to Load Analytics")
                .font(.headline)
            
            Text(error)
                .font(.caption)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
            
            Button("Retry") {
                Task {
                    await metricsService.refreshAllMetrics()
                }
            }
            .buttonStyle(.bordered)
        }
        .frame(maxWidth: .infinity, minHeight: 200)
    }
    
    private func taskMetricsSection(_ metrics: TaskMetrics) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Task Performance")
                .font(.title2)
                .fontWeight(.semibold)
            
            // Summary Cards
            HStack(spacing: 12) {
                AnalyticsMetricCard(
                    title: "Total Tasks",
                    value: "\(metrics.totalTasks)",
                    subtitle: "In System",
                    color: .blue,
                    icon: "list.bullet.rectangle"
                )
                
                AnalyticsMetricCard(
                    title: "Completion",
                    value: "\(metrics.completionPercentage)%",
                    subtitle: "Success Rate",
                    color: .green,
                    icon: "checkmark.circle.fill"
                )
            }
            
            HStack(spacing: 12) {
                AnalyticsMetricCard(
                    title: "Avg. Time",
                    value: metrics.averageCompletionTimeFormatted,
                    subtitle: "Per Task",
                    color: .orange,
                    icon: "clock.fill"
                )
                
                AnalyticsMetricCard(
                    title: "Active",
                    value: "\(metrics.byStatus.activeCount)",
                    subtitle: "In Progress",
                    color: .purple,
                    icon: "play.circle.fill"
                )
            }
            
            // Status Breakdown
            StatusBreakdownView(statusCount: metrics.byStatus)
            
            // Priority Distribution
            PriorityDistributionView(priorityCount: metrics.byPriority)
        }
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(12)
    }
    
    private func kanbanStatisticsSection(_ stats: KanbanStatistics) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Kanban Flow")
                .font(.title2)
                .fontWeight(.semibold)
            
            // Flow Metrics
            HStack(spacing: 12) {
                AnalyticsMetricCard(
                    title: "Flow Efficiency",
                    value: "\(stats.efficiency.flowEfficiencyPercentage)%",
                    subtitle: "Work Flow",
                    color: .green,
                    icon: "arrow.right.circle.fill"
                )
                
                AnalyticsMetricCard(
                    title: "Cycle Time",
                    value: stats.cycleTime.averageCycleTimeFormatted,
                    subtitle: "Average",
                    color: .blue,
                    icon: "timer"
                )
            }
            
            HStack(spacing: 12) {
                AnalyticsMetricCard(
                    title: "Velocity",
                    value: stats.throughput.velocityTrend.displayName,
                    subtitle: "This Week",
                    color: Color(stats.throughput.velocityTrend.color),
                    icon: "chart.line.uptrend.xyaxis"
                )
                
                AnalyticsMetricCard(
                    title: "Quality",
                    value: "\(stats.efficiency.qualityScorePercentage)%",
                    subtitle: "Score",
                    color: .indigo,
                    icon: "star.fill"
                )
            }
            
            // Column Utilization
            ColumnUtilizationView(utilization: stats.columnUtilization)
            
            // Throughput Chart
            ThroughputView(throughput: stats.throughput)
        }
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(12)
    }
    
    private func performanceSection(_ performance: PerformanceMetrics) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("System Performance")
                    .font(.title2)
                    .fontWeight(.semibold)
                
                Spacer()
                
                Text("Grade: \(performance.performanceGrade)")
                    .font(.headline)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 6)
                    .background(gradeColor(performance.performanceGrade))
                    .foregroundColor(.white)
                    .cornerRadius(8)
            }
            
            HStack(spacing: 12) {
                AnalyticsMetricCard(
                    title: "CPU Usage",
                    value: "\(performance.cpuPercentage)%",
                    subtitle: "Current",
                    color: .red,
                    icon: "cpu"
                )
                
                AnalyticsMetricCard(
                    title: "Memory",
                    value: "\(performance.memoryUsage)MB",
                    subtitle: "Used",
                    color: .orange,
                    icon: "memorychip"
                )
            }
            
            HStack(spacing: 12) {
                AnalyticsMetricCard(
                    title: "Network",
                    value: String(format: "%.0fms", performance.networkLatency * 1000),
                    subtitle: "Latency",
                    color: .blue,
                    icon: "wifi"
                )
                
                AnalyticsMetricCard(
                    title: "Frame Rate",
                    value: String(format: "%.0f FPS", performance.frameRate),
                    subtitle: "Rendering",
                    color: .green,
                    icon: "speedometer"
                )
            }
        }
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(12)
    }
    
    private func systemHealthSection(_ health: SystemHealthStatus) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("System Health")
                    .font(.title2)
                    .fontWeight(.semibold)
                
                Spacer()
                
                HealthStatusBadge(level: health.overall)
            }
            
            VStack(spacing: 8) {
                MetricsServiceHealthRow(service: health.backend)
                MetricsServiceHealthRow(service: health.database)
                MetricsServiceHealthRow(service: health.webSocket)
                MetricsServiceHealthRow(service: health.tasks)
            }
            
            Text("Last checked: \(formatDate(health.lastChecked))")
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(12)
    }
    
    // MARK: - Helper Methods
    
    private func gradeColor(_ grade: String) -> Color {
        switch grade {
        case "A": return .green
        case "B": return .blue
        case "C": return .orange
        case "D": return .red
        default: return .red
        }
    }
    
    private func formatDate(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateStyle = .none
        formatter.timeStyle = .short
        return formatter.string(from: date)
    }
}

// MARK: - Supporting Views

@available(iOS 18.0, macOS 14.0, *)
struct AnalyticsMetricCard: View {
    let title: String
    let value: String
    let subtitle: String
    let color: Color
    let icon: String
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: icon)
                    .foregroundColor(color)
                    .font(.title2)
                
                Spacer()
            }
            
            Text(value)
                .font(.title2)
                .fontWeight(.bold)
            
            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(.caption)
                    .fontWeight(.medium)
                
                Text(subtitle)
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
        }
        .padding()
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color(.systemBackground))
        .cornerRadius(8)
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct StatusBreakdownView: View {
    let statusCount: TaskStatusCount
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Status Distribution")
                .font(.subheadline)
                .fontWeight(.medium)
            
            HStack(spacing: 4) {
                ForEach(statusItems, id: \.name) { item in
                    VStack(spacing: 4) {
                        Rectangle()
                            .fill(item.color)
                            .frame(height: 6)
                            .frame(width: CGFloat(item.count) / CGFloat(statusCount.total) * 200)
                        
                        Text("\(item.count)")
                            .font(.caption2)
                            .fontWeight(.medium)
                        
                        Text(item.name)
                            .font(.caption2)
                            .foregroundColor(.secondary)
                    }
                }
            }
        }
    }
    
    private var statusItems: [(name: String, count: Int, color: Color)] {
        [
            ("Backlog", statusCount.backlog, .gray),
            ("Progress", statusCount.inProgress, .blue),
            ("Testing", statusCount.testing, .orange),
            ("Done", statusCount.done, .green)
        ]
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct PriorityDistributionView: View {
    let priorityCount: TaskPriorityCount
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Priority Distribution")
                .font(.subheadline)
                .fontWeight(.medium)
            
            LazyVGrid(columns: Array(repeating: GridItem(.flexible()), count: 4), spacing: 8) {
                ForEach(priorityItems, id: \.name) { item in
                    VStack(spacing: 4) {
                        Circle()
                            .fill(item.color)
                            .frame(width: 20, height: 20)
                            .overlay(
                                Text("\(item.count)")
                                    .font(.caption2)
                                    .fontWeight(.bold)
                                    .foregroundColor(.white)
                            )
                        
                        Text(item.name)
                            .font(.caption2)
                            .foregroundColor(.secondary)
                    }
                }
            }
        }
    }
    
    private var priorityItems: [(name: String, count: Int, color: Color)] {
        [
            ("Low", priorityCount.low, .green),
            ("Med", priorityCount.medium, .blue),
            ("High", priorityCount.high, .orange),
            ("Urgent", priorityCount.urgent, .red)
        ]
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct ColumnUtilizationView: View {
    let utilization: ColumnUtilization
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Column Utilization")
                .font(.subheadline)
                .fontWeight(.medium)
            
            VStack(spacing: 6) {
                UtilizationBar(
                    title: "In Progress",
                    percentage: utilization.inProgressUtilizationPercentage,
                    isAtCapacity: utilization.isInProgressAtCapacity
                )
                
                UtilizationBar(
                    title: "Testing",
                    percentage: utilization.testingUtilizationPercentage,
                    isAtCapacity: utilization.isTestingAtCapacity
                )
            }
        }
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct UtilizationBar: View {
    let title: String
    let percentage: Int
    let isAtCapacity: Bool
    
    var body: some View {
        HStack {
            Text(title)
                .font(.caption)
                .frame(width: 80, alignment: .leading)
            
            GeometryReader { geometry in
                ZStack(alignment: .leading) {
                    Rectangle()
                        .fill(Color(.systemGray5))
                        .frame(height: 8)
                        .cornerRadius(4)
                    
                    Rectangle()
                        .fill(isAtCapacity ? .red : .blue)
                        .frame(width: geometry.size.width * CGFloat(percentage) / 100, height: 8)
                        .cornerRadius(4)
                }
            }
            .frame(height: 8)
            
            Text("\(percentage)%")
                .font(.caption)
                .fontWeight(.medium)
                .frame(width: 40, alignment: .trailing)
        }
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct ThroughputView: View {
    let throughput: ThroughputMetrics
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Throughput")
                .font(.subheadline)
                .fontWeight(.medium)
            
            HStack(spacing: 16) {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Today")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    Text("\(throughput.tasksCompletedToday)")
                        .font(.title3)
                        .fontWeight(.semibold)
                }
                
                VStack(alignment: .leading, spacing: 4) {
                    Text("This Week")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    Text("\(throughput.tasksCompletedThisWeek)")
                        .font(.title3)
                        .fontWeight(.semibold)
                }
                
                VStack(alignment: .leading, spacing: 4) {
                    Text("Daily Avg")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    Text(String(format: "%.1f", throughput.averageTasksPerDay))
                        .font(.title3)
                        .fontWeight(.semibold)
                }
                
                Spacer()
            }
        }
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct HealthStatusBadge: View {
    let level: HealthLevel
    
    var body: some View {
        HStack(spacing: 6) {
            Image(systemName: level.iconName)
                .foregroundColor(Color(level.color))
            
            Text(level.displayName)
                .font(.caption)
                .fontWeight(.medium)
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(Color(level.color).opacity(0.2))
        .cornerRadius(8)
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct MetricsServiceHealthRow: View {
    let service: ServiceHealth
    
    var body: some View {
        HStack {
            Image(systemName: service.level.iconName)
                .foregroundColor(Color(service.level.color))
                .frame(width: 20)
            
            VStack(alignment: .leading, spacing: 2) {
                Text(service.serviceName)
                    .font(.subheadline)
                    .fontWeight(.medium)
                
                Text(service.message)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
            
            if let responseTime = service.responseTime {
                Text(String(format: "%.0fms", responseTime * 1000))
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .padding(.vertical, 4)
    }
}
