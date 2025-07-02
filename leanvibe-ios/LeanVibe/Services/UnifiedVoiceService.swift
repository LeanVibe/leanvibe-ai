import Foundation
import Combine
import Speech
import SwiftUI

/// Unified voice service that consolidates all voice-related functionality
/// This replaces the fragmented VoiceManager, GlobalVoiceManager, and related services
@available(iOS 18.0, macOS 14.0, *)
@MainActor
class UnifiedVoiceService: ObservableObject {
    
    // MARK: - Singleton
    static let shared = UnifiedVoiceService()
    
    // MARK: - Published State
    @Published private(set) var state: VoiceState = .idle
    @Published private(set) var recognizedText: String = ""
    @Published private(set) var audioLevel: Float = 0.0
    @Published private(set) var confidenceScore: Float = 0.0
    
    // MARK: - Dependencies
    private let speechRecognitionService: SpeechRecognitionService
    private let audioCoordinator: AudioSessionCoordinator
    private let webSocketService: WebSocketService
    private let permissionManager: VoicePermissionManager
    private let wakePhraseManager: WakePhraseManager
    private let voiceProcessor: DashboardVoiceProcessor
    
    // MARK: - Private State
    private var cancellables = Set<AnyCancellable>()
    private let clientId = "UnifiedVoiceService-\(UUID().uuidString)"
    
    // MARK: - Configuration
    private let commandMappings: [String: String] = [
        "status": "/status",
        "list files": "/list-files", 
        "current directory": "/current-dir",
        "help": "/help",
        "show architecture": "/architecture",
        "create task": "/create-task",
        "show tasks": "/tasks",
        "show me the status": "/status",
        "what's the current directory": "/current-dir",
        "list all files": "/list-files"
    ]
    
    // MARK: - Initialization
    
    private init() {
        self.speechRecognitionService = SpeechRecognitionService()
        self.audioCoordinator = AudioSessionCoordinator.shared
        self.webSocketService = WebSocketService()
        self.permissionManager = VoicePermissionManager()
        
        // Initialize voice processor and wake phrase manager with dependency injection
        // Create new ProjectManager instance and use SettingsManager singleton
        let projectManager = ProjectManager()
        let settingsManager = SettingsManager.shared
        
        self.voiceProcessor = DashboardVoiceProcessor(
            projectManager: projectManager,
            webSocketService: webSocketService,
            settingsManager: settingsManager
        )
        
        self.wakePhraseManager = WakePhraseManager(
            webSocketService: webSocketService,
            projectManager: projectManager,
            voiceProcessor: voiceProcessor
        )
        
        setupBindings()
    }
    
    // MARK: - Public Interface
    
    /// Start voice listening in the specified mode
    func startListening(mode: ListeningMode = .pushToTalk) async {
        guard AppConfiguration.shared.isVoiceEnabled else {
            print("🎤 UnifiedVoiceService: Voice features disabled")
            return
        }
        
        guard state.canStartListening else {
            print("🎤 UnifiedVoiceService: Cannot start listening in current state: \(state)")
            return
        }
        
        // Check permissions first
        guard permissionManager.isFullyAuthorized else {
            state = .permissionRequired
            return
        }
        
        state = .starting
        
        do {
            switch mode {
            case .pushToTalk:
                try await startPushToTalkListening()
            case .wakeWord:
                try await startWakeWordListening()
            }
        } catch {
            handleError(VoiceError.from(error))
        }
    }
    
    /// Stop voice listening
    func stopListening() {
        guard state.isListening else { return }
        
        speechRecognitionService.stopListening()
        wakePhraseManager.stopWakeListening()
        
        if !recognizedText.isEmpty {
            state = .processing(transcript: recognizedText)
            Task { [weak self] in
                let textToProcess = self?.recognizedText ?? ""
                await self?.processVoiceCommand(textToProcess)
            }
        } else {
            state = .idle
        }
    }
    
    /// Toggle listening state
    func toggleListening(mode: ListeningMode = .pushToTalk) async {
        if state.isListening {
            stopListening()
        } else {
            await startListening(mode: mode)
        }
    }
    
    /// Request voice permissions
    func requestPermissions() async {
        state = .permissionRequired
        
        permissionManager.requestFullPermissions { [weak self] success in
            Task { @MainActor [weak self] in
                if success {
                    self?.state = .idle
                } else {
                    self?.handleError(.permissionDenied)
                }
            }
        }
    }
    
    /// Reset the voice service to idle state
    func reset() {
        stopListening()
        recognizedText = ""
        audioLevel = 0.0
        confidenceScore = 0.0
        state = .idle
    }
    
    // MARK: - Private Implementation
    
    private func setupBindings() {
        // Bind to speech recognition service
        speechRecognitionService.$recognizedText
            .assign(to: &$recognizedText)
        
        speechRecognitionService.$audioLevel
            .assign(to: &$audioLevel)
        
        speechRecognitionService.$confidenceScore
            .assign(to: &$confidenceScore)
        
        speechRecognitionService.$recognitionState
            .sink { [weak self] recognitionState in
                self?.handleSpeechRecognitionStateChange(recognitionState)
            }
            .store(in: &cancellables)
        
        // Bind to wake phrase manager
        wakePhraseManager.$wakePhraseDetected
            .filter { $0 }
            .sink { [weak self] _ in
                self?.handleWakePhraseDetected()
            }
            .store(in: &cancellables)
        
        // Bind to permission manager
        permissionManager.$isFullyAuthorized
            .sink { [weak self] authorized in
                self?.handlePermissionChange(authorized)
            }
            .store(in: &cancellables)
    }
    
    private func startPushToTalkListening() async throws {
        speechRecognitionService.startListening()
        state = .listening(mode: .pushToTalk)
    }
    
    private func startWakeWordListening() async throws {
        wakePhraseManager.startWakeListening()
        state = .listening(mode: .wakeWord)
    }
    
    private func handleSpeechRecognitionStateChange(_ recognitionState: SpeechRecognitionService.RecognitionState) {
        switch recognitionState {
        case .idle:
            if case .listening = state {
                // Keep listening state until explicitly stopped
            } else {
                state = .idle
            }
            
        case .listening:
            // Speech recognition is active
            break
            
        case .processing:
            if !recognizedText.isEmpty {
                state = .processing(transcript: recognizedText)
            }
            
        case .completed:
            if !recognizedText.isEmpty {
                state = .processing(transcript: recognizedText)
                Task { [weak self] in
                    let textToProcess = self?.recognizedText ?? ""
                    await self?.processVoiceCommand(textToProcess)
                }
            } else {
                state = .idle
            }
            
        case .error(let errorMessage):
            handleError(VoiceError.recognitionFailed(errorMessage))
        }
    }
    
    private func handleWakePhraseDetected() {
        guard case .listening(.wakeWord) = state else { return }
        
        // Transition from wake word listening to command listening
        wakePhraseManager.stopWakeListening()
        speechRecognitionService.startListening()
        state = .listening(mode: .pushToTalk)
    }
    
    private func handlePermissionChange(_ authorized: Bool) {
        if !authorized && state.requiresPermissions {
            state = .permissionRequired
        }
    }
    
    private func handleError(_ error: VoiceError) {
        print("🎤 UnifiedVoiceService: Error occurred - \(error.localizedDescription)")
        state = .error(error)
        
        // Auto-recovery for certain errors
        Task { [weak self] in
            try? await Task.sleep(for: .seconds(2))
            await MainActor.run {
                if case .error = self?.state {
                    self?.state = .idle
                }
            }
        }
    }
    
    private func processVoiceCommand(_ command: String) async {
        let processedCommand = preprocessCommand(command)
        
        // Send to voice processor for advanced processing
        await voiceProcessor.processVoiceCommand(processedCommand)
        
        // Send to WebSocket service
        webSocketService.sendCommand(processedCommand)
        
        // Create voice message for history
        let voiceMessage = AgentMessage(
            content: "🎤 Voice: \(command)",
            isFromUser: true,
            type: .command
        )
        
        await MainActor.run {
            webSocketService.messages.append(voiceMessage)
        }
        
        // Reset and return to appropriate listening mode
        speechRecognitionService.resetRecognition()
        
        // Return to wake word listening if that was the previous mode
        if case .listening(.wakeWord) = state {
            wakePhraseManager.startWakeListening()
            state = .listening(mode: .wakeWord)
        } else {
            state = .idle
        }
    }
    
    private func preprocessCommand(_ command: String) -> String {
        let lowercased = command.lowercased().trimmingCharacters(in: .whitespacesAndNewlines)
        
        // Check for exact matches first
        if let mappedCommand = commandMappings[lowercased] {
            return mappedCommand
        }
        
        // Check for partial matches
        for (pattern, mappedCommand) in commandMappings {
            if lowercased.contains(pattern) {
                return mappedCommand
            }
        }
        
        // Return as natural language if no mapping found
        return lowercased
    }
}

// MARK: - Voice State Management

enum VoiceState: Equatable {
    case idle
    case permissionRequired
    case starting
    case listening(mode: ListeningMode)
    case processing(transcript: String)
    case error(VoiceError)
    
    var isListening: Bool {
        if case .listening = self { return true }
        return false
    }
    
    var canStartListening: Bool {
        switch self {
        case .idle, .permissionRequired:
            return true
        default:
            return false
        }
    }
    
    var requiresPermissions: Bool {
        switch self {
        case .listening, .starting:
            return true
        default:
            return false
        }
    }
    
    var displayText: String {
        switch self {
        case .idle:
            return "Ready"
        case .permissionRequired:
            return "Permissions Required"
        case .starting:
            return "Starting..."
        case .listening(let mode):
            switch mode {
            case .pushToTalk:
                return "Listening..."
            case .wakeWord:
                return "Listening for 'Hey LeanVibe'"
            }
        case .processing(let transcript):
            return "Processing: \(transcript)"
        case .error(let error):
            return "Error: \(error.localizedDescription)"
        }
    }
}

enum ListeningMode: Equatable {
    case pushToTalk
    case wakeWord
}

// MARK: - Voice Error Types

enum VoiceError: Error, LocalizedError, Equatable {
    case permissionDenied
    case permissionRestricted
    case audioEngineError(String)
    case recognitionUnavailable
    case recognitionFailed(String)
    case wakePhraseError(String)
    case networkError(String)
    case unknown(String)
    
    var errorDescription: String? {
        switch self {
        case .permissionDenied:
            return "Microphone permission is required for voice commands"
        case .permissionRestricted:
            return "Voice recognition is restricted on this device"
        case .audioEngineError(let message):
            return "Audio system error: \(message)"
        case .recognitionUnavailable:
            return "Speech recognition is currently unavailable"
        case .recognitionFailed(let message):
            return "Recognition failed: \(message)"
        case .wakePhraseError(let message):
            return "Wake phrase detection error: \(message)"
        case .networkError(let message):
            return "Network error: \(message)"
        case .unknown(let message):
            return "Unknown error: \(message)"
        }
    }
    
    static func from(_ error: Error) -> VoiceError {
        if let voiceError = error as? VoiceError {
            return voiceError
        } else if let recognitionError = error as? RecognitionError {
            switch recognitionError {
            case .microphonePermissionDenied:
                return .permissionDenied
            case .speechRecognitionPermissionDenied:
                return .permissionDenied
            case .audioEngineFailure:
                return .audioEngineError("Failed to start audio engine")
            case .recognitionFailed(let message):
                return .recognitionFailed(message)
            }
        } else {
            return .unknown(error.localizedDescription)
        }
    }
}

// MARK: - Public Extensions

extension UnifiedVoiceService {
    
    /// Convenience computed properties for UI bindings
    var isIdle: Bool { state == .idle }
    var isListening: Bool { state.isListening }
    var needsPermissions: Bool { state == .permissionRequired }
    var currentStateText: String { state.displayText }
    
    /// Voice command capabilities check
    var canStartVoiceCommand: Bool {
        permissionManager.isFullyAuthorized && state.canStartListening
    }
}