"""Tests for DomainContext -- Phase 2 domain intelligence model."""

from __future__ import annotations

import pytest

from src.orchestrator.generators.domain_context import (
    DomainContext,
    build_domain_context,
)
from src.orchestrator.intent_schema import DomainType, IntentSpec


def _make_spec(**kwargs) -> IntentSpec:
    defaults = {
        "project_name": "test-project",
        "description": "Test project",
        "raw_intent": "test intent",
    }
    defaults.update(kwargs)
    return IntentSpec(**defaults)


class TestBuildDomainContext:
    """Tests for build_domain_context factory."""

    def test_generic_domain_returns_context(self) -> None:
        spec = _make_spec(domain_type=DomainType.GENERIC)
        ctx = build_domain_context(spec)
        assert isinstance(ctx, DomainContext)
        assert ctx.domain_type == DomainType.GENERIC

    def test_healthcare_domain(self) -> None:
        spec = _make_spec(domain_type=DomainType.HEALTHCARE)
        ctx = build_domain_context(spec)
        assert ctx.domain_type == DomainType.HEALTHCARE
        assert len(ctx.email_domains) > 0
        assert len(ctx.first_names) > 0
        assert len(ctx.last_names) > 0
        assert len(ctx.compliance_frameworks) > 0

    def test_legal_domain(self) -> None:
        spec = _make_spec(domain_type=DomainType.LEGAL)
        ctx = build_domain_context(spec)
        assert ctx.domain_type == DomainType.LEGAL
        assert ctx.org_name != ""

    def test_all_domains_produce_valid_context(self) -> None:
        for dt in DomainType:
            spec = _make_spec(domain_type=dt)
            ctx = build_domain_context(spec)
            assert ctx is not None
            assert ctx.domain_type == dt
            assert len(ctx.first_names) >= 5
            assert len(ctx.last_names) >= 5
            assert len(ctx.statuses) >= 3
            assert ctx.support_email != ""

    def test_context_is_frozen(self) -> None:
        spec = _make_spec(domain_type=DomainType.HEALTHCARE)
        ctx = build_domain_context(spec)
        with pytest.raises(AttributeError):
            ctx.org_name = "modified"  # type: ignore[misc]

    def test_cybersecurity_domain(self) -> None:
        spec = _make_spec(domain_type=DomainType.CYBERSECURITY)
        ctx = build_domain_context(spec)
        assert ctx.domain_type == DomainType.CYBERSECURITY
        assert len(ctx.vendors) > 0
        assert len(ctx.source_systems) > 0

    def test_iot_smart_city_domain(self) -> None:
        spec = _make_spec(domain_type=DomainType.IOT_SMART_CITY)
        ctx = build_domain_context(spec)
        assert ctx.domain_type == DomainType.IOT_SMART_CITY

    def test_logistics_domain(self) -> None:
        spec = _make_spec(domain_type=DomainType.LOGISTICS)
        ctx = build_domain_context(spec)
        assert ctx.domain_type == DomainType.LOGISTICS

    def test_retail_domain(self) -> None:
        spec = _make_spec(domain_type=DomainType.RETAIL)
        ctx = build_domain_context(spec)
        assert ctx.domain_type == DomainType.RETAIL

    def test_manufacturing_domain(self) -> None:
        spec = _make_spec(domain_type=DomainType.MANUFACTURING)
        ctx = build_domain_context(spec)
        assert ctx.domain_type == DomainType.MANUFACTURING

    def test_agriculture_domain(self) -> None:
        spec = _make_spec(domain_type=DomainType.AGRICULTURE)
        ctx = build_domain_context(spec)
        assert ctx.domain_type == DomainType.AGRICULTURE

    def test_government_domain(self) -> None:
        spec = _make_spec(domain_type=DomainType.GOVERNMENT)
        ctx = build_domain_context(spec)
        assert ctx.domain_type == DomainType.GOVERNMENT

    def test_finance_domain(self) -> None:
        spec = _make_spec(domain_type=DomainType.FINANCE)
        ctx = build_domain_context(spec)
        assert ctx.domain_type == DomainType.FINANCE

    def test_description_templates_non_empty(self) -> None:
        for dt in DomainType:
            spec = _make_spec(domain_type=dt)
            ctx = build_domain_context(spec)
            assert len(ctx.description_templates) >= 3


class TestDomainContextFields:
    """Tests for DomainContext field structure."""

    def test_terminology_is_dict(self) -> None:
        spec = _make_spec(domain_type=DomainType.HEALTHCARE)
        ctx = build_domain_context(spec)
        assert isinstance(ctx.terminology, dict)

    def test_portal_urls_non_empty(self) -> None:
        spec = _make_spec(domain_type=DomainType.HEALTHCARE)
        ctx = build_domain_context(spec)
        assert len(ctx.portal_urls) > 0

    def test_cities_and_streets_populated(self) -> None:
        spec = _make_spec(domain_type=DomainType.IOT_SMART_CITY)
        ctx = build_domain_context(spec)
        assert len(ctx.cities) >= 5
        assert len(ctx.streets) >= 5
