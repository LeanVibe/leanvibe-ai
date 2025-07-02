
import SwiftUI

@available(iOS 18.0, macOS 14.0, *)
struct AdvancedFeaturesOnboardingView: View {
    var onContinue: () -> Void

    var body: some View {
        VStack {
            Text("Unlock Advanced Features")
                .font(.largeTitle)
                .fontWeight(.bold)
                .padding()
            
            Text("LeanVibe offers powerful features like real-time notifications, intelligent code analysis, and more. Explore them as you become a power user.")
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
