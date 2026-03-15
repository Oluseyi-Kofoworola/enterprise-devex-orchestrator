# Demo Script: smart-city-ai-operations-platform-extre

> Duration: 3 minutes | No improvisation -- follow this script exactly.

## Project Overview

- **Description:** Build an enterprise-grade AI-powered smart city operations platform that orchestrates **9 distinct domain entities** across every supported data store (Cosmos DB, SQL, Blob Storage, Redis, AI Search, 
- **Domain Entities:** Incident, Asset, Sensor, ServiceRequest, TransitRoute, Vehicle, Zone, WorkOrder, AuditLog
- **Data Stores:** Cosmos Db, Blob Storage, Sql, Redis, Ai Search, Table Storage
- **Compute:** Container Apps
- **Region:** eastus2

## Setup (Before Recording)

1. Ensure Azure subscription is active
2. Ensure `.env` is configured
3. Have a terminal open in the project root
4. Have Azure Portal open in a browser tab
5. (Optional) Have backup screenshots in `docs/screenshots/`

## Demo Flow

### Minute 0:00 -- 0:30 | Introduction

**Say:** "We built an Enterprise DevEx Orchestrator -- a Copilot SDK-powered
agent that transforms plain-English business intent into production-ready,
secure, deployable Azure workloads. Today we'll demonstrate it with a
build an enterprise-grade ai-powered smart city operations platform that orchestrates **9 distinct domain entities** across every supported data store (cosmos db, sql, blob storage, redis, ai search,  use case."

**Show:** README.md in the repo

### Minute 0:30 -- 1:30 | Agent in Action

**Run:**
```bash
python -m src.orchestrator.main scaffold \
  --file intent.md -o ./smart-city-ai-operations-platform-extre
```

**Show:**
- Intent parsing output -- notice the 9 domain entities extracted: Incident, Asset, Sensor, ServiceRequest, TransitRoute, Vehicle, Zone, WorkOrder, AuditLog
- Architecture plan (`docs/plan.md`) with Build an enterprise-grade AI-powered smart city operations platform that orchestrates **9 distinct domain entities** across every supported data store (Cosmos DB, SQL, Blob Storage, Redis, AI Search, 
- Mermaid diagram rendering
- Governance validation report -- all checks PASS

**Say:** "The agent parsed our intent, extracted 9 domain
entities (Incident, Asset, Sensor, ServiceRequest, TransitRoute, Vehicle, Zone, WorkOrder, AuditLog), generated an architecture plan with ADRs and
threat model, validated against governance policies, and produced deployable
infrastructure."

### Minute 1:30 -- 2:15 | Generated Artifacts

**Show:**
- `infra/bicep/main.bicep` -- Infrastructure as Code with Cosmos Db, Blob Storage, Sql, Redis, Ai Search, Table Storage
- `infra/bicep/modules/` -- Modular Bicep files
- `.github/workflows/` -- CI/CD pipelines with OIDC
- `src/app/main.py` -- Interactive business dashboard + API
- `docs/security.md` -- Security controls and STRIDE threat model
- `docs/governance-report.md` -- Governance validation results

**Highlight the business dashboard:**
- KPI cards showing live counts per entity (Incident, Asset, Sensor, ServiceRequest, TransitRoute, Vehicle, Zone, WorkOrder, AuditLog)
- Data tables with search, status badges, and workflow actions
- Create/edit forms auto-generated from domain schema
- Approve/reject/process workflow buttons

**Sample API endpoints to demo:**
- `GET /audit_logs` -- Query with filters by event_type, agent_name, user_role, status, date range

**Say:** "Every artifact is domain-specific: the API handles Incident, Asset, Sensor, ServiceRequest, TransitRoute, Vehicle, Zone, WorkOrder, AuditLog with
full CRUD and workflow actions. Infrastructure includes Cosmos Db, Blob Storage, Sql, Redis, Ai Search, Table Storage,
managed identity, Key Vault, and CI/CD with OIDC -- all generated from
the intent file."

### Minute 2:15 -- 2:45 | Live Deployment

**Option A (Live):**
```bash
az deployment group create \
  --resource-group rg-smart-city-ai-operations-platform-extre-prod \
  --template-file infra/bicep/main.bicep \
  --parameters infra/bicep/parameters/dev.parameters.json
```

**Option B (Pre-deployed):**
- Switch to Azure Portal
- Show Resource Group with all resources
- Click into Container App -> show dashboard with Incident, Asset, Sensor, ServiceRequest, TransitRoute, Vehicle, Zone, WorkOrder, AuditLog data
- Click into Log Analytics -> run sample KQL query

### Minute 2:45 -- 3:00 | Wrap Up

**Say:** "Enterprises don't need faster code. They need safe, compliant,
repeatable architecture. We built a Copilot SDK-powered orchestrator that
turns intent into governed infrastructure with domain-aware APIs, interactive
dashboards, security, observability, and CI/CD -- all tailored to your
business problem."

## Backup Plan

If live demo fails:
1. Show pre-recorded terminal output
2. Show Azure Portal screenshots in `docs/screenshots/`
3. Walk through generated code in the repo
4. Open `http://localhost:8000/` to show the interactive dashboard locally

## Azure Portal Locations to Show

| Resource | What to Click |
|----------|--------------|
| Resource Group | Overview -> see all resources |
| Container App | Overview -> FQDN, Revisions |
| Key Vault | Access policies -> RBAC |
| Log Analytics | Logs -> run KQL query |
| Container Registry | Repositories -> image |

## Sample KQL Query

```kql
ContainerAppConsoleLogs_CL
| where ContainerAppName_s == "smart-city-ai-operations-platform-extre"
| project TimeGenerated, Log_s, RevisionName_s
| order by TimeGenerated desc
| take 20
```

---
*Generated by Enterprise DevEx Orchestrator Agent*
