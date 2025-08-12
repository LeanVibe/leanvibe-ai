"""
Observability Agent - Monitoring & Health Checks Generation
Generates monitoring, logging, alerting, and observability configurations
"""

import asyncio
import json
import logging
import os
import tempfile
from typing import Dict, List, Any, Optional
from uuid import UUID

from ...services.assembly_line_system import BaseAIAgent, AgentType, AgentResult, AgentStatus, QualityGateResult, QualityGateCheck
from ...models.mvp_models import TechnicalBlueprint

logger = logging.getLogger(__name__)


class ObservabilityAgent(BaseAIAgent):
    """AI agent that generates monitoring and observability configurations"""
    
    def __init__(self):
        super().__init__(AgentType.OBSERVABILITY)
    
    async def _execute_agent(
        self,
        mvp_project_id: UUID,
        input_data: Dict[str, Any],
        progress_callback: Optional[callable] = None
    ) -> AgentResult:
        """Generate observability and monitoring configurations"""
        
        blueprint_data = input_data.get("blueprint", {})
        backend_output = input_data.get("backend_output", {})
        frontend_output = input_data.get("frontend_output", {})
        infrastructure_output = input_data.get("infrastructure_output", {})
        
        if not blueprint_data:
            return AgentResult(
                agent_type=self.agent_type,
                status=AgentStatus.FAILED,
                error_message="No blueprint data provided"
            )
        
        try:
            # Parse blueprint
            blueprint = TechnicalBlueprint(**blueprint_data)
            
            # Create temporary directory for generated configs
            temp_dir = tempfile.mkdtemp(prefix=f"mvp_observability_{mvp_project_id}_")
            
            # Progress tracking
            total_steps = 7
            current_step = 0
            
            # Step 1: Generate monitoring stack configurations
            if progress_callback:
                await progress_callback(self.agent_type, AgentStatus.RUNNING, (current_step / total_steps) * 100)
            
            monitoring_configs = await self._generate_monitoring_stack(blueprint)
            monitoring_dir = "monitoring"
            for config_name, config_content in monitoring_configs.items():
                await self._write_file(temp_dir, f"{monitoring_dir}/{config_name}", config_content)
            current_step += 1
            
            # Step 2: Generate application metrics
            if progress_callback:
                await progress_callback(self.agent_type, AgentStatus.RUNNING, (current_step / total_steps) * 100)
            
            app_metrics = await self._generate_application_metrics(blueprint)
            for file_name, content in app_metrics.items():
                await self._write_file(temp_dir, f"app_metrics/{file_name}", content)
            current_step += 1
            
            # Step 3: Generate logging configurations
            if progress_callback:
                await progress_callback(self.agent_type, AgentStatus.RUNNING, (current_step / total_steps) * 100)
            
            logging_configs = await self._generate_logging_config(blueprint)
            for config_name, config_content in logging_configs.items():
                await self._write_file(temp_dir, f"logging/{config_name}", config_content)
            current_step += 1
            
            # Step 4: Generate alerting rules
            if progress_callback:
                await progress_callback(self.agent_type, AgentStatus.RUNNING, (current_step / total_steps) * 100)
            
            alert_configs = await self._generate_alerting_rules(blueprint)
            for config_name, config_content in alert_configs.items():
                await self._write_file(temp_dir, f"alerts/{config_name}", config_content)
            current_step += 1
            
            # Step 5: Generate dashboards
            if progress_callback:
                await progress_callback(self.agent_type, AgentStatus.RUNNING, (current_step / total_steps) * 100)
            
            dashboard_configs = await self._generate_dashboards(blueprint)
            for dashboard_name, dashboard_config in dashboard_configs.items():
                await self._write_file(temp_dir, f"dashboards/{dashboard_name}", dashboard_config)
            current_step += 1
            
            # Step 6: Generate health check system
            if progress_callback:
                await progress_callback(self.agent_type, AgentStatus.RUNNING, (current_step / total_steps) * 100)
            
            health_checks = await self._generate_health_checks(blueprint)
            for check_name, check_config in health_checks.items():
                await self._write_file(temp_dir, f"health_checks/{check_name}", check_config)
            current_step += 1
            
            # Step 7: Generate observability documentation
            if progress_callback:
                await progress_callback(self.agent_type, AgentStatus.RUNNING, (current_step / total_steps) * 100)
            
            docs = await self._generate_observability_docs(blueprint)
            await self._write_file(temp_dir, "OBSERVABILITY.md", docs)
            current_step += 1
            
            # Calculate confidence
            confidence_score = await self._calculate_confidence(blueprint, temp_dir)
            
            # Collect all generated files
            artifacts = await self._collect_artifacts(temp_dir)
            
            return AgentResult(
                agent_type=self.agent_type,
                status=AgentStatus.COMPLETED,
                output={
                    "generated_config_path": temp_dir,
                    "monitoring_config": blueprint.monitoring_config,
                    "performance_targets": blueprint.performance_targets,
                    "observability_files": len(artifacts)
                },
                artifacts=artifacts,
                metrics={
                    "monitoring_stack": True,
                    "logging_configured": True,
                    "alerting_rules": True,
                    "dashboards_generated": len(dashboard_configs),
                    "health_checks_configured": True,
                    "sli_slo_defined": True
                },
                confidence_score=confidence_score
            )
            
        except Exception as e:
            self.logger.error(f"Observability generation failed: {e}")
            return AgentResult(
                agent_type=self.agent_type,
                status=AgentStatus.FAILED,
                error_message=str(e)
            )
    
    async def _generate_monitoring_stack(self, blueprint: TechnicalBlueprint) -> Dict[str, str]:
        """Generate monitoring stack configurations (Prometheus, Grafana)"""
        
        configs = {}
        
        # Prometheus configuration
        configs["prometheus.yml"] = '''global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'backend'
    static_configs:
      - targets: ['backend:8765']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'frontend'
    static_configs:
      - targets: ['frontend:80']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']

  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']'''
        
        # Grafana provisioning
        configs["grafana/provisioning/datasources/prometheus.yml"] = '''apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true'''
        
        # Docker Compose for monitoring stack
        configs["docker-compose.monitoring.yml"] = '''version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - ./alert_rules.yml:/etc/prometheus/alert_rules.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/usr/share/prometheus/console_libraries'
      - '--web.console.templates=/usr/share/prometheus/consoles'
      - '--web.enable-lifecycle'

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
      - ./dashboards:/var/lib/grafana/dashboards

  alertmanager:
    image: prom/alertmanager:latest
    container_name: alertmanager
    ports:
      - "9093:9093"
    volumes:
      - ./alertmanager.yml:/etc/alertmanager/alertmanager.yml
      - alertmanager_data:/alertmanager

  node-exporter:
    image: prom/node-exporter:latest
    container_name: node-exporter
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.ignored-mount-points=^/(sys|proc|dev|host|etc)($$|/)'

volumes:
  prometheus_data:
  grafana_data:
  alertmanager_data:'''
        
        # Alertmanager configuration
        configs["alertmanager.yml"] = '''global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'alertmanager@yourdomain.com'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'

receivers:
  - name: 'web.hook'
    email_configs:
      - to: 'admin@yourdomain.com'
        subject: 'Alert: {{ .GroupLabels.alertname }}'
        body: |
          {{ range .Alerts }}
          Alert: {{ .Annotations.summary }}
          Description: {{ .Annotations.description }}
          {{ end }}

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'dev', 'instance']'''
        
        return configs
    
    async def _generate_application_metrics(self, blueprint: TechnicalBlueprint) -> Dict[str, str]:
        """Generate application-specific metrics collection"""
        
        metrics = {}
        
        # Backend metrics middleware
        metrics["backend_metrics.py"] = '''"""
Application metrics collection for FastAPI
"""
import time
from typing import Callable
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import FastAPI, Request, Response
import psutil

# Metrics definitions
REQUEST_COUNT = Counter(
    'http_requests_total', 
    'Total HTTP requests', 
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

ACTIVE_CONNECTIONS = Gauge(
    'active_connections',
    'Number of active connections'
)

DATABASE_CONNECTIONS = Gauge(
    'database_connections_active',
    'Number of active database connections'
)

MEMORY_USAGE = Gauge(
    'memory_usage_bytes',
    'Memory usage in bytes'
)

CPU_USAGE = Gauge(
    'cpu_usage_percent',
    'CPU usage percentage'
)

def metrics_middleware(app: FastAPI):
    """Add metrics collection middleware"""
    
    @app.middleware("http")
    async def collect_metrics(request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        response = await call_next(request)
        
        # Record request metrics
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        
        REQUEST_DURATION.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(time.time() - start_time)
        
        return response
    
    @app.get("/metrics")
    async def get_metrics():
        """Expose Prometheus metrics"""
        # Update system metrics
        MEMORY_USAGE.set(psutil.virtual_memory().used)
        CPU_USAGE.set(psutil.cpu_percent())
        
        return Response(
            generate_latest(),
            media_type=CONTENT_TYPE_LATEST
        )

# Business metrics
USER_REGISTRATIONS = Counter(
    'user_registrations_total',
    'Total user registrations'
)

API_ERRORS = Counter(
    'api_errors_total',
    'Total API errors',
    ['error_type']
)

def track_user_registration():
    """Track user registration event"""
    USER_REGISTRATIONS.inc()

def track_api_error(error_type: str):
    """Track API error"""
    API_ERRORS.labels(error_type=error_type).inc()'''
        
        # Frontend metrics (JavaScript)
        metrics["frontend_metrics.js"] = '''/**
 * Frontend metrics collection
 */

class MetricsCollector {
  constructor() {
    this.metrics = {
      pageViews: 0,
      userInteractions: 0,
      errors: 0,
      loadTimes: []
    };
    
    this.init();
  }
  
  init() {
    // Track page views
    this.trackPageView();
    
    // Track performance
    this.trackPerformance();
    
    // Track errors
    this.trackErrors();
    
    // Track user interactions
    this.trackInteractions();
    
    // Send metrics periodically
    setInterval(() => this.sendMetrics(), 60000); // Every minute
  }
  
  trackPageView() {
    this.metrics.pageViews++;
    
    // Send to analytics
    this.sendEvent('page_view', {
      path: window.location.pathname,
      timestamp: Date.now()
    });
  }
  
  trackPerformance() {
    window.addEventListener('load', () => {
      const perfData = performance.getEntriesByType('navigation')[0];
      const loadTime = perfData.loadEventEnd - perfData.fetchStart;
      
      this.metrics.loadTimes.push(loadTime);
      
      this.sendEvent('page_load', {
        loadTime: loadTime,
        domContentLoaded: perfData.domContentLoadedEventEnd - perfData.fetchStart,
        firstPaint: performance.getEntriesByType('paint')[0]?.startTime || 0
      });
    });
  }
  
  trackErrors() {
    window.addEventListener('error', (event) => {
      this.metrics.errors++;
      
      this.sendEvent('javascript_error', {
        message: event.message,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        stack: event.error?.stack
      });
    });
    
    window.addEventListener('unhandledrejection', (event) => {
      this.metrics.errors++;
      
      this.sendEvent('promise_rejection', {
        reason: event.reason,
        stack: event.reason?.stack
      });
    });
  }
  
  trackInteractions() {
    ['click', 'submit', 'input'].forEach(eventType => {
      document.addEventListener(eventType, (event) => {
        this.metrics.userInteractions++;
        
        this.sendEvent('user_interaction', {
          type: eventType,
          target: event.target.tagName,
          id: event.target.id,
          className: event.target.className
        });
      });
    });
  }
  
  async sendEvent(eventName, data) {
    try {
      await fetch('/api/analytics/events', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          event: eventName,
          data: data,
          timestamp: Date.now(),
          sessionId: this.getSessionId(),
          userId: this.getUserId()
        })
      });
    } catch (error) {
      console.warn('Failed to send metrics:', error);
    }
  }
  
  async sendMetrics() {
    await this.sendEvent('metrics_summary', this.metrics);
    
    // Reset counters
    this.metrics.userInteractions = 0;
    this.metrics.errors = 0;
  }
  
  getSessionId() {
    let sessionId = sessionStorage.getItem('sessionId');
    if (!sessionId) {
      sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
      sessionStorage.setItem('sessionId', sessionId);
    }
    return sessionId;
  }
  
  getUserId() {
    return localStorage.getItem('userId') || 'anonymous';
  }
}

// Initialize metrics collection
if (typeof window !== 'undefined') {
  window.metricsCollector = new MetricsCollector();
}

export default MetricsCollector;'''
        
        return metrics
    
    async def _generate_logging_config(self, blueprint: TechnicalBlueprint) -> Dict[str, str]:
        """Generate logging configurations"""
        
        configs = {}
        
        # Python logging configuration
        configs["logging_config.py"] = '''"""
Centralized logging configuration
"""
import logging
import logging.config
import json
import os
from datetime import datetime

# Logging configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'detailed': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'json': {
            'format': '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s", "filename": "%(filename)s", "lineno": %(lineno)d}',
            'datefmt': '%Y-%m-%dT%H:%M:%S'
        },
        'simple': {
            'format': '%(levelname)s - %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'detailed',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'DEBUG',
            'formatter': 'json',
            'filename': '/var/log/app/application.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5
        },
        'error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'ERROR',
            'formatter': 'json',
            'filename': '/var/log/app/errors.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5
        }
    },
    'loggers': {
        'app': {
            'level': 'DEBUG',
            'handlers': ['console', 'file', 'error_file'],
            'propagate': False
        },
        'uvicorn': {
            'level': 'INFO',
            'handlers': ['console', 'file']
        },
        'sqlalchemy': {
            'level': 'WARNING',
            'handlers': ['file']
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console']
    }
}

def setup_logging():
    """Setup logging configuration"""
    # Create log directory if it doesn't exist
    log_dir = '/var/log/app'
    os.makedirs(log_dir, exist_ok=True)
    
    logging.config.dictConfig(LOGGING_CONFIG)
    
    logger = logging.getLogger('app')
    logger.info('Logging configuration initialized')

# Structured logging helpers
def log_api_request(request, response_time=None, status_code=None):
    """Log API request with structured data"""
    logger = logging.getLogger('app.api')
    
    log_data = {
        'event': 'api_request',
        'method': request.method,
        'path': request.url.path,
        'query_params': str(request.query_params),
        'user_agent': request.headers.get('user-agent'),
        'client_ip': request.client.host,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if response_time:
        log_data['response_time'] = response_time
    if status_code:
        log_data['status_code'] = status_code
    
    logger.info(json.dumps(log_data))

def log_business_event(event_name, data=None):
    """Log business events with structured data"""
    logger = logging.getLogger('app.business')
    
    log_data = {
        'event': 'business_event',
        'event_name': event_name,
        'data': data or {},
        'timestamp': datetime.utcnow().isoformat()
    }
    
    logger.info(json.dumps(log_data))

def log_error(error, context=None):
    """Log errors with context"""
    logger = logging.getLogger('app.error')
    
    log_data = {
        'event': 'error',
        'error_type': type(error).__name__,
        'error_message': str(error),
        'context': context or {},
        'timestamp': datetime.utcnow().isoformat()
    }
    
    logger.error(json.dumps(log_data))'''
        
        # Fluentd configuration for log aggregation
        configs["fluentd.conf"] = '''<source>
  @type tail
  path /var/log/app/*.log
  pos_file /var/log/fluentd/app.log.pos
  tag app.*
  <parse>
    @type json
    time_key timestamp
    time_format %Y-%m-%dT%H:%M:%S
  </parse>
</source>

<filter app.**>
  @type record_transformer
  <record>
    hostname ${hostname}
    service_name mvp-app
    environment #{ENV['ENVIRONMENT'] || 'development'}
  </record>
</filter>

<match app.**>
  @type elasticsearch
  host elasticsearch
  port 9200
  index_name app-logs
  type_name _doc
  include_timestamp true
  logstash_format true
  logstash_prefix app-logs
  logstash_dateformat %Y.%m.%d
  <buffer>
    flush_thread_count 1
    flush_interval 5s
    chunk_limit_size 2M
    queue_limit_length 32
    retry_max_interval 30
    retry_forever true
  </buffer>
</match>'''
        
        return configs
    
    async def _generate_alerting_rules(self, blueprint: TechnicalBlueprint) -> Dict[str, str]:
        """Generate alerting rules"""
        
        rules = {}
        
        # Prometheus alerting rules
        rules["alert_rules.yml"] = '''groups:
  - name: application.rules
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} requests per second"

      - alert: HighResponseTime
        expr: http_request_duration_seconds{quantile="0.95"} > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"
          description: "95th percentile response time is {{ $value }} seconds"

      - alert: DatabaseConnectionError
        expr: up{job="backend"} == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Backend service is down"
          description: "Backend service has been down for more than 2 minutes"

      - alert: HighMemoryUsage
        expr: memory_usage_bytes / 1024 / 1024 / 1024 > 1
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value }}GB"

      - alert: HighCPUUsage
        expr: cpu_usage_percent > 80
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage"
          description: "CPU usage is {{ $value }}%"

      - alert: DiskSpaceLow
        expr: (node_filesystem_avail_bytes / node_filesystem_size_bytes) * 100 < 10
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Disk space low"
          description: "Disk space is {{ $value }}% full"

  - name: business.rules
    rules:
      - alert: LowUserRegistrations
        expr: rate(user_registrations_total[1h]) < 0.1
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "Low user registration rate"
          description: "User registration rate is {{ $value }} per hour"

      - alert: HighAPIErrorRate
        expr: rate(api_errors_total[5m]) > 5
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "High API error rate"
          description: "API error rate is {{ $value }} errors per second"'''
        
        return rules
    
    async def _generate_dashboards(self, blueprint: TechnicalBlueprint) -> Dict[str, str]:
        """Generate Grafana dashboards"""
        
        dashboards = {}
        
        # Application overview dashboard
        dashboards["application_overview.json"] = json.dumps({
            "dashboard": {
                "id": None,
                "title": "MVP Application Overview",
                "tags": ["mvp", "overview"],
                "timezone": "browser",
                "panels": [
                    {
                        "id": 1,
                        "title": "Request Rate",
                        "type": "stat",
                        "targets": [
                            {
                                "expr": "sum(rate(http_requests_total[5m]))",
                                "legendFormat": "Requests/sec"
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "unit": "reqps",
                                "min": 0
                            }
                        },
                        "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0}
                    },
                    {
                        "id": 2,
                        "title": "Error Rate",
                        "type": "stat",
                        "targets": [
                            {
                                "expr": "sum(rate(http_requests_total{status=~\"5..\"}[5m])) / sum(rate(http_requests_total[5m]))",
                                "legendFormat": "Error Rate"
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "unit": "percentunit",
                                "max": 1,
                                "min": 0
                            }
                        },
                        "gridPos": {"h": 8, "w": 6, "x": 6, "y": 0}
                    },
                    {
                        "id": 3,
                        "title": "Response Time",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "http_request_duration_seconds{quantile=\"0.50\"}",
                                "legendFormat": "50th percentile"
                            },
                            {
                                "expr": "http_request_duration_seconds{quantile=\"0.95\"}",
                                "legendFormat": "95th percentile"
                            }
                        ],
                        "yAxes": [
                            {
                                "unit": "s",
                                "min": 0
                            }
                        ],
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8}
                    }
                ],
                "time": {
                    "from": "now-1h",
                    "to": "now"
                },
                "refresh": "30s"
            }
        }, indent=2)
        
        # Business metrics dashboard
        dashboards["business_metrics.json"] = json.dumps({
            "dashboard": {
                "id": None,
                "title": "Business Metrics",
                "tags": ["mvp", "business"],
                "panels": [
                    {
                        "id": 1,
                        "title": "User Registrations",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "rate(user_registrations_total[1h])",
                                "legendFormat": "Registrations/hour"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
                    },
                    {
                        "id": 2,
                        "title": "Active Users",
                        "type": "stat",
                        "targets": [
                            {
                                "expr": "sum(active_connections)",
                                "legendFormat": "Active Users"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 6, "x": 12, "y": 0}
                    }
                ]
            }
        }, indent=2)
        
        return dashboards
    
    async def _generate_health_checks(self, blueprint: TechnicalBlueprint) -> Dict[str, str]:
        """Generate health check configurations"""
        
        checks = {}
        
        # Comprehensive health check endpoint
        checks["health_check.py"] = '''"""
Comprehensive health check system
"""
import asyncio
import logging
import time
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from ..models.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()

class HealthCheckRegistry:
    """Registry for health checks"""
    
    def __init__(self):
        self.checks = {}
    
    def register(self, name: str, check_func):
        """Register a health check"""
        self.checks[name] = check_func
    
    async def run_all(self) -> Dict[str, Any]:
        """Run all registered health checks"""
        results = {}
        overall_healthy = True
        
        for name, check_func in self.checks.items():
            try:
                start_time = time.time()
                result = await check_func()
                duration = time.time() - start_time
                
                results[name] = {
                    "healthy": result.get("healthy", True),
                    "message": result.get("message", "OK"),
                    "duration_ms": round(duration * 1000, 2),
                    "details": result.get("details", {})
                }
                
                if not result.get("healthy", True):
                    overall_healthy = False
                    
            except Exception as e:
                logger.error(f"Health check {name} failed: {e}")
                results[name] = {
                    "healthy": False,
                    "message": str(e),
                    "duration_ms": 0,
                    "details": {}
                }
                overall_healthy = False
        
        return {
            "healthy": overall_healthy,
            "timestamp": time.time(),
            "checks": results
        }

# Global health check registry
health_registry = HealthCheckRegistry()

async def check_database():
    """Check database connectivity"""
    try:
        db = next(get_db())
        result = db.execute(text("SELECT 1"))
        row = result.fetchone()
        
        if row and row[0] == 1:
            return {"healthy": True, "message": "Database connection OK"}
        else:
            return {"healthy": False, "message": "Database query failed"}
    except Exception as e:
        return {"healthy": False, "message": f"Database error: {str(e)}"}

async def check_external_apis():
    """Check external API dependencies"""
    # Add checks for external services here
    return {"healthy": True, "message": "No external APIs configured"}

async def check_disk_space():
    """Check available disk space"""
    import shutil
    try:
        total, used, free = shutil.disk_usage("/")
        free_percent = (free / total) * 100
        
        if free_percent < 10:
            return {
                "healthy": False,
                "message": f"Low disk space: {free_percent:.1f}% free",
                "details": {"free_percent": free_percent}
            }
        
        return {
            "healthy": True,
            "message": f"Disk space OK: {free_percent:.1f}% free",
            "details": {"free_percent": free_percent}
        }
    except Exception as e:
        return {"healthy": False, "message": f"Disk check failed: {str(e)}"}

async def check_memory():
    """Check memory usage"""
    import psutil
    try:
        memory = psutil.virtual_memory()
        used_percent = memory.percent
        
        if used_percent > 90:
            return {
                "healthy": False,
                "message": f"High memory usage: {used_percent:.1f}%",
                "details": {"used_percent": used_percent}
            }
        
        return {
            "healthy": True,
            "message": f"Memory usage OK: {used_percent:.1f}%",
            "details": {"used_percent": used_percent}
        }
    except Exception as e:
        return {"healthy": False, "message": f"Memory check failed: {str(e)}"}

# Register health checks
health_registry.register("database", check_database)
health_registry.register("external_apis", check_external_apis)
health_registry.register("disk_space", check_disk_space)
health_registry.register("memory", check_memory)

@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {"status": "healthy", "timestamp": time.time()}

@router.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with all components"""
    result = await health_registry.run_all()
    
    if not result["healthy"]:
        raise HTTPException(status_code=503, detail=result)
    
    return result

@router.get("/health/ready")
async def readiness_check():
    """Kubernetes readiness probe"""
    # Quick checks for readiness
    try:
        db = next(get_db())
        db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception:
        raise HTTPException(status_code=503, detail="Not ready")

@router.get("/health/live")
async def liveness_check():
    """Kubernetes liveness probe"""
    # Basic liveness check
    return {"status": "alive"}'''
        
        # Kubernetes health check configuration
        checks["k8s_health_checks.yaml"] = '''# Add to your deployment YAML
spec:
  template:
    spec:
      containers:
      - name: backend
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8765
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8765
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3'''
        
        return checks
    
    async def _generate_observability_docs(self, blueprint: TechnicalBlueprint) -> str:
        """Generate observability documentation"""
        
        docs = '''# Observability Guide

This document describes the monitoring, logging, and alerting setup for your MVP application.

## Monitoring Stack

The application uses the following monitoring components:

- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboards
- **Alertmanager**: Alert routing and notification
- **Node Exporter**: System metrics
- **Application metrics**: Custom business and performance metrics

### Quick Start

```bash
# Start monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

# Access dashboards
# Grafana: http://localhost:3000 (admin/admin)
# Prometheus: http://localhost:9090
# Alertmanager: http://localhost:9093
```

## Metrics

### Application Metrics

The application exposes the following metrics at `/metrics`:

**HTTP Metrics**:
- `http_requests_total`: Total HTTP requests by method, endpoint, and status
- `http_request_duration_seconds`: Request duration histogram

**System Metrics**:
- `memory_usage_bytes`: Current memory usage
- `cpu_usage_percent`: Current CPU usage percentage
- `active_connections`: Number of active connections

**Business Metrics**:
- `user_registrations_total`: Total user registrations
- `api_errors_total`: Total API errors by type

### Custom Metrics

Add custom metrics in your code:

```python
from prometheus_client import Counter, Histogram

# Create custom metrics
CUSTOM_COUNTER = Counter('custom_events_total', 'Custom events')
CUSTOM_HISTOGRAM = Histogram('custom_duration_seconds', 'Custom duration')

# Use in your code
CUSTOM_COUNTER.inc()
with CUSTOM_HISTOGRAM.time():
    # Your code here
    pass
```

## Dashboards

### Available Dashboards

1. **Application Overview**: Request rate, error rate, response times
2. **Business Metrics**: User registrations, active users
3. **Infrastructure**: System metrics, resource usage

### Creating Custom Dashboards

1. Access Grafana at http://localhost:3000
2. Create new dashboard
3. Add panels with Prometheus queries
4. Save and export dashboard JSON

## Alerting

### Alert Rules

The following alerts are configured:

**Application Alerts**:
- High error rate (>10% for 5 minutes)
- High response time (>2 seconds for 5 minutes)
- Service down (backend unreachable for 2 minutes)

**Infrastructure Alerts**:
- High memory usage (>1GB for 10 minutes)
- High CPU usage (>80% for 10 minutes)
- Low disk space (<10% available)

**Business Alerts**:
- Low user registration rate (<0.1/hour for 1 hour)
- High API error rate (>5 errors/second for 10 minutes)

### Adding Custom Alerts

1. Edit `monitoring/alert_rules.yml`
2. Add new alert rule:
```yaml
- alert: CustomAlert
  expr: your_metric > threshold
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Custom alert fired"
    description: "Your custom alert description"
```

3. Reload Prometheus configuration:
```bash
curl -X POST http://localhost:9090/-/reload
```

## Logging

### Log Levels

- **DEBUG**: Detailed information for debugging
- **INFO**: General information about application flow
- **WARNING**: Warning messages for potential issues
- **ERROR**: Error messages for failures
- **CRITICAL**: Critical errors that may cause application failure

### Log Format

Logs are structured in JSON format:
```json
{
  "timestamp": "2024-01-01T12:00:00",
  "level": "INFO",
  "logger": "app.api",
  "message": "API request processed",
  "filename": "main.py",
  "lineno": 42
}
```

### Log Aggregation

Logs are collected and stored using:
- **Fluentd**: Log collection and forwarding
- **Elasticsearch**: Log storage and indexing
- **Kibana**: Log visualization and search

### Viewing Logs

```bash
# View application logs
docker-compose logs -f backend

# View error logs only
docker-compose logs -f backend | grep ERROR

# View logs in Kibana
# Access: http://localhost:5601
```

## Health Checks

### Endpoints

- `GET /health`: Basic health check
- `GET /health/detailed`: Comprehensive health check with all components
- `GET /health/ready`: Kubernetes readiness probe
- `GET /health/live`: Kubernetes liveness probe

### Health Check Components

- Database connectivity
- External API dependencies
- Disk space availability
- Memory usage
- System resources

## Troubleshooting

### Common Issues

**High Memory Usage**:
1. Check `/health/detailed` for memory metrics
2. Review application logs for memory leaks
3. Scale horizontally or increase memory limits

**High Error Rate**:
1. Check error logs for specific error messages
2. Review recent deployments or changes
3. Check external service dependencies

**Database Connection Issues**:
1. Verify database service is running
2. Check connection string configuration
3. Review database logs for errors

### Debugging Steps

1. Check application health: `curl http://localhost:8765/health/detailed`
2. Review recent logs: `docker-compose logs --tail=100 backend`
3. Check metrics in Grafana dashboards
4. Review active alerts in Alertmanager
5. Verify system resources: `docker stats`

## Performance Optimization

### Monitoring Performance

1. Track key metrics:
   - Response time percentiles (50th, 95th, 99th)
   - Request rate and error rate
   - Database query performance
   - Memory and CPU usage

2. Set up alerts for performance degradation
3. Regular performance testing and profiling

### Optimization Strategies

- Database query optimization
- Caching implementation
- Load balancing
- Resource scaling
- Code profiling and optimization

## Security Monitoring

### Security Metrics

- Failed authentication attempts
- Suspicious API usage patterns
- Unusual traffic patterns
- Security audit events

### Security Alerts

Configure alerts for:
- Multiple failed login attempts
- Unusual API access patterns
- Security policy violations
- Suspicious user behavior

## Compliance and Auditing

### Audit Logs

All user actions and system events are logged for compliance:
- User authentication and authorization
- Data access and modifications
- Administrative actions
- System configuration changes

### Data Retention

- Application logs: 30 days
- Audit logs: 1 year
- Metrics: 90 days
- Error logs: 6 months

## Best Practices

1. **Metrics**: Measure what matters to your business
2. **Alerts**: Alert on symptoms, not causes
3. **Dashboards**: Keep dashboards focused and actionable
4. **Logs**: Include context and structured data
5. **Performance**: Monitor user experience metrics
6. **Security**: Monitor for security threats and compliance
7. **Documentation**: Keep observability documentation updated

For additional support, refer to the individual component documentation and community resources.'''
        
        return docs
    
    # Helper methods
    
    async def _write_file(self, base_dir: str, file_path: str, content: str):
        """Write content to file, creating directories as needed"""
        full_path = os.path.join(base_dir, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    async def _calculate_confidence(self, blueprint: TechnicalBlueprint, temp_dir: str) -> float:
        """Calculate confidence score for generated observability"""
        confidence_factors = []
        
        # Blueprint completeness
        blueprint_score = blueprint.confidence_score if hasattr(blueprint, 'confidence_score') else 0.8
        confidence_factors.append(blueprint_score)
        
        # Monitoring completeness
        expected_configs = ["monitoring/prometheus.yml", "dashboards/", "alerts/"]
        generated_files = await self._collect_artifacts(temp_dir)
        completeness = len([f for f in expected_configs if any(f in path for path in generated_files)]) / len(expected_configs)
        confidence_factors.append(completeness)
        
        # Performance targets handling
        performance_targets = blueprint.performance_targets or {}
        monitoring_config = blueprint.monitoring_config or {}
        observability_score = 0.8 + (0.1 if performance_targets else 0) + (0.1 if monitoring_config else 0)
        confidence_factors.append(min(1.0, observability_score))
        
        return sum(confidence_factors) / len(confidence_factors)
    
    async def _collect_artifacts(self, temp_dir: str) -> List[str]:
        """Collect all generated file paths"""
        artifacts = []
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                full_path = os.path.join(root, file)
                relative_path = os.path.relpath(full_path, temp_dir)
                artifacts.append(relative_path)
        return artifacts
    
    async def quality_check(self, result: AgentResult) -> QualityGateResult:
        """Perform quality checks on generated observability"""
        checks = []
        
        # Check essential monitoring components
        essential_components = ["monitoring", "alerts", "dashboards"]
        missing_components = []
        for component in essential_components:
            if not any(component in artifact for artifact in result.artifacts):
                missing_components.append(component)
        
        if missing_components:
            checks.append(QualityGateCheck(
                check_name="monitoring_components",
                passed=False,
                score=0.6,
                details=f"Missing monitoring components: {missing_components}",
                fix_suggestions=[f"Generate {c} configuration" for c in missing_components]
            ))
        else:
            checks.append(QualityGateCheck(
                check_name="monitoring_components",
                passed=True,
                score=1.0,
                details="All monitoring components generated"
            ))
        
        # Check alerting configuration
        has_alerts = result.metrics.get("alerting_rules", False)
        checks.append(QualityGateCheck(
            check_name="alerting_rules",
            passed=has_alerts,
            score=1.0 if has_alerts else 0.7,
            details="Alerting rules configured" if has_alerts else "Limited alerting configuration"
        ))
        
        # Check dashboard availability
        dashboards_count = result.metrics.get("dashboards_generated", 0)
        if dashboards_count < 2:
            checks.append(QualityGateCheck(
                check_name="dashboards",
                passed=False,
                score=0.5,
                details=f"Too few dashboards: {dashboards_count}",
                fix_suggestions=["Generate more comprehensive dashboards"]
            ))
        else:
            checks.append(QualityGateCheck(
                check_name="dashboards",
                passed=True,
                score=1.0,
                details=f"Good dashboard coverage: {dashboards_count} dashboards"
            ))
        
        # Calculate overall result
        overall_score = sum(check.score for check in checks) / len(checks) if checks else 0.0
        overall_passed = all(check.passed for check in checks)
        
        return QualityGateResult(
            overall_passed=overall_passed,
            overall_score=overall_score,
            checks=checks
        )