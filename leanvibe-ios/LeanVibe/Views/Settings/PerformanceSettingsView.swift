import SwiftUI

/// Performance Settings view for configuring app performance optimizations
/// Provides controls for memory management, rendering, and system resource usage
@available(iOS 18.0, macOS 14.0, *)
struct PerformanceSettingsView: View {
    
    // MARK: - Properties
    
    @ObservedObject var settingsManager: SettingsManager
    @State private var showingPerformanceAnalysis = false
    @State private var isRunningAnalysis = false
    @State private var performanceMetrics: PerformanceMetrics?
    
    // Local state for performance settings
    @State private var enablePerformanceMonitoring = false
    @State private var optimizeMemoryUsage = true
    @State private var enableFrameRateOptimization = true
    @State private var enableBatteryOptimization = true
    @State private var maxConcurrentOperations: Double = 4
    @State private var cacheSize: Double = 100
    @State private var enablePreloading = false
    @State private var backgroundProcessingEnabled = true
    @State private var enableVectorization = true
    @State private var thermalStateMonitoring = true
    @State private var enableReducedMotion = false
    
    init(settingsManager: SettingsManager = SettingsManager.shared) {
        self.settingsManager = settingsManager
    }
    
    // MARK: - Body
    
    var body: some View {
        List {
            Section {
                Text("Configure performance settings to optimize LeanVibe for your device capabilities and usage patterns.")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .padding(.vertical, 4)
            }
            
            // Performance Monitoring Section
            Section("Performance Monitoring") {
                Toggle("Enable Performance Monitoring", isOn: $enablePerformanceMonitoring)
                    .help("Monitor app performance and resource usage")
                
                Toggle("Thermal State Monitoring", isOn: $thermalStateMonitoring)
                    .help("Adjust performance based on device thermal state")
                
                if enablePerformanceMonitoring {
                    Button("Run Performance Analysis") {
                        runPerformanceAnalysis()
                    }
                    .foregroundColor(.blue)
                    .disabled(isRunningAnalysis)
                    
                    if isRunningAnalysis {
                        HStack {
                            ProgressView()
                                .scaleEffect(0.8)
                            Text("Analyzing performance...")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                    }
                    
                    if let metrics = performanceMetrics {
                        PerformanceMetricsView(metrics: metrics)
                    }
                }
            }
            
            // Memory Management Section
            Section("Memory Management") {
                Toggle("Optimize Memory Usage", isOn: $optimizeMemoryUsage)
                    .help("Automatically manage memory allocation and cleanup")
                
                VStack(alignment: .leading, spacing: 8) {
                    Text("Cache Size: \(Int(cacheSize))MB")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    
                    Slider(value: $cacheSize, in: 50...500, step: 25) {
                        Text("Cache Size")
                    }
                    .help("Amount of memory allocated for caching")
                }
                .padding(.vertical, 4)
                
                Toggle("Enable Preloading", isOn: $enablePreloading)
                    .help("Preload frequently accessed data")
            }
            
            // CPU & Processing Section
            Section("CPU & Processing") {
                VStack(alignment: .leading, spacing: 8) {
                    Text("Max Concurrent Operations: \(Int(maxConcurrentOperations))")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    
                    Slider(value: $maxConcurrentOperations, in: 1...8, step: 1) {
                        Text("Max Concurrent Operations")
                    }
                    .help("Maximum number of concurrent background operations")
                }
                .padding(.vertical, 4)
                
                Toggle("Enable Vectorization", isOn: $enableVectorization)
                    .help("Use SIMD instructions for performance-critical operations")
                
                Toggle("Background Processing", isOn: $backgroundProcessingEnabled)
                    .help("Allow background processing when app is not active")
            }
            
            // Rendering & UI Section
            Section("Rendering & UI") {
                Toggle("Frame Rate Optimization", isOn: $enableFrameRateOptimization)
                    .help("Optimize rendering for smooth UI interactions")
                
                Toggle("Reduce Motion Effects", isOn: $enableReducedMotion)
                    .help("Minimize animations and transitions")
                
                NavigationLink(destination: RenderingSettingsView()) {
                    HStack {
                        Image(systemName: "paintbrush")
                            .foregroundColor(.purple)
                        VStack(alignment: .leading) {
                            Text("Rendering Settings")
                            Text("Advanced rendering configuration")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                    }
                }
            }
            
            // Battery & Power Section
            Section("Battery & Power") {
                Toggle("Battery Optimization", isOn: $enableBatteryOptimization)
                    .help("Reduce power consumption when on battery")
                
                NavigationLink(destination: PowerManagementView()) {
                    HStack {
                        Image(systemName: "battery.100")
                            .foregroundColor(.green)
                        VStack(alignment: .leading) {
                            Text("Power Management")
                            Text("Advanced power settings")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                    }
                }
            }
            
            // Performance Presets Section
            Section("Performance Presets") {
                Button("High Performance") {
                    applyPerformancePreset(.highPerformance)
                }
                .foregroundColor(.red)
                
                Button("Balanced") {
                    applyPerformancePreset(.balanced)
                }
                .foregroundColor(.blue)
                
                Button("Battery Saver") {
                    applyPerformancePreset(.batterySaver)
                }
                .foregroundColor(.green)
                
                Text("Presets automatically configure multiple settings for optimal performance.")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .navigationTitle("Performance Settings")
        .navigationBarTitleDisplayMode(.large)
        .onAppear {
            loadSettings()
        }
        .onChange(of: enablePerformanceMonitoring) { saveSettings() }
        .onChange(of: optimizeMemoryUsage) { saveSettings() }
        .onChange(of: enableFrameRateOptimization) { saveSettings() }
        .onChange(of: enableBatteryOptimization) { saveSettings() }
        .onChange(of: maxConcurrentOperations) { saveSettings() }
        .onChange(of: cacheSize) { saveSettings() }
        .onChange(of: enablePreloading) { saveSettings() }
        .onChange(of: backgroundProcessingEnabled) { saveSettings() }
        .onChange(of: enableVectorization) { saveSettings() }
        .onChange(of: thermalStateMonitoring) { saveSettings() }
        .onChange(of: enableReducedMotion) { saveSettings() }
    }
    
    // MARK: - Methods
    
    private func loadSettings() {
        let settings = settingsManager.performance
        
        enablePerformanceMonitoring = settings.enablePerformanceMonitoring
        optimizeMemoryUsage = settings.optimizeMemoryUsage
        enableFrameRateOptimization = settings.enableFrameRateOptimization
        enableBatteryOptimization = settings.enableBatteryOptimization
        maxConcurrentOperations = Double(settings.maxConcurrentOperations)
        cacheSize = Double(settings.cacheSize)
        enablePreloading = settings.enablePreloading
        backgroundProcessingEnabled = settings.backgroundProcessingEnabled
        enableVectorization = settings.enableVectorization
        thermalStateMonitoring = settings.thermalStateMonitoring
        enableReducedMotion = settings.enableReducedMotion
        
        print("✅ Performance settings loaded from SettingsManager")
    }
    
    private func saveSettings() {
        var settings = settingsManager.performance
        
        settings.enablePerformanceMonitoring = enablePerformanceMonitoring
        settings.optimizeMemoryUsage = optimizeMemoryUsage
        settings.enableFrameRateOptimization = enableFrameRateOptimization
        settings.enableBatteryOptimization = enableBatteryOptimization
        settings.maxConcurrentOperations = Int(maxConcurrentOperations)
        settings.cacheSize = Int(cacheSize)
        settings.enablePreloading = enablePreloading
        settings.backgroundProcessingEnabled = backgroundProcessingEnabled
        settings.enableVectorization = enableVectorization
        settings.thermalStateMonitoring = thermalStateMonitoring
        settings.enableReducedMotion = enableReducedMotion
        
        settingsManager.performance = settings
        
        print("✅ Performance settings saved to SettingsManager")
    }
    
    private func runPerformanceAnalysis() {
        isRunningAnalysis = true
        
        // Simulate performance analysis
        DispatchQueue.main.asyncAfter(deadline: .now() + 3.0) {
            performanceMetrics = PerformanceMetrics(
                cpuUsage: Double.random(in: 15...35),
                memoryUsage: Double.random(in: 200...400),
                frameRate: Double.random(in: 55...60),
                batteryImpact: Double.random(in: 5...15),
                thermalState: .nominal
            )
            isRunningAnalysis = false
        }
    }
    
    private func applyPerformancePreset(_ preset: PerformancePreset) {
        switch preset {
        case .highPerformance:
            enablePerformanceMonitoring = true
            optimizeMemoryUsage = false
            enableFrameRateOptimization = true
            enableBatteryOptimization = false
            maxConcurrentOperations = 8
            cacheSize = 500
            enablePreloading = true
            backgroundProcessingEnabled = true
            enableVectorization = true
            enableReducedMotion = false
            
        case .balanced:
            enablePerformanceMonitoring = true
            optimizeMemoryUsage = true
            enableFrameRateOptimization = true
            enableBatteryOptimization = true
            maxConcurrentOperations = 4
            cacheSize = 100
            enablePreloading = true
            backgroundProcessingEnabled = true
            enableVectorization = true
            enableReducedMotion = false
            
        case .batterySaver:
            enablePerformanceMonitoring = false
            optimizeMemoryUsage = true
            enableFrameRateOptimization = false
            enableBatteryOptimization = true
            maxConcurrentOperations = 2
            cacheSize = 50
            enablePreloading = false
            backgroundProcessingEnabled = false
            enableVectorization = false
            enableReducedMotion = true
        }
        
        saveSettings()
    }
}

// MARK: - Supporting Views

struct PerformanceMetricsView: View {
    let metrics: PerformanceMetrics
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Current Performance Metrics")
                .font(.headline)
                .padding(.bottom, 4)
            
            MetricRow(label: "CPU Usage", value: "\(String(format: "%.1f", metrics.cpuUsage))%", color: colorForCPU(metrics.cpuUsage))
            MetricRow(label: "Memory Usage", value: "\(String(format: "%.0f", metrics.memoryUsage))MB", color: colorForMemory(metrics.memoryUsage))
            MetricRow(label: "Frame Rate", value: "\(String(format: "%.0f", metrics.frameRate))fps", color: colorForFrameRate(metrics.frameRate))
            MetricRow(label: "Battery Impact", value: "\(String(format: "%.1f", metrics.batteryImpact))%", color: colorForBattery(metrics.batteryImpact))
            MetricRow(label: "Thermal State", value: metrics.thermalState.displayName, color: metrics.thermalState.color)
        }
        .padding()
        .background(Color.secondary.opacity(0.1))
        .cornerRadius(8)
    }
    
    private func colorForCPU(_ usage: Double) -> Color {
        usage < 25 ? .green : usage < 50 ? .orange : .red
    }
    
    private func colorForMemory(_ usage: Double) -> Color {
        usage < 250 ? .green : usage < 350 ? .orange : .red
    }
    
    private func colorForFrameRate(_ rate: Double) -> Color {
        rate >= 58 ? .green : rate >= 45 ? .orange : .red
    }
    
    private func colorForBattery(_ impact: Double) -> Color {
        impact < 10 ? .green : impact < 15 ? .orange : .red
    }
}

struct MetricRow: View {
    let label: String
    let value: String
    let color: Color
    
    var body: some View {
        HStack {
            Text(label)
                .font(.caption)
            Spacer()
            Text(value)
                .font(.caption)
                .fontWeight(.medium)
                .foregroundColor(color)
        }
    }
}

struct RenderingSettingsView: View {
    var body: some View {
        List {
            Section {
                Text("Advanced rendering configuration for optimal visual performance.")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .padding(.vertical, 4)
            }
            
            Section("Rendering Quality") {
                Text("Rendering quality settings will be implemented here.")
                    .font(.body)
                    .foregroundColor(.secondary)
            }
        }
        .navigationTitle("Rendering Settings")
        .navigationBarTitleDisplayMode(.large)
    }
}

struct PowerManagementView: View {
    var body: some View {
        List {
            Section {
                Text("Advanced power management settings for optimal battery life.")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .padding(.vertical, 4)
            }
            
            Section("Power Management") {
                Text("Power management settings will be implemented here.")
                    .font(.body)
                    .foregroundColor(.secondary)
            }
        }
        .navigationTitle("Power Management")
        .navigationBarTitleDisplayMode(.large)
    }
}

// MARK: - Supporting Types

struct PerformanceMetrics {
    let cpuUsage: Double
    let memoryUsage: Double
    let frameRate: Double
    let batteryImpact: Double
    let thermalState: ThermalState
}

enum ThermalState {
    case nominal
    case fair
    case serious
    case critical
    
    var displayName: String {
        switch self {
        case .nominal: return "Nominal"
        case .fair: return "Fair"
        case .serious: return "Serious"
        case .critical: return "Critical"
        }
    }
    
    var color: Color {
        switch self {
        case .nominal: return .green
        case .fair: return .yellow
        case .serious: return .orange
        case .critical: return .red
        }
    }
}

enum PerformancePreset {
    case highPerformance
    case balanced
    case batterySaver
}

#Preview {
    PerformanceSettingsView()
}