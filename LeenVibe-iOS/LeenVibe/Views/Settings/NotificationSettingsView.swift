import SwiftUI
import UserNotifications

/// Notification Settings view for configuring push notifications and in-app alerts
/// Manages all notification preferences for the LeenVibe app
struct NotificationSettingsView: View {
    
    // MARK: - Properties
    
    @StateObject private var settingsManager = SettingsManager.shared
    @State private var notificationAuthStatus: UNAuthorizationStatus = .notDetermined
    @State private var isRequestingPermission = false
    @State private var showingQuietHours = false
    @State private var showingTestNotification = false
    
    // MARK: - Body
    
    var body: some View {
        List {
            // Permission Status
            permissionStatusSection
            
            // Push Notifications
            pushNotificationsSection
            
            // In-App Notifications
            inAppNotificationsSection
            
            // Notification Types
            notificationTypesSection
            
            // Quiet Hours
            quietHoursSection
            
            // Testing & Management
            testingSection
        }
        .navigationTitle("Notifications")
        .navigationBarTitleDisplayMode(.inline)
        .onAppear {
            checkNotificationPermission()
        }
        .sheet(isPresented: $showingQuietHours) {
            QuietHoursSettingsView()
        }
        .alert("Test Notification", isPresented: $showingTestNotification) {
            Button("Send") {
                sendTestNotification()
            }
            Button("Cancel", role: .cancel) { }
        } message: {
            Text("Send a test notification to verify your settings?")
        }
    }
    
    // MARK: - View Sections
    
    private var permissionStatusSection: some View {
        Section("Permission Status") {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Notification Permission")
                        .fontWeight(.medium)
                    
                    HStack {
                        permissionStatusIndicator
                        Text(permissionStatusText)
                            .foregroundColor(.secondary)
                    }
                }
                
                Spacer()
                
                if notificationAuthStatus == .notDetermined || notificationAuthStatus == .denied {
                    if isRequestingPermission {
                        ProgressView()
                            .controlSize(.small)
                    } else {
                        Button(notificationAuthStatus == .denied ? "Settings" : "Request") {
                            handlePermissionAction()
                        }
                        .buttonStyle(.bordered)
                        .controlSize(.small)
                    }
                }
            }
            
            if notificationAuthStatus == .denied {
                VStack(alignment: .leading, spacing: 8) {
                    Text("Notification Permission Required")
                        .font(.subheadline)
                        .fontWeight(.medium)
                        .foregroundColor(.orange)
                    
                    Text("To receive push notifications, please enable notifications for LeenVibe in iOS Settings.")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                .padding(.vertical, 4)
            }
        }
    }
    
    private var pushNotificationsSection: some View {
        Section("Push Notifications") {
            Toggle("Enable Push Notifications", isOn: $settingsManager.notificationSettings.pushNotificationsEnabled)
                .disabled(notificationAuthStatus != .authorized)
                .onChange(of: settingsManager.notificationSettings.pushNotificationsEnabled) { _, enabled in
                    handlePushNotificationsToggle(enabled)
                }
            
            if settingsManager.notificationSettings.pushNotificationsEnabled && notificationAuthStatus == .authorized {
                Toggle("Task Notifications", isOn: $settingsManager.notificationSettings.taskNotificationsEnabled)
                
                Toggle("Voice Command Results", isOn: $settingsManager.notificationSettings.voiceNotificationsEnabled)
                
                Toggle("System Notifications", isOn: $settingsManager.notificationSettings.systemNotificationsEnabled)
                
                VStack(alignment: .leading, spacing: 8) {
                    Text("Push Notification Examples")
                        .font(.subheadline)
                        .fontWeight(.medium)
                    
                    VStack(alignment: .leading, spacing: 4) {
                        if settingsManager.notificationSettings.taskNotificationsEnabled {
                            NotificationPreview(
                                title: "Task Completed",
                                body: "Fix login bug has been moved to Done",
                                type: .task
                            )
                        }
                        
                        if settingsManager.notificationSettings.voiceNotificationsEnabled {
                            NotificationPreview(
                                title: "Voice Command",
                                body: "Successfully created task: Review settings",
                                type: .voice
                            )
                        }
                        
                        if settingsManager.notificationSettings.systemNotificationsEnabled {
                            NotificationPreview(
                                title: "Connection Lost",
                                body: "Reconnecting to LeenVibe server...",
                                type: .system
                            )
                        }
                    }
                }
                .padding(.vertical, 4)
            }
        }
    }
    
    private var inAppNotificationsSection: some View {
        Section("In-App Notifications") {
            Toggle("Banner Notifications", isOn: $settingsManager.notificationSettings.bannerNotificationsEnabled)
            
            Toggle("Sound Effects", isOn: $settingsManager.notificationSettings.soundEffectsEnabled)
            
            Toggle("Haptic Feedback", isOn: $settingsManager.notificationSettings.hapticFeedbackEnabled)
                .onChange(of: settingsManager.notificationSettings.hapticFeedbackEnabled) { _, enabled in
                    if enabled {
                        testHapticFeedback()
                    }
                }
            
            Toggle("Notification Badge", isOn: $settingsManager.notificationSettings.notificationBadgeEnabled)
            
            VStack(alignment: .leading, spacing: 8) {
                Text("In-App Notification Preview")
                    .font(.subheadline)
                    .fontWeight(.medium)
                
                if settingsManager.notificationSettings.bannerNotificationsEnabled {
                    HStack {
                        Image(systemName: "checkmark.circle.fill")
                            .foregroundColor(.green)
                        
                        VStack(alignment: .leading, spacing: 2) {
                            Text("Task Created")
                                .font(.caption)
                                .fontWeight(.medium)
                            
                            Text("New task added to backlog")
                                .font(.caption2)
                                .foregroundColor(.secondary)
                        }
                        
                        Spacer()
                    }
                    .padding(.horizontal, 12)
                    .padding(.vertical, 8)
                    .background(Color(.systemGray6))
                    .cornerRadius(8)
                } else {
                    Text("Banner notifications disabled")
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .italic()
                }
            }
            .padding(.vertical, 4)
        }
    }
    
    private var notificationTypesSection: some View {
        Section("Notification Types") {
            NotificationTypeRow(
                icon: "plus.circle",
                iconColor: .green,
                title: "Task Created",
                description: "When new tasks are added",
                isEnabled: $settingsManager.notificationSettings.taskCreatedNotifications
            )
            
            NotificationTypeRow(
                icon: "checkmark.circle",
                iconColor: .blue,
                title: "Task Completed",
                description: "When tasks are marked as done",
                isEnabled: $settingsManager.notificationSettings.taskCompletedNotifications
            )
            
            NotificationTypeRow(
                icon: "clock.badge.exclamationmark",
                iconColor: .orange,
                title: "Task Overdue",
                description: "When tasks pass their due date",
                isEnabled: $settingsManager.notificationSettings.taskOverdueNotifications
            )
            
            NotificationTypeRow(
                icon: "mic.badge.plus",
                iconColor: .purple,
                title: "Voice Command Results",
                description: "Confirmation of voice actions",
                isEnabled: $settingsManager.notificationSettings.voiceCommandResultNotifications
            )
            
            NotificationTypeRow(
                icon: "network",
                iconColor: .red,
                title: "Server Connection",
                description: "Connection status changes",
                isEnabled: $settingsManager.notificationSettings.serverConnectionNotifications
            )
        }
    }
    
    private var quietHoursSection: some View {
        Section("Quiet Hours") {
            Toggle("Enable Quiet Hours", isOn: $settingsManager.notificationSettings.quietHoursEnabled)
            
            if settingsManager.notificationSettings.quietHoursEnabled {
                HStack {
                    Text("Start Time")
                    Spacer()
                    DatePicker(
                        "",
                        selection: $settingsManager.notificationSettings.quietHoursStart,
                        displayedComponents: .hourAndMinute
                    )
                    .labelsHidden()
                }
                
                HStack {
                    Text("End Time")
                    Spacer()
                    DatePicker(
                        "",
                        selection: $settingsManager.notificationSettings.quietHoursEnd,
                        displayedComponents: .hourAndMinute
                    )
                    .labelsHidden()
                }
                
                VStack(alignment: .leading, spacing: 8) {
                    Text("Quiet Hours Schedule")
                        .font(.subheadline)
                        .fontWeight(.medium)
                    
                    Text("Notifications will be silenced from \(formatTime(settingsManager.notificationSettings.quietHoursStart)) to \(formatTime(settingsManager.notificationSettings.quietHoursEnd))")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                .padding(.vertical, 4)
            }
            
            Button(action: { showingQuietHours = true }) {
                SettingsRow(
                    icon: "moon.circle",
                    iconColor: .indigo,
                    title: "Advanced Quiet Hours",
                    subtitle: "Custom schedules and exceptions"
                )
            }
            .buttonStyle(.plain)
        }
    }
    
    private var testingSection: some View {
        Section("Testing & Management") {
            Button(action: { showingTestNotification = true }) {
                SettingsRow(
                    icon: "bell.badge",
                    iconColor: .blue,
                    title: "Send Test Notification",
                    subtitle: "Verify notification settings"
                )
            }
            .buttonStyle(.plain)
            .disabled(notificationAuthStatus != .authorized)
            
            Button(action: { clearNotificationHistory() }) {
                SettingsRow(
                    icon: "trash",
                    iconColor: .orange,
                    title: "Clear Notification History",
                    subtitle: "Remove delivered notifications"
                )
            }
            .buttonStyle(.plain)
            
            NavigationLink("Notification History") {
                NotificationHistoryView()
            }
            
            Button(action: { resetNotificationSettings() }) {
                SettingsRow(
                    icon: "arrow.clockwise",
                    iconColor: .red,
                    title: "Reset Notification Settings",
                    subtitle: "Restore default notification preferences"
                )
            }
            .buttonStyle(.plain)
        }
    }
    
    // MARK: - Helper Properties
    
    private var permissionStatusIndicator: some View {
        Image(systemName: permissionStatusIcon)
            .foregroundColor(permissionStatusColor)
    }
    
    private var permissionStatusIcon: String {
        switch notificationAuthStatus {
        case .authorized:
            return "checkmark.circle.fill"
        case .denied:
            return "xmark.circle.fill"
        case .notDetermined:
            return "questionmark.circle"
        case .provisional:
            return "checkmark.circle"
        case .ephemeral:
            return "clock.circle"
        @unknown default:
            return "questionmark.circle"
        }
    }
    
    private var permissionStatusColor: Color {
        switch notificationAuthStatus {
        case .authorized:
            return .green
        case .denied:
            return .red
        case .notDetermined:
            return .orange
        case .provisional:
            return .yellow
        case .ephemeral:
            return .blue
        @unknown default:
            return .gray
        }
    }
    
    private var permissionStatusText: String {
        switch notificationAuthStatus {
        case .authorized:
            return "Authorized"
        case .denied:
            return "Denied"
        case .notDetermined:
            return "Not Requested"
        case .provisional:
            return "Provisional"
        case .ephemeral:
            return "Ephemeral"
        @unknown default:
            return "Unknown"
        }
    }
    
    // MARK: - Actions
    
    private func checkNotificationPermission() {
        UNUserNotificationCenter.current().getNotificationSettings { settings in
            DispatchQueue.main.async {
                notificationAuthStatus = settings.authorizationStatus
            }
        }
    }
    
    private func handlePermissionAction() {
        if notificationAuthStatus == .denied {
            // Open system settings
            if let settingsURL = URL(string: UIApplication.openSettingsURLString) {
                UIApplication.shared.open(settingsURL)
            }
        } else {
            // Request permission
            requestNotificationPermission()
        }
    }
    
    private func requestNotificationPermission() {
        isRequestingPermission = true
        
        UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound, .badge]) { granted, error in
            DispatchQueue.main.async {
                isRequestingPermission = false
                checkNotificationPermission()
                
                if granted {
                    settingsManager.notificationSettings.pushNotificationsEnabled = true
                }
            }
        }
    }
    
    private func handlePushNotificationsToggle(_ enabled: Bool) {
        if enabled && notificationAuthStatus != .authorized {
            requestNotificationPermission()
        }
    }
    
    private func testHapticFeedback() {
        let impact = UIImpactFeedbackGenerator(style: .medium)
        impact.impactOccurred()
    }
    
    private func sendTestNotification() {
        let content = UNMutableNotificationContent()
        content.title = "Test Notification"
        content.body = "This is a test notification from LeenVibe"
        content.sound = settingsManager.notificationSettings.soundEffectsEnabled ? .default : nil
        
        let request = UNNotificationRequest(
            identifier: "test-notification",
            content: content,
            trigger: UNTimeIntervalNotificationTrigger(timeInterval: 1, repeats: false)
        )
        
        UNUserNotificationCenter.current().add(request)
    }
    
    private func clearNotificationHistory() {
        UNUserNotificationCenter.current().removeAllDeliveredNotifications()
    }
    
    private func resetNotificationSettings() {
        settingsManager.resetSettings(NotificationSettings.self)
    }
    
    private func formatTime(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.timeStyle = .short
        return formatter.string(from: date)
    }
}

// MARK: - Supporting Views

struct NotificationTypeRow: View {
    let icon: String
    let iconColor: Color
    let title: String
    let description: String
    @Binding var isEnabled: Bool
    
    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .font(.system(size: 16, weight: .medium))
                .foregroundColor(iconColor)
                .frame(width: 24, height: 24)
                .background(iconColor.opacity(0.15))
                .clipShape(RoundedRectangle(cornerRadius: 6))
            
            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(.body)
                    .fontWeight(.medium)
                
                Text(description)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
            
            Toggle("", isOn: $isEnabled)
                .labelsHidden()
        }
        .padding(.vertical, 4)
    }
}

struct NotificationPreview: View {
    let title: String
    let message: String
    let type: NotificationType
    
    enum NotificationType {
        case task, voice, system
        
        var color: Color {
            switch self {
            case .task: return .green
            case .voice: return .purple
            case .system: return .orange
            }
        }
        
        var icon: String {
            switch self {
            case .task: return "checkmark.circle.fill"
            case .voice: return "mic.circle.fill"
            case .system: return "exclamationmark.triangle.fill"
            }
        }
    }
    
    var body: some View {
        HStack(spacing: 8) {
            Image(systemName: type.icon)
                .foregroundColor(type.color)
                .font(.caption)
            
            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(.caption)
                    .fontWeight(.semibold)
                
                Text(message)
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 6)
        .background(Color(.systemGray6))
        .cornerRadius(6)
    }
}

struct QuietHoursSettingsView: View {
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            List {
                Section("Advanced Quiet Hours") {
                    Text("Custom schedules and exceptions")
                }
            }
            .navigationTitle("Quiet Hours")
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


// MARK: - Preview

#Preview {
    NavigationView {
        NotificationSettingsView()
    }
}