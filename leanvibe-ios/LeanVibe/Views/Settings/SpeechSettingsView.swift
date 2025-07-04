import SwiftUI

@available(iOS 18.0, macOS 14.0, *)
struct SpeechSettingsView: View {
    @ObservedObject var settingsManager: SettingsManager
    @State private var speechRate: Double = 0.5
    @State private var voicePitch: Double = 1.0
    @State private var voiceVolume: Double = 0.8
    @State private var isTestingSpeech = false
    @Environment(\.dismiss) private var dismiss
    
    init(settingsManager: SettingsManager) {
        self.settingsManager = settingsManager
    }
    
    init() {
        self.settingsManager = SettingsManager.shared
    }
    
    var body: some View {
        NavigationView {
            List {
                Section {
                    Text("Configure speech synthesis settings for voice commands and responses.")
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .padding(.vertical, 4)
                }
                
                Section("Voice Settings") {
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Text("Speech Rate")
                            Spacer()
                            Text("\(Int(speechRate * 100))%")
                                .foregroundColor(.secondary)
                        }
                        Slider(value: $speechRate, in: 0.1...2.0, step: 0.1)
                            .accentColor(Color(.systemBlue))
                    }
                    
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Text("Voice Pitch")
                            Spacer()
                            Text(String(format: "%.1f", voicePitch))
                                .foregroundColor(.secondary)
                        }
                        Slider(value: $voicePitch, in: 0.5...2.0, step: 0.1)
                            .accentColor(Color(.systemBlue))
                    }
                    
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Text("Voice Volume")
                            Spacer()
                            Text("\(Int(voiceVolume * 100))%")
                                .foregroundColor(.secondary)
                        }
                        Slider(value: $voiceVolume, in: 0.0...1.0, step: 0.1)
                            .accentColor(Color(.systemBlue))
                    }
                }
                
                Section("Voice Selection") {
                    NavigationLink(destination: VoiceSelectionView()) {
                        HStack {
                            Image(systemName: "person.wave.2")
                                .foregroundColor(Color(.systemBlue))
                            VStack(alignment: .leading) {
                                Text("Voice Type")
                                Text("Samantha (Female)")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                        }
                    }
                    
                    NavigationLink(destination: LanguageSelectionView()) {
                        HStack {
                            Image(systemName: "globe")
                                .foregroundColor(Color(.systemBlue))
                            VStack(alignment: .leading) {
                                Text("Language")
                                Text("English (US)")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                        }
                    }
                }
                
                Section("Speech Enhancement") {
                    Toggle("Enhanced Clarity", isOn: .constant(true))
                    Toggle("Background Noise Reduction", isOn: .constant(false))
                    Toggle("Punctuation Pronunciation", isOn: .constant(false))
                }
                
                Section("Test Speech") {
                    Button(action: {
                        testSpeechSettings()
                    }) {
                        HStack {
                            Image(systemName: isTestingSpeech ? "speaker.wave.3.fill" : "speaker.wave.2")
                                .foregroundColor(isTestingSpeech ? Color(.systemOrange) : Color(.systemBlue))
                            Text(isTestingSpeech ? "Speaking..." : "Test Current Settings")
                                .foregroundColor(.primary)
                        }
                    }
                    .disabled(isTestingSpeech)
                }
            }
            .navigationTitle("Speech Settings")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Done") {
                        saveSettings()
                        dismiss()
                    }
                }
            }
        }
    }
    
    private func saveSettings() {
        // Save speech settings to SettingsManager
        print("Saving speech settings:")
        print("- Speech Rate: \(speechRate)")
        print("- Voice Pitch: \(voicePitch)")
        print("- Voice Volume: \(voiceVolume)")
    }
    
    private func testSpeechSettings() {
        isTestingSpeech = true
        
        // Simulate speech testing
        DispatchQueue.main.asyncAfter(deadline: .now() + 3.0) {
            isTestingSpeech = false
        }
    }
}

// Supporting voice selection view
@available(iOS 18.0, macOS 14.0, *)
struct VoiceSelectionView: View {
    @State private var selectedVoice = "Samantha"
    private let availableVoices = [
        ("Samantha", "Female, Clear"),
        ("Alex", "Male, Warm"),
        ("Victoria", "Female, Professional"),
        ("Tom", "Male, Deep"),
        ("Karen", "Female, Friendly")
    ]
    
    var body: some View {
        List {
            Section("Available Voices") {
                ForEach(availableVoices, id: \.0) { voice in
                    Button(action: {
                        selectedVoice = voice.0
                    }) {
                        HStack {
                            VStack(alignment: .leading) {
                                Text(voice.0)
                                    .foregroundColor(.primary)
                                Text(voice.1)
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                            Spacer()
                            if selectedVoice == voice.0 {
                                Image(systemName: "checkmark")
                                    .foregroundColor(Color(.systemBlue))
                            }
                            Button(action: {
                                // Test voice
                            }) {
                                Image(systemName: "play.circle")
                                    .foregroundColor(Color(.systemBlue))
                            }
                        }
                    }
                }
            }
        }
        .navigationTitle("Voice Selection")
    }
}

// Supporting language selection view
@available(iOS 18.0, macOS 14.0, *)
struct LanguageSelectionView: View {
    @State private var selectedLanguage = "en-US"
    private let availableLanguages = [
        ("en-US", "English (United States)"),
        ("en-GB", "English (United Kingdom)"),
        ("es-ES", "Spanish (Spain)"),
        ("fr-FR", "French (France)"),
        ("de-DE", "German (Germany)")
    ]
    
    var body: some View {
        List {
            Section("Available Languages") {
                ForEach(availableLanguages, id: \.0) { language in
                    Button(action: {
                        selectedLanguage = language.0
                    }) {
                        HStack {
                            Text(language.1)
                                .foregroundColor(.primary)
                            Spacer()
                            if selectedLanguage == language.0 {
                                Image(systemName: "checkmark")
                                    .foregroundColor(Color(.systemBlue))
                            }
                        }
                    }
                }
            }
        }
        .navigationTitle("Language Selection")
    }
}

#Preview {
    SpeechSettingsView()
}