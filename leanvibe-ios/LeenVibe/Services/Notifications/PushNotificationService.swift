import Foundation
import UserNotifications

@MainActor
class PushNotificationService: NSObject, ObservableObject {
    @Published var isAuthorized = false
    
    override init() {
        super.init()
        checkAuthorizationStatus()
    }
    
    private func checkAuthorizationStatus() {
        UNUserNotificationCenter.current().getNotificationSettings { settings in
            DispatchQueue.main.async {
                self.isAuthorized = settings.authorizationStatus == .authorized
            }
        }
    }
}

// MARK: - Models
struct DeliveredNotification {
    let id: String
    let title: String
    let body: String
    let deliveredDate: Date
}

struct PendingNotification {
    let id: String
    let title: String
    let body: String
    let scheduledDate: Date
}

struct LocalNotificationRequest {
    let id: String
    let content: UNNotificationContent
    let trigger: UNNotificationTrigger?
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