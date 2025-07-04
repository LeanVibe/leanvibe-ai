import Foundation

// MARK: - Backend Settings Error Types
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

// MARK: - Temporary AllSettings Definition (to fix compilation)
struct AllSettings: Codable {
    let connection: ConnectionPreferences
    let voice: VoiceSettings
    let notifications: NotificationSettings
    let kanban: KanbanSettings
    let accessibility: AccessibilitySettings
    let architecture: ArchitectureSettings
}

// Note: Full model definitions are in SettingsManager.swift
// This is a temporary stub to resolve compilation issues

/// Service for syncing settings with the backend
/// NO HARDCODED VALUES - All settings come from backend dynamically
@available(iOS 18.0, macOS 14.0, *)
@MainActor
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
                architecture: backendSettings.architecture ?? ArchitectureSettings()
            )
            
            // Cache the results
            settingsCache = allSettings
            lastFetchDate = Date()
            
            return allSettings
            
        } catch {
            lastError = error.localizedDescription
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
                architecture: settings.architecture
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
            architecture: getDefaultArchitectureSettings()
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
}

// Models are now imported from SettingsModels.swift