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
        VStack(alignment: .leading, spacing: PremiumDesignSystem.Spacing.md) {
            // Column header
            HStack {
                Text(status.displayName)
                    .font(.headline)
                    .fontWeight(.semibold)
                
                Spacer()
                
                Text("\(tasks.count)")
                    .font(.caption)
                    .padding(.horizontal, PremiumDesignSystem.Spacing.sm)
                    .padding(.vertical, PremiumDesignSystem.Spacing.xs)
                    .background(PremiumDesignSystem.Colors.buttonPrimary.opacity(0.1))
                    .foregroundColor(PremiumDesignSystem.Colors.buttonPrimary)
                    .clipShape(Capsule())
            }
            .padding(.horizontal, PremiumDesignSystem.Spacing.lg)
            .padding(.top, PremiumDesignSystem.Spacing.lg)
            
            // Task cards
            ScrollView {
                LazyVStack(spacing: PremiumDesignSystem.Spacing.md) {
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
                .padding(.horizontal, PremiumDesignSystem.Spacing.lg)
            }
            .frame(minHeight: 400)
            
            Spacer()
        }
        .frame(width: 280)
        .background(PremiumDesignSystem.Colors.secondaryBackground)
        .clipShape(RoundedRectangle(cornerRadius: PremiumDesignSystem.CornerRadius.card))
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
        VStack(alignment: .leading, spacing: PremiumDesignSystem.Spacing.sm) {
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
        .padding(PremiumDesignSystem.Spacing.md)
        .background(PremiumDesignSystem.Colors.background)
        .clipShape(RoundedRectangle(cornerRadius: PremiumDesignSystem.CornerRadius.sm))
        .onTapGesture {
            onTap()
        }
    }
    
    private var priorityIndicator: some View {
        Circle()
            .fill(priorityColor)
            .frame(width: PremiumDesignSystem.Spacing.sm, height: PremiumDesignSystem.Spacing.sm)
    }
    
    private var priorityColor: Color {
        switch task.priority {
        case .urgent:
            return PremiumDesignSystem.Colors.error
        case .high:
            return PremiumDesignSystem.Colors.warning
        case .medium:
            return Color(.systemYellow)
        case .low:
            return PremiumDesignSystem.Colors.success
        }
    }
    
    private var confidenceIndicator: some View {
        HStack(spacing: PremiumDesignSystem.Spacing.xs) {
            Image(systemName: "brain")
                .font(.caption2)
                .foregroundColor(PremiumDesignSystem.Colors.buttonPrimary)
            
            Text("\(Int(task.confidence * 100))%")
                .font(.caption2)
                .foregroundColor(PremiumDesignSystem.Colors.buttonPrimary)
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
    .padding(PremiumDesignSystem.Spacing.containerPadding)
}