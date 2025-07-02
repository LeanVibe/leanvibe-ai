
import SwiftUI

@available(iOS 18.0, macOS 14.0, *)
struct TutorialOverlay: ViewModifier {
    let tutorial: Tutorial
    @State private var currentStep: TutorialStep?

    func body(content: Content) -> some View {
        content
            .overlay(tutorialContent)
    }

    @ViewBuilder
    private var tutorialContent: some View {
        if let step = currentStep {
            // Placeholder for the tutorial content
            Text(step.text)
                .padding()
                .background(Color.black.opacity(0.8))
                .foregroundColor(.white)
                .cornerRadius(10)
                .padding()
        }
    }
}

@available(iOS 18.0, macOS 14.0, *)
extension View {
    func tutorialOverlay(_ tutorial: Tutorial) -> some View {
        modifier(TutorialOverlay(tutorial: tutorial))
    }
}
