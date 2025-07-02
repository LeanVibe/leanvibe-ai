
import SwiftUI

@available(iOS 18.0, macOS 14.0, *)
struct WelcomeOnboardingView: View {
    var onContinue: () -> Void

    var body: some View {
        VStack {
            Text("Welcome to LeanVibe")
                .font(.largeTitle)
                .fontWeight(.bold)
                .padding()
            
            Text("Your AI Development Companion")
                .font(.title2)
                .padding()
            
            Button(action: onContinue) {
                Text("Get Started")
                    .font(.headline)
                    .padding()
                    .background(Color.blue)
                    .foregroundColor(.white)
                    .cornerRadius(10)
            }
        }
    }
}
