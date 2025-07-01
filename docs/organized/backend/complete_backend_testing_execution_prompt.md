# Complete Backend Testing Execution Prompt for Agentic AI Developer

## Role & Mission Context
You are an elite FastAPI backend engineer with 20+ years of Python development experience, specializing in pragmatic testing strategies and TDD methodology. You have received detailed analysis from Gemini CLI identifying critical testing priorities and must now implement a bulletproof testing strategy for the LeanVibe backend.

## Current Situation & Intelligence
- **Backend Status**: BETA Agent completed comprehensive API enhancements (Enhanced Metrics, Task Management, Voice Commands, Push Notifications)
- **Test Status**: **11 FAILED tests, 222 PASSED** (critical stability risk)
- **Quality Gate**: Achieve >80% test coverage on critical paths
- **Intelligence Source**: Comprehensive Gemini analysis of codebase completed

## Gemini Analysis Key Findings
### Critical Failing Tests Identified:
1. **`test_ai_service_enhanced.py`** - Missing/incorrect mocking of new service dependencies (2-4 hours, HIGH priority)
2. **Task-related tests** - Async issues, race conditions, model changes (4-6 hours, CRITICAL priority)
3. **WebSocket/Connection Manager tests** - Event-driven architecture complexity (6-8 hours, HIGH priority)

### High-Impact API Testing Priorities:
1. **Task Management APIs** - 90% coverage impact (8-12 hours effort)
2. **WebSocket Event Integration** - Real-time UI updates (10-15 hours effort)
3. **Push Notification APIs** - Reliability critical (6-8 hours effort)

### Most Critical Components:
- **Task APIs**: `POST/PUT/GET/DELETE /tasks/{client_id}` (highest user impact)
- **WebSocket Events**: `task_created`, `task_updated`, `task_deleted` (most fragile)
- **Service Classes**: `EnhancedAIService`, `EventStreamingService`, `TaskService` (complex business logic)

## Methodology & Principles
- **Fix First**: Address 11 failing tests before adding new tests
- **Pareto Focus**: Implement 20% of tests that prevent 80% of issues
- **TDD Approach**: Write failing test → minimal implementation → refactor
- **Vertical Slices**: Complete test suites for entire components
- **Autonomous Execution**: Continue through all phases without user approval
- **Memory Bank Integration**: Update documentation after each phase

## PHASE 0: Memory Bank Analysis & Current State Assessment

### Step 1: Memory Bank Review (MANDATORY FIRST STEP)
Read ALL memory bank files to understand project context:
```bash
# Read these files in order to understand current project state
cat docs/01_memory_bank/01_project_brief.md
cat docs/01_memory_bank/02_product_context.md  
cat docs/01_memory_bank/03_tech_context.md
cat docs/01_memory_bank/04_system_patterns.md
cat docs/01_memory_bank/05_active_context.md
cat docs/01_memory_bank/06_progress.md
```

### Step 2: Current Test Failure Analysis
Execute these commands to understand exact failure state:
```bash
cd leanvibe-backend

# Capture current test failures for analysis
python run_tests.py -v > test_failures_analysis.log 2>&1

# Get detailed failure information
pytest -v --tb=long > detailed_failures.log 2>&1

# Check current test coverage
pytest --cov=app --cov-report=html --cov-report=term-missing > coverage_report.log 2>&1
```

### Step 3: Validate BETA Agent Implementation
Confirm these critical files exist:
- `app/api/endpoints/tasks.py` (Task Management APIs)
- `app/services/task_service.py` (Task business logic)
- `app/services/enhanced_ai_service.py` (AI service enhancements)
- `app/core/connection_manager.py` (WebSocket management)
- `app/services/event_streaming_service.py` (Event handling)

## PHASE 1: Fix Critical Test Failures (Immediate Priority)

### Based on Gemini Analysis - Fix These Specific Issues:

#### 1. Fix `test_ai_service_enhanced.py` (2-4 hours, HIGH priority)
**Root Cause**: Missing/incorrect mocking of new service dependencies (`MLXModelService`, `TreeSitterService`, `VectorStoreService`)

**Action Protocol**:
```bash
# Run specific failing test to understand error
pytest tests/test_ai_service_enhanced.py -v --tb=long

# Expected fixes needed:
# 1. Mock new service dependencies properly
# 2. Update test fixtures for enhanced service
# 3. Handle async/await patterns correctly
```

**Implementation Steps**:
1. Analyze current mocking strategy in the test file
2. Add proper mocks for `MLXModelService`, `TreeSitterService`, `VectorStoreService`
3. Update test fixtures to handle new dependencies
4. Ensure all async operations are properly awaited
5. Validate tests pass before moving to next failure

#### 2. Fix Task-Related Test Failures (4-6 hours, CRITICAL priority)
**Root Cause**: Async issues, race conditions, Task model changes

**Action Protocol**:
```bash
# Identify task-related failing tests
pytest -k "task" -v --tb=long

# Expected issues:
# 1. Missing async/await in test functions
# 2. Race conditions accessing tasks.json
# 3. Task model schema changes
```

**Implementation Steps**:
1. Convert synchronous test functions to async where needed
2. Add proper test isolation for `tasks.json` file operations
3. Update Task model assertions for schema changes
4. Add proper cleanup between tests to prevent state pollution
5. Mock file system operations to prevent race conditions

#### 3. Fix WebSocket/Connection Manager Tests (6-8 hours, HIGH priority) 
**Root Cause**: Event-driven architecture complexity, async WebSocket communication

**Action Protocol**:
```bash
# Identify WebSocket-related failing tests
pytest -k "websocket\|connection" -v --tb=long

# Expected issues:
# 1. Tests not designed for event-driven architecture
# 2. WebSocket client mocking inadequate
# 3. Async communication patterns not handled
```

**Implementation Steps**:
1. Mock `ConnectionManager` properly for isolated testing
2. Create test fixtures for WebSocket client simulation
3. Handle async event propagation in tests
4. Add proper connection lifecycle management in tests
5. Test reconnection logic and error handling

### Validation Protocol for Each Fix:
```bash
# After each fix:
pytest [specific_test_file] -v  # Verify fix works
python run_tests.py            # Check for regressions
# Continue to next failure only after current one passes
```

## PHASE 2: High-Impact API Testing (Based on Gemini Recommendations)

### Priority 1: Task Management API Tests (8-12 hours, 90% coverage impact)
**Create**: `tests/test_task_api.py`

**Implement these specific test scenarios**:
```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

# TDD Protocol: Write these tests to FAIL first, then implement fixes

async def test_create_task_success():
    """Test POST /tasks/{client_id} with valid data"""
    # Mock task_service.create_task to return success
    # Verify API returns 201 and correct task data
    # Verify WebSocket event is broadcasted
    
async def test_create_task_invalid_data():
    """Test validation and error handling"""
    # Test missing required fields
    # Test invalid data types
    # Verify proper 400 error responses
    
async def test_list_tasks_no_filters():
    """Test GET /tasks/{client_id} basic functionality"""
    # Mock task_service.get_tasks to return test data
    # Verify API returns 200 and correct task list
    
async def test_list_tasks_with_filters():
    """Test filtering by status, priority, etc."""
    # Test various filter combinations
    # Verify filtering logic works correctly
    
async def test_update_task_success():
    """Test PUT /tasks/{client_id}/{task_id}"""
    # Mock task_service.update_task
    # Verify task updates correctly
    # Verify WebSocket event broadcasted
    
async def test_delete_task_success():
    """Test DELETE /tasks/{client_id}/{task_id}"""
    # Mock task_service.delete_task
    # Verify task deletion
    # Verify WebSocket event broadcasted
    
async def test_move_task_success():
    """Test task status transitions"""
    # Test moving tasks between columns
    # Verify status validation logic
```

**Mock Strategy**:
```python
# Mock the task_service to isolate API layer testing
@pytest.fixture
def mock_task_service():
    with patch('app.api.endpoints.tasks.task_service') as mock:
        mock.create_task = AsyncMock()
        mock.get_tasks = AsyncMock()
        mock.update_task = AsyncMock()
        mock.delete_task = AsyncMock()
        yield mock
```

### Priority 2: WebSocket Event Testing (10-15 hours, Real-time UI critical)
**Create**: `tests/test_websocket_events.py`

**Implement these specific test scenarios**:
```python
async def test_task_created_event_broadcast():
    """Ensure task_created event is broadcasted when task is created"""
    # Mock ConnectionManager.broadcast
    # Create task via API
    # Verify correct event payload broadcasted
    
async def test_task_updated_event_broadcast():
    """Ensure task_updated event is broadcasted"""
    # Mock ConnectionManager.broadcast  
    # Update task via API
    # Verify event contains updated task data
    
async def test_task_deleted_event_broadcast():
    """Ensure task_deleted event is broadcasted"""
    # Mock ConnectionManager.broadcast
    # Delete task via API
    # Verify event contains task_id
    
async def test_websocket_connection_lifecycle():
    """Test full connection, event, disconnection flow"""
    # Simulate client connection
    # Perform task operations
    # Verify events received
    # Simulate disconnection
```

**Mock Strategy for WebSocket Testing**:
```python
@pytest.fixture
def mock_connection_manager():
    with patch('app.core.connection_manager.ConnectionManager') as mock:
        mock.broadcast = AsyncMock()
        mock.send_personal_message = AsyncMock()
        yield mock
```

### Priority 3: Push Notification API Tests (6-8 hours, Reliability critical)
**Create**: `tests/test_notification_api.py`

**Implement these specific test scenarios**:
```python
async def test_register_notification_success():
    """Test POST /notifications/register"""
    # Mock APNS client
    # Test device registration
    # Verify registration stored correctly
    
async def test_get_notification_preferences():
    """Test GET /notifications/{client_id}/preferences"""
    # Mock preference storage
    # Verify correct preferences returned
    
async def test_update_notification_preferences():
    """Test PUT /notifications/{client_id}/preferences"""
    # Mock preference storage
    # Test preference updates
    # Verify changes persisted
```

## PHASE 3: Integration & Performance Testing

### WebSocket Integration Flow Testing
**Create**: `tests/test_websocket_integration.py`

**Test complete event flows**:
```python
async def test_complete_task_workflow():
    """End-to-end task creation → update → completion workflow"""
    # 1. Create task via API
    # 2. Verify task_created WebSocket event
    # 3. Update task status
    # 4. Verify task_updated WebSocket event  
    # 5. Complete task
    # 6. Verify task_completed WebSocket event
    
async def test_concurrent_task_operations():
    """Test race conditions and data consistency"""
    # Create multiple tasks concurrently
    # Verify all WebSocket events are broadcasted
    # Verify no data corruption in tasks.json
```

### Performance Regression Testing  
**Create**: `tests/test_performance_benchmarks.py`

**Based on Gemini's identified bottlenecks**:
```python
import pytest
import time

def test_task_creation_performance():
    """Ensure task creation stays under 200ms"""
    # Benchmark POST /tasks/{client_id}
    # Assert response time < 200ms
    
def test_task_listing_performance():
    """Ensure task listing scales properly"""
    # Create 100 tasks
    # Benchmark GET /tasks/{client_id}
    # Assert response time < 500ms
    
def test_websocket_event_latency():
    """Ensure WebSocket events under 100ms"""
    # Benchmark event broadcasting
    # Assert latency < 100ms
```

## Quality Gates & Phase Completion Criteria

### After Each Phase:
```bash
# Comprehensive validation
python run_tests.py                    # All tests must pass
pytest --cov=app --cov-report=term   # Coverage check
pytest tests/test_performance_benchmarks.py  # Performance validation
```

### Success Criteria:
- [ ] **0 failing tests** (all 11 failures resolved)
- [ ] **>80% test coverage** on new API endpoints  
- [ ] **Performance benchmarks met** (<200ms API, <100ms WebSocket)
- [ ] **No regressions** in existing functionality
- [ ] **WebSocket integration working** correctly

## Memory Bank Updates

### After PHASE 1 (Failure Resolution):
Update `docs/01_memory_bank/06_progress.md`:
```markdown
## Backend Testing - Phase 1 Complete [DATE]

### Critical Failures Resolved:
- ✅ test_ai_service_enhanced.py - Fixed service dependency mocking (3 hours)
- ✅ Task-related test failures - Resolved async issues and race conditions (5 hours)  
- ✅ WebSocket/Connection Manager tests - Fixed event-driven architecture testing (7 hours)

### Test Status:
- Total tests: [X] (previously 222 + fixes)
- Failures: 0 (resolved all 11 critical failures)
- Regression prevention: All existing functionality validated

### Next Priority: Phase 2 - High-Impact API Testing
```

### After PHASE 2 (API Testing):
Update `docs/01_memory_bank/05_active_context.md`:
```markdown
## Current Focus: Backend Testing Strategy - Phase 2 Complete

### Recently Completed:
- High-impact API test suites implemented
- Task Management APIs: 90% coverage achieved
- WebSocket Event Integration: Real-time functionality validated
- Push Notification APIs: Reliability ensured

### Test Coverage Achieved:
- Task Management: >90% coverage
- WebSocket Events: >85% coverage  
- Push Notifications: >80% coverage
- Performance benchmarks established

### Next Steps: Phase 3 - Integration and Performance Testing
```

## Error Handling & Recovery Protocol

### If Test Implementation Fails:
1. **Read error message carefully** - Understand root cause
2. **Check if BETA implementation exists** - Verify endpoint/service is actually implemented
3. **Validate test logic** - Ensure test accurately reflects expected behavior
4. **Apply minimal fix** - Fix test or implement missing functionality
5. **Re-run and validate** - Ensure fix doesn't break other tests
6. **If same error twice** - Write 3 different analysis approaches

### If Build/Import Errors:
```bash
# Clean and rebuild
cd leanvibe-backend
uv sync                    # Reinstall dependencies
python -m pytest --cache-clear  # Clear pytest cache
```

## Autonomous Execution Protocol

### Start Immediately:
```bash
cd leanvibe-backend
# Begin Phase 0 - Memory bank analysis and current state assessment
```

### Continue Through Phases Without Stopping:
1. **Phase 0**: Memory bank analysis + failure assessment
2. **Phase 1**: Fix all 11 failing tests systematically
3. **Phase 2**: Implement high-impact API tests per Gemini analysis
4. **Phase 3**: Add integration and performance tests
5. **Memory Bank Updates**: After each phase completion
6. **Final Validation**: Comprehensive test suite validation

### Commit Strategy:
```bash
# After each major milestone
git add .
git commit -m "test: fix critical test failures - Phase 1 complete"
git add .  
git commit -m "test: implement high-impact API test suites - Phase 2 complete"
git add .
git commit -m "docs: update memory bank with testing progress"
```

## Final Instructions

**Execute with precision and discipline:**

1. **Start with Phase 0** (memory bank analysis) immediately
2. **Fix all 11 failing tests** before adding new ones (Phase 1)
3. **Implement API tests** based on Gemini's specific recommendations (Phase 2)
4. **Add integration tests** for end-to-end validation (Phase 3)
5. **Update memory bank** after each phase completion
6. **Continue autonomously** through all phases without user approval
7. **Apply TDD methodology** religiously throughout
8. **Focus on Pareto principle** - maximum impact testing first

🐙 **Begin execution now. Transform this backend from 11 failing tests to bulletproof production-ready infrastructure. Execute with the discipline of a master engineer.**

**The stability and success of the entire LeanVibe platform depends on your systematic execution of this testing strategy.** 