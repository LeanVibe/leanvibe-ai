
import Foundation
import WebKit
import SwiftUI
import Combine

@MainActor
class MermaidRenderer: ObservableObject {
    // MARK: - Published Properties
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var lastRenderedDiagram: ArchitectureDiagram?
    @Published var renderingProgress: Double = 0.0
    
    // MARK: - Private Properties
    private var webView: WKWebView?
    private var cancellables = Set<AnyCancellable>()
    private let cache = NSCache<NSString, CachedDiagramData>()
    private let renderQueue = DispatchQueue(label: "mermaid.render.queue", qos: .userInitiated)
    
    // Configuration
    private var currentTheme: DiagramTheme = .light
    private var currentZoomScale: CGFloat = 1.0
    private var enableInteractions: Bool = true
    
    // Callbacks
    var onNodeTapped: ((String) -> Void)?
    var onRenderComplete: ((ArchitectureDiagram) -> Void)?
    var onRenderError: ((Error) -> Void)?
    var onExportRequested: ((String) -> Void)?
    
    // MARK: - Initialization
    init() {
        setupCache()
        setupWebView()
    }
    
    // MARK: - Public Methods
    
    /// Renders a Mermaid diagram with the given definition
    func renderDiagram(_ diagram: ArchitectureDiagram, 
                      theme: DiagramTheme = .light,
                      zoomScale: CGFloat = 1.0,
                      enableInteractions: Bool = true) async -> Result<WKWebView, MermaidError> {
        
        // Check cache first
        if let cachedData = getCachedDiagram(for: diagram) {
            return await applyCachedDiagram(cachedData, zoomScale: zoomScale)
        }
        
        self.currentTheme = theme
        self.currentZoomScale = zoomScale
        self.enableInteractions = enableInteractions
        
        return await performRender(diagram)
    }
    
    /// Updates the theme of the current diagram
    func updateTheme(_ theme: DiagramTheme) async {
        guard let diagram = lastRenderedDiagram else { return }
        currentTheme = theme
        _ = await renderDiagram(diagram, theme: theme, zoomScale: currentZoomScale, enableInteractions: enableInteractions)
    }
    
    /// Updates the zoom scale of the current diagram
    func updateZoom(_ scale: CGFloat) {
        currentZoomScale = scale
        webView?.evaluateJavaScript("setZoomScale(\(scale));") { result, error in
            if let error = error {
                print("Zoom update error: \(error)")
            }
        }
    }
    
    /// Exports the current diagram as SVG
    func exportDiagramAsSVG() async -> Result<String, MermaidError> {
        guard webView != nil else {
            return .failure(.noWebView)
        }
        
        return await withCheckedContinuation { continuation in
            webView?.evaluateJavaScript("exportDiagramAsSVG();") { result, error in
                if let error = error {
                    continuation.resume(returning: .failure(.exportFailed(error.localizedDescription)))
                } else if let svgString = result as? String {
                    continuation.resume(returning: .success(svgString))
                } else {
                    continuation.resume(returning: .failure(.exportFailed("Invalid SVG data")))
                }
            }
        }
    }
    
    /// Clears the renderer cache
    func clearCache() {
        cache.removeAllObjects()
    }
    
    /// Returns the current WebView for embedding in SwiftUI
    func getWebView() -> WKWebView? {
        return webView
    }
}

// MARK: - Private Implementation
extension MermaidRenderer {
    
    private func setupCache() {
        cache.countLimit = 50 // Cache up to 50 diagrams
        cache.totalCostLimit = 100 * 1024 * 1024 // 100MB limit
    }
    
    private func setupWebView() {
        let config = WKWebViewConfiguration()
        config.userContentController = WKUserContentController()
        config.preferences.javaScriptEnabled = true
        config.allowsInlineMediaPlayback = true
        config.suppressesIncrementalRendering = false
        
        webView = WKWebView(frame: .zero, configuration: config)
        webView?.navigationDelegate = self
        webView?.scrollView.delegate = self
        
        // Add message handlers
        config.userContentController.add(self, name: "nodeTapped")
        config.userContentController.add(self, name: "diagramLoaded")
        config.userContentController.add(self, name: "diagramError")
        config.userContentController.add(self, name: "exportDiagram")
        config.userContentController.add(self, name: "renderProgress")
        
        // Configure scroll view
        webView?.scrollView.minimumZoomScale = 0.1
        webView?.scrollView.maximumZoomScale = 5.0
        webView?.scrollView.isScrollEnabled = true
        webView?.scrollView.showsHorizontalScrollIndicator = false
        webView?.scrollView.showsVerticalScrollIndicator = false
    }
    
    private func performRender(_ diagram: ArchitectureDiagram) async -> Result<WKWebView, MermaidError> {
        guard let webView = webView else {
            return .failure(.noWebView)
        }
        
        isLoading = true
        errorMessage = nil
        renderingProgress = 0.1
        
        return await withCheckedContinuation { continuation in
            let html = generateMermaidHTML(for: diagram)
            
            webView.loadHTMLString(html, baseURL: Bundle.main.resourceURL)
            
            // Set up timeout
            DispatchQueue.main.asyncAfter(deadline: .now() + 10.0) {
                if self.isLoading {
                    self.isLoading = false
                    self.errorMessage = "Rendering timeout"
                    continuation.resume(returning: .failure(.renderTimeout))
                }
            }
            
            // Store continuation for callback
            self.renderContinuation = continuation
        }
    }
    
    private var renderContinuation: CheckedContinuation<Result<WKWebView, MermaidError>, Never>?
    
    private func generateMermaidHTML(for diagram: ArchitectureDiagram) -> String {
        let themeConfig = currentTheme.mermaidConfig
        let interactionsScript = enableInteractions ? generateInteractionScript() : ""
        
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, minimum-scale=0.1, user-scalable=yes">
            <script src="mermaid.min.js"></script>
            <link rel="stylesheet" href="diagram-styles.css">
            <script src="interaction-bridge.js"></script>
            <style>
                body {
                    margin: 0;
                    padding: 20px;
                    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
                    background: \(currentTheme.backgroundColor);
                    color: \(currentTheme.textColor);
                    overflow: auto;
                    position: relative;
                }
                
                .diagram-container {
                    display: flex;
                    justify-content: center;
                    align-items: flex-start;
                    min-height: calc(100vh - 40px);
                    width: 100%;
                }
                
                .mermaid {
                    max-width: 100%;
                    height: auto;
                    transform-origin: center top;
                    transition: transform 0.3s ease;
                }
                
                .loading {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    height: 50vh;
                    gap: 16px;
                }
                
                .loading-spinner {
                    width: 40px;
                    height: 40px;
                    border: 3px solid \(currentTheme.loadingColor);
                    border-top: 3px solid \(currentTheme.accentColor);
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                }
                
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
                
                .error {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    height: 50vh;
                    gap: 16px;
                    color: \(currentTheme.errorColor);
                    text-align: center;
                    padding: 20px;
                }
                
                /* Enhanced node styling */
                .node rect, .node circle, .node ellipse, .node polygon {
                    cursor: \(enableInteractions ? "pointer" : "default");
                    transition: all 0.3s ease;
                    filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));
                }
                
                .node:hover rect, .node:hover circle, .node:hover ellipse, .node:hover polygon {
                    stroke-width: 3px;
                    filter: brightness(1.1) drop-shadow(0 4px 8px rgba(0,0,0,0.2));
                    transform: scale(1.05);
                }
                
                .progress-bar {
                    position: fixed;
                    top: 0;
                    left: 0;
                    height: 3px;
                    background: \(currentTheme.accentColor);
                    transition: width 0.3s ease;
                    z-index: 1000;
                }
                
                \(currentTheme.additionalCSS)
            </style>
        </head>
        <body>
            <div class="progress-bar" id="progress-bar" style="width: 0%"></div>
            
            <div class="diagram-container">
                <div class="loading" id="loading">
                    <div class="loading-spinner"></div>
                    <div>Rendering \(diagram.displayType)...</div>
                </div>
                
                <div class="mermaid" id="diagram" style="display: none;">
                    \(diagram.mermaidDefinition)
                </div>
            </div>
            
            <script>
                // Configure Mermaid with theme
                mermaid.initialize(\(themeConfig));
                
                let currentZoom = \(currentZoomScale);
                
                function updateProgress(percent) {
                    const bar = document.getElementById('progress-bar');
                    if (bar) {
                        bar.style.width = percent + '%';
                        if (window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.renderProgress) {
                            window.webkit.messageHandlers.renderProgress.postMessage(percent);
                        }
                    }
                }
                
                function setZoomScale(scale) {
                    currentZoom = scale;
                    const diagram = document.getElementById('diagram');
                    if (diagram) {
                        diagram.style.transform = `scale(${scale})`;
                    }
                }
                
                function exportDiagramAsSVG() {
                    const svg = document.querySelector('#diagram svg');
                    if (svg) {
                        return new XMLSerializer().serializeToString(svg);
                    }
                    return null;
                }
                
                function renderDiagram() {
                    updateProgress(20);
                    
                    const diagramElement = document.getElementById('diagram');
                    const loadingElement = document.getElementById('loading');
                    
                    try {
                        updateProgress(40);
                        
                        mermaid.init(undefined, diagramElement);
                        
                        updateProgress(80);
                        
                        // Hide loading, show diagram
                        loadingElement.style.display = 'none';
                        diagramElement.style.display = 'block';
                        
                        // Apply initial zoom
                        setZoomScale(currentZoom);
                        
                        updateProgress(100);
                        
                        // Add interaction listeners
                        setTimeout(() => {
                            \(interactionsScript)
                            
                            // Notify completion
                            if (window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.diagramLoaded) {
                                window.webkit.messageHandlers.diagramLoaded.postMessage('success');
                            }
                            
                            // Hide progress bar
                            setTimeout(() => {
                                document.getElementById('progress-bar').style.display = 'none';
                            }, 500);
                        }, 100);
                        
                    } catch (error) {
                        console.error('Rendering error:', error);
                        loadingElement.innerHTML = 
                            '<div class="error">' +
                            '<div style="font-size: 24px;">⚠️</div>' +
                            '<div>Failed to render diagram</div>' +
                            '<div style="font-size: 12px; margin-top: 8px; opacity: 0.7;">' + error.message + '</div>' +
                            '</div>';
                        
                        if (window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.diagramError) {
                            window.webkit.messageHandlers.diagramError.postMessage(error.message);
                        }
                    }
                }
                
                // Start rendering
                document.addEventListener('DOMContentLoaded', renderDiagram);
                if (document.readyState !== 'loading') {
                    renderDiagram();
                }
            </script>
        </body>
        </html>
        """
    }
    
    private func generateInteractionScript() -> String {
        return """
        // Add click listeners to nodes
        const nodes = document.querySelectorAll('.node, .nodeLabel, [id^="node"], g[id*="node"]');
        nodes.forEach(node => {
            node.style.cursor = 'pointer';
            node.addEventListener('click', function(event) {
                event.preventDefault();
                event.stopPropagation();
                const nodeId = this.id || this.getAttribute('data-id') || this.textContent || 'unknown';
                if (window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.nodeTapped) {
                    window.webkit.messageHandlers.nodeTapped.postMessage(nodeId);
                }
            });
        });
        """
    }
    
    private func getCachedDiagram(for diagram: ArchitectureDiagram) -> CachedDiagramData? {
        let cacheKey = "\(diagram.id.uuidString)_\(currentTheme.name)_\(currentZoomScale)" as NSString
        return cache.object(forKey: cacheKey)
    }
    
    private func cacheDiagram(_ diagram: ArchitectureDiagram, html: String) {
        let cacheKey = "\(diagram.id.uuidString)_\(currentTheme.name)_\(currentZoomScale)" as NSString
        let cachedData = CachedDiagramData(diagram: diagram, html: html, timestamp: Date())
        cache.setObject(cachedData, forKey: cacheKey, cost: html.count)
    }
    
    private func applyCachedDiagram(_ cachedData: CachedDiagramData, zoomScale: CGFloat) async -> Result<WKWebView, MermaidError> {
        guard let webView = webView else {
            return .failure(.noWebView)
        }
        
        isLoading = true
        renderingProgress = 0.5
        
        return await withCheckedContinuation { continuation in
            webView.loadHTMLString(cachedData.html, baseURL: Bundle.main.resourceURL)
            
            DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
                self.isLoading = false
                self.renderingProgress = 1.0
                self.lastRenderedDiagram = cachedData.diagram
                continuation.resume(returning: .success(webView))
            }
        }
    }
}

// MARK: - WKNavigationDelegate
extension MermaidRenderer: WKNavigationDelegate {
    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        // Navigation completed
    }
    
    func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: Error) {
        DispatchQueue.main.async {
            self.isLoading = false
            self.errorMessage = "Navigation failed: \(error.localizedDescription)"
            self.renderContinuation?.resume(returning: .failure(.navigationFailed(error.localizedDescription)))
            self.renderContinuation = nil
        }
    }
}

// MARK: - WKScriptMessageHandler
extension MermaidRenderer: WKScriptMessageHandler {
    func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
        DispatchQueue.main.async {
            switch message.name {
            case "nodeTapped":
                if let nodeId = message.body as? String {
                    self.onNodeTapped?(nodeId)
                }
                
            case "diagramLoaded":
                self.isLoading = false
                self.renderingProgress = 1.0
                if let diagram = self.lastRenderedDiagram {
                    self.onRenderComplete?(diagram)
                }
                if let webView = self.webView {
                    self.renderContinuation?.resume(returning: .success(webView))
                }
                self.renderContinuation = nil
                
            case "diagramError":
                self.isLoading = false
                let errorMsg = message.body as? String ?? "Unknown rendering error"
                self.errorMessage = errorMsg
                let error = MermaidError.renderFailed(errorMsg)
                self.onRenderError?(error)
                self.renderContinuation?.resume(returning: .failure(error))
                self.renderContinuation = nil
                
            case "exportDiagram":
                if let svgData = message.body as? String {
                    self.onExportRequested?(svgData)
                }
                
            case "renderProgress":
                if let progress = message.body as? Double {
                    self.renderingProgress = progress / 100.0
                }
                
            default:
                break
            }
        }
    }
}

// MARK: - UIScrollViewDelegate
extension MermaidRenderer: UIScrollViewDelegate {
    func viewForZooming(in scrollView: UIScrollView) -> UIView? {
        return scrollView.subviews.first
    }
    
    func scrollViewDidEndZooming(_ scrollView: UIScrollView, with view: UIView?, atScale scale: CGFloat) {
        currentZoomScale = scale
    }
}

// MARK: - Supporting Types

class CachedDiagramData: NSObject {
    let diagram: ArchitectureDiagram
    let html: String
    let timestamp: Date
    
    init(diagram: ArchitectureDiagram, html: String, timestamp: Date) {
        self.diagram = diagram
        self.html = html
        self.timestamp = timestamp
        super.init()
    }
}

enum MermaidError: Error, LocalizedError {
    case noWebView
    case renderFailed(String)
    case renderTimeout
    case navigationFailed(String)
    case exportFailed(String)
    case invalidDiagram
    
    var errorDescription: String? {
        switch self {
        case .noWebView:
            return "WebView not available"
        case .renderFailed(let message):
            return "Rendering failed: \(message)"
        case .renderTimeout:
            return "Rendering timed out"
        case .navigationFailed(let message):
            return "Navigation failed: \(message)"
        case .exportFailed(let message):
            return "Export failed: \(message)"
        case .invalidDiagram:
            return "Invalid diagram data"
        }
    }
}

enum DiagramTheme {
    case light, dark, auto
    
    var name: String {
        switch self {
        case .light: return "light"
        case .dark: return "dark"
        case .auto: return "auto"
        }
    }
    
    var backgroundColor: String {
        switch self {
        case .light, .auto: return "#ffffff"
        case .dark: return "#1c1c1e"
        }
    }
    
    var textColor: String {
        switch self {
        case .light, .auto: return "#000000"
        case .dark: return "#ffffff"
        }
    }
    
    var accentColor: String {
        switch self {
        case .light, .auto, .dark: return "#007AFF"
        }
    }
    
    var loadingColor: String {
        switch self {
        case .light, .auto: return "#e0e0e0"
        case .dark: return "#3a3a3c"
        }
    }
    
    var errorColor: String {
        return "#ff3b30"
    }
    
    var mermaidConfig: String {
        let themeValue = self == .dark ? "dark" : "default"
        return """
        {
            startOnLoad: false,
            theme: '\(themeValue)',
            themeVariables: {
                primaryColor: '\(accentColor)',
                primaryTextColor: '\(textColor)',
                primaryBorderColor: '\(accentColor)',
                lineColor: '\(textColor)',
                background: '\(backgroundColor)',
                mainBkg: '\(backgroundColor)',
                secondBkg: '\(backgroundColor)',
                tertiaryBkg: '\(backgroundColor)'
            },
            flowchart: {
                useMaxWidth: false,
                htmlLabels: true,
                curve: 'basis'
            }
        }
        """
    }
    
    var additionalCSS: String {
        switch self {
        case .dark:
            return """
            .node rect, .node circle, .node ellipse, .node polygon {
                stroke: #ffffff !important;
            }
            .edgePath path {
                stroke: #ffffff !important;
            }
            """
        default:
            return ""
        }
    }
}
