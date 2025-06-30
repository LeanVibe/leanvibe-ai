
import SwiftUI
import Charts

@available(iOS 18.0, macOS 14.0, *)
struct ConfidenceChartView: View {
    let data: [MetricHistory]

    var body: some View {
        VStack(alignment: .leading) {
            Text("Confidence Score Over Time")
                .font(.headline)
                .padding(.bottom, 5)

            Chart {
                ForEach(data) {
                    LineMark(
                        x: .value("Date", $0.timestamp),
                        y: .value("Confidence", $0.confidenceScore)
                    )
                    .interpolationMethod(.catmullRom)
                    .foregroundStyle(.blue)
                }
            }
            .chartYScale(domain: 0...1)
            .frame(height: 200)
        }
        .padding()
    }
}
