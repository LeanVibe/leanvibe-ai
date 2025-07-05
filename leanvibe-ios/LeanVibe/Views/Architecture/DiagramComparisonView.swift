import SwiftUI

@available(iOS 18.0, macOS 14.0, *)
struct DiagramComparisonView: View {
    let beforeDiagram: ArchitectureDiagram
    let afterDiagram: ArchitectureDiagram
    
    @State private var selectedView: ComparisonView = .sideBySide
    @State private var highlightChanges = true
    @State private var syncZoom = true
    @State private var currentZoom: CGFloat = 1.0
    
    enum ComparisonView: String, CaseIterable {
        case sideBySide = "Side by Side"
        case overlay = "Overlay"
        case swipe = "Swipe"
    }

    var body: some View {
        VStack(spacing: 0) {
            // Control bar
            HStack {
                Picker("View", selection: $selectedView) {
                    ForEach(ComparisonView.allCases, id: \.self) { view in
                        Text(view.rawValue).tag(view)
                    }
                }
                .pickerStyle(SegmentedPickerStyle())
                
                Spacer()
                
                HStack(spacing: 16) {
                    Toggle("Highlight Changes", isOn: $highlightChanges)
                        .toggleStyle(SwitchToggleStyle())
                    
                    Toggle("Sync Zoom", isOn: $syncZoom)
                        .toggleStyle(SwitchToggleStyle())
                }
                .font(.caption)
            }
            .padding()
            .background(#if os(iOS)
Color(.systemGray6)
#else
Color.gray.opacity(0.1)
#endif)
            
            // Main comparison view
            switch selectedView {
            case .sideBySide:
                sideBySideView
            case .overlay:
                overlayView
            case .swipe:
                swipeView
            }
        }
    }
    
    @ViewBuilder
    private var sideBySideView: some View {
        HStack(spacing: 1) {
            VStack(spacing: 8) {
                headerView(title: "Before", subtitle: beforeDiagram.displayType, color: .red)
                ArchitectureWebView(
                    diagramDefinition: beforeDiagram.mermaidDefinition,
                    zoomScale: currentZoom
                ) { nodeId in
                    handleNodeTap(nodeId, in: "before")
                }
            }
            
            Divider()
            
            VStack(spacing: 8) {
                headerView(title: "After", subtitle: afterDiagram.displayType, color: .green)
                ArchitectureWebView(
                    diagramDefinition: afterDiagram.mermaidDefinition,
                    zoomScale: currentZoom
                ) { nodeId in
                    handleNodeTap(nodeId, in: "after")
                }
            }
        }
    }
    
    @ViewBuilder
    private var overlayView: some View {
        ZStack {
            VStack(spacing: 8) {
                headerView(title: "Before (Background)", subtitle: beforeDiagram.displayType, color: .red)
                ArchitectureWebView(
                    diagramDefinition: beforeDiagram.mermaidDefinition,
                    zoomScale: currentZoom
                ) { nodeId in
                    handleNodeTap(nodeId, in: "before")
                }
                .opacity(0.5)
            }
            
            VStack(spacing: 8) {
                headerView(title: "After (Overlay)", subtitle: afterDiagram.displayType, color: .green)
                ArchitectureWebView(
                    diagramDefinition: afterDiagram.mermaidDefinition,
                    zoomScale: currentZoom
                ) { nodeId in
                    handleNodeTap(nodeId, in: "after")
                }
                .opacity(0.8)
            }
        }
    }
    
    @ViewBuilder
    private var swipeView: some View {
        GeometryReader { geometry in
            ZStack {
                // Before diagram (left side)
                VStack(spacing: 8) {
                    headerView(title: "Before", subtitle: beforeDiagram.displayType, color: .red)
                    ArchitectureWebView(
                        diagramDefinition: beforeDiagram.mermaidDefinition,
                        zoomScale: currentZoom
                    ) { nodeId in
                        handleNodeTap(nodeId, in: "before")
                    }
                }
                
                // After diagram (right side)
                VStack(spacing: 8) {
                    headerView(title: "After", subtitle: afterDiagram.displayType, color: .green)
                    ArchitectureWebView(
                        diagramDefinition: afterDiagram.mermaidDefinition,
                        zoomScale: currentZoom
                    ) { nodeId in
                        handleNodeTap(nodeId, in: "after")
                    }
                }
                .mask(
                    Rectangle()
                        .offset(x: geometry.size.width * 0.5)
                )
            }
        }
    }
    
    @ViewBuilder
    private func headerView(title: String, subtitle: String, color: Color) -> some View {
        HStack {
            Circle()
                .fill(color)
                .frame(width: 12, height: 12)
            
            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(.headline)
                    .foregroundColor(color)
                
                Text(subtitle)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
            
            if let beforeDate = beforeDiagram.updatedAt,
               let afterDate = afterDiagram.updatedAt {
                Text(relativeDateString(from: beforeDate, to: afterDate))
                    .font(.caption2)
                    .foregroundColor(.secondary)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(Color(.systemGray5))
                    .clipShape(RoundedRectangle(cornerRadius: 8))
            }
        }
        .padding(.horizontal)
        .padding(.vertical, 8)
        .background(#if os(iOS)
Color(.systemGray6)
#else
Color.gray.opacity(0.1)
#endif)
    }
    
    private func handleNodeTap(_ nodeId: String, in diagram: String) {
        print("Tapped node \(nodeId) in '\(diagram)' diagram")
        // Could highlight corresponding nodes in both diagrams
    }
    
    private func relativeDateString(from: Date, to: Date) -> String {
        let interval = to.timeIntervalSince(from)
        let formatter = RelativeDateTimeFormatter()
        formatter.unitsStyle = .abbreviated
        return formatter.localizedString(for: to, relativeTo: from)
    }
}
