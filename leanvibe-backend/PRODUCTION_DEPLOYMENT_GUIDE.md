# Production Deployment and Operations Guide

## Overview

This comprehensive guide provides enterprise-grade deployment and operations procedures for LeanVibe at scale. The deployment architecture supports multi-cloud infrastructure, enterprise SLA requirements (99.95% uptime), automated scaling, and comprehensive monitoring with disaster recovery capabilities.

## Infrastructure Requirements

### Kubernetes Cluster Specifications

#### Minimum Production Cluster Requirements

**Control Plane Configuration:**
- **Kubernetes Version**: 1.27+ (managed service recommended)
- **Control Plane**: Multi-AZ deployment with 3 master nodes minimum
- **API Server**: Load balanced across availability zones
- **etcd**: Encrypted, backed up every 6 hours with point-in-time recovery
- **Network Policy**: Calico or Cilium for micro-segmentation

**Node Group Architecture:**
```yaml
# System Node Group - Critical system components
system_nodes:
  instance_type: "t3.medium"
  min_size: 2
  max_size: 4
  desired_size: 2
  disk_size: 50GB
  labels:
    role: "system"
    tier: "system"
  taints:
    - key: "CriticalAddonsOnly"
      value: "true"
      effect: "NO_SCHEDULE"

# Application Node Group - LeanVibe backend services
application_nodes:
  instance_type: "t3.large, t3.xlarge"
  min_size: 3
  max_size: 20
  desired_size: 5
  disk_size: 100GB
  labels:
    role: "application"
    tier: "backend"

# Database Node Group - Data tier services
database_nodes:
  instance_type: "r5.large, r5.xlarge" 
  min_size: 2
  max_size: 6
  desired_size: 3
  disk_size: 200GB
  labels:
    role: "database"
    tier: "data"
  taints:
    - key: "database"
      value: "true"
      effect: "NO_SCHEDULE"
```

### Database and Caching Infrastructure

#### Neo4j Cluster Configuration

**Production Neo4j Setup:**
```yaml
# Neo4j Causal Cluster for High Availability
neo4j_cluster:
  core_servers: 3          # Core servers for write operations
  read_replicas: 2         # Read replicas for scaling
  instance_type: "r5.xlarge"
  storage_type: "gp3"
  storage_size: "500GB"
  iops: 3000
  backup_retention: 30     # 30-day backup retention
  monitoring_enabled: true
  encryption:
    at_rest: true
    in_transit: true
  memory_allocation:
    heap_size: "8G"
    page_cache: "4G"
```

**Neo4j Kubernetes Deployment:**
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: neo4j-cluster
  namespace: leanvibe-production
spec:
  serviceName: neo4j
  replicas: 3
  template:
    spec:
      containers:
      - name: neo4j
        image: neo4j:5.15-enterprise
        env:
        - name: NEO4J_ACCEPT_LICENSE_AGREEMENT
          value: "yes"
        - name: NEO4J_dbms_mode
          value: "CORE"
        - name: NEO4J_dbms_cluster_discovery_endpoints
          value: "neo4j-0.neo4j:5000,neo4j-1.neo4j:5000,neo4j-2.neo4j:5000"
        - name: NEO4J_dbms_cluster_minimum__initial__system__primaries__count
          value: "3"
        resources:
          requests:
            memory: "8Gi"
            cpu: "2"
          limits:
            memory: "16Gi"
            cpu: "4"
        volumeMounts:
        - name: data
          mountPath: /data
        - name: logs  
          mountPath: /logs
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 500Gi
      storageClassName: gp3-encrypted
```

#### Redis Cluster Configuration

**Enterprise Redis Setup:**
```yaml
# Redis Cluster for Session Management and Caching
redis_cluster:
  cluster_mode: true
  node_type: "cache.r6g.xlarge"
  num_cache_nodes: 6      # 3 shards with 1 replica each
  parameter_group: "redis7"
  engine_version: "7.0"
  port: 6379
  
  # High Availability Configuration
  automatic_failover: true
  multi_az: true
  
  # Security Configuration
  at_rest_encryption: true
  transit_encryption: true
  auth_token_enabled: true
  
  # Backup Configuration
  snapshot_retention_limit: 7
  snapshot_window: "02:00-03:00"
  maintenance_window: "sun:04:00-sun:05:00"
  
  # Performance Configuration
  reserved_memory_percent: 25
```

### Security and Compliance Hardening

#### Pod Security Standards

**Enterprise Security Policies:**
```yaml
apiVersion: v1
kind: Pod
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 1000
    fsGroup: 1000
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: leanvibe-backend
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      runAsNonRoot: true
      runAsUser: 1000
      capabilities:
        drop:
        - ALL
```

#### Network Security Policies

**Micro-segmentation Configuration:**
```yaml
# Network Policy for Backend Services
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: leanvibe-backend-policy
  namespace: leanvibe-production
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: leanvibe
      app.kubernetes.io/component: backend
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: leanvibe-production
    ports:
    - protocol: TCP
      port: 8765
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: leanvibe-production
    ports:
    - protocol: TCP
      port: 7687  # Neo4j
    - protocol: TCP
      port: 6379  # Redis
  - to: []  # External HTTPS traffic
    ports:
    - protocol: TCP
      port: 443
```

## Deployment Procedures

### Infrastructure as Code (Terraform)

#### Multi-Cloud Deployment Setup

**AWS Infrastructure Deployment:**
```bash
#!/bin/bash
# AWS Production Deployment Script

# Export environment variables
export AWS_REGION="us-east-1"
export ENVIRONMENT="production"
export PROJECT_NAME="leanvibe"

# Initialize Terraform
terraform init \
  -backend-config="bucket=leanvibe-terraform-state-prod" \
  -backend-config="key=infrastructure/terraform.tfstate" \
  -backend-config="region=$AWS_REGION" \
  -backend-config="encrypt=true" \
  -backend-config="dynamodb_table=leanvibe-terraform-locks"

# Plan infrastructure changes
terraform plan \
  -var="environment=$ENVIRONMENT" \
  -var="aws_region=$AWS_REGION" \
  -var="kubernetes_version=1.27" \
  -var="db_instance_class=db.r5.xlarge" \
  -var="redis_node_type=cache.r6g.xlarge" \
  -out=production.tfplan

# Apply infrastructure changes
terraform apply production.tfplan

# Output important connection information
terraform output -json > infrastructure_outputs.json
```

**Azure Infrastructure Deployment:**
```bash
#!/bin/bash
# Azure Production Deployment Script

# Set Azure environment
export ARM_SUBSCRIPTION_ID="your-subscription-id"
export ARM_TENANT_ID="your-tenant-id"
export ARM_CLIENT_ID="your-client-id"
export ARM_CLIENT_SECRET="your-client-secret"

# Initialize Terraform for Azure
terraform init \
  -backend-config="storage_account_name=leanvibeterraformstate" \
  -backend-config="container_name=production" \
  -backend-config="key=infrastructure.terraform.tfstate"

# Deploy Azure resources
terraform plan \
  -var="environment=production" \
  -var="location=East US" \
  -var="kubernetes_version=1.27" \
  -out=azure-production.tfplan

terraform apply azure-production.tfplan
```

#### Terraform Configuration Management

**Environment-Specific Variables:**
```hcl
# terraform/environments/production/terraform.tfvars
environment = "production"
aws_region  = "us-east-1"

# Kubernetes configuration
kubernetes_version = "1.27"

# Network configuration
vpc_cidr = "10.0.0.0/16"
public_subnet_cidrs   = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
private_subnet_cidrs  = ["10.0.10.0/24", "10.0.11.0/24", "10.0.12.0/24"]
database_subnet_cidrs = ["10.0.20.0/24", "10.0.21.0/24", "10.0.22.0/24"]

# Database configuration
db_instance_class        = "db.r5.xlarge"
db_allocated_storage     = 500
db_max_allocated_storage = 2000

# Redis configuration
redis_node_type = "cache.r6g.xlarge"

# Domain configuration
domain_name = "leanvibe.ai"

# Enterprise features
enable_waf           = true
enable_shield        = true
enable_guard_duty    = true
enable_config        = true
enable_cloudtrail    = true
enable_security_hub  = true
```

### Application Deployment

#### Docker Image Build and Registry

**Production Dockerfile:**
```dockerfile
# Multi-stage build for production optimization
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim as production

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -g 1000 leanvibe \
    && useradd -r -u 1000 -g leanvibe leanvibe

# Copy virtual environment
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create application directories
RUN mkdir -p /app/logs /app/cache /tmp \
    && chown -R leanvibe:leanvibe /app /tmp

# Copy application code
COPY --chown=leanvibe:leanvibe . /app
WORKDIR /app

# Switch to non-root user
USER leanvibe

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8765/health || exit 1

# Run application
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**CI/CD Pipeline (GitHub Actions):**
```yaml
name: Production Deployment
on:
  push:
    branches: [main]
    tags: ['v*']

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    environment: production
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v4
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: us-east-1
        
    - name: Login to Amazon ECR
      id: login-ecr
      uses: aws-actions/amazon-ecr-login@v2
      
    - name: Build and push Docker image
      env:
        ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
        ECR_REPOSITORY: leanvibe-backend
        IMAGE_TAG: ${{ github.sha }}
      run: |
        docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
        docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
        docker tag $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPOSITORY:latest
        docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest
        
    - name: Deploy to Kubernetes
      run: |
        aws eks update-kubeconfig --name leanvibe-production --region us-east-1
        kubectl set image deployment/leanvibe-backend \
          leanvibe-backend=$ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG \
          -n leanvibe-production
        kubectl rollout status deployment/leanvibe-backend -n leanvibe-production --timeout=600s
        
    - name: Run post-deployment health checks
      run: |
        kubectl wait --for=condition=available --timeout=300s deployment/leanvibe-backend -n leanvibe-production
        ./scripts/health_check.sh production
```

#### Database Migration and Schema Management

**Automated Migration Pipeline:**
```python
# Database migration management
from app.core.database import get_database_session
from alembic import command
from alembic.config import Config

class ProductionMigrationManager:
    def __init__(self):
        self.alembic_cfg = Config("alembic.ini")
    
    async def run_pre_deployment_checks(self):
        """Run comprehensive pre-deployment database checks"""
        
        # Check database connectivity
        async with get_database_session() as db:
            result = await db.execute("SELECT 1")
            assert result.scalar() == 1
        
        # Check current migration status
        current_revision = command.current(self.alembic_cfg)
        target_revision = command.heads(self.alembic_cfg)
        
        logger.info(f"Current revision: {current_revision}")
        logger.info(f"Target revision: {target_revision}")
        
        # Validate migration scripts
        await self.validate_migration_scripts()
        
        # Check for data conflicts
        await self.check_data_conflicts()
        
        return {
            "database_healthy": True,
            "migration_required": current_revision != target_revision,
            "backup_required": True
        }
    
    async def create_pre_migration_backup(self):
        """Create full database backup before migration"""
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_name = f"pre_migration_backup_{timestamp}"
        
        # Create database backup
        backup_command = [
            "pg_dump",
            "-h", os.getenv("DATABASE_HOST"),
            "-U", os.getenv("DATABASE_USER"),
            "-d", os.getenv("DATABASE_NAME"),
            "-f", f"/backups/{backup_name}.sql",
            "--verbose"
        ]
        
        process = await asyncio.create_subprocess_exec(
            *backup_command,
            env={**os.environ, "PGPASSWORD": os.getenv("DATABASE_PASSWORD")}
        )
        
        await process.wait()
        
        if process.returncode != 0:
            raise Exception("Database backup failed")
        
        logger.info(f"Database backup created: {backup_name}.sql")
        return backup_name
    
    async def run_migrations(self):
        """Execute database migrations with error handling"""
        
        try:
            # Run migrations
            command.upgrade(self.alembic_cfg, "head")
            logger.info("Database migrations completed successfully")
            
            # Verify migration success
            await self.verify_migration_success()
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            
            # Rollback migrations if possible
            await self.rollback_migrations()
            raise
    
    async def verify_migration_success(self):
        """Verify migration was successful"""
        
        # Check table structure
        async with get_database_session() as db:
            # Verify critical tables exist
            critical_tables = ["tenants", "users", "subscriptions", "billing_accounts"]
            
            for table in critical_tables:
                result = await db.execute(
                    "SELECT count(*) FROM information_schema.tables WHERE table_name = %s",
                    (table,)
                )
                
                if result.scalar() == 0:
                    raise Exception(f"Critical table {table} missing after migration")
        
        logger.info("Migration verification completed successfully")
```

### Configuration Management and Secrets

#### Kubernetes ConfigMaps and Secrets

**Application Configuration:**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: leanvibe-config
  namespace: leanvibe-production
data:
  # Application configuration
  ENVIRONMENT: "production"
  LOG_LEVEL: "INFO"
  
  # API Configuration
  API_VERSION: "v1"
  API_TIMEOUT: "30"
  MAX_REQUEST_SIZE: "50MB"
  
  # Redis Configuration
  REDIS_HOST: "redis-cluster.leanvibe-production.svc.cluster.local"
  REDIS_PORT: "6379"
  REDIS_DB: "0"
  CACHE_TTL: "3600"
  
  # Neo4j Configuration
  NEO4J_URI: "neo4j://neo4j-cluster.leanvibe-production.svc.cluster.local:7687"
  NEO4J_DATABASE: "leanvibe"
  
  # Monitoring Configuration
  PROMETHEUS_METRICS: "true"
  PROMETHEUS_PORT: "9090"
  HEALTH_CHECK_INTERVAL: "30"
  
  # Enterprise Features
  MULTI_TENANCY: "true"
  SSO_ENABLED: "true"
  BILLING_ENABLED: "true"
  
  # Performance Configuration
  WORKER_PROCESSES: "4"
  MAX_CONNECTIONS: "1000"
  KEEPALIVE_TIMEOUT: "65"
---
apiVersion: v1
kind: Secret
metadata:
  name: leanvibe-secrets
  namespace: leanvibe-production
type: Opaque
stringData:
  # Database Secrets
  DATABASE_PASSWORD: "{{ .Values.database.password }}"
  NEO4J_PASSWORD: "{{ .Values.neo4j.password }}"
  REDIS_PASSWORD: "{{ .Values.redis.password }}"
  
  # JWT and Encryption Keys
  JWT_SECRET_KEY: "{{ .Values.security.jwt_secret }}"
  ENCRYPTION_KEY: "{{ .Values.security.encryption_key }}"
  
  # External Service API Keys
  STRIPE_SECRET_KEY: "{{ .Values.stripe.secret_key }}"
  STRIPE_WEBHOOK_SECRET: "{{ .Values.stripe.webhook_secret }}"
  
  # OAuth Provider Secrets
  GOOGLE_OAUTH_SECRET: "{{ .Values.oauth.google.secret }}"
  MICROSOFT_OAUTH_SECRET: "{{ .Values.oauth.microsoft.secret }}"
  OKTA_OAUTH_SECRET: "{{ .Values.oauth.okta.secret }}"
  
  # Monitoring and Logging
  DATADOG_API_KEY: "{{ .Values.monitoring.datadog.api_key }}"
  SENTRY_DSN: "{{ .Values.monitoring.sentry.dsn }}"
```

**Secrets Management with External Secrets Operator:**
```yaml
# AWS Secrets Manager Integration
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: leanvibe-external-secrets
  namespace: leanvibe-production
spec:
  refreshInterval: 15m
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: leanvibe-secrets
    creationPolicy: Owner
  data:
  - secretKey: DATABASE_PASSWORD
    remoteRef:
      key: leanvibe/production/database
      property: password
  - secretKey: STRIPE_SECRET_KEY
    remoteRef:
      key: leanvibe/production/stripe
      property: secret_key
  - secretKey: JWT_SECRET_KEY
    remoteRef:
      key: leanvibe/production/security
      property: jwt_secret
```

## Monitoring and Observability

### Comprehensive Monitoring Stack

#### Prometheus and Grafana Setup

**Prometheus Configuration:**
```yaml
# Prometheus deployment for metrics collection
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus
  namespace: leanvibe-monitoring
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: prometheus
        image: prom/prometheus:v2.45.0
        args:
        - '--config.file=/etc/prometheus/prometheus.yml'
        - '--storage.tsdb.path=/prometheus/'
        - '--web.console.libraries=/etc/prometheus/console_libraries'
        - '--web.console.templates=/etc/prometheus/consoles'
        - '--storage.tsdb.retention.time=30d'
        - '--web.enable-lifecycle'
        - '--web.enable-admin-api'
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi" 
            cpu: "2"
        volumeMounts:
        - name: prometheus-config-volume
          mountPath: /etc/prometheus/
        - name: prometheus-storage-volume
          mountPath: /prometheus/
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: leanvibe-monitoring
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s
    
    rule_files:
    - "leanvibe_alerts.yml"
    
    alerting:
      alertmanagers:
      - static_configs:
        - targets:
          - alertmanager:9093
    
    scrape_configs:
    # LeanVibe Backend Services
    - job_name: 'leanvibe-backend'
      kubernetes_sd_configs:
      - role: endpoints
        namespaces:
          names:
          - leanvibe-production
      relabel_configs:
      - source_labels: [__meta_kubernetes_service_name]
        action: keep
        regex: leanvibe-backend
    
    # Neo4j Monitoring
    - job_name: 'neo4j'
      static_configs:
      - targets: ['neo4j-cluster:2004']
    
    # Redis Monitoring
    - job_name: 'redis'
      static_configs:
      - targets: ['redis-exporter:9121']
    
    # Kubernetes Cluster Monitoring
    - job_name: 'kubernetes-nodes'
      kubernetes_sd_configs:
      - role: node
      relabel_configs:
      - action: labelmap
        regex: __meta_kubernetes_node_label_(.+)
```

#### Enterprise Alerting Configuration

**Critical Alert Rules:**
```yaml
# leanvibe_alerts.yml
groups:
- name: leanvibe.production.critical
  rules:
  # System Health Alerts
  - alert: LeanVibeBackendDown
    expr: up{job="leanvibe-backend"} == 0
    for: 30s
    labels:
      severity: critical
      service: leanvibe-backend
    annotations:
      summary: "LeanVibe Backend service is down"
      description: "LeanVibe Backend has been down for more than 30 seconds"
      runbook_url: "https://docs.leanvibe.ai/runbooks/backend-down"
  
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
    for: 2m
    labels:
      severity: warning
      service: leanvibe-backend
    annotations:
      summary: "High error rate detected"
      description: "Error rate is {{ $value }} errors per second"
  
  - alert: DatabaseConnectionFailure
    expr: neo4j_up == 0
    for: 1m
    labels:
      severity: critical
      service: neo4j
    annotations:
      summary: "Neo4j database is unavailable"
      description: "Cannot connect to Neo4j database"
  
  # Performance Alerts
  - alert: HighResponseTime
    expr: histogram_quantile(0.95, http_request_duration_seconds_bucket) > 2
    for: 5m
    labels:
      severity: warning
      service: leanvibe-backend
    annotations:
      summary: "High response time"
      description: "95th percentile response time is {{ $value }}s"
  
  - alert: HighCPUUsage
    expr: cpu_usage_percent > 85
    for: 5m
    labels:
      severity: warning
      service: system
    annotations:
      summary: "High CPU usage"
      description: "CPU usage is {{ $value }}%"
  
  - alert: HighMemoryUsage  
    expr: memory_usage_percent > 90
    for: 5m
    labels:
      severity: critical
      service: system
    annotations:
      summary: "High memory usage"
      description: "Memory usage is {{ $value }}%"
  
  # Business Metrics Alerts
  - alert: BillingSystemDown
    expr: billing_system_healthy == 0
    for: 1m
    labels:
      severity: critical
      service: billing
    annotations:
      summary: "Billing system is unhealthy"
      description: "Billing system health check failed"
  
  - alert: HighTenantChurnRate
    expr: tenant_churn_rate_monthly > 5
    for: 15m
    labels:
      severity: warning
      service: business
    annotations:
      summary: "High tenant churn rate"
      description: "Monthly churn rate is {{ $value }}%"
  
  - alert: PaymentProcessingFailure
    expr: payment_success_rate < 0.95
    for: 10m
    labels:
      severity: critical
      service: billing
    annotations:
      summary: "Payment processing failure rate too high"
      description: "Payment success rate is {{ $value }}"
```

#### Custom Business Metrics

**Enterprise KPI Monitoring:**
```python
# Custom metrics collection for business KPIs
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry

# Define custom metrics
tenant_registrations = Counter(
    'leanvibe_tenant_registrations_total',
    'Total number of tenant registrations',
    ['plan', 'region']
)

subscription_revenue = Gauge(
    'leanvibe_subscription_revenue_usd',
    'Current subscription revenue in USD',
    ['plan', 'billing_interval']
)

api_request_duration = Histogram(
    'leanvibe_api_request_duration_seconds',
    'API request duration',
    ['method', 'endpoint', 'tenant_plan'],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 5.0]
)

tenant_usage_metrics = Gauge(
    'leanvibe_tenant_usage',
    'Current tenant usage metrics',
    ['tenant_id', 'metric_type']
)

billing_events = Counter(
    'leanvibe_billing_events_total',
    'Total billing events',
    ['event_type', 'tenant_plan', 'status']
)

# Metrics collection service
class EnterpriseMetricsCollector:
    def __init__(self):
        self.registry = CollectorRegistry()
    
    async def collect_business_metrics(self):
        """Collect and update business KPIs"""
        
        # Collect subscription revenue by plan
        revenue_by_plan = await self.get_revenue_by_plan()
        for plan, revenue in revenue_by_plan.items():
            subscription_revenue.labels(plan=plan, billing_interval='monthly').set(revenue)
        
        # Collect tenant usage metrics
        tenant_usage = await self.get_tenant_usage_metrics()
        for tenant_id, metrics in tenant_usage.items():
            for metric_type, value in metrics.items():
                tenant_usage_metrics.labels(tenant_id=tenant_id, metric_type=metric_type).set(value)
        
        # Collect API performance metrics by tenant plan
        await self.collect_api_performance_by_plan()
    
    async def record_tenant_registration(self, plan: str, region: str):
        """Record new tenant registration"""
        tenant_registrations.labels(plan=plan, region=region).inc()
    
    async def record_billing_event(self, event_type: str, tenant_plan: str, status: str):
        """Record billing system events"""
        billing_events.labels(event_type=event_type, tenant_plan=tenant_plan, status=status).inc()
```

### Log Management and Analysis

#### Centralized Logging with Fluentd and ELK Stack

**Fluentd Configuration:**
```yaml
# Fluentd DaemonSet for log collection
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluentd
  namespace: leanvibe-monitoring
spec:
  template:
    spec:
      containers:
      - name: fluentd
        image: fluent/fluentd-kubernetes-daemonset:v1.16-debian-elasticsearch8-1
        env:
        - name: FLUENT_ELASTICSEARCH_HOST
          value: "elasticsearch.leanvibe-monitoring.svc.cluster.local"
        - name: FLUENT_ELASTICSEARCH_PORT
          value: "9200"
        - name: FLUENT_ELASTICSEARCH_SCHEME
          value: "https"
        - name: FLUENT_ELASTICSEARCH_SSL_VERIFY
          value: "true"
        - name: FLUENT_ELASTICSEARCH_USER
          value: "elastic"
        - name: FLUENT_ELASTICSEARCH_PASSWORD
          valueFrom:
            secretKeyRef:
              name: elasticsearch-credentials
              key: password
        resources:
          limits:
            memory: 200Mi
            cpu: 100m
          requests:
            memory: 200Mi
            cpu: 100m
        volumeMounts:
        - name: config-volume
          mountPath: /fluentd/etc/
        - name: varlog
          mountPath: /var/log
        - name: varlibdockercontainers
          mountPath: /var/lib/docker/containers
          readOnly: true
      volumes:
      - name: config-volume
        configMap:
          name: fluentd-config
      - name: varlog
        hostPath:
          path: /var/log
      - name: varlibdockercontainers
        hostPath:
          path: /var/lib/docker/containers
```

**Elasticsearch Index Templates:**
```json
{
  "index_patterns": ["leanvibe-*"],
  "template": {
    "settings": {
      "number_of_shards": 3,
      "number_of_replicas": 1,
      "index.lifecycle.name": "leanvibe-policy",
      "index.lifecycle.rollover_alias": "leanvibe-logs"
    },
    "mappings": {
      "properties": {
        "@timestamp": {"type": "date"},
        "level": {"type": "keyword"},
        "message": {"type": "text"},
        "tenant_id": {"type": "keyword"},
        "user_id": {"type": "keyword"},
        "request_id": {"type": "keyword"},
        "service": {"type": "keyword"},
        "component": {"type": "keyword"},
        "duration_ms": {"type": "integer"},
        "status_code": {"type": "integer"},
        "error": {
          "type": "object",
          "properties": {
            "type": {"type": "keyword"},
            "message": {"type": "text"},
            "stack_trace": {"type": "text"}
          }
        }
      }
    }
  }
}
```

## Operational Procedures

### Incident Response

#### On-Call Rotation and Escalation

**Incident Severity Classification:**
```python
class IncidentSeverity:
    SEV1_CRITICAL = {
        "description": "Complete service outage or data loss",
        "response_time": "15 minutes",
        "escalation_time": "30 minutes",
        "notification_channels": ["pagerduty", "slack", "sms", "phone"],
        "stakeholders": ["on_call_engineer", "engineering_manager", "cto"]
    }
    
    SEV2_HIGH = {
        "description": "Major feature unavailable or severe performance degradation",
        "response_time": "30 minutes", 
        "escalation_time": "60 minutes",
        "notification_channels": ["pagerduty", "slack"],
        "stakeholders": ["on_call_engineer", "engineering_manager"]
    }
    
    SEV3_MEDIUM = {
        "description": "Minor feature issues or moderate performance impact",
        "response_time": "2 hours",
        "escalation_time": "4 hours",
        "notification_channels": ["slack", "email"],
        "stakeholders": ["on_call_engineer"]
    }
    
    SEV4_LOW = {
        "description": "Cosmetic issues or minimal impact",
        "response_time": "24 hours",
        "escalation_time": "72 hours", 
        "notification_channels": ["email"],
        "stakeholders": ["engineering_team"]
    }
```

**Automated Incident Response:**
```python
class IncidentResponseAutomation:
    async def handle_critical_incident(self, alert_data):
        """Automated response for critical incidents"""
        
        # Create incident ticket
        incident = await self.create_incident_ticket(alert_data, severity="SEV1")
        
        # Scale up resources immediately
        await self.emergency_scale_up()
        
        # Enable circuit breakers
        await self.enable_circuit_breakers()
        
        # Notify stakeholders
        await self.notify_stakeholders(incident, severity="SEV1")
        
        # Start status page update
        await self.update_status_page("investigating", incident.id)
        
        # Begin automated diagnostics
        diagnostics = await self.run_automated_diagnostics()
        
        # Update incident with initial findings
        await self.update_incident(incident.id, {"diagnostics": diagnostics})
        
        return incident
    
    async def emergency_scale_up(self):
        """Emergency scaling procedures"""
        
        # Scale backend pods to maximum
        await k8s_client.patch_namespaced_deployment_scale(
            name="leanvibe-backend",
            namespace="leanvibe-production",
            body={"spec": {"replicas": 20}}
        )
        
        # Scale database read replicas
        await self.scale_database_read_replicas(target_count=5)
        
        # Enable additional caching layers
        await self.enable_emergency_caching()
        
        logger.info("Emergency scaling activated")
```

#### Status Page Management

**Automated Status Updates:**
```python
class StatusPageManager:
    def __init__(self):
        self.status_page_api = StatusPageAPI()
        self.components = {
            "api": "LeanVibe API",
            "dashboard": "Web Dashboard",
            "billing": "Billing System",
            "sso": "Single Sign-On",
            "database": "Database",
            "cache": "Cache Layer"
        }
    
    async def update_component_status(self, component: str, status: str, message: str = None):
        """Update individual component status"""
        
        await self.status_page_api.update_component(
            component_id=self.components[component],
            status=status,  # operational, degraded_performance, partial_outage, major_outage
            description=message
        )
        
        # Send notifications for status changes
        if status in ["partial_outage", "major_outage"]:
            await self.notify_customers(component, status, message)
    
    async def create_maintenance_window(self, start_time, duration, affected_components):
        """Schedule maintenance window"""
        
        maintenance = await self.status_page_api.create_scheduled_maintenance(
            name=f"LeanVibe System Maintenance - {start_time.strftime('%Y-%m-%d')}",
            start_time=start_time,
            end_time=start_time + duration,
            status="scheduled",
            affected_components=affected_components,
            description="Scheduled maintenance to improve system performance and reliability"
        )
        
        # Send advance notifications
        await self.notify_customers_maintenance(maintenance)
        
        return maintenance
```

### Maintenance and Updates

#### Planned Maintenance Windows

**Blue-Green Deployment Strategy:**
```bash
#!/bin/bash
# Blue-Green deployment script

set -e

ENVIRONMENT="production"
NAMESPACE="leanvibe-production"
DEPLOYMENT="leanvibe-backend"
NEW_IMAGE="$1"

echo "Starting blue-green deployment..."
echo "New image: $NEW_IMAGE"

# Create green deployment
kubectl create deployment ${DEPLOYMENT}-green \
  --image=$NEW_IMAGE \
  --namespace=$NAMESPACE \
  --dry-run=client -o yaml | kubectl apply -f -

# Copy configuration from blue deployment
kubectl get deployment $DEPLOYMENT -n $NAMESPACE -o yaml | \
  sed 's/'"$DEPLOYMENT"'/'"$DEPLOYMENT"'-green/g' | \
  sed 's/app: '"$DEPLOYMENT"'/app: '"$DEPLOYMENT"'-green/g' | \
  kubectl apply -f -

# Wait for green deployment to be ready
echo "Waiting for green deployment to be ready..."
kubectl rollout status deployment/${DEPLOYMENT}-green -n $NAMESPACE --timeout=600s

# Run health checks on green deployment
echo "Running health checks on green deployment..."
GREEN_POD=$(kubectl get pods -n $NAMESPACE -l app=${DEPLOYMENT}-green -o jsonpath='{.items[0].metadata.name}')
kubectl port-forward $GREEN_POD 8080:8765 -n $NAMESPACE &
PORT_FORWARD_PID=$!

sleep 5

# Health check
if curl -f http://localhost:8080/health; then
    echo "Green deployment health check passed"
else
    echo "Green deployment health check failed"
    kill $PORT_FORWARD_PID
    kubectl delete deployment ${DEPLOYMENT}-green -n $NAMESPACE
    exit 1
fi

kill $PORT_FORWARD_PID

# Switch traffic to green deployment
echo "Switching traffic to green deployment..."
kubectl patch service $DEPLOYMENT -n $NAMESPACE -p '{"spec":{"selector":{"app":"'${DEPLOYMENT}'-green"}}}'

# Wait for traffic switch to complete
sleep 10

# Final health check
echo "Running final health checks..."
if curl -f https://api.leanvibe.ai/health; then
    echo "Production health check passed"
else
    echo "Production health check failed - rolling back"
    kubectl patch service $DEPLOYMENT -n $NAMESPACE -p '{"spec":{"selector":{"app":"'$DEPLOYMENT'"}}}'
    kubectl delete deployment ${DEPLOYMENT}-green -n $NAMESPACE
    exit 1
fi

# Clean up old blue deployment
echo "Cleaning up old deployment..."
kubectl delete deployment $DEPLOYMENT -n $NAMESPACE

# Rename green deployment to blue
kubectl patch deployment ${DEPLOYMENT}-green -n $NAMESPACE -p '{"metadata":{"name":"'$DEPLOYMENT'"},"spec":{"selector":{"matchLabels":{"app":"'$DEPLOYMENT'"}},"template":{"metadata":{"labels":{"app":"'$DEPLOYMENT'"}}}}}'

echo "Blue-green deployment completed successfully"
```

#### Database Migration Procedures

**Zero-Downtime Migration Strategy:**
```python
class ZeroDowntimeMigrationManager:
    async def execute_zero_downtime_migration(self, migration_id: str):
        """Execute zero-downtime database migration"""
        
        # Phase 1: Create shadow tables and triggers
        await self.create_shadow_tables(migration_id)
        await self.create_sync_triggers(migration_id)
        
        # Phase 2: Backfill shadow tables
        await self.backfill_shadow_tables(migration_id)
        
        # Phase 3: Enable dual writes
        await self.enable_dual_writes(migration_id)
        
        # Phase 4: Verify data consistency
        consistency_check = await self.verify_data_consistency(migration_id)
        if not consistency_check.passed:
            await self.rollback_migration(migration_id)
            raise Exception("Data consistency check failed")
        
        # Phase 5: Switch reads to new tables
        await self.switch_reads_to_new_tables(migration_id)
        
        # Phase 6: Verify application health
        health_check = await self.run_application_health_check()
        if not health_check.passed:
            await self.switch_reads_to_old_tables(migration_id)
            raise Exception("Application health check failed after migration")
        
        # Phase 7: Clean up old tables and triggers
        await self.cleanup_old_tables(migration_id)
        
        logger.info(f"Zero-downtime migration {migration_id} completed successfully")
        
    async def create_shadow_tables(self, migration_id: str):
        """Create shadow tables with new schema"""
        
        migration = await self.get_migration(migration_id)
        
        for table_migration in migration.table_migrations:
            shadow_table_name = f"{table_migration.table_name}_shadow"
            
            # Create shadow table with new schema
            create_sql = f"""
            CREATE TABLE {shadow_table_name} (
                LIKE {table_migration.table_name} INCLUDING ALL
            );
            """
            
            # Apply schema changes to shadow table
            for change in table_migration.schema_changes:
                alter_sql = f"ALTER TABLE {shadow_table_name} {change.sql}"
                await self.execute_sql(alter_sql)
            
            logger.info(f"Created shadow table: {shadow_table_name}")
```

### Performance Optimization

#### Auto-scaling Configuration

**Horizontal Pod Autoscaler (HPA):**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: leanvibe-backend-hpa
  namespace: leanvibe-production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: leanvibe-backend
  minReplicas: 3
  maxReplicas: 50
  metrics:
  # CPU-based scaling
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  # Memory-based scaling  
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  # Custom metrics for request rate
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "100"
  # Custom metrics for tenant load
  - type: Pods
    pods:
      metric:
        name: active_tenants_per_pod
      target:
        type: AverageValue
        averageValue: "50"
  
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300  # 5 minutes
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
      - type: Pods
        value: 1
        periodSeconds: 60
      selectPolicy: Min
    scaleUp:
      stabilizationWindowSeconds: 60   # 1 minute
      policies:
      - type: Percent
        value: 100
        periodSeconds: 60
      - type: Pods
        value: 5
        periodSeconds: 60
      selectPolicy: Max
```

**Vertical Pod Autoscaler (VPA):**
```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: leanvibe-backend-vpa
  namespace: leanvibe-production
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: leanvibe-backend
  updatePolicy:
    updateMode: "Auto"  # Auto-update resource requests
  resourcePolicy:
    containerPolicies:
    - containerName: leanvibe-backend
      minAllowed:
        cpu: 100m
        memory: 256Mi
      maxAllowed:
        cpu: 4
        memory: 8Gi
      mode: Auto
```

## Enterprise SLA Management

### Service Level Objectives

#### Enterprise SLA Targets

**Team Tier SLA (99.9% Uptime):**
```python
TEAM_SLA_TARGETS = {
    "availability": {
        "target": 99.9,           # 99.9% uptime
        "downtime_budget": "43.8 minutes/month",
        "measurement_window": "calendar_month"
    },
    "performance": {
        "api_response_time_p95": 500,    # 500ms 95th percentile
        "api_response_time_p99": 1000,   # 1000ms 99th percentile
        "database_query_time_p95": 100   # 100ms 95th percentile
    },
    "recovery": {
        "rpo": 60,               # 1 hour Recovery Point Objective
        "rto": 240               # 4 hour Recovery Time Objective
    }
}
```

**Enterprise Tier SLA (99.95% Uptime):**
```python
ENTERPRISE_SLA_TARGETS = {
    "availability": {
        "target": 99.95,          # 99.95% uptime
        "downtime_budget": "21.9 minutes/month",
        "measurement_window": "calendar_month"
    },
    "performance": {
        "api_response_time_p95": 200,    # 200ms 95th percentile
        "api_response_time_p99": 500,    # 500ms 99th percentile
        "database_query_time_p95": 50    # 50ms 95th percentile
    },
    "recovery": {
        "rpo": 5,                # 5 minute Recovery Point Objective
        "rto": 60                # 1 hour Recovery Time Objective
    },
    "support": {
        "response_time_sev1": 15,        # 15 minutes for SEV1
        "response_time_sev2": 60,        # 1 hour for SEV2
        "escalation_time": 30            # 30 minutes to escalate
    }
}
```

#### SLA Monitoring and Reporting

**Automated SLA Monitoring:**
```python
class SLAMonitor:
    def __init__(self):
        self.prometheus_client = PrometheusClient()
        self.alertmanager_client = AlertmanagerClient()
        
    async def calculate_monthly_sla_compliance(self, tenant_id: UUID) -> Dict:
        """Calculate SLA compliance for tenant"""
        
        tenant = await tenant_service.get_tenant(tenant_id)
        sla_targets = self.get_sla_targets(tenant.plan)
        
        # Calculate availability SLA
        uptime_metrics = await self.prometheus_client.query_range(
            query='up{service="leanvibe-backend"}',
            start_time=datetime.utcnow().replace(day=1),  # Start of month
            end_time=datetime.utcnow()
        )
        
        availability = self.calculate_availability(uptime_metrics)
        
        # Calculate performance SLA
        response_time_metrics = await self.prometheus_client.query_range(
            query='histogram_quantile(0.95, http_request_duration_seconds_bucket)',
            start_time=datetime.utcnow().replace(day=1),
            end_time=datetime.utcnow()
        )
        
        p95_response_time = self.calculate_p95_response_time(response_time_metrics)
        
        # Calculate SLA compliance
        sla_compliance = {
            "tenant_id": str(tenant_id),
            "plan": tenant.plan.value,
            "measurement_period": {
                "start": datetime.utcnow().replace(day=1).isoformat(),
                "end": datetime.utcnow().isoformat()
            },
            "availability": {
                "target": sla_targets["availability"]["target"],
                "actual": availability,
                "compliant": availability >= sla_targets["availability"]["target"],
                "downtime_budget_used": self.calculate_downtime_budget_used(availability)
            },
            "performance": {
                "p95_response_time_target": sla_targets["performance"]["api_response_time_p95"],
                "p95_response_time_actual": p95_response_time,
                "compliant": p95_response_time <= sla_targets["performance"]["api_response_time_p95"]
            },
            "overall_sla_compliance": self.calculate_overall_compliance(availability, p95_response_time, sla_targets)
        }
        
        # Store SLA metrics
        await self.store_sla_metrics(sla_compliance)
        
        # Alert if SLA is breached
        if not sla_compliance["overall_sla_compliance"]:
            await self.alert_sla_breach(tenant_id, sla_compliance)
        
        return sla_compliance
    
    async def generate_sla_report(self, tenant_id: UUID, period: str = "monthly") -> Dict:
        """Generate comprehensive SLA report"""
        
        report = {
            "report_id": str(uuid4()),
            "tenant_id": str(tenant_id),
            "report_period": period,
            "generated_at": datetime.utcnow().isoformat(),
            "sla_summary": await self.calculate_monthly_sla_compliance(tenant_id),
            "incident_summary": await self.get_incident_summary(tenant_id, period),
            "performance_trends": await self.get_performance_trends(tenant_id, period),
            "recommendations": await self.generate_sla_recommendations(tenant_id)
        }
        
        # Store report
        await self.store_sla_report(report)
        
        # Send to customer success team for enterprise customers
        tenant = await tenant_service.get_tenant(tenant_id)
        if tenant.plan == TenantPlan.ENTERPRISE:
            await self.notify_customer_success_team(report)
        
        return report
```

### Support and Escalation

**Enterprise Customer Support:**
- **Response Time**: <1 hour for critical issues, <4 hours for non-critical
- **Escalation Path**: On-call Engineer → Engineering Manager → CTO → CEO
- **Support Channels**: Dedicated Slack channel, phone support, email support
- **Account Management**: Dedicated Customer Success Manager for enterprise accounts

### Contact Enterprise Operations Support

**Technical Operations:**
- **Email**: ops-support@leanvibe.ai  
- **Phone**: +1 (555) 123-4567 ext. 1
- **Emergency**: +1 (555) 123-4567 ext. 911
- **Slack**: #enterprise-operations in LeanVibe Community

**Platform Architecture:**
- **Email**: platform-engineering@leanvibe.ai
- **Scheduling**: [Book Architecture Review](https://calendly.com/leanvibe/platform-review)
- **Documentation**: [Operations Knowledge Base](https://docs.leanvibe.ai/operations)

**Site Reliability Engineering:**
- **Email**: sre@leanvibe.ai
- **Incident Response**: incident-response@leanvibe.ai
- **Post-Incident Reviews**: pir@leanvibe.ai

---

**Ready for production deployment?** Contact our platform engineering team for personalized deployment assistance and ensure reliable, scalable operations with comprehensive monitoring and enterprise-grade SLA compliance.

This comprehensive guide provides enterprise-grade production deployment and operations procedures with the reliability, scalability, and monitoring capabilities required for large-scale SaaS platform operations.