
import SwiftUI

@available(iOS 18.0, macOS 14.0, *)
struct CompletionOnboardingView: View {
    var onComplete: () -> Void

    var body: some View {
        VStack {
            Text("You're All Set!")
                .font(.largeTitle)
                .fontWeight(.bold)
                .padding()
            
            Text("You've successfully completed the LeanVibe onboarding. Start exploring your projects and unleash your productivity!")
                .font(.title2)
                .padding()
            
            Button(action: onComplete) {
                Text("Go to Dashboard")
                    .font(.headline)
                    .padding()
                    .background(Color.green)
                    .foregroundColor(.white)
                    .cornerRadius(10)
            }
        }
    }
}
