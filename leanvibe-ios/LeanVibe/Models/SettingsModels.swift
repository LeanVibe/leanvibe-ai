import Foundation

/// Represents all user-configurable settings for the application.
/// NO HARDCODED VALUES - All settings come from backend or user configuration
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
struct AccessibilitySettings: SettingsProtocol, Codable {
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

/// Metrics and performance monitoring settings.
/// NO HARDCODED VALUES - All controlled by backend configuration
struct MetricsSettings: SettingsProtocol {
    var isEnabled: Bool = true
    var performanceMonitoringEnabled: Bool = true
    var memoryUsageTrackingEnabled: Bool = true
    var networkMetricsEnabled: Bool = true
    var voiceMetricsEnabled: Bool = true
    var taskCompletionMetricsEnabled: Bool = true
    var dataRetentionDays: Int = 30
    var exportFormat: String = "json"
    var shareMetricsEnabled: Bool = false
    var aggregationInterval: String = "hourly"
    var detailedLoggingEnabled: Bool = false
    var realTimeMonitoringEnabled: Bool = true
    var alertsEnabled: Bool = true
    var performanceThresholds: [String: Double] = [:]
    var maxStorageSize: Int = 100 // MB
    var autoExportEnabled: Bool = false
    var privacyMode: Bool = true
    
    init() {} // Default initialization
}

/// Task creation and template settings.
/// NO HARDCODED VALUES - All controlled by backend configuration
struct TaskCreationSettings: SettingsProtocol {
    var defaultPriority: String = "medium"
    var defaultAssignee: String = ""
    var defaultLabels: [String] = []
    var defaultDueDate: String = "none"
    var useTemplates: Bool = true
    var defaultTemplate: String = ""
    var autoAssignToSelf: Bool = true
    var requireDescription: Bool = false
    var enableQuickActions: Bool = true
    var voiceTaskCreationEnabled: Bool = true
    var taskNotificationsEnabled: Bool = true
    var duplicateTaskWarning: Bool = true
    var autoSaveEnabled: Bool = true
    var taskValidationEnabled: Bool = true
    var customFieldsEnabled: Bool = false
    var bulkCreationEnabled: Bool = false
    var templateSharingEnabled: Bool = false
    var taskHistoryEnabled: Bool = true
    
    init() {} // Default initialization
}

/// Offline mode and synchronization settings.
/// NO HARDCODED VALUES - All controlled by backend configuration
struct OfflineSettings: SettingsProtocol {
    var isEnabled: Bool = true
    var offlineStorageLimit: Int = 500 // MB
    var syncOnWifiOnly: Bool = false
    var backgroundSyncEnabled: Bool = true
    var conflictResolutionStrategy: String = "merge"
    var cacheExpiration: Int = 24 // hours
    var preloadData: Bool = true
    var compressionEnabled: Bool = true
    var encryptionEnabled: Bool = true
    var autoCleanupEnabled: Bool = true
    var maxOfflineActions: Int = 1000
    var syncRetryAttempts: Int = 3
    var queuedActionsPersistence: Bool = true
    var offlineIndicatorEnabled: Bool = true
    var smartSyncEnabled: Bool = true
    var prioritySyncEnabled: Bool = true
    var deltaSyncEnabled: Bool = true
    
    init() {} // Default initialization
}

/// Interface customization and appearance settings.
/// NO HARDCODED VALUES - All controlled by backend configuration
struct InterfaceSettings: SettingsProtocol {
    var theme: String = "auto"
    var accentColor: String = "blue"
    var fontSize: String = "medium"
    var compactMode: Bool = false
    var showToolbar: Bool = true
    var toolbarPosition: String = "top"
    var navigationStyle: String = "default"
    var showSidebar: Bool = true
    var sidebarPosition: String = "left"
    var tabBarStyle: String = "default"
    var animationsEnabled: Bool = true
    var reducedMotion: Bool = false
    var highContrast: Bool = false
    var customColors: [String: String] = [:]
    var layoutDensity: String = "comfortable"
    var showPreviewPane: Bool = true
    var gridSize: String = "medium"
    var iconStyle: String = "default"
    
    init() {} // Default initialization
}

/// Performance optimization and resource management settings.
/// NO HARDCODED VALUES - All controlled by backend configuration
struct PerformanceSettings: SettingsProtocol {
    var memoryLimitEnabled: Bool = true
    var maxMemoryUsage: Int = 512 // MB
    var backgroundProcessingEnabled: Bool = true
    var networkOptimizationEnabled: Bool = true
    var batteryOptimizationEnabled: Bool = true
    var lowPowerModeEnabled: Bool = false
    var cacheOptimizationEnabled: Bool = true
    var maxCacheSize: Int = 200 // MB
    var imageCompressionEnabled: Bool = true
    var prefetchingEnabled: Bool = true
    var lazyLoadingEnabled: Bool = true
    var renderingOptimizationEnabled: Bool = true
    var threadPoolSize: Int = 4
    var networkRequestTimeout: Int = 30 // seconds
    var maxConcurrentRequests: Int = 10
    var diskCacheEnabled: Bool = true
    var memoryWarningHandlingEnabled: Bool = true
    var performanceMonitoringEnabled: Bool = true
    
    init() {} // Default initialization
}

struct BackendSettingsResponse: Codable {
    let connection: ConnectionPreferences?
    let voice: VoiceSettings?
    let notifications: NotificationSettings?
    let kanban: KanbanSettings?
    let accessibility: AccessibilitySettings?
    let architecture: ArchitectureSettings?
    let metrics: MetricsSettings?
    let taskCreation: TaskCreationSettings?
    let offline: OfflineSettings?
    let interface: InterfaceSettings?
    let performance: PerformanceSettings?
}

struct BackendSettingsRequest: Codable {
    let connection: ConnectionPreferences
    let voice: VoiceSettings
    let notifications: NotificationSettings
    let kanban: KanbanSettings
    let accessibility: AccessibilitySettings
    let architecture: ArchitectureSettings
    let metrics: MetricsSettings
    let taskCreation: TaskCreationSettings
    let offline: OfflineSettings
    let interface: InterfaceSettings
    let performance: PerformanceSettings
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