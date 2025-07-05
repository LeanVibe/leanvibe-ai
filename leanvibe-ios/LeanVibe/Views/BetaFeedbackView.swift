import SwiftUI

/// Beta feedback collection view for TestFlight users
/// Provides easy way for beta testers to submit feedback, bug reports, and suggestions
@available(iOS 18.0, macOS 14.0, *)
struct BetaFeedbackView: View {
    @ObservedObject private var analytics = BetaAnalyticsService.shared
    @Environment(\.dismiss) private var dismiss
    
    @State private var feedbackType: BetaFeedbackType = .general
    @State private var feedbackMessage: String = ""
    @State private var rating: Int = 5
    @State private var currentScreen: String = ""
    @State private var showThankYou = false
    @State private var isSubmitting = false
    
    var body: some View {
        Form {
                Section("Feedback Type") {
                    Picker("Type", selection: $feedbackType) {
                        ForEach(BetaFeedbackType.allCases, id: \.self) { type in
                            Text(type.displayName)
                                .tag(type)
                        }
                    }
                    .pickerStyle(.menu)
                }
                
                Section("Your Feedback") {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Tell us about your experience:")
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                        
                        TextEditor(text: $feedbackMessage)
                            .frame(minHeight: 100)
                            .padding(8)
                            .background(Color(UIColor.systemGray6))
                            .cornerRadius(8)
                    }
                    
                    HStack {
                        Text("Current Screen:")
                        TextField("Screen name", text: $currentScreen)
                            .textFieldStyle(.roundedBorder)
                    }
                }
                
                if feedbackType == .general {
                    Section("Overall Rating") {
                        HStack {
                            Text("Rate your experience:")
                            Spacer()
                            HStack(spacing: 4) {
                                ForEach(1...5, id: \.self) { star in
                                    Button(action: {
                                        rating = star
                                    }) {
                                        Image(systemName: star <= rating ? "star.fill" : "star")
                                            .foregroundColor(star <= rating ? .yellow : .gray)
                                            .font(.title2)
                                    }
                                }
                            }
                        }
                    }
                }
                
                Section("Beta Testing Info") {
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Text("App Version:")
                            Spacer()
                            Text(Bundle.main.appVersionLong)
                                .foregroundColor(.secondary)
                        }
                        
                        HStack {
                            Text("Device:")
                            Spacer()
                            Text("\(UIDevice.current.model) - iOS \(UIDevice.current.systemVersion)")
                                .foregroundColor(.secondary)
                        }
                        
                        HStack {
                            Text("Build Date:")
                            Spacer()
                            Text(Date().formatted(.dateTime.month().day().year()))
                                .foregroundColor(.secondary)
                        }
                    }
                    .font(.caption)
                }
                
                Section("Privacy Notice") {
                    VStack(alignment: .leading, spacing: 8) {
                        Label("Your Privacy is Protected", systemImage: "lock.shield")
                            .font(.subheadline)
                            .foregroundColor(.green)
                        
                        Text("Feedback is stored locally and only shared anonymously to improve the app. No personal information is collected.")
                            .font(.caption)
                            .foregroundColor(.secondary)
                            .fixedSize(horizontal: false, vertical: true)
                    }
                }
            }
            .navigationTitle("Beta Feedback")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
                
                ToolbarItem(placement: .confirmationAction) {
                    Button("Submit") {
                        submitFeedback()
                    }
                    .disabled(feedbackMessage.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || isSubmitting)
                }
            }
        }
        .onAppear {
            analytics.recordUsageMetric(
                event: .screenView,
                screen: "beta_feedback"
            )
        }
        .alert("Thank You!", isPresented: $showThankYou) {
            Button("Close") {
                dismiss()
            }
        } message: {
            Text("Your feedback has been recorded and will help improve the app. Thank you for participating in our beta test!")
        }
    }
    
    private func submitFeedback() {
        guard !feedbackMessage.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return }
        
        isSubmitting = true
        
        // Add a small delay to show the submitting state
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            analytics.recordFeedback(
                type: feedbackType,
                screen: currentScreen.isEmpty ? "unknown" : currentScreen,
                message: feedbackMessage,
                rating: feedbackType == .general ? rating : nil,
                metadata: [
                    "device_model": UIDevice.current.model,
                    "ios_version": UIDevice.current.systemVersion,
                    "app_version": Bundle.main.appVersionLong
                ]
            )
            
            isSubmitting = false
            showThankYou = true
            
            // Track feedback submission
            analytics.recordUsageMetric(
                event: .featureUsed,
                screen: "beta_feedback",
                metadata: ["feedback_type": feedbackType.rawValue]
            )
        }
    }
}

// MARK: - Beta Analytics Dashboard

@available(iOS 18.0, macOS 14.0, *)
struct BetaAnalyticsDashboardView: View {
    @ObservedObject private var analytics = BetaAnalyticsService.shared
    @State private var showingExportAlert = false
    @State private var exportData: String = ""
    
    var body: some View {
        NavigationView {
            List {
                Section("Analytics Status") {
                    HStack {
                        Label("Beta Analytics", systemImage: "chart.bar.doc.horizontal")
                        Spacer()
                        Toggle("", isOn: Binding(
                            get: { analytics.isEnabled },
                            set: { analytics.setAnalyticsEnabled($0) }
                        ))
                    }
                    
                    if analytics.isEnabled {
                        Label("Data collection active", systemImage: "checkmark.circle.fill")
                            .foregroundColor(.green)
                    } else {
                        Label("Data collection disabled", systemImage: "xmark.circle.fill")
                            .foregroundColor(.red)
                    }
                }
                
                if analytics.isEnabled {
                    Section("Current Data") {
                        HStack {
                            Text("Feedback Items:")
                            Spacer()
                            Text("\(analytics.feedbackQueue.count)")
                                .foregroundColor(.secondary)
                        }
                        
                        HStack {
                            Text("Usage Events:")
                            Spacer()
                            Text("\(analytics.usageMetrics.count)")
                                .foregroundColor(.secondary)
                        }
                        
                        HStack {
                            Text("Crash Reports:")
                            Spacer()
                            Text("\(analytics.crashReports.count)")
                                .foregroundColor(.secondary)
                        }
                    }
                    
                    Section("Recent Feedback") {
                        if analytics.feedbackQueue.isEmpty {
                            Text("No feedback yet")
                                .foregroundColor(.secondary)
                        } else {
                            ForEach(analytics.feedbackQueue.suffix(5).reversed(), id: \.id) { feedback in
                                VStack(alignment: .leading, spacing: 4) {
                                    HStack {
                                        Text(feedback.type.displayName)
                                            .font(.caption)
                                            .padding(.horizontal, 8)
                                            .padding(.vertical, 2)
                                            .background(Color(feedback.type.color))
                                            .foregroundColor(.white)
                                            .cornerRadius(4)
                                        
                                        Spacer()
                                        
                                        Text(feedback.timestamp.formatted(.relative(presentation: .named)))
                                            .font(.caption)
                                            .foregroundColor(.secondary)
                                    }
                                    
                                    Text(feedback.message)
                                        .font(.body)
                                        .lineLimit(2)
                                    
                                    if let rating = feedback.rating {
                                        HStack {
                                            ForEach(1...5, id: \.self) { star in
                                                Image(systemName: star <= rating ? "star.fill" : "star")
                                                    .foregroundColor(star <= rating ? .yellow : .gray)
                                                    .font(.caption)
                                            }
                                        }
                                    }
                                }
                                .padding(.vertical, 4)
                            }
                        }
                    }
                    
                    Section("Actions") {
                        Button(action: {
                            if let data = analytics.exportBetaDataAsJSON() {
                                exportData = data
                                showingExportAlert = true
                            }
                        }) {
                            Label("Export Data", systemImage: "square.and.arrow.up")
                        }
                        
                        Button(action: {
                            analytics.clearAllData()
                        }) {
                            Label("Clear All Data", systemImage: "trash")
                                .foregroundColor(.red)
                        }
                    }
                }
            }
            .navigationTitle("Beta Analytics")
            .alert("Export Data", isPresented: $showingExportAlert) {
                Button("Copy to Clipboard") {
                    UIPasteboard.general.string = exportData
                }
                Button("Cancel", role: .cancel) { }
            } message: {
                Text("Beta analytics data has been prepared for export. You can copy it to clipboard and share with the development team.")
            }
        }
    }
}

// MARK: - Extensions

extension BetaFeedbackType {
    var displayName: String {
        switch self {
        case .bug:
            return "Bug Report"
        case .featureRequest:
            return "Feature Request"
        case .usability:
            return "Usability Issue"
        case .general:
            return "General Feedback"
        case .performance:
            return "Performance Issue"
        }
    }
    
    var color: UIColor {
        switch self {
        case .bug:
            return .systemRed
        case .featureRequest:
            return .systemBlue
        case .usability:
            return .systemOrange
        case .general:
            return .systemGreen
        case .performance:
            return .systemPurple
        }
    }
}

// MARK: - Preview

@available(iOS 18.0, macOS 14.0, *)
struct BetaFeedbackView_Previews: PreviewProvider {
    static var previews: some View {
        BetaFeedbackView()
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct BetaAnalyticsDashboardView_Previews: PreviewProvider {
    static var previews: some View {
        BetaAnalyticsDashboardView()
    }
}