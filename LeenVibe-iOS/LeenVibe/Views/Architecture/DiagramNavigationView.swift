
import SwiftUI

@available(iOS 18.0, macOS 14.0, *)
struct DiagramNavigationView: View {
    @Binding var zoomScale: CGFloat
    let onZoomIn: () -> Void
    let onZoomOut: () -> Void
    let onReset: () -> Void
    let onRefresh: () -> Void
    let onExport: () -> Void

    var body: some View {
        VStack(spacing: 8) {
            // Zoom controls
            VStack(spacing: 4) {
                Button(action: onZoomIn) {
                    Image(systemName: "plus.magnifyingglass")
                        .font(.system(size: 16, weight: .medium))
                        .foregroundColor(.blue)
                }
                .disabled(zoomScale >= 3.0)
                
                Text("\(Int(zoomScale * 100))%")
                    .font(.caption2)
                    .foregroundColor(.secondary)
                    .frame(width: 40)
                
                Button(action: onZoomOut) {
                    Image(systemName: "minus.magnifyingglass")
                        .font(.system(size: 16, weight: .medium))
                        .foregroundColor(.blue)
                }
                .disabled(zoomScale <= 0.3)
            }
            
            Divider()
                .frame(width: 20)
            
            // Action controls
            VStack(spacing: 8) {
                Button(action: onReset) {
                    Image(systemName: "arrow.uturn.backward")
                        .font(.system(size: 16, weight: .medium))
                        .foregroundColor(.blue)
                }
                
                Button(action: onRefresh) {
                    Image(systemName: "arrow.clockwise")
                        .font(.system(size: 16, weight: .medium))
                        .foregroundColor(.blue)
                }
                
                Button(action: onExport) {
                    Image(systemName: "square.and.arrow.up")
                        .font(.system(size: 16, weight: .medium))
                        .foregroundColor(.blue)
                }
            }
        }
        .padding(12)
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(.ultraThinMaterial)
                .shadow(color: .black.opacity(0.1), radius: 4, x: 0, y: 2)
        )
    }
}
