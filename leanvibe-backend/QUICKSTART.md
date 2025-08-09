# ⚡ LeanVibe Quick Start - Autonomous Development in 5 Minutes

> **From zero to 8+ hours of hands-off development productivity**

This guide gets you started with LeanVibe's autonomous XP workflow that handles 85%+ of deployments automatically while you focus on building features.

## 🎯 What You'll Achieve

By the end of this guide, you'll have:
- ✅ Autonomous development environment with smart shortcuts
- ✅ Contract-first API development with auto-generation
- ✅ Quality ratcheting that prevents code regression
- ✅ 4-tier testing system with <60s inner loop
- ✅ Auto-merge deployments with <60s rollback capability

---

## Step 1: Lightning Setup (60 seconds)

### One Command to Rule Them All
```bash
# Clone and setup with autonomous toolchain
git clone https://github.com/leanvibe-ai/leanvibe-backend
cd leanvibe-backend
./start.sh --autonomous

# This automatically:
# ✅ Installs uv + dependencies + MLX framework
# ✅ Sets up quality ratchet and git hooks
# ✅ Configures developer shortcuts (vf, vp, fix, gen)
# ✅ Initializes contract generation tools
# ✅ Starts monitoring dashboard
```

### Verify Autonomous Readiness
```bash
# Source the developer shortcuts
source scripts/dev_shortcuts.sh

# Check system health
health
# Expected: ✅ All green checks, "autonomous_ready": true

# Quick smoke test
vf
# Expected: ✅ All Tier 0 tests pass in <60s
```

---

## Step 2: Your First Autonomous Feature (3 minutes)

### Create a Feature with Contract-First Development

```bash
# Create feature branch
git checkout -b feature/awesome-new-endpoint

# 1. Define your API contract first
vim contracts/openapi.yaml
# Add new endpoint definition (see example below)

# 2. Generate models from contract
gen
# ✅ Auto-generates Python models + TypeScript types

# 3. Implement the endpoint
vim app/api/endpoints/awesome.py
# Write your endpoint implementation

# 4. Add tests (tier 0 for speed)
vim tests/tier0/test_awesome.py
# Write fast unit tests

# 5. Fast verification cycle
vf              # Verify fast (<60s) - includes contract validation
fix             # Auto-fix any formatting/import issues  
gen             # Regenerate contracts if schema changed
vf              # Verify again
```

### Example: Adding a New Endpoint

**1. Update contract (`contracts/openapi.yaml`):**
```yaml
paths:
  /api/awesome:
    get:
      summary: Get awesome data
      responses:
        '200':
          description: Awesome data response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AwesomeResponse'

components:
  schemas:
    AwesomeResponse:
      type: object
      required: [message, timestamp]
      properties:
        message:
          type: string
        timestamp:
          type: string
          format: date-time
        data:
          type: object
```

**2. Generate models:**
```bash
gen
# ✅ Creates Python models in app/models/
# ✅ Creates TypeScript types in contracts/types.ts
```

**3. Implement endpoint:**
```python
# app/api/endpoints/awesome.py
from fastapi import APIRouter
from app.models.generated import AwesomeResponse
from datetime import datetime

router = APIRouter()

@router.get("/api/awesome", response_model=AwesomeResponse)
async def get_awesome():
    return AwesomeResponse(
        message="This is awesome!",
        timestamp=datetime.now().isoformat(),
        data={"autonomous": True}
    )
```

**4. Add fast test:**
```python
# tests/tier0/test_awesome.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_awesome_endpoint():
    response = client.get("/api/awesome")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "timestamp" in data
    assert data["message"] == "This is awesome!"
```

---

## Step 3: Autonomous Deployment (30 seconds active time)

### Quality-Assured Commit and Push

```bash
# Fast pre-commit verification
vf              # Tier 0 tests + quality ratchet + contract validation

# Quick commit with automatic quality checks
qc "feat: add awesome endpoint with contract validation"

# Push with comprehensive PR verification
pp              # Runs Tier 1 tests, creates PR if needed

# Add auto-merge label for autonomous deployment
gh pr edit --add-label "auto-merge"
```

### What Happens Autonomously (No human intervention needed!)

1. **Automatic Testing Pipeline:**
   - ✅ Tier 0 tests (<60s) 
   - ✅ Tier 1 integration tests (3-5m)
   - ✅ Contract validation
   - ✅ Quality ratchet enforcement

2. **Automatic Deployment:**
   - ✅ Auto-merge when all checks pass
   - ✅ Canary deployment (10% traffic)
   - ✅ Synthetic health probes
   - ✅ Auto-promotion to 100% OR automatic rollback

3. **Continuous Monitoring:**
   - ✅ Real-time health validation
   - ✅ Performance regression detection
   - ✅ <60s rollback if issues detected

---

## Step 4: Monitor Your Autonomous System

### Real-Time Quality Dashboard
```bash
# Open interactive quality metrics
qd
# Shows: coverage trends, mutation score, performance, auto-merge rate
```

### Check Deployment Status
```bash
# PR status and checks
gh pr view --json checks,labels

# Production health
curl http://localhost:8000/health/complete
```

### Quality Ratchet Status
```bash
# View quality report
qr

# Current quality metrics vs targets:
# ✅ Coverage: 78% (target: 75%, trending: 85%)
# ✅ Mutation Score: 65% (target: 60%)
# ✅ Performance P95: 450ms (target: <500ms)
# ✅ Auto-merge Rate: 87% (target: 85%)
```

---

## Step 5: Advanced Autonomous Workflows

### Contract Evolution
```bash
# Update API contract
vim contracts/openapi.yaml

# Detect breaking changes
gen --validate-compatibility
# ✅ Warns about breaking changes
# ✅ Suggests migration strategies
# ✅ Updates schema drift tracking

# Generate new models
gen
```

### Multi-Tier Testing Strategy
```bash
# Different test tiers for different needs
t0              # Tier 0: <60s - unit, contract, type checking
t1              # Tier 1: 3-5m - integration, websocket, smoke tests
t2              # Tier 2: 30m - e2e, performance, mutation (5%)
# t3 runs weekly - comprehensive validation (2h)

# Watch mode for continuous feedback
tw              # Watches files and runs Tier 0 tests
```

### Emergency Procedures
```bash
# Emergency rollback (<60s recovery)
./deploy/rollback.sh production --emergency

# Pause autonomous deployments
gh pr edit --add-label "emergency-pause"

# Resume autonomous operations
gh pr edit --remove-label "emergency-pause" --add-label "auto-merge"
```

---

## 🧠 Understanding the Autonomous Workflow

### The Magic Behind the Shortcuts

| Shortcut | What It Does | Time Saved |
|----------|-------------|------------|
| `vf` | Tier 0 tests + quality ratchet + contracts | 5-15 minutes |
| `vp` | Full PR validation + quality enforcement | 20-45 minutes |
| `fix` | Auto-format + import cleanup + lint fixes | 5-10 minutes |
| `gen` | Contract → model generation + validation | 10-20 minutes |
| `qc` | Quality-checked commit with pre-commit hooks | 5-10 minutes |
| `pp` | Push + PR creation + verification | 15-30 minutes |

### Quality Ratcheting in Action

```bash
# Before your change
qr
# Coverage: 75%, Mutation: 60%, Performance: 480ms

# After your change - quality must improve or stay same
qre
# ✅ Coverage: 78% (+3% improvement)
# ✅ Mutation: 62% (+2% improvement)  
# ✅ Performance: 450ms (30ms improvement)
# ✅ Quality ratchet passed - change approved
```

### Contract-First Benefits

- **No Integration Surprises**: Contracts validated before merge
- **Type Safety**: Auto-generated models prevent runtime errors
- **Documentation**: Always up-to-date API documentation
- **Breaking Change Detection**: Prevents accidental API breaks
- **Client Code Generation**: Frontend gets TypeScript types automatically

---

## 🏆 Productivity Gains

### Before vs After LeanVibe

| Traditional Development | LeanVibe Autonomous |
|------------------------|-------------------|
| 2-4 hours per feature deployment | 8+ hours of continuous coding |
| Manual testing and deployment | 85%+ fully automated |
| 10-30 minute rollbacks | <60 second recovery |
| Constant context switching | Focus on features, not process |
| Quality regressions common | Prevented by ratcheting |
| Manual PR reviews for everything | Smart auto-merge for routine changes |

### Real Developer Testimonial

> *"I pushed 12 features yesterday and only had to manually intervene once. The system handled testing, deployment, and monitoring while I focused on building. When I came back from lunch, 3 more features had deployed themselves successfully."*
>
> — Senior Developer using LeanVibe

---

## 🚀 Next Steps

### Explore Advanced Features
- **[API Documentation](./API.md)** - Deep dive into contract-first development
- **[Autonomous Deployment](./AUTONOMOUS_DEPLOYMENT.md)** - Understanding the full pipeline
- **[Quality Ratcheting Guide](./tools/quality_ratchet.py)** - Advanced quality metrics

### Customize Your Environment
```bash
# Explore all available shortcuts
shortcuts

# Customize quality ratchet settings
vim quality_ratchet.json

# Add custom deployment hooks
vim deploy/canary.sh
```

### Join the Community
- Share your autonomous development wins
- Contribute to the shortcuts and tooling
- Help improve the auto-merge success rate

---

**🤖 Welcome to autonomous development! Your 8-hour coding sessions await.**

*Remember: The goal isn't to remove humans from development—it's to remove humans from the boring, repetitive parts so you can focus on building amazing features.*