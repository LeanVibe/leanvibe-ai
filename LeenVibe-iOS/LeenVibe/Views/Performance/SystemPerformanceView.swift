import SwiftUI
import Combine

// MARK: - System Performance Dashboard

struct SystemPerformanceView: View {
    @StateObject private var integratedManager: IntegratedPerformanceManager
    @State private var showingDetailedMetrics = false
    @State private var selectedMetricCategory: MetricCategory = .overview
    
    enum MetricCategory: String, CaseIterable {
        case overview = "Overview"
        case performance = "Performance"
        case battery = "Battery"
        case memory = "Memory"
        case network = "Network"
        case voice = "Voice"
        
        var icon: String {
            switch self {
            case .overview: return "chart.line.uptrend.xyaxis"
            case .performance: return "speedometer"
            case .battery: return "battery.100"
            case .memory: return "memorychip"
            case .network: return "network"
            case .voice: return "mic"
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
        self._integratedManager = StateObject(wrappedValue: IntegratedPerformanceManager(
            performanceAnalytics: performanceAnalytics,
            batteryManager: batteryManager,
            memoryManager: memoryManager,
            voiceManager: voiceManager,
            networkManager: networkManager
        ))
    }
    
    var body: some View {
        NavigationView {
            ScrollView {
                LazyVStack(spacing: PremiumDesignSystem.sectionSpacing) {
                    // System Health Overview
                    systemHealthCard
                    
                    // Performance State
                    performanceStateCard
                    
                    // Metric Categories
                    metricCategoriesSection
                    
                    // Selected Category Details
                    categoryDetailSection
                    
                    // System Alerts
                    systemAlertsSection
                    
                    // Quick Actions
                    quickActionsSection
                }
                .padding()
            }
            .navigationTitle("System Performance")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: {
                        PremiumHaptics.contextualFeedback(for: .buttonTap)
                        showingDetailedMetrics.toggle()
                    }) {
                        Image(systemName: "chart.bar.doc.horizontal")
                            .font(.title2)
                    }
                }
            }
            .sheet(isPresented: $showingDetailedMetrics) {
                DetailedMetricsView(manager: integratedManager)
            }
        }
    }
    
    // MARK: - System Health Card
    
    private var systemHealthCard: some View {
        PremiumCard(style: .glass) {
            VStack(spacing: 16) {
                HStack {
                    Image(systemName: "heart.circle.fill")
                        .font(.title)
                        .foregroundColor(integratedManager.systemHealth.color)
                    
                    VStack(alignment: .leading, spacing: 4) {
                        Text("System Health")
                            .font(PremiumDesignSystem.Typography.headline)
                        
                        Text(integratedManager.systemHealth.description)
                            .font(PremiumDesignSystem.Typography.subheadline)
                            .foregroundColor(PremiumDesignSystem.Colors.secondaryText)
                    }
                    
                    Spacer()
                    
                    SystemHealthIndicator(health: integratedManager.systemHealth)
                }
                
                // Health Score Progress
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Text("Overall Score")
                            .font(PremiumDesignSystem.Typography.caption)
                            .foregroundColor(PremiumDesignSystem.Colors.secondaryText)
                        
                        Spacer()
                        
                        Text("\(Int(integratedManager.getSystemReport().overallScore))%")
                            .font(PremiumDesignSystem.Typography.caption)
                            .fontWeight(.semibold)
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
    
    // MARK: - Performance State Card
    
    private var performanceStateCard: some View {
        PremiumCard(style: .elevated) {
            VStack(spacing: 16) {
                HStack {
                    Image(systemName: "speedometer")
                        .font(.title)
                        .foregroundColor(integratedManager.performanceState.color)
                    
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Performance State")
                            .font(PremiumDesignSystem.Typography.headline)
                        
                        Text(integratedManager.performanceState.description)
                            .font(PremiumDesignSystem.Typography.subheadline)
                            .foregroundColor(PremiumDesignSystem.Colors.secondaryText)
                    }
                    
                    Spacer()
                    
                    if integratedManager.optimizationLevel != .none {
                        OptimizationBadge(level: integratedManager.optimizationLevel)
                    }
                }
                
                // Real-time Metrics Preview
                HStack(spacing: 20) {
                    MetricPreview(
                        title: "FPS",
                        value: String(format: "%.0f", integratedManager.performanceAnalytics.metrics.frameRate),
                        color: integratedManager.performanceAnalytics.metrics.frameRate >= 55 ? .green : .orange
                    )
                    
                    MetricPreview(
                        title: "Memory",
                        value: String(format: "%.0fMB", integratedManager.performanceAnalytics.metrics.memoryUsage),
                        color: integratedManager.performanceAnalytics.metrics.memoryUsage < 200 ? .green : .orange
                    )
                    
                    MetricPreview(
                        title: "Battery",
                        value: String(format: "%.0f%%", integratedManager.batteryManager.batteryLevel * 100),
                        color: integratedManager.batteryManager.batteryLevel > 0.3 ? .green : .red
                    )
                }
            }
        }
        .hapticFeedback(.buttonTap)
    }
    
    // MARK: - Metric Categories Section
    
    private var metricCategoriesSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Performance Categories")
                .font(PremiumDesignSystem.Typography.title3)
                .fontWeight(.semibold)
            
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 12) {
                    ForEach(MetricCategory.allCases, id: \.rawValue) { category in
                        CategoryButton(
                            category: category,
                            isSelected: selectedMetricCategory == category
                        ) {
                            PremiumHaptics.selection()
                            withAnimation(PremiumTransitions.easeInOut) {
                                selectedMetricCategory = category
                            }
                        }
                    }
                }
                .padding(.horizontal)
            }
        }
    }
    
    // MARK: - Category Detail Section
    
    private var categoryDetailSection: some View {
        Group {
            switch selectedMetricCategory {
            case .overview:
                OverviewMetricsView(manager: integratedManager)
            case .performance:
                PerformanceMetricsView(analytics: integratedManager.performanceAnalytics)
            case .battery:
                BatteryMetricsView(manager: integratedManager.batteryManager)
            case .memory:
                MemoryMetricsView(manager: integratedManager.memoryManager)
            case .network:
                NetworkMetricsView(manager: integratedManager.networkManager)
            case .voice:
                VoiceMetricsView(manager: integratedManager.voiceManager)
            }
        }
        .transition(PremiumTransitions.cardTransition)
        .animation(PremiumTransitions.spring, value: selectedMetricCategory)
    }
    
    // MARK: - System Alerts Section
    
    private var systemAlertsSection: some View {
        Group {
            if !integratedManager.alerts.isEmpty {
                VStack(alignment: .leading, spacing: 12) {
                    HStack {
                        Text("System Alerts")
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
                        ForEach(integratedManager.alerts.prefix(5)) { alert in
                            SystemAlertRow(alert: alert) {
                                PremiumHaptics.contextualFeedback(for: .buttonTap)
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
            
            HStack(spacing: 12) {
                Button("Optimize") {
                    PremiumHaptics.contextualFeedback(for: .saveAction)
                    integratedManager.manualOptimization()
                }
                .premiumButtonStyle(variant: .primary)
                
                Button("Reset") {
                    PremiumHaptics.contextualFeedback(for: .buttonTap)
                    integratedManager.resetOptimizations()
                }
                .premiumButtonStyle(variant: .outline)
                
                Spacer()
            }
        }
    }
}

// MARK: - Supporting Views

struct SystemHealthIndicator: View {
    let health: IntegratedPerformanceManager.SystemHealth
    
    var body: some View {
        ZStack {
            Circle()
                .stroke(health.color.opacity(0.3), lineWidth: 3)
                .frame(width: 40, height: 40)
            
            Circle()
                .trim(from: 0, to: healthProgress)
                .stroke(health.color, style: StrokeStyle(lineWidth: 3, lineCap: .round))
                .frame(width: 40, height: 40)
                .rotationEffect(.degrees(-90))
                .animation(.easeInOut(duration: 1.0), value: healthProgress)
            
            Text(healthIcon)
                .font(.caption)
        }
    }
    
    private var healthProgress: CGFloat {
        switch health {
        case .excellent: return 1.0
        case .good: return 0.75
        case .fair: return 0.5
        case .poor: return 0.25
        }
    }
    
    private var healthIcon: String {
        switch health {
        case .excellent: return "✓"
        case .good: return "○"
        case .fair: return "△"
        case .poor: return "✗"
        }
    }
}

struct OptimizationBadge: View {
    let level: IntegratedPerformanceManager.OptimizationLevel
    
    var body: some View {
        Text(level.description)
            .font(.caption2)
            .fontWeight(.medium)
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(badgeColor.opacity(0.2))
            .foregroundColor(badgeColor)
            .cornerRadius(8)
    }
    
    private var badgeColor: Color {
        switch level {
        case .none: return .gray
        case .light: return .blue
        case .moderate: return .orange
        case .aggressive: return .red
        }
    }
}

struct MetricPreview: View {
    let title: String
    let value: String
    let color: Color
    
    var body: some View {
        VStack(spacing: 4) {
            Text(title)
                .font(.caption)
                .foregroundColor(PremiumDesignSystem.Colors.secondaryText)
            
            Text(value)
                .font(.headline)
                .fontWeight(.semibold)
                .foregroundColor(color)
        }
    }
}

struct CategoryButton: View {
    let category: SystemPerformanceView.MetricCategory
    let isSelected: Bool
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            HStack(spacing: 8) {
                Image(systemName: category.icon)
                    .font(.caption)
                
                Text(category.rawValue)
                    .font(.caption)
                    .fontWeight(.medium)
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
            .background(
                RoundedRectangle(cornerRadius: 20)
                    .fill(isSelected ? PremiumDesignSystem.Colors.primary : PremiumDesignSystem.Colors.secondaryBackground)
            )
            .foregroundColor(isSelected ? .white : PremiumDesignSystem.Colors.primaryText)
        }
        .scaleEffect(isSelected ? 1.05 : 1.0)
        .animation(PremiumTransitions.microInteraction, value: isSelected)
    }
}

struct SystemAlertRow: View {
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
                
                Text(timeAgo)
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
        .background(
            RoundedRectangle(cornerRadius: 8)
                .fill(alert.severity.color.opacity(0.1))
        )
    }
    
    private var timeAgo: String {
        let formatter = RelativeDateTimeFormatter()
        formatter.unitsStyle = .abbreviated
        return formatter.localizedString(for: alert.timestamp, relativeTo: Date())
    }
}

// MARK: - Detail Views (Placeholder implementations)

struct OverviewMetricsView: View {
    let manager: IntegratedPerformanceManager
    
    var body: some View {
        PremiumCard(style: .standard) {
            VStack(alignment: .leading, spacing: 16) {
                Text("System Overview")
                    .font(PremiumDesignSystem.Typography.headline)
                
                Text("All systems operating within normal parameters.")
                    .font(PremiumDesignSystem.Typography.body)
                    .foregroundColor(PremiumDesignSystem.Colors.secondaryText)
                
                HStack {
                    Text("Last Updated:")
                    Spacer()
                    Text(Date(), style: .time)
                        .foregroundColor(PremiumDesignSystem.Colors.secondaryText)
                }
                .font(PremiumDesignSystem.Typography.caption)
            }
        }
    }
}

struct PerformanceMetricsView: View {
    let analytics: PerformanceAnalytics
    
    var body: some View {
        PremiumCard(style: .standard) {
            VStack(alignment: .leading, spacing: 16) {
                Text("Performance Metrics")
                    .font(PremiumDesignSystem.Typography.headline)
                
                VStack(spacing: 12) {
                    MetricRow(title: "Frame Rate", value: "\(String(format: "%.1f", analytics.metrics.frameRate)) fps")
                    MetricRow(title: "Dropped Frames", value: "\(analytics.metrics.droppedFrames)")
                    MetricRow(title: "Memory Usage", value: "\(String(format: "%.1f", analytics.metrics.memoryUsage)) MB")
                }
            }
        }
    }
}

struct BatteryMetricsView: View {
    let manager: BatteryOptimizedManager
    
    var body: some View {
        PremiumCard(style: .standard) {
            VStack(alignment: .leading, spacing: 16) {
                Text("Battery Metrics")
                    .font(PremiumDesignSystem.Typography.headline)
                
                VStack(spacing: 12) {
                    MetricRow(title: "Battery Level", value: "\(String(format: "%.0f", manager.batteryLevel * 100))%")
                    MetricRow(title: "Usage Rate", value: "\(String(format: "%.1f", manager.batteryUsageRate))%/hr")
                    MetricRow(title: "Optimization", value: manager.optimizationLevel.description)
                }
            }
        }
    }
}

struct MemoryMetricsView: View {
    let manager: OptimizedArchitectureService
    
    var body: some View {
        PremiumCard(style: .standard) {
            VStack(alignment: .leading, spacing: 16) {
                Text("Memory Metrics")
                    .font(PremiumDesignSystem.Typography.headline)
                
                Text("Memory optimization and caching status.")
                    .font(PremiumDesignSystem.Typography.body)
                    .foregroundColor(PremiumDesignSystem.Colors.secondaryText)
            }
        }
    }
}

struct NetworkMetricsView: View {
    let manager: OptimizedWebSocketService
    
    var body: some View {
        PremiumCard(style: .standard) {
            VStack(alignment: .leading, spacing: 16) {
                Text("Network Metrics")
                    .font(PremiumDesignSystem.Typography.headline)
                
                Text("WebSocket connection and optimization status.")
                    .font(PremiumDesignSystem.Typography.body)
                    .foregroundColor(PremiumDesignSystem.Colors.secondaryText)
            }
        }
    }
}

struct VoiceMetricsView: View {
    let manager: OptimizedVoiceManager
    
    var body: some View {
        PremiumCard(style: .standard) {
            VStack(alignment: .leading, spacing: 16) {
                Text("Voice Metrics")
                    .font(PremiumDesignSystem.Typography.headline)
                
                VStack(spacing: 12) {
                    MetricRow(title: "Current Latency", value: "\(String(format: "%.2f", manager.currentLatency))s")
                    MetricRow(title: "Optimization Status", value: manager.isOptimized ? "Enabled" : "Disabled")
                }
            }
        }
    }
}

struct MetricRow: View {
    let title: String
    let value: String
    
    var body: some View {
        HStack {
            Text(title)
                .font(PremiumDesignSystem.Typography.body)
            
            Spacer()
            
            Text(value)
                .font(PremiumDesignSystem.Typography.body)
                .fontWeight(.medium)
                .foregroundColor(PremiumDesignSystem.Colors.primary)
        }
    }
}

struct DetailedMetricsView: View {
    let manager: IntegratedPerformanceManager
    
    var body: some View {
        NavigationView {
            ScrollView {
                LazyVStack(spacing: 20) {
                    Text("Detailed system metrics would be displayed here")
                        .font(PremiumDesignSystem.Typography.body)
                        .foregroundColor(PremiumDesignSystem.Colors.secondaryText)
                        .padding()
                }
            }
            .navigationTitle("Detailed Metrics")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Done") {
                        // Dismiss action would be handled by the parent
                    }
                }
            }
        }
    }
}