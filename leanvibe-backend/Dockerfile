# LeanVibe Backend Production Dockerfile
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r leanvibe \
    && useradd -r -g leanvibe leanvibe

# Copy Python packages from builder
COPY --from=builder /root/.local /home/leanvibe/.local

# Set working directory
WORKDIR /app

# Copy application code
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Create necessary directories
RUN mkdir -p /app/data /app/logs /app/cache \
    && chown -R leanvibe:leanvibe /app

# Switch to non-root user
USER leanvibe

# Set environment variables
ENV PATH=/home/leanvibe/.local/bin:$PATH
ENV PYTHONPATH=/app/src
ENV LEANVIBE_DATA_DIR=/app/data
ENV LEANVIBE_LOG_DIR=/app/logs
ENV LEANVIBE_CACHE_DIR=/app/cache

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Expose port
EXPOSE 8001

# Start command
CMD ["python", "-m", "app.main"]