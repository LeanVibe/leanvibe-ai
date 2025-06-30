# KAPPA Agent - Implementation Prompts & Patterns

This document contains the key prompts, patterns, and implementation approaches used throughout KAPPA's task completion journey.

## Task 08: Settings & Configuration System Implementation

### Core Implementation Prompt
```
Create a comprehensive Settings & Configuration System for LeanVibe iOS app that provides complete control over all features built in previous tasks:

1. Voice System Configuration (KAPPA's specialty)
2. Kanban Board Customization (KAPPA's creation)  
3. Server Connection Management
4. Accessibility Controls
5. Notification Preferences

Requirements:
- Centralized SettingsManager with auto-save
- Type-safe Codable settings models
- Real-time UI updates with @Published properties
- Interactive testing tools (voice, connection, notifications)
- Export/import functionality for settings backup
- iOS-native UX patterns and accessibility compliance
```

### Settings Architecture Pattern
```swift
// Protocol-based settings architecture
protocol SettingsProtocol: Codable {
    static func load() -> Self
    func save()
    static var storageKey: String { get }
}

// Centralized reactive settings manager
class SettingsManager: ObservableObject {
    static let shared = SettingsManager()
    
    @Published var voiceSettings = VoiceSettings()
    @Published var kanbanSettings = KanbanSettings()
    // ... other settings
    
    private func setupAutoSave() {
        Publishers.CombineLatest6(
            $appSettings, $voiceSettings, $kanbanSettings,
            $notificationSettings, $connectionSettings, $accessibilitySettings
        )
        .debounce(for: .seconds(1), scheduler: RunLoop.main)
        .sink { [weak self] _ in self?.saveAllSettings() }
        .store(in: &cancellables)
    }
}
```

### Voice Settings Integration Pattern
```swift
// Integration with existing voice system
struct VoiceSettingsView: View {
    @StateObject private var settingsManager = SettingsManager.shared
    
    private var wakePhraseSection: some View {
        Section("Wake Phrase") {
            Toggle("Enable 'Hey LeanVibe'", isOn: $settingsManager.voiceSettings.wakePhraseEnabled)
                .onChange(of: settingsManager.voiceSettings.wakePhraseEnabled) { _, enabled in
                    handleWakePhraseToggle(enabled) // Integrate with VoiceManager
                }
            
            if settingsManager.voiceSettings.wakePhraseEnabled {
                VStack(alignment: .leading, spacing: 8) {
                    Text("Sensitivity")
                    Slider(value: $settingsManager.voiceSettings.wakePhraseSensitivity, in: 0.1...1.0)
                    Text("Higher sensitivity = more responsive but may trigger accidentally")
                        .font(.caption).foregroundColor(.secondary)
                }
            }
        }
    }
}
```

### Interactive Testing Pattern
```swift
// Voice testing interface with real-time feedback
struct VoiceTestView: View {
    @State private var isListening = false
    @State private var recognizedText = ""
    @State private var testResults: [VoiceTestResult] = []
    
    var body: some View {
        VStack {
            Button(isListening ? "Stop Testing" : "Start Test") {
                toggleListening()
            }
            
            if isListening {
                VoiceWaveformView() // Animated waveform during recognition
            }
            
            if !recognizedText.isEmpty {
                Text("Recognized: \(recognizedText)")
                    .padding().background(Color.gray.opacity(0.1))
            }
        }
    }
}
```

### QR Scanner Integration Pattern
```swift
// Camera-based QR scanner for server setup
struct QRScannerView: View {
    let onResult: (String) -> Void
    @State private var hasPermission = false
    
    var body: some View {
        ZStack {
            if hasPermission {
                QRCodeScannerRepresentable { result in
                    if let serverConfig = parseQRCode(result) {
                        updateServerSettings(serverConfig)
                    }
                }
            } else {
                CameraPermissionView()
            }
        }
        .onAppear { checkCameraPermission() }
    }
    
    private func parseQRCode(_ content: String) -> ServerConfig? {
        // Parse "leanvibe://server/host:port?ssl=true" format
        guard let url = URL(string: content),
              url.scheme == "leanvibe" else { return nil }
        // ... parsing logic
    }
}
```

## SwiftUI Best Practices Used

### State Management
```swift
// Proper state management with @StateObject and @ObservedObject
@StateObject private var settingsManager = SettingsManager.shared  // Create once
@ObservedObject var webSocketService: WebSocketService            // Injected dependency
@State private var showingModal = false                           // Local UI state
```

### Reactive UI Updates
```swift
// onChange modifiers for immediate feedback
Toggle("Enable Feature", isOn: $settings.featureEnabled)
    .onChange(of: settings.featureEnabled) { _, enabled in
        handleFeatureToggle(enabled)
    }

// Computed properties for dynamic UI
private var statusColor: Color {
    webSocketService.isConnected ? .green : .red
}
```

### Sheet Presentations
```swift
// Modal presentations for complex configuration
.sheet(isPresented: $showingAdvancedSettings) {
    AdvancedSettingsView()
}
.sheet(isPresented: $showingQRScanner) {
    QRScannerView { result in handleQRResult(result) }
}
```

### Custom Components
```swift
// Reusable settings row component
struct SettingsRow: View {
    let icon: String
    let iconColor: Color
    let title: String
    let subtitle: String
    
    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .foregroundColor(iconColor)
                .frame(width: 24, height: 24)
                .background(iconColor.opacity(0.15))
                .clipShape(RoundedRectangle(cornerRadius: 6))
            
            VStack(alignment: .leading, spacing: 2) {
                Text(title).font(.body).fontWeight(.medium)
                Text(subtitle).font(.caption).foregroundColor(.secondary)
            }
            Spacer()
        }
    }
}
```

## iOS Integration Patterns

### Notification Permissions
```swift
// Proper UNUserNotificationCenter integration
private func requestNotificationPermission() {
    UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound, .badge]) { granted, error in
        DispatchQueue.main.async {
            if granted {
                settingsManager.notificationSettings.pushNotificationsEnabled = true
            }
        }
    }
}
```

### Camera Permissions
```swift
// AVFoundation camera permission handling
private func checkCameraPermission() {
    switch AVCaptureDevice.authorizationStatus(for: .video) {
    case .authorized:
        hasPermission = true
    case .notDetermined:
        requestCameraPermission()
    case .denied, .restricted:
        showPermissionAlert = true
    }
}
```

### System Settings Integration
```swift
// Open iOS Settings when needed
private func openSystemSettings() {
    if let settingsURL = URL(string: UIApplication.openSettingsURLString) {
        UIApplication.shared.open(settingsURL)
    }
}
```

### Accessibility Integration
```swift
// Detect system accessibility features
AccessibilityFeatureStatus(
    feature: "VoiceOver",
    isEnabled: UIAccessibility.isVoiceOverRunning
)
AccessibilityFeatureStatus(
    feature: "Reduce Motion", 
    isEnabled: UIAccessibility.isReduceMotionEnabled
)
```

## Error Handling Patterns

### Safe Parsing
```swift
// Safe UserDefaults loading with fallbacks
static func load() -> VoiceSettings {
    guard let data = UserDefaults.standard.data(forKey: storageKey),
          let settings = try? JSONDecoder().decode(VoiceSettings.self, from: data) else {
        return VoiceSettings() // Safe fallback to defaults
    }
    return settings
}
```

### Connection Testing
```swift
// Graceful connection testing with timeout
private func testConnection() {
    isTestingConnection = true
    connectionTestResult = nil
    
    // Simulate connection test with timeout
    DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
        isTestingConnection = false
        connectionTestResult = serverConfigured ? .success : .failure("Connection timeout")
    }
}
```

### Permission Handling
```swift
// Handle various permission states gracefully
private var permissionStatusText: String {
    switch notificationAuthStatus {
    case .authorized: return "Authorized"
    case .denied: return "Denied"
    case .notDetermined: return "Not Requested"
    case .provisional: return "Provisional"
    @unknown default: return "Unknown"
    }
}
```

## Performance Optimizations

### Debounced Auto-Save
```swift
// Prevent excessive UserDefaults writes
.debounce(for: .seconds(1), scheduler: RunLoop.main)
.sink { [weak self] _ in self?.saveAllSettings() }
```

### Lazy Loading
```swift
// Load complex views only when needed
.sheet(isPresented: $showingAdvancedSettings) {
    AdvancedSettingsView() // Created only when shown
}
```

### Memory Management
```swift
// Proper Combine cleanup
private var cancellables = Set<AnyCancellable>()

deinit {
    cancellables.removeAll()
}
```

## Documentation Patterns

### Code Documentation
```swift
/// Comprehensive Voice Settings view for configuring the voice system built by KAPPA
/// Provides controls for wake phrase, speech recognition, voice commands, and testing
struct VoiceSettingsView: View {
    
    // MARK: - Properties
    // MARK: - Body  
    // MARK: - View Sections
    // MARK: - Actions
}
```

### Feature Documentation
```markdown
## 🎯 Key Features Delivered

### Voice Settings (My Specialty)
- Complete voice system configuration for the voice interface I built
- Wake phrase controls with sensitivity adjustment
- Speech recognition settings and voice testing interface

### Technical Excellence
- **Type Safety**: Codable protocols with proper validation
- **Real-time Updates**: @Published properties with auto-save
- **Integration Ready**: Works with all systems from previous tasks
```

This comprehensive prompt and pattern library captures the key implementation approaches that made the Settings & Configuration System successful and can be applied to future iOS development tasks.