FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt* pyproject.toml* ./
COPY app/ ./app/

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install fastapi uvicorn websockets pydantic aiofiles httpx rich pyyaml psutil pytest pytest-asyncio

# Create non-root user
RUN useradd -m -u 1000 leanvibe && \
    chown -R leanvibe:leanvibe /app
USER leanvibe

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start the application
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF < /dev/null