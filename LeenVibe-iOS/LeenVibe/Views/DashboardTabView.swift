import SwiftUI

struct DashboardTabView: View {
    @StateObject private var webSocketService = WebSocketService()
    @StateObject private var projectManager = ProjectManager()
    @StateObject private var speechService: SpeechRecognitionService
    @StateObject private var wakePhraseManager: WakePhraseManager
    @StateObject private var permissionManager = VoicePermissionManager()
    @StateObject private var globalVoice: GlobalVoiceManager
    @StateObject private var navigationCoordinator = NavigationCoordinator()
    
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
        self._globalVoice = StateObject(wrappedValue: GlobalVoiceManager(
            webSocketService: webSocket,
            projectManager: projectMgr
        ))
    }
    
    var body: some View {
        ZStack {
            TabView(selection: $navigationCoordinator.selectedTab) {
                NavigationStack(path: $navigationCoordinator.navigationPath) {
                    ProjectDashboardView(
                        projectManager: projectManager,
                        webSocketService: webSocketService
                    )
                    .navigationDestination(for: String.self) { destination in
                        if destination.hasPrefix("project-") {
                            let projectId = String(destination.dropFirst("project-".count))
                            ProjectDetailView(projectId: projectId, projectManager: projectManager)
                        }
                    }
                }
                .tabItem {
                    Label(NavigationCoordinator.Tab.projects.title, 
                          systemImage: NavigationCoordinator.Tab.projects.systemImage)
                }
                .tag(NavigationCoordinator.Tab.projects.rawValue)
                
                NavigationStack(path: $navigationCoordinator.navigationPath) {
                    ChatView(webSocketService: webSocketService)
                }
                .tabItem {
                    Label(NavigationCoordinator.Tab.agent.title,
                          systemImage: NavigationCoordinator.Tab.agent.systemImage)
                }
                .tag(NavigationCoordinator.Tab.agent.rawValue)
                
                NavigationStack(path: $navigationCoordinator.navigationPath) {
                    MonitoringView(
                        projectManager: projectManager,
                        webSocketService: webSocketService
                    )
                    .navigationDestination(for: String.self) { destination in
                        if destination.hasPrefix("task-") {
                            let taskId = String(destination.dropFirst("task-".count))
                            TaskDetailView(taskId: taskId, webSocketService: webSocketService)
                        }
                    }
                }
                .tabItem {
                    Label(NavigationCoordinator.Tab.monitor.title,
                          systemImage: NavigationCoordinator.Tab.monitor.systemImage)
                }
                .tag(NavigationCoordinator.Tab.monitor.rawValue)
                
                NavigationStack(path: $navigationCoordinator.navigationPath) {
                    SettingsTabView(webSocketService: webSocketService)
                }
                .tabItem {
                    Label(NavigationCoordinator.Tab.settings.title,
                          systemImage: NavigationCoordinator.Tab.settings.systemImage)
                }
                .tag(NavigationCoordinator.Tab.settings.rawValue)
                
                NavigationStack(path: $navigationCoordinator.navigationPath) {
                    VoiceTabView(
                        webSocketService: webSocketService,
                        projectManager: projectManager
                    )
                }
                .tabItem {
                    ZStack {
                        Label(NavigationCoordinator.Tab.voice.title,
                              systemImage: NavigationCoordinator.Tab.voice.systemImage)
                        
                        VoiceStatusBadge(
                            wakePhraseManager: wakePhraseManager,
                            speechService: speechService
                        )
                        .offset(x: 10, y: -10)
                    }
                }
                .tag(NavigationCoordinator.Tab.voice.rawValue)
            }
            
            // Floating voice indicator (appears on all tabs except Voice tab)
            FloatingVoiceIndicator(
                wakePhraseManager: wakePhraseManager,
                speechService: speechService,
                permissionManager: permissionManager,
                webSocketService: webSocketService
            )
            
            // Global voice command overlay
            if globalVoice.isVoiceCommandActive {
                GlobalVoiceCommandView(globalVoice: globalVoice)
                    .zIndex(999)
            }
        }
        .environmentObject(navigationCoordinator)
        .onAppear {
            // Initialize project manager with WebSocket service
            projectManager.configure(with: webSocketService)
            
            // Start global voice listening if permissions are available
            if permissionManager.isFullyAuthorized {
                globalVoice.startGlobalVoiceListening()
            }
        }
        .onDisappear {
            // Stop global voice listening when view disappears
            globalVoice.stopGlobalVoiceListening()
        }
        .onOpenURL { url in
            navigationCoordinator.handleURL(url)
        }
    }
}

#Preview {
    DashboardTabView()
}