import SwiftUI
import Foundation
import Combine

@MainActor
class AppLifecycleManager: ObservableObject {
    @Published var appState: AppState = .launching
    @Published var lastError: String?
    @Published var backgroundTime: TimeInterval = 0
    @Published var sessionDuration: TimeInterval = 0
    
    private let connectionManager = ConnectionStorageManager()
    private let permissionManager = VoicePermissionManager()
    private var sessionStartTime: Date?
    private var backgroundStartTime: Date?
    private var cancellables = Set<AnyCancellable>()
    
    enum AppState: Equatable {
        case launching
        case needsOnboarding
        case needsPermissions
        case ready
        case background
        case error(String)
        
        static func == (lhs: AppState, rhs: AppState) -> Bool {
            switch (lhs, rhs) {
            case (.launching, .launching), (.needsOnboarding, .needsOnboarding),
                 (.needsPermissions, .needsPermissions), (.ready, .ready),
                 (.background, .background):
                return true
            case let (.error(lhsMessage), .error(rhsMessage)):
                return lhsMessage == rhsMessage
            default:
                return false
            }
        }
        
        var description: String {
            switch self {
            case .launching:
                return "Launching"
            case .needsOnboarding:
                return "Needs Setup"
            case .needsPermissions:
                return "Needs Permissions"
            case .ready:
                return "Ready"
            case .background:
                return "Background"
            case .error(let message):
                return "Error: \(message)"
            }
        }
    }
    
    init() {
        setupAppLifecycleObservers()
        startSessionTracking()
    }
    
    private func setupAppLifecycleObservers() {
        // Observe app lifecycle notifications
        NotificationCenter.default.publisher(for: UIApplication.willEnterForegroundNotification)
            .sink { [weak self] _ in
                self?.handleForegroundTransition()
            }
            .store(in: &cancellables)
        
        NotificationCenter.default.publisher(for: UIApplication.didEnterBackgroundNotification)
            .sink { [weak self] _ in
                self?.handleBackgroundTransition()
            }
            .store(in: &cancellables)
        
        NotificationCenter.default.publisher(for: UIApplication.willTerminateNotification)
            .sink { [weak self] _ in
                self?.handleAppTermination()
            }
            .store(in: &cancellables)
    }
    
    private func startSessionTracking() {
        sessionStartTime = Date()
        
        // Update session duration every minute
        Timer.scheduledTimer(withTimeInterval: 60.0, repeats: true) { [weak self] _ in
            self?.updateSessionDuration()
        }
    }
    
    private func updateSessionDuration() {
        guard let startTime = sessionStartTime else { return }
        sessionDuration = Date().timeIntervalSince(startTime)
    }
    
    // MARK: - Lifecycle State Management
    
    func initialize() async {
        appState = .launching
        
        // Small delay to show launch screen
        try? await Task.sleep(nanoseconds: 1_000_000_000) // 1 second
        
        // Check connection
        guard connectionManager.hasStoredConnection() else {
            appState = .needsOnboarding
            return
        }
        
        // Check permissions
        let hasVoicePermission = await checkVoicePermissions()
        guard hasVoicePermission else {
            appState = .needsPermissions
            return
        }
        
        // Test connection
        let isConnected = await testBackendConnection()
        if isConnected {
            appState = .ready
        } else {
            appState = .error("Cannot connect to backend server")
        }
    }
    
    private func checkVoicePermissions() async -> Bool {
        return await withCheckedContinuation { continuation in
            permissionManager.requestFullPermissions { granted in
                continuation.resume(returning: granted)
            }
        }
    }
    
    private func testBackendConnection() async -> Bool {
        // Simulate connection test
        try? await Task.sleep(nanoseconds: 500_000_000) // 0.5 seconds
        
        // In a real implementation, this would test the WebSocket connection
        guard let connection = connectionManager.currentConnection else {
            return false
        }
        
        // For now, assume connection is good if we have stored settings
        return !connection.host.isEmpty && connection.port > 0
    }
    
    func handleBackgroundTransition() {
        guard appState == .ready else { return }
        
        backgroundStartTime = Date()
        appState = .background
        
        // Save app state
        saveAppState()
        
        // Pause resource-intensive operations
        pauseBackgroundOperations()
    }
    
    func handleForegroundTransition() {
        // Calculate background duration
        if let backgroundStart = backgroundStartTime {
            backgroundTime += Date().timeIntervalSince(backgroundStart)
            backgroundStartTime = nil
        }
        
        // Restore app state based on previous state
        if appState == .background {
            appState = .ready
            
            // Resume operations
            resumeForegroundOperations()
            
            // Re-check connection if we were in background for more than 5 minutes
            if backgroundTime > 300 {
                Task {
                    let isConnected = await testBackendConnection()
                    if !isConnected {
                        appState = .error("Connection lost while in background")
                    }
                }
            }
        }
    }
    
    private func handleAppTermination() {
        saveAppState()
        updateSessionDuration()
        
        // Log session statistics
        print("Session ended - Duration: \(sessionDuration)s, Background time: \(backgroundTime)s")
    }
    
    // MARK: - State Persistence
    
    private func saveAppState() {
        let stateData: [String: Any] = [
            "lastActiveTime": Date().timeIntervalSince1970,
            "sessionDuration": sessionDuration,
            "backgroundTime": backgroundTime
        ]
        
        UserDefaults.standard.set(stateData, forKey: "AppLifecycleState")
    }
    
    private func loadAppState() {
        guard let stateData = UserDefaults.standard.dictionary(forKey: "AppLifecycleState") else {
            return
        }
        
        if let lastActiveTime = stateData["lastActiveTime"] as? TimeInterval {
            let timeSinceLastActive = Date().timeIntervalSince1970 - lastActiveTime
            
            // If app was inactive for more than 24 hours, reset some state
            if timeSinceLastActive > 86400 {
                resetSessionState()
            }
        }
        
        if let savedBackgroundTime = stateData["backgroundTime"] as? TimeInterval {
            backgroundTime = savedBackgroundTime
        }
    }
    
    private func resetSessionState() {
        sessionStartTime = Date()
        sessionDuration = 0
        backgroundTime = 0
    }
    
    // MARK: - Resource Management
    
    private func pauseBackgroundOperations() {
        // Notify other components to pause operations
        NotificationCenter.default.post(
            name: NSNotification.Name("AppDidEnterBackground"),
            object: nil
        )
    }
    
    private func resumeForegroundOperations() {
        // Notify other components to resume operations
        NotificationCenter.default.post(
            name: NSNotification.Name("AppDidEnterForeground"),
            object: nil
        )
    }
    
    // MARK: - Error Handling
    
    func handleError(_ error: String) {
        lastError = error
        appState = .error(error)
    }
    
    func retryFromError() {
        lastError = nil
        Task {
            await initialize()
        }
    }
    
    func resetToOnboarding() {
        connectionManager.clearStoredConnection()
        appState = .needsOnboarding
        lastError = nil
    }
    
    // MARK: - State Queries
    
    var isReady: Bool {
        return appState == .ready
    }
    
    var needsSetup: Bool {
        return appState == .needsOnboarding || appState == .needsPermissions
    }
    
    var hasError: Bool {
        if case .error = appState {
            return true
        }
        return false
    }
    
    var canUseVoiceFeatures: Bool {
        return isReady && permissionManager.isFullyAuthorized
    }
}