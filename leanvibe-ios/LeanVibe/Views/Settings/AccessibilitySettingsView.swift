import SwiftUI

/// Accessibility Settings view for configuring accessibility features
/// Provides comprehensive accessibility controls for visual, motor, and cognitive needs
@available(iOS 18.0, macOS 14.0, *)
@available(iOS 18.0, macOS 14.0, *)
struct AccessibilitySettingsView: View {
    
    // MARK: - Properties
    
    @State private var settingsManager = SettingsManager.shared
    @State private var showingAccessibilityGuide = false
    
    // MARK: - Body
    
    var body: some View {
        List {
            // Visual Accessibility
            visualAccessibilitySection
            
            // Voice & Audio Accessibility
            voiceAccessibilitySection
            
            // Motor Accessibility
            motorAccessibilitySection
            
            // System Integration
            systemIntegrationSection
            
            // Help & Resources
            helpSection
        }
        .navigationTitle("Accessibility")
        .navigationBarTitleDisplayMode(.inline)
        .sheet(isPresented: $showingAccessibilityGuide) {
            AccessibilityGuideView()
        }
    }
    
    // MARK: - View Sections
    
    private var visualAccessibilitySection: some View {
        Section("Visual Accessibility") {
            Toggle("High Contrast Mode", isOn: $settingsManager.accessibility.highContrastMode)
                .onChange(of: settingsManager.accessibility.highContrastMode) { _, enabled in
                    handleHighContrastToggle(enabled)
                }
            
            Toggle("Reduce Motion", isOn: $settingsManager.accessibility.reduceMotion)
                .onChange(of: settingsManager.accessibility.reduceMotion) { _, enabled in
                    handleReduceMotionToggle(enabled)
                }
            
            Toggle("Large Font Size", isOn: $settingsManager.accessibility.largeFontSize)
                .onChange(of: settingsManager.accessibility.largeFontSize) { _, enabled in
                    handleLargeFontToggle(enabled)
                }
            
            Toggle("Bold Text", isOn: $settingsManager.accessibility.boldText)
                .onChange(of: settingsManager.accessibility.boldText) { _, enabled in
                    handleBoldTextToggle(enabled)
                }
            
            VStack(alignment: .leading, spacing: 8) {
                Text("Current Font Preview")
                    .font(.subheadline)
                    .fontWeight(.medium)
                
                Text("Sample text with current accessibility settings applied")
                    .font(previewFont)
                    .fontWeight(settingsManager.accessibility.boldText ? .bold : .regular)
                    .padding()
                    .background(backgroundColorForPreview)
                    .foregroundColor(textColorForPreview)
                    .cornerRadius(8)
            }
            .padding(.vertical, 4)
        }
    }
    
    private var voiceAccessibilitySection: some View {
        Section("Voice & Audio") {
            Toggle("VoiceOver Optimizations", isOn: $settingsManager.accessibility.voiceOverOptimizations)
            
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Text("Speech Rate Adjustment")
                    Spacer()
                    Text("\(Int(settingsManager.accessibility.speechRateAdjustment * 100))%")
                        .foregroundColor(.secondary)
                }
                
                Slider(
                    value: $settingsManager.accessibility.speechRateAdjustment,
                    in: 0.5...2.0,
                    step: 0.1
                )
                
                Text("Adjust speech synthesis speed for voice feedback")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            .padding(.vertical, 4)
            
            Toggle("Extended Voice Commands", isOn: $settingsManager.accessibility.extendedVoiceCommands)
            
            VStack(alignment: .leading, spacing: 8) {
                Text("Voice Command Examples")
                    .font(.subheadline)
                    .fontWeight(.medium)
                
                VStack(alignment: .leading, spacing: 4) {
                    Text("• \"Navigate to settings\"")
                    Text("• \"Read current task\"")
                    Text("• \"Move task to done\"")
                    Text("• \"Show help for this screen\"")
                }
                .font(.caption)
                .foregroundColor(.secondary)
                .padding(.leading)
            }
            .padding(.vertical, 4)
        }
    }
    
    private var motorAccessibilitySection: some View {
        Section("Motor Accessibility") {
            Toggle("Extended Touch Targets", isOn: $settingsManager.accessibility.extendedTouchTargets)
                .onChange(of: settingsManager.accessibility.extendedTouchTargets) { _, enabled in
                    handleExtendedTouchTargetsToggle(enabled)
                }
            
            Toggle("Reduce Gestures", isOn: $settingsManager.accessibility.reduceGestures)
                .onChange(of: settingsManager.accessibility.reduceGestures) { _, enabled in
                    handleReduceGesturesToggle(enabled)
                }
            
            Toggle("One-Handed Mode", isOn: $settingsManager.accessibility.oneHandedMode)
                .onChange(of: settingsManager.accessibility.oneHandedMode) { _, enabled in
                    handleOneHandedModeToggle(enabled)
                }
            
            VStack(alignment: .leading, spacing: 8) {
                Text("Touch Target Preview")
                    .font(.subheadline)
                    .fontWeight(.medium)
                
                HStack(spacing: 16) {
                    Button("Normal") {}
                        .buttonStyle(.bordered)
                        .controlSize(settingsManager.accessibility.extendedTouchTargets ? .large : .regular)
                    
                    Button("Extended") {}
                        .buttonStyle(.bordered)
                        .controlSize(settingsManager.accessibility.extendedTouchTargets ? .large : .regular)
                }
                
                Text("Touch targets are automatically enlarged when enabled")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            .padding(.vertical, 4)
        }
    }
    
    private var systemIntegrationSection: some View {
        Section("System Integration") {
            Button(action: { openSystemAccessibilitySettings() }) {
                SettingsRow(
                    icon: "gear",
                    iconColor: .blue,
                    title: "System Accessibility",
                    subtitle: "Open iOS Accessibility settings"
                )
            }
            .buttonStyle(.plain)
            
            Button(action: { testVoiceOverCompatibility() }) {
                SettingsRow(
                    icon: "speaker.wave.3",
                    iconColor: .green,
                    title: "Test VoiceOver",
                    subtitle: "Verify VoiceOver functionality"
                )
            }
            .buttonStyle(.plain)
            
            Button(action: { testSwitchControlCompatibility() }) {
                SettingsRow(
                    icon: "switch.2",
                    iconColor: .orange,
                    title: "Test Switch Control",
                    subtitle: "Verify Switch Control compatibility"
                )
            }
            .buttonStyle(.plain)
            
            VStack(alignment: .leading, spacing: 8) {
                Text("Detected Accessibility Features")
                    .font(.subheadline)
                    .fontWeight(.medium)
                
                VStack(alignment: .leading, spacing: 4) {
                    AccessibilityFeatureStatus(
                        feature: "VoiceOver",
                        isEnabled: UIAccessibility.isVoiceOverRunning
                    )
                    
                    AccessibilityFeatureStatus(
                        feature: "Switch Control",
                        isEnabled: UIAccessibility.isSwitchControlRunning
                    )
                    
                    AccessibilityFeatureStatus(
                        feature: "Reduced Motion",
                        isEnabled: UIAccessibility.isReduceMotionEnabled
                    )
                    
                    AccessibilityFeatureStatus(
                        feature: "Bold Text",
                        isEnabled: UIAccessibility.isBoldTextEnabled
                    )
                }
            }
            .padding(.vertical, 4)
        }
    }
    
    private var helpSection: some View {
        Section("Help & Resources") {
            Button(action: { showingAccessibilityGuide = true }) {
                SettingsRow(
                    icon: "book",
                    iconColor: .blue,
                    title: "Accessibility Guide",
                    subtitle: "Learn about accessibility features"
                )
            }
            .buttonStyle(.plain)
            
            Button(action: { reportAccessibilityIssue() }) {
                SettingsRow(
                    icon: "exclamationmark.bubble",
                    iconColor: .red,
                    title: "Report Accessibility Issue",
                    subtitle: "Help us improve accessibility"
                )
            }
            .buttonStyle(.plain)
            
            Button(action: { resetAccessibilitySettings() }) {
                SettingsRow(
                    icon: "arrow.clockwise",
                    iconColor: .orange,
                    title: "Reset Accessibility Settings",
                    subtitle: "Restore default accessibility settings"
                )
            }
            .buttonStyle(.plain)
        }
    }
    
    // MARK: - Helper Properties
    
    private var previewFont: Font {
        if settingsManager.accessibility.largeFontSize {
            return .title2
        } else {
            return .body
        }
    }
    
    private var backgroundColorForPreview: Color {
        if settingsManager.accessibility.highContrastMode {
            return Color.black
        } else {
            return Color(.systemGray6)
        }
    }
    
    private var textColorForPreview: Color {
        if settingsManager.accessibility.highContrastMode {
            return Color.white
        } else {
            return Color.primary
        }
    }
    
    // MARK: - Actions
    
    private func handleHighContrastToggle(_ enabled: Bool) {
        // Apply high contrast mode to app theme
        print("High contrast mode: \(enabled)")
    }
    
    private func handleReduceMotionToggle(_ enabled: Bool) {
        // Apply reduced motion settings
        print("Reduce motion: \(enabled)")
    }
    
    private func handleLargeFontToggle(_ enabled: Bool) {
        // Apply large font settings
        print("Large font: \(enabled)")
    }
    
    private func handleBoldTextToggle(_ enabled: Bool) {
        // Apply bold text settings
        print("Bold text: \(enabled)")
    }
    
    private func handleExtendedTouchTargetsToggle(_ enabled: Bool) {
        // Apply extended touch target settings
        print("Extended touch targets: \(enabled)")
    }
    
    private func handleReduceGesturesToggle(_ enabled: Bool) {
        // Apply reduced gestures settings
        print("Reduce gestures: \(enabled)")
    }
    
    private func handleOneHandedModeToggle(_ enabled: Bool) {
        // Apply one-handed mode settings
        print("One-handed mode: \(enabled)")
    }
    
    private func openSystemAccessibilitySettings() {
        if let settingsURL = URL(string: UIApplication.openSettingsURLString) {
            UIApplication.shared.open(settingsURL)
        }
    }
    
    private func testVoiceOverCompatibility() {
        // Test VoiceOver compatibility
        print("Testing VoiceOver compatibility")
    }
    
    private func testSwitchControlCompatibility() {
        // Test Switch Control compatibility
        print("Testing Switch Control compatibility")
    }
    
    private func reportAccessibilityIssue() {
        // Open accessibility issue reporting
        print("Reporting accessibility issue")
    }
    
    private func resetAccessibilitySettings() {
        // Reset accessibility settings to defaults
        settingsManager.resetSettings(AccessibilitySettings.self)
    }
}

// MARK: - Supporting Views

@available(iOS 18.0, macOS 14.0, *)
struct AccessibilityFeatureStatus: View {
    let feature: String
    let isEnabled: Bool
    
    var body: some View {
        HStack {
            Image(systemName: isEnabled ? "checkmark.circle.fill" : "xmark.circle.fill")
                .foregroundColor(isEnabled ? .green : .gray)
            
            Text(feature)
                .font(.caption)
            
            Spacer()
            
            Text(isEnabled ? "Enabled" : "Disabled")
                .font(.caption)
                .foregroundColor(.secondary)
        }
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct AccessibilityGuideView: View {
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    // Introduction
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Accessibility in LeanVibe")
                            .font(.title2)
                            .fontWeight(.bold)
                        
                        Text("LeanVibe is designed to be accessible to everyone. Here's how to use our accessibility features:")
                            .foregroundColor(.secondary)
                    }
                    
                    // Visual Features
                    AccessibilityGuideSection(
                        title: "Visual Features",
                        icon: "eye",
                        features: [
                            "High Contrast Mode: Increases contrast for better visibility",
                            "Large Font Size: Makes text easier to read",
                            "Bold Text: Improves text visibility",
                            "Reduce Motion: Minimizes animations that may cause discomfort"
                        ]
                    )
                    
                    // Voice Features
                    AccessibilityGuideSection(
                        title: "Voice & Audio",
                        icon: "speaker.wave.3",
                        features: [
                            "VoiceOver Optimizations: Enhanced screen reader support",
                            "Extended Voice Commands: Additional voice control options",
                            "Speech Rate Adjustment: Customize voice feedback speed",
                            "Voice Navigation: Navigate the app using voice commands"
                        ]
                    )
                    
                    // Motor Features
                    AccessibilityGuideSection(
                        title: "Motor Accessibility",
                        icon: "hand.tap",
                        features: [
                            "Extended Touch Targets: Larger buttons for easier tapping",
                            "Reduce Gestures: Simplifies complex gestures",
                            "One-Handed Mode: Optimizes layout for single-hand use",
                            "Switch Control Support: Compatible with external switches"
                        ]
                    )
                    
                    // Voice Commands
                    VStack(alignment: .leading, spacing: 12) {
                        Label("Voice Commands", systemImage: "mic")
                            .font(.headline)
                            .foregroundColor(.blue)
                        
                        VStack(alignment: .leading, spacing: 8) {
                            Text("Try these voice commands:")
                                .fontWeight(.medium)
                            
                            VStack(alignment: .leading, spacing: 4) {
                                Text("• \"Hey LeanVibe, show settings\"")
                                Text("• \"Navigate to dashboard\"")
                                Text("• \"Create new task\"")
                                Text("• \"Read current screen\"")
                                Text("• \"Help with accessibility\"")
                            }
                            .font(.caption)
                            .foregroundColor(.secondary)
                            .padding(.leading)
                        }
                    }
                    
                    Spacer(minLength: 20)
                }
                .padding()
            }
            .navigationTitle("Accessibility Guide")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Done") {
                        dismiss()
                    }
                }
            }
        }
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct AccessibilityGuideSection: View {
    let title: String
    let icon: String
    let features: [String]
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Label(title, systemImage: icon)
                .font(.headline)
                .foregroundColor(.blue)
            
            VStack(alignment: .leading, spacing: 6) {
                ForEach(features, id: \.self) { feature in
                    HStack(alignment: .top, spacing: 8) {
                        Image(systemName: "checkmark.circle.fill")
                            .foregroundColor(.green)
                            .font(.caption)
                            .padding(.top, 2)
                        
                        Text(feature)
                            .font(.caption)
                            .fixedSize(horizontal: false, vertical: true)
                    }
                }
            }
            .padding(.leading)
        }
    }
}

// MARK: - Preview

#Preview {
    NavigationView {
        AccessibilitySettingsView()
    }
}