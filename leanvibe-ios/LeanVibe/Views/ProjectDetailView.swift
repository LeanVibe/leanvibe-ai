import SwiftUI

@available(iOS 18.0, macOS 14.0, *)
struct ProjectDetailView: View {
    let project: Project
    @ObservedObject var projectManager: ProjectManager
    @ObservedObject var webSocketService: WebSocketService
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            ScrollView {
                LazyVStack(spacing: 20) {
                    // Project Header
                    projectHeaderSection
                    
                    // Metrics Section
                    projectMetricsSection
                    
                    // Actions Section
                    projectActionsSection
                }
                .padding()
            }
            .navigationTitle(project.displayName)
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Done") {
                        dismiss()
                    }
                }
            }
        }
    }
    
    private var projectHeaderSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: project.language.icon)
                    .foregroundColor(Color(project.language.color))
                    .font(.largeTitle)
                
                VStack(alignment: .leading, spacing: 4) {
                    Text(project.displayName)
                        .font(.title)
                        .fontWeight(.bold)
                    
                    Text(project.language.rawValue)
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }
                
                Spacer()
                
                ProjectStatusBadge(status: project.status)
            }
            
            Text(project.path)
                .font(.caption)
                .foregroundColor(.secondary)
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
                .background(Color(.systemGray6))
                .cornerRadius(8)
        }
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(16)
    }
    
    private var projectMetricsSection: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Project Metrics")
                .font(.headline)
                .fontWeight(.semibold)
            
            LazyVGrid(columns: [
                GridItem(.flexible()),
                GridItem(.flexible())
            ], spacing: 12) {
                MetricDetailCard(
                    title: "Files",
                    value: "\(project.metrics.filesCount)",
                    icon: "doc.text",
                    color: .blue
                )
                
                MetricDetailCard(
                    title: "Lines of Code",
                    value: "\(project.metrics.linesOfCode)",
                    icon: "number",
                    color: .green
                )
                
                MetricDetailCard(
                    title: "Health Score",
                    value: String(format: "%.1f%%", project.metrics.healthScore * 100),
                    icon: "heart.fill",
                    color: Color(project.metrics.healthColor)
                )
                
                MetricDetailCard(
                    title: "Issues",
                    value: "\(project.metrics.issuesCount)",
                    icon: "exclamationmark.triangle",
                    color: project.metrics.issuesCount > 0 ? .red : .gray
                )
            }
            
            // Health Score
            VStack(alignment: .leading, spacing: 8) {
                Text("Health Score")
                    .font(.subheadline)
                    .fontWeight(.medium)
                
                HealthScoreBar(score: project.metrics.healthScore)
            }
            .padding()
            .background(Color(.systemGray6))
            .cornerRadius(12)
        }
    }
    
    private var projectActionsSection: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Actions")
                .font(.headline)
                .fontWeight(.semibold)
            
            VStack(spacing: 12) {
                ProjectActionButton(
                    title: "Analyze Project",
                    icon: "magnifyingglass",
                    color: .blue,
                    isEnabled: webSocketService.isConnected
                ) {
                    Task {
                        await projectManager.analyzeProject(project)
                    }
                }
                
                ProjectActionButton(
                    title: "Open in Agent Chat",
                    icon: "brain.head.profile",
                    color: .purple,
                    isEnabled: webSocketService.isConnected
                ) {
                    webSocketService.sendCommand("/analyze-project \(project.path)")
                    dismiss()
                }
                
                ProjectActionButton(
                    title: "Remove Project",
                    icon: "trash",
                    color: .red,
                    isEnabled: true
                ) {
                    Task {
                        do {
                            try await projectManager.removeProject(project)
                            await MainActor.run {
                                dismiss()
                            }
                        } catch {
                            print("Failed to remove project: \(error)")
                        }
                    }
                }
            }
        }
    }
}

struct MetricDetailCard: View {
    let title: String
    let value: String
    let icon: String
    let color: Color
    
    var body: some View {
        VStack(spacing: 8) {
            Image(systemName: icon)
                .font(.title2)
                .foregroundColor(color)
            
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

struct ProjectActionButton: View {
    let title: String
    let icon: String
    let color: Color
    let isEnabled: Bool
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            HStack {
                Image(systemName: icon)
                    .font(.body)
                
                Text(title)
                    .font(.body)
                    .fontWeight(.medium)
                
                Spacer()
            }
            .padding()
            .background(isEnabled ? color.opacity(0.1) : Color(.systemGray5))
            .foregroundColor(isEnabled ? color : .gray)
            .cornerRadius(12)
        }
        .disabled(!isEnabled)
    }
}

#Preview {
    ProjectDetailView(
        project: Project(
            displayName: "Sample Project",
            path: "/path/to/project",
            language: .swift
        ),
        projectManager: ProjectManager(),
        webSocketService: WebSocketService()
    )
}