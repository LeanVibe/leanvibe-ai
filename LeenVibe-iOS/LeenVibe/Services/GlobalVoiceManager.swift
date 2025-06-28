import SwiftUI
import Foundation
import Combine

@MainActor
class GlobalVoiceManager: ObservableObject {
    @Published var isListening = false
    @Published var isVoiceCommandActive = false
    @Published var voiceCommandText = ""
    @Published var isWakeListening = false
    
    private let wakePhraseManager: WakePhraseManager
    private let speechRecognition: SpeechRecognitionService
    private let permissionManager = VoicePermissionManager()
    private let voiceProcessor: DashboardVoiceProcessor
    
    private var cancellables = Set<AnyCancellable>()
    
    init(webSocketService: WebSocketService, projectManager: ProjectManager) {
        self.voiceProcessor = DashboardVoiceProcessor(
            projectManager: projectManager,
            webSocketService: webSocketService
        )
        
        self.wakePhraseManager = WakePhraseManager(
            webSocketService: webSocketService,
            projectManager: projectManager,
            voiceProcessor: voiceProcessor
        )
        
        self.speechRecognition = SpeechRecognitionService(webSocketService: webSocketService)
        
        setupVoiceObservers()
    }
    
    private func setupVoiceObservers() {
        // Observe wake phrase detection
        wakePhraseManager.$wakePhraseDetected
            .sink { [weak self] detected in
                if detected {
                    self?.triggerVoiceCommand()
                }
            }
            .store(in: &cancellables)
        
        // Observe wake listening state
        wakePhraseManager.$isWakeListening
            .sink { [weak self] listening in
                self?.isWakeListening = listening
            }
            .store(in: &cancellables)
    }
    
    func startGlobalVoiceListening() {
        guard permissionManager.isFullyAuthorized else {
            print("Voice permissions not granted")
            return
        }
        
        wakePhraseManager.startWakeListening()
    }
    
    func stopGlobalVoiceListening() {
        wakePhraseManager.stopWakeListening()
    }
    
    func triggerVoiceCommand() {
        isVoiceCommandActive = true
        voiceCommandText = ""
        
        // Stop wake listening temporarily
        wakePhraseManager.stopWakeListening()
        
        // Start listening for command
        speechRecognition.startListening { [weak self] result in
            DispatchQueue.main.async {
                switch result {
                case .success(let text):
                    self?.voiceCommandText = text
                    Task {
                        await self?.processVoiceCommand(text)
                    }
                case .failure(let error):
                    print("Voice recognition error: \(error)")
                    self?.dismissVoiceCommand()
                }
            }
        }
    }
    
    func dismissVoiceCommand() {
        isVoiceCommandActive = false
        voiceCommandText = ""
        speechRecognition.stopListening()
        
        // Resume wake phrase listening after a short delay
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            if self.permissionManager.isFullyAuthorized {
                self.wakePhraseManager.startWakeListening()
            }
        }
    }
    
    private func processVoiceCommand(_ command: String) async {
        // Process the voice command through the voice processor
        await voiceProcessor.processVoiceCommand(command)
        
        // Dismiss the voice interface after processing
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
            self.dismissVoiceCommand()
        }
    }
    
    // MARK: - Voice Status
    
    var voiceStatus: VoiceStatus {
        if !permissionManager.isFullyAuthorized {
            return .noPermission
        } else if isVoiceCommandActive {
            return .activeCommand
        } else if isWakeListening {
            return .listening
        } else {
            return .inactive
        }
    }
    
    enum VoiceStatus {
        case noPermission
        case inactive
        case listening
        case activeCommand
        
        var description: String {
            switch self {
            case .noPermission:
                return "No Permission"
            case .inactive:
                return "Voice Inactive"
            case .listening:
                return "Listening for 'Hey LeenVibe'"
            case .activeCommand:
                return "Voice Command Active"
            }
        }
        
        var color: Color {
            switch self {
            case .noPermission:
                return .red
            case .inactive:
                return .gray
            case .listening:
                return .green
            case .activeCommand:
                return .blue
            }
        }
    }
}

import Combine