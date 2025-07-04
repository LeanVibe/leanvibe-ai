import Foundation
import Speech
import AVFoundation
import Combine
import SwiftUI

@available(iOS 18.0, macOS 14.0, *)
@available(*, deprecated, message: "VoiceManager is deprecated. Use VoiceManagerFactory with UnifiedVoiceService instead. See VoiceServiceDeprecationPlan for migration guidance.")
@MainActor
class VoiceManager: ObservableObject {
    @Published var isListening = false
    @Published var currentCommand = ""
    @Published var isProcessing = false
    @Published var lastError: String?
    @Published var recognitionConfidence: Float = 0.0
    @Published var audioLevel: Float = 0.0
    
    private let speechService: SpeechRecognitionService
    private let webSocketService: WebSocketService
    private var cancellables = Set<AnyCancellable>()
    
    init(speechService: SpeechRecognitionService, webSocketService: WebSocketService) {
        self.speechService = speechService
        self.webSocketService = webSocketService
        setupBindings()
    }
    
    deinit {
        // Don't perform async operations in deinit - let the service clean up naturally
        // The SpeechRecognitionService handles its own cleanup in its deinit
    }
    
    private func setupBindings() {
        // Bind speech service state to voice manager state
        speechService.$isListening
            .assign(to: &$isListening)
        
        speechService.$recognizedText
            .assign(to: &$currentCommand)
        
        speechService.$audioLevel
            .assign(to: &$audioLevel)
        
        speechService.$confidenceScore
            .map { Float($0) }
            .assign(to: &$recognitionConfidence)
        
        speechService.$lastError
            .assign(to: &$lastError)
        
        // Process completed recognitions
        speechService.$recognitionState
            .filter { $0 == .completed }
            .sink { [weak self] _ in
                Task { @MainActor [weak self] in
                    await self?.processVoiceCommand()
                }
            }
            .store(in: &cancellables)
    }
    
    func startListening() async {
        guard !isListening else { return }
        
        currentCommand = ""
        lastError = nil
        
        speechService.startListening()
    }
    
    func stopListening() {
        guard isListening else { return }
        speechService.stopListening()
    }
    
    func toggleListening() async {
        if isListening {
            stopListening()
        } else {
            await startListening()
        }
    }
    
    private func processVoiceCommand() async {
        guard !currentCommand.isEmpty else { return }
        
        isProcessing = true
        defer { isProcessing = false }
        
        let processedCommand = preprocessCommand(currentCommand)
        
        // Send command to backend
        webSocketService.sendCommand(processedCommand)
        
        // Log the voice command
        let voiceMessage = AgentMessage(
            content: "🎤 Voice: \(currentCommand)",
            isFromUser: true,
            type: .command
        )
        
        await MainActor.run {
            webSocketService.messages.append(voiceMessage)
        }
        
        // Reset for next command
        speechService.resetRecognition()
    }
    
    private func preprocessCommand(_ command: String) -> String {
        let lowercased = command.lowercased().trimmingCharacters(in: .whitespacesAndNewlines)
        
        // Basic command mappings
        let commandMappings: [String: String] = [
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
        
        // Check for exact matches
        if let mappedCommand = commandMappings[lowercased] {
            return mappedCommand
        }
        
        // Check for partial matches
        for (pattern, command) in commandMappings {
            if lowercased.contains(pattern) {
                return command
            }
        }
        
        // Return as natural language if no mapping found
        return lowercased
    }
    
    // Public interface for voice command capabilities
    var canStartListening: Bool {
        return !isListening && !isProcessing
    }
    
    var isActive: Bool {
        return isListening || isProcessing
    }
}