import SwiftUI

struct KanbanBoardView: View {
    @StateObject private var taskService: TaskService
    @State private var showingTaskCreation = false
    @State private var showingSettings = false
    @State private var selectedTask: Task?
    @State private var draggedTask: Task?
    @State private var searchText = ""
    @State private var sortOption: TaskSortOption = .priority
    @State private var showingStatistics = false
    
    private let columns: [TaskStatus] = [.backlog, .inProgress, .testing, .done]
    private let webSocketService: WebSocketService
    
    init(webSocketService: WebSocketService) {
        self.webSocketService = webSocketService
        self._taskService = StateObject(wrappedValue: TaskService(webSocketService: webSocketService))
    }
    
    var body: some View {
        NavigationView {
            GeometryReader { geometry in
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 16) {
                        ForEach(columns, id: \.self) { status in
                            KanbanColumnView(
                                status: status,
                                tasks: filteredTasks(for: status),
                                taskService: taskService,
                                draggedTask: $draggedTask,
                                selectedTask: $selectedTask,
                                columnWidth: columnWidth(for: geometry)
                            )
                        }
                    }
                    .padding(.horizontal)
                }
                .refreshable {
                    await taskService.loadTasks()
                }
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
                                        Text(option.displayName)
                                        if sortOption == option {
                                            Image(systemName: "checkmark")
                                        }
                                    }
                                }
                            }
                        }
                        
                        Divider()
                        
                        Button(action: { showingTaskCreation = true }) {
                            Label("New Task", systemImage: "plus")
                        }
                        
                        Button(action: { showingSettings = true }) {
                            Label("Settings", systemImage: "gear")
                        }
                    } label: {
                        Image(systemName: "ellipsis.circle")
                    }
                }
            }
            .sheet(isPresented: $showingTaskCreation) {
                TaskCreationView(taskService: taskService)
            }
            .sheet(isPresented: $showingStatistics) {
                TaskStatisticsView(taskService: taskService)
            }
            .sheet(item: $selectedTask) { task in
                TaskDetailView(task: task, taskService: taskService)
            }
            .alert("Error", isPresented: .constant(taskService.error != nil)) {
                Button("OK") {
                    taskService.error = nil
                }
            } message: {
                if let error = taskService.error {
                    Text(error)
                }
            }
        }
        .task {
            await taskService.loadTasks()
        }
    }
    
    private func filteredTasks(for status: TaskStatus) -> [Task] {
        let statusTasks = taskService.tasksByStatus(status)
        let filtered = searchText.isEmpty ? statusTasks : statusTasks.filter {
            $0.title.localizedCaseInsensitiveContains(searchText) ||
            $0.description.localizedCaseInsensitiveContains(searchText) ||
            $0.tags.contains { $0.localizedCaseInsensitiveContains(searchText) }
        }
        return taskService.sortedTasks(by: sortOption).filter { filtered.contains($0) }
    }
    
    private func columnWidth(for geometry: GeometryProxy) -> CGFloat {
        let availableWidth = geometry.size.width - 80 // Account for padding and spacing
        let columnCount = CGFloat(columns.count)
        let minimumColumnWidth: CGFloat = 280
        
        let calculatedWidth = availableWidth / columnCount
        return max(calculatedWidth, minimumColumnWidth)
    }
}

struct KanbanColumnView: View {
    let status: TaskStatus
    let tasks: [Task]
    let taskService: TaskService
    @Binding var draggedTask: Task?
    @Binding var selectedTask: Task?
    let columnWidth: CGFloat
    
    @State private var isTargeted = false
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Column Header
            columnHeader
            
            // Task Cards
            LazyVStack(spacing: 8) {
                ForEach(tasks) { task in
                    TaskCardView(
                        task: task,
                        onTap: { selectedTask = task },
                        onDragStart: { draggedTask = task },
                        onDragEnd: { draggedTask = nil }
                    )
                }
            }
            
            Spacer(minLength: 100)
        }
        .frame(width: columnWidth)
        .padding(.vertical, 16)
        .padding(.horizontal, 12)
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color.gray.opacity(0.05))
                .overlay(
                    RoundedRectangle(cornerRadius: 12)
                        .stroke(
                            isTargeted ? Color.blue : Color.gray.opacity(0.2),
                            lineWidth: isTargeted ? 2 : 1
                        )
                )
        )
        .dropDestination(for: Task.self) { droppedTasks, location in
            guard let droppedTask = droppedTasks.first,
                  droppedTask.status != status else { return false }
            
            Task {
                await taskService.moveTask(droppedTask, to: status)
            }
            return true
        } isTargeted: { targeted in
            withAnimation(.easeInOut(duration: 0.2)) {
                isTargeted = targeted
            }
        }
    }
    
    private var columnHeader: some View {
        HStack {
            Image(systemName: status.systemIcon)
                .foregroundColor(Color(status.statusColor))
            
            Text(status.displayName)
                .font(.headline)
                .fontWeight(.semibold)
            
            Spacer()
            
            Text("\(tasks.count)")
                .font(.caption)
                .fontWeight(.medium)
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(Color.gray.opacity(0.2))
                .clipShape(Capsule())
        }
    }
}

struct TaskCardView: View {
    let task: Task
    let onTap: () -> Void
    let onDragStart: () -> Void
    let onDragEnd: () -> Void
    
    @State private var isDragging = false
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            // Priority and Confidence Header
            HStack {
                Text(task.priorityEmoji)
                    .font(.caption)
                
                Spacer()
                
                ConfidenceIndicatorView(confidence: task.confidence)
                
                if task.requiresApproval {
                    Image(systemName: "person.crop.circle.badge.exclamationmark")
                        .foregroundColor(.orange)
                        .font(.caption)
                }
            }
            
            // Task Title
            Text(task.title)
                .font(.subheadline)
                .fontWeight(.medium)
                .lineLimit(2)
                .multilineTextAlignment(.leading)
            
            // Task Description
            if !task.description.isEmpty {
                Text(task.description)
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .lineLimit(3)
                    .multilineTextAlignment(.leading)
            }
            
            // Tags
            if !task.tags.isEmpty {
                TagsView(tags: Array(task.tags.prefix(3)))
            }
            
            // Footer with metadata
            HStack {
                if let assignedTo = task.assignedTo {
                    Text(assignedTo)
                        .font(.caption2)
                        .foregroundColor(.secondary)
                }
                
                Spacer()
                
                if let effort = task.estimatedEffort {
                    Text(formatDuration(effort))
                        .font(.caption2)
                        .foregroundColor(.secondary)
                }
            }
        }
        .padding(12)
        .background(
            RoundedRectangle(cornerRadius: 8)
                .fill(Color.white)
                .shadow(
                    color: .black.opacity(isDragging ? 0.3 : 0.1),
                    radius: isDragging ? 8 : 2,
                    x: 0,
                    y: isDragging ? 4 : 1
                )
        )
        .scaleEffect(isDragging ? 1.05 : 1.0)
        .opacity(isDragging ? 0.8 : 1.0)
        .animation(.easeInOut(duration: 0.2), value: isDragging)
        .draggable(task) {
            TaskCardView(
                task: task,
                onTap: {},
                onDragStart: {},
                onDragEnd: {}
            )
            .opacity(0.8)
        }
        .onTapGesture {
            onTap()
        }
        .simultaneousGesture(
            DragGesture()
                .onChanged { _ in
                    if !isDragging {
                        isDragging = true
                        onDragStart()
                    }
                }
                .onEnded { _ in
                    isDragging = false
                    onDragEnd()
                }
        )
    }
    
    private func formatDuration(_ seconds: TimeInterval) -> String {
        let hours = Int(seconds) / 3600
        let minutes = (Int(seconds) % 3600) / 60
        
        if hours > 0 {
            return "\(hours)h \(minutes)m"
        } else {
            return "\(minutes)m"
        }
    }
}

struct ConfidenceIndicatorView: View {
    let confidence: Double
    
    var body: some View {
        HStack(spacing: 2) {
            Text("\(Int(confidence * 100))%")
                .font(.caption2)
                .fontWeight(.medium)
            
            Circle()
                .fill(confidenceColor)
                .frame(width: 8, height: 8)
        }
        .padding(.horizontal, 6)
        .padding(.vertical, 2)
        .background(
            Capsule()
                .fill(confidenceColor.opacity(0.2))
        )
    }
    
    private var confidenceColor: Color {
        switch confidence {
        case 0.8...1.0:
            return .green
        case 0.5..<0.8:
            return .yellow
        default:
            return .red
        }
    }
}

struct TagsView: View {
    let tags: [String]
    
    var body: some View {
        HStack(spacing: 4) {
            ForEach(tags, id: \.self) { tag in
                Text(tag)
                    .font(.caption2)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(
                        Capsule()
                            .fill(Color.blue.opacity(0.1))
                    )
                    .foregroundColor(.blue)
            }
            
            if tags.count < 3 {
                Spacer()
            }
        }
    }
}

// MARK: - Task Conformance to Transferable

extension Task: Transferable {
    static var transferRepresentation: some TransferRepresentation {
        CodableRepresentation(contentType: .data)
    }
}

#Preview {
    KanbanBoardView(webSocketService: WebSocketService())
}