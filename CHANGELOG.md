# Changelog

All notable changes to Algorand MCP Workers will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive open source community files and templates
- Enhanced documentation and contribution guidelines
- Security policy and vulnerability reporting procedures
- Code of conduct for community participation

### Changed
- Improved README with additional badges and community links
- Enhanced package.json metadata for better discoverability

### Security
- Added security best practices documentation
- Implemented secure configuration examples

## [1.2.0] - 2025-01-15

### Added
- **New Features**
  - Multi-signature transaction support in Actions MCP Worker
  - Real-time transaction monitoring via Server-Sent Events
  - Advanced search and filtering capabilities in Remote MCP Worker
  - Comprehensive asset metadata retrieval
  - Block explorer data access endpoints

### Changed
- **Performance Improvements**
  - Optimized Algorand client connection pooling
  - Enhanced caching strategies for blockchain data
  - Improved error handling and retry logic
  - Better rate limiting implementation

- **API Enhancements**
  - Extended transaction building parameters
  - Added support for application call transactions
  - Enhanced account information endpoints
  - Improved error response formatting

### Fixed
- **Bug Fixes**
  - Fixed transaction parameter validation edge cases
  - Resolved Docker container networking issues
  - Corrected Kubernetes resource limit configurations
  - Fixed intermittent connection timeout issues

### Security
- Enhanced input validation using Zod schemas
- Improved rate limiting configuration
- Updated security headers in HTTP responses
- Added request origin validation

## [1.1.2] - 2024-12-20

### Fixed
- Critical fix for transaction fee calculation
- Resolved memory leak in connection pooling
- Fixed Cloudflare Workers deployment configuration

### Security
- Updated dependencies to address security vulnerabilities
- Enhanced CORS configuration options
- Improved error message sanitization

## [1.1.1] - 2024-12-10

### Fixed
- Fixed Docker image build process for multi-platform support
- Resolved Kubernetes health check configuration
- Corrected environment variable handling in production

### Changed
- Updated base Docker images to latest stable versions
- Improved logging configuration and format consistency
- Enhanced monitoring and metrics collection

## [1.1.0] - 2024-12-01

### Added
- **Kubernetes Support**
  - Complete Helm charts for production deployment
  - Auto-scaling configuration with HorizontalPodAutoscaler
  - Network policies for enhanced security
  - Comprehensive monitoring and alerting setup

- **Enhanced Deployment Options**
  - One-command Docker setup with `make quick-start`
  - Production-ready Kubernetes configurations
  - Improved Cloudflare Workers deployment process
  - Environment-specific configuration management

### Changed
- **Architecture Improvements**
  - Refactored shared packages for better modularity
  - Enhanced error handling throughout the codebase
  - Improved configuration management system
  - Better separation of concerns between workers

- **Developer Experience**
  - Added comprehensive development documentation
  - Improved local development setup process
  - Enhanced testing framework and coverage
  - Better debugging tools and logging

### Deprecated
- Legacy configuration format (migration guide provided)
- Old Docker Compose format (v2.x compatibility maintained)

## [1.0.2] - 2024-11-15

### Fixed
- Resolved transaction simulation accuracy issues
- Fixed asset information retrieval for certain token types
- Corrected block data parsing edge cases

### Security
- Updated all dependencies to latest secure versions
- Enhanced API input validation
- Improved error handling to prevent information leakage

## [1.0.1] - 2024-11-08

### Fixed
- Fixed transaction building for payment transactions
- Resolved connection timeout issues with AlgoNode APIs
- Corrected OpenAPI documentation generation

### Changed
- Improved error messages for better debugging
- Enhanced logging output formatting
- Updated documentation examples

## [1.0.0] - 2024-11-01

### Added
- **Initial Release** 🎉
  - Actions MCP Worker for transaction operations
  - Remote MCP Worker for blockchain data access
  - Complete Model Context Protocol (MCP) implementation
  - Docker and Docker Compose support
  - Comprehensive API documentation
  - Production-ready configuration

- **Core Features**
  - Transaction building, simulation, and submission
  - Account information and balance retrieval
  - Transaction history and analytics
  - Asset information and metadata access
  - Block data and network statistics
  - Real-time health monitoring

- **Deployment Support**
  - Local development with Docker Compose
  - Cloudflare Workers deployment
  - Production-ready containerization
  - Comprehensive documentation

### Technical Details
- Built with TypeScript for type safety
- Uses Hono framework for high-performance HTTP handling
- Integrates with Algorand SDK for blockchain operations
- Implements MCP protocol for AI agent compatibility
- Supports both testnet and mainnet operations

---

## Release Types

Our releases follow these categories:

### 🚀 Major Releases (x.0.0)
- Breaking changes to APIs or architecture
- Major new features or capabilities
- Significant performance improvements
- New deployment options

### ✨ Minor Releases (x.y.0)
- New features and capabilities
- Enhanced existing functionality
- Performance improvements
- New configuration options
- Backward-compatible changes

### 🔧 Patch Releases (x.y.z)
- Bug fixes and stability improvements
- Security updates and patches
- Documentation updates
- Minor configuration improvements
- Dependency updates

## Development Releases

### Alpha Releases (x.y.z-alpha.n)
- Early development features
- Experimental functionality
- Breaking changes possible
- Not recommended for production

### Beta Releases (x.y.z-beta.n)
- Feature-complete pre-releases
- API stable, bug fixes ongoing
- Community testing encouraged
- Suitable for staging environments

### Release Candidates (x.y.z-rc.n)
- Final testing before stable release
- No new features, bug fixes only
- Production testing encouraged
- Stable API guaranteed

## Migration Guides

### Upgrading from 1.1.x to 1.2.x

**Configuration Changes:**
- Update environment variables (see example configurations)
- Review rate limiting settings
- Check CORS configuration

**API Changes:**
- New multi-signature endpoints available
- Enhanced error response format
- Additional transaction parameters supported

**Deployment Changes:**
- Updated Docker images
- New Kubernetes resource requirements
- Enhanced monitoring configuration

### Breaking Changes in 1.0.0

This is the first stable release, establishing the baseline API and architecture.

---

## Support Policy

### Long-Term Support (LTS)
- **1.2.x**: Current LTS, supported until Q2 2025
- **1.1.x**: Maintenance support until Q1 2025
- **1.0.x**: End of life, upgrade recommended

### Security Updates
- **Critical**: Patches released within 24-48 hours
- **High**: Patches released within 1 week
- **Medium/Low**: Included in next scheduled release

### Compatibility Promise
- **Patch versions**: No breaking changes, safe to upgrade
- **Minor versions**: Backward compatible, new features added
- **Major versions**: May include breaking changes, migration guide provided

---

## Getting Help

- 📖 **Documentation**: [Project README](README.md)
- 🤝 **Contributing**: [Contributing Guide](CONTRIBUTING.md)
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/ByteQuester/algorand-showcase/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/ByteQuester/algorand-showcase/discussions)
- 🔒 **Security**: [Security Policy](SECURITY.md)

---

**Legend:**
- 🎉 Major milestone
- ✨ New feature
- 🔧 Bug fix
- 🚀 Performance improvement
- 🔒 Security enhancement
- 📖 Documentation
- 🏗️ Infrastructure
- ⚠️ Breaking change
- 📦 Dependency update