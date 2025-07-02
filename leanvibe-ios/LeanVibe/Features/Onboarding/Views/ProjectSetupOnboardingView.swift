
import SwiftUI

@available(iOS 18.0, macOS 14.0, *)
struct ProjectSetupOnboardingView: View {
    var onContinue: () -> Void

    var body: some View {
        VStack {
            Text("Set Up Your First Project")
                .font(.largeTitle)
                .fontWeight(.bold)
                .padding()
            
            Text("Connect to your local project to get started. You can do this by scanning a QR code from the LeanVibe CLI.")
                .font(.title2)
                .padding()
            
            Button(action: onContinue) {
                Text("Scan QR Code")
                    .font(.headline)
                    .padding()
                    .background(Color.blue)
                    .foregroundColor(.white)
                    .cornerRadius(10)
            }
        }
    }
}
