"""Cost Estimator -- provides Azure monthly cost estimates.

Produces a cost breakdown for each Azure resource in the architecture plan.
Delegates SKU selection to the DeploymentProfile/SKUSelector system for
environment-aware, workload-classified resource sizing.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.orchestrator.generators.deployment_profile import (
    DeploymentProfile,
    SKUSelector,
    profile_to_markdown,
)
from src.orchestrator.intent_schema import ComputeTarget, DataStore, IntentSpec, PlanOutput
from src.orchestrator.logging import get_logger

logger = get_logger(__name__)


# -- Baseline monthly pricing (USD, lowest tier, dev workload) -------
# Kept for backward compatibility; new code uses DeploymentProfile.
_BASELINE_PRICES: dict[str, dict[str, float]] = {
    "container_apps": {
        "compute": 30.0,
        "environment": 0.0,
    },
    "app_service": {
        "B1_plan": 13.14,
        "B2_plan": 26.28,
        "S1_plan": 69.35,
    },
    "functions": {
        "consumption": 0.0,
        "premium_EP1": 146.00,
    },
    "log_analytics": {
        "workspace": 2.76,
    },
    "managed_identity": {
        "identity": 0.0,
    },
    "keyvault": {
        "standard": 0.03,
    },
    "container_registry": {
        "standard": 5.00,
    },
    "blob_storage": {
        "hot_lrs": 2.08,
    },
    "cosmos_db": {
        "serverless": 0.25,
    },
    "sql": {
        "basic": 4.90,
    },
    "redis": {
        "basic_C0": 16.00,
    },
}


@dataclass
class CostLineItem:
    """A single line item in the cost estimate."""

    resource: str
    sku: str
    monthly_usd: float
    notes: str = ""


@dataclass
class CostEstimate:
    """Aggregate cost estimate for the full architecture."""

    items: list[CostLineItem] = field(default_factory=list)

    @property
    def total_monthly(self) -> float:
        return sum(item.monthly_usd for item in self.items)

    def to_markdown(self) -> str:
        lines = [
            "# Estimated Monthly Cost",
            "",
            "> These are **approximate baseline** costs for a dev-tier workload.",
            "> Actual costs vary with usage, region, and reserved pricing.",
            "",
            "| Resource | SKU / Tier | Est. Monthly (USD) | Notes |",
            "|----------|-----------|--------------------:|-------|",
        ]
        for item in self.items:
            lines.append(f"| {item.resource} | {item.sku} | ${item.monthly_usd:,.2f} | {item.notes} |")
        lines.append(f"| **Total** | | **${self.total_monthly:,.2f}** | |")
        lines.append("")
        lines.append(
            "*Prices are approximate USD baseline for East US. "
            "Use the [Azure Pricing Calculator](https://azure.microsoft.com/pricing/calculator/) "
            "for detailed estimates.*"
        )
        return "\n".join(lines)


class CostEstimator:
    """Estimates monthly Azure cost for a given IntentSpec and PlanOutput.

    Uses the DeploymentProfile/SKUSelector system for environment-aware
    SKU selection and pricing.
    """

    def estimate(self, spec: IntentSpec, plan: PlanOutput) -> CostEstimate:
        logger.info("cost_estimator.start", project=spec.project_name)

        profile = SKUSelector.select(spec)
        items: list[CostLineItem] = []
        for sku in profile.all_items:
            items.append(CostLineItem(sku.resource, sku.sku_name, sku.monthly_usd, sku.notes))

        logger.info("cost_estimator.complete", total=sum(i.monthly_usd for i in items))
        return CostEstimate(items=items)

    def estimate_with_profile(self, spec: IntentSpec) -> tuple[CostEstimate, DeploymentProfile]:
        """Return both the cost estimate and the full deployment profile."""
        profile = SKUSelector.select(spec)
        items = [CostLineItem(s.resource, s.sku_name, s.monthly_usd, s.notes) for s in profile.all_items]
        return CostEstimate(items=items), profile

    @staticmethod
    def profile_markdown(spec: IntentSpec) -> str:
        """Generate a cost markdown using the deployment profile system."""
        profile = SKUSelector.select(spec)
        return profile_to_markdown(profile)
