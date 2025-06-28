import SwiftUI
import Combine

/// Centralized settings management for all LeenVibe features
/// Coordinates settings for Voice, Kanban, Architecture, and other systems
class SettingsManager: ObservableObject {
    static let shared = SettingsManager()
    
    // MARK: - Published Settings
    
    @Published var appSettings = AppSettings()
    @Published var voiceSettings = VoiceSettings()
    @Published var kanbanSettings = KanbanSettings()
    @Published var notificationSettings = NotificationSettings()
    @Published var connectionSettings = ConnectionSettings()
    @Published var accessibilitySettings = AccessibilitySettings()
    
    // MARK: - Private Properties
    
    private var cancellables = Set<AnyCancellable>()
    private let userDefaults = UserDefaults.standard
    
    // MARK: - Initialization
    
    private init() {
        loadAllSettings()
        setupAutoSave()
    }
    
    // MARK: - Public Methods
    
    /// Load all settings from persistent storage
    func loadAllSettings() {
        appSettings = AppSettings.load()
        voiceSettings = VoiceSettings.load()
        kanbanSettings = KanbanSettings.load()
        notificationSettings = NotificationSettings.load()
        connectionSettings = ConnectionSettings.load()
        accessibilitySettings = AccessibilitySettings.load()
    }
    
    /// Save all settings to persistent storage
    func saveAllSettings() {
        appSettings.save()
        voiceSettings.save()
        kanbanSettings.save()
        notificationSettings.save()
        connectionSettings.save()
        accessibilitySettings.save()
    }
    
    /// Reset all settings to defaults
    func resetAllSettings() {
        appSettings = AppSettings()
        voiceSettings = VoiceSettings()
        kanbanSettings = KanbanSettings()
        notificationSettings = NotificationSettings()
        connectionSettings = ConnectionSettings()
        accessibilitySettings = AccessibilitySettings()
        saveAllSettings()
    }
    
    /// Reset specific settings category
    func resetSettings<T: SettingsProtocol>(_ settingsType: T.Type) {
        switch settingsType {
        case is AppSettings.Type:
            appSettings = AppSettings()
            appSettings.save()
        case is VoiceSettings.Type:
            voiceSettings = VoiceSettings()
            voiceSettings.save()
        case is KanbanSettings.Type:
            kanbanSettings = KanbanSettings()
            kanbanSettings.save()
        case is NotificationSettings.Type:
            notificationSettings = NotificationSettings()
            notificationSettings.save()
        case is ConnectionSettings.Type:
            connectionSettings = ConnectionSettings()
            connectionSettings.save()
        case is AccessibilitySettings.Type:
            accessibilitySettings = AccessibilitySettings()
            accessibilitySettings.save()
        default:
            break
        }
    }
    
    /// Export settings as JSON for backup
    func exportSettings() -> Data? {
        let exportData = SettingsExport(
            app: appSettings,
            voice: voiceSettings,
            kanban: kanbanSettings,
            notifications: notificationSettings,
            connection: connectionSettings,
            accessibility: accessibilitySettings,
            exportDate: Date()
        )
        
        return try? JSONEncoder().encode(exportData)
    }
    
    /// Import settings from JSON backup
    func importSettings(from data: Data) throws {
        let importData = try JSONDecoder().decode(SettingsExport.self, from: data)
        
        appSettings = importData.app
        voiceSettings = importData.voice
        kanbanSettings = importData.kanban
        notificationSettings = importData.notifications
        connectionSettings = importData.connection
        accessibilitySettings = importData.accessibility
        
        saveAllSettings()
    }
    
    // MARK: - Private Methods
    
    private func setupAutoSave() {
        // Auto-save when any settings change
        Publishers.CombineLatest6(
            $appSettings,
            $voiceSettings,
            $kanbanSettings,
            $notificationSettings,
            $connectionSettings,
            $accessibilitySettings
        )
        .debounce(for: .seconds(1), scheduler: RunLoop.main)
        .sink { [weak self] _ in
            self?.saveAllSettings()
        }
        .store(in: &cancellables)
    }
}

// MARK: - Settings Protocol

protocol SettingsProtocol: Codable {
    static func load() -> Self
    func save()
    static var storageKey: String { get }
}

// MARK: - App Settings

struct AppSettings: SettingsProtocol {
    static let storageKey = "AppSettings"
    
    // Interface preferences
    var interfaceTheme: InterfaceTheme = .system
    var showAdvancedFeatures = false
    var enableHapticFeedback = true
    var animationsEnabled = true
    
    // Developer options
    var developerModeEnabled = false
    var showDebugInfo = false
    var enableLogging = false
    
    // Performance settings
    var enablePerformanceMonitoring = false
    var maxConcurrentOperations = 10
    
    static func load() -> AppSettings {
        guard let data = UserDefaults.standard.data(forKey: storageKey),
              let settings = try? JSONDecoder().decode(AppSettings.self, from: data) else {
            return AppSettings()
        }
        return settings
    }
    
    func save() {
        if let data = try? JSONEncoder().encode(self) {
            UserDefaults.standard.set(data, forKey: Self.storageKey)
        }
    }
}

enum InterfaceTheme: String, CaseIterable, Codable {
    case light = "light"
    case dark = "dark"
    case system = "system"
    
    var displayName: String {
        switch self {
        case .light: return "Light"
        case .dark: return "Dark"
        case .system: return "System"
        }
    }
}

// MARK: - Voice Settings

struct VoiceSettings: SettingsProtocol {
    static let storageKey = "VoiceSettings"
    
    // Wake phrase configuration
    var wakePhraseEnabled = true
    var wakePhrasePhrase = "Hey LeenVibe"
    var wakePhraseSensitivity: Double = 0.7
    var wakePhraseTimeout: TimeInterval = 5.0
    
    // Speech recognition
    var voiceFeedbackEnabled = true
    var backgroundListening = false
    var recognitionLanguage = "en-US"
    var confidenceThreshold: Double = 0.7
    var autoStopListening = true
    var maxRecordingDuration: TimeInterval = 30.0
    
    // Voice commands
    var enableVoiceCommands = true
    var commandHistoryEnabled = true
    var maxHistoryItems = 50
    var enableCustomCommands = false
    
    // Audio settings
    var microphoneGain: Double = 1.0
    var noiseReduction = true
    var echoCanselation = true
    
    static func load() -> VoiceSettings {
        guard let data = UserDefaults.standard.data(forKey: storageKey),
              let settings = try? JSONDecoder().decode(VoiceSettings.self, from: data) else {
            return VoiceSettings()
        }
        return settings
    }
    
    func save() {
        if let data = try? JSONEncoder().encode(self) {
            UserDefaults.standard.set(data, forKey: Self.storageKey)
        }
    }
}

// MARK: - Kanban Settings

struct KanbanSettings: SettingsProtocol {
    static let storageKey = "KanbanSettings"
    
    // Board behavior
    var autoRefresh = true
    var refreshInterval: TimeInterval = 30.0
    var showStatistics = true
    var compactMode = false
    var enableAnimations = true
    
    // Columns configuration
    var columnOrder = ["backlog", "in_progress", "testing", "done"]
    var showColumnTaskCounts = true
    var enableColumnCustomization = true
    
    // Task management
    var enableVoiceTaskCreation = true
    var showTaskIds = false
    var defaultTaskPriority = "medium"
    var autoAssignTasks = false
    var enableTaskNotifications = true
    
    // Performance
    var maxTasksPerColumn = 100
    var enableInfiniteScroll = true
    var prefetchTaskDetails = true
    
    // Integration
    var syncWithBackend = true
    var offlineModeEnabled = true
    var conflictResolution: ConflictResolution = .askUser
    
    static func load() -> KanbanSettings {
        guard let data = UserDefaults.standard.data(forKey: storageKey),
              let settings = try? JSONDecoder().decode(KanbanSettings.self, from: data) else {
            return KanbanSettings()
        }
        return settings
    }
    
    func save() {
        if let data = try? JSONEncoder().encode(self) {
            UserDefaults.standard.set(data, forKey: Self.storageKey)
        }
    }
}

enum ConflictResolution: String, CaseIterable, Codable {
    case askUser = "ask_user"
    case useLocal = "use_local"
    case useRemote = "use_remote"
    case mergeChanges = "merge_changes"
    
    var displayName: String {
        switch self {
        case .askUser: return "Ask User"
        case .useLocal: return "Use Local Changes"
        case .useRemote: return "Use Remote Changes"
        case .mergeChanges: return "Merge Changes"
        }
    }
}

// MARK: - Notification Settings

struct NotificationSettings: SettingsProtocol {
    static let storageKey = "NotificationSettings"
    
    // Push notifications
    var pushNotificationsEnabled = false
    var taskNotificationsEnabled = true
    var voiceNotificationsEnabled = true
    var systemNotificationsEnabled = true
    
    // In-app notifications
    var bannerNotificationsEnabled = true
    var soundEffectsEnabled = true
    var hapticFeedbackEnabled = true
    var notificationBadgeEnabled = true
    
    // Notification types
    var taskCreatedNotifications = true
    var taskCompletedNotifications = true
    var taskOverdueNotifications = true
    var voiceCommandResultNotifications = true
    var serverConnectionNotifications = true
    
    // Quiet hours
    var quietHoursEnabled = false
    var quietHoursStart = Calendar.current.date(from: DateComponents(hour: 22)) ?? Date()
    var quietHoursEnd = Calendar.current.date(from: DateComponents(hour: 8)) ?? Date()
    
    static func load() -> NotificationSettings {
        guard let data = UserDefaults.standard.data(forKey: storageKey),
              let settings = try? JSONDecoder().decode(NotificationSettings.self, from: data) else {
            return NotificationSettings()
        }
        return settings
    }
    
    func save() {
        if let data = try? JSONEncoder().encode(self) {
            UserDefaults.standard.set(data, forKey: Self.storageKey)
        }
    }
}

// MARK: - Connection Settings

struct ConnectionSettings: SettingsProtocol {
    static let storageKey = "ConnectionSettings"
    
    // Server configuration
    var serverURL = ""
    var serverPort = 8000
    var useHTTPS = false
    var apiVersion = "v1"
    
    // Connection behavior
    var autoReconnect = true
    var connectionTimeout: TimeInterval = 30.0
    var retryAttempts = 3
    var retryDelay: TimeInterval = 5.0
    
    // WebSocket settings
    var webSocketEnabled = true
    var webSocketHeartbeat: TimeInterval = 30.0
    var webSocketReconnectDelay: TimeInterval = 5.0
    
    // Sync preferences
    var syncInterval: TimeInterval = 60.0
    var backgroundSyncEnabled = true
    var wifiOnlySync = false
    
    static func load() -> ConnectionSettings {
        guard let data = UserDefaults.standard.data(forKey: storageKey),
              let settings = try? JSONDecoder().decode(ConnectionSettings.self, from: data) else {
            return ConnectionSettings()
        }
        return settings
    }
    
    func save() {
        if let data = try? JSONEncoder().encode(self) {
            UserDefaults.standard.set(data, forKey: Self.storageKey)
        }
    }
}

// MARK: - Accessibility Settings

struct AccessibilitySettings: SettingsProtocol {
    static let storageKey = "AccessibilitySettings"
    
    // Visual accessibility
    var highContrastMode = false
    var reduceMotion = false
    var largeFontSize = false
    var boldText = false
    
    // Voice accessibility
    var voiceOverOptimizations = true
    var speechRateAdjustment: Double = 1.0
    var extendedVoiceCommands = false
    
    // Motor accessibility
    var extendedTouchTargets = false
    var reduceGestures = false
    var oneHandedMode = false
    
    static func load() -> AccessibilitySettings {
        guard let data = UserDefaults.standard.data(forKey: storageKey),
              let settings = try? JSONDecoder().decode(AccessibilitySettings.self, from: data) else {
            return AccessibilitySettings()
        }
        return settings
    }
    
    func save() {
        if let data = try? JSONEncoder().encode(self) {
            UserDefaults.standard.set(data, forKey: Self.storageKey)
        }
    }
}

// MARK: - Settings Export/Import

struct SettingsExport: Codable {
    let app: AppSettings
    let voice: VoiceSettings
    let kanban: KanbanSettings
    let notifications: NotificationSettings
    let connection: ConnectionSettings
    let accessibility: AccessibilitySettings
    let exportDate: Date
    let version: String = "1.0"
}

// MARK: - Settings Notifications

extension SettingsManager {
    
    /// Post notification when settings change
    func notifySettingsChanged(category: SettingsCategory) {
        NotificationCenter.default.post(
            name: .settingsDidChange,
            object: self,
            userInfo: ["category": category]
        )
    }
}

enum SettingsCategory: String, CaseIterable {
    case app = "app"
    case voice = "voice"
    case kanban = "kanban"
    case notifications = "notifications"
    case connection = "connection"
    case accessibility = "accessibility"
}

extension Notification.Name {
    static let settingsDidChange = Notification.Name("settingsDidChange")
}