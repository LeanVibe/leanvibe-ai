import Foundation
import Speech
import SwiftUI

@available(iOS 14.0, macOS 11.0, *)
@MainActor
class CommandAndControlService: NSObject, ObservableObject, SFSpeechRecognizerDelegate {
    
    private let projectManager: ProjectManager
    private let webSocketService: WebSocketService
    private let settingsManager: SettingsManager
    private let commandProcessor: VoiceCommandProcessor
    
    @Published var lastCommand: VoiceCommand?
    @Published var isProcessing = false
    
    private let speechRecognizer: SFSpeechRecognizer?
    private var recognitionRequest: SFSpeechAudioBufferRecognitionRequest?
    private var recognitionTask: SFSpeechRecognitionTask?
    private let audioEngine = AVAudioEngine()
    
    init(projectManager: ProjectManager, webSocketService: WebSocketService, settingsManager: SettingsManager) {
        self.projectManager = projectManager
        self.webSocketService = webSocketService
        self.settingsManager = settingsManager
        self.commandProcessor = VoiceCommandProcessor(settings: settingsManager.voice)
        self.speechRecognizer = SFSpeechRecognizer(locale: Locale(identifier: "en-US"))
        
        super.init()
        
        speechRecognizer?.delegate = self
    }
    
    func startListening() {
        guard !audioEngine.isRunning else { return }
        
        let recognitionRequest = SFSpeechAudioBufferRecognitionRequest()
        self.recognitionRequest = recognitionRequest
        
        recognitionRequest.shouldReportPartialResults = true
        
        guard let speechRecognizer = speechRecognizer else { return }
        
        recognitionTask = speechRecognizer.recognitionTask(with: recognitionRequest) { [weak self] result, error in
            guard let self = self else { return }
            
            if let result = result, result.isFinal {
                Task {
                    await self.processVoiceCommand(result.bestTranscription.formattedString)
                }
                self.stopListening()
            }
        }
        
        let inputNode = audioEngine.inputNode
        let recordingFormat = inputNode.outputFormat(forBus: 0)
        inputNode.installTap(onBus: 0, bufferSize: 1024, format: recordingFormat) { buffer, _ in
            self.recognitionRequest?.append(buffer)
        }
        
        audioEngine.prepare()
        
        do {
            try audioEngine.start()
        } catch {
            print("audioEngine couldn't start because of an error: \(error.localizedDescription)")
        }
    }
    
    func stopListening() {
        if audioEngine.isRunning {
            audioEngine.stop()
            recognitionRequest?.endAudio()
            audioEngine.inputNode.removeTap(onBus: 0)
        }
        recognitionTask?.cancel()
        recognitionTask = nil
        recognitionRequest = nil
    }
    
    func processVoiceCommand(_ transcription: String) async {
        isProcessing = true
        defer { isProcessing = false }
        
        let command = commandProcessor.processVoiceInput(transcription)
        lastCommand = command
        
        // Execute dashboard-specific commands
        await executeCommand(command)
        
        // Send to WebSocket as fallback
        sendToWebSocket(command)
    }
    
    private func executeCommand(_ command: VoiceCommand) async {
        switch command.intent {
        case .project:
            await handleProjectCommand(command)
        case .navigation:
            handleNavigationCommand(command)
        case .status:
            await handleStatusCommand(command)
        default:
            // Handle generic commands through WebSocket
            break
        }
    }
    
    private func handleProjectCommand(_ command: VoiceCommand) async {
        let processedCommand = command.processedCommand.lowercased()
        
        if processedCommand.contains("analyze") {
            await analyzeCurrentProjects()
        } else if processedCommand.contains("refresh") {
            await refreshDashboard()
        } else if processedCommand.contains("status") || processedCommand.contains("health") {
            showProjectStatus()
        } else if processedCommand.contains("switch") || processedCommand.contains("change") {
            // Could trigger project selection UI
            sendFeedbackMessage("📁 Project switching interface would open here")
        }
    }
    
    private func handleNavigationCommand(_ command: VoiceCommand) {
        let processedCommand = command.processedCommand.lowercased()
        
        if processedCommand.contains("dashboard") || processedCommand.contains("home") {
            // Navigate to projects tab (index 0)
            sendFeedbackMessage("🏠 Navigating to dashboard...")
        } else if processedCommand.contains("monitoring") || processedCommand.contains("monitor") {
            // Navigate to monitoring tab (index 2)
            sendFeedbackMessage("📊 Navigating to monitoring...")
        } else if processedCommand.contains("settings") {
            // Navigate to settings tab (index 3)
            sendFeedbackMessage("⚙️ Navigating to settings...")
        }
    }
    
    private func handleStatusCommand(_ command: VoiceCommand) async {
        let activeProjects = projectManager.projects.filter { $0.status == .active }
        let totalProjects = projectManager.projects.count
        
        let statusMessage = """
        📊 Dashboard Status:
        • \(totalProjects) total projects
        • \(activeProjects.count) active projects
        • Connection: \(webSocketService.isConnected ? "Connected" : "Disconnected")
        """
        
        sendFeedbackMessage(statusMessage)
    }
    
    private func analyzeCurrentProjects() async {
        let activeProjects = projectManager.projects.filter { $0.status == .active }
        
        if activeProjects.isEmpty {
            sendFeedbackMessage("🔍 No active projects to analyze")
            return
        }
        
        sendFeedbackMessage("🔍 Analyzing \(activeProjects.count) active project(s)...")
        
        for project in activeProjects {
            await projectManager.analyzeProject(project)
        }
        
        sendFeedbackMessage("✅ Project analysis started")
    }
    
    private func refreshDashboard() async {
        sendFeedbackMessage("🔄 Refreshing dashboard...")
        
        await projectManager.refreshProjects()
        
        sendFeedbackMessage("✅ Dashboard refreshed")
    }
    
    private func showProjectStatus() {
        let projects = projectManager.projects
        
        if projects.isEmpty {
            sendFeedbackMessage("📁 No projects found")
            return
        }
        
        let activeCount = projects.filter { $0.status == .active }.count
        let inactiveCount = projects.count - activeCount
        
        var statusMessage = "📁 Project Status:\n"
        statusMessage += "• Active: \(activeCount)\n"
        statusMessage += "• Inactive: \(inactiveCount)\n"
        
        // Show health summary
        let healthyProjects = projects.filter { $0.metrics.healthScore > 0.8 }.count
        let warningProjects = projects.filter { $0.metrics.healthScore > 0.6 && $0.metrics.healthScore <= 0.8 }.count
        let criticalProjects = projects.filter { $0.metrics.healthScore <= 0.6 }.count
        
        statusMessage += "• Healthy: \(healthyProjects)\n"
        statusMessage += "• Warning: \(warningProjects)\n"
        statusMessage += "• Critical: \(criticalProjects)"
        
        sendFeedbackMessage(statusMessage)
    }
    
    private func sendToWebSocket(_ command: VoiceCommand) {
        // Create voice command message
        let voiceMessage = VoiceCommandMessage(
            voiceCommand: command,
            clientId: "ios-dashboard"
        )
        
        do {
            let data = try JSONEncoder().encode(voiceMessage)
            let jsonString = String(data: data, encoding: .utf8) ?? ""
            webSocketService.sendMessage(jsonString, type: "voice_command")
        } catch {
            // Fallback to simple command
            webSocketService.sendMessage(command.processedCommand, type: "voice_command")
        }
    }
    
    private func sendFeedbackMessage(_ content: String) {
        let feedbackMessage = AgentMessage(
            content: content,
            isFromUser: false,
            type: .response
        )
        webSocketService.messages.append(feedbackMessage)
    }
} 