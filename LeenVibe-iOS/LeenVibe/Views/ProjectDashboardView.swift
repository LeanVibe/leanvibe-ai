import SwiftUI

struct ProjectDashboardView: View {
    @ObservedObject var projectManager: ProjectManager
    @ObservedObject var webSocketService: WebSocketService
    @State private var showingAddProject = false
    @State private var selectedProject: Project?
    
    private let columns = [
        GridItem(.flexible(), spacing: 16),
        GridItem(.flexible(), spacing: 16)
    ]
    
    var body: some View {
        NavigationView {
            ScrollView {
                LazyVStack(spacing: 20) {
                    // Header Section
                    headerSection
                    
                    // Connection Status
                    connectionStatusCard
                    
                    // Projects Grid
                    projectsGridSection
                    
                    // Quick Actions
                    quickActionsSection
                }
                .padding()
            }
            .navigationTitle("Projects")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: { showingAddProject = true }) {
                        Image(systemName: "plus.circle.fill")
                            .font(.title2)
                    }
                }
            }
            .refreshable {
                await projectManager.refreshProjects()
            }
            .sheet(isPresented: $showingAddProject) {
                AddProjectView(projectManager: projectManager)
            }
            .sheet(item: $selectedProject) { project in
                ProjectDetailView(
                    project: project,
                    projectManager: projectManager,
                    webSocketService: webSocketService
                )
            }
        }
    }
    
    private var headerSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Dashboard")
                        .font(.title)
                        .fontWeight(.bold)
                    
                    Text("Manage your coding projects")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }
                
                Spacer()
                
                VStack(alignment: .trailing, spacing: 4) {
                    Text("\(projectManager.projects.count)")
                        .font(.title2)
                        .fontWeight(.semibold)
                        .foregroundColor(.primary)
                    
                    Text("Projects")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
            
            // Active projects summary
            if !projectManager.getActiveProjects().isEmpty {
                HStack {
                    Circle()
                        .fill(Color.green)
                        .frame(width: 8, height: 8)
                    
                    Text("\(projectManager.getActiveProjects().count) active project(s)")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    
                    Spacer()
                }
            }
        }
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(16)
    }
    
    private var connectionStatusCard: some View {
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
            
            if projectManager.isLoading {
                ProgressView()
                    .scaleEffect(0.8)
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(12)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(webSocketService.isConnected ? Color.green.opacity(0.3) : Color.red.opacity(0.3), lineWidth: 1)
        )
    }
    
    private var projectsGridSection: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                Text("Projects")
                    .font(.title2)
                    .fontWeight(.semibold)
                
                Spacer()
                
                if projectManager.isLoading {
                    ProgressView()
                        .scaleEffect(0.8)
                }
            }
            
            if projectManager.projects.isEmpty {
                emptyProjectsView
            } else {
                LazyVGrid(columns: columns, spacing: 16) {
                    ForEach(projectManager.projects) { project in
                        ProjectCard(project: project) {
                            selectedProject = project
                        }
                    }
                }
            }
        }
    }
    
    private var emptyProjectsView: some View {
        VStack(spacing: 16) {
            Image(systemName: "folder.badge.plus")
                .font(.system(size: 48))
                .foregroundColor(.secondary)
            
            Text("No Projects Yet")
                .font(.title2)
                .fontWeight(.semibold)
            
            Text("Connect to your LeenVibe agent and start analyzing your codebase")
                .font(.body)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
            
            Button(action: { showingAddProject = true }) {
                HStack {
                    Image(systemName: "plus")
                    Text("Add Your First Project")
                }
                .padding()
                .background(Color.blue)
                .foregroundColor(.white)
                .cornerRadius(12)
            }
        }
        .padding(40)
        .background(Color(.systemGray6))
        .cornerRadius(16)
    }
    
    private var quickActionsSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Quick Actions")
                .font(.headline)
                .fontWeight(.semibold)
            
            LazyVGrid(columns: columns, spacing: 12) {
                QuickActionCard(
                    title: "Refresh All",
                    icon: "arrow.clockwise",
                    color: .blue
                ) {
                    Task {
                        await projectManager.refreshProjects()
                    }
                }
                
                QuickActionCard(
                    title: "Agent Chat",
                    icon: "brain.head.profile",
                    color: .purple
                ) {
                    // Navigate to chat tab
                }
                
                QuickActionCard(
                    title: "Monitor",
                    icon: "chart.line.uptrend.xyaxis",
                    color: .green
                ) {
                    // Navigate to monitoring tab
                }
                
                QuickActionCard(
                    title: "Settings",
                    icon: "gear",
                    color: .gray
                ) {
                    // Navigate to settings tab
                }
            }
        }
    }
}

struct ProjectCard: View {
    let project: Project
    let onTap: () -> Void
    
    var body: some View {
        Button(action: onTap) {
            VStack(alignment: .leading, spacing: 12) {
                // Header with language icon and status
                HStack {
                    HStack(spacing: 8) {
                        Image(systemName: project.language.iconName)
                            .foregroundColor(Color(project.language.color))
                            .font(.title2)
                        
                        VStack(alignment: .leading, spacing: 2) {
                            Text(project.displayName)
                                .font(.headline)
                                .fontWeight(.semibold)
                                .foregroundColor(.primary)
                                .lineLimit(1)
                            
                            Text(project.language.displayName)
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                    }
                    
                    Spacer()
                    
                    StatusBadge(status: project.status)
                }
                
                // Metrics row
                HStack(spacing: 16) {
                    MetricItem(
                        icon: "doc.text",
                        value: "\(project.metrics.fileCount)",
                        label: "Files"
                    )
                    
                    MetricItem(
                        icon: "number",
                        value: "\(project.metrics.lineCount)",
                        label: "Lines"
                    )
                    
                    if project.metrics.issueCount > 0 {
                        MetricItem(
                            icon: "exclamationmark.triangle",
                            value: "\(project.metrics.issueCount)",
                            label: "Issues",
                            color: .red
                        )
                    }
                }
                
                // Health score
                HealthScoreBar(score: project.metrics.healthScore)
                
                // Last activity
                HStack {
                    Text("Last activity:")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    
                    Text(project.lastActivity, style: .relative)
                        .font(.caption)
                        .foregroundColor(.secondary)
                    
                    Spacer()
                }
            }
            .padding()
            .background(Color(.systemBackground))
            .cornerRadius(16)
            .overlay(
                RoundedRectangle(cornerRadius: 16)
                    .stroke(Color(.systemGray4), lineWidth: 1)
            )
            .shadow(color: .black.opacity(0.05), radius: 8, x: 0, y: 2)
        }
        .buttonStyle(PlainButtonStyle())
    }
}

struct StatusBadge: View {
    let status: ProjectStatus
    
    var body: some View {
        HStack(spacing: 4) {
            Image(systemName: status.iconName)
                .font(.caption)
            
            Text(status.displayName)
                .font(.caption)
                .fontWeight(.medium)
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(Color(status.color).opacity(0.2))
        .foregroundColor(Color(status.color))
        .cornerRadius(8)
    }
}

struct MetricItem: View {
    let icon: String
    let value: String
    let label: String
    var color: Color = .primary
    
    var body: some View {
        VStack(spacing: 2) {
            HStack(spacing: 4) {
                Image(systemName: icon)
                    .font(.caption)
                    .foregroundColor(color)
                
                Text(value)
                    .font(.caption)
                    .fontWeight(.semibold)
                    .foregroundColor(color)
            }
            
            Text(label)
                .font(.caption2)
                .foregroundColor(.secondary)
        }
    }
}

struct HealthScoreBar: View {
    let score: Double
    
    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text("Health")
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                Spacer()
                
                Text("\(Int(score * 100))%")
                    .font(.caption)
                    .fontWeight(.medium)
                    .foregroundColor(Color(healthColor))
            }
            
            GeometryReader { geometry in
                ZStack(alignment: .leading) {
                    Rectangle()
                        .fill(Color(.systemGray5))
                        .frame(height: 4)
                        .cornerRadius(2)
                    
                    Rectangle()
                        .fill(Color(healthColor))
                        .frame(width: geometry.size.width * score, height: 4)
                        .cornerRadius(2)
                }
            }
            .frame(height: 4)
        }
    }
    
    private var healthColor: String {
        if score >= 0.8 { return "green" }
        if score >= 0.6 { return "yellow" }
        if score >= 0.4 { return "orange" }
        return "red"
    }
}

struct QuickActionCard: View {
    let title: String
    let icon: String
    let color: Color
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            VStack(spacing: 8) {
                Image(systemName: icon)
                    .font(.title2)
                    .foregroundColor(color)
                
                Text(title)
                    .font(.caption)
                    .fontWeight(.medium)
                    .foregroundColor(.primary)
            }
            .frame(maxWidth: .infinity)
            .padding()
            .background(Color(.systemGray6))
            .cornerRadius(12)
        }
        .buttonStyle(PlainButtonStyle())
    }
}

struct ProjectDashboardView_Previews: PreviewProvider {
    static var previews: some View {
        ProjectDashboardView(project: .constant(Project.mock()))
    }
}