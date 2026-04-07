"""Tests for new features -- multi-language, multi-compute, cost estimation, intent detection.

Consolidated: parameterized tests replace per-language/per-target repetition.
"""

from __future__ import annotations

import pytest

from src.orchestrator.agents.intent_parser import IntentParserAgent
from src.orchestrator.config import AppConfig, AzureConfig, CopilotConfig, LLMConfig
from src.orchestrator.generators.app_generator import AppGenerator
from src.orchestrator.generators.bicep_generator import BicepGenerator
from src.orchestrator.generators.cost_estimator import CostEstimate, CostEstimator
from src.orchestrator.intent_schema import (
    LANGUAGE_FRAMEWORKS,
    AppType,
    AuthModel,
    CICDRequirements,
    ComplianceFramework,
    ComponentSpec,
    ComputeTarget,
    DataStore,
    IntentSpec,
    NetworkingModel,
    ObservabilityRequirements,
    PlanOutput,
    SecurityRequirements,
    ThreatEntry,
)


def _make_config() -> AppConfig:
    return AppConfig(
        azure=AzureConfig(
            subscription_id="00000000-0000-0000-0000-000000000000",
            resource_group="rg-test",
            location="eastus2",
        ),
        copilot=CopilotConfig(github_token=""),
        llm=LLMConfig(
            provider="template-only",
            model="none",
            azure_openai_endpoint="",
            azure_openai_api_key="",
            azure_openai_deployment="gpt-4o",
        ),
        log_level="WARNING",
    )


def _make_spec(
    language: str = "python",
    compute_target: ComputeTarget = ComputeTarget.CONTAINER_APPS,
    data_stores: list[DataStore] | None = None,
) -> IntentSpec:
    return IntentSpec(
        project_name="test-project",
        app_type=AppType.API,
        description="A test API service",
        raw_intent="Build a test API",
        language=language,
        framework=LANGUAGE_FRAMEWORKS.get(language, "fastapi"),
        compute_target=compute_target,
        data_stores=data_stores or [],
        security=SecurityRequirements(
            auth_model=AuthModel.MANAGED_IDENTITY,
            compliance_framework=ComplianceFramework.GENERAL,
            data_classification="internal",
            networking=NetworkingModel.PRIVATE,
        ),
        observability=ObservabilityRequirements(log_analytics=True, health_endpoint=True),
        cicd=CICDRequirements(oidc_auth=True),
        azure_region="eastus2",
        resource_group_name="rg-test",
        environment="dev",
        confidence=0.85,
    )


def _make_plan() -> PlanOutput:
    return PlanOutput(
        title="Test Architecture Plan",
        summary="Test plan",
        components=[
            ComponentSpec(
                name="compute",
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


# ===================================================================
# Multi-Language App Generator
# ===================================================================


class TestMultiLanguageAppGenerator:
    """Test that AppGenerator routes correctly by language (parameterized)."""

    def setup_method(self) -> None:
        self.gen = AppGenerator()

    @pytest.mark.parametrize("language,main_file,dep_file", [
        ("python", "src/app/main.py", "src/app/requirements.txt"),
        ("node", "src/app/index.js", "src/app/package.json"),
        ("dotnet", "src/app/Program.cs", None),
    ])
    def test_generates_main_and_deps(self, language, main_file, dep_file) -> None:
        files = self.gen.generate(_make_spec(language=language))
        assert main_file in files
        if dep_file:
            assert dep_file in files

    @pytest.mark.parametrize("language,main_file,keyword", [
        ("python", "src/app/main.py", "FastAPI"),
        ("node", "src/app/index.js", "express"),
        ("dotnet", "src/app/Program.cs", "/health"),
    ])
    def test_main_has_framework_keyword(self, language, main_file, keyword) -> None:
        files = self.gen.generate(_make_spec(language=language))
        assert keyword in files[main_file]

    @pytest.mark.parametrize("language,image_keyword", [
        ("python", "python:"),
        ("node", "node:"),
        ("dotnet", "dotnet"),
    ])
    def test_dockerfile_has_language_image(self, language, image_keyword) -> None:
        files = self.gen.generate(_make_spec(language=language))
        assert image_keyword in files["src/app/Dockerfile"].lower()

    def test_node_root_has_html_landing_page(self) -> None:
        files = self.gen.generate(_make_spec(language="node"))
        index_js = files["src/app/index.js"]
        assert "<!DOCTYPE html>" in index_js
        assert "res.send(html)" in index_js

    @pytest.mark.parametrize("language,main_file", [
        ("node", "src/app/index.js"),
        ("dotnet", "src/app/Program.cs"),
    ])
    def test_supports_key_vault_uri(self, language, main_file) -> None:
        files = self.gen.generate(_make_spec(language=language))
        content = files[main_file]
        assert "KEY_VAULT_URI" in content
        assert "KEY_VAULT_NAME" in content

    def test_dotnet_generates_csproj(self) -> None:
        files = self.gen.generate(_make_spec(language="dotnet"))
        assert any(f.endswith(".csproj") for f in files)

    def test_dotnet_generates_appsettings(self) -> None:
        files = self.gen.generate(_make_spec(language="dotnet"))
        assert "src/app/appsettings.json" in files

    def test_dotnet_root_has_html_landing_page(self) -> None:
        files = self.gen.generate(_make_spec(language="dotnet"))
        program_cs = files["src/app/Program.cs"]
        assert "<!DOCTYPE html>" in program_cs
        assert 'Results.Content(html, "text/html")' in program_cs


# ===================================================================
# Multi-Compute Target Bicep Generator
# ===================================================================


class TestMultiComputeBicepGenerator:
    """Test Bicep generator routes correctly by compute target (parameterized)."""

    def setup_method(self) -> None:
        self.gen = BicepGenerator()

    @pytest.mark.parametrize("target,expected_module,keyword_in_main", [
        (ComputeTarget.CONTAINER_APPS, "infra/bicep/modules/container-app.bicep", "container"),
        (ComputeTarget.APP_SERVICE, "infra/bicep/modules/app-service.bicep", "app_service"),
        (ComputeTarget.FUNCTIONS, "infra/bicep/modules/function-app.bicep", "functions"),
    ])
    def test_target_generates_correct_module(self, target, expected_module, keyword_in_main) -> None:
        spec = _make_spec(compute_target=target)
        files = self.gen.generate(spec, _make_plan())
        assert expected_module in files
        assert keyword_in_main in files["infra/bicep/main.bicep"].lower()

    def test_container_apps_generates_acr(self) -> None:
        spec = _make_spec(compute_target=ComputeTarget.CONTAINER_APPS)
        files = self.gen.generate(spec, _make_plan())
        assert "infra/bicep/modules/container-registry.bicep" in files

    @pytest.mark.parametrize("target", [ComputeTarget.APP_SERVICE, ComputeTarget.FUNCTIONS])
    def test_non_container_targets_skip_acr(self, target) -> None:
        files = self.gen.generate(_make_spec(compute_target=target), _make_plan())
        assert "infra/bicep/modules/container-registry.bicep" not in files

    def test_app_service_module_has_plan(self) -> None:
        files = self.gen.generate(_make_spec(compute_target=ComputeTarget.APP_SERVICE), _make_plan())
        assert "serverfarms" in files["infra/bicep/modules/app-service.bicep"]

    def test_functions_module_has_consumption(self) -> None:
        files = self.gen.generate(_make_spec(compute_target=ComputeTarget.FUNCTIONS), _make_plan())
        bicep = files["infra/bicep/modules/function-app.bicep"]
        assert "Dynamic" in bicep or "Y1" in bicep

    @pytest.mark.parametrize("component", [
        "infra/bicep/modules/keyvault.bicep",
        "infra/bicep/modules/log-analytics.bicep",
        "infra/bicep/modules/managed-identity.bicep",
    ])
    def test_always_has_core_modules(self, component) -> None:
        for target in ComputeTarget:
            files = self.gen.generate(_make_spec(compute_target=target), _make_plan())
            assert component in files, f"Missing {component} for {target}"


# ===================================================================
# Cost Estimator
# ===================================================================


class TestCostEstimator:
    """Test cost estimation for different architectures."""

    def setup_method(self) -> None:
        self.est = CostEstimator()

    def test_returns_cost_estimate(self) -> None:
        result = self.est.estimate(_make_spec(), _make_plan())
        assert isinstance(result, CostEstimate)

    def test_has_items(self) -> None:
        result = self.est.estimate(_make_spec(), _make_plan())
        assert len(result.items) > 0

    def test_total_is_sum_of_items(self) -> None:
        result = self.est.estimate(_make_spec(), _make_plan())
        assert result.total_monthly == sum(i.monthly_usd for i in result.items)

    def test_container_apps_includes_acr(self) -> None:
        result = self.est.estimate(_make_spec(compute_target=ComputeTarget.CONTAINER_APPS), _make_plan())
        resources = [i.resource for i in result.items]
        assert "Container Registry" in resources

    def test_app_service_cheaper_than_container_apps(self) -> None:
        ca_cost = self.est.estimate(_make_spec(compute_target=ComputeTarget.CONTAINER_APPS), _make_plan()).total_monthly
        as_cost = self.est.estimate(_make_spec(compute_target=ComputeTarget.APP_SERVICE), _make_plan()).total_monthly
        assert as_cost < ca_cost

    def test_functions_cheapest(self) -> None:
        fn_cost = self.est.estimate(_make_spec(compute_target=ComputeTarget.FUNCTIONS), _make_plan()).total_monthly
        ca_cost = self.est.estimate(_make_spec(compute_target=ComputeTarget.CONTAINER_APPS), _make_plan()).total_monthly
        assert fn_cost < ca_cost

    def test_blob_storage_adds_cost(self) -> None:
        no_blob = self.est.estimate(_make_spec(data_stores=[]), _make_plan()).total_monthly
        with_blob = self.est.estimate(_make_spec(data_stores=[DataStore.BLOB_STORAGE]), _make_plan()).total_monthly
        assert with_blob > no_blob

    def test_multiple_data_stores_additive(self) -> None:
        one_store = self.est.estimate(_make_spec(data_stores=[DataStore.BLOB_STORAGE]), _make_plan()).total_monthly
        two_stores = self.est.estimate(
            _make_spec(data_stores=[DataStore.BLOB_STORAGE, DataStore.REDIS]), _make_plan()
        ).total_monthly
        assert two_stores > one_store

    def test_markdown_output(self) -> None:
        result = self.est.estimate(_make_spec(), _make_plan())
        md = result.to_markdown()
        assert "Estimated Monthly Cost" in md
        assert "$" in md

    def test_always_includes_core_infra(self) -> None:
        result = self.est.estimate(_make_spec(), _make_plan())
        resources = [i.resource for i in result.items]
        assert "Log Analytics" in resources
        assert "Key Vault" in resources
        assert "Managed Identity" in resources


# ===================================================================
# Intent Parser -- Language & Compute Detection
# ===================================================================


class TestIntentParserLanguageDetection:
    """Test that the rule-based parser detects language and compute target (parameterized)."""

    def setup_method(self) -> None:
        self.parser = IntentParserAgent(_make_config())

    @pytest.mark.parametrize("intent,expected_lang", [
        ("Build a secure API with blob storage", "python"),
        ("Build a nodejs REST API with express", "node"),
        ("Build a JavaScript API service", "node"),
        ("Build a csharp microservice with sql database", "dotnet"),
        ("Build a dotnet API for data processing", "dotnet"),
    ])
    def test_detects_language(self, intent, expected_lang) -> None:
        spec = self.parser.parse(intent)
        assert spec.language == expected_lang

    @pytest.mark.parametrize("intent,expected_target", [
        ("Build a secure API with blob storage", ComputeTarget.CONTAINER_APPS),
        ("Build a web app using app service with SQL", ComputeTarget.APP_SERVICE),
        ("Build a serverless event processor", ComputeTarget.FUNCTIONS),
        ("Build an Azure function for image processing", ComputeTarget.FUNCTIONS),
    ])
    def test_detects_compute_target(self, intent, expected_target) -> None:
        spec = self.parser.parse(intent)
        assert spec.compute_target == expected_target

    @pytest.mark.parametrize("intent,lang,framework", [
        ("Build a python API", "python", "fastapi"),
        ("Build a nodejs API", "node", "express"),
        ("Build a dotnet web service", "dotnet", "aspnet"),
    ])
    def test_framework_follows_language(self, intent, lang, framework) -> None:
        spec = self.parser.parse(intent)
        assert spec.language == lang
        assert spec.framework == framework


class TestSchemaEnums:
    """Test the enum types, mappings, and defaults."""

    def test_compute_target_and_language_values(self) -> None:
        assert ComputeTarget.CONTAINER_APPS.value == "container_apps"
        assert ComputeTarget.APP_SERVICE.value == "app_service"
        assert ComputeTarget.FUNCTIONS.value == "functions"
        assert LANGUAGE_FRAMEWORKS["python"] == "fastapi"
        assert LANGUAGE_FRAMEWORKS["node"] == "express"
        assert LANGUAGE_FRAMEWORKS["dotnet"] == "aspnet"

    def test_intent_spec_defaults(self) -> None:
        spec = IntentSpec(
            project_name="test-defaults",
            description="Test defaults",
            raw_intent="test",
        )
        assert spec.language == "python"
        assert spec.framework == "fastapi"
        assert spec.compute_target == ComputeTarget.CONTAINER_APPS
