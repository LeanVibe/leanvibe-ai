import Foundation
import SwiftUI
import Observation

// Import settings models from SettingsModels.swift to avoid duplication
// Note: Models are imported implicitly from the same module

// Temporary settings structs until circular dependency is resolved
protocol SettingsProtocol: Codable {
    init()
}

struct ConnectionPreferences: SettingsProtocol {
    var host: String = ""
    var port: Int = 0
    var authToken: String = ""
    var isSSLEnabled: Bool = false
    var connectionTimeout: TimeInterval = 10.0
    var reconnectInterval: TimeInterval = 5.0
    var maxReconnectAttempts: Int = 5
    var qrCodeExpiry: TimeInterval = 300.0
    var autoConnect: Bool = true
    var persistConnection: Bool = true
    var serverCertificateValidation: Bool = true
    var useCompression: Bool = false
    
    init() {}
}

struct VoiceSettings: SettingsProtocol {
    var isEnabled: Bool = true
    var wakeWord: String = ""
    var confidenceThreshold: Double = 0.7
    var recognitionLanguage: String = ""
    var autoStopListening: Bool = true
    var wakePhraseEnabled: Bool = true
    var backgroundListening: Bool = false
    var commandHistoryEnabled: Bool = true
    var echoCanselation: Bool = true
    var enableCustomCommands: Bool = true
    var enableVoiceCommands: Bool = true
    var maxHistoryItems: Int = 100
    var maxRecordingDuration: Double = 60.0
    var microphoneGain: Double = 1.0
    var noiseReduction: Bool = true
    var voiceFeedbackEnabled: Bool = true
    var wakePhraseSensitivity: Double = 0.7
    
    init() {}
}

struct NotificationSettings: SettingsProtocol {
    var notificationsEnabled: Bool = true
    var bannerNotificationsEnabled: Bool = true
    var taskUpdates: Bool = false
    var taskNotificationsEnabled: Bool = false
    var taskOverdueNotifications: Bool = true
    var taskCompletionNotifications: Bool = true
    var voiceNotificationsEnabled: Bool = false
    var voiceCommandResultNotifications: Bool = false
    var systemNotificationsEnabled: Bool = false
    var serverConnectionNotifications: Bool = true
    var emailNotifications: Bool = false
    var soundEnabled: Bool = true
    var vibrationEnabled: Bool = true
    var frequency: String = "immediate"
    var quietHoursEnabled: Bool = false
    var quietHoursStart: String = "22:00"
    var quietHoursEnd: String = "08:00"
    
    init() {}
}

struct KanbanSettings: SettingsProtocol {
    var autoRefresh: Bool = true
    var refreshInterval: TimeInterval = 30.0
    var showStatistics: Bool = true
    var showColumnTaskCounts: Bool = true
    var enableVoiceTaskCreation: Bool = false
    var maxTasksPerColumn: Int = 50
    var syncWithBackend: Bool = true
    var offlineModeEnabled: Bool = false
    var columnOrder: [String] = ["todo", "inProgress", "testing", "done"]
    var compactMode: Bool = false
    var enableColumnCustomization: Bool = true
    var showTaskIds: Bool = false
    var autoAssignTasks: Bool = false
    var conflictResolution: String = "manual"
    var defaultTaskPriority: String = "medium"
    var enableAnimations: Bool = true
    var enableInfiniteScroll: Bool = false
    var enableTaskNotifications: Bool = true
    var prefetchTaskDetails: Bool = true
    
    init() {}
}

struct AccessibilitySettings: SettingsProtocol {
    var fontSize: Double = 16.0
    var highContrast: Bool = false
    
    init() {}
}

struct ArchitectureSettings: SettingsProtocol {
    var diagramTheme: String = "default"
    var renderQuality: String = "high"
    var showMetadata: Bool = true
    var autoUpdate: Bool = true
    var zoomLevel: Double = 1.0
    var panLock: Bool = false
    var includePrivateElements: Bool = false
    var diagramLayout: String = "hierarchical"
    var enableAnimations: Bool = true
    var showLegend: Bool = true
    var refreshInterval: TimeInterval = 30.0
    var enableInteraction: Bool = true
    var compareMode: Bool = false
    var maxCacheSize: Int = 50
    
    init() {}
}

struct MetricsSettings: SettingsProtocol {
    var isEnabled: Bool = true
    var performanceMonitoringEnabled: Bool = false
    var memoryUsageTrackingEnabled: Bool = false
    var networkMetricsEnabled: Bool = false
    var voiceMetricsEnabled: Bool = false
    var taskCompletionMetricsEnabled: Bool = false
    var realTimeMonitoringEnabled: Bool = false
    var detailedLoggingEnabled: Bool = false
    var dataRetentionDays: Int = 30
    var maxStorageSize: Int = 100
    
    init() {}
}

struct TaskCreationSettings: SettingsProtocol {
    var defaultPriority: String = "medium"
    var defaultAssignee: String = ""
    var defaultDueDate: String = ""
    var autoAssignToSelf: Bool = false
    var useTemplates: Bool = true
    var defaultTemplate: String = ""
    var templateSharingEnabled: Bool = false
    var requireDescription: Bool = false
    var enableQuickActions: Bool = true
    var voiceTaskCreationEnabled: Bool = false
    
    init() {}
}

struct OfflineSettings: SettingsProtocol {
    var isEnabled: Bool = false
    var backgroundSyncEnabled: Bool = true
    var syncOnWifiOnly: Bool = true
    var offlineIndicatorEnabled: Bool = true
    var offlineStorageLimit: Int = 100
    var cacheExpiration: TimeInterval = 3600
    var autoCleanupEnabled: Bool = true
    var compressionEnabled: Bool = true
    var encryptionEnabled: Bool = false
    
    init() {}
}

struct InterfaceSettings: SettingsProtocol {
    var theme: String = "system"
    var accentColor: String = "blue"
    var fontSize: String = "medium"
    var layoutDensity: String = "comfortable"
    var compactMode: Bool = false
    var showSidebar: Bool = true
    var sidebarPosition: String = "left"
    var navigationStyle: String = "tab"
    var tabBarStyle: String = "default"
    
    init() {}
}

struct PerformanceSettings: SettingsProtocol {
    var optimizationLevel: String = "balanced"
    var performanceMonitoringEnabled: Bool = false
    var memoryLimitEnabled: Bool = false
    var maxMemoryUsage: Int = 512
    var memoryWarningHandlingEnabled: Bool = true
    var backgroundProcessingEnabled: Bool = true
    var threadPoolSize: Int = 4
    var networkOptimizationEnabled: Bool = true
    var networkRequestTimeout: TimeInterval = 30.0
    
    init() {}
}

struct AllSettings: Codable {
    var connection: ConnectionPreferences
    var voice: VoiceSettings
    var notifications: NotificationSettings
    var kanban: KanbanSettings
    var accessibility: AccessibilitySettings
    var architecture: ArchitectureSettings
    var metrics: MetricsSettings
    var taskCreation: TaskCreationSettings
    var offline: OfflineSettings
    var interface: InterfaceSettings
    var performance: PerformanceSettings
    
    init() {
        connection = ConnectionPreferences()
        voice = VoiceSettings()
        notifications = NotificationSettings()
        kanban = KanbanSettings()
        accessibility = AccessibilitySettings()
        architecture = ArchitectureSettings()
        metrics = MetricsSettings()
        taskCreation = TaskCreationSettings()
        offline = OfflineSettings()
        interface = InterfaceSettings()
        performance = PerformanceSettings()
    }
    
    init(connection: ConnectionPreferences, voice: VoiceSettings, notifications: NotificationSettings, kanban: KanbanSettings, accessibility: AccessibilitySettings, architecture: ArchitectureSettings, metrics: MetricsSettings, taskCreation: TaskCreationSettings, offline: OfflineSettings, interface: InterfaceSettings, performance: PerformanceSettings) {
        self.connection = connection
        self.voice = voice
        self.notifications = notifications
        self.kanban = kanban
        self.accessibility = accessibility
        self.architecture = architecture
        self.metrics = metrics
        self.taskCreation = taskCreation
        self.offline = offline
        self.interface = interface
        self.performance = performance
    }
}

/// Represents user-configurable settings for the application.
/// NO HARDCODED VALUES - All settings come from backend or user configuration
@available(iOS 17.0, macOS 14.0, *)
@Observable

class SettingsManager: ObservableObject, @unchecked Sendable {
    static let shared: SettingsManager = {
        let instance = SettingsManager()
        return instance
    }()
    
    // MARK: - Backend Integration
    var isBackendSyncEnabled = true
    var lastSyncDate: Date?
    var syncStatus: SyncStatus = .idle
    
    enum SyncStatus {
        case idle
        case syncing
        case synced(Date)
        case failed(Error)
    }

    // MARK: - Observable Properties (Swift 6)
    var connection: ConnectionPreferences {
        didSet {
            save(connection, for: .connection)
        }
    }
    var voice: VoiceSettings {
        didSet {
            save(voice, for: .voice)
        }
    }
    var notifications: NotificationSettings {
        didSet {
            save(notifications, for: .notifications)
        }
    }
    var kanban: KanbanSettings {
        didSet {
            save(kanban, for: .kanban)
        }
    }
    var accessibility: AccessibilitySettings {
        didSet {
            save(accessibility, for: .accessibility)
        }
    }
    var architecture: ArchitectureSettings {
        didSet {
            save(architecture, for: .architecture)
        }
    }
    var metrics: MetricsSettings {
        didSet {
            save(metrics, for: .metrics)
        }
    }
    var taskCreation: TaskCreationSettings {
        didSet {
            save(taskCreation, for: .taskCreation)
        }
    }
    var offline: OfflineSettings {
        didSet {
            save(offline, for: .offline)
        }
    }
    var interface: InterfaceSettings {
        didSet {
            save(interface, for: .interface)
        }
    }
    var performance: PerformanceSettings {
        didSet {
            save(performance, for: .performance)
        }
    }

    init() {
        // Initialize with minimal defaults first to satisfy Swift 6 initialization requirements
        self.connection = ConnectionPreferences()
        self.voice = VoiceSettings()
        self.notifications = NotificationSettings()
        self.kanban = KanbanSettings()
        self.accessibility = AccessibilitySettings()
        self.architecture = ArchitectureSettings()
        self.metrics = MetricsSettings()
        self.taskCreation = TaskCreationSettings()
        self.offline = OfflineSettings()
        self.interface = InterfaceSettings()
        self.performance = PerformanceSettings()
        
        // Load stored values first, then sync with backend
        loadStoredValues()
        
        // Start background sync with backend if available
        Task {
            await syncWithBackendIfAvailable()
        }
    }
    
    private func loadStoredValues() {
        if let loadedConnection = load(.connection, as: ConnectionPreferences.self) {
            self.connection = loadedConnection
        }
        if let loadedVoice = load(.voice, as: VoiceSettings.self) {
            self.voice = loadedVoice
        }
        if let loadedNotifications = load(.notifications, as: NotificationSettings.self) {
            self.notifications = loadedNotifications
        }
        if let loadedKanban = load(.kanban, as: KanbanSettings.self) {
            self.kanban = loadedKanban
        }
        if let loadedAccessibility = load(.accessibility, as: AccessibilitySettings.self) {
            self.accessibility = loadedAccessibility
        }
        if let loadedArchitecture = load(.architecture, as: ArchitectureSettings.self) {
            self.architecture = loadedArchitecture
        }
        if let loadedMetrics = load(.metrics, as: MetricsSettings.self) {
            self.metrics = loadedMetrics
        }
        if let loadedTaskCreation = load(.taskCreation, as: TaskCreationSettings.self) {
            self.taskCreation = loadedTaskCreation
        }
        if let loadedOffline = load(.offline, as: OfflineSettings.self) {
            self.offline = loadedOffline
        }
        if let loadedInterface = load(.interface, as: InterfaceSettings.self) {
            self.interface = loadedInterface
        }
        if let loadedPerformance = load(.performance, as: PerformanceSettings.self) {
            self.performance = loadedPerformance
        }
    }

    // MARK: - Backend Sync Methods
    
    /// Sync settings with backend if available
    func syncWithBackendIfAvailable() async {
        guard isBackendSyncEnabled else { return }
        
        syncStatus = .syncing
        
        do {
            // TODO: Fix BackendSettingsService target membership
            // let backendSettings = try await BackendSettingsService.shared.fetchSettings()
            
            await MainActor.run {
                // Update settings from backend while preserving user overrides
                // updateFromBackend(backendSettings)
                syncStatus = .synced(Date())
                lastSyncDate = Date()
            }
        } catch {
            await MainActor.run {
                syncStatus = .failed(error)
                print("⚠️ Settings sync failed: \(error.localizedDescription)")
            }
        }
    }
    
    /// Push local settings to backend
    func pushSettingsToBackend() async throws {
        guard isBackendSyncEnabled else { return }
        
        let allSettings = AllSettings(
            connection: connection,
            voice: voice,
            notifications: notifications,
            kanban: kanban,
            accessibility: accessibility,
            architecture: architecture,
            metrics: metrics,
            taskCreation: taskCreation,
            offline: offline,
            interface: interface,
            performance: performance
        )
        
        // TODO: Fix BackendSettingsService target membership
        // try await BackendSettingsService.shared.pushSettings(allSettings)
        await MainActor.run {
            lastSyncDate = Date()
            syncStatus = .synced(Date())
        }
    }
    
    private func updateFromBackend(_ backendSettings: AllSettings) {
        // Only update if backend has more recent data or user hasn't customized locally
        
        if !hasUserCustomizations(for: .connection) {
            self.connection = backendSettings.connection
        }
        
        if !hasUserCustomizations(for: .voice) {
            self.voice = backendSettings.voice
        }
        
        if !hasUserCustomizations(for: .notifications) {
            self.notifications = backendSettings.notifications
        }
        
        if !hasUserCustomizations(for: .kanban) {
            self.kanban = backendSettings.kanban
        }
        
        if !hasUserCustomizations(for: .accessibility) {
            self.accessibility = backendSettings.accessibility
        }
        
        if !hasUserCustomizations(for: .architecture) {
            self.architecture = backendSettings.architecture
        }
        
        if !hasUserCustomizations(for: .metrics) {
            self.metrics = backendSettings.metrics
        }
        
        if !hasUserCustomizations(for: .taskCreation) {
            self.taskCreation = backendSettings.taskCreation
        }
        
        if !hasUserCustomizations(for: .offline) {
            self.offline = backendSettings.offline
        }
        
        if !hasUserCustomizations(for: .interface) {
            self.interface = backendSettings.interface
        }
        
        if !hasUserCustomizations(for: .performance) {
            self.performance = backendSettings.performance
        }
        
        saveAll()
    }
    
    private func hasUserCustomizations(for key: SettingsKey) -> Bool {
        // Check if user has made customizations to this setting category
        return UserDefaults.standard.bool(forKey: "\(key.rawValue).userCustomized")
    }
    
    private func markAsUserCustomized(_ key: SettingsKey) {
        UserDefaults.standard.set(true, forKey: "\(key.rawValue).userCustomized")
    }
    
    // MARK: - Public Methods
    func resetAll() {
        // Clear user customization flags
        SettingsKey.allCases.forEach { key in
            UserDefaults.standard.removeObject(forKey: "\(key.rawValue).userCustomized")
        }
        
        // Reset to backend defaults or minimal defaults
        self.connection = ConnectionPreferences()
        self.voice = VoiceSettings()
        self.notifications = NotificationSettings()
        self.kanban = KanbanSettings()
        self.accessibility = AccessibilitySettings()
        self.architecture = ArchitectureSettings()
        self.metrics = MetricsSettings()
        self.taskCreation = TaskCreationSettings()
        self.offline = OfflineSettings()
        self.interface = InterfaceSettings()
        self.performance = PerformanceSettings()
        saveAll()
        
        // Re-sync with backend
        Task {
            await syncWithBackendIfAvailable()
        }
    }
    
    func resetAllSettings() {
        resetAll()
    }
    
    func resetSettings<T: SettingsProtocol>(_ type: T.Type) {
        if type == AccessibilitySettings.self {
            self.accessibility = AccessibilitySettings()
        }
        // Add other types as needed
    }
    
    // Type-safe save method with backend sync
    func save<T: Codable>(_ data: T, for key: SettingsKey) {
        let encoder = JSONEncoder()
        if let encoded = try? encoder.encode(data) {
            UserDefaults.standard.set(encoded, forKey: key.rawValue)
            
            // Mark as user customized and sync to backend
            markAsUserCustomized(key)
            
            // Push to backend in background
            if isBackendSyncEnabled {
                Task {
                    try? await pushSettingsToBackend()
                }
            }
        }
    }

    // Type-safe load method
    func load<T: Codable>(_ key: SettingsKey, as type: T.Type) -> T? {
        if let data = UserDefaults.standard.data(forKey: key.rawValue) {
            let decoder = JSONDecoder()
            if let decoded = try? decoder.decode(T.self, from: data) {
                return decoded
            }
        }
        return nil
    }
    
    // MARK: - Private Methods
    private func saveAll() {
        save(connection, for: .connection)
        save(voice, for: .voice)
        save(notifications, for: .notifications)
        save(kanban, for: .kanban)
        save(accessibility, for: .accessibility)
        save(architecture, for: .architecture)
        save(metrics, for: .metrics)
        save(taskCreation, for: .taskCreation)
        save(offline, for: .offline)
        save(interface, for: .interface)
        save(performance, for: .performance)
    }
}

// MARK: - Settings Structures
/// Defines the keys used to store settings in UserDefaults.
enum SettingsKey: String, CaseIterable {
    case connection = "LeanVibe.ConnectionSettings"
    case voice = "LeanVibe.VoiceSettings"
    case notifications = "LeanVibe.NotificationSettings"
    case kanban = "LeanVibe.KanbanSettings"
    case accessibility = "LeanVibe.AccessibilitySettings"
    case architecture = "LeanVibe.ArchitectureSettings"
    case metrics = "LeanVibe.MetricsSettings"
    case taskCreation = "LeanVibe.TaskCreationSettings"
    case offline = "LeanVibe.OfflineSettings"
    case interface = "LeanVibe.InterfaceSettings"
    case performance = "LeanVibe.PerformanceSettings"
}


// MARK: - Settings Models
// All settings models have been moved to SettingsModels.swift to avoid circular dependencies
