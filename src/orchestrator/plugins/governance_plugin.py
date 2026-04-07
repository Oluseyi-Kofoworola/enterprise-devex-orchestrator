"""Governance Plugins -- organisation-specific compliance rules.

Each plugin exposes ``collect(spec)`` returning policy-rule-like objects
that the GovernanceReviewer can evaluate alongside built-in policies.
They also expose ``generate(spec)`` for optional documentation output.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.orchestrator.intent_schema import IntentSpec
from src.orchestrator.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class PluginPolicyRule:
    """Lightweight policy rule produced by governance plugins."""

    id: str
    name: str
    description: str
    severity: str  # ERROR, WARNING, INFO
    category: str
    remediation: str

    def check(self, spec: IntentSpec) -> bool:
        """Return True if the spec violates this rule."""
        return False  # overridden by individual plugins


class DataResidencyPolicy:
    """Enforces data residency constraints (region allow-lists)."""

    ALLOWED_REGIONS = {
        "HIPAA_GUIDANCE": {"eastus", "eastus2", "westus2", "centralus", "southcentralus"},
        "GDPR": {"westeurope", "northeurope", "francecentral", "germanywestcentral"},
        "FEDRAMP_GUIDANCE": {"usgovvirginia", "usgovarizona", "usdodeast", "usdodcentral"},
    }

    def applies_to(self, spec: IntentSpec) -> bool:
        framework = spec.security.compliance_framework.value.upper()
        return framework in self.ALLOWED_REGIONS

    def collect(self, spec: IntentSpec, **kwargs: Any) -> list[PluginPolicyRule]:
        framework = spec.security.compliance_framework.value.upper()
        allowed = self.ALLOWED_REGIONS.get(framework, set())
        rules = []
        if spec.azure_region not in allowed:
            rules.append(
                PluginPolicyRule(
                    id="PLUGIN-GOV-001",
                    name="data-residency-violation",
                    description=(
                        f"Region '{spec.azure_region}' is not approved for "
                        f"{framework} data residency. "
                        f"Allowed: {', '.join(sorted(allowed))}"
                    ),
                    severity="ERROR",
                    category="compliance",
                    remediation=f"Change region to one of: {', '.join(sorted(allowed))}",
                )
            )
        return rules

    def generate(self, spec: IntentSpec, **kwargs: Any) -> dict[str, str]:
        framework = spec.security.compliance_framework.value.upper()
        allowed = self.ALLOWED_REGIONS.get(framework, set())
        status = "COMPLIANT" if spec.azure_region in allowed else "NON-COMPLIANT"
        return {
            "docs/data-residency.md": f"""\
# Data Residency Report

| Field | Value |
|-------|-------|
| Compliance Framework | {framework} |
| Configured Region | {spec.azure_region} |
| Status | **{status}** |
| Allowed Regions | {', '.join(sorted(allowed)) if allowed else 'N/A'} |
""",
        }


class CostBudgetPolicy:
    """Enforces cost-awareness by flagging expensive SKU tiers in non-prod."""

    EXPENSIVE_KEYWORDS = {"premium", "enterprise", "dedicated", "isolated"}

    def applies_to(self, spec: IntentSpec) -> bool:
        return spec.environment in ("dev", "staging")

    def collect(self, spec: IntentSpec, **kwargs: Any) -> list[PluginPolicyRule]:
        rules: list[PluginPolicyRule] = []
        raw = spec.raw_intent.lower()
        for kw in self.EXPENSIVE_KEYWORDS:
            if kw in raw:
                rules.append(
                    PluginPolicyRule(
                        id="PLUGIN-GOV-002",
                        name="cost-budget-warning",
                        description=(
                            f"Intent mentions '{kw}' tier in '{spec.environment}' "
                            f"environment. Consider using Standard/Basic for non-prod."
                        ),
                        severity="WARNING",
                        category="cost",
                        remediation=f"Remove or downgrade '{kw}' tier for {spec.environment} environment.",
                    )
                )
        return rules

    def generate(self, spec: IntentSpec, **kwargs: Any) -> dict[str, str]:
        return {}


class TagCompliancePolicy:
    """Enforces enterprise tagging standards on generated resources."""

    REQUIRED_TAGS = ["project", "environment", "managedBy", "dataSensitivity", "owner"]

    def applies_to(self, spec: IntentSpec) -> bool:
        return True

    def collect(self, spec: IntentSpec, **kwargs: Any) -> list[PluginPolicyRule]:
        missing = [t for t in self.REQUIRED_TAGS if not self._tag_present(t, spec)]
        rules: list[PluginPolicyRule] = []
        if missing:
            rules.append(
                PluginPolicyRule(
                    id="PLUGIN-GOV-003",
                    name="tag-compliance-gap",
                    description=(
                        f"Required enterprise tags may be missing: {', '.join(missing)}. "
                        f"Ensure all Bicep resources include these tags."
                    ),
                    severity="WARNING",
                    category="standards",
                    remediation=f"Add missing tags to all resource declarations: {', '.join(missing)}",
                )
            )
        return rules

    def generate(self, spec: IntentSpec, **kwargs: Any) -> dict[str, str]:
        return {}

    @staticmethod
    def _tag_present(tag: str, spec: IntentSpec) -> bool:
        """Heuristic: check if tag value can be derived from spec."""
        mapping = {
            "project": spec.project_name,
            "environment": spec.environment,
            "managedBy": "bicep",
            "dataSensitivity": spec.security.data_classification,
            "owner": "",  # may not always be present
        }
        return bool(mapping.get(tag, ""))
