# LeanVibe Enterprise Deployment Procedures

## Table of Contents
1. [Overview](#overview)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Standard Deployment Procedures](#standard-deployment-procedures)
4. [Emergency Deployment Procedures](#emergency-deployment-procedures)
5. [Rollback Procedures](#rollback-procedures)
6. [Post-Deployment Verification](#post-deployment-verification)
7. [Environment Management](#environment-management)
8. [Troubleshooting Guide](#troubleshooting-guide)

## Overview

This document provides comprehensive procedures for deploying the LeanVibe Enterprise SaaS platform across all environments. All deployments must follow security, quality, and operational best practices to maintain our enterprise SLA commitments.

### Deployment Environments
- **Development**: Continuous deployment from feature branches
- **Staging**: Daily deployments from `develop` branch
- **Production**: Controlled deployments from `main` branch with approval gates

### Key Principles
1. **Zero-Downtime Deployments**: All production deployments use blue-green or canary strategies
2. **Automated Testing**: Full test suite must pass before production deployment
3. **Security First**: All deployments require security scanning and approval
4. **Rollback Ready**: Every deployment must have a tested rollback plan

## Pre-Deployment Checklist

### Development Team Checklist
- [ ] All tests passing in CI/CD pipeline
- [ ] Code review completed and approved
- [ ] Security scan results reviewed and approved
- [ ] Database migrations tested and documented
- [ ] Performance impact assessed
- [ ] Rollback plan prepared and tested
- [ ] Documentation updated
- [ ] Monitoring and alerting configured for new features

### DevOps Team Checklist
- [ ] Infrastructure changes reviewed and approved
- [ ] Kubernetes manifests validated
- [ ] Secrets and configuration updated
- [ ] Backup verification completed
- [ ] Capacity planning reviewed
- [ ] Disaster recovery procedures updated
- [ ] Runbooks updated for new functionality

### Security Team Checklist (for Production)
- [ ] SAST (Static Application Security Testing) passed
- [ ] DAST (Dynamic Application Security Testing) passed
- [ ] Container security scan passed
- [ ] Infrastructure security scan passed
- [ ] Compliance requirements verified
- [ ] Access control changes reviewed

## Standard Deployment Procedures

### 1. Staging Deployment (Automated)

Staging deployments are triggered automatically when code is merged to the `develop` branch.

#### Monitoring the Deployment
```bash
# Watch the GitHub Actions workflow
gh run watch

# Monitor staging environment
kubectl get pods -n leanvibe-staging -w

# Check deployment status
kubectl rollout status deployment/leanvibe-backend -n leanvibe-staging
```

#### Validation Steps
```bash
# Health check
curl -f https://api-staging.leanvibe.ai/health

# Run integration tests
npm run test:integration:staging

# Smoke test critical features
curl -X POST https://api-staging.leanvibe.ai/api/v1/tenants \
  -H "Authorization: Bearer $STAGING_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name": "staging-test", "tier": "team"}'
```

### 2. Production Deployment (Manual Approval)

Production deployments require manual approval and follow a strict process.

#### Step 1: Pre-Deployment Verification
```bash
# Verify staging is healthy
curl -f https://api-staging.leanvibe.ai/health

# Check current production status
kubectl get pods -n leanvibe-production
kubectl top nodes

# Verify backup completion
kubectl get jobs -n leanvibe-backup | grep $(date +%Y%m%d)
```

#### Step 2: Deploy to Production
```bash
# Option A: Via GitHub Actions (Recommended)
gh workflow run production-security.yml \
  --field environment=production \
  --field skip_security_scan=false

# Option B: Manual Deployment (Emergency Only)
# Set up kubectl context
aws eks update-kubeconfig --region us-east-1 --name leanvibe-production

# Update image
kubectl set image deployment/leanvibe-backend \
  leanvibe-backend=ghcr.io/leanvibe/leanvibe-backend:$NEW_TAG \
  -n leanvibe-production

# Monitor rollout
kubectl rollout status deployment/leanvibe-backend -n leanvibe-production --timeout=600s
```

#### Step 3: Blue-Green Deployment Process
```bash
# Create green deployment
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: leanvibe-backend-green
  namespace: leanvibe-production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: leanvibe-backend
      version: green
  template:
    metadata:
      labels:
        app: leanvibe-backend
        version: green
    spec:
      containers:
      - name: leanvibe-backend
        image: ghcr.io/leanvibe/leanvibe-backend:$NEW_TAG
        # ... rest of container spec
EOF

# Wait for green to be ready
kubectl wait --for=condition=Available deployment/leanvibe-backend-green \
  -n leanvibe-production --timeout=600s

# Test green deployment
kubectl port-forward deployment/leanvibe-backend-green 8080:8000 -n leanvibe-production &
curl -f http://localhost:8080/health
kill %1  # Stop port-forward

# Switch traffic to green
kubectl patch service leanvibe-backend -n leanvibe-production \
  -p '{"spec":{"selector":{"version":"green"}}}'

# Monitor for 5 minutes, then remove blue
sleep 300
kubectl delete deployment leanvibe-backend-blue -n leanvibe-production

# Rename green to standard name
kubectl patch deployment leanvibe-backend-green -n leanvibe-production \
  -p '{"metadata":{"name":"leanvibe-backend"}}'
```

### 3. Canary Deployment (Gradual Rollout)

For high-risk changes, use canary deployments to minimize impact.

```bash
# Deploy canary with 10% traffic
kubectl apply -f - <<EOF
apiVersion: v1
kind: Service
metadata:
  name: leanvibe-backend-canary
  namespace: leanvibe-production
spec:
  selector:
    app: leanvibe-backend
    version: canary
  ports:
  - port: 80
    targetPort: 8000
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: leanvibe-backend-canary
  namespace: leanvibe-production
spec:
  replicas: 1  # 10% of normal traffic
  selector:
    matchLabels:
      app: leanvibe-backend
      version: canary
  template:
    metadata:
      labels:
        app: leanvibe-backend
        version: canary
    spec:
      containers:
      - name: leanvibe-backend
        image: ghcr.io/leanvibe/leanvibe-backend:$NEW_TAG
        # ... container spec
EOF

# Monitor canary metrics for 30 minutes
# If successful, gradually increase traffic:
# 10% -> 25% -> 50% -> 100%

# Scale canary up and stable down
kubectl scale deployment leanvibe-backend-canary --replicas=2 -n leanvibe-production
kubectl scale deployment leanvibe-backend --replicas=2 -n leanvibe-production

# Final switch: 100% to canary
kubectl scale deployment leanvibe-backend --replicas=0 -n leanvibe-production
kubectl scale deployment leanvibe-backend-canary --replicas=3 -n leanvibe-production
```

### 4. Database Migrations

Database migrations require special handling to prevent data loss.

#### Step 1: Backup Database
```bash
# Trigger emergency backup
kubectl create job --from=cronjob/neo4j-backup \
  migration-backup-$(date +%Y%m%d%H%M) \
  -n leanvibe-backup

# Wait for backup completion
kubectl wait --for=condition=complete \
  job/migration-backup-$(date +%Y%m%d%H%M) \
  -n leanvibe-backup --timeout=1800s
```

#### Step 2: Apply Migration
```bash
# Create migration job
kubectl apply -f - <<EOF
apiVersion: batch/v1
kind: Job
metadata:
  name: database-migration-$(date +%Y%m%d%H%M)
  namespace: leanvibe-production
spec:
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: migration
        image: ghcr.io/leanvibe/leanvibe-backend:$NEW_TAG
        command: ["python", "-m", "alembic", "upgrade", "head"]
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: leanvibe-database-secrets
              key: DATABASE_URL
EOF

# Monitor migration
kubectl logs job/database-migration-$(date +%Y%m%d%H%M) -n leanvibe-production -f
```

#### Step 3: Validate Migration
```bash
# Check database schema
kubectl exec deployment/neo4j -n leanvibe-production -- \
  cypher-shell -u neo4j -p $NEO4J_PASSWORD \
  "CALL db.schema.visualization()"

# Run validation queries
kubectl exec deployment/neo4j -n leanvibe-production -- \
  cypher-shell -u neo4j -p $NEO4J_PASSWORD \
  "MATCH (n) RETURN labels(n), count(n)"
```

## Emergency Deployment Procedures

For critical security fixes or production outages, emergency deployments bypass normal approval processes.

### Prerequisites for Emergency Deployment
- **Security Officer Approval**: Required for all emergency deployments
- **Incident Commander**: Must be assigned and leading the response
- **Communication**: Stakeholders notified of emergency deployment

### Emergency Deployment Steps
```bash
# 1. Immediate deployment with security scan bypass
gh workflow run production-security.yml \
  --field environment=production \
  --field skip_security_scan=true

# 2. Manual emergency deployment
kubectl set image deployment/leanvibe-backend \
  leanvibe-backend=ghcr.io/leanvibe/leanvibe-backend:emergency-$TAG \
  -n leanvibe-production

# 3. Force immediate rollout
kubectl rollout restart deployment/leanvibe-backend -n leanvibe-production

# 4. Monitor deployment
kubectl rollout status deployment/leanvibe-backend -n leanvibe-production
```

### Post-Emergency Procedures
1. **Immediate Security Scan**: Run full security scan within 4 hours
2. **Change Review**: Engineering team reviews emergency changes within 24 hours
3. **Process Improvement**: Document lessons learned and update procedures

## Rollback Procedures

Every deployment must have a tested rollback plan. Rollbacks should complete within 5 minutes.

### Automated Rollback (Recommended)
```bash
# Rollback to previous version
kubectl rollout undo deployment/leanvibe-backend -n leanvibe-production

# Check rollback status
kubectl rollout status deployment/leanvibe-backend -n leanvibe-production

# Verify rollback success
kubectl get pods -l app=leanvibe-backend -n leanvibe-production
```

### Manual Rollback
```bash
# Get deployment history
kubectl rollout history deployment/leanvibe-backend -n leanvibe-production

# Rollback to specific revision
kubectl rollout undo deployment/leanvibe-backend \
  --to-revision=2 \
  -n leanvibe-production
```

### Database Rollback (Critical)
```bash
# Stop application to prevent data corruption
kubectl scale deployment leanvibe-backend --replicas=0 -n leanvibe-production

# Restore from backup
kubectl apply -f - <<EOF
apiVersion: batch/v1
kind: Job
metadata:
  name: database-rollback-$(date +%Y%m%d%H%M)
  namespace: leanvibe-backup
spec:
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: rollback
        image: leanvibe-backup-tools:latest
        command: ["/scripts/neo4j-recovery.sh"]
        args: ["$BACKUP_NAME", "leanvibe-production", "full"]
        env:
        - name: S3_BACKUP_BUCKET
          value: "leanvibe-backups-prod-us-east-1"
        # ... other environment variables
EOF

# Wait for rollback completion
kubectl wait --for=condition=complete \
  job/database-rollback-$(date +%Y%m%d%H%M) \
  -n leanvibe-backup --timeout=3600s

# Restart application
kubectl scale deployment leanvibe-backend --replicas=3 -n leanvibe-production
```

## Post-Deployment Verification

After every deployment, run comprehensive verification tests.

### Automated Health Checks
```bash
# Run health check suite
./scripts/health-check-suite.sh production

# Specific checks
curl -f https://api.leanvibe.ai/health
curl -f https://api.leanvibe.ai/health/db
curl -f https://api.leanvibe.ai/health/cache
```

### Business Logic Verification
```bash
# Test tenant creation
curl -X POST https://api.leanvibe.ai/api/v1/tenants \
  -H "Authorization: Bearer $PROD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name": "deployment-test-'$(date +%s)'", "tier": "team"}'

# Test authentication
curl -X POST https://api.leanvibe.ai/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@leanvibe.ai", "password": "secure-password"}'

# Test billing integration
curl -X GET https://api.leanvibe.ai/api/v1/billing/health \
  -H "Authorization: Bearer $PROD_API_KEY"
```

### Performance Validation
```bash
# Run performance tests
k6 run --vus 50 --duration 2m performance-tests/api-load-test.js

# Check response time metrics
curl -s "https://grafana.leanvibe.ai/api/datasources/proxy/1/api/v1/query?query=histogram_quantile(0.95,%20rate(http_request_duration_seconds_bucket[5m]))" | jq '.data.result[0].value[1]'
```

### Customer Impact Assessment
```bash
# Check error rates
curl -s "https://grafana.leanvibe.ai/api/datasources/proxy/1/api/v1/query?query=rate(http_requests_total{status=~'5..'}[5m])" | jq '.data.result[0].value[1]'

# Validate SLA metrics
./scripts/validate-sla-metrics.sh

# Check customer-facing services
curl -f https://app.leanvibe.ai
curl -f https://docs.leanvibe.ai
```

## Environment Management

### Development Environment
- **Auto-deployment**: Every push to feature branches
- **Testing**: Automated test suite runs on every commit
- **Data**: Synthetic test data, reset nightly
- **Monitoring**: Basic metrics and logs

### Staging Environment
- **Deployment**: Daily from `develop` branch
- **Testing**: Full integration test suite
- **Data**: Production-like dataset (anonymized)
- **Monitoring**: Production-like monitoring setup

### Production Environment
- **Deployment**: Manual approval required
- **Testing**: Comprehensive validation before and after deployment
- **Data**: Real customer data with full compliance measures
- **Monitoring**: Complete observability stack with alerting

### Environment Promotion Process
```
Feature Branch → Development → Staging → Production
     ↓              ↓            ↓           ↓
  Unit Tests    Integration   E2E Tests   Manual
                   Tests                   Approval
```

## Troubleshooting Guide

### Common Deployment Issues

#### 1. Pod Stuck in Pending State
```bash
# Check node resources
kubectl describe node

# Check pod events
kubectl describe pod $POD_NAME -n leanvibe-production

# Common solutions:
kubectl scale deployment leanvibe-backend --replicas=2 -n leanvibe-production
kubectl delete pod $POD_NAME -n leanvibe-production  # Force reschedule
```

#### 2. Image Pull Errors
```bash
# Check image exists
docker manifest inspect ghcr.io/leanvibe/leanvibe-backend:$TAG

# Check registry credentials
kubectl get secret regcred -n leanvibe-production -o yaml

# Recreate registry secret if needed
kubectl create secret docker-registry regcred \
  --docker-server=ghcr.io \
  --docker-username=$GITHUB_USERNAME \
  --docker-password=$GITHUB_TOKEN \
  -n leanvibe-production
```

#### 3. Database Migration Failures
```bash
# Check migration logs
kubectl logs job/$MIGRATION_JOB_NAME -n leanvibe-production

# Manual migration rollback
kubectl exec deployment/neo4j -n leanvibe-production -- \
  cypher-shell -u neo4j -p $NEO4J_PASSWORD \
  "CALL apoc.schema.assert({}, {})"

# Restore from backup
kubectl create job --from=cronjob/neo4j-backup \
  migration-recovery-$(date +%Y%m%d%H%M) \
  -n leanvibe-backup
```

#### 4. Service Mesh Issues
```bash
# Check Istio configuration
kubectl get virtualservice -n leanvibe-production
kubectl get destinationrule -n leanvibe-production

# Restart Istio proxy
kubectl rollout restart deployment/leanvibe-backend -n leanvibe-production

# Check service mesh metrics
kubectl exec deployment/istio-proxy -n istio-system -- \
  pilot-agent request GET stats/prometheus | grep leanvibe
```

### Rollback Decision Matrix

| Issue Type | Severity | Rollback Decision | Timeline |
|------------|----------|-------------------|----------|
| Performance Degradation | >50% slower | Immediate rollback | <5 minutes |
| Error Rate Spike | >5% error rate | Immediate rollback | <5 minutes |
| Security Vulnerability | Any level | Immediate rollback | <2 minutes |
| Feature Bug | Non-critical | Consider rollback | <15 minutes |
| Database Issue | Data at risk | Emergency rollback + restore | <10 minutes |

### Communication During Deployments

#### Slack Channels
- **#deployments**: All deployment notifications
- **#incidents**: If deployment issues arise
- **#engineering**: Engineering team updates
- **#customer-success**: Customer impact communications

#### Status Page Updates
```
🔄 MAINTENANCE: We are deploying updates to improve performance and add new features. No downtime is expected, but some requests may experience slightly longer response times.

Started: 14:00 UTC
Expected Duration: 30 minutes
```

#### Post-Deployment Notification
```
✅ DEPLOYMENT COMPLETE: Successfully deployed version 2.4.1 with improved API performance and enhanced security features. All systems operating normally.

Completed: 14:25 UTC
Version: 2.4.1
Changes: Performance improvements, security enhancements, bug fixes
```

---

**Document Version**: 1.8  
**Last Updated**: January 2024  
**Review Schedule**: Monthly  
**Owner**: DevOps Team  

**Emergency Contact**: +1-555-DEPLOY (+1-555-337-5696)  
**Escalation**: escalation@leanvibe.ai