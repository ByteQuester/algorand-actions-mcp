# Multi-stage Dockerfile for Algorand DeFi Lending Platform
FROM node:18-alpine as node-builder

WORKDIR /app

# Copy package files for dependency resolution
COPY src/packages/package.json src/packages/pnpm-lock.yaml* ./packages/
COPY src/mcp-services/*/package.json ./mcp-services/

# Install Node.js dependencies
RUN npm install -g pnpm
RUN cd packages && pnpm install --frozen-lockfile
WORKDIR /app
COPY src/mcp-services ./mcp-services
COPY src/packages ./packages

# Build TypeScript packages
RUN cd packages && pnpm run build
RUN cd mcp-services && for service in */; do cd "$service" && pnpm run build && cd ..; done

# Python stage for business logic engines
FROM python:3.9-slim as python-builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python requirements
COPY src/business-logic-engines/*/requirements.txt ./requirements/
RUN find requirements/ -name "requirements.txt" -exec cat {} \; | sort -u > combined-requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r combined-requirements.txt

# Copy Python source code
COPY src/business-logic-engines ./business-logic-engines

# Final runtime stage
FROM node:18-alpine as runtime

# Install system dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    curl \
    postgresql-client \
    redis

WORKDIR /app

# Copy built Node.js applications
COPY --from=node-builder /app/packages/dist ./packages/dist
COPY --from=node-builder /app/mcp-services ./mcp-services
COPY --from=node-builder /app/packages/node_modules ./packages/node_modules

# Copy Python applications and dependencies
COPY --from=python-builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=python-builder /app/business-logic-engines ./business-logic-engines

# Copy configuration and scripts
COPY config ./config
COPY database ./database
COPY scripts ./scripts

# Create non-root user for security
RUN addgroup -g 1001 -S appgroup && \
    adduser -S appuser -u 1001 -G appgroup

# Set permissions
RUN chown -R appuser:appgroup /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8080}/health || exit 1

# Environment variables
ENV NODE_ENV=production
ENV PORT=8080
ENV LOG_LEVEL=info

# Expose port
EXPOSE 8080

# Start script
CMD ["node", "mcp-services/algorand-reader-mcp/server.js"]