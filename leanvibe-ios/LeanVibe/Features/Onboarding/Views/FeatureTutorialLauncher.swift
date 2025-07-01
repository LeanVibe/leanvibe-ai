
import SwiftUI

@available(iOS 18.0, macOS 14.0, *)
struct FeatureTutorialLauncher: View {
    let feature: DiscoverableFeature

    var body: some View {
        Button("Learn \(feature.name)") {
            // TutorialCoordinator.launch(tutorial: feature.tutorial)
            print("Launch tutorial for \(feature.name)")
        }
    }
}
