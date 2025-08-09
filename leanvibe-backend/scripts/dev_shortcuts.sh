#!/bin/bash
#
# LeanVibe Developer Shortcuts - Extreme Programming Workflow Ergonomics
# Source this file to get developer-friendly aliases for common tasks
#
# Usage: source scripts/dev_shortcuts.sh
#

# Color codes for better UX
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored status messages
print_status() {
    echo -e "${BLUE}[LeanVibe]${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# =============================================================================
# TIER 0: Pre-commit shortcuts (developer inner loop)
# =============================================================================

# Fast verification before commit - Tier 0 tests only
alias vf='verify_fast'
verify_fast() {
    print_status "Running fast verification (Tier 0)..."
    start_time=$(date +%s)
    
    if make test-tier0; then
        end_time=$(date +%s)
        duration=$((end_time - start_time))
        print_success "Fast verification completed in ${duration}s"
        
        # Auto-run quality ratchet
        if python tools/quality_ratchet.py --no-record; then
            print_success "Quality ratchet check passed!"
        else
            print_warning "Quality ratchet check failed, but not enforced for dev"
        fi
        return 0
    else
        print_error "Fast verification failed!"
        return 1
    fi
}

# =============================================================================
# TIER 1: PR preparation shortcuts
# =============================================================================

# Comprehensive PR verification - Tier 1 tests
alias vp='verify_pr'
verify_pr() {
    print_status "Running PR verification (Tier 1)..."
    start_time=$(date +%s)
    
    # First run quality ratchet to baseline current state
    print_status "Recording baseline metrics..."
    python tools/quality_ratchet.py --no-record > /dev/null 2>&1
    
    if make test-tier1; then
        end_time=$(date +%s)
        duration=$((end_time - start_time))
        print_success "PR verification completed in ${duration}s"
        
        # Enforce quality ratchet for PR
        if python tools/quality_ratchet.py --enforce; then
            print_success "Quality ratchet enforced - ready for PR!"
        else
            print_error "Quality ratchet failed - PR not ready"
            return 1
        fi
        return 0
    else
        print_error "PR verification failed!"
        return 1
    fi
}

# =============================================================================
# Code Quality Shortcuts
# =============================================================================

# Auto-fix formatting and linting issues
alias fix='auto_fix'
auto_fix() {
    print_status "Auto-fixing code quality issues..."
    
    # Format code
    print_status "Formatting with black and isort..."
    make format
    
    # Try to fix simple linting issues
    print_status "Running automated fixes..."
    
    # Auto-fix imports with isort
    isort app/ tests/ --force-single-line-imports --line-length=88
    
    # Auto-fix with black
    black app/ tests/ --line-length=88
    
    # Run autoflake to remove unused imports
    if command -v autoflake >/dev/null 2>&1; then
        autoflake --remove-all-unused-imports --recursive --in-place app/ tests/
    fi
    
    print_success "Auto-fix completed! Run 'vf' to verify changes."
}

# =============================================================================
# Contract Generation Shortcuts
# =============================================================================

# Generate/update API contracts from schemas
alias gen='generate_contracts'
generate_contracts() {
    print_status "Generating API contracts from schemas..."
    
    if [ -f "contracts/generate.py" ]; then
        cd contracts
        python generate.py
        cd ..
        print_success "Contracts generated successfully!"
        
        # Check if any files were updated
        if git diff --quiet contracts/; then
            print_status "No contract changes detected"
        else
            print_warning "Contract files updated - review and commit changes"
            git diff --stat contracts/
        fi
    else
        print_error "Contract generator not found at contracts/generate.py"
        return 1
    fi
}

# =============================================================================
# Testing Shortcuts
# =============================================================================

# Run specific test categories
alias t0='test_tier0'
alias t1='test_tier1'
alias t2='test_tier2'

test_tier0() {
    print_status "Running Tier 0 tests..."
    make test-tier0
}

test_tier1() {
    print_status "Running Tier 1 tests..."
    make test-tier1
}

test_tier2() {
    print_status "Running Tier 2 tests..."
    make test-tier2
}

# Watch mode for continuous testing
alias tw='test_watch'
test_watch() {
    print_status "Starting test watch mode (Tier 0)..."
    make watch-tier0
}

# =============================================================================
# Quality Monitoring Shortcuts
# =============================================================================

# Show quality dashboard
alias qd='quality_dashboard'
quality_dashboard() {
    print_status "Opening quality metrics dashboard..."
    if [ -f "tools/metrics_dashboard.py" ]; then
        python tools/metrics_dashboard.py --serve
    else
        print_status "Generating quality report..."
        python tools/quality_ratchet.py --report
    fi
}

# Quality ratchet shortcuts
alias qr='quality_ratchet'
alias qre='quality_ratchet_enforce'

quality_ratchet() {
    python tools/quality_ratchet.py --report
}

quality_ratchet_enforce() {
    python tools/quality_ratchet.py --enforce
}

# =============================================================================
# Development Workflow Shortcuts
# =============================================================================

# Quick commit with automatic quality checks
alias qc='quick_commit'
quick_commit() {
    local message="$1"
    if [ -z "$message" ]; then
        print_error "Usage: qc 'commit message'"
        return 1
    fi
    
    print_status "Running pre-commit checks..."
    if vf; then
        print_status "Committing changes..."
        git add .
        git commit -m "$message"
        print_success "Committed successfully!"
    else
        print_error "Pre-commit checks failed. Fix issues and try again."
        return 1
    fi
}

# Push with PR checks
alias pp='push_pr'
push_pr() {
    local branch=$(git branch --show-current)
    print_status "Preparing to push branch: $branch"
    
    if vp; then
        print_status "Pushing to origin..."
        git push origin "$branch"
        print_success "Push completed! Ready to create PR."
    else
        print_error "PR verification failed. Fix issues and try again."
        return 1
    fi
}

# =============================================================================
# Environment and Setup Shortcuts
# =============================================================================

# Health check for development environment
alias health='dev_health_check'
dev_health_check() {
    print_status "Checking development environment health..."
    
    # Check Python environment
    echo -e "${CYAN}Python Environment:${NC}"
    python --version
    pip --version
    
    # Check key dependencies
    echo -e "${CYAN}Key Dependencies:${NC}"
    python -c "import pytest; print(f'pytest: {pytest.__version__}')" 2>/dev/null || print_error "pytest not installed"
    python -c "import coverage; print(f'coverage: {coverage.__version__}')" 2>/dev/null || print_error "coverage not installed"
    python -c "import black; print(f'black: {black.__version__}')" 2>/dev/null || print_error "black not installed"
    
    # Check Git setup
    echo -e "${CYAN}Git Configuration:${NC}"
    git config user.name 2>/dev/null || print_warning "Git user.name not configured"
    git config user.email 2>/dev/null || print_warning "Git user.email not configured"
    
    # Check project structure
    echo -e "${CYAN}Project Structure:${NC}"
    [ -f "Makefile" ] && echo "✅ Makefile found" || print_error "Makefile missing"
    [ -f "pyproject.toml" ] && echo "✅ pyproject.toml found" || print_error "pyproject.toml missing"
    [ -d "app" ] && echo "✅ app/ directory found" || print_error "app/ directory missing"
    [ -d "tests" ] && echo "✅ tests/ directory found" || print_error "tests/ directory missing"
    [ -d "tools" ] && echo "✅ tools/ directory found" || print_error "tools/ directory missing"
    
    # Test system health
    make test-system-health
}

# Setup development environment
alias setup='dev_setup'
dev_setup() {
    print_status "Setting up development environment..."
    
    # Install dependencies
    make install
    
    # Setup tools
    make setup-tools
    
    # Install pre-commit hooks if available
    if [ -d ".githooks" ]; then
        print_status "Installing git hooks..."
        git config core.hooksPath .githooks
        chmod +x .githooks/*
        print_success "Git hooks installed!"
    fi
    
    # Run health check
    dev_health_check
    
    print_success "Development environment setup complete!"
    print_status "Try running 'vf' to verify everything works!"
}

# =============================================================================
# Performance and Debugging Shortcuts
# =============================================================================

# Profile test performance
alias prof='profile_tests'
profile_tests() {
    print_status "Profiling test performance..."
    python -m pytest tests/ --profile-svg --profile-path=test_results/profile.svg
    print_success "Profile saved to test_results/profile.svg"
}

# Memory usage analysis
alias mem='memory_analysis'
memory_analysis() {
    print_status "Running memory analysis..."
    python -m pytest tests/ --memray --memray-path=test_results/memory_profile.bin
    print_success "Memory profile saved to test_results/memory_profile.bin"
}

# =============================================================================
# Help and Documentation
# =============================================================================

# Show available shortcuts
alias shortcuts='show_shortcuts'
alias help='show_shortcuts'

show_shortcuts() {
    echo -e "${PURPLE}LeanVibe Developer Shortcuts${NC}"
    echo "================================="
    echo ""
    echo -e "${CYAN}Quality Shortcuts:${NC}"
    echo "  vf          - Verify fast (Tier 0 tests, <60s)"
    echo "  vp          - Verify PR (Tier 1 tests, 3-5m)"
    echo "  fix         - Auto-fix formatting and linting"
    echo "  gen         - Generate contracts from schemas"
    echo ""
    echo -e "${CYAN}Testing Shortcuts:${NC}"
    echo "  t0          - Run Tier 0 tests only"
    echo "  t1          - Run Tier 1 tests only" 
    echo "  t2          - Run Tier 2 tests only"
    echo "  tw          - Watch mode for continuous testing"
    echo ""
    echo -e "${CYAN}Quality Monitoring:${NC}"
    echo "  qd          - Quality dashboard/metrics"
    echo "  qr          - Quality ratchet report"
    echo "  qre         - Quality ratchet enforce"
    echo ""
    echo -e "${CYAN}Workflow Shortcuts:${NC}"
    echo "  qc 'msg'    - Quick commit with pre-commit checks"
    echo "  pp          - Push with PR verification"
    echo ""
    echo -e "${CYAN}Environment:${NC}"
    echo "  health      - Check development environment"
    echo "  setup       - Setup development environment"
    echo "  shortcuts   - Show this help"
    echo ""
    echo -e "${CYAN}Performance:${NC}"
    echo "  prof        - Profile test performance"
    echo "  mem         - Memory usage analysis"
}

# =============================================================================
# Initialization
# =============================================================================

# Print welcome message when sourced
print_status "LeanVibe developer shortcuts loaded!"
print_status "Type 'shortcuts' for available commands"
print_status "Quick start: 'vf' for fast checks, 'vp' for PR verification"

# Export functions so they're available in subshells
export -f verify_fast verify_pr auto_fix generate_contracts
export -f test_tier0 test_tier1 test_tier2 test_watch
export -f quality_dashboard quality_ratchet quality_ratchet_enforce
export -f quick_commit push_pr dev_health_check dev_setup
export -f profile_tests memory_analysis show_shortcuts
export -f print_status print_success print_warning print_error