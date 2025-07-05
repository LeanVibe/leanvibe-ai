import SwiftUI

/// Comprehensive task dependency visualization and management view
@available(iOS 18.0, macOS 14.0, *)
struct TaskDependencyView: View {
    @ObservedObject var taskService: TaskService
    let projectId: UUID
    @Environment(\.dismiss) private var dismiss
    
    @State private var selectedTask: LeanVibeTask?
    @State private var showingDependencyGraph = false
    @State private var dependencyFilter: DependencyFilter = .all
    @State private var searchText = ""
    @State private var showingAddDependency = false
    
    enum DependencyFilter: String, CaseIterable {
        case all = "All Tasks"
        case withDependencies = "Has Dependencies"
        case noDependencies = "No Dependencies"
        case blocked = "Blocked Tasks"
        case blocking = "Blocking Tasks"
        
        var systemImage: String {
            switch self {
            case .all: return "list.bullet"
            case .withDependencies: return "arrow.triangle.branch"
            case .noDependencies: return "circle"
            case .blocked: return "exclamationmark.triangle"
            case .blocking: return "stop.circle"
            }
        }
    }
    
    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                // Filter Section
                filterSection
                
                // Dependency Overview
                dependencyOverviewSection
                
                // Tasks List with Dependencies
                taskListSection
            }
            .navigationTitle("Task Dependencies")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Done") {
                        dismiss()
                    }
                }
                
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: { showingDependencyGraph = true }) {
                        Image(systemName: "network")
                    }
                }
            }
        }
        .sheet(isPresented: $showingDependencyGraph) {
            TaskDependencyGraphView(taskService: taskService, projectId: projectId)
        }
        .sheet(isPresented: $showingAddDependency) {
            if let task = selectedTask {
                AddTaskDependencyView(
                    task: task,
                    availableTasks: availableTasksForDependency(task: task),
                    onDependencyAdded: { dependencyId in
                        addDependency(to: task, dependencyId: dependencyId)
                    }
                )
            }
        }
    }
    
    // MARK: - View Sections
    
    private var filterSection: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 12) {
                ForEach(DependencyFilter.allCases, id: \.self) { filter in
                    FilterChip(
                        title: filter.rawValue,
                        systemImage: filter.systemImage,
                        isSelected: dependencyFilter == filter,
                        onTap: { dependencyFilter = filter }
                    )
                }
            }
            .padding(.horizontal)
        }
        .padding(.vertical, 8)
    }
    
    private var dependencyOverviewSection: some View {
        VStack(spacing: 12) {
            HStack(spacing: 20) {
                DependencyMetricCard(
                    title: "Total Dependencies",
                    value: "\(totalDependencyCount)",
                    systemImage: "arrow.triangle.branch",
                    color: .blue
                )
                
                DependencyMetricCard(
                    title: "Blocked Tasks",
                    value: "\(blockedTasksCount)",
                    systemImage: "exclamationmark.triangle",
                    color: .orange
                )
                
                DependencyMetricCard(
                    title: "Ready Tasks",
                    value: "\(readyTasksCount)",
                    systemImage: "checkmark.circle",
                    color: .green
                )
            }
            
            if criticalPathTasks.count > 0 {
                CriticalPathIndicator(tasks: criticalPathTasks)
            }
        }
        .padding(.horizontal)
        .padding(.bottom)
    }
    
    private var taskListSection: some View {
        List {
            ForEach(filteredTasks, id: \.id) { task in
                TaskDependencyRow(
                    task: task,
                    dependentTasks: getDependentTasks(for: task),
                    blockingTasks: getBlockingTasks(for: task),
                    onTaskTap: { selectedTask = task },
                    onAddDependency: {
                        selectedTask = task
                        showingAddDependency = true
                    },
                    onRemoveDependency: { dependencyId in
                        removeDependency(from: task, dependencyId: dependencyId)
                    }
                )
            }
        }
        .listStyle(.plain)
        .searchable(text: $searchText, prompt: "Search tasks...")
    }
    
    // MARK: - Computed Properties
    
    private var filteredTasks: [LeanVibeTask] {
        let projectTasks = taskService.tasks.filter { $0.projectId == projectId }
        
        var filtered: [LeanVibeTask]
        
        switch dependencyFilter {
        case .all:
            filtered = projectTasks
        case .withDependencies:
            filtered = projectTasks.filter { !$0.dependencies.isEmpty }
        case .noDependencies:
            filtered = projectTasks.filter { $0.dependencies.isEmpty }
        case .blocked:
            filtered = projectTasks.filter { isTaskBlocked($0) }
        case .blocking:
            filtered = projectTasks.filter { isTaskBlocking($0) }
        }
        
        if !searchText.isEmpty {
            filtered = filtered.filter { task in
                task.title.localizedCaseInsensitiveContains(searchText) ||
                task.description?.localizedCaseInsensitiveContains(searchText) == true
            }
        }
        
        return filtered.sorted { $0.priority.rawValue > $1.priority.rawValue }
    }
    
    private var totalDependencyCount: Int {
        return taskService.tasks
            .filter { $0.projectId == projectId }
            .reduce(0) { $0 + $1.dependencies.count }
    }
    
    private var blockedTasksCount: Int {
        return taskService.tasks
            .filter { $0.projectId == projectId }
            .filter { isTaskBlocked($0) }
            .count
    }
    
    private var readyTasksCount: Int {
        return taskService.tasks
            .filter { $0.projectId == projectId }
            .filter { $0.status == .todo && !isTaskBlocked($0) }
            .count
    }
    
    private var criticalPathTasks: [LeanVibeTask] {
        // Simplified critical path detection - tasks with most dependencies
        return taskService.tasks
            .filter { $0.projectId == projectId }
            .filter { $0.dependencies.count >= 2 }
            .sorted { $0.dependencies.count > $1.dependencies.count }
            .prefix(3)
            .map { $0 }
    }
    
    // MARK: - Helper Methods
    
    private func isTaskBlocked(_ task: LeanVibeTask) -> Bool {
        return !task.dependencies.isEmpty && 
               task.dependencies.contains { dependencyId in
                   let dependentTask = taskService.tasks.first { $0.id == dependencyId }
                   return dependentTask?.status != .done
               }
    }
    
    private func isTaskBlocking(_ task: LeanVibeTask) -> Bool {
        return taskService.tasks.contains { otherTask in
            otherTask.dependencies.contains(task.id) && otherTask.status != .done
        }
    }
    
    private func getDependentTasks(for task: LeanVibeTask) -> [LeanVibeTask] {
        return task.dependencies.compactMap { dependencyId in
            taskService.tasks.first { $0.id == dependencyId }
        }
    }
    
    private func getBlockingTasks(for task: LeanVibeTask) -> [LeanVibeTask] {
        return taskService.tasks.filter { otherTask in
            otherTask.dependencies.contains(task.id)
        }
    }
    
    private func availableTasksForDependency(task: LeanVibeTask) -> [LeanVibeTask] {
        return taskService.tasks.filter { candidateTask in
            candidateTask.projectId == projectId &&
            candidateTask.id != task.id &&
            !task.dependencies.contains(candidateTask.id) &&
            !candidateTask.dependencies.contains(task.id) // Prevent circular dependencies
        }
    }
    
    private func addDependency(to task: LeanVibeTask, dependencyId: UUID) {
        var updatedTask = task
        updatedTask.dependencies.append(dependencyId)
        updatedTask.updatedAt = Date()
        
        Task {
            try? await taskService.updateTask(updatedTask)
        }
    }
    
    private func removeDependency(from task: LeanVibeTask, dependencyId: UUID) {
        var updatedTask = task
        updatedTask.dependencies.removeAll { $0 == dependencyId }
        updatedTask.updatedAt = Date()
        
        Task {
            try? await taskService.updateTask(updatedTask)
        }
    }
}

// MARK: - Supporting Views

@available(iOS 18.0, macOS 14.0, *)
struct FilterChip: View {
    let title: String
    let systemImage: String
    let isSelected: Bool
    let onTap: () -> Void
    
    var body: some View {
        Button(action: onTap) {
            HStack(spacing: 6) {
                Image(systemName: systemImage)
                    .font(.caption)
                Text(title)
                    .font(.caption)
                    .fontWeight(.medium)
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
            .background(
                RoundedRectangle(cornerRadius: 20)
                    .fill(isSelected ? Color.blue : Color(.systemGray5))
            )
            .foregroundColor(isSelected ? .white : .primary)
        }
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct DependencyMetricCard: View {
    let title: String
    let value: String
    let systemImage: String
    let color: Color
    
    var body: some View {
        VStack(spacing: 4) {
            Image(systemName: systemImage)
                .font(.title2)
                .foregroundColor(color)
            
            Text(value)
                .font(.title2)
                .fontWeight(.bold)
            
            Text(title)
                .font(.caption)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity)
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(12)
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct CriticalPathIndicator: View {
    let tasks: [LeanVibeTask]
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: "timer")
                    .foregroundColor(.red)
                Text("Critical Path")
                    .font(.headline)
                    .foregroundColor(.red)
            }
            
            ForEach(tasks, id: \.id) { task in
                HStack {
                    Circle()
                        .fill(Color.red)
                        .frame(width: 6, height: 6)
                    
                    Text(task.title)
                        .font(.caption)
                        .lineLimit(1)
                    
                    Spacer()
                    
                    Text("\(task.dependencies.count) deps")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
        }
        .padding()
        .background(Color.red.opacity(0.1))
        .cornerRadius(12)
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct TaskDependencyRow: View {
    let task: LeanVibeTask
    let dependentTasks: [LeanVibeTask]
    let blockingTasks: [LeanVibeTask]
    let onTaskTap: () -> Void
    let onAddDependency: () -> Void
    let onRemoveDependency: (UUID) -> Void
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Main Task Info
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(task.title)
                        .font(.headline)
                        .lineLimit(2)
                    
                    HStack {
                        TaskStatusBadge(status: task.status)
                        TaskPriorityBadge(priority: task.priority)
                        
                        if isBlocked {
                            Image(systemName: "exclamationmark.triangle.fill")
                                .foregroundColor(.orange)
                                .font(.caption)
                        }
                    }
                }
                
                Spacer()
                
                Button(action: onAddDependency) {
                    Image(systemName: "plus.circle")
                        .foregroundColor(.blue)
                }
            }
            .onTapGesture { onTaskTap() }
            
            // Dependencies Section
            if !dependentTasks.isEmpty {
                VStack(alignment: .leading, spacing: 6) {
                    Text("Depends on:")
                        .font(.caption)
                        .fontWeight(.semibold)
                        .foregroundColor(.secondary)
                    
                    ForEach(dependentTasks, id: \.id) { dependentTask in
                        DependencyTaskChip(
                            task: dependentTask,
                            onRemove: { onRemoveDependency(dependentTask.id) }
                        )
                    }
                }
            }
            
            // Blocking Section
            if !blockingTasks.isEmpty {
                VStack(alignment: .leading, spacing: 6) {
                    Text("Blocking:")
                        .font(.caption)
                        .fontWeight(.semibold)
                        .foregroundColor(.secondary)
                    
                    ForEach(blockingTasks.prefix(3), id: \.id) { blockingTask in
                        HStack {
                            Circle()
                                .fill(Color.red)
                                .frame(width: 4, height: 4)
                            
                            Text(blockingTask.title)
                                .font(.caption)
                                .lineLimit(1)
                            
                            Spacer()
                        }
                    }
                }
            }
        }
        .padding(.vertical, 8)
    }
    
    private var isBlocked: Bool {
        return !dependentTasks.isEmpty && dependentTasks.contains { $0.status != .done }
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct DependencyTaskChip: View {
    let task: LeanVibeTask
    let onRemove: () -> Void
    
    var body: some View {
        HStack(spacing: 6) {
            Circle()
                .fill(task.status == .done ? Color.green : Color.orange)
                .frame(width: 8, height: 8)
            
            Text(task.title)
                .font(.caption)
                .lineLimit(1)
            
            Button(action: onRemove) {
                Image(systemName: "xmark.circle.fill")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(Color(.systemGray6))
        .cornerRadius(12)
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct TaskStatusBadge: View {
    let status: TaskStatus
    
    var body: some View {
        Text(status.displayName)
            .font(.caption2)
            .padding(.horizontal, 6)
            .padding(.vertical, 2)
            .background(status.color.opacity(0.2))
            .foregroundColor(status.color)
            .cornerRadius(4)
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct TaskPriorityBadge: View {
    let priority: TaskPriority
    
    var body: some View {
        Text(priority.displayName)
            .font(.caption2)
            .padding(.horizontal, 6)
            .padding(.vertical, 2)
            .background(priority.color.opacity(0.2))
            .foregroundColor(priority.color)
            .cornerRadius(4)
    }
}

// Extensions removed - displayName and color properties already defined in Task.swift

#Preview {
    TaskDependencyView(taskService: TaskService(), projectId: UUID())
}