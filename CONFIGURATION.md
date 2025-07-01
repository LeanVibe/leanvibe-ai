# LeanVibe Configuration Guide

This guide covers environment configuration for LeanVibe across development, staging, and production environments.

## Quick Start

1. **Copy environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Update configuration:**
   ```bash
   # Set your environment
   LEANVIBE_ENV=development  # or staging, production
   
   # Set API URL (iOS will auto-detect based on environment)
   LEANVIBE_API_URL=http://localhost:8001
   ```

3. **Start the backend server:**
   ```bash
   cd leanvibe-backend
   python test_server.py
   ```

4. **Build iOS app:**
   ```bash
   cd leanvibe-ios
   xcodebuild -project LeanVibe.xcodeproj -scheme LeanVibe
   ```

## Environment Configuration

### Development Environment

**Backend (.env):**
```bash
LEANVIBE_ENV=development
LEANVIBE_HOST=localhost
LEANVIBE_PORT=8001
LEANVIBE_MLX_STRATEGY=MOCK
LEANVIBE_ENABLE_LOGGING=true
```

**iOS (automatic):**
- API URL: `http://localhost:8001`
- WebSocket: `ws://localhost:8001/ws`
- Debug logging: Enabled
- Certificate pinning: Disabled

### Staging Environment

**Backend (.env):**
```bash
LEANVIBE_ENV=staging
LEANVIBE_HOST=0.0.0.0
LEANVIBE_PORT=8001
LEANVIBE_MLX_STRATEGY=PRAGMATIC
LEANVIBE_SECRET_KEY=your-staging-secret
LEANVIBE_DATABASE_URL=postgresql://...
```

**iOS (Info.plist):**
```xml
<key>API_BASE_URL</key>
<string>https://staging-api.leanvibe.ai</string>
```

### Production Environment

**Backend (.env):**
```bash
LEANVIBE_ENV=production
LEANVIBE_HOST=0.0.0.0
LEANVIBE_PORT=8001
LEANVIBE_MLX_STRATEGY=PRODUCTION
LEANVIBE_SECRET_KEY=your-production-secret
LEANVIBE_DATABASE_URL=postgresql://...
LEANVIBE_REDIS_URL=redis://...
```

**iOS (Info.plist):**
```xml
<key>API_BASE_URL</key>
<string>https://api.leanvibe.ai</string>
<key>VOICE_FEATURES_ENABLED</key>
<true/>
<key>CODE_COMPLETION_ENABLED</key>
<true/>
```

## iOS Configuration

### Environment Detection

The iOS app automatically detects environment:

1. **Debug Build**: Uses localhost (development)
2. **TestFlight**: Uses staging URLs
3. **App Store**: Uses production URLs

### Manual Override

Override via environment variables:
```bash
# During development
export LEANVIBE_API_URL=http://192.168.1.100:8001
```

Or in Xcode scheme environment variables.

### Configuration Validation

The app validates configuration on startup:
```swift
// Validate in AppDelegate or SceneDelegate
do {
    try AppConfiguration.shared.validateConfiguration()
    AppConfiguration.shared.printConfiguration() // Debug only
} catch {
    fatalError("Configuration error: \(error)")
}
```

## Backend Configuration

### MLX Strategy Selection

**MOCK** (Development):
- Fast, reliable responses
- No GPU required
- Perfect for testing

**PRAGMATIC** (Staging):
- Balanced performance/quality
- Good for testing with real AI

**PRODUCTION** (Production):
- Best quality responses
- Requires MLX-compatible hardware
- Full GPU utilization

### CORS Configuration

**Development:**
```python
allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"]
```

**Production:**
```python
allow_origins=["https://app.leanvibe.ai", "https://leanvibe.ai"]
```

### Security Settings

**Required for Production:**
- `LEANVIBE_SECRET_KEY`: Secure random key
- `LEANVIBE_DATABASE_URL`: Production database
- CORS origins: Specific domains only
- HTTPS only
- Rate limiting enabled

## Deployment Configuration

### Docker Deployment

**Backend Dockerfile:**
```dockerfile
FROM python:3.12-slim

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Set environment
ENV LEANVIBE_ENV=production
ENV LEANVIBE_HOST=0.0.0.0
ENV LEANVIBE_PORT=8001

# Start server
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

**Environment Variables:**
```bash
# Required
LEANVIBE_SECRET_KEY=your-secret-key
LEANVIBE_DATABASE_URL=postgresql://...

# Optional
LEANVIBE_MLX_STRATEGY=PRODUCTION
LEANVIBE_REDIS_URL=redis://...
```

### iOS App Store Configuration

**Build Settings:**
1. Set `API_BASE_URL` in Info.plist
2. Configure provisioning profiles
3. Enable required capabilities:
   - Microphone access
   - Network access
   - Background processing

**Release Build:**
```bash
xcodebuild -project LeanVibe.xcodeproj \
           -scheme LeanVibe \
           -configuration Release \
           -archivePath LeanVibe.xcarchive \
           archive
```

## Feature Flags

### Backend Feature Flags

```bash
# MLX Features
LEANVIBE_MLX_STRATEGY=PRODUCTION  # MOCK, PRAGMATIC, PRODUCTION

# Monitoring
LEANVIBE_ENABLE_MONITORING=true
LEANVIBE_ENABLE_METRICS=true

# Security
LEANVIBE_ENABLE_RATE_LIMITING=true
LEANVIBE_ENABLE_API_KEY_AUTH=true
```

### iOS Feature Flags

```xml
<!-- Info.plist -->
<key>VOICE_FEATURES_ENABLED</key>
<true/>
<key>CODE_COMPLETION_ENABLED</key>
<true/>
<key>ANALYTICS_ENABLED</key>
<false/>
```

## Troubleshooting

### Common Issues

**iOS can't connect to backend:**
```swift
// Check configuration
AppConfiguration.shared.printConfiguration()

// Verify URLs
print("API URL: \(AppConfiguration.shared.apiBaseURL)")
print("WebSocket: \(AppConfiguration.shared.webSocketURL)")
```

**Backend CORS errors:**
```bash
# Check environment
echo $LEANVIBE_ENV

# Verify CORS origins
curl -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: POST" \
     -X OPTIONS \
     http://localhost:8001/health
```

**MLX not working:**
```bash
# Check strategy
echo $LEANVIBE_MLX_STRATEGY

# Test MLX endpoint
curl http://localhost:8001/health-mlx
```

### Debug Mode

**Enable debug logging:**
```bash
# Backend
LEANVIBE_ENV=development
export PYTHONPATH=$PYTHONPATH:.

# iOS
# Debug builds automatically enable logging
```

### Production Checklist

**Backend:**
- [ ] `LEANVIBE_ENV=production`
- [ ] `LEANVIBE_SECRET_KEY` set
- [ ] Database URL configured
- [ ] CORS origins restricted
- [ ] Rate limiting enabled
- [ ] HTTPS configured
- [ ] Monitoring enabled

**iOS:**
- [ ] Production API URL in Info.plist
- [ ] Certificate pinning enabled
- [ ] Analytics configured
- [ ] Push notifications configured
- [ ] App Store provisioning profile

## Security Considerations

### Production Security

1. **Never commit secrets** to version control
2. **Use environment variables** for all secrets
3. **Enable HTTPS** for all environments except localhost
4. **Restrict CORS origins** in production
5. **Enable rate limiting** and monitoring
6. **Regular security audits** of dependencies

### iOS Security

1. **Certificate pinning** for production API
2. **Keychain storage** for sensitive data
3. **App Transport Security** enabled
4. **Network security** configured
5. **Data encryption** at rest and in transit

## Performance Optimization

### Backend Performance

```bash
# Production optimizations
LEANVIBE_MLX_STRATEGY=PRODUCTION  # Best AI quality
LEANVIBE_ENABLE_MONITORING=true   # Track performance
LEANVIBE_REDIS_URL=redis://...     # Caching layer
```

### iOS Performance

```xml
<!-- Optimize for production -->
<key>VOICE_FEATURES_ENABLED</key>
<true/>
<key>ANALYTICS_ENABLED</key>
<true/>
```

## Monitoring and Logging

### Backend Monitoring

```bash
# Enable monitoring
LEANVIBE_ENABLE_MONITORING=true
LEANVIBE_METRICS_PORT=9090

# Log levels
LEANVIBE_LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

### iOS Analytics

```swift
// Configure analytics in production
if AppConfiguration.shared.isAnalyticsEnabled {
    Analytics.configure(apiKey: AppConfiguration.shared.analyticsAPIKey)
}
```

---

For more information, see:
- [Backend API Documentation](./docs/api.md)
- [iOS Architecture Guide](./leanvibe-ios/README.md)
- [Deployment Guide](./docs/deployment.md)