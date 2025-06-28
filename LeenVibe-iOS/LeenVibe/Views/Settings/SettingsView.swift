import SwiftUI

/// Main Settings view providing comprehensive configuration for all LeenVibe features
/// Built by KAPPA to configure Voice, Kanban, Architecture, and other systems
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
                ToolbarItem(placement: .navigationBarTrailing) {
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
                    iconColor: .blue,
                    title: "Voice Commands",
                    subtitle: settingsManager.voiceSettings.wakePhraseEnabled ? "Hey LeenVibe enabled" : "Disabled"
                )
            }
            
            NavigationLink(destination: WakePhraseSettingsView()) {
                SettingsRow(
                    icon: "waveform",
                    iconColor: .green,
                    title: "Wake Phrase Configuration",
                    subtitle: "\"\(settingsManager.voiceSettings.wakePhrasePhrase)\""
                )
            }
            
            NavigationLink(destination: SpeechSettingsView()) {
                SettingsRow(
                    icon: "bubble.left.and.bubble.right",
                    iconColor: .orange,
                    title: "Speech Recognition",
                    subtitle: settingsManager.voiceSettings.recognitionLanguage
                )
            }
            
            NavigationLink(destination: VoiceTestView()) {
                SettingsRow(
                    icon: "testtube.2",
                    iconColor: .purple,
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
                    icon: "kanban",
                    iconColor: .indigo,
                    title: "Kanban Preferences",
                    subtitle: settingsManager.kanbanSettings.autoRefresh ? "Auto-refresh enabled" : "Manual refresh"
                )
            }
            
            NavigationLink(destination: TaskNotificationSettingsView()) {
                SettingsRow(
                    icon: "bell.badge",
                    iconColor: .red,
                    title: "Task Notifications",
                    subtitle: settingsManager.notificationSettings.taskNotificationsEnabled ? "Enabled" : "Disabled"
                )
            }
            
            NavigationLink(destination: MetricsSettingsView()) {
                SettingsRow(
                    icon: "chart.bar.fill",
                    iconColor: .teal,
                    title: "Productivity Metrics",
                    subtitle: settingsManager.kanbanSettings.showStatistics ? "Visible" : "Hidden"
                )
            }
            
            NavigationLink(destination: TaskCreationSettingsView()) {
                SettingsRow(
                    icon: "plus.square.fill",
                    iconColor: .mint,
                    title: "Task Creation",
                    subtitle: "Default settings & quick actions"
                )
            }
        }
    }
    
    private var connectionSection: some View {
        Section("Connection & Sync") {
            NavigationLink(destination: ServerSettingsView(webSocketService: webSocketService)) {
                SettingsRow(
                    icon: "server.rack",
                    iconColor: .cyan,
                    title: "Server Configuration",
                    subtitle: connectionStatusText
                )
            }
            
            NavigationLink(destination: SyncSettingsView()) {
                SettingsRow(
                    icon: "arrow.triangle.2.circlepath",
                    iconColor: .blue,
                    title: "Sync Preferences",
                    subtitle: settingsManager.connectionSettings.backgroundSyncEnabled ? "Background sync on" : "Manual sync"
                )
            }
            
            NavigationLink(destination: OfflineSettingsView()) {
                SettingsRow(
                    icon: "wifi.slash",
                    iconColor: .orange,
                    title: "Offline Mode",
                    subtitle: settingsManager.kanbanSettings.offlineModeEnabled ? "Enabled" : "Disabled"
                )
            }
            
            NavigationLink(destination: NetworkDiagnosticsView()) {
                SettingsRow(
                    icon: "network",
                    iconColor: .green,
                    title: "Network Diagnostics",
                    subtitle: "Connection testing & troubleshooting"
                )
            }
        }
    }
    
    private var appPreferencesSection: some View {
        Section("Appearance & Behavior") {
            NavigationLink(destination: InterfaceSettingsView()) {
                SettingsRow(
                    icon: "paintbrush.fill",
                    iconColor: .pink,
                    title: "Interface",
                    subtitle: settingsManager.appSettings.interfaceTheme.displayName + " theme"
                )
            }
            
            NavigationLink(destination: AccessibilitySettingsView()) {
                SettingsRow(
                    icon: "accessibility",
                    iconColor: .blue,
                    title: "Accessibility",
                    subtitle: accessibilityStatusText
                )
            }
            
            NavigationLink(destination: NotificationSettingsView()) {
                SettingsRow(
                    icon: "bell.fill",
                    iconColor: .red,
                    title: "Notifications",
                    subtitle: settingsManager.notificationSettings.pushNotificationsEnabled ? "Push enabled" : "In-app only"
                )
            }
            
            NavigationLink(destination: PerformanceSettingsView()) {
                SettingsRow(
                    icon: "speedometer",
                    iconColor: .yellow,
                    title: "Performance",
                    subtitle: "Animations & responsiveness"
                )
            }
        }
    }
    
    private var advancedFeaturesSection: some View {
        Section("Advanced Features") {
            NavigationLink(destination: DeveloperSettingsView()) {
                SettingsRow(
                    icon: "hammer.fill",
                    iconColor: .gray,
                    title: "Developer Options",
                    subtitle: settingsManager.appSettings.developerModeEnabled ? "Enabled" : "Disabled"
                )
            }
            
            NavigationLink(destination: ArchitectureViewerSettingsView()) {
                SettingsRow(
                    icon: "flowchart.box",
                    iconColor: .purple,
                    title: "Architecture Viewer",
                    subtitle: "Diagram preferences & rendering"
                )
            }
            
            NavigationLink(destination: IntegrationSettingsView()) {
                SettingsRow(
                    icon: "link",
                    iconColor: .indigo,
                    title: "System Integration",
                    subtitle: "Cross-system communication"
                )
            }
            
            NavigationLink(destination: BackupRestoreView()) {
                SettingsRow(
                    icon: "externaldrive.fill",
                    iconColor: .brown,
                    title: "Backup & Restore",
                    subtitle: "Settings backup & migration"
                )
            }
        }
    }
    
    private var supportSection: some View {
        Section("Support & Information") {
            NavigationLink(destination: HelpView()) {
                SettingsRow(
                    icon: "questionmark.circle.fill",
                    iconColor: .blue,
                    title: "Help & Tutorials",
                    subtitle: "User guides & feature tutorials"
                )
            }
            
            Button(action: { showingAbout = true }) {
                SettingsRow(
                    icon: "info.circle.fill",
                    iconColor: .gray,
                    title: "About LeenVibe",
                    subtitle: "Version info & credits"
                )
            }
            .buttonStyle(.plain)
            
            NavigationLink(destination: PrivacyPolicyView()) {
                SettingsRow(
                    icon: "hand.raised.fill",
                    iconColor: .orange,
                    title: "Privacy Policy",
                    subtitle: "Data handling & privacy"
                )
            }
            
            NavigationLink(destination: DiagnosticsView()) {
                SettingsRow(
                    icon: "stethoscope",
                    iconColor: .red,
                    title: "System Diagnostics",
                    subtitle: "Health checks & troubleshooting"
                )
            }
        }
    }
    
    private var toolbarMenu: some View {
        Menu {
            Button(action: { showingExportImport = true }) {
                Label("Export/Import Settings", systemImage: "arrow.up.arrow.down.circle")
            }
            
            Button(action: resetAllSettings) {
                Label("Reset All Settings", systemImage: "arrow.clockwise.circle")
            }
            
            Divider()
            
            Button(action: { settingsManager.saveAllSettings() }) {
                Label("Save Settings", systemImage: "square.and.arrow.down")
            }
        } label: {
            Image(systemName: "ellipsis.circle")
        }
    }
    
    // MARK: - Helper Properties
    
    private var connectionStatusText: String {
        if webSocketService.isConnected {
            return "Connected"
        } else if settingsManager.connectionSettings.serverURL.isEmpty {
            return "Not configured"
        } else {
            return "Disconnected"
        }
    }
    
    private var accessibilityStatusText: String {
        let settings = settingsManager.accessibilitySettings
        var features: [String] = []
        
        if settings.highContrastMode { features.append("High Contrast") }
        if settings.reduceMotion { features.append("Reduce Motion") }
        if settings.largeFontSize { features.append("Large Font") }
        
        return features.isEmpty ? "Standard" : features.joined(separator: ", ")
    }
    
    // MARK: - Actions
    
    private func resetAllSettings() {
        settingsManager.resetAllSettings()
    }
}

// MARK: - Settings Row Component

struct SettingsRow: View {
    let icon: String
    let iconColor: Color
    let title: String
    let subtitle: String
    
    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .font(.system(size: 16, weight: .medium))
                .foregroundColor(iconColor)
                .frame(width: 24, height: 24)
                .background(iconColor.opacity(0.15))
                .clipShape(RoundedRectangle(cornerRadius: 6))
            
            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(.body)
                    .fontWeight(.medium)
                
                Text(subtitle)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
        }
        .padding(.vertical, 4)
    }
}

// MARK: - Placeholder Views (to be implemented)

struct WakePhraseSettingsView: View {
    var body: some View {
        Text("Wake Phrase Settings")
            .navigationTitle("Wake Phrase")
    }
}

struct SpeechSettingsView: View {
    var body: some View {
        Text("Speech Settings")
            .navigationTitle("Speech Recognition")
    }
}

struct TaskNotificationSettingsView: View {
    var body: some View {
        Text("Task Notification Settings")
            .navigationTitle("Task Notifications")
    }
}

struct MetricsSettingsView: View {
    var body: some View {
        Text("Metrics Settings")
            .navigationTitle("Productivity Metrics")
    }
}

struct TaskCreationSettingsView: View {
    var body: some View {
        Text("Task Creation Settings")
            .navigationTitle("Task Creation")
    }
}

struct SyncSettingsView: View {
    var body: some View {
        Text("Sync Settings")
            .navigationTitle("Sync Preferences")
    }
}

struct OfflineSettingsView: View {
    var body: some View {
        Text("Offline Settings")
            .navigationTitle("Offline Mode")
    }
}

struct NetworkDiagnosticsView: View {
    var body: some View {
        Text("Network Diagnostics")
            .navigationTitle("Network Diagnostics")
    }
}

struct InterfaceSettingsView: View {
    var body: some View {
        Text("Interface Settings")
            .navigationTitle("Interface")
    }
}

struct PerformanceSettingsView: View {
    var body: some View {
        Text("Performance Settings")
            .navigationTitle("Performance")
    }
}

struct DeveloperSettingsView: View {
    var body: some View {
        Text("Developer Settings")
            .navigationTitle("Developer Options")
    }
}

struct ArchitectureViewerSettingsView: View {
    var body: some View {
        Text("Architecture Viewer Settings")
            .navigationTitle("Architecture Viewer")
    }
}

struct IntegrationSettingsView: View {
    var body: some View {
        Text("Integration Settings")
            .navigationTitle("System Integration")
    }
}

struct BackupRestoreView: View {
    var body: some View {
        Text("Backup & Restore")
            .navigationTitle("Backup & Restore")
    }
}

struct HelpView: View {
    var body: some View {
        Text("Help & Tutorials")
            .navigationTitle("Help")
    }
}

struct AboutView: View {
    var body: some View {
        NavigationView {
            VStack(spacing: 20) {
                Image(systemName: "brain.head.profile")
                    .font(.system(size: 64))
                    .foregroundColor(.blue)
                
                Text("LeenVibe")
                    .font(.largeTitle)
                    .fontWeight(.bold)
                
                Text("L3 Coding Agent Platform")
                    .font(.title3)
                    .foregroundColor(.secondary)
                
                Text("Version 1.0.0")
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                Spacer()
            }
            .padding()
            .navigationTitle("About")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Done") {
                        // Handle dismiss
                    }
                }
            }
        }
    }
}

struct PrivacyPolicyView: View {
    var body: some View {
        Text("Privacy Policy")
            .navigationTitle("Privacy Policy")
    }
}

struct DiagnosticsView: View {
    var body: some View {
        Text("System Diagnostics")
            .navigationTitle("Diagnostics")
    }
}

struct SettingsExportImportView: View {
    var body: some View {
        NavigationView {
            Text("Export/Import Settings")
                .navigationTitle("Backup Settings")
        }
    }
}

// MARK: - Preview

#Preview {
    SettingsView(webSocketService: WebSocketService())
}