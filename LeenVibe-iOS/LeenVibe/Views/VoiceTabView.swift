import SwiftUI
import Speech

struct VoiceTabView: View {
    @ObservedObject var webSocketService: WebSocketService
    @ObservedObject var projectManager: ProjectManager
    
    @StateObject private var speechService: SpeechRecognitionService
    @StateObject private var permissionManager = VoicePermissionManager()
    @StateObject private var voiceProcessor: DashboardVoiceProcessor
    @StateObject private var wakePhraseManager: WakePhraseManager
    
    @State private var showingPermissionSheet = false
    @State private var showingVoiceModal = false
    
    init(webSocketService: WebSocketService, projectManager: ProjectManager) {
        self.webSocketService = webSocketService
        self.projectManager = projectManager
        self._speechService = StateObject(wrappedValue: SpeechRecognitionService(webSocketService: webSocketService))
        self._voiceProcessor = StateObject(wrappedValue: DashboardVoiceProcessor(projectManager: projectManager, webSocketService: webSocketService))
        self._wakePhraseManager = StateObject(wrappedValue: WakePhraseManager(
            webSocketService: webSocketService,
            projectManager: projectManager,
            voiceProcessor: DashboardVoiceProcessor(projectManager: projectManager, webSocketService: webSocketService)
        ))
    }
    
    var body: some View {
        NavigationView {
            VStack(spacing: 20) {
                // Header with voice status
                voiceStatusHeader
                
                // Voice controls section
                voiceControlsSection
                
                // Quick voice commands for project management
                quickProjectCommands
                
                // Recent voice commands history
                recentVoiceCommands
                
                Spacer()
            }
            .padding()
            .navigationTitle("Voice Commands")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: { showingPermissionSheet = true }) {
                        Image(systemName: "gear")
                    }
                }
            }
        }
        .sheet(isPresented: $showingPermissionSheet) {
            VoicePermissionSetupView(permissionManager: permissionManager)
        }
        .sheet(isPresented: $showingVoiceModal) {
            VoiceCommandView(webSocketService: webSocketService)
        }
        .onAppear {
            permissionManager.checkPermissionsStatus()
            setupWakePhraseNotifications()
        }
        .onDisappear {
            NotificationCenter.default.removeObserver(self)
        }
    }
    
    private var voiceStatusHeader: some View {
        VStack(spacing: 16) {
            // Voice availability status
            HStack {
                Circle()
                    .fill(voiceStatusColor)
                    .frame(width: 12, height: 12)
                
                Text(voiceStatusText)
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                
                Spacer()
                
                if permissionManager.isFullyAuthorized {
                    Button(action: { showingVoiceModal = true }) {
                        Image(systemName: "waveform.circle.fill")
                            .font(.title2)
                            .foregroundColor(.blue)
                    }
                }
            }
            
            // Wake phrase status
            if permissionManager.isFullyAuthorized {
                HStack {
                    Image(systemName: wakePhraseManager.isWakeListening ? "ear.fill" : "ear")
                        .foregroundColor(wakePhraseManager.isWakeListening ? .green : .gray)
                        .scaleEffect(wakePhraseManager.wakePhraseDetected ? 1.3 : 1.0)
                        .animation(.easeInOut(duration: 0.2), value: wakePhraseManager.wakePhraseDetected)
                    
                    Text(wakePhraseStatusText)
                        .font(.caption)
                        .foregroundColor(.secondary)
                    
                    Spacer()
                    
                    Button(wakePhraseManager.isWakeListening ? "Disable" : "Enable") {
                        wakePhraseManager.toggleWakeListening()
                    }
                    .font(.caption)
                    .buttonStyle(.bordered)
                    .controlSize(.small)
                }
            }
        }
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color.gray.opacity(0.1))
        )
    }
    
    private var voiceControlsSection: some View {
        VStack(spacing: 16) {
            Text("Voice Controls")
                .font(.headline)
                .frame(maxWidth: .infinity, alignment: .leading)
            
            if !permissionManager.isFullyAuthorized {
                VStack(spacing: 12) {
                    Image(systemName: "mic.slash.circle")
                        .font(.system(size: 40))
                        .foregroundColor(.orange)
                    
                    Text("Voice permissions required")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                    
                    Button("Enable Voice Commands") {
                        showingPermissionSheet = true
                    }
                    .buttonStyle(.borderedProminent)
                }
                .padding()
                .background(
                    RoundedRectangle(cornerRadius: 12)
                        .fill(Color.orange.opacity(0.1))
                )
            } else {
                HStack(spacing: 20) {
                    Button(action: { showingVoiceModal = true }) {
                        VStack(spacing: 8) {
                            Image(systemName: "mic.circle.fill")
                                .font(.system(size: 30))
                                .foregroundColor(.blue)
                            
                            Text("Start Listening")
                                .font(.caption)
                                .fontWeight(.medium)
                        }
                    }
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(
                        RoundedRectangle(cornerRadius: 12)
                            .fill(Color.blue.opacity(0.1))
                    )
                    
                    Button(action: { wakePhraseManager.toggleWakeListening() }) {
                        VStack(spacing: 8) {
                            Image(systemName: wakePhraseManager.isWakeListening ? "ear.fill" : "ear")
                                .font(.system(size: 30))
                                .foregroundColor(wakePhraseManager.isWakeListening ? .green : .gray)
                            
                            Text(wakePhraseManager.isWakeListening ? "Wake Active" : "Wake Inactive")
                                .font(.caption)
                                .fontWeight(.medium)
                        }
                    }
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(
                        RoundedRectangle(cornerRadius: 12)
                            .fill((wakePhraseManager.isWakeListening ? Color.green : Color.gray).opacity(0.1))
                    )
                }
            }
        }
    }
    
    private var quickProjectCommands: some View {
        VStack(spacing: 16) {
            Text("Quick Project Commands")
                .font(.headline)
                .frame(maxWidth: .infinity, alignment: .leading)
            
            LazyVGrid(columns: [
                GridItem(.flexible()),
                GridItem(.flexible())
            ], spacing: 12) {
                QuickCommandCard(
                    icon: "chart.line.uptrend.xyaxis",
                    title: "Project Status",
                    subtitle: "\"Show project status\"",
                    color: .blue
                )
                
                QuickCommandCard(
                    icon: "arrow.clockwise",
                    title: "Refresh Dashboard",
                    subtitle: "\"Refresh dashboard\"",
                    color: .green
                )
                
                QuickCommandCard(
                    icon: "magnifyingglass.circle",
                    title: "Analyze Project",
                    subtitle: "\"Analyze project\"",
                    color: .orange
                )
                
                QuickCommandCard(
                    icon: "list.bullet",
                    title: "List Files",
                    subtitle: "\"List files\"",
                    color: .purple
                )
            }
        }
    }
    
    private var recentVoiceCommands: some View {
        VStack(spacing: 16) {
            Text("Recent Voice Commands")
                .font(.headline)
                .frame(maxWidth: .infinity, alignment: .leading)
            
            if webSocketService.messages.filter({ $0.content.hasPrefix("🎤") }).isEmpty {
                Text("No voice commands yet")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .frame(maxWidth: .infinity, alignment: .center)
                    .padding()
            } else {
                ScrollView {
                    LazyVStack(spacing: 8) {
                        ForEach(webSocketService.messages.filter({ $0.content.hasPrefix("🎤") }).suffix(5).reversed(), id: \.id) { message in
                            VoiceCommandHistoryRow(message: message)
                        }
                    }
                }
                .frame(maxHeight: 200)
            }
        }
    }
    
    // MARK: - Computed Properties
    
    private var voiceStatusColor: Color {
        if !permissionManager.isFullyAuthorized {
            return .red
        } else if speechService.isListening {
            return .green
        } else {
            return .orange
        }
    }
    
    private var voiceStatusText: String {
        if !permissionManager.isFullyAuthorized {
            return "Voice permissions required"
        } else if speechService.isListening {
            return "Listening for commands..."
        } else {
            return "Voice commands ready"
        }
    }
    
    private var wakePhraseStatusText: String {
        if wakePhraseManager.wakePhraseDetected {
            return "Wake phrase detected!"
        } else if wakePhraseManager.isWakeListening {
            return "Wake phrase listening active"
        } else {
            return "Wake phrase listening inactive"
        }
    }
    
    // MARK: - Wake Phrase Notifications
    
    private func setupWakePhraseNotifications() {
        NotificationCenter.default.addObserver(
            forName: NSNotification.Name("WakePhraseDetected"),
            object: nil,
            queue: .main
        ) { _ in
            self.showingVoiceModal = true
        }
    }
}

struct QuickCommandCard: View {
    let icon: String
    let title: String
    let subtitle: String
    let color: Color
    
    var body: some View {
        VStack(spacing: 8) {
            Image(systemName: icon)
                .font(.system(size: 24))
                .foregroundColor(color)
            
            Text(title)
                .font(.caption)
                .fontWeight(.medium)
                .multilineTextAlignment(.center)
            
            Text(subtitle)
                .font(.caption2)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity)
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(color.opacity(0.1))
        )
    }
}

struct VoiceCommandHistoryRow: View {
    let message: AgentMessage
    
    var body: some View {
        HStack {
            Image(systemName: "mic.circle.fill")
                .foregroundColor(.blue)
                .font(.caption)
            
            Text(message.content)
                .font(.caption)
                .lineLimit(1)
            
            Spacer()
            
            Text(message.timestamp, style: .time)
                .font(.caption2)
                .foregroundColor(.secondary)
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .background(
            RoundedRectangle(cornerRadius: 8)
                .fill(Color.gray.opacity(0.1))
        )
    }
}

#Preview {
    VoiceTabView(
        webSocketService: WebSocketService(),
        projectManager: ProjectManager()
    )
}