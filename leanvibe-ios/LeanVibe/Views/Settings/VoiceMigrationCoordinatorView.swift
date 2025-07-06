import SwiftUI
import Combine

/// Administrative view for managing voice service migration
/// Allows testing and controlling the gradual migration from legacy services to UnifiedVoiceService
@available(iOS 18.0, macOS 14.0, *)
struct VoiceMigrationCoordinatorView: View {
    @StateObject private var voiceFactory = VoiceManagerFactory()
    @State private var showingMigrationDetails = false
    @State private var isPerformingMigration = false
    @State private var lastMigrationTime: Date?
    
    var body: some View {
        NavigationView {
            VStack(spacing: 20) {
                // Header
                VStack(spacing: 8) {
                    Image(systemName: "waveform.path.ecg")
                        .font(.largeTitle)
                        .foregroundColor(.blue)
                    
                    Text("Voice Service Migration")
                        .font(.title2)
                        .fontWeight(.semibold)
                    
                    Text("Manage the transition to UnifiedVoiceService")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                .padding(.top)
                
                // Current Status Card
                CurrentStatusCard(
                    isUnified: voiceFactory.isUsingUnifiedService,
                    migrationStatus: voiceFactory.migrationStatus
                )
                
                // Migration Controls
                VStack(spacing: 16) {
                    if voiceFactory.canMigrate {
                        MigrationButton(
                            title: "Migrate to Unified Service",
                            systemImage: "arrow.up.circle.fill",
                            color: .green,
                            isLoading: isPerformingMigration
                        ) {
                            await performMigration()
                        }
                    }
                    
                    if voiceFactory.canFallback {
                        MigrationButton(
                            title: "Fallback to Legacy Services",
                            systemImage: "arrow.down.circle.fill",
                            color: .orange,
                            isLoading: isPerformingMigration
                        ) {
                            await performFallback()
                        }
                    }
                    
                    MigrationButton(
                        title: "Reset All Services",
                        systemImage: "arrow.clockwise.circle.fill",
                        color: .blue,
                        isLoading: isPerformingMigration
                    ) {
                        await resetServices()
                    }
                }
                .disabled(isPerformingMigration)
                
                // Service Details
                ServiceDetailsView(voiceFactory: voiceFactory)
                
                Spacer()
                
                // Footer
                if let lastTime = lastMigrationTime {
                    Text("Last action: \\(lastTime.formatted(date: .omitted, time: .shortened))")
                        .font(.caption2)
                        .foregroundColor(.secondary)
                }
            }
            .padding()
            .navigationTitle("Voice Migration")
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
                MigrationDetailsView(voiceFactory: voiceFactory)
            }
        }
    }
    
    // MARK: - Migration Actions
    
    private func performMigration() async {
        isPerformingMigration = true
        defer { isPerformingMigration = false }
        
        await voiceFactory.migrateToUnifiedService()
        lastMigrationTime = Date()
    }
    
    private func performFallback() async {
        isPerformingMigration = true
        defer { isPerformingMigration = false }
        
        await voiceFactory.fallbackToLegacyServices()
        lastMigrationTime = Date()
    }
    
    private func resetServices() async {
        isPerformingMigration = true
        defer { isPerformingMigration = false }
        
        await voiceFactory.resetAllServices()
        lastMigrationTime = Date()
    }
}

// MARK: - Supporting Views

@available(iOS 18.0, macOS 14.0, *)
struct CurrentStatusCard: View {
    let isUnified: Bool
    let migrationStatus: MigrationStatus
    
    var body: some View {
        VStack(spacing: 12) {
            HStack {
                Image(systemName: isUnified ? "checkmark.seal.fill" : "exclamationmark.triangle.fill")
                    .foregroundColor(migrationStatus.color)
                
                VStack(alignment: .leading, spacing: 4) {
                    Text(isUnified ? "Unified Service Active" : "Legacy Services Active")
                        .font(.headline)
                        .foregroundColor(.primary)
                    
                    Text(migrationStatus.displayText)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                
                Spacer()
            }
            
            // Status indicator
            HStack {
                Text("Status:")
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                Spacer()
                
                Text(migrationStatus.rawValue)
                    .font(.caption)
                    .fontWeight(.medium)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(migrationStatus.color.opacity(0.2))
                    .foregroundColor(migrationStatus.color)
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
}

@available(iOS 18.0, macOS 14.0, *)
struct MigrationButton: View {
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
struct ServiceDetailsView: View {
    @ObservedObject var voiceFactory: VoiceManagerFactory
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Service Information")
                .font(.headline)
                .padding(.bottom, 4)
            
            if voiceFactory.isUsingUnifiedService {
                ServiceDetailRow(
                    title: "Unified Voice Service",
                    value: "Active",
                    color: .green
                )
                
                if let unifiedService = voiceFactory.unifiedVoiceService {
                    ServiceDetailRow(
                        title: "Current State",
                        value: unifiedService.currentStateText,
                        color: .blue
                    )
                    
                    ServiceDetailRow(
                        title: "Can Start Commands",
                        value: unifiedService.canStartVoiceCommand ? "Yes" : "No",
                        color: unifiedService.canStartVoiceCommand ? .green : .orange
                    )
                }
            } else {
                ServiceDetailRow(
                    title: "Legacy Voice Manager",
                    value: voiceFactory.legacyVoiceManager != nil ? "Active" : "Inactive",
                    color: voiceFactory.legacyVoiceManager != nil ? .green : .red
                )
                
                ServiceDetailRow(
                    title: "Global Voice Manager",
                    value: voiceFactory.globalVoiceManager != nil ? "Active" : "Inactive",
                    color: voiceFactory.globalVoiceManager != nil ? .green : .red
                )
                
                ServiceDetailRow(
                    title: "Optimized Voice Manager",
                    value: voiceFactory.optimizedVoiceManager != nil ? "Active" : "Inactive",
                    color: voiceFactory.optimizedVoiceManager != nil ? .green : .red
                )
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
struct MigrationDetailsView: View {
    @ObservedObject var voiceFactory: VoiceManagerFactory
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            VStack(alignment: .leading, spacing: 16) {
                Text("Migration Details")
                    .font(.title2)
                    .fontWeight(.semibold)
                
                VStack(alignment: .leading, spacing: 8) {
                    Text("Feature Flag Configuration")
                        .font(.headline)
                    
                    Text("USE_UNIFIED_VOICE_SERVICE: \(AppConfiguration.shared.useUnifiedVoiceService ? "true" : "false")")
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
                    Text("Migration Benefits")
                        .font(.headline)
                    
                    FeatureBenefitRow(
                        icon: "checkmark.circle.fill",
                        title: "Memory Safety",
                        description: "Eliminates nonisolated(unsafe) properties"
                    )
                    
                    FeatureBenefitRow(
                        icon: "checkmark.circle.fill", 
                        title: "Audio Coordination",
                        description: "Central audio session management"
                    )
                    
                    FeatureBenefitRow(
                        icon: "checkmark.circle.fill",
                        title: "State Management",
                        description: "Unified voice state machine"
                    )
                    
                    FeatureBenefitRow(
                        icon: "checkmark.circle.fill",
                        title: "Error Handling",
                        description: "Comprehensive error recovery"
                    )
                }
                
                Spacer()
            }
            .padding()
            .navigationTitle("Migration Info")
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