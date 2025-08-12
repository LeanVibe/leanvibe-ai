"""
Infrastructure Agent - Docker & Deployment Configuration Generation  
Generates Docker containers, deployment configs, and infrastructure as code
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


class InfrastructureAgent(BaseAIAgent):
    """AI agent that generates infrastructure and deployment configurations"""
    
    def __init__(self):
        super().__init__(AgentType.INFRASTRUCTURE)
    
    async def _execute_agent(
        self,
        mvp_project_id: UUID,
        input_data: Dict[str, Any],
        progress_callback: Optional[callable] = None
    ) -> AgentResult:
        """Generate infrastructure and deployment configurations"""
        
        blueprint_data = input_data.get("blueprint", {})
        backend_output = input_data.get("backend_output", {})
        frontend_output = input_data.get("frontend_output", {})
        
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
            temp_dir = tempfile.mkdtemp(prefix=f"mvp_infrastructure_{mvp_project_id}_")
            
            # Progress tracking
            total_steps = 6
            current_step = 0
            
            # Step 1: Generate Docker configurations
            if progress_callback:
                await progress_callback(self.agent_type, AgentStatus.RUNNING, (current_step / total_steps) * 100)
            
            docker_configs = await self._generate_docker_configs(blueprint, backend_output, frontend_output)
            for config_name, config_content in docker_configs.items():
                await self._write_file(temp_dir, config_name, config_content)
            current_step += 1
            
            # Step 2: Generate Kubernetes manifests
            if progress_callback:
                await progress_callback(self.agent_type, AgentStatus.RUNNING, (current_step / total_steps) * 100)
            
            k8s_configs = await self._generate_kubernetes_configs(blueprint)
            k8s_dir = "k8s"
            for config_name, config_content in k8s_configs.items():
                await self._write_file(temp_dir, f"{k8s_dir}/{config_name}", config_content)
            current_step += 1
            
            # Step 3: Generate CI/CD pipeline
            if progress_callback:
                await progress_callback(self.agent_type, AgentStatus.RUNNING, (current_step / total_steps) * 100)
            
            cicd_configs = await self._generate_cicd_pipeline(blueprint)
            for config_name, config_content in cicd_configs.items():
                await self._write_file(temp_dir, config_name, config_content)
            current_step += 1
            
            # Step 4: Generate environment configurations
            if progress_callback:
                await progress_callback(self.agent_type, AgentStatus.RUNNING, (current_step / total_steps) * 100)
            
            env_configs = await self._generate_environment_configs(blueprint)
            for config_name, config_content in env_configs.items():
                await self._write_file(temp_dir, config_name, config_content)
            current_step += 1
            
            # Step 5: Generate deployment scripts
            if progress_callback:
                await progress_callback(self.agent_type, AgentStatus.RUNNING, (current_step / total_steps) * 100)
            
            deploy_scripts = await self._generate_deployment_scripts(blueprint)
            scripts_dir = "scripts"
            for script_name, script_content in deploy_scripts.items():
                await self._write_file(temp_dir, f"{scripts_dir}/{script_name}", script_content)
                # Make scripts executable
                script_path = os.path.join(temp_dir, scripts_dir, script_name)
                os.chmod(script_path, 0o755)
            current_step += 1
            
            # Step 6: Generate infrastructure documentation
            if progress_callback:
                await progress_callback(self.agent_type, AgentStatus.RUNNING, (current_step / total_steps) * 100)
            
            docs = await self._generate_infrastructure_docs(blueprint)
            await self._write_file(temp_dir, "DEPLOYMENT.md", docs)
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
                    "deployment_type": blueprint.deployment_config.get("type", "docker"),
                    "scaling_config": blueprint.scaling_config,
                    "infrastructure_files": len(artifacts)
                },
                artifacts=artifacts,
                metrics={
                    "config_files_generated": len(artifacts),
                    "deployment_ready": True,
                    "kubernetes_support": True,
                    "cicd_pipeline": True,
                    "auto_scaling": bool(blueprint.scaling_config)
                },
                confidence_score=confidence_score
            )
            
        except Exception as e:
            self.logger.error(f"Infrastructure generation failed: {e}")
            return AgentResult(
                agent_type=self.agent_type,
                status=AgentStatus.FAILED,
                error_message=str(e)
            )
    
    async def _generate_docker_configs(self, blueprint: TechnicalBlueprint, backend_output: Dict, frontend_output: Dict) -> Dict[str, str]:
        """Generate Docker configurations"""
        
        configs = {}
        
        # Backend Dockerfile (if not already generated)
        configs["backend/Dockerfile"] = '''FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \\
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 8765

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8765/health || exit 1

# Start application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8765"]'''
        
        # Frontend Dockerfile
        configs["frontend/Dockerfile"] = '''FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy source code
COPY . .

# Build application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built application
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
    CMD wget --no-verbose --tries=1 --spider http://localhost/health || exit 1

CMD ["nginx", "-g", "daemon off;"]'''
        
        # Nginx configuration
        configs["frontend/nginx.conf"] = '''server {
    listen 80;
    server_name localhost;
    
    root /usr/share/nginx/html;
    index index.html;
    
    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Handle client routing
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # API proxy
    location /api/ {
        proxy_pass http://backend:8765/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\\n";
        add_header Content-Type text/plain;
    }
}'''
        
        # Docker Compose for local development
        configs["docker-compose.yml"] = '''version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8765:8765"
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/mvp
      - SECRET_KEY=your-secret-key-here
      - DEBUG=true
    depends_on:
      - postgres
    volumes:
      - ./backend:/app
    command: ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8765", "--reload"]

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:80"
    depends_on:
      - backend

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=mvp
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:'''
        
        # Production Docker Compose
        configs["docker-compose.prod.yml"] = '''version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=false
    depends_on:
      - postgres
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    depends_on:
      - backend
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend
    restart: unless-stopped

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:'''
        
        return configs
    
    async def _generate_kubernetes_configs(self, blueprint: TechnicalBlueprint) -> Dict[str, str]:
        """Generate Kubernetes manifests"""
        
        configs = {}
        
        # Namespace
        configs["namespace.yaml"] = '''apiVersion: v1
kind: Namespace
metadata:
  name: mvp-app
  labels:
    name: mvp-app'''
        
        # Backend deployment
        configs["backend-deployment.yaml"] = '''apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: mvp-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: mvp-backend:latest
        ports:
        - containerPort: 8765
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: database-url
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: secret-key
        livenessProbe:
          httpGet:
            path: /health
            port: 8765
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8765
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            cpu: 100m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 512Mi'''
        
        # Frontend deployment
        configs["frontend-deployment.yaml"] = '''apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: mvp-app
spec:
  replicas: 2
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: frontend
        image: mvp-frontend:latest
        ports:
        - containerPort: 80
        livenessProbe:
          httpGet:
            path: /health
            port: 80
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            cpu: 50m
            memory: 64Mi
          limits:
            cpu: 200m
            memory: 128Mi'''
        
        # Services
        configs["services.yaml"] = '''apiVersion: v1
kind: Service
metadata:
  name: backend-service
  namespace: mvp-app
spec:
  selector:
    app: backend
  ports:
  - port: 8765
    targetPort: 8765
  type: ClusterIP
---
apiVersion: v1
kind: Service
metadata:
  name: frontend-service
  namespace: mvp-app
spec:
  selector:
    app: frontend
  ports:
  - port: 80
    targetPort: 80
  type: ClusterIP'''
        
        # Ingress
        configs["ingress.yaml"] = '''apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: mvp-ingress
  namespace: mvp-app
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - your-domain.com
    secretName: mvp-tls
  rules:
  - host: your-domain.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: backend-service
            port:
              number: 8765
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 80'''
        
        return configs
    
    async def _generate_cicd_pipeline(self, blueprint: TechnicalBlueprint) -> Dict[str, str]:
        """Generate CI/CD pipeline configurations"""
        
        configs = {}
        
        # GitHub Actions workflow
        configs[".github/workflows/deploy.yml"] = '''name: Deploy MVP

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        
    - name: Install Python dependencies
      run: |
        cd backend
        pip install -r requirements.txt
        
    - name: Install Node dependencies
      run: |
        cd frontend
        npm ci
        
    - name: Run backend tests
      run: |
        cd backend
        pytest
        
    - name: Run frontend tests
      run: |
        cd frontend
        npm test
        
  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
    - uses: actions/checkout@v3
    
    - name: Log in to Container Registry
      uses: docker/login-action@v2
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
        
    - name: Build and push backend image
      uses: docker/build-push-action@v3
      with:
        context: ./backend
        push: true
        tags: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}-backend:latest
        
    - name: Build and push frontend image
      uses: docker/build-push-action@v3
      with:
        context: ./frontend
        push: true
        tags: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}-frontend:latest
        
  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to Kubernetes
      run: |
        echo "${{ secrets.KUBECONFIG }}" | base64 -d > kubeconfig
        export KUBECONFIG=kubeconfig
        kubectl apply -f k8s/
        kubectl rollout restart deployment/backend -n mvp-app
        kubectl rollout restart deployment/frontend -n mvp-app'''
        
        return configs
    
    async def _generate_environment_configs(self, blueprint: TechnicalBlueprint) -> Dict[str, str]:
        """Generate environment configuration files"""
        
        configs = {}
        
        # Environment variables template
        configs[".env.example"] = '''# Database
DATABASE_URL=postgresql://username:password@localhost:5432/mvp

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# Frontend
REACT_APP_API_URL=http://localhost:8765

# Redis (optional)
REDIS_URL=redis://localhost:6379

# Email (optional)
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your-email@example.com
SMTP_PASSWORD=your-email-password

# External APIs
# Add your external API keys here'''
        
        # Kubernetes secrets template
        configs["k8s/secrets.yaml"] = '''apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
  namespace: mvp-app
type: Opaque
stringData:
  database-url: "postgresql://username:password@postgres:5432/mvp"
  secret-key: "your-secret-key-here"
  jwt-secret: "your-jwt-secret-here"'''
        
        return configs
    
    async def _generate_deployment_scripts(self, blueprint: TechnicalBlueprint) -> Dict[str, str]:
        """Generate deployment scripts"""
        
        scripts = {}
        
        # Local development script
        scripts["dev.sh"] = '''#!/bin/bash
set -e

echo "Starting local development environment..."

# Build and start services
docker-compose up --build -d

echo "Services starting..."
echo "Backend: http://localhost:8765"
echo "Frontend: http://localhost:3000"
echo "Database: localhost:5432"

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 10

# Check backend health
curl -f http://localhost:8765/health || echo "Backend not ready yet"

# Check frontend health
curl -f http://localhost:3000/health || echo "Frontend not ready yet"

echo "Development environment is ready!"'''
        
        # Production deployment script
        scripts["deploy.sh"] = '''#!/bin/bash
set -e

echo "Deploying to production..."

# Check if kubectl is configured
kubectl cluster-info || {
    echo "Error: kubectl is not configured"
    exit 1
}

# Apply Kubernetes manifests
echo "Applying Kubernetes manifests..."
kubectl apply -f k8s/

# Wait for deployments to be ready
echo "Waiting for deployments..."
kubectl wait --for=condition=available --timeout=300s deployment/backend -n mvp-app
kubectl wait --for=condition=available --timeout=300s deployment/frontend -n mvp-app

# Get external IP
EXTERNAL_IP=$(kubectl get service frontend-service -n mvp-app -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
echo "Application deployed successfully!"
echo "Access your application at: http://$EXTERNAL_IP"'''
        
        # Database migration script
        scripts["migrate.sh"] = '''#!/bin/bash
set -e

echo "Running database migrations..."

# Run migrations in the backend container
docker-compose exec backend alembic upgrade head

echo "Migrations completed!"'''
        
        return scripts
    
    async def _generate_infrastructure_docs(self, blueprint: TechnicalBlueprint) -> str:
        """Generate infrastructure documentation"""
        
        docs = '''# Deployment Guide

This document provides instructions for deploying your MVP application.

## Architecture

The application consists of:
- **Backend**: FastAPI application with PostgreSQL database
- **Frontend**: React application served by Nginx
- **Infrastructure**: Docker containers with Kubernetes orchestration

## Local Development

### Prerequisites
- Docker and Docker Compose
- Node.js 18+
- Python 3.11+

### Quick Start
```bash
# Start all services
./scripts/dev.sh

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8765
# API Documentation: http://localhost:8765/docs
```

### Individual Services
```bash
# Backend only
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend only
cd frontend
npm install
npm start
```

## Production Deployment

### Prerequisites
- Kubernetes cluster
- kubectl configured
- Container registry access

### Deployment Steps

1. **Build and push images**:
   ```bash
   # Build images
   docker build -t your-registry/mvp-backend:latest ./backend
   docker build -t your-registry/mvp-frontend:latest ./frontend
   
   # Push to registry
   docker push your-registry/mvp-backend:latest
   docker push your-registry/mvp-frontend:latest
   ```

2. **Configure secrets**:
   ```bash
   # Update k8s/secrets.yaml with your values
   kubectl apply -f k8s/secrets.yaml
   ```

3. **Deploy application**:
   ```bash
   ./scripts/deploy.sh
   ```

## Environment Variables

### Backend
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT signing key
- `DEBUG`: Enable debug mode (development only)

### Frontend
- `REACT_APP_API_URL`: Backend API base URL

## Monitoring

The application includes health check endpoints:
- Backend: `GET /health`
- Frontend: `GET /health`

### Kubernetes Health Checks
- Liveness probes: Restart containers if unhealthy
- Readiness probes: Route traffic only to ready containers

## Scaling

### Horizontal Scaling
```bash
# Scale backend
kubectl scale deployment backend --replicas=5 -n mvp-app

# Scale frontend
kubectl scale deployment frontend --replicas=3 -n mvp-app
```

### Vertical Scaling
Edit resource limits in deployment YAML files and reapply.

## Security

### Best Practices Implemented
- Non-root containers
- Security headers in Nginx
- Kubernetes network policies
- Secret management
- TLS termination at ingress

### Additional Recommendations
- Regular security updates
- Vulnerability scanning
- Network segmentation
- Access controls

## Troubleshooting

### Common Issues

**Backend not starting**:
```bash
# Check logs
kubectl logs -f deployment/backend -n mvp-app

# Check database connection
kubectl exec -it deployment/backend -n mvp-app -- python -c "from app.models.database import engine; print(engine.execute('SELECT 1'))"
```

**Frontend not loading**:
```bash
# Check logs
kubectl logs -f deployment/frontend -n mvp-app

# Check nginx configuration
kubectl exec -it deployment/frontend -n mvp-app -- nginx -t
```

### Support
For additional support, check the application logs and Kubernetes events:
```bash
kubectl get events -n mvp-app --sort-by=.metadata.creationTimestamp
```
'''
        
        return docs
    
    # Helper methods
    
    async def _write_file(self, base_dir: str, file_path: str, content: str):
        """Write content to file, creating directories as needed"""
        full_path = os.path.join(base_dir, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    async def _calculate_confidence(self, blueprint: TechnicalBlueprint, temp_dir: str) -> float:
        """Calculate confidence score for generated infrastructure"""
        confidence_factors = []
        
        # Blueprint completeness
        blueprint_score = blueprint.confidence_score if hasattr(blueprint, 'confidence_score') else 0.8
        confidence_factors.append(blueprint_score)
        
        # Infrastructure completeness
        expected_configs = ["docker-compose.yml", "k8s/namespace.yaml", ".github/workflows/deploy.yml"]
        generated_files = await self._collect_artifacts(temp_dir)
        completeness = len([f for f in expected_configs if any(f in path for path in generated_files)]) / len(expected_configs)
        confidence_factors.append(completeness)
        
        # Deployment complexity handling
        deployment_config = blueprint.deployment_config or {}
        scaling_config = blueprint.scaling_config or {}
        complexity_score = 0.8 + (0.1 if deployment_config else 0) + (0.1 if scaling_config else 0)
        confidence_factors.append(min(1.0, complexity_score))
        
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
        """Perform quality checks on generated infrastructure"""
        checks = []
        
        # Check essential files
        essential_files = ["docker-compose.yml", "k8s/", ".github/workflows/"]
        missing_files = []
        for essential in essential_files:
            if not any(essential in artifact for artifact in result.artifacts):
                missing_files.append(essential)
        
        if missing_files:
            checks.append(QualityGateCheck(
                check_name="essential_infrastructure",
                passed=False,
                score=0.5,
                details=f"Missing essential infrastructure: {missing_files}",
                fix_suggestions=[f"Generate {f}" for f in missing_files]
            ))
        else:
            checks.append(QualityGateCheck(
                check_name="essential_infrastructure",
                passed=True,
                score=1.0,
                details="All essential infrastructure files generated"
            ))
        
        # Check deployment readiness
        has_deployment = result.metrics.get("deployment_ready", False)
        checks.append(QualityGateCheck(
            check_name="deployment_readiness",
            passed=has_deployment,
            score=1.0 if has_deployment else 0.6,
            details="Deployment configuration ready" if has_deployment else "Limited deployment configuration"
        ))
        
        # Check CI/CD pipeline
        has_cicd = result.metrics.get("cicd_pipeline", False)
        checks.append(QualityGateCheck(
            check_name="cicd_pipeline",
            passed=has_cicd,
            score=1.0 if has_cicd else 0.7,
            details="CI/CD pipeline configured" if has_cicd else "Manual deployment only"
        ))
        
        # Calculate overall result
        overall_score = sum(check.score for check in checks) / len(checks) if checks else 0.0
        overall_passed = all(check.passed for check in checks)
        
        return QualityGateResult(
            overall_passed=overall_passed,
            overall_score=overall_score,
            checks=checks
        )