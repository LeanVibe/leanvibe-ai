import SwiftUI
import Foundation

@available(iOS 18.0, macOS 14.0, *)
@MainActor
class RetryManager: ObservableObject {
    static let shared = RetryManager()
    
    @Published var activeRetries: [RetryOperation] = []
    @Published var retryHistory: [RetryOperation] = []
    
    private init() {}
    
    /// Execute an operation with retry logic
    func executeWithRetry<T>(
        operation: @escaping () async throws -> T,
        maxAttempts: Int = 3,
        backoffStrategy: BackoffStrategy = .exponential(),
        retryCondition: @escaping (Error) -> Bool = { _ in true },
        onAttempt: @escaping (Int, Error?) -> Void = { _, _ in },
        context: String = ""
    ) async throws -> T {
        let retryOp = RetryOperation(
            maxAttempts: maxAttempts,
            backoffStrategy: backoffStrategy,
            context: context
        )
        
        activeRetries.append(retryOp)
        defer { 
            if let index = activeRetries.firstIndex(where: { $0.id == retryOp.id }) {
                activeRetries.remove(at: index)
            }
            retryHistory.append(retryOp)
        }
        
        var lastError: Error?
        
        for attempt in 1...maxAttempts {
            retryOp.currentAttempt = attempt
            retryOp.lastAttemptTime = Date()
            
            do {
                let result = try await operation()
                retryOp.status = .succeeded
                onAttempt(attempt, nil)
                return result
            } catch {
                lastError = error
                retryOp.lastError = error
                onAttempt(attempt, error)
                
                // Check if we should retry this error
                guard retryCondition(error) && attempt < maxAttempts else {
                    retryOp.status = .failed
                    break
                }
                
                // Apply backoff delay
                let delay = backoffStrategy.delay(for: attempt)
                retryOp.nextRetryTime = Date().addingTimeInterval(delay)
                
                try await Task.sleep(for: .seconds(delay))
            }
        }
        
        retryOp.status = .failed
        throw lastError ?? RetryError.maxAttemptsExceeded
    }
    
    /// Create a retry action for GlobalErrorManager with enhanced error categorization
    func createRetryAction<T>(
        operation: @escaping () async throws -> T,
        maxAttempts: Int = 3,
        backoffStrategy: BackoffStrategy = .exponential(),
        context: String = "",
        category: ErrorCategory = .system,
        onSuccess: @escaping (T) -> Void = { _ in },
        onFailure: @escaping (Error) -> Void = { _ in }
    ) -> () -> Void {
        return {
            Task { @MainActor in
                do {
                    let result = try await self.executeWithRetry(
                        operation: operation,
                        maxAttempts: maxAttempts,
                        backoffStrategy: backoffStrategy,
                        context: context
                    )
                    onSuccess(result)
                    GlobalErrorManager.shared.showSuccess("Operation completed successfully")
                } catch {
                    onFailure(error)
                    GlobalErrorManager.shared.showError(error, context: "Retry failed: \(context)", category: category)
                    
                    // Trigger automatic recovery if appropriate
                    if category == .network || category == .service {
                        let appError = AppError.from(error, context: context, category: category)
                        Task {
                            await ErrorRecoveryManager.shared.attemptRecovery(for: appError)
                        }
                    }
                }
            }
        }
    }
    
    /// Check if an operation should be retried based on error type
    static func shouldRetry(_ error: Error) -> Bool {
        switch error {
        case TaskServiceError.networkFailure,
             TaskServiceError.invalidData:
            return true
        case TaskServiceError.unauthorized,
             TaskServiceError.taskNotFound:
            return false
        case let urlError as URLError:
            return urlError.code == .timedOut || 
                   urlError.code == .cannotConnectToHost ||
                   urlError.code == .networkConnectionLost
        default:
            return true
        }
    }
}

@available(iOS 18.0, macOS 14.0, *)
class RetryOperation: ObservableObject, Identifiable {
    let id = UUID()
    let createdAt = Date()
    let maxAttempts: Int
    let backoffStrategy: BackoffStrategy
    let context: String
    
    @Published var currentAttempt: Int = 0
    @Published var status: RetryStatus = .pending
    @Published var lastAttemptTime: Date?
    @Published var nextRetryTime: Date?
    var lastError: Error?
    
    init(maxAttempts: Int, backoffStrategy: BackoffStrategy, context: String) {
        self.maxAttempts = maxAttempts
        self.backoffStrategy = backoffStrategy
        self.context = context
    }
}

@available(iOS 18.0, macOS 14.0, *)
enum RetryStatus {
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

enum BackoffStrategy {
    case linear(TimeInterval)
    case exponential(base: TimeInterval = 1.0, multiplier: Double = 2.0)
    case fixed(TimeInterval)
    case custom((Int) -> TimeInterval)
    
    func delay(for attempt: Int) -> TimeInterval {
        switch self {
        case .linear(let interval):
            return interval * Double(attempt)
        case .exponential(let base, let multiplier):
            return base * pow(multiplier, Double(attempt - 1))
        case .fixed(let interval):
            return interval
        case .custom(let calculator):
            return calculator(attempt)
        }
    }
}

enum RetryError: LocalizedError {
    case maxAttemptsExceeded
    case operationCancelled
    
    var errorDescription: String? {
        switch self {
        case .maxAttemptsExceeded:
            return "Maximum retry attempts exceeded"
        case .operationCancelled:
            return "Retry operation was cancelled"
        }
    }
}