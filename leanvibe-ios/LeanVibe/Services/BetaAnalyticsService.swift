import Foundation
import SwiftUI

/// Beta testing analytics service for capturing user feedback and usage patterns
/// Provides comprehensive insights for improving the app before App Store launch
@available(iOS 18.0, macOS 14.0, *)
final class BetaAnalyticsService: ObservableObject {
    
    // MARK: - Singleton
    static let shared = BetaAnalyticsService()
    
    // MARK: - Properties
    @Published var isEnabled: Bool = false
    @Published var feedbackQueue: [BetaFeedback] = []
    @Published var usageMetrics: [UsageMetric] = []
    @Published var crashReports: [CrashReport] = []
    
    private let userDefaults = UserDefaults.standard
    private let maxStoredEvents = 1000
    private let feedbackKey = "beta_feedback_events"
    private let usageKey = "beta_usage_metrics"
    private let crashKey = "beta_crash_reports"
    
    // MARK: - Initialization
    private init() {
        self.isEnabled = userDefaults.bool(forKey: "beta_analytics_enabled")
        loadStoredData()
    }
    
    // MARK: - Beta Feedback Management
    
    /// Record user feedback during beta testing
    func recordFeedback(
        type: BetaFeedbackType,
        screen: String,
        message: String,
        rating: Int? = nil,
        metadata: [String: Any]? = nil
    ) {
        guard isEnabled else { return }
        
        let feedback = BetaFeedback(
            id: UUID(),
            type: type,
            screen: screen,
            message: message,
            rating: rating,
            metadata: metadata,
            timestamp: Date(),
            appVersion: Bundle.main.appVersionLong
        )
        
        DispatchQueue.main.async {
            self.feedbackQueue.append(feedback)
            self.trimFeedbackIfNeeded()
            self.persistFeedback()
        }
    }
    
    /// Record general app usage metrics
    func recordUsageMetric(
        event: UsageEventType,
        screen: String,
        duration: TimeInterval? = nil,
        metadata: [String: Any]? = nil
    ) {
        guard isEnabled else { return }
        
        let metric = UsageMetric(
            id: UUID(),
            event: event,
            screen: screen,
            duration: duration,
            metadata: metadata,
            timestamp: Date(),
            appVersion: Bundle.main.appVersionLong
        )
        
        DispatchQueue.main.async {
            self.usageMetrics.append(metric)
            self.trimMetricsIfNeeded()
            self.persistUsageMetrics()
        }
    }
    
    /// Record crash or error information
    func recordCrash(
        error: Error,
        screen: String,
        context: String,
        stackTrace: String? = nil
    ) {
        let crashReport = CrashReport(
            id: UUID(),
            error: error.localizedDescription,
            screen: screen,
            context: context,
            stackTrace: stackTrace,
            timestamp: Date(),
            appVersion: Bundle.main.appVersionLong,
            deviceInfo: collectDeviceInfo()
        )
        
        DispatchQueue.main.async {
            self.crashReports.append(crashReport)
            self.trimCrashReportsIfNeeded()
            self.persistCrashReports()
        }
    }
    
    // MARK: - Beta Testing Specific Events
    
    /// Track which features are most used during beta
    func trackFeatureUsage(_ feature: String, screen: String) {
        recordUsageMetric(
            event: .featureUsed,
            screen: screen,
            metadata: ["feature": feature]
        )
    }
    
    /// Track user onboarding completion rate
    func trackOnboardingStep(_ step: String, completed: Bool) {
        recordUsageMetric(
            event: completed ? .onboardingCompleted : .onboardingAbandoned,
            screen: "onboarding",
            metadata: ["step": step]
        )
    }
    
    /// Track voice command success/failure rates
    func trackVoiceCommand(_ command: String, success: Bool, recognitionTime: TimeInterval?) {
        recordUsageMetric(
            event: success ? .voiceCommandSuccess : .voiceCommandFailure,
            screen: "voice",
            duration: recognitionTime,
            metadata: ["command": command]
        )
    }
    
    /// Track task creation and completion patterns
    func trackTaskInteraction(_ action: String, taskType: String, success: Bool) {
        recordUsageMetric(
            event: success ? .taskActionSuccess : .taskActionFailure,
            screen: "kanban",
            metadata: ["action": action, "taskType": taskType]
        )
    }
    
    /// Track backend connectivity issues
    func trackConnectivityIssue(_ issue: String, screen: String) {
        recordUsageMetric(
            event: .connectivityIssue,
            screen: screen,
            metadata: ["issue": issue]
        )
    }
    
    // MARK: - Data Export for TestFlight Feedback
    
    /// Generate comprehensive beta testing report
    func generateBetaReport() -> BetaTestingReport {
        let report = BetaTestingReport(
            generatedAt: Date(),
            appVersion: Bundle.main.appVersionLong,
            totalFeedbacks: feedbackQueue.count,
            totalUsageEvents: usageMetrics.count,
            totalCrashes: crashReports.count,
            feedbackSummary: generateFeedbackSummary(),
            usageSummary: generateUsageSummary(),
            crashSummary: generateCrashSummary(),
            recommendations: generateRecommendations()
        )
        
        return report
    }
    
    /// Export data for manual review or sending to development team
    func exportBetaDataAsJSON() -> String? {
        let exportData = BetaExportData(
            feedback: feedbackQueue,
            usage: usageMetrics,
            crashes: crashReports,
            exportedAt: Date()
        )
        
        do {
            let jsonData = try JSONEncoder().encode(exportData)
            return String(data: jsonData, encoding: .utf8)
        } catch {
            recordCrash(error: error, screen: "analytics", context: "export_failure")
            return nil
        }
    }
    
    // MARK: - Configuration
    
    /// Enable/disable beta analytics (GDPR compliant)
    func setAnalyticsEnabled(_ enabled: Bool) {
        isEnabled = enabled
        userDefaults.set(enabled, forKey: "beta_analytics_enabled")
        
        if !enabled {
            clearAllData()
        }
    }
    
    /// Clear all stored analytics data
    func clearAllData() {
        feedbackQueue.removeAll()
        usageMetrics.removeAll()
        crashReports.removeAll()
        
        userDefaults.removeObject(forKey: feedbackKey)
        userDefaults.removeObject(forKey: usageKey)
        userDefaults.removeObject(forKey: crashKey)
    }
    
    // MARK: - Private Methods
    
    private func loadStoredData() {
        loadFeedback()
        loadUsageMetrics()
        loadCrashReports()
    }
    
    private func loadFeedback() {
        if let data = userDefaults.data(forKey: feedbackKey),
           let feedback = try? JSONDecoder().decode([BetaFeedback].self, from: data) {
            self.feedbackQueue = feedback
        }
    }
    
    private func loadUsageMetrics() {
        if let data = userDefaults.data(forKey: usageKey),
           let metrics = try? JSONDecoder().decode([UsageMetric].self, from: data) {
            self.usageMetrics = metrics
        }
    }
    
    private func loadCrashReports() {
        if let data = userDefaults.data(forKey: crashKey),
           let crashes = try? JSONDecoder().decode([CrashReport].self, from: data) {
            self.crashReports = crashes
        }
    }
    
    private func persistFeedback() {
        if let data = try? JSONEncoder().encode(feedbackQueue) {
            userDefaults.set(data, forKey: feedbackKey)
        }
    }
    
    private func persistUsageMetrics() {
        if let data = try? JSONEncoder().encode(usageMetrics) {
            userDefaults.set(data, forKey: usageKey)
        }
    }
    
    private func persistCrashReports() {
        if let data = try? JSONEncoder().encode(crashReports) {
            userDefaults.set(data, forKey: crashKey)
        }
    }
    
    private func trimFeedbackIfNeeded() {
        if feedbackQueue.count > maxStoredEvents {
            feedbackQueue = Array(feedbackQueue.suffix(maxStoredEvents))
        }
    }
    
    private func trimMetricsIfNeeded() {
        if usageMetrics.count > maxStoredEvents {
            usageMetrics = Array(usageMetrics.suffix(maxStoredEvents))
        }
    }
    
    private func trimCrashReportsIfNeeded() {
        if crashReports.count > maxStoredEvents {
            crashReports = Array(crashReports.suffix(maxStoredEvents))
        }
    }
    
    private func collectDeviceInfo() -> DeviceInfo {
        return DeviceInfo(
            model: UIDevice.current.model,
            systemVersion: UIDevice.current.systemVersion,
            screenSize: UIScreen.main.bounds.size,
            memoryGB: ProcessInfo.processInfo.physicalMemory / (1024 * 1024 * 1024)
        )
    }
    
    private func generateFeedbackSummary() -> FeedbackSummary {
        let bugReports = feedbackQueue.filter { $0.type == .bug }.count
        let featureRequests = feedbackQueue.filter { $0.type == .featureRequest }.count
        let usabilityIssues = feedbackQueue.filter { $0.type == .usability }.count
        let generalFeedback = feedbackQueue.filter { $0.type == .general }.count
        
        let ratings = feedbackQueue.compactMap { $0.rating }
        let averageRating = ratings.isEmpty ? 0 : ratings.reduce(0, +) / ratings.count
        
        return FeedbackSummary(
            totalFeedbacks: feedbackQueue.count,
            bugReports: bugReports,
            featureRequests: featureRequests,
            usabilityIssues: usabilityIssues,
            generalFeedback: generalFeedback,
            averageRating: averageRating
        )
    }
    
    private func generateUsageSummary() -> UsageSummary {
        let screenViews = usageMetrics.filter { $0.event == .screenView }.count
        let featureUsages = usageMetrics.filter { $0.event == .featureUsed }.count
        let voiceCommands = usageMetrics.filter { $0.event == .voiceCommandSuccess || $0.event == .voiceCommandFailure }.count
        let taskActions = usageMetrics.filter { $0.event == .taskActionSuccess || $0.event == .taskActionFailure }.count
        
        let sessionsCount = Set(usageMetrics.map { Calendar.current.startOfDay(for: $0.timestamp) }).count
        
        return UsageSummary(
            totalEvents: usageMetrics.count,
            screenViews: screenViews,
            featureUsages: featureUsages,
            voiceCommands: voiceCommands,
            taskActions: taskActions,
            sessionsCount: sessionsCount
        )
    }
    
    private func generateCrashSummary() -> CrashSummary {
        let uniqueErrors = Set(crashReports.map { $0.error }).count
        let mostCommonScreen = crashReports.reduce(into: [:]) { counts, crash in
            counts[crash.screen, default: 0] += 1
        }.max(by: { $0.value < $1.value })?.key ?? "unknown"
        
        return CrashSummary(
            totalCrashes: crashReports.count,
            uniqueErrors: uniqueErrors,
            mostCommonScreen: mostCommonScreen
        )
    }
    
    private func generateRecommendations() -> [String] {
        var recommendations: [String] = []
        
        // Crash analysis
        if crashReports.count > 5 {
            recommendations.append("High crash rate detected - prioritize stability fixes")
        }
        
        // Feedback analysis
        let bugReports = feedbackQueue.filter { $0.type == .bug }.count
        if bugReports > feedbackQueue.count / 2 {
            recommendations.append("Many bug reports - focus on quality improvements")
        }
        
        // Usage analysis
        let voiceCommands = usageMetrics.filter { $0.event == .voiceCommandFailure }.count
        let totalVoice = usageMetrics.filter { $0.event == .voiceCommandSuccess || $0.event == .voiceCommandFailure }.count
        if totalVoice > 0 && voiceCommands > totalVoice / 2 {
            recommendations.append("Voice command failure rate high - improve speech recognition")
        }
        
        // Onboarding analysis
        let onboardingAbandoned = usageMetrics.filter { $0.event == .onboardingAbandoned }.count
        if onboardingAbandoned > 3 {
            recommendations.append("Users abandoning onboarding - simplify initial setup")
        }
        
        if recommendations.isEmpty {
            recommendations.append("Beta testing proceeding well - continue monitoring metrics")
        }
        
        return recommendations
    }
}

// MARK: - Data Models

struct BetaFeedback: Codable, Identifiable {
    let id: UUID
    let type: BetaFeedbackType
    let screen: String
    let message: String
    let rating: Int?
    let metadata: [String: String]?
    let timestamp: Date
    let appVersion: String
    
    init(id: UUID, type: BetaFeedbackType, screen: String, message: String, rating: Int?, metadata: [String: Any]?, timestamp: Date, appVersion: String) {
        self.id = id
        self.type = type
        self.screen = screen
        self.message = message
        self.rating = rating
        self.metadata = metadata?.compactMapValues { "\($0)" }
        self.timestamp = timestamp
        self.appVersion = appVersion
    }
}

enum BetaFeedbackType: String, Codable, CaseIterable {
    case bug = "bug"
    case featureRequest = "feature_request"
    case usability = "usability"
    case general = "general"
    case performance = "performance"
}

struct UsageMetric: Codable, Identifiable {
    let id: UUID
    let event: UsageEventType
    let screen: String
    let duration: TimeInterval?
    let metadata: [String: String]?
    let timestamp: Date
    let appVersion: String
    
    init(id: UUID, event: UsageEventType, screen: String, duration: TimeInterval?, metadata: [String: Any]?, timestamp: Date, appVersion: String) {
        self.id = id
        self.event = event
        self.screen = screen
        self.duration = duration
        self.metadata = metadata?.compactMapValues { "\($0)" }
        self.timestamp = timestamp
        self.appVersion = appVersion
    }
}

enum UsageEventType: String, Codable, CaseIterable {
    case screenView = "screen_view"
    case featureUsed = "feature_used"
    case onboardingCompleted = "onboarding_completed"
    case onboardingAbandoned = "onboarding_abandoned"
    case voiceCommandSuccess = "voice_command_success"
    case voiceCommandFailure = "voice_command_failure"
    case taskActionSuccess = "task_action_success"
    case taskActionFailure = "task_action_failure"
    case connectivityIssue = "connectivity_issue"
    case errorEncountered = "error_encountered"
}

struct CrashReport: Codable, Identifiable {
    let id: UUID
    let error: String
    let screen: String
    let context: String
    let stackTrace: String?
    let timestamp: Date
    let appVersion: String
    let deviceInfo: DeviceInfo
}

struct DeviceInfo: Codable {
    let model: String
    let systemVersion: String
    let screenSize: CGSize
    let memoryGB: UInt64
}

struct BetaTestingReport: Codable {
    let generatedAt: Date
    let appVersion: String
    let totalFeedbacks: Int
    let totalUsageEvents: Int
    let totalCrashes: Int
    let feedbackSummary: FeedbackSummary
    let usageSummary: UsageSummary
    let crashSummary: CrashSummary
    let recommendations: [String]
}

struct FeedbackSummary: Codable {
    let totalFeedbacks: Int
    let bugReports: Int
    let featureRequests: Int
    let usabilityIssues: Int
    let generalFeedback: Int
    let averageRating: Int
}

struct UsageSummary: Codable {
    let totalEvents: Int
    let screenViews: Int
    let featureUsages: Int
    let voiceCommands: Int
    let taskActions: Int
    let sessionsCount: Int
}

struct CrashSummary: Codable {
    let totalCrashes: Int
    let uniqueErrors: Int
    let mostCommonScreen: String
}

struct BetaExportData: Codable {
    let feedback: [BetaFeedback]
    let usage: [UsageMetric]
    let crashes: [CrashReport]
    let exportedAt: Date
}

// MARK: - Bundle Extension
extension Bundle {
    var appVersionLong: String {
        let version = infoDictionary?["CFBundleShortVersionString"] as? String ?? "Unknown"
        let build = infoDictionary?["CFBundleVersion"] as? String ?? "Unknown"
        return "\(version) (\(build))"
    }
}