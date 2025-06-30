import SwiftUI

@available(iOS 18.0, macOS 14.0, *)
struct GlobalVoiceCommandView: View {
    @ObservedObject var globalVoice: GlobalVoiceManager
    @State private var animationScale: CGFloat = 0.8
    @State private var pulseOpacity: Double = 0.3
    
    var body: some View {
        ZStack {
            // Background overlay
            Color.black.opacity(0.4)
                .ignoresSafeArea()
                .onTapGesture {
                    globalVoice.dismissVoiceCommand()
                }
            
            VStack(spacing: 24) {
                // Voice status header
                VStack(spacing: 8) {
                    Text("Hey LeanVibe")
                        .font(.title2)
                        .fontWeight(.semibold)
                        .foregroundColor(.white)
                    
                    Text("Listening...")
                        .font(.subheadline)
                        .foregroundColor(.white.opacity(0.8))
                }
                
                // Animated microphone icon
                ZStack {
                    // Pulse effect
                    Circle()
                        .fill(Color.blue.opacity(pulseOpacity))
                        .frame(width: 120, height: 120)
                        .scaleEffect(animationScale)
                    
                    // Microphone icon
                    Image(systemName: "mic.circle.fill")
                        .font(.system(size: 60))
                        .foregroundColor(.blue)
                        .background(Color.white)
                        .clipShape(Circle())
                        .shadow(color: .blue.opacity(0.3), radius: 8, x: 0, y: 4)
                }
                .onAppear {
                    withAnimation(.easeInOut(duration: 1.0).repeatForever(autoreverses: true)) {
                        animationScale = 1.2
                        pulseOpacity = 0.8
                    }
                }
                
                // Voice command text
                VStack(spacing: 12) {
                    if !globalVoice.voiceCommandText.isEmpty {
                        VStack(spacing: 8) {
                            Text("You said:")
                                .font(.caption)
                                .foregroundColor(.white.opacity(0.7))
                            
                            Text(globalVoice.voiceCommandText)
                                .font(.headline)
                                .foregroundColor(.white)
                                .multilineTextAlignment(.center)
                                .padding(.horizontal, 16)
                                .padding(.vertical, 8)
                                .background(Color.white.opacity(0.1))
                                .cornerRadius(8)
                        }
                    } else {
                        Text("Speak your command...")
                            .font(.subheadline)
                            .foregroundColor(.white.opacity(0.6))
                    }
                }
                
                // Cancel button
                Button(action: {
                    globalVoice.dismissVoiceCommand()
                }) {
                    HStack(spacing: 8) {
                        Image(systemName: "xmark.circle.fill")
                            .font(.title3)
                        Text("Cancel")
                            .font(.headline)
                    }
                    .foregroundColor(.white)
                    .padding(.horizontal, 24)
                    .padding(.vertical, 12)
                    .background(Color.white.opacity(0.2))
                    .cornerRadius(25)
                }
                .padding(.top, 16)
            }
            .padding(.horizontal, 32)
            .background(
                LinearGradient(
                    gradient: Gradient(colors: [
                        Color.blue.opacity(0.8),
                        Color.purple.opacity(0.8)
                    ]),
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
            )
            .cornerRadius(20)
            .padding(.horizontal, 24)
            .shadow(color: .black.opacity(0.3), radius: 12, x: 0, y: 8)
        }
        .transition(.asymmetric(
            insertion: .scale(scale: 0.8).combined(with: .opacity),
            removal: .scale(scale: 0.9).combined(with: .opacity)
        ))
        .animation(.spring(response: 0.4, dampingFraction: 0.8), value: globalVoice.isVoiceCommandActive)
    }
}

#Preview {
    ZStack {
        Color.gray.ignoresSafeArea()
        
        GlobalVoiceCommandView(globalVoice: {
            let webSocket = WebSocketService()
            let projectManager = ProjectManager()
            let globalVoice = GlobalVoiceManager(webSocketService: webSocket, projectManager: projectManager, settingsManager: SettingsManager.shared)
            globalVoice.isVoiceCommandActive = true
            globalVoice.voiceCommandText = "Show me the project status"
            return globalVoice
        }())
    }
}