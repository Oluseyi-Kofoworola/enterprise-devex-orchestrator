# Enterprise Standards -- SLHS Voice Agent v3.0

> **Azure Cloud Adoption Framework (CAF)** naming conventions and enterprise tagging
> Enforced by the Enterprise Standards Engine

---

## Naming Conventions (Azure CAF)

### Resource Names (Deployed)

| Resource Type | Prefix | Name | Convention |
|--------------|--------|------|-----------|
| Resource Group | `rg-` | `rg-enterprise-devex-orchestrator-dev` | `rg-<project>-<env>` |
| Log Analytics | `-law` | `devex-orchestrator-dev-law` | `<project>-<env>-law` |
| Managed Identity | `-id` | `devex-orchestrator-dev-id` | `<project>-<env>-id` |
| Key Vault | `kv` | `devexorchestratordevkv` | `<project><env>kv` (no hyphens) |
| Container Registry | `acr` | `devexorchestratordevacr` | `<project><env>acr` (no hyphens) |
| Container App | -- | `devex-orchestrator-dev` | `<project>-<env>` |
| Container App Env | `-env` | `devex-orchestrator-dev-env` | `<project>-<env>-env` |

### Naming Rules

| Rule | Constraint |
|------|-----------|
| Allowed characters | Lowercase alphanumeric + hyphens (except Key Vault & ACR: no hyphens) |
| Max length | Resource-specific (Key Vault: 24, ACR: 50, others: 63) |
| No trailing hyphens | Names must not end with `-` |
| No consecutive hyphens | `--` is not allowed |
| Environment suffix | `-dev`, `-staging`, `-prod` |

### Supported Resource Types (20)

| Type | Prefix/Suffix | Example |
|------|--------------|---------|
| Resource Group | `rg-` | `rg-myapp-dev` |
| Storage Account | `st` | `stmyappdev` |
| Key Vault | `kv` | `myappdevkv` |
| Container Registry | `acr` | `myappdevacr` |
| Container App | -- | `myapp-dev` |
| Container App Env | `-env` | `myapp-dev-env` |
| App Service Plan | `plan-` | `plan-myapp-dev` |
| App Service | `app-` | `app-myapp-dev` |
| Function App | `func-` | `func-myapp-dev` |
| Cosmos DB | `cosmos-` | `cosmos-myapp-dev` |
| SQL Server | `sql-` | `sql-myapp-dev` |
| SQL Database | `sqldb-` | `sqldb-myapp-dev` |
| Redis Cache | `redis-` | `redis-myapp-dev` |
| Log Analytics | `-law` | `myapp-dev-law` |
| Managed Identity | `-id` | `myapp-dev-id` |
| Virtual Network | `vnet-` | `vnet-myapp-dev` |
| Subnet | `snet-` | `snet-myapp-dev` |
| NSG | `nsg-` | `nsg-myapp-dev` |
| Public IP | `pip-` | `pip-myapp-dev` |
| Load Balancer | `lb-` | `lb-myapp-dev` |

### Region Abbreviations (34)

| Region | Abbreviation |
|--------|-------------|
| eastus | eus |
| eastus2 | eus2 |
| westus | wus |
| westus2 | wus2 |
| westus3 | wus3 |
| centralus | cus |
| northcentralus | ncus |
| southcentralus | scus |
| westcentralus | wcus |
| canadacentral | cac |
| canadaeast | cae |
| brazilsouth | brs |
| northeurope | neu |
| westeurope | weu |
| uksouth | uks |
| ukwest | ukw |
| francecentral | frc |
| francesouth | frs |
| germanywestcentral | gwc |
| norwayeast | noe |
| swedencentral | swc |
| switzerlandnorth | szn |
| eastasia | ea |
| southeastasia | sea |
| japaneast | jpe |
| japanwest | jpw |
| koreacentral | krc |
| koreasouth | krs |
| australiaeast | aue |
| australiasoutheast | ause |
| centralindia | cin |
| southindia | sin |
| westindia | win |
| southafricanorth | san |

---

## Tagging Standard

### Required Tags (7)

| Tag | Description | Validation | Example |
|-----|-------------|-----------|---------|
| `project` | Project identifier | `^[a-z][a-z0-9-]{1,62}$` | `devex-orchestrator` |
| `environment` | Deployment stage | `^(dev\|staging\|prod)$` | `dev` |
| `managedBy` | IaC tool | `^(bicep\|terraform\|pulumi\|manual)$` | `bicep` |
| `owner` | Team or individual | Non-empty string | `platform-team` |
| `costCenter` | Billing allocation | `^[A-Z]{2}-[0-9]{4,6}$` | `IT-50100` |
| `dataClassification` | Data sensitivity | `^(public\|internal\|confidential\|restricted)$` | `confidential` |
| `generator` | Scaffold generator | Non-empty string | `enterprise-devex-orchestrator` |

### Optional Tags (5)

| Tag | Description | Validation | Example |
|-----|-------------|-----------|---------|
| `workload` | Workload type | Non-empty string | `voice-agent` |
| `compliance` | Compliance framework | Non-empty string | `HIPAA` |
| `sla` | Service level target | `^[0-9]{2,3}(\.[0-9]{1,2})?%$` | `99.9%` |
| `dr` | Disaster recovery tier | `^(tier[1-4]\|none)$` | `tier2` |
| `expiresOn` | Resource expiry | `^[0-9]{4}-[0-9]{2}-[0-9]{2}$` | `2026-12-31` |

### Tags Applied to SLHS Voice Agent

```json
{
  "project": "devex-orchestrator",
  "environment": "dev",
  "managedBy": "bicep",
  "generator": "enterprise-devex-orchestrator",
  "dataClassification": "confidential",
  "workload": "voice-agent",
  "compliance": "HIPAA"
}
```

---

## Standards Engine Components

| Component | Module | Purpose |
|-----------|--------|---------|
| NamingEngine | `src/orchestrator/standards/` | 20 resource types, 34 region abbreviations |
| TaggingEngine | `src/orchestrator/standards/` | 7 required + 5 optional tags, regex validation |
| EnterpriseStandardsConfig | `standards.yaml` | YAML-driven config for all standards |

### Standards Validation (67 Tests)

```powershell
# Run standards tests
pytest tests/test_standards.py -v

# 67 tests covering:
# - Resource naming for all 20 types
# - Region abbreviation mapping
# - Tag validation (required + optional)
# - Tag regex pattern enforcement
# - Config loading and defaults
```

---

*Enterprise Standards Engine | Azure CAF Aligned*
*Automated naming + tagging enforcement across all generated resources*


