import SwiftUI
import Speech

@available(iOS 18.0, macOS 14.0, *)
struct VoiceCommandView: View {
    @StateObject private var speechService: SpeechRecognitionService
    @StateObject private var permissionManager = VoicePermissionManager()
    @Environment(\.presentationMode) private var presentationMode
    
    private let webSocketService: WebSocketService
    private let settingsManager: SettingsManager
    
    @State private var showingPermissionSheet = false
    @State private var voiceCommand: VoiceCommand?
    @State private var showingCommandConfirmation = false
    
    init(webSocketService: WebSocketService, settingsManager: SettingsManager) {
        self.webSocketService = webSocketService
        self.settingsManager = settingsManager
        self._speechService = StateObject(wrappedValue: SpeechRecognitionService())
    }
    
    var body: some View {
        ZStack {
            // Background blur
            Color.black.opacity(0.4)
                .edgesIgnoringSafeArea(.all)
                .onTapGesture {
                    presentationMode.wrappedValue.dismiss()
                }
            
            // Main voice interface
            VStack(spacing: 0) {
                // Header
                voiceHeaderSection
                
                // Main content
                if !permissionManager.isFullyAuthorized {
                    permissionRequiredView
                } else {
                    voiceInterfaceView
                }
                
                // Footer controls
                voiceControlsSection
            }
            .background(
                RoundedRectangle(cornerRadius: 20)
                    .fill(Color.white.opacity(0.95))
                    .shadow(radius: 20)
            )
            .padding()
        }
        .sheet(isPresented: $showingPermissionSheet) {
            VoicePermissionSetupView(permissionManager: permissionManager)
        }
        .sheet(isPresented: $showingCommandConfirmation) {
            if let command = voiceCommand {
                VoiceCommandConfirmationView(
                    command: command,
                    onConfirm: { confirmCommand(command) },
                    onCancel: { voiceCommand = nil }
                )
            }
        }
        .onAppear {
            permissionManager.checkPermissionsStatus()
        }
        .onChange(of: speechService.recognitionState) { state in
            if case .completed = state {
                processCompletedRecognition()
            }
        }
    }
    
    private var voiceHeaderSection: some View {
        VStack(spacing: 8) {
            HStack {
                Image(systemName: "waveform.circle.fill")
                    .font(.title2)
                    .foregroundColor(.blue)
                
                Text("Voice Commands")
                    .font(.headline)
                    .fontWeight(.semibold)
                
                Spacer()
                
                Button(action: { presentationMode.wrappedValue.dismiss() }) {
                    Image(systemName: "xmark.circle.fill")
                        .font(.title2)
                        .foregroundColor(.secondary)
                }
            }
            
            Text(recognitionStateDescription)
                .font(.subheadline)
                .foregroundColor(.secondary)
        }
        .padding()
    }
    
    private var permissionRequiredView: some View {
        VStack(spacing: 20) {
            Image(systemName: "mic.slash.circle")
                .font(.system(size: 60))
                .foregroundColor(.orange)
            
            Text("Voice Permissions Needed")
                .font(.title2)
                .fontWeight(.semibold)
            
            Text(permissionStatusDescription)
                .font(.body)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
            
            Button("Enable Voice Commands") {
                showingPermissionSheet = true
            }
            .buttonStyle(.borderedProminent)
            .controlSize(.large)
        }
        .padding()
    }
    
    private var voiceInterfaceView: some View {
        VStack(spacing: 24) {
            // Waveform visualization
            VoiceWaveformView(
                audioLevel: speechService.audioLevel,
                isListening: speechService.isListening,
                recognitionState: speechService.recognitionState
            )
            .frame(height: 120)
            
            // Transcription display
            transcriptionSection
            
            // Quick commands
            if !speechService.isListening {
                quickCommandsSection
            }
        }
        .padding()
    }
    
    private var transcriptionSection: some View {
        VStack(spacing: 8) {
            if !speechService.recognizedText.isEmpty {
                VStack(alignment: .leading, spacing: 8) {
                    Text("You said:")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    
                    Text(speechService.recognizedText)
                        .font(.body)
                        .padding()
                        .background(
                            RoundedRectangle(cornerRadius: 8)
                                .fill(Color.blue.opacity(0.1))
                        )
                        .animation(.easeInOut, value: speechService.recognizedText)
                }
            } else if speechService.isListening {
                Text("Listening...")
                    .font(.body)
                    .foregroundColor(.secondary)
                    .padding()
            } else {
                Text("Tap the microphone to start")
                    .font(.body)
                    .foregroundColor(.secondary)
                    .padding()
            }
        }
        .frame(minHeight: 60)
    }
    
    private var quickCommandsSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Try saying:")
                .font(.caption)
                .fontWeight(.medium)
                .foregroundColor(.secondary)
            
            LazyVStack(alignment: .leading, spacing: 8) {
                QuickVoiceCommand(
                    phrase: "Hey LeanVibe, show status",
                    description: "Check agent status",
                    icon: "checkmark.circle"
                )
                
                QuickVoiceCommand(
                    phrase: "List files",
                    description: "Show current directory files",
                    icon: "doc.text"
                )
                
                QuickVoiceCommand(
                    phrase: "Show help",
                    description: "Display available commands",
                    icon: "questionmark.circle"
                )
            }
        }
        .padding(.horizontal)
    }
    
    private var voiceControlsSection: some View {
        HStack(spacing: 24) {
            // Settings button
            Button(action: { showingPermissionSheet = true }) {
                VStack(spacing: 4) {
                    Image(systemName: "gear")
                        .font(.title2)
                    Text("Settings")
                        .font(.caption)
                }
            }
            .foregroundColor(.secondary)
            
            Spacer()
            
            // Main microphone button
            Button(action: { toggleListening() }) {
                ZStack {
                    Circle()
                        .fill(microphoneButtonColor)
                        .frame(width: 80, height: 80)
                        .scaleEffect(speechService.isListening ? 1.1 : 1.0)
                        .animation(.easeInOut(duration: 0.2), value: speechService.isListening)
                    
                    Image(systemName: microphoneIconName)
                        .font(.title)
                        .foregroundColor(.white)
                }
            }
            .disabled(!(permissionManager.isFullyAuthorized && !speechService.isListening))
            .buttonStyle(DefaultButtonStyle())
            
            Spacer()
            
            // Help button
            Button(action: { /* Show help */ }) {
                VStack(spacing: 4) {
                    Image(systemName: "questionmark.circle")
                        .font(.title2)
                    Text("Help")
                        .font(.caption)
                }
            }
            .foregroundColor(.secondary)
        }
        .padding()
    }
    
    private var microphoneButtonColor: Color {
        if !(permissionManager.isFullyAuthorized && !speechService.isListening) {
            return .gray
        } else if speechService.isListening {
            return .red
        } else {
            return .blue
        }
    }
    
    private var microphoneIconName: String {
        if speechService.isListening {
            return "stop.fill"
        } else {
            return "mic.fill"
        }
    }
    
    private func processCompletedRecognition() {
        guard !speechService.recognizedText.isEmpty else { return }
        
        // TODO: Fix VoiceSettings import issue
        let processor = VoiceCommandProcessor() // (settings: settingsManager.voice)
        let command = processor.processVoiceInput(speechService.recognizedText)
        
        if command.requiresConfirmation {
            voiceCommand = command
            showingCommandConfirmation = true
        } else {
            executeCommand(command)
        }
    }
    
    private func confirmCommand(_ command: VoiceCommand) {
        voiceCommand = nil
        executeCommand(command)
    }
    
    private func executeCommand(_ command: VoiceCommand) {
        // Send to WebSocket service
        let voiceMessage = VoiceCommandMessage(
            voiceCommand: command,
            clientId: "ios-voice-client"
        )
        
        do {
            let data = try JSONEncoder().encode(voiceMessage)
            let jsonString = String(data: data, encoding: .utf8) ?? ""
            webSocketService.sendMessage(jsonString, type: "voice_command")
            
            // Also send the processed command directly
            webSocketService.sendMessage(command.processedCommand, type: "voice_command")
            
        } catch {
            print("Failed to encode voice command: \(error)")
            // Fallback to simple command
            webSocketService.sendMessage(command.processedCommand, type: "voice_command")
        }
        
        // Close voice interface after successful command
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            presentationMode.wrappedValue.dismiss()
        }
    }
    
    private var recognitionStateDescription: String {
        switch speechService.recognitionState {
        case .idle: return "Idle"
        case .listening: return "Listening..."
        case .processing: return "Processing..."
        case .completed: return "Completed"
        case .error(let message): return "Error: \(message)"
        }
    }
    
    private var permissionStatusDescription: String {
        switch permissionManager.permissionStatus {
        case .notDetermined:
            return "Permissions not determined."
        case .granted:
            return "All permissions granted."
        case .denied:
            return "Permissions denied. Please enable in Settings."
        case .restricted:
            return "Permissions restricted."
        }
    }
    
    private func toggleListening() {
        if speechService.isListening {
            DispatchQueue.main.async {
                speechService.stopListening()
            }
        } else {
            DispatchQueue.main.async {
                speechService.startListening()
            }
        }
    }
}

struct QuickVoiceCommand: View {
    let phrase: String
    let description: String
    let icon: String
    
    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .foregroundColor(.blue)
                .frame(width: 20)
            
            VStack(alignment: .leading, spacing: 2) {
                Text(phrase)
                    .font(.subheadline)
                    .fontWeight(.medium)
                
                Text(description)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
        }
        .padding(.vertical, 4)
    }
}

struct VoiceCommandConfirmationView: View {
    let command: VoiceCommand
    let onConfirm: () -> Void
    let onCancel: () -> Void
    
    var body: some View {
        NavigationStack {
            VStack(spacing: 24) {
                VStack(spacing: 16) {
                    Image(systemName: "questionmark.circle.fill")
                        .font(.system(size: 50))
                        .foregroundColor(.orange)
                    
                    Text("Confirm Voice Command")
                        .font(.title2)
                        .fontWeight(.semibold)
                    
                    VStack(alignment: .leading, spacing: 8) {
                        Text("You said:")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        
                        Text(command.originalText)
                            .font(.body)
                            .padding()
                            .background(
                                RoundedRectangle(cornerRadius: 8)
                                    .fill(Color.gray.opacity(0.1))
                            )
                        
                        Text("Will execute:")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        
                        Text(command.processedCommand)
                            .font(.body)
                            .fontWeight(.medium)
                            .padding()
                            .background(
                                RoundedRectangle(cornerRadius: 8)
                                    .fill(Color.blue.opacity(0.1))
                            )
                        
                        HStack {
                            Text("Confidence:")
                            Spacer()
                            Text("\(Int(command.confidence * 100))%")
                                .fontWeight(.medium)
                                .foregroundColor(command.isHighConfidence ? .green : .orange)
                        }
                        .font(.caption)
                        .foregroundColor(.secondary)
                    }
                }
                
                Spacer()
                
                VStack(spacing: 12) {
                    Button("Execute Command") {
                        onConfirm()
                    }
                    .buttonStyle(DefaultButtonStyle())
                    .controlSize(.large)
                    
                    Button("Cancel") {
                        onCancel()
                    }
                    .buttonStyle(DefaultButtonStyle())
                }
            }
            .padding()
            .navigationTitle("Confirm Command")
#if os(iOS)
            .navigationBarTitleDisplayMode(.inline)
#endif
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Cancel") {
                        onCancel()
                    }
                }
            }
        }
    }
}

#Preview {
    VoiceCommandView(webSocketService: WebSocketService(), settingsManager: SettingsManager.shared)
}
