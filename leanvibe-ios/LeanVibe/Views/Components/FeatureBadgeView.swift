import SwiftUI

/// Visual indicators for beta, experimental, and feature-flagged content
/// Provides clear labeling and warnings for incomplete or testing features
@available(iOS 18.0, macOS 14.0, *)
struct FeatureBadgeView: View {
    let feature: FeatureFlag
    let style: BadgeStyle
    
    enum BadgeStyle {
        case compact
        case full
        case banner
    }
    
    var body: some View {
        Group {
            switch style {
            case .compact:
                compactBadge
            case .full:
                fullBadge
            case .banner:
                bannerBadge
            }
        }
    }
    
    // MARK: - Compact Badge
    
    private var compactBadge: some View {
        HStack(spacing: 2) {
            if feature.isBetaOnly {
                Text("BETA")
                    .font(PremiumDesignSystem.Components.Badge.font)
                    .padding(.horizontal, PremiumDesignSystem.Components.Badge.horizontalPadding)
                    .padding(.vertical, PremiumDesignSystem.Components.Badge.verticalPadding)
                    .background(PremiumDesignSystem.Colors.betaBadge)
                    .foregroundColor(.white)
                    .cornerRadius(PremiumDesignSystem.Components.Badge.cornerRadius)
            }
            
            if feature.isExperimental {
                Text("EXP")
                    .font(PremiumDesignSystem.Components.Badge.font)
                    .padding(.horizontal, PremiumDesignSystem.Components.Badge.horizontalPadding)
                    .padding(.vertical, PremiumDesignSystem.Components.Badge.verticalPadding)
                    .background(PremiumDesignSystem.Colors.experimentalBadge)
                    .foregroundColor(.white)
                    .cornerRadius(PremiumDesignSystem.Components.Badge.cornerRadius)
            }
            
            if isDebugOverridden {
                Text("DEV")
                    .font(PremiumDesignSystem.Components.Badge.font)
                    .padding(.horizontal, PremiumDesignSystem.Components.Badge.horizontalPadding)
                    .padding(.vertical, PremiumDesignSystem.Components.Badge.verticalPadding)
                    .background(PremiumDesignSystem.Colors.debugBadge)
                    .foregroundColor(.white)
                    .cornerRadius(PremiumDesignSystem.Components.Badge.cornerRadius)
            }
        }
    }
    
    // MARK: - Full Badge
    
    private var fullBadge: some View {
        VStack(spacing: PremiumDesignSystem.Spacing.xs) {
            HStack {
                Image(systemName: badgeIcon)
                    .font(.caption)
                    .foregroundColor(badgeColor)
                
                Text(badgeTitle)
                    .font(.caption)
                    .fontWeight(.medium)
                    .foregroundColor(badgeColor)
                
                Spacer()
            }
            
            if let subtitle = badgeSubtitle {
                HStack {
                    Text(subtitle)
                        .font(.caption2)
                        .foregroundColor(.secondary)
                        .lineLimit(2)
                    Spacer()
                }
            }
        }
        .padding(.horizontal, PremiumDesignSystem.Spacing.sm)
        .padding(.vertical, PremiumDesignSystem.Spacing.xs)
        .background(badgeColor.opacity(0.1))
        .overlay(
            RoundedRectangle(cornerRadius: PremiumDesignSystem.CornerRadius.sm)
                .stroke(badgeColor.opacity(0.3), lineWidth: 1)
        )
        .cornerRadius(PremiumDesignSystem.CornerRadius.sm)
    }
    
    // MARK: - Banner Badge
    
    private var bannerBadge: some View {
        HStack {
            Image(systemName: badgeIcon)
                .font(.body)
                .foregroundColor(badgeColor)
            
            VStack(alignment: .leading, spacing: PremiumDesignSystem.Spacing.xs) {
                Text(bannerTitle)
                    .font(.body)
                    .fontWeight(.medium)
                    .foregroundColor(badgeColor)
                
                if let description = bannerDescription {
                    Text(description)
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .lineLimit(3)
                }
            }
            
            Spacer()
        }
        .padding(PremiumDesignSystem.Spacing.containerPadding)
        .background(badgeColor.opacity(0.1))
        .overlay(
            Rectangle()
                .frame(height: 1)
                .foregroundColor(badgeColor.opacity(0.3)),
            alignment: .bottom
        )
    }
    
    // MARK: - Computed Properties
    
    private var badgeIcon: String {
        if feature.isBetaOnly {
            return PremiumDesignSystem.Icons.beta
        } else if feature.isExperimental {
            return PremiumDesignSystem.Icons.experimental
        } else if isDebugOverridden {
            return PremiumDesignSystem.Icons.debug
        } else {
            return PremiumDesignSystem.Icons.feature
        }
    }
    
    private var badgeColor: Color {
        if feature.isBetaOnly {
            return PremiumDesignSystem.Colors.betaBadge
        } else if feature.isExperimental {
            return PremiumDesignSystem.Colors.experimentalBadge
        } else if isDebugOverridden {
            return PremiumDesignSystem.Colors.debugBadge
        } else {
            return PremiumDesignSystem.Colors.iconSecondary
        }
    }
    
    private var badgeTitle: String {
        if feature.isBetaOnly {
            return "Beta Feature"
        } else if feature.isExperimental {
            return "Experimental"
        } else if isDebugOverridden {
            return "Debug Override"
        } else {
            return "Feature Flag"
        }
    }
    
    private var badgeSubtitle: String? {
        if feature.isBetaOnly {
            return "May be unstable"
        } else if feature.isExperimental {
            return "Under development"
        } else if isDebugOverridden {
            return "Development mode"
        } else {
            return nil
        }
    }
    
    private var bannerTitle: String {
        if feature.isBetaOnly {
            return "Beta Feature: \(feature.displayName)"
        } else if feature.isExperimental {
            return "Experimental: \(feature.displayName)"
        } else if isDebugOverridden {
            return "Debug Override: \(feature.displayName)"
        } else {
            return feature.displayName
        }
    }
    
    private var bannerDescription: String? {
        if feature.isBetaOnly {
            return "This feature is in beta testing and may have limited functionality or stability issues."
        } else if feature.isExperimental {
            return "This is an experimental feature under active development. Use with caution."
        } else if isDebugOverridden {
            return "This feature has been enabled for development testing only."
        } else {
            return feature.description
        }
    }
    
    private var isDebugOverridden: Bool {
        return FeatureFlagManager.shared.overrideFlags[feature] != nil
    }
}

/// A view modifier that adds feature badges to any view
@available(iOS 18.0, macOS 14.0, *)
struct FeatureBadgeModifier: ViewModifier {
    let feature: FeatureFlag
    let style: FeatureBadgeView.BadgeStyle
    let position: BadgePosition
    
    enum BadgePosition {
        case topLeading
        case topTrailing
        case bottom
        case overlay
    }
    
    func body(content: Content) -> some View {
        ZStack {
            content
            
            switch position {
            case .topLeading:
                VStack {
                    HStack {
                        FeatureBadgeView(feature: feature, style: style)
                        Spacer()
                    }
                    Spacer()
                }
                .padding(.top, PremiumDesignSystem.Spacing.sm)
                .padding(.leading, PremiumDesignSystem.Spacing.sm)
                
            case .topTrailing:
                VStack {
                    HStack {
                        Spacer()
                        FeatureBadgeView(feature: feature, style: style)
                    }
                    Spacer()
                }
                .padding(.top, PremiumDesignSystem.Spacing.sm)
                .padding(.trailing, PremiumDesignSystem.Spacing.sm)
                
            case .bottom:
                VStack {
                    Spacer()
                    FeatureBadgeView(feature: feature, style: style)
                }
                .padding(.bottom, PremiumDesignSystem.Spacing.sm)
                
            case .overlay:
                FeatureBadgeView(feature: feature, style: style)
            }
        }
    }
}

@available(iOS 18.0, macOS 14.0, *)
extension View {
    /// Add a feature badge to any view
    func featureBadge(
        _ feature: FeatureFlag,
        style: FeatureBadgeView.BadgeStyle = .compact,
        position: FeatureBadgeModifier.BadgePosition = .topTrailing
    ) -> some View {
        self.modifier(FeatureBadgeModifier(feature: feature, style: style, position: position))
    }
}

/// A wrapper view that automatically shows badges for beta/experimental features
@available(iOS 18.0, macOS 14.0, *)
struct FeatureLabeledView<Content: View>: View {
    let feature: FeatureFlag
    let showBadge: Bool
    let content: () -> Content
    
    init(feature: FeatureFlag, showBadge: Bool = true, @ViewBuilder content: @escaping () -> Content) {
        self.feature = feature
        self.showBadge = showBadge
        self.content = content
    }
    
    var body: some View {
        VStack(spacing: 0) {
            // Show banner if feature needs special attention
            if showBadge && shouldShowBanner {
                FeatureBadgeView(feature: feature, style: .banner)
            }
            
            // Main content
            content()
                .featureBadge(feature, style: .compact, position: .topTrailing)
        }
    }
    
    private var shouldShowBanner: Bool {
        return feature.isBetaOnly || feature.isExperimental || 
               FeatureFlagManager.shared.overrideFlags[feature] != nil
    }
}

// MARK: - Preview

#Preview("Compact Badges") {
    VStack(spacing: 16) {
        HStack {
            Text("Beta Feature")
            FeatureBadgeView(feature: .betaAnalytics, style: .compact)
        }
        
        HStack {
            Text("Experimental Feature")
            FeatureBadgeView(feature: .experimentalUI, style: .compact)
        }
        
        HStack {
            Text("Normal Feature")
            FeatureBadgeView(feature: .kanbanBoard, style: .compact)
        }
    }
    .padding(PremiumDesignSystem.Spacing.containerPadding)
}

#Preview("Full Badges") {
    VStack(spacing: 16) {
        FeatureBadgeView(feature: .betaAnalytics, style: .full)
        FeatureBadgeView(feature: .experimentalUI, style: .full)
        FeatureBadgeView(feature: .kanbanBoard, style: .full)
    }
    .padding(PremiumDesignSystem.Spacing.containerPadding)
}

#Preview("Banner Badges") {
    VStack(spacing: 0) {
        FeatureBadgeView(feature: .betaAnalytics, style: .banner)
        FeatureBadgeView(feature: .experimentalUI, style: .banner)
    }
}

#Preview("Feature Labeled View") {
    FeatureLabeledView(feature: .betaAnalytics) {
        VStack {
            Text("Beta Analytics Dashboard")
                .font(.title)
            Text("This is a beta feature with limited functionality")
                .foregroundColor(.secondary)
        }
        .padding(PremiumDesignSystem.Spacing.containerPadding)
        .background(Color(.systemGroupedBackground))
    }
}