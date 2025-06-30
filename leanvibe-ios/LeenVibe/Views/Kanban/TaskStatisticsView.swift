import SwiftUI
import Charts

@available(iOS 18.0, macOS 14.0, *)
@MainActor
struct TaskStatisticsView: View {
    @Environment(\.dismiss) private var dismiss
    @ObservedObject var taskService: TaskService
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    Text("No statistics available.")
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