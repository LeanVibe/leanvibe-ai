import SwiftUI
import Foundation

@available(iOS 18.0, macOS 14.0, *)
@MainActor
class GlobalErrorManager: ObservableObject {
    static let shared = GlobalErrorManager()
    
    @Published var currentError: AppError?
    @Published var showingErrorAlert = false
    @Published var errorHistory: [AppError] = []
    
    private init() {}
    
    /// Display an error with automatic dismissal
    func showError(_ error: AppError) {
        currentError = error
        showingErrorAlert = true
        addToHistory(error)
        
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
    
    /// Display an error from a standard Error
    func showError(_ error: Error, context: String = "") {
        let appError = AppError.from(error, context: context)
        showError(appError)
    }
    
    /// Hide the current error
    func hideError() {
        currentError = nil
        showingErrorAlert = false
    }
    
    /// Clear error history
    func clearHistory() {
        errorHistory.removeAll()
    }
    
    private func addToHistory(_ error: AppError) {
        errorHistory.append(error)
        
        // Keep only last 50 errors
        if errorHistory.count > 50 {
            errorHistory.removeFirst(errorHistory.count - 50)
        }
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct AppError: Identifiable, Equatable {
    let id = UUID()
    let title: String
    let message: String
    let severity: ErrorSeverity
    let context: String
    let timestamp: Date
    let retryAction: (() -> Void)?
    let autoDismissDelay: TimeInterval
    
    init(
        title: String,
        message: String,
        severity: ErrorSeverity = .warning,
        context: String = "",
        retryAction: (() -> Void)? = nil,
        autoDismissDelay: TimeInterval = 5.0
    ) {
        self.title = title
        self.message = message
        self.severity = severity
        self.context = context
        self.timestamp = Date()
        self.retryAction = retryAction
        self.autoDismissDelay = autoDismissDelay
    }
    
    static func == (lhs: AppError, rhs: AppError) -> Bool {
        lhs.id == rhs.id
    }
    
    static func from(_ error: Error, context: String = "") -> AppError {
        if let taskError = error as? TaskServiceError {
            return AppError(
                title: "Task Operation Failed",
                message: taskError.localizedDescription,
                severity: .warning,
                context: context
            )
        } else if let networkError = error as? URLError {
            return AppError(
                title: "Network Error",
                message: networkError.localizedDescription,
                severity: .error,
                context: context
            )
        } else {
            return AppError(
                title: "Unexpected Error",
                message: error.localizedDescription,
                severity: .error,
                context: context
            )
        }
    }
}

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

// Note: TaskServiceError is defined in TaskService.swift