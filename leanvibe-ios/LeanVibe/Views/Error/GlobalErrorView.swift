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
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(spacing: 12) {
                Image(systemName: error.severity.systemImage)
                    .foregroundColor(error.severity.color)
                    .font(.title2)
                
                VStack(alignment: .leading, spacing: 4) {
                    Text(error.title)
                        .font(.headline)
                        .fontWeight(.semibold)
                    
                    Text(error.message)
                        .font(.body)
                        .foregroundColor(.secondary)
                }
                
                Spacer()
                
                Button(action: onDismiss) {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundColor(.secondary)
                        .font(.title2)
                }
            }
            
            if let retryAction = error.retryAction {
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
                    .foregroundColor(.tertiary)
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
    GlobalErrorView(errorManager: GlobalErrorManager.shared)
}