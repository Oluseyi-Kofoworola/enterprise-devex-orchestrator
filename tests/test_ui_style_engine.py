"""Tests for the UI Style Engine -- dynamic design intelligence reasoning system."""

import pytest

from src.orchestrator.generators.ui_style_engine import (
    UIStyleEngine,
    _UI_STYLES,
    _FONT_PAIRINGS,
    _INDUSTRY_RULES,
    QUALITY_CHECKLIST,
)
from src.orchestrator.generators.frontend_generator import _get_style_classes
from src.orchestrator.intent_schema import IntentSpec, SecurityRequirements, ObservabilityRequirements, CICDRequirements


def _make_spec(project_name: str = "test-project", description: str = "A test service"):
    """Create a minimal valid IntentSpec for testing."""
    return IntentSpec(
        project_name=project_name,
        app_type="api",
        description=description,
        raw_intent=description,
        data_stores=[],
        entities=[],
        security=SecurityRequirements(
            auth_model="managed_identity",
            compliance_framework="general",
            data_classification="internal",
            networking="private",
            encryption_at_rest=True,
            encryption_in_transit=True,
            secret_management=True,
        ),
        observability=ObservabilityRequirements(log_analytics=True, health_endpoint=True),
        cicd=CICDRequirements(oidc_auth=True),
        azure_region="eastus2",
        resource_group_name="rg-test",
        environment="dev",
        confidence=0.85,
    )


@pytest.fixture
def engine():
    return UIStyleEngine()


# ── Style Engine Basics ──────────────────────────────────────────

class TestUIStyleEngine:
    """Core UIStyleEngine tests."""

    def test_recommend_returns_recommendation(self, engine):
        rec = engine.recommend("healthcare")
        assert rec.primary_style == "soft_ui"
        assert rec.secondary_style == "minimalism"
        assert rec.font_pairing is not None
        assert rec.css_effects
        assert rec.google_fonts_url.startswith("https://fonts.googleapis.com")

    def test_recommend_unknown_domain_falls_back(self, engine):
        rec = engine.recommend("unknown_domain_xyz")
        # Should fallback to saas rules
        assert rec.primary_style in _UI_STYLES
        assert rec.css_effects

    def test_all_domains_produce_valid_recommendations(self, engine):
        for domain in _INDUSTRY_RULES:
            rec = engine.recommend(domain)
            assert rec.primary_style in _UI_STYLES
            assert rec.secondary_style in _UI_STYLES
            assert rec.font_pairing is not None
            assert rec.google_fonts_url
            assert isinstance(rec.anti_patterns, list)
            assert isinstance(rec.quality_checks, list)
            assert isinstance(rec.key_effects, list)

    def test_motion_effects_always_included(self, engine):
        """All recommendations should include motion CSS for stagger animations."""
        for domain in _INDUSTRY_RULES:
            rec = engine.recommend(domain)
            assert "motion-fade-up" in rec.css_effects or "motion" in rec.primary_style

    def test_google_fonts_url_has_display_swap(self, engine):
        for domain in ["healthcare", "fintech", "ecommerce"]:
            rec = engine.recommend(domain)
            assert "display=swap" in rec.google_fonts_url

    def test_dark_mode_default_for_iot(self, engine):
        rec = engine.recommend("iot_smart_city")
        assert rec.dark_mode_default is True

    def test_dark_mode_default_off_for_healthcare(self, engine):
        rec = engine.recommend("healthcare")
        assert rec.dark_mode_default is False


# ── Style Definitions ────────────────────────────────────────────

class TestStyleDefinitions:
    """Validate the built-in UI style definitions."""

    def test_minimum_styles_available(self):
        assert len(_UI_STYLES) >= 10

    def test_each_style_has_css_effects(self):
        for key, style in _UI_STYLES.items():
            assert style.css_effects, f"Style {key} has no CSS effects"
            assert style.name
            assert style.description

    def test_glassmorphism_has_backdrop_blur(self):
        assert "backdrop-filter" in _UI_STYLES["glassmorphism"].css_effects

    def test_neumorphism_has_box_shadow(self):
        assert "box-shadow" in _UI_STYLES["neumorphism"].css_effects

    def test_aurora_has_gradient(self):
        assert "gradient" in _UI_STYLES["aurora"].css_effects.lower()

    def test_motion_driven_has_keyframes(self):
        css = _UI_STYLES["motion_driven"].css_effects
        assert "@keyframes" in css
        assert "motion-fade-up" in css


# ── Font Pairings ────────────────────────────────────────────────

class TestFontPairings:
    """Validate font pairing definitions."""

    def test_minimum_pairings_available(self):
        assert len(_FONT_PAIRINGS) >= 10

    def test_each_pairing_has_google_import(self):
        for key, fp in _FONT_PAIRINGS.items():
            assert fp.google_import, f"Font pairing {key} missing google_import"
            assert fp.heading
            assert fp.body
            assert fp.mood

    def test_font_matching_by_domain(self, engine):
        """Healthcare should get a readable/warm font."""
        rec = engine.recommend("healthcare")
        mood = rec.font_pairing.mood.lower()
        assert any(w in mood for w in ["readable", "warm", "approachable", "friendly"])

    def test_font_matching_fintech(self, engine):
        """Fintech should get a clean/technical font."""
        rec = engine.recommend("fintech")
        mood = rec.font_pairing.mood.lower()
        assert any(w in mood for w in ["clean", "technical", "modern", "precise"])


# ── Industry Rules ───────────────────────────────────────────────

class TestIndustryRules:
    """Validate industry-specific design reasoning rules."""

    def test_minimum_rules_available(self):
        assert len(_INDUSTRY_RULES) >= 10

    def test_each_rule_has_required_fields(self):
        for domain, rule in _INDUSTRY_RULES.items():
            assert rule.recommended_styles, f"Domain {domain} has no recommended styles"
            assert rule.font_mood, f"Domain {domain} has no font_mood"
            assert rule.anti_patterns, f"Domain {domain} has no anti_patterns"
            assert rule.key_effects, f"Domain {domain} has no key_effects"
            assert rule.landing_pattern, f"Domain {domain} has no landing_pattern"

    def test_healthcare_no_red_primary(self):
        rule = _INDUSTRY_RULES["healthcare"]
        anti = " ".join(rule.anti_patterns).lower()
        assert "red" in anti

    def test_fintech_no_playful(self):
        rule = _INDUSTRY_RULES["fintech"]
        anti = " ".join(rule.anti_patterns).lower()
        assert "playful" in anti


# ── Quality Checklist ────────────────────────────────────────────

class TestQualityChecklist:
    def test_checklist_has_items(self):
        assert len(QUALITY_CHECKLIST) >= 10

    def test_contrast_ratio_mentioned(self):
        combined = " ".join(QUALITY_CHECKLIST)
        assert "4.5:1" in combined

    def test_reduced_motion_mentioned(self):
        combined = " ".join(QUALITY_CHECKLIST)
        assert "reduced-motion" in combined


# ── Style-to-Class Mapping ──────────────────────────────────────

class TestStyleClassMapping:
    """Test the _get_style_classes helper in frontend_generator."""

    def test_all_known_styles_have_mapping(self):
        for style_key in _UI_STYLES:
            classes = _get_style_classes(style_key)
            assert isinstance(classes, dict)
            assert "card" in classes
            assert "container" in classes

    def test_glassmorphism_card_class(self):
        cls = _get_style_classes("glassmorphism")
        assert cls["card"] == "glass-card"
        assert cls["header"] == "glass-header"

    def test_neumorphism_card_class(self):
        cls = _get_style_classes("neumorphism")
        assert cls["card"] == "neu-card"

    def test_bento_grid_has_bento_class(self):
        cls = _get_style_classes("bento_grid")
        assert "bento" in cls["kpi_grid"]

    def test_aurora_has_container_class(self):
        cls = _get_style_classes("aurora")
        assert cls["container"] == "aurora-bg"

    def test_unknown_style_returns_fallback(self):
        cls = _get_style_classes("nonexistent_style")
        assert isinstance(cls, dict)
        assert "card" in cls

    def test_motion_driven_has_motion_classes(self):
        cls = _get_style_classes("motion_driven")
        assert "motion" in cls["motion_container"]
        assert "motion" in cls["motion_item"]


# ── Integration with DesignSystem ────────────────────────────────

class TestDesignSystemIntegration:
    """Test that the style engine integrates with DesignSystem tokens."""

    def test_design_tokens_have_ui_style(self):
        from src.orchestrator.generators.design_system import DesignSystem

        ds = DesignSystem()
        spec = _make_spec("test-health", "Hospital management system")
        tokens = ds.generate_tokens(spec)
        assert hasattr(tokens, 'ui_style')
        assert tokens.ui_style

    def test_css_effects_injected_into_css(self):
        from src.orchestrator.generators.design_system import DesignSystem

        ds = DesignSystem()
        spec = _make_spec("test-health", "Hospital management system")
        tokens = ds.generate_tokens(spec)
        css = ds.generate_css_variables(tokens)
        assert "--ui-style" in css
        assert "--font-heading-family" in css
        assert "--font-body-family" in css

    def test_google_fonts_url_set(self):
        from src.orchestrator.generators.design_system import DesignSystem

        ds = DesignSystem()
        spec = _make_spec("test-ecommerce", "Online shopping platform")
        tokens = ds.generate_tokens(spec)
        assert tokens.google_fonts_url
        assert "googleapis" in tokens.google_fonts_url

    def test_different_domains_get_different_styles(self):
        from src.orchestrator.generators.design_system import DesignSystem

        ds = DesignSystem()
        spec_health = _make_spec("hospital-mgmt", "Hospital patient management system")
        spec_fintech = _make_spec("trading-platform", "Financial trading platform for stocks")

        tokens_health = ds.generate_tokens(spec_health)
        tokens_fintech = ds.generate_tokens(spec_fintech)

        # Different domains should get different style recommendations
        assert tokens_health.ui_style != tokens_fintech.ui_style or \
               tokens_health.font_heading != tokens_fintech.font_heading
