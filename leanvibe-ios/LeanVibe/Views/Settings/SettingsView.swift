import SwiftUI

// Ensure ArchitectureViewerSettingsView is available
// (The implementation is in ArchitectureViewerSettingsView.swift)

/// Main Settings view providing comprehensive configuration for all LeanVibe features
/// Built by KAPPA to configure Voice, Kanban, Architecture, and other systems
@available(iOS 18.0, macOS 14.0, *)
struct SettingsView: View {
    
    // MARK: - Properties
    
    @StateObject private var settingsManager = SettingsManager.shared
    @ObservedObject var webSocketService: WebSocketService
    @State private var showingAbout = false
    @State private var showingExportImport = false
    
    // MARK: - Body
    
    var body: some View {
        NavigationView {
            List {
                // Voice & Speech Section
                voiceSettingsSection
                
                // Task Management Section
                taskManagementSection
                
                // Connection & Sync Section
                connectionSection
                
                // App Preferences Section
                appPreferencesSection
                
                // Advanced Features Section
                advancedFeaturesSection
                
                // Support & About Section
                supportSection
            }
            .navigationTitle("Settings")
            .toolbar {
                ToolbarItem(placement: .automatic) {
                    toolbarMenu
                }
            }
        }
        .sheet(isPresented: $showingAbout) {
            AboutView()
        }
        .sheet(isPresented: $showingExportImport) {
            SettingsExportImportView()
        }
    }
    
    // MARK: - View Sections
    
    private var voiceSettingsSection: some View {
        Section("Voice & Speech") {
            NavigationLink(destination: VoiceSettingsView()) {
                SettingsRow(
                    icon: "mic.fill",
                    iconColor: Color(.systemBlue),
                    title: "Voice Commands",
                    subtitle: settingsManager.voice.autoStopListening ? "Hey LeanVibe enabled" : "Disabled"
                )
            }
            
            NavigationLink(destination: WakePhraseSettingsView()) {
                SettingsRow(
                    icon: "waveform",
                    iconColor: Color(.systemGreen),
                    title: "Wake Phrase Configuration",
                    subtitle: "\"\(settingsManager.voice.wakeWord)\""
                )
            }
            
            NavigationLink(destination: SpeechSettingsView()) {
                SettingsRow(
                    icon: "bubble.left.and.bubble.right",
                    iconColor: Color(.systemOrange),
                    title: "Speech Recognition",
                    subtitle: "Default"
                )
            }
            
            NavigationLink(destination: VoiceTestView()) {
                SettingsRow(
                    icon: "testtube.2",
                    iconColor: Color(.systemPurple),
                    title: "Voice Testing",
                    subtitle: "Test voice recognition"
                )
            }
        }
    }
    
    private var taskManagementSection: some View {
        Section("Task Management") {
            NavigationLink(destination: KanbanSettingsView()) {
                SettingsRow(
                    icon: "rectangle.3.offgrid",
                    iconColor: Color(.systemIndigo),
                    title: "Kanban Preferences",
                    subtitle: "Auto-refresh enabled"
                )
            }
            
            NavigationLink(destination: TaskNotificationSettingsView()) {
                SettingsRow(
                    icon: "bell.badge",
                    iconColor: Color(.systemRed),
                    title: "Task Notifications",
                    subtitle: "Enabled"
                )
            }
            
            // TODO: Implement MetricsSettingsView - currently placeholder
            /*
            NavigationLink(destination: MetricsSettingsView()) {
                SettingsRow(
                    icon: "chart.bar.fill",
                    iconColor: .teal,
                    title: "Productivity Metrics",
                    subtitle: "Visible"
                )
            }
            */
            
            // TODO: Implement TaskCreationSettingsView - currently placeholder
            /*
            NavigationLink(destination: TaskCreationSettingsView()) {
                SettingsRow(
                    icon: "plus.square.fill",
                    iconColor: .mint,
                    title: "Task Creation",
                    subtitle: "Default settings & quick actions"
                )
            }
            */
        }
    }
    
    private var connectionSection: some View {
        Section("Connection & Sync") {
            NavigationLink(destination: ServerSettingsView()) {
                SettingsRow(
                    icon: "server.rack",
                    iconColor: Color(.systemTeal),
                    title: "Server Configuration",
                    subtitle: connectionStatusText
                )
            }
            
            // TODO: Re-enable SyncSettingsView after fixing BackendSettingsService
            /*
            NavigationLink(destination: SyncSettingsView()) {
                SettingsRow(
                    icon: "arrow.triangle.2.circlepath",
                    iconColor: Color(.systemBlue),
                    title: "Sync Preferences",
                    subtitle: "Background sync on"
                )
            }
            */
            
            // TODO: Implement OfflineSettingsView - currently placeholder
            /*
            NavigationLink(destination: OfflineSettingsView()) {
                SettingsRow(
                    icon: "wifi.slash",
                    iconColor: .orange,
                    title: "Offline Mode",
                    subtitle: "Enabled"
                )
            }
            */
            
            NavigationLink(destination: NetworkDiagnosticsView()) {
                SettingsRow(
                    icon: "network",
                    iconColor: Color(.systemGreen),
                    title: "Network Diagnostics",
                    subtitle: "Connection testing & troubleshooting"
                )
            }
        }
    }
    
    private var appPreferencesSection: some View {
        Section("Appearance & Behavior") {
            // TODO: Implement InterfaceSettingsView - currently placeholder
            /*
            NavigationLink(destination: InterfaceSettingsView()) {
                SettingsRow(
                    icon: "paintbrush.fill",
                    iconColor: .pink,
                    title: "Interface",
                    subtitle: "Default theme"
                )
            }
            */
            
            NavigationLink(destination: AccessibilitySettingsView()) {
                SettingsRow(
                    icon: "accessibility",
                    iconColor: Color(.systemBlue),
                    title: "Accessibility",
                    subtitle: "Default"
                )
            }
            
            NavigationLink(destination: NotificationSettingsView()) {
                SettingsRow(
                    icon: "bell.fill",
                    iconColor: Color(.systemRed),
                    title: "Notifications",
                    subtitle: "Push enabled"
                )
            }
            
            // TODO: Implement PerformanceSettingsView - currently placeholder
            /*
            NavigationLink(destination: PerformanceSettingsView()) {
                SettingsRow(
                    icon: "speedometer",
                    iconColor: .yellow,
                    title: "Performance",
                    subtitle: "Animations & responsiveness"
                )
            }
            */
        }
    }
    
    private var advancedFeaturesSection: some View {
        Section("Advanced Features") {
            // TODO: Fix ErrorHistoryView and GlobalErrorManager resolution
            // NavigationLink(destination: ErrorHistoryView(errorManager: GlobalErrorManager.shared)) {
            //     SettingsRow(
            //         icon: "exclamationmark.triangle.fill",
            //         iconColor: .orange,
            //         title: "Error History",
            //         subtitle: "\(GlobalErrorManager.shared.errorHistory.count) errors logged"
            //     )
            // }
            
            // TODO: Fix RetryMonitorView and RetryManager resolution
            // NavigationLink(destination: RetryMonitorView(retryManager: RetryManager.shared)) {
            //     SettingsRow(
            //         icon: "arrow.clockwise.circle.fill",
            //         iconColor: .blue,
            //         title: "Retry Monitor",
            //         subtitle: "\(RetryManager.shared.activeRetries.count) active retries"
            //     )
            // }
            
            // TODO: Implement DeveloperSettingsView - currently placeholder
            /*
            NavigationLink(destination: DeveloperSettingsView()) {
                SettingsRow(
                    icon: "hammer.fill",
                    iconColor: .gray,
                    title: "Developer Options",
                    subtitle: "Disabled"
                )
            }
            */
            
            NavigationLink(destination: ArchitectureViewerSettingsView()) {
                SettingsRow(
                    icon: "network",
                    iconColor: Color(.systemPurple),
                    title: "Architecture Viewer",
                    subtitle: architectureStatusText
                )
            }
            
            // TODO: Implement IntegrationSettingsView - currently placeholder
            /*
            NavigationLink(destination: IntegrationSettingsView()) {
                SettingsRow(
                    icon: "link",
                    iconColor: .indigo,
                    title: "System Integration",
                    subtitle: "Cross-system communication"
                )
            }
            */
            
            // TODO: Implement BackupRestoreView - currently placeholder
            /*
            NavigationLink(destination: BackupRestoreView()) {
                SettingsRow(
                    icon: "externaldrive.fill",
                    iconColor: .brown,
                    title: "Backup & Restore",
                    subtitle: "Settings backup & migration"
                )
            }
            */
        }
    }
    
    private var supportSection: some View {
        Section("Support & About") {
            // TODO: Implement HelpView - currently placeholder
            /*
            NavigationLink(destination: HelpView()) {
                SettingsRow(
                    icon: "questionmark.circle.fill",
                    iconColor: .green,
                    title: "Help & Documentation",
                    subtitle: "Guides & tutorials"
                )
            }
            */
            
            Button(action: {
                showingAbout.toggle()
            }) {
                SettingsRow(
                    icon: "info.circle.fill",
                    iconColor: Color(.systemBlue),
                    title: "About LeanVibe",
                    subtitle: "Version \(Bundle.main.appVersion)"
                )
            }
            
            // TODO: Implement PrivacyPolicyView - currently placeholder
            /*
            NavigationLink(destination: PrivacyPolicyView()) {
                SettingsRow(
                    icon: "lock.shield.fill",
                    iconColor: .gray,
                    title: "Privacy Policy",
                    subtitle: "Your data, your rights"
                )
            }
            */
        }
    }
    
    private var toolbarMenu: some View {
        Menu {
            Button(action: {
                showingExportImport.toggle()
            }) {
                Label("Export/Import Settings", systemImage: "arrow.up.arrow.down.circle")
            }
            
            Button(role: .destructive, action: {
                settingsManager.resetAllSettings()
            }) {
                Label("Reset All Settings", systemImage: "trash")
            }
        } label: {
            Image(systemName: "ellipsis.circle")
        }
    }
    
    // MARK: - Helper Properties
    
    private var connectionStatusText: String {
        webSocketService.isConnected ? "Connected" : "Disconnected"
    }
    
    private var accessibilityStatusText: String {
        "Default"
    }
    
    private var architectureStatusText: String {
        let theme = settingsManager.architecture.diagramTheme.capitalized
        let quality = settingsManager.architecture.renderQuality.capitalized
        return "\(theme) theme, \(quality) quality"
    }
}

// MARK: - Helper Components

@available(iOS 18.0, macOS 14.0, *)
struct SettingsRow: View {
    let icon: String
    let iconColor: Color
    let title: String
    let subtitle: String
    
    var body: some View {
        HStack(spacing: 15) {
            Image(systemName: icon)
                .font(.title2)
                .foregroundColor(.white)
                .frame(width: 40, height: 40)
                .background(iconColor)
                .cornerRadius(8)
            
            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(.headline)
                Text(subtitle)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .padding(.vertical, 8)
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct AboutView: View {
    var body: some View {
        Text("About LeanVibe")
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct SettingsExportImportView: View {
    var body: some View {
        Text("Export/Import Settings")
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct WakePhraseSettingsView: View {
    var body: some View {
        Text("Wake Phrase Settings")
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct SpeechSettingsView: View {
    var body: some View {
        Text("Speech Settings")
    }
}



@available(iOS 18.0, macOS 14.0, *)
struct TaskNotificationSettingsView: View {
    var body: some View {
        Text("Task Notification Settings")
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct MetricsSettingsView: View {
    var body: some View {
        Text("Metrics Settings")
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct TaskCreationSettingsView: View {
    var body: some View {
        Text("Task Creation Settings")
    }
}

// TODO: Re-enable after fixing BackendSettingsService target membership
/*
@available(iOS 18.0, macOS 14.0, *)
struct SyncSettingsView: View {
    @StateObject private var settingsManager = SettingsManager.shared
    // TODO: Fix BackendSettingsService target membership
    // @StateObject private var backendService = BackendSettingsService.shared
    @Bindable private var bindableSettingsManager: SettingsManager = SettingsManager.shared
    @State private var isSyncing = false
    @State private var showingResetConfirmation = false
    
    var body: some View {
        List {
            // Backend Status Section
            Section("Backend Status") {
                HStack {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Backend Connection")
                            .fontWeight(.medium)
                        
                        HStack {
                            Circle()
                                .fill(backendService.isAvailable ? .green : .red)
                                .frame(width: 8, height: 8)
                            
                            Text(backendService.isAvailable ? "Connected" : "Disconnected")
                                .foregroundColor(.secondary)
                                .font(.caption)
                        }
                    }
                    
                    Spacer()
                    
                    Button(backendService.isAvailable ? "Sync Now" : "Retry") {
                        Task {
                            await syncWithBackend()
                        }
                    }
                    .disabled(isSyncing)
                    .buttonStyle(.bordered)
                    .controlSize(.small)
                }
                
                if let lastSync = settingsManager.lastSyncDate {
                    Text("Last sync: \(formatDate(lastSync))")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                
                if let error = backendService.lastError {
                    Text("Error: \(error)")
                        .font(.caption)
                        .foregroundColor(.red)
                        .padding(.top, 4)
                }
            }
            
            // Sync Preferences
            Section("Sync Preferences") {
                Toggle("Auto-Sync Settings", isOn: $bindableSettingsManager.isBackendSyncEnabled)
                    .onChange(of: settingsManager.isBackendSyncEnabled) { _, enabled in
                        if enabled {
                            Task {
                                await syncWithBackend()
                            }
                        }
                    }
                
                if settingsManager.isBackendSyncEnabled {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Automatic synchronization keeps your settings consistent across devices and ensures they're backed up to your LeanVibe backend.")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    .padding(.vertical, 4)
                }
            }
            
            // Sync Status
            Section("Sync Status") {
                HStack {
                    Text("Current Status")
                    Spacer()
                    Text(syncStatusText)
                        .foregroundColor(syncStatusColor)
                        .font(.caption)
                }
                
                if case .syncing = settingsManager.syncStatus {
                    HStack {
                        ProgressView()
                            .controlSize(.small)
                        Text("Synchronizing...")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }
            }
            
            // Manual Actions
            Section("Manual Actions") {
                Button(action: {
                    Task {
                        await forceSyncFromBackend()
                    }
                }) {
                    SettingsRow(
                        icon: "arrow.down.circle",
                        iconColor: .blue,
                        title: "Pull from Backend",
                        subtitle: "Download latest settings from server"
                    )
                }
                .buttonStyle(.plain)
                .disabled(isSyncing || !backendService.isAvailable)
                
                Button(action: {
                    Task {
                        await pushToBackend()
                    }
                }) {
                    SettingsRow(
                        icon: "arrow.up.circle",
                        iconColor: .green,
                        title: "Push to Backend",
                        subtitle: "Upload current settings to server"
                    )
                }
                .buttonStyle(.plain)
                .disabled(isSyncing || !backendService.isAvailable)
                
                Button(action: {
                    showingResetConfirmation = true
                }) {
                    SettingsRow(
                        icon: "arrow.clockwise.circle",
                        iconColor: .orange,
                        title: "Reset to Backend Defaults",
                        subtitle: "Restore settings from server"
                    )
                }
                .buttonStyle(.plain)
                .disabled(isSyncing || !backendService.isAvailable)
            }
        }
        .navigationTitle("Sync Settings")
        .navigationBarTitleDisplayMode(.inline)
        .confirmationDialog(
            "Reset to Backend Defaults",
            isPresented: $showingResetConfirmation,
            titleVisibility: .visible
        ) {
            Button("Reset All Settings", role: .destructive) {
                Task {
                    await resetToBackendDefaults()
                }
            }
            Button("Cancel", role: .cancel) {}
        } message: {
            Text("This will replace all local settings with the latest values from your backend. This action cannot be undone.")
        }
    }
    
    private var syncStatusText: String {
        switch settingsManager.syncStatus {
        case .idle:
            return "Idle"
        case .syncing:
            return "Syncing..."
        case .synced(let date):
            return "Synced \(formatTime(date))"
        case .failed:
            return "Failed"
        }
    }
    
    private var syncStatusColor: Color {
        switch settingsManager.syncStatus {
        case .idle:
            return .secondary
        case .syncing:
            return .blue
        case .synced:
            return .green
        case .failed:
            return .red
        }
    }
    
    private func syncWithBackend() async {
        isSyncing = true
        await settingsManager.syncWithBackendIfAvailable()
        isSyncing = false
    }
    
    private func forceSyncFromBackend() async {
        isSyncing = true
        do {
            _ = try await backendService.refreshSettings()
            await settingsManager.syncWithBackendIfAvailable()
        } catch {
            print("Failed to force sync: \(error)")
        }
        isSyncing = false
    }
    
    private func pushToBackend() async {
        isSyncing = true
        do {
            try await settingsManager.pushSettingsToBackend()
        } catch {
            print("Failed to push to backend: \(error)")
        }
        isSyncing = false
    }
    
    private func resetToBackendDefaults() async {
        isSyncing = true
        settingsManager.resetAll()
        isSyncing = false
    }
    
    private func formatDate(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateStyle = .short
        formatter.timeStyle = .short
        return formatter.string(from: date)
    }
    
    private func formatTime(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.timeStyle = .short
        return formatter.string(from: date)
    }
}
*/

@available(iOS 18.0, macOS 14.0, *)
struct OfflineSettingsView: View {
    var body: some View {
        Text("Offline Settings")
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct NetworkDiagnosticsView: View {
    var body: some View {
        Text("Network Diagnostics")
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct InterfaceSettingsView: View {
    var body: some View {
        Text("Interface Settings")
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct PerformanceSettingsView: View {
    var body: some View {
        Text("Performance Settings")
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct DeveloperSettingsView: View {
    var body: some View {
        Text("Developer Settings")
    }
}


@available(iOS 18.0, macOS 14.0, *)
struct ArchitectureViewerSettingsView: View {
    @StateObject private var settingsManager = SettingsManager.shared
    @Bindable private var bindableSettingsManager: SettingsManager = SettingsManager.shared
    @State private var showingResetConfirmation = false

    var body: some View {
        List {
            // Diagram Rendering Section
            Section("Diagram Rendering") {
                HStack {
                    Text("Theme")
                    Spacer()
                    Picker("Theme", selection: $bindableSettingsManager.architecture.diagramTheme) {
                        Text("Default").tag("default")
                        Text("Dark").tag("dark")
                        Text("Forest").tag("forest")
                        Text("Neutral").tag("neutral")
                        Text("Base").tag("base")
                    }
                    .pickerStyle(.menu)
                }
                
                HStack {
                    Text("Layout")
                    Spacer()
                    Picker("Layout", selection: $bindableSettingsManager.architecture.diagramLayout) {
                        Text("Auto").tag("auto")
                        Text("Top to Bottom").tag("TB")
                        Text("Bottom to Top").tag("BT")
                        Text("Left to Right").tag("LR")
                        Text("Right to Left").tag("RL")
                    }
                    .pickerStyle(.menu)
                }
                
                HStack {
                    Text("Quality")
                    Spacer()
                    Picker("Quality", selection: $bindableSettingsManager.architecture.renderQuality) {
                        Text("High").tag("high")
                        Text("Medium").tag("medium")
                        Text("Low").tag("low")
                    }
                    .pickerStyle(.segmented)
                }
                
                Toggle("Enable Animations", isOn: $bindableSettingsManager.architecture.enableAnimations)
                Toggle("Show Node Labels", isOn: $bindableSettingsManager.architecture.showNodeLabels)
                Toggle("Show Edge Labels", isOn: $bindableSettingsManager.architecture.showEdgeLabels)
            }
            
            // Change Detection Section
            Section("Change Detection") {
                Toggle("Auto-Refresh", isOn: $bindableSettingsManager.architecture.autoRefreshEnabled)
                
                if settingsManager.architecture.autoRefreshEnabled {
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Text("Refresh Interval")
                            Spacer()
                            Text("\(Int(settingsManager.architecture.refreshInterval))s")
                                .foregroundColor(.secondary)
                        }
                        
                        Slider(
                            value: $bindableSettingsManager.architecture.refreshInterval,
                            in: 5...300,
                            step: 5
                        )
                    }
                    .padding(.vertical, 4)
                }
                
                Toggle("Change Notifications", isOn: $bindableSettingsManager.architecture.changeNotificationsEnabled)
                Toggle("Highlight Changes", isOn: $bindableSettingsManager.architecture.highlightChanges)
                
                HStack {
                    Text("Compare Mode")
                    Spacer()
                    Picker("Compare Mode", selection: $bindableSettingsManager.architecture.compareMode) {
                        Text("Side by Side").tag("side-by-side")
                        Text("Overlay").tag("overlay")
                        Text("Sequential").tag("sequential")
                    }
                    .pickerStyle(.menu)
                }
            }
            
            // Performance Section
            Section("Performance") {
                Toggle("Memory Optimization", isOn: $bindableSettingsManager.architecture.enableMemoryOptimization)
                
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Text("Cache Size")
                        Spacer()
                        Text("\(settingsManager.architecture.maxCacheSize) MB")
                            .foregroundColor(.secondary)
                    }
                    
                    Slider(
                        value: Binding(
                            get: { Double(settingsManager.architecture.maxCacheSize) },
                            set: { bindableSettingsManager.architecture.maxCacheSize = Int($0) }
                        ),
                        in: 10...200,
                        step: 10
                    )
                }
                .padding(.vertical, 4)
                
                Toggle("WebView Pooling", isOn: $bindableSettingsManager.architecture.enableWebViewPooling)
                Toggle("Performance Monitoring", isOn: $bindableSettingsManager.architecture.performanceMonitoringEnabled)
            }
            
            // Export & Sharing Section
            Section("Export & Sharing") {
                HStack {
                    Text("Default Export Format")
                    Spacer()
                    Picker("Export Format", selection: $bindableSettingsManager.architecture.defaultExportFormat) {
                        Text("Mermaid").tag("mermaid")
                        Text("SVG").tag("svg")
                        Text("PNG").tag("png")
                        Text("PDF").tag("pdf")
                    }
                    .pickerStyle(.menu)
                }
                
                Toggle("Include Metadata", isOn: $bindableSettingsManager.architecture.includeMetadataInExport)
                Toggle("Auto-Save Exports", isOn: $bindableSettingsManager.architecture.autoSaveExports)
            }
            
            // Advanced Features Section
            Section("Advanced Features") {
                Toggle("Diagram Versioning", isOn: $bindableSettingsManager.architecture.enableDiagramVersioning)
                Toggle("Collaborative Editing", isOn: $bindableSettingsManager.architecture.enableCollaborativeEditing)
                Toggle("Real-Time Sync", isOn: $bindableSettingsManager.architecture.enableRealTimeSync)
            }
            
            // Reset Section
            Section("Reset") {
                Button("Reset All Architecture Settings") {
                    showingResetConfirmation = true
                }
                .foregroundColor(.red)
            }
        }
        .navigationTitle("Architecture Viewer")
        .navigationBarTitleDisplayMode(.inline)
        .confirmationDialog(
            "Reset Architecture Settings",
            isPresented: $showingResetConfirmation,
            titleVisibility: .visible
        ) {
            Button("Reset All Settings", role: .destructive) {
                settingsManager.architecture = ArchitectureSettings()
            }
            Button("Cancel", role: .cancel) {}
        } message: {
            Text("This will reset all Architecture Viewer settings to their default values. This action cannot be undone.")
        }
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct IntegrationSettingsView: View {
    var body: some View {
        Text("Integration Settings")
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct BackupRestoreView: View {
    var body: some View {
        Text("Backup & Restore")
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct HelpView: View {
    var body: some View {
        Text("Help")
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct PrivacyPolicyView: View {
    var body: some View {
        Text("Privacy Policy")
    }
}

extension Bundle {
    var appVersion: String {
        (infoDictionary?["CFBundleShortVersionString"] as? String) ?? "1.0"
    }
}

// MARK: - Previews

struct SettingsView_Previews: PreviewProvider {
    static var previews: some View {
        SettingsView(webSocketService: WebSocketService())
    }
}