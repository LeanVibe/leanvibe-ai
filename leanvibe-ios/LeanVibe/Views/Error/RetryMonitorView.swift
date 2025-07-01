import SwiftUI

@available(iOS 18.0, macOS 14.0, *)
struct RetryMonitorView: View {
    @ObservedObject var retryManager: RetryManager
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            List {
                if retryManager.activeRetries.isEmpty && retryManager.retryHistory.isEmpty {
                    ContentUnavailableView(
                        "No Retry Operations",
                        systemImage: "arrow.clockwise.circle",
                        description: Text("No retry operations have been performed yet.")
                    )
                } else {
                    activeRetriesSection
                    retryHistorySection
                }
            }
            .navigationTitle("Retry Monitor")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Close") {
                        dismiss()
                    }
                }
                
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Clear History") {
                        retryManager.retryHistory.removeAll()
                    }
                    .disabled(retryManager.retryHistory.isEmpty)
                }
            }
        }
    }
    
    @ViewBuilder
    private var activeRetriesSection: some View {
        if !retryManager.activeRetries.isEmpty {
            Section("Active Retries") {
                ForEach(retryManager.activeRetries) { operation in
                    RetryOperationRowView(operation: operation)
                }
            }
        }
    }
    
    @ViewBuilder
    private var retryHistorySection: some View {
        if !retryManager.retryHistory.isEmpty {
            Section("Retry History") {
                ForEach(retryManager.retryHistory.reversed()) { operation in
                    RetryOperationRowView(operation: operation)
                }
            }
        }
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct RetryOperationRowView: View {
    let operation: RetryOperation
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: operation.status.systemImage)
                    .foregroundColor(operation.status.color)
                
                Text(operation.context.isEmpty ? "Retry Operation" : operation.context)
                    .font(.headline)
                
                Spacer()
                
                if operation.status == .inProgress {
                    ProgressView()
                        .scaleEffect(0.8)
                }
                
                Text("\(operation.currentAttempt)/\(operation.maxAttempts)")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Strategy: \(operation.backoffStrategy.displayName)")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    
                    if let lastAttempt = operation.lastAttemptTime {
                        Text("Last attempt: \(DateFormatter.retryTimestamp.string(from: lastAttempt))")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }
                
                Spacer()
                
                if let nextRetry = operation.nextRetryTime, operation.status == .inProgress {
                    VStack(alignment: .trailing, spacing: 2) {
                        Text("Next retry:")
                            .font(.caption2)
                            .foregroundColor(.secondary)
                        Text(DateFormatter.retryTimestamp.string(from: nextRetry))
                            .font(.caption)
                            .foregroundColor(.orange)
                    }
                }
            }
            
            if let error = operation.lastError {
                Text("Last error: \(error.localizedDescription)")
                    .font(.caption)
                    .foregroundColor(.red)
                    .lineLimit(2)
            }
        }
        .padding(.vertical, 4)
    }
}

@available(iOS 18.0, macOS 14.0, *)
extension BackoffStrategy {
    var displayName: String {
        switch self {
        case .linear(let interval):
            return "Linear (\(interval)s)"
        case .exponential(let base, let multiplier):
            return "Exponential (\(base)s × \(multiplier))"
        case .fixed(let interval):
            return "Fixed (\(interval)s)"
        case .custom:
            return "Custom"
        }
    }
}

extension DateFormatter {
    static let retryTimestamp: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateStyle = .none
        formatter.timeStyle = .medium
        return formatter
    }()
}

#Preview {
    RetryMonitorView(retryManager: RetryManager.shared)
}