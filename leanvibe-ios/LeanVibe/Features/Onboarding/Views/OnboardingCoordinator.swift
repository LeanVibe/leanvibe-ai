
import SwiftUI

@available(iOS 18.0, macOS 14.0, *)
struct OnboardingCoordinator: View {
    @StateObject private var onboardingManager = OnboardingManager()
    @State private var currentStep: OnboardingStep = .welcome
    @State private var isStateRestored = false

    var body: some View {
        NavigationView {
            if isStateRestored {
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
            } else {
                // Show loading state while determining correct step
                ProgressView("Loading...")
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            }
        }
        .onAppear {
            // Initialize to the correct step immediately to prevent flash of wrong content
            restoreOnboardingState()
        }
    }
    
    private func restoreOnboardingState() {
        // Determine the correct step based on saved progress
        if onboardingManager.isOnboardingComplete {
            // All steps completed - show completion
            currentStep = .completion
        } else if let nextStep = onboardingManager.getNextIncompleteStep() {
            // Resume from next incomplete step
            currentStep = nextStep
        } else {
            // No saved state or empty state - start from beginning
            currentStep = .welcome
        }
        
        // State is now properly restored, show the content
        isStateRestored = true
    }
}
