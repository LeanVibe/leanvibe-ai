import SwiftUI

/// Column Customization view for configuring Kanban board columns
/// Provides controls for adding, editing, reordering, and styling columns
@available(iOS 18.0, macOS 14.0, *)
struct ColumnCustomizationView: View {
    
    // MARK: - Properties
    
    @ObservedObject var settingsManager: SettingsManager
    @Environment(\.dismiss) private var dismiss
    @State private var columns: [CustomKanbanColumn] = []
    @State private var showingAddColumn = false
    @State private var editingColumn: CustomKanbanColumn?
    @State private var showingDeleteConfirmation = false
    @State private var columnToDelete: CustomKanbanColumn?
    @State private var draggedColumn: CustomKanbanColumn?
    
    init(settingsManager: SettingsManager = SettingsManager.shared) {
        self.settingsManager = settingsManager
    }
    
    // MARK: - Body
    
    var body: some View {
        NavigationView {
            List {
                Section {
                    Text("Customize your Kanban board columns. Drag to reorder, tap to edit, or add new columns.")
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .padding(.vertical, 4)
                }
                
                Section("Board Columns") {
                    ForEach(columns) { column in
                        ColumnRow(
                            column: column,
                            onEdit: { editingColumn = column },
                            onDelete: { 
                                columnToDelete = column
                                showingDeleteConfirmation = true
                            }
                        )
                        .onDrag {
                            draggedColumn = column
                            return NSItemProvider(object: column.id.uuidString as NSString)
                        }
                        .onDrop(of: [.text], delegate: ColumnDropDelegate(
                            column: column,
                            columns: $columns,
                            draggedColumn: $draggedColumn
                        ))
                    }
                    
                    Button(action: { showingAddColumn = true }) {
                        HStack {
                            Image(systemName: "plus.circle.fill")
                                .foregroundColor(.blue)
                            Text("Add Column")
                                .foregroundColor(.blue)
                        }
                    }
                }
                
                Section("Column Presets") {
                    Button("Default Workflow") {
                        applyPreset(.defaultWorkflow)
                    }
                    .foregroundColor(.blue)
                    
                    Button("Agile/Scrum") {
                        applyPreset(.agileScrum)
                    }
                    .foregroundColor(.blue)
                    
                    Button("Bug Tracking") {
                        applyPreset(.bugTracking)
                    }
                    .foregroundColor(.blue)
                    
                    Button("Simple Kanban") {
                        applyPreset(.simpleKanban)
                    }
                    .foregroundColor(.blue)
                }
                
                Section("Global Column Settings") {
                    Toggle("Show task counts in columns", isOn: .constant(true))
                    Toggle("Enable column color coding", isOn: .constant(true))
                    Toggle("Auto-collapse empty columns", isOn: .constant(false))
                    
                    NavigationLink("Advanced Column Rules") {
                        ColumnRulesView()
                    }
                }
            }
            .navigationTitle("Customize Columns")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
                
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Save") {
                        saveColumns()
                        dismiss()
                    }
                    .fontWeight(.semibold)
                }
            }
        }
        .onAppear {
            loadColumns()
        }
        .sheet(isPresented: $showingAddColumn) {
            ColumnEditorView(
                column: CustomKanbanColumn.defaultColumn(),
                isNew: true,
                onSave: { newColumn in
                    columns.append(newColumn)
                }
            )
        }
        .sheet(item: $editingColumn) { column in
            ColumnEditorView(
                column: column,
                isNew: false,
                onSave: { editedColumn in
                    if let index = columns.firstIndex(where: { $0.id == column.id }) {
                        columns[index] = editedColumn
                    }
                }
            )
        }
        .alert("Delete Column", isPresented: $showingDeleteConfirmation) {
            Button("Delete", role: .destructive) {
                if let column = columnToDelete {
                    deleteColumn(column)
                }
            }
            Button("Cancel", role: .cancel) {}
        } message: {
            if let column = columnToDelete {
                Text("Are you sure you want to delete '\(column.title)'? This action cannot be undone.")
            }
        }
    }
    
    // MARK: - Methods
    
    private func loadColumns() {
        // Load from settings or use defaults
        columns = [
            CustomKanbanColumn(title: "To Do", color: .blue, allowedTaskTypes: [.task, .story], maxTaskLimit: nil),
            CustomKanbanColumn(title: "In Progress", color: .orange, allowedTaskTypes: [.task, .story], maxTaskLimit: 5),
            CustomKanbanColumn(title: "Review", color: .purple, allowedTaskTypes: [.task, .story], maxTaskLimit: 3),
            CustomKanbanColumn(title: "Done", color: .green, allowedTaskTypes: [.task, .story, .bug], maxTaskLimit: nil)
        ]
        
        print("✅ Columns loaded")
    }
    
    private func saveColumns() {
        // Save to settings manager
        var kanbanSettings = settingsManager.kanban
        kanbanSettings.customColumns = columns.map { column in
            KanbanColumnSettings(
                id: column.id.uuidString,
                title: column.title,
                color: column.color.toHex(),
                position: columns.firstIndex(of: column) ?? 0,
                isVisible: true,
                maxTaskLimit: column.maxTaskLimit
            )
        }
        settingsManager.kanban = kanbanSettings
        
        print("✅ Columns saved to SettingsManager")
    }
    
    private func deleteColumn(_ column: CustomKanbanColumn) {
        columns.removeAll { $0.id == column.id }
        columnToDelete = nil
    }
    
    private func applyPreset(_ preset: ColumnPreset) {
        switch preset {
        case .defaultWorkflow:
            columns = [
                CustomKanbanColumn(title: "Backlog", color: .gray, allowedTaskTypes: [.task, .story], maxTaskLimit: nil),
                CustomKanbanColumn(title: "To Do", color: .blue, allowedTaskTypes: [.task, .story], maxTaskLimit: nil),
                CustomKanbanColumn(title: "In Progress", color: .orange, allowedTaskTypes: [.task, .story], maxTaskLimit: 3),
                CustomKanbanColumn(title: "Review", color: .purple, allowedTaskTypes: [.task, .story], maxTaskLimit: 2),
                CustomKanbanColumn(title: "Done", color: .green, allowedTaskTypes: [.task, .story], maxTaskLimit: nil)
            ]
            
        case .agileScrum:
            columns = [
                CustomKanbanColumn(title: "Product Backlog", color: .gray, allowedTaskTypes: [.story, .epic], maxTaskLimit: nil),
                CustomKanbanColumn(title: "Sprint Backlog", color: .blue, allowedTaskTypes: [.story, .task], maxTaskLimit: nil),
                CustomKanbanColumn(title: "In Progress", color: .orange, allowedTaskTypes: [.story, .task], maxTaskLimit: 5),
                CustomKanbanColumn(title: "Testing", color: .yellow, allowedTaskTypes: [.story, .task], maxTaskLimit: 3),
                CustomKanbanColumn(title: "Review", color: .purple, allowedTaskTypes: [.story, .task], maxTaskLimit: 2),
                CustomKanbanColumn(title: "Done", color: .green, allowedTaskTypes: [.story, .task], maxTaskLimit: nil)
            ]
            
        case .bugTracking:
            columns = [
                CustomKanbanColumn(title: "Reported", color: .red, allowedTaskTypes: [.bug], maxTaskLimit: nil),
                CustomKanbanColumn(title: "Triaged", color: .orange, allowedTaskTypes: [.bug], maxTaskLimit: nil),
                CustomKanbanColumn(title: "In Progress", color: .blue, allowedTaskTypes: [.bug], maxTaskLimit: 3),
                CustomKanbanColumn(title: "Testing", color: .yellow, allowedTaskTypes: [.bug], maxTaskLimit: 2),
                CustomKanbanColumn(title: "Verified", color: .purple, allowedTaskTypes: [.bug], maxTaskLimit: nil),
                CustomKanbanColumn(title: "Closed", color: .green, allowedTaskTypes: [.bug], maxTaskLimit: nil)
            ]
            
        case .simpleKanban:
            columns = [
                CustomKanbanColumn(title: "To Do", color: .blue, allowedTaskTypes: [.task], maxTaskLimit: nil),
                CustomKanbanColumn(title: "Doing", color: .orange, allowedTaskTypes: [.task], maxTaskLimit: 3),
                CustomKanbanColumn(title: "Done", color: .green, allowedTaskTypes: [.task], maxTaskLimit: nil)
            ]
        }
    }
}

// MARK: - Supporting Views

struct ColumnRow: View {
    let column: CustomKanbanColumn
    let onEdit: () -> Void
    let onDelete: () -> Void
    
    var body: some View {
        HStack {
            // Drag handle
            Image(systemName: "line.3.horizontal")
                .foregroundColor(.secondary)
                .font(.caption)
            
            // Column color indicator
            RoundedRectangle(cornerRadius: 4)
                .fill(column.color)
                .frame(width: 8, height: 32)
            
            VStack(alignment: .leading, spacing: 4) {
                Text(column.title)
                    .font(.headline)
                
                HStack {
                    if let limit = column.maxTaskLimit {
                        Text("Max: \(limit) tasks")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    
                    Text("\(column.allowedTaskTypes.count) task types")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
            
            Spacer()
            
            // Action buttons
            HStack(spacing: 12) {
                Button(action: onEdit) {
                    Image(systemName: "pencil")
                        .foregroundColor(.blue)
                }
                
                Button(action: onDelete) {
                    Image(systemName: "trash")
                        .foregroundColor(.red)
                }
            }
        }
        .padding(.vertical, 4)
    }
}

struct ColumnEditorView: View {
    @State var column: CustomKanbanColumn
    let isNew: Bool
    let onSave: (CustomKanbanColumn) -> Void
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            Form {
                Section("Basic Information") {
                    TextField("Column Title", text: $column.title)
                    
                    ColorPicker("Column Color", selection: Binding(
                        get: { column.color },
                        set: { column.color = $0 }
                    ))
                }
                
                Section("Task Limits") {
                    Toggle("Set maximum task limit", isOn: Binding(
                        get: { column.maxTaskLimit != nil },
                        set: { enabled in
                            column.maxTaskLimit = enabled ? 5 : nil
                        }
                    ))
                    
                    if column.maxTaskLimit != nil {
                        Stepper("Max Tasks: \(column.maxTaskLimit ?? 0)", 
                               value: Binding(
                                get: { column.maxTaskLimit ?? 0 },
                                set: { column.maxTaskLimit = $0 }
                               ),
                               in: 1...20)
                    }
                }
                
                Section("Allowed Task Types") {
                    ForEach(TaskType.allCases, id: \.self) { taskType in
                        Toggle(taskType.displayName, isOn: Binding(
                            get: { column.allowedTaskTypes.contains(taskType) },
                            set: { enabled in
                                if enabled {
                                    if !column.allowedTaskTypes.contains(taskType) {
                                        column.allowedTaskTypes.append(taskType)
                                    }
                                } else {
                                    column.allowedTaskTypes.removeAll { $0 == taskType }
                                }
                            }
                        ))
                    }
                }
            }
            .navigationTitle(isNew ? "New Column" : "Edit Column")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
                
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Save") {
                        onSave(column)
                        dismiss()
                    }
                    .disabled(column.title.isEmpty)
                }
            }
        }
    }
}

struct ColumnRulesView: View {
    var body: some View {
        List {
            Section {
                Text("Configure advanced rules for column behavior and task transitions.")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .padding(.vertical, 4)
            }
            
            Section("Column Rules") {
                Text("Advanced column rules will be implemented here.")
                    .font(.body)
                    .foregroundColor(.secondary)
            }
        }
        .navigationTitle("Column Rules")
        .navigationBarTitleDisplayMode(.large)
    }
}

// MARK: - Drag and Drop Support

struct ColumnDropDelegate: DropDelegate {
    let column: CustomKanbanColumn
    @Binding var columns: [CustomKanbanColumn]
    @Binding var draggedColumn: CustomKanbanColumn?
    
    func performDrop(info: DropInfo) -> Bool {
        return true
    }
    
    func dropEntered(info: DropInfo) {
        guard let draggedColumn = draggedColumn,
              let fromIndex = columns.firstIndex(of: draggedColumn),
              let toIndex = columns.firstIndex(of: column) else { return }
        
        if fromIndex != toIndex {
            withAnimation {
                columns.move(fromOffsets: IndexSet(integer: fromIndex), toOffset: toIndex > fromIndex ? toIndex + 1 : toIndex)
            }
        }
    }
}

// MARK: - Supporting Types

struct CustomKanbanColumn: Identifiable, Equatable, Hashable {
    let id = UUID()
    var title: String
    var color: Color
    var allowedTaskTypes: [TaskType]
    var maxTaskLimit: Int?
    
    static func defaultColumn() -> CustomKanbanColumn {
        return CustomKanbanColumn(
            title: "New Column",
            color: .blue,
            allowedTaskTypes: [.task],
            maxTaskLimit: nil
        )
    }
    
    static func == (lhs: KanbanColumn, rhs: KanbanColumn) -> Bool {
        lhs.id == rhs.id
    }
    
    func hash(into hasher: inout Hasher) {
        hasher.combine(id)
    }
}

struct KanbanColumnSettings {
    let id: String
    let title: String
    let color: String
    let position: Int
    let isVisible: Bool
    let maxTaskLimit: Int?
}

enum TaskType: String, CaseIterable {
    case task = "task"
    case story = "story"
    case bug = "bug"
    case epic = "epic"
    
    var displayName: String {
        switch self {
        case .task: return "Task"
        case .story: return "User Story"
        case .bug: return "Bug"
        case .epic: return "Epic"
        }
    }
}

enum ColumnPreset {
    case defaultWorkflow
    case agileScrum
    case bugTracking
    case simpleKanban
}

// MARK: - Color Extension

extension Color {
    func toHex() -> String {
        let uiColor = UIColor(self)
        var red: CGFloat = 0
        var green: CGFloat = 0
        var blue: CGFloat = 0
        var alpha: CGFloat = 0
        
        uiColor.getRed(&red, green: &green, blue: &blue, alpha: &alpha)
        
        return String(format: "#%02X%02X%02X",
                     Int(red * 255),
                     Int(green * 255),
                     Int(blue * 255))
    }
}

#Preview {
    ColumnCustomizationView()
}