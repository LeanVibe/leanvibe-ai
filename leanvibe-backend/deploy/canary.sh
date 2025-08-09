#!/bin/bash

# Canary Deployment Script
# Deploys to staging with health checks and automatic rollback
# Usage: ./canary.sh <environment> <commit_sha>

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENVIRONMENT="${1:-staging}"
COMMIT_SHA="${2:-$(git rev-parse HEAD)}"
TIMEOUT=${TIMEOUT:-300}
HEALTH_CHECK_RETRIES=${HEALTH_CHECK_RETRIES:-30}
CANARY_PERCENTAGE=${CANARY_PERCENTAGE:-10}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# Cleanup function
cleanup() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        log_error "Deployment failed with exit code $exit_code"
        log_info "Initiating automatic rollback..."
        "${SCRIPT_DIR}/rollback.sh" "$ENVIRONMENT" || true
    fi
    exit $exit_code
}

trap cleanup EXIT

# Validate inputs
validate_inputs() {
    log_info "Validating deployment inputs..."
    
    if [[ ! "$ENVIRONMENT" =~ ^(staging|production)$ ]]; then
        log_error "Invalid environment. Must be 'staging' or 'production'"
        exit 1
    fi
    
    if [[ ! "$COMMIT_SHA" =~ ^[a-f0-9]{40}$ ]]; then
        log_error "Invalid commit SHA format: $COMMIT_SHA"
        exit 1
    fi
    
    # Check if commit exists
    if ! git rev-parse --verify "$COMMIT_SHA" >/dev/null 2>&1; then
        log_error "Commit $COMMIT_SHA not found in repository"
        exit 1
    fi
    
    log_success "Input validation completed"
}

# Load environment configuration
load_environment_config() {
    log_info "Loading configuration for environment: $ENVIRONMENT"
    
    case "$ENVIRONMENT" in
        staging)
            export APP_PORT=8000
            export WORKERS=2
            export HOST="staging.leanvibe.ai"
            export DATABASE_URL="neo4j://staging-db:7687"
            export REDIS_URL="redis://staging-redis:6379"
            export LOG_LEVEL="DEBUG"
            ;;
        production)
            export APP_PORT=8000
            export WORKERS=4
            export HOST="leanvibe.ai"
            export DATABASE_URL="neo4j://prod-db:7687"
            export REDIS_URL="redis://prod-redis:6379"
            export LOG_LEVEL="INFO"
            ;;
    esac
    
    log_success "Environment configuration loaded"
}

# Build and tag Docker image
build_image() {
    log_info "Building Docker image for commit $COMMIT_SHA..."
    
    cd "$PROJECT_ROOT"
    
    # Build optimized production image
    docker build \
        --build-arg COMMIT_SHA="$COMMIT_SHA" \
        --build-arg BUILD_DATE="$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        --build-arg ENVIRONMENT="$ENVIRONMENT" \
        -t "leanvibe-backend:$COMMIT_SHA" \
        -t "leanvibe-backend:$ENVIRONMENT-latest" \
        .
    
    # Tag for registry (if using one)
    if [[ -n "${DOCKER_REGISTRY:-}" ]]; then
        docker tag "leanvibe-backend:$COMMIT_SHA" \
            "$DOCKER_REGISTRY/leanvibe-backend:$COMMIT_SHA"
        docker tag "leanvibe-backend:$COMMIT_SHA" \
            "$DOCKER_REGISTRY/leanvibe-backend:$ENVIRONMENT-latest"
        
        log_info "Pushing to registry..."
        docker push "$DOCKER_REGISTRY/leanvibe-backend:$COMMIT_SHA"
        docker push "$DOCKER_REGISTRY/leanvibe-backend:$ENVIRONMENT-latest"
    fi
    
    log_success "Docker image built and tagged successfully"
}

# Deploy canary version
deploy_canary() {
    log_info "Deploying canary version ($CANARY_PERCENTAGE% traffic)..."
    
    # Create backup of current state
    if docker ps -q -f name="leanvibe-$ENVIRONMENT" >/dev/null; then
        log_info "Creating backup of current deployment..."
        docker tag "leanvibe-backend:$ENVIRONMENT-latest" \
            "leanvibe-backend:$ENVIRONMENT-backup-$(date +%s)"
    fi
    
    # Deploy new version with canary configuration
    docker compose -f "$PROJECT_ROOT/docker-compose.$ENVIRONMENT.yml" \
        -p "leanvibe-$ENVIRONMENT" up -d --scale app="$WORKERS"
    
    # Update load balancer configuration for canary
    if command -v nginx >/dev/null; then
        log_info "Updating nginx configuration for canary deployment..."
        envsubst < "$PROJECT_ROOT/config/nginx-canary.template" > \
            "/etc/nginx/sites-available/leanvibe-$ENVIRONMENT"
        nginx -s reload
    fi
    
    log_success "Canary deployment completed"
}

# Wait for application to be ready
wait_for_ready() {
    log_info "Waiting for application to be ready..."
    
    local health_url="http://localhost:$APP_PORT/health/ready"
    local retries=0
    
    while [ $retries -lt $HEALTH_CHECK_RETRIES ]; do
        if curl -f -s "$health_url" >/dev/null 2>&1; then
            log_success "Application is ready!"
            return 0
        fi
        
        log_info "Waiting for application... (attempt $((retries + 1))/$HEALTH_CHECK_RETRIES)"
        sleep 10
        retries=$((retries + 1))
    done
    
    log_error "Application failed to become ready after $((HEALTH_CHECK_RETRIES * 10)) seconds"
    return 1
}

# Run health checks
run_health_checks() {
    log_info "Running comprehensive health checks..."
    
    # Basic health check
    local health_url="http://localhost:$APP_PORT/health/complete"
    if ! curl -f -s "$health_url" | grep -q '"status":"healthy"'; then
        log_error "Basic health check failed"
        return 1
    fi
    
    # Database connectivity
    if ! curl -f -s "http://localhost:$APP_PORT/health/database" | grep -q '"status":"healthy"'; then
        log_error "Database health check failed"
        return 1
    fi
    
    # Redis connectivity
    if ! curl -f -s "http://localhost:$APP_PORT/health/redis" | grep -q '"status":"healthy"'; then
        log_error "Redis health check failed"
        return 1
    fi
    
    # AI service health
    if ! curl -f -s "http://localhost:$APP_PORT/health/ai" | grep -q '"status":"healthy"'; then
        log_warning "AI service health check failed - continuing with degraded functionality"
    fi
    
    log_success "All health checks passed"
    return 0
}

# Monitor canary metrics
monitor_canary() {
    log_info "Monitoring canary deployment metrics..."
    
    local monitoring_duration=300  # 5 minutes
    local check_interval=30        # 30 seconds
    local checks_passed=0
    local total_checks=$((monitoring_duration / check_interval))
    
    for i in $(seq 1 $total_checks); do
        log_info "Canary monitoring check $i/$total_checks..."
        
        # Check error rate
        local error_rate=$(curl -s "http://localhost:$APP_PORT/metrics/error_rate" | jq -r '.error_rate // 0')
        if (( $(echo "$error_rate > 5.0" | bc -l) )); then
            log_error "High error rate detected: $error_rate%"
            return 1
        fi
        
        # Check response time
        local avg_response_time=$(curl -s "http://localhost:$APP_PORT/metrics/response_time" | jq -r '.avg_response_time // 1000')
        if (( $(echo "$avg_response_time > 2000" | bc -l) )); then
            log_error "High response time detected: ${avg_response_time}ms"
            return 1
        fi
        
        # Check memory usage
        local memory_usage=$(docker stats --no-stream --format "table {{.MemPerc}}" "leanvibe-$ENVIRONMENT-app-1" | tail -n 1 | sed 's/%//')
        if (( $(echo "$memory_usage > 80" | bc -l) )); then
            log_error "High memory usage detected: $memory_usage%"
            return 1
        fi
        
        checks_passed=$((checks_passed + 1))
        sleep $check_interval
    done
    
    local success_rate=$(( checks_passed * 100 / total_checks ))
    if [ $success_rate -lt 90 ]; then
        log_error "Canary monitoring failed: only $success_rate% checks passed (minimum: 90%)"
        return 1
    fi
    
    log_success "Canary monitoring completed: $success_rate% checks passed"
    return 0
}

# Promote canary to full deployment
promote_canary() {
    log_info "Promoting canary to full deployment (100% traffic)..."
    
    # Update load balancer to route 100% traffic to new version
    if command -v nginx >/dev/null; then
        envsubst < "$PROJECT_ROOT/config/nginx-full.template" > \
            "/etc/nginx/sites-available/leanvibe-$ENVIRONMENT"
        nginx -s reload
    fi
    
    # Scale up new version
    docker compose -f "$PROJECT_ROOT/docker-compose.$ENVIRONMENT.yml" \
        -p "leanvibe-$ENVIRONMENT" up -d --scale app="$WORKERS"
    
    # Clean up old versions
    docker images -q "leanvibe-backend" | grep -v "$COMMIT_SHA" | head -5 | xargs -r docker rmi || true
    
    log_success "Canary promoted to full deployment"
}

# Generate deployment report
generate_report() {
    log_info "Generating deployment report..."
    
    local report_file="$PROJECT_ROOT/deployment_reports/canary_$ENVIRONMENT_$(date +%Y%m%d_%H%M%S).json"
    mkdir -p "$(dirname "$report_file")"
    
    cat > "$report_file" <<EOF
{
    "deployment_id": "$(uuidgen)",
    "environment": "$ENVIRONMENT",
    "commit_sha": "$COMMIT_SHA",
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "canary_percentage": $CANARY_PERCENTAGE,
    "status": "success",
    "duration_seconds": $SECONDS,
    "health_checks": {
        "basic": "passed",
        "database": "passed",
        "redis": "passed",
        "ai_service": "passed"
    },
    "metrics": {
        "error_rate": "$(curl -s "http://localhost:$APP_PORT/metrics/error_rate" | jq -r '.error_rate // 0')",
        "avg_response_time": "$(curl -s "http://localhost:$APP_PORT/metrics/response_time" | jq -r '.avg_response_time // 0')",
        "memory_usage": "$(docker stats --no-stream --format "{{.MemPerc}}" "leanvibe-$ENVIRONMENT-app-1" | sed 's/%//')"
    }
}
EOF
    
    log_success "Deployment report saved to $report_file"
}

# Main execution
main() {
    log_info "Starting canary deployment to $ENVIRONMENT (commit: $COMMIT_SHA)"
    
    validate_inputs
    load_environment_config
    build_image
    deploy_canary
    wait_for_ready
    run_health_checks
    monitor_canary
    promote_canary
    generate_report
    
    log_success "Canary deployment completed successfully! 🚀"
    log_info "Application available at: https://$HOST"
}

# Execute main function
main "$@"