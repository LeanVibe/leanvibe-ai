import SwiftUI

struct FloatingVoiceIndicator: View {
    @ObservedObject var wakePhraseManager: WakePhraseManager
    @ObservedObject var speechService: SpeechRecognitionService
    @ObservedObject var permissionManager: VoicePermissionManager
    
    @State private var isExpanded = false
    @State private var showingVoiceModal = false
    
    let webSocketService: WebSocketService
    
    var body: some View {
        VStack {
            Spacer()
            
            HStack {
                Spacer()
                
                if shouldShowIndicator {
                    voiceIndicator
                        .onTapGesture {
                            if permissionManager.isFullyAuthorized {
                                showingVoiceModal = true
                            } else {
                                withAnimation(.spring()) {
                                    isExpanded.toggle()
                                }
                            }
                        }
                        .contextMenu {
                            if permissionManager.isFullyAuthorized {
                                Button(action: {
                                    wakePhraseManager.toggleWakeListening()
                                }) {
                                    Label(
                                        wakePhraseManager.isWakeListening ? "Disable Wake Phrase" : "Enable Wake Phrase",
                                        systemImage: wakePhraseManager.isWakeListening ? "ear.slash" : "ear"
                                    )
                                }
                                
                                Button(action: {
                                    showingVoiceModal = true
                                }) {
                                    Label("Open Voice Commands", systemImage: "mic.circle")
                                }
                            } else {
                                Button("Voice permissions required") {
                                    // Could trigger permission setup
                                }
                            }
                        }
                }
            }
            .padding(.trailing, 20)
            .padding(.bottom, 20)
        }
        .sheet(isPresented: $showingVoiceModal) {
            VoiceCommandView(webSocketService: webSocketService)
        }
        .onChange(of: wakePhraseManager.wakePhraseDetected) { detected in
            if detected {
                withAnimation(.spring()) {
                    showingVoiceModal = true
                }
            }
        }
    }
    
    private var shouldShowIndicator: Bool {
        // Show indicator when voice is active or permissions available
        return permissionManager.isFullyAuthorized || 
               wakePhraseManager.isWakeListening ||
               speechService.isListening
    }
    
    @ViewBuilder
    private var voiceIndicator: some View {
        Group {
            if isExpanded && !permissionManager.isFullyAuthorized {
                expandedPermissionIndicator
            } else {
                compactVoiceIndicator
            }
        }
        .animation(.spring(response: 0.4, dampingFraction: 0.8), value: isExpanded)
    }
    
    private var compactVoiceIndicator: some View {
        ZStack {
            Circle()
                .fill(.ultraThickMaterial)
                .frame(width: 60, height: 60)
                .shadow(color: .black.opacity(0.2), radius: 8, x: 0, y: 4)
            
            // Pulsing background for active states
            if wakePhraseManager.isWakeListening || speechService.isListening {
                Circle()
                    .stroke(indicatorColor, lineWidth: 2)
                    .frame(width: 60, height: 60)
                    .scaleEffect(wakePhraseManager.wakePhraseDetected ? 1.2 : 1.0)
                    .opacity(0.8)
                    .animation(.easeInOut(duration: 1.0).repeatForever(autoreverses: true), value: wakePhraseManager.isWakeListening)
            }
            
            // Main icon
            Image(systemName: indicatorIcon)
                .font(.system(size: 24, weight: .medium))
                .foregroundColor(indicatorColor)
                .scaleEffect(speechService.isListening ? 1.1 : 1.0)
                .animation(.easeInOut(duration: 0.2), value: speechService.isListening)
            
            // Audio level visualization
            if speechService.isListening && speechService.audioLevel > 0 {
                Circle()
                    .stroke(Color.blue.opacity(0.3), lineWidth: 1)
                    .frame(width: 60 + CGFloat(speechService.audioLevel * 20), height: 60 + CGFloat(speechService.audioLevel * 20))
                    .animation(.easeOut(duration: 0.1), value: speechService.audioLevel)
            }
        }
        .accessibilityLabel("Voice Commands")
        .accessibilityHint(accessibilityHint)
    }
    
    private var expandedPermissionIndicator: some View {
        HStack(spacing: 12) {
            Image(systemName: "mic.slash.circle")
                .font(.system(size: 20))
                .foregroundColor(.orange)
            
            VStack(alignment: .leading, spacing: 2) {
                Text("Voice Permissions")
                    .font(.caption)
                    .fontWeight(.medium)
                
                Text("Tap to enable")
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 12)
        .background(.ultraThickMaterial)
        .cornerRadius(20)
        .shadow(color: .black.opacity(0.2), radius: 8, x: 0, y: 4)
    }
    
    // MARK: - Computed Properties
    
    private var indicatorIcon: String {
        if !permissionManager.isFullyAuthorized {
            return "mic.slash.circle.fill"
        } else if speechService.isListening {
            return "mic.fill"
        } else if wakePhraseManager.isWakeListening {
            return "ear.fill"
        } else {
            return "mic.circle"
        }
    }
    
    private var indicatorColor: Color {
        if !permissionManager.isFullyAuthorized {
            return .orange
        } else if speechService.isListening {
            return .red
        } else if wakePhraseManager.isWakeListening {
            return .green
        } else {
            return .blue
        }
    }
    
    private var accessibilityHint: String {
        if !permissionManager.isFullyAuthorized {
            return "Voice permissions required. Tap to enable."
        } else if speechService.isListening {
            return "Currently listening for voice commands. Tap to stop."
        } else if wakePhraseManager.isWakeListening {
            return "Wake phrase listening active. Say 'Hey LeenVibe' to start."
        } else {
            return "Tap to start voice commands."
        }
    }
}

// MARK: - Voice Status Badge for Tab Items

struct VoiceStatusBadge: View {
    @ObservedObject var wakePhraseManager: WakePhraseManager
    @ObservedObject var speechService: SpeechRecognitionService
    
    var body: some View {
        if speechService.isListening || wakePhraseManager.wakePhraseDetected {
            Circle()
                .fill(badgeColor)
                .frame(width: 8, height: 8)
                .scaleEffect(wakePhraseManager.wakePhraseDetected ? 1.5 : 1.0)
                .animation(.easeInOut(duration: 0.3), value: wakePhraseManager.wakePhraseDetected)
        }
    }
    
    private var badgeColor: Color {
        if speechService.isListening {
            return .red
        } else if wakePhraseManager.wakePhraseDetected {
            return .green
        } else {
            return .clear
        }
    }
}

#Preview {
    ZStack {
        Color.gray.opacity(0.1)
            .ignoresSafeArea()
        
        FloatingVoiceIndicator(
            wakePhraseManager: WakePhraseManager(
                webSocketService: WebSocketService(),
                projectManager: ProjectManager(),
                voiceProcessor: DashboardVoiceProcessor(
                    projectManager: ProjectManager(),
                    webSocketService: WebSocketService()
                )
            ),
            speechService: SpeechRecognitionService(webSocketService: WebSocketService()),
            permissionManager: VoicePermissionManager(),
            webSocketService: WebSocketService()
        )
    }
}