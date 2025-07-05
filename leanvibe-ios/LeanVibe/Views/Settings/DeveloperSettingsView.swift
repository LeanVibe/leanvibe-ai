import SwiftUI

/// Developer Settings View - Debug tools and development features
@available(iOS 18.0, macOS 14.0, *)
struct DeveloperSettingsView: View {
    
    // MARK: - Properties
    
    @StateObject private var featureFlagManager = FeatureFlagManager.shared
    @StateObject private var settingsManager = SettingsManager.shared
    @State private var showingResetConfirmation = false
    @State private var showingCacheCleared = false
    
    // MARK: - Body
    
    var body: some View {
        List {
            debugInfoSection
            featureFlagSection
            dataManagementSection
            performanceSection
            loggingSection
        }
        .navigationTitle("Developer Settings")
        .navigationBarTitleDisplayMode(.inline)
        .alert("Reset All Settings", isPresented: $showingResetConfirmation) {
            Button("Reset", role: .destructive) {
                resetAllSettings()
            }
            Button("Cancel", role: .cancel) { }
        } message: {
            Text("This will reset all settings to defaults. This action cannot be undone.")
        }
        .alert("Cache Cleared", isPresented: $showingCacheCleared) {
            Button("OK") { }
        } message: {
            Text("All cached data has been cleared successfully.")
        }
    }
    
    // MARK: - View Sections
    
    private var debugInfoSection: some View {
        Section("Debug Information") {
            LabeledContent("Build Configuration", value: buildConfiguration)
            LabeledContent("App Version", value: appVersion)
            LabeledContent("Build Number", value: buildNumber)
            LabeledContent("iOS Version", value: iosVersion)
            LabeledContent("Device Model", value: deviceModel)
        }
    }
    
    private var featureFlagSection: some View {
        Section("Feature Flags") {
            NavigationLink("Feature Flag Debug") {
                FeatureFlagDebugView()
            }
            
            Button("Reset Feature Flags") {
                featureFlagManager.resetToDefaults()
            }
            .foregroundColor(.blue)
        }
    }
    
    private var dataManagementSection: some View {
        Section("Data Management") {
            Button("Clear All Caches") {
                clearAllCaches()
                showingCacheCleared = true
            }
            .foregroundColor(.blue)
            
            Button("Export Settings") {
                exportSettings()
            }
            .foregroundColor(.blue)
            
            Button("Reset All Settings") {
                showingResetConfirmation = true
            }
            .foregroundColor(.red)
        }
    }
    
    private var performanceSection: some View {
        Section("Performance") {
            NavigationLink("Performance Monitor") {
                SystemHealthDashboard()
            }
            
            NavigationLink("Error History") {
                ErrorHistoryView()
            }
            
            NavigationLink("Retry Monitor") {
                RetryMonitorView(retryManager: RetryManager.shared)
            }
        }
    }
    
    private var loggingSection: some View {
        Section("Logging") {
            Toggle("Verbose Logging", isOn: .constant(true))
                .disabled(true) // Always enabled in debug builds
            
            Toggle("Network Logging", isOn: .constant(true))
                .disabled(true) // Always enabled in debug builds
            
            Button("Export Logs") {
                exportLogs()
            }
            .foregroundColor(.blue)
        }
    }
    
    // MARK: - Computed Properties
    
    private var buildConfiguration: String {
        #if DEBUG
        return "Debug"
        #else
        return "Release"
        #endif
    }
    
    private var appVersion: String {
        Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "Unknown"
    }
    
    private var buildNumber: String {
        Bundle.main.infoDictionary?["CFBundleVersion"] as? String ?? "Unknown"
    }
    
    private var iosVersion: String {
        UIDevice.current.systemVersion
    }
    
    private var deviceModel: String {
        UIDevice.current.model
    }
    
    // MARK: - Actions
    
    private func clearAllCaches() {
        // Clear UserDefaults cache
        URLCache.shared.removeAllCachedResponses()
        
        // Clear settings cache if applicable
        // This is a placeholder for actual cache clearing logic
        print("🧹 Developer: All caches cleared")
    }
    
    private func exportSettings() {
        // Export current settings configuration
        // This is a placeholder for actual export logic
        print("📤 Developer: Settings exported")
    }
    
    private func resetAllSettings() {
        // Reset to factory defaults
        settingsManager.resetToDefaults()
        featureFlagManager.resetToDefaults()
        print("🔄 Developer: All settings reset to defaults")
    }
    
    private func exportLogs() {
        // Export application logs
        // This is a placeholder for actual log export logic
        print("📋 Developer: Logs exported")
    }
}

#if DEBUG
@available(iOS 18.0, macOS 14.0, *)
struct DeveloperSettingsView_Previews: PreviewProvider {
    static var previews: some View {
        NavigationView {
            DeveloperSettingsView()
        }
    }
}
#endif