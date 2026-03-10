# Governance Report -- SLHS Voice Agent v3.0

> **Status: PASS_WITH_WARNINGS**
> 25 governance checks executed | 24 passed | 1 warning

---

## Summary

| Metric | Value |
|--------|-------|
| **Overall Status** | PASS_WITH_WARNINGS |
| **Checks Run** | 25 |
| **Passed** | 24 |
| **Failed** | 0 |
| **Warnings** | 1 |
| **Run Date** | 2026-03-15 |
| **Engine** | Enterprise DevEx Orchestrator Governance Reviewer |

---

## Governance Checks

### Identity & Access (6/6 PASS)

| # | Check | Status | Evidence |
|---|-------|--------|----------|
| 1 | Managed Identity present | PASS | User-assigned MI: `devex-orchestrator-dev-id` |
| 2 | No hardcoded credentials | PASS | Zero passwords/keys in codebase |
| 3 | RBAC over access policies | PASS | Key Vault uses RBAC model |
| 4 | Least-privilege roles | PASS | Only `AcrPull` and `Key Vault Secrets User` |
| 5 | No admin accounts on ACR | PASS | Admin disabled on `devexorchestratordevacr` |
| 6 | OIDC for CI/CD | PASS | GitHub Actions uses federated credentials |

### Secrets Management (4/4 PASS)

| # | Check | Status | Evidence |
|---|-------|--------|----------|
| 7 | Key Vault present | PASS | `devexorchestratordevkv` deployed |
| 8 | Soft delete enabled | PASS | 90-day retention |
| 9 | Purge protection | PASS | Enabled |
| 10 | No secrets in env vars | PASS | Only AZURE_CLIENT_ID (non-secret) and AZURE_KEYVAULT_URL |

### Networking (3/3 PASS)

| # | Check | Status | Evidence |
|---|-------|--------|----------|
| 11 | TLS 1.2+ enforced | PASS | Container Apps managed TLS |
| 12 | HTTPS-only ingress | PASS | HTTP redirect to HTTPS |
| 13 | No public storage endpoints | PASS | No storage accounts with public access |

### Container Security (4/4 PASS)

| # | Check | Status | Evidence |
|---|-------|--------|----------|
| 14 | Non-root container | PASS | `USER appuser` in Dockerfile |
| 15 | Minimal base image | PASS | `python:3.11-slim` |
| 16 | No sensitive build args | PASS | No secrets passed during build |
| 17 | Resource limits set | PASS | 0.25 vCPU, 0.5 Gi memory |

### Observability (3/3 PASS)

| # | Check | Status | Evidence |
|---|-------|--------|----------|
| 18 | Log Analytics workspace | PASS | `devex-orchestrator-dev-law` |
| 19 | Structured logging | PASS | JSON format to stdout |
| 20 | Health endpoint | PASS | `/health` returns version + status |

### CI/CD Security (2/2 PASS)

| # | Check | Status | Evidence |
|---|-------|--------|----------|
| 21 | No stored credentials in CI | PASS | OIDC federation |
| 22 | CodeQL scanning | PASS | GitHub Actions workflow |

### Governance Quality (2/3 -- 1 WARNING)

| # | Check | Status | Evidence |
|---|-------|--------|----------|
| 23 | ADRs documented | PASS | 6 ADRs in plan.md |
| 24 | STRIDE threat model | PASS | 6 categories with mitigations |
| 25 | CAF naming compliance | WARNING | Resource group `rg-devex-orchestrator-dev` follows convention, but some resource names could improve length compliance |

---

## Warning Details

### W-25: CAF Naming -- Minor Deviation

**Check:** All resource names follow Azure Cloud Adoption Framework naming conventions.

**Finding:** The resource group name `rg-devex-orchestrator-dev` follows the
`rg-<project>-<env>` pattern correctly. However, the Key Vault name
`devexorchestratordevkv` approaches the 24-character limit (22 chars).

**Recommendation:** For longer project names, consider abbreviating the project
portion to stay well within Azure naming limits (3-24 chars for Key Vault).

**Severity:** Low -- current names are valid and functional.

---

## Policy Catalog Referenced

| Policy ID | Policy Name | Category |
|-----------|-------------|----------|
| GOV-001 | Managed Identity Required | Identity |
| GOV-002 | No Hardcoded Credentials | Identity |
| GOV-003 | RBAC Over Access Policies | Identity |
| GOV-004 | Least Privilege Roles | Identity |
| GOV-005 | ACR Admin Disabled | Identity |
| GOV-006 | OIDC for CI/CD | Identity |
| GOV-007 | Key Vault Present | Secrets |
| GOV-008 | Soft Delete Enabled | Secrets |
| GOV-009 | Purge Protection Enabled | Secrets |
| GOV-010 | No Secrets in Env Vars | Secrets |
| GOV-011 | TLS 1.2+ Enforced | Network |
| GOV-012 | HTTPS-Only Ingress | Network |
| GOV-013 | No Public Storage | Network |
| GOV-014 | Non-Root Container | Container |
| GOV-015 | Minimal Base Image | Container |
| GOV-016 | No Sensitive Build Args | Container |
| GOV-017 | Resource Limits Set | Container |
| GOV-018 | Log Analytics Present | Observability |
| GOV-019 | Structured Logging | Observability |
| GOV-020 | Health Endpoint | Observability |
| GOV-021 | No Stored CI Credentials | CI/CD |
| GOV-022 | CodeQL Scanning | CI/CD |
| GOV-023 | ADRs Documented | Governance |
| GOV-024 | STRIDE Threat Model | Governance |
| GOV-025 | CAF Naming Compliance | Governance |

---

*Governance assessment by Enterprise DevEx Orchestrator*
*20-policy catalog with automated validation*
