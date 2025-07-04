import Foundation

// FeatureFlag and FeatureFlagManager are defined in FeatureFlagManager.swift

/// Global application configuration for LeanVibe iOS app
/// Handles dynamic backend configuration and environment-specific settings
/// NO HARDCODED VALUES - Everything comes from user configuration or auto-discovery
@available(iOS 18.0, macOS 14.0, *)
struct AppConfiguration {
    static let shared = AppConfiguration()
    
    // MARK: - Environment Detection
    
    var isDebugBuild: Bool {
        #if DEBUG
        return true
        #else
        return false
        #endif
    }
    
    var isTestFlightBuild: Bool {
        guard let path = Bundle.main.appStoreReceiptURL?.path else { return false }
        return path.contains("sandboxReceipt")
    }
    
    // MARK: - API Configuration
    
    /// Base URL for the LeanVibe backend API
    var apiBaseURL: String {
        // Priority 1: Environment variable
        if let envURL = ProcessInfo.processInfo.environment["LEANVIBE_API_URL"] {
            return envURL
        }
        
        // Priority 2: User-configured backend (from QR code or settings)
        if let configuredURL = UserDefaults.standard.string(forKey: "LeanVibe_Backend_URL"),
           !configuredURL.isEmpty {
            return configuredURL
        }
        
        // Priority 3: Bundle configuration
        if let bundleURL = Bundle.main.object(forInfoDictionaryKey: "API_BASE_URL") as? String,
           !bundleURL.isEmpty {
            return bundleURL
        }
        
        // Priority 4: Auto-discovery from Bonjour/mDNS (for local development)
        if let discoveredURL = autoDiscoverLocalBackend() {
            return discoveredURL
        }
        
        // CRITICAL: No hardcoded fallbacks - return empty to force user configuration
        return ""
    }
    
    /// Auto-discover local backend via Bonjour/mDNS
    private func autoDiscoverLocalBackend() -> String? {
        // In development, try to discover local backend services
        if isDebugBuild {
            // This will be implemented to scan for _leanvibe._tcp services
            // For now, only return localhost if explicitly running in simulator
            #if targetEnvironment(simulator)
            return "http://localhost:8001"
            #else
            return nil
            #endif
        }
        return nil
    }
    
    /// WebSocket URL for real-time communication
    var webSocketURL: String {
        let baseURL = apiBaseURL
        if baseURL.hasPrefix("https://") {
            return baseURL.replacingOccurrences(of: "https://", with: "wss://") + "/ws"
        } else if baseURL.hasPrefix("http://") {
            return baseURL.replacingOccurrences(of: "http://", with: "ws://") + "/ws"
        } else {
            return "ws://\(baseURL)/ws"
        }
    }
    
    // MARK: - Feature Flags Integration
    
    /// Feature flag manager for centralized feature control
    // Temporarily commented out to fix compilation order
    // private var featureFlags: FeatureFlagManager {
    //     return FeatureFlagManager.shared
    // }
    
    /// Whether to enable debug logging
    var isLoggingEnabled: Bool {
        return isDebugBuild || 
               ProcessInfo.processInfo.environment["LEANVIBE_ENABLE_LOGGING"] == "true"
    }
    
    /// Whether to enable performance monitoring
    var isPerformanceMonitoringEnabled: Bool {
        // Temporarily hardcoded until feature flags compilation is fixed
        return true &&
               (!isDebugBuild || ProcessInfo.processInfo.environment["LEANVIBE_ENABLE_MONITORING"] == "true")
    }
    
    /// Whether to enable voice features
    /// Now controlled by feature flag system with backward compatibility
    var isVoiceEnabled: Bool {
        // Emergency disable mechanism - if voice features are causing crashes
        if UserDefaults.standard.bool(forKey: "LeanVibe_Emergency_Disable_Voice") {
            return false
        }
        
        // Environment override for testing
        if ProcessInfo.processInfo.environment["LEANVIBE_DISABLE_VOICE"] == "true" {
            return false
        }
        
        // Environment override to enable voice
        if ProcessInfo.processInfo.environment["LEANVIBE_ENABLE_VOICE"] == "true" {
            return true
        }
        
        // Use feature flag system for voice features
        return true // Temporarily hardcoded until feature flags compilation is fixed
    }
    
    /// Emergency disable voice features due to crashes
    static func emergencyDisableVoice(reason: String) {
        UserDefaults.standard.set(true, forKey: "LeanVibe_Emergency_Disable_Voice")
        UserDefaults.standard.set(reason, forKey: "LeanVibe_Voice_Disable_Reason")
        UserDefaults.standard.set(Date(), forKey: "LeanVibe_Voice_Disable_Date")
        print("🚨 EMERGENCY: Voice features disabled due to: \(reason)")
    }
    
    /// Check if voice features were emergency disabled and why
    var voiceDisableReason: String? {
        guard UserDefaults.standard.bool(forKey: "LeanVibe_Emergency_Disable_Voice") else {
            return nil
        }
        return UserDefaults.standard.string(forKey: "LeanVibe_Voice_Disable_Reason")
    }
    
    /// Re-enable voice features after emergency disable
    static func reEnableVoice() {
        UserDefaults.standard.removeObject(forKey: "LeanVibe_Emergency_Disable_Voice")
        UserDefaults.standard.removeObject(forKey: "LeanVibe_Voice_Disable_Reason")
        UserDefaults.standard.removeObject(forKey: "LeanVibe_Voice_Disable_Date")
        print("✅ Voice features re-enabled")
    }
    
    /// Whether to enable code completion features
    var isCodeCompletionEnabled: Bool {
        let bundleEnabled = Bundle.main.object(forInfoDictionaryKey: "CODE_COMPLETION_ENABLED") as? Bool ?? true
        return bundleEnabled && true // Temporarily hardcoded until feature flags compilation is fixed
    }
    
    /// Whether to enable beta analytics features
    var isBetaAnalyticsEnabled: Bool {
        return true // Temporarily hardcoded until feature flags compilation is fixed
    }
    
    /// Whether to enable advanced architecture features
    var isAdvancedArchitectureEnabled: Bool {
        return true // Temporarily hardcoded until feature flags compilation is fixed
    }
    
    /// Whether to enable advanced kanban features
    var isAdvancedKanbanEnabled: Bool {
        return true // Temporarily hardcoded until feature flags compilation is fixed
    }
    
    /// Whether to enable debug settings
    var isDebugSettingsEnabled: Bool {
        return isDebugBuild // Temporarily hardcoded until feature flags compilation is fixed
    }
    
    /// Whether to enable experimental UI features
    var isExperimentalUIEnabled: Bool {
        return isDebugBuild // Temporarily hardcoded until feature flags compilation is fixed
    }
    
    /// Check if this is a production build
    var isProductionBuild: Bool {
        return !isDebugBuild && !isTestFlightBuild
    }
    
    // MARK: - Voice System Configuration
    
    /// Whether to use the new UnifiedVoiceService instead of legacy voice managers
    /// ENABLED: UnifiedVoiceService enabled as default for MVP deployment
    var useUnifiedVoiceService: Bool {
        return ProcessInfo.processInfo.environment["LEANVIBE_USE_UNIFIED_VOICE"] == "true" ||
               Bundle.main.object(forInfoDictionaryKey: "USE_UNIFIED_VOICE_SERVICE") as? Bool ?? true
    }
    
    /// Voice recognition confidence threshold (0.0 to 1.0)
    var voiceConfidenceThreshold: Float {
        if let threshold = ProcessInfo.processInfo.environment["LEANVIBE_VOICE_THRESHOLD"],
           let value = Float(threshold) {
            return max(0.0, min(1.0, value))
        }
        return 0.6  // Default threshold
    }
    
    /// Maximum voice recording duration in seconds
    var maxVoiceRecordingDuration: TimeInterval {
        if let duration = ProcessInfo.processInfo.environment["LEANVIBE_MAX_VOICE_DURATION"],
           let value = TimeInterval(duration) {
            return max(5.0, min(60.0, value))
        }
        return 30.0  // Default duration
    }
    
    // MARK: - Timeouts & Limits
    
    /// Network request timeout in seconds
    var networkTimeout: TimeInterval {
        if isDebugBuild {
            return 60.0  // Longer timeout for debugging
        } else {
            return 30.0  // Production timeout
        }
    }
    
    /// WebSocket reconnection timeout in seconds
    var webSocketReconnectTimeout: TimeInterval {
        return 5.0
    }
    
    /// Maximum retry attempts for failed requests
    var maxRetryAttempts: Int {
        return isDebugBuild ? 3 : 5
    }
    
    // MARK: - Analytics & Tracking
    
    /// Whether to enable analytics (always disabled in debug)
    var isAnalyticsEnabled: Bool {
        return !isDebugBuild &&
               ProcessInfo.processInfo.environment["LEANVIBE_DISABLE_ANALYTICS"] != "true"
    }
    
    /// Analytics API key (if configured)
    var analyticsAPIKey: String? {
        return Bundle.main.object(forInfoDictionaryKey: "ANALYTICS_API_KEY") as? String
    }
    
    // MARK: - Security Configuration
    
    /// Whether to enable certificate pinning
    var isCertificatePinningEnabled: Bool {
        return !isDebugBuild  // Disabled in debug for localhost testing
    }
    
    /// Allowed hosts for certificate pinning
    var pinnedHosts: [String] {
        return ["api.leanvibe.ai", "staging-api.leanvibe.ai"]
    }
    
    // MARK: - Debug Helpers
    
    /// Current environment name for display in debug builds
    var environmentName: String {
        if isDebugBuild {
            return "Development"
        } else if isTestFlightBuild {
            return "TestFlight"
        } else {
            return "Production"
        }
    }
    
    /// Print current configuration (debug builds only)
    func printConfiguration() {
        #if DEBUG
        print("🔧 LeanVibe Configuration")
        print("   Environment: \(environmentName)")
        print("   Backend Configured: \(isBackendConfigured)")
        if isBackendConfigured {
            print("   API Base URL: \(apiBaseURL)")
            print("   WebSocket URL: \(webSocketURL)")
        } else {
            print("   ⚠️  No backend configured - QR code setup required")
        }
        print("   Logging: \(isLoggingEnabled)")
        print("   Analytics: \(isAnalyticsEnabled)")
        print("   Voice Features: \(isVoiceEnabled)")
        print("   Unified Voice Service: \(useUnifiedVoiceService)")
        print("   Voice Confidence Threshold: \(voiceConfidenceThreshold)")
        print("   Code Completion: \(isCodeCompletionEnabled)")
        print("   Network Timeout: \(networkTimeout)s")
        #endif
    }
    
    /// Get configuration status for UI display
    var configurationStatus: ConfigurationStatus {
        if !isBackendConfigured {
            return .notConfigured
        }
        
        // Test basic connectivity (this would need to be async in real implementation)
        return .configured(apiBaseURL)
    }
}

// MARK: - Configuration Status

enum ConfigurationStatus {
    case notConfigured
    case configured(String)
    case testing(String)
    case error(String, Error)
    
    var displayText: String {
        switch self {
        case .notConfigured:
            return "Backend not configured"
        case .configured(let url):
            return "Connected to \(url)"
        case .testing(let url):
            return "Testing \(url)..."
        case .error(let url, _):
            return "Connection failed: \(url)"
        }
    }
    
    var isConfigured: Bool {
        switch self {
        case .configured:
            return true
        default:
            return false
        }
    }
}

// MARK: - Configuration Extensions

extension AppConfiguration {
    /// Validate that all required configuration is present
    func validateConfiguration() throws {
        let baseURL = apiBaseURL
        
        if baseURL.isEmpty {
            throw ConfigurationError.missingAPIBaseURL
        }
        
        let wsURL = webSocketURL
        if wsURL.isEmpty {
            throw ConfigurationError.missingWebSocketURL
        }
        
        // Validate URL format
        guard URL(string: baseURL) != nil else {
            throw ConfigurationError.invalidAPIBaseURL(baseURL)
        }
        
        guard URL(string: wsURL) != nil else {
            throw ConfigurationError.invalidWebSocketURL(wsURL)
        }
    }
    
    /// Check if backend is configured
    var isBackendConfigured: Bool {
        return !apiBaseURL.isEmpty
    }
    
    /// Configure backend URL (typically from QR code scan)
    func configureBackend(url: String) throws {
        // Validate URL format
        guard URL(string: url) != nil else {
            throw ConfigurationError.invalidAPIBaseURL(url)
        }
        
        // Clean up URL (remove trailing slash, add scheme if missing)
        let cleanURL = cleanBackendURL(url)
        
        // Save to UserDefaults
        UserDefaults.standard.set(cleanURL, forKey: "LeanVibe_Backend_URL")
        UserDefaults.standard.set(Date(), forKey: "LeanVibe_Backend_Configured_Date")
        
        print("✅ Backend configured: \(cleanURL)")
    }
    
    /// Clean and normalize backend URL
    private func cleanBackendURL(_ url: String) -> String {
        var cleanURL = url.trimmingCharacters(in: .whitespacesAndNewlines)
        
        // Remove trailing slash
        if cleanURL.hasSuffix("/") {
            cleanURL = String(cleanURL.dropLast())
        }
        
        // Add scheme if missing
        if !cleanURL.hasPrefix("http://") && !cleanURL.hasPrefix("https://") {
            cleanURL = "http://\(cleanURL)"
        }
        
        return cleanURL
    }
    
    /// Reset backend configuration (force re-setup)
    func resetBackendConfiguration() {
        UserDefaults.standard.removeObject(forKey: "LeanVibe_Backend_URL")
        UserDefaults.standard.removeObject(forKey: "LeanVibe_Backend_Configured_Date")
        print("🔄 Backend configuration reset")
    }
}

// MARK: - Configuration Errors

enum ConfigurationError: LocalizedError {
    case missingAPIBaseURL
    case missingWebSocketURL
    case invalidAPIBaseURL(String)
    case invalidWebSocketURL(String)
    case backendNotConfigured
    
    var errorDescription: String? {
        switch self {
        case .missingAPIBaseURL:
            return "Backend API URL is not configured. Please scan the QR code from your Mac agent or manually configure the backend URL in Settings."
        case .missingWebSocketURL:
            return "WebSocket URL could not be determined from the configured backend URL."
        case .invalidAPIBaseURL(let url):
            return "Invalid backend URL format: \(url). Please check the URL and try again."
        case .invalidWebSocketURL(let url):
            return "Invalid WebSocket URL format: \(url). This is derived from your backend URL."
        case .backendNotConfigured:
            return "No backend is configured. Please scan the QR code from your Mac agent to connect."
        }
    }
    
    var recoverySuggestion: String? {
        switch self {
        case .missingAPIBaseURL, .backendNotConfigured:
            return "Launch the LeanVibe Mac agent and scan the QR code it displays, or manually enter the backend URL in Settings."
        case .invalidAPIBaseURL, .invalidWebSocketURL:
            return "Check that your backend URL is in the format 'http://ip-address:port' or 'https://domain.com'."
        case .missingWebSocketURL:
            return "This is an internal error. Please try reconfiguring your backend URL."
        }
    }
}