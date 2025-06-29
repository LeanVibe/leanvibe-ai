import SwiftUI

struct TaskCreationView: View {
    @Environment(\.dismiss) private var dismiss
    @ObservedObject var taskService: TaskService
    
    @State private var title = ""
    @State private var description = ""
    @State private var priority: TaskPriority = .medium
    @State private var assignedTo = ""
    @State private var newTag = ""
    @State private var tags: [String] = []
    @State private var isCreating = false
    
    private var isFormValid: Bool {
        !title.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }
    
    var body: some View {
        NavigationView {
            Form {
                Section("Task Details") {
                    TextField("Task title", text: $title, axis: .vertical)
                        .lineLimit(1...3)
                    
                    TextField("Description (optional)", text: $description, axis: .vertical)
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
                    TextField("Assigned to (optional)", text: $assignedTo)
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
                    Button(action: createTask) {
                        HStack {
                            if isCreating {
                                ProgressView()
                                    .scaleEffect(0.8)
                            }
                            Text("Create Task")
                        }
                        .frame(maxWidth: .infinity)
                    }
                    .disabled(!isFormValid || isCreating)
                }
            }
            .navigationTitle("New Task")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        dismiss()
                    }
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
    
    private func createTask() {
        guard isFormValid else { return }
        
        isCreating = true
        
        Task {
            // TODO: Implement createTask in TaskService
            // await taskService.createTask(
            //     title: title.trimmingCharacters(in: .whitespacesAndNewlines),
            //     description: description.trimmingCharacters(in: .whitespacesAndNewlines),
            //     priority: priority,
            //     assignedTo: assignedTo.isEmpty ? nil : assignedTo,
            //     tags: tags
            // )
            
            await MainActor.run {
                isCreating = false
                dismiss()
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
        case .critical:
            return "🔴"
        }
    }
}

struct TagsFlowView: View {
    let tags: [String]
    let onRemove: (String) -> Void
    
    var body: some View {
        LazyVGrid(columns: [GridItem(.adaptive(minimum: 80))], alignment: .leading, spacing: 8) {
            ForEach(tags, id: \.self) { tag in
                HStack(spacing: 4) {
                    Text(tag)
                        .font(.caption)
                    
                    Button(action: { onRemove(tag) }) {
                        Image(systemName: "xmark")
                            .font(.caption2)
                    }
                }
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(
                    Capsule()
                        .fill(Color.blue.opacity(0.1))
                )
                .foregroundColor(.blue)
            }
        }
    }
}

struct TaskCreationView_Previews: PreviewProvider {
    static var previews: some View {
        TaskCreationView(taskService: TaskService())
    }
}