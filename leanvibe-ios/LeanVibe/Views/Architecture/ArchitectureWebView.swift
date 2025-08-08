
import SwiftUI
import WebKit
#if canImport(UIKit)
import UIKit
#endif

@available(iOS 18.0, macOS 14.0, *)
struct ArchitectureWebView: View {
    let diagramDefinition: String
    let zoomScale: CGFloat
    let onNodeTapped: (String) -> Void
    
    @State private var diagram: ArchitectureDiagram
    @State private var theme: DiagramTheme = .light
    
    init(diagramDefinition: String, zoomScale: CGFloat = 1.0, onNodeTapped: @escaping (String) -> Void) {
        self.diagramDefinition = diagramDefinition
        self.zoomScale = zoomScale
        self.onNodeTapped = onNodeTapped
        
        // Create diagram from definition
        self._diagram = State(initialValue: ArchitectureDiagram(
            name: "Architecture Diagram",
            mermaidDefinition: diagramDefinition,
            description: "Architecture visualization",
            diagramType: "architecture"
        ))
    }
    
    var body: some View {
        MermaidView(
            diagram: diagram,
            theme: theme,
            zoomScale: zoomScale,
            enableInteractions: true,
            onNodeTapped: onNodeTapped
        )
        .onChange(of: diagramDefinition) {
            // Update diagram when definition changes
            diagram = ArchitectureDiagram(
                name: diagram.name,
                mermaidDefinition: diagramDefinition,
                description: diagram.description,
                diagramType: diagram.diagramType
            )
        }
        .onAppear {
            // Set theme based on color scheme
            updateThemeFromColorScheme()
        }
        .onReceive(NotificationCenter.default.publisher(for: UIApplication.willEnterForegroundNotification)) { _ in
            updateThemeFromColorScheme()
        }
    }
    
    private func updateThemeFromColorScheme() {
        let colorScheme = UITraitCollection.current.userInterfaceStyle
        theme = colorScheme == .dark ? .dark : .light
    }
}
