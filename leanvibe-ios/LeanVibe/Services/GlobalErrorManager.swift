import SwiftUI
import Foundation


@available(iOS 18.0, macOS 14.0, *)
@MainActor
class GlobalErrorManager: ObservableObject {
    nonisolated static let shared = GlobalErrorManager()
    
    @Published var currentError: AppError?
    @Published var showingErrorAlert = false
    @Published var errorHistory: [AppError] = []
    @Published var networkStatus: NetworkStatus = .unknown
    @Published var serviceStatuses: [String: ServiceStatus] = [:]
    
    private var errorStats: [ErrorCategory: Int] = [:]
    private var isOfflineMode = false
    
    nonisolated private init() {}
    
    /// Display an error with automatic dismissal and categorization
    func showError(_ error: AppError) {
        currentError = error
        showingErrorAlert = true
        addToHistory(error)
        updateErrorStats(error.category)
        
        // Handle offline scenarios
        if error.category == .network && error.severity == .critical {
            enableOfflineMode()
        }
        
        // Auto-dismiss after delay for non-critical errors
        if error.severity != .critical {
            Task {
                try await Task.sleep(for: .seconds(error.autoDismissDelay))
                if currentError?.id == error.id {
                    hideError()
                }
            }
        }
    }
    
    /// Display an error from a standard Error with enhanced categorization
    func showError(_ error: Error, context: String = "", category: ErrorCategory? = nil) {
        let appError = AppError.from(error, context: context, category: category)
        showError(appError)
    }
    
    /// Show success message
    func showSuccess(_ message: String, autoDismiss: Bool = true) {
        let successError = AppError(
            title: "Success",
            message: message,
            severity: .info,
            category: .system,
            context: "success",
            autoDismissDelay: autoDismiss ? 3.0 : 0
        )
        showError(successError)
    }
    
    /// Show network status update
    func updateNetworkStatus(_ status: NetworkStatus) {
        networkStatus = status
        
        if status == .connected && isOfflineMode {
            disableOfflineMode()
            showSuccess("Connection restored", autoDismiss: true)
        }
    }
    
    /// Update service status
    func updateServiceStatus(_ serviceName: String, status: ServiceStatus) {
        serviceStatuses[serviceName] = status
        
        if status == .failed {
            let error = AppError(
                title: "Service Unavailable",
                message: "\(serviceName) is currently unavailable",
                severity: .warning,
                category: .service,
                context: serviceName
            )
            showError(error)
        }
    }
    
    /// Hide the current error
    func hideError() {
        currentError = nil
        showingErrorAlert = false
    }
    
    /// Clear error history
    func clearHistory() {
        errorHistory.removeAll()
        errorStats.removeAll()
    }
    
    /// Get error statistics
    func getErrorStats() -> [ErrorCategory: Int] {
        return errorStats
    }
    
    /// Check if in offline mode
    func isInOfflineMode() -> Bool {
        return isOfflineMode
    }
    
    private func addToHistory(_ error: AppError) {
        errorHistory.append(error)
        
        // Keep only last 100 errors for better debugging
        if errorHistory.count > 100 {
            errorHistory.removeFirst(errorHistory.count - 100)
        }
    }
    
    private func updateErrorStats(_ category: ErrorCategory) {
        errorStats[category, default: 0] += 1
    }
    
    func enableOfflineMode() {
        isOfflineMode = true
        NotificationCenter.default.post(name: .offlineModeEnabled, object: nil)
    }
    
    private func disableOfflineMode() {
        isOfflineMode = false
        NotificationCenter.default.post(name: .offlineModeDisabled, object: nil)
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct AppError: Identifiable, Equatable {
    let id = UUID()
    let title: String
    let message: String
    let severity: ErrorSeverity
    let category: ErrorCategory
    let context: String
    let timestamp: Date
    let retryAction: (() -> Void)?
    let autoDismissDelay: TimeInterval
    let userFacingMessage: String
    let technicalDetails: String?
    let suggestedActions: [ErrorAction]
    
    init(
        title: String,
        message: String,
        severity: ErrorSeverity = .warning,
        category: ErrorCategory = .system,
        context: String = "",
        retryAction: (() -> Void)? = nil,
        autoDismissDelay: TimeInterval = 5.0,
        userFacingMessage: String? = nil,
        technicalDetails: String? = nil,
        suggestedActions: [ErrorAction] = []
    ) {
        self.title = title
        self.message = message
        self.severity = severity
        self.category = category
        self.context = context
        self.timestamp = Date()
        self.retryAction = retryAction
        self.autoDismissDelay = autoDismissDelay
        self.userFacingMessage = userFacingMessage ?? message
        self.technicalDetails = technicalDetails
        self.suggestedActions = suggestedActions.isEmpty ? ErrorAction.defaultActions(for: category) : suggestedActions
    }
    
    static func == (lhs: AppError, rhs: AppError) -> Bool {
        lhs.id == rhs.id
    }
    
    static func from(_ error: Error, context: String = "", category: ErrorCategory? = nil) -> AppError {
        let determinedCategory = category ?? ErrorCategory.from(error)
        
        switch error {
        case let taskError as TaskServiceError:
            return AppError(
                title: "Task Operation Failed",
                message: taskError.localizedDescription,
                severity: taskError.severity,
                category: determinedCategory,
                context: context,
                userFacingMessage: taskError.userFacingMessage,
                technicalDetails: taskError.technicalDetails
            )
        case let networkError as URLError:
            return AppError(
                title: networkError.isConnectivityError ? "Connection Lost" : "Network Error",
                message: networkError.localizedDescription,
                severity: networkError.isConnectivityError ? .critical : .error,
                category: .network,
                context: context,
                userFacingMessage: networkError.userFacingMessage,
                technicalDetails: "URL Error Code: \(networkError.code.rawValue)"
            )
        case let serviceError as BackendSettingsError:
            return AppError(
                title: "Settings Sync Failed",
                message: serviceError.localizedDescription,
                severity: .warning,
                category: .service,
                context: context,
                userFacingMessage: serviceError.localizedDescription
            )
        default:
            return AppError(
                title: "Unexpected Error",
                message: error.localizedDescription,
                severity: .error,
                category: determinedCategory,
                context: context,
                userFacingMessage: "Something went wrong. Please try again.",
                technicalDetails: "\(type(of: error)): \(error.localizedDescription)"
            )
        }
    }
}

@available(iOS 18.0, macOS 14.0, *)
enum ErrorSeverity {
    case info
    case warning
    case error
    case critical
    
    var color: Color {
        switch self {
        case .info: return .blue
        case .warning: return .orange
        case .error: return .red
        case .critical: return .red
        }
    }
    
    var systemImage: String {
        switch self {
        case .info: return "info.circle.fill"
        case .warning: return "exclamationmark.triangle.fill"
        case .error: return "xmark.circle.fill"
        case .critical: return "exclamationmark.octagon.fill"
        }
    }
}

// MARK: - Error Categories and Supporting Types

@available(iOS 18.0, macOS 14.0, *)
enum ErrorCategory: String, CaseIterable, Codable {
    case network = "network"
    case service = "service"
    case data = "data"
    case ui = "ui"
    case system = "system"
    case permission = "permission"
    case validation = "validation"
    
    var displayName: String {
        switch self {
        case .network: return "Network"
        case .service: return "Service"
        case .data: return "Data"
        case .ui: return "Interface"
        case .system: return "System"
        case .permission: return "Permission"
        case .validation: return "Validation"
        }
    }
    
    var systemImage: String {
        switch self {
        case .network: return "wifi.exclamationmark"
        case .service: return "server.rack"
        case .data: return "cylinder.split.1x2"
        case .ui: return "display.trianglebadge.exclamationmark"
        case .system: return "gear.badge.xmark"
        case .permission: return "lock.shield"
        case .validation: return "checkmark.shield"
        }
    }
    
    static func from(_ error: Error) -> ErrorCategory {
        switch error {
        case is URLError:
            return .network
        case is TaskServiceError:
            return .service
        case is BackendSettingsError:
            return .service
        case is DecodingError, is EncodingError:
            return .data
        default:
            return .system
        }
    }
}

@available(iOS 18.0, macOS 14.0, *)
enum NetworkStatus: String, CaseIterable {
    case connected = "connected"
    case disconnected = "disconnected"
    case slow = "slow"
    case unknown = "unknown"
    
    var color: Color {
        switch self {
        case .connected: return .green
        case .disconnected: return .red
        case .slow: return .orange
        case .unknown: return .gray
        }
    }
    
    var systemImage: String {
        switch self {
        case .connected: return "wifi"
        case .disconnected: return "wifi.slash"
        case .slow: return "wifi.exclamationmark"
        case .unknown: return "questionmark.circle"
        }
    }
}

@available(iOS 18.0, macOS 14.0, *)
enum ServiceStatus: String, CaseIterable {
    case healthy = "healthy"
    case degraded = "degraded"
    case failed = "failed"
    case unknown = "unknown"
    
    var color: Color {
        switch self {
        case .healthy: return .green
        case .degraded: return .orange
        case .failed: return .red
        case .unknown: return .gray
        }
    }
    
    var systemImage: String {
        switch self {
        case .healthy: return "checkmark.circle.fill"
        case .degraded: return "exclamationmark.triangle.fill"
        case .failed: return "xmark.circle.fill"
        case .unknown: return "questionmark.circle.fill"
        }
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct ErrorAction: Identifiable, Equatable {
    let id = UUID()
    let title: String
    let systemImage: String
    let action: () -> Void
    let isPrimary: Bool
    
    init(title: String, systemImage: String, isPrimary: Bool = false, action: @escaping () -> Void) {
        self.title = title
        self.systemImage = systemImage
        self.isPrimary = isPrimary
        self.action = action
    }
    
    static func == (lhs: ErrorAction, rhs: ErrorAction) -> Bool {
        lhs.id == rhs.id
    }
    
    static func defaultActions(for category: ErrorCategory) -> [ErrorAction] {
        switch category {
        case .network:
            return [
                ErrorAction(title: "Retry", systemImage: "arrow.clockwise", isPrimary: true) {
                    // Default retry action
                },
                ErrorAction(title: "Go Offline", systemImage: "wifi.slash") {
                    Task { @MainActor in
                        GlobalErrorManager.shared.enableOfflineMode()
                    }
                }
            ]
        case .service:
            return [
                ErrorAction(title: "Retry", systemImage: "arrow.clockwise", isPrimary: true) {
                    // Default retry action
                },
                ErrorAction(title: "Use Local Data", systemImage: "internaldrive") {
                    // Switch to local fallback
                }
            ]
        case .data:
            return [
                ErrorAction(title: "Refresh", systemImage: "arrow.clockwise", isPrimary: true) {
                    // Default refresh action
                }
            ]
        case .ui:
            return [
                ErrorAction(title: "Dismiss", systemImage: "xmark", isPrimary: true) {
                    Task { @MainActor in
                        GlobalErrorManager.shared.hideError()
                    }
                }
            ]
        case .system, .permission, .validation:
            return [
                ErrorAction(title: "OK", systemImage: "checkmark", isPrimary: true) {
                    Task { @MainActor in
                        GlobalErrorManager.shared.hideError()
                    }
                }
            ]
        }
    }
}

// MARK: - Notification Extensions

extension Notification.Name {
    static let offlineModeEnabled = Notification.Name("offlineModeEnabled")
    static let offlineModeDisabled = Notification.Name("offlineModeDisabled")
}

// MARK: - Error Extensions

extension URLError {
    var isConnectivityError: Bool {
        [.notConnectedToInternet, .networkConnectionLost, .cannotConnectToHost, .timedOut].contains(code)
    }
    
    var userFacingMessage: String {
        switch code {
        case .notConnectedToInternet:
            return "No internet connection. Please check your network settings."
        case .networkConnectionLost:
            return "Connection was lost. Trying to reconnect..."
        case .cannotConnectToHost:
            return "Cannot reach the server. Please try again later."
        case .timedOut:
            return "Request timed out. Please check your connection."
        default:
            return "Network error occurred. Please try again."
        }
    }
}

extension TaskServiceError {
    var severity: ErrorSeverity {
        switch self {
        case .unauthorized:
            return .critical
        case .networkFailure:
            return .error
        case .taskNotFound, .invalidTaskData:
            return .warning
        default:
            return .error
        }
    }
    
    var userFacingMessage: String {
        switch self {
        case .unauthorized:
            return "You don't have permission to perform this action."
        case .networkFailure:
            return "Unable to connect to the server. Your changes have been saved locally."
        case .taskNotFound:
            return "This task could not be found. It may have been deleted."
        case .invalidTaskData(let message):
            return message
        default:
            return "Task operation failed. Please try again."
        }
    }
    
    var technicalDetails: String {
        return "TaskServiceError.\(self)"
    }
}


// Note: Additional service errors would have similar extensions