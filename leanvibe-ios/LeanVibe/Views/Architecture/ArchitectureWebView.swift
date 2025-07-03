
import SwiftUI
import WebKit
#if canImport(UIKit)
import UIKit
#endif

@available(iOS 18.0, macOS 14.0, *)
struct ArchitectureWebView: UIViewRepresentable {
    let diagramDefinition: String
    let zoomScale: CGFloat
    let onNodeTapped: (String) -> Void
    
    @State private var isLoading = true
    @State private var hasError = false

    func makeUIView(context: Context) -> WKWebView {
        let configuration = WKWebViewConfiguration()
        configuration.userContentController = WKUserContentController()
        
        let webView = WKWebView(frame: .zero, configuration: configuration)
        webView.navigationDelegate = context.coordinator
        webView.scrollView.delegate = context.coordinator
        
        // Configure the web view to allow communication from JavaScript
        let contentController = webView.configuration.userContentController
        contentController.add(context.coordinator, name: "nodeTapped")
        contentController.add(context.coordinator, name: "diagramLoaded")
        contentController.add(context.coordinator, name: "diagramError")
        contentController.add(context.coordinator, name: "exportDiagram")
        
        // Enable scrolling and zooming
        webView.scrollView.isScrollEnabled = true
        webView.scrollView.minimumZoomScale = 0.3
        webView.scrollView.maximumZoomScale = 3.0
        webView.scrollView.zoomScale = zoomScale
        
        loadMermaidDiagram(in: webView)
        return webView
    }

    func updateUIView(_ uiView: WKWebView, context: Context) {
        // Update zoom if changed
        if abs(uiView.scrollView.zoomScale - zoomScale) > 0.01 {
            uiView.scrollView.setZoomScale(zoomScale, animated: true)
        }
        
        // Reload diagram if definition changed
        if context.coordinator.lastDiagramDefinition != diagramDefinition {
            loadMermaidDiagram(in: uiView)
            context.coordinator.lastDiagramDefinition = diagramDefinition
        }
    }

    private func loadMermaidDiagram(in webView: WKWebView) {
        let html = generateMermaidHTML(diagram: diagramDefinition)
        webView.loadHTMLString(html, baseURL: Bundle.main.resourceURL)
    }

    private func generateMermaidHTML(diagram: String) -> String {
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, minimum-scale=0.2, user-scalable=yes">
            <script src="mermaid.min.js"></script>
            <link rel="stylesheet" href="diagram-styles.css">
            <script src="interaction-bridge.js"></script>
            <style>
                body {
                    margin: 0;
                    padding: 20px;
                    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
                    background-color: #ffffff;
                    overflow: auto;
                    position: relative;
                }
                
                .mermaid {
                    display: flex;
                    justify-content: center;
                    align-items: flex-start;
                    min-height: 90vh;
                    width: 100%;
                    padding: 20px;
                    box-sizing: border-box;
                }
                
                /* Enhanced node styling */
                .node rect, .node circle, .node ellipse, .node polygon {
                    cursor: pointer;
                    transition: all 0.3s ease;
                    filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));
                }
                
                .node:hover rect, .node:hover circle, .node:hover ellipse, .node:hover polygon {
                    stroke-width: 3px;
                    filter: brightness(1.1) drop-shadow(0 4px 8px rgba(0,0,0,0.2));
                    transform: scale(1.05);
                }
                
                .node:active rect, .node:active circle, .node:active ellipse, .node:active polygon {
                    transform: scale(0.95);
                }
                
                /* Loading indicator */
                .loading {
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                    height: 90vh;
                    font-size: 18px;
                    color: #666;
                    gap: 16px;
                }
                
                .loading-spinner {
                    width: 40px;
                    height: 40px;
                    border: 4px solid #f3f3f3;
                    border-top: 4px solid #007AFF;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                }
                
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
                
                /* Error styling */
                .error {
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                    height: 90vh;
                    color: #ff6b6b;
                    text-align: center;
                    padding: 20px;
                    gap: 16px;
                }
                
                .error-icon {
                    font-size: 48px;
                    margin-bottom: 16px;
                }
                
                /* Zoom controls */
                .zoom-controls {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    display: flex;
                    flex-direction: column;
                    gap: 8px;
                    z-index: 1000;
                }
                
                .zoom-button {
                    width: 44px;
                    height: 44px;
                    border-radius: 22px;
                    border: none;
                    background: rgba(0, 122, 255, 0.9);
                    color: white;
                    font-size: 18px;
                    font-weight: bold;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: all 0.2s ease;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
                }
                
                .zoom-button:hover {
                    background: rgba(0, 122, 255, 1);
                    transform: scale(1.1);
                }
                
                .zoom-button:active {
                    transform: scale(0.9);
                }
                
                /* Export button */
                .export-button {
                    position: fixed;
                    bottom: 20px;
                    right: 20px;
                    padding: 12px 20px;
                    background: rgba(52, 199, 89, 0.9);
                    color: white;
                    border: none;
                    border-radius: 20px;
                    font-size: 14px;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.2s ease;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
                }
                
                .export-button:hover {
                    background: rgba(52, 199, 89, 1);
                    transform: translateY(-2px);
                }
                
                /* Responsive design */
                @media (max-width: 768px) {
                    .zoom-controls {
                        top: 10px;
                        right: 10px;
                    }
                    
                    .export-button {
                        bottom: 10px;
                        right: 10px;
                    }
                    
                    .zoom-button {
                        width: 36px;
                        height: 36px;
                        font-size: 16px;
                    }
                }
            </style>
        </head>
        <body>
            <div id="diagram-container">
                <div class="loading" id="loading">
                    <div class="loading-spinner"></div>
                    <div>Loading architecture diagram...</div>
                </div>
                <div class="mermaid" id="mermaid-diagram" style="display: none;">
                    \(diagram)
                </div>
            </div>
            
            <!-- Zoom Controls -->
            <div class="zoom-controls">
                <button class="zoom-button" onclick="zoomIn()">+</button>
                <button class="zoom-button" onclick="zoomOut()">−</button>
                <button class="zoom-button" onclick="resetZoom()">⌂</button>
            </div>
            
            <!-- Export Button -->
            <button class="export-button" onclick="exportDiagram()">Export SVG</button>
            
            <script>
                // Enhanced Mermaid configuration
                mermaid.initialize({ 
                    startOnLoad: false,
                    theme: 'default',
                    themeVariables: {
                        primaryColor: '#007AFF',
                        primaryTextColor: '#FFFFFF',
                        primaryBorderColor: '#005ecf',
                        lineColor: '#333333',
                        secondaryColor: '#F5F5F5',
                        tertiaryColor: '#E0E0E0',
                        background: '#ffffff',
                        mainBkg: '#ffffff',
                        secondBkg: '#f8f9fa',
                        tertiaryBkg: '#e9ecef'
                    },
                    flowchart: {
                        useMaxWidth: false,
                        htmlLabels: true,
                        curve: 'basis',
                        padding: 20
                    },
                    sequence: {
                        useMaxWidth: false,
                        diagramMarginX: 20,
                        diagramMarginY: 20
                    },
                    gantt: {
                        useMaxWidth: false,
                        leftPadding: 20,
                        rightPadding: 20
                    },
                    class: {
                        useMaxWidth: false
                    },
                    state: {
                        useMaxWidth: false
                    },
                    er: {
                        useMaxWidth: false
                    },
                    journey: {
                        useMaxWidth: false
                    },
                    pie: {
                        useMaxWidth: false
                    }
                });
                
                // Global variables for zoom control
                let currentZoom = 1;
                let minZoom = 0.2;
                let maxZoom = 5;
                let zoomStep = 0.2;
                
                // Function to render diagram
                function renderDiagram() {
                    const diagramElement = document.getElementById('mermaid-diagram');
                    const loadingElement = document.getElementById('loading');
                    
                    try {
                        mermaid.init(undefined, diagramElement);
                        
                        // Hide loading, show diagram
                        loadingElement.style.display = 'none';
                        diagramElement.style.display = 'block';
                        
                        // Add click listeners to nodes after rendering
                        setTimeout(() => {
                            addNodeListeners();
                            sendDiagramLoaded();
                        }, 100);
                        
                    } catch (error) {
                        console.error('Error rendering diagram:', error);
                        loadingElement.innerHTML = '<div class="error"><div class="error-icon">⚠️</div><div>Failed to render diagram</div><div style="font-size: 12px; margin-top: 8px; opacity: 0.7;">' + error.message + '</div></div>';
                        sendDiagramError(error.message);
                    }
                }
                
                // Add click listeners to nodes
                function addNodeListeners() {
                    const nodes = document.querySelectorAll('.node, .nodeLabel, [id^="node"], g[id*="node"]');
                    nodes.forEach(node => {
                        node.style.cursor = 'pointer';
                        node.addEventListener('click', function(event) {
                            event.preventDefault();
                            event.stopPropagation();
                            const nodeId = this.id || this.getAttribute('data-id') || this.textContent || 'unknown';
                            sendNodeTap(nodeId);
                        });
                    });
                }
                
                // Zoom functions
                function zoomIn() {
                    if (currentZoom < maxZoom) {
                        currentZoom += zoomStep;
                        applyZoom();
                    }
                }
                
                function zoomOut() {
                    if (currentZoom > minZoom) {
                        currentZoom -= zoomStep;
                        applyZoom();
                    }
                }
                
                function resetZoom() {
                    currentZoom = 1;
                    applyZoom();
                }
                
                function applyZoom() {
                    const diagram = document.getElementById('mermaid-diagram');
                    if (diagram) {
                        diagram.style.transform = `scale(${currentZoom})`;
                        diagram.style.transformOrigin = 'center top';
                    }
                }
                
                // Export function
                function exportDiagram() {
                    const svg = document.querySelector('#mermaid-diagram svg');
                    if (svg) {
                        const svgData = new XMLSerializer().serializeToString(svg);
                        sendExportRequest(svgData);
                    }
                }
                
                // Communication with iOS app
                function sendDiagramLoaded() {
                    if (window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.diagramLoaded) {
                        window.webkit.messageHandlers.diagramLoaded.postMessage('loaded');
                    }
                }
                
                function sendDiagramError(error) {
                    if (window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.diagramError) {
                        window.webkit.messageHandlers.diagramError.postMessage(error);
                    }
                }
                
                function sendExportRequest(svgData) {
                    if (window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.exportDiagram) {
                        window.webkit.messageHandlers.exportDiagram.postMessage(svgData);
                    }
                }
                
                // Start rendering when page loads
                document.addEventListener('DOMContentLoaded', function() {
                    renderDiagram();
                });
                
                // Fallback in case DOMContentLoaded already fired
                if (document.readyState === 'loading') {
                    document.addEventListener('DOMContentLoaded', renderDiagram);
                } else {
                    renderDiagram();
                }
                
                // Handle pinch-to-zoom gestures
                let lastTouchDistance = 0;
                
                document.addEventListener('touchstart', function(e) {
                    if (e.touches.length === 2) {
                        lastTouchDistance = Math.hypot(
                            e.touches[0].pageX - e.touches[1].pageX,
                            e.touches[0].pageY - e.touches[1].pageY
                        );
                    }
                });
                
                document.addEventListener('touchmove', function(e) {
                    if (e.touches.length === 2) {
                        e.preventDefault();
                        const currentDistance = Math.hypot(
                            e.touches[0].pageX - e.touches[1].pageX,
                            e.touches[0].pageY - e.touches[1].pageY
                        );
                        
                        if (lastTouchDistance > 0) {
                            const scaleFactor = currentDistance / lastTouchDistance;
                            const newZoom = currentZoom * scaleFactor;
                            
                            if (newZoom >= minZoom && newZoom <= maxZoom) {
                                currentZoom = newZoom;
                                applyZoom();
                            }
                        }
                        
                        lastTouchDistance = currentDistance;
                    }
                });
                
                document.addEventListener('touchend', function(e) {
                    if (e.touches.length < 2) {
                        lastTouchDistance = 0;
                    }
                });
            </script>
        </body>
        </html>
        """
    }
    
    func makeCoordinator() -> Coordinator {
        Coordinator(self)
    }

    class Coordinator: NSObject, WKNavigationDelegate, WKScriptMessageHandler, UIScrollViewDelegate {
        var parent: ArchitectureWebView
        var lastDiagramDefinition: String = ""

        init(_ parent: ArchitectureWebView) {
            self.parent = parent
        }

        func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
            // Apply zoom scale after loading
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
                webView.scrollView.setZoomScale(self.parent.zoomScale, animated: false)
            }
        }
        
        func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: Error) {
            print("WebView navigation failed: \(error.localizedDescription)")
        }
        
        func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
            switch message.name {
            case "nodeTapped":
                if let nodeId = message.body as? String {
                    parent.onNodeTapped(nodeId)
                }
            case "diagramLoaded":
                print("Diagram loaded successfully")
            case "diagramError":
                if let error = message.body as? String {
                    print("Diagram error: \(error)")
                }
            case "exportDiagram":
                if let svgData = message.body as? String {
                    handleExportRequest(svgData)
                }
            default:
                break
            }
        }
        
        private func handleExportRequest(_ svgData: String) {
            // Save SVG to documents directory
            let documentsPath = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
            let fileName = "architecture_diagram_\(Date().timeIntervalSince1970).svg"
            let fileURL = documentsPath.appendingPathComponent(fileName)
            
            do {
                try svgData.write(to: fileURL, atomically: true, encoding: .utf8)
                print("SVG diagram exported to: \(fileURL)")
                
                // Share the file
                DispatchQueue.main.async {
                    let activityVC = UIActivityViewController(activityItems: [fileURL], applicationActivities: nil)
                    
                    if let windowScene = UIApplication.shared.connectedScenes.first as? UIWindowScene,
                       let window = windowScene.windows.first {
                        window.rootViewController?.present(activityVC, animated: true)
                    }
                }
            } catch {
                print("Error saving SVG: \(error)")
            }
        }
        
        // UIScrollViewDelegate methods for zoom handling
        func viewForZooming(in scrollView: UIScrollView) -> UIView? {
            return scrollView.subviews.first
        }
        
        func scrollViewDidEndZooming(_ scrollView: UIScrollView, with view: UIView?, atScale scale: CGFloat) {
            // Could notify parent of zoom changes if needed
        }
    }
}
