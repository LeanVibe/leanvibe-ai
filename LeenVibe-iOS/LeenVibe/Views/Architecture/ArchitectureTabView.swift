import SwiftUI

@MainActor
struct ArchitectureTabView: View {
    @StateObject private var service = ArchitectureVisualizationService(webSocketService: WebSocketService())
    @State private var showComparison = false
    @State private var selectedProject: String = "default_project"
    @State private var showingExportSheet = false
    @State private var exportedDiagram: String = ""

    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                // Main Content Area
                ZStack(alignment: .bottomTrailing) {
                    Group {
                        if service.isLoading {
                            ArchitectureLoadingView()
                        } else if let diagram = service.currentDiagram {
                            if showComparison {
                                DiagramComparisonView(
                                    beforeDiagram: diagram,
                                    afterDiagram: diagram // TODO: Implement real comparison
                                )
                            } else {
                                ArchitectureWebView(
                                    diagramDefinition: diagram.mermaidDefinition,
                                    zoomScale: service.zoomScale
                                ) { nodeId in
                                    handleNodeTapped(nodeId)
                                }
                            }
                        } else if let errorMessage = service.errorMessage {
                            ErrorView(errorMessage: errorMessage) {
                                Task {
                                    await service.refreshDiagram(clientId: selectedProject)
                                }
                            }
                        } else {
                            EmptyArchitectureView {
                                Task {
                                    await service.fetchProjectArchitecture(clientId: selectedProject)
                                }
                            }
                        }
                    }
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                    
                    // Floating Navigation Controls
                    if !service.isLoading && service.currentDiagram != nil {
                        DiagramNavigationView(
                            zoomScale: $service.zoomScale,
                            onZoomIn: { 
                                service.zoomScale = min(service.zoomScale * 1.2, 3.0)
                            },
                            onZoomOut: { 
                                service.zoomScale = max(service.zoomScale * 0.8, 0.3)
                            },
                            onReset: { 
                                service.zoomScale = 1.0
                            },
                            onRefresh: {
                                Task {
                                    await service.refreshDiagram(clientId: selectedProject)
                                }
                            },
                            onExport: {
                                exportDiagram()
                            }
                        )
                        .padding()
                    }
                }
            }
            .navigationTitle("Architecture")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItemGroup(placement: .navigationBarTrailing) {
                    Button(action: {
                        service.fetchArchitecture()
                    }) {
                        Image(systemName: "arrow.clockwise")
                    }
                    
                    Button(action: { showComparison.toggle() }) {
                        Image(systemName: showComparison ? "doc.text.image.fill" : "doc.text.image")
                    }
                    .disabled(service.currentDiagram == nil)
                    
                    Menu {
                        Button("Refresh") {
                            Task {
                                await service.refreshDiagram(clientId: selectedProject)
                            }
                        }
                        
                        Button("Export") {
                            exportDiagram()
                        }
                        .disabled(service.currentDiagram == nil)
                        
                        Divider()
                        
                        Button("Settings") {
                            // TODO: Add settings
                        }
                    } label: {
                        Image(systemName: "ellipsis.circle")
                    }
                }
            }
            .onAppear {
                setupInitialLoad()
            }
            .sheet(isPresented: $showingExportSheet) {
                ExportDiagramSheet(diagramContent: exportedDiagram)
            }
        }
        .sheet(isPresented: $showComparison) {
            DiagramComparisonView(
                service: service,
                webSocketService: WebSocketService()
            )
        }
    }
    
    private func setupInitialLoad() {
        // Fetch initial diagram
        Task {
            await service.fetchProjectArchitecture(clientId: selectedProject)
        }
    }
    
    private func handleNodeTapped(_ nodeId: String) {
        print("Node tapped: \(nodeId)")
        // TODO: Implement node detail view or navigation
        // Could show code for that component, navigate to file, etc.
    }
    
    private func exportDiagram() {
        if let diagramContent = service.exportDiagram() {
            exportedDiagram = diagramContent
            showingExportSheet = true
        }
    }
}

// MARK: - Supporting Views

struct ErrorView: View {
    let errorMessage: String
    let onRetry: () -> Void
    
    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: "exclamationmark.triangle")
                .font(.system(size: 48))
                .foregroundColor(.orange)
            
            Text("Architecture Loading Failed")
                .font(.title2)
                .fontWeight(.semibold)
            
            Text(errorMessage)
                .font(.body)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal)
            
            Button("Retry") {
                onRetry()
            }
            .buttonStyle(.borderedProminent)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color.gray.opacity(0.05))
    }
}

struct EmptyArchitectureView: View {
    let onLoadDiagram: () -> Void
    
    var body: some View {
        VStack(spacing: 20) {
            Image(systemName: "square.3.layers.3d")
                .font(.system(size: 64))
                .foregroundColor(.blue)
            
            Text("No Architecture Diagram")
                .font(.title2)
                .fontWeight(.semibold)
            
            Text("Load your project's architecture visualization to see the component relationships and structure.")
                .font(.body)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal)
            
            Button("Load Architecture") {
                onLoadDiagram()
            }
            .buttonStyle(.borderedProminent)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color.gray.opacity(0.05))
    }
}

struct ExportDiagramSheet: View {
    let diagramContent: String
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            ScrollView {
                Text(diagramContent)
                    .font(.system(.body, design: .monospaced))
                    .padding()
                    .background(Color.gray.opacity(0.1))
                    .cornerRadius(8)
                    .padding()
            }
            .navigationTitle("Export Diagram")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Done") {
                        dismiss()
                    }
                }
                
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Copy") {
                        UIPasteboard.general.string = diagramContent
                        dismiss()
                    }
                }
            }
        }
    }
}

/*
struct DiagramTypePicker: View {
    @Binding var selectedType: DiagramType
    let availableTypes: [DiagramType]
    let onTypeChanged: (DiagramType) -> Void
    
    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 12) {
                ForEach(availableTypes) { type in
                    Button(action: {
                        selectedType = type
                        onTypeChanged(type)
                    }) {
                        Text(type.displayName)
                            .font(.caption)
                            .padding(.horizontal, 12)
                            .padding(.vertical, 6)
                            .background(
                                RoundedRectangle(cornerRadius: 16)
                                    .fill(selectedType == type ? Color.blue : Color.gray.opacity(0.2))
                            )
                            .foregroundColor(selectedType == type ? .white : .primary)
                    }
                    .buttonStyle(PlainButtonStyle())
                }
            }
            .padding(.horizontal)
        }
        .padding(.vertical, 8)
        .background(Color.gray.opacity(0.1))
    }
}
*/
