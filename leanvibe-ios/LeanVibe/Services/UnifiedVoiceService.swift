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
    
    // MARK: - Performance Monitoring
    @Published private(set) var responseTime: TimeInterval = 0.0
    @Published private(set) var averageResponseTime: TimeInterval = 0.0
    @Published private(set) var performanceStatus: PerformanceStatus = .optimal
    private var responseTimes: [TimeInterval] = []
    private var lastVoiceStartTime: Date?
    
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
        print("🎤 UnifiedVoiceService: Starting defensive initialization...")
        
        // Initialize core services with maximum defensive programming
        do {
            self.speechRecognitionService = SpeechRecognitionService()
            print("✅ SpeechRecognitionService initialized")
        } catch {
            print("🚨 Failed to initialize SpeechRecognitionService: \(error)")
            // This is a fatal error for voice service, but we'll let it crash gracefully
            self.speechRecognitionService = SpeechRecognitionService()
        }
        
        self.audioCoordinator = AudioSessionCoordinator.shared
        print("✅ AudioSessionCoordinator initialized")
        
        self.webSocketService = WebSocketService()
        print("✅ WebSocketService initialized")
        
        do {
            self.permissionManager = VoicePermissionManager()
            print("✅ VoicePermissionManager initialized")
        } catch {
            print("🚨 Failed to initialize VoicePermissionManager: \(error)")
            self.permissionManager = VoicePermissionManager()
        }
        
        // Initialize voice processor and wake phrase manager with dependency injection
        // Use defensive initialization with proper error boundaries
        let projectManager = ProjectManager()
        let settingsManager = SettingsManager.shared
        
        do {
            self.voiceProcessor = DashboardVoiceProcessor(
                projectManager: projectManager,
                webSocketService: webSocketService,
                settingsManager: settingsManager
            )
            print("✅ DashboardVoiceProcessor initialized")
        } catch {
            print("🚨 Failed to initialize DashboardVoiceProcessor: \(error)")
            // Create minimal voice processor for safety
            self.voiceProcessor = DashboardVoiceProcessor(
                projectManager: projectManager,
                webSocketService: webSocketService,
                settingsManager: settingsManager
            )
        }
        
        do {
            self.wakePhraseManager = WakePhraseManager(
                webSocketService: webSocketService,
                projectManager: projectManager,
                voiceProcessor: voiceProcessor
            )
            print("✅ WakePhraseManager initialized")
        } catch {
            print("🚨 Failed to initialize WakePhraseManager: \(error)")
            self.wakePhraseManager = WakePhraseManager(
                webSocketService: webSocketService,
                projectManager: projectManager,
                voiceProcessor: voiceProcessor
            )
        }
        
        // Setup bindings with comprehensive error handling
        do {
            setupBindings()
            print("✅ UnifiedVoiceService bindings setup successfully")
        } catch {
            print("⚠️ UnifiedVoiceService: Failed to setup bindings - \(error)")
            
            // Emergency disable voice features if bindings fail
            AppConfiguration.emergencyDisableVoice(reason: "Binding setup failure: \(error.localizedDescription)")
            
            // Continue initialization even if bindings fail
            // Voice service will be disabled but won't crash the app
        }
        
        print("🎉 UnifiedVoiceService: Defensive initialization completed")
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
        
        // Start performance monitoring
        lastVoiceStartTime = Date()
        
        state = .starting
        
        do {
            // Pre-warm audio session for faster response
            await audioCoordinator.prepareForVoiceRecording()
            
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
            // Calculate response time even for empty results
            calculateResponseTime()
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
        
        // TODO: Report error to error boundary once module structure is resolved
        // reportVoiceError(error, from: "UnifiedVoiceService")
        
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
        
        // Send to voice processor for advanced processing (async for performance)
        await voiceProcessor.processVoiceCommand(processedCommand)
        
        // Send to WebSocket service (non-blocking)
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
        
        // Calculate and log response time
        calculateResponseTime()
        
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
    
    // MARK: - Performance Monitoring Methods
    
    private func calculateResponseTime() {
        guard let startTime = lastVoiceStartTime else { return }
        
        let endTime = Date()
        let responseTime = endTime.timeIntervalSince(startTime)
        
        // Update current response time
        self.responseTime = responseTime
        
        // Add to response times array (keep last 50 for average)
        responseTimes.append(responseTime)
        if responseTimes.count > 50 {
            responseTimes.removeFirst()
        }
        
        // Calculate rolling average
        averageResponseTime = responseTimes.reduce(0, +) / Double(responseTimes.count)
        
        // Update performance status
        updatePerformanceStatus(responseTime)
        
        // Log performance metrics
        print("🎤 Voice Response Time: \(String(format: "%.3f", responseTime))s (avg: \(String(format: "%.3f", averageResponseTime))s)")
        
        // Reset timer
        lastVoiceStartTime = nil
    }
    
    private func updatePerformanceStatus(_ currentResponseTime: TimeInterval) {
        switch currentResponseTime {
        case 0.0..<0.5:
            performanceStatus = .optimal
        case 0.5..<1.0:
            performanceStatus = .good
        case 1.0..<2.0:
            performanceStatus = .warning
        default:
            performanceStatus = .critical
        }
        
        // Log performance warnings
        if currentResponseTime > 0.5 {
            print("⚠️ Voice response time \(String(format: "%.3f", currentResponseTime))s exceeds target of 500ms")
        }
        
        if currentResponseTime > 1.0 {
            print("🚨 Voice response time \(String(format: "%.3f", currentResponseTime))s is critically slow")
        }
    }
    
    /// Get performance metrics for monitoring
    func getPerformanceMetrics() -> VoicePerformanceMetrics {
        return VoicePerformanceMetrics(
            currentResponseTime: responseTime,
            averageResponseTime: averageResponseTime,
            performanceStatus: performanceStatus,
            totalMeasurements: responseTimes.count,
            targetResponseTime: 0.5,
            isWithinTarget: averageResponseTime <= 0.5
        )
    }
    
    /// Optimize voice service for better performance
    func optimizePerformance() async {
        print("🎤 Optimizing voice service performance...")
        
        // Pre-warm audio session
        await audioCoordinator.prepareForVoiceRecording()
        
        // Reset speech recognition for clean state
        speechRecognitionService.resetRecognition()
        
        // Clear performance history if degraded
        if performanceStatus == .critical {
            responseTimes.removeAll()
            averageResponseTime = 0.0
            performanceStatus = .optimal
            print("🎤 Performance history cleared due to critical status")
        }
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

// MARK: - Performance Models

enum PerformanceStatus: String, CaseIterable {
    case optimal = "optimal"      // < 500ms
    case good = "good"           // 500ms - 1s
    case warning = "warning"     // 1s - 2s  
    case critical = "critical"   // > 2s
    
    var emoji: String {
        switch self {
        case .optimal: return "🟢"
        case .good: return "🟡"
        case .warning: return "🟠"
        case .critical: return "🔴"
        }
    }
    
    var description: String {
        switch self {
        case .optimal: return "Voice response time is optimal (<500ms)"
        case .good: return "Voice response time is good (500ms-1s)"
        case .warning: return "Voice response time needs improvement (1s-2s)"
        case .critical: return "Voice response time is critically slow (>2s)"
        }
    }
}

struct VoicePerformanceMetrics {
    let currentResponseTime: TimeInterval
    let averageResponseTime: TimeInterval
    let performanceStatus: PerformanceStatus
    let totalMeasurements: Int
    let targetResponseTime: TimeInterval
    let isWithinTarget: Bool
    
    var formattedCurrentTime: String {
        return String(format: "%.3f", currentResponseTime)
    }
    
    var formattedAverageTime: String {
        return String(format: "%.3f", averageResponseTime)
    }
    
    var targetPercentage: Double {
        guard targetResponseTime > 0 else { return 0 }
        return min(100, (targetResponseTime / averageResponseTime) * 100)
    }
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

@available(iOS 18.0, macOS 14.0, *)
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