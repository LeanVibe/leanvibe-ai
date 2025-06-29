import Foundation
import Combine
import os.log

/// Advanced notification analytics and delivery tracking service
/// Provides comprehensive insights into notification performance and user engagement
@MainActor
class NotificationAnalyticsService: ObservableObject {
    
    // MARK: - Published Properties
    
    @Published var analyticsData: NotificationAnalytics?
    @Published var deliveryStats: DeliveryStatistics?
    @Published var engagementMetrics: EngagementMetrics?
    @Published var performanceInsights: [PerformanceInsight] = []
    
    // MARK: - Event Tracking
    
    private var events: [NotificationEvent] = []
    private var deliveryRecords: [DeliveryRecord] = []
    private var engagementRecords: [EngagementRecord] = []
    
    // MARK: - Storage
    
    private let userDefaults = UserDefaults.standard
    private let eventsKey = "NotificationEventsKey"
    private let deliveryKey = "NotificationDeliveryKey"
    private let engagementKey = "NotificationEngagementKey"
    
    // MARK: - Configuration
    
    private let maxEventsHistory = 1000
    private let analyticsUpdateInterval: TimeInterval = 300 // 5 minutes
    
    // MARK: - Logging
    
    private let logger = Logger(subsystem: "com.leenvibe.notifications", category: "Analytics")
    
    // MARK: - Timer
    
    private var analyticsTimer: Timer?
    
    init() {
        loadStoredData()
        startAnalyticsUpdates()
        logger.info("NotificationAnalyticsService initialized")
    }
    
    // Note: stopAnalyticsUpdates should be called explicitly when no longer needed
    // Cannot call async methods in deinit
    
    // MARK: - Event Tracking
    
    func trackNotificationSent(
        id: String,
        type: NotificationType,
        category: String,
        isPersonalized: Bool = false
    ) {
        let event = NotificationEvent(
            id: UUID().uuidString,
            notificationId: id,
            type: .sent,
            category: category,
            notificationType: type,
            timestamp: Date(),
            isPersonalized: isPersonalized
        )
        
        recordEvent(event)
        
        let deliveryRecord = DeliveryRecord(
            notificationId: id,
            sentAt: Date(),
            deliveredAt: nil,
            deliveryStatus: .sent,
            attemptCount: 1
        )
        
        recordDelivery(deliveryRecord)
        
        logger.debug("Tracked notification sent: \(id)")
    }
    
    func trackNotificationDelivered(
        id: String,
        deliveryTime: TimeInterval
    ) {
        let event = NotificationEvent(
            id: UUID().uuidString,
            notificationId: id,
            type: .delivered,
            timestamp: Date(),
            deliveryTime: deliveryTime
        )
        
        recordEvent(event)
        
        // Update delivery record
        if let index = deliveryRecords.firstIndex(where: { $0.notificationId == id }) {
            deliveryRecords[index] = DeliveryRecord(
                notificationId: id,
                sentAt: deliveryRecords[index].sentAt,
                deliveredAt: Date(),
                deliveryStatus: .delivered,
                attemptCount: deliveryRecords[index].attemptCount,
                deliveryTime: deliveryTime
            )
        }
        
        logger.debug("Tracked notification delivered: \(id)")
    }
    
    func trackNotificationOpened(
        id: String,
        timeToOpen: TimeInterval
    ) {
        let event = NotificationEvent(
            id: UUID().uuidString,
            notificationId: id,
            type: .opened,
            timestamp: Date(),
            timeToOpen: timeToOpen
        )
        
        recordEvent(event)
        
        let engagementRecord = EngagementRecord(
            notificationId: id,
            openedAt: Date(),
            timeToOpen: timeToOpen,
            actionTaken: .opened
        )
        
        recordEngagement(engagementRecord)
        
        logger.debug("Tracked notification opened: \(id)")
    }
    
    func trackNotificationDismissed(
        id: String,
        timeToDismiss: TimeInterval
    ) {
        let event = NotificationEvent(
            id: UUID().uuidString,
            notificationId: id,
            type: .dismissed,
            timestamp: Date(),
            timeToDismiss: timeToDismiss
        )
        
        recordEvent(event)
        
        let engagementRecord = EngagementRecord(
            notificationId: id,
            dismissedAt: Date(),
            timeToDismiss: timeToDismiss,
            actionTaken: .dismissed
        )
        
        recordEngagement(engagementRecord)
        
        logger.debug("Tracked notification dismissed: \(id)")
    }
    
    func trackNotificationActionTaken(
        id: String,
        actionId: String,
        actionType: NotificationActionType
    ) {
        let event = NotificationEvent(
            id: UUID().uuidString,
            notificationId: id,
            type: .actionTaken,
            timestamp: Date(),
            actionId: actionId,
            actionType: actionType
        )
        
        recordEvent(event)
        
        let engagementRecord = EngagementRecord(
            notificationId: id,
            actionTakenAt: Date(),
            actionId: actionId,
            actionType: actionType,
            actionTaken: .actionTaken
        )
        
        recordEngagement(engagementRecord)
        
        logger.debug("Tracked notification action: \(actionId) for \(id)")
    }
    
    func trackNotificationFailed(
        id: String,
        error: Error
    ) {
        let event = NotificationEvent(
            id: UUID().uuidString,
            notificationId: id,
            type: .failed,
            timestamp: Date(),
            errorMessage: error.localizedDescription
        )
        
        recordEvent(event)
        
        // Update delivery record
        if let index = deliveryRecords.firstIndex(where: { $0.notificationId == id }) {
            deliveryRecords[index] = DeliveryRecord(
                notificationId: id,
                sentAt: deliveryRecords[index].sentAt,
                deliveredAt: nil,
                deliveryStatus: .failed,
                attemptCount: deliveryRecords[index].attemptCount + 1,
                errorMessage: error.localizedDescription
            )
        }
        
        logger.error("Tracked notification failed: \(id) - \(error.localizedDescription)")
    }
    
    // MARK: - Analytics Calculation
    
    func calculateAnalytics() async {
        logger.info("Calculating notification analytics")
        
        let now = Date()
        let calendar = Calendar.current
        
        // Calculate delivery statistics
        await calculateDeliveryStatistics()
        
        // Calculate engagement metrics
        await calculateEngagementMetrics()
        
        // Generate performance insights
        await generatePerformanceInsights()
        
        // Update overall analytics
        analyticsData = NotificationAnalytics(
            totalNotificationsSent: deliveryRecords.count,
            totalDelivered: deliveryRecords.filter { $0.deliveryStatus == .delivered }.count,
            totalOpened: engagementRecords.filter { $0.actionTaken == .opened }.count,
            totalFailed: deliveryRecords.filter { $0.deliveryStatus == .failed }.count,
            averageDeliveryTime: calculateAverageDeliveryTime(),
            averageOpenRate: calculateOpenRate(),
            lastUpdated: now,
            timeRange: .last30Days
        )
        
        saveAnalyticsData()
        logger.info("Analytics calculation completed")
    }
    
    private func calculateDeliveryStatistics() async {
        let totalSent = deliveryRecords.count
        let totalDelivered = deliveryRecords.filter { $0.deliveryStatus == .delivered }.count
        let totalFailed = deliveryRecords.filter { $0.deliveryStatus == .failed }.count
        let totalPending = totalSent - totalDelivered - totalFailed
        
        let deliveryRate = totalSent > 0 ? Double(totalDelivered) / Double(totalSent) : 0
        let failureRate = totalSent > 0 ? Double(totalFailed) / Double(totalSent) : 0
        
        let avgDeliveryTime = calculateAverageDeliveryTime()
        let deliveryTimeP95 = calculateDeliveryTimePercentile(0.95)
        
        deliveryStats = DeliveryStatistics(
            totalSent: totalSent,
            totalDelivered: totalDelivered,
            totalFailed: totalFailed,
            totalPending: totalPending,
            deliveryRate: deliveryRate,
            failureRate: failureRate,
            averageDeliveryTime: avgDeliveryTime,
            p95DeliveryTime: deliveryTimeP95,
            lastUpdated: Date()
        )
    }
    
    private func calculateEngagementMetrics() async {
        let totalDelivered = deliveryRecords.filter { $0.deliveryStatus == .delivered }.count
        let totalOpened = engagementRecords.filter { $0.actionTaken == .opened }.count
        let totalDismissed = engagementRecords.filter { $0.actionTaken == .dismissed }.count
        let totalActionsTaken = engagementRecords.filter { $0.actionTaken == .actionTaken }.count
        
        let openRate = totalDelivered > 0 ? Double(totalOpened) / Double(totalDelivered) : 0
        let dismissalRate = totalDelivered > 0 ? Double(totalDismissed) / Double(totalDelivered) : 0
        let actionRate = totalDelivered > 0 ? Double(totalActionsTaken) / Double(totalDelivered) : 0
        
        let avgTimeToOpen = calculateAverageTimeToOpen()
        let avgTimeToDismiss = calculateAverageTimeToDismiss()
        
        // Calculate engagement by category
        let categoryEngagement = calculateEngagementByCategory()
        
        // Calculate engagement by time of day
        let timeOfDayEngagement = calculateEngagementByTimeOfDay()
        
        engagementMetrics = EngagementMetrics(
            openRate: openRate,
            dismissalRate: dismissalRate,
            actionRate: actionRate,
            averageTimeToOpen: avgTimeToOpen,
            averageTimeToDismiss: avgTimeToDismiss,
            engagementByCategory: categoryEngagement,
            engagementByTimeOfDay: timeOfDayEngagement,
            lastUpdated: Date()
        )
    }
    
    private func generatePerformanceInsights() async {
        var insights: [PerformanceInsight] = []
        
        // Delivery performance insight
        if let deliveryStats = deliveryStats {
            if deliveryStats.deliveryRate < 0.8 {
                insights.append(PerformanceInsight(
                    type: .lowDeliveryRate,
                    severity: .high,
                    title: "Low Delivery Rate",
                    description: "Delivery rate is \(Int(deliveryStats.deliveryRate * 100))%. Consider checking notification permissions and timing.",
                    recommendation: "Review notification settings and consider optimizing send times.",
                    impact: .deliveryOptimization
                ))
            }
            
            if deliveryStats.averageDeliveryTime > 30.0 {
                insights.append(PerformanceInsight(
                    type: .slowDelivery,
                    severity: .medium,
                    title: "Slow Delivery",
                    description: "Average delivery time is \(Int(deliveryStats.averageDeliveryTime))s.",
                    recommendation: "Optimize notification payload size and delivery timing.",
                    impact: .deliveryOptimization
                ))
            }
        }
        
        // Engagement performance insight
        if let engagementMetrics = engagementMetrics {
            if engagementMetrics.openRate < 0.1 {
                insights.append(PerformanceInsight(
                    type: .lowEngagement,
                    severity: .high,
                    title: "Low Open Rate",
                    description: "Open rate is \(Int(engagementMetrics.openRate * 100))%.",
                    recommendation: "Improve notification content and personalization.",
                    impact: .engagementOptimization
                ))
            }
            
            if engagementMetrics.dismissalRate > 0.7 {
                insights.append(PerformanceInsight(
                    type: .highDismissal,
                    severity: .medium,
                    title: "High Dismissal Rate",
                    description: "Dismissal rate is \(Int(engagementMetrics.dismissalRate * 100))%.",
                    recommendation: "Review notification frequency and relevance.",
                    impact: .contentOptimization
                ))
            }
        }
        
        // Best performing category insight
        if let engagementMetrics = engagementMetrics {
            if let bestCategory = engagementMetrics.engagementByCategory.max(by: { $0.value.openRate < $1.value.openRate }) {
                insights.append(PerformanceInsight(
                    type: .bestPerformingCategory,
                    severity: .info,
                    title: "Best Performing Category",
                    description: "\(bestCategory.key) notifications have the highest open rate at \(Int(bestCategory.value.openRate * 100))%.",
                    recommendation: "Consider increasing frequency of \(bestCategory.key) notifications.",
                    impact: .contentOptimization
                ))
            }
        }
        
        performanceInsights = insights
    }
    
    // MARK: - Helper Calculations
    
    private func calculateAverageDeliveryTime() -> TimeInterval {
        let deliveredRecords = deliveryRecords.filter { $0.deliveryStatus == .delivered && $0.deliveryTime != nil }
        guard !deliveredRecords.isEmpty else { return 0 }
        
        let totalTime = deliveredRecords.compactMap { $0.deliveryTime }.reduce(0, +)
        return totalTime / Double(deliveredRecords.count)
    }
    
    private func calculateDeliveryTimePercentile(_ percentile: Double) -> TimeInterval {
        let deliveryTimes = deliveryRecords.compactMap { $0.deliveryTime }.sorted()
        guard !deliveryTimes.isEmpty else { return 0 }
        
        let index = Int(Double(deliveryTimes.count) * percentile)
        return deliveryTimes[min(index, deliveryTimes.count - 1)]
    }
    
    private func calculateOpenRate() -> Double {
        let totalDelivered = deliveryRecords.filter { $0.deliveryStatus == .delivered }.count
        let totalOpened = engagementRecords.filter { $0.actionTaken == .opened }.count
        
        return totalDelivered > 0 ? Double(totalOpened) / Double(totalDelivered) : 0
    }
    
    private func calculateAverageTimeToOpen() -> TimeInterval {
        let openRecords = engagementRecords.filter { $0.actionTaken == .opened && $0.timeToOpen != nil }
        guard !openRecords.isEmpty else { return 0 }
        
        let totalTime = openRecords.compactMap { $0.timeToOpen }.reduce(0, +)
        return totalTime / Double(openRecords.count)
    }
    
    private func calculateAverageTimeToDismiss() -> TimeInterval {
        let dismissRecords = engagementRecords.filter { $0.actionTaken == .dismissed && $0.timeToDismiss != nil }
        guard !dismissRecords.isEmpty else { return 0 }
        
        let totalTime = dismissRecords.compactMap { $0.timeToDismiss }.reduce(0, +)
        return totalTime / Double(dismissRecords.count)
    }
    
    private func calculateEngagementByCategory() -> [String: CategoryEngagement] {
        var categoryStats: [String: CategoryEngagement] = [:]
        
        // Group events by category
        let eventsByCategory = Dictionary(grouping: events) { event in
            event.category ?? "unknown"
        }
        
        for (category, categoryEvents) in eventsByCategory {
            let sentEvents = categoryEvents.filter { $0.type == .sent }
            let deliveredEvents = categoryEvents.filter { $0.type == .delivered }
            let openedEvents = categoryEvents.filter { $0.type == .opened }
            
            let deliveryRate = sentEvents.count > 0 ? Double(deliveredEvents.count) / Double(sentEvents.count) : 0
            let openRate = deliveredEvents.count > 0 ? Double(openedEvents.count) / Double(deliveredEvents.count) : 0
            
            categoryStats[category] = CategoryEngagement(
                totalSent: sentEvents.count,
                totalDelivered: deliveredEvents.count,
                totalOpened: openedEvents.count,
                deliveryRate: deliveryRate,
                openRate: openRate
            )
        }
        
        return categoryStats
    }
    
    private func calculateEngagementByTimeOfDay() -> [Int: TimeOfDayEngagement] {
        var hourlyStats: [Int: TimeOfDayEngagement] = [:]
        
        let calendar = Calendar.current
        
        // Group events by hour
        for hour in 0..<24 {
            let hourEvents = events.filter { event in
                calendar.component(.hour, from: event.timestamp) == hour
            }
            
            let sentEvents = hourEvents.filter { $0.type == .sent }
            let deliveredEvents = hourEvents.filter { $0.type == .delivered }
            let openedEvents = hourEvents.filter { $0.type == .opened }
            
            let deliveryRate = sentEvents.count > 0 ? Double(deliveredEvents.count) / Double(sentEvents.count) : 0
            let openRate = deliveredEvents.count > 0 ? Double(openedEvents.count) / Double(deliveredEvents.count) : 0
            
            hourlyStats[hour] = TimeOfDayEngagement(
                hour: hour,
                totalSent: sentEvents.count,
                totalDelivered: deliveredEvents.count,
                totalOpened: openedEvents.count,
                deliveryRate: deliveryRate,
                openRate: openRate
            )
        }
        
        return hourlyStats
    }
    
    // MARK: - Data Management
    
    private func recordEvent(_ event: NotificationEvent) {
        events.append(event)
        
        // Maintain history limit
        if events.count > maxEventsHistory {
            events.removeFirst(events.count - maxEventsHistory)
        }
        
        saveEvents()
    }
    
    private func recordDelivery(_ record: DeliveryRecord) {
        if let existingIndex = deliveryRecords.firstIndex(where: { $0.notificationId == record.notificationId }) {
            deliveryRecords[existingIndex] = record
        } else {
            deliveryRecords.append(record)
        }
        
        saveDeliveryRecords()
    }
    
    private func recordEngagement(_ record: EngagementRecord) {
        engagementRecords.append(record)
        saveEngagementRecords()
    }
    
    // MARK: - Timer Management
    
    private func startAnalyticsUpdates() {
        analyticsTimer = Timer.scheduledTimer(withTimeInterval: analyticsUpdateInterval, repeats: true) { _ in
            Task { @MainActor in
                await self.calculateAnalytics()
            }
        }
    }
    
    private func stopAnalyticsUpdates() {
        analyticsTimer?.invalidate()
        analyticsTimer = nil
    }
    
    // MARK: - Export Functionality
    
    func exportAnalyticsData() async -> NotificationAnalyticsExport {
        await calculateAnalytics()
        
        return NotificationAnalyticsExport(
            analytics: analyticsData,
            deliveryStats: deliveryStats,
            engagementMetrics: engagementMetrics,
            performanceInsights: performanceInsights,
            events: Array(events.suffix(100)), // Last 100 events
            deliveryRecords: deliveryRecords,
            engagementRecords: engagementRecords,
            exportDate: Date()
        )
    }
    
    // MARK: - Data Persistence
    
    private func loadStoredData() {
        loadEvents()
        loadDeliveryRecords()
        loadEngagementRecords()
    }
    
    private func saveEvents() {
        if let data = try? JSONEncoder().encode(events) {
            userDefaults.set(data, forKey: eventsKey)
        }
    }
    
    private func loadEvents() {
        if let data = userDefaults.data(forKey: eventsKey),
           let events = try? JSONDecoder().decode([NotificationEvent].self, from: data) {
            self.events = events
        }
    }
    
    private func saveDeliveryRecords() {
        if let data = try? JSONEncoder().encode(deliveryRecords) {
            userDefaults.set(data, forKey: deliveryKey)
        }
    }
    
    private func loadDeliveryRecords() {
        if let data = userDefaults.data(forKey: deliveryKey),
           let records = try? JSONDecoder().decode([DeliveryRecord].self, from: data) {
            self.deliveryRecords = records
        }
    }
    
    private func saveEngagementRecords() {
        if let data = try? JSONEncoder().encode(engagementRecords) {
            userDefaults.set(data, forKey: engagementKey)
        }
    }
    
    private func loadEngagementRecords() {
        if let data = userDefaults.data(forKey: engagementKey),
           let records = try? JSONDecoder().decode([EngagementRecord].self, from: data) {
            self.engagementRecords = records
        }
    }
    
    private func saveAnalyticsData() {
        // Save computed analytics data
        if let analytics = analyticsData,
           let data = try? JSONEncoder().encode(analytics) {
            userDefaults.set(data, forKey: "AnalyticsDataKey")
        }
        
        if let deliveryStats = deliveryStats,
           let data = try? JSONEncoder().encode(deliveryStats) {
            userDefaults.set(data, forKey: "DeliveryStatsKey")
        }
        
        if let engagementMetrics = engagementMetrics,
           let data = try? JSONEncoder().encode(engagementMetrics) {
            userDefaults.set(data, forKey: "EngagementMetricsKey")
        }
    }
}

// MARK: - Supporting Types

struct NotificationEvent: Codable, Identifiable {
    let id: String
    let notificationId: String
    let type: NotificationEventType
    let category: String?
    let notificationType: NotificationType?
    let timestamp: Date
    let deliveryTime: TimeInterval?
    let timeToOpen: TimeInterval?
    let timeToDismiss: TimeInterval?
    let actionId: String?
    let actionType: NotificationActionType?
    let errorMessage: String?
    let isPersonalized: Bool?
    
    init(
        id: String,
        notificationId: String,
        type: NotificationEventType,
        category: String? = nil,
        notificationType: NotificationType? = nil,
        timestamp: Date,
        deliveryTime: TimeInterval? = nil,
        timeToOpen: TimeInterval? = nil,
        timeToDismiss: TimeInterval? = nil,
        actionId: String? = nil,
        actionType: NotificationActionType? = nil,
        errorMessage: String? = nil,
        isPersonalized: Bool? = nil
    ) {
        self.id = id
        self.notificationId = notificationId
        self.type = type
        self.category = category
        self.notificationType = notificationType
        self.timestamp = timestamp
        self.deliveryTime = deliveryTime
        self.timeToOpen = timeToOpen
        self.timeToDismiss = timeToDismiss
        self.actionId = actionId
        self.actionType = actionType
        self.errorMessage = errorMessage
        self.isPersonalized = isPersonalized
    }
}

struct DeliveryRecord: Codable {
    let notificationId: String
    let sentAt: Date
    let deliveredAt: Date?
    let deliveryStatus: DeliveryStatus
    let attemptCount: Int
    let deliveryTime: TimeInterval?
    let errorMessage: String?
    
    init(
        notificationId: String,
        sentAt: Date,
        deliveredAt: Date? = nil,
        deliveryStatus: DeliveryStatus,
        attemptCount: Int,
        deliveryTime: TimeInterval? = nil,
        errorMessage: String? = nil
    ) {
        self.notificationId = notificationId
        self.sentAt = sentAt
        self.deliveredAt = deliveredAt
        self.deliveryStatus = deliveryStatus
        self.attemptCount = attemptCount
        self.deliveryTime = deliveryTime
        self.errorMessage = errorMessage
    }
}

struct EngagementRecord: Codable {
    let notificationId: String
    let openedAt: Date?
    let dismissedAt: Date?
    let actionTakenAt: Date?
    let timeToOpen: TimeInterval?
    let timeToDismiss: TimeInterval?
    let actionId: String?
    let actionType: NotificationActionType?
    let actionTaken: UserAction
    
    init(
        notificationId: String,
        openedAt: Date? = nil,
        dismissedAt: Date? = nil,
        actionTakenAt: Date? = nil,
        timeToOpen: TimeInterval? = nil,
        timeToDismiss: TimeInterval? = nil,
        actionId: String? = nil,
        actionType: NotificationActionType? = nil,
        actionTaken: UserAction
    ) {
        self.notificationId = notificationId
        self.openedAt = openedAt
        self.dismissedAt = dismissedAt
        self.actionTakenAt = actionTakenAt
        self.timeToOpen = timeToOpen
        self.timeToDismiss = timeToDismiss
        self.actionId = actionId
        self.actionType = actionType
        self.actionTaken = actionTaken
    }
}

struct NotificationAnalytics: Codable {
    let totalNotificationsSent: Int
    let totalDelivered: Int
    let totalOpened: Int
    let totalFailed: Int
    let averageDeliveryTime: TimeInterval
    let averageOpenRate: Double
    let lastUpdated: Date
    let timeRange: AnalyticsTimeRange
}

struct DeliveryStatistics: Codable {
    let totalSent: Int
    let totalDelivered: Int
    let totalFailed: Int
    let totalPending: Int
    let deliveryRate: Double
    let failureRate: Double
    let averageDeliveryTime: TimeInterval
    let p95DeliveryTime: TimeInterval
    let lastUpdated: Date
}

struct EngagementMetrics: Codable {
    let openRate: Double
    let dismissalRate: Double
    let actionRate: Double
    let averageTimeToOpen: TimeInterval
    let averageTimeToDismiss: TimeInterval
    let engagementByCategory: [String: CategoryEngagement]
    let engagementByTimeOfDay: [Int: TimeOfDayEngagement]
    let lastUpdated: Date
}

struct CategoryEngagement: Codable {
    let totalSent: Int
    let totalDelivered: Int
    let totalOpened: Int
    let deliveryRate: Double
    let openRate: Double
}

struct TimeOfDayEngagement: Codable {
    let hour: Int
    let totalSent: Int
    let totalDelivered: Int
    let totalOpened: Int
    let deliveryRate: Double
    let openRate: Double
}

struct PerformanceInsight: Codable, Identifiable {
    let id = UUID()
    let type: InsightType
    let severity: InsightSeverity
    let title: String
    let description: String
    let recommendation: String
    let impact: InsightImpact
}

struct NotificationAnalyticsExport: Codable {
    let analytics: NotificationAnalytics?
    let deliveryStats: DeliveryStatistics?
    let engagementMetrics: EngagementMetrics?
    let performanceInsights: [PerformanceInsight]
    let events: [NotificationEvent]
    let deliveryRecords: [DeliveryRecord]
    let engagementRecords: [EngagementRecord]
    let exportDate: Date
}

// MARK: - Enums

enum NotificationEventType: String, Codable, CaseIterable {
    case sent
    case delivered
    case opened
    case dismissed
    case actionTaken
    case failed
}

enum DeliveryStatus: String, Codable, CaseIterable {
    case sent
    case delivered
    case failed
    case pending
}

enum UserAction: String, Codable, CaseIterable {
    case opened
    case dismissed
    case actionTaken
}

enum NotificationActionType: String, Codable, CaseIterable {
    case view
    case dismiss
    case snooze
    case reply
    case custom
}

enum AnalyticsTimeRange: String, Codable, CaseIterable {
    case last24Hours
    case last7Days
    case last30Days
    case last90Days
}

enum InsightType: String, Codable, CaseIterable {
    case lowDeliveryRate
    case slowDelivery
    case lowEngagement
    case highDismissal
    case bestPerformingCategory
    case optimalSendTime
}

enum InsightSeverity: String, Codable, CaseIterable {
    case info
    case low
    case medium
    case high
    case critical
}

enum InsightImpact: String, Codable, CaseIterable {
    case deliveryOptimization
    case engagementOptimization
    case contentOptimization
    case timingOptimization
}