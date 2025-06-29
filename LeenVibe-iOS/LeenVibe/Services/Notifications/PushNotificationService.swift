import Foundation
import UserNotifications
#if canImport(UIKit)
import UIKit
#endif
import Combine
import os.log

/// Standalone Push Notification Service for LeenVibe iOS App
/// Handles APNs registration, local notifications, and delivery management
@MainActor
class PushNotificationService: NSObject, ObservableObject {
    
    // MARK: - Singleton Instance
    static let shared = PushNotificationService()
    
    // MARK: - Published Properties
    
    @Published var isRegisteredForRemoteNotifications = false
    @Published var notificationPermissionStatus: UNAuthorizationStatus = .notDetermined
    @Published var deviceToken: String?
    @Published var pendingNotifications: [PendingNotification] = []
    @Published var deliveredNotifications: [DeliveredNotification] = []
    
    // MARK: - Configuration
    
    private let notificationCenter = UNUserNotificationCenter.current()
    private let logger = Logger(subsystem: "com.leenvibe.notifications", category: "PushService")
    
    // MARK: - Notification Categories
    
    private enum NotificationCategory {
        static let general = "GENERAL"
        static let reminder = "REMINDER"
        static let achievement = "ACHIEVEMENT"
        static let social = "SOCIAL"
        static let system = "SYSTEM"
    }
    
    // MARK: - Notification Actions
    
    private enum NotificationAction {
        static let view = "VIEW_ACTION"
        static let dismiss = "DISMISS_ACTION"
        static let snooze = "SNOOZE_ACTION"
        static let reply = "REPLY_ACTION"
    }
    
    // MARK: - Storage
    
    private let userDefaults = UserDefaults.standard
    private let deviceTokenKey = "DeviceTokenKey"
    private let notificationPreferencesKey = "NotificationPreferencesKey"
    
    override init() {
        super.init()
        setupNotificationCenter()
        loadStoredData()
        logger.info("PushNotificationService initialized")
    }
    
    // MARK: - Setup
    
    private func setupNotificationCenter() {
        notificationCenter.delegate = self
        registerNotificationCategories()
    }
    
    private func registerNotificationCategories() {
        // General category with basic actions
        let viewAction = UNNotificationAction(
            identifier: NotificationAction.view,
            title: "View",
            options: [.foreground]
        )
        
        let dismissAction = UNNotificationAction(
            identifier: NotificationAction.dismiss,
            title: "Dismiss",
            options: [.destructive]
        )
        
        let generalCategory = UNNotificationCategory(
            identifier: NotificationCategory.general,
            actions: [viewAction, dismissAction],
            intentIdentifiers: [],
            options: []
        )
        
        // Reminder category with snooze option
        let snoozeAction = UNNotificationAction(
            identifier: NotificationAction.snooze,
            title: "Snooze 10min",
            options: []
        )
        
        let reminderCategory = UNNotificationCategory(
            identifier: NotificationCategory.reminder,
            actions: [viewAction, snoozeAction, dismissAction],
            intentIdentifiers: [],
            options: []
        )
        
        // Social category with reply option
        let replyAction = UNTextInputNotificationAction(
            identifier: NotificationAction.reply,
            title: "Reply",
            options: [],
            textInputButtonTitle: "Send",
            textInputPlaceholder: "Type your message..."
        )
        
        let socialCategory = UNNotificationCategory(
            identifier: NotificationCategory.social,
            actions: [replyAction, viewAction, dismissAction],
            intentIdentifiers: [],
            options: []
        )
        
        // Achievement category
        let achievementCategory = UNNotificationCategory(
            identifier: NotificationCategory.achievement,
            actions: [viewAction],
            intentIdentifiers: [],
            options: []
        )
        
        // System category
        let systemCategory = UNNotificationCategory(
            identifier: NotificationCategory.system,
            actions: [viewAction, dismissAction],
            intentIdentifiers: [],
            options: []
        )
        
        notificationCenter.setNotificationCategories([
            generalCategory,
            reminderCategory,
            socialCategory,
            achievementCategory,
            systemCategory
        ])
        
        logger.info("Registered notification categories")
    }
    
    // MARK: - Permission Management
    
    func requestNotificationPermissions() async -> Bool {
        do {
            let granted = try await notificationCenter.requestAuthorization(
                options: [.alert, .sound, .badge, .provisional, .criticalAlert]
            )
            
            await MainActor.run {
                if granted {
                    registerForRemoteNotifications()
                }
            }
            
            await updatePermissionStatus()
            logger.info("Notification permissions requested: \(granted)")
            return granted
            
        } catch {
            logger.error("Failed to request notification permissions: \(error)")
            return false
        }
    }
    
    func updatePermissionStatus() async {
        let settings = await notificationCenter.notificationSettings()
        await MainActor.run {
            notificationPermissionStatus = settings.authorizationStatus
        }
    }
    
    private func registerForRemoteNotifications() {
        DispatchQueue.main.async {
            UIApplication.shared.registerForRemoteNotifications()
        }
    }
    
    // MARK: - Device Token Management
    
    func didRegisterForRemoteNotifications(withDeviceToken deviceToken: Data) {
        let tokenString = deviceToken.map { String(format: "%02.2hhx", $0) }.joined()
        
        self.deviceToken = tokenString
        self.isRegisteredForRemoteNotifications = true
        
        // Store device token
        userDefaults.set(tokenString, forKey: deviceTokenKey)
        
        // Send token to backend
        Task {
            await sendDeviceTokenToBackend(tokenString)
        }
        
        logger.info("Registered for remote notifications with token: \(tokenString.prefix(10))...")
    }
    
    func didFailToRegisterForRemoteNotifications(withError error: Error) {
        isRegisteredForRemoteNotifications = false
        logger.error("Failed to register for remote notifications: \(error)")
    }
    
    private func sendDeviceTokenToBackend(_ token: String) async {
        // Implementation would send token to backend API
        logger.debug("Sending device token to backend: \(token.prefix(10))...")
        
        // Simulated API call
        do {
            // let response = await apiClient.registerDeviceToken(token)
            logger.info("Device token registered with backend successfully")
        } catch {
            logger.error("Failed to register device token with backend: \(error)")
        }
    }
    
    // MARK: - Local Notifications
    
    func scheduleLocalNotification(_ notification: LocalNotificationRequest) async -> Bool {
        do {
            let content = createNotificationContent(from: notification)
            let trigger = createNotificationTrigger(from: notification.trigger)
            
            let request = UNNotificationRequest(
                identifier: notification.id,
                content: content,
                trigger: trigger
            )
            
            try await notificationCenter.add(request)
            
            // Track pending notification
            let pendingNotification = PendingNotification(
                id: notification.id,
                title: notification.title,
                body: notification.body,
                scheduledDate: notification.trigger.date ?? Date(),
                category: notification.category
            )
            
            pendingNotifications.append(pendingNotification)
            
            logger.info("Scheduled local notification: \(notification.id)")
            return true
            
        } catch {
            logger.error("Failed to schedule local notification: \(error)")
            return false
        }
    }
    
    func cancelNotification(withId id: String) {
        notificationCenter.removePendingNotificationRequests(withIdentifiers: [id])
        pendingNotifications.removeAll { $0.id == id }
        logger.info("Cancelled notification: \(id)")
    }
    
    func cancelAllNotifications() {
        notificationCenter.removeAllPendingNotificationRequests()
        pendingNotifications.removeAll()
        logger.info("Cancelled all pending notifications")
    }
    
    // MARK: - Notification Content Creation
    
    private func createNotificationContent(from request: LocalNotificationRequest) -> UNMutableNotificationContent {
        let content = UNMutableNotificationContent()
        
        content.title = request.title
        content.body = request.body
        content.categoryIdentifier = request.category
        switch request.sound {
        case .default:
            content.sound = .default
        case .none:
            content.sound = nil
        case .custom(let soundName):
            content.sound = UNNotificationSound(named: UNNotificationSoundName(rawValue: soundName))
        }
        
        if let subtitle = request.subtitle {
            content.subtitle = subtitle
        }
        
        if let badge = request.badge {
            content.badge = NSNumber(value: badge)
        }
        
        if let userInfo = request.userInfo {
            content.userInfo = userInfo
        }
        
        // Add attachments if any
        if let attachments = request.attachments {
            content.attachments = attachments
        }
        
        return content
    }
    
    private func createNotificationTrigger(from trigger: NotificationTrigger) -> UNNotificationTrigger? {
        switch trigger {
        case .immediate:
            return UNTimeIntervalNotificationTrigger(timeInterval: 1, repeats: false)
            
        case .date(let date):
            let components = Calendar.current.dateComponents([.year, .month, .day, .hour, .minute], from: date)
            return UNCalendarNotificationTrigger(dateMatching: components, repeats: false)
            
        case .timeInterval(let interval, let repeats):
            return UNTimeIntervalNotificationTrigger(timeInterval: interval, repeats: repeats)
            
        case .location(let region, let repeats):
            return UNLocationNotificationTrigger(region: region, repeats: repeats)
        }
    }
    
    // MARK: - Quick Notification Methods
    
    func sendWelcomeNotification() async {
        let notification = LocalNotificationRequest(
            id: "welcome_\(UUID().uuidString)",
            title: "Welcome to LeenVibe! 🎉",
            body: "Start your journey with personalized meditation and wellness content.",
            category: NotificationCategory.general,
            trigger: .immediate
        )
        
        await scheduleLocalNotification(notification)
    }
    
    func sendDailyReminderNotification(at date: Date) async {
        let notification = LocalNotificationRequest(
            id: "daily_reminder_\(UUID().uuidString)",
            title: "Time for Your Daily Practice 🧘‍♀️",
            body: "Take a moment to center yourself with a quick meditation session.",
            category: NotificationCategory.reminder,
            trigger: .date(date)
        )
        
        await scheduleLocalNotification(notification)
    }
    
    func sendAchievementNotification(achievement: String) async {
        let notification = LocalNotificationRequest(
            id: "achievement_\(UUID().uuidString)",
            title: "Achievement Unlocked! 🏆",
            body: "Congratulations! You've earned: \(achievement)",
            category: NotificationCategory.achievement,
            trigger: .immediate
        )
        
        await scheduleLocalNotification(notification)
    }
    
    // MARK: - Notification History
    
    func getDeliveredNotifications() async -> [DeliveredNotification] {
        let delivered = await notificationCenter.deliveredNotifications()
        
        return delivered.map { notification in
            DeliveredNotification(
                id: notification.request.identifier,
                title: notification.request.content.title,
                body: notification.request.content.body,
                deliveredDate: notification.date,
                category: notification.request.content.categoryIdentifier
            )
        }
    }
    
    func getPendingNotifications() async -> [PendingNotification] {
        let pending = await notificationCenter.pendingNotificationRequests()
        
        return pending.compactMap { request in
            guard let trigger = request.trigger as? UNCalendarNotificationTrigger,
                  let nextTriggerDate = trigger.nextTriggerDate() else {
                return nil
            }
            
            return PendingNotification(
                id: request.identifier,
                title: request.content.title,
                body: request.content.body,
                scheduledDate: nextTriggerDate,
                category: request.content.categoryIdentifier
            )
        }
    }
    
    // MARK: - Badge Management
    
    func updateBadgeCount(_ count: Int) {
        DispatchQueue.main.async {
            UIApplication.shared.applicationIconBadgeNumber = count
        }
        logger.debug("Updated badge count to: \(count)")
    }
    
    func clearBadge() {
        updateBadgeCount(0)
    }
    
    // MARK: - Data Persistence
    
    private func loadStoredData() {
        deviceToken = userDefaults.string(forKey: deviceTokenKey)
        isRegisteredForRemoteNotifications = deviceToken != nil
    }
    
    // MARK: - Notification Preferences
    
    func getNotificationPreferences() -> NotificationPreferences {
        if let data = userDefaults.data(forKey: notificationPreferencesKey),
           let preferences = try? JSONDecoder().decode(NotificationPreferences.self, from: data) {
            return preferences
        }
        return NotificationPreferences() // Default preferences
    }
    
    func saveNotificationPreferences(_ preferences: NotificationPreferences) {
        if let data = try? JSONEncoder().encode(preferences) {
            userDefaults.set(data, forKey: notificationPreferencesKey)
            logger.info("Saved notification preferences")
        }
    }
    
    // MARK: - Analytics
    
    private func trackNotificationEvent(_ event: NotificationEvent) {
        logger.info("Notification event: \(String(describing: event.type)) for ID: \(event.notificationId)")
        // Implementation would send analytics to backend
    }
    
    private func handleReplyAction(notification: UNNotification, text: String) {
        logger.info("Handling reply action for notification: \\(notification.request.identifier), text: \\(text)")
        // Implementation would send reply to appropriate service
    }
}

extension PushNotificationService: UNUserNotificationCenterDelegate {
    
    nonisolated func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        willPresent notification: UNNotification,
        withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void
    ) {
        // Handle the notification when it's being presented
        completionHandler([.alert, .badge, .sound])
    }
    
    nonisolated func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        didReceive response: UNNotificationResponse,
        withCompletionHandler completionHandler: @escaping () -> Void
    ) {
        // Handle the notification when it's being interacted with
        completionHandler()
    }
}

// MARK: - Supporting Types

struct LocalNotificationRequest {
    let id: String
    let title: String
    let body: String
    let subtitle: String?
    let category: String
    let sound: NotificationSound
    let badge: Int?
    let userInfo: [AnyHashable: Any]?
    let attachments: [UNNotificationAttachment]?
    let trigger: NotificationTrigger
    
    init(
        id: String = UUID().uuidString,
        title: String,
        body: String,
        subtitle: String? = nil,
        category: String,
        sound: NotificationSound = .default,
        badge: Int? = nil,
        userInfo: [AnyHashable: Any]? = nil,
        attachments: [UNNotificationAttachment]? = nil,
        trigger: NotificationTrigger
    ) {
        self.id = id
        self.title = title
        self.body = body
        self.subtitle = subtitle
        self.category = category
        self.sound = sound
        self.badge = badge
        self.userInfo = userInfo
        self.attachments = attachments
        self.trigger = trigger
    }
}

enum NotificationSound {
    case `default`
    case none
    case custom(String)
}

enum NotificationTrigger {
    case immediate
    case date(Date)
    case timeInterval(TimeInterval, repeats: Bool)
    case location(CLRegion, repeats: Bool)
    
    var date: Date? {
        switch self {
        case .date(let date):
            return date
        case .timeInterval(let interval, _):
            return Date().addingTimeInterval(interval)
        default:
            return nil
        }
    }
}

struct PendingNotification: Identifiable {
    let id: String
    let title: String
    let body: String
    let scheduledDate: Date
    let category: String
}

struct DeliveredNotification: Identifiable {
    let id: String
    let title: String
    let body: String
    let deliveredDate: Date
    let category: String
}

struct NotificationPreferences: Codable {
    var allowGeneralNotifications = true
    var allowReminders = true
    var allowAchievements = true
    var allowSocial = true
    var allowSystem = true
    var quietHoursEnabled = false
    var quietHoursStart = "22:00"
    var quietHoursEnd = "08:00"
    var preferredTime = "09:00"
}

/*
struct NotificationEvent {
    let type: NotificationEventType
    let notificationId: String
    let timestamp: Date
    let actionId: String?
    
    init(type: NotificationEventType, notificationId: String, timestamp: Date, actionId: String? = nil) {
        self.type = type
        self.notificationId = notificationId
        self.timestamp = timestamp
        self.actionId = actionId
    }
}

enum NotificationEventType {
    case scheduled
    case presented
    case interacted
    case dismissed
}
*/

import CoreLocation