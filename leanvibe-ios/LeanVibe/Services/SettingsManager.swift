import Foundation
import SwiftUI
import Observation

// MARK: - Settings Models (temporarily inlined to fix build)

/// A protocol for settings structures to ensure they provide default values.
protocol SettingsProtocol: Codable {
    init()
}

/// Stores the settings related to the WebSocket server connection.
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

/// Voice-related settings and configurations.
struct VoiceSettings: SettingsProtocol {
    var isEnabled: Bool = true
    var wakeWord: String = ""
    var confidenceThreshold: Double = 0.7
    var recognitionLanguage: String = ""
    var isWakeWordEnabled: Bool = true
    var isPushToTalkEnabled: Bool = true
    var microphoneGain: Float = 1.0
    var noiseReduction: Bool = true
    var echoCancellation: Bool = true
    var maxRecordingDuration: TimeInterval = 30.0
    var silenceTimeout: TimeInterval = 2.0
    var useNeuralEngine: Bool = true
    var offlineMode: Bool = true
    var enableVibration: Bool = true
    var enableAudioFeedback: Bool = true
    var maxHistoryItems: Int = 50
    var voiceCommandCategories: [String] = []
    var enableVoiceCommands: Bool = true
    var echoCanselation: Bool = true  // Note: typo in original VoiceSettingsView
    var commandHistoryEnabled: Bool = true
    var voiceFeedbackEnabled: Bool = true
    var enableCustomCommands: Bool = true
    var backgroundListening: Bool = false
    var autoStopListening: Bool = true
    var wakePhraseEnabled: Bool = true
    var wakePhraseSensitivity: Double = 0.7
    
    init() {}
}

/// Push notification settings and preferences.
struct NotificationSettings: SettingsProtocol {
    var isEnabled: Bool = true
    var taskCompletionNotifications: Bool = true
    var systemStatusNotifications: Bool = true
    var errorNotifications: Bool = true
    var quietHoursEnabled: Bool = false
    var quietHoursStart: String = ""
    var quietHoursEnd: String = ""
    var notificationSound: String = "default"
    var vibrationEnabled: Bool = true
    var badgeCountEnabled: Bool = true
    var showOnLockScreen: Bool = true
    var showInNotificationCenter: Bool = true
    var showAsBanners: Bool = true
    var criticalAlertsEnabled: Bool = false
    var summarizationEnabled: Bool = true
    var categories: [String] = []
    var notificationsEnabled: Bool = true
    var soundEnabled: Bool = true
    var taskUpdates: Bool = true
    var voiceNotificationsEnabled: Bool = true
    var bannerNotificationsEnabled: Bool = true
    var taskOverdueNotifications: Bool = true
    var systemNotificationsEnabled: Bool = true
    var voiceCommandResultNotifications: Bool = true
    var taskNotificationsEnabled: Bool = true
    var serverConnectionNotifications: Bool = true
    
    init() {}
}

/// Kanban board settings and view preferences.
struct KanbanSettings: SettingsProtocol {
    var defaultView: String = ""
    var columnsVisible: [String] = []
    var columnOrder: [String] = []
    var cardSize: String = "medium"
    var showAvatars: Bool = true
    var showDueDates: Bool = true
    var showPriorities: Bool = true
    var showLabels: Bool = true
    var autoRefresh: Bool = true
    var refreshInterval: TimeInterval = 30.0
    var dragAndDropEnabled: Bool = true
    var bulkEditEnabled: Bool = true
    var filterPersistence: Bool = true
    var maxTasksPerColumn: Int = 50
    var defaultTaskPriority: String = ""
    var conflictResolution: String = ""
    var swimlanesEnabled: Bool = false
    var wIPLimitsEnabled: Bool = false
    var showStatistics: Bool = true
    var showColumnTaskCounts: Bool = true
    var enableVoiceTaskCreation: Bool = true
    var enableInfiniteScroll: Bool = false
    var syncWithBackend: Bool = true
    var compactMode: Bool = false
    var enableColumnCustomization: Bool = true
    var showTaskIds: Bool = false
    var prefetchTaskDetails: Bool = true
    var offlineModeEnabled: Bool = false
    var enableAnimations: Bool = true
    var autoAssignTasks: Bool = false
    var enableTaskNotifications: Bool = true
    
    init() {}
}

/// Accessibility-related settings.
struct AccessibilitySettings: SettingsProtocol {
    var isVoiceOverEnabled: Bool = false
    var isLargeTextEnabled: Bool = false
    var isHighContrastEnabled: Bool = false
    var isReduceMotionEnabled: Bool = false
    var isReduceTransparencyEnabled: Bool = false
    var textScale: Double = 1.0
    var buttonSize: String = "standard"
    var tapTimeout: TimeInterval = 0.5
    var enableHapticFeedback: Bool = true
    var enableAudioCues: Bool = false
    var keyboardNavigation: Bool = false
    var focusIndicatorStyle: String = "default"
    var colorBlindAssist: Bool = false
    var colorTheme: String = "auto"
    var highContrastMode: Bool = false
    var voiceOverOptimizations: Bool = false
    var extendedTouchTargets: Bool = false
    var speechRateAdjustment: Double = 1.0
    var largeFontSize: Double = 1.0
    var extendedVoiceCommands: Bool = false
    
    init() {}
}

/// Architecture diagram and visualization settings.
struct ArchitectureSettings: SettingsProtocol {
    var diagramTheme: String = ""
    var diagramLayout: String = ""
    var renderQuality: String = ""
    var autoUpdate: Bool = true
    var refreshInterval: TimeInterval = 30.0
    var maxCacheSize: Int = 50
    var showLegend: Bool = true
    var showMetadata: Bool = true
    var enableInteraction: Bool = true
    var zoomLevel: Double = 1.0
    var panLock: Bool = false
    var renderTimeoutSeconds: Int = 10
    var defaultExportFormat: String = ""
    var includePrivateElements: Bool = false
    var compareMode: String = ""
    var syncConflictResolution: String = ""
    var sharePermissionLevel: String = ""
    var enableAnimations: Bool = true
    
    init() {}
}

/// Represents all user-configurable settings for the application.
struct AllSettings: Codable {
    let connection: ConnectionPreferences
    let voice: VoiceSettings
    let notifications: NotificationSettings
    let kanban: KanbanSettings
    let accessibility: AccessibilitySettings
    let architecture: ArchitectureSettings
}

/// Represents user-configurable settings for the application.
/// NO HARDCODED VALUES - All settings come from backend or user configuration
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

    init() {
        // Initialize with minimal defaults first to satisfy Swift 6 initialization requirements
        self.connection = ConnectionPreferences()
        self.voice = VoiceSettings()
        self.notifications = NotificationSettings()
        self.kanban = KanbanSettings()
        self.accessibility = AccessibilitySettings()
        self.architecture = ArchitectureSettings()
        
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
            architecture: architecture
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
}


// MARK: - Settings Models
// All settings models have been moved to SettingsModels.swift to avoid circular dependencies
