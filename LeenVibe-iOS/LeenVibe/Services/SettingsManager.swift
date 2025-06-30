import SwiftUI
import Combine

/// Centralized settings management for all LeanVibe features
/// Coordinates settings for Voice, Kanban, Architecture, and other systems
@available(iOS 14.0, macOS 10.15, *)
@MainActor
class SettingsManager: ObservableObject {
    @MainActor static let shared = SettingsManager()
    
    // MARK: - Published Settings
    
    @Published var appSettings = AppSettings()
    @Published var voiceSettings = VoiceSettings()
    @Published var kanbanSettings = KanbanSettings()
    @Published var notificationSettings = NotificationSettings()
    @Published var accessibilitySettings = AccessibilitySettings()
    @Published var connectionSettings = ConnectionPreferences()
    
    // Voice Settings
    @Published var isVoiceEnabled: Bool = true
    @Published var voiceSensitivity: Double = 0.5
    @Published var wakePhraseEnabled: Bool = true
    @Published var selectedWakePhrase: String = "Hey LeanVibe"
    @Published var voiceLanguage: String = "en-US"
    @Published var continuousListening: Bool = false
    @Published var backgroundListening: Bool = false
    
    // Notification Settings  
    @Published var notificationsEnabled: Bool = true
    @Published var terminalNotifications: Bool = true
    @Published var buildNotifications: Bool = true
    @Published var errorNotifications: Bool = true
    @Published var soundEnabled: Bool = true
    @Published var vibrationEnabled: Bool = true
    @Published var quietHoursEnabled: Bool = false
    @Published var quietHoursStart: Date = Calendar.current.date(from: DateComponents(hour: 22, minute: 0)) ?? Date()
    @Published var quietHoursEnd: Date = Calendar.current.date(from: DateComponents(hour: 8, minute: 0)) ?? Date()
    
    // Server Settings
    @Published var serverURL: String = "http://localhost:8000"
    @Published var autoReconnect: Bool = true
    @Published var connectionTimeout: Double = 30.0
    @Published var maxRetries: Int = 3
    
    // Kanban Settings
    @Published var autoArchive: Bool = true
    @Published var archiveDays: Int = 30
    @Published var showMetrics: Bool = true
    @Published var taskAnimations: Bool = true
    
    // Architecture Settings
    @Published var autoRefreshDiagrams: Bool = true
    @Published var refreshInterval: Double = 60.0
    @Published var diagramTheme: String = "default"
    @Published var showNodeLabels: Bool = true
    
    // Accessibility Settings
    @Published var fontSize: Double = 16.0
    @Published var highContrast: Bool = false
    @Published var reduceMotion: Bool = false
    @Published var voiceOver: Bool = false
    
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
        accessibilitySettings = AccessibilitySettings.load()
        connectionSettings = ConnectionPreferences.load()
        loadSettings()
    }
    
    /// Save all settings to persistent storage
    func saveAllSettings() {
        appSettings.save()
        voiceSettings.save()
        kanbanSettings.save()
        notificationSettings.save()
        accessibilitySettings.save()
        connectionSettings.save()
        saveSettings()
    }
    
    /// Reset all settings to defaults
    func resetAllSettings() {
        appSettings = AppSettings()
        voiceSettings = VoiceSettings()
        kanbanSettings = KanbanSettings()
        notificationSettings = NotificationSettings()
        accessibilitySettings = AccessibilitySettings()
        connectionSettings = ConnectionPreferences()
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
        case is AccessibilitySettings.Type:
            accessibilitySettings = AccessibilitySettings()
            accessibilitySettings.save()
        case is ConnectionPreferences.Type:
            connectionSettings = ConnectionPreferences()
            connectionSettings.save()
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
            accessibility: accessibilitySettings,
            connection: connectionSettings,
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
        accessibilitySettings = importData.accessibility
        connectionSettings = importData.connection
        
        saveAllSettings()
    }
    
    // MARK: - Private Methods
    
    private func setupAutoSave() {
        // Use CombineLatest4 instead of CombineLatest5 since CombineLatest5 doesn't exist
        Publishers.CombineLatest4(
            $isVoiceEnabled,
            $notificationsEnabled,
            $serverURL,
            $autoReconnect
        )
        .debounce(for: .seconds(1), scheduler: RunLoop.main)
        .sink { [weak self] (_: Bool, _: Bool, _: String, _: Bool) in
            self?.saveSettings()
        }
        .store(in: &cancellables)
        
        // Setup another combiner for the remaining settings
        Publishers.CombineLatest4(
            $voiceSensitivity,
            $fontSize,
            $refreshInterval,
            $connectionTimeout
        )
        .debounce(for: .seconds(1), scheduler: RunLoop.main)
        .sink { [weak self] (_: Double, _: Double, _: Double, _: Double) in
            self?.saveSettings()
        }
        .store(in: &cancellables)
    }
    
    private func saveSettings() {
        let encoder = JSONEncoder()
        
        let settingsData = SettingsData(
            isVoiceEnabled: isVoiceEnabled,
            voiceSensitivity: voiceSensitivity,
            wakePhraseEnabled: wakePhraseEnabled,
            selectedWakePhrase: selectedWakePhrase,
            voiceLanguage: voiceLanguage,
            notificationsEnabled: notificationsEnabled,
            terminalNotifications: terminalNotifications,
            buildNotifications: buildNotifications,
            errorNotifications: errorNotifications,
            soundEnabled: soundEnabled,
            vibrationEnabled: vibrationEnabled,
            serverURL: serverURL,
            autoReconnect: autoReconnect,
            connectionTimeout: connectionTimeout,
            maxRetries: maxRetries,
            autoArchive: autoArchive,
            archiveDays: archiveDays,
            showMetrics: showMetrics,
            taskAnimations: taskAnimations,
            autoRefreshDiagrams: autoRefreshDiagrams,
            refreshInterval: refreshInterval,
            diagramTheme: diagramTheme,
            showNodeLabels: showNodeLabels,
            fontSize: fontSize,
            highContrast: highContrast,
            reduceMotion: reduceMotion,
            voiceOver: voiceOver
        )
        
        do {
            let data = try encoder.encode(settingsData)
            UserDefaults.standard.set(data, forKey: "LeanVibeSettings")
        } catch {
            print("Failed to save settings: \(error)")
        }
    }
    
    private func loadSettings() {
        guard let data = UserDefaults.standard.data(forKey: "LeanVibeSettings"),
              let settingsData = try? JSONDecoder().decode(SettingsData.self, from: data) else {
            return
        }
        
        isVoiceEnabled = settingsData.isVoiceEnabled
        voiceSensitivity = settingsData.voiceSensitivity
        wakePhraseEnabled = settingsData.wakePhraseEnabled
        selectedWakePhrase = settingsData.selectedWakePhrase
        voiceLanguage = settingsData.voiceLanguage
        notificationsEnabled = settingsData.notificationsEnabled
        terminalNotifications = settingsData.terminalNotifications
        buildNotifications = settingsData.buildNotifications
        errorNotifications = settingsData.errorNotifications
        soundEnabled = settingsData.soundEnabled
        vibrationEnabled = settingsData.vibrationEnabled
        serverURL = settingsData.serverURL
        autoReconnect = settingsData.autoReconnect
        connectionTimeout = settingsData.connectionTimeout
        maxRetries = settingsData.maxRetries
        autoArchive = settingsData.autoArchive
        archiveDays = settingsData.archiveDays
        showMetrics = settingsData.showMetrics
        taskAnimations = settingsData.taskAnimations
        autoRefreshDiagrams = settingsData.autoRefreshDiagrams
        refreshInterval = settingsData.refreshInterval
        diagramTheme = settingsData.diagramTheme
        showNodeLabels = settingsData.showNodeLabels
        fontSize = settingsData.fontSize
        highContrast = settingsData.highContrast
        reduceMotion = settingsData.reduceMotion
        voiceOver = settingsData.voiceOver
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
    var wakePhrasePhrase = "Hey LeanVibe"
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

enum ConflictResolution: String, CaseIterable, Codable {
    case clientWins = "client_wins"
    case serverWins = "server_wins"
    case manual = "manual"
    case timestamp = "timestamp"
    
    var displayName: String {
        switch self {
        case .clientWins: return "Client Wins"
        case .serverWins: return "Server Wins"
        case .manual: return "Manual Resolution"
        case .timestamp: return "Latest Timestamp"
        }
    }
}

struct KanbanSettings: SettingsProtocol {
    static let storageKey = "KanbanSettings"
    
    // Board behavior
    var autoRefresh = true
    var refreshInterval: TimeInterval = 30.0
    var showStatistics = true
    var compactMode = false
    var enableAnimations = true
    var showColumnTaskCounts = true
    var maxTasksPerColumn = 20
    var enableColumnCustomization = true
    var enableInfiniteScroll = false
    var columnOrder: [String] = ["todo", "inProgress", "review", "done"]
    
    // Task display
    var showAssignee = true
    var showDueDate = true
    var showPriority = true
    var taskCardSize: TaskCardSize = .medium
    var showTaskIds = false
    var defaultTaskPriority: TaskPriority = .medium
    var prefetchTaskDetails = true
    
    // Voice features
    var enableVoiceTaskCreation = false
    var autoAssignTasks = false
    var enableTaskNotifications = true
    
    // Sync settings
    var syncWithBackend = false
    var offlineModeEnabled = true
    var conflictResolution: ConflictResolution = .timestamp
    
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

enum TaskCardSize: String, CaseIterable, Codable {
    case small = "small"
    case medium = "medium"
    case large = "large"
    
    var displayName: String {
        switch self {
        case .small: return "Small"
        case .medium: return "Medium"
        case .large: return "Large"
        }
    }
}


// MARK: - Notification Settings

struct NotificationSettings: SettingsProtocol {
    static let storageKey = "NotificationSettings"
    
    // General notification settings
    var notificationsEnabled = true
    var alertStyle: AlertStyle = .banner
    var soundEnabled = true
    var vibrationEnabled = true
    var showPreviews: ShowPreviews = .always
    
    // Notification types
    var taskUpdates = true
    var agentMentions = true
    var projectStatusChanges = true
    var newDecisionLogs = true
    var systemAlerts = true
    var voiceNotificationsEnabled = true
    var bannerNotificationsEnabled = true
    var taskOverdueNotifications = true
    var taskNotificationsEnabled = true
    var systemNotificationsEnabled = true
    var voiceCommandResultNotifications = true
    var serverConnectionNotifications = true
    
    // Quiet hours
    var quietHoursEnabled = false
    var quietHoursStart = "22:00"
    var quietHoursEnd = "08:00"
    
    // Push notifications
    var pushNotificationsEnabled: Bool = true
    var mentionNotificationsEnabled: Bool = true
    
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

enum AlertStyle: String, CaseIterable, Codable {
    case banner = "banner"
    case alert = "alert"
    case none = "none"
}

enum ShowPreviews: String, CaseIterable, Codable {
    case always = "always"
    case whenUnlocked = "when_unlocked"
    case never = "never"
}


// MARK: - Accessibility Settings

struct AccessibilitySettings: SettingsProtocol {
    static let storageKey = "AccessibilitySettings"
    
    // Text size and contrast
    var dynamicTypeEnabled = true
    var largerTextEnabled = false
    var highContrastEnabled = false
    var boldText = false
    
    // Motion and animation
    var reduceMotion = false
    
    // VoiceOver
    var voiceOverEnabled = false
    var voiceOverOptimizations = false
    var speechRateAdjustment: Double = 1.0
    var extendedVoiceCommands = false
    
    // High contrast mode
    var highContrastMode: Bool = false
    
    // Large font size
    var largeFontSize: Bool = false
    
    // Touch targets
    var extendedTouchTargets = false
    var reduceGestures = false
    var oneHandedMode = false
    
    // Dynamic type support
    var dynamicTypeSupport: Bool = true
    
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

// MARK: - Connection Settings

struct ConnectionPreferences: SettingsProtocol {
    static let storageKey = "ConnectionSettings"
    
    var backgroundSyncEnabled: Bool = true
    var autoConnect: Bool = true
    var connectionTimeout: Double = 30.0
    
    // Server connection properties
    var serverURL: String = ""
    var serverPort: Int = 8000
    var useHTTPS: Bool = false
    var autoReconnect: Bool = true
    var retryAttempts: Int = 3
    var retryDelay: Double = 5.0
    
    // WebSocket properties
    var webSocketEnabled: Bool = true
    var webSocketHeartbeat: Double = 30.0
    var webSocketReconnectDelay: Double = 5.0
    
    static func load() -> ConnectionPreferences {
        guard let data = UserDefaults.standard.data(forKey: storageKey),
              let settings = try? JSONDecoder().decode(ConnectionPreferences.self, from: data) else {
            return ConnectionPreferences()
        }
        return settings
    }
    
    func save() {
        if let data = try? JSONEncoder().encode(self) {
            UserDefaults.standard.set(data, forKey: Self.storageKey)
        }
    }
}

// MARK: - Settings Export Structure

struct SettingsExport: Codable {
    let app: AppSettings
    let voice: VoiceSettings
    let kanban: KanbanSettings
    let notifications: NotificationSettings
    let accessibility: AccessibilitySettings
    let connection: ConnectionPreferences
    let exportDate: Date
}

// Supporting data structure for encoding/decoding
private struct SettingsData: Codable {
    let isVoiceEnabled: Bool
    let voiceSensitivity: Double
    let wakePhraseEnabled: Bool
    let selectedWakePhrase: String
    let voiceLanguage: String
    let notificationsEnabled: Bool
    let terminalNotifications: Bool
    let buildNotifications: Bool
    let errorNotifications: Bool
    let soundEnabled: Bool
    let vibrationEnabled: Bool
    let serverURL: String
    let autoReconnect: Bool
    let connectionTimeout: Double
    let maxRetries: Int
    let autoArchive: Bool
    let archiveDays: Int
    let showMetrics: Bool
    let taskAnimations: Bool
    let autoRefreshDiagrams: Bool
    let refreshInterval: Double
    let diagramTheme: String
    let showNodeLabels: Bool
    let fontSize: Double
    let highContrast: Bool
    let reduceMotion: Bool
    let voiceOver: Bool
} 