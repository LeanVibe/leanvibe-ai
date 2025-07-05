import SwiftUI

/// Error History View - Shows historical errors and recovery attempts
@available(iOS 18.0, macOS 14.0, *)
struct ErrorHistoryView: View {
    
    // MARK: - Properties
    
    @StateObject private var errorManager = GlobalErrorManager.shared
    @State private var selectedFilter = ErrorFilter.all
    @State private var showingClearConfirmation = false
    
    // MARK: - Body
    
    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                // Filter Controls
                filterSection
                
                // Error List
                if filteredErrors.isEmpty {
                    emptyStateView
                } else {
                    List {
                        ForEach(filteredErrors, id: \.id) { error in
                            ErrorHistoryRow(error: error)
                        }
                    }
                    .listStyle(.plain)
                }
            }
            .navigationTitle("Error History")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Clear") {
                        showingClearConfirmation = true
                    }
                    .disabled(errorManager.errorHistory.isEmpty)
                }
            }
        }
        .alert("Clear Error History", isPresented: $showingClearConfirmation) {
            Button("Clear", role: .destructive) {
                errorManager.clearErrorHistory()
            }
            Button("Cancel", role: .cancel) { }
        } message: {
            Text("This will permanently clear all error history. This action cannot be undone.")
        }
    }
    
    // MARK: - View Components
    
    private var filterSection: some View {
        Picker("Filter", selection: $selectedFilter) {
            ForEach(ErrorFilter.allCases, id: \.self) { filter in
                Text(filter.displayName).tag(filter)
            }
        }
        .pickerStyle(.segmented)
        .padding()
    }
    
    private var emptyStateView: some View {
        VStack(spacing: 20) {
            Image(systemName: "checkmark.circle.fill")
                .font(.system(size: 60))
                .foregroundColor(.green)
            
            Text("No Errors")
                .font(.title2)
                .fontWeight(.medium)
            
            Text("Your app is running smoothly! Error history will appear here when issues occur.")
                .font(.body)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
    
    // MARK: - Computed Properties
    
    private var filteredErrors: [AppError] {
        switch selectedFilter {
        case .all:
            return errorManager.errorHistory
        case .critical:
            return errorManager.errorHistory.filter { $0.severity == .critical }
        case .error:
            return errorManager.errorHistory.filter { $0.severity == .error }
        case .warning:
            return errorManager.errorHistory.filter { $0.severity == .warning }
        case .recent:
            let oneHourAgo = Date().addingTimeInterval(-3600)
            return errorManager.errorHistory.filter { $0.timestamp > oneHourAgo }
        }
    }
}

// MARK: - Supporting Views

@available(iOS 18.0, macOS 14.0, *)
struct ErrorHistoryRow: View {
    let error: AppError
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                // Severity Indicator
                Circle()
                    .fill(severityColor)
                    .frame(width: 8, height: 8)
                
                Text(error.title)
                    .font(.headline)
                    .lineLimit(2)
                
                Spacer()
                
                Text(formatTimestamp(error.timestamp))
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Text(error.message)
                .font(.body)
                .foregroundColor(.primary)
                .lineLimit(3)
            
            if !error.context.isEmpty {
                Text("Context: \(error.context)")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .padding(.vertical, 4)
    }
    
    private var severityColor: Color {
        switch error.severity {
        case .critical:
            return .red
        case .error:
            return .orange
        case .warning:
            return .yellow
        case .info:
            return .blue
        }
    }
    
    private func formatTimestamp(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateStyle = .none
        formatter.timeStyle = .short
        return formatter.string(from: date)
    }
}

// MARK: - Supporting Types

enum ErrorFilter: String, CaseIterable {
    case all = "all"
    case critical = "critical"
    case error = "error"
    case warning = "warning"
    case recent = "recent"
    
    var displayName: String {
        switch self {
        case .all: return "All"
        case .critical: return "Critical"
        case .error: return "Errors"
        case .warning: return "Warnings"
        case .recent: return "Recent"
        }
    }
}

#if DEBUG
@available(iOS 18.0, macOS 14.0, *)
struct ErrorHistoryView_Previews: PreviewProvider {
    static var previews: some View {
        ErrorHistoryView()
    }
}
#endif