
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
            <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=3.0, minimum-scale=0.3, user-scalable=yes">
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
                }
                
                .mermaid {
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 90vh;
                    width: 100%;
                }
                
                /* Enhanced node styling */
                .node rect, .node circle, .node ellipse, .node polygon {
                    cursor: pointer;
                    transition: all 0.2s ease;
                }
                
                .node:hover rect, .node:hover circle, .node:hover ellipse, .node:hover polygon {
                    stroke-width: 3px;
                    filter: brightness(1.1);
                }
                
                /* Loading indicator */
                .loading {
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 90vh;
                    font-size: 18px;
                    color: #666;
                }
                
                /* Error styling */
                .error {
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 90vh;
                    color: #ff6b6b;
                    text-align: center;
                    padding: 20px;
                }
            </style>
        </head>
        <body>
            <div id="diagram-container">
                <div class="loading" id="loading">Loading diagram...</div>
                <div class="mermaid" id="mermaid-diagram" style="display: none;">
                    \(diagram)
                </div>
            </div>
            
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
                        tertiaryColor: '#E0E0E0'
                    },
                    flowchart: {
                        useMaxWidth: false,
                        htmlLabels: true,
                        curve: 'basis'
                    },
                    sequence: {
                        useMaxWidth: false
                    },
                    gantt: {
                        useMaxWidth: false
                    }
                });
                
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
                        loadingElement.innerHTML = '<div class="error">Failed to render diagram:<br>' + error.message + '</div>';
                    }
                }
                
                // Add click listeners to nodes
                function addNodeListeners() {
                    const nodes = document.querySelectorAll('.node, .nodeLabel, [id^="node"]');
                    nodes.forEach(node => {
                        node.style.cursor = 'pointer';
                        node.addEventListener('click', function(event) {
                            event.preventDefault();
                            event.stopPropagation();
                            const nodeId = this.id || this.getAttribute('data-id') || 'unknown';
                            sendNodeTap(nodeId);
                        });
                    });
                }
                
                // Notify iOS app that diagram is loaded
                function sendDiagramLoaded() {
                    if (window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.diagramLoaded) {
                        window.webkit.messageHandlers.diagramLoaded.postMessage('loaded');
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
            default:
                break
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
