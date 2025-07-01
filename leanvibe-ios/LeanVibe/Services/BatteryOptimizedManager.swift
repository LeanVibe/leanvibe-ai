import SwiftUI
import Combine

// MARK: - Battery-Aware Performance Management

@available(iOS 18.0, macOS 14.0, *)
@MainActor
class BatteryOptimizedManager: ObservableObject {
    @Published var batteryLevel: Float = 1.0
    @Published var isLowPowerModeEnabled = false
    @Published var batteryState: UIDevice.BatteryState = .unknown
    @Published var isOptimized = false
    @Published var optimizationLevel: OptimizationLevel = .none
    @Published var batteryUsageRate: Double = 0.0 // % per hour
    
    // Battery monitoring
    nonisolated(unsafe) private var batteryMonitoringTimer: Timer?
    private var batteryHistory: [BatterySnapshot] = []
    private let maxHistoryCount = 20 // Keep 20 snapshots (about 20 minutes)
    
    // Optimization settings
    private var originalSettings = OriginalSettings()
    private let batteryOptimizer = BatteryOptimizer()
    
    // Background task management
    private var backgroundTaskManager = BackgroundTaskManager()
    
    enum OptimizationLevel: CaseIterable {
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
        
        var batteryThreshold: Float {
            switch self {
            case .none: return 0.0
            case .light: return 0.5 // 50%
            case .moderate: return 0.3 // 30%
            case .aggressive: return 0.2 // 20%
            }
        }
    }
    
    init() {
        setupBatteryMonitoring()
        startBatteryTracking()
    }
    
    deinit {
        // Battery tracking will be stopped when the object is deallocated
        batteryMonitoringTimer?.invalidate()
    }
    
    // MARK: - Battery Monitoring Setup
    
    private func setupBatteryMonitoring() {
        UIDevice.current.isBatteryMonitoringEnabled = true
        
        // Initial battery state
        updateBatteryInfo()
        
        // Battery level change notifications
        NotificationCenter.default.addObserver(
            forName: UIDevice.batteryLevelDidChangeNotification,
            object: nil,
            queue: .main
        ) { [weak self] _ in
            Task { @MainActor in
                self?.updateBatteryInfo()
            }
        }
        
        // Battery state change notifications
        NotificationCenter.default.addObserver(
            forName: UIDevice.batteryStateDidChangeNotification,
            object: nil,
            queue: .main
        ) { [weak self] _ in
            Task { @MainActor in
                self?.updateBatteryInfo()
            }
        }
        
        // Low power mode notifications
        NotificationCenter.default.addObserver(
            forName: .NSProcessInfoPowerStateDidChange,
            object: nil,
            queue: .main
        ) { [weak self] _ in
            Task { @MainActor in
                self?.updatePowerModeStatus()
            }
        }
    }
    
    private func startBatteryTracking() {
        batteryMonitoringTimer = Timer.scheduledTimer(withTimeInterval: 60.0, repeats: true) { [weak self] _ in
            Task { @MainActor in
                self?.recordBatterySnapshot()
                self?.calculateBatteryUsageRate()
                self?.evaluateOptimizationNeeds()
            }
        }
    }
    
    private func stopBatteryTracking() {
        batteryMonitoringTimer?.invalidate()
        batteryMonitoringTimer = nil
        UIDevice.current.isBatteryMonitoringEnabled = false
    }
    
    // MARK: - Battery Information Updates
    
    private func updateBatteryInfo() {
        batteryLevel = UIDevice.current.batteryLevel
        batteryState = UIDevice.current.batteryState
        
        // Auto-optimize based on battery level
        evaluateOptimizationNeeds()
    }
    
    private func updatePowerModeStatus() {
        isLowPowerModeEnabled = ProcessInfo.processInfo.isLowPowerModeEnabled
        
        if isLowPowerModeEnabled {
            enableBatterySavingMode()
        } else if optimizationLevel == .aggressive {
            // Reduce optimization level when low power mode is disabled
            setOptimizationLevel(.moderate)
        }
    }
    
    private func recordBatterySnapshot() {
        let snapshot = BatterySnapshot(
            timestamp: Date(),
            batteryLevel: batteryLevel,
            batteryState: batteryState,
            isLowPowerMode: isLowPowerModeEnabled
        )
        
        batteryHistory.append(snapshot)
        
        // Keep only recent history
        if batteryHistory.count > maxHistoryCount {
            batteryHistory.removeFirst()
        }
    }
    
    private func calculateBatteryUsageRate() {
        guard batteryHistory.count >= 2 else { return }
        
        let recent = batteryHistory.suffix(5) // Last 5 minutes
        guard recent.count >= 2 else { return }
        
        let firstSnapshot = recent.first!
        let lastSnapshot = recent.last!
        
        let timeInterval = lastSnapshot.timestamp.timeIntervalSince(firstSnapshot.timestamp)
        let batteryDrop = firstSnapshot.batteryLevel - lastSnapshot.batteryLevel
        
        // Calculate usage rate per hour
        if timeInterval > 0 && batteryDrop > 0 {
            batteryUsageRate = Double(batteryDrop) / (timeInterval / 3600.0) * 100
        }
    }
    
    // MARK: - Optimization Logic
    
    private func evaluateOptimizationNeeds() {
        let newOptimizationLevel: OptimizationLevel
        
        if isLowPowerModeEnabled {
            newOptimizationLevel = .aggressive
        } else if batteryLevel < 0.1 { // 10%
            newOptimizationLevel = .aggressive
        } else if batteryLevel < 0.2 { // 20%
            newOptimizationLevel = .moderate
        } else if batteryLevel < 0.3 || batteryUsageRate > 20 { // 30% or high usage
            newOptimizationLevel = .light
        } else {
            newOptimizationLevel = .none
        }
        
        if newOptimizationLevel != optimizationLevel {
            setOptimizationLevel(newOptimizationLevel)
        }
    }
    
    func setOptimizationLevel(_ level: OptimizationLevel) {
        guard level != optimizationLevel else { return }
        
        // Store original settings before any optimization
        if optimizationLevel == .none && level != .none {
            originalSettings.capture()
        }
        
        optimizationLevel = level
        
        switch level {
        case .none:
            disableBatterySavingMode()
        case .light:
            enableLightOptimization()
        case .moderate:
            enableModerateOptimization()
        case .aggressive:
            enableBatterySavingMode()
        }
        
        isOptimized = level != .none
        
        print("🔋 Battery Manager: Optimization level set to \(level.description)")
    }
    
    // MARK: - Optimization Implementations
    
    private func enableLightOptimization() {
        batteryOptimizer.applyLightOptimizations()
        
        // Reduce voice processing frequency slightly
        NotificationCenter.default.post(
            name: .batteryOptimizationChanged,
            object: BatteryOptimizationSettings(
                level: .light,
                reduceVoiceProcessing: true,
                reduceAnimationFrameRate: false,
                enableBackgroundTaskLimiting: false,
                enableNetworkBatching: false
            )
        )
    }
    
    private func enableModerateOptimization() {
        batteryOptimizer.applyModerateOptimizations()
        
        // Reduce animation frame rates and voice processing
        NotificationCenter.default.post(
            name: .batteryOptimizationChanged,
            object: BatteryOptimizationSettings(
                level: .moderate,
                reduceVoiceProcessing: true,
                reduceAnimationFrameRate: true,
                enableBackgroundTaskLimiting: true,
                enableNetworkBatching: true
            )
        )
    }
    
    private func enableBatterySavingMode() {
        batteryOptimizer.applyAggressiveOptimizations()
        
        // Comprehensive battery saving
        NotificationCenter.default.post(
            name: .batteryOptimizationChanged,
            object: BatteryOptimizationSettings(
                level: .aggressive,
                reduceVoiceProcessing: true,
                reduceAnimationFrameRate: true,
                enableBackgroundTaskLimiting: true,
                enableNetworkBatching: true
            )
        )
        
        // Reduce background processing
        backgroundTaskManager.enablePowerSavingMode()
        
        print("🔋 Battery Manager: Aggressive battery saving mode enabled")
    }
    
    private func disableBatterySavingMode() {
        batteryOptimizer.restoreOriginalSettings(originalSettings)
        
        // Restore normal operation
        NotificationCenter.default.post(
            name: .batteryOptimizationChanged,
            object: BatteryOptimizationSettings(
                level: .none,
                reduceVoiceProcessing: false,
                reduceAnimationFrameRate: false,
                enableBackgroundTaskLimiting: false,
                enableNetworkBatching: false
            )
        )
        
        backgroundTaskManager.disablePowerSavingMode()
        
        print("🔋 Battery Manager: Battery optimizations disabled")
    }
    
    // MARK: - Manual Controls
    
    func optimizeForBatteryUsage() {
        if batteryLevel < 0.5 {
            setOptimizationLevel(.moderate)
        } else {
            setOptimizationLevel(.light)
        }
    }
    
    func disableOptimizations() {
        setOptimizationLevel(.none)
    }
    
    // MARK: - Battery Reports
    
    func getBatteryReport() -> BatteryReport {
        let averageBatteryLevel = batteryHistory.isEmpty ? batteryLevel :
            batteryHistory.map { $0.batteryLevel }.reduce(0, +) / Float(batteryHistory.count)
        
        let chargingTime = batteryHistory.filter { $0.batteryState == .charging }.count
        let dischargingTime = batteryHistory.filter { $0.batteryState == .unplugged }.count
        
        return BatteryReport(
            currentLevel: batteryLevel,
            averageLevel: averageBatteryLevel,
            usageRate: batteryUsageRate,
            isOptimized: isOptimized,
            optimizationLevel: optimizationLevel,
            lowPowerModeEnabled: isLowPowerModeEnabled,
            chargingPercentage: Double(chargingTime) / Double(max(batteryHistory.count, 1)) * 100,
            estimatedTimeRemaining: calculateEstimatedTimeRemaining()
        )
    }
    
    private func calculateEstimatedTimeRemaining() -> TimeInterval {
        guard batteryUsageRate > 0 else { return 0 }
        
        let remainingBattery = Double(batteryLevel) * 100
        return (remainingBattery / batteryUsageRate) * 3600 // Convert to seconds
    }
}

// MARK: - Battery Optimizer

class BatteryOptimizer {
    func applyLightOptimizations() {
        // Reduce non-critical background tasks
        DispatchQueue.global(qos: .background).async {
            // Implement light optimizations
        }
    }
    
    func applyModerateOptimizations() {
        // Reduce refresh rates and processing frequency
        DispatchQueue.global(qos: .background).async {
            // Implement moderate optimizations
        }
    }
    
    func applyAggressiveOptimizations() {
        // Minimize all non-essential operations
        DispatchQueue.global(qos: .background).async {
            // Implement aggressive optimizations
        }
    }
    
    func restoreOriginalSettings(_ settings: OriginalSettings) {
        // Restore all original settings
        DispatchQueue.global(qos: .background).async {
            // Restore original configurations
        }
    }
}

// MARK: - Background Task Manager

class BackgroundTaskManager {
    private var powerSavingMode = false
    
    func enablePowerSavingMode() {
        powerSavingMode = true
        
        // Reduce background task frequency
        // Limit concurrent operations
        // Defer non-critical tasks
    }
    
    func disablePowerSavingMode() {
        powerSavingMode = false
        
        // Restore normal background task behavior
    }
}

// MARK: - Supporting Types

struct BatterySnapshot {
    let timestamp: Date
    let batteryLevel: Float
    let batteryState: UIDevice.BatteryState
    let isLowPowerMode: Bool
}

struct OriginalSettings {
    var displayLinkFrameRate: Int = 60
    var animationDuration: Double = 0.3
    var voiceProcessingFrequency: Double = 1.0
    var networkRequestTimeout: TimeInterval = 30.0
    
    mutating func capture() {
        // Capture current settings before optimization
        displayLinkFrameRate = 60
        animationDuration = 0.3
        voiceProcessingFrequency = 1.0
        networkRequestTimeout = 30.0
    }
}

struct BatteryOptimizationSettings {
    let level: BatteryOptimizedManager.OptimizationLevel
    let reduceVoiceProcessing: Bool
    let reduceAnimationFrameRate: Bool
    let enableBackgroundTaskLimiting: Bool
    let enableNetworkBatching: Bool
}

struct BatteryReport {
    let currentLevel: Float
    let averageLevel: Float
    let usageRate: Double // % per hour
    let isOptimized: Bool
    let optimizationLevel: BatteryOptimizedManager.OptimizationLevel
    let lowPowerModeEnabled: Bool
    let chargingPercentage: Double
    let estimatedTimeRemaining: TimeInterval // seconds
    
    var status: BatteryStatus {
        if currentLevel > 0.7 {
            return .excellent
        } else if currentLevel > 0.3 {
            return .good
        } else {
            return .critical
        }
    }
    
    var usageStatus: UsageStatus {
        if usageRate < 10 {
            return .efficient
        } else if usageRate < 20 {
            return .moderate
        } else {
            return .heavy
        }
    }
    
    enum BatteryStatus {
        case excellent, good, critical
        
        var description: String {
            switch self {
            case .excellent: return "Excellent Battery"
            case .good: return "Good Battery"
            case .critical: return "Critical Battery"
            }
        }
        
        var color: Color {
            switch self {
            case .excellent: return .green
            case .good: return .orange
            case .critical: return .red
            }
        }
    }
    
    enum UsageStatus {
        case efficient, moderate, heavy
        
        var description: String {
            switch self {
            case .efficient: return "Efficient Usage"
            case .moderate: return "Moderate Usage"
            case .heavy: return "Heavy Usage"
            }
        }
        
        var color: Color {
            switch self {
            case .efficient: return .green
            case .moderate: return .orange
            case .heavy: return .red
            }
        }
    }
}

// MARK: - Notification Extensions

extension Notification.Name {
    static let batteryOptimizationChanged = Notification.Name("batteryOptimizationChanged")
}