
import Foundation
import Combine

class OnboardingManager: ObservableObject {
    @Published var progress = OnboardingProgress() {
        didSet {
            saveProgress()
        }
    }
    
    private let userDefaultsKey = "onboardingProgress"

    init() {
        loadProgress()
    }

    func markStepCompleted(_ step: OnboardingStep) {
        progress.completedSteps.insert(step)
    }
    
    func isStepCompleted(_ step: OnboardingStep) -> Bool {
        progress.completedSteps.contains(step)
    }

    private func saveProgress() {
        if let encoded = try? JSONEncoder().encode(progress) {
            UserDefaults.standard.set(encoded, forKey: userDefaultsKey)
        }
    }

    private func loadProgress() {
        if let savedProgress = UserDefaults.standard.data(forKey: userDefaultsKey) {
            if let decodedProgress = try? JSONDecoder().decode(OnboardingProgress.self, from: savedProgress) {
                self.progress = decodedProgress
            }
        }
    }
}
