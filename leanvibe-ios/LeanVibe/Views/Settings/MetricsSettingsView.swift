import SwiftUI

/// Metrics Settings view for configuring analytics and performance tracking
/// Provides controls for data collection, reporting, and privacy settings
@available(iOS 18.0, macOS 14.0, *)
struct MetricsSettingsView: View {
    
    // MARK: - Properties
    
    @ObservedObject var settingsManager: SettingsManager
    @State private var showingDataExport = false
    @State private var showingPrivacySettings = false
    
    // Local state for metrics settings
    @State private var enableMetricsCollection = true
    @State private var enablePerformanceTracking = true
    @State private var enableUsageAnalytics = false
    @State private var enableCrashReporting = true
    @State private var enableAnonymousReporting = true
    @State private var dataRetentionPeriod: Double = 30
    @State private var reportingFrequency: ReportingFrequency = .weekly
    @State private var enableLocalAnalytics = true
    @State private var enableTrendAnalysis = true
    @State private var enableProductivityMetrics = true
    @State private var enableTeamMetrics = false
    @State private var enableBenchmarking = false
    @State private var enableRealTimeMetrics = true
    @State private var metricsDetailLevel: MetricsDetailLevel = .standard
    
    init(settingsManager: SettingsManager = SettingsManager.shared) {
        self.settingsManager = settingsManager
    }
    
    // MARK: - Body
    
    var body: some View {
        List {
            Section {
                Text("Configure data collection and analytics to improve your productivity and app performance.")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .padding(.vertical, 4)
            }
            
            // Privacy & Data Collection Section
            Section("Privacy & Data Collection") {
                Toggle("Enable Metrics Collection", isOn: $enableMetricsCollection)
                    .help("Allow the app to collect usage and performance metrics")
                
                if enableMetricsCollection {
                    Toggle("Anonymous Reporting Only", isOn: $enableAnonymousReporting)
                        .help("All data will be anonymized before collection")
                    
                    Toggle("Local Analytics Only", isOn: $enableLocalAnalytics)
                        .help("Keep all analytics data on this device")
                    
                    NavigationLink("Privacy Settings") {
                        MetricsPrivacyView()
                    }
                }
            }
            
            // Performance Tracking Section
            Section("Performance Tracking") {
                Toggle("Performance Monitoring", isOn: $enablePerformanceTracking)
                    .help("Track app performance and response times")
                
                Toggle("Crash Reporting", isOn: $enableCrashReporting)
                    .help("Automatically report crashes to help improve stability")
                
                Toggle("Real-time Metrics", isOn: $enableRealTimeMetrics)
                    .help("Enable live performance monitoring")
                
                if enablePerformanceTracking {
                    Picker("Detail Level", selection: $metricsDetailLevel) {
                        Text("Basic").tag(MetricsDetailLevel.basic)
                        Text("Standard").tag(MetricsDetailLevel.standard)
                        Text("Detailed").tag(MetricsDetailLevel.detailed)
                        Text("Comprehensive").tag(MetricsDetailLevel.comprehensive)
                    }
                    .pickerStyle(MenuPickerStyle())
                }
            }
            
            // Usage Analytics Section
            Section("Usage Analytics") {
                Toggle("Usage Analytics", isOn: $enableUsageAnalytics)
                    .help("Track feature usage and user interaction patterns")
                
                Toggle("Productivity Metrics", isOn: $enableProductivityMetrics)
                    .help("Analyze your task completion and productivity patterns")
                
                Toggle("Trend Analysis", isOn: $enableTrendAnalysis)
                    .help("Identify patterns and trends in your work")
                
                if enableUsageAnalytics {
                    NavigationLink("Analytics Dashboard") {
                        MetricsAnalyticsDashboardView()
                    }
                }
            }
            
            // Team & Collaboration Section
            Section("Team & Collaboration") {
                Toggle("Team Metrics", isOn: $enableTeamMetrics)
                    .help("Collect metrics for team collaboration features")
                
                Toggle("Benchmarking", isOn: $enableBenchmarking)
                    .help("Compare your productivity with anonymized benchmarks")
                
                if enableTeamMetrics {
                    Text("Team metrics are shared only with your team members and require explicit consent from all participants.")
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .padding(.vertical, 4)
                }
            }
            
            // Data Retention Section
            Section("Data Retention") {
                VStack(alignment: .leading, spacing: 8) {
                    Text("Data Retention: \(Int(dataRetentionPeriod)) days")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    
                    Slider(value: $dataRetentionPeriod, in: 7...365, step: 7) {
                        Text("Data Retention Period")
                    }
                    .help("How long to keep metrics data on this device")
                }
                .padding(.vertical, 4)
                
                Picker("Reporting Frequency", selection: $reportingFrequency) {
                    Text("Daily").tag(ReportingFrequency.daily)
                    Text("Weekly").tag(ReportingFrequency.weekly)
                    Text("Monthly").tag(ReportingFrequency.monthly)
                    Text("Never").tag(ReportingFrequency.never)
                }
                .pickerStyle(MenuPickerStyle())
                .help("How often to generate summary reports")
            }
            
            // Data Management Section
            Section("Data Management") {
                NavigationLink("View Collected Data") {
                    MetricsDataView()
                }
                
                Button("Export Metrics Data") {
                    showingDataExport = true
                }
                .foregroundColor(.blue)
                
                Button("Clear All Metrics Data") {
                    clearAllMetricsData()
                }
                .foregroundColor(.red)
                
                NavigationLink("Data Usage Statistics") {
                    MetricsDataUsageView()
                }
            }
            
            // Insights & Reports Section
            Section("Insights & Reports") {
                NavigationLink("Productivity Insights") {
                    ProductivityInsightsView()
                }
                
                NavigationLink("Performance Reports") {
                    PerformanceReportsView()
                }
                
                NavigationLink("Custom Reports") {
                    CustomReportsView()
                }
                
                if enableTrendAnalysis {
                    NavigationLink("Trend Analysis") {
                        TrendAnalysisView()
                    }
                }
            }
        }
        .navigationTitle("Metrics Settings")
        .navigationBarTitleDisplayMode(.large)
        .onAppear {
            loadSettings()
        }
        .onChange(of: enableMetricsCollection) { saveSettings() }
        .onChange(of: enablePerformanceTracking) { saveSettings() }
        .onChange(of: enableUsageAnalytics) { saveSettings() }
        .onChange(of: enableCrashReporting) { saveSettings() }
        .onChange(of: enableAnonymousReporting) { saveSettings() }
        .onChange(of: dataRetentionPeriod) { saveSettings() }
        .onChange(of: reportingFrequency) { saveSettings() }
        .onChange(of: enableLocalAnalytics) { saveSettings() }
        .onChange(of: enableTrendAnalysis) { saveSettings() }
        .onChange(of: enableProductivityMetrics) { saveSettings() }
        .onChange(of: enableTeamMetrics) { saveSettings() }
        .onChange(of: enableBenchmarking) { saveSettings() }
        .onChange(of: enableRealTimeMetrics) { saveSettings() }
        .onChange(of: metricsDetailLevel) { saveSettings() }
        .sheet(isPresented: $showingDataExport) {
            MetricsDataExportView()
        }
    }
    
    // MARK: - Methods
    
    private func loadSettings() {
        let settings = settingsManager.metrics
        
        enableMetricsCollection = settings.enableMetricsCollection
        enablePerformanceTracking = settings.enablePerformanceTracking
        enableUsageAnalytics = settings.enableUsageAnalytics
        enableCrashReporting = settings.enableCrashReporting
        enableAnonymousReporting = settings.enableAnonymousReporting
        dataRetentionPeriod = Double(settings.dataRetentionPeriod)
        reportingFrequency = ReportingFrequency(rawValue: settings.reportingFrequency) ?? .weekly
        enableLocalAnalytics = settings.enableLocalAnalytics
        enableTrendAnalysis = settings.enableTrendAnalysis
        enableProductivityMetrics = settings.enableProductivityMetrics
        enableTeamMetrics = settings.enableTeamMetrics
        enableBenchmarking = settings.enableBenchmarking
        enableRealTimeMetrics = settings.enableRealTimeMetrics
        metricsDetailLevel = MetricsDetailLevel(rawValue: settings.metricsDetailLevel) ?? .standard
        
        print("✅ Metrics settings loaded from SettingsManager")
    }
    
    private func saveSettings() {
        var settings = settingsManager.metrics
        
        settings.enableMetricsCollection = enableMetricsCollection
        settings.enablePerformanceTracking = enablePerformanceTracking
        settings.enableUsageAnalytics = enableUsageAnalytics
        settings.enableCrashReporting = enableCrashReporting
        settings.enableAnonymousReporting = enableAnonymousReporting
        settings.dataRetentionPeriod = Int(dataRetentionPeriod)
        settings.reportingFrequency = reportingFrequency.rawValue
        settings.enableLocalAnalytics = enableLocalAnalytics
        settings.enableTrendAnalysis = enableTrendAnalysis
        settings.enableProductivityMetrics = enableProductivityMetrics
        settings.enableTeamMetrics = enableTeamMetrics
        settings.enableBenchmarking = enableBenchmarking
        settings.enableRealTimeMetrics = enableRealTimeMetrics
        settings.metricsDetailLevel = metricsDetailLevel.rawValue
        
        settingsManager.metrics = settings
        
        print("✅ Metrics settings saved to SettingsManager")
    }
    
    private func clearAllMetricsData() {
        // Clear all stored metrics data
        UserDefaults.standard.removeObject(forKey: "MetricsData")
        print("✅ All metrics data cleared")
    }
}

// MARK: - Supporting Views

struct MetricsPrivacyView: View {
    var body: some View {
        List {
            Section {
                Text("Learn about what data is collected and how it's used to improve your experience.")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .padding(.vertical, 4)
            }
            
            Section("Data Collection Details") {
                Text("Privacy settings and data collection details will be implemented here.")
                    .font(.body)
                    .foregroundColor(.secondary)
            }
        }
        .navigationTitle("Privacy Settings")
        .navigationBarTitleDisplayMode(.large)
    }
}

struct MetricsAnalyticsDashboardView: View {
    var body: some View {
        List {
            Section {
                Text("View your usage analytics and productivity insights.")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .padding(.vertical, 4)
            }
            
            Section("Analytics Dashboard") {
                Text("Comprehensive analytics dashboard will be implemented here.")
                    .font(.body)
                    .foregroundColor(.secondary)
            }
        }
        .navigationTitle("Analytics Dashboard")
        .navigationBarTitleDisplayMode(.large)
    }
}

struct MetricsDataView: View {
    var body: some View {
        List {
            Section {
                Text("View all data that has been collected by the app.")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .padding(.vertical, 4)
            }
            
            Section("Collected Data") {
                Text("Data viewer will be implemented here.")
                    .font(.body)
                    .foregroundColor(.secondary)
            }
        }
        .navigationTitle("Collected Data")
        .navigationBarTitleDisplayMode(.large)
    }
}

struct MetricsDataExportView: View {
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            List {
                Section {
                    Text("Export your metrics data in various formats.")
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .padding(.vertical, 4)
                }
                
                Section("Export Options") {
                    Text("Data export functionality will be implemented here.")
                        .font(.body)
                        .foregroundColor(.secondary)
                }
            }
            .navigationTitle("Export Data")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Done") {
                        dismiss()
                    }
                }
            }
        }
    }
}

struct MetricsDataUsageView: View {
    var body: some View {
        List {
            Section {
                Text("View statistics about your metrics data usage and storage.")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .padding(.vertical, 4)
            }
            
            Section("Data Usage") {
                Text("Data usage statistics will be implemented here.")
                    .font(.body)
                    .foregroundColor(.secondary)
            }
        }
        .navigationTitle("Data Usage")
        .navigationBarTitleDisplayMode(.large)
    }
}

struct ProductivityInsightsView: View {
    var body: some View {
        List {
            Section {
                Text("Discover insights about your productivity patterns and habits.")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .padding(.vertical, 4)
            }
            
            Section("Productivity Insights") {
                Text("Productivity insights will be implemented here.")
                    .font(.body)
                    .foregroundColor(.secondary)
            }
        }
        .navigationTitle("Productivity Insights")
        .navigationBarTitleDisplayMode(.large)
    }
}

struct PerformanceReportsView: View {
    var body: some View {
        List {
            Section {
                Text("View detailed reports about app performance and system metrics.")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .padding(.vertical, 4)
            }
            
            Section("Performance Reports") {
                Text("Performance reports will be implemented here.")
                    .font(.body)
                    .foregroundColor(.secondary)
            }
        }
        .navigationTitle("Performance Reports")
        .navigationBarTitleDisplayMode(.large)
    }
}

struct CustomReportsView: View {
    var body: some View {
        List {
            Section {
                Text("Create and customize your own metrics reports.")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .padding(.vertical, 4)
            }
            
            Section("Custom Reports") {
                Text("Custom report builder will be implemented here.")
                    .font(.body)
                    .foregroundColor(.secondary)
            }
        }
        .navigationTitle("Custom Reports")
        .navigationBarTitleDisplayMode(.large)
    }
}

struct TrendAnalysisView: View {
    var body: some View {
        List {
            Section {
                Text("Analyze trends in your productivity and app usage over time.")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .padding(.vertical, 4)
            }
            
            Section("Trend Analysis") {
                Text("Trend analysis charts and insights will be implemented here.")
                    .font(.body)
                    .foregroundColor(.secondary)
            }
        }
        .navigationTitle("Trend Analysis")
        .navigationBarTitleDisplayMode(.large)
    }
}

// MARK: - Supporting Types

enum ReportingFrequency: String, CaseIterable {
    case daily = "daily"
    case weekly = "weekly"
    case monthly = "monthly"
    case never = "never"
    
    var displayName: String {
        switch self {
        case .daily: return "Daily"
        case .weekly: return "Weekly"
        case .monthly: return "Monthly"
        case .never: return "Never"
        }
    }
}

enum MetricsDetailLevel: String, CaseIterable {
    case basic = "basic"
    case standard = "standard"
    case detailed = "detailed"
    case comprehensive = "comprehensive"
    
    var displayName: String {
        switch self {
        case .basic: return "Basic"
        case .standard: return "Standard"
        case .detailed: return "Detailed"
        case .comprehensive: return "Comprehensive"
        }
    }
}

#Preview {
    MetricsSettingsView()
}