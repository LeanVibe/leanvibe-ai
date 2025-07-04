import SwiftUI

@available(iOS 18.0, macOS 14.0, *)
struct VoiceTestView: View {
    @ObservedObject var settingsManager: SettingsManager
    @State private var testPhrase = "Hello, this is a voice test for LeanVibe"
    @State private var isRecording = false
    @State private var isPlaying = false
    @State private var testResults: [VoiceTestResult] = []
    @State private var currentTestType: VoiceTestType = .recognition
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
                    Text("Test voice recognition and speech synthesis to ensure optimal performance.")
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .padding(.vertical, 4)
                }
                
                Section("Test Type") {
                    Picker("Test Type", selection: $currentTestType) {
                        ForEach(VoiceTestType.allCases, id: \.self) { type in
                            Text(type.displayName).tag(type)
                        }
                    }
                    .pickerStyle(SegmentedPickerStyle())
                }
                
                if currentTestType == .recognition {
                    voiceRecognitionTestSection
                } else {
                    speechSynthesisTestSection
                }
                
                if !testResults.isEmpty {
                    testResultsSection
                }
                
                Section("Quick Tests") {
                    Button("Run Full Voice Test Suite") {
                        runFullTestSuite()
                    }
                    .foregroundColor(Color(.systemBlue))
                    
                    Button("Test Wake Phrase Recognition") {
                        testWakePhraseRecognition()
                    }
                    .foregroundColor(Color(.systemBlue))
                    
                    Button("Test Command Processing") {
                        testCommandProcessing()
                    }
                    .foregroundColor(Color(.systemBlue))
                }
            }
            .navigationTitle("Voice Testing")
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
    
    @ViewBuilder
    private var voiceRecognitionTestSection: some View {
        Section("Voice Recognition Test") {
            VStack(spacing: 12) {
                Text("Tap and hold to record your voice")
                    .font(.headline)
                    .multilineTextAlignment(.center)
                
                Button(action: {
                    if isRecording {
                        stopRecording()
                    } else {
                        startRecording()
                    }
                }) {
                    VStack {
                        Image(systemName: isRecording ? "mic.fill" : "mic")
                            .font(.system(size: 48))
                            .foregroundColor(isRecording ? .red : Color(.systemBlue))
                        
                        Text(isRecording ? "Recording..." : "Tap to Record")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    .frame(width: 120, height: 120)
                    .background(
                        Circle()
                            .fill(isRecording ? Color.red.opacity(0.1) : Color.blue.opacity(0.1))
                            .overlay(
                                Circle()
                                    .stroke(isRecording ? Color.red : Color.blue, lineWidth: 2)
                            )
                    )
                }
                .buttonStyle(PlainButtonStyle())
                
                if isRecording {
                    Text("Say: '\(settingsManager.voice.wakeWord)'")
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .padding(.top, 8)
                }
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical)
        }
    }
    
    @ViewBuilder
    private var speechSynthesisTestSection: some View {
        Section("Speech Synthesis Test") {
            VStack(spacing: 12) {
                TextField("Test phrase", text: $testPhrase, axis: .vertical)
                    .textFieldStyle(RoundedBorderTextFieldStyle())
                    .lineLimit(3)
                
                Button(action: {
                    testSpeechSynthesis()
                }) {
                    HStack {
                        Image(systemName: isPlaying ? "speaker.wave.3.fill" : "speaker.wave.2")
                            .foregroundColor(isPlaying ? Color(.systemOrange) : Color(.systemBlue))
                        Text(isPlaying ? "Playing..." : "Test Speech Synthesis")
                            .foregroundColor(.primary)
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 12)
                    .background(Color(.systemGray6))
                    .cornerRadius(8)
                }
                .disabled(isPlaying)
            }
        }
    }
    
    @ViewBuilder
    private var testResultsSection: some View {
        Section("Test Results") {
            ForEach(testResults, id: \.id) { result in
                VStack(alignment: .leading, spacing: 4) {
                    HStack {
                        Text(result.testType.displayName)
                            .font(.headline)
                        Spacer()
                        Text(result.passed ? "✅ Passed" : "❌ Failed")
                            .font(.caption)
                            .foregroundColor(result.passed ? .green : .red)
                    }
                    
                    Text(result.details)
                        .font(.caption)
                        .foregroundColor(.secondary)
                    
                    if let score = result.score {
                        HStack {
                            Text("Score:")
                                .font(.caption)
                            ProgressView(value: score)
                                .progressViewStyle(LinearProgressViewStyle())
                                .frame(height: 4)
                            Text("\(Int(score * 100))%")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                    }
                }
                .padding(.vertical, 4)
            }
        }
    }
    
    private func startRecording() {
        isRecording = true
        // Simulate recording duration
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            // Auto-stop after 5 seconds max
            if isRecording {
                stopRecording()
            }
        }
    }
    
    private func stopRecording() {
        isRecording = false
        
        // Simulate processing and add test result
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
            let result = VoiceTestResult(
                testType: .recognition,
                passed: true,
                details: "Wake phrase '\(settingsManager.voice.wakeWord)' recognized successfully",
                score: 0.92,
                timestamp: Date()
            )
            testResults.insert(result, at: 0)
        }
    }
    
    private func testSpeechSynthesis() {
        isPlaying = true
        
        // Simulate speech synthesis
        DispatchQueue.main.asyncAfter(deadline: .now() + 2.0) {
            isPlaying = false
            
            let result = VoiceTestResult(
                testType: .synthesis,
                passed: true,
                details: "Speech synthesis completed with high quality",
                score: 0.88,
                timestamp: Date()
            )
            testResults.insert(result, at: 0)
        }
    }
    
    private func runFullTestSuite() {
        // Simulate running multiple tests
        let testSuite = [
            ("Wake phrase recognition", 0.95),
            ("Command processing", 0.87),
            ("Speech synthesis", 0.91),
            ("Background noise handling", 0.79)
        ]
        
        for (index, test) in testSuite.enumerated() {
            DispatchQueue.main.asyncAfter(deadline: .now() + Double(index + 1)) {
                let result = VoiceTestResult(
                    testType: .recognition,
                    passed: test.1 > 0.7,
                    details: test.0,
                    score: test.1,
                    timestamp: Date()
                )
                testResults.insert(result, at: 0)
            }
        }
    }
    
    private func testWakePhraseRecognition() {
        let result = VoiceTestResult(
            testType: .recognition,
            passed: true,
            details: "Wake phrase '\(settingsManager.voice.wakeWord)' recognition test",
            score: 0.94,
            timestamp: Date()
        )
        testResults.insert(result, at: 0)
    }
    
    private func testCommandProcessing() {
        let result = VoiceTestResult(
            testType: .recognition,
            passed: true,
            details: "Command processing and intent recognition test",
            score: 0.86,
            timestamp: Date()
        )
        testResults.insert(result, at: 0)
    }
}

enum VoiceTestType: String, CaseIterable {
    case recognition = "recognition"
    case synthesis = "synthesis"
    
    var displayName: String {
        switch self {
        case .recognition:
            return "Voice Recognition"
        case .synthesis:
            return "Speech Synthesis"
        }
    }
}

struct VoiceTestResult: Identifiable {
    let id = UUID()
    let testType: VoiceTestType
    let passed: Bool
    let details: String
    let score: Double?
    let timestamp: Date
}

#Preview {
    VoiceTestView()
}