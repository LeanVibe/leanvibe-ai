import SwiftUI
import Foundation

@available(iOS 18.0, macOS 14.0, *)
@MainActor
struct KanbanBoardView: View {
    @ObservedObject var taskService: TaskService
    let projectId: UUID
    @State private var showingCreateTask = false
    @State private var selectedTask: LeanVibeTask?
    @State private var editingTask: LeanVibeTask?
    @State private var searchText = ""
    @State private var showingStatistics = false
    @State private var showingSettings = false
    @State private var sortOption: String = "priority"
    @State private var draggedTask: LeanVibeTask?
    @State private var isOfflineMode = false
    @State private var showingOfflineAlert = false
    @State private var showingDependencies = false

    var body: some View {
        NavigationView {
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 16) {
                    ForEach(TaskStatus.allCases, id: \.self) { status in
                        KanbanColumnView(
                            status: status,
                            tasks: filteredTasks(for: status),
                            taskService: taskService,
                            selectedTask: $selectedTask,
                            draggedTask: $draggedTask,
                            onDragError: { error in
                                // Error is handled by the ErrorDisplayView overlay
                                // TaskService.lastError will be displayed
                            }
                        )
                    }
                }
                .padding(.horizontal)
            }
            .navigationTitle("Tasks")
            .navigationBarTitleDisplayMode(.large)
            .searchable(text: $searchText, prompt: "Search tasks...")
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    HStack {
                        Button(action: { showingStatistics = true }) {
                            Image(systemName: "chart.bar.xaxis")
                        }
                        
                        Button(action: { showingDependencies = true }) {
                            Image(systemName: "arrow.triangle.branch")
                        }
                        
                        // Offline mode indicator
                        if isOfflineMode {
                            Button(action: { showingOfflineAlert = true }) {
                                Image(systemName: "wifi.slash")
                                    .foregroundColor(.orange)
                            }
                        }
                    }
                }
                
                ToolbarItem(placement: .navigationBarTrailing) {
                    HStack {
                        // Add task button
                        Button(action: { showingCreateTask = true }) {
                            Image(systemName: "plus")
                        }
                        
                        Menu {
                            Section("Sort by") {
                                ForEach(["priority", "due_date", "title"], id: \.self) { option in
                                    Button(action: { sortOption = option }) {
                                        HStack {
                                            Text(option.capitalized)
                                            if sortOption == option {
                                                Image(systemName: "checkmark")
                                            }
                                        }
                                    }
                                }
                            }
                            
                            Divider()
                            
                            Button(action: { 
                                Task {
                                    try? await taskService.loadTasks(for: projectId)
                                }
                            }) {
                                Label("Refresh", systemImage: "arrow.clockwise")
                            }
                            
                            Button(action: { showingSettings = true }) {
                                Label("Settings", systemImage: "gear")
                            }
                        } label: {
                            Image(systemName: "ellipsis.circle")
                        }
                    }
                }
            }
            .overlay(alignment: .top) {
                // Display task service errors
                if let error = taskService.lastError {
                    ErrorDisplayView(
                        error: error,
                        onRetry: {
                            Task {
                                try? await taskService.loadTasks(for: projectId)
                            }
                        }
                    )
                    .padding()
                }
            }
            .sheet(isPresented: $showingStatistics) {
                TaskStatisticsView(taskService: taskService)
            }
            .sheet(isPresented: $showingDependencies) {
                // TODO: Re-enable TaskDependencyView after fixing compilation order
                Text("Task Dependencies")
                    .font(.largeTitle)
                    .foregroundColor(.secondary)
            }
            .sheet(isPresented: $showingCreateTask) {
                TaskCreationView(taskService: taskService, projectId: projectId)
            }
            .sheet(item: $selectedTask) { task in
                TaskDetailView(taskService: taskService, task: task)
            }
            .alert("Offline Mode", isPresented: $showingOfflineAlert) {
                Button("OK") { }
            } message: {
                Text("You're currently offline. Changes will be saved locally and synced when connection is restored.")
            }
        }
        .task {
            // Load tasks for the current project when view appears
            do {
                try await taskService.loadTasks(for: projectId)
                isOfflineMode = false // Successfully loaded from backend
            } catch {
                // Check if this is a network error to set offline mode
                if let taskError = error as? TaskServiceError,
                   case .networkFailure = taskError {
                    isOfflineMode = true
                }
            }
        }
        .refreshable {
            // Add pull-to-refresh functionality with error handling
            do {
                try await taskService.loadTasks(for: projectId)
            } catch {
                // Global error manager handles the error display
                // TaskService already shows the error via GlobalErrorManager
            }
        }
    }
    
    private func filteredTasks(for status: TaskStatus) -> [LeanVibeTask] {
        let statusTasks = taskService.tasks.filter { $0.status == status }
        let filtered = searchText.isEmpty ? statusTasks : statusTasks.filter {
            $0.title.localizedCaseInsensitiveContains(searchText) ||
            ($0.description?.localizedCaseInsensitiveContains(searchText) ?? false) ||
            $0.tags.contains { $0.localizedCaseInsensitiveContains(searchText) }
        }
        
        // Simple sorting by priority for now
        return filtered.sorted { $0.priority.weight > $1.priority.weight }
    }
}
