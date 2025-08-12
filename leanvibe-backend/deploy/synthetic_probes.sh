#!/bin/bash

# Synthetic Probes Script
# Comprehensive health validation including API, WebSocket, and performance checks
# Usage: ./synthetic_probes.sh <environment> [--comprehensive] [--critical] [--timeout=<seconds>]

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENVIRONMENT="${1:-staging}"
COMPREHENSIVE_MODE=false
CRITICAL_MODE=false
PROBE_TIMEOUT=${PROBE_TIMEOUT:-30}
RETRY_COUNT=${RETRY_COUNT:-3}
RETRY_DELAY=${RETRY_DELAY:-10}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Probe results storage
declare -A PROBE_RESULTS
declare -A PROBE_METRICS
TOTAL_PROBES=0
PASSED_PROBES=0
FAILED_PROBES=0

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
}

log_critical() {
    echo -e "${RED}${BOLD}[CRITICAL]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
}

log_probe() {
    echo -e "${PURPLE}[PROBE]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
}

# Parse arguments
parse_arguments() {
    for arg in "$@"; do
        case $arg in
            --comprehensive)
                COMPREHENSIVE_MODE=true
                PROBE_TIMEOUT=60
                log_info "Comprehensive probe mode activated"
                shift
                ;;
            --critical)
                CRITICAL_MODE=true
                PROBE_TIMEOUT=120
                COMPREHENSIVE_MODE=true
                log_info "Critical probe mode activated (all checks)"
                shift
                ;;
            --timeout=*)
                PROBE_TIMEOUT="${arg#*=}"
                shift
                ;;
            *)
                # Unknown argument
                ;;
        esac
    done
}

# Environment configuration
load_environment_config() {
    case "$ENVIRONMENT" in
        staging)
            export BASE_URL="https://staging.leanvibe.ai"
            export WS_URL="wss://staging.leanvibe.ai/ws"
            export API_KEY="${STAGING_API_KEY:-test-api-key}"
            ;;
        production)
            export BASE_URL="https://leanvibe.ai"
            export WS_URL="wss://leanvibe.ai/ws"
            export API_KEY="${PROD_API_KEY:-}"
            if [[ -z "$API_KEY" ]]; then
                log_error "Production API key not set"
                exit 1
            fi
            ;;
        *)
            export BASE_URL="http://localhost:8765"
            export WS_URL="ws://localhost:8765/ws"
            export API_KEY="test-api-key"
            ;;
    esac
    
    log_info "Target URL: $BASE_URL"
}

# Record probe result
record_probe_result() {
    local probe_name="$1"
    local status="$2"
    local response_time="${3:-0}"
    local details="${4:-}"
    
    PROBE_RESULTS["$probe_name"]="$status"
    PROBE_METRICS["$probe_name"]="$response_time"
    TOTAL_PROBES=$((TOTAL_PROBES + 1))
    
    if [[ "$status" == "PASS" ]]; then
        PASSED_PROBES=$((PASSED_PROBES + 1))
        log_success "✓ $probe_name (${response_time}ms) $details"
    else
        FAILED_PROBES=$((FAILED_PROBES + 1))
        log_error "✗ $probe_name (${response_time}ms) $details"
    fi
}

# Generic HTTP probe with retries
http_probe() {
    local url="$1"
    local expected_status="${2:-200}"
    local probe_name="$3"
    local method="${4:-GET}"
    local data="${5:-}"
    
    log_probe "Testing $probe_name: $method $url"
    
    local attempt=1
    while [[ $attempt -le $RETRY_COUNT ]]; do
        local start_time=$(date +%s%3N)
        local status_code response_time
        
        if [[ -n "$data" ]]; then
            local response=$(curl -s -w "%{http_code}:%{time_total}" \
                --connect-timeout "$PROBE_TIMEOUT" \
                --max-time "$PROBE_TIMEOUT" \
                -X "$method" \
                -H "Content-Type: application/json" \
                -H "Authorization: Bearer $API_KEY" \
                -d "$data" \
                "$url" 2>/dev/null || echo "000:999")
        else
            local response=$(curl -s -w "%{http_code}:%{time_total}" \
                --connect-timeout "$PROBE_TIMEOUT" \
                --max-time "$PROBE_TIMEOUT" \
                -X "$method" \
                -H "Authorization: Bearer $API_KEY" \
                "$url" 2>/dev/null || echo "000:999")
        fi
        
        status_code=$(echo "$response" | tail -1 | cut -d':' -f1)
        response_time=$(echo "$response" | tail -1 | cut -d':' -f2 | cut -d'.' -f1)
        response_time=$((response_time * 1000))  # Convert to milliseconds
        
        if [[ "$status_code" -eq "$expected_status" ]]; then
            record_probe_result "$probe_name" "PASS" "$response_time"
            return 0
        fi
        
        log_warning "Attempt $attempt failed: HTTP $status_code (expected $expected_status)"
        attempt=$((attempt + 1))
        [[ $attempt -le $RETRY_COUNT ]] && sleep "$RETRY_DELAY"
    done
    
    record_probe_result "$probe_name" "FAIL" "$response_time" "HTTP $status_code"
    return 1
}

# Basic health checks
run_basic_health_checks() {
    log_info "Running basic health checks..."
    
    # Root endpoint
    http_probe "$BASE_URL/" 200 "Root Endpoint"
    
    # Health endpoint
    http_probe "$BASE_URL/health" 200 "Basic Health Check"
    
    # Complete health check
    http_probe "$BASE_URL/health/complete" 200 "Complete Health Check"
    
    # Ready endpoint
    http_probe "$BASE_URL/health/ready" 200 "Readiness Check"
}

# Database health checks
run_database_health_checks() {
    log_info "Running database health checks..."
    
    # Database health
    http_probe "$BASE_URL/health/database" 200 "Database Connectivity"
    
    # Redis health
    http_probe "$BASE_URL/health/redis" 200 "Redis Connectivity"
    
    if [[ "$COMPREHENSIVE_MODE" == "true" ]]; then
        # Database query performance
        local start_time=$(date +%s%3N)
        local response=$(curl -s -w "%{time_total}" \
            --connect-timeout "$PROBE_TIMEOUT" \
            -H "Authorization: Bearer $API_KEY" \
            "$BASE_URL/api/projects?limit=1" 2>/dev/null)
        local end_time=$(date +%s%3N)
        local query_time=$(((end_time - start_time)))
        
        if [[ $query_time -lt 2000 ]]; then
            record_probe_result "Database Query Performance" "PASS" "$query_time"
        else
            record_probe_result "Database Query Performance" "FAIL" "$query_time" "Slow query"
        fi
    fi
}

# API functionality checks
run_api_functionality_checks() {
    log_info "Running API functionality checks..."
    
    # API root
    http_probe "$BASE_URL/api/" 200 "API Root"
    
    # Projects endpoint
    http_probe "$BASE_URL/api/projects" 200 "Projects API"
    
    # Tasks endpoint
    http_probe "$BASE_URL/api/tasks" 200 "Tasks API"
    
    if [[ "$COMPREHENSIVE_MODE" == "true" ]]; then
        # Create test project
        local test_data='{"name":"probe-test-project","description":"Synthetic probe test"}'
        local create_response=$(curl -s -w "%{http_code}" \
            --connect-timeout "$PROBE_TIMEOUT" \
            -X POST \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer $API_KEY" \
            -d "$test_data" \
            "$BASE_URL/api/projects" 2>/dev/null || echo "000")
        
        if [[ "$create_response" == "201" ]]; then
            record_probe_result "Project Creation" "PASS" "0"
            
            # List projects to verify creation
            http_probe "$BASE_URL/api/projects?name=probe-test-project" 200 "Project Verification"
            
            # Cleanup test project (best effort)
            curl -s -X DELETE \
                -H "Authorization: Bearer $API_KEY" \
                "$BASE_URL/api/projects/probe-test-project" >/dev/null 2>&1 || true
        else
            record_probe_result "Project Creation" "FAIL" "0" "HTTP $create_response"
        fi
    fi
}

# WebSocket functionality checks
run_websocket_checks() {
    log_info "Running WebSocket functionality checks..."
    
    # WebSocket connection test using a simple Node.js or Python script
    local ws_test_script=$(mktemp)
    cat > "$ws_test_script" <<EOF
#!/usr/bin/env python3
import asyncio
import websockets
import json
import sys
import time

async def test_websocket():
    start_time = time.time() * 1000
    try:
        uri = "$WS_URL"
        async with websockets.connect(uri, timeout=30) as websocket:
            # Send test message
            test_message = {"type": "ping", "data": "probe"}
            await websocket.send(json.dumps(test_message))
            
            # Wait for response
            response = await asyncio.wait_for(websocket.recv(), timeout=10)
            end_time = time.time() * 1000
            
            if response:
                print(f"PASS:{int(end_time - start_time)}")
            else:
                print("FAIL:0")
    except Exception as e:
        end_time = time.time() * 1000
        print(f"FAIL:{int(end_time - start_time)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_websocket())
EOF
    
    chmod +x "$ws_test_script"
    
    local ws_result
    if ws_result=$(timeout "$PROBE_TIMEOUT" python3 "$ws_test_script" 2>/dev/null); then
        local status=$(echo "$ws_result" | cut -d':' -f1)
        local response_time=$(echo "$ws_result" | cut -d':' -f2)
        record_probe_result "WebSocket Connection" "$status" "$response_time"
    else
        record_probe_result "WebSocket Connection" "FAIL" "0" "Connection timeout"
    fi
    
    rm -f "$ws_test_script"
}

# AI service health checks
run_ai_service_checks() {
    log_info "Running AI service health checks..."
    
    # AI health endpoint
    http_probe "$BASE_URL/health/ai" 200 "AI Service Health"
    
    if [[ "$COMPREHENSIVE_MODE" == "true" ]]; then
        # AI inference test
        local ai_test_data='{"prompt":"Hello, test inference","max_tokens":10}'
        local start_time=$(date +%s%3N)
        
        local ai_response=$(curl -s -w "%{http_code}" \
            --connect-timeout 60 \
            -X POST \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer $API_KEY" \
            -d "$ai_test_data" \
            "$BASE_URL/api/ai/generate" 2>/dev/null || echo "000")
        
        local end_time=$(date +%s%3N)
        local inference_time=$(((end_time - start_time)))
        
        if [[ "$ai_response" =~ ^2[0-9]{2}$ ]]; then
            record_probe_result "AI Inference" "PASS" "$inference_time"
        else
            record_probe_result "AI Inference" "FAIL" "$inference_time" "HTTP $ai_response"
        fi
    fi
}

# Performance benchmarks
run_performance_benchmarks() {
    if [[ "$COMPREHENSIVE_MODE" != "true" ]]; then
        return 0
    fi
    
    log_info "Running performance benchmarks..."
    
    # Concurrent request test
    local concurrent_requests=10
    local temp_dir=$(mktemp -d)
    
    log_probe "Testing $concurrent_requests concurrent requests..."
    
    for i in $(seq 1 $concurrent_requests); do
        (
            local response_time=$(curl -s -w "%{time_total}" -o /dev/null \
                --connect-timeout 30 \
                -H "Authorization: Bearer $API_KEY" \
                "$BASE_URL/api/projects" 2>/dev/null || echo "999")
            echo "$response_time" > "$temp_dir/response_$i.txt"
        ) &
    done
    
    wait
    
    # Calculate average response time
    local total_time=0
    local successful_requests=0
    for file in "$temp_dir"/response_*.txt; do
        if [[ -f "$file" ]]; then
            local time_val=$(cat "$file")
            if [[ "$time_val" != "999" ]]; then
                total_time=$(echo "$total_time + ($time_val * 1000)" | bc -l)
                successful_requests=$((successful_requests + 1))
            fi
        fi
    done
    
    if [[ $successful_requests -gt 0 ]]; then
        local avg_time=$(echo "scale=0; $total_time / $successful_requests" | bc -l)
        if [[ $(echo "$avg_time < 3000" | bc -l) -eq 1 ]]; then
            record_probe_result "Concurrent Load ($concurrent_requests req)" "PASS" "${avg_time%.*}"
        else
            record_probe_result "Concurrent Load ($concurrent_requests req)" "FAIL" "${avg_time%.*}" "High latency"
        fi
    else
        record_probe_result "Concurrent Load ($concurrent_requests req)" "FAIL" "0" "All requests failed"
    fi
    
    rm -rf "$temp_dir"
}

# Security checks
run_security_checks() {
    if [[ "$COMPREHENSIVE_MODE" != "true" ]]; then
        return 0
    fi
    
    log_info "Running security checks..."
    
    # Test unauthorized access
    local unauth_response=$(curl -s -w "%{http_code}" -o /dev/null \
        --connect-timeout 30 \
        "$BASE_URL/api/projects" 2>/dev/null || echo "000")
    
    if [[ "$unauth_response" == "401" || "$unauth_response" == "403" ]]; then
        record_probe_result "Unauthorized Access Protection" "PASS" "0"
    else
        record_probe_result "Unauthorized Access Protection" "FAIL" "0" "HTTP $unauth_response"
    fi
    
    # Test HTTPS redirect (production only)
    if [[ "$ENVIRONMENT" == "production" ]]; then
        local http_url="${BASE_URL/https/http}"
        local redirect_response=$(curl -s -w "%{http_code}" -o /dev/null \
            --connect-timeout 30 \
            "$http_url/health" 2>/dev/null || echo "000")
        
        if [[ "$redirect_response" =~ ^3[0-9]{2}$ ]]; then
            record_probe_result "HTTPS Redirect" "PASS" "0"
        else
            record_probe_result "HTTPS Redirect" "FAIL" "0" "HTTP $redirect_response"
        fi
    fi
}

# Critical system checks
run_critical_checks() {
    if [[ "$CRITICAL_MODE" != "true" ]]; then
        return 0
    fi
    
    log_info "Running critical system checks..."
    
    # Memory usage check (if available)
    if command -v docker >/dev/null; then
        local memory_usage=$(docker stats --no-stream --format "{{.MemPerc}}" \
            "leanvibe-$ENVIRONMENT-app-1" 2>/dev/null | sed 's/%//' || echo "0")
        
        if [[ "$memory_usage" =~ ^[0-9]+$ ]]; then
            if [[ $memory_usage -lt 85 ]]; then
                record_probe_result "Memory Usage Check" "PASS" "0" "${memory_usage}%"
            else
                record_probe_result "Memory Usage Check" "FAIL" "0" "${memory_usage}% (high)"
            fi
        else
            record_probe_result "Memory Usage Check" "FAIL" "0" "Unable to check"
        fi
    fi
    
    # Disk space check (if available)
    local disk_usage=$(df -h / 2>/dev/null | awk 'NR==2{print $5}' | sed 's/%//' || echo "0")
    if [[ "$disk_usage" =~ ^[0-9]+$ ]]; then
        if [[ $disk_usage -lt 90 ]]; then
            record_probe_result "Disk Space Check" "PASS" "0" "${disk_usage}%"
        else
            record_probe_result "Disk Space Check" "FAIL" "0" "${disk_usage}% (high)"
        fi
    fi
    
    # Service uptime check
    if command -v docker >/dev/null; then
        local uptime_status=$(docker ps --filter "name=leanvibe-$ENVIRONMENT" \
            --format "{{.Status}}" 2>/dev/null | head -1)
        
        if [[ "$uptime_status" =~ ^Up ]]; then
            record_probe_result "Service Uptime" "PASS" "0" "$uptime_status"
        else
            record_probe_result "Service Uptime" "FAIL" "0" "$uptime_status"
        fi
    fi
}

# Generate probe report
generate_probe_report() {
    log_info "Generating probe report..."
    
    local success_rate=$(( PASSED_PROBES * 100 / TOTAL_PROBES ))
    local report_file="$PROJECT_ROOT/test_results/synthetic_probes_$ENVIRONMENT_$(date +%Y%m%d_%H%M%S).json"
    
    mkdir -p "$(dirname "$report_file")"
    
    # Create detailed report
    cat > "$report_file" <<EOF
{
    "probe_id": "$(uuidgen)",
    "environment": "$ENVIRONMENT",
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "comprehensive_mode": $COMPREHENSIVE_MODE,
    "critical_mode": $CRITICAL_MODE,
    "summary": {
        "total_probes": $TOTAL_PROBES,
        "passed_probes": $PASSED_PROBES,
        "failed_probes": $FAILED_PROBES,
        "success_rate": $success_rate
    },
    "results": {
EOF
    
    # Add individual probe results
    local first=true
    for probe in "${!PROBE_RESULTS[@]}"; do
        [[ "$first" != "true" ]] && echo "," >> "$report_file"
        echo "        \"$probe\": {" >> "$report_file"
        echo "            \"status\": \"${PROBE_RESULTS[$probe]}\"," >> "$report_file"
        echo "            \"response_time_ms\": ${PROBE_METRICS[$probe]}" >> "$report_file"
        echo -n "        }" >> "$report_file"
        first=false
    done
    
    cat >> "$report_file" <<EOF

    },
    "target_url": "$BASE_URL",
    "probe_timeout": $PROBE_TIMEOUT
}
EOF
    
    log_success "Probe report saved to $report_file"
}

# Display results summary
display_summary() {
    echo
    echo "=================================="
    echo "   SYNTHETIC PROBES SUMMARY"
    echo "=================================="
    echo "Environment: $ENVIRONMENT"
    echo "Target URL: $BASE_URL"
    echo "Mode: $([ "$CRITICAL_MODE" == "true" ] && echo "Critical" || ([ "$COMPREHENSIVE_MODE" == "true" ] && echo "Comprehensive" || echo "Basic"))"
    echo
    echo "Total Probes: $TOTAL_PROBES"
    echo -e "Passed: ${GREEN}$PASSED_PROBES${NC}"
    echo -e "Failed: ${RED}$FAILED_PROBES${NC}"
    echo -e "Success Rate: $([ $((PASSED_PROBES * 100 / TOTAL_PROBES)) -ge 90 ] && echo -e "${GREEN}" || echo -e "${RED}")$((PASSED_PROBES * 100 / TOTAL_PROBES))%${NC}"
    echo "=================================="
    
    # List failed probes
    if [[ $FAILED_PROBES -gt 0 ]]; then
        echo
        echo "Failed Probes:"
        for probe in "${!PROBE_RESULTS[@]}"; do
            if [[ "${PROBE_RESULTS[$probe]}" == "FAIL" ]]; then
                echo -e "  ${RED}✗ $probe${NC}"
            fi
        done
    fi
    
    echo
}

# Main execution
main() {
    log_info "Starting synthetic probes for $ENVIRONMENT"
    
    load_environment_config
    
    # Run probe suites
    run_basic_health_checks
    run_database_health_checks
    run_api_functionality_checks
    run_websocket_checks
    run_ai_service_checks
    run_performance_benchmarks
    run_security_checks
    run_critical_checks
    
    generate_probe_report
    display_summary
    
    # Exit with appropriate code
    local success_rate=$((PASSED_PROBES * 100 / TOTAL_PROBES))
    local min_success_rate=$([ "$CRITICAL_MODE" == "true" ] && echo 95 || echo 85)
    
    if [[ $success_rate -ge $min_success_rate ]]; then
        log_success "Synthetic probes completed successfully! ✅"
        exit 0
    else
        log_error "Synthetic probes failed! Success rate: $success_rate% (minimum: $min_success_rate%)"
        exit 1
    fi
}

# Parse arguments and execute
parse_arguments "$@"
main