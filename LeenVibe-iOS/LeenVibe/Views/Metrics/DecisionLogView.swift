
import SwiftUI

@available(iOS 18.0, macOS 14.0, *)
struct DecisionLogView: View {
    let decisions: [DecisionLog]
    @State private var searchText = ""

    var filteredDecisions: [DecisionLog] {
        if searchText.isEmpty {
            return decisions
        } else {
            return decisions.filter {
                $0.decision.localizedCaseInsensitiveContains(searchText) ||
                $0.reason.localizedCaseInsensitiveContains(searchText)
            }
        }
    }

    var body: some View {
        VStack(alignment: .leading) {
            Text("AI Decision Log")
                .font(.headline)
                .padding(.bottom, 5)

            TextField("Search decisions", text: $searchText)
                .padding(7)
                .background(Color(.systemGray6))
                .cornerRadius(8)
                .padding(.horizontal)

            List(filteredDecisions) { decision in
                VStack(alignment: .leading) {
                    Text(decision.decision)
                        .font(.subheadline)
                    Text(decision.reason)
                        .font(.caption)
                        .foregroundColor(.gray)
                    HStack {
                        Text("Confidence: \(decision.confidenceScore, specifier: "%.2f")")
                            .font(.caption2)
                        Spacer()
                        Text(decision.timestamp, style: .relative)
                            .font(.caption2)
                    }
                }
            }
        }
        .padding()
    }
}
