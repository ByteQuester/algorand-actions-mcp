# 📚 Algorand Showcase Documentation Hub

> **Your complete guide to the AI-powered Algorand lending platform - Find anything in 30 seconds or less**

Welcome to the comprehensive documentation for Algorand Showcase! This hub provides organized access to all 915+ documentation files in this repository with clear learning paths from beginner to expert.

## 🚀 Quick Start Paths

### ⚡ 5-Minute Quick Start
**Goal:** Get the system running locally
1. [Main README](README.md) - Overview and quick setup
2. [Docker Setup](docs/DOCKER.md) - Local development with Docker
3. [Test Your Installation](README.md#🧪-test-your-installation)

### 🎯 30-Minute Deep Dive
**Goal:** Understand architecture and run examples
1. Start with [5-Minute Quick Start](#⚡-5-minute-quick-start)
2. [Architecture Overview](README.md#🏗️-architecture-overview)
3. [MCP Protocol Introduction](apps/mcp-services/README.md)
4. [Example API Usage](README.md#example-api-usage)
5. [Choose Your First Agent Example](#🤖-agent-examples-library)

### 🚀 2-Hour Production Setup
**Goal:** Deploy to production environment
1. Complete [30-Minute Deep Dive](#🎯-30-minute-deep-dive)
2. [Kubernetes Deployment](docs/K8S_SCOPE.md)
3. [Production Checklist](README.md#kubernetes-production-checklist)
4. [Monitoring & Security](README.md#📊-monitoring--observability)

## 📋 Documentation Categories

### 🏠 Getting Started
| Document | Description | Time | Audience |
|----------|-------------|------|----------|
| [Main README](README.md) | Complete project overview and quick start | 10 min | Everyone |
| [Docker Guide](docs/DOCKER.md) | Local development setup | 15 min | Developers |
| [Contributing Guide](CONTRIBUTING.md) | How to contribute to the project | 5 min | Contributors |

### 🏗️ Core Architecture
| Document | Description | Time | Audience |
|----------|-------------|------|----------|
| [MCP Services Overview](apps/README.md) | Model Context Protocol services | 10 min | Developers |
| [Actions MCP Worker](apps/mcp-services/algorand-actions-mcp/README.md) | Transaction operations service | 15 min | Blockchain devs |
| [Remote MCP Worker](apps/mcp-services/algorand-remote-mcp/README.md) | Blockchain data access service | 15 min | Blockchain devs |
| [Packages Overview](packages/README.md) | Shared libraries and utilities | 10 min | Developers |

### ☸️ Deployment & Operations
| Document | Description | Time | Audience |
|----------|-------------|------|----------|
| [Kubernetes Setup](docs/K8S_SCOPE.md) | Production Kubernetes deployment | 30 min | DevOps |
| [Environment Configuration](environments/README.md) | Multi-environment setup | 20 min | DevOps |
| [CI/CD Pipeline](docs/CI_PLAN.md) | Continuous integration setup | 15 min | DevOps |

### 🤖 Agent Examples Library

#### **Beginner Examples** (Start here!)
| Agent | Description | Use Case | Time |
|-------|-------------|----------|------|
| [Core Basic Config](apps/core/adk-python/contributing/samples/core_basic_config/README.md) | Simple agent setup | Learning basics | 10 min |
| [Hello World Ollama](apps/core/adk-python/contributing/samples/hello_world_ollama/README.md) | Local AI agent | Local development | 15 min |
| [A2A Basic](apps/core/adk-python/contributing/samples/a2a_basic/README.md) | Agent-to-agent communication | Multi-agent systems | 20 min |

#### **Blockchain Integration**
| Agent | Description | Use Case | Time |
|-------|-------------|----------|------|
| [Algorand MCP Examples](apps/core/adk-python/contributing/samples/mcp_stdio_notion_agent/README.md) | MCP protocol integration | Blockchain agents | 25 min |
| [Transaction Builder](apps/core/adk-python/contributing/samples/application_integration_agent/README.md) | Transaction operations | Financial applications | 30 min |

#### **Advanced Examples**
| Agent | Description | Use Case | Time |
|-------|-------------|----------|------|
| [Multi-Agent Systems](apps/core/adk-python/contributing/samples/multi_agent_basic_config/README.md) | Complex agent orchestration | Enterprise workflows | 45 min |
| [Financial Advisor](apps/core/adk-samples/python/agents/financial-advisor/README.md) | AI financial planning | FinTech applications | 60 min |
| [Data Science Agent](apps/core/adk-samples/python/agents/data-science/README.md) | Data analysis and ML | Analytics platforms | 45 min |

#### **Industry-Specific**
| Agent | Description | Use Case | Time |
|-------|-------------|----------|------|
| [Auto Insurance](apps/core/adk-samples/python/agents/auto-insurance-agent/README.md) | Insurance claim processing | Insurance industry | 40 min |
| [Customer Service](apps/core/adk-samples/python/agents/customer-service/README.md) | Automated customer support | Service industry | 35 min |
| [Academic Research](apps/core/adk-samples/python/agents/academic-research/README.md) | Research assistance | Education/Research | 50 min |

### 📖 API Reference
| Document | Description | Audience |
|----------|-------------|----------|
| [Actions API](apps/mcp-services/algorand-actions-mcp/README.md#api-endpoints) | Transaction operations API | Developers |
| [Remote API](apps/mcp-services/algorand-remote-mcp/README.md#api-endpoints) | Blockchain data API | Developers |
| [MCP Protocol Spec](https://modelcontextprotocol.io/) | Official MCP specification | Protocol developers |

### 🛡️ Security & Governance
| Document | Description | Audience |
|----------|-------------|----------|
| [Security Policy](SECURITY.md) | Security guidelines and reporting | Everyone |
| [Code of Conduct](CODE_OF_CONDUCT.md) | Community standards | Everyone |
| [Governance](GOVERNANCE.md) | Project governance model | Contributors |

## 🔍 Find What You Need

### By Role
- **🆕 New User**: Start with [Main README](README.md) → [Docker Guide](docs/DOCKER.md)
- **👨‍💻 Developer**: [Core Architecture](#🏗️-core-architecture) → [Agent Examples](#🤖-agent-examples-library)
- **🚀 DevOps Engineer**: [Deployment & Operations](#☸️-deployment--operations)
- **🤖 AI Researcher**: [Agent Examples Library](#🤖-agent-examples-library)
- **🏦 FinTech Builder**: [Financial Examples](apps/core/adk-samples/python/agents/financial-advisor/README.md)

### By Technology
- **🔗 Blockchain/Algorand**: [Actions MCP](apps/mcp-services/algorand-actions-mcp/README.md) + [Remote MCP](apps/mcp-services/algorand-remote-mcp/README.md)
- **🤖 AI/MCP Protocol**: [ADK Python Samples](apps/core/adk-python/contributing/samples/)
- **☸️ Kubernetes**: [K8S Setup](docs/K8S_SCOPE.md) + [Environments](environments/README.md)
- **🐳 Docker**: [Docker Guide](docs/DOCKER.md)
- **☁️ Cloudflare Workers**: [Main README Deployment](README.md#☁️-option-2-cloudflare-workers)

### By Use Case
- **💰 Lending Platform**: [Main README](README.md) → [Financial Advisor Agent](apps/core/adk-samples/python/agents/financial-advisor/README.md)
- **🏦 Banking Integration**: [Transaction Examples](#blockchain-integration)
- **📊 Data Analytics**: [Data Science Agent](apps/core/adk-samples/python/agents/data-science/README.md)
- **🎯 Multi-Agent Systems**: [Multi-Agent Examples](#advanced-examples)

## 🗺️ Learning Journeys

### Journey 1: From Zero to Local Development
```
📖 Main README (10 min)
    ↓
🐳 Docker Setup (15 min)
    ↓
🧪 Test Installation (5 min)
    ↓
🤖 Try Basic Agent Example (15 min)
    ↓
🎯 Build Your First Agent (30 min)
```

### Journey 2: Understanding the Architecture
```
🏗️ Architecture Overview (10 min)
    ↓
📡 MCP Protocol Basics (15 min)
    ↓
🔧 Actions MCP Worker (20 min)
    ↓
📊 Remote MCP Worker (20 min)
    ↓
🤖 End-to-End Example (30 min)
```

### Journey 3: Production Deployment
```
☸️ Kubernetes Overview (15 min)
    ↓
🔧 Environment Configuration (20 min)
    ↓
🚀 Deploy to Staging (30 min)
    ↓
📊 Setup Monitoring (25 min)
    ↓
🛡️ Security Configuration (20 min)
    ↓
🎯 Deploy to Production (30 min)
```

## 🆘 Need Help?

### Quick Help by Topic
- **🚨 Can't find something?** Use Ctrl+F to search this page, or check the [project structure](README.md#📁-project-structure)
- **🐛 Something broken?** See [Troubleshooting](README.md#🆘-troubleshooting) or [report an issue](https://github.com/ByteQuester/algorand-showcase/issues)
- **❓ Have questions?** Join our [discussions](https://github.com/ByteQuester/algorand-showcase/discussions)
- **🤝 Want to contribute?** Read the [Contributing Guide](CONTRIBUTING.md)

### Support Channels
- 📋 **Documentation Issues**: [File an issue](https://github.com/ByteQuester/algorand-showcase/issues/new) with the "documentation" label
- 💬 **General Questions**: [GitHub Discussions](https://github.com/ByteQuester/algorand-showcase/discussions)
- 🐛 **Bugs**: [Bug Report](https://github.com/ByteQuester/algorand-showcase/issues/new?template=bug_report.yml)
- ✨ **Feature Requests**: [Feature Request](https://github.com/ByteQuester/algorand-showcase/issues/new?template=feature_request.yml)

## 🔄 Next Steps Based on Your Goal

### I want to...
- **🏃‍♂️ Get started quickly** → [5-Minute Quick Start](#⚡-5-minute-quick-start)
- **🤖 Build an AI agent** → [Agent Examples Library](#🤖-agent-examples-library)
- **🏦 Integrate with blockchain** → [Blockchain Integration](#blockchain-integration)
- **🚀 Deploy to production** → [Production Setup](#🚀-2-hour-production-setup)
- **🤝 Contribute to the project** → [Contributing Guide](CONTRIBUTING.md)
- **📚 Understand the architecture** → [Core Architecture](#🏗️-core-architecture)

---

<div align="center">
  <p><strong>📚 Documentation maintained with ❤️ by the Algorand Showcase community</strong></p>
  <p>
    <a href="README.md">🏠 Back to Main README</a> •
    <a href="https://github.com/ByteQuester/algorand-showcase/issues">🐛 Report Documentation Issues</a> •
    <a href="CONTRIBUTING.md">🤝 Improve These Docs</a>
  </p>
</div>