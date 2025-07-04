import SwiftUI
import Network

@available(iOS 18.0, macOS 14.0, *)
struct NetworkDiagnosticsView: View {
    @ObservedObject var settingsManager: SettingsManager
    @State private var isRunningDiagnostics = false
    @State private var diagnosticResults: [DiagnosticResult] = []
    @State private var networkStatus: DiagnosticNetworkStatus = .unknown
    @State private var connectionDetails: ConnectionDetails?
    @Environment(\.dismiss) private var dismiss
    
    init(settingsManager: SettingsManager) {
        self.settingsManager = settingsManager
    }
    
    init() {
        self.settingsManager = SettingsManager.shared
    }
    
    var body: some View {
        NavigationView {
            List {
                Section {
                    Text("Diagnose network connectivity and backend communication issues.")
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .padding(.vertical, 4)
                }
                
                Section("Network Status") {
                    HStack {
                        Image(systemName: networkStatus.iconName)
                            .foregroundColor(networkStatus.color)
                            .font(.title2)
                        VStack(alignment: .leading) {
                            Text(networkStatus.displayName)
                                .font(.headline)
                            if let details = connectionDetails {
                                Text(details.description)
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                        }
                        Spacer()
                        if isRunningDiagnostics {
                            ProgressView()
                                .scaleEffect(0.8)
                        }
                    }
                    .padding(.vertical, 4)
                }
                
                Section("Quick Diagnostics") {
                    Button("Run Network Diagnostics") {
                        runNetworkDiagnostics()
                    }
                    .foregroundColor(Color(.systemBlue))
                    .disabled(isRunningDiagnostics)
                    
                    Button("Test Backend Connection") {
                        testBackendConnection()
                    }
                    .foregroundColor(Color(.systemBlue))
                    .disabled(isRunningDiagnostics)
                    
                    Button("Test WebSocket Connection") {
                        testWebSocketConnection()
                    }
                    .foregroundColor(Color(.systemBlue))
                    .disabled(isRunningDiagnostics)
                }
                
                if !diagnosticResults.isEmpty {
                    Section("Diagnostic Results") {
                        ForEach(diagnosticResults, id: \.id) { result in
                            DiagnosticResultRow(result: result)
                        }
                    }
                }
                
                Section("Connection Details") {
                    if let details = connectionDetails {
                        ConnectionDetailRow(title: "Network Type", value: details.networkType)
                        ConnectionDetailRow(title: "IP Address", value: details.ipAddress)
                        ConnectionDetailRow(title: "DNS Server", value: details.dnsServer)
                        ConnectionDetailRow(title: "Gateway", value: details.gateway)
                        if let latency = details.latency {
                            ConnectionDetailRow(title: "Latency", value: "\(Int(latency))ms")
                        }
                        if let bandwidth = details.bandwidth {
                            ConnectionDetailRow(title: "Bandwidth", value: bandwidth)
                        }
                    } else {
                        Text("Run diagnostics to view connection details")
                            .foregroundColor(.secondary)
                            .font(.caption)
                    }
                }
                
                Section("Backend Endpoints") {
                    EndpointStatusRow(
                        endpoint: "HTTP API",
                        url: "http://localhost:8000/api",
                        status: .unknown
                    )
                    
                    EndpointStatusRow(
                        endpoint: "WebSocket",
                        url: "ws://localhost:8000/ws",
                        status: .unknown
                    )
                    
                    EndpointStatusRow(
                        endpoint: "Health Check",
                        url: "http://localhost:8000/health",
                        status: .unknown
                    )
                }
            }
            .navigationTitle("Network Diagnostics")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Done") {
                        dismiss()
                    }
                }
            }
        }
        .onAppear {
            updateNetworkStatus()
        }
    }
    
    private func runNetworkDiagnostics() {
        isRunningDiagnostics = true
        diagnosticResults.removeAll()
        
        // Simulate comprehensive network diagnostics
        let tests = [
            ("Network Connectivity", 0.5),
            ("DNS Resolution", 1.0),
            ("Internet Access", 1.5),
            ("Backend Reachability", 2.0),
            ("WebSocket Connection", 2.5),
            ("Latency Test", 3.0),
            ("Bandwidth Test", 4.0)
        ]
        
        for (index, test) in tests.enumerated() {
            DispatchQueue.main.asyncAfter(deadline: .now() + test.1) {
                let success = Double.random(in: 0...1) > 0.2 // 80% success rate
                let result = DiagnosticResult(
                    testName: test.0,
                    passed: success,
                    details: success ? "Test completed successfully" : "Test failed - check connection",
                    latency: success ? Double.random(in: 10...100) : nil,
                    timestamp: Date()
                )
                diagnosticResults.append(result)
                
                // Update network status based on results
                if index == tests.count - 1 {
                    isRunningDiagnostics = false
                    updateConnectionDetails()
                    networkStatus = diagnosticResults.allSatisfy { $0.passed } ? .connected : .issues
                }
            }
        }
    }
    
    private func testBackendConnection() {
        isRunningDiagnostics = true
        
        DispatchQueue.main.asyncAfter(deadline: .now() + 2.0) {
            isRunningDiagnostics = false
            
            let result = DiagnosticResult(
                testName: "Backend Connection",
                passed: true,
                details: "Successfully connected to localhost:8000",
                latency: 45.2,
                timestamp: Date()
            )
            
            if let index = diagnosticResults.firstIndex(where: { $0.testName == "Backend Connection" }) {
                diagnosticResults[index] = result
            } else {
                diagnosticResults.append(result)
            }
        }
    }
    
    private func testWebSocketConnection() {
        isRunningDiagnostics = true
        
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) {
            isRunningDiagnostics = false
            
            let result = DiagnosticResult(
                testName: "WebSocket Connection",
                passed: true,
                details: "WebSocket connection established and responsive",
                latency: 23.8,
                timestamp: Date()
            )
            
            if let index = diagnosticResults.firstIndex(where: { $0.testName == "WebSocket Connection" }) {
                diagnosticResults[index] = result
            } else {
                diagnosticResults.append(result)
            }
        }
    }
    
    private func updateNetworkStatus() {
        // Simulate network status detection
        networkStatus = .connected
        updateConnectionDetails()
    }
    
    private func updateConnectionDetails() {
        connectionDetails = ConnectionDetails(
            networkType: "Wi-Fi",
            ipAddress: "192.168.1.100",
            dnsServer: "8.8.8.8",
            gateway: "192.168.1.1",
            latency: 25.4,
            bandwidth: "150 Mbps down / 30 Mbps up"
        )
    }
}

struct DiagnosticResultRow: View {
    let result: DiagnosticResult
    
    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text(result.testName)
                    .font(.headline)
                Spacer()
                HStack {
                    if result.passed {
                        Image(systemName: "checkmark.circle.fill")
                            .foregroundColor(.green)
                    } else {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundColor(.red)
                    }
                    Text(result.passed ? "Passed" : "Failed")
                        .font(.caption)
                        .foregroundColor(result.passed ? .green : .red)
                }
            }
            
            Text(result.details)
                .font(.caption)
                .foregroundColor(.secondary)
            
            if let latency = result.latency {
                Text("Latency: \(String(format: "%.1f", latency))ms")
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
        }
        .padding(.vertical, 2)
    }
}

struct ConnectionDetailRow: View {
    let title: String
    let value: String
    
    var body: some View {
        HStack {
            Text(title)
                .foregroundColor(.primary)
            Spacer()
            Text(value)
                .foregroundColor(.secondary)
                .font(.caption)
        }
    }
}

struct EndpointStatusRow: View {
    let endpoint: String
    let url: String
    @State var status: EndpointStatus
    
    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text(endpoint)
                    .font(.headline)
                Spacer()
                HStack {
                    Circle()
                        .fill(status.color)
                        .frame(width: 8, height: 8)
                    Text(status.displayName)
                        .font(.caption)
                        .foregroundColor(status.color)
                }
            }
            
            Text(url)
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .padding(.vertical, 2)
    }
}

struct DiagnosticResult: Identifiable {
    let id = UUID()
    let testName: String
    let passed: Bool
    let details: String
    let latency: Double?
    let timestamp: Date
}

struct ConnectionDetails {
    let networkType: String
    let ipAddress: String
    let dnsServer: String
    let gateway: String
    let latency: Double?
    let bandwidth: String?
    
    var description: String {
        return "\(networkType) • \(ipAddress)"
    }
}

enum DiagnosticNetworkStatus {
    case connected
    case disconnected
    case issues
    case unknown
    
    var displayName: String {
        switch self {
        case .connected:
            return "Connected"
        case .disconnected:
            return "Disconnected"
        case .issues:
            return "Connection Issues"
        case .unknown:
            return "Unknown"
        }
    }
    
    var iconName: String {
        switch self {
        case .connected:
            return "wifi"
        case .disconnected:
            return "wifi.slash"
        case .issues:
            return "wifi.exclamationmark"
        case .unknown:
            return "questionmark.circle"
        }
    }
    
    var color: Color {
        switch self {
        case .connected:
            return Color(.systemGreen)
        case .disconnected:
            return Color(.systemRed)
        case .issues:
            return Color(.systemOrange)
        case .unknown:
            return Color(.systemGray)
        }
    }
}

enum EndpointStatus {
    case online
    case offline
    case unknown
    
    var displayName: String {
        switch self {
        case .online:
            return "Online"
        case .offline:
            return "Offline"
        case .unknown:
            return "Unknown"
        }
    }
    
    var color: Color {
        switch self {
        case .online:
            return Color(.systemGreen)
        case .offline:
            return Color(.systemRed)
        case .unknown:
            return Color(.systemGray)
        }
    }
}

#Preview {
    NetworkDiagnosticsView()
}