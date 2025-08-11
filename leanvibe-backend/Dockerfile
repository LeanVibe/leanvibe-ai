# Multi-stage production-ready Dockerfile for LeanVibe Backend
# Stage 1: Build environment with all dependencies
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create and set working directory
WORKDIR /build

# Copy dependency files
COPY requirements.txt* pyproject.toml* ./

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install fastapi uvicorn[standard] websockets pydantic aiofiles httpx rich pyyaml psutil \
    pytest pytest-asyncio python-dotenv pydantic-settings asyncpg redis neo4j chromadb \
    sqlalchemy alembic bcrypt python-jose[cryptography] python-multipart

# Stage 2: Runtime environment
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app"

# Install runtime system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get autoremove -y \
    && apt-get autoclean

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Create application directory and user
RUN groupadd -r leanvibe && useradd -r -g leanvibe -d /app -s /sbin/nologin leanvibe
WORKDIR /app

# Copy application code
COPY --chown=leanvibe:leanvibe app/ ./app/
COPY --chown=leanvibe:leanvibe VERSION ./
COPY --chown=leanvibe:leanvibe *.py ./

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/.sessions && \
    chown -R leanvibe:leanvibe /app

# Switch to non-root user
USER leanvibe

# Expose port
EXPOSE 8000

# Health check using production health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/production/health/live || exit 1

# Production command with optimized settings
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4", \
     "--loop", "uvloop", \
     "--http", "httptools", \
     "--access-log", \
     "--no-server-header"]

# Development stage (optional)
FROM production as development

USER root

# Install development dependencies
RUN pip install pytest pytest-asyncio pytest-cov black isort mypy pre-commit

# Install git for development
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

USER leanvibe

# Development command with hot reload
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--reload", \
     "--reload-dir", "/app/app"]