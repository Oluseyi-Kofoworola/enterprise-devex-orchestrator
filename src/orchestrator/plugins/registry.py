"""Unified Plugin Registry -- collects and manages all plugin categories.

Each category has its own typed registry.  ``create_default_plugins()``
pre-loads all built-in plugins so the generators can query them immediately.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.orchestrator.intent_schema import IntentSpec
from src.orchestrator.logging import get_logger

logger = get_logger(__name__)


@dataclass
class PluginEntry:
    """Metadata for a single registered plugin."""

    name: str
    plugin: Any
    priority: int = 100
    enabled: bool = True


class TypedPluginRegistry:
    """Generic typed registry for a single plugin category."""

    def __init__(self, category: str) -> None:
        self._category = category
        self._plugins: list[PluginEntry] = []

    @property
    def category(self) -> str:
        return self._category

    def register(self, name: str, plugin: Any, priority: int = 100) -> None:
        self._plugins.append(PluginEntry(name=name, plugin=plugin, priority=priority))
        logger.info("plugin.registered", category=self._category, name=name, priority=priority)

    def unregister(self, name: str) -> bool:
        before = len(self._plugins)
        self._plugins = [p for p in self._plugins if p.name != name]
        return len(self._plugins) < before

    def get(self, name: str) -> Any | None:
        for p in self._plugins:
            if p.name == name and p.enabled:
                return p.plugin
        return None

    @property
    def names(self) -> list[str]:
        return [p.name for p in sorted(self._plugins, key=lambda p: p.priority) if p.enabled]

    def all_plugins(self) -> list[Any]:
        return [p.plugin for p in sorted(self._plugins, key=lambda p: p.priority) if p.enabled]

    def generate_all(self, spec: IntentSpec, **kwargs: Any) -> dict[str, str]:
        """Execute all plugins in priority order, merging file outputs."""
        files: dict[str, str] = {}
        for entry in sorted(self._plugins, key=lambda p: p.priority):
            if not entry.enabled:
                continue
            if hasattr(entry.plugin, "applies_to") and not entry.plugin.applies_to(spec):
                continue
            result = entry.plugin.generate(spec, **kwargs)
            files.update(result)
        return files

    def collect_all(self, spec: IntentSpec, **kwargs: Any) -> list[Any]:
        """Collect non-file outputs (policies, rules) from all plugins."""
        items: list[Any] = []
        for entry in sorted(self._plugins, key=lambda p: p.priority):
            if not entry.enabled:
                continue
            if hasattr(entry.plugin, "applies_to") and not entry.plugin.applies_to(spec):
                continue
            result = entry.plugin.collect(spec, **kwargs)
            items.extend(result)
        return items

    def __len__(self) -> int:
        return len([p for p in self._plugins if p.enabled])

    def __contains__(self, name: str) -> bool:
        return any(p.name == name for p in self._plugins)


@dataclass
class PluginRegistry:
    """Central registry holding all 7 plugin categories."""

    resource: TypedPluginRegistry = field(default_factory=lambda: TypedPluginRegistry("resource"))
    route: TypedPluginRegistry = field(default_factory=lambda: TypedPluginRegistry("route"))
    dashboard: TypedPluginRegistry = field(default_factory=lambda: TypedPluginRegistry("dashboard"))
    cicd: TypedPluginRegistry = field(default_factory=lambda: TypedPluginRegistry("cicd"))
    governance: TypedPluginRegistry = field(default_factory=lambda: TypedPluginRegistry("governance"))
    security: TypedPluginRegistry = field(default_factory=lambda: TypedPluginRegistry("security"))
    docs: TypedPluginRegistry = field(default_factory=lambda: TypedPluginRegistry("docs"))

    @property
    def all_categories(self) -> dict[str, TypedPluginRegistry]:
        return {
            "resource": self.resource,
            "route": self.route,
            "dashboard": self.dashboard,
            "cicd": self.cicd,
            "governance": self.governance,
            "security": self.security,
            "docs": self.docs,
        }

    @property
    def total_plugins(self) -> int:
        return sum(len(r) for r in self.all_categories.values())

    def summary(self) -> dict[str, int]:
        return {name: len(reg) for name, reg in self.all_categories.items()}


def create_default_plugins() -> PluginRegistry:
    """Build a PluginRegistry pre-loaded with all built-in plugins."""
    from src.orchestrator.plugins.resource_plugin import (
        ServiceBusPlugin,
        EventGridPlugin,
        FrontDoorPlugin,
    )
    from src.orchestrator.plugins.route_plugin import (
        HealthRoutePlugin,
        WebhookRoutePlugin,
        BulkOperationRoutePlugin,
    )
    from src.orchestrator.plugins.dashboard_plugin import (
        StatusDistributionWidget,
        TimelineWidget,
        MetricCardWidget,
    )
    from src.orchestrator.plugins.cicd_plugin import (
        LoadTestStagePlugin,
        CanaryDeployStagePlugin,
        SmokeTestStagePlugin,
    )
    from src.orchestrator.plugins.governance_plugin import (
        DataResidencyPolicy,
        CostBudgetPolicy,
        TagCompliancePolicy,
    )
    from src.orchestrator.plugins.security_plugin import (
        WAFRulesPlugin,
        DDoSProtectionPlugin,
        NetworkIsolationPlugin,
    )
    from src.orchestrator.plugins.docs_plugin import (
        RunbookDocPlugin,
        APIReferenceDocPlugin,
        ComplianceEvidenceDocPlugin,
    )

    registry = PluginRegistry()

    # -- Resource plugins (custom Bicep modules) -------------------------
    registry.resource.register("service-bus", ServiceBusPlugin(), priority=10)
    registry.resource.register("event-grid", EventGridPlugin(), priority=20)
    registry.resource.register("front-door", FrontDoorPlugin(), priority=30)

    # -- Route plugins (custom API patterns) -----------------------------
    registry.route.register("health", HealthRoutePlugin(), priority=10)
    registry.route.register("webhook", WebhookRoutePlugin(), priority=20)
    registry.route.register("bulk-ops", BulkOperationRoutePlugin(), priority=30)

    # -- Dashboard plugins (React widgets) -------------------------------
    registry.dashboard.register("status-distribution", StatusDistributionWidget(), priority=10)
    registry.dashboard.register("timeline", TimelineWidget(), priority=20)
    registry.dashboard.register("metric-card", MetricCardWidget(), priority=30)

    # -- CI/CD plugins (pipeline stages) ---------------------------------
    registry.cicd.register("load-test", LoadTestStagePlugin(), priority=10)
    registry.cicd.register("canary-deploy", CanaryDeployStagePlugin(), priority=20)
    registry.cicd.register("smoke-test", SmokeTestStagePlugin(), priority=30)

    # -- Governance plugins (compliance rules) ---------------------------
    registry.governance.register("data-residency", DataResidencyPolicy(), priority=10)
    registry.governance.register("cost-budget", CostBudgetPolicy(), priority=20)
    registry.governance.register("tag-compliance", TagCompliancePolicy(), priority=30)

    # -- Security plugins (WAF, DDoS, network) ---------------------------
    registry.security.register("waf-rules", WAFRulesPlugin(), priority=10)
    registry.security.register("ddos-protection", DDoSProtectionPlugin(), priority=20)
    registry.security.register("network-isolation", NetworkIsolationPlugin(), priority=30)

    # -- Docs plugins (custom doc sections) ------------------------------
    registry.docs.register("runbook", RunbookDocPlugin(), priority=10)
    registry.docs.register("api-reference", APIReferenceDocPlugin(), priority=20)
    registry.docs.register("compliance-evidence", ComplianceEvidenceDocPlugin(), priority=30)

    return registry
