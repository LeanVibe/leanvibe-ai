import SwiftUI

/// A graceful degradation view shown when features are disabled
/// Provides clear messaging and alternatives to users
@available(iOS 18.0, macOS 14.0, *)
struct FeatureDisabledView: View {
    let feature: FeatureFlag
    let alternativeAction: (() -> Void)?
    let alternativeTitle: String?
    
    init(feature: FeatureFlag, alternativeAction: (() -> Void)? = nil, alternativeTitle: String? = nil) {
        self.feature = feature
        self.alternativeAction = alternativeAction
        self.alternativeTitle = alternativeTitle
    }
    
    var body: some View {
        VStack(spacing: 20) {
            // Feature icon
            Image(systemName: iconName(for: feature))
                .font(.system(size: 48))
                .foregroundColor(.secondary)
            
            // Title
            Text("\(feature.displayName) Unavailable")
                .font(.title2)
                .fontWeight(.semibold)
                .multilineTextAlignment(.center)
            
            // Explanation
            VStack(spacing: 12) {
                Text("This feature is currently disabled.")
                    .font(.body)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
                
                if let reason = disabledReason(for: feature) {
                    Text(reason)
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .multilineTextAlignment(.center)
                        .padding(.horizontal)
                }
            }
            
            // Alternative action button
            if let alternativeAction = alternativeAction,
               let alternativeTitle = alternativeTitle {
                Button(action: alternativeAction) {
                    Text(alternativeTitle)
                        .font(.body)
                        .fontWeight(.medium)
                        .foregroundColor(.white)
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(Color.blue)
                        .cornerRadius(10)
                }
                .padding(.horizontal)
            }
            
            // Enable feature button (debug builds only)
            if AppConfiguration.shared.isDebugBuild {
                Button(action: {
                    FeatureFlagManager.shared.setOverrideFlag(feature, enabled: true)
                }) {
                    Text("Enable for Testing")
                        .font(.caption)
                        .foregroundColor(.orange)
                }
            }
        }
        .padding()
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color(.systemGroupedBackground))
    }
    
    private func iconName(for feature: FeatureFlag) -> String {
        switch feature.category {
        case .voice:
            return "mic.slash"
        case .beta:
            return "flask"
        case .performance:
            return "chart.line.downtrend.xyaxis"
        case .architecture:
            return "square.stack.3d.up.slash"
        case .kanban:
            return "list.bullet.rectangle"
        case .settings:
            return "gearshape"
        case .notifications:
            return "bell.slash"
        case .onboarding:
            return "person.crop.circle.badge.questionmark"
        case .production:
            return "hammer"
        case .connection:
            return "wifi.slash"
        case .codeCompletion:
            return "chevron.left.forwardslash.chevron.right"
        }
    }
    
    private func disabledReason(for feature: FeatureFlag) -> String? {
        // Check for emergency disable reason
        let emergencyInfo = FeatureFlagManager.shared.getEmergencyDisableReason(feature)
        if let reason = emergencyInfo.reason {
            return "Temporarily disabled: \(reason)"
        }
        
        // Provide category-specific reasons
        switch feature.category {
        case .voice:
            return "Voice features are currently disabled for stability improvements."
        case .beta:
            return "Beta features are only available to testers and may be unstable."
        case .performance:
            return "Performance features are disabled to reduce resource usage."
        case .architecture:
            return "Architecture features require additional backend configuration."
        case .kanban:
            return "Task management features are being improved."
        case .settings:
            return "Advanced settings are not available in this build."
        case .notifications:
            return "Notification features require user permission."
        case .onboarding:
            return "Onboarding features are not needed for experienced users."
        case .production:
            return "Production tools are only available in development builds."
        case .connection:
            return "Connection features require network access."
        case .codeCompletion:
            return "Code completion features are currently being updated."
        }
    }
}

/// A wrapper view that automatically shows FeatureDisabledView when feature is disabled
@available(iOS 18.0, macOS 14.0, *)
struct FeatureGatedView<Content: View>: View {
    let feature: FeatureFlag
    let content: () -> Content
    let alternativeAction: (() -> Void)?
    let alternativeTitle: String?
    
    @ObservedObject private var featureFlags = FeatureFlagManager.shared
    
    init(
        feature: FeatureFlag,
        alternativeAction: (() -> Void)? = nil,
        alternativeTitle: String? = nil,
        @ViewBuilder content: @escaping () -> Content
    ) {
        self.feature = feature
        self.content = content
        self.alternativeAction = alternativeAction
        self.alternativeTitle = alternativeTitle
    }
    
    var body: some View {
        if featureFlags.isFeatureEnabled(feature) {
            content()
        } else {
            FeatureDisabledView(
                feature: feature,
                alternativeAction: alternativeAction,
                alternativeTitle: alternativeTitle
            )
        }
    }
}

/// Extension to AppConfiguration for easy access to environment checks
extension AppConfiguration {
    var isDebugBuild: Bool {
        #if DEBUG
        return true
        #else
        return false
        #endif
    }
}

// MARK: - Preview

#Preview("Voice Feature Disabled") {
    FeatureDisabledView(
        feature: .voiceFeatures,
        alternativeAction: { print("Alternative action") },
        alternativeTitle: "Use Text Input Instead"
    )
}

#Preview("Beta Feature Disabled") {
    FeatureDisabledView(feature: .betaAnalytics)
}

#Preview("Feature Gated View") {
    FeatureGatedView(
        feature: .voiceFeatures,
        alternativeAction: { print("Use keyboard") },
        alternativeTitle: "Use Keyboard Input"
    ) {
        VStack {
            Text("Voice Feature Content")
                .font(.title)
            Text("This content is only shown when voice features are enabled")
                .foregroundColor(.secondary)
        }
        .padding()
    }
}