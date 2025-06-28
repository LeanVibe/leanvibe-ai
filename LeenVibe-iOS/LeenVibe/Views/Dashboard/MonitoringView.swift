import SwiftUI

struct MonitoringView: View {
    @ObservedObject var projectManager: ProjectManager
    @ObservedObject var webSocketService: WebSocketService
    @StateObject private var taskService = TaskService()
    @State private var selectedTimeRange: TimeRange = .last24Hours
    @State private var showingSessionDetails = false
    @State private var selectedSession: ProjectSession?
    @State private var selectedDashboardTab: DashboardTab = .overview
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 20) {
                    // Dashboard tab selector
                    dashboardTabSelector
                    
                    // Time range selector
                    timeRangeSelector
                    
                    // Content based on selected tab
                    Group {
                        switch selectedDashboardTab {
                        case .overview:
                            overviewContent
                        case .tasks:
                            taskManagementContent
                        case .performance:
                            performanceContent
                        case .system:
                            systemHealthContent
                        }
                    }
                }
                .padding()
            }
            .navigationTitle("Monitoring")
            .navigationBarTitleDisplayMode(.large)
            .refreshable {
                await refreshData()
            }
            .onAppear {
                Task {
                    await loadDashboardData()
                    taskService.startAutoRefresh()
                }
            }
            .onDisappear {
                taskService.stopAutoRefresh()
            }
        }
        .sheet(item: $selectedSession) { session in
            SessionDetailView(session: session)
        }
    }
    
    private var timeRangeSelector: some View {
        Picker("Time Range", selection: $selectedTimeRange) {
            ForEach(TimeRange.allCases, id: \.self) { range in
                Text(range.displayName).tag(range)
            }
        }
        .pickerStyle(.segmented)
    }
    
    private var connectionStatusCard: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "antenna.radiowaves.left.and.right")
                    .foregroundColor(.blue)
                Text("Connection Status")
                    .font(.headline)
                Spacer()
                Circle()
                    .fill(webSocketService.isConnected ? .green : .red)
                    .frame(width: 12, height: 12)
            }
            
            Divider()
            
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Text("Status:")
                        .foregroundColor(.secondary)
                    Spacer()
                    Text(webSocketService.connectionStatus)
                        .fontWeight(.medium)
                }
                
                if let connectionInfo = webSocketService.getCurrentConnectionInfo() {
                    HStack {
                        Text("Server:")
                            .foregroundColor(.secondary)
                        Spacer()
                        Text(connectionInfo)
                            .fontWeight(.medium)
                    }
                }
                
                HStack {
                    Text("Messages:")
                        .foregroundColor(.secondary)
                    Spacer()
                    Text("\(webSocketService.messages.count)")
                        .fontWeight(.medium)
                }
                
                if let error = webSocketService.lastError {
                    HStack {
                        Image(systemName: "exclamationmark.triangle.fill")
                            .foregroundColor(.orange)
                        Text(error)
                            .font(.caption)
                            .foregroundColor(.secondary)
                            .lineLimit(2)
                    }
                }
            }
        }
        .padding()
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 12))
    }
    
    private var activeSessionsCard: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "clock.arrow.circlepath")
                    .foregroundColor(.green)
                Text("Active Sessions")
                    .font(.headline)
                Spacer()
                Text("\(projectManager.activeSessions.count)")
                    .font(.caption)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(.green.opacity(0.2), in: Capsule())
            }
            
            Divider()
            
            if projectManager.activeSessions.isEmpty {
                Text("No active sessions")
                    .foregroundColor(.secondary)
                    .frame(maxWidth: .infinity, alignment: .center)
                    .padding(.vertical)
            } else {
                LazyVStack(spacing: 8) {
                    ForEach(projectManager.activeSessions.prefix(3)) { session in
                        SessionRowView(session: session) {
                            selectedSession = session
                            showingSessionDetails = true
                        }
                    }
                    
                    if projectManager.activeSessions.count > 3 {
                        Button("View All (\(projectManager.activeSessions.count))") {
                            // Show all sessions view
                        }
                        .font(.caption)
                        .foregroundColor(.blue)
                    }
                }
            }
        }
        .padding()
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 12))
    }
    
    private var projectHealthCard: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "heart.fill")
                    .foregroundColor(.pink)
                Text("Project Health")
                    .font(.headline)
                Spacer()
            }
            
            Divider()
            
            if projectManager.projects.isEmpty {
                Text("No projects available")
                    .foregroundColor(.secondary)
                    .frame(maxWidth: .infinity, alignment: .center)
                    .padding(.vertical)
            } else {
                LazyVGrid(columns: [
                    GridItem(.flexible()),
                    GridItem(.flexible())
                ], spacing: 12) {
                    ForEach(projectManager.projects.prefix(4)) { project in
                        ProjectHealthView(project: project)
                    }
                }
            }
        }
        .padding()
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 12))
    }
    
    private var performanceMetricsCard: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "speedometer")
                    .foregroundColor(.orange)
                Text("Performance Metrics")
                    .font(.headline)
                Spacer()
            }
            
            Divider()
            
            LazyVGrid(columns: [
                GridItem(.flexible()),
                GridItem(.flexible())
            ], spacing: 16) {
                MetricView(
                    title: "Avg Response Time",
                    value: "1.2s",
                    trend: .down,
                    color: .green
                )
                
                MetricView(
                    title: "Memory Usage",
                    value: "89MB",
                    trend: .up,
                    color: .orange
                )
                
                MetricView(
                    title: "Active Connections",
                    value: "\(webSocketService.isConnected ? 1 : 0)",
                    trend: .stable,
                    color: .blue
                )
                
                MetricView(
                    title: "Success Rate",
                    value: "98.5%",
                    trend: .up,
                    color: .green
                )
            }
        }
        .padding()
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 12))
    }
    
    // MARK: - Task Management Cards
    
    private func taskMetricsOverviewCard(_ metrics: TaskMetrics) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "list.bullet.rectangle")
                    .foregroundColor(.blue)
                Text("Task Overview")
                    .font(.headline)
                Spacer()
                Text("\(metrics.completionPercentage)%")
                    .font(.caption)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(.blue.opacity(0.2), in: Capsule())
            }
            
            Divider()
            
            LazyVGrid(columns: [
                GridItem(.flexible()),
                GridItem(.flexible())
            ], spacing: 16) {
                MetricView(
                    title: "Total Tasks",
                    value: "\(metrics.totalTasks)",
                    trend: .stable,
                    color: .blue
                )
                
                MetricView(
                    title: "Completion Rate",
                    value: "\(metrics.completionPercentage)%",
                    trend: .up,
                    color: .green
                )
                
                MetricView(
                    title: "Active Tasks",
                    value: "\(metrics.byStatus.activeCount)",
                    trend: .stable,
                    color: .orange
                )
                
                MetricView(
                    title: "Avg Time",
                    value: metrics.averageCompletionTimeFormatted,
                    trend: .down,
                    color: .purple
                )
            }
        }
        .padding()
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 12))
    }
    
    private func taskMetricsDetailCard(_ metrics: TaskMetrics) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "chart.bar.fill")
                    .foregroundColor(.blue)
                Text("Task Analytics")
                    .font(.headline)
                Spacer()
                Text("Updated \(metrics.lastUpdated, style: .time)")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Divider()
            
            VStack(alignment: .leading, spacing: 12) {
                Text("Status: \(metrics.byStatus.backlog) Backlog, \(metrics.byStatus.inProgress) In Progress, \(metrics.byStatus.testing) Testing, \(metrics.byStatus.done) Done")
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                Text("Priority: \(metrics.byPriority.low) Low, \(metrics.byPriority.medium) Medium, \(metrics.byPriority.high) High, \(metrics.byPriority.critical) Critical")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .padding()
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 12))
    }
    
    private func kanbanStatisticsCard(_ stats: KanbanStatistics) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "rectangle.3.group")
                    .foregroundColor(.green)
                Text("Kanban Analytics")
                    .font(.headline)
                Spacer()
                Text("\(stats.efficiency.healthScorePercentage)%")
                    .font(.caption)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(Color(stats.efficiency.healthScoreColor).opacity(0.2), in: Capsule())
            }
            
            Divider()
            
            LazyVGrid(columns: [
                GridItem(.flexible()),
                GridItem(.flexible())
            ], spacing: 16) {
                MetricView(
                    title: "Throughput",
                    value: "\(stats.throughput.tasksCompletedToday)",
                    trend: .up,
                    color: .green
                )
                
                MetricView(
                    title: "Cycle Time",
                    value: stats.cycleTime.averageCycleTimeFormatted,
                    trend: .down,
                    color: .blue
                )
                
                MetricView(
                    title: "Flow Efficiency",
                    value: "\(stats.efficiency.flowEfficiencyPercentage)%",
                    trend: .up,
                    color: .purple
                )
                
                MetricView(
                    title: "WIP Utilization",
                    value: "\(stats.columnUtilization.inProgressUtilizationPercentage)%",
                    trend: .stable,
                    color: .orange
                )
            }
        }
        .padding()
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 12))
    }
    
    private func taskDistributionCard(_ metrics: TaskMetrics) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "chart.pie.fill")
                    .foregroundColor(.purple)
                Text("Task Distribution")
                    .font(.headline)
                Spacer()
            }
            
            Divider()
            
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Text("Backlog: \(metrics.byStatus.backlog)")
                        .font(.caption)
                    Spacer()
                    Text("In Progress: \(metrics.byStatus.inProgress)")
                        .font(.caption)
                }
                
                HStack {
                    Text("Testing: \(metrics.byStatus.testing)")
                        .font(.caption)
                    Spacer()
                    Text("Done: \(metrics.byStatus.done)")
                        .font(.caption)
                }
                
                if metrics.byPriority.urgentCount > 0 {
                    HStack {
                        Image(systemName: "exclamationmark.triangle.fill")
                            .foregroundColor(.red)
                        Text("\(metrics.byPriority.urgentCount) urgent tasks")
                            .font(.caption)
                            .foregroundColor(.red)
                        Spacer()
                    }
                }
            }
        }
        .padding()
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 12))
    }
    
    private func realTimePerformanceCard(_ performance: PerformanceMetrics) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "gauge.badge.plus")
                    .foregroundColor(.green)
                Text("Real-time Performance")
                    .font(.headline)
                Spacer()
                Text(performance.performanceGrade)
                    .font(.caption)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(performance.isPerformanceGood ? .green.opacity(0.2) : .red.opacity(0.2), in: Capsule())
            }
            
            Divider()
            
            LazyVGrid(columns: [
                GridItem(.flexible()),
                GridItem(.flexible())
            ], spacing: 16) {
                MetricView(
                    title: "CPU Usage",
                    value: "\(performance.cpuPercentage)%",
                    trend: performance.cpuUsage < 0.5 ? .down : .up,
                    color: performance.cpuUsage < 0.7 ? .green : .orange
                )
                
                MetricView(
                    title: "Memory",
                    value: "\(performance.memoryUsage)MB",
                    trend: .stable,
                    color: performance.memoryUsage < 100 ? .green : .orange
                )
                
                MetricView(
                    title: "Frame Rate",
                    value: "\(Int(performance.frameRate))fps",
                    trend: performance.frameRate >= 55 ? .up : .down,
                    color: performance.frameRate >= 55 ? .green : .red
                )
                
                MetricView(
                    title: "API Latency",
                    value: "\(Int(performance.networkLatency * 1000))ms",
                    trend: performance.networkLatency < 0.1 ? .down : .up,
                    color: performance.networkLatency < 0.1 ? .green : .orange
                )
            }
        }
        .padding()
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 12))
    }
    
    private var apiPerformanceCard: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "network")
                    .foregroundColor(.blue)
                Text("API Performance")
                    .font(.headline)
                Spacer()
            }
            
            Divider()
            
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Text("/api/tasks/stats")
                        .font(.caption)
                        .fontFamily(.monospaced)
                    Spacer()
                    Text("120ms")
                        .font(.caption)
                        .foregroundColor(.green)
                }
                
                HStack {
                    Text("/api/kanban/board")
                        .font(.caption)
                        .fontFamily(.monospaced)
                    Spacer()
                    Text("95ms")
                        .font(.caption)
                        .foregroundColor(.green)
                }
                
                HStack {
                    Text("/health")
                        .font(.caption)
                        .fontFamily(.monospaced)
                    Spacer()
                    Text("45ms")
                        .font(.caption)
                        .foregroundColor(.green)
                }
            }
        }
        .padding()
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 12))
    }
    
    private func systemHealthCard(_ health: SystemHealthStatus) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: health.overall.iconName)
                    .foregroundColor(Color(health.overall.color))
                Text("System Health")
                    .font(.headline)
                Spacer()
                Text(health.overall.displayName)
                    .font(.caption)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(Color(health.overall.color).opacity(0.2), in: Capsule())
            }
            
            Divider()
            
            VStack(spacing: 8) {
                HStack {
                    Text(health.backend.serviceName)
                        .font(.caption)
                    Spacer()
                    Image(systemName: health.backend.level.iconName)
                        .foregroundColor(Color(health.backend.level.color))
                        .font(.caption)
                    Text(health.backend.level.displayName)
                        .font(.caption)
                        .foregroundColor(Color(health.backend.level.color))
                }
                
                HStack {
                    Text(health.tasks.serviceName)
                        .font(.caption)
                    Spacer()
                    Image(systemName: health.tasks.level.iconName)
                        .foregroundColor(Color(health.tasks.level.color))
                        .font(.caption)
                    Text(health.tasks.level.displayName)
                        .font(.caption)
                        .foregroundColor(Color(health.tasks.level.color))
                }
                
                HStack {
                    Text(health.webSocket.serviceName)
                        .font(.caption)
                    Spacer()
                    Image(systemName: health.webSocket.level.iconName)
                        .foregroundColor(Color(health.webSocket.level.color))
                        .font(.caption)
                    Text(health.webSocket.level.displayName)
                        .font(.caption)
                        .foregroundColor(Color(health.webSocket.level.color))
                }
            }
        }
        .padding()
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 12))
    }
    
    private func serviceDetailsCard(_ health: SystemHealthStatus) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "info.circle.fill")
                    .foregroundColor(.blue)
                Text("Service Details")
                    .font(.headline)
                Spacer()
                Text("Last checked: \(health.lastChecked, style: .time)")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Divider()
            
            VStack(spacing: 8) {
                VStack(alignment: .leading, spacing: 4) {
                    Text(health.backend.serviceName)
                        .font(.caption)
                        .fontWeight(.medium)
                    Text(health.backend.message)
                        .font(.caption2)
                        .foregroundColor(.secondary)
                    if let responseTime = health.backend.responseTime {
                        Text("Response: \(Int(responseTime * 1000))ms")
                            .font(.caption2)
                            .foregroundColor(.secondary)
                    }
                }
                
                Divider()
                
                VStack(alignment: .leading, spacing: 4) {
                    Text(health.tasks.serviceName)
                        .font(.caption)
                        .fontWeight(.medium)
                    Text(health.tasks.message)
                        .font(.caption2)
                        .foregroundColor(.secondary)
                    if let responseTime = health.tasks.responseTime {
                        Text("Response: \(Int(responseTime * 1000))ms")
                            .font(.caption2)
                            .foregroundColor(.secondary)
                    }
                }
            }
        }
        .padding()
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 12))
    }
    
    private var connectionDiagnosticsCard: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "stethoscope")
                    .foregroundColor(.purple)
                Text("Connection Diagnostics")
                    .font(.headline)
                Spacer()
            }
            
            Divider()
            
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Text("Base URL:")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    Spacer()
                    Text("localhost:8002")
                        .font(.caption)
                        .fontFamily(.monospaced)
                }
                
                HStack {
                    Text("Connection Status:")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    Spacer()
                    Text(webSocketService.connectionStatus)
                        .font(.caption)
                        .foregroundColor(webSocketService.isConnected ? .green : .red)
                }
                
                HStack {
                    Text("Last Error:")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    Spacer()
                    Text(taskService.lastError ?? "None")
                        .font(.caption)
                        .foregroundColor(taskService.lastError == nil ? .green : .orange)
                        .lineLimit(1)
                }
                
                HStack {
                    Text("Auto Refresh:")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    Spacer()
                    Text("Enabled")
                        .font(.caption)
                        .foregroundColor(.blue)
                }
            }
        }
        .padding()
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 12))
    }
    
    private func refreshData() async {
        await projectManager.refreshProjects()
        await loadDashboardData()
    }
    
    private func loadDashboardData() async {
        await taskService.loadTaskStatistics()
        await taskService.loadKanbanStatistics()
        await taskService.checkSystemHealth()
    }
    
    // MARK: - Dashboard Tab Selector
    
    private var dashboardTabSelector: some View {
        Picker("Dashboard View", selection: $selectedDashboardTab) {
            ForEach(DashboardTab.allCases, id: \.self) { tab in
                Text(tab.displayName).tag(tab)
            }
        }
        .pickerStyle(.segmented)
    }
    
    // MARK: - Dashboard Content Sections
    
    private var overviewContent: some View {
        VStack(spacing: 20) {
            // Connection status card
            connectionStatusCard
            
            // Task metrics overview
            if let metrics = taskService.taskMetrics {
                taskMetricsOverviewCard(metrics)
            }
            
            // Active sessions
            activeSessionsCard
            
            // Project health overview
            projectHealthCard
        }
    }
    
    private var taskManagementContent: some View {
        VStack(spacing: 20) {
            // Task statistics
            if let metrics = taskService.taskMetrics {
                taskMetricsDetailCard(metrics)
            }
            
            // Kanban statistics
            if let kanbanStats = taskService.kanbanStatistics {
                kanbanStatisticsCard(kanbanStats)
            }
            
            // Task distribution charts
            if let metrics = taskService.taskMetrics {
                taskDistributionCard(metrics)
            }
        }
    }
    
    private var performanceContent: some View {
        VStack(spacing: 20) {
            // Performance metrics
            performanceMetricsCard
            
            // Real-time performance monitoring
            if let performance = taskService.performanceMetrics {
                realTimePerformanceCard(performance)
            }
            
            // API response times
            apiPerformanceCard
        }
    }
    
    private var systemHealthContent: some View {
        VStack(spacing: 20) {
            // System health overview
            if let health = taskService.systemHealth {
                systemHealthCard(health)
            }
            
            // Service details
            if let health = taskService.systemHealth {
                serviceDetailsCard(health)
            }
            
            // Connection diagnostics
            connectionDiagnosticsCard
        }
    }
}

struct SessionRowView: View {
    let session: ProjectSession
    let onTap: () -> Void
    
    var body: some View {
        Button(action: onTap) {
            HStack {
                VStack(alignment: .leading, spacing: 2) {
                    Text(session.projectId)
                        .font(.caption)
                        .fontWeight(.medium)
                    Text("Client: \(session.clientId)")
                        .font(.caption2)
                        .foregroundColor(.secondary)
                }
                
                Spacer()
                
                VStack(alignment: .trailing, spacing: 2) {
                    Text(session.startTime, style: .time)
                        .font(.caption)
                    if let endTime = session.endTime {
                        Text(endTime, style: .time)
                            .font(.caption2)
                            .foregroundColor(.secondary)
                    } else {
                        Text("Active")
                            .font(.caption2)
                            .foregroundColor(.green)
                    }
                }
            }
            .padding(.vertical, 4)
        }
        .buttonStyle(.plain)
    }
}

struct ProjectHealthView: View {
    let project: Project
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: project.language.icon)
                    .foregroundColor(Color(project.language.color))
                    .font(.caption)
                
                Text(project.name)
                    .font(.caption)
                    .fontWeight(.medium)
                    .lineLimit(1)
            }
            
            VStack(alignment: .leading, spacing: 4) {
                HStack {
                    Text("Health")
                        .font(.caption2)
                        .foregroundColor(.secondary)
                    Spacer()
                    Text(project.metrics.healthDescription)
                        .font(.caption2)
                        .fontWeight(.medium)
                        .foregroundColor(Color(project.metrics.healthColor))
                }
                
                ProgressView(value: project.metrics.healthScore)
                    .progressViewStyle(LinearProgressViewStyle(tint: Color(project.metrics.healthColor)))
                    .scaleEffect(y: 0.5)
            }
        }
        .padding(8)
        .background(.gray.opacity(0.1), in: RoundedRectangle(cornerRadius: 8))
    }
}

struct MetricView: View {
    let title: String
    let value: String
    let trend: TrendDirection
    let color: Color
    
    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text(title)
                    .font(.caption)
                    .foregroundColor(.secondary)
                Spacer()
                Image(systemName: trend.icon)
                    .font(.caption2)
                    .foregroundColor(trend.color)
            }
            
            Text(value)
                .font(.title3)
                .fontWeight(.semibold)
                .foregroundColor(color)
        }
        .padding(8)
        .background(.gray.opacity(0.1), in: RoundedRectangle(cornerRadius: 8))
    }
}

struct SessionDetailView: View {
    let session: ProjectSession
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    Text("Session Details")
                        .font(.headline)
                    
                    VStack(alignment: .leading, spacing: 8) {
                        DetailRow(label: "Project ID", value: session.projectId)
                        DetailRow(label: "Client ID", value: session.clientId)
                        DetailRow(label: "Start Time", value: session.startTime.formatted())
                        if let endTime = session.endTime {
                            DetailRow(label: "End Time", value: endTime.formatted())
                        }
                        DetailRow(label: "Duration", value: String(format: "%.1fs", session.duration))
                    }
                }
                .padding()
            }
            .navigationTitle("Session")
            .navigationBarTitleDisplayMode(.inline)
        }
    }
}

struct DetailRow: View {
    let label: String
    let value: String
    
    var body: some View {
        HStack {
            Text(label)
                .foregroundColor(.secondary)
            Spacer()
            Text(value)
                .fontWeight(.medium)
        }
    }
}

enum TimeRange: CaseIterable {
    case last1Hour
    case last24Hours
    case lastWeek
    case lastMonth
    
    var displayName: String {
        switch self {
        case .last1Hour: return "1H"
        case .last24Hours: return "24H"
        case .lastWeek: return "1W"
        case .lastMonth: return "1M"
        }
    }
}

enum TrendDirection {
    case up
    case down
    case stable
    
    var icon: String {
        switch self {
        case .up: return "arrow.up"
        case .down: return "arrow.down"
        case .stable: return "minus"
        }
    }
    
    var color: Color {
        switch self {
        case .up: return .green
        case .down: return .red
        case .stable: return .gray
        }
    }
}

enum DashboardTab: CaseIterable {
    case overview
    case tasks
    case performance
    case system
    
    var displayName: String {
        switch self {
        case .overview: return "Overview"
        case .tasks: return "Tasks"
        case .performance: return "Performance"
        case .system: return "System"
        }
    }
}

#Preview {
    MonitoringView(
        projectManager: ProjectManager(),
        webSocketService: WebSocketService()
    )
}