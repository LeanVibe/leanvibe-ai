
import Foundation

enum OnboardingStep: String, CaseIterable, Codable, Hashable {
    case welcome
    case voicePermissions
    case projectSetup
    case dashboardTour
    case voiceCommandDemo
    case architectureViewer
    case kanbanIntroduction
    case advancedFeatures
    case completion
}
