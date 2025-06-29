import SwiftUI
import Combine

// MARK: - Integrated Performance Management System

@MainActor
class IntegratedPerformanceManager: ObservableObject {
    @Published var performanceState: PerformanceState = .optimal
    @Published var optimizationLevel: OptimizationLevel = .none
    @Published var systemHealth: SystemHealth = .excellent
    @Published var alerts: [SystemAlert] = []
    
    // Sub-managers
    private let performanceAnalytics: PerformanceAnalytics
    private let batteryManager: BatteryOptimizedManager
    private let memoryManager: OptimizedArchitectureService
    private let voiceManager: OptimizedVoiceManager
    private let networkManager: OptimizedWebSocketService
    
    private var cancellables = Set<AnyCancellable>()
    private var monitoringTimer: Timer?
    
    enum PerformanceState {
        case optimal
        case good
        case degraded
        case critical
        
        var description: String {
            switch self {
            case .optimal: return "Optimal Performance"
            case .good: return "Good Performance"
            case .degraded: return "Degraded Performance"
            case .critical: return "Critical Performance"
            }
        }
        
        var color: Color {
            switch self {
            case .optimal: return .green
            case .good: return .blue
            case .degraded: return .orange
            case .critical: return .red
            }
        }
    }
    
    enum OptimizationLevel {
        case none
        case light
        case moderate
        case aggressive
        
        var description: String {
            switch self {
            case .none: return "No Optimization"
            case .light: return "Light Optimization"
            case .moderate: return "Moderate Optimization"
            case .aggressive: return "Aggressive Optimization"
            }
        }
    }
    
    enum SystemHealth {
        case excellent
        case good
        case fair
        case poor
        
        var description: String {
            switch self {
            case .excellent: return "Excellent System Health"
            case .good: return "Good System Health"
            case .fair: return "Fair System Health"
            case .poor: return "Poor System Health"
            }
        }
        
        var color: Color {
            switch self {
            case .excellent: return .green
            case .good: return .blue
            case .fair: return .orange
            case .poor: return .red
            }
        }
    }
    
    init(
        performanceAnalytics: PerformanceAnalytics,
        batteryManager: BatteryOptimizedManager,
        memoryManager: OptimizedArchitectureService,
        voiceManager: OptimizedVoiceManager,
        networkManager: OptimizedWebSocketService
    ) {
        self.performanceAnalytics = performanceAnalytics
        self.batteryManager = batteryManager
        self.memoryManager = memoryManager
        self.voiceManager = voiceManager
        self.networkManager = networkManager
        
        setupIntegrationSubscriptions()
        startIntegratedMonitoring()
    }
    
    deinit {
        stopIntegratedMonitoring()
    }
    
    // MARK: - Integration Setup
    
    private func setupIntegrationSubscriptions() {
        // Battery optimization subscription
        batteryManager.$optimizationLevel
            .sink { [weak self] level in
                self?.handleBatteryOptimizationChange(level)
            }
            .store(in: &cancellables)
        
        // Performance analytics subscription
        performanceAnalytics.$metrics
            .sink { [weak self] metrics in
                self?.handlePerformanceMetricsUpdate(metrics)
            }
            .store(in: &cancellables)
        
        // Memory optimization subscription
        memoryManager.$isOptimized
            .sink { [weak self] optimized in
                self?.handleMemoryOptimizationChange(optimized)
            }
            .store(in: &cancellables)
        
        // Voice performance subscription
        voiceManager.$currentLatency
            .sink { [weak self] latency in
                self?.handleVoiceLatencyChange(latency)
            }
            .store(in: &cancellables)
        
        // Network performance subscription
        networkManager.$isOptimized
            .sink { [weak self] optimized in
                self?.handleNetworkOptimizationChange(optimized)
            }
            .store(in: &cancellables)
    }
    
    private func startIntegratedMonitoring() {
        monitoringTimer = Timer.scheduledTimer(withTimeInterval: 5.0, repeats: true) { [weak self] _ in
            self?.evaluateSystemHealth()
            self?.optimizeSystemPerformance()
            self?.generateSystemRecommendations()
        }
    }
    
    private func stopIntegratedMonitoring() {
        monitoringTimer?.invalidate()
        monitoringTimer = nil
    }
    
    // MARK: - Performance Integration Logic
    
    private func handleBatteryOptimizationChange(_ level: BatteryOptimizedManager.OptimizationLevel) {
        // Cascade battery optimization to other systems
        switch level {
        case .none:
            optimizationLevel = .none
            notifySubsystemsOptimizationLevel(.none)
        case .light:
            optimizationLevel = .light
            notifySubsystemsOptimizationLevel(.light)
        case .moderate:
            optimizationLevel = .moderate
            notifySubsystemsOptimizationLevel(.moderate)
        case .aggressive:
            optimizationLevel = .aggressive
            notifySubsystemsOptimizationLevel(.aggressive)
        }
        
        addAlert(.info, "Battery optimization level changed to \(level.description)")
    }
    
    private func handlePerformanceMetricsUpdate(_ metrics: PerformanceMetrics) {
        // Update performance state based on key metrics
        let frameRateScore = metrics.frameRate / 60.0
        let memoryScore = max(0, (300 - metrics.memoryUsage) / 300)
        let voiceScore = max(0, (2.0 - metrics.voiceResponseTime) / 2.0)
        
        let overallScore = (frameRateScore + memoryScore + voiceScore) / 3.0
        
        let newState: PerformanceState
        if overallScore >= 0.9 {
            newState = .optimal
        } else if overallScore >= 0.7 {
            newState = .good
        } else if overallScore >= 0.5 {
            newState = .degraded
        } else {
            newState = .critical
        }
        
        if newState != performanceState {
            performanceState = newState
            handlePerformanceStateChange(newState)
        }
    }
    
    private func handleMemoryOptimizationChange(_ optimized: Bool) {
        if optimized {
            addAlert(.info, "Memory optimization enabled")
        } else {
            addAlert(.info, "Memory optimization disabled")
        }
    }
    
    private func handleVoiceLatencyChange(_ latency: TimeInterval) {
        if latency > 1.0 {
            addAlert(.warning, "Voice response time is high: \(String(format: "%.2f", latency))s")
            
            // Auto-optimize voice system
            Task {
                await voiceManager.optimizeForPerformance()
            }
        }
    }
    
    private func handleNetworkOptimizationChange(_ optimized: Bool) {
        if optimized {
            addAlert(.info, "Network optimization enabled")
        }
    }
    
    private func handlePerformanceStateChange(_ state: PerformanceState) {
        switch state {
        case .optimal:
            PremiumHaptics.successNotification()
            addAlert(.success, "System performance is optimal")
        case .good:
            addAlert(.info, "System performance is good")
        case .degraded:
            PremiumHaptics.warningNotification()
            addAlert(.warning, "System performance is degraded")
            triggerAutomaticOptimization()
        case .critical:
            PremiumHaptics.errorNotification()
            addAlert(.critical, "Critical performance issues detected")
            triggerEmergencyOptimization()
        }
    }
    
    // MARK: - System Health Evaluation
    
    private func evaluateSystemHealth() {
        let batteryHealth = evaluateBatteryHealth()
        let memoryHealth = evaluateMemoryHealth()
        let performanceHealth = evaluatePerformanceHealth()
        let networkHealth = evaluateNetworkHealth()
        
        let overallHealth = (batteryHealth + memoryHealth + performanceHealth + networkHealth) / 4.0
        
        let newSystemHealth: SystemHealth
        if overallHealth >= 0.9 {
            newSystemHealth = .excellent
        } else if overallHealth >= 0.7 {
            newSystemHealth = .good
        } else if overallHealth >= 0.5 {
            newSystemHealth = .fair
        } else {
            newSystemHealth = .poor
        }
        
        if newSystemHealth != systemHealth {
            systemHealth = newSystemHealth
        }
    }
    
    private func evaluateBatteryHealth() -> Double {
        if batteryManager.batteryLevel > 0.7 && !batteryManager.isLowPowerModeEnabled {
            return 1.0
        } else if batteryManager.batteryLevel > 0.3 {
            return 0.7
        } else if batteryManager.batteryLevel > 0.1 {
            return 0.5
        } else {
            return 0.2
        }
    }
    
    private func evaluateMemoryHealth() -> Double {
        let currentMemory = performanceAnalytics.metrics.memoryUsage
        if currentMemory < 150 {
            return 1.0
        } else if currentMemory < 200 {
            return 0.7
        } else if currentMemory < 250 {
            return 0.5
        } else {
            return 0.2
        }
    }
    
    private func evaluatePerformanceHealth() -> Double {
        let frameRate = performanceAnalytics.metrics.frameRate
        if frameRate >= 58 {
            return 1.0
        } else if frameRate >= 45 {
            return 0.7
        } else if frameRate >= 30 {
            return 0.5
        } else {
            return 0.2
        }
    }
    
    private func evaluateNetworkHealth() -> Double {
        let latency = performanceAnalytics.metrics.networkLatency
        if latency < 100 {
            return 1.0
        } else if latency < 300 {
            return 0.7
        } else if latency < 500 {
            return 0.5
        } else {
            return 0.2
        }
    }
    
    // MARK: - Optimization Strategies
    
    private func optimizeSystemPerformance() {
        // Intelligent optimization based on current state
        switch performanceState {
        case .optimal:
            // Maintain current state, no action needed
            break
        case .good:
            // Light optimizations to prevent degradation
            applyLightOptimizations()
        case .degraded:
            // Moderate optimizations to improve performance
            applyModerateOptimizations()
        case .critical:
            // Aggressive optimizations to restore functionality
            applyAggressiveOptimizations()
        }
    }
    
    private func applyLightOptimizations() {
        NotificationCenter.default.post(
            name: .integratedOptimizationRequired,
            object: IntegratedOptimizationSettings(
                level: .light,
                enableMemoryCleanup: false,
                reduceAnimationComplexity: false,
                optimizeVoiceProcessing: true,
                enableNetworkBatching: false
            )
        )
    }
    
    private func applyModerateOptimizations() {
        NotificationCenter.default.post(
            name: .integratedOptimizationRequired,
            object: IntegratedOptimizationSettings(
                level: .moderate,
                enableMemoryCleanup: true,
                reduceAnimationComplexity: true,
                optimizeVoiceProcessing: true,
                enableNetworkBatching: true
            )
        )
    }
    
    private func applyAggressiveOptimizations() {
        NotificationCenter.default.post(
            name: .integratedOptimizationRequired,
            object: IntegratedOptimizationSettings(
                level: .aggressive,
                enableMemoryCleanup: true,
                reduceAnimationComplexity: true,
                optimizeVoiceProcessing: true,
                enableNetworkBatching: true
            )
        )
        
        // Force battery optimization
        batteryManager.optimizeForBatteryUsage()
    }
    
    private func triggerAutomaticOptimization() {
        optimizationLevel = .moderate
        applyModerateOptimizations()
        addAlert(.info, "Automatic performance optimization enabled")
    }
    
    private func triggerEmergencyOptimization() {
        optimizationLevel = .aggressive
        applyAggressiveOptimizations()
        addAlert(.warning, "Emergency performance optimization enabled")
    }
    
    // MARK: - Cross-System Communication
    
    private func notifySubsystemsOptimizationLevel(_ level: OptimizationLevel) {
        let settings = IntegratedOptimizationSettings(
            level: level,
            enableMemoryCleanup: level != .none,
            reduceAnimationComplexity: level == .moderate || level == .aggressive,
            optimizeVoiceProcessing: level != .none,
            enableNetworkBatching: level == .moderate || level == .aggressive
        )
        
        NotificationCenter.default.post(
            name: .integratedOptimizationRequired,
            object: settings
        )
    }
    
    private func generateSystemRecommendations() {
        // Generate cross-system optimization recommendations
        var recommendations: [SystemRecommendation] = []
        
        // Battery-based recommendations
        if batteryManager.batteryLevel < 0.3 {
            recommendations.append(SystemRecommendation(
                category: .battery,
                priority: .high,
                title: "Enable Battery Optimization",
                description: "Low battery detected. Enable aggressive power saving mode.",
                action: { [weak self] in
                    self?.batteryManager.optimizeForBatteryUsage()
                }
            ))
        }
        
        // Memory-based recommendations
        if performanceAnalytics.metrics.memoryUsage > 200 {
            recommendations.append(SystemRecommendation(
                category: .memory,
                priority: .medium,
                title: "Optimize Memory Usage",
                description: "High memory usage detected. Clear caches and optimize allocations.",
                action: { [weak self] in
                    Task {
                        await self?.memoryManager.optimizeMemoryUsage()
                    }
                }
            ))
        }
        
        // Performance-based recommendations
        if performanceAnalytics.metrics.frameRate < 50 {
            recommendations.append(SystemRecommendation(
                category: .performance,
                priority: .high,
                title: "Optimize Animation Performance",
                description: "Low frame rate detected. Reduce animation complexity.",
                action: { [weak self] in
                    self?.applyModerateOptimizations()
                }
            ))
        }
        
        // Update recommendations if they've changed
        // This would be sent to a recommendations manager
    }
    
    // MARK: - Alert Management
    
    private func addAlert(_ severity: AlertSeverity, _ message: String) {
        let alert = SystemAlert(
            severity: severity,
            message: message,
            timestamp: Date()
        )
        
        alerts.append(alert)
        
        // Keep only recent alerts
        if alerts.count > 20 {
            alerts = Array(alerts.suffix(20))
        }
        
        // Trigger haptic feedback for important alerts
        switch severity {
        case .success:
            PremiumHaptics.successNotification()
        case .warning:
            PremiumHaptics.warningNotification()
        case .critical:
            PremiumHaptics.errorNotification()
        case .info:
            break // No haptic for info alerts
        }
    }
    
    // MARK: - Public Interface
    
    func getSystemReport() -> IntegratedSystemReport {
        return IntegratedSystemReport(
            performanceState: performanceState,
            systemHealth: systemHealth,
            optimizationLevel: optimizationLevel,
            batteryReport: batteryManager.getBatteryReport(),
            performanceReport: performanceAnalytics.generatePerformanceReport(),
            alerts: alerts,
            timestamp: Date()
        )
    }
    
    func manualOptimization() {
        triggerAutomaticOptimization()
        addAlert(.info, "Manual optimization triggered")
    }
    
    func resetOptimizations() {
        optimizationLevel = .none
        notifySubsystemsOptimizationLevel(.none)
        batteryManager.disableOptimizations()
        addAlert(.info, "All optimizations reset")
    }
    
    func clearAlerts() {
        alerts.removeAll()
    }
}

// MARK: - Supporting Types

struct IntegratedOptimizationSettings {
    let level: IntegratedPerformanceManager.OptimizationLevel
    let enableMemoryCleanup: Bool
    let reduceAnimationComplexity: Bool
    let optimizeVoiceProcessing: Bool
    let enableNetworkBatching: Bool
}

struct SystemAlert: Identifiable {
    let id = UUID()
    let severity: AlertSeverity
    let message: String
    let timestamp: Date
    
    enum AlertSeverity {
        case info, success, warning, critical
        
        var color: Color {
            switch self {
            case .info: return .blue
            case .success: return .green
            case .warning: return .orange
            case .critical: return .red
            }
        }
        
        var icon: String {
            switch self {
            case .info: return "info.circle"
            case .success: return "checkmark.circle"
            case .warning: return "exclamationmark.triangle"
            case .critical: return "xmark.octagon"
            }
        }
    }
}

typealias AlertSeverity = SystemAlert.AlertSeverity

struct SystemRecommendation: Identifiable {
    let id = UUID()
    let category: Category
    let priority: Priority
    let title: String
    let description: String
    let action: () -> Void
    
    enum Category {
        case battery, memory, performance, network, voice
        
        var icon: String {
            switch self {
            case .battery: return "battery.100"
            case .memory: return "memorychip"
            case .performance: return "speedometer"
            case .network: return "network"
            case .voice: return "mic"
            }
        }
    }
    
    enum Priority {
        case low, medium, high
        
        var color: Color {
            switch self {
            case .low: return .green
            case .medium: return .orange
            case .high: return .red
            }
        }
    }
}

struct IntegratedSystemReport {
    let performanceState: IntegratedPerformanceManager.PerformanceState
    let systemHealth: IntegratedPerformanceManager.SystemHealth
    let optimizationLevel: IntegratedPerformanceManager.OptimizationLevel
    let batteryReport: BatteryReport
    let performanceReport: PerformanceReport
    let alerts: [SystemAlert]
    let timestamp: Date
    
    var overallScore: Double {
        let performanceScore = performanceReport.performanceScore
        let batteryScore = Double(batteryReport.currentLevel) * 100
        let healthScore: Double
        
        switch systemHealth {
        case .excellent: healthScore = 100
        case .good: healthScore = 75
        case .fair: healthScore = 50
        case .poor: healthScore = 25
        }
        
        return (performanceScore + batteryScore + healthScore) / 3.0
    }
    
    var status: String {
        if overallScore >= 80 {
            return "Excellent System Status"
        } else if overallScore >= 60 {
            return "Good System Status"
        } else if overallScore >= 40 {
            return "Fair System Status"
        } else {
            return "Poor System Status"
        }
    }
}

// MARK: - Notification Extensions

extension Notification.Name {
    static let integratedOptimizationRequired = Notification.Name("integratedOptimizationRequired")
}