import SwiftUI
#if canImport(UIKit)
import UIKit
#endif

// MARK: - Premium Design System

@available(iOS 15.0, macOS 12.0, *)
struct PremiumDesignSystem {
    // MARK: - Material Design
    static let glassMaterial = Material.ultraThinMaterial
    static let thickGlassMaterial = Material.thickMaterial
    static let cardShadow = Color.black.opacity(0.1)
    static let elevatedShadow = Color.black.opacity(0.2)
    
    // MARK: - Shadow Definitions
    struct Shadow {
        let color: Color
        let radius: CGFloat
        let x: CGFloat
        let y: CGFloat
    }
    
    struct Shadows {
        static let card = Shadow(color: Color.black.opacity(0.1), radius: 8, x: 0, y: 4)
        static let elevated = Shadow(color: Color.black.opacity(0.2), radius: 12, x: 0, y: 8)
        static let floating = Shadow(color: Color.black.opacity(0.25), radius: 20, x: 0, y: 12)
        static let subtle = Shadow(color: Color.black.opacity(0.05), radius: 4, x: 0, y: 2)
    }
    
    // MARK: - Spacing & Layout
    static let cornerRadius: CGFloat = 16
    static let smallCornerRadius: CGFloat = 8
    static let largeCornerRadius: CGFloat = 24
    static let cardPadding: CGFloat = 16
    static let sectionSpacing: CGFloat = 24
    static let itemSpacing: CGFloat = 12
    
    // MARK: - Animation
    static let animationDuration: Double = 0.3
    static let springDuration: Double = 0.6
    static let microInteractionDuration: Double = 0.15
    
    // MARK: - Premium Color Palette
    struct Colors {
        // Primary Colors - Theme Aware
        static let primary = Color.accentColor
        static let primaryLight = Color.accentColor.opacity(0.7)
        static let primaryDark = Color.accentColor.opacity(0.9)
        
        // Secondary Colors - Theme Aware
        static let secondary = Color(.systemBlue)
        static let accent = Color(.systemTeal)
        
        // Status Colors - Theme Aware
        static let success = Color(.systemGreen)
        static let warning = Color(.systemOrange)
        static let error = Color(.systemRed)
        static let info = Color(.systemBlue)
        
        // Neutral Colors
        #if canImport(UIKit)
        static let background = Color(UIColor.systemBackground)
        static let secondaryBackground = Color(UIColor.secondarySystemBackground)
        static let tertiaryBackground = Color(UIColor.tertiarySystemBackground)
        
        // Text Colors
        static let primaryText = Color(UIColor.label)
        static let secondaryText = Color(UIColor.secondaryLabel)
        static let tertiaryText = Color(UIColor.tertiaryLabel)
        #else
        static let background = Color.white
        static let secondaryBackground = Color.gray.opacity(0.1)
        static let tertiaryBackground = Color.gray.opacity(0.05)
        
        // Text Colors
        static let primaryText = Color.primary
        static let secondaryText = Color.secondary
        static let tertiaryText = Color.secondary.opacity(0.7)
        #endif
        
        // Glassmorphism Colors - Theme Aware
        #if canImport(UIKit)
        static let glassBackground = Color(UIColor.systemBackground).opacity(0.1)
        static let glassStroke = Color(UIColor.separator).opacity(0.3)
        #else
        static let glassBackground = Color.primary.opacity(0.1)
        static let glassStroke = Color.primary.opacity(0.2)
        #endif
    }
    
    // MARK: - Enhanced Typography
    struct Typography {
        static let largeTitle = Font.largeTitle.weight(.bold)
        static let title = Font.title.weight(.semibold)
        static let title2 = Font.title2.weight(.semibold)
        static let title3 = Font.title3.weight(.medium)
        static let headline = Font.headline.weight(.medium)
        static let subheadline = Font.subheadline.weight(.medium)
        static let body = Font.body
        static let bodyEmphasized = Font.body.weight(.medium)
        static let callout = Font.callout
        static let caption = Font.caption.weight(.medium)
        static let caption2 = Font.caption2
        
        // Custom Typography
        static let heroTitle = Font.system(size: 34, weight: .bold, design: .default)
        static let cardTitle = Font.system(size: 18, weight: .semibold, design: .default)
        static let buttonTitle = Font.system(size: 16, weight: .semibold, design: .default)
    }
    
}

// MARK: - Premium Card Component

@available(iOS 18.0, macOS 14.0, *)
struct PremiumCard<Content: View>: View {
    let content: Content
    let style: CardStyle
    
    @State private var isPressed = false
    @State private var isHovered = false
    
    enum CardStyle {
        case standard
        case elevated
        case glass
        case floating
        
        var shadow: PremiumDesignSystem.Shadow {
            switch self {
            case .standard:
                return PremiumDesignSystem.Shadows.card
            case .elevated:
                return PremiumDesignSystem.Shadows.elevated
            case .glass:
                return PremiumDesignSystem.Shadows.card
            case .floating:
                return PremiumDesignSystem.Shadows.floating
            }
        }
        
        @ViewBuilder
        var background: some View {
            switch self {
            case .standard, .elevated:
                PremiumDesignSystem.Colors.background
            case .glass:
                Rectangle()
                    .fill(PremiumDesignSystem.Colors.glassBackground)
                    .background(PremiumDesignSystem.glassMaterial)
            case .floating:
                Rectangle()
                    .fill(PremiumDesignSystem.Colors.glassBackground)
                    .background(PremiumDesignSystem.thickGlassMaterial)
            }
        }
    }
    
    init(style: CardStyle = .standard, @ViewBuilder content: () -> Content) {
        self.style = style
        self.content = content()
    }
    
    var body: some View {
        content
            .padding(PremiumDesignSystem.cardPadding)
            .background(style.background)
            .cornerRadius(PremiumDesignSystem.cornerRadius)
            .shadow(
                color: isPressed ? style.shadow.color.opacity(0.5) : style.shadow.color,
                radius: isPressed ? style.shadow.radius * 0.5 : style.shadow.radius,
                x: style.shadow.x,
                y: isPressed ? style.shadow.y * 0.5 : style.shadow.y
            )
            .scaleEffect(isPressed ? 0.98 : (isHovered ? 1.02 : 1.0))
            .animation(.easeInOut(duration: PremiumDesignSystem.microInteractionDuration), value: isPressed)
            .animation(.easeInOut(duration: PremiumDesignSystem.microInteractionDuration), value: isHovered)
            .gesture(
                DragGesture(minimumDistance: 0)
                    .onChanged { _ in
                        if !isPressed {
                            withAnimation {
                                isPressed = true
                            }
                            PremiumHaptics.lightImpact()
                        }
                    }
                    .onEnded { _ in
                        withAnimation {
                            isPressed = false
                        }
                    }
            )
            .onHover { hovering in
                withAnimation {
                    isHovered = hovering
                }
            }
    }
}

// MARK: - Premium Button Styles

@available(iOS 18.0, macOS 14.0, *)
struct PremiumButtonStyle: ButtonStyle {
    let variant: ButtonVariant
    
    enum ButtonVariant {
        case primary
        case secondary
        case outline
        case ghost
        case destructive
        
        var backgroundColor: Color {
            switch self {
            case .primary:
                return PremiumDesignSystem.Colors.primary
            case .secondary:
                return PremiumDesignSystem.Colors.secondary
            case .outline, .ghost:
                return Color.clear
            case .destructive:
                return PremiumDesignSystem.Colors.error
            }
        }
        
        var foregroundColor: Color {
            switch self {
            case .primary, .secondary, .destructive:
                return .white
            case .outline:
                return PremiumDesignSystem.Colors.primary
            case .ghost:
                return PremiumDesignSystem.Colors.primaryText
            }
        }
        
        var borderColor: Color? {
            switch self {
            case .outline:
                return PremiumDesignSystem.Colors.primary
            default:
                return nil
            }
        }
    }
    
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(PremiumDesignSystem.Typography.buttonTitle)
            .foregroundColor(variant.foregroundColor)
            .padding(.horizontal, 24)
            .padding(.vertical, 12)
            .background(
                RoundedRectangle(cornerRadius: PremiumDesignSystem.cornerRadius)
                    .fill(variant.backgroundColor)
            )
            .overlay(
                RoundedRectangle(cornerRadius: PremiumDesignSystem.cornerRadius)
                    .stroke(variant.borderColor ?? Color.clear, lineWidth: variant.borderColor != nil ? 2 : 0)
            )
            .scaleEffect(configuration.isPressed ? 0.95 : 1.0)
            .opacity(configuration.isPressed ? 0.8 : 1.0)
            .animation(.easeInOut(duration: PremiumDesignSystem.microInteractionDuration), value: configuration.isPressed)
            .onChange(of: configuration.isPressed) { _, pressed in
                if pressed {
                    PremiumHaptics.lightImpact()
                }
            }
    }
}

// MARK: - Sophisticated Haptic Feedback System

@MainActor
class PremiumHaptics {
    #if canImport(UIKit) && !os(macOS)
    private static let lightImpactGenerator = UIImpactFeedbackGenerator(style: .light)
    private static let mediumImpactGenerator = UIImpactFeedbackGenerator(style: .medium)
    private static let heavyImpactGenerator = UIImpactFeedbackGenerator(style: .heavy)
    private static let notificationGenerator = UINotificationFeedbackGenerator()
    private static let selectionGenerator = UISelectionFeedbackGenerator()
    #endif
    
    static func prepareGenerators() {
        #if canImport(UIKit) && !os(macOS)
        lightImpactGenerator.prepare()
        mediumImpactGenerator.prepare()
        heavyImpactGenerator.prepare()
        notificationGenerator.prepare()
        selectionGenerator.prepare()
        #endif
    }
    
    // MARK: - Basic Haptics
    
    static func lightImpact() {
        lightImpactGenerator.prepare()
        lightImpactGenerator.impactOccurred()
    }
    
    static func mediumImpact() {
        mediumImpactGenerator.prepare()
        mediumImpactGenerator.impactOccurred()
    }
    
    static func heavyImpact() {
        heavyImpactGenerator.prepare()
        heavyImpactGenerator.impactOccurred()
    }
    
    static func selection() {
        selectionGenerator.prepare()
        selectionGenerator.selectionChanged()
    }
    
    // MARK: - Notification Haptics
    
    static func successNotification() {
        notificationGenerator.prepare()
        notificationGenerator.notificationOccurred(.success)
    }
    
    static func errorNotification() {
        notificationGenerator.prepare()
        notificationGenerator.notificationOccurred(.error)
    }
    
    static func warningNotification() {
        notificationGenerator.prepare()
        notificationGenerator.notificationOccurred(.warning)
    }
    
    // MARK: - Custom Haptic Patterns
    
    static func voiceActivation() {
        mediumImpact()
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
            lightImpact()
        }
    }
    
    static func taskCompleted() {
        successNotification()
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
            lightImpact()
        }
    }
    
    static func cardFlip() {
        lightImpact()
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.05) {
            lightImpact()
        }
    }
    
    static func tabSwitch() {
        selection()
    }
    
    static func pullToRefresh() {
        lightImpact()
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
            mediumImpact()
        }
    }
    
    static func dragAndDrop() {
        heavyImpact()
    }
    
    static func navigationPop() {
        lightImpact()
    }
    
    static func modalPresent() {
        mediumImpact()
    }
    
    static func modalDismiss() {
        lightImpact()
    }
    
    // MARK: - Context-Aware Haptics
    
    static func contextualFeedback(for action: HapticAction) {
        switch action {
        case .buttonTap:
            lightImpact()
        case .toggleSwitch:
            mediumImpact()
        case .deleteAction:
            errorNotification()
        case .saveAction:
            successNotification()
        case .voiceCommand:
            voiceActivation()
        case .taskCompletion:
            taskCompleted()
        case .errorOccurred:
            errorNotification()
        case .refreshData:
            pullToRefresh()
        case .navigation:
            selection()
        }
    }
    
    enum HapticAction {
        case buttonTap
        case toggleSwitch
        case deleteAction
        case saveAction
        case voiceCommand
        case taskCompletion
        case errorOccurred
        case refreshData
        case navigation
    }
}

// MARK: - Premium Transitions

@available(iOS 18.0, macOS 14.0, *)
struct PremiumTransitions {
    static let spring = Animation.spring(
        response: 0.6,
        dampingFraction: 0.8,
        blendDuration: 0.2
    )
    
    static let easeInOut = Animation.easeInOut(duration: PremiumDesignSystem.animationDuration)
    static let easeOut = Animation.easeOut(duration: 0.25)
    static let microInteraction = Animation.easeInOut(duration: PremiumDesignSystem.microInteractionDuration)
    
    // MARK: - Page Transitions
    @MainActor
    static let pageTransition = AnyTransition.asymmetric(
        insertion: .move(edge: .trailing).combined(with: .opacity),
        removal: .move(edge: .leading).combined(with: .opacity)
    )
    
    // MARK: - Modal Transitions
    @MainActor
    static let modalTransition = AnyTransition.asymmetric(
        insertion: .move(edge: .bottom).combined(with: .opacity),
        removal: .move(edge: .bottom).combined(with: .opacity)
    )
    
    // MARK: - Card Transitions
    @MainActor
    static let cardTransition = AnyTransition.asymmetric(
        insertion: .scale(scale: 0.8).combined(with: .opacity),
        removal: .scale(scale: 1.1).combined(with: .opacity)
    )
    
    // MARK: - Slide Transitions
    nonisolated(unsafe) static let slideFromRight = AnyTransition.move(edge: .trailing)
    nonisolated(unsafe) static let slideFromLeft = AnyTransition.move(edge: .leading)
    nonisolated(unsafe) static let slideFromTop = AnyTransition.move(edge: .top)
    nonisolated(unsafe) static let slideFromBottom = AnyTransition.move(edge: .bottom)
    
    // MARK: - Custom Transitions
    nonisolated(unsafe) static let fadeScale = AnyTransition.scale.combined(with: .opacity)
    nonisolated(unsafe) static let flipHorizontal = AnyTransition.asymmetric(
        insertion: .scale(scale: 0.01).combined(with: .opacity),
        removal: .scale(scale: 0.01).combined(with: .opacity)
    )
}

// MARK: - View Extensions for Premium Design

@available(iOS 18.0, macOS 14.0, *)
extension View {
    func premiumCard(style: PremiumCard<AnyView>.CardStyle = .standard) -> some View {
        PremiumCard(style: style) {
            AnyView(self)
        }
    }
    
    func premiumButtonStyle(variant: PremiumButtonStyle.ButtonVariant = .primary) -> some View {
        self.buttonStyle(PremiumButtonStyle(variant: variant))
    }
    
    func hapticFeedback(_ action: PremiumHaptics.HapticAction) -> some View {
        self.onTapGesture {
            PremiumHaptics.contextualFeedback(for: action)
        }
    }
    
    func premiumShadow(_ shadowStyle: PremiumDesignSystem.Shadow) -> some View {
        self.shadow(
            color: shadowStyle.color,
            radius: shadowStyle.radius,
            x: shadowStyle.x,
            y: shadowStyle.y
        )
    }
    
    func glassmorphism() -> some View {
        self
            .background(PremiumDesignSystem.Colors.glassBackground)
            .overlay(
                RoundedRectangle(cornerRadius: PremiumDesignSystem.cornerRadius)
                    .stroke(PremiumDesignSystem.Colors.glassStroke, lineWidth: 1)
            )
            .backdrop(PremiumDesignSystem.glassMaterial)
    }
    
    func backdrop(_ material: Material) -> some View {
        self.background(material)
    }
}

// MARK: - Supporting Types

struct Shadow {
    let color: Color
    let radius: CGFloat
    let x: CGFloat
    let y: CGFloat
}

// MARK: - Premium Loading States

@available(iOS 18.0, macOS 14.0, *)
struct PremiumLoadingView: View {
    @State private var isAnimating = false
    let size: CGFloat
    let color: Color
    
    init(size: CGFloat = 50, color: Color = PremiumDesignSystem.Colors.primary) {
        self.size = size
        self.color = color
    }
    
    var body: some View {
        ZStack {
            Circle()
                .stroke(color.opacity(0.3), lineWidth: 4)
                .frame(width: size, height: size)
            
            Circle()
                .trim(from: 0, to: 0.7)
                .stroke(color, style: StrokeStyle(lineWidth: 4, lineCap: .round))
                .frame(width: size, height: size)
                .rotationEffect(.degrees(isAnimating ? 360 : 0))
                .animation(
                    .linear(duration: 1.0).repeatForever(autoreverses: false),
                    value: isAnimating
                )
        }
        .onAppear {
            isAnimating = true
        }
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct PremiumProgressBar: View {
    let progress: Double
    let color: Color
    let backgroundColor: Color
    
    init(
        progress: Double,
        color: Color = PremiumDesignSystem.Colors.primary,
        backgroundColor: Color = PremiumDesignSystem.Colors.tertiaryBackground
    ) {
        self.progress = progress
        self.color = color
        self.backgroundColor = backgroundColor
    }
    
    var body: some View {
        GeometryReader { geometry in
            ZStack(alignment: .leading) {
                Rectangle()
                    .fill(backgroundColor)
                    .frame(height: 8)
                    .cornerRadius(4)
                
                Rectangle()
                    .fill(color)
                    .frame(width: geometry.size.width * progress, height: 8)
                    .cornerRadius(4)
                    .animation(.easeInOut(duration: 0.5), value: progress)
            }
        }
        .frame(height: 8)
    }
}
