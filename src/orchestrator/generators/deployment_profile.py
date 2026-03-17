"""Deployment Profile & SKU Selector -- environment-aware resource sizing.

Replaces hardcoded SKU selections with a structured system that maps
(environment, workload_class) → concrete Azure SKUs and pricing.

Components:
- WorkloadClass: enum classifying workload intensity
- DeploymentProfile: frozen dataclass with all SKU selections for a deployment
- SKUSelector: deterministic SKU selection based on environment + workload
- PricingCatalog: structured pricing data separated from deployment logic
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from src.orchestrator.intent_schema import ComputeTarget, DataStore, IntentSpec


class WorkloadClass(str, Enum):
    """Workload intensity classification."""
    DEV = "dev"
    STAGING = "staging"
    PRODUCTION_LOW = "production_low"
    PRODUCTION_HIGH = "production_high"


@dataclass(frozen=True)
class SKUSpec:
    """A single resource SKU selection with pricing."""
    resource: str
    sku_name: str
    tier: str
    monthly_usd: float
    notes: str = ""


@dataclass(frozen=True)
class DeploymentProfile:
    """Complete set of SKU selections for a deployment environment."""
    environment: str
    workload_class: WorkloadClass
    compute: SKUSpec
    log_analytics: SKUSpec
    key_vault: SKUSpec
    identity: SKUSpec
    registry: SKUSpec | None
    data_stores: list[SKUSpec]
    ai_services: list[SKUSpec]

    @property
    def total_monthly(self) -> float:
        total = self.compute.monthly_usd + self.log_analytics.monthly_usd
        total += self.key_vault.monthly_usd + self.identity.monthly_usd
        if self.registry:
            total += self.registry.monthly_usd
        total += sum(ds.monthly_usd for ds in self.data_stores)
        total += sum(ai.monthly_usd for ai in self.ai_services)
        return total

    @property
    def all_items(self) -> list[SKUSpec]:
        items = [self.compute, self.log_analytics, self.key_vault, self.identity]
        if self.registry:
            items.append(self.registry)
        items.extend(self.data_stores)
        items.extend(self.ai_services)
        return items


# ── Pricing Catalog ──────────────────────────────────────────────────
# Structured pricing tables keyed by (resource_type, environment_tier).

_COMPUTE_SKUS: dict[tuple[ComputeTarget, WorkloadClass], SKUSpec] = {
    # Container Apps
    (ComputeTarget.CONTAINER_APPS, WorkloadClass.DEV): SKUSpec(
        "Container App", "Consumption", "dev", 30.00, "0.5 vCPU / 1 GiB, min replica"
    ),
    (ComputeTarget.CONTAINER_APPS, WorkloadClass.STAGING): SKUSpec(
        "Container App", "Consumption", "staging", 60.00, "1 vCPU / 2 GiB, 2 replicas"
    ),
    (ComputeTarget.CONTAINER_APPS, WorkloadClass.PRODUCTION_LOW): SKUSpec(
        "Container App", "Dedicated-D4", "prod", 120.00, "2 vCPU / 4 GiB, 2-10 replicas"
    ),
    (ComputeTarget.CONTAINER_APPS, WorkloadClass.PRODUCTION_HIGH): SKUSpec(
        "Container App", "Dedicated-D8", "prod", 240.00, "4 vCPU / 8 GiB, 3-20 replicas"
    ),
    # App Service
    (ComputeTarget.APP_SERVICE, WorkloadClass.DEV): SKUSpec(
        "App Service Plan", "B1", "dev", 13.14, "Basic B1 Linux"
    ),
    (ComputeTarget.APP_SERVICE, WorkloadClass.STAGING): SKUSpec(
        "App Service Plan", "S1", "staging", 69.35, "Standard S1, autoscale"
    ),
    (ComputeTarget.APP_SERVICE, WorkloadClass.PRODUCTION_LOW): SKUSpec(
        "App Service Plan", "P1v3", "prod", 138.70, "Premium v3 P1"
    ),
    (ComputeTarget.APP_SERVICE, WorkloadClass.PRODUCTION_HIGH): SKUSpec(
        "App Service Plan", "P2v3", "prod", 277.40, "Premium v3 P2, zone redundant"
    ),
    # Functions
    (ComputeTarget.FUNCTIONS, WorkloadClass.DEV): SKUSpec(
        "Function App", "Consumption", "dev", 0.00, "1M free executions/mo"
    ),
    (ComputeTarget.FUNCTIONS, WorkloadClass.STAGING): SKUSpec(
        "Function App", "Consumption", "staging", 0.00, "Pay-per-execution"
    ),
    (ComputeTarget.FUNCTIONS, WorkloadClass.PRODUCTION_LOW): SKUSpec(
        "Function App", "EP1", "prod", 146.00, "Elastic Premium EP1"
    ),
    (ComputeTarget.FUNCTIONS, WorkloadClass.PRODUCTION_HIGH): SKUSpec(
        "Function App", "EP2", "prod", 292.00, "Elastic Premium EP2"
    ),
}

_DATASTORE_SKUS: dict[tuple[DataStore, WorkloadClass], SKUSpec] = {
    # Blob Storage
    (DataStore.BLOB_STORAGE, WorkloadClass.DEV): SKUSpec(
        "Blob Storage", "Hot LRS", "dev", 2.08, "~100 GB"
    ),
    (DataStore.BLOB_STORAGE, WorkloadClass.STAGING): SKUSpec(
        "Blob Storage", "Hot ZRS", "staging", 4.16, "~500 GB, zone redundant"
    ),
    (DataStore.BLOB_STORAGE, WorkloadClass.PRODUCTION_LOW): SKUSpec(
        "Blob Storage", "Hot GRS", "prod", 8.32, "~1 TB, geo-redundant"
    ),
    (DataStore.BLOB_STORAGE, WorkloadClass.PRODUCTION_HIGH): SKUSpec(
        "Blob Storage", "Hot RA-GRS", "prod", 10.40, "~2 TB, read-access geo"
    ),
    # Cosmos DB
    (DataStore.COSMOS_DB, WorkloadClass.DEV): SKUSpec(
        "Cosmos DB", "Serverless", "dev", 0.25, "Low RU usage"
    ),
    (DataStore.COSMOS_DB, WorkloadClass.STAGING): SKUSpec(
        "Cosmos DB", "Autoscale 400", "staging", 24.00, "400 RU/s autoscale"
    ),
    (DataStore.COSMOS_DB, WorkloadClass.PRODUCTION_LOW): SKUSpec(
        "Cosmos DB", "Autoscale 4000", "prod", 240.00, "4000 RU/s, zone redundant"
    ),
    (DataStore.COSMOS_DB, WorkloadClass.PRODUCTION_HIGH): SKUSpec(
        "Cosmos DB", "Provisioned 10000", "prod", 584.00, "10K RU/s, multi-region"
    ),
    # SQL
    (DataStore.SQL, WorkloadClass.DEV): SKUSpec(
        "Azure SQL", "Basic DTU", "dev", 4.90, "5 DTU"
    ),
    (DataStore.SQL, WorkloadClass.STAGING): SKUSpec(
        "Azure SQL", "S1 Standard", "staging", 30.00, "20 DTU"
    ),
    (DataStore.SQL, WorkloadClass.PRODUCTION_LOW): SKUSpec(
        "Azure SQL", "GP-S Gen5 2vCore", "prod", 110.50, "General Purpose Serverless"
    ),
    (DataStore.SQL, WorkloadClass.PRODUCTION_HIGH): SKUSpec(
        "Azure SQL", "BC Gen5 4vCore", "prod", 460.00, "Business Critical, zone redundant"
    ),
    # Redis
    (DataStore.REDIS, WorkloadClass.DEV): SKUSpec(
        "Redis Cache", "Basic C0", "dev", 16.00, "250 MB"
    ),
    (DataStore.REDIS, WorkloadClass.STAGING): SKUSpec(
        "Redis Cache", "Standard C1", "staging", 40.50, "1 GB, replicated"
    ),
    (DataStore.REDIS, WorkloadClass.PRODUCTION_LOW): SKUSpec(
        "Redis Cache", "Premium P1", "prod", 172.00, "6 GB, clustering"
    ),
    (DataStore.REDIS, WorkloadClass.PRODUCTION_HIGH): SKUSpec(
        "Redis Cache", "Premium P3", "prod", 688.00, "26 GB, cluster, zone redundant"
    ),
}

_CORE_INFRA: dict[str, dict[WorkloadClass, SKUSpec]] = {
    "log_analytics": {
        WorkloadClass.DEV: SKUSpec("Log Analytics", "Pay-per-GB", "dev", 2.76, "~1 GB/mo ingest"),
        WorkloadClass.STAGING: SKUSpec("Log Analytics", "Pay-per-GB", "staging", 6.90, "~3 GB/mo ingest"),
        WorkloadClass.PRODUCTION_LOW: SKUSpec("Log Analytics", "Pay-per-GB", "prod", 13.80, "~5 GB/mo ingest"),
        WorkloadClass.PRODUCTION_HIGH: SKUSpec("Log Analytics", "Commitment 100", "prod", 76.50, "100 GB/day commitment"),
    },
    "key_vault": {
        WorkloadClass.DEV: SKUSpec("Key Vault", "Standard", "dev", 0.03, "Low operations"),
        WorkloadClass.STAGING: SKUSpec("Key Vault", "Standard", "staging", 0.03, ""),
        WorkloadClass.PRODUCTION_LOW: SKUSpec("Key Vault", "Standard", "prod", 0.30, "Moderate operations"),
        WorkloadClass.PRODUCTION_HIGH: SKUSpec("Key Vault", "Premium HSM", "prod", 3.00, "HSM-backed keys"),
    },
    "identity": {
        WorkloadClass.DEV: SKUSpec("Managed Identity", "Free", "dev", 0.00, ""),
        WorkloadClass.STAGING: SKUSpec("Managed Identity", "Free", "staging", 0.00, ""),
        WorkloadClass.PRODUCTION_LOW: SKUSpec("Managed Identity", "Free", "prod", 0.00, ""),
        WorkloadClass.PRODUCTION_HIGH: SKUSpec("Managed Identity", "Free", "prod", 0.00, ""),
    },
    "registry": {
        WorkloadClass.DEV: SKUSpec("Container Registry", "Basic", "dev", 5.00, "10 GB"),
        WorkloadClass.STAGING: SKUSpec("Container Registry", "Standard", "staging", 10.00, "100 GB"),
        WorkloadClass.PRODUCTION_LOW: SKUSpec("Container Registry", "Premium", "prod", 50.00, "500 GB, geo-replication"),
        WorkloadClass.PRODUCTION_HIGH: SKUSpec("Container Registry", "Premium", "prod", 50.00, "500 GB, geo-replication"),
    },
}


class SKUSelector:
    """Deterministic SKU selection based on environment and workload classification."""

    @staticmethod
    def classify_workload(spec: IntentSpec) -> WorkloadClass:
        """Classify workload intensity from the intent spec."""
        env = spec.environment.lower()
        if env == "dev":
            return WorkloadClass.DEV
        if env == "staging":
            return WorkloadClass.STAGING

        # Production: classify based on entity count, data stores, AI usage
        entity_count = len(spec.entities)
        ds_count = len(spec.data_stores)
        if spec.uses_ai or entity_count > 8 or ds_count > 3:
            return WorkloadClass.PRODUCTION_HIGH
        return WorkloadClass.PRODUCTION_LOW

    @staticmethod
    def select(spec: IntentSpec) -> DeploymentProfile:
        """Build a complete DeploymentProfile from the intent spec."""
        wc = SKUSelector.classify_workload(spec)
        compute_target = getattr(spec, "compute_target", ComputeTarget.CONTAINER_APPS)

        # Compute
        compute = _COMPUTE_SKUS.get(
            (compute_target, wc),
            _COMPUTE_SKUS[(ComputeTarget.CONTAINER_APPS, WorkloadClass.DEV)],
        )

        # Core infra
        log_analytics = _CORE_INFRA["log_analytics"][wc]
        key_vault = _CORE_INFRA["key_vault"][wc]
        identity = _CORE_INFRA["identity"][wc]

        # Registry (only for container-based compute)
        registry = None
        if compute_target in (ComputeTarget.CONTAINER_APPS, ComputeTarget.APP_SERVICE):
            registry = _CORE_INFRA["registry"][wc]

        # Data stores
        data_stores = []
        for ds in spec.data_stores:
            if ds == DataStore.NONE:
                continue
            key = (ds, wc)
            if key in _DATASTORE_SKUS:
                data_stores.append(_DATASTORE_SKUS[key])
            else:
                # Fallback for stores without tiered pricing (table, ai_search)
                data_stores.append(SKUSpec(ds.value, "Standard", wc.value, 5.00, ""))

        # AI services
        ai_services: list[SKUSpec] = []
        if spec.uses_ai:
            if wc in (WorkloadClass.DEV, WorkloadClass.STAGING):
                ai_services.append(SKUSpec("Azure OpenAI", "S0", wc.value, 0.00, "Pay-per-token"))
            else:
                ai_services.append(SKUSpec("Azure OpenAI", "S0 PTU", wc.value, 0.00, "Provisioned throughput"))
            if DataStore.AI_SEARCH in spec.data_stores:
                if wc == WorkloadClass.DEV:
                    ai_services.append(SKUSpec("AI Search", "Free", "dev", 0.00, "50 MB, 3 indexes"))
                elif wc == WorkloadClass.STAGING:
                    ai_services.append(SKUSpec("AI Search", "Basic", "staging", 75.00, "2 GB, 15 indexes"))
                else:
                    ai_services.append(SKUSpec("AI Search", "S1", "prod", 250.00, "25 GB, scaled"))

        return DeploymentProfile(
            environment=spec.environment,
            workload_class=wc,
            compute=compute,
            log_analytics=log_analytics,
            key_vault=key_vault,
            identity=identity,
            registry=registry,
            data_stores=data_stores,
            ai_services=ai_services,
        )


def profile_to_markdown(profile: DeploymentProfile) -> str:
    """Render a DeploymentProfile as a cost-estimate markdown table."""
    lines = [
        "# Estimated Monthly Cost",
        "",
        f"> Environment: **{profile.environment}** | Workload: **{profile.workload_class.value}**",
        "",
        "> These are **approximate baseline** costs. Actual costs vary with usage, region, and reserved pricing.",
        "",
        "| Resource | SKU / Tier | Est. Monthly (USD) | Notes |",
        "|----------|-----------|--------------------:|-------|",
    ]
    for item in profile.all_items:
        lines.append(f"| {item.resource} | {item.sku_name} | ${item.monthly_usd:,.2f} | {item.notes} |")
    lines.append(f"| **Total** | | **${profile.total_monthly:,.2f}** | |")
    lines.append("")
    lines.append(
        "*Prices are approximate USD baseline for East US. "
        "Use the [Azure Pricing Calculator](https://azure.microsoft.com/pricing/calculator/) "
        "for detailed estimates.*"
    )
    return "\n".join(lines)
