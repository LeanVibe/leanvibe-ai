import SwiftUI

struct MonitoringView: View {
    @ObservedObject var projectManager: ProjectManager
    @ObservedObject var webSocketService: WebSocketService
    
    private func colorFromString(_ colorName: String) -> Color {
        switch colorName {
        case "orange": return .orange
        case "yellow": return .yellow
        case "blue": return .blue
        case "purple": return .purple
        case "red": return .red
        case "green": return .green
        case "pink": return .pink
        case "gray": return .gray
        default: return .gray
        }
    }
    
    var body: some View {
        NavigationView {
            ScrollView {
                LazyVStack(spacing: 16) {
                    // Connection Status
                    connectionStatusSection
                    
                    // Active Projects
                    activeProjectsSection
                    
                    // System Metrics (placeholder)
                    systemMetricsSection
                }
                .padding()
            }
            .navigationTitle("Monitor")
            .navigationBarTitleDisplayMode(.large)
        }
    }
    
    private var connectionStatusSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Connection Status")
                .font(.headline)
                .fontWeight(.semibold)
            
            HStack {
                Image(systemName: webSocketService.isConnected ? "wifi" : "wifi.slash")
                    .foregroundColor(webSocketService.isConnected ? .green : .red)
                    .font(.title2)
                
                VStack(alignment: .leading, spacing: 4) {
                    Text(webSocketService.isConnected ? "Connected" : "Disconnected")
                        .font(.headline)
                        .foregroundColor(webSocketService.isConnected ? .green : .red)
                    
                    Text(webSocketService.connectionStatus)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                
                Spacer()
            }
            .padding()
            .background(Color(.systemGray6))
            .cornerRadius(12)
        }
    }
    
    private var activeProjectsSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Active Projects")
                .font(.headline)
                .fontWeight(.semibold)
            
            if projectManager.projects.filter({ $0.status == .active }).isEmpty {
                Text("No active projects")
                    .foregroundColor(.secondary)
                    .padding()
                    .frame(maxWidth: .infinity)
                    .background(Color(.systemGray6))
                    .cornerRadius(12)
            } else {
                ForEach(projectManager.projects.filter({ $0.status == .active }), id: \.id) { project in
                    HStack {
                        Image(systemName: project.language.icon)
                            .foregroundColor(colorFromString(project.language.color))
                        
                        VStack(alignment: .leading) {
                            Text(project.name)
                                .font(.headline)
                            Text(project.language.rawValue)
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                        
                        Spacer()
                        
                        Text("\(project.metrics.fileCount) files")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    .padding()
                    .background(Color(.systemGray6))
                    .cornerRadius(12)
                }
            }
        }
    }
    
    private var systemMetricsSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("System Status")
                .font(.headline)
                .fontWeight(.semibold)
            
            LazyVGrid(columns: [
                GridItem(.flexible()),
                GridItem(.flexible())
            ], spacing: 12) {
                MetricCard(title: "Messages", value: "\(webSocketService.messages.count)", unit: "", color: .blue, trend: .stable, icon: "message.fill")
                MetricCard(title: "Projects", value: "\(projectManager.projects.count)", unit: "", color: .blue, trend: .stable, icon: "folder.fill")
            }
        }
    }
}

struct MonitoringMetricCard: View {
    let title: String
    let value: String
    let icon: String
    
    var body: some View {
        VStack(spacing: 8) {
            Image(systemName: icon)
                .font(.title2)
                .foregroundColor(.blue)
            
            Text(value)
                .font(.title2)
                .fontWeight(.bold)
            
            Text(title)
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .frame(maxWidth: .infinity)
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(12)
    }
}

#Preview {
    MonitoringView(
        projectManager: ProjectManager(),
        webSocketService: WebSocketService()
    )
}