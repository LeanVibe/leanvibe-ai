import Foundation
import SwiftUI

/// Integration examples and utilities for the comprehensive error handling system
/// This file provides examples of how to integrate the error handling system across the app

@available(iOS 18.0, macOS 14.0, *)
class ErrorHandlingIntegration {
    
    // MARK: - Integration Examples
    
    /// Example: Integrating error handling in a service method
    static func exampleServiceMethodWithErrorHandling() async {
        do {
            // Simulate a service operation that might fail
            try await performTaskOperation()
            
            // Show success message
            GlobalErrorManager.shared.showSuccess("Task completed successfully")
            
        } catch {
            // Categorize the error appropriately
            let category: ErrorCategory = {
                if error is URLError {
                    return .network
                } else if error is TaskServiceError {
                    return .service
                } else {
                    return .system
                }
            }()
            
            // Create comprehensive error with recovery actions
            let appError = AppError(
                title: "Task Operation Failed",
                message: error.localizedDescription,
                severity: .error,
                category: category,
                context: "task_operation",
                userFacingMessage: "Unable to complete the task. Please try again.",
                technicalDetails: "Error: \(type(of: error)) - \(error.localizedDescription)",
                suggestedActions: [
                    ErrorAction(title: "Retry", systemImage: "arrow.clockwise", isPrimary: true) {
                        Task {
                            await exampleServiceMethodWithErrorHandling()
                        }
                    },
                    ErrorAction(title: "Work Offline", systemImage: "wifi.slash") {
                        GlobalErrorManager.shared.enableOfflineMode()
                    }
                ]
            )
            
            // Show error to user
            GlobalErrorManager.shared.showError(appError)
            
            // Automatically attempt recovery for critical errors
            if category == .network || category == .service {
                await ErrorRecoveryManager.shared.attemptRecovery(for: appError)
            }
        }
    }
    
    /// Example: Network request with proper error handling
    static func exampleNetworkRequestWithErrorHandling(endpoint: String) async throws -> Data {
        do {
            guard let url = URL(string: endpoint) else {
                throw URLError(.badURL)
            }
            
            let (data, response) = try await URLSession.shared.data(from: url)
            
            guard let httpResponse = response as? HTTPURLResponse else {
                throw URLError(.badServerResponse)
            }
            
            guard 200...299 ~= httpResponse.statusCode else {
                throw URLError(.badServerResponse)
            }
            
            return data
            
        } catch {
            // Handle network errors with proper categorization
            if let urlError = error as? URLError {
                NetworkErrorHandler.shared.handleRESTAPIError(urlError, endpoint: endpoint, httpMethod: "GET")
            }
            
            throw error
        }
    }
    
    /// Example: WebSocket connection with error handling
    static func exampleWebSocketWithErrorHandling() {
        // This would be integrated into WebSocketService
        Task {
            do {
                // Simulate WebSocket connection attempt
                try await connectWebSocket()
                
            } catch {
                // Handle WebSocket-specific errors
                NetworkErrorHandler.shared.handleWebSocketError(error, endpoint: "/ws")
                
                // Attempt fallback to polling if WebSocket fails
                await ErrorRecoveryManager.shared.scheduleRetry({
                    try await connectWebSocket()
                }, for: AppError.from(error, context: "websocket_connection", category: .network), delay: 5.0)
            }
        }
    }
    
    /// Example: Service health monitoring integration
    static func integrateServiceHealthMonitoring() {
        // Register services for health monitoring
        let taskServiceConfig = ServiceConfiguration(
            healthEndpoint: "/api/tasks/health",
            criticalityLevel: .high,
            healthCheckInterval: 30.0,
            timeoutInterval: 10.0
        )
        
        ServiceErrorHandler.shared.registerService("TaskService", configuration: taskServiceConfig)
        
        // Listen for service status changes
        NotificationCenter.default.addObserver(
            forName: .taskServiceFallback,
            object: nil,
            queue: .main
        ) { _ in
            // Switch to local storage when task service fails
            enableLocalTaskStorage()
        }
    }
    
    /// Example: Retry mechanism with exponential backoff
    static func exampleRetryWithBackoff() async {
        let retryAction = RetryManager.shared.createRetryAction(
            operation: {
                try await performNetworkOperation()
            },
            maxAttempts: 3,
            backoffStrategy: .exponentialBackoff(baseDelay: 1.0, maxDelay: 30.0),
            context: "network_operation",
            category: .network,
            onSuccess: { result in
                print("Operation succeeded: \(result)")
            },
            onFailure: { error in
                print("Operation failed after retries: \(error)")
            }
        )
        
        retryAction()
    }
    
    // MARK: - Integration Utilities
    
    /// Setup error handling for the entire app
    static func setupAppWideErrorHandling() {
        // Initialize all error handlers
        _ = GlobalErrorManager.shared
        _ = NetworkErrorHandler.shared
        _ = ServiceErrorHandler.shared
        _ = ErrorRecoveryManager.shared
        
        // Setup global error handling for unhandled exceptions
        setupGlobalExceptionHandler()
        
        // Register for system notifications
        setupSystemNotificationHandlers()
    }
    
    /// Setup global exception handler
    private static func setupGlobalExceptionHandler() {
        // This would capture unhandled errors and route them through our system
        NSSetUncaughtExceptionHandler { exception in
            let error = AppError(
                title: "Unexpected Error",
                message: exception.reason ?? "An unexpected error occurred",
                severity: .critical,
                category: .system,
                context: "uncaught_exception",
                userFacingMessage: "The app encountered an unexpected error. Please restart the app.",
                technicalDetails: "Exception: \(exception.name) - \(exception.reason ?? "No reason")"
            )
            
            Task { @MainActor in
                GlobalErrorManager.shared.showError(error)
            }
        }
    }
    
    /// Setup system notification handlers
    private static func setupSystemNotificationHandlers() {
        // Memory pressure notifications
        NotificationCenter.default.addObserver(
            forName: UIApplication.didReceiveMemoryWarningNotification,
            object: nil,
            queue: .main
        ) { _ in
            let warning = AppError(
                title: "Memory Warning",
                message: "The app is using too much memory",
                severity: .warning,
                category: .system,
                context: "memory_pressure",
                userFacingMessage: "The app will free up memory to improve performance.",
                suggestedActions: [
                    ErrorAction(title: "Clear Cache", systemImage: "trash", isPrimary: true) {
                        NotificationCenter.default.post(name: .cleanupMemory, object: nil)
                    }
                ]
            )
            
            GlobalErrorManager.shared.showError(warning)
        }
        
        // Network status changes
        NotificationCenter.default.addObserver(
            forName: .networkLost,
            object: nil,
            queue: .main
        ) { _ in
            GlobalErrorManager.shared.enableOfflineMode()
        }
    }
    
    /// Create a standardized error for common scenarios
    static func createNetworkError(context: String, endpoint: String? = nil) -> AppError {
        return AppError(
            title: "Network Error",
            message: "Unable to connect to the server",
            severity: .error,
            category: .network,
            context: context,
            userFacingMessage: "Please check your internet connection and try again.",
            technicalDetails: endpoint.map { "Endpoint: \($0)" },
            suggestedActions: [
                ErrorAction(title: "Retry", systemImage: "arrow.clockwise", isPrimary: true) {
                    // Retry action would be provided by caller
                },
                ErrorAction(title: "Go Offline", systemImage: "wifi.slash") {
                    GlobalErrorManager.shared.enableOfflineMode()
                }
            ]
        )
    }
    
    /// Create a standardized error for service failures
    static func createServiceError(serviceName: String, context: String) -> AppError {
        return AppError(
            title: "\(serviceName) Unavailable",
            message: "\(serviceName) is currently not responding",
            severity: .warning,
            category: .service,
            context: context,
            userFacingMessage: "\(serviceName) is temporarily unavailable. Your data is safe.",
            technicalDetails: "Service: \(serviceName), Context: \(context)",
            suggestedActions: [
                ErrorAction(title: "Retry", systemImage: "arrow.clockwise", isPrimary: true) {
                    Task {
                        await ServiceErrorHandler.shared.retryService(serviceName)
                    }
                },
                ErrorAction(title: "Use Local Data", systemImage: "internaldrive") {
                    NotificationCenter.default.post(name: .enableLocalFallback, object: serviceName)
                }
            ]
        )
    }
    
    // MARK: - Mock Operations (for example purposes)
    
    private static func performTaskOperation() async throws {
        // Simulate network delay
        try await Task.sleep(for: .seconds(1))
        
        // Simulate random failure
        if Bool.random() {
            throw TaskServiceError.networkFailure
        }
    }
    
    private static func performNetworkOperation() async throws -> String {
        try await Task.sleep(for: .seconds(0.5))
        
        if Bool.random() {
            throw URLError(.timedOut)
        }
        
        return "Success"
    }
    
    private static func connectWebSocket() async throws {
        try await Task.sleep(for: .seconds(1))
        
        if Bool.random() {
            throw URLError(.cannotConnectToHost)
        }
    }
    
    private static func enableLocalTaskStorage() {
        // Implementation would switch TaskService to local-only mode
        print("Switched to local task storage")
    }
}

// MARK: - SwiftUI Integration Examples

@available(iOS 18.0, macOS 14.0, *)
struct ErrorHandlingExampleView: View {
    @ObservedObject private var errorManager = GlobalErrorManager.shared
    @ObservedObject private var networkHandler = NetworkErrorHandler.shared
    @ObservedObject private var serviceHandler = ServiceErrorHandler.shared
    
    var body: some View {
        VStack(spacing: 20) {
            // Network status indicator
            HStack {
                Image(systemName: networkHandler.networkStatus.systemImage)
                    .foregroundColor(networkHandler.networkStatus.color)
                
                Text("Network: \(networkHandler.networkStatus.rawValue)")
                    .font(.caption)
            }
            
            // Service status indicators
            ForEach(Array(serviceHandler.getAllServiceHealth().keys.sorted()), id: \.self) { serviceName in
                if let healthInfo = serviceHandler.getServiceHealth(serviceName) {
                    HStack {
                        Image(systemName: healthInfo.status.systemImage)
                            .foregroundColor(healthInfo.status.color)
                        
                        Text("\(serviceName): \(healthInfo.status.rawValue)")
                            .font(.caption)
                    }
                }
            }
            
            // Test buttons
            Button("Test Network Error") {
                Task {
                    await ErrorHandlingIntegration.exampleServiceMethodWithErrorHandling()
                }
            }
            .buttonStyle(.bordered)
            
            Button("Test Service Failure") {
                let error = ErrorHandlingIntegration.createServiceError(serviceName: "TestService", context: "manual_test")
                errorManager.showError(error)
            }
            .buttonStyle(.bordered)
            
            Button("Show System Health") {
                // This would navigate to SystemHealthDashboard
            }
            .buttonStyle(.borderedProminent)
        }
        .padding()
        .overlay(
            // Global error overlay
            GlobalErrorView(errorManager: errorManager)
        )
    }
}

// MARK: - Extension for Easy Integration

@available(iOS 18.0, macOS 14.0, *)
extension View {
    /// Add comprehensive error handling to any view
    func withErrorHandling() -> some View {
        self.overlay(
            GlobalErrorView(errorManager: GlobalErrorManager.shared)
        )
        .onAppear {
            ErrorHandlingIntegration.setupAppWideErrorHandling()
        }
    }
    
    /// Add network status monitoring to any view
    func withNetworkMonitoring() -> some View {
        self.environmentObject(NetworkErrorHandler.shared)
    }
    
    /// Add service health monitoring to any view
    func withServiceMonitoring() -> some View {
        self.environmentObject(ServiceErrorHandler.shared)
    }
}

#Preview {
    if #available(iOS 18.0, macOS 14.0, *) {
        ErrorHandlingExampleView()
    } else {
        Text("Preview unavailable")
    }
}