import SwiftUI
import UserNotifications

/// Comprehensive notification settings and preferences UI
/// Provides granular control over notification types, timing, and personalization
struct NotificationSettingsView: View {
    
    @StateObject private var pushService = PushNotificationService()
    @StateObject private var contentManager: NotificationContentManager
    
    @State private var preferences: NotificationPreferences
    @State private var personalizationProfile: PersonalizationProfile
    @State private var showingPermissionAlert = false
    @State private var showingTestNotification = false
    @State private var isLoading = false
    
    init() {
        let pushService = PushNotificationService()
        let contentManager = NotificationContentManager(pushService: pushService)
        
        self._contentManager = StateObject(wrappedValue: contentManager)
        self._preferences = State(initialValue: contentManager.getNotificationPreferences())
        self._personalizationProfile = State(initialValue: contentManager.personalizationProfile ?? PersonalizationProfile())
    }
    
    var body: some View {
        NavigationView {
            Form {
                // Permission Status Section
                Section("Notification Status") {
                    PermissionStatusRow(
                        status: pushService.notificationPermissionStatus,
                        isRegistered: pushService.isRegisteredForRemoteNotifications
                    )
                    
                    if pushService.notificationPermissionStatus != .authorized {
                        Button("Enable Notifications") {
                            Task {
                                await requestPermissions()
                            }
                        }
                        .foregroundColor(.blue)
                    }
                }
                
                // Notification Types Section
                Section("Notification Types") {
                    NotificationTypeToggle(
                        title: "General Notifications",
                        description: "App updates, tips, and general information",
                        isEnabled: $preferences.allowGeneralNotifications,
                        icon: "bell.fill"
                    )
                    
                    NotificationTypeToggle(
                        title: "Daily Reminders",
                        description: "Meditation and wellness practice reminders",
                        isEnabled: $preferences.allowReminders,
                        icon: "clock.fill"
                    )
                    
                    NotificationTypeToggle(
                        title: "Achievements",
                        description: "Milestone celebrations and progress updates",
                        isEnabled: $preferences.allowAchievements,
                        icon: "trophy.fill"
                    )
                    
                    NotificationTypeToggle(
                        title: "Social Updates",
                        description: "Friend activities and community interactions",
                        isEnabled: $preferences.allowSocial,
                        icon: "person.2.fill"
                    )
                    
                    NotificationTypeToggle(
                        title: "System Notifications",
                        description: "Important app and account notifications",
                        isEnabled: $preferences.allowSystem,
                        icon: "gear.circle.fill"
                    )
                }
                
                // Timing & Schedule Section
                Section("Timing & Schedule") {
                    // Preferred reminder time
                    HStack {
                        Label("Preferred Time", systemImage: "clock")
                        Spacer()
                        DatePicker(
                            "",
                            selection: Binding(
                                get: { timeFromString(preferences.preferredTime) },
                                set: { preferences.preferredTime = timeToString($0) }
                            ),
                            displayedComponents: .hourAndMinute
                        )
                        .labelsHidden()
                    }
                    
                    // Quiet hours toggle
                    Toggle("Quiet Hours", isOn: $preferences.quietHoursEnabled)
                    
                    if preferences.quietHoursEnabled {
                        HStack {
                            Label("Start Time", systemImage: "moon.fill")
                            Spacer()
                            DatePicker(
                                "",
                                selection: Binding(
                                    get: { timeFromString(preferences.quietHoursStart) },
                                    set: { preferences.quietHoursStart = timeToString($0) }
                                ),
                                displayedComponents: .hourAndMinute
                            )
                            .labelsHidden()
                        }
                        
                        HStack {
                            Label("End Time", systemImage: "sun.max.fill")
                            Spacer()
                            DatePicker(
                                "",
                                selection: Binding(
                                    get: { timeFromString(preferences.quietHoursEnd) },
                                    set: { preferences.quietHoursEnd = timeToString($0) }
                                ),
                                displayedComponents: .hourAndMinute
                            )
                            .labelsHidden()
                        }
                    }
                }
                
                // Personalization Section
                Section("Personalization") {
                    NavigationLink(destination: PersonalizationView(profile: $personalizationProfile)) {
                        Label("Customize Experience", systemImage: "person.circle")
                    }
                    
                    HStack {
                        Label("Session Duration", systemImage: "timer")
                        Spacer()
                        Picker("Duration", selection: $personalizationProfile.preferredSessionDuration) {
                            ForEach([5, 10, 15, 20, 30], id: \.self) { duration in
                                Text("\(duration) min").tag(duration)
                            }
                        }
                        .pickerStyle(MenuPickerStyle())
                    }
                }
                
                // Management Section
                Section("Management") {
                    NavigationLink(destination: NotificationHistoryView(pushService: pushService)) {
                        Label("Notification History", systemImage: "list.bullet")
                    }
                    
                    NavigationLink(destination: CampaignManagementView(contentManager: contentManager)) {
                        Label("Manage Campaigns", systemImage: "calendar")
                    }
                    
                    Button("Test Notification") {
                        Task {
                            await sendTestNotification()
                        }
                    }
                    .foregroundColor(.blue)
                    
                    Button("Clear All Notifications") {
                        pushService.cancelAllNotifications()
                        pushService.clearBadge()
                    }
                    .foregroundColor(.red)
                }
                
                // Statistics Section
                if let metrics = contentManager.deliveryMetrics {
                    Section("Statistics") {
                        StatisticRow(title: "Total Sent", value: "\(metrics.totalSent)")
                        StatisticRow(title: "Delivered", value: "\(metrics.totalDelivered)")
                        StatisticRow(title: "Delivery Rate", value: "\(Int(metrics.deliveryRate * 100))%")
                        StatisticRow(title: "Last Updated", value: formatDate(metrics.lastUpdated))
                    }
                }
            }
            .navigationTitle("Notifications")
            .navigationBarTitleDisplayMode(.large)
            .onAppear {
                Task {
                    await loadSettings()
                }
            }
            .onChange(of: preferences) { _ in
                savePreferences()
            }
            .onChange(of: personalizationProfile) { _ in
                savePersonalizationProfile()
            }
            .alert("Notification Permission", isPresented: $showingPermissionAlert) {
                Button("Settings") {
                    openAppSettings()
                }
                Button("Cancel", role: .cancel) { }
            } message: {
                Text("To receive notifications, please enable them in Settings.")
            }
        }
    }
    
    // MARK: - Helper Methods
    
    private func loadSettings() async {
        await pushService.updatePermissionStatus()
        await contentManager.updateDeliveryMetrics()
        
        preferences = contentManager.getNotificationPreferences()
        if let profile = contentManager.personalizationProfile {
            personalizationProfile = profile
        }
    }
    
    private func requestPermissions() async {
        let granted = await pushService.requestNotificationPermissions()
        if !granted {
            showingPermissionAlert = true
        }
    }
    
    private func savePreferences() {
        contentManager.saveNotificationPreferences(preferences)
    }
    
    private func savePersonalizationProfile() {
        contentManager.updatePersonalizationProfile(personalizationProfile)
    }
    
    private func sendTestNotification() async {
        await pushService.sendWelcomeNotification()
        showingTestNotification = true
        
        DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
            showingTestNotification = false
        }
    }
    
    private func openAppSettings() {
        if let settingsUrl = URL(string: UIApplication.openSettingsURLString) {
            UIApplication.shared.open(settingsUrl)
        }
    }
    
    private func timeFromString(_ timeString: String) -> Date {
        let formatter = DateFormatter()
        formatter.dateFormat = "HH:mm"
        return formatter.date(from: timeString) ?? Date()
    }
    
    private func timeToString(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "HH:mm"
        return formatter.string(from: date)
    }
    
    private func formatDate(_ date: Date) -> String {
        let formatter = RelativeDateTimeFormatter()
        return formatter.localizedString(for: date, relativeTo: Date())
    }
}

// MARK: - Supporting Views

struct PermissionStatusRow: View {
    let status: UNAuthorizationStatus
    let isRegistered: Bool
    
    var body: some View {
        HStack {
            Label("Permission Status", systemImage: statusIcon)
                .foregroundColor(statusColor)
            
            Spacer()
            
            VStack(alignment: .trailing, spacing: 2) {
                Text(statusText)
                    .font(.headline)
                    .foregroundColor(statusColor)
                
                if isRegistered {
                    Text("APNs Registered")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
        }
    }
    
    private var statusIcon: String {
        switch status {
        case .authorized:
            return "checkmark.circle.fill"
        case .denied:
            return "xmark.circle.fill"
        case .notDetermined:
            return "questionmark.circle.fill"
        case .provisional:
            return "clock.circle.fill"
        case .ephemeral:
            return "timer.circle.fill"
        @unknown default:
            return "questionmark.circle.fill"
        }
    }
    
    private var statusColor: Color {
        switch status {
        case .authorized:
            return .green
        case .denied:
            return .red
        case .notDetermined:
            return .orange
        case .provisional:
            return .blue
        case .ephemeral:
            return .purple
        @unknown default:
            return .gray
        }
    }
    
    private var statusText: String {
        switch status {
        case .authorized:
            return "Enabled"
        case .denied:
            return "Disabled"
        case .notDetermined:
            return "Not Set"
        case .provisional:
            return "Provisional"
        case .ephemeral:
            return "Temporary"
        @unknown default:
            return "Unknown"
        }
    }
}

struct NotificationTypeToggle: View {
    let title: String
    let description: String
    @Binding var isEnabled: Bool
    let icon: String
    
    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                HStack {
                    Image(systemName: icon)
                        .foregroundColor(.blue)
                        .frame(width: 20)
                    
                    Text(title)
                        .font(.headline)
                }
                
                Text(description)
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.leading)
            }
            
            Spacer()
            
            Toggle("", isOn: $isEnabled)
                .labelsHidden()
        }
        .padding(.vertical, 4)
    }
}

struct StatisticRow: View {
    let title: String
    let value: String
    
    var body: some View {
        HStack {
            Text(title)
            Spacer()
            Text(value)
                .foregroundColor(.secondary)
        }
    }
}

// MARK: - Personalization View

struct PersonalizationView: View {
    @Binding var profile: PersonalizationProfile
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        Form {
            Section("Personal Information") {
                HStack {
                    Text("Name")
                    Spacer()
                    TextField("Optional", text: Binding(
                        get: { profile.userName ?? "" },
                        set: { profile = PersonalizationProfile(
                            userName: $0.isEmpty ? nil : $0,
                            preferredReminderTime: profile.preferredReminderTime,
                            preferredSessionDuration: profile.preferredSessionDuration,
                            interests: profile.interests,
                            completedSessions: profile.completedSessions,
                            currentStreak: profile.currentStreak,
                            timezone: profile.timezone,
                            lastActiveDate: profile.lastActiveDate
                        )}
                    ))
                    .multilineTextAlignment(.trailing)
                }
            }
            
            Section("Preferences") {
                HStack {
                    Text("Reminder Time")
                    Spacer()
                    DatePicker(
                        "",
                        selection: Binding(
                            get: { timeFromString(profile.preferredReminderTime) },
                            set: { profile = PersonalizationProfile(
                                userName: profile.userName,
                                preferredReminderTime: timeToString($0),
                                preferredSessionDuration: profile.preferredSessionDuration,
                                interests: profile.interests,
                                completedSessions: profile.completedSessions,
                                currentStreak: profile.currentStreak,
                                timezone: profile.timezone,
                                lastActiveDate: profile.lastActiveDate
                            )}
                        ),
                        displayedComponents: .hourAndMinute
                    )
                    .labelsHidden()
                }
                
                Picker("Session Duration", selection: Binding(
                    get: { profile.preferredSessionDuration },
                    set: { duration in
                        profile = PersonalizationProfile(
                            userName: profile.userName,
                            preferredReminderTime: profile.preferredReminderTime,
                            preferredSessionDuration: duration,
                            interests: profile.interests,
                            completedSessions: profile.completedSessions,
                            currentStreak: profile.currentStreak,
                            timezone: profile.timezone,
                            lastActiveDate: profile.lastActiveDate
                        )
                    }
                )) {
                    ForEach([5, 10, 15, 20, 30, 45, 60], id: \.self) { duration in
                        Text("\(duration) minutes").tag(duration)
                    }
                }
            }
            
            Section("Interests") {
                InterestSelectionView(selectedInterests: Binding(
                    get: { profile.interests },
                    set: { interests in
                        profile = PersonalizationProfile(
                            userName: profile.userName,
                            preferredReminderTime: profile.preferredReminderTime,
                            preferredSessionDuration: profile.preferredSessionDuration,
                            interests: interests,
                            completedSessions: profile.completedSessions,
                            currentStreak: profile.currentStreak,
                            timezone: profile.timezone,
                            lastActiveDate: profile.lastActiveDate
                        )
                    }
                ))
            }
            
            Section("Statistics") {
                StatisticRow(title: "Completed Sessions", value: "\(profile.completedSessions)")
                StatisticRow(title: "Current Streak", value: "\(profile.currentStreak) days")
                StatisticRow(title: "Last Active", value: formatDate(profile.lastActiveDate))
            }
        }
        .navigationTitle("Personalization")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .navigationBarTrailing) {
                Button("Done") {
                    dismiss()
                }
            }
        }
    }
    
    private func timeFromString(_ timeString: String) -> Date {
        let formatter = DateFormatter()
        formatter.dateFormat = "HH:mm"
        return formatter.date(from: timeString) ?? Date()
    }
    
    private func timeToString(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "HH:mm"
        return formatter.string(from: date)
    }
    
    private func formatDate(_ date: Date) -> String {
        let formatter = RelativeDateTimeFormatter()
        return formatter.localizedString(for: date, relativeTo: Date())
    }
}

struct InterestSelectionView: View {
    @Binding var selectedInterests: [String]
    
    private let availableInterests = [
        "Meditation", "Mindfulness", "Breathing", "Sleep", 
        "Stress Relief", "Focus", "Relaxation", "Wellness",
        "Yoga", "Self-Care", "Motivation", "Gratitude"
    ]
    
    var body: some View {
        ForEach(availableInterests, id: \.self) { interest in
            MultipleSelectionRow(
                title: interest,
                isSelected: selectedInterests.contains(interest)
            ) {
                if selectedInterests.contains(interest) {
                    selectedInterests.removeAll { $0 == interest }
                } else {
                    selectedInterests.append(interest)
                }
            }
        }
    }
}

struct MultipleSelectionRow: View {
    let title: String
    let isSelected: Bool
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            HStack {
                Text(title)
                    .foregroundColor(.primary)
                Spacer()
                if isSelected {
                    Image(systemName: "checkmark")
                        .foregroundColor(.blue)
                }
            }
        }
        .buttonStyle(PlainButtonStyle())
    }
}

#Preview {
    NotificationSettingsView()
}