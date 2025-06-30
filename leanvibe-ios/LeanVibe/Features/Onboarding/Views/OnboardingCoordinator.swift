
import SwiftUI

struct OnboardingCoordinator: View {
    @State private var currentStep: OnboardingStep = .welcome
    @StateObject private var onboardingManager = OnboardingManager()

    var body: some View {
        NavigationView {
            switch currentStep {
            case .welcome:
                WelcomeOnboardingView(onContinue: { 
                    onboardingManager.markStepCompleted(.welcome)
                    currentStep = .voicePermissions 
                })
            case .voicePermissions:
                VoicePermissionOnboardingView(onContinue: { 
                    onboardingManager.markStepCompleted(.voicePermissions)
                    currentStep = .projectSetup 
                })
            case .projectSetup:
                ProjectSetupOnboardingView(onContinue: { 
                    onboardingManager.markStepCompleted(.projectSetup)
                    currentStep = .dashboardTour 
                })
            case .dashboardTour:
                DashboardTourOnboardingView(onContinue: { 
                    onboardingManager.markStepCompleted(.dashboardTour)
                    currentStep = .voiceCommandDemo 
                })
            case .voiceCommandDemo:
                VoiceCommandDemoOnboardingView(onContinue: { 
                    onboardingManager.markStepCompleted(.voiceCommandDemo)
                    currentStep = .architectureViewer 
                })
            case .architectureViewer:
                ArchitectureViewerOnboardingView(onContinue: { 
                    onboardingManager.markStepCompleted(.architectureViewer)
                    currentStep = .kanbanIntroduction 
                })
            case .kanbanIntroduction:
                KanbanIntroductionOnboardingView(onContinue: { 
                    onboardingManager.markStepCompleted(.kanbanIntroduction)
                    currentStep = .advancedFeatures 
                })
            case .advancedFeatures:
                AdvancedFeaturesOnboardingView(onContinue: { 
                    onboardingManager.markStepCompleted(.advancedFeatures)
                    currentStep = .completion 
                })
            case .completion:
                CompletionOnboardingView(onComplete: { 
                    onboardingManager.markStepCompleted(.completion)
                    // Handle completion, e.g., dismiss onboarding
                })
            }
        }
    }
}
