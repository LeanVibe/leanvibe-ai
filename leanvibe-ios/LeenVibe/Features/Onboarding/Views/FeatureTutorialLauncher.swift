
import SwiftUI

struct FeatureTutorialLauncher: View {
    let feature: DiscoverableFeature

    var body: some View {
        Button("Learn \(feature.name)") {
            // TutorialCoordinator.launch(tutorial: feature.tutorial)
            print("Launch tutorial for \(feature.name)")
        }
    }
}
