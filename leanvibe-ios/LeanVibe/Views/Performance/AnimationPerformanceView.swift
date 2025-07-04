import SwiftUI

// MARK: - Performance-Optimized Animation Extensions

@available(iOS 18.0, macOS 14.0, *)
extension View {
    func performanceOptimizedAnimation<V: Equatable>(
        _ value: V,
        duration: Double = 0.3
    ) -> some View {
        self.animation(
            .timingCurve(0.4, 0.0, 0.2, 1.0, duration: duration),
            value: value
        )
        .drawingGroup() // Flatten to bitmap for complex animations
    }
    
    func optimizedSpringAnimation<V: Equatable>(
        _ value: V,
        response: Double = 0.6,
        dampingFraction: Double = 0.8
    ) -> some View {
        self.animation(
            .spring(response: response, dampingFraction: dampingFraction, blendDuration: 0.2),
            value: value
        )
        .drawingGroup()
    }
    
    func highPerformanceTransition<V: Equatable>(
        _ value: V,
        transition: AnyTransition = .opacity
    ) -> some View {
        self.transition(transition)
            .animation(.easeInOut(duration: 0.25), value: value)
            .drawingGroup()
    }
}

// MARK: - Optimized Kanban Board Animations

struct OptimizedKanbanBoardView: View {
    @StateObject private var viewModel = KanbanViewModel()
    @State private var draggedTask: AnimationTask?
    @State private var dragOffset = CGSize.zero
    @GestureState private var isDragging = false
    
    // Performance optimization
    @State private var shouldOptimizeAnimations = false
    
    var body: some View {
        GeometryReader { geometry in
            ScrollView(.horizontal, showsIndicators: false) {
                LazyHStack(spacing: 16) {
                    ForEach(viewModel.columns) { column in
                        ColumnView(
                            column: column,
                            tasks: viewModel.tasksFor(column),
                            draggedTask: $draggedTask,
                            shouldOptimize: shouldOptimizeAnimations
                        )
                        .frame(width: min(300, geometry.size.width * 0.8))
                    }
                }
                .padding(.horizontal)
            }
        }
        .coordinateSpace(name: "kanban")
        .onReceive(NotificationCenter.default.publisher(for: UIApplication.didReceiveMemoryWarningNotification)) { _ in
            // Enable performance optimizations on memory pressure
            shouldOptimizeAnimations = true
        }
        .onReceive(NotificationCenter.default.publisher(for: UIApplication.willEnterForegroundNotification)) { _ in
            // Reset optimizations when returning to foreground
            shouldOptimizeAnimations = false
        }
    }
}

struct ColumnView: View {
    let column: KanbanColumn
    let tasks: [AnimationTask]
    @Binding var draggedTask: AnimationTask?
    let shouldOptimize: Bool
    
    @State private var isHighlighted = false
    @State private var dropTargetPosition: CGPoint?
    
    var body: some View {
        VStack(spacing: 12) {
            // Column Header
            HStack {
                Text(column.title)
                    .font(.headline)
                    .fontWeight(.semibold)
                
                Spacer()
                
                Text("\(tasks.count)")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(Color.gray.opacity(0.2))
                    .cornerRadius(12)
            }
            .padding(.horizontal)
            
            // Tasks List
            LazyVStack(spacing: 8) {
                ForEach(tasks) { task in
                    OptimizedTaskCardView(
                        task: task,
                        isDragged: draggedTask?.id == task.id,
                        shouldOptimize: shouldOptimize
                    )
                    .onDrag {
                        draggedTask = task
                        return NSItemProvider(object: task.id as NSString)
                    }
                    .onDrop(of: [.text], delegate: TaskDropDelegate(
                        task: task,
                        column: column,
                        draggedTask: $draggedTask
                    ))
                }
            }
            .padding(.horizontal)
            
            Spacer()
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color(.systemGray6))
                .opacity(isHighlighted ? 0.8 : 1.0)
        )
        .scaleEffect(isHighlighted ? 1.02 : 1.0)
        .performanceOptimizedAnimation(isHighlighted)
        .onDrop(of: [.text], isTargeted: $isHighlighted) { providers in
            return handleDrop(providers: providers)
        }
    }
    
    private func handleDrop(providers: [NSItemProvider]) -> Bool {
        guard let draggedTask = draggedTask else { return false }
        
        // Move task to this column
        // Implementation would update the task's column
        self.draggedTask = nil
        return true
    }
}

struct OptimizedTaskCardView: View {
    let task: AnimationTask
    let isDragged: Bool
    let shouldOptimize: Bool
    
    @State private var isPressed = false
    @State private var cardOffset = CGSize.zero
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(task.title)
                    .font(.subheadline)
                    .fontWeight(.medium)
                    .lineLimit(2)
                
                Spacer()
                
                TaskPriorityIndicator(priority: task.priority)
            }
            
            if let description = task.description {
                Text(description)
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .lineLimit(3)
            }
            
            HStack {
                TaskStatusBadge(status: task.status)
                
                Spacer()
                
                if let assignee = task.assignee {
                    Text(assignee)
                        .font(.caption2)
                        .foregroundColor(.secondary)
                }
            }
        }
        .padding(12)
        .background(
            RoundedRectangle(cornerRadius: 8)
                .fill(Color(.systemBackground))
                .shadow(
                    color: .black.opacity(isDragged ? 0.3 : 0.1),
                    radius: isDragged ? 12 : 4,
                    x: 0,
                    y: isDragged ? 8 : 2
                )
        )
        .scaleEffect(isDragged ? 1.05 : isPressed ? 0.98 : 1.0)
        .offset(cardOffset)
        .opacity(isDragged ? 0.8 : 1.0)
        .rotationEffect(.degrees(isDragged ? 3 : 0))
        
        // Conditional animation optimization
        .modifier(ConditionalAnimationModifier(shouldOptimize: shouldOptimize, isDragged: isDragged, isPressed: isPressed))
        
        .onTapGesture {
            // Standard tap interaction - iOS HIG compliant
            // Brief press feedback for user interaction
            withAnimation(.easeInOut(duration: 0.1)) {
                isPressed = true
            }
            
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
                withAnimation(.easeInOut(duration: 0.1)) {
                    isPressed = false
                }
            }
        }
    }
}

// MARK: - Supporting Views

struct ConditionalAnimationModifier: ViewModifier {
    let shouldOptimize: Bool
    let isDragged: Bool
    let isPressed: Bool
    
    func body(content: Content) -> some View {
        if shouldOptimize {
            content
                .animation(.linear(duration: 0.1), value: isDragged)
                .animation(.linear(duration: 0.1), value: isPressed)
        } else {
            content
                .performanceOptimizedAnimation(isDragged)
                .performanceOptimizedAnimation(isPressed)
        }
    }
}

struct TaskPriorityIndicator: View {
    let priority: TaskPriority
    
    var body: some View {
        Circle()
            .fill(Color(priority.color))
            .frame(width: 8, height: 8)
    }
}

struct TaskStatusBadge: View {
    let status: AnimationTaskStatus
    
    var body: some View {
        Text(status.displayName)
            .font(.caption2)
            .fontWeight(.medium)
            .padding(.horizontal, 6)
            .padding(.vertical, 2)
            .background(status.color.opacity(0.2))
            .foregroundColor(status.color)
            .cornerRadius(4)
    }
}

// MARK: - Drop Delegate

struct TaskDropDelegate: DropDelegate {
    let task: AnimationTask
    let column: KanbanColumn
    @Binding var draggedTask: AnimationTask?
    
    func performDrop(info: DropInfo) -> Bool {
        guard let draggedTask = draggedTask else { return false }
        
        // Perform the drop operation
        // In a real implementation, this would update the backend
        self.draggedTask = nil
        return true
    }
    
    func dropUpdated(info: DropInfo) -> DropProposal? {
        return DropProposal(operation: .move)
    }
}

// MARK: - Conditional View Modifier

extension View {
    @ViewBuilder
    func `if`<Content: View>(_ condition: Bool, transform: (Self) -> Content, else elseTransform: (Self) -> Content) -> some View {
        if condition {
            transform(self)
        } else {
            elseTransform(self)
        }
    }
    
    @ViewBuilder
    func `if`<Content: View>(_ condition: Bool, transform: (Self) -> Content) -> some View {
        if condition {
            transform(self)
        } else {
            self
        }
    }
}

// MARK: - Performance Monitoring

class AnimationPerformanceMonitor: ObservableObject {
    @Published var frameRate: Double = 60.0
    @Published var droppedFrames: Int = 0
    @Published var animationComplexity: AnimationComplexity = .low
    
    private var displayLink: CADisplayLink?
    private var lastFrameTime: CFTimeInterval = 0
    private var frameCount = 0
    
    enum AnimationComplexity {
        case low, medium, high
        
        var maxConcurrentAnimations: Int {
            switch self {
            case .low: return 10
            case .medium: return 6
            case .high: return 3
            }
        }
    }
    
    func startMonitoring() {
        displayLink = CADisplayLink(target: self, selector: #selector(frameUpdate))
        displayLink?.add(to: .main, forMode: .common)
    }
    
    func stopMonitoring() {
        displayLink?.invalidate()
        displayLink = nil
    }
    
    @objc private func frameUpdate(displayLink: CADisplayLink) {
        let currentTime = displayLink.timestamp
        
        if lastFrameTime > 0 {
            let frameDuration = currentTime - lastFrameTime
            let currentFrameRate = 1.0 / frameDuration
            
            // Update frame rate with exponential moving average
            frameRate = frameRate * 0.9 + currentFrameRate * 0.1
            
            // Count dropped frames (if frame time > 16.67ms for 60fps)
            if frameDuration > 1.0/60.0 + 0.002 { // 2ms tolerance
                droppedFrames += 1
            }
            
            // Adjust animation complexity based on performance
            updateAnimationComplexity()
        }
        
        lastFrameTime = currentTime
        frameCount += 1
        
        // Reset counters every second
        if frameCount >= 60 {
            frameCount = 0
            droppedFrames = max(0, droppedFrames - 1) // Gradual recovery
        }
    }
    
    private func updateAnimationComplexity() {
        if frameRate < 45 || droppedFrames > 5 {
            animationComplexity = .high
        } else if frameRate < 55 || droppedFrames > 2 {
            animationComplexity = .medium
        } else {
            animationComplexity = .low
        }
    }
}

// MARK: - Supporting Types

// Use a different name to avoid conflict with global Task model
struct AnimationTask: Identifiable, Codable {
    let id: String
    let title: String
    let description: String?
    let status: AnimationTaskStatus
    let priority: TaskPriority
    let assignee: String?
    let columnId: String
    
    init(id: String = UUID().uuidString, title: String, description: String? = nil, status: AnimationTaskStatus, priority: TaskPriority, assignee: String? = nil, columnId: String) {
        self.id = id
        self.title = title
        self.description = description
        self.status = status
        self.priority = priority
        self.assignee = assignee
        self.columnId = columnId
    }
}

enum AnimationTaskStatus: String, CaseIterable, Codable {
    case todo = "todo"
    case inProgress = "in_progress"
    case review = "review"
    case done = "done"
    
    var displayName: String {
        switch self {
        case .todo: return "To Do"
        case .inProgress: return "In Progress"
        case .review: return "Review"
        case .done: return "Done"
        }
    }
    
    var color: Color {
        switch self {
        case .todo: return .gray
        case .inProgress: return .blue
        case .review: return .orange
        case .done: return .green
        }
    }
}

struct KanbanColumn: Identifiable, Codable {
    let id: String
    let title: String
    let order: Int
    
    init(id: String = UUID().uuidString, title: String, order: Int) {
        self.id = id
        self.title = title
        self.order = order
    }
}

// MARK: - ViewModel

@MainActor
class KanbanViewModel: ObservableObject {
    @Published var columns: [KanbanColumn] = []
    @Published var tasks: [AnimationTask] = []
    
    init() {
        loadDefaultData()
    }
    
    func tasksFor(_ column: KanbanColumn) -> [AnimationTask] {
        return tasks.filter { $0.columnId == column.id }
    }
    
    private func loadDefaultData() {
        columns = [
            KanbanColumn(title: "To Do", order: 0),
            KanbanColumn(title: "In Progress", order: 1),
            KanbanColumn(title: "Review", order: 2),
            KanbanColumn(title: "Done", order: 3)
        ]
        
        // Sample tasks
        tasks = [
            AnimationTask(title: "Design UI Components", status: .todo, priority: .high, columnId: columns[0].id),
            AnimationTask(title: "Implement API Integration", status: .inProgress, priority: .medium, assignee: "John", columnId: columns[1].id),
            AnimationTask(title: "Write Unit Tests", status: .review, priority: .low, assignee: "Sarah", columnId: columns[2].id),
            AnimationTask(title: "Deploy to Production", status: .done, priority: .urgent, assignee: "Mike", columnId: columns[3].id)
        ]
    }
}