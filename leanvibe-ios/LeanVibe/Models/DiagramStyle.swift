
import SwiftUI

enum DiagramTheme {
    case light, dark
}

@available(iOS 13.0, macOS 10.15, *)
struct DiagramStyle {
    let theme: DiagramTheme
    let backgroundColor: Color
    let nodeColor: Color
    let textColor: Color
}
