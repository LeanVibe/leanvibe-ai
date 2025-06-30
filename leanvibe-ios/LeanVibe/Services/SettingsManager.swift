import Foundation
import SwiftUI
import Observation

/// Represents user-configurable settings for the application.
@Observable
class SettingsManager: ObservableObject, @unchecked Sendable {
    static let shared: SettingsManager = {
        let instance = SettingsManager()
        return instance
    }()

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

    init() {
        self.connection = load(.connection, as: ConnectionPreferences.self) ?? ConnectionPreferences()
        self.voice = load(.voice, as: VoiceSettings.self) ?? VoiceSettings()
        self.notifications = load(.notifications, as: NotificationSettings.self) ?? NotificationSettings()
        self.kanban = load(.kanban, as: KanbanSettings.self) ?? KanbanSettings()
        self.accessibility = load(.accessibility, as: AccessibilitySettings.self) ?? AccessibilitySettings()
    }

    // MARK: - Public Methods
    func resetAll() {
        self.connection = ConnectionPreferences()
        self.voice = VoiceSettings()
        self.notifications = NotificationSettings()
        self.kanban = KanbanSettings()
        self.accessibility = AccessibilitySettings()
        saveAll()
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
    
    // Type-safe save method
    func save<T: Codable>(_ data: T, for key: SettingsKey) {
        let encoder = JSONEncoder()
        if let encoded = try? encoder.encode(data) {
            UserDefaults.standard.set(encoded, forKey: key.rawValue)
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
    }
}

// MARK: - Settings Structures
/// Defines the keys used to store settings in UserDefaults.
enum SettingsKey: String {
    case connection = "LeanVibe.ConnectionSettings"
    case voice = "LeanVibe.VoiceSettings"
    case notifications = "LeanVibe.NotificationSettings"
    case kanban = "LeanVibe.KanbanSettings"
    case accessibility = "LeanVibe.AccessibilitySettings"
}

/// A protocol for settings structures to ensure they provide default values.
protocol SettingsProtocol: Codable {
    init()
}

// MARK: - Settings Definitions
/// Stores the settings related to the WebSocket server connection.
struct ConnectionPreferences: SettingsProtocol {
    var host: String = "127.0.0.1"
    var port: Int = 8765
    var authToken: String = "your_auth_token"
    var useSSL: Bool = false
    
    var url: URL? {
        var components = URLComponents()
        components.scheme = useSSL ? "wss" : "ws"
        components.host = host
        components.port = port
        return components.url
    }
    
    init(host: String = "127.0.0.1", port: Int = 8765, authToken: String = "your_auth_token", useSSL: Bool = false) {
        self.host = host
        self.port = port
        self.authToken = authToken
        self.useSSL = useSSL
    }
    
    init() {
        // Initializes with default values
    }
}

/// Stores settings related to voice commands and transcription.
struct VoiceSettings: SettingsProtocol {
    var wakeWord: String = "Hey Lean"
    var autoStartListening: Bool = true
    var autoStopListening: Bool = false
    var wakePhraseEnabled: Bool = true
    var wakePhraseSensitivity: Double = 0.5
    var voiceFeedbackEnabled: Bool = true
    var backgroundListening: Bool = false
    var recognitionLanguage: String = "en-US"
    
    init(wakeWord: String = "Hey Lean", autoStartListening: Bool = true) {
        self.wakeWord = wakeWord
        self.autoStartListening = autoStartListening
    }
    
    init() {
        // Default initializer
    }
}

/// Stores the settings related to notifications.
struct NotificationSettings: SettingsProtocol {
    var enableNotifications: Bool = true
    var notificationsEnabled: Bool = true // Alias for compatibility
    var alertTone: String = "default"
    var allowReminders: Bool = true
    var quietHoursEnabled: Bool = false
    var quietHoursStart: String = "22:00"
    var quietHoursEnd: String = "07:00"
    var enablePushNotifications: Bool = true
    var taskDeadlineNotifications: Bool = true
    var achievementNotifications: Bool = true
    var weeklyDigest: Bool = true
    
    // Additional properties used by NotificationSettingsView
    var taskUpdates: Bool = true
    var voiceNotificationsEnabled: Bool = true
    var systemNotificationsEnabled: Bool = true
    var taskNotificationsEnabled: Bool = true
    var bannerNotificationsEnabled: Bool = true
    var soundEnabled: Bool = true
    var vibrationEnabled: Bool = true
    var taskOverdueNotifications: Bool = true
    var voiceCommandResultNotifications: Bool = true
    var serverConnectionNotifications: Bool = true
    
    init(enableNotifications: Bool = true, alertTone: String = "default") {
        self.enableNotifications = enableNotifications
        self.notificationsEnabled = enableNotifications
        self.alertTone = alertTone
    }
    
    init() {
        // Default initializer
    }
}

/// Stores the settings related to the kanban board.
struct KanbanSettings: SettingsProtocol {
    var defaultView: String = "board" // "board" or "list"
    var showTaskIDs: Bool = false
    var showTaskIds: Bool = false // Alias for compatibility
    
    // Auto-refresh settings
    var autoRefresh: Bool = true
    var refreshInterval: Double = 30.0
    
    // Display settings
    var showStatistics: Bool = true
    var compactMode: Bool = false
    var enableAnimations: Bool = true
    var showColumnTaskCounts: Bool = true
    var enableColumnCustomization: Bool = true
    
    // Column settings
    var columnOrder: [String] = ["todo", "in-progress", "done"]
    
    // Voice integration
    var enableVoiceTaskCreation: Bool = false
    
    // Task settings
    var defaultTaskPriority: String = "medium"
    var autoAssignTasks: Bool = false
    var enableTaskNotifications: Bool = true
    var maxTasksPerColumn: Int = 50
    
    // Performance settings
    var enableInfiniteScroll: Bool = false
    var prefetchTaskDetails: Bool = true
    
    // Sync settings
    var syncWithBackend: Bool = true
    var offlineModeEnabled: Bool = false
    var conflictResolution: String = "manual"
    
    init(defaultView: String = "board", showTaskIDs: Bool = false) {
        self.defaultView = defaultView
        self.showTaskIDs = showTaskIDs
        self.showTaskIds = showTaskIDs
    }
    
    init() {
        // Default initializer
    }
}

/// Stores the settings related to accessibility features.
struct AccessibilitySettings: SettingsProtocol {
    var highContrastMode: Bool = false
    var reduceMotion: Bool = false
    var voiceOverOptimizations: Bool = false
    var largeFontSize: Bool = false
    var boldText: Bool = false
    var speechRateAdjustment: Double = 1.0
    var extendedVoiceCommands: Bool = false
    var extendedTouchTargets: Bool = false
    var reduceGestures: Bool = false
    var oneHandedMode: Bool = false
    
    init() {
        // Default initializer
    }
}

// MARK: - Environment Key for Swift 6 Injection
struct SettingsManagerEnvironmentKey: EnvironmentKey {
    static var defaultValue: SettingsManager {
        SettingsManager.shared
    }
}

extension EnvironmentValues {
    var settingsManager: SettingsManager {
        get { self[SettingsManagerEnvironmentKey.self] }
        set { self[SettingsManagerEnvironmentKey.self] = newValue }
    }
} 