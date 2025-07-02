import SwiftUI
import Foundation
import Combine

@available(iOS 18.0, macOS 14.0, *)
@available(*, deprecated, message: "GlobalVoiceManager is deprecated. Use VoiceManagerFactory with UnifiedVoiceService instead. See VoiceServiceDeprecationPlan for migration guidance.")
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
    
    init(webSocketService: WebSocketService, projectManager: ProjectManager, settingsManager: SettingsManager) {
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
        
        self.speechRecognition = SpeechRecognitionService()
        
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
        
        // Observe recognition completion
        speechRecognition.$recognitionState
            .sink { [weak self] state in
                guard let self = self else { return }
                switch state {
                case .completed:
                    let text = self.speechRecognition.recognizedText
                    self.voiceCommandText = text
                    Task { await self.processVoiceCommand(text) }
                case .error(let error):
                    print("Voice recognition error: \(error)")
                    self.dismissVoiceCommand()
                default:
                    break
                }
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
        speechRecognition.startListening()
    }
    
    func dismissVoiceCommand() {
        isVoiceCommandActive = false
        voiceCommandText = ""
        speechRecognition.stopListening()
        
        // Resume wake phrase listening after a short delay
        Task { @MainActor in
            try? await Task.sleep(for: .milliseconds(500))
            if permissionManager.isFullyAuthorized {
                wakePhraseManager.startWakeListening()
            }
        }
    }
    
    private func processVoiceCommand(_ command: String) async {
        // Process the voice command through the voice processor
        await voiceProcessor.processVoiceCommand(command)
        
        // Dismiss the voice interface after processing
        Task { @MainActor in
            try? await Task.sleep(for: .seconds(1))
            dismissVoiceCommand()
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
                return "Listening for 'Hey LeanVibe'"
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