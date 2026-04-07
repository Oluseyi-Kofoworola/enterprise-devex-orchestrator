"""Tests for the Design System generator -- domain detection, token generation, CSS output."""

from __future__ import annotations

from src.orchestrator.generators.design_system import DesignSystem, DesignTokens
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


def _make_spec(
    raw_intent: str = "Build a test API",
    description: str = "A test service",
    entities: list[EntitySpec] | None = None,
) -> IntentSpec:
    return IntentSpec(
        project_name="test-project",
        app_type=AppType.API,
        description=description,
        raw_intent=raw_intent,
        data_stores=[],
        entities=entities or [],
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


class TestDesignSystemDomainDetection:
    """Test domain detection from intent specs."""

    def setup_method(self) -> None:
        self.ds = DesignSystem()

    def test_default_domain(self) -> None:
        spec = _make_spec(raw_intent="Build a generic app")
        domain = self.ds.detect_domain(spec)
        assert domain == "generic"

    def test_healthcare_domain(self) -> None:
        spec = _make_spec(raw_intent="Build a patient management system for hospitals")
        domain = self.ds.detect_domain(spec)
        assert domain == "healthcare"

    def test_fintech_domain(self) -> None:
        spec = _make_spec(raw_intent="Build a payment processing banking platform")
        domain = self.ds.detect_domain(spec)
        assert domain == "fintech"

    def test_ecommerce_domain(self) -> None:
        spec = _make_spec(raw_intent="Build an online store with shopping cart for products")
        domain = self.ds.detect_domain(spec)
        assert domain == "ecommerce"

    def test_logistics_domain(self) -> None:
        spec = _make_spec(raw_intent="Build a fleet management logistics tracking system")
        domain = self.ds.detect_domain(spec)
        assert domain == "logistics"

    def test_iot_domain(self) -> None:
        spec = _make_spec(raw_intent="Build an IoT sensor monitoring dashboard")
        domain = self.ds.detect_domain(spec)
        assert domain == "iot_smart_city"

    def test_legal_domain(self) -> None:
        spec = _make_spec(raw_intent="Build a contract review legal compliance system")
        domain = self.ds.detect_domain(spec)
        assert domain == "legal"

    def test_education_domain(self) -> None:
        spec = _make_spec(raw_intent="Build a student enrollment learning management system")
        domain = self.ds.detect_domain(spec)
        assert domain == "education"

    def test_saas_domain(self) -> None:
        spec = _make_spec(raw_intent="Build a multi-tenant SaaS subscription billing platform")
        domain = self.ds.detect_domain(spec)
        assert domain == "saas"

    def test_ai_ml_domain(self) -> None:
        spec = _make_spec(raw_intent="Build a machine learning model training pipeline")
        domain = self.ds.detect_domain(spec)
        assert domain == "ai_ml"

    def test_real_estate_domain(self) -> None:
        spec = _make_spec(raw_intent="Build a property listing real estate management system")
        domain = self.ds.detect_domain(spec)
        assert domain == "real_estate"

    def test_entity_names_contribute_to_detection(self) -> None:
        entities = [
            EntitySpec(
                name="Patient",
                fields=[FieldSpec(name="name", field_type="str")],
            ),
        ]
        spec = _make_spec(raw_intent="Build a management system", entities=entities)
        domain = self.ds.detect_domain(spec)
        assert domain == "healthcare"


class TestDesignTokenGeneration:
    """Test design token generation."""

    def setup_method(self) -> None:
        self.ds = DesignSystem()

    def test_returns_design_tokens(self) -> None:
        spec = _make_spec()
        tokens = self.ds.generate_tokens(spec)
        assert isinstance(tokens, DesignTokens)

    def test_tokens_have_required_fields(self) -> None:
        spec = _make_spec()
        tokens = self.ds.generate_tokens(spec)
        assert tokens.primary
        assert tokens.bg_primary
        assert tokens.text_primary
        assert tokens.font_heading
        assert tokens.font_body
        assert tokens.gradient_header

    def test_healthcare_preset_applied(self) -> None:
        spec = _make_spec(raw_intent="Build a patient health care management system")
        tokens = self.ds.generate_tokens(spec)
        # Healthcare should have teal-ish primary
        assert tokens.primary != ""

    def test_dark_mode_overrides_present(self) -> None:
        spec = _make_spec()
        tokens = self.ds.generate_tokens(spec)
        assert tokens.dark_bg_primary
        assert tokens.dark_text_primary
        assert tokens.dark_surface_card

    def test_chart_palette_has_entries(self) -> None:
        spec = _make_spec()
        tokens = self.ds.generate_tokens(spec)
        assert len(tokens.chart_palette) >= 6

    def test_anti_patterns_is_list(self) -> None:
        spec = _make_spec()
        tokens = self.ds.generate_tokens(spec)
        assert isinstance(tokens.anti_patterns, list)


class TestCSSGeneration:
    """Test CSS variable generation."""

    def setup_method(self) -> None:
        self.ds = DesignSystem()

    def test_generates_css(self) -> None:
        spec = _make_spec()
        tokens = self.ds.generate_tokens(spec)
        css = self.ds.generate_css_variables(tokens)
        assert ":root" in css
        assert "--color-primary" in css
        assert "--bg-primary" in css

    def test_dark_mode_in_css(self) -> None:
        spec = _make_spec()
        tokens = self.ds.generate_tokens(spec)
        css = self.ds.generate_css_variables(tokens)
        assert ".dark" in css or "dark" in css

    def test_focus_ring_in_css(self) -> None:
        spec = _make_spec()
        tokens = self.ds.generate_tokens(spec)
        css = self.ds.generate_css_variables(tokens)
        assert "focus" in css.lower()

    def test_skeleton_animation_in_css(self) -> None:
        spec = _make_spec()
        tokens = self.ds.generate_tokens(spec)
        css = self.ds.generate_css_variables(tokens)
        assert "skeleton" in css.lower()

    def test_reduced_motion_in_css(self) -> None:
        spec = _make_spec()
        tokens = self.ds.generate_tokens(spec)
        css = self.ds.generate_css_variables(tokens)
        assert "prefers-reduced-motion" in css


class TestDesignSpec:
    """Test full design spec generation."""

    def setup_method(self) -> None:
        self.ds = DesignSystem()

    def test_generates_two_files(self) -> None:
        spec = _make_spec()
        files = self.ds.generate_design_spec(spec)
        css_key = [k for k in files if k.endswith(".css")]
        json_key = [k for k in files if k.endswith(".json")]
        assert len(css_key) == 1
        assert len(json_key) == 1

    def test_css_file_is_valid(self) -> None:
        spec = _make_spec()
        files = self.ds.generate_design_spec(spec)
        css_key = [k for k in files if k.endswith(".css")][0]
        css = files[css_key]
        assert ":root" in css
        assert "--color-primary" in css

    def test_json_file_is_valid(self) -> None:
        import json

        spec = _make_spec()
        files = self.ds.generate_design_spec(spec)
        json_key = [k for k in files if k.endswith(".json")][0]
        data = json.loads(files[json_key])
        assert "domain" in data

    def test_different_domains_produce_different_tokens(self) -> None:
        spec_health = _make_spec(raw_intent="Build a patient healthcare system")
        spec_fintech = _make_spec(raw_intent="Build a banking payment platform")
        tokens_health = self.ds.generate_tokens(spec_health)
        tokens_fintech = self.ds.generate_tokens(spec_fintech)
        # Different domains should have different primary colors
        assert tokens_health.primary != tokens_fintech.primary
