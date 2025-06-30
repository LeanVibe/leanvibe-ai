import Foundation
import UserNotifications

@MainActor
class PushNotificationService: NSObject, ObservableObject {
    static let shared = PushNotificationService()
    
    @Published var isAuthorized = false
    @Published var isRegisteredForRemoteNotifications = false
    @Published var deviceToken: String?
    @Published var pendingNotifications: [PendingNotification] = []
    
    var notificationPermissionStatus: UNAuthorizationStatus = .notDetermined
    
    override init() {
        super.init()
        checkAuthorizationStatus()
        UNUserNotificationCenter.current().delegate = self
    }
    
    private func checkAuthorizationStatus() {
        UNUserNotificationCenter.current().getNotificationSettings { [weak self] settings in
            let authStatus = settings.authorizationStatus
            DispatchQueue.main.async {
                self?.isAuthorized = authStatus == .authorized
                self?.notificationPermissionStatus = authStatus
            }
        }
    }
    
    // MARK: - Device Token Management
    func didRegisterForRemoteNotifications(withDeviceToken deviceToken: Data) {
        let tokenString = deviceToken.map { String(format: "%02.2hhx", $0) }.joined()
        self.deviceToken = tokenString
        self.isRegisteredForRemoteNotifications = true
    }
    
    func didFailToRegisterForRemoteNotifications(withError error: Error) {
        self.deviceToken = nil
        self.isRegisteredForRemoteNotifications = false
    }
    
    // MARK: - Local Notification Management
    func scheduleLocalNotification(_ notification: LocalNotificationRequest) async -> Bool {
        do {
            let request = UNNotificationRequest(
                identifier: notification.id,
                content: notification.content,
                trigger: notification.unTrigger
            )
            
            try await UNUserNotificationCenter.current().add(request)
            
            let pendingNotification = PendingNotification(
                id: notification.id,
                title: notification.title,
                body: notification.body,
                category: notification.category,
                scheduledDate: Date()
            )
            pendingNotifications.append(pendingNotification)
            
            return true
        } catch {
            print("Failed to schedule notification: \(error)")
            return false
        }
    }
    
    func cancelNotification(withId id: String) {
        UNUserNotificationCenter.current().removePendingNotificationRequests(withIdentifiers: [id])
        pendingNotifications.removeAll { $0.id == id }
    }
    
    func cancelAllNotifications() {
        UNUserNotificationCenter.current().removeAllPendingNotificationRequests()
        pendingNotifications.removeAll()
    }
    
    // MARK: - Badge Management
    func updateBadgeCount(_ count: Int) {
        UNUserNotificationCenter.current().setBadgeCount(count)
    }
    
    func clearBadge() {
        UNUserNotificationCenter.current().setBadgeCount(0)
    }
    
    // MARK: - Notification History
    func getDeliveredNotifications() async -> [DeliveredNotification] {
        let deliveredRequests = await UNUserNotificationCenter.current().deliveredNotifications()
        return deliveredRequests.map { notification in
            DeliveredNotification(
                id: notification.request.identifier,
                title: notification.request.content.title,
                body: notification.request.content.body,
                category: notification.request.content.categoryIdentifier,
                deliveredDate: notification.date
            )
        }
    }
    
    func getPendingNotifications() async -> [PendingNotification] {
        let pendingRequests = await UNUserNotificationCenter.current().pendingNotificationRequests()
        return pendingRequests.map { request in
            PendingNotification(
                id: request.identifier,
                title: request.content.title,
                body: request.content.body,
                category: request.content.categoryIdentifier,
                scheduledDate: Date() // This would ideally be the trigger date
            )
        }
    }
    
    // MARK: - Quick Notification Methods
    func sendWelcomeNotification() async {
        let notification = LocalNotificationRequest(
            id: "welcome_notification",
            title: "Welcome to LeanVibe!",
            body: "Get started with your productivity journey",
            category: "WELCOME",
            trigger: .timeInterval(1, repeats: false)
        )
        
        await scheduleLocalNotification(notification)
    }
    
    func sendDailyReminderNotification(at date: Date) async {
        let dateComponents = Calendar.current.dateComponents([.hour, .minute], from: date)
        
        let notification = LocalNotificationRequest(
            id: "daily_reminder",
            title: "Daily Practice Reminder",
            body: "Time for your daily productivity session",
            category: "REMINDER",
            trigger: .calendar(dateComponents, repeats: true)
        )
        
        await scheduleLocalNotification(notification)
    }
    
    func sendAchievementNotification(achievement: String) async {
        let notification = LocalNotificationRequest(
            id: "achievement_\(UUID().uuidString)",
            title: "Achievement Unlocked!",
            body: achievement,
            category: "ACHIEVEMENT",
            trigger: .timeInterval(1, repeats: false)
        )
        
        await scheduleLocalNotification(notification)
    }
}

// MARK: - Models
struct DeliveredNotification: Identifiable {
    let id: String
    let title: String
    let body: String
    let category: String
    let deliveredDate: Date
}

struct PendingNotification: Identifiable {
    let id: String
    let title: String
    let body: String
    let category: String
    let scheduledDate: Date
}

struct LocalNotificationRequest {
    let id: String
    let title: String
    let body: String
    let category: String
    let trigger: NotificationTrigger
    
    var content: UNNotificationContent {
        let content = UNMutableNotificationContent()
        content.title = title
        content.body = body
        content.categoryIdentifier = category
        return content
    }
    
    var unTrigger: UNNotificationTrigger? {
        switch trigger {
        case .immediate:
            return UNTimeIntervalNotificationTrigger(timeInterval: 0.1, repeats: false)
        case .timeInterval(let interval, let repeats):
            return UNTimeIntervalNotificationTrigger(timeInterval: interval, repeats: repeats)
        case .calendar(let dateComponents, let repeats):
            return UNCalendarNotificationTrigger(dateMatching: dateComponents, repeats: repeats)
        }
    }
}

enum NotificationTrigger {
    case immediate
    case timeInterval(TimeInterval, repeats: Bool)
    case calendar(DateComponents, repeats: Bool)
}

extension PushNotificationService: @preconcurrency UNUserNotificationCenterDelegate {
    
    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        willPresent notification: UNNotification,
        withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void
    ) {
        // Handle the notification when it's being presented
        completionHandler([.alert, .badge, .sound])
    }

    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        didReceive response: UNNotificationResponse,
        withCompletionHandler completionHandler: @escaping () -> Void
    ) {
        // Handle the notification when it's being interacted with
        completionHandler()
    }
} 