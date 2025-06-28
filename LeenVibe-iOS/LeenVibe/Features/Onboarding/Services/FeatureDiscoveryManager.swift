
import Foundation

enum DiscoverableFeature: String, CaseIterable, Identifiable {
    case dashboard
    case voiceCommands
    case architectureViewer
    case kanban
    case notifications
    
    var id: String { self.rawValue }
    
    var name: String {
        switch self {
        case .dashboard: return "Dashboard"
        case .voiceCommands: return "Voice Commands"
        case .architectureViewer: return "Architecture Viewer"
        case .kanban: return "Kanban Board"
        case .notifications: return "Notifications"
        }
    }
}

enum ExpertiseLevel: String, Codable {
    case beginner
    case intermediate
    case expert
}

class FeatureDiscoveryManager: ObservableObject {
    @Published var availableFeatures: [DiscoverableFeature] = DiscoverableFeature.allCases
    @Published var userExpertiseLevel: ExpertiseLevel = .beginner
    
    func suggestNextFeature() -> DiscoverableFeature? {
        // Placeholder for logic to suggest next feature based on user behavior
        return nil
    }
    
    func showContextualTip(for feature: DiscoverableFeature) -> String? {
        // Placeholder for contextual tips
        return nil
    }
}
