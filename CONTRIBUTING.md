# Contributing to LeanVibe

Welcome to LeanVibe's autonomous Extreme Programming (XP) workflow! This guide will help you contribute effectively to our contract-first, test-driven development process that achieves **85%+ autonomous deployments**.

## 🚀 Quick Start

```bash
# 1. Set up development environment
source scripts/dev_shortcuts.sh
setup

# 2. Create feature branch
git checkout -b feature/your-awesome-feature

# 3. Use contract-first development
gen  # Generate contracts from schemas

# 4. Follow TDD cycle
vf   # Verify fast (Tier 0 tests, <60s)

# 5. Push with auto-merge
pp   # Push with PR verification
gh pr create --title "feat: your awesome feature" --label "auto-merge"
```

## 🏗️ Development Philosophy

### Contract-First Development
Everything starts with API contracts (OpenAPI/AsyncAPI schemas):
1. **Define contracts first** - Update `contracts/openapi.yaml` or `contracts/asyncapi.yaml`
2. **Generate code** - Run `gen` to auto-generate models and types
3. **Write tests** - Contract tests validate all API responses
4. **Implement** - Code that satisfies the contracts

### Test-Driven Development (TDD)
Strict TDD cycle with fast feedback:
```
Red → Green → Refactor → Commit
 ↓      ↓        ↓         ↓
Test   Code   Clean    Quality Gate
```

### Autonomous Quality Gates
Our 4-tier testing system ensures autonomous deployments:
- **Tier 0** (<60s): Unit tests, contracts, types, lint
- **Tier 1** (3-5m): Integration, WebSocket, smoke tests, coverage
- **Tier 2** (30m): E2E, performance regression, mutation testing
- **Tier 3** (2h): Load testing, security scanning, dependency audit

## 📋 Contribution Workflow

### 1. Environment Setup

#### First-Time Setup
```bash
# Clone and enter repository
git clone https://github.com/your-org/leanvibe-ai.git
cd leanvibe-ai

# Set up development environment
source scripts/dev_shortcuts.sh
setup

# Verify environment health
health
```

#### Development Dependencies
The setup process installs:
- Python 3.11+ with pip/uv
- Testing tools: pytest, coverage, mutation testing
- Code quality: black, isort, flake8, mypy
- Git hooks for autonomous quality enforcement

### 2. Branch Strategy

#### Trunk-Based Development
- **Main branch**: Production-ready code, always deployable
- **Feature branches**: Short-lived (<24h), small changes (<300 LOC)
- **No long-lived branches**: Merge or delete within 1 day

#### Branch Naming Convention
```bash
feature/DS-123-add-websocket-auth    # New feature
fix/DS-456-memory-leak-in-ai         # Bug fix
refactor/DS-789-simplify-cache       # Code cleanup
docs/DS-101-update-api-guide         # Documentation
```

### 3. Contract-First Development Process

#### Step 1: Define API Contract
```yaml
# contracts/openapi.yaml
paths:
  /api/v1/tasks:
    post:
      summary: Create new task
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateTaskRequest'
      responses:
        201:
          description: Task created successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Task'
```

#### Step 2: Generate Code
```bash
gen  # Generates Python models, Swift types, TypeScript interfaces
```

#### Step 3: Write Contract Tests
```python
# tests/test_contracts.py
def test_create_task_contract():
    """Validate create task endpoint follows OpenAPI spec."""
    response = client.post("/api/v1/tasks", json={
        "title": "Test task",
        "description": "Contract validation test"
    })
    
    # Contract validation
    assert response.status_code == 201
    validate_schema(response.json(), "Task")
```

### 4. Testing Requirements

#### Quality Gates (Enforced Automatically)
- **Test Coverage**: ≥75% (gate), target 85%
- **Mutation Score**: ≥70% (weekly validation)
- **Performance**: <10% regression tolerance
- **Security**: Zero critical vulnerabilities
- **Type Safety**: 100% mypy compliance

#### Tier 0: Pre-Commit Tests (<60s)
Run before every commit:
```bash
vf  # Fast verification shortcut
# Or manually:
make test-tier0
```

Tests:
- Unit tests for all new/modified functions
- Contract validation for API changes
- Type checking with mypy
- Code formatting and linting

#### Tier 1: PR Gate Tests (3-5m)
Automatically runs on PR creation:
```bash
vp  # PR verification shortcut
# Or manually:
make test-tier1
```

Tests:
- Integration tests between components
- WebSocket connection and event tests
- API smoke tests with authentication
- Coverage analysis and quality ratchet enforcement

### 5. Code Quality Standards

#### Formatting and Linting
Use auto-fix for consistent code style:
```bash
fix  # Auto-fix formatting and imports
```

Manual standards:
- **Black**: Line length 88 characters
- **isort**: Single-line imports, sorted alphabetically
- **flake8**: PEP8 compliance with project-specific rules
- **mypy**: Strict type checking enabled

#### Code Review Automation
PRs are automatically reviewed for:
- Contract compliance validation
- Test coverage requirements
- Performance impact analysis
- Security vulnerability scanning
- Documentation completeness

### 6. Auto-Merge Process

#### Requirements for Auto-Merge
Add the `auto-merge` label to enable autonomous deployment:

```bash
gh pr create --title "feat: add awesome feature" --label "auto-merge"
```

**Auto-merge criteria** (all must pass):
- ✅ All Tier 0 + Tier 1 tests pass
- ✅ Code coverage ≥ 75%
- ✅ Quality ratchet requirements met
- ✅ No "do-not-merge" or "wip" labels
- ✅ Branch protection rules satisfied
- ✅ Successful canary deployment
- ✅ Synthetic health probes pass (≥85% success rate)

#### Manual Review Requirements
Some changes **always require human review**:
- Security-related changes (authentication, authorization)
- Database schema modifications
- Breaking API changes
- Infrastructure configuration changes
- Third-party integrations

Add `needs-review` label to disable auto-merge.

### 7. Feature Development Patterns

#### Micro-Changes Approach
Keep changes small for fast feedback:
- **<300 lines of code** per PR
- **Single concern** per feature branch
- **Always deployable** incremental changes
- **Feature flags** for work-in-progress features

#### Contract Evolution
When modifying existing APIs:
1. **Add new fields** as optional first
2. **Deprecate old fields** with migration plan
3. **Version endpoints** for breaking changes
4. **Update all clients** before removing fields

#### Error Handling Standards
Consistent error handling across the codebase:
```python
# Use structured error responses
from app.core.exceptions import ValidationError, NotFoundError

@app.post("/api/v1/tasks")
async def create_task(task: CreateTaskRequest) -> Task:
    try:
        return await task_service.create_task(task)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
```

### 8. Performance and Monitoring

#### Performance Budgets
All changes must meet performance budgets:
- **API Response Time**: P95 < 500ms
- **Memory Usage**: < 500MB total
- **Test Execution**: Tier 0 < 60s, Tier 1 < 5m
- **Build Time**: < 2 minutes

#### Observability Requirements
New features must include:
- **Health checks** for monitoring
- **Metrics** for performance tracking
- **Logging** for debugging
- **Error tracking** with structured data

Example:
```python
from app.core.monitoring import track_performance, log_structured

@track_performance("api.tasks.create")
async def create_task(task: CreateTaskRequest) -> Task:
    log_structured("task.creation.started", {"task_type": task.type})
    
    result = await task_service.create_task(task)
    
    log_structured("task.creation.completed", {
        "task_id": result.id,
        "duration_ms": context.duration
    })
    
    return result
```

## 🛠️ Development Tools and Shortcuts

### Essential Developer Shortcuts
Source the shortcuts file in your shell:
```bash
source scripts/dev_shortcuts.sh
```

**Quality shortcuts:**
- `vf` - Verify fast (Tier 0 tests, <60s)
- `vp` - Verify PR (Tier 1 tests, 3-5m)
- `fix` - Auto-fix formatting and linting
- `gen` - Generate contracts from schemas

**Testing shortcuts:**
- `t0`, `t1`, `t2` - Run specific test tiers
- `tw` - Watch mode for continuous testing
- `qd` - Quality dashboard with metrics

**Workflow shortcuts:**
- `qc 'message'` - Quick commit with quality checks
- `pp` - Push with PR verification
- `health` - Development environment health check

### IDE Integration

#### VS Code Configuration
Add to `.vscode/settings.json`:
```json
{
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "python.sortImports.args": ["--force-single-line-imports"],
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["-v", "--tb=short"],
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

#### Git Hooks
Pre-commit hooks automatically enforce quality:
```bash
# Install hooks (done by setup)
make install-hooks

# Manual installation
git config core.hooksPath .githooks
chmod +x .githooks/*
```

## 📊 Quality Monitoring

### Quality Ratchets
The quality ratchet system prevents regression:
```json
{
  "coverage_percent_min": 75.0,    // Must not decrease
  "mutation_score_min": 70.0,      // Weekly validation
  "performance_p95_max": 500.0,    // Response time budget
  "flaky_test_count_max": 2,       // Reliability target
  "security_issues_max": 0         // Zero tolerance
}
```

View current quality metrics:
```bash
qr   # Quality ratchet report
qd   # Interactive quality dashboard
```

### Continuous Improvement
Weekly quality review includes:
- **Test suite health** - Flaky test detection and removal
- **Performance trends** - Regression analysis and optimization
- **Security posture** - Dependency updates and vulnerability scans
- **Code quality metrics** - Technical debt assessment

## 🚨 Troubleshooting

### Common Issues

#### Tests Failing Locally
```bash
# Clean and retry
make clean
vf

# Check environment health
health

# View detailed test output
pytest tests/ -v --tb=long

# Run specific test category
t0  # Tier 0 only
t1  # Tier 1 only
```

#### Quality Ratchet Failures
```bash
# View quality report
qr

# Check coverage details
make coverage

# Fix common quality issues
fix

# View mutation testing results
make test-tier2
```

#### Auto-Merge Not Working
```bash
# Check PR status
gh pr checks

# Verify labels
gh pr view --json labels

# Check branch protection rules
gh api repos/:owner/:repo/branches/main/protection
```

#### Contract Generation Issues
```bash
# Regenerate contracts
gen

# Validate schema syntax
python -c "import yaml; yaml.safe_load(open('contracts/openapi.yaml'))"

# Check generated files
git diff contracts/
```

### Performance Optimization

#### Test Suite Performance
```bash
# Profile test execution
prof

# Run tests in parallel
make test-tier0-parallel

# Memory usage analysis
mem
```

#### Development Workflow Optimization
```bash
# Enable continuous testing
tw

# Use quality dashboard for insights
qd

# Monitor git hooks performance
time vf
```

## 🎯 Success Metrics

### Autonomous Operation Targets
- **85%+ fully autonomous deployments** without human intervention
- **<2 minutes** from commit to canary deployment
- **<5 minutes** to detect and rollback failures
- **99.9% uptime** with autonomous recovery

### Developer Experience Metrics
- **<60 seconds** for Tier 0 test feedback
- **<5 minutes** for PR validation
- **<24 hours** average PR lifetime
- **<2% flaky test rate** in CI

### Quality Indicators
- **≥75% test coverage** (gate), target 85%
- **≥70% mutation score** (weekly validation)
- **<10% performance regression** tolerance
- **Zero critical security vulnerabilities**

## 📚 Additional Resources

- [Development Guide](DEVELOPMENT_GUIDE.md) - Complete onboarding and daily workflow
- [Testing Guide](TESTING_GUIDE.md) - Comprehensive testing strategy
- [Autonomous Deployment](leanvibe-backend/AUTONOMOUS_DEPLOYMENT.md) - CI/CD pipeline details
- [XP Autonomous Workflow](XP_AUTONOMOUS_WORKFLOW.md) - Core principles and practices

## 🤝 Getting Help

### Communication Channels
- **GitHub Issues** - Bug reports and feature requests
- **GitHub Discussions** - Questions and community discussions
- **Pull Requests** - Code reviews and collaboration

### Escalation Process
1. **Self-service** - Use troubleshooting guide and tools
2. **Documentation** - Search existing guides and references
3. **Community** - Ask questions in GitHub Discussions
4. **Maintainers** - Tag core team for urgent issues

### Code of Conduct
We follow the [Contributor Covenant](https://www.contributor-covenant.org/):
- **Be welcoming** to newcomers and experienced contributors
- **Be respectful** of different viewpoints and experiences
- **Focus on what's best** for the community and project
- **Show empathy** towards other community members

---

**🤖 Remember: This autonomous system is designed to handle 85%+ of development tasks automatically. Focus on solving problems, and let the automation handle the quality gates!**