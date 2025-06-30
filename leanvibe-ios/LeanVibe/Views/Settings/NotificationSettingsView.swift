import SwiftUI
import UserNotifications

/// Notification Settings view for configuring push notifications and in-app alerts
/// Manages all notification preferences for the LeanVibe app
@available(iOS 18.0, macOS 14.0, *)
struct NotificationSettingsView: View {
    
    // MARK: - Properties
    
    @Environment(\.settingsManager) private var settingsManager
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
                    
                    Text("To receive push notifications, please enable notifications for LeanVibe in iOS Settings.")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                .padding(.vertical, 4)
            }
        }
    }
    
    private var pushNotificationsSection: some View {
        Section("Push Notifications") {
            Toggle("Enable Push Notifications", isOn: $settingsManager.notificationSettings.notificationsEnabled)
                .disabled(notificationAuthStatus != .authorized)
                .onChange(of: settingsManager.notificationSettings.notificationsEnabled) { _, enabled in
                    handlePushNotificationsToggle(enabled)
                }
            
            if settingsManager.notificationSettings.notificationsEnabled && notificationAuthStatus == .authorized {
                Toggle("Task Notifications", isOn: $settingsManager.notificationSettings.taskUpdates)
                
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
                                message: "Fix login bug has been moved to Done",
                                type: .task
                            )
                        }
                        
                        if settingsManager.notificationSettings.voiceNotificationsEnabled {
                            NotificationPreview(
                                title: "Voice Command",
                                message: "Successfully created task: Review settings",
                                type: .voice
                            )
                        }
                        
                        if settingsManager.notificationSettings.systemNotificationsEnabled {
                            NotificationPreview(
                                title: "Connection Lost",
                                message: "Reconnecting to LeanVibe server...",
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
            Toggle("Banner Notifications", isOn: $settingsManager.notificationSettings.notificationsEnabled)
            
            Toggle("Sound Effects", isOn: $settingsManager.notificationSettings.soundEnabled)
            
            Toggle("Vibration", isOn: $settingsManager.notificationSettings.vibrationEnabled)
                .onChange(of: settingsManager.notificationSettings.vibrationEnabled) { _, enabled in
                    if enabled {
                        testHapticFeedback()
                    }
                }
            
            
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
                isEnabled: $settingsManager.notificationSettings.taskUpdates
            )
            
            NotificationTypeRow(
                icon: "checkmark.circle",
                iconColor: .blue,
                title: "Task Completed",
                description: "When tasks are marked as done",
                isEnabled: $settingsManager.notificationSettings.taskUpdates
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
                        selection: Binding<Date>(
                            get: { 
                                DateFormatter.timeFormatter.date(from: settingsManager.notificationSettings.quietHoursStart) ?? Date()
                            },
                            set: { newValue in
                                settingsManager.notificationSettings.quietHoursStart = DateFormatter.timeFormatter.string(from: newValue)
                            }
                        ),
                        displayedComponents: .hourAndMinute
                    )
                    .labelsHidden()
                }
                
                HStack {
                    Text("End Time")
                    Spacer()
                    DatePicker(
                        "",
                        selection: Binding<Date>(
                            get: { 
                                DateFormatter.timeFormatter.date(from: settingsManager.notificationSettings.quietHoursEnd) ?? Date()
                            },
                            set: { newValue in
                                settingsManager.notificationSettings.quietHoursEnd = DateFormatter.timeFormatter.string(from: newValue)
                            }
                        ),
                        displayedComponents: .hourAndMinute
                    )
                    .labelsHidden()
                }
                
                VStack(alignment: .leading, spacing: 8) {
                    Text("Quiet Hours Schedule")
                        .font(.subheadline)
                        .fontWeight(.medium)
                    
                    Text("Notifications will be silenced from \(settingsManager.notificationSettings.quietHoursStart) to \(settingsManager.notificationSettings.quietHoursEnd)")
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
                NotificationHistoryView(pushService: PushNotificationService.shared)
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
            let authStatus = settings.authorizationStatus
            Task { @MainActor in
                notificationAuthStatus = authStatus
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
                    settingsManager.notificationSettings.notificationsEnabled = true
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
        content.body = "This is a test notification from LeanVibe"
        content.sound = settingsManager.notificationSettings.soundEnabled ? .default : nil
        
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

// MARK: - Date Formatter Extension

extension DateFormatter {
    static let timeFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateFormat = "HH:mm"
        return formatter
    }()
}

// MARK: - Preview

#Preview {
    NavigationView {
        NotificationSettingsView()
    }
}