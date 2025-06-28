import SwiftUI

struct TaskDetailView: View {
    @Environment(\.dismiss) private var dismiss
    @ObservedObject var taskService: TaskService
    
    @State var task: Task
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
            if let decision = task.agentDecision {
                AgentDecisionApprovalView(
                    decision: decision,
                    taskService: taskService,
                    feedback: $approvalFeedback
                )
            }
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

struct StatusBadge: View {
    let status: TaskStatus
    
    var body: some View {
        HStack(spacing: 4) {
            Image(systemName: status.systemIcon)
            Text(status.displayName)
        }
        .font(.caption)
        .fontWeight(.medium)
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(
            Capsule()
                .fill(Color(status.statusColor).opacity(0.2))
        )
        .foregroundColor(Color(status.statusColor))
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
    let task: Task
    let taskService: TaskService
    
    var body: some View {
        Menu("Change Status") {
            ForEach(TaskStatus.allCases, id: \.self) { status in
                if status != task.status {
                    Button(action: {
                        Task {
                            await taskService.moveTask(task, to: status)
                        }
                    }) {
                        HStack {
                            Image(systemName: status.systemIcon)
                            Text(status.displayName)
                        }
                    }
                }
            }
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
            task: .constant(Task.mock()),
            taskService: TaskService()
        )
    }
}