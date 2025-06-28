import SwiftUI
import Foundation
import Combine

@MainActor
class AppCoordinator: ObservableObject {
    @Published var isConfigured = false
    @Published var showingQRScanner = false
    @Published var appState: AppState = .launching
    @Published var errorMessage: String?
    
    private let connectionManager = ConnectionStorageManager()
    private let lifecycleManager = AppLifecycleManager()
    
    enum AppState {
        case launching
        case needsConfiguration
        case ready
        case error(String)
    }
    
    init() {
        setupLifecycleObserver()
        initializeApp()
    }
    
    private func setupLifecycleObserver() {
        // Observe lifecycle manager state changes
        lifecycleManager.$appState
            .sink { [weak self] lifecycleState in
                self?.handleLifecycleStateChange(lifecycleState)
            }
            .store(in: &cancellables)
    }
    
    private var cancellables = Set<AnyCancellable>()
    
    private func initializeApp() {
        Task {
            await lifecycleManager.initialize()
        }
    }
    
    private func handleLifecycleStateChange(_ lifecycleState: AppLifecycleManager.AppState) {
        switch lifecycleState {
        case .launching:
            appState = .launching
        case .needsOnboarding:
            appState = .needsConfiguration
            showingQRScanner = true
            isConfigured = false
        case .ready:
            appState = .ready
            isConfigured = true
            showingQRScanner = false
        case .error(let message):
            appState = .error(message)
            errorMessage = message
            showingQRScanner = false
        case .needsPermissions:
            // Handle permissions in the ready state for now
            appState = .ready
            isConfigured = true
            showingQRScanner = false
        case .background:
            // Background state doesn't change the coordinator state
            break
        }
    }
    
    func handleQRScanSuccess() {
        // Connection was successful, reinitialize the app
        Task {
            await lifecycleManager.initialize()
        }
    }
    
    func handleQRScanFailure(error: String) {
        lifecycleManager.handleError(error)
    }
    
    func retryConfiguration() {
        lifecycleManager.retryFromError()
    }
    
    func resetApp() {
        lifecycleManager.resetToOnboarding()
    }
    
    // MARK: - Lifecycle Access
    
    var lifecycleState: AppLifecycleManager.AppState {
        return lifecycleManager.appState
    }
    
    var sessionDuration: TimeInterval {
        return lifecycleManager.sessionDuration
    }
    
    var canUseVoiceFeatures: Bool {
        return lifecycleManager.canUseVoiceFeatures
    }
}