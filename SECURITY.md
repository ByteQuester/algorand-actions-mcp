# Security Policy

## 🔒 Security Commitment

The Algorand MCP Workers project takes security seriously. We are committed to ensuring the security and integrity of our software and the safety of our users' blockchain operations.

## 🚨 Supported Versions

We provide security updates for the following versions:

| Version | Supported          | End of Support |
| ------- | ------------------ | -------------- |
| 1.2.x   | ✅ Active support  | TBD            |
| 1.1.x   | ✅ Security fixes  | June 2025      |
| 1.0.x   | ❌ End of life     | March 2025     |
| < 1.0   | ❌ End of life     | January 2025   |

### Support Policy

* **Active Support**: Full security and bug fixes, new features
* **Security Fixes**: Critical security patches only
* **End of Life**: No updates, upgrade strongly recommended

## 🛡️ Security Features

### Built-in Security Measures

* **Input Validation**: All API inputs are validated using Zod schemas
* **Rate Limiting**: Configurable rate limiting on all endpoints
* **CORS Protection**: Configurable CORS policies
* **Authentication**: OAuth 2.0 support for protected operations
* **Network Policies**: Kubernetes network segmentation
* **Container Security**: Non-root containers, read-only filesystems
* **Secrets Management**: Environment variable based configuration
* **TLS/SSL**: Encrypted communication in production deployments

### Algorand-Specific Security

* **Transaction Validation**: Comprehensive transaction parameter validation
* **Network Isolation**: Separate configurations for testnet/mainnet
* **Private Key Handling**: No private key storage or transmission
* **Multi-signature Support**: Secure multi-signature transaction workflows
* **Read-only Operations**: Data access tools are read-only by design

## 🚨 Reporting Security Vulnerabilities

### How to Report

If you discover a security vulnerability, please report it responsibly:

#### 🎯 Preferred Method: Private Disclosure

**Email**: [security@algorand-mcp.com](mailto:security@algorand-mcp.com)

**Subject**: `[SECURITY] Brief description of vulnerability`

#### 🔐 Encrypted Communication

For sensitive reports, use our PGP key:

```
-----BEGIN PGP PUBLIC KEY BLOCK-----
[PGP KEY WOULD GO HERE]
-----END PGP PUBLIC KEY BLOCK-----
```

**Fingerprint**: `1234 5678 9ABC DEF0 1234 5678 9ABC DEF0 1234 5678`

#### 📋 What to Include

Please provide the following information:

* **Vulnerability Description**: Clear description of the security issue
* **Impact Assessment**: Potential impact and severity
* **Affected Components**: Which parts of the system are affected
* **Reproduction Steps**: Detailed steps to reproduce the vulnerability
* **Proof of Concept**: Code or commands demonstrating the issue (if safe)
* **Suggested Fix**: Any recommendations for remediation (optional)
* **Discovery Context**: How you discovered the vulnerability
* **Contact Information**: How we can reach you for follow-up

### 📧 Report Template

```
Subject: [SECURITY] Brief vulnerability description

Vulnerability Details:
- Component: [Actions MCP Worker / Remote MCP Worker / etc.]
- Severity: [Critical / High / Medium / Low]
- Type: [e.g., Input validation, Authentication bypass, etc.]

Description:
[Detailed description of the vulnerability]

Impact:
[What could an attacker achieve?]

Reproduction Steps:
1. [Step 1]
2. [Step 2]
3. [Result]

Environment:
- Version: [e.g., v1.2.0]
- Deployment: [Docker/Kubernetes/Cloudflare Workers]
- OS: [if relevant]

Additional Information:
[Any other relevant details]

Suggested Mitigation:
[If you have suggestions]

Contact:
- Name: [Your name or handle]
- Email: [Your email]
- Preferred contact method: [Email/GitHub/etc.]
```

## ⏱️ Response Timeline

We are committed to responding to security reports promptly:

| Timeline | Action |
|----------|--------|
| **24 hours** | Initial acknowledgment of your report |
| **72 hours** | Preliminary assessment and severity classification |
| **1 week** | Detailed investigation and impact analysis |
| **2 weeks** | Fix development and testing (for most issues) |
| **4 weeks** | Public disclosure (coordinated with reporter) |

### Severity Classification

* **Critical**: Immediate threat, affects production systems
* **High**: Significant security risk, affects multiple users
* **Medium**: Moderate risk, limited impact or requires specific conditions
* **Low**: Minor security improvement, best practice enhancement

## 🔐 Security Best Practices

### For Users

#### Deployment Security

* **Environment Variables**: Never commit secrets to version control
* **Network Security**: Use proper firewall rules and network policies
* **Access Control**: Implement proper authentication and authorization
* **Regular Updates**: Keep dependencies and base images updated
* **Monitoring**: Enable security monitoring and alerting

#### Configuration Security

```bash
# Example secure environment configuration
ALGOD_TOKEN=""  # Use empty string for AlgoNode public API
ALGOD_ADDR="https://testnet-api.algonode.cloud"  # Use HTTPS
ENABLE_CORS="false"  # Disable CORS in production
RATE_LIMIT_REQUESTS="100"  # Appropriate rate limiting
LOG_LEVEL="warn"  # Avoid debug logs in production
```

#### Docker Security

```dockerfile
# Security best practices in Dockerfile
USER node  # Run as non-root user
COPY --chown=node:node . /app  # Proper file ownership
RUN chmod -R 755 /app  # Appropriate file permissions
```

#### Kubernetes Security

```yaml
# Security contexts in Kubernetes
securityContext:
  runAsNonRoot: true
  runAsUser: 1001
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
  capabilities:
    drop:
      - ALL
```

### For Developers

#### Code Security

* **Input Validation**: Always validate and sanitize inputs
* **Error Handling**: Avoid exposing sensitive information in errors
* **Logging**: Don't log sensitive data (private keys, tokens, etc.)
* **Dependencies**: Regularly audit and update dependencies
* **Code Review**: Require security review for sensitive changes

#### Testing Security

```bash
# Security testing commands
npm audit                    # Check for vulnerable dependencies
pnpm audit                  # Alternative package manager audit
docker scan <image>         # Scan Docker images for vulnerabilities
trivy fs .                  # Filesystem vulnerability scanning
```

## 🔍 Security Monitoring

### Automated Security Checks

Our CI/CD pipeline includes:

* **Dependency Scanning**: `npm audit` and `pnpm audit`
* **Container Scanning**: Docker image vulnerability scanning
* **Code Analysis**: Static analysis for security issues
* **Secret Detection**: Scanning for accidentally committed secrets
* **License Compliance**: Ensuring secure and compatible licenses

### Runtime Security

* **Health Checks**: Regular health monitoring of deployed services
* **Log Monitoring**: Automated analysis of security-relevant logs
* **Intrusion Detection**: Monitoring for suspicious activity patterns
* **Rate Limiting**: Automatic protection against abuse

## 🚫 Security Scope

### In Scope

* **Core MCP Workers**: All code in `apps/` directory
* **Shared Packages**: All code in `packages/` directory
* **Docker Images**: Official container images
* **Kubernetes Manifests**: Deployment configurations
* **CI/CD Pipelines**: GitHub Actions workflows
* **Documentation**: Security-related documentation

### Out of Scope

* **Dependencies**: Third-party library vulnerabilities (report to upstream)
* **Infrastructure**: Underlying cloud provider or Kubernetes platform
* **Algorand Network**: The Algorand blockchain itself
* **User Applications**: Applications built using our MCP workers
* **Social Engineering**: Phishing or human-based attacks
* **Physical Security**: Physical access to deployment infrastructure

## 🏆 Recognition

### Security Researcher Credits

We believe in recognizing security researchers who help improve our project:

* **Hall of Fame**: Public recognition on our security page
* **GitHub Credits**: Mentioned in security advisory and release notes
* **Swag**: Project stickers and other merchandise (when available)
* **Reference**: Professional reference for security research work

### Responsible Disclosure

We follow responsible disclosure practices:

* **Coordination**: We work with reporters to coordinate public disclosure
* **Credit**: Security researchers receive appropriate credit
* **Timeline**: We aim for disclosure within 90 days of initial report
* **Notification**: Users are notified of security updates through multiple channels

## 📚 Security Resources

### Documentation

* [Deployment Security Guide](docs/SECURITY_DEPLOYMENT.md)
* [Development Security Guide](docs/SECURITY_DEVELOPMENT.md)
* [Incident Response Plan](docs/SECURITY_INCIDENT_RESPONSE.md)

### External Resources

* [Algorand Security Best Practices](https://developer.algorand.org/docs/security/)
* [Docker Security Best Practices](https://docs.docker.com/develop/security-best-practices/)
* [Kubernetes Security](https://kubernetes.io/docs/concepts/security/)
* [OWASP Top 10](https://owasp.org/www-project-top-ten/)

### Security Tools

* **Static Analysis**: ESLint security rules, Semgrep
* **Dependency Scanning**: npm audit, Snyk, Dependabot
* **Container Scanning**: Trivy, Docker Scout
* **Runtime Security**: Falco, OPA Gatekeeper

## 🔄 Security Updates

### Notification Channels

* **GitHub Security Advisories**: Official security announcements
* **Release Notes**: Security fixes highlighted in releases
* **Email List**: Security-specific mailing list (coming soon)
* **Social Media**: Important security updates on project accounts

### Update Process

1. **Discovery**: Vulnerability identified and verified
2. **Assessment**: Impact analysis and severity classification
3. **Development**: Fix developed and tested
4. **Review**: Security review and approval
5. **Release**: Security update released
6. **Notification**: Users notified through all channels
7. **Documentation**: Security advisory published

## 📞 Contact Information

### Security Team

* **Primary Contact**: [security@algorand-mcp.com](mailto:security@algorand-mcp.com)
* **Emergency Contact**: [urgent-security@algorand-mcp.com](mailto:urgent-security@algorand-mcp.com)
* **General Inquiries**: [security-questions@algorand-mcp.com](mailto:security-questions@algorand-mcp.com)

### Response Times

* **Critical Issues**: 2-4 hours during business hours
* **High Priority**: 24 hours
* **Medium Priority**: 72 hours
* **General Questions**: 1 week

## 🔒 Encryption and Keys

### Supported Encryption

* **Communication**: TLS 1.2+ for all HTTPS traffic
* **Storage**: AES-256 for encrypted storage (when applicable)
* **Signatures**: Ed25519 for Algorand transactions
* **Hashing**: SHA-256 for data integrity

### Key Management

* **No Key Storage**: MCP workers never store private keys
* **Transaction Signing**: Client-side signing only
* **API Keys**: Secure environment variable management
* **Rotation**: Regular rotation of service API keys

## ⚖️ Legal

### Safe Harbor

We provide safe harbor for security researchers who:

* **Follow responsible disclosure practices**
* **Do not access user data beyond what's necessary to demonstrate the vulnerability**
* **Do not disrupt or damage our services**
* **Report vulnerabilities in good faith**

### Privacy

* **Reporter Privacy**: We protect the privacy of security reporters
* **Data Handling**: Minimal data collection, secure storage
* **Retention**: Security reports retained only as long as necessary
* **Sharing**: Information shared only on a need-to-know basis

---

## 🙏 Thank You

Security is a team effort. Thank you for helping keep Algorand MCP Workers and its users safe!

---

*This security policy was last updated on September 13, 2025. Please check for updates regularly.*