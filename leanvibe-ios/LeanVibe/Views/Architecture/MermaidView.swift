import SwiftUI
import WebKit

@available(iOS 18.0, macOS 14.0, *)
struct MermaidView: View {
    // MARK: - Properties
    let diagram: ArchitectureDiagram
    let theme: DiagramTheme
    let enableInteractions: Bool
    let zoomScale: CGFloat
    
    // MARK: - Callbacks
    let onNodeTapped: (String) -> Void
    let onExportRequested: ((String) -> Void)?
    let onError: ((Error) -> Void)?
    
    // MARK: - State
    @StateObject private var renderer = MermaidRenderer()
    @State private var webView: WKWebView?
    @State private var showExportSheet = false
    @State private var exportedSVG = ""
    @State private var showErrorAlert = false
    @State private var currentError: Error?
    @State private var isInitialLoad = true
    
    // MARK: - Initialization
    init(
        diagram: ArchitectureDiagram,
        theme: DiagramTheme = .light,
        zoomScale: CGFloat = 1.0,
        enableInteractions: Bool = true,
        onNodeTapped: @escaping (String) -> Void = { _ in },
        onExportRequested: ((String) -> Void)? = nil,
        onError: ((Error) -> Void)? = nil
    ) {
        self.diagram = diagram
        self.theme = theme
        self.zoomScale = zoomScale
        self.enableInteractions = enableInteractions
        self.onNodeTapped = onNodeTapped
        self.onExportRequested = onExportRequested
        self.onError = onError
    }
    
    // MARK: - Body
    var body: some View {
        ZStack {
            // Background
            Color(theme == .dark ? .black : .white)
                .ignoresSafeArea()
            
            // Main Content
            VStack(spacing: 0) {
                // Progress bar
                if renderer.isLoading && renderer.renderingProgress > 0 {
                    ProgressView(value: renderer.renderingProgress, total: 1.0)
                        .progressViewStyle(LinearProgressViewStyle(tint: .blue))
                        .scaleEffect(x: 1, y: 0.5, anchor: .center)
                        .animation(.easeInOut, value: renderer.renderingProgress)
                }
                
                // WebView or Loading/Error States
                Group {
                    if renderer.isLoading && isInitialLoad {
                        loadingView
                    } else if let error = renderer.errorMessage {
                        errorView(error)
                    } else if let webView = webView {
                        MermaidWebViewRepresentable(webView: webView)
                            .transition(.opacity)
                    } else {
                        emptyStateView
                    }
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            }
            
            // Floating controls
            floatingControls
        }
        .onAppear {
            setupRenderer()
            loadDiagram()
        }
        .onChange(of: diagram) {
            loadDiagram()
        }
        .sheet(isPresented: $showExportSheet) {
            ExportSheet(svgData: exportedSVG, diagramName: diagram.name)
        }
        .alert("Rendering Error", isPresented: $showErrorAlert) {
            Button("OK") {
                showErrorAlert = false
            }
            Button("Retry") {
                loadDiagram()
            }
        } message: {
            if let error = currentError {
                Text(error.localizedDescription)
            }
        }
    }
    
    // MARK: - Subviews
    
    private var loadingView: some View {
        VStack(spacing: 20) {
            // Animated loading indicator
            ZStack {
                Circle()
                    .stroke(Color.gray.opacity(0.3), lineWidth: 4)
                    .frame(width: 60, height: 60)
                
                Circle()
                    .trim(from: 0, to: 0.7)
                    .stroke(Color.blue, lineWidth: 4)
                    .frame(width: 60, height: 60)
                    .rotationEffect(.degrees(-90))
                    .animation(.linear(duration: 1).repeatForever(autoreverses: false), value: renderer.isLoading)
            }
            
            VStack(spacing: 8) {
                Text("Rendering \(diagram.displayType)")
                    .font(.headline)
                    .foregroundColor(.primary)
                
                if renderer.renderingProgress > 0 {
                    Text("\(Int(renderer.renderingProgress * 100))% complete")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                
                Text(diagram.name)
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color(theme == .dark ? .black : .white))
    }
    
    private func errorView(_ errorMessage: String) -> some View {
        VStack(spacing: 20) {
            Image(systemName: "exclamationmark.triangle")
                .font(.system(size: 48))
                .foregroundColor(.orange)
            
            VStack(spacing: 8) {
                Text("Rendering Failed")
                    .font(.headline)
                    .foregroundColor(.primary)
                
                Text(errorMessage)
                    .font(.body)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal)
            }
            
            HStack(spacing: 16) {
                Button("Retry") {
                    loadDiagram()
                }
                .buttonStyle(.borderedProminent)
                
                Button("Export Raw") {
                    exportRawMermaid()
                }
                .buttonStyle(.bordered)
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color(theme == .dark ? .black : .white))
    }
    
    private var emptyStateView: some View {
        VStack(spacing: 20) {
            Image(systemName: "doc.text")
                .font(.system(size: 48))
                .foregroundColor(.gray)
            
            Text("No Diagram Available")
                .font(.headline)
                .foregroundColor(.primary)
            
            Button("Load Diagram") {
                loadDiagram()
            }
            .buttonStyle(.borderedProminent)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color(theme == .dark ? .black : .white))
    }
    
    private var floatingControls: some View {
        VStack {
            Spacer()
            
            HStack {
                Spacer()
                
                VStack(spacing: 12) {
                    // Export button
                    FloatingActionButton(
                        icon: "square.and.arrow.up",
                        color: .green,
                        action: exportDiagram
                    )
                    .disabled(webView == nil)
                    
                    // Refresh button
                    FloatingActionButton(
                        icon: "arrow.clockwise",
                        color: .blue,
                        action: loadDiagram
                    )
                    .disabled(renderer.isLoading)
                    
                    // Theme toggle button
                    FloatingActionButton(
                        icon: theme == .dark ? "sun.max" : "moon",
                        color: .purple,
                        action: toggleTheme
                    )
                }
                .padding()
            }
        }
    }
}

// MARK: - Methods
extension MermaidView {
    
    private func setupRenderer() {
        // Set up callbacks
        renderer.onNodeTapped = { nodeId in
            onNodeTapped(nodeId)
        }
        
        renderer.onExportRequested = { svgData in
            exportedSVG = svgData
            showExportSheet = true
            onExportRequested?(svgData)
        }
        
        renderer.onRenderError = { error in
            currentError = error
            showErrorAlert = true
            onError?(error)
        }
        
        renderer.onRenderComplete = { _ in
            isInitialLoad = false
        }
    }
    
    private func loadDiagram() {
        Task {
            let result = await renderer.renderDiagram(
                diagram,
                theme: theme,
                zoomScale: zoomScale,
                enableInteractions: enableInteractions
            )
            
            switch result {
            case .success(let renderedWebView):
                await MainActor.run {
                    self.webView = renderedWebView
                    self.isInitialLoad = false
                }
            case .failure(let error):
                await MainActor.run {
                    self.currentError = error
                    self.showErrorAlert = true
                    self.onError?(error)
                }
            }
        }
    }
    
    private func exportDiagram() {
        Task {
            let result = await renderer.exportDiagramAsSVG()
            
            switch result {
            case .success(let svgData):
                await MainActor.run {
                    self.exportedSVG = svgData
                    self.showExportSheet = true
                }
            case .failure(let error):
                await MainActor.run {
                    self.currentError = error
                    self.showErrorAlert = true
                }
            }
        }
    }
    
    private func exportRawMermaid() {
        exportedSVG = diagram.mermaidDefinition
        showExportSheet = true
    }
    
    private func toggleTheme() {
        let newTheme: DiagramTheme = theme == .dark ? .light : .dark
        Task {
            await renderer.updateTheme(newTheme)
        }
    }
}

// MARK: - Supporting Views

@available(iOS 18.0, macOS 14.0, *)
struct MermaidWebViewRepresentable: UIViewRepresentable {
    let webView: WKWebView
    
    func makeUIView(context: Context) -> WKWebView {
        return webView
    }
    
    func updateUIView(_ uiView: WKWebView, context: Context) {
        // Updates handled by the renderer
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct FloatingActionButton: View {
    let icon: String
    let color: Color
    let action: () -> Void
    
    @Environment(\.isEnabled) private var isEnabled
    
    var body: some View {
        Button(action: action) {
            Image(systemName: icon)
                .font(.title2)
                .foregroundColor(.white)
                .frame(width: 48, height: 48)
                .background(isEnabled ? color : Color.gray)
                .clipShape(Circle())
                .shadow(radius: 4)
        }
        .scaleEffect(isEnabled ? 1.0 : 0.9)
        .animation(.easeInOut(duration: 0.1), value: isEnabled)
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct ExportSheet: View {
    let svgData: String
    let diagramName: String
    
    @Environment(\.dismiss) private var dismiss
    @State private var showShareSheet = false
    
    var body: some View {
        NavigationView {
            VStack(spacing: 20) {
                VStack(spacing: 8) {
                    Image(systemName: "doc.text")
                        .font(.system(size: 48))
                        .foregroundColor(.blue)
                    
                    Text("Export \(diagramName)")
                        .font(.title2)
                        .fontWeight(.semibold)
                }
                
                VStack(alignment: .leading, spacing: 16) {
                    exportOption(
                        title: "Copy to Clipboard",
                        icon: "doc.on.clipboard",
                        action: copyToClipboard
                    )
                    
                    exportOption(
                        title: "Share",
                        icon: "square.and.arrow.up",
                        action: shareExport
                    )
                    
                    exportOption(
                        title: "Save to Files",
                        icon: "folder",
                        action: saveToFiles
                    )
                }
                .padding()
                
                Spacer()
            }
            .navigationTitle("Export Diagram")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Done") {
                        dismiss()
                    }
                }
            }
        }
    }
    
    private func exportOption(title: String, icon: String, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            HStack {
                Image(systemName: icon)
                    .foregroundColor(.blue)
                    .frame(width: 24)
                
                Text(title)
                    .foregroundColor(.primary)
                
                Spacer()
                
                Image(systemName: "chevron.right")
                    .foregroundColor(.secondary)
                    .font(.caption)
            }
            .padding(.vertical, 8)
        }
    }
    
    private func copyToClipboard() {
        UIPasteboard.general.string = svgData
        dismiss()
    }
    
    private func shareExport() {
        showShareSheet = true
    }
    
    private func saveToFiles() {
        // Implementation for saving to Files app
        let documentsPath = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        let fileName = "\(diagramName.replacingOccurrences(of: " ", with: "_")).svg"
        let fileURL = documentsPath.appendingPathComponent(fileName)
        
        do {
            try svgData.write(to: fileURL, atomically: true, encoding: .utf8)
            
            // Show share sheet for the file
            let activityVC = UIActivityViewController(activityItems: [fileURL], applicationActivities: nil)
            
            if let windowScene = UIApplication.shared.connectedScenes.first as? UIWindowScene,
               let window = windowScene.windows.first,
               let rootVC = window.rootViewController {
                rootVC.present(activityVC, animated: true)
            }
        } catch {
            print("Error saving file: \(error)")
        }
    }
}

// MARK: - Convenience Initializers
extension MermaidView {
    
    /// Simplified initializer for basic usage
    init(diagram: ArchitectureDiagram, onNodeTapped: @escaping (String) -> Void = { _ in }) {
        self.init(
            diagram: diagram,
            theme: .light,
            zoomScale: 1.0,
            enableInteractions: true,
            onNodeTapped: onNodeTapped
        )
    }
    
    /// Initializer with theme support
    init(diagram: ArchitectureDiagram, theme: DiagramTheme, onNodeTapped: @escaping (String) -> Void = { _ in }) {
        self.init(
            diagram: diagram,
            theme: theme,
            zoomScale: 1.0,
            enableInteractions: true,
            onNodeTapped: onNodeTapped
        )
    }
}

// MARK: - Preview
#Preview {
    let sampleDiagram = ArchitectureDiagram(
        name: "Sample Architecture",
        mermaidDefinition: """
        graph TD
            A[Frontend] --> B[API Gateway]
            B --> C[Microservice 1]
            B --> D[Microservice 2]
            C --> E[Database 1]
            D --> F[Database 2]
        """,
        description: "Sample architecture diagram for preview",
        diagramType: "architecture"
    )
    
    return MermaidView(diagram: sampleDiagram) { nodeId in
        print("Tapped node: \(nodeId)")
    }
}