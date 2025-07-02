import SwiftUI
import Combine

// MARK: - Real-Time Performance Dashboard

struct RealTimePerformanceDashboard: View {
    @StateObject private var performanceAnalytics = PerformanceAnalytics()
    @StateObject private var batteryManager = BatteryOptimizedManager()
    @StateObject private var memoryManager = OptimizedArchitectureService()
    @StateObject private var voiceFactory = VoiceManagerFactory()
    @StateObject private var networkManager = OptimizedWebSocketService()
    @StateObject private var integratedManager: IntegratedPerformanceManager
    
    @State private var selectedTimeRange: TimeRange = .live
    @State private var showingDetailedView = false
    @State private var isAutoRefreshEnabled = true
    
    enum TimeRange: String, CaseIterable {
        case live = "Live"
        case minute1 = "1m"
        case minute5 = "5m"
        case minute15 = "15m"
        case hour1 = "1h"
        
        var seconds: TimeInterval {
            switch self {
            case .live: return 5
            case .minute1: return 60
            case .minute5: return 300
            case .minute15: return 900
            case .hour1: return 3600
            }
        }
    }
    
    init() {
        let analytics = PerformanceAnalytics()
        let battery = BatteryOptimizedManager()
        let memory = OptimizedArchitectureService()
        let voiceFactory = VoiceManagerFactory()
        let network = OptimizedWebSocketService()
        
        self._performanceAnalytics = StateObject(wrappedValue: analytics)
        self._batteryManager = StateObject(wrappedValue: battery)
        self._memoryManager = StateObject(wrappedValue: memory)
        self._voiceFactory = StateObject(wrappedValue: voiceFactory)
        self._networkManager = StateObject(wrappedValue: network)
        self._integratedManager = StateObject(wrappedValue: IntegratedPerformanceManager(
            performanceAnalytics: analytics,
            batteryManager: battery,
            memoryManager: memory,
            voiceManager: voiceFactory.optimizedVoiceManager ?? OptimizedVoiceManager(),
            networkManager: network
        ))
    }
    
    var body: some View {
        NavigationView {
            ScrollView {
                LazyVStack(spacing: 20) {
                    // Real-Time Status Overview
                    realTimeStatusSection
                    
                    // Performance Metrics Grid
                    performanceMetricsGrid
                    
                    // Live Charts Section
                    liveChartsSection
                    
                    // System Optimization Status
                    optimizationStatusSection
                    
                    // Performance Alerts
                    alertsSection
                    
                    // Quick Actions
                    quickActionsSection
                }
                .padding()
            }
            .navigationTitle("Performance Monitor")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItemGroup(placement: .navigationBarTrailing) {
                    autoRefreshToggle
                    timeRangeSelector
                    detailButton
                }
            }
            .refreshable {
                await refreshAllMetrics()
            }
            .sheet(isPresented: $showingDetailedView) {
                DetailedPerformanceView(manager: integratedManager)
            }
        }
        .onAppear {
            startRealTimeMonitoring()
        }
        .onDisappear {
            stopRealTimeMonitoring()
        }
    }
    
    // MARK: - Real-Time Status Section
    
    private var realTimeStatusSection: some View {
        PremiumCard(style: .glass) {
            VStack(spacing: 16) {
                HStack {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("System Status")
                            .font(PremiumDesignSystem.Typography.headline)
                        
                        Text(integratedManager.systemHealth.description)
                            .font(PremiumDesignSystem.Typography.subheadline)
                            .foregroundColor(integratedManager.systemHealth.color)
                    }
                    
                    Spacer()
                    
                    RealTimeIndicator(
                        isActive: performanceAnalytics.isMonitoring,
                        color: integratedManager.systemHealth.color
                    )
                }
                
                // Live Performance Score
                VStack(spacing: 8) {
                    HStack {
                        Text("Performance Score")
                            .font(PremiumDesignSystem.Typography.body)
                        
                        Spacer()
                        
                        Text("\(Int(integratedManager.getSystemReport().overallScore))%")
                            .font(PremiumDesignSystem.Typography.title2)
                            .fontWeight(.bold)
                            .foregroundColor(integratedManager.systemHealth.color)
                    }
                    
                    PremiumProgressBar(
                        progress: integratedManager.getSystemReport().overallScore / 100.0,
                        color: integratedManager.systemHealth.color
                    )
                }
            }
        }
        .hapticFeedback(.buttonTap)
    }
    
    // MARK: - Performance Metrics Grid
    
    private var performanceMetricsGrid: some View {
        LazyVGrid(columns: [
            GridItem(.flexible()),
            GridItem(.flexible())
        ], spacing: 16) {
            // Frame Rate Card
            MetricCard(
                title: "Frame Rate",
                value: String(format: "%.1f", performanceAnalytics.metrics.frameRate),
                unit: "fps",
                color: performanceAnalytics.metrics.frameRate >= 55 ? .green : .orange,
                trend: .stable,
                icon: "speedometer"
            )
            
            // Memory Usage Card
            MetricCard(
                title: "Memory",
                value: String(format: "%.0f", performanceAnalytics.metrics.memoryUsage),
                unit: "MB",
                color: performanceAnalytics.metrics.memoryUsage < 200 ? .green : .orange,
                trend: .decreasing,
                icon: "memorychip"
            )
            
            // Battery Level Card
            MetricCard(
                title: "Battery",
                value: String(format: "%.0f", batteryManager.batteryLevel * 100),
                unit: "%",
                color: batteryManager.batteryLevel > 0.3 ? .green : .red,
                trend: batteryManager.batteryState == .charging ? .increasing : .decreasing,
                icon: "battery.100"
            )
            
            // Voice Latency Card
            MetricCard(
                title: "Voice Latency",
                value: String(format: "%.0f", (voiceFactory.optimizedVoiceManager?.currentLatency ?? 0.0) * 1000),
                unit: "ms",
                color: (voiceFactory.optimizedVoiceManager?.currentLatency ?? 0.0) < 0.5 ? .green : .orange,
                trend: .stable,
                icon: "mic"
            )
        }
    }
    
    // MARK: - Live Charts Section
    
    private var liveChartsSection: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                Text("Live Performance Charts")
                    .font(PremiumDesignSystem.Typography.title3)
                    .fontWeight(.semibold)
                
                Spacer()
                
                Text("Updated every \(Int(selectedTimeRange.seconds))s")
                    .font(PremiumDesignSystem.Typography.caption)
                    .foregroundColor(PremiumDesignSystem.Colors.secondaryText)
            }
            
            TabView {
                // Frame Rate Chart
                LiveChartView(
                    title: "Frame Rate",
                    data: generateFrameRateData(),
                    color: .blue,
                    unit: "fps"
                )
                .tag(0)
                
                // Memory Usage Chart
                LiveChartView(
                    title: "Memory Usage",
                    data: generateMemoryData(),
                    color: .orange,
                    unit: "MB"
                )
                .tag(1)
                
                // Battery Usage Chart
                LiveChartView(
                    title: "Battery Level",
                    data: generateBatteryData(),
                    color: .green,
                    unit: "%"
                )
                .tag(2)
            }
            .frame(height: 200)
            .tabViewStyle(PageTabViewStyle(indexDisplayMode: .automatic))
        }
    }
    
    // MARK: - Optimization Status Section
    
    private var optimizationStatusSection: some View {
        PremiumCard(style: .elevated) {
            VStack(alignment: .leading, spacing: 16) {
                Text("System Optimizations")
                    .font(PremiumDesignSystem.Typography.headline)
                
                VStack(spacing: 12) {
                    OptimizationStatusRow(
                        title: "Battery Optimization",
                        isEnabled: batteryManager.isOptimized,
                        level: batteryManager.optimizationLevel.description,
                        color: batteryManager.isOptimized ? .green : .gray
                    )
                    
                    OptimizationStatusRow(
                        title: "Memory Optimization",
                        isEnabled: memoryManager.isOptimized,
                        level: "Active",
                        color: memoryManager.isOptimized ? .green : .gray
                    )
                    
                    OptimizationStatusRow(
                        title: "Voice Optimization",
                        isEnabled: voiceFactory.optimizedVoiceManager?.isOptimized ?? false,
                        level: (voiceFactory.optimizedVoiceManager?.isLowLatencyMode ?? false) ? "Low Latency" : "Standard",
                        color: (voiceFactory.optimizedVoiceManager?.isOptimized ?? false) ? .green : .gray
                    )
                    
                    OptimizationStatusRow(
                        title: "Network Optimization",
                        isEnabled: networkManager.isOptimized,
                        level: "Connection Pooling",
                        color: networkManager.isOptimized ? .green : .gray
                    )
                }
            }
        }
        .hapticFeedback(.buttonTap)
    }
    
    // MARK: - Alerts Section
    
    private var alertsSection: some View {
        Group {
            if !integratedManager.alerts.isEmpty {
                VStack(alignment: .leading, spacing: 12) {
                    HStack {
                        Text("Performance Alerts")
                            .font(PremiumDesignSystem.Typography.title3)
                            .fontWeight(.semibold)
                        
                        Spacer()
                        
                        Button("Clear All") {
                            PremiumHaptics.contextualFeedback(for: .buttonTap)
                            integratedManager.clearAlerts()
                        }
                        .font(PremiumDesignSystem.Typography.caption)
                        .foregroundColor(PremiumDesignSystem.Colors.primary)
                    }
                    
                    LazyVStack(spacing: 8) {
                        ForEach(integratedManager.alerts.prefix(3)) { alert in
                            AlertCard(alert: alert) {
                                integratedManager.dismissAlert(alert)
                            }
                        }
                    }
                }
            }
        }
    }
    
    // MARK: - Quick Actions Section
    
    private var quickActionsSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Quick Actions")
                .font(PremiumDesignSystem.Typography.title3)
                .fontWeight(.semibold)
            
            LazyVGrid(columns: [
                GridItem(.flexible()),
                GridItem(.flexible())
            ], spacing: 12) {
                ActionButton(
                    title: "Optimize Performance",
                    icon: "bolt.circle.fill",
                    color: .blue
                ) {
                    PremiumHaptics.contextualFeedback(for: .saveAction)
                    integratedManager.manualOptimization()
                }
                
                ActionButton(
                    title: "Clear Memory",
                    icon: "trash.circle.fill",
                    color: .orange
                ) {
                    PremiumHaptics.contextualFeedback(for: .buttonTap)
                    Task {
                        await memoryManager.optimizeMemoryUsage()
                    }
                }
                
                ActionButton(
                    title: "Reset Optimizations",
                    icon: "arrow.clockwise.circle.fill",
                    color: .gray
                ) {
                    PremiumHaptics.contextualFeedback(for: .buttonTap)
                    integratedManager.resetOptimizations()
                }
                
                ActionButton(
                    title: "Export Report",
                    icon: "square.and.arrow.up.circle.fill",
                    color: .green
                ) {
                    PremiumHaptics.contextualFeedback(for: .buttonTap)
                    exportPerformanceReport()
                }
            }
        }
    }
    
    // MARK: - Toolbar Components
    
    private var autoRefreshToggle: some View {
        Button(action: {
            PremiumHaptics.selection()
            isAutoRefreshEnabled.toggle()
        }) {
            Image(systemName: isAutoRefreshEnabled ? "play.circle.fill" : "pause.circle.fill")
                .font(.title3)
                .foregroundColor(isAutoRefreshEnabled ? .green : .gray)
        }
    }
    
    private var timeRangeSelector: some View {
        Menu {
            ForEach(TimeRange.allCases, id: \.rawValue) { range in
                Button(range.rawValue) {
                    PremiumHaptics.selection()
                    selectedTimeRange = range
                }
            }
        } label: {
            Text(selectedTimeRange.rawValue)
                .font(.caption)
                .fontWeight(.medium)
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(PremiumDesignSystem.Colors.secondaryBackground)
                .cornerRadius(8)
        }
    }
    
    private var detailButton: some View {
        Button(action: {
            PremiumHaptics.contextualFeedback(for: .buttonTap)
            showingDetailedView = true
        }) {
            Image(systemName: "chart.bar.doc.horizontal")
                .font(.title3)
        }
    }
    
    // MARK: - Performance Monitoring
    
    private func startRealTimeMonitoring() {
        performanceAnalytics.startPerformanceMonitoring()
    }
    
    private func stopRealTimeMonitoring() {
        performanceAnalytics.stopPerformanceMonitoring()
    }
    
    private func refreshAllMetrics() async {
        // Trigger refresh of all performance metrics
        await memoryManager.optimizeMemoryUsage()
        // Additional refresh logic would go here
    }
    
    private func exportPerformanceReport() {
        let report = integratedManager.getSystemReport()
        // Export functionality would be implemented here
        print("📊 Exporting performance report: \(report.status)")
    }
    
    // MARK: - Mock Data Generation (for demo)
    
    private func generateFrameRateData() -> [ChartDataPoint] {
        return (0..<20).map { i in
            ChartDataPoint(
                x: Double(i),
                y: Double.random(in: 50...60),
                timestamp: Date().addingTimeInterval(-Double(20 - i) * 5)
            )
        }
    }
    
    private func generateMemoryData() -> [ChartDataPoint] {
        return (0..<20).map { i in
            ChartDataPoint(
                x: Double(i),
                y: Double.random(in: 100...250),
                timestamp: Date().addingTimeInterval(-Double(20 - i) * 5)
            )
        }
    }
    
    private func generateBatteryData() -> [ChartDataPoint] {
        return (0..<20).map { i in
            ChartDataPoint(
                x: Double(i),
                y: max(20, 100 - Double(i) * 2), // Simulated battery drain
                timestamp: Date().addingTimeInterval(-Double(20 - i) * 5)
            )
        }
    }
}

// MARK: - Supporting Views

struct RealTimeIndicator: View {
    let isActive: Bool
    let color: Color
    @State private var isAnimating = false
    
    var body: some View {
        HStack(spacing: 8) {
            Circle()
                .fill(isActive ? color : .gray)
                .frame(width: 12, height: 12)
                .scaleEffect(isAnimating ? 1.2 : 1.0)
                .animation(.easeInOut(duration: 1.0).repeatForever(autoreverses: true), value: isAnimating)
            
            Text(isActive ? "LIVE" : "PAUSED")
                .font(.caption2)
                .fontWeight(.bold)
                .foregroundColor(isActive ? color : .gray)
        }
        .onAppear {
            if isActive {
                isAnimating = true
            }
        }
    }
}

struct MetricCard: View {
    let title: String
    let value: String
    let unit: String
    let color: Color
    let trend: TrendDirection
    let icon: String
    
    enum TrendDirection {
        case increasing, decreasing, stable
        
        var icon: String {
            switch self {
            case .increasing: return "arrow.up.right"
            case .decreasing: return "arrow.down.right"
            case .stable: return "minus"
            }
        }
        
        var color: Color {
            switch self {
            case .increasing: return .green
            case .decreasing: return .red
            case .stable: return .gray
            }
        }
    }
    
    var body: some View {
        PremiumCard(style: .standard) {
            VStack(alignment: .leading, spacing: 12) {
                HStack {
                    Image(systemName: icon)
                        .font(.title3)
                        .foregroundColor(color)
                    
                    Spacer()
                    
                    Image(systemName: trend.icon)
                        .font(.caption)
                        .foregroundColor(trend.color)
                }
                
                VStack(alignment: .leading, spacing: 4) {
                    HStack(alignment: .lastTextBaseline, spacing: 4) {
                        Text(value)
                            .font(.title2)
                            .fontWeight(.bold)
                            .foregroundColor(color)
                        
                        Text(unit)
                            .font(.caption)
                            .foregroundColor(PremiumDesignSystem.Colors.secondaryText)
                    }
                    
                    Text(title)
                        .font(.caption)
                        .foregroundColor(PremiumDesignSystem.Colors.secondaryText)
                }
            }
        }
        .hapticFeedback(.buttonTap)
    }
}

struct LiveChartView: View {
    let title: String
    let data: [ChartDataPoint]
    let color: Color
    let unit: String
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(title)
                    .font(PremiumDesignSystem.Typography.headline)
                
                Spacer()
                
                if let latest = data.last {
                    Text("\(String(format: "%.1f", latest.y)) \(unit)")
                        .font(PremiumDesignSystem.Typography.caption)
                        .foregroundColor(color)
                }
            }
            
            // Simplified chart representation
            GeometryReader { geometry in
                Path { path in
                    guard !data.isEmpty else { return }
                    
                    let maxY = data.map { $0.y }.max() ?? 0
                    let minY = data.map { $0.y }.min() ?? 0
                    let range = maxY - minY
                    
                    let stepX = geometry.size.width / CGFloat(data.count - 1)
                    
                    for (index, point) in data.enumerated() {
                        let x = CGFloat(index) * stepX
                        let y = geometry.size.height - (CGFloat(point.y - minY) / CGFloat(range)) * geometry.size.height
                        
                        if index == 0 {
                            path.move(to: CGPoint(x: x, y: y))
                        } else {
                            path.addLine(to: CGPoint(x: x, y: y))
                        }
                    }
                }
                .stroke(color, lineWidth: 2)
            }
        }
        .padding()
        .background(PremiumDesignSystem.Colors.secondaryBackground)
        .cornerRadius(PremiumDesignSystem.cornerRadius)
    }
}

struct ChartDataPoint {
    let x: Double
    let y: Double
    let timestamp: Date
}

struct OptimizationStatusRow: View {
    let title: String
    let isEnabled: Bool
    let level: String
    let color: Color
    
    var body: some View {
        HStack {
            Circle()
                .fill(color)
                .frame(width: 8, height: 8)
            
            Text(title)
                .font(PremiumDesignSystem.Typography.body)
            
            Spacer()
            
            Text(level)
                .font(PremiumDesignSystem.Typography.caption)
                .foregroundColor(PremiumDesignSystem.Colors.secondaryText)
        }
    }
}

struct AlertCard: View {
    let alert: SystemAlert
    let onDismiss: () -> Void
    
    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: alert.severity.icon)
                .font(.title3)
                .foregroundColor(alert.severity.color)
            
            VStack(alignment: .leading, spacing: 2) {
                Text(alert.message)
                    .font(.subheadline)
                    .fontWeight(.medium)
                
                Text(RelativeDateTimeFormatter().localizedString(for: alert.timestamp, relativeTo: Date()))
                    .font(.caption)
                    .foregroundColor(PremiumDesignSystem.Colors.tertiaryText)
            }
            
            Spacer()
            
            Button(action: onDismiss) {
                Image(systemName: "xmark.circle.fill")
                    .font(.caption)
                    .foregroundColor(PremiumDesignSystem.Colors.tertiaryText)
            }
        }
        .padding(12)
        .background(alert.severity.color.opacity(0.1))
        .cornerRadius(8)
    }
}

struct ActionButton: View {
    let title: String
    let icon: String
    let color: Color
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            VStack(spacing: 8) {
                Image(systemName: icon)
                    .font(.title2)
                    .foregroundColor(color)
                
                Text(title)
                    .font(.caption)
                    .fontWeight(.medium)
                    .multilineTextAlignment(.center)
            }
            .frame(maxWidth: .infinity)
            .padding()
            .background(PremiumDesignSystem.Colors.secondaryBackground)
            .cornerRadius(PremiumDesignSystem.cornerRadius)
        }
        .buttonStyle(PlainButtonStyle())
    }
}

struct DetailedPerformanceView: View {
    let manager: IntegratedPerformanceManager
    
    var body: some View {
        NavigationView {
            ScrollView {
                Text("Detailed performance metrics and analysis would be displayed here")
                    .padding()
            }
            .navigationTitle("Detailed Performance")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Done") {
                        // Dismiss functionality
                    }
                }
            }
        }
    }
}