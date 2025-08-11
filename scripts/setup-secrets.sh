#!/bin/bash

# LeanVibe Production Secrets Management Setup
# This script helps configure environment secrets for different deployment stages

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENTS=("development" "staging" "production")
VAULT_NAMESPACE="leanvibe"

echo -e "${BLUE}🔐 LeanVibe Secrets Management Setup${NC}"
echo "================================================"

# Function to generate secure random secrets
generate_secret() {
    openssl rand -hex 32
}

# Function to generate JWT secrets
generate_jwt_secret() {
    openssl rand -base64 64
}

# Function to create Kubernetes secrets
create_k8s_secrets() {
    local env=$1
    local namespace="leanvibe-${env}"
    
    echo -e "${YELLOW}Creating Kubernetes secrets for ${env}...${NC}"
    
    # Create namespace if it doesn't exist
    kubectl create namespace ${namespace} --dry-run=client -o yaml | kubectl apply -f -
    
    # Database secrets
    kubectl create secret generic leanvibe-database \
        --from-literal=host="${DB_HOST}" \
        --from-literal=port="${DB_PORT}" \
        --from-literal=database="${DB_NAME}" \
        --from-literal=username="${DB_USER}" \
        --from-literal=password="${DB_PASSWORD}" \
        --from-literal=url="postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}" \
        --namespace=${namespace} \
        --dry-run=client -o yaml | kubectl apply -f -
    
    # Application secrets
    kubectl create secret generic leanvibe-app \
        --from-literal=secret-key="${SECRET_KEY}" \
        --from-literal=jwt-secret="${JWT_SECRET}" \
        --from-literal=encryption-key="${ENCRYPTION_KEY}" \
        --from-literal=api-key="${API_KEY}" \
        --namespace=${namespace} \
        --dry-run=client -o yaml | kubectl apply -f -
    
    # External service secrets
    kubectl create secret generic leanvibe-external \
        --from-literal=redis-url="${REDIS_URL}" \
        --from-literal=neo4j-url="${NEO4J_URL}" \
        --from-literal=neo4j-user="${NEO4J_USER}" \
        --from-literal=neo4j-password="${NEO4J_PASSWORD}" \
        --from-literal=ollama-url="${OLLAMA_URL}" \
        --namespace=${namespace} \
        --dry-run=client -o yaml | kubectl apply -f -
    
    # Monitoring secrets
    if [[ "$env" == "production" || "$env" == "staging" ]]; then
        kubectl create secret generic leanvibe-monitoring \
            --from-literal=prometheus-user="${PROMETHEUS_USER}" \
            --from-literal=prometheus-password="${PROMETHEUS_PASSWORD}" \
            --from-literal=grafana-admin-user="${GRAFANA_ADMIN_USER}" \
            --from-literal=grafana-admin-password="${GRAFANA_ADMIN_PASSWORD}" \
            --namespace=${namespace} \
            --dry-run=client -o yaml | kubectl apply -f -
    fi
    
    # SSL/TLS certificates
    if [[ "$env" == "production" || "$env" == "staging" ]]; then
        if [[ -f "certs/${env}/tls.crt" && -f "certs/${env}/tls.key" ]]; then
            kubectl create secret tls leanvibe-tls \
                --cert="certs/${env}/tls.crt" \
                --key="certs/${env}/tls.key" \
                --namespace=${namespace} \
                --dry-run=client -o yaml | kubectl apply -f -
            echo -e "${GREEN}✅ SSL certificates configured for ${env}${NC}"
        else
            echo -e "${YELLOW}⚠️  SSL certificates not found for ${env}. Run setup-ssl.sh first.${NC}"
        fi
    fi
    
    echo -e "${GREEN}✅ Kubernetes secrets created for ${env}${NC}"
}

# Function to setup environment variables
setup_env_vars() {
    local env=$1
    
    echo -e "${YELLOW}Setting up environment variables for ${env}...${NC}"
    
    case $env in
        "development")
            DB_HOST="localhost"
            DB_PORT="5432"
            DB_NAME="leanvibe_dev"
            DB_USER="leanvibe_user"
            DB_PASSWORD=$(generate_secret)
            REDIS_URL="redis://localhost:6379/0"
            NEO4J_URL="neo4j://localhost:7687"
            NEO4J_USER="neo4j"
            NEO4J_PASSWORD=$(generate_secret)
            OLLAMA_URL="http://localhost:11434"
            ;;
        "staging")
            DB_HOST="postgres-staging.leanvibe.internal"
            DB_PORT="5432"
            DB_NAME="leanvibe_staging"
            DB_USER="leanvibe_staging_user"
            DB_PASSWORD=$(generate_secret)
            REDIS_URL="redis://redis-staging.leanvibe.internal:6379/0"
            NEO4J_URL="neo4j://neo4j-staging.leanvibe.internal:7687"
            NEO4J_USER="neo4j"
            NEO4J_PASSWORD=$(generate_secret)
            OLLAMA_URL="http://ollama-staging.leanvibe.internal:11434"
            PROMETHEUS_USER="prometheus"
            PROMETHEUS_PASSWORD=$(generate_secret)
            GRAFANA_ADMIN_USER="admin"
            GRAFANA_ADMIN_PASSWORD=$(generate_secret)
            ;;
        "production")
            DB_HOST="postgres-production.leanvibe.internal"
            DB_PORT="5432"
            DB_NAME="leanvibe_production"
            DB_USER="leanvibe_prod_user"
            DB_PASSWORD=$(generate_secret)
            REDIS_URL="redis://redis-production.leanvibe.internal:6379/0"
            NEO4J_URL="neo4j://neo4j-production.leanvibe.internal:7687"
            NEO4J_USER="neo4j"
            NEO4J_PASSWORD=$(generate_secret)
            OLLAMA_URL="http://ollama-production.leanvibe.internal:11434"
            PROMETHEUS_USER="prometheus"
            PROMETHEUS_PASSWORD=$(generate_secret)
            GRAFANA_ADMIN_USER="admin"
            GRAFANA_ADMIN_PASSWORD=$(generate_secret)
            ;;
    esac
    
    # Common secrets for all environments
    SECRET_KEY=$(generate_secret)
    JWT_SECRET=$(generate_jwt_secret)
    ENCRYPTION_KEY=$(generate_secret)
    API_KEY=$(generate_secret)
    
    # Create .env file for local development
    if [[ "$env" == "development" ]]; then
        cat > .env.${env} << EOF
# LeanVibe ${env^} Environment Configuration
# Generated: $(date)
# WARNING: Keep this file secure and never commit to version control

# Environment
LEANVIBE_ENV=${env}
LOG_LEVEL=DEBUG

# Security
LEANVIBE_SECRET_KEY=${SECRET_KEY}
LEANVIBE_JWT_SECRET=${JWT_SECRET}
LEANVIBE_ENCRYPTION_KEY=${ENCRYPTION_KEY}
LEANVIBE_API_KEY=${API_KEY}

# Database
LEANVIBE_DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}
DB_HOST=${DB_HOST}
DB_PORT=${DB_PORT}
DB_NAME=${DB_NAME}
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASSWORD}

# Redis
LEANVIBE_REDIS_URL=${REDIS_URL}

# Neo4j Graph Database
NEO4J_URL=${NEO4J_URL}
NEO4J_USER=${NEO4J_USER}
NEO4J_PASSWORD=${NEO4J_PASSWORD}

# AI Services
OLLAMA_URL=${OLLAMA_URL}
LEANVIBE_MLX_STRATEGY=REAL

# Server Configuration
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
EOF
        
        echo -e "${GREEN}✅ Environment file created: .env.${env}${NC}"
        echo -e "${YELLOW}⚠️  Remember to source this file or copy to .env for local development${NC}"
    fi
}

# Function to encrypt secrets for GitHub
encrypt_for_github() {
    local env=$1
    
    echo -e "${YELLOW}Preparing GitHub secrets for ${env}...${NC}"
    
    # Install GitHub CLI if not available
    if ! command -v gh &> /dev/null; then
        echo -e "${RED}❌ GitHub CLI (gh) not found. Please install it first.${NC}"
        return 1
    fi
    
    # Set secrets in GitHub repository
    case $env in
        "staging")
            echo "${KUBECONFIG_STAGING_B64}" | gh secret set STAGING_KUBECONFIG --env staging
            echo "${DB_PASSWORD}" | gh secret set STAGING_DB_PASSWORD --env staging
            echo "${SECRET_KEY}" | gh secret set STAGING_SECRET_KEY --env staging
            echo "${JWT_SECRET}" | gh secret set STAGING_JWT_SECRET --env staging
            echo "${NEO4J_PASSWORD}" | gh secret set STAGING_NEO4J_PASSWORD --env staging
            echo "${PROMETHEUS_PASSWORD}" | gh secret set STAGING_PROMETHEUS_PASSWORD --env staging
            echo "${GRAFANA_ADMIN_PASSWORD}" | gh secret set STAGING_GRAFANA_PASSWORD --env staging
            ;;
        "production")
            echo "${KUBECONFIG_PRODUCTION_B64}" | gh secret set PRODUCTION_KUBECONFIG --env production
            echo "${DB_PASSWORD}" | gh secret set PRODUCTION_DB_PASSWORD --env production
            echo "${SECRET_KEY}" | gh secret set PRODUCTION_SECRET_KEY --env production
            echo "${JWT_SECRET}" | gh secret set PRODUCTION_JWT_SECRET --env production
            echo "${NEO4J_PASSWORD}" | gh secret set PRODUCTION_NEO4J_PASSWORD --env production
            echo "${PROMETHEUS_PASSWORD}" | gh secret set PRODUCTION_PROMETHEUS_PASSWORD --env production
            echo "${GRAFANA_ADMIN_PASSWORD}" | gh secret set PRODUCTION_GRAFANA_PASSWORD --env production
            ;;
    esac
    
    # Common secrets
    echo "${SLACK_WEBHOOK_URL:-}" | gh secret set SLACK_WEBHOOK_URL || echo "Slack webhook not configured"
    echo "${DOCKER_REGISTRY_TOKEN:-$GITHUB_TOKEN}" | gh secret set DOCKER_REGISTRY_TOKEN || echo "Using GITHUB_TOKEN for registry"
    
    echo -e "${GREEN}✅ GitHub secrets configured for ${env}${NC}"
}

# Function to setup HashiCorp Vault (optional)
setup_vault() {
    echo -e "${YELLOW}Setting up HashiCorp Vault integration...${NC}"
    
    if ! command -v vault &> /dev/null; then
        echo -e "${YELLOW}⚠️  HashiCorp Vault CLI not found. Skipping Vault setup.${NC}"
        return 0
    fi
    
    # Enable KV secrets engine
    vault secrets enable -path=leanvibe kv-v2 2>/dev/null || true
    
    # Store secrets in Vault
    for env in "${ENVIRONMENTS[@]}"; do
        setup_env_vars "$env"
        
        vault kv put leanvibe/${env}/database \
            host="${DB_HOST}" \
            port="${DB_PORT}" \
            database="${DB_NAME}" \
            username="${DB_USER}" \
            password="${DB_PASSWORD}" \
            url="postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"
        
        vault kv put leanvibe/${env}/application \
            secret_key="${SECRET_KEY}" \
            jwt_secret="${JWT_SECRET}" \
            encryption_key="${ENCRYPTION_KEY}" \
            api_key="${API_KEY}"
        
        vault kv put leanvibe/${env}/external \
            redis_url="${REDIS_URL}" \
            neo4j_url="${NEO4J_URL}" \
            neo4j_user="${NEO4J_USER}" \
            neo4j_password="${NEO4J_PASSWORD}" \
            ollama_url="${OLLAMA_URL}"
        
        if [[ "$env" != "development" ]]; then
            vault kv put leanvibe/${env}/monitoring \
                prometheus_user="${PROMETHEUS_USER}" \
                prometheus_password="${PROMETHEUS_PASSWORD}" \
                grafana_admin_user="${GRAFANA_ADMIN_USER}" \
                grafana_admin_password="${GRAFANA_ADMIN_PASSWORD}"
        fi
    done
    
    echo -e "${GREEN}✅ Secrets stored in HashiCorp Vault${NC}"
}

# Function to rotate secrets
rotate_secrets() {
    local env=$1
    
    echo -e "${YELLOW}Rotating secrets for ${env}...${NC}"
    
    # Generate new secrets
    setup_env_vars "$env"
    
    # Update Kubernetes secrets
    create_k8s_secrets "$env"
    
    # Update GitHub secrets
    if [[ "$env" != "development" ]]; then
        encrypt_for_github "$env"
    fi
    
    # Update Vault secrets
    if command -v vault &> /dev/null; then
        setup_vault
    fi
    
    echo -e "${GREEN}✅ Secrets rotated for ${env}${NC}"
    echo -e "${YELLOW}⚠️  Don't forget to restart applications to pick up new secrets${NC}"
}

# Function to validate secrets
validate_secrets() {
    local env=$1
    local namespace="leanvibe-${env}"
    
    echo -e "${YELLOW}Validating secrets for ${env}...${NC}"
    
    # Check Kubernetes secrets exist
    secrets=(
        "leanvibe-database"
        "leanvibe-app"
        "leanvibe-external"
    )
    
    if [[ "$env" != "development" ]]; then
        secrets+=("leanvibe-monitoring")
        secrets+=("leanvibe-tls")
    fi
    
    for secret in "${secrets[@]}"; do
        if kubectl get secret "$secret" --namespace="$namespace" >/dev/null 2>&1; then
            echo -e "${GREEN}✅ Secret $secret exists${NC}"
        else
            echo -e "${RED}❌ Secret $secret missing${NC}"
        fi
    done
    
    # Test database connection
    echo "Testing database connectivity..."
    DB_URL=$(kubectl get secret leanvibe-database --namespace="$namespace" -o jsonpath='{.data.url}' | base64 -d)
    if psql "$DB_URL" -c "SELECT 1;" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Database connection successful${NC}"
    else
        echo -e "${RED}❌ Database connection failed${NC}"
    fi
}

# Main menu
show_menu() {
    echo ""
    echo "Select an option:"
    echo "1) Setup all environments"
    echo "2) Setup development environment"
    echo "3) Setup staging environment"
    echo "4) Setup production environment"
    echo "5) Rotate secrets for environment"
    echo "6) Validate secrets for environment"
    echo "7) Setup HashiCorp Vault"
    echo "8) Exit"
    echo ""
}

# Main execution
main() {
    if [[ $# -eq 0 ]]; then
        # Interactive mode
        while true; do
            show_menu
            read -p "Enter choice [1-8]: " choice
            
            case $choice in
                1)
                    for env in "${ENVIRONMENTS[@]}"; do
                        echo -e "${BLUE}Setting up ${env} environment...${NC}"
                        setup_env_vars "$env"
                        if [[ "$env" != "development" ]]; then
                            create_k8s_secrets "$env"
                            encrypt_for_github "$env"
                        fi
                    done
                    ;;
                2)
                    setup_env_vars "development"
                    ;;
                3)
                    setup_env_vars "staging"
                    create_k8s_secrets "staging"
                    encrypt_for_github "staging"
                    ;;
                4)
                    setup_env_vars "production"
                    create_k8s_secrets "production"
                    encrypt_for_github "production"
                    ;;
                5)
                    echo "Available environments: ${ENVIRONMENTS[*]}"
                    read -p "Enter environment to rotate: " env
                    if [[ " ${ENVIRONMENTS[*]} " =~ " ${env} " ]]; then
                        rotate_secrets "$env"
                    else
                        echo -e "${RED}❌ Invalid environment${NC}"
                    fi
                    ;;
                6)
                    echo "Available environments: ${ENVIRONMENTS[*]}"
                    read -p "Enter environment to validate: " env
                    if [[ " ${ENVIRONMENTS[*]} " =~ " ${env} " ]]; then
                        validate_secrets "$env"
                    else
                        echo -e "${RED}❌ Invalid environment${NC}"
                    fi
                    ;;
                7)
                    setup_vault
                    ;;
                8)
                    echo -e "${GREEN}Goodbye!${NC}"
                    exit 0
                    ;;
                *)
                    echo -e "${RED}Invalid option${NC}"
                    ;;
            esac
        done
    else
        # Command line mode
        case $1 in
            "setup")
                if [[ -n $2 ]]; then
                    setup_env_vars "$2"
                    if [[ "$2" != "development" ]]; then
                        create_k8s_secrets "$2"
                        encrypt_for_github "$2"
                    fi
                else
                    echo "Usage: $0 setup [environment]"
                    exit 1
                fi
                ;;
            "rotate")
                if [[ -n $2 ]]; then
                    rotate_secrets "$2"
                else
                    echo "Usage: $0 rotate [environment]"
                    exit 1
                fi
                ;;
            "validate")
                if [[ -n $2 ]]; then
                    validate_secrets "$2"
                else
                    echo "Usage: $0 validate [environment]"
                    exit 1
                fi
                ;;
            "vault")
                setup_vault
                ;;
            *)
                echo "Usage: $0 {setup|rotate|validate|vault} [environment]"
                echo "Or run without arguments for interactive mode"
                exit 1
                ;;
        esac
    fi
}

# Safety checks
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    # Check requirements
    if ! command -v kubectl &> /dev/null; then
        echo -e "${RED}❌ kubectl not found. Please install it first.${NC}"
        exit 1
    fi
    
    if ! command -v openssl &> /dev/null; then
        echo -e "${RED}❌ openssl not found. Please install it first.${NC}"
        exit 1
    fi
    
    # Create directories
    mkdir -p certs/{staging,production}
    mkdir -p secrets/{staging,production}
    
    # Run main function
    main "$@"
fi