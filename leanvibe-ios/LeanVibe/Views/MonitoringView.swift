import SwiftUI

@available(iOS 18.0, macOS 14.0, *)
struct MonitoringView: View {
    @ObservedObject var projectManager: ProjectManager
    @ObservedObject var webSocketService: WebSocketService
    @ObservedObject var taskService: TaskService
    
    @State private var selectedProject: Project?
    @State private var showingKanban = false
    
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
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: {
                        // Show Kanban with first active project if available
                        if let activeProject = projectManager.projects.first(where: { $0.status == .active }) {
                            selectedProject = activeProject
                            showingKanban = true
                        }
                    }) {
                        Image(systemName: "kanban")
                            .font(.title2)
                    }
                    .disabled(projectManager.projects.filter({ $0.status == .active }).isEmpty)
                }
            }
            .sheet(isPresented: $showingKanban) {
                if let project = selectedProject {
                    NavigationView {
                        KanbanBoardView(taskService: taskService, projectId: project.id)
                            .navigationTitle("Tasks - \(project.displayName)")
                            .navigationBarTitleDisplayMode(.inline)
                            .toolbar {
                                ToolbarItem(placement: .navigationBarLeading) {
                                    Button("Done") {
                                        showingKanban = false
                                    }
                                }
                            }
                    }
                }
            }
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
            .background({
#if os(iOS)
            return Color(.systemGray6)
#else
            return Color.gray.opacity(0.1)
#endif
        }())
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
                    .background({
#if os(iOS)
            return Color(.systemGray6)
#else
            return Color.gray.opacity(0.1)
#endif
        }())
                    .cornerRadius(12)
            } else {
                ForEach(projectManager.projects.filter({ $0.status == .active }), id: \.id) { project in
                    Button(action: {
                        selectedProject = project
                        showingKanban = true
                    }) {
                        HStack {
                            Image(systemName: project.language.icon)
                                .foregroundColor(colorFromString(project.language.color))
                            
                            VStack(alignment: .leading) {
                                Text(project.displayName)
                                    .font(.headline)
                                    .foregroundColor(.primary)
                                Text(project.language.rawValue)
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                            
                            Spacer()
                            
                            VStack(alignment: .trailing) {
                                Text("\(project.metrics.filesCount) files")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                                Text("Tap for tasks")
                                    .font(.caption2)
                                    .foregroundColor(.blue)
                            }
                            
                            Image(systemName: "chevron.right")
                                .foregroundColor(.secondary)
                                .font(.caption)
                        }
                        .padding()
                        .background({
#if os(iOS)
            return Color(.systemGray6)
#else
            return Color.gray.opacity(0.1)
#endif
        }())
                        .cornerRadius(12)
                    }
                    .buttonStyle(PlainButtonStyle())
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

@available(iOS 18.0, macOS 14.0, *)
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
        .background({
#if os(iOS)
            return Color(.systemGray6)
#else
            return Color.gray.opacity(0.1)
#endif
        }())
        .cornerRadius(12)
    }
}

#Preview {
    MonitoringView(
        projectManager: ProjectManager(),
        webSocketService: WebSocketService(),
        taskService: TaskService()
    )
}