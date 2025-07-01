import SwiftUI

@available(iOS 18.0, macOS 14.0, *)
struct ErrorDisplayView: View {
    let error: String?
    let onRetry: (() -> Void)?
    
    init(error: String?, onRetry: (() -> Void)? = nil) {
        self.error = error
        self.onRetry = onRetry
    }
    
    var body: some View {
        if let error = error {
            VStack(spacing: 12) {
                Image(systemName: "exclamationmark.triangle.fill")
                    .font(.title)
                    .foregroundColor(.orange)
                
                Text(error)
                    .font(.body)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal)
                
                if let onRetry = onRetry {
                    Button("Retry") {
                        onRetry()
                    }
                    .buttonStyle(.borderedProminent)
                }
            }
            .padding()
            .background(.regularMaterial)
            .cornerRadius(12)
            .padding(.horizontal)
        }
    }
}

#Preview {
    VStack(spacing: 20) {
        ErrorDisplayView(error: "Network timeout occurred")
        
        ErrorDisplayView(
            error: "Failed to load data",
            onRetry: { print("Retry tapped") }
        )
        
        ErrorDisplayView(error: nil)
    }
}