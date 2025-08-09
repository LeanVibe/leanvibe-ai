# LeanVibe Enterprise Incident Response Runbook

## Table of Contents
1. [Overview](#overview)
2. [Incident Classification](#incident-classification)
3. [Response Procedures](#response-procedures)
4. [Common Incidents](#common-incidents)
5. [Escalation Matrix](#escalation-matrix)
6. [Post-Incident Procedures](#post-incident-procedures)
7. [Contact Information](#contact-information)

## Overview

This runbook provides comprehensive procedures for responding to production incidents in the LeanVibe Enterprise SaaS platform. All incidents must be handled according to established SLA requirements and customer commitments.

### SLA Targets by Tier
- **Enterprise Tier**: 99.95% uptime, <200ms response time, <1 hour RTO
- **Team Tier**: 99.9% uptime, <500ms response time, <4 hour RTO
- **Developer Tier**: 99.5% uptime, <1s response time, <8 hour RTO

### Key Principles
1. **Customer First**: Minimize customer impact above all else
2. **Communicate Early**: Internal and external communication within 15 minutes
3. **Document Everything**: Record all actions and decisions for learning
4. **Learn and Improve**: Conduct blameless post-incident reviews

## Incident Classification

### P0 - Critical (RTO: 1 hour)
**Definition**: Complete service outage or data loss affecting all customers
**Examples**:
- API completely down (5+ minute outage)
- Database corruption or unavailability
- Security breach or data leak
- Payment system failure affecting billing

**Immediate Actions**:
1. Page on-call engineer immediately
2. Create incident war room (Slack #incident-p0)
3. Notify executives within 15 minutes
4. Begin customer communications within 30 minutes

### P1 - High (RTO: 4 hours)
**Definition**: Significant degradation affecting majority of customers
**Examples**:
- Severe performance degradation (>5x normal response time)
- Authentication system issues
- Critical feature completely unavailable
- Database performance severely degraded

**Immediate Actions**:
1. Page on-call engineer within 5 minutes
2. Create incident channel (Slack #incident-p1)
3. Notify engineering manager within 30 minutes
4. Begin customer communications within 1 hour

### P2 - Medium (RTO: 8 hours)
**Definition**: Moderate impact affecting subset of customers
**Examples**:
- Non-critical feature unavailable
- Performance degradation for specific tenant tier
- Partial API functionality issues
- Monitoring/alerting system issues

**Immediate Actions**:
1. Alert on-call engineer within 15 minutes
2. Create incident ticket
3. Notify team lead within 2 hours
4. Consider customer communications

### P3 - Low (RTO: 24 hours)
**Definition**: Minor issues with minimal customer impact
**Examples**:
- UI cosmetic issues
- Non-critical background job failures
- Development environment issues
- Minor monitoring gaps

**Immediate Actions**:
1. Create ticket for next business day
2. Document in weekly team review
3. No immediate escalation required

## Response Procedures

### Initial Response (First 15 Minutes)

#### 1. Acknowledge and Assess
```bash
# Acknowledge the alert immediately
curl -X POST https://api.pagerduty.com/incidents/{incident_id}/acknowledge

# Quick health assessment
kubectl get pods -n leanvibe-production
kubectl get services -n leanvibe-production
curl -s https://api.leanvibe.ai/health | jq
```

#### 2. Create Incident Channel
```
# Slack command
/create-incident P1 "API response time degradation"

# Invite key stakeholders
/invite @oncall-engineer @engineering-manager @customer-success
```

#### 3. Initial Investigation
```bash
# Check application logs
kubectl logs -l app.kubernetes.io/name=leanvibe -n leanvibe-production --tail=100

# Check metrics in Grafana
open https://grafana.leanvibe.ai/d/leanvibe-overview

# Check database status
kubectl exec deployment/neo4j -n leanvibe-production -- cypher-shell -u neo4j -p $NEO4J_PASSWORD "CALL dbms.components()"
```

### Communication Templates

#### Internal Communication (Slack)
```
🚨 INCIDENT: [P1] API Response Time Degradation
Status: INVESTIGATING
Start Time: 2024-01-15 14:30 UTC
Impact: 50% of API requests experiencing 5x normal latency
Investigation: Checking database performance and connection pools
Next Update: 15 minutes
Incident Commander: @jane.doe
```

#### Customer Communication (Status Page)
```
🔍 INVESTIGATING: We are investigating reports of slower response times for some API requests. We have identified the cause and are working on a resolution. We'll provide updates every 30 minutes.

Posted: 14:35 UTC
Next Update: 15:05 UTC
```

### Escalation Triggers

#### Automatic Escalation to P0
- Any P1 incident lasting >2 hours
- Customer data at risk
- Security implications identified
- Media/social media attention

#### Management Notification
- P0: Immediate (within 15 minutes)
- P1: Within 1 hour
- P2: Next business day summary
- P3: Weekly summary

## Common Incidents

### 1. API Performance Degradation

#### Symptoms
- Increased response times (>2x normal)
- Timeout errors
- Customer complaints

#### Investigation Steps
```bash
# Check application metrics
kubectl top pods -n leanvibe-production

# Review recent deployments
kubectl rollout history deployment/leanvibe-backend -n leanvibe-production

# Check database performance
kubectl exec deployment/neo4j -n leanvibe-production -- \
  cypher-shell -u neo4j -p $NEO4J_PASSWORD \
  "CALL db.stats() YIELD section, data RETURN section, data"

# Check cache hit rates
kubectl exec deployment/redis -n leanvibe-production -- \
  redis-cli -a $REDIS_PASSWORD INFO stats | grep cache_hit_rate
```

#### Common Resolutions
1. **Database Query Optimization**
   ```bash
   # Identify slow queries
   kubectl logs deployment/neo4j -n leanvibe-production | grep "Query slow"
   
   # Add missing indexes if identified
   kubectl exec deployment/neo4j -n leanvibe-production -- \
     cypher-shell -u neo4j -p $NEO4J_PASSWORD \
     "CREATE INDEX IF NOT EXISTS FOR (n:Tenant) ON (n.id)"
   ```

2. **Scale Application Pods**
   ```bash
   # Temporary scaling
   kubectl scale deployment leanvibe-backend --replicas=6 -n leanvibe-production
   
   # Monitor improvement
   watch kubectl get hpa -n leanvibe-production
   ```

3. **Restart Services** (Last Resort)
   ```bash
   # Rolling restart
   kubectl rollout restart deployment/leanvibe-backend -n leanvibe-production
   kubectl rollout status deployment/leanvibe-backend -n leanvibe-production
   ```

### 2. Database Connection Issues

#### Symptoms
- Database connection errors
- Connection pool exhaustion
- Neo4j unavailable errors

#### Investigation Steps
```bash
# Check Neo4j status
kubectl get pods -l app.kubernetes.io/name=neo4j -n leanvibe-production

# Check connection counts
kubectl exec deployment/neo4j -n leanvibe-production -- \
  cypher-shell -u neo4j -p $NEO4J_PASSWORD \
  "CALL dbms.listConnections() YIELD connectionId, connector, username, userAgent, serverAddress, clientAddress"

# Review application connection pool settings
kubectl get configmap leanvibe-config -n leanvibe-production -o yaml
```

#### Common Resolutions
1. **Increase Connection Pool Size**
   ```bash
   kubectl patch configmap leanvibe-config -n leanvibe-production --type merge -p '{"data":{"CONNECTION_POOL_SIZE":"30"}}'
   kubectl rollout restart deployment/leanvibe-backend -n leanvibe-production
   ```

2. **Restart Database** (If Unresponsive)
   ```bash
   # Save current state first
   kubectl exec deployment/neo4j -n leanvibe-production -- \
     neo4j-admin backup --backup-dir=/tmp/emergency-backup --name=emergency

   # Restart Neo4j
   kubectl rollout restart statefulset/neo4j -n leanvibe-production
   kubectl rollout status statefulset/neo4j -n leanvibe-production
   ```

### 3. Authentication/Authorization Issues

#### Symptoms
- Users cannot log in
- "Unauthorized" errors
- SSO integration failures

#### Investigation Steps
```bash
# Check auth service logs
kubectl logs deployment/leanvibe-backend -n leanvibe-production | grep -i auth

# Test authentication endpoint
curl -X POST https://api.leanvibe.ai/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test"}'

# Check SSO provider status
curl -s https://your-sso-provider.com/health
```

#### Common Resolutions
1. **Restart Auth Service**
   ```bash
   kubectl rollout restart deployment/leanvibe-backend -n leanvibe-production
   ```

2. **Check SSO Configuration**
   ```bash
   kubectl get secret leanvibe-secrets -n leanvibe-production -o yaml
   # Verify SSO credentials are correct
   ```

### 4. Payment/Billing Issues

#### Symptoms
- Payment processing failures
- Webhook delivery failures
- Subscription status errors

#### Investigation Steps
```bash
# Check billing service logs
kubectl logs deployment/leanvibe-backend -n leanvibe-production | grep -i billing

# Check Stripe webhook status
curl https://api.stripe.com/v1/webhook_endpoints \
  -u $STRIPE_SECRET_KEY: | jq '.data[].status'

# Review recent billing events
kubectl logs deployment/leanvibe-backend -n leanvibe-production | grep "webhook_received"
```

#### Common Resolutions
1. **Retry Failed Webhooks**
   ```bash
   # Access Stripe dashboard to retry webhooks
   # Or programmatically retry billing events
   kubectl exec deployment/leanvibe-backend -n leanvibe-production -- \
     python -c "from app.services.billing_service import retry_failed_events; retry_failed_events()"
   ```

### 5. Cache/Redis Issues

#### Symptoms
- High cache miss rates
- Redis connection errors
- Session management issues

#### Investigation Steps
```bash
# Check Redis status
kubectl get pods -l app.kubernetes.io/name=redis -n leanvibe-production

# Check Redis memory usage
kubectl exec deployment/redis -n leanvibe-production -- \
  redis-cli -a $REDIS_PASSWORD INFO memory

# Check cache hit rates
kubectl exec deployment/redis -n leanvibe-production -- \
  redis-cli -a $REDIS_PASSWORD INFO stats | grep cache_hit
```

#### Common Resolutions
1. **Clear Problematic Cache Keys**
   ```bash
   kubectl exec deployment/redis -n leanvibe-production -- \
     redis-cli -a $REDIS_PASSWORD FLUSHDB
   ```

2. **Restart Redis** (If Unresponsive)
   ```bash
   kubectl rollout restart deployment/redis -n leanvibe-production
   kubectl rollout status deployment/redis -n leanvibe-production
   ```

## Escalation Matrix

### On-Call Rotation
| Role | Primary | Secondary | Manager |
|------|---------|-----------|---------|
| **Site Reliability** | John Smith (+1-555-0101) | Jane Doe (+1-555-0102) | Mike Johnson (+1-555-0103) |
| **Backend Engineering** | Sarah Wilson (+1-555-0201) | Tom Brown (+1-555-0202) | Lisa Chen (+1-555-0203) |
| **DevOps** | Alex Rodriguez (+1-555-0301) | Sam Taylor (+1-555-0302) | Chris Lee (+1-555-0303) |

### Escalation Timeline
- **0-15 minutes**: On-call engineer responds
- **15-30 minutes**: Incident commander assigned
- **30-60 minutes**: Engineering manager notified (P1) or CTO (P0)
- **60+ minutes**: VP Engineering and CEO notified (P0 only)

### External Escalations
- **Customer Success**: For customer-facing impacts
- **Security Team**: For any security implications
- **Legal/Compliance**: For data breach or compliance issues
- **Public Relations**: For media attention or social media escalation

## Post-Incident Procedures

### Immediate Post-Resolution (Within 4 Hours)
1. **Update Status Page**
   ```
   ✅ RESOLVED: The API performance issues have been resolved. All services are operating normally. We will continue monitoring and provide a detailed incident report within 24 hours.
   
   Resolved: 16:45 UTC
   Duration: 2h 15m
   ```

2. **Internal Incident Closure**
   ```
   📋 INCIDENT RESOLVED: [P1] API Response Time Degradation
   
   Resolution: Database query optimization and connection pool tuning
   Duration: 2h 15m
   Root Cause: Unoptimized query introduced in recent release
   Next Steps: Post-incident review scheduled for tomorrow 10 AM
   ```

### Post-Incident Review (Within 24 Hours)
1. **Schedule blameless postmortem meeting**
2. **Gather timeline of events and decisions**
3. **Identify contributing factors and root causes**
4. **Document lessons learned and action items**
5. **Update runbooks and procedures**

### Incident Report Template
```markdown
# Incident Report: API Performance Degradation

## Summary
On January 15, 2024, LeanVibe experienced API performance degradation affecting 50% of requests from 14:30 to 16:45 UTC.

## Impact
- **Duration**: 2 hours 15 minutes
- **Affected Services**: Main API, tenant management
- **Customer Impact**: 50% of API requests experienced 5x normal latency
- **Revenue Impact**: Estimated $12K in potential lost revenue

## Timeline
- **14:30**: Automated alerts triggered for high response times
- **14:32**: On-call engineer acknowledged and began investigation
- **14:35**: Customer communication posted on status page
- **15:00**: Root cause identified as database query inefficiency
- **15:30**: Database indexes added, performance improving
- **16:45**: Full service restoration confirmed

## Root Cause
A recent code deployment introduced an unoptimized database query that caused connection pool exhaustion during peak traffic.

## Contributing Factors
1. Missing database index on frequently queried field
2. Insufficient load testing of new query patterns
3. Database connection pool size too small for peak load

## Action Items
1. [P0] Add database query performance tests to CI pipeline
2. [P1] Increase database connection pool size in production
3. [P1] Implement automated query performance monitoring
4. [P2] Enhance load testing scenarios for database queries

## Lessons Learned
- Database changes need more thorough performance testing
- Connection pool monitoring should trigger alerts earlier
- Customer communication was effective but could be faster
```

## Contact Information

### Emergency Contacts
- **Incident Hotline**: +1-555-INCIDENT (+1-555-462-4336)
- **Security Emergency**: security-emergency@leanvibe.ai
- **Executive Escalation**: executives@leanvibe.ai

### Useful Links
- **Status Page**: https://status.leanvibe.ai
- **Grafana Dashboards**: https://grafana.leanvibe.ai
- **Incident Management**: https://leanvibe.pagerduty.com
- **Runbooks Repository**: https://github.com/leanvibe/runbooks
- **Architecture Documentation**: https://docs.leanvibe.ai/architecture

### Key Commands Quick Reference
```bash
# Get cluster status
kubectl get nodes
kubectl get pods -A

# Check application health
curl -s https://api.leanvibe.ai/health | jq

# Scale application
kubectl scale deployment leanvibe-backend --replicas=N -n leanvibe-production

# View recent logs
kubectl logs -l app.kubernetes.io/name=leanvibe -n leanvibe-production --tail=100

# Database query
kubectl exec deployment/neo4j -n leanvibe-production -- cypher-shell -u neo4j -p $NEO4J_PASSWORD "RETURN 1"

# Cache status
kubectl exec deployment/redis -n leanvibe-production -- redis-cli -a $REDIS_PASSWORD INFO

# Start emergency backup
kubectl create job --from=cronjob/neo4j-backup neo4j-emergency-backup -n leanvibe-backup
```

---

**Document Version**: 2.1  
**Last Updated**: January 2024  
**Review Schedule**: Quarterly  
**Owner**: SRE Team  

**Remember**: In an incident, customer communication and service restoration are the top priorities. Document thoroughly but don't let documentation delay response actions.