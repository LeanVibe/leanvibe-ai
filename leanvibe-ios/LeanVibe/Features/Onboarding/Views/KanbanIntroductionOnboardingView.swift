
import SwiftUI

@available(iOS 17.0, macOS 14.0, *)
struct KanbanIntroductionOnboardingView: View {
    var onContinue: () -> Void

    var body: some View {
        VStack {
            Text("Manage Tasks with Kanban")
                .font(.largeTitle)
                .fontWeight(.bold)
                .padding()
            
            Text("LeanVibe's integrated Kanban board helps you visualize and manage your development tasks with ease. Drag and drop to update status.")
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
