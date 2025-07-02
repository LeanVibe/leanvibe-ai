import SwiftUI
import Combine

// MARK: - Performance Analytics Integration

@available(iOS 18.0, macOS 14.0, *)
@MainActor
class PerformanceAnalytics: ObservableObject {
    @Published var metrics = AnalyticsPerformanceMetrics()
    @Published var alerts: [PerformanceAlert] = []
    @Published var isMonitoring = false
    @Published var optimizationRecommendations: [OptimizationRecommendation] = []
    
    nonisolated(unsafe) private var displayLink: CADisplayLink?
    private var lastFrameTime: CFTimeInterval = 0
    private var frameCount = 0
    private var performanceHistory: [PerformanceSnapshot] = []
    
    // Auto-optimization settings
    private let autoOptimizationEnabled = true
    private let frameRateThreshold: Double = 50
    private let memoryThreshold: Double = 200 // MB
    private let batteryThreshold: Float = 0.2 // 20%
    
    init() {
        setupPerformanceMonitoring()
    }
    
    deinit {
        displayLink?.invalidate()
        displayLink = nil
        NotificationCenter.default.removeObserver(self)
    }
    
    // MARK: - Performance Monitoring
    
    func startPerformanceMonitoring() {
        guard !isMonitoring else { return }
        
        isMonitoring = true
        
        displayLink = CADisplayLink(target: self, selector: #selector(frameUpdate))
        displayLink?.add(to: .main, forMode: .common)
        
        // Start continuous monitoring
        Timer.scheduledTimer(withTimeInterval: 5.0, repeats: true) { [weak self] _ in
            Task { await self?.updateDetailedMetrics() }
        }
        
        print("📊 Performance Analytics: Monitoring started")
    }
    
    func stopPerformanceMonitoring() {
        displayLink?.invalidate()
        displayLink = nil
        isMonitoring = false
        
        print("📊 Performance Analytics: Monitoring stopped")
    }
    
    private func setupPerformanceMonitoring() {
        // Setup memory warning observer
        NotificationCenter.default.addObserver(
            forName: UIApplication.didReceiveMemoryWarningNotification,
            object: nil,
            queue: .main
        ) { [weak self] _ in
            Task { await self?.handleMemoryWarning() }
        }
        
        // Setup background/foreground observers
        NotificationCenter.default.addObserver(
            forName: UIApplication.didEnterBackgroundNotification,
            object: nil,
            queue: .main
        ) { [weak self] _ in
            Task { await self?.handleBackgroundTransition() }
        }
        
        NotificationCenter.default.addObserver(
            forName: UIApplication.willEnterForegroundNotification,
            object: nil,
            queue: .main
        ) { [weak self] _ in
            Task { await self?.handleForegroundTransition() }
        }
    }
    
    @objc private func frameUpdate(displayLink: CADisplayLink) {
        let currentTime = displayLink.timestamp
        
        if lastFrameTime > 0 {
            let frameDuration = currentTime - lastFrameTime
            let currentFrameRate = 1.0 / frameDuration
            
            // Update frame rate with exponential moving average
            metrics.frameRate = metrics.frameRate * 0.9 + currentFrameRate * 0.1
            
            // Count dropped frames
            if frameDuration > 1.0/60.0 + 0.002 { // 2ms tolerance for 60fps
                metrics.droppedFrames += 1
            }
            
            // Auto-optimize if performance drops
            if autoOptimizationEnabled && metrics.frameRate < frameRateThreshold {
                applyPerformanceOptimizations()
            }
        }
        
        lastFrameTime = currentTime
        frameCount += 1
        
        // Reset counters and create snapshot every second
        if frameCount >= 60 {
            createPerformanceSnapshot()
            frameCount = 0
            metrics.droppedFrames = max(0, metrics.droppedFrames - 1) // Gradual recovery
        }
    }
    
    private func updateDetailedMetrics() {
        // Update memory usage
        metrics.memoryUsage = getCurrentMemoryUsage()
        
        // Update battery usage
        metrics.batteryLevel = UIDevice.current.batteryLevel
        metrics.isLowPowerModeEnabled = ProcessInfo.processInfo.isLowPowerModeEnabled
        
        // Update network metrics
        updateNetworkMetrics()
        
        // Update voice response time
        updateVoiceMetrics()
        
        // Check for performance issues
        analyzePerformanceIssues()
        
        // Generate recommendations
        generateOptimizationRecommendations()
    }
    
    private func createPerformanceSnapshot() {
        let snapshot = PerformanceSnapshot(
            timestamp: Date(),
            frameRate: metrics.frameRate,
            memoryUsage: metrics.memoryUsage,
            batteryLevel: metrics.batteryLevel,
            networkLatency: metrics.networkLatency,
            voiceResponseTime: metrics.voiceResponseTime
        )
        
        performanceHistory.append(snapshot)
        
        // Keep only last 100 snapshots (about 1.7 minutes at 1 snapshot/second)
        if performanceHistory.count > 100 {
            performanceHistory.removeFirst()
        }
    }
    
    // MARK: - Metrics Collection
    
    private func getCurrentMemoryUsage() -> Double {
        var info = mach_task_basic_info()
        var count = mach_msg_type_number_t(MemoryLayout<mach_task_basic_info>.size)/4
        
        let kerr: kern_return_t = withUnsafeMutablePointer(to: &info) {
            $0.withMemoryRebound(to: integer_t.self, capacity: 1) {
                task_info(mach_task_self_,
                         task_flavor_t(MACH_TASK_BASIC_INFO),
                         $0,
                         &count)
            }
        }
        
        if kerr == KERN_SUCCESS {
            return Double(info.resident_size) / 1024.0 / 1024.0
        }
        return 0
    }
    
    private func updateNetworkMetrics() {
        // This would integrate with actual network monitoring
        // For now, using mock data
        metrics.networkLatency = Double.random(in: 50...200) // ms
    }
    
    private func updateVoiceMetrics() {
        // This would integrate with VoiceManager
        // For now, using mock data
        metrics.voiceResponseTime = Double.random(in: 0.2...0.8) // seconds
    }
    
    // MARK: - Performance Analysis
    
    private func analyzePerformanceIssues() {
        var newAlerts: [PerformanceAlert] = []
        
        // Memory analysis
        if metrics.memoryUsage > memoryThreshold {
            newAlerts.append(PerformanceAlert(
                type: .highMemory,
                severity: metrics.memoryUsage > memoryThreshold * 1.5 ? .critical : .warning,
                message: "High memory usage: \(String(format: "%.1f", metrics.memoryUsage))MB",
                recommendation: "Consider clearing caches or reducing concurrent operations"
            ))
        }
        
        // Frame rate analysis
        if metrics.frameRate < frameRateThreshold {
            newAlerts.append(PerformanceAlert(
                type: .lowFrameRate,
                severity: metrics.frameRate < 30 ? .critical : .warning,
                message: "Low frame rate: \(String(format: "%.1f", metrics.frameRate))fps",
                recommendation: "Reduce animation complexity or enable performance mode"
            ))
        }
        
        // Battery analysis
        if metrics.batteryLevel < batteryThreshold && !metrics.isLowPowerModeEnabled {
            newAlerts.append(PerformanceAlert(
                type: .lowBattery,
                severity: .warning,
                message: "Low battery: \(String(format: "%.0f", metrics.batteryLevel * 100))%",
                recommendation: "Consider enabling battery optimization mode"
            ))
        }
        
        // Voice response analysis
        if metrics.voiceResponseTime > 1.0 {
            newAlerts.append(PerformanceAlert(
                type: .slowVoiceResponse,
                severity: .warning,
                message: "Slow voice response: \(String(format: "%.2f", metrics.voiceResponseTime))s",
                recommendation: "Optimize voice processing or check audio permissions"
            ))
        }
        
        // Update alerts (keep only recent ones)
        alerts = (alerts + newAlerts).suffix(10).map { $0 }
    }
    
    private func generateOptimizationRecommendations() {
        var recommendations: [OptimizationRecommendation] = []
        
        // Memory optimization recommendations
        if metrics.memoryUsage > memoryThreshold * 0.8 {
            recommendations.append(OptimizationRecommendation(
                category: .memory,
                priority: .medium,
                title: "Memory Usage Optimization",
                description: "Memory usage is approaching limits. Consider implementing lazy loading and caching optimizations.",
                impact: .moderate,
                implementationComplexity: .low
            ))
        }
        
        // Animation optimization recommendations
        if metrics.frameRate < 55 {
            recommendations.append(OptimizationRecommendation(
                category: .animation,
                priority: .high,
                title: "Animation Performance",
                description: "Frame rate is below optimal. Consider reducing animation complexity or using hardware acceleration.",
                impact: .high,
                implementationComplexity: .medium
            ))
        }
        
        // Battery optimization recommendations
        if metrics.isLowPowerModeEnabled {
            recommendations.append(OptimizationRecommendation(
                category: .battery,
                priority: .high,
                title: "Low Power Mode Optimization",
                description: "Device is in low power mode. Reduce background processing and lower refresh rates.",
                impact: .high,
                implementationComplexity: .low
            ))
        }
        
        // Network optimization recommendations
        if metrics.networkLatency > 500 {
            recommendations.append(OptimizationRecommendation(
                category: .network,
                priority: .medium,
                title: "Network Performance",
                description: "High network latency detected. Consider implementing request batching and local caching.",
                impact: .moderate,
                implementationComplexity: .medium
            ))
        }
        
        optimizationRecommendations = recommendations
    }
    
    // MARK: - Auto-Optimization
    
    private func applyPerformanceOptimizations() {
        guard autoOptimizationEnabled else { return }
        
        // Reduce animation complexity
        NotificationCenter.default.post(
            name: .performanceOptimizationRequired,
            object: PerformanceOptimizationSettings(
                enableReducedMotion: true,
                reducedUpdateFrequency: true,
                enableMemoryCleanup: metrics.memoryUsage > memoryThreshold
            )
        )
        
        // Add optimization alert
        alerts.append(PerformanceAlert(
            type: .optimization,
            severity: .info,
            message: "Performance optimizations applied automatically",
            recommendation: "Optimizations have been enabled to maintain smooth performance"
        ))
        
        print("📊 Performance Analytics: Auto-optimizations applied")
    }
    
    // MARK: - Event Handlers
    
    private func handleMemoryWarning() {
        metrics.memoryWarnings += 1
        
        alerts.append(PerformanceAlert(
            type: .memoryWarning,
            severity: .critical,
            message: "System memory warning received",
            recommendation: "Immediate memory cleanup required"
        ))
        
        // Trigger aggressive cleanup
        NotificationCenter.default.post(name: .memoryWarningReceived, object: nil)
    }
    
    private func handleBackgroundTransition() {
        metrics.backgroundTransitions += 1
        
        // Reduce monitoring frequency in background
        displayLink?.preferredFramesPerSecond = 30
    }
    
    private func handleForegroundTransition() {
        metrics.foregroundTransitions += 1
        
        // Resume normal monitoring frequency
        displayLink?.preferredFramesPerSecond = 60
        
        // Re-evaluate performance after background time
        updateDetailedMetrics()
    }
    
    // MARK: - Performance Reports
    
    func generatePerformanceReport() -> PerformanceReport {
        let averageFrameRate = performanceHistory.isEmpty ? metrics.frameRate :
            performanceHistory.map { $0.frameRate }.reduce(0, +) / Double(performanceHistory.count)
        
        let averageMemoryUsage = performanceHistory.isEmpty ? metrics.memoryUsage :
            performanceHistory.map { $0.memoryUsage }.reduce(0, +) / Double(performanceHistory.count)
        
        return PerformanceReport(
            currentMetrics: metrics,
            averageFrameRate: averageFrameRate,
            averageMemoryUsage: averageMemoryUsage,
            totalAlerts: alerts.count,
            criticalAlerts: alerts.filter { $0.severity == .critical }.count,
            optimizationRecommendations: optimizationRecommendations.count,
            performanceScore: calculatePerformanceScore(),
            monitoringDuration: isMonitoring ? Date().timeIntervalSince(Date()) : 0
        )
    }
    
    private func calculatePerformanceScore() -> Double {
        var score: Double = 100
        
        // Frame rate impact (30% weight)
        let frameRateScore = min(metrics.frameRate / 60.0, 1.0) * 30
        
        // Memory impact (25% weight)
        let memoryScore = max(0, (300 - metrics.memoryUsage) / 300) * 25
        
        // Battery impact (20% weight)
        let batteryScore = Double(metrics.batteryLevel) * 20
        
        // Voice response impact (15% weight)
        let voiceScore = max(0, (2.0 - metrics.voiceResponseTime) / 2.0) * 15
        
        // Network impact (10% weight)
        let networkScore = max(0, (1000 - metrics.networkLatency) / 1000) * 10
        
        score = frameRateScore + memoryScore + batteryScore + voiceScore + networkScore
        
        return max(0, min(100, score))
    }
    
    // MARK: - Manual Optimization
    
    func optimizePerformance() {
        applyPerformanceOptimizations()
        
        // Clear old performance history
        if performanceHistory.count > 50 {
            performanceHistory = Array(performanceHistory.suffix(50))
        }
        
        // Clear old alerts
        alerts = alerts.filter { alert in
            Date().timeIntervalSince(alert.timestamp) < 300 // Keep last 5 minutes
        }
    }
    
    func clearAlerts() {
        alerts.removeAll()
    }
    
    func dismissAlert(_ alert: PerformanceAlert) {
        alerts.removeAll { $0.id == alert.id }
    }
}

// MARK: - Supporting Types

struct AnalyticsPerformanceMetrics {
    var frameRate: Double = 60.0
    var droppedFrames: Int = 0
    var memoryUsage: Double = 0.0
    var batteryLevel: Float = 1.0
    var isLowPowerModeEnabled = false
    var networkLatency: Double = 0.0
    var voiceResponseTime: Double = 0.0
    var memoryWarnings = 0
    var backgroundTransitions = 0
    var foregroundTransitions = 0
}

struct PerformanceSnapshot {
    let timestamp: Date
    let frameRate: Double
    let memoryUsage: Double
    let batteryLevel: Float
    let networkLatency: Double
    let voiceResponseTime: Double
}

struct PerformanceAlert: Identifiable {
    let id = UUID()
    let type: AlertType
    let severity: Severity
    let message: String
    let recommendation: String
    let timestamp = Date()
    
    enum AlertType {
        case highMemory
        case lowFrameRate
        case lowBattery
        case slowVoiceResponse
        case memoryWarning
        case optimization
    }
    
    enum Severity {
        case info, warning, critical
        
        var color: Color {
            switch self {
            case .info: return .blue
            case .warning: return .orange
            case .critical: return .red
            }
        }
        
        var icon: String {
            switch self {
            case .info: return "info.circle"
            case .warning: return "exclamationmark.triangle"
            case .critical: return "xmark.octagon"
            }
        }
    }
}

struct OptimizationRecommendation: Identifiable {
    let id = UUID()
    let category: Category
    let priority: Priority
    let title: String
    let description: String
    let impact: Impact
    let implementationComplexity: Complexity
    
    enum Category {
        case memory, animation, battery, network, voice
        
        var icon: String {
            switch self {
            case .memory: return "memorychip"
            case .animation: return "wand.and.rays"
            case .battery: return "battery.100"
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
    
    enum Impact {
        case low, moderate, high
    }
    
    enum Complexity {
        case low, medium, high
    }
}

struct PerformanceReport {
    let currentMetrics: AnalyticsPerformanceMetrics
    let averageFrameRate: Double
    let averageMemoryUsage: Double
    let totalAlerts: Int
    let criticalAlerts: Int
    let optimizationRecommendations: Int
    let performanceScore: Double
    let monitoringDuration: TimeInterval
    
    var status: PerformanceStatus {
        if performanceScore >= 80 {
            return .excellent
        } else if performanceScore >= 60 {
            return .good
        } else {
            return .needsImprovement
        }
    }
    
    enum PerformanceStatus {
        case excellent, good, needsImprovement
        
        var description: String {
            switch self {
            case .excellent: return "Excellent Performance"
            case .good: return "Good Performance"
            case .needsImprovement: return "Needs Improvement"
            }
        }
        
        var color: Color {
            switch self {
            case .excellent: return .green
            case .good: return .orange
            case .needsImprovement: return .red
            }
        }
    }
}

struct PerformanceOptimizationSettings {
    let enableReducedMotion: Bool
    let reducedUpdateFrequency: Bool
    let enableMemoryCleanup: Bool
}

// MARK: - Notification Extensions

extension Notification.Name {
    static let performanceOptimizationRequired = Notification.Name("performanceOptimizationRequired")
    static let memoryWarningReceived = Notification.Name("memoryWarningReceived")
}