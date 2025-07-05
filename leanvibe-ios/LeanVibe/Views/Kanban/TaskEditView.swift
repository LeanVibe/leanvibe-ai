import SwiftUI

@available(iOS 18.0, macOS 14.0, *)
struct TaskEditView: View {
    @Environment(\.dismiss) private var dismiss
    @Binding var task: LeanVibeTask
    @ObservedObject var taskService: TaskService
    
    @State private var title: String
    @State private var description: String
    @State private var priority: TaskPriority
    @State private var assignedTo: String
    @State private var tags: [String]
    @State private var newTag = ""
    @State private var isUpdating = false
    
    init(task: Binding<LeanVibeTask>, taskService: TaskService) {
        self._task = task
        self.taskService = taskService
        
        // Initialize state with current task values
        self._title = State(initialValue: task.wrappedValue.title)
        self._description = State(initialValue: task.wrappedValue.description ?? "")
        self._priority = State(initialValue: task.wrappedValue.priority)
        self._assignedTo = State(initialValue: task.wrappedValue.assignedTo ?? "")
        self._tags = State(initialValue: task.wrappedValue.tags)
    }
    
    private var isFormValid: Bool {
        !title.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }
    
    private var hasChanges: Bool {
        title != task.title ||
        description != task.description ||
        priority != task.priority ||
        (assignedTo.isEmpty ? nil : assignedTo) != task.assignedTo ||
        tags != task.tags
    }
    
    var body: some View {
        Form {
                Section("Task Details") {
                    TextField("Task title", text: $title, axis: .vertical)
                        .lineLimit(1...3)
                    
                    TextField("Description", text: $description, axis: .vertical)
                        .lineLimit(2...6)
                }
                
                Section("Priority") {
                    Picker("Priority", selection: $priority) {
                        ForEach(TaskPriority.allCases, id: \.self) { priority in
                            HStack {
                                Text(priority.rawValue.capitalized)
                                Spacer()
                                Text(priorityEmoji(priority))
                            }
                            .tag(priority)
                        }
                    }
                    .pickerStyle(.segmented)
                }
                
                Section("Assignment") {
                    TextField("Assigned to", text: $assignedTo)
                        .textContentType(.name)
                }
                
                Section("Tags") {
                    HStack {
                        TextField("Add tag", text: $newTag)
                            .onSubmit {
                                addTag()
                            }
                        
                        Button("Add", action: addTag)
                            .disabled(newTag.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                    }
                    
                    if !tags.isEmpty {
                        TagsFlowView(tags: tags, onRemove: { tag in
                            tags.removeAll { $0 == tag }
                        })
                    }
                }
                
                Section {
                    Button(action: updateTask) {
                        HStack {
                            if isUpdating {
                                ProgressView()
                                    .scaleEffect(0.8)
                            }
                            Text("Update Task")
                        }
                        .frame(maxWidth: .infinity)
                    }
                    .disabled(!isFormValid || !hasChanges || isUpdating)
                }
            }
            .navigationTitle("Edit Task")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
            }
        }
    
    private func addTag() {
        let trimmedTag = newTag.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmedTag.isEmpty, !tags.contains(trimmedTag) else { return }
        
        tags.append(trimmedTag)
        newTag = ""
    }
    
    private func updateTask() {
        guard isFormValid, hasChanges else { return }
        
        isUpdating = true
        
        // Update the task with new values
        var updatedTask = task
        updatedTask.title = title.trimmingCharacters(in: .whitespacesAndNewlines)
        updatedTask.description = description.trimmingCharacters(in: .whitespacesAndNewlines)
        updatedTask.priority = priority
        updatedTask.assignedTo = assignedTo.isEmpty ? nil : assignedTo
        updatedTask.tags = tags
        updatedTask.updatedAt = Date()
        
        Task {
            do {
                try await taskService.updateTask(updatedTask)
                
                await MainActor.run {
                    self.task = updatedTask
                    isUpdating = false
                    dismiss()
                }
            } catch {
                await MainActor.run {
                    isUpdating = false
                    // Global error manager handles the error display
                    // TaskService already shows the error via GlobalErrorManager
                }
            }
        }
    }
    
    private func priorityEmoji(_ priority: TaskPriority) -> String {
        switch priority {
        case .low:
            return "🟢"
        case .medium:
            return "🟡"
        case .high:
            return "🟠"
        case .urgent:
            return "🔴"
        }
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct TaskEditView_Previews: PreviewProvider {
    static var previews: some View {
        TaskEditView(
            task: .constant(LeanVibeTask(
                id: UUID(),
                title: "Sample Task",
                description: "This is a sample task for preview",
                status: .inProgress,
                priority: .medium,
                projectId: UUID(),
                confidence: 0.85,
                clientId: "preview-client"
            )),
            taskService: TaskService()
        )
    }
}