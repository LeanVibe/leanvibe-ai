import SwiftUI

// MARK: - Production Readiness Dashboard

struct ProductionReadinessView: View {
    @StateObject private var validator: ProductionReadinessValidator
    @State private var showingDetailedReport = false
    @State private var currentReport: ProductionReadinessReport?
    
    init(
        performanceValidator: PerformanceValidationSuite,
        integratedManager: IntegratedPerformanceManager
    ) {
        self._validator = StateObject(wrappedValue: ProductionReadinessValidator(
            performanceValidator: performanceValidator,
            integratedManager: integratedManager
        ))
    }
    
    var body: some View {
        NavigationView {
            ScrollView {
                LazyVStack(spacing: 24) {
                    // Production Status Header
                    productionStatusHeader
                    
                    // Quick Action Section
                    quickActionSection
                    
                    // Current Validation Progress
                    if validator.isValidating {
                        validationProgressSection
                    }
                    
                    // Validation Results by Category
                    if !validator.validationResults.isEmpty {
                        validationResultsSection
                    }
                    
                    // Production Score & Grade
                    if validator.readinessScore > 0 {
                        productionScoreSection
                    }
                    
                    // Final Assessment
                    if !validator.validationResults.isEmpty {
                        finalAssessmentSection
                    }
                }
                .padding()
            }
            .navigationTitle("Production Readiness")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItemGroup(placement: .navigationBarTrailing) {
                    if let report = currentReport {
                        Button("Export Report") {
                            PremiumHaptics.contextualFeedback(for: .buttonTap)
                            showingDetailedReport = true
                        }
                    }
                    
                    if !validator.isValidating && !validator.validationResults.isEmpty {
                        Button("Refresh") {
                            PremiumHaptics.contextualFeedback(for: .refreshData)
                            runValidation()
                        }
                    }
                }
            }
            .sheet(isPresented: $showingDetailedReport) {
                if let report = currentReport {
                    ProductionReportView(report: report)
                }
            }
        }
    }
    
    // MARK: - Production Status Header
    
    private var productionStatusHeader: some View {
        PremiumCard(style: .glass) {
            VStack(spacing: 20) {
                HStack {
                    ProductionStatusIndicator(
                        isReady: validator.isProductionReady,
                        isValidating: validator.isValidating
                    )
                    
                    VStack(alignment: .leading, spacing: 6) {
                        Text("Production Status")
                            .font(PremiumDesignSystem.Typography.headline)
                        
                        Text(productionStatusText)
                            .font(PremiumDesignSystem.Typography.subheadline)
                            .foregroundColor(productionStatusColor)
                    }
                    
                    Spacer()
                    
                    if validator.readinessScore > 0 {
                        VStack(alignment: .trailing, spacing: 4) {
                            Text("\(Int(validator.readinessScore))%")
                                .font(PremiumDesignSystem.Typography.title)
                                .fontWeight(.bold)
                                .foregroundColor(readinessScoreColor)
                            
                            Text("Ready")
                                .font(PremiumDesignSystem.Typography.caption)
                                .foregroundColor(PremiumDesignSystem.Colors.secondaryText)
                        }
                    }
                }
                
                if validator.readinessScore > 0 {
                    VStack(spacing: 8) {
                        HStack {
                            Text("Production Readiness")
                                .font(PremiumDesignSystem.Typography.body)
                            
                            Spacer()
                            
                            Text(getProductionGrade().rawValue)
                                .font(PremiumDesignSystem.Typography.body)
                                .fontWeight(.bold)
                                .foregroundColor(getProductionGrade().color)
                        }
                        
                        PremiumProgressBar(
                            progress: validator.readinessScore / 100.0,
                            color: readinessScoreColor
                        )
                    }
                }
            }
        }
    }
    
    // MARK: - Quick Action Section
    
    private var quickActionSection: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Production Validation")
                .font(PremiumDesignSystem.Typography.title3)
                .fontWeight(.semibold)
            
            PremiumCard(style: .elevated) {
                VStack(spacing: 20) {
                    HStack {
                        VStack(alignment: .leading, spacing: 8) {
                            Text("Comprehensive Production Readiness Check")
                                .font(PremiumDesignSystem.Typography.headline)
                            
                            Text("Validates performance, stability, efficiency, quality, UX, security, integration, and App Store readiness")
                                .font(PremiumDesignSystem.Typography.caption)
                                .foregroundColor(PremiumDesignSystem.Colors.secondaryText)
                        }
                        
                        Spacer()
                    }
                    
                    if !validator.isValidating {
                        Button("Run Production Validation") {
                            PremiumHaptics.contextualFeedback(for: .saveAction)
                            runValidation()
                        }
                        .premiumButtonStyle(variant: .primary)
                        .frame(maxWidth: .infinity)
                    } else {
                        HStack {
                            PremiumLoadingView(size: 20)
                            Text("Running Validation...")
                                .font(PremiumDesignSystem.Typography.body)
                                .foregroundColor(PremiumDesignSystem.Colors.secondaryText)
                        }
                        .frame(maxWidth: .infinity)
                        .padding()
                    }
                }
            }
        }
    }
    
    // MARK: - Validation Progress Section
    
    private var validationProgressSection: some View {
        PremiumCard(style: .standard) {
            VStack(spacing: 16) {
                HStack {
                    Text("Current Validation")
                        .font(PremiumDesignSystem.Typography.headline)
                    
                    Spacer()
                    
                    PremiumLoadingView(size: 24)
                }
                
                HStack {
                    Text(validator.currentCheck)
                        .font(PremiumDesignSystem.Typography.body)
                        .foregroundColor(PremiumDesignSystem.Colors.primary)
                    
                    Spacer()
                }
                
                // Progress indicator
                let progress = Double(validator.validationResults.count) / 8.0 // 8 main categories
                PremiumProgressBar(
                    progress: progress,
                    color: PremiumDesignSystem.Colors.primary
                )
            }
        }
        .transition(PremiumTransitions.fadeScale)
    }
    
    // MARK: - Validation Results Section
    
    private var validationResultsSection: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                Text("Validation Results")
                    .font(PremiumDesignSystem.Typography.title3)
                    .fontWeight(.semibold)
                
                Spacer()
                
                let passedCount = validator.validationResults.filter { $0.passed }.count
                let totalCount = validator.validationResults.count
                
                Text("\(passedCount)/\(totalCount) Passed")
                    .font(PremiumDesignSystem.Typography.caption)
                    .foregroundColor(passedCount == totalCount ? .green : .orange)
            }
            
            // Results by Category
            let groupedResults = Dictionary(grouping: validator.validationResults) { $0.category }
            
            LazyVStack(spacing: 12) {
                ForEach(ProductionCategory.allCases, id: \.rawValue) { category in
                    if let results = groupedResults[category] {
                        ProductionCategoryCard(
                            category: category,
                            results: results
                        )
                    }
                }
            }
        }
    }
    
    // MARK: - Production Score Section
    
    private var productionScoreSection: some View {
        PremiumCard(style: .floating) {
            VStack(spacing: 20) {
                HStack {
                    Image(systemName: getProductionGrade().rawValue == "A+" ? "star.fill" : "checkmark.seal.fill")
                        .font(.largeTitle)
                        .foregroundColor(getProductionGrade().color)
                    
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Production Grade")
                            .font(PremiumDesignSystem.Typography.headline)
                        
                        Text(getProductionGrade().rawValue)
                            .font(PremiumDesignSystem.Typography.largeTitle)
                            .fontWeight(.bold)
                            .foregroundColor(getProductionGrade().color)
                    }
                    
                    Spacer()
                    
                    VStack(alignment: .trailing, spacing: 4) {
                        Text("\(Int(validator.readinessScore))%")
                            .font(PremiumDesignSystem.Typography.largeTitle)
                            .fontWeight(.bold)
                            .foregroundColor(readinessScoreColor)
                        
                        Text("Score")
                            .font(PremiumDesignSystem.Typography.caption)
                            .foregroundColor(PremiumDesignSystem.Colors.secondaryText)
                    }
                }
                
                Text(getProductionGrade().description)
                    .font(PremiumDesignSystem.Typography.body)
                    .foregroundColor(PremiumDesignSystem.Colors.secondaryText)
                    .multilineTextAlignment(.center)
            }
        }
    }
    
    // MARK: - Final Assessment Section
    
    private var finalAssessmentSection: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Final Assessment")
                .font(PremiumDesignSystem.Typography.title3)
                .fontWeight(.semibold)
            
            PremiumCard(style: validator.isProductionReady ? .standard : .elevated) {
                VStack(spacing: 16) {
                    HStack {
                        Image(systemName: validator.isProductionReady ? "checkmark.circle.fill" : "exclamationmark.triangle.fill")
                            .font(.title)
                            .foregroundColor(validator.isProductionReady ? .green : .orange)
                        
                        VStack(alignment: .leading, spacing: 4) {
                            Text(validator.isProductionReady ? "Ready for Production" : "Requires Attention")
                                .font(PremiumDesignSystem.Typography.headline)
                                .foregroundColor(validator.isProductionReady ? .green : .orange)
                            
                            Text(finalAssessmentText)
                                .font(PremiumDesignSystem.Typography.body)
                                .foregroundColor(PremiumDesignSystem.Colors.secondaryText)
                        }
                        
                        Spacer()
                    }
                    
                    if validator.isProductionReady {
                        ProductionReadyActions()
                    } else {
                        ProductionIssuesActions(
                            criticalIssues: getCriticalIssuesCount(),
                            failedTests: getFailedTestsCount()
                        )
                    }
                }
            }
        }
    }
    
    // MARK: - Helper Methods
    
    private func runValidation() {
        Task {
            await validator.validateProductionReadiness()
            currentReport = validator.generateProductionReport()
        }
    }
    
    private var productionStatusText: String {
        if validator.isValidating {
            return "Validating production readiness..."
        } else if validator.validationResults.isEmpty {
            return "Ready to validate production readiness"
        } else if validator.isProductionReady {
            return "Application is ready for production deployment"
        } else {
            return "Application requires improvements before production"
        }
    }
    
    private var productionStatusColor: Color {
        if validator.isValidating {
            return PremiumDesignSystem.Colors.primary
        } else if validator.isProductionReady {
            return .green
        } else {
            return .orange
        }
    }
    
    private var readinessScoreColor: Color {
        let score = validator.readinessScore
        if score >= 90 { return .green }
        else if score >= 80 { return .blue }
        else if score >= 70 { return .orange }
        else { return .red }
    }
    
    private func getProductionGrade() -> ProductionGrade {
        if validator.readinessScore >= 95 { return .A }
        else if validator.readinessScore >= 85 { return .B }
        else if validator.readinessScore >= 75 { return .C }
        else if validator.readinessScore >= 65 { return .D }
        else { return .F }
    }
    
    private var finalAssessmentText: String {
        if validator.isProductionReady {
            return "All critical systems are operational and meet production standards. Application is ready for App Store submission."
        } else {
            let criticalIssues = getCriticalIssuesCount()
            let failedTests = getFailedTestsCount()
            
            if criticalIssues > 0 {
                return "\(criticalIssues) critical issue(s) detected. These must be resolved before production deployment."
            } else {
                return "\(failedTests) test(s) failed. Review and address these issues to improve production readiness."
            }
        }
    }
    
    private func getCriticalIssuesCount() -> Int {
        return validator.validationResults.reduce(0) { $0 + $1.criticalIssues }
    }
    
    private func getFailedTestsCount() -> Int {
        return validator.validationResults.filter { !$0.passed }.count
    }
}

// MARK: - Supporting Views

struct ProductionStatusIndicator: View {
    let isReady: Bool
    let isValidating: Bool
    @State private var isAnimating = false
    
    var body: some View {
        ZStack {
            Circle()
                .fill(indicatorColor.opacity(0.2))
                .frame(width: 60, height: 60)
            
            Circle()
                .stroke(indicatorColor, lineWidth: 3)
                .frame(width: 60, height: 60)
                .scaleEffect(isAnimating ? 1.1 : 1.0)
                .animation(.easeInOut(duration: 1.0).repeatForever(autoreverses: true), value: isAnimating)
            
            Image(systemName: indicatorIcon)
                .font(.title2)
                .foregroundColor(indicatorColor)
        }
        .onAppear {
            if isValidating {
                isAnimating = true
            }
        }
    }
    
    private var indicatorColor: Color {
        if isValidating {
            return .blue
        } else if isReady {
            return .green
        } else {
            return .orange
        }
    }
    
    private var indicatorIcon: String {
        if isValidating {
            return "gear"
        } else if isReady {
            return "checkmark"
        } else {
            return "exclamationmark"
        }
    }
}

struct ProductionCategoryCard: View {
    let category: ProductionCategory
    let results: [ProductionCheckResult]
    @State private var isExpanded = false
    
    var body: some View {
        PremiumCard(style: .standard) {
            VStack(spacing: 12) {
                Button(action: {
                    PremiumHaptics.selection()
                    withAnimation(PremiumTransitions.easeInOut) {
                        isExpanded.toggle()
                    }
                }) {
                    HStack {
                        Image(systemName: category.icon)
                            .font(.title3)
                            .foregroundColor(category.color)
                        
                        VStack(alignment: .leading, spacing: 2) {
                            Text(category.rawValue)
                                .font(PremiumDesignSystem.Typography.subheadline)
                                .fontWeight(.medium)
                            
                            let passedCount = results.filter { $0.passed }.count
                            Text("\(passedCount)/\(results.count) passed")
                                .font(PremiumDesignSystem.Typography.caption)
                                .foregroundColor(PremiumDesignSystem.Colors.secondaryText)
                        }
                        
                        Spacer()
                        
                        let categoryScore = results.reduce(0) { $0 + $1.score } / Double(results.count)
                        
                        VStack(alignment: .trailing, spacing: 2) {
                            Text("\(Int(categoryScore))%")
                                .font(PremiumDesignSystem.Typography.subheadline)
                                .fontWeight(.bold)
                                .foregroundColor(getScoreColor(categoryScore))
                            
                            Image(systemName: isExpanded ? "chevron.up" : "chevron.down")
                                .font(.caption)
                                .foregroundColor(PremiumDesignSystem.Colors.tertiaryText)
                        }
                    }
                }
                .buttonStyle(PlainButtonStyle())
                
                if isExpanded {
                    VStack(spacing: 8) {
                        ForEach(results) { result in
                            ProductionCheckRow(result: result)
                        }
                    }
                    .transition(PremiumTransitions.slideFromTop)
                }
            }
        }
    }
    
    private func getScoreColor(_ score: Double) -> Color {
        if score >= 90 { return .green }
        else if score >= 80 { return .blue }
        else if score >= 70 { return .orange }
        else { return .red }
    }
}

struct ProductionCheckRow: View {
    let result: ProductionCheckResult
    
    var body: some View {
        HStack {
            Image(systemName: result.passed ? "checkmark.circle.fill" : "xmark.circle.fill")
                .font(.caption)
                .foregroundColor(result.status.color)
            
            VStack(alignment: .leading, spacing: 2) {
                Text(result.checkName)
                    .font(.caption)
                    .fontWeight(.medium)
                
                Text(result.details)
                    .font(.caption2)
                    .foregroundColor(PremiumDesignSystem.Colors.tertiaryText)
            }
            
            Spacer()
            
            Text("\(Int(result.score))%")
                .font(.caption)
                .fontWeight(.medium)
                .foregroundColor(result.status.color)
        }
        .padding(.vertical, 4)
    }
}

struct ProductionReadyActions: View {
    var body: some View {
        VStack(spacing: 12) {
            HStack {
                Button("Generate Report") {
                    PremiumHaptics.contextualFeedback(for: .buttonTap)
                    // Report generation action
                }
                .premiumButtonStyle(variant: .outline)
                
                Button("Deploy to Production") {
                    PremiumHaptics.contextualFeedback(for: .saveAction)
                    // Production deployment action
                }
                .premiumButtonStyle(variant: .primary)
            }
            
            Text("🎉 Congratulations! Your application meets all production standards.")
                .font(.caption)
                .foregroundColor(.green)
                .multilineTextAlignment(.center)
        }
    }
}

struct ProductionIssuesActions: View {
    let criticalIssues: Int
    let failedTests: Int
    
    var body: some View {
        VStack(spacing: 12) {
            if criticalIssues > 0 {
                HStack {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .foregroundColor(.red)
                    
                    Text("\(criticalIssues) critical issue(s) must be resolved")
                        .font(.caption)
                        .fontWeight(.medium)
                        .foregroundColor(.red)
                    
                    Spacer()
                }
            }
            
            HStack {
                Button("View Issues") {
                    PremiumHaptics.contextualFeedback(for: .buttonTap)
                    // View issues action
                }
                .premiumButtonStyle(variant: .outline)
                
                Button("Re-run Validation") {
                    PremiumHaptics.contextualFeedback(for: .refreshData)
                    // Re-run validation action
                }
                .premiumButtonStyle(variant: .primary)
            }
        }
    }
}

// MARK: - Production Report View

struct ProductionReportView: View {
    let report: ProductionReadinessReport
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            ScrollView {
                LazyVStack(alignment: .leading, spacing: 20) {
                    // Report Header
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Production Readiness Report")
                            .font(PremiumDesignSystem.Typography.largeTitle)
                            .fontWeight(.bold)
                        
                        Text("Generated: \(report.timestamp.formatted())")
                            .font(PremiumDesignSystem.Typography.caption)
                            .foregroundColor(PremiumDesignSystem.Colors.secondaryText)
                    }
                    
                    // Summary
                    PremiumCard(style: .elevated) {
                        VStack(alignment: .leading, spacing: 16) {
                            Text("Executive Summary")
                                .font(PremiumDesignSystem.Typography.headline)
                            
                            Text(report.summary)
                                .font(PremiumDesignSystem.Typography.body)
                                .foregroundColor(PremiumDesignSystem.Colors.secondaryText)
                        }
                    }
                    
                    // Detailed Results
                    Text("Detailed Results")
                        .font(PremiumDesignSystem.Typography.title3)
                        .fontWeight(.semibold)
                    
                    ForEach(report.results) { result in
                        ProductionCheckRow(result: result)
                    }
                }
                .padding()
            }
            .navigationTitle("Production Report")
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