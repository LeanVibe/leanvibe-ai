import SwiftUI

@available(iOS 18.0, macOS 14.0, *)
struct TaskDetailView: View {
    @Environment(\.dismiss) private var dismiss
    @ObservedObject var taskService: TaskService
    
    @State var task: LeanVibeTask
    @State private var isEditing = false
    @State private var showingApprovalSheet = false
    @State private var approvalFeedback = ""
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    // Header Section
                    taskHeaderSection
                    
                    // Description Section
                    if !task.description.isEmpty {
                        descriptionSection
                    }
                    
                    // Metadata Section
                    metadataSection
                    
                    // Agent Decision Section
                    if let decision = task.agentDecision {
                        agentDecisionSection(decision)
                    }
                    
                    // Tags Section
                    if !task.tags.isEmpty {
                        tagsSection
                    }
                    
                    // Timeline Section
                    timelineSection
                }
                .padding()
            }
            .navigationTitle("Task Details")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Close") {
                        dismiss()
                    }
                }
                
                ToolbarItem(placement: .navigationBarTrailing) {
                    Menu {
                        Button(action: { isEditing = true }) {
                            Label("Edit Task", systemImage: "pencil")
                        }
                        
                        if task.requiresApproval {
                            Button(action: { showingApprovalSheet = true }) {
                                Label("Review Decision", systemImage: "checkmark.circle")
                            }
                        }
                        
                        StatusChangeMenu(task: task, taskService: taskService)
                    } label: {
                        Image(systemName: "ellipsis.circle")
                    }
                }
            }
        }
        .sheet(isPresented: $isEditing) {
            TaskEditView(task: $task, taskService: taskService)
        }
        .sheet(isPresented: $showingApprovalSheet) {
            // TODO: Implement AgentDecisionApprovalView
            Text("Agent Decision Approval - Coming Soon")
                .padding()
        }
    }
    
    private var taskHeaderSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                StatusBadge(status: task.status)
                Spacer()
                ConfidenceIndicatorView(confidence: task.confidence)
            }
            
            Text(task.title)
                .font(.title2)
                .fontWeight(.semibold)
            
            HStack {
                Text(task.priorityEmoji)
                Text(task.priority.rawValue.capitalized + " Priority")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            }
        }
    }
    
    private var descriptionSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Description")
                .font(.headline)
            
            Text(task.description)
                .font(.body)
                .padding(.leading, 8)
        }
    }
    
    private var metadataSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Details")
                .font(.headline)
            
            VStack(spacing: 8) {
                MetadataRow(
                    icon: "person.fill",
                    label: "Assigned to",
                    value: task.assignedTo ?? "Unassigned"
                )
                
                MetadataRow(
                    icon: "calendar",
                    label: "Created",
                    value: DateFormatter.taskDate.string(from: task.createdAt)
                )
                
                MetadataRow(
                    icon: "clock",
                    label: "Last updated",
                    value: DateFormatter.taskDate.string(from: task.updatedAt)
                )
                
                if let estimatedEffort = task.estimatedEffort {
                    MetadataRow(
                        icon: "hourglass",
                        label: "Estimated effort",
                        value: formatDuration(estimatedEffort)
                    )
                }
                
                if let actualEffort = task.actualEffort {
                    MetadataRow(
                        icon: "stopwatch",
                        label: "Actual effort",
                        value: formatDuration(actualEffort)
                    )
                }
            }
        }
    }
    
    private func agentDecisionSection(_ decision: AgentDecision) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("AI Agent Decision")
                    .font(.headline)
                
                Spacer()
                
                ApprovalStatusBadge(status: decision.approvalStatus)
            }
            
            VStack(alignment: .leading, spacing: 8) {
                Text("Recommendation")
                    .font(.subheadline)
                    .fontWeight(.medium)
                
                Text(decision.recommendation)
                    .font(.body)
                    .padding(.leading, 8)
            }
            
            VStack(alignment: .leading, spacing: 8) {
                Text("Reasoning")
                    .font(.subheadline)
                    .fontWeight(.medium)
                
                Text(decision.reasoning)
                    .font(.body)
                    .foregroundColor(.secondary)
                    .padding(.leading, 8)
            }
            
            HStack {
                Text("Confidence: \(Int(decision.confidence * 100))%")
                    .font(.caption)
                    .fontWeight(.medium)
                
                Spacer()
                
                if decision.requiresHumanApproval {
                    Label("Requires Approval", systemImage: "person.crop.circle.badge.exclamationmark")
                        .font(.caption)
                        .foregroundColor(.orange)
                }
            }
            
            if let feedback = decision.humanFeedback, !feedback.isEmpty {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Human Feedback")
                        .font(.subheadline)
                        .fontWeight(.medium)
                    
                    Text(feedback)
                        .font(.body)
                        .foregroundColor(.secondary)
                        .padding(.leading, 8)
                }
            }
        }
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color.blue.opacity(0.05))
        )
    }
    
    private var tagsSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Tags")
                .font(.headline)
            
            TagsView(tags: task.tags)
        }
    }
    
    private var timelineSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Timeline")
                .font(.headline)
            
            VStack(alignment: .leading, spacing: 12) {
                TimelineItem(
                    icon: "plus.circle.fill",
                    title: "Task Created",
                    subtitle: DateFormatter.taskDateTime.string(from: task.createdAt),
                    color: .green
                )
                
                if task.updatedAt > task.createdAt {
                    TimelineItem(
                        icon: "pencil.circle.fill",
                        title: "Last Updated",
                        subtitle: DateFormatter.taskDateTime.string(from: task.updatedAt),
                        color: .blue
                    )
                }
                
                if let decision = task.agentDecision {
                    TimelineItem(
                        icon: "brain.head.profile",
                        title: "AI Decision Made",
                        subtitle: DateFormatter.taskDateTime.string(from: decision.createdAt),
                        color: .purple
                    )
                }
            }
        }
    }
    
    private func formatDuration(_ seconds: TimeInterval) -> String {
        let hours = Int(seconds) / 3600
        let minutes = (Int(seconds) % 3600) / 60
        
        if hours > 0 {
            return "\(hours)h \(minutes)m"
        } else {
            return "\(minutes)m"
        }
    }
}

struct ConfidenceIndicatorView: View {
    let confidence: Double
    
    var body: some View {
        HStack(spacing: 4) {
            Circle()
                .fill(confidenceColor)
                .frame(width: 8, height: 8)
            Text("\(Int(confidence * 100))%")
                .font(.caption)
                .fontWeight(.medium)
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(
            Capsule()
                .fill(confidenceColor.opacity(0.2))
        )
        .foregroundColor(confidenceColor)
    }
    
    private var confidenceColor: Color {
        switch confidence {
        case 0.8...1.0: return .green
        case 0.5..<0.8: return .orange
        default: return .red
        }
    }
}

struct TagsView: View {
    let tags: [String]
    
    var body: some View {
        LazyVGrid(columns: [
            GridItem(.adaptive(minimum: 80))
        ], spacing: 8) {
            ForEach(tags, id: \.self) { tag in
                Text(tag)
                    .font(.caption)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(Color.blue.opacity(0.2))
                    .foregroundColor(.blue)
                    .cornerRadius(4)
            }
        }
    }
}

struct StatusBadge: View {
    let status: TaskStatus
    
    var body: some View {
        HStack(spacing: 4) {
            Image(systemName: statusIcon(for: status))
            Text(status.displayName)
        }
        .font(.caption)
        .fontWeight(.medium)
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(
            Capsule()
                .fill(statusColor(for: status).opacity(0.2))
        )
        .foregroundColor(statusColor(for: status))
    }
    
    private func statusIcon(for status: TaskStatus) -> String {
        switch status {
        case .backlog:
            return "tray.full"
        case .inProgress:
            return "play.circle"
        case .testing:
            return "checkmark.circle"
        case .done:
            return "checkmark.circle.fill"
        case .blocked:
            return "exclamationmark.triangle"
        }
    }
    
    private func statusColor(for status: TaskStatus) -> Color {
        switch status {
        case .backlog:
            return .gray
        case .inProgress:
            return .blue
        case .testing:
            return .orange
        case .done:
            return .green
        case .blocked:
            return .red
        }
    }
}

struct ApprovalStatusBadge: View {
    let status: ApprovalStatus
    
    var body: some View {
        Text(status.displayName)
            .font(.caption)
            .fontWeight(.medium)
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(
                Capsule()
                    .fill(Color(status.color).opacity(0.2))
            )
            .foregroundColor(Color(status.color))
    }
}

struct MetadataRow: View {
    let icon: String
    let label: String
    let value: String
    
    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .foregroundColor(.secondary)
                .frame(width: 16)
            
            Text(label)
                .font(.subheadline)
                .foregroundColor(.secondary)
            
            Spacer()
            
            Text(value)
                .font(.subheadline)
                .fontWeight(.medium)
        }
    }
}

struct TimelineItem: View {
    let icon: String
    let title: String
    let subtitle: String
    let color: Color
    
    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .foregroundColor(color)
                .frame(width: 16)
            
            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(.subheadline)
                    .fontWeight(.medium)
                
                Text(subtitle)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
        }
    }
}

struct StatusChangeMenu: View {
    let task: LeanVibeTask
    let taskService: TaskService
    
    var body: some View {
        Menu("Change Status") {
            ForEach(TaskStatus.allCases, id: \.self) { status in
                if status != task.status {
                    Button(action: {
                        // TODO: Implement moveTask in TaskService
                        // Task {
                        //     await taskService.moveTask(task, to: status)
                        // }
                    }) {
                        HStack {
                            Image(systemName: statusIcon(for: status))
                            Text(status.displayName)
                        }
                    }
                }
            }
        }
    }
    
    private func statusIcon(for status: TaskStatus) -> String {
        switch status {
        case .backlog:
            return "tray.full"
        case .inProgress:
            return "play.circle"
        case .testing:
            return "checkmark.circle"
        case .done:
            return "checkmark.circle.fill"
        case .blocked:
            return "exclamationmark.triangle"
        }
    }
}

extension DateFormatter {
    static let taskDate: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        formatter.timeStyle = .none
        return formatter
    }()
    
    static let taskDateTime: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        formatter.timeStyle = .short
        return formatter
    }()
}

struct TaskDetailView_Previews: PreviewProvider {
    static var previews: some View {
        TaskDetailView(
            taskService: TaskService(),
            task: LeanVibeTask(
                id: UUID(),
                title: "Sample Task",
                description: "This is a sample task for preview",
                status: .inProgress,
                priority: .medium,
                confidence: 0.85,
                clientId: "preview-client"
            )
        )
    }
}
