import XCTest
import UserNotifications
import Combine
@testable import LeenVibe

/// Comprehensive test suite for push notification system
/// Tests core functionality, edge cases, and integration scenarios
final class PushNotificationTests: XCTestCase {
    
    // MARK: - Test Dependencies
    
    private var pushService: PushNotificationService!
    private var contentManager: NotificationContentManager!
    private var analyticsService: NotificationAnalyticsService!
    private var cancellables: Set<AnyCancellable>!
    
    // MARK: - Mock Dependencies
    
    private var mockNotificationCenter: MockUNUserNotificationCenter!
    
    override func setUpWithError() throws {
        try super.setUpWithError()
        
        // Initialize services
        pushService = PushNotificationService()
        contentManager = NotificationContentManager(pushService: pushService)
        analyticsService = NotificationAnalyticsService()
        cancellables = Set<AnyCancellable>()
        
        // Setup mocks
        mockNotificationCenter = MockUNUserNotificationCenter()
    }
    
    override func tearDownWithError() throws {
        cancellables?.removeAll()
        cancellables = nil
        pushService = nil
        contentManager = nil
        analyticsService = nil
        mockNotificationCenter = nil
        
        try super.tearDownWithError()
    }
    
    // MARK: - Push Service Tests
    
    func testPushServiceInitialization() throws {
        XCTAssertNotNil(pushService)
        XCTAssertEqual(pushService.notificationPermissionStatus, .notDetermined)
        XCTAssertFalse(pushService.isRegisteredForRemoteNotifications)
        XCTAssertNil(pushService.deviceToken)
    }
    
    func testDeviceTokenRegistration() throws {
        let testTokenData = Data("test_device_token".utf8)
        
        pushService.didRegisterForRemoteNotifications(withDeviceToken: testTokenData)
        
        XCTAssertTrue(pushService.isRegisteredForRemoteNotifications)
        XCTAssertNotNil(pushService.deviceToken)
        XCTAssertEqual(pushService.deviceToken?.count, 34) // Expected token string length
    }
    
    func testDeviceTokenRegistrationFailure() throws {
        let testError = NSError(domain: "TestError", code: 1001, userInfo: nil)
        
        pushService.didFailToRegisterForRemoteNotifications(withError: testError)
        
        XCTAssertFalse(pushService.isRegisteredForRemoteNotifications)
        XCTAssertNil(pushService.deviceToken)
    }
    
    func testLocalNotificationScheduling() async throws {
        let notification = LocalNotificationRequest(
            id: "test_notification",
            title: "Test Title",
            body: "Test Body",
            category: "GENERAL",
            trigger: .timeInterval(5.0, repeats: false)
        )
        
        let success = await pushService.scheduleLocalNotification(notification)
        
        XCTAssertTrue(success)
        XCTAssertTrue(pushService.pendingNotifications.contains { $0.id == "test_notification" })
    }
    
    func testNotificationCancellation() async throws {
        // First schedule a notification
        let notification = LocalNotificationRequest(
            id: "test_cancel",
            title: "Test Cancel",
            body: "Test Body",
            category: "GENERAL",
            trigger: .timeInterval(10.0, repeats: false)
        )
        
        await pushService.scheduleLocalNotification(notification)
        XCTAssertTrue(pushService.pendingNotifications.contains { $0.id == "test_cancel" })
        
        // Then cancel it
        pushService.cancelNotification(withId: "test_cancel")
        
        XCTAssertFalse(pushService.pendingNotifications.contains { $0.id == "test_cancel" })
    }
    
    func testBadgeManagement() throws {
        // Test setting badge count
        pushService.updateBadgeCount(5)
        
        // Test clearing badge
        pushService.clearBadge()
    }
    
    // MARK: - Content Manager Tests
    
    func testContentManagerInitialization() throws {
        XCTAssertNotNil(contentManager)
        XCTAssertFalse(contentManager.contentTemplates.isEmpty)
        XCTAssertTrue(contentManager.scheduledCampaigns.isEmpty)
    }
    
    func testTemplateLoading() throws {
        let templates = contentManager.contentTemplates
        
        XCTAssertFalse(templates.isEmpty)
        XCTAssertTrue(templates.contains { $0.type == .welcome })
        XCTAssertTrue(templates.contains { $0.type == .reminder })
        XCTAssertTrue(templates.contains { $0.type == .achievement })
    }
    
    func testPersonalizedNotificationGeneration() async throws {
        let templateId = "daily_meditation"
        let personalizationData = ["duration": "10", "preferredTime": "09:00"]
        
        let notification = await contentManager.generatePersonalizedNotification(
            templateId: templateId,
            personalizationData: personalizationData
        )
        
        XCTAssertNotNil(notification)
        XCTAssertTrue(notification!.body.contains("10"))
    }
    
    func testCampaignCreation() async throws {
        let campaign = NotificationCampaign(
            id: "test_campaign",
            name: "Test Campaign",
            description: "Test campaign description",
            startDate: Date(),
            endDate: Calendar.current.date(byAdding: .day, value: 3, to: Date()) ?? Date(),
            schedule: [
                CampaignScheduleItem(templateId: "welcome_day1", offsetDays: 0),
                CampaignScheduleItem(templateId: "welcome_day3", offsetDays: 2)
            ]
        )
        
        let success = await contentManager.createNotificationCampaign(campaign)
        
        XCTAssertTrue(success)
        XCTAssertTrue(contentManager.scheduledCampaigns.contains { $0.id == "test_campaign" })
    }
    
    func testWelcomeCampaignCreation() async throws {
        let success = await contentManager.createWelcomeCampaign()
        
        XCTAssertTrue(success)
        XCTAssertTrue(contentManager.scheduledCampaigns.contains { $0.name.contains("Welcome") })
    }
    
    func testDailyReminderCampaignCreation() async throws {
        let days = 5
        let success = await contentManager.createDailyReminderCampaign(for: days)
        
        XCTAssertTrue(success)
        
        let campaign = contentManager.scheduledCampaigns.first { $0.name.contains("Daily") }
        XCTAssertNotNil(campaign)
        XCTAssertEqual(campaign?.schedule.count, days)
    }
    
    func testCampaignCancellation() async throws {
        // Create a campaign first
        await contentManager.createWelcomeCampaign()
        
        guard let campaignId = contentManager.scheduledCampaigns.first?.id else {
            XCTFail("No campaign found to cancel")
            return
        }
        
        contentManager.cancelCampaign(withId: campaignId)
        
        let cancelledCampaign = contentManager.scheduledCampaigns.first { $0.id == campaignId }
        XCTAssertEqual(cancelledCampaign?.status, .cancelled)
    }
    
    // MARK: - Analytics Tests
    
    func testAnalyticsServiceInitialization() throws {
        XCTAssertNotNil(analyticsService)
        XCTAssertNil(analyticsService.analyticsData)
        XCTAssertNil(analyticsService.deliveryStats)
        XCTAssertNil(analyticsService.engagementMetrics)
    }
    
    func testNotificationEventTracking() async throws {
        // Track notification sent
        analyticsService.trackNotificationSent(
            id: "test_notification",
            type: .reminder,
            category: "REMINDER"
        )
        
        // Track notification delivered
        analyticsService.trackNotificationDelivered(
            id: "test_notification",
            deliveryTime: 2.5
        )
        
        // Track notification opened
        analyticsService.trackNotificationOpened(
            id: "test_notification",
            timeToOpen: 5.0
        )
        
        // Calculate analytics
        await analyticsService.calculateAnalytics()
        
        XCTAssertNotNil(analyticsService.analyticsData)
        XCTAssertEqual(analyticsService.analyticsData?.totalNotificationsSent, 1)
        XCTAssertEqual(analyticsService.analyticsData?.totalDelivered, 1)
        XCTAssertEqual(analyticsService.analyticsData?.totalOpened, 1)
    }
    
    func testDeliveryStatisticsCalculation() async throws {
        // Track multiple notifications
        for i in 1...10 {
            analyticsService.trackNotificationSent(
                id: "notification_\(i)",
                type: .reminder,
                category: "REMINDER"
            )
            
            if i <= 8 { // 8 out of 10 delivered
                analyticsService.trackNotificationDelivered(
                    id: "notification_\(i)",
                    deliveryTime: Double(i)
                )
            }
            
            if i >= 9 { // 2 failed
                analyticsService.trackNotificationFailed(
                    id: "notification_\(i)",
                    error: NSError(domain: "TestError", code: 1001, userInfo: nil)
                )
            }
        }
        
        await analyticsService.calculateAnalytics()
        
        let deliveryStats = analyticsService.deliveryStats
        XCTAssertNotNil(deliveryStats)
        XCTAssertEqual(deliveryStats?.totalSent, 10)
        XCTAssertEqual(deliveryStats?.totalDelivered, 8)
        XCTAssertEqual(deliveryStats?.totalFailed, 2)
        XCTAssertEqual(deliveryStats?.deliveryRate, 0.8, accuracy: 0.01)
        XCTAssertEqual(deliveryStats?.failureRate, 0.2, accuracy: 0.01)
    }
    
    func testEngagementMetricsCalculation() async throws {
        // Track notifications with various engagement patterns
        for i in 1...10 {
            analyticsService.trackNotificationSent(
                id: "engagement_\(i)",
                type: .reminder,
                category: "REMINDER"
            )
            
            analyticsService.trackNotificationDelivered(
                id: "engagement_\(i)",
                deliveryTime: 1.0
            )
            
            if i <= 6 { // 6 out of 10 opened
                analyticsService.trackNotificationOpened(
                    id: "engagement_\(i)",
                    timeToOpen: Double(i * 2)
                )
            } else { // 4 dismissed
                analyticsService.trackNotificationDismissed(
                    id: "engagement_\(i)",
                    timeToDismiss: Double(i)
                )
            }
        }
        
        await analyticsService.calculateAnalytics()
        
        let engagementMetrics = analyticsService.engagementMetrics
        XCTAssertNotNil(engagementMetrics)
        XCTAssertEqual(engagementMetrics?.openRate, 0.6, accuracy: 0.01)
        XCTAssertEqual(engagementMetrics?.dismissalRate, 0.4, accuracy: 0.01)
    }
    
    func testPerformanceInsightsGeneration() async throws {
        // Create scenario with low delivery rate
        for i in 1...10 {
            analyticsService.trackNotificationSent(
                id: "insight_\(i)",
                type: .reminder,
                category: "REMINDER"
            )
            
            if i <= 5 { // Only 50% delivery rate
                analyticsService.trackNotificationDelivered(
                    id: "insight_\(i)",
                    deliveryTime: 1.0
                )
                
                if i <= 1 { // Very low open rate
                    analyticsService.trackNotificationOpened(
                        id: "insight_\(i)",
                        timeToOpen: 2.0
                    )
                }
            } else {
                analyticsService.trackNotificationFailed(
                    id: "insight_\(i)",
                    error: NSError(domain: "TestError", code: 1001, userInfo: nil)
                )
            }
        }
        
        await analyticsService.calculateAnalytics()
        
        let insights = analyticsService.performanceInsights
        XCTAssertFalse(insights.isEmpty)
        XCTAssertTrue(insights.contains { $0.type == .lowDeliveryRate })
        XCTAssertTrue(insights.contains { $0.type == .lowEngagement })
    }
    
    func testAnalyticsDataExport() async throws {
        // Add some test data
        analyticsService.trackNotificationSent(
            id: "export_test",
            type: .reminder,
            category: "REMINDER"
        )
        
        analyticsService.trackNotificationDelivered(
            id: "export_test",
            deliveryTime: 1.5
        )
        
        let exportData = await analyticsService.exportAnalyticsData()
        
        XCTAssertNotNil(exportData.analytics)
        XCTAssertNotNil(exportData.deliveryStats)
        XCTAssertNotNil(exportData.engagementMetrics)
        XCTAssertFalse(exportData.events.isEmpty)
    }
    
    // MARK: - Integration Tests
    
    func testFullNotificationWorkflow() async throws {
        // Create personalization profile
        let profile = PersonalizationProfile(
            userName: "Test User",
            preferredReminderTime: "09:00",
            preferredSessionDuration: 10
        )
        contentManager.updatePersonalizationProfile(profile)
        
        // Generate personalized notification
        let notification = await contentManager.generatePersonalizedNotification(
            templateId: "daily_meditation",
            personalizationData: ["duration": "10"]
        )
        
        XCTAssertNotNil(notification)
        
        // Schedule the notification
        let success = await pushService.scheduleLocalNotification(notification!)
        XCTAssertTrue(success)
        
        // Track analytics
        analyticsService.trackNotificationSent(
            id: notification!.id,
            type: .reminder,
            category: notification!.category
        )
        
        // Simulate delivery and engagement
        analyticsService.trackNotificationDelivered(
            id: notification!.id,
            deliveryTime: 2.0
        )
        
        analyticsService.trackNotificationOpened(
            id: notification!.id,
            timeToOpen: 5.0
        )
        
        // Calculate analytics
        await analyticsService.calculateAnalytics()
        
        // Verify results
        XCTAssertEqual(analyticsService.analyticsData?.totalNotificationsSent, 1)
        XCTAssertEqual(analyticsService.analyticsData?.totalDelivered, 1)
        XCTAssertEqual(analyticsService.analyticsData?.totalOpened, 1)
    }
    
    func testCampaignExecutionAndTracking() async throws {
        let expectation = XCTestExpectation(description: "Campaign execution")
        
        // Create and execute welcome campaign
        let success = await contentManager.createWelcomeCampaign()
        XCTAssertTrue(success)
        
        let campaign = contentManager.scheduledCampaigns.first { $0.name.contains("Welcome") }
        XCTAssertNotNil(campaign)
        
        // Simulate campaign execution and tracking
        for scheduleItem in campaign!.schedule {
            let notificationId = "campaign_\(campaign!.id)_\(scheduleItem.templateId)"
            
            analyticsService.trackNotificationSent(
                id: notificationId,
                type: .welcome,
                category: "GENERAL"
            )
            
            analyticsService.trackNotificationDelivered(
                id: notificationId,
                deliveryTime: 1.0
            )
        }
        
        await analyticsService.calculateAnalytics()
        
        XCTAssertEqual(analyticsService.analyticsData?.totalNotificationsSent, campaign!.schedule.count)
        
        expectation.fulfill()
        await fulfillment(of: [expectation], timeout: 1.0)
    }
    
    // MARK: - Performance Tests
    
    func testNotificationSchedulingPerformance() async throws {
        let notificationCount = 100
        let startTime = CFAbsoluteTimeGetCurrent()
        
        for i in 1...notificationCount {
            let notification = LocalNotificationRequest(
                id: "perf_test_\(i)",
                title: "Performance Test \(i)",
                body: "Testing notification scheduling performance",
                category: "GENERAL",
                trigger: .timeInterval(Double(i), repeats: false)
            )
            
            await pushService.scheduleLocalNotification(notification)
        }
        
        let endTime = CFAbsoluteTimeGetCurrent()
        let executionTime = endTime - startTime
        
        XCTAssertEqual(pushService.pendingNotifications.count, notificationCount)
        XCTAssertLessThan(executionTime, 5.0, "Scheduling 100 notifications should take less than 5 seconds")
    }
    
    func testAnalyticsCalculationPerformance() async throws {
        let eventCount = 1000
        
        // Generate large dataset
        for i in 1...eventCount {
            analyticsService.trackNotificationSent(
                id: "perf_analytics_\(i)",
                type: .reminder,
                category: "REMINDER"
            )
            
            if i % 2 == 0 {
                analyticsService.trackNotificationDelivered(
                    id: "perf_analytics_\(i)",
                    deliveryTime: Double.random(in: 0.5...3.0)
                )
                
                if i % 4 == 0 {
                    analyticsService.trackNotificationOpened(
                        id: "perf_analytics_\(i)",
                        timeToOpen: Double.random(in: 1.0...10.0)
                    )
                }
            }
        }
        
        let startTime = CFAbsoluteTimeGetCurrent()
        await analyticsService.calculateAnalytics()
        let endTime = CFAbsoluteTimeGetCurrent()
        
        let executionTime = endTime - startTime
        
        XCTAssertNotNil(analyticsService.analyticsData)
        XCTAssertLessThan(executionTime, 2.0, "Analytics calculation should take less than 2 seconds for 1000 events")
    }
    
    // MARK: - Edge Case Tests
    
    func testEmptyNotificationScheduling() async throws {
        let notification = LocalNotificationRequest(
            id: "",
            title: "",
            body: "",
            category: "GENERAL",
            trigger: .immediate
        )
        
        let success = await pushService.scheduleLocalNotification(notification)
        XCTAssertTrue(success) // Should handle empty content gracefully
    }
    
    func testInvalidCampaignCreation() async throws {
        let invalidCampaign = NotificationCampaign(
            id: "invalid_campaign",
            name: "Invalid Campaign",
            description: "Campaign with invalid dates",
            startDate: Date().addingTimeInterval(86400), // Tomorrow
            endDate: Date(), // Today (invalid)
            schedule: []
        )
        
        let success = await contentManager.createNotificationCampaign(invalidCampaign)
        XCTAssertFalse(success) // Should fail validation
    }
    
    func testNonExistentTemplatePersonalization() async throws {
        let notification = await contentManager.generatePersonalizedNotification(
            templateId: "non_existent_template"
        )
        
        XCTAssertNil(notification) // Should return nil for non-existent template
    }
    
    func testAnalyticsWithNoData() async throws {
        await analyticsService.calculateAnalytics()
        
        let analytics = analyticsService.analyticsData
        XCTAssertNotNil(analytics)
        XCTAssertEqual(analytics?.totalNotificationsSent, 0)
        XCTAssertEqual(analytics?.totalDelivered, 0)
        XCTAssertEqual(analytics?.totalOpened, 0)
    }
    
    // MARK: - Memory and Resource Tests
    
    func testMemoryUsageWithLargeDataset() async throws {
        let initialMemory = getMemoryUsage()
        
        // Generate large amount of test data
        for i in 1...10000 {
            analyticsService.trackNotificationSent(
                id: "memory_test_\(i)",
                type: .reminder,
                category: "REMINDER"
            )
        }
        
        await analyticsService.calculateAnalytics()
        
        let finalMemory = getMemoryUsage()
        let memoryIncrease = finalMemory - initialMemory
        
        XCTAssertLessThan(memoryIncrease, 50.0, "Memory increase should be less than 50MB for large dataset")
    }
    
    func testResourceCleanup() async throws {
        // Schedule many notifications
        for i in 1...50 {
            let notification = LocalNotificationRequest(
                id: "cleanup_test_\(i)",
                title: "Cleanup Test",
                body: "Testing resource cleanup",
                category: "GENERAL",
                trigger: .timeInterval(Double(i), repeats: false)
            )
            
            await pushService.scheduleLocalNotification(notification)
        }
        
        XCTAssertEqual(pushService.pendingNotifications.count, 50)
        
        // Cancel all notifications
        pushService.cancelAllNotifications()
        
        XCTAssertTrue(pushService.pendingNotifications.isEmpty)
    }
    
    // MARK: - Helper Methods
    
    private func getMemoryUsage() -> Double {
        let info = mach_task_basic_info()
        var count = mach_msg_type_number_t(MemoryLayout<mach_task_basic_info>.size)/4
        
        let kerr: kern_return_t = withUnsafeMutablePointer(to: &info) {
            $0.withMemoryRebound(to: integer_t.self, capacity: 1) {
                task_info(mach_task_self_, task_flavor_t(MACH_TASK_BASIC_INFO), $0, &count)
            }
        }
        
        if kerr == KERN_SUCCESS {
            return Double(info.resident_size) / 1024.0 / 1024.0 // Convert to MB
        }
        
        return 0
    }
}

// MARK: - Mock Classes

class MockUNUserNotificationCenter {
    var scheduledNotifications: [UNNotificationRequest] = []
    var authorizationStatus: UNAuthorizationStatus = .notDetermined
    
    func requestAuthorization(options: UNAuthorizationOptions) async throws -> Bool {
        authorizationStatus = .authorized
        return true
    }
    
    func add(_ request: UNNotificationRequest) async throws {
        scheduledNotifications.append(request)
    }
    
    func removeAllPendingNotificationRequests() {
        scheduledNotifications.removeAll()
    }
    
    func removePendingNotificationRequests(withIdentifiers identifiers: [String]) {
        scheduledNotifications.removeAll { identifiers.contains($0.identifier) }
    }
}

// MARK: - Test Extensions

extension PushNotificationTests {
    
    func testQuickNotificationMethods() async throws {
        // Test welcome notification
        await pushService.sendWelcomeNotification()
        XCTAssertTrue(pushService.pendingNotifications.contains { $0.title.contains("Welcome") })
        
        // Test daily reminder
        let reminderDate = Calendar.current.date(byAdding: .hour, value: 1, to: Date()) ?? Date()
        await pushService.sendDailyReminderNotification(at: reminderDate)
        XCTAssertTrue(pushService.pendingNotifications.contains { $0.title.contains("Daily Practice") })
        
        // Test achievement notification
        await pushService.sendAchievementNotification(achievement: "First Week Complete")
        XCTAssertTrue(pushService.pendingNotifications.contains { $0.title.contains("Achievement") })
    }
    
    func testNotificationPreferences() throws {
        let preferences = contentManager.getNotificationPreferences()
        XCTAssertNotNil(preferences)
        
        // Modify preferences
        var modifiedPreferences = preferences
        modifiedPreferences.allowReminders = false
        modifiedPreferences.quietHoursEnabled = true
        
        contentManager.saveNotificationPreferences(modifiedPreferences)
        
        let savedPreferences = contentManager.getNotificationPreferences()
        XCTAssertFalse(savedPreferences.allowReminders)
        XCTAssertTrue(savedPreferences.quietHoursEnabled)
    }
    
    func testPersonalizationProfile() throws {
        let profile = PersonalizationProfile(
            userName: "Test User",
            preferredReminderTime: "08:30",
            preferredSessionDuration: 15,
            interests: ["Meditation", "Mindfulness"],
            completedSessions: 25,
            currentStreak: 7
        )
        
        contentManager.updatePersonalizationProfile(profile)
        
        let savedProfile = contentManager.personalizationProfile
        XCTAssertNotNil(savedProfile)
        XCTAssertEqual(savedProfile?.userName, "Test User")
        XCTAssertEqual(savedProfile?.preferredReminderTime, "08:30")
        XCTAssertEqual(savedProfile?.preferredSessionDuration, 15)
        XCTAssertEqual(savedProfile?.completedSessions, 25)
        XCTAssertEqual(savedProfile?.currentStreak, 7)
    }
}