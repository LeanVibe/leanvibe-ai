import SwiftUI

/// Main Settings view providing comprehensive configuration for all LeanVibe features
/// Built by KAPPA to configure Voice, Kanban, Architecture, and other systems
@available(iOS 18.0, macOS 14.0, *)
struct SettingsView: View {
    
    // MARK: - Properties
    
    @Environment(\.settingsManager) private var settingsManager
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
                    iconColor: .blue,
                    title: "Voice Commands",
                    subtitle: settingsManager.voice.autoStopListening ? "Hey LeanVibe enabled" : "Disabled"
                )
            }
            
            NavigationLink(destination: WakePhraseSettingsView()) {
                SettingsRow(
                    icon: "waveform",
                    iconColor: .green,
                    title: "Wake Phrase Configuration",
                    subtitle: "\"\(settingsManager.voice.wakeWord)\""
                )
            }
            
            NavigationLink(destination: SpeechSettingsView()) {
                SettingsRow(
                    icon: "bubble.left.and.bubble.right",
                    iconColor: .orange,
                    title: "Speech Recognition",
                    subtitle: "Default"
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
                    icon: "rectangle.3.offgrid",
                    iconColor: .indigo,
                    title: "Kanban Preferences",
                    subtitle: "Auto-refresh enabled"
                )
            }
            
            NavigationLink(destination: TaskNotificationSettingsView()) {
                SettingsRow(
                    icon: "bell.badge",
                    iconColor: .red,
                    title: "Task Notifications",
                    subtitle: "Enabled"
                )
            }
            
            NavigationLink(destination: MetricsSettingsView()) {
                SettingsRow(
                    icon: "chart.bar.fill",
                    iconColor: .teal,
                    title: "Productivity Metrics",
                    subtitle: "Visible"
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
            NavigationLink(destination: ServerSettingsView()) {
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
                    subtitle: "Background sync on"
                )
            }
            
            NavigationLink(destination: OfflineSettingsView()) {
                SettingsRow(
                    icon: "wifi.slash",
                    iconColor: .orange,
                    title: "Offline Mode",
                    subtitle: "Enabled"
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
                    subtitle: "Default theme"
                )
            }
            
            /*
            NavigationLink(destination: AccessibilitySettingsView()) {
                SettingsRow(
                    icon: "accessibility",
                    iconColor: .blue,
                    title: "Accessibility",
                    subtitle: "Default"
                )
            }
            */
            
            NavigationLink(destination: NotificationSettingsView()) {
                SettingsRow(
                    icon: "bell.fill",
                    iconColor: .red,
                    title: "Notifications",
                    subtitle: "Push enabled"
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
                    subtitle: "Disabled"
                )
            }
            
            NavigationLink(destination: ArchitectureViewerSettingsView()) {
                SettingsRow(
                    icon: "network",
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
        Section("Support & About") {
            NavigationLink(destination: HelpView()) {
                SettingsRow(
                    icon: "questionmark.circle.fill",
                    iconColor: .green,
                    title: "Help & Documentation",
                    subtitle: "Guides & tutorials"
                )
            }
            
            Button(action: {
                showingAbout.toggle()
            }) {
                SettingsRow(
                    icon: "info.circle.fill",
                    iconColor: .blue,
                    title: "About LeanVibe",
                    subtitle: "Version \(Bundle.main.appVersion)"
                )
            }
            
            NavigationLink(destination: PrivacyPolicyView()) {
                SettingsRow(
                    icon: "lock.shield.fill",
                    iconColor: .gray,
                    title: "Privacy Policy",
                    subtitle: "Your data, your rights"
                )
            }
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
}

// MARK: - Helper Components

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

struct AboutView: View {
    var body: some View {
        Text("About LeanVibe")
    }
}

struct SettingsExportImportView: View {
    var body: some View {
        Text("Export/Import Settings")
    }
}

struct WakePhraseSettingsView: View {
    var body: some View {
        Text("Wake Phrase Settings")
    }
}

struct SpeechSettingsView: View {
    var body: some View {
        Text("Speech Settings")
    }
}



struct TaskNotificationSettingsView: View {
    var body: some View {
        Text("Task Notification Settings")
    }
}

struct MetricsSettingsView: View {
    var body: some View {
        Text("Metrics Settings")
    }
}

struct TaskCreationSettingsView: View {
    var body: some View {
        Text("Task Creation Settings")
    }
}

struct SyncSettingsView: View {
    var body: some View {
        Text("Sync Settings")
    }
}

struct OfflineSettingsView: View {
    var body: some View {
        Text("Offline Settings")
    }
}

struct NetworkDiagnosticsView: View {
    var body: some View {
        Text("Network Diagnostics")
    }
}

struct InterfaceSettingsView: View {
    var body: some View {
        Text("Interface Settings")
    }
}

struct PerformanceSettingsView: View {
    var body: some View {
        Text("Performance Settings")
    }
}

struct DeveloperSettingsView: View {
    var body: some View {
        Text("Developer Settings")
    }
}

struct ArchitectureViewerSettingsView: View {
    var body: some View {
        Text("Architecture Viewer Settings")
    }
}

struct IntegrationSettingsView: View {
    var body: some View {
        Text("Integration Settings")
    }
}

struct BackupRestoreView: View {
    var body: some View {
        Text("Backup & Restore")
    }
}

struct HelpView: View {
    var body: some View {
        Text("Help")
    }
}

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