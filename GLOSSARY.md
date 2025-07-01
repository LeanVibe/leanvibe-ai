# LeanVibe AI - Comprehensive Glossary & Search Guide

## 🔍 Quick Search Guide

**Finding Information Fast:**
- **Ctrl+F / Cmd+F**: Search this glossary for terms and concepts
- **Technical Terms**: Look in [Technical Components](#-technical-components) section
- **Process & Workflow**: Check [Process & Methodology](#-process--methodology) section  
- **Current Status**: Reference [Status & Metrics](#-status--metrics) section
- **File Locations**: Use [Documentation Cross-References](#-documentation-cross-references) section

---

## 🎯 Core Concepts & Terms

### **Agent System**
Multi-agent development methodology with 5 specialist AI agents working in parallel using dedicated git worktrees.
- **Current Status**: 99.8% MVP complete with 4 active + 1 offboarded agents
- **Location**: [Agent System Guide](./docs/core/AGENT_SYSTEM_GUIDE.md)
- **Related**: Worktree Strategy, Agent Specialization, Integration Architecture

### **ALPHA Agent**
iOS Dashboard Foundation Specialist focused on iOS app architecture and infrastructure.
- **Status**: ✅ Active - Leading production readiness efforts
- **Deliverables**: iOS Dashboard (3,000+ lines), Xcode Project, Performance Optimization
- **Location**: [ALPHA Agent Tasks](./docs/organized/agents/ALPHA/)
- **Related**: iOS Development, Performance Optimization, Production Readiness

### **Apple MLX Framework**
On-device AI processing framework for Apple Silicon (M1/M2/M3) required for local AI inference.
- **Performance**: <250MB model size, <2s generation time
- **Integration**: Qwen2.5-Coder-32B model with complete on-device processing
- **Location**: [System Architecture](./docs/core/SYSTEM_ARCHITECTURE.md)
- **Related**: Local-First Architecture, AI Model Integration, Privacy Compliance

### **Backend Infrastructure**
Central Python FastAPI hub with AI models, code analysis, WebSocket/REST APIs.
- **Status**: 95% production ready with <2s response times
- **Architecture**: Service-oriented (AI, TreeSitter, VectorStore, Event services)
- **Location**: [Backend Documentation](./docs/organized/backend/)
- **Related**: FastAPI, WebSocket Protocol, Session Management

### **BETA Agent**
Backend API Enhancement Specialist focused on server-side infrastructure and performance.
- **Status**: ✅ Active - System audit completed
- **Deliverables**: API enhancements, Push Notifications (7,100+ lines), Production audit
- **Location**: [BETA Agent Tasks](./docs/organized/agents/BETA/)
- **Related**: Backend Infrastructure, API Development, Performance Optimization

### **CLI Tool Integration**
Python-based command-line interface with rich terminal UI and backend integration.
- **Status**: 85% production ready with enhanced user experience
- **Features**: Command structure, configuration management, project workspace support
- **Location**: [Development Workflow](./docs/core/DEVELOPMENT_WORKFLOW.md)
- **Related**: Developer Experience, Cross-Platform Integration, CLI Enhancement

### **Confidence-Driven Framework**
AI decision-making system with 4-tier confidence scoring for autonomous vs. human-guided actions.
- **Thresholds**: 90%+ autonomous, 80-89% logged, 70-79% checkpoints, 60-69% collaborative, <60% escalation
- **Implementation**: Pydantic AI agents with L3 coding capabilities
- **Location**: [L3 Agent Integration](./docs/organized/backend/L3_AGENT_INTEGRATION.md)
- **Related**: AI Model Integration, Decision Framework, Human-AI Collaboration

### **DELTA Agent**
CLI Enhancement & Developer Experience Expert focused on command-line interface and iOS-CLI bridge.
- **Status**: 🔄 Active - Working on unified developer experience
- **Deliverables**: CLI modernization, Task management APIs, iOS-CLI bridge
- **Location**: [DELTA Agent Tasks](./docs/organized/agents/DELTA/)
- **Related**: CLI Tool Integration, Developer Experience, Cross-Platform Features

### **FastAPI Backend**
Central server implementation using Python FastAPI framework for AI processing and communication.
- **Performance**: <2s response times, <100MB per session
- **Features**: WebSocket + REST APIs, session management, real-time communication
- **Location**: [Backend Documentation](./docs/organized/backend/)
- **Related**: Backend Infrastructure, API Architecture, Performance Optimization

### **GAMMA Agent**
Architecture Visualization Expert focused on visual development tools and user experience.
- **Status**: ✅ Completed - All tasks integrated to main branch
- **Deliverables**: Architecture Viewer (WebKit + Mermaid.js), User Onboarding, Metrics Dashboard
- **Location**: [GAMMA Agent Tasks](./docs/organized/agents/GAMMA/)
- **Related**: Architecture Visualization, User Experience, WebKit Integration

### **Git Worktree Strategy**
Parallel development approach using 7 specialized worktrees for conflict-free agent development.
- **Structure**: Dedicated branches for each agent with isolated development streams
- **Benefits**: Conflict-free development, parallel progress, clean integration
- **Location**: [Worktree Development Guide](./docs/WORKTREE_DEVELOPMENT_GUIDE.md)
- **Related**: Agent Management, Parallel Development, Integration Strategy

### **iOS Application**
SwiftUI-based mobile app with 4-tab architecture, voice interface, and real-time monitoring.
- **Status**: Core features 90% ready, stability 60% (critical fixes needed)
- **Performance**: <200MB memory, <500ms voice response, 60fps animations
- **Location**: [iOS Documentation](./docs/organized/ios/)
- **Related**: SwiftUI Development, Voice Interface, Performance Optimization

### **KAPPA Agent**
Voice Interface & Integration Testing Specialist (completed and offboarded).
- **Status**: ✅ OFFBOARDED - All tasks completed successfully
- **Deliverables**: Kanban Board (2,662+ lines), Voice Interface, Settings System (3,870+ lines)
- **Location**: [KAPPA Agent Tasks](./docs/organized/agents/KAPPA/)
- **Related**: Voice Interface System, Integration Testing, Task Management

### **Local-First Architecture**
Complete privacy-focused design with all processing happening on-device using Apple MLX.
- **Features**: Zero data collection, no cloud dependencies, COPPA compliance
- **Benefits**: Complete privacy, offline functionality, regulatory compliance
- **Location**: [System Architecture](./docs/core/SYSTEM_ARCHITECTURE.md)
- **Related**: Privacy Compliance, Apple MLX Framework, On-Device Processing

### **MVP (Minimum Viable Product)**
Current LeanVibe AI implementation status with 99.8% feature completion.
- **Status**: Sophisticated local AI coding assistant with voice interface
- **Completion**: 99.8% of planned features implemented
- **Location**: [Production Status](./docs/core/PRODUCTION_STATUS.md)
- **Related**: Production Readiness, Feature Implementation, System Integration

### **Production Readiness**
Current status assessment showing 79% readiness with 3-4 week timeline to production.
- **Metrics**: Backend 95%, iOS core 90%, iOS stability 60%, CLI 85%
- **Blockers**: iOS build system, push notification implementation
- **Location**: [Production Status](./docs/core/PRODUCTION_STATUS.md)
- **Related**: Critical Blockers, Performance Metrics, Timeline Planning

### **Push Notification System**
Comprehensive iOS notification implementation with 2,847+ lines of production-grade code.
- **Status**: Backend 100% ready, iOS 40% implemented (critical gap)
- **Features**: Privacy-compliant, analytics, intelligent content delivery
- **Location**: [Push Notification Documentation](./docs/organized/ios/PUSH_NOTIFICATION_SYSTEM_DOCUMENTATION.md)
- **Related**: iOS Development, Backend Integration, Privacy Compliance

### **Qwen2.5-Coder-32B**
Local AI model optimized for Apple MLX with <250MB size and <2s generation time.
- **Integration**: Pydantic AI framework with confidence-driven decision making
- **Capabilities**: Code analysis, generation, review, refactoring
- **Location**: [System Architecture](./docs/core/SYSTEM_ARCHITECTURE.md)
- **Related**: Apple MLX Framework, AI Model Integration, Local Processing

### **SwiftUI iOS App**
Native iOS application built with SwiftUI featuring glass effects and sophisticated animations.
- **Architecture**: 4-tab structure (Projects, Agent, Monitor, Settings)
- **Performance**: All targets exceeded with 60fps animations and <5% battery usage
- **Location**: [iOS Documentation](./docs/organized/ios/)
- **Related**: iOS Development, Performance Optimization, User Interface

### **Voice Interface System**
"Hey LeanVibe" wake phrase detection with natural language processing and <500ms response.
- **Technology**: Apple Speech Recognition framework with on-device processing
- **Performance**: <500ms response time, robust speech recognition
- **Location**: [Voice Interface Documentation](./docs/organized/ios/)
- **Related**: Speech Recognition, Natural Language Processing, User Experience

### **WebSocket Protocol**
Real-time communication system with enhanced reconnection and session state preservation.
- **Performance**: <1ms reconnection detection, 24-hour state retention
- **Features**: Missed event replay, heartbeat monitoring, client optimization
- **Location**: [WebSocket Implementation](./docs/organized/backend/SPRINT_1_5_SUMMARY.md)
- **Related**: Real-Time Communication, Session Management, Integration Architecture

---

## 🏗️ Technical Components

### **API Architecture**
RESTful API design with comprehensive endpoint structure for AI, projects, and sessions.
- **Structure**: `/api/v1/` with ai, projects, sessions, websocket endpoints
- **Performance**: <2s response times with comprehensive error handling
- **Location**: [System Architecture](./docs/core/SYSTEM_ARCHITECTURE.md)
- **Related**: Backend Infrastructure, Integration Architecture, Performance

### **Architecture Visualization**
Interactive system visualization using WebKit + Mermaid.js integration.
- **Status**: Functional but needs optimization (3-5s load time → <1s target)
- **Features**: Real-time diagrams, dependency mapping, system analysis
- **Location**: [Architecture Viewer Documentation](./docs/organized/agents/GAMMA/)
- **Related**: System Visualization, WebKit Integration, Performance Optimization

### **Build System**
Xcode project configuration with SwiftLint integration and automated quality gates.
- **Status**: ❌ Critical blocker requiring immediate attention
- **Requirements**: 100% build success rate, comprehensive test coverage
- **Location**: [Development Workflow](./docs/core/DEVELOPMENT_WORKFLOW.md)
- **Related**: iOS Development, Quality Assurance, Production Deployment

### **Code Analysis Pipeline**
Multi-stage code analysis using TreeSitter parsing, semantic analysis, and pattern recognition.
- **Components**: Syntax trees, type checking, dependency mapping, code smell detection
- **Integration**: Xcode, Git, SwiftLint, testing frameworks
- **Location**: [System Architecture](./docs/core/SYSTEM_ARCHITECTURE.md)
- **Related**: AI Processing, Code Quality, Development Tools

### **Integration Architecture**
Cross-platform communication and state management system.
- **Status**: 85% operational with real-time project updates
- **Components**: WebSocket + REST APIs, state synchronization, conflict resolution
- **Location**: [System Integration Analysis](./docs/organized/production/SYSTEM_INTEGRATION_ANALYSIS.md)
- **Related**: Cross-Platform Features, Real-Time Communication, State Management

### **Kanban Board System**
4-column task management interface with drag-and-drop functionality and real-time updates.
- **Implementation**: 2,662+ lines of production-ready code
- **Features**: Multi-project support, real-time synchronization, WebSocket integration
- **Location**: [Kanban Implementation](./docs/organized/agents/KAPPA/)
- **Related**: Task Management, Real-Time Updates, User Interface

### **L3 Coding Agent**
Advanced autonomous coding agent with pydantic.ai integration and confidence scoring.
- **Capabilities**: Multi-session support (up to 10 concurrent), automatic cleanup, state persistence
- **Performance**: <2s response times, <100MB per session
- **Location**: [L3 Agent Integration](./docs/organized/backend/L3_AGENT_INTEGRATION.md)
- **Related**: AI Processing, Session Management, Autonomous Development

### **Memory Management**
System memory optimization with monitoring, limits, and leak prevention.
- **iOS Targets**: <200MB total usage (achieved), leak prevention in WebSocket connections
- **Backend Targets**: <100MB per session, automatic session cleanup
- **Location**: [Performance Optimization](./docs/organized/ios/PERFORMANCE_OPTIMIZATION_SUMMARY.md)
- **Related**: Performance Optimization, System Reliability, Resource Management

### **Performance Monitoring**
Real-time metrics collection with automated benchmarking and optimization alerts.
- **Metrics**: Response times, memory usage, frame rates, battery consumption
- **Automation**: Continuous monitoring, regression detection, performance budgets
- **Location**: [Performance Documentation](./docs/organized/ios/)
- **Related**: System Monitoring, Quality Assurance, Performance Optimization

### **Session Management**
Multi-session AI processing with state persistence and automatic cleanup.
- **Capabilities**: Up to 10 concurrent sessions, 24-hour inactivity cleanup, JSON persistence
- **Performance**: 5-minute auto-save intervals, complete state restoration
- **Location**: [Session Management](./docs/organized/backend/)
- **Related**: AI Processing, State Management, Backend Infrastructure

### **Testing Framework**
Comprehensive testing infrastructure with 95%+ coverage across all components.
- **iOS Testing**: Unit, integration, UI, performance, accessibility tests
- **Backend Testing**: API, integration, load, security tests
- **Location**: [Testing Documentation](./docs/organized/)
- **Related**: Quality Assurance, Test Coverage, Validation Framework

### **WebKit Integration**
Advanced web view integration for architecture visualization and interactive diagrams.
- **Implementation**: WebKit + Mermaid.js for dynamic system visualization
- **Performance Issue**: Current 3-5s load time needs optimization to <1s
- **Location**: [Architecture Viewer](./docs/organized/agents/GAMMA/)
- **Related**: System Visualization, Performance Optimization, User Interface

---

## 🔄 Process & Methodology

### **Agent Coordination Protocol**
Systematic approach to managing multiple AI agents with clear responsibilities and integration points.
- **Process**: STATUS.md updates, cross-agent dependencies, quality gates, knowledge transfer
- **Benefits**: Conflict-free development, coordinated delivery, comprehensive documentation
- **Location**: [Agent Management Methodology](./docs/AI_AGENT_MANAGEMENT_METHODOLOGY.md)
- **Related**: Multi-Agent Development, Project Coordination, Quality Management

### **Agent Management Methodology**
Comprehensive framework for managing AI agents in complex software development projects.
- **Components**: Onboarding, task assignment, progress tracking, integration planning
- **Success Metrics**: 99.8% MVP completion, 10,000+ lines of code, 95%+ test coverage
- **Location**: [Agent Management](./docs/AI_AGENT_MANAGEMENT_METHODOLOGY.md)
- **Related**: Agent Coordination, Development Process, Quality Standards

### **Build Validation Process**
Quality assurance framework ensuring code quality before commits and integration.
- **Gates**: SwiftLint checks, test coverage verification, performance validation
- **Automation**: Pre-commit hooks, integration health checks, regression testing
- **Location**: [Development Workflow](./docs/core/DEVELOPMENT_WORKFLOW.md)
- **Related**: Quality Assurance, Code Quality, Continuous Integration

### **Commit Strategy**
Conventional commit format with automatic quality validation and integration testing.
- **Format**: `type(scope): description` with ticket references and breaking change indicators
- **Validation**: All tests pass, build success, code quality checks
- **Location**: [Development Workflow](./docs/core/DEVELOPMENT_WORKFLOW.md)
- **Related**: Version Control, Quality Gates, Development Standards

### **Integration Strategy**
Systematic approach to merging parallel agent development streams with quality validation.
- **Process**: Pre-integration validation, compatibility testing, performance assessment
- **Schedule**: Weekly integration cycles with comprehensive validation
- **Location**: [Integration Lessons Learned](./docs/integration_lessons_learned.md)
- **Related**: Quality Assurance, Agent Coordination, System Integration

### **Production Deployment Process**
Step-by-step procedures for deploying LeanVibe AI to production environment.
- **Phases**: Critical blocker resolution, user experience enhancement, production polish
- **Timeline**: 3-week execution plan with defined success criteria
- **Location**: [Production Deployment Guide](./docs/organized/production/)
- **Related**: Production Readiness, Deployment Strategy, Quality Validation

### **Quality Gates**
Multi-level validation framework ensuring high-quality code and system integration.
- **Levels**: Code quality, integration testing, performance validation, production readiness
- **Enforcement**: "No Build = No Commit" principle, interface contracts, incremental integration
- **Location**: [Integration Lessons Learned](./docs/integration_lessons_learned.md)
- **Related**: Quality Assurance, Build Validation, Integration Strategy

### **Sprint Planning**
Agile development approach adapted for multi-agent parallel development.
- **Structure**: 3-week production readiness sprints with defined deliverables
- **Coordination**: Agent-specific tasks with cross-dependencies and integration points
- **Location**: [Production Status](./docs/core/PRODUCTION_STATUS.md)
- **Related**: Project Management, Agent Coordination, Timeline Planning

### **Task Lifecycle Management**
Comprehensive tracking of tasks from assignment through completion and integration.
- **States**: Assigned, In Progress, Review, Integrated, Archived
- **Tracking**: Daily updates, weekly integration, quality validation, documentation
- **Location**: [Agent System Guide](./docs/core/AGENT_SYSTEM_GUIDE.md)
- **Related**: Project Management, Agent Coordination, Progress Tracking

### **Testing Strategy**
Multi-level testing approach with automated validation and comprehensive coverage.
- **Levels**: Unit testing (80%+ coverage), integration testing, end-to-end validation
- **Automation**: Continuous testing, performance benchmarking, regression detection
- **Location**: [Testing Documentation](./docs/organized/)
- **Related**: Quality Assurance, Test Coverage, Validation Framework

---

## 📊 Status & Metrics

### **Component Readiness Scores**
Current production readiness assessment across all system components.
- **Backend Infrastructure**: 95% ready (excellent)
- **iOS Core Features**: 90% ready (very good)
- **iOS Stability**: 60% ready (critical fixes needed)
- **CLI Integration**: 85% ready (good)
- **Overall**: 79% ready (target: 95%+)
- **Location**: [Production Status](./docs/core/PRODUCTION_STATUS.md)

### **Critical Blockers**
High-impact issues preventing production deployment.
- **Count**: 2 critical blockers identified
- **Issues**: iOS build system configuration, push notification iOS implementation gap
- **Timeline**: Sprint 1 (Week 1) resolution required
- **Location**: [Production Status](./docs/core/PRODUCTION_STATUS.md)

### **Integration Health**
Status of cross-component communication and system integration.
- **iOS ↔ Backend**: 95% operational (excellent)
- **Backend ↔ CLI**: 75% operational (good, needs optimization)
- **Cross-Platform State**: 70% synchronized (needs conflict resolution)
- **AI Model Processing**: 85% reliable (very good)
- **Location**: [System Integration Analysis](./docs/organized/production/)

### **Performance Benchmarks**
Achieved performance metrics compared to targets.
- **iOS Memory**: <200MB (target <500MB) - **60% better**
- **Voice Response**: <500ms (target <2s) - **75% better**
- **Backend Response**: <2s (target <2s) - **Meets target**
- **WebSocket Reconnection**: <1ms (target <5s) - **99.98% better**
- **Location**: [Performance Documentation](./docs/organized/ios/)

### **Production Timeline**
Sprint-based roadmap for achieving production readiness.
- **Sprint 1 (Week 1)**: Critical blocker resolution
- **Sprint 2 (Week 2)**: User experience enhancement  
- **Sprint 3 (Week 3)**: Production polish and validation
- **Target**: 95%+ production readiness
- **Location**: [Production Status](./docs/core/PRODUCTION_STATUS.md)

### **Test Coverage Metrics**
Comprehensive testing coverage across all system components.
- **iOS Application**: 95%+ unit tests, 85% integration, 80% UI tests
- **Backend System**: 90%+ API tests, 85% integration, 75% load tests
- **End-to-End**: 70% user journeys (needs enhancement)
- **Overall Target**: 95%+ comprehensive coverage
- **Location**: [Testing Documentation](./docs/organized/)

---

## 📁 Documentation Cross-References

### **Core Documentation**
- **[DOCUMENTATION_INDEX.md](./DOCUMENTATION_INDEX.md)** - Master index with comprehensive navigation
- **[docs/core/SYSTEM_ARCHITECTURE.md](./docs/core/SYSTEM_ARCHITECTURE.md)** - Complete technical architecture
- **[docs/core/AGENT_SYSTEM_GUIDE.md](./docs/core/AGENT_SYSTEM_GUIDE.md)** - Multi-agent coordination methodology
- **[docs/core/PRODUCTION_STATUS.md](./docs/core/PRODUCTION_STATUS.md)** - Current production readiness assessment
- **[docs/core/DEVELOPMENT_WORKFLOW.md](./docs/core/DEVELOPMENT_WORKFLOW.md)** - Development standards and practices

### **Organized Documentation**
- **[docs/organized/ios/](./docs/organized/ios/)** - iOS development, testing, and deployment
- **[docs/organized/backend/](./docs/organized/backend/)** - Backend architecture and API specifications
- **[docs/organized/agents/](./docs/organized/agents/)** - Agent task specifications and coordination
- **[docs/organized/production/](./docs/organized/production/)** - Production readiness and deployment

### **Agent-Specific Documentation**
- **[docs/organized/agents/ALPHA/](./docs/organized/agents/ALPHA/)** - iOS Dashboard Foundation tasks
- **[docs/organized/agents/BETA/](./docs/organized/agents/BETA/)** - Backend API Enhancement tasks
- **[docs/organized/agents/DELTA/](./docs/organized/agents/DELTA/)** - CLI Enhancement tasks
- **[docs/organized/agents/GAMMA/](./docs/organized/agents/GAMMA/)** - Architecture Visualization tasks (completed)
- **[docs/organized/agents/KAPPA/](./docs/organized/agents/KAPPA/)** - Voice Interface tasks (completed)

### **Implementation-Specific Files**
- **[leanvibe-ios/docs/PLAN.md](./leanvibe-ios/docs/PLAN.md)** - iOS development roadmap and critical fixes
- **[leanvibe-backend/SPRINT_1_5_SUMMARY.md](./leanvibe-backend/SPRINT_1_5_SUMMARY.md)** - WebSocket reconnection system
- **[leanvibe-backend/L3_AGENT_INTEGRATION.md](./leanvibe-backend/L3_AGENT_INTEGRATION.md)** - L3 coding agent implementation

### **Historical Documentation**
- **[docs/archive/organized/](./docs/archive/organized/)** - Organized historical documentation
- **[docs/archive/organized/historical/](./docs/archive/organized/historical/)** - Market research and original vision
- **[docs/archive/organized/superseded/](./docs/archive/organized/superseded/)** - Outdated specifications
- **[docs/archive/organized/implementation-history/](./docs/archive/organized/implementation-history/)** - Sprint logs and evolution

---

## 🔍 Search Tips & Usage Patterns

### **Quick Reference Searches**
```
Ctrl+F / Cmd+F + Search Term:
- "Agent" → Find all agent-related information
- "iOS" → iOS development and implementation details  
- "Backend" → Server-side architecture and APIs
- "Production" → Production readiness and deployment
- "Performance" → Performance metrics and optimization
- "Testing" → Test coverage and validation frameworks
```

### **Status Information Searches**
```
Search for current status:
- "Status:" → Component readiness and progress
- "Location:" → Find relevant documentation files
- "Related:" → Discover connected concepts and files
- "Critical" → Identify blockers and high-priority issues
```

### **Technical Implementation Searches**
```
Find technical details:
- "Architecture" → System design and technical structure
- "Integration" → Cross-component communication
- "WebSocket" → Real-time communication details
- "SwiftUI" → iOS interface implementation
- "FastAPI" → Backend server implementation
```

**Last Updated**: 2025-07-01  
**Maintained By**: LeanVibe AI Documentation System  
**Purpose**: Comprehensive search and reference guide for all LeanVibe AI documentation