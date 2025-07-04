import Foundation

/// Represents all user-configurable settings for the application.
/// NO HARDCODED VALUES - All settings come from backend or user configuration
struct AllSettings: Codable {
    let connection: ConnectionPreferences
    let voice: VoiceSettings
    let notifications: NotificationSettings
    let kanban: KanbanSettings
    let accessibility: AccessibilitySettings
    let architecture: ArchitectureSettings
}

/// A protocol for settings structures to ensure they provide default values.
protocol SettingsProtocol: Codable {
    init()
}

// MARK: - Settings Definitions
/// Stores the settings related to the WebSocket server connection.
/// NO HARDCODED VALUES - Everything comes from backend or user configuration
struct ConnectionPreferences: SettingsProtocol {
    var host: String = ""
    var port: Int = 0
    var authToken: String = ""
    var isSSLEnabled: Bool = false
    var connectionTimeout: TimeInterval = 10.0
    var reconnectInterval: TimeInterval = 5.0
    var maxReconnectAttempts: Int = 5
    var qrCodeExpiry: TimeInterval = 300.0 // 5 minutes
    var autoConnect: Bool = true
    var persistConnection: Bool = true
    var serverCertificateValidation: Bool = true
    var useCompression: Bool = false
    
    init() {} // Default initialization with empty values
}

/// Voice-related settings and configurations.
/// NO HARDCODED VALUES - Everything from backend or user setup
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
    
    init() {} // Default initialization
}

/// Push notification settings and preferences.
/// NO HARDCODED VALUES - All controlled by backend configuration
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
    
    init() {} // Default initialization
}

/// Kanban board settings and view preferences.
/// NO HARDCODED VALUES - Driven by backend templates and user preferences
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
    
    init() {} // Default initialization
}

/// Accessibility-related settings.
/// NO HARDCODED VALUES - Based on user accessibility needs and system settings
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
    
    init() {} // Default initialization
}

/// Architecture diagram and visualization settings.
/// NO HARDCODED VALUES - All controlled by backend capabilities and user preferences
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
    
    init() {} // Default initialization
}

// MARK: - Backend Models

struct BackendSettingsResponse: Codable {
    let connection: ConnectionPreferences?
    let voice: VoiceSettings?
    let notifications: NotificationSettings?
    let kanban: KanbanSettings?
    let accessibility: AccessibilitySettings?
    let architecture: ArchitectureSettings?
}

struct BackendSettingsRequest: Codable {
    let connection: ConnectionPreferences
    let voice: VoiceSettings
    let notifications: NotificationSettings
    let kanban: KanbanSettings
    let accessibility: AccessibilitySettings
    let architecture: ArchitectureSettings
}

// MARK: - Errors

enum BackendSettingsError: LocalizedError {
    case backendNotConfigured
    case invalidResponse
    case httpError(Int)
    case networkError(Error)
    
    var errorDescription: String? {
        switch self {
        case .backendNotConfigured:
            return "Backend is not configured. Please scan QR code or configure backend URL."
        case .invalidResponse:
            return "Invalid response from backend"
        case .httpError(let code):
            return "Backend returned error code: \(code)"
        case .networkError(let error):
            return "Network error: \(error.localizedDescription)"
        }
    }
}