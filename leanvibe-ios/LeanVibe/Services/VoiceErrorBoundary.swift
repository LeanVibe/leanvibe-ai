import Foundation
import SwiftUI

/// Global error boundary for voice services to prevent app crashes
/// Implements circuit breaker pattern for voice service failures
@available(iOS 18.0, macOS 14.0, *)
@MainActor
class VoiceErrorBoundary: ObservableObject {
    static let shared = VoiceErrorBoundary()
    
    @Published private(set) var isVoiceSystemHealthy = true
    @Published private(set) var lastError: String?
    @Published private(set) var errorCount = 0
    @Published private(set) var lastErrorTime: Date?
    
    // Circuit breaker thresholds
    private let maxErrorsBeforeDisable = 3
    private let errorResetTimeInterval: TimeInterval = 300 // 5 minutes
    private let emergencyDisableTimeInterval: TimeInterval = 60 // 1 minute
    
    private var errors: [VoiceServiceError] = []
    
    private init() {
        setupErrorObserver()
    }
    
    /// Record a voice service error and decide if voice should be disabled
    func recordVoiceError(_ error: Error, from service: String) {
        let voiceError = VoiceServiceError(
            error: error,
            service: service,
            timestamp: Date()
        )
        
        errors.append(voiceError)
        errorCount += 1
        lastError = error.localizedDescription
        lastErrorTime = Date()
        
        print("🚨 VoiceErrorBoundary: Error #\(errorCount) from \(service): \(error.localizedDescription)")
        
        // Clean up old errors
        cleanupOldErrors()
        
        // Check if we should disable voice services
        evaluateVoiceSystemHealth()
    }
    
    /// Check if voice services should be disabled due to frequent errors
    private func evaluateVoiceSystemHealth() {
        let recentErrors = getRecentErrors()
        
        // If we have too many recent errors, disable voice system
        if recentErrors.count >= maxErrorsBeforeDisable {
            disableVoiceSystemDueToCrashes()
        }
        
        // Check for rapid succession errors (potential crash loop)
        if checkForRapidErrors() {
            emergencyDisableVoiceSystem()
        }
    }
    
    /// Get errors from the last reset interval
    private func getRecentErrors() -> [VoiceServiceError] {
        let cutoffTime = Date().addingTimeInterval(-errorResetTimeInterval)
        return errors.filter { $0.timestamp > cutoffTime }
    }
    
    /// Check for errors happening in rapid succession
    private func checkForRapidErrors() -> Bool {
        let cutoffTime = Date().addingTimeInterval(-emergencyDisableTimeInterval)
        let rapidErrors = errors.filter { $0.timestamp > cutoffTime }
        return rapidErrors.count >= 2 // 2 errors within 1 minute = emergency
    }
    
    /// Disable voice system due to repeated crashes
    private func disableVoiceSystemDueToCrashes() {
        isVoiceSystemHealthy = false
        
        let errorSummary = getRecentErrors()
            .map { "\($0.service): \($0.error.localizedDescription)" }
            .joined(separator: "; ")
        
        AppConfiguration.emergencyDisableVoice(reason: "Multiple errors: \(errorSummary)")
        
        print("🚨 VoiceErrorBoundary: Voice system disabled due to \(errorCount) recent errors")
        
        // Schedule automatic re-enable attempt
        scheduleHealthCheck()
    }
    
    /// Emergency disable for rapid succession errors
    private func emergencyDisableVoiceSystem() {
        isVoiceSystemHealthy = false
        AppConfiguration.emergencyDisableVoice(reason: "Emergency: Rapid error succession detected")
        
        print("🚨 VoiceErrorBoundary: EMERGENCY disable - rapid error succession detected")
    }
    
    /// Clean up errors older than the reset interval
    private func cleanupOldErrors() {
        let cutoffTime = Date().addingTimeInterval(-errorResetTimeInterval * 2) // Keep 2x interval for history
        errors.removeAll { $0.timestamp < cutoffTime }
    }
    
    /// Schedule a health check to potentially re-enable voice services
    private func scheduleHealthCheck() {
        Task {
            // Wait 10 minutes before attempting to re-enable
            try? await Task.sleep(nanoseconds: 600_000_000_000) // 10 minutes
            
            await MainActor.run {
                attemptVoiceSystemRecovery()
            }
        }
    }
    
    /// Attempt to recover voice system if errors have stopped
    private func attemptVoiceSystemRecovery() {
        let recentErrors = getRecentErrors()
        
        // If no recent errors, try to re-enable
        if recentErrors.isEmpty {
            print("🔄 VoiceErrorBoundary: Attempting voice system recovery...")
            AppConfiguration.reEnableVoice()
            isVoiceSystemHealthy = true
            errorCount = 0
            lastError = nil
        } else {
            print("⏳ VoiceErrorBoundary: Still have recent errors, delaying recovery")
            scheduleHealthCheck() // Try again later
        }
    }
    
    /// Manually reset the error boundary (for debugging)
    func resetErrorBoundary() {
        errors.removeAll()
        errorCount = 0
        lastError = nil
        lastErrorTime = nil
        isVoiceSystemHealthy = true
        AppConfiguration.reEnableVoice()
        print("🔄 VoiceErrorBoundary: Manually reset")
    }
    
    /// Set up global error observer for unhandled exceptions
    private func setupErrorObserver() {
        NotificationCenter.default.addObserver(
            forName: NSNotification.Name("VoiceServiceError"),
            object: nil,
            queue: .main
        ) { [weak self] notification in
            if let error = notification.userInfo?["error"] as? Error,
               let service = notification.userInfo?["service"] as? String {
                self?.recordVoiceError(error, from: service)
            }
        }
    }
    
    /// Get current status for debugging
    var debugStatus: String {
        return """
        VoiceErrorBoundary Status:
        - System Healthy: \(isVoiceSystemHealthy)
        - Total Errors: \(errorCount)
        - Recent Errors: \(getRecentErrors().count)
        - Last Error: \(lastError ?? "None")
        - Last Error Time: \(lastErrorTime?.description ?? "None")
        - Voice Disabled Reason: \(AppConfiguration.shared.voiceDisableReason ?? "None")
        """
    }
}

/// Voice service error tracking
struct VoiceServiceError {
    let error: Error
    let service: String
    let timestamp: Date
}

/// Extension to easily post voice errors to the error boundary
extension Notification.Name {
    static let voiceServiceError = Notification.Name("VoiceServiceError")
}

/// Helper function to post voice service errors
func reportVoiceError(_ error: Error, from service: String) {
    NotificationCenter.default.post(
        name: .voiceServiceError,
        object: nil,
        userInfo: ["error": error, "service": service]
    )
}