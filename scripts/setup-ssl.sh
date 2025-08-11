#!/bin/bash

# LeanVibe SSL/TLS Certificate Management and Automation
# This script manages SSL certificates using Let's Encrypt and cert-manager

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔐 LeanVibe SSL/TLS Certificate Management${NC}"
echo "================================================="

# Configuration
CERT_MANAGER_VERSION="v1.13.2"
ACME_EMAIL="admin@leanvibe.app"  # Replace with your email
ENVIRONMENTS=("staging" "production")

# Domain configuration
declare -A DOMAINS
DOMAINS[staging]="staging-api.leanvibe.app staging.leanvibe.app"
DOMAINS[production]="api.leanvibe.app leanvibe.app www.leanvibe.app"

# Function to install cert-manager
install_cert_manager() {
    echo -e "${YELLOW}Installing cert-manager ${CERT_MANAGER_VERSION}...${NC}"
    
    # Add cert-manager CRDs
    kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/${CERT_MANAGER_VERSION}/cert-manager.crds.yaml
    
    # Create cert-manager namespace
    kubectl create namespace cert-manager --dry-run=client -o yaml | kubectl apply -f -
    
    # Add Jetstack Helm repository
    helm repo add jetstack https://charts.jetstack.io
    helm repo update
    
    # Install cert-manager
    helm upgrade --install \
        cert-manager jetstack/cert-manager \
        --namespace cert-manager \
        --version ${CERT_MANAGER_VERSION} \
        --set installCRDs=false \
        --set global.leaderElection.namespace=cert-manager
    
    # Wait for cert-manager to be ready
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/instance=cert-manager -n cert-manager --timeout=300s
    
    echo -e "${GREEN}✅ cert-manager installed successfully${NC}"
}

# Function to create ClusterIssuer for Let's Encrypt
create_cluster_issuer() {
    local env=$1
    local staging_flag=""
    
    if [[ "$env" == "staging" ]]; then
        staging_flag="-staging"
    fi
    
    echo -e "${YELLOW}Creating ClusterIssuer for ${env}...${NC}"
    
    cat << EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-${env}
spec:
  acme:
    # ACME server URL for Let's Encrypt
    server: https://acme${staging_flag}-v02.api.letsencrypt.org/directory
    # Email address used for ACME registration
    email: ${ACME_EMAIL}
    # Name of a secret used to store the ACME account private key
    privateKeySecretRef:
      name: letsencrypt-${env}
    # Enable the HTTP-01 challenge provider
    solvers:
    - http01:
        ingress:
          class: nginx
    # Enable DNS-01 challenge provider (optional, for wildcard certificates)
    - dns01:
        cloudflare:
          email: ${ACME_EMAIL}
          apiTokenSecretRef:
            name: cloudflare-api-token
            key: api-token
      selector:
        dnsNames:
        - '*.leanvibe.app'
EOF
    
    echo -e "${GREEN}✅ ClusterIssuer letsencrypt-${env} created${NC}"
}

# Function to create certificate for environment
create_certificate() {
    local env=$1
    local namespace="leanvibe-${env}"
    local domains_list=${DOMAINS[$env]}
    
    echo -e "${YELLOW}Creating certificate for ${env} environment...${NC}"
    
    # Create namespace if it doesn't exist
    kubectl create namespace ${namespace} --dry-run=client -o yaml | kubectl apply -f -
    
    # Build domains array for YAML
    local domains_yaml=""
    for domain in $domains_list; do
        domains_yaml="${domains_yaml}  - ${domain}\n"
    done
    
    # Create Certificate resource
    cat << EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: leanvibe-tls-${env}
  namespace: ${namespace}
spec:
  # Secret names are always required
  secretName: leanvibe-tls
  
  # At least one of a DNS Name, URI, or IP address is required
  dnsNames:
$(echo -e "$domains_yaml")
  
  # Issuer references are always required
  issuerRef:
    name: letsencrypt-${env}
    kind: ClusterIssuer
    group: cert-manager.io
  
  # Certificate renewal settings
  duration: 2160h # 90 days
  renewBefore: 360h # 15 days before expiry
  
  # Private key settings
  privateKey:
    algorithm: RSA
    encoding: PKCS1
    size: 2048
  
  # Subject settings
  subject:
    organizationalUnits:
    - LeanVibe
    countries:
    - US
    provinces:
    - CA
    localities:
    - San Francisco
    organizations:
    - LeanVibe Inc
  
  # Key usages
  usages:
  - digital signature
  - key encipherment
EOF
    
    echo -e "${GREEN}✅ Certificate leanvibe-tls-${env} created${NC}"
}

# Function to create ingress with TLS
create_tls_ingress() {
    local env=$1
    local namespace="leanvibe-${env}"
    local primary_domain
    
    case $env in
        "staging")
            primary_domain="staging-api.leanvibe.app"
            ;;
        "production")
            primary_domain="api.leanvibe.app"
            ;;
    esac
    
    echo -e "${YELLOW}Creating TLS-enabled ingress for ${env}...${NC}"
    
    cat << EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: leanvibe-ingress-${env}
  namespace: ${namespace}
  annotations:
    # Nginx ingress controller annotations
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
    nginx.ingress.kubernetes.io/ssl-protocols: "TLSv1.2 TLSv1.3"
    nginx.ingress.kubernetes.io/ssl-ciphers: "ECDHE-RSA-AES128-GCM-SHA256,ECDHE-RSA-AES256-GCM-SHA384,ECDHE-RSA-AES128-SHA256,ECDHE-RSA-AES256-SHA384"
    
    # Security headers
    nginx.ingress.kubernetes.io/server-snippet: |
      add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
      add_header X-Frame-Options "DENY" always;
      add_header X-Content-Type-Options "nosniff" always;
      add_header X-XSS-Protection "1; mode=block" always;
      add_header Referrer-Policy "strict-origin-when-cross-origin" always;
      add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none';" always;
    
    # Rate limiting
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
    
    # CORS
    nginx.ingress.kubernetes.io/enable-cors: "true"
    nginx.ingress.kubernetes.io/cors-allow-origin: "https://${primary_domain}"
    nginx.ingress.kubernetes.io/cors-allow-methods: "GET, POST, PUT, DELETE, OPTIONS"
    nginx.ingress.kubernetes.io/cors-allow-headers: "Content-Type, Authorization, X-Requested-With"
    
    # Let's Encrypt certificate issuer
    cert-manager.io/cluster-issuer: "letsencrypt-${env}"
    
spec:
  ingressClassName: nginx
  
  tls:
  - hosts:
$(for domain in ${DOMAINS[$env]}; do echo "    - $domain"; done)
    secretName: leanvibe-tls
  
  rules:
$(for domain in ${DOMAINS[$env]}; do
  echo "  - host: $domain"
  echo "    http:"
  echo "      paths:"
  echo "      - path: /"
  echo "        pathType: Prefix"
  echo "        backend:"
  echo "          service:"
  echo "            name: leanvibe-backend-${env}"
  echo "            port:"
  echo "              number: 8000"
done)
EOF
    
    echo -e "${GREEN}✅ TLS-enabled ingress created for ${env}${NC}"
}

# Function to setup monitoring for SSL certificates
setup_ssl_monitoring() {
    echo -e "${YELLOW}Setting up SSL certificate monitoring...${NC}"
    
    # Create certificate monitoring ServiceMonitor for Prometheus
    cat << EOF | kubectl apply -f -
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: cert-manager-metrics
  namespace: cert-manager
  labels:
    app.kubernetes.io/name: cert-manager
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: cert-manager
  endpoints:
  - port: tcp-prometheus-servicemonitor
    interval: 60s
    path: /metrics
EOF
    
    # Create PrometheusRule for SSL certificate alerts
    cat << EOF | kubectl apply -f -
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: ssl-certificate-alerts
  namespace: monitoring
  labels:
    prometheus: leanvibe
spec:
  groups:
  - name: ssl-certificate
    rules:
    - alert: SSLCertificateExpiringSoon
      expr: (certmanager_certificate_expiration_timestamp_seconds - time()) / 86400 < 30
      for: 12h
      labels:
        severity: warning
      annotations:
        summary: "SSL certificate expiring soon"
        description: "SSL certificate for {{ \$labels.name }} expires in {{ \$value }} days"
    
    - alert: SSLCertificateExpired
      expr: (certmanager_certificate_expiration_timestamp_seconds - time()) / 86400 < 0
      for: 1m
      labels:
        severity: critical
      annotations:
        summary: "SSL certificate expired"
        description: "SSL certificate for {{ \$labels.name }} has expired"
    
    - alert: SSLCertificateRenewalFailed
      expr: certmanager_certificate_ready_status{condition="False"} == 1
      for: 15m
      labels:
        severity: critical
      annotations:
        summary: "SSL certificate renewal failed"
        description: "SSL certificate renewal failed for {{ \$labels.name }}"
EOF
    
    echo -e "${GREEN}✅ SSL monitoring configured${NC}"
}

# Function to verify SSL setup
verify_ssl_setup() {
    local env=$1
    local namespace="leanvibe-${env}"
    
    echo -e "${YELLOW}Verifying SSL setup for ${env}...${NC}"
    
    # Check Certificate status
    echo "Checking certificate status..."
    kubectl get certificate leanvibe-tls-${env} -n ${namespace} -o wide
    
    # Check Certificate details
    cert_ready=$(kubectl get certificate leanvibe-tls-${env} -n ${namespace} -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}')
    
    if [[ "$cert_ready" == "True" ]]; then
        echo -e "${GREEN}✅ Certificate is ready${NC}"
        
        # Get certificate details
        kubectl describe certificate leanvibe-tls-${env} -n ${namespace}
        
        # Check certificate expiration
        expiry=$(kubectl get secret leanvibe-tls -n ${namespace} -o jsonpath='{.data.tls\.crt}' | base64 -d | openssl x509 -noout -enddate | cut -d= -f2)
        echo -e "${GREEN}Certificate expires: ${expiry}${NC}"
        
    else
        echo -e "${RED}❌ Certificate not ready${NC}"
        echo "Certificate events:"
        kubectl describe certificate leanvibe-tls-${env} -n ${namespace} | tail -20
        
        echo "CertificateRequest status:"
        kubectl get certificaterequest -n ${namespace}
        
        echo "Order status:"
        kubectl get order -n ${namespace}
    fi
    
    # Check Ingress
    echo "Checking ingress..."
    kubectl get ingress leanvibe-ingress-${env} -n ${namespace} -o wide
    
    # Test SSL endpoints (if domains resolve)
    for domain in ${DOMAINS[$env]}; do
        if nslookup "$domain" >/dev/null 2>&1; then
            echo "Testing SSL for $domain..."
            if timeout 10 openssl s_client -connect "$domain:443" -servername "$domain" < /dev/null 2>/dev/null | grep -q "Verify return code: 0"; then
                echo -e "${GREEN}✅ SSL verification successful for $domain${NC}"
            else
                echo -e "${YELLOW}⚠️  SSL verification failed for $domain (may not be propagated yet)${NC}"
            fi
        else
            echo -e "${YELLOW}⚠️  Domain $domain does not resolve${NC}"
        fi
    done
}

# Function to renew certificates manually
renew_certificates() {
    echo -e "${YELLOW}Triggering certificate renewal...${NC}"
    
    for env in "${ENVIRONMENTS[@]}"; do
        local namespace="leanvibe-${env}"
        
        echo "Renewing certificate for ${env}..."
        
        # Delete existing certificate to trigger renewal
        kubectl delete certificate leanvibe-tls-${env} -n ${namespace} --ignore-not-found
        
        # Recreate certificate
        create_certificate "$env"
        
        # Wait for certificate to be issued
        echo "Waiting for certificate to be ready..."
        kubectl wait --for=condition=ready certificate/leanvibe-tls-${env} -n ${namespace} --timeout=600s
        
        echo -e "${GREEN}✅ Certificate renewed for ${env}${NC}"
    done
}

# Function to backup certificates
backup_certificates() {
    echo -e "${YELLOW}Backing up certificates...${NC}"
    
    backup_dir="ssl-backup-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$backup_dir"
    
    for env in "${ENVIRONMENTS[@]}"; do
        local namespace="leanvibe-${env}"
        
        echo "Backing up certificates for ${env}..."
        
        # Export certificate
        kubectl get secret leanvibe-tls -n ${namespace} -o yaml > "${backup_dir}/cert-${env}.yaml"
        
        # Export certificate in PEM format
        kubectl get secret leanvibe-tls -n ${namespace} -o jsonpath='{.data.tls\.crt}' | base64 -d > "${backup_dir}/cert-${env}.crt"
        kubectl get secret leanvibe-tls -n ${namespace} -o jsonpath='{.data.tls\.key}' | base64 -d > "${backup_dir}/key-${env}.key"
        
        echo "Certificate details for ${env}:" >> "${backup_dir}/cert-info-${env}.txt"
        openssl x509 -in "${backup_dir}/cert-${env}.crt" -text -noout >> "${backup_dir}/cert-info-${env}.txt"
    done
    
    # Create backup archive
    tar -czf "${backup_dir}.tar.gz" "${backup_dir}"
    rm -rf "${backup_dir}"
    
    echo -e "${GREEN}✅ Certificates backed up to ${backup_dir}.tar.gz${NC}"
}

# Function to show certificate status
show_certificate_status() {
    echo -e "${YELLOW}SSL Certificate Status Report${NC}"
    echo "================================"
    
    for env in "${ENVIRONMENTS[@]}"; do
        local namespace="leanvibe-${env}"
        
        echo -e "\n${BLUE}${env^} Environment:${NC}"
        
        # Check if certificate exists
        if kubectl get certificate leanvibe-tls-${env} -n ${namespace} >/dev/null 2>&1; then
            # Certificate status
            cert_ready=$(kubectl get certificate leanvibe-tls-${env} -n ${namespace} -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}')
            cert_reason=$(kubectl get certificate leanvibe-tls-${env} -n ${namespace} -o jsonpath='{.status.conditions[?(@.type=="Ready")].message}')
            
            if [[ "$cert_ready" == "True" ]]; then
                echo -e "  Status: ${GREEN}✅ Ready${NC}"
                
                # Get expiration date
                if kubectl get secret leanvibe-tls -n ${namespace} >/dev/null 2>&1; then
                    expiry=$(kubectl get secret leanvibe-tls -n ${namespace} -o jsonpath='{.data.tls\.crt}' | base64 -d | openssl x509 -noout -enddate | cut -d= -f2)
                    expiry_epoch=$(date -d "$expiry" +%s 2>/dev/null || echo "0")
                    current_epoch=$(date +%s)
                    days_until_expiry=$(( (expiry_epoch - current_epoch) / 86400 ))
                    
                    if [ $days_until_expiry -gt 30 ]; then
                        echo -e "  Expires: ${GREEN}$expiry (${days_until_expiry} days)${NC}"
                    elif [ $days_until_expiry -gt 7 ]; then
                        echo -e "  Expires: ${YELLOW}$expiry (${days_until_expiry} days)${NC}"
                    else
                        echo -e "  Expires: ${RED}$expiry (${days_until_expiry} days)${NC}"
                    fi
                    
                    # Get certificate details
                    issuer=$(kubectl get secret leanvibe-tls -n ${namespace} -o jsonpath='{.data.tls\.crt}' | base64 -d | openssl x509 -noout -issuer | cut -d= -f2-)
                    echo "  Issuer: $issuer"
                    
                    # Get subject alternative names
                    sans=$(kubectl get secret leanvibe-tls -n ${namespace} -o jsonpath='{.data.tls\.crt}' | base64 -d | openssl x509 -noout -text | grep -A 1 "Subject Alternative Name" | tail -1 | sed 's/^[[:space:]]*//')
                    echo "  Domains: $sans"
                fi
            else
                echo -e "  Status: ${RED}❌ Not Ready${NC}"
                echo "  Reason: $cert_reason"
            fi
            
            # Get renewal information
            renewal_time=$(kubectl get certificate leanvibe-tls-${env} -n ${namespace} -o jsonpath='{.status.renewalTime}')
            if [[ -n "$renewal_time" ]]; then
                echo "  Next Renewal: $renewal_time"
            fi
            
        else
            echo -e "  Status: ${RED}❌ Certificate not found${NC}"
        fi
        
        # Check domains
        echo "  Domain Status:"
        for domain in ${DOMAINS[$env]}; do
            if timeout 5 curl -s -I "https://$domain" >/dev/null 2>&1; then
                echo -e "    $domain: ${GREEN}✅ Accessible${NC}"
            else
                echo -e "    $domain: ${RED}❌ Not accessible${NC}"
            fi
        done
    done
    
    echo ""
}

# Main menu
show_menu() {
    echo ""
    echo "SSL/TLS Certificate Management Options:"
    echo "1) Install cert-manager"
    echo "2) Setup SSL for all environments" 
    echo "3) Setup SSL for staging only"
    echo "4) Setup SSL for production only"
    echo "5) Verify SSL setup"
    echo "6) Show certificate status"
    echo "7) Renew certificates manually"
    echo "8) Backup certificates"
    echo "9) Setup SSL monitoring"
    echo "10) Exit"
    echo ""
}

# Main execution function
main() {
    if [[ $# -eq 0 ]]; then
        # Interactive mode
        while true; do
            show_menu
            read -p "Enter choice [1-10]: " choice
            
            case $choice in
                1)
                    install_cert_manager
                    ;;
                2)
                    install_cert_manager
                    for env in "${ENVIRONMENTS[@]}"; do
                        create_cluster_issuer "$env"
                        create_certificate "$env"
                        create_tls_ingress "$env"
                    done
                    setup_ssl_monitoring
                    ;;
                3)
                    create_cluster_issuer "staging"
                    create_certificate "staging"
                    create_tls_ingress "staging"
                    ;;
                4)
                    create_cluster_issuer "production"
                    create_certificate "production"
                    create_tls_ingress "production"
                    ;;
                5)
                    echo "Available environments: ${ENVIRONMENTS[*]}"
                    read -p "Enter environment to verify (or 'all'): " env
                    if [[ "$env" == "all" ]]; then
                        for e in "${ENVIRONMENTS[@]}"; do
                            verify_ssl_setup "$e"
                        done
                    elif [[ " ${ENVIRONMENTS[*]} " =~ " ${env} " ]]; then
                        verify_ssl_setup "$env"
                    else
                        echo -e "${RED}❌ Invalid environment${NC}"
                    fi
                    ;;
                6)
                    show_certificate_status
                    ;;
                7)
                    renew_certificates
                    ;;
                8)
                    backup_certificates
                    ;;
                9)
                    setup_ssl_monitoring
                    ;;
                10)
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
            "install")
                install_cert_manager
                ;;
            "setup")
                if [[ -n $2 ]]; then
                    if [[ "$2" == "all" ]]; then
                        install_cert_manager
                        for env in "${ENVIRONMENTS[@]}"; do
                            create_cluster_issuer "$env"
                            create_certificate "$env"
                            create_tls_ingress "$env"
                        done
                        setup_ssl_monitoring
                    elif [[ " ${ENVIRONMENTS[*]} " =~ " $2 " ]]; then
                        create_cluster_issuer "$2"
                        create_certificate "$2"
                        create_tls_ingress "$2"
                    else
                        echo -e "${RED}❌ Invalid environment: $2${NC}"
                        echo "Available: ${ENVIRONMENTS[*]} all"
                        exit 1
                    fi
                else
                    echo "Usage: $0 setup [environment|all]"
                    exit 1
                fi
                ;;
            "verify")
                if [[ -n $2 ]]; then
                    if [[ " ${ENVIRONMENTS[*]} " =~ " $2 " ]]; then
                        verify_ssl_setup "$2"
                    else
                        echo -e "${RED}❌ Invalid environment: $2${NC}"
                        exit 1
                    fi
                else
                    echo "Usage: $0 verify [environment]"
                    exit 1
                fi
                ;;
            "status")
                show_certificate_status
                ;;
            "renew")
                renew_certificates
                ;;
            "backup")
                backup_certificates
                ;;
            "monitor")
                setup_ssl_monitoring
                ;;
            *)
                echo "Usage: $0 {install|setup|verify|status|renew|backup|monitor} [environment]"
                echo "Or run without arguments for interactive mode"
                exit 1
                ;;
        esac
    fi
}

# Safety checks and requirements
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    # Check requirements
    if ! command -v kubectl &> /dev/null; then
        echo -e "${RED}❌ kubectl not found. Please install it first.${NC}"
        exit 1
    fi
    
    if ! command -v helm &> /dev/null; then
        echo -e "${RED}❌ helm not found. Please install it first.${NC}"
        exit 1
    fi
    
    if ! command -v openssl &> /dev/null; then
        echo -e "${RED}❌ openssl not found. Please install it first.${NC}"
        exit 1
    fi
    
    # Create necessary directories
    mkdir -p certs/{staging,production}
    
    # Run main function
    main "$@"
fi