"""Tests for DeploymentProfile & SKUSelector -- Phase 4-5."""

from __future__ import annotations

import pytest

from src.orchestrator.generators.deployment_profile import (
    DeploymentProfile,
    SKUSelector,
    SKUSpec,
    WorkloadClass,
    profile_to_markdown,
)
from src.orchestrator.intent_schema import ComputeTarget, DataStore, IntentSpec


def _make_spec(**kwargs) -> IntentSpec:
    defaults = {
        "project_name": "test-project",
        "description": "Test project",
        "raw_intent": "test intent",
    }
    defaults.update(kwargs)
    return IntentSpec(**defaults)


class TestWorkloadClassification:
    """Tests for SKUSelector.classify_workload."""

    def test_dev_environment(self) -> None:
        spec = _make_spec(environment="dev")
        assert SKUSelector.classify_workload(spec) == WorkloadClass.DEV

    def test_staging_environment(self) -> None:
        spec = _make_spec(environment="staging")
        assert SKUSelector.classify_workload(spec) == WorkloadClass.STAGING

    def test_prod_low(self) -> None:
        spec = _make_spec(environment="prod")
        assert SKUSelector.classify_workload(spec) == WorkloadClass.PRODUCTION_LOW

    def test_prod_high_with_ai(self) -> None:
        spec = _make_spec(environment="prod", uses_ai=True)
        assert SKUSelector.classify_workload(spec) == WorkloadClass.PRODUCTION_HIGH

    def test_prod_high_with_many_entities(self) -> None:
        from src.orchestrator.intent_schema import EntitySpec
        entities = [EntitySpec(name=f"Entity{i}") for i in range(10)]
        spec = _make_spec(environment="prod", entities=entities)
        assert SKUSelector.classify_workload(spec) == WorkloadClass.PRODUCTION_HIGH


class TestSKUSelector:
    """Tests for SKUSelector.select."""

    def test_dev_container_apps(self) -> None:
        spec = _make_spec(compute_target=ComputeTarget.CONTAINER_APPS)
        profile = SKUSelector.select(spec)
        assert profile.environment == "dev"
        assert profile.workload_class == WorkloadClass.DEV
        assert profile.compute.resource == "Container App"
        assert profile.registry is not None

    def test_dev_functions_no_registry(self) -> None:
        spec = _make_spec(compute_target=ComputeTarget.FUNCTIONS)
        profile = SKUSelector.select(spec)
        assert profile.registry is None
        assert profile.compute.resource == "Function App"

    def test_dev_app_service(self) -> None:
        spec = _make_spec(compute_target=ComputeTarget.APP_SERVICE)
        profile = SKUSelector.select(spec)
        assert profile.compute.resource == "App Service Plan"
        assert profile.registry is not None

    def test_data_stores_included(self) -> None:
        spec = _make_spec(data_stores=[DataStore.BLOB_STORAGE, DataStore.COSMOS_DB])
        profile = SKUSelector.select(spec)
        ds_names = [ds.resource for ds in profile.data_stores]
        assert "Blob Storage" in ds_names
        assert "Cosmos DB" in ds_names

    def test_ai_services_included(self) -> None:
        spec = _make_spec(uses_ai=True, data_stores=[DataStore.AI_SEARCH])
        profile = SKUSelector.select(spec)
        assert len(profile.ai_services) >= 1
        ai_names = [s.resource for s in profile.ai_services]
        assert "Azure OpenAI" in ai_names

    def test_total_monthly_is_sum(self) -> None:
        spec = _make_spec()
        profile = SKUSelector.select(spec)
        computed = sum(s.monthly_usd for s in profile.all_items)
        assert abs(profile.total_monthly - computed) < 0.01

    def test_core_infra_always_present(self) -> None:
        spec = _make_spec()
        profile = SKUSelector.select(spec)
        assert profile.log_analytics is not None
        assert profile.key_vault is not None
        assert profile.identity is not None

    def test_none_datastore_excluded(self) -> None:
        spec = _make_spec(data_stores=[DataStore.NONE])
        profile = SKUSelector.select(spec)
        assert len(profile.data_stores) == 0


class TestDeploymentProfileMarkdown:
    """Tests for profile_to_markdown rendering."""

    def test_markdown_contains_header(self) -> None:
        spec = _make_spec()
        profile = SKUSelector.select(spec)
        md = profile_to_markdown(profile)
        assert "# Estimated Monthly Cost" in md

    def test_markdown_contains_environment(self) -> None:
        spec = _make_spec(environment="staging")
        profile = SKUSelector.select(spec)
        md = profile_to_markdown(profile)
        assert "staging" in md

    def test_markdown_contains_total(self) -> None:
        spec = _make_spec()
        profile = SKUSelector.select(spec)
        md = profile_to_markdown(profile)
        assert "**Total**" in md

    def test_markdown_table_format(self) -> None:
        spec = _make_spec()
        profile = SKUSelector.select(spec)
        md = profile_to_markdown(profile)
        assert "| Resource |" in md
        assert "| SKU / Tier |" in md


class TestSKUSpec:
    """Tests for SKUSpec data class."""

    def test_frozen(self) -> None:
        sku = SKUSpec("Resource", "Standard", "dev", 10.0)
        with pytest.raises(AttributeError):
            sku.resource = "Modified"  # type: ignore[misc]

    def test_default_notes(self) -> None:
        sku = SKUSpec("Resource", "Standard", "dev", 10.0)
        assert sku.notes == ""

    def test_notes_set(self) -> None:
        sku = SKUSpec("Resource", "Standard", "dev", 10.0, "Test note")
        assert sku.notes == "Test note"
