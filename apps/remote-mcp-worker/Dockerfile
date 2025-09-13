# Multi-stage build for Remote MCP Worker
FROM node:20-alpine AS base

# Install system dependencies
RUN apk add --no-cache \
    libc6-compat \
    wget \
    curl

# Set working directory
WORKDIR /app

# Enable pnpm
RUN corepack enable pnpm

# Copy workspace and package files
COPY pnpm-workspace.yaml ./
COPY pnpm-lock.yaml ./
COPY package.json ./
COPY apps/remote-mcp-worker/package.json ./apps/remote-mcp-worker/
COPY packages/ ./packages/

# Install dependencies
RUN pnpm install --no-frozen-lockfile

# Copy source code and polyfill loader
COPY cloudflare-polyfill-loader.mjs ./cloudflare-polyfill-loader.mjs
COPY apps/remote-mcp-worker/ ./apps/remote-mcp-worker/

# Build packages and worker
RUN pnpm --filter "@algorand-showcase/*" run build
RUN pnpm --filter "@algorand-showcase/remote-mcp-worker" run build

# Production stage
FROM node:20-alpine AS runner

# Install runtime dependencies
RUN apk add --no-cache wget curl

# Create non-root user
RUN addgroup --system --gid 1001 worker && \
    adduser --system --uid 1001 worker

WORKDIR /app

# Copy built application and dependencies
COPY --from=base /app/node_modules ./node_modules
COPY --from=base /app/packages ./packages
COPY --from=base /app/apps/remote-mcp-worker ./apps/remote-mcp-worker
COPY --from=base /app/pnpm-workspace.yaml ./pnpm-workspace.yaml
COPY --from=base /app/package.json ./package.json
COPY --from=base /app/cloudflare-polyfill-loader.mjs ./cloudflare-polyfill-loader.mjs

# Set ownership
RUN chown -R worker:worker /app
USER worker

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1

# Expose port
EXPOSE 8080

# Environment defaults
ENV NODE_ENV=production
ENV PORT=8080
ENV ALGORAND_NETWORK=mainnet
ENV ALGORAND_ALGOD=https://mainnet-api.algonode.cloud
ENV ALGORAND_INDEXER=https://mainnet-idx.algonode.cloud
ENV ALGORAND_TOKEN=
ENV READ_ONLY=true

# Start the server
CMD ["node", "apps/remote-mcp-worker/server.js"]