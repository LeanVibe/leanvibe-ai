
import SwiftUI

struct DashboardTourOnboardingView: View {
    var onContinue: () -> Void

    var body: some View {
        VStack {
            Text("Explore Your Dashboard")
                .font(.largeTitle)
                .fontWeight(.bold)
                .padding()
            
            Text("The LeenVibe dashboard provides a real-time overview of your projects, metrics, and tasks. Let's take a quick tour.")
                .font(.title2)
                .padding()
            
            Button(action: onContinue) {
                Text("Start Tour")
                    .font(.headline)
                    .padding()
                    .background(Color.blue)
                    .foregroundColor(.white)
                    .cornerRadius(10)
            }
        }
    }
}
