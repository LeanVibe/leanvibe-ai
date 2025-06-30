
import Foundation

struct OnboardingProgress: Codable {
    var completedSteps: Set<OnboardingStep> = []
}
