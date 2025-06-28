
import SwiftUI

struct DiagramComparisonView: View {
    let beforeDiagram: ArchitectureDiagram
    let afterDiagram: ArchitectureDiagram

    var body: some View {
        HStack {
            VStack {
                Text("Before")
                    .font(.headline)
                ArchitectureWebView(diagramDefinition: beforeDiagram.mermaidDefinition) {
                    nodeId in
                    print("Tapped node \(nodeId) in 'before' diagram")
                }
            }
            
            VStack {
                Text("After")
                    .font(.headline)
                ArchitectureWebView(diagramDefinition: afterDiagram.mermaidDefinition) {
                    nodeId in
                    print("Tapped node \(nodeId) in 'after' diagram")
                }
            }
        }
    }
}
