import Foundation
import Speech
import AVFoundation
import SwiftUI
import _Concurrency

@MainActor
class VoicePermissionManager: ObservableObject {
    @Published var hasMicrophonePermission = false
    @Published var hasSpeechRecognitionPermission = false
    @Published var permissionStatus: PermissionStatus = .notDetermined
    @Published var isFullyAuthorized = false
    @Published var permissionError: String?
    
    @Published private(set) var speechAuthorizationStatus: SFSpeechRecognizerAuthorizationStatus = .notDetermined
    @Published private(set) var microphoneAuthorizationStatus: AVAudioSession.RecordPermission = .undetermined
    
    enum PermissionStatus {
        case notDetermined
        case granted
        case denied
        case restricted
    }
    
    init() {
        checkPermissions()
    }
    
    func checkPermissions() {
        checkMicrophonePermission()
        checkSpeechRecognitionPermission()
        updateOverallStatus()
    }
    
    func openAppSettings() {
        #if canImport(UIKit)
        if let settingsURL = URL(string: UIApplication.openSettingsURLString) {
            UIApplication.shared.open(settingsURL)
        }
        #endif
    }
    
    private func checkMicrophonePermission() {
        let status = AVAudioSession.sharedInstance().recordPermission
        hasMicrophonePermission = (status == .granted)
    }
    
    private func checkSpeechRecognitionPermission() {
        let status = SFSpeechRecognizer.authorizationStatus()
        hasSpeechRecognitionPermission = (status == .authorized)
    }
    
    func requestPermissions(completion: @escaping (Bool) -> Void) {
        requestMicrophonePermission { [weak self] micGranted in
            guard let self = self else { return }
            if micGranted {
                self.requestSpeechRecognitionPermission { speechGranted in
                    let allGranted = micGranted && speechGranted
                    _Concurrency.Task { @MainActor in
                        self.updateOverallStatus()
                        completion(allGranted)
                    }
                }
            } else {
                _Concurrency.Task { @MainActor in
                    self.updateOverallStatus()
                    completion(false)
                }
            }
        }
    }
    
    func requestFullPermissions(completion: @escaping (Bool) -> Void) {
        requestPermissions(completion: completion)
    }
    
    private func requestMicrophonePermission(completion: @escaping (Bool) -> Void) {
        AVAudioSession.sharedInstance().requestRecordPermission { granted in
            DispatchQueue.main.async {
                self.hasMicrophonePermission = granted
                completion(granted)
            }
        }
    }
    
    private func requestSpeechRecognitionPermission(completion: @escaping (Bool) -> Void) {
        SFSpeechRecognizer.requestAuthorization { status in
            DispatchQueue.main.async {
                self.hasSpeechRecognitionPermission = (status == .authorized)
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
            } else if micStatus == .undetermined || speechStatus == .notDetermined {
                permissionStatus = .notDetermined
            } else {
                permissionStatus = .restricted
            }
            isFullyAuthorized = false
        }
        updateAuthorizationStatus()
    }
    
    private func updateAuthorizationStatus() {
        speechAuthorizationStatus = SFSpeechRecognizer.authorizationStatus()
        microphoneAuthorizationStatus = AVAudioSession.sharedInstance().recordPermission
        updatePermissionError()
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
    
    func openSettings() {
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
            return "Undetermined"
        case .denied:
            return "Denied"
        case .granted:
            return "Granted"
        @unknown default:
            return "Unknown"
        }
    }
    
    var isGranted: Bool {
        return self == .granted
    }
}
