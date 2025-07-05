import SwiftUI

/// View for adding dependencies to a task with smart suggestions
@available(iOS 18.0, macOS 14.0, *)
struct AddTaskDependencyView: View {
    let task: LeanVibeTask
    let availableTasks: [LeanVibeTask]
    let onDependencyAdded: (UUID) -> Void
    
    @Environment(\.dismiss) private var dismiss
    @State private var searchText = ""
    @State private var selectedTasks: Set<UUID> = []
    @State private var suggestionFilter: SuggestionFilter = .all
    
    enum SuggestionFilter: String, CaseIterable {
        case all = "All Available"
        case samePriority = "Same Priority"
        case prerequisites = "Prerequisites"
        case related = "Related"
        
        var systemImage: String {
            switch self {
            case .all: return "list.bullet"
            case .samePriority: return "equal.square"
            case .prerequisites: return "arrow.up.circle"
            case .related: return "link"
            }
        }
    }
    
    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                // Current Task Info
                currentTaskSection
                
                Divider()
                
                // Filter Section
                filterSection
                
                // Available Tasks List
                taskSelectionList
                
                // Add Dependencies Button
                addDependenciesButton
            }
            .navigationTitle("Add Dependencies")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
            }
        }
        .searchable(text: $searchText, prompt: "Search tasks...")
    }
    
    // MARK: - View Sections
    
    private var currentTaskSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Adding dependencies to:")
                .font(.caption)
                .foregroundColor(.secondary)
            
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(task.title)
                        .font(.headline)
                        .lineLimit(2)
                    
                    HStack {
                        TaskStatusBadge(status: task.status)
                        TaskPriorityBadge(priority: task.priority)
                    }
                }
                
                Spacer()
                
                VStack(alignment: .trailing, spacing: 4) {
                    Text("Current Dependencies")
                        .font(.caption2)
                        .foregroundColor(.secondary)
                    Text("\(task.dependencies.count)")
                        .font(.title3)
                        .fontWeight(.semibold)
                }
            }
        }
        .padding()
        .background(#if os(iOS)
Color(.systemGray6)
#else
Color.gray.opacity(0.1)
#endif)
    }
    
    private var filterSection: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 12) {
                ForEach(SuggestionFilter.allCases, id: \.self) { filter in
                    FilterChip(
                        title: filter.rawValue,
                        systemImage: filter.systemImage,
                        isSelected: suggestionFilter == filter,
                        onTap: { suggestionFilter = filter }
                    )
                }
            }
            .padding(.horizontal)
        }
        .padding(.vertical, 8)
    }
    
    private var taskSelectionList: some View {
        List {
            if smartSuggestions.isEmpty && filteredTasks.isEmpty {
                ContentUnavailableView(
                    "No Available Tasks",
                    systemImage: "list.bullet.clipboard",
                    description: Text("All tasks are either already dependencies or would create circular dependencies.")
                )
            } else {
                // Smart Suggestions Section
                if !smartSuggestions.isEmpty && searchText.isEmpty {
                    Section("Smart Suggestions") {
                        ForEach(smartSuggestions, id: \.id) { suggestedTask in
                            TaskDependencyRow(
                                task: suggestedTask,
                                isSelected: selectedTasks.contains(suggestedTask.id),
                                suggestion: getSuggestionReason(for: suggestedTask),
                                onToggle: { toggleTaskSelection(suggestedTask.id) }
                            )
                        }
                    }
                }
                
                // All Available Tasks Section
                Section(searchText.isEmpty ? "All Available Tasks" : "Search Results") {
                    ForEach(filteredTasks, id: \.id) { availableTask in
                        TaskDependencyRow(
                            task: availableTask,
                            isSelected: selectedTasks.contains(availableTask.id),
                            suggestion: nil,
                            onToggle: { toggleTaskSelection(availableTask.id) }
                        )
                    }
                }
            }
        }
        .listStyle(.insetGrouped)
    }
    
    private var addDependenciesButton: some View {
        VStack(spacing: 12) {
            if !selectedTasks.isEmpty {
                Text("Adding \(selectedTasks.count) dependenc\(selectedTasks.count == 1 ? "y" : "ies")")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Button(action: addSelectedDependencies) {
                HStack {
                    Image(systemName: "arrow.triangle.branch")
                    Text("Add \(selectedTasks.count) Dependenc\(selectedTasks.count == 1 ? "y" : "ies")")
                }
                .font(.headline)
                .foregroundColor(.white)
                .frame(maxWidth: .infinity)
                .padding()
                .background(selectedTasks.isEmpty ? Color.gray : Color.blue)
                .cornerRadius(12)
            }
            .disabled(selectedTasks.isEmpty)
        }
        .padding()
        .background(Color(.systemGroupedBackground))
    }
    
    // MARK: - Computed Properties
    
    private var filteredTasks: [LeanVibeTask] {
        var filtered = availableTasks
        
        // Apply suggestion filter
        switch suggestionFilter {
        case .all:
            break
        case .samePriority:
            filtered = filtered.filter { $0.priority == task.priority }
        case .prerequisites:
            filtered = filtered.filter { 
                $0.status == .todo || $0.status == .backlog
            }
        case .related:
            filtered = filtered.filter { candidateTask in
                // Simple relatedness check based on shared tags or similar titles
                let sharedTags = Set(task.tags).intersection(Set(candidateTask.tags))
                let titleSimilarity = task.title.lowercased().components(separatedBy: " ")
                    .contains { word in
                        candidateTask.title.lowercased().contains(word) && word.count > 3
                    }
                return !sharedTags.isEmpty || titleSimilarity
            }
        }
        
        // Apply search filter
        if !searchText.isEmpty {
            filtered = filtered.filter { candidateTask in
                candidateTask.title.localizedCaseInsensitiveContains(searchText) ||
                candidateTask.description?.localizedCaseInsensitiveContains(searchText) == true ||
                candidateTask.tags.contains { $0.localizedCaseInsensitiveContains(searchText) }
            }
        }
        
        // Remove smart suggestions from regular list to avoid duplicates
        let suggestionIds = Set(smartSuggestions.map { $0.id })
        filtered = filtered.filter { !suggestionIds.contains($0.id) }
        
        return filtered.sorted { $0.priority.rawValue > $1.priority.rawValue }
    }
    
    private var smartSuggestions: [LeanVibeTask] {
        guard searchText.isEmpty else { return [] }
        
        var suggestions: [LeanVibeTask] = []
        
        // Suggest tasks that are prerequisites (earlier in workflow)
        let prerequisites = availableTasks.filter { candidateTask in
            let currentStatusIndex = TaskStatus.allCases.firstIndex(of: task.status) ?? 0
            let candidateStatusIndex = TaskStatus.allCases.firstIndex(of: candidateTask.status) ?? 0
            return candidateStatusIndex < currentStatusIndex && candidateTask.priority.rawValue >= task.priority.rawValue
        }
        suggestions.append(contentsOf: prerequisites.prefix(3))
        
        // Suggest tasks with shared tags
        let relatedByTags = availableTasks.filter { candidateTask in
            let sharedTags = Set(task.tags).intersection(Set(candidateTask.tags))
            return !sharedTags.isEmpty && !suggestions.contains(where: { $0.id == candidateTask.id })
        }
        suggestions.append(contentsOf: relatedByTags.prefix(2))
        
        // Suggest high-priority tasks that are not yet done
        let highPriorityTasks = availableTasks.filter { candidateTask in
            candidateTask.priority == .urgent || candidateTask.priority == .high &&
            candidateTask.status != .done &&
            !suggestions.contains(where: { $0.id == candidateTask.id })
        }
        suggestions.append(contentsOf: highPriorityTasks.prefix(2))
        
        return Array(suggestions.prefix(5))
    }
    
    // MARK: - Helper Methods
    
    private func toggleTaskSelection(_ taskId: UUID) {
        if selectedTasks.contains(taskId) {
            selectedTasks.remove(taskId)
        } else {
            selectedTasks.insert(taskId)
        }
    }
    
    private func addSelectedDependencies() {
        for taskId in selectedTasks {
            onDependencyAdded(taskId)
        }
        dismiss()
    }
    
    private func getSuggestionReason(for task: LeanVibeTask) -> String {
        // Check what type of suggestion this is
        let currentStatusIndex = TaskStatus.allCases.firstIndex(of: self.task.status) ?? 0
        let candidateStatusIndex = TaskStatus.allCases.firstIndex(of: task.status) ?? 0
        
        if candidateStatusIndex < currentStatusIndex {
            return "Prerequisite workflow step"
        }
        
        let sharedTags = Set(self.task.tags).intersection(Set(task.tags))
        if !sharedTags.isEmpty {
            return "Related: \(sharedTags.first ?? "")"
        }
        
        if task.priority == .urgent || task.priority == .high {
            return "High priority dependency"
        }
        
        return "Suggested"
    }
}

// MARK: - Supporting Views

@available(iOS 18.0, macOS 14.0, *)
struct TaskDependencyRow: View {
    let task: LeanVibeTask
    let isSelected: Bool
    let suggestion: String?
    let onToggle: () -> Void
    
    var body: some View {
        HStack {
            // Selection Indicator
            Button(action: onToggle) {
                Image(systemName: isSelected ? "checkmark.circle.fill" : "circle")
                    .foregroundColor(isSelected ? .blue : .gray)
                    .font(.title2)
            }
            
            VStack(alignment: .leading, spacing: 4) {
                Text(task.title)
                    .font(.headline)
                    .lineLimit(2)
                
                HStack {
                    TaskStatusBadge(status: task.status)
                    TaskPriorityBadge(priority: task.priority)
                    
                    if let suggestion = suggestion {
                        Text(suggestion)
                            .font(.caption2)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 2)
                            .background(Color.blue.opacity(0.1))
                            .foregroundColor(.blue)
                            .cornerRadius(4)
                    }
                }
                
                if !task.tags.isEmpty {
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 4) {
                            ForEach(task.tags.prefix(3), id: \.self) { tag in
                                Text(tag)
                                    .font(.caption2)
                                    .padding(.horizontal, 4)
                                    .padding(.vertical, 2)
                                    .background(Color(.systemGray5))
                                    .cornerRadius(3)
                            }
                        }
                    }
                }
                
                if let description = task.description {
                    Text(description)
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .lineLimit(2)
                }
            }
            
            Spacer()
            
            // Dependency count indicator
            if !task.dependencies.isEmpty {
                VStack {
                    Text("\(task.dependencies.count)")
                        .font(.caption)
                        .fontWeight(.semibold)
                    Text("deps")
                        .font(.caption2)
                        .foregroundColor(.secondary)
                }
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(#if os(iOS)
Color(.systemGray6)
#else
Color.gray.opacity(0.1)
#endif)
                .cornerRadius(8)
            }
        }
        .contentShape(Rectangle())
        .onTapGesture { onToggle() }
    }
}

#Preview {
    AddTaskDependencyView(
        task: LeanVibeTask(
            title: "Implement API endpoint",
            description: "Create REST API for user management",
            status: .todo,
            priority: .high,
            projectId: UUID(),
            createdAt: Date(),
            updatedAt: Date(),
            confidence: 0.9,
            agentDecision: nil,
            clientId: "preview",
            assignedTo: nil,
            estimatedEffort: nil,
            actualEffort: nil,
            tags: ["backend", "api"],
            dependencies: [],
            attachments: []
        ),
        availableTasks: [],
        onDependencyAdded: { _ in }
    )
}