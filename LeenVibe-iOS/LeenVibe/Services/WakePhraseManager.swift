import Foundation
import Speech
import AVFoundation
import SwiftUI

@MainActor
class WakePhraseManager: NSObject, ObservableObject, SFSpeechRecognizerDelegate {
    @Published var isWakeListening = false
    @Published var wakePhraseDetected = false
    @Published var lastWakeDetection: WakePhraseDetection?
    @Published var isAvailable = false
    @Published var lastError: String?
    @Published var audioLevel: Float = 0.0
    
    private let speechRecognizer: SFSpeechRecognizer?
    private var wakeRecognitionRequest: SFSpeechAudioBufferRecognitionRequest?
    nonisolated(unsafe) private var wakeRecognitionTask: SFSpeechRecognitionTask?
    nonisolated(unsafe) private let wakeAudioEngine = AVAudioEngine()
    
    private let webSocketService: WebSocketService
    private let projectManager: ProjectManager
    private let voiceProcessor: DashboardVoiceProcessor
    
    // Wake phrase configuration
    private let wakePhrase = "hey leanvibe"
    private let wakePhraseAlternatives = [
        "hey lynn vibe",
        "hey lean vibe", 
        "hey leen vibe",
        "hey lee vibe",
        "a leanvibe"
        "hey leanvibe"
    ]
    
    // Detection settings
    private let confidenceThreshold: Float = 0.6
    private let silenceTimeout: TimeInterval = 3.0
    nonisolated(unsafe) private var silenceTimer: Timer?
    
    init(webSocketService: WebSocketService, projectManager: ProjectManager, voiceProcessor: DashboardVoiceProcessor) {
        self.webSocketService = webSocketService
        self.projectManager = projectManager
        self.voiceProcessor = voiceProcessor
        self.speechRecognizer = SFSpeechRecognizer(locale: Locale(identifier: "en-US"))
        
        super.init()
        
        setupSpeechRecognizer()
        checkPermissions()
    }
    
    deinit {
        // Cleanup will be handled automatically
        wakeAudioEngine.stop()
        wakeRecognitionTask?.cancel()
        silenceTimer?.invalidate()
    }
    
    // MARK: - Setup and Permissions
    
    private func setupSpeechRecognizer() {
        speechRecognizer?.delegate = self
        isAvailable = speechRecognizer?.isAvailable ?? false
    }
    
    private func checkPermissions() {
        let speechStatus = SFSpeechRecognizer.authorizationStatus()
        let microphoneStatus = AVAudioSession.sharedInstance().recordPermission
        
        isAvailable = speechStatus == .authorized && microphoneStatus == .granted
    }
    
    // MARK: - Wake Phrase Detection
    
    func startWakeListening() {
        guard isAvailable else {
            lastError = "Wake listening not available - permissions required"
            return
        }
        
        guard !isWakeListening else { return }
        
        stopWakeListening()
        isWakeListening = true
        wakePhraseDetected = false
        
        setupWakeRecognition()
        startWakeAudioEngine()
        
        sendWakeStatusUpdate("🎤 Wake phrase listening started")
    }
    
    func stopWakeListening() {
        isWakeListening = false
        
        if wakeAudioEngine.isRunning {
            wakeAudioEngine.stop()
            wakeAudioEngine.inputNode.removeTap(onBus: 0)
        }
        
        wakeRecognitionRequest?.endAudio()
        wakeRecognitionTask?.cancel()
        wakeRecognitionRequest = nil
        wakeRecognitionTask = nil
        
        silenceTimer?.invalidate()
        audioLevel = 0.0
        
        if wakePhraseDetected {
            sendWakeStatusUpdate("🛑 Wake phrase listening stopped")
        }
    }
    
    private func setupWakeRecognition() {
        wakeRecognitionRequest = SFSpeechAudioBufferRecognitionRequest()
        guard let wakeRecognitionRequest = wakeRecognitionRequest else { return }
        
        wakeRecognitionRequest.shouldReportPartialResults = true
        wakeRecognitionRequest.requiresOnDeviceRecognition = true
        
        guard let speechRecognizer = speechRecognizer else { return }
        
        wakeRecognitionTask = speechRecognizer.recognitionTask(with: wakeRecognitionRequest) { [weak self] result, error in
            DispatchQueue.main.async {
                self?.handleWakeRecognitionResult(result: result, error: error)
            }
        }
    }
    
    private func startWakeAudioEngine() {
        let inputNode = wakeAudioEngine.inputNode
        let recordingFormat = inputNode.outputFormat(forBus: 0)
        
        inputNode.installTap(onBus: 0, bufferSize: 1024, format: recordingFormat) { [weak self] buffer, _ in
            self?.wakeRecognitionRequest?.append(buffer)
            self?.calculateWakeAudioLevel(from: buffer)
        }
        
        do {
            wakeAudioEngine.prepare()
            try wakeAudioEngine.start()
        } catch {
            DispatchQueue.main.async {
                self.lastError = "Wake audio engine failed to start"
                self.stopWakeListening()
            }
        }
    }
    
    private func calculateWakeAudioLevel(from buffer: AVAudioPCMBuffer) {
        guard let channelData = buffer.floatChannelData?[0] else { return }
        
        let frameLength = Int(buffer.frameLength)
        var sum: Float = 0.0
        
        for i in 0..<frameLength {
            sum += abs(channelData[i])
        }
        
        let averageLevel = sum / Float(frameLength)
        let normalizedLevel = min(averageLevel * 15, 1.0) // More sensitive for wake detection
        
        DispatchQueue.main.async {
            self.audioLevel = normalizedLevel
        }
    }
    
    // MARK: - Recognition Result Handling
    
    private func handleWakeRecognitionResult(result: SFSpeechRecognitionResult?, error: Error?) {
        if let error = error {
            lastError = "Wake recognition error: \(error.localizedDescription)"
            // Don't stop listening for wake phrase on errors - keep trying
            return
        }
        
        guard let result = result else { return }
        
        let currentTranscription = result.bestTranscription.formattedString.lowercased()
        let confidence = result.bestTranscription.segments.last?.confidence ?? 0.0
        
        // Reset silence timer on any speech
        if !currentTranscription.isEmpty {
            resetSilenceTimer()
        }
        
        // Check for wake phrase
        if detectWakePhrase(in: currentTranscription, confidence: confidence) {
            let detection = WakePhraseDetection(
                detectedPhrase: currentTranscription,
                confidence: Double(confidence),
                audioLevel: audioLevel
            )
            
            lastWakeDetection = detection
            wakePhraseDetected = true
            
            handleWakePhraseDetected(detection)
        }
        
        // Keep wake listening active - restart on final results
        if result.isFinal {
            startSilenceTimer()
        }
    }
    
    private func detectWakePhrase(in transcription: String, confidence: Float) -> Bool {
        guard confidence >= confidenceThreshold else { return false }
        
        let cleanedTranscription = transcription
            .trimmingCharacters(in: .whitespacesAndNewlines)
            .replacingOccurrences(of: ".", with: "")
            .replacingOccurrences(of: ",", with: "")
            .replacingOccurrences(of: "?", with: "")
            .replacingOccurrences(of: "!", with: "")
        
        // Check exact wake phrase
        if cleanedTranscription.contains(wakePhrase) {
            return true
        }
        
        // Check alternative pronunciations
        for alternative in wakePhraseAlternatives {
            if cleanedTranscription.contains(alternative) {
                return true
            }
        }
        
        // Check for partial matches at the beginning
        let words = cleanedTranscription.components(separatedBy: " ")
        if words.count >= 2 {
            let firstTwoWords = "\(words[0]) \(words[1])"
            if firstTwoWords.contains("hey") && 
               (firstTwoWords.contains("leen") || firstTwoWords.contains("lynn") || firstTwoWords.contains("lean")) {
                return true
            }
        }
        
        return false
    }
    
    private func handleWakePhraseDetected(_ detection: WakePhraseDetection) {
        // Temporarily stop wake listening to process command
        stopWakeListening()
        
        // Provide haptic feedback
        let impact = UIImpactFeedbackGenerator(style: .medium)
        impact.impactOccurred()
        
        // Log the wake phrase detection
        sendWakeStatusUpdate("✨ Wake phrase detected: \"\(detection.detectedPhrase)\"")
        
        // Start voice command processing with a brief delay
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            self.triggerVoiceCommandSession()
        }
        
        // Restart wake listening after a delay
        DispatchQueue.main.asyncAfter(deadline: .now() + 5.0) {
            if !self.isWakeListening {
                self.startWakeListening()
            }
        }
    }
    
    private func triggerVoiceCommandSession() {
        // This would trigger the voice command interface
        // For now, we'll post a notification that the UI can observe
        NotificationCenter.default.post(
            name: NSNotification.Name("WakePhraseDetected"),
            object: lastWakeDetection
        )
        
        sendWakeStatusUpdate("🎤 Voice command session starting...")
    }
    
    // MARK: - Timer Management
    
    private func resetSilenceTimer() {
        silenceTimer?.invalidate()
    }
    
    private func startSilenceTimer() {
        silenceTimer = Timer.scheduledTimer(withTimeInterval: silenceTimeout, repeats: false) { [weak self] _ in
            Task { @MainActor in
                self?.handleSilenceTimeout()
            }
        }
    }
    
    private func handleSilenceTimeout() {
        // Restart wake recognition after silence
        if isWakeListening {
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                if self.isWakeListening {
                    self.setupWakeRecognition()
                    if !self.wakeAudioEngine.isRunning {
                        self.startWakeAudioEngine()
                    }
                }
            }
        }
    }
    
    // MARK: - Public Interface
    
    func toggleWakeListening() {
        if isWakeListening {
            stopWakeListening()
        } else {
            startWakeListening()
        }
    }
    
    var canStartWakeListening: Bool {
        return isAvailable && !isWakeListening
    }
    
    // MARK: - Feedback
    
    private func sendWakeStatusUpdate(_ message: String) {
        let statusMessage = AgentMessage(
            content: message,
            isFromUser: false,
            type: .status
        )
        webSocketService.messages.append(statusMessage)
    }
}

/*
extension WakePhraseManager: SFSpeechRecognizerDelegate {
    
    public func speechRecognizer(_ speechRecognizer: SFSpeechRecognizer, availabilityDidChange available: Bool) {
        if available {
            isAvailable = true
        } else {
            isAvailable = false
        }
    }
}
*/