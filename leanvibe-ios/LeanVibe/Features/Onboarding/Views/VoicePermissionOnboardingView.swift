
import SwiftUI

@available(iOS 17.0, macOS 14.0, *)
struct VoicePermissionOnboardingView: View {
    var onContinue: () -> Void

    var body: some View {
        VStack {
            Text("Enable Voice Control")
                .font(.largeTitle)
                .fontWeight(.bold)
                .padding()
            
            Text("LeanVibe uses voice commands to help you code faster. Please grant microphone permissions to enable this feature.")
                .font(.title2)
                .padding()
            
            Button(action: onContinue) {
                Text("Grant Permission")
                    .font(.headline)
                    .padding()
                    .background(Color.blue)
                    .foregroundColor(.white)
                    .cornerRadius(10)
            }
        }
    }
}
