import SwiftUI
import Foundation
import Combine

@available(iOS 18.0, macOS 14.0, *)
@MainActor
class AppCoordinator: ObservableObject {
    @Published var isConfigured = false
    @Published var showingQRScanner = false
    @Published var appState: AppState = .launching
    @Published var errorMessage: String?
    
    private let connectionManager = ConnectionStorageManager()
    private let lifecycleManager = AppLifecycleManager()
    
    enum AppState: Equatable {
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
            .sink { [weak self] state in
                self?.handleLifecycleStateChange(state)
            }
            .store(in: &cancellables)
    }
    
    private var cancellables = Set<AnyCancellable>()
    
    func initializeApp() {
        Task {
            await lifecycleManager.initialize()
        }
    }
    
    func handleQRScanSuccess() {
        showingQRScanner = false
        appState = .ready
    }
    
    func handleQRScanFailure(error: String) {
        errorMessage = error
        appState = .error(error)
    }
    
    private func handleLifecycleStateChange(_ state: AppLifecycleManager.AppState) {
        switch state {
        case .launching:
            appState = .launching
        case .needsOnboarding:
            appState = .needsConfiguration
        case .needsPermissions:
            appState = .needsConfiguration
        case .ready:
            appState = .ready
            isConfigured = true
        case .background:
            // Don't change coordinator state during background
            break
        case .error(let message):
            appState = .error(message)
            errorMessage = message
        }
    }
    
    func showQRScanner() {
        showingQRScanner = true
    }
    
    func hideQRScanner() {
        showingQRScanner = false
    }
    
    func handleQRCode(_ code: String) {
        hideQRScanner()
        
        _Concurrency.Task {
            await processQRCode(code)
        }
    }
    
    private func processQRCode(_ code: String) async {
        // Parse QR code and configure connection
        guard let components = parseQRCode(code) else {
            errorMessage = "Invalid QR code format"
            appState = .error("Invalid QR code format")
            return
        }
        
        // Store connection details
        let connection = ServerConfig(
            host: components.host,
            port: components.port,
            websocketPath: "/ws",
            serverName: nil,
            network: nil
        )
        
        connectionManager.store(connection)
        
        // Test connection
        let success = await testConnection(connection)
        if success {
            isConfigured = true
            appState = .ready
        } else {
            appState = .error("Failed to connect to server")
        }
    }
    
    private func parseQRCode(_ code: String) -> (host: String, port: Int, apiKey: String)? {
        // Parse QR code format: leanvibe://connect?host=localhost&port=8000&key=abc123
        guard let url = URL(string: code),
              url.scheme == "leanvibe",
              url.host == "connect" else {
            return nil
        }
        
        let components = URLComponents(url: url, resolvingAgainstBaseURL: false)
        guard let queryItems = components?.queryItems,
              let host = queryItems.first(where: { $0.name == "host" })?.value,
              let portString = queryItems.first(where: { $0.name == "port" })?.value,
              let port = Int(portString),
              let apiKey = queryItems.first(where: { $0.name == "key" })?.value else {
            return nil
        }
        
        return (host: host, port: port, apiKey: apiKey)
    }
    
    private func testConnection(_ connection: ServerConfig) async -> Bool {
        // Simulate connection test
        try? await _Concurrency.Task.sleep(nanoseconds: 1_000_000_000)
        
        // In a real implementation, this would test the WebSocket connection
        return !connection.host.isEmpty && connection.port > 0
    }
    
    func retry() {
        errorMessage = nil
        appState = .launching
        initializeApp()
    }
    
    func resetConfiguration() {
        connectionManager.clearConnection()
        isConfigured = false
        appState = .needsConfiguration
        errorMessage = nil
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

struct ServerConnection {
    let host: String
    let port: Int
    let apiKey: String
}
