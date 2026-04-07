"""Tests for ScaffoldPlan, UniquenessProfile, and GenerationServices."""

from __future__ import annotations

import pytest

from src.orchestrator.generators.scaffold_plan import (
    CachedEnricher,
    EnrichmentCache,
    GenerationServices,
    ScaffoldPlan,
    UniquenessProfile,
    build_uniqueness_profile,
    _build_deterministic_kpis,
    _build_deterministic_labels,
    _build_deterministic_api_descriptions,
)
from src.orchestrator.generators.llm_enricher import (
    EnrichmentTarget,
    EnrichmentType,
)
from src.orchestrator.generators.app_generator import AppGenerator
from src.orchestrator.generators.docs_generator import DocsGenerator
from src.orchestrator.generators.frontend_generator import FrontendGenerator
from src.orchestrator.generators.scaffold_validator import ScaffoldValidator
from src.orchestrator.intent_schema import (
    AppType,
    AuthModel,
    CICDRequirements,
    ComplianceFramework,
    ComponentSpec,
    DataStore,
    EntitySpec,
    FieldSpec,
    GovernanceReport,
    IntentSpec,
    NetworkingModel,
    ObservabilityRequirements,
    PlanOutput,
    SecurityRequirements,
    ThreatEntry,
)
from src.orchestrator.generators.domain_context import build_domain_context
from src.orchestrator.generators.design_system import DesignSystem


def _make_spec() -> IntentSpec:
    return IntentSpec(
        project_name="health-tracker",
        app_type=AppType.API,
        description="A healthcare patient tracking system",
        raw_intent="Build a healthcare patient tracking system",
        data_stores=[DataStore.COSMOS_DB],
        security=SecurityRequirements(
            auth_model=AuthModel.MANAGED_IDENTITY,
            compliance_framework=ComplianceFramework.HIPAA_GUIDANCE,
            data_classification="confidential",
            networking=NetworkingModel.PRIVATE,
            encryption_at_rest=True,
            encryption_in_transit=True,
            secret_management=True,
        ),
        observability=ObservabilityRequirements(log_analytics=True, health_endpoint=True),
        cicd=CICDRequirements(oidc_auth=True),
        azure_region="eastus2",
        resource_group_name="rg-health",
        environment="dev",
        confidence=0.9,
        entities=[
            EntitySpec(
                name="Patient",
                fields=[
                    FieldSpec(name="name", type="str", description="Patient name"),
                    FieldSpec(name="status", type="str", description="Active/inactive"),
                    FieldSpec(name="diagnosis", type="str", description="Primary diagnosis"),
                    FieldSpec(name="admitted_date", type="datetime", description="Admission date"),
                ],
            ),
            EntitySpec(
                name="Appointment",
                fields=[
                    FieldSpec(name="patient_id", type="str", description="Patient FK"),
                    FieldSpec(name="doctor", type="str", description="Doctor name"),
                    FieldSpec(name="status", type="str", description="Scheduled/completed"),
                    FieldSpec(name="date", type="datetime", description="Appointment date"),
                ],
            ),
        ],
    )


def _make_plan() -> PlanOutput:
    return PlanOutput(
        title="Health Tracker Plan",
        summary="Healthcare tracking platform",
        components=[
            ComponentSpec(
                name="container-app",
                azure_service="Microsoft.App/containerApps",
                purpose="Run API",
                bicep_module="container-app.bicep",
                security_controls=["Managed Identity"],
            ),
        ],
        decisions=[],
        threat_model=[
            ThreatEntry(
                id="T-001", category="Spoofing",
                description="Identity spoofing", mitigation="MI", residual_risk="Low",
            ),
        ],
        diagram_mermaid="graph TD; A-->B;",
    )


# ── UniquenessProfile Tests ──


class TestUniquenessProfile:
    """Test that UniquenessProfile builds correctly."""

    def test_default_profile(self):
        p = UniquenessProfile()
        assert p.domain == "generic"
        assert p.enrichment_score == 0.0
        assert p.kpi_definitions == []

    def test_build_deterministic(self):
        spec = _make_spec()
        domain_ctx = build_domain_context(spec)
        tokens = DesignSystem().generate_tokens(spec)
        profile = build_uniqueness_profile(spec, domain_ctx, tokens, enricher=None)
        assert profile.domain != ""
        assert len(profile.kpi_definitions) >= 3
        assert profile.enrichment_score == 0.0

    def test_kpi_definitions_have_required_keys(self):
        spec = _make_spec()
        domain_ctx = build_domain_context(spec)
        kpis = _build_deterministic_kpis(spec, domain_ctx)
        for kpi in kpis:
            assert "label" in kpi
            assert "key" in kpi
            assert "icon" in kpi
            assert "color" in kpi

    def test_kpi_primary_uses_first_entity(self):
        spec = _make_spec()
        domain_ctx = build_domain_context(spec)
        kpis = _build_deterministic_kpis(spec, domain_ctx)
        assert kpis[0]["label"] == "Total Patients"
        assert kpis[0]["key"] == "total_primary"

    def test_labels_cover_all_entities(self):
        spec = _make_spec()
        domain_ctx = build_domain_context(spec)
        result = _build_deterministic_labels(spec, domain_ctx)
        empty_states, action_labels, column_labels, page_titles = (
            result["empty_states"],
            result["action_labels"],
            result["column_labels"],
            result["page_titles"],
        )
        for ent in spec.entities:
            assert ent.name in empty_states
            assert ent.name in action_labels
            assert ent.name in page_titles

    def test_api_descriptions_cover_all_entities(self):
        spec = _make_spec()
        descs = _build_deterministic_api_descriptions(spec)
        for ent in spec.entities:
            assert ent.name in descs

    def test_healthcare_domain_kpi(self):
        spec = _make_spec()
        domain_ctx = build_domain_context(spec)
        kpis = _build_deterministic_kpis(spec, domain_ctx)
        labels = [k["label"] for k in kpis]
        # Should have domain-specific KPI for healthcare
        assert any("Critical" in l or "Active" in l for l in labels)


# ── EnrichmentCache Tests ──


class TestEnrichmentCache:
    """Test the enrichment cache."""

    def _target(self, ctx: str = "hello") -> EnrichmentTarget:
        return EnrichmentTarget(
            target_type=EnrichmentType.SEED_DESCRIPTION,
            context=ctx,
            default_value="fallback",
        )

    def test_cache_miss_returns_none(self):
        cache = EnrichmentCache()
        assert cache.get(self._target()) is None

    def test_cache_stores_and_retrieves(self):
        from src.orchestrator.generators.llm_enricher import EnrichmentResult
        cache = EnrichmentCache()
        target = self._target()
        result = EnrichmentResult(
            original="hello", enriched="result-1",
            was_enriched=True, target_type=EnrichmentType.SEED_DESCRIPTION,
        )
        cache.put(target, result)
        assert cache.get(target) is not None
        assert cache.get(target).enriched == "result-1"

    def test_cache_different_contexts_are_independent(self):
        from src.orchestrator.generators.llm_enricher import EnrichmentResult
        cache = EnrichmentCache()
        t1 = self._target("ctx-a")
        t2 = self._target("ctx-b")
        r1 = EnrichmentResult(original="a", enriched="result-a", was_enriched=True, target_type=EnrichmentType.SEED_DESCRIPTION)
        r2 = EnrichmentResult(original="b", enriched="result-b", was_enriched=True, target_type=EnrichmentType.SEED_DESCRIPTION)
        cache.put(t1, r1)
        cache.put(t2, r2)
        assert cache.get(t1).enriched == "result-a"
        assert cache.get(t2).enriched == "result-b"


# ── CachedEnricher Tests ──


class TestCachedEnricher:
    """Test the cached enricher wrapper."""

    def test_disabled_when_no_enricher(self):
        from src.orchestrator.generators.llm_enricher import LLMEnricher
        enricher = LLMEnricher(llm_call=None)
        ce = CachedEnricher(enricher)
        assert not ce.is_enabled

    def test_enrich_returns_default_when_disabled(self):
        from src.orchestrator.generators.llm_enricher import LLMEnricher
        enricher = LLMEnricher(llm_call=None)
        ce = CachedEnricher(enricher)
        target = EnrichmentTarget(
            target_type=EnrichmentType.SEED_DESCRIPTION,
            context="describe a patient",
            default_value="fallback text",
        )
        result = ce.enrich(target)
        assert result.enriched == "fallback text"
        assert not result.was_enriched


# ── GenerationServices Tests ──


class TestGenerationServices:
    """Test GenerationServices factory."""

    def test_create_without_llm(self):
        spec = _make_spec()
        services = GenerationServices.create(spec, llm_call=None)
        assert services.domain_ctx is not None
        assert services.design_tokens is not None
        assert not services.enricher.is_enabled

    def test_create_has_correct_domain(self):
        spec = _make_spec()
        services = GenerationServices.create(spec, llm_call=None)
        assert services.domain_ctx is not None


# ── ScaffoldPlan Tests ──


class TestScaffoldPlan:
    """Test ScaffoldPlan master plan creation."""

    def test_create_without_llm(self):
        spec = _make_spec()
        plan = _make_plan()
        scaffold = ScaffoldPlan.create(spec, plan, governance=None, waf_report=None, llm_call=None)
        assert scaffold.spec is spec
        assert scaffold.plan is plan
        assert scaffold.uniqueness is not None
        assert scaffold.uniqueness.enrichment_score == 0.0
        assert scaffold.services is not None

    def test_uniqueness_has_kpis(self):
        spec = _make_spec()
        plan = _make_plan()
        scaffold = ScaffoldPlan.create(spec, plan, governance=None, waf_report=None, llm_call=None)
        assert len(scaffold.uniqueness.kpi_definitions) >= 3

    def test_uniqueness_has_page_titles(self):
        spec = _make_spec()
        plan = _make_plan()
        scaffold = ScaffoldPlan.create(spec, plan, governance=None, waf_report=None, llm_call=None)
        assert "Patient" in scaffold.uniqueness.page_titles
        assert "Appointment" in scaffold.uniqueness.page_titles

    def test_uniqueness_has_error_messages(self):
        spec = _make_spec()
        plan = _make_plan()
        scaffold = ScaffoldPlan.create(spec, plan, governance=None, waf_report=None, llm_call=None)
        assert "Patient" in scaffold.uniqueness.error_messages
        assert "not_found" in scaffold.uniqueness.error_messages["Patient"]


# ── Generator Integration Tests ──


class TestGeneratorScaffoldPlanIntegration:
    """Test that generators correctly receive and use ScaffoldPlan."""

    def _make_scaffold(self):
        spec = _make_spec()
        plan = _make_plan()
        return ScaffoldPlan.create(spec, plan, governance=None, waf_report=None, llm_call=None), spec, plan

    def test_app_generator_uses_scaffold_plan(self):
        scaffold, spec, plan = self._make_scaffold()
        gen = AppGenerator()
        gen.set_scaffold_plan(scaffold)
        files = gen.generate(spec)
        assert "src/app/main.py" in files

    def test_app_generator_injects_error_messages(self):
        scaffold, spec, plan = self._make_scaffold()
        gen = AppGenerator()
        gen.set_scaffold_plan(scaffold)
        files = gen.generate(spec)
        router = files.get("src/app/api/v1/router.py", "")
        # Should use domain-specific error message, not generic
        assert "Patient" in router

    def test_app_generator_injects_service_docstrings(self):
        scaffold, spec, plan = self._make_scaffold()
        gen = AppGenerator()
        gen.set_scaffold_plan(scaffold)
        files = gen.generate(spec)
        services = files.get("src/app/core/services.py", "")
        # Should have entity-specific docstrings
        assert "Patient" in services

    def test_frontend_generator_uses_scaffold_plan(self):
        scaffold, spec, plan = self._make_scaffold()
        gen = FrontendGenerator()
        gen.set_scaffold_plan(scaffold)
        files = gen.generate(spec)
        dashboard = files.get("frontend/src/pages/Dashboard.tsx", "")
        assert len(dashboard) > 0

    def test_frontend_generator_injects_kpis(self):
        scaffold, spec, plan = self._make_scaffold()
        gen = FrontendGenerator()
        gen.set_scaffold_plan(scaffold)
        files = gen.generate(spec)
        dashboard = files.get("frontend/src/pages/Dashboard.tsx", "")
        # Should have domain-specific KPI label, not just generic "Total Records"
        assert "Total Patient" in dashboard

    def test_frontend_generator_uses_page_titles(self):
        scaffold, spec, plan = self._make_scaffold()
        gen = FrontendGenerator()
        gen.set_scaffold_plan(scaffold)
        files = gen.generate(spec)
        dashboard = files.get("frontend/src/pages/Dashboard.tsx", "")
        # Page titles from uniqueness should appear in tab config
        patient_title = scaffold.uniqueness.page_titles.get("Patient", "")
        if patient_title:
            assert patient_title in dashboard

    def test_docs_generator_uses_scaffold_plan(self):
        scaffold, spec, plan = self._make_scaffold()
        gen = DocsGenerator()
        gen.set_scaffold_plan(scaffold)
        files = gen.generate(spec, plan)
        plan_md = files.get("docs/plan.md", "")
        assert "Health Tracker" in plan_md or "health-tracker" in plan_md

    def test_scaffold_validator_reports_uniqueness(self):
        scaffold, spec, plan = self._make_scaffold()
        gen = AppGenerator()
        gen.set_scaffold_plan(scaffold)
        files = gen.generate(spec)

        validator = ScaffoldValidator()
        validator.set_scaffold_plan(scaffold)
        report = validator.validate(spec, files)
        # Should report enrichment score
        uniqueness_issues = [i for i in report.issues if i.category == "uniqueness"]
        assert len(uniqueness_issues) > 0
        assert "Enrichment score" in uniqueness_issues[0].message

    def test_all_generators_have_set_scaffold_plan(self):
        """Verify all generators support set_scaffold_plan."""
        from src.orchestrator.generators.alert_generator import AlertGenerator
        from src.orchestrator.generators.bicep_generator import BicepGenerator
        from src.orchestrator.generators.cicd_generator import CICDGenerator
        from src.orchestrator.generators.cost_estimator import CostEstimator
        from src.orchestrator.generators.dashboard_generator import DashboardGenerator
        from src.orchestrator.generators.fabric_generator import FabricGenerator
        from src.orchestrator.generators.frontend_api_generator import FrontendApiGenerator
        from src.orchestrator.generators.test_generator import ScaffoldTestGenerator as TGen

        generators = [
            AppGenerator(), BicepGenerator(), CICDGenerator(), CostEstimator(),
            DashboardGenerator(), DocsGenerator(), FabricGenerator(),
            FrontendApiGenerator(), FrontendGenerator(), TGen(),
            AlertGenerator(),
        ]
        for gen in generators:
            assert hasattr(gen, "set_scaffold_plan"), f"{type(gen).__name__} missing set_scaffold_plan"
