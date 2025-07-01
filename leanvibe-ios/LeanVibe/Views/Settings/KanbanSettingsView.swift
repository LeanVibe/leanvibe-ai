import SwiftUI

/// Comprehensive Kanban Settings view for configuring the Kanban board built by KAPPA
/// Provides controls for board behavior, columns, tasks, and integration features
@available(iOS 18.0, macOS 14.0, *)
struct KanbanSettingsView: View {
    
    // MARK: - Properties
    
    @StateObject private var settingsManager = SettingsManager.shared
    @Bindable private var bindableSettingsManager: SettingsManager = SettingsManager.shared
    @State private var showingColumnCustomization = false
    @State private var showingTaskDefaults = false
    @State private var showingPerformanceSettings = false
    
    // MARK: - Body
    
    var body: some View {
        List {
            // Board Behavior Section
            boardBehaviorSection
            
            // Columns Configuration
            columnsSection
            
            // Task Management
            taskManagementSection
            
            // Performance Settings
            performanceSection
            
            // Integration Settings
            integrationSection
            
            // Advanced Options
            advancedSection
        }
        .navigationTitle("Kanban Settings")
        .navigationBarTitleDisplayMode(.inline)
        .sheet(isPresented: $showingColumnCustomization) {
            ColumnCustomizationView()
        }
        .sheet(isPresented: $showingTaskDefaults) {
            TaskDefaultsView()
        }
        .sheet(isPresented: $showingPerformanceSettings) {
            PerformanceSettingsView()
        }
    }
    
    // MARK: - View Sections
    
    private var boardBehaviorSection: some View {
        Section("Board Behavior") {
            Toggle("Auto-refresh from server", isOn: $bindableSettingsManager.kanban.autoRefresh)
                .onChange(of: settingsManager.kanban.autoRefresh) { _, enabled in
                    handleAutoRefreshToggle(enabled)
                }
            
            if settingsManager.kanban.autoRefresh {
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Text("Refresh Interval")
                        Spacer()
                        Text("\(Int(settingsManager.kanban.refreshInterval))s")
                            .foregroundColor(.secondary)
                    }
                    
                    Slider(
                        value: $bindableSettingsManager.kanban.refreshInterval,
                        in: 10...300,
                        step: 10
                    )
                    
                    Text("How often to check for updates from the server")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                .padding(.vertical, 4)
            }
            
            Toggle("Show task statistics", isOn: $bindableSettingsManager.kanban.showStatistics)
            
            Toggle("Compact mode", isOn: $bindableSettingsManager.kanban.compactMode)
            
            Toggle("Enable animations", isOn: $bindableSettingsManager.kanban.enableAnimations)
        }
    }
    
    private var columnsSection: some View {
        Section("Columns Configuration") {
            Toggle("Show task counts", isOn: $bindableSettingsManager.kanban.showColumnTaskCounts)
            
            Toggle("Allow column customization", isOn: $bindableSettingsManager.kanban.enableColumnCustomization)
            
            Button(action: { showingColumnCustomization = true }) {
                SettingsRow(
                    icon: "rectangle.3.group",
                    iconColor: .blue,
                    title: "Customize Columns",
                    subtitle: "Edit column names and order"
                )
            }
            .buttonStyle(.plain)
            .disabled(!settingsManager.kanban.enableColumnCustomization)
            
            VStack(alignment: .leading, spacing: 8) {
                Text("Current Column Order")
                    .font(.subheadline)
                    .fontWeight(.medium)
                
                HStack {
                    ForEach(settingsManager.kanban.columnOrder, id: \.self) { column in
                        Text(column.capitalized)
                            .font(.caption)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 4)
                            .background(Color.blue.opacity(0.1))
                            .foregroundColor(.blue)
                            .cornerRadius(6)
                    }
                    
                    Spacer()
                }
            }
            .padding(.vertical, 4)
        }
    }
    
    private var taskManagementSection: some View {
        Section("Task Management") {
            Toggle("Voice task creation", isOn: $bindableSettingsManager.kanban.enableVoiceTaskCreation)
            
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Voice task creation")
                    Text("Enable voice commands like 'Create task: Fix login bug'")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                Spacer()
            }
            .padding(.vertical, 4)
            
            Toggle("Show task IDs", isOn: $bindableSettingsManager.kanban.showTaskIds)
            
            HStack {
                Text("Default Priority")
                Spacer()
                Picker("Priority", selection: $bindableSettingsManager.kanban.defaultTaskPriority) {
                    Text("Low").tag("low")
                    Text("Medium").tag("medium")
                    Text("High").tag("high")
                    Text("Critical").tag("critical")
                }
                .pickerStyle(.menu)
            }
            
            Toggle("Auto-assign tasks", isOn: $bindableSettingsManager.kanban.autoAssignTasks)
            
            Toggle("Task notifications", isOn: $bindableSettingsManager.kanban.enableTaskNotifications)
            
            Button(action: { showingTaskDefaults = true }) {
                SettingsRow(
                    icon: "doc.badge.plus",
                    iconColor: .green,
                    title: "Default Task Settings",
                    subtitle: "Configure new task defaults"
                )
            }
            .buttonStyle(.plain)
        }
    }
    
    private var performanceSection: some View {
        Section("Performance") {
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Text("Max Tasks Per Column")
                    Spacer()
                    Text("\(settingsManager.kanban.maxTasksPerColumn)")
                        .foregroundColor(.secondary)
                }
                
                Slider(
                    value: Binding(
                        get: { Double(bindableSettingsManager.kanban.maxTasksPerColumn) },
                        set: { newValue in
                            bindableSettingsManager.kanban.maxTasksPerColumn = Int(newValue)
                        }
                    ),
                    in: 50...500,
                    step: 25
                )
                
                Text("Limit tasks displayed per column for better performance")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            .padding(.vertical, 4)
            
            Toggle("Infinite scroll", isOn: $bindableSettingsManager.kanban.enableInfiniteScroll)
            
            Toggle("Prefetch task details", isOn: $bindableSettingsManager.kanban.prefetchTaskDetails)
            
            Button(action: { showingPerformanceSettings = true }) {
                SettingsRow(
                    icon: "speedometer",
                    iconColor: .orange,
                    title: "Advanced Performance",
                    subtitle: "Memory and rendering optimizations"
                )
            }
            .buttonStyle(.plain)
        }
    }
    
    private var integrationSection: some View {
        Section("Integration & Sync") {
            Toggle("Sync with backend", isOn: $bindableSettingsManager.kanban.syncWithBackend)
                .onChange(of: settingsManager.kanban.syncWithBackend) { _, enabled in
                    handleSyncToggle(enabled)
                }
            
            Toggle("Offline mode", isOn: $bindableSettingsManager.kanban.offlineModeEnabled)
            
            HStack {
                Text("Conflict Resolution")
                Spacer()
                Picker("Resolution", selection: $bindableSettingsManager.kanban.conflictResolution) {
                    Text("Manual").tag("manual")
                    Text("Auto-merge").tag("auto-merge")
                    Text("Server wins").tag("server-wins")
                    Text("Local wins").tag("local-wins")
                }
                .pickerStyle(.menu)
            }
            
            VStack(alignment: .leading, spacing: 8) {
                Text("Sync Status")
                    .font(.subheadline)
                    .fontWeight(.medium)
                
                HStack {
                    Image(systemName: syncStatusIcon)
                        .foregroundColor(syncStatusColor)
                    
                    Text(syncStatusText)
                        .foregroundColor(.secondary)
                    
                    Spacer()
                    
                    if settingsManager.kanban.syncWithBackend {
                        Button("Sync Now") {
                            forceSyncWithBackend()
                        }
                        .font(.caption)
                        .buttonStyle(.bordered)
                        .controlSize(.mini)
                    }
                }
            }
            .padding(.vertical, 4)
        }
    }
    
    private var advancedSection: some View {
        Section("Advanced") {
            NavigationLink("Workflow Rules") {
                WorkflowRulesView()
            }
            
            NavigationLink("Custom Fields") {
                CustomFieldsView()
            }
            
            Button(action: { exportKanbanSettings() }) {
                SettingsRow(
                    icon: "square.and.arrow.up",
                    iconColor: .blue,
                    title: "Export Board Configuration",
                    subtitle: "Save current settings for backup"
                )
            }
            .buttonStyle(.plain)
            
            Button(action: { clearKanbanCache() }) {
                SettingsRow(
                    icon: "trash.circle",
                    iconColor: .orange,
                    title: "Clear Cache",
                    subtitle: "Clear cached tasks and refresh from server"
                )
            }
            .buttonStyle(.plain)
            
            Button(action: { resetKanbanSettings() }) {
                SettingsRow(
                    icon: "arrow.clockwise",
                    iconColor: .red,
                    title: "Reset to Defaults",
                    subtitle: "Restore factory Kanban settings"
                )
            }
            .buttonStyle(.plain)
        }
    }
    
    // MARK: - Helper Properties
    
    private var syncStatusIcon: String {
        if settingsManager.kanban.syncWithBackend {
            return settingsManager.kanban.offlineModeEnabled ? "wifi.slash" : "checkmark.circle.fill"
        } else {
            return "xmark.circle.fill"
        }
    }
    
    private var syncStatusColor: Color {
        if settingsManager.kanban.syncWithBackend {
            return settingsManager.kanban.offlineModeEnabled ? .orange : .green
        } else {
            return .red
        }
    }
    
    private var syncStatusText: String {
        if !settingsManager.kanban.syncWithBackend {
            return "Sync disabled"
        } else if settingsManager.kanban.offlineModeEnabled {
            return "Offline mode - will sync when connected"
        } else {
            return "Connected and syncing"
        }
    }
    
    // MARK: - Actions
    
    private func handleAutoRefreshToggle(_ enabled: Bool) {
        if enabled {
            // Start auto-refresh service
            startKanbanAutoRefresh()
        } else {
            // Stop auto-refresh service
            stopKanbanAutoRefresh()
        }
    }
    
    private func handleSyncToggle(_ enabled: Bool) {
        if enabled {
            // Enable backend synchronization
            enableKanbanSync()
        } else {
            // Disable backend synchronization
            disableKanbanSync()
        }
    }
    
    private func startKanbanAutoRefresh() {
        // Implementation would integrate with KanbanService
        print("Starting Kanban auto-refresh with interval: \(settingsManager.kanban.refreshInterval)s")
    }
    
    private func stopKanbanAutoRefresh() {
        // Implementation would integrate with KanbanService
        print("Stopping Kanban auto-refresh")
    }
    
    private func enableKanbanSync() {
        // Implementation would integrate with backend sync service
        print("Enabling Kanban backend sync")
    }
    
    private func disableKanbanSync() {
        // Implementation would integrate with backend sync service
        print("Disabling Kanban backend sync")
    }
    
    private func forceSyncWithBackend() {
        // Force immediate sync with backend
        print("Forcing Kanban sync with backend")
    }
    
    private func exportKanbanSettings() {
        // Export Kanban configuration
        print("Exporting Kanban settings")
    }
    
    private func clearKanbanCache() {
        // Clear cached Kanban data
        print("Clearing Kanban cache")
    }
    
    private func resetKanbanSettings() {
        // Reset Kanban settings to defaults
        settingsManager.resetSettings(KanbanSettings.self)
    }
}

// MARK: - Supporting Views

struct ColumnCustomizationView: View {
    @Environment(\.dismiss) private var dismiss
    @StateObject private var settingsManager = SettingsManager.shared
    @Bindable private var bindableSettingsManager: SettingsManager = SettingsManager.shared
    @State private var columnOrder: [String] = []
    @State private var newColumnName = ""
    @State private var showingAddColumn = false
    
    var body: some View {
        NavigationView {
            List {
                Section("Column Order") {
                    ForEach(columnOrder, id: \.self) { column in
                        HStack {
                            Image(systemName: "line.3.horizontal")
                                .foregroundColor(.secondary)
                            
                            Text(column.capitalized)
                            
                            Spacer()
                            
                            Button("Remove") {
                                removeColumn(column)
                            }
                            .font(.caption)
                            .foregroundColor(.red)
                        }
                    }
                    .onMove(perform: moveColumns)
                }
                
                Section {
                    Button("Add Column") {
                        showingAddColumn = true
                    }
                }
            }
            .navigationTitle("Customize Columns")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
                
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Save") {
                        saveColumnOrder()
                        dismiss()
                    }
                }
            }
            .onAppear {
                columnOrder = settingsManager.kanban.columnOrder
            }
            .alert("Add Column", isPresented: $showingAddColumn) {
                TextField("Column Name", text: $newColumnName)
                Button("Add") {
                    addColumn()
                }
                Button("Cancel", role: .cancel) { }
            }
        }
    }
    
    private func moveColumns(from source: IndexSet, to destination: Int) {
        columnOrder.move(fromOffsets: source, toOffset: destination)
    }
    
    private func removeColumn(_ column: String) {
        columnOrder.removeAll { $0 == column }
    }
    
    private func addColumn() {
        if !newColumnName.isEmpty {
            columnOrder.append(newColumnName.lowercased().replacingOccurrences(of: " ", with: "_"))
            newColumnName = ""
        }
    }
    
    private func saveColumnOrder() {
        bindableSettingsManager.kanban.columnOrder = columnOrder
    }
}

struct TaskDefaultsView: View {
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            List {
                Section("Default Task Settings") {
                    Text("Task default configuration")
                }
            }
            .navigationTitle("Task Defaults")
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

@available(iOS 18.0, macOS 14.0, *)
struct KanbanPerformanceSettingsView: View {
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            List {
                Section("Performance Optimizations") {
                    Text("Advanced performance settings")
                }
            }
            .navigationTitle("Performance")
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

struct WorkflowRulesView: View {
    var body: some View {
        List {
            Section("Workflow Rules") {
                Text("Configure automatic task transitions")
            }
        }
        .navigationTitle("Workflow Rules")
    }
}

struct CustomFieldsView: View {
    var body: some View {
        List {
            Section("Custom Fields") {
                Text("Add custom task fields")
            }
        }
        .navigationTitle("Custom Fields")
    }
}

// MARK: - Preview

#Preview {
    NavigationView {
        KanbanSettingsView()
    }
}
