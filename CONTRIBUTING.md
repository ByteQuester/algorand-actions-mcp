# Contributing to Algorand MCP Workers

🎉 **Thank you for your interest in contributing to Algorand MCP Workers!**

We're excited to have you join our community of developers building the future of AI-blockchain integration. This guide will help you get started with contributing to this production-ready project.

## 🌟 Ways to Contribute

### 🐛 Bug Reports
Found a bug? Help us fix it by providing detailed information:
- **Search existing issues** to avoid duplicates
- **Use the bug report template** when creating new issues
- **Include reproduction steps** and environment details
- **Add relevant logs** and error messages

### 💡 Feature Requests
Have an idea for improvement?
- **Check our roadmap** and existing feature requests
- **Use the feature request template** with clear use cases
- **Discuss complex features** in GitHub Discussions first
- **Consider implementation complexity** and maintainability

### 📖 Documentation
Help improve our docs:
- **Fix typos** and unclear instructions
- **Add missing examples** and use cases
- **Improve API documentation**
- **Create tutorials** and guides

### 💻 Code Contributions
Ready to dive into the codebase?
- **Start with good first issues** labeled `good-first-issue`
- **Follow our coding standards** and architecture patterns
- **Add comprehensive tests** for new features
- **Update documentation** for your changes

## 🚀 Getting Started

### Prerequisites

Ensure you have the following installed:
- **Node.js 18+** with pnpm package manager
- **Docker & Docker Compose** for local development
- **Git** for version control
- **kubectl & Helm** (optional, for Kubernetes development)

### Fork & Clone

1. **Fork** the repository on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/algorand-showcase.git
   cd algorand-showcase
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/ByteQuester/algorand-showcase.git
   ```

### Development Setup

1. **Install dependencies**:
   ```bash
   pnpm install
   ```

2. **Build all packages**:
   ```bash
   pnpm build
   ```

3. **Start development environment**:
   ```bash
   # Option 1: Docker Compose (recommended)
   docker-compose up -d

   # Option 2: Local development
   make dev
   ```

4. **Verify setup**:
   ```bash
   # Test Actions MCP Worker
   curl http://localhost:8788/health

   # Test Remote MCP Worker
   curl http://localhost:8789/health
   ```

### Development Commands

| Command | Purpose |
|---------|---------|
| `pnpm build` | Build all packages and applications |
| `pnpm test` | Run all tests with coverage |
| `pnpm test:watch` | Run tests in watch mode |
| `pnpm lint` | Lint all code with auto-fix |
| `pnpm typecheck` | TypeScript type checking |
| `pnpm dev` | Start development servers |
| `make docker-build` | Build Docker containers |
| `make docker-test` | Test Docker containers |

## 📋 Development Workflow

### 1. Create Feature Branch

```bash
# Sync with upstream
git fetch upstream
git checkout main
git merge upstream/main

# Create feature branch
git checkout -b feature/amazing-feature
```

### 2. Make Changes

- **Follow code style**: ESLint and Prettier are configured
- **Write tests**: Maintain or improve test coverage
- **Update docs**: Keep documentation in sync with changes
- **Commit often**: Use descriptive commit messages

### 3. Test Your Changes

```bash
# Run all tests
pnpm test

# Test specific package
pnpm --filter "@algorand-showcase/mcp-core" test

# Integration tests
make test-integration

# Docker container tests
make docker-test
```

### 4. Submit Pull Request

1. **Push your branch**:
   ```bash
   git push origin feature/amazing-feature
   ```

2. **Create Pull Request** on GitHub:
   - Use the PR template
   - Link related issues
   - Add clear description
   - Request appropriate reviewers

3. **Respond to feedback**:
   - Address review comments
   - Update documentation if needed
   - Ensure CI passes

## 🏗️ Project Architecture

Understanding the codebase structure helps you contribute effectively:

### Core Components

```
├── apps/                          # MCP Worker Applications
│   ├── actions-mcp-worker/       # Transaction operations
│   └── remote-mcp-worker/        # Blockchain data access
├── packages/                     # Shared libraries
│   ├── mcp-core/                # MCP utilities & base classes
│   ├── algorand-clients/        # Algorand SDK wrappers
│   ├── config/                  # Configuration management
│   └── types/                   # TypeScript definitions
├── environments/                # Kubernetes deployment
└── docs/                       # Documentation
```

### Key Patterns

1. **MCP Tools**: Extend `MCPTool` base class in `packages/mcp-core`
2. **HTTP Adapters**: Convert MCP tools to REST APIs
3. **Client Wrappers**: Add retry logic and error handling to Algorand clients
4. **Configuration**: Environment-based config with validation

### Adding New MCP Tools

1. **Create tool class**:
   ```typescript
   export class MyNewTool extends MCPTool {
     constructor() {
       super({
         name: 'my_new_tool',
         description: 'Description of what this tool does',
         schema: z.object({
           param1: z.string(),
           param2: z.number()
         })
       });
     }

     async execute(params: MyToolParams): Promise<MyToolResult> {
       // Implementation here
     }
   }
   ```

2. **Register in worker**:
   ```typescript
   // In worker's init() method
   this.registerTool(new MyNewTool());
   ```

3. **Add HTTP endpoint**:
   ```typescript
   // In http-adapter.ts
   app.post('/tools/my_new_tool', async (c) => {
     // HTTP wrapper logic
   });
   ```

4. **Write tests**:
   ```typescript
   describe('MyNewTool', () => {
     it('should handle valid input', async () => {
       // Test implementation
     });
   });
   ```

## ✅ Code Standards

### TypeScript Guidelines

- **Strict mode**: All code uses strict TypeScript settings
- **Type safety**: Avoid `any` types, use proper interfaces
- **Error handling**: Use Result types for error-prone operations
- **Documentation**: Add JSDoc comments for public APIs

### Code Style

We use automated formatting with Prettier and linting with ESLint:

```bash
# Auto-fix code style issues
pnpm lint --fix

# Check formatting
pnpm format:check

# Auto-format code
pnpm format:write
```

### Testing Requirements

- **Unit tests**: Test individual functions and classes
- **Integration tests**: Test API endpoints and workflows
- **Coverage**: Maintain >80% code coverage
- **Mocking**: Mock external dependencies (Algorand APIs)

Example test:
```typescript
describe('PaymentTool', () => {
  it('should build valid payment transaction', async () => {
    const tool = new PaymentTool();
    const result = await tool.execute({
      sender: 'VALID_ADDRESS',
      receiver: 'VALID_ADDRESS',
      amount: 1000000
    });

    expect(result.success).toBe(true);
    expect(result.data).toHaveProperty('txn');
  });
});
```

### Documentation Standards

- **API docs**: Auto-generated from JSDoc comments
- **README updates**: Update relevant README files
- **Examples**: Include practical usage examples
- **Changelog**: Add entries for user-facing changes

## 🔍 Testing Guidelines

### Running Tests

```bash
# All tests
pnpm test

# Specific package
pnpm --filter "@algorand-showcase/mcp-core" test

# Watch mode
pnpm test:watch

# Coverage report
pnpm test:coverage
```

### Test Categories

1. **Unit Tests** (`*.test.ts`):
   - Test individual functions and classes
   - Mock external dependencies
   - Fast execution (< 1ms per test)

2. **Integration Tests** (`*.integration.test.ts`):
   - Test API endpoints
   - Test database interactions
   - Use test containers

3. **E2E Tests** (`*.e2e.test.ts`):
   - Test complete workflows
   - Use real Docker containers
   - Test deployment scenarios

### Mock Guidelines

```typescript
// Mock Algorand clients
jest.mock('@algorand-showcase/algorand-clients', () => ({
  AlgodClientWrapper: jest.fn().mockImplementation(() => ({
    buildPaymentTransaction: jest.fn().mockResolvedValue({
      success: true,
      data: 'base64-encoded-txn'
    })
  }))
}));
```

## 🚀 Deployment Testing

### Local Testing

Test your changes in a realistic environment:

```bash
# Build and test Docker containers
make docker-build
make docker-test

# Full integration test
make test-integration

# Load testing (optional)
make load-test
```

### Kubernetes Testing

For infrastructure changes:

```bash
# Validate Helm charts
cd environments && ./validate.sh

# Dry-run deployment
./deploy.sh -e development --dry-run

# Deploy to local cluster
./deploy.sh -e development -w all
```

## 📦 Release Process

### Version Management

We use semantic versioning (SemVer):
- **Patch** (x.x.1): Bug fixes, minor improvements
- **Minor** (x.1.x): New features, backward compatible
- **Major** (1.x.x): Breaking changes

### Release Checklist

1. **Update version numbers** in package.json files
2. **Update CHANGELOG.md** with new features/fixes
3. **Run full test suite** and ensure all pass
4. **Build and test containers**
5. **Update documentation** if needed
6. **Create release PR** with version bump
7. **Tag release** after PR merge

## 🤝 Community Guidelines

### Code of Conduct

We follow the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). Please read it and help us maintain a welcoming community.

### Communication

- **GitHub Discussions**: For questions and general discussion
- **GitHub Issues**: For bugs and feature requests
- **Pull Requests**: For code review and collaboration
- **Discord** (coming soon): For real-time chat

### Recognition

Contributors are recognized in several ways:
- **GitHub contributors graph**: Automatic recognition
- **Release notes**: Major contributors mentioned
- **Documentation**: Contributor acknowledgments
- **Special badges**: For significant contributions

## 🆘 Getting Help

### Documentation Resources

- **README.md**: Project overview and quick start
- **API Documentation**: Auto-generated OpenAPI docs
- **Architecture docs**: In `docs/` directory
- **Deployment guides**: Docker and Kubernetes setup

### Asking for Help

1. **Search existing issues** and discussions first
2. **Use appropriate channels**:
   - Bug reports: GitHub Issues
   - Questions: GitHub Discussions
   - Feature ideas: GitHub Discussions
   - Code review: Pull Request comments

3. **Provide context**:
   - Your environment (OS, Node.js version, etc.)
   - Steps to reproduce issues
   - Relevant logs and error messages
   - What you've already tried

### Common Issues

#### Development Setup
```bash
# Node version issues
nvm use 18

# pnpm installation
npm install -g pnpm

# Docker permission issues (Linux)
sudo usermod -aG docker $USER
newgrp docker
```

#### Build Issues
```bash
# Clear node_modules
rm -rf node_modules
pnpm install

# Clear build cache
pnpm clean
pnpm build
```

#### Test Issues
```bash
# Update test snapshots
pnpm test -u

# Debug specific test
pnpm test --grep "test name"
```

## 🏆 Maintainer Guidelines

### For Core Maintainers

If you're a core maintainer, please also follow:

1. **Review PRs promptly** (within 2-3 business days)
2. **Provide constructive feedback** and suggestions
3. **Test changes locally** before approving
4. **Maintain backward compatibility** when possible
5. **Update documentation** for significant changes
6. **Follow security best practices** for sensitive changes

### Release Responsibilities

Core maintainers handle releases:

1. **Version coordination**: Ensure proper version bumps
2. **Changelog maintenance**: Keep CHANGELOG.md updated
3. **Security reviews**: Extra scrutiny for security-related changes
4. **Breaking changes**: Clear communication and migration guides
5. **Hotfix releases**: Quick response to critical issues

## 📝 License

By contributing to Algorand MCP Workers, you agree that your contributions will be licensed under the MIT License.

---

## 🎉 Thank You!

Your contributions help make Algorand MCP Workers better for everyone. Whether you're fixing a typo, adding a feature, or helping with documentation, every contribution matters.

Ready to contribute? Check out our [good first issues](https://github.com/ByteQuester/algorand-showcase/labels/good-first-issue) to get started!

---

<div align="center">
  <p>
    <a href="https://github.com/ByteQuester/algorand-showcase">🏠 Back to README</a> •
    <a href="https://github.com/ByteQuester/algorand-showcase/issues/new/choose">🐛 Report Bug</a> •
    <a href="https://github.com/ByteQuester/algorand-showcase/discussions">💬 Start Discussion</a>
  </p>
  <p>Made with ❤️ by the Algorand MCP community</p>
</div>