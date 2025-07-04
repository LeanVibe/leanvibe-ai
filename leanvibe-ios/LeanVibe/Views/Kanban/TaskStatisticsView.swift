import SwiftUI
import Charts

@available(iOS 18.0, macOS 14.0, *)
@MainActor
struct TaskStatisticsView: View {
    @Environment(\.dismiss) private var dismiss
    @ObservedObject var taskService: TaskService
    @State private var isLoading = true
    
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                if isLoading {
                    ProgressView("Loading statistics...")
                        .frame(maxWidth: .infinity, alignment: .center)
                } else {
                    statisticsContent
                }
            }
            .padding()
        }
        .navigationTitle("Task Statistics")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .navigationBarTrailing) {
                Button("Done") {
                    dismiss()
                }
            }
        }
        .task {
            await loadStatistics()
        }
    }
    
    @ViewBuilder
    private var statisticsContent: some View {
        // Task Overview
        VStack(alignment: .leading, spacing: 16) {
            Text("Task Overview")
                .font(.title2)
                .fontWeight(.bold)
            
            LazyVGrid(columns: Array(repeating: GridItem(.flexible()), count: 2), spacing: 16) {
                if let metrics = taskService.taskMetrics {
                    StatCard(
                        title: "Total Tasks",
                        value: "\(metrics.totalTasks)",
                        icon: "list.number",
                        color: .blue
                    )
                    
                    StatCard(
                        title: "Completion Rate",
                        value: "\(metrics.completionPercentage)%",
                        icon: "chart.bar.fill",
                        color: .green
                    )
                    
                    StatCard(
                        title: "In Progress",
                        value: "\(metrics.byStatus.inProgress)",
                        icon: "arrow.clockwise",
                        color: .orange
                    )
                    
                    StatCard(
                        title: "Done",
                        value: "\(metrics.byStatus.done)",
                        icon: "checkmark.circle.fill",
                        color: .green
                    )
                } else {
                    ForEach(0..<4, id: \.self) { _ in
                        StatCard(
                            title: "Loading...",
                            value: "-",
                            icon: "ellipsis",
                            color: .gray
                        )
                    }
                }
            }
        }
        
        // Kanban Statistics
        if let kanbanStats = taskService.kanbanStatistics {
            VStack(alignment: .leading, spacing: 16) {
                Text("Kanban Flow")
                    .font(.title2)
                    .fontWeight(.bold)
                
                VStack(spacing: 12) {
                    // Throughput
                    HStack {
                        Text("Tasks Completed Today:")
                            .font(.subheadline)
                        Spacer()
                        Text("\(kanbanStats.throughput.tasksCompletedToday)")
                            .font(.headline)
                            .foregroundColor(.green)
                    }
                    
                    HStack {
                        Text("Tasks Completed This Week:")
                            .font(.subheadline)
                        Spacer()
                        Text("\(kanbanStats.throughput.tasksCompletedThisWeek)")
                            .font(.headline)
                            .foregroundColor(.blue)
                    }
                    
                    HStack {
                        Text("Velocity Trend:")
                            .font(.subheadline)
                        Spacer()
                        Text(kanbanStats.throughput.velocityTrend.displayName)
                            .font(.headline)
                            .foregroundColor(Color(kanbanStats.throughput.velocityTrend.color))
                    }
                }
                .padding()
                .background(Color.gray.opacity(0.1))
                .cornerRadius(8)
            }
        }
        
        // Performance Metrics
        if let perfMetrics = taskService.performanceMetrics {
            VStack(alignment: .leading, spacing: 16) {
                Text("Performance")
                    .font(.title2)
                    .fontWeight(.bold)
                
                LazyVGrid(columns: Array(repeating: GridItem(.flexible()), count: 2), spacing: 16) {
                    StatCard(
                        title: "CPU Usage",
                        value: "\(perfMetrics.cpuPercentage)%",
                        icon: "cpu",
                        color: perfMetrics.cpuUsage > 0.7 ? .red : .green
                    )
                    
                    StatCard(
                        title: "Memory",
                        value: "\(perfMetrics.memoryUsage)MB",
                        icon: "memorychip",
                        color: perfMetrics.memoryUsage > 100 ? .orange : .green
                    )
                    
                    StatCard(
                        title: "API Response",
                        value: "\(Int(perfMetrics.apiResponseTime * 1000))ms",
                        icon: "network",
                        color: perfMetrics.apiResponseTime > 1.0 ? .red : .green
                    )
                    
                    StatCard(
                        title: "Grade",
                        value: perfMetrics.performanceGrade,
                        icon: "star.fill",
                        color: perfMetrics.isPerformanceGood ? .green : .orange
                    )
                }
            }
        }
    }
    
    private func loadStatistics() async {
        isLoading = true
        
        // Load all statistics
        await taskService.loadTaskStatistics()
        await taskService.loadKanbanStatistics()
        await taskService.updatePerformanceMetrics()
        
        isLoading = false
    }
}

struct StatCard: View {
    let title: String
    let value: String
    let icon: String
    let color: Color
    
    var body: some View {
        VStack(spacing: 8) {
            HStack {
                Image(systemName: icon)
                    .foregroundColor(color)
                
                Spacer()
                
                Text(value)
                    .font(.title2)
                    .fontWeight(.bold)
                    .foregroundColor(color)
            }
            
            Text(title)
                .font(.caption)
                .foregroundColor(.secondary)
                .frame(maxWidth: .infinity, alignment: .leading)
        }
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 8)
                .fill(color.opacity(0.1))
        )
    }
}

struct AttentionTaskRow: View {
    let task: LeanVibeTask
    
    var body: some View {
        HStack(spacing: 12) {
            Text(task.priorityEmoji)
            
            VStack(alignment: .leading, spacing: 2) {
                Text(task.title)
                    .font(.subheadline)
                    .fontWeight(.medium)
                    .lineLimit(1)
                
                HStack {
                    Text("Confidence: \(Int(task.confidence * 100))%")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    
                    if task.requiresApproval {
                        Text("• Needs approval")
                            .font(.caption)
                            .foregroundColor(.orange)
                    }
                }
            }
            
            Spacer()
            
            Image(systemName: "chevron.right")
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .padding(.vertical, 8)
    }
}

struct StatusData {
    let status: TaskStatus
    let count: Int
}

struct PriorityData {
    let priority: TaskPriority
    let count: Int
}

struct TaskStatisticsView_Previews: PreviewProvider {
    static var previews: some View {
        TaskStatisticsView(taskService: TaskService())
    }
}