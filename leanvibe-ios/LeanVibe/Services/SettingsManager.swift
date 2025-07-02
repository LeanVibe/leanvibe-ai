import Foundation
import SwiftUI
import Observation

/// Represents user-configurable settings for the application.
@available(iOS 18.0, macOS 14.0, *)
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
    var architecture: ArchitectureSettings {
        didSet {
            save(architecture, for: .architecture)
        }
    }

    init() {
        // Initialize with defaults first to satisfy Swift 6 initialization requirements
        self.connection = ConnectionPreferences()
        self.voice = VoiceSettings()
        self.notifications = NotificationSettings()
        self.kanban = KanbanSettings()
        self.accessibility = AccessibilitySettings()
        self.architecture = ArchitectureSettings()
        
        // Then load saved values
        loadStoredValues()
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

    // MARK: - Public Methods
    func resetAll() {
        self.connection = ConnectionPreferences()
        self.voice = VoiceSettings()
        self.notifications = NotificationSettings()
        self.kanban = KanbanSettings()
        self.accessibility = AccessibilitySettings()
        self.architecture = ArchitectureSettings()
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
        save(architecture, for: .architecture)
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
    case architecture = "LeanVibe.ArchitectureSettings"
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
    
    // Additional properties used by VoiceSettingsView
    var confidenceThreshold: Double = 0.7
    var maxRecordingDuration: Double = 30.0
    var enableVoiceCommands: Bool = true
    var commandHistoryEnabled: Bool = true
    var maxHistoryItems: Int = 50
    var enableCustomCommands: Bool = false
    var microphoneGain: Double = 1.0
    var noiseReduction: Bool = true
    var echoCanselation: Bool = true
    
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

/// Stores the settings related to architecture visualization features.
struct ArchitectureSettings: SettingsProtocol {
    // MARK: - Diagram Rendering Settings
    var diagramTheme: String = "default"
    var diagramLayout: String = "auto"
    var renderQuality: String = "high"
    var maxNodeCount: Int = 100
    var enableAnimations: Bool = true
    var animationSpeed: Double = 1.0
    var zoomLevel: Double = 1.0
    var showNodeLabels: Bool = true
    var showEdgeLabels: Bool = true
    var compactLayout: Bool = false
    
    // MARK: - Change Detection Settings
    var autoRefreshEnabled: Bool = true
    var refreshInterval: Double = 30.0
    var changeNotificationsEnabled: Bool = true
    var highlightChanges: Bool = true
    var changeNotificationSound: Bool = false
    var autoDetectArchitectureChanges: Bool = true
    var compareMode: String = "side-by-side" // "side-by-side", "overlay", "sequential"
    
    // MARK: - Approval Workflow Settings
    var requireApprovalForChanges: Bool = false
    var autoApproveMinorChanges: Bool = true
    var approvalNotificationsEnabled: Bool = true
    var approvalTimeoutMinutes: Int = 60
    var enableApprovalComments: Bool = true
    var showApprovalHistory: Bool = true
    
    // MARK: - Performance Settings
    var enableMemoryOptimization: Bool = false
    var maxCacheSize: Int = 50 // MB
    var renderTimeoutSeconds: Int = 10
    var enableWebViewPooling: Bool = true
    var maxConcurrentRenders: Int = 3
    var enableBackgroundRendering: Bool = false
    var performanceMonitoringEnabled: Bool = false
    
    // MARK: - Export and Sharing Settings
    var defaultExportFormat: String = "mermaid" // "mermaid", "svg", "png", "pdf"
    var exportQuality: String = "high"
    var includeMetadataInExport: Bool = true
    var enableShareExtension: Bool = true
    var autoSaveExports: Bool = false
    var exportCompressionEnabled: Bool = true
    
    // MARK: - UI Customization Settings
    var showToolbar: Bool = true
    var showMinimap: Bool = false
    var enableFullScreenMode: Bool = true
    var showGridLines: Bool = false
    var showRuler: Bool = false
    var darkModeSupport: Bool = true
    var customColorScheme: String = "system" // "system", "light", "dark", "custom"
    
    // MARK: - Interaction Settings  
    var enableNodeInteraction: Bool = true
    var enableZoomGestures: Bool = true
    var enablePanGestures: Bool = true
    var doubleTapToZoom: Bool = true
    var longPressForDetails: Bool = true
    var keyboardShortcutsEnabled: Bool = true
    
    // MARK: - Advanced Features
    var enableDiagramVersioning: Bool = false
    var maxVersionHistory: Int = 10
    var enableCollaborativeEditing: Bool = false
    var enableRealTimeSync: Bool = false
    var enableDiagramComments: Bool = false
    var enableDiagramAnnotations: Bool = false
    var enableCustomNodeTypes: Bool = false
    
    // MARK: - Network and Sync Settings
    var enableOnlineSync: Bool = true
    var syncConflictResolution: String = "manual" // "manual", "local-wins", "remote-wins", "merge"
    var offlineModeEnabled: Bool = true
    var enableDiagramSharing: Bool = true
    var sharePermissionLevel: String = "view-only" // "view-only", "comment", "edit"
    
    // MARK: - Notification Settings
    var diagramUpdateNotifications: Bool = true
    var errorNotifications: Bool = true
    var performanceWarnings: Bool = false
    var newFeatureNotifications: Bool = true
    var weeklyDigestEnabled: Bool = false
    
    // MARK: - Accessibility Features
    var highContrastDiagrams: Bool = false
    var largeTextInDiagrams: Bool = false
    var voiceOverDiagramDescriptions: Bool = false
    var reducedMotionDiagrams: Bool = false
    var alternativeTextForNodes: Bool = true
    
    init() {
        // Default initializer with sensible defaults
    }
}

 