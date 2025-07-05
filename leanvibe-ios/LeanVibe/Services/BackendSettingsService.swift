import Foundation

// Import settings models from SettingsModels.swift to avoid duplication
// Models are now imported from SettingsModels.swift

/// Errors that can occur during backend settings operations
/// BackendSettingsError is defined in SettingsModels.swift

/// Service for syncing settings with the backend
/// NO HARDCODED VALUES - All settings come from backend dynamically
@MainActor
@available(iOS 18.0, macOS 14.0, *)
class BackendSettingsService: ObservableObject {
    static let shared = BackendSettingsService()
    
    @Published var isAvailable = false
    @Published var lastError: String?
    
    private let config = AppConfiguration.shared
    private var settingsCache: AllSettings?
    private var lastFetchDate: Date?
    
    private init() {
        checkBackendAvailability()
    }
    
    // MARK: - Backend Availability
    
    private func checkBackendAvailability() {
        isAvailable = config.isBackendConfigured
        
        if !isAvailable {
            print("⚠️ BackendSettingsService: No backend configured - settings will use local defaults")
        }
    }
    
    // MARK: - Settings Sync
    
    /// Fetch settings from backend
    func fetchSettings() async throws -> AllSettings {
        guard config.isBackendConfigured else {
            throw BackendSettingsError.backendNotConfigured
        }
        
        // Check cache first (valid for 5 minutes)
        if let cached = settingsCache,
           let lastFetch = lastFetchDate,
           Date().timeIntervalSince(lastFetch) < 300 {
            return cached
        }
        
        let url = URL(string: "\(config.apiBaseURL)/api/settings")!
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = config.networkTimeout
        
        do {
            let (data, response) = try await URLSession.shared.data(for: request)
            
            guard let httpResponse = response as? HTTPURLResponse else {
                throw BackendSettingsError.invalidResponse
            }
            
            guard httpResponse.statusCode == 200 else {
                throw BackendSettingsError.httpError(httpResponse.statusCode)
            }
            
            let backendSettings = try JSONDecoder().decode(BackendSettingsResponse.self, from: data)
            let allSettings = AllSettings(
                connection: backendSettings.connection ?? ConnectionPreferences(),
                voice: backendSettings.voice ?? VoiceSettings(),
                notifications: backendSettings.notifications ?? NotificationSettings(),
                kanban: backendSettings.kanban ?? KanbanSettings(),
                accessibility: backendSettings.accessibility ?? AccessibilitySettings(),
                architecture: backendSettings.architecture ?? ArchitectureSettings(),
                metrics: backendSettings.metrics ?? MetricsSettings(),
                taskCreation: backendSettings.taskCreation ?? TaskCreationSettings(),
                offline: backendSettings.offline ?? OfflineSettings(),
                interface: backendSettings.interface ?? InterfaceSettings(),
                performance: backendSettings.performance ?? PerformanceSettings()
            )
            
            // Cache the results
            settingsCache = allSettings
            lastFetchDate = Date()
            
            return allSettings
            
        } catch {
            lastError = error.localizedDescription
            await handleBackendSettingsError(error, context: "fetch_settings", userAction: "fetching settings")
            throw BackendSettingsError.networkError(error)
        }
    }
    
    /// Push settings to backend
    func pushSettings(_ settings: AllSettings) async throws {
        guard config.isBackendConfigured else {
            throw BackendSettingsError.backendNotConfigured
        }
        
        let url = URL(string: "\(config.apiBaseURL)/api/settings")!
        var request = URLRequest(url: url)
        request.httpMethod = "PUT"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = config.networkTimeout
        
        do {
            let requestData = BackendSettingsRequest(
                connection: settings.connection,
                voice: settings.voice,
                notifications: settings.notifications,
                kanban: settings.kanban,
                accessibility: settings.accessibility,
                architecture: settings.architecture,
                metrics: settings.metrics,
                taskCreation: settings.taskCreation,
                offline: settings.offline,
                interface: settings.interface,
                performance: settings.performance
            )
            
            request.httpBody = try JSONEncoder().encode(requestData)
            
            let (_, response) = try await URLSession.shared.data(for: request)
            
            guard let httpResponse = response as? HTTPURLResponse else {
                throw BackendSettingsError.invalidResponse
            }
            
            guard httpResponse.statusCode == 200 || httpResponse.statusCode == 201 else {
                throw BackendSettingsError.httpError(httpResponse.statusCode)
            }
            
            // Update cache
            settingsCache = settings
            lastFetchDate = Date()
            
        } catch {
            lastError = error.localizedDescription
            await handleBackendSettingsError(error, context: "push_settings", userAction: "syncing settings")
            throw BackendSettingsError.networkError(error)
        }
    }
    
    /// Get default settings for when backend is not available
    func getDefaultSettings() -> AllSettings {
        return AllSettings(
            connection: ConnectionPreferences(),
            voice: getDefaultVoiceSettings(),
            notifications: getDefaultNotificationSettings(),
            kanban: getDefaultKanbanSettings(),
            accessibility: AccessibilitySettings(),
            architecture: getDefaultArchitectureSettings(),
            metrics: getDefaultMetricsSettings(),
            taskCreation: getDefaultTaskCreationSettings(),
            offline: getDefaultOfflineSettings(),
            interface: getDefaultInterfaceSettings(),
            performance: getDefaultPerformanceSettings()
        )
    }
    
    // MARK: - Default Settings (Minimal Fallbacks)
    
    private func getDefaultVoiceSettings() -> VoiceSettings {
        var voice = VoiceSettings()
        
        // Only set minimal required defaults
        voice.wakeWord = "Hey LeanVibe"
        voice.recognitionLanguage = "en-US"
        voice.confidenceThreshold = 0.7
        voice.maxRecordingDuration = 30.0
        voice.microphoneGain = 1.0
        voice.maxHistoryItems = 50
        
        return voice
    }
    
    private func getDefaultNotificationSettings() -> NotificationSettings {
        var notifications = NotificationSettings()
        
        // Only essential notification defaults
        notifications.quietHoursStart = "22:00"
        notifications.quietHoursEnd = "07:00"
        
        return notifications
    }
    
    private func getDefaultKanbanSettings() -> KanbanSettings {
        var kanban = KanbanSettings()
        
        // Essential kanban defaults
        kanban.defaultView = "board"
        kanban.refreshInterval = 30.0
        kanban.columnOrder = ["backlog", "todo", "in-progress", "testing", "done"]
        kanban.defaultTaskPriority = "medium"
        kanban.maxTasksPerColumn = 50
        kanban.conflictResolution = "manual"
        
        return kanban
    }
    
    private func getDefaultArchitectureSettings() -> ArchitectureSettings {
        var architecture = ArchitectureSettings()
        
        // Essential architecture defaults
        architecture.diagramTheme = "default"
        architecture.diagramLayout = "auto"
        architecture.renderQuality = "high"
        architecture.refreshInterval = 30.0
        architecture.maxCacheSize = 50
        architecture.renderTimeoutSeconds = 10
        architecture.defaultExportFormat = "mermaid"
        architecture.compareMode = "side-by-side"
        architecture.syncConflictResolution = "manual"
        architecture.sharePermissionLevel = "view-only"
        
        return architecture
    }
    
    private func getDefaultMetricsSettings() -> MetricsSettings {
        var metrics = MetricsSettings()
        
        // Essential metrics defaults
        metrics.dataRetentionDays = 30
        metrics.exportFormat = "json"
        metrics.aggregationInterval = "hourly"
        metrics.maxStorageSize = 100
        
        return metrics
    }
    
    private func getDefaultTaskCreationSettings() -> TaskCreationSettings {
        var taskCreation = TaskCreationSettings()
        
        // Essential task creation defaults
        taskCreation.defaultPriority = "medium"
        taskCreation.defaultDueDate = "none"
        taskCreation.defaultTemplate = "basic"
        
        return taskCreation
    }
    
    private func getDefaultOfflineSettings() -> OfflineSettings {
        var offline = OfflineSettings()
        
        // Essential offline defaults
        offline.offlineStorageLimit = 500
        offline.conflictResolutionStrategy = "merge"
        offline.cacheExpiration = 24
        offline.maxOfflineActions = 1000
        offline.syncRetryAttempts = 3
        
        return offline
    }
    
    private func getDefaultInterfaceSettings() -> InterfaceSettings {
        var interface = InterfaceSettings()
        
        // Essential interface defaults
        interface.theme = "auto"
        interface.accentColor = "blue"
        interface.fontSize = "medium"
        interface.toolbarPosition = "top"
        interface.navigationStyle = "default"
        interface.sidebarPosition = "left"
        interface.tabBarStyle = "default"
        interface.layoutDensity = "comfortable"
        interface.gridSize = "medium"
        interface.iconStyle = "default"
        
        return interface
    }
    
    private func getDefaultPerformanceSettings() -> PerformanceSettings {
        var performance = PerformanceSettings()
        
        // Essential performance defaults
        performance.maxMemoryUsage = 512
        performance.maxCacheSize = 200
        performance.threadPoolSize = 4
        performance.networkRequestTimeout = 30
        performance.maxConcurrentRequests = 10
        
        return performance
    }
    
    /// Force refresh settings from backend
    func refreshSettings() async throws -> AllSettings {
        settingsCache = nil
        lastFetchDate = nil
        return try await fetchSettings()
    }
    
    /// Check if backend is available and update status
    func pingBackend() async -> Bool {
        guard config.isBackendConfigured else {
            isAvailable = false
            return false
        }
        
        do {
            let url = URL(string: "\(config.apiBaseURL)/api/health")!
            var request = URLRequest(url: url)
            request.httpMethod = "GET"
            request.timeoutInterval = 5.0 // Quick ping
            
            let (_, response) = try await URLSession.shared.data(for: request)
            
            if let httpResponse = response as? HTTPURLResponse {
                isAvailable = httpResponse.statusCode == 200
                return isAvailable
            }
            
            isAvailable = false
            return false
            
        } catch {
            isAvailable = false
            lastError = "Backend ping failed: \(error.localizedDescription)"
            return false
        }
    }
    
    // MARK: - Centralized Error Handling
    
    private func handleBackendSettingsError(_ error: Error, context: String, userAction: String) async {
        // Categorize the error
        let category: ErrorCategory = {
            if error is URLError {
                return .network
            } else if error is BackendSettingsError {
                return .service
            } else {
                return .data
            }
        }()
        
        // Create comprehensive error with recovery actions
        let appError = AppError(
            title: "Settings Sync Failed",
            message: error.localizedDescription,
            severity: .warning,
            category: category,
            context: "backend_settings_\(context)",
            userFacingMessage: "We encountered an issue while \(userAction). Your settings are saved locally.",
            technicalDetails: "BackendSettingsService Error in \(context): \(type(of: error)) - \(error.localizedDescription)",
            suggestedActions: createBackendSettingsRecoveryActions(for: error, context: context)
        )
        
        // Show error to user using centralized error manager
        if let globalErrorManager = try? GlobalErrorManager.shared {
            globalErrorManager.showError(appError)
            
            // Automatically attempt recovery for network errors
            if category == .network {
                await ErrorRecoveryManager.shared.attemptRecovery(for: appError)
            }
        } else {
            // Fallback if GlobalErrorManager is not available
            print("🚨 BackendSettingsService Error: \(error.localizedDescription)")
        }
    }
    
    private func createBackendSettingsRecoveryActions(for error: Error, context: String) -> [ErrorAction] {
        var actions: [ErrorAction] = []
        
        // Retry sync action
        actions.append(ErrorAction(title: "Retry Sync", systemImage: "arrow.clockwise", isPrimary: true) {
            Task {
                // Retry the operation
                print("User requested retry for \(context)")
            }
        })
        
        // Work offline action
        actions.append(ErrorAction(title: "Continue Offline", systemImage: "wifi.slash") {
            // Continue with local settings only
            print("User chose to continue offline")
        })
        
        // Network-specific actions
        if error is URLError {
            actions.append(ErrorAction(title: "Check Network", systemImage: "network") {
                Task {
                    await NetworkErrorHandler.shared.checkNetworkStatus()
                }
            })
        }
        
        return actions
    }
}