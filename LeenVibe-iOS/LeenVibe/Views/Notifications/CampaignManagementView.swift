import SwiftUI

/// Campaign Management View - Create and manage notification campaigns
@available(iOS 18.0, macOS 14.0, *)
struct CampaignManagementView: View {
    @ObservedObject var contentManager: NotificationContentManager
    
    @State private var showingCreateCampaign = false
    @State private var showingCampaignDetail = false
    @State private var selectedCampaign: NotificationCampaign?
    
    var body: some View {
        List {
            // Active Campaigns Section
            Section("Active Campaigns") {
                if contentManager.scheduledCampaigns.filter({ $0.status == .active }).isEmpty {
                    EmptyStateRow(
                        icon: "calendar",
                        message: "No active campaigns"
                    )
                } else {
                    ForEach(contentManager.scheduledCampaigns.filter { $0.status == .active }) { campaign in
                        CampaignRow(campaign: campaign) {
                            selectedCampaign = campaign
                            showingCampaignDetail = true
                        }
                    }
                }
            }
            
            // Draft & Completed Campaigns
            Section("Other Campaigns") {
                ForEach(contentManager.scheduledCampaigns.filter { $0.status != .active }) { campaign in
                    CampaignRow(campaign: campaign) {
                        selectedCampaign = campaign
                        showingCampaignDetail = true
                    }
                }
            }
        }
        .navigationTitle("Campaigns")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .navigationBarTrailing) {
                Button {
                    showingCreateCampaign = true
                } label: {
                    Image(systemName: "plus")
                }
            }
        }
        .sheet(isPresented: $showingCreateCampaign) {
            CreateCampaignView(contentManager: contentManager)
        }
        .sheet(item: $selectedCampaign) { campaign in
            CampaignDetailView(
                campaign: campaign,
                contentManager: contentManager
            )
        }
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct CampaignRow: View {
    let campaign: NotificationCampaign
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Text(campaign.name)
                        .font(.headline)
                        .foregroundColor(.primary)
                    
                    Spacer()
                    
                    CampaignStatusBadge(status: campaign.status)
                }
                
                Text(campaign.description)
                    .font(.body)
                    .foregroundColor(.secondary)
                    .lineLimit(2)
                
                HStack {
                    Label(formatDate(campaign.startDate), systemImage: "calendar")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    
                    Spacer()
                    
                    Text("\(campaign.schedule.count) notifications")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
            .padding(.vertical, 4)
        }
        .buttonStyle(PlainButtonStyle())
    }
    
    private func formatDate(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        return formatter.string(from: date)
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct CampaignStatusBadge: View {
    let status: CampaignStatus
    
    var body: some View {
        Text(status.rawValue.capitalized)
            .font(.caption2)
            .fontWeight(.semibold)
            .foregroundColor(textColor)
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(backgroundColor)
            .clipShape(Capsule())
    }
    
    private var textColor: Color {
        switch status {
        case .draft:
            return .gray
        case .active:
            return .green
        case .paused:
            return .orange
        case .completed:
            return .blue
        case .cancelled:
            return .red
        }
    }
    
    private var backgroundColor: Color {
        switch status {
        case .draft:
            return .gray.opacity(0.1)
        case .active:
            return .green.opacity(0.1)
        case .paused:
            return .orange.opacity(0.1)
        case .completed:
            return .blue.opacity(0.1)
        case .cancelled:
            return .red.opacity(0.1)
        }
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct EmptyStateRow: View {
    let icon: String
    let message: String
    
    var body: some View {
        HStack {
            Image(systemName: icon)
                .foregroundColor(.secondary)
            
            Text(message)
                .foregroundColor(.secondary)
            
            Spacer()
        }
        .padding(.vertical, 8)
    }
}

// MARK: - Create Campaign View

@available(iOS 18.0, macOS 14.0, *)
struct CreateCampaignView: View {
    @ObservedObject var contentManager: NotificationContentManager
    @Environment(\.dismiss) private var dismiss
    
    @State private var campaignName = ""
    @State private var campaignDescription = ""
    @State private var startDate = Date()
    @State private var endDate = Calendar.current.date(byAdding: .day, value: 7, to: Date()) ?? Date()
    @State private var selectedTemplates: [String] = []
    @State private var isCreating = false
    
    var body: some View {
        NavigationView {
            Form {
                Section("Campaign Details") {
                    TextField("Campaign Name", text: $campaignName)
                    TextField("Description", text: $campaignDescription, axis: .vertical)
                        .lineLimit(3)
                }
                
                Section("Schedule") {
                    DatePicker("Start Date", selection: $startDate, displayedComponents: [.date, .hourAndMinute])
                    DatePicker("End Date", selection: $endDate, displayedComponents: [.date, .hourAndMinute])
                }
                
                Section("Notification Templates") {
                    ForEach(contentManager.contentTemplates) { template in
                        TemplateSelectionRow(
                            template: template,
                            isSelected: selectedTemplates.contains(template.id)
                        ) {
                            if selectedTemplates.contains(template.id) {
                                selectedTemplates.removeAll { $0 == template.id }
                            } else {
                                selectedTemplates.append(template.id)
                            }
                        }
                    }
                }
            }
            .navigationTitle("Create Campaign")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
                
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Create") {
                        Task {
                            await createCampaign()
                        }
                    }
                    .disabled(campaignName.isEmpty || selectedTemplates.isEmpty || isCreating)
                }
            }
        }
    }
    
    private func createCampaign() async {
        isCreating = true
        
        let schedule = selectedTemplates.enumerated().map { index, templateId in
            CampaignScheduleItem(
                templateId: templateId,
                offsetDays: index,
                preferredTime: "09:00"
            )
        }
        
        let campaign = NotificationCampaign(
            id: "custom_\(UUID().uuidString)",
            name: campaignName,
            description: campaignDescription,
            startDate: startDate,
            endDate: endDate,
            schedule: schedule
        )
        
        let success = await contentManager.createNotificationCampaign(campaign)
        
        isCreating = false
        
        if success {
            dismiss()
        }
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct TemplateSelectionRow: View {
    let template: NotificationTemplate
    let isSelected: Bool
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(template.title)
                        .font(.headline)
                        .foregroundColor(.primary)
                    
                    Text(template.body)
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .lineLimit(2)
                    
                    HStack {
                        Text(template.type.rawValue.capitalized)
                            .font(.caption2)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 2)
                            .background(Color.blue.opacity(0.1))
                            .clipShape(Capsule())
                        
                        Text(template.priority.rawValue.capitalized)
                            .font(.caption2)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 2)
                            .background(priorityColor.opacity(0.1))
                            .clipShape(Capsule())
                    }
                }
                
                Spacer()
                
                if isSelected {
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundColor(.blue)
                }
            }
            .padding(.vertical, 4)
        }
        .buttonStyle(PlainButtonStyle())
    }
    
    private var priorityColor: Color {
        switch template.priority {
        case .low:
            return .green
        case .medium:
            return .orange
        case .high:
            return .red
        case .critical:
            return .purple
        }
    }
}

// MARK: - Campaign Detail View

@available(iOS 18.0, macOS 14.0, *)
struct CampaignDetailView: View {
    let campaign: NotificationCampaign
    @ObservedObject var contentManager: NotificationContentManager
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            List {
                Section("Campaign Information") {
                    DetailRow(title: "Name", value: campaign.name)
                    DetailRow(title: "Description", value: campaign.description)
                    DetailRow(title: "Status", value: campaign.status.rawValue.capitalized)
                    DetailRow(title: "Start Date", value: formatDate(campaign.startDate))
                    DetailRow(title: "End Date", value: formatDate(campaign.endDate))
                }
                
                Section("Schedule (\(campaign.schedule.count) notifications)") {
                    ForEach(Array(campaign.schedule.enumerated()), id: \.offset) { index, item in
                        ScheduleItemRow(item: item, index: index)
                    }
                }
                
                if campaign.status == .active {
                    Section("Actions") {
                        Button("Cancel Campaign") {
                            contentManager.cancelCampaign(withId: campaign.id)
                            dismiss()
                        }
                        .foregroundColor(.red)
                    }
                }
            }
            .navigationTitle("Campaign Details")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Done") {
                        dismiss()
                    }
                }
            }
        }
    }
    
    private func formatDate(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        formatter.timeStyle = .short
        return formatter.string(from: date)
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct DetailRow: View {
    let title: String
    let value: String
    
    var body: some View {
        HStack {
            Text(title)
                .foregroundColor(.secondary)
            Spacer()
            Text(value)
                .foregroundColor(.primary)
        }
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct ScheduleItemRow: View {
    let item: CampaignScheduleItem
    let index: Int
    
    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text("Day \(item.offsetDays + 1)")
                    .font(.headline)
                
                Spacer()
                
                if let time = item.preferredTime {
                    Text(time)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
            
            Text("Template: \(item.templateId)")
                .font(.caption)
                .foregroundColor(.secondary)
            
            if !item.personalizationData.isEmpty {
                Text("Personalized: \(item.personalizationData.keys.joined(separator: ", "))")
                    .font(.caption)
                    .foregroundColor(.blue)
            }
        }
        .padding(.vertical, 4)
    }
}

#Preview {
    NavigationView {
        CampaignManagementView(contentManager: NotificationContentManager(pushService: PushNotificationService()))
    }
}