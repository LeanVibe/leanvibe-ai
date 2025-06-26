# LeenVibe L3 Coding Agent - MVP Specification

## Product Overview

### Vision Statement
LeenVibe empowers passionate senior engineers to finalize their dream side projects with a semi-autonomous L3 coding agent running on their own hardware that they can easily control from their iOS device.

### Target Users
Senior engineers with Apple Silicon Macs (M3 Max or better with 48GB+ RAM) and iOS devices (iPhone 14 Pro or better).

### Key Differentiators
- Runs entirely on local hardware - no cloud dependencies
- Deep integration with development workflows (vim+tmux)
- Seamless iOS mobile monitoring and control
- Architecture visualization and dependency mapping
- Human-in-the-loop confidence and quality gates

## System Architecture

![LeenVibe System Architecture](https://ppl-ai-code-interpreter-files.s3.amazonaws.com/web/direct-files/34e96e5b4a516e3866bc76aeb182aa96/fb25af2e-2951-472d-b16e-f06c819409b7/6f7b4e9e.png)

### Mac Backend Components

#### MLX-LM Engine (Qwen2.5-Coder-32B)
- Apple Silicon-optimized large language model for code generation and understanding
- Requirements:
  - Hardware: Apple M3 Max with 48GB+ unified memory
  - Disk Space: ~20GB for model weights and quantization
  - Dependencies: MLX framework, MLX-LM package

#### Tree-sitter AST Parser
- Fast, incremental parsing system for code analysis and dependency extraction
- Supported Languages: Python, JavaScript, TypeScript, Go, Rust, C++, Java, Swift

#### Neo4j Graph Database
- Graph database for storing code relationships and architecture information
- Key Features:
  - Code entity relationships storage
  - Fast traversal queries for dependency mapping
  - Visualization data preparation
  - Schema-free relationship modeling

#### Pydantic.ai L3 Agent Framework
- Type-safe, structured framework for building autonomous coding agents
- Key Features:
  - State management across sessions
  - Tool integration with type safety
  - Confidence scoring and human intervention triggers
  - Decision logging and explainability

#### FastAPI WebSocket Server
- Real-time communication server for iOS app integration
- Endpoints:
  - `/ws/{client_id}`: WebSocket connection for real-time communication
  - `/health`: Server health check endpoint
  - `/version`: API version information

### iOS Client Components

![LeenVibe iOS App Interface](https://pplx-res.cloudinary.com/image/upload/v1750501678/gpt4o_images/wpsg9z2g3zexmquwlqaw.png)

#### UI Components

1. **Kanban Board**
   - Visual project task management interface
   - Features:
     - Drag-and-drop task management
     - Task status visualization
     - Confidence indicator per task
     - One-tap task details view

2. **Architecture Viewer**
   - Code architecture visualization using Mermaid
   - Features:
     - Interactive dependency graph
     - Zoom and pan navigation
     - Tap-to-navigate to code entity
     - Historical comparison view

3. **Voice Interface**
   - Natural language voice control for the agent
   - Features:
     - Wake phrase detection
     - On-device speech-to-text
     - Command recognition
     - Voice feedback

4. **Metrics Dashboard**
   - Agent performance and status visualization
   - Features:
     - Confidence score trends
     - Decision logs timeline
     - Progress metrics
     - Resource utilization

#### Requirements
- iOS Version: iOS 17.0+
- Device: iPhone 14 Pro or newer (for neural engine)
- Network: Local WiFi connection to Mac

## Core Features and User Stories

### 1. Live Dependency Mapping

**Description**: Automatically analyze and visualize code architecture in real-time

**User Story**: As a senior engineer, I want real-time dependency updates during coding to avoid architectural drift.

**Acceptance Criteria**:
- System parses code files using Tree-sitter to extract syntax trees
- Dependencies are identified and stored in Neo4j graph database
- Architecture diagrams are generated in Mermaid.js format
- Changes to code update the architecture view within 2 seconds
- iOS app displays the architecture diagram with interactive elements

**Implementation Notes**: Use AST parsing to identify imports, function calls, and class relationships. Store nodes and edges in Neo4j for querying. Generate Mermaid.js diagrams from the graph data.

### 2. Change Impact Analysis

**Description**: Identify and alert on the impact of code changes to other components

**User Story**: As a senior engineer working on a side project, I want to understand the impact of my changes before committing them.

**Acceptance Criteria**:
- System detects modified files and analyzes their dependencies
- Impact analysis identifies affected components
- High-impact changes trigger alerts with confidence scores
- iOS app displays impact visualization with affected components
- Suggestions for risk mitigation are provided

**Implementation Notes**: Compare AST before and after changes. Traverse the dependency graph to identify affected nodes. Use the LLM to generate risk assessments and mitigation suggestions.

### 3. CLI and iOS Integration

**Description**: Seamless workflow between command-line and mobile interfaces

**User Story**: As a vim+tmux user, I want to interact with the agent through familiar CLI interfaces while monitoring progress on my phone.

**Acceptance Criteria**:
- CLI commands mirror Claude Code CLI patterns
- State changes in CLI are reflected in real-time on iOS app
- iOS app can trigger actions that execute in the CLI environment
- Voice commands from iOS can control CLI workflows
- Transitions between interfaces maintain full context

**Implementation Notes**: Implement WebSocket communication between CLI client and server. Use a shared state manager to synchronize state. Create a command router that handles commands from both interfaces.

## L3 Agent Architecture

![LeenVibe L3 Agent Architecture](https://ppl-ai-code-interpreter-files.s3.amazonaws.com/web/direct-files/34e96e5b4a516e3866bc76aeb182aa96/c9751ead-7375-4f79-8349-3aaf334d3758/49213ba4.png)

### Agent Components

1. **L3CodingAgent (main class)**
   - Core agent implementation with run, plan, and reflect methods
   - Manages state and dependencies
   - Coordinates tool execution

2. **AgentDependencies**
   - Dependency injection for workspace path, client ID, and session data
   - Enables flexible configuration and testing

3. **AgentState**
   - Maintains conversation history, project context, and confidence scores
   - Provides methods for state updates and retrieval

4. **Tools Interface**
   - Abstract interface for all agent tools
   - Implemented by concrete tool classes:
     - FileSystemTool: File operations
     - CodeAnalysisTool: Code parsing and dependency detection

5. **LLMService**
   - Interface to MLX-LM model
   - Handles text generation and embedding

6. **SessionManager**
   - Manages active agent sessions
   - Creates, retrieves, and deletes sessions

7. **GraphStore**
   - Wrapper for Neo4j graph database
   - Manages nodes, edges, and queries

## Data Flow

![LeenVibe Code Dependency Mapping Process](https://ppl-ai-code-interpreter-files.s3.amazonaws.com/web/direct-files/34e96e5b4a516e3866bc76aeb182aa96/96494a42-fd77-479f-80c9-36646f303c9e/177edd57.png)

### Main Flows

#### Code Analysis Flow
1. Code changes detected in editor
2. Tree-sitter parses files to generate AST
3. AST analyzed for dependencies and structure
4. Relationships stored in Neo4j graph
5. Architecture data sent to iOS via WebSockets
6. iOS renders updated architecture visualization

#### Command Execution Flow
1. Command received from CLI or iOS
2. Command routed to appropriate agent tool
3. Agent determines execution plan
4. If confidence below threshold, request human input
5. Execute command and capture results
6. Update state and send results to interfaces

## User Journeys

### Onboarding Journey

1. **Install Mac Agent**
   - Command: `brew install leenvibe`
   - Success: Installation completes without errors

2. **Configure Project**
   - Command: `leenvibe init /path/to/project`
   - Success: Project is scanned and initial architecture map is generated

3. **Install iOS App**
   - Success: App is installed and opens without errors

4. **Pair Devices**
   - Success: Devices are paired and connection is established

### Daily Workflow Journey

1. **Review Project Status**
   - Success: Kanban board shows current tasks and their status

2. **Start Coding Session**
   - Command: `leenvibe start`
   - Success: Agent is active and monitoring code changes

3. **Code with Agent Assistance**
   - Command: `leenvibe generate function to parse JSON data`
   - Success: Agent generates code that meets requirements

4. **Monitor Architecture**
   - Success: Architecture diagram updates to reflect changes

5. **Voice Control**
   - Command: "Hey LeenVibe, analyze the performance of the parse function"
   - Success: Agent performs analysis and reports results

## Implementation Roadmap

### Phase 1: Foundation (2 weeks)
- Set up basic Mac agent with MLX-LM integration
- Implement core CLI interface
- Create basic iOS app with WebSocket connection
- Establish basic agent-iOS communication

### Phase 2: Code Analysis Engine (3 weeks)
- Implement Tree-sitter integration for code parsing
- Set up Neo4j for relationship storage
- Create basic architecture visualization
- Implement real-time code monitoring

### Phase 3: L3 Agent Capabilities (4 weeks)
- Implement pydantic.ai agent framework
- Create tool implementations for key functions
- Develop state management system
- Implement confidence scoring and human gates

### Phase 4: iOS Experience (3 weeks)
- Develop Kanban board UI
- Implement architecture visualization viewer
- Create voice command interface
- Build metrics dashboard

### Phase 5: Integration and Testing (2 weeks)
- End-to-end testing of all workflows
- Performance optimization
- User experience refinement
- Documentation and onboarding flow

## Technical Requirements

### Mac Backend
- Hardware: Apple Silicon Mac (M3 Max or better) with 48GB+ RAM
- OS: macOS 14.0+
- Dependencies:
  - Python 3.11+
  - MLX Framework
  - MLX-LM
  - Neo4j
  - Tree-sitter
  - FastAPI
  - Pydantic.ai

### iOS Client
- Hardware: iPhone 14 Pro or newer
- OS: iOS 17.0+
- Dependencies:
  - SwiftUI
  - Combine
  - Speech framework
  - Mermaid.js renderer
  - WebSocket client

### Development Tools
- Xcode 15+
- SwiftUI Preview
- Python development environment
- Neo4j Desktop
- Docker for development dependencies

## Security Considerations

### Data Privacy
- All data remains on user's devices - no cloud transmission
- End-to-end encryption for WebSocket communication
- No telemetry or usage data collection
- Secure pairing mechanism between Mac and iOS

### Code Security
- Sandboxed execution environment for generated code
- Static analysis of generated code before execution
- Permission controls for file system access
- Encryption of locally stored model weights

### Authentication
- Device-based authentication for iOS-Mac pairing
- Session token validation for all communications
- Automatic session expiration after inactivity
- Biometric authentication option for sensitive operations

## Testing Strategy

### Unit Testing
- Frameworks: pytest, XCTest
- Coverage Targets: 90% code coverage
- Focus Areas:
  - Agent tool implementations
  - AST parsing accuracy
  - State management
  - iOS UI components

### Integration Testing
- Frameworks: pytest-asyncio, XCTest
- Focus Areas:
  - WebSocket communication
  - End-to-end workflows
  - Neo4j data consistency
  - Cross-device state synchronization

### Performance Testing
- Metrics:
  - Architecture diagram generation < 2s
  - LLM response time < 1s
  - iOS UI responsiveness < 100ms
  - Memory usage < 75% of available
- Benchmarks:
  - Processing 100k+ lines of code codebase
  - Handling complex architecture with 1000+ components
  - Concurrent users from multiple iOS devices

## Deployment Strategy

### Mac Distribution
- Method: Homebrew package
- Updates: Automated updates via Homebrew
- Packaging: Self-contained package with dependencies

### iOS Distribution
- Method: App Store
- Updates: Standard App Store update process
- Requirements: iOS 17.0+ with neural engine

### Model Distribution
- Method: On-demand download during setup
- Storage: Local storage with versioning
- Updates: Optional model updates with backward compatibility