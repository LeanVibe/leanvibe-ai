import Foundation
import Combine

/// Backend configuration service for dynamic app settings
/// Eliminates hardcoded values by fetching configuration from backend API
@available(iOS 18.0, macOS 14.0, *)
@MainActor
class BackendConfigService: ObservableObject {
    static let shared = BackendConfigService()
    
    // MARK: - Published Properties
    @Published var appConfig: AppConfig?
    @Published var featureFlags: FeatureFlags?
    @Published var themeConfig: ThemeConfig?
    @Published var voiceConfig: VoiceConfig?
    @Published var isLoading: Bool = false
    @Published var lastError: String?
    
    // MARK: - Configuration Models
    
    struct AppConfig: Codable {
        let appVersion: String
        let buildNumber: String
        let appName: String
        let onboardingMessage: String
        let supportEmail: String
        let docsUrl: String
        
        enum CodingKeys: String, CodingKey {
            case appVersion = "app_version"
            case buildNumber = "build_number"
            case appName = "app_name"
            case onboardingMessage = "onboarding_message"
            case supportEmail = "support_email"
            case docsUrl = "docs_url"
        }
    }
    
    struct FeatureFlags: Codable {
        let voiceFeatures: Bool
        let wakePhraseDetection: Bool
        let voiceRecognition: Bool
        let betaFeedback: Bool
        let betaAnalytics: Bool
        let advancedSettings: Bool
        let debugSettings: Bool
        let networkDiagnostics: Bool
        let performanceMonitoring: Bool
        let documentIntelligence: Bool
        let codeCompletion: Bool
        let architectureAnalysis: Bool
        let realTimeSync: Bool
        
        enum CodingKeys: String, CodingKey {
            case voiceFeatures = "voice_features"
            case wakePhraseDetection = "wake_phrase_detection"
            case voiceRecognition = "voice_recognition"
            case betaFeedback = "beta_feedback"
            case betaAnalytics = "beta_analytics"
            case advancedSettings = "advanced_settings"
            case debugSettings = "debug_settings"
            case networkDiagnostics = "network_diagnostics"
            case performanceMonitoring = "performance_monitoring"
            case documentIntelligence = "document_intelligence"
            case codeCompletion = "code_completion"
            case architectureAnalysis = "architecture_analysis"
            case realTimeSync = "real_time_sync"
        }
    }
    
    struct ThemeConfig: Codable {
        let primaryColor: String
        let secondaryColor: String
        let successColor: String
        let errorColor: String
        let warningColor: String
        let languageColors: [String: String]
        
        enum CodingKeys: String, CodingKey {
            case primaryColor = "primary_color"
            case secondaryColor = "secondary_color"
            case successColor = "success_color"
            case errorColor = "error_color"
            case warningColor = "warning_color"
            case languageColors = "language_colors"
        }
    }
    
    struct VoiceConfig: Codable {
        let defaultWakePhrase: String
        let wakePhraseText: String
        let voiceTimeoutSeconds: Int
        let speechRecognitionLanguage: String
        let quickCommands: [String]
        let commandTemplates: [String: String]
        
        enum CodingKeys: String, CodingKey {
            case defaultWakePhrase = "default_wake_phrase"
            case wakePhraseText = "wake_phrase_sensitivity"
            case voiceTimeoutSeconds = "voice_timeout_seconds"
            case speechRecognitionLanguage = "speech_recognition_language"
            case quickCommands = "quick_commands"
            case commandTemplates = "command_templates"
        }
    }
    
    // MARK: - Private Properties
    private let userId: String = "default" // For now, use default user
    private var cancellables = Set<AnyCancellable>()
    
    private init() {
        // Auto-load configuration on init
        Task {
            await loadConfiguration()
        }
    }
    
    // MARK: - Public Methods
    
    /// Load complete configuration from backend
    func loadConfiguration() async {
        isLoading = true
        lastError = nil
        
        do {
            // Load all configuration components
            async let appTask = fetchAppConfig()
            async let featuresTask = fetchFeatureFlags()
            async let themeTask = fetchThemeConfig()
            async let voiceTask = fetchVoiceConfig()
            
            let (app, features, theme, voice) = try await (appTask, featuresTask, themeTask, voiceTask)
            
            await MainActor.run {
                self.appConfig = app
                self.featureFlags = features
                self.themeConfig = theme
                self.voiceConfig = voice
                self.isLoading = false
            }
            
            print("✅ Backend configuration loaded successfully")
            
        } catch {
            await MainActor.run {
                self.lastError = "Failed to load configuration: \\(error.localizedDescription)"
                self.isLoading = false
            }
            print("❌ Failed to load backend configuration: \\(error)")
        }
    }
    
    /// Get app version from backend or fallback to default
    var appVersion: String {
        return appConfig?.appVersion ?? "0.2.0"
    }
    
    /// Get onboarding message from backend or fallback to default
    var onboardingMessage: String {
        return appConfig?.onboardingMessage ?? "Connect to your LeanVibe agent to start coding"
    }
    
    /// Check if a feature is enabled
    func isFeatureEnabled(_ feature: Feature) -> Bool {
        guard let flags = featureFlags else { return feature.defaultValue }
        
        switch feature {
        case .voiceFeatures: return flags.voiceFeatures
        case .wakePhraseDetection: return flags.wakePhraseDetection
        case .voiceRecognition: return flags.voiceRecognition
        case .betaFeedback: return flags.betaFeedback
        case .betaAnalytics: return flags.betaAnalytics
        case .advancedSettings: return flags.advancedSettings
        case .debugSettings: return flags.debugSettings
        case .networkDiagnostics: return flags.networkDiagnostics
        case .performanceMonitoring: return flags.performanceMonitoring
        case .documentIntelligence: return flags.documentIntelligence
        case .codeCompletion: return flags.codeCompletion
        case .architectureAnalysis: return flags.architectureAnalysis
        case .realTimeSync: return flags.realTimeSync
        }
    }
    
    /// Get color for programming language
    func colorForLanguage(_ language: String) -> String {
        return themeConfig?.languageColors[language.lowercased()] ?? "#8E8E93"
    }
    
    /// Get quick voice commands
    var quickVoiceCommands: [String] {
        return voiceConfig?.quickCommands ?? [
            "Show project status",
            "List current tasks",
            "Open project dashboard"
        ]
    }
    
    // MARK: - Private Network Methods
    
    private func fetchAppConfig() async throws -> AppConfig {
        let url = URL(string: "\\(AppConfiguration.shared.apiBaseURL)/api/v1/config/app?user_id=\\(userId)")!
        let (data, _) = try await URLSession.shared.data(from: url)
        return try JSONDecoder().decode(AppConfig.self, from: data)
    }
    
    private func fetchFeatureFlags() async throws -> FeatureFlags {
        let url = URL(string: "\\(AppConfiguration.shared.apiBaseURL)/api/v1/config/features?user_id=\\(userId)")!
        let (data, _) = try await URLSession.shared.data(from: url)
        return try JSONDecoder().decode(FeatureFlags.self, from: data)
    }
    
    private func fetchThemeConfig() async throws -> ThemeConfig {
        let url = URL(string: "\\(AppConfiguration.shared.apiBaseURL)/api/v1/config/theme?user_id=\\(userId)")!
        let (data, _) = try await URLSession.shared.data(from: url)
        return try JSONDecoder().decode(ThemeConfig.self, from: data)
    }
    
    private func fetchVoiceConfig() async throws -> VoiceConfig {
        let url = URL(string: "\\(AppConfiguration.shared.apiBaseURL)/api/v1/config/voice?user_id=\\(userId)")!
        let (data, _) = try await URLSession.shared.data(from: url)
        return try JSONDecoder().decode(VoiceConfig.self, from: data)
    }
}

// MARK: - Feature Enum

enum Feature {
    case voiceFeatures
    case wakePhraseDetection
    case voiceRecognition
    case betaFeedback
    case betaAnalytics
    case advancedSettings
    case debugSettings
    case networkDiagnostics
    case performanceMonitoring
    case documentIntelligence
    case codeCompletion
    case architectureAnalysis
    case realTimeSync
    
    /// Default value if backend is unavailable
    var defaultValue: Bool {
        switch self {
        case .voiceFeatures, .voiceRecognition, .wakePhraseDetection: return true
        case .betaFeedback, .betaAnalytics: return true
        case .advancedSettings, .debugSettings: return true
        case .networkDiagnostics, .performanceMonitoring: return true
        case .codeCompletion, .architectureAnalysis: return true
        case .realTimeSync: return true
        case .documentIntelligence: return false // Coming soon
        }
    }
}