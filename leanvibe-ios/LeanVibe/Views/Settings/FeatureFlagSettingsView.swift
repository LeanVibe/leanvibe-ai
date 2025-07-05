import SwiftUI

/// User-facing feature flag settings view for production and TestFlight builds
/// Provides controlled access to stable feature toggles without overwhelming users
@available(iOS 18.0, macOS 14.0, *)
struct FeatureFlagSettingsView: View {
    
    // MARK: - Properties
    @ObservedObject private var featureFlags = FeatureFlagManager.shared
    @State private var showingAdvancedSettings = false
    @State private var showingBetaWarning = false
    @State private var pendingBetaFeature: FeatureFlag?
    
    // MARK: - Body
    
    var body: some View {
        List {
            // Core Features Section
            coreFeaturesSection
            
            // Beta Features Section (if any beta features are available)
            if !betaFeatures.isEmpty {
                betaFeaturesSection
            }
            
            // Advanced Features Section (non-production builds)
            if !AppConfiguration.shared.isProductionBuild {
                advancedFeaturesSection
            }
            
            // Debug Section (debug builds only)
            if AppConfiguration.shared.isDebugBuild {
                debugSection
            }
        }
        .navigationTitle("Feature Settings")
        .navigationBarTitleDisplayMode(.inline)
        .alert("Beta Feature Warning", isPresented: $showingBetaWarning) {
            Button("Enable") {
                if let feature = pendingBetaFeature {
                    featureFlags.setLocalFlag(feature, enabled: true)
                    pendingBetaFeature = nil
                }
            }
            
            Button("Cancel", role: .cancel) {
                pendingBetaFeature = nil
            }
        } message: {
            if let feature = pendingBetaFeature {
                Text("'\(feature.displayName)' is a beta feature that may be unstable or incomplete. Enable at your own risk.")
            }
        }
        .sheet(isPresented: $showingAdvancedSettings) {
            FeatureFlagDebugView()
        }
    }
    
    // MARK: - Core Features Section
    
    private var coreFeaturesSection: some View {
        Section(header: Text("Core Features"), 
                footer: Text("These features are stable and recommended for daily use.")) {
            
            // Architecture Visualization
            if coreFeatures.contains(.architectureVisualization) {
                FeatureToggleRow(
                    feature: .architectureVisualization,
                    featureFlags: featureFlags
                )
            }
            
            // Kanban Board
            if coreFeatures.contains(.kanbanBoard) {
                FeatureToggleRow(
                    feature: .kanbanBoard,
                    featureFlags: featureFlags
                )
            }
            
            // Push Notifications
            if coreFeatures.contains(.pushNotifications) {
                FeatureToggleRow(
                    feature: .pushNotifications,
                    featureFlags: featureFlags
                )
            }
            
            // Code Completion
            if coreFeatures.contains(.codeCompletion) {
                FeatureToggleRow(
                    feature: .codeCompletion,
                    featureFlags: featureFlags
                )
            }
            
            // QR Code Scanning
            if coreFeatures.contains(.qrCodeScanning) {
                FeatureToggleRow(
                    feature: .qrCodeScanning,
                    featureFlags: featureFlags
                )
            }
        }
    }
    
    // MARK: - Beta Features Section
    
    private var betaFeaturesSection: some View {
        Section(header: Text("Beta Features"), 
                footer: Text("These features are in beta testing and may have limited functionality.")) {
            
            ForEach(betaFeatures, id: \.id) { feature in
                BetaFeatureToggleRow(
                    feature: feature,
                    featureFlags: featureFlags,
                    onToggle: { feature, enabled in
                        if enabled && feature.isBetaOnly {
                            pendingBetaFeature = feature
                            showingBetaWarning = true
                        } else {
                            featureFlags.setLocalFlag(feature, enabled: enabled)
                        }
                    }
                )
            }
        }
    }
    
    // MARK: - Advanced Features Section
    
    private var advancedFeaturesSection: some View {
        Section(header: Text("Advanced Features"), 
                footer: Text("These features are for advanced users and may require additional configuration.")) {
            
            ForEach(advancedFeatures, id: \.id) { feature in
                AdvancedFeatureToggleRow(
                    feature: feature,
                    featureFlags: featureFlags
                )
            }
        }
    }
    
    // MARK: - Debug Section
    
    private var debugSection: some View {
        Section(header: Text("Debug & Development"), 
                footer: Text("These options are only available in debug builds.")) {
            
            Button(action: {
                showingAdvancedSettings = true
            }) {
                Label("Advanced Feature Flags", systemImage: "gearshape.2")
            }
            
            Button(action: {
                featureFlags.resetAllFeaturesToDefaults()
            }) {
                Label("Reset All Features", systemImage: "arrow.counterclockwise")
                    .foregroundColor(.orange)
            }
        }
    }
    
    // MARK: - Computed Properties
    
    private var coreFeatures: [FeatureFlag] {
        return [
            .architectureVisualization,
            .kanbanBoard,
            .pushNotifications,
            .codeCompletion,
            .qrCodeScanning,
            .websocketConnection,
            .backendConfiguration,
            .onboardingSystem
        ]
    }
    
    private var betaFeatures: [FeatureFlag] {
        return FeatureFlag.allCases.filter { feature in
            feature.isBetaOnly && 
            !feature.category.isInternalOnly &&
            featureFlags.getDefaultValue(for: feature) // Only show if default is enabled for current environment
        }
    }
    
    private var advancedFeatures: [FeatureFlag] {
        return [
            .advancedArchitectureFeatures,
            .advancedKanbanFeatures,
            .performanceMonitoring,
            .networkDiagnostics,
            .documentIntelligence,
            .featureDiscovery
        ]
    }
}

// MARK: - Feature Toggle Row Views

struct FeatureToggleRow: View {
    let feature: FeatureFlag
    let featureFlags: FeatureFlagManager
    
    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text(feature.displayName)
                    .font(.body)
                
                Text(feature.description)
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .lineLimit(2)
            }
            
            Spacer()
            
            Toggle("", isOn: Binding(
                get: { featureFlags.isFeatureEnabled(feature) },
                set: { enabled in
                    featureFlags.setLocalFlag(feature, enabled: enabled)
                }
            ))
            .toggleStyle(SwitchToggleStyle())
        }
        .padding(.vertical, 2)
    }
}

struct BetaFeatureToggleRow: View {
    let feature: FeatureFlag
    let featureFlags: FeatureFlagManager
    let onToggle: (FeatureFlag, Bool) -> Void
    
    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                HStack {
                    Text(feature.displayName)
                        .font(.body)
                    
                    Text("BETA")
                        .font(.caption2)
                        .fontWeight(.bold)
                        .padding(.horizontal, 4)
                        .padding(.vertical, 1)
                        .background(Color.blue)
                        .foregroundColor(.white)
                        .cornerRadius(3)
                }
                
                Text(feature.description)
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .lineLimit(2)
            }
            
            Spacer()
            
            Toggle("", isOn: Binding(
                get: { featureFlags.isFeatureEnabled(feature) },
                set: { enabled in
                    onToggle(feature, enabled)
                }
            ))
            .toggleStyle(SwitchToggleStyle())
        }
        .padding(.vertical, 2)
    }
}

struct AdvancedFeatureToggleRow: View {
    let feature: FeatureFlag
    let featureFlags: FeatureFlagManager
    
    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                HStack {
                    Text(feature.displayName)
                        .font(.body)
                    
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
                }
                
                Text(feature.description)
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .lineLimit(2)
            }
            
            Spacer()
            
            Toggle("", isOn: Binding(
                get: { featureFlags.isFeatureEnabled(feature) },
                set: { enabled in
                    featureFlags.setLocalFlag(feature, enabled: enabled)
                }
            ))
            .toggleStyle(SwitchToggleStyle())
        }
        .padding(.vertical, 2)
    }
}

// MARK: - Extensions

extension FeatureFlagManager {
    fileprivate func getDefaultValue(for feature: FeatureFlag) -> Bool {
        return getDefaultValue(for: feature) // This would need to be made internal in the actual implementation
    }
}

extension FeatureCategory {
    fileprivate var isInternalOnly: Bool {
        switch self {
        case .production, .beta:
            return true
        default:
            return false
        }
    }
}

extension AppConfiguration {
    fileprivate var isProductionBuild: Bool {
        return !isDebugBuild && !isTestFlightBuild
    }
}

// MARK: - Preview

#Preview {
    NavigationView {
        FeatureFlagSettingsView()
    }
}