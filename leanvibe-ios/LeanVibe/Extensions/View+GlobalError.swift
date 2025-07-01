import SwiftUI

@available(iOS 18.0, macOS 14.0, *)
extension View {
    /// Adds global error handling to any view
    func withGlobalErrorHandling() -> some View {
        self.overlay(
            GlobalErrorView(errorManager: GlobalErrorManager.shared),
            alignment: .top
        )
    }
    
    /// Shows an error using the global error manager
    func showError(_ error: AppError) -> some View {
        self.onAppear {
            GlobalErrorManager.shared.showError(error)
        }
    }
    
    /// Shows an error from a standard Error using the global error manager
    func showError(_ error: Error, context: String = "") -> some View {
        self.onAppear {
            GlobalErrorManager.shared.showError(error, context: context)
        }
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct GlobalErrorModifier: ViewModifier {
    @ObservedObject private var errorManager = GlobalErrorManager.shared
    
    func body(content: Content) -> some View {
        content
            .overlay(
                GlobalErrorView(errorManager: errorManager),
                alignment: .top
            )
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct ErrorHandlingWrapper<Content: View>: View {
    let content: Content
    @ObservedObject private var errorManager = GlobalErrorManager.shared
    
    init(@ViewBuilder content: () -> Content) {
        self.content = content()
    }
    
    var body: some View {
        ZStack {
            content
            
            GlobalErrorView(errorManager: errorManager)
        }
    }
}

// Helper functions for common error scenarios
@available(iOS 18.0, macOS 14.0, *)
extension GlobalErrorManager {
    
    /// Show a network error with retry functionality
    func showNetworkError(retryAction: @escaping () -> Void) {
        let error = AppError(
            title: "Network Error",
            message: "Unable to connect to the server. Please check your internet connection and try again.",
            severity: .error,
            context: "Network operation",
            retryAction: retryAction
        )
        showError(error)
    }
    
    /// Show a validation error
    func showValidationError(_ message: String) {
        let error = AppError(
            title: "Validation Error",
            message: message,
            severity: .warning,
            context: "User input validation"
        )
        showError(error)
    }
    
    /// Show a success message
    func showSuccess(_ message: String) {
        let error = AppError(
            title: "Success",
            message: message,
            severity: .info,
            context: "Operation completed",
            autoDismissDelay: 3.0
        )
        showError(error)
    }
    
    /// Show a critical error that requires immediate attention
    func showCriticalError(_ message: String) {
        let error = AppError(
            title: "Critical Error",
            message: message,
            severity: .critical,
            context: "System error",
            autoDismissDelay: 0 // No auto-dismiss for critical errors
        )
        showError(error)
    }
    
    /// Show a network error with automatic retry functionality
    func showNetworkError<T>(
        operation: @escaping () async throws -> T,
        context: String = "Network operation",
        onSuccess: @escaping (T) -> Void = { _ in },
        onFailure: @escaping (Error) -> Void = { _ in }
    ) {
        let retryAction = RetryManager.shared.createRetryAction(
            operation: operation,
            maxAttempts: 3,
            backoffStrategy: .exponential(base: 1.0, multiplier: 2.0),
            context: context,
            onSuccess: onSuccess,
            onFailure: onFailure
        )
        
        let error = AppError(
            title: "Network Error",
            message: "Unable to connect to the server. Tap 'Retry' to try again.",
            severity: .error,
            context: context,
            retryAction: retryAction
        )
        showError(error)
    }
    
    /// Show a task operation error with retry functionality
    func showTaskOperationError<T>(
        operation: @escaping () async throws -> T,
        context: String,
        onSuccess: @escaping (T) -> Void = { _ in },
        onFailure: @escaping (Error) -> Void = { _ in }
    ) {
        let retryAction = RetryManager.shared.createRetryAction(
            operation: operation,
            maxAttempts: 2,
            backoffStrategy: .fixed(1.0),
            context: context,
            onSuccess: onSuccess,
            onFailure: onFailure
        )
        
        let error = AppError(
            title: "Operation Failed",
            message: "The operation could not be completed. Tap 'Retry' to try again.",
            severity: .warning,
            context: context,
            retryAction: retryAction
        )
        showError(error)
    }
}