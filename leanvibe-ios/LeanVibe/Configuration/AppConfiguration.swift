import Foundation

/// Global application configuration for LeanVibe iOS app
/// Handles environment-specific settings for development, staging, and production
@available(iOS 18.0, *)
struct AppConfiguration {
    static let shared = AppConfiguration()
    
    // MARK: - Environment Detection
    
    private var isDebugBuild: Bool {
        #if DEBUG
        return true
        #else
        return false
        #endif
    }
    
    private var isTestFlightBuild: Bool {
        guard let path = Bundle.main.appStoreReceiptURL?.path else { return false }
        return path.contains("sandboxReceipt")
    }
    
    // MARK: - API Configuration
    
    /// Base URL for the LeanVibe backend API
    var apiBaseURL: String {
        if let envURL = ProcessInfo.processInfo.environment["LEANVIBE_API_URL"] {
            return envURL
        }
        
        if let bundleURL = Bundle.main.object(forInfoDictionaryKey: "API_BASE_URL") as? String,
           !bundleURL.isEmpty {
            return bundleURL
        }
        
        // Environment-specific defaults
        if isDebugBuild {
            return "http://localhost:8001"  // Development server
        } else if isTestFlightBuild {
            return "https://staging-api.leanvibe.ai"  // Staging environment
        } else {
            return "https://api.leanvibe.ai"  // Production environment
        }
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
    
    // MARK: - Feature Flags
    
    /// Whether to enable debug logging
    var isLoggingEnabled: Bool {
        return isDebugBuild || 
               ProcessInfo.processInfo.environment["LEANVIBE_ENABLE_LOGGING"] == "true"
    }
    
    /// Whether to enable performance monitoring
    var isPerformanceMonitoringEnabled: Bool {
        return !isDebugBuild ||
               ProcessInfo.processInfo.environment["LEANVIBE_ENABLE_MONITORING"] == "true"
    }
    
    /// Whether to enable voice features
    /// DISABLED for now due to startup crashes - will re-enable with proper defensive programming
    var isVoiceEnabled: Bool {
        // Emergency disable mechanism - if voice features are causing crashes
        if UserDefaults.standard.bool(forKey: "LeanVibe_Emergency_Disable_Voice") {
            return false
        }
        
        // Environment override for testing
        if ProcessInfo.processInfo.environment["LEANVIBE_DISABLE_VOICE"] == "true" {
            return false
        }
        
        // Temporarily disabled due to startup crashes
        // Voice features can be re-enabled by setting LEANVIBE_ENABLE_VOICE=true
        if ProcessInfo.processInfo.environment["LEANVIBE_ENABLE_VOICE"] == "true" {
            return true
        }
        
        return false  // Disabled by default for stability
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
        return Bundle.main.object(forInfoDictionaryKey: "CODE_COMPLETION_ENABLED") as? Bool ?? true
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
        print("   API Base URL: \(apiBaseURL)")
        print("   WebSocket URL: \(webSocketURL)")
        print("   Logging: \(isLoggingEnabled)")
        print("   Analytics: \(isAnalyticsEnabled)")
        print("   Voice Features: \(isVoiceEnabled)")
        print("   Unified Voice Service: \(useUnifiedVoiceService)")
        print("   Voice Confidence Threshold: \(voiceConfidenceThreshold)")
        print("   Code Completion: \(isCodeCompletionEnabled)")
        print("   Network Timeout: \(networkTimeout)s")
        #endif
    }
}

// MARK: - Configuration Extensions

extension AppConfiguration {
    /// Validate that all required configuration is present
    func validateConfiguration() throws {
        guard !apiBaseURL.isEmpty else {
            throw ConfigurationError.missingAPIBaseURL
        }
        
        guard !webSocketURL.isEmpty else {
            throw ConfigurationError.missingWebSocketURL
        }
        
        // Validate URL format
        guard URL(string: apiBaseURL) != nil else {
            throw ConfigurationError.invalidAPIBaseURL(apiBaseURL)
        }
        
        guard URL(string: webSocketURL) != nil else {
            throw ConfigurationError.invalidWebSocketURL(webSocketURL)
        }
    }
}

// MARK: - Configuration Errors

enum ConfigurationError: LocalizedError {
    case missingAPIBaseURL
    case missingWebSocketURL
    case invalidAPIBaseURL(String)
    case invalidWebSocketURL(String)
    
    var errorDescription: String? {
        switch self {
        case .missingAPIBaseURL:
            return "API Base URL is not configured"
        case .missingWebSocketURL:
            return "WebSocket URL is not configured"
        case .invalidAPIBaseURL(let url):
            return "Invalid API Base URL: \(url)"
        case .invalidWebSocketURL(let url):
            return "Invalid WebSocket URL: \(url)"
        }
    }
}