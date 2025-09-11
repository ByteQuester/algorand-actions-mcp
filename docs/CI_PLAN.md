# CI/CD Plan

This document outlines the continuous integration and deployment strategy for the monorepo structure.

## CI/CD Strategy

### Build Matrix with pnpm Workspaces

The CI system will leverage pnpm workspaces for efficient dependency management and parallel builds.

**Workspace Configuration** (`pnpm-workspace.yaml`):
```yaml
packages:
  - 'packages/*'
  - 'apps/*'
```

**Root Package.json Scripts**:
```json
{
  "scripts": {
    "build": "pnpm -r build",
    "test": "pnpm -r test",
    "lint": "pnpm -r lint",
    "typecheck": "pnpm -r typecheck",
    "dev": "pnpm -r --parallel dev"
  }
}
```

## GitHub Actions Workflows

### 1. CI Workflow (`.github/workflows/ci.yml`)

**Triggers**: Push, Pull Request
**Strategy**: Matrix build for packages and apps

```yaml
name: CI
on: [push, pull_request]

jobs:
  changes:
    runs-on: ubuntu-latest
    outputs:
      packages: ${{ steps.changes.outputs.packages }}
      apps: ${{ steps.changes.outputs.apps }}
    steps:
      - uses: actions/checkout@v4
      - uses: dorny/paths-filter@v2
        id: changes
        with:
          filters: |
            packages:
              - 'packages/**'
            apps:
              - 'apps/**'

  lint-and-typecheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v2
      - uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'pnpm'
      - run: pnpm install --frozen-lockfile
      - run: pnpm lint
      - run: pnpm typecheck

  test-packages:
    needs: changes
    if: needs.changes.outputs.packages == 'true'
    runs-on: ubuntu-latest
    strategy:
      matrix:
        package: [mcp-core, algorand-clients, config, types]
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v2
      - uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'pnpm'
      - run: pnpm install --frozen-lockfile
      - run: pnpm --filter @algorand-showcase/${{ matrix.package }} test

  test-apps:
    needs: changes
    if: needs.changes.outputs.apps == 'true'
    runs-on: ubuntu-latest
    strategy:
      matrix:
        app: [actions-mcp-worker, remote-mcp-worker]
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v2
      - uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'pnpm'
      - run: pnpm install --frozen-lockfile
      - run: pnpm --filter @algorand-showcase/${{ matrix.app }} test
```

### 2. Deploy Workflow (`.github/workflows/deploy.yml`)

**Triggers**: Push to main, Release tags
**Strategy**: Deploy apps to Cloudflare Workers

```yaml
name: Deploy
on:
  push:
    branches: [main]
  release:
    types: [published]

jobs:
  deploy-workers:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        app: [actions-mcp-worker, remote-mcp-worker]
    environment:
      name: ${{ github.ref == 'refs/heads/main' && 'staging' || 'production' }}
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v2
      - uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'pnpm'
      - run: pnpm install --frozen-lockfile
      - run: pnpm --filter @algorand-showcase/${{ matrix.app }} build
      - uses: cloudflare/wrangler-action@v3
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
          workingDirectory: apps/${{ matrix.app }}
          environment: ${{ github.ref == 'refs/heads/main' && 'staging' || 'production' }}
```

### 3. Release Workflow (`.github/workflows/release.yml`)

**Triggers**: Manual dispatch, Version tags
**Purpose**: Automated changelog and release notes

```yaml
name: Release
on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-node@v4
        with:
          node-version: '18'
      - run: npx conventional-changelog-cli -p angular -i CHANGELOG.md -s
      - uses: softprops/action-gh-release@v1
        with:
          body_path: CHANGELOG.md
```

## Deployment Targets

### Cloudflare Workers
- **Staging**: `main` branch deployments
- **Production**: Release tag deployments
- **Environment Variables**: Managed through Cloudflare dashboard
- **Secrets**: Stored in GitHub repository secrets

### Future Docker Deployments
- **Registry**: GitHub Container Registry (ghcr.io)
- **Orchestration**: Kubernetes with Helm charts
- **Environments**: Development, Staging, Production

## Build Optimization

### Caching Strategy
1. **Node modules**: Cache pnpm store between builds
2. **Build artifacts**: Cache TypeScript compilation
3. **Docker layers**: Multi-stage builds with layer caching

### Parallel Execution
1. **Workspace builds**: pnpm runs packages in parallel
2. **Matrix jobs**: Multiple apps/packages build simultaneously
3. **Conditional execution**: Only affected workspaces are tested/built

### Environment Management
1. **Secrets**: GitHub repository secrets for sensitive data
2. **Variables**: GitHub repository variables for configuration
3. **Environments**: Separate staging/production with approval gates

## Quality Gates

### Required Checks
- [ ] Linting passes for all workspaces
- [ ] Type checking passes for all workspaces
- [ ] Unit tests pass for all workspaces
- [ ] Integration tests pass for apps
- [ ] Security scan passes (future)
- [ ] Performance benchmarks pass (future)

### Branch Protection
- Require pull request reviews
- Require status checks to pass
- Require branches to be up to date
- Restrict force pushes
- Require signed commits (future)

## Monitoring and Alerts

### Build Notifications
- Slack integration for failed builds
- Email notifications for deployment failures
- GitHub status checks for PR validation

### Deployment Monitoring
- Cloudflare Analytics for Worker performance
- Error tracking with Sentry (future)
- Performance monitoring with DataDog (future)

## Migration Strategy

1. **Phase 1**: Set up pnpm workspace configuration
2. **Phase 2**: Migrate existing GitHub Actions to matrix builds
3. **Phase 3**: Add workspace-aware testing and linting
4. **Phase 4**: Implement deployment pipelines for new app structure
5. **Phase 5**: Add quality gates and monitoring