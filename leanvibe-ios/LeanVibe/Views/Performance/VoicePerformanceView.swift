import SwiftUI

@available(iOS 18.0, macOS 14.0, *)
struct VoicePerformanceView: View {
    @StateObject private var voiceService = UnifiedVoiceService.shared
    @State private var performanceMetrics: VoicePerformanceMetrics?
    @State private var showOptimizationAlert = false
    
    private let targetResponseTime: TimeInterval = 0.5
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 20) {
                    // Performance Status Card
                    performanceStatusCard
                    
                    // Response Time Metrics
                    responseTimeMetrics
                    
                    // Performance Chart (simplified)
                    performanceChart
                    
                    // Optimization Controls
                    optimizationControls
                }
                .padding()
            }
            .navigationTitle("Voice Performance")
            .onAppear {
                refreshMetrics()
            }
            .alert("Performance Optimization", isPresented: $showOptimizationAlert) {
                Button("Optimize Now") {
                    Task {
                        await voiceService.optimizePerformance()
                        refreshMetrics()
                    }
                }
                Button("Cancel", role: .cancel) { }
            } message: {
                Text("This will optimize voice recognition for better response times. Current average: \(performanceMetrics?.formattedAverageTime ?? "0.000")s")
            }
        }
    }
    
    private var performanceStatusCard: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("Performance Status")
                    .font(.headline)
                Spacer()
                Text(voiceService.performanceStatus.emoji)
                    .font(.title2)
            }
            
            Text(voiceService.performanceStatus.description)
                .font(.subheadline)
                .foregroundColor(.secondary)
            
            HStack {
                VStack(alignment: .leading) {
                    Text("Target Response Time")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    Text("\(String(format: "%.3f", targetResponseTime))s")
                        .font(.title3)
                        .fontWeight(.semibold)
                }
                
                Spacer()
                
                VStack(alignment: .trailing) {
                    Text("Current Average")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    Text("\(String(format: "%.3f", voiceService.averageResponseTime))s")
                        .font(.title3)
                        .fontWeight(.semibold)
                        .foregroundColor(averageResponseTimeColor)
                }
            }
        }
        .padding()
        .background(#if os(iOS)
Color(.systemGray6)
#else
Color.gray.opacity(0.1)
#endif)
        .cornerRadius(12)
    }
    
    private var responseTimeMetrics: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Response Time Metrics")
                .font(.headline)
            
            HStack {
                metricCard(
                    title: "Last Response",
                    value: "\(String(format: "%.3f", voiceService.responseTime))s",
                    color: responseTimeColor(voiceService.responseTime)
                )
                
                metricCard(
                    title: "Average",
                    value: "\(String(format: "%.3f", voiceService.averageResponseTime))s",
                    color: averageResponseTimeColor
                )
            }
            
            HStack {
                metricCard(
                    title: "Target",
                    value: "< 0.500s",
                    color: .blue
                )
                
                metricCard(
                    title: "Performance",
                    value: "\(String(format: "%.1f", targetPercentage))%",
                    color: performancePercentageColor
                )
            }
        }
    }
    
    private var performanceChart: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Performance Trend")
                .font(.headline)
            
            ZStack {
                Rectangle()
                    .fill(#if os(iOS)
Color(.systemGray6)
#else
Color.gray.opacity(0.1)
#endif)
                    .frame(height: 120)
                    .cornerRadius(8)
                
                VStack {
                    HStack {
                        Text("Target: 500ms")
                            .font(.caption)
                            .foregroundColor(.blue)
                        Spacer()
                        Text("Current: \(String(format: "%.0f", voiceService.averageResponseTime * 1000))ms")
                            .font(.caption)
                            .foregroundColor(averageResponseTimeColor)
                    }
                    .padding(.horizontal, 12)
                    .padding(.top, 8)
                    
                    Spacer()
                    
                    // Simple progress bar representation
                    ProgressView(value: min(1.0, targetResponseTime / max(voiceService.averageResponseTime, 0.001)))
                        .progressViewStyle(LinearProgressViewStyle(tint: averageResponseTimeColor))
                        .padding(.horizontal, 12)
                        .padding(.bottom, 8)
                }
            }
        }
    }
    
    private var optimizationControls: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Performance Controls")
                .font(.headline)
            
            Button(action: {
                showOptimizationAlert = true
            }) {
                HStack {
                    Image(systemName: "speedometer")
                    Text("Optimize Performance")
                }
                .frame(maxWidth: .infinity)
                .padding()
                .background(Color.blue)
                .foregroundColor(.white)
                .cornerRadius(8)
            }
            
            Button(action: {
                refreshMetrics()
            }) {
                HStack {
                    Image(systemName: "arrow.clockwise")
                    Text("Refresh Metrics")
                }
                .frame(maxWidth: .infinity)
                .padding()
                .background(Color(.systemGray4))
                .foregroundColor(.primary)
                .cornerRadius(8)
            }
        }
    }
    
    private func metricCard(title: String, value: String, color: Color) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title)
                .font(.caption)
                .foregroundColor(.secondary)
            Text(value)
                .font(.title3)
                .fontWeight(.semibold)
                .foregroundColor(color)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding()
        .background(#if os(iOS)
Color(.systemGray6)
#else
Color.gray.opacity(0.1)
#endif)
        .cornerRadius(8)
    }
    
    private func refreshMetrics() {
        performanceMetrics = voiceService.getPerformanceMetrics()
    }
    
    // MARK: - Color Helpers
    
    private func responseTimeColor(_ time: TimeInterval) -> Color {
        switch time {
        case 0.0..<0.5: return .green
        case 0.5..<1.0: return .yellow
        case 1.0..<2.0: return .orange
        default: return .red
        }
    }
    
    private var averageResponseTimeColor: Color {
        responseTimeColor(voiceService.averageResponseTime)
    }
    
    private var performancePercentageColor: Color {
        if targetPercentage >= 90 { return .green }
        if targetPercentage >= 70 { return .yellow }
        if targetPercentage >= 50 { return .orange }
        return .red
    }
    
    private var targetPercentage: Double {
        guard voiceService.averageResponseTime > 0 else { return 100 }
        return min(100, (targetResponseTime / voiceService.averageResponseTime) * 100)
    }
}

@available(iOS 18.0, macOS 14.0, *)
#Preview {
    VoicePerformanceView()
}