# KAPPA Agent - Task 08: Settings & Configuration System

**Assignment Date**: Post Major Integration Completion  
**Worktree**: Create new worktree `../leenvibe-ios-settings`  
**Branch**: `feature/settings-configuration-system`  
**Status**: 🔄 ASSIGNED  

## Mission Brief

Outstanding achievement on your previous deliveries! Your Kanban Board, Voice Interface, and Integration Testing work has been successfully integrated into the main project. Now we need your UI expertise to complete the final missing piece: a comprehensive Settings & Configuration System that ties together all the features you've built.

## Context & Current Status

- ✅ **Your Kanban Board**: Successfully integrated with backend APIs working
- ✅ **Your Voice Interface**: "Hey LeenVibe" wake phrase system fully integrated
- ✅ **Your Integration Testing**: Complete validation framework delivered
- ✅ **Main Project**: 78 Swift files unified with all your work included
- ❌ **Missing**: Settings system to configure all the features you built
- ❌ **Missing**: User preferences for voice, notifications, and app behavior

## Your New Mission

Create a comprehensive Settings & Configuration System that allows users to configure all the sophisticated features you've built, providing a polished and user-friendly way to customize their LeenVibe experience.

## Working Directory

**New Worktree**: `../leenvibe-ios-settings`  
**Integration Target**: `/Users/bogdan/work/leanvibe-ai/LeenVibe-iOS/`  
**Branch**: `feature/settings-configuration-system`

## 🛠️ Settings System Architecture

### 1. Main Settings Interface
**Comprehensive settings tab for DashboardTabView**

```swift
// Your task: Create the main settings view that replaces the placeholder
struct SettingsTabView: View {
    @StateObject private var settingsManager = SettingsManager.shared
    @StateObject private var voiceSettings = VoiceSettingsManager()
    @StateObject private var notificationSettings = NotificationSettingsManager()
    
    var body: some View {
        NavigationView {
            List {
                // Voice Settings Section
                Section("Voice & Speech") {
                    NavigationLink("Voice Commands", destination: VoiceSettingsView())
                    NavigationLink("Wake Phrase Configuration", destination: WakePhraseSettingsView())
                    NavigationLink("Speech Recognition", destination: SpeechSettingsView())
                }
                
                // Task Management Settings
                Section("Task Management") {
                    NavigationLink("Kanban Preferences", destination: KanbanSettingsView())
                    NavigationLink("Task Notifications", destination: TaskNotificationSettingsView())
                    NavigationLink("Productivity Metrics", destination: MetricsSettingsView())
                }
                
                // Connection & Sync
                Section("Connection") {
                    NavigationLink("Server Configuration", destination: ServerSettingsView())
                    NavigationLink("Sync Preferences", destination: SyncSettingsView())
                    NavigationLink("Offline Mode", destination: OfflineSettingsView())
                }
                
                // App Preferences
                Section("Appearance & Behavior") {
                    NavigationLink("Interface", destination: InterfaceSettingsView())
                    NavigationLink("Accessibility", destination: AccessibilitySettingsView())
                    NavigationLink("Developer Options", destination: DeveloperSettingsView())
                }
                
                // About & Help
                Section("Support") {
                    NavigationLink("Help & Tutorials", destination: HelpView())
                    NavigationLink("About LeenVibe", destination: AboutView())
                    NavigationLink("Privacy Policy", destination: PrivacyView())
                }
            }
            .navigationTitle("Settings")
        }
    }
}
```

### 2. Voice Settings (Your Specialty)
**Configure the voice system you built**

```swift
struct VoiceSettingsView: View {
    @StateObject private var voiceManager = VoiceManager.shared
    @StateObject private var speechRecognition = SpeechRecognitionService.shared
    @State private var wakePhraseEnabled = true
    @State private var voiceFeedbackEnabled = true
    @State private var backgroundListening = false
    
    var body: some View {
        List {
            Section("Wake Phrase") {
                Toggle("Enable 'Hey LeenVibe'", isOn: $wakePhraseEnabled)
                    .onChange(of: wakePhraseEnabled) { enabled in
                        if enabled {
                            voiceManager.startWakePhraseDetection()
                        } else {
                            voiceManager.stopWakePhraseDetection()
                        }
                    }
                
                if wakePhraseEnabled {
                    VStack(alignment: .leading) {
                        Text("Sensitivity")
                        Slider(value: $voiceManager.wakePhrasesensitivity, in: 0.1...1.0)
                        Text("Higher sensitivity = more responsive but may trigger accidentally")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }
            }
            
            Section("Speech Recognition") {
                Toggle("Voice Feedback", isOn: $voiceFeedbackEnabled)
                Toggle("Background Listening", isOn: $backgroundListening)
                
                HStack {
                    Text("Language")
                    Spacer()
                    Picker("Language", selection: $speechRecognition.recognitionLanguage) {
                        Text("English (US)").tag("en-US")
                        Text("English (UK)").tag("en-GB")
                        // Add more languages as needed
                    }
                }
            }
            
            Section("Voice Commands") {
                NavigationLink("Test Voice Recognition", destination: VoiceTestView())
                NavigationLink("Command History", destination: VoiceHistoryView())
                NavigationLink("Custom Commands", destination: CustomCommandsView())
            }
            
            Section("Troubleshooting") {
                Button("Reset Voice Settings") {
                    resetVoiceSettings()
                }
                .foregroundColor(.red)
            }
        }
        .navigationTitle("Voice Settings")
    }
    
    private func resetVoiceSettings() {
        // Reset all voice-related settings to defaults
        voiceManager.resetToDefaults()
        speechRecognition.resetToDefaults()
    }
}
```

### 3. Kanban Settings (Your Kanban System)
**Configure the Kanban board you built**

```swift
struct KanbanSettingsView: View {
    @AppStorage("kanbanAutoRefresh") private var autoRefresh = true
    @AppStorage("kanbanShowStatistics") private var showStatistics = true
    @AppStorage("kanbanCompactMode") private var compactMode = false
    @AppStorage("kanbanColumnOrder") private var columnOrderData = Data()
    
    var body: some View {
        List {
            Section("Board Behavior") {
                Toggle("Auto-refresh from server", isOn: $autoRefresh)
                Toggle("Show task statistics", isOn: $showStatistics)
                Toggle("Compact mode", isOn: $compactMode)
            }
            
            Section("Columns") {
                NavigationLink("Customize Columns", destination: ColumnCustomizationView())
                NavigationLink("Column Order", destination: ColumnOrderView())
            }
            
            Section("Task Creation") {
                NavigationLink("Default Task Settings", destination: DefaultTaskSettingsView())
                NavigationLink("Quick Actions", destination: QuickActionsSettingsView())
            }
            
            Section("Integration") {
                Toggle("Voice task creation", isOn: .constant(true))
                Text("Enable voice commands like 'Create task: Fix login bug'")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .navigationTitle("Kanban Settings")
    }
}
```

### 4. Notification Settings
**Configure the notification system BETA is building**

```swift
struct NotificationSettingsView: View {
    @StateObject private var notificationManager = NotificationManager.shared
    @State private var pushNotificationsEnabled = false
    @State private var taskNotificationsEnabled = true
    @State private var voiceNotificationsEnabled = true
    
    var body: some View {
        List {
            Section("Push Notifications") {
                Toggle("Enable Push Notifications", isOn: $pushNotificationsEnabled)
                    .onChange(of: pushNotificationsEnabled) { enabled in
                        if enabled {
                            Task {
                                await requestNotificationPermission()
                            }
                        }
                    }
                
                if pushNotificationsEnabled {
                    Toggle("Task Updates", isOn: $taskNotificationsEnabled)
                    Toggle("Voice Command Results", isOn: $voiceNotificationsEnabled)
                    Toggle("Server Disconnection", isOn: .constant(true))
                }
            }
            
            Section("In-App Notifications") {
                Toggle("Banner notifications", isOn: .constant(true))
                Toggle("Sound effects", isOn: .constant(true))
                Toggle("Haptic feedback", isOn: .constant(true))
            }
            
            Section("Quiet Hours") {
                NavigationLink("Do Not Disturb", destination: QuietHoursView())
            }
        }
        .navigationTitle("Notifications")
    }
    
    private func requestNotificationPermission() async {
        await notificationManager.requestPermission()
    }
}
```

## 🔧 Settings Data Management

### 1. Settings Manager
**Centralized settings coordination**

```swift
class SettingsManager: ObservableObject {
    static let shared = SettingsManager()
    
    @Published var appSettings = AppSettings()
    @Published var voiceSettings = VoiceSettings()
    @Published var kanbanSettings = KanbanSettings()
    @Published var notificationSettings = NotificationSettings()
    
    private init() {
        loadSettings()
    }
    
    func loadSettings() {
        // Load from UserDefaults, Keychain, or other persistence
        appSettings = AppSettings.load()
        voiceSettings = VoiceSettings.load()
        kanbanSettings = KanbanSettings.load()
        notificationSettings = NotificationSettings.load()
    }
    
    func saveSettings() {
        appSettings.save()
        voiceSettings.save()
        kanbanSettings.save()
        notificationSettings.save()
    }
    
    func resetAllSettings() {
        appSettings = AppSettings()
        voiceSettings = VoiceSettings()
        kanbanSettings = KanbanSettings()
        notificationSettings = NotificationSettings()
        saveSettings()
    }
}
```

### 2. Settings Models
**Type-safe settings structures**

```swift
struct VoiceSettings: Codable {
    var wakePhraseEnabled = true
    var wakePhrasePhrase = "Hey LeenVibe"
    var wakePhraseTimeout = 5.0
    var voiceFeedbackEnabled = true
    var backgroundListening = false
    var recognitionLanguage = "en-US"
    var confidence_threshold = 0.7
    
    func save() {
        if let data = try? JSONEncoder().encode(self) {
            UserDefaults.standard.set(data, forKey: "VoiceSettings")
        }
    }
    
    static func load() -> VoiceSettings {
        guard let data = UserDefaults.standard.data(forKey: "VoiceSettings"),
              let settings = try? JSONDecoder().decode(VoiceSettings.self, from: data) else {
            return VoiceSettings()
        }
        return settings
    }
}

struct KanbanSettings: Codable {
    var autoRefresh = true
    var refreshInterval = 30.0 // seconds
    var showStatistics = true
    var compactMode = false
    var columnOrder = ["backlog", "in_progress", "testing", "done"]
    var enableVoiceTaskCreation = true
    var showTaskIds = false
    
    func save() {
        if let data = try? JSONEncoder().encode(self) {
            UserDefaults.standard.set(data, forKey: "KanbanSettings")
        }
    }
    
    static func load() -> KanbanSettings {
        guard let data = UserDefaults.standard.data(forKey: "KanbanSettings"),
              let settings = try? JSONDecoder().decode(KanbanSettings.self, from: data) else {
            return KanbanSettings()
        }
        return settings
    }
}
```

## 🎨 Advanced Settings Features

### 1. Voice Testing Interface
**Test the voice system you built**

```swift
struct VoiceTestView: View {
    @StateObject private var voiceManager = VoiceManager.shared
    @State private var isListening = false
    @State private var recognizedText = ""
    @State private var testResults: [VoiceTestResult] = []
    
    var body: some View {
        VStack(spacing: 20) {
            Text("Voice Recognition Test")
                .font(.title2)
                .fontWeight(.semibold)
            
            // Wake phrase test
            VStack {
                Text("Wake Phrase Test")
                    .font(.headline)
                
                Button(isListening ? "Stop Listening" : "Test 'Hey LeenVibe'") {
                    if isListening {
                        stopWakePhraseTest()
                    } else {
                        startWakePhraseTest()
                    }
                }
                .buttonStyle(.borderedProminent)
                
                if isListening {
                    VoiceWaveformView()
                        .frame(height: 60)
                }
            }
            
            // Recognition results
            if !recognizedText.isEmpty {
                VStack(alignment: .leading) {
                    Text("Recognized:")
                        .font(.headline)
                    Text(recognizedText)
                        .padding()
                        .background(Color.gray.opacity(0.1))
                        .cornerRadius(8)
                }
            }
            
            // Test history
            if !testResults.isEmpty {
                List(testResults) { result in
                    VStack(alignment: .leading) {
                        Text(result.input)
                            .fontWeight(.semibold)
                        Text("Confidence: \(result.confidence, specifier: "%.1f")%")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }
            }
            
            Spacer()
        }
        .padding()
        .navigationTitle("Voice Test")
    }
    
    private func startWakePhraseTest() {
        isListening = true
        voiceManager.startWakePhraseDetection { [weak self] in
            DispatchQueue.main.async {
                self?.wakePhraseDetected()
            }
        }
    }
    
    private func stopWakePhraseTest() {
        isListening = false
        voiceManager.stopWakePhraseDetection()
    }
    
    private func wakePhraseDetected() {
        recognizedText = "Wake phrase detected!"
        let result = VoiceTestResult(
            input: "Hey LeenVibe",
            confidence: Double.random(in: 80...95),
            timestamp: Date()
        )
        testResults.insert(result, at: 0)
        stopWakePhraseTest()
    }
}

struct VoiceTestResult: Identifiable {
    let id = UUID()
    let input: String
    let confidence: Double
    let timestamp: Date
}
```

### 2. Connection Management
**Manage server connections and sync**

```swift
struct ServerSettingsView: View {
    @StateObject private var connectionManager = ConnectionStorageManager.shared
    @State private var currentServerURL = ""
    @State private var connectionStatus: ConnectionStatus = .unknown
    @State private var showingQRScanner = false
    
    enum ConnectionStatus {
        case unknown, connecting, connected, disconnected, error(String)
    }
    
    var body: some View {
        List {
            Section("Current Connection") {
                HStack {
                    Text("Status")
                    Spacer()
                    connectionStatusView
                }
                
                if !currentServerURL.isEmpty {
                    HStack {
                        Text("Server")
                        Spacer()
                        Text(currentServerURL)
                            .foregroundColor(.secondary)
                    }
                }
                
                Button("Test Connection") {
                    testCurrentConnection()
                }
            }
            
            Section("Configuration") {
                Button("Scan QR Code") {
                    showingQRScanner = true
                }
                
                Button("Manual Setup") {
                    // Show manual server entry
                }
                
                NavigationLink("Advanced Settings", destination: AdvancedConnectionView())
            }
            
            Section("Troubleshooting") {
                Button("Reset Connection") {
                    resetConnection()
                }
                .foregroundColor(.red)
            }
        }
        .navigationTitle("Server Settings")
        .onAppear {
            loadCurrentConnection()
        }
        .sheet(isPresented: $showingQRScanner) {
            QRScannerView { serverConfig in
                handleNewConnection(serverConfig)
            }
        }
    }
    
    @ViewBuilder
    private var connectionStatusView: some View {
        switch connectionStatus {
        case .connected:
            Label("Connected", systemImage: "checkmark.circle.fill")
                .foregroundColor(.green)
        case .connecting:
            Label("Connecting...", systemImage: "arrow.clockwise")
                .foregroundColor(.orange)
        case .disconnected:
            Label("Disconnected", systemImage: "xmark.circle.fill")
                .foregroundColor(.red)
        case .error(let message):
            Label("Error", systemImage: "exclamationmark.triangle.fill")
                .foregroundColor(.red)
        case .unknown:
            Label("Unknown", systemImage: "questionmark.circle")
                .foregroundColor(.gray)
        }
    }
    
    private func loadCurrentConnection() {
        if let config = connectionManager.loadStoredConnection() {
            currentServerURL = config.baseURL
            connectionStatus = .connected
        }
    }
    
    private func testCurrentConnection() {
        connectionStatus = .connecting
        // Test connection logic
        DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
            connectionStatus = .connected
        }
    }
    
    private func handleNewConnection(_ serverConfig: ServerConfig) {
        connectionManager.store(serverConfig)
        currentServerURL = serverConfig.baseURL
        connectionStatus = .connected
        showingQRScanner = false
    }
    
    private func resetConnection() {
        connectionManager.clearStoredConnection()
        currentServerURL = ""
        connectionStatus = .disconnected
    }
}
```

## 📊 Quality Gates

### Settings System Requirements
- [ ] All major app features have configuration options
- [ ] Voice settings control your voice system effectively
- [ ] Kanban settings customize your Kanban board behavior
- [ ] Settings persist across app launches
- [ ] Settings changes take effect immediately
- [ ] Reset options work correctly for all sections
- [ ] Settings are organized logically and easy to find

### Integration Requirements
- [ ] Voice settings integrate with VoiceManager and SpeechRecognitionService
- [ ] Kanban settings affect KanbanBoardView behavior
- [ ] Notification settings prepare for BETA's push notification system
- [ ] Connection settings work with existing WebSocket service
- [ ] All settings are accessible from the main DashboardTabView

## 🎯 Success Criteria

### Comprehensive Configuration
- [ ] Users can configure all voice features you built
- [ ] Users can customize Kanban board behavior
- [ ] Users can manage server connections and sync preferences
- [ ] Users can test and troubleshoot voice recognition
- [ ] Settings provide clear explanations and helpful defaults

### User Experience Excellence
- [ ] Settings interface feels native and polished
- [ ] Changes provide immediate visual feedback
- [ ] Help and explanation text guides users effectively
- [ ] Advanced features are available but not overwhelming
- [ ] Settings reset and troubleshooting options work reliably

## 🚀 Development Strategy

### Week 1: Core Settings Infrastructure
- Main SettingsTabView and navigation structure
- Voice settings for your voice system
- Kanban settings for your board system
- Settings persistence and data management

### Week 2: Advanced Features & Polish
- Voice testing and troubleshooting interface
- Connection management and QR integration
- Advanced settings and developer options
- Help system and user guidance

## Priority

**HIGH** - This completes the user experience for all the sophisticated features you've built. Your deep knowledge of the voice and Kanban systems makes you the ideal specialist to create their configuration interfaces.

## Expected Timeline

**Week 1**: Core settings system and main feature configurations  
**Week 2**: Advanced features, testing interfaces, and polish

## Your Achievement Journey

**Task 1**: ✅ iOS Kanban Board System (COMPLETE)  
**Task 2**: ✅ iOS Voice Interface System (COMPLETE)  
**Task 3**: ✅ Voice Integration with Dashboard (COMPLETE)  
**Task 4**: ✅ iOS Integration Testing & End-to-End Validation (COMPLETE)  
**Task 5**: ✅ Advanced Testing Automation (COMPLETE)  
**Task 6**: ✅ iOS Architecture Viewer Completion (COMPLETE)  
**Task 7**: ✅ Kanban Backend Integration Testing (COMPLETE)  
**Task 8**: 🔄 Settings & Configuration System

You're the perfect specialist for this task because you built the voice and Kanban systems that need configuration, and you understand the user experience requirements from your extensive UI work. Let's give users complete control over the sophisticated features you've created! ⚙️✨📱