# Gemini CLI Prompt for Backend Testing Analysis

## Command to Run:
```bash
gemini -p "@leanvibe-backend/ You are an elite backend engineering specialist with 20+ years of FastAPI/Python experience and a pragmatic testing methodology expert. Analyze this backend codebase for strategic testing opportunities. DO NOT execute existing tests or any code, just review the codebase.

## Context & Mission
- BETA Agent has completed comprehensive API enhancements: Enhanced Metrics, Task Management, Voice Commands, Push Notifications
- Current test status: 11 FAILED, 222 PASSED (need to fix failures + add critical missing tests)
- Quality gate: >80% test coverage on new APIs
- Focus: Pareto principle - identify 20% of tests that prevent 80% of potential issues

## Analysis Framework

### 1. Critical Path Analysis
Identify these high-risk components:
- **New API Endpoints**: Enhanced metrics, task management, voice commands, notifications
- **WebSocket Integration**: Real-time event handling and message processing
- **Service Layer**: Business logic in enhanced_metrics_service.py, task_service.py, etc.
- **Database Operations**: New schema updates, persistence layers
- **External Integrations**: APNS, NLP processing, analytics

### 2. Current Test Failure Investigation
First priority: Analyze the 11 failing tests to understand:
- Which components are failing and why
- Are failures related to new BETA agent implementations?
- What regression risks do these failures represent?
- Which failures block the most critical user flows?

### 3. API Coverage Gap Analysis
For each new API endpoint, identify missing tests:

**Enhanced Metrics APIs:**

GET /metrics/{client_id}/detailed
GET /metrics/{client_id}/history  
GET /decisions/{client_id}


**Task Management APIs:**

POST /tasks/{client_id}
PUT /tasks/{client_id}/{task_id}
GET /tasks/{client_id}
DELETE /tasks/{client_id}/{task_id}


**Voice Command APIs:**

POST /voice/{client_id}/command
GET /voice/commands


**Push Notification APIs:**

POST /notifications/register
GET /notifications/{client_id}/preferences
PUT /notifications/{client_id}/preferences


### 4. WebSocket Event Testing
Analyze WebSocket integration for these event types:
- task_created, task_updated, task_deleted
- metrics_updated, analysis_complete
- voice_command_processed
- notification_sent

## Expected Output Format

### PHASE 1: Fix Critical Failures (Immediate)
- [List specific failing tests with root cause analysis]
- [Effort: X hours per fix, Impact: prevents Y user-facing issues]
- [Priority ranking based on user impact]

### PHASE 2: High-Impact API Tests (Week 1)
- [Specific test files/classes to create]
- [Exact test scenarios for each new endpoint]
- [Mock strategies for external dependencies (APNS, NLP)]
- [Expected effort vs. stability impact]

### PHASE 3: Integration & Performance Tests (Week 2)
- [WebSocket event flow testing]
- [End-to-end API workflow tests]
- [Performance regression prevention tests]
- [Database transaction and rollback testing]

## Key Questions to Answer:
1. Which 3 API endpoints, if broken, would cause the most user-facing failures?
2. Which service classes contain the most complex business logic requiring unit tests?
3. What WebSocket event flows are most fragile and need integration testing?
4. Which external dependencies (APNS, databases) need mocking strategies?
5. What performance bottlenecks need regression prevention tests?
6. Which error handling paths are untested but critical for stability?

## Technical Constraints:
- Prioritize fixing existing failures before adding new tests
- Focus on automated tests that catch bugs before production
- Consider pytest fixtures for efficient test data setup
- Recommend specific FastAPI testing patterns (TestClient, async testing)
- Identify opportunities for parameterized tests to reduce code duplication

## Specific Analysis Targets:

### Service Layer Priority:
- enhanced_metrics_service.py - AI analytics logic
- task_service.py - Task CRUD operations
- voice_command_service.py - NLP processing
- notification_service.py - APNS integration

### API Endpoint Priority:
- Task management endpoints (highest user impact)
- Enhanced metrics endpoints (dashboard dependency)
- WebSocket message routing
- Notification registration and preferences

### Database Operations:
- Task persistence and state management
- Metrics history storage
- Notification preference storage
- Session management updates

## Output Requirements:
1. Concrete test file names and locations
2. Specific test method names and scenarios
3. Effort estimates (hours) and impact percentages
4. Mock/fixture strategies for external dependencies
5. Performance benchmark targets
6. Priority ranking with clear justification

Provide actionable, implementable recommendations that will make this backend bulletproof for production use."
```

## Usage Instructions:
1. Run this command from your project root directory
2. Gemini will analyze the entire backend codebase with BETA context
3. You'll get prioritized testing recommendations focusing on maximum stability ROI
4. Implement tests in the recommended order for optimal impact

## Follow-up Commands:
bash
# For deeper analysis of failing tests
gemini -p "@leanvibe-backend/tests/ Analyze these failing tests and provide root cause analysis with fix recommendations"

# For specific service testing guidance
gemini -p "@leanvibe-backend/app/services/ Focus on testing strategy for these service classes, identifying complex business logic that needs unit test coverage"

# For API endpoint testing patterns
gemini -p "@leanvibe-backend/app/api/ Analyze these FastAPI endpoints and recommend comprehensive test scenarios using TestClient and async testing patterns"


## Expected Deliverables:
- Prioritized list of 11 failing test fixes
- High-impact test suite recommendations for BETA agent's new APIs  
- Specific test scenarios for WebSocket integration
- Mock strategies for external dependencies (APNS, NLP)
- Performance regression prevention tests
- Clear implementation roadmap with effort estimates 