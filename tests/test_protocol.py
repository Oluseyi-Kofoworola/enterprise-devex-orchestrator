"""Tests for the Generator Protocol, Registry, and Adapter system."""

from __future__ import annotations

import pytest

from src.orchestrator.generators.protocol import (
    GeneratorAdapter,
    GeneratorContext,
    GeneratorProtocol,
    GeneratorRegistry,
    _bridge_cost,
    _bridge_docs,
    _bridge_spec_only,
    _bridge_spec_plan,
    _bridge_cicd,
    create_default_registry,
)
from src.orchestrator.intent_schema import (
    AppType,
    AuthModel,
    CICDRequirements,
    ComplianceFramework,
    ComponentSpec,
    DataStore,
    GovernanceReport,
    IntentSpec,
    NetworkingModel,
    ObservabilityRequirements,
    PlanOutput,
    SecurityRequirements,
    ThreatEntry,
)


# -- Fixtures ---------------------------------------------------------------

def _make_spec(data_stores: list[DataStore] | None = None) -> IntentSpec:
    return IntentSpec(
        project_name="test-project",
        app_type=AppType.API,
        description="A test API service",
        raw_intent="Build a test API",
        data_stores=data_stores or [],
        security=SecurityRequirements(
            auth_model=AuthModel.MANAGED_IDENTITY,
            compliance_framework=ComplianceFramework.GENERAL,
            data_classification="internal",
            networking=NetworkingModel.PRIVATE,
            encryption_at_rest=True,
            encryption_in_transit=True,
            secret_management=True,
        ),
        observability=ObservabilityRequirements(
            log_analytics=True,
            health_endpoint=True,
        ),
        cicd=CICDRequirements(oidc_auth=True),
        azure_region="eastus2",
        resource_group_name="rg-test",
        environment="dev",
        confidence=0.85,
    )


def _make_plan() -> PlanOutput:
    return PlanOutput(
        title="Test Architecture Plan",
        summary="Test architecture plan",
        components=[
            ComponentSpec(
                name="container-app",
                azure_service="Microsoft.App/containerApps",
                purpose="Run application",
                bicep_module="container-app.bicep",
                security_controls=["Managed Identity"],
            ),
        ],
        decisions=[],
        threat_model=[
            ThreatEntry(
                id="T-001",
                category="Spoofing",
                description="Identity spoofing",
                mitigation="Managed Identity",
                residual_risk="Low",
            ),
        ],
        diagram_mermaid="graph TD; A-->B;",
    )


# -- GeneratorContext -------------------------------------------------------

class TestGeneratorContext:
    """Test the GeneratorContext dataclass."""

    def test_defaults(self) -> None:
        ctx = GeneratorContext()
        assert ctx.plan is None
        assert ctx.governance is None
        assert ctx.waf_report is None
        assert ctx.version == 1
        assert ctx.standards is None
        assert ctx.extra == {}

    def test_with_plan(self) -> None:
        plan = _make_plan()
        ctx = GeneratorContext(plan=plan)
        assert ctx.plan is plan

    def test_frozen(self) -> None:
        ctx = GeneratorContext()
        with pytest.raises(AttributeError):
            ctx.plan = _make_plan()  # type: ignore[misc]

    def test_extra_dict(self) -> None:
        ctx = GeneratorContext(extra={"custom_key": 42})
        assert ctx.extra["custom_key"] == 42


# -- GeneratorProtocol ------------------------------------------------------

class TestGeneratorProtocol:
    """Test the structural protocol via isinstance checks."""

    def test_conforming_class(self) -> None:
        class Good:
            def generate(self, spec, context):
                return {"file.txt": "content"}
        assert isinstance(Good(), GeneratorProtocol)

    def test_nonconforming_class(self) -> None:
        class Bad:
            def produce(self, spec, context):
                return {}
        assert not isinstance(Bad(), GeneratorProtocol)


# -- GeneratorAdapter -------------------------------------------------------

class TestGeneratorAdapter:
    """Test the adapter pattern for wrapping legacy generators."""

    def test_spec_only_bridge(self) -> None:
        class FakeGen:
            def generate(self, spec):
                return {"f.txt": spec.project_name}

        adapter = GeneratorAdapter(FakeGen(), _bridge_spec_only)
        result = adapter.generate(_make_spec(), GeneratorContext())
        assert result == {"f.txt": "test-project"}

    def test_spec_plan_bridge(self) -> None:
        class FakeBicep:
            def generate(self, spec, plan):
                return {"main.bicep": plan.title}

        plan = _make_plan()
        adapter = GeneratorAdapter(FakeBicep(), _bridge_spec_plan)
        result = adapter.generate(_make_spec(), GeneratorContext(plan=plan))
        assert result == {"main.bicep": "Test Architecture Plan"}

    def test_cicd_bridge(self) -> None:
        class FakeCICD:
            def generate(self, spec, version=1):
                return {"ci.yml": f"v{version}"}

        adapter = GeneratorAdapter(FakeCICD(), _bridge_cicd)
        result = adapter.generate(_make_spec(), GeneratorContext(version=3))
        assert result == {"ci.yml": "v3"}

    def test_docs_bridge(self) -> None:
        class FakeDocs:
            def generate(self, spec, plan, governance=None, waf_report=None):
                return {"docs.md": f"gov={governance is not None}"}

        plan = _make_plan()
        gov = GovernanceReport(
            status="PASS", checks=[], summary="All checks passed", recommendations=[],
        )
        adapter = GeneratorAdapter(FakeDocs(), _bridge_docs)
        ctx = GeneratorContext(plan=plan, governance=gov)
        result = adapter.generate(_make_spec(), ctx)
        assert result == {"docs.md": "gov=True"}

    def test_cost_bridge(self) -> None:
        from dataclasses import dataclass

        @dataclass
        class FakeEstimate:
            def to_markdown(self):
                return "# Cost: $42"

        class FakeCost:
            def estimate(self, spec, plan):
                return FakeEstimate()

        plan = _make_plan()
        adapter = GeneratorAdapter(FakeCost(), _bridge_cost)
        result = adapter.generate(_make_spec(), GeneratorContext(plan=plan))
        assert result == {"docs/cost-estimate.md": "# Cost: $42"}

    def test_adapter_satisfies_protocol(self) -> None:
        class Dummy:
            def generate(self, spec):
                return {}
        adapter = GeneratorAdapter(Dummy(), _bridge_spec_only)
        assert isinstance(adapter, GeneratorProtocol)


# -- GeneratorRegistry ------------------------------------------------------

class TestGeneratorRegistry:
    """Test registry registration, lookup, and execution."""

    def _make_adapter(self, name: str) -> GeneratorAdapter:
        class Stub:
            def __init__(self, n):
                self._n = n
            def generate(self, spec):
                return {f"{self._n}.txt": "ok"}
        return GeneratorAdapter(Stub(name), _bridge_spec_only)

    def test_register_and_names(self) -> None:
        reg = GeneratorRegistry()
        reg.register("alpha", self._make_adapter("alpha"), priority=20)
        reg.register("beta", self._make_adapter("beta"), priority=10)
        # Names should be in priority order
        assert reg.names == ["beta", "alpha"]

    def test_len_and_contains(self) -> None:
        reg = GeneratorRegistry()
        reg.register("a", self._make_adapter("a"))
        assert len(reg) == 1
        assert "a" in reg
        assert "b" not in reg

    def test_get(self) -> None:
        reg = GeneratorRegistry()
        adapter = self._make_adapter("x")
        reg.register("x", adapter)
        assert reg.get("x") is adapter
        assert reg.get("missing") is None

    def test_unregister(self) -> None:
        reg = GeneratorRegistry()
        reg.register("a", self._make_adapter("a"))
        assert reg.unregister("a") is True
        assert len(reg) == 0
        assert reg.unregister("nonexistent") is False

    def test_run_all_merges_files(self) -> None:
        reg = GeneratorRegistry()
        reg.register("a", self._make_adapter("a"), priority=10)
        reg.register("b", self._make_adapter("b"), priority=20)
        files = reg.run_all(_make_spec(), GeneratorContext())
        assert "a.txt" in files
        assert "b.txt" in files

    def test_priority_order(self) -> None:
        """Later priorities can overwrite files from earlier ones."""
        class OverwriteGen:
            def __init__(self, val):
                self._val = val
            def generate(self, spec):
                return {"shared.txt": self._val}

        reg = GeneratorRegistry()
        reg.register(
            "first",
            GeneratorAdapter(OverwriteGen("first"), _bridge_spec_only),
            priority=10,
        )
        reg.register(
            "second",
            GeneratorAdapter(OverwriteGen("second"), _bridge_spec_only),
            priority=20,
        )
        files = reg.run_all(_make_spec(), GeneratorContext())
        assert files["shared.txt"] == "second"

    def test_empty_registry(self) -> None:
        reg = GeneratorRegistry()
        files = reg.run_all(_make_spec(), GeneratorContext())
        assert files == {}


# -- create_default_registry ------------------------------------------------

class TestDefaultRegistry:
    """Test the factory that pre-loads all 9 built-in generators."""

    def test_has_all_generators(self) -> None:
        reg = create_default_registry()
        expected = {"bicep", "cicd", "app", "frontend", "docs", "tests", "alerts", "dashboard", "cost"}
        assert set(reg.names) == expected

    def test_count(self) -> None:
        reg = create_default_registry()
        assert len(reg) == 9

    def test_priority_order_starts_with_bicep(self) -> None:
        reg = create_default_registry()
        assert reg.names[0] == "bicep"

    def test_run_all_produces_files(self) -> None:
        spec = _make_spec()
        plan = _make_plan()
        ctx = GeneratorContext(plan=plan)
        reg = create_default_registry()
        files = reg.run_all(spec, ctx)
        # Should produce a large number of files from all generators
        assert len(files) > 20
        # Spot-check key files
        assert any("main.bicep" in k for k in files)
        assert any("deploy.yml" in k for k in files)
        assert any("main.py" in k for k in files)
        assert "docs/cost-estimate.md" in files

    def test_each_adapter_satisfies_protocol(self) -> None:
        reg = create_default_registry()
        for name in reg.names:
            gen = reg.get(name)
            assert isinstance(gen, GeneratorProtocol), f"{name} does not satisfy GeneratorProtocol"


# -- Integration: InfrastructureGeneratorAgent via registry -----------------

class TestInfraGeneratorIntegration:
    """Verify the InfrastructureGeneratorAgent still works after refactor."""

    def test_generate_produces_expected_files(self) -> None:
        from src.orchestrator.agents.infra_generator import InfrastructureGeneratorAgent
        from src.orchestrator.config import AppConfig

        agent = InfrastructureGeneratorAgent(config=AppConfig())
        spec = _make_spec()
        plan = _make_plan()
        files = agent.generate(spec, plan)

        assert isinstance(files, dict)
        assert len(files) > 20
        # Verify key file categories are present
        bicep_files = [k for k in files if k.endswith(".bicep")]
        workflow_files = [k for k in files if ".github/workflows" in k]
        doc_files = [k for k in files if k.startswith("docs/")]
        assert len(bicep_files) > 0
        assert len(workflow_files) > 0
        assert len(doc_files) > 0
        assert "docs/cost-estimate.md" in files
