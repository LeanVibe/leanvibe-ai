import SwiftUI

@available(iOS 18.0, macOS 14.0, *)
struct GlobalErrorView: View {
    @ObservedObject var errorManager: GlobalErrorManager
    
    var body: some View {
        VStack {
            Spacer()
            
            if let error = errorManager.currentError, errorManager.showingErrorAlert {
                ErrorBannerView(error: error) {
                    errorManager.hideError()
                }
                .transition(.move(edge: .top).combined(with: .opacity))
                .animation(.spring(response: 0.5, dampingFraction: 0.8), value: errorManager.showingErrorAlert)
            }
        }
        .zIndex(999)
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct ErrorBannerView: View {
    let error: AppError
    let onDismiss: () -> Void
    @State private var showDetails = false
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(spacing: 12) {
                // Category and severity icons
                HStack(spacing: 4) {
                    Image(systemName: error.category.systemImage)
                        .foregroundColor(error.category == .network ? .blue : error.severity.color)
                        .font(.caption)
                    
                    Image(systemName: error.severity.systemImage)
                        .foregroundColor(error.severity.color)
                        .font(.title2)
                }
                
                VStack(alignment: .leading, spacing: 4) {
                    HStack {
                        Text(error.title)
                            .font(.headline)
                            .fontWeight(.semibold)
                        
                        if !error.context.isEmpty {
                            Text("• \(error.context)")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                    }
                    
                    Text(error.userFacingMessage)
                        .font(.body)
                        .foregroundColor(.secondary)
                    
                    if showDetails && error.technicalDetails != nil {
                        Text(error.technicalDetails!)
                            .font(.caption)
                            .foregroundColor(.secondary.opacity(0.7))
                            .padding(.top, 4)
                    }
                }
                
                Spacer()
                
                VStack(spacing: 4) {
                    Button(action: onDismiss) {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundColor(.secondary)
                            .font(.title2)
                    }
                    
                    if error.technicalDetails != nil {
                        Button(action: { showDetails.toggle() }) {
                            Image(systemName: showDetails ? "info.circle.fill" : "info.circle")
                                .foregroundColor(.secondary)
                                .font(.caption)
                        }
                    }
                }
            }
            
            // Action buttons
            if !error.suggestedActions.isEmpty {
                HStack {
                    Spacer()
                    
                    ForEach(error.suggestedActions) { action in
                        if action.isPrimary {
                            Button(action.title) {
                                action.action()
                                onDismiss()
                            }
                            .buttonStyle(BorderedProminentButtonStyle())
                            .controlSize(.small)
                        } else {
                            Button(action.title) {
                                action.action()
                            }
                            .buttonStyle(BorderedButtonStyle())
                            .controlSize(.small)
                        }
                    }
                }
            }
            
            // Legacy retry action support
            if let retryAction = error.retryAction, error.suggestedActions.isEmpty {
                HStack {
                    Spacer()
                    
                    Button("Retry") {
                        retryAction()
                        onDismiss()
                    }
                    .buttonStyle(.bordered)
                    .controlSize(.small)
                }
            }
        }
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(.regularMaterial)
                .shadow(radius: 8)
        )
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(error.severity.color, lineWidth: 2)
        )
        .padding(.horizontal)
        .padding(.top, 8)
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct ErrorHistoryView: View {
    @ObservedObject var errorManager: GlobalErrorManager
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            List {
                if errorManager.errorHistory.isEmpty {
                    Text("No errors recorded")
                        .foregroundColor(.secondary)
                        .frame(maxWidth: .infinity, alignment: .center)
                } else {
                    ForEach(errorManager.errorHistory.reversed()) { error in
                        ErrorHistoryRowView(error: error)
                    }
                }
            }
            .navigationTitle("Error History")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Close") {
                        dismiss()
                    }
                }
                
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Clear") {
                        errorManager.clearHistory()
                    }
                    .disabled(errorManager.errorHistory.isEmpty)
                }
            }
        }
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct ErrorHistoryRowView: View {
    let error: AppError
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: error.severity.systemImage)
                    .foregroundColor(error.severity.color)
                
                Text(error.title)
                    .font(.headline)
                
                Spacer()
                
                Text(DateFormatter.errorTimestamp.string(from: error.timestamp))
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Text(error.message)
                .font(.body)
                .foregroundColor(.secondary)
            
            if !error.context.isEmpty {
                Text("Context: \(error.context)")
                    .font(.caption)
                    .foregroundColor(.secondary.opacity(0.7))
            }
        }
        .padding(.vertical, 4)
    }
}

extension DateFormatter {
    static let errorTimestamp: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateStyle = .none
        formatter.timeStyle = .medium
        return formatter
    }()
}

#Preview {
    if #available(iOS 18.0, macOS 14.0, *) {
        GlobalErrorView(errorManager: GlobalErrorManager.shared)
    } else {
        Text("Preview unavailable")
    }
}