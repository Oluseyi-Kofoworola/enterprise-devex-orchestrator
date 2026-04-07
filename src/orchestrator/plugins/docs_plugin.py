"""Docs Plugins -- custom documentation section generators.

Each plugin generates one or more Markdown documentation files
(runbooks, API references, compliance evidence, etc.).
"""

from __future__ import annotations

from src.orchestrator.intent_schema import IntentSpec
from src.orchestrator.logging import get_logger

logger = get_logger(__name__)


class RunbookDocPlugin:
    """Generates an operational runbook with incident-response playbooks."""

    def applies_to(self, spec: IntentSpec) -> bool:
        return True  # Every project benefits from a runbook

    def generate(self, spec: IntentSpec, **kwargs) -> dict[str, str]:
        entity_section = ""
        for entity in spec.entities[:5]:
            entity_section += f"""
### {entity.name.replace('_', ' ').title()} Issues

| Symptom | Check | Action |
|---------|-------|--------|
| {entity.name} API returns 500 | Check application logs | Restart container app revision |
| {entity.name} data missing | Verify data store connectivity | Check connection strings in Key Vault |
| Slow {entity.name} queries | Review query performance | Add index or optimize query pattern |
"""
        stores = {s.value if hasattr(s, "value") else s for s in (spec.data_stores or [])}
        store_checks = ""
        if any("cosmos" in s for s in stores):
            store_checks += "- **Cosmos DB**: Check RU consumption, partition key hot spots\n"
        if any("sql" in s for s in stores):
            store_checks += "- **Azure SQL**: Check DTU usage, long-running queries\n"
        if any("redis" in s for s in stores):
            store_checks += "- **Redis Cache**: Check memory usage, eviction rate\n"
        if any("blob" in s for s in stores):
            store_checks += "- **Blob Storage**: Check throttling metrics, access patterns\n"

        return {
            "docs/runbook.md": f"""\
# Operational Runbook -- {spec.project_name}

> Auto-generated operational guide. Customize for your environment.

## Quick Reference

| Resource | Environment | Region |
|----------|-------------|--------|
| {spec.project_name} | {spec.environment} | {spec.azure_region} |

## Health Checks

```bash
# Application health
curl https://<app-url>/health

# Readiness probe (includes dependency checks)
curl https://<app-url>/health/ready
```

## Incident Response

### Severity Levels

| Level | Response Time | Escalation |
|-------|--------------|------------|
| P1 -- Critical | 15 minutes | On-call + team lead |
| P2 -- High | 1 hour | On-call engineer |
| P3 -- Medium | 4 hours | Next business day |
| P4 -- Low | 1 business day | Backlog |

## Entity-Specific Playbooks
{entity_section}

## Data Store Health
{store_checks if store_checks else "No external data stores configured."}

## Rollback Procedure

1. Identify the last known good revision
2. Run: `az containerapp revision activate --name <app> --revision <good-revision>`
3. Shift traffic: `az containerapp ingress traffic set --revision-weight <good>=100`
4. Verify health endpoint returns 200
5. Investigate root cause of failed deployment

## Contacts

| Role | Contact |
|------|---------|
| On-Call Engineer | _TBD_ |
| Team Lead | _TBD_ |
| Platform Team | _TBD_ |
""",
        }


class APIReferenceDocPlugin:
    """Generates API reference documentation from entity definitions."""

    def applies_to(self, spec: IntentSpec) -> bool:
        return len(spec.entities) > 0

    def generate(self, spec: IntentSpec, **kwargs) -> dict[str, str]:
        sections = []
        for entity in spec.entities:
            fields_table = "| Field | Type | Description |\n|-------|------|-------------|\n"
            for f in entity.fields:
                fields_table += f"| `{f.name}` | `{f.type}` | {f.description or '--'} |\n"

            endpoints = f"""
### `GET /api/{entity.name}`
List all {entity.name} records.

### `POST /api/{entity.name}`
Create a new {entity.name} record.

**Request Body:** JSON object with fields below.

### `GET /api/{entity.name}/{{id}}`
Retrieve a single {entity.name} by ID.

### `DELETE /api/{entity.name}/{{id}}`
Delete a {entity.name} record.
"""
            sections.append(
                f"## {entity.name.replace('_', ' ').title()}\n\n"
                f"{fields_table}\n"
                f"### Endpoints\n{endpoints}"
            )

        all_sections = "\n---\n\n".join(sections)
        return {
            "docs/api-reference.md": f"""\
# API Reference -- {spec.project_name}

> Auto-generated from entity definitions. Update as your API evolves.

Base URL: `https://<app-url>/api`

## Authentication

All endpoints require a valid bearer token (Managed Identity or Entra ID).

---

{all_sections}

---

## Common Response Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request -- validation error |
| 401 | Unauthorized -- missing or invalid token |
| 404 | Not Found |
| 429 | Too Many Requests -- rate limited |
| 500 | Internal Server Error |
""",
        }


class ComplianceEvidenceDocPlugin:
    """Generates compliance evidence documentation mapping controls to implementation."""

    def applies_to(self, spec: IntentSpec) -> bool:
        return spec.security.compliance_framework.value != "general"

    def generate(self, spec: IntentSpec, **kwargs) -> dict[str, str]:
        framework = spec.security.compliance_framework.value.upper()
        controls = _FRAMEWORK_CONTROLS.get(framework, _FRAMEWORK_CONTROLS["GENERAL"])

        rows = ""
        for ctrl in controls:
            rows += f"| {ctrl['id']} | {ctrl['name']} | {ctrl['evidence']} | Implemented |\n"

        return {
            "docs/compliance-evidence.md": f"""\
# Compliance Evidence -- {spec.project_name}

> Framework: **{framework}**
> Generated: auto
> Environment: {spec.environment}

## Control Mapping

| Control ID | Control Name | Evidence | Status |
|-----------|-------------|----------|--------|
{rows}

## Architecture Controls

| Security Control | Implementation |
|-----------------|----------------|
| Encryption at rest | {"Enabled" if spec.security.encryption_at_rest else "Not configured"} |
| Encryption in transit | {"HTTPS enforced" if spec.security.encryption_in_transit else "Not configured"} |
| Secret management | {"Azure Key Vault" if spec.security.secret_management else "Not configured"} |
| Authentication | {spec.security.auth_model.value} |
| Network model | {spec.security.networking.value} |
| Data classification | {spec.security.data_classification} |

## Audit Trail

All infrastructure changes are tracked via:
- Git version control (commit history)
- Azure Activity Log
- GitHub Actions workflow run logs
- `.devex/state.json` state tracking with hash verification
""",
        }


_FRAMEWORK_CONTROLS = {
    "SOC2_GUIDANCE": [
        {"id": "CC6.1", "name": "Logical Access Controls", "evidence": "Managed Identity + RBAC in Bicep"},
        {"id": "CC6.6", "name": "Encryption in Transit", "evidence": "TLS 1.2+ enforced, HTTPS only"},
        {"id": "CC6.7", "name": "Encryption at Rest", "evidence": "Azure-managed encryption keys"},
        {"id": "CC7.2", "name": "System Monitoring", "evidence": "Log Analytics + diagnostic settings"},
        {"id": "CC8.1", "name": "Change Management", "evidence": "Git + PR workflow + CI/CD gates"},
    ],
    "HIPAA_GUIDANCE": [
        {"id": "164.312(a)", "name": "Access Control", "evidence": "Managed Identity + Key Vault RBAC"},
        {"id": "164.312(c)", "name": "Integrity", "evidence": "Immutable container images in ACR"},
        {"id": "164.312(d)", "name": "Authentication", "evidence": "Entra ID / Managed Identity"},
        {"id": "164.312(e)", "name": "Transmission Security", "evidence": "TLS 1.2+ enforced"},
        {"id": "164.316(b)", "name": "Documentation", "evidence": "Auto-generated docs + ADRs"},
    ],
    "FEDRAMP_GUIDANCE": [
        {"id": "Req 1", "name": "Network Security", "evidence": "NSG + Private Endpoints + VNet"},
        {"id": "Req 3", "name": "Protect Cardholder Data", "evidence": "Key Vault + encryption at rest"},
        {"id": "Req 6", "name": "Secure Development", "evidence": "CodeQL + Dependabot + SAST"},
        {"id": "Req 8", "name": "Access Control", "evidence": "RBAC + Managed Identity"},
        {"id": "Req 10", "name": "Logging & Monitoring", "evidence": "Log Analytics + alerts"},
    ],
    "GENERAL": [
        {"id": "SEC-01", "name": "Authentication", "evidence": "Managed Identity configured"},
        {"id": "SEC-02", "name": "Encryption", "evidence": "TLS 1.2+ and encryption at rest"},
        {"id": "SEC-03", "name": "Logging", "evidence": "Log Analytics workspace enabled"},
        {"id": "SEC-04", "name": "Access Control", "evidence": "RBAC role assignments"},
    ],
}
