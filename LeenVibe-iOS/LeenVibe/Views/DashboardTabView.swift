import SwiftUI

struct DashboardTabView: View {
    @StateObject private var webSocketService = WebSocketService()
    @StateObject private var projectManager = ProjectManager()
    @StateObject private var speechService: SpeechRecognitionService
    @StateObject private var wakePhraseManager: WakePhraseManager
    @StateObject private var permissionManager = VoicePermissionManager()
    
    @State private var showingVoiceInterface = false
    
    init() {
        let webSocket = WebSocketService()
        let projectMgr = ProjectManager()
        let voiceProcessor = DashboardVoiceProcessor(projectManager: projectMgr, webSocketService: webSocket)
        
        self._webSocketService = StateObject(wrappedValue: webSocket)
        self._projectManager = StateObject(wrappedValue: projectMgr)
        self._speechService = StateObject(wrappedValue: SpeechRecognitionService(webSocketService: webSocket))
        self._wakePhraseManager = StateObject(wrappedValue: WakePhraseManager(
            webSocketService: webSocket,
            projectManager: projectMgr,
            voiceProcessor: voiceProcessor
        ))
    }
    
    var body: some View {
        ZStack {
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
                
                VoiceTabView(
                    webSocketService: webSocketService,
                    projectManager: projectManager
                )
                .tabItem {
                    ZStack {
                        Label("Voice", systemImage: "mic.circle.fill")
                        
                        VoiceStatusBadge(
                            wakePhraseManager: wakePhraseManager,
                            speechService: speechService
                        )
                        .offset(x: 10, y: -10)
                    }
                }
                .tag(4)
            }
            
            // Floating voice indicator (appears on all tabs except Voice tab)
            FloatingVoiceIndicator(
                wakePhraseManager: wakePhraseManager,
                speechService: speechService,
                permissionManager: permissionManager,
                webSocketService: webSocketService
            )
        }
        .onAppear {
            // Initialize project manager with WebSocket service
            projectManager.configure(with: webSocketService)
            
            // Start wake phrase listening if permissions are available
            if permissionManager.isFullyAuthorized {
                wakePhraseManager.startWakeListening()
            }
        }
    }
}

#Preview {
    DashboardTabView()
}