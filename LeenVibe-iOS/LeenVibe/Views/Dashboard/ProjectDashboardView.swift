import SwiftUI

struct ProjectDashboardView: View {
    @ObservedObject var projectManager: ProjectManager
    @ObservedObject var webSocketService: WebSocketService
    @State private var showingAddProject = false
    
    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                // Header with refresh and add buttons
                headerView
                
                // Main content
                if projectManager.isLoading {
                    loadingView
                } else if projectManager.projects.isEmpty {
                    emptyStateView
                } else {
                    projectsGridView
                }
            }
            .navigationTitle("Projects")
            .navigationBarTitleDisplayMode(.large)
            .refreshable {
                await projectManager.refreshProjects()
                AccessibilityHelper.announcementForAction("Projects refreshed")
            }
            .announceOnChange(projectManager.isLoading) { isLoading in
                isLoading ? "Loading projects" : "Projects loaded"
            }
            .sheet(isPresented: $showingAddProject) {
                AddProjectView(projectManager: projectManager)
            }
        }
    }
    
    private var headerView: some View {
        HStack {
            VStack(alignment: .leading) {
                Text("Active Projects")
                    .font(.headline)
                Text("\(projectManager.projects.count) projects")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
            
            Button("Add Project") {
                showingAddProject = true
            }
            .buttonStyle(.bordered)
            .minimumTouchTarget()
            .accessibleButton(
                label: "Add Project",
                hint: AccessibilityHelper.accessibilityHint(for: .addProject)
            )
            .voiceControlSupport(identifier: "add-project-button", label: "Add Project")
        }
        .padding()
        .background(.ultraThinMaterial)
    }
    
    private var loadingView: some View {
        VStack {
            ProgressView()
            Text("Loading projects...")
                .foregroundColor(.secondary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
    
    private var emptyStateView: some View {
        VStack(spacing: 20) {
            Image(systemName: "folder.badge.plus")
                .font(.system(size: 60))
                .foregroundColor(.blue)
            
            Text("No Projects Yet")
                .font(.title2)
                .fontWeight(.medium)
            
            Text("Add your first project to get started with LeenVibe")
                .font(.body)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
            
            Button("Add First Project") {
                showingAddProject = true
            }
            .buttonStyle(.borderedProminent)
            .minimumTouchTarget()
            .accessibleButton(
                label: "Add First Project",
                hint: "Double tap to create your first project and get started with LeenVibe"
            )
            .voiceControlSupport(identifier: "add-first-project", label: "Add First Project")
        }
        .padding()
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
    
    private var projectsGridView: some View {
        ScrollView {
            LazyVGrid(columns: [
                GridItem(.flexible(), spacing: 16),
                GridItem(.flexible(), spacing: 16)
            ], spacing: 16) {
                ForEach(projectManager.projects) { project in
                    NavigationLink(destination: ProjectDetailView(project: project, projectManager: projectManager)) {
                        ProjectCardView(project: project)
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding()
        }
    }
}

struct ProjectCardView: View {
    let project: Project
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: project.language.icon)
                    .foregroundColor(Color(project.language.color))
                    .font(.title2)
                
                Spacer()
                
                Circle()
                    .fill(Color(project.status.color))
                    .frame(width: 12, height: 12)
            }
            
            VStack(alignment: .leading, spacing: 4) {
                Text(project.name)
                    .font(.headline)
                    .lineLimit(1)
                
                Text(project.language.rawValue)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
            
            VStack(alignment: .leading, spacing: 4) {
                HStack {
                    Text("Health")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    
                    Spacer()
                    
                    Text(project.metrics.healthDescription)
                        .font(.caption)
                        .fontWeight(.medium)
                        .foregroundColor(Color(project.metrics.healthColor))
                }
                
                ProgressView(value: project.metrics.healthScore)
                    .progressViewStyle(LinearProgressViewStyle(tint: Color(project.metrics.healthColor)))
                    .scaleEffect(y: 0.5)
            }
        }
        .padding()
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 12))
        .frame(height: 120)
        .accessibleCard(
            label: AccessibilityHelper.accessibilityLabel(for: project),
            hint: AccessibilityHelper.accessibilityHint(for: .openProject),
            identifier: "project-card-\(project.id)"
        )
        .dynamicTypeSupport()
        .minimumTouchTarget(size: 120)
    }
}

#Preview {
    ProjectDashboardView(
        projectManager: ProjectManager(),
        webSocketService: WebSocketService()
    )
}