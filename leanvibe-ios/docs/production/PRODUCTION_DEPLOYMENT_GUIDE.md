# LeenVibe Production Deployment Guide

## Prerequisites

### System Requirements
- **macOS**: 13.0+ (for iOS development)
- **Xcode**: 15.0+ with iOS 18.0+ SDK
- **Python**: 3.11+ with pip/uv package manager
- **Hardware**: Apple Silicon recommended, 16GB RAM minimum
- **Storage**: 10GB+ available space
- **Network**: High-speed internet for dependencies

### Development Tools
- **Git**: Version control
- **Docker**: Container deployment (optional)
- **nginx**: Reverse proxy (production)
- **SSL Certificates**: HTTPS/WSS support
- **Monitoring Tools**: System observability

## Backend Deployment

### 1. Environment Setup

#### Clone Repository
```bash
git clone https://github.com/your-org/leenvibe-ios-dashboard.git
cd leenvibe-ios-dashboard/leenvibe-backend
```

#### Python Environment
```bash
# Using uv (recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv
source .venv/bin/activate
uv sync

# Using pip (alternative)
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Environment Variables
```bash
# Create .env file
cat > .env << EOF
# Server Configuration
HOST=0.0.0.0
PORT=8002
DEBUG=false
LOG_LEVEL=info

# Security
SECRET_KEY=your-super-secret-key-here
CORS_ORIGINS=["https://your-domain.com"]

# Database (if using persistent storage)
DATABASE_URL=postgresql://user:pass@localhost:5432/leenvibe

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=8003

# Task Management
TASK_STORAGE_PATH=/data/tasks
MAX_TASKS_PER_USER=1000
TASK_CLEANUP_INTERVAL=3600

# WebSocket
WS_MAX_CONNECTIONS=100
WS_HEARTBEAT_INTERVAL=30
EOF
```

### 2. Database Configuration

#### SQLite (Development/Small Production)
```python
# app/core/config.py
DATABASE_URL = "sqlite:///./leenvibe.db"
```

#### PostgreSQL (Production)
```bash
# Install PostgreSQL
brew install postgresql
brew services start postgresql

# Create database
createdb leenvibe

# Update environment
DATABASE_URL="postgresql://postgres:password@localhost:5432/leenvibe"
```

#### Database Migration
```python
# app/models/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Initialize tables
Base.metadata.create_all(bind=engine)
```

### 3. Security Hardening

#### API Security
```python
# app/core/security.py
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import HTTPException, Depends
import jwt

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Apply to protected endpoints
@router.get("/api/tasks", dependencies=[Depends(verify_token)])
async def protected_endpoint():
    pass
```

#### CORS Configuration
```python
# app/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

#### Rate Limiting
```python
# app/middleware/rate_limit.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@limiter.limit("100/minute")
@router.post("/api/tasks")
async def create_task(request: Request):
    pass
```

### 4. Performance Tuning

#### Uvicorn Configuration
```python
# gunicorn.conf.py
bind = "0.0.0.0:8002"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
preload_app = True
keepalive = 2
```

#### Connection Pooling
```python
# app/core/database.py
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

#### Caching Strategy
```python
# app/services/cache_service.py
import redis
from functools import wraps

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_result(expiration=300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            result = await func(*args, **kwargs)
            redis_client.setex(cache_key, expiration, json.dumps(result))
            return result
        return wrapper
    return decorator

@cache_result(expiration=60)
async def get_task_stats():
    # Expensive computation
    pass
```

### 5. Monitoring & Logging

#### Structured Logging
```python
# app/core/logging.py
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        return json.dumps(log_entry)

# Configure logging
logging.basicConfig(level=logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger = logging.getLogger(__name__)
logger.addHandler(handler)
```

#### Health Check Endpoint
```python
# app/api/endpoints/health.py
@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "services": {
            "database": await check_database_health(),
            "redis": await check_redis_health(),
            "task_storage": await check_task_storage_health()
        }
    }
```

#### Metrics Collection
```python
# app/middleware/metrics.py
from prometheus_client import Counter, Histogram, generate_latest
import time

REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
    REQUEST_DURATION.observe(duration)
    
    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

## iOS App Deployment

### 1. Code Signing Setup

#### Apple Developer Account
1. **Enroll** in Apple Developer Program ($99/year)
2. **Create** App ID in Developer Portal
3. **Generate** signing certificates
4. **Create** provisioning profiles

#### Xcode Configuration
```bash
# Create xcconfig file
# ios-production.xcconfig
CODE_SIGN_STYLE = Manual
DEVELOPMENT_TEAM = YOUR_TEAM_ID
CODE_SIGN_IDENTITY = iPhone Distribution
PROVISIONING_PROFILE_SPECIFIER = LeenVibe Production

# Release build configuration
SWIFT_OPTIMIZATION_LEVEL = -O
SWIFT_COMPILATION_MODE = wholemodule
GCC_OPTIMIZATION_LEVEL = s
ENABLE_BITCODE = YES
```

#### Automatic Signing (Xcode)
```swift
// In project settings
Team: Your Development Team
Bundle Identifier: com.leenvibe.ios
Signing Certificate: Apple Distribution
Provisioning Profile: Automatic
```

### 2. Build Configuration

#### Production Settings
```swift
// Production/Release.xcconfig
API_BASE_URL = https://api.leenvibe.com
WEBSOCKET_URL = wss://api.leenvibe.com/ws
ENABLE_DEBUG_LOGS = NO
ENABLE_ANALYTICS = YES
APP_VERSION = 1.0.0
BUILD_NUMBER = 1
```

#### Info.plist Configuration
```xml
<!-- Info.plist -->
<key>NSAppTransportSecurity</key>
<dict>
    <key>NSAllowsArbitraryLoads</key>
    <false/>
    <key>NSExceptionDomains</key>
    <dict>
        <key>api.leenvibe.com</key>
        <dict>
            <key>NSExceptionAllowsInsecureHTTPLoads</key>
            <false/>
            <key>NSExceptionMinimumTLSVersion</key>
            <string>TLSv1.2</string>
        </dict>
    </dict>
</key>

<key>NSCameraUsageDescription</key>
<string>LeenVibe uses the camera to scan QR codes for server pairing.</string>

<key>NSMicrophoneUsageDescription</key>
<string>LeenVibe uses the microphone for voice commands and AI interaction.</string>
```

### 3. TestFlight Setup

#### Build Archive
```bash
# Command line build
xcodebuild -workspace LeenVibe.xcworkspace \
           -scheme LeenVibe \
           -configuration Release \
           -archivePath ./build/LeenVibe.xcarchive \
           archive

# Export for TestFlight
xcodebuild -exportArchive \
           -archivePath ./build/LeenVibe.xcarchive \
           -exportPath ./build \
           -exportOptionsPlist ExportOptions.plist
```

#### ExportOptions.plist
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>method</key>
    <string>app-store</string>
    <key>teamID</key>
    <string>YOUR_TEAM_ID</string>
    <key>uploadSymbols</key>
    <true/>
    <key>uploadBitcode</key>
    <false/>
</dict>
</plist>
```

#### Upload to TestFlight
```bash
# Using Xcode Organizer
# 1. Window > Organizer
# 2. Select archive
# 3. Distribute App > App Store Connect
# 4. Upload

# Using altool (command line)
xcrun altool --upload-app \
             --type ios \
             --file "LeenVibe.ipa" \
             --username "your@email.com" \
             --password "@keychain:AC_PASSWORD"
```

### 4. App Store Preparation

#### App Store Connect Setup
1. **Create** new app in App Store Connect
2. **Configure** app information and metadata
3. **Upload** screenshots and app preview
4. **Set** pricing and availability
5. **Submit** for review

#### App Store Screenshots
```swift
// Screenshot automation with UI Tests
func testAppStoreScreenshots() {
    let app = XCUIApplication()
    app.launch()
    
    // Dashboard screenshot
    takeScreenshot(name: "01-Dashboard")
    
    // Task management
    app.tabBars.buttons["Monitor"].tap()
    takeScreenshot(name: "02-TaskManagement")
    
    // Settings
    app.tabBars.buttons["Settings"].tap()
    takeScreenshot(name: "03-Settings")
}

func takeScreenshot(name: String) {
    let screenshot = XCUIScreen.main.screenshot()
    let attachment = XCTAttachment(screenshot: screenshot)
    attachment.name = name
    attachment.lifetime = .keepAlways
    add(attachment)
}
```

## Production Infrastructure

### 1. Server Deployment

#### Docker Containerization
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Start application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
```

#### Docker Compose
```yaml
# docker-compose.yml
version: '3.8'

services:
  leenvibe-backend:
    build: .
    ports:
      - "8002:8002"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/leenvibe
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    restart: unless-stopped
    
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: leenvibe
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    
  redis:
    image: redis:7-alpine
    restart: unless-stopped
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - leenvibe-backend
    restart: unless-stopped

volumes:
  postgres_data:
```

#### Nginx Configuration
```nginx
# nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server leenvibe-backend:8002;
    }
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    
    server {
        listen 80;
        server_name api.leenvibe.com;
        return 301 https://$server_name$request_uri;
    }
    
    server {
        listen 443 ssl http2;
        server_name api.leenvibe.com;
        
        # SSL Configuration
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
        
        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
        
        location / {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        location /ws {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

### 2. SSL Certificate Setup

#### Let's Encrypt (Free)
```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Generate certificate
sudo certbot --nginx -d api.leenvibe.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

#### Manual Certificate
```bash
# Generate private key
openssl genrsa -out key.pem 2048

# Generate certificate signing request
openssl req -new -key key.pem -out cert.csr

# Generate self-signed certificate (for testing)
openssl x509 -req -days 365 -in cert.csr -signkey key.pem -out cert.pem
```

### 3. Monitoring & Observability

#### Prometheus + Grafana
```yaml
# monitoring/docker-compose.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana

volumes:
  grafana_data:
```

#### Prometheus Configuration
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'leenvibe-backend'
    static_configs:
      - targets: ['localhost:8002']
    metrics_path: '/metrics'
    scrape_interval: 5s
```

#### Application Metrics
```python
# app/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Business metrics
TASKS_CREATED = Counter('tasks_created_total', 'Total tasks created')
TASKS_COMPLETED = Counter('tasks_completed_total', 'Total tasks completed')
ACTIVE_CONNECTIONS = Gauge('websocket_connections_active', 'Active WebSocket connections')
RESPONSE_TIME = Histogram('http_response_time_seconds', 'HTTP response time')

# Usage in endpoints
@router.post("/api/tasks")
async def create_task():
    TASKS_CREATED.inc()
    # ... task creation logic
```

## Backup & Recovery

### 1. Database Backup
```bash
#!/bin/bash
# backup.sh

# PostgreSQL backup
pg_dump -h localhost -U postgres leenvibe > backup_$(date +%Y%m%d_%H%M%S).sql

# Compress backup
gzip backup_$(date +%Y%m%d_%H%M%S).sql

# Upload to cloud storage (AWS S3)
aws s3 cp backup_$(date +%Y%m%d_%H%M%S).sql.gz s3://leenvibe-backups/

# Cleanup old backups (keep last 30 days)
find . -name "backup_*.sql.gz" -mtime +30 -delete
```

### 2. Application State Backup
```python
# app/services/backup_service.py
import json
import boto3
from datetime import datetime

class BackupService:
    def __init__(self):
        self.s3 = boto3.client('s3')
        
    async def backup_tasks(self):
        tasks = await task_storage.get_all_tasks()
        backup_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0",
            "tasks": [task.dict() for task in tasks]
        }
        
        filename = f"tasks_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        
        self.s3.put_object(
            Bucket='leenvibe-backups',
            Key=filename,
            Body=json.dumps(backup_data)
        )
        
    async def restore_tasks(self, backup_file):
        response = self.s3.get_object(Bucket='leenvibe-backups', Key=backup_file)
        backup_data = json.loads(response['Body'].read())
        
        for task_data in backup_data['tasks']:
            await task_storage.create_task(task_data)
```

### 3. Disaster Recovery Plan
```markdown
## Disaster Recovery Procedures

### RTO (Recovery Time Objective): 4 hours
### RPO (Recovery Point Objective): 1 hour

### Recovery Steps:
1. **Assess Damage**: Identify failed components
2. **Restore Infrastructure**: Deploy new servers if needed
3. **Restore Database**: Latest backup + transaction logs
4. **Restore Application**: Deploy latest Docker images
5. **Validate System**: Run health checks
6. **Resume Operations**: Update DNS, notify users

### Emergency Contacts:
- DevOps Lead: +1-555-0123
- Database Admin: +1-555-0124
- Product Owner: +1-555-0125
```

## Security Checklist

### Backend Security
- [ ] **Input Validation**: All endpoints validate input
- [ ] **SQL Injection**: Parameterized queries only
- [ ] **XSS Protection**: Proper output encoding
- [ ] **CSRF Protection**: CSRF tokens implemented
- [ ] **Rate Limiting**: API rate limits configured
- [ ] **Authentication**: JWT tokens with expiration
- [ ] **Authorization**: Role-based access control
- [ ] **HTTPS Only**: All communications encrypted
- [ ] **Security Headers**: HSTS, CSP, X-Frame-Options
- [ ] **Error Handling**: No sensitive data in errors

### iOS Security
- [ ] **Certificate Pinning**: API certificate validation
- [ ] **Keychain Storage**: Secure credential storage
- [ ] **Code Obfuscation**: Production code protection
- [ ] **Jailbreak Detection**: Runtime security checks
- [ ] **Network Security**: HTTPS/WSS only
- [ ] **Data Encryption**: Local data encrypted
- [ ] **Screen Recording**: Sensitive screen protection
- [ ] **Debug Prevention**: No debug code in production

### Infrastructure Security
- [ ] **Firewall Rules**: Minimal port exposure
- [ ] **VPN Access**: Secure admin access
- [ ] **Log Monitoring**: Security event tracking
- [ ] **Intrusion Detection**: Automated threat detection
- [ ] **Backup Encryption**: Encrypted backup storage
- [ ] **Access Control**: Principle of least privilege
- [ ] **Patch Management**: Regular security updates
- [ ] **Vulnerability Scanning**: Automated security scans

## Performance Optimization

### Backend Optimization
- [ ] **Database Indexing**: Optimal query performance
- [ ] **Connection Pooling**: Efficient database connections
- [ ] **Caching Strategy**: Redis for frequently accessed data
- [ ] **Async Processing**: Non-blocking operations
- [ ] **Load Balancing**: Multiple server instances
- [ ] **CDN Integration**: Static asset delivery
- [ ] **Compression**: Gzip response compression
- [ ] **Memory Management**: Efficient memory usage

### iOS Optimization
- [ ] **Image Optimization**: Compressed, cached images
- [ ] **Network Efficiency**: Batched API calls
- [ ] **Memory Management**: ARC optimization
- [ ] **Background Processing**: Efficient background tasks
- [ ] **UI Performance**: 60fps rendering
- [ ] **Battery Optimization**: Minimal background activity
- [ ] **App Size**: Minimal binary size
- [ ] **Launch Time**: Fast app startup

## Deployment Checklist

### Pre-deployment
- [ ] **Code Review**: All changes reviewed
- [ ] **Testing**: Unit, integration, e2e tests pass
- [ ] **Performance**: Load testing completed
- [ ] **Security**: Security scan completed
- [ ] **Documentation**: Deployment docs updated
- [ ] **Backup**: Current state backed up
- [ ] **Rollback Plan**: Rollback procedure ready
- [ ] **Monitoring**: Alerts configured

### Deployment
- [ ] **Maintenance Mode**: Enable if needed
- [ ] **Database Migration**: Schema updates applied
- [ ] **Application Deployment**: New version deployed
- [ ] **Configuration**: Environment variables updated
- [ ] **SSL Certificates**: Valid certificates installed
- [ ] **Health Checks**: All services healthy
- [ ] **Smoke Tests**: Critical paths verified
- [ ] **Performance**: Response times acceptable

### Post-deployment
- [ ] **Monitoring**: Metrics trending normally
- [ ] **Error Rates**: Error rates within limits
- [ ] **User Experience**: No user-reported issues
- [ ] **Documentation**: Deployment logged
- [ ] **Team Notification**: Stakeholders informed
- [ ] **Cleanup**: Old versions cleaned up
- [ ] **Lessons Learned**: Deployment reviewed
- [ ] **Next Steps**: Future improvements planned

## Conclusion

This production deployment guide provides comprehensive instructions for deploying LeenVibe in a secure, scalable, and maintainable manner. Following these procedures ensures a robust production environment capable of supporting real-world usage while maintaining security and performance standards.

Regular reviews and updates of this guide are essential as the system evolves and new requirements emerge.