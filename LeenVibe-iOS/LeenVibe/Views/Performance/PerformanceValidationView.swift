import SwiftUI

// MARK: - Performance Validation View

struct PerformanceValidationView: View {
    @StateObject private var validationSuite: PerformanceValidationSuite
    @State private var showingDetailedReport = false
    @State private var currentReport: PerformanceValidationReport?
    
    init(
        performanceAnalytics: PerformanceAnalytics,
        batteryManager: BatteryOptimizedManager,
        memoryManager: OptimizedArchitectureService,
        voiceManager: OptimizedVoiceManager,
        networkManager: OptimizedWebSocketService,
        integratedManager: IntegratedPerformanceManager
    ) {
        self._validationSuite = StateObject(wrappedValue: PerformanceValidationSuite(
            performanceAnalytics: performanceAnalytics,
            batteryManager: batteryManager,
            memoryManager: memoryManager,
            voiceManager: voiceManager,
            networkManager: networkManager,
            integratedManager: integratedManager
        ))
    }
    
    var body: some View {
        NavigationView {
            ScrollView {
                LazyVStack(spacing: 20) {
                    // Validation Status Header
                    validationStatusHeader
                    
                    // Run Validation Section
                    runValidationSection
                    
                    // Current Test Progress
                    if validationSuite.isRunning {
                        currentTestProgress
                    }
                    
                    // Validation Results
                    if !validationSuite.validationResults.isEmpty {
                        validationResultsSection
                    }
                    
                    // Overall Score
                    if validationSuite.overallScore > 0 {
                        overallScoreSection
                    }
                }
                .padding()
            }
            .navigationTitle("Performance Validation")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    if let report = currentReport {
                        Button("Report") {
                            PremiumHaptics.contextualFeedback(for: .buttonTap)
                            showingDetailedReport = true
                        }
                    }
                }
            }
            .sheet(isPresented: $showingDetailedReport) {
                if let report = currentReport {
                    ValidationReportView(report: report)
                }
            }
        }
    }
    
    // MARK: - Validation Status Header
    
    private var validationStatusHeader: some View {
        PremiumCard(style: .glass) {
            VStack(spacing: 16) {
                HStack {
                    Image(systemName: "checkmark.shield.fill")
                        .font(.title)
                        .foregroundColor(validationSuite.overallScore >= 80 ? .green : .orange)
                    
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Performance Validation")
                            .font(PremiumDesignSystem.Typography.headline)
                        
                        Text(validationStatusText)
                            .font(PremiumDesignSystem.Typography.subheadline)
                            .foregroundColor(PremiumDesignSystem.Colors.secondaryText)
                    }
                    
                    Spacer()
                    
                    if validationSuite.isRunning {
                        PremiumLoadingView(size: 30)
                    }
                }
                
                if validationSuite.overallScore > 0 {
                    VStack(spacing: 8) {
                        HStack {
                            Text("Overall Score")
                                .font(PremiumDesignSystem.Typography.body)
                            
                            Spacer()
                            
                            Text("\(Int(validationSuite.overallScore))%")
                                .font(PremiumDesignSystem.Typography.title2)
                                .fontWeight(.bold)
                                .foregroundColor(scoreColor)
                        }
                        
                        PremiumProgressBar(
                            progress: validationSuite.overallScore / 100.0,
                            color: scoreColor
                        )
                    }
                }
            }
        }
    }
    
    // MARK: - Run Validation Section
    
    private var runValidationSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Performance Tests")
                .font(PremiumDesignSystem.Typography.title3)
                .fontWeight(.semibold)
            
            PremiumCard(style: .elevated) {
                VStack(spacing: 16) {
                    HStack {
                        VStack(alignment: .leading, spacing: 4) {
                            Text("Comprehensive Performance Validation")
                                .font(PremiumDesignSystem.Typography.headline)
                            
                            Text("Tests memory, voice, animation, battery, and system integration")
                                .font(PremiumDesignSystem.Typography.caption)
                                .foregroundColor(PremiumDesignSystem.Colors.secondaryText)
                        }
                        
                        Spacer()
                        
                        if !validationSuite.isRunning {
                            Button("Run Tests") {
                                PremiumHaptics.contextualFeedback(for: .saveAction)
                                Task {
                                    await validationSuite.runFullValidation()
                                    currentReport = validationSuite.generateValidationReport()
                                }
                            }
                            .premiumButtonStyle(variant: .primary)
                        }
                    }
                    
                    // Test Categories Preview
                    LazyVGrid(columns: [
                        GridItem(.flexible()),
                        GridItem(.flexible()),
                        GridItem(.flexible())
                    ], spacing: 8) {
                        TestCategoryBadge(title: "Memory", icon: "memorychip", color: .blue)
                        TestCategoryBadge(title: "Voice", icon: "mic", color: .green)
                        TestCategoryBadge(title: "Animation", icon: "wand.and.rays", color: .purple)
                        TestCategoryBadge(title: "Battery", icon: "battery.100", color: .orange)
                        TestCategoryBadge(title: "Network", icon: "network", color: .cyan)
                        TestCategoryBadge(title: "Integration", icon: "gearshape.2", color: .indigo)
                    }
                }
            }
        }
    }
    
    // MARK: - Current Test Progress
    
    private var currentTestProgress: some View {
        PremiumCard(style: .standard) {
            VStack(spacing: 12) {
                HStack {
                    Text("Running Test")
                        .font(PremiumDesignSystem.Typography.headline)
                    
                    Spacer()
                    
                    PremiumLoadingView(size: 20)
                }
                
                HStack {
                    Text(validationSuite.currentTest)
                        .font(PremiumDesignSystem.Typography.body)
                        .foregroundColor(PremiumDesignSystem.Colors.secondaryText)
                    
                    Spacer()
                }
            }
        }
        .transition(PremiumTransitions.fadeScale)
    }
    
    // MARK: - Validation Results Section
    
    private var validationResultsSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("Test Results")
                    .font(PremiumDesignSystem.Typography.title3)
                    .fontWeight(.semibold)
                
                Spacer()
                
                let passedCount = validationSuite.validationResults.filter { $0.passed }.count
                let totalCount = validationSuite.validationResults.count
                
                Text("\(passedCount)/\(totalCount) Passed")
                    .font(PremiumDesignSystem.Typography.caption)
                    .foregroundColor(passedCount == totalCount ? .green : .orange)
            }
            
            LazyVStack(spacing: 8) {
                ForEach(validationSuite.validationResults) { result in
                    ValidationResultCard(result: result)
                }
            }
        }
    }
    
    // MARK: - Overall Score Section
    
    private var overallScoreSection: some View {
        PremiumCard(style: .floating) {
            VStack(spacing: 16) {
                HStack {
                    Image(systemName: scoreIcon)
                        .font(.title)
                        .foregroundColor(scoreColor)
                    
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Performance Grade")
                            .font(PremiumDesignSystem.Typography.headline)
                        
                        Text(validationSuite.generateValidationReport().grade.rawValue)
                            .font(PremiumDesignSystem.Typography.title)
                            .fontWeight(.bold)
                            .foregroundColor(scoreColor)
                    }
                    
                    Spacer()
                    
                    VStack(alignment: .trailing, spacing: 4) {
                        Text("\(Int(validationSuite.overallScore))%")
                            .font(PremiumDesignSystem.Typography.title)
                            .fontWeight(.bold)
                            .foregroundColor(scoreColor)
                        
                        Text("Overall Score")
                            .font(PremiumDesignSystem.Typography.caption)
                            .foregroundColor(PremiumDesignSystem.Colors.secondaryText)
                    }
                }
                
                let report = validationSuite.generateValidationReport()
                HStack {
                    ProductionReadinessBadge(isReady: report.meetsCriteria)
                    
                    Spacer()
                    
                    Button("View Report") {
                        PremiumHaptics.contextualFeedback(for: .buttonTap)
                        currentReport = report
                        showingDetailedReport = true
                    }
                    .premiumButtonStyle(variant: .outline)
                }
            }
        }
    }
    
    // MARK: - Computed Properties
    
    private var validationStatusText: String {
        if validationSuite.isRunning {
            return "Running performance validation tests..."
        } else if validationSuite.validationResults.isEmpty {
            return "Ready to validate performance optimization"
        } else {
            let report = validationSuite.generateValidationReport()
            return report.meetsCriteria ? "All tests passed - Production ready!" : "Some tests failed - Review results"
        }
    }
    
    private var scoreColor: Color {
        let score = validationSuite.overallScore
        if score >= 90 { return .green }
        else if score >= 80 { return .blue }
        else if score >= 70 { return .orange }
        else { return .red }
    }
    
    private var scoreIcon: String {
        let score = validationSuite.overallScore
        if score >= 90 { return "star.fill" }
        else if score >= 80 { return "checkmark.circle.fill" }
        else if score >= 70 { return "exclamationmark.triangle.fill" }
        else { return "xmark.circle.fill" }
    }
}

// MARK: - Supporting Views

struct TestCategoryBadge: View {
    let title: String
    let icon: String
    let color: Color
    
    var body: some View {
        VStack(spacing: 4) {
            Image(systemName: icon)
                .font(.caption)
                .foregroundColor(color)
            
            Text(title)
                .font(.caption2)
                .fontWeight(.medium)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 8)
        .background(color.opacity(0.1))
        .cornerRadius(8)
    }
}

struct ValidationResultCard: View {
    let result: ValidationResult
    
    var body: some View {
        PremiumCard(style: .standard) {
            VStack(spacing: 12) {
                HStack {
                    Image(systemName: result.passed ? "checkmark.circle.fill" : "xmark.circle.fill")
                        .font(.title3)
                        .foregroundColor(result.status.color)
                    
                    VStack(alignment: .leading, spacing: 2) {
                        Text(result.testName)
                            .font(PremiumDesignSystem.Typography.subheadline)
                            .fontWeight(.medium)
                        
                        Text(result.details)
                            .font(PremiumDesignSystem.Typography.caption)
                            .foregroundColor(PremiumDesignSystem.Colors.secondaryText)
                    }
                    
                    Spacer()
                    
                    VStack(alignment: .trailing, spacing: 2) {
                        Text(result.status.description)
                            .font(PremiumDesignSystem.Typography.caption)
                            .fontWeight(.medium)
                            .foregroundColor(result.status.color)
                        
                        Text("\(String(format: "%.2f", result.actualValue)) \(result.unit)")
                            .font(PremiumDesignSystem.Typography.caption2)
                            .foregroundColor(PremiumDesignSystem.Colors.tertiaryText)
                    }
                }
                
                // Performance Bar
                VStack(spacing: 4) {
                    HStack {
                        Text("Target: \(String(format: "%.2f", result.targetValue)) \(result.unit)")
                            .font(PremiumDesignSystem.Typography.caption2)
                            .foregroundColor(PremiumDesignSystem.Colors.tertiaryText)
                        
                        Spacer()
                        
                        Text("Execution: \(String(format: "%.3f", result.executionTime))s")
                            .font(PremiumDesignSystem.Typography.caption2)
                            .foregroundColor(PremiumDesignSystem.Colors.tertiaryText)
                    }
                    
                    PerformanceComparisonBar(
                        target: result.targetValue,
                        actual: result.actualValue,
                        passed: result.passed
                    )
                }
            }
        }
        .hapticFeedback(.buttonTap)
    }
}

struct PerformanceComparisonBar: View {
    let target: Double
    let actual: Double
    let passed: Bool
    
    var body: some View {
        GeometryReader { geometry in
            ZStack(alignment: .leading) {
                // Background
                Rectangle()
                    .fill(Color.gray.opacity(0.2))
                    .frame(height: 6)
                    .cornerRadius(3)
                
                // Target line
                Rectangle()
                    .fill(Color.blue.opacity(0.5))
                    .frame(width: 2, height: 10)
                    .offset(x: targetPosition(in: geometry.size.width))
                
                // Actual value bar
                Rectangle()
                    .fill(passed ? Color.green : Color.red)
                    .frame(width: actualWidth(in: geometry.size.width), height: 6)
                    .cornerRadius(3)
            }
        }
        .frame(height: 10)
    }
    
    private func targetPosition(in width: CGFloat) -> CGFloat {
        let maxValue = max(target, actual) * 1.2
        return (target / maxValue) * width
    }
    
    private func actualWidth(in width: CGFloat) -> CGFloat {
        let maxValue = max(target, actual) * 1.2
        return (actual / maxValue) * width
    }
}

struct ProductionReadinessBadge: View {
    let isReady: Bool
    
    var body: some View {
        HStack(spacing: 6) {
            Image(systemName: isReady ? "checkmark.seal.fill" : "exclamationmark.triangle.fill")
                .font(.caption)
                .foregroundColor(isReady ? .green : .orange)
            
            Text(isReady ? "Production Ready" : "Needs Attention")
                .font(.caption)
                .fontWeight(.medium)
                .foregroundColor(isReady ? .green : .orange)
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 6)
        .background((isReady ? Color.green : Color.orange).opacity(0.1))
        .cornerRadius(12)
    }
}

// MARK: - Validation Report View

struct ValidationReportView: View {
    let report: PerformanceValidationReport
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            ScrollView {
                LazyVStack(alignment: .leading, spacing: 20) {
                    // Report Header
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Performance Validation Report")
                            .font(PremiumDesignSystem.Typography.largeTitle)
                            .fontWeight(.bold)
                        
                        Text("Generated: \(report.timestamp.formatted())")
                            .font(PremiumDesignSystem.Typography.caption)
                            .foregroundColor(PremiumDesignSystem.Colors.secondaryText)
                    }
                    
                    // Summary Card
                    PremiumCard(style: .elevated) {
                        VStack(alignment: .leading, spacing: 16) {
                            Text("Summary")
                                .font(PremiumDesignSystem.Typography.headline)
                            
                            VStack(spacing: 12) {
                                ReportSummaryRow(title: "Overall Score", value: "\(Int(report.overallScore))%")
                                ReportSummaryRow(title: "Grade", value: report.grade.rawValue)
                                ReportSummaryRow(title: "Tests Passed", value: "\(report.passedTests)/\(report.totalTests)")
                                ReportSummaryRow(title: "Production Ready", value: report.meetsCriteria ? "YES" : "NO")
                            }
                        }
                    }
                    
                    // Detailed Results
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Detailed Results")
                            .font(PremiumDesignSystem.Typography.title3)
                            .fontWeight(.semibold)
                        
                        ForEach(report.results) { result in
                            ValidationResultCard(result: result)
                        }
                    }
                }
                .padding()
            }
            .navigationTitle("Validation Report")
            .navigationBarTitleDisplayMode(.inline)
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

struct ReportSummaryRow: View {
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