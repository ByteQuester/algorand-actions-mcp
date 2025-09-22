# Simplified Dockerfile for Algorand DeFi Lending Platform
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy Python requirements and install dependencies
COPY requirements-minimal.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY src ./src
COPY config ./config
COPY database ./database
COPY scripts ./scripts

# Create non-root user for security
RUN groupadd -g 1001 appgroup || true && \
    useradd -u 1001 -g appgroup -s /bin/false -M appuser

# Set permissions
RUN chown -R appuser:appgroup /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8080}/health || exit 1

# Environment variables
ENV PYTHONPATH=/app/src
ENV PORT=8080
ENV LOG_LEVEL=info

# Expose port
EXPOSE 8080

# Start the Python API server
CMD ["python3", "src/api/src/server.py"]