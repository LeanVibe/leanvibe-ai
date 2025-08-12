# LeanVibe Synthetic Probes and Observability System

## Overview

A comprehensive observability-as-tests system for LeanVibe backend following XP principles. Provides **pragmatic monitoring** that detects issues in <60s and alerts within 120s with clear, actionable guidance.

## ✅ Implementation Complete

### 1. Synthetic Probes (`app/monitoring/synthetic_probes.py`)
- **HealthProbe**: `/health` endpoint validation (<1s SLA)
- **MetricsProbe**: `/metrics` endpoint validation (<2s SLA)
- **WebSocketProbe**: WebSocket handshake validation (<5s SLA)
- **APIProbe**: Core API endpoints with auth (<3s each)
- **SyntheticProbeRunner**: Orchestrates all probes concurrently
- **ProbeHistory**: Tracks trends and success rates

### 2. Observability System (`app/monitoring/observability.py`)
- **ErrorBudgetTracker**: Tracks error rates, freezes merges when exceeded
- **PerformanceBudgets**: Response time SLA monitoring (P95 < 500ms)
- **HealthDashboard**: Aggregates system health data
- **AlertManager**: Notifications for threshold breaches

### 3. Dashboard Interface (`monitoring/dashboard.html`)
- Real-time HTML dashboard with auto-refresh
- System health overview with color-coded status
- Individual probe results and trends
- Error budget consumption with deployment freeze warnings
- Performance metrics and SLA compliance
- Active alerts with recommended actions

### 4. FastAPI Integration (`app/api/endpoints/synthetic_monitoring.py`)
- `GET /monitoring/health`: Overall system health
- `GET /monitoring/metrics`: Prometheus-style metrics
- `GET /monitoring/dashboard`: HTML dashboard
- `GET /monitoring/probes`: Run synthetic probes on demand
- `GET /monitoring/error-budget`: Deployment freeze decisions
- `GET /monitoring/performance-budget`: SLA compliance status
- `GET /monitoring/alerts`: Active alerts with actions

### 5. Alert System (`monitoring/alerts.py`)
- **Console notifications** (always enabled) with colored output
- **Email alerts** (configurable with SMTP)
- **Slack webhooks** (configurable)
- **Custom webhooks** (configurable)
- **Rate limiting** (max 10 alerts per 5min window)
- **Alert conditions** for health, performance, errors, WebSocket

## Key Features

### Error Budget Management
- **API Endpoints**: 5% error rate budget
- **WebSocket**: 10% error rate budget  
- **AI Processing**: 15% error rate budget
- **System Health**: 2% error rate budget
- **Automatic deployment freeze** when budgets exhausted

### Performance SLA Monitoring
- **API Response Time**: P95 < 500ms
- **WebSocket Latency**: P95 < 200ms
- **AI Processing**: P95 < 5000ms
- **Database Queries**: P95 < 100ms

### Alert Conditions
- Health probe failures (3+ in 5min window)
- Performance budget exceeded (P95 > target for 5min)
- Error budget consumed (>80% consumption)
- WebSocket disconnection spikes

## Quick Start

### 1. Start the Backend
```bash
cd /Users/bogdan/work/leanvibe-ai/leanvibe-backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8765
```

### 2. Access Monitoring
- **Dashboard**: http://localhost:8765/monitoring/dashboard
- **Health API**: http://localhost:8765/monitoring/health
- **Metrics**: http://localhost:8765/monitoring/metrics
- **Probes**: http://localhost:8765/monitoring/probes

### 3. Test Monitoring System
```bash
# Demo the complete system
python monitoring/demo_monitoring.py --demo-all

# Test individual components
python monitoring/demo_monitoring.py --demo-probes
python monitoring/demo_monitoring.py --demo-error-budgets
python monitoring/demo_monitoring.py --demo-alerts

# Test alert notifications
python monitoring/alerts.py --test-alerts
```

## Example Monitoring Results

### Synthetic Probe Results
```json
{
  "health": {
    "status": "healthy",
    "response_time_ms": 145,
    "message": "Health endpoint responding correctly"
  },
  "websocket": {
    "status": "healthy", 
    "response_time_ms": 892,
    "message": "WebSocket handshake and message exchange successful"
  }
}
```

### Error Budget Status
```json
{
  "deployment_frozen": false,
  "overall_health": "healthy",
  "budgets": {
    "api_endpoints": {
      "status": "healthy",
      "error_rate": 0.02,
      "budget_consumption": 0.4,
      "threshold": 0.05
    }
  }
}
```

### Performance Budget Status
```json
{
  "overall_health": "healthy",
  "budgets": {
    "api_response_time": {
      "status": "healthy",
      "percentiles": {
        "p95": 387,
        "p99": 456
      },
      "target_p95": 500
    }
  }
}
```

## Architecture Benefits

### XP Principles Applied
- **Simple Design**: Clear, single-responsibility components
- **Fast Feedback**: Issues detected in <60s, alerts within 120s
- **Actionable Results**: Every alert includes recommended actions
- **Pragmatic Monitoring**: Focus on business-impacting metrics

### Production Ready
- **Comprehensive Coverage**: Probes, budgets, alerts, dashboard
- **Deployment Safety**: Error budget freeze prevents bad deploys  
- **Performance SLAs**: Automated P95 response time monitoring
- **Multi-Channel Alerts**: Console, email, Slack, webhook support
- **Rate Limiting**: Prevents alert spam during incidents

### Integration Ready
- **Prometheus Metrics**: Standard metrics format
- **REST APIs**: Easy integration with external tools
- **Real-time Dashboard**: HTML interface for operations teams
- **JSON APIs**: Programmatic access to all monitoring data

## Customization

### Configure Error Budgets
```python
# Modify in app/monitoring/observability.py
budgets = {
    "api_endpoints": ErrorBudget("API Endpoints", 0.05),  # 5% error rate
    "custom_service": ErrorBudget("Custom Service", 0.10),  # 10% error rate
}
```

### Configure Performance Budgets
```python
# Modify in app/monitoring/observability.py  
budgets = {
    "api_response_time": PerformanceBudget("API", 500.0, 1000.0),  # P95 < 500ms
    "custom_endpoint": PerformanceBudget("Custom", 200.0, 500.0),  # P95 < 200ms
}
```

### Configure Alert Notifications
```python
# Email configuration
config = NotificationConfig(
    email_enabled=True,
    email_smtp_server="smtp.gmail.com",
    email_username="alerts@yourcompany.com",
    email_password="your-app-password",
    email_to=["oncall@yourcompany.com"]
)

# Slack configuration  
config.slack_enabled = True
config.slack_webhook_url = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

## Files Created

```
app/monitoring/
├── __init__.py                     # Module initialization
├── synthetic_probes.py             # Probe classes and runner
└── observability.py                # Error budgets, performance budgets, alerts

app/api/endpoints/
└── synthetic_monitoring.py         # FastAPI monitoring endpoints

monitoring/
├── dashboard.html                  # Real-time HTML dashboard
├── alerts.py                       # Notification system  
├── demo_monitoring.py             # Demonstration script
└── README.md                       # This documentation
```

## Next Steps

1. **Configure Notifications**: Set up email/Slack for production alerts
2. **Customize Thresholds**: Adjust SLAs based on your requirements  
3. **Integration**: Connect to existing monitoring tools via APIs
4. **Scaling**: Add more probes for additional services
5. **Automation**: Integrate with CI/CD for deployment decisions

## Monitoring Philosophy

> "The best monitoring system is the one that prevents problems from becoming incidents, and when incidents do occur, guides you to the fastest resolution."

This system embodies XP principles by being:
- **Simple**: Easy to understand and maintain
- **Fast**: Quick detection and clear feedback
- **Actionable**: Every alert includes what to do next
- **Pragmatic**: Focuses on business-critical metrics

🚀 **LeanVibe monitoring system is ready for production use!**