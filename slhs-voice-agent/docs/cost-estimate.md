# Cost Estimate -- SLHS Voice Agent v3.0

> **Monthly cost estimate** for all Azure resources in `rg-devex-orchestrator-dev`
> Region: East US 2 | Environment: Development

---

## Resource Cost Summary

| # | Resource | SKU/Tier | Monthly Cost | Notes |
|---|----------|----------|-------------|-------|
| 1 | Container App | Consumption | $0.00 - $18.00 | First 2M requests free; scale-to-zero |
| 2 | Container App Environment | Consumption | $0.00 | Included with Container Apps |
| 3 | Container Registry | Basic | $5.00 | 10 GB storage included |
| 4 | Key Vault | Standard | $0.03 | $0.03/10K operations; minimal usage in dev |
| 5 | Managed Identity | -- | $0.00 | No cost for user-assigned managed identity |
| 6 | Log Analytics | Pay-as-you-go | $2.76 - $5.00 | 5 GB/month free; ~1-2 GB dev ingestion |
| 7 | Resource Group | -- | $0.00 | No cost for resource groups |
| **Total** | | | **$7.79 - $28.03** | |

---

## Cost Breakdown by Service

### Container App (`devex-orchestrator-dev`)

| Dimension | Unit Price | Dev Estimate |
|-----------|-----------|-------------|
| vCPU | $0.000024/sec | ~$2.00/mo (light usage) |
| Memory | $0.000003/GiB/sec | ~$1.00/mo |
| Requests | $0.40/million | $0.00 (under 2M free tier) |
| Scale-to-zero | -- | $0.00 when idle |
| **Subtotal** | | **$0.00 - $18.00** |

*Consumption plan: pay only for active processing. Scale-to-zero means zero cost during idle periods. Dev workloads typically cost <$5/month.*

### Container Registry (`devexorchestratordevacr`)

| Tier | Storage | Builds | Monthly |
|------|---------|--------|---------|
| Basic | 10 GB included | -- | $5.00 |

*ACR Basic is sufficient for dev. `az acr build` runs use ACR compute (included in tier pricing for Basic builds).*

### Key Vault (`devexorchestratordevkv`)

| Operation | Unit Price | Dev Estimate |
|-----------|-----------|-------------|
| Secret operations | $0.03/10K | ~$0.03/mo |
| Certificate operations | $3.00/renewal | $0.00 (none in dev) |
| HSM keys | N/A | $0.00 (not used) |
| **Subtotal** | | **$0.03** |

*Soft-delete and purge protection enabled (no extra cost). Managed Identity access via RBAC (no extra cost).*

### Log Analytics (`devex-orchestrator-dev-law`)

| Dimension | Free Tier | Overage | Dev Estimate |
|-----------|-----------|---------|-------------|
| Data ingestion | 5 GB/month free | $2.76/GB | $0.00 - $2.76 |
| Retention | 31 days free | $0.10/GB/day | $0.00 |
| **Subtotal** | | | **$0.00 - $5.00** |

*Dev environments typically ingest 1-2 GB/month. The 5 GB free tier covers most dev workloads. 90-day retention configured via Bicep `logRetentionDays` parameter.*

### Managed Identity (`devex-orchestrator-dev-id`)

No cost. User-assigned managed identities are free. RBAC role assignments are free.

---

## Environment Comparison

| Resource | Dev | Staging | Prod |
|----------|-----|---------|------|
| Container App | $0-18 | $15-40 | $50-200 |
| Container Registry | $5 (Basic) | $10 (Standard) | $50 (Premium) |
| Key Vault | $0.03 | $0.10 | $3.00 |
| Log Analytics | $0-5 | $5-15 | $15-50 |
| Managed Identity | $0 | $0 | $0 |
| **Total** | **$8-28** | **$30-65** | **$118-303** |

---

## Cost Optimization Controls

| Control | Implementation | Savings |
|---------|---------------|---------|
| Scale-to-zero | Container Apps Consumption plan | 100% during idle |
| Free tier usage | Log Analytics 5 GB, Container Apps 2M requests | ~$10/mo |
| Basic ACR | Sufficient for dev/staging | $45/mo vs Premium |
| No HSM keys | Standard Key Vault, not Premium | $1/key/mo |
| Single replica | Dev runs min 0, max 1 | No idle compute |
| Consumption plan | No reserved capacity | Pay only for usage |

### WAF Cost Optimization Pillar Alignment

- **CO-01**: Right-sized resources (Consumption plan, Basic ACR)
- **CO-02**: Scale-to-zero eliminates idle costs
- **CO-03**: Free tier maximized across services
- **CO-04**: No over-provisioned capacity

---

## Pricing Notes

1. All prices are **East US 2** region, USD, as of 2025
2. Container Apps Consumption pricing: vCPU-seconds + GiB-seconds + requests
3. First 180,000 vCPU-seconds and 360,000 GiB-seconds per month are **free**
4. Managed Identity and RBAC assignments have **zero cost**
5. Production estimates assume 10K DAU with 50 requests/user/day
6. Actual costs depend on traffic patterns; monitor via Azure Cost Management

---

*Cost estimates based on Azure pricing calculator and actual dev usage patterns*
*All resources tagged with `costCenter: IT-50100` for billing allocation*
