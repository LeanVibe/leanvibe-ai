
import SwiftUI

struct ArchitectureViewerOnboardingView: View {
    var onContinue: () -> Void

    var body: some View {
        VStack {
            Text("Visualize Your Architecture")
                .font(.largeTitle)
                .fontWeight(.bold)
                .padding()
            
            Text("Explore interactive architecture diagrams to understand your codebase at a glance. See how components connect and evolve.")
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
