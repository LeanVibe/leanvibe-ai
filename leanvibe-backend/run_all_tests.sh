#!/bin/bash

# LeanVibe Test Automation Script
# 
# This script runs comprehensive tests using the mock infrastructure,
# providing fast and reliable testing without external dependencies.

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="${PROJECT_ROOT}/venv"
COVERAGE_MIN_THRESHOLD=70
RESULTS_DIR="${PROJECT_ROOT}/test_results"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="${RESULTS_DIR}/test_run_${TIMESTAMP}.log"

echo -e "${BLUE}=== LeanVibe Test Automation Suite ===${NC}"
echo -e "${BLUE}Timestamp: $(date)${NC}"
echo -e "${BLUE}Project Root: ${PROJECT_ROOT}${NC}"
echo

# Function to log messages
log() {
    echo -e "$1" | tee -a "${LOG_FILE}"
}

# Function to run command and log output
run_command() {
    local command="$1"
    local description="$2"
    
    log "${BLUE}Running: ${description}${NC}"
    log "${YELLOW}Command: ${command}${NC}"
    
    if eval "$command" >> "${LOG_FILE}" 2>&1; then
        log "${GREEN}✓ SUCCESS: ${description}${NC}"
        return 0
    else
        log "${RED}✗ FAILED: ${description}${NC}"
        return 1
    fi
}

# Create results directory
mkdir -p "${RESULTS_DIR}"

# Initialize log file
echo "LeanVibe Test Run - $(date)" > "${LOG_FILE}"
echo "=======================================" >> "${LOG_FILE}"

# Change to project directory
cd "${PROJECT_ROOT}"

log "${BLUE}Step 1: Environment Setup${NC}"

# Check if virtual environment exists
if [ ! -d "${VENV_PATH}" ]; then
    log "${YELLOW}Creating virtual environment...${NC}"
    python -m venv "${VENV_PATH}"
fi

# Activate virtual environment
if [ -f "${VENV_PATH}/bin/activate" ]; then
    source "${VENV_PATH}/bin/activate"
    log "${GREEN}✓ Virtual environment activated${NC}"
elif [ -f "${VENV_PATH}/Scripts/activate" ]; then
    source "${VENV_PATH}/Scripts/activate"
    log "${GREEN}✓ Virtual environment activated (Windows)${NC}"
else
    log "${YELLOW}⚠ No virtual environment found, using system Python${NC}"
fi

# Install/update dependencies
log "${BLUE}Step 2: Dependency Management${NC}"

run_command "pip install -e ." "Install project in development mode"
run_command "pip install pytest pytest-cov pytest-asyncio pytest-benchmark" "Install test dependencies"

log "${BLUE}Step 3: Mock Infrastructure Validation${NC}"

# Test that mocks are working
run_command "python -c 'from tests.mocks import get_mock_status; print(\"Mock status:\", get_mock_status())'" "Validate mock infrastructure"

log "${BLUE}Step 4: Basic Test Suite${NC}"

# Run basic tests first
run_command "python -m pytest tests/test_basic.py -v --tb=short" "Basic functionality tests"

log "${BLUE}Step 5: Mock Integration Tests${NC}"

# Run mock integration tests
run_command "python -m pytest tests/test_mock_integration.py -v --tb=short" "Mock integration tests"

log "${BLUE}Step 6: Core Service Tests${NC}"

# Run existing service tests that should now work with mocks
CORE_TEST_FILES=(
    "tests/test_ai_service.py"
    "tests/test_models.py"
    "tests/test_integration.py"
    "tests/test_service_manager.py"
)

for test_file in "${CORE_TEST_FILES[@]}"; do
    if [ -f "${test_file}" ]; then
        run_command "python -m pytest ${test_file} -v --tb=short" "Core service tests: $(basename ${test_file})"
    else
        log "${YELLOW}⚠ Test file not found: ${test_file}${NC}"
    fi
done

log "${BLUE}Step 7: API Endpoint Tests${NC}"

# Test API endpoints
API_TEST_FILES=(
    "tests/test_cli_bridge_api.py"
    "tests/test_task_api.py"
    "tests/test_notification_api.py"
)

for test_file in "${API_TEST_FILES[@]}"; do
    if [ -f "${test_file}" ]; then
        run_command "python -m pytest ${test_file} -v --tb=short" "API tests: $(basename ${test_file})"
    else
        log "${YELLOW}⚠ API test file not found: ${test_file}${NC}"
    fi
done

log "${BLUE}Step 8: Performance Benchmarks${NC}"

# Run benchmark tests
if run_command "python -m pytest tests/test_mock_benchmarks.py -v -m benchmark --tb=short" "Performance benchmarks"; then
    log "${GREEN}✓ Benchmarks completed successfully${NC}"
else
    log "${YELLOW}⚠ Benchmarks had issues but continuing${NC}"
fi

log "${BLUE}Step 9: Coverage Analysis${NC}"

# Generate coverage report
COVERAGE_FILE="${RESULTS_DIR}/coverage_${TIMESTAMP}.xml"
COVERAGE_HTML_DIR="${RESULTS_DIR}/coverage_html_${TIMESTAMP}"

run_command "python -m pytest tests/ --cov=app --cov-report=xml:${COVERAGE_FILE} --cov-report=html:${COVERAGE_HTML_DIR} --cov-report=term" "Generate coverage report"

# Check coverage threshold
if command -v coverage &> /dev/null; then
    COVERAGE_PERCENT=$(coverage report --show-missing | grep TOTAL | awk '{print $4}' | sed 's/%//')
    if [ "${COVERAGE_PERCENT}" -ge "${COVERAGE_MIN_THRESHOLD}" ]; then
        log "${GREEN}✓ Coverage ${COVERAGE_PERCENT}% meets threshold of ${COVERAGE_MIN_THRESHOLD}%${NC}"
    else
        log "${YELLOW}⚠ Coverage ${COVERAGE_PERCENT}% below threshold of ${COVERAGE_MIN_THRESHOLD}%${NC}"
    fi
else
    log "${YELLOW}⚠ Coverage tool not available${NC}"
fi

log "${BLUE}Step 10: Regression Test Suite${NC}"

# Run regression tests with different configurations
REGRESSION_CONFIGS=(
    "--tb=short"
    "--tb=long --maxfail=5"
    "-x --tb=short"  # Stop on first failure
)

for config in "${REGRESSION_CONFIGS[@]}"; do
    log "${YELLOW}Running regression tests with config: ${config}${NC}"
    if run_command "python -m pytest tests/test_basic.py tests/test_mock_integration.py ${config}" "Regression test (${config})"; then
        log "${GREEN}✓ Regression test passed with ${config}${NC}"
    else
        log "${RED}✗ Regression test failed with ${config}${NC}"
        break
    fi
done

log "${BLUE}Step 11: Test Summary and Cleanup${NC}"

# Count test results
TOTAL_TESTS=$(grep -E "passed|failed|error" "${LOG_FILE}" | wc -l || echo "0")
PASSED_TESTS=$(grep -c "SUCCESS:" "${LOG_FILE}" || echo "0")
FAILED_TESTS=$(grep -c "FAILED:" "${LOG_FILE}" || echo "0")

# Generate summary report
SUMMARY_FILE="${RESULTS_DIR}/test_summary_${TIMESTAMP}.txt"
cat > "${SUMMARY_FILE}" << EOF
LeanVibe Test Summary - ${TIMESTAMP}
====================================

Test Configuration:
- Project Root: ${PROJECT_ROOT}
- Timestamp: $(date)
- Coverage Threshold: ${COVERAGE_MIN_THRESHOLD}%

Test Results:
- Total Test Steps: ${TOTAL_TESTS}
- Passed: ${PASSED_TESTS}
- Failed: ${FAILED_TESTS}
- Success Rate: $(( PASSED_TESTS * 100 / (PASSED_TESTS + FAILED_TESTS + 1) ))%

Files Generated:
- Detailed Log: ${LOG_FILE}
- Coverage Report: ${COVERAGE_FILE}
- Coverage HTML: ${COVERAGE_HTML_DIR}
- Summary Report: ${SUMMARY_FILE}

Mock Infrastructure Status:
$(python -c "from tests.mocks import get_mock_status; import json; print(json.dumps(get_mock_status(), indent=2))" 2>/dev/null || echo "Mock status unavailable")

EOF

# Display final summary
log ""
log "${BLUE}=== Test Summary ===${NC}"
log "Test Steps Executed: ${TOTAL_TESTS}"
log "Successful Steps: ${GREEN}${PASSED_TESTS}${NC}"
log "Failed Steps: ${RED}${FAILED_TESTS}${NC}"

if [ "${FAILED_TESTS}" -eq 0 ]; then
    log "${GREEN}🎉 All tests completed successfully!${NC}"
    log "Summary report: ${SUMMARY_FILE}"
    log "Coverage report: ${COVERAGE_HTML_DIR}/index.html"
    exit 0
else
    log "${YELLOW}⚠ Some tests had issues. Check the detailed log: ${LOG_FILE}${NC}"
    log "Summary report: ${SUMMARY_FILE}"
    exit 1
fi