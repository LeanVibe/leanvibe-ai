
import SwiftUI

enum AppView {
    case dashboard
    case architecture
    case kanban
    case settings
    case voice
}

@available(iOS 18.0, macOS 14.0, *)
struct ContextualHelpButton: View {
    let currentView: AppView
    @State private var showHelpContent = false

    var body: some View {
        Button(action: { showHelpContent.toggle() }) {
            Image(systemName: "questionmark.circle.fill")
                .font(.title2)
                .foregroundColor(.blue)
        }
        .overlay(alignment: .topTrailing) {
            if showHelpContent {
                Text("Help content for \(currentView)")
                    .padding()
                    .background(Color.white)
                    .cornerRadius(8)
                    .shadow(radius: 5)
                    .offset(x: -10, y: 30)
            }
        }
    }
}
