"""Tests for the Plugin System -- registry, all 7 plugin categories."""

from __future__ import annotations

import pytest

from src.orchestrator.intent_schema import (
    AppType,
    AuthModel,
    CICDRequirements,
    ComplianceFramework,
    DataStore,
    EntitySpec,
    FieldSpec,
    IntentSpec,
    NetworkingModel,
    ObservabilityRequirements,
    SecurityRequirements,
)
from src.orchestrator.plugins.registry import (
    PluginEntry,
    PluginRegistry,
    TypedPluginRegistry,
    create_default_plugins,
)
from src.orchestrator.plugins.resource_plugin import (
    EventGridPlugin,
    FrontDoorPlugin,
    ServiceBusPlugin,
)
from src.orchestrator.plugins.route_plugin import (
    BulkOperationRoutePlugin,
    HealthRoutePlugin,
    WebhookRoutePlugin,
)
from src.orchestrator.plugins.dashboard_plugin import (
    MetricCardWidget,
    StatusDistributionWidget,
    TimelineWidget,
)
from src.orchestrator.plugins.cicd_plugin import (
    CanaryDeployStagePlugin,
    LoadTestStagePlugin,
    SmokeTestStagePlugin,
)
from src.orchestrator.plugins.governance_plugin import (
    CostBudgetPolicy,
    DataResidencyPolicy,
    PluginPolicyRule,
    TagCompliancePolicy,
)
from src.orchestrator.plugins.security_plugin import (
    DDoSProtectionPlugin,
    NetworkIsolationPlugin,
    WAFRulesPlugin,
)
from src.orchestrator.plugins.docs_plugin import (
    APIReferenceDocPlugin,
    ComplianceEvidenceDocPlugin,
    RunbookDocPlugin,
)


# -- Fixtures ---------------------------------------------------------------


def _make_spec(**overrides) -> IntentSpec:
    defaults = dict(
        project_name="test-project",
        app_type=AppType.API,
        description="A test API service",
        raw_intent="Build a test API with event-driven messaging and webhook support",
        data_stores=[DataStore.COSMOS_DB, DataStore.REDIS],
        security=SecurityRequirements(
            auth_model=AuthModel.MANAGED_IDENTITY,
            compliance_framework=ComplianceFramework.GENERAL,
            data_classification="internal",
            networking=NetworkingModel.PRIVATE,
            encryption_at_rest=True,
            encryption_in_transit=True,
            secret_management=True,
            enable_waf=True,
        ),
        observability=ObservabilityRequirements(
            log_analytics=True,
            health_endpoint=True,
        ),
        cicd=CICDRequirements(
            oidc_auth=True,
            environments=["dev", "staging"],
        ),
        entities=[
            EntitySpec(
                name="order",
                fields=[
                    FieldSpec(name="id", type="str"),
                    FieldSpec(name="status", type="str"),
                    FieldSpec(name="created_at", type="datetime"),
                    FieldSpec(name="total", type="float"),
                ],
                description="Customer order",
            ),
            EntitySpec(
                name="customer",
                fields=[
                    FieldSpec(name="id", type="str"),
                    FieldSpec(name="name", type="str"),
                    FieldSpec(name="email", type="str"),
                ],
                description="Customer record",
            ),
            EntitySpec(
                name="product",
                fields=[
                    FieldSpec(name="id", type="str"),
                    FieldSpec(name="name", type="str"),
                    FieldSpec(name="price", type="float"),
                ],
                description="Product catalog item",
            ),
        ],
        azure_region="eastus2",
        resource_group_name="rg-test",
        environment="dev",
        confidence=0.85,
    )
    defaults.update(overrides)
    return IntentSpec(**defaults)


# -- TypedPluginRegistry ----------------------------------------------------


class TestTypedPluginRegistry:
    """Core registry mechanics."""

    def test_register_and_get(self) -> None:
        reg = TypedPluginRegistry("test")
        reg.register("alpha", object(), priority=10)
        assert "alpha" in reg
        assert len(reg) == 1

    def test_unregister(self) -> None:
        reg = TypedPluginRegistry("test")
        reg.register("alpha", object())
        assert reg.unregister("alpha")
        assert len(reg) == 0

    def test_unregister_missing(self) -> None:
        reg = TypedPluginRegistry("test")
        assert not reg.unregister("nope")

    def test_priority_order(self) -> None:
        reg = TypedPluginRegistry("test")
        reg.register("b", object(), priority=20)
        reg.register("a", object(), priority=10)
        reg.register("c", object(), priority=30)
        assert reg.names == ["a", "b", "c"]

    def test_generate_all_skips_non_matching(self) -> None:
        spec = _make_spec()

        class NoMatch:
            def applies_to(self, _):
                return False
            def generate(self, *a, **kw):
                return {"nope.txt": "should not appear"}

        class YesMatch:
            def applies_to(self, _):
                return True
            def generate(self, *a, **kw):
                return {"yes.txt": "included"}

        reg = TypedPluginRegistry("test")
        reg.register("no", NoMatch())
        reg.register("yes", YesMatch())
        files = reg.generate_all(spec)
        assert "yes.txt" in files
        assert "nope.txt" not in files

    def test_collect_all(self) -> None:
        spec = _make_spec()

        class Collector:
            def collect(self, _spec, **kw):
                return ["item1", "item2"]

        reg = TypedPluginRegistry("test")
        reg.register("col", Collector())
        items = reg.collect_all(spec)
        assert items == ["item1", "item2"]


# -- PluginRegistry ---------------------------------------------------------


class TestPluginRegistry:
    def test_all_categories(self) -> None:
        pr = PluginRegistry()
        assert set(pr.all_categories.keys()) == {
            "resource", "route", "dashboard", "cicd", "governance", "security", "docs",
        }

    def test_total_starts_at_zero(self) -> None:
        pr = PluginRegistry()
        assert pr.total_plugins == 0

    def test_summary(self) -> None:
        pr = PluginRegistry()
        pr.resource.register("x", object())
        s = pr.summary()
        assert s["resource"] == 1
        assert s["route"] == 0


# -- create_default_plugins -------------------------------------------------


class TestCreateDefaultPlugins:
    def test_loads_all_21_plugins(self) -> None:
        registry = create_default_plugins()
        assert registry.total_plugins == 21

    def test_each_category_has_3(self) -> None:
        registry = create_default_plugins()
        for name, cat in registry.all_categories.items():
            assert len(cat) == 3, f"{name} should have 3 plugins, got {len(cat)}"


# -- Resource Plugins -------------------------------------------------------


class TestServiceBusPlugin:
    def test_applies_to_event_driven(self) -> None:
        spec = _make_spec(raw_intent="event-driven processing pipeline")
        assert ServiceBusPlugin().applies_to(spec)

    def test_not_applies_to_simple(self) -> None:
        spec = _make_spec(raw_intent="simple crud api")
        assert not ServiceBusPlugin().applies_to(spec)

    def test_generate_produces_bicep(self) -> None:
        spec = _make_spec()
        files = ServiceBusPlugin().generate(spec)
        assert any("service-bus.bicep" in k for k in files)
        content = list(files.values())[0]
        assert "Microsoft.ServiceBus/namespaces" in content
        assert "disableLocalAuth: true" in content


class TestEventGridPlugin:
    def test_applies_to_event_driven(self) -> None:
        spec = _make_spec(raw_intent="event grid notification system")
        assert EventGridPlugin().applies_to(spec)

    def test_generate_produces_bicep(self) -> None:
        spec = _make_spec()
        files = EventGridPlugin().generate(spec)
        assert any("event-grid.bicep" in k for k in files)
        content = list(files.values())[0]
        assert "CloudEventSchemaV1_0" in content


class TestFrontDoorPlugin:
    def test_applies_when_waf_enabled(self) -> None:
        spec = _make_spec()  # enable_waf=True in fixture
        assert FrontDoorPlugin().applies_to(spec)

    def test_generate_produces_bicep(self) -> None:
        spec = _make_spec()
        files = FrontDoorPlugin().generate(spec)
        assert any("front-door.bicep" in k for k in files)
        content = list(files.values())[0]
        assert "Microsoft.Cdn/profiles" in content


# -- Route Plugins ----------------------------------------------------------


class TestHealthRoutePlugin:
    def test_applies_when_health_enabled(self) -> None:
        spec = _make_spec()
        assert HealthRoutePlugin().applies_to(spec)

    def test_generate_includes_readiness(self) -> None:
        spec = _make_spec()
        files = HealthRoutePlugin().generate(spec)
        assert any("health.py" in k for k in files)
        content = list(files.values())[0]
        assert "readiness" in content
        assert "cosmos" in content  # data_stores includes cosmos


class TestWebhookRoutePlugin:
    def test_applies_to_webhook_intent(self) -> None:
        spec = _make_spec(raw_intent="webhook callback handler")
        assert WebhookRoutePlugin().applies_to(spec)

    def test_generate_includes_hmac(self) -> None:
        spec = _make_spec()
        files = WebhookRoutePlugin().generate(spec)
        content = list(files.values())[0]
        assert "hmac" in content.lower()


class TestBulkOperationRoutePlugin:
    def test_applies_with_many_entities(self) -> None:
        spec = _make_spec()
        # default fixture has enough entities or keyword match
        plugin = BulkOperationRoutePlugin()
        # Test with keyword
        spec2 = _make_spec(raw_intent="bulk import of csv data")
        assert plugin.applies_to(spec2)


# -- Dashboard Plugins ------------------------------------------------------


class TestStatusDistributionWidget:
    def test_generate_produces_tsx(self) -> None:
        spec = _make_spec()
        files = StatusDistributionWidget().generate(spec)
        assert any(".tsx" in k for k in files)
        content = list(files.values())[0]
        assert "StatusDistribution" in content


class TestTimelineWidget:
    def test_generate_produces_tsx(self) -> None:
        spec = _make_spec()
        files = TimelineWidget().generate(spec)
        assert any("Timeline.tsx" in k for k in files)


class TestMetricCardWidget:
    def test_always_applies(self) -> None:
        spec = _make_spec()
        assert MetricCardWidget().applies_to(spec)

    def test_generate_produces_tsx(self) -> None:
        spec = _make_spec()
        files = MetricCardWidget().generate(spec)
        assert any("MetricCard.tsx" in k for k in files)
        content = list(files.values())[0]
        assert "sparkline" in content.lower()


# -- CI/CD Plugins ----------------------------------------------------------


class TestLoadTestStagePlugin:
    def test_applies_to_performance(self) -> None:
        spec = _make_spec(raw_intent="load test the service")
        assert LoadTestStagePlugin().applies_to(spec)

    def test_generate_produces_workflow(self) -> None:
        spec = _make_spec(raw_intent="load test the service")
        files = LoadTestStagePlugin().generate(spec)
        assert any("load-test.yml" in k for k in files)
        assert any("load-test.js" in k for k in files)


class TestCanaryDeployStagePlugin:
    def test_applies_with_multiple_envs(self) -> None:
        spec = _make_spec()  # fixture has [dev, staging]
        assert CanaryDeployStagePlugin().applies_to(spec)

    def test_generate_produces_workflow(self) -> None:
        spec = _make_spec()
        files = CanaryDeployStagePlugin().generate(spec)
        assert any("canary-deploy.yml" in k for k in files)
        content = list(files.values())[0]
        assert "revision" in content.lower()


class TestSmokeTestStagePlugin:
    def test_always_applies(self) -> None:
        spec = _make_spec()
        assert SmokeTestStagePlugin().applies_to(spec)

    def test_generate_has_health_check(self) -> None:
        spec = _make_spec()
        files = SmokeTestStagePlugin().generate(spec)
        content = list(files.values())[0]
        assert "/health" in content


# -- Governance Plugins -----------------------------------------------------


class TestDataResidencyPolicy:
    def test_applies_to_hipaa(self) -> None:
        spec = _make_spec(
            security=SecurityRequirements(compliance_framework=ComplianceFramework.HIPAA_GUIDANCE)
        )
        assert DataResidencyPolicy().applies_to(spec)

    def test_not_applies_to_general(self) -> None:
        spec = _make_spec()
        assert not DataResidencyPolicy().applies_to(spec)

    def test_collect_violation(self) -> None:
        spec = _make_spec(
            security=SecurityRequirements(compliance_framework=ComplianceFramework.HIPAA_GUIDANCE),
            azure_region="westeurope",
        )
        rules = DataResidencyPolicy().collect(spec)
        assert len(rules) == 1
        assert rules[0].severity == "ERROR"
        assert "westeurope" in rules[0].description

    def test_collect_compliant(self) -> None:
        spec = _make_spec(
            security=SecurityRequirements(compliance_framework=ComplianceFramework.HIPAA_GUIDANCE),
            azure_region="eastus",
        )
        rules = DataResidencyPolicy().collect(spec)
        assert len(rules) == 0

    def test_generate_produces_doc(self) -> None:
        spec = _make_spec(
            security=SecurityRequirements(compliance_framework=ComplianceFramework.HIPAA_GUIDANCE),
        )
        files = DataResidencyPolicy().generate(spec)
        assert any("data-residency.md" in k for k in files)


class TestCostBudgetPolicy:
    def test_applies_to_dev(self) -> None:
        spec = _make_spec(environment="dev")
        assert CostBudgetPolicy().applies_to(spec)

    def test_not_applies_to_prod(self) -> None:
        spec = _make_spec(environment="prod")
        assert not CostBudgetPolicy().applies_to(spec)

    def test_flags_premium_in_dev(self) -> None:
        spec = _make_spec(raw_intent="deploy premium cosmos in dev")
        rules = CostBudgetPolicy().collect(spec)
        assert any(r.severity == "WARNING" for r in rules)


class TestTagCompliancePolicy:
    def test_always_applies(self) -> None:
        spec = _make_spec()
        assert TagCompliancePolicy().applies_to(spec)

    def test_collect_returns_rules(self) -> None:
        spec = _make_spec()
        rules = TagCompliancePolicy().collect(spec)
        # "owner" is typically missing
        assert isinstance(rules, list)


# -- Security Plugins -------------------------------------------------------


class TestWAFRulesPlugin:
    def test_applies_when_waf_enabled(self) -> None:
        spec = _make_spec()
        assert WAFRulesPlugin().applies_to(spec)

    def test_generate_includes_owasp(self) -> None:
        spec = _make_spec()
        files = WAFRulesPlugin().generate(spec)
        content = list(files.values())[0]
        assert "Microsoft_DefaultRuleSet" in content
        assert "RateLimitRule" in content


class TestDDoSProtectionPlugin:
    def test_applies_to_prod(self) -> None:
        spec = _make_spec(environment="prod")
        assert DDoSProtectionPlugin().applies_to(spec)

    def test_generate_produces_bicep(self) -> None:
        spec = _make_spec(environment="prod")
        files = DDoSProtectionPlugin().generate(spec)
        assert any("ddos-protection.bicep" in k for k in files)


class TestNetworkIsolationPlugin:
    def test_applies_to_private(self) -> None:
        spec = _make_spec()  # fixture uses private networking
        assert NetworkIsolationPlugin().applies_to(spec)

    def test_generate_produces_vnet(self) -> None:
        spec = _make_spec()
        files = NetworkIsolationPlugin().generate(spec)
        assert any("network-isolation.bicep" in k for k in files)
        content = list(files.values())[0]
        assert "10.0.0.0/16" in content
        assert "app-subnet" in content


# -- Docs Plugins -----------------------------------------------------------


class TestRunbookDocPlugin:
    def test_always_applies(self) -> None:
        spec = _make_spec()
        assert RunbookDocPlugin().applies_to(spec)

    def test_generate_produces_runbook(self) -> None:
        spec = _make_spec()
        files = RunbookDocPlugin().generate(spec)
        assert any("runbook.md" in k for k in files)
        content = list(files.values())[0]
        assert "Incident Response" in content


class TestAPIReferenceDocPlugin:
    def test_applies_with_entities(self) -> None:
        spec = _make_spec()
        assert APIReferenceDocPlugin().applies_to(spec)

    def test_generate_includes_endpoints(self) -> None:
        spec = _make_spec()
        files = APIReferenceDocPlugin().generate(spec)
        content = list(files.values())[0]
        assert "GET" in content
        assert "POST" in content


class TestComplianceEvidenceDocPlugin:
    def test_applies_non_general(self) -> None:
        spec = _make_spec(
            security=SecurityRequirements(compliance_framework=ComplianceFramework.HIPAA_GUIDANCE)
        )
        assert ComplianceEvidenceDocPlugin().applies_to(spec)

    def test_not_applies_general(self) -> None:
        spec = _make_spec()
        assert not ComplianceEvidenceDocPlugin().applies_to(spec)

    def test_generate_hipaa_controls(self) -> None:
        spec = _make_spec(
            security=SecurityRequirements(compliance_framework=ComplianceFramework.HIPAA_GUIDANCE)
        )
        files = ComplianceEvidenceDocPlugin().generate(spec)
        content = list(files.values())[0]
        assert "HIPAA_GUIDANCE" in content
        assert "164.312" in content


# -- Integration: generate_all across categories ----------------------------


class TestPluginIntegration:
    """Test that the full registry generates files from multiple categories."""

    def test_resource_generate_all(self) -> None:
        registry = create_default_plugins()
        spec = _make_spec()
        files = registry.resource.generate_all(spec)
        # event-driven in raw_intent -> ServiceBus + EventGrid match
        assert len(files) >= 1
        assert all(isinstance(v, str) for v in files.values())

    def test_governance_collect_all(self) -> None:
        registry = create_default_plugins()
        spec = _make_spec(environment="dev", raw_intent="premium cosmos database")
        rules = registry.governance.collect_all(spec)
        assert isinstance(rules, list)
        # CostBudgetPolicy should fire on "premium" in dev
        assert any(
            getattr(r, "severity", None) == "WARNING"
            for r in rules
        )

    def test_docs_generate_all(self) -> None:
        registry = create_default_plugins()
        spec = _make_spec()
        files = registry.docs.generate_all(spec)
        assert any("runbook" in k for k in files)
        assert any("api-reference" in k for k in files)
