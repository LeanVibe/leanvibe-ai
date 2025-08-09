# LeanVibe Backend Tiered Test System
# Following Extreme Programming principles with fast feedback loops
# 
# Test Tiers:
# - Tier 0: Pre-commit (<60s) - Unit tests, type checking, linting, contract tests
# - Tier 1: PR Gate (3-5m) - Full contract tests, WebSocket tests, smoke tests, coverage
# - Tier 2: Nightly (30m) - E2E tests, mutation testing sample, performance regression
# - Tier 3: Weekly (2h) - Load testing, security scanning, dependency audit

.PHONY: help install test-tier0 test-tier1 test-tier2 test-tier3 lint format type-check coverage clean setup-tools verify-fast verify-pr auto-fix generate-contracts quality-dashboard

# Default target
help:
	@echo "LeanVibe Tiered Test System"
	@echo ""
	@echo "Available targets:"
	@echo "  install      - Install dependencies and setup tools"
	@echo "  test-tier0   - Pre-commit tests (<60s): Units, contracts, types, lint"
	@echo "  test-tier1   - PR gate tests (3-5m): Full contracts, WebSocket, smoke, coverage"
	@echo "  test-tier2   - Nightly tests (30m): E2E, mutation sample, perf regression"
	@echo "  test-tier3   - Weekly tests (2h): Load testing, security scan, dependency audit"
	@echo ""
	@echo "Developer Shortcuts:"
	@echo "  verify-fast  - Fast verification (Tier 0 + quality ratchet)"
	@echo "  verify-pr    - PR verification (Tier 1 + quality ratchet enforce)"
	@echo "  auto-fix     - Auto-fix formatting and linting issues"
	@echo "  generate-contracts - Generate/update API contracts from schemas"
	@echo ""
	@echo "Quality & Monitoring:"
	@echo "  quality-dashboard - Open quality metrics dashboard"
	@echo "  lint         - Run all linting checks"
	@echo "  format       - Format code with black and isort"
	@echo "  type-check   - Run mypy type checking"
	@echo "  coverage     - Generate coverage report"
	@echo "  clean        - Clean test artifacts"
	@echo "  setup-tools  - Setup testing tools"

# Environment variables
PYTHON = python3
PIP = pip3
PYTEST = pytest
VENV_DIR = venv
TEST_DIR = tests
TOOLS_DIR = tools
COVERAGE_MIN = 70

# Install dependencies and setup environment
install:
	@echo "🔧 Installing dependencies..."
	$(PIP) install -e .[dev,test]
	$(PIP) install pre-commit pytest-timeout pytest-xdist pytest-mock mutpy bandit safety
	@echo "✅ Dependencies installed"

# Setup testing tools
setup-tools:
	@echo "🛠️  Setting up testing tools..."
	mkdir -p $(TOOLS_DIR)
	mkdir -p test_results/metrics
	mkdir -p test_results/reports
	touch test_results/metrics/performance.json
	touch test_results/metrics/flaky_tests.json
	touch test_results/metrics/coverage_history.json
	@echo "✅ Tools setup complete"

# =============================================================================
# TIER 0: Pre-commit Tests (<60s)
# Fast, essential checks that must pass before any commit
# =============================================================================
test-tier0: setup-tools
	@echo "🚀 Running Tier 0 tests (Pre-commit, target <60s)..."
	@start_time=$$(date +%s); \
	$(MAKE) lint && \
	$(MAKE) type-check && \
	$(PYTHON) $(TOOLS_DIR)/schema_drift.py --check && \
	$(PYTEST) -m "unit or contract" --maxfail=3 --tb=short -q && \
	$(PYTHON) $(TOOLS_DIR)/coverage_gate.py --min-increase=0 && \
	end_time=$$(date +%s); \
	duration=$$((end_time - start_time)); \
	echo "⏱️  Tier 0 completed in $${duration}s"; \
	if [ $$duration -gt 60 ]; then \
		echo "⚠️  WARNING: Tier 0 took $${duration}s (target <60s)"; \
	fi

# =============================================================================
# TIER 1: PR Gate Tests (3-5 minutes)
# Comprehensive validation before merging PRs
# =============================================================================
test-tier1: setup-tools
	@echo "🔍 Running Tier 1 tests (PR Gate, target 3-5m)..."
	@start_time=$$(date +%s); \
	$(PYTEST) -m "integration or websocket or smoke" --cov=app --cov-branch --cov-report=term --cov-report=html:test_results/coverage_html --maxfail=5 -x && \
	$(PYTHON) $(TOOLS_DIR)/flaky_detector.py --analyze && \
	$(PYTHON) $(TOOLS_DIR)/coverage_gate.py --enforce && \
	end_time=$$(date +%s); \
	duration=$$((end_time - start_time)); \
	echo "⏱️  Tier 1 completed in $${duration}s"; \
	if [ $$duration -gt 300 ]; then \
		echo "⚠️  WARNING: Tier 1 took $${duration}s (target <300s)"; \
	fi

# =============================================================================
# TIER 2: Nightly Tests (30 minutes)
# Extended testing for regression detection and quality assurance
# =============================================================================
test-tier2: setup-tools
	@echo "🌙 Running Tier 2 tests (Nightly, target 30m)..."
	@start_time=$$(date +%s); \
	$(PYTEST) -m "e2e or performance" --maxfail=10 --tb=line && \
	$(PYTHON) $(TOOLS_DIR)/perf_regression.py --baseline=main --threshold=10 && \
	mut.py --target app --unit-test tests --runner pytest --show-mutants | head -100 && \
	end_time=$$(date +%s); \
	duration=$$((end_time - start_time)); \
	echo "⏱️  Tier 2 completed in $${duration}s"; \
	if [ $$duration -gt 1800 ]; then \
		echo "⚠️  WARNING: Tier 2 took $${duration}s (target <1800s)"; \
	fi

# =============================================================================
# TIER 3: Weekly Tests (2 hours)
# Comprehensive security, performance and dependency validation
# =============================================================================
test-tier3: setup-tools
	@echo "🔒 Running Tier 3 tests (Weekly, target 2h)..."
	@start_time=$$(date +%s); \
	$(PYTEST) -m "load or security or dependency_audit" --maxfail=20 --tb=line && \
	bandit -r app/ -f json -o test_results/reports/security.json && \
	safety check --json --output test_results/reports/dependencies.json && \
	$(PYTHON) $(TOOLS_DIR)/perf_regression.py --full-analysis && \
	end_time=$$(date +%s); \
	duration=$$((end_time - start_time)); \
	echo "⏱️  Tier 3 completed in $${duration}s"; \
	if [ $$duration -gt 7200 ]; then \
		echo "⚠️  WARNING: Tier 3 took $${duration}s (target <7200s)"; \
	fi

# =============================================================================
# Code Quality Targets
# =============================================================================
lint:
	@echo "🧹 Running linting checks..."
	black --check --diff app/ tests/
	isort --check-only --diff app/ tests/
	flake8 app/ tests/

format:
	@echo "✨ Formatting code..."
	black app/ tests/
	isort app/ tests/

type-check:
	@echo "🔍 Running type checks..."
	mypy app/ --ignore-missing-imports

coverage:
	@echo "📊 Generating coverage report..."
	$(PYTEST) --cov=app --cov-branch --cov-report=term --cov-report=html:test_results/coverage_html --cov-report=xml:test_results/coverage.xml
	@echo "Coverage report generated at test_results/coverage_html/index.html"

# =============================================================================
# Utility Targets
# =============================================================================
clean:
	@echo "🧽 Cleaning test artifacts..."
	rm -rf test_results/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Development shortcuts
dev-test: test-tier0
	@echo "✅ Development tests completed"

pr-ready: test-tier1
	@echo "✅ PR ready - all gate tests passed"

# Parallel execution for faster feedback
test-tier0-parallel: setup-tools
	@echo "🚀 Running Tier 0 tests in parallel..."
	$(PYTEST) -m "tier0" -n auto --maxfail=3 --tb=short -q

test-tier1-parallel: setup-tools
	@echo "🔍 Running Tier 1 tests in parallel..."
	$(PYTEST) -m "tier1" -n auto --cov=app --maxfail=5

# Test specific components
test-contracts:
	$(PYTEST) -m "contracts" -v

test-websocket:
	$(PYTEST) -m "websocket" -v

test-performance:
	$(PYTEST) -m "performance" --benchmark-only

# Continuous feedback during development
watch-tier0:
	@echo "👀 Watching for changes, running Tier 0 tests..."
	watchmedo auto-restart --patterns="*.py" --recursive --ignore-patterns="*/.git/*;*/test_results/*" -- make test-tier0

# Health check for the test system itself
test-system-health:
	@echo "🏥 Checking test system health..."
	@$(PYTHON) -c "import pytest; print(f'pytest version: {pytest.__version__}')"
	@$(PYTHON) -c "import coverage; print(f'coverage version: {coverage.__version__}')"
	@test -d $(TOOLS_DIR) && echo "✅ Tools directory exists" || echo "❌ Tools directory missing"
	@test -f $(TOOLS_DIR)/schema_drift.py && echo "✅ Schema drift detector ready" || echo "❌ Schema drift detector missing"
	@test -f $(TOOLS_DIR)/flaky_detector.py && echo "✅ Flaky test detector ready" || echo "❌ Flaky test detector missing"
	@test -f $(TOOLS_DIR)/coverage_gate.py && echo "✅ Coverage gate ready" || echo "❌ Coverage gate missing"
	@test -f $(TOOLS_DIR)/perf_regression.py && echo "✅ Performance regression detector ready" || echo "❌ Performance regression detector missing"

# =============================================================================
# Developer Ergonomic Shortcuts - Autonomous XP Workflow
# =============================================================================

# Fast verification - Tier 0 tests with quality ratchet check
verify-fast: test-tier0
	@echo "🎯 Running quality ratchet check..."
	@$(PYTHON) $(TOOLS_DIR)/quality_ratchet.py --no-record || echo "⚠️  Quality ratchet check failed (warning only for dev)"
	@echo "✅ Fast verification completed!"

# PR verification - Tier 1 tests with quality ratchet enforcement
verify-pr: test-tier1
	@echo "🎯 Enforcing quality ratchet..."
	@$(PYTHON) $(TOOLS_DIR)/quality_ratchet.py --enforce
	@echo "✅ PR verification completed - ready for merge!"

# Auto-fix formatting and linting issues
auto-fix:
	@echo "🔧 Auto-fixing code quality issues..."
	@echo "📝 Formatting with black and isort..."
	black app/ tests/ --line-length=88
	isort app/ tests/ --force-single-line-imports --line-length=88
	@if command -v autoflake >/dev/null 2>&1; then \
		echo "🧹 Removing unused imports with autoflake..."; \
		autoflake --remove-all-unused-imports --recursive --in-place app/ tests/; \
	fi
	@echo "✅ Auto-fix completed! Run 'make verify-fast' to verify changes."

# Generate/update API contracts from schemas
generate-contracts:
	@echo "📋 Generating API contracts from schemas..."
	@if [ -f "contracts/generate.py" ]; then \
		cd contracts && $(PYTHON) generate.py && cd ..; \
		echo "✅ Contracts generated successfully!"; \
		if ! git diff --quiet contracts/; then \
			echo "⚠️  Contract files updated - review and commit changes:"; \
			git diff --stat contracts/; \
		else \
			echo "ℹ️  No contract changes detected"; \
		fi \
	else \
		echo "❌ Contract generator not found at contracts/generate.py"; \
		exit 1; \
	fi

# Quality metrics dashboard
quality-dashboard:
	@echo "📊 Opening quality metrics dashboard..."
	@if [ -f "$(TOOLS_DIR)/metrics_dashboard.py" ]; then \
		$(PYTHON) $(TOOLS_DIR)/metrics_dashboard.py --serve; \
	else \
		echo "ℹ️  Dashboard not available, showing quality report:"; \
		$(PYTHON) $(TOOLS_DIR)/quality_ratchet.py --report; \
	fi

# =============================================================================
# Git Hooks Integration
# =============================================================================

# Install git hooks for autonomous quality enforcement
install-hooks:
	@echo "🔗 Installing git hooks..."
	@git config core.hooksPath .githooks
	@chmod +x .githooks/*
	@echo "✅ Git hooks installed!"
	@echo "   • pre-commit: Tier 0 tests + quality checks"
	@echo "   • pre-push: Tier 1 tests + quality ratchet"
	@echo "   • commit-msg: Conventional commit validation"

# =============================================================================
# Developer Environment Setup
# =============================================================================

# Complete development environment setup
dev-setup: install setup-tools install-hooks
	@echo "🚀 Setting up complete development environment..."
	@if [ -f "scripts/dev_shortcuts.sh" ]; then \
		echo "💡 To enable developer shortcuts, run:"; \
		echo "   source scripts/dev_shortcuts.sh"; \
		echo ""; \
		echo "Available shortcuts after sourcing:"; \
		echo "   vf     - verify-fast"; \
		echo "   vp     - verify-pr"; \
		echo "   fix    - auto-fix"; \
		echo "   gen    - generate-contracts"; \
		echo "   qd     - quality-dashboard"; \
	fi
	@$(MAKE) test-system-health
	@echo "✅ Development environment setup complete!"