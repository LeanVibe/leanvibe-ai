import SwiftUI

@available(iOS 18.0, macOS 14.0, *)
struct SyncSettingsView: View {
    @ObservedObject var settingsManager: SettingsManager
    @State private var autoSyncEnabled = true
    @State private var syncInterval: SyncInterval = .realTime
    @State private var wifiOnlySync = false
    @State private var conflictResolution: ConflictResolution = .mergeChanges
    @State private var lastSyncTime: Date?
    @State private var isSyncing = false
    @State private var syncStatus: SyncStatus = .idle
    @Environment(\.dismiss) private var dismiss
    
    init(settingsManager: SettingsManager) {
        self.settingsManager = settingsManager
        self._lastSyncTime = State(initialValue: Date().addingTimeInterval(-3600)) // 1 hour ago
    }
    
    init() {
        self.settingsManager = SettingsManager.shared
        self._lastSyncTime = State(initialValue: Date().addingTimeInterval(-3600)) // 1 hour ago
    }
    
    var body: some View {
        NavigationView {
            List {
                Section {
                    Text("Configure how your data synchronizes across devices and with the backend server.")
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .padding(.vertical, 4)
                }
                
                Section("Sync Status") {
                    HStack {
                        Image(systemName: syncStatus.iconName)
                            .foregroundColor(syncStatus.color)
                        VStack(alignment: .leading) {
                            Text(syncStatus.displayName)
                                .font(.headline)
                            if let lastSync = lastSyncTime {
                                Text("Last sync: \(lastSync, formatter: relativeDateFormatter)")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                        }
                        Spacer()
                        if isSyncing {
                            ProgressView()
                                .scaleEffect(0.8)
                        }
                    }
                    .padding(.vertical, 4)
                }
                
                Section("Sync Settings") {
                    Toggle("Auto-Sync", isOn: $autoSyncEnabled)
                    
                    if autoSyncEnabled {
                        Picker("Sync Interval", selection: $syncInterval) {
                            ForEach(SyncInterval.allCases, id: \.self) { interval in
                                Text(interval.displayName).tag(interval)
                            }
                        }
                    }
                    
                    Toggle("Wi-Fi Only", isOn: $wifiOnlySync)
                    
                    Picker("Conflict Resolution", selection: $conflictResolution) {
                        ForEach(ConflictResolution.allCases, id: \.self) { resolution in
                            Text(resolution.displayName).tag(resolution)
                        }
                    }
                }
                
                Section("Data Types") {
                    SyncDataTypeRow(
                        title: "Projects",
                        subtitle: "Project configurations and metadata",
                        isEnabled: .constant(true),
                        lastSync: lastSyncTime
                    )
                    
                    SyncDataTypeRow(
                        title: "Tasks",
                        subtitle: "Task boards and progress tracking",
                        isEnabled: .constant(true),
                        lastSync: lastSyncTime
                    )
                    
                    SyncDataTypeRow(
                        title: "Settings",
                        subtitle: "App preferences and configurations",
                        isEnabled: .constant(false),
                        lastSync: nil
                    )
                    
                    SyncDataTypeRow(
                        title: "Architecture Diagrams",
                        subtitle: "Generated and cached diagrams",
                        isEnabled: .constant(true),
                        lastSync: lastSyncTime?.addingTimeInterval(-1800)
                    )
                }
                
                Section("Manual Actions") {
                    Button("Sync Now") {
                        performManualSync()
                    }
                    .foregroundColor(Color(.systemBlue))
                    .disabled(isSyncing)
                    
                    Button("Force Full Sync") {
                        performFullSync()
                    }
                    .foregroundColor(Color(.systemOrange))
                    .disabled(isSyncing)
                    
                    Button("Clear Local Cache") {
                        clearLocalCache()
                    }
                    .foregroundColor(Color(.systemRed))
                }
                
                Section("Connection Info") {
                    ConnectionStatusRow(
                        title: "Backend Server",
                        status: .connected,
                        details: "leanvibe-backend:8000"
                    )
                    
                    ConnectionStatusRow(
                        title: "WebSocket",
                        status: .connected,
                        details: "Real-time updates active"
                    )
                    
                    ConnectionStatusRow(
                        title: "File System",
                        status: .connected,
                        details: "Local project discovery"
                    )
                }
            }
            .navigationTitle("Sync Settings")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Done") {
                        saveSettings()
                        dismiss()
                    }
                }
            }
        }
    }
    
    private func performManualSync() {
        isSyncing = true
        syncStatus = .syncing
        
        DispatchQueue.main.asyncAfter(deadline: .now() + 2.0) {
            isSyncing = false
            syncStatus = .connected
            lastSyncTime = Date()
        }
    }
    
    private func performFullSync() {
        isSyncing = true
        syncStatus = .syncing
        
        DispatchQueue.main.asyncAfter(deadline: .now() + 5.0) {
            isSyncing = false
            syncStatus = .connected
            lastSyncTime = Date()
        }
    }
    
    private func clearLocalCache() {
        // Simulate clearing cache
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
            // Reset sync time to indicate fresh start
            lastSyncTime = nil
        }
    }
    
    private func saveSettings() {
        print("Saving sync settings:")
        print("- Auto-sync: \(autoSyncEnabled)")
        print("- Sync interval: \(syncInterval.rawValue)")
        print("- WiFi only: \(wifiOnlySync)")
        print("- Conflict resolution: \(conflictResolution.rawValue)")
    }
    
    private var relativeDateFormatter: DateFormatter {
        let formatter = DateFormatter()
        formatter.doesRelativeDateFormatting = true
        formatter.dateStyle = .none
        formatter.timeStyle = .short
        return formatter
    }
}

struct SyncDataTypeRow: View {
    let title: String
    let subtitle: String
    @Binding var isEnabled: Bool
    let lastSync: Date?
    
    var body: some View {
        HStack {
            VStack(alignment: .leading) {
                Text(title)
                    .font(.body)
                Text(subtitle)
                    .font(.caption)
                    .foregroundColor(.secondary)
                if let lastSync = lastSync {
                    Text("Last: \(lastSync, formatter: timeFormatter)")
                        .font(.caption2)
                        .foregroundColor(.secondary)
                }
            }
            Spacer()
            Toggle("", isOn: $isEnabled)
                .labelsHidden()
        }
    }
    
    private var timeFormatter: DateFormatter {
        let formatter = DateFormatter()
        formatter.timeStyle = .short
        return formatter
    }
}

struct ConnectionStatusRow: View {
    let title: String
    let status: ConnectionStatus
    let details: String
    
    var body: some View {
        HStack {
            VStack(alignment: .leading) {
                Text(title)
                    .font(.body)
                Text(details)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            Spacer()
            HStack {
                Circle()
                    .fill(status.color)
                    .frame(width: 8, height: 8)
                Text(status.displayName)
                    .font(.caption)
                    .foregroundColor(status.color)
            }
        }
    }
}

enum SyncInterval: String, CaseIterable {
    case realTime = "real_time"
    case fiveMinutes = "5_minutes"
    case fifteenMinutes = "15_minutes"
    case hourly = "hourly"
    case manual = "manual"
    
    var displayName: String {
        switch self {
        case .realTime:
            return "Real-time"
        case .fiveMinutes:
            return "Every 5 minutes"
        case .fifteenMinutes:
            return "Every 15 minutes"
        case .hourly:
            return "Hourly"
        case .manual:
            return "Manual only"
        }
    }
}

enum ConflictResolution: String, CaseIterable {
    case mergeChanges = "merge"
    case serverWins = "server_wins"
    case localWins = "local_wins"
    case askUser = "ask_user"
    
    var displayName: String {
        switch self {
        case .mergeChanges:
            return "Merge Changes"
        case .serverWins:
            return "Server Wins"
        case .localWins:
            return "Local Wins"
        case .askUser:
            return "Ask Me"
        }
    }
}

enum SyncStatus {
    case idle
    case syncing
    case connected
    case disconnected
    case error
    
    var displayName: String {
        switch self {
        case .idle:
            return "Ready"
        case .syncing:
            return "Syncing..."
        case .connected:
            return "Connected"
        case .disconnected:
            return "Disconnected"
        case .error:
            return "Error"
        }
    }
    
    var iconName: String {
        switch self {
        case .idle:
            return "checkmark.circle"
        case .syncing:
            return "arrow.triangle.2.circlepath"
        case .connected:
            return "checkmark.circle.fill"
        case .disconnected:
            return "xmark.circle"
        case .error:
            return "exclamationmark.triangle"
        }
    }
    
    var color: Color {
        switch self {
        case .idle:
            return Color(.systemBlue)
        case .syncing:
            return Color(.systemOrange)
        case .connected:
            return Color(.systemGreen)
        case .disconnected:
            return Color(.systemRed)
        case .error:
            return Color(.systemRed)
        }
    }
}

enum ConnectionStatus {
    case connected
    case disconnected
    case error
    
    var displayName: String {
        switch self {
        case .connected:
            return "Connected"
        case .disconnected:
            return "Disconnected"
        case .error:
            return "Error"
        }
    }
    
    var color: Color {
        switch self {
        case .connected:
            return Color(.systemGreen)
        case .disconnected:
            return Color(.systemRed)
        case .error:
            return Color(.systemOrange)
        }
    }
}

#Preview {
    SyncSettingsView()
}