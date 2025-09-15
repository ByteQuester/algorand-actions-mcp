# 🏢 Hosting-Monorepo Integration Guide

**Target**: Seamless integration of Algorand Showcase into hosting-monorepo
**Strategy**: Component-by-component migration with preserved functionality
**Complexity**: Medium - Well-organized structure enables smooth integration

## 📋 Integration Overview

The Algorand Showcase has been pre-organized with hosting-monorepo integration in mind. The clean structure, standardized configurations, and comprehensive documentation provide a solid foundation for seamless migration.

### Key Integration Advantages
- **Pre-organized structure** aligns with monorepo patterns
- **Environment-based configuration** ready for multi-environment deployment
- **Standardized Docker configs** compatible with container orchestration
- **Component isolation** enables independent deployment and scaling
- **Comprehensive documentation** reduces integration complexity

## 🗺️ Component Migration Strategy

### Migration Approach: Modular Integration
1. **Preserve Functionality**: No breaking changes during migration
2. **Incremental Migration**: Component-by-component approach
3. **Validation at Each Step**: Test functionality after each component migration
4. **Rollback Strategy**: Clear rollback procedures for each component
5. **Documentation Updates**: Update documentation during migration

## 📁 Component Mapping to Hosting-Monorepo

### 1. Lending Platform Application
**Source**: `/apps/lending-platform/`
**Target**: `/apps/algorand-showcase-lending/`

```
hosting-monorepo/
├── apps/
│   └── algorand-showcase-lending/
│       ├── src/                    # Production source code
│       │   ├── agents/            # ADK framework agents
│       │   ├── core/              # Platform core modules
│       │   └── ui/                # User interface components
│       ├── scripts/               # Development and deployment tools
│       ├── config/                # Environment configurations
│       ├── tests/                 # Test suites
│       ├── docs/                  # Documentation
│       ├── Dockerfile             # Container configuration
│       ├── docker-compose.yml     # Local development setup
│       └── package.json           # Node.js dependencies
```

#### Migration Steps
1. **Copy Source Code**: Transfer all `/src/` contents
2. **Adapt Build Configuration**: Update package.json and build scripts
3. **Environment Integration**: Merge configuration with hosting-monorepo env system
4. **Dependency Resolution**: Integrate with shared packages
5. **Testing Integration**: Adapt test suites for monorepo structure
6. **Documentation Update**: Update paths and references

### 2. MCP Services
**Source**: `/apps/mcp-services/`
**Target**: `/services/algorand-mcp/`

```
hosting-monorepo/
├── services/
│   └── algorand-mcp/
│       ├── reader/                # Algorand Reader MCP Service
│       │   ├── src/
│       │   ├── config/
│       │   ├── Dockerfile
│       │   └── wrangler.toml
│       ├── writer/                # Algorand Writer MCP Service
│       │   ├── src/
│       │   ├── config/
│       │   ├── Dockerfile
│       │   └── wrangler.toml
│       ├── shared/                # Shared MCP utilities
│       ├── docker-compose.yml     # Multi-service deployment
│       └── docs/                  # Service documentation
```

#### Migration Steps
1. **Service Separation**: Split reader and writer into separate services
2. **Configuration Standardization**: Align with hosting-monorepo config patterns
3. **Shared Code Extraction**: Move common code to shared utilities
4. **Container Orchestration**: Adapt for hosting-monorepo deployment patterns
5. **Service Discovery**: Integrate with hosting-monorepo service mesh
6. **Monitoring Integration**: Connect with hosting-monorepo observability stack

### 3. Shared Packages
**Source**: `/packages/`
**Target**: `/packages/algorand-*`

```
hosting-monorepo/
├── packages/
│   ├── algorand-clients/          # Blockchain client libraries
│   ├── algorand-config/           # Configuration utilities
│   ├── algorand-lending-api/      # Lending API definitions
│   ├── algorand-lending-core/     # Core lending logic
│   ├── algorand-mcp-core/         # MCP protocol implementations
│   └── algorand-types/            # TypeScript definitions
```

#### Migration Steps
1. **Namespace Addition**: Prefix packages with `algorand-` for clarity
2. **Dependency Analysis**: Map dependencies between packages
3. **Build Order Definition**: Define build sequence for dependency resolution
4. **Workspace Integration**: Integrate with hosting-monorepo workspace configuration
5. **Version Management**: Align with hosting-monorepo versioning strategy
6. **Distribution Strategy**: Configure package publishing and distribution

## ⚙️ Workspace Configuration Integration

### Package.json Workspace Configuration
```json
{
  "name": "hosting-monorepo",
  "workspaces": [
    "apps/*",
    "services/*",
    "packages/*",
    "apps/algorand-showcase-lending",
    "services/algorand-mcp/*",
    "packages/algorand-*"
  ],
  "scripts": {
    "build:algorand": "pnpm run --filter '@algorand/*' build",
    "test:algorand": "pnpm run --filter '@algorand/*' test",
    "dev:algorand-lending": "pnpm run --filter algorand-showcase-lending dev",
    "deploy:algorand-mcp": "pnpm run --filter '@algorand/mcp-*' deploy"
  }
}
```

### TypeScript Configuration Integration
```json
{
  "extends": "../../tsconfig.base.json",
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@algorand/clients": ["../../packages/algorand-clients/src"],
      "@algorand/config": ["../../packages/algorand-config/src"],
      "@algorand/lending-api": ["../../packages/algorand-lending-api/src"],
      "@algorand/lending-core": ["../../packages/algorand-lending-core/src"],
      "@algorand/mcp-core": ["../../packages/algorand-mcp-core/src"],
      "@algorand/types": ["../../packages/algorand-types/src"]
    }
  },
  "references": [
    {"path": "../../packages/algorand-clients"},
    {"path": "../../packages/algorand-config"},
    {"path": "../../packages/algorand-lending-api"},
    {"path": "../../packages/algorand-lending-core"},
    {"path": "../../packages/algorand-mcp-core"},
    {"path": "../../packages/algorand-types"}
  ]
}
```

## 🔗 Dependency Management Strategy

### Build Dependency Graph
```mermaid
graph TD
    A[algorand-types] --> B[algorand-clients]
    A --> C[algorand-config]
    A --> D[algorand-mcp-core]

    B --> E[algorand-lending-core]
    C --> E
    D --> E

    E --> F[algorand-lending-api]

    F --> G[algorand-showcase-lending]
    D --> H[algorand-mcp-reader]
    D --> I[algorand-mcp-writer]

    B --> H
    B --> I
```

### Build Order Sequence
1. **Foundation Layer**: `algorand-types`
2. **Infrastructure Layer**: `algorand-clients`, `algorand-config`, `algorand-mcp-core`
3. **Business Logic Layer**: `algorand-lending-core`
4. **API Layer**: `algorand-lending-api`
5. **Application Layer**: `algorand-showcase-lending`
6. **Service Layer**: `algorand-mcp-reader`, `algorand-mcp-writer`

### Shared Package Dependencies
```json
{
  "dependencies": {
    "@algorand/types": "workspace:*",
    "@algorand/clients": "workspace:*",
    "@algorand/config": "workspace:*",
    "@algorand/lending-core": "workspace:*",
    "@algorand/mcp-core": "workspace:*"
  },
  "devDependencies": {
    "typescript": "^5.0.0",
    "@types/node": "^20.0.0"
  }
}
```

## 🌍 Environment Configuration Integration

### Hosting-Monorepo Environment Strategy
```bash
# Root environment variables
ALGORAND_NETWORK=testnet
ALGORAND_NODE_URL=https://testnet-api.algonode.cloud
ALGORAND_INDEXER_URL=https://testnet-idx.algonode.cloud

# Service-specific variables
ALGORAND_READER_PORT=8002
ALGORAND_WRITER_PORT=8003
LENDING_PLATFORM_PORT=8004

# Shared database configuration
DATABASE_URL=postgresql://user:pass@localhost:5432/algorand_showcase
REDIS_URL=redis://localhost:6379

# AI service configuration
GOOGLE_API_KEY=${GOOGLE_API_KEY}
GOOGLE_GENAI_USE_VERTEXAI=true

# Security configuration
JWT_SECRET=${JWT_SECRET}
CORS_ORIGIN=https://hosting-platform.com
```

### Environment File Organization
```
hosting-monorepo/
├── .env.example                   # Template for all environments
├── .env.development               # Development environment
├── .env.staging                   # Staging environment
├── .env.production               # Production environment
├── apps/algorand-showcase-lending/
│   ├── .env.local.example        # Local development overrides
│   └── config/
│       ├── development.json      # Development-specific config
│       ├── staging.json          # Staging-specific config
│       └── production.json       # Production-specific config
└── services/algorand-mcp/
    ├── reader/.env.example       # Reader service configuration
    ├── writer/.env.example       # Writer service configuration
    └── shared/config/            # Shared MCP configuration
```

## 🔧 Build System Integration

### Root Build Configuration
```json
{
  "scripts": {
    "build": "turbo run build",
    "build:algorand": "turbo run build --filter=@algorand/*",
    "dev": "turbo run dev --parallel",
    "dev:algorand": "turbo run dev --filter=@algorand/* --parallel",
    "test": "turbo run test",
    "test:algorand": "turbo run test --filter=@algorand/*",
    "lint": "turbo run lint",
    "lint:algorand": "turbo run lint --filter=@algorand/*"
  }
}
```

### Turbo Configuration
```json
{
  "$schema": "https://turbo.build/schema.json",
  "pipeline": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": ["dist/**", "build/**"]
    },
    "test": {
      "dependsOn": ["build"],
      "outputs": ["coverage/**"]
    },
    "lint": {
      "outputs": []
    },
    "dev": {
      "cache": false,
      "persistent": true
    }
  }
}
```

### Dockerfile Integration
```dockerfile
# Multi-stage build for production
FROM node:18-alpine AS base
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN npm install -g pnpm

FROM base AS deps
RUN pnpm install --frozen-lockfile

FROM base AS builder
COPY . .
COPY --from=deps /app/node_modules ./node_modules
RUN pnpm build --filter=algorand-showcase-lending

FROM node:18-alpine AS runner
WORKDIR /app
COPY --from=builder /app/apps/algorand-showcase-lending/dist ./
COPY --from=builder /app/apps/algorand-showcase-lending/package.json ./
EXPOSE 8004
CMD ["node", "index.js"]
```

## 🚀 CI/CD Pipeline Integration

### GitHub Actions Workflow
```yaml
name: Algorand Showcase CI/CD

on:
  push:
    paths:
      - 'apps/algorand-showcase-lending/**'
      - 'services/algorand-mcp/**'
      - 'packages/algorand-*/**'
  pull_request:
    paths:
      - 'apps/algorand-showcase-lending/**'
      - 'services/algorand-mcp/**'
      - 'packages/algorand-*/**'

jobs:
  test-algorand:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: pnpm/action-setup@v2
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'pnpm'

      - run: pnpm install --frozen-lockfile
      - run: pnpm run build --filter=@algorand/*
      - run: pnpm run test --filter=@algorand/*
      - run: pnpm run lint --filter=@algorand/*

  deploy-staging:
    needs: test-algorand
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: |
          docker build -t algorand-showcase:staging .
          docker push registry.hosting-platform.com/algorand-showcase:staging

      - run: |
          kubectl apply -f k8s/staging/
          kubectl rollout status deployment/algorand-showcase -n staging

  deploy-production:
    needs: test-algorand
    if: github.ref == 'refs/heads/production'
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v3
      - run: |
          docker build -t algorand-showcase:latest .
          docker push registry.hosting-platform.com/algorand-showcase:latest

      - run: |
          kubectl apply -f k8s/production/
          kubectl rollout status deployment/algorand-showcase -n production
```

## 🎯 Service Discovery & Communication

### Internal Service Communication
```yaml
# Kubernetes Service Discovery
apiVersion: v1
kind: Service
metadata:
  name: algorand-mcp-reader
  namespace: algorand-services
spec:
  selector:
    app: algorand-mcp-reader
  ports:
  - port: 8002
    targetPort: 8002

---
apiVersion: v1
kind: Service
metadata:
  name: algorand-mcp-writer
  namespace: algorand-services
spec:
  selector:
    app: algorand-mcp-writer
  ports:
  - port: 8003
    targetPort: 8003

---
apiVersion: v1
kind: Service
metadata:
  name: algorand-showcase-lending
  namespace: algorand-services
spec:
  selector:
    app: algorand-showcase-lending
  ports:
  - port: 8004
    targetPort: 8004
```

### Service Configuration
```typescript
// Service discovery configuration
export const serviceConfig = {
  mcp: {
    reader: {
      endpoint: process.env.ALGORAND_READER_ENDPOINT || 'http://algorand-mcp-reader:8002',
      timeout: 5000,
      retries: 3
    },
    writer: {
      endpoint: process.env.ALGORAND_WRITER_ENDPOINT || 'http://algorand-mcp-writer:8003',
      timeout: 10000,
      retries: 3
    }
  },
  lending: {
    endpoint: process.env.LENDING_PLATFORM_ENDPOINT || 'http://algorand-showcase-lending:8004',
    timeout: 5000,
    retries: 3
  }
};
```

## 📊 Monitoring & Observability Integration

### Prometheus Metrics Integration
```typescript
// Metrics configuration
import { Registry, Counter, Histogram, Gauge } from 'prom-client';

export const register = new Registry();

export const httpRequestsTotal = new Counter({
  name: 'algorand_http_requests_total',
  help: 'Total number of HTTP requests',
  labelNames: ['method', 'route', 'status_code'],
  registers: [register]
});

export const httpRequestDuration = new Histogram({
  name: 'algorand_http_request_duration_seconds',
  help: 'Duration of HTTP requests in seconds',
  labelNames: ['method', 'route'],
  registers: [register]
});

export const algorandTransactionsTotal = new Counter({
  name: 'algorand_transactions_total',
  help: 'Total number of Algorand transactions processed',
  labelNames: ['type', 'status'],
  registers: [register]
});
```

### Logging Integration
```typescript
// Structured logging configuration
import winston from 'winston';

export const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  defaultMeta: {
    service: 'algorand-showcase',
    environment: process.env.NODE_ENV || 'development'
  },
  transports: [
    new winston.transports.File({
      filename: 'logs/error.log',
      level: 'error'
    }),
    new winston.transports.File({
      filename: 'logs/combined.log'
    })
  ]
});

if (process.env.NODE_ENV !== 'production') {
  logger.add(new winston.transports.Console({
    format: winston.format.simple()
  }));
}
```

## 🔒 Security Integration

### Secret Management
```typescript
// Secret management integration
interface SecretConfig {
  googleApiKey: string;
  jwtSecret: string;
  databaseUrl: string;
  algorandPrivateKey: string;
}

export async function loadSecrets(): Promise<SecretConfig> {
  if (process.env.NODE_ENV === 'production') {
    // Use hosting-monorepo secret management
    return {
      googleApiKey: await getSecret('GOOGLE_API_KEY'),
      jwtSecret: await getSecret('JWT_SECRET'),
      databaseUrl: await getSecret('DATABASE_URL'),
      algorandPrivateKey: await getSecret('ALGORAND_PRIVATE_KEY')
    };
  } else {
    // Use environment variables for development
    return {
      googleApiKey: process.env.GOOGLE_API_KEY!,
      jwtSecret: process.env.JWT_SECRET!,
      databaseUrl: process.env.DATABASE_URL!,
      algorandPrivateKey: process.env.ALGORAND_PRIVATE_KEY!
    };
  }
}
```

### RBAC Integration
```yaml
# Role-Based Access Control
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: algorand-services
  name: algorand-service-reader
rules:
- apiGroups: [""]
  resources: ["configmaps", "secrets"]
  verbs: ["get", "list"]
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["get", "list"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: algorand-service-binding
  namespace: algorand-services
subjects:
- kind: ServiceAccount
  name: algorand-service-account
  namespace: algorand-services
roleRef:
  kind: Role
  name: algorand-service-reader
  apiGroup: rbac.authorization.k8s.io
```

## 📝 Migration Checklist

### Pre-Migration Validation
- [ ] **Source Code Review**: Validate all source code is ready for migration
- [ ] **Dependency Analysis**: Map all package dependencies
- [ ] **Configuration Audit**: Review environment configuration requirements
- [ ] **Security Scan**: Perform security scanning on all components
- [ ] **Performance Baseline**: Establish performance benchmarks

### Migration Execution
- [ ] **Package Migration**: Migrate shared packages first
- [ ] **Service Migration**: Migrate MCP services
- [ ] **Application Migration**: Migrate lending platform application
- [ ] **Configuration Integration**: Integrate environment configurations
- [ ] **Build System Integration**: Update build scripts and workflows

### Post-Migration Validation
- [ ] **Functionality Testing**: Verify all features work correctly
- [ ] **Integration Testing**: Test component interactions
- [ ] **Performance Testing**: Validate performance benchmarks
- [ ] **Security Testing**: Perform security validation
- [ ] **Documentation Update**: Update all documentation with new paths

### Deployment Validation
- [ ] **Development Environment**: Deploy and test in development
- [ ] **Staging Environment**: Deploy and test in staging
- [ ] **Load Testing**: Perform load testing
- [ ] **Monitoring Validation**: Verify monitoring and alerting
- [ ] **Production Deployment**: Deploy to production environment

## 🎯 Success Criteria

### Technical Success Metrics
- ✅ **Zero Downtime Migration**: No service interruption during migration
- ✅ **Performance Maintenance**: No performance degradation post-migration
- ✅ **Functionality Preservation**: All features work as before
- ✅ **Security Compliance**: All security requirements met
- ✅ **Monitoring Integration**: Full observability maintained

### Operational Success Metrics
- ✅ **Team Readiness**: Operations team trained on new deployment
- ✅ **Documentation Quality**: Complete operational documentation
- ✅ **Incident Response**: Incident response procedures updated
- ✅ **Backup Strategy**: Backup and recovery procedures implemented
- ✅ **Rollback Capability**: Rollback procedures tested and verified

## 📋 Risk Mitigation

### Identified Risks and Mitigations

#### High Risk: Service Communication Changes
- **Risk**: Service endpoints change during migration
- **Mitigation**: Use service discovery with environment variable fallbacks
- **Contingency**: Maintain old endpoints during transition period

#### Medium Risk: Configuration Conflicts
- **Risk**: Environment variable conflicts with hosting-monorepo
- **Mitigation**: Namespace all Algorand-specific variables with `ALGORAND_` prefix
- **Contingency**: Use configuration inheritance to resolve conflicts

#### Low Risk: Build Process Changes
- **Risk**: Build scripts don't work in hosting-monorepo environment
- **Mitigation**: Test build process in isolation before migration
- **Contingency**: Maintain separate build scripts during transition

## 🎉 Integration Summary

The Algorand Showcase is perfectly positioned for hosting-monorepo integration due to its:

### Pre-Migration Advantages
- **Clean, organized structure** that aligns with monorepo patterns
- **Environment-based configuration** ready for multi-environment deployment
- **Component isolation** enabling independent deployment and scaling
- **Comprehensive documentation** reducing integration complexity
- **Standardized build processes** compatible with monorepo tooling

### Expected Integration Benefits
- **Reduced operational complexity** through shared infrastructure
- **Improved development velocity** through shared tooling and processes
- **Enhanced monitoring and observability** through centralized platforms
- **Better resource utilization** through container orchestration
- **Simplified deployment processes** through standardized CI/CD

### Integration Timeline
- **Week 1**: Package migration and workspace configuration
- **Week 2**: Service migration and integration testing
- **Week 3**: Application migration and end-to-end testing
- **Week 4**: Production deployment and monitoring validation

**The Algorand Showcase is READY FOR SEAMLESS HOSTING-MONOREPO INTEGRATION.**

---

**Integration Strategy by**: Claude Code
**Date**: September 15, 2025
**Version**: 1.0