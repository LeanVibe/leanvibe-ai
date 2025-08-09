# LeanVibe Enterprise Monitoring & Alerting Playbook

## Table of Contents
1. [Monitoring Overview](#monitoring-overview)
2. [Key Metrics and Thresholds](#key-metrics-and-thresholds)
3. [Alert Response Procedures](#alert-response-procedures)
4. [Dashboard Guide](#dashboard-guide)
5. [Log Analysis](#log-analysis)
6. [Performance Troubleshooting](#performance-troubleshooting)
7. [Business Metrics](#business-metrics)
8. [Monitoring Maintenance](#monitoring-maintenance)

## Monitoring Overview

LeanVibe's monitoring stack provides comprehensive observability across application, infrastructure, and business metrics. Our monitoring supports enterprise SLA commitments and enables proactive issue detection.

### Monitoring Stack Components
- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboards
- **AlertManager**: Alert routing and escalation
- **Loki**: Log aggregation (future implementation)
- **Jaeger**: Distributed tracing (future implementation)

### Monitoring Principles
1. **Proactive Detection**: Identify issues before customers are affected
2. **Actionable Alerts**: Every alert must have a clear response procedure
3. **Business Context**: Technical metrics tied to business impact
4. **SLA Tracking**: Continuous monitoring of enterprise SLA commitments

## Key Metrics and Thresholds

### Application Performance Metrics

#### API Response Time
```promql
# 95th percentile response time
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Thresholds:
# - Enterprise Tier: >200ms (Warning), >500ms (Critical)
# - Team Tier: >500ms (Warning), >1s (Critical)
# - Developer Tier: >1s (Warning), >2s (Critical)
```

#### API Error Rate
```promql
# Error rate percentage
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) * 100

# Thresholds:
# - Warning: >1% error rate
# - Critical: >5% error rate
```

#### Throughput
```promql
# Requests per second
rate(http_requests_total[5m])

# Thresholds:
# - Warning: <100 RPS (unexpectedly low)
# - Critical: <10 RPS (service degradation)
```

### Infrastructure Metrics

#### CPU Usage
```promql
# Node CPU utilization
100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# Pod CPU utilization
rate(container_cpu_usage_seconds_total[5m]) * 100

# Thresholds:
# - Warning: >80% sustained for 10 minutes
# - Critical: >95% sustained for 5 minutes
```

#### Memory Usage
```promql
# Node memory utilization
(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100

# Pod memory utilization
container_memory_usage_bytes / container_spec_memory_limit_bytes * 100

# Thresholds:
# - Warning: >80% memory usage
# - Critical: >95% memory usage
```

#### Disk Usage
```promql
# Disk utilization
(1 - (node_filesystem_avail_bytes / node_filesystem_size_bytes)) * 100

# Thresholds:
# - Warning: >85% disk usage
# - Critical: >95% disk usage
```

### Database Metrics

#### Neo4j Connection Count
```promql
# Active connections
neo4j_bolt_connections_opened_total - neo4j_bolt_connections_closed_total

# Thresholds:
# - Warning: >80% of max connections
# - Critical: >95% of max connections
```

#### Neo4j Query Performance
```promql
# Slow queries per second
rate(neo4j_cypher_queries_total{quantile="0.95"}[5m])

# Thresholds:
# - Warning: >500ms 95th percentile
# - Critical: >2s 95th percentile
```

### Cache Metrics

#### Redis Hit Rate
```promql
# Cache hit rate percentage
redis_keyspace_hits_total / (redis_keyspace_hits_total + redis_keyspace_misses_total) * 100

# Thresholds:
# - Warning: <85% hit rate
# - Critical: <70% hit rate
```

#### Redis Memory Usage
```promql
# Memory utilization
redis_memory_used_bytes / redis_memory_max_bytes * 100

# Thresholds:
# - Warning: >80% memory usage
# - Critical: >95% memory usage
```

### Business Metrics

#### Active Tenants
```promql
# Current active tenants
sum(active_tenants_total)

# Thresholds:
# - Warning: 10% decrease from previous week
# - Critical: 25% decrease from previous week
```

#### Monthly Recurring Revenue (MRR)
```promql
# Current MRR
monthly_recurring_revenue_usd

# Thresholds:
# - Warning: 5% decrease from previous month
# - Critical: 15% decrease from previous month
```

#### API Usage by Tier
```promql
# Requests per tier
sum(rate(http_requests_total[5m])) by (tenant_tier)

# Monitor for unusual patterns that might indicate issues
```

## Alert Response Procedures

### High-Priority Alerts

#### API Response Time Alert
**Alert**: `LeanVibeHighResponseTime`
**Severity**: Warning/Critical
**SLA Impact**: Direct impact on customer experience

**Response Steps**:
1. **Immediate Assessment** (2 minutes)
   ```bash
   # Check current performance
   curl -s -w "%{time_total}\n" -o /dev/null https://api.leanvibe.ai/health
   
   # Check Grafana dashboard
   open https://grafana.leanvibe.ai/d/leanvibe-overview
   ```

2. **Investigation** (5 minutes)
   ```bash
   # Check application logs
   kubectl logs -l app.kubernetes.io/name=leanvibe -n leanvibe-production --tail=100 | grep -i error
   
   # Check database performance
   kubectl exec deployment/neo4j -n leanvibe-production -- \
     cypher-shell -u neo4j -p $NEO4J_PASSWORD \
     "CALL db.stats() YIELD section, data WHERE section CONTAINS 'query' RETURN section, data"
   ```

3. **Immediate Actions**
   ```bash
   # Scale up application if CPU/memory bound
   kubectl scale deployment leanvibe-backend --replicas=6 -n leanvibe-production
   
   # Clear cache if cache-related
   kubectl exec deployment/redis -n leanvibe-production -- redis-cli -a $REDIS_PASSWORD FLUSHDB
   
   # Restart application if needed (last resort)
   kubectl rollout restart deployment/leanvibe-backend -n leanvibe-production
   ```

#### API Error Rate Alert
**Alert**: `LeanVibeHighErrorRate`
**Severity**: Critical
**SLA Impact**: Service degradation affecting customers

**Response Steps**:
1. **Immediate Triage**
   ```bash
   # Check error types
   kubectl logs -l app.kubernetes.io/name=leanvibe -n leanvibe-production | grep -i "500\|error" | tail -20
   
   # Check specific error patterns
   kubectl logs -l app.kubernetes.io/name=leanvibe -n leanvibe-production | grep -E "(database|timeout|connection)" | tail -10
   ```

2. **Root Cause Analysis**
   ```bash
   # Check database connectivity
   kubectl exec deployment/neo4j -n leanvibe-production -- cypher-shell -u neo4j -p $NEO4J_PASSWORD "RETURN 1"
   
   # Check Redis connectivity
   kubectl exec deployment/redis -n leanvibe-production -- redis-cli -a $REDIS_PASSWORD ping
   
   # Check external service dependencies
   curl -s https://api.stripe.com/v1/account -u $STRIPE_SECRET_KEY:
   ```

3. **Resolution Actions**
   ```bash
   # If database issues
   kubectl rollout restart statefulset/neo4j -n leanvibe-production
   
   # If cache issues
   kubectl rollout restart deployment/redis -n leanvibe-production
   
   # If application issues
   kubectl rollout restart deployment/leanvibe-backend -n leanvibe-production
   ```

### Infrastructure Alerts

#### High CPU Usage
**Alert**: `HighCPUUsage`
**Severity**: Warning/Critical

**Response Steps**:
1. **Identify CPU-intensive pods**
   ```bash
   kubectl top pods -n leanvibe-production --sort-by=cpu
   ```

2. **Scale up resources**
   ```bash
   # Scale application
   kubectl scale deployment leanvibe-backend --replicas=6 -n leanvibe-production
   
   # Add more nodes if needed (via AWS Auto Scaling Group)
   aws autoscaling set-desired-capacity --auto-scaling-group-name leanvibe-nodes --desired-capacity 6
   ```

#### High Memory Usage
**Alert**: `HighMemoryUsage`
**Severity**: Warning/Critical

**Response Steps**:
1. **Identify memory usage patterns**
   ```bash
   kubectl top pods -n leanvibe-production --sort-by=memory
   kubectl describe pod $HIGH_MEMORY_POD -n leanvibe-production
   ```

2. **Check for memory leaks**
   ```bash
   # Monitor memory usage over time
   kubectl logs $POD_NAME -n leanvibe-production | grep -i "memory\|oom"
   ```

3. **Scale or restart affected pods**
   ```bash
   kubectl delete pod $HIGH_MEMORY_POD -n leanvibe-production
   kubectl scale deployment leanvibe-backend --replicas=6 -n leanvibe-production
   ```

### Database Alerts

#### Neo4j Connection Alert
**Alert**: `Neo4jHighConnections`
**Severity**: Warning/Critical

**Response Steps**:
1. **Check connection pool status**
   ```bash
   kubectl exec deployment/neo4j -n leanvibe-production -- \
     cypher-shell -u neo4j -p $NEO4J_PASSWORD \
     "CALL dbms.listConnections() YIELD connectionId, connector, username RETURN count(*)"
   ```

2. **Increase connection pool size** (if needed)
   ```bash
   kubectl patch configmap leanvibe-config -n leanvibe-production \
     --type merge -p '{"data":{"CONNECTION_POOL_SIZE":"40"}}'
   kubectl rollout restart deployment/leanvibe-backend -n leanvibe-production
   ```

#### Neo4j Performance Alert
**Alert**: `Neo4jSlowQueries`
**Severity**: Warning

**Response Steps**:
1. **Identify slow queries**
   ```bash
   kubectl logs deployment/neo4j -n leanvibe-production | grep "Query slow" | tail -10
   ```

2. **Optimize queries or add indexes**
   ```bash
   # Add missing indexes
   kubectl exec deployment/neo4j -n leanvibe-production -- \
     cypher-shell -u neo4j -p $NEO4J_PASSWORD \
     "CREATE INDEX IF NOT EXISTS FOR (n:Tenant) ON (n.id)"
   ```

### Business Metric Alerts

#### Low Tenant Signup Rate
**Alert**: `LowTenantSignupRate`
**Severity**: Warning
**Business Impact**: Revenue and growth impact

**Response Steps**:
1. **Verify alert accuracy**
   ```bash
   # Check recent signups
   kubectl exec deployment/leanvibe-backend -n leanvibe-production -- \
     python -c "from app.services.tenant_service import get_recent_signups; print(get_recent_signups(24))"
   ```

2. **Check signup flow health**
   ```bash
   # Test signup API
   curl -X POST https://api.leanvibe.ai/api/v1/tenants \
     -H "Content-Type: application/json" \
     -d '{"name":"health-check-'$(date +%s)'","tier":"team","email":"test@example.com"}'
   ```

3. **Notify business stakeholders**
   - Send alert to #business-metrics Slack channel
   - Email customer success team if critical

## Dashboard Guide

### LeanVibe Enterprise Overview Dashboard
**URL**: `https://grafana.leanvibe.ai/d/leanvibe-overview`

**Key Panels**:
- **API Request Rate**: Real-time request volume
- **Response Time (95th percentile)**: Performance SLA tracking
- **Error Rate**: Service reliability indicator
- **Active Tenants**: Business health metric
- **Monthly Recurring Revenue**: Financial health

**Usage**:
- Primary dashboard for on-call engineers
- First place to check during incidents
- Real-time view of system health

### Kubernetes Cluster Overview Dashboard
**URL**: `https://grafana.leanvibe.ai/d/kubernetes-overview`

**Key Panels**:
- **Node CPU/Memory Usage**: Infrastructure health
- **Pod Status**: Application deployment status
- **Network I/O**: Traffic patterns
- **Storage Usage**: Disk utilization

**Usage**:
- Infrastructure-focused troubleshooting
- Capacity planning
- Resource utilization analysis

### Business Metrics Dashboard
**URL**: `https://grafana.leanvibe.ai/d/business-metrics`

**Key Panels**:
- **Tenant Signups (24h)**: Daily growth tracking
- **MRR Trend**: Revenue monitoring
- **Tenant Distribution by Tier**: Customer segmentation
- **Feature Usage**: Product adoption metrics

**Usage**:
- Business stakeholder reviews
- Product decision making
- Customer success analysis

### Database Performance Dashboard
**URL**: `https://grafana.leanvibe.ai/d/database-performance`

**Key Panels**:
- **Query Performance**: Response time trends
- **Connection Pool Usage**: Resource utilization
- **Transaction Volume**: Database load
- **Cache Hit Rates**: Efficiency metrics

## Log Analysis

### Application Log Patterns

#### Error Investigation
```bash
# Recent errors
kubectl logs -l app.kubernetes.io/name=leanvibe -n leanvibe-production | grep -i error | tail -20

# Specific error types
kubectl logs -l app.kubernetes.io/name=leanvibe -n leanvibe-production | grep "500 Internal Server Error"

# Database connection errors
kubectl logs -l app.kubernetes.io/name=leanvibe -n leanvibe-production | grep -i "connection.*failed\|timeout"
```

#### Performance Analysis
```bash
# Slow requests
kubectl logs -l app.kubernetes.io/name=leanvibe -n leanvibe-production | grep "slow_request" | tail -10

# Memory usage patterns
kubectl logs -l app.kubernetes.io/name=leanvibe -n leanvibe-production | grep -i "memory\|gc"
```

### Database Log Analysis
```bash
# Neo4j slow queries
kubectl logs deployment/neo4j -n leanvibe-production | grep "Query slow"

# Neo4j connection issues
kubectl logs deployment/neo4j -n leanvibe-production | grep -i "connection\|timeout"

# Transaction failures
kubectl logs deployment/neo4j -n leanvibe-production | grep -i "transaction.*failed"
```

## Performance Troubleshooting

### Common Performance Issues

#### 1. High API Response Time
**Symptoms**: >95th percentile response time above SLA thresholds

**Investigation**:
```bash
# Check individual component performance
kubectl exec deployment/leanvibe-backend -n leanvibe-production -- \
  curl -s -w "Total: %{time_total}s, Connect: %{time_connect}s, DB: %{time_starttransfer}s\n" \
  -o /dev/null http://localhost:8000/health/db

# Database query analysis
kubectl exec deployment/neo4j -n leanvibe-production -- \
  cypher-shell -u neo4j -p $NEO4J_PASSWORD \
  "CALL db.logs() YIELD level, message WHERE level = 'WARN' RETURN message LIMIT 10"
```

**Solutions**:
- Scale application pods
- Optimize database queries
- Clear and warm caches
- Add database indexes

#### 2. High Memory Usage
**Symptoms**: Pods approaching memory limits, OOM kills

**Investigation**:
```bash
# Memory usage by pod
kubectl top pods -n leanvibe-production --sort-by=memory

# Check for memory leaks
kubectl logs $POD_NAME -n leanvibe-production | grep -i "out of memory\|oom\|memory leak"
```

**Solutions**:
- Increase pod memory limits
- Identify and fix memory leaks
- Optimize memory usage patterns
- Scale horizontally instead of vertically

#### 3. Database Performance Degradation
**Symptoms**: Slow queries, connection timeouts

**Investigation**:
```bash
# Active connections
kubectl exec deployment/neo4j -n leanvibe-production -- \
  cypher-shell -u neo4j -p $NEO4J_PASSWORD \
  "CALL dbms.listConnections() YIELD connectionId RETURN count(connectionId)"

# Query performance
kubectl logs deployment/neo4j -n leanvibe-production | grep -E "took [0-9]+ms" | tail -10
```

**Solutions**:
- Add database indexes
- Optimize expensive queries
- Increase connection pool size
- Consider read replicas

## Business Metrics

### Revenue Tracking
```promql
# Monthly Recurring Revenue growth
increase(monthly_recurring_revenue_usd[30d])

# Revenue by tenant tier
sum(monthly_recurring_revenue_usd) by (tenant_tier)
```

### Customer Health
```promql
# Tenant churn rate
rate(tenant_cancellations_total[24h]) / rate(tenant_signups_total[24h])

# Feature adoption rate
sum(feature_usage_total) by (feature_name) / sum(active_tenants_total)
```

### Product Usage
```promql
# API usage patterns
sum(rate(http_requests_total[5m])) by (endpoint)

# Most used features
topk(10, sum(rate(feature_usage_total[1h])) by (feature_name))
```

## Monitoring Maintenance

### Daily Monitoring Tasks
- [ ] Review overnight alerts and incidents
- [ ] Check dashboard health and data freshness
- [ ] Verify backup completion status
- [ ] Review business metrics trends

### Weekly Monitoring Tasks
- [ ] Review alert accuracy and tune thresholds
- [ ] Analyze performance trends and capacity planning
- [ ] Update runbooks based on recent incidents
- [ ] Check monitoring system health and storage usage

### Monthly Monitoring Tasks
- [ ] Review SLA performance against commitments
- [ ] Update business metric baselines
- [ ] Audit alert configurations and recipients
- [ ] Plan monitoring infrastructure upgrades

### Quarterly Monitoring Tasks
- [ ] Comprehensive monitoring system review
- [ ] Update monitoring strategy based on business changes
- [ ] Review and update escalation procedures
- [ ] Training updates for new team members

### Alert Configuration Management

#### Adding New Alerts
```yaml
# Prometheus alerting rule template
groups:
- name: leanvibe.new.rules
  rules:
  - alert: NewMetricAlert
    expr: new_metric > 100
    for: 5m
    labels:
      severity: warning
      service: leanvibe-backend
    annotations:
      summary: "New metric alert triggered"
      description: "New metric {{ $value }} exceeds threshold"
      runbook_url: "https://github.com/leanvibe/runbooks/new-metric-alert"
```

#### Alert Tuning Process
1. **Monitor alert frequency** - Reduce noise from false positives
2. **Validate business impact** - Ensure alerts correlate with real issues
3. **Test escalation paths** - Verify notifications reach the right people
4. **Update thresholds** - Adjust based on historical data and business requirements

---

**Document Version**: 2.0  
**Last Updated**: January 2024  
**Review Schedule**: Monthly  
**Owner**: SRE Team  

**Monitoring Support**: monitoring@leanvibe.ai  
**Emergency Escalation**: +1-555-MONITOR (+1-555-666-4867)