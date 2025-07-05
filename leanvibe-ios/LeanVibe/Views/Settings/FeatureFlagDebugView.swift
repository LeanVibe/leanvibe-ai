import SwiftUI

/// Debug interface for managing feature flags in development builds
/// Provides easy toggle mechanism for testing features and flag combinations
@available(iOS 18.0, macOS 14.0, *)
struct FeatureFlagDebugView: View {
    
    // MARK: - Properties
    @ObservedObject private var featureFlags = FeatureFlagManager.shared
    @State private var searchText = ""
    @State private var selectedCategory: FeatureCategory? = nil
    @State private var showingStatusSummary = false
    @State private var showingExportSheet = false
    @State private var exportedData = ""
    
    // MARK: - Body
    
    var body: some View {
        NavigationView {
            List {
                // Feature Status Summary
                statusSummarySection
                
                // Quick Actions
                quickActionsSection
                
                // Feature Categories
                categoriesSection
                
                // All Features List
                allFeaturesSection
            }
            .navigationTitle("Feature Flags")
            .navigationBarTitleDisplayMode(.inline)
            .searchable(text: $searchText, prompt: "Search features...")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    toolbarMenu
                }
            }
        }
        .sheet(isPresented: $showingStatusSummary) {
            FeatureFlagStatusSummaryView()
        }
        .sheet(isPresented: $showingExportSheet) {
            FeatureFlagExportView(data: exportedData)
        }
    }
    
    // MARK: - Status Summary Section
    
    private var statusSummarySection: some View {
        Section("Status Overview") {
            let summary = featureFlags.getFeatureStatusSummary()
            
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Text("Environment")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    Spacer()
                    Text(summary.environment.rawValue.capitalized)
                        .font(.caption)
                        .fontWeight(.medium)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 2)
                        .background(environmentColor(summary.environment))
                        .foregroundColor(.white)
                        .cornerRadius(4)
                }
                
                HStack {
                    Text("Enabled Features")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    Spacer()
                    Text("\(summary.enabledFeatures)/\(summary.totalFeatures)")
                        .font(.caption)
                        .fontWeight(.medium)
                }
                
                if summary.overriddenFeatures > 0 {
                    HStack {
                        Text("Debug Overrides")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        Spacer()
                        Text("\(summary.overriddenFeatures)")
                            .font(.caption)
                            .fontWeight(.medium)
                            .foregroundColor(.orange)
                    }
                }
                
                if summary.remoteControlledFeatures > 0 {
                    HStack {
                        Text("Remote Controlled")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        Spacer()
                        Text("\(summary.remoteControlledFeatures)")
                            .font(.caption)
                            .fontWeight(.medium)
                            .foregroundColor(.blue)
                    }
                }
            }
            .padding(.vertical, 4)
        }
    }
    
    // MARK: - Quick Actions Section
    
    private var quickActionsSection: some View {
        Section("Quick Actions") {
            Button(action: {
                showingStatusSummary = true
            }) {
                Label("View Detailed Status", systemImage: "chart.bar.doc.horizontal")
            }
            
            Button(action: {
                exportFeatureFlags()
            }) {
                Label("Export Configuration", systemImage: "square.and.arrow.up")
            }
            
            Button(action: {
                featureFlags.resetAllFeaturesToDefaults()
            }) {
                Label("Reset All to Defaults", systemImage: "arrow.counterclockwise")
                    .foregroundColor(.orange)
            }
        }
    }
    
    // MARK: - Categories Section
    
    private var categoriesSection: some View {
        Section("Feature Categories") {
            ForEach(FeatureCategory.allCases, id: \.self) { category in
                CategoryRowView(category: category, featureFlags: featureFlags)
            }
        }
    }
    
    // MARK: - All Features Section
    
    private var allFeaturesSection: some View {
        Section("All Features") {
            ForEach(filteredFeatures, id: \.id) { feature in
                FeatureRowView(feature: feature, featureFlags: featureFlags)
            }
        }
    }
    
    // MARK: - Computed Properties
    
    private var filteredFeatures: [FeatureFlag] {
        let features = FeatureFlag.allCases
        
        let categoryFiltered = if let selectedCategory = selectedCategory {
            features.filter { $0.category == selectedCategory }
        } else {
            features
        }
        
        if searchText.isEmpty {
            return categoryFiltered
        } else {
            return categoryFiltered.filter { feature in
                feature.displayName.localizedCaseInsensitiveContains(searchText) ||
                feature.description.localizedCaseInsensitiveContains(searchText) ||
                feature.rawValue.localizedCaseInsensitiveContains(searchText)
            }
        }
    }
    
    // MARK: - Toolbar Menu
    
    private var toolbarMenu: some View {
        Menu {
            Button(action: {
                selectedCategory = nil
            }) {
                Label("Show All Categories", systemImage: "list.bullet")
            }
            
            Divider()
            
            ForEach(FeatureCategory.allCases, id: \.self) { category in
                Button(action: {
                    selectedCategory = category
                }) {
                    Label(category.displayName, systemImage: "folder")
                }
            }
        } label: {
            Image(systemName: "ellipsis.circle")
        }
    }
    
    // MARK: - Helper Methods
    
    private func environmentColor(_ environment: Environment) -> Color {
        switch environment {
        case .debug:
            return .green
        case .testFlight:
            return .orange
        case .production:
            return .red
        }
    }
    
    private func exportFeatureFlags() {
        let summary = featureFlags.getFeatureStatusSummary()
        let enabledFeatures = featureFlags.getEnabledFeatures()
        
        let exportData = """
        Feature Flags Export
        Generated: \(Date())
        Environment: \(summary.environment.rawValue)
        
        Enabled Features (\(enabledFeatures.count)):
        \(enabledFeatures.map { "- \($0.displayName) (\($0.rawValue))" }.joined(separator: "\n"))
        
        All Features Status:
        \(FeatureFlag.allCases.map { feature in
            let isEnabled = featureFlags.isFeatureEnabled(feature)
            return "- \(feature.displayName): \(isEnabled ? "✅" : "❌")"
        }.joined(separator: "\n"))
        """
        
        exportedData = exportData
        showingExportSheet = true
    }
}

// MARK: - Category Row View

struct CategoryRowView: View {
    let category: FeatureCategory
    let featureFlags: FeatureFlagManager
    
    var body: some View {
        let categoryFeatures = FeatureFlag.allCases.filter { $0.category == category }
        let enabledCount = categoryFeatures.filter { featureFlags.isFeatureEnabled($0) }.count
        
        HStack {
            VStack(alignment: .leading) {
                Text(category.displayName)
                    .font(.body)
                    .fontWeight(.medium)
                
                Text("\(enabledCount)/\(categoryFeatures.count) enabled")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
            
            Button(action: {
                let allEnabled = categoryFeatures.allSatisfy { featureFlags.isFeatureEnabled($0) }
                featureFlags.enableFeaturesForCategory(category, enabled: !allEnabled)
            }) {
                let allEnabled = categoryFeatures.allSatisfy { featureFlags.isFeatureEnabled($0) }
                Image(systemName: allEnabled ? "checkmark.circle.fill" : "circle")
                    .foregroundColor(allEnabled ? .green : .gray)
            }
        }
        .padding(.vertical, 2)
    }
}

// MARK: - Feature Row View

struct FeatureRowView: View {
    let feature: FeatureFlag
    let featureFlags: FeatureFlagManager
    
    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                VStack(alignment: .leading, spacing: 2) {
                    HStack {
                        Text(feature.displayName)
                            .font(.body)
                            .fontWeight(.medium)
                        
                        if feature.isExperimental {
                            Text("EXPERIMENTAL")
                                .font(.caption2)
                                .fontWeight(.bold)
                                .padding(.horizontal, 4)
                                .padding(.vertical, 1)
                                .background(Color.orange)
                                .foregroundColor(.white)
                                .cornerRadius(3)
                        }
                        
                        if feature.isBetaOnly {
                            Text("BETA")
                                .font(.caption2)
                                .fontWeight(.bold)
                                .padding(.horizontal, 4)
                                .padding(.vertical, 1)
                                .background(Color.blue)
                                .foregroundColor(.white)
                                .cornerRadius(3)
                        }
                    }
                    
                    Text(feature.description)
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .lineLimit(2)
                }
                
                Spacer()
                
                VStack(alignment: .trailing, spacing: 4) {
                    Toggle("", isOn: Binding(
                        get: { featureFlags.isFeatureEnabled(feature) },
                        set: { enabled in
                            featureFlags.setOverrideFlag(feature, enabled: enabled)
                        }
                    ))
                    .toggleStyle(SwitchToggleStyle())
                    
                    if featureFlags.overrideFlags[feature] != nil {
                        Text("Override")
                            .font(.caption2)
                            .foregroundColor(.orange)
                    }
                }
            }
            
            // Show emergency disable info if applicable
            let emergencyInfo = featureFlags.getEmergencyDisableReason(feature)
            if let reason = emergencyInfo.reason {
                HStack {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .foregroundColor(.red)
                        .font(.caption)
                    
                    Text("Emergency Disabled: \(reason)")
                        .font(.caption)
                        .foregroundColor(.red)
                    
                    Spacer()
                    
                    if let date = emergencyInfo.date {
                        Text(date, style: .date)
                            .font(.caption2)
                            .foregroundColor(.secondary)
                    }
                }
                .padding(.top, 2)
            }
        }
        .padding(.vertical, 4)
    }
}

// MARK: - Status Summary View

struct FeatureFlagStatusSummaryView: View {
    @ObservedObject private var featureFlags = FeatureFlagManager.shared
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    let summary = featureFlags.getFeatureStatusSummary()
                    
                    // Environment Info
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Environment")
                            .font(.headline)
                        
                        HStack {
                            Text(summary.environment.rawValue.capitalized)
                                .font(.title2)
                                .fontWeight(.bold)
                            
                            Spacer()
                            
                            Text("Runtime")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                    }
                    .padding()
                    .background(
#if os(iOS)
Color(.systemGray6)
#else
Color.gray.opacity(0.1)
#endif)
                    .cornerRadius(8)
                    
                    // Feature Statistics
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Feature Statistics")
                            .font(.headline)
                        
                        StatRow(label: "Total Features", value: "\(summary.totalFeatures)")
                        StatRow(label: "Enabled", value: "\(summary.enabledFeatures)")
                        StatRow(label: "Disabled", value: "\(summary.disabledFeatures)")
                        StatRow(label: "Debug Overrides", value: "\(summary.overriddenFeatures)", color: .orange)
                        StatRow(label: "Remote Controlled", value: "\(summary.remoteControlledFeatures)", color: .blue)
                    }
                    .padding()
                    .background(
#if os(iOS)
Color(.systemGray6)
#else
Color.gray.opacity(0.1)
#endif)
                    .cornerRadius(8)
                    
                    // Category Breakdown
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Category Breakdown")
                            .font(.headline)
                        
                        ForEach(FeatureCategory.allCases, id: \.self) { category in
                            let categoryFeatures = FeatureFlag.allCases.filter { $0.category == category }
                            let enabledCount = categoryFeatures.filter { featureFlags.isFeatureEnabled($0) }.count
                            
                            StatRow(
                                label: category.displayName,
                                value: "\(enabledCount)/\(categoryFeatures.count)"
                            )
                        }
                    }
                    .padding()
                    .background(
#if os(iOS)
Color(.systemGray6)
#else
Color.gray.opacity(0.1)
#endif)
                    .cornerRadius(8)
                }
                .padding()
            }
            .navigationTitle("Feature Flag Status")
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

// MARK: - Stat Row View

struct StatRow: View {
    let label: String
    let value: String
    let color: Color
    
    init(label: String, value: String, color: Color = .primary) {
        self.label = label
        self.value = value
        self.color = color
    }
    
    var body: some View {
        HStack {
            Text(label)
                .font(.body)
            
            Spacer()
            
            Text(value)
                .font(.body)
                .fontWeight(.medium)
                .foregroundColor(color)
        }
    }
}

// MARK: - Export View

struct FeatureFlagExportView: View {
    let data: String
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            ScrollView {
                Text(data)
                    .font(.system(.body, design: .monospaced))
                    .padding()
                    .frame(maxWidth: .infinity, alignment: .leading)
            }
            .navigationTitle("Feature Flag Export")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Done") {
                        dismiss()
                    }
                }
                
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Copy") {
                        UIPasteboard.general.string = data
                    }
                }
            }
        }
    }
}

// MARK: - Preview

#Preview {
    FeatureFlagDebugView()
}