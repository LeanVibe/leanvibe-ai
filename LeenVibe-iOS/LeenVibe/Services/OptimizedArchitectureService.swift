import SwiftUI
import Foundation
import WebKit

@MainActor
class OptimizedArchitectureService: ObservableObject {
    @Published var currentDiagram: ArchitectureDiagram?
    @Published var isLoading = false
    @Published var memoryUsage: Double = 0
    
    // Wrapper class to allow structs in NSCache
    private class CachedDiagram: NSObject {
        let diagram: ArchitectureDiagram
        init(diagram: ArchitectureDiagram) {
            self.diagram = diagram
        }
    }
    
    private var diagramCache = NSCache<NSString, CachedDiagram>()
    private var webViewPool = WebViewPool()
    private let memoryMonitor = MemoryMonitor()
    
    // Performance metrics
    private var renderTimes: [TimeInterval] = []
    private let maxRenderHistory = 10
    
    init() {
        configureDiagramCache()
        setupMemoryMonitoring()
        setupMemoryWarningObserver()
    }
    
    deinit {
        // Cleanup is handled automatically by ARC
    }
    
    // MARK: - Memory Optimization
    
    private func configureDiagramCache() {
        diagramCache.countLimit = 10 // Limit cached diagrams
        diagramCache.totalCostLimit = 50 * 1024 * 1024 // 50MB limit
        
        // Eviction handler to cleanup resources
        diagramCache.evictsObjectsWithDiscardedContent = true
    }
    
    private func setupMemoryWarningObserver() {
        NotificationCenter.default.addObserver(
            forName: UIApplication.didReceiveMemoryWarningNotification,
            object: nil,
            queue: .main
        ) { [weak self] _ in
            Task { await self?.handleMemoryWarning() }
        }
    }
    
    private func handleMemoryWarning() {
        // Aggressive cleanup on memory warning
        diagramCache.removeAllObjects()
        webViewPool.cleanupIdleWebViews()
        
        // Clear render history
        renderTimes.removeAll()
        
        // Force garbage collection
        autoreleasepool {
            // This block forces cleanup of autoreleased objects
        }
        
        print("📊 Architecture Service: Memory warning handled, cache cleared")
    }
    
    private func setupMemoryMonitoring() {
        Timer.scheduledTimer(withTimeInterval: 5.0, repeats: true) { [weak self] _ in
            Task { await self?.updateMemoryUsage() }
        }
    }
    
    private func updateMemoryUsage() {
        memoryUsage = memoryMonitor.getCurrentMemoryUsage()
        
        // Auto-cleanup if memory usage is high
        if memoryUsage > 150 { // 150MB threshold
            performAutomaticCleanup()
        }
    }
    
    private func performAutomaticCleanup() {
        // Remove oldest cached diagrams
        if diagramCache.countLimit > 5 {
            diagramCache.countLimit = 5
        }
        
        // Cleanup WebView pool
        webViewPool.reducePoolSize()
        
        print("📊 Architecture Service: Automatic cleanup performed")
    }
    
    // MARK: - Optimized Diagram Rendering
    
    func renderDiagram(_ specification: String, type: DiagramType) async -> ArchitectureDiagram? {
        let startTime = Date()
        isLoading = true
        defer { isLoading = false }
        
        // Check cache first
        let cacheKey = NSString(string: "\(type.rawValue):\(specification.hashValue)")
        if let cachedDiagram = diagramCache.object(forKey: cacheKey) {
            recordRenderTime(Date().timeIntervalSince(startTime))
            return cachedDiagram.diagram
        }
        
        do {
            // Use optimized WebView from pool
            let webView = await webViewPool.getWebView()
            
            // Render with optimized settings
            let diagram = try await renderDiagramOptimized(
                specification: specification,
                type: type,
                webView: webView
            )
            
            // Cache the result
            diagramCache.setObject(CachedDiagram(diagram: diagram), forKey: cacheKey)
            
            // Return WebView to pool
            webViewPool.returnWebView(webView)
            
            recordRenderTime(Date().timeIntervalSince(startTime))
            return diagram
            
        } catch {
            print("📊 Architecture Service: Render error - \(error)")
            return nil
        }
    }
    
    private func renderDiagramOptimized(
        specification: String,
        type: DiagramType,
        webView: WKWebView
    ) async throws -> ArchitectureDiagram {
        
        // Optimize JavaScript execution
        let optimizedHTML = generateOptimizedHTML(for: specification, type: type)
        
        return try await withCheckedThrowingContinuation { continuation in
            webView.loadHTMLString(optimizedHTML, baseURL: nil)
            
            // Set timeout for rendering
            let timeout = DispatchWorkItem {
                continuation.resume(throwing: ArchitectureServiceError.renderTimeout)
            }
            DispatchQueue.main.asyncAfter(deadline: .now() + 10, execute: timeout)
            
            // Monitor for completion
            webView.evaluateJavaScript("document.readyState") { [weak self] result, error in
                timeout.cancel()
                
                if let error = error {
                    continuation.resume(throwing: error)
                    return
                }
                
                // Extract rendered diagram
                Task {
                    if let diagram = await self?.extractDiagramFromWebView(webView) {
                        continuation.resume(returning: diagram)
                    } else {
                        continuation.resume(throwing: ArchitectureServiceError.extractionFailed)
                    }
                }
            }
        }
    }
    
    private func generateOptimizedHTML(for specification: String, type: DiagramType) -> String {
        // Minimized HTML with optimized Mermaid configuration
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { margin: 0; padding: 16px; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }
                #diagram { max-width: 100%; }
                .mermaid { background: transparent; }
            </style>
            <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
        </head>
        <body>
            <div id="diagram" class="mermaid">\(specification)</div>
            <script>
                mermaid.initialize({
                    startOnLoad: false,
                    theme: 'default',
                    themeVariables: { fontSize: '14px' },
                    flowchart: { htmlLabels: false, useMaxWidth: true },
                    securityLevel: 'loose',
                    maxTextSize: 90000
                });
                mermaid.run();
            </script>
        </body>
        </html>
        """
    }
    
    private func extractDiagramFromWebView(_ webView: WKWebView) async -> ArchitectureDiagram? {
        // Extract SVG and create optimized diagram object
        do {
            let result = try await webView.evaluateJavaScript("document.querySelector('.mermaid svg')?.outerHTML")
            guard let svgString = result as? String else {
                return nil
            }
            
            let diagram = ArchitectureDiagram(
                id: UUID(),
                name: "Architecture Diagram",
                mermaidDefinition: svgString,
                description: "Generated diagram",
                diagramType: "flowchart",
                createdAt: Date(),
                updatedAt: Date()
            )
            
            return diagram
        } catch {
            print("Error extracting diagram: \(error)")
            return nil
        }
    }
    
    // MARK: - Performance Tracking
    
    private func recordRenderTime(_ time: TimeInterval) {
        renderTimes.append(time)
        if renderTimes.count > maxRenderHistory {
            renderTimes.removeFirst()
        }
    }
    
    var averageRenderTime: TimeInterval {
        guard !renderTimes.isEmpty else { return 0 }
        return renderTimes.reduce(0, +) / Double(renderTimes.count)
    }
    
    var isPerformanceOptimal: Bool {
        return averageRenderTime < 3.0 && memoryUsage < 200
    }
    
    // MARK: - Resource Management
    
    func optimizeMemoryUsage() {
        // Manual optimization trigger
        diagramCache.removeAllObjects()
        webViewPool.optimizePool()
        performAutomaticCleanup()
    }
    
    private func cleanupResources() {
        diagramCache.removeAllObjects()
        webViewPool.cleanupIdleWebViews()
        NotificationCenter.default.removeObserver(self)
        print("📊 Architecture Service: Cleanup complete")
    }
}

// MARK: - WebView Pool for Optimized Rendering

@MainActor
class WebViewPool {
    private var pool: [WKWebView] = []
    private let maxPoolSize = 3
    
    func getWebView() async -> WKWebView {
        if let webView = pool.popLast() {
            return webView
        } else {
            return createWebView()
        }
    }
    
    func returnWebView(_ webView: WKWebView) {
        if pool.count < maxPoolSize {
            pool.append(webView)
        }
    }
    
    func cleanupIdleWebViews() {
        pool.removeAll()
    }
    
    func reducePoolSize() {
        if pool.count > 1 {
            pool.removeFirst()
        }
    }
    
    func optimizePool() {
        // Based on usage, can decide to shrink or grow pool
    }
    
    private func createWebView() -> WKWebView {
        let configuration = WKWebViewConfiguration()
        let webView = WKWebView(frame: .zero, configuration: configuration)
        webView.isOpaque = false
        webView.backgroundColor = .clear
        return webView
    }
}

// MARK: - Memory Monitor
class MemoryMonitor {
    func getCurrentMemoryUsage() -> Double {
        var taskInfo = mach_task_basic_info()
        var count = mach_msg_type_number_t(MemoryLayout<mach_task_basic_info>.size) / 4
        let kerr: kern_return_t = withUnsafeMutablePointer(to: &taskInfo) {
            $0.withMemoryRebound(to: integer_t.self, capacity: 1) {
                task_info(mach_task_self_, task_flavor_t(MACH_TASK_BASIC_INFO), $0, &count)
            }
        }
        
        if kerr == KERN_SUCCESS {
            return Double(taskInfo.resident_size) / 1024.0 / 1024.0 // In MB
        } else {
            return 0
        }
    }
}
enum DiagramType: String, Codable {
    case flowchart
    case sequence
    case classDiagram = "class"
    case state
    case erd = "erDiagram"
    case journey
    case gantt
    case pie
    case quadrant
    case requirement
    case mindmap
    case timeline
    case sankey
    case gitgraph = "gitGraph"
}
enum ArchitectureServiceError: Error {
    case renderTimeout
    case extractionFailed
} 