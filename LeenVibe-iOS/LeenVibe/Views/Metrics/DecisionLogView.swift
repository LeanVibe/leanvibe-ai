
import SwiftUI

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

            List(filteredDecisions) {
                VStack(alignment: .leading) {
                    Text($0.decision)
                        .font(.subheadline)
                    Text($0.reason)
                        .font(.caption)
                        .foregroundColor(.gray)
                    HStack {
                        Text("Confidence: \($0.confidenceScore, specifier: "%.2f")")
                            .font(.caption2)
                        Spacer()
                        Text($0.timestamp, style: .relative)
                            .font(.caption2)
                    }
                }
            }
        }
        .padding()
    }
}
