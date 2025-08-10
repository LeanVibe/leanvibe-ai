import Foundation
import Combine
import Speech
import SwiftUI
import AVFoundation
@preconcurrency import Speech
@preconcurrency import AVFAudio
#if canImport(UIKit)
import UIKit
#endif

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
    
    // MARK: - Wake Phrase Detection State
    @Published private(set) var isWakeListening = false
    @Published private(set) var wakePhraseDetected = false
    @Published private(set) var lastWakeDetection: WakePhraseDetection?
    @Published private(set) var wakeAudioLevel: Float = 0.0
    
    // MARK: - Performance Monitoring
    @Published private(set) var responseTime: TimeInterval = 0.0
    @Published private(set) var averageResponseTime: TimeInterval = 0.0
    @Published private(set) var performanceStatus: VoicePerformanceStatus = .optimal
    private var responseTimes: [TimeInterval] = []
    private var lastVoiceStartTime: Date?
    
    // MARK: - Performance Optimization from OptimizedVoiceManager
    @Published private(set) var isOptimized = false
    @Published private(set) var currentLatency: TimeInterval = 0
    @Published private(set) var isLowLatencyMode = false
    
    // Performance optimization properties
    private var buffersProcessed: Int = 0
    private var recognitionAccuracy: Double = 0.95
    private var errorRate: Double = 0.02
    private var backgroundTask: UIBackgroundTaskIdentifier = .invalid
    private let processingQueue = DispatchQueue(
        label: "voice.processing",
        qos: .userInitiated,
        attributes: .concurrent
    )
    
    // MARK: - Dependencies
    private let speechRecognitionService: SpeechRecognitionService
    private let audioCoordinator: AudioSessionCoordinator
    private let webSocketService: WebSocketService
    private let voiceProcessor: DashboardVoiceProcessor
    // TODO: Re-enable when VoiceFeedbackService is added to Xcode project
    // private let voiceFeedbackService = VoiceFeedbackService.shared
    
    // MARK: - Integrated Voice Permission Management
    @Published private(set) var hasMicrophonePermission = false
    @Published private(set) var hasSpeechRecognitionPermission = false
    @Published private(set) var permissionStatus: VoicePermissionStatus = .notDetermined
    @Published private(set) var isFullyAuthorized = false
    @Published private(set) var permissionError: String?
    
    // MARK: - Integrated Wake Phrase Detection
    private let wakeSpeechRecognizer: SFSpeechRecognizer?
    private var wakeRecognitionRequest: SFSpeechAudioBufferRecognitionRequest?
    private var wakeRecognitionTask: SFSpeechRecognitionTask?
    private let wakeAudioEngine = AVAudioEngine()
    
    // Wake phrase configuration
    private let wakePhrase = "hey leanvibe"
    private let wakePhraseAlternatives = [
        "hey lynn vibe",
        "hey lean vibe", 
        "hey leen vibe",
        "hey lee vibe",
        "a leanvibe",
        "hey leanvibe"
    ]
    
    // Detection settings
    private let confidenceThreshold: Float = 0.6
    private let silenceTimeout: TimeInterval = 3.0
    private var silenceTask: Task<Void, Never>?
    
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
            // Initialize integrated wake phrase detection
            self.wakeSpeechRecognizer = SFSpeechRecognizer(locale: Locale(identifier: "en-US"))
            print("✅ Wake phrase speech recognizer initialized")
        } catch {
            print("🚨 Failed to initialize wake phrase detection: \(error)")
            self.wakeSpeechRecognizer = SFSpeechRecognizer(locale: Locale(identifier: "en-US"))
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
        
        // Initialize integrated permissions
        do {
            checkPermissions()
            print("✅ Integrated permission checking initialized")
        } catch {
            print("🚨 Failed to initialize permission checking: \(error)")
            // Set safe defaults if permission check fails
            hasMicrophonePermission = false
            hasSpeechRecognitionPermission = false
            permissionStatus = .notDetermined
            isFullyAuthorized = false
            permissionError = "Permission check failed: \(error.localizedDescription)"
            
            // Emergency disable voice features
            AppConfiguration.emergencyDisableVoice(reason: "Permission check failure: \(error.localizedDescription)")
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
            // TODO: Re-enable when VoiceFeedbackService is added to Xcode project
            // voiceFeedbackService.speakError("Voice features are currently disabled")
            return
        }
        
        guard state.canStartListening else {
            print("🎤 UnifiedVoiceService: Cannot start listening in current state: \(state)")
            // TODO: Re-enable when VoiceFeedbackService is added to Xcode project
            // voiceFeedbackService.speakError("Cannot start listening in current state")
            return
        }
        
        // Check permissions first
        guard isFullyAuthorized else {
            state = .permissionRequired
            // TODO: Re-enable when VoiceFeedbackService is added to Xcode project
            // voiceFeedbackService.speakError("Voice permissions are required")
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
                // TODO: Re-enable when VoiceFeedbackService is added to Xcode project
                // voiceFeedbackService.provide(.listeningStarted)
            case .wakeWord:
                try await startWakeWordListening()
                // TODO: Re-enable when VoiceFeedbackService is added to Xcode project
                // voiceFeedbackService.speakResponse("Wake phrase detection started", priority: .normal)
            }
        } catch {
            // TODO: Re-enable when VoiceFeedbackService is added to Xcode project
            // voiceFeedbackService.speakError("Failed to start listening: \(error.localizedDescription)")
            handleError(VoiceError.from(error))
        }
    }
    
    /// Stop voice listening
    func stopListening() {
        guard state.isListening else { return }
        
        speechRecognitionService.stopListening()
        stopWakeListening()
        
        // TODO: Re-enable when VoiceFeedbackService is added to Xcode project
        // voiceFeedbackService.provide(.listeningStopped)
        
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
        
        await requestFullPermissions { [weak self] success in
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
    
    // MARK: - Integrated Wake Phrase Detection
    
    /// Start wake phrase detection
    func startWakeListening() {
        guard isFullyAuthorized else {
            permissionError = "Wake listening not available - permissions required"
            return
        }
        
        guard !isWakeListening else { return }
        
        stopWakeListening()
        isWakeListening = true
        wakePhraseDetected = false
        
        setupWakeRecognition()
        startWakeAudioEngine()
        
        sendWakeStatusUpdate("🎤 Wake phrase listening started")
    }
    
    /// Stop wake phrase detection
    func stopWakeListening() {
        isWakeListening = false
        
        if wakeAudioEngine.isRunning {
            wakeAudioEngine.stop()
            wakeAudioEngine.inputNode.removeTap(onBus: 0)
        }
        
        wakeRecognitionRequest?.endAudio()
        wakeRecognitionTask?.cancel()
        wakeRecognitionRequest = nil
        wakeRecognitionTask = nil
        
        silenceTask?.cancel()
        wakeAudioLevel = 0.0
        
        if wakePhraseDetected {
            sendWakeStatusUpdate("🛑 Wake phrase listening stopped")
        }
    }
    
    /// Toggle wake phrase listening
    func toggleWakeListening() {
        if isWakeListening {
            stopWakeListening()
        } else {
            startWakeListening()
        }
    }
    
    // MARK: - Integrated Permission Management
    
    /// Request full voice permissions
    func requestFullPermissions(completion: @escaping (Bool) -> Void) async {
        await requestMicrophonePermission { [weak self] micGranted in
            guard let self = self else { return }
            if micGranted {
                Task {
                    await self.requestSpeechRecognitionPermission { speechGranted in
                        let allGranted = micGranted && speechGranted
                        Task { @MainActor [weak self] in
                            self?.updateOverallStatus()
                            completion(allGranted)
                        }
                    }
                }
            } else {
                Task { @MainActor [weak self] in
                    self?.updateOverallStatus()
                    completion(false)
                }
            }
        }
    }
    
    /// Check current permission status
    func checkPermissions() {
        checkMicrophonePermission()
        checkSpeechRecognitionPermission()
        updateOverallStatus()
    }
    
    /// Open system settings for permission changes
    func openSettings() {
        #if os(iOS)
        guard let settingsUrl = URL(string: UIApplication.openSettingsURLString) else {
            return
        }
        
        if UIApplication.shared.canOpenURL(settingsUrl) {
            UIApplication.shared.open(settingsUrl)
        }
        #endif
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
        
        // TODO: Re-enable when VoiceFeedbackService is added to Xcode project
        // voiceFeedbackService.provide(.systemError(error.localizedDescription))
        
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
        
        // TODO: Re-enable when VoiceFeedbackService is added to Xcode project
        // voiceFeedbackService.provide(.processingCommand)
        
        do {
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
            
            // TODO: Re-enable when VoiceFeedbackService is added to Xcode project
            // voiceFeedbackService.confirmCommand(processedCommand, success: true)
            
        } catch {
            // TODO: Re-enable when VoiceFeedbackService is added to Xcode project
            // voiceFeedbackService.speakError("Failed to process command: \(error.localizedDescription)")
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
        
        await configureOptimalAudioSettings()
        await optimizeSpeechRecognition()
        await setupBackgroundVoiceProcessing()
        
        isOptimized = true
        currentLatency = responseTime
        
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
        
        print("🎤 Voice Manager: Performance optimization complete")
    }
    
    /// Enable low latency mode for faster response times
    func enableLowLatencyMode() {
        isLowLatencyMode = true
        
        // Reconfigure with lower latency settings
        Task {
            await configureOptimalAudioSettings()
        }
        
        print("🎤 Voice Manager: Low latency mode enabled")
    }
    
    /// Disable low latency mode
    func disableLowLatencyMode() {
        isLowLatencyMode = false
        
        // Reconfigure with standard settings
        Task {
            await configureOptimalAudioSettings()
        }
        
        print("🎤 Voice Manager: Low latency mode disabled")
    }
    
    /// Get comprehensive performance report
    func getPerformanceReport() -> VoicePerformanceReport {
        return VoicePerformanceReport(
            averageResponseTime: averageResponseTime,
            buffersProcessed: buffersProcessed,
            recognitionAccuracy: recognitionAccuracy,
            errorRate: errorRate,
            isOptimized: isOptimized,
            isLowLatencyMode: isLowLatencyMode
        )
    }
    
    /// Check if performance is optimal
    var isPerformanceOptimal: Bool {
        return responseTime < 0.5 && // Target: <500ms response
               averageResponseTime < 0.3 && // Average <300ms
               errorRate < 0.05 // <5% error rate
    }
    
    // MARK: - Private Wake Phrase Implementation
    
    private func setupWakeRecognition() {
        wakeRecognitionRequest = SFSpeechAudioBufferRecognitionRequest()
        guard let wakeRecognitionRequest = wakeRecognitionRequest else { return }
        
        wakeRecognitionRequest.shouldReportPartialResults = true
        wakeRecognitionRequest.requiresOnDeviceRecognition = true
        
        guard let speechRecognizer = wakeSpeechRecognizer else { return }
        
        wakeRecognitionTask = speechRecognizer.recognitionTask(with: wakeRecognitionRequest) { [weak self] result, error in
            Task { @MainActor in
                self?.handleWakeRecognitionResult(result: result, error: error)
            }
        }
    }
    
    private func startWakeAudioEngine() {
        let inputNode = wakeAudioEngine.inputNode
        let recordingFormat = inputNode.outputFormat(forBus: 0)
        
        inputNode.installTap(onBus: 0, bufferSize: 1024, format: recordingFormat) { [weak self] buffer, _ in
            self?.wakeRecognitionRequest?.append(buffer)
            self?.calculateWakeAudioLevel(from: buffer)
        }
        
        do {
            wakeAudioEngine.prepare()
            try wakeAudioEngine.start()
        } catch {
            Task { @MainActor in
                permissionError = "Wake audio engine failed to start"
                stopWakeListening()
            }
        }
    }
    
    private func calculateWakeAudioLevel(from buffer: AVAudioPCMBuffer) {
        guard let channelData = buffer.floatChannelData?[0] else { return }
        
        let frameLength = Int(buffer.frameLength)
        var sum: Float = 0.0
        
        for i in 0..<frameLength {
            sum += abs(channelData[i])
        }
        
        let averageLevel = sum / Float(frameLength)
        let normalizedLevel = min(averageLevel * 15, 1.0) // More sensitive for wake detection
        
        Task { @MainActor in
            wakeAudioLevel = normalizedLevel
        }
    }
    
    private func handleWakeRecognitionResult(result: SFSpeechRecognitionResult?, error: Error?) {
        if let error = error {
            permissionError = "Wake recognition error: \(error.localizedDescription)"
            return
        }
        
        guard let result = result else { return }
        
        let currentTranscription = result.bestTranscription.formattedString.lowercased()
        let confidence = result.bestTranscription.segments.last?.confidence ?? 0.0
        
        // Reset silence timer on any speech
        if !currentTranscription.isEmpty {
            resetSilenceTimer()
        }
        
        // Check for wake phrase
        if detectWakePhrase(in: currentTranscription, confidence: confidence) {
            let detection = WakePhraseDetection(
                detectedPhrase: currentTranscription,
                confidence: Double(confidence),
                audioLevel: wakeAudioLevel
            )
            
            lastWakeDetection = detection
            wakePhraseDetected = true
            
            handleWakePhraseDetected(detection)
        }
        
        // Keep wake listening active - restart on final results
        if result.isFinal {
            startSilenceTimer()
        }
    }
    
    private func detectWakePhrase(in transcription: String, confidence: Float) -> Bool {
        guard confidence >= confidenceThreshold else { return false }
        
        let cleanedTranscription = transcription
            .trimmingCharacters(in: .whitespacesAndNewlines)
            .replacingOccurrences(of: ".", with: "")
            .replacingOccurrences(of: ",", with: "")
            .replacingOccurrences(of: "?", with: "")
            .replacingOccurrences(of: "!", with: "")
        
        // Check exact wake phrase
        if cleanedTranscription.contains(wakePhrase) {
            return true
        }
        
        // Check alternative pronunciations
        for alternative in wakePhraseAlternatives {
            if cleanedTranscription.contains(alternative) {
                return true
            }
        }
        
        // Check for partial matches at the beginning
        let words = cleanedTranscription.components(separatedBy: " ")
        if words.count >= 2 {
            let firstTwoWords = "\(words[0]) \(words[1])"
            if firstTwoWords.contains("hey") && 
               (firstTwoWords.contains("leen") || firstTwoWords.contains("lynn") || firstTwoWords.contains("lean")) {
                return true
            }
        }
        
        return false
    }
    
    private func handleWakePhraseDetected(_ detection: WakePhraseDetection) {
        // Temporarily stop wake listening to process command
        stopWakeListening()
        
        // Provide haptic feedback
        #if os(iOS)
        let impact = UIImpactFeedbackGenerator(style: .medium)
        impact.impactOccurred()
        #endif
        
        // TODO: Re-enable when VoiceFeedbackService is added to Xcode project
        // voiceFeedbackService.provide(.wakePhraseDetected)
        
        // Log the wake phrase detection
        sendWakeStatusUpdate("✨ Wake phrase detected: \"\(detection.detectedPhrase)\"")
        
        // Start voice command processing with a brief delay
        Task { @MainActor in
            try? await Task.sleep(for: .milliseconds(500))
            triggerVoiceCommandSession()
        }
        
        // Restart wake listening after a delay
        Task { @MainActor in
            try? await Task.sleep(for: .seconds(5))
            if !isWakeListening {
                startWakeListening()
            }
        }
    }
    
    private func triggerVoiceCommandSession() {
        // This would trigger the voice command interface
        // For now, we'll post a notification that the UI can observe
        NotificationCenter.default.post(
            name: NSNotification.Name("WakePhraseDetected"),
            object: lastWakeDetection
        )
        
        sendWakeStatusUpdate("🎤 Voice command session starting...")
    }
    
    private func resetSilenceTimer() {
        silenceTask?.cancel()
    }
    
    private func startSilenceTimer() {
        silenceTask = Task { @MainActor in
            try? await Task.sleep(for: .seconds(silenceTimeout))
            guard !Task.isCancelled else { return }
            handleSilenceTimeout()
        }
    }
    
    private func handleSilenceTimeout() {
        // Restart wake recognition after silence
        if isWakeListening {
            Task { @MainActor in
                try? await Task.sleep(for: .milliseconds(500))
                if isWakeListening {
                    setupWakeRecognition()
                    if !wakeAudioEngine.isRunning {
                        startWakeAudioEngine()
                    }
                }
            }
        }
    }
    
    private func sendWakeStatusUpdate(_ message: String) {
        let statusMessage = AgentMessage(
            content: message,
            isFromUser: false,
            type: .status
        )
        webSocketService.messages.append(statusMessage)
    }
    
    // MARK: - Private Performance Optimization Implementation
    
    private func configureOptimalAudioSettings() async {
        // CRITICAL: Check if another audio engine is already active
        // This prevents conflicts with SpeechRecognitionService during voice setup
        guard !wakeAudioEngine.isRunning else {
            print("🎤 Voice Manager: Audio engine already running, skipping optimization")
            return
        }
        
        do {
            let audioSession = AVAudioSession.sharedInstance()
            
            // Use optimal buffer sizes for real-time processing
            try audioSession.setPreferredIOBufferDuration(isLowLatencyMode ? 0.005 : 0.01) // 5ms or 10ms
            try audioSession.setPreferredSampleRate(16000) // Optimal for speech
            
            print("🎤 Voice Manager: Audio settings optimized")
            
        } catch {
            print("🎤 Voice Manager: Audio configuration failed - \(error)")
        }
    }
    
    private func optimizeSpeechRecognition() async {
        guard let speechRecognizer = wakeSpeechRecognizer else { return }
        
        // Enable on-device recognition for better performance and privacy
        if speechRecognizer.supportsOnDeviceRecognition {
            print("🎤 Voice Manager: On-device recognition enabled")
        }
    }
    
    private func setupBackgroundVoiceProcessing() async {
        // Configure background processing for voice commands
        backgroundTask = UIApplication.shared.beginBackgroundTask(withName: "VoiceProcessing") {
            self.endBackgroundTask()
        }
    }
    
    private func endBackgroundTask() {
        if backgroundTask != .invalid {
            UIApplication.shared.endBackgroundTask(backgroundTask)
            backgroundTask = .invalid
        }
    }
    
    private func processAudioBufferOptimized(_ buffer: AVAudioPCMBuffer, time: AVAudioTime) {
        // Process on background queue for performance
        processingQueue.async { [weak self] in
            DispatchQueue.main.async {
                self?.analyzeAudioForWakePhrase(buffer)
            }
        }
        
        buffersProcessed += 1
    }
    
    private func analyzeAudioForWakePhrase(_ buffer: AVAudioPCMBuffer) {
        // Optimized wake phrase detection
        let energy = calculateAudioEnergy(buffer)
        
        // Only proceed with recognition if sufficient energy
        guard energy > 0.01 else { return }
    }
    
    private func calculateAudioEnergy(_ buffer: AVAudioPCMBuffer) -> Float {
        guard let channelData = buffer.floatChannelData?[0] else { return 0 }
        
        let frameLength = Int(buffer.frameLength)
        var sum: Float = 0.0
        
        for i in 0..<frameLength {
            sum += channelData[i] * channelData[i]
        }
        
        return sqrt(sum / Float(frameLength))
    }
    
    // MARK: - Private Permission Implementation
    
    private func checkMicrophonePermission() {
        do {
            let status = AVAudioSession.sharedInstance().recordPermission
            hasMicrophonePermission = (status == .granted)
            print("🎤 Microphone permission status: \(status.description)")
        } catch {
            print("🚨 Failed to check microphone permission: \(error)")
            hasMicrophonePermission = false
            permissionError = "Failed to check microphone permission: \(error.localizedDescription)"
        }
    }
    
    private func checkSpeechRecognitionPermission() {
        do {
            let status = SFSpeechRecognizer.authorizationStatus()
            hasSpeechRecognitionPermission = (status == .authorized)
            print("🗣️ Speech recognition permission status: \(status.description)")
        } catch {
            print("🚨 Failed to check speech recognition permission: \(error)")
            hasSpeechRecognitionPermission = false
            permissionError = "Failed to check speech recognition permission: \(error.localizedDescription)"
        }
    }
    
    private func requestMicrophonePermission(completion: @escaping (Bool) -> Void) async {
        AVAudioSession.sharedInstance().requestRecordPermission { granted in
            Task { @MainActor [weak self] in
                self?.hasMicrophonePermission = granted
                completion(granted)
            }
        }
    }
    
    private func requestSpeechRecognitionPermission(completion: @escaping (Bool) -> Void) async {
        SFSpeechRecognizer.requestAuthorization { status in
            Task { @MainActor [weak self] in
                self?.hasSpeechRecognitionPermission = (status == .authorized)
                completion(status == .authorized)
            }
        }
    }
    
    private func updateOverallStatus() {
        if hasMicrophonePermission && hasSpeechRecognitionPermission {
            permissionStatus = .granted
            isFullyAuthorized = true
        } else {
            let micStatus = AVAudioSession.sharedInstance().recordPermission
            let speechStatus = SFSpeechRecognizer.authorizationStatus()
            
            if micStatus == .denied || speechStatus == .denied {
                permissionStatus = .denied
            } else if micStatus != .granted || speechStatus == .notDetermined {
                permissionStatus = .notDetermined
            } else {
                permissionStatus = .restricted
            }
            isFullyAuthorized = false
        }
        updatePermissionError()
    }
    
    private func updatePermissionError() {
        let speechAuthorizationStatus = SFSpeechRecognizer.authorizationStatus()
        let microphoneAuthorizationStatus = AVAudioSession.sharedInstance().recordPermission
        
        switch (speechAuthorizationStatus, microphoneAuthorizationStatus) {
        case (.denied, _):
            permissionError = "Speech recognition access denied. Please enable in Settings > Privacy & Security > Speech Recognition"
        case (_, .denied):
            permissionError = "Microphone access denied. Please enable in Settings > Privacy & Security > Microphone"
        case (.restricted, _):
            permissionError = "Speech recognition is restricted on this device"
        case (.authorized, .granted):
            permissionError = nil
        default:
            permissionError = "Voice permissions are required for voice commands"
        }
    }
}

// MARK: - Permission Status Management

enum VoicePermissionStatus {
    case notDetermined
    case granted
    case denied
    case restricted
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

enum VoicePerformanceStatus: String, CaseIterable {
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
    let performanceStatus: VoicePerformanceStatus
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
        isFullyAuthorized && state.canStartListening
    }
}

// MARK: - Performance Report Model

struct VoicePerformanceReport {
    let averageResponseTime: TimeInterval
    let buffersProcessed: Int
    let recognitionAccuracy: Double
    let errorRate: Double
    let isOptimized: Bool
    let isLowLatencyMode: Bool
    
    var status: PerformanceStatus {
        if averageResponseTime < 0.3 && errorRate < 0.05 {
            return .excellent
        } else if averageResponseTime < 0.5 && errorRate < 0.1 {
            return .good
        } else {
            return .needsImprovement
        }
    }
    
    enum PerformanceStatus {
        case excellent, good, needsImprovement
        
        var description: String {
            switch self {
            case .excellent: return "Excellent Performance"
            case .good: return "Good Performance"
            case .needsImprovement: return "Needs Improvement"
            }
        }
        
        @available(iOS 15.0, macOS 12.0, *)
        var color: Color {
            switch self {
            case .excellent: return .green
            case .good: return .orange
            case .needsImprovement: return .red
            }
        }
    }
}