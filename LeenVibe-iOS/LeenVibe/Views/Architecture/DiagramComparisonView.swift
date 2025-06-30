import SwiftUI

@available(iOS 18.0, macOS 14.0, *)
struct DiagramComparisonView: View {
    let beforeDiagram: ArchitectureDiagram
    let afterDiagram: ArchitectureDiagram

    var body: some View {
        HStack {
            VStack {
                Text("Before")
                    .font(.headline)
                ArchitectureWebView(
                    diagramDefinition: beforeDiagram.mermaidDefinition,
                    zoomScale: 1.0
                ) { nodeId in
                    print("Tapped node \(nodeId) in 'before' diagram")
                }
            }
            
            VStack {
                Text("After")
                    .font(.headline)
                ArchitectureWebView(
                    diagramDefinition: afterDiagram.mermaidDefinition,
                    zoomScale: 1.0
                ) { nodeId in
                    print("Tapped node \(nodeId) in 'after' diagram")
                }
            }
        }
    }
}
