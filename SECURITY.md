# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 2.x     | ✅ Yes     |
| 1.x     | ❌ No      |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

To report a security vulnerability, use [GitHub private vulnerability reporting](https://github.com/Oluseyi-Kofoworola/enterprise-devex-orchestrator/security/advisories/new).

Include:
- A description of the vulnerability and its potential impact
- Steps to reproduce (proof-of-concept if possible)
- Any affected versions you are aware of
- Suggested remediation if you have one

You should receive an acknowledgement within **48 hours** and a substantive response
within **7 days**. We will keep you informed of the remediation timeline.

## Security Design

The orchestrator is designed with security as a first-class concern:

- **No credentials in generated code** — all secrets are referenced via environment variables or Key Vault
- **OIDC for CI/CD** — generated GitHub Actions workflows use OpenID Connect, never stored tokens
- **Managed Identity** — generated Azure workloads use Managed Identity, not service principal keys
- **Soft delete and purge protection** — Key Vault templates enforce these by default
- **Non-root containers** — generated Dockerfiles run as a non-root user
- **OWASP security headers** — generated FastAPI apps include `X-Content-Type-Options`, `X-Frame-Options`, `Strict-Transport-Security`, and CSP headers

## Scope

Vulnerabilities in the following areas are in scope:

- The `devex` CLI and orchestration engine (`src/orchestrator/`)
- Generated Bicep templates that introduce insecure defaults
- Generated application code with exploitable security flaws (e.g., injection, SSRF, IDOR)
- Dependency vulnerabilities in `pyproject.toml`

Out of scope: vulnerabilities in user-generated output after customization, third-party LLM provider APIs.
