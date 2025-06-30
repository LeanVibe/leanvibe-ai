import SwiftUI
import Foundation

@MainActor
class NavigationCoordinator: ObservableObject {
    @Published var selectedTab = 0
    @Published var navigationPath = NavigationPath()
    @Published var pendingDeepLink: DeepLink?
    
    enum DeepLink: Equatable {
        case dashboard
        case projects
        case agent
        case monitor
        case settings
        case voice
        case project(String)
        case task(String)
        case qrScanner
        case voiceCommand
        
        static func == (lhs: DeepLink, rhs: DeepLink) -> Bool {
            switch (lhs, rhs) {
            case (.dashboard, .dashboard), (.projects, .projects), (.agent, .agent),
                 (.monitor, .monitor), (.settings, .settings), (.voice, .voice),
                 (.qrScanner, .qrScanner), (.voiceCommand, .voiceCommand):
                return true
            case let (.project(lhsId), .project(rhsId)):
                return lhsId == rhsId
            case let (.task(lhsId), .task(rhsId)):
                return lhsId == rhsId
            default:
                return false
            }
        }
    }
    
    enum Tab: Int, CaseIterable {
        case projects = 0
        case agent = 1
        case monitor = 2
        case settings = 3
        case voice = 4
        
        var title: String {
            switch self {
            case .projects: return "Projects"
            case .agent: return "Agent"
            case .monitor: return "Monitor"
            case .settings: return "Settings"
            case .voice: return "Voice"
            }
        }
        
        var systemImage: String {
            switch self {
            case .projects: return "folder.fill"
            case .agent: return "brain.head.profile"
            case .monitor: return "chart.line.uptrend.xyaxis"
            case .settings: return "gear"
            case .voice: return "mic.circle.fill"
            }
        }
    }
    
    func handle(deepLink: DeepLink) {
        pendingDeepLink = deepLink
        
        switch deepLink {
        case .dashboard, .projects:
            selectedTab = Tab.projects.rawValue
        case .agent:
            selectedTab = Tab.agent.rawValue
        case .monitor:
            selectedTab = Tab.monitor.rawValue
        case .settings:
            selectedTab = Tab.settings.rawValue
        case .voice, .voiceCommand:
            selectedTab = Tab.voice.rawValue
        case .project(let projectId):
            selectedTab = Tab.projects.rawValue
            navigateToProject(projectId)
        case .task(let taskId):
            selectedTab = Tab.monitor.rawValue
            navigateToTask(taskId)
        case .qrScanner:
            // QR scanner is handled at app level, not tab level
            break
        }
    }
    
    private func navigateToProject(_ projectId: String) {
        // Clear existing navigation
        navigationPath = NavigationPath()
        
        // Add project to navigation path
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
            self.navigationPath.append("project-\(projectId)")
        }
    }
    
    private func navigateToTask(_ taskId: String) {
        // Clear existing navigation
        navigationPath = NavigationPath()
        
        // Add task to navigation path
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
            self.navigationPath.append("task-\(taskId)")
        }
    }
    
    func resetNavigation() {
        navigationPath = NavigationPath()
        pendingDeepLink = nil
    }
    
    func popToRoot() {
        navigationPath = NavigationPath()
    }
    
    func switchToTab(_ tab: Tab) {
        selectedTab = tab.rawValue
        resetNavigation()
    }
    
    // MARK: - URL Handling
    
    func handleURL(_ url: URL) {
        guard url.scheme == "leanvibe" else { return }
        
        let path = url.path
        let components = path.components(separatedBy: "/").filter { !$0.isEmpty }
        
        guard !components.isEmpty else {
            handle(deepLink: .dashboard)
            return
        }
        
        switch components[0] {
        case "projects":
            if components.count > 1 {
                handle(deepLink: .project(components[1]))
            } else {
                handle(deepLink: .projects)
            }
        case "agent":
            handle(deepLink: .agent)
        case "monitor":
            handle(deepLink: .monitor)
        case "settings":
            handle(deepLink: .settings)
        case "voice":
            handle(deepLink: .voice)
        case "task":
            if components.count > 1 {
                handle(deepLink: .task(components[1]))
            } else {
                handle(deepLink: .monitor)
            }
        case "qr":
            handle(deepLink: .qrScanner)
        default:
            handle(deepLink: .dashboard)
        }
    }
    
    // MARK: - Voice Command Navigation
    
    func handleVoiceCommand(_ command: String) {
        let lowercased = command.lowercased()
        
        if lowercased.contains("project") {
            handle(deepLink: .projects)
        } else if lowercased.contains("agent") || lowercased.contains("chat") {
            handle(deepLink: .agent)
        } else if lowercased.contains("monitor") || lowercased.contains("status") {
            handle(deepLink: .monitor)
        } else if lowercased.contains("settings") || lowercased.contains("config") {
            handle(deepLink: .settings)
        } else if lowercased.contains("voice") {
            handle(deepLink: .voice)
        } else if lowercased.contains("scan") || lowercased.contains("qr") {
            handle(deepLink: .qrScanner)
        }
    }
}