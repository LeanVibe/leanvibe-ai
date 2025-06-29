import SwiftUI
import UserNotifications

/// Notification History View - Shows delivered and pending notifications
@MainActor
struct NotificationHistoryView: View {
    @ObservedObject var pushService: PushNotificationService
    
    @State private var deliveredNotifications: [DeliveredNotification] = []
    @State private var pendingNotifications: [PendingNotification] = []
    @State private var selectedTab = 0
    @State private var isLoading = true
    
    var body: some View {
        VStack {
            Picker("Notification Type", selection: $selectedTab) {
                Text("Delivered").tag(0)
                Text("Pending").tag(1)
            }
            .pickerStyle(SegmentedPickerStyle())
            .padding()
            
            if isLoading {
                ProgressView("Loading notifications...")
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                TabView(selection: $selectedTab) {
                    // Delivered Notifications Tab
                    DeliveredNotificationsView(notifications: deliveredNotifications)
                        .tag(0)
                    
                    // Pending Notifications Tab
                    PendingNotificationsView(
                        notifications: pendingNotifications,
                        onCancel: { notificationId in
                            cancelNotification(notificationId)
                        }
                    )
                    .tag(1)
                }
                .tabViewStyle(PageTabViewStyle(indexDisplayMode: .never))
            }
        }
        .navigationTitle("Notification History")
        .navigationBarTitleDisplayMode(.inline)
        .onAppear {
            Task {
                await loadNotifications()
            }
        }
        .refreshable {
            Task {
                await loadNotifications()
            }
        }
    }
    
    private func loadNotifications() async {
        isLoading = true
        
        async let delivered = pushService.getDeliveredNotifications()
        async let pending = pushService.getPendingNotifications()
        
        do {
            deliveredNotifications = await delivered
            pendingNotifications = await pending
        }
        
        isLoading = false
    }
    
    private func cancelNotification(_ notificationId: String) {
        pushService.cancelNotification(withId: notificationId)
        pendingNotifications.removeAll { $0.id == notificationId }
    }
}

struct DeliveredNotificationsView: View {
    let notifications: [DeliveredNotification]
    
    var body: some View {
        List {
            if notifications.isEmpty {
                EmptyStateView(
                    icon: "bell.slash",
                    title: "No Delivered Notifications",
                    message: "Delivered notifications will appear here"
                )
            } else {
                ForEach(notifications) { notification in
                    NotificationHistoryCard(
                        title: notification.title,
                        body: notification.body,
                        date: notification.deliveredDate,
                        category: notification.category,
                        status: .delivered
                    )
                }
            }
        }
        .listStyle(PlainListStyle())
    }
}

struct PendingNotificationsView: View {
    let notifications: [PendingNotification]
    let onCancel: (String) -> Void
    
    var body: some View {
        List {
            if notifications.isEmpty {
                EmptyStateView(
                    icon: "clock",
                    title: "No Pending Notifications",
                    message: "Scheduled notifications will appear here"
                )
            } else {
                ForEach(notifications) { notification in
                    NotificationHistoryCard(
                        title: notification.title,
                        body: notification.body,
                        date: notification.scheduledDate,
                        category: notification.category,
                        status: .pending,
                        onCancel: {
                            onCancel(notification.id)
                        }
                    )
                }
            }
        }
        .listStyle(PlainListStyle())
    }
}

struct NotificationHistoryCard: View {
    let title: String
    let message: String
    let date: Date
    let category: String
    let status: NotificationStatus
    let onCancel: (() -> Void)?
    
    init(title: String, body: String, date: Date, category: String, status: NotificationStatus, onCancel: (() -> Void)? = nil) {
        self.title = title
        self.message = body
        self.date = date
        self.category = category
        self.status = status
        self.onCancel = onCancel
    }
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                // Category Icon
                Image(systemName: categoryIcon)
                    .foregroundColor(categoryColor)
                    .frame(width: 24, height: 24)
                
                VStack(alignment: .leading, spacing: 4) {
                    Text(title)
                        .font(.headline)
                        .lineLimit(2)
                    
                    Text(category.capitalized)
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 2)
                        .background(categoryColor.opacity(0.1))
                        .clipShape(Capsule())
                }
                
                Spacer()
                
                // Status Badge
                NotificationStatusBadge(status: status)
            }
            
            Text(message)
                .font(.body)
                .foregroundColor(.secondary)
                .lineLimit(3)
            
            HStack {
                Text(formatDate(date))
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                Spacer()
                
                if status == .pending, let onCancel = onCancel {
                    Button("Cancel") {
                        onCancel()
                    }
                    .font(.caption)
                    .foregroundColor(.red)
                }
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 12))
        .shadow(color: Color.black.opacity(0.05), radius: 2, x: 0, y: 1)
    }
    
    private var categoryIcon: String {
        switch category.lowercased() {
        case "general":
            return "bell.fill"
        case "reminder":
            return "clock.fill"
        case "achievement":
            return "trophy.fill"
        case "social":
            return "person.2.fill"
        case "system":
            return "gear.circle.fill"
        default:
            return "bell.fill"
        }
    }
    
    private var categoryColor: Color {
        switch category.lowercased() {
        case "general":
            return .blue
        case "reminder":
            return .orange
        case "achievement":
            return .yellow
        case "social":
            return .green
        case "system":
            return .purple
        default:
            return .blue
        }
    }
    
    private func formatDate(_ date: Date) -> String {
        let formatter = RelativeDateTimeFormatter()
        formatter.unitsStyle = .abbreviated
        return formatter.localizedString(for: date, relativeTo: Date())
    }
}

/*
struct StatusBadge: View {
    let status: String
    
    var body: some View {
        Text(status)
            .font(.caption.bold())
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(statusColor.opacity(0.15))
            .foregroundColor(statusColor)
            .cornerRadius(8)
    }
    
    private var statusColor: Color {
        switch status.lowercased() {
        case "sent":
            return .blue
        case "delivered":
            return .green
        case "failed":
            return .red
        default:
            return .gray
        }
    }
}
*/

struct EmptyStateView: View {
    let icon: String
    let title: String
    let message: String
    
    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: icon)
                .font(.system(size: 48))
                .foregroundColor(.secondary)
            
            Text(title)
                .font(.headline)
                .foregroundColor(.secondary)
            
            Text(message)
                .font(.body)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color(.systemGroupedBackground))
    }
}

enum NotificationStatus: String, CaseIterable, Identifiable {
    var id: String { self.rawValue }
    case delivered
    case pending
    case opened
    case cancelled
    case failed
    
    var displayName: String {
        switch self {
        case .pending: return "Pending"
        case .delivered: return "Delivered"
        case .opened: return "Opened"
        case .cancelled: return "Cancelled"
        case .failed: return "Failed"
        }
    }
}

struct NotificationStatusBadge: View {
    let status: NotificationStatus
    
    var body: some View {
        HStack(spacing: 4) {
            Image(systemName: statusIcon)
                .font(.caption)
            Text(status.displayName)
                .font(.caption)
                .fontWeight(.medium)
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(statusColor.opacity(0.2))
        .foregroundColor(statusColor)
        .cornerRadius(8)
    }
    
    private var statusIcon: String {
        switch status {
        case .pending:
            return "clock"
        case .delivered:
            return "checkmark.circle"
        case .opened:
            return "envelope.open"
        case .cancelled:
            return "xmark.circle"
        case .failed:
            return "exclamationmark.triangle"
        }
    }
    
    private var statusColor: Color {
        switch status {
        case .pending:
            return .orange
        case .delivered:
            return .blue
        case .opened:
            return .green
        case .cancelled:
            return .gray
        case .failed:
            return .red
        }
    }
}

#Preview {
    NavigationView {
        NotificationHistoryView(pushService: PushNotificationService())
    }
}