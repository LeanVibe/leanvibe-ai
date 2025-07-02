# LeanVibe CLI Production Dockerfile
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
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
    git \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r leanvibe \
    && useradd -r -g leanvibe leanvibe

# Copy Python packages from builder
COPY --from=builder /root/.local /home/leanvibe/.local

# Set working directory
WORKDIR /app

# Copy application code
COPY src/ ./src/
COPY cli.py .

# Create necessary directories
RUN mkdir -p /app/config /app/logs \
    && chown -R leanvibe:leanvibe /app

# Switch to non-root user
USER leanvibe

# Set environment variables
ENV PATH=/home/leanvibe/.local/bin:$PATH
ENV PYTHONPATH=/app/src
ENV LEANVIBE_CLI_CONFIG_DIR=/app/config
ENV LEANVIBE_CLI_LOG_DIR=/app/logs

# Entry point
ENTRYPOINT ["python", "cli.py"]
CMD ["--help"]