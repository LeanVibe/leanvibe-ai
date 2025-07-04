import Foundation
import Network
import Combine

@available(iOS 18.0, macOS 14.0, *)
@MainActor
class NetworkErrorHandler: ObservableObject {
    static let shared = NetworkErrorHandler()
    
    @Published var isConnected = true
    @Published var connectionType: NWInterface.InterfaceType?
    @Published var latency: TimeInterval = 0
    @Published var isSlowConnection = false
    
    private let monitor = NWPathMonitor()
    private let queue = DispatchQueue(label: "NetworkMonitor")
    private var cancellables = Set<AnyCancellable>()
    
    // Connection quality monitoring
    private var lastLatencyCheck = Date.distantPast
    private let latencyCheckInterval: TimeInterval = 30 // Check every 30 seconds
    
    // WebSocket vs REST API error differentiation
    private var webSocketErrors: [String: Date] = [:]
    private var restAPIErrors: [String: Date] = [:]
    
    private init() {
        startMonitoring()
    }
    
    deinit {
        monitor.cancel()
    }
    
    // MARK: - Network Monitoring
    
    private func startMonitoring() {
        monitor.pathUpdateHandler = { [weak self] path in
            Task { @MainActor [weak self] in
                self?.updateConnectionStatus(path)
            }
        }
        monitor.start(queue: queue)
    }
    
    private func updateConnectionStatus(_ path: NWPath) {
        let wasConnected = isConnected
        isConnected = path.status == .satisfied
        
        // Update connection type
        if let interface = path.availableInterfaces.first {
            connectionType = interface.type
        }
        
        // Update global error manager
        let networkStatus: NetworkStatus = isConnected ? .connected : .disconnected
        GlobalErrorManager.shared.updateNetworkStatus(networkStatus)
        
        // Handle connection state changes
        if !wasConnected && isConnected {
            handleConnectionRestored()
        } else if wasConnected && !isConnected {
            handleConnectionLost()
        }
        
        // Check connection quality if connected
        if isConnected {
            Task {
                await checkConnectionQuality()
            }
        }
    }
    
    private func handleConnectionRestored() {
        // Clear old error records
        cleanupOldErrors()
        
        // Notify services to retry failed operations
        NotificationCenter.default.post(name: .networkRestored, object: nil)
        
        // Show success message
        GlobalErrorManager.shared.showSuccess("Connection restored", autoDismiss: true)
    }
    
    private func handleConnectionLost() {
        // Show connection lost error
        let error = AppError(
            title: "Connection Lost",
            message: "No internet connection available",
            severity: .critical,
            category: .network,
            context: "network_monitor",
            userFacingMessage: "Your device is offline. Some features may not work.",
            suggestedActions: [
                ErrorAction(title: "Retry", systemImage: "arrow.clockwise", isPrimary: true) {
                    Task { @MainActor in
                        await NetworkErrorHandler.shared.checkConnectionQuality()
                    }
                },
                ErrorAction(title: "Settings", systemImage: "gear") {
                    // Open network settings
                    if let settingsUrl = URL(string: "App-Prefs:root=WIFI") {
                        UIApplication.shared.open(settingsUrl)
                    }
                }
            ]
        )
        
        GlobalErrorManager.shared.showError(error)
        
        // Notify services to switch to offline mode
        NotificationCenter.default.post(name: .networkLost, object: nil)
    }
    
    // MARK: - Connection Quality Monitoring
    
    private func checkConnectionQuality() async {
        guard isConnected else { return }
        
        let now = Date()
        guard now.timeIntervalSince(lastLatencyCheck) > latencyCheckInterval else { return }
        lastLatencyCheck = now
        
        // Measure latency to a reliable endpoint
        let startTime = Date()
        
        do {
            // Use a lightweight endpoint for latency check
            let url = URL(string: "https://www.apple.com/library/test/success.html")!
            var request = URLRequest(url: url)
            request.timeoutInterval = 5.0
            request.httpMethod = "HEAD"
            
            let (_, response) = try await URLSession.shared.data(for: request)
            
            if let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 {
                let measuredLatency = Date().timeIntervalSince(startTime)
                await updateLatency(measuredLatency)
            }
        } catch {
            // If latency check fails, connection might be slow or unstable
            await updateLatency(5.0) // Assume slow connection
        }
    }
    
    private func updateLatency(_ newLatency: TimeInterval) {
        latency = newLatency
        
        let wasSlowConnection = isSlowConnection
        isSlowConnection = newLatency > 2.0 // Consider > 2s as slow
        
        // Update global status
        let networkStatus: NetworkStatus = isSlowConnection ? .slow : .connected
        GlobalErrorManager.shared.updateNetworkStatus(networkStatus)
        
        // Show warning for slow connections
        if !wasSlowConnection && isSlowConnection {
            let warning = AppError(
                title: "Slow Connection",
                message: "Your internet connection is slow. Some features may be delayed.",
                severity: .warning,
                category: .network,
                context: "slow_connection",
                autoDismissDelay: 3.0
            )
            GlobalErrorManager.shared.showError(warning)
        }
    }
    
    // MARK: - Error Type Differentiation
    
    func handleWebSocketError(_ error: Error, endpoint: String) {
        webSocketErrors[endpoint] = Date()
        
        let appError: AppError
        
        if let urlError = error as? URLError {
            switch urlError.code {
            case .networkConnectionLost:
                appError = AppError(
                    title: "WebSocket Disconnected",
                    message: "Real-time connection lost",
                    severity: .warning,
                    category: .network,
                    context: "websocket:\(endpoint)",
                    userFacingMessage: "Real-time updates temporarily unavailable. Reconnecting...",
                    suggestedActions: [
                        ErrorAction(title: "Reconnect", systemImage: "arrow.clockwise", isPrimary: true) {
                            self.reconnectWebSocket(endpoint)
                        }
                    ]
                )
            case .cannotConnectToHost:
                appError = AppError(
                    title: "WebSocket Connection Failed",
                    message: "Cannot connect to real-time server",
                    severity: .error,
                    category: .network,
                    context: "websocket:\(endpoint)",
                    userFacingMessage: "Cannot establish real-time connection. Using polling instead.",
                    suggestedActions: [
                        ErrorAction(title: "Use Polling", systemImage: "arrow.clockwise", isPrimary: true) {
                            self.fallbackToPolling(endpoint)
                        }
                    ]
                )
            default:
                appError = AppError.from(error, context: "websocket:\(endpoint)", category: .network)
            }
        } else {
            appError = AppError.from(error, context: "websocket:\(endpoint)", category: .network)
        }
        
        GlobalErrorManager.shared.showError(appError)
    }
    
    func handleRESTAPIError(_ error: Error, endpoint: String, httpMethod: String) {
        restAPIErrors["\(httpMethod):\(endpoint)"] = Date()
        
        let appError: AppError
        
        if let urlError = error as? URLError {
            switch urlError.code {
            case .notConnectedToInternet:
                appError = AppError(
                    title: "Offline",
                    message: "API request failed - no internet",
                    severity: .warning,
                    category: .network,
                    context: "\(httpMethod):\(endpoint)",
                    userFacingMessage: "You're offline. Changes will sync when connection is restored.",
                    suggestedActions: [
                        ErrorAction(title: "Retry When Online", systemImage: "wifi", isPrimary: true) {
                            self.scheduleRetryWhenOnline(endpoint, httpMethod)
                        }
                    ]
                )
            case .timedOut:
                appError = AppError(
                    title: "Request Timeout",
                    message: "API request timed out",
                    severity: .warning,
                    category: .network,
                    context: "\(httpMethod):\(endpoint)",
                    userFacingMessage: "Request is taking too long. Please try again.",
                    suggestedActions: [
                        ErrorAction(title: "Retry", systemImage: "arrow.clockwise", isPrimary: true) {
                            self.retryAPIRequest(endpoint, httpMethod)
                        }
                    ]
                )
            default:
                appError = AppError.from(error, context: "\(httpMethod):\(endpoint)", category: .network)
            }
        } else {
            appError = AppError.from(error, context: "\(httpMethod):\(endpoint)", category: .network)
        }
        
        GlobalErrorManager.shared.showError(appError)
    }
    
    // MARK: - Recovery Actions
    
    private func reconnectWebSocket(_ endpoint: String) {
        NotificationCenter.default.post(
            name: .reconnectWebSocket,
            object: nil,
            userInfo: ["endpoint": endpoint]
        )
    }
    
    private func fallbackToPolling(_ endpoint: String) {
        NotificationCenter.default.post(
            name: .fallbackToPolling,
            object: nil,
            userInfo: ["endpoint": endpoint]
        )
    }
    
    private func retryAPIRequest(_ endpoint: String, _ httpMethod: String) {
        NotificationCenter.default.post(
            name: .retryAPIRequest,
            object: nil,
            userInfo: ["endpoint": endpoint, "method": httpMethod]
        )
    }
    
    private func scheduleRetryWhenOnline(_ endpoint: String, _ httpMethod: String) {
        // Store the retry request for when connection is restored
        NotificationCenter.default.post(
            name: .scheduleRetryWhenOnline,
            object: nil,
            userInfo: ["endpoint": endpoint, "method": httpMethod]
        )
    }
    
    // MARK: - Error Analytics
    
    func getErrorStats() -> NetworkErrorStats {
        let now = Date()
        let oneHourAgo = now.addingTimeInterval(-3600)
        
        let recentWebSocketErrors = webSocketErrors.values.filter { $0 > oneHourAgo }.count
        let recentRESTErrors = restAPIErrors.values.filter { $0 > oneHourAgo }.count
        
        return NetworkErrorStats(
            webSocketErrors: recentWebSocketErrors,
            restAPIErrors: recentRESTErrors,
            connectionType: connectionType,
            averageLatency: latency,
            isSlowConnection: isSlowConnection
        )
    }
    
    private func cleanupOldErrors() {
        let oneDayAgo = Date().addingTimeInterval(-86400)
        
        webSocketErrors = webSocketErrors.filter { $0.value > oneDayAgo }
        restAPIErrors = restAPIErrors.filter { $0.value > oneDayAgo }
    }
}

// MARK: - Supporting Types

struct NetworkErrorStats {
    let webSocketErrors: Int
    let restAPIErrors: Int
    let connectionType: NWInterface.InterfaceType?
    let averageLatency: TimeInterval
    let isSlowConnection: Bool
}

// MARK: - Notification Extensions

extension Notification.Name {
    static let networkRestored = Notification.Name("networkRestored")
    static let networkLost = Notification.Name("networkLost")
    static let reconnectWebSocket = Notification.Name("reconnectWebSocket")
    static let fallbackToPolling = Notification.Name("fallbackToPolling")
    static let retryAPIRequest = Notification.Name("retryAPIRequest")
    static let scheduleRetryWhenOnline = Notification.Name("scheduleRetryWhenOnline")
}

// MARK: - UIApplication Extension for Settings

extension UIApplication {
    func openSettings() {
        if let settingsUrl = URL(string: UIApplication.openSettingsURLString) {
            open(settingsUrl)
        }
    }
}