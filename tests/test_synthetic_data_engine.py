"""Tests for the Synthea-inspired synthetic data engine."""

import pytest
from datetime import datetime, timezone

from src.orchestrator.generators.synthetic_data_engine import (
    SyntheticDataConfig,
    generate_name,
    generate_clustered_timestamp,
    simulate_lifecycle,
    get_domain_code,
    correlated_value,
    generate_cross_entity_fk,
    generate_address,
    generate_phone,
    generate_email,
    generate_vital_sign,
    select_weighted,
    _deterministic_hash,
    FIRST_NAMES_WEIGHTED,
    LAST_NAMES_WEIGHTED,
    LIFECYCLE_PATTERNS,
    DOMAIN_CODES,
    SEVERITY_CORRELATIONS,
)


class TestDeterministicHash:
    """Hash reproducibility -- core requirement for synthetic data."""

    def test_same_inputs_produce_same_output(self):
        assert _deterministic_hash("a", 1, "f") == _deterministic_hash("a", 1, "f")

    def test_different_inputs_produce_different_output(self):
        assert _deterministic_hash("a", 1) != _deterministic_hash("b", 1)

    def test_row_sensitivity(self):
        assert _deterministic_hash("e", 1) != _deterministic_hash("e", 2)


class TestDemographicNames:
    """Synthea-style weighted demographic name generation."""

    def test_generates_first_and_last(self):
        first, last = generate_name(1, "Patient")
        assert first in [n for n, _ in FIRST_NAMES_WEIGHTED]
        assert last in [n for n, _ in LAST_NAMES_WEIGHTED]

    def test_deterministic_across_calls(self):
        assert generate_name(1, "Patient") == generate_name(1, "Patient")

    def test_different_rows_produce_unique_names(self):
        names = {generate_name(r, "Patient") for r in range(1, 20)}
        assert len(names) > 5  # should have reasonable diversity from 19 rows

    def test_different_entities_produce_different_names(self):
        assert generate_name(1, "Patient") != generate_name(1, "Doctor")

    def test_weighted_distribution_covers_pool(self):
        """Over many rows, all weighted names should appear (coverage)."""
        firsts = {generate_name(r, "TestEntity")[0] for r in range(1, 100)}
        assert len(firsts) >= 10  # at least 10 of 30 names represented


class TestClusteredTimestamps:
    """Timestamps should cluster around business hours, not even spread."""

    def test_generates_datetime_object(self):
        ts = generate_clustered_timestamp(1, 12, "Order")
        assert isinstance(ts, datetime)

    def test_within_spread_range(self):
        now = datetime(2025, 6, 15, 12, 0, tzinfo=timezone.utc)
        ts = generate_clustered_timestamp(1, 12, "Order", spread_days=90, base_time=now)
        delta = now - ts
        assert 0 <= delta.days <= 95  # within spread + jitter

    @pytest.mark.parametrize("row", [1, 6, 12])
    def test_deterministic(self, row):
        t1 = generate_clustered_timestamp(row, 12, "E")
        t2 = generate_clustered_timestamp(row, 12, "E")
        assert t1 == t2

    def test_business_hours_bias(self):
        """Majority of timestamps should fall during business hours (6-20)."""
        hours = [generate_clustered_timestamp(r, 50, "E").hour for r in range(1, 51)]
        business_hours = sum(1 for h in hours if 6 <= h <= 20)
        assert business_hours / len(hours) > 0.6  # >60% in business hours


class TestLifecycleSimulation:
    """State machine lifecycle (Synthea Generic Module Framework inspired)."""

    @pytest.mark.parametrize("pattern", list(LIFECYCLE_PATTERNS.keys()))
    def test_all_patterns_return_valid_status(self, pattern):
        status, history = simulate_lifecycle(pattern, 1, pattern)
        assert isinstance(status, str)
        assert len(status) > 0

    def test_history_contains_transitions(self):
        status, history = simulate_lifecycle("order", 1, "order")
        assert isinstance(history, list)
        assert len(history) >= 1
        for from_s, to_s, hours in history:
            assert isinstance(from_s, str)
            assert isinstance(to_s, str)
            assert hours >= 0

    def test_deterministic(self):
        s1, h1 = simulate_lifecycle("incident", 5, "cyber")
        s2, h2 = simulate_lifecycle("incident", 5, "cyber")
        assert s1 == s2
        assert h1 == h2

    def test_different_rows_may_end_at_different_states(self):
        statuses = {simulate_lifecycle("ticket", r)[0] for r in range(1, 20)}
        assert len(statuses) >= 2  # not everyone ends at same state


class TestDomainCodes:
    """Domain-specific coding systems (ICD-10, SKU, tracking numbers)."""

    @pytest.mark.parametrize("domain,code_type", [
        ("healthcare", "diagnosis_code"),
        ("healthcare", "procedure_code"),
        ("healthcare", "medication"),
        ("logistics", "tracking_number"),
        ("retail", "sku"),
        ("finance", "instrument"),
    ])
    def test_returns_code_and_description(self, domain, code_type):
        result = get_domain_code(domain, code_type, 1, "TestEntity")
        assert result is not None
        code, desc = result
        assert len(code) > 0
        assert len(desc) > 0

    def test_unknown_domain_returns_none(self):
        assert get_domain_code("unknown", "diagnosis_code", 1, "E") is None

    def test_deterministic(self):
        r1 = get_domain_code("healthcare", "diagnosis_code", 3, "Patient")
        r2 = get_domain_code("healthcare", "diagnosis_code", 3, "Patient")
        assert r1 == r2


class TestCorrelatedValues:
    """Severity ↔ response time / cost correlation."""

    def test_critical_has_shorter_response(self):
        crit = correlated_value("critical", "response_hours", 1, "E")
        low = correlated_value("low", "response_hours", 1, "E")
        assert crit < low  # critical responds faster

    def test_critical_has_higher_cost(self):
        crit = correlated_value("critical", "cost_multiplier", 1, "E")
        low = correlated_value("low", "cost_multiplier", 1, "E")
        assert crit > low

    @pytest.mark.parametrize("severity", ["critical", "high", "medium", "low"])
    def test_all_severities_produce_float(self, severity):
        val = correlated_value(severity, "impact_score", 1, "E")
        assert isinstance(val, float)
        assert 0.0 <= val <= 1.0


class TestCrossEntityFK:
    """Cross-entity foreign key verification."""

    def test_fk_references_valid_target_row(self):
        fk = generate_cross_entity_fk("Patient", 1, 12, "Encounter")
        assert fk.startswith("patient-")
        row_num = int(fk.split("-")[1])
        assert 1 <= row_num <= 12

    def test_deterministic(self):
        fk1 = generate_cross_entity_fk("Order", 5, 12, "LineItem")
        fk2 = generate_cross_entity_fk("Order", 5, 12, "LineItem")
        assert fk1 == fk2

    def test_different_sources_may_reference_different_targets(self):
        fks = {generate_cross_entity_fk("Patient", r, 12, "Encounter") for r in range(1, 13)}
        assert len(fks) >= 3  # not all pointing to same target


class TestRealisticValueGenerators:
    """Address, phone, email, vital sign generators."""

    def test_address_looks_realistic(self):
        addr = generate_address(1, "Patient")
        assert "," in addr  # has city separator
        parts = addr.split(",")
        assert len(parts) >= 2

    def test_phone_is_safe_555_prefix(self):
        phone = generate_phone(1, "Patient")
        assert "555" in phone  # safe for testing (not real numbers)
        assert phone.startswith("+1-")

    def test_email_uses_name_components(self):
        email = generate_email("James", "Smith", "test.com")
        assert email == "james.smith@test.com"

    @pytest.mark.parametrize("vital", ["systolic_bp", "heart_rate", "temperature", "bmi", "blood_oxygen"])
    def test_vital_signs_in_realistic_range(self, vital):
        val = generate_vital_sign(vital, 1, "Patient")
        assert isinstance(val, float)
        assert val > 0


class TestSyntheticDataConfig:
    """Configuration dataclass."""

    def test_defaults(self):
        cfg = SyntheticDataConfig()
        assert cfg.record_count == 12
        assert cfg.spread_days == 90
        assert cfg.temporal_clustering is True

    def test_custom_record_count(self):
        cfg = SyntheticDataConfig(record_count=100)
        assert cfg.record_count == 100


class TestSelectWeighted:
    """Weighted selection from distributions."""

    def test_returns_item_from_list(self):
        items = [("a", 0.5), ("b", 0.3), ("c", 0.2)]
        result = select_weighted(items, 100)
        assert result in ["a", "b", "c"]

    def test_deterministic(self):
        items = [("x", 0.7), ("y", 0.3)]
        r1 = select_weighted(items, 42)
        r2 = select_weighted(items, 42)
        assert r1 == r2
