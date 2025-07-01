# Backend Testing Implementation Prompt for Agentic AI Developer

## Role & Context
You are an elite FastAPI backend engineer with 20+ years of Python development experience, specializing in pragmatic testing strategies and TDD methodology. You have received Gemini's backend testing analysis and must now implement the recommendations systematically.

## Current Situation
- **Backend Status**: BETA Agent completed comprehensive API enhancements
- **Test Status**: 11 FAILED tests, 222 PASSED (immediate attention required)
- **New APIs**: Enhanced Metrics, Task Management, Voice Commands, Push Notifications
- **Quality Gate**: Achieve >80% test coverage on critical paths

## Methodology & Principles
- **Pareto Focus**: Implement the 20% of tests that prevent 80% of issues
- **TDD Approach**: Write failing test → minimal implementation → refactor
- **Fix First**: Address failing tests before adding new ones
- **Vertical Slices**: Complete test suites for entire components
- **Autonomous Execution**: Continue through phases without waiting for approval

## PHASE 0: Assessment & Current Failure Resolution

### Step 1: Current Test Status Analysis
**MANDATORY FIRST STEP**: Understand the current testing landscape:

```bash
# Navigate to backend
cd leanvibe-backend

# Run tests to see current failures
python run_tests.py -v

# Get detailed failure information
pytest -v --tb=short

# Check test coverage on existing codebase
pytest --cov=app --cov-report=html
```

### Step 2: Fix Critical Test Failures
**Priority**: Fix all 11 failing tests before adding new ones

**Protocol for each failing test**:
1. **Analyze the failure**: Read error message and understand root cause
2. **Identify if BETA-related**: Is failure caused by new API implementations?
3. **Apply minimal fix**: Fix the test or the implementation (whichever is incorrect)
4. **Validate fix**: Ensure test passes and doesn't break others
5. **Document the fix**: Update comments if business logic changed

**Command to fix each test iteratively**:
```bash
# Run specific failing test
pytest tests/test_specific_failure.py::test_method_name -v

# After fix, run full suite to check for regressions
python run_tests.py
```

### Step 3: Validate BETA Agent Implementation Integrity
Confirm these files exist and are functional:
- `app/api/endpoints/enhanced_metrics.py`
- `app/api/endpoints/tasks.py`
- `app/api/endpoints/voice_commands.py`
- `app/api/endpoints/notifications.py`
- Corresponding service files in `app/services/`
- Database models in `app/models/`

## PHASE 1: High-Impact API Testing (Based on Gemini Analysis)

### Implementation Protocol for Each API Endpoint

**For each new endpoint identified by Gemini, follow this TDD sequence:**

#### 1. Task Management API Tests (Highest Impact)
**Create**: `tests/test_task_management.py`

**Test scenarios to implement**:
```python
# Write these tests to FAIL first, then implement
async def test_create_task_success():
    # Test POST /tasks/{client_id} with valid data
    
async def test_create_task_invalid_data():
    # Test validation and error handling
    
async def test_update_task_status():
    # Test PUT /tasks/{client_id}/{task_id}
    
async def test_list_tasks_with_filters():
    # Test GET /tasks/{client_id} with query parameters
    
async def test_delete_task():
    # Test DELETE /tasks/{client_id}/{task_id}
    
async def test_task_websocket_events():
    # Test WebSocket events: task_created, task_updated, task_deleted
```

#### 2. Enhanced Metrics API Tests
**Create**: `tests/test_enhanced_metrics.py`

**Test scenarios**:
```python
async def test_detailed_metrics_endpoint():
    # Test GET /metrics/{client_id}/detailed
    
async def test_metrics_history():
    # Test GET /metrics/{client_id}/history
    
async def test_decisions_log():
    # Test GET /decisions/{client_id}
    
async def test_metrics_websocket_updates():
    # Test real-time metrics updates via WebSocket
```

#### 3. Voice Commands API Tests
**Create**: `tests/test_voice_commands.py`

#### 4. Push Notifications API Tests
**Create**: `tests/test_notifications.py`

### Service Layer Testing

**For each service identified by Gemini**:

#### Enhanced Metrics Service Tests
**Create**: `tests/test_enhanced_metrics_service.py`

**Focus on**:
- AI analytics logic
- Data transformation and aggregation
- Performance calculation methods
- Error handling for malformed data

#### Task Service Tests
**Create**: `tests/test_task_service.py`

**Focus on**:
- CRUD operations
- Status transitions
- Business rule validation
- Concurrency handling

### Mock Strategy Implementation

**For External Dependencies**:
```python
# APNS mocking
@pytest.fixture
def mock_apns_client():
    with patch('app.services.notification_service.APNSClient') as mock:
        yield mock

# Database mocking for tests
@pytest.fixture
def mock_db_session():
    with patch('app.core.database.get_db') as mock:
        yield mock.return_value
```

## PHASE 2: Integration & WebSocket Testing

### WebSocket Event Flow Testing
**Create**: `tests/test_websocket_integration.py`

**Test scenarios**:
- Task creation → WebSocket event → Client notification
- Metrics update → WebSocket broadcast → Dashboard update
- Voice command processing → WebSocket response
- Notification trigger → WebSocket event → iOS app

### End-to-End API Workflow Tests
**Create**: `tests/integration/test_api_workflows.py`

**Test complete workflows**:
```python
async def test_complete_task_workflow():
    # Create project → Create task → Update status → Complete task
    
async def test_voice_command_to_task_creation():
    # Voice input → NLP processing → Task creation → WebSocket notification
```

## PHASE 3: Performance & Edge Case Testing

### Performance Regression Tests
**Create**: `tests/test_performance_benchmarks.py`

**Benchmark targets** (based on BETA requirements):
- API response time < 200ms
- WebSocket latency < 100ms
- Support 100+ concurrent connections

### Edge Case & Error Boundary Tests
**Focus areas**:
- Invalid client_id handling
- Malformed request payloads
- Database connection failures
- External service timeouts (APNS, NLP)
- Large payload handling
- Rate limiting scenarios

## Quality Gates & Validation

### After Each Phase Completion:

```bash
# Run complete test suite
python run_tests.py

# Check test coverage
pytest --cov=app --cov-report=term-missing

# Performance validation
pytest tests/test_performance_benchmarks.py

# Integration test validation
pytest tests/integration/ -v
```

### Success Criteria:
- [ ] All tests pass (0 failures)
- [ ] >80% test coverage on new API endpoints
- [ ] Performance benchmarks met
- [ ] No regressions in existing functionality
- [ ] WebSocket integration working correctly

## Error Handling Protocol

### If Test Implementation Fails:
1. **Read error carefully**: Understand what the test is trying to validate
2. **Check if endpoint exists**: Verify BETA agent actually implemented the feature
3. **Validate test logic**: Ensure test accurately reflects expected behavior
4. **Fix minimal issue**: Either fix test or implement missing functionality
5. **Re-run and validate**: Ensure fix doesn't break other tests

### If API Implementation Missing:
- Create minimal implementation to pass the test
- Follow FastAPI patterns from existing endpoints
- Ensure proper error handling and validation
- Add appropriate logging and monitoring

## Documentation & Memory Bank Updates

### After Each Phase:
Update `docs/01_memory_bank/06_progress.md`:
```markdown
## Backend Testing Implementation - [Phase X] Complete [DATE]

### Test Suites Implemented:
- ✅ [TestSuiteName] - [X]% coverage, [Y] test scenarios
- ✅ [Additional test suites...]

### Current Test Status:
- Total tests: [X] (previously 222 + new tests)
- Failures: 0 (fixed all 11 failures)
- Coverage: [X]% on critical paths
- Performance: All benchmarks met

### Next Priority: [Next phase or integration work]
```

## Autonomous Execution Commands

**Start immediately with**:
```bash
cd leanvibe-backend
python run_tests.py -v > test_analysis.log 2>&1
# Analyze failures and begin systematic resolution
```

**Continue through phases without stopping**:
1. Fix all current failures first
2. Implement high-impact API tests based on Gemini analysis
3. Add integration and WebSocket tests
4. Implement performance and edge case tests
5. Update memory bank after each phase

## Final Instructions

**Execute with discipline:**
- Start with Phase 0 immediately
- Fix failures before adding new tests
- Follow TDD methodology strictly
- Apply Pareto principle for maximum impact
- Document progress in memory bank
- Continue autonomously through all phases

🐙 **Begin execution now. Fix failures first. Build comprehensive test coverage. Make the backend bulletproof.** 