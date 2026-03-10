# Security Posture -- SLHS Voice Agent v3.0

> **Defense-in-depth security** across identity, secrets, network, container,
> supply chain, and application layers.

---

## Security Summary

| Dimension | Status | Implementation |
|-----------|--------|---------------|
| Identity | PASS | User-assigned Managed Identity -- zero credentials in code |
| Secrets | PASS | Key Vault with RBAC, soft-delete, purge protection |
| Network | PASS | TLS 1.2+ enforced, HTTPS-only ingress |
| Container | PASS | Non-root user, minimal base image, multi-stage build |
| Registry | PASS | ACR admin disabled, Managed Identity pull (AcrPull role) |
| Logging | PASS | Structured JSON to Log Analytics, no PII in logs |
| Supply Chain | PASS | Dependabot, CodeQL scanning, pinned dependencies |
| Data | PASS | Input sanitization, session isolation, HTML escaping |

---

## STRIDE Threat Model

### 1. Spoofing

| Threat | Risk | Mitigation |
|--------|------|------------|
| Identity spoofing of service | Medium | Managed Identity with Azure AD -- no passwords or keys |
| User session hijacking | Medium | UUID-based sessions, no cookies with PII, server-side session store |
| ACR image tampering | Low | Managed Identity pull, no admin credentials exposed |

### 2. Tampering

| Threat | Risk | Mitigation |
|--------|------|------------|
| Container image modification | Medium | ACR with admin disabled, signed images path |
| API request manipulation | Medium | Pydantic input validation on all endpoints |
| Log tampering | Low | Logs shipped to Log Analytics (append-only, centralized) |

### 3. Repudiation

| Threat | Risk | Mitigation |
|--------|------|------------|
| Untracked API calls | Medium | Structured JSON logging with timestamp, session_id, intent |
| Denied patient record access | Medium | Audit trail in logs, operation-level tracking |
| Deployment without approval | Low | Git-based deploy, revision history in Container Apps |

### 4. Information Disclosure

| Threat | Risk | Mitigation |
|--------|------|------------|
| Patient data in logs | High | No PII logged -- only session_id and intent classification |
| Key Vault secret exposure | High | RBAC access, soft-delete, purge protection, no env vars |
| Error message leaking internals | Medium | FastAPI production mode, generic error responses |
| Voice data interception | Medium | TLS 1.2+ on all connections, HTTPS-only ingress |

### 5. Denial of Service

| Threat | Risk | Mitigation |
|--------|------|------------|
| API flood | Medium | Container Apps built-in scaling limits |
| Voice API abuse | Low | Session-scoped rate limiting, browser-side controls |
| Container resource exhaustion | Low | CPU/memory limits (0.25 vCPU / 0.5 Gi) with health probes |

### 6. Elevation of Privilege

| Threat | Risk | Mitigation |
|--------|------|------------|
| Container breakout | Low | Non-root user, read-only filesystem where possible |
| RBAC over-permissioning | Low | Least-privilege roles: AcrPull, Key Vault Secrets User only |
| Cross-session data access | Medium | Session isolation with UUID boundaries, no shared state |

---

## Security Controls by Component

### Container App (`devex-orchestrator-dev`)

| Control | Detail |
|---------|--------|
| Runtime identity | User-assigned Managed Identity (no secrets) |
| Container user | Non-root (security best practice) |
| Resource limits | 0.25 vCPU, 0.5 Gi memory |
| Health probes | `/health` endpoint for liveness and readiness |
| Ingress | External HTTPS-only, TLS 1.2+ |
| Scaling | 0-10 replicas (consumption plan) |

### Key Vault (`devexorchestratordevkv`)

| Control | Detail |
|---------|--------|
| Access model | RBAC (not access policies) |
| Soft delete | Enabled (90-day retention) |
| Purge protection | Enabled |
| Network | Azure backbone access via Managed Identity |
| Permitted role | `Key Vault Secrets User` for MI only |

### Container Registry (`devexorchestratordevacr`)

| Control | Detail |
|---------|--------|
| Admin account | Disabled |
| Pull authentication | Managed Identity with `AcrPull` role |
| Build method | Cloud-side `az acr build` (no local Docker) |

### Log Analytics (`devex-orchestrator-dev-law`)

| Control | Detail |
|---------|--------|
| Retention | 30 days |
| Access | Workspace-scoped RBAC |
| Format | Structured JSON (machine-parseable) |
| PII | No patient data in logs |

---

## RBAC Role Assignments

| Principal | Resource | Role | Justification |
|-----------|----------|------|---------------|
| `devex-orchestrator-dev-id` | Key Vault | Key Vault Secrets User | Read secrets at runtime |
| `devex-orchestrator-dev-id` | ACR | AcrPull | Pull container images |
| `devex-orchestrator-dev-id` | Container App | Contributor | Self-management |
| Deployment identity | Resource Group | Contributor | Infrastructure provisioning |

> **Principle:** Every role assignment follows least-privilege. No Contributor
> or Owner roles on Key Vault. No admin credentials anywhere.

---

## Application Security

### Input Validation

```python
# All API inputs validated via Pydantic models
class ChatRequest(BaseModel):
    message: str  # Validated string type
    session_id: Optional[str] = None  # UUID format

# HTML output escaped to prevent XSS
html_mod.escape(user_input)
```

### Session Security

- UUID-based session identifiers (no sequential IDs)
- Server-side session storage (not client cookies)
- Session isolation -- no cross-session data access
- No PII stored in session identifiers

### Voice Security

- Web Speech API audio processed in browser (not sent to our servers)
- Speech recognition via browser's built-in engine (Google/system)
- No audio recording or storage
- Auto-retry on network failure (3 attempts with backoff)

---

## Compliance Alignment

| Framework | Status | Evidence |
|-----------|--------|----------|
| HIPAA Technical Safeguards | Aligned | Encryption in transit (TLS), access controls (RBAC), audit logs |
| SOC 2 Type II | Aligned | Managed Identity, Key Vault, structured logging, access controls |
| Azure CIS Benchmark | Aligned | Non-root containers, RBAC over access policies, admin disabled on ACR |
| OWASP Top 10 | Mitigated | Input validation, output encoding, no hardcoded secrets, session management |

---

## Security Testing

```powershell
# Run security-focused tests
pytest tests/test_security.py -v

# Verify no secrets in codebase
Select-String -Path "slhs-voice-agent/src/app/*.py" -Pattern "(password|secret|key)\s*=" -CaseSensitive:$false

# Check container runs as non-root
# Verified in Dockerfile: USER appuser
```

---

*Security posture validated by Enterprise Governance Reviewer*
*STRIDE threat model covers all 6 categories with documented mitigations*
