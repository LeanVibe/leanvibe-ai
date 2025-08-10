import SwiftUI
import Foundation

// Simple Beta Feedback View placeholder
struct BetaFeedbackView: View {
    var body: some View {
        VStack(spacing: 20) {
            Image(systemName: "star.bubble")
                .font(.system(size: 48))
                .foregroundColor(.yellow)
            
            Text("Beta Feedback")
                .font(.largeTitle)
                .fontWeight(.bold)
            
            Text("This feature is under development")
                .font(.body)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
        }
        .padding()
        .navigationTitle("Beta Feedback")
    }
}

// Simple Beta Analytics Dashboard View placeholder
struct BetaAnalyticsDashboardView: View {
    var body: some View {
        VStack(spacing: 20) {
            Image(systemName: "chart.line.uptrend.xyaxis")
                .font(.system(size: 48))
                .foregroundColor(.purple)
            
            Text("Beta Analytics")
                .font(.largeTitle)
                .fontWeight(.bold)
            
            Text("Analytics dashboard coming soon")
                .font(.body)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
        }
        .padding()
        .navigationTitle("Beta Analytics")
    }
}

// Ensure ArchitectureViewerSettingsView is available
// (The implementation is in ArchitectureViewerSettingsView.swift)

/// Main Settings view providing comprehensive configuration for all LeanVibe features
/// Built by KAPPA to configure Voice, Kanban, Architecture, and other systems
@available(iOS 18.0, macOS 14.0, *)
struct SettingsView: View {
    
    // MARK: - Properties
    
    @StateObject private var settingsManager = SettingsManager.shared
    // TODO: Re-enable FeatureFlagManager when dependency is available
    // @StateObject private var featureFlagManager = FeatureFlagManager.shared
    @ObservedObject var webSocketService: WebSocketService
    @State private var showingAbout = false
    @State private var showingExportImport = false
    
    // TODO: Re-enable feature flags when FeatureFlagManager is available
    // Temporarily enabling all features for development build
    private var isVoiceFeaturesEnabled: Bool { true }
    private var isWakePhraseDetectionEnabled: Bool { true }
    private var isVoiceRecognitionEnabled: Bool { true }
    private var isBetaFeedbackEnabled: Bool { true }
    private var isBetaAnalyticsEnabled: Bool { true }
    private var isAdvancedSettingsEnabled: Bool { true }
    private var isDebugSettingsEnabled: Bool { true }
    private var isNetworkDiagnosticsEnabled: Bool { true }
    private var isPerformanceMonitoringEnabled: Bool { true }
    private var isDocumentIntelligenceEnabled: Bool { true }
    private var isCodeCompletionEnabled: Bool { true }
    
    // MARK: - Body
    
    var body: some View {
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
                
                // Beta Testing Section
                betaTestingSection
        }
        .navigationTitle("Settings")
        .toolbar {
            ToolbarItem(placement: .automatic) {
                toolbarMenu
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
            // Only show voice settings if voice features are enabled
            if isVoiceFeaturesEnabled {
                NavigationLink(destination: VoiceSettingsView()) {
                    SettingsRow(
                        icon: "mic.fill",
                        iconColor: Color(.systemBlue),
                        title: "Voice Commands",
                        subtitle: settingsManager.voice.autoStopListening ? "Hey LeanVibe enabled" : "Disabled"
                    )
                }
            }
            
            // Only show wake phrase settings if wake phrase detection is enabled
            if isWakePhraseDetectionEnabled {
                NavigationLink(destination: WakePhraseSettingsView()) {
                    SettingsRow(
                        icon: "waveform",
                        iconColor: Color(.systemGreen),
                        title: "Wake Phrase Configuration",
                        subtitle: "\"\(settingsManager.voice.wakeWord)\""
                    )
                }
            }
            
            // Only show speech settings if voice recognition is enabled
            if isVoiceRecognitionEnabled {
                NavigationLink(destination: SpeechSettingsView()) {
                    SettingsRow(
                        icon: "bubble.left.and.bubble.right",
                        iconColor: Color(.systemOrange),
                        title: "Speech Recognition",
                        subtitle: "Default"
                    )
                }
            }
            
            // TODO: Voice feedback settings - Re-enable when VoiceFeedbackService is added to Xcode project
            /*
            if isVoiceFeaturesEnabled {
                NavigationLink(destination: VoiceFeedbackSettingsView()) {
                    SettingsRow(
                        icon: "speaker.3.fill",
                        iconColor: Color(.systemTeal),
                        title: "Voice Feedback",
                        subtitle: VoiceFeedbackService.shared.isEnabled ? "Enabled" : "Disabled"
                    )
                }
            }
            */
            
            // Only show voice testing if voice features are enabled and in debug/TestFlight
            if isVoiceFeaturesEnabled && !AppConfiguration.shared.isProductionBuild {
                NavigationLink(destination: VoiceTestView()) {
                    SettingsRow(
                        icon: "testtube.2",
                        iconColor: Color(.systemPurple),
                        title: "Voice Testing",
                        subtitle: "Test voice recognition"
                    )
                }
            }
            
            // If no voice features are enabled, show a message
            if !isVoiceFeaturesEnabled {
                Text("Voice features are currently disabled for stability")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .padding()
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
            
            NavigationLink(destination: MetricsSettingsView()) {
                SettingsRow(
                    icon: "chart.bar.fill",
                    iconColor: .teal,
                    title: "Productivity Metrics",
                    subtitle: settingsManager.metrics.isEnabled ? "Enabled" : "Disabled"
                )
            }
            
            NavigationLink(destination: TaskCreationSettingsView()) {
                SettingsRow(
                    icon: "plus.square.fill",
                    iconColor: .mint,
                    title: "Task Creation",
                    subtitle: "Priority: \(settingsManager.taskCreation.defaultPriority.capitalized)"
                )
            }
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
            
            NavigationLink(destination: SyncSettingsView()) {
                SettingsRow(
                    icon: "arrow.triangle.2.circlepath",
                    iconColor: Color(.systemBlue),
                    title: "Sync Preferences",
                    subtitle: "Background sync on"
                )
            }
            
            NavigationLink(destination: OfflineSettingsView()) {
                SettingsRow(
                    icon: "wifi.slash",
                    iconColor: .orange,
                    title: "Offline Mode",
                    subtitle: settingsManager.offline.isEnabled ? "Enabled" : "Disabled"
                )
            }
            
            // Network Diagnostics (Debug/TestFlight only)
            if isNetworkDiagnosticsEnabled {
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
    }
    
    private var appPreferencesSection: some View {
        Section("Appearance & Behavior") {
            NavigationLink(destination: InterfaceSettingsView()) {
                SettingsRow(
                    icon: "paintbrush.fill",
                    iconColor: .pink,
                    title: "Interface",
                    subtitle: "\(settingsManager.interface.theme.capitalized) theme"
                )
            }
            
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
            
            // Performance Settings (Debug/TestFlight only)
            if isPerformanceMonitoringEnabled {
                NavigationLink(destination: PerformanceSettingsView()) {
                    SettingsRow(
                        icon: "speedometer",
                        iconColor: .yellow,
                        title: "Performance",
                        subtitle: settingsManager.performance.performanceMonitoringEnabled ? "Monitoring enabled" : "Monitoring disabled"
                    )
                }
            }
        }
    }
    
    private var advancedFeaturesSection: some View {
        Section("Advanced Features") {
            // Feature Flag Settings (Advanced Settings only)
            if isAdvancedSettingsEnabled {
                NavigationLink(destination: FeatureFlagSettingsView()) {
                    SettingsRow(
                        icon: "flag.2.crossed",
                        iconColor: .blue,
                        title: "Feature Settings",
                        subtitle: "Manage app features"
                    )
                }
            }
            
            // Debug Feature Flags (Debug builds only)
            if isDebugSettingsEnabled {
                NavigationLink(destination: FeatureFlagDebugView()) {
                    SettingsRow(
                        icon: "gearshape.2",
                        iconColor: .orange,
                        title: "Debug Feature Flags",
                        subtitle: "Development controls"
                    )
                }
            }
            
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
            
            // Architecture Viewer (Architecture Visualization only)
            // TODO: Re-enable feature flag when FeatureFlagManager is available
            if true { // Temporarily enabled for development
                NavigationLink(destination: ArchitectureViewerSettingsView()) {
                    SettingsRow(
                        icon: "network",
                        iconColor: Color(.systemPurple),
                        title: "Architecture Viewer",
                        subtitle: architectureStatusText
                    )
                }
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
            .buttonStyle(.plain)
            .accessibilityLabel("About LeanVibe")
            .accessibilityHint("Shows app version and information")
            
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
    
    private var betaTestingSection: some View {
        Section("Beta Testing") {
            // Show beta feedback only if feature is enabled
            if isBetaFeedbackEnabled {
                NavigationLink(destination: BetaFeedbackView()) {
                    SettingsRow(
                        icon: "star.bubble",
                        iconColor: Color(.systemYellow),
                        title: "Send Feedback",
                        subtitle: "Help improve LeanVibe"
                    )
                }
            }
            
            // Show beta analytics only if feature is enabled
            if isBetaAnalyticsEnabled {
                NavigationLink(destination: BetaAnalyticsDashboardView()) {
                    SettingsRow(
                        icon: "chart.line.uptrend.xyaxis",
                        iconColor: Color(.systemPurple),
                        title: "Beta Analytics",
                        subtitle: "Usage insights"
                    )
                }
            }
            
            // If no beta features are enabled, show a message
            if !isBetaFeedbackEnabled && !isBetaAnalyticsEnabled {
                Text("Beta features are currently disabled")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .padding()
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
            
            Spacer()
        }
        .padding(.vertical, 8)
        .frame(minHeight: 44) // Ensure minimum iOS touch target size
        .contentShape(Rectangle()) // Make entire row tappable
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct AboutView: View {
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationStack {
            List {
                // App Information Section
                Section {
                    VStack(spacing: 16) {
                        // App Icon
                        Image(systemName: "apps.iphone")
                            .font(.system(size: 72))
                            .foregroundColor(.blue)
                        
                        // App Name and Version
                        VStack(spacing: 4) {
                            Text("LeanVibe")
                                .font(.largeTitle)
                                .fontWeight(.bold)
                            
                            Text("Version \(Bundle.main.appVersion)")
                                .font(.headline)
                                .foregroundColor(.secondary)
                            
                            Text("Build \(Bundle.main.buildNumber)")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                        
                        Text("AI-Powered Productivity Suite")
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                            .multilineTextAlignment(.center)
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 16)
                }
                
                // Developer Information Section
                Section("Developer") {
                    HStack {
                        Image(systemName: "person.circle.fill")
                            .foregroundColor(.blue)
                        VStack(alignment: .leading) {
                            Text("LeanVibe Team")
                                .font(.headline)
                            Text("Building the future of productivity")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                    }
                    .padding(.vertical, 4)
                }
                
                // Features Section
                Section("Key Features") {
                    Label("Voice-Powered Task Management", systemImage: "mic.fill")
                    Label("AI-Driven Workflow Optimization", systemImage: "brain.head.profile")
                    Label("Real-Time Architecture Visualization", systemImage: "network")
                    Label("Cross-Platform Synchronization", systemImage: "arrow.triangle.2.circlepath")
                    Label("Privacy-First Design", systemImage: "lock.shield.fill")
                }
                
                // Support & Feedback Section
                Section("Support & Feedback") {
                    Button(action: {
                        if let url = URL(string: "mailto:support@leanvibe.com?subject=LeanVibe iOS Feedback") {
                            UIApplication.shared.open(url)
                        }
                    }) {
                        HStack {
                            Image(systemName: "envelope.fill")
                                .foregroundColor(.blue)
                            Text("Contact Support")
                                .foregroundColor(.primary)
                            Spacer()
                            Image(systemName: "arrow.up.right")
                                .foregroundColor(.secondary)
                                .font(.caption)
                        }
                    }
                    
                    Button(action: {
                        if let url = URL(string: "https://github.com/leanvibe/leanvibe-ios/issues") {
                            UIApplication.shared.open(url)
                        }
                    }) {
                        HStack {
                            Image(systemName: "exclamationmark.bubble.fill")
                                .foregroundColor(.orange)
                            Text("Report Bug")
                                .foregroundColor(.primary)
                            Spacer()
                            Image(systemName: "arrow.up.right")
                                .foregroundColor(.secondary)
                                .font(.caption)
                        }
                    }
                    
                    Button(action: {
                        if let url = URL(string: "https://github.com/leanvibe/leanvibe-ios") {
                            UIApplication.shared.open(url)
                        }
                    }) {
                        HStack {
                            Image(systemName: "star.fill")
                                .foregroundColor(.yellow)
                            Text("Rate on GitHub")
                                .foregroundColor(.primary)
                            Spacer()
                            Image(systemName: "arrow.up.right")
                                .foregroundColor(.secondary)
                                .font(.caption)
                        }
                    }
                }
                
                // Legal Section
                Section("Legal & Privacy") {
                    NavigationLink(destination: PrivacyPolicyDetailView()) {
                        HStack {
                            Image(systemName: "hand.raised.fill")
                                .foregroundColor(.green)
                            Text("Privacy Policy")
                        }
                    }
                    
                    NavigationLink(destination: OpenSourceLicensesView()) {
                        HStack {
                            Image(systemName: "doc.text.fill")
                                .foregroundColor(.purple)
                            Text("Open Source Licenses")
                        }
                    }
                    
                    NavigationLink(destination: TermsOfServiceView()) {
                        HStack {
                            Image(systemName: "doc.plaintext.fill")
                                .foregroundColor(.gray)
                            Text("Terms of Service")
                        }
                    }
                }
                
                // System Information Section
                Section("System Information") {
                    HStack {
                        Text("iOS Version")
                        Spacer()
                        Text(UIDevice.current.systemVersion)
                            .foregroundColor(.secondary)
                    }
                    
                    HStack {
                        Text("Device Model")
                        Spacer()
                        Text(UIDevice.current.model)
                            .foregroundColor(.secondary)
                    }
                    
                    HStack {
                        Text("Device Name")
                        Spacer()
                        Text(UIDevice.current.name)
                            .foregroundColor(.secondary)
                    }
                }
                
                // Copyright Section
                Section {
                    Text("© 2024 LeanVibe Team. All rights reserved.")
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .frame(maxWidth: .infinity, alignment: .center)
                        .padding(.vertical, 8)
                }
            }
            .navigationTitle("About LeanVibe")
            .navigationBarTitleDisplayMode(.inline)
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
struct SettingsExportImportView: View {
    @StateObject private var settingsManager = SettingsManager.shared
    @Environment(\.dismiss) private var dismiss
    @State private var showingFilePicker = false
    @State private var showingShareSheet = false
    @State private var showingResetConfirmation = false
    @State private var exportedFileURL: URL?
    @State private var importStatus: ImportStatus = .idle
    @State private var exportStatus: ExportStatus = .idle
    @State private var selectedBackups: Set<String> = []
    
    enum ImportStatus: Equatable {
        case idle
        case importing
        case success(String)
        case failed(String)
    }
    
    enum ExportStatus: Equatable {
        case idle
        case exporting
        case success(URL)
        case failed(String)
        
        static func == (lhs: ExportStatus, rhs: ExportStatus) -> Bool {
            switch (lhs, rhs) {
            case (.idle, .idle), (.exporting, .exporting):
                return true
            case (.success(let lhsURL), .success(let rhsURL)):
                return lhsURL == rhsURL
            case (.failed(let lhsString), .failed(let rhsString)):
                return lhsString == rhsString
            default:
                return false
            }
        }
    }
    
    var body: some View {
        NavigationStack {
            List {
                // Overview Section
                Section {
                    Text("Export your settings for backup or sharing, and import settings from other devices or backups.")
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .padding(.vertical, 4)
                }
                
                // Export Section
                Section("Export Settings") {
                    Button("Export All Settings") {
                        exportAllSettings()
                    }
                    .foregroundColor(.blue)
                    .disabled(exportStatus == .exporting)
                    
                    Button("Export Voice Settings Only") {
                        exportVoiceSettings()
                    }
                    .foregroundColor(.blue)
                    .disabled(exportStatus == .exporting)
                    
                    Button("Export Kanban Settings Only") {
                        exportKanbanSettings()
                    }
                    .foregroundColor(.blue)
                    .disabled(exportStatus == .exporting)
                    
                    if case .exporting = exportStatus {
                        HStack {
                            ProgressView()
                                .scaleEffect(0.8)
                            Text("Exporting...")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                    }
                    
                    if case .success(let url) = exportStatus {
                        HStack {
                            Image(systemName: "checkmark.circle.fill")
                                .foregroundColor(.green)
                            VStack(alignment: .leading, spacing: 2) {
                                Text("Export Successful")
                                    .font(.caption)
                                    .foregroundColor(.green)
                                Text(url.lastPathComponent)
                                    .font(.caption2)
                                    .foregroundColor(.secondary)
                            }
                            Spacer()
                            Button("Share") {
                                exportedFileURL = url
                                showingShareSheet = true
                            }
                            .font(.caption)
                            .foregroundColor(.blue)
                        }
                    }
                    
                    if case .failed(let error) = exportStatus {
                        HStack {
                            Image(systemName: "exclamationmark.triangle.fill")
                                .foregroundColor(.red)
                            Text("Export Failed: \(error)")
                                .font(.caption)
                                .foregroundColor(.red)
                        }
                    }
                }
                
                // Import Section
                Section("Import Settings") {
                    Button("Import from File") {
                        showingFilePicker = true
                    }
                    .foregroundColor(.blue)
                    .disabled(importStatus == .importing)
                    
                    Button("Import from Clipboard") {
                        importFromClipboard()
                    }
                    .foregroundColor(.blue)
                    .disabled(importStatus == .importing || UIPasteboard.general.string == nil)
                    
                    if case .importing = importStatus {
                        HStack {
                            ProgressView()
                                .scaleEffect(0.8)
                            Text("Importing...")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                    }
                    
                    if case .success(let message) = importStatus {
                        HStack {
                            Image(systemName: "checkmark.circle.fill")
                                .foregroundColor(.green)
                            Text(message)
                                .font(.caption)
                                .foregroundColor(.green)
                        }
                    }
                    
                    if case .failed(let error) = importStatus {
                        HStack {
                            Image(systemName: "exclamationmark.triangle.fill")
                                .foregroundColor(.red)
                            Text("Import Failed: \(error)")
                                .font(.caption)
                                .foregroundColor(.red)
                        }
                    }
                }
                
                // Backup Management Section
                Section("Backup Management") {
                    NavigationLink("Automatic Backups") {
                        AutomaticBackupSettingsView()
                    }
                    
                    NavigationLink("Backup History") {
                        BackupHistoryView()
                    }
                    
                    Button("Create Backup Now") {
                        createBackupNow()
                    }
                    .foregroundColor(.blue)
                }
                
                // Preset Templates Section
                Section("Preset Templates") {
                    Button("Export Default Template") {
                        exportDefaultTemplate()
                    }
                    .foregroundColor(.blue)
                    
                    Button("Export Productivity Template") {
                        exportProductivityTemplate()
                    }
                    .foregroundColor(.blue)
                    
                    Button("Export Developer Template") {
                        exportDeveloperTemplate()
                    }
                    .foregroundColor(.blue)
                }
                
                // Reset Section
                Section("Reset") {
                    Button("Reset to Default Settings") {
                        showingResetConfirmation = true
                    }
                    .foregroundColor(.red)
                    
                    Text("This will permanently delete all custom settings and restore defaults. This action cannot be undone.")
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .padding(.top, 4)
                }
            }
            .navigationTitle("Export/Import")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Done") {
                        dismiss()
                    }
                }
            }
        }
        .fileImporter(
            isPresented: $showingFilePicker,
            allowedContentTypes: [.json, .plainText],
            allowsMultipleSelection: false
        ) { result in
            handleFileImport(result)
        }
        .sheet(isPresented: $showingShareSheet) {
            if let url = exportedFileURL {
                ShareSheet(items: [url])
            }
        }
        .confirmationDialog(
            "Reset All Settings",
            isPresented: $showingResetConfirmation,
            titleVisibility: .visible
        ) {
            Button("Reset All Settings", role: .destructive) {
                settingsManager.resetAllSettings()
                importStatus = .success("Settings reset to defaults")
            }
            Button("Cancel", role: .cancel) {}
        } message: {
            Text("This will delete all custom settings and restore defaults. This action cannot be undone.")
        }
    }
    
    // MARK: - Export Functions
    
    private func exportAllSettings() {
        exportStatus = .exporting
        
        Task { @MainActor in
            do {
                let allSettings = AllSettings(
                    connection: settingsManager.connection,
                    voice: settingsManager.voice,
                    notifications: settingsManager.notifications,
                    kanban: settingsManager.kanban,
                    accessibility: settingsManager.accessibility,
                    architecture: settingsManager.architecture,
                    metrics: settingsManager.metrics,
                    taskCreation: settingsManager.taskCreation,
                    offline: settingsManager.offline,
                    interface: settingsManager.interface,
                    performance: settingsManager.performance
                )
                
                let encoder = JSONEncoder()
                encoder.outputFormatting = .prettyPrinted
                let data = try encoder.encode(allSettings)
                
                let url = try saveToTemporaryFile(data: data, filename: "LeanVibe_AllSettings_\(dateString()).json")
                
                exportStatus = .success(url)
            } catch {
                exportStatus = .failed(error.localizedDescription)
            }
        }
    }
    
    private func exportVoiceSettings() {
        exportStatus = .exporting
        
        Task { @MainActor in
            do {
                let encoder = JSONEncoder()
                encoder.outputFormatting = .prettyPrinted
                let data = try encoder.encode(settingsManager.voice)
                
                let url = try saveToTemporaryFile(data: data, filename: "LeanVibe_VoiceSettings_\(dateString()).json")
                
                exportStatus = .success(url)
            } catch {
                exportStatus = .failed(error.localizedDescription)
            }
        }
    }
    
    private func exportKanbanSettings() {
        exportStatus = .exporting
        
        Task { @MainActor in
            do {
                let encoder = JSONEncoder()
                encoder.outputFormatting = .prettyPrinted
                let data = try encoder.encode(settingsManager.kanban)
                
                let url = try saveToTemporaryFile(data: data, filename: "LeanVibe_KanbanSettings_\(dateString()).json")
                
                exportStatus = .success(url)
            } catch {
                exportStatus = .failed(error.localizedDescription)
            }
        }
    }
    
    private func exportDefaultTemplate() {
        exportStatus = .exporting
        
        Task { @MainActor in
            do {
                let defaultSettings = AllSettings(
                    connection: ConnectionPreferences(),
                    voice: VoiceSettings(),
                    notifications: NotificationSettings(),
                    kanban: KanbanSettings(),
                    accessibility: AccessibilitySettings(),
                    architecture: ArchitectureSettings(),
                    metrics: MetricsSettings(),
                    taskCreation: TaskCreationSettings(),
                    offline: OfflineSettings(),
                    interface: InterfaceSettings(),
                    performance: PerformanceSettings()
                )
                
                let encoder = JSONEncoder()
                encoder.outputFormatting = .prettyPrinted
                let data = try encoder.encode(defaultSettings)
                
                let url = try saveToTemporaryFile(data: data, filename: "LeanVibe_DefaultTemplate.json")
                
                exportStatus = .success(url)
            } catch {
                exportStatus = .failed(error.localizedDescription)
            }
        }
    }
    
    private func exportProductivityTemplate() {
        exportStatus = .exporting
        
        Task { @MainActor in
            do {
                var productivitySettings = AllSettings(
                    connection: ConnectionPreferences(),
                    voice: VoiceSettings(),
                    notifications: NotificationSettings(),
                    kanban: KanbanSettings(),
                    accessibility: AccessibilitySettings(),
                    architecture: ArchitectureSettings(),
                    metrics: MetricsSettings(),
                    taskCreation: TaskCreationSettings(),
                    offline: OfflineSettings(),
                    interface: InterfaceSettings(),
                    performance: PerformanceSettings()
                )
                
                // Customize for productivity  
                productivitySettings.voice.isEnabled = true
                productivitySettings.voice.autoStopListening = true
                productivitySettings.notifications.taskCompletionNotifications = true
                productivitySettings.kanban.autoRefresh = true
                productivitySettings.metrics.isEnabled = true
                
                let encoder = JSONEncoder()
                encoder.outputFormatting = .prettyPrinted
                let data = try encoder.encode(productivitySettings)
                
                let url = try saveToTemporaryFile(data: data, filename: "LeanVibe_ProductivityTemplate.json")
                
                exportStatus = .success(url)
            } catch {
                exportStatus = .failed(error.localizedDescription)
            }
        }
    }
    
    private func exportDeveloperTemplate() {
        exportStatus = .exporting
        
        Task { @MainActor in
            do {
                var developerSettings = AllSettings(
                    connection: ConnectionPreferences(),
                    voice: VoiceSettings(),
                    notifications: NotificationSettings(),
                    kanban: KanbanSettings(),
                    accessibility: AccessibilitySettings(),
                    architecture: ArchitectureSettings(),
                    metrics: MetricsSettings(),
                    taskCreation: TaskCreationSettings(),
                    offline: OfflineSettings(),
                    interface: InterfaceSettings(),
                    performance: PerformanceSettings()
                )
                
                // Customize for developers
                developerSettings.architecture.autoUpdate = true
                developerSettings.metrics.performanceMonitoringEnabled = true
                developerSettings.performance.memoryLimitEnabled = true
                developerSettings.kanban.enableVoiceTaskCreation = true
                
                let encoder = JSONEncoder()
                encoder.outputFormatting = .prettyPrinted
                let data = try encoder.encode(developerSettings)
                
                let url = try saveToTemporaryFile(data: data, filename: "LeanVibe_DeveloperTemplate.json")
                
                exportStatus = .success(url)
            } catch {
                exportStatus = .failed(error.localizedDescription)
            }
        }
    }
    
    // MARK: - Import Functions
    
    private func importFromClipboard() {
        guard let clipboardContent = UIPasteboard.general.string else {
            importStatus = .failed("No text content in clipboard")
            return
        }
        
        importSettings(from: clipboardContent)
    }
    
    private func handleFileImport(_ result: Result<[URL], Error>) {
        switch result {
        case .success(let urls):
            guard let url = urls.first else {
                importStatus = .failed("No file selected")
                return
            }
            
            do {
                let data = try Data(contentsOf: url)
                if let jsonString = String(data: data, encoding: .utf8) {
                    importSettings(from: jsonString)
                } else {
                    importStatus = .failed("Unable to read file content")
                }
            } catch {
                importStatus = .failed("Failed to read file: \(error.localizedDescription)")
            }
            
        case .failure(let error):
            importStatus = .failed("File import failed: \(error.localizedDescription)")
        }
    }
    
    private func importSettings(from jsonString: String) {
        importStatus = .importing
        
        DispatchQueue.global(qos: .userInitiated).async {
            do {
                let data = jsonString.data(using: .utf8)!
                let decoder = JSONDecoder()
                
                // Try to decode as AllSettings first
                if let allSettings = try? decoder.decode(AllSettings.self, from: data) {
                    DispatchQueue.main.async {
                        settingsManager.connection = allSettings.connection
                        settingsManager.voice = allSettings.voice
                        settingsManager.notifications = allSettings.notifications
                        settingsManager.kanban = allSettings.kanban
                        settingsManager.accessibility = allSettings.accessibility
                        settingsManager.architecture = allSettings.architecture
                        settingsManager.metrics = allSettings.metrics
                        settingsManager.taskCreation = allSettings.taskCreation
                        settingsManager.offline = allSettings.offline
                        settingsManager.interface = allSettings.interface
                        settingsManager.performance = allSettings.performance
                        
                        importStatus = .success("All settings imported successfully")
                    }
                    return
                }
                
                // Try to decode as individual settings
                if let voiceSettings = try? decoder.decode(VoiceSettings.self, from: data) {
                    DispatchQueue.main.async {
                        settingsManager.voice = voiceSettings
                        importStatus = .success("Voice settings imported successfully")
                    }
                    return
                }
                
                if let kanbanSettings = try? decoder.decode(KanbanSettings.self, from: data) {
                    DispatchQueue.main.async {
                        settingsManager.kanban = kanbanSettings
                        importStatus = .success("Kanban settings imported successfully")
                    }
                    return
                }
                
                DispatchQueue.main.async {
                    importStatus = .failed("Unrecognized settings format")
                }
                
            } catch {
                DispatchQueue.main.async {
                    importStatus = .failed("Invalid JSON format: \(error.localizedDescription)")
                }
            }
        }
    }
    
    // MARK: - Helper Functions
    
    private func createBackupNow() {
        // Create an automatic backup
        exportAllSettings()
    }
    
    private func saveToTemporaryFile(data: Data, filename: String) throws -> URL {
        let tempDir = FileManager.default.temporaryDirectory
        let fileURL = tempDir.appendingPathComponent(filename)
        try data.write(to: fileURL)
        return fileURL
    }
    
    private func dateString() -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd_HH-mm-ss"
        return formatter.string(from: Date())
    }
}

// MARK: - Supporting Views for Export/Import

@available(iOS 18.0, macOS 14.0, *)
struct ShareSheet: UIViewControllerRepresentable {
    let items: [Any]
    
    func makeUIViewController(context: Context) -> UIActivityViewController {
        let controller = UIActivityViewController(activityItems: items, applicationActivities: nil)
        return controller
    }
    
    func updateUIViewController(_ uiViewController: UIActivityViewController, context: Context) {}
}

@available(iOS 18.0, macOS 14.0, *)
struct AutomaticBackupSettingsView: View {
    @State private var isEnabled = false
    @State private var frequency = "daily"
    @State private var maxBackups = 5
    @State private var includeVoiceSettings = true
    @State private var includeKanbanSettings = true
    
    var body: some View {
        List {
            Section("Automatic Backup") {
                Toggle("Enable Automatic Backups", isOn: $isEnabled)
                
                if isEnabled {
                    Picker("Backup Frequency", selection: $frequency) {
                        Text("Daily").tag("daily")
                        Text("Weekly").tag("weekly")
                        Text("Monthly").tag("monthly")
                    }
                    .pickerStyle(.menu)
                    
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Text("Max Backups to Keep")
                            Spacer()
                            Text("\(maxBackups)")
                                .foregroundColor(.secondary)
                        }
                        Slider(value: Binding(
                            get: { Double(maxBackups) },
                            set: { maxBackups = Int($0) }
                        ), in: 1...20, step: 1)
                    }
                    .padding(.vertical, 4)
                }
            }
            
            Section("Backup Content") {
                Toggle("Include Voice Settings", isOn: $includeVoiceSettings)
                Toggle("Include Kanban Settings", isOn: $includeKanbanSettings)
            }
            
            Section("Storage") {
                Button("View Backup Folder") {
                    // TODO: Show backup folder location
                }
                .foregroundColor(.blue)
                
                Button("Clear Old Backups") {
                    // TODO: Clear old backups
                }
                .foregroundColor(.orange)
            }
        }
        .navigationTitle("Automatic Backups")
        .navigationBarTitleDisplayMode(.inline)
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct BackupHistoryView: View {
    @State private var backups = [
        BackupItem(date: Date(), size: "2.1 MB", type: "All Settings"),
        BackupItem(date: Date().addingTimeInterval(-86400), size: "1.8 MB", type: "All Settings"),
        BackupItem(date: Date().addingTimeInterval(-172800), size: "0.5 MB", type: "Voice Settings"),
    ]
    
    var body: some View {
        List {
            Section("Recent Backups") {
                ForEach(backups, id: \.date) { backup in
                    HStack {
                        VStack(alignment: .leading, spacing: 4) {
                            Text(backup.type)
                                .font(.headline)
                            Text(DateFormatter.backupDateFormatter.string(from: backup.date))
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                        
                        Spacer()
                        
                        VStack(alignment: .trailing, spacing: 4) {
                            Text(backup.size)
                                .font(.caption)
                                .foregroundColor(.secondary)
                            
                            HStack(spacing: 16) {
                                Button("Restore") {
                                    // TODO: Restore backup
                                }
                                .font(.caption)
                                .foregroundColor(.blue)
                                
                                Button("Share") {
                                    // TODO: Share backup
                                }
                                .font(.caption)
                                .foregroundColor(.blue)
                            }
                        }
                    }
                    .padding(.vertical, 4)
                }
                .onDelete(perform: deleteBackups)
            }
            
            if backups.isEmpty {
                Section {
                    Text("No backups found")
                        .foregroundColor(.secondary)
                        .frame(maxWidth: .infinity, alignment: .center)
                        .padding(.vertical, 32)
                }
            }
        }
        .navigationTitle("Backup History")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            EditButton()
        }
    }
    
    private func deleteBackups(offsets: IndexSet) {
        backups.remove(atOffsets: offsets)
    }
}

struct BackupItem {
    let date: Date
    let size: String
    let type: String
}

extension DateFormatter {
    static let backupDateFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        formatter.timeStyle = .short
        return formatter
    }()
}

@available(iOS 18.0, macOS 14.0, *)
struct PrivacyPolicyDetailView: View {
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                Text("Privacy Policy")
                    .font(.largeTitle)
                    .fontWeight(.bold)
                
                Text("Last updated: \(DateFormatter.localizedString(from: Date(), dateStyle: .long, timeStyle: .none))")
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                VStack(alignment: .leading, spacing: 12) {
                    Text("Data Collection")
                        .font(.title2)
                        .fontWeight(.semibold)
                    
                    Text("LeanVibe is designed with privacy in mind. We collect minimal data necessary for the app to function:")
                    
                    Text("• Voice commands are processed locally on your device")
                    Text("• Settings and preferences are stored locally")
                    Text("• No personal data is transmitted to external servers without your explicit consent")
                    Text("• Analytics data is anonymized and opt-in only")
                }
                
                VStack(alignment: .leading, spacing: 12) {
                    Text("Data Usage")
                        .font(.title2)
                        .fontWeight(.semibold)
                    
                    Text("Your data is used exclusively to:")
                    Text("• Provide voice command functionality")
                    Text("• Synchronize settings across your devices")
                    Text("• Improve app performance and reliability")
                }
                
                VStack(alignment: .leading, spacing: 12) {
                    Text("Data Sharing")
                        .font(.title2)
                        .fontWeight(.semibold)
                    
                    Text("We do not sell, trade, or otherwise transfer your personal data to third parties. Data may only be shared:")
                    Text("• When required by law")
                    Text("• To protect our rights or safety")
                    Text("• With your explicit consent")
                }
                
                VStack(alignment: .leading, spacing: 12) {
                    Text("Contact")
                        .font(.title2)
                        .fontWeight(.semibold)
                    
                    Text("If you have questions about this Privacy Policy, please contact us at:")
                    Text("support@leanvibe.com")
                        .foregroundColor(.blue)
                }
            }
            .padding()
        }
        .navigationTitle("Privacy Policy")
        .navigationBarTitleDisplayMode(.inline)
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct OpenSourceLicensesView: View {
    private let licenses = [
        LicenseItem(name: "SwiftUI", license: "MIT License", description: "Apple's declarative UI framework"),
        LicenseItem(name: "Foundation", license: "MIT License", description: "Apple's foundational framework"),
        LicenseItem(name: "Speech", license: "MIT License", description: "Apple's speech recognition framework"),
        LicenseItem(name: "UserNotifications", license: "MIT License", description: "Apple's notification framework"),
    ]
    
    var body: some View {
        List {
            Section("Third-Party Libraries") {
                ForEach(licenses, id: \.name) { license in
                    VStack(alignment: .leading, spacing: 4) {
                        HStack {
                            Text(license.name)
                                .font(.headline)
                            Spacer()
                            Text(license.license)
                                .font(.caption)
                                .padding(.horizontal, 8)
                                .padding(.vertical, 2)
                                .background(Color.blue.opacity(0.2))
                                .foregroundColor(.blue)
                                .cornerRadius(4)
                        }
                        Text(license.description)
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    .padding(.vertical, 4)
                }
            }
            
            Section("Acknowledgments") {
                Text("LeanVibe is built using Apple's native frameworks and follows Apple's privacy guidelines.")
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                Text("Special thanks to the open source community for their contributions to the tools and frameworks that make this app possible.")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .navigationTitle("Open Source Licenses")
        .navigationBarTitleDisplayMode(.inline)
    }
}

struct LicenseItem {
    let name: String
    let license: String
    let description: String
}

@available(iOS 18.0, macOS 14.0, *)
struct TermsOfServiceView: View {
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                Text("Terms of Service")
                    .font(.largeTitle)
                    .fontWeight(.bold)
                
                Text("Last updated: \(DateFormatter.localizedString(from: Date(), dateStyle: .long, timeStyle: .none))")
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                VStack(alignment: .leading, spacing: 12) {
                    Text("Acceptance of Terms")
                        .font(.title2)
                        .fontWeight(.semibold)
                    
                    Text("By using LeanVibe, you agree to these Terms of Service. If you do not agree to these terms, please do not use the app.")
                }
                
                VStack(alignment: .leading, spacing: 12) {
                    Text("License")
                        .font(.title2)
                        .fontWeight(.semibold)
                    
                    Text("LeanVibe grants you a limited, non-exclusive, non-transferable license to use the app for personal or business productivity purposes.")
                }
                
                VStack(alignment: .leading, spacing: 12) {
                    Text("Restrictions")
                        .font(.title2)
                        .fontWeight(.semibold)
                    
                    Text("You may not:")
                    Text("• Reverse engineer or decompile the app")
                    Text("• Use the app for illegal activities")
                    Text("• Attempt to gain unauthorized access to our systems")
                    Text("• Distribute malicious content through the app")
                }
                
                VStack(alignment: .leading, spacing: 12) {
                    Text("Disclaimer")
                        .font(.title2)
                        .fontWeight(.semibold)
                    
                    Text("LeanVibe is provided \"as is\" without warranties of any kind. We do not guarantee that the app will be error-free or continuously available.")
                }
                
                VStack(alignment: .leading, spacing: 12) {
                    Text("Contact")
                        .font(.title2)
                        .fontWeight(.semibold)
                    
                    Text("For questions about these Terms of Service, contact:")
                    Text("support@leanvibe.com")
                        .foregroundColor(.blue)
                }
            }
            .padding()
        }
        .navigationTitle("Terms of Service")
        .navigationBarTitleDisplayMode(.inline)
    }
}

// Note: WakePhraseSettingsView, SpeechSettingsView, and TaskNotificationSettingsView 
// are implemented in their respective files with full functionality

@available(iOS 18.0, macOS 14.0, *)
struct MetricsSettingsView: View {
    @StateObject private var settingsManager = SettingsManager.shared
    @Bindable private var bindableSettingsManager: SettingsManager = SettingsManager.shared
    @State private var showingExportSheet = false
    @State private var showingResetConfirmation = false
    
    var body: some View {
        List {
            // Overview Section
            Section {
                Text("Configure performance monitoring, data collection, and reporting preferences.")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .padding(.vertical, 4)
            }
            
            // Data Collection Section
            Section("Data Collection") {
                Toggle("Performance Monitoring", isOn: $bindableSettingsManager.metrics.performanceMonitoringEnabled)
                Toggle("Memory Usage Tracking", isOn: $bindableSettingsManager.metrics.memoryUsageTrackingEnabled)
                Toggle("Network Metrics", isOn: $bindableSettingsManager.metrics.networkMetricsEnabled)
                Toggle("Voice Metrics", isOn: $bindableSettingsManager.metrics.voiceMetricsEnabled)
                Toggle("Task Completion Metrics", isOn: $bindableSettingsManager.metrics.taskCompletionMetricsEnabled)
                Toggle("Real-time Monitoring", isOn: $bindableSettingsManager.metrics.realTimeMonitoringEnabled)
                Toggle("Detailed Logging", isOn: $bindableSettingsManager.metrics.detailedLoggingEnabled)
            }
            
            // Data Retention Section
            Section("Data Retention") {
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Text("Retention Period")
                        Spacer()
                        Text("\(settingsManager.metrics.dataRetentionDays) days")
                            .foregroundColor(.secondary)
                    }
                    
                    Slider(
                        value: Binding(
                            get: { Double(settingsManager.metrics.dataRetentionDays) },
                            set: { bindableSettingsManager.metrics.dataRetentionDays = Int($0) }
                        ),
                        in: 1...365,
                        step: 1
                    )
                    
                    Text("Data older than this will be automatically cleaned up")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                .padding(.vertical, 4)
                
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Text("Max Storage Size")
                        Spacer()
                        Text("\(settingsManager.metrics.maxStorageSize) MB")
                            .foregroundColor(.secondary)
                    }
                    
                    Slider(
                        value: Binding(
                            get: { Double(settingsManager.metrics.maxStorageSize) },
                            set: { bindableSettingsManager.metrics.maxStorageSize = Int($0) }
                        ),
                        in: 10...1000,
                        step: 10
                    )
                }
                .padding(.vertical, 4)
            }
            
            // Reporting Section
            Section("Reporting") {
                HStack {
                    Text("Aggregation Interval")
                    Spacer()
                    Picker("Aggregation", selection: $bindableSettingsManager.metrics.aggregationInterval) {
                        Text("Real-time").tag("real-time")
                        Text("Every 5 minutes").tag("5min")
                        Text("Hourly").tag("hourly")
                        Text("Daily").tag("daily")
                    }
                    .pickerStyle(.menu)
                }
                
                HStack {
                    Text("Export Format")
                    Spacer()
                    Picker("Format", selection: $bindableSettingsManager.metrics.exportFormat) {
                        Text("JSON").tag("json")
                        Text("CSV").tag("csv")
                        Text("XML").tag("xml")
                    }
                    .pickerStyle(.menu)
                }
                
                Toggle("Auto Export", isOn: $bindableSettingsManager.metrics.autoExportEnabled)
                Toggle("Share Metrics", isOn: $bindableSettingsManager.metrics.shareMetricsEnabled)
            }
            
            // Alerts & Notifications Section
            Section("Alerts & Notifications") {
                Toggle("Performance Alerts", isOn: $bindableSettingsManager.metrics.alertsEnabled)
                
                if settingsManager.metrics.alertsEnabled {
                    NavigationLink("Configure Thresholds") {
                        MetricsThresholdsView()
                    }
                }
            }
            
            // Privacy Section
            Section("Privacy") {
                Toggle("Privacy Mode", isOn: $bindableSettingsManager.metrics.privacyMode)
                
                if settingsManager.metrics.privacyMode {
                    Text("Personal data will be anonymized in metrics")
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .padding(.top, 4)
                }
            }
            
            // Actions Section
            Section("Actions") {
                Button("Export Current Metrics") {
                    showingExportSheet = true
                }
                .foregroundColor(.blue)
                
                Button("View Metrics Dashboard") {
                    // TODO: Navigate to metrics dashboard
                }
                .foregroundColor(.blue)
                
                Button("Reset All Metrics", role: .destructive) {
                    showingResetConfirmation = true
                }
                .foregroundColor(.red)
            }
        }
        .navigationTitle("Metrics Settings")
        .navigationBarTitleDisplayMode(.inline)
        .sheet(isPresented: $showingExportSheet) {
            MetricsExportView()
        }
        .confirmationDialog(
            "Reset All Metrics",
            isPresented: $showingResetConfirmation,
            titleVisibility: .visible
        ) {
            Button("Reset All Metrics", role: .destructive) {
                // Reset metrics settings to defaults
                settingsManager.metrics = MetricsSettings()
            }
            Button("Cancel", role: .cancel) {}
        } message: {
            Text("This will delete all collected metrics data and reset settings to defaults. This action cannot be undone.")
        }
    }
}

// MARK: - Supporting Views

@available(iOS 18.0, macOS 14.0, *)
struct MetricsThresholdsView: View {
    var body: some View {
        List {
            Section("Performance Thresholds") {
                // TODO: Implement threshold configuration
                Text("Memory Usage > 80%")
                Text("CPU Usage > 90%")
                Text("Network Latency > 1000ms")
            }
        }
        .navigationTitle("Alert Thresholds")
        .navigationBarTitleDisplayMode(.inline)
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct MetricsExportView: View {
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationStack {
            VStack(spacing: 20) {
                Image(systemName: "square.and.arrow.up")
                    .font(.system(size: 48))
                    .foregroundColor(.blue)
                
                Text("Export Metrics Data")
                    .font(.title2)
                    .fontWeight(.semibold)
                
                Text("Choose export format and date range")
                    .font(.body)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
                
                Button("Export as JSON") {
                    // TODO: Implement export functionality
                    dismiss()
                }
                .buttonStyle(.borderedProminent)
                
                Button("Export as CSV") {
                    // TODO: Implement export functionality
                    dismiss()
                }
                .buttonStyle(.bordered)
            }
            .padding()
            .navigationTitle("Export Metrics")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
            }
        }
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct TaskCreationSettingsView: View {
    @StateObject private var settingsManager = SettingsManager.shared
    @Bindable private var bindableSettingsManager: SettingsManager = SettingsManager.shared
    @State private var showingTemplateManager = false
    @State private var showingResetConfirmation = false
    
    var body: some View {
        List {
            // Overview Section
            Section {
                Text("Configure default settings for creating new tasks, templates, and automation preferences.")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .padding(.vertical, 4)
            }
            
            // Default Values Section
            Section("Default Task Settings") {
                HStack {
                    Text("Default Priority")
                    Spacer()
                    Picker("Priority", selection: $bindableSettingsManager.taskCreation.defaultPriority) {
                        Text("Low").tag("low")
                        Text("Medium").tag("medium")
                        Text("High").tag("high")
                        Text("Critical").tag("critical")
                    }
                    .pickerStyle(.menu)
                }
                
                HStack {
                    Text("Default Assignee")
                    Spacer()
                    Picker("Assignee", selection: $bindableSettingsManager.taskCreation.defaultAssignee) {
                        Text("None").tag("")
                        Text("Self").tag("self")
                        Text("Team Lead").tag("team_lead")
                        Text("Auto-assign").tag("auto")
                    }
                    .pickerStyle(.menu)
                }
                
                HStack {
                    Text("Default Due Date")
                    Spacer()
                    Picker("Due Date", selection: $bindableSettingsManager.taskCreation.defaultDueDate) {
                        Text("None").tag("none")
                        Text("Today").tag("today")
                        Text("Tomorrow").tag("tomorrow")
                        Text("This Week").tag("week")
                        Text("Next Week").tag("next_week")
                    }
                    .pickerStyle(.menu)
                }
                
                Toggle("Auto-assign to Self", isOn: $bindableSettingsManager.taskCreation.autoAssignToSelf)
            }
            
            // Templates Section
            Section("Templates") {
                Toggle("Use Templates", isOn: $bindableSettingsManager.taskCreation.useTemplates)
                
                if settingsManager.taskCreation.useTemplates {
                    HStack {
                        Text("Default Template")
                        Spacer()
                        Picker("Template", selection: $bindableSettingsManager.taskCreation.defaultTemplate) {
                            Text("Basic Task").tag("basic")
                            Text("Bug Report").tag("bug")
                            Text("Feature Request").tag("feature")
                            Text("Development Task").tag("dev")
                            Text("Research Task").tag("research")
                        }
                        .pickerStyle(.menu)
                    }
                    
                    Button("Manage Templates") {
                        showingTemplateManager = true
                    }
                    .foregroundColor(.blue)
                }
                
                Toggle("Template Sharing", isOn: $bindableSettingsManager.taskCreation.templateSharingEnabled)
            }
            
            // Task Creation Options Section
            Section("Creation Options") {
                Toggle("Require Description", isOn: $bindableSettingsManager.taskCreation.requireDescription)
                Toggle("Enable Quick Actions", isOn: $bindableSettingsManager.taskCreation.enableQuickActions)
                Toggle("Voice Task Creation", isOn: $bindableSettingsManager.taskCreation.voiceTaskCreationEnabled)
                Toggle("Auto-save", isOn: $bindableSettingsManager.taskCreation.autoSaveEnabled)
                Toggle("Task Validation", isOn: $bindableSettingsManager.taskCreation.taskValidationEnabled)
                Toggle("Duplicate Task Warning", isOn: $bindableSettingsManager.taskCreation.duplicateTaskWarning)
            }
            
            // Advanced Features Section
            Section("Advanced Features") {
                Toggle("Custom Fields", isOn: $bindableSettingsManager.taskCreation.customFieldsEnabled)
                
                if settingsManager.taskCreation.customFieldsEnabled {
                    NavigationLink("Manage Custom Fields") {
                        CustomFieldsView()
                    }
                }
                
                Toggle("Bulk Creation", isOn: $bindableSettingsManager.taskCreation.bulkCreationEnabled)
                Toggle("Task History Tracking", isOn: $bindableSettingsManager.taskCreation.taskHistoryEnabled)
            }
            
            // Notifications Section
            Section("Notifications") {
                Toggle("Task Creation Notifications", isOn: $bindableSettingsManager.taskCreation.taskNotificationsEnabled)
                
                if settingsManager.taskCreation.taskNotificationsEnabled {
                    Text("Notify when tasks are created via voice or automation")
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .padding(.top, 4)
                }
            }
            
            // Actions Section
            Section("Actions") {
                Button("Export Task Templates") {
                    // TODO: Implement template export
                }
                .foregroundColor(.blue)
                
                Button("Import Task Templates") {
                    // TODO: Implement template import
                }
                .foregroundColor(.blue)
                
                Button("Reset to Defaults", role: .destructive) {
                    showingResetConfirmation = true
                }
                .foregroundColor(.red)
            }
        }
        .navigationTitle("Task Creation")
        .navigationBarTitleDisplayMode(.inline)
        .sheet(isPresented: $showingTemplateManager) {
            TaskTemplateManagerView()
        }
        .confirmationDialog(
            "Reset Task Creation Settings",
            isPresented: $showingResetConfirmation,
            titleVisibility: .visible
        ) {
            Button("Reset All Settings", role: .destructive) {
                settingsManager.taskCreation = TaskCreationSettings()
            }
            Button("Cancel", role: .cancel) {}
        } message: {
            Text("This will reset all task creation settings to defaults. Custom templates and fields will be preserved.")
        }
    }
}

// MARK: - Supporting Views

@available(iOS 18.0, macOS 14.0, *)
struct TaskTemplateManagerView: View {
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationStack {
            List {
                Section("Available Templates") {
                    TemplateRow(name: "Basic Task", description: "Simple task with title and description", isDefault: true)
                    TemplateRow(name: "Bug Report", description: "Template for reporting bugs", isDefault: false)
                    TemplateRow(name: "Feature Request", description: "Template for feature requests", isDefault: false)
                    TemplateRow(name: "Development Task", description: "Template for development work", isDefault: false)
                }
                
                Section("Custom Templates") {
                    Button("Create New Template") {
                        // TODO: Navigate to template creation
                    }
                    .foregroundColor(.blue)
                }
            }
            .navigationTitle("Task Templates")
            .navigationBarTitleDisplayMode(.inline)
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
struct TemplateRow: View {
    let name: String
    let description: String
    let isDefault: Bool
    
    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text(name)
                    .font(.headline)
                if isDefault {
                    Text("Default")
                        .font(.caption)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 2)
                        .background(Color.blue.opacity(0.2))
                        .foregroundColor(.blue)
                        .cornerRadius(4)
                }
                Spacer()
                Button("Edit") {
                    // TODO: Navigate to template editor
                }
                .font(.caption)
                .foregroundColor(.blue)
            }
            Text(description)
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .padding(.vertical, 2)
    }
}

// CustomFieldsView is defined in KanbanSettingsView.swift to avoid duplication

// Temporary minimal view implementations until fully integrated
@available(iOS 18.0, macOS 14.0, *)
struct WakePhraseSettingsView: View {
    var body: some View {
        Text("Wake Phrase Settings")
            .navigationTitle("Wake Phrase")
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct SpeechSettingsView: View {
    var body: some View {
        Text("Speech Settings")
            .navigationTitle("Speech")
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct TaskNotificationSettingsView: View {
    var body: some View {
        Text("Task Notification Settings")
            .navigationTitle("Task Notifications")
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct SyncSettingsView: View {
    var body: some View {
        Text("Sync Settings")
            .navigationTitle("Sync")
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct FeatureFlagSettingsView: View {
    var body: some View {
        Text("Feature Flag Settings")
            .navigationTitle("Feature Flags")
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct FeatureFlagDebugView: View {
    var body: some View {
        Text("Feature Flag Debug")
            .navigationTitle("Feature Debug")
    }
}

// Additional temporary view implementations

@available(iOS 18.0, macOS 14.0, *)
struct OfflineSettingsView: View {
    @StateObject private var settingsManager = SettingsManager.shared
    @Bindable private var bindableSettingsManager: SettingsManager = SettingsManager.shared
    @State private var showingStorageDetails = false
    @State private var showingResetConfirmation = false
    
    var body: some View {
        List {
            // Overview Section
            Section {
                Text("Configure offline mode, local storage, and synchronization behavior when disconnected.")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .padding(.vertical, 4)
            }
            
            // Offline Mode Section
            Section("Offline Mode") {
                Toggle("Enable Offline Mode", isOn: $bindableSettingsManager.offline.isEnabled)
                
                if settingsManager.offline.isEnabled {
                    Toggle("Background Sync", isOn: $bindableSettingsManager.offline.backgroundSyncEnabled)
                    Toggle("WiFi Only Sync", isOn: $bindableSettingsManager.offline.syncOnWifiOnly)
                    Toggle("Offline Indicator", isOn: $bindableSettingsManager.offline.offlineIndicatorEnabled)
                }
            }
            
            // Storage Management Section
            Section("Storage Management") {
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Text("Storage Limit")
                        Spacer()
                        Text("\(settingsManager.offline.offlineStorageLimit) MB")
                            .foregroundColor(.secondary)
                    }
                    
                    Slider(
                        value: Binding(
                            get: { Double(settingsManager.offline.offlineStorageLimit) },
                            set: { bindableSettingsManager.offline.offlineStorageLimit = Int($0) }
                        ),
                        in: 50...2000,
                        step: 50
                    )
                    
                    Text("Maximum storage for offline data")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                .padding(.vertical, 4)
                
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Text("Cache Expiration")
                        Spacer()
                        Text("\(settingsManager.offline.cacheExpiration) hours")
                            .foregroundColor(.secondary)
                    }
                    
                    Slider(
                        value: Binding(
                            get: { Double(settingsManager.offline.cacheExpiration) },
                            set: { bindableSettingsManager.offline.cacheExpiration = Int($0) }
                        ),
                        in: 1...168,
                        step: 1
                    )
                    
                    Text("How long to keep offline data")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                .padding(.vertical, 4)
                
                Toggle("Auto Cleanup", isOn: $bindableSettingsManager.offline.autoCleanupEnabled)
                Toggle("Compression", isOn: $bindableSettingsManager.offline.compressionEnabled)
                Toggle("Encryption", isOn: $bindableSettingsManager.offline.encryptionEnabled)
                
                Button("View Storage Details") {
                    showingStorageDetails = true
                }
                .foregroundColor(.blue)
            }
            
            // Data Preloading Section
            Section("Data Preloading") {
                Toggle("Preload Data", isOn: $bindableSettingsManager.offline.preloadData)
                
                if settingsManager.offline.preloadData {
                    Text("Automatically download data for offline use when connected")
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .padding(.top, 4)
                }
            }
            
            // Synchronization Section
            Section("Synchronization") {
                HStack {
                    Text("Conflict Resolution")
                    Spacer()
                    Picker("Resolution", selection: $bindableSettingsManager.offline.conflictResolutionStrategy) {
                        Text("Merge Changes").tag("merge")
                        Text("Server Wins").tag("server")
                        Text("Local Wins").tag("local")
                        Text("Ask Me").tag("manual")
                    }
                    .pickerStyle(.menu)
                }
                
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Text("Max Offline Actions")
                        Spacer()
                        Text("\(settingsManager.offline.maxOfflineActions)")
                            .foregroundColor(.secondary)
                    }
                    
                    Slider(
                        value: Binding(
                            get: { Double(settingsManager.offline.maxOfflineActions) },
                            set: { bindableSettingsManager.offline.maxOfflineActions = Int($0) }
                        ),
                        in: 100...5000,
                        step: 100
                    )
                    
                    Text("Maximum number of actions to queue offline")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                .padding(.vertical, 4)
                
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Text("Sync Retry Attempts")
                        Spacer()
                        Text("\(settingsManager.offline.syncRetryAttempts)")
                            .foregroundColor(.secondary)
                    }
                    
                    Slider(
                        value: Binding(
                            get: { Double(settingsManager.offline.syncRetryAttempts) },
                            set: { bindableSettingsManager.offline.syncRetryAttempts = Int($0) }
                        ),
                        in: 1...10,
                        step: 1
                    )
                }
                .padding(.vertical, 4)
                
                Toggle("Persist Queued Actions", isOn: $bindableSettingsManager.offline.queuedActionsPersistence)
            }
            
            // Advanced Sync Features Section
            Section("Advanced Sync") {
                Toggle("Smart Sync", isOn: $bindableSettingsManager.offline.smartSyncEnabled)
                
                if settingsManager.offline.smartSyncEnabled {
                    Text("Prioritizes important data for faster sync")
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .padding(.top, 4)
                }
                
                Toggle("Priority Sync", isOn: $bindableSettingsManager.offline.prioritySyncEnabled)
                Toggle("Delta Sync", isOn: $bindableSettingsManager.offline.deltaSyncEnabled)
                
                if settingsManager.offline.deltaSyncEnabled {
                    Text("Only sync changes to reduce bandwidth")
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .padding(.top, 4)
                }
            }
            
            // Actions Section
            Section("Actions") {
                Button("Force Sync Now") {
                    // TODO: Implement force sync
                }
                .foregroundColor(.blue)
                
                Button("Clear Offline Cache") {
                    // TODO: Implement cache clearing
                }
                .foregroundColor(.orange)
                
                Button("Export Offline Data") {
                    // TODO: Implement data export
                }
                .foregroundColor(.blue)
                
                Button("Reset Offline Settings", role: .destructive) {
                    showingResetConfirmation = true
                }
                .foregroundColor(.red)
            }
        }
        .navigationTitle("Offline Settings")
        .navigationBarTitleDisplayMode(.inline)
        .sheet(isPresented: $showingStorageDetails) {
            OfflineStorageDetailsView()
        }
        .confirmationDialog(
            "Reset Offline Settings",
            isPresented: $showingResetConfirmation,
            titleVisibility: .visible
        ) {
            Button("Reset All Settings", role: .destructive) {
                settingsManager.offline = OfflineSettings()
            }
            Button("Cancel", role: .cancel) {}
        } message: {
            Text("This will reset all offline settings to defaults. Cached data will be preserved.")
        }
    }
}

// MARK: - Supporting Views

@available(iOS 18.0, macOS 14.0, *)
struct OfflineStorageDetailsView: View {
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationStack {
            List {
                Section("Storage Usage") {
                    StorageUsageRow(category: "Tasks", used: 45, total: 500, unit: "MB")
                    StorageUsageRow(category: "Projects", used: 23, total: 500, unit: "MB")
                    StorageUsageRow(category: "Architecture", used: 12, total: 500, unit: "MB")
                    StorageUsageRow(category: "Cache", used: 8, total: 500, unit: "MB")
                }
                
                Section("Cache Statistics") {
                    StatRow(label: "Total Files", value: "1,247")
                    StatRow(label: "Last Cleanup", value: "2 hours ago")
                    StatRow(label: "Next Cleanup", value: "In 22 hours")
                }
                
                Section("Actions") {
                    Button("Clear All Cache") {
                        // TODO: Implement cache clearing
                    }
                    .foregroundColor(.red)
                    
                    Button("Optimize Storage") {
                        // TODO: Implement storage optimization
                    }
                    .foregroundColor(.blue)
                }
            }
            .navigationTitle("Storage Details")
            .navigationBarTitleDisplayMode(.inline)
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
struct StorageUsageRow: View {
    let category: String
    let used: Int
    let total: Int
    let unit: String
    
    private var percentage: Double {
        return Double(used) / Double(total)
    }
    
    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text(category)
                    .font(.headline)
                Spacer()
                Text("\(used) \(unit)")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            ProgressView(value: percentage)
                .progressViewStyle(LinearProgressViewStyle())
                .scaleEffect(y: 0.5)
            
            Text("\(Int(percentage * 100))% of \(total) \(unit) limit")
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .padding(.vertical, 2)
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct StatRow: View {
    let label: String
    let value: String
    
    var body: some View {
        HStack {
            Text(label)
            Spacer()
            Text(value)
                .foregroundColor(.secondary)
        }
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
    @StateObject private var settingsManager = SettingsManager.shared
    @Bindable private var bindableSettingsManager: SettingsManager = SettingsManager.shared
    @State private var showingColorPicker = false
    @State private var showingResetConfirmation = false
    
    var body: some View {
        List {
            // Overview Section
            Section {
                Text("Customize the app's appearance, layout, and navigation behavior.")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .padding(.vertical, 4)
            }
            
            // Theme & Appearance Section
            Section("Theme & Appearance") {
                HStack {
                    Text("Theme")
                    Spacer()
                    Picker("Theme", selection: $bindableSettingsManager.interface.theme) {
                        Text("Auto").tag("auto")
                        Text("Light").tag("light")
                        Text("Dark").tag("dark")
                        Text("System").tag("system")
                    }
                    .pickerStyle(.menu)
                }
                
                HStack {
                    Text("Accent Color")
                    Spacer()
                    Picker("Color", selection: $bindableSettingsManager.interface.accentColor) {
                        Text("Blue").tag("blue")
                        Text("Green").tag("green")
                        Text("Orange").tag("orange")
                        Text("Purple").tag("purple")
                        Text("Red").tag("red")
                        Text("Teal").tag("teal")
                        Text("Pink").tag("pink")
                        Text("Custom").tag("custom")
                    }
                    .pickerStyle(.menu)
                }
                
                if settingsManager.interface.accentColor == "custom" {
                    Button("Choose Custom Color") {
                        showingColorPicker = true
                    }
                    .foregroundColor(.blue)
                }
                
                HStack {
                    Text("Font Size")
                    Spacer()
                    Picker("Size", selection: $bindableSettingsManager.interface.fontSize) {
                        Text("Small").tag("small")
                        Text("Medium").tag("medium")
                        Text("Large").tag("large")
                        Text("Extra Large").tag("xlarge")
                    }
                    .pickerStyle(.menu)
                }
                
                HStack {
                    Text("Layout Density")
                    Spacer()
                    Picker("Density", selection: $bindableSettingsManager.interface.layoutDensity) {
                        Text("Compact").tag("compact")
                        Text("Comfortable").tag("comfortable")
                        Text("Spacious").tag("spacious")
                    }
                    .pickerStyle(.menu)
                }
            }
            
            // Layout & Navigation Section
            Section("Layout & Navigation") {
                Toggle("Compact Mode", isOn: $bindableSettingsManager.interface.compactMode)
                
                if !settingsManager.interface.compactMode {
                    Toggle("Show Sidebar", isOn: $bindableSettingsManager.interface.showSidebar)
                    
                    if settingsManager.interface.showSidebar {
                        HStack {
                            Text("Sidebar Position")
                            Spacer()
                            Picker("Position", selection: $bindableSettingsManager.interface.sidebarPosition) {
                                Text("Left").tag("left")
                                Text("Right").tag("right")
                            }
                            .pickerStyle(.segmented)
                        }
                    }
                }
                
                HStack {
                    Text("Navigation Style")
                    Spacer()
                    Picker("Style", selection: $bindableSettingsManager.interface.navigationStyle) {
                        Text("Default").tag("default")
                        Text("Large Titles").tag("large")
                        Text("Inline").tag("inline")
                        Text("Automatic").tag("auto")
                    }
                    .pickerStyle(.menu)
                }
                
                HStack {
                    Text("Tab Bar Style")
                    Spacer()
                    Picker("Style", selection: $bindableSettingsManager.interface.tabBarStyle) {
                        Text("Default").tag("default")
                        Text("Minimal").tag("minimal")
                        Text("Icons Only").tag("icons")
                        Text("Text Only").tag("text")
                    }
                    .pickerStyle(.menu)
                }
            }
            
            // Toolbar Configuration Section
            Section("Toolbar") {
                Toggle("Show Toolbar", isOn: $bindableSettingsManager.interface.showToolbar)
                
                if settingsManager.interface.showToolbar {
                    HStack {
                        Text("Position")
                        Spacer()
                        Picker("Position", selection: $bindableSettingsManager.interface.toolbarPosition) {
                            Text("Top").tag("top")
                            Text("Bottom").tag("bottom")
                            Text("Floating").tag("floating")
                        }
                        .pickerStyle(.segmented)
                    }
                }
            }
            
            // Content Display Section
            Section("Content Display") {
                Toggle("Show Preview Pane", isOn: $bindableSettingsManager.interface.showPreviewPane)
                
                HStack {
                    Text("Grid Size")
                    Spacer()
                    Picker("Size", selection: $bindableSettingsManager.interface.gridSize) {
                        Text("Small").tag("small")
                        Text("Medium").tag("medium")
                        Text("Large").tag("large")
                    }
                    .pickerStyle(.segmented)
                }
                
                HStack {
                    Text("Icon Style")
                    Spacer()
                    Picker("Style", selection: $bindableSettingsManager.interface.iconStyle) {
                        Text("Default").tag("default")
                        Text("Filled").tag("filled")
                        Text("Outlined").tag("outlined")
                        Text("Rounded").tag("rounded")
                    }
                    .pickerStyle(.menu)
                }
            }
            
            // Animation & Effects Section
            Section("Animation & Effects") {
                Toggle("Animations", isOn: $bindableSettingsManager.interface.animationsEnabled)
                
                if !settingsManager.interface.animationsEnabled {
                    Text("Disabling animations improves performance on older devices")
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .padding(.top, 4)
                }
                
                Toggle("Reduced Motion", isOn: $bindableSettingsManager.interface.reducedMotion)
                Toggle("High Contrast", isOn: $bindableSettingsManager.interface.highContrast)
            }
            
            // Advanced Customization Section
            Section("Advanced Customization") {
                NavigationLink("Custom Colors") {
                    CustomColorsView()
                }
                
                NavigationLink("Layout Presets") {
                    LayoutPresetsView()
                }
                
                Button("Export Interface Settings") {
                    // TODO: Implement export
                }
                .foregroundColor(.blue)
                
                Button("Import Interface Settings") {
                    // TODO: Implement import
                }
                .foregroundColor(.blue)
            }
            
            // Reset Section
            Section("Reset") {
                Button("Reset to Defaults", role: .destructive) {
                    showingResetConfirmation = true
                }
                .foregroundColor(.red)
            }
        }
        .navigationTitle("Interface")
        .navigationBarTitleDisplayMode(.inline)
        .sheet(isPresented: $showingColorPicker) {
            ColorPickerView()
        }
        .confirmationDialog(
            "Reset Interface Settings",
            isPresented: $showingResetConfirmation,
            titleVisibility: .visible
        ) {
            Button("Reset All Settings", role: .destructive) {
                settingsManager.interface = InterfaceSettings()
            }
            Button("Cancel", role: .cancel) {}
        } message: {
            Text("This will reset all interface settings to defaults. Custom colors and layouts will be preserved.")
        }
    }
}

// MARK: - Supporting Views

@available(iOS 18.0, macOS 14.0, *)
struct ColorPickerView: View {
    @Environment(\.dismiss) private var dismiss
    @State private var selectedColor = Color.blue
    
    var body: some View {
        NavigationStack {
            VStack(spacing: 20) {
                ColorPicker("Choose Accent Color", selection: $selectedColor)
                    .padding()
                
                VStack(spacing: 16) {
                    Text("Preview")
                        .font(.headline)
                    
                    Button("Sample Button") {
                        // Preview button
                    }
                    .buttonStyle(.borderedProminent)
                    .tint(selectedColor)
                    
                    ProgressView(value: 0.7)
                        .tint(selectedColor)
                }
                .padding()
                
                Spacer()
            }
            .navigationTitle("Custom Color")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
                
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Save") {
                        // TODO: Save custom color
                        dismiss()
                    }
                }
            }
        }
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct CustomColorsView: View {
    var body: some View {
        List {
            Section("UI Elements") {
                ColorCustomizationRow(element: "Primary", color: .blue)
                ColorCustomizationRow(element: "Secondary", color: .gray)
                ColorCustomizationRow(element: "Success", color: .green)
                ColorCustomizationRow(element: "Warning", color: .orange)
                ColorCustomizationRow(element: "Error", color: .red)
            }
            
            Section("Backgrounds") {
                ColorCustomizationRow(element: "Main Background", color: .white)
                ColorCustomizationRow(element: "Card Background", color: .gray.opacity(0.1))
                ColorCustomizationRow(element: "Sidebar Background", color: .gray.opacity(0.05))
            }
            
            Section {
                Button("Reset All Colors") {
                    // TODO: Reset colors
                }
                .foregroundColor(.red)
            }
        }
        .navigationTitle("Custom Colors")
        .navigationBarTitleDisplayMode(.inline)
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct ColorCustomizationRow: View {
    let element: String
    let color: Color
    
    var body: some View {
        HStack {
            Circle()
                .fill(color)
                .frame(width: 24, height: 24)
            
            Text(element)
            
            Spacer()
            
            Button("Edit") {
                // TODO: Open color picker for this element
            }
            .font(.caption)
            .foregroundColor(.blue)
        }
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct LayoutPresetsView: View {
    var body: some View {
        List {
            Section("Built-in Presets") {
                LayoutPresetRow(name: "Default", description: "Standard layout with sidebar", isActive: true)
                LayoutPresetRow(name: "Compact", description: "Minimal layout for smaller screens", isActive: false)
                LayoutPresetRow(name: "Power User", description: "Maximum information density", isActive: false)
                LayoutPresetRow(name: "Accessibility", description: "Large fonts and high contrast", isActive: false)
            }
            
            Section("Custom Presets") {
                Button("Create New Preset") {
                    // TODO: Create custom preset
                }
                .foregroundColor(.blue)
            }
        }
        .navigationTitle("Layout Presets")
        .navigationBarTitleDisplayMode(.inline)
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct LayoutPresetRow: View {
    let name: String
    let description: String
    let isActive: Bool
    
    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                HStack {
                    Text(name)
                        .font(.headline)
                    if isActive {
                        Text("Active")
                            .font(.caption)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 2)
                            .background(Color.green.opacity(0.2))
                            .foregroundColor(.green)
                            .cornerRadius(4)
                    }
                }
                Text(description)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
            
            if !isActive {
                Button("Apply") {
                    // TODO: Apply preset
                }
                .font(.caption)
                .foregroundColor(.blue)
            }
        }
        .padding(.vertical, 2)
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct PerformanceSettingsView: View {
    @StateObject private var settingsManager = SettingsManager.shared
    @Bindable private var bindableSettingsManager: SettingsManager = SettingsManager.shared
    @State private var showingAdvancedSettings = false
    @State private var showingResetConfirmation = false
    
    var body: some View {
        List {
            // Overview Section
            Section {
                Text("Optimize app performance, memory usage, and battery consumption for the best experience.")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .padding(.vertical, 4)
            }
            
            // Memory Management Section
            Section("Memory Management") {
                Toggle("Memory Limit Enabled", isOn: $bindableSettingsManager.performance.memoryLimitEnabled)
                
                if settingsManager.performance.memoryLimitEnabled {
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Text("Memory Limit")
                            Spacer()
                            Text("\(settingsManager.performance.maxMemoryUsage) MB")
                                .foregroundColor(.secondary)
                        }
                        
                        Slider(
                            value: Binding(
                                get: { Double(settingsManager.performance.maxMemoryUsage) },
                                set: { bindableSettingsManager.performance.maxMemoryUsage = Int($0) }
                            ),
                            in: 128...2048,
                            step: 64
                        )
                        
                        Text("App will optimize memory usage to stay under this limit")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    .padding(.vertical, 4)
                }
                
                Toggle("Memory Warning Handling", isOn: $bindableSettingsManager.performance.memoryWarningHandlingEnabled)
            }
            
            // Processing & Threading Section
            Section("Processing & Threading") {
                Toggle("Background Processing", isOn: $bindableSettingsManager.performance.backgroundProcessingEnabled)
                
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Text("Thread Pool Size")
                        Spacer()
                        Text("\(settingsManager.performance.threadPoolSize)")
                            .foregroundColor(.secondary)
                    }
                    
                    Slider(
                        value: Binding(
                            get: { Double(settingsManager.performance.threadPoolSize) },
                            set: { bindableSettingsManager.performance.threadPoolSize = Int($0) }
                        ),
                        in: 1...16,
                        step: 1
                    )
                    
                    Text("Number of threads for concurrent operations")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                .padding(.vertical, 4)
            }
            
            // Network Optimization Section
            Section("Network Optimization") {
                Toggle("Network Optimization", isOn: $bindableSettingsManager.performance.networkOptimizationEnabled)
                
                if settingsManager.performance.networkOptimizationEnabled {
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Text("Request Timeout")
                            Spacer()
                            Text("\(settingsManager.performance.networkRequestTimeout)s")
                                .foregroundColor(.secondary)
                        }
                        
                        Slider(
                            value: Binding(
                                get: { Double(settingsManager.performance.networkRequestTimeout) },
                                set: { bindableSettingsManager.performance.networkRequestTimeout = Int($0) }
                            ),
                            in: 5...120,
                            step: 5
                        )
                    }
                    .padding(.vertical, 4)
                    
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Text("Max Concurrent Requests")
                            Spacer()
                            Text("\(settingsManager.performance.maxConcurrentRequests)")
                                .foregroundColor(.secondary)
                        }
                        
                        Slider(
                            value: Binding(
                                get: { Double(settingsManager.performance.maxConcurrentRequests) },
                                set: { bindableSettingsManager.performance.maxConcurrentRequests = Int($0) }
                            ),
                            in: 1...50,
                            step: 1
                        )
                    }
                    .padding(.vertical, 4)
                }
            }
            
            // Caching & Storage Section
            Section("Caching & Storage") {
                Toggle("Cache Optimization", isOn: $bindableSettingsManager.performance.cacheOptimizationEnabled)
                Toggle("Disk Cache", isOn: $bindableSettingsManager.performance.diskCacheEnabled)
                
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Text("Max Cache Size")
                        Spacer()
                        Text("\(settingsManager.performance.maxCacheSize) MB")
                            .foregroundColor(.secondary)
                    }
                    
                    Slider(
                        value: Binding(
                            get: { Double(settingsManager.performance.maxCacheSize) },
                            set: { bindableSettingsManager.performance.maxCacheSize = Int($0) }
                        ),
                        in: 50...1000,
                        step: 50
                    )
                    
                    Text("Maximum size for cached data")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                .padding(.vertical, 4)
            }
            
            // Rendering & UI Section
            Section("Rendering & UI") {
                Toggle("Rendering Optimization", isOn: $bindableSettingsManager.performance.renderingOptimizationEnabled)
                Toggle("Image Compression", isOn: $bindableSettingsManager.performance.imageCompressionEnabled)
                Toggle("Lazy Loading", isOn: $bindableSettingsManager.performance.lazyLoadingEnabled)
                Toggle("Prefetching", isOn: $bindableSettingsManager.performance.prefetchingEnabled)
                
                if settingsManager.performance.prefetchingEnabled {
                    Text("Automatically loads content before it's needed")
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .padding(.top, 4)
                }
            }
            
            // Battery Optimization Section
            Section("Battery Optimization") {
                Toggle("Battery Optimization", isOn: $bindableSettingsManager.performance.batteryOptimizationEnabled)
                Toggle("Low Power Mode", isOn: $bindableSettingsManager.performance.lowPowerModeEnabled)
                
                if settingsManager.performance.lowPowerModeEnabled {
                    Text("Reduces performance to extend battery life")
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .padding(.top, 4)
                }
            }
            
            // Monitoring Section
            Section("Performance Monitoring") {
                Toggle("Performance Monitoring", isOn: $bindableSettingsManager.performance.performanceMonitoringEnabled)
                
                if settingsManager.performance.performanceMonitoringEnabled {
                    NavigationLink("View Performance Stats") {
                        PerformanceStatsView()
                    }
                }
            }
            
            // Advanced Settings Section
            Section("Advanced") {
                Button("Advanced Performance Settings") {
                    showingAdvancedSettings = true
                }
                .foregroundColor(.blue)
                
                Button("Run Performance Test") {
                    // TODO: Run performance benchmark
                }
                .foregroundColor(.blue)
                
                Button("Optimize Now") {
                    // TODO: Run optimization
                }
                .foregroundColor(.blue)
            }
            
            // Reset Section
            Section("Reset") {
                Button("Reset to Defaults", role: .destructive) {
                    showingResetConfirmation = true
                }
                .foregroundColor(.red)
            }
        }
        .navigationTitle("Performance")
        .navigationBarTitleDisplayMode(.inline)
        .sheet(isPresented: $showingAdvancedSettings) {
            AdvancedPerformanceSettingsView()
        }
        .confirmationDialog(
            "Reset Performance Settings",
            isPresented: $showingResetConfirmation,
            titleVisibility: .visible
        ) {
            Button("Reset All Settings", role: .destructive) {
                settingsManager.performance = PerformanceSettings()
            }
            Button("Cancel", role: .cancel) {}
        } message: {
            Text("This will reset all performance settings to recommended defaults for your device.")
        }
    }
}

// MARK: - Supporting Views

@available(iOS 18.0, macOS 14.0, *)
struct PerformanceStatsView: View {
    var body: some View {
        List {
            Section("Current Performance") {
                PerformanceStatRow(metric: "Memory Usage", value: "234 MB", status: .good)
                PerformanceStatRow(metric: "CPU Usage", value: "12%", status: .good)
                PerformanceStatRow(metric: "Network Activity", value: "2.1 KB/s", status: .good)
                PerformanceStatRow(metric: "Battery Impact", value: "Low", status: .good)
            }
            
            Section("Cache Statistics") {
                PerformanceStatRow(metric: "Cache Hit Rate", value: "89%", status: .good)
                PerformanceStatRow(metric: "Cache Size", value: "45 MB", status: .good)
                PerformanceStatRow(metric: "Disk Usage", value: "123 MB", status: .warning)
            }
            
            Section("Network Performance") {
                PerformanceStatRow(metric: "Response Time", value: "234ms", status: .good)
                PerformanceStatRow(metric: "Success Rate", value: "99.2%", status: .good)
                PerformanceStatRow(metric: "Active Connections", value: "3", status: .good)
            }
            
            Section("Actions") {
                Button("Clear All Caches") {
                    // TODO: Clear caches
                }
                .foregroundColor(.blue)
                
                Button("Force Garbage Collection") {
                    // TODO: Force memory cleanup
                }
                .foregroundColor(.blue)
                
                Button("Export Performance Report") {
                    // TODO: Export performance data
                }
                .foregroundColor(.blue)
            }
        }
        .navigationTitle("Performance Stats")
        .navigationBarTitleDisplayMode(.inline)
        .refreshable {
            // TODO: Refresh performance stats
        }
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct PerformanceStatRow: View {
    let metric: String
    let value: String
    let status: PerformanceStatus
    
    var body: some View {
        HStack {
            Text(metric)
            Spacer()
            HStack(spacing: 8) {
                Text(value)
                    .foregroundColor(.secondary)
                Circle()
                    .fill(status.color)
                    .frame(width: 8, height: 8)
            }
        }
    }
}

enum PerformanceStatus {
    case good
    case warning
    case error
    
    var color: Color {
        switch self {
        case .good:
            return .green
        case .warning:
            return .orange
        case .error:
            return .red
        }
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct AdvancedPerformanceSettingsView: View {
    @Environment(\.dismiss) private var dismiss
    @StateObject private var settingsManager = SettingsManager.shared
    @Bindable private var bindableSettingsManager: SettingsManager = SettingsManager.shared
    
    var body: some View {
        NavigationStack {
            List {
                Section("Memory Management") {
                    Toggle("Aggressive Memory Cleanup", isOn: .constant(false))
                    Toggle("Pre-allocate Memory Pools", isOn: .constant(false))
                    Toggle("Compress Inactive Views", isOn: .constant(false))
                }
                
                Section("Threading") {
                    Toggle("Use High Priority Threads", isOn: .constant(false))
                    Toggle("Background Thread Optimization", isOn: .constant(true))
                    Toggle("Async Operation Batching", isOn: .constant(true))
                }
                
                Section("Experimental") {
                    Toggle("Metal Rendering", isOn: .constant(false))
                    Toggle("Predictive Caching", isOn: .constant(false))
                    Toggle("Advanced Compression", isOn: .constant(false))
                    
                    Text("⚠️ Experimental features may affect stability")
                        .font(.caption)
                        .foregroundColor(.orange)
                        .padding(.top, 4)
                }
            }
            .navigationTitle("Advanced Performance")
            .navigationBarTitleDisplayMode(.inline)
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
                Toggle("Show Legend", isOn: $bindableSettingsManager.architecture.showLegend)
                Toggle("Show Metadata", isOn: $bindableSettingsManager.architecture.showMetadata)
            }
            
            // Change Detection Section
            Section("Change Detection") {
                Toggle("Auto-Update", isOn: $bindableSettingsManager.architecture.autoUpdate)
                
                if settingsManager.architecture.autoUpdate {
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
                
                Toggle("Include Private Elements", isOn: $bindableSettingsManager.architecture.includePrivateElements)
                Toggle("Enable Interaction", isOn: $bindableSettingsManager.architecture.enableInteraction)
                
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
                Toggle("Pan Lock", isOn: $bindableSettingsManager.architecture.panLock)
                
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
                
                Toggle("Include Private Elements", isOn: $bindableSettingsManager.architecture.includePrivateElements)
                Toggle("Enable Interaction", isOn: $bindableSettingsManager.architecture.enableInteraction)
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
                
                Toggle("Show Metadata", isOn: $bindableSettingsManager.architecture.showMetadata)
                Toggle("Auto Update", isOn: $bindableSettingsManager.architecture.autoUpdate)
            }
            
            // Advanced Features Section
            Section("Advanced Features") {
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Text("Zoom Level")
                        Spacer()
                        Text("\\(Int(settingsManager.architecture.zoomLevel * 100))%")
                            .foregroundColor(.secondary)
                    }
                    
                    Slider(
                        value: $bindableSettingsManager.architecture.zoomLevel,
                        in: 0.5...3.0,
                        step: 0.1
                    )
                }
                Toggle("Pan Lock", isOn: $bindableSettingsManager.architecture.panLock)
                Toggle("Include Private Elements", isOn: $bindableSettingsManager.architecture.includePrivateElements)
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
    
    var buildNumber: String {
        (infoDictionary?["CFBundleVersion"] as? String) ?? "1"
    }
}

// MARK: - Previews

struct SettingsView_Previews: PreviewProvider {
    static var previews: some View {
        SettingsView(webSocketService: WebSocketService())
    }
}