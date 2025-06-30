import Foundation
import Speech
import AVFoundation
import Combine

@available(macOS 10.15, iOS 13.0, *)
@MainActor
class SpeechRecognitionService: NSObject, ObservableObject {
    @Published var isListening = false
    @Published var recognizedText = ""
    @Published var confidenceScore: Float = 0.0
    @Published var recognitionState: RecognitionState = .idle
    @Published var audioLevel: Float = 0.0
    @Published var lastError: String?
    
    enum RecognitionState: Equatable {
        case idle
        case listening
        case processing
        case completed
        case error(String)
    }
    
    nonisolated(unsafe) private var audioEngine: AVAudioEngine?
    nonisolated(unsafe) private var recognitionRequest: SFSpeechAudioBufferRecognitionRequest?
    nonisolated(unsafe) private var recognitionTask: SFSpeechRecognitionTask?
    nonisolated(unsafe) private var speechRecognizer: SFSpeechRecognizer?
    nonisolated(unsafe) private var audioLevelTimer: Timer?
    nonisolated(unsafe) private var silenceTimer: Timer?
    nonisolated(unsafe) private var recordingTimer: Timer?
    private var cancellables = Set<AnyCancellable>()
    
    // Configuration
    private let maxRecordingDuration: TimeInterval = 30.0
    private let silenceTimeout: TimeInterval = 3.0
    private let audioLevelUpdateInterval: TimeInterval = 0.1
    
    override init() {
        super.init()
        setupSpeechRecognizer()
    }
    
    deinit {
#if os(iOS)
        // Safely cleanup audio resources on deinit
        // These operations must be performed synchronously to avoid dispatch queue violations
        if let engine = audioEngine {
            engine.stop()
            if engine.inputNode.numberOfInputs > 0 {
                engine.inputNode.removeTap(onBus: 0)
            }
        }
        recognitionTask?.cancel()
        recognitionRequest?.endAudio()
        
        // Invalidate timers safely
        audioLevelTimer?.invalidate()
        silenceTimer?.invalidate() 
        recordingTimer?.invalidate()
#endif
    }
    
    private func setupSpeechRecognizer() {
#if os(iOS)
        // Initialize speech recognizer safely
        if Thread.isMainThread {
            speechRecognizer = SFSpeechRecognizer(locale: Locale(identifier: "en-US"))
            speechRecognizer?.delegate = self
        } else {
            DispatchQueue.main.sync {
                speechRecognizer = SFSpeechRecognizer(locale: Locale(identifier: "en-US"))
                speechRecognizer?.delegate = self
            }
        }
#else
        speechRecognizer = nil
#endif
    }
    
    #if os(iOS)
    func startListening() {
        guard !isListening else { return }
        recognizedText = ""
        confidenceScore = 0.0
        lastError = nil
        recognitionState = .listening
        requestPermissions { [weak self] micGranted, speechStatus in
            guard let self = self else { return }
            guard micGranted else {
                self.recognitionState = .error("Microphone permission denied")
                return
            }
            guard speechStatus == .authorized else {
                self.recognitionState = .error("Speech recognition permission denied")
                return
            }
            do {
                try self.startAudioEngine()
                self.setupRecognitionRequest()
                self.isListening = true
                self.startTimers()
            } catch {
                self.recognitionState = .error(error.localizedDescription)
                self.lastError = error.localizedDescription
            }
        }
    }
    #endif
    
    func stopListening() {
        guard isListening else { return }
        
        isListening = false
        recognitionState = .processing
        
        audioEngine?.stop()
        audioEngine?.inputNode.removeTap(onBus: 0)
        recognitionRequest?.endAudio()
        stopTimers()
        
        // Process final recognition
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            self.recognitionState = .completed
        }
    }
    
    private func startTimers() {
        // Audio level monitoring
        audioLevelTimer = Timer.scheduledTimer(withTimeInterval: audioLevelUpdateInterval, repeats: true) { _ in
            // Timer handled by audio tap
        }
        
        // Silence detection
        silenceTimer = Timer.scheduledTimer(withTimeInterval: silenceTimeout, repeats: false) { [weak self] _ in
            Task { @MainActor [weak self] in
                self?.handleSilenceTimeout()
            }
        }
        
        // Maximum recording duration
        recordingTimer = Timer.scheduledTimer(withTimeInterval: maxRecordingDuration, repeats: false) { [weak self] _ in
            Task { @MainActor [weak self] in
                self?.handleRecordingTimeout()
            }
        }
    }
    
    private func stopTimers() {
        audioLevelTimer?.invalidate()
        silenceTimer?.invalidate()
        recordingTimer?.invalidate()
        
        audioLevelTimer = nil
        silenceTimer = nil
        recordingTimer = nil
    }
    
    private func handleSilenceTimeout() {
        if isListening && recognitionState == .listening {
            stopListening()
        }
    }
    
    private func handleRecordingTimeout() {
        if isListening {
            stopListening()
        }
    }
    
    private func handleRecognitionResult(result: SFSpeechRecognitionResult?, error: Error?) {
        if let error = error {
            recognitionState = .error(error.localizedDescription)
            lastError = error.localizedDescription
            stopListening()
            return
        }
        
        guard let result = result else { return }
        
        recognizedText = result.bestTranscription.formattedString
        confidenceScore = result.bestTranscription.segments.last?.confidence ?? 0.0
        
        if result.isFinal {
            recognitionState = .completed
            stopListening()
        }
    }
    
    func resetRecognition() {
        recognizedText = ""
        confidenceScore = 0.0
        audioLevel = 0.0
        recognitionState = .idle
        lastError = nil
    }
    
    #if os(iOS)
    func requestPermissions(completion: @escaping (Bool, SFSpeechRecognizerAuthorizationStatus) -> Void) {
        AVAudioSession.sharedInstance().requestRecordPermission { micGranted in
            SFSpeechRecognizer.requestAuthorization { speechStatus in
                completion(micGranted, speechStatus)
            }
        }
    }
    #endif
}

#if os(iOS)
extension SpeechRecognitionService: SFSpeechRecognizerDelegate {
    nonisolated func speechRecognizer(_ speechRecognizer: SFSpeechRecognizer, availabilityDidChange available: Bool) {
        Task { @MainActor [weak self] in
            if !available {
                self?.recognitionState = .error("Speech recognizer became unavailable")
                self?.stopListening()
            }
        }
    }
}

// Restore iOS-only methods
extension SpeechRecognitionService {
    func startAudioEngine() throws {
        audioEngine = AVAudioEngine()
        guard let audioEngine = audioEngine else {
            throw RecognitionError.audioEngineFailure
        }
        let inputNode = audioEngine.inputNode
        let recordingFormat = inputNode.outputFormat(forBus: 0)
        inputNode.installTap(onBus: 0, bufferSize: 1024, format: recordingFormat) { [weak self] buffer, _ in
            self?.recognitionRequest?.append(buffer)
            let level = self?.calculateAudioLevel(from: buffer) ?? 0.0
            DispatchQueue.main.async {
                self?.audioLevel = level
            }
        }
        audioEngine.prepare()
        try audioEngine.start()
    }
    
    func setupRecognitionRequest() {
        recognitionRequest = SFSpeechAudioBufferRecognitionRequest()
        guard let recognitionRequest = recognitionRequest else { return }
        recognitionRequest.shouldReportPartialResults = true
        recognitionRequest.requiresOnDeviceRecognition = false
        recognitionTask = speechRecognizer?.recognitionTask(with: recognitionRequest) { [weak self] result, error in
            DispatchQueue.main.async {
                self?.handleRecognitionResult(result: result, error: error)
            }
        }
    }
    
    private func calculateAudioLevel(from buffer: AVAudioPCMBuffer) -> Float {
        guard let channelData = buffer.floatChannelData?[0] else { return 0.0 }
        let channelDataArray = Array(UnsafeBufferPointer(start: channelData, count: Int(buffer.frameLength)))
        let rms = sqrt(channelDataArray.map { $0 * $0 }.reduce(0, +) / Float(channelDataArray.count))
        return min(max(rms * 20, 0.0), 1.0)
    }
}
#endif

#if os(macOS)
// Provide stubs for macOS that set error states or do nothing
#endif

// MARK: - Supporting Types
enum RecognitionError: LocalizedError {
    case microphonePermissionDenied
    case speechRecognitionPermissionDenied
    case audioEngineFailure
    case recognitionFailed(String)
    
    var errorDescription: String? {
        switch self {
        case .microphonePermissionDenied:
            return "Microphone permission is required for voice recognition"
        case .speechRecognitionPermissionDenied:
            return "Speech recognition permission is required"
        case .audioEngineFailure:
            return "Failed to start audio engine"
        case .recognitionFailed(let message):
            return "Recognition failed: \(message)"
        }
    }
}

#if os(iOS)
// All AVAudioSession, SFSpeechRecognizer, and related code here
#endif 