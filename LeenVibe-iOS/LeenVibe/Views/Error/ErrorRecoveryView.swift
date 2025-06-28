import SwiftUI

struct ErrorRecoveryView: View {
    let errorMessage: String
    let onRetry: () -> Void
    let onReset: () -> Void
    
    var body: some View {
        ZStack {
            // Background
            LinearGradient(
                gradient: Gradient(colors: [Color.red.opacity(0.1), Color.orange.opacity(0.1)]),
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            .ignoresSafeArea()
            
            VStack(spacing: 30) {
                Spacer()
                
                // Error Icon
                Image(systemName: "exclamationmark.triangle.fill")
                    .font(.system(size: 80))
                    .foregroundColor(.orange)
                
                // Error Title
                Text("Connection Failed")
                    .font(.title)
                    .fontWeight(.bold)
                    .foregroundColor(.primary)
                
                // Error Message
                Text(errorMessage)
                    .font(.body)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal, 32)
                
                Spacer()
                
                // Action Buttons
                VStack(spacing: 16) {
                    Button(action: onRetry) {
                        HStack(spacing: 12) {
                            Image(systemName: "arrow.clockwise")
                                .font(.title3)
                            Text("Try Again")
                                .font(.headline)
                        }
                        .foregroundColor(.white)
                        .padding(.horizontal, 32)
                        .padding(.vertical, 16)
                        .background(Color.blue)
                        .cornerRadius(12)
                        .shadow(color: .blue.opacity(0.3), radius: 8, x: 0, y: 4)
                    }
                    
                    Button(action: onReset) {
                        HStack(spacing: 12) {
                            Image(systemName: "arrow.counterclockwise")
                                .font(.title3)
                            Text("Start Over")
                                .font(.headline)
                        }
                        .foregroundColor(.orange)
                        .padding(.horizontal, 32)
                        .padding(.vertical, 16)
                        .background(Color.orange.opacity(0.1))
                        .overlay(
                            RoundedRectangle(cornerRadius: 12)
                                .stroke(Color.orange, lineWidth: 2)
                        )
                    }
                }
                
                Spacer()
                
                // Help Text
                Text("Make sure your LeenVibe server is running and the QR code is valid.")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal, 32)
            }
        }
    }
}

#Preview {
    ErrorRecoveryView(
        errorMessage: "Failed to connect to server. Please check your network connection and try again.",
        onRetry: {},
        onReset: {}
    )
}