import Foundation
import Speech
import AVFoundation
import SwiftUI

@MainActor
class VoiceManager: ObservableObject {
    @Published var isListening = false
    @Published var isAvailable = false
    @Published var transcription = ""
    @Published var authorizationStatus: SFSpeechRecognizerAuthorizationStatus = .notDetermined
    @Published var lastError: String?
    @Published var audioLevel: Float = 0.0
    
    private let speechRecognizer: SFSpeechRecognizer?
    private var recognitionRequest: SFSpeechAudioBufferRecognitionRequest?
    private var recognitionTask: SFSpeechRecognitionTask?
    private let audioEngine = AVAudioEngine()
    
    private let webSocketService: WebSocketService
    
    init(webSocketService: WebSocketService) {
        self.webSocketService = webSocketService
        self.speechRecognizer = SFSpeechRecognizer(locale: Locale(identifier: "en-US"))
        
        setupSpeechRecognizer()
        requestPermissions()
    }
    
    deinit {
        stopListening()
    }
    
    private func setupSpeechRecognizer() {
        isAvailable = speechRecognizer?.isAvailable ?? false
    }
    
    func requestPermissions() {
        SFSpeechRecognizer.requestAuthorization { [weak self] status in
            DispatchQueue.main.async {
                self?.authorizationStatus = status
                
                if status == .authorized {
                    self?.requestMicrophonePermission()
                } else {
                    self?.lastError = "Speech recognition access denied"
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
    
    func startListening() {
        guard isAvailable && authorizationStatus == .authorized else {
            lastError = "Speech recognition not available or not authorized"
            return
        }
        
        stopListening() // Stop any existing recognition
        
        isListening = true
        transcription = ""
        
        setupRecognition()
        startAudioEngine()
    }
    
    func stopListening() {
        isListening = false
        
        if audioEngine.isRunning {
            audioEngine.stop()
            audioEngine.inputNode.removeTap(onBus: 0)
        }
        
        recognitionRequest?.endAudio()
        recognitionTask?.cancel()
        recognitionRequest = nil
        recognitionTask = nil
        
        audioLevel = 0.0
    }
    
    private func setupRecognition() {
        recognitionRequest = SFSpeechAudioBufferRecognitionRequest()
        
        guard let recognitionRequest = recognitionRequest else {
            lastError = "Unable to create recognition request"
            return
        }
        
        recognitionRequest.shouldReportPartialResults = true
        recognitionRequest.requiresOnDeviceRecognition = true
        
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
    
    private func calculateAudioLevel(from buffer: AVAudioPCMBuffer) {
        guard let channelData = buffer.floatChannelData?[0] else { return }
        
        let frameLength = Int(buffer.frameLength)
        var sum: Float = 0.0
        
        for i in 0..<frameLength {
            sum += abs(channelData[i])
        }
        
        let averageLevel = sum / Float(frameLength)
        let normalizedLevel = min(averageLevel * 20, 1.0)
        
        DispatchQueue.main.async {
            self.audioLevel = normalizedLevel
        }
    }
    
    private func handleRecognitionResult(result: SFSpeechRecognitionResult?, error: Error?) {
        if let error = error {
            lastError = "Recognition error: \(error.localizedDescription)"
            stopListening()
            return
        }
        
        guard let result = result else { return }
        
        transcription = result.bestTranscription.formattedString
        
        if result.isFinal {
            processCompletedTranscription()
        }
    }
    
    private func processCompletedTranscription() {
        guard !transcription.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            stopListening()
            return
        }
        
        let processedCommand = preprocessVoiceCommand(transcription)
        webSocketService.sendMessage(processedCommand, type: "voice_command")
        
        // Add voice message to chat
        let voiceMessage = AgentMessage(
            content: "🎤 Voice: \(transcription)",
            isFromUser: true,
            type: .command
        )
        webSocketService.messages.append(voiceMessage)
        
        stopListening()
    }
    
    private func preprocessVoiceCommand(_ command: String) -> String {
        let lowercased = command.lowercased()
            .trimmingCharacters(in: .whitespacesAndNewlines)
            .replacingOccurrences(of: "hey leenvibe", with: "")
            .replacingOccurrences(of: "leenvibe", with: "")
            .trimmingCharacters(in: .whitespacesAndNewlines)
        
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
        
        return lowercased
    }
    
    func toggleListening() {
        if isListening {
            stopListening()
        } else {
            startListening()
        }
    }
    
    var canStartListening: Bool {
        return isAvailable && authorizationStatus == .authorized && !isListening
    }
}