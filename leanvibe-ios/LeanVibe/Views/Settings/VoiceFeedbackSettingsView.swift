import SwiftUI
import AVFoundation

/// Settings view for Voice Feedback configuration
@available(iOS 18.0, macOS 14.0, *)
struct VoiceFeedbackSettingsView: View {
    
    // MARK: - Properties
    @ObservedObject private var voiceFeedbackService = VoiceFeedbackService.shared
    @State private var availableVoices: [AVSpeechSynthesisVoice] = []
    @State private var showingVoiceTest = false
    
    // MARK: - Body
    
    var body: some View {
        List {
            // Main toggle section
            enabledSection
            
            // Voice configuration section
            if voiceFeedbackService.isEnabled {
                voiceConfigurationSection
                
                // Audio settings section  
                audioSettingsSection
                
                // Additional options section
                additionalOptionsSection
                
                // Test section
                testSection
            }
        }
        .navigationTitle("Voice Feedback")
        .navigationBarTitleDisplayMode(.large)
        .onAppear {
            loadAvailableVoices()
        }
    }
    
    // MARK: - Sections
    
    private var enabledSection: some View {
        Section {
            HStack {
                Image(systemName: "speaker.3.fill")
                    .foregroundColor(.teal)
                    .frame(width: 24)
                
                VStack(alignment: .leading, spacing: 2) {
                    Text("Enable Voice Feedback")
                        .font(.body)
                    Text("Hear confirmations and responses")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                
                Spacer()
                
                Toggle("", isOn: $voiceFeedbackService.isEnabled)
                    .labelsHidden()
            }
        } footer: {
            Text("When enabled, LeanVibe will speak confirmations, errors, and status updates to provide audio feedback for voice commands.")
        }
    }
    
    private var voiceConfigurationSection: some View {
        Section("Voice Selection") {
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Image(systemName: "person.wave.2.fill")
                        .foregroundColor(.blue)
                        .frame(width: 24)
                    
                    Text("Voice")
                        .font(.body)
                    
                    Spacer()
                    
                    Button(action: testCurrentVoice) {
                        Image(systemName: "play.circle.fill")
                            .foregroundColor(.blue)
                    }
                    .buttonStyle(PlainButtonStyle())
                }
                
                Picker("Voice", selection: $voiceFeedbackService.preferredVoice) {
                    ForEach(availableVoices, id: \.language) { voice in
                        VStack(alignment: .leading) {
                            Text(voice.name)
                                .font(.body)
                            Text(voice.language)
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                        .tag(voice.language)
                    }
                }
                .pickerStyle(MenuPickerStyle())
            }
        } footer: {
            Text("Choose the voice that will provide audio feedback. Test different voices to find your preference.")
        }
    }
    
    private var audioSettingsSection: some View {
        Section("Audio Settings") {
            // Speech rate setting
            VStack(alignment: .leading, spacing: 12) {
                HStack {
                    Image(systemName: "speedometer")
                        .foregroundColor(.orange)
                        .frame(width: 24)
                    
                    Text("Speech Rate")
                        .font(.body)
                    
                    Spacer()
                    
                    Text(String(format: "%.1fx", voiceFeedbackService.speechRate * 2))
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                
                Slider(
                    value: $voiceFeedbackService.speechRate,
                    in: 0.1...1.0,
                    step: 0.1
                ) {
                    Text("Speech Rate")
                } minimumValueLabel: {
                    Image(systemName: "tortoise.fill")
                        .foregroundColor(.secondary)
                } maximumValueLabel: {
                    Image(systemName: "hare.fill")
                        .foregroundColor(.secondary)
                }
            }
            
            // Speech volume setting
            VStack(alignment: .leading, spacing: 12) {
                HStack {
                    Image(systemName: "speaker.wave.3.fill")
                        .foregroundColor(.green)
                        .frame(width: 24)
                    
                    Text("Speech Volume")
                        .font(.body)
                    
                    Spacer()
                    
                    Text("\(Int(voiceFeedbackService.speechVolume * 100))%")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                
                Slider(
                    value: $voiceFeedbackService.speechVolume,
                    in: 0.0...1.0,
                    step: 0.1
                ) {
                    Text("Speech Volume")
                } minimumValueLabel: {
                    Image(systemName: "speaker.fill")
                        .foregroundColor(.secondary)
                } maximumValueLabel: {
                    Image(systemName: "speaker.wave.3.fill")
                        .foregroundColor(.secondary)
                }
            }
        }
    }
    
    private var additionalOptionsSection: some View {
        Section("Additional Options") {
            // Haptic feedback toggle
            HStack {
                Image(systemName: "iphone.radiowaves.left.and.right")
                    .foregroundColor(.purple)
                    .frame(width: 24)
                
                VStack(alignment: .leading, spacing: 2) {
                    Text("Haptic Feedback")
                        .font(.body)
                    Text("Vibration with voice feedback")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                
                Spacer()
                
                Toggle("", isOn: $voiceFeedbackService.enableHapticFeedback)
                    .labelsHidden()
            }
            
            // Quiet mode toggle
            HStack {
                Image(systemName: "moon.fill")
                    .foregroundColor(.indigo)
                    .frame(width: 24)
                
                VStack(alignment: .leading, spacing: 2) {
                    Text("Quiet Mode")
                        .font(.body)
                    Text("Temporarily disable voice feedback")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                
                Spacer()
                
                Toggle("", isOn: $voiceFeedbackService.quietModeEnabled)
                    .labelsHidden()
            }
        } footer: {
            Text("Quiet mode temporarily disables voice feedback while keeping the feature enabled. Useful in quiet environments.")
        }
    }
    
    private var testSection: some View {
        Section("Testing") {
            Button(action: testVoiceFeedback) {
                HStack {
                    Image(systemName: "play.circle.fill")
                        .foregroundColor(.blue)
                        .frame(width: 24)
                    
                    Text("Test Voice Feedback")
                        .font(.body)
                        .foregroundColor(.primary)
                    
                    Spacer()
                    
                    if voiceFeedbackService.isSpeaking {
                        ProgressView()
                            .scaleEffect(0.8)
                    }
                }
            }
            .disabled(voiceFeedbackService.quietModeEnabled)
            
            Button(action: testCommandConfirmation) {
                HStack {
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundColor(.green)
                        .frame(width: 24)
                    
                    Text("Test Command Confirmation")
                        .font(.body)
                        .foregroundColor(.primary)
                    
                    Spacer()
                }
            }
            .disabled(voiceFeedbackService.quietModeEnabled)
            
            Button(action: testErrorMessage) {
                HStack {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .foregroundColor(.red)
                        .frame(width: 24)
                    
                    Text("Test Error Message")
                        .font(.body)
                        .foregroundColor(.primary)
                    
                    Spacer()
                }
            }
            .disabled(voiceFeedbackService.quietModeEnabled)
            
            if voiceFeedbackService.isSpeaking {
                Button(action: stopCurrentSpeech) {
                    HStack {
                        Image(systemName: "stop.circle.fill")
                            .foregroundColor(.red)
                            .frame(width: 24)
                        
                        Text("Stop Speaking")
                            .font(.body)
                            .foregroundColor(.red)
                        
                        Spacer()
                    }
                }
            }
        } footer: {
            if voiceFeedbackService.quietModeEnabled {
                Text("Testing is disabled while in quiet mode.")
            } else {
                Text("Test different types of voice feedback to ensure they work properly with your settings.")
            }
        }
    }
    
    // MARK: - Actions
    
    private func loadAvailableVoices() {
        availableVoices = voiceFeedbackService.getAvailableVoices()
    }
    
    private func testCurrentVoice() {
        let selectedVoice = availableVoices.first { $0.language == voiceFeedbackService.preferredVoice }
        let voiceName = selectedVoice?.name ?? "Default voice"
        voiceFeedbackService.speakResponse("This is \(voiceName) speaking", priority: .high)
    }
    
    private func testVoiceFeedback() {
        voiceFeedbackService.testVoice()
    }
    
    private func testCommandConfirmation() {
        voiceFeedbackService.confirmCommand("status", success: true)
    }
    
    private func testErrorMessage() {
        voiceFeedbackService.speakError("This is a test error message")
    }
    
    private func stopCurrentSpeech() {
        voiceFeedbackService.stopSpeaking()
    }
}

// MARK: - Preview
#if DEBUG
@available(iOS 18.0, macOS 14.0, *)
struct VoiceFeedbackSettingsView_Previews: PreviewProvider {
    static var previews: some View {
        NavigationView {
            VoiceFeedbackSettingsView()
        }
    }
}
#endif