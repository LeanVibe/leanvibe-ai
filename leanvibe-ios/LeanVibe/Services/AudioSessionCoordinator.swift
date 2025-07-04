import Foundation
import AVFoundation
import Speech
import Combine

/// Central coordinator for managing audio resources and preventing conflicts
/// This is the ONLY service that should directly manage AVAudioEngine and AVAudioSession
@MainActor
class AudioSessionCoordinator: ObservableObject {
    
    // MARK: - Singleton Pattern
    static let shared = AudioSessionCoordinator()
    
    // MARK: - Published State
    @Published private(set) var isAudioSessionActive = false
    @Published private(set) var currentAudioMode: AudioMode = .idle
    @Published private(set) var audioLevel: Float = 0.0
    @Published private(set) var lastError: AudioCoordinatorError?
    
    // MARK: - Audio Resources (SINGLE SOURCE OF TRUTH)
    private var audioEngine: AVAudioEngine?
    private var audioSession = AVAudioSession.sharedInstance()
    
    // MARK: - Audio Buffer Distribution
    private let audioBufferSubject = PassthroughSubject<AVAudioPCMBuffer, Never>()
    var audioBufferPublisher: AnyPublisher<AVAudioPCMBuffer, Never> {
        audioBufferSubject.eraseToAnyPublisher()
    }
    
    // MARK: - Client Management
    private var activeClients: Set<String> = []
    private var clientModeRequests: [String: AudioMode] = [:]
    
    // MARK: - Configuration
    private let bufferSize: AVAudioFrameCount = 1024
    private let preferredSampleRate: Double = 16000
    private let preferredIOBufferDuration: TimeInterval = 0.01 // 10ms for low latency
    
    // MARK: - Performance Optimization
    private var isPreWarmed = false
    private var preWarmTimer: Timer?
    
    private init() {
        setupAudioSessionNotifications()
    }
    
    deinit {
        // Note: Cannot access @MainActor properties from deinit due to sendability requirements
        // Audio resources will be cleaned up when the instance is deallocated
        print("🎤 AudioCoordinator: Deallocating - resources will be cleaned up automatically")
    }
    
    // MARK: - Audio Modes
    enum AudioMode {
        case idle
        case wakeListening      // Background wake phrase detection
        case commandListening   // Active voice command recording
        case processing         // Processing audio data
        
        var sessionCategory: AVAudioSession.Category {
            switch self {
            case .idle:
                return .ambient
            case .wakeListening:
                return .record
            case .commandListening:
                return .playAndRecord
            case .processing:
                return .playAndRecord
            }
        }
        
        var sessionOptions: AVAudioSession.CategoryOptions {
            switch self {
            case .idle:
                return []
            case .wakeListening:
                return [.allowBluetooth]
            case .commandListening, .processing:
                return [.defaultToSpeaker, .allowBluetoothA2DP]
            }
        }
    }
    
    // MARK: - Performance Optimization Methods
    
    /// Pre-warm audio session for faster voice response times
    func prepareForVoiceRecording() async {
        guard !isPreWarmed else {
            print("🎤 AudioCoordinator: Already pre-warmed")
            return
        }
        
        print("🎤 AudioCoordinator: Pre-warming audio session for optimal performance...")
        
        do {
            // Configure audio session for low-latency recording
            try await configureAudioSessionForRecording()
            
            // Pre-initialize audio engine components
            await initializeAudioEngineComponents()
            
            isPreWarmed = true
            
            // Set timer to clear pre-warm state after 30 seconds of inactivity
            preWarmTimer?.invalidate()
            preWarmTimer = Timer.scheduledTimer(withTimeInterval: 30.0, repeats: false) { [weak self] _ in
                Task { @MainActor [weak self] in
                    self?.clearPreWarmState()
                }
            }
            
            print("🎤 AudioCoordinator: Audio session pre-warmed successfully")
            
        } catch {
            print("⚠️ AudioCoordinator: Pre-warm failed: \(error)")
            lastError = .configurationFailed(error)
        }
    }
    
    private func configureAudioSessionForRecording() async throws {
        try audioSession.setCategory(.playAndRecord, mode: .measurement, options: [.defaultToSpeaker, .allowBluetooth])
        try audioSession.setPreferredIOBufferDuration(preferredIOBufferDuration)
        try audioSession.setPreferredSampleRate(preferredSampleRate)
        try audioSession.setActive(true)
    }
    
    private func initializeAudioEngineComponents() async {
        if audioEngine == nil {
            audioEngine = AVAudioEngine()
        }
        
        guard let engine = audioEngine else { return }
        
        // Pre-configure input node
        let inputNode = engine.inputNode
        let inputFormat = inputNode.outputFormat(forBus: 0)
        
        // Install tap for faster startup when actually needed
        if inputNode.outputFormat(forBus: 0).sampleRate > 0 {
            // Only install if not already connected
            print("🎤 AudioCoordinator: Pre-configuring input node")
        }
    }
    
    private func clearPreWarmState() {
        print("🎤 AudioCoordinator: Clearing pre-warm state due to inactivity")
        isPreWarmed = false
        preWarmTimer?.invalidate()
        preWarmTimer = nil
    }
    
    // MARK: - Public Client Interface
    
    /// Register a client for audio access
    func registerClient(_ clientId: String, requestedMode: AudioMode) async -> Result<Void, AudioCoordinatorError> {
        print("🎤 AudioCoordinator: Registering client '\(clientId)' for mode '\(requestedMode)'")
        
        activeClients.insert(clientId)
        clientModeRequests[clientId] = requestedMode
        
        return await updateAudioModeForClients()
    }
    
    /// Unregister a client from audio access
    func unregisterClient(_ clientId: String) async {
        print("🎤 AudioCoordinator: Unregistering client '\(clientId)'")
        
        activeClients.remove(clientId)
        clientModeRequests.removeValue(forKey: clientId)
        
        if activeClients.isEmpty {
            await stopAudioSession()
        } else {
            await updateAudioModeForClients()
        }
    }
    
    /// Update a client's requested audio mode
    func updateClientMode(_ clientId: String, requestedMode: AudioMode) async -> Result<Void, AudioCoordinatorError> {
        guard activeClients.contains(clientId) else {
            return .failure(.clientNotRegistered(clientId))
        }
        
        clientModeRequests[clientId] = requestedMode
        return await updateAudioModeForClients()
    }
    
    // MARK: - Private Audio Management
    
    private func updateAudioModeForClients() async -> Result<Void, AudioCoordinatorError> {
        let newMode = determineOptimalAudioMode()
        
        if newMode != currentAudioMode {
            print("🎤 AudioCoordinator: Switching from '\(currentAudioMode)' to '\(newMode)'")
            return await switchToAudioMode(newMode)
        }
        
        return .success(())
    }
    
    private func determineOptimalAudioMode() -> AudioMode {
        // Priority order: commandListening > processing > wakeListening > idle
        let modes = Array(clientModeRequests.values)
        
        if modes.contains(.commandListening) {
            return .commandListening
        } else if modes.contains(.processing) {
            return .processing
        } else if modes.contains(.wakeListening) {
            return .wakeListening
        } else {
            return .idle
        }
    }
    
    private func switchToAudioMode(_ mode: AudioMode) async -> Result<Void, AudioCoordinatorError> {
        // Stop current audio session if running
        if isAudioSessionActive {
            await stopAudioSession()
        }
        
        // Start new audio session if not idle
        if mode != .idle {
            return await startAudioSession(for: mode)
        } else {
            currentAudioMode = .idle
            return .success(())
        }
    }
    
    private func startAudioSession(for mode: AudioMode) async -> Result<Void, AudioCoordinatorError> {
        do {
            // Configure audio session for the requested mode
            try audioSession.setCategory(
                mode.sessionCategory,
                mode: .default,
                options: mode.sessionOptions
            )
            
            // Optimize for low latency
            try audioSession.setPreferredIOBufferDuration(preferredIOBufferDuration)
            try audioSession.setPreferredSampleRate(preferredSampleRate)
            
            // Activate the audio session
            try audioSession.setActive(true)
            
            // Create and configure audio engine
            audioEngine = AVAudioEngine()
            guard let audioEngine = audioEngine else {
                throw AudioCoordinatorError.audioEngineCreationFailed
            }
            
            let inputNode = audioEngine.inputNode
            let recordingFormat = inputNode.outputFormat(forBus: 0)
            
            // Install tap to distribute audio buffers to clients
            inputNode.installTap(onBus: 0, bufferSize: bufferSize, format: recordingFormat) { [weak self] buffer, _ in
                Task { @MainActor [weak self] in
                    self?.processAudioBuffer(buffer)
                }
            }
            
            // Start the audio engine
            audioEngine.prepare()
            try audioEngine.start()
            
            // Update state
            currentAudioMode = mode
            isAudioSessionActive = true
            lastError = nil
            
            print("🎤 AudioCoordinator: Audio session started successfully for mode '\(mode)'")
            return .success(())
            
        } catch {
            let coordinatorError = AudioCoordinatorError.audioSessionStartFailed(error)
            lastError = coordinatorError
            print("🎤 AudioCoordinator: Failed to start audio session - \(error)")
            return .failure(coordinatorError)
        }
    }
    
    private func stopAudioSession() async {
        print("🎤 AudioCoordinator: Stopping audio session")
        
        // Stop audio engine
        audioEngine?.stop()
        if let inputNode = audioEngine?.inputNode, inputNode.numberOfInputs > 0 {
            inputNode.removeTap(onBus: 0)
        }
        audioEngine = nil
        
        // Deactivate audio session
        do {
            try audioSession.setActive(false)
        } catch {
            print("🎤 AudioCoordinator: Warning - failed to deactivate audio session: \(error)")
        }
        
        // Update state
        isAudioSessionActive = false
        currentAudioMode = .idle
        audioLevel = 0.0
    }
    
    private func processAudioBuffer(_ buffer: AVAudioPCMBuffer) {
        // Calculate audio level for monitoring
        audioLevel = calculateAudioLevel(from: buffer)
        
        // Distribute buffer to all registered clients
        audioBufferSubject.send(buffer)
    }
    
    private func calculateAudioLevel(from buffer: AVAudioPCMBuffer) -> Float {
        guard let channelData = buffer.floatChannelData?[0] else { return 0.0 }
        
        let frameLength = Int(buffer.frameLength)
        guard frameLength > 0 else { return 0.0 }
        
        let channelDataArray = Array(UnsafeBufferPointer(start: channelData, count: frameLength))
        let rms = sqrt(channelDataArray.map { $0 * $0 }.reduce(0, +) / Float(frameLength))
        return min(max(rms * 20, 0.0), 1.0)
    }
    
    // MARK: - Audio Session Notifications
    
    private func setupAudioSessionNotifications() {
        NotificationCenter.default.addObserver(
            forName: AVAudioSession.interruptionNotification,
            object: nil,
            queue: .main
        ) { [weak self] notification in
            guard let self = self else { return }
            // Extract notification data and make it sendable
            let typeValue = notification.userInfo?[AVAudioSessionInterruptionTypeKey] as? UInt
            Task { @MainActor in
                await self.handleAudioInterruption(typeValue: typeValue)
            }
        }
        
        NotificationCenter.default.addObserver(
            forName: AVAudioSession.routeChangeNotification,
            object: nil,
            queue: .main
        ) { [weak self] notification in
            guard let self = self else { return }
            // Extract notification data and make it sendable
            let reasonValue = notification.userInfo?[AVAudioSessionRouteChangeReasonKey] as? UInt
            Task { @MainActor in
                await self.handleAudioRouteChange(reasonValue: reasonValue)
            }
        }
    }
    
    private func handleAudioInterruption(typeValue: UInt?) async {
        guard let typeValue = typeValue,
              let type = AVAudioSession.InterruptionType(rawValue: typeValue) else {
            return
        }
        
        switch type {
        case .began:
            print("🎤 AudioCoordinator: Audio interruption began")
            await stopAudioSession()
        case .ended:
            print("🎤 AudioCoordinator: Audio interruption ended")
            if !activeClients.isEmpty {
                await updateAudioModeForClients()
            }
        @unknown default:
            break
        }
    }
    
    private func handleAudioRouteChange(reasonValue: UInt?) async {
        guard let reasonValue = reasonValue,
              let reason = AVAudioSession.RouteChangeReason(rawValue: reasonValue) else {
            return
        }
        
        print("🎤 AudioCoordinator: Audio route changed - reason: \(reason)")
        
        // Restart audio session for certain route changes to ensure optimal configuration
        switch reason {
        case .newDeviceAvailable, .oldDeviceUnavailable:
            if isAudioSessionActive {
                let currentMode = self.currentAudioMode
                await stopAudioSession()
                await switchToAudioMode(currentMode)
            }
        default:
            break
        }
    }
    
    // MARK: - Shutdown
    
    func shutdown() async {
        print("🎤 AudioCoordinator: Shutting down")
        activeClients.removeAll()
        clientModeRequests.removeAll()
        await stopAudioSession()
    }
}

// MARK: - Error Types

enum AudioCoordinatorError: LocalizedError {
    case audioEngineCreationFailed
    case audioSessionStartFailed(Error)
    case clientNotRegistered(String)
    case invalidAudioMode
    
    var errorDescription: String? {
        switch self {
        case .audioEngineCreationFailed:
            return "Failed to create audio engine"
        case .audioSessionStartFailed(let error):
            return "Failed to start audio session: \(error.localizedDescription)"
        case .clientNotRegistered(let clientId):
            return "Client '\(clientId)' is not registered"
        case .invalidAudioMode:
            return "Invalid audio mode requested"
        }
    }
}

// MARK: - Client Helper Extensions

extension AudioSessionCoordinator {
    
    /// Convenience method for speech recognition clients
    func registerSpeechClient(_ clientId: String) async -> Result<Void, AudioCoordinatorError> {
        return await registerClient(clientId, requestedMode: .commandListening)
    }
    
    /// Convenience method for wake phrase detection clients
    func registerWakeClient(_ clientId: String) async -> Result<Void, AudioCoordinatorError> {
        return await registerClient(clientId, requestedMode: .wakeListening)
    }
    
    /// Get current audio session status for client debugging
    var debugStatus: String {
        return """
        AudioSessionCoordinator Status:
        - Mode: \(currentAudioMode)
        - Active: \(isAudioSessionActive)
        - Clients: \(activeClients.count)
        - Audio Level: \(audioLevel)
        - Last Error: \(lastError?.localizedDescription ?? "None")
        """
    }
}