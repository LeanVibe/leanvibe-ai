import SwiftUI
import _Concurrency

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
                mainContentArea
                
                // Controls
                controlsSection
            }
            .navigationTitle("Architecture")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Export") {
                        exportCurrentDiagram()
                    }
                    .disabled(service.diagram == nil)
                }
            }
        }
        .sheet(isPresented: $showingExportSheet) {
            DiagramExportView(diagramCode: exportedDiagram)
        }
        .onAppear {
            loadDiagramForProject()
        }
    }
    
    @ViewBuilder
    private var mainContentArea: some View {
        ZStack(alignment: .bottomTrailing) {
            Group {
                if service.isLoading {
                    ArchitectureLoadingView()
                } else if let diagram = service.diagram {
                    if showComparison {
                        // For comparison view, we'll use the same diagram for now
                        // In a real implementation, you'd store previous versions
                        DiagramComparisonView(
                            beforeDiagram: diagram,
                            afterDiagram: diagram
                        )
                    } else {
                        ArchitectureWebView(
                            diagramDefinition: diagram.mermaidDefinition,
                            zoomScale: 1.0
                        ) { nodeId in
                            handleNodeTap(nodeId)
                        }
                    }
                } else if let error = service.errorMessage {
                    VStack(spacing: 16) {
                        Image(systemName: "exclamationmark.triangle")
                            .font(.largeTitle)
                            .foregroundColor(.orange)
                        Text("Failed to load architecture")
                            .font(.headline)
                        Text(error)
                            .font(.caption)
                            .foregroundColor(.secondary)
                        Button("Retry") {
                            loadDiagramForProject()
                        }
                    }
                    .padding()
                } else {
                    VStack(spacing: 16) {
                        Image(systemName: "doc.text")
                            .font(.largeTitle)
                            .foregroundColor(.secondary)
                        Text("No architecture diagram available")
                            .font(.headline)
                        Button("Generate Diagram") {
                            loadDiagramForProject()
                        }
                    }
                    .padding()
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            
            // Floating action button for refresh
            Button(action: {
                _Concurrency.Task {
                    await service.fetchInitialDiagram(for: selectedProject)
                }
            }) {
                Image(systemName: "arrow.clockwise")
                    .font(.title2)
                    .foregroundColor(.white)
                    .frame(width: 44, height: 44)
                    .background(Color.blue)
                    .clipShape(Circle())
                    .shadow(radius: 4)
            }
            .padding()
            .disabled(service.isLoading)
        }
    }
    
    @ViewBuilder
    private var controlsSection: some View {
        HStack {
            // Project selector
            Picker("Project", selection: $selectedProject) {
                Text("Default Project").tag("default_project")
                Text("Mobile App").tag("mobile_app")
                Text("Backend API").tag("backend_api")
            }
            .pickerStyle(SegmentedPickerStyle())
            .onChange(of: selectedProject) { _ in
                loadDiagramForProject()
            }
            
            Spacer()
            
            // Comparison toggle
            Button(action: {
                showComparison.toggle()
            }) {
                HStack {
                    Image(systemName: "square.stack")
                    Text("Compare")
                }
                .font(.caption)
                .foregroundColor(showComparison ? .white : .blue)
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
                .background(showComparison ? Color.blue : Color.clear)
                .overlay(
                    RoundedRectangle(cornerRadius: 6)
                        .stroke(Color.blue, lineWidth: 1)
                )
                .clipShape(RoundedRectangle(cornerRadius: 6))
            }
            .disabled(service.diagram == nil)
            
            // Auto-refresh toggle
            Button(action: {
                _Concurrency.Task {
                    await service.fetchInitialDiagram(for: selectedProject)
                }
            }) {
                HStack {
                    Image(systemName: "arrow.triangle.2.circlepath")
                    Text("Auto-Refresh")
                }
                .font(.caption)
                .foregroundColor(.blue)
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
                .overlay(
                    RoundedRectangle(cornerRadius: 6)
                        .stroke(Color.blue, lineWidth: 1)
                )
                .clipShape(RoundedRectangle(cornerRadius: 6))
            }
        }
        .padding()
        .background(Color(.systemGray6))
    }
    
    private func loadDiagramForProject() {
        _Concurrency.Task {
            await service.fetchInitialDiagram(for: selectedProject)
        }
    }
    
    private func exportCurrentDiagram() {
        if let diagram = service.diagram {
            exportedDiagram = diagram.mermaidDefinition
            showingExportSheet = true
        }
    }
    
    private func handleNodeTap(_ nodeId: String) {
        _Concurrency.Task {
            await service.requestDiagramUpdate(for: nodeId, in: selectedProject)
        }
    }
}

// Helper view for diagram export
struct DiagramExportView: View {
    let diagramCode: String
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            ScrollView {
                Text(diagramCode)
                    .font(.system(.caption, design: .monospaced))
                    .padding()
            }
            .navigationTitle("Export Diagram")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Done") {
                        dismiss()
                    }
                }
            }
        }
    }
}

#Preview {
    ArchitectureTabView()
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
            VStack(alignment: .leading, spacing: 16) {
                Text("Export Architecture Diagram")
                    .font(.title2)
                    .fontWeight(.semibold)
                
                Text("Mermaid Definition:")
                    .font(.headline)
                
                ScrollView {
                    Text(diagramContent)
                        .font(.system(.body, design: .monospaced))
                        .padding()
                        .background(Color.gray.opacity(0.1))
                        .cornerRadius(8)
                }
                
                HStack {
                    Button("Copy to Clipboard") {
                        UIPasteboard.general.string = diagramContent
                    }
                    .buttonStyle(.borderedProminent)
                    
                    Spacer()
                    
                    Button("Done") {
                        dismiss()
                    }
                    .buttonStyle(.bordered)
                }
            }
            .padding()
            .navigationTitle("Export")
            .navigationBarTitleDisplayMode(.inline)
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


