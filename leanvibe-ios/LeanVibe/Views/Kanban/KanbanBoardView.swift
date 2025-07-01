import SwiftUI

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
    @State private var sortOption: TaskSortOption = .priority
    @State private var draggedTask: LeanVibeTask?
    @State private var errorMessage: String?
    @State private var showingError = false

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
                                errorMessage = error
                                showingError = true
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
                    Button(action: { showingStatistics = true }) {
                        Image(systemName: "chart.bar.xaxis")
                    }
                }
                
                ToolbarItem(placement: .navigationBarTrailing) {
                    Menu {
                        Section("Sort by") {
                            ForEach(TaskSortOption.allCases, id: \.self) { option in
                                Button(action: { sortOption = option }) {
                                    HStack {
                                        Text(option.rawValue.capitalized)
                                        if sortOption == option {
                                            Image(systemName: "checkmark")
                                        }
                                    }
                                }
                            }
                        }
                        
                        Divider()
                        
                        Button(action: { showingSettings = true }) {
                            Label("Settings", systemImage: "gear")
                        }
                    } label: {
                        Image(systemName: "ellipsis.circle")
                    }
                }
            }
            .sheet(isPresented: $showingStatistics) {
                TaskStatisticsView(taskService: taskService)
            }
            .sheet(item: $selectedTask) { task in
                TaskDetailView(taskService: taskService, task: task)
            }
            .alert("Drag & Drop Error", isPresented: $showingError) {
                Button("OK") { 
                    showingError = false
                    errorMessage = nil
                }
            } message: {
                Text(errorMessage ?? "An error occurred while moving the task")
            }
        }
        .task {
            // Load tasks for the current project when view appears
            do {
                try await taskService.loadTasks(for: projectId)
            } catch {
                await MainActor.run {
                    errorMessage = "Failed to load tasks: \(error.localizedDescription)"
                    showingError = true
                }
            }
        }
        .refreshable {
            // Add pull-to-refresh functionality with error handling
            do {
                try await taskService.loadTasks(for: projectId)
            } catch {
                errorMessage = "Failed to refresh tasks: \(error.localizedDescription)"
                showingError = true
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

@available(iOS 18.0, macOS 14.0, *)
struct KanbanColumnView: View {
    let status: TaskStatus
    let tasks: [LeanVibeTask]
    let taskService: TaskService
    @Binding var selectedTask: LeanVibeTask?
    @Binding var draggedTask: LeanVibeTask?
    let onDragError: (String) -> Void
    @State private var isDropTarget = false
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Column Header
            HStack {
                Image(systemName: status.systemIcon)
                    .foregroundColor(colorFromString(getStatusColor(status)))
                
                Text(status.displayName)
                    .font(.headline)
                    .fontWeight(.semibold)
                
                Spacer()
                
                Text("\(tasks.count)")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(Color(.systemGray5))
                    .cornerRadius(8)
            }
            .padding(.horizontal)
            
            // Tasks
            ScrollView {
                LazyVStack(spacing: 8) {
                    ForEach(tasks) { task in
                        TaskCardView(
                            task: task,
                            isDragged: draggedTask?.id == task.id,
                            onDragStarted: { draggedTask = task },
                            onDragEnded: { draggedTask = nil }
                        )
                        .onTapGesture {
                            selectedTask = task
                        }
                    }
                }
                .padding(.horizontal)
            }
        }
        .frame(width: 280)
        .background(isDropTarget ? Color.blue.opacity(0.1) : Color(red: 0.95, green: 0.95, blue: 0.97))
        .cornerRadius(12)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(isDropTarget ? Color.blue : Color.clear, lineWidth: 2)
        )
        .dropDestination(for: String.self) { droppedItems, location in
            guard let droppedTaskId = droppedItems.first,
                  let taskUUID = UUID(uuidString: droppedTaskId),
                  let draggedTaskFound = taskService.tasks.first(where: { $0.id == taskUUID }) else {
                onDragError("Invalid task data")
                return false
            }
            
            // Check if this is actually a move (different status)
            guard draggedTaskFound.status != status else {
                return false // Same column, no need to move
            }
            
            // Provide immediate visual feedback
            withAnimation(.spring(response: 0.4, dampingFraction: 0.8)) {
                isDropTarget = false
            }
            
            // Update task status with proper error handling
            Task {
                do {
                    try await taskService.updateTaskStatus(taskUUID, status)
                    
                    // Haptic feedback for successful move
                    DispatchQueue.main.async {
                        #if os(iOS)
                        let impactFeedback = UIImpactFeedbackGenerator(style: .medium)
                        impactFeedback.impactOccurred()
                        #endif
                    }
                } catch {
                    DispatchQueue.main.async {
                        onDragError("Failed to move task: \(error.localizedDescription)")
                        
                        // Error haptic feedback
                        #if os(iOS)
                        let notificationFeedback = UINotificationFeedbackGenerator()
                        notificationFeedback.notificationOccurred(.error)
                        #endif
                    }
                }
            }
            
            return true
        } isTargeted: { isTargeted in
            withAnimation(.easeInOut(duration: 0.2)) {
                isDropTarget = isTargeted
            }
            
            // Subtle haptic feedback when hovering over drop target
            if isTargeted {
                #if os(iOS)
                let selectionFeedback = UISelectionFeedbackGenerator()
                selectionFeedback.selectionChanged()
                #endif
            }
        }
    }
    
    private func colorFromString(_ colorName: String) -> Color {
        switch colorName {
        case "gray": return .gray
        case "blue": return .blue
        case "orange": return .orange
        case "green": return .green
        case "red": return .red
        default: return .gray
        }
    }
    
    private func getStatusColor(_ status: TaskStatus) -> String {
        switch status {
        case .todo: return "gray"
        case .inProgress: return "blue"
        case .done: return "green"
        }
    }
}

struct TaskCardView: View {
    let task: LeanVibeTask
    let isDragged: Bool
    let onDragStarted: () -> Void
    let onDragEnded: () -> Void
    @State private var isDraggedOver = false
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(task.title)
                    .font(.headline)
                    .lineLimit(2)
                
                Spacer()
                
                Circle()
                    .fill(task.priority.color)
                    .frame(width: 8, height: 8)
            }
            
            if let description = task.description, !description.isEmpty {
                Text(description)
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .lineLimit(3)
            }
            
            HStack {
                ForEach(task.tags.prefix(3), id: \.self) { tag in
                    Text(tag)
                        .font(.caption2)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(Color.blue.opacity(0.2))
                        .foregroundColor(.blue)
                        .cornerRadius(4)
                }
                
                Spacer()
                
                if task.requiresApproval {
                    Image(systemName: "person.crop.circle.badge.questionmark")
                        .foregroundColor(.orange)
                        .font(.caption)
                }
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(8)
        .shadow(radius: isDragged ? 8 : 2)
        .opacity(isDragged ? 0.7 : 1.0)
        .scaleEffect(isDragged ? 0.95 : 1.0)
        .animation(.spring(response: 0.3, dampingFraction: 0.7), value: isDragged)
        .draggable(task.id.uuidString) {
            // Enhanced drag preview with better styling
            VStack(alignment: .leading, spacing: 6) {
                HStack {
                    Text(task.title)
                        .font(.headline)
                        .lineLimit(1)
                        .foregroundColor(.primary)
                    
                    Spacer()
                    
                    Circle()
                        .fill(task.priority.color)
                        .frame(width: 8, height: 8)
                }
                
                Text(task.status.displayName)
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(Color(.systemGray5))
                    .cornerRadius(4)
            }
            .padding(12)
            .background(Color(.systemBackground))
            .cornerRadius(10)
            .shadow(color: .black.opacity(0.3), radius: 12, x: 0, y: 8)
            .overlay(
                RoundedRectangle(cornerRadius: 10)
                    .stroke(task.priority.color, lineWidth: 2)
            )
        }
        .onDrag {
            onDragStarted()
            
            // Haptic feedback on drag start
            #if os(iOS)
            let impactFeedback = UIImpactFeedbackGenerator(style: .light)
            impactFeedback.impactOccurred()
            #endif
            
            return NSItemProvider(object: task.id.uuidString as NSString)
        }
        .onDrop(of: ["public.text"], delegate: TaskCardDropDelegate(
            task: task,
            onDragEnded: onDragEnded
        ))
    }
}

enum TaskSortOption: String, CaseIterable {
    case priority = "priority"
    case date = "date"
    case title = "title"
}

struct TaskCardDropDelegate: DropDelegate {
    let task: LeanVibeTask
    let onDragEnded: () -> Void
    
    func performDrop(info: DropInfo) -> Bool {
        onDragEnded()
        return false // Let the column handle the actual drop
    }
    
    func dropExited(info: DropInfo) {
        onDragEnded()
    }
    
    func dropUpdated(info: DropInfo) -> DropProposal? {
        return DropProposal(operation: .move)
    }
}

#Preview {
    KanbanBoardView(taskService: TaskService(), projectId: UUID())
}