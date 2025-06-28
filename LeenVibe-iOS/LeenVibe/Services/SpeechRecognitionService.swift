import Foundation
import Speech
import AVFoundation
import Combine

@MainActor
class SpeechRecognitionService: NSObject, ObservableObject, SFSpeechRecognizerDelegate {
    @Published var isListening = false
    @Published var isAvailable = false
    @Published var transcription = ""
    @Published var authorizationStatus: SFSpeechRecognizerAuthorizationStatus = .notDetermined
    @Published var lastError: String?
    @Published var audioLevel: Float = 0.0
    @Published var recognitionState: RecognitionState = .idle
    
    private let speechRecognizer: SFSpeechRecognizer?
    private var recognitionRequest: SFSpeechAudioBufferRecognitionRequest?
    private var recognitionTask: SFSpeechRecognitionTask?
    private let audioEngine = AVAudioEngine()
    private var audioLevelTimer: Timer?
    
    private let webSocketService: WebSocketService
    private var cancellables = Set<AnyCancellable>()
    
    // Configuration
    private let silenceTimeout: TimeInterval = 2.0
    private let maxRecordingDuration: TimeInterval = 60.0
    private var silenceTimer: Timer?
    private var recordingTimer: Timer?
    
    enum RecognitionState {
        case idle
        case listening
        case processing
        case completed
        case error(String)
        
        var description: String {
            switch self {
            case .idle:
                return "Ready"
            case .listening:
                return "Listening..."
            case .processing:
                return "Processing..."
            case .completed:
                return "Completed"
            case .error(let message):
                return "Error: \(message)"
            }
        }
    }
    
    init(webSocketService: WebSocketService) {
        self.webSocketService = webSocketService
        self.speechRecognizer = SFSpeechRecognizer(locale: Locale(identifier: "en-US"))
        
        setupSpeechRecognizer()
        requestPermissions()
    }
    
    deinit {
        stopListening()
        audioLevelTimer?.invalidate()
        silenceTimer?.invalidate()
        recordingTimer?.invalidate()
    }
    
    // MARK: - Setup and Permissions
    
    private func setupSpeechRecognizer() {
        speechRecognizer?.delegate = self
        isAvailable = speechRecognizer?.isAvailable ?? false
    }
    
    func requestPermissions() {
        // Request speech recognition permission
        SFSpeechRecognizer.requestAuthorization { [weak self] status in
            DispatchQueue.main.async {
                self?.authorizationStatus = status
                
                switch status {
                case .authorized:
                    self?.requestMicrophonePermission()
                case .denied, .restricted:
                    self?.lastError = "Speech recognition access denied"
                case .notDetermined:
                    self?.lastError = "Speech recognition permission not determined"
                @unknown default:
                    self?.lastError = "Unknown speech recognition permission status"
                }
            }
        }
    }
    
    private func requestMicrophonePermission() {
        AVAudioSession.sharedInstance().requestRecordPermission { [weak self] granted in
            DispatchQueue.main.async {
                if granted {
                    self?.configureAudioSession()
                } else {
                    self?.lastError = "Microphone access denied"
                }
            }
        }
    }
    
    private func configureAudioSession() {
        do {
            let audioSession = AVAudioSession.sharedInstance()
            try audioSession.setCategory(.record, mode: .measurement, options: .duckOthers)
            try audioSession.setActive(true, options: .notifyOthersOnDeactivation)
            isAvailable = true
            lastError = nil
        } catch {
            lastError = "Audio session configuration failed: \(error.localizedDescription)"
        }
    }
    
    // MARK: - Speech Recognition Control
    
    func startListening() {
        guard isAvailable && authorizationStatus == .authorized else {
            lastError = "Speech recognition not available or not authorized"
            return
        }
        
        // Stop any existing recognition
        stopListening()
        
        recognitionState = .listening
        isListening = true
        transcription = ""
        
        setupRecognition()
        startAudioEngine()
        startAudioLevelMonitoring()
        startRecordingTimeout()
    }
    
    func stopListening() {
        recognitionState = .idle
        isListening = false
        
        // Clean up timers
        silenceTimer?.invalidate()
        recordingTimer?.invalidate()
        audioLevelTimer?.invalidate()
        
        // Stop audio engine
        if audioEngine.isRunning {
            audioEngine.stop()
            audioEngine.inputNode.removeTap(onBus: 0)
        }
        
        // Clean up recognition
        recognitionRequest?.endAudio()
        recognitionTask?.cancel()
        recognitionRequest = nil
        recognitionTask = nil
        
        // Reset audio level
        audioLevel = 0.0
    }
    
    private func setupRecognition() {
        recognitionRequest = SFSpeechAudioBufferRecognitionRequest()
        
        guard let recognitionRequest = recognitionRequest else {
            lastError = "Unable to create recognition request"
            return
        }
        
        recognitionRequest.shouldReportPartialResults = true
        recognitionRequest.requiresOnDeviceRecognition = true // Privacy-first approach
        
        guard let speechRecognizer = speechRecognizer else {
            lastError = "Speech recognizer not available"
            return
        }
        
        recognitionTask = speechRecognizer.recognitionTask(with: recognitionRequest) { [weak self] result, error in
            DispatchQueue.main.async {
                self?.handleRecognitionResult(result: result, error: error)
            }
        }
    }
    
    private func startAudioEngine() {
        let inputNode = audioEngine.inputNode
        let recordingFormat = inputNode.outputFormat(forBus: 0)
        
        inputNode.installTap(onBus: 0, bufferSize: 1024, format: recordingFormat) { [weak self] buffer, _ in
            self?.recognitionRequest?.append(buffer)
            
            // Calculate audio level for visualization
            self?.calculateAudioLevel(from: buffer)
        }
        
        do {
            audioEngine.prepare()
            try audioEngine.start()
        } catch {
            DispatchQueue.main.async {
                self.lastError = "Audio engine failed to start: \(error.localizedDescription)"
                self.stopListening()
            }
        }
    }
    
    // MARK: - Audio Level Monitoring
    
    private func startAudioLevelMonitoring() {
        audioLevelTimer = Timer.scheduledTimer(withTimeInterval: 0.1, repeats: true) { [weak self] _ in
            // Audio level is updated in calculateAudioLevel
        }
    }
    
    private func calculateAudioLevel(from buffer: AVAudioPCMBuffer) {
        guard let channelData = buffer.floatChannelData?[0] else { return }
        
        let frameLength = Int(buffer.frameLength)
        var sum: Float = 0.0
        
        for i in 0..<frameLength {
            sum += abs(channelData[i])
        }
        
        let averageLevel = sum / Float(frameLength)
        let normalizedLevel = min(averageLevel * 20, 1.0) // Amplify and normalize
        
        DispatchQueue.main.async {
            self.audioLevel = normalizedLevel
        }
    }
    
    // MARK: - Recognition Result Handling
    
    private func handleRecognitionResult(result: SFSpeechRecognitionResult?, error: Error?) {
        if let error = error {
            lastError = "Recognition error: \(error.localizedDescription)"
            recognitionState = .error(error.localizedDescription)
            stopListening()
            return
        }
        
        guard let result = result else { return }
        
        transcription = result.bestTranscription.formattedString
        
        // Reset silence timer on new speech
        if !transcription.isEmpty {
            resetSilenceTimer()
        }
        
        if result.isFinal {
            recognitionState = .completed
            processCompletedTranscription()
        }
    }
    
    private func processCompletedTranscription() {
        guard !transcription.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            stopListening()
            return
        }
        
        recognitionState = .processing
        
        // Process the voice command
        Task {
            await processVoiceCommand(transcription)
            stopListening()
        }
    }
    
    // MARK: - Voice Command Processing
    
    private func processVoiceCommand(_ command: String) async {
        // Basic command processing - will be enhanced with natural language processing
        let processedCommand = preprocessVoiceCommand(command)
        
        // Send to WebSocket service
        webSocketService.sendMessage(processedCommand, type: "voice_command")
        
        // Log the voice command
        let voiceMessage = AgentMessage(
            content: "🎤 Voice: \(command)",
            isFromUser: true,
            type: .command
        )
        webSocketService.messages.append(voiceMessage)
    }
    
    private func preprocessVoiceCommand(_ command: String) -> String {
        let lowercased = command.lowercased().trimmingCharacters(in: .whitespacesAndNewlines)
        
        // Basic command mapping
        let commandMappings: [String: String] = [
            "status": "/status",
            "list files": "/list-files",
            "current directory": "/current-dir",
            "help": "/help",
            "show me the status": "/status",
            "what's the current directory": "/current-dir",
            "list all files": "/list-files",
            "show help": "/help"
        ]
        
        // Check for exact matches first
        if let mappedCommand = commandMappings[lowercased] {
            return mappedCommand
        }
        
        // Check for partial matches
        for (pattern, command) in commandMappings {
            if lowercased.contains(pattern) {
                return command
            }
        }
        
        // If no mapping found, send as natural language
        return lowercased
    }
    
    // MARK: - Timeout Management
    
    private func resetSilenceTimer() {
        silenceTimer?.invalidate()
        silenceTimer = Timer.scheduledTimer(withTimeInterval: silenceTimeout, repeats: false) { [weak self] _ in
            self?.handleSilenceTimeout()
        }
    }
    
    private func handleSilenceTimeout() {
        if !transcription.isEmpty {
            recognitionState = .completed
            processCompletedTranscription()
        } else {
            stopListening()
        }
    }
    
    private func startRecordingTimeout() {
        recordingTimer = Timer.scheduledTimer(withTimeInterval: maxRecordingDuration, repeats: false) { [weak self] _ in
            self?.handleRecordingTimeout()
        }
    }
    
    private func handleRecordingTimeout() {
        lastError = "Recording timeout reached"
        stopListening()
    }
    
    // MARK: - Public Interface
    
    var canStartListening: Bool {
        return isAvailable && 
               authorizationStatus == .authorized && 
               !isListening &&
               recognitionState != .processing
    }
    
    func toggleListening() {
        if isListening {
            stopListening()
        } else {
            startListening()
        }
    }
}

/*
extension SpeechRecognitionService: SFSpeechRecognizerDelegate {
    
    public func speechRecognizer(_ speechRecognizer: SFSpeechRecognizer, availabilityDidChange available: Bool) {
        if available {
            isAvailable = true
        } else {
            isAvailable = false
        }
    }
}
*/