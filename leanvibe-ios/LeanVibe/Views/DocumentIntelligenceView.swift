import SwiftUI

/// View for managing document intelligence and automatic Kanban task generation
@available(iOS 18.0, macOS 14.0, *)
struct DocumentIntelligenceView: View {
    
    // MARK: - Properties
    
    @StateObject private var documentService: DocumentIntelligenceService
    @StateObject private var projectManager = ProjectManager()
    @StateObject private var taskService = TaskService()
    
    @State private var selectedProject: Project?
    @State private var showingTaskPreview = false
    @State private var showingSettings = false
    @State private var autoProcessingEnabled = true
    @State private var selectedDocumentType: DocumentType = .plan
    
    // MARK: - Initialization
    
    init() {
        self._documentService = StateObject(wrappedValue: DocumentIntelligenceService(taskService: TaskService()))
    }
    
    // MARK: - Body
    
    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                // Header Controls
                headerSection
                
                // Main Content
                if documentService.isProcessing {
                    processingSection
                } else if documentService.discoveredTasks.isEmpty {
                    emptyStateSection
                } else {
                    discoveredTasksSection
                }
            }
            .navigationTitle("Document Intelligence")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Settings") {
                        showingSettings = true
                    }
                }
            }
        }
        .sheet(isPresented: $showingTaskPreview) {
            TaskPreviewSheet(
                tasks: documentService.discoveredTasks,
                onCreateTasks: { tasks in
                    Task {
                        await createSelectedTasks(tasks)
                    }
                }
            )
        }
        .sheet(isPresented: $showingSettings) {
            DocumentIntelligenceSettingsView(autoProcessingEnabled: $autoProcessingEnabled)
        }
        .onAppear {
            Task {
                try? await projectManager.refreshProjects()
                if let firstProject = projectManager.projects.first {
                    selectedProject = firstProject
                }
            }
        }
    }
    
    // MARK: - View Sections
    
    private var headerSection: some View {
        VStack(spacing: 16) {
            // Project Selection
            if !projectManager.projects.isEmpty {
                VStack(alignment: .leading, spacing: 8) {
                    Text("Select Project")
                        .font(.headline)
                    
                    Picker("Project", selection: $selectedProject) {
                        ForEach(projectManager.projects, id: \.id) { project in
                            Text(project.displayName).tag(project as Project?)
                        }
                    }
                    .pickerStyle(.menu)
                    .onChange(of: selectedProject) { _, _ in
                        if autoProcessingEnabled {
                            processCurrentProject()
                        }
                    }
                }
            }
            
            // Action Buttons
            HStack(spacing: 12) {
                Button(action: {
                    processCurrentProject()
                }) {
                    HStack {
                        Image(systemName: "doc.text.magnifyingglass")
                        Text("Analyze Documents")
                    }
                    .font(.subheadline)
                    .foregroundColor(.white)
                    .padding(.horizontal, 16)
                    .padding(.vertical, 8)
                    .background(Color.blue)
                    .cornerRadius(8)
                }
                .disabled(selectedProject == nil || documentService.isProcessing)
                
                if !documentService.discoveredTasks.isEmpty {
                    Button(action: {
                        showingTaskPreview = true
                    }) {
                        HStack {
                            Image(systemName: "eye")
                            Text("Preview Tasks")
                        }
                        .font(.subheadline)
                        .foregroundColor(.blue)
                        .padding(.horizontal, 16)
                        .padding(.vertical, 8)
                        .overlay(
                            RoundedRectangle(cornerRadius: 8)
                                .stroke(Color.blue, lineWidth: 1)
                        )
                    }
                }
            }
        }
        .padding()
        .background(Color(.systemGray6))
    }
    
    private var processingSection: some View {
        VStack(spacing: 20) {
            ProgressView()
                .scaleEffect(1.5)
            
            Text("Analyzing Documents")
                .font(.title2)
                .fontWeight(.medium)
            
            Text(documentService.processingStatus)
                .font(.caption)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color(.systemBackground))
    }
    
    private var emptyStateSection: some View {
        VStack(spacing: 20) {
            Image(systemName: "doc.text.below.ecg")
                .font(.system(size: 60))
                .foregroundColor(.blue)
            
            Text("No Documents Analyzed")
                .font(.title2)
                .fontWeight(.medium)
            
            Text("Select a project and click 'Analyze Documents' to automatically extract tasks from your documentation.")
                .font(.body)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal)
            
            if let lastProcessed = documentService.lastProcessedDate {
                Text("Last processed: \(lastProcessed, formatter: dateFormatter)")
                    .font(.caption)
                    .foregroundColor(.tertiary)
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color(.systemBackground))
    }
    
    private var discoveredTasksSection: some View {
        VStack(spacing: 0) {
            // Document Type Filter
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 12) {
                    ForEach(DocumentType.allCases, id: \.self) { docType in
                        let taskCount = documentService.getTasks(from: docType).count
                        
                        Button(action: {
                            selectedDocumentType = docType
                        }) {
                            VStack(spacing: 4) {
                                Text(docType.displayName)
                                    .font(.caption)
                                    .fontWeight(.medium)
                                
                                Text("\(taskCount)")
                                    .font(.caption2)
                                    .foregroundColor(.secondary)
                            }
                            .padding(.horizontal, 12)
                            .padding(.vertical, 8)
                            .background(
                                RoundedRectangle(cornerRadius: 8)
                                    .fill(selectedDocumentType == docType ? Color.blue : Color(.systemGray5))
                            )
                            .foregroundColor(selectedDocumentType == docType ? .white : .primary)
                        }
                        .disabled(taskCount == 0)
                    }
                }
                .padding(.horizontal)
            }
            .padding(.vertical, 8)
            
            // Tasks List
            List {
                ForEach(documentService.getTasks(from: selectedDocumentType), id: \.id) { task in
                    DocumentTaskRow(task: task)
                }
            }
            .listStyle(.plain)
        }
    }
    
    // MARK: - Helper Methods
    
    private func processCurrentProject() {
        guard let project = selectedProject else { return }
        
        Task {
            do {
                try await documentService.processProjectDocuments(for: project)
            } catch {
                print("Failed to process documents: \(error)")
            }
        }
    }
    
    private func createSelectedTasks(_ tasks: [DocumentTask]) async {
        // Implementation for creating tasks in the backend
        for task in tasks {
            let leanVibeTask = LeanVibeTask(
                id: task.id,
                title: task.title,
                description: task.description,
                status: task.suggestedStatus,
                priority: task.suggestedPriority,
                projectId: task.projectId,
                createdAt: Date(),
                updatedAt: Date(),
                confidence: task.confidence,
                agentDecision: nil,
                clientId: "document-intelligence",
                assignedTo: nil,
                estimatedEffort: nil,
                actualEffort: nil,
                tags: task.tags,
                dependencies: [],
                attachments: []
            )
            
            try? await taskService.createTask(leanVibeTask)
        }
    }
    
    private var dateFormatter: DateFormatter {
        let formatter = DateFormatter()
        formatter.dateStyle = .short
        formatter.timeStyle = .short
        return formatter
    }
}

// MARK: - Supporting Views

@available(iOS 18.0, macOS 14.0, *)
struct DocumentTaskRow: View {
    let task: DocumentTask
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                // Priority Indicator
                Circle()
                    .fill(task.suggestedPriority.color)
                    .frame(width: 8, height: 8)
                
                Text(task.title)
                    .font(.headline)
                    .lineLimit(2)
                
                Spacer()
                
                // Confidence Badge
                Text("\(Int(task.confidence * 100))%")
                    .font(.caption2)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(confidenceColor(task.confidence))
                    .foregroundColor(.white)
                    .cornerRadius(4)
            }
            
            HStack {
                // Status and Source
                Label(task.suggestedStatus.displayName, systemImage: task.suggestedStatus.systemImage)
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                Spacer()
                
                Text(task.documentSource)
                    .font(.caption2)
                    .foregroundColor(.tertiary)
            }
            
            // Tags
            if !task.tags.isEmpty {
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 4) {
                        ForEach(task.tags, id: \.self) { tag in
                            Text(tag)
                                .font(.caption2)
                                .padding(.horizontal, 6)
                                .padding(.vertical, 2)
                                .background(Color(.systemGray5))
                                .cornerRadius(4)
                        }
                    }
                }
            }
        }
        .padding(.vertical, 4)
    }
    
    private func confidenceColor(_ confidence: Double) -> Color {
        if confidence >= 0.8 { return .green }
        else if confidence >= 0.6 { return .orange }
        else { return .red }
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct TaskPreviewSheet: View {
    let tasks: [DocumentTask]
    let onCreateTasks: ([DocumentTask]) -> Void
    
    @Environment(\.dismiss) private var dismiss
    @State private var selectedTasks: Set<UUID> = []
    
    var body: some View {
        NavigationView {
            VStack {
                List {
                    ForEach(tasks, id: \.id) { task in
                        HStack {
                            Button(action: {
                                if selectedTasks.contains(task.id) {
                                    selectedTasks.remove(task.id)
                                } else {
                                    selectedTasks.insert(task.id)
                                }
                            }) {
                                Image(systemName: selectedTasks.contains(task.id) ? "checkmark.circle.fill" : "circle")
                                    .foregroundColor(selectedTasks.contains(task.id) ? .blue : .gray)
                            }
                            
                            DocumentTaskRow(task: task)
                        }
                    }
                }
                
                HStack {
                    Button("Select All") {
                        selectedTasks = Set(tasks.map { $0.id })
                    }
                    .disabled(selectedTasks.count == tasks.count)
                    
                    Spacer()
                    
                    Button("Create Selected (\(selectedTasks.count))") {
                        let tasksToCreate = tasks.filter { selectedTasks.contains($0.id) }
                        onCreateTasks(tasksToCreate)
                        dismiss()
                    }
                    .disabled(selectedTasks.isEmpty)
                    .buttonStyle(.borderedProminent)
                }
                .padding()
            }
            .navigationTitle("Preview Tasks")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
            }
        }
        .onAppear {
            // Auto-select high-confidence tasks
            selectedTasks = Set(tasks.filter { $0.confidence >= 0.7 }.map { $0.id })
        }
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct DocumentIntelligenceSettingsView: View {
    @Binding var autoProcessingEnabled: Bool
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            Form {
                Section("Processing Options") {
                    Toggle("Auto-process on project change", isOn: $autoProcessingEnabled)
                }
                
                Section("Document Types") {
                    Text("Supported document types for task extraction:")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    
                    ForEach(DocumentType.allCases, id: \.self) { docType in
                        HStack {
                            Text(docType.displayName)
                            Spacer()
                            Text("Priority \(docType.backlogPriority)")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                    }
                }
            }
            .navigationTitle("Document Intelligence")
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

// MARK: - Extensions

extension TaskStatus {
    var systemImage: String {
        switch self {
        case .backlog: return "tray"
        case .todo: return "list.bullet"
        case .inProgress: return "gear"
        case .testing: return "checkmark.seal"
        case .done: return "checkmark.circle"
        }
    }
    
    var displayName: String {
        switch self {
        case .backlog: return "Backlog"
        case .todo: return "To-Do"
        case .inProgress: return "In Progress"
        case .testing: return "Testing"
        case .done: return "Done"
        }
    }
}

extension TaskPriority {
    var color: Color {
        switch self {
        case .low: return .green
        case .medium: return .yellow
        case .high: return .orange
        case .urgent: return .red
        }
    }
}

#Preview {
    DocumentIntelligenceView()
}