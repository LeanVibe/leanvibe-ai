import SwiftUI

// MARK: - Premium Transition Extensions

@available(iOS 18.0, macOS 14.0, *)
extension View {
    // MARK: - Page Transitions
    
    func premiumPageTransition(isPresented: Bool) -> some View {
        self
            .transition(PremiumTransitions.pageTransition)
            .animation(PremiumTransitions.spring, value: isPresented)
    }
    
    func premiumModalTransition(isPresented: Bool) -> some View {
        self
            .transition(PremiumTransitions.modalTransition)
            .animation(PremiumTransitions.easeInOut, value: isPresented)
    }
    
    func premiumCardTransition(isPresented: Bool) -> some View {
        self
            .transition(PremiumTransitions.cardTransition)
            .animation(PremiumTransitions.spring, value: isPresented)
    }
    
    // MARK: - Interactive Transitions
    
    func premiumSwipeTransition(
        direction: SwipeDirection,
        isPresented: Bool
    ) -> some View {
        self
            .transition(direction.transition)
            .animation(PremiumTransitions.easeOut, value: isPresented)
    }
    
    func premiumFadeTransition(
        duration: Double = PremiumDesignSystem.animationDuration,
        isPresented: Bool
    ) -> some View {
        self
            .transition(.opacity)
            .animation(.easeInOut(duration: duration), value: isPresented)
    }
    
    func premiumScaleTransition(
        scale: CGFloat = 0.8,
        isPresented: Bool
    ) -> some View {
        self
            .transition(PremiumTransitions.fadeScale)
            .animation(PremiumTransitions.spring, value: isPresented)
    }
    
    // MARK: - State-Based Transitions
    
    func premiumStateTransition<V: Equatable>(
        for value: V,
        transition: AnyTransition = PremiumTransitions.cardTransition
    ) -> some View {
        self
            .transition(transition)
            .animation(PremiumTransitions.spring, value: value)
    }
    
    // MARK: - Conditional Transitions
    
    func premiumConditionalTransition(
        condition: Bool,
        activeTransition: AnyTransition = PremiumTransitions.slideFromRight,
        inactiveTransition: AnyTransition = PremiumTransitions.slideFromLeft
    ) -> some View {
        self
            .transition(condition ? activeTransition : inactiveTransition)
            .animation(PremiumTransitions.easeInOut, value: condition)
    }
    
    // MARK: - Navigation Transitions
    
    func premiumNavigationTransition(
        isNavigating: Bool,
        direction: NavigationDirection = .forward
    ) -> some View {
        self
            .transition(direction.transition)
            .animation(PremiumTransitions.easeInOut, value: isNavigating)
            .onAppear {
                if isNavigating {
                    PremiumHaptics.navigationPop()
                }
            }
    }
    
    // MARK: - Content Transitions
    
    func premiumContentChange<V: Equatable>(
        for value: V,
        transition: ContentTransitionType = .fade
    ) -> some View {
        self
            .transition(transition.transition)
            .animation(transition.animation, value: value)
    }
    
    // MARK: - Interactive Gestures with Transitions
    
    func premiumDragTransition(
        offset: CGSize,
        threshold: CGFloat = 100
    ) -> some View {
        self
            .offset(offset)
            .scaleEffect(1 - abs(offset.width) / 1000)
            .opacity(1 - abs(offset.width) / 500.0)
            .animation(PremiumTransitions.microInteraction, value: offset)
    }
    
    func premiumPullToRefreshTransition(
        pullDistance: CGFloat,
        threshold: CGFloat = 80
    ) -> some View {
        self
            .offset(y: max(0, pullDistance))
            .scaleEffect(1 + min(pullDistance / 1000, 0.1))
            .animation(PremiumTransitions.spring, value: pullDistance)
    }
            
    
    // MARK: - Loading State Transitions
    
    
    
    // MARK: - Error State Transitions
    
    func premiumErrorTransition(
        hasError: Bool,
        errorContent: some View
    ) -> some View {
        ZStack {
            if !hasError {
                self
                    .transition(PremiumTransitions.slideFromBottom)
            }
            
            if hasError {
                errorContent
                    .transition(PremiumTransitions.slideFromTop)
            }
        }
        .animation(PremiumTransitions.spring, value: hasError)
        .onChange(of: hasError) { newValue in
            if newValue {
                PremiumHaptics.errorNotification()
            }
        }
    }
    
    // MARK: - Success State Transitions
    
    func premiumSuccessTransition(
        showSuccess: Bool,
        successContent: some View
    ) -> some View {
        ZStack {
            self
            
            if showSuccess {
                successContent
                    .transition(PremiumTransitions.fadeScale)
            }
        }
        .animation(PremiumTransitions.spring, value: showSuccess)
        
    }
    
    // MARK: - List Item Transitions
    
    func premiumListItemTransition(
        index: Int,
        staggerDelay: Double = 0.1
    ) -> some View {
        self
            .transition(.asymmetric(
                insertion: .move(edge: .trailing).combined(with: .opacity),
                removal: .move(edge: .leading).combined(with: .opacity)
            ))
            .animation(
                .easeInOut(duration: 0.3).delay(Double(index) * staggerDelay),
                value: index
            )
    }
    
    // MARK: - Tab Transitions
    
    func premiumTabTransition(
        selectedTab: Int,
        currentTab: Int
    ) -> some View {
        self
            .transition(.asymmetric(
                insertion: selectedTab > currentTab ? 
                    .move(edge: .trailing) : .move(edge: .leading),
                removal: selectedTab > currentTab ? 
                    .move(edge: .leading) : .move(edge: .trailing)
            ))
            .animation(PremiumTransitions.easeInOut, value: selectedTab)
    }
}

// MARK: - Supporting Types

enum SwipeDirection {
    case left, right, up, down
    
    var transition: AnyTransition {
        switch self {
        case .left: return PremiumTransitions.slideFromLeft
        case .right: return PremiumTransitions.slideFromRight
        case .up: return PremiumTransitions.slideFromTop
        case .down: return PremiumTransitions.slideFromBottom
        }
    }
}

enum NavigationDirection {
    case forward, backward
    
    var transition: AnyTransition {
        switch self {
        case .forward: return PremiumTransitions.slideFromRight
        case .backward: return PremiumTransitions.slideFromLeft
        }
    }
}

enum ContentTransitionType {
    case fade
    case scale
    case slide
    case flip
    case custom(AnyTransition, Animation)
    
    var transition: AnyTransition {
        switch self {
        case .fade:
            return .opacity
        case .scale:
            return PremiumTransitions.fadeScale
        case .slide:
            return PremiumTransitions.slideFromRight
        case .flip:
            return PremiumTransitions.flipHorizontal
        case .custom(let transition, _):
            return transition
        }
    }
    
    var animation: Animation {
        switch self {
        case .fade, .scale, .slide, .flip:
            return PremiumTransitions.easeInOut
        case .custom(_, let animation):
            return animation
        }
    }
}

// MARK: - Transition Coordinators

@MainActor
class PremiumTransitionCoordinator: ObservableObject {
    @Published var isTransitioning = false
    @Published var transitionProgress: Double = 0
    
    private var transitionTimer: Timer?
    
    func beginTransition(duration: Double = 0.3) {
        isTransitioning = true
        transitionProgress = 0
        
        let steps = Int(duration * 60) // 60 FPS
        let increment = 1.0 / Double(steps)
        
        transitionTimer?.invalidate()
        transitionTimer = Timer.scheduledTimer(withTimeInterval: duration / Double(steps), repeats: true) { [weak self] _ in
            guard let self = self else { return }
            
            DispatchQueue.main.async {
                self.transitionProgress += increment
                
                if self.transitionProgress >= 1.0 {
                    self.completeTransition()
                }
            }
        }
    }
    
    func completeTransition() {
        isTransitioning = false
        transitionProgress = 1.0
        transitionTimer?.invalidate()
        transitionTimer = nil
    }
    
    func cancelTransition() {
        isTransitioning = false
        transitionProgress = 0
        transitionTimer?.invalidate()
        transitionTimer = nil
    }
}

// MARK: - Advanced Transition Modifiers

struct PremiumTransitionModifier: ViewModifier {
    let isPresented: Bool
    let transition: AnyTransition
    let animation: Animation
    let hapticFeedback: PremiumHaptics.HapticAction?
    
    func body(content: Content) -> some View {
        content
            .transition(transition)
            .animation(animation, value: isPresented)
            .onChange(of: isPresented) { newValue in
                if let hapticFeedback = hapticFeedback, newValue {
                    PremiumHaptics.contextualFeedback(for: hapticFeedback)
                }
            }
    }
}

extension View {
    func premiumTransition(
        isPresented: Bool,
        transition: AnyTransition = PremiumTransitions.cardTransition,
        animation: Animation = PremiumTransitions.spring,
        hapticFeedback: PremiumHaptics.HapticAction? = nil
    ) -> some View {
        self.modifier(PremiumTransitionModifier(
            isPresented: isPresented,
            transition: transition,
            animation: animation,
            hapticFeedback: hapticFeedback
        ))
    }
}

// MARK: - Gesture-Based Transitions

struct PremiumSwipeTransition: ViewModifier {
    @State private var dragOffset = CGSize.zero
    @State private var isDragging = false
    
    let onSwipe: (SwipeDirection) -> Void
    let threshold: CGFloat
    
    func body(content: Content) -> some View {
        content
            .offset(dragOffset)
            .scaleEffect(isDragging ? 0.95 : 1.0)
            .opacity(isDragging ? 0.8 : 1.0)
            .gesture(
                DragGesture()
                    .onChanged { value in
                        if !isDragging {
                            isDragging = true
                            PremiumHaptics.lightImpact()
                        }
                        dragOffset = value.translation
                    }
                    .onEnded { value in
                        isDragging = false
                        
                        let direction = getSwipeDirection(from: value.translation)
                        let distance = getSwipeDistance(from: value.translation)
                        
                        if distance > threshold {
                            onSwipe(direction)
                            PremiumHaptics.mediumImpact()
                        }
                        
                        withAnimation(PremiumTransitions.spring) {
                            dragOffset = .zero
                        }
                    }
            )
            .animation(PremiumTransitions.microInteraction, value: isDragging)
    }
    
    private func getSwipeDirection(from translation: CGSize) -> SwipeDirection {
        if abs(translation.width) > abs(translation.height) {
            return translation.width > 0 ? .right : .left
        } else {
            return translation.height > 0 ? .down : .up
        }
    }
    
    private func getSwipeDistance(from translation: CGSize) -> CGFloat {
        return sqrt(translation.width * translation.width + translation.height * translation.height)
    }
}

extension View {
    func premiumSwipeGesture(
        threshold: CGFloat = 100,
        onSwipe: @escaping (SwipeDirection) -> Void
    ) -> some View {
        self.modifier(PremiumSwipeTransition(
            onSwipe: onSwipe,
            threshold: threshold
        ))
    }
}

// MARK: - Performance-Optimized Transitions

struct PerformanceOptimizedTransition: ViewModifier {
    let isPresented: Bool
    let shouldOptimize: Bool
    
    func body(content: Content) -> some View {
        Group {
            if shouldOptimize {
                content
                    .transition(.opacity)
                    .animation(.linear(duration: 0.1), value: isPresented)
            } else {
                content
                    .transition(PremiumTransitions.cardTransition)
                    .animation(PremiumTransitions.spring, value: isPresented)
            }
        }
    }
}

extension View {
    func performanceAwareTransition(
        isPresented: Bool,
        shouldOptimize: Bool = false
    ) -> some View {
        self.modifier(PerformanceOptimizedTransition(
            isPresented: isPresented,
            shouldOptimize: shouldOptimize
        ))
    }
}