import Foundation
import Combine

@available(iOS 18.0, macOS 14.0, *)
@MainActor
class ServiceErrorHandler: ObservableObject {
    static let shared = ServiceErrorHandler()
    
    @Published var serviceHealthStatus: [String: ServiceHealthInfo] = [:]
    @Published var degradedServices: Set<String> = []
    @Published var failedServices: Set<String> = []
    
    private var cancellables = Set<AnyCancellable>()
    private var healthCheckTimers: [String: Timer] = [:]
    private var serviceRetryAttempts: [String: Int] = [:]
    private var lastHealthChecks: [String: Date] = [:]
    
    // Circuit breaker pattern for services
    private var circuitBreakers: [String: CircuitBreaker] = [:]
    
    private init() {
        setupKnownServices()
        startHealthMonitoring()
    }
    
    // MARK: - Service Registration
    
    private func setupKnownServices() {
        let knownServices = [
            "TaskService": ServiceConfiguration(
                healthEndpoint: "/api/tasks/health",
                criticalityLevel: .high,
                healthCheckInterval: 30.0,
                timeoutInterval: 10.0
            ),
            "WebSocketService": ServiceConfiguration(
                healthEndpoint: "/ws/health",
                criticalityLevel: .high,
                healthCheckInterval: 15.0,
                timeoutInterval: 5.0
            ),
            "BackendSettingsService": ServiceConfiguration(
                healthEndpoint: "/api/settings/health",
                criticalityLevel: .medium,
                healthCheckInterval: 60.0,
                timeoutInterval: 10.0
            ),
            "ArchitectureVisualizationService": ServiceConfiguration(
                healthEndpoint: "/api/architecture/health",
                criticalityLevel: .medium,
                healthCheckInterval: 60.0,
                timeoutInterval: 15.0
            ),
            "VoiceService": ServiceConfiguration(
                healthEndpoint: "/api/voice/health",
                criticalityLevel: .low,
                healthCheckInterval: 120.0,
                timeoutInterval: 5.0
            ),
            "MetricsService": ServiceConfiguration(
                healthEndpoint: "/api/metrics/health",
                criticalityLevel: .low,
                healthCheckInterval: 120.0,
                timeoutInterval: 10.0
            )
        ]
        
        for (serviceName, config) in knownServices {
            registerService(serviceName, configuration: config)
        }
    }
    
    func registerService(_ serviceName: String, configuration: ServiceConfiguration) {
        serviceHealthStatus[serviceName] = ServiceHealthInfo(
            name: serviceName,
            status: .unknown,
            configuration: configuration,
            lastCheck: nil,
            lastError: nil,
            responseTime: nil
        )
        
        circuitBreakers[serviceName] = CircuitBreaker(
            failureThreshold: 5,
            recoveryTimeout: 60.0
        )
        
        scheduleHealthCheck(for: serviceName)
    }
    
    // MARK: - Health Monitoring
    
    private func startHealthMonitoring() {
        // Monitor network status changes
        NotificationCenter.default.publisher(for: .networkRestored)
            .sink { [weak self] _ in
                self?.handleNetworkRestored()
            }
            .store(in: &cancellables)
        
        NotificationCenter.default.publisher(for: .networkLost)
            .sink { [weak self] _ in
                self?.handleNetworkLost()
            }
            .store(in: &cancellables)
    }
    
    private func scheduleHealthCheck(for serviceName: String) {
        guard let serviceInfo = serviceHealthStatus[serviceName] else { return }
        
        // Cancel existing timer
        healthCheckTimers[serviceName]?.invalidate()
        
        // Schedule new health check
        let timer = Timer.scheduledTimer(withTimeInterval: serviceInfo.configuration.healthCheckInterval, repeats: true) { [weak self] _ in
            Task { @MainActor [weak self] in
                await self?.performHealthCheck(for: serviceName)
            }
        }
        
        healthCheckTimers[serviceName] = timer
    }
    
    private func performHealthCheck(for serviceName: String) async {
        guard let serviceInfo = serviceHealthStatus[serviceName],
              let circuitBreaker = circuitBreakers[serviceName] else { return }
        
        // Skip health check if circuit breaker is open
        if circuitBreaker.state == .open {
            if circuitBreaker.shouldAttemptReset() {
                circuitBreaker.state = .halfOpen
            } else {
                return
            }
        }
        
        let startTime = Date()
        
        do {
            let isHealthy = try await checkServiceHealth(serviceInfo.configuration)
            let responseTime = Date().timeIntervalSince(startTime)
            
            // Update service status
            let newStatus: ServiceStatus = isHealthy ? .healthy : .degraded
            await updateServiceStatus(serviceName, status: newStatus, responseTime: responseTime, error: nil)
            
            // Reset circuit breaker on success
            circuitBreaker.recordSuccess()
            
        } catch {
            let responseTime = Date().timeIntervalSince(startTime)
            
            // Record failure in circuit breaker
            circuitBreaker.recordFailure()
            
            // Determine error severity
            let newStatus: ServiceStatus = circuitBreaker.state == .open ? .failed : .degraded
            await updateServiceStatus(serviceName, status: newStatus, responseTime: responseTime, error: error)
            
            // Handle service-specific errors
            await handleServiceError(serviceName, error: error, circuitBreaker: circuitBreaker)
        }
    }
    
    private func checkServiceHealth(_ config: ServiceConfiguration) async throws -> Bool {
        guard let baseURL = AppConfiguration.shared.apiBaseURL.isEmpty ? nil : AppConfiguration.shared.apiBaseURL else {
            throw ServiceError.backendNotConfigured
        }
        
        guard let url = URL(string: "\(baseURL)\(config.healthEndpoint)") else {
            throw ServiceError.invalidConfiguration
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.timeoutInterval = config.timeoutInterval
        
        let (_, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw ServiceError.invalidResponse
        }
        
        return 200...299 ~= httpResponse.statusCode
    }
    
    private func updateServiceStatus(_ serviceName: String, status: ServiceStatus, responseTime: TimeInterval, error: Error?) {
        guard var serviceInfo = serviceHealthStatus[serviceName] else { return }
        
        let previousStatus = serviceInfo.status
        serviceInfo.status = status
        serviceInfo.lastCheck = Date()
        serviceInfo.lastError = error
        serviceInfo.responseTime = responseTime
        
        serviceHealthStatus[serviceName] = serviceInfo
        
        // Update service collections
        updateServiceCollections(serviceName, previousStatus: previousStatus, newStatus: status)
        
        // Update global error manager
        GlobalErrorManager.shared.updateServiceStatus(serviceName, status: status)
        
        // Handle status changes
        if previousStatus != status {
            handleServiceStatusChange(serviceName, from: previousStatus, to: status, error: error)
        }
    }
    
    private func updateServiceCollections(_ serviceName: String, previousStatus: ServiceStatus, newStatus: ServiceStatus) {
        // Remove from previous collections
        degradedServices.remove(serviceName)
        failedServices.remove(serviceName)
        
        // Add to new collections
        switch newStatus {
        case .degraded:
            degradedServices.insert(serviceName)
        case .failed:
            failedServices.insert(serviceName)
        default:
            break
        }
    }
    
    // MARK: - Error Handling
    
    private func handleServiceError(_ serviceName: String, error: Error, circuitBreaker: CircuitBreaker) async {
        guard let serviceInfo = serviceHealthStatus[serviceName] else { return }
        
        let criticalityLevel = serviceInfo.configuration.criticalityLevel
        let severity: ErrorSeverity = circuitBreaker.state == .open ? .critical : (criticalityLevel == .high ? .error : .warning)
        
        let appError = AppError(
            title: "\(serviceName) Unavailable",
            message: error.localizedDescription,
            severity: severity,
            category: .service,
            context: serviceName,
            userFacingMessage: createUserFacingMessage(for: serviceName, error: error, circuitBreaker: circuitBreaker),
            technicalDetails: "Service: \(serviceName), Circuit Breaker: \(circuitBreaker.state), Error: \(error)",
            suggestedActions: createSuggestedActions(for: serviceName, criticalityLevel: criticalityLevel, circuitBreaker: circuitBreaker)
        )
        
        // Only show error for critical services or when circuit breaker opens
        if criticalityLevel == .high || circuitBreaker.state == .open {
            GlobalErrorManager.shared.showError(appError)
        }
        
        // Trigger fallback mechanisms
        await triggerFallbackMechanisms(for: serviceName, criticalityLevel: criticalityLevel)
    }
    
    private func handleServiceStatusChange(_ serviceName: String, from previousStatus: ServiceStatus, to newStatus: ServiceStatus, error: Error?) {
        switch (previousStatus, newStatus) {
        case (_, .healthy):
            if previousStatus != .healthy && previousStatus != .unknown {
                // Service recovered
                let success = AppError(
                    title: "\(serviceName) Restored",
                    message: "\(serviceName) is now operational",
                    severity: .info,
                    category: .service,
                    context: serviceName,
                    autoDismissDelay: 3.0
                )
                GlobalErrorManager.shared.showError(success)
            }
            
        case (.healthy, .failed), (.degraded, .failed):
            // Service completely failed
            triggerCriticalServiceFailure(serviceName)
            
        default:
            break
        }
    }
    
    private func triggerCriticalServiceFailure(_ serviceName: String) {
        guard let serviceInfo = serviceHealthStatus[serviceName],
              serviceInfo.configuration.criticalityLevel == .high else { return }
        
        let error = AppError(
            title: "Critical Service Failed",
            message: "\(serviceName) is not responding",
            severity: .critical,
            category: .service,
            context: serviceName,
            userFacingMessage: "A critical service is unavailable. Some features may not work properly.",
            suggestedActions: [
                ErrorAction(title: "Use Offline Mode", systemImage: "wifi.slash", isPrimary: true) {
                    GlobalErrorManager.shared.enableOfflineMode()
                },
                ErrorAction(title: "Check Connection", systemImage: "wifi") {
                    Task { @MainActor in
                        await NetworkErrorHandler.shared.checkConnectionQuality()
                    }
                }
            ]
        )
        
        GlobalErrorManager.shared.showError(error)
    }
    
    // MARK: - Fallback Mechanisms
    
    private func triggerFallbackMechanisms(for serviceName: String, criticalityLevel: ServiceCriticality) async {
        switch serviceName {
        case "TaskService":
            NotificationCenter.default.post(name: .taskServiceFallback, object: nil)
        case "WebSocketService":
            NotificationCenter.default.post(name: .webSocketFallback, object: nil)
        case "BackendSettingsService":
            NotificationCenter.default.post(name: .settingsServiceFallback, object: nil)
        case "ArchitectureVisualizationService":
            NotificationCenter.default.post(name: .architectureServiceFallback, object: nil)
        default:
            break
        }
    }
    
    // MARK: - Recovery Actions
    
    func retryService(_ serviceName: String) async {
        guard let circuitBreaker = circuitBreakers[serviceName] else { return }
        
        // Reset circuit breaker for manual retry
        circuitBreaker.reset()
        
        // Immediately perform health check
        await performHealthCheck(for: serviceName)
    }
    
    func forceServiceRecovery(_ serviceName: String) {
        guard let circuitBreaker = circuitBreakers[serviceName] else { return }
        
        // Force circuit breaker closed
        circuitBreaker.forceClose()
        
        // Reset retry attempts
        serviceRetryAttempts[serviceName] = 0
        
        // Schedule immediate health check
        Task { @MainActor in
            await performHealthCheck(for: serviceName)
        }
    }
    
    // MARK: - Network Event Handlers
    
    private func handleNetworkRestored() {
        // Reset all circuit breakers
        for circuitBreaker in circuitBreakers.values {
            if circuitBreaker.state == .open {
                circuitBreaker.state = .halfOpen
            }
        }
        
        // Trigger health checks for all services
        for serviceName in serviceHealthStatus.keys {
            Task { @MainActor in
                await performHealthCheck(for: serviceName)
            }
        }
    }
    
    private func handleNetworkLost() {
        // Mark all services as unknown since network is down
        for serviceName in serviceHealthStatus.keys {
            updateServiceStatus(serviceName, status: .unknown, responseTime: 0, error: nil)
        }
    }
    
    // MARK: - Helper Methods
    
    private func createUserFacingMessage(for serviceName: String, error: Error, circuitBreaker: CircuitBreaker) -> String {
        if circuitBreaker.state == .open {
            return "\(serviceName) is temporarily unavailable. Using local data where possible."
        }
        
        switch serviceName {
        case "TaskService":
            return "Task synchronization is temporarily unavailable. Your changes are saved locally."
        case "WebSocketService":
            return "Real-time updates are temporarily unavailable. Data will refresh periodically."
        case "BackendSettingsService":
            return "Settings sync is temporarily unavailable. Using local settings."
        case "ArchitectureVisualizationService":
            return "Architecture diagrams may be outdated. Refresh when connection improves."
        case "VoiceService":
            return "Voice features are temporarily unavailable."
        case "MetricsService":
            return "Performance metrics are temporarily unavailable."
        default:
            return "\(serviceName) is temporarily unavailable."
        }
    }
    
    private func createSuggestedActions(for serviceName: String, criticalityLevel: ServiceCriticality, circuitBreaker: CircuitBreaker) -> [ErrorAction] {
        var actions: [ErrorAction] = []
        
        // Always offer retry for failed services
        actions.append(
            ErrorAction(title: "Retry", systemImage: "arrow.clockwise", isPrimary: true) {
                Task { @MainActor in
                    await ServiceErrorHandler.shared.retryService(serviceName)
                }
            }
        )
        
        // Offer specific actions based on service type
        switch serviceName {
        case "TaskService":
            actions.append(
                ErrorAction(title: "Work Offline", systemImage: "internaldrive") {
                    NotificationCenter.default.post(name: .taskServiceFallback, object: nil)
                }
            )
        case "WebSocketService":
            actions.append(
                ErrorAction(title: "Use Polling", systemImage: "arrow.clockwise") {
                    NotificationCenter.default.post(name: .webSocketFallback, object: nil)
                }
            )
        default:
            break
        }
        
        // For critical services, offer network diagnostics
        if criticalityLevel == .high {
            actions.append(
                ErrorAction(title: "Check Network", systemImage: "wifi") {
                    Task { @MainActor in
                        await NetworkErrorHandler.shared.checkConnectionQuality()
                    }
                }
            )
        }
        
        return actions
    }
    
    // MARK: - Public Interface
    
    func getServiceHealth(_ serviceName: String) -> ServiceHealthInfo? {
        return serviceHealthStatus[serviceName]
    }
    
    func getAllServiceHealth() -> [String: ServiceHealthInfo] {
        return serviceHealthStatus
    }
    
    func getCriticalServices() -> [String] {
        return serviceHealthStatus.compactMap { name, info in
            info.configuration.criticalityLevel == .high ? name : nil
        }
    }
    
    func getFailedCriticalServices() -> [String] {
        return getCriticalServices().filter { failedServices.contains($0) }
    }
}

// MARK: - Supporting Types

struct ServiceConfiguration {
    let healthEndpoint: String
    let criticalityLevel: ServiceCriticality
    let healthCheckInterval: TimeInterval
    let timeoutInterval: TimeInterval
}

struct ServiceHealthInfo {
    let name: String
    var status: ServiceStatus
    let configuration: ServiceConfiguration
    var lastCheck: Date?
    var lastError: Error?
    var responseTime: TimeInterval?
}

enum ServiceCriticality: String, CaseIterable {
    case high = "high"
    case medium = "medium"
    case low = "low"
    
    var displayName: String {
        switch self {
        case .high: return "Critical"
        case .medium: return "Important"
        case .low: return "Optional"
        }
    }
}

enum ServiceError: LocalizedError {
    case backendNotConfigured
    case invalidConfiguration
    case invalidResponse
    case serviceUnavailable
    
    var errorDescription: String? {
        switch self {
        case .backendNotConfigured:
            return "Backend is not configured"
        case .invalidConfiguration:
            return "Invalid service configuration"
        case .invalidResponse:
            return "Invalid response from service"
        case .serviceUnavailable:
            return "Service is currently unavailable"
        }
    }
}

// MARK: - Circuit Breaker Pattern

class CircuitBreaker {
    enum State {
        case closed
        case open
        case halfOpen
    }
    
    var state: State = .closed
    private let failureThreshold: Int
    private let recoveryTimeout: TimeInterval
    private var failureCount: Int = 0
    private var lastFailureTime: Date?
    
    init(failureThreshold: Int, recoveryTimeout: TimeInterval) {
        self.failureThreshold = failureThreshold
        self.recoveryTimeout = recoveryTimeout
    }
    
    func recordSuccess() {
        failureCount = 0
        state = .closed
        lastFailureTime = nil
    }
    
    func recordFailure() {
        failureCount += 1
        lastFailureTime = Date()
        
        if failureCount >= failureThreshold {
            state = .open
        }
    }
    
    func shouldAttemptReset() -> Bool {
        guard let lastFailure = lastFailureTime else { return false }
        return Date().timeIntervalSince(lastFailure) >= recoveryTimeout
    }
    
    func reset() {
        failureCount = 0
        state = .closed
        lastFailureTime = nil
    }
    
    func forceClose() {
        state = .closed
        failureCount = 0
        lastFailureTime = nil
    }
}

// MARK: - Notification Extensions

extension Notification.Name {
    static let taskServiceFallback = Notification.Name("taskServiceFallback")
    static let webSocketFallback = Notification.Name("webSocketFallback")
    static let settingsServiceFallback = Notification.Name("settingsServiceFallback")
    static let architectureServiceFallback = Notification.Name("architectureServiceFallback")
}