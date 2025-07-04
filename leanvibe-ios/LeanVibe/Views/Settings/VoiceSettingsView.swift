import SwiftUI

// Temporary VoiceTestView until voice services are fully integrated
@available(iOS 18.0, macOS 14.0, *)
struct VoiceTestView: View {
    var body: some View {
        Text("Voice Test View")
            .navigationTitle("Voice Test")
    }
}

/// Comprehensive Voice Settings view for configuring the voice system built by KAPPA
/// Provides controls for wake phrase, speech recognition, voice commands, and testing
@available(iOS 18.0, macOS 14.0, *)
struct VoiceSettingsView: View {
    
    // MARK: - Properties
    
    @StateObject private var settingsManager = SettingsManager.shared
    @Bindable private var bindableSettingsManager: SettingsManager = SettingsManager.shared
    @State private var isTestingVoice = false
    @State private var showingVoiceTest = false
    @State private var showingAdvancedSettings = false
    
    // MARK: - Body
    
    var body: some View {
        List {
            // Wake Phrase Configuration
            wakePhraseSection
            
            // Speech Recognition Settings
            speechRecognitionSection
            
            // Voice Commands Configuration
            voiceCommandsSection
            
            // Audio Settings
            audioSettingsSection
            
            // Testing & Troubleshooting
            testingSection
            
            // Advanced Options
            advancedSection
        }
        .navigationTitle("Voice Settings")
        .navigationBarTitleDisplayMode(.inline)
        .sheet(isPresented: $showingVoiceTest) {
            NavigationView {
                VoiceTestView()
            }
        }
        .sheet(isPresented: $showingAdvancedSettings) {
            NavigationView {
                AdvancedVoiceSettingsView()
            }
        }
    }
    
    // MARK: - View Sections
    
    private var wakePhraseSection: some View {
        Section("Wake Phrase") {
            Toggle("Enable 'Hey LeanVibe'", isOn: $bindableSettingsManager.voice.wakePhraseEnabled)
                .onChange(of: settingsManager.voice.wakePhraseEnabled) { _, enabled in
                    handleWakePhraseToggle(enabled)
                }
            
            if settingsManager.voice.wakePhraseEnabled {
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Text("Phrase")
                        Spacer()
                        Text("\"\(settingsManager.voice.wakeWord)\"")
                            .foregroundColor(.secondary)
                            .fontWeight(.medium)
                    }
                    
                    Text("Sensitivity")
                        .font(.subheadline)
                        .fontWeight(.medium)
                    
                    HStack {
                        Text("Low")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        
                        Slider(
                            value: $bindableSettingsManager.voice.wakePhraseSensitivity,
                            in: 0.1...1.0,
                            step: 0.1
                        )
                        
                        Text("High")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    
                    Text("Higher sensitivity = more responsive but may trigger accidentally")
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .padding(.top, 4)
                }
                .padding(.vertical, 4)
                
                HStack {
                    Text("Timeout")
                    Spacer()
                    Text("\(Int(settingsManager.voice.maxRecordingDuration))s")
                        .foregroundColor(.secondary)
                }
            }
        }
    }
    
    private var speechRecognitionSection: some View {
        Section("Speech Recognition") {
            Toggle("Voice Feedback", isOn: $bindableSettingsManager.voice.voiceFeedbackEnabled)
            
            Toggle("Background Listening", isOn: $bindableSettingsManager.voice.backgroundListening)
            
            HStack {
                Text("Language")
                Spacer()
                Picker("Language", selection: $bindableSettingsManager.voice.recognitionLanguage) {
                    Text("English (US)").tag("en-US")
                    Text("English (UK)").tag("en-GB")
                    Text("English (AU)").tag("en-AU")
                    Text("English (CA)").tag("en-CA")
                }
                .pickerStyle(.menu)
            }
            
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Text("Confidence Threshold")
                    Spacer()
                    Text("\(Int(settingsManager.voice.confidenceThreshold * 100))%")
                        .foregroundColor(.secondary)
                }
                
                Slider(
                    value: $bindableSettingsManager.voice.confidenceThreshold,
                    in: 0.1...1.0,
                    step: 0.05
                )
                
                Text("Minimum confidence required for voice command recognition")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            .padding(.vertical, 4)
            
            Toggle("Auto-stop Listening", isOn: $bindableSettingsManager.voice.autoStopListening)
            
            HStack {
                Text("Max Recording Duration")
                Spacer()
                Text("\(Int(settingsManager.voice.maxRecordingDuration))s")
                    .foregroundColor(.secondary)
            }
        }
    }
    
    private var voiceCommandsSection: some View {
        Section("Voice Commands") {
            Toggle("Enable Voice Commands", isOn: $bindableSettingsManager.voice.enableVoiceCommands)
            
            if settingsManager.voice.enableVoiceCommands {
                Toggle("Command History", isOn: $bindableSettingsManager.voice.commandHistoryEnabled)
                
                HStack {
                    Text("History Items")
                    Spacer()
                    Text("\(settingsManager.voice.maxHistoryItems)")
                        .foregroundColor(.secondary)
                }
                
                Toggle("Custom Commands", isOn: $bindableSettingsManager.voice.enableCustomCommands)
                
                NavigationLink("Manage Custom Commands") {
                    CustomCommandsView()
                }
                .disabled(!settingsManager.voice.enableCustomCommands)
            }
        }
    }
    
    private var audioSettingsSection: some View {
        Section("Audio Settings") {
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Text("Microphone Gain")
                    Spacer()
                    Text("\(Int(settingsManager.voice.microphoneGain * 100))%")
                        .foregroundColor(.secondary)
                }
                
                Slider(
                    value: $bindableSettingsManager.voice.microphoneGain,
                    in: 0.1...2.0,
                    step: 0.1
                )
            }
            .padding(.vertical, 4)
            
            Toggle("Noise Reduction", isOn: $bindableSettingsManager.voice.noiseReduction)
            
            Toggle("Echo Cancellation", isOn: $bindableSettingsManager.voice.echoCanselation)
        }
    }
    
    private var testingSection: some View {
        Section("Testing & Diagnostics") {
            Button(action: { showingVoiceTest = true }) {
                SettingsRow(
                    icon: "testtube.2",
                    iconColor: .purple,
                    title: "Voice Recognition Test",
                    subtitle: "Test wake phrase and voice commands"
                )
            }
            .buttonStyle(.plain)
            .accessibilityLabel("Voice Recognition Test")
            .accessibilityHint("Opens voice testing interface")
            
            Button(action: { runVoiceCalibration() }) {
                SettingsRow(
                    icon: "tuningfork",
                    iconColor: .orange,
                    title: "Audio Calibration",
                    subtitle: isTestingVoice ? "Testing..." : "Optimize microphone settings"
                )
            }
            .buttonStyle(.plain)
            .disabled(isTestingVoice)
            .accessibilityLabel("Audio Calibration")
            .accessibilityHint("Optimizes microphone settings for better voice recognition")
            
            NavigationLink("Voice Command History") {
                VoiceHistoryView()
            }
            .disabled(!settingsManager.voice.commandHistoryEnabled)
        }
    }
    
    private var advancedSection: some View {
        Section("Advanced") {
            Button(action: { showingAdvancedSettings = true }) {
                SettingsRow(
                    icon: "gearshape.2",
                    iconColor: .gray,
                    title: "Advanced Voice Settings",
                    subtitle: "Expert configuration options"
                )
            }
            .buttonStyle(.plain)
            .accessibilityLabel("Advanced Voice Settings")
            .accessibilityHint("Opens advanced voice configuration options")
            
            Button(action: { exportVoiceSettings() }) {
                SettingsRow(
                    icon: "square.and.arrow.up",
                    iconColor: .blue,
                    title: "Export Voice Profile",
                    subtitle: "Save voice settings for backup"
                )
            }
            .buttonStyle(.plain)
            .accessibilityLabel("Export Voice Profile")
            .accessibilityHint("Saves current voice settings for backup")
            
            Button(action: { resetVoiceSettings() }) {
                SettingsRow(
                    icon: "arrow.clockwise",
                    iconColor: .red,
                    title: "Reset to Defaults",
                    subtitle: "Restore factory voice settings"
                )
            }
            .buttonStyle(.plain)
            .accessibilityLabel("Reset to Defaults")
            .accessibilityHint("Restores all voice settings to factory defaults")
        }
    }
    
    // MARK: - Actions
    
    private func handleWakePhraseToggle(_ enabled: Bool) {
        if enabled {
            // Start wake phrase detection
            requestMicrophonePermission()
        } else {
            // Stop wake phrase detection
            stopWakePhraseDetection()
        }
    }
    
    private func requestMicrophonePermission() {
        // Request microphone permission for wake phrase detection
        // Implementation would integrate with actual VoiceManager
    }
    
    private func stopWakePhraseDetection() {
        // Stop wake phrase detection
        // Implementation would integrate with actual VoiceManager
    }
    
    private func runVoiceCalibration() {
        isTestingVoice = true
        
        // Simulate voice calibration process
        DispatchQueue.main.asyncAfter(deadline: .now() + 3) {
            isTestingVoice = false
        }
    }
    
    private func exportVoiceSettings() {
        // Export voice settings as JSON or file
        // Implementation for voice profile backup
    }
    
    private func resetVoiceSettings() {
        // Reset voice settings to defaults
        settingsManager.resetSettings(VoiceSettings.self)
    }
}

// MARK: - Supporting Views

struct CustomCommandsView: View {
    var body: some View {
        Text("Custom Commands Configuration")
            .navigationTitle("Custom Commands")
    }
}

struct VoiceHistoryView: View {
    var body: some View {
        Text("Voice Command History")
            .navigationTitle("Command History")
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct AdvancedVoiceSettingsView: View {
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        Text("Advanced Voice Configuration")
            .navigationTitle("Advanced Settings")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Done") {
                        dismiss()
                    }
                }
            }
    }
}

// MARK: - Preview

#Preview {
    NavigationView {
        VoiceSettingsView()
    }
}