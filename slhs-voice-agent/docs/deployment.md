# Deployment Guide -- SLHS Voice Agent v3.0

> **St. Luke's Health System Voice Agent** -- Enterprise Healthcare Assistant
> Built as a 0.0001% engineering showcase | Azure Well-Architected Framework aligned

## Live Production

| Attribute | Value |
|-----------|-------|
| **URL** | `https://devex-orchestrator-dev.greenbay-9ec52bc2.eastus2.azurecontainerapps.io` |
| **Version** | v3.0.0 (app) / v3.0.1 (container image) |
| **Region** | East US 2 |
| **Status** | Production -- serving traffic |

---

## Architecture (Deployed)

```
Internet (TLS 1.2+)
  +-- Azure Container Apps (external ingress, HTTPS-only, port 8000)
        +-- FastAPI + Uvicorn (2 workers, non-root container)
        |     +-- /health          -> Health probe (liveness + readiness)
        |     +-- /                -> Voice Chat UI (SPA with Web Speech API)
        |     +-- /chat            -> Conversational AI engine (10+ intents)
        |     +-- /patients        -> Patient record lookup (5 patients)
        |     +-- /appointments    -> Appointment scheduling
        |     +-- /docs            -> OpenAPI/Swagger documentation
        +-- Azure Key Vault (RBAC, soft-delete + purge protection)
        +-- Azure Container Registry (admin disabled, MI pull)
        +-- User-Assigned Managed Identity (zero secrets)
        +-- Log Analytics Workspace (JSON structured logs, 30d retention)
```

---

## Deployed Azure Resources

| Resource | Name | SKU | Purpose |
|----------|------|-----|---------|
| Resource Group | `rg-devex-orchestrator-dev` | -- | Logical container |
| Log Analytics | `devex-orchestrator-dev-law` | PerGB2018 | Centralized logging |
| Managed Identity | `devex-orchestrator-dev-id` | -- | Zero-secret auth |
| Key Vault | `devexorchestratordevkv` | Standard | Secrets management |
| Container Registry | `devexorchestratordevacr` | Basic | Image storage |
| Container App Env | `devex-orchestrator-dev-env` | Consumption | Serverless hosting |
| Container App | `devex-orchestrator-dev` | 0.25 vCPU / 0.5 Gi | Application runtime |

---

## Prerequisites

| Tool | Version | Required | Notes |
|------|---------|----------|-------|
| Azure CLI | 2.50+ | Yes | `az --version` to check |
| Bicep CLI | 0.22+ | Yes | Bundled with Azure CLI |
| Python | 3.11+ | Yes | Local dev only |
| Docker | -- | **No** | Builds happen on ACR (cloud-side) |

> **Key insight:** This deployment requires NO local Docker installation.
> All container builds use `az acr build` -- cloud-side builds eliminate
> local environment inconsistencies.

---

## Deployment Pipeline

### Step 1: Authenticate

```powershell
az login
az account set --subscription "e47370c7-8804-46b9-86f9-a96f5e950535"
```

### Step 2: Deploy Infrastructure (Bicep)

```powershell
# Validate -- catch errors before deploy
az deployment group validate `
  --resource-group rg-devex-orchestrator-dev `
  --template-file infra/bicep/main.bicep `
  --parameters infra/bicep/parameters/dev.bicepparam

# What-if -- preview all changes (dry run)
az deployment group what-if `
  --resource-group rg-devex-orchestrator-dev `
  --template-file infra/bicep/main.bicep `
  --parameters infra/bicep/parameters/dev.bicepparam

# Deploy -- create/update infrastructure
az deployment group create `
  --resource-group rg-devex-orchestrator-dev `
  --template-file infra/bicep/main.bicep `
  --parameters infra/bicep/parameters/dev.bicepparam
```

### Step 3: Build Container Image (Cloud Build)

```powershell
# Build on ACR -- no local Docker needed
az acr build `
  --registry devexorchestratordevacr `
  --image slhs-voice-agent:v3.0.1 `
  --file slhs-voice-agent/src/app/Dockerfile `
  slhs-voice-agent/src/app/ `
  --no-logs

# Verify image exists
az acr repository show-tags `
  --name devexorchestratordevacr `
  --repository slhs-voice-agent `
  --output table
```

> **`--no-logs` flag:** Required on Windows terminals (cp1252 encoding) to
> prevent charmap errors when Docker build output contains non-ASCII characters.

### Step 4: Deploy Application

```powershell
az containerapp update `
  --name devex-orchestrator-dev `
  --resource-group rg-devex-orchestrator-dev `
  --image devexorchestratordevacr.azurecr.io/slhs-voice-agent:v3.0.1
```

### Step 5: Verify

```powershell
$BASE = "https://devex-orchestrator-dev.greenbay-9ec52bc2.eastus2.azurecontainerapps.io"

# Health check -- must return {"status":"healthy","version":"3.0.0"}
Invoke-RestMethod "$BASE/health"

# All endpoints must return HTTP 200
@("/health", "/", "/patients", "/appointments") | ForEach-Object {
    $status = (Invoke-WebRequest "$BASE$_" -UseBasicParsing).StatusCode
    Write-Output "$_ -> $status"
}

# Check active revision
az containerapp revision list `
  --name devex-orchestrator-dev `
  --resource-group rg-devex-orchestrator-dev `
  -o table
```

---

## Rollback

### Application Rollback (< 2 minutes)

```powershell
# List all revisions with traffic weights
az containerapp revision list `
  --name devex-orchestrator-dev `
  --resource-group rg-devex-orchestrator-dev `
  -o table

# Activate previous good revision
az containerapp revision activate `
  --name devex-orchestrator-dev `
  --resource-group rg-devex-orchestrator-dev `
  --revision <previous-revision-name>

# Shift 100% traffic to the safe revision
az containerapp ingress traffic set `
  --name devex-orchestrator-dev `
  --resource-group rg-devex-orchestrator-dev `
  --revision-weight <previous-revision-name>=100
```

### Infrastructure Rollback

```powershell
# Revert Bicep to previous commit
git log --oneline infra/bicep/
git checkout <commit-hash> -- infra/bicep/

# Redeploy previous infrastructure
az deployment group create `
  --resource-group rg-devex-orchestrator-dev `
  --template-file infra/bicep/main.bicep `
  --parameters infra/bicep/parameters/dev.bicepparam
```

---

## Environment Variables

| Variable | Value | Source |
|----------|-------|--------|
| `AZURE_CLIENT_ID` | `f2df34ec-9aaa-43f5-87fc-7a15c636da35` | Managed Identity |
| `AZURE_KEYVAULT_URL` | `https://devexorchestratordevkv.vault.azure.net/` | Key Vault |
| `PORT` | `8000` | Container Apps platform |

---

## Security Controls (Production)

| Control | Implementation | WAF Pillar |
|---------|---------------|------------|
| Identity | User-assigned Managed Identity -- zero secrets | Security |
| Secrets | Key Vault RBAC + soft-delete + purge protection | Security |
| Container | Non-root user, minimal base image | Security |
| Transport | TLS 1.2+ enforced, HTTPS-only ingress | Security |
| Registry | ACR admin disabled, MI-based AcrPull | Security |
| Logging | Structured JSON -> Log Analytics | Operational Excellence |
| Builds | Cloud-side ACR builds, no local Docker | Reliability |
| Rollback | Revision-based instant rollback | Reliability |

---

## Teardown

```powershell
# WARNING: Destroys ALL resources. Key Vault enters 90-day soft-delete.
az group delete --name rg-devex-orchestrator-dev --yes --no-wait

# Verify deletion
az group show --name rg-devex-orchestrator-dev 2>$null
if ($LASTEXITCODE -ne 0) { Write-Output "Resource group deleted" }
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `az acr build` charmap error | Windows cp1252 terminal | Add `--no-logs` flag |
| Container CrashLoopBackOff | App startup failure | `az containerapp logs show --name devex-orchestrator-dev -g rg-devex-orchestrator-dev` |
| Key Vault 403 Forbidden | Missing RBAC role | Grant `Key Vault Secrets User` to Managed Identity |
| Health check timeout | Port mismatch | Confirm container exposes port 8000 |
| Voice "network error" in browser | Corporate firewall blocks Google Speech API | Expected -- app auto-retries 3x with exponential backoff |
| Image pull error | ACR auth failure | Verify `AcrPull` role on Managed Identity |
| Revision not receiving traffic | Traffic weight is 0% | `az containerapp ingress traffic set` |

---

*SLHS Voice Agent -- St. Luke's Health System*
*Built with the Enterprise DevEx Orchestrator | Azure WAF Aligned*
