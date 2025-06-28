
import SwiftUI

enum DiagramTheme {
    case light, dark
}

struct DiagramStyle {
    let theme: DiagramTheme
    let backgroundColor: Color
    let nodeColor: Color
    let textColor: Color
}
