import Foundation
import Combine
import SwiftUI

@available(iOS 18.0, macOS 14.0, *)
@MainActor
class ErrorRecoveryManager: ObservableObject {
    static let shared = ErrorRecoveryManager()
    
    @Published var activeRecoveries: [RecoveryOperation] = []
    @Published var recoveryHistory: [RecoveryOperation] = []
    @Published var isInRecoveryMode = false
    
    private var cancellables = Set<AnyCancellable>()
    private var recoveryStrategies: [ErrorCategory: [RecoveryStrategy]] = [:]
    private var pendingRetries: [String: PendingRetry] = [:]
    private var recoveryMetrics: RecoveryMetrics = RecoveryMetrics()
    
    private init() {
        setupRecoveryStrategies()
        setupNotificationListeners()
    }
    
    // MARK: - Recovery Strategies Setup
    
    private func setupRecoveryStrategies() {
        recoveryStrategies = [
            .network: [
                .immediateRetry(maxAttempts: 3),
                .exponentialBackoff(baseDelay: 1.0, maxDelay: 30.0),
                .degradedMode,
                .offlineMode
            ],
            .service: [
                .immediateRetry(maxAttempts: 2),
                .circuitBreakerReset,
                .fallbackService,
                .localFallback
            ],
            .data: [
                .immediateRetry(maxAttempts: 1),
                .dataRefresh,
                .cacheRecovery,
                .resetToDefaults
            ],
            .ui: [
                .viewRefresh,
                .navigationReset,
                .stateRecovery
            ],
            .system: [
                .processRestart,
                .memoryCleanup,
                .configurationReset
            ],
            .permission: [
                .permissionRequest,
                .alternativeMethod,
                .userGuidance
            ],
            .validation: [
                .inputCorrection,
                .defaultValueSubstitution,
                .userPrompt
            ]
        ]
    }
    
    private func setupNotificationListeners() {
        // Network recovery notifications
        NotificationCenter.default.publisher(for: .networkRestored)
            .sink { [weak self] _ in
                Task { @MainActor [weak self] in
                    await self?.handleNetworkRestored()
                }
            }
            .store(in: &cancellables)
        
        // Service fallback notifications
        NotificationCenter.default.publisher(for: .taskServiceFallback)
            .sink { [weak self] _ in
                self?.enableTaskServiceFallback()
            }
            .store(in: &cancellables)
        
        NotificationCenter.default.publisher(for: .webSocketFallback)
            .sink { [weak self] _ in
                self?.enableWebSocketFallback()
            }
            .store(in: &cancellables)
        
        // Recovery completion notifications
        NotificationCenter.default.publisher(for: .recoveryCompleted)
            .sink { [weak self] notification in
                self?.handleRecoveryCompleted(notification)
            }
            .store(in: &cancellables)
    }
    
    // MARK: - Public Recovery Interface
    
    func attemptRecovery(for error: AppError, using strategies: [RecoveryStrategy]? = nil) async {
        let recoveryOp = RecoveryOperation(
            errorId: error.id,
            errorCategory: error.category,
            strategies: strategies ?? recoveryStrategies[error.category] ?? [],
            context: error.context
        )
        
        activeRecoveries.append(recoveryOp)
        isInRecoveryMode = !activeRecoveries.isEmpty
        
        await executeRecoveryOperation(recoveryOp)
    }
    
    func attemptRecovery(for appError: AppError) async {
        await attemptRecovery(for: appError, using: nil)
    }
    
    func scheduleRetry(_ operation: @escaping () async throws -> Void, 
                      for error: AppError, 
                      delay: TimeInterval = 0) {
        let retryId = UUID().uuidString
        let pendingRetry = PendingRetry(
            id: retryId,
            operation: operation,
            error: error,
            scheduledTime: Date().addingTimeInterval(delay)
        )
        
        pendingRetries[retryId] = pendingRetry
        
        if delay > 0 {
            Task {
                try await Task.sleep(for: .seconds(delay))
                await executeScheduledRetry(retryId)
            }
        } else {
            Task { @MainActor in
                await executeScheduledRetry(retryId)
            }
        }
    }
    
    func cancelRecovery(for errorId: UUID) {
        activeRecoveries.removeAll { $0.errorId == errorId }
        isInRecoveryMode = !activeRecoveries.isEmpty
    }
    
    func clearRecoveryHistory() {
        recoveryHistory.removeAll()
        recoveryMetrics = RecoveryMetrics()
    }
    
    // MARK: - Recovery Execution
    
    private func executeRecoveryOperation(_ operation: RecoveryOperation) async {
        operation.status = .inProgress
        operation.startTime = Date()
        
        for strategy in operation.strategies {
            do {
                let success = try await executeRecoveryStrategy(strategy, for: operation)
                if success {
                    operation.status = .succeeded
                    operation.successfulStrategy = strategy
                    await completeRecovery(operation)
                    return
                }
            } catch {
                operation.lastError = error
                print("Recovery strategy \(strategy) failed: \(error)")
            }
        }
        
        // All strategies failed
        operation.status = .failed
        await completeRecovery(operation)
    }
    
    private func executeRecoveryStrategy(_ strategy: RecoveryStrategy, for operation: RecoveryOperation) async throws -> Bool {
        operation.currentStrategy = strategy
        
        switch strategy {
        case .immediateRetry(let maxAttempts):
            return try await executeImmediateRetry(maxAttempts: maxAttempts, operation: operation)
            
        case .exponentialBackoff(let baseDelay, let maxDelay):
            return try await executeExponentialBackoff(baseDelay: baseDelay, maxDelay: maxDelay, operation: operation)
            
        case .degradedMode:
            return await enableDegradedMode(for: operation)
            
        case .offlineMode:
            return await enableOfflineMode(for: operation)
            
        case .circuitBreakerReset:
            return await resetCircuitBreaker(for: operation)
            
        case .fallbackService:
            return await enableFallbackService(for: operation)
            
        case .localFallback:
            return await enableLocalFallback(for: operation)
            
        case .dataRefresh:
            return try await refreshData(for: operation)
            
        case .cacheRecovery:
            return await recoverFromCache(for: operation)
            
        case .resetToDefaults:
            return await resetToDefaults(for: operation)
            
        case .viewRefresh:
            return await refreshView(for: operation)
            
        case .navigationReset:
            return await resetNavigation(for: operation)
            
        case .stateRecovery:
            return await recoverState(for: operation)
            
        case .processRestart:
            return await restartProcess(for: operation)
            
        case .memoryCleanup:
            return await cleanupMemory(for: operation)
            
        case .configurationReset:
            return await resetConfiguration(for: operation)
            
        case .permissionRequest:
            return await requestPermission(for: operation)
            
        case .alternativeMethod:
            return await useAlternativeMethod(for: operation)
            
        case .userGuidance:
            return await provideUserGuidance(for: operation)
            
        case .inputCorrection:
            return await correctInput(for: operation)
            
        case .defaultValueSubstitution:
            return await substituteDefaultValue(for: operation)
            
        case .userPrompt:
            return await promptUser(for: operation)
        }
    }
    
    // MARK: - Strategy Implementations
    
    private func executeImmediateRetry(maxAttempts: Int, operation: RecoveryOperation) async throws -> Bool {
        for attempt in 1...maxAttempts {
            do {
                try await performOperationRetry(for: operation)
                recordRecoverySuccess(strategy: .immediateRetry(maxAttempts: maxAttempts))
                return true
            } catch {
                if attempt == maxAttempts {
                    throw error
                }
                // Brief delay between retries
                try await Task.sleep(for: .seconds(1))
            }
        }
        return false
    }
    
    private func executeExponentialBackoff(baseDelay: TimeInterval, maxDelay: TimeInterval, operation: RecoveryOperation) async throws -> Bool {
        var currentDelay = baseDelay
        var attempt = 1
        
        while currentDelay <= maxDelay {
            try await Task.sleep(for: .seconds(currentDelay))
            
            do {
                try await performOperationRetry(for: operation)
                recordRecoverySuccess(strategy: .exponentialBackoff(baseDelay: baseDelay, maxDelay: maxDelay))
                return true
            } catch {
                if currentDelay >= maxDelay {
                    throw error
                }
                currentDelay = min(currentDelay * 2, maxDelay)
                attempt += 1
            }
        }
        return false
    }
    
    private func enableDegradedMode(for operation: RecoveryOperation) async -> Bool {
        NotificationCenter.default.post(name: .enableDegradedMode, object: operation.context)
        recordRecoverySuccess(strategy: .degradedMode)
        return true
    }
    
    private func enableOfflineMode(for operation: RecoveryOperation) async -> Bool {
        GlobalErrorManager.shared.enableOfflineMode()
        recordRecoverySuccess(strategy: .offlineMode)
        return true
    }
    
    private func resetCircuitBreaker(for operation: RecoveryOperation) async -> Bool {
        // Extract service name from context
        let serviceName = operation.context
        ServiceErrorHandler.shared.forceServiceRecovery(serviceName)
        recordRecoverySuccess(strategy: .circuitBreakerReset)
        return true
    }
    
    private func enableFallbackService(for operation: RecoveryOperation) async -> Bool {
        switch operation.context {
        case "TaskService":
            NotificationCenter.default.post(name: .taskServiceFallback, object: nil)
        case "WebSocketService":
            NotificationCenter.default.post(name: .webSocketFallback, object: nil)
        default:
            return false
        }
        recordRecoverySuccess(strategy: .fallbackService)
        return true
    }
    
    private func enableLocalFallback(for operation: RecoveryOperation) async -> Bool {
        NotificationCenter.default.post(name: .enableLocalFallback, object: operation.context)
        recordRecoverySuccess(strategy: .localFallback)
        return true
    }
    
    private func refreshData(for operation: RecoveryOperation) async throws -> Bool {
        NotificationCenter.default.post(name: .refreshData, object: operation.context)
        recordRecoverySuccess(strategy: .dataRefresh)
        return true
    }
    
    private func recoverFromCache(for operation: RecoveryOperation) async -> Bool {
        NotificationCenter.default.post(name: .recoverFromCache, object: operation.context)
        recordRecoverySuccess(strategy: .cacheRecovery)
        return true
    }
    
    private func resetToDefaults(for operation: RecoveryOperation) async -> Bool {
        NotificationCenter.default.post(name: .resetToDefaults, object: operation.context)
        recordRecoverySuccess(strategy: .resetToDefaults)
        return true
    }
    
    private func refreshView(for operation: RecoveryOperation) async -> Bool {
        NotificationCenter.default.post(name: .refreshView, object: operation.context)
        recordRecoverySuccess(strategy: .viewRefresh)
        return true
    }
    
    private func resetNavigation(for operation: RecoveryOperation) async -> Bool {
        NotificationCenter.default.post(name: .resetNavigation, object: nil)
        recordRecoverySuccess(strategy: .navigationReset)
        return true
    }
    
    private func recoverState(for operation: RecoveryOperation) async -> Bool {
        NotificationCenter.default.post(name: .recoverState, object: operation.context)
        recordRecoverySuccess(strategy: .stateRecovery)
        return true
    }
    
    private func restartProcess(for operation: RecoveryOperation) async -> Bool {
        // This would be implemented to restart specific processes/services
        NotificationCenter.default.post(name: .restartProcess, object: operation.context)
        recordRecoverySuccess(strategy: .processRestart)
        return true
    }
    
    private func cleanupMemory(for operation: RecoveryOperation) async -> Bool {
        // Trigger memory cleanup
        NotificationCenter.default.post(name: .cleanupMemory, object: nil)
        recordRecoverySuccess(strategy: .memoryCleanup)
        return true
    }
    
    private func resetConfiguration(for operation: RecoveryOperation) async -> Bool {
        NotificationCenter.default.post(name: .resetConfiguration, object: operation.context)
        recordRecoverySuccess(strategy: .configurationReset)
        return true
    }
    
    private func requestPermission(for operation: RecoveryOperation) async -> Bool {
        NotificationCenter.default.post(name: .requestPermission, object: operation.context)
        recordRecoverySuccess(strategy: .permissionRequest)
        return true
    }
    
    private func useAlternativeMethod(for operation: RecoveryOperation) async -> Bool {
        NotificationCenter.default.post(name: .useAlternativeMethod, object: operation.context)
        recordRecoverySuccess(strategy: .alternativeMethod)
        return true
    }
    
    private func provideUserGuidance(for operation: RecoveryOperation) async -> Bool {
        NotificationCenter.default.post(name: .provideUserGuidance, object: operation.context)
        recordRecoverySuccess(strategy: .userGuidance)
        return true
    }
    
    private func correctInput(for operation: RecoveryOperation) async -> Bool {
        NotificationCenter.default.post(name: .correctInput, object: operation.context)
        recordRecoverySuccess(strategy: .inputCorrection)
        return true
    }
    
    private func substituteDefaultValue(for operation: RecoveryOperation) async -> Bool {
        NotificationCenter.default.post(name: .substituteDefaultValue, object: operation.context)
        recordRecoverySuccess(strategy: .defaultValueSubstitution)
        return true
    }
    
    private func promptUser(for operation: RecoveryOperation) async -> Bool {
        NotificationCenter.default.post(name: .promptUser, object: operation.context)
        recordRecoverySuccess(strategy: .userPrompt)
        return true
    }
    
    private func performOperationRetry(for operation: RecoveryOperation) async throws {
        // This would contain the actual retry logic specific to the operation type
        // For now, we'll assume the retry is successful
        // In a real implementation, this would call the original failed operation
    }
    
    // MARK: - Recovery Completion
    
    private func completeRecovery(_ operation: RecoveryOperation) async {
        operation.endTime = Date()
        
        // Remove from active recoveries
        activeRecoveries.removeAll { $0.id == operation.id }
        isInRecoveryMode = !activeRecoveries.isEmpty
        
        // Add to history
        recoveryHistory.append(operation)
        
        // Update metrics
        updateRecoveryMetrics(operation)
        
        // Notify completion
        NotificationCenter.default.post(
            name: .recoveryCompleted,
            object: operation,
            userInfo: ["success": operation.status == .succeeded]
        )
        
        // Show user notification for important recoveries
        if operation.errorCategory == .network || operation.errorCategory == .service {
            let message = operation.status == .succeeded ? 
                "System recovered successfully" : 
                "Recovery failed. Some features may be limited."
            
            let severity: ErrorSeverity = operation.status == .succeeded ? .info : .warning
            
            let notification = AppError(
                title: "Recovery Update",
                message: message,
                severity: severity,
                category: .system,
                context: "recovery",
                autoDismissDelay: 3.0
            )
            
            GlobalErrorManager.shared.showError(notification)
        }
        
        // Clean up old history
        if recoveryHistory.count > 100 {
            recoveryHistory.removeFirst(recoveryHistory.count - 100)
        }
    }
    
    private func executeScheduledRetry(_ retryId: String) async {
        guard let pendingRetry = pendingRetries.removeValue(forKey: retryId) else { return }
        
        do {
            try await pendingRetry.operation()
            
            // Success - show confirmation
            GlobalErrorManager.shared.showSuccess("Operation completed successfully", autoDismiss: true)
        } catch {
            // Retry failed - attempt recovery
            await attemptRecovery(for: pendingRetry.error)
        }
    }
    
    // MARK: - Event Handlers
    
    private func handleNetworkRestored() async {
        // Retry all pending network-related operations
        let networkRetries = pendingRetries.filter { $0.value.error.category == .network }
        
        for (retryId, _) in networkRetries {
            await executeScheduledRetry(retryId)
        }
    }
    
    private func enableTaskServiceFallback() {
        // Task service fallback logic
        NotificationCenter.default.post(name: .useLocalTaskStorage, object: nil)
    }
    
    private func enableWebSocketFallback() {
        // WebSocket fallback to polling
        NotificationCenter.default.post(name: .usePollingMode, object: nil)
    }
    
    private func handleRecoveryCompleted(_ notification: Notification) {
        // Handle external recovery completion notifications
        if let operation = notification.object as? RecoveryOperation,
           let success = notification.userInfo?["success"] as? Bool {
            
            if success {
                recordRecoverySuccess(strategy: operation.currentStrategy)
            } else {
                recordRecoveryFailure(strategy: operation.currentStrategy)
            }
        }
    }
    
    // MARK: - Metrics and Analytics
    
    private func updateRecoveryMetrics(_ operation: RecoveryOperation) {
        recoveryMetrics.totalRecoveries += 1
        
        if operation.status == .succeeded {
            recoveryMetrics.successfulRecoveries += 1
            recoveryMetrics.successfulStrategies[operation.successfulStrategy?.description ?? "unknown", default: 0] += 1
        } else {
            recoveryMetrics.failedRecoveries += 1
        }
        
        if let startTime = operation.startTime, let endTime = operation.endTime {
            let duration = endTime.timeIntervalSince(startTime)
            recoveryMetrics.averageRecoveryTime = (recoveryMetrics.averageRecoveryTime + duration) / 2
        }
        
        recoveryMetrics.recoveriesByCategory[operation.errorCategory, default: 0] += 1
    }
    
    private func recordRecoverySuccess(strategy: RecoveryStrategy) {
        recoveryMetrics.successfulStrategies[strategy.description, default: 0] += 1
    }
    
    private func recordRecoveryFailure(strategy: RecoveryStrategy) {
        recoveryMetrics.failedStrategies[strategy.description, default: 0] += 1
    }
    
    func getRecoveryMetrics() -> RecoveryMetrics {
        return recoveryMetrics
    }
    
    func getRecoverySuccessRate() -> Double {
        guard recoveryMetrics.totalRecoveries > 0 else { return 0 }
        return Double(recoveryMetrics.successfulRecoveries) / Double(recoveryMetrics.totalRecoveries)
    }
}

// MARK: - Supporting Types

@available(iOS 18.0, macOS 14.0, *)
class RecoveryOperation: ObservableObject, Identifiable {
    let id = UUID()
    let errorId: UUID
    let errorCategory: ErrorCategory
    let strategies: [RecoveryStrategy]
    let context: String
    
    @Published var status: RecoveryStatus = .pending
    @Published var currentStrategy: RecoveryStrategy?
    var successfulStrategy: RecoveryStrategy?
    var startTime: Date?
    var endTime: Date?
    var lastError: Error?
    
    init(errorId: UUID, errorCategory: ErrorCategory, strategies: [RecoveryStrategy], context: String) {
        self.errorId = errorId
        self.errorCategory = errorCategory
        self.strategies = strategies
        self.context = context
    }
}

enum RecoveryStatus {
    case pending
    case inProgress
    case succeeded
    case failed
    
    var color: Color {
        switch self {
        case .pending: return .orange
        case .inProgress: return .blue
        case .succeeded: return .green
        case .failed: return .red
        }
    }
    
    var systemImage: String {
        switch self {
        case .pending: return "clock"
        case .inProgress: return "arrow.clockwise"
        case .succeeded: return "checkmark.circle"
        case .failed: return "xmark.circle"
        }
    }
}

enum RecoveryStrategy {
    // Network strategies
    case immediateRetry(maxAttempts: Int)
    case exponentialBackoff(baseDelay: TimeInterval, maxDelay: TimeInterval)
    case degradedMode
    case offlineMode
    
    // Service strategies
    case circuitBreakerReset
    case fallbackService
    case localFallback
    
    // Data strategies
    case dataRefresh
    case cacheRecovery
    case resetToDefaults
    
    // UI strategies
    case viewRefresh
    case navigationReset
    case stateRecovery
    
    // System strategies
    case processRestart
    case memoryCleanup
    case configurationReset
    
    // Permission strategies
    case permissionRequest
    case alternativeMethod
    case userGuidance
    
    // Validation strategies
    case inputCorrection
    case defaultValueSubstitution
    case userPrompt
    
    var description: String {
        switch self {
        case .immediateRetry(let maxAttempts):
            return "Immediate Retry (\(maxAttempts)x)"
        case .exponentialBackoff:
            return "Exponential Backoff"
        case .degradedMode:
            return "Degraded Mode"
        case .offlineMode:
            return "Offline Mode"
        case .circuitBreakerReset:
            return "Circuit Breaker Reset"
        case .fallbackService:
            return "Fallback Service"
        case .localFallback:
            return "Local Fallback"
        case .dataRefresh:
            return "Data Refresh"
        case .cacheRecovery:
            return "Cache Recovery"
        case .resetToDefaults:
            return "Reset to Defaults"
        case .viewRefresh:
            return "View Refresh"
        case .navigationReset:
            return "Navigation Reset"
        case .stateRecovery:
            return "State Recovery"
        case .processRestart:
            return "Process Restart"
        case .memoryCleanup:
            return "Memory Cleanup"
        case .configurationReset:
            return "Configuration Reset"
        case .permissionRequest:
            return "Permission Request"
        case .alternativeMethod:
            return "Alternative Method"
        case .userGuidance:
            return "User Guidance"
        case .inputCorrection:
            return "Input Correction"
        case .defaultValueSubstitution:
            return "Default Value Substitution"
        case .userPrompt:
            return "User Prompt"
        }
    }
}

struct PendingRetry {
    let id: String
    let operation: () async throws -> Void
    let error: AppError
    let scheduledTime: Date
}

struct RecoveryMetrics {
    var totalRecoveries: Int = 0
    var successfulRecoveries: Int = 0
    var failedRecoveries: Int = 0
    var averageRecoveryTime: TimeInterval = 0
    var recoveriesByCategory: [ErrorCategory: Int] = [:]
    var successfulStrategies: [String: Int] = [:]
    var failedStrategies: [String: Int] = [:]
}

// MARK: - Additional Notification Extensions

extension Notification.Name {
    static let recoveryCompleted = Notification.Name("recoveryCompleted")
    static let enableDegradedMode = Notification.Name("enableDegradedMode")
    static let enableLocalFallback = Notification.Name("enableLocalFallback")
    static let refreshData = Notification.Name("refreshData")
    static let recoverFromCache = Notification.Name("recoverFromCache")
    static let resetToDefaults = Notification.Name("resetToDefaults")
    static let refreshView = Notification.Name("refreshView")
    static let resetNavigation = Notification.Name("resetNavigation")
    static let recoverState = Notification.Name("recoverState")
    static let restartProcess = Notification.Name("restartProcess")
    static let cleanupMemory = Notification.Name("cleanupMemory")
    static let resetConfiguration = Notification.Name("resetConfiguration")
    static let requestPermission = Notification.Name("requestPermission")
    static let useAlternativeMethod = Notification.Name("useAlternativeMethod")
    static let provideUserGuidance = Notification.Name("provideUserGuidance")
    static let correctInput = Notification.Name("correctInput")
    static let substituteDefaultValue = Notification.Name("substituteDefaultValue")
    static let promptUser = Notification.Name("promptUser")
    static let useLocalTaskStorage = Notification.Name("useLocalTaskStorage")
    static let usePollingMode = Notification.Name("usePollingMode")
}