import SwiftUI

struct DashboardTabView: View {
    @StateObject private var webSocketService = WebSocketService()
    @StateObject private var projectManager = ProjectManager()
    
    var body: some View {
        TabView {
            ProjectDashboardView(
                projectManager: projectManager,
                webSocketService: webSocketService
            )
            .tabItem {
                Label("Projects", systemImage: "folder.fill")
            }
            .tag(0)
            
            ChatView(webSocketService: webSocketService)
                .tabItem {
                    Label("Agent", systemImage: "brain.head.profile")
                }
                .tag(1)
            
            MonitoringView(
                projectManager: projectManager,
                webSocketService: webSocketService
            )
            .tabItem {
                Label("Monitor", systemImage: "chart.line.uptrend.xyaxis")
            }
            .tag(2)
            
            SettingsTabView(webSocketService: webSocketService)
                .tabItem {
                    Label("Settings", systemImage: "gear")
                }
                .tag(3)
        }
        .onAppear {
            // Initialize project manager with WebSocket service
            projectManager.configure(with: webSocketService)
        }
    }
}

#Preview {
    DashboardTabView()
}