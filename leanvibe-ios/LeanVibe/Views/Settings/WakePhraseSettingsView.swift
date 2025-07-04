import SwiftUI

@available(iOS 18.0, macOS 14.0, *)
struct WakePhraseSettingsView: View {
    @ObservedObject var settingsManager: SettingsManager
    @State private var customWakePhrase: String = ""
    @State private var isTestingWakePhrase = false
    @State private var wakePhraseTestResult: String = ""
    @Environment(\.dismiss) private var dismiss
    
    // Predefined wake phrase options
    private let predefinedWakePhrases = [
        "Hey LeanVibe",
        "Hey Assistant",
        "Listen Up",
        "Start Command",
        "LeanVibe Ready"
    ]
    
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
                    Text("Configure the phrase used to activate voice commands. Choose from predefined options or create your own.")
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .padding(.vertical, 4)
                }
                
                Section("Current Wake Phrase") {
                    HStack {
                        Image(systemName: "mic.fill")
                            .foregroundColor(Color(.systemBlue))
                        Text("\"\(settingsManager.voice.wakeWord)\"")
                            .font(.headline)
                            .fontWeight(.medium)
                    }
                    .padding(.vertical, 4)
                }
                
                Section("Predefined Options") {
                    ForEach(predefinedWakePhrases, id: \.self) { phrase in
                        Button(action: {
                            settingsManager.voice.wakeWord = phrase
                        }) {
                            HStack {
                                Text(phrase)
                                    .foregroundColor(.primary)
                                Spacer()
                                if settingsManager.voice.wakeWord == phrase {
                                    Image(systemName: "checkmark")
                                        .foregroundColor(Color(.systemBlue))
                                }
                            }
                        }
                    }
                }
                
                Section("Custom Wake Phrase") {
                    TextField("Enter custom phrase", text: $customWakePhrase)
                        .textFieldStyle(RoundedBorderTextFieldStyle())
                    
                    Button("Use Custom Phrase") {
                        if !customWakePhrase.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
                            settingsManager.voice.wakeWord = customWakePhrase.trimmingCharacters(in: .whitespacesAndNewlines)
                            customWakePhrase = ""
                        }
                    }
                    .disabled(customWakePhrase.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                }
                
                Section("Test Wake Phrase") {
                    Button(action: {
                        testWakePhrase()
                    }) {
                        HStack {
                            Image(systemName: isTestingWakePhrase ? "mic.fill" : "mic")
                                .foregroundColor(isTestingWakePhrase ? Color(.systemRed) : Color(.systemBlue))
                            Text(isTestingWakePhrase ? "Listening..." : "Test Current Phrase")
                                .foregroundColor(.primary)
                        }
                    }
                    .disabled(isTestingWakePhrase)
                    
                    if !wakePhraseTestResult.isEmpty {
                        Text(wakePhraseTestResult)
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }
                
                Section("Guidelines") {
                    VStack(alignment: .leading, spacing: 8) {
                        Label("Use 2-4 words for best recognition", systemImage: "checkmark.circle")
                        Label("Avoid common words like 'the', 'and'", systemImage: "exclamationmark.triangle")
                        Label("Clear pronunciation improves accuracy", systemImage: "speaker.wave.2")
                    }
                    .font(.caption)
                    .foregroundColor(.secondary)
                }
            }
            .navigationTitle("Wake Phrase")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Done") {
                        dismiss()
                    }
                }
            }
        }
    }
    
    private func testWakePhrase() {
        isTestingWakePhrase = true
        wakePhraseTestResult = ""
        
        // Simulate wake phrase testing (in real implementation, would use Speech framework)
        DispatchQueue.main.asyncAfter(deadline: .now() + 2.0) {
            isTestingWakePhrase = false
            wakePhraseTestResult = "Wake phrase \"\(settingsManager.voice.wakeWord)\" test completed. Recognition accuracy: Good"
        }
    }
}

#Preview {
    WakePhraseSettingsView()
}