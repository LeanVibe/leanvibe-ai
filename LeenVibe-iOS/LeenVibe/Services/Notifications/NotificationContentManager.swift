import Foundation
import UserNotifications
import Combine
import os.log

/// Advanced notification content management and intelligent scheduling system
/// Handles dynamic content generation, personalization, and optimal delivery timing
@MainActor
class NotificationContentManager: ObservableObject {
    
    // MARK: - Published Properties
    
    @Published var contentTemplates: [NotificationTemplate] = []
    @Published var scheduledCampaigns: [NotificationCampaign] = []
    @Published var deliveryMetrics: NotificationDeliveryMetrics?
    @Published var personalizationProfile: PersonalizationProfile?
    
    // MARK: - Dependencies
    
    private let pushService: PushNotificationService
    private let logger = Logger(subsystem: "com.leenvibe.notifications", category: "ContentManager")
    
    // MARK: - Content Generation
    
    private let contentGenerator = NotificationContentGenerator()
    private let personalizer = NotificationPersonalizer()
    private let scheduler = IntelligentScheduler()
    
    // MARK: - Storage
    
    private let userDefaults = UserDefaults.standard
    private let templatesKey = "NotificationTemplatesKey"
    private let campaignsKey = "NotificationCampaignsKey"
    private let metricsKey = "NotificationMetricsKey"
    
    init(pushService: PushNotificationService) {
        self.pushService = pushService
        loadStoredData()
        setupDefaultTemplates()
        logger.info("NotificationContentManager initialized")
    }
    
    // MARK: - Template Management
    
    private func setupDefaultTemplates() {
        if contentTemplates.isEmpty {
            contentTemplates = createDefaultTemplates()
            saveTemplates()
        }
    }
    
    private func createDefaultTemplates() -> [NotificationTemplate] {
        return [
            // Welcome Series
            NotificationTemplate(
                id: "welcome_day1",
                type: .welcome,
                title: "Welcome to LeenVibe! 🌟",
                body: "Start your wellness journey with personalized meditation and mindfulness practices.",
                category: "GENERAL",
                priority: .high,
                tags: ["welcome", "onboarding"],
                personalizationFields: ["userName"]
            ),
            
            NotificationTemplate(
                id: "welcome_day3",
                type: .welcome,
                title: "Ready to explore? 🧭",
                body: "Discover guided meditations, breathing exercises, and mindfulness techniques tailored just for you.",
                category: "GENERAL",
                priority: .medium,
                tags: ["welcome", "exploration"],
                personalizationFields: []
            ),
            
            // Daily Reminders
            NotificationTemplate(
                id: "daily_meditation",
                type: .reminder,
                title: "Time for mindfulness 🧘‍♀️",
                body: "Take {duration} minutes to center yourself with today's guided meditation.",
                category: "REMINDER",
                priority: .medium,
                tags: ["daily", "meditation"],
                personalizationFields: ["duration", "preferredTime"]
            ),
            
            NotificationTemplate(
                id: "breathing_reminder",
                type: .reminder,
                title: "Breathe and reset 💨",
                body: "A quick 2-minute breathing exercise can help you refocus and energize.",
                category: "REMINDER",
                priority: .low,
                tags: ["breathing", "quick"],
                personalizationFields: []
            ),
            
            // Achievement Notifications
            NotificationTemplate(
                id: "streak_milestone",
                type: .achievement,
                title: "Amazing streak! 🔥",
                body: "Congratulations! You've maintained your {streakType} practice for {days} days straight!",
                category: "ACHIEVEMENT",
                priority: .high,
                tags: ["streak", "milestone"],
                personalizationFields: ["streakType", "days"]
            ),
            
            NotificationTemplate(
                id: "session_completion",
                type: .achievement,
                title: "Session complete! ✨",
                body: "Great job finishing your {sessionType} session. You're {percentage}% closer to your weekly goal!",
                category: "ACHIEVEMENT",
                priority: .medium,
                tags: ["completion", "progress"],
                personalizationFields: ["sessionType", "percentage"]
            ),
            
            // Motivational Content
            NotificationTemplate(
                id: "weekly_motivation",
                type: .motivation,
                title: "Your weekly insight 💡",
                body: "{motivationalQuote} - Take a moment to reflect on your wellness journey.",
                category: "GENERAL",
                priority: .low,
                tags: ["motivation", "weekly"],
                personalizationFields: ["motivationalQuote"]
            ),
            
            // Educational Tips
            NotificationTemplate(
                id: "wellness_tip",
                type: .educational,
                title: "Wellness tip of the day 🌱",
                body: "{tip} Try incorporating this into your daily routine for better well-being.",
                category: "GENERAL",
                priority: .low,
                tags: ["tip", "education"],
                personalizationFields: ["tip"]
            ),
            
            // Social Notifications
            NotificationTemplate(
                id: "friend_achievement",
                type: .social,
                title: "Friend's milestone! 👥",
                body: "{friendName} just completed their {milestone}. Send them some encouragement!",
                category: "SOCIAL",
                priority: .medium,
                tags: ["social", "friend", "milestone"],
                personalizationFields: ["friendName", "milestone"]
            ),
            
            // System Notifications
            NotificationTemplate(
                id: "update_available",
                type: .system,
                title: "App update available 📱",
                body: "New features and improvements are ready. Update now for the best experience.",
                category: "SYSTEM",
                priority: .medium,
                tags: ["update", "system"],
                personalizationFields: []
            )
        ]
    }
    
    // MARK: - Campaign Management
    
    func createNotificationCampaign(_ campaign: NotificationCampaign) async -> Bool {
        do {
            // Validate campaign
            guard validateCampaign(campaign) else {
                logger.error("Campaign validation failed: \(campaign.id)")
                return false
            }
            
            // Schedule campaign notifications
            let scheduledNotifications = try await scheduleNotificationsForCampaign(campaign)
            
            // Update campaign with scheduled notification IDs
            var updatedCampaign = campaign
            updatedCampaign.scheduledNotificationIds = scheduledNotifications.map { $0.id }
            updatedCampaign.status = .active
            
            scheduledCampaigns.append(updatedCampaign)
            saveCampaigns()
            
            logger.info("Created campaign: \(campaign.id) with \(scheduledNotifications.count) notifications")
            return true
            
        } catch {
            logger.error("Failed to create campaign: \(error)")
            return false
        }
    }
    
    func cancelCampaign(withId campaignId: String) {
        guard let campaignIndex = scheduledCampaigns.firstIndex(where: { $0.id == campaignId }) else {
            logger.warning("Campaign not found: \(campaignId)")
            return
        }
        
        let campaign = scheduledCampaigns[campaignIndex]
        
        // Cancel all scheduled notifications for this campaign
        for notificationId in campaign.scheduledNotificationIds {
            pushService.cancelNotification(withId: notificationId)
        }
        
        // Update campaign status
        scheduledCampaigns[campaignIndex].status = .cancelled
        saveCampaigns()
        
        logger.info("Cancelled campaign: \(campaignId)")
    }
    
    // MARK: - Content Generation
    
    func generatePersonalizedNotification(
        templateId: String,
        personalizationData: [String: Any] = [:]
    ) async -> LocalNotificationRequest? {
        
        guard let template = contentTemplates.first(where: { $0.id == templateId }) else {
            logger.error("Template not found: \(templateId)")
            return nil
        }
        
        // Generate personalized content
        let personalizedContent = await personalizer.personalizeContent(
            template: template,
            data: personalizationData,
            profile: personalizationProfile
        )
        
        // Determine optimal delivery time
        let optimalTime = await scheduler.calculateOptimalDeliveryTime(
            for: template.type,
            userProfile: personalizationProfile
        )
        
        let notification = LocalNotificationRequest(
            id: "generated_\(templateId)_\(UUID().uuidString)",
            title: personalizedContent.title,
            body: personalizedContent.body,
            subtitle: personalizedContent.subtitle,
            category: template.category,
            trigger: .date(optimalTime)
        )
        
        logger.debug("Generated personalized notification from template: \(templateId)")
        return notification
    }
    
    // MARK: - Intelligent Scheduling
    
    private func scheduleNotificationsForCampaign(_ campaign: NotificationCampaign) async throws -> [LocalNotificationRequest] {
        var scheduledNotifications: [LocalNotificationRequest] = []
        
        for scheduleItem in campaign.schedule {
            guard let template = contentTemplates.first(where: { $0.id == scheduleItem.templateId }) else {
                logger.warning("Template not found for schedule item: \(scheduleItem.templateId)")
                continue
            }
            
            let deliveryTime = calculateDeliveryTime(
                from: campaign.startDate,
                offset: scheduleItem.offsetDays,
                preferredTime: scheduleItem.preferredTime
            )
            
            // Skip if delivery time is in the past
            guard deliveryTime > Date() else {
                logger.debug("Skipping past delivery time for template: \(template.id)")
                continue
            }
            
            // Generate personalized content
            let personalizedContent = await personalizer.personalizeContent(
                template: template,
                data: scheduleItem.personalizationData,
                profile: personalizationProfile
            )
            
            let notification = LocalNotificationRequest(
                id: "campaign_\(campaign.id)_\(template.id)_\(UUID().uuidString)",
                title: personalizedContent.title,
                body: personalizedContent.body,
                subtitle: personalizedContent.subtitle,
                category: template.category,
                trigger: .date(deliveryTime)
            )
            
            // Schedule the notification
            let success = await pushService.scheduleLocalNotification(notification)
            if success {
                scheduledNotifications.append(notification)
            }
        }
        
        return scheduledNotifications
    }
    
    private func calculateDeliveryTime(
        from startDate: Date,
        offset offsetDays: Int,
        preferredTime: String?
    ) -> Date {
        let calendar = Calendar.current
        var deliveryDate = calendar.date(byAdding: .day, value: offsetDays, to: startDate) ?? startDate
        
        // Apply preferred time if specified
        if let preferredTime = preferredTime,
           let timeComponents = parseTimeString(preferredTime) {
            deliveryDate = calendar.date(
                bySettingHour: timeComponents.hour,
                minute: timeComponents.minute,
                second: 0,
                of: deliveryDate
            ) ?? deliveryDate
        }
        
        return deliveryDate
    }
    
    private func parseTimeString(_ timeString: String) -> (hour: Int, minute: Int)? {
        let components = timeString.split(separator: ":").compactMap { Int($0) }
        guard components.count == 2 else { return nil }
        return (hour: components[0], minute: components[1])
    }
    
    // MARK: - Quick Campaign Methods
    
    func createWelcomeCampaign() async -> Bool {
        let welcomeCampaign = NotificationCampaign(
            id: "welcome_series_\(UUID().uuidString)",
            name: "Welcome Series",
            description: "Onboarding sequence for new users",
            startDate: Date(),
            endDate: Calendar.current.date(byAdding: .day, value: 7, to: Date()) ?? Date(),
            schedule: [
                CampaignScheduleItem(
                    templateId: "welcome_day1",
                    offsetDays: 0,
                    preferredTime: "10:00"
                ),
                CampaignScheduleItem(
                    templateId: "welcome_day3",
                    offsetDays: 2,
                    preferredTime: "14:00"
                ),
                CampaignScheduleItem(
                    templateId: "daily_meditation",
                    offsetDays: 3,
                    preferredTime: "09:00",
                    personalizationData: ["duration": "5"]
                )
            ]
        )
        
        return await createNotificationCampaign(welcomeCampaign)
    }
    
    func createDailyReminderCampaign(for days: Int) async -> Bool {
        let schedule = (0..<days).map { day in
            CampaignScheduleItem(
                templateId: "daily_meditation",
                offsetDays: day,
                preferredTime: personalizationProfile?.preferredReminderTime ?? "09:00",
                personalizationData: [
                    "duration": String(personalizationProfile?.preferredSessionDuration ?? 10)
                ]
            )
        }
        
        let reminderCampaign = NotificationCampaign(
            id: "daily_reminders_\(UUID().uuidString)",
            name: "Daily Meditation Reminders",
            description: "Daily reminders for meditation practice",
            startDate: Date(),
            endDate: Calendar.current.date(byAdding: .day, value: days, to: Date()) ?? Date(),
            schedule: schedule
        )
        
        return await createNotificationCampaign(reminderCampaign)
    }
    
    // MARK: - Analytics & Metrics
    
    func updateDeliveryMetrics() async {
        let delivered = await pushService.getDeliveredNotifications()
        let pending = await pushService.getPendingNotifications()
        
        let metrics = NotificationDeliveryMetrics(
            totalSent: delivered.count + pending.count,
            totalDelivered: delivered.count,
            totalPending: pending.count,
            deliveryRate: delivered.count > 0 ? Double(delivered.count) / Double(delivered.count + pending.count) : 0,
            lastUpdated: Date()
        )
        
        deliveryMetrics = metrics
        saveMetrics()
    }
    
    // MARK: - Personalization Profile
    
    func updatePersonalizationProfile(_ profile: PersonalizationProfile) {
        personalizationProfile = profile
        savePersonalizationProfile()
        logger.info("Updated personalization profile")
    }
    
    // MARK: - Validation
    
    private func validateCampaign(_ campaign: NotificationCampaign) -> Bool {
        // Check if campaign dates are valid
        guard campaign.startDate <= campaign.endDate else {
            logger.error("Invalid campaign dates: start date after end date")
            return false
        }
        
        // Check if templates exist
        for scheduleItem in campaign.schedule {
            guard contentTemplates.contains(where: { $0.id == scheduleItem.templateId }) else {
                logger.error("Template not found: \(scheduleItem.templateId)")
                return false
            }
        }
        
        return true
    }
    
    // MARK: - Data Persistence
    
    private func loadStoredData() {
        loadTemplates()
        loadCampaigns()
        loadMetrics()
        loadPersonalizationProfile()
    }
    
    private func loadTemplates() {
        if let data = userDefaults.data(forKey: templatesKey),
           let templates = try? JSONDecoder().decode([NotificationTemplate].self, from: data) {
            contentTemplates = templates
        }
    }
    
    private func saveTemplates() {
        if let data = try? JSONEncoder().encode(contentTemplates) {
            userDefaults.set(data, forKey: templatesKey)
        }
    }
    
    private func loadCampaigns() {
        if let data = userDefaults.data(forKey: campaignsKey),
           let campaigns = try? JSONDecoder().decode([NotificationCampaign].self, from: data) {
            scheduledCampaigns = campaigns
        }
    }
    
    private func saveCampaigns() {
        if let data = try? JSONEncoder().encode(scheduledCampaigns) {
            userDefaults.set(data, forKey: campaignsKey)
        }
    }
    
    private func loadMetrics() {
        if let data = userDefaults.data(forKey: metricsKey),
           let metrics = try? JSONDecoder().decode(NotificationDeliveryMetrics.self, from: data) {
            deliveryMetrics = metrics
        }
    }
    
    private func saveMetrics() {
        if let metrics = deliveryMetrics,
           let data = try? JSONEncoder().encode(metrics) {
            userDefaults.set(data, forKey: metricsKey)
        }
    }
    
    private func loadPersonalizationProfile() {
        if let data = userDefaults.data(forKey: "PersonalizationProfileKey"),
           let profile = try? JSONDecoder().decode(PersonalizationProfile.self, from: data) {
            personalizationProfile = profile
        }
    }
    
    private func savePersonalizationProfile() {
        if let profile = personalizationProfile,
           let data = try? JSONEncoder().encode(profile) {
            userDefaults.set(data, forKey: "PersonalizationProfileKey")
        }
    }
}

// MARK: - Supporting Types

struct NotificationTemplate: Codable, Identifiable {
    let id: String
    let type: NotificationType
    let title: String
    let body: String
    let category: String
    let priority: NotificationPriority
    let tags: [String]
    let personalizationFields: [String]
    
    var subtitle: String? = nil
    var soundName: String? = nil
    var badgeCount: Int? = nil
}

struct NotificationCampaign: Codable, Identifiable {
    let id: String
    let name: String
    let description: String
    let startDate: Date
    let endDate: Date
    let schedule: [CampaignScheduleItem]
    
    var status: CampaignStatus = .draft
    var scheduledNotificationIds: [String] = []
    var targetAudience: [String] = []
}

struct CampaignScheduleItem: Codable {
    let templateId: String
    let offsetDays: Int
    let preferredTime: String?
    let personalizationData: [String: String]
    
    init(templateId: String, offsetDays: Int, preferredTime: String? = nil, personalizationData: [String: String] = [:]) {
        self.templateId = templateId
        self.offsetDays = offsetDays
        self.preferredTime = preferredTime
        self.personalizationData = personalizationData
    }
}

struct PersonalizedContent {
    let title: String
    let body: String
    let subtitle: String?
}

struct NotificationDeliveryMetrics: Codable {
    let totalSent: Int
    let totalDelivered: Int
    let totalPending: Int
    let deliveryRate: Double
    let lastUpdated: Date
}

struct PersonalizationProfile: Codable {
    let userName: String?
    let preferredReminderTime: String
    let preferredSessionDuration: Int
    let interests: [String]
    let completedSessions: Int
    let currentStreak: Int
    let timezone: String
    let lastActiveDate: Date
    
    init(
        userName: String? = nil,
        preferredReminderTime: String = "09:00",
        preferredSessionDuration: Int = 10,
        interests: [String] = [],
        completedSessions: Int = 0,
        currentStreak: Int = 0,
        timezone: String = TimeZone.current.identifier,
        lastActiveDate: Date = Date()
    ) {
        self.userName = userName
        self.preferredReminderTime = preferredReminderTime
        self.preferredSessionDuration = preferredSessionDuration
        self.interests = interests
        self.completedSessions = completedSessions
        self.currentStreak = currentStreak
        self.timezone = timezone
        self.lastActiveDate = lastActiveDate
    }
}

enum NotificationType: String, Codable, CaseIterable {
    case welcome
    case reminder
    case achievement
    case motivation
    case educational
    case social
    case system
}

enum NotificationPriority: String, Codable, CaseIterable {
    case low
    case medium
    case high
    case critical
}

enum CampaignStatus: String, Codable, CaseIterable {
    case draft
    case active
    case paused
    case completed
    case cancelled
}

// MARK: - Content Generation & Personalization

class NotificationContentGenerator {
    private let motivationalQuotes = [
        "Every moment is a fresh beginning.",
        "Peace comes from within. Do not seek it without.",
        "The present moment is the only time over which we have dominion.",
        "Meditation is not evasion; it is a serene encounter with reality.",
        "Your mind is a garden. Your thoughts are the seeds."
    ]
    
    private let wellnessTips = [
        "Take three deep breaths before starting any important task",
        "Practice gratitude by writing down three things you're thankful for",
        "Step outside for fresh air and natural light",
        "Stay hydrated by drinking water regularly throughout the day",
        "Take short breaks every hour to stretch and reset"
    ]
    
    func getRandomMotivationalQuote() -> String {
        return motivationalQuotes.randomElement() ?? motivationalQuotes[0]
    }
    
    func getRandomWellnessTip() -> String {
        return wellnessTips.randomElement() ?? wellnessTips[0]
    }
}

@MainActor
class NotificationPersonalizer {
    func personalizeContent(
        template: NotificationTemplate,
        data: [String: Any],
        profile: PersonalizationProfile?
    ) async -> PersonalizedContent {
        
        var personalizedTitle = template.title
        var personalizedBody = template.body
        
        // Apply personalization data
        for (key, value) in data {
            let placeholder = "{\(key)}"
            personalizedTitle = personalizedTitle.replacingOccurrences(of: placeholder, with: String(describing: value))
            personalizedBody = personalizedBody.replacingOccurrences(of: placeholder, with: String(describing: value))
        }
        
        // Apply profile-based personalization
        if let profile = profile {
            if let userName = profile.userName {
                personalizedTitle = personalizedTitle.replacingOccurrences(of: "{userName}", with: userName)
                personalizedBody = personalizedBody.replacingOccurrences(of: "{userName}", with: userName)
            }
            
            personalizedTitle = personalizedTitle.replacingOccurrences(of: "{preferredTime}", with: profile.preferredReminderTime)
            personalizedBody = personalizedBody.replacingOccurrences(of: "{duration}", with: String(profile.preferredSessionDuration))
        }
        
        // Apply dynamic content based on template type
        switch template.type {
        case .motivation:
            let quote = NotificationContentGenerator().getRandomMotivationalQuote()
            personalizedBody = personalizedBody.replacingOccurrences(of: "{motivationalQuote}", with: quote)
            
        case .educational:
            let tip = NotificationContentGenerator().getRandomWellnessTip()
            personalizedBody = personalizedBody.replacingOccurrences(of: "{tip}", with: tip)
            
        default:
            break
        }
        
        return PersonalizedContent(
            title: personalizedTitle,
            body: personalizedBody,
            subtitle: template.subtitle
        )
    }
}

@MainActor
class IntelligentScheduler {
    func calculateOptimalDeliveryTime(
        for type: NotificationType,
        userProfile: PersonalizationProfile?
    ) async -> Date {
        
        let calendar = Calendar.current
        let now = Date()
        
        // Default optimal times based on notification type
        let optimalHour: Int
        switch type {
        case .welcome:
            optimalHour = 10 // Mid-morning
        case .reminder:
            optimalHour = Int(userProfile?.preferredReminderTime.prefix(2) ?? "09") ?? 9
        case .achievement:
            optimalHour = 12 // Lunch time for positive reinforcement
        case .motivation:
            optimalHour = 8 // Morning motivation
        case .educational:
            optimalHour = 15 // Afternoon learning
        case .social:
            optimalHour = 18 // Evening social time
        case .system:
            optimalHour = 11 // Late morning for system notifications
        }
        
        // Calculate next occurrence of optimal time
        var optimalDate = calendar.date(bySettingHour: optimalHour, minute: 0, second: 0, of: now) ?? now
        
        // If the time has passed today, schedule for tomorrow
        if optimalDate <= now {
            optimalDate = calendar.date(byAdding: .day, value: 1, to: optimalDate) ?? optimalDate
        }
        
        return optimalDate
    }
}