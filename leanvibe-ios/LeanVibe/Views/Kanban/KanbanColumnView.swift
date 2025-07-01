import SwiftUI

@available(iOS 18.0, macOS 14.0, *)
struct KanbanColumnView: View {
    let status: TaskStatus
    let tasks: [LeanVibeTask]
    let taskService: TaskService
    @Binding var selectedTask: LeanVibeTask?
    @Binding var draggedTask: LeanVibeTask?
    let onDragError: (String) -> Void
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Column header
            HStack {
                Text(status.displayName)
                    .font(.headline)
                    .fontWeight(.semibold)
                
                Spacer()
                
                Text("\(tasks.count)")
                    .font(.caption)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(Color.blue.opacity(0.1))
                    .foregroundColor(.blue)
                    .clipShape(Capsule())
            }
            .padding(.horizontal, 16)
            .padding(.top, 16)
            
            // Task cards
            ScrollView {
                LazyVStack(spacing: 12) {
                    ForEach(tasks) { task in
                        TaskCardView(
                            task: task,
                            onTap: { selectedTask = task }
                        )
                        .draggable(task) {
                            // Drag preview
                            TaskCardView(task: task, onTap: {})
                                .frame(width: 200)
                        }
                        .onDrag {
                            draggedTask = task
                            return NSItemProvider(object: task.id.uuidString as NSString)
                        }
                    }
                }
                .padding(.horizontal, 16)
            }
            .frame(minHeight: 400)
            
            Spacer()
        }
        .frame(width: 280)
        .background(Color(.systemGray6))
        .clipShape(RoundedRectangle(cornerRadius: 12))
        .dropDestination(for: String.self) { items, location in
            guard let draggedTask = draggedTask,
                  draggedTask.status != status else { return false }
            
            // Update task status
            Task {
                do {
                    try await taskService.updateTaskStatus(draggedTask.id, status)
                    self.draggedTask = nil
                } catch {
                    onDragError("Failed to update task: \(error.localizedDescription)")
                }
            }
            
            return true
        }
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct TaskCardView: View {
    let task: LeanVibeTask
    let onTap: () -> Void
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(task.title)
                    .font(.headline)
                    .fontWeight(.medium)
                    .multilineTextAlignment(.leading)
                
                Spacer()
                
                priorityIndicator
            }
            
            if let description = task.description, !description.isEmpty {
                Text(description)
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .lineLimit(2)
            }
            
            HStack {
                confidenceIndicator
                
                Spacer()
                
                Text(formatDate(task.updatedAt))
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
        }
        .padding(12)
        .background(.regularMaterial)
        .clipShape(RoundedRectangle(cornerRadius: 8))
        .onTapGesture {
            onTap()
        }
    }
    
    private var priorityIndicator: some View {
        Circle()
            .fill(priorityColor)
            .frame(width: 8, height: 8)
    }
    
    private var priorityColor: Color {
        switch task.priority {
        case .urgent:
            return .red
        case .high:
            return .orange
        case .medium:
            return .yellow
        case .low:
            return .green
        }
    }
    
    private var confidenceIndicator: some View {
        HStack(spacing: 4) {
            Image(systemName: "brain")
                .font(.caption2)
                .foregroundColor(.blue)
            
            Text("\(Int(task.confidence * 100))%")
                .font(.caption2)
                .foregroundColor(.blue)
        }
    }
    
    private func formatDate(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateStyle = .none
        formatter.timeStyle = .short
        return formatter.string(from: date)
    }
}

#Preview {
    let sampleTask = LeanVibeTask(
        title: "Sample Task",
        description: "This is a sample task for preview",
        status: .inProgress,
        priority: .medium,
        projectId: UUID(),
        confidence: 0.85,
        clientId: "preview"
    )
    
    return KanbanColumnView(
        status: .inProgress,
        tasks: [sampleTask],
        taskService: TaskService(),
        selectedTask: .constant(nil),
        draggedTask: .constant(nil),
        onDragError: { _ in }
    )
    .frame(height: 600)
    .padding()
}