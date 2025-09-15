# =============================================================================
# ALGORAND WRITER MCP SERVICE - PRODUCTION DOCKER BUILD
# =============================================================================
# Multi-stage Docker build for production-ready Algorand Writer MCP service
# Optimized for security, performance, and minimal image size

# -----------------------------------------------------------------------------
# STAGE 1: Dependencies & Build
# -----------------------------------------------------------------------------
FROM node:20-alpine AS dependencies

# Install system dependencies for build
RUN apk add --no-cache \
    libc6-compat \
    git \
    python3 \
    make \
    g++

# Set working directory
WORKDIR /app

# Enable pnpm
RUN corepack enable pnpm

# Copy workspace configuration
COPY pnpm-workspace.yaml ./
COPY pnpm-lock.yaml ./
COPY package.json ./

# Copy package definitions
COPY apps/mcp-services/algorand-writer-mcp/package.json ./apps/mcp-services/algorand-writer-mcp/
COPY packages/ ./packages/

# Install all dependencies
RUN pnpm install --frozen-lockfile --prefer-offline

# -----------------------------------------------------------------------------
# STAGE 2: Build Application
# -----------------------------------------------------------------------------
FROM dependencies AS builder

# Copy source code
COPY apps/mcp-services/algorand-writer-mcp/ ./apps/mcp-services/algorand-writer-mcp/

# Build shared packages first
RUN pnpm --filter "@algorand-showcase/*" run build

# Build the main application
RUN pnpm --filter "@algorand-showcase/actions-mcp-worker" run build

# Remove development dependencies
RUN pnpm prune --prod

# -----------------------------------------------------------------------------
# STAGE 3: Production Runtime
# -----------------------------------------------------------------------------
FROM node:20-alpine AS production

# Install only runtime dependencies
RUN apk add --no-cache \
    wget \
    curl \
    tini

# Create non-root user with specific UID/GID for security
RUN addgroup --system --gid 1001 mcpservice && \
    adduser --system --uid 1001 --ingroup mcpservice mcpservice

# Set secure working directory
WORKDIR /app

# Copy application files with proper ownership
COPY --from=builder --chown=mcpservice:mcpservice /app/node_modules ./node_modules
COPY --from=builder --chown=mcpservice:mcpservice /app/packages ./packages
COPY --from=builder --chown=mcpservice:mcpservice /app/apps/mcp-services/algorand-writer-mcp ./apps/mcp-services/algorand-writer-mcp
COPY --from=builder --chown=mcpservice:mcpservice /app/pnpm-workspace.yaml ./pnpm-workspace.yaml
COPY --from=builder --chown=mcpservice:mcpservice /app/package.json ./package.json

# Create required directories with proper permissions
RUN mkdir -p /app/logs /app/tmp && \
    chown -R mcpservice:mcpservice /app/logs /app/tmp

# Switch to non-root user
USER mcpservice

# Configure health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:${PORT:-8080}/health || exit 1

# Expose service port
EXPOSE 8080

# Production environment defaults
ENV NODE_ENV=production \
    PORT=8080 \
    ALGORAND_NETWORK=testnet \
    ALGORAND_ALGOD=https://testnet-api.algonode.cloud \
    ALGORAND_INDEXER=https://testnet-idx.algonode.cloud \
    READ_ONLY=false \
    ALLOW_MAINNET=false \
    LOG_LEVEL=info \
    PERFORMANCE_MONITORING=true

# Security labels
LABEL \
    maintainer="Algorand Showcase Team" \
    description="Production-ready Algorand Writer MCP Service" \
    version="0.1.1" \
    security.non-root="true" \
    security.readonly-rootfs="false"

# Use tini as init system for proper signal handling
ENTRYPOINT ["/sbin/tini", "--"]

# Start the service
CMD ["node", "apps/mcp-services/algorand-writer-mcp/server.js"]