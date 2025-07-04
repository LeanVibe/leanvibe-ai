import SwiftUI

/// Visual dependency graph showing task relationships and flow
@available(iOS 18.0, macOS 14.0, *)
struct TaskDependencyGraphView: View {
    @ObservedObject var taskService: TaskService
    let projectId: UUID
    @Environment(\.dismiss) private var dismiss
    
    @State private var graphLayout: GraphLayout = .hierarchical
    @State private var selectedTask: LeanVibeTask?
    @State private var zoomScale: CGFloat = 1.0
    @State private var graphOffset: CGSize = .zero
    
    enum GraphLayout: String, CaseIterable {
        case hierarchical = "Hierarchical"
        case circular = "Circular" 
        case force = "Force-Directed"
        
        var systemImage: String {
            switch self {
            case .hierarchical: return "list.bullet.indent"
            case .circular: return "circle.grid.cross"
            case .force: return "network"
            }
        }
    }
    
    var body: some View {
        NavigationView {
            ZStack {
                // Background
                Color(.systemGroupedBackground)
                    .ignoresSafeArea()
                
                // Graph Canvas
                ScrollView([.horizontal, .vertical], showsIndicators: false) {
                    ZStack {
                        // Dependency Lines
                        Canvas { context, size in
                            drawDependencyLines(context: context, size: size)
                        }
                        
                        // Task Nodes
                        ForEach(projectTasks, id: \.id) { task in
                            TaskNode(
                                task: task,
                                isSelected: selectedTask?.id == task.id,
                                position: getNodePosition(for: task, in: CGSize(width: 800, height: 600)),
                                onTap: { selectedTask = task }
                            )
                        }
                    }
                    .frame(width: 800, height: 600)
                }
                .scaleEffect(zoomScale)
                .offset(graphOffset)
                .gesture(
                    MagnificationGesture()
                        .onChanged { value in
                            zoomScale = value
                        }
                        .simultaneously(with:
                            DragGesture()
                                .onChanged { value in
                                    graphOffset = value.translation
                                }
                        )
                )
                
                // Controls Overlay
                VStack {
                    HStack {
                        // Layout Picker
                        Picker("Layout", selection: $graphLayout) {
                            ForEach(GraphLayout.allCases, id: \.self) { layout in
                                Label(layout.rawValue, systemImage: layout.systemImage)
                                    .tag(layout)
                            }
                        }
                        .pickerStyle(.segmented)
                        .frame(maxWidth: 300)
                        
                        Spacer()
                        
                        // Zoom Controls
                        HStack {
                            Button(action: { zoomScale *= 0.8 }) {
                                Image(systemName: "minus.magnifyingglass")
                            }
                            
                            Button(action: { 
                                zoomScale = 1.0
                                graphOffset = .zero
                            }) {
                                Image(systemName: "arrow.clockwise")
                            }
                            
                            Button(action: { zoomScale *= 1.2 }) {
                                Image(systemName: "plus.magnifyingglass")
                            }
                        }
                        .buttonStyle(.bordered)
                    }
                    
                    Spacer()
                    
                    // Legend
                    graphLegend
                }
                .padding()
                
                // Task Detail Overlay
                if let task = selectedTask {
                    VStack {
                        Spacer()
                        TaskGraphDetailCard(
                            task: task,
                            dependentTasks: getDependentTasks(for: task),
                            blockingTasks: getBlockingTasks(for: task),
                            onDismiss: { selectedTask = nil }
                        )
                    }
                    .transition(.move(edge: .bottom))
                }
            }
            .navigationTitle("Dependency Graph")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Done") {
                        dismiss()
                    }
                }
            }
        }
        .animation(.easeInOut, value: selectedTask)
    }
    
    // MARK: - Computed Properties
    
    private var projectTasks: [LeanVibeTask] {
        return taskService.tasks.filter { $0.projectId == projectId }
    }
    
    private var graphLegend: some View {
        HStack(spacing: 20) {
            LegendItem(color: .green, label: "Ready")
            LegendItem(color: .orange, label: "Blocked")
            LegendItem(color: .blue, label: "In Progress")
            LegendItem(color: .gray, label: "Done")
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(12)
        .shadow(radius: 2)
    }
    
    // MARK: - Helper Methods
    
    private func getNodePosition(for task: LeanVibeTask, in canvasSize: CGSize) -> CGPoint {
        let taskIndex = projectTasks.firstIndex(where: { $0.id == task.id }) ?? 0
        
        switch graphLayout {
        case .hierarchical:
            return getHierarchicalPosition(for: task, index: taskIndex, canvasSize: canvasSize)
        case .circular:
            return getCircularPosition(for: task, index: taskIndex, canvasSize: canvasSize)
        case .force:
            return getForceDirectedPosition(for: task, index: taskIndex, canvasSize: canvasSize)
        }
    }
    
    private func getHierarchicalPosition(for task: LeanVibeTask, index: Int, canvasSize: CGSize) -> CGPoint {
        let statusIndex = TaskStatus.allCases.firstIndex(of: task.status) ?? 0
        let tasksInStatus = projectTasks.filter { $0.status == task.status }
        let taskIndexInStatus = tasksInStatus.firstIndex(where: { $0.id == task.id }) ?? 0
        
        let x = (CGFloat(statusIndex) * canvasSize.width / CGFloat(TaskStatus.allCases.count - 1)) + 100
        let y = CGFloat(taskIndexInStatus * 80) + 100
        
        return CGPoint(x: x, y: y)
    }
    
    private func getCircularPosition(for task: LeanVibeTask, index: Int, canvasSize: CGSize) -> CGPoint {
        let centerX = canvasSize.width / 2
        let centerY = canvasSize.height / 2
        let radius = min(centerX, centerY) - 100
        
        let angle = (2 * .pi * CGFloat(index)) / CGFloat(projectTasks.count)
        let x = centerX + radius * cos(angle)
        let y = centerY + radius * sin(angle)
        
        return CGPoint(x: x, y: y)
    }
    
    private func getForceDirectedPosition(for task: LeanVibeTask, index: Int, canvasSize: CGSize) -> CGPoint {
        // Simplified force-directed layout
        let dependencyCount = task.dependencies.count
        let blockingCount = getBlockingTasks(for: task).count
        
        let x = CGFloat(dependencyCount * 120 + 100) + CGFloat.random(in: -50...50)
        let y = CGFloat(blockingCount * 80 + 100) + CGFloat.random(in: -30...30)
        
        return CGPoint(
            x: min(max(x, 50), canvasSize.width - 50),
            y: min(max(y, 50), canvasSize.height - 50)
        )
    }
    
    private func drawDependencyLines(context: GraphicsContext, size: CGSize) {
        for task in projectTasks {
            let fromPosition = getNodePosition(for: task, in: size)
            
            for dependencyId in task.dependencies {
                if let dependentTask = projectTasks.first(where: { $0.id == dependencyId }) {
                    let toPosition = getNodePosition(for: dependentTask, in: size)
                    
                    var path = Path()
                    path.move(to: fromPosition)
                    path.addLine(to: toPosition)
                    
                    let strokeColor = dependentTask.status == .done ? Color.green : Color.orange
                    context.stroke(path, with: .color(strokeColor), lineWidth: 2)
                    
                    // Draw arrow
                    drawArrow(context: context, from: fromPosition, to: toPosition, color: strokeColor)
                }
            }
        }
    }
    
    private func drawArrow(context: GraphicsContext, from: CGPoint, to: CGPoint, color: Color) {
        let arrowLength: CGFloat = 10
        let arrowAngle: CGFloat = .pi / 6
        
        let dx = to.x - from.x
        let dy = to.y - from.y
        let angle = atan2(dy, dx)
        
        let arrowPoint1 = CGPoint(
            x: to.x - arrowLength * cos(angle - arrowAngle),
            y: to.y - arrowLength * sin(angle - arrowAngle)
        )
        
        let arrowPoint2 = CGPoint(
            x: to.x - arrowLength * cos(angle + arrowAngle),
            y: to.y - arrowLength * sin(angle + arrowAngle)
        )
        
        var arrowPath = Path()
        arrowPath.move(to: to)
        arrowPath.addLine(to: arrowPoint1)
        arrowPath.move(to: to)
        arrowPath.addLine(to: arrowPoint2)
        
        context.stroke(arrowPath, with: .color(color), lineWidth: 2)
    }
    
    private func getDependentTasks(for task: LeanVibeTask) -> [LeanVibeTask] {
        return task.dependencies.compactMap { dependencyId in
            projectTasks.first { $0.id == dependencyId }
        }
    }
    
    private func getBlockingTasks(for task: LeanVibeTask) -> [LeanVibeTask] {
        return projectTasks.filter { otherTask in
            otherTask.dependencies.contains(task.id)
        }
    }
}

// MARK: - Supporting Views

@available(iOS 18.0, macOS 14.0, *)
struct TaskNode: View {
    let task: LeanVibeTask
    let isSelected: Bool
    let position: CGPoint
    let onTap: () -> Void
    
    var body: some View {
        VStack(spacing: 4) {
            Circle()
                .fill(nodeColor)
                .frame(width: 40, height: 40)
                .overlay(
                    Text(task.priority.shortName)
                        .font(.caption2)
                        .fontWeight(.bold)
                        .foregroundColor(.white)
                )
                .overlay(
                    Circle()
                        .stroke(isSelected ? Color.blue : Color.clear, lineWidth: 3)
                )
            
            Text(task.title)
                .font(.caption2)
                .fontWeight(.medium)
                .multilineTextAlignment(.center)
                .lineLimit(2)
                .frame(width: 80)
        }
        .position(position)
        .onTapGesture { onTap() }
        .scaleEffect(isSelected ? 1.1 : 1.0)
        .animation(.spring(response: 0.3), value: isSelected)
    }
    
    private var nodeColor: Color {
        if isTaskBlocked {
            return .orange
        }
        
        switch task.status {
        case .done:
            return .gray
        case .inProgress:
            return .blue
        default:
            return task.dependencies.isEmpty ? .green : .orange
        }
    }
    
    private var isTaskBlocked: Bool {
        return !task.dependencies.isEmpty && task.status != .done
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct TaskGraphDetailCard: View {
    let task: LeanVibeTask
    let dependentTasks: [LeanVibeTask]
    let blockingTasks: [LeanVibeTask]
    let onDismiss: () -> Void
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
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
                
                Button(action: onDismiss) {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundColor(.secondary)
                }
            }
            
            if !dependentTasks.isEmpty {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Dependencies (\(dependentTasks.count))")
                        .font(.caption)
                        .fontWeight(.semibold)
                        .foregroundColor(.secondary)
                    
                    LazyVGrid(columns: Array(repeating: GridItem(.flexible()), count: 2), spacing: 4) {
                        ForEach(dependentTasks.prefix(4), id: \.id) { dep in
                            HStack {
                                Circle()
                                    .fill(dep.status == .done ? Color.green : Color.orange)
                                    .frame(width: 6, height: 6)
                                Text(dep.title)
                                    .font(.caption2)
                                    .lineLimit(1)
                                Spacer()
                            }
                        }
                    }
                }
            }
            
            if !blockingTasks.isEmpty {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Blocking (\(blockingTasks.count))")
                        .font(.caption)
                        .fontWeight(.semibold)
                        .foregroundColor(.secondary)
                    
                    ForEach(blockingTasks.prefix(3), id: \.id) { blocking in
                        HStack {
                            Circle()
                                .fill(Color.red)
                                .frame(width: 6, height: 6)
                            Text(blocking.title)
                                .font(.caption2)
                                .lineLimit(1)
                            Spacer()
                        }
                    }
                }
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(12)
        .shadow(radius: 4)
        .padding(.horizontal)
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct LegendItem: View {
    let color: Color
    let label: String
    
    var body: some View {
        HStack(spacing: 4) {
            Circle()
                .fill(color)
                .frame(width: 8, height: 8)
            Text(label)
                .font(.caption2)
        }
    }
}

// Extensions
extension TaskPriority {
    var shortName: String {
        switch self {
        case .low: return "L"
        case .medium: return "M"
        case .high: return "H"
        case .urgent: return "U"
        }
    }
}

#Preview {
    TaskDependencyGraphView(taskService: TaskService(), projectId: UUID())
}