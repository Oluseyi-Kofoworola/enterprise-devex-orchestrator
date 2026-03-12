# Deployment Guide

> **Enterprise DevEx Orchestrator** -- Deploy orchestrator-generated scaffolds to Azure

---

## Prerequisites

| Requirement | Command to Verify |
|------------|------------------|
| Azure CLI | `az version` |
| Python 3.11+ | `python --version` |
| Bicep CLI | `az bicep version` |
| Azure subscription | `az account show` |

## Deployment Architecture

The orchestrator generates scaffolds with a standardized deployment pipeline:

```
devex scaffold -> infra/bicep/ + src/app/ + frontend/ + .github/workflows/
                          |
                    az deployment group create (Bicep)
                          |
                    az acr build (backend + frontend images)
                          |
                    az containerapp update (deploy revisions)
```

## Quick Deploy (Manual)

### 1. Generate Scaffold

```bash
# From intent
devex scaffold --intent "Build a healthcare voice agent API with cosmos and redis"

# From intent file
devex scaffold --intent-file intent.md

# Preview plan without generating files
devex plan --intent "Build a patient portal API"
```

### 2. Deploy Infrastructure

```bash
# Set variables
RG="rg-<project-name>-dev"
LOCATION="eastus2"

# Create resource group
az group create --name $RG --location $LOCATION

# Deploy Bicep
az deployment group create \
  --resource-group $RG \
  --template-file infra/bicep/main.bicep \
  --parameters @infra/bicep/parameters/dev.bicepparam
```

### 3. Build and Deploy Application

```bash
# Get ACR name from deployment outputs
ACR_NAME=$(az deployment group show --resource-group $RG --name main --query properties.outputs.acrName.value -o tsv)

# Build backend in ACR (no local Docker required)
az acr build --registry $ACR_NAME --image <project>-api:v1.0.0 --no-logs src/app/

# Build frontend in ACR
az acr build --registry $ACR_NAME --image <project>-frontend:v1.0.0 --no-logs frontend/

# Update backend Container App
az containerapp update \
  --name <project>-dev \
  --resource-group $RG \
  --image ${ACR_NAME}.azurecr.io/<project>-api:v1.0.0

# Update frontend Container App (if deployed separately)
az containerapp update \
  --name <project>-frontend-dev \
  --resource-group $RG \
  --image ${ACR_NAME}.azurecr.io/<project>-frontend:v1.0.0
```

### 4. Verify

```bash
# Get app URL
APP_URL=$(az containerapp show --name <project>-dev --resource-group $RG --query properties.configuration.ingress.fqdn -o tsv)

# Health check
curl https://$APP_URL/health
```

## Staged Deploy (Orchestrator)

The built-in deploy orchestrator runs a 4-stage pipeline:

```bash
devex deploy --output-dir ./my-project --resource-group $RG --region eastus2
```

| Stage | Action | On Failure |
|-------|--------|-----------|
| 1. Validate | `az deployment group validate` | Stop with errors |
| 2. What-If | `az deployment group what-if` | Show diff, continue |
| 3. Deploy | `az deployment group create` | Retry transient, stop hard errors |
| 4. Verify | Health probe + log check | Report status |

## CI/CD (GitHub Actions)

Generated scaffolds include 4 workflows:

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `validate.yml` | PR to main | Bicep lint + what-if |
| `deploy.yml` | Push to main | Build + deploy |
| `dependabot.yml` | Schedule | Dependency updates |
| `codeql.yml` | Schedule + PR | Security scanning |

All workflows use **OIDC federation** -- no stored credentials.

## Example Deployment Reference

After scaffolding, your deployment resources follow this pattern:

| Resource | Naming Convention |
|----------|------------------|
| Resource Group | `rg-<project>-<env>` |
| Region | As specified in intent |
| Container App (API) | `<project>-<env>` |
| Container App (Frontend) | `<project>-frontend-<env>` |
| ACR | `<project><env>acr` |
| API Image | `<acr-name>.azurecr.io/<project>-api:<version>` |
| Frontend Image | `<acr-name>.azurecr.io/<project>-frontend:<version>` |
| URL | `https://<container-app-fqdn>` |

```bash
# Example deploy command
az acr build --registry <acr-name> --image <project>:v1.0.0 --no-logs <output-dir>/src/app/
```

## Rollback

```bash
# List revisions
az containerapp revision list --name <app> --resource-group $RG --query "[].name" -o tsv

# Switch traffic to previous revision
az containerapp ingress traffic set --name <app> --resource-group $RG \
  --revision-weight <previous-revision>=100
```

## Frontend Deployment

Generated scaffolds include a React + Vite + TypeScript frontend with a multi-stage Dockerfile:

```bash
# The frontend Dockerfile uses multi-stage build:
# Stage 1: node:18-alpine builds the React app
# Stage 2: nginx:alpine serves the static assets

# Build and deploy frontend
az acr build --registry $ACR_NAME --image <project>-frontend:v1.0.0 --no-logs frontend/
```

The frontend connects to the backend API via the `VITE_API_URL` environment variable set at build time.

---

*Deployment patterns enforce enterprise security: OIDC auth, Managed Identity, RBAC over access policies.*
*Full-stack scaffolds: Backend (Python/Node.js/.NET) + Frontend (React+Vite+TypeScript) + Infrastructure (Bicep).*


