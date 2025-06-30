import SwiftUI

@MainActor
struct KanbanBoardView: View {
    @ObservedObject var taskService: TaskService
    @State private var showingCreateTask = false
    @State private var selectedTask: LeenVibeTask?
    @State private var editingTask: LeenVibeTask?
    @State private var searchText = ""
    @State private var showingStatistics = false
    @State private var showingSettings = false
    @State private var sortOption: TaskSortOption = .priority
    @State private var draggedTask: LeenVibeTask?

    var body: some View {
        NavigationView {
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 16) {
                    ForEach(TaskStatus.allCases, id: \.self) { status in
                        KanbanColumnView(
                            status: status,
                            tasks: filteredTasks(for: status),
                            taskService: taskService,
                            selectedTask: $selectedTask
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
            .alert("Error", isPresented: .constant(false)) {
                Button("OK") {}
            } message: {
                Text("An error occurred")
            }
        }
        .task {
            // Load tasks when view appears
        }
    }
    
    private func filteredTasks(for status: TaskStatus) -> [LeenVibeTask] {
        let statusTasks = taskService.tasks.filter { $0.status == status }
        let filtered = searchText.isEmpty ? statusTasks : statusTasks.filter {
            $0.title.localizedCaseInsensitiveContains(searchText) ||
            $0.description.localizedCaseInsensitiveContains(searchText) ||
            $0.tags.contains { $0.localizedCaseInsensitiveContains(searchText) }
        }
        
        // Simple sorting by priority for now
        return filtered.sorted { $0.priority.weight > $1.priority.weight }
    }
}

struct KanbanColumnView: View {
    let status: TaskStatus
    let tasks: [LeenVibeTask]
    let taskService: TaskService
    @Binding var selectedTask: LeenVibeTask?
    
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
                        TaskCardView(task: task)
                            .onTapGesture {
                                selectedTask = task
                            }
                    }
                }
                .padding(.horizontal)
            }
        }
        .frame(width: 280)
        .background(Color(.systemGray6))
        .cornerRadius(12)
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
        case .backlog: return "gray"
        case .inProgress: return "blue"
        case .testing: return "orange"
        case .done: return "green"
        case .blocked: return "red"
        }
    }
}

struct TaskCardView: View {
    let task: LeenVibeTask
    
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
            
            if !task.description.isEmpty {
                Text(task.description)
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
        .shadow(radius: 1)
    }
}

enum TaskSortOption: String, CaseIterable {
    case priority = "priority"
    case date = "date"
    case title = "title"
}

#Preview {
    KanbanBoardView(taskService: TaskService())
}