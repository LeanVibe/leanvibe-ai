import Foundation
import SwiftUI

/// Centralized feature flag management system for LeanVibe iOS app
/// Provides environment-aware feature gating, remote flag support, and debug controls
/// Ensures incomplete or experimental features are hidden from production users
@available(iOS 18.0, macOS 14.0, *)
final class FeatureFlagManager: ObservableObject {
    
    // MARK: - Singleton
    static let shared = FeatureFlagManager()
    
    // MARK: - Properties
    @Published var localFlags: [FeatureFlag: Bool] = [:]
    @Published var remoteFlags: [FeatureFlag: Bool] = [:]
    @Published var overrideFlags: [FeatureFlag: Bool] = [:]
    
    private let userDefaults = UserDefaults.standard
    private let flagPrefix = "LeanVibe_FeatureFlag_"
    private let overridePrefix = "LeanVibe_FeatureFlagOverride_"
    
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
    
    private var isProductionBuild: Bool {
        return !isDebugBuild && !isTestFlightBuild
    }
    
    // MARK: - Initialization
    private init() {
        loadLocalFlags()
        loadRemoteFlags()
        loadOverrideFlags()
        configureDefaultFlags()
    }
    
    // MARK: - Feature Flag Resolution
    
    /// Check if a feature is enabled, considering all flag sources
    /// Priority: 1. Override flags (debug) 2. Remote flags 3. Local flags 4. Default values
    func isFeatureEnabled(_ feature: FeatureFlag) -> Bool {
        // Priority 1: Override flags (debug builds only)
        if isDebugBuild, let override = overrideFlags[feature] {
            return override
        }
        
        // Priority 2: Remote flags (for A/B testing and emergency disables)
        if let remote = remoteFlags[feature] {
            return remote
        }
        
        // Priority 3: Local flags (user preferences)
        if let local = localFlags[feature] {
            return local
        }
        
        // Priority 4: Default values based on environment
        return getDefaultValue(for: feature)
    }
    
    /// Get default value for a feature based on current environment
    internal func getDefaultValue(for feature: FeatureFlag) -> Bool {
        switch feature {
        // Voice Features - Disabled by default due to stability issues
        case .voiceFeatures:
            return false
        case .voiceRecognition:
            return false
        case .voiceCommands:
            return false
        case .wakePhraseDetection:
            return false
            
        // Beta Features - Only enabled in debug builds
        case .betaAnalytics:
            return isDebugBuild
        case .betaFeedback:
            return isDebugBuild
        case .experimentalUI:
            return isDebugBuild
        case .advancedMetrics:
            return isDebugBuild
            
        // Performance Features - Enabled based on environment
        case .performanceMonitoring:
            return !isProductionBuild
        case .realTimePerformanceDashboard:
            return isDebugBuild
        case .animationPerformanceView:
            return isDebugBuild
        case .systemPerformanceView:
            return isDebugBuild
        case .voicePerformanceView:
            return isDebugBuild
            
        // Architecture Features - Limited availability
        case .architectureVisualization:
            return true
        case .advancedArchitectureFeatures:
            return !isProductionBuild
        case .diagramComparison:
            return !isProductionBuild
        case .architectureMetrics:
            return isDebugBuild
            
        // Kanban Features - Generally available
        case .kanbanBoard:
            return true
        case .advancedKanbanFeatures:
            return !isProductionBuild
        case .taskDependencyGraph:
            return !isProductionBuild
        case .taskStatistics:
            return !isProductionBuild
            
        // Settings Features - Selective availability
        case .advancedSettings:
            return !isProductionBuild
        case .debugSettings:
            return isDebugBuild
        case .networkDiagnostics:
            return !isProductionBuild
        case .syncSettings:
            return !isProductionBuild
            
        // Notification Features - Available but can be disabled
        case .pushNotifications:
            return true
        case .notificationAnalytics:
            return isDebugBuild
        case .campaignManagement:
            return isDebugBuild
            
        // Onboarding Features - Always available
        case .onboardingSystem:
            return true
        case .advancedOnboarding:
            return !isProductionBuild
        case .featureDiscovery:
            return !isProductionBuild
            
        // Production Features - Environment specific
        case .productionReadiness:
            return isDebugBuild
        case .qualityGates:
            return isDebugBuild
        case .buildValidation:
            return isDebugBuild
            
        // Connection Features - Always available
        case .websocketConnection:
            return true
        case .qrCodeScanning:
            return true
        case .backendConfiguration:
            return true
            
        // Code Completion Features - Available but can be disabled
        case .codeCompletion:
            return true
        case .documentIntelligence:
            return !isProductionBuild
        case .codeCompletionTesting:
            return isDebugBuild
        }
    }
    
    // MARK: - Feature Flag Management
    
    /// Set a local flag value (persisted to UserDefaults)
    func setLocalFlag(_ feature: FeatureFlag, enabled: Bool) {
        localFlags[feature] = enabled
        userDefaults.set(enabled, forKey: flagPrefix + feature.rawValue)
        objectWillChange.send()
    }
    
    /// Set an override flag value (debug builds only, not persisted)
    func setOverrideFlag(_ feature: FeatureFlag, enabled: Bool?) {
        guard isDebugBuild else { return }
        
        if let enabled = enabled {
            overrideFlags[feature] = enabled
            userDefaults.set(enabled, forKey: overridePrefix + feature.rawValue)
        } else {
            overrideFlags.removeValue(forKey: feature)
            userDefaults.removeObject(forKey: overridePrefix + feature.rawValue)
        }
        objectWillChange.send()
    }
    
    /// Update remote flags (from server or configuration)
    func updateRemoteFlags(_ flags: [FeatureFlag: Bool]) {
        remoteFlags = flags
        objectWillChange.send()
        
        // Log remote flag updates in debug builds
        if isDebugBuild {
            print("🚩 Remote flags updated: \(flags)")
        }
    }
    
    /// Emergency disable a feature (creates remote flag override)
    func emergencyDisableFeature(_ feature: FeatureFlag, reason: String) {
        remoteFlags[feature] = false
        
        // Log emergency disable
        let timestamp = Date()
        userDefaults.set(false, forKey: "EmergencyDisabled_\(feature.rawValue)")
        userDefaults.set(reason, forKey: "EmergencyDisableReason_\(feature.rawValue)")
        userDefaults.set(timestamp, forKey: "EmergencyDisableDate_\(feature.rawValue)")
        
        objectWillChange.send()
        
        print("🚨 EMERGENCY DISABLE: \(feature.rawValue) - \(reason)")
    }
    
    /// Clear emergency disable for a feature
    func clearEmergencyDisable(_ feature: FeatureFlag) {
        remoteFlags.removeValue(forKey: feature)
        
        userDefaults.removeObject(forKey: "EmergencyDisabled_\(feature.rawValue)")
        userDefaults.removeObject(forKey: "EmergencyDisableReason_\(feature.rawValue)")
        userDefaults.removeObject(forKey: "EmergencyDisableDate_\(feature.rawValue)")
        
        objectWillChange.send()
        
        print("✅ Emergency disable cleared for: \(feature.rawValue)")
    }
    
    /// Get emergency disable reason for a feature
    func getEmergencyDisableReason(_ feature: FeatureFlag) -> (reason: String?, date: Date?) {
        let reason = userDefaults.string(forKey: "EmergencyDisableReason_\(feature.rawValue)")
        let date = userDefaults.object(forKey: "EmergencyDisableDate_\(feature.rawValue)") as? Date
        return (reason, date)
    }
    
    // MARK: - Bulk Operations
    
    /// Enable all features for a category (debug builds only)
    func enableFeaturesForCategory(_ category: FeatureCategory, enabled: Bool = true) {
        guard isDebugBuild else { return }
        
        let features = FeatureFlag.allCases.filter { $0.category == category }
        for feature in features {
            setOverrideFlag(feature, enabled: enabled)
        }
    }
    
    /// Reset all feature flags to defaults
    func resetAllFeaturesToDefaults() {
        localFlags.removeAll()
        overrideFlags.removeAll()
        
        // Clear UserDefaults
        for feature in FeatureFlag.allCases {
            userDefaults.removeObject(forKey: flagPrefix + feature.rawValue)
            userDefaults.removeObject(forKey: overridePrefix + feature.rawValue)
        }
        
        objectWillChange.send()
    }
    
    /// Get all enabled features for current environment
    func getEnabledFeatures() -> [FeatureFlag] {
        return FeatureFlag.allCases.filter { isFeatureEnabled($0) }
    }
    
    /// Get feature status summary for debugging
    func getFeatureStatusSummary() -> FeatureStatusSummary {
        let allFeatures = FeatureFlag.allCases
        let enabledFeatures = allFeatures.filter { isFeatureEnabled($0) }
        let disabledFeatures = allFeatures.filter { !isFeatureEnabled($0) }
        let overriddenFeatures = allFeatures.filter { overrideFlags[$0] != nil }
        let remoteControlledFeatures = allFeatures.filter { remoteFlags[$0] != nil }
        
        return FeatureStatusSummary(
            totalFeatures: allFeatures.count,
            enabledFeatures: enabledFeatures.count,
            disabledFeatures: disabledFeatures.count,
            overriddenFeatures: overriddenFeatures.count,
            remoteControlledFeatures: remoteControlledFeatures.count,
            environment: getCurrentEnvironment()
        )
    }
    
    // MARK: - Private Methods
    
    private func loadLocalFlags() {
        for feature in FeatureFlag.allCases {
            if userDefaults.object(forKey: flagPrefix + feature.rawValue) != nil {
                localFlags[feature] = userDefaults.bool(forKey: flagPrefix + feature.rawValue)
            }
        }
    }
    
    private func loadRemoteFlags() {
        // In future versions, this would load from a remote configuration service
        // For now, remote flags are only set through emergency disable or API calls
    }
    
    private func loadOverrideFlags() {
        guard isDebugBuild else { return }
        
        for feature in FeatureFlag.allCases {
            if userDefaults.object(forKey: overridePrefix + feature.rawValue) != nil {
                overrideFlags[feature] = userDefaults.bool(forKey: overridePrefix + feature.rawValue)
            }
        }
    }
    
    private func configureDefaultFlags() {
        // Set any initial configuration based on environment
        if isDebugBuild {
            // In debug builds, enable certain features by default
            if localFlags[.performanceMonitoring] == nil {
                localFlags[.performanceMonitoring] = true
            }
        }
    }
    
    private func getCurrentEnvironment() -> Environment {
        if isDebugBuild {
            return .debug
        } else if isTestFlightBuild {
            return .testFlight
        } else {
            return .production
        }
    }
}

// MARK: - Feature Flag Definitions

/// All available feature flags in the LeanVibe app
enum FeatureFlag: String, CaseIterable, Identifiable {
    // Voice Features
    case voiceFeatures = "voice_features"
    case voiceRecognition = "voice_recognition"
    case voiceCommands = "voice_commands"
    case wakePhraseDetection = "wake_phrase_detection"
    
    // Beta Features
    case betaAnalytics = "beta_analytics"
    case betaFeedback = "beta_feedback"
    case experimentalUI = "experimental_ui"
    case advancedMetrics = "advanced_metrics"
    
    // Performance Features
    case performanceMonitoring = "performance_monitoring"
    case realTimePerformanceDashboard = "real_time_performance_dashboard"
    case animationPerformanceView = "animation_performance_view"
    case systemPerformanceView = "system_performance_view"
    case voicePerformanceView = "voice_performance_view"
    
    // Architecture Features
    case architectureVisualization = "architecture_visualization"
    case advancedArchitectureFeatures = "advanced_architecture_features"
    case diagramComparison = "diagram_comparison"
    case architectureMetrics = "architecture_metrics"
    
    // Kanban Features
    case kanbanBoard = "kanban_board"
    case advancedKanbanFeatures = "advanced_kanban_features"
    case taskDependencyGraph = "task_dependency_graph"
    case taskStatistics = "task_statistics"
    
    // Settings Features
    case advancedSettings = "advanced_settings"
    case debugSettings = "debug_settings"
    case networkDiagnostics = "network_diagnostics"
    case syncSettings = "sync_settings"
    
    // Notification Features
    case pushNotifications = "push_notifications"
    case notificationAnalytics = "notification_analytics"
    case campaignManagement = "campaign_management"
    
    // Onboarding Features
    case onboardingSystem = "onboarding_system"
    case advancedOnboarding = "advanced_onboarding"
    case featureDiscovery = "feature_discovery"
    
    // Production Features
    case productionReadiness = "production_readiness"
    case qualityGates = "quality_gates"
    case buildValidation = "build_validation"
    
    // Connection Features
    case websocketConnection = "websocket_connection"
    case qrCodeScanning = "qr_code_scanning"
    case backendConfiguration = "backend_configuration"
    
    // Code Completion Features
    case codeCompletion = "code_completion"
    case documentIntelligence = "document_intelligence"
    case codeCompletionTesting = "code_completion_testing"
    
    var id: String { rawValue }
    
    var displayName: String {
        switch self {
        case .voiceFeatures: return "Voice Features"
        case .voiceRecognition: return "Voice Recognition"
        case .voiceCommands: return "Voice Commands"
        case .wakePhraseDetection: return "Wake Phrase Detection"
        case .betaAnalytics: return "Beta Analytics"
        case .betaFeedback: return "Beta Feedback"
        case .experimentalUI: return "Experimental UI"
        case .advancedMetrics: return "Advanced Metrics"
        case .performanceMonitoring: return "Performance Monitoring"
        case .realTimePerformanceDashboard: return "Real-time Performance Dashboard"
        case .animationPerformanceView: return "Animation Performance View"
        case .systemPerformanceView: return "System Performance View"
        case .voicePerformanceView: return "Voice Performance View"
        case .architectureVisualization: return "Architecture Visualization"
        case .advancedArchitectureFeatures: return "Advanced Architecture Features"
        case .diagramComparison: return "Diagram Comparison"
        case .architectureMetrics: return "Architecture Metrics"
        case .kanbanBoard: return "Kanban Board"
        case .advancedKanbanFeatures: return "Advanced Kanban Features"
        case .taskDependencyGraph: return "Task Dependency Graph"
        case .taskStatistics: return "Task Statistics"
        case .advancedSettings: return "Advanced Settings"
        case .debugSettings: return "Debug Settings"
        case .networkDiagnostics: return "Network Diagnostics"
        case .syncSettings: return "Sync Settings"
        case .pushNotifications: return "Push Notifications"
        case .notificationAnalytics: return "Notification Analytics"
        case .campaignManagement: return "Campaign Management"
        case .onboardingSystem: return "Onboarding System"
        case .advancedOnboarding: return "Advanced Onboarding"
        case .featureDiscovery: return "Feature Discovery"
        case .productionReadiness: return "Production Readiness"
        case .qualityGates: return "Quality Gates"
        case .buildValidation: return "Build Validation"
        case .websocketConnection: return "WebSocket Connection"
        case .qrCodeScanning: return "QR Code Scanning"
        case .backendConfiguration: return "Backend Configuration"
        case .codeCompletion: return "Code Completion"
        case .documentIntelligence: return "Document Intelligence"
        case .codeCompletionTesting: return "Code Completion Testing"
        }
    }
    
    var description: String {
        switch self {
        case .voiceFeatures: return "Enable voice-powered features and interactions"
        case .voiceRecognition: return "Enable speech-to-text recognition"
        case .voiceCommands: return "Enable voice command processing"
        case .wakePhraseDetection: return "Enable wake phrase detection"
        case .betaAnalytics: return "Enable beta testing analytics and feedback collection"
        case .betaFeedback: return "Enable beta feedback submission"
        case .experimentalUI: return "Enable experimental UI components and designs"
        case .advancedMetrics: return "Enable advanced performance and usage metrics"
        case .performanceMonitoring: return "Enable performance monitoring and tracking"
        case .realTimePerformanceDashboard: return "Enable real-time performance dashboard"
        case .animationPerformanceView: return "Enable animation performance testing view"
        case .systemPerformanceView: return "Enable system performance monitoring view"
        case .voicePerformanceView: return "Enable voice performance testing view"
        case .architectureVisualization: return "Enable architecture diagram visualization"
        case .advancedArchitectureFeatures: return "Enable advanced architecture features"
        case .diagramComparison: return "Enable diagram comparison functionality"
        case .architectureMetrics: return "Enable architecture metrics and analysis"
        case .kanbanBoard: return "Enable kanban board for task management"
        case .advancedKanbanFeatures: return "Enable advanced kanban features"
        case .taskDependencyGraph: return "Enable task dependency graph visualization"
        case .taskStatistics: return "Enable task statistics and analytics"
        case .advancedSettings: return "Enable advanced settings and configuration"
        case .debugSettings: return "Enable debug settings and tools"
        case .networkDiagnostics: return "Enable network diagnostics and troubleshooting"
        case .syncSettings: return "Enable sync settings and configuration"
        case .pushNotifications: return "Enable push notifications"
        case .notificationAnalytics: return "Enable notification analytics"
        case .campaignManagement: return "Enable notification campaign management"
        case .onboardingSystem: return "Enable user onboarding system"
        case .advancedOnboarding: return "Enable advanced onboarding features"
        case .featureDiscovery: return "Enable feature discovery and tutorials"
        case .productionReadiness: return "Enable production readiness validation"
        case .qualityGates: return "Enable quality gates and validation"
        case .buildValidation: return "Enable build validation tools"
        case .websocketConnection: return "Enable WebSocket real-time connection"
        case .qrCodeScanning: return "Enable QR code scanning for configuration"
        case .backendConfiguration: return "Enable backend configuration"
        case .codeCompletion: return "Enable code completion features"
        case .documentIntelligence: return "Enable document intelligence features"
        case .codeCompletionTesting: return "Enable code completion testing interface"
        }
    }
    
    var category: FeatureCategory {
        switch self {
        case .voiceFeatures, .voiceRecognition, .voiceCommands, .wakePhraseDetection:
            return .voice
        case .betaAnalytics, .betaFeedback, .experimentalUI, .advancedMetrics:
            return .beta
        case .performanceMonitoring, .realTimePerformanceDashboard, .animationPerformanceView, .systemPerformanceView, .voicePerformanceView:
            return .performance
        case .architectureVisualization, .advancedArchitectureFeatures, .diagramComparison, .architectureMetrics:
            return .architecture
        case .kanbanBoard, .advancedKanbanFeatures, .taskDependencyGraph, .taskStatistics:
            return .kanban
        case .advancedSettings, .debugSettings, .networkDiagnostics, .syncSettings:
            return .settings
        case .pushNotifications, .notificationAnalytics, .campaignManagement:
            return .notifications
        case .onboardingSystem, .advancedOnboarding, .featureDiscovery:
            return .onboarding
        case .productionReadiness, .qualityGates, .buildValidation:
            return .production
        case .websocketConnection, .qrCodeScanning, .backendConfiguration:
            return .connection
        case .codeCompletion, .documentIntelligence, .codeCompletionTesting:
            return .codeCompletion
        }
    }
    
    var isExperimental: Bool {
        switch self {
        case .experimentalUI, .advancedMetrics, .diagramComparison, .taskDependencyGraph, .advancedKanbanFeatures, .documentIntelligence:
            return true
        default:
            return false
        }
    }
    
    var isBetaOnly: Bool {
        switch self {
        case .betaAnalytics, .betaFeedback, .debugSettings, .buildValidation, .codeCompletionTesting:
            return true
        default:
            return false
        }
    }
}

// MARK: - Feature Categories

enum FeatureCategory: String, CaseIterable {
    case voice = "voice"
    case beta = "beta"
    case performance = "performance"
    case architecture = "architecture"
    case kanban = "kanban"
    case settings = "settings"
    case notifications = "notifications"
    case onboarding = "onboarding"
    case production = "production"
    case connection = "connection"
    case codeCompletion = "code_completion"
    
    var displayName: String {
        switch self {
        case .voice: return "Voice & Speech"
        case .beta: return "Beta Testing"
        case .performance: return "Performance"
        case .architecture: return "Architecture"
        case .kanban: return "Task Management"
        case .settings: return "Settings"
        case .notifications: return "Notifications"
        case .onboarding: return "Onboarding"
        case .production: return "Production"
        case .connection: return "Connection"
        case .codeCompletion: return "Code Completion"
        }
    }
}

// MARK: - Supporting Types

enum AppEnvironment: String {
    case debug = "debug"
    case testFlight = "testflight"
    case production = "production"
}

struct FeatureStatusSummary {
    let totalFeatures: Int
    let enabledFeatures: Int
    let disabledFeatures: Int
    let overriddenFeatures: Int
    let remoteControlledFeatures: Int
    let environment: Environment
}

// MARK: - SwiftUI Integration

extension FeatureFlagManager {
    /// SwiftUI view modifier to conditionally show content based on feature flags
    func featureFlag<Content: View>(_ feature: FeatureFlag, @ViewBuilder content: () -> Content) -> some View {
        Group {
            if isFeatureEnabled(feature) {
                content()
            } else {
                EmptyView()
            }
        }
    }
}

// MARK: - View Modifier for Feature Flags

struct FeatureFlagModifier: ViewModifier {
    let feature: FeatureFlag
    let fallback: AnyView?
    
    @ObservedObject private var featureFlags = FeatureFlagManager.shared
    
    func body(content: Content) -> some View {
        if featureFlags.isFeatureEnabled(feature) {
            content
        } else if let fallback = fallback {
            fallback
        } else {
            EmptyView()
        }
    }
}

extension View {
    /// Conditionally show view based on feature flag
    func featureFlag(_ feature: FeatureFlag) -> some View {
        self.modifier(FeatureFlagModifier(feature: feature, fallback: nil))
    }
    
    /// Conditionally show view based on feature flag with fallback
    func featureFlag<Fallback: View>(_ feature: FeatureFlag, fallback: Fallback) -> some View {
        self.modifier(FeatureFlagModifier(feature: feature, fallback: AnyView(fallback)))
    }
}