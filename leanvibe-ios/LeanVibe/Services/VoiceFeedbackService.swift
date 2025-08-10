import Foundation
import AVFoundation
import Combine

/// Service responsible for providing audio feedback to users
@available(iOS 18.0, macOS 14.0, *)
@MainActor
class VoiceFeedbackService: ObservableObject {
    
    // MARK: - Singleton
    static let shared = VoiceFeedbackService()
    
    // MARK: - Published State
    @Published private(set) var isSpeaking = false
    @Published private(set) var currentMessage: String?
    @Published var isEnabled = true
    @Published var speechRate: Float = 0.5
    @Published var speechVolume: Float = 0.8
    @Published var preferredVoice: String = "en-US"
    @Published var enableHapticFeedback = true
    @Published var quietModeEnabled = false
    
    // MARK: - Private Properties
    private let synthesizer = AVSpeechSynthesizer()
    private var speechQueue: [VoiceFeedbackMessage] = []
    private var cancellables = Set<AnyCancellable>()
    
    // MARK: - Initialization
    private init() {
        setupSynthesizer()
        setupBindings()
        print("🔊 VoiceFeedbackService: Initialized successfully")
    }
    
    private func setupSynthesizer() {
        synthesizer.delegate = self
    }
    
    private func setupBindings() {
        // Listen to settings changes and adjust accordingly
        $isEnabled
            .sink { [weak self] enabled in
                if !enabled {
                    self?.stopSpeaking()
                }
            }
            .store(in: &cancellables)
        
        $quietModeEnabled
            .sink { [weak self] quietMode in
                if quietMode {
                    self?.stopSpeaking()
                }
            }
            .store(in: &cancellables)
    }
    
    // MARK: - Public Interface
    
    /// Speak a response message to the user
    func speakResponse(_ message: String, priority: VoicePriority = .normal) {
        guard isEnabled && !quietModeEnabled else { 
            print("🔊 VoiceFeedbackService: Skipping speech - disabled or quiet mode")
            return 
        }
        
        let feedback = VoiceFeedbackMessage(
            text: message,
            priority: priority,
            rate: speechRate,
            volume: speechVolume
        )
        
        if priority == .urgent || !isSpeaking {
            speakImmediately(feedback)
        } else {
            speechQueue.append(feedback)
            print("🔊 VoiceFeedbackService: Queued message: \(message)")
        }
    }
    
    /// Speak command confirmation
    func confirmCommand(_ command: String, success: Bool) {
        let message = success ? 
            "Command '\(command)' completed successfully" : 
            "Command '\(command)' failed to execute"
        speakResponse(message, priority: .high)
        
        // Provide haptic feedback if enabled
        if enableHapticFeedback {
            provideHapticFeedback(for: success)
        }
    }
    
    /// Speak error messages
    func speakError(_ error: String) {
        speakResponse("Error: \(error)", priority: .urgent)
        
        // Provide haptic feedback for errors
        if enableHapticFeedback {
            provideHapticFeedback(for: false)
        }
    }
    
    /// Speak status updates
    func speakStatus(_ status: String) {
        speakResponse(status, priority: .normal)
    }
    
    /// Speak welcome message
    func speakWelcome() {
        speakResponse("Welcome to LeanVibe. Voice commands are ready.", priority: .high)
    }
    
    /// Speak wake phrase confirmation
    func speakWakePhraseDetected() {
        speakResponse("Listening for your command", priority: .urgent)
    }
    
    /// Stop current speech
    func stopSpeaking() {
        synthesizer.stopSpeaking(at: .immediate)
        speechQueue.removeAll()
        isSpeaking = false
        currentMessage = nil
        print("🔊 VoiceFeedbackService: Speech stopped")
    }
    
    /// Pause current speech
    func pauseSpeaking() {
        synthesizer.pauseSpeaking(at: .immediate)
        print("🔊 VoiceFeedbackService: Speech paused")
    }
    
    /// Resume paused speech
    func resumeSpeaking() {
        synthesizer.continueSpeaking()
        print("🔊 VoiceFeedbackService: Speech resumed")
    }
    
    /// Get available voices for the current language
    func getAvailableVoices() -> [AVSpeechSynthesisVoice] {
        let voices = AVSpeechSynthesisVoice.speechVoices()
        return voices.filter { voice in
            voice.language.hasPrefix("en") // Filter for English voices
        }.sorted { $0.name < $1.name }
    }
    
    /// Test voice with sample message
    func testVoice() {
        speakResponse("This is a test of the voice feedback system", priority: .high)
    }
    
    // MARK: - Private Implementation
    
    private func speakImmediately(_ feedback: VoiceFeedbackMessage) {
        if isSpeaking && feedback.priority == .urgent {
            synthesizer.stopSpeaking(at: .immediate)
        }
        
        let utterance = AVSpeechUtterance(string: feedback.text)
        
        // Configure voice based on preferences
        if let selectedVoice = AVSpeechSynthesisVoice(language: preferredVoice) {
            utterance.voice = selectedVoice
        } else {
            // Fallback to default English voice
            utterance.voice = AVSpeechSynthesisVoice(language: "en-US")
        }
        
        utterance.rate = feedback.rate
        utterance.volume = feedback.volume
        utterance.pitchMultiplier = 1.0
        
        currentMessage = feedback.text
        isSpeaking = true
        
        print("🔊 VoiceFeedbackService: Speaking: \(feedback.text)")
        synthesizer.speak(utterance)
    }
    
    private func processNextInQueue() {
        guard !speechQueue.isEmpty else { return }
        
        let next = speechQueue.removeFirst()
        speakImmediately(next)
        print("🔊 VoiceFeedbackService: Processing queued message")
    }
    
    private func provideHapticFeedback(for success: Bool) {
        #if os(iOS)
        let feedbackGenerator: UINotificationFeedbackGenerator
        feedbackGenerator = UINotificationFeedbackGenerator()
        
        if success {
            feedbackGenerator.notificationOccurred(.success)
        } else {
            feedbackGenerator.notificationOccurred(.error)
        }
        #endif
    }
}

// MARK: - AVSpeechSynthesizerDelegate
extension VoiceFeedbackService: AVSpeechSynthesizerDelegate {
    
    nonisolated func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didStart utterance: AVSpeechUtterance) {
        print("🔊 VoiceFeedbackService: Started speaking: \(utterance.speechString)")
    }
    
    nonisolated func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didFinish utterance: AVSpeechUtterance) {
        Task { @MainActor in
            print("🔊 VoiceFeedbackService: Finished speaking: \(utterance.speechString)")
            self.isSpeaking = false
            self.currentMessage = nil
            self.processNextInQueue()
        }
    }
    
    nonisolated func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didCancel utterance: AVSpeechUtterance) {
        Task { @MainActor in
            print("🔊 VoiceFeedbackService: Cancelled speaking: \(utterance.speechString)")
            self.isSpeaking = false
            self.currentMessage = nil
        }
    }
    
    nonisolated func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didPause utterance: AVSpeechUtterance) {
        print("🔊 VoiceFeedbackService: Paused speaking: \(utterance.speechString)")
    }
    
    nonisolated func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didContinue utterance: AVSpeechUtterance) {
        print("🔊 VoiceFeedbackService: Resumed speaking: \(utterance.speechString)")
    }
    
    nonisolated func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, willSpeakRangeOfSpeechString characterRange: NSRange, utterance: AVSpeechUtterance) {
        // Optional: Could be used for highlighting text while speaking
    }
}

// MARK: - Supporting Types

enum VoicePriority: Int, CaseIterable {
    case low = 0
    case normal = 1
    case high = 2
    case urgent = 3
    
    var description: String {
        switch self {
        case .low: return "Low"
        case .normal: return "Normal"
        case .high: return "High"
        case .urgent: return "Urgent"
        }
    }
}

struct VoiceFeedbackMessage {
    let text: String
    let priority: VoicePriority
    let rate: Float
    let volume: Float
    let timestamp: Date = Date()
    
    var id: String {
        "\(timestamp.timeIntervalSince1970)-\(text.hashValue)"
    }
}

// MARK: - Voice Feedback Settings Helper
class VoiceFeedbackSettings: ObservableObject {
    @Published var preferredVoice: String = "en-US"
    @Published var enableHapticFeedback = true
    @Published var quietModeEnabled = false
    @Published var speechRate: Float = 0.5
    @Published var speechVolume: Float = 0.8
    
    // Convenience computed properties
    var normalizedSpeechRate: Float {
        return max(0.1, min(1.0, speechRate))
    }
    
    var normalizedSpeechVolume: Float {
        return max(0.0, min(1.0, speechVolume))
    }
}

// MARK: - Voice Feedback Error Types
enum VoiceFeedbackError: Error, LocalizedError {
    case speechSynthesisUnavailable
    case voiceNotFound(String)
    case audioSessionError(String)
    case unknown(String)
    
    var errorDescription: String? {
        switch self {
        case .speechSynthesisUnavailable:
            return "Speech synthesis is not available on this device"
        case .voiceNotFound(let voice):
            return "Voice '\(voice)' not found"
        case .audioSessionError(let message):
            return "Audio session error: \(message)"
        case .unknown(let message):
            return "Unknown voice feedback error: \(message)"
        }
    }
}

// MARK: - Public Extensions for Convenience
@available(iOS 18.0, macOS 14.0, *)
extension VoiceFeedbackService {
    
    /// Quick feedback for common scenarios
    enum QuickFeedback {
        case commandSucceeded(String)
        case commandFailed(String)
        case wakePhraseDetected
        case listeningStarted
        case listeningStopped
        case processingCommand
        case systemError(String)
        
        var message: String {
            switch self {
            case .commandSucceeded(let command):
                return "Command \(command) executed successfully"
            case .commandFailed(let command):
                return "Failed to execute command \(command)"
            case .wakePhraseDetected:
                return "Wake phrase detected. Listening for your command"
            case .listeningStarted:
                return "Listening for voice command"
            case .listeningStopped:
                return "Voice listening stopped"
            case .processingCommand:
                return "Processing your command"
            case .systemError(let error):
                return "System error: \(error)"
            }
        }
        
        var priority: VoicePriority {
            switch self {
            case .commandSucceeded:
                return .high
            case .commandFailed, .systemError:
                return .urgent
            case .wakePhraseDetected:
                return .urgent
            case .listeningStarted, .listeningStopped, .processingCommand:
                return .normal
            }
        }
    }
    
    /// Provide quick feedback using predefined messages
    func provide(_ feedback: QuickFeedback) {
        speakResponse(feedback.message, priority: feedback.priority)
    }
    
    /// Chain multiple feedback messages
    func speakSequence(_ messages: [String], withDelay delay: TimeInterval = 0.5) {
        for (index, message) in messages.enumerated() {
            if index == 0 {
                speakResponse(message, priority: .high)
            } else {
                // Add delayed messages to queue
                DispatchQueue.main.asyncAfter(deadline: .now() + delay * Double(index)) {
                    self.speakResponse(message, priority: .normal)
                }
            }
        }
    }
    
    /// Check if voice feedback is currently available
    var isAvailable: Bool {
        return isEnabled && !quietModeEnabled && AVSpeechSynthesisVoice.speechVoices().count > 0
    }
    
    /// Get current queue length
    var queueLength: Int {
        return speechQueue.count
    }
    
    /// Clear the speech queue without stopping current speech
    func clearQueue() {
        speechQueue.removeAll()
        print("🔊 VoiceFeedbackService: Speech queue cleared")
    }
}