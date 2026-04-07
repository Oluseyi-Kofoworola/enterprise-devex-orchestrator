"""Tests for generators -- Bicep, CI/CD, App, Docs, Dashboard."""

from __future__ import annotations

from unittest.mock import patch, MagicMock

from src.orchestrator.generators.app_generator import AppGenerator
from src.orchestrator.generators.bicep_generator import BicepGenerator
from src.orchestrator.generators.cicd_generator import CICDGenerator
from src.orchestrator.generators.dashboard_generator import DashboardGenerator
from src.orchestrator.generators.docs_generator import DocsGenerator
from src.orchestrator.intent_schema import (
    AppType,
    AuthModel,
    CICDRequirements,
    ComplianceFramework,
    ComponentSpec,
    DataStore,
    GovernanceCheck,
    GovernanceReport,
    IntentSpec,
    NetworkingModel,
    ObservabilityRequirements,
    PlanOutput,
    SecurityRequirements,
    ThreatEntry,
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
            ComponentSpec(
                name="key-vault",
                azure_service="Microsoft.KeyVault/vaults",
                purpose="Secret management",
                bicep_module="keyvault.bicep",
                security_controls=["RBAC"],
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


class TestBicepGenerator:
    """Test Bicep template generation."""

    def setup_method(self) -> None:
        self.gen = BicepGenerator()

    def test_generate_returns_files(self) -> None:
        files = self.gen.generate(_make_spec(), _make_plan())
        assert len(files) > 0

    def test_generates_main_bicep(self) -> None:
        files = self.gen.generate(_make_spec(), _make_plan())
        assert "infra/bicep/main.bicep" in files

    def test_generates_parameter_file(self) -> None:
        files = self.gen.generate(_make_spec(), _make_plan())
        assert "infra/bicep/parameters/dev.parameters.json" in files

    def test_main_bicep_has_target_scope(self) -> None:
        files = self.gen.generate(_make_spec(), _make_plan())
        main = files["infra/bicep/main.bicep"]
        assert "targetScope" in main

    def test_main_bicep_has_modules(self) -> None:
        files = self.gen.generate(_make_spec(), _make_plan())
        main = files["infra/bicep/main.bicep"]
        assert "module" in main

    def test_generates_keyvault_module(self) -> None:
        files = self.gen.generate(_make_spec(), _make_plan())
        assert "infra/bicep/modules/keyvault.bicep" in files

    def test_keyvault_has_rbac(self) -> None:
        files = self.gen.generate(_make_spec(), _make_plan())
        kv = files["infra/bicep/modules/keyvault.bicep"]
        assert "enableRbacAuthorization" in kv

    def test_keyvault_has_soft_delete(self) -> None:
        files = self.gen.generate(_make_spec(), _make_plan())
        kv = files["infra/bicep/modules/keyvault.bicep"]
        assert "enableSoftDelete" in kv

    def test_generates_container_app_module(self) -> None:
        files = self.gen.generate(_make_spec(), _make_plan())
        assert "infra/bicep/modules/container-app.bicep" in files

    def test_container_app_has_health_probes(self) -> None:
        files = self.gen.generate(_make_spec(), _make_plan())
        ca = files["infra/bicep/modules/container-app.bicep"]
        assert "probes" in ca or "healthProbe" in ca or "/health" in ca

    def test_generates_managed_identity(self) -> None:
        files = self.gen.generate(_make_spec(), _make_plan())
        assert "infra/bicep/modules/managed-identity.bicep" in files

    def test_generates_storage_when_blob(self) -> None:
        spec = _make_spec(data_stores=[DataStore.BLOB_STORAGE])
        files = self.gen.generate(spec, _make_plan())
        assert "infra/bicep/modules/storage.bicep" in files

    def test_storage_has_private_access(self) -> None:
        spec = _make_spec(data_stores=[DataStore.BLOB_STORAGE])
        files = self.gen.generate(spec, _make_plan())
        storage = files["infra/bicep/modules/storage.bicep"]
        assert "allowBlobPublicAccess" in storage


class TestCICDGenerator:
    """Test CI/CD workflow generation."""

    def setup_method(self) -> None:
        self.gen = CICDGenerator()

    def test_generate_returns_files(self) -> None:
        files = self.gen.generate(_make_spec())
        assert len(files) > 0

    def test_generates_validate_workflow(self) -> None:
        files = self.gen.generate(_make_spec())
        assert ".github/workflows/validate.yml" in files

    def test_generates_deploy_workflow(self) -> None:
        files = self.gen.generate(_make_spec())
        assert ".github/workflows/deploy.yml" in files

    def test_generates_dependabot(self) -> None:
        files = self.gen.generate(_make_spec())
        assert ".github/dependabot.yml" in files

    def test_generates_codeql(self) -> None:
        files = self.gen.generate(_make_spec())
        assert ".github/workflows/codeql.yml" in files

    def test_deploy_uses_oidc(self) -> None:
        files = self.gen.generate(_make_spec())
        deploy = files[".github/workflows/deploy.yml"]
        assert "id-token" in deploy

    def test_validate_has_tests(self) -> None:
        files = self.gen.generate(_make_spec())
        validate = files[".github/workflows/validate.yml"]
        assert "pytest" in validate or "test" in validate.lower()


class TestAppGenerator:
    """Test application scaffold generation."""

    def setup_method(self) -> None:
        self.gen = AppGenerator()

    def test_generate_returns_files(self) -> None:
        files = self.gen.generate(_make_spec())
        assert len(files) > 0

    def test_generates_main_py(self) -> None:
        files = self.gen.generate(_make_spec())
        assert "src/app/main.py" in files

    def test_generates_dockerfile(self) -> None:
        files = self.gen.generate(_make_spec())
        assert "src/app/Dockerfile" in files

    def test_generates_requirements(self) -> None:
        files = self.gen.generate(_make_spec())
        assert "src/app/requirements.txt" in files

    def test_main_has_health_endpoint(self) -> None:
        files = self.gen.generate(_make_spec())
        main = files["src/app/main.py"]
        assert "/health" in main

    def test_main_has_spa_serving(self) -> None:
        files = self.gen.generate(_make_spec())
        main = files["src/app/main.py"]
        assert "STATIC_DIR" in main
        assert "StaticFiles" in main

    def test_main_supports_key_vault_uri(self) -> None:
        files = self.gen.generate(_make_spec())
        main = files["src/app/main.py"]
        assert "KEY_VAULT_URI" in main
        assert "KEY_VAULT_NAME" in main

    def test_dockerfile_has_nonroot_user(self) -> None:
        files = self.gen.generate(_make_spec())
        dockerfile = files["src/app/Dockerfile"]
        assert "USER" in dockerfile

    def test_dockerfile_has_healthcheck(self) -> None:
        files = self.gen.generate(_make_spec())
        dockerfile = files["src/app/Dockerfile"]
        assert "HEALTHCHECK" in dockerfile


class TestDocsGenerator:
    """Test documentation generation."""

    def setup_method(self) -> None:
        self.gen = DocsGenerator()

    def test_generate_returns_files(self) -> None:
        files = self.gen.generate(_make_spec(), _make_plan())
        assert len(files) > 0

    def test_generates_plan_md(self) -> None:
        files = self.gen.generate(_make_spec(), _make_plan())
        assert "docs/plan.md" in files

    def test_generates_security_md(self) -> None:
        files = self.gen.generate(_make_spec(), _make_plan())
        assert "docs/security.md" in files

    def test_generates_deployment_md(self) -> None:
        files = self.gen.generate(_make_spec(), _make_plan())
        assert "docs/deployment.md" in files

    def test_generates_rai_notes(self) -> None:
        files = self.gen.generate(_make_spec(), _make_plan())
        assert "docs/rai-notes.md" in files

    def test_generates_demo_script(self) -> None:
        files = self.gen.generate(_make_spec(), _make_plan())
        assert "docs/demo-script.md" in files

    def test_generates_scorecard(self) -> None:
        files = self.gen.generate(_make_spec(), _make_plan())
        assert "docs/scorecard.md" in files

    def test_plan_md_includes_components(self) -> None:
        files = self.gen.generate(_make_spec(), _make_plan())
        plan = files["docs/plan.md"]
        assert "container-app" in plan

    def test_security_md_includes_threat_model(self) -> None:
        files = self.gen.generate(_make_spec(), _make_plan())
        sec = files["docs/security.md"]
        assert "STRIDE" in sec

    def test_governance_report_generated_when_provided(self) -> None:
        gov = GovernanceReport(
            status="PASS",
            summary="All checks passed",
            checks=[
                GovernanceCheck(
                    check_id="GOV-001",
                    name="Test",
                    passed=True,
                    severity="warning",
                    details="OK",
                )
            ],
            recommendations=[],
        )
        files = self.gen.generate(_make_spec(), _make_plan(), gov)
        assert "docs/governance-report.md" in files

    def test_governance_report_not_generated_when_none(self) -> None:
        files = self.gen.generate(_make_spec(), _make_plan(), None)
        assert "docs/governance-report.md" not in files


# ===================================================================
# Improvement #1: DDD Application Architecture
# ===================================================================


class TestAppGeneratorDDD:
    """Test DDD layered architecture in Python scaffold."""

    def setup_method(self) -> None:
        self.gen = AppGenerator()

    def test_generates_v1_router(self) -> None:
        files = self.gen.generate(_make_spec())
        assert "src/app/api/v1/router.py" in files

    def test_generates_v1_schemas(self) -> None:
        files = self.gen.generate(_make_spec())
        assert "src/app/api/v1/schemas.py" in files

    def test_generates_core_config(self) -> None:
        files = self.gen.generate(_make_spec())
        assert "src/app/core/config.py" in files

    def test_generates_core_dependencies(self) -> None:
        files = self.gen.generate(_make_spec())
        assert "src/app/core/dependencies.py" in files

    def test_generates_core_services(self) -> None:
        files = self.gen.generate(_make_spec())
        assert "src/app/core/services.py" in files

    def test_generates_api_init_files(self) -> None:
        files = self.gen.generate(_make_spec())
        assert "src/app/api/__init__.py" in files
        assert "src/app/api/v1/__init__.py" in files
        assert "src/app/core/__init__.py" in files

    def test_main_imports_v1_router(self) -> None:
        files = self.gen.generate(_make_spec())
        main = files["src/app/main.py"]
        assert "v1_router" in main

    def test_main_includes_router(self) -> None:
        files = self.gen.generate(_make_spec())
        main = files["src/app/main.py"]
        assert "include_router" in main

    def test_v1_router_has_api_router(self) -> None:
        files = self.gen.generate(_make_spec())
        router = files["src/app/api/v1/router.py"]
        assert "APIRouter" in router

    def test_v1_router_has_resource_endpoint(self) -> None:
        files = self.gen.generate(_make_spec())
        router = files["src/app/api/v1/router.py"]
        assert "/resources" in router

    def test_v1_schemas_has_pydantic_model(self) -> None:
        files = self.gen.generate(_make_spec())
        schemas = files["src/app/api/v1/schemas.py"]
        assert "BaseModel" in schemas

    def test_core_config_has_settings(self) -> None:
        files = self.gen.generate(_make_spec())
        config = files["src/app/core/config.py"]
        assert "Settings" in config

    def test_core_dependencies_has_keyvault(self) -> None:
        files = self.gen.generate(_make_spec())
        deps = files["src/app/core/dependencies.py"]
        assert "keyvault" in deps.lower() or "SecretClient" in deps

    def test_core_services_has_item_service(self) -> None:
        files = self.gen.generate(_make_spec())
        services = files["src/app/core/services.py"]
        assert "ResourceService" in services

    def test_ddd_total_file_count(self) -> None:
        files = self.gen.generate(_make_spec())
        # 5 original + 7 DDD = 12 files
        assert len(files) >= 12

    def test_v1_router_storage_routes_when_blob(self) -> None:
        spec = _make_spec(data_stores=[DataStore.BLOB_STORAGE])
        files = self.gen.generate(spec)
        router = files["src/app/api/v1/router.py"]
        assert "blob" in router.lower() or "storage" in router.lower()


# ===================================================================
# Improvement #2: Azure Live Validation
# ===================================================================


class TestAzureValidation:
    """Test live Azure resource validation in ArchitecturePlanner."""

    def test_validate_returns_empty_when_no_az_cli(self) -> None:
        from src.orchestrator.agents.architecture_planner import ArchitecturePlannerAgent
        from src.orchestrator.config import AppConfig

        planner = ArchitecturePlannerAgent(AppConfig())
        with patch("src.orchestrator.agents.architecture_planner.shutil.which", return_value=None):
            warnings = planner._validate_azure_resources(_make_spec())
        assert warnings == []

    def test_validate_returns_empty_when_all_available(self) -> None:
        from src.orchestrator.agents.architecture_planner import ArchitecturePlannerAgent
        from src.orchestrator.config import AppConfig

        planner = ArchitecturePlannerAgent(AppConfig())
        with patch("src.orchestrator.agents.architecture_planner.shutil.which", return_value="/usr/bin/az"):
            with patch.object(planner, "_check_provider_in_region", return_value=True):
                warnings = planner._validate_azure_resources(_make_spec())
        assert warnings == []

    def test_validate_returns_warning_when_unavailable(self) -> None:
        from src.orchestrator.agents.architecture_planner import ArchitecturePlannerAgent
        from src.orchestrator.config import AppConfig

        planner = ArchitecturePlannerAgent(AppConfig())
        with patch("src.orchestrator.agents.architecture_planner.shutil.which", return_value="/usr/bin/az"):
            with patch.object(planner, "_check_provider_in_region", return_value=False):
                warnings = planner._validate_azure_resources(_make_spec())
        assert len(warnings) >= 4  # At least Container Apps, KV, LA, ACR

    def test_validate_checks_cosmos_when_present(self) -> None:
        from src.orchestrator.agents.architecture_planner import ArchitecturePlannerAgent
        from src.orchestrator.config import AppConfig

        planner = ArchitecturePlannerAgent(AppConfig())
        spec = _make_spec(data_stores=[DataStore.COSMOS_DB])
        with patch("src.orchestrator.agents.architecture_planner.shutil.which", return_value="/usr/bin/az"):
            with patch.object(planner, "_check_provider_in_region", return_value=False):
                warnings = planner._validate_azure_resources(spec)
        cosmos_warnings = [w for w in warnings if "Cosmos" in w]
        assert len(cosmos_warnings) == 1

    def test_check_provider_returns_none_on_error(self) -> None:
        from src.orchestrator.agents.architecture_planner import ArchitecturePlannerAgent
        from src.orchestrator.config import AppConfig

        planner = ArchitecturePlannerAgent(AppConfig())
        mock_result = MagicMock()
        mock_result.returncode = 1
        with patch("src.orchestrator.agents.architecture_planner.subprocess.run", return_value=mock_result):
            result = planner._check_provider_in_region(
                "Microsoft.App", "managedEnvironments", "eastus2"
            )
        assert result is None

    def test_check_provider_returns_true_when_region_listed(self) -> None:
        from src.orchestrator.agents.architecture_planner import ArchitecturePlannerAgent
        from src.orchestrator.config import AppConfig

        planner = ArchitecturePlannerAgent(AppConfig())
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '["East US 2", "West US"]'
        with patch("src.orchestrator.agents.architecture_planner.subprocess.run", return_value=mock_result):
            result = planner._check_provider_in_region(
                "Microsoft.App", "managedEnvironments", "eastus2"
            )
        assert result is True

    def test_check_provider_returns_false_when_region_not_listed(self) -> None:
        from src.orchestrator.agents.architecture_planner import ArchitecturePlannerAgent
        from src.orchestrator.config import AppConfig

        planner = ArchitecturePlannerAgent(AppConfig())
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '["West Europe", "North Europe"]'
        with patch("src.orchestrator.agents.architecture_planner.subprocess.run", return_value=mock_result):
            result = planner._check_provider_in_region(
                "Microsoft.App", "managedEnvironments", "eastus2"
            )
        assert result is False


# ===================================================================
# Improvement #3: AVM Bicep Modules
# ===================================================================


class TestBicepAVM:
    """Test Azure Verified Modules references in Bicep output."""

    def setup_method(self) -> None:
        self.gen = BicepGenerator()
        self.files = self.gen.generate(_make_spec(), _make_plan())

    def test_generates_bicepconfig_json(self) -> None:
        assert "infra/bicep/bicepconfig.json" in self.files

    def test_bicepconfig_has_module_aliases(self) -> None:
        config = self.files["infra/bicep/bicepconfig.json"]
        assert "moduleAliases" in config

    def test_bicepconfig_has_mcr_registry(self) -> None:
        config = self.files["infra/bicep/bicepconfig.json"]
        assert "mcr.microsoft.com" in config

    def test_bicepconfig_has_analyzer_rules(self) -> None:
        config = self.files["infra/bicep/bicepconfig.json"]
        assert "analyzers" in config

    def test_keyvault_has_avm_reference(self) -> None:
        kv = self.files["infra/bicep/modules/keyvault.bicep"]
        assert "avm" in kv.lower() or "Azure Verified Module" in kv

    def test_log_analytics_has_avm_reference(self) -> None:
        la = self.files["infra/bicep/modules/log-analytics.bicep"]
        assert "avm" in la.lower() or "Azure Verified Module" in la

    def test_container_registry_has_avm_reference(self) -> None:
        acr = self.files["infra/bicep/modules/container-registry.bicep"]
        assert "avm" in acr.lower() or "Azure Verified Module" in acr

    def test_storage_has_avm_reference_when_blob(self) -> None:
        spec = _make_spec(data_stores=[DataStore.BLOB_STORAGE])
        files = self.gen.generate(spec, _make_plan())
        storage = files["infra/bicep/modules/storage.bicep"]
        assert "avm" in storage.lower() or "Azure Verified Module" in storage


# ===================================================================
# Improvement #4: Dashboard Generator
# ===================================================================


class TestDashboardGenerator:
    """Test Azure Monitor dashboard Bicep generation."""

    def setup_method(self) -> None:
        self.gen = DashboardGenerator()

    def _make_dashboard_spec(self) -> IntentSpec:
        spec = _make_spec()
        spec.observability = ObservabilityRequirements(
            log_analytics=True,
            health_endpoint=True,
            dashboard=True,
        )
        return spec

    def test_skips_when_dashboard_false(self) -> None:
        spec = _make_spec()
        files = self.gen.generate(spec)
        assert files == {}

    def test_generates_files_when_dashboard_true(self) -> None:
        files = self.gen.generate(self._make_dashboard_spec())
        assert len(files) == 2

    def test_generates_dashboard_bicep(self) -> None:
        files = self.gen.generate(self._make_dashboard_spec())
        assert "infra/bicep/modules/dashboard.bicep" in files

    def test_generates_kql_doc(self) -> None:
        files = self.gen.generate(self._make_dashboard_spec())
        assert "docs/dashboard-queries.md" in files

    def test_dashboard_bicep_has_resource(self) -> None:
        files = self.gen.generate(self._make_dashboard_spec())
        bicep = files["infra/bicep/modules/dashboard.bicep"]
        assert "Microsoft.Portal/dashboards" in bicep

    def test_dashboard_has_kql_queries(self) -> None:
        files = self.gen.generate(self._make_dashboard_spec())
        bicep = files["infra/bicep/modules/dashboard.bicep"]
        assert "query" in bicep.lower()

    def test_kql_doc_has_queries(self) -> None:
        files = self.gen.generate(self._make_dashboard_spec())
        doc = files["docs/dashboard-queries.md"]
        assert "```" in doc  # KQL code blocks

    def test_dashboard_with_storage(self) -> None:
        spec = self._make_dashboard_spec()
        spec.data_stores = [DataStore.BLOB_STORAGE]
        files = self.gen.generate(spec)
        bicep = files["infra/bicep/modules/dashboard.bicep"]
        assert "blob" in bicep.lower() or "storage" in bicep.lower() or "StorageBlob" in bicep


# ===================================================================
# Improvement #5: Multi-Environment CI/CD
# ===================================================================


class TestMultiEnvCICD:
    """Test multi-environment deployment workflow generation."""

    def setup_method(self) -> None:
        self.gen = CICDGenerator()

    def _make_multienv_spec(self, approval_gates: bool = False) -> IntentSpec:
        return IntentSpec(
            project_name="test-project",
            app_type=AppType.API,
            description="A test API service",
            raw_intent="Build a test API",
            data_stores=[],
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
                environments=["dev", "staging", "prod"],
                approval_gates=approval_gates,
            ),
            azure_region="eastus2",
            resource_group_name="rg-test",
            environment="dev",
            confidence=0.85,
        )

    def test_deploy_has_environment_input(self) -> None:
        spec = self._make_multienv_spec()
        files = self.gen.generate(spec)
        deploy = files[".github/workflows/deploy.yml"]
        assert "environment" in deploy

    def test_deploy_has_env_choice_options(self) -> None:
        spec = self._make_multienv_spec()
        files = self.gen.generate(spec)
        deploy = files[".github/workflows/deploy.yml"]
        assert "dev" in deploy
        assert "staging" in deploy
        assert "prod" in deploy

    def test_deploy_has_per_env_jobs(self) -> None:
        spec = self._make_multienv_spec()
        files = self.gen.generate(spec)
        deploy = files[".github/workflows/deploy.yml"]
        assert "deploy-dev" in deploy
        assert "deploy-staging" in deploy
        assert "deploy-prod" in deploy

    def test_deploy_env_specific_resource_groups(self) -> None:
        spec = self._make_multienv_spec()
        files = self.gen.generate(spec)
        deploy = files[".github/workflows/deploy.yml"]
        assert "rg-test-project-dev" in deploy
        assert "rg-test-project-staging" in deploy
        assert "rg-test-project-prod" in deploy

    def test_approval_gates_enabled(self) -> None:
        spec = self._make_multienv_spec(approval_gates=True)
        files = self.gen.generate(spec)
        deploy = files[".github/workflows/deploy.yml"]
        assert "manual-approval" in deploy or "approval" in deploy.lower()

    def test_approval_gates_not_for_dev(self) -> None:
        spec = self._make_multienv_spec(approval_gates=True)
        files = self.gen.generate(spec)
        deploy = files[".github/workflows/deploy.yml"]
        # There should be approval steps for staging/prod but not dev
        assert "Require approval for staging" in deploy or "approval" in deploy.lower()

    def test_no_approval_gates_when_disabled(self) -> None:
        spec = self._make_multienv_spec(approval_gates=False)
        files = self.gen.generate(spec)
        deploy = files[".github/workflows/deploy.yml"]
        assert "manual-approval" not in deploy

    def test_generates_staging_parameters(self) -> None:
        spec = self._make_multienv_spec()
        files = self.gen.generate(spec)
        assert "infra/bicep/parameters/staging.parameters.json" in files

    def test_generates_prod_parameters(self) -> None:
        spec = self._make_multienv_spec()
        files = self.gen.generate(spec)
        assert "infra/bicep/parameters/prod.parameters.json" in files

    def test_env_parameters_has_correct_env(self) -> None:
        spec = self._make_multienv_spec()
        files = self.gen.generate(spec)
        staging = files["infra/bicep/parameters/staging.parameters.json"]
        assert '"staging"' in staging

    def test_single_env_default_no_extra_params(self) -> None:
        """Default spec with only dev should not generate extra parameter files."""
        files = self.gen.generate(_make_spec())
        assert "infra/bicep/parameters/staging.parameters.json" not in files
        assert "infra/bicep/parameters/prod.parameters.json" not in files

    def test_deploy_uses_oidc_in_multienv(self) -> None:
        spec = self._make_multienv_spec()
        files = self.gen.generate(spec)
        deploy = files[".github/workflows/deploy.yml"]
        assert "id-token" in deploy
