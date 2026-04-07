"""Tests for Test Generator and Alert Generator superpowers (consolidated)."""

from __future__ import annotations

import pytest

from src.orchestrator.generators.alert_generator import AlertGenerator
from src.orchestrator.generators.test_generator import ScaffoldTestGenerator
from src.orchestrator.intent_schema import (
    AppType,
    AuthModel,
    CICDRequirements,
    ComplianceFramework,
    DataStore,
    IntentSpec,
    NetworkingModel,
    ObservabilityRequirements,
    SecurityRequirements,
)


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
        cicd=CICDRequirements(
            oidc_auth=True,
        ),
        azure_region="eastus2",
        resource_group_name="rg-test",
        environment="dev",
        confidence=0.85,
    )


# ----------------- Test Generator -----------------


class TestTestGenerator:
    def setup_method(self) -> None:
        self.gen = ScaffoldTestGenerator()

    @pytest.mark.parametrize("filepath,content_keyword", [
        ("tests/conftest.py", "@pytest.fixture"),
        ("tests/__init__.py", None),
        ("tests/test_health.py", "test_health"),
        ("tests/test_api.py", "def test_"),
        ("tests/test_security.py", None),
        ("tests/test_config.py", None),
        ("tests/requirements-test.txt", "pytest"),
    ])
    def test_generates_expected_files(self, filepath, content_keyword) -> None:
        files = self.gen.generate(_make_spec())
        assert filepath in files
        if content_keyword:
            assert content_keyword in files[filepath]

    def test_generates_health_test_with_200(self) -> None:
        files = self.gen.generate(_make_spec())
        assert "200" in files["tests/test_health.py"]

    def test_with_blob_storage_adds_storage_tests(self) -> None:
        files = self.gen.generate(_make_spec(data_stores=[DataStore.BLOB_STORAGE]))
        assert "tests/test_storage.py" in files
        assert "storage" in files["tests/test_storage.py"].lower()

    def test_without_blob_storage_no_storage_tests(self) -> None:
        files = self.gen.generate(_make_spec())
        assert "tests/test_storage.py" not in files

    def test_conftest_has_client_fixture(self) -> None:
        files = self.gen.generate(_make_spec())
        content = files["tests/conftest.py"]
        assert "client" in content


# ----------------- Alert Generator -----------------


class TestAlertGenerator:
    def setup_method(self) -> None:
        self.gen = AlertGenerator()

    @pytest.mark.parametrize("filepath,content_keyword", [
        ("infra/modules/alerts.bicep", "Microsoft.Insights/metricAlerts"),
        ("infra/modules/action-group.bicep", "emailReceivers"),
        ("docs/alerting-runbook.md", None),
    ])
    def test_generates_expected_files(self, filepath, content_keyword) -> None:
        files = self.gen.generate(_make_spec())
        assert filepath in files
        if content_keyword:
            assert content_keyword in files[filepath]

    def test_alerts_bicep_has_scheduled_query(self) -> None:
        files = self.gen.generate(_make_spec())
        assert "Microsoft.Insights/scheduledQueryRules" in files["infra/modules/alerts.bicep"]

    def test_runbook_has_severity_table(self) -> None:
        files = self.gen.generate(_make_spec())
        content = files["docs/alerting-runbook.md"]
        assert "Severity" in content or "severity" in content

    def test_with_blob_storage_adds_storage_alerts(self) -> None:
        files = self.gen.generate(_make_spec(data_stores=[DataStore.BLOB_STORAGE]))
        content = files["infra/modules/alerts.bicep"]
        assert "storage" in content.lower() or "Availability" in content

    def test_alerts_bicep_has_parameters(self) -> None:
        files = self.gen.generate(_make_spec())
        assert "param" in files["infra/modules/alerts.bicep"]

    def test_alert_names_use_project_name(self) -> None:
        files = self.gen.generate(_make_spec())
        content = files["infra/modules/alerts.bicep"]
        assert "test-project" in content or "testproject" in content.lower() or "name:" in content
