import SwiftUI

/// Comprehensive Voice Settings view for configuring the voice system built by KAPPA
/// Provides controls for wake phrase, speech recognition, voice commands, and testing
struct VoiceSettingsView: View {
    
    // MARK: - Properties
    
    @StateObject private var settingsManager = SettingsManager.shared
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
            VoiceTestView()
        }
        .sheet(isPresented: $showingAdvancedSettings) {
            AdvancedVoiceSettingsView()
        }
    }
    
    // MARK: - View Sections
    
    private var wakePhraseSection: some View {
        Section("Wake Phrase") {
            Toggle("Enable 'Hey LeenVibe'", isOn: $settingsManager.voiceSettings.wakePhraseEnabled)
                .onChange(of: settingsManager.voiceSettings.wakePhraseEnabled) { _, enabled in
                    handleWakePhraseToggle(enabled)
                }
            
            if settingsManager.voiceSettings.wakePhraseEnabled {
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Text("Phrase")
                        Spacer()
                        Text("\"\(settingsManager.voiceSettings.wakePhrasePhrase)\"")
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
                            value: $settingsManager.voiceSettings.wakePhraseSensitivity,
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
                    Text("\(Int(settingsManager.voiceSettings.wakePhraseTimeout))s")
                        .foregroundColor(.secondary)
                }
            }
        }
    }
    
    private var speechRecognitionSection: some View {
        Section("Speech Recognition") {
            Toggle("Voice Feedback", isOn: $settingsManager.voiceSettings.voiceFeedbackEnabled)
            
            Toggle("Background Listening", isOn: $settingsManager.voiceSettings.backgroundListening)
            
            HStack {
                Text("Language")
                Spacer()
                Picker("Language", selection: $settingsManager.voiceSettings.recognitionLanguage) {
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
                    Text("\(Int(settingsManager.voiceSettings.confidenceThreshold * 100))%")
                        .foregroundColor(.secondary)
                }
                
                Slider(
                    value: $settingsManager.voiceSettings.confidenceThreshold,
                    in: 0.1...1.0,
                    step: 0.05
                )
                
                Text("Minimum confidence required for voice command recognition")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            .padding(.vertical, 4)
            
            Toggle("Auto-stop Listening", isOn: $settingsManager.voiceSettings.autoStopListening)
            
            HStack {
                Text("Max Recording Duration")
                Spacer()
                Text("\(Int(settingsManager.voiceSettings.maxRecordingDuration))s")
                    .foregroundColor(.secondary)
            }
        }
    }
    
    private var voiceCommandsSection: some View {
        Section("Voice Commands") {
            Toggle("Enable Voice Commands", isOn: $settingsManager.voiceSettings.enableVoiceCommands)
            
            if settingsManager.voiceSettings.enableVoiceCommands {
                Toggle("Command History", isOn: $settingsManager.voiceSettings.commandHistoryEnabled)
                
                HStack {
                    Text("History Items")
                    Spacer()
                    Text("\(settingsManager.voiceSettings.maxHistoryItems)")
                        .foregroundColor(.secondary)
                }
                
                Toggle("Custom Commands", isOn: $settingsManager.voiceSettings.enableCustomCommands)
                
                NavigationLink("Manage Custom Commands") {
                    CustomCommandsView()
                }
                .disabled(!settingsManager.voiceSettings.enableCustomCommands)
            }
        }
    }
    
    private var audioSettingsSection: some View {
        Section("Audio Settings") {
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Text("Microphone Gain")
                    Spacer()
                    Text("\(Int(settingsManager.voiceSettings.microphoneGain * 100))%")
                        .foregroundColor(.secondary)
                }
                
                Slider(
                    value: $settingsManager.voiceSettings.microphoneGain,
                    in: 0.1...2.0,
                    step: 0.1
                )
            }
            .padding(.vertical, 4)
            
            Toggle("Noise Reduction", isOn: $settingsManager.voiceSettings.noiseReduction)
            
            Toggle("Echo Cancellation", isOn: $settingsManager.voiceSettings.echoCanselation)
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
            
            NavigationLink("Voice Command History") {
                VoiceHistoryView()
            }
            .disabled(!settingsManager.voiceSettings.commandHistoryEnabled)
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
            
            Button(action: { exportVoiceSettings() }) {
                SettingsRow(
                    icon: "square.and.arrow.up",
                    iconColor: .blue,
                    title: "Export Voice Profile",
                    subtitle: "Save voice settings for backup"
                )
            }
            .buttonStyle(.plain)
            
            Button(action: { resetVoiceSettings() }) {
                SettingsRow(
                    icon: "arrow.clockwise",
                    iconColor: .red,
                    title: "Reset to Defaults",
                    subtitle: "Restore factory voice settings"
                )
            }
            .buttonStyle(.plain)
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

struct VoiceTestView: View {
    @Environment(\.dismiss) private var dismiss
    @State private var isListening = false
    @State private var recognizedText = ""
    @State private var testResults: [VoiceTestResult] = []
    @State private var currentTest: VoiceTestType = .wakePhrase
    
    enum VoiceTestType: String, CaseIterable {
        case wakePhrase = "Wake Phrase"
        case speechRecognition = "Speech Recognition"
        case noiseTest = "Noise Tolerance"
        
        var instructions: String {
            switch self {
            case .wakePhrase:
                return "Say 'Hey LeenVibe' to test wake phrase detection"
            case .speechRecognition:
                return "Speak clearly to test speech recognition accuracy"
            case .noiseTest:
                return "Test recognition in noisy environments"
            }
        }
    }
    
    var body: some View {
        NavigationView {
            VStack(spacing: 24) {
                // Test Type Picker
                Picker("Test Type", selection: $currentTest) {
                    ForEach(VoiceTestType.allCases, id: \.self) { testType in
                        Text(testType.rawValue).tag(testType)
                    }
                }
                .pickerStyle(.segmented)
                
                // Instructions
                Text(currentTest.instructions)
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal)
                
                // Voice Test Interface
                VStack(spacing: 16) {
                    Button(action: toggleListening) {
                        VStack {
                            Image(systemName: isListening ? "stop.circle.fill" : "mic.circle.fill")
                                .font(.system(size: 64))
                                .foregroundColor(isListening ? .red : .blue)
                            
                            Text(isListening ? "Stop Testing" : "Start Test")
                                .font(.headline)
                        }
                    }
                    .buttonStyle(.plain)
                    
                    if isListening {
                        VoiceWaveformView()
                            .frame(height: 60)
                    }
                }
                
                // Recognition Results
                if !recognizedText.isEmpty {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Recognized:")
                            .font(.headline)
                        
                        Text(recognizedText)
                            .padding()
                            .background(Color(.systemGray6))
                            .cornerRadius(8)
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(.horizontal)
                }
                
                // Test Results
                if !testResults.isEmpty {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Recent Tests")
                            .font(.headline)
                        
                        ForEach(testResults.prefix(3)) { result in
                            HStack {
                                VStack(alignment: .leading) {
                                    Text(result.input)
                                        .fontWeight(.medium)
                                    Text("\(result.confidence, specifier: "%.1f")% confidence")
                                        .font(.caption)
                                        .foregroundColor(.secondary)
                                }
                                
                                Spacer()
                                
                                Image(systemName: result.confidence > 70 ? "checkmark.circle.fill" : "xmark.circle.fill")
                                    .foregroundColor(result.confidence > 70 ? .green : .red)
                            }
                            .padding(.vertical, 4)
                        }
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(.horizontal)
                }
                
                Spacer()
            }
            .padding()
            .navigationTitle("Voice Test")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Done") {
                        dismiss()
                    }
                }
            }
        }
    }
    
    private func toggleListening() {
        if isListening {
            stopVoiceTest()
        } else {
            startVoiceTest()
        }
    }
    
    private func startVoiceTest() {
        isListening = true
        recognizedText = ""
        
        // Simulate voice recognition
        DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
            simulateVoiceRecognition()
        }
    }
    
    private func stopVoiceTest() {
        isListening = false
    }
    
    private func simulateVoiceRecognition() {
        let testPhrases = ["Hey LeenVibe", "Create task", "Show dashboard", "Test recognition"]
        let randomPhrase = testPhrases.randomElement() ?? "Test phrase"
        let confidence = Double.random(in: 60...95)
        
        recognizedText = randomPhrase
        
        let result = VoiceTestResult(
            input: randomPhrase,
            confidence: confidence,
            timestamp: Date(),
            testType: currentTest
        )
        
        testResults.insert(result, at: 0)
        stopVoiceTest()
    }
}

struct VoiceTestResult: Identifiable {
    let id = UUID()
    let input: String
    let confidence: Double
    let timestamp: Date
    let testType: VoiceTestView.VoiceTestType
}

struct VoiceWaveformView: View {
    @State private var animationOffset: CGFloat = 0
    
    var body: some View {
        HStack(spacing: 2) {
            ForEach(0..<20, id: \.self) { _ in
                RoundedRectangle(cornerRadius: 2)
                    .fill(Color.blue)
                    .frame(width: 3)
                    .frame(height: CGFloat.random(in: 10...50))
                    .animation(
                        Animation.easeInOut(duration: Double.random(in: 0.3...0.8))
                            .repeatForever(autoreverses: true),
                        value: animationOffset
                    )
            }
        }
        .onAppear {
            animationOffset = 1
        }
    }
}

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

struct AdvancedVoiceSettingsView: View {
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
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
}

// MARK: - Preview

#Preview {
    NavigationView {
        VoiceSettingsView()
    }
}