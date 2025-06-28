import SwiftUI
import Charts

struct TaskStatisticsView: View {
    @Environment(\.dismiss) private var dismiss
    @ObservedObject var taskService: TaskService
    
    private var statistics: TaskStatistics {
        taskService.getTaskStatistics()
    }
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 24) {
                    // Overview Cards
                    overviewSection
                    
                    // Status Distribution Chart
                    statusDistributionSection
                    
                    // Priority Distribution
                    priorityDistributionSection
                    
                    // Confidence Analysis
                    confidenceAnalysisSection
                    
                    // Tasks Requiring Attention
                    tasksRequiringAttentionSection
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
        }
    }
    
    private var overviewSection: some View {
        VStack(spacing: 16) {
            Text("Overview")
                .font(.headline)
                .frame(maxWidth: .infinity, alignment: .leading)
            
            LazyVGrid(columns: [
                GridItem(.flexible()),
                GridItem(.flexible())
            ], spacing: 16) {
                StatCard(
                    title: "Total Tasks",
                    value: "\(statistics.total)",
                    icon: "list.bullet",
                    color: .blue
                )
                
                StatCard(
                    title: "Completed",
                    value: "\(statistics.completed)",
                    icon: "checkmark.circle.fill",
                    color: .green
                )
                
                StatCard(
                    title: "In Progress",
                    value: "\(statistics.inProgress)",
                    icon: "gear",
                    color: .orange
                )
                
                StatCard(
                    title: "Need Approval",
                    value: "\(statistics.requiresApproval)",
                    icon: "person.crop.circle.badge.exclamationmark",
                    color: .red
                )
            }
        }
    }
    
    private var statusDistributionSection: some View {
        VStack(spacing: 16) {
            Text("Status Distribution")
                .font(.headline)
                .frame(maxWidth: .infinity, alignment: .leading)
            
            let statusData = TaskStatus.allCases.map { status in
                StatusData(
                    status: status,
                    count: taskService.tasksByStatus(status).count
                )
            }
            
            Chart(statusData, id: \.status) { data in
                BarMark(
                    x: .value("Status", data.status.displayName),
                    y: .value("Count", data.count)
                )
                .foregroundStyle(Color(data.status.statusColor))
            }
            .frame(height: 200)
            .chartYAxis {
                AxisMarks(position: .leading)
            }
        }
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color.gray.opacity(0.05))
        )
    }
    
    private var priorityDistributionSection: some View {
        VStack(spacing: 16) {
            Text("Priority Distribution")
                .font(.headline)
                .frame(maxWidth: .infinity, alignment: .leading)
            
            let priorityData = TaskPriority.allCases.map { priority in
                PriorityData(
                    priority: priority,
                    count: taskService.tasks.filter { $0.priority == priority }.count
                )
            }
            
            Chart(priorityData, id: \.priority) { data in
                SectorMark(
                    angle: .value("Count", data.count),
                    innerRadius: .ratio(0.5),
                    angularInset: 2
                )
                .foregroundStyle(priorityColor(data.priority))
                .opacity(data.count > 0 ? 1.0 : 0.3)
            }
            .frame(height: 200)
            
            // Legend
            LazyVGrid(columns: [
                GridItem(.flexible()),
                GridItem(.flexible())
            ], spacing: 8) {
                ForEach(priorityData, id: \.priority) { data in
                    HStack(spacing: 8) {
                        Circle()
                            .fill(priorityColor(data.priority))
                            .frame(width: 12, height: 12)
                        
                        Text("\(data.priority.rawValue.capitalized): \(data.count)")
                            .font(.caption)
                    }
                }
            }
        }
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color.gray.opacity(0.05))
        )
    }
    
    private var confidenceAnalysisSection: some View {
        VStack(spacing: 16) {
            Text("Confidence Analysis")
                .font(.headline)
                .frame(maxWidth: .infinity, alignment: .leading)
            
            VStack(spacing: 12) {
                ProgressView(
                    "Average Confidence",
                    value: statistics.averageConfidence,
                    total: 1.0
                )
                .progressViewStyle(LinearProgressViewStyle(tint: confidenceColor(statistics.averageConfidence)))
                
                Text("\(Int(statistics.averageConfidence * 100))%")
                    .font(.title2)
                    .fontWeight(.semibold)
                    .foregroundColor(confidenceColor(statistics.averageConfidence))
                
                HStack {
                    Text("Low confidence tasks:")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                    
                    Spacer()
                    
                    Text("\(taskService.tasks.filter { $0.confidence < 0.5 }.count)")
                        .font(.subheadline)
                        .fontWeight(.semibold)
                        .foregroundColor(.red)
                }
            }
        }
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color.gray.opacity(0.05))
        )
    }
    
    private var tasksRequiringAttentionSection: some View {
        VStack(spacing: 16) {
            Text("Tasks Requiring Attention")
                .font(.headline)
                .frame(maxWidth: .infinity, alignment: .leading)
            
            let attentionTasks = taskService.tasksRequiringApproval()
            
            if attentionTasks.isEmpty {
                VStack(spacing: 8) {
                    Image(systemName: "checkmark.circle.fill")
                        .font(.title)
                        .foregroundColor(.green)
                    
                    Text("All tasks are on track!")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }
                .frame(maxWidth: .infinity)
                .padding()
            } else {
                ForEach(attentionTasks.prefix(5)) { task in
                    AttentionTaskRow(task: task)
                }
                
                if attentionTasks.count > 5 {
                    Text("... and \(attentionTasks.count - 5) more")
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .frame(maxWidth: .infinity, alignment: .center)
                }
            }
        }
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color.gray.opacity(0.05))
        )
    }
    
    private func priorityColor(_ priority: TaskPriority) -> Color {
        switch priority {
        case .low:
            return .green
        case .medium:
            return .yellow
        case .high:
            return .orange
        case .critical:
            return .red
        }
    }
    
    private func confidenceColor(_ confidence: Double) -> Color {
        switch confidence {
        case 0.8...1.0:
            return .green
        case 0.5..<0.8:
            return .yellow
        default:
            return .red
        }
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
    let task: Task
    
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

#Preview {
    TaskStatisticsView(taskService: TaskService(webSocketService: WebSocketService()))
}