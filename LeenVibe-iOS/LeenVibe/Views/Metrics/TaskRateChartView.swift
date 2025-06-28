
import SwiftUI
import Charts

struct TaskRateChartView: View {
    let data: [TaskCompletionData]

    var body: some View {
        VStack(alignment: .leading) {
            Text("Task Completion Rate")
                .font(.headline)
                .padding(.bottom, 5)

            Chart {
                ForEach(data) {
                    BarMark(
                        x: .value("Status", $0.status),
                        y: .value("Count", $0.count)
                    )
                    .foregroundStyle(by: .value("Status", $0.status))
                }
            }
            .frame(height: 200)
        }
        .padding()
    }
}
