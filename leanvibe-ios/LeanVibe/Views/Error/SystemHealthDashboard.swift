import SwiftUI
import Network

@available(iOS 18.0, macOS 14.0, *)
struct SystemHealthDashboard: View {
    @ObservedObject var errorManager = GlobalErrorManager.shared
    @ObservedObject var networkHandler = NetworkErrorHandler.shared
    @ObservedObject var serviceHandler = ServiceErrorHandler.shared
    @ObservedObject var recoveryManager = ErrorRecoveryManager.shared
    
    @State private var selectedCategory: ErrorCategory? = nil
    @State private var showingErrorHistory = false
    @State private var showingRecoveryHistory = false
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 20) {
                    // Overall System Status
                    systemStatusSection
                    
                    // Network Status
                    networkStatusSection
                    
                    // Service Health
                    serviceHealthSection
                    
                    // Recovery Status
                    recoveryStatusSection
                    
                    // Error Analytics
                    errorAnalyticsSection
                }
                .padding()
            }
            .navigationTitle("System Health")
            .navigationBarItems(trailing: Menu("Actions") {
                Button("Clear Error History") {
                    errorManager.clearHistory()
                }
                Button("Force Recovery") {
                    Task {
                        for serviceName in serviceHandler.getFailedCriticalServices() {
                            await serviceHandler.retryService(serviceName)
                        }
                    }
                }
                Button("Test Network") {
                    Task {
                        await networkHandler.checkConnectionQuality()
                    }
                }
            })
            .sheet(isPresented: $showingErrorHistory) {
                ErrorHistoryView(errorManager: errorManager)
            }
            .sheet(isPresented: $showingRecoveryHistory) {
                RecoveryHistoryView(recoveryManager: recoveryManager)
            }
        }
    }
    
    // MARK: - System Status Section
    
    private var systemStatusSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: overallSystemStatus.systemImage)
                    .foregroundColor(overallSystemStatus.color)
                    .font(.title2)
                
                Text("System Status")
                    .font(.headline)
                    .fontWeight(.semibold)
                
                Spacer()
                
                Text(overallSystemStatusText)
                    .font(.caption)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(overallSystemStatus.color.opacity(0.2))
                    .foregroundColor(overallSystemStatus.color)
                    .cornerRadius(8)
            }
            
            if errorManager.isInOfflineMode() {
                HStack {
                    Image(systemName: "wifi.slash")
                        .foregroundColor(.orange)
                    
                    Text("Offline Mode Enabled")
                        .font(.body)
                        .foregroundColor(.secondary)
                    
                    Spacer()
                    
                    Button("Go Online") {
                        Task {
                            await networkHandler.checkConnectionQuality()
                        }
                    }
                    .buttonStyle(.bordered)
                    .controlSize(.small)
                }
                .padding()
                .background(.orange.opacity(0.1))
                .cornerRadius(8)
            }
            
            if recoveryManager.isInRecoveryMode {
                HStack {
                    ProgressView()
                        .scaleEffect(0.8)
                    
                    Text("System Recovery in Progress")
                        .font(.body)
                        .foregroundColor(.secondary)
                    
                    Spacer()
                    
                    Text("\(recoveryManager.activeRecoveries.count) active")
                        .font(.caption)
                        .foregroundColor(.blue)
                }
                .padding()
                .background(.blue.opacity(0.1))
                .cornerRadius(8)
            }
        }
        .padding()
        .background(.regularMaterial)
        .cornerRadius(12)
    }
    
    // MARK: - Network Status Section
    
    private var networkStatusSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: networkHandler.networkStatus.systemImage)
                    .foregroundColor(networkHandler.networkStatus.color)
                    .font(.title2)
                
                Text("Network")
                    .font(.headline)
                    .fontWeight(.semibold)
                
                Spacer()
                
                if networkHandler.isConnected {
                    VStack(alignment: .trailing) {
                        Text(networkHandler.networkStatus.rawValue.capitalized)
                            .font(.caption)
                            .foregroundColor(networkHandler.networkStatus.color)
                        
                        if networkHandler.latency > 0 {
                            Text("\(Int(networkHandler.latency * 1000))ms")
                                .font(.caption2)
                                .foregroundColor(.secondary)
                        }
                    }
                }
            }
            
            if let connectionType = networkHandler.connectionType {
                HStack {
                    Image(systemName: connectionTypeIcon(connectionType))
                        .foregroundColor(.secondary)
                    
                    Text(connectionTypeText(connectionType))
                        .font(.body)
                        .foregroundColor(.secondary)
                    
                    Spacer()
                    
                    if networkHandler.isSlowConnection {
                        Text("Slow")
                            .font(.caption)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 2)
                            .background(.orange.opacity(0.2))
                            .foregroundColor(.orange)
                            .cornerRadius(4)
                    }
                }
            }
            
            let networkStats = networkHandler.getErrorStats()
            if networkStats.webSocketErrors > 0 || networkStats.restAPIErrors > 0 {
                HStack {
                    Text("Recent Errors:")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    
                    if networkStats.webSocketErrors > 0 {
                        Text("WebSocket: \(networkStats.webSocketErrors)")
                            .font(.caption)
                            .foregroundColor(.orange)
                    }
                    
                    if networkStats.restAPIErrors > 0 {
                        Text("API: \(networkStats.restAPIErrors)")
                            .font(.caption)
                            .foregroundColor(.red)
                    }
                    
                    Spacer()
                }
            }
        }
        .padding()
        .background(.regularMaterial)
        .cornerRadius(12)
    }
    
    // MARK: - Service Health Section
    
    private var serviceHealthSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "server.rack")
                    .foregroundColor(.blue)
                    .font(.title2)
                
                Text("Services")
                    .font(.headline)
                    .fontWeight(.semibold)
                
                Spacer()
                
                if !serviceHandler.failedServices.isEmpty {
                    Text("\(serviceHandler.failedServices.count) failed")
                        .font(.caption)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(.red.opacity(0.2))
                        .foregroundColor(.red)
                        .cornerRadius(4)
                } else if !serviceHandler.degradedServices.isEmpty {
                    Text("\(serviceHandler.degradedServices.count) degraded")
                        .font(.caption)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(.orange.opacity(0.2))
                        .foregroundColor(.orange)
                        .cornerRadius(4)
                } else {
                    Text("All Healthy")
                        .font(.caption)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(.green.opacity(0.2))
                        .foregroundColor(.green)
                        .cornerRadius(4)
                }
            }
            
            ForEach(Array(serviceHandler.getAllServiceHealth().keys.sorted()), id: \.self) { serviceName in
                if let healthInfo = serviceHandler.getServiceHealth(serviceName) {
                    ServiceHealthRow(serviceName: serviceName, healthInfo: healthInfo)
                }
            }
        }
        .padding()
        .background(.regularMaterial)
        .cornerRadius(12)
    }
    
    // MARK: - Recovery Status Section
    
    private var recoveryStatusSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "arrow.clockwise")
                    .foregroundColor(.green)
                    .font(.title2)
                
                Text("Recovery")
                    .font(.headline)
                    .fontWeight(.semibold)
                
                Spacer()
                
                Button("History") {
                    showingRecoveryHistory = true
                }
                .font(.caption)
                .buttonStyle(.bordered)
                .controlSize(.mini)
            }
            
            let metrics = recoveryManager.getRecoveryMetrics()
            let successRate = recoveryManager.getRecoverySuccessRate()
            
            HStack {
                VStack(alignment: .leading) {
                    Text("Success Rate")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    
                    Text("\(Int(successRate * 100))%")
                        .font(.title3)
                        .fontWeight(.semibold)
                        .foregroundColor(successRate > 0.8 ? .green : successRate > 0.5 ? .orange : .red)
                }
                
                Spacer()
                
                VStack(alignment: .center) {
                    Text("Total")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    
                    Text("\(metrics.totalRecoveries)")
                        .font(.title3)
                        .fontWeight(.semibold)
                }
                
                Spacer()
                
                VStack(alignment: .trailing) {
                    Text("Avg Time")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    
                    Text("\(String(format: "%.1f", metrics.averageRecoveryTime))s")
                        .font(.title3)
                        .fontWeight(.semibold)
                }
            }
            
            if !recoveryManager.activeRecoveries.isEmpty {
                Divider()
                
                Text("Active Recoveries")
                    .font(.subheadline)
                    .fontWeight(.medium)
                
                ForEach(recoveryManager.activeRecoveries) { recovery in
                    ActiveRecoveryRow(recovery: recovery)
                }
            }
        }
        .padding()
        .background(.regularMaterial)
        .cornerRadius(12)
    }
    
    // MARK: - Error Analytics Section
    
    private var errorAnalyticsSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "chart.bar")
                    .foregroundColor(.purple)
                    .font(.title2)
                
                Text("Error Analytics")
                    .font(.headline)
                    .fontWeight(.semibold)
                
                Spacer()
                
                Button("History") {
                    showingErrorHistory = true
                }
                .font(.caption)
                .buttonStyle(.bordered)
                .controlSize(.mini)
            }
            
            let errorStats = errorManager.getErrorStats()
            
            if !errorStats.isEmpty {
                ForEach(Array(errorStats.sorted(by: { $0.value > $1.value })), id: \.key) { category, count in
                    HStack {
                        Image(systemName: category.systemImage)
                            .foregroundColor(.secondary)
                            .frame(width: 20)
                        
                        Text(category.displayName)
                            .font(.body)
                        
                        Spacer()
                        
                        Text("\(count)")
                            .font(.caption)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 2)
                            .background(.secondary.opacity(0.2))
                            .cornerRadius(4)
                    }
                    .contentShape(Rectangle())
                    .onTapGesture {
                        selectedCategory = category
                    }
                }
            } else {
                HStack {
                    Image(systemName: "checkmark.circle")
                        .foregroundColor(.green)
                    
                    Text("No errors recorded")
                        .font(.body)
                        .foregroundColor(.secondary)
                }
            }
        }
        .padding()
        .background(.regularMaterial)
        .cornerRadius(12)
    }
    
    // MARK: - Helper Properties
    
    private var overallSystemStatus: ServiceStatus {
        if !serviceHandler.failedServices.isEmpty {
            return .failed
        } else if !serviceHandler.degradedServices.isEmpty || networkHandler.isSlowConnection {
            return .degraded
        } else if networkHandler.isConnected {
            return .healthy
        } else {
            return .unknown
        }
    }
    
    private var overallSystemStatusText: String {
        switch overallSystemStatus {
        case .healthy: return "Healthy"
        case .degraded: return "Degraded"
        case .failed: return "Critical"
        case .unknown: return "Unknown"
        }
    }
    
    private func connectionTypeIcon(_ type: NWInterface.InterfaceType) -> String {
        switch type {
        case .wifi: return "wifi"
        case .cellular: return "antenna.radiowaves.left.and.right"
        case .wiredEthernet: return "cable.connector"
        default: return "network"
        }
    }
    
    private func connectionTypeText(_ type: NWInterface.InterfaceType) -> String {
        switch type {
        case .wifi: return "Wi-Fi"
        case .cellular: return "Cellular"
        case .wiredEthernet: return "Ethernet"
        default: return "Network"
        }
    }
}

// MARK: - Supporting Views

@available(iOS 18.0, macOS 14.0, *)
struct ServiceHealthRow: View {
    let serviceName: String
    let healthInfo: ServiceHealthInfo
    
    var body: some View {
        HStack {
            Image(systemName: healthInfo.status.systemImage)
                .foregroundColor(healthInfo.status.color)
                .frame(width: 16)
            
            VStack(alignment: .leading, spacing: 2) {
                Text(serviceName)
                    .font(.body)
                
                if let lastCheck = healthInfo.lastCheck {
                    Text("Last checked: \(DateFormatter.relativeTime.string(from: lastCheck))")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
            
            Spacer()
            
            VStack(alignment: .trailing, spacing: 2) {
                Text(healthInfo.status.rawValue.capitalized)
                    .font(.caption)
                    .foregroundColor(healthInfo.status.color)
                
                if let responseTime = healthInfo.responseTime {
                    Text("\(Int(responseTime * 1000))ms")
                        .font(.caption2)
                        .foregroundColor(.secondary)
                }
            }
        }
        .padding(.vertical, 4)
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct ActiveRecoveryRow: View {
    @ObservedObject var recovery: RecoveryOperation
    
    var body: some View {
        HStack {
            Image(systemName: recovery.status.systemImage)
                .foregroundColor(recovery.status.color)
                .frame(width: 16)
            
            VStack(alignment: .leading, spacing: 2) {
                Text(recovery.errorCategory.displayName)
                    .font(.body)
                
                if let strategy = recovery.currentStrategy {
                    Text(strategy.description)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
            
            Spacer()
            
            if recovery.status == .inProgress {
                ProgressView()
                    .scaleEffect(0.8)
            } else {
                Text(recovery.status == .succeeded ? "Success" : "Failed")
                    .font(.caption)
                    .foregroundColor(recovery.status.color)
            }
        }
        .padding(.vertical, 4)
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct RecoveryHistoryView: View {
    @ObservedObject var recoveryManager: ErrorRecoveryManager
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            List {
                if recoveryManager.recoveryHistory.isEmpty {
                    Text("No recovery operations recorded")
                        .foregroundColor(.secondary)
                        .frame(maxWidth: .infinity, alignment: .center)
                } else {
                    ForEach(recoveryManager.recoveryHistory.reversed()) { recovery in
                        RecoveryHistoryRow(recovery: recovery)
                    }
                }
            }
            .navigationTitle("Recovery History")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Close") {
                        dismiss()
                    }
                }
                
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Clear") {
                        recoveryManager.clearRecoveryHistory()
                    }
                    .disabled(recoveryManager.recoveryHistory.isEmpty)
                }
            }
        }
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct RecoveryHistoryRow: View {
    let recovery: RecoveryOperation
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: recovery.status.systemImage)
                    .foregroundColor(recovery.status.color)
                
                Text(recovery.errorCategory.displayName)
                    .font(.headline)
                
                Spacer()
                
                if let startTime = recovery.startTime {
                    Text(DateFormatter.errorTimestamp.string(from: startTime))
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
            
            if let successfulStrategy = recovery.successfulStrategy {
                Text("Recovered using: \(successfulStrategy.description)")
                    .font(.body)
                    .foregroundColor(.secondary)
            } else if recovery.status == .failed {
                Text("Recovery failed after trying \(recovery.strategies.count) strategies")
                    .font(.body)
                    .foregroundColor(.secondary)
            }
            
            if !recovery.context.isEmpty {
                Text("Context: \(recovery.context)")
                    .font(.caption)
                    .foregroundColor(.secondary.opacity(0.7))
            }
        }
        .padding(.vertical, 4)
    }
}

// MARK: - DateFormatter Extensions

extension DateFormatter {
    static let relativeTime: DateFormatter = {
        let formatter = DateFormatter()
        formatter.doesRelativeDateFormatting = true
        formatter.dateStyle = .none
        formatter.timeStyle = .short
        return formatter
    }()
}

#Preview {
    if #available(iOS 18.0, macOS 14.0, *) {
        SystemHealthDashboard()
    } else {
        Text("Preview unavailable")
    }
}