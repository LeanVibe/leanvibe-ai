# 🛠 LeanVibe Installation Guide - Complete XP Toolchain Setup

> **From zero to autonomous development in one command, with full XP toolchain**

This guide provides comprehensive installation instructions for LeanVibe's autonomous development platform, including all tools needed for contract-first development, quality ratcheting, and 8+ hour hands-off coding sessions.

## 📋 Table of Contents

- [System Requirements](#system-requirements)
- [Quick Installation](#quick-installation)
- [Manual Installation](#manual-installation)
- [XP Toolchain Setup](#xp-toolchain-setup)
- [Git Hooks Configuration](#git-hooks-configuration)  
- [Quality Ratchet Initialization](#quality-ratchet-initialization)
- [Developer Shortcuts Setup](#developer-shortcuts-setup)
- [Monitoring System Configuration](#monitoring-system-configuration)
- [Verification & Testing](#verification--testing)
- [Troubleshooting](#troubleshooting)

---

## 💻 System Requirements

### Minimum Requirements
- **OS**: macOS 13.0+ (Apple Silicon preferred) or Linux Ubuntu 20.04+
- **Memory**: 8GB RAM (16GB+ recommended for MLX)
- **Storage**: 5GB free space
- **Network**: Internet connection for initial setup

### Recommended Setup
- **Hardware**: Mac Studio/MacBook Pro with M2/M3/M4 chip
- **Memory**: 32GB RAM for optimal MLX performance
- **Storage**: SSD with 20GB+ free space
- **Terminal**: iTerm2 or modern terminal with color support

### Software Prerequisites
- **Git**: 2.30+
- **Python**: 3.11+ (pyenv recommended)
- **Node.js**: 18+ (for TypeScript client generation)
- **Docker**: 20+ (for production deployment)

---

## ⚡ Quick Installation

### One-Command Setup (Recommended)

```bash
# Download and run autonomous setup
curl -fsSL https://raw.githubusercontent.com/leanvibe-ai/leanvibe-backend/main/install.sh | bash -s -- --autonomous

# Or clone first, then setup
git clone https://github.com/leanvibe-ai/leanvibe-backend.git
cd leanvibe-backend
./start.sh --autonomous
```

**What this installs:**
- ✅ Python environment with uv package manager
- ✅ All dependencies including MLX framework
- ✅ Quality ratchet tools and configuration
- ✅ Git hooks for pre-commit validation
- ✅ Developer shortcuts (vf, vp, fix, gen, qc, pp)
- ✅ Contract generation tools
- ✅ Monitoring dashboard
- ✅ Synthetic probe infrastructure
- ✅ Auto-merge deployment pipeline

### Verify Quick Installation

```bash
# Source developer shortcuts
source scripts/dev_shortcuts.sh

# Check autonomous readiness
health

# Expected output:
# ✅ Python Environment: 3.11.7
# ✅ All dependencies installed
# ✅ MLX framework ready
# ✅ Quality ratchet initialized
# ✅ Git hooks configured
# ✅ Developer shortcuts active
# ✅ Autonomous development ready!

# Quick smoke test
vf
# Expected: All Tier 0 tests pass in <60s
```

---

## 🔧 Manual Installation

### Step 1: Environment Setup

```bash
# Install uv package manager (Python environment management)
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env

# Clone repository
git clone https://github.com/leanvibe-ai/leanvibe-backend.git
cd leanvibe-backend

# Create virtual environment and install dependencies
uv sync
```

### Step 2: MLX Framework (Apple Silicon)

```bash
# Install MLX for Apple Silicon acceleration
uv sync --extra mlx

# Verify MLX installation
uv run python -c "import mlx.core; print('✅ MLX available')"

# For Linux/Intel Macs (fallback to CPU mode)
uv sync --extra cpu-only
```

### Step 3: Database Setup (Optional)

```bash
# Install Neo4j (for graph features)
brew install neo4j
brew services start neo4j

# Or use Docker
docker run -d --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:latest

# Verify connection
curl http://localhost:7474
```

### Step 4: Development Tools

```bash
# Install Node.js for TypeScript generation
brew install node

# Install additional development tools
npm install -g wscat          # WebSocket testing
brew install jq               # JSON processing
pip install --user pre-commit # Git hooks framework
```

---

## 🧰 XP Toolchain Setup

### Quality Ratchet Installation

```bash
# Initialize quality ratchet system
python tools/quality_ratchet.py --init

# This creates:
# ✅ quality_ratchet.json - Target metrics and thresholds
# ✅ Baseline measurements for your codebase
# ✅ Quality gate enforcement rules
# ✅ Trend tracking configuration

# Verify quality ratchet
python tools/quality_ratchet.py --report
```

### Test Infrastructure Setup

```bash
# Install test dependencies
uv sync --extra test

# Setup 4-tier testing structure
mkdir -p tests/{tier0,tier1,tier2,integration}

# Configure pytest for different tiers
cat > pytest.ini << 'EOF'
[tool:pytest]
testpaths = tests
markers =
    tier0: Fast tests (<60s) - unit, contract, type checking
    tier1: PR gate tests (3-5m) - integration, coverage validation
    tier2: Nightly tests (30m) - e2e, performance, mutation testing
    tier3: Weekly tests (2h) - comprehensive validation
    unit: Unit tests
    integration: Integration tests
    contract: Contract validation tests
    performance: Performance tests
    mutation: Mutation testing
    e2e: End-to-end tests
EOF

# Verify test setup
make test-tier0
```

### Contract Generation Setup

```bash
# Install OpenAPI tools
pip install openapi-spec-validator
npm install -g @openapitools/openapi-generator-cli

# Setup contract generation
chmod +x contracts/generate.py

# Initialize contract toolchain
cd contracts
python generate.py --init
cd ..

# Verify contract generation
gen  # Should generate models from openapi.yaml
```

---

## 🎣 Git Hooks Configuration

### Pre-commit Hooks Installation

```bash
# Create git hooks directory
mkdir -p .githooks

# Pre-commit hook (runs Tier 0 tests + quality ratchet)
cat > .githooks/pre-commit << 'EOF'
#!/bin/bash
set -e

echo "🔍 Running pre-commit validation..."

# Source developer shortcuts if available
if [[ -f "scripts/dev_shortcuts.sh" ]]; then
    source scripts/dev_shortcuts.sh
fi

# Run fast verification (Tier 0)
if command -v vf &> /dev/null; then
    vf
else
    echo "Running manual pre-commit checks..."
    make test-tier0
    python tools/quality_ratchet.py --no-record
fi

echo "✅ Pre-commit validation passed!"
EOF

# Pre-push hook (runs Tier 1 tests)
cat > .githooks/pre-push << 'EOF'
#!/bin/bash
set -e

echo "🚀 Running pre-push validation..."

# Source developer shortcuts if available
if [[ -f "scripts/dev_shortcuts.sh" ]]; then
    source scripts/dev_shortcuts.sh
fi

# Run PR verification (Tier 1)  
if command -v vp &> /dev/null; then
    vp
else
    echo "Running manual pre-push checks..."
    make test-tier1
    python tools/quality_ratchet.py --enforce
fi

echo "✅ Pre-push validation passed!"
EOF

# Make hooks executable
chmod +x .githooks/pre-commit
chmod +x .githooks/pre-push

# Configure Git to use custom hooks
git config core.hooksPath .githooks

echo "✅ Git hooks configured successfully!"
```

### Verify Git Hooks

```bash
# Test pre-commit hook
git add -A
git commit -m "test: verify git hooks" --no-verify  # Skip for testing
git reset --soft HEAD~1  # Undo commit

# Test with hook enabled (should run Tier 0 tests)
echo "# Test change" >> README.md
git add README.md
git commit -m "test: verify pre-commit hook"
# Should automatically run vf and quality ratchet
```

---

## 📊 Quality Ratchet Initialization

### Configure Quality Targets

```bash
# Initialize with your project's current metrics
python tools/quality_ratchet.py --init --measure-baseline

# This analyzes your codebase and creates:
cat quality_ratchet.json
```

```json
{
  "global_targets": {
    "coverage_percent_min": 70.0,
    "mutation_score_min": 60.0,
    "test_execution_time_max": 60.0,
    "performance_p95_max": 500.0,
    "memory_usage_mb_max": 500.0,
    "flaky_test_count_max": 2,
    "security_issues_max": 0,
    "technical_debt_ratio_max": 0.05
  },
  "per_module_targets": {
    "app/api": {
      "coverage_percent_min": 80.0
    },
    "app/core": {
      "coverage_percent_min": 85.0
    },
    "app/services": {
      "coverage_percent_min": 75.0
    }
  },
  "ratchet_settings": {
    "min_improvement_threshold": 0.5,
    "regression_tolerance": 1.0,
    "consecutive_improvements_required": 2,
    "grace_period_hours": 24
  }
}
```

### Customize Quality Gates

```bash
# Edit targets based on your project needs
vim quality_ratchet.json

# For new projects - start with achievable targets:
{
  "global_targets": {
    "coverage_percent_min": 50.0,  # Start low, ratchet up
    "mutation_score_min": 30.0,    # Build quality gradually
    "test_execution_time_max": 120.0  # Allow more time initially
  }
}

# For mature projects - set aggressive targets:
{
  "global_targets": {
    "coverage_percent_min": 85.0,  # High quality bar
    "mutation_score_min": 75.0,    # Strong test quality
    "test_execution_time_max": 30.0   # Fast feedback loop
  }
}
```

### Enable Quality Enforcement

```bash
# Test quality ratchet (non-enforcing)
python tools/quality_ratchet.py --report

# Enable enforcement (blocks commits that decrease quality)
python tools/quality_ratchet.py --enforce

# Add to CI/CD pipeline
cat >> .github/workflows/quality-gate.yml << 'EOF'
name: Quality Gate
on: [push, pull_request]
jobs:
  quality-ratchet:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: uv sync
      - name: Run quality ratchet
        run: python tools/quality_ratchet.py --enforce --strict
EOF
```

---

## 🚀 Developer Shortcuts Setup

### Install Developer Shortcuts

```bash
# Make shortcuts executable
chmod +x scripts/dev_shortcuts.sh

# Add to shell profile for permanent access
echo 'source /path/to/leanvibe-backend/scripts/dev_shortcuts.sh' >> ~/.zshrc
# or for bash:
echo 'source /path/to/leanvibe-backend/scripts/dev_shortcuts.sh' >> ~/.bashrc

# Source for current session
source scripts/dev_shortcuts.sh

# Verify shortcuts are available
shortcuts
```

**Available shortcuts after setup:**
```bash
# Quality shortcuts
vf          # Verify fast (Tier 0 tests, <60s)
vp          # Verify PR (Tier 1 tests, 3-5m)
fix         # Auto-fix formatting and linting
gen         # Generate contracts from schemas

# Testing shortcuts  
t0          # Run Tier 0 tests only
t1          # Run Tier 1 tests only
t2          # Run Tier 2 tests only
tw          # Watch mode for continuous testing

# Quality monitoring
qd          # Quality dashboard/metrics
qr          # Quality ratchet report
qre         # Quality ratchet enforce

# Workflow shortcuts
qc 'msg'    # Quick commit with pre-commit checks
pp          # Push with PR verification

# Environment
health      # Check development environment
setup       # Setup development environment
```

### Configure Make Commands

```bash
# Create Makefile with common tasks
cat > Makefile << 'EOF'
.PHONY: install test test-tier0 test-tier1 test-tier2 format lint clean

# Installation
install:
	uv sync --all-extras

install-dev:
	uv sync --all-extras --dev

# Testing tiers
test-tier0:
	uv run pytest -m "tier0 or unit or contract" --maxfail=1 --timeout=50

test-tier1:
	uv run pytest -m "tier1 or integration" --cov=app --cov-fail-under=75

test-tier2:
	uv run pytest -m "tier2 or e2e or performance" --timeout=1800

test-all:
	uv run pytest tests/ -v --cov=app

# Watch mode
watch-tier0:
	uv run ptw --runner "pytest -m tier0"

# Code quality
format:
	uv run black app/ tests/
	uv run isort app/ tests/

lint:
	uv run ruff check app/ tests/
	uv run mypy app/

# Quality gates
quality-check:
	python tools/quality_ratchet.py --report

quality-enforce:
	python tools/quality_ratchet.py --enforce

# Contract generation
generate-contracts:
	cd contracts && python generate.py

# Clean up
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +

# Development server
dev:
	uv run uvicorn app.main:app --reload --log-level debug

# Production server
prod:
	uv run gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker

# Health checks
health:
	@python -c "import requests; print('Health:', requests.get('http://localhost:8000/health').json())"

# Setup everything
setup-all: install generate-contracts
	@echo "✅ Setup complete - run 'make dev' to start server"
EOF
```

---

## 📊 Monitoring System Configuration

### Metrics Dashboard Setup

```bash
# Install monitoring dependencies
pip install prometheus_client grafana-api

# Create monitoring configuration
mkdir -p monitoring/config

# Setup metrics collection
cat > monitoring/metrics_config.py << 'EOF'
"""Monitoring configuration for LeanVibe"""

METRICS_CONFIG = {
    "quality_metrics": {
        "test_coverage": {"threshold": 75, "target": 85},
        "mutation_score": {"threshold": 60, "target": 75},
        "performance_p95": {"threshold": 500, "target": 300}
    },
    "deployment_metrics": {
        "auto_merge_rate": {"threshold": 80, "target": 90},
        "rollback_frequency": {"threshold": 5, "target": 2},
        "deployment_success": {"threshold": 95, "target": 98}
    },
    "developer_metrics": {
        "commit_frequency": {"target": 8},
        "pr_cycle_time": {"threshold": 240, "target": 120},
        "context_switches": {"threshold": 5, "target": 2}
    }
}
EOF

# Start metrics dashboard
python tools/metrics_dashboard.py --serve --port 3000
# Dashboard available at http://localhost:3000
```

### Synthetic Monitoring Setup

```bash
# Create synthetic probe configuration
mkdir -p monitoring/probes

# Setup health probes
cat > deploy/synthetic_probes.sh << 'EOF'
#!/bin/bash
# Synthetic monitoring probes for autonomous deployment validation

set -e

ENVIRONMENT=${1:-staging}
MODE=${2:-normal}  # normal, comprehensive, emergency

BASE_URL="http://localhost:8000"
if [ "$ENVIRONMENT" = "production" ]; then
    BASE_URL="https://api.leanvibe.ai"
elif [ "$ENVIRONMENT" = "staging" ]; then
    BASE_URL="https://staging-api.leanvibe.ai"
fi

echo "🔍 Running synthetic probes against $BASE_URL..."

# Basic health check
echo "Testing basic health..."
curl -f "$BASE_URL/health" > /dev/null
echo "✅ Basic health check passed"

# MLX service health
echo "Testing MLX service..."
curl -f "$BASE_URL/health/mlx" > /dev/null  
echo "✅ MLX health check passed"

# API endpoints
echo "Testing API endpoints..."
curl -f "$BASE_URL/api/projects" > /dev/null
echo "✅ Projects API responding"

# Performance validation
echo "Testing performance..."
RESPONSE_TIME=$(curl -o /dev/null -s -w '%{time_total}' "$BASE_URL/health")
if (( $(echo "$RESPONSE_TIME > 1.0" | bc -l) )); then
    echo "❌ Health endpoint too slow: ${RESPONSE_TIME}s"
    exit 1
fi
echo "✅ Performance check passed: ${RESPONSE_TIME}s"

# Contract validation
if [ "$MODE" = "comprehensive" ]; then
    echo "Running comprehensive validation..."
    python monitoring/contract_validation.py "$BASE_URL"
    echo "✅ Contract validation passed"
fi

echo "🎉 All synthetic probes passed!"
EOF

chmod +x deploy/synthetic_probes.sh
```

### Alert Configuration

```bash
# Setup alerting for autonomous failures
cat > monitoring/alerts.py << 'EOF'
"""Alert configuration for autonomous development failures"""

ALERT_RULES = {
    "auto_merge_failure": {
        "condition": "auto_merge_rate < 80%",
        "severity": "warning", 
        "notify": ["developers", "devops"],
        "message": "Auto-merge rate below threshold - requires attention"
    },
    "quality_regression": {
        "condition": "coverage_drop > 5%",
        "severity": "critical",
        "notify": ["developers", "qa"],
        "message": "Code coverage dropped significantly"
    },
    "deployment_failure": {
        "condition": "deployment_failures > 2 in 1h",
        "severity": "critical", 
        "notify": ["devops", "oncall"],
        "message": "Multiple deployment failures - autonomous system may be compromised"
    }
}

# Webhook configurations
WEBHOOKS = {
    "slack": "https://hooks.slack.com/services/...",
    "pagerduty": "https://events.pagerduty.com/integration/...",
    "email": "alerts@leanvibe.ai"
}
EOF
```

---

## ✅ Verification & Testing

### Complete Installation Verification

```bash
# Run comprehensive installation test
python tools/installation_validator.py

# Expected output:
"""
🔍 LeanVibe Installation Validation
=====================================

✅ Python Environment
   - Version: 3.11.7
   - Virtual environment: Active
   - Package manager: uv 0.1.44

✅ Dependencies  
   - Core packages: 47/47 installed
   - MLX framework: Available
   - Test framework: Ready
   - Quality tools: Configured

✅ Git Configuration
   - Repository: Clean
   - Hooks: Installed (.githooks)
   - Pre-commit: Active
   - Pre-push: Active

✅ Quality System
   - Ratchet config: Valid
   - Baseline metrics: Recorded
   - Enforcement: Ready
   - Targets: Achievable

✅ Developer Tools
   - Shortcuts: Active (12 commands)
   - Make targets: 18 available
   - Contract generation: Ready
   - Monitoring: Configured

✅ Testing Infrastructure
   - Tier 0: 23 tests, <60s target
   - Tier 1: 87 tests, 3-5m target  
   - Tier 2: 34 tests, 30m target
   - Coverage: 78% current

✅ Autonomous Readiness
   - Auto-merge: Configured
   - Quality gates: Active
   - Rollback: <60s capable
   - Monitoring: Enabled

🚀 Installation complete! Ready for 8+ hour autonomous development.
"""
```

### Test Autonomous Workflow

```bash
# Create test feature to verify autonomous pipeline
git checkout -b test/autonomous-verification

# Add simple test endpoint
echo 'def test_autonomous_verification(): assert True' > tests/tier0/test_autonomous.py

# Run through autonomous workflow
vf              # Should pass in <60s
fix             # Should show no fixes needed
qc "test: verify autonomous workflow"
pp              # Should create PR and pass all checks

# Verify auto-merge setup
gh pr view --json labels
# Should show labels for auto-merge eligibility

# Clean up test
git checkout main
git branch -D test/autonomous-verification
```

### Performance Benchmarking

```bash
# Run performance benchmarks to establish baselines
python tools/performance_benchmark.py --full

# Results saved to test_results/performance_baseline.json
# Use for future performance regression detection

# Test Tier 0 speed requirement
time make test-tier0
# Should complete in <60 seconds

# Test quality ratchet performance
time python tools/quality_ratchet.py --report
# Should complete in <10 seconds for responsive development
```

---

## 🐛 Troubleshooting

### Common Installation Issues

#### MLX Installation Problems (Apple Silicon)
```bash
# Check architecture
uname -m
# Expected: arm64 for Apple Silicon

# Reinstall MLX with specific options
pip uninstall mlx mlx-lm
uv sync --extra mlx --reinstall-package mlx

# Verify installation
python -c "import mlx.core; print(f'MLX version: {mlx.__version__}')"
```

#### Permission Issues
```bash
# Fix git hooks permissions
chmod +x .githooks/*
git config core.hooksPath .githooks

# Fix script permissions
find scripts/ -name "*.sh" -exec chmod +x {} \;

# Fix Python path issues
echo "export PYTHONPATH=\$PYTHONPATH:\$(pwd)" >> ~/.zshrc
```

#### Quality Ratchet Configuration Issues
```bash
# Reset quality ratchet to defaults
rm quality_ratchet.json
python tools/quality_ratchet.py --init --reset

# Debug quality metrics
python tools/quality_ratchet.py --debug --verbose

# Check test discovery
pytest --collect-only | grep "tier0\|tier1"
```

### Environment-Specific Issues

#### macOS Issues
```bash
# Install Xcode command line tools if needed
xcode-select --install

# Fix Python SSL issues  
/Applications/Python\ 3.11/Install\ Certificates.command

# Homebrew permission fixes
sudo chown -R $(whoami) $(brew --prefix)/*
```

#### Linux Issues
```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install build-essential python3-dev

# Fix locale issues
export LC_ALL=C.UTF-8
export LANG=C.UTF-8
```

#### Docker Issues
```bash
# Test Docker setup
docker run hello-world

# Fix Docker daemon issues
sudo systemctl start docker
sudo usermod -aG docker $USER
```

### Performance Optimization

#### Speed Up Test Execution
```bash
# Parallel test execution
pip install pytest-xdist
export PYTEST_ADDOPTS="-n auto"

# Optimize Python imports
pip install importtime
python -X importtime -c "import app.main" 2> import_time.log
```

#### Memory Usage Optimization
```bash
# Monitor memory usage during tests
pip install memory_profiler
python -m memory_profiler tools/quality_ratchet.py

# Optimize MLX memory usage
export MLX_GPU_MEMORY_LIMIT=4096  # MB
```

### Getting Help

#### Debug Information Collection
```bash
# Generate comprehensive debug report
python tools/debug_report.py > debug_info.txt

# Include system information
uname -a >> debug_info.txt
python --version >> debug_info.txt
git --version >> debug_info.txt
docker --version >> debug_info.txt

# Test results
make test-tier0 2>&1 | tee test_debug.log
```

#### Community Support
- **GitHub Issues**: [Report bugs and feature requests](https://github.com/leanvibe-ai/leanvibe-backend/issues)
- **Documentation**: [Browse additional guides](./README.md)
- **Examples**: [See autonomous workflow examples](./QUICKSTART.md)

---

## 🎯 Next Steps

### Start Your First Autonomous Session

```bash
# Source shortcuts permanently
echo 'source /path/to/leanvibe-backend/scripts/dev_shortcuts.sh' >> ~/.zshrc
exec zsh

# Start development server
make dev

# Create your first autonomous feature
git checkout -b feature/my-awesome-feature
# ... make changes ...
vf && qc "feat: awesome feature" && pp

# Add auto-merge label and let the system take over!
gh pr edit --add-label "auto-merge"
```

### Customize for Your Team

```bash
# Adjust quality targets for your codebase
vim quality_ratchet.json

# Customize shortcuts for your workflow  
vim scripts/dev_shortcuts.sh

# Configure deployment pipeline
vim .github/workflows/autonomous.yml
```

### Monitor Your Autonomous Success

```bash
# Track your autonomous development metrics
qd  # Quality dashboard

# Measure productivity improvements
# - Time spent on features vs process
# - Auto-merge success rate  
# - Rollback frequency
# - Developer context switches
```

---

**🤖 Installation complete! You're now ready for 8+ hours of autonomous development.**

*The future of software development is autonomous. Your productivity journey starts now.*