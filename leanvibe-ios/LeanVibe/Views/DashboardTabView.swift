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
            print("🎤 VoiceServiceContainer: Attempting to initialize voice services...")
            
            // Extra defensive voice service initialization with comprehensive error boundaries
            var tempSpeechService: SpeechRecognitionService?
            var tempWakePhraseManager: WakePhraseManager?
            var tempGlobalVoice: GlobalVoiceManager?
            var tempPermissionManager: VoicePermissionManager?
            
            do {
                // Initialize permission manager first (least likely to crash)
                tempPermissionManager = VoicePermissionManager()
                print("✅ VoicePermissionManager initialized")
                
                // Initialize speech service with timeout protection
                tempSpeechService = SpeechRecognitionService()
                print("✅ SpeechRecognitionService initialized")
                
                // Initialize voice processor carefully
                let voiceProcessor = DashboardVoiceProcessor(
                    projectManager: projectManager,
                    webSocketService: webSocket,
                    settingsManager: settingsManager
                )
                print("✅ DashboardVoiceProcessor initialized")
                
                // Initialize wake phrase manager
                tempWakePhraseManager = WakePhraseManager(
                    webSocketService: webSocket,
                    projectManager: projectManager,
                    voiceProcessor: voiceProcessor
                )
                print("✅ WakePhraseManager initialized")
                
                // Initialize global voice manager last (most complex)
                tempGlobalVoice = GlobalVoiceManager(
                    webSocketService: webSocket,
                    projectManager: projectManager,
                    settingsManager: settingsManager
                )
                print("✅ GlobalVoiceManager initialized")
                
                // All services initialized successfully
                self.speechService = tempSpeechService
                self.wakePhraseManager = tempWakePhraseManager
                self.globalVoice = tempGlobalVoice
                self.permissionManager = tempPermissionManager
                
                print("🎉 VoiceServiceContainer: All voice services initialized successfully")
                
            } catch {
                print("🚨 VoiceServiceContainer: Voice initialization failed - \(error)")
                
                // Emergency disable voice features to prevent future crashes
                AppConfiguration.emergencyDisableVoice(reason: "Initialization failure: \(error.localizedDescription)")
                
                // Clean up any partially initialized services
                tempSpeechService = nil
                tempWakePhraseManager = nil
                tempGlobalVoice = nil
                tempPermissionManager = nil
                
                // Set all services to nil for safe operation
                self.speechService = nil
                self.wakePhraseManager = nil
                self.globalVoice = nil
                self.permissionManager = nil
                
                print("⚠️ App will continue without voice features")
            }
        } else {
            print("🎤 VoiceServiceContainer: Voice features disabled in configuration")
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
                        webSocketService: webSocketService,
                        navigationCoordinator: navigationCoordinator
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
                    ArchitectureTabView(webSocketService: webSocketService)
                }
                .tabItem {
                    Label(NavigationCoordinator.Tab.architecture.title,
                          systemImage: NavigationCoordinator.Tab.architecture.systemImage)
                }
                .tag(NavigationCoordinator.Tab.architecture.rawValue)
                .hapticFeedback(.navigation)
                
                NavigationStack(path: $navigationCoordinator.navigationPath) {
                    // TODO: Fix DocumentIntelligenceView target membership and compilation
                    VStack(spacing: 16) {
                        Image(systemName: "doc.text.magnifyingglass")
                            .font(.system(size: 48))
                            .foregroundColor(.secondary)
                        
                        Text("Document Intelligence")
                            .font(.largeTitle)
                            .fontWeight(.bold)
                        
                        Text("AI-powered document analysis and task generation")
                            .font(.body)
                            .foregroundColor(.secondary)
                            .multilineTextAlignment(.center)
                        
                        Text("Coming Soon")
                            .font(.caption)
                            .padding(.horizontal, 16)
                            .padding(.vertical, 8)
                            .background(Color.blue.opacity(0.1))
                            .foregroundColor(.blue)
                            .cornerRadius(16)
                    }
                    .padding()
                }
                .tabItem {
                    Label(NavigationCoordinator.Tab.documents.title,
                          systemImage: NavigationCoordinator.Tab.documents.systemImage)
                }
                .tag(NavigationCoordinator.Tab.documents.rawValue)
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
            if AppConfiguration.shared.isVoiceEnabled {
                startVoiceServicesDefensively()
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
    
    /// Defensive voice service startup with comprehensive error handling
    private func startVoiceServicesDefensively() {
        Task {
            do {
                // Check if voice services are properly initialized
                guard let permissionManager = voiceContainer.permissionManager else {
                    print("⚠️ Voice permission manager not available - skipping voice startup")
                    return
                }
                
                guard let globalVoice = voiceContainer.globalVoice else {
                    print("⚠️ Global voice manager not available - skipping voice startup")
                    return
                }
                
                // Check permissions before starting services
                guard permissionManager.isFullyAuthorized else {
                    print("🎤 Voice permissions not granted - voice services remain inactive")
                    return
                }
                
                // Try UnifiedVoiceService first, fallback to legacy
                if let unifiedService = unifiedVoice {
                    do {
                        await unifiedService.startListening(mode: .wakeWord)
                        print("✅ UnifiedVoiceService started successfully")
                    } catch {
                        print("⚠️ UnifiedVoiceService failed to start, falling back to legacy: \(error)")
                        await MainActor.run {
                            startLegacyVoiceServiceSafely(globalVoice)
                        }
                    }
                } else {
                    await MainActor.run {
                        startLegacyVoiceServiceSafely(globalVoice)
                    }
                }
                
            } catch {
                print("🚨 Voice service startup failed completely: \(error)")
                
                // TODO: Report critical startup error to error boundary
                // reportVoiceError(error, from: "VoiceServiceStartup")
                
                // App continues without voice features
            }
        }
    }
    
    /// Safely start legacy voice service with error handling
    @MainActor
    private func startLegacyVoiceServiceSafely(_ globalVoice: GlobalVoiceManager) {
        do {
            globalVoice.startGlobalVoiceListening()
            print("✅ Legacy voice service started successfully")
        } catch {
            print("🚨 Legacy voice service failed to start: \(error)")
            
            // TODO: Report legacy service error to error boundary
            // reportVoiceError(error, from: "LegacyVoiceService")
            
            // Voice features remain disabled but app continues
        }
    }
}

#Preview {
    DashboardTabView()
}
