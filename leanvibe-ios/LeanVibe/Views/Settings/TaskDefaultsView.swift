import SwiftUI

/// Task Defaults Settings view for configuring default task properties and behaviors
/// Provides controls for new task creation, assignment, and workflow defaults
@available(iOS 18.0, macOS 14.0, *)
struct TaskDefaultsView: View {
    
    // MARK: - Properties
    
    @ObservedObject var settingsManager: SettingsManager
    @State private var showingCustomFieldsEditor = false
    @State private var showingWorkflowRulesEditor = false
    
    // Local state for task default settings
    @State private var defaultPriority: TaskDefaultPriority = .medium
    @State private var defaultStatus: TaskDefaultStatus = .todo
    @State private var defaultEstimate: Double = 4
    @State private var autoAssignEnabled = false
    @State private var defaultAssignee = ""
    @State private var enableDueDateDefaults = false
    @State private var defaultDueDateOffset: Double = 7
    @State private var enableTagDefaults = false
    @State private var defaultTags: [String] = []
    @State private var newTagText = ""
    @State private var autoGenerateTaskIds = true
    @State private var taskIdPrefix = "TASK"
    @State private var enableTemplates = true
    @State private var defaultTemplate = "Standard Task"
    @State private var enableDescriptionTemplate = false
    @State private var descriptionTemplate = ""
    
    init(settingsManager: SettingsManager = SettingsManager.shared) {
        self.settingsManager = settingsManager
    }
    
    // MARK: - Body
    
    var body: some View {
        List {
            Section {
                Text("Configure default values and behaviors for new tasks in the Kanban board.")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .padding(.vertical, 4)
            }
            
            // Basic Task Defaults Section
            Section("Basic Task Defaults") {
                // Priority Picker
                Picker("Default Priority", selection: $defaultPriority) {
                    ForEach(TaskDefaultPriority.allCases, id: \.self) { priority in
                        HStack {
                            Circle()
                                .fill(priority.color)
                                .frame(width: 12, height: 12)
                            Text(priority.displayName)
                        }
                        .tag(priority)
                    }
                }
                .pickerStyle(MenuPickerStyle())
                
                // Status Picker
                Picker("Default Status", selection: $defaultStatus) {
                    ForEach(TaskDefaultStatus.allCases, id: \.self) { status in
                        Text(status.displayName).tag(status)
                    }
                }
                .pickerStyle(MenuPickerStyle())
                
                // Estimate Slider
                VStack(alignment: .leading, spacing: 8) {
                    Text("Default Estimate: \(String(format: "%.1f", defaultEstimate)) hours")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    
                    Slider(value: $defaultEstimate, in: 0.5...40, step: 0.5) {
                        Text("Default Estimate")
                    }
                }
                .padding(.vertical, 4)
            }
            
            // Assignment Defaults Section
            Section("Assignment Defaults") {
                Toggle("Auto-assign new tasks", isOn: $autoAssignEnabled)
                
                if autoAssignEnabled {
                    HStack {
                        Text("Default Assignee")
                        Spacer()
                        TextField("Enter username", text: $defaultAssignee)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                            .frame(maxWidth: 150)
                    }
                }
            }
            
            // Due Date Defaults Section
            Section("Due Date Defaults") {
                Toggle("Set default due dates", isOn: $enableDueDateDefaults)
                
                if enableDueDateDefaults {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Default due date: \(Int(defaultDueDateOffset)) days from creation")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        
                        Slider(value: $defaultDueDateOffset, in: 1...30, step: 1) {
                            Text("Days Offset")
                        }
                    }
                    .padding(.vertical, 4)
                }
            }
            
            // Tags and Labels Section
            Section("Tags and Labels") {
                Toggle("Apply default tags", isOn: $enableTagDefaults)
                
                if enableTagDefaults {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Default Tags")
                            .font(.headline)
                        
                        // Display current tags
                        if !defaultTags.isEmpty {
                            LazyVGrid(columns: [GridItem(.adaptive(minimum: 80))], spacing: 8) {
                                ForEach(defaultTags, id: \.self) { tag in
                                    TagChip(tag: tag) {
                                        removeTag(tag)
                                    }
                                }
                            }
                        }
                        
                        // Add new tag
                        HStack {
                            TextField("Add tag", text: $newTagText)
                                .textFieldStyle(RoundedBorderTextFieldStyle())
                                .onSubmit {
                                    addTag()
                                }
                            
                            Button("Add") {
                                addTag()
                            }
                            .disabled(newTagText.isEmpty)
                        }
                    }
                }
            }
            
            // Task ID Generation Section
            Section("Task ID Generation") {
                Toggle("Auto-generate task IDs", isOn: $autoGenerateTaskIds)
                
                if autoGenerateTaskIds {
                    HStack {
                        Text("ID Prefix")
                        Spacer()
                        TextField("Prefix", text: $taskIdPrefix)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                            .frame(maxWidth: 100)
                    }
                    
                    Text("Example: \(taskIdPrefix)-001, \(taskIdPrefix)-002, etc.")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
            
            // Templates Section
            Section("Task Templates") {
                Toggle("Enable task templates", isOn: $enableTemplates)
                
                if enableTemplates {
                    Picker("Default Template", selection: $defaultTemplate) {
                        Text("Standard Task").tag("Standard Task")
                        Text("Bug Report").tag("Bug Report")
                        Text("Feature Request").tag("Feature Request")
                        Text("Code Review").tag("Code Review")
                        Text("Documentation").tag("Documentation")
                    }
                    .pickerStyle(MenuPickerStyle())
                    
                    NavigationLink("Manage Templates") {
                        TaskTemplatesView()
                    }
                }
                
                Toggle("Default description template", isOn: $enableDescriptionTemplate)
                
                if enableDescriptionTemplate {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Description Template")
                            .font(.headline)
                        
                        TextEditor(text: $descriptionTemplate)
                            .frame(minHeight: 100)
                            .overlay(
                                RoundedRectangle(cornerRadius: 8)
                                    .stroke(Color.secondary.opacity(0.3), lineWidth: 1)
                            )
                        
                        Text("Use {{title}}, {{priority}}, {{assignee}} as placeholders")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }
            }
            
            // Advanced Configuration Section
            Section("Advanced Configuration") {
                Button("Custom Fields") {
                    showingCustomFieldsEditor = true
                }
                .foregroundColor(.blue)
                
                Button("Workflow Rules") {
                    showingWorkflowRulesEditor = true
                }
                .foregroundColor(.blue)
                
                Button("Reset to Defaults") {
                    resetToDefaults()
                }
                .foregroundColor(.red)
            }
        }
        .navigationTitle("Task Defaults")
        .navigationBarTitleDisplayMode(.large)
        .onAppear {
            loadSettings()
        }
        .onChange(of: defaultPriority) { saveSettings() }
        .onChange(of: defaultStatus) { saveSettings() }
        .onChange(of: defaultEstimate) { saveSettings() }
        .onChange(of: autoAssignEnabled) { saveSettings() }
        .onChange(of: defaultAssignee) { saveSettings() }
        .onChange(of: enableDueDateDefaults) { saveSettings() }
        .onChange(of: defaultDueDateOffset) { saveSettings() }
        .onChange(of: enableTagDefaults) { saveSettings() }
        .onChange(of: defaultTags) { saveSettings() }
        .onChange(of: autoGenerateTaskIds) { saveSettings() }
        .onChange(of: taskIdPrefix) { saveSettings() }
        .onChange(of: enableTemplates) { saveSettings() }
        .onChange(of: defaultTemplate) { saveSettings() }
        .onChange(of: enableDescriptionTemplate) { saveSettings() }
        .onChange(of: descriptionTemplate) { saveSettings() }
        .sheet(isPresented: $showingCustomFieldsEditor) {
            CustomFieldsView()
        }
        .sheet(isPresented: $showingWorkflowRulesEditor) {
            WorkflowRulesView()
        }
    }
    
    // MARK: - Methods
    
    private func loadSettings() {
        let settings = settingsManager.taskCreation
        
        defaultPriority = TaskDefaultPriority(rawValue: settings.defaultPriority) ?? .medium
        defaultStatus = TaskDefaultStatus(rawValue: settings.defaultStatus) ?? .todo
        defaultEstimate = settings.defaultEstimate
        autoAssignEnabled = settings.autoAssignEnabled
        defaultAssignee = settings.defaultAssignee
        enableDueDateDefaults = settings.enableDueDateDefaults
        defaultDueDateOffset = Double(settings.defaultDueDateOffset)
        enableTagDefaults = settings.enableTagDefaults
        defaultTags = settings.defaultTags
        autoGenerateTaskIds = settings.autoGenerateTaskIds
        taskIdPrefix = settings.taskIdPrefix
        enableTemplates = settings.enableTemplates
        defaultTemplate = settings.defaultTemplate
        enableDescriptionTemplate = settings.enableDescriptionTemplate
        descriptionTemplate = settings.descriptionTemplate
        
        print("✅ Task defaults settings loaded from SettingsManager")
    }
    
    private func saveSettings() {
        var settings = settingsManager.taskCreation
        
        settings.defaultPriority = defaultPriority.rawValue
        settings.defaultStatus = defaultStatus.rawValue
        settings.defaultEstimate = defaultEstimate
        settings.autoAssignEnabled = autoAssignEnabled
        settings.defaultAssignee = defaultAssignee
        settings.enableDueDateDefaults = enableDueDateDefaults
        settings.defaultDueDateOffset = Int(defaultDueDateOffset)
        settings.enableTagDefaults = enableTagDefaults
        settings.defaultTags = defaultTags
        settings.autoGenerateTaskIds = autoGenerateTaskIds
        settings.taskIdPrefix = taskIdPrefix
        settings.enableTemplates = enableTemplates
        settings.defaultTemplate = defaultTemplate
        settings.enableDescriptionTemplate = enableDescriptionTemplate
        settings.descriptionTemplate = descriptionTemplate
        
        settingsManager.taskCreation = settings
        
        print("✅ Task defaults settings saved to SettingsManager")
    }
    
    private func addTag() {
        let trimmedTag = newTagText.trimmingCharacters(in: .whitespacesAndNewlines)
        if !trimmedTag.isEmpty && !defaultTags.contains(trimmedTag) {
            defaultTags.append(trimmedTag)
            newTagText = ""
        }
    }
    
    private func removeTag(_ tag: String) {
        defaultTags.removeAll { $0 == tag }
    }
    
    private func resetToDefaults() {
        defaultPriority = .medium
        defaultStatus = .todo
        defaultEstimate = 4.0
        autoAssignEnabled = false
        defaultAssignee = ""
        enableDueDateDefaults = false
        defaultDueDateOffset = 7
        enableTagDefaults = false
        defaultTags = []
        autoGenerateTaskIds = true
        taskIdPrefix = "TASK"
        enableTemplates = true
        defaultTemplate = "Standard Task"
        enableDescriptionTemplate = false
        descriptionTemplate = ""
        
        saveSettings()
    }
}

// MARK: - Supporting Views

struct TagChip: View {
    let tag: String
    let onRemove: () -> Void
    
    var body: some View {
        HStack(spacing: 4) {
            Text(tag)
                .font(.caption)
                .foregroundColor(.white)
            
            Button(action: onRemove) {
                Image(systemName: "xmark.circle.fill")
                    .font(.caption)
                    .foregroundColor(.white.opacity(0.8))
            }
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(Color.blue)
        .cornerRadius(12)
    }
}

struct TaskTemplatesView: View {
    var body: some View {
        List {
            Section {
                Text("Manage task templates for different types of work.")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .padding(.vertical, 4)
            }
            
            Section("Available Templates") {
                Text("Task template management will be implemented here.")
                    .font(.body)
                    .foregroundColor(.secondary)
            }
        }
        .navigationTitle("Task Templates")
        .navigationBarTitleDisplayMode(.large)
    }
}

struct CustomFieldsView: View {
    var body: some View {
        NavigationView {
            List {
                Section {
                    Text("Define custom fields for tasks to capture additional information.")
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .padding(.vertical, 4)
                }
                
                Section("Custom Fields") {
                    Text("Custom fields management will be implemented here.")
                        .font(.body)
                        .foregroundColor(.secondary)
                }
            }
            .navigationTitle("Custom Fields")
            .navigationBarTitleDisplayMode(.large)
        }
    }
}

struct WorkflowRulesView: View {
    var body: some View {
        NavigationView {
            List {
                Section {
                    Text("Define rules for automatic task transitions and behaviors.")
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .padding(.vertical, 4)
                }
                
                Section("Workflow Rules") {
                    Text("Workflow rules management will be implemented here.")
                        .font(.body)
                        .foregroundColor(.secondary)
                }
            }
            .navigationTitle("Workflow Rules")
            .navigationBarTitleDisplayMode(.large)
        }
    }
}

// MARK: - Supporting Types

enum TaskDefaultPriority: String, CaseIterable {
    case low = "low"
    case medium = "medium"
    case high = "high"
    case urgent = "urgent"
    
    var displayName: String {
        switch self {
        case .low: return "Low"
        case .medium: return "Medium"
        case .high: return "High"
        case .urgent: return "Urgent"
        }
    }
    
    var color: Color {
        switch self {
        case .low: return .green
        case .medium: return .blue
        case .high: return .orange
        case .urgent: return .red
        }
    }
}

enum TaskDefaultStatus: String, CaseIterable {
    case todo = "todo"
    case inProgress = "in_progress"
    case review = "review"
    case done = "done"
    
    var displayName: String {
        switch self {
        case .todo: return "To Do"
        case .inProgress: return "In Progress"
        case .review: return "Review"
        case .done: return "Done"
        }
    }
}

#Preview {
    TaskDefaultsView()
}