
import SwiftUI

@available(iOS 18.0, macOS 14.0, *)
struct MetricsDashboardView: View {
    @StateObject private var viewModel = MetricsViewModel(clientId: "default_project")

    var body: some View {
        NavigationView {
            ScrollView {
                VStack(alignment: .leading) {
                    Text("AI Performance Metrics")
                        .font(.largeTitle)
                        .fontWeight(.bold)
                        .padding(.horizontal)

                    if viewModel.isLoadingMetrics || viewModel.isLoadingDecisions {
                        ProgressView("Loading metrics...")
                            .padding()
                    } else if let errorMessage = viewModel.errorMessage {
                        Text(errorMessage)
                            .foregroundColor(.red)
                            .padding()
                    } else {
                        // Summary Stats
                        HStack {
                            MetricSummaryCard(title: "Avg. Confidence", value: String(format: "%.2f", viewModel.averageConfidence))
                            MetricSummaryCard(title: "Total Tasks", value: "\(viewModel.totalTasksCompleted)")
                        }
                        .padding(.horizontal)

                        // Charts
                        ConfidenceChartView(data: viewModel.metricHistory)
                        TaskRateChartView(data: [
                            TaskCompletionData(status: "Done", count: 70),
                            TaskCompletionData(status: "In Progress", count: 20),
                            TaskCompletionData(status: "Blocked", count: 10)
                        ]) // Placeholder data

                        // Decision Log
                        DecisionLogView(decisions: viewModel.decisionLog)
                    }
                }
            }
            .navigationTitle("")
            .navigationBarHidden(true)
            .task {
                await viewModel.fetchMetrics()
                await viewModel.fetchDecisions()
            }
        }
    }
}

struct MetricSummaryCard: View {
    let title: String
    let value: String

    var body: some View {
        VStack {
            Text(title)
                .font(.caption)
                .foregroundColor(.gray)
            Text(value)
                .font(.title2)
                .fontWeight(.bold)
        }
        .padding()
        .frame(maxWidth: .infinity)
        .background(Color.white)
        .cornerRadius(10)
        .shadow(radius: 1)
    }
}
