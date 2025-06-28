import Foundation
import Speech
import AVFoundation

@MainActor
class VoicePermissionManager: ObservableObject {
    @Published var speechAuthorizationStatus: SFSpeechRecognizerAuthorizationStatus = .notDetermined
    @Published var microphoneAuthorizationStatus: AVAudioSession.RecordPermission = .undetermined
    @Published var isFullyAuthorized = false
    @Published var permissionError: String?
    
    var canRequestPermissions: Bool {
        speechAuthorizationStatus == .notDetermined || microphoneAuthorizationStatus == .undetermined
    }
    
    var needsPermissions: Bool {
        speechAuthorizationStatus != .authorized || microphoneAuthorizationStatus != .granted
    }
    
    var permissionStatusDescription: String {
        if isFullyAuthorized {
            return "Voice commands are ready to use"
        } else if speechAuthorizationStatus == .denied || microphoneAuthorizationStatus == .denied {
            return "Voice permissions denied. Please enable in Settings"
        } else if speechAuthorizationStatus == .restricted {
            return "Speech recognition is restricted on this device"
        } else {
            return "Voice permissions needed for voice commands"
        }
    }
    
    init() {
        updateAuthorizationStatus()
    }
    
    func requestAllPermissions() async {
        await requestSpeechRecognitionPermission()
        await requestMicrophonePermission()
        updateFullAuthorizationStatus()
    }
    
    private func requestSpeechRecognitionPermission() async {
        return await withCheckedContinuation { continuation in
            SFSpeechRecognizer.requestAuthorization { [weak self] status in
                DispatchQueue.main.async {
                    self?.speechAuthorizationStatus = status
                    self?.updatePermissionError()
                    continuation.resume()
                }
            }
        }
    }
    
    private func requestMicrophonePermission() async {
        return await withCheckedContinuation { continuation in
            AVAudioSession.sharedInstance().requestRecordPermission { [weak self] granted in
                DispatchQueue.main.async {
                    self?.microphoneAuthorizationStatus = granted ? .granted : .denied
                    self?.updatePermissionError()
                    continuation.resume()
                }
            }
        }
    }
    
    private func updateAuthorizationStatus() {
        speechAuthorizationStatus = SFSpeechRecognizer.authorizationStatus()
        microphoneAuthorizationStatus = AVAudioSession.sharedInstance().recordPermission
        updateFullAuthorizationStatus()
        updatePermissionError()
    }
    
    private func updateFullAuthorizationStatus() {
        isFullyAuthorized = speechAuthorizationStatus == .authorized && microphoneAuthorizationStatus == .granted
    }
    
    private func updatePermissionError() {
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
    
    func openAppSettings() {
        guard let settingsUrl = URL(string: UIApplication.openSettingsURLString) else {
            return
        }
        
        if UIApplication.shared.canOpenURL(settingsUrl) {
            UIApplication.shared.open(settingsUrl)
        }
    }
    
    func checkPermissionsStatus() {
        updateAuthorizationStatus()
    }
    
    // MARK: - Privacy Information
    
    var privacyDescription: String {
        """
        Voice commands are processed entirely on your device for maximum privacy:
        
        • Speech recognition runs locally using Apple's on-device engine
        • No voice data is sent to external servers
        • Transcribed text is sent to your connected Mac agent
        • Voice recordings are not stored or shared
        • You can disable voice commands at any time
        """
    }
    
    var permissionRationale: String {
        """
        LeenVibe needs these permissions to enable voice commands:
        
        🎤 Microphone Access
        To hear your voice commands like "Hey LeenVibe, show status"
        
        🗣️ Speech Recognition
        To convert your speech to text for command processing
        
        All processing happens on your device - no data leaves your iPhone.
        """
    }
}

// MARK: - Permission Status Helpers

extension SFSpeechRecognizerAuthorizationStatus {
    var description: String {
        switch self {
        case .notDetermined:
            return "Not determined"
        case .denied:
            return "Denied"
        case .restricted:
            return "Restricted"
        case .authorized:
            return "Authorized"
        @unknown default:
            return "Unknown"
        }
    }
    
    var isGranted: Bool {
        return self == .authorized
    }
}

extension AVAudioSession.RecordPermission {
    var description: String {
        switch self {
        case .undetermined:
            return "Not determined"
        case .denied:
            return "Denied"
        case .granted:
            return "Granted"
        @unknown default:
            return "Unknown"
        }
    }
}