import SwiftUI
import UserNotifications

@available(iOS 18.0, macOS 14.0, *)
struct TaskNotificationSettingsView: View {
    @ObservedObject var settingsManager: SettingsManager
    @StateObject private var notificationService = PushNotificationService.shared
    @State private var taskCompletionNotifications = true
    @State private var highPriorityTaskAlerts = true
    @State private var dailyProgressSummary = false
    @State private var overdueTaskReminders = true
    @State private var newTaskAssignments = true
    @State private var reminderTime = Date()
    @State private var quietHoursEnabled = false
    @State private var quietHoursStart = Calendar.current.date(from: DateComponents(hour: 22, minute: 0))!
    @State private var quietHoursEnd = Calendar.current.date(from: DateComponents(hour: 8, minute: 0))!
    @State private var showingPermissionAlert = false
    @Environment(\.dismiss) private var dismiss
    
    init(settingsManager: SettingsManager) {
        self.settingsManager = settingsManager
    }
    
    init() {
        self.settingsManager = SettingsManager.shared
    }
    
    var body: some View {
        NavigationView {
            List {
                Section {
                    Text("Configure when and how you receive notifications about task updates, completions, and reminders.")
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .padding(.vertical, 4)
                }
                
                Section("Permission Status") {
                    HStack {
                        Image(systemName: notificationService.isAuthorized ? "checkmark.circle.fill" : "exclamationmark.triangle.fill")
                            .foregroundColor(notificationService.isAuthorized ? .green : .orange)
                        VStack(alignment: .leading) {
                            Text(notificationService.isAuthorized ? "Notifications Enabled" : "Notifications Disabled")
                                .font(.headline)
                            Text(notificationService.isAuthorized ? "You'll receive task notifications" : "Enable in Settings to receive notifications")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                        Spacer()
                        if !notificationService.isAuthorized {
                            Button("Enable") {
                                requestNotificationPermission()
                            }
                            .foregroundColor(Color(.systemBlue))
                        }
                    }
                    .padding(.vertical, 4)
                }
                
                Section("Task Updates") {
                    Toggle("Task Completion Alerts", isOn: $taskCompletionNotifications)
                    Toggle("High Priority Task Alerts", isOn: $highPriorityTaskAlerts)
                    Toggle("Overdue Task Reminders", isOn: $overdueTaskReminders)
                    Toggle("New Task Assignments", isOn: $newTaskAssignments)
                }
                
                Section("Daily Summaries") {
                    Toggle("Daily Progress Summary", isOn: $dailyProgressSummary)
                    
                    if dailyProgressSummary {
                        DatePicker(
                            "Summary Time",
                            selection: $reminderTime,
                            displayedComponents: .hourAndMinute
                        )
                        .datePickerStyle(CompactDatePickerStyle())
                    }
                }
                
                Section("Quiet Hours") {
                    Toggle("Enable Quiet Hours", isOn: $quietHoursEnabled)
                    
                    if quietHoursEnabled {
                        DatePicker(
                            "Start Time",
                            selection: $quietHoursStart,
                            displayedComponents: .hourAndMinute
                        )
                        .datePickerStyle(CompactDatePickerStyle())
                        
                        DatePicker(
                            "End Time",
                            selection: $quietHoursEnd,
                            displayedComponents: .hourAndMinute
                        )
                        .datePickerStyle(CompactDatePickerStyle())
                        
                        Text("No notifications will be sent during quiet hours except for urgent tasks.")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }
                
                Section("Notification Style") {
                    NavigationLink(destination: NotificationStyleView()) {
                        HStack {
                            Image(systemName: "app.badge")
                                .foregroundColor(Color(.systemBlue))
                            VStack(alignment: .leading) {
                                Text("Notification Style")
                                Text("Banner, Alert, Badge")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                        }
                    }
                }
                
                Section("Test Notifications") {
                    Button("Send Test Notification") {
                        sendTestNotification()
                    }
                    .foregroundColor(Color(.systemBlue))
                    .disabled(!notificationService.isAuthorized)
                    
                    if !notificationService.isAuthorized {
                        Text("Enable notification permissions to test")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }
            }
            .navigationTitle("Task Notifications")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Done") {
                        saveSettings()
                        dismiss()
                    }
                }
            }
        }
    }
    
    private func saveSettings() {
        // Save notification preferences to SettingsManager
        // In a real implementation, these would be stored in UserDefaults or Core Data
        print("Saving notification settings:")
        print("- Task Completion: \(taskCompletionNotifications)")
        print("- High Priority: \(highPriorityTaskAlerts)")
        print("- Overdue Reminders: \(overdueTaskReminders)")
        print("- Daily Summary: \(dailyProgressSummary)")
        print("- Quiet Hours: \(quietHoursEnabled)")
    }
    
    private func sendTestNotification() {
        guard notificationService.isAuthorized else {
            showingPermissionAlert = true
            return
        }
        
        // Create test request using the proper LocalNotificationRequest structure
        let request = LocalNotificationRequest(
            id: "test-notification-\(Date().timeIntervalSince1970)",
            title: "LeanVibe Test Notification",
            body: "This is a test notification from your task management settings.",
            category: "TASK_NOTIFICATION_TEST",
            trigger: .timeInterval(1, repeats: false)
        )
        
        Task {
            let success = await notificationService.scheduleLocalNotification(request)
            DispatchQueue.main.async {
                print("Test notification \(success ? "scheduled successfully" : "failed to schedule")")
            }
        }
    }
    
    private func requestNotificationPermission() {
        UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .badge, .sound]) { granted, error in
            DispatchQueue.main.async {
                if granted {
                    notificationService.isAuthorized = true
                } else {
                    showingPermissionAlert = true
                }
            }
        }
    }
}

// Supporting view for notification style configuration
@available(iOS 18.0, macOS 14.0, *)
struct NotificationStyleView: View {
    @State private var showBanners = true
    @State private var showAlerts = false
    @State private var showBadges = true
    @State private var playSounds = true
    
    var body: some View {
        List {
            Section("Display Style") {
                Toggle("Show Banners", isOn: $showBanners)
                Toggle("Show Alerts", isOn: $showAlerts)
                Toggle("Show Badge Count", isOn: $showBadges)
            }
            
            Section("Sound & Haptics") {
                Toggle("Play Notification Sounds", isOn: $playSounds)
                
                if playSounds {
                    NavigationLink("Notification Sound") {
                        NotificationSoundPicker()
                    }
                }
            }
            
            Section {
                Text("These settings control how task notifications appear on your device. Changes take effect immediately.")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .navigationTitle("Notification Style")
        .navigationBarTitleDisplayMode(.large)
    }
}

// Placeholder for notification sound picker
@available(iOS 18.0, macOS 14.0, *)
struct NotificationSoundPicker: View {
    @State private var selectedSound = "Default"
    private let availableSounds = ["Default", "Chime", "Bell", "Ping", "Pop"]
    
    var body: some View {
        List {
            ForEach(availableSounds, id: \.self) { sound in
                Button(action: {
                    selectedSound = sound
                }) {
                    HStack {
                        Text(sound)
                            .foregroundColor(.primary)
                        Spacer()
                        if selectedSound == sound {
                            Image(systemName: "checkmark")
                                .foregroundColor(Color(.systemBlue))
                        }
                    }
                }
            }
        }
        .navigationTitle("Notification Sound")
    }
}

#Preview {
    TaskNotificationSettingsView()
}