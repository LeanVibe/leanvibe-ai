#!/bin/bash

# Emergency Rollback Script
# Instantly rollback to previous stable version on health check failures
# Usage: ./rollback.sh <environment> [--emergency] [--to-version=<commit_sha>]

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENVIRONMENT="${1:-staging}"
EMERGENCY_MODE=false
TARGET_VERSION=""
ROLLBACK_TIMEOUT=${ROLLBACK_TIMEOUT:-60}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

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

log_emergency() {
    echo -e "${RED}${BOLD}[EMERGENCY]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
}

# Parse arguments
parse_arguments() {
    for arg in "$@"; do
        case $arg in
            --emergency)
                EMERGENCY_MODE=true
                ROLLBACK_TIMEOUT=15  # Faster rollback in emergency
                log_emergency "Emergency rollback mode activated"
                shift
                ;;
            --to-version=*)
                TARGET_VERSION="${arg#*=}"
                shift
                ;;
            *)
                # Unknown argument
                ;;
        esac
    done
}

# Validate inputs
validate_inputs() {
    log_info "Validating rollback inputs..."
    
    if [[ ! "$ENVIRONMENT" =~ ^(staging|production)$ ]]; then
        log_error "Invalid environment. Must be 'staging' or 'production'"
        exit 1
    fi
    
    if [[ -n "$TARGET_VERSION" ]] && [[ ! "$TARGET_VERSION" =~ ^[a-f0-9]{40}$ ]]; then
        log_error "Invalid target version format: $TARGET_VERSION"
        exit 1
    fi
    
    log_success "Input validation completed"
}

# Find last stable version
find_last_stable_version() {
    log_info "Finding last stable version for rollback..."
    
    local deployments_dir="$PROJECT_ROOT/deployment_reports"
    
    if [[ -n "$TARGET_VERSION" ]]; then
        log_info "Using specified target version: $TARGET_VERSION"
        echo "$TARGET_VERSION"
        return 0
    fi
    
    # Look for last successful deployment in the same environment
    if [[ -d "$deployments_dir" ]]; then
        local last_stable=$(find "$deployments_dir" -name "*_$ENVIRONMENT_*.json" \
            -exec grep -l '"status": "success"' {} \; \
            | sort -r | head -1)
        
        if [[ -n "$last_stable" ]]; then
            local commit_sha=$(jq -r '.commit_sha' "$last_stable")
            log_success "Found last stable version: $commit_sha"
            echo "$commit_sha"
            return 0
        fi
    fi
    
    # Fallback to Docker images
    local backup_image=$(docker images "leanvibe-backend" \
        --filter "label=environment=$ENVIRONMENT" \
        --format "{{.Tag}}" | grep -E '^[a-f0-9]{40}$' | head -1)
    
    if [[ -n "$backup_image" ]]; then
        log_success "Found backup image version: $backup_image"
        echo "$backup_image"
        return 0
    fi
    
    # Last resort: look for backup tag
    local backup_tag="leanvibe-backend:$ENVIRONMENT-backup-"
    backup_image=$(docker images --format "{{.Repository}}:{{.Tag}}" | grep "$backup_tag" | head -1)
    
    if [[ -n "$backup_image" ]]; then
        local version=$(echo "$backup_image" | sed "s/.*$backup_tag//")
        log_warning "Using emergency backup version: $version"
        echo "$backup_image"
        return 0
    fi
    
    log_error "No stable version found for rollback!"
    return 1
}

# Stop current deployment
stop_current_deployment() {
    log_info "Stopping current deployment..."
    
    # Stop the application containers immediately
    docker compose -f "$PROJECT_ROOT/docker-compose.$ENVIRONMENT.yml" \
        -p "leanvibe-$ENVIRONMENT" down --timeout 10 || true
    
    # Remove potentially problematic containers
    docker ps -a --filter "name=leanvibe-$ENVIRONMENT" -q | \
        xargs -r docker rm -f || true
    
    if [[ "$EMERGENCY_MODE" == "true" ]]; then
        # In emergency mode, kill all related processes
        log_emergency "Emergency shutdown - killing all leanvibe processes"
        pkill -f "leanvibe" || true
        pkill -f "uvicorn.*leanvibe" || true
    fi
    
    log_success "Current deployment stopped"
}

# Load balancer maintenance mode
enable_maintenance_mode() {
    log_info "Enabling maintenance mode..."
    
    if command -v nginx >/dev/null; then
        # Create maintenance page configuration
        cat > "/etc/nginx/sites-available/leanvibe-$ENVIRONMENT-maintenance" <<EOF
server {
    listen 80;
    server_name $([ "$ENVIRONMENT" = "production" ] && echo "leanvibe.ai" || echo "staging.leanvibe.ai");
    
    location / {
        return 503 'Service temporarily unavailable - maintenance in progress';
        add_header Content-Type text/plain;
    }
    
    location /health {
        return 200 'maintenance';
        add_header Content-Type text/plain;
    }
}
EOF
        
        # Enable maintenance mode
        ln -sf "/etc/nginx/sites-available/leanvibe-$ENVIRONMENT-maintenance" \
               "/etc/nginx/sites-enabled/leanvibe-$ENVIRONMENT"
        nginx -s reload || true
    fi
    
    log_success "Maintenance mode enabled"
}

# Rollback to stable version
rollback_to_stable() {
    local stable_version="$1"
    log_info "Rolling back to stable version: $stable_version"
    
    # Update environment variables for rollback
    export ROLLBACK_VERSION="$stable_version"
    export DEPLOYMENT_TYPE="rollback"
    
    # Start the stable version
    if [[ "$stable_version" =~ ^leanvibe-backend: ]]; then
        # It's a full image name
        export LEANVIBE_IMAGE="$stable_version"
    else
        # It's a commit SHA
        export LEANVIBE_IMAGE="leanvibe-backend:$stable_version"
    fi
    
    # Check if the image exists
    if ! docker images --format "{{.Repository}}:{{.Tag}}" | grep -q "$LEANVIBE_IMAGE"; then
        log_error "Rollback image not found: $LEANVIBE_IMAGE"
        
        if [[ "$EMERGENCY_MODE" == "true" ]]; then
            log_emergency "Attempting to pull image from registry..."
            docker pull "$DOCKER_REGISTRY/leanvibe-backend:$stable_version" || \
            docker tag "$DOCKER_REGISTRY/leanvibe-backend:$stable_version" "$LEANVIBE_IMAGE" || \
            log_error "Failed to pull rollback image from registry"
        else
            return 1
        fi
    fi
    
    # Deploy the stable version
    timeout "$ROLLBACK_TIMEOUT" docker compose \
        -f "$PROJECT_ROOT/docker-compose.$ENVIRONMENT.yml" \
        -p "leanvibe-$ENVIRONMENT" up -d --timeout 30
    
    log_success "Rollback deployment started"
}

# Wait for rollback to be ready
wait_for_rollback_ready() {
    log_info "Waiting for rollback to be ready..."
    
    local health_url="http://localhost:${APP_PORT:-8000}/health/ready"
    local retries=0
    local max_retries=$([ "$EMERGENCY_MODE" == "true" ] && echo 6 || echo 15)
    
    while [ $retries -lt $max_retries ]; do
        if curl -f -s --connect-timeout 5 "$health_url" >/dev/null 2>&1; then
            log_success "Rollback version is ready!"
            return 0
        fi
        
        log_info "Waiting for rollback... (attempt $((retries + 1))/$max_retries)"
        sleep $([ "$EMERGENCY_MODE" == "true" ] && echo 5 || echo 10)
        retries=$((retries + 1))
    done
    
    log_error "Rollback failed to become ready"
    return 1
}

# Verify rollback health
verify_rollback_health() {
    log_info "Verifying rollback health..."
    
    local base_url="http://localhost:${APP_PORT:-8000}"
    local checks_passed=0
    local total_checks=4
    
    # Basic health check
    if curl -f -s --connect-timeout 10 "$base_url/health/complete" | grep -q '"status":"healthy"'; then
        log_success "✓ Basic health check passed"
        checks_passed=$((checks_passed + 1))
    else
        log_error "✗ Basic health check failed"
    fi
    
    # Database connectivity (optional in emergency mode)
    if [[ "$EMERGENCY_MODE" != "true" ]]; then
        if curl -f -s --connect-timeout 10 "$base_url/health/database" | grep -q '"status":"healthy"'; then
            log_success "✓ Database health check passed"
            checks_passed=$((checks_passed + 1))
        else
            log_warning "✗ Database health check failed"
        fi
    else
        log_info "Skipping database check in emergency mode"
        checks_passed=$((checks_passed + 1))
    fi
    
    # Critical API endpoints
    if curl -f -s --connect-timeout 10 "$base_url/api/health" >/dev/null; then
        log_success "✓ API endpoints accessible"
        checks_passed=$((checks_passed + 1))
    else
        log_error "✗ API endpoints not accessible"
    fi
    
    # Memory usage check
    local memory_usage=$(docker stats --no-stream --format "{{.MemPerc}}" "leanvibe-$ENVIRONMENT-app-1" 2>/dev/null | sed 's/%//' || echo "0")
    if [[ "$memory_usage" =~ ^[0-9]+$ ]] && [ "$memory_usage" -lt 90 ]; then
        log_success "✓ Memory usage normal ($memory_usage%)"
        checks_passed=$((checks_passed + 1))
    else
        log_warning "✗ High memory usage or unable to check"
    fi
    
    local success_rate=$(( checks_passed * 100 / total_checks ))
    local min_success_rate=$([ "$EMERGENCY_MODE" == "true" ] && echo 50 || echo 75)
    
    if [ $success_rate -ge $min_success_rate ]; then
        log_success "Rollback verification passed ($success_rate% checks passed)"
        return 0
    else
        log_error "Rollback verification failed ($success_rate% checks passed, minimum: $min_success_rate%)"
        return 1
    fi
}

# Restore load balancer configuration
restore_load_balancer() {
    log_info "Restoring load balancer configuration..."
    
    if command -v nginx >/dev/null; then
        # Restore normal configuration
        if [[ -f "$PROJECT_ROOT/config/nginx-$ENVIRONMENT.template" ]]; then
            envsubst < "$PROJECT_ROOT/config/nginx-$ENVIRONMENT.template" > \
                "/etc/nginx/sites-available/leanvibe-$ENVIRONMENT"
        else
            # Fallback configuration
            cat > "/etc/nginx/sites-available/leanvibe-$ENVIRONMENT" <<EOF
upstream leanvibe_backend {
    server localhost:${APP_PORT:-8000} max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name $([ "$ENVIRONMENT" = "production" ] && echo "leanvibe.ai" || echo "staging.leanvibe.ai");
    
    location / {
        proxy_pass http://leanvibe_backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_connect_timeout 10s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
    
    location /health {
        proxy_pass http://leanvibe_backend/health;
        access_log off;
    }
}
EOF
        fi
        
        ln -sf "/etc/nginx/sites-available/leanvibe-$ENVIRONMENT" \
               "/etc/nginx/sites-enabled/leanvibe-$ENVIRONMENT"
        nginx -s reload || nginx -s restart
    fi
    
    log_success "Load balancer configuration restored"
}

# Generate rollback report
generate_rollback_report() {
    local stable_version="$1"
    local status="$2"
    
    log_info "Generating rollback report..."
    
    local report_file="$PROJECT_ROOT/deployment_reports/rollback_$ENVIRONMENT_$(date +%Y%m%d_%H%M%S).json"
    mkdir -p "$(dirname "$report_file")"
    
    cat > "$report_file" <<EOF
{
    "rollback_id": "$(uuidgen)",
    "environment": "$ENVIRONMENT",
    "rolled_back_to": "$stable_version",
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "emergency_mode": $EMERGENCY_MODE,
    "status": "$status",
    "duration_seconds": $SECONDS,
    "trigger": "$([ "$EMERGENCY_MODE" == "true" ] && echo "emergency" || echo "planned")",
    "health_verification": {
        "completed": true,
        "passed": $([ "$status" == "success" ] && echo "true" || echo "false")
    }
}
EOF
    
    log_success "Rollback report saved to $report_file"
}

# Send notifications
send_notifications() {
    local status="$1"
    local stable_version="$2"
    
    if [[ "$EMERGENCY_MODE" == "true" ]]; then
        log_emergency "ROLLBACK COMPLETED - STATUS: $status"
        log_emergency "Environment: $ENVIRONMENT"
        log_emergency "Rolled back to: $stable_version"
        
        # Send emergency notifications (Slack, PagerDuty, etc.)
        if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
            curl -X POST -H 'Content-type: application/json' \
                --data "{\"text\":\"🚨 EMERGENCY ROLLBACK: $ENVIRONMENT rolled back to $stable_version - Status: $status\"}" \
                "$SLACK_WEBHOOK_URL" || true
        fi
    else
        log_info "Rollback completed - Status: $status"
    fi
}

# Main execution
main() {
    local start_time=$(date +%s)
    
    if [[ "$EMERGENCY_MODE" == "true" ]]; then
        log_emergency "EMERGENCY ROLLBACK INITIATED for $ENVIRONMENT"
    else
        log_info "Starting rollback for $ENVIRONMENT"
    fi
    
    validate_inputs
    
    local stable_version
    if ! stable_version=$(find_last_stable_version); then
        log_error "Cannot proceed with rollback - no stable version found"
        exit 1
    fi
    
    enable_maintenance_mode
    stop_current_deployment
    rollback_to_stable "$stable_version"
    
    if wait_for_rollback_ready && verify_rollback_health; then
        restore_load_balancer
        generate_rollback_report "$stable_version" "success"
        send_notifications "SUCCESS" "$stable_version"
        
        local duration=$(($(date +%s) - start_time))
        log_success "Rollback completed successfully in ${duration}s! 🔄"
        log_info "Application restored at: https://$([ "$ENVIRONMENT" = "production" ] && echo "leanvibe.ai" || echo "staging.leanvibe.ai")"
        exit 0
    else
        generate_rollback_report "$stable_version" "failed"
        send_notifications "FAILED" "$stable_version"
        log_error "Rollback verification failed - manual intervention required!"
        exit 1
    fi
}

# Parse arguments and execute
parse_arguments "$@"
main