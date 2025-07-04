import SwiftUI

@available(iOS 18.0, macOS 14.0, *)
struct ProjectDashboardView: View {
    @ObservedObject var projectManager: ProjectManager
    @ObservedObject var webSocketService: WebSocketService
    @ObservedObject var navigationCoordinator: NavigationCoordinator
    @State private var showingAddProject = false
    @State private var selectedProject: Project?
    
    private let columns = [
        GridItem(.flexible(), spacing: PremiumDesignSystem.Spacing.lg),
        GridItem(.flexible(), spacing: PremiumDesignSystem.Spacing.lg)
    ]
    
    var body: some View {
        NavigationView {
            ScrollView {
                LazyVStack(spacing: PremiumDesignSystem.Spacing.xl) {
                    // Header Section
                    headerSection
                    
                    // Connection Status
                    connectionStatusCard
                    
                    // Projects Grid
                    projectsGridSection
                    
                    // Quick Actions
                    quickActionsSection
                }
                .padding(PremiumDesignSystem.Spacing.containerPadding)
            }
            .navigationTitle("Projects")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: { 
                        PremiumHaptics.contextualFeedback(for: .buttonTap)
                        showingAddProject = true 
                    }) {
                        Image(systemName: "plus.circle.fill")
                            .font(.title2)
                    }
                }
            }
            .refreshable {
                PremiumHaptics.pullToRefresh()
                do {
                    try await projectManager.refreshProjects()
                } catch {
                    // Error is handled by projectManager.lastError
                }
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
        VStack(alignment: .leading, spacing: PremiumDesignSystem.Spacing.md) {
            HStack {
                VStack(alignment: .leading, spacing: PremiumDesignSystem.Spacing.xs) {
                    Text("Dashboard")
                        .font(.title)
                        .fontWeight(.bold)
                    
                    Text("Manage your coding projects")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }
                
                Spacer()
                
                VStack(alignment: .trailing, spacing: PremiumDesignSystem.Spacing.xs) {
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
            if !projectManager.projects.filter({ $0.status == .active }).isEmpty {
                HStack {
                    Circle()
                        .fill(PremiumDesignSystem.Colors.success)
                        .frame(width: PremiumDesignSystem.Spacing.sm, height: PremiumDesignSystem.Spacing.sm)
                    
                    Text("\(projectManager.projects.filter({ $0.status == .active }).count) active project(s)")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    
                    Spacer()
                }
            }
        }
        .padding(PremiumDesignSystem.Spacing.containerPadding)
        .background(PremiumDesignSystem.Colors.secondaryBackground)
        .cornerRadius(PremiumDesignSystem.CornerRadius.card)
    }
    
    private var connectionStatusCard: some View {
        HStack {
            Image(systemName: webSocketService.isConnected ? PremiumDesignSystem.Icons.online : PremiumDesignSystem.Icons.offline)
                .foregroundColor(webSocketService.isConnected ? PremiumDesignSystem.Colors.success : PremiumDesignSystem.Colors.error)
                .font(.title2)
            
            VStack(alignment: .leading, spacing: PremiumDesignSystem.Spacing.xs) {
                Text(webSocketService.isConnected ? "Connected" : "Disconnected")
                    .font(.headline)
                    .foregroundColor(webSocketService.isConnected ? PremiumDesignSystem.Colors.success : PremiumDesignSystem.Colors.error)
                
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
        .padding(PremiumDesignSystem.Spacing.containerPadding)
        .background(PremiumDesignSystem.Colors.background)
        .cornerRadius(PremiumDesignSystem.CornerRadius.card)
        .overlay(
            RoundedRectangle(cornerRadius: PremiumDesignSystem.CornerRadius.card)
                .stroke(webSocketService.isConnected ? PremiumDesignSystem.Colors.success.opacity(0.3) : PremiumDesignSystem.Colors.error.opacity(0.3), lineWidth: 1)
        )
    }
    
    private var projectsGridSection: some View {
        VStack(alignment: .leading, spacing: PremiumDesignSystem.Spacing.lg) {
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
                LazyVGrid(columns: columns, spacing: PremiumDesignSystem.Spacing.lg) {
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
        VStack(spacing: PremiumDesignSystem.Spacing.lg) {
            Image(systemName: "folder.badge.plus")
                .font(.system(size: 48))
                .foregroundColor(.secondary)
            
            Text("No Projects Yet")
                .font(.title2)
                .fontWeight(.semibold)
            
            Text("Connect to your LeanVibe agent and start analyzing your codebase")
                .font(.body)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
            
            Button(action: { showingAddProject = true }) {
                HStack {
                    Image(systemName: "plus")
                    Text("Add Your First Project")
                }
                .padding(PremiumDesignSystem.Spacing.containerPadding)
                .background(PremiumDesignSystem.Colors.buttonPrimary)
                .foregroundColor(.white)
                .cornerRadius(PremiumDesignSystem.CornerRadius.button)
            }
        }
        .padding(PremiumDesignSystem.Spacing.xxxl)
        .background(PremiumDesignSystem.Colors.secondaryBackground)
        .cornerRadius(PremiumDesignSystem.CornerRadius.card)
    }
    
    private var quickActionsSection: some View {
        VStack(alignment: .leading, spacing: PremiumDesignSystem.Spacing.md) {
            Text("Quick Actions")
                .font(.headline)
                .fontWeight(.semibold)
            
            LazyVGrid(columns: columns, spacing: PremiumDesignSystem.Spacing.md) {
                QuickActionCard(
                    title: "Refresh All",
                    icon: "arrow.clockwise",
                    color: PremiumDesignSystem.Colors.buttonPrimary
                ) {
                    Task {
                        do {
                            try await projectManager.refreshProjects()
                        } catch {
                            // Error is handled by projectManager.lastError
                        }
                    }
                }
                
                QuickActionCard(
                    title: "Agent Chat",
                    icon: "brain.head.profile",
                    color: PremiumDesignSystem.Colors.debugBadge
                ) {
                    navigationCoordinator.switchToTab(.agent)
                }
                
                QuickActionCard(
                    title: "Monitor",
                    icon: "chart.line.uptrend.xyaxis",
                    color: PremiumDesignSystem.Colors.success
                ) {
                    navigationCoordinator.switchToTab(.monitor)
                }
                
                QuickActionCard(
                    title: "Settings",
                    icon: "gear",
                    color: PremiumDesignSystem.Colors.iconSecondary
                ) {
                    navigationCoordinator.switchToTab(.settings)
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
            VStack(alignment: .leading, spacing: PremiumDesignSystem.Spacing.md) {
                // Header with language icon and status
                HStack {
                    HStack(spacing: PremiumDesignSystem.Spacing.sm) {
                        Image(systemName: project.language.icon)
                            .foregroundColor(Color(project.language.color))
                            .font(.title2)
                        
                        VStack(alignment: .leading, spacing: PremiumDesignSystem.Spacing.xs) {
                            Text(project.displayName)
                                .font(.headline)
                                .fontWeight(.semibold)
                                .foregroundColor(.primary)
                                .lineLimit(1)
                            
                            Text(project.language.rawValue)
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                    }
                    
                    Spacer()
                    
                    ProjectStatusBadge(status: project.status)
                }
                
                // Metrics row
                HStack(spacing: PremiumDesignSystem.Spacing.lg) {
                    MetricItem(
                        icon: "doc.text",
                        value: "\(project.metrics.filesCount)",
                        label: "Files"
                    )
                    
                    MetricItem(
                        icon: "number",
                        value: "\(project.metrics.linesOfCode)",
                        label: "Lines"
                    )
                    
                    if project.metrics.issuesCount > 0 {
                        MetricItem(
                            icon: "exclamationmark.triangle",
                            value: "\(project.metrics.issuesCount)",
                            label: "Issues",
                            color: PremiumDesignSystem.Colors.error
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
            .padding(PremiumDesignSystem.Spacing.containerPadding)
            .background(PremiumDesignSystem.Colors.background)
            .cornerRadius(PremiumDesignSystem.CornerRadius.card)
            .overlay(
                RoundedRectangle(cornerRadius: PremiumDesignSystem.CornerRadius.card)
                    .stroke(PremiumDesignSystem.Colors.tertiaryBackground, lineWidth: 1)
            )
            .premiumShadow(PremiumDesignSystem.Shadows.card)
        }
        .buttonStyle(PlainButtonStyle())
    }
}

struct ProjectStatusBadge: View {
    let status: ProjectStatus
    
    var body: some View {
        HStack(spacing: PremiumDesignSystem.Spacing.xs) {
            Image(systemName: status.icon)
                .font(.caption)
            
            Text(status.rawValue)
                .font(.caption)
                .fontWeight(.medium)
        }
        .padding(.horizontal, PremiumDesignSystem.Spacing.sm)
        .padding(.vertical, PremiumDesignSystem.Spacing.xs)
        .background(Color(status.color).opacity(0.2))
        .foregroundColor(Color(status.color))
        .cornerRadius(PremiumDesignSystem.CornerRadius.sm)
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct MetricItem: View {
    let icon: String
    let value: String
    let label: String
    var color: Color = .primary
    
    var body: some View {
        VStack(spacing: PremiumDesignSystem.Spacing.xs) {
            HStack(spacing: PremiumDesignSystem.Spacing.xs) {
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

@available(iOS 18.0, macOS 14.0, *)
struct HealthScoreBar: View {
    let score: Double
    
    var body: some View {
        VStack(alignment: .leading, spacing: PremiumDesignSystem.Spacing.xs) {
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
                        .fill(Color.gray.opacity(0.2))
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
        if score >= 0.8 { return "systemGreen" }
        if score >= 0.6 { return "systemYellow" }
        if score >= 0.4 { return "systemOrange" }
        return "systemRed"
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct QuickActionCard: View {
    let title: String
    let icon: String
    let color: Color
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            VStack(spacing: PremiumDesignSystem.Spacing.sm) {
                Image(systemName: icon)
                    .font(.title2)
                    .foregroundColor(color)
                
                Text(title)
                    .font(.caption)
                    .fontWeight(.medium)
                    .foregroundColor(.primary)
            }
            .frame(maxWidth: .infinity)
            .padding(PremiumDesignSystem.Spacing.containerPadding)
            .background(PremiumDesignSystem.Colors.secondaryBackground)
            .cornerRadius(PremiumDesignSystem.CornerRadius.card)
        }
        .buttonStyle(PlainButtonStyle())
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct ProjectDashboardView_Previews: PreviewProvider {
    static var previews: some View {
        ProjectDashboardView(
            projectManager: ProjectManager(),
            webSocketService: WebSocketService(),
            navigationCoordinator: NavigationCoordinator()
        )
    }
}