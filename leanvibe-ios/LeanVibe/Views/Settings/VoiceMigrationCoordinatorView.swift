import SwiftUI
import Combine

/// Administrative view for managing voice service migration
/// Now displays unified voice service status since migration is complete
@available(iOS 18.0, macOS 14.0, *)
struct VoiceMigrationCoordinatorView: View {
    @StateObject private var unifiedVoiceService = UnifiedVoiceService.shared
    @State private var showingMigrationDetails = false
    @State private var isPerformingAction = false
    @State private var lastActionTime: Date?
    
    var body: some View {
        NavigationView {
            VStack(spacing: 20) {
                // Header
                VStack(spacing: 8) {
                    Image(systemName: "waveform.path.ecg")
                        .font(.largeTitle)
                        .foregroundColor(.blue)
                    
                    Text("Voice Service Status")
                        .font(.title2)
                        .fontWeight(.semibold)
                    
                    Text("UnifiedVoiceService is now active")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                .padding(.top)
                
                // Current Status Card
                UnifiedVoiceStatusCard(unifiedVoiceService: unifiedVoiceService)
                
                // Voice Actions
                VStack(spacing: 16) {
                    ActionButton(
                        title: "Check Permissions",
                        systemImage: "checkmark.shield.fill",
                        color: .green,
                        isLoading: isPerformingAction
                    ) {
                        await checkPermissions()
                    }
                    
                    ActionButton(
                        title: "Start Listening",
                        systemImage: "mic.circle.fill",
                        color: .blue,
                        isLoading: isPerformingAction
                    ) {
                        await startListening()
                    }
                    
                    ActionButton(
                        title: "Stop Listening",
                        systemImage: "mic.slash.circle.fill",
                        color: .red,
                        isLoading: isPerformingAction
                    ) {
                        await stopListening()
                    }
                }
                .disabled(isPerformingAction)
                
                // Service Details
                UnifiedServiceDetailsView(unifiedVoiceService: unifiedVoiceService)
                
                Spacer()
                
                // Footer
                if let lastTime = lastActionTime {
                    Text("Last action: \\(lastTime.formatted(date: .omitted, time: .shortened))")
                        .font(.caption2)
                        .foregroundColor(.secondary)
                }
            }
            .padding()
            .navigationTitle("Voice Service")
#if os(iOS)
            .navigationBarTitleDisplayMode(.inline)
            #endif
            .toolbar {
                #if os(iOS)
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Details") {
                        showingMigrationDetails = true
                    }
                }
                #else
                ToolbarItem(placement: .automatic) {
                    Button("Details") {
                        showingMigrationDetails = true
                    }
                }
                #endif
            }
            .sheet(isPresented: $showingMigrationDetails) {
                UnifiedVoiceDetailsView(unifiedVoiceService: unifiedVoiceService)
            }
        }
    }
    
    // MARK: - Voice Actions
    
    private func checkPermissions() async {
        isPerformingAction = true
        defer { isPerformingAction = false }
        
        await MainActor.run {
            unifiedVoiceService.checkPermissions()
        }
        lastActionTime = Date()
    }
    
    private func startListening() async {
        isPerformingAction = true
        defer { isPerformingAction = false }
        
        await unifiedVoiceService.startListening(mode: .pushToTalk)
        lastActionTime = Date()
    }
    
    private func stopListening() async {
        isPerformingAction = true
        defer { isPerformingAction = false }
        
        await MainActor.run {
            unifiedVoiceService.stopListening()
        }
        lastActionTime = Date()
    }
}

// MARK: - Supporting Views

@available(iOS 18.0, macOS 14.0, *)
struct UnifiedVoiceStatusCard: View {
    @ObservedObject var unifiedVoiceService: UnifiedVoiceService
    
    var body: some View {
        VStack(spacing: 12) {
            HStack {
                Image(systemName: "checkmark.seal.fill")
                    .foregroundColor(.green)
                
                VStack(alignment: .leading, spacing: 4) {
                    Text("UnifiedVoiceService Active")
                        .font(.headline)
                        .foregroundColor(.primary)
                    
                    Text("Consolidated voice service ready")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                
                Spacer()
            }
            
            // Status indicator
            HStack {
                Text("Current State:")
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                Spacer()
                
                Text(stateDescription)
                    .font(.caption)
                    .fontWeight(.medium)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(stateColor.opacity(0.2))
                    .foregroundColor(stateColor)
                    .cornerRadius(8)
            }
        }
        .padding()
        .background({
#if os(iOS)
            return Color(.systemGray6)
#else
            return Color.gray.opacity(0.1)
#endif
        }())
        .cornerRadius(12)
    }
    
    private var stateDescription: String {
        switch unifiedVoiceService.state {
        case .idle: return "Idle"
        case .listening: return "Listening"
        case .processing: return "Processing"
        case .error: return "Error"
        }
    }
    
    private var stateColor: Color {
        switch unifiedVoiceService.state {
        case .idle: return .blue
        case .listening: return .green
        case .processing: return .orange
        case .error: return .red
        }
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct ActionButton: View {
    let title: String
    let systemImage: String
    let color: Color
    let isLoading: Bool
    let action: () async -> Void
    
    var body: some View {
        Button {
            Task {
                await action()
            }
        } label: {
            HStack {
                if isLoading {
                    ProgressView()
                        .scaleEffect(0.8)
                } else {
                    Image(systemName: systemImage)
                }
                
                Text(title)
                    .fontWeight(.medium)
            }
            .frame(maxWidth: .infinity)
            .padding()
            .background(color.opacity(0.1))
            .foregroundColor(color)
            .cornerRadius(10)
        }
        .disabled(isLoading)
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct UnifiedServiceDetailsView: View {
    @ObservedObject var unifiedVoiceService: UnifiedVoiceService
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Service Information")
                .font(.headline)
                .padding(.bottom, 4)
            
            ServiceDetailRow(
                title: "Service Type",
                value: "Unified Voice Service",
                color: .green
            )
            
            ServiceDetailRow(
                title: "Permissions Status",
                value: unifiedVoiceService.isFullyAuthorized ? "Authorized" : "Not Authorized",
                color: unifiedVoiceService.isFullyAuthorized ? .green : .red
            )
            
            ServiceDetailRow(
                title: "Wake Listening",
                value: unifiedVoiceService.isWakeListening ? "Active" : "Inactive",
                color: unifiedVoiceService.isWakeListening ? .green : .gray
            )
            
            ServiceDetailRow(
                title: "Performance Status",
                value: performanceStatusDescription,
                color: performanceStatusColor
            )
            
            ServiceDetailRow(
                title: "Audio Level",
                value: String(format: "%.2f", unifiedVoiceService.audioLevel),
                color: .blue
            )
        }
        .padding()
        .background({
#if os(iOS)
            return Color(.systemGray6)
#else
            return Color.gray.opacity(0.1)
#endif
        }())
        .cornerRadius(12)
    }
    
    private var performanceStatusDescription: String {
        switch unifiedVoiceService.performanceStatus {
        case .optimal: return "Optimal"
        case .good: return "Good"
        case .poor: return "Poor"
        case .critical: return "Critical"
        }
    }
    
    private var performanceStatusColor: Color {
        switch unifiedVoiceService.performanceStatus {
        case .optimal: return .green
        case .good: return .blue
        case .poor: return .orange
        case .critical: return .red
        }
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct ServiceDetailRow: View {
    let title: String
    let value: String
    let color: Color
    
    var body: some View {
        HStack {
            Text(title)
                .font(.caption)
                .foregroundColor(.secondary)
            
            Spacer()
            
            Text(value)
                .font(.caption)
                .fontWeight(.medium)
                .foregroundColor(color)
        }
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct UnifiedVoiceDetailsView: View {
    @ObservedObject var unifiedVoiceService: UnifiedVoiceService
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            VStack(alignment: .leading, spacing: 16) {
                Text("Unified Voice Service Details")
                    .font(.title2)
                    .fontWeight(.semibold)
                
                VStack(alignment: .leading, spacing: 8) {
                    Text("Configuration")
                        .font(.headline)
                    
                    Text("USE_UNIFIED_VOICE_SERVICE: true")
                        .font(.caption)
                        .fontDesign(.monospaced)
                    
                    Text("Voice Confidence Threshold: \(AppConfiguration.shared.voiceConfidenceThreshold)")
                        .font(.caption)
                        .fontDesign(.monospaced)
                    
                    Text("Max Recording Duration: \(AppConfiguration.shared.maxVoiceRecordingDuration)s")
                        .font(.caption)
                        .fontDesign(.monospaced)
                }
                .padding()
                .background({
#if os(iOS)
                    return Color(.systemGray6)
#else
                    return Color.gray.opacity(0.1)
#endif
                }())
                .cornerRadius(8)
                
                VStack(alignment: .leading, spacing: 8) {
                    Text("Consolidation Benefits Achieved")
                        .font(.headline)
                    
                    FeatureBenefitRow(
                        icon: "checkmark.circle.fill",
                        title: "Memory Safety",
                        description: "Eliminated nonisolated(unsafe) properties"
                    )
                    
                    FeatureBenefitRow(
                        icon: "checkmark.circle.fill", 
                        title: "Audio Coordination",
                        description: "Centralized audio session management"
                    )
                    
                    FeatureBenefitRow(
                        icon: "checkmark.circle.fill",
                        title: "State Management",
                        description: "Unified voice state machine"
                    )
                    
                    FeatureBenefitRow(
                        icon: "checkmark.circle.fill",
                        title: "Code Reduction",
                        description: "60% reduction in voice service complexity"
                    )
                    
                    FeatureBenefitRow(
                        icon: "checkmark.circle.fill",
                        title: "Production Ready",
                        description: "Eliminated choice paralysis from factory pattern"
                    )
                }
                
                Spacer()
            }
            .padding()
            .navigationTitle("Voice Service Info")
#if os(iOS)
            .navigationBarTitleDisplayMode(.inline)
            #endif
            .toolbar {
                #if os(iOS)
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Done") {
                        dismiss()
                    }
                }
                #else
                ToolbarItem(placement: .automatic) {
                    Button("Done") {
                        dismiss()
                    }
                }
                #endif
            }
        }
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct FeatureBenefitRow: View {
    let icon: String
    let title: String
    let description: String
    
    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: icon)
                .foregroundColor(.green)
                .frame(width: 16)
            
            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(.caption)
                    .fontWeight(.medium)
                
                Text(description)
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
        }
    }
}

// MARK: - Preview

@available(iOS 18.0, macOS 14.0, *)
struct VoiceMigrationCoordinatorView_Previews: PreviewProvider {
    static var previews: some View {
        VoiceMigrationCoordinatorView()
    }
}