import SwiftUI

struct QROnboardingView: View {
    @StateObject private var webSocketService = WebSocketService()
    @ObservedObject var coordinator: AppCoordinator
    @State private var showingQRScanner = true
    
    var body: some View {
        ZStack {
            // Background
            LinearGradient(
                gradient: Gradient(colors: [Color.blue.opacity(0.8), Color.purple.opacity(0.8)]),
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            .ignoresSafeArea()
            
            VStack(spacing: 30) {
                Spacer()
                
                // App Logo and Title
                VStack(spacing: 16) {
                    Image(systemName: "brain.head.profile")
                        .font(.system(size: 80))
                        .foregroundColor(.white)
                    
                    Text("LeenVibe")
                        .font(.largeTitle)
                        .fontWeight(.bold)
                        .foregroundColor(.white)
                    
                    Text("AI Development Assistant")
                        .font(.title3)
                        .foregroundColor(.white.opacity(0.8))
                }
                
                Spacer()
                
                // Welcome Text
                VStack(spacing: 12) {
                    Text("Welcome to LeenVibe")
                        .font(.title2)
                        .fontWeight(.semibold)
                        .foregroundColor(.white)
                    
                    Text("Connect to your LeenVibe server by scanning the QR code displayed on your server dashboard.")
                        .font(.body)
                        .foregroundColor(.white.opacity(0.9))
                        .multilineTextAlignment(.center)
                        .padding(.horizontal, 32)
                }
                
                Spacer()
                
                // QR Scan Button
                Button(action: {
                    showingQRScanner = true
                }) {
                    HStack(spacing: 12) {
                        Image(systemName: "qrcode.viewfinder")
                            .font(.title2)
                        Text("Scan QR Code")
                            .font(.headline)
                    }
                    .foregroundColor(.blue)
                    .padding(.horizontal, 32)
                    .padding(.vertical, 16)
                    .background(Color.white)
                    .cornerRadius(12)
                    .shadow(color: .black.opacity(0.2), radius: 8, x: 0, y: 4)
                }
                
                Spacer()
            }
        }
        .sheet(isPresented: $showingQRScanner) {
            ServerQRScannerView(
                onResult: { qrContent in
                    // Handle QR code result
                    Task {
                        do {
                            try await webSocketService.connectWithQRCode(qrContent)
                            coordinator.handleQRScanSuccess()
                        } catch {
                            coordinator.handleQRScanFailure(error: error.localizedDescription)
                        }
                    }
                    showingQRScanner = false
                }
            )
        }
    }
}

#Preview {
    QROnboardingView(coordinator: AppCoordinator())
}