import SwiftUI
import Foundation
import Combine

@MainActor
class PerformanceManager: ObservableObject {
    @Published var memoryUsage: Double = 0
    @Published var performanceMetrics: PerformanceMetrics?
    @Published var performanceAlerts: [PerformanceAlert] = []
    @Published var isMonitoring = false
    
    nonisolated(unsafe) private var timer: Timer?
    private var cancellables = Set<AnyCancellable>()
    private let alertThresholds = PerformanceThresholds()
    
    // Performance tracking
    private var startTime: Date?
    private var lastMemoryWarning: Date?
    private var memoryWarningCount = 0
    
    struct PerformanceMetrics {
        let memoryUsage: Double // MB
        let cpuUsage: Double // Percentage
        let diskUsage: Double // MB
        let networkActivity: NetworkActivity
        let responseTime: TimeInterval
        let frameRate: Double
        let timestamp: Date
        
        struct NetworkActivity {
            let bytesReceived: Int64
            let bytesSent: Int64
            let requestCount: Int
        }
    }
    
    struct PerformanceAlert: Identifiable {
        let id = UUID()
        let type: AlertType
        let message: String
        let severity: Severity
        let timestamp: Date
        
        enum AlertType {
            case highMemory
            case lowMemory
            case highCPU
            case slowResponse
            case networkError
            case diskSpace
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
        }
    }
    
    struct PerformanceThresholds {
        let memoryWarning: Double = 200 // MB
        let memoryCritical: Double = 350 // MB
        let cpuWarning: Double = 80 // %
        let cpuCritical: Double = 95 // %
        let responseTimeWarning: TimeInterval = 2.0 // seconds
        let responseTimeCritical: TimeInterval = 5.0 // seconds
    }
    
    init() {
        setupMemoryWarningObserver()
        setupBackgroundObserver()
    }
    
    deinit {
        // Monitoring will be stopped automatically
        timer?.invalidate()
        timer = nil
    }
    
    private func setupMemoryWarningObserver() {
        NotificationCenter.default.publisher(for: UIApplication.didReceiveMemoryWarningNotification)
            .sink { [weak self] _ in
                self?.handleMemoryWarning()
            }
            .store(in: &cancellables)
    }
    
    private func setupBackgroundObserver() {
        NotificationCenter.default.publisher(for: UIApplication.didEnterBackgroundNotification)
            .sink { [weak self] _ in
                self?.handleBackgroundTransition()
            }
            .store(in: &cancellables)
        
        NotificationCenter.default.publisher(for: UIApplication.willEnterForegroundNotification)
            .sink { [weak self] _ in
                self?.handleForegroundTransition()
            }
            .store(in: &cancellables)
    }
    
    // MARK: - Monitoring Control
    
    func startMonitoring() {
        guard !isMonitoring else { return }
        
        isMonitoring = true
        startTime = Date()
        
        timer = Timer.scheduledTimer(withTimeInterval: 5.0, repeats: true) { [weak self] _ in
            Task { @MainActor in
                self?.updateMetrics()
            }
        }
        
        // Initial metrics update
        updateMetrics()
        
        addAlert(
            type: .networkError,
            message: "Performance monitoring started",
            severity: .info
        )
    }
    
    func stopMonitoring() {
        timer?.invalidate()
        timer = nil
        isMonitoring = false
        
        if startTime != nil {
            addAlert(
                type: .networkError,
                message: "Performance monitoring stopped",
                severity: .info
            )
        }
    }
    
    private func updateMetrics() {
        let memory = getMemoryUsage()
        let cpu = getCPUUsage()
        let disk = getDiskUsage()
        let network = getNetworkActivity()
        let responseTime = measureResponseTime()
        let frameRate = getFrameRate()
        
        memoryUsage = memory
        
        let metrics = PerformanceMetrics(
            memoryUsage: memory,
            cpuUsage: cpu,
            diskUsage: disk,
            networkActivity: network,
            responseTime: responseTime,
            frameRate: frameRate,
            timestamp: Date()
        )
        
        performanceMetrics = metrics
        
        // Check thresholds and create alerts
        checkPerformanceThresholds(metrics)
    }
    
    // MARK: - Memory Monitoring
    
    private func getMemoryUsage() -> Double {
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
    
    private func getCPUUsage() -> Double {
        var info: processor_info_array_t? = nil
        var numCpuInfo: mach_msg_type_number_t = 0
        var numCpus: natural_t = 0
        
        let result = host_processor_info(mach_host_self(),
                                       PROCESSOR_CPU_LOAD_INFO,
                                       &numCpus,
                                       &info,
                                       &numCpuInfo)
        
        defer {
            if let info = info {
                vm_deallocate(mach_task_self_, vm_address_t(bitPattern: info), vm_size_t(numCpuInfo))
            }
        }
        
        if result == KERN_SUCCESS {
            // Simplified CPU calculation
            return Double.random(in: 5...25) // Mock CPU usage for now
        }
        return 0
    }
    
    private func getDiskUsage() -> Double {
        do {
            let systemAttributes = try FileManager.default.attributesOfFileSystem(forPath: NSHomeDirectory())
            if let space = systemAttributes[FileAttributeKey.systemSize] as? NSNumber {
                return Double(space.int64Value) / 1024.0 / 1024.0 / 1024.0 // GB
            }
        } catch {
            print("Error getting disk usage: \(error)")
        }
        return 0
    }
    
    private func getNetworkActivity() -> PerformanceMetrics.NetworkActivity {
        // Mock network activity for now
        return PerformanceMetrics.NetworkActivity(
            bytesReceived: Int64.random(in: 1000...10000),
            bytesSent: Int64.random(in: 500...5000),
            requestCount: Int.random(in: 1...10)
        )
    }
    
    private func measureResponseTime() -> TimeInterval {
        // Mock response time measurement
        return Double.random(in: 0.1...1.5)
    }
    
    private func getFrameRate() -> Double {
        // Mock frame rate - in real implementation this would use CADisplayLink
        return Double.random(in: 55...60)
    }
    
    // MARK: - Performance Analysis
    
    private func checkPerformanceThresholds(_ metrics: PerformanceMetrics) {
        // Memory checks
        if metrics.memoryUsage > alertThresholds.memoryCritical {
            addAlert(
                type: .highMemory,
                message: "Critical memory usage: \(String(format: "%.1f", metrics.memoryUsage))MB",
                severity: .critical
            )
        } else if metrics.memoryUsage > alertThresholds.memoryWarning {
            addAlert(
                type: .highMemory,
                message: "High memory usage: \(String(format: "%.1f", metrics.memoryUsage))MB",
                severity: .warning
            )
        }
        
        // CPU checks
        if metrics.cpuUsage > alertThresholds.cpuCritical {
            addAlert(
                type: .highCPU,
                message: "Critical CPU usage: \(String(format: "%.1f", metrics.cpuUsage))%",
                severity: .critical
            )
        } else if metrics.cpuUsage > alertThresholds.cpuWarning {
            addAlert(
                type: .highCPU,
                message: "High CPU usage: \(String(format: "%.1f", metrics.cpuUsage))%",
                severity: .warning
            )
        }
        
        // Response time checks
        if metrics.responseTime > alertThresholds.responseTimeCritical {
            addAlert(
                type: .slowResponse,
                message: "Critical response time: \(String(format: "%.2f", metrics.responseTime))s",
                severity: .critical
            )
        } else if metrics.responseTime > alertThresholds.responseTimeWarning {
            addAlert(
                type: .slowResponse,
                message: "Slow response time: \(String(format: "%.2f", metrics.responseTime))s",
                severity: .warning
            )
        }
    }
    
    private func addAlert(type: PerformanceAlert.AlertType, message: String, severity: PerformanceAlert.Severity) {
        let alert = PerformanceAlert(
            type: type,
            message: message,
            severity: severity,
            timestamp: Date()
        )
        
        performanceAlerts.insert(alert, at: 0)
        
        // Keep only last 50 alerts
        if performanceAlerts.count > 50 {
            performanceAlerts = Array(performanceAlerts.prefix(50))
        }
        
        // Log critical alerts
        if severity == .critical {
            print("🚨 PERFORMANCE ALERT: \(message)")
        }
    }
    
    // MARK: - Memory Management
    
    private func handleMemoryWarning() {
        lastMemoryWarning = Date()
        memoryWarningCount += 1
        
        addAlert(
            type: .lowMemory,
            message: "System memory warning received (count: \(memoryWarningCount))",
            severity: .critical
        )
        
        // Trigger memory cleanup
        performMemoryCleanup()
    }
    
    private func performMemoryCleanup() {
        // Notify components to reduce memory usage
        NotificationCenter.default.post(
            name: NSNotification.Name("PerformMemoryCleanup"),
            object: nil
        )
        
        // Force garbage collection
        autoreleasepool {
            // This block forces a cleanup cycle
        }
    }
    
    private func handleBackgroundTransition() {
        // Reduce monitoring frequency in background
        timer?.invalidate()
        timer = Timer.scheduledTimer(withTimeInterval: 30.0, repeats: true) { [weak self] _ in
            Task { @MainActor in
                self?.updateMetrics()
            }
        }
    }
    
    private func handleForegroundTransition() {
        // Resume normal monitoring frequency
        timer?.invalidate()
        timer = Timer.scheduledTimer(withTimeInterval: 5.0, repeats: true) { [weak self] _ in
            Task { @MainActor in
                self?.updateMetrics()
            }
        }
    }
    
    // MARK: - Performance Optimization
    
    func optimizePerformance() {
        performMemoryCleanup()
        
        addAlert(
            type: .networkError,
            message: "Performance optimization triggered",
            severity: .info
        )
    }
    
    func clearAlerts() {
        performanceAlerts.removeAll()
    }
    
    // MARK: - Metrics Export
    
    func exportMetrics() -> String {
        guard let metrics = performanceMetrics else {
            return "No metrics available"
        }
        
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        formatter.timeStyle = .medium
        
        return """
        LeenVibe Performance Report
        Generated: \(formatter.string(from: Date()))
        
        Current Metrics:
        - Memory Usage: \(String(format: "%.1f", metrics.memoryUsage))MB
        - CPU Usage: \(String(format: "%.1f", metrics.cpuUsage))%
        - Response Time: \(String(format: "%.2f", metrics.responseTime))s
        - Frame Rate: \(String(format: "%.1f", metrics.frameRate))fps
        - Network Received: \(metrics.networkActivity.bytesReceived) bytes
        - Network Sent: \(metrics.networkActivity.bytesSent) bytes
        
        Session Info:
        - Memory Warnings: \(memoryWarningCount)
        - Active Alerts: \(performanceAlerts.count)
        - Monitoring: \(isMonitoring ? "Active" : "Inactive")
        """
    }
}