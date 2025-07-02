
import SwiftUI

@available(iOS 18.0, macOS 14.0, *)
struct VoiceCommandDemoOnboardingView: View {
    var onContinue: () -> Void

    var body: some View {
        VStack {
            Text("Voice Command Demo")
                .font(.largeTitle)
                .fontWeight(.bold)
                .padding()
            
            Text("Experience the power of voice control. Try saying 'Hey LeanVibe, show project status'.")
                .font(.title2)
                .padding()
            
            Button(action: onContinue) {
                Text("Next")
                    .font(.headline)
                    .padding()
                    .background(Color.blue)
                    .foregroundColor(.white)
                    .cornerRadius(10)
            }
        }
    }
}
