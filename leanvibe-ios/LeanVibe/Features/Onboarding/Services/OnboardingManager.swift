
import Foundation
import Combine

@available(iOS 18.0, macOS 14.0, *)
class OnboardingManager: ObservableObject {
    @Published private var onboardingProgress = OnboardingProgress() {
        didSet {
            saveState()
        }
    }
    
    // MARK: - OnboardingManagerProtocol Implementation
    
    var completedSteps: Set<OnboardingStep> {
        onboardingProgress.completedSteps
    }
    
    var isOnboardingComplete: Bool {
        completedSteps.count == OnboardingStep.allCases.count
    }
    
    var progress: Double {
        let totalSteps = OnboardingStep.allCases.count
        let completedCount = completedSteps.count
        return totalSteps > 0 ? Double(completedCount) / Double(totalSteps) : 0.0
    }
    
    private let userDefaultsKey = "onboardingProgress"

    init() {
        loadState()
    }

    func markStepCompleted(_ step: OnboardingStep) {
        onboardingProgress.completedSteps.insert(step)
    }
    
    func getNextIncompleteStep() -> OnboardingStep? {
        return OnboardingStep.allCases.first { step in
            !completedSteps.contains(step)
        }
    }
    
    func isStepCompleted(_ step: OnboardingStep) -> Bool {
        return completedSteps.contains(step)
    }
    
    func resetOnboarding() {
        onboardingProgress = OnboardingProgress()
    }

    func saveState() {
        if let encoded = try? JSONEncoder().encode(onboardingProgress) {
            UserDefaults.standard.set(encoded, forKey: userDefaultsKey)
        }
    }

    func loadState() {
        if let savedProgress = UserDefaults.standard.data(forKey: userDefaultsKey) {
            if let decodedProgress = try? JSONDecoder().decode(OnboardingProgress.self, from: savedProgress) {
                self.onboardingProgress = decodedProgress
            }
        }
    }
}
