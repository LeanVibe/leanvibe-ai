import SwiftUI
import Speech
import AVFoundation

@available(iOS 18.0, macOS 14.0, *)
struct VoicePermissionSetupView: View {
    @ObservedObject var permissionManager: VoicePermissionManager
    @Environment(\.dismiss) private var dismiss
    
    @State private var currentStep = 0
    @State private var isRequestingPermissions = false
    
    private let setupSteps = [
        "Welcome to Voice Commands",
        "Privacy Information",
        "Enable Microphone",
        "Enable Speech Recognition",
        "Setup Complete"
    ]
    
    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                // Progress indicator
                setupProgressView
                
                // Main content
                ScrollView {
                    VStack(spacing: 24) {
                        stepContent
                    }
                    .padding()
                }
                
                // Bottom controls
                bottomControlsView
            }
            .navigationTitle("Voice Setup")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Skip") {
                        dismiss()
                    }
                    .opacity(currentStep < setupSteps.count - 1 ? 1 : 0)
                }
            }
        }
        .onAppear {
            permissionManager.checkPermissionsStatus()
            updateCurrentStep()
        }
        .onChange(of: permissionManager.isFullyAuthorized) { authorized in
            if authorized && currentStep < setupSteps.count - 1 {
                currentStep = setupSteps.count - 1
            }
        }
    }
    
    private var setupProgressView: some View {
        VStack(spacing: 8) {
            HStack {
                ForEach(0..<setupSteps.count, id: \.self) { index in
                    Circle()
                        .fill(index <= currentStep ? Color.blue : Color.gray.opacity(0.3))
                        .frame(width: 8, height: 8)
                    
                    if index < setupSteps.count - 1 {
                        Rectangle()
                            .fill(index < currentStep ? Color.blue : Color.gray.opacity(0.3))
                            .frame(height: 2)
                    }
                }
            }
            .padding(.horizontal)
            
            Text(setupSteps[currentStep])
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .padding(.vertical)
        .background(Color.gray.opacity(0.05))
    }
    
    @ViewBuilder
    private var stepContent: some View {
        switch currentStep {
        case 0:
            welcomeStep
        case 1:
            privacyStep
        case 2:
            microphonePermissionStep
        case 3:
            speechRecognitionStep
        case 4:
            completionStep
        default:
            EmptyView()
        }
    }
    
    private var welcomeStep: some View {
        VStack(spacing: 24) {
            Image(systemName: "waveform.circle.fill")
                .font(.system(size: 80))
                .foregroundColor(.blue)
            
            Text("Control LeanVibe with Your Voice")
                .font(.title2)
                .fontWeight(.semibold)
                .multilineTextAlignment(.center)
            
            VStack(alignment: .leading, spacing: 16) {
                FeatureRow(
                    icon: "mic.circle.fill",
                    title: "Hands-Free Control",
                    description: "Use voice commands while coding"
                )
                
                FeatureRow(
                    icon: "shield.checkered",
                    title: "Privacy First",
                    description: "All processing happens on your device"
                )
                
                FeatureRow(
                    icon: "brain.head.profile",
                    title: "Smart Commands",
                    description: "Natural language understanding"
                )
            }
            .padding()
            .background(
                RoundedRectangle(cornerRadius: 12)
                    .fill(Color.blue.opacity(0.05))
            )
        }
    }
    
    private var privacyStep: some View {
        VStack(spacing: 24) {
            Image(systemName: "hand.raised.circle.fill")
                .font(.system(size: 60))
                .foregroundColor(.green)
            
            Text("Your Privacy Matters")
                .font(.title2)
                .fontWeight(.semibold)
            
            VStack(alignment: .leading, spacing: 12) {
                PrivacyPoint(
                    icon: "iphone",
                    text: "Speech recognition runs entirely on your iPhone"
                )
                
                PrivacyPoint(
                    icon: "mic.slash",
                    text: "Voice recordings are never stored or shared"
                )
                
                PrivacyPoint(
                    icon: "network.slash",
                    text: "No voice data is sent to external servers"
                )
                
                PrivacyPoint(
                    icon: "text.bubble",
                    text: "Only text commands are sent to your Mac agent"
                )
            }
            
            Text(permissionManager.privacyDescription)
                .font(.caption)
                .foregroundColor(.secondary)
                .padding()
                .background(Color.gray.opacity(0.1))
                .cornerRadius(8)
        }
    }
    
    private var microphonePermissionStep: some View {
        VStack(spacing: 24) {
            Image(systemName: microphoneStepIcon)
                .font(.system(size: 60))
                .foregroundColor(microphoneStepColor)
            
            Text("Microphone Access")
                .font(.title2)
                .fontWeight(.semibold)
            
            Text("LeanVibe needs microphone access to hear your voice commands.")
                .font(.body)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
            
            VStack(spacing: 12) {
                HStack {
                    Text("Status:")
                    Spacer()
                    Text(permissionManager.microphoneAuthorizationStatus.description)
                        .fontWeight(.medium)
                        .foregroundColor(microphoneStatusColor)
                }
                .padding()
                .background(Color.gray.opacity(0.1))
                .cornerRadius(8)
                
                if permissionManager.microphoneAuthorizationStatus == .denied {
                    Button("Open Settings") {
                        permissionManager.openAppSettings()
                    }
                    .buttonStyle(.bordered)
                }
            }
        }
    }
    
    private var speechRecognitionStep: some View {
        VStack(spacing: 24) {
            Image(systemName: speechStepIcon)
                .font(.system(size: 60))
                .foregroundColor(speechStepColor)
            
            Text("Speech Recognition")
                .font(.title2)
                .fontWeight(.semibold)
            
            Text("Enable speech recognition to convert your voice to text commands.")
                .font(.body)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
            
            VStack(spacing: 12) {
                HStack {
                    Text("Status:")
                    Spacer()
                    Text(permissionManager.speechAuthorizationStatus.description)
                        .fontWeight(.medium)
                        .foregroundColor(speechStatusColor)
                }
                .padding()
                .background(Color.gray.opacity(0.1))
                .cornerRadius(8)
                
                if permissionManager.speechAuthorizationStatus == .denied {
                    Button("Open Settings") {
                        permissionManager.openAppSettings()
                    }
                    .buttonStyle(.bordered)
                }
            }
        }
    }
    
    private var completionStep: some View {
        VStack(spacing: 24) {
            Image(systemName: "checkmark.circle.fill")
                .font(.system(size: 80))
                .foregroundColor(.green)
            
            Text("Voice Commands Ready!")
                .font(.title2)
                .fontWeight(.semibold)
            
            Text("You can now use voice commands to control LeanVibe. Try saying:")
                .font(.body)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
            
            VStack(alignment: .leading, spacing: 12) {
                ExampleCommand(command: "Hey LeanVibe, show status")
                ExampleCommand(command: "List files")
                ExampleCommand(command: "Show help")
            }
            .padding()
            .background(Color.green.opacity(0.1))
            .cornerRadius(12)
            
            Text("Access voice commands from the microphone button in the main interface.")
                .font(.caption)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
        }
    }
    
    private var bottomControlsView: some View {
        VStack(spacing: 12) {
            if currentStep < setupSteps.count - 1 {
                Button(action: nextStep) {
                    HStack {
                        if isRequestingPermissions {
                            ProgressView()
                                .scaleEffect(0.8)
                        }
                        Text(nextButtonTitle)
                    }
                    .frame(maxWidth: .infinity)
                }
                .buttonStyle(.borderedProminent)
                .controlSize(.large)
                .disabled(isRequestingPermissions || !canProceedToNextStep)
                
                if currentStep > 0 {
                    Button("Previous") {
                        previousStep()
                    }
                    .buttonStyle(.bordered)
                }
            } else {
                Button("Start Using Voice Commands") {
                    dismiss()
                }
                .buttonStyle(.borderedProminent)
                .controlSize(.large)
            }
        }
        .padding()
    }
    
    // MARK: - Step Logic
    
    private func updateCurrentStep() {
        if permissionManager.isFullyAuthorized {
            currentStep = setupSteps.count - 1
        } else if permissionManager.speechAuthorizationStatus.isGranted {
            currentStep = 3
        } else if permissionManager.microphoneAuthorizationStatus == .granted {
            currentStep = 2
        }
    }
    
    private func nextStep() {
        switch currentStep {
        case 0, 1:
            currentStep += 1
        case 2:
            requestMicrophonePermission()
        case 3:
            requestSpeechPermission()
        default:
            break
        }
    }
    
    private func previousStep() {
        if currentStep > 0 {
            currentStep -= 1
        }
    }
    
    private func requestMicrophonePermission() {
        isRequestingPermissions = true
        
        Task {
            permissionManager.requestFullPermissions { _ in }
            
            await MainActor.run {
                isRequestingPermissions = false
                if permissionManager.microphoneAuthorizationStatus == .granted {
                    currentStep += 1
                }
            }
        }
    }
    
    private func requestSpeechPermission() {
        isRequestingPermissions = true
        
        Task {
            permissionManager.requestFullPermissions { _ in }
            
            await MainActor.run {
                isRequestingPermissions = false
                if permissionManager.isFullyAuthorized {
                    currentStep += 1
                }
            }
        }
    }
    
    // MARK: - Computed Properties
    
    private var canProceedToNextStep: Bool {
        switch currentStep {
        case 0, 1:
            return true
        case 2:
            return permissionManager.microphoneAuthorizationStatus != .denied
        case 3:
            return permissionManager.speechAuthorizationStatus != .denied
        default:
            return false
        }
    }
    
    private var nextButtonTitle: String {
        switch currentStep {
        case 0:
            return "Get Started"
        case 1:
            return "Continue"
        case 2:
            return "Enable Microphone"
        case 3:
            return "Enable Speech Recognition"
        default:
            return "Next"
        }
    }
    
    private var microphoneStepIcon: String {
        switch permissionManager.microphoneAuthorizationStatus {
        case .granted:
            return "mic.circle.fill"
        case .denied:
            return "mic.slash.circle.fill"
        default:
            return "mic.circle"
        }
    }
    
    private var microphoneStepColor: Color {
        switch permissionManager.microphoneAuthorizationStatus {
        case .granted:
            return .green
        case .denied:
            return .red
        default:
            return .blue
        }
    }
    
    private var microphoneStatusColor: Color {
        switch permissionManager.microphoneAuthorizationStatus {
        case .granted:
            return .green
        case .denied:
            return .red
        default:
            return .orange
        }
    }
    
    private var speechStepIcon: String {
        switch permissionManager.speechAuthorizationStatus {
        case .authorized:
            return "waveform.circle.fill"
        case .denied, .restricted:
            return "waveform.slash"
        default:
            return "waveform.circle"
        }
    }
    
    private var speechStepColor: Color {
        switch permissionManager.speechAuthorizationStatus {
        case .authorized:
            return .green
        case .denied, .restricted:
            return .red
        default:
            return .blue
        }
    }
    
    private var speechStatusColor: Color {
        switch permissionManager.speechAuthorizationStatus {
        case .authorized:
            return .green
        case .denied, .restricted:
            return .red
        default:
            return .orange
        }
    }
}

// MARK: - Supporting Views

struct FeatureRow: View {
    let icon: String
    let title: String
    let description: String
    
    var body: some View {
        HStack(spacing: 16) {
            Image(systemName: icon)
                .font(.title2)
                .foregroundColor(.blue)
                .frame(width: 30)
            
            VStack(alignment: .leading, spacing: 4) {
                Text(title)
                    .font(.subheadline)
                    .fontWeight(.medium)
                
                Text(description)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
        }
    }
}

struct PrivacyPoint: View {
    let icon: String
    let text: String
    
    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .foregroundColor(.green)
                .frame(width: 20)
            
            Text(text)
                .font(.subheadline)
            
            Spacer()
        }
    }
}

struct ExampleCommand: View {
    let command: String
    
    var body: some View {
        HStack {
            Image(systemName: "quote.bubble")
                .foregroundColor(.green)
            
            Text(command)
                .font(.subheadline)
                .fontWeight(.medium)
            
            Spacer()
        }
    }
}

#Preview {
    VoicePermissionSetupView(permissionManager: VoicePermissionManager())
}