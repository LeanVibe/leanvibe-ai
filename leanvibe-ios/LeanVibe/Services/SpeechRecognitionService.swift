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
    
    private var audioEngine: AVAudioEngine?
    private var recognitionRequest: SFSpeechAudioBufferRecognitionRequest?
    private var recognitionTask: SFSpeechRecognitionTask?
    private var speechRecognizer: SFSpeechRecognizer?
    private var silenceTask: Task<Void, Never>?
    private var recordingTimeoutTask: Task<Void, Never>?
    private var cancellables = Set<AnyCancellable>()
    private let audioCoordinator = AudioSessionCoordinator.shared
    private let clientId = "SpeechRecognitionService-\(UUID().uuidString)"
    
    // Configuration
    private let maxRecordingDuration: TimeInterval = 30.0
    private let silenceTimeout: TimeInterval = 3.0
    private let audioLevelUpdateInterval: TimeInterval = 0.1
    
    override init() {
        super.init()
        setupSpeechRecognizer()
    }
    
    deinit {
        // Cancel tasks immediately - they are designed to be cancelled safely
        silenceTask?.cancel()
        recordingTimeoutTask?.cancel()
        
        // Audio engine cleanup will happen naturally when the instance is deallocated
        // This is safer than attempting async cleanup in deinit
    }
    
    private func setupSpeechRecognizer() {
#if os(iOS)
        // @MainActor ensures we're always on main thread - no need for dispatch checks
        speechRecognizer = SFSpeechRecognizer(locale: Locale(identifier: "en-US"))
        speechRecognizer?.delegate = self
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
            Task {
                let result = await self.audioCoordinator.registerSpeechClient(self.clientId)
                switch result {
                case .success:
                    await self.setupRecognitionRequest()
                    self.isListening = true
                    self.startTimers()
                    self.setupAudioBufferSubscription()
                case .failure(let error):
                    self.recognitionState = .error(error.localizedDescription)
                    self.lastError = error.localizedDescription
                }
            }
        }
    }
    #endif
    
    func stopListening() {
        guard isListening else { return }
        
        isListening = false
        recognitionState = .processing
        
        // Unregister from audio coordinator
        Task {
            await audioCoordinator.unregisterClient(clientId)
        }
        
        recognitionRequest?.endAudio()
        stopTimers()
        
        // Process final recognition
        Task { @MainActor [weak self] in
            try? await Task.sleep(nanoseconds: 500_000_000) // 0.5 seconds
            self?.recognitionState = .completed
        }
    }
    
    private func startTimers() {
        // Silence detection using modern async Task.sleep
        silenceTask = Task { [weak self] in
            try? await Task.sleep(for: .seconds(self?.silenceTimeout ?? 3.0))
            guard !Task.isCancelled else { return }
            await MainActor.run { [weak self] in
                self?.handleSilenceTimeout()
            }
        }
        
        // Maximum recording duration using modern async Task.sleep
        recordingTimeoutTask = Task { [weak self] in
            try? await Task.sleep(for: .seconds(self?.maxRecordingDuration ?? 30.0))
            guard !Task.isCancelled else { return }
            await MainActor.run { [weak self] in
                self?.handleRecordingTimeout()
            }
        }
    }
    
    private func stopTimers() {
        silenceTask?.cancel()
        recordingTimeoutTask?.cancel()
        
        silenceTask = nil
        recordingTimeoutTask = nil
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
                Task { @MainActor in
                    completion(micGranted, speechStatus)
                }
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

// MARK: - Audio Integration with Coordinator
extension SpeechRecognitionService {
    private func setupAudioBufferSubscription() {
        // Subscribe to audio buffers from the coordinator
        audioCoordinator.audioBufferPublisher
            .sink { [weak self] buffer in
                Task { @MainActor [weak self] in
                    self?.processAudioBuffer(buffer)
                }
            }
            .store(in: &cancellables)
    }
    
    private func processAudioBuffer(_ buffer: AVAudioPCMBuffer) {
        // Send buffer to speech recognition
        recognitionRequest?.append(buffer)
        
        // Update audio level
        audioLevel = calculateAudioLevel(from: buffer)
    }
    
    private func setupRecognitionRequest() async {
        recognitionRequest = SFSpeechAudioBufferRecognitionRequest()
        guard let recognitionRequest = recognitionRequest else { return }
        recognitionRequest.shouldReportPartialResults = true
        recognitionRequest.requiresOnDeviceRecognition = true
        recognitionTask = speechRecognizer?.recognitionTask(with: recognitionRequest) { [weak self] result, error in
            Task { @MainActor [weak self] in
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