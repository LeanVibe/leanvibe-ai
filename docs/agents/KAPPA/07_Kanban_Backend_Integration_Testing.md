# KAPPA Agent - Task 07: Kanban Backend Integration & Testing Validation

**Assignment Date**: Sprint 1 Integration Phase  
**Worktree**: Use existing `../leenvibe-ios-visualization`  
**Branch**: `feature/kanban-backend-integration`  
**Status**: 🚨 **HIGH PRIORITY** - Validate Your 2,662+ Line Kanban UI Works!

## Mission Brief

**INTEGRATION VALIDATION**: The Backend Task Management APIs are now LIVE! Your beautifully crafted 2,662+ line Kanban UI needs to be connected and validated with the real backend. Additionally, your 9,755+ line testing framework needs to verify the entire integrated system works flawlessly.

## Critical Context

- ✅ **Backend APIs COMPLETE**: All Task Management endpoints implemented and tested
- ✅ **Your Kanban UI**: 2,662+ lines waiting for backend connection
- ✅ **Your Testing Framework**: 9,755+ lines ready to validate everything
- 🎯 **IMPACT**: Major MVP feature becomes fully functional

## Your Integration Mission

### 1. Connect Kanban UI to Backend APIs

**Update KanbanService.swift** to use real backend:
```swift
// Replace mock data with real API calls
class KanbanService: ObservableObject {
    private let baseURL = "http://localhost:8000/api/tasks"
    
    func fetchKanbanBoard() async throws -> KanbanBoard {
        let url = URL(string: "\(baseURL)/kanban/board")!
        let (data, _) = try await URLSession.shared.data(from: url)
        return try JSONDecoder().decode(KanbanBoard.self, from: data)
    }
    
    func moveTask(taskId: String, to status: TaskStatus) async throws {
        let url = URL(string: "\(baseURL)/\(taskId)/status")!
        var request = URLRequest(url: url)
        request.httpMethod = "PUT"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let statusUpdate = ["status": status.rawValue]
        request.httpBody = try JSONEncoder().encode(statusUpdate)
        
        let (data, _) = try await URLSession.shared.data(for: request)
        // Handle response
    }
}
```

### 2. WebSocket Real-time Updates

**Integrate WebSocket for live updates**:
```swift
extension KanbanService {
    func connectWebSocket() {
        webSocketService.messagesPublisher
            .filter { $0.type == "task_update" }
            .sink { [weak self] message in
                self?.handleTaskUpdate(message)
            }
            .store(in: &cancellables)
    }
    
    private func handleTaskUpdate(_ message: AgentMessage) {
        // Update local Kanban state based on WebSocket message
        // Refresh UI with new task positions
    }
}
```

### 3. Comprehensive Integration Testing

**Create KanbanIntegrationTests.swift**:
```swift
class KanbanIntegrationTests: XCTestCase {
    func testCreateTaskAppearsInBacklog() async throws {
        // Create task via API
        let task = try await api.createTask(title: "Test Task")
        
        // Verify appears in Kanban board
        let board = try await kanbanService.fetchKanbanBoard()
        XCTAssert(board.backlog.contains(where: { $0.id == task.id }))
    }
    
    func testDragAndDropUpdatesBackend() async throws {
        // Create task
        let task = try await api.createTask(title: "Drag Test")
        
        // Simulate drag to in_progress
        try await kanbanService.moveTask(taskId: task.id, to: .inProgress)
        
        // Verify backend updated
        let updatedTask = try await api.getTask(task.id)
        XCTAssertEqual(updatedTask.status, .inProgress)
    }
    
    func testWebSocketRealtimeUpdates() async throws {
        // Connect WebSocket
        await webSocketService.connect()
        
        // Create task from another client
        let task = try await api.createTask(title: "Realtime Test")
        
        // Verify Kanban UI updated automatically
        await fulfillment(of: [kanbanUpdateExpectation], timeout: 5.0)
        XCTAssert(kanbanView.hasTask(withId: task.id))
    }
}
```

### 4. End-to-End Workflow Testing

**Test complete user workflows**:
- Create task → Appears in backlog
- Drag to in_progress → Backend updates
- Another user moves task → Your UI updates
- Delete task → Removes from board
- Bulk operations → UI handles efficiently

### 5. Performance Validation

Using your testing framework, validate:
- Task creation < 500ms
- Drag-and-drop < 200ms response
- WebSocket updates < 100ms
- Smooth animations during moves
- Memory usage stable with 100+ tasks

## Success Criteria

### Integration Complete When:
- [ ] All Kanban CRUD operations use real backend APIs
- [ ] WebSocket real-time updates working
- [ ] Drag-and-drop persists to backend
- [ ] All integration tests passing
- [ ] Performance targets met
- [ ] Error handling for network issues
- [ ] Offline mode with sync

### Testing Framework Validation:
- [ ] Your 9,755+ line test suite runs against integrated system
- [ ] New integration tests cover all workflows
- [ ] Performance benchmarks documented
- [ ] Edge cases handled gracefully

## Technical Implementation Notes

1. **API Response Mapping**: Ensure your Task models match backend response
2. **Error Handling**: Network failures, timeout, invalid responses
3. **Optimistic Updates**: Update UI immediately, sync with backend
4. **Conflict Resolution**: Handle concurrent edits
5. **State Management**: Keep local state in sync with backend

## Why This Is Critical

Your Kanban UI is the **centerpiece of the MVP**. With these backend connections:
- Project managers can track tasks in real-time
- Multiple users can collaborate simultaneously  
- Changes persist across app restarts
- The full vision of LeenVibe comes to life

## Resources

- Backend API Documentation: `/api/docs`
- Task API Endpoints: See `app/api/endpoints/tasks.py`
- WebSocket Protocol: See Task Update messages
- Your existing code: `KanbanBoardView.swift`, `TaskCardView.swift`

## Priority

**🚨 HIGHEST** - This unlocks the primary MVP feature and validates months of work!

**Task 7**: Bring your Kanban to life with real backend power! 🎯📱🚀