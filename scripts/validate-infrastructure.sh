#!/bin/bash

# LeanVibe Infrastructure Validation Script
# Comprehensive validation of CI/CD pipeline, security, and monitoring infrastructure

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 LeanVibe Infrastructure Validation${NC}"
echo "========================================="

# Global validation results
VALIDATION_RESULTS=()
VALIDATION_PASSED=0
VALIDATION_FAILED=0
VALIDATION_WARNINGS=0

# Function to log validation results
log_result() {
    local test_name="$1"
    local status="$2"
    local message="$3"
    
    case $status in
        "PASS")
            echo -e "${GREEN}✅ ${test_name}: PASSED${NC}"
            [[ -n "$message" ]] && echo -e "   ${message}"
            VALIDATION_RESULTS+=("✅ $test_name: PASSED")
            ((VALIDATION_PASSED++))
            ;;
        "FAIL")
            echo -e "${RED}❌ ${test_name}: FAILED${NC}"
            [[ -n "$message" ]] && echo -e "   ${message}"
            VALIDATION_RESULTS+=("❌ $test_name: FAILED - $message")
            ((VALIDATION_FAILED++))
            ;;
        "WARN")
            echo -e "${YELLOW}⚠️  ${test_name}: WARNING${NC}"
            [[ -n "$message" ]] && echo -e "   ${message}"
            VALIDATION_RESULTS+=("⚠️ $test_name: WARNING - $message")
            ((VALIDATION_WARNINGS++))
            ;;
    esac
}

# Function to validate GitHub Actions workflows
validate_github_actions() {
    echo -e "\n${BLUE}🔧 Validating GitHub Actions Workflows${NC}"
    
    # Check if workflows directory exists
    if [[ ! -d ".github/workflows" ]]; then
        log_result "GitHub Workflows Directory" "FAIL" "Directory .github/workflows not found"
        return
    fi
    
    # Validate CI/CD workflow
    if [[ -f ".github/workflows/ci-cd.yml" ]]; then
        # Check workflow syntax
        if yamllint .github/workflows/ci-cd.yml >/dev/null 2>&1; then
            log_result "CI/CD Workflow Syntax" "PASS"
        else
            log_result "CI/CD Workflow Syntax" "FAIL" "YAML syntax errors found"
        fi
        
        # Check for required jobs
        required_jobs=("backend-test" "cli-test" "ios-test" "security-scan" "code-quality" "build-and-push" "deploy-staging")
        for job in "${required_jobs[@]}"; do
            if grep -q "^ *${job}:" .github/workflows/ci-cd.yml; then
                log_result "CI/CD Job: $job" "PASS"
            else
                log_result "CI/CD Job: $job" "FAIL" "Job not found in workflow"
            fi
        done
    else
        log_result "CI/CD Workflow File" "FAIL" "File .github/workflows/ci-cd.yml not found"
    fi
    
    # Validate production deployment workflow
    if [[ -f ".github/workflows/deploy-production.yml" ]]; then
        if yamllint .github/workflows/deploy-production.yml >/dev/null 2>&1; then
            log_result "Production Deployment Workflow Syntax" "PASS"
        else
            log_result "Production Deployment Workflow Syntax" "FAIL" "YAML syntax errors found"
        fi
        
        # Check for blue/green deployment strategy
        if grep -q "canary" .github/workflows/deploy-production.yml; then
            log_result "Blue/Green Deployment Strategy" "PASS"
        else
            log_result "Blue/Green Deployment Strategy" "WARN" "Canary deployment not found"
        fi
    else
        log_result "Production Deployment Workflow" "FAIL" "File .github/workflows/deploy-production.yml not found"
    fi
    
    # Validate security audit workflow
    if [[ -f ".github/workflows/security-audit.yml" ]]; then
        if yamllint .github/workflows/security-audit.yml >/dev/null 2>&1; then
            log_result "Security Audit Workflow Syntax" "PASS"
        else
            log_result "Security Audit Workflow Syntax" "FAIL" "YAML syntax errors found"
        fi
        
        # Check for security tools
        security_tools=("bandit" "safety" "trivy" "semgrep")
        for tool in "${security_tools[@]}"; do
            if grep -q "$tool" .github/workflows/security-audit.yml; then
                log_result "Security Tool: $tool" "PASS"
            else
                log_result "Security Tool: $tool" "WARN" "Tool not found in security workflow"
            fi
        done
    else
        log_result "Security Audit Workflow" "FAIL" "File .github/workflows/security-audit.yml not found"
    fi
}

# Function to validate security infrastructure
validate_security() {
    echo -e "\n${BLUE}🔒 Validating Security Infrastructure${NC}"
    
    # Check SSL setup script
    if [[ -f "scripts/setup-ssl.sh" && -x "scripts/setup-ssl.sh" ]]; then
        log_result "SSL Setup Script" "PASS"
        
        # Check for cert-manager integration
        if grep -q "cert-manager" scripts/setup-ssl.sh; then
            log_result "Cert-Manager Integration" "PASS"
        else
            log_result "Cert-Manager Integration" "FAIL" "cert-manager not found in SSL setup"
        fi
        
        # Check for Let's Encrypt integration
        if grep -q "letsencrypt" scripts/setup-ssl.sh; then
            log_result "Let's Encrypt Integration" "PASS"
        else
            log_result "Let's Encrypt Integration" "FAIL" "Let's Encrypt not configured"
        fi
    else
        log_result "SSL Setup Script" "FAIL" "Script scripts/setup-ssl.sh not found or not executable"
    fi
    
    # Check secrets management script
    if [[ -f "scripts/setup-secrets.sh" && -x "scripts/setup-secrets.sh" ]]; then
        log_result "Secrets Management Script" "PASS"
        
        # Check for environment separation
        if grep -q "staging\|production" scripts/setup-secrets.sh; then
            log_result "Environment Separation" "PASS"
        else
            log_result "Environment Separation" "WARN" "Environment separation not clearly defined"
        fi
        
        # Check for secret rotation capability
        if grep -q "rotate" scripts/setup-secrets.sh; then
            log_result "Secret Rotation" "PASS"
        else
            log_result "Secret Rotation" "WARN" "Secret rotation not implemented"
        fi
    else
        log_result "Secrets Management Script" "FAIL" "Script scripts/setup-secrets.sh not found or not executable"
    fi
    
    # Check Docker security
    dockerfiles=$(find . -name "Dockerfile" -not -path "./.git/*")
    if [[ -n "$dockerfiles" ]]; then
        log_result "Docker Files Found" "PASS"
        
        for dockerfile in $dockerfiles; do
            # Check for non-root user
            if grep -q "USER " "$dockerfile"; then
                log_result "Docker Security: Non-root user in $(basename $(dirname $dockerfile))" "PASS"
            else
                log_result "Docker Security: Non-root user in $(basename $(dirname $dockerfile))" "WARN" "Consider running as non-root user"
            fi
            
            # Check for multi-stage build
            if grep -c "^FROM " "$dockerfile" | awk '$1 > 1 {exit 0} {exit 1}'; then
                log_result "Docker Security: Multi-stage build in $(basename $(dirname $dockerfile))" "PASS"
            else
                log_result "Docker Security: Multi-stage build in $(basename $(dirname $dockerfile))" "WARN" "Consider using multi-stage builds"
            fi
        done
    else
        log_result "Docker Files" "WARN" "No Dockerfiles found"
    fi
}

# Function to validate monitoring setup
validate_monitoring() {
    echo -e "\n${BLUE}📊 Validating Monitoring Infrastructure${NC}"
    
    # Check Prometheus configuration
    if [[ -f "leanvibe-backend/monitoring/prometheus.yml" ]]; then
        log_result "Prometheus Configuration" "PASS"
        
        # Check for required scrape configs
        scrape_configs=("leanvibe-backend" "postgres" "redis" "neo4j")
        for config in "${scrape_configs[@]}"; do
            if grep -q "$config" leanvibe-backend/monitoring/prometheus.yml; then
                log_result "Prometheus Scrape Config: $config" "PASS"
            else
                log_result "Prometheus Scrape Config: $config" "WARN" "Scrape config not found"
            fi
        done
    else
        log_result "Prometheus Configuration" "FAIL" "File leanvibe-backend/monitoring/prometheus.yml not found"
    fi
    
    # Check alerting rules
    if [[ -f "monitoring/alerts/production-alerts.yaml" ]]; then
        log_result "Production Alert Rules" "PASS"
        
        # Validate YAML syntax
        if yamllint monitoring/alerts/production-alerts.yaml >/dev/null 2>&1; then
            log_result "Alert Rules Syntax" "PASS"
        else
            log_result "Alert Rules Syntax" "FAIL" "YAML syntax errors in alert rules"
        fi
        
        # Check for critical alert types
        alert_types=("service-availability" "database-health" "resource-utilization" "security-monitoring")
        for alert_type in "${alert_types[@]}"; do
            if grep -q "$alert_type" monitoring/alerts/production-alerts.yaml; then
                log_result "Alert Group: $alert_type" "PASS"
            else
                log_result "Alert Group: $alert_type" "WARN" "Alert group not found"
            fi
        done
    else
        log_result "Production Alert Rules" "FAIL" "File monitoring/alerts/production-alerts.yaml not found"
    fi
    
    # Check Grafana dashboards
    if [[ -f "monitoring/grafana/dashboards/leanvibe-production-overview.json" ]]; then
        log_result "Grafana Production Dashboard" "PASS"
        
        # Validate JSON syntax
        if jq . monitoring/grafana/dashboards/leanvibe-production-overview.json >/dev/null 2>&1; then
            log_result "Dashboard JSON Syntax" "PASS"
        else
            log_result "Dashboard JSON Syntax" "FAIL" "JSON syntax errors in dashboard"
        fi
        
        # Check for essential panels
        essential_panels=("Service Status" "Request Rate" "Response Time" "Error Rate" "CPU Usage" "Memory Usage")
        for panel in "${essential_panels[@]}"; do
            if grep -q "$panel" monitoring/grafana/dashboards/leanvibe-production-overview.json; then
                log_result "Dashboard Panel: $panel" "PASS"
            else
                log_result "Dashboard Panel: $panel" "WARN" "Panel not found in dashboard"
            fi
        done
    else
        log_result "Grafana Production Dashboard" "FAIL" "File monitoring/grafana/dashboards/leanvibe-production-overview.json not found"
    fi
}

# Function to validate Docker and Kubernetes configurations
validate_container_orchestration() {
    echo -e "\n${BLUE}🐳 Validating Container Orchestration${NC}"
    
    # Check Docker Compose files
    compose_files=("docker-compose.yml" "leanvibe-backend/docker-compose.staging.yml" "leanvibe-backend/docker-compose.production.yml")
    for compose_file in "${compose_files[@]}"; do
        if [[ -f "$compose_file" ]]; then
            log_result "Docker Compose: $(basename $compose_file)" "PASS"
            
            # Validate syntax
            if docker-compose -f "$compose_file" config >/dev/null 2>&1; then
                log_result "Docker Compose Syntax: $(basename $compose_file)" "PASS"
            else
                log_result "Docker Compose Syntax: $(basename $compose_file)" "FAIL" "Syntax errors found"
            fi
        else
            log_result "Docker Compose: $(basename $compose_file)" "WARN" "File not found"
        fi
    done
    
    # Check Kubernetes manifests
    if [[ -d "leanvibe-backend/k8s" ]]; then
        log_result "Kubernetes Manifests Directory" "PASS"
        
        k8s_files=$(find leanvibe-backend/k8s -name "*.yaml" -o -name "*.yml")
        if [[ -n "$k8s_files" ]]; then
            for k8s_file in $k8s_files; do
                if kubectl --dry-run=client apply -f "$k8s_file" >/dev/null 2>&1; then
                    log_result "K8s Manifest: $(basename $k8s_file)" "PASS"
                else
                    log_result "K8s Manifest: $(basename $k8s_file)" "FAIL" "Validation failed"
                fi
            done
        else
            log_result "Kubernetes Manifests" "WARN" "No YAML files found in k8s directory"
        fi
    else
        log_result "Kubernetes Manifests Directory" "WARN" "Directory leanvibe-backend/k8s not found"
    fi
    
    # Check for health checks in containers
    dockerfile_dirs=("leanvibe-backend" "leanvibe-cli")
    for dir in "${dockerfile_dirs[@]}"; do
        if [[ -f "$dir/Dockerfile" ]]; then
            if grep -q "HEALTHCHECK" "$dir/Dockerfile"; then
                log_result "Docker Healthcheck: $dir" "PASS"
            else
                log_result "Docker Healthcheck: $dir" "WARN" "No HEALTHCHECK instruction found"
            fi
        fi
    done
}

# Function to validate deployment scripts
validate_deployment_scripts() {
    echo -e "\n${BLUE}🚀 Validating Deployment Scripts${NC}"
    
    # Check main deployment scripts
    deployment_scripts=("deploy-leanvibe.sh" "start_leanvibe.sh")
    for script in "${deployment_scripts[@]}"; do
        if [[ -f "$script" && -x "$script" ]]; then
            log_result "Deployment Script: $script" "PASS"
        elif [[ -f "$script" ]]; then
            log_result "Deployment Script: $script" "WARN" "Script exists but not executable"
        else
            log_result "Deployment Script: $script" "WARN" "Script not found"
        fi
    done
    
    # Check for environment-specific deployment scripts
    env_scripts=("leanvibe-backend/deploy/deploy_production.sh")
    for script in "${env_scripts[@]}"; do
        if [[ -f "$script" && -x "$script" ]]; then
            log_result "Environment Script: $(basename $script)" "PASS"
        else
            log_result "Environment Script: $(basename $script)" "WARN" "Script not found or not executable"
        fi
    done
    
    # Check for rollback capabilities
    if [[ -f "leanvibe-backend/deploy/rollback.sh" && -x "leanvibe-backend/deploy/rollback.sh" ]]; then
        log_result "Rollback Script" "PASS"
    else
        log_result "Rollback Script" "WARN" "Rollback script not found"
    fi
    
    # Check for canary deployment support
    if [[ -f "leanvibe-backend/deploy/canary.sh" && -x "leanvibe-backend/deploy/canary.sh" ]]; then
        log_result "Canary Deployment Script" "PASS"
    else
        log_result "Canary Deployment Script" "WARN" "Canary deployment script not found"
    fi
}

# Function to validate backup and disaster recovery
validate_backup_dr() {
    echo -e "\n${BLUE}💾 Validating Backup and Disaster Recovery${NC}"
    
    # Check for backup configurations
    if [[ -d "leanvibe-backend/k8s/backup" ]]; then
        log_result "Backup Configuration Directory" "PASS"
        
        backup_files=("cronjobs.yaml" "disaster-recovery.yaml")
        for backup_file in "${backup_files[@]}"; do
            if [[ -f "leanvibe-backend/k8s/backup/$backup_file" ]]; then
                log_result "Backup Config: $backup_file" "PASS"
            else
                log_result "Backup Config: $backup_file" "WARN" "File not found"
            fi
        done
    else
        log_result "Backup Configuration" "WARN" "Directory leanvibe-backend/k8s/backup not found"
    fi
    
    # Check for runbooks
    if [[ -d "leanvibe-backend/runbooks" ]]; then
        log_result "Runbooks Directory" "PASS"
        
        runbook_files=("deployment-procedures.md" "incident-response.md" "monitoring-playbook.md")
        for runbook in "${runbook_files[@]}"; do
            if [[ -f "leanvibe-backend/runbooks/$runbook" ]]; then
                log_result "Runbook: $runbook" "PASS"
            else
                log_result "Runbook: $runbook" "WARN" "File not found"
            fi
        done
    else
        log_result "Runbooks Directory" "WARN" "Directory leanvibe-backend/runbooks not found"
    fi
}

# Function to validate API health endpoints
validate_health_endpoints() {
    echo -e "\n${BLUE}🏥 Validating Health Endpoints${NC}"
    
    # Check if backend is running locally
    if curl -s http://localhost:8000/health >/dev/null 2>&1; then
        log_result "Basic Health Endpoint" "PASS"
        
        # Check detailed health endpoint
        if curl -s http://localhost:8000/production/health/detailed >/dev/null 2>&1; then
            log_result "Detailed Health Endpoint" "PASS"
        else
            log_result "Detailed Health Endpoint" "WARN" "Endpoint not accessible"
        fi
        
        # Check metrics endpoint
        if curl -s http://localhost:8000/production/metrics >/dev/null 2>&1; then
            log_result "Metrics Endpoint" "PASS"
        else
            log_result "Metrics Endpoint" "WARN" "Endpoint not accessible"
        fi
    else
        log_result "Health Endpoints" "WARN" "Backend not running locally - cannot test endpoints"
    fi
}

# Function to validate performance benchmarks
validate_performance() {
    echo -e "\n${BLUE}⚡ Validating Performance Configuration${NC}"
    
    # Check for performance configuration files
    perf_files=("leanvibe-backend/budgets/performance_sla.json" "leanvibe-backend/config/performance_sla.json")
    for perf_file in "${perf_files[@]}"; do
        if [[ -f "$perf_file" ]]; then
            log_result "Performance SLA Configuration" "PASS"
            
            # Validate JSON syntax
            if jq . "$perf_file" >/dev/null 2>&1; then
                log_result "Performance SLA JSON Syntax" "PASS"
            else
                log_result "Performance SLA JSON Syntax" "FAIL" "JSON syntax errors"
            fi
            break
        fi
    done
    
    # Check for load testing scripts
    if [[ -f "leanvibe-backend/test_production_load_stress.py" ]]; then
        log_result "Load Testing Script" "PASS"
    else
        log_result "Load Testing Script" "WARN" "Load testing script not found"
    fi
    
    # Check for performance monitoring
    if [[ -f "leanvibe-backend/test_performance_optimization.py" ]]; then
        log_result "Performance Monitoring Script" "PASS"
    else
        log_result "Performance Monitoring Script" "WARN" "Performance monitoring script not found"
    fi
}

# Function to run lightweight integration tests
run_integration_tests() {
    echo -e "\n${BLUE}🧪 Running Integration Tests${NC}"
    
    # Test GitHub Actions workflow validation
    if command -v act >/dev/null 2>&1; then
        if act --list >/dev/null 2>&1; then
            log_result "GitHub Actions Local Testing" "PASS" "act can list workflows"
        else
            log_result "GitHub Actions Local Testing" "WARN" "act command failed"
        fi
    else
        log_result "GitHub Actions Local Testing" "WARN" "act command not available"
    fi
    
    # Test Docker builds
    docker_dirs=("leanvibe-backend" "leanvibe-cli")
    for dir in "${docker_dirs[@]}"; do
        if [[ -f "$dir/Dockerfile" ]]; then
            echo "Testing Docker build for $dir..."
            if docker build --no-cache -f "$dir/Dockerfile" -t "leanvibe-$dir:test" "$dir" >/dev/null 2>&1; then
                log_result "Docker Build: $dir" "PASS"
                # Clean up test image
                docker rmi "leanvibe-$dir:test" >/dev/null 2>&1 || true
            else
                log_result "Docker Build: $dir" "FAIL" "Docker build failed"
            fi
        fi
    done
    
    # Test configuration files
    if [[ -f "docker-compose.yml" ]]; then
        if docker-compose config >/dev/null 2>&1; then
            log_result "Docker Compose Configuration Test" "PASS"
        else
            log_result "Docker Compose Configuration Test" "FAIL" "Configuration validation failed"
        fi
    fi
}

# Function to generate validation report
generate_report() {
    echo -e "\n${BLUE}📋 Validation Report Summary${NC}"
    echo "================================="
    
    echo -e "${GREEN}Passed: $VALIDATION_PASSED${NC}"
    echo -e "${YELLOW}Warnings: $VALIDATION_WARNINGS${NC}"
    echo -e "${RED}Failed: $VALIDATION_FAILED${NC}"
    echo ""
    
    # Calculate overall score
    total_tests=$((VALIDATION_PASSED + VALIDATION_WARNINGS + VALIDATION_FAILED))
    if [[ $total_tests -gt 0 ]]; then
        success_rate=$(( (VALIDATION_PASSED * 100) / total_tests ))
        echo -e "Overall Success Rate: ${success_rate}%"
    fi
    
    echo ""
    echo "Detailed Results:"
    echo "================="
    for result in "${VALIDATION_RESULTS[@]}"; do
        echo "$result"
    done
    
    # Create validation report file
    report_file="infrastructure-validation-$(date +%Y%m%d-%H%M%S).txt"
    {
        echo "LeanVibe Infrastructure Validation Report"
        echo "Generated: $(date)"
        echo "========================================"
        echo ""
        echo "Summary:"
        echo "Passed: $VALIDATION_PASSED"
        echo "Warnings: $VALIDATION_WARNINGS" 
        echo "Failed: $VALIDATION_FAILED"
        echo "Success Rate: ${success_rate}%"
        echo ""
        echo "Detailed Results:"
        for result in "${VALIDATION_RESULTS[@]}"; do
            echo "$result"
        done
        echo ""
        echo "Recommendations:"
        echo "==============="
        if [[ $VALIDATION_FAILED -gt 0 ]]; then
            echo "- Address all FAILED validations before production deployment"
        fi
        if [[ $VALIDATION_WARNINGS -gt 0 ]]; then
            echo "- Review WARNING items for potential improvements"
        fi
        echo "- Run this validation regularly to ensure infrastructure health"
        echo "- Update configurations as the system evolves"
    } > "$report_file"
    
    echo -e "\n${GREEN}✅ Validation report saved to: $report_file${NC}"
    
    # Return appropriate exit code
    if [[ $VALIDATION_FAILED -gt 0 ]]; then
        echo -e "\n${RED}❌ Validation FAILED - Critical issues found${NC}"
        return 1
    elif [[ $VALIDATION_WARNINGS -gt 0 ]]; then
        echo -e "\n${YELLOW}⚠️  Validation completed with WARNINGS${NC}"
        return 0
    else
        echo -e "\n${GREEN}✅ Validation PASSED - All checks successful${NC}"
        return 0
    fi
}

# Main validation function
main() {
    echo "Starting comprehensive infrastructure validation..."
    echo ""
    
    # Check dependencies
    dependencies=("yamllint" "jq" "docker" "docker-compose" "kubectl")
    for dep in "${dependencies[@]}"; do
        if ! command -v "$dep" >/dev/null 2>&1; then
            log_result "Dependency: $dep" "WARN" "Command not found - some validations may be skipped"
        else
            log_result "Dependency: $dep" "PASS"
        fi
    done
    
    # Run validation modules
    validate_github_actions
    validate_security
    validate_monitoring  
    validate_container_orchestration
    validate_deployment_scripts
    validate_backup_dr
    validate_health_endpoints
    validate_performance
    
    # Run integration tests if requested
    if [[ "${1:-}" == "--integration" ]]; then
        run_integration_tests
    fi
    
    # Generate final report
    generate_report
}

# Safety checks and execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    # Change to repository root
    cd "$(dirname "${BASH_SOURCE[0]}")/.."
    
    # Check if we're in the right directory
    if [[ ! -f "README.md" ]] || [[ ! -d ".github" ]]; then
        echo -e "${RED}❌ Script must be run from LeanVibe repository root${NC}"
        exit 1
    fi
    
    # Run main validation
    main "$@"
fi