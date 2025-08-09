# Autonomous CI/CD Deployment System

This repository implements a comprehensive autonomous CI/CD pipeline following extreme programming principles, designed to handle 85%+ of deployments automatically with safe rollback mechanisms.

## 🚀 System Overview

### Autonomous Features
- **Auto-merge PRs** when all checks pass + "auto-merge" label
- **Canary deployments** with automatic promotion or rollback
- **Synthetic health probes** for comprehensive validation  
- **Instant rollback** on health check failures
- **Tiered testing** for fast feedback and comprehensive validation

### Quality Gates
- **75%+ test coverage** required for PR merge
- **Mutation testing** for test quality validation
- **Performance regression detection** (10% threshold)
- **Security scanning** with dependency audits
- **Flaky test quarantine** to maintain CI reliability

## 📋 Pipeline Structure

### Tier 0: Pre-commit Tests (<60s)
```bash
# Runs on every push - fail fast
pytest -m "unit or contract or type_check" --maxfail=1 --timeout=50
```
- Unit tests
- Contract validation  
- Type checking
- Static analysis (black, isort, flake8, mypy)

### Tier 1: PR Gate Tests (3-5m)
```bash  
# Runs on PRs - integration validation
pytest -m "integration or websocket or smoke" --cov=app --cov-fail-under=75
```
- Integration tests
- WebSocket functionality
- Smoke tests
- Coverage gate (75% minimum)

### Tier 2: Nightly Tests (30m)
```bash
# Runs nightly - quality assurance
pytest -m "e2e or performance or mutation"
```
- End-to-end workflows
- Performance regression detection
- Mutation testing (5% sample)
- Flaky test detection
- Security scanning

### Tier 3: Weekly Tests (2h)
```bash
# Runs weekly - comprehensive validation  
pytest -m "load or security" --comprehensive
```
- Full mutation testing (100%)
- Dependency updates with security audit
- Comprehensive load testing
- Chaos engineering
- Database migration testing

## 🔄 Deployment Flow

### 1. Development Workflow
```
Feature Branch → PR → Auto-merge → Canary → Production
      ↓              ↓         ↓        ↓         ↓
   Tier 0       Tier 1     Deploy   Health    Promote
   Tests        Tests      Staging  Checks    100%
```

### 2. Auto-merge Conditions
PR is automatically merged when:
- ✅ All Tier 0 + Tier 1 tests pass
- ✅ Coverage ≥ 75%
- ✅ Has "auto-merge" label
- ✅ No "do-not-merge" or "work-in-progress" labels
- ✅ Canary deployment successful
- ✅ Synthetic probes pass (≥85% success rate)

### 3. Deployment Process
```bash
# 1. Canary Deployment (10% traffic)
./deploy/canary.sh staging $COMMIT_SHA

# 2. Health Validation
./deploy/synthetic_probes.sh staging --comprehensive

# 3. Auto-promotion or Rollback
# If healthy: promote to 100% traffic
# If unhealthy: automatic rollback
./deploy/rollback.sh staging --emergency
```

## 📊 Monitoring & Metrics

### Health Check Endpoints
- `GET /health` - Basic health check
- `GET /health/complete` - Comprehensive health validation
- `GET /health/database` - Database connectivity
- `GET /health/redis` - Redis connectivity  
- `GET /health/ai` - AI service status

### Synthetic Probes
Automated validation covering:
- **API functionality** - CRUD operations, authentication
- **WebSocket connections** - Real-time features
- **Performance benchmarks** - Response times, throughput
- **Security checks** - Authorization, HTTPS redirects
- **Infrastructure metrics** - Memory, CPU, disk usage

### Rollback Triggers
Automatic rollback when:
- Error rate > 10%
- Response time > 5000ms  
- Health check failures ≥ 3
- Synthetic probe failures ≥ 2
- Memory usage > 90%

## 🛠 Setup Instructions

### 1. Configure Branch Protection
```bash
# Apply branch protection rules
gh api repos/:owner/:repo/branches/main/protection \
  --method PUT --input .github/branch-protection-main.json

gh api repos/:owner/:repo/branches/develop/protection \
  --method PUT --input .github/branch-protection-develop.json
```

### 2. Setup Environment Protection
```bash
# Configure staging environment
gh api repos/:owner/:repo/environments/staging \
  --method PUT --input .github/environment-staging.json

# Configure production environment  
gh api repos/:owner/:repo/environments/production \
  --method PUT --input .github/environment-production.json
```

### 3. Required Secrets
Set the following repository secrets:
```bash
STAGING_API_KEY=<staging-api-key>
PROD_API_KEY=<production-api-key>
PROD_DB_PASSWORD=<production-db-password>
PROD_REDIS_PASSWORD=<production-redis-password>
SLACK_WEBHOOK_URL=<slack-notifications>
DOCKER_REGISTRY=<container-registry-url>
```

### 4. Validate Pipeline
```bash
# Run comprehensive validation
python3 scripts/validate_pipeline.py

# Should output: "🚀 Pipeline validation PASSED!"
```

## 🏗 Architecture

### Workflow Files
- `.github/workflows/autonomous.yml` - Main CI/CD pipeline
- `.github/workflows/nightly.yml` - Nightly quality assurance  
- `.github/workflows/weekly.yml` - Weekly comprehensive testing

### Deployment Scripts
- `deploy/canary.sh` - Canary deployment with health checks
- `deploy/rollback.sh` - Instant rollback on failures
- `deploy/synthetic_probes.sh` - Comprehensive health validation

### Configuration Files
- `.github/branch-protection*.json` - Branch protection rules
- `.github/environment-*.json` - Environment protection settings
- `docker-compose.*.yml` - Environment-specific deployments
- `config/performance_sla.json` - Performance thresholds

## 🎯 Usage Examples

### 1. Standard Development Flow
```bash
# Create feature branch
git checkout -b feature/new-awesome-feature

# Make changes and commit
git add . && git commit -m "feat: add awesome feature"

# Push and create PR
git push -u origin feature/new-awesome-feature
gh pr create --title "Add awesome feature" --body "Description..."

# Add auto-merge label for autonomous deployment
gh pr edit --add-label "auto-merge"

# Pipeline will:
# 1. Run Tier 0 tests (<60s)
# 2. Run Tier 1 tests on PR (3-5m)  
# 3. Deploy canary to staging
# 4. Run synthetic probes
# 5. Auto-merge if all pass
# 6. Deploy to production
```

### 2. Emergency Rollback
```bash
# Manual emergency rollback
./deploy/rollback.sh production --emergency

# Rollback to specific version
./deploy/rollback.sh production --to-version=abc123def456

# Check rollback status
curl https://leanvibe.ai/health/complete
```

### 3. Manual Deployment
```bash
# Deploy specific version to staging
./deploy/canary.sh staging abc123def456

# Run health checks
./deploy/synthetic_probes.sh staging --comprehensive

# Promote if healthy (done automatically in CI)
```

## 📈 Metrics & Reporting

### Autonomous Success Rate
Target: **85%+ fully autonomous deployments**

Tracked metrics:
- Deployment success rate
- Time to production (commit → live)
- Rollback frequency and speed
- Test suite reliability (flaky test rate)
- Coverage trends

### Quality Indicators
- **Test Coverage**: ≥75% (gate), target 85%
- **Mutation Score**: ≥70% (weekly validation)
- **Performance**: <5% regression tolerance
- **Security**: Zero critical vulnerabilities
- **Uptime**: 99.9% availability target

## 🚨 Troubleshooting

### Common Issues

#### Auto-merge Not Working
```bash
# Check branch protection status
gh api repos/:owner/:repo/branches/main/protection

# Verify required checks are passing
gh pr checks <pr-number>

# Check PR labels
gh pr view <pr-number> --json labels
```

#### Deployment Failures
```bash
# Check deployment logs
docker compose -f docker-compose.staging.yml logs app

# Run synthetic probes manually
./deploy/synthetic_probes.sh staging --comprehensive

# Check health endpoints
curl -f https://staging.leanvibe.ai/health/complete
```

#### Rollback Issues
```bash
# Emergency rollback with verbose logging
./deploy/rollback.sh production --emergency 2>&1 | tee rollback.log

# Check available backup versions
docker images leanvibe-backend --filter "label=environment=production"
```

### Performance Optimization
```bash
# Run performance benchmarks
pytest -m performance --benchmark-json=benchmarks.json

# Check for performance regressions  
python3 tools/perf_regression.py --baseline-commit=HEAD~10

# Optimize Docker builds
docker build --build-arg BUILDKIT_INLINE_CACHE=1 .
```

## 🔐 Security Considerations

### Automated Security Scanning
- **Dependency scanning** with `safety` and `pip-audit`
- **Static analysis** with `bandit` and `semgrep`  
- **Container scanning** with integrated tools
- **Secret detection** in CI pipeline

### Production Security
- **Environment separation** with dedicated credentials
- **Network isolation** via Docker networks
- **Resource limits** to prevent resource exhaustion
- **Automated certificate management**

### Audit Trail
All deployments tracked with:
- Commit SHA and deployment timestamp
- Health check results and metrics
- Rollback triggers and recovery time
- User actions and approval chains

## 📚 Additional Resources

- [Extreme Programming Practices](https://www.extremeprogramming.org/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [Canary Deployment Patterns](https://martinfowler.com/bliki/CanaryRelease.html)

---

**🤖 This system is designed for autonomous operation. Human intervention should only be required for architecture changes, security issues, or when the autonomous success rate drops below 85%.**