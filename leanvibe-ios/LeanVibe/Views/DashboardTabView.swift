import SwiftUI

// Voice service wrapper to handle optional initialization
@MainActor
class VoiceServiceContainer: ObservableObject {
    let speechService: SpeechRecognitionService?
    let wakePhraseManager: WakePhraseManager?
    let permissionManager: VoicePermissionManager?
    let globalVoice: GlobalVoiceManager?
    
    init(webSocket: WebSocketService, projectManager: ProjectManager, settingsManager: SettingsManager, isVoiceEnabled: Bool) {
        if isVoiceEnabled {
            let voiceProcessor = DashboardVoiceProcessor(
                projectManager: projectManager,
                webSocketService: webSocket,
                settingsManager: settingsManager
            )
            
            self.speechService = SpeechRecognitionService()
            self.wakePhraseManager = WakePhraseManager(
                webSocketService: webSocket,
                projectManager: projectManager,
                voiceProcessor: voiceProcessor
            )
            self.globalVoice = GlobalVoiceManager(
                webSocketService: webSocket,
                projectManager: projectManager,
                settingsManager: settingsManager
            )
            self.permissionManager = VoicePermissionManager()
        } else {
            self.speechService = nil
            self.wakePhraseManager = nil
            self.globalVoice = nil
            self.permissionManager = nil
        }
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct DashboardTabView: View {
    @StateObject private var webSocketService = WebSocketService.shared
    @StateObject private var projectManager = ProjectManager()
    @StateObject private var voiceContainer: VoiceServiceContainer
    @StateObject private var taskService = TaskService()
    // Conditional service initialization based on configuration
    private var unifiedVoice: UnifiedVoiceService? {
        guard AppConfiguration.shared.isVoiceEnabled else { return nil }
        return AppConfiguration.shared.useUnifiedVoiceService ? UnifiedVoiceService.shared : nil
    }
    @StateObject private var navigationCoordinator = NavigationCoordinator()
    @StateObject private var performanceAnalytics = PerformanceAnalytics()
    @StateObject private var batteryManager = BatteryOptimizedManager()
    @StateObject private var settingsManager = SettingsManager.shared
    
    @State private var showingVoiceInterface = false
    
    init() {
        let webSocket = WebSocketService.shared
        let projectMgr = ProjectManager()
        let settingsMgr = SettingsManager.shared
        
        self._webSocketService = StateObject(wrappedValue: webSocket)
        self._projectManager = StateObject(wrappedValue: projectMgr)
        
        // Initialize voice container with conditional voice services
        self._voiceContainer = StateObject(wrappedValue: VoiceServiceContainer(
            webSocket: webSocket,
            projectManager: projectMgr,
            settingsManager: settingsMgr,
            isVoiceEnabled: AppConfiguration.shared.isVoiceEnabled
        ))
    }
    
    var body: some View {
        ZStack {
            // Premium background with glassmorphism
            Rectangle()
                .fill(PremiumDesignSystem.Colors.background)
                .ignoresSafeArea()
            
            TabView(selection: $navigationCoordinator.selectedTab) {
                NavigationStack(path: $navigationCoordinator.navigationPath) {
                    ProjectDashboardView(
                        projectManager: projectManager,
                        webSocketService: webSocketService
                    )
                    .navigationDestination(for: String.self) { destination in
                        if destination.hasPrefix("project-") {
                            let projectId = String(destination.dropFirst("project-".count))
                            if let projectUUID = UUID(uuidString: projectId),
                               let project = projectManager.projects.first(where: { $0.id == projectUUID }) {
                                ProjectDetailView(
                                    project: project, 
                                    projectManager: projectManager,
                                    webSocketService: webSocketService
                                )
                            }
                        }
                    }
                }
                .tabItem {
                    Label(NavigationCoordinator.Tab.projects.title, 
                          systemImage: NavigationCoordinator.Tab.projects.systemImage)
                }
                .tag(NavigationCoordinator.Tab.projects.rawValue)
                .hapticFeedback(.navigation)
                
                NavigationStack(path: $navigationCoordinator.navigationPath) {
                    ChatView(webSocketService: webSocketService)
                }
                .tabItem {
                    Label(NavigationCoordinator.Tab.agent.title,
                          systemImage: NavigationCoordinator.Tab.agent.systemImage)
                }
                .tag(NavigationCoordinator.Tab.agent.rawValue)
                .hapticFeedback(.navigation)
                
                NavigationStack(path: $navigationCoordinator.navigationPath) {
                    MonitoringView(
                        projectManager: projectManager,
                        webSocketService: webSocketService,
                        taskService: taskService
                    )
                }
                .tabItem {
                    Label(NavigationCoordinator.Tab.monitor.title,
                          systemImage: NavigationCoordinator.Tab.monitor.systemImage)
                }
                .tag(NavigationCoordinator.Tab.monitor.rawValue)
                .hapticFeedback(.navigation)
                
                NavigationStack(path: $navigationCoordinator.navigationPath) {
                    SettingsTabView(webSocketService: webSocketService)
                }
                .tabItem {
                    Label(NavigationCoordinator.Tab.settings.title,
                          systemImage: NavigationCoordinator.Tab.settings.systemImage)
                }
                .tag(NavigationCoordinator.Tab.settings.rawValue)
                .hapticFeedback(.navigation)
                
                if AppConfiguration.shared.isVoiceEnabled {
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
                            
                            if let wakePhraseManager = voiceContainer.wakePhraseManager,
                               let speechService = voiceContainer.speechService {
                                VoiceStatusBadge(
                                    wakePhraseManager: wakePhraseManager,
                                    speechService: speechService
                                )
                                .offset(x: 10, y: -10)
                            }
                        }
                    }
                    .tag(NavigationCoordinator.Tab.voice.rawValue)
                    .hapticFeedback(.navigation)
                }
                
            }
            .premiumShadow(PremiumDesignSystem.Shadows.elevated)
            .animation(PremiumTransitions.easeInOut, value: navigationCoordinator.selectedTab)
            
            // Floating voice indicator (appears on all tabs except Voice tab)
            if AppConfiguration.shared.isVoiceEnabled,
               let wakePhraseManager = voiceContainer.wakePhraseManager,
               let speechService = voiceContainer.speechService,
               let permissionManager = voiceContainer.permissionManager {
                FloatingVoiceIndicator(
                    wakePhraseManager: wakePhraseManager,
                    speechService: speechService,
                    permissionManager: permissionManager,
                    webSocketService: webSocketService
                )
            }
            
            // Global voice command overlay with premium transitions
            if AppConfiguration.shared.isVoiceEnabled,
               let globalVoice = voiceContainer.globalVoice {
                if let unifiedService = unifiedVoice {
                    // Use UnifiedVoiceService for new voice interface
                    if unifiedService.state.isListening || isProcessingState(unifiedService.state) {
                        // TODO: Create UnifiedVoiceCommandView - using legacy view for now
                        GlobalVoiceCommandView(globalVoice: globalVoice)
                            .transition(PremiumTransitions.modalTransition)
                            .zIndex(999)
                    }
                } else {
                    // Fallback to legacy GlobalVoiceManager
                    if globalVoice.isVoiceCommandActive {
                        GlobalVoiceCommandView(globalVoice: globalVoice)
                            .transition(PremiumTransitions.modalTransition)
                            .zIndex(999)
                    }
                }
            }
        }                                                                                                                                                                     
        // .withGlobalErrorHandling() // TODO: Fix View extension availability issue
        .environmentObject(navigationCoordinator)
        .onAppear {
            // Initialize project manager with WebSocket service
            projectManager.configure(with: webSocketService)
            
            // Start performance monitoring
            performanceAnalytics.startPerformanceMonitoring()
            
            // Start global voice listening if voice features are enabled and permissions are available
            if AppConfiguration.shared.isVoiceEnabled,
               let permissionManager = voiceContainer.permissionManager,
               let globalVoice = voiceContainer.globalVoice,
               permissionManager.isFullyAuthorized {
                if let unifiedService = unifiedVoice {
                    Task {
                        do {
                            await unifiedService.startListening(mode: .wakeWord)
                        } catch {
                            // Critical: Graceful fallback to legacy service on error
                            print("⚠️ UnifiedVoiceService failed to start, falling back to legacy: \(error)")
                            await MainActor.run {
                                globalVoice.startGlobalVoiceListening()
                            }
                        }
                    }
                } else {
                    globalVoice.startGlobalVoiceListening()
                }
            }
            
            // Premium haptic feedback for app launch
            PremiumHaptics.contextualFeedback(for: .buttonTap)
        }
        .onDisappear {
            // Stop global voice listening when view disappears
            if AppConfiguration.shared.isVoiceEnabled,
               let globalVoice = voiceContainer.globalVoice {
                if let unifiedService = unifiedVoice {
                    unifiedService.stopListening()
                } else {
                    globalVoice.stopGlobalVoiceListening()
                }
            }
            
            // Stop performance monitoring
            performanceAnalytics.stopPerformanceMonitoring()
        }
        .onOpenURL { url in
            navigationCoordinator.handleURL(url)
        }
    }
    
    // MARK: - Helper Methods
    
    /// Check if the voice state is in processing mode
    private func isProcessingState(_ state: VoiceState) -> Bool {
        if case .processing = state {
            return true
        }
        return false
    }
}

#Preview {
    DashboardTabView()
}
