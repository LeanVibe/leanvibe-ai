
import SwiftUI

@available(iOS 18.0, macOS 14.0, *)
struct ArchitectureLoadingView: View {
    @State private var isAnimating = false
    @State private var opacity = 0.4
    
    var body: some View {
        VStack(spacing: 24) {
            // Loading animation with interconnected nodes
            ZStack {
                // Background circles
                ForEach(0..<6, id: \.self) { index in
                    Circle()
                        .fill(Color.blue.opacity(0.3))
                        .frame(width: 20, height: 20)
                        .offset(x: circleOffset(for: index).x, y: circleOffset(for: index).y)
                        .scaleEffect(isAnimating ? 1.2 : 0.8)
                        .opacity(isAnimating ? 1.0 : 0.5)
                        .animation(
                            Animation.easeInOut(duration: 1.5)
                                .repeatForever(autoreverses: true)
                                .delay(Double(index) * 0.1),
                            value: isAnimating
                        )
                }
                
                // Connecting lines
                ForEach(0..<6, id: \.self) { index in
                    if index < 5 {
                        Path { path in
                            let start = circleOffset(for: index)
                            let end = circleOffset(for: index + 1)
                            path.move(to: CGPoint(x: start.x, y: start.y))
                            path.addLine(to: CGPoint(x: end.x, y: end.y))
                        }
                        .stroke(Color.blue.opacity(0.4), lineWidth: 2)
                        .opacity(opacity)
                        .animation(
                            Animation.easeInOut(duration: 2.0)
                                .repeatForever(autoreverses: true),
                            value: opacity
                        )
                    }
                }
            }
            .frame(width: 200, height: 120)
            
            VStack(spacing: 12) {
                Text("Loading Architecture")
                    .font(.title2)
                    .fontWeight(.semibold)
                    .foregroundColor(.primary)
                
                Text("Analyzing project structure and dependencies...")
                    .font(.body)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal)
                
                // Progress indicator
                ProgressView()
                    .progressViewStyle(CircularProgressViewStyle(tint: .blue))
                    .scaleEffect(1.2)
            }
        }
        .padding()
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color(.systemBackground))
        .onAppear {
            withAnimation {
                isAnimating = true
                opacity = 1.0
            }
        }
    }
    
    private func circleOffset(for index: Int) -> CGPoint {
        let angle = Double(index) * (2 * .pi / 6)
        let radius: CGFloat = 50
        return CGPoint(
            x: cos(angle) * radius,
            y: sin(angle) * radius
        )
    }
}
